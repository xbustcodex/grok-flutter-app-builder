#!/usr/bin/env python3
"""
Grok Flutter App Builder - Simple Local Web UI (Gradio)

Run with:
  export XAI_API_KEY=xai-...
  python web_ui.py

Then open the local URL shown in the terminal.
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Optional

import gradio as gr
from openai import OpenAI

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
        raise ValueError("XAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")


def extract_files(response: str) -> dict[str, str]:
    files = {}
    pattern = re.compile(
        r"```(?:dart|yaml|xml|json|md|txt|gradle|kotlin|swift)?\s*\n"
        r"(?://|#)\s*([^\n]+)\n"
        r"(.*?)\n```",
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(response):
        path = match.group(1).strip().lstrip("./")
        content = match.group(2).rstrip() + "\n"
        if path.startswith("lib/") or path in ("pubspec.yaml", "README.md", "analysis_options.yaml") or "/" in path:
            files[path] = content
    return files


def generate_app(description: str, project_name: str, model: str, progress=gr.Progress()):
    if not description.strip():
        return "Please enter an app description.", None, ""

    progress(0.1, desc="Calling Grok...")
    try:
        client = get_client()
    except ValueError as e:
        return str(e), None, ""

    full_prompt = f"""Build a complete Flutter application for Android and Desktop based on this description:

{description}

Requirements:
- Use a modern, clean Material 3 design with light/dark mode support.
- Prefer Riverpod for state management if the app has non-trivial state; otherwise Provider is fine.
- Use go_router for navigation if there is more than one screen.
- Make the UI responsive so it looks good on both phones and desktop windows.
- Include a proper pubspec.yaml with all needed dependencies and correct SDK constraints.
- Generate every necessary file (main.dart, screens, models, providers/services, theme, etc.).
- The project must be runnable after `flutter pub get` + `flutter run`.

Start generating now."""

    try:
        response = client.chat.completions.create(
            model=model or "grok-4.7",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.35,
            max_tokens=16000,
        )
        content = response.choices[0].message.content or ""
    except Exception as e:
        return f"API Error: {e}", None, ""

    progress(0.7, desc="Extracting files...")

    name = project_name.strip() or "flutter_app"
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name).lower() or "flutter_app"

    # Create a temporary directory with the project
    tmpdir = Path(tempfile.mkdtemp(prefix=f"grok_{name}_"))
    files = extract_files(content)

    (tmpdir / "GROK_RESPONSE.md").write_text(content, encoding="utf-8")

    file_list = []
    for rel_path, file_content in files.items():
        target = tmpdir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file_content, encoding="utf-8")
        file_list.append(rel_path)

    progress(1.0, desc="Done!")

    summary = f"""### Project generated successfully!

**Folder:** `{tmpdir}`

**Files created ({len(file_list)}):**
""" + "\n".join(f"- `{f}`" for f in sorted(file_list))

    if not file_list:
        summary += "\n\n⚠️ No structured files were auto-extracted. Check the full response below and copy manually."

    summary += f"""

### Next steps
```bash
cd {tmpdir}
flutter pub get
flutter run -d windows   # or macos / linux / android / chrome
```
"""

    return summary, str(tmpdir), content


with gr.Blocks(title="Grok Flutter App Builder", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🚀 Grok Flutter App Builder
    Describe any Android + Desktop app and Grok will generate a complete Flutter project for you.
    
    **Requires** `XAI_API_KEY` environment variable (get one at [console.x.ai](https://console.x.ai)).
    """)

    with gr.Row():
        with gr.Column(scale=2):
            description = gr.Textbox(
                label="App Description",
                placeholder="e.g. A beautiful habit tracker with streaks, dark mode, local storage and weekly charts",
                lines=5,
            )
            project_name = gr.Textbox(label="Project Name (optional)", placeholder="habit_tracker")
            model = gr.Dropdown(
                choices=["grok-4.7", "grok-4.3", "grok-4.6", "grok-build-0.1"],
                value="grok-4.7",
                label="Model",
            )
            btn = gr.Button("Generate App", variant="primary")
        with gr.Column(scale=1):
            gr.Markdown("""
            ### Tips
            - Be specific about features
            - Mention design style if you care
            - Say if you need auth / offline / charts etc.
            """)

    output_md = gr.Markdown(label="Result")
    output_path = gr.Textbox(label="Generated project path", interactive=False)
    full_response = gr.Textbox(label="Full Grok Response (for reference)", lines=15)

    btn.click(
        fn=generate_app,
        inputs=[description, project_name, model],
        outputs=[output_md, output_path, full_response],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
