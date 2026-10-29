from PySide6.QtWidgets import QWidget
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, QFont,
    QRadialGradient, QLinearGradient, QPainterPathStroker
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QTimer
from app.core.models import MouseButton, ButtonMapping
from typing import Dict, Optional

class MouseVisualizerWidget(QWidget):
    """
    Tactile 3D Volumetric Mouse Visualizer Widget.
    Renders an ergonomic 3D mouse chassis with realistic lighting,
    specular highlights, metallic knurled scroll wheel, and extruded side thumb paddles.
    Provides interactive selection and real-time click feedback.
    """

    button_clicked = Signal(MouseButton)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 380)
        self.setMouseTracking(True)

        self.selected_button: Optional[MouseButton] = MouseButton.XBUTTON1
        self.hovered_button: Optional[MouseButton] = None
        self.active_press_button: Optional[MouseButton] = None

        self.mappings: Dict[str, ButtonMapping] = {}

        # Flash timer for live click feedback
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._reset_flash)

    def set_mappings(self, mappings: Dict[str, ButtonMapping]):
        self.mappings = mappings
        self.update()

    def set_selected_button(self, button: MouseButton):
        self.selected_button = button
        self.update()

    def flash_button(self, button: MouseButton):
        """Triggered when a physical mouse button press is intercepted."""
        self.active_press_button = button
        self._flash_timer.start(180)
        self.update()

    def _reset_flash(self):
        self.active_press_button = None
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position()
        old_hover = self.hovered_button
        self.hovered_button = self._get_button_at(pos.x(), pos.y())
        if self.hovered_button != old_hover:
            self.update()

    def mousePressEvent(self, event):
        pos = event.position()
        btn = self._get_button_at(pos.x(), pos.y())
        if btn:
            self.selected_button = btn
            self.button_clicked.emit(btn)
            self.update()

    def _get_geometry(self):
        """Computes coordinates and vector paths for all 3D mouse components."""
        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # Ergonomic 3D Mouse Dimensions
        mw = 156.0
        mh = 265.0
        top = cy - mh / 2.0 + 12.0
        left = cx - mw / 2.0

        # Primary Left Button Path (ergonomic finger contour)
        p_left = QPainterPath()
        p_left.moveTo(cx - 3.5, top + 6.0)
        p_left.lineTo(left + 26.0, top)
        p_left.quadTo(left + 8.0, top + 14.0, left + 6.0, top + 80.0)
        p_left.lineTo(cx - 3.5, top + 80.0)
        p_left.closeSubpath()

        # Primary Right Button Path
        p_right = QPainterPath()
        p_right.moveTo(cx + 3.5, top + 6.0)
        p_right.lineTo(left + mw - 26.0, top)
        p_right.quadTo(left + mw - 8.0, top + 14.0, left + mw - 6.0, top + 80.0)
        p_right.lineTo(cx + 3.5, top + 80.0)
        p_right.closeSubpath()

        # 3D Recessed Scroll Wheel Well
        well_rect = QRectF(cx - 12.0, top + 16.0, 24.0, 52.0)
        # 3D Metallic Knurled Scroll Wheel
        wheel_rect = QRectF(cx - 8.5, top + 20.0, 17.0, 44.0)

        # 3D Sculpted Side Buttons (Extruded left thumb wing)
        # Forward Button (XButton2 - Upper)
        p_side2 = QPainterPath()
        p_side2.moveTo(left - 4.0, cy - 38.0)
        p_side2.lineTo(left - 20.0, cy - 30.0)
        p_side2.quadTo(left - 22.0, cy - 14.0, left - 18.0, cy - 8.0)
        p_side2.lineTo(left - 3.0, cy - 14.0)
        p_side2.closeSubpath()

        # Back Button (XButton1 - Lower)
        p_side1 = QPainterPath()
        p_side1.moveTo(left - 3.0, cy - 10.0)
        p_side1.lineTo(left - 18.0, cy - 5.0)
        p_side1.quadTo(left - 21.0, cy + 15.0, left - 15.0, cy + 28.0)
        p_side1.lineTo(left - 2.0, cy + 18.0)
        p_side1.closeSubpath()

        # 3D Palm Rest / Chassis Lower Body
        p_palm = QPainterPath()
        p_palm.moveTo(left + 6.0, top + 82.0)
        p_palm.lineTo(left + mw - 6.0, top + 82.0)
        p_palm.quadTo(left + mw + 10.0, cy + 45.0, left + mw - 14.0, top + mh)
        p_palm.quadTo(cx, top + mh + 16.0, left + 14.0, top + mh)
        p_palm.quadTo(left - 10.0, cy + 45.0, left + 6.0, top + 82.0)
        p_palm.closeSubpath()

        # Full Underbelly Shadow Path
        p_base = QPainterPath()
        p_base.moveTo(left + 22.0, top - 2.0)
        p_base.lineTo(left + mw - 22.0, top - 2.0)
        p_base.quadTo(left + mw + 14.0, cy + 45.0, left + mw - 12.0, top + mh + 4.0)
        p_base.quadTo(cx, top + mh + 22.0, left + 12.0, top + mh + 4.0)
        p_base.quadTo(left - 24.0, cy + 45.0, left + 22.0, top - 2.0)
        p_base.closeSubpath()

        return {
            "geo_cx": cx, "geo_cy": cy, "geo_top": top, "geo_left": left, "geo_mw": mw, "geo_mh": mh,
            "base": p_base,
            "palm": p_palm,
            "well": well_rect,
            MouseButton.LEFT: p_left,
            MouseButton.RIGHT: p_right,
            MouseButton.MIDDLE: wheel_rect,
            MouseButton.XBUTTON2: p_side2,
            MouseButton.XBUTTON1: p_side1,
        }

    def _get_button_at(self, x: float, y: float) -> Optional[MouseButton]:
        g = self._get_geometry()
        pt = QPointF(x, y)

        if g[MouseButton.MIDDLE].contains(pt):
            return MouseButton.MIDDLE

        for btn in (MouseButton.XBUTTON2, MouseButton.XBUTTON1, MouseButton.LEFT, MouseButton.RIGHT):
            if g[btn].contains(pt):
                return btn

        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        g = self._get_geometry()
        cx, cy = g["geo_cx"], g["geo_cy"]
        top, left = g["geo_top"], g["geo_left"]
        mw, mh = g["geo_mw"], g["geo_mh"]

        # ==========================================
        # 1. AMBIENT 3D CONTACT & DROP SHADOWS
        # ==========================================
        # Ambient diffuse floor shadow
        diffuse_grad = QRadialGradient(cx, cy + 55.0, 160.0)
        diffuse_grad.setColorAt(0.0, QColor(0, 0, 0, 130))
        diffuse_grad.setColorAt(0.6, QColor(0, 0, 0, 65))
        diffuse_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(diffuse_grad))
        painter.drawEllipse(QRectF(cx - 120.0, cy - 60.0, 240.0, 270.0))

        # Sharp bottom contact shadow (gives grounding depth)
        contact_grad = QRadialGradient(cx, top + mh + 2.0, 75.0)
        contact_grad.setColorAt(0.0, QColor(0, 0, 0, 170))
        contact_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(contact_grad))
        painter.drawEllipse(QRectF(cx - 75.0, top + mh - 12.0, 150.0, 36.0))

        # ==========================================
        # 2. UNDERBELLY SKIRT / 3D CHAMFER BASE
        # ==========================================
        skirt_grad = QLinearGradient(left, top, left + mw, top + mh)
        skirt_grad.setColorAt(0.0, QColor(22, 22, 28))
        skirt_grad.setColorAt(1.0, QColor(10, 10, 14))
        painter.setPen(QPen(QColor(45, 45, 58), 1.5))
        painter.setBrush(QBrush(skirt_grad))
        painter.drawPath(g["base"])

        # ==========================================
        # 3. 3D PALM REST DOME (Volumetric Curvature)
        # ==========================================
        palm_grad = QRadialGradient(cx + 8.0, cy + 50.0, 135.0)
        palm_grad.setColorAt(0.0, QColor(48, 50, 64))     # Specular crown highlight
        palm_grad.setColorAt(0.45, QColor(32, 33, 42))    # Mid-body obsidian plastic
        palm_grad.setColorAt(0.85, QColor(20, 20, 27))    # Fall-off ambient shadow
        palm_grad.setColorAt(1.0, QColor(14, 14, 18))     # Edge bevel

        painter.setPen(QPen(QColor(60, 63, 78), 1.2))
        painter.setBrush(QBrush(palm_grad))
        painter.drawPath(g["palm"])

        # Specular sheen arc along top dome of palm rest
        sheen_path = QPainterPath()
        sheen_path.moveTo(left + 24.0, cy + 30.0)
        sheen_path.quadTo(cx, cy + 22.0, left + mw - 24.0, cy + 30.0)
        sheen_path.quadTo(cx, cy + 26.0, left + 24.0, cy + 30.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.drawPath(sheen_path)

        # 3D Backlit Brand Emblem / LED (MousePilot "MP")
        emblem_rect = QRectF(cx - 20.0, top + mh - 58.0, 40.0, 26.0)
        # Glow halo
        led_glow = QRadialGradient(cx, top + mh - 45.0, 32.0)
        led_glow.setColorAt(0.0, QColor(0, 113, 227, 80))
        led_glow.setColorAt(1.0, QColor(0, 113, 227, 0))
        painter.setBrush(QBrush(led_glow))
        painter.drawEllipse(QRectF(cx - 32.0, top + mh - 77.0, 64.0, 64.0))

        # Emblem Core
        painter.setPen(QPen(QColor(70, 140, 240, 210), 1.5))
        painter.setBrush(QColor(16, 24, 38, 200))
        painter.drawRoundedRect(emblem_rect, 6.0, 6.0)
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(QColor(220, 235, 255, 230))
        painter.drawText(emblem_rect, Qt.AlignmentFlag.AlignCenter, "MP")

        # ==========================================
        # 4. RECESSED SCROLL WHEEL WELL (Deep Trench)
        # ==========================================
        well_rect = g["well"]
        well_grad = QLinearGradient(well_rect.left(), well_rect.top(), well_rect.right(), well_rect.top())
        well_grad.setColorAt(0.0, QColor(8, 8, 12))
        well_grad.setColorAt(0.5, QColor(15, 15, 20))
        well_grad.setColorAt(1.0, QColor(8, 8, 12))
        painter.setPen(QPen(QColor(30, 30, 40), 1.2))
        painter.setBrush(QBrush(well_grad))
        painter.drawRoundedRect(well_rect, 8.0, 8.0)

        # ==========================================
        # 5. BUTTON RENDERER (Primary & Side Buttons)
        # ==========================================
        def draw_button(btn: MouseButton, path: QPainterPath):
            is_active = (self.active_press_button == btn)
            is_selected = (self.selected_button == btn)
            is_hovered = (self.hovered_button == btn)

            # 3D Lighting Gradients based on State
            bbox = path.boundingRect()
            top_light = bbox.top()
            bot_dark = bbox.bottom()

            btn_grad = QLinearGradient(bbox.center().x(), top_light, bbox.center().x(), bot_dark)

            if is_active:
                # Active Press: Emerald Neon Glow
                btn_grad.setColorAt(0.0, QColor(64, 220, 115))
                btn_grad.setColorAt(1.0, QColor(25, 140, 65))
                edge_pen = QPen(QColor(120, 255, 160), 2.0)
                glow_color = QColor(48, 209, 88, 130)
            elif is_selected:
                # Selected: Apple Electric Blue 3D Metallic
                btn_grad.setColorAt(0.0, QColor(0, 145, 255))
                btn_grad.setColorAt(0.5, QColor(0, 113, 227))
                btn_grad.setColorAt(1.0, QColor(0, 85, 185))
                edge_pen = QPen(QColor(120, 200, 255), 2.0)
                glow_color = QColor(0, 113, 227, 120)
            elif is_hovered:
                # Hovered: Illuminated dark slate with specular edge
                btn_grad.setColorAt(0.0, QColor(68, 71, 90))
                btn_grad.setColorAt(0.6, QColor(48, 51, 65))
                btn_grad.setColorAt(1.0, QColor(36, 38, 48))
                edge_pen = QPen(QColor(130, 135, 160), 1.6)
                glow_color = QColor(120, 140, 180, 50)
            else:
                # Normal State: Deep ergonomic sculpted plastic
                btn_grad.setColorAt(0.0, QColor(50, 52, 66))
                btn_grad.setColorAt(0.5, QColor(38, 40, 52))
                btn_grad.setColorAt(1.0, QColor(26, 27, 35))
                edge_pen = QPen(QColor(65, 68, 84), 1.2)
                glow_color = None

            # Render Volumetric Selection/Press Glow
            if glow_color:
                stroker = QPainterPathStroker()
                stroker.setWidth(8.0)
                stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                glow_path = stroker.createStroke(path)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(glow_color)
                painter.drawPath(glow_path)

            # Draw 3D Button Body
            painter.setPen(edge_pen)
            painter.setBrush(QBrush(btn_grad))
            painter.drawPath(path)

            # Top Specular Chiseled Rim Highlight
            if not is_active and not is_selected:
                rim_path = QPainterPath()
                rim_path.moveTo(bbox.left() + 4.0, top_light + 2.0)
                rim_path.lineTo(bbox.right() - 4.0, top_light + 2.0)
                painter.setPen(QPen(QColor(255, 255, 255, 45), 1.2))
                painter.drawPath(rim_path)

        # Draw Left & Right Primary 3D Click Buttons
        draw_button(MouseButton.LEFT, g[MouseButton.LEFT])
        draw_button(MouseButton.RIGHT, g[MouseButton.RIGHT])

        # Draw Sculpted 3D Side Thumb Paddles (Extruded)
        draw_button(MouseButton.XBUTTON2, g[MouseButton.XBUTTON2])
        draw_button(MouseButton.XBUTTON1, g[MouseButton.XBUTTON1])

        # ==========================================
        # 6. 3D METALLIC KNURLED SCROLL WHEEL
        # ==========================================
        wr = g[MouseButton.MIDDLE]
        is_wheel_active = (self.active_press_button == MouseButton.MIDDLE)
        is_wheel_sel = (self.selected_button == MouseButton.MIDDLE)
        is_wheel_hov = (self.hovered_button == MouseButton.MIDDLE)

        # Drop shadow inside the well behind the wheel
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 110))
        painter.drawRoundedRect(wr.adjusted(1.0, 2.0, 1.0, 2.0), 5.0, 5.0)

        # Cylindrical Metallic Gradient (Left-to-Right specular lighting)
        wheel_cyl = QLinearGradient(wr.left(), wr.top(), wr.right(), wr.top())
        if is_wheel_active:
            wheel_cyl.setColorAt(0.0, QColor(25, 140, 65))
            wheel_cyl.setColorAt(0.45, QColor(100, 240, 140))
            wheel_cyl.setColorAt(0.65, QColor(64, 220, 115))
            wheel_cyl.setColorAt(1.0, QColor(20, 110, 50))
            wheel_border = QColor(120, 255, 160)
        elif is_wheel_sel:
            wheel_cyl.setColorAt(0.0, QColor(0, 75, 170))
            wheel_cyl.setColorAt(0.45, QColor(120, 200, 255))
            wheel_cyl.setColorAt(0.65, QColor(0, 130, 245))
            wheel_cyl.setColorAt(1.0, QColor(0, 60, 145))
            wheel_border = QColor(140, 210, 255)
        elif is_wheel_hov:
            wheel_cyl.setColorAt(0.0, QColor(45, 48, 60))
            wheel_cyl.setColorAt(0.45, QColor(120, 125, 150))
            wheel_cyl.setColorAt(0.65, QColor(85, 90, 110))
            wheel_cyl.setColorAt(1.0, QColor(35, 38, 48))
            wheel_border = QColor(140, 145, 170)
        else:
            wheel_cyl.setColorAt(0.0, QColor(30, 32, 40))
            wheel_cyl.setColorAt(0.45, QColor(95, 100, 120))  # Specular highlight core
            wheel_cyl.setColorAt(0.65, QColor(65, 68, 82))
            wheel_cyl.setColorAt(1.0, QColor(22, 24, 30))
            wheel_border = QColor(50, 53, 66)

        painter.setPen(QPen(wheel_border, 1.5))
        painter.setBrush(QBrush(wheel_cyl))
        painter.drawRoundedRect(wr, 6.0, 6.0)

        # 3D Knurled Grip Ribs (horizontal tactile ridges)
        y_rib = wr.top() + 6.0
        while y_rib < wr.bottom() - 4.0:
            # Highlight ridge
            painter.setPen(QPen(QColor(255, 255, 255, 85 if not is_wheel_sel else 140), 1.0))
            painter.drawLine(int(wr.left() + 2.5), int(y_rib), int(wr.right() - 2.5), int(y_rib))
            # Groove shadow beneath ridge
            painter.setPen(QPen(QColor(0, 0, 0, 90), 1.0))
            painter.drawLine(int(wr.left() + 2.5), int(y_rib + 1.2), int(wr.right() - 2.5), int(y_rib + 1.2))
            y_rib += 6.5

        # ==========================================
        # 7. HIGH-FIDELITY LABELS & CALLOUTS
        # ==========================================
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        # Left Click Label
        painter.setPen(QColor(220, 225, 235))
        painter.drawText(QRectF(cx - 72.0, top + 34.0, 56.0, 20.0), Qt.AlignmentFlag.AlignCenter, "TRÁI")

        # Right Click Label
        painter.drawText(QRectF(cx + 16.0, top + 34.0, 56.0, 20.0), Qt.AlignmentFlag.AlignCenter, "PHẢI")

        # Side Button Callout Badges
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        painter.setPen(QColor(170, 180, 200))

        # Fwd Callout
        fwd_rect = QRectF(left - 96.0, cy - 36.0, 72.0, 20.0)
        painter.drawText(fwd_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "Hông 2 (Fwd)")

        # Back Callout
        back_rect = QRectF(left - 96.0, cy + 4.0, 72.0, 20.0)
        painter.drawText(back_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "Hông 1 (Back)")

        # Middle Wheel Callout
        mid_rect = QRectF(cx - 40.0, top - 3.0, 80.0, 16.0)
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QColor(140, 190, 255) if is_wheel_sel else QColor(140, 145, 160))
        painter.drawText(mid_rect, Qt.AlignmentFlag.AlignCenter, "CUỘN / GIỮA")
