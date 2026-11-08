import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from configure_app import configure, load_config
from bootstrap import bootstrap


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'lib').mkdir()
        (self.root / 'test').mkdir()
        (self.root / 'pubspec.yaml').write_text('name: sidestart\nversion: 0.1.0+1\n')
        (self.root / 'lib/main.dart').write_text(
            "import 'package:sidestart/model.dart';\n"
            "MaterialApp(title: 'SideStart', home: Text('Keep me'));\n"
            "AppBar(title: const Text('SideStart'));\n")
        (self.root / 'test/widget_test.dart').write_text("import 'package:sidestart/main.dart';\n")

    def apply(self, **kwargs):
        values = dict(name='my_app', organization='dev.example', display_name='My App')
        values.update(kwargs)
        return configure(self.root, **values)

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_updates_project_imports_and_titles(self):
        self.apply(repository='example/my-app')
        self.assertIn('name: my_app\n', (self.root / 'pubspec.yaml').read_text())
        main = (self.root / 'lib/main.dart').read_text()
        self.assertIn('package:my_app/model.dart', main)
        self.assertEqual(main.count("'My App'"), 2)
        self.assertIn("Text('Keep me')", main)
        self.assertIn('package:my_app/main.dart', (self.root / 'test/widget_test.dart').read_text())
        self.assertEqual(json.loads((self.root / 'source-config.json').read_text()), {'repository': 'example/my-app'})
        self.assertEqual(load_config(self.root)['organization'], 'dev.example')

    def test_dart_display_name_is_escaped(self):
        self.apply(display_name="Jo's $App\\Test")
        self.assertIn(r"'Jo\'s \$App\\Test'", (self.root / 'lib/main.dart').read_text())

    def test_invalid_inputs_do_not_change_files(self):
        before = self.snapshot()
        for values in [dict(name='../bad'), dict(name='class'), dict(name='MyApp'),
                       dict(organization='example'), dict(organization='dev.bad-name'),
                       dict(display_name=''), dict(display_name='bad\nname'),
                       dict(repository='https://github.com/a/b')]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.apply(**values)
            self.assertEqual(self.snapshot(), before)

    def test_existing_native_project_refused_without_writes(self):
        (self.root / 'ios').mkdir()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'already exist'):
            self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_idempotent_and_same_configuration_allowed_after_generation(self):
        self.apply()
        (self.root / 'ios').mkdir()
        self.assertEqual(self.apply(), [])

    def test_pubspec_mismatch_refused_before_writes(self):
        (self.root / 'pubspec.yaml').write_text('name: different\n')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'pubspec.yaml'):
            self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_bootstrap_passes_configured_identity_to_flutter(self):
        self.apply()
        def generate(command, **kwargs):
            self.assertIn('--org=dev.example', command)
            self.assertIn('--project-name=my_app', command)
            scaffold = Path(command[-1])
            self.assertEqual(scaffold.name, 'my_app')
            (scaffold / 'web').mkdir(parents=True)
            (scaffold / 'web/index.html').write_text('<title>my_app</title>')
            (scaffold / 'web/manifest.json').write_text('{}')
        with patch('bootstrap.subprocess.run', side_effect=generate):
            bootstrap(self.root, ['web'], 'flutter')
        self.assertEqual((self.root / 'web/index.html').read_text(), '<title>My App</title>')
        self.assertEqual(json.loads((self.root / 'web/manifest.json').read_text())['name'], 'My App')


if __name__ == '__main__':
    unittest.main()
