# arabic-tashkeel-app

Automatic Arabic Diacritization Desktop App (PySide6)

## Features
- Accepts multiline Arabic text and applies diacritics automatically.
- RTL-aware input/output with crisp modern styling.
- Uses the open-source **camel-tools** pretrained diacritizer when installed, otherwise falls back to a lightweight heuristic diacritizer (documented below).
- Handles large texts on a background thread to keep the UI responsive.
- Single-file source (`tashkeel_app.py`) for easy deployment.

## Environment setup (Garuda/Arch Linux, virtualenv)
```bash
# 1) Create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2) Upgrade pip
pip install --upgrade pip

# 3) Install dependencies (PySide6 is required; camel-tools is recommended for best quality)
pip install PySide6 camel-tools==1.5.5
# If camel-tools fails to build, install only PySide6; the app will use the heuristic fallback.
```

## Run the app
```bash
source .venv/bin/activate
python tashkeel_app.py
```

## Usage
1. Paste or type Arabic text in the left pane (RTL supported).
2. Click **تشكيــل** to diacritize. Processing happens on a background thread.
3. Copy the diacritized text from the right pane using **نسخ النص المشكّل**.
4. Use **مسح** to clear both panes.

## Replacing the fallback diacritizer
The app automatically detects `camel_tools` if available. To plug in another model:
- Replace `HeuristicDiacritizer.diacritize` in `tashkeel_app.py` with your own implementation that accepts and returns a string.
- Alternatively, instantiate your model inside `DiacritizerEngine` and return its output; the UI will surface the model name via `DiacritizationResult.model_name`.

## Notes
- High DPI scaling is enabled for crisp rendering.
- The UI remains responsive even for large inputs because diacritization runs on a dedicated worker thread.
