# App and source in the same repository

SideStart publishes its IPA and AltStore/SideStore source as release assets in `code-by-fh/sidestart`:

```text
https://github.com/code-by-fh/sidestart/releases/latest/download/altstore-source.json
```

Template copies automatically use their own GitHub owner and repository name. The source URL stays the same across releases; IPA download URLs identify specific versions.

A push to `main` or `master` first builds a release for an iOS device without Apple signing. `make_source.py` generates JSON, an icon, and a checksum from the IPA. The release job publishes these files using its provided `GITHUB_TOKEN`. No additional credentials or separate download repository are required.

For local publication with your existing GitHub CLI authentication:

```powershell
python scripts/publish_source.py --ipa downloads/run-123/sidestart-ios-unsigned.ipa
```

The destination repository must be public. The publisher does not change its visibility. It rejects an already published version/build combination containing different IPA bytes; use a higher build number for a new build. Older versions cannot replace newer ones.

## Shared catalog

The app source can also be registered in the central [ios-apps catalog](https://github.com/code-by-fh/ios-apps). Its stable source URL is:

```text
https://raw.githubusercontent.com/code-by-fh/ios-apps/main/altstore-source.json
```

The catalog supports both open-source and closed-source apps with public distribution files. App releases do not update it automatically. Commit any registry changes, then manually run its refresh workflow:

```powershell
gh workflow run refresh-catalog.yml --repo code-by-fh/ios-apps --ref main
```

The catalog has no scheduled refresh. Pushes and pull requests run checks without publishing a catalog.

Schema: [AltStore: Make a Source](https://faq.altstore.io/developers/make-a-source). Reference implementation: [NOOP source](https://github.com/ryanbr/noop/blob/main/altstore-source.json).
