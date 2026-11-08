# Validation record

## Initial preparation

The following historical record describes the initial Windows preparation on November 8, 2026. It does not describe every later change or the current GitHub authentication state.

- `python -m unittest discover -s scripts -p test_*.py -v`: **12 tests passed** during the initial preparation. They covered preservation of platform files, isolated template generation, the minimum iOS version, and rejection of incomplete, incorrectly packaged, or unsuitable app bundles. Test bundles were synthetic files, not compiled iOS apps.
- The PowerShell parser accepted `setup.ps1`, `publish.ps1`, and `scripts/install-flutter.ps1`.
- Workflow YAML and job dependencies were inspected locally.
- Two subagents contributed research and technical review. That review identified no definite build blocker.

At that stage, Flutter was not installed locally and shell network access was restricted. Local Flutter analysis, widget tests, SDK installation, native project generation, and a real GitHub/Xcode build had not run. GitHub CLI authentication was invalid at that stage, and the initial preparation had not created or pushed a remote repository.

Filesystem restrictions prevented creation of `C:\Development\sidestart` and `C:\Users\flori\Development\sidestart` during initial preparation. The starter was initially assembled in the writable `%LOCALAPPDATA%\Temp\sidestart` directory and subsequently transferred to the development repository.

## Subsequent build evidence

An IPA from GitHub Actions run `42522193982` was subsequently downloaded to `downloads/run-42522193982/sidestart-ios-unsigned.ipa`. Its inspected metadata was version `0.1.0`, build `3`, bundle identifier `dev.sidestart.sidestart`, and minimum iOS version `15.0`. Its size was 6,165,711 bytes. Source generation from that IPA completed successfully.

This is evidence for that particular downloaded build. It does not establish that later source changes passed CI or that the app was installed and launched on an iPhone.

## Validation expectations

After relevant changes, run the Python checks, Flutter analysis, and widget tests documented in the README. Confirm the GitHub Actions result for the exact pushed commit. Distinguish mocked native tools and GitHub responses from actual compilation and publication.

Signing, installation, and launch on a real iPhone require importing the IPA with a personal sideloader. No confirmed iPhone installation or launch is recorded here. Passing Python tests does not prove that an iOS app runs correctly; the native build checks compilation and packaging, while a signed device test verifies launch and interaction.
