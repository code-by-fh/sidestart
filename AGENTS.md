# Flutter sideload app template

- Use the Flutter SDK in `.fvmrc`; the starter has no third-party runtime packages.
- Configure a new template copy with `python scripts/configure_app.py --name ... --organization ... --display-name ...` before creating native platform directories. `app-config.json` is the central identity configuration.
- `python scripts/bootstrap.py` generates missing native projects and preserves existing ones.
- Run `python -m unittest discover -s scripts -p test_*.py`, `flutter pub get`, `flutter analyze` and `flutter test` after relevant changes. Report unavailable checks explicitly.
- iOS builds are unsigned release device builds. `scripts/package_ipa.py` packages them; `scripts/make_source.py` derives source metadata from the actual IPA.
- Minimum iOS version is 15.0. Adding native capabilities requires checking free-account signing support and source permissions.
- Never store Apple credentials, signing certificates or personal GitHub tokens in the repository or CI. The release job uses its provided GITHUB_TOKEN.
- `.github/workflows/builds.yml` publishes on main/master pushes and manual runs; PRs do not publish. Generated release tags must not trigger another workflow. Unconfigured template copies skip native builds and releases.
- Sources and versioned IPA downloads live in the app's own public GitHub repository. Preserve source history and immutable IPA bytes.
- Distinguish tests with fake native tools or fake GitHub responses from an actual native build and a signed iPhone installation.
