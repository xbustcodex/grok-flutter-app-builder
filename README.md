# Grok Flutter App Builder

A specialized **system prompt + local CLI + web UI** that turns Grok into a Flutter app generator for **Android + Desktop (Windows / macOS / Linux)**.

> **Honest status (Nov 2026)**  
> This is currently a **high-quality source-code generator**.  
> Automatic Windows EXE / Android APK compilation, full build verification, and self-healing are **not yet complete**.  
> A basic `build_helper.py` is included as the first step toward that pipeline.

## What you get

| Component | Status |
|-----------|--------|
| System prompt / persona | Ready |
| Python CLI | Ready (with path sanitization) |
| Gradio web UI | Ready (localhost only by default) |
| Grok API integration | Ready – **xAI + OpenRouter** |
| Flutter source generation | Ready – always validate output |
| Automatic Windows EXE | Not yet (use `build_helper.py` + Flutter SDK) |
| Automatic Android APK | Not yet (use `build_helper.py` + Flutter SDK) |
| Build verification & repair | Not yet |

## Security notes

- Generated file paths are sanitized (`_safe_rel_path`) to prevent directory traversal.
- The Gradio web UI binds to **127.0.0.1** by default (not 0.0.0.0).
- `requirements.txt` includes both `openai` and `gradio`.

## Cost note & providers

This tool talks to an OpenAI-compatible API. It does **not** use a Grok website / SuperGrok chat subscription.

Supported providers:

| Provider   | Env var              | Base URL                          | Notes |
|------------|----------------------|-----------------------------------|-------|
| **xAI** (official) | `XAI_API_KEY`     | `https://api.x.ai/v1`            | Direct from xAI |
| **OpenRouter**     | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1` | Easy billing, many models, use `x-ai/grok-4.7` etc. |

Set `GROK_PROVIDER=xai|openrouter|auto` (default `auto` prefers OpenRouter if its key is present).

## Quick Start (CLI)

```bash
# 1. API key (pick one)
export XAI_API_KEY=xai-your-key-here          # official xAI
# or
export OPENROUTER_API_KEY=sk-or-v1-...       # OpenRouter

# Optional: force provider
# export GROK_PROVIDER=openrouter

# 2. Dependencies
pip install -r requirements.txt

# 3. Generate
python flutter_app_builder_cli.py --name habit_tracker "A habit tracker with streaks, dark mode and local storage"

# With explicit provider / model
python flutter_app_builder_cli.py --provider openrouter --model x-ai/grok-4.7 "..."

# 4. Resolve dependencies + optional build
python build_helper.py habit_tracker
python build_helper.py habit_tracker --platform windows --release
python build_helper.py habit_tracker --platform android --release
```

## Web UI

```bash
pip install -r requirements.txt
export XAI_API_KEY=xai-...   # or OPENROUTER_API_KEY=sk-or-...
python web_ui.py
# → http://127.0.0.1:7860
```

## Using the System Prompt only

1. Open `flutter_app_builder_system_prompt.md`
2. Copy the prompt under the horizontal line
3. Paste it as the System Prompt in any Grok client or the API
4. Describe the app you want

## Recommended models

- `grok-4.7` (default) – strongest for code
- `grok-4.3` – cheaper, still excellent
- `grok-build-0.1` – specialized coding model (if available)

On OpenRouter use the `x-ai/` prefix, e.g. `x-ai/grok-4.7`.

## Roadmap (priority order)

1. **Finish the compilation & verification pipeline**
   - Automatic `flutter pub get` + platform builds
   - Capture and surface compiler errors
   - Optional “repair” loop that feeds errors back to Grok
2. Better validation of generated Flutter projects
3. Optional support for other stacks (React Native, Tauri, etc.)

## Example prompts

- “A minimalist expense tracker with categories, monthly charts, and CSV export”
- “A desktop-first markdown notes app with folders, search, and live preview”
- “A cross-platform pomodoro timer with task list, stats, and system tray support”

## License

MIT (or whatever you prefer – currently no formal license file).

Enjoy building – and please treat the generated code as a strong starting point that still needs human review and testing.
