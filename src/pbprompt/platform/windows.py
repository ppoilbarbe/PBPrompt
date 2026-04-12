"""Windows-specific platform services.

Config directory : ``%APPDATA%\\pbprompt\\``
Notifications    : win10toast if available, otherwise silent
Auto-start: Windows Registry
             ``HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run``
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import platformdirs

logger = logging.getLogger(__name__)

_APP_NAME = "pbprompt"
_APP_AUTHOR = "PBMou"
_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_REG_VALUE = "PBPrompt"


def get_config_dir() -> Path:
    """Return ``%APPDATA%\\pbprompt\\``."""
    return Path(platformdirs.user_config_dir(_APP_NAME, _APP_AUTHOR))


def notify(title: str, message: str) -> None:
    """Send a Windows toast notification.

    Requires ``win10toast`` or falls back to a silent no-op.

    Parameters
    ----------
    title:
        Notification title.
    message:
        Notification body text.
    """
    try:
        from win10toast import ToastNotifier  # type: ignore[import]

        notifier = ToastNotifier()
        notifier.show_toast(title, message, duration=4, threaded=True)
    except ImportError:
        logger.debug("win10toast not installed; skipping notification.")
    except Exception:  # noqa: BLE001
        logger.debug("Windows notification failed.", exc_info=True)


def set_autostart(enabled: bool = True) -> None:
    """Add or remove the application from the Windows startup registry.

    Parameters
    ----------
    enabled:
        ``True`` to enable autostart, ``False`` to disable.
    """
    if sys.platform != "win32":
        logger.warning("set_autostart called on non-Windows platform.")
        return

    import winreg  # type: ignore[import]

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_KEY,
            0,
            winreg.KEY_SET_VALUE,
        )
        if enabled:
            import shutil

            executable = shutil.which("pbprompt") or "pbprompt"
            winreg.SetValueEx(key, _REG_VALUE, 0, winreg.REG_SZ, executable)
            logger.info("Autostart registry key set.")
        else:
            remove_autostart()
        winreg.CloseKey(key)
    except Exception:  # noqa: BLE001
        logger.warning("Failed to set autostart registry key.", exc_info=True)


def remove_autostart() -> None:
    """Remove the autostart registry entry if it exists."""
    if sys.platform != "win32":
        return

    import winreg  # type: ignore[import]

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_KEY,
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, _REG_VALUE)
        winreg.CloseKey(key)
        logger.info("Autostart registry key removed.")
    except FileNotFoundError:
        pass  # Key did not exist
    except Exception:  # noqa: BLE001
        logger.warning("Failed to remove autostart registry key.", exc_info=True)
