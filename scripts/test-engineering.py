#!/usr/bin/env python3
"""Real .NET maintenance fixtures and mutation checks; not an agent behavior test."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from validation import ROOT, load_json

FIXTURE = ROOT / 'evals/fixtures/dotnet'
MUTATIONS = {
    'library-boundary': ('src/Pricing/PriceCalculator.cs', 'quantity >= 10', 'quantity > 10', 'Pricing', 'DiscountBoundary'),
    'library-rounding': ('src/Pricing/PriceCalculator.cs', 'MidpointRounding.ToEven', 'MidpointRounding.AwayFromZero', 'Pricing', 'RoundsToEven'),
    'http-validation': ('src/Catalog.Api/Program.cs', 'request.Quantity <= 0', 'request.Quantity < 0', 'Catalog.Api', 'RejectsInvalidQuantityWithoutPersisting'),
    'worker-deduplication': ('src/Queue.Worker/QueueWorker.cs', 'if (completed.Contains(id)) continue;', 'if (completed.Contains(id) && id.Length == 0) continue;', 'Queue.Worker', 'DeduplicatesCompletedItems'),
    'worker-cancellation': ('src/Queue.Worker/QueueWorker.cs', 'ReadAllAsync(stoppingToken)', 'ReadAllAsync()', 'Queue.Worker', 'StopsWhileWaitingForInput'),
    'public-contract': ('src/Contracts/Receipt.cs', 'JsonPropertyName("amount")', 'JsonPropertyName("total")', 'Checkout', 'SerializedReceiptContract'),
}


def test_results(directory):
    """Reject missing TRX, zero discovered/executed tests, and skipped-only runs."""
    files = list(Path(directory).glob('*.trx'))
    if not files:
        raise ValueError('no TRX results; test execution is unverified')
    total = executed = passed = failed = 0
    failures = []
    ns = {'t': 'http://microsoft.com/schemas/VisualStudio/TeamTest/2010'}
    for path in files:
        tree = ET.parse(path)
        counters = tree.find('.//t:Counters', ns)
        if counters is None:
            raise ValueError('TRX missing counters')
        total += int(counters.get('total', 0))
        executed += int(counters.get('executed', 0))
        passed += int(counters.get('passed', 0))
        failed += int(counters.get('failed', 0))
        failures.extend(r.get('testName', '') for r in tree.findall('.//t:UnitTestResult', ns) if r.get('outcome') == 'Failed')
    if total <= 0 or executed <= 0 or passed + failed != total:
        raise ValueError(f'incomplete/zero tests: total={total}, executed={executed}, passed={passed}, failed={failed}')
    return {'total': total, 'passed': passed, 'failed': failed, 'failures': failures}


class Harness:
    def __init__(self, output, dotnet):
        self.output, self.dotnet = output.resolve(), dotnet
        self.work = self.output / 'workspace'
        self.records = []
        self.sdk = load_json(FIXTURE / 'global.json')['sdk']['version']
        self.env = dict(os.environ, DOTNET_CLI_HOME=str(self.output / 'cli'),
                        DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1', DOTNET_CLI_TELEMETRY_OPTOUT='1',
                        DOTNET_NOLOGO='1', DOTNET_ADD_GLOBAL_TOOLS_TO_PATH='0',
                        MSBUILDDISABLENODEREUSE='1',
                        DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE='true')

    def command(self, label, *args, timeout=180):
        log = self.output / f'{label}.log'
        command = [self.dotnet, *map(str, args)]
        try:
            result = subprocess.run(command, cwd=self.work, env=self.env, capture_output=True,
                                    text=True, encoding='utf-8', errors='replace', timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            log.write_text(str(error), encoding='utf-8')
            raise RuntimeError(f'{label}: {error}') from error
        log.write_text(json.dumps({'argv': command, 'cwd': str(self.work), 'exit_code': result.returncode}) +
                       '\n' + result.stdout + result.stderr, encoding='utf-8')
        return result

    def record(self, case, status, evidence, reason='', **extra):
        row = {'case_id': case, 'layer': 'deterministic', 'host': 'dotnet', 'host_version': self.sdk,
               'model_version': None, 'skill_version': 'engineering@' + load_json(ROOT / 'plugins/engineering/.claude-plugin/plugin.json')['version'],
               'status': status, 'evidence': evidence, 'reason': reason, **extra}
        self.records.append(row)
        print(json.dumps(row), flush=True)

    def test(self, label, project=None):
        result_dir = self.output / label
        target = f'tests/{project}.Tests/{project}.Tests.csproj' if project else 'Maintenance.slnx'
        result = self.command(label, 'test', target, '--no-restore', '-m:1', '--logger', 'trx', '--results-directory', result_dir)
        summary = test_results(result_dir)
        return result.returncode, summary

    def execute(self):
        self.output.mkdir(parents=True, exist_ok=True)
        shutil.copytree(FIXTURE, self.work, ignore=shutil.ignore_patterns('bin', 'obj', 'TestResults'))
        # A user-owned edit survives every experiment; never reset the workspace.
        sentinel = self.work / 'user-notes.txt'
        sentinel.write_text('Uncommitted user note: preserve this file.\n', encoding='utf-8')
        try:
            if not shutil.which(self.dotnet):
                (self.output / 'sdk.log').write_text(f'Executable unavailable: {self.dotnet}\n', encoding='utf-8')
                self.record('prerequisites', 'blocked', ['sdk.log'], 'dotnet executable unavailable')
                return 2
            version = self.command('sdk', '--version')
            if version.returncode or version.stdout.strip() != self.sdk:
                self.record('prerequisites', 'blocked', ['sdk.log'], f'exact SDK {self.sdk} unavailable')
                return 2
            restore = self.command('restore', 'restore', 'Maintenance.slnx', '-m:1', timeout=300)
            if restore.returncode:
                text = restore.stdout + restore.stderr
                blocked = any(s in text for s in ('NU1301', 'Unable to load the service index', 'Permission denied', 'Operation not permitted'))
                self.record('restore', 'blocked' if blocked else 'failed', ['restore.log'], 'dependency restore failed')
                return 2 if blocked else 1
            code, summary = self.test('baseline')
            if code or summary['failed']:
                self.record('baseline', 'failed', ['baseline.log'], 'baseline failed', tests=summary)
                return 1
            self.record('baseline', 'passed', ['baseline.log', 'baseline'], tests=summary)
            for case, (relative, before, after, project, expected_failure) in MUTATIONS.items():
                path = self.work / relative
                original_bytes = path.read_bytes()
                original = original_bytes.decode('utf-8')
                if original.count(before) != 1:
                    raise ValueError(f'{case}: mutation anchor changed')
                try:
                    path.write_text(original.replace(before, after), encoding='utf-8')
                    code, summary = self.test(case + '-broken', project)
                    if code == 0 or not any(expected_failure in name for name in summary['failures']):
                        raise ValueError(f'{case}: did not observe the expected behavioral failure')
                finally:
                    path.write_bytes(original_bytes)
                code, fixed = self.test(case + '-fixed', project)
                if code or fixed['failed']:
                    raise ValueError(f'{case}: repair did not restore passing tests')
                self.record(case, 'passed', [case + '-broken.log', case + '-fixed.log'], broken=summary, fixed=fixed)
            # A structural change is checked against the same consumer and serialization tests.
            path = self.work / 'src/Pricing/PriceCalculator.cs'
            original_bytes = path.read_bytes()
            original = original_bytes.decode('utf-8')
            try:
                changed = original.replace('var discounted = quantity >= 10 ? subtotal * 0.9m : subtotal;',
                                           'var discounted = ApplyDiscount(subtotal, quantity);')
                changed = changed.replace('\n}', '\n    private static decimal ApplyDiscount(decimal subtotal, int quantity) => quantity >= 10 ? subtotal * 0.9m : subtotal;\n}')
                path.write_text(changed, encoding='utf-8')
                code, summary = self.test('refactor')
                if code or summary['failed']:
                    raise ValueError('refactor changed external behavior')
                self.record('refactor-contracts', 'passed', ['baseline.log', 'refactor.log'], tests=summary)
            finally:
                path.write_bytes(original_bytes)
            if sentinel.read_text(encoding='utf-8') != 'Uncommitted user note: preserve this file.\n':
                raise ValueError('user edit lost')
            for source in FIXTURE.rglob('*'):
                if source.is_file() and not {'bin', 'obj', 'TestResults'} & set(source.relative_to(FIXTURE).parts):
                    if source.read_bytes() != (self.work / source.relative_to(FIXTURE)).read_bytes():
                        raise ValueError(f'fixture not restored: {source}')
            return 0
        except (ValueError, RuntimeError, OSError) as error:
            self.record('harness', 'failed', [p.name for p in self.output.glob('*.log')], str(error))
            return 1
        finally:
            (self.output / 'results.json').write_text(json.dumps({
                'timestamp': datetime.now(timezone.utc).isoformat(), 'records': self.records,
                'not_verified': ['agent routing/execution', 'host installation', 'non-SQLite database semantics']}, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--dotnet', default='dotnet')
    parser.add_argument('--nuget-packages', type=Path, help='optional isolated NuGet cache')
    args = parser.parse_args()
    if args.nuget_packages:
        os.environ['NUGET_PACKAGES'] = str(args.nuget_packages.resolve())
    output = args.output or Path(tempfile.mkdtemp(prefix='engineering-fixtures-'))
    print(f'Evidence: {output}', flush=True)
    return Harness(output, args.dotnet).execute()


if __name__ == '__main__':
    raise SystemExit(main())
