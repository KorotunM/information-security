"""Экран кода Хэмминга [7,4]."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
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
        self.current_codeword = ""
        self._build_ui()

    def _build_ui(self) -> None:
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        input_panel = create_section("Кодирование и исправление ошибки")
        form = QFormLayout(input_panel)
        form.setSpacing(10)

        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("Введите 4 бита, например: 1011")

        self.encoded_edit = QLineEdit()
        self.encoded_edit.setReadOnly(True)
        self.corrupted_edit = QLineEdit()
        self.corrupted_edit.setPlaceholderText("После построения кода измените один бит вручную")
        self.s1_edit = QLineEdit()
        self.s1_edit.setReadOnly(True)
        self.s2_edit = QLineEdit()
        self.s2_edit.setReadOnly(True)
        self.s3_edit = QLineEdit()
        self.s3_edit.setReadOnly(True)
        self.syndrome_edit = QLineEdit()
        self.syndrome_edit.setReadOnly(True)
        self.corrected_edit = QLineEdit()
        self.corrected_edit.setReadOnly(True)
        self.decoded_edit = QLineEdit()
        self.decoded_edit.setReadOnly(True)

        form.addRow("Информационное сообщение:", self.message_edit)
        form.addRow("Кодовое слово:", self.encoded_edit)
        form.addRow("Искажённое слово:", self.corrupted_edit)
        form.addRow("Синдром s1:", self.s1_edit)
        form.addRow("Синдром s2:", self.s2_edit)
        form.addRow("Синдром s3:", self.s3_edit)
        form.addRow("Синдром (s3s2s1):", self.syndrome_edit)
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
            ("Внести ошибку", self.introduce_error),
            ("Исправить", self.correct_word),
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
        if len(bits) != 4:
            raise InputValidationError("Для Hamming [7,4] нужно ввести ровно 4 информационных бита.")

        codeword = self.service.encode_block(bits)
        self.current_codeword = codeword
        self.encoded_edit.setText(codeword)
        self.corrupted_edit.setText(codeword)
        self.corrected_edit.clear()
        self.decoded_edit.clear()
        self._set_syndrome_fields("000")
        self._update_visual_table(codeword)

        steps = "\n".join(
            [
                "Построение Hamming [7,4]:",
                f"Информационные биты: {bits}",
                "Проверочные биты размещаются в позициях 1, 2 и 4.",
                f"Полученное кодовое слово: {codeword}",
                "Теперь можно изменить один бит в поле «Искажённое слово» и нажать «Внести ошибку».",
            ]
        )
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def introduce_error(self) -> None:
        if not self.current_codeword:
            raise InputValidationError("Сначала постройте кодовое слово.")

        corrupted = validate_binary_string(self.corrupted_edit.text(), "Искажённое слово")
        if len(corrupted) != 7:
            raise InputValidationError("Искажённое слово должно состоять ровно из 7 бит.")

        syndrome, position = self.service.analyze_word(corrupted)
        self._set_syndrome_fields(syndrome)
        self._update_visual_table(corrupted)

        steps = "\n".join(
            [
                "Анализ искажённого слова:",
                f"Исходное кодовое слово: {self.current_codeword}",
                f"Искажённое слово: {corrupted}",
                f"s1 = {syndrome[2]}",
                f"s2 = {syndrome[1]}",
                f"s3 = {syndrome[0]}",
                f"Синдром (s3s2s1) = {syndrome}",
                f"Позиция ошибки: {position if position else 'ошибки нет'}",
            ]
        )
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def correct_word(self) -> None:
        corrupted = validate_binary_string(self.corrupted_edit.text(), "Искажённое слово")
        if len(corrupted) != 7:
            raise InputValidationError("Искажённое слово должно состоять ровно из 7 бит.")

        result = self.service.correct_word(corrupted)
        self.corrected_edit.setText(result.corrected_word)
        self.decoded_edit.setText(result.decoded_bits)
        self._set_syndrome_fields(result.syndrome)
        self._update_visual_table(result.corrected_word)

        steps = "\n".join(
            [
                "Исправление по синдрому:",
                f"Принятое слово: {result.received_word}",
                f"s1 = {result.syndrome[2]}",
                f"s2 = {result.syndrome[1]}",
                f"s3 = {result.syndrome[0]}",
                f"Синдром (s3s2s1) = {result.syndrome}",
                f"Позиция ошибки: {result.error_position if result.error_position else 'ошибки нет'}",
                f"Исправленное слово: {result.corrected_word}",
                f"Декодированное сообщение: {result.decoded_bits}",
            ]
        )
        self.steps_output.setPlainText(steps)
        self.set_steps(steps)

    def clear_form(self) -> None:
        self.message_edit.clear()
        self.encoded_edit.clear()
        self.corrupted_edit.clear()
        self.s1_edit.clear()
        self.s2_edit.clear()
        self.s3_edit.clear()
        self.syndrome_edit.clear()
        self.corrected_edit.clear()
        self.decoded_edit.clear()
        self.visual_table.clearContents()
        self.steps_output.clear()
        self.current_codeword = ""
        self.set_steps("")

    def load_example(self) -> None:
        self.message_edit.setText("1011")
        self.build_code()
        self.corrupted_edit.setText("0100011")
        self.introduce_error()

    def show_steps(self) -> None:
        self.show_steps_dialog("Шаги Hamming [7,4]")

    def _set_syndrome_fields(self, syndrome: str) -> None:
        self.s1_edit.setText(syndrome[2])
        self.s2_edit.setText(syndrome[1])
        self.s3_edit.setText(syndrome[0])
        self.syndrome_edit.setText(syndrome)

    def _update_visual_table(self, word: str) -> None:
        positions = [str(index) for index in range(1, 8)]
        p1_mask = ["✓" if index in (1, 3, 5, 7) else "" for index in range(1, 8)]
        p2_mask = ["✓" if index in (2, 3, 6, 7) else "" for index in range(1, 8)]
        p4_mask = ["✓" if index in (4, 5, 6, 7) else "" for index in range(1, 8)]
        rows = [positions, list(word), p1_mask, p2_mask, p4_mask]
        for row_index, row_values in enumerate(rows):
            for column_index, value in enumerate(row_values):
                self.visual_table.setItem(row_index, column_index, QTableWidgetItem(value))
