"""Настройка логирования приложения."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def configure_logging(log_file: str = "logs/app.log") -> logging.Logger:
    """Настраивает файловое и консольное логирование."""

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("crypto_lab")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


def install_excepthook(logger: logging.Logger) -> None:
    """Перехватывает необработанные исключения и пишет их в лог."""

    def handle_exception(exc_type, exc_value, exc_traceback) -> None:  # type: ignore[no-untyped-def]
        logger.exception(
            "Необработанное исключение",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception
