"""Qt-стили приложения."""

APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #f4f1ea;
    color: #21313c;
    font-family: "Bahnschrift", "Segoe UI";
    font-size: 13px;
}

QLabel#MutedLabel {
    color: #5c6d78;
}

QLabel#SectionTitle {
    font-size: 16px;
    font-weight: 700;
    color: #143547;
}

QGroupBox {
    border: 1px solid #d3d9d6;
    border-radius: 12px;
    margin-top: 10px;
    padding-top: 10px;
    background: #fffdf9;
    font-weight: 700;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QFrame#InfoCard {
    border: 1px solid #d5ddd8;
    border-radius: 14px;
    background: #ffffff;
}

QPushButton {
    background: #1f6f78;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background: #165860;
}

QPushButton:pressed {
    background: #11444a;
}

QPushButton#DashboardCard {
    text-align: center;
    padding: 16px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1d5e69, stop:1 #29818c);
    min-height: 110px;
}

QLineEdit, QSpinBox, QComboBox, QTextEdit, QTableWidget {
    background: #ffffff;
    border: 1px solid #cad4cf;
    border-radius: 8px;
    padding: 6px;
    selection-background-color: #1f6f78;
}

QTableWidget {
    background: #ffffff;
    alternate-background-color: #ffffff;
    selection-background-color: #ffffff;
    selection-color: #21313c;
    gridline-color: #d9e0dc;
}

QTableWidget::item {
    background: #ffffff;
    color: #21313c;
}

QTableWidget::item:selected {
    background: #ffffff;
    color: #21313c;
}

QTextEdit#MonospaceEdit {
    font-family: "Cascadia Mono", "Consolas";
}

QHeaderView::section {
    background: #ffffff;
    color: #1e3644;
    padding: 6px;
    border: none;
    border-right: 1px solid #c6d2cc;
    border-bottom: 1px solid #c6d2cc;
    font-weight: 700;
}

QScrollArea {
    border: none;
    background: transparent;
}
"""
