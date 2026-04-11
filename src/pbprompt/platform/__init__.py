"""Platform-abstraction layer.

OS-specific config paths are funnelled through this module.  The rest of
the application imports only from here, never from the individual
``linux``, ``windows`` or ``macos`` sub-modules.

Example
-------
    from pbprompt.platform import get_config_dir

    cfg_dir = get_config_dir()
"""

from __future__ import annotations

import sys

# ---------------------------------------------------------------------------
# Dynamic import of the right platform implementation
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    from pbprompt.platform.windows import get_config_dir  # noqa: F401
elif sys.platform == "darwin":
    from pbprompt.platform.macos import get_config_dir  # noqa: F401
else:  # Linux and other POSIX systems
    from pbprompt.platform.linux import get_config_dir  # noqa: F401


__all__ = ["get_config_dir"]
