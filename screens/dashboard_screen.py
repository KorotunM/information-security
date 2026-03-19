"""Главная страница приложения."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QPushButton, QWidget

from screens.base_screen import ScrollScreen


class DashboardScreen(ScrollScreen):
    """Главный экран со списком доступных модулей."""

    def __init__(
        self,
        navigate: Callable[[str], None],
        logger: logging.Logger,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="",
            subtitle="",
            logger=logger,
            parent=parent,
        )
        self.navigate = navigate
        self._build_ui()

    def _build_ui(self) -> None:
        cards = QWidget()
        grid = QGridLayout(cards)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        modules = [
            ("rsa", "RSA"),
            ("avkr", "Классический АВКР"),
            ("mvkr", "Классический МВКР"),
            ("gakp", "Обобщённый АВКР"),
            ("gmkp", "Обобщённый МВКР"),
            ("hamming", "Код Хэмминга"),
        ]

        for index, (screen_name, title) in enumerate(modules):
            button = QPushButton(title)
            button.setObjectName("DashboardCard")
            button.setMinimumHeight(110)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _=False, name=screen_name: self.navigate(name))
            grid.addWidget(button, index // 2, index % 2)

        self.content_layout.addWidget(cards)
