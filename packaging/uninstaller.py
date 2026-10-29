import os
import sys
import winreg
import shutil
import subprocess
import ctypes
from ctypes import wintypes

APP_NAME = "MousePilot"
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\MousePilot"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def kill_running_app():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "MousePilot.exe"], capture_output=True)
    except Exception:
        pass

def remove_shortcuts(install_dir: str):
    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    desktop_lnk = os.path.join(desktop, "MousePilot.lnk")
    if os.path.exists(desktop_lnk):
        try: os.remove(desktop_lnk)
        except Exception: pass

    programs = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\MousePilot")
    if os.path.exists(programs):
        try: shutil.rmtree(programs, ignore_errors=True)
        except Exception: pass

def remove_registry():
    # Remove autostart
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
    except Exception:
        pass

    # Remove uninstall entry in HKCU
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
    except Exception:
        pass

    # Remove uninstall entry in HKLM if present
    try:
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, UNINSTALL_KEY)
    except Exception:
        pass

def main():
    install_dir = os.path.abspath(os.path.dirname(__file__))

    # Confirmation pop-up
    MB_YESNO = 4
    MB_ICONQUESTION = 32
    IDYES = 6
    res = ctypes.windll.user32.MessageBoxW(
        0,
        "Bạn có chắc chắn muốn gỡ cài đặt hoàn toàn MousePilot khỏi máy tính không?",
        "Gỡ Cài Đặt MousePilot",
        MB_YESNO | MB_ICONQUESTION
    )
    if res != IDYES:
        sys.exit(0)

    kill_running_app()
    remove_shortcuts(install_dir)
    remove_registry()

    # Schedule self-deletion of install_dir via cmd after exit
    bat_cleaner = os.path.join(os.environ.get("TEMP", ""), "clean_mousepilot.bat")
    with open(bat_cleaner, "w") as f:
        f.write(f'''@echo off
timeout /t 2 /nobreak >nul
rmdir /s /q "{install_dir}"
del "%~f0"
''')

    subprocess.Popen(["cmd.exe", "/c", bat_cleaner], creationflags=0x08000000)

    ctypes.windll.user32.MessageBoxW(
        0,
        "MousePilot đã được gỡ cài đặt thành công khỏi hệ thống máy tính của bạn.",
        "Gỡ Cài Đặt Hoàn Tất",
        64 # MB_ICONINFORMATION
    )
    sys.exit(0)

if __name__ == "__main__":
    main()
