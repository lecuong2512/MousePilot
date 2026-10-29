from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QCheckBox, QSlider, QMessageBox
)
from PySide6.QtCore import Qt
from app.core.config_manager import ConfigManager
from app.core.win32_input import get_mouse_speed, set_mouse_speed
import winreg
import sys
import os

REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "MousePilot"

def set_windows_autostart(enable: bool) -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                exe_path = sys.executable
                script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "main.py"))
                cmd = f'"{exe_path}" "{script_path}" --tray'
                winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_REG_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"[Settings] Lỗi cài đặt autostart: {e}")
        return False

class SettingsView(QWidget):
    """General settings view: Autostart, tray options, panic key, and mouse sensitivity."""

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header
        lbl_title = QLabel("Cài Đặt Hệ Thống & Tùy Chọn")
        lbl_title.setProperty("class", "TitleLabel")
        main_layout.addWidget(lbl_title)

        lbl_sub = QLabel("Quản lý khởi động hệ thống, khay tác vụ và độ nhạy con trỏ chuột Windows.")
        lbl_sub.setProperty("class", "SubtitleLabel")
        main_layout.addWidget(lbl_sub)

        # Card 1: System settings
        card_sys = QFrame()
        card_sys.setProperty("class", "CardFrame")
        c1_layout = QVBoxLayout(card_sys)
        c1_layout.setSpacing(12)

        lbl_c1_title = QLabel("Tùy Chọn Chạy Nền")
        lbl_c1_title.setProperty("class", "SectionHeader")
        c1_layout.addWidget(lbl_c1_title)

        self.chk_autostart = QCheckBox("Khởi động ứng dụng cùng Windows")
        self.chk_autostart.setChecked(self.config_manager.start_with_windows)
        self.chk_autostart.toggled.connect(self._on_autostart_toggle)
        c1_layout.addWidget(self.chk_autostart)

        self.chk_tray = QCheckBox("Thu nhỏ xuống khay hệ thống (System Tray) khi bấm nút đóng [X]")
        self.chk_tray.setChecked(self.config_manager.minimize_to_tray)
        self.chk_tray.toggled.connect(self._on_tray_toggle)
        c1_layout.addWidget(self.chk_tray)

        self.chk_guard = QCheckBox("Bật chế độ bảo vệ Chuột Trái (Cảnh báo trước khi thay đổi nút trái)")
        self.chk_guard.setChecked(self.config_manager.left_click_guard)
        self.chk_guard.toggled.connect(self._on_guard_toggle)
        c1_layout.addWidget(self.chk_guard)

        main_layout.addWidget(card_sys)

        # Card 2: Sensitivity (Pointer Speed)
        card_speed = QFrame()
        card_speed.setProperty("class", "CardFrame")
        c2_layout = QVBoxLayout(card_speed)
        c2_layout.setSpacing(10)

        lbl_c2_title = QLabel("Tốc Độ Con Trỏ Chuột Hệ Thống (Mouse Speed / Sensitivity)")
        lbl_c2_title.setProperty("class", "SectionHeader")
        c2_layout.addWidget(lbl_c2_title)

        curr_speed = get_mouse_speed()
        self.lbl_speed_val = QLabel(f"Tốc độ hiện tại: {curr_speed} / 20")
        self.lbl_speed_val.setStyleSheet("color: #0071e3; font-weight: bold;")
        c2_layout.addWidget(self.lbl_speed_val)

        slider_box = QHBoxLayout()
        lbl_slow = QLabel("Chậm (1)")
        lbl_slow.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        slider_box.addWidget(lbl_slow)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 20)
        self.slider.setValue(curr_speed)
        self.slider.valueChanged.connect(self._on_speed_changed)
        slider_box.addWidget(self.slider, stretch=1)

        lbl_fast = QLabel("Nhanh (20)")
        lbl_fast.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        slider_box.addWidget(lbl_fast)
        c2_layout.addLayout(slider_box)

        main_layout.addWidget(card_speed)

        # Card 3: Emergency Panic Key Safety Information
        card_panic = QFrame()
        card_panic.setProperty("class", "CardFrame")
        c3_layout = QVBoxLayout(card_panic)
        c3_layout.setSpacing(8)

        lbl_c3_title = QLabel("🛡️ Phím Tắt Khẩn Cấp (Emergency Panic Key)")
        lbl_c3_title.setStyleSheet("color: #ff9f0a; font-weight: bold; font-size: 14px;")
        c3_layout.addWidget(lbl_c3_title)

        lbl_panic_info = QLabel(
            "Nếu bạn vô tình gán nhầm phím làm chuột không thể bấm bình thường, hãy nhấn tổ hợp:\n"
            "<b style='color:#ffffff; font-size:14px; background-color:#382b15; padding:4px 8px; border-radius:4px;'>Ctrl + Shift + Alt + M</b>\n"
            "Tổ hợp phím này sẽ ngay lập tức tạm dừng toàn bộ Hook để trả chuột về trạng thái bình thường."
        )
        lbl_panic_info.setStyleSheet("color: #d1d5db; line-height: 1.5;")
        c3_layout.addWidget(lbl_panic_info)

        main_layout.addWidget(card_panic)
        main_layout.addStretch()

    def _on_autostart_toggle(self, enabled: bool):
        self.config_manager.start_with_windows = enabled
        self.config_manager.save()
        set_windows_autostart(enabled)

    def _on_tray_toggle(self, enabled: bool):
        self.config_manager.minimize_to_tray = enabled
        self.config_manager.save()

    def _on_guard_toggle(self, enabled: bool):
        self.config_manager.left_click_guard = enabled
        self.config_manager.save()

    def _on_speed_changed(self, value: int):
        self.lbl_speed_val.setText(f"Tốc độ hiện tại: {value} / 20")
        set_mouse_speed(value)
