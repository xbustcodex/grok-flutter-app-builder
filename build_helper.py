#!/usr/bin/env python3
"""
Grok Flutter App Builder – Build, Verify & Repair Helper

Capabilities:
  1. flutter pub get
  2. flutter analyze  (verification)
  3. flutter build windows / android / ... (EXE / APK)
  4. Optional --repair : feed analyzer/build errors back to Grok for a fix pass

Requires Flutter SDK on PATH.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def run(cmd: list[str], cwd: Path, timeout: int = 900) -> tuple[int, str, str]:
    print(f"→ {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = result.stdout or ""
        err = result.stderr or ""
        if out.strip():
            print(out)
        if err.strip():
            print(err, file=sys.stderr)
        return result.returncode, out, err
    except subprocess.TimeoutExpired:
        print("Command timed out", file=sys.stderr)
        return 1, "", "timeout"
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}", file=sys.stderr)
        return 1, "", "not found"


def check_flutter() -> bool:
    return shutil.which("flutter") is not None


def has_pubspec(project: Path) -> bool:
    return (project / "pubspec.yaml").exists()


# ---------------------------------------------------------------------------
# Core steps
# ---------------------------------------------------------------------------

def step_pub_get(project: Path) -> tuple[bool, str]:
    code, out, err = run(["flutter", "pub", "get"], project)
    combined = out + "\n" + err
    return code == 0, combined


def step_analyze(project: Path) -> tuple[bool, str]:
    code, out, err = run(["flutter", "analyze", "--no-fatal-infos"], project)
    combined = out + "\n" + err
    return code == 0, combined


def step_build(project: Path, platform: str, release: bool = False) -> tuple[bool, str]:
    cmd = ["flutter", "build", platform]
    if release:
        cmd.append("--release")
    code, out, err = run(cmd, project, timeout=1200)
    combined = out + "\n" + err
    return code == 0, combined


def find_artifacts(project: Path, platform: str, release: bool) -> list[str]:
    """Return paths of interesting build outputs if they exist."""
    mode = "release" if release else "debug"
    candidates = []
    if platform == "windows":
        candidates = [
            project / f"build/windows/x64/runner/{mode}",
            project / f"build/windows/runner/{mode}",
        ]
    elif platform == "android":
        candidates = [
            project / "build/app/outputs/flutter-apk/app-release.apk",
            project / "build/app/outputs/flutter-apk/app-debug.apk",
            project / "build/app/outputs/apk/release/app-release.apk",
            project / "build/app/outputs/apk/debug/app-debug.apk",
        ]
    elif platform == "web":
        candidates = [project / "build/web"]
    found = []
    for c in candidates:
        if c.exists():
            found.append(str(c))
    return found


# ---------------------------------------------------------------------------
# Optional repair via Grok
# ---------------------------------------------------------------------------

def attempt_repair(project: Path, error_log: str, provider: str = "auto") -> bool:
    """Send the error log + current key files back to Grok and apply suggested patches."""
    try:
        from providers import get_client, resolve_model
    except ImportError:
        sys.path.insert(0, str(Path(__file__).parent))
        from providers import get_client, resolve_model

    print("\n=== Repair pass – sending errors to Grok ===")
    try:
        client, prov, default_model = get_client(provider)
        model = resolve_model(None, prov)
    except Exception as e:
        print(f"Cannot create client for repair: {e}")
        return False

    sources = []
    for p in sorted(project.rglob("*.dart")):
        if "test" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8")
            rel = p.relative_to(project)
            sources.append(f"// {rel}\n{text}")
        except Exception:
            pass
        if sum(len(s) for s in sources) > 60000:
            break

    pubspec = ""
    if (project / "pubspec.yaml").exists():
        pubspec = (project / "pubspec.yaml").read_text(encoding="utf-8")

    prompt = f"""You are fixing a Flutter project that failed analysis or build.

### Error log
```
{error_log[:12000]}
```

### pubspec.yaml
```yaml
{pubspec}
```

### Current Dart sources
{chr(10).join(sources[:15])}

Please output ONLY the files that need to be changed or added, using the exact format:

```dart
// relative/path.dart
...full new content...
```

```yaml
# pubspec.yaml
...full new content...
```

Do not explain. Just the corrected files.
"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert Flutter engineer. Output only corrected files in the requested format."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=12000,
        )
        content = resp.choices[0].message.content or ""
    except Exception as e:
        print(f"Repair API call failed: {e}")
        return False

    import re
    files = {}
    pattern = re.compile(
        r"```(?:dart|yaml)?\s*\n(?://|#)\s*([^\n]+)\n(.*?)\n```",
        re.DOTALL | re.IGNORECASE,
    )
    for m in pattern.finditer(content):
        raw = m.group(1).strip().lstrip("./")
        body = m.group(2).rstrip() + "\n"
        if ".." in raw or raw.startswith("/"):
            continue
        files[raw] = body

    if not files:
        print("Repair response contained no usable file blocks.")
        (project / "REPAIR_RESPONSE.md").write_text(content, encoding="utf-8")
        return False

    for rel, body in files.items():
        target = (project / rel).resolve()
        if not str(target).startswith(str(project.resolve())):
            print(f"  Skipping unsafe path from repair: {rel}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        print(f"  ✓ repaired {rel}")

    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Verify and build a generated Flutter project (Windows EXE / Android APK)"
    )
    parser.add_argument("project_dir", help="Path to the generated Flutter project")
    parser.add_argument(
        "--platform",
        choices=["windows", "android", "linux", "macos", "web", "all"],
        default=None,
        help="Platform to build. Omit to only run pub get + analyze.",
    )
    parser.add_argument("--release", action="store_true", help="Build in release mode")
    parser.add_argument(
        "--repair",
        action="store_true",
        help="If analyze or build fails, ask Grok to repair and retry once",
    )
    parser.add_argument(
        "--provider",
        default="auto",
        help="Provider for the repair pass (auto/xai/openrouter/together/fireworks/generic)",
    )
    parser.add_argument(
        "--skip-analyze",
        action="store_true",
        help="Skip flutter analyze step",
    )
    args = parser.parse_args()

    project = Path(args.project_dir).resolve()
    if not project.is_dir():
        print(f"Error: {project} is not a directory")
        sys.exit(1)
    if not has_pubspec(project):
        print(f"Error: No pubspec.yaml in {project}")
        sys.exit(1)
    if not check_flutter():
        print("Error: Flutter SDK not found on PATH.")
        print("Install: https://docs.flutter.dev/get-started/install")
        sys.exit(1)

    print(f"Project : {project}")
    print(f"Flutter : {shutil.which('flutter')}")
    print()

    # 1. pub get
    ok, log = step_pub_get(project)
    if not ok:
        print("flutter pub get failed.")
        if args.repair:
            if attempt_repair(project, log, args.provider):
                ok, log = step_pub_get(project)
        if not ok:
            sys.exit(1)

    # 2. analyze (verification)
    if not args.skip_analyze:
        print("\n=== flutter analyze ===")
        ok, log = step_analyze(project)
        if not ok:
            print("Analyzer reported issues.")
            if args.repair:
                if attempt_repair(project, log, args.provider):
                    step_pub_get(project)
                    ok, log = step_analyze(project)
            if not ok:
                print("Verification failed. Fix the issues above or run with --repair.")
                if not args.platform:
                    sys.exit(1)

    # 3. build
    if not args.platform:
        print("\n✓ Verification finished. Pass --platform windows|android|... to compile.")
        return

    platforms = (
        ["windows", "android", "linux", "macos", "web"]
        if args.platform == "all"
        else [args.platform]
    )

    overall_ok = True
    for plat in platforms:
        print(f"\n=== Building {plat} ({'release' if args.release else 'debug'}) ===")
        ok, log = step_build(project, plat, args.release)
        if not ok and args.repair:
            print("Build failed – attempting repair...")
            if attempt_repair(project, log, args.provider):
                step_pub_get(project)
                ok, log = step_build(project, plat, args.release)

        if ok:
            arts = find_artifacts(project, plat, args.release)
            print(f"✓ {plat} build succeeded")
            for a in arts:
                print(f"  → {a}")
        else:
            print(f"✗ {plat} build failed")
            overall_ok = False

    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
