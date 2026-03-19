"""Главное окно приложения."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import QMainWindow, QStackedWidget

from screens.additive_knapsack_screen import AdditiveKnapsackScreen
from screens.dashboard_screen import DashboardScreen
from screens.generalized_additive_screen import GeneralizedAdditiveScreen
from screens.generalized_multiplicative_screen import GeneralizedMultiplicativeScreen
from screens.hamming_screen import HammingScreen
from screens.multiplicative_knapsack_screen import MultiplicativeKnapsackScreen
from screens.rsa_screen import RSAScreen
from services.additive_knapsack_service import AdditiveKnapsackService
from services.generalized_additive_knapsack_service import GeneralizedAdditiveKnapsackService
from services.generalized_multiplicative_knapsack_service import GeneralizedMultiplicativeKnapsackService
from services.hamming_service import HammingService
from services.multiplicative_knapsack_service import MultiplicativeKnapsackService
from services.rsa_service import RSAService


class CryptoLabWindow(QMainWindow):
    """Главное окно с навигацией по экранам."""

    def __init__(self, logger: logging.Logger, parent=None) -> None:
        super().__init__(parent)
        self.logger = logger
        self.setWindowTitle("Криптографический практикум")
        self.resize(1540, 960)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.screens: dict[str, int] = {}

        self._build_screens()
        self.navigate("dashboard")

    def _build_screens(self) -> None:
        rsa_service = RSAService()
        additive_service = AdditiveKnapsackService()
        multiplicative_service = MultiplicativeKnapsackService()
        generalized_additive_service = GeneralizedAdditiveKnapsackService()
        generalized_multiplicative_service = GeneralizedMultiplicativeKnapsackService()
        hamming_service = HammingService()

        self._register(
            "dashboard",
            DashboardScreen(
                navigate=self.navigate,
                logger=self.logger,
            ),
        )
        self._register("rsa", RSAScreen(rsa_service, lambda: self.navigate("dashboard"), self.logger))
        self._register(
            "avkr",
            AdditiveKnapsackScreen(additive_service, lambda: self.navigate("dashboard"), self.logger),
        )
        self._register(
            "mvkr",
            MultiplicativeKnapsackScreen(
                multiplicative_service,
                lambda: self.navigate("dashboard"),
                self.logger,
            ),
        )
        self._register(
            "gakp",
            GeneralizedAdditiveScreen(
                generalized_additive_service,
                lambda: self.navigate("dashboard"),
                self.logger,
            ),
        )
        self._register(
            "gmkp",
            GeneralizedMultiplicativeScreen(
                generalized_multiplicative_service,
                lambda: self.navigate("dashboard"),
                self.logger,
            ),
        )
        self._register("hamming", HammingScreen(hamming_service, lambda: self.navigate("dashboard"), self.logger))

    def _register(self, name: str, widget) -> None:  # type: ignore[no-untyped-def]
        index = self.stack.addWidget(widget)
        self.screens[name] = index

    def navigate(self, name: str) -> None:
        """Переключает экран."""

        if name not in self.screens:
            raise KeyError(f"Экран {name!r} не зарегистрирован.")
        self.stack.setCurrentIndex(self.screens[name])
