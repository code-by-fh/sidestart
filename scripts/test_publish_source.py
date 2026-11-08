"""Exercise publication boundaries with a fake GitHub service; no network calls."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from publish_source import ensure_public_repository, publish, verify_public_downloads
import test_make_source


class FakeGitHub:
    def __init__(self, private=False, exists=True, empty=False):
        self.private, self.exists, self.empty = private, exists, empty
        self.calls = []
        self.uploaded_source = None

    def api(self, path, **kwargs):
        self.calls.append(('api', path, kwargs))
        if path == 'repos/example/downloads':
            if not self.exists:
                return None
            return {'private': self.private, 'default_branch': 'main'}
        if path.endswith('branches?per_page=1'):
            return [] if self.empty else [{'name': 'main'}]
        if path.endswith('contents/README.md'):
            self.empty = False
            return {}
        if path.endswith('releases/latest') or '/releases/tags/' in path:
            return None
        raise AssertionError(path)

    def run(self, *arguments, **kwargs):
        self.calls.append(('run', arguments, kwargs))
        if arguments[:2] == ('repo', 'create'):
            self.exists = True
        if arguments[:2] == ('release', 'upload'):
            source = next(Path(argument) for argument in arguments if argument.endswith('altstore-source.json'))
            self.uploaded_source = json.loads(source.read_text())
            for argument in arguments:
                if argument.endswith(('.ipa', '.png', '.json', '.sha256')):
                    if not Path(argument).is_file():
                        raise AssertionError(f'Missing upload: {argument}')
        return ''


class PublisherTests(unittest.TestCase):
    def setUp(self):
        fixture = test_make_source.SourceTests('test_metadata_matches_ipa')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.ipa = fixture.ipa

    def test_draft_upload_publish_order_and_correct_public_source(self):
        github = FakeGitHub()
        with patch('publish_source.verify_public_downloads') as verify, \
                contextlib.redirect_stdout(io.StringIO()):
            url = publish(self.ipa, 'example/downloads', github, target='a' * 40)
        calls = [call[1] for call in github.calls if call[0] == 'run']
        actions = [call[:2] for call in calls]
        self.assertLess(actions.index(('release', 'create')), actions.index(('release', 'upload')))
        self.assertLess(actions.index(('release', 'upload')), actions.index(('release', 'edit')))
        self.assertIn('--draft', calls[actions.index(('release', 'create'))])
        self.assertIn('a' * 40, calls[actions.index(('release', 'create'))])
        self.assertIn('--draft=false', calls[actions.index(('release', 'edit'))])
        self.assertEqual(url, 'https://github.com/example/downloads/releases/latest/download/altstore-source.json')
        self.assertEqual(github.uploaded_source['apps'][0]['versions'][0]['buildVersion'], '3')
        verify.assert_called_once()

    def test_private_repository_is_never_made_public(self):
        github = FakeGitHub(private=True)
        with self.assertRaisesRegex(RuntimeError, 'never changes repository visibility'):
            publish(self.ipa, 'example/downloads', github)
        self.assertFalse(any(call[0] == 'run' and call[1][:2] == ('release', 'create') for call in github.calls))
        self.assertFalse(any(call[0] == 'run' and '--visibility' in call[1] for call in github.calls))

    def test_missing_app_repository_does_not_create_an_extra_repository(self):
        github = FakeGitHub(exists=False, empty=True)
        with self.assertRaisesRegex(RuntimeError, 'Create an app repository from the template'):
            ensure_public_repository(github, 'example/downloads')
        self.assertFalse(any(call[0] == 'run' for call in github.calls))

    def test_anonymous_verification_checks_actual_ipa_bytes(self):
        ipa_bytes = self.ipa.read_bytes()
        source = {'apps': [{'iconURL': 'https://example.test/icon.png', 'versions': [{
            'version': '0.1.0', 'buildVersion': '3', 'downloadURL': 'https://example.test/app.ipa',
        }]}]}
        expected = {'version': '0.1.0', 'buildVersion': '3', 'size': len(ipa_bytes),
                    'sha256': hashlib.sha256(ipa_bytes).hexdigest()}
        with patch('publish_source.urllib.request.urlopen', side_effect=[
            io.BytesIO(json.dumps(source).encode()), io.BytesIO(ipa_bytes), io.BytesIO(b'\x89PNG\r\n\x1a\n'),
        ]) as request:
            verify_public_downloads('https://example.test/source.json', expected)
        for call in request.call_args_list:
            self.assertFalse(call.args[0].has_header('Authorization'))

    def test_corrupt_public_ipa_is_rejected(self):
        source = {'apps': [{'versions': [{'version': '0.1.0', 'buildVersion': '3',
                                         'downloadURL': 'https://example.test/app.ipa'}]}]}
        expected = {'version': '0.1.0', 'buildVersion': '3', 'size': 3, 'sha256': '0' * 64}
        with patch('publish_source.urllib.request.urlopen', side_effect=[
            io.BytesIO(json.dumps(source).encode()), io.BytesIO(b'bad'),
        ]):
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                verify_public_downloads('https://example.test/source.json', expected)


if __name__ == '__main__':
    unittest.main()
