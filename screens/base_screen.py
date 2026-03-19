"""Базовые классы экранов."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from ui.components import StepsDialog, create_subtitle_label, create_title_label, show_error
from utils.validation import InputValidationError


class ScrollScreen(QWidget):
    """Базовый экран со скроллом."""

    def __init__(
        self,
        title: str,
        subtitle: str,
        logger: logging.Logger,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.logger = logger
        self.last_steps = ""

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.content_layout = QVBoxLayout(container)
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(16)
        if title:
            self.content_layout.addWidget(create_title_label(title))
        if subtitle:
            self.content_layout.addWidget(create_subtitle_label(subtitle))

        scroll.setWidget(container)
        root_layout.addWidget(scroll)

    def run_action(self, action: Callable[[], None]) -> None:
        """Безопасно выполняет обработчик кнопки."""

        try:
            action()
        except InputValidationError as error:
            show_error(self, str(error))
        except Exception as error:  # pragma: no cover - защитная ветка GUI
            self.logger.exception("Необработанная ошибка GUI")
            show_error(self, f"Произошла внутренняя ошибка: {error}")

    def set_steps(self, text: str) -> None:
        """Запоминает последние шаги вычислений."""

        self.last_steps = text

    def show_steps_dialog(self, title: str) -> None:
        """Показывает модальное окно с шагами вычислений."""

        StepsDialog(title, self.last_steps, self).exec()
