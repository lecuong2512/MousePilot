import os
import subprocess
import threading
from typing import Dict, Any, Optional
from app.core.models import ButtonMapping, ActionCategory
from app.core.win32_input import (
    send_mouse_click,
    send_key_combo,
    send_unicode_text,
    get_mouse_speed,
    set_mouse_speed,
)

# Standard Keyboard Shortcut Presets
SHORTCUT_PRESETS = {
    "copy": (["ctrl", "c"], "Sao chép (Ctrl + C)"),
    "paste": (["ctrl", "v"], "Dán (Ctrl + V)"),
    "cut": (["ctrl", "x"], "Cắt (Ctrl + X)"),
    "undo": (["ctrl", "z"], "Hoàn tác (Ctrl + Z)"),
    "redo": (["ctrl", "y"], "Làm lại (Ctrl + Y)"),
    "save": (["ctrl", "s"], "Lưu tệp (Ctrl + S)"),
    "select_all": (["ctrl", "a"], "Chọn tất cả (Ctrl + A)"),
    "close_tab": (["ctrl", "w"], "Đóng Tab / Cửa sổ (Ctrl + W)"),
    "new_tab": (["ctrl", "t"], "Mở Tab Mới (Ctrl + T)"),
    "reopen_tab": (["ctrl", "shift", "t"], "Mở lại Tab vừa đóng (Ctrl + Shift + T)"),
    "switch_window": (["alt", "tab"], "Chuyển cửa sổ (Alt + Tab)"),
    "task_view": (["win", "tab"], "Task View hệ thống (Win + Tab)"),
    "show_desktop": (["win", "d"], "Hiện màn hình Desktop (Win + D)"),
    "screenshot": (["win", "shift", "s"], "Chụp ảnh màn hình Snipping (Win + Shift + S)"),
    "lock_pc": (["win", "l"], "Khóa màn hình máy tính (Win + L)"),
    "file_explorer": (["win", "e"], "Mở File Explorer (Win + E)"),
    "refresh": (["f5"], "Làm mới trang (F5)"),
    "hard_refresh": (["ctrl", "f5"], "Xóa cache & Tải lại trang (Ctrl + F5)"),
    "enter": (["enter"], "Phím Enter"),
    "escape": (["esc"], "Phím Esc"),
    "backspace": (["backspace"], "Phím Backspace"),
    "delete": (["delete"], "Phím Delete"),
}

# Media Action Presets
MEDIA_PRESETS = {
    "volume_up": (["volume_up"], "Tăng âm lượng"),
    "volume_down": (["volume_down"], "Giảm âm lượng"),
    "volume_mute": (["volume_mute"], "Tắt / Bật tiếng (Mute)"),
    "media_play_pause": (["media_play_pause"], "Phát / Tạm dừng nhạc (Play/Pause)"),
    "media_next": (["media_next"], "Bài kế tiếp (Next Track)"),
    "media_prev": (["media_prev"], "Bài trước đó (Previous Track)"),
}

class ActionExecutor:
    """Executes actions mapped to mouse buttons in non-blocking background workers."""

    def __init__(self):
        self._prev_dpi_speed: Optional[int] = None

    def execute_mapping(self, mapping: ButtonMapping) -> bool:
        """
        Execute the action for the given button mapping.
        Returns True if the event was handled and swallowed; False if it should pass through.
        """
        if not mapping.enabled or mapping.category == ActionCategory.DEFAULT:
            return False

        if mapping.category == ActionCategory.DISABLED:
            # Swallow event without doing anything
            return True

        # Dispatch async to avoid holding the hook callback
        threading.Thread(target=self._run_action, args=(mapping,), daemon=True).start()
        return True

    def _run_action(self, mapping: ButtonMapping) -> None:
        cat = mapping.category
        act = mapping.action_type
        params = mapping.params or {}

        try:
            if cat == ActionCategory.MOUSE:
                if act == "double_click":
                    send_mouse_click("left", double=True)
                elif act == "middle_click":
                    send_mouse_click("middle")
                elif act == "right_click":
                    send_mouse_click("right")
                elif act == "left_click":
                    send_mouse_click("left")
                elif act == "xbutton1":
                    send_mouse_click("xbutton1")
                elif act == "xbutton2":
                    send_mouse_click("xbutton2")

            elif cat == ActionCategory.KEYBOARD:
                if act in SHORTCUT_PRESETS:
                    keys, _ = SHORTCUT_PRESETS[act]
                    send_key_combo(keys)
                elif act == "custom_combo":
                    keys = params.get("keys", [])
                    if keys:
                        send_key_combo(keys)

            elif cat == ActionCategory.MEDIA:
                if act in MEDIA_PRESETS:
                    keys, _ = MEDIA_PRESETS[act]
                    send_key_combo(keys)

            elif cat == ActionCategory.SYSTEM:
                if act == "task_view":
                    send_key_combo(["win", "tab"])
                elif act == "show_desktop":
                    send_key_combo(["win", "d"])
                elif act == "screenshot":
                    send_key_combo(["win", "shift", "s"])
                elif act == "lock_pc":
                    send_key_combo(["win", "l"])
                elif act == "explorer":
                    send_key_combo(["win", "e"])

            elif cat == ActionCategory.CUSTOM_APP:
                target = params.get("target", "").strip()
                if target:
                    if target.startswith("http://") or target.startswith("https://") or os.path.exists(target):
                        os.startfile(target)
                    else:
                        subprocess.Popen(target, shell=True)

            elif cat == ActionCategory.TEXT_SNIPPET:
                text = params.get("text", "")
                if text:
                    send_unicode_text(text)

            elif cat == ActionCategory.DPI_SPEED:
                current = get_mouse_speed()
                target_speed = params.get("speed", 15 if current <= 10 else 10)
                set_mouse_speed(target_speed)

        except Exception as e:
            print(f"[ActionExecutor] Action error {act}: {e}")
