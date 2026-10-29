from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
from app.core.devices import get_connected_mice
from app.core.models import MouseDevice
from typing import List, Optional

class DeviceScannerWorker(QThread):
    """Background worker to query WMI/SetupAPI without freezing the GUI."""
    devices_loaded = Signal(list)

    def run(self):
        try:
            devs = get_connected_mice()
            self.devices_loaded.emit(devs)
        except Exception:
            self.devices_loaded.emit([])

class DeviceCard(QFrame):
    """Card showing hardware info for a connected mouse or touchpad."""

    def __init__(self, device: MouseDevice, parent=None):
        super().__init__(parent)
        self.device = device
        self.setProperty("class", "SubCard")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Header: Icon + Friendly Name + Status badge
        top_layout = QHBoxLayout()
        icon_str = "🖱️" if not self.device.is_touchpad else "💻"
        lbl_icon = QLabel(icon_str)
        lbl_icon.setStyleSheet("font-size: 20px;")
        top_layout.addWidget(lbl_icon)

        lbl_name = QLabel(self.device.friendly_name)
        lbl_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        top_layout.addWidget(lbl_name, stretch=1)

        lbl_status = QLabel("● ĐANG KẾT NỐI")
        lbl_status.setStyleSheet("color: #34c759; font-weight: 600; font-size: 11px;")
        top_layout.addWidget(lbl_status)
        layout.addLayout(top_layout)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #383848; max-height: 1px;")
        layout.addWidget(sep)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(4)

        def add_info_row(row: int, title: str, value: str):
            lbl_t = QLabel(title)
            lbl_t.setStyleSheet("color: #a1a1aa; font-size: 12px;")
            lbl_v = QLabel(value)
            lbl_v.setStyleSheet("color: #ffffff; font-weight: 500; font-size: 12px;")
            grid.addWidget(lbl_t, row, 0)
            grid.addWidget(lbl_v, row, 1)

        add_info_row(0, "Chuẩn kết nối:", self.device.connection_type)
        add_info_row(1, "Nhà sản xuất / Chipset:", self.device.manufacturer)
        add_info_row(2, "Mã phần cứng (Hardware ID):", self.device.hardware_id)
        add_info_row(3, "Tên Windows PNP:", self.device.name)
        add_info_row(4, "Số nút chuẩn hỗ trợ:", f"{self.device.button_count} nút chính + cuộn")

        layout.addLayout(grid)

class DevicesView(QWidget):
    """View to list and refresh all connected physical mouse devices non-blockingly."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[DeviceScannerWorker] = None
        self._setup_ui()
        # Defer scan slightly so UI shows instantly
        self.refresh_devices()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Title and refresh button
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("Thiết Bị Chuột Đang Kết Nối")
        lbl_title.setProperty("class", "TitleLabel")
        title_box.addWidget(lbl_title)

        lbl_sub = QLabel("Danh sách các chuột vật lý và bàn rê cảm ứng được phát hiện trên máy tính.")
        lbl_sub.setProperty("class", "SubtitleLabel")
        title_box.addWidget(lbl_sub)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.btn_refresh = QPushButton("🔄 Quét Lại Thiết Bị")
        self.btn_refresh.setProperty("class", "PrimaryButton")
        self.btn_refresh.clicked.connect(self.refresh_devices)
        top_bar.addWidget(self.btn_refresh)
        main_layout.addLayout(top_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #0071e3; }")
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # Scroll area for device cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)

        scroll.setWidget(self.cards_container)
        main_layout.addWidget(scroll)

    def refresh_devices(self):
        if self.worker and self.worker.isRunning():
            return

        self.btn_refresh.setEnabled(False)
        self.progress_bar.show()

        self.worker = DeviceScannerWorker()
        self.worker.devices_loaded.connect(self._on_devices_loaded)
        self.worker.start()

    def _on_devices_loaded(self, devices: List[MouseDevice]):
        self.progress_bar.hide()
        self.btn_refresh.setEnabled(True)

        while self.cards_layout.count() > 0:
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not devices:
            empty_lbl = QLabel("Không tìm thấy thiết bị chuột nào. Hãy kiểm tra lại kết nối USB/Bluetooth.")
            empty_lbl.setStyleSheet("color: #a1a1aa; padding: 20px; font-size: 14px;")
            self.cards_layout.addWidget(empty_lbl)
        else:
            for dev in devices:
                card = DeviceCard(dev)
                self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()
