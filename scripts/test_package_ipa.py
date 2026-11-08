import plistlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from package_ipa import inspect_bundle, validate_archive


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = self.root / 'Runner.app'
        self.app.mkdir()
        self.info = {'CFBundleExecutable': 'Runner',
                     'CFBundleIdentifier': 'dev.example.sidestart',
                     'CFBundleSupportedPlatforms': ['iPhoneOS']}
        self.write_info()
        for relative in ['Runner', 'Frameworks/Flutter.framework/Flutter',
                         'Frameworks/App.framework/App',
                         'Frameworks/App.framework/flutter_assets/AssetManifest.bin']:
            target = self.app / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'fixture')

    def write_info(self):
        (self.app / 'Info.plist').write_bytes(plistlib.dumps(self.info))

    def test_accept_complete_device_bundle(self):
        self.assertEqual(inspect_bundle(self.app), self.info)

    def test_reject_simulator(self):
        self.info['CFBundleSupportedPlatforms'] = ['iPhoneSimulator']
        self.write_info()
        with self.assertRaisesRegex(ValueError, 'device bundle'):
            inspect_bundle(self.app)

    def test_reject_missing_flutter_engine(self):
        (self.app / 'Frameworks/Flutter.framework/Flutter').unlink()
        with self.assertRaisesRegex(ValueError, 'Flutter release file'):
            inspect_bundle(self.app)

    def test_reject_debug_kernel(self):
        (self.app / 'Frameworks/App.framework/flutter_assets/kernel_blob.bin').touch()
        with self.assertRaisesRegex(ValueError, 'Debug Dart kernel'):
            inspect_bundle(self.app)

    def test_reject_executable_path_traversal(self):
        self.info['CFBundleExecutable'] = '../Runner'
        self.write_info()
        with self.assertRaisesRegex(ValueError, 'CFBundleExecutable'):
            inspect_bundle(self.app)

    def test_archive_layout(self):
        output = self.root / 'test.ipa'
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr('Payload/Runner.app/Info.plist', plistlib.dumps(self.info))
        validate_archive(output)

    def test_reject_incorrect_archive_root(self):
        output = self.root / 'test.ipa'
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr('Runner.app/Info.plist', b'fixture')
        with self.assertRaisesRegex(ValueError, 'Payload'):
            validate_archive(output)

    def test_reject_archive_traversal(self):
        output = self.root / 'test.ipa'
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr('Payload/Runner.app/Info.plist', b'fixture')
            archive.writestr('Payload/../evil', b'fixture')
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            validate_archive(output)


if __name__ == '__main__':
    unittest.main()
