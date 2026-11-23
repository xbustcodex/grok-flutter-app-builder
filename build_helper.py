#!/usr/bin/env python3
"""
Grok Flutter App Builder - Build Helper

Attempts to run `flutter pub get` and optional platform builds
on a generated project. This is the first step toward automatic
Windows EXE / Android APK compilation.

Requires Flutter SDK to be installed and on PATH.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    print(f"→ {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode, result.stdout, result.stderr


def check_flutter() -> bool:
    return shutil.which("flutter") is not None


def main():
    parser = argparse.ArgumentParser(description="Build a generated Flutter project")
    parser.add_argument("project_dir", help="Path to the generated Flutter project")
    parser.add_argument(
        "--platform",
        choices=["windows", "android", "linux", "macos", "web", "all"],
        default=None,
        help="Target platform to build (default: only run pub get)",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Build in release mode",
    )
    args = parser.parse_args()

    project = Path(args.project_dir).resolve()
    if not project.is_dir():
        print(f"Error: {project} is not a directory")
        sys.exit(1)

    if not (project / "pubspec.yaml").exists():
        print(f"Error: No pubspec.yaml found in {project}")
        sys.exit(1)

    if not check_flutter():
        print("Error: Flutter SDK not found on PATH.")
        print("Install from https://docs.flutter.dev/get-started/install")
        sys.exit(1)

    print(f"Project: {project}")
    print()

    # Always run pub get first
    code, _, _ = run(["flutter", "pub", "get"], project)
    if code != 0:
        print("flutter pub get failed. Fix dependency issues before building.")
        sys.exit(code)

    if not args.platform:
        print("\n✓ Dependencies resolved. Use --platform windows|android|... to build.")
        return

    mode = "release" if args.release else "debug"
    platforms = ["windows", "android", "linux", "macos", "web"] if args.platform == "all" else [args.platform]

    for plat in platforms:
        print(f"\n=== Building for {plat} ({mode}) ===")
        cmd = ["flutter", "build", plat]
        if args.release:
            cmd.append("--release")
        code, _, _ = run(cmd, project)
        if code == 0:
            print(f"✓ {plat} build succeeded")
            if plat == "windows":
                print(f"  Look in: {project}/build/windows/x64/runner/{mode}/")
            elif plat == "android":
                print(f"  APK: {project}/build/app/outputs/flutter-apk/")
        else:
            print(f"✗ {plat} build failed (exit {code})")


if __name__ == "__main__":
    main()
