"""
Enable/disable launching the app automatically when Windows starts, via the
per-user Run registry key (HKCU). No administrator privileges required.
"""
from __future__ import annotations

import sys

from app.config import APP_NAME

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _winreg():
    if sys.platform != "win32":
        return None
    import winreg  # type: ignore

    return winreg


def is_enabled() -> bool:
    winreg = _winreg()
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable(executable_path: str, args: str = "--minimized") -> bool:
    winreg = _winreg()
    if winreg is None:
        return False
    command = f'"{executable_path}" {args}'.strip()
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        return True
    except OSError:
        return False


def disable() -> bool:
    winreg = _winreg()
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, APP_NAME)
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False
