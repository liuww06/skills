import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validation import HOSTS, INDEXES, load_json, validate


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


sync = module('sync', 'sync-version.py')
refresh = module('refresh', 'update.py')


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        shutil.copytree(ROOT / 'plugins', self.root / 'plugins')
        for name in INDEXES:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def edit_json(self, name, edit):
        path = self.root / name
        data = load_json(path)
        edit(data)
        path.write_text(json.dumps(data), encoding='utf-8')

    def invalid(self, expected):
        errors = validate(self.root)
        self.assertTrue(errors)
        self.assertIn(expected, '\n'.join(errors))

    def test_existing_plugins_and_shared_references(self):
        self.assertEqual([], validate(self.root))

    def test_manifest_drift_each_host(self):
        for host in HOSTS:
            with self.subTest(host=host):
                path = self.root / f'plugins/dotnet/{host}/plugin.json'
                before = path.read_bytes()
                self.edit_json(str(path.relative_to(self.root)), lambda d: d.update(version='0.2.0'))
                self.invalid('manifest mismatch: version')
                path.write_bytes(before)

    def test_missing_skill_name(self):
        path = self.root / 'plugins/hello-world/skills/greeting/SKILL.md'
        path.write_text(path.read_text(encoding='utf-8').replace('name: greeting\n', ''), encoding='utf-8')
        self.invalid('skill.name')

    def test_duplicate_entries_each_marketplace(self):
        for name in INDEXES:
            with self.subTest(index=name):
                path = self.root / name
                before = path.read_bytes()
                self.edit_json(name, lambda d: d['plugins'].append(d['plugins'][0]))
                self.invalid('duplicate plugin')
                path.write_bytes(before)

    def test_wrong_json_types_and_constants(self):
        path = self.root / 'plugins/hello-world/.claude-plugin/plugin.json'
        original = path.read_text(encoding='utf-8')
        for payload in ('null', '[]', '{"name": NaN}', '{"name": Infinity}', '{"name": "a", "name": "b"}'):
            with self.subTest(payload=payload):
                path.write_text(payload, encoding='utf-8')
                self.assertTrue(validate(self.root))
        path.write_text(original, encoding='utf-8')
        for value in (None, True, [], {}, 1):
            with self.subTest(value=value):
                self.edit_json(str(path.relative_to(self.root)), lambda d: d.update(version=value))
                self.invalid('version: expected nonblank string')
                path.write_text(original, encoding='utf-8')

    def test_yaml_is_typed_and_rejects_duplicate_keys(self):
        path = self.root / 'plugins/hello-world/skills/greeting/SKILL.md'
        original = path.read_text(encoding='utf-8')
        for field in ('name: true', 'name: [greeting]', 'name: greeting\nname: other', 'description: {}'):
            with self.subTest(field=field):
                path.write_text('---\n' + field + '\n---\nBody', encoding='utf-8')
                self.assertTrue(validate(self.root))
        path.write_text(original, encoding='utf-8')

    def test_broken_and_escaping_links(self):
        path = self.root / 'plugins/hello-world/skills/greeting/SKILL.md'
        original = path.read_text(encoding='utf-8')
        for link in ('missing.md', '../../../../README.md', '%2e%2e/%2e%2e/%2e%2e/README.md', 'file:///etc/passwd'):
            with self.subTest(link=link):
                path.write_text(original + f'\n[resource]({link})\n', encoding='utf-8')
                self.assertTrue(validate(self.root))
        path.write_text(original, encoding='utf-8')

    def test_missing_shared_reference(self):
        (self.root / 'plugins/invest/references/data-sources.md').unlink()
        self.invalid('missing resource')

    def test_symlink_resource(self):
        path = self.root / 'plugins/hello-world/skills/greeting/escape.md'
        try:
            path.symlink_to(self.root / 'marketplace.json')
        except OSError:
            self.skipTest('symlink privilege unavailable')
        self.invalid('symlink')

    def test_command_target_drift(self):
        path = self.root / 'plugins/engineering/commands/bugfix.md'
        path.write_text(path.read_text(encoding='utf-8').replace('/bugfix/SKILL.md', '/repo-assess/SKILL.md'), encoding='utf-8')
        self.invalid('command must forward')

    def test_ui_prompt_and_boolean_types(self):
        path = self.root / 'plugins/engineering/skills/bugfix/agents/openai.yaml'
        original = path.read_text(encoding='utf-8')
        path.write_text(original + 'policy:\n  allow_implicit_invocation: "false"\n', encoding='utf-8')
        self.invalid('must be boolean')
        path.write_text(original.replace('$bugfix', '$missing'), encoding='utf-8')
        self.invalid('default_prompt must invoke')

    def test_source_escape_and_wrong_entry_type(self):
        for edit in (lambda d: d['plugins'][0].update(source='../outside'),
                     lambda d: d.update(plugins={}), lambda d: d['plugins'].append(None)):
            path = self.root / INDEXES[0]
            original = path.read_bytes()
            self.edit_json(INDEXES[0], edit)
            self.assertTrue(validate(self.root))
            path.write_bytes(original)

    def test_sync_six_versions_and_preserve_metadata(self):
        changed = sync.changes(self.root, 'dotnet', '1.2.3-rc.1+build.2')
        self.assertEqual(6, len(changed))
        for path, (before_bytes, after_bytes) in changed.items():
            self.assertEqual(1, after_bytes.count(b'1.2.3-rc.1+build.2'))
            self.assertEqual(before_bytes, after_bytes.replace(b'1.2.3-rc.1+build.2', b'0.1.0'))
        before = load_json(self.root / 'plugins/dotnet/.codex-plugin/plugin.json')
        sync.apply(changed)
        after = load_json(self.root / 'plugins/dotnet/.codex-plugin/plugin.json')
        self.assertEqual(before['interface'], after['interface'])
        self.assertEqual([], validate(self.root))
        self.assertEqual({}, sync.changes(self.root, 'dotnet', '1.2.3-rc.1+build.2'))

    def test_sync_repairs_drift(self):
        self.edit_json('plugins/dotnet/.codex-plugin/plugin.json', lambda d: d.update(version='0.9.0'))
        sync.apply(sync.changes(self.root, 'dotnet', '0.1.0'))
        self.assertEqual([], validate(self.root))

    def test_sync_preflight_no_partial_write(self):
        self.edit_json(INDEXES[0], lambda d: d['plugins'].append(d['plugins'][0]))
        path = self.root / 'plugins/dotnet/.claude-plugin/plugin.json'
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            sync.changes(self.root, 'dotnet', '0.2.0')
        self.assertEqual(before, path.read_bytes())

    def test_sync_rollback_io_failure(self):
        changed = sync.changes(self.root, 'dotnet', '0.2.0')
        original = sync.os.replace
        count = 0
        def fail_second(source, target):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError('simulated write failure')
            original(source, target)
        with patch.object(sync.os, 'replace', side_effect=fail_second):
            with self.assertRaises(OSError):
                sync.apply(changed)
        for path, (before, _) in changed.items():
            self.assertEqual(before, path.read_bytes())

    def test_check_and_diff_do_not_write(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*.json')}
        for flag, code in (('--check', 1), ('--diff', 0)):
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/sync-version.py'), 'dotnet', '0.2.0', '--root', str(self.root), flag], capture_output=True)
            self.assertEqual(code, result.returncode, result.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def refresh_fake(self, stream):
        worker = refresh.Refresh(self.root, self.root / 'logs')
        installed = [{'id': 'hello-world@leo-skills', 'enabled': True,
                      'installPath': str(self.root / 'plugins/hello-world')}]
        def run(*args, **kwargs):
            if args[:3] == ('plugin', 'marketplace', 'list'):
                return json.dumps([{'name': 'leo-skills', 'source': 'directory', 'path': str(self.root)}])
            if args[:2] == ('plugin', 'list'):
                return json.dumps(installed)
            return stream if args[0] == '-p' else ''
        with patch.object(worker, 'run', side_effect=run):
            return worker.execute(['hello-world'])

    def test_echo_marker_is_not_loading_evidence(self):
        rows = self.refresh_fake(json.dumps({'type':'result', 'subtype':'success', 'result':'VERIFY-OK-123'}))
        self.assertEqual('unverified', rows[0]['discovery_status'])
        self.assertEqual('unverified', rows[0]['task_status'])

    def test_host_metadata_is_discovery_only(self):
        rows = self.refresh_fake('\n'.join(map(json.dumps, [
            {'type':'system', 'subtype':'init', 'skills':['hello-world:greeting'], 'slash_commands':['hello-world:hello']},
            {'type':'result', 'subtype':'success'}])))
        self.assertEqual('passed', rows[0]['discovery_status'])
        self.assertEqual('unverified', rows[0]['task_status'])

    def test_missing_or_malformed_discovery_evidence_is_unverified(self):
        for skills in (None, {}, ['hello-world:greeting']):
            with self.subTest(skills=skills):
                rows = self.refresh_fake('\n'.join(map(json.dumps, [
                    {'type':'system', 'subtype':'init', 'skills':skills},
                    {'type':'result', 'subtype':'success'}])))
                self.assertEqual('unverified', rows[0]['discovery_status'])

    def test_nonzero_with_marker_is_error(self):
        worker = refresh.Refresh(self.root, self.root / 'logs')
        completed = subprocess.CompletedProcess(['claude'], 7, 'VERIFY-OK-123', 'failure')
        with patch.object(refresh.subprocess, 'run', return_value=completed):
            with self.assertRaisesRegex(RuntimeError, 'exit 7'):
                worker.run('-p', 'probe')

    def test_host_error_event_not_success(self):
        with self.assertRaisesRegex(ValueError, 'host reported an error'):
            self.refresh_fake(json.dumps({'type':'result','is_error': True, 'result':'VERIFY-OK-123'}))


if __name__ == '__main__':
    unittest.main()
