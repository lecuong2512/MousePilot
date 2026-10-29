import json
import os
import sys
from typing import Dict, List, Optional
from app.core.models import Profile, ButtonMapping, MouseButton, ActionCategory

APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "MousePilot")
CONFIG_FILE = os.path.join(APPDATA_DIR, "config.json")

def create_default_presets() -> Dict[str, Profile]:
    """Build default built-in profile presets."""
    # 1. Mặc định hệ thống
    default_mappings = {}
    for btn in MouseButton:
        default_mappings[btn.value] = ButtonMapping(
            button=btn,
            category=ActionCategory.DEFAULT,
            action_type="default",
            label="Mặc định Windows",
        )
    p_default = Profile(
        id="default",
        name="Mặc Định (Default)",
        description="Các nút chuột hoạt động theo cài đặt gốc của hệ điều hành Windows.",
        is_active=True,
        mappings=default_mappings,
    )

    # 2. Văn phòng & Năng suất (Office & Productivity)
    office_mappings = dict(default_mappings)
    office_mappings[MouseButton.XBUTTON1.value] = ButtonMapping(
        button=MouseButton.XBUTTON1,
        category=ActionCategory.KEYBOARD,
        action_type="copy",
        label="Sao chép (Ctrl + C)",
    )
    office_mappings[MouseButton.XBUTTON2.value] = ButtonMapping(
        button=MouseButton.XBUTTON2,
        category=ActionCategory.KEYBOARD,
        action_type="paste",
        label="Dán (Ctrl + V)",
    )
    office_mappings[MouseButton.MIDDLE.value] = ButtonMapping(
        button=MouseButton.MIDDLE,
        category=ActionCategory.KEYBOARD,
        action_type="close_tab",
        label="Đóng Tab hiện tại (Ctrl + W)",
    )
    p_office = Profile(
        id="office",
        name="Văn Phòng & Năng Suất (Office)",
        description="Tối ưu cho công việc: Nút hông 1 sao chép (Ctrl+C), Nút hông 2 dán (Ctrl+V), Nút giữa đóng Tab.",
        is_active=False,
        mappings=office_mappings,
    )

    # 3. Đa phương tiện & Giải trí (Media Control)
    media_mappings = dict(default_mappings)
    media_mappings[MouseButton.XBUTTON1.value] = ButtonMapping(
        button=MouseButton.XBUTTON1,
        category=ActionCategory.MEDIA,
        action_type="media_prev",
        label="Bài trước đó (Previous Track)",
    )
    media_mappings[MouseButton.XBUTTON2.value] = ButtonMapping(
        button=MouseButton.XBUTTON2,
        category=ActionCategory.MEDIA,
        action_type="media_next",
        label="Bài kế tiếp (Next Track)",
    )
    media_mappings[MouseButton.MIDDLE.value] = ButtonMapping(
        button=MouseButton.MIDDLE,
        category=ActionCategory.MEDIA,
        action_type="media_play_pause",
        label="Phát / Dừng nhạc (Play/Pause)",
    )
    p_media = Profile(
        id="media",
        name="Giải Trí & Âm Nhạc (Media)",
        description="Điều khiển nghe nhạc YouTube/Spotify: Nút hông qua bài/lùi bài, Nút giữa Play/Pause.",
        is_active=False,
        mappings=media_mappings,
    )

    # 4. Lập trình viên & Thiết kế (Dev & Design)
    dev_mappings = dict(default_mappings)
    dev_mappings[MouseButton.XBUTTON1.value] = ButtonMapping(
        button=MouseButton.XBUTTON1,
        category=ActionCategory.KEYBOARD,
        action_type="undo",
        label="Hoàn tác (Ctrl + Z)",
    )
    dev_mappings[MouseButton.XBUTTON2.value] = ButtonMapping(
        button=MouseButton.XBUTTON2,
        category=ActionCategory.KEYBOARD,
        action_type="redo",
        label="Làm lại (Ctrl + Y)",
    )
    dev_mappings[MouseButton.MIDDLE.value] = ButtonMapping(
        button=MouseButton.MIDDLE,
        category=ActionCategory.KEYBOARD,
        action_type="save",
        label="Lưu nhanh tệp (Ctrl + S)",
    )
    p_dev = Profile(
        id="developer",
        name="Lập Trình & Đồ Họa (Dev & Design)",
        description="Nút hông Ctrl+Z (Undo) và Ctrl+Y (Redo), Nút giữa Ctrl+S (Lưu tệp tức thì).",
        is_active=False,
        mappings=dev_mappings,
    )

    return {
        "default": p_default,
        "office": p_office,
        "media": p_media,
        "developer": p_dev,
    }

class ConfigManager:
    """Manages persistent application settings and mouse mapping profiles."""

    def __init__(self):
        self.profiles: Dict[str, Profile] = {}
        self.active_profile_id: str = "default"
        self.start_with_windows: bool = False
        self.minimize_to_tray: bool = True
        self.left_click_guard: bool = True
        self.emergency_panic_key: str = "Ctrl + Shift + Alt + M"
        self.load()

    def get_active_profile(self) -> Profile:
        if self.active_profile_id in self.profiles:
            return self.profiles[self.active_profile_id]
        if "default" in self.profiles:
            return self.profiles["default"]
        # Fallback create
        presets = create_default_presets()
        self.profiles = presets
        return presets["default"]

    def set_active_profile(self, profile_id: str) -> None:
        if profile_id in self.profiles:
            for p in self.profiles.values():
                p.is_active = (p.id == profile_id)
            self.active_profile_id = profile_id
            self.save()

    def update_mapping(self, profile_id: str, button: MouseButton, mapping: ButtonMapping) -> None:
        if profile_id in self.profiles:
            self.profiles[profile_id].mappings[button.value] = mapping
            self.save()

    def save(self) -> None:
        """Serialize configuration to JSON."""
        try:
            os.makedirs(APPDATA_DIR, exist_ok=True)
            data = {
                "active_profile_id": self.active_profile_id,
                "start_with_windows": self.start_with_windows,
                "minimize_to_tray": self.minimize_to_tray,
                "left_click_guard": self.left_click_guard,
                "emergency_panic_key": self.emergency_panic_key,
                "profiles": {pid: p.to_dict() for pid, p in self.profiles.items()},
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ConfigManager] Save config error: {e}")

    def load(self) -> None:
        """Load configuration from JSON or initialize defaults."""
        if not os.path.exists(CONFIG_FILE):
            self.profiles = create_default_presets()
            self.active_profile_id = "default"
            self.save()
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.active_profile_id = data.get("active_profile_id", "default")
            self.start_with_windows = data.get("start_with_windows", False)
            self.minimize_to_tray = data.get("minimize_to_tray", True)
            self.left_click_guard = data.get("left_click_guard", True)
            self.emergency_panic_key = data.get("emergency_panic_key", "Ctrl + Shift + Alt + M")

            raw_profiles = data.get("profiles", {})
            self.profiles = {}
            for pid, pdata in raw_profiles.items():
                self.profiles[pid] = Profile.from_dict(pdata)

            if not self.profiles:
                self.profiles = create_default_presets()
        except Exception as e:
            print(f"[ConfigManager] Load config error, resetting defaults: {e}")
            self.profiles = create_default_presets()
            self.active_profile_id = "default"
            self.save()
