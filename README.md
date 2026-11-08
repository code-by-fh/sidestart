# SideStart

A Flutter starter and GitHub template for iOS, Android, Windows, and web apps. GitHub Actions builds an unsigned iOS device app, publishes the IPA and source JSON in this repository, and attaches the Android APK to the same release. License: [MIT](LICENSE).

## Install SideStart

After a successful release, add this source in SideStore under **Sources → + / Add Source**:

```text
https://github.com/code-by-fh/sidestart/releases/latest/download/altstore-source.json
```

The IPA is signed with your own Apple Account. SideStore requires its usual setup, Wi-Fi, and local VPN connection. Free account signing requires regular app renewal. See [Sideloading](docs/SIDELOADING.md).

The shared catalog for all registered apps is hosted separately:

```text
https://raw.githubusercontent.com/code-by-fh/ios-apps/main/altstore-source.json
```

Publishing an app release does not update that catalog automatically. After the app source is ready, manually run **Actions → Refresh app catalog → Run workflow → main** in [ios-apps](https://github.com/code-by-fh/ios-apps), or use:

```powershell
gh workflow run refresh-catalog.yml --repo code-by-fh/ios-apps --ref main
```

## Use this template for a new app

On GitHub, choose **Use this template → Create a new repository** and create a public app repository. Alternatively, use GitHub CLI:

```powershell
gh repo create my-app --template code-by-fh/sidestart --public --clone
cd my-app
python scripts/configure_app.py --name my_app --organization dev.example --display-name "My App"
git add app-config.json pubspec.yaml lib test
git commit -m "Configure new app"
git push
```

Choose an appropriate `dev.example` and `my_app` for each app. Flutter derives platform identifiers from these values. Unique identifiers allow multiple apps to be installed together. `app-config.json` holds the project name, organization, and display name. The configuration command also updates package imports, `pubspec.yaml`, and the example app titles.

**Configure the app before generating native platform directories.** The script rejects identity changes when native projects already exist, preventing stale bundle identifiers. Unchanged template copies initially run checks only. iOS and Android builds and publication start after committing a unique project name or organization.

After a successful build, the new source URL is:

```text
https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY/releases/latest/download/altstore-source.json
```

The pipeline uses the new GitHub repository name and metadata from the built IPA. No separate download repository or Apple signing certificate in GitHub is required.

## Develop locally

Requirements: Python 3.10+, Git, and the Flutter SDK pinned in `.fvmrc`. Chrome is sufficient for an initial Windows test. Install the SDK using the verified download script:

```powershell
.\scripts\install-flutter.ps1
# Run the PATH command printed by the script, then:
.\setup.ps1 -Device chrome
```

`bootstrap.py` generates missing platform projects from the pinned SDK's official templates and preserves existing files. Commit generated native directories when you need to customize them.

Run checks with:

```powershell
python -m unittest discover -s scripts -p test_*.py
flutter pub get
flutter analyze
flutter test
```

## Builds and releases

Each push to `main` or `master` builds and publishes the configured app. Manual runs are also supported. Pull requests never publish. Generated release tags such as `v0.1.0-build.3` do not trigger additional builds. The build number comes from `github.run_number`; the app version comes from `pubspec.yaml`.

Source JSON derives the bundle identifier, app name, version, build number, minimum iOS version, size, and permissions from the actual IPA. Version history is preserved. A release is first prepared as a draft with all required files, then published. An Android build failure does not block iOS publication.

The repository must be public. The pipeline uses only the automatically provided `GITHUB_TOKEN`, with write access in publication jobs. New template copies may require GitHub Actions and workflow write permissions to be enabled once.

The Android APK uses a development signing key for personal testing. Configure a permanent signing key before relying on Android updates across builds.

## Publish an existing IPA manually

```powershell
python scripts/publish_source.py --ipa downloads/run-123/sidestart-ios-unsigned.ipa
```

The destination is inferred from the current GitHub repository. Override it with `--repository owner/repo`. The publisher does not make existing private repositories public.

All documentation, comments, UI text, messages, and metadata in this project must be written in English. See [AGENTS.md](AGENTS.md).
