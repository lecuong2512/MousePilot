from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
    QStackedWidget, QLabel, QPushButton, QComboBox, QSystemTrayIcon,
    QMenu, QMessageBox, QFrame, QApplication, QStyle
)
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtGui import QIcon, QAction, QFont, QCloseEvent
import ctypes
from ctypes import wintypes

from app.core.models import MouseButton, ButtonMapping, ActionCategory
from app.core.config_manager import ConfigManager
from app.core.mouse_hook import MouseHookEngine
from app.core.action_executor import ActionExecutor
from app.ui.views.mapping_view import MappingView
from app.ui.views.devices_view import DevicesView
from app.ui.views.live_monitor import LiveMonitorView
from app.ui.views.profiles_view import ProfilesView
from app.ui.views.settings_view import SettingsView

user32 = ctypes.windll.user32
HOTKEY_PANIC_ID = 9001
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000

class MouseSignalBridge(QObject):
    """Bridges events from Win32 background hook thread to Qt Main GUI Thread."""
    mouse_event_received = Signal(object, bool, int, int)

class MainWindow(QMainWindow):
    """
    Main Application Window for MousePilot.
    """

    def __init__(self, config_manager: ConfigManager, hook_engine: MouseHookEngine):
        super().__init__()
        self.config_manager = config_manager
        self.hook_engine = hook_engine
        self.signal_bridge = MouseSignalBridge()

        self.setWindowTitle("MousePilot — Bộ Điều Khiển & Tùy Biến Nút Chuột Windows")
        self.resize(1020, 680)
        self.setMinimumSize(920, 580)

        # Connect hook bridge
        self.signal_bridge.mouse_event_received.connect(self._handle_mouse_event_on_main_thread)
        self.hook_engine.set_event_listener(self._hook_event_callback)

        self._setup_ui()
        self._setup_tray()
        self._register_global_panic_hotkey()

        # Load initial profile
        active_prof = self.config_manager.get_active_profile()
        self.hook_engine.set_mappings(active_prof.mappings)
        self.mapping_view.load_profile(active_prof)
        self.live_monitor_view.set_mappings(active_prof.mappings)
        self._sync_header_profile_combo()

        self.statusBar().setStyleSheet("color: #a1a1aa; font-size: 12px; background: #16161a; padding: 4px 12px;")
        self.statusBar().showMessage("Sẵn sàng. Can thiệp chuột đang HOẠT ĐỘNG.", 4000)

    def _setup_ui(self):
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # TOP BAR
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #1a1a20; border-bottom: 1px solid #2d2d38;")
        top_bar.setFixedHeight(64)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(18, 0, 18, 0)
        top_layout.setSpacing(14)

        # Logo / Brand
        lbl_logo = QLabel("🖱️ MousePilot")
        lbl_logo.setStyleSheet("font-size: 17px; font-weight: 800; color: #ffffff;")
        top_layout.addWidget(lbl_logo)

        lbl_sub = QLabel("— Tùy biến mọi nút chuột")
        lbl_sub.setStyleSheet("color: #71717a; font-size: 13px;")
        top_layout.addWidget(lbl_sub)

        top_layout.addStretch()

        # Profile Switcher in Header
        lbl_prof = QLabel("Hồ sơ:")
        lbl_prof.setStyleSheet("color: #a1a1aa; font-size: 12px; font-weight: 500;")
        top_layout.addWidget(lbl_prof)

        self.combo_profile = QComboBox()
        self.combo_profile.currentIndexChanged.connect(self._on_header_profile_changed)
        top_layout.addWidget(self.combo_profile)

        # Hook Toggle Status Button
        self.btn_toggle_hook = QPushButton("● CAN THIỆP: ĐANG BẬT")
        self.btn_toggle_hook.setProperty("class", "SuccessButton")
        self.btn_toggle_hook.clicked.connect(self._toggle_hook_state)
        top_layout.addWidget(self.btn_toggle_hook)

        central_layout.addWidget(top_bar)

        # BODY: Sidebar + Stacked Views
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar navigation
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("SidebarList")
        self.sidebar.setFixedWidth(200)

        nav_items = [
            ("🖱️  Gán Phím", "mapping"),
            ("💻  Thiết Bị", "devices"),
            ("⚡  Kiểm Tra Live", "monitor"),
            ("🎯  Hồ Sơ (Profiles)", "profiles"),
            ("⚙️  Cài Đặt", "settings"),
        ]

        for text, key in nav_items:
            self.sidebar.addItem(text)

        self.sidebar.currentRowChanged.connect(self._on_sidebar_row_changed)
        body_layout.addWidget(self.sidebar)

        # Stacked Views
        self.stack = QStackedWidget()

        self.mapping_view = MappingView()
        self.mapping_view.mapping_changed.connect(self._on_mapping_changed)
        self.stack.addWidget(self.mapping_view)

        self.devices_view = DevicesView()
        self.stack.addWidget(self.devices_view)

        self.live_monitor_view = LiveMonitorView()
        self.stack.addWidget(self.live_monitor_view)

        self.profiles_view = ProfilesView(self.config_manager)
        self.profiles_view.profile_activated.connect(self._on_profile_activated)
        self.stack.addWidget(self.profiles_view)

        self.settings_view = SettingsView(self.config_manager)
        self.stack.addWidget(self.settings_view)

        body_layout.addWidget(self.stack, stretch=1)
        central_layout.addWidget(body_widget, stretch=1)

        self.setCentralWidget(central_widget)
        self.sidebar.setCurrentRow(0)

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.windowIcon() if not self.windowIcon().isNull() else QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.tray.setToolTip("MousePilot — Bộ điều khiển chuột")

        tray_menu = QMenu()
        self.action_tray_toggle = QAction("Tạm dừng Can Thiệp", self)
        self.action_tray_toggle.triggered.connect(self._toggle_hook_state)
        tray_menu.addAction(self.action_tray_toggle)

        tray_menu.addSeparator()

        action_open = QAction("Mở Cửa Sổ Chính", self)
        action_open.triggered.connect(self.showNormal)
        tray_menu.addAction(action_open)

        action_quit = QAction("Thoát Hoàn Toàn", self)
        action_quit.triggered.connect(self._quit_application)
        tray_menu.addAction(action_quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def _register_global_panic_hotkey(self):
        """Register global hotkey Ctrl + Shift + Alt + M."""
        try:
            hwnd = int(self.winId())
            res = user32.RegisterHotKey(
                hwnd, HOTKEY_PANIC_ID,
                MOD_CONTROL | MOD_SHIFT | MOD_ALT | MOD_NOREPEAT,
                ord("M")
            )
            if res:
                print("[MousePilot] Emergency panic hotkey registered: Ctrl + Shift + Alt + M")
        except Exception as e:
            print(f"[MousePilot] Register hotkey error: {e}")

    def nativeEvent(self, eventType, message):
        """Catch global panic hotkey message."""
        try:
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0312:  # WM_HOTKEY
                if msg.wParam == HOTKEY_PANIC_ID:
                    self._toggle_hook_state()
                    status = "TẠM DỪNG" if self.hook_engine.is_paused else "HOẠT ĐỘNG"
                    self.tray.showMessage(
                        "MousePilot",
                        f"Phím khẩn cấp đã kích hoạt! Trạng thái can thiệp: {status}",
                        QSystemTrayIcon.MessageIcon.Information, 2000
                    )
                    return True, 0
        except Exception:
            pass
        return super().nativeEvent(eventType, message)

    def _hook_event_callback(self, button: MouseButton, is_down: bool, x: int, y: int):
        """Called from Win32 background thread, route to Qt GUI thread."""
        self.signal_bridge.mouse_event_received.emit(button, is_down, x, y)

    def _handle_mouse_event_on_main_thread(self, button: MouseButton, is_down: bool, x: int, y: int):
        if is_down:
            self.mapping_view.flash_button(button)
            active_prof = self.config_manager.get_active_profile()
            mapping = active_prof.mappings.get(button.value)
            if mapping and mapping.enabled and mapping.category != ActionCategory.DEFAULT:
                self.statusBar().showMessage(f"⚡ Đã bấm {button.short_name} ➔ Thực thi: {mapping.label}", 3000)
        self.live_monitor_view.on_mouse_event(button, is_down, x, y)

    def _on_sidebar_row_changed(self, row: int):
        self.stack.setCurrentIndex(row)
        if row == 1:
            self.devices_view.refresh_devices()

    def _sync_header_profile_combo(self):
        self.combo_profile.blockSignals(True)
        self.combo_profile.clear()
        for pid, p in self.config_manager.profiles.items():
            self.combo_profile.addItem(p.name, pid)
        idx = self.combo_profile.findData(self.config_manager.active_profile_id)
        if idx >= 0:
            self.combo_profile.setCurrentIndex(idx)
        self.combo_profile.blockSignals(False)

    def _on_header_profile_changed(self, index: int):
        pid = self.combo_profile.currentData()
        if pid:
            self._on_profile_activated(pid)

    def _on_profile_activated(self, profile_id: str):
        self.config_manager.set_active_profile(profile_id)
        active_prof = self.config_manager.get_active_profile()
        self.hook_engine.set_mappings(active_prof.mappings)
        self.mapping_view.load_profile(active_prof)
        self.live_monitor_view.set_mappings(active_prof.mappings)
        self._sync_header_profile_combo()

        self.statusBar().setStyleSheet("color: #a1a1aa; font-size: 12px; background: #16161a; padding: 4px 12px;")
        self.statusBar().showMessage("Sẵn sàng. Can thiệp chuột đang HOẠT ĐỘNG.", 4000)
        self.tray.showMessage("MousePilot", f"Đã chuyển sang hồ sơ: {active_prof.name}", QSystemTrayIcon.MessageIcon.Information, 1500)

    def _on_mapping_changed(self, button: MouseButton, mapping: ButtonMapping):
        pid = self.config_manager.active_profile_id
        self.config_manager.update_mapping(pid, button, mapping)
        active_prof = self.config_manager.get_active_profile()
        self.hook_engine.set_mappings(active_prof.mappings)
        self.live_monitor_view.set_mappings(active_prof.mappings)

    def _toggle_hook_state(self):
        if self.hook_engine.is_paused:
            self.hook_engine.resume()
            self.btn_toggle_hook.setText("● CAN THIỆP: ĐANG BẬT")
            self.btn_toggle_hook.setProperty("class", "SuccessButton")
            self.action_tray_toggle.setText("Tạm dừng Can Thiệp")
        else:
            self.hook_engine.pause()
            self.btn_toggle_hook.setText("○ CAN THIỆP: ĐANG TẮT (BẤM ĐỂ BẬT)")
            self.btn_toggle_hook.setProperty("class", "PrimaryButton")
            self.action_tray_toggle.setText("Bật Can Thiệp Trở Lại")
        self.btn_toggle_hook.style().unpolish(self.btn_toggle_hook)
        self.btn_toggle_hook.style().polish(self.btn_toggle_hook)

    def closeEvent(self, event: QCloseEvent):
        if self.config_manager.minimize_to_tray:
            event.ignore()
            self.hide()
            self.tray.showMessage(
                "MousePilot",
                "Ứng dụng đang chạy ngầm trong khay hệ thống để tiếp tục can thiệp nút chuột.",
                QSystemTrayIcon.MessageIcon.Information, 2000
            )
        else:
            self._quit_application()

    def _quit_application(self):
        try:
            hwnd = int(self.winId())
            user32.UnregisterHotKey(hwnd, HOTKEY_PANIC_ID)
        except Exception:
            pass
        self.hook_engine.stop()
        QApplication.quit()
