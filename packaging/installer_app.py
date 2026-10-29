import os
import sys
import zipfile
import shutil
import winreg
import subprocess
import ctypes
from ctypes import wintypes

from PySide6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QProgressBar,
    QFileDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QFont, QPixmap

APP_NAME = "MousePilot"
APP_DISPLAY_NAME = "MousePilot — Bộ Điều Khiển Nút Chuột Windows"
APP_VERSION = "1.0.0"
PUBLISHER = "MousePilot Software"
MUTEX_NAME = r"Local\MousePilot_SingleInstanceMutex"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def get_default_install_dir():
    if is_admin():
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        return os.path.join(pf, APP_NAME)
    else:
        local_app = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(local_app, "Programs", APP_NAME)

def get_payload_path():
    # If frozen with PyInstaller
    if hasattr(sys, "_MEIPASS"):
        p = os.path.join(sys._MEIPASS, "payload.zip")
        if os.path.exists(p):
            return p
    # Local fallback
    local_p = os.path.join(os.path.dirname(__file__), "payload.zip")
    if os.path.exists(local_p):
        return local_p
    return None

class InstallWorker(QThread):
    progress_changed = Signal(int, str)
    install_finished = Signal(bool, str)

    def __init__(self, target_dir: str, create_desktop: bool, create_startmenu: bool, autostart: bool):
        super().__init__()
        self.target_dir = target_dir
        self.create_desktop = create_desktop
        self.create_startmenu = create_startmenu
        self.autostart = autostart

    def run(self):
        try:
            payload_path = get_payload_path()
            if not payload_path or not os.path.exists(payload_path):
                self.install_finished.emit(False, "Không tìm thấy tệp gói cài đặt (payload.zip)!")
                return

            self.progress_changed.emit(10, "Đang chuẩn bị thư mục cài đặt...")
            os.makedirs(self.target_dir, exist_ok=True)

            self.progress_changed.emit(25, "Đang giải nén tập tin hệ thống MousePilot...")
            with zipfile.ZipFile(payload_path, 'r') as z:
                total_files = len(z.infolist())
                for idx, item in enumerate(z.infolist()):
                    z.extract(item, self.target_dir)
                    if idx % 10 == 0:
                        pct = 25 + int((idx / total_files) * 50)
                        self.progress_changed.emit(pct, f"Đang sao chép: {item.filename[:30]}...")

            target_exe = os.path.join(self.target_dir, "MousePilot.exe")
            uninstaller_exe = os.path.join(self.target_dir, "uninstall.exe")

            # 3. Create Shortcuts
            self.progress_changed.emit(80, "Đang tạo lối tắt màn hình và Start Menu...")
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")

                if self.create_desktop:
                    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
                    sc = shell.CreateShortCut(os.path.join(desktop, "MousePilot.lnk"))
                    sc.Targetpath = target_exe
                    sc.WorkingDirectory = self.target_dir
                    sc.IconLocation = f"{target_exe},0"
                    sc.Description = APP_DISPLAY_NAME
                    sc.save()

                if self.create_startmenu:
                    start_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\MousePilot")
                    os.makedirs(start_dir, exist_ok=True)
                    sc = shell.CreateShortCut(os.path.join(start_dir, "MousePilot.lnk"))
                    sc.Targetpath = target_exe
                    sc.WorkingDirectory = self.target_dir
                    sc.IconLocation = f"{target_exe},0"
                    sc.Description = APP_DISPLAY_NAME
                    sc.save()

                    if os.path.exists(uninstaller_exe):
                        sc_un = shell.CreateShortCut(os.path.join(start_dir, "Gỡ cài đặt MousePilot.lnk"))
                        sc_un.Targetpath = uninstaller_exe
                        sc_un.WorkingDirectory = self.target_dir
                        sc_un.Description = "Gỡ cài đặt MousePilot khỏi hệ thống"
                        sc_un.save()
            except Exception as e:
                print(f"[Installer] Lỗi tạo shortcut: {e}")

            # 4. Register in Windows Settings / Add Remove Programs
            self.progress_changed.emit(90, "Đang đăng ký ứng dụng vào hệ điều hành Windows...")
            root_key = winreg.HKEY_LOCAL_MACHINE if is_admin() else winreg.HKEY_CURRENT_USER
            uninstall_reg_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"
            try:
                with winreg.CreateKey(root_key, uninstall_reg_path) as k:
                    winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, APP_DISPLAY_NAME)
                    winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
                    winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
                    winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ, f'"{target_exe}",0')
                    winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, self.target_dir)
                    winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_exe}"')
                    winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
            except Exception as e:
                print(f"[Installer] Lỗi ghi registry: {e}")

            # 5. Windows Auto-start in Run key
            if self.autostart:
                self.progress_changed.emit(95, "Đang thiết lập khởi động cùng Windows...")
                try:
                    run_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_path, 0, winreg.KEY_SET_VALUE) as rk:
                        cmd = f'"{target_exe}" --tray'
                        winreg.SetValueEx(rk, APP_NAME, 0, winreg.REG_SZ, cmd)
                except Exception as e:
                    print(f"[Installer] Lỗi ghi autostart: {e}")

            self.progress_changed.emit(100, "Cài đặt thành công!")
            self.install_finished.emit(True, target_exe)

        except Exception as e:
            self.install_finished.emit(False, str(e))

class InstallerWindow(QWizard):
    """
    Modern Apple HIG / Windows 11 Fluent Installer Wizard.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cài Đặt MousePilot — Trình Cài Đặt Hệ Thống")
        self.resize(620, 460)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e24;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QPushButton {
                background-color: #0071e3;
                color: #ffffff;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0077ed;
            }
            QPushButton:disabled {
                background-color: #333340;
                color: #777788;
            }
            QLineEdit {
                background-color: #2a2a34;
                border: 1px solid #404052;
                border-radius: 6px;
                padding: 6px 10px;
                color: #ffffff;
            }
            QCheckBox {
                spacing: 8px;
            }
            QProgressBar {
                background-color: #272732;
                border: 1px solid #3c3c4a;
                border-radius: 6px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #34c759;
                border-radius: 5px;
            }
        """)

        # Add pages
        self.page_welcome = self._create_welcome_page()
        self.page_options = self._create_options_page()
        self.page_install = self._create_install_page()
        self.page_finish = self._create_finish_page()

        self.addPage(self.page_welcome)
        self.addPage(self.page_options)
        self.addPage(self.page_install)
        self.addPage(self.page_finish)

        self.target_exe_path = ""
        self.currentIdChanged.connect(self._on_page_changed)

    def _create_welcome_page(self):
        page = QWizardPage()
        page.setTitle("Chào Mừng Đến Với Trình Cài Đặt MousePilot")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        lbl_desc = QLabel(
            "Trình cài đặt này sẽ cài đặt <b>MousePilot</b> thành một ứng dụng hệ thống trên máy tính của bạn.<br><br>"
            "MousePilot giúp bạn:<br>"
            "• Nhận diện chuột phần cứng (USB, Wireless 2.4G, Bluetooth, Touchpad).<br>"
            "• Tùy biến mọi nút chuột: Gán phím tắt, Media, Mở App, Macro.<br>"
            "• Chạy ngầm mượt mà 0-freeze, có khay hệ thống và phím tắt khẩn cấp an toàn.<br><br>"
            "Nhấn <b>Tiếp tục (Next)</b> để cấu hình thư mục và tùy chọn cài đặt."
        )
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)
        layout.addStretch()
        return page

    def _create_options_page(self):
        page = QWizardPage()
        page.setTitle("Chọn Vị Trí Cài Đặt & Tùy Chọn")
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Thư mục cài đặt ứng dụng:"))
        dir_layout = QHBoxLayout()
        self.txt_dir = QLineEdit(get_default_install_dir())
        dir_layout.addWidget(self.txt_dir)
        btn_browse = QPushButton("Chọn Thư Mục...")
        btn_browse.setStyleSheet("background-color: #363646;")
        btn_browse.clicked.connect(self._browse_dir)
        dir_layout.addWidget(btn_browse)
        layout.addLayout(dir_layout)

        layout.addWidget(QLabel("Tùy chọn bổ sung:"))
        self.chk_desktop = QCheckBox("Tạo biểu tượng lối tắt ngoài màn hình Desktop")
        self.chk_desktop.setChecked(True)
        layout.addWidget(self.chk_desktop)

        self.chk_startmenu = QCheckBox("Tạo lối tắt trong Start Menu và gỡ cài đặt")
        self.chk_startmenu.setChecked(True)
        layout.addWidget(self.chk_startmenu)

        self.chk_autostart = QCheckBox("Tự động chạy ngầm trong khay hệ thống khi khởi động Windows")
        self.chk_autostart.setChecked(True)
        layout.addWidget(self.chk_autostart)

        self.chk_system_reg = QCheckBox("Đăng ký thành phần mềm hệ thống (Apps & Features / Control Panel)")
        self.chk_system_reg.setChecked(True)
        layout.addWidget(self.chk_system_reg)

        layout.addStretch()
        return page

    def _create_install_page(self):
        page = QWizardPage()
        page.setTitle("Đang Tiến Hành Cài Đặt")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        self.lbl_status = QLabel("Đang chuẩn bị...")
        layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        return page

    def _create_finish_page(self):
        page = QWizardPage()
        page.setTitle("Cài Đặt Hoàn Tất Thành Công!")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        lbl_done = QLabel(
            "Chúc mừng! <b>MousePilot</b> đã được cài đặt thành công thành ứng dụng hệ thống trên máy tính của bạn.<br><br>"
            "Bạn có thể mở ứng dụng từ màn hình Desktop, Start Menu, hoặc từ khay hệ thống bất cứ lúc nào."
        )
        lbl_done.setWordWrap(True)
        layout.addWidget(lbl_done)

        self.chk_launch = QCheckBox("Khởi chạy MousePilot ngay bây giờ")
        self.chk_launch.setChecked(True)
        layout.addWidget(self.chk_launch)

        layout.addStretch()
        return page

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn Thư Mục Cài Đặt", self.txt_dir.text())
        if d:
            self.txt_dir.setText(os.path.join(d, APP_NAME))

    def _on_page_changed(self, page_id: int):
        if page_id == 2:  # Install page
            self.button(QWizard.WizardButton.BackButton).setEnabled(False)
            self.button(QWizard.WizardButton.NextButton).setEnabled(False)

            self.worker = InstallWorker(
                target_dir=self.txt_dir.text().strip(),
                create_desktop=self.chk_desktop.isChecked(),
                create_startmenu=self.chk_startmenu.isChecked(),
                autostart=self.chk_autostart.isChecked(),
            )
            self.worker.progress_changed.connect(self._on_progress)
            self.worker.install_finished.connect(self._on_install_finished)
            self.worker.start()

        elif page_id == 3:  # Finish page
            self.button(QWizard.WizardButton.BackButton).setEnabled(False)

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(msg)

    def _on_install_finished(self, success: bool, result_msg: str):
        if success:
            self.target_exe_path = result_msg
            self.next()
        else:
            QMessageBox.critical(self, "Lỗi Cài Đặt", f"Quá trình cài đặt gặp sự cố:\n{result_msg}")

    def accept(self):
        if self.chk_launch.isChecked() and self.target_exe_path and os.path.exists(self.target_exe_path):
            try:
                subprocess.Popen([self.target_exe_path])
            except Exception:
                pass
        super().accept()

def main():
    app = QApplication(sys.argv)
    wizard = InstallerWindow()
    wizard.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
