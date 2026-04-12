"""Linux-specific platform services.

Config directory : ``~/.config/pbprompt/``  (XDG_CONFIG_HOME)
Notifications    : ``notify-send`` (fallback: silent)
Auto-start       : ``~/.config/autostart/pbprompt.desktop``
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

import platformdirs

logger = logging.getLogger(__name__)

_APP_NAME = "pbprompt"
_APP_AUTHOR = "PBMou"


def get_config_dir() -> Path:
    """Return ``~/.config/pbprompt/`` (XDG-compliant)."""
    return Path(platformdirs.user_config_dir(_APP_NAME, _APP_AUTHOR))


def notify(title: str, message: str) -> None:
    """Send a desktop notification via ``notify-send`` if available.

    Parameters
    ----------
    title:
        Notification title.
    message:
        Notification body text.
    """
    if shutil.which("notify-send") is None:
        logger.debug("notify-send not found; skipping notification.")
        return
    try:
        subprocess.run(
            ["notify-send", title, message],
            check=False,
            timeout=5,
        )
    except Exception:  # noqa: BLE001
        logger.debug("notify-send failed.", exc_info=True)


def set_autostart(enabled: bool = True) -> None:
    """Create or remove the XDG autostart .desktop file.

    Parameters
    ----------
    enabled:
        ``True`` to install autostart, ``False`` to remove it.
    """
    autostart_dir = Path.home() / ".config" / "autostart"
    desktop_file = autostart_dir / "pbprompt.desktop"

    if enabled:
        autostart_dir.mkdir(parents=True, exist_ok=True)
        executable = shutil.which("pbprompt") or "pbprompt"
        content = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=PBPrompt\n"
            f"Exec={executable}\n"
            "Comment=AI Prompt Manager\n"
            "X-GNOME-Autostart-enabled=true\n"
        )
        desktop_file.write_text(content, encoding="utf-8")
        logger.info("Autostart file created: %s", desktop_file)
    else:
        remove_autostart()


def remove_autostart() -> None:
    """Remove the XDG autostart .desktop file if it exists."""
    desktop_file = Path.home() / ".config" / "autostart" / "pbprompt.desktop"
    if desktop_file.exists():
        desktop_file.unlink()
        logger.info("Autostart file removed: %s", desktop_file)
