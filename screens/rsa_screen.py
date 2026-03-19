"""Экран RSA."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from models.crypto_models import RSAKeyPair
from screens.base_screen import ScrollScreen
from services.rsa_service import RSAService
from ui.components import (
    KeyValueTable,
    create_action_button,
    create_multiline_output,
    create_section,
)
from utils.validation import InputValidationError, parse_int


class RSAScreen(ScrollScreen):
    """Экран учебной криптосистемы RSA."""

    def __init__(
        self,
        service: RSAService,
        on_back: Callable[[], None],
        logger: logging.Logger,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="RSA",
            subtitle="",
            logger=logger,
            parent=parent,
        )
        self.service = service
        self.on_back = on_back
        self.current_key_pair: RSAKeyPair | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QGridLayout()
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        input_panel = create_section("Параметры и сообщения")
        form = QFormLayout(input_panel)
        form.setSpacing(10)

        self.p_edit = QLineEdit()
        self.q_edit = QLineEdit()
        self.e_edit = QLineEdit()
        self.e_edit.setPlaceholderText("Если пусто, будет выбран e автоматически")

        pq_buttons = QWidget()
        pq_layout = QHBoxLayout(pq_buttons)
        pq_layout.setContentsMargins(0, 0, 0, 0)
        pq_layout.setSpacing(8)
        auto_button = create_action_button("Автогенерация p и q")
        auto_button.clicked.connect(lambda: self.run_action(self.auto_generate_primes))
        pq_layout.addWidget(auto_button)

        self.plaintext_edit = create_multiline_output(read_only=False)
        self.plaintext_edit.setPlaceholderText("Только строчные английские буквы и пробел")
        self.ciphertext_edit = create_multiline_output(read_only=False)
        self.decrypted_edit = create_multiline_output(read_only=True)

        form.addRow("p:", self.p_edit)
        form.addRow("q:", self.q_edit)
        form.addRow("e:", self.e_edit)
        form.addRow("", pq_buttons)
        form.addRow("Открытый текст:", self.plaintext_edit)
        form.addRow("Шифртекст:", self.ciphertext_edit)
        form.addRow("Расшифрованный текст:", self.decrypted_edit)

        output_panel = create_section("Промежуточные данные")
        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(14, 14, 14, 14)
        output_layout.setSpacing(10)

        self.key_table = KeyValueTable()
        self.key_table.set_mapping(
            {"p": "-", "q": "-", "n": "-", "phi(n)": "-", "e": "-", "d": "-"}
        )
        output_layout.addWidget(self.key_table)

        self.steps_output = create_multiline_output(read_only=True)
        steps_section = create_section("Пошаговые вычисления", self.steps_output)

        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        buttons = [
            ("Сгенерировать ключи", self.generate_keys),
            ("Зашифровать", self.encrypt_text),
            ("Расшифровать", self.decrypt_text),
            ("Очистить", self.clear_form),
            ("Показать шаги", self.show_steps),
            ("Пример", self.load_example),
            ("Назад на главную", self.on_back),
        ]
        for label, handler in buttons:
            button = create_action_button(label)
            button.clicked.connect(lambda _=False, callback=handler: self.run_action(callback))
            actions_layout.addWidget(button)

        layout.addWidget(input_panel, 0, 0)
        layout.addWidget(output_panel, 0, 1)
        layout.addWidget(actions, 1, 0, 1, 2)
        layout.addWidget(steps_section, 2, 0, 1, 2)

        wrapper = QWidget()
        wrapper.setLayout(layout)
        self.content_layout.addWidget(wrapper)

    def generate_keys(self) -> None:
        p = parse_int(self.p_edit.text(), "p", minimum=2)
        q = parse_int(self.q_edit.text(), "q", minimum=2)
        e_text = self.e_edit.text().strip()
        e = parse_int(e_text, "e", minimum=2) if e_text else None

        self.current_key_pair, steps = self.service.generate_keys(p, q, e)
        self._update_key_table(self.current_key_pair)
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def auto_generate_primes(self) -> None:
        key_pair, steps = self.service.auto_generate_keys(bit_length=10)
        self.current_key_pair = key_pair
        self.p_edit.setText(str(key_pair.p))
        self.q_edit.setText(str(key_pair.q))
        self.e_edit.setText(str(key_pair.e))
        self._update_key_table(key_pair)
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def encrypt_text(self) -> None:
        key_pair = self._require_key_pair()
        payload = self.service.encrypt_text(self.plaintext_edit.toPlainText(), key_pair)
        self.ciphertext_edit.setPlainText(payload.encoded)
        self.steps_output.setPlainText(payload.steps)
        self.set_steps(payload.steps)

    def decrypt_text(self) -> None:
        key_pair = self._require_key_pair()
        text, steps = self.service.decrypt_text(self.ciphertext_edit.toPlainText(), key_pair)
        self.decrypted_edit.setPlainText(text)
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def clear_form(self) -> None:
        self.p_edit.clear()
        self.q_edit.clear()
        self.e_edit.clear()
        self.plaintext_edit.clear()
        self.ciphertext_edit.clear()
        self.decrypted_edit.clear()
        self.key_table.set_mapping(
            {"p": "-", "q": "-", "n": "-", "phi(n)": "-", "e": "-", "d": "-"}
        )
        self.steps_output.clear()
        self.current_key_pair = None
        self.set_steps("")

    def load_example(self) -> None:
        values = self.service.example_values()
        self.p_edit.setText(values["p"])
        self.q_edit.setText(values["q"])
        self.e_edit.setText(values["e"])
        self.plaintext_edit.setPlainText(values["text"])
        self.generate_keys()

    def show_steps(self) -> None:
        self.show_steps_dialog("Шаги RSA")

    def _update_key_table(self, key_pair: RSAKeyPair) -> None:
        self.key_table.set_mapping(
            {
                "p": key_pair.p,
                "q": key_pair.q,
                "n": key_pair.n,
                "phi(n)": key_pair.phi,
                "e": key_pair.e,
                "d": key_pair.d,
            }
        )

    def _require_key_pair(self) -> RSAKeyPair:
        if self.current_key_pair is None:
            raise InputValidationError("Сначала сгенерируйте ключи RSA.")
        return self.current_key_pair
