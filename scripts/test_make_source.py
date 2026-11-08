import hashlib
import json
from pathlib import Path
import plistlib
import struct
import tempfile
import unittest
import zipfile

from make_source import ROOT, icon_png, make_source, read_entitlements


def macho(entitlements=None, der=False):
    if entitlements is None and not der:
        return struct.pack('<8I', 0xFEEDFACF, 0x0100000C, 0, 2, 0, 0, 0, 0)
    data = plistlib.dumps(entitlements or {})
    blob = struct.pack('>II', 0xFADE7171, len(data) + 8) + data
    if der:
        blob = struct.pack('>II', 0xFADE7172, 9) + b'x'
    signature = struct.pack('>IIIII', 0xFADE0CC0, 20 + len(blob), 1, 7 if der else 5, 20) + blob
    return (struct.pack('<8I', 0xFEEDFACF, 0x0100000C, 0, 2, 1, 16, 0, 0)
            + struct.pack('<4I', 0x1D, 16, 48, len(signature)) + signature)


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ipa = self.root / 'original.ipa'
        self.output = self.root / 'output'
        self.info = {'CFBundleIdentifier': 'dev.sidestart.sidestart',
                     'CFBundleShortVersionString': '0.1.0', 'CFBundleVersion': '3',
                     'MinimumOSVersion': '15.0', 'CFBundleExecutable': 'Runner',
                     'CFBundleSupportedPlatforms': ['iPhoneOS']}
        self.write_ipa()

    def write_ipa(self, extra=None, binary=None):
        with zipfile.ZipFile(self.ipa, 'w') as archive:
            archive.writestr(ROOT + 'Info.plist', plistlib.dumps(self.info))
            archive.writestr(ROOT + 'Runner', binary if binary is not None else macho())
            for name, value in (extra or {}).items():
                archive.writestr(name, value)

    def generate(self, **kwargs):
        return make_source(self.ipa, 'example/sidestart-downloads', self.output,
                           release_date='2026-11-08', **kwargs)

    def source(self):
        return json.loads((self.output / 'altstore-source.json').read_text())

    def test_metadata_matches_ipa(self):
        metadata = self.generate()
        app = self.source()['apps'][0]
        version = app['versions'][0]
        self.assertEqual(metadata['tag'], 'v0.1.0-build.3')
        self.assertEqual(version['version'], '0.1.0')
        self.assertEqual(version['buildVersion'], '3')
        self.assertEqual(version['minOSVersion'], '15.0')
        self.assertEqual(version['size'], self.ipa.stat().st_size)
        self.assertEqual(metadata['sha256'], hashlib.sha256(self.ipa.read_bytes()).hexdigest())
        self.assertIn('/download/v0.1.0-build.3/', version['downloadURL'])
        self.assertTrue(metadata['sourceURL'].endswith('/latest/download/altstore-source.json'))
        self.assertEqual(app['appPermissions'], {'entitlements': [], 'privacy': {}})

    def test_privacy_and_entitlements_from_binary(self):
        self.info['NSCameraUsageDescription'] = 'Scan a code.'
        self.write_ipa(binary=macho({'application-identifier': 'ABC.bundle',
                                    'com.apple.security.application-groups': ['group.test']}))
        self.generate()
        permissions = self.source()['apps'][0]['appPermissions']
        self.assertEqual(permissions['entitlements'], ['com.apple.security.application-groups'])
        self.assertEqual(permissions['privacy'], {'NSCameraUsageDescription': 'Scan a code.'})

    def test_reject_simulator(self):
        self.info['CFBundleSupportedPlatforms'] = ['iPhoneSimulator']
        self.write_ipa()
        with self.assertRaisesRegex(ValueError, 'device IPA'):
            self.generate()

    def test_reject_extensions_and_profiles(self):
        for path in ['PlugIns/Widget.appex/Info.plist', 'embedded.mobileprovision']:
            with self.subTest(path=path):
                self.write_ipa(extra={ROOT + path: b'test'})
                with self.assertRaisesRegex(ValueError, 'extensions/profiles'):
                    self.generate()

    def test_reject_unsafe_repository(self):
        for repository in ['https://github.com/owner/repo', 'owner/repo/extra', 'owner/../repo', 'a/b?x']:
            with self.subTest(repository=repository):
                with self.assertRaisesRegex(ValueError, 'owner/repo'):
                    make_source(self.ipa, repository, self.output)

    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            make_source(self.ipa, 'example/repo', self.output, release_date='2026-02-31')

    def test_history_preserved_and_deduplicated(self):
        self.generate()
        previous = self.root / 'previous.json'
        source = self.source()
        old = dict(source['apps'][0]['versions'][0], buildVersion='2')
        source['apps'][0]['versions'] += [old, old]
        previous.write_text(json.dumps(source))
        self.generate(previous=previous)
        self.assertEqual([v['buildVersion'] for v in self.source()['apps'][0]['versions']], ['3', '2'])

    def test_history_bundle_mismatch(self):
        self.generate()
        previous = self.root / 'previous.json'
        source = self.source()
        source['apps'][0]['bundleIdentifier'] = 'wrong.bundle'
        previous.write_text(json.dumps(source))
        with self.assertRaisesRegex(ValueError, 'bundle identifier'):
            self.generate(previous=previous)

    def test_reject_older_build(self):
        self.generate()
        previous = self.root / 'previous.json'
        source = self.source()
        source['apps'][0]['versions'][0]['buildVersion'] = '10'
        previous.write_text(json.dumps(source))
        with self.assertRaisesRegex(ValueError, 'older version/build'):
            self.generate(previous=previous)

    def test_same_input_and_output_directory(self):
        self.generate()
        target = self.output / 'sidestart-ios-unsigned.ipa'
        result = make_source(target, 'example/sidestart-downloads', self.output)
        self.assertEqual(result['size'], self.ipa.stat().st_size)

    def test_der_only_entitlements_rejected(self):
        with self.assertRaisesRegex(ValueError, 'DER-only'):
            read_entitlements(macho(der=True))

    def test_truncated_macho_rejected(self):
        with self.assertRaises(ValueError):
            read_entitlements(b'not macho')

    def test_png_header_and_dimensions(self):
        icon = icon_png()
        self.assertEqual(icon[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack_from('>II', icon, 16), (512, 512))


if __name__ == '__main__':
    unittest.main()
