"""Переиспользуемые виджеты интерфейса."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def create_title_label(text: str) -> QLabel:
    """Создаёт заголовок страницы."""

    label = QLabel(text)
    font = QFont("Bahnschrift", 20)
    font.setBold(True)
    label.setFont(font)
    label.setWordWrap(True)
    return label


def create_subtitle_label(text: str) -> QLabel:
    """Создаёт поясняющий текст под заголовком."""

    label = QLabel(text)
    label.setWordWrap(True)
    label.setObjectName("MutedLabel")
    return label


def create_section(title: str, widget: QWidget | None = None) -> QGroupBox:
    """Создаёт стандартную секцию интерфейса."""

    box = QGroupBox(title)
    if widget is not None:
        layout = QVBoxLayout(box)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(widget)
    return box


def create_info_card(title: str, text: str) -> QFrame:
    """Создаёт компактную информационную карточку."""

    card = QFrame()
    card.setObjectName("InfoCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(8)

    heading = QLabel(title)
    heading.setObjectName("SectionTitle")
    body = QLabel(text)
    body.setWordWrap(True)
    body.setTextInteractionFlags(Qt.TextSelectableByMouse)

    layout.addWidget(heading)
    layout.addWidget(body)
    return card


def create_multiline_output(read_only: bool = True) -> QTextEdit:
    """Создаёт текстовое поле для многострочного ввода/вывода."""

    edit = QTextEdit()
    edit.setReadOnly(read_only)
    edit.setMinimumHeight(110)
    edit.setAcceptRichText(False)
    edit.setObjectName("MonospaceEdit" if read_only else "TextInput")
    return edit


class KeyValueTable(QTableWidget):
    """Таблица вида «параметр - значение»."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(["Параметр", "Значение"])
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setAlternatingRowColors(False)
        self.setFocusPolicy(Qt.NoFocus)

    def set_mapping(self, mapping: dict[str, str | int]) -> None:
        """Заполняет таблицу значениями."""

        self.setRowCount(len(mapping))
        for row, (key, value) in enumerate(mapping.items()):
            self.setItem(row, 0, QTableWidgetItem(str(key)))
            self.setItem(row, 1, QTableWidgetItem(str(value)))


class SequenceTable(QTableWidget):
    """Таблица одной последовательности."""

    def __init__(self, title_prefix: str, parent: QWidget | None = None) -> None:
        super().__init__(1, 0, parent)
        self.title_prefix = title_prefix
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setAlternatingRowColors(False)
        self.setFocusPolicy(Qt.NoFocus)

    def set_sequence(self, values: list[int]) -> None:
        """Заполняет таблицу последовательностью."""

        self.setColumnCount(len(values))
        self.setHorizontalHeaderLabels(
            [f"{self.title_prefix}{index + 1}" for index in range(len(values))]
        )
        for column, value in enumerate(values):
            self.setItem(0, column, QTableWidgetItem(str(value)))


class StepsDialog(QDialog):
    """Окно для просмотра пошаговых вычислений."""

    def __init__(self, title: str, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(840, 620)
        layout = QVBoxLayout(self)

        viewer = create_multiline_output(read_only=True)
        viewer.setPlainText(text or "Шаги ещё не сформированы.")
        layout.addWidget(viewer)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


def create_action_button(text: str) -> QPushButton:
    """Создаёт кнопку действия с общим стилем."""

    button = QPushButton(text)
    button.setMinimumHeight(38)
    return button


def build_info_grid(cards: list[QWidget]) -> QWidget:
    """Укладывает карточки теории в сетку."""

    wrapper = QWidget()
    layout = QGridLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(12)
    layout.setVerticalSpacing(12)
    for index, card in enumerate(cards):
        row = index // 2
        column = index % 2
        layout.addWidget(card, row, column)
    return wrapper


def show_error(parent: QWidget, message: str) -> None:
    """Показывает сообщение об ошибке."""

    QMessageBox.critical(parent, "Ошибка", message)


def show_info(parent: QWidget, title: str, message: str) -> None:
    """Показывает информационное сообщение."""

    QMessageBox.information(parent, title, message)
