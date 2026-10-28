"""Shared repository contracts; these checks do not certify host compatibility."""
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
import yaml

ROOT = Path(__file__).resolve().parents[1]
INDEXES = ('marketplace.json', '.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json')
HOSTS = ('.zcode-plugin', '.claude-plugin', '.codex-plugin')
COMMON = ('name', 'version', 'description', 'author', 'license', 'keywords')
NAME = re.compile(r'[a-z0-9]+(?:[._-][a-z0-9]+)*\Z')
VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?\Z')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pairs(items):
    result = {}
    for key, value in items:
        require(isinstance(key, str), f'object key must be a string: {key!r}')
        require(key not in result, f'duplicate key: {key}')
        result[key] = value
    return result


class StrictLoader(yaml.SafeLoader):
    pass


def mapping(loader, node):
    loader.flatten_mapping(node)
    return pairs((loader.construct_object(k), loader.construct_object(v)) for k, v in node.value)


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def invalid_constant(value):
    raise ValueError(f'invalid JSON constant: {value}')


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_constant=invalid_constant)


def load_yaml(text):
    return yaml.load(text, Loader=StrictLoader)


def obj(value, label):
    require(type(value) is dict, f'{label}: expected object')
    return value


def string(value, label, limit=None):
    require(isinstance(value, str) and bool(value.strip()), f'{label}: expected nonblank string')
    if limit is not None:
        require(len(value) <= limit, f'{label}: exceeds {limit} characters')
    return value


def strings(value, label):
    require(type(value) is list, f'{label}: expected array')
    for entry in value:
        string(entry, label)
    require(len(value) == len(set(value)), f'{label}: duplicate entries')


def frontmatter(path):
    text = path.read_text(encoding='utf-8')
    match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
    require(match is not None, f'{path}: missing or unterminated YAML frontmatter')
    meta = obj(load_yaml(match[1]), str(path))
    require(bool(text[match.end():].strip()), f'{path}: empty instruction body')
    return meta


def contained(base, relative, label):
    string(relative, label)
    require(not Path(relative).is_absolute() and '\\' not in relative, f'{label}: expected relative POSIX path')
    target = (base / relative).resolve()
    require(target.is_relative_to(base.resolve()), f'{label}: path escapes package: {relative}')
    require(target.exists(), f'{label}: missing resource: {relative}')
    return target


def links(path, plugin):
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'(?ms)^```[^\n]*\n.*?^```[^\n]*$', '', text)
    targets = re.findall(r'\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\s*\)', text)
    targets += re.findall(r'(?m)^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)', text)
    targets += re.findall(r'`((?:\.\.?/)+(?:references|skills|assets)/[^`]+)`', text)
    targets += re.findall(r'`((?:\$\{CLAUDE_PLUGIN_ROOT\}/)?skills/[^`]+/SKILL\.md)`', text)
    result = set()
    for target in targets:
        target = target.strip('<>')
        if target.startswith('#'):
            continue
        base = path.parent
        if target.startswith('${CLAUDE_PLUGIN_ROOT}/'):
            target, base = target.removeprefix('${CLAUDE_PLUGIN_ROOT}/'), plugin
        elif target.startswith('skills/') and path.parent.name == 'commands':
            base = plugin
        parsed = urlsplit(target)
        if parsed.scheme in ('http', 'https', 'mailto'):
            continue
        require(not parsed.scheme and not parsed.netloc, f'{path}: unsupported resource URI: {target}')
        target_path = (base / unquote(parsed.path)).resolve()
        require(target_path.is_relative_to(plugin.resolve()), f'{path}: resource outside plugin: {target}')
        require(target_path.is_file(), f'{path}: missing resource: {target}')
        result.add(target_path)
    return result


def validate_plugin(plugin):
    require(len(plugin.name) <= 64 and NAME.fullmatch(plugin.name) is not None, f'invalid plugin name: {plugin.name}')
    for path in plugin.rglob('*'):
        require(not path.is_symlink(), f'symlink in package: {path}')
    manifests = []
    for host in HOSTS:
        manifest = obj(load_json(plugin / host / 'plugin.json'), host)
        for key in ('name', 'version', 'description', 'license'):
            string(manifest.get(key), f'{host}.{key}')
        require(manifest['name'] == plugin.name, f'{host}: plugin name/path mismatch')
        require(VERSION.fullmatch(manifest['version']), f'{host}: invalid SemVer')
        string(obj(manifest.get('author'), 'author').get('name'), 'author.name')
        strings(manifest.get('keywords'), 'keywords')
        if 'skills' in manifest:
            target = contained(plugin, manifest['skills'], 'manifest.skills')
            require(target == (plugin / 'skills').resolve(), 'manifest.skills must select packaged skills directory')
        if 'interface' in manifest:
            ui = obj(manifest['interface'], 'interface')
            for key in ('displayName', 'shortDescription', 'longDescription', 'developerName', 'category'):
                if key in ui:
                    string(ui[key], f'interface.{key}')
            if 'capabilities' in ui:
                strings(ui['capabilities'], 'interface.capabilities')
            if 'defaultPrompt' in ui:
                if isinstance(ui['defaultPrompt'], list):
                    require(1 <= len(ui['defaultPrompt']) <= 3, 'interface.defaultPrompt length')
                    strings(ui['defaultPrompt'], 'interface.defaultPrompt')
                else:
                    string(ui['defaultPrompt'], 'interface.defaultPrompt')
        manifests.append(manifest)
    for key in COMMON:
        require(all(m[key] == manifests[0][key] for m in manifests), f'manifest mismatch: {key}')
    skills = sorted((plugin / 'skills').glob('*/SKILL.md'))
    require(bool(skills), 'no skills/*/SKILL.md')
    directories = {p.name for p in (plugin / 'skills').iterdir() if p.is_dir()}
    require(directories == {p.parent.name for p in skills}, 'skill directory without SKILL.md')
    for path in skills:
        meta = frontmatter(path)
        name = string(meta.get('name'), 'skill.name', 64)
        require(name == path.parent.name and name == name.lower() and
                all(part.isalnum() for part in name.split('-')), f'invalid skill name/path: {name}')
        string(meta.get('description'), 'skill.description', 1024)
        for key in ('license', 'compatibility', 'allowed-tools'):
            if key in meta:
                string(meta[key], f'skill.{key}')
        if 'metadata' in meta:
            for key, value in obj(meta['metadata'], 'skill.metadata').items():
                string(value, f'skill.metadata.{key}')
        ui_path = path.parent / 'agents/openai.yaml'
        if ui_path.exists():
            data = obj(load_yaml(ui_path.read_text(encoding='utf-8')), 'openai.yaml')
            if 'interface' in data:
                ui = obj(data['interface'], 'interface')
                for key in ('display_name', 'short_description'):
                    string(ui.get(key), f'interface.{key}')
                if 'default_prompt' in ui:
                    prompt = string(ui['default_prompt'], 'default_prompt')
                    require(f'${name}' in prompt, f'default_prompt must invoke ${name}')
                for key in ('icon_small', 'icon_large'):
                    if key in ui:
                        contained(path.parent, ui[key], key)
            if 'policy' in data:
                policy = obj(data['policy'], 'policy')
                require(set(policy) <= {'allow_implicit_invocation', 'products'}, 'unsupported policy field')
                require(policy.get('allow_implicit_invocation') is None or
                        type(policy['allow_implicit_invocation']) is bool, 'allow_implicit_invocation must be boolean')
                if policy.get('products') is not None:
                    strings(policy['products'], 'policy.products')
                    require(set(policy['products']) <= {'CHAT', 'CODEX', 'HERMES'}, 'unknown product')
    for path in (plugin / 'commands').glob('*.md'):
        meta = frontmatter(path)
        string(meta.get('description'), 'command.description')
        if 'name' in meta:
            require(meta['name'] == path.stem, 'command name/path mismatch')
        for key in ('argument-hint', 'allowed-tools'):
            if key in meta:
                string(meta[key], f'command.{key}')
        targets = {p for p in links(path, plugin) if p.name == 'SKILL.md'}
        if path.stem in directories:
            require(targets == {(plugin / 'skills' / path.stem / 'SKILL.md').resolve()},
                    f'command must forward to matching skill: {path.stem}')
    for path in plugin.rglob('*.md'):
        links(path, plugin)
    return manifests[0]


def validate(root=ROOT):
    root = Path(root).resolve()
    errors, indexes, manifests = [], [], {}
    try:
        require((root / 'plugins').is_dir(), 'missing plugins directory')
        plugins = sorted(p for p in (root / 'plugins').iterdir() if p.is_dir())
        require(bool(plugins), 'empty plugins directory')
    except ValueError as error:
        return [str(error)]
    for plugin in plugins:
        try:
            require(not plugin.is_symlink(), f'symlink plugin: {plugin}')
            manifests[plugin.name] = validate_plugin(plugin)
        except (ValueError, OSError, yaml.YAMLError) as error:
            errors.append(f'{plugin.name}: {error}')
    for index in INDEXES:
        try:
            data = obj(load_json(root / index), index)
            string(data.get('name'), 'marketplace.name')
            string(data.get('description'), 'marketplace.description')
            entries = data.get('plugins')
            require(type(entries) is list and bool(entries), 'plugins must be nonempty array')
            names = set()
            for entry in entries:
                obj(entry, 'entry')
                name = string(entry.get('name'), 'entry.name', 64)
                require(NAME.fullmatch(name), f'invalid plugin name: {name}')
                require(name not in names, f'duplicate plugin: {name}')
                names.add(name)
                string(entry.get('description'), 'entry.description')
                version = string(entry.get('version'), 'entry.version')
                require(VERSION.fullmatch(version), f'invalid entry version: {version}')
                source = entry.get('source')
                if index == INDEXES[2]:
                    obj(source, 'Codex source')
                    require(source.get('source') == 'local', 'expected local Codex source')
                    source = source.get('path')
                else:
                    string(source, 'source')
                require(source == f'./plugins/{name}', f'source/name mismatch: {name}')
                contained(root, source, 'source')
                if name in manifests:
                    require(version == manifests[name]['version'], f'version mismatch: {name}')
                if 'tags' in entry:
                    strings(entry['tags'], 'tags')
                if 'category' in entry:
                    string(entry['category'], 'category')
                if 'policy' in entry:
                    policy = obj(entry['policy'], 'policy')
                    require(policy.get('installation') in ('AVAILABLE', 'INSTALLED_BY_DEFAULT', 'NOT_AVAILABLE'), 'invalid installation policy')
                    require(policy.get('authentication') in ('ON_INSTALL', 'ON_USE'), 'invalid authentication policy')
            require(names == {p.name for p in plugins}, 'marketplace/plugin directory set mismatch')
            indexes.append(data)
        except (ValueError, OSError, yaml.YAMLError) as error:
            errors.append(f'{index}: {error}')
    if len(indexes) == 3:
        if indexes[0] != indexes[1]:
            errors.append('ZCode/Claude marketplace contents differ')
        for key in ('name', 'description'):
            if len({data[key] for data in indexes}) != 1:
                errors.append(f'marketplace mismatch: {key}')
        baseline = {e['name']: (e['version'], e['description']) for e in indexes[0]['plugins']}
        for data in indexes[1:]:
            if {e['name']: (e['version'], e['description']) for e in data['plugins']} != baseline:
                errors.append('marketplace entry metadata mismatch')
    return errors
