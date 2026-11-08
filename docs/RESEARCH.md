# Technical research

Initial research date: November 8, 2026. These sources informed the implementation. Reading documentation or reviewing workflow files does not prove that a particular commit builds or that an app launches on an iPhone. See [VALIDATION.md](VALIDATION.md) for recorded evidence.

## Windows development and cloud iOS builds

[Flutter iOS deployment](https://docs.flutter.dev/deployment/ios) describes the iOS build and distribution tools. Compiling the iOS target requires Xcode and macOS. A GitHub-hosted macOS runner handles that step while the Dart project can be edited on Windows. This sideloading workflow builds a physical-device app in release mode without Apple signing and packages it as an IPA.

The project pins the SDK version in `.fvmrc` and generates missing platform projects from official templates using that SDK. Existing native projects are preserved. Local Flutter checks remain unverified wherever the required SDK and tooling are unavailable.

## NOOP as a reference

The user-provided [NOOP repository](https://github.com/ryanbr/noop) documents direct IPA downloads and installation using AltStore or SideStore. NOOP uses native Swift targets, but its distribution approach also applies to a Flutter device app.

The reviewed [release workflow, `fork-release.yml`](https://github.com/ryanbr/noop/blob/main/.github/workflows/fork-release.yml), builds the iOS target on macOS in release mode with code signing disabled, packages the app inside a `Payload` directory, and uploads the IPA as a release asset. Its `app-build.yml` primarily checks compilation and tests. NOOP's extra handling for widgets, HealthKit, and App Groups is unnecessary for the minimal SideStart app, which has none of those features. Statements or error diagnoses in NOOP's documentation do not replace a device test of this project.

## Signing with a free Apple Account

[Apple's developer account overview](https://developer.apple.com/help/account/basics/about-your-developer-account) documents Personal Team limits, including ten App IDs, three devices, three apps per device, and seven-day provisioning validity. This project's unsigned CI build requires neither a paid Apple Developer account nor Apple certificates or credentials in GitHub. Personal signing happens later in the sideloader.

The [SideStore FAQ](https://docs.sidestore.io/docs/faq) explains signing with personal development certificates and regular background refresh. SideStore itself uses an app slot. The reviewed [Windows prerequisites](https://docs.sidestore.io/docs/installation/prerequisites) use iloader and LocalDevVPN. Installation, updates, and renewal require the connections described by SideStore. Its [installation guide](https://docs.sidestore.io/docs/installation/install) covers trusting the profile, enabling Developer Mode, and performing the initial manual refresh.

## GitHub artifacts and releases

[GitHub artifact documentation](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-what-your-workflow-does/storing-and-sharing-data-from-a-workflow) explains build artifacts and retention. An Actions run can provide an IPA artifact for authenticated download. [GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) provide versioned publication with attached files.

The current SideStart workflow publishes on configured `main`/`master` pushes and manual runs, using generated version/build tags. Those tags do not trigger recursive builds. IPA publication is independent of Android build success; the APK is attached afterward when available.

[GitHub-hosted runner documentation](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners) describes supported operating systems and billing. Private repositories must account for available minutes and applicable billing. The current public source publisher requires a public destination repository and uses the workflow's provided token.

## App sources and the shared catalog

[AltStore's source schema](https://faq.altstore.io/developers/make-a-source) defines app metadata and ordered version lists. The bundle identifier, version, build number, file size, and declared permissions must match the IPA. A public source requires anonymously accessible metadata, icon, and IPA URLs. Private GitHub files are unsuitable as public download endpoints.

SideStart generates its source from the actual IPA and publishes it alongside release assets. A direct IPA download and import remains available independently of the source listing.

The separate [ios-apps repository](https://github.com/code-by-fh/ios-apps) combines registered public app sources into one catalog, supporting both open-source and closed-source apps. Closed-source development repositories can remain private while distribution files are public. Its catalog refresh is **manual only**: pushes and pull requests run checks, and app releases do not trigger catalog publication automatically.
