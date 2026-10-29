from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDateTime, QTimer
from app.core.models import MouseButton, ButtonMapping
from typing import Dict, Optional

class LiveClickPad(QFrame):
    """Visual feedback target area for users to click and test buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(110)
        self.setStyleSheet("""
            background-color: #202028;
            border: 2px dashed #404050;
            border-radius: 12px;
        """)
        self._setup_ui()

        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(self._reset_display)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_main = QLabel("🎯 BẤM BẤT KỲ NÚT CHUỘT NÀO ĐỂ THỬ NGHIỆM")
        self.lbl_main.setStyleSheet("font-size: 16px; font-weight: bold; color: #a1a1aa;")
        layout.addWidget(self.lbl_main, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl_sub = QLabel("Hệ thống sẽ bắt tín hiệu phần cứng và hiển thị trạng thái can thiệp ngay lập tức.")
        self.lbl_sub.setStyleSheet("font-size: 12px; color: #71717a;")
        layout.addWidget(self.lbl_sub, alignment=Qt.AlignmentFlag.AlignCenter)

    def trigger_event(self, button: MouseButton, is_down: bool, x: int, y: int, action_label: str):
        state_str = "NHẤN XUỐNG (DOWN)" if is_down else "THẢ RA (UP)"
        self.lbl_main.setText(f"🔥 {button.display_name} — {state_str}")
        self.lbl_sub.setText(f"Tọa độ: ({x}, {y}) | Chức năng gán: {action_label}")

        self.setStyleSheet("""
            background-color: #1e3a29;
            border: 2px solid #34c759;
            border-radius: 12px;
        """)
        self.lbl_main.setStyleSheet("font-size: 16px; font-weight: bold; color: #34c759;")

        self._reset_timer.start(350)

    def _reset_display(self):
        self.setStyleSheet("""
            background-color: #202028;
            border: 2px dashed #404050;
            border-radius: 12px;
        """)
        self.lbl_main.setStyleSheet("font-size: 16px; font-weight: bold; color: #a1a1aa;")
        self.lbl_main.setText("🎯 BẤM BẤT KỲ NÚT CHUỘT NÀO ĐỂ THỬ NGHIỆM")
        self.lbl_sub.setText("Hệ thống sẽ bắt tín hiệu phần cứng và hiển thị trạng thái can thiệp ngay lập tức.")

class LiveMonitorView(QWidget):
    """View showing live mouse events and event inspection log."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_count = 0
        self.current_mappings: Dict[str, ButtonMapping] = {}
        self._setup_ui()

    def set_mappings(self, mappings: Dict[str, ButtonMapping]):
        self.current_mappings = mappings

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("Kiểm Tra Tín Hiệu Chuột Trực Tiếp")
        lbl_title.setProperty("class", "TitleLabel")
        title_box.addWidget(lbl_title)

        lbl_sub = QLabel("Theo dõi thời gian thực các sự kiện chuột được chặn hoặc thực thi qua hook.")
        lbl_sub.setProperty("class", "SubtitleLabel")
        title_box.addWidget(lbl_sub)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.btn_clear = QPushButton("🗑️ Xóa Nhật Ký")
        self.btn_clear.clicked.connect(self.clear_log)
        top_bar.addWidget(self.btn_clear)
        main_layout.addLayout(top_bar)

        # Visual Test Pad
        self.click_pad = LiveClickPad()
        main_layout.addWidget(self.click_pad)

        # Table of events
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Thời Gian", "Nút Chuột", "Trạng Thái", "Tọa Độ (X, Y)", "Hành Động Ánh Xạ"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table)

    def on_mouse_event(self, button: MouseButton, is_down: bool, x: int, y: int):
        self.event_count += 1
        time_str = QDateTime.currentDateTime().toString("HH:mm:ss.zzz")
        mapping = self.current_mappings.get(button.value)
        action_label = mapping.label if (mapping and mapping.enabled) else "Mặc định hệ thống"

        # Update visual pad
        self.click_pad.trigger_event(button, is_down, x, y, action_label)

        # Insert table row at top
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem(time_str))
        self.table.setItem(0, 1, QTableWidgetItem(button.short_name))
        self.table.setItem(0, 2, QTableWidgetItem("Nhấn (Down)" if is_down else "Thả (Up)"))
        self.table.setItem(0, 3, QTableWidgetItem(f"{x}, {y}"))
        self.table.setItem(0, 4, QTableWidgetItem(action_label))

        # Keep max 100 rows
        if self.table.rowCount() > 100:
            self.table.removeRow(self.table.rowCount() - 1)

    def clear_log(self):
        self.table.setRowCount(0)
        self.event_count = 0
