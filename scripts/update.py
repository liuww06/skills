#!/usr/bin/env python3
"""Refresh local Claude plugins and inspect host discovery evidence, never task correctness."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from validation import ROOT, load_json, require, validate


class Refresh:
    def __init__(self, root, output, cli='claude'):
        self.root, self.output, self.cli = root, output, cli
        self.counter = 0
        output.mkdir(parents=True, exist_ok=True)

    def run(self, *args, cwd=None, timeout=120):
        self.counter += 1
        command = [self.cli, *args]
        try:
            result = subprocess.run(command, cwd=cwd or self.root, capture_output=True,
                                    text=True, encoding='utf-8', errors='replace', timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            (self.output / f'{self.counter}.log').write_text(str(error), encoding='utf-8')
            raise RuntimeError(f'host unavailable/timeout; see {self.counter}.log') from error
        (self.output / f'{self.counter}.log').write_text(
            json.dumps({'argv': command, 'cwd': str(cwd or self.root), 'exit_code': result.returncode}) +
            '\n' + result.stdout + result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError(f'host exit {result.returncode}; see {self.counter}.log')
        return result.stdout

    def json(self, *args):
        return json.loads(self.run(*args))

    def execute(self, names):
        errors = validate(self.root)
        require(not errors, '\n'.join(errors))
        market = load_json(self.root / '.claude-plugin/marketplace.json')
        marketplace = market['name']
        require(set(names) <= {e['name'] for e in market['plugins']}, 'unknown plugin')
        registered = self.json('plugin', 'marketplace', 'list', '--json')
        matches = [entry for entry in registered if entry['name'] == marketplace]
        if matches:
            require(len(matches) == 1 and matches[0].get('source') == 'directory' and
                    Path(matches[0].get('path', '')).resolve() == self.root.resolve(),
                    'marketplace name already points elsewhere; refusing to replace it')
        else:
            self.run('plugin', 'marketplace', 'add', str(self.root))
        installed = self.json('plugin', 'list', '--json')
        for name in names:
            identity = f'{name}@{marketplace}'
            if any(entry['id'] == identity for entry in installed):
                self.run('plugin', 'uninstall', identity)
            self.run('plugin', 'install', identity)
        installed = self.json('plugin', 'list', '--json')
        results = []
        for name in names:
            expected = self.root / 'plugins' / name
            identity = f'{name}@{marketplace}'
            matches = [entry for entry in installed if entry['id'] == identity and entry.get('enabled') is True]
            row = {'plugin': name, 'artifact_status': 'unverified', 'discovery_status': 'unverified',
                   'task_status': 'unverified', 'reason': 'host discovery evidence not yet observed'}
            if len(matches) == 1 and isinstance(matches[0].get('readFromFolder') or matches[0].get('installPath'), str):
                actual = Path(matches[0].get('readFromFolder') or matches[0]['installPath'])
                expected_files = {p.relative_to(expected) for p in expected.rglob('*') if p.is_file()}
                actual_files = {p.relative_to(actual) for p in actual.rglob('*') if p.is_file()}
                require(expected_files == actual_files, f'installed file inventory differs: {name}')
                for source in expected.rglob('*'):
                    if source.is_file():
                        destination = actual / source.relative_to(expected)
                        require(destination.is_file() and
                                hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(destination.read_bytes()).digest(),
                                f'installed bytes differ: {destination}')
                row['artifact_status'] = 'passed'
            results.append(row)
        # This prompt cannot prove loading; only host-emitted init metadata counts.
        with tempfile.TemporaryDirectory(prefix='skills-discovery-') as work:
            stream = self.run('-p', 'Do no project work. This session only checks plugin discovery.',
                              '--output-format', 'stream-json', '--verbose', '--tools', '',
                              '--no-session-persistence', cwd=Path(work))
        events = [json.loads(line) for line in stream.splitlines() if line.strip()]
        require(not any(e.get('is_error') for e in events), 'host reported an error despite exit 0')
        inits = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
        terminal = [e for e in events if e.get('type') == 'result' and e.get('subtype') == 'success']
        if inits and terminal:
            exposed = set()
            for field in ('skills', 'slash_commands'):
                values = inits[-1].get(field)
                if isinstance(values, list):
                    exposed.update(value for value in values if isinstance(value, str))
            for row in results:
                expected = {f"{row['plugin']}:{p.parent.name}" for p in
                            (self.root / 'plugins' / row['plugin'] / 'skills').glob('*/SKILL.md')}
                expected.update(f"{row['plugin']}:{p.stem}" for p in
                                (self.root / 'plugins' / row['plugin'] / 'commands').glob('*.md'))
                if expected <= exposed:
                    row['discovery_status'] = 'passed'
                    row['reason'] = 'host init metadata lists all skills; task behavior remains unverified'
        return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plugin', nargs='?')
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, help='directory for command logs and report')
    args = parser.parse_args()
    output = args.output or Path(tempfile.mkdtemp(prefix='skills-refresh-'))
    print(f'Evidence: {output}', flush=True)
    try:
        names = [args.plugin] if args.plugin else [e['name'] for e in load_json(args.root / 'marketplace.json')['plugins']]
        rows = Refresh(args.root, output).execute(names)
        (output / 'results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        for row in rows:
            print(json.dumps(row, ensure_ascii=False))
        return 0 if all(r['artifact_status'] == r['discovery_status'] == 'passed' for r in rows) else 2
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        output.mkdir(parents=True, exist_ok=True)
        (output / 'results.json').write_text(json.dumps({'status': 'failed', 'reason': str(error)}) + '\n', encoding='utf-8')
        print(f'FAIL: {error}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
