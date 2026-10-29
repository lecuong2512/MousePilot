"""
Apple HIG & Modern Fluent Dark Theme definitions and QSS stylesheet.
"""

DARK_THEME = """
/* Global Application Styling */
QWidget {
    background-color: #18181b;
    color: #f4f4f5;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
    font-size: 13px;
    selection-background-color: #0071e3;
    selection-color: #ffffff;
}

/* Main Window */
QMainWindow {
    background-color: #121215;
}

/* Sidebar Navigation */
QListWidget#SidebarList {
    background-color: #1e1e24;
    border: none;
    border-right: 1px solid #2e2e38;
    outline: none;
    padding: 12px 6px;
}

QListWidget#SidebarList::item {
    height: 42px;
    padding-left: 14px;
    border-radius: 8px;
    color: #a1a1aa;
    font-weight: 500;
    margin-bottom: 4px;
}

QListWidget#SidebarList::item:hover {
    background-color: #272730;
    color: #ffffff;
}

QListWidget#SidebarList::item:selected {
    background-color: #0071e3;
    color: #ffffff;
    font-weight: 600;
}

/* Card Containers */
QFrame.CardFrame {
    background-color: #202028;
    border: 1px solid #32323e;
    border-radius: 12px;
    padding: 16px;
}

QFrame.SubCard {
    background-color: #272732;
    border: 1px solid #3c3c4a;
    border-radius: 10px;
    padding: 12px;
}

/* Typography */
QLabel.TitleLabel {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}

QLabel.SectionHeader {
    font-size: 15px;
    font-weight: 600;
    color: #ffffff;
}

QLabel.SubtitleLabel {
    font-size: 12px;
    color: #a1a1aa;
}

QLabel.BadgeLabel {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
}

/* Buttons */
QPushButton {
    background-color: #2d2d38;
    color: #ffffff;
    border: 1px solid #404050;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
    outline: none;
}

QPushButton:hover {
    background-color: #383846;
    border-color: #55556a;
}

QPushButton:pressed {
    background-color: #22222c;
}

QPushButton:disabled {
    background-color: #1f1f26;
    color: #666675;
    border-color: #2a2a34;
}

QPushButton.PrimaryButton {
    background-color: #0071e3;
    color: #ffffff;
    border: 1px solid #0077ed;
    font-weight: 600;
}

QPushButton.PrimaryButton:hover {
    background-color: #0077ed;
}

QPushButton.PrimaryButton:pressed {
    background-color: #005bb5;
}

QPushButton.SuccessButton {
    background-color: #248a3d;
    color: #ffffff;
    border: 1px solid #2ea043;
    font-weight: 600;
}

QPushButton.DangerButton {
    background-color: #cf222e;
    color: #ffffff;
    border: 1px solid #da3633;
    font-weight: 600;
}

QPushButton.DangerButton:hover {
    background-color: #e53e3e;
}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1c1c24;
    border: 1px solid #363644;
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #0071e3;
    background-color: #22222c;
}

/* Combo Boxes */
QComboBox {
    background-color: #272732;
    border: 1px solid #3c3c4a;
    border-radius: 8px;
    padding: 6px 12px;
    color: #ffffff;
    min-width: 140px;
}

QComboBox:hover {
    border-color: #55556a;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #202028;
    border: 1px solid #3a3a48;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #0071e3;
    color: #ffffff;
}

/* Tables & Lists */
QTableWidget, QTableView {
    background-color: #1e1e26;
    border: 1px solid #30303c;
    border-radius: 10px;
    gridline-color: #2a2a36;
    color: #ffffff;
    selection-background-color: #0071e3;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #272732;
    color: #a1a1aa;
    font-weight: 600;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #363644;
}

/* Scroll Bars */
QScrollBar:vertical {
    background: #18181b;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #3f3f46;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #52525b;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #30303c;
    border-radius: 10px;
    background-color: #202028;
    top: -1px;
}

QTabBar::tab {
    background-color: #1e1e26;
    color: #a1a1aa;
    border: 1px solid #30303c;
    border-bottom: none;
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #202028;
    color: #ffffff;
    font-weight: 600;
    border-color: #3f3f4e;
}

QTabBar::tab:hover {
    color: #ffffff;
    background-color: #282834;
}

/* Checkbox */
QCheckBox {
    spacing: 8px;
    color: #ffffff;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #4a4a5a;
    background-color: #22222c;
}

QCheckBox::indicator:checked {
    background-color: #0071e3;
    border-color: #0071e3;
}
"""
