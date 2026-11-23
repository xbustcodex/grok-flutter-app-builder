# Grok Flutter App Builder

Turn Grok into a Flutter app generator for **Android + Desktop**.

This is currently a **source-code generator + helper**, not a fully automatic one-click APK/EXE factory.

## Current status

| Area                              | Status                                      |
|-----------------------------------|---------------------------------------------|
| Python CLI                        | Implemented                                 |
| Gradio web UI                     | Implemented                                 |
| Grok API integration              | Implemented (requires paid API key)         |
| Flutter source generation         | Implemented                                 |
| Path sanitization / safety        | Implemented                                 |
| Basic build verification helper   | Implemented (`build_helper.py`)             |
| Automatic Windows EXE compilation | Partial – helper attempts `flutter build`   |
| Automatic Android APK compilation | Partial – helper attempts `flutter build`   |
| Full signing & store packaging    | Not implemented (you finish these steps)    |
| Multi-framework (RN, Electron…)   | Roadmap only                                |

## Important notes

1. **API cost** – The CLI and web UI call the official xAI API (`api.x.ai`). This is separate from any Grok website / X subscription and is billed by token usage. Check [console.x.ai](https://console.x.ai) for pricing.

2. **Compilation** – Fully automatic production-ready APKs and signed Windows executables require a properly configured Flutter + Android SDK + Visual Studio environment on the machine that runs the build. The included `build_helper.py` will attempt the builds and give clear feedback, but it cannot magically install missing SDKs or signing keys for you.

3. **Security** – Generated file paths are sanitized to prevent directory traversal. The Gradio UI binds to `127.0.0.1` by default.

## Quick start

```bash
# 1. API key
export XAI_API_KEY=xai-...

# 2. Dependencies
pip install -r requirements.txt

# 3. Generate an app
python flutter_app_builder_cli.py --name habit_tracker "Habit tracker with streaks, dark mode and local storage"

# 4. Enter the project and verify / build
cd habit_tracker
python ../build_helper.py --all          # or --android / --windows
flutter run -d windows                   # or android / chrome
```

### Web UI

```bash
python web_ui.py
# then open http://127.0.0.1:7860
```

### System prompt only

Copy the content of `flutter_app_builder_system_prompt.md` into any Grok chat as the system message.

## Files

- `flutter_app_builder_cli.py` – Command-line generator
- `web_ui.py` – Local Gradio interface (localhost only)
- `build_helper.py` – Attempt `flutter pub get`, analyze, and platform builds
- `flutter_app_builder_system_prompt.md` – Persona / system prompt
- `requirements.txt` – `openai` + `gradio`

## Roadmap (honest)

Priority order:

1. Better validation & automatic repair loops (feed build errors back to Grok)
2. More reliable file extraction + project scaffolding
3. Optional support for other stacks (React Native, Tauri, etc.)
4. Deeper integration with signing / packaging once the core generation is solid

## Contributing / feedback

Open issues or PRs on this repo. The most valuable feedback is real build failures from generated projects so the prompt and helpers can be improved.
