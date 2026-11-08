"""Build an AltStore Classic/SideStore source from a minimal Flutter device IPA.

Source schema: https://faq.altstore.io/developers/make-a-source
Only a single app without extensions or provisioning profiles is supported.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import plistlib
import re
import shutil
import struct
import zipfile
import zlib

IPA_NAME = 'sidestart-ios-unsigned.ipa'
ROOT = 'Payload/Runner.app/'


def read_entitlements(binary: bytes) -> list[str]:
    """Read XML entitlement keys from an arm64 Mach-O, or fail closed."""
    if len(binary) < 32 or binary[:4] != b'\xcf\xfa\xed\xfe':
        raise ValueError('Expected a thin arm64 Mach-O executable')
    _, cpu, _, _, ncmds, command_bytes, _, _ = struct.unpack_from('<8I', binary)
    if cpu != 0x0100000C or 32 + command_bytes > len(binary):
        raise ValueError('Invalid arm64 Mach-O load commands')
    position = 32
    for _ in range(ncmds):
        if position + 8 > 32 + command_bytes:
            raise ValueError('Truncated Mach-O load commands')
        command, size = struct.unpack_from('<II', binary, position)
        if size < 8 or position + size > 32 + command_bytes:
            raise ValueError('Invalid Mach-O command size')
        if command == 0x1D:  # LC_CODE_SIGNATURE
            if size < 16:
                raise ValueError('Truncated code signature command')
            offset, length = struct.unpack_from('<II', binary, position + 8)
            signature = binary[offset:offset + length]
            if len(signature) != length or length < 12:
                raise ValueError('Truncated code signature')
            magic, total, count = struct.unpack_from('>III', signature)
            if magic != 0xFADE0CC0 or total > len(signature) or 12 + count * 8 > total:
                raise ValueError('Unsupported code signature format')
            xml = None
            der = False
            for index in range(count):
                slot, start = struct.unpack_from('>II', signature, 12 + index * 8)
                if start + 8 > total:
                    raise ValueError('Invalid signature blob offset')
                blob_magic, blob_size = struct.unpack_from('>II', signature, start)
                if blob_size < 8 or start + blob_size > total:
                    raise ValueError('Invalid signature blob size')
                if slot == 5:
                    if blob_magic != 0xFADE7171:
                        raise ValueError('Unsupported XML entitlement blob')
                    xml = plistlib.loads(signature[start + 8:start + blob_size])
                if slot == 7:
                    der = True
            if der and xml is None:
                raise ValueError('DER-only entitlements require a publisher update')
            if xml is not None and not isinstance(xml, dict):
                raise ValueError('Entitlements must be a dictionary')
            implicit = {'application-identifier', 'com.apple.developer.team-identifier',
                        'com.app.developer.team-identifier'}
            return sorted(key for key in (xml or {}) if key not in implicit)
        position += size
    return []


def inspect_ipa(path: Path) -> tuple[dict, dict]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP entries are not supported')
        for name in names:
            parts = PurePosixPath(name).parts
            if '..' in parts or name.startswith('/') or '\\' in name:
                raise ValueError('Unsafe IPA archive path')
            if name.startswith('Payload/') and not name.startswith(ROOT):
                if name != 'Payload/':
                    raise ValueError('Expected one Runner.app bundle')
            if ('PlugIns' in parts or any(p.endswith('.appex') for p in parts)
                    or name.endswith('embedded.mobileprovision')
                    or name.endswith('.entitlements')):
                raise ValueError('Only minimal apps without extensions/profiles are supported')
        if archive.testzip() is not None:
            raise ValueError('Corrupt IPA archive')
        info = plistlib.loads(archive.read(ROOT + 'Info.plist'))
        if info.get('CFBundleSupportedPlatforms') != ['iPhoneOS']:
            raise ValueError('Expected an iPhoneOS device IPA')
        for key in ('CFBundleIdentifier', 'CFBundleShortVersionString',
                    'CFBundleVersion', 'MinimumOSVersion', 'CFBundleExecutable'):
            if not isinstance(info.get(key), str) or not info[key]:
                raise ValueError('Missing IPA metadata: ' + key)
        for key in ('CFBundleShortVersionString', 'CFBundleVersion', 'MinimumOSVersion'):
            if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*', info[key]):
                raise ValueError('Unsupported numeric version: ' + key)
        if not re.fullmatch(r'[A-Za-z0-9.-]+', info['CFBundleIdentifier']):
            raise ValueError('Invalid bundle identifier')
        executable = info['CFBundleExecutable']
        if '/' in executable or '\\' in executable or executable in ('.', '..'):
            raise ValueError('Invalid executable name')
        entitlements = read_entitlements(archive.read(ROOT + executable))
        privacy = {key: value for key, value in info.items() if 'UsageDescription' in key}
        if any(not isinstance(value, str) for value in privacy.values()):
            raise ValueError('Privacy descriptions must be strings')
        return info, {'entitlements': entitlements, 'privacy': privacy}


def icon_png() -> bytes:
    """A small deterministic PNG icon; no imaging dependency required."""
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    pixels = bytearray()
    for y in range(512):
        pixels.append(0)  # PNG scanline filter: none
        for x in range(512):
            plus = (224 <= x < 288 and 128 <= y < 384) or (128 <= x < 384 and 224 <= y < 288)
            pixels.extend((99, 230, 203) if plus else (16, 24, 29))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 512, 512, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(pixels, 9)) + chunk(b'IEND', b''))


def make_source(ipa: Path, repository: str, output_dir: Path,
                previous: Path | None = None, release_date: str | None = None) -> dict:
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}', repository):
        raise ValueError('Repository must be owner/repo, without URL or extra path')
    release_date = release_date or datetime.now(timezone.utc).date().isoformat()
    date.fromisoformat(release_date)
    info, permissions = inspect_ipa(ipa)
    version, build = info['CFBundleShortVersionString'], info['CFBundleVersion']
    tag = f'v{version}-build.{build}'
    base = f'https://github.com/{repository}'
    source_url = base + '/releases/latest/download/altstore-source.json'
    icon_url = base + '/releases/latest/download/icon.png'
    download_url = f'{base}/releases/download/{tag}/{IPA_NAME}'
    digest = hashlib.sha256(ipa.read_bytes()).hexdigest()
    display_name = info.get('CFBundleDisplayName') or info.get('CFBundleName') or 'SideStart'
    if not isinstance(display_name, str):
        raise ValueError('The app display name must be a string')
    entry = {'version': version, 'buildVersion': build, 'date': release_date,
             'localizedDescription': f'{display_name} {version} ({build}).',
             'downloadURL': download_url, 'size': ipa.stat().st_size,
             'minOSVersion': info['MinimumOSVersion']}
    history = []
    if previous is not None:
        old = json.loads(previous.read_text(encoding='utf-8-sig'))
        apps = old.get('apps', [])
        if len(apps) != 1 or apps[0].get('bundleIdentifier') != info['CFBundleIdentifier']:
            raise ValueError('Previous source bundle identifier does not match this IPA')
        if old.get('sourceURL') != source_url:
            raise ValueError('Previous source repository does not match this publication')
        def numeric(value):
            if not isinstance(value, str) or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*', value):
                raise ValueError('Previous source has invalid numeric version metadata')
            parts = [int(part) for part in value.split('.')]
            while len(parts) > 1 and parts[-1] == 0:
                parts.pop()
            return tuple(parts)
        current = (numeric(version), numeric(build))
        seen = {(version, build)}
        for item in apps[0].get('versions', []):
            if (numeric(item['version']), numeric(item['buildVersion'])) > current:
                raise ValueError('Refusing to publish an older version/build than the previous source')
            identity = (item['version'], item['buildVersion'])
            if identity not in seen:
                history.append(item)
                seen.add(identity)
    description = 'A minimal offline counter app. Install and refresh with SideStore or AltStore Classic.'
    app = {'name': display_name, 'bundleIdentifier': info['CFBundleIdentifier'],
           'developerName': repository.split('/')[0], 'localizedDescription': description,
           'iconURL': icon_url, 'tintColor': '63E6CB', 'category': 'utilities',
           'versions': [entry] + history, 'appPermissions': permissions}
    source = {'name': display_name, 'identifier': info['CFBundleIdentifier'] + '.source',
              'sourceURL': source_url, 'subtitle': f'{display_name} for SideStore and AltStore Classic',
              'description': description, 'iconURL': icon_url, 'website': base,
              'tintColor': '63E6CB', 'apps': [app], 'news': []}
    metadata = {'tag': tag, 'repository': repository, 'sourceURL': source_url,
                'downloadURL': download_url, 'file': IPA_NAME, 'sha256': digest,
                'size': ipa.stat().st_size, 'bundleIdentifier': info['CFBundleIdentifier'],
                'version': version, 'buildNumber': build, 'minimumOSVersion': info['MinimumOSVersion']}
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / IPA_NAME
    if target.resolve() != ipa.resolve():
        shutil.copy2(ipa, target)
    (output_dir / 'altstore-source.json').write_text(json.dumps(source, indent=2) + '\n', encoding='utf-8')
    (output_dir / 'release-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    (output_dir / (IPA_NAME + '.sha256')).write_text(f'{digest}  {IPA_NAME}\n', encoding='utf-8')
    (output_dir / 'icon.png').write_bytes(icon_png())
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ipa', type=Path, required=True)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--date', dest='release_date')
    args = parser.parse_args()
    print(json.dumps(make_source(**vars(args)), indent=2))


if __name__ == '__main__':
    main()
