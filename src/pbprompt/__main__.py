"""Entry point for PBPrompt application."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from pbprompt import __app_name__, __description__, __version__
from pbprompt.config import AppConfig
from pbprompt.i18n import setup_i18n


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pbprompt",
        description=__description__,
        epilog=(
            "Prompts are stored in a YAML file and can be translated via multiple "
            "online services (Google, DeepL, MyMemory, …). "
            "Use File › Open to load an existing file or File › New to start fresh."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--log-level",
        metavar="LEVEL",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="override the log level set in the configuration file "
        "(DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    parser.add_argument(
        "--config",
        metavar="DIR",
        default=None,
        help="use DIR as the configuration directory instead of the platform "
        "default (e.g. ~/.config/pbprompt on Linux); config.yaml is read from "
        "and written to DIR",
    )
    parser.add_argument(
        "file",
        nargs="?",
        metavar="FILE",
        help=(
            "YAML prompt file to open on startup. "
            "Takes priority over the last-used file (auto-load is skipped). "
            "If the file cannot be read, an error dialog explains the reason "
            "and an empty list is loaded."
        ),
    )
    return parser.parse_args()


def _load_bundled_fonts(app: object) -> None:
    """Register bundled fonts and set a reliable default font (frozen builds only).

    The libfontconfig.so bundled by PyInstaller has its default config path
    hardcoded to the build machine's conda prefix.  On any other machine that
    path is missing and fontconfig fails silently, leaving Qt with no valid
    system font.  This function bypasses fontconfig for font selection:
      1. All bundled .ttf files are registered in Qt's font database.
      2. Ubuntu (shipped with fonts-conda-ecosystem) is set as the application
         font so the UI always looks correct regardless of the host configuration.
    The runtime hook (rthook_fonts.py) still generates a portable fonts.conf so
    that fontconfig rendering settings (anti-aliasing, hinting…) are inherited
    from the system /etc/fonts/fonts.conf.
    """
    if not getattr(sys, "frozen", False):
        return
    from pathlib import Path

    from PySide6.QtGui import QFont, QFontDatabase

    fonts_dir = Path(sys._MEIPASS) / "fonts"  # type: ignore[attr-defined]
    if not fonts_dir.is_dir():
        return

    loaded: set[str] = set()
    for ttf in sorted(fonts_dir.glob("*.ttf")):
        fid = QFontDatabase.addApplicationFont(str(ttf))
        if fid >= 0:
            loaded.update(QFontDatabase.applicationFontFamilies(fid))

    # Set Ubuntu as the default application font so the bundle renders
    # consistently on any machine, regardless of whether fontconfig finds
    # the system config.
    if "Ubuntu" in loaded:
        current = app.font()  # type: ignore[union-attr]
        app.setFont(  # type: ignore[union-attr]
            QFont("Ubuntu", current.pointSize() if current.pointSize() > 0 else 10)
        )


def main() -> None:
    """Launch the PBPrompt application."""
    args = _parse_args()

    app = QApplication(sys.argv)
    _load_bundled_fonts(app)
    app.setApplicationName(__app_name__)
    app.setOrganizationName("PBMou")
    app.setApplicationVersion(__version__)

    # Load configuration (provides log level, language, etc.)
    if args.config:
        AppConfig.set_config_dir(Path(args.config))
    config = AppConfig.load()

    # Configure logging (CLI flag overrides config file)
    log_level_name = args.log_level or config.log_level
    logging.basicConfig(
        level=getattr(logging, log_level_name, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting %s %s", __app_name__, __version__)

    # Initialise i18n *before* building any GUI widgets
    setup_i18n(config.display_language)

    # Import GUI *after* i18n so all translatable strings are ready
    from pbprompt.gui.main_window import MainWindow  # noqa: PLC0415

    initial_file = Path(args.file) if args.file else None
    window = MainWindow(config=config, initial_file=initial_file)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
