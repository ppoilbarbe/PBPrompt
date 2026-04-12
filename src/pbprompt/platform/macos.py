"""macOS-specific platform services.

Config directory : ``~/Library/Application Support/pbprompt/``
Notifications    : ``osascript`` display notification
Auto-start       : LaunchAgent plist in ``~/Library/LaunchAgents/``
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
_BUNDLE_ID = "com.pbsoft.pbprompt"


def get_config_dir() -> Path:
    """Return ``~/Library/Application Support/pbprompt/``."""
    return Path(platformdirs.user_config_dir(_APP_NAME, _APP_AUTHOR))


def notify(title: str, message: str) -> None:
    """Send a macOS notification via ``osascript``.

    Parameters
    ----------
    title:
        Notification title.
    message:
        Notification body text.
    """
    if shutil.which("osascript") is None:
        logger.debug("osascript not available; skipping notification.")
        return
    script = f'display notification "{message}" with title "{title}"'
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=False,
            timeout=5,
        )
    except Exception:  # noqa: BLE001
        logger.debug("osascript notification failed.", exc_info=True)


def set_autostart(enabled: bool = True) -> None:
    """Install or remove a LaunchAgent plist for login-start.

    Parameters
    ----------
    enabled:
        ``True`` to install, ``False`` to remove.
    """
    agents_dir = Path.home() / "Library" / "LaunchAgents"
    plist_file = agents_dir / f"{_BUNDLE_ID}.plist"

    if enabled:
        agents_dir.mkdir(parents=True, exist_ok=True)
        executable = shutil.which("pbprompt") or "pbprompt"
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{_BUNDLE_ID}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{executable}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
        plist_file.write_text(plist_content, encoding="utf-8")
        # Load immediately
        subprocess.run(["launchctl", "load", str(plist_file)], check=False)
        logger.info("LaunchAgent installed: %s", plist_file)
    else:
        remove_autostart()


def remove_autostart() -> None:
    """Unload and remove the LaunchAgent plist."""
    plist_file = Path.home() / "Library" / "LaunchAgents" / f"{_BUNDLE_ID}.plist"
    if plist_file.exists():
        subprocess.run(["launchctl", "unload", str(plist_file)], check=False)
        plist_file.unlink()
        logger.info("LaunchAgent removed: %s", plist_file)
