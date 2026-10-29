import sys
import os
import ctypes
from ctypes import wintypes
from typing import Optional

# Ensure local package import
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont

from app.core.config_manager import ConfigManager
from app.core.mouse_hook import MouseHookEngine
from app.ui.theme import DARK_THEME
from app.ui.main_window import MainWindow

MUTEX_NAME = r"Local\MousePilot_SingleInstanceMutex"
kernel32 = ctypes.windll.kernel32

def check_single_instance() -> Optional[wintypes.HANDLE]:
    """Ensure only one instance of MousePilot runs using Win32 Named Mutex."""
    mutex = kernel32.CreateMutexW(None, True, MUTEX_NAME)
    last_error = kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183
    if last_error == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(mutex)
        return None
    return mutex

def setup_exception_hook():
    """Global exception catcher to prevent silent crashes."""
    def excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        import traceback
        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"[FATAL EXCEPTION]:\n{err_msg}")
    sys.excepthook = excepthook

def main():
    setup_exception_hook()

    # 1. Enforce Win32 Single Instance Mutex
    mutex_handle = check_single_instance()
    if not mutex_handle:
        print("[MousePilot] Instance already running, focusing existing window...")
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "MousePilot — Bộ Điều Khiển & Tùy Biến Nút Chuột Windows")
        if hwnd:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
        sys.exit(0)

    # 2. Configure High-DPI PassThrough
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("MousePilot")
    app.setOrganizationName("MousePilot")
    app.setStyleSheet(DARK_THEME)

    icon_path = os.path.join(os.path.dirname(__file__), "app", "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 3. Initialize Core Managers & Hook Engine
    config_mgr = ConfigManager()
    hook_engine = MouseHookEngine()
    hook_engine.start()

    # 4. Create Main Window
    window = MainWindow(config_mgr, hook_engine)

    # Clean shutdown hook
    def on_quit():
        print("[MousePilot] Đang dừng Hook và giải phóng tài nguyên...")
        hook_engine.stop()
        if mutex_handle:
            kernel32.ReleaseMutex(mutex_handle)
            kernel32.CloseHandle(mutex_handle)

    app.aboutToQuit.connect(on_quit)

    # Check start mode
    if "--tray" in sys.argv:
        window.hide()
    else:
        window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
