"""Экран «О программе»."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtWidgets import QPushButton, QWidget

from screens.base_screen import ScrollScreen
from ui.components import build_info_grid, create_info_card


class AboutScreen(ScrollScreen):
    """Экран с общей информацией о проекте."""

    def __init__(
        self,
        on_back: Callable[[], None],
        logger: logging.Logger,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="О программе",
            subtitle="Учебный проект для демонстрации криптографических алгоритмов и кода Хэмминга.",
            logger=logger,
            parent=parent,
        )
        self.on_back = on_back
        self._build_ui()

    def _build_ui(self) -> None:
        cards = [
            create_info_card(
                "Какие темы включены",
                "RSA, классические и обобщённые рюкзачные криптосистемы, а также Hamming [7,4].",
            ),
            create_info_card(
                "Как использовать",
                "Откройте нужный модуль с главной страницы, сгенерируйте параметры, "
                "введите сообщение и просмотрите вычисления.",
            ),
            create_info_card(
                "Учебная направленность",
                "Схемы специально сделаны прозрачными: показываются ключи, преобразования, "
                "криптограммы и ограничения криптостойкости.",
            ),
            create_info_card(
                "Архитектура",
                "GUI отделён от математической логики. Сервисы находятся в `services/`, "
                "модели — в `models/`, общие утилиты — в `utils/`.",
            ),
        ]
        self.content_layout.addWidget(build_info_grid(cards))

        back_button = QPushButton("Назад на главную")
        back_button.clicked.connect(self.on_back)
        self.content_layout.addWidget(back_button)
