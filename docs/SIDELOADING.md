# Install SideStart on an iPhone

## Build output

GitHub Actions compiles Flutter in **release mode for a physical iOS device** on a macOS runner. It packages `Runner.app` as `Payload/Runner.app` inside an IPA. The file has no usable Apple developer signature yet. SideStore, AltStore Classic, or Sideloadly signs and installs it with your own Apple Account. A simulator build cannot be used for this process.

A successful CI build verifies compilation and package structure. Installation and interaction on an iPhone require a separate device test. No confirmed device test is recorded in [VALIDATION.md](VALIDATION.md).

## Set up SideStore using Windows

Follow the current official [prerequisites](https://docs.sidestore.io/docs/installation/prerequisites) and [installation instructions](https://docs.sidestore.io/docs/installation/install). The setup reviewed for this project uses **iloader and LocalDevVPN**:

1. Prepare an iPhone with a passcode and supported iOS version, an Apple Account, Wi-Fi, and a Windows computer for initial setup. SideStore's documented minimum is iOS 15; the built IPA's minimum version also applies.
2. Install the Apple device drivers or iTunes and iloader specified in the official Windows instructions.
3. Install LocalDevVPN on the iPhone as directed by SideStore.
4. Connect the iPhone over USB and trust the computer. Sign in to iloader with your Apple Account and choose **Install SideStore (Stable)**.
5. On the iPhone, trust the developer profile under **Settings → General → VPN & Device Management**. On iOS 16 or later, also enable **Developer Mode** under **Privacy & Security** and complete the requested restart. Dialogs vary by iOS version.
6. Connect to Wi-Fi and LocalDevVPN, open SideStore, and sign in with the same Apple Account.
7. Manually refresh SideStore once under **My Apps**, as described in its official instructions.

Apple credentials belong only in the signing software you configure. This project does not put them in source files or GitHub Actions secrets.

## Install from a source

After a successful public release, add the app source in **SideStore → Sources → + / Add Source**:

```text
https://github.com/code-by-fh/sidestart/releases/latest/download/altstore-source.json
```

Alternatively, add the shared catalog:

```text
https://raw.githubusercontent.com/code-by-fh/ios-apps/main/altstore-source.json
```

The shared catalog is refreshed manually on GitHub. Publishing a new app release does not automatically update it. After its refresh workflow succeeds, refresh the source list in SideStore to see the new catalog contents.

## Import an IPA directly

1. Wait for the iOS job in `.github/workflows/builds.yml` to succeed.
2. Download its IPA artifact and extract the outer GitHub artifact ZIP, or download the IPA from the GitHub release. Private artifact downloads require GitHub authentication.
3. Transfer the `.ipa` to the iPhone's Files app using your preferred file transfer method.
4. Enable Wi-Fi and LocalDevVPN. In SideStore, use **My Apps → +** to select the IPA, or use its available import action.
5. After signing and installation succeed, open SideStart. Increase and reset the counter, rotate the screen, and restart the app.

Direct IPA import does not require public hosting. A source provides a convenient listing and update mechanism once public metadata, icon, and IPA URLs are available.

## Expiration and updates

According to [Apple](https://developer.apple.com/help/account/basics/about-your-developer-account), free account provisioning has limits including three development apps per device, ten App IDs, and seven-day provisioning validity. The [SideStore FAQ](https://docs.sidestore.io/docs/faq) states that SideStore itself uses one of the three active app slots.

SideStore attempts background renewal before expiration. Check the remaining validity and successful renewal regularly. Wi-Fi and the local VPN connection required by SideStore must be available. You can also renew manually before expiration. iPhone updates or resets may require repeating setup or renewing the pairing file.

For an app update, refresh its source listing or import the new IPA from a successful build. Keep the bundle identifier unchanged so the signing tool can recognize the same app. Update the version in `pubspec.yaml` for a new app version; CI supplies the build number from `github.run_number`. The example app uses no additional Apple capabilities or app extensions.

## Troubleshooting

First check that the iOS build and packaging succeeded, the file ends in `.ipa`, and the outer GitHub artifact ZIP has been extracted. Then check the developer profile, Developer Mode, Wi-Fi, LocalDevVPN, app limit, and remaining validity. Look up the specific signing error in [SideStore troubleshooting](https://docs.sidestore.io/docs/troubleshooting).

AltStore **Classic** and [Sideloadly](https://sideloadly.io/) are alternative signing tools. AltStore PAL uses a different distribution process from the unsigned development IPA import described here.
