"""Точка входа в приложение."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.application import CryptoLabWindow
from app.styles import APP_STYLESHEET
from utils.logger import configure_logging, install_excepthook


def main() -> int:
    """Запускает Qt-приложение."""

    logger = configure_logging()
    install_excepthook(logger)

    app = QApplication(sys.argv)
    app.setApplicationName("Криптографический практикум")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)

    window = CryptoLabWindow(logger=logger)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
