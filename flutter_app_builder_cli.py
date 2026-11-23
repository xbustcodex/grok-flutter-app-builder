#!/usr/bin/env python3
"""
Grok Flutter App Builder CLI
A local tool that uses the xAI Grok API to generate complete Flutter apps
(Android + Desktop) from a natural-language description.

Requirements:
  pip install openai
  export XAI_API_KEY=your_key_here   # get one at https://console.x.ai

Usage examples:
  python flutter_app_builder_cli.py "A todo list app with dark mode and local storage"
  python flutter_app_builder_cli.py --interactive
  python flutter_app_builder_cli.py --name my_notes --desc "Simple notes app with categories"
"""

import argparse
import os
import sys
import re
from pathlib import Path
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    print("Missing dependency. Run:  pip install openai")
    sys.exit(1)


SYSTEM_PROMPT = """You are Grok Flutter App Builder, an expert senior Flutter engineer and product-minded app architect created by xAI.

Your sole purpose is to help the user design and generate complete, production-ready Flutter applications that run on Android and desktop (Windows / macOS / Linux) using a single codebase.

### Core Principles
- Always prefer Flutter (latest stable channel practices) with Material 3.
- Produce clean, well-structured, maintainable code following official Flutter best practices and effective Dart guidelines.
- Use modern packages only when necessary (list them in pubspec.yaml with compatible versions).
- Favor composition, proper state management (Riverpod preferred for medium+ apps, Provider for simple ones), and clear separation of concerns.
- Make the app responsive and adaptive for both mobile and desktop.
- Include proper error handling, loading states, and basic accessibility.
- Generate complete, runnable projects — never leave TODOs or incomplete stubs unless the feature is explicitly out of scope.

### Output Format (strict)
Structure your response exactly like this:

1. **Project Overview**
   Short description + architecture decisions + key packages.

2. **File Tree**
   A clean tree of every file you create.

3. **Complete Files**
   For every file output a fenced code block. The very first line inside the block must be a comment with the relative path, e.g.:

```dart
// lib/main.dart
...full code...
```

```yaml
# pubspec.yaml
...full code...
```

```dart
// lib/screens/home_screen.dart
...
```

4. **How to Run**
   Exact commands the user should run after the files are written.

5. **Next Steps**
   Optional improvements.

Do not wrap the entire response in one big code block. Output the overview in markdown, then the individual file blocks.
Always generate a complete, self-contained Flutter project that works after `flutter pub get` and `flutter run`.
"""


def get_client() -> OpenAI:
    api_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if not api_key:
        print("Error: Set the environment variable XAI_API_KEY")
        print("Get a key at: https://console.x.ai")
        print("Then:  export XAI_API_KEY=xai-...")
        sys.exit(1)

    return OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )


def call_grok(client: OpenAI, user_message: str, model: str = "grok-4.7") -> str:
    print(f"\n→ Calling Grok ({model})... this may take 20–90 seconds for a full app.\n")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.35,
        max_tokens=16000,
    )
    return response.choices[0].message.content or ""


def extract_files(response: str) -> dict[str, str]:
    """Parse the response and extract path → content from fenced code blocks.
    More robust: handles both // path and # path comments, and also
    language tags that contain the path (some models do that).
    """
    files = {}

    # Primary pattern: comment on first line of the code block
    pattern = re.compile(
        r"```(?:dart|yaml|xml|json|md|txt|gradle|kotlin|swift|html)?\s*\n"
        r"(?://|#)\s*([^\n]+)\n"          # path comment
        r"(.*?)\n```",
        re.DOTALL | re.IGNORECASE,
    )

    for match in pattern.finditer(response):
        path = match.group(1).strip().lstrip("./")
        content = match.group(2).rstrip() + "\n"
        if path and (path.startswith("lib/") or "/" in path or path.endswith((".dart", ".yaml", ".md", ".json"))):
            files[path] = content

    # Secondary pattern: sometimes the path is put in the language tag
    # e.g. ```dart:lib/main.dart
    alt_pattern = re.compile(
        r"```(?:dart|yaml|md)?[:\s]+([^\n`]+)\n"
        r"(.*?)\n```",
        re.DOTALL | re.IGNORECASE,
    )
    for match in alt_pattern.finditer(response):
        path = match.group(1).strip().lstrip("./")
        content = match.group(2).rstrip() + "\n"
        if path and path not in files and (path.startswith("lib/") or path.endswith((".dart", ".yaml", ".md"))):
            files[path] = content

    if not files:
        print("Warning: Could not auto-extract files cleanly. The full response will be saved as GROK_RESPONSE.md")
    return files


def write_project(project_dir: Path, files: dict[str, str], full_response: str):
    project_dir.mkdir(parents=True, exist_ok=True)

    # Always save the raw response for reference
    (project_dir / "GROK_RESPONSE.md").write_text(full_response, encoding="utf-8")

    if not files:
        print("No structured files extracted. Open GROK_RESPONSE.md and copy the code manually.")
        return

    for rel_path, content in files.items():
        target = project_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"  ✓ {rel_path}")

    print(f"\nProject written to: {project_dir.resolve()}")


def interactive_mode(client: OpenAI, model: str) -> str:
    print("=== Grok Flutter App Builder (Interactive) ===")
    print("Describe the app you want. Include key features, style, any special requirements.")
    print("Type your description, then press Enter twice (or Ctrl-D) when finished.\n")

    lines = []
    try:
        while True:
            line = input()
            if line.strip() == "" and lines and lines[-1].strip() == "":
                break
            lines.append(line)
    except EOFError:
        pass

    description = "\n".join(lines).strip()
    if not description:
        print("No description given. Exiting.")
        sys.exit(0)
    return description


def main():
    parser = argparse.ArgumentParser(
        description="Generate Flutter (Android + Desktop) apps with Grok"
    )
    parser.add_argument(
        "description",
        nargs="?",
        help="Natural language description of the app",
    )
    parser.add_argument(
        "--name", "-n",
        help="Project folder name (default: derived from description or 'flutter_app')",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode – type a multi-line description",
    )
    parser.add_argument(
        "--model",
        default="grok-4.7",
        help="Grok model to use (default: grok-4.7)",
    )
    parser.add_argument(
        "--out", "-o",
        default=".",
        help="Parent directory for the new project (default: current dir)",
    )
    args = parser.parse_args()

    client = get_client()

    if args.interactive or not args.description:
        user_prompt = interactive_mode(client, args.model)
    else:
        user_prompt = args.description

    # Strengthen the request
    full_user_message = f"""Build a complete Flutter application for Android and Desktop based on this description:

{user_prompt}

Requirements:
- Use a modern, clean Material 3 design with light/dark mode support.
- Prefer Riverpod for state management if the app has non-trivial state; otherwise Provider is fine.
- Use go_router for navigation if there is more than one screen.
- Make the UI responsive so it looks good on both phones and desktop windows.
- Include a proper pubspec.yaml with all needed dependencies and correct SDK constraints.
- Generate every necessary file (main.dart, screens, models, providers/services, theme, etc.).
- The project must be runnable after `flutter pub get` + `flutter run`.

Start generating now."""

    response = call_grok(client, full_user_message, model=args.model)

    # Determine project name
    project_name = args.name
    if not project_name:
        # Simple heuristic
        words = re.findall(r"[a-zA-Z0-9]+", user_prompt.lower())
        project_name = "_".join(words[:3]) if words else "flutter_app"
        project_name = re.sub(r"[^a-z0-9_]", "", project_name) or "flutter_app"

    project_dir = Path(args.out) / project_name
    print(f"\nExtracting files into ./{project_name}/ ...")
    files = extract_files(response)
    write_project(project_dir, files, response)

    print("\n" + "=" * 60)
    print("Done!")
    print(f"1. cd {project_dir}")
    print("2. flutter pub get")
    print("3. flutter run -d windows   # or macos / linux / chrome / android")
    print("=" * 60)
    print("\nTip: Open GROK_RESPONSE.md inside the folder if any files are missing.")


if __name__ == "__main__":
    main()
