#!/usr/bin/env python3
"""Validate packaged skills and all three marketplace indexes."""
import argparse
import sys
from pathlib import Path
from validation import ROOT, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        print('\n'.join(f'FAIL: {error}' for error in errors), file=sys.stderr)
        return 1
    print('PASS: plugin manifests, skill/command metadata, local resources and three marketplaces')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
