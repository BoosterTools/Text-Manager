"""
Resolves where the application stores its persistent data.

On Windows this resolves to %APPDATA%\\PersonalTextManager. On other
platforms (used for running the test-suite / development) it falls back
to a local ``.data`` folder or ``~/.personal-text-manager``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from app.config import ORG_NAME


def get_app_data_dir() -> Path:
    """Return (and create if needed) the directory used for app data."""
    override = os.environ.get("PTM_DATA_DIR")
    if override:
        path = Path(override)
    elif sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home())
        path = Path(base) / ORG_NAME
    else:
        path = Path.home() / f".{ORG_NAME.lower()}"

    path.mkdir(parents=True, exist_ok=True)
    return path


def get_database_path() -> Path:
    return get_app_data_dir() / "data.db"


def get_log_path() -> Path:
    log_dir = get_app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "app.log"


def get_icon_path() -> Path:
    # When frozen by PyInstaller, assets are unpacked next to the exe
    # under sys._MEIPASS.
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent.parent.parent
    return base / "assets" / "icons" / "app_icon.ico"
