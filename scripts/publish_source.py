"""Publish an unsigned iOS app and SideStore source in its public GitHub repository."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request

from make_source import make_source


class GitHubError(RuntimeError):
    def __init__(self, arguments, result):
        self.missing = 'HTTP 404' in result.stderr
        try:
            self.missing |= str(json.loads(result.stdout).get('status')) == '404'
        except (ValueError, AttributeError):
            pass
        super().__init__(f"gh {' '.join(arguments)} failed:\n{result.stderr.strip()}")


class GitHub:
    def run(self, *arguments, data=None):
        result = subprocess.run(
            ['gh', *arguments], input=json.dumps(data) if data is not None else None,
            capture_output=True, text=True, encoding='utf-8',
            cwd=Path(__file__).resolve().parents[1],
        )
        if result.returncode:
            raise GitHubError(arguments, result)
        return result.stdout

    def api(self, path, *, method='GET', data=None, missing_ok=False):
        arguments = ['api', path, '--method', method]
        if data is not None:
            arguments.extend(['--input', '-'])
        try:
            return json.loads(self.run(*arguments, data=data))
        except GitHubError as error:
            if missing_ok and error.missing:
                return None
            raise


def ensure_public_repository(github, repository):
    endpoint = f'repos/{repository}'
    info = github.api(endpoint, missing_ok=True)
    if info is None:
        raise RuntimeError(f'{repository} does not exist. Create an app repository from the template first.')
    if info['private']:
        raise RuntimeError(
            f'{repository} is private. Make the app repository public before publishing. '
            'This script never changes repository visibility.'
        )
    return info['default_branch']


def anonymous_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'SideStart-source-publisher/1.0'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def verify_public_downloads(source_url, expected):
    """Verify via HTTPS without passing GitHub CLI credentials to requests."""
    source = anonymous_json(source_url + '?check=' + str(time.time_ns()))
    version = source['apps'][0]['versions'][0]
    if (version['version'], version['buildVersion']) != (expected['version'], expected['buildVersion']):
        raise ValueError('The public source does not yet describe the selected IPA.')
    digest = hashlib.sha256()
    length = 0
    request = urllib.request.Request(version['downloadURL'], headers={
        'User-Agent': 'SideStart-source-publisher/1.0',
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        for chunk in iter(lambda: response.read(1024 * 1024), b''):
            digest.update(chunk)
            length += len(chunk)
    if length != expected['size'] or digest.hexdigest() != expected['sha256']:
        raise ValueError('Public IPA size or SHA-256 does not match the local file.')
    request = urllib.request.Request(source['apps'][0]['iconURL'])
    with urllib.request.urlopen(request, timeout=45) as response:
        if response.read(8) != b'\x89PNG\r\n\x1a\n':
            raise ValueError('The public source icon is not a PNG.')


def generate(ipa, repository, output, previous=None):
    make_source(ipa, repository, output, previous=previous)
    return json.loads((output / 'altstore-source.json').read_text(encoding='utf-8'))


def publish(ipa, repository, github=None, target=None):
    github = github or GitHub()
    with tempfile.TemporaryDirectory(prefix='sidestart-source-') as temporary:
        staging = Path(temporary)
        output = staging / 'release'
        current = generate(ipa, repository, output)
        version = current['apps'][0]['versions'][0]
        tag = f"v{version['version']}-build.{version['buildVersion']}"
        source_url = f'https://github.com/{repository}/releases/latest/download/altstore-source.json'
        expected = {
            'version': version['version'], 'buildVersion': version['buildVersion'],
            'size': ipa.stat().st_size, 'sha256': hashlib.sha256(ipa.read_bytes()).hexdigest(),
        }
        github.run('auth', 'status')
        branch = ensure_public_repository(github, repository)
        latest = github.api(f'repos/{repository}/releases/latest', missing_ok=True)
        if latest is not None:
            previous_dir = staging / 'previous'
            previous_dir.mkdir()
            github.run('release', 'download', latest['tag_name'], '--repo', repository,
                       '--pattern', 'altstore-source.json', '--dir', str(previous_dir))
            previous_path = previous_dir / 'altstore-source.json'
            current = generate(ipa, repository, output, previous_path)

        existing = github.api(f'repos/{repository}/releases/tags/{tag}', missing_ok=True)
        if existing is not None and not existing['draft']:
            checksums = staging / 'existing'
            checksums.mkdir()
            github.run('release', 'download', tag, '--repo', repository,
                       '--pattern', 'sidestart-ios-unsigned.ipa.sha256', '--dir', str(checksums))
            old_digest = (checksums / 'sidestart-ios-unsigned.ipa.sha256').read_text().split()[0]
            if old_digest != expected['sha256']:
                raise ValueError('This version/build already exists with different IPA bytes. Increase the build number.')
            print('The identical IPA is already published; keeping immutable release files.')
        else:
            if existing is None:
                github.run('release', 'create', tag, '--repo', repository, '--draft',
                           '--target', target or branch, '--title', f"{current['apps'][0]['name']} {version['version']} ({version['buildVersion']})",
                           '--notes', 'Unsigned iOS app. Add the source URL to SideStore or AltStore Classic: ' + source_url)
            assets = [str(output / name) for name in (
                'sidestart-ios-unsigned.ipa', 'sidestart-ios-unsigned.ipa.sha256',
                'altstore-source.json', 'icon.png',
            )]
            github.run('release', 'upload', tag, '--repo', repository, '--clobber', *assets)
            github.run('release', 'edit', tag, '--repo', repository, '--draft=false', '--latest')
        print('Checking that source, IPA and icon are reachable without signing in...')
        for attempt in range(4):
            try:
                verify_public_downloads(source_url, expected)
                break
            except (OSError, ValueError, KeyError):
                if attempt == 3:
                    print(f'Published, but anonymous verification failed. Check this URL: {source_url}')
                    raise
                time.sleep(5)
        print('\nSource verified. Paste this URL into SideStore > Sources > Add Source:\n' + source_url)
        return source_url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository')
    parser.add_argument('--ipa', type=Path)
    parser.add_argument('--target', help='Exact source commit represented by this IPA')
    args = parser.parse_args()
    if args.repository is None:
        args.repository = GitHub().run('repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner').strip()
    if not shutil.which('gh'):
        parser.error('GitHub CLI is missing. Install gh and run gh auth login.')
    ipa = args.ipa
    if ipa is None:
        candidates = list((Path(__file__).resolve().parents[1] / 'downloads').rglob('sidestart-ios-unsigned.ipa'))
        if not candidates:
            parser.error('No downloaded IPA found. Run publish.ps1 first or pass --ipa <path>.')
        ipa = max(candidates, key=lambda path: path.stat().st_mtime)
    print(f'Publishing IPA: {ipa}')
    publish(ipa.resolve(), args.repository, target=args.target)


if __name__ == '__main__':
    main()
