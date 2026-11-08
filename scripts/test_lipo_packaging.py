"""Regression coverage for the lipo CLI contract and complete IPA packaging."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch
import zipfile

from package_ipa import package
import test_package_ipa


class LipoPackagingTests(unittest.TestCase):
    def setUp(self):
        fixture = test_package_ipa.PackagingTests('test_accept_complete_device_bundle')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.app = fixture.app
        self.output = fixture.root / 'dist/sidestart.ipa'

    def test_package_obeys_lipo_contract_and_writes_verified_archive(self):
        checked = []

        def native_tool(command, *, check):
            self.assertTrue(check)
            if command[0] == 'lipo':
                # -verify_arch consumes ALL subsequent arguments as architectures.
                # A filename placed after it is invalid in Apple's CLI.
                index = command.index('-verify_arch')
                self.assertEqual(index, 2, 'input must precede -verify_arch')
                self.assertEqual(command[index + 1:], ['arm64'])
                self.assertTrue(Path(command[1]).is_file())
                checked.append(Path(command[1]).name)
            elif command[0] == 'ditto' and '-c' not in command:
                shutil.copytree(command[-2], command[-1])
            elif command[0] == 'ditto':
                payload = Path(command[-2])
                with zipfile.ZipFile(command[-1], 'w') as archive:
                    for file in payload.rglob('*'):
                        if file.is_file():
                            archive.write(file, file.relative_to(payload.parent).as_posix())
            else:
                self.fail(f'Unexpected native command: {command}')

        with patch('package_ipa.sys.platform', 'darwin'), \
                patch('package_ipa.subprocess.run', side_effect=native_tool), \
                contextlib.redirect_stdout(io.StringIO()):
            package(self.app, self.output)

        self.assertEqual(checked, ['Runner', 'Flutter', 'App'])
        metadata = json.loads(self.output.with_suffix('.json').read_text())
        digest = hashlib.sha256(self.output.read_bytes()).hexdigest()
        self.assertEqual(metadata['sha256'], digest)
        self.assertEqual(metadata['size'], self.output.stat().st_size)
        self.assertIn(digest, self.output.with_suffix('.ipa.sha256').read_text())
        with zipfile.ZipFile(self.output) as archive:
            self.assertIn('Payload/Runner.app/Info.plist', archive.namelist())

    def test_bad_architecture_stops_before_ipa_creation(self):
        failure = subprocess.CalledProcessError(1, ['lipo'])
        with patch('package_ipa.sys.platform', 'darwin'), \
                patch('package_ipa.subprocess.run', side_effect=failure) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                package(self.app, self.output)
        self.assertEqual(run.call_count, 1)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
