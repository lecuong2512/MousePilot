import ctypes
from ctypes import wintypes
import time
from typing import List, Optional

# Win32 APIs
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Magic marker to recognize our injected inputs and prevent infinite hook loops
MAGIC_EXTRA_INFO = 0x564D5301

# Input Types
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

# Mouse Event Flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000

XBUTTON1 = 0x0001
XBUTTON2 = 0x0002

# Keyboard Event Flags
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

# System Parameters
SPI_GETMOUSESPEED = 0x0070
SPI_SETMOUSESPEED = 0x0071
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02

# Common Virtual Key Codes
VK_MAP = {
    # Modifiers
    "ctrl": 0x11,
    "lctrl": 0xA2,
    "rctrl": 0xA3,
    "shift": 0x10,
    "lshift": 0xA0,
    "rshift": 0xA1,
    "alt": 0x12,
    "lalt": 0xA4,
    "ralt": 0xA5,
    "win": 0x5B,
    "lwin": 0x5B,
    "rwin": 0x5C,
    
    # Navigation / Editing
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "prtscr": 0x2C,
    "printscreen": 0x2C,
    "insert": 0x2D,
    "delete": 0x2E,

    # Function Keys
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,

    # Media Controls
    "volume_mute": 0xAD,
    "volume_down": 0xAE,
    "volume_up": 0xAF,
    "media_next": 0xB0,
    "media_prev": 0xB1,
    "media_stop": 0xB2,
    "media_play_pause": 0xB3,
    "browser_back": 0xA6,
    "browser_forward": 0xA7,
    "browser_refresh": 0xA8,
    "browser_stop": 0xA9,
    "browser_search": 0xAA,
    "browser_favorites": 0xAB,
    "browser_home": 0xAC,
}

# Add basic letters and digits
for c in "abcdefghijklmnopqrstuvwxyz":
    VK_MAP[c] = ord(c.upper())
for d in "0123456789":
    VK_MAP[d] = ord(d)


# CTypes Structures for SendInput
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUT_UNION),
    ]

LPINPUT = ctypes.POINTER(INPUT)
user32.SendInput.argtypes = [wintypes.UINT, LPINPUT, ctypes.c_int]
user32.SendInput.restype = wintypes.UINT

def send_key_combo(keys: List[str]) -> None:
    """
    Send a sequence of keys down then up in reverse order.
    Uses keybd_event with scan codes and MAGIC_EXTRA_INFO for 100% reliable execution.
    """
    vk_codes = []
    for k in keys:
        k_clean = k.lower().strip()
        vk = VK_MAP.get(k_clean)
        if vk is not None:
            vk_codes.append(vk)

    if not vk_codes:
        return

    # 1. Press all keys down in order
    for vk in vk_codes:
        scan = user32.MapVirtualKeyW(vk, 0)
        flags = 0
        if vk in (0x5B, 0x5C, 0xA5, 0xA3): # Extended keys (Win, Right Alt, Right Ctrl)
            flags |= KEYEVENTF_EXTENDEDKEY
        user32.keybd_event(vk, scan, flags, MAGIC_EXTRA_INFO)
        time.sleep(0.012)

    # Dwell time to ensure target application registers the combo
    time.sleep(0.035)

    # 2. Release all keys in reverse order
    for vk in reversed(vk_codes):
        scan = user32.MapVirtualKeyW(vk, 0)
        flags = KEYEVENTF_KEYUP
        if vk in (0x5B, 0x5C, 0xA5, 0xA3):
            flags |= KEYEVENTF_EXTENDEDKEY
        user32.keybd_event(vk, scan, flags, MAGIC_EXTRA_INFO)
        time.sleep(0.012)

def send_mouse_click(button: str, double: bool = False) -> None:
    """Simulate a mouse button click or double click using mouse_event."""
    button = button.lower()
    flags_down = 0
    flags_up = 0
    data = 0

    if button in ("left", "l"):
        flags_down = MOUSEEVENTF_LEFTDOWN
        flags_up = MOUSEEVENTF_LEFTUP
    elif button in ("right", "r"):
        flags_down = MOUSEEVENTF_RIGHTDOWN
        flags_up = MOUSEEVENTF_RIGHTUP
    elif button in ("middle", "m"):
        flags_down = MOUSEEVENTF_MIDDLEDOWN
        flags_up = MOUSEEVENTF_MIDDLEUP
    elif button in ("xbutton1", "back"):
        flags_down = MOUSEEVENTF_XDOWN
        flags_up = MOUSEEVENTF_XUP
        data = XBUTTON1
    elif button in ("xbutton2", "forward"):
        flags_down = MOUSEEVENTF_XDOWN
        flags_up = MOUSEEVENTF_XUP
        data = XBUTTON2

    if not flags_down:
        return

    clicks = 2 if double else 1
    for i in range(clicks):
        user32.mouse_event(flags_down, 0, 0, data, MAGIC_EXTRA_INFO)
        time.sleep(0.018)
        user32.mouse_event(flags_up, 0, 0, data, MAGIC_EXTRA_INFO)
        if i < clicks - 1:
            time.sleep(0.05)

def send_mouse_wheel(delta: int, horizontal: bool = False) -> None:
    """Simulate wheel scrolling."""
    flag = MOUSEEVENTF_HWHEEL if horizontal else MOUSEEVENTF_WHEEL
    user32.mouse_event(flag, 0, 0, delta, MAGIC_EXTRA_INFO)

def send_unicode_text(text: str) -> None:
    """Simulate typing text characters directly via Unicode scan codes."""
    for char in text:
        code = ord(char)
        # Down
        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.u.ki.wVk = 0
        inp_down.u.ki.wScan = code
        inp_down.u.ki.dwFlags = KEYEVENTF_UNICODE
        inp_down.u.ki.time = 0
        inp_down.u.ki.dwExtraInfo = MAGIC_EXTRA_INFO

        # Up
        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.u.ki.wVk = 0
        inp_up.u.ki.wScan = code
        inp_up.u.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
        inp_up.u.ki.time = 0
        inp_up.u.ki.dwExtraInfo = MAGIC_EXTRA_INFO

        arr = (INPUT * 2)(inp_down, inp_up)
        user32.SendInput(2, arr, ctypes.sizeof(INPUT))
        time.sleep(0.01)

def get_mouse_speed() -> int:
    """Get Windows mouse pointer speed (1-20)."""
    speed = ctypes.c_uint()
    user32.SystemParametersInfoW(SPI_GETMOUSESPEED, 0, ctypes.byref(speed), 0)
    return speed.value

def set_mouse_speed(speed: int) -> bool:
    """Set Windows mouse pointer speed (1-20)."""
    speed = max(1, min(20, speed))
    res = user32.SystemParametersInfoW(SPI_SETMOUSESPEED, 0, speed, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
    return bool(res)
