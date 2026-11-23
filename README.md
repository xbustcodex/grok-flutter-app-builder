# Grok Flutter App Builder

A specialized **system prompt + local CLI tool** that turns Grok into a powerful Flutter app generator for **Android + Desktop (Windows/macOS/Linux)**.

## What you get

1. **System Prompt** (`flutter_app_builder_system_prompt.md`)  
   Copy-paste into any Grok chat (or set as the system message in the API) to turn Grok into a dedicated Flutter app architect.

2. **Local CLI** (`flutter_app_builder_cli.py`)  
   A Python script that calls the official xAI Grok API, generates a complete Flutter project from a natural-language description, and writes all the files to disk.

## Quick Start (CLI)

### 1. Get an API key
- Go to https://console.x.ai
- Create an API key
- Export it:

```bash
export XAI_API_KEY=xai-your-key-here
```

### 2. Install dependency
```bash
pip install openai
```

### 3. Run the builder

**One-liner:**
```bash
python flutter_app_builder_cli.py "A beautiful habit tracker with streaks, dark mode, and local storage"
```

**Interactive (multi-line description):**
```bash
python flutter_app_builder_cli.py --interactive
```

**Named project:**
```bash
python flutter_app_builder_cli.py --name habit_tracker "Habit tracker with daily goals and charts"
```

### 4. Run the generated app
```bash
cd habit_tracker          # or whatever the folder is called
flutter pub get
flutter run -d windows    # or macos / linux / chrome / android
```

## Using the System Prompt only (no CLI)

1. Open `flutter_app_builder_system_prompt.md`
2. Copy the entire prompt under the horizontal line
3. Paste it as the **System Prompt** in:
   - https://grok.x.ai (or the chat interface you use)
   - Any OpenAI-compatible client pointed at `https://api.x.ai/v1`
4. Then just say:  
   “Build me a Flutter todo app with categories and cloud sync using Firebase”

Grok will reply with a full project structure + every source file.

## Recommended models
- `grok-4.7` (default) – strongest overall, especially for code
- `grok-4.3` – cheaper & still excellent for most apps
- `grok-build-0.1` – specialized coding model (if available)

## Tips for best results
- Be specific about features, design style, and whether you need auth / offline / charts / etc.
- After the first generation, you can continue the conversation: “Add a settings screen with theme switcher” or “Make the list reorderable”.
- The CLI always saves the raw Grok response as `GROK_RESPONSE.md` inside the project folder in case any file extraction missed something.

## Example prompts that work well
- “A minimalist expense tracker with categories, monthly charts, and CSV export”
- “A desktop-first markdown notes app with folders, search, and live preview”
- “A cross-platform pomodoro timer with task list, stats, and system tray support”
- “A simple Instagram-style photo gallery that works offline and supports desktop drag-and-drop”

Enjoy building!
