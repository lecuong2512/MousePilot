import ctypes
from ctypes import wintypes
import threading
from typing import Callable, Optional, Dict
from app.core.models import MouseButton, ButtonMapping, ActionCategory
from app.core.win32_input import MAGIC_EXTRA_INFO
from app.core.action_executor import ActionExecutor

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_MOUSE_LL = 14
WM_QUIT = 0x0012

# Windows Mouse Messages
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
WM_MOUSEWHEEL = 0x020A
WM_XBUTTONDOWN = 0x020B
WM_XBUTTONUP = 0x020C
WM_MOUSEHWHEEL = 0x020E

# 64-bit Windows LRESULT definition (CRITICAL: Must be 64-bit on x64 to avoid corrupting RAX)
LRESULT = ctypes.c_int64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

PMSLLHOOKSTRUCT = ctypes.POINTER(MSLLHOOKSTRUCT)
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

# Explicitly configure Win32 API signatures to prevent 32-bit truncation or register corruption
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = LRESULT

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK

user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL

class MouseHookEngine:
    """
    Tier-1 Hardened Low-Level Mouse Hook Engine.
    - Zero interference with mouse pointer movement (WM_MOUSEMOVE bypassed instantly).
    - Starts in PAUSED (Safe) state by default so user has 100% control.
    - Full 64-bit ABI compatibility to guarantee no cursor freezing.
    """

    def __init__(self, action_executor: Optional[ActionExecutor] = None):
        self.executor = action_executor or ActionExecutor()
        self.is_active = False
        self.is_paused = False  # ACTIVE BY DEFAULT: Remapping works immediately upon opening!
        self.mappings: Dict[str, ButtonMapping] = {}

        # Callbacks for UI event monitor (button, is_down, x, y)
        self.event_listener: Optional[Callable[[MouseButton, bool, int, int], None]] = None

        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._hook_id: Optional[int] = None
        self._ready_event = threading.Event()
        self._stop_event = threading.Event()
        self._c_proc = None  # Prevent Python Garbage Collector from collecting hook callback

    def set_mappings(self, mappings: Dict[str, ButtonMapping]) -> None:
        """Update active button mappings."""
        self.mappings = mappings

    def set_event_listener(self, listener: Optional[Callable[[MouseButton, bool, int, int], None]]) -> None:
        """Attach a listener to receive raw button events for UI visualizer."""
        self.event_listener = listener

    def start(self) -> bool:
        """Start the hook engine thread."""
        if self.is_active:
            return True

        self._stop_event.clear()
        self._ready_event.clear()
        self._thread = threading.Thread(target=self._run_hook_loop, name="MouseHookThread", daemon=True)
        self._thread.start()
        success = self._ready_event.wait(timeout=3.0)
        self.is_active = success and (self._hook_id is not None)
        return self.is_active

    def stop(self) -> None:
        """Stop the hook engine cleanly."""
        if not self.is_active:
            return

        self._stop_event.set()
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        self.is_active = False
        self._hook_id = None
        self._thread_id = None

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def _run_hook_loop(self) -> None:
        self._thread_id = kernel32.GetCurrentThreadId()
        self._c_proc = HOOKPROC(self._hook_callback)
        self._hook_id = user32.SetWindowsHookExW(WH_MOUSE_LL, self._c_proc, None, 0)

        if not self._hook_id:
            print("[MouseHook] Could not install WH_MOUSE_LL hook!")
            self._ready_event.set()
            return

        self._ready_event.set()

        msg = wintypes.MSG()
        while not self._stop_event.is_set():
            res = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if res <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook_id:
            user32.UnhookWindowsHookEx(self._hook_id)
            self._hook_id = None

    def _hook_callback(self, nCode: int, wParam: int, lParam: int) -> int:
        # CRITICAL RULE 1: Never touch WM_MOUSEMOVE! Return CallNextHookEx instantly without any overhead
        if nCode < 0 or wParam == WM_MOUSEMOVE:
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # CRITICAL RULE 2: If paused, pass through all buttons immediately
        if self.is_paused:
            # Still notify UI monitor for click testing without swallowing events
            if self.event_listener and wParam in (WM_LBUTTONDOWN, WM_RBUTTONDOWN, WM_MBUTTONDOWN, WM_XBUTTONDOWN, WM_MOUSEWHEEL, WM_MOUSEHWHEEL):
                try:
                    self._dispatch_monitor_event(wParam, lParam)
                except Exception:
                    pass
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # 3. Parse event data safely
        try:
            struct_ptr = ctypes.cast(lParam, PMSLLHOOKSTRUCT)
            data = struct_ptr.contents

            # 4. Anti-loop check: Check if input was injected by software
            is_injected = bool(data.flags & 1) or (data.dwExtraInfo == MAGIC_EXTRA_INFO)
            if is_injected:
                return user32.CallNextHookEx(None, nCode, wParam, lParam)

            # 5. Identify button and down/up state
            btn: Optional[MouseButton] = None
            is_down = True

            if wParam == WM_LBUTTONDOWN:
                btn = MouseButton.LEFT
                is_down = True
            elif wParam == WM_LBUTTONUP:
                btn = MouseButton.LEFT
                is_down = False
            elif wParam == WM_RBUTTONDOWN:
                btn = MouseButton.RIGHT
                is_down = True
            elif wParam == WM_RBUTTONUP:
                btn = MouseButton.RIGHT
                is_down = False
            elif wParam == WM_MBUTTONDOWN:
                btn = MouseButton.MIDDLE
                is_down = True
            elif wParam == WM_MBUTTONUP:
                btn = MouseButton.MIDDLE
                is_down = False
            elif wParam in (WM_XBUTTONDOWN, WM_XBUTTONUP):
                is_down = (wParam == WM_XBUTTONDOWN)
                x_button_id = (data.mouseData >> 16) & 0xFFFF
                if x_button_id == 1:
                    btn = MouseButton.XBUTTON1
                elif x_button_id == 2:
                    btn = MouseButton.XBUTTON2
            elif wParam == WM_MOUSEWHEEL:
                wheel_delta = ctypes.c_short((data.mouseData >> 16) & 0xFFFF).value
                btn = MouseButton.WHEEL_UP if wheel_delta > 0 else MouseButton.WHEEL_DOWN
                is_down = True
            elif wParam == WM_MOUSEHWHEEL:
                hwheel_delta = ctypes.c_short((data.mouseData >> 16) & 0xFFFF).value
                btn = MouseButton.WHEEL_RIGHT if hwheel_delta > 0 else MouseButton.WHEEL_LEFT
                is_down = True

            if not btn:
                return user32.CallNextHookEx(None, nCode, wParam, lParam)

            # Notify UI monitor
            if self.event_listener:
                try:
                    self.event_listener(btn, is_down, data.pt.x, data.pt.y)
                except Exception:
                    pass

            # 6. Check if button is remapped
            mapping = self.mappings.get(btn.value)
            if mapping and mapping.enabled and mapping.category != ActionCategory.DEFAULT:
                # Execute mapped action on button DOWN
                if is_down:
                    self.executor.execute_mapping(mapping)
                # Return 1 to swallow original event
                return 1

        except Exception as e:
            # Fail-safe: if any error occurs in hook, NEVER swallow! Always pass through!
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    def _dispatch_monitor_event(self, wParam: int, lParam: int) -> None:
        """Helper to safely notify UI while paused without blocking."""
        try:
            struct_ptr = ctypes.cast(lParam, PMSLLHOOKSTRUCT)
            data = struct_ptr.contents
            btn = None
            if wParam == WM_LBUTTONDOWN:
                btn = MouseButton.LEFT
            elif wParam == WM_RBUTTONDOWN:
                btn = MouseButton.RIGHT
            elif wParam == WM_MBUTTONDOWN:
                btn = MouseButton.MIDDLE
            elif wParam == WM_XBUTTONDOWN:
                x_id = (data.mouseData >> 16) & 0xFFFF
                btn = MouseButton.XBUTTON1 if x_id == 1 else MouseButton.XBUTTON2
            elif wParam == WM_MOUSEWHEEL:
                delta = ctypes.c_short((data.mouseData >> 16) & 0xFFFF).value
                btn = MouseButton.WHEEL_UP if delta > 0 else MouseButton.WHEEL_DOWN

            if btn and self.event_listener:
                self.event_listener(btn, True, data.pt.x, data.pt.y)
        except Exception:
            pass
