import re
from typing import List, Optional
from app.core.models import MouseDevice

# Known hardware vendors dictionary
KNOWN_VENDORS = {
    "1EA7": "Sharkoon / 2.4G Optical Wireless",
    "046D": "Logitech",
    "1532": "Razer",
    "045E": "Microsoft",
    "1038": "SteelSeries",
    "1B1C": "Corsair",
    "258A": "SinoWealth / Darmoshark / Machenike",
    "09DA": "A4Tech / Bloody",
    "2717": "Xiaomi",
    "04F2": "Chicony",
    "06CB": "Synaptics Precision Touchpad",
    "0488": "Cirque",
    "044E": "Alps Alpine",
    "0B05": "ASUS ROG",
    "17EF": "Lenovo",
    "03F0": "HP",
    "413C": "Dell",
}

def parse_device_id(device_id: str) -> dict:
    """Extract VID, PID, and hardware tags from Windows Device ID string."""
    info = {
        "vid": None,
        "pid": None,
        "is_touchpad": False,
        "connection_type": "USB",
    }
    
    vid_match = re.search(r"VID_([0-9A-Fa-f]{4})", device_id, re.IGNORECASE)
    if vid_match:
        info["vid"] = vid_match.group(1).upper()

    pid_match = re.search(r"PID_([0-9A-Fa-f]{4})", device_id, re.IGNORECASE)
    if pid_match:
        info["pid"] = pid_match.group(1).upper()

    dev_upper = device_id.upper()
    if "DELL" in dev_upper or "SYN" in dev_upper or "ALPS" in dev_upper or "TOUCHPAD" in dev_upper or "ELAN" in dev_upper:
        info["is_touchpad"] = True
        info["connection_type"] = "Bàn di chuột tích hợp (Internal Touchpad)"
    elif "BTH" in dev_upper or "BLUETOOTH" in dev_upper:
        info["connection_type"] = "Bluetooth Wireless"
    elif info["vid"] in ("1EA7", "258A") or "WIRELESS" in dev_upper:
        info["connection_type"] = "Không dây (2.4G Wireless Dongle)"
    else:
        info["connection_type"] = "Cáp USB (Wired USB)"

    return info

def get_connected_mice() -> List[MouseDevice]:
    """Enumerate all connected pointing devices using WMI/COM."""
    devices: List[MouseDevice] = []
    seen_ids = set()

    try:
        import win32com.client
        wmi = win32com.client.GetObject("winmgmts:")
        query_res = wmi.ExecQuery("Select * from Win32_PointingDevice")

        for item in query_res:
            dev_id = getattr(item, "DeviceID", "") or ""
            if not dev_id or dev_id in seen_ids:
                continue
            seen_ids.add(dev_id)

            parsed = parse_device_id(dev_id)
            raw_name = getattr(item, "Name", "HID-compliant mouse")
            mfg = getattr(item, "Manufacturer", "Generic")
            status = getattr(item, "Status", "OK")
            num_buttons = getattr(item, "NumberOfButtons", 5) or 5

            # Construct friendly name
            friendly = raw_name
            vendor_name = KNOWN_VENDORS.get(parsed["vid"]) if parsed["vid"] else None
            
            if parsed["is_touchpad"]:
                friendly = "Dell Precision Touchpad (Bàn rê cảm ứng)"
            elif vendor_name:
                friendly = f"Chuột {vendor_name} ({parsed['connection_type']})"
            elif parsed["vid"] and parsed["pid"]:
                friendly = f"Chuột HID USB (VID_{parsed['vid']}&PID_{parsed['pid']})"

            devices.append(MouseDevice(
                device_id=dev_id,
                name=raw_name,
                friendly_name=friendly,
                manufacturer=vendor_name or mfg,
                hardware_id=f"VID_{parsed['vid']}&PID_{parsed['pid']}" if parsed["vid"] else dev_id,
                status=status,
                is_touchpad=parsed["is_touchpad"],
                connection_type=parsed["connection_type"],
                button_count=num_buttons if num_buttons > 0 else 5,
            ))
    except Exception as e:
        # Fallback if WMI fails
        devices.append(MouseDevice(
            device_id="DEFAULT_FALLBACK_MOUSE",
            name="Standard Windows Mouse",
            friendly_name="Chuột Tiêu Chuẩn (Windows Pointing Device)",
            manufacturer="Standard HID",
            hardware_id="GENERIC_MOUSE",
            status="OK",
            is_touchpad=False,
            connection_type="USB / Wireless",
            button_count=5,
        ))

    return devices
