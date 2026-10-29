from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any

class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
    XBUTTON1 = "xbutton1"   # Side Button 1 (Back / Nút hông dưới)
    XBUTTON2 = "xbutton2"   # Side Button 2 (Forward / Nút hông trên)
    WHEEL_UP = "wheel_up"
    WHEEL_DOWN = "wheel_down"
    WHEEL_LEFT = "wheel_left"
    WHEEL_RIGHT = "wheel_right"

    @property
    def display_name(self) -> str:
        names = {
            MouseButton.LEFT: "Chuột Trái (Left Click)",
            MouseButton.RIGHT: "Chuột Phải (Right Click)",
            MouseButton.MIDDLE: "Nút Cuộn Giữa (Middle / Wheel Click)",
            MouseButton.XBUTTON1: "Nút Hông 1 (Back / Nút Dưới)",
            MouseButton.XBUTTON2: "Nút Hông 2 (Forward / Nút Trên)",
            MouseButton.WHEEL_UP: "Cuộn Lên (Scroll Up)",
            MouseButton.WHEEL_DOWN: "Cuộn Xuống (Scroll Down)",
            MouseButton.WHEEL_LEFT: "Nghiêng Bánh Xe Trái (Tilt Left)",
            MouseButton.WHEEL_RIGHT: "Nghiêng Bánh Xe Phải (Tilt Right)",
        }
        return names.get(self, self.value)

    @property
    def short_name(self) -> str:
        shorts = {
            MouseButton.LEFT: "Trái (L)",
            MouseButton.RIGHT: "Phải (R)",
            MouseButton.MIDDLE: "Giữa (M)",
            MouseButton.XBUTTON1: "Hông 1 (Back)",
            MouseButton.XBUTTON2: "Hông 2 (Fwd)",
            MouseButton.WHEEL_UP: "Cuộn Lên",
            MouseButton.WHEEL_DOWN: "Cuộn Xuống",
            MouseButton.WHEEL_LEFT: "Nghiêng Trái",
            MouseButton.WHEEL_RIGHT: "Nghiêng Phải",
        }
        return shorts.get(self, self.value)

class ActionCategory(str, Enum):
    DEFAULT = "default"         # Giữ nguyên chức năng gốc của Windows
    MOUSE = "mouse"             # Chức năng chuột khác (Double Click, Middle Click...)
    KEYBOARD = "keyboard"       # Phím tắt & tổ hợp phím (Ctrl+C, Ctrl+V, Win+Tab...)
    MEDIA = "media"             # Điều khiển nhạc & âm lượng (Volume, Mute, Play/Pause)
    SYSTEM = "system"           # Tác vụ hệ điều hành (Chụp màn hình, Khóa máy, Thu nhỏ...)
    CUSTOM_APP = "custom_app"   # Mở ứng dụng hoặc trang Web
    TEXT_SNIPPET = "text_snippet" # Tự động gõ đoạn văn bản / chữ ký
    DPI_SPEED = "dpi_speed"     # Đổi tốc độ chuột / DPI
    DISABLED = "disabled"       # Vô hiệu hóa nút (không làm gì)

@dataclass
class ButtonMapping:
    button: MouseButton
    category: ActionCategory = ActionCategory.DEFAULT
    action_type: str = "default"
    label: str = "Mặc định hệ thống"
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "button": self.button.value,
            "category": self.category.value,
            "action_type": self.action_type,
            "label": self.label,
            "params": self.params,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ButtonMapping":
        return cls(
            button=MouseButton(data.get("button", "left")),
            category=ActionCategory(data.get("category", "default")),
            action_type=data.get("action_type", "default"),
            label=data.get("label", "Mặc định hệ thống"),
            params=data.get("params", {}),
            enabled=data.get("enabled", True),
        )

@dataclass
class Profile:
    id: str
    name: str
    description: str
    is_active: bool = False
    mappings: Dict[str, ButtonMapping] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "mappings": {k: v.to_dict() for k, v in self.mappings.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        mappings = {}
        raw_mappings = data.get("mappings", {})
        for k, v in raw_mappings.items():
            mappings[k] = ButtonMapping.from_dict(v)
        return cls(
            id=data.get("id", "default"),
            name=data.get("name", "Mặc định"),
            description=data.get("description", ""),
            is_active=data.get("is_active", False),
            mappings=mappings,
        )

@dataclass
class MouseDevice:
    device_id: str
    name: str
    friendly_name: str
    manufacturer: str
    hardware_id: str
    status: str
    is_touchpad: bool = False
    connection_type: str = "USB"
    button_count: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
