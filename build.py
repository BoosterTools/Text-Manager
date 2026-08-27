"""
Builds a standalone Windows executable with PyInstaller.

Usage (on Windows, with requirements-dev.txt installed):

    python build.py

Produces dist/PersonalTextManager.exe — a single-file executable that does
NOT require Python to be installed on the target machine.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = "PersonalTextManager"
ENTRY_POINT = ROOT / "app" / "main.py"
ICON_PATH = ROOT / "assets" / "icons" / "app_icon.ico"
ASSETS_DIR = ROOT / "assets"


def main() -> int:
    if sys.platform != "win32":
        print(
            "WARNING: this produces a Windows executable and is normally run "
            "on Windows (or Windows via GitHub Actions). Continuing anyway "
            "so the build can still be inspected/tested locally.",
            file=sys.stderr,
        )

    try:
        import PyInstaller.__main__  # noqa: F401
    except ImportError:
        print(
            "PyInstaller is not installed. Run: pip install -r requirements-dev.txt",
            file=sys.stderr,
        )
        return 1

    # Clean previous build artifacts so stale files never sneak into a release.
    for stale in ("build", "dist", f"{APP_NAME}.spec"):
        path = ROOT / stale
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            path.unlink(missing_ok=True)

    add_data_sep = ";" if sys.platform == "win32" else ":"

    args = [
        str(ENTRY_POINT),
        "--name", APP_NAME,
        "--onefile",
        "--windowed",  # no console window for a GUI app
        "--noconfirm",
        "--add-data", f"{ASSETS_DIR}{add_data_sep}assets",
        "--hidden-import", "keyboard",
        "--hidden-import", "PySide6.QtSvg",
    ]

    if ICON_PATH.exists():
        args += ["--icon", str(ICON_PATH)]
    else:
        print(
            f"NOTE: no icon found at {ICON_PATH} — building without a custom "
            "icon. Drop an .ico file there to brand the executable."
        )

    import PyInstaller.__main__

    print("Running PyInstaller with args:", " ".join(args))
    PyInstaller.__main__.run(args)

    exe_path = ROOT / "dist" / f"{APP_NAME}.exe"
    if exe_path.exists():
        print(f"\nBuild succeeded: {exe_path}")
        return 0
    print("\nBuild finished but the expected executable was not found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
