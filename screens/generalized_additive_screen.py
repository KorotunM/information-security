"""Экран обобщённого аддитивного рюкзака."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from models.crypto_models import AdditiveKnapsackKeyPair
from screens.base_screen import ScrollScreen
from services.generalized_additive_knapsack_service import GeneralizedAdditiveKnapsackService
from ui.components import (
    KeyValueTable,
    SequenceTable,
    create_action_button,
    create_multiline_output,
    create_section,
)
from utils.text_codec import FIXED_INPUT_ALPHABET
from utils.validation import InputValidationError, parse_int, parse_int_sequence


class GeneralizedAdditiveScreen(ScrollScreen):
    """Экран GAKP/GAKR."""

    def __init__(
        self,
        service: GeneralizedAdditiveKnapsackService,
        on_back: Callable[[], None],
        logger: logging.Logger,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="Обобщённый аддитивный рюкзак (GAKP / GAKR)",
            subtitle="",
            logger=logger,
            parent=parent,
        )
        self.service = service
        self.on_back = on_back
        self.current_key_pair: AdditiveKnapsackKeyPair | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        input_panel = create_section("Параметры и сообщение")
        form = QFormLayout(input_panel)
        form.setSpacing(10)

        self.length_spin = QSpinBox()
        self.length_spin.setRange(4, 32)
        self.length_spin.setValue(4)
        self.base_spin = QSpinBox()
        self.base_spin.setRange(2, 10)
        self.base_spin.setValue(3)

        self.alphabet_edit = QLineEdit(FIXED_INPUT_ALPHABET)
        self.alphabet_edit.setReadOnly(True)

        self.private_edit = QLineEdit()
        self.private_edit.setPlaceholderText("Можно оставить пустым для автогенерации")
        self.modulus_edit = QLineEdit()
        self.modulus_edit.setPlaceholderText("Если пусто, подберётся автоматически")
        self.multiplier_edit = QLineEdit()
        self.multiplier_edit.setPlaceholderText("Если пусто, подберётся автоматически")

        self.message_edit = create_multiline_output(read_only=False)
        self.message_edit.setPlaceholderText("Только строчные английские буквы и пробел")
        self.ciphertext_edit = create_multiline_output(read_only=False)
        self.decrypted_edit = create_multiline_output(read_only=True)
        self.numeric_view = create_multiline_output(read_only=True)

        form.addRow("Длина рюкзака n:", self.length_spin)
        form.addRow("Параметр p:", self.base_spin)
        form.addRow("Алфавит:", self.alphabet_edit)
        form.addRow("Закрытый рюкзак:", self.private_edit)
        form.addRow("Модуль m:", self.modulus_edit)
        form.addRow("Множитель a:", self.multiplier_edit)
        form.addRow("Сообщение:", self.message_edit)
        form.addRow("Шифртекст:", self.ciphertext_edit)
        form.addRow("Расшифрованный текст:", self.decrypted_edit)
        form.addRow("Числовые эквиваленты:", self.numeric_view)

        output_panel = create_section("Ключи и пространства")
        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(14, 14, 14, 14)
        output_layout.setSpacing(10)

        self.summary_table = KeyValueTable()
        self.summary_table.set_mapping(
            {"p": "-", "m": "-", "a": "-", "a^(-1) mod m": "-", "Размер блока n": "-"}
        )
        self.private_table = SequenceTable("W")
        self.public_table = SequenceTable("B")
        output_layout.addWidget(self.summary_table)
        output_layout.addWidget(self.private_table)
        output_layout.addWidget(self.public_table)

        self.steps_output = create_multiline_output(read_only=True)
        steps_section = create_section("Шаги вычислений", self.steps_output)

        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        buttons = [
            ("Сгенерировать ключи", self.generate_keys),
            ("Зашифровать", self.encrypt_message),
            ("Расшифровать", self.decrypt_message),
            ("Очистить", self.clear_form),
            ("Показать шаги", self.show_steps),
            ("Пример", self.load_example),
            ("Назад на главную", self.on_back),
        ]
        for label, handler in buttons:
            button = create_action_button(label)
            button.clicked.connect(lambda _=False, callback=handler: self.run_action(callback))
            actions_layout.addWidget(button)

        grid.addWidget(input_panel, 0, 0)
        grid.addWidget(output_panel, 0, 1)
        grid.addWidget(actions, 1, 0, 1, 2)
        grid.addWidget(steps_section, 2, 0, 1, 2)

        wrapper = QWidget()
        wrapper.setLayout(grid)
        self.content_layout.addWidget(wrapper)

    def generate_keys(self) -> None:
        base = self.base_spin.value()
        private_text = self.private_edit.text().strip()
        private_sequence = (
            parse_int_sequence(private_text, "Закрытый рюкзак", minimum_len=2, item_minimum=1)
            if private_text
            else None
        )
        length = len(private_sequence) if private_sequence else self.length_spin.value()
        modulus = parse_int(self.modulus_edit.text(), "Модуль m", minimum=2) if self.modulus_edit.text().strip() else None
        multiplier = parse_int(self.multiplier_edit.text(), "Множитель a", minimum=2) if self.multiplier_edit.text().strip() else None

        self.current_key_pair, steps = self.service.generate_keys(
            length=length,
            base=base,
            private_sequence=private_sequence,
            modulus=modulus,
            multiplier=multiplier,
        )
        self.length_spin.setValue(len(self.current_key_pair.private_sequence))
        self.private_edit.setText(", ".join(map(str, self.current_key_pair.private_sequence)))
        self.modulus_edit.setText(str(self.current_key_pair.modulus))
        self.multiplier_edit.setText(str(self.current_key_pair.multiplier))
        self._update_key_views(self.current_key_pair)
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def encrypt_message(self) -> None:
        key_pair = self._require_key_pair()
        alphabet = self.alphabet_edit.text()
        encoded, steps, _payload = self.service.encrypt_text(
            self.message_edit.toPlainText(),
            key_pair,
            alphabet=alphabet,
            base=self.base_spin.value(),
        )
        self.ciphertext_edit.setPlainText(encoded)
        self.numeric_view.setPlainText(
            "Кодирование: a→0, b→1, ..., z→25, пробел→26; затем каждый символ переводится "
            "в p-ичный блок длины n."
        )
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def decrypt_message(self) -> None:
        key_pair = self._require_key_pair()
        text, steps = self.service.decrypt_text(
            self.ciphertext_edit.toPlainText(),
            key_pair,
            alphabet=self.alphabet_edit.text(),
            base=self.base_spin.value(),
        )
        self.decrypted_edit.setPlainText(text)
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def clear_form(self) -> None:
        self.length_spin.setValue(4)
        self.base_spin.setValue(3)
        self.alphabet_edit.setText(FIXED_INPUT_ALPHABET)
        self.private_edit.clear()
        self.modulus_edit.clear()
        self.multiplier_edit.clear()
        self.message_edit.clear()
        self.ciphertext_edit.clear()
        self.decrypted_edit.clear()
        self.numeric_view.clear()
        self.summary_table.set_mapping(
            {"p": "-", "m": "-", "a": "-", "a^(-1) mod m": "-", "Размер блока n": "-"}
        )
        self.private_table.set_sequence([])
        self.public_table.set_sequence([])
        self.steps_output.clear()
        self.current_key_pair = None
        self.set_steps("")

    def load_example(self) -> None:
        values = self.service.example_values()
        self.length_spin.setValue(int(values["length"]))
        self.base_spin.setValue(int(values["base"]))
        self.private_edit.setText(values["private_sequence"])
        self.modulus_edit.setText(values["modulus"])
        self.multiplier_edit.setText(values["multiplier"])
        self.message_edit.setPlainText(values["message"])
        self.generate_keys()

    def show_steps(self) -> None:
        self.show_steps_dialog("Шаги GAKP")

    def _update_key_views(self, key_pair: AdditiveKnapsackKeyPair) -> None:
        self.summary_table.set_mapping(
            {
                "p": self.base_spin.value(),
                "m": key_pair.modulus,
                "a": key_pair.multiplier,
                "a^(-1) mod m": key_pair.inverse_multiplier,
                "Размер блока n": len(key_pair.public_sequence),
            }
        )
        self.private_table.set_sequence(key_pair.private_sequence)
        self.public_table.set_sequence(key_pair.public_sequence)

    def _require_key_pair(self) -> AdditiveKnapsackKeyPair:
        if self.current_key_pair is None:
            raise InputValidationError("Сначала сгенерируйте ключи GAKP.")
        return self.current_key_pair
