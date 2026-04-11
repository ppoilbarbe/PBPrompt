"""Entry point for PBPrompt application."""

from __future__ import annotations

import argparse
import logging
import sys

from PyQt5.QtWidgets import QApplication

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


def main() -> None:
    """Launch the PBPrompt application."""
    args = _parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setOrganizationName("PBSoft")
    app.setApplicationVersion(__version__)

    # Load configuration (provides log level, language, etc.)
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
    from pathlib import Path  # noqa: PLC0415

    from pbprompt.gui.main_window import MainWindow  # noqa: PLC0415

    initial_file = Path(args.file) if args.file else None
    window = MainWindow(config=config, initial_file=initial_file)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
