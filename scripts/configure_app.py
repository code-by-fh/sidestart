"""Configure a new template before generating native platform directories."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

DEFAULT_CONFIG = {'projectName': 'sidestart', 'organization': 'dev.sidestart',
                  'displayName': 'SideStart'}
RESERVED = set('abstract as assert async augment await base break case catch class const '
               'continue covariant default deferred do dynamic else enum export extends '
               'extension external factory false final finally for Function get hide if '
               'implements import in interface is late library mixin new null of on '
               'operator part required rethrow return sealed set show static super switch '
               'sync this throw true try type typedef var void when while with yield '
               'flutter dart'.split())


def validate_config(config):
    if not isinstance(config, dict) or set(config) != set(DEFAULT_CONFIG):
        raise ValueError('app-config.json must contain projectName, organization and displayName')
    name, organization, display = (config[key] for key in DEFAULT_CONFIG)
    if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9_]*', name) or name in RESERVED:
        raise ValueError('Project name must be lowercase_with_underscores and not a Dart keyword')
    if not isinstance(organization, str) or not re.fullmatch(r'[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)+', organization):
        raise ValueError('Organization must be reverse DNS, such as dev.example (lowercase letters/digits)')
    if not isinstance(display, str) or not display.strip() or display != display.strip() or any(ord(c) < 32 for c in display):
        raise ValueError('Display name must be nonempty, trimmed text without control characters')
    return config


def load_config(root):
    path = Path(root) / 'app-config.json'
    return validate_config(json.loads(path.read_text(encoding='utf-8-sig')) if path.exists()
                           else dict(DEFAULT_CONFIG))


def dart_string(value):
    return "'" + value.replace('\\', '\\\\').replace("'", "\\'").replace('$', '\\$') + "'"


def configure(root, name, organization, display_name, repository=None):
    root = Path(root).resolve()
    config = validate_config({'projectName': name, 'organization': organization,
                              'displayName': display_name})
    old = load_config(root)
    if repository is not None and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}', repository):
        raise ValueError('Repository must be owner/repo')
    if config != old and any((root / platform).exists() for platform in ('ios', 'android', 'windows', 'web', 'macos', 'linux')):
        raise ValueError('Native platform directories already exist. Configure a fresh template before running bootstrap.py.')
    updates = {}
    pubspec = root / 'pubspec.yaml'
    original = pubspec.read_text(encoding='utf-8-sig')
    content, count = re.subn(r'^name:\s*' + re.escape(old['projectName']) + r'\s*$',
                             'name: ' + name, original, flags=re.MULTILINE)
    if count != 1:
        raise ValueError('pubspec.yaml name must match app-config.json before configuration')
    updates[pubspec] = content
    for directory in ('lib', 'test'):
        for path in (root / directory).rglob('*.dart'):
            text = path.read_text(encoding='utf-8-sig')
            text = text.replace('package:' + old['projectName'] + '/', 'package:' + name + '/')
            if path == root / 'lib/main.dart':
                old_literal, new_literal = dart_string(old['displayName']), dart_string(display_name)
                text = re.sub(r'(\btitle:\s*)' + re.escape(old_literal),
                              lambda match: match.group(1) + new_literal, text)
                text = re.sub(r'(\btitle:\s*(?:const\s+)?Text\(\s*)' + re.escape(old_literal),
                              lambda match: match.group(1) + new_literal, text)
            updates[path] = text
    updates[root / 'app-config.json'] = json.dumps(config, indent=2, ensure_ascii=False) + '\n'
    if repository is not None:
        updates[root / 'source-config.json'] = json.dumps({'repository': repository}, indent=2) + '\n'
    # Validate every destination before writing anything, including linked files.
    for path in updates:
        if not path.resolve().is_relative_to(root):
            raise ValueError('Configuration path resolves outside the project: ' + str(path))
    changed = []
    for path, text in updates.items():
        if not path.exists() or path.read_text(encoding='utf-8-sig') != text:
            path.write_text(text, encoding='utf-8')
            changed.append(str(path.relative_to(root)))
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--organization', required=True)
    parser.add_argument('--display-name', required=True)
    parser.add_argument('--repository')
    args = parser.parse_args()
    changed = configure(Path(__file__).resolve().parents[1], **vars(args))
    print('Updated: ' + ', '.join(changed) if changed else 'Configuration already matches.')
    print('Next: python scripts/bootstrap.py, then flutter pub get.')


if __name__ == '__main__':
    main()
