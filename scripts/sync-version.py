#!/usr/bin/env python3
"""Synchronize one plugin's six version fields. --check/--diff never write."""
import argparse
import difflib
import json
import os
from pathlib import Path
import shutil
import tempfile
from validation import HOSTS, INDEXES, NAME, ROOT, VERSION, load_json, require, validate


def replace_value(text, path, value):
    """Locate a parsed JSON value without reformatting unrelated content."""
    decoder = json.JSONDecoder()
    position = 0
    def whitespace(index):
        while index < len(text) and text[index].isspace():
            index += 1
        return index
    for component in path:
        position = whitespace(position)
        position = whitespace(position + 1)  # enter object or array
        index = 0
        while True:
            if isinstance(component, str):
                key, end = decoder.raw_decode(text, position)
                position = whitespace(whitespace(end) + 1)  # colon
                matched = key == component
            else:
                matched = index == component
            if matched:
                break
            _, end = decoder.raw_decode(text, position)
            position = whitespace(whitespace(end) + 1)  # comma
            index += 1
    position = whitespace(position)
    _, end = decoder.raw_decode(text, position)
    return text[:position] + json.dumps(value) + text[end:]


def changes(root, name, version):
    require(NAME.fullmatch(name), 'invalid plugin name')
    require(VERSION.fullmatch(version), 'expected strict SemVer')
    result = {}
    for relative in [f'plugins/{name}/{host}/plugin.json' for host in HOSTS] + list(INDEXES):
        path = root / relative
        require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), 'symlink/escaping version file')
        data = load_json(path)
        if relative in INDEXES:
            entries = [(i, e) for i, e in enumerate(data['plugins']) if e['name'] == name]
            require(len(entries) == 1, f'{relative}: expected exactly one {name} entry')
            index, target = entries[0]
            key_path = ['plugins', index, 'version']
        else:
            require(data['name'] == name, f'{relative}: name mismatch')
            target = data
            key_path = ['version']
        if target['version'] == version:
            continue
        before = path.read_bytes()
        result[path] = (before, replace_value(before.decode('utf-8'), key_path, version).encode('utf-8'))
    # Validate the entire proposed repository before modifying any file.
    with tempfile.TemporaryDirectory(prefix='skills-version-') as temp:
        staged = Path(temp)
        shutil.copytree(root / 'plugins', staged / 'plugins', symlinks=True)
        for relative in INDEXES:
            (staged / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / relative, staged / relative)
        for path, (_, after) in result.items():
            (staged / path.relative_to(root)).write_bytes(after)
        errors = validate(staged)
        require(not errors, '\n'.join(errors))
    return result


def apply(changed):
    # Prepare every replacement before touching originals. Roll back on an I/O error.
    prepared, applied = {}, []
    try:
        for path, (before, after) in changed.items():
            require(path.read_bytes() == before, f'file changed concurrently: {path}')
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.version-', delete=False) as handle:
                prepared[path] = Path(handle.name)
                handle.write(after)
            os.chmod(prepared[path], path.stat().st_mode)
        for path, temporary in prepared.items():
            require(path.read_bytes() == changed[path][0], f'file changed concurrently: {path}')
            os.replace(temporary, path)
            applied.append(path)
    except Exception:
        for path in reversed(applied):
            path.write_bytes(changed[path][0])
        raise
    finally:
        for temporary in prepared.values():
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plugin')
    parser.add_argument('version')
    parser.add_argument('--root', type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='exit 1 if any field differs from target')
    mode.add_argument('--diff', action='store_true', help='show proposed differences without writing')
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        changed = changes(root, args.plugin, args.version)
        if args.diff:
            for path, (before, after) in changed.items():
                name = str(path.relative_to(root))
                print(''.join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True), name, name)), end='')
        elif args.check:
            print(f'{"FAIL" if changed else "PASS"}: {len(changed)} version file(s) need updating')
            return int(bool(changed))
        else:
            apply(changed)
            print(f'PASS: synchronized {args.plugin} to {args.version}; {len(changed)} file(s) changed')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'FAIL: {error}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
