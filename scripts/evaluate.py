#!/usr/bin/env python3
"""Prepare isolated agent cases, optionally run Claude, and validate reviewed records.

No transcript keyword or model self-report can promote a task to passed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from validation import NAME, ROOT, load_json, require

spec = importlib.util.spec_from_file_location('fixtures', ROOT / 'scripts/test-engineering.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
STATUSES = {'passed', 'failed', 'blocked', 'unverified'}


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and not
            {'.git', 'bin', 'obj', 'TestResults'} & set(p.relative_to(root).parts)}


def prepare(case, output, condition, invocation='natural'):
    require(condition == 'enabled' or invocation == 'natural', 'disabled comparison uses natural invocation')
    require(not output.exists(), 'output already exists; use a fresh directory')
    output.mkdir(parents=True)
    work = output / 'workspace'
    shutil.copytree(fixtures.FIXTURE, work, ignore=shutil.ignore_patterns('bin', 'obj', 'TestResults'))
    subprocess.run(['git', 'init', '-q'], cwd=work, check=True)
    subprocess.run(['git', 'add', '.'], cwd=work, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture baseline'], cwd=work, check=True)
    mutation = case.get('mutation')
    if mutation in fixtures.MUTATIONS:
        relative, before, after, *_ = fixtures.MUTATIONS[mutation]
        path = work / relative
        text = path.read_text(encoding='utf-8')
        require(text.count(before) == 1, 'mutation anchor changed')
        path.write_text(text.replace(before, after), encoding='utf-8')
    elif mutation == 'comment-only':
        with (work / 'src/Pricing/PriceCalculator.cs').open('a', encoding='utf-8') as handle:
            handle.write('\n// Bulk pricing uses the established quantity threshold.\n')
    if case['id'] == 'regression-tests-positive':
        (work / 'tests/Pricing.Tests/PriceTests.cs').unlink()
    if case['id'] == 'bugfix-user-edits':
        (work / 'user-notes.txt').write_text('User note: keep this file.\n', encoding='utf-8')
        with (work / 'src/Pricing/PriceCalculator.cs').open('a', encoding='utf-8') as handle:
            handle.write('\n// user note: pricing audit pending\n')
    # Simulated tool restrictions are outside the agent workspace and explicitly recorded.
    environment = case.get('environment') or ('missing-sdk' if case['scenario'] == 'restricted' else None)
    if environment:
        shim = output / 'shim'
        shim.mkdir()
        replies = {
            'missing-sdk': ('dotnet: SDK unavailable in this evaluation; installation prohibited', 127),
            'zero-tests': ('No test is available. Total tests: 0. Passed: 0. Failed: 0.', 0),
            'tool-failure': ('Test tool failed before execution.', 9),
            'database-unavailable': ('SQLite Error 14: unable to open database file; integration execution blocked.', 1),
        }
        message, code = replies[environment]
        (shim / 'dotnet').write_text(f'#!/bin/sh\nprintf "%s\\n" "{message}"\nexit {code}\n', encoding='utf-8')
        (shim / 'dotnet').chmod(0o755)
    prompt = case['prompt'] if invocation == 'natural' else f"/engineering:{case['skill']} {case['prompt']}"
    (output / 'prompt.txt').write_text(prompt + '\n', encoding='utf-8')
    manifest = {'case': case, 'condition': condition, 'invocation': invocation, 'environment': environment,
                'before': snapshot(work), 'created': datetime.now(timezone.utc).isoformat(),
                'plugin_digest': snapshot(ROOT / 'plugins/engineering')}
    (output / 'run.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def run_claude(output, condition, timeout, dotnet=None, nuget_packages=None):
    manifest = load_json(output / 'run.json')
    command = ['claude', '-p', (output / 'prompt.txt').read_text(encoding='utf-8'),
               '--output-format', 'stream-json', '--verbose', '--no-session-persistence',
               '--setting-sources', 'user', '--settings', '{"disableAllHooks":true}',
               '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
               '--permission-mode', 'acceptEdits', '--tools', 'Read,Write,Edit,Glob,Grep,Skill,Bash',
               '--allowedTools', 'Read,Write,Edit,Glob,Grep,Skill,Bash']
    if condition == 'enabled':
        command += ['--plugin-dir', str(ROOT / 'plugins/engineering')]
    env = dict(os.environ)
    env.update(DOTNET_CLI_HOME=str(output / 'cli'), DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1')
    if dotnet:
        env['PATH'] = str(dotnet.resolve().parent) + os.pathsep + env.get('PATH', '')
    if nuget_packages:
        env['NUGET_PACKAGES'] = str(nuget_packages.resolve())
    if (output / 'shim').exists():
        env['PATH'] = str(output / 'shim') + os.pathsep + env.get('PATH', '')
    host_version = subprocess.run(['claude', '--version'], capture_output=True, text=True, check=True).stdout.strip()
    started = datetime.now(timezone.utc)
    code, reason = None, ''
    try:
        with (output / 'host.jsonl').open('w', encoding='utf-8') as stdout, (output / 'host.stderr').open('w', encoding='utf-8') as stderr:
            process = subprocess.run(command, cwd=output / 'workspace', env=env, stdout=stdout, stderr=stderr, timeout=timeout)
            code = process.returncode
    except (OSError, subprocess.TimeoutExpired) as error:
        reason = str(error)
    events = []
    for line in (output / 'host.jsonl').read_text(encoding='utf-8').splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    init = next((e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init'), {})
    result = next((e for e in reversed(events) if e.get('type') == 'result'), {})
    model = init.get('model')
    status = 'unverified' if code == 0 and result.get('subtype') == 'success' and not result.get('is_error') else 'blocked'
    if status == 'blocked' and not reason:
        reason = f'host invocation did not succeed (exit {code}); inspect host logs'
    if status == 'unverified':
        reason = 'host completed; independent task/trigger grading required'
    record = {'case_id': manifest['case']['id'], 'layer': 'agent', 'host': 'claude', 'host_version': host_version,
              'model_version': model, 'skill_version': 'engineering@' + load_json(ROOT / 'plugins/engineering/.claude-plugin/plugin.json')['version'],
              'condition': condition, 'invocation': manifest['invocation'], 'status': status, 'evidence': ['host.jsonl', 'host.stderr', 'run.json'],
              'reason': reason, 'exit_code': code, 'timestamp': datetime.now(timezone.utc).isoformat(),
              'duration_seconds': (datetime.now(timezone.utc) - started).total_seconds(),
              'cost_usd': result.get('total_cost_usd'), 'usage': result.get('usage')}
    (output / 'record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (output / 'response.txt').write_text(str(result.get('result', '')), encoding='utf-8')
    # These invariants can reject a result, but cannot alone prove task correctness.
    after = snapshot(output / 'workspace')
    if manifest['case']['readonly'] and after != manifest['before']:
        record.update(status='failed', reason='read-only task changed workspace files')
        (output / 'record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False), flush=True)
    return 0 if record['status'] == 'unverified' else 2 if record['status'] == 'blocked' else 1


def validate_record(path):
    record = load_json(path)
    require(type(record) is dict, 'record must be object')
    for key in ('case_id', 'host', 'host_version', 'skill_version', 'timestamp'):
        require(isinstance(record.get(key), str) and record[key].strip(), f'missing {key}')
    require(datetime.fromisoformat(record['timestamp']).tzinfo is not None, 'timestamp needs timezone')
    known = {c['id'] for c in load_json(ROOT / 'evals/cases.json')['cases']}
    require(record['case_id'] in known, 'unknown case')
    require(record.get('layer') == 'agent', 'expected agent record')
    require(record.get('condition') in ('enabled', 'disabled'), 'missing comparison condition')
    require(record.get('status') in STATUSES, 'invalid status')
    if record['status'] in ('passed', 'failed'):
        require(isinstance(record.get('model_version'), str) and record['model_version'].strip(), 'graded task needs exact model')
    require(type(record.get('evidence')) is list and bool(record['evidence']), 'evidence required')
    for relative in record['evidence']:
        require(isinstance(relative, str) and not Path(relative).is_absolute(), 'evidence must be relative')
        target = (path.parent / relative).resolve()
        require(target.is_relative_to(path.parent.resolve()) and target.is_file(), 'evidence file missing/outside record directory')
    require(isinstance(record.get('reason'), str) and bool(record['reason'].strip()), 'reason required')
    if record['status'] == 'passed':
        require(type(record.get('exit_code')) is int and record['exit_code'] == 0, 'nonzero/unexecuted host cannot pass')
        require(type(record.get('checks')) is list and bool(record['checks']), 'independent checks required')
        require(all(type(c) is dict and c.get('status') == 'passed' and isinstance(c.get('evidence'), str)
                    and c['evidence'] in record['evidence'] for c in record['checks']), 'every check must pass with evidence')
    return record


def verify_candidate(output, dotnet, nuget_packages, label=None):
    """Independent execution on another copy; human contract/routing review remains required."""
    manifest = load_json(output / 'run.json')
    require(manifest['case']['skill'] in ('bugfix', 'regression-tests', 'safe-refactor'),
            'use manual evidence review for assessment/review cases')
    require(label is None or NAME.fullmatch(label), 'invalid verification label')
    directory = output / ('verification' if label is None else f'verification-{label}')
    require(not directory.exists(), 'verification already exists; retain it and use a fresh run')
    directory.mkdir()
    harness = fixtures.Harness(directory, str(dotnet or 'dotnet'))
    if nuget_packages:
        harness.env['NUGET_PACKAGES'] = str(nuget_packages.resolve())
    shutil.copytree(output / 'workspace', harness.work,
                    ignore=shutil.ignore_patterns('.git', 'bin', 'obj', 'TestResults'))
    checks = []
    try:
        version = harness.command('sdk', '--version')
        require(version.returncode == 0 and version.stdout.strip() == harness.sdk, 'required SDK unavailable')
        restore = harness.command('restore', 'restore', 'Maintenance.slnx', '-m:1', timeout=300)
        require(restore.returncode == 0, 'candidate restore failed; inspect verification/restore.log')
        code, baseline = harness.test('candidate')
        require(code == 0 and baseline['failed'] == 0, 'candidate test suite failed')
        checks.append({'check': 'candidate-suite', 'status': 'passed', 'evidence': 'candidate.log', 'tests': baseline})
        mutations = ['library-boundary', 'library-rounding'] if manifest['case']['skill'] == 'regression-tests' else []
        if manifest['case']['skill'] == 'bugfix' and manifest['case'].get('mutation') in fixtures.MUTATIONS:
            mutations = [manifest['case']['mutation']]
        for name in mutations:
            relative, before, after, project, _ = fixtures.MUTATIONS[name]
            path = harness.work / relative
            original = path.read_bytes()
            require(original.count(before.encode()) == 1, 'candidate changed mutation anchor; manual mutation required')
            try:
                path.write_bytes(original.replace(before.encode(), after.encode()))
                code, broken = harness.test(name + '-broken', project)
                require(code != 0 and broken['failed'] > 0, 'candidate tests did not detect mutation')
            finally:
                path.write_bytes(original)
            code, restored = harness.test(name + '-restored', project)
            require(code == 0 and restored['failed'] == 0, 'candidate not restored to passing tests')
            checks.append({'check': name, 'status': 'passed', 'evidence': name + '-broken.log',
                           'restored_evidence': name + '-restored.log', 'broken': broken, 'restored': restored})
        print(json.dumps(checks), flush=True)
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        checks.append({'check': 'verification', 'status': 'failed', 'reason': str(error)})
        print(f'FAIL: {error}')
        return 1
    finally:
        (directory / 'summary.json').write_text(json.dumps(checks, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ('prepare', 'run'):
        p = sub.add_parser(name)
        p.add_argument('--case', required=True)
        p.add_argument('--output', type=Path, required=True)
        p.add_argument('--condition', choices=('enabled', 'disabled'), default='enabled')
        p.add_argument('--invocation', choices=('natural', 'explicit'), default='natural')
        if name == 'run':
            p.add_argument('--timeout', type=int, default=300)
            p.add_argument('--dotnet', type=Path, help='optional SDK executable for the agent PATH')
            p.add_argument('--nuget-packages', type=Path)
    check = sub.add_parser('validate-record')
    check.add_argument('record', type=Path)
    verify = sub.add_parser('verify')
    verify.add_argument('output', type=Path, help='completed run directory')
    verify.add_argument('--dotnet', type=Path)
    verify.add_argument('--nuget-packages', type=Path)
    verify.add_argument('--label', help='retain a previous verification and write a separately named retry')
    args = parser.parse_args()
    try:
        if args.action == 'validate-record':
            validate_record(args.record)
            print('PASS: record structure/evidence; semantic grading still belongs to the reviewer')
            return 0
        if args.action == 'verify':
            return verify_candidate(args.output.resolve(), args.dotnet, args.nuget_packages, args.label)
        cases = {c['id']: c for c in load_json(ROOT / 'evals/cases.json')['cases']}
        require(args.case in cases, 'unknown case')
        prepare(cases[args.case], args.output.resolve(), args.condition, args.invocation)
        print(f'Prepared: {args.output}', flush=True)
        return run_claude(args.output.resolve(), args.condition, args.timeout, args.dotnet, args.nuget_packages) if args.action == 'run' else 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'FAIL: {error}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
