"""Generate native Flutter projects from the pinned SDK, preserving existing files."""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from configure_app import load_config

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = {
    "ios": "Runner.xcodeproj/project.pbxproj",
    "android": "app/src/main/AndroidManifest.xml",
    "web": "index.html",
    "windows": "CMakeLists.txt",
}


def configure_ios(directory: Path, display_name: str = "SideStart") -> None:
    project = directory / PLATFORMS["ios"]
    content = project.read_text(encoding="utf-8")
    content, matches = re.subn(
        r"IPHONEOS_DEPLOYMENT_TARGET = [0-9.]+;",
        "IPHONEOS_DEPLOYMENT_TARGET = 15.0;",
        content,
    )
    if not matches:
        raise RuntimeError("Flutter template has no iOS deployment target; review SDK template.")
    project.write_text(content, encoding="utf-8")
    info_path = directory / "Runner/Info.plist"
    with info_path.open("rb") as stream:
        info = plistlib.load(stream)
    info["CFBundleDisplayName"] = display_name
    with info_path.open("wb") as stream:
        plistlib.dump(info, stream, sort_keys=False)
    framework_info = directory / "Flutter/AppFrameworkInfo.plist"
    if framework_info.exists():
        with framework_info.open("rb") as stream:
            info = plistlib.load(stream)
        info["MinimumOSVersion"] = "15.0"
        with framework_info.open("wb") as stream:
            plistlib.dump(info, stream, sort_keys=False)


def bootstrap(root: Path, platforms: list[str], flutter: str) -> list[str]:
    config = load_config(root)
    project_name = config["projectName"]
    display_name = config["displayName"]
    missing = []
    for platform in platforms:
        destination = root / platform
        if destination.exists():
            if not (destination / PLATFORMS[platform]).is_file():
                raise RuntimeError(
                    f"Incomplete {platform}/ directory. Restore it or move it aside first."
                )
            print(f"Keeping existing {platform}/")
        else:
            missing.append(platform)
    if not missing:
        return []

    # Generate outside the app: flutter create must never overwrite Dart source,
    # pubspec.yaml, tests, or custom native projects in this repository.
    with tempfile.TemporaryDirectory(prefix="sidestart-scaffold-") as temporary:
        scaffold = Path(temporary) / project_name
        subprocess.run(
            [
                flutter, "create", "--template=app", "--empty", "--no-pub",
                f"--platforms={','.join(missing)}", f"--org={config['organization']}",
                f"--project-name={project_name}", str(scaffold),
            ],
            check=True,
        )
        for platform in missing:
            source = scaffold / platform
            if not (source / PLATFORMS[platform]).is_file():
                raise RuntimeError(f"Flutter did not generate a complete {platform} project.")
            if platform == "ios":
                configure_ios(source, display_name)
            elif platform == "android":
                manifest = source / PLATFORMS[platform]
                android_label = escape(display_name, {'"': "&quot;"})
                manifest.write_text(
                    manifest.read_text(encoding="utf-8").replace(
                        f'android:label="{project_name}"',
                        f'android:label="{android_label}"'
                    ),
                    encoding="utf-8",
                )
            elif platform == "web":
                index = source / "index.html"
                index.write_text(index.read_text(encoding="utf-8").replace(
                    f"<title>{project_name}</title>", f"<title>{escape(display_name)}</title>"
                ), encoding="utf-8")
                manifest_path = source / "manifest.json"
                if manifest_path.exists():
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest.update(name=display_name, short_name=display_name)
                    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            elif platform == "windows":
                cpp_name = display_name.replace("\\", "\\\\").replace('"', '\\"')
                for relative in ["runner/main.cpp", "runner/Runner.rc"]:
                    path = source / relative
                    if path.exists():
                        text = path.read_text(encoding="utf-8")
                        if relative.endswith("main.cpp"):
                            text = text.replace(f'L"{project_name}"', f'L"{cpp_name}"')
                        else:
                            text = re.sub(
                                r'(VALUE "(?:FileDescription|ProductName)", ")' + re.escape(project_name) + r'(")',
                                lambda match: match.group(1) + cpp_name + match.group(2), text,
                            )
                        path.write_text(text, encoding="utf-8")
            shutil.copytree(source, root / platform)
            print(f"Created {platform}/")
        metadata = scaffold / ".metadata"
        if metadata.exists() and not (root / ".metadata").exists():
            shutil.copy2(metadata, root / ".metadata")
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platforms", default=",".join(PLATFORMS))
    args = parser.parse_args()
    platforms = list(dict.fromkeys(args.platforms.split(",")))
    if not platforms or any(platform not in PLATFORMS for platform in platforms):
        parser.error(f"Supported platforms: {', '.join(PLATFORMS)}")
    flutter = shutil.which("flutter")
    if not flutter:
        parser.error("Flutter is missing from PATH. Install the SDK version in .fvmrc first.")
    pinned = json.loads((ROOT / ".fvmrc").read_text(encoding="utf-8"))["flutter"]
    result = subprocess.run(
        [flutter, "--version", "--machine"], check=True,
        capture_output=True, text=True, encoding="utf-8",
    )
    actual = json.loads(result.stdout)["frameworkVersion"]
    if actual != pinned:
        parser.error(f"Flutter {pinned} required; found {actual}. Check .fvmrc and PATH.")
    bootstrap(ROOT, platforms, flutter)


if __name__ == "__main__":
    main()
