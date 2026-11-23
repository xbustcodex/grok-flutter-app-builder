# Grok Flutter App Builder

Turn Grok into a Flutter app generator for **Android + Desktop** (Windows / macOS / Linux).

## Current status

| Feature | Status |
|---------|--------|
| System prompt / persona | Ready |
| CLI + Gradio web UI | Ready |
| Multi-provider API | **xAI · OpenRouter · Together · Fireworks · Generic** |
| Path sanitization | Ready |
| Localhost-only web UI | Ready |
| `flutter pub get` + `analyze` | Ready (`build_helper.py`) |
| Windows EXE / Android APK build | **Ready** (requires Flutter SDK) |
| Automatic repair loop | **Ready** (`--repair`) |
| Full self-healing CI-style pipeline | In progress |

## Providers

| Provider | Env var | Notes |
|----------|---------|-------|
| **xAI** (official) | `XAI_API_KEY` | `https://api.x.ai/v1` |
| **OpenRouter** | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1` |
| **Together** | `TOGETHER_API_KEY` | `https://api.together.xyz/v1` |
| **Fireworks** | `FIREWORKS_API_KEY` | `https://api.fireworks.ai/inference/v1` |
| **Generic** | `BASE_URL` + `API_KEY` | Any OpenAI-compatible endpoint |

`GROK_PROVIDER=auto|xai|openrouter|together|fireworks|generic` (default `auto`).

## Quick start

```bash
# 1. Key (pick one)
export XAI_API_KEY=xai-...
# or
export OPENROUTER_API_KEY=sk-or-v1-...
# or
export TOGETHER_API_KEY=...
# or generic:
export BASE_URL=https://your-endpoint/v1
export API_KEY=...

# 2. Install
pip install -r requirements.txt

# 3. Generate
python flutter_app_builder_cli.py --name habit_tracker \
  "A habit tracker with streaks, dark mode and local storage"

# 4. Verify + build (Windows EXE example)
python build_helper.py habit_tracker --platform windows --release

# Or let the CLI do it in one shot:
python flutter_app_builder_cli.py --name habit_tracker --build windows --repair \
  "A habit tracker..."

# Android APK
python build_helper.py habit_tracker --platform android --release --repair
```

## Web UI

```bash
python web_ui.py
# → http://127.0.0.1:7860
```

## Build helper details

```bash
python build_helper.py <project_dir> [options]

Options:
  --platform windows|android|linux|macos|web|all
  --release
  --repair          # if analyze/build fails, ask Grok to fix and retry once
  --provider ...    # which API to use for the repair pass
  --skip-analyze
```

The repair pass feeds the error log + key source files back to Grok and applies the returned patches (path-sanitized).

## Security

- All generated / repaired paths go through `_safe_rel_path` (no `..`, no absolute paths).
- Web UI listens on `127.0.0.1` only.

## Cost

Uses the paid API of the provider you configure. Does **not** use a Grok website subscription.

## Roadmap

1. Better multi-file repair and iterative fix loops
2. Project template validation before first build
3. Optional other stacks (React Native, Tauri, …)

## License

MIT-style – use freely.
