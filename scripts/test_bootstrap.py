"""Test platform generation isolation and preservation without needing Flutter."""

import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bootstrap import bootstrap, configure_ios


class BootstrapTests(unittest.TestCase):
    def test_existing_platform_and_app_source_are_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "web").mkdir()
            (root / "web/index.html").write_text("custom", encoding="utf-8")
            (root / "pubspec.yaml").write_text("custom", encoding="utf-8")
            with patch("bootstrap.subprocess.run") as run:
                self.assertEqual(bootstrap(root, ["web"], "flutter"), [])
                run.assert_not_called()
            self.assertEqual((root / "web/index.html").read_text(), "custom")
            self.assertEqual((root / "pubspec.yaml").read_text(), "custom")

    def test_partial_platform_is_reported_instead_of_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "ios").mkdir()
            with self.assertRaisesRegex(RuntimeError, "Incomplete ios"):
                bootstrap(root, ["ios"], "flutter")

    def test_scaffold_generated_outside_root_only_platforms_copied(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "lib").mkdir()
            (root / "lib/main.dart").write_text("my app", encoding="utf-8")

            def fake_flutter(command, **kwargs):
                scaffold = Path(command[-1])
                self.assertFalse(scaffold.is_relative_to(root))
                (scaffold / "web").mkdir(parents=True)
                (scaffold / "web/index.html").write_text("web", encoding="utf-8")
                (scaffold / "pubspec.yaml").write_text("wrong", encoding="utf-8")
                (scaffold / ".metadata").write_text("metadata", encoding="utf-8")

            with patch("bootstrap.subprocess.run", side_effect=fake_flutter):
                self.assertEqual(bootstrap(root, ["web"], "flutter"), ["web"])
            self.assertEqual((root / "lib/main.dart").read_text(), "my app")
            self.assertFalse((root / "pubspec.yaml").exists())
            self.assertEqual((root / "web/index.html").read_text(), "web")

    def test_ios_name_and_minimum_version_configured_together(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Runner.xcodeproj").mkdir()
            project = root / "Runner.xcodeproj/project.pbxproj"
            project.write_text("IPHONEOS_DEPLOYMENT_TARGET = 13.0;", encoding="utf-8")
            for name in ["Runner/Info.plist", "Flutter/AppFrameworkInfo.plist"]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("wb") as stream:
                    plistlib.dump({"MinimumOSVersion": "13.0"}, stream)
            configure_ios(root)
            self.assertIn("15.0", project.read_text())
            with (root / "Runner/Info.plist").open("rb") as stream:
                self.assertEqual(plistlib.load(stream)["CFBundleDisplayName"], "SideStart")
            with (root / "Flutter/AppFrameworkInfo.plist").open("rb") as stream:
                self.assertEqual(plistlib.load(stream)["MinimumOSVersion"], "15.0")


if __name__ == "__main__":
    unittest.main()
