from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QWidget, QGridLayout, QLineEdit, QFileDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from app.core.models import MouseButton, ButtonMapping, ActionCategory
from app.core.action_executor import SHORTCUT_PRESETS, MEDIA_PRESETS
from typing import Optional, List

class KeyRecorderWidget(QLineEdit):
    """Line edit that intercepts keys and records them as combination strings."""
    keys_recorded = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Nhấp vào đây và nhấn tổ hợp phím (VD: Ctrl + Alt + K)...")
        self.recorded_keys: List[str] = []

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()

        keys = []
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            keys.append("ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            keys.append("alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            keys.append("shift")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            keys.append("win")

        # Map special keys
        key_name = None
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            key_name = f"f{key - Qt.Key.Key_F1 + 1}"
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            key_name = "enter"
        elif key == Qt.Key.Key_Escape:
            key_name = "esc"
        elif key == Qt.Key.Key_Space:
            key_name = "space"
        elif key == Qt.Key.Key_Tab:
            key_name = "tab"
        elif key == Qt.Key.Key_Backspace:
            key_name = "backspace"
        elif key == Qt.Key.Key_Delete:
            key_name = "delete"
        elif Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            key_name = chr(key).lower()
        elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            key_name = chr(key)

        if key_name and key_name not in keys:
            keys.append(key_name)

        if keys:
            self.recorded_keys = keys
            display = " + ".join([k.upper() for k in keys])
            self.setText(display)
            self.keys_recorded.emit(keys)

class ActionConfigDialog(QDialog):
    """
    Dialog to customize the action of a mouse button.
    """

    def __init__(self, button: MouseButton, current_mapping: Optional[ButtonMapping] = None, parent=None):
        super().__init__(parent)
        self.button = button
        self.current_mapping = current_mapping or ButtonMapping(button=button)
        self.result_mapping = self.current_mapping

        self.setWindowTitle(f"Cấu Hình Nút: {button.display_name}")
        self.resize(560, 480)
        self.setStyleSheet("background-color: #1e1e24;")

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Title & Subtitle
        header_layout = QVBoxLayout()
        title = QLabel(f"Thiết Lập Chức Năng: {self.button.display_name}")
        title.setProperty("class", "TitleLabel")
        header_layout.addWidget(title)

        curr_label = QLabel(f"Chức năng hiện tại: <b style='color:#0071e3'>{self.current_mapping.label}</b>")
        curr_label.setStyleSheet("color: #a1a1aa; font-size: 13px;")
        header_layout.addWidget(curr_label)
        main_layout.addLayout(header_layout)

        # Warning banner if Left Click
        if self.button == MouseButton.LEFT:
            warn_frame = QFrame()
            warn_frame.setStyleSheet("background-color: #3b1812; border: 1px solid #da3633; border-radius: 8px; padding: 10px;")
            warn_layout = QHBoxLayout(warn_frame)
            warn_layout.setContentsMargins(10, 6, 10, 6)
            warn_text = QLabel("⚠️ CẢNH BÁO: Bạn đang thay đổi Chuột Trái! Hãy cẩn thận để không bị mất chức năng click cơ bản.")
            warn_text.setStyleSheet("color: #ff7b72; font-weight: bold;")
            warn_layout.addWidget(warn_text)
            main_layout.addWidget(warn_frame)

        # Tab widget for categories
        self.tabs = QTabWidget()

        # 1. Tab Keyboard Shortcuts
        tab_kb = QWidget()
        kb_layout = QVBoxLayout(tab_kb)
        kb_layout.addWidget(QLabel("Chọn phím tắt thông dụng:"))

        grid = QGridLayout()
        grid.setSpacing(8)
        row, col = 0, 0
        for action_key, (keys, name) in SHORTCUT_PRESETS.items():
            btn = QPushButton(name)
            btn.setStyleSheet("text-align: left; padding: 8px 12px;")
            btn.clicked.connect(lambda ch=False, ak=action_key, n=name, k=keys: self._select_shortcut(ak, n, k))
            grid.addWidget(btn, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
        kb_layout.addLayout(grid)

        kb_layout.addWidget(QLabel("Hoặc tự ghi tổ hợp phím tùy ý:"))
        self.key_recorder = KeyRecorderWidget()
        kb_layout.addWidget(self.key_recorder)
        btn_apply_custom_key = QPushButton("Áp Dụng Phím Tự Ghi")
        btn_apply_custom_key.setProperty("class", "PrimaryButton")
        btn_apply_custom_key.clicked.connect(self._select_custom_recorded_key)
        kb_layout.addWidget(btn_apply_custom_key)
        self.tabs.addTab(tab_kb, "⌨️ Bàn Phím")

        # 2. Tab Mouse Actions
        tab_mouse = QWidget()
        mouse_layout = QVBoxLayout(tab_mouse)
        mouse_actions = [
            ("double_click", "Nhấp Đúp Chuột Trái (Double Click)"),
            ("middle_click", "Nhấp Nút Cuộn Giữa (Middle Click)"),
            ("right_click", "Nhấp Chuột Phải (Right Click)"),
            ("left_click", "Nhấp Chuột Trái (Left Click)"),
            ("xbutton1", "Nút Hông 1 (Browser Back)"),
            ("xbutton2", "Nút Hông 2 (Browser Forward)"),
        ]
        for act, label in mouse_actions:
            btn = QPushButton(label)
            btn.setStyleSheet("text-align: left; padding: 10px 14px;")
            btn.clicked.connect(lambda ch=False, a=act, l=label: self._select_mouse_action(a, l))
            mouse_layout.addWidget(btn)
        mouse_layout.addStretch()
        self.tabs.addTab(tab_mouse, "🖱️ Chuột")

        # 3. Tab Media Controls
        tab_media = QWidget()
        media_layout = QVBoxLayout(tab_media)
        for act, (_, label) in MEDIA_PRESETS.items():
            btn = QPushButton(label)
            btn.setStyleSheet("text-align: left; padding: 10px 14px;")
            btn.clicked.connect(lambda ch=False, a=act, l=label: self._select_media_action(a, l))
            media_layout.addWidget(btn)
        media_layout.addStretch()
        self.tabs.addTab(tab_media, "🎵 Âm Lượng & Media")

        # 4. Tab App Launcher
        tab_app = QWidget()
        app_layout = QVBoxLayout(tab_app)
        app_layout.addWidget(QLabel("Nhập đường dẫn ứng dụng (.exe) hoặc liên kết Web:"))
        self.app_input = QLineEdit()
        self.app_input.setPlaceholderText("VD: calc.exe hoặc https://youtube.com hoặc C:\\App.exe")
        app_layout.addWidget(self.app_input)
        
        btn_browse = QPushButton("📁 Chọn File Trên Máy...")
        btn_browse.clicked.connect(self._browse_app)
        app_layout.addWidget(btn_browse)

        btn_apply_app = QPushButton("Áp Dụng Mở Ứng Dụng")
        btn_apply_app.setProperty("class", "PrimaryButton")
        btn_apply_app.clicked.connect(self._select_app_action)
        app_layout.addWidget(btn_apply_app)
        app_layout.addStretch()
        self.tabs.addTab(tab_app, "🚀 Mở Ứng Dụng")

        # 5. Tab Text Snippet
        tab_text = QWidget()
        text_layout = QVBoxLayout(tab_text)
        text_layout.addWidget(QLabel("Nhập văn bản cần tự động gõ khi nhấn nút chuột:"))
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("VD: your_email@example.com hoặc chữ ký...")
        text_layout.addWidget(self.text_input)
        btn_apply_text = QPushButton("Áp Dụng Tự Động Gõ")
        btn_apply_text.setProperty("class", "PrimaryButton")
        btn_apply_text.clicked.connect(self._select_text_action)
        text_layout.addWidget(btn_apply_text)
        text_layout.addStretch()
        self.tabs.addTab(tab_text, "📝 Gõ Văn Bản")

        # 6. Tab Options (Reset / Disable)
        tab_opt = QWidget()
        opt_layout = QVBoxLayout(tab_opt)
        btn_default = QPushButton("🔄 Trả Về Mặc Định Của Windows")
        btn_default.clicked.connect(self._select_default_action)
        opt_layout.addWidget(btn_default)

        btn_disable = QPushButton("🚫 Vô Hiệu Hóa Nút Này (Không làm gì)")
        btn_disable.setProperty("class", "DangerButton")
        btn_disable.clicked.connect(self._select_disable_action)
        opt_layout.addWidget(btn_disable)
        opt_layout.addStretch()
        self.tabs.addTab(tab_opt, "⚙️ Khác")

        main_layout.addWidget(self.tabs)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        btn_cancel = QPushButton("Hủy Bỏ")
        btn_cancel.clicked.connect(self.reject)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_cancel)
        main_layout.addLayout(bottom_layout)

    def _select_shortcut(self, action_key: str, label: str, keys: List[str]):
        self.result_mapping = ButtonMapping(
            button=self.button,
            category=ActionCategory.KEYBOARD,
            action_type=action_key,
            label=label,
            params={"keys": keys},
        )
        self.accept()

    def _select_custom_recorded_key(self):
        keys = self.key_recorder.recorded_keys
        if not keys:
            QMessageBox.warning(self, "Thông báo", "Vui lòng nhấn tổ hợp phím trước!")
            return
        display = " + ".join([k.upper() for k in keys])
        self.result_mapping = ButtonMapping(
            button=self.button,
            category=ActionCategory.KEYBOARD,
            action_type="custom_combo",
            label=f"Phím tắt: {display}",
            params={"keys": keys},
        )
        self.accept()

    def _select_mouse_action(self, action_type: str, label: str):
        self.result_mapping = ButtonMapping(
            button=self.button,
            category=ActionCategory.MOUSE,
            action_type=action_type,
            label=label,
        )
        self.accept()

    def _select_media_action(self, action_type: str, label: str):
        self.result_mapping = ButtonMapping(
            button=self.button,
            category=ActionCategory.MEDIA,
            action_type=action_type,
            label=label,
        )
        self.accept()

    def _browse_app(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn Ứng Dụng", "", "Tất cả tập tin (*.*);;Ứng dụng (*.exe)")
        if path:
            self.app_input.setText(path)

    def _select_app_action(self):
        target = self.app_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Thông báo", "Vui lòng nhập đường dẫn hoặc link web!")
            return
        name = target.split("\\")[-1] if "\\" in target else target
        self.result_mapping = ButtonMapping(
            button=self.button,
            category=ActionCategory.CUSTOM_APP,
            action_type="launch_app",
            label=f"Mở: {name}",
            params={"target": target},
        )
        self.accept()

    def _select_text_action(self):
        text = self.text_input.text().strip()
        if not text:
            QMessageBox.warning(self, "Thông báo", "Vui lòng nhập nội dung văn bản!")
            return
        self.result_mapping = ButtonMapping(
            button=self.button,
            category=ActionCategory.TEXT_SNIPPET,
            action_type="type_text",
            label=f"Gõ: '{text[:15]}...'",
            params={"text": text},
        )
        self.accept()

    def _select_default_action(self):
        self.result_mapping = ButtonMapping(
            button=self.button,
            category=ActionCategory.DEFAULT,
            action_type="default",
            label="Mặc định Windows",
        )
        self.accept()

    def _select_disable_action(self):
        self.result_mapping = ButtonMapping(
            button=self.button,
            category=ActionCategory.DISABLED,
            action_type="disabled",
            label="Vô hiệu hóa (Tắt)",
        )
        self.accept()
