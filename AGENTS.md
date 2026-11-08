# SideStart

- Use the exact Flutter version in `.fvmrc`; the app has no third-party runtime packages.
- Run `python scripts/bootstrap.py` to generate missing native platform directories from that SDK. Existing native directories are preserved and should be committed after generation.
- Run `flutter pub get`, `flutter analyze`, `flutter test` and `python -m unittest discover -s scripts -p test_*.py` after relevant changes.
- iOS uses a release device build with `--no-codesign`, then `scripts/package_ipa.py`. A simulator build cannot be sideloaded.
- Keep Apple credentials and signing certificates outside the repository and CI. The user signs the IPA using their sideloader.
- Minimum iOS version is 15.0. Adding plugins or Apple capabilities requires checking compatibility with free-account signing.
- Distinguish tested Python packaging logic, a successful real native build, and an actual iPhone installation test in reports.
- The build workflow is `.github/workflows/builds.yml`. Pushes create artifacts; matching `v<pubspec-version>` tags create releases.
