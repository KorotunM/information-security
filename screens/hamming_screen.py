"""Экран кода Хэмминга [7,4]."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from screens.base_screen import ScrollScreen
from services.hamming_service import HammingService
from ui.components import (
    KeyValueTable,
    create_action_button,
    create_multiline_output,
    create_section,
)
from utils.validation import InputValidationError, validate_binary_string


class HammingScreen(ScrollScreen):
    """Экран кода Хэмминга [7,4]."""

    def __init__(
        self,
        service: HammingService,
        on_back: Callable[[], None],
        logger: logging.Logger,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="Передача данных и код Хэмминга [7,4]",
            subtitle="",
            logger=logger,
            parent=parent,
        )
        self.service = service
        self.on_back = on_back
        self._build_ui()

    def _build_ui(self) -> None:
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        input_panel = create_section("Параметры передачи")
        form = QFormLayout(input_panel)
        form.setSpacing(10)

        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("Например: 10110011")

        self.block_spin = QSpinBox()
        self.block_spin.setRange(1, 1)
        self.position_spin = QSpinBox()
        self.position_spin.setRange(1, 7)
        self.position_spin.setValue(3)

        self.encoded_edit = create_multiline_output(read_only=True)
        self.corrupted_edit = create_multiline_output(read_only=True)
        self.syndrome_edit = QLineEdit()
        self.syndrome_edit.setReadOnly(True)
        self.corrected_edit = create_multiline_output(read_only=True)
        self.decoded_edit = create_multiline_output(read_only=True)

        form.addRow("Информационное сообщение:", self.message_edit)
        form.addRow("Номер блока:", self.block_spin)
        form.addRow("Позиция ошибки (1..7):", self.position_spin)
        form.addRow("Кодовое слово:", self.encoded_edit)
        form.addRow("Искажённое слово:", self.corrupted_edit)
        form.addRow("Синдром:", self.syndrome_edit)
        form.addRow("Исправленное слово:", self.corrected_edit)
        form.addRow("Декодированное сообщение:", self.decoded_edit)

        output_panel = create_section("Таблица битов и проверок")
        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(14, 14, 14, 14)
        output_layout.setSpacing(10)

        self.summary_table = KeyValueTable()
        self.summary_table.set_mapping(
            {"Код": "[7,4]", "Проверочных битов": "3", "Исправляет ошибок": "1", "d_min": "3"}
        )
        self.visual_table = QTableWidget(5, 7)
        self.visual_table.setVerticalHeaderLabels(
            ["Позиции", "Биты", "Проверка p1", "Проверка p2", "Проверка p4"]
        )
        self.visual_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.visual_table.setSelectionMode(QTableWidget.NoSelection)
        self.visual_table.horizontalHeader().setStretchLastSection(True)
        output_layout.addWidget(self.summary_table)
        output_layout.addWidget(self.visual_table)

        self.steps_output = create_multiline_output(read_only=True)
        steps_section = create_section("Пошаговые вычисления", self.steps_output)

        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        buttons = [
            ("Построить код", self.build_code),
            ("Закодировать", self.encode_message),
            ("Внести ошибку", self.introduce_error),
            ("Вычислить синдром", self.compute_syndrome),
            ("Исправить", self.correct_payload),
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

    def build_code(self) -> None:
        bits = validate_binary_string(self.message_edit.text(), "Информационное сообщение")
        first_block = (bits + "0000")[:4]
        codeword = self.service.encode_block(first_block)
        parity_count = self.service.parity_count_for_data(4)
        steps = "\n".join(
            [
                "Построение Hamming [7,4]:",
                f"Для 4 информационных бит требуется r = {parity_count}, так как 2^r >= m + r + 1.",
                "Проверочные биты занимают позиции 1, 2 и 4.",
                f"Первый демонстрационный блок: {first_block} -> {codeword}",
            ]
        )
        self._update_visual_table(codeword)
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def encode_message(self) -> None:
        result = self.service.encode_message(self.message_edit.text())
        self.encoded_edit.setPlainText(result.encoded)
        self.corrupted_edit.clear()
        self.corrected_edit.clear()
        self.decoded_edit.clear()
        self.syndrome_edit.clear()
        self.block_spin.setRange(1, len(result.codewords))
        self._update_visual_table(result.codewords[0])
        self.steps_output.setPlainText(result.steps)
        self.set_steps(result.steps)

    def introduce_error(self) -> None:
        payload = self._active_payload(prefer_corrupted=False)
        corrupted, steps = self.service.introduce_error(
            payload,
            block_index=self.block_spin.value(),
            position=self.position_spin.value(),
        )
        self.corrupted_edit.setPlainText(corrupted)
        _, words = self.service.parse_payload(corrupted)
        self._update_visual_table(words[self.block_spin.value() - 1])
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def compute_syndrome(self) -> None:
        payload = self._active_payload()
        _, words = self.service.parse_payload(payload)
        word = words[self.block_spin.value() - 1]
        syndrome, position = self.service.analyze_word(word)
        self.syndrome_edit.setText(f"{syndrome} (позиция {position})")
        steps = "\n".join(
            [
                "Вычисление синдрома:",
                f"Выбранный блок: {word}",
                f"Синдром = {syndrome}",
                f"Позиция ошибки = {position if position else 'ошибки нет'}",
            ]
        )
        self._update_visual_table(word)
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def correct_payload(self) -> None:
        payload = self._active_payload()
        corrected, steps = self.service.decode_payload(payload)
        decoded_bits = self.service.decode_to_information_bits(corrected)
        self.corrected_edit.setPlainText(corrected)
        self.decoded_edit.setPlainText(decoded_bits)
        _, words = self.service.parse_payload(corrected)
        self._update_visual_table(words[self.block_spin.value() - 1])
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def clear_form(self) -> None:
        self.message_edit.clear()
        self.encoded_edit.clear()
        self.corrupted_edit.clear()
        self.syndrome_edit.clear()
        self.corrected_edit.clear()
        self.decoded_edit.clear()
        self.block_spin.setRange(1, 1)
        self.position_spin.setValue(3)
        self.visual_table.clearContents()
        self.steps_output.clear()
        self.set_steps("")

    def load_example(self) -> None:
        self.message_edit.setText(self.service.example_bits())
        self.encode_message()

    def show_steps(self) -> None:
        self.show_steps_dialog("Шаги Hamming [7,4]")

    def _active_payload(self, prefer_corrupted: bool = True) -> str:
        if prefer_corrupted and self.corrupted_edit.toPlainText().strip():
            return self.corrupted_edit.toPlainText()
        if self.encoded_edit.toPlainText().strip():
            return self.encoded_edit.toPlainText()
        if self.corrupted_edit.toPlainText().strip():
            return self.corrupted_edit.toPlainText()
        raise InputValidationError("Сначала постройте и закодируйте сообщение.")

    def _update_visual_table(self, word: str) -> None:
        positions = [str(index) for index in range(1, 8)]
        p1_mask = ["✓" if index in (1, 3, 5, 7) else "" for index in range(1, 8)]
        p2_mask = ["✓" if index in (2, 3, 6, 7) else "" for index in range(1, 8)]
        p4_mask = ["✓" if index in (4, 5, 6, 7) else "" for index in range(1, 8)]
        rows = [positions, list(word), p1_mask, p2_mask, p4_mask]
        for row_index, row_values in enumerate(rows):
            for column_index, value in enumerate(row_values):
                self.visual_table.setItem(row_index, column_index, QTableWidgetItem(value))
