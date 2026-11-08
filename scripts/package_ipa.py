"""Validate and package an unsigned Flutter device release on macOS."""
import argparse
import hashlib
import json
import plistlib
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def inspect_bundle(app):
    app = Path(app)
    with (app / 'Info.plist').open('rb') as stream:
        info = plistlib.load(stream)
    executable = info.get('CFBundleExecutable', '')
    if not executable or Path(executable).name != executable:
        raise ValueError('Invalid CFBundleExecutable')
    required = [executable, 'Frameworks/Flutter.framework/Flutter',
                'Frameworks/App.framework/App',
                'Frameworks/App.framework/flutter_assets/AssetManifest.bin']
    for relative in required:
        path = app / relative
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f'Missing or empty Flutter release file: {relative}')
    if info.get('CFBundleSupportedPlatforms') != ['iPhoneOS']:
        raise ValueError('Expected an iPhoneOS device bundle, not a simulator build')
    if not info.get('CFBundleIdentifier'):
        raise ValueError('Missing CFBundleIdentifier')
    assets = app / 'Frameworks/App.framework/flutter_assets'
    if (assets / 'kernel_blob.bin').exists():
        raise ValueError('Debug Dart kernel found; build with --release')
    return info


def validate_archive(path):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('Corrupt IPA archive')
        names = archive.namelist()
        if not names or any(not name.startswith('Payload/') for name in names):
            raise ValueError('IPA must contain only a top-level Payload directory')
        if 'Payload/Runner.app/Info.plist' not in names:
            raise ValueError('IPA is missing Payload/Runner.app/Info.plist')
        for name in names:
            if '..' in Path(name).parts or name.startswith('/'):
                raise ValueError('Unsafe archive path')


def package(app, output):
    app, output = Path(app).resolve(), Path(output).resolve()
    info = inspect_bundle(app)
    if sys.platform != 'darwin':
        raise RuntimeError('IPA packaging requires macOS (ditto and lipo)')
    # Reject Intel/simulator artifacts and require actual arm64 Mach-O binaries.
    for binary in [app / info['CFBundleExecutable'],
                   app / 'Frameworks/Flutter.framework/Flutter',
                   app / 'Frameworks/App.framework/App']:
        subprocess.run(['lipo', '-verify_arch', 'arm64', str(binary)], check=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sidestart-ipa-') as staging:
        payload = Path(staging) / 'Payload'
        payload.mkdir()
        subprocess.run(['ditto', '--norsrc', str(app), str(payload / 'Runner.app')], check=True)
        subprocess.run(['ditto', '-c', '-k', '--keepParent', '--norsrc',
                        str(payload), str(output)], check=True)
    validate_archive(output)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + '.sha256').write_text(
        f'{digest}  {output.name}\n', encoding='utf-8')
    metadata = {'file': output.name, 'sha256': digest, 'size': output.stat().st_size,
                'bundleIdentifier': info['CFBundleIdentifier'],
                'version': info.get('CFBundleShortVersionString'),
                'buildNumber': info.get('CFBundleVersion'),
                'minimumOSVersion': info.get('MinimumOSVersion'),
                'signing': 'unsigned; sign with your sideloader before installation'}
    output.with_suffix('.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', default='build/ios/iphoneos/Runner.app')
    parser.add_argument('--output', default='dist/sidestart-ios-unsigned.ipa')
    args = parser.parse_args()
    package(args.app, args.output)
