# Personal Text Manager

A personal **hotkey text expander + clipboard session manager** for Windows,
built with Python and PySide6. Save frequently used words, sentences, and
long prompts, assign a global keyboard shortcut to each one, and insert
them instantly into Claude, ChatGPT, Microsoft Word, Excel, browsers,
email clients, or any other Windows application — plus a live view of
everything you copy during the current session.

> 🔒 **100% local & offline.** Clipboard data and saved expressions never
> leave your computer. No cloud sync, no analytics, no third-party APIs.

---

## Features

### ⌨️ Hotkey Text Expander
- Save any word, sentence, or long multi-paragraph prompt and assign a
  global keyboard shortcut (e.g. `Ctrl+Alt+1`) that works system-wide —
  in Claude, ChatGPT, Word, Excel, Chrome, Edge, Notepad, email clients,
  and web forms.
- Press-to-capture hotkey assignment ("Press your desired shortcut...")
  instead of typing shortcut strings by hand.
- Automatic **conflict detection** — you're warned before two expressions
  can share the same shortcut, with an explicit override option.
- Reliable clipboard-based insertion for long text, fully preserving
  Unicode: Kurdish Sorani, Arabic, and other non-Latin scripts included.
- Categories, favorites, search, duplicate, enable/disable, and a one-click
  "Test" (copies the expression so you can paste it anywhere to preview it).

### 📋 Clipboard Session Tracking
- Continuously monitors the Windows clipboard and lists everything you
  copy during the current session — **duplicates are preserved on purpose**,
  so copying "inventory management" three times shows three entries.
- **Copy All** merges every item with a configurable separator (new line,
  blank line, comma, semicolon, or custom).
- **New Session** clears the list (with a confirmation prompt) without
  touching your saved hotkeys or settings.
- Search filters the visible list without deleting anything.
- Pause / Resume monitoring at any time.
- Export the session to TXT, CSV, or JSON.

### 🖥️ Modern Desktop Experience
- Clean, modern PySide6 interface — Dashboard, Clipboard Session,
  My Hotkeys, Favorites, Categories, and Settings.
- Light / Dark / System theme.
- System tray integration: minimizing keeps clipboard monitoring and
  hotkeys active in the background.
- Optional "Start with Windows" (via the per-user registry Run key — no
  administrator rights required).
- Import/export saved hotkeys as JSON or CSV for backup and portability.

---

## How it works (architecture notes)

- **Clipboard capture** listens to Qt's native `QClipboard.dataChanged`
  signal (event-driven, not polling), so it reliably captures one entry
  per real copy event — including repeated copies of identical text —
  without needing an artificial "clipboard changed" heuristic.
- **Text insertion** stages the expression on the clipboard, sends
  `Ctrl+V`, and restores your previous clipboard content afterwards. This
  is the most reliable way to insert long, multi-paragraph, Unicode text
  into arbitrary Windows applications without simulating thousands of
  individual keystrokes. The app always tells the clipboard monitor to
  ignore these internal writes, so staging/restoring text never shows up
  as a fake "copied" session item.
- **Global hotkeys** use the [`keyboard`](https://github.com/boppreh/keyboard)
  package, which installs a low-level Windows keyboard hook that works
  regardless of which application currently has focus.
- **Storage** is a local SQLite database (no server, no account) at
  `%APPDATA%\PersonalTextManager\data.db`.

---

## Project Structure

```text
personal-text-manager/
├── app/
│   ├── main.py              # Entry point
│   ├── config.py            # Constants, default settings/categories
│   ├── database/            # SQLite schema + CRUD (app/database/db.py)
│   ├── clipboard/           # Clipboard monitor (event-driven, self-write safe)
│   ├── hotkeys/             # Global hotkey manager, capture widget, text inserter
│   ├── models/               # Plain dataclasses (Expression, ClipboardItem, Category)
│   ├── services/             # Business logic: expressions, session, settings, import/export
│   ├── ui/
│   │   ├── main_window.py    # Wires everything together
│   │   ├── theme.py          # Light/Dark QSS stylesheets
│   │   ├── tray.py           # System tray icon & menu
│   │   ├── pages/            # Dashboard, Session, Hotkeys, Favorites, Categories, Settings
│   │   └── widgets/          # Reusable widgets (dialogs, hotkey capture, list views)
│   └── utils/                 # Logging, paths, Windows "start with Windows" registry helper
├── assets/
│   ├── icons/                 # Drop app_icon.ico here (optional — a fallback is generated)
│   └── screenshots/
├── tests/                      # pytest suite (pure-Python service/DB tests)
├── requirements.txt             # Runtime dependencies
├── requirements-dev.txt         # + pytest, PyInstaller
├── build.py                     # PyInstaller build script -> dist/PersonalTextManager.exe
├── .github/workflows/build.yml  # CI: tests + builds the .exe on every push, releases on tags
└── README.md
```

---

## Getting Started (running from source)

**Requirements:** Windows 10/11, Python 3.11+.

```powershell
# 1. Clone your repository
git clone https://github.com/<your-username>/personal-text-manager.git
cd personal-text-manager

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python -m app.main
```

On first launch, the app creates its local database at
`%APPDATA%\PersonalTextManager\data.db` and seeds it with a starter set of
categories. Nothing is sent anywhere.

---

## Building the standalone .exe

### Locally, on Windows
```powershell
pip install -r requirements-dev.txt
python build.py
```
This produces `dist/PersonalTextManager.exe` — a single file that runs on
any Windows 10/11 PC **without** requiring Python to be installed.

### Via GitHub Actions (recommended)
This repository already includes `.github/workflows/build.yml`, which:
1. Checks out the repo on a `windows-latest` runner.
2. Installs Python and dependencies.
3. Runs the full test suite.
4. Builds the Windows executable with `build.py`.
5. Uploads it as a downloadable **workflow artifact** on every push/PR.
6. On any pushed tag matching `v*` (e.g. `v1.0.0`), also publishes a
   **GitHub Release** with the `.exe` attached.

To use it:
```powershell
git add .
git commit -m "Initial commit"
git push origin main
```
Then open your repo on GitHub → **Actions** tab → the latest **Build**
run → **Artifacts** → download `PersonalTextManager-windows-exe`.

To cut a proper release with a downloadable `.exe` on the Releases page:
```powershell
git tag v1.0.0
git push origin v1.0.0
```

---

## Running the tests

```powershell
pip install -r requirements-dev.txt
pytest tests/ -v
```
The suite covers expression CRUD, hotkey conflict detection and override,
clipboard session duplicate-preservation, search-without-delete, "New
Session" numbering resets, session trimming, settings, and JSON/CSV
import/export — including round-tripping Kurdish Sorani Unicode text.

---

## Configuration reference (Settings page)

| Section | Option | Notes |
|---|---|---|
| Clipboard | Enable clipboard monitoring | Master on/off switch |
| Clipboard | Start monitoring automatically | Applies on next launch |
| Clipboard | Ignore empty clipboard content | Skips empty/whitespace-only copies |
| Clipboard | Maximum session items | Oldest items are trimmed once exceeded |
| Clipboard | Copy separator | New line / blank line / comma / semicolon / custom |
| Hotkeys | Enable global hotkeys | Master on/off switch |
| Hotkeys | Insertion method | Clipboard paste (recommended) or keystroke simulation |
| Hotkeys | Conflict behavior | Block (ask) or always override |
| Appearance | Theme | Light / Dark / System |
| Startup | Start with Windows | Uses the per-user registry Run key, no admin needed |
| Startup | Start minimized / in tray | Controls initial window state |

---

## Privacy

Clipboard data and saved expressions are processed **entirely locally** on
your computer in a local SQLite database. This application does not upload
clipboard contents or expressions to any cloud server, analytics service,
third-party API, or AI service — and never will, unless a future feature
explicitly asks for your consent first. Application logs record only
technical events (e.g. "hotkey registration failed") and never clipboard
or expression content.

---

## Troubleshooting

- **Hotkeys don't trigger anywhere:** confirm Settings → Hotkeys → "Enable
  global hotkeys" is on, and that the `keyboard` package installed
  correctly (`pip show keyboard`). Some games/anti-cheat software block
  low-level keyboard hooks system-wide — this is a known limitation of any
  hotkey utility, not specific to this app.
- **Pasted text looks wrong in a particular app:** switch Settings →
  Hotkeys → Insertion method to "Keystroke simulation" as a fallback for
  apps that block programmatic paste.
- **Nothing appears when I copy text:** check Settings → Clipboard →
  "Enable clipboard monitoring", and confirm monitoring isn't paused
  (Dashboard shows "● Active" / "○ Paused").

---

## License

MIT — see [LICENSE](LICENSE).
