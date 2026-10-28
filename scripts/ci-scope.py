#!/usr/bin/env python3
"""Select costly deterministic jobs; missing history conservatively runs both."""
import os
import re
import subprocess


def main():
    base = os.environ.get('BASE_SHA', '')
    changed = None
    if re.fullmatch('[0-9a-f]{40}', base) and base != '0' * 40:
        diff = subprocess.run(['git', 'diff', '--name-only', base, 'HEAD'], capture_output=True, text=True)
        if diff.returncode == 0:
            changed = diff.stdout.splitlines()
    common = changed is None or any(p.startswith(('.github/', 'scripts/', 'tests/')) or p == 'requirements-dev.txt' for p in changed)
    values = {
        'engineering': common or any(p.startswith(('plugins/engineering/', 'evals/')) for p in changed or []),
        'dotnet': common or any(p.startswith('plugins/dotnet/') for p in changed or []),
    }
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
        for name, value in values.items():
            output.write(f'{name}={str(value).lower()}\n')


if __name__ == '__main__':
    main()
