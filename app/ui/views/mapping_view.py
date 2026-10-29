from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from app.core.models import MouseButton, ButtonMapping, ActionCategory, Profile
from app.ui.mouse_widget import MouseVisualizerWidget
from app.ui.action_dialog import ActionConfigDialog
from typing import Dict, Optional

class ButtonRowWidget(QFrame):
    """Widget representing one mouse button row in the configuration list."""
    edit_requested = Signal(MouseButton)
    toggle_requested = Signal(MouseButton, bool)

    def __init__(self, button: MouseButton, mapping: ButtonMapping, parent=None):
        super().__init__(parent)
        self.button = button
        self.mapping = mapping
        self.setProperty("class", "SubCard")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # Button icon / indicator
        icon_lbl = QLabel(self._get_button_icon(self.button))
        icon_lbl.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_lbl)

        # Button title & info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        name_lbl = QLabel(self.button.display_name)
        name_lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #ffffff;")
        info_layout.addWidget(name_lbl)

        self.action_lbl = QLabel(self.mapping.label)
        self._update_action_style()
        info_layout.addWidget(self.action_lbl)
        layout.addLayout(info_layout, stretch=1)

        # Enable / Disable toggle
        self.chk_enabled = QCheckBox("Bật")
        self.chk_enabled.setChecked(self.mapping.enabled)
        self.chk_enabled.toggled.connect(lambda v: self.toggle_requested.emit(self.button, v))
        layout.addWidget(self.chk_enabled)

        # Edit button
        btn_edit = QPushButton("Chỉnh Sửa")
        btn_edit.setStyleSheet("padding: 6px 12px; font-size: 12px;")
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.button))
        layout.addWidget(btn_edit)

    def update_mapping(self, mapping: ButtonMapping):
        self.mapping = mapping
        self.action_lbl.setText(mapping.label)
        self.chk_enabled.setChecked(mapping.enabled)
        self._update_action_style()

    def _update_action_style(self):
        cat = self.mapping.category
        if not self.mapping.enabled or cat == ActionCategory.DEFAULT:
            color = "#a1a1aa"
            bg = "#272732"
        elif cat == ActionCategory.KEYBOARD:
            color = "#58a6ff"
            bg = "#1f385c"
        elif cat == ActionCategory.MEDIA:
            color = "#bc8cff"
            bg = "#3a225c"
        elif cat == ActionCategory.MOUSE:
            color = "#3fb950"
            bg = "#1c3d28"
        elif cat == ActionCategory.DISABLED:
            color = "#f85149"
            bg = "#481d22"
        else:
            color = "#d29922"
            bg = "#3b2c1a"

        self.action_lbl.setStyleSheet(f"""
            color: {color};
            background-color: {bg};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        """)

    def _get_button_icon(self, button: MouseButton) -> str:
        icons = {
            MouseButton.LEFT: "👈",
            MouseButton.RIGHT: "👉",
            MouseButton.MIDDLE: "⚙️",
            MouseButton.XBUTTON1: "◀️",
            MouseButton.XBUTTON2: "▶️",
            MouseButton.WHEEL_UP: "🔼",
            MouseButton.WHEEL_DOWN: "🔽",
            MouseButton.WHEEL_LEFT: "⏪",
            MouseButton.WHEEL_RIGHT: "⏩",
        }
        return icons.get(button, "🖱️")

class MappingView(QWidget):
    """
    Main Mapping View:
    - Left column: Visual 2D Mouse Widget & Selected Button Detail.
    - Right column: Scrollable list of all customizable buttons.
    """
    mapping_changed = Signal(MouseButton, ButtonMapping)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_profile: Optional[Profile] = None
        self.row_widgets: Dict[str, ButtonRowWidget] = {}
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(18)

        # LEFT COLUMN: Interactive Mouse Visualizer
        left_card = QFrame()
        left_card.setProperty("class", "CardFrame")
        left_card.setFixedWidth(320)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        lbl_vis_title = QLabel("Mô Hình Trực Quan")
        lbl_vis_title.setProperty("class", "SectionHeader")
        left_layout.addWidget(lbl_vis_title)

        lbl_vis_hint = QLabel("Nhấp chuột trực tiếp lên mô hình để chọn nút:")
        lbl_vis_hint.setProperty("class", "SubtitleLabel")
        left_layout.addWidget(lbl_vis_hint)

        self.visualizer = MouseVisualizerWidget()
        self.visualizer.button_clicked.connect(self._on_visualizer_button_clicked)
        left_layout.addWidget(self.visualizer, alignment=Qt.AlignmentFlag.AlignCenter)

        # Selected button summary box
        self.box_selected = QFrame()
        self.box_selected.setProperty("class", "SubCard")
        sel_layout = QVBoxLayout(self.box_selected)
        sel_layout.setContentsMargins(10, 10, 10, 10)
        sel_layout.setSpacing(4)

        self.lbl_sel_name = QLabel("Nút đang chọn: Nút Hông 1")
        self.lbl_sel_name.setStyleSheet("font-weight: bold; color: #ffffff;")
        sel_layout.addWidget(self.lbl_sel_name)

        self.lbl_sel_act = QLabel("Chức năng: Sao chép (Ctrl + C)")
        self.lbl_sel_act.setStyleSheet("color: #0071e3;")
        sel_layout.addWidget(self.lbl_sel_act)

        self.btn_sel_edit = QPushButton("Chỉnh Sửa Nút Này")
        self.btn_sel_edit.setProperty("class", "PrimaryButton")
        self.btn_sel_edit.clicked.connect(self._edit_current_selected_button)
        sel_layout.addWidget(self.btn_sel_edit)

        left_layout.addWidget(self.box_selected)
        left_layout.addStretch()
        main_layout.addWidget(left_card)

        # RIGHT COLUMN: List of buttons
        right_card = QFrame()
        right_card.setProperty("class", "CardFrame")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(12)

        top_right = QHBoxLayout()
        lbl_list_title = QLabel("Danh Sách Các Nút & Chức Năng")
        lbl_list_title.setProperty("class", "SectionHeader")
        top_right.addWidget(lbl_list_title)
        top_right.addStretch()
        right_layout.addLayout(top_right)

        # Scroll area for rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        self.container_layout = QVBoxLayout(container)
        self.container_layout.setContentsMargins(0, 0, 8, 0)
        self.container_layout.setSpacing(8)

        # Order of buttons in UI list
        button_order = [
            MouseButton.XBUTTON1,
            MouseButton.XBUTTON2,
            MouseButton.MIDDLE,
            MouseButton.LEFT,
            MouseButton.RIGHT,
            MouseButton.WHEEL_UP,
            MouseButton.WHEEL_DOWN,
            MouseButton.WHEEL_LEFT,
            MouseButton.WHEEL_RIGHT,
        ]

        for btn in button_order:
            default_map = ButtonMapping(button=btn)
            row = ButtonRowWidget(btn, default_map)
            row.edit_requested.connect(self._open_edit_dialog)
            row.toggle_requested.connect(self._toggle_button)
            self.row_widgets[btn.value] = row
            self.container_layout.addWidget(row)

        self.container_layout.addStretch()
        scroll.setWidget(container)
        right_layout.addWidget(scroll)
        main_layout.addWidget(right_card, stretch=1)

    def load_profile(self, profile: Profile):
        self.current_profile = profile
        self.visualizer.set_mappings(profile.mappings)

        for btn in MouseButton:
            mapping = profile.mappings.get(btn.value)
            if not mapping:
                mapping = ButtonMapping(button=btn)
            if btn.value in self.row_widgets:
                self.row_widgets[btn.value].update_mapping(mapping)

        # Refresh selected info
        self._update_selected_summary()

    def flash_button(self, button: MouseButton):
        """Forward real-time physical click feedback to visualizer."""
        self.visualizer.flash_button(button)

    def _on_visualizer_button_clicked(self, button: MouseButton):
        self._update_selected_summary()

    def _update_selected_summary(self):
        btn = self.visualizer.selected_button
        if not btn:
            return
        self.lbl_sel_name.setText(f"Nút đang chọn: {btn.short_name}")
        if self.current_profile and btn.value in self.current_profile.mappings:
            m = self.current_profile.mappings[btn.value]
            self.lbl_sel_act.setText(f"Chức năng: {m.label}")
        else:
            self.lbl_sel_act.setText("Chức năng: Mặc định Windows")

    def _edit_current_selected_button(self):
        btn = self.visualizer.selected_button
        if btn:
            self._open_edit_dialog(btn)

    def _open_edit_dialog(self, button: MouseButton):
        current_map = None
        if self.current_profile and button.value in self.current_profile.mappings:
            current_map = self.current_profile.mappings[button.value]

        dlg = ActionConfigDialog(button, current_map, self)
        if dlg.exec():
            new_mapping = dlg.result_mapping
            if button.value in self.row_widgets:
                self.row_widgets[button.value].update_mapping(new_mapping)
            self.mapping_changed.emit(button, new_mapping)
            self._update_selected_summary()

    def _toggle_button(self, button: MouseButton, is_enabled: bool):
        if self.current_profile and button.value in self.current_profile.mappings:
            m = self.current_profile.mappings[button.value]
            m.enabled = is_enabled
            self.mapping_changed.emit(button, m)
