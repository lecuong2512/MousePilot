from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox, QInputDialog, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from app.core.models import Profile, ButtonMapping, MouseButton, ActionCategory
from app.core.config_manager import ConfigManager
import json
import uuid
from typing import Dict

class ProfileCard(QFrame):
    """Card representing one configuration profile."""
    activate_clicked = Signal(str)
    delete_clicked = Signal(str)

    def __init__(self, profile: Profile, is_current: bool, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.is_current = is_current
        self.setProperty("class", "SubCard")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Header
        top = QHBoxLayout()
        icon = "🌟" if self.is_current else "📁"
        lbl_name = QLabel(f"{icon} {self.profile.name}")
        lbl_name.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        top.addWidget(lbl_name, stretch=1)

        if self.is_current:
            lbl_badge = QLabel("● ĐANG SỬ DỤNG")
            lbl_badge.setStyleSheet("color: #34c759; font-weight: bold; font-size: 11px;")
            top.addWidget(lbl_badge)
        else:
            btn_act = QPushButton("Kích Hoạt")
            btn_act.setProperty("class", "PrimaryButton")
            btn_act.clicked.connect(lambda: self.activate_clicked.emit(self.profile.id))
            top.addWidget(btn_act)

            if self.profile.id not in ("default", "office", "media", "developer"):
                btn_del = QPushButton("Xóa")
                btn_del.setProperty("class", "DangerButton")
                btn_del.clicked.connect(lambda: self.delete_clicked.emit(self.profile.id))
                top.addWidget(btn_del)

        layout.addLayout(top)

        # Description
        lbl_desc = QLabel(self.profile.description or "Chưa có mô tả.")
        lbl_desc.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        # Key mappings summary preview
        summary_tags = []
        for btn in (MouseButton.XBUTTON1, MouseButton.XBUTTON2, MouseButton.MIDDLE):
            if btn.value in self.profile.mappings:
                m = self.profile.mappings[btn.value]
                if m.enabled and m.category != ActionCategory.DEFAULT:
                    summary_tags.append(f"{btn.short_name}: {m.label}")

        if summary_tags:
            lbl_tags = QLabel("  |  ".join(summary_tags))
            lbl_tags.setStyleSheet("color: #58a6ff; font-size: 11px; font-weight: 500;")
            layout.addWidget(lbl_tags)

class ProfilesView(QWidget):
    """View to manage, create, export, and switch mouse button profiles."""
    profile_activated = Signal(str)

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._setup_ui()
        self.refresh_profiles()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header with action buttons
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("Hồ Sơ Cấu Hình (Profiles)")
        lbl_title.setProperty("class", "TitleLabel")
        title_box.addWidget(lbl_title)

        lbl_sub = QLabel("Chuyển đổi nhanh giữa các chế độ làm việc, văn phòng, giải trí hoặc gaming.")
        lbl_sub.setProperty("class", "SubtitleLabel")
        title_box.addWidget(lbl_sub)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        btn_new = QPushButton("➕ Tạo Hồ Sơ Mới")
        btn_new.setProperty("class", "PrimaryButton")
        btn_new.clicked.connect(self._create_new_profile)
        top_bar.addWidget(btn_new)

        btn_export = QPushButton("📤 Xuất JSON")
        btn_export.clicked.connect(self._export_profiles)
        top_bar.addWidget(btn_export)

        btn_import = QPushButton("📥 Nhập JSON")
        btn_import.clicked.connect(self._import_profiles)
        top_bar.addWidget(btn_import)

        main_layout.addLayout(top_bar)

        # Scroll area for profile cards
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

    def refresh_profiles(self):
        while self.cards_layout.count() > 0:
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        active_id = self.config_manager.active_profile_id
        for pid, profile in self.config_manager.profiles.items():
            is_active = (pid == active_id)
            card = ProfileCard(profile, is_active)
            card.activate_clicked.connect(self._activate_profile)
            card.delete_clicked.connect(self._delete_profile)
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _activate_profile(self, profile_id: str):
        self.config_manager.set_active_profile(profile_id)
        self.refresh_profiles()
        self.profile_activated.emit(profile_id)

    def _delete_profile(self, profile_id: str):
        ret = QMessageBox.question(
            self, "Xác nhận xóa", f"Bạn có chắc muốn xóa hồ sơ '{profile_id}' không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            if profile_id in self.config_manager.profiles:
                del self.config_manager.profiles[profile_id]
                self.config_manager.save()
                self.refresh_profiles()

    def _create_new_profile(self):
        name, ok = QInputDialog.getText(self, "Tạo Hồ Sơ Mới", "Nhập tên hồ sơ (VD: Photoshop, Valorant, Excel):")
        if ok and name.strip():
            new_id = f"custom_{uuid.uuid4().hex[:6]}"
            # Copy from default
            active_prof = self.config_manager.get_active_profile()
            new_mappings = {k: ButtonMapping.from_dict(v.to_dict()) for k, v in active_prof.mappings.items()}
            new_profile = Profile(
                id=new_id,
                name=name.strip(),
                description=f"Hồ sơ tùy chỉnh {name.strip()}",
                is_active=False,
                mappings=new_mappings,
            )
            self.config_manager.profiles[new_id] = new_profile
            self.config_manager.save()
            self.refresh_profiles()
            self._activate_profile(new_id)

    def _export_profiles(self):
        path, _ = QFileDialog.getSaveFileName(self, "Xuất Hồ Sơ", "mouse_profiles.json", "JSON (*.json)")
        if path:
            try:
                data = {pid: p.to_dict() for pid, p in self.config_manager.profiles.items()}
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "Thành công", "Đã xuất hồ sơ ra file thành công!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xuất file: {e}")

    def _import_profiles(self):
        path, _ = QFileDialog.getOpenFileName(self, "Nhập Hồ Sơ", "", "JSON (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for pid, pdata in data.items():
                    self.config_manager.profiles[pid] = Profile.from_dict(pdata)
                self.config_manager.save()
                self.refresh_profiles()
                QMessageBox.information(self, "Thành công", "Đã nhập thêm hồ sơ thành công!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"File không đúng định dạng: {e}")
