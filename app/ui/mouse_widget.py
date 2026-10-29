from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QRadialGradient, QLinearGradient
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QTimer
from app.core.models import MouseButton, ButtonMapping
from typing import Dict, Optional

class MouseVisualizerWidget(QWidget):
    """
    Interactive 2D Mouse Visualizer.
    - Draws an ergonomic mouse with all buttons.
    - Lets users click any part to select and remap that button.
    - Flashes in real-time when physical mouse clicks are detected.
    """

    button_clicked = Signal(MouseButton)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 360)
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
        """Called when physical mouse button click occurs."""
        self.active_press_button = button
        self._flash_timer.start(160)
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

    def _get_geometry_paths(self):
        """Define regions for mouse chassis and buttons."""
        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2

        # Chassis dimensions
        mw = 160
        mh = 270
        top = cy - mh / 2 + 10
        left = cx - mw / 2

        # Left button path
        path_left = QPainterPath()
        path_left.moveTo(cx - 5, top)
        path_left.lineTo(left + 25, top)
        path_left.quadTo(left + 5, top + 15, left + 4, top + 75)
        path_left.lineTo(cx - 5, top + 75)
        path_left.closeSubpath()

        # Right button path
        path_right = QPainterPath()
        path_right.moveTo(cx + 5, top)
        path_right.lineTo(left + mw - 25, top)
        path_right.quadTo(left + mw - 5, top + 15, left + mw - 4, top + 75)
        path_right.lineTo(cx + 5, top + 75)
        path_right.closeSubpath()

        # Wheel path
        wheel_rect = QRectF(cx - 10, top + 20, 20, 48)

        # Side button 2 (Forward / upper)
        path_side2 = QPainterPath()
        path_side2.addRoundedRect(QRectF(left - 16, cy - 40, 16, 32), 6, 6)

        # Side button 1 (Back / lower)
        path_side1 = QPainterPath()
        path_side1.addRoundedRect(QRectF(left - 16, cy + 2, 16, 34), 6, 6)

        # Body chassis path (palm rest)
        path_body = QPainterPath()
        path_body.moveTo(left + 4, top + 78)
        path_body.lineTo(left + mw - 4, top + 78)
        path_body.quadTo(left + mw + 4, cy + 50, left + mw - 15, top + mh)
        path_body.quadTo(cx, top + mh + 15, left + 15, top + mh)
        path_body.quadTo(left - 4, cy + 50, left + 4, top + 78)
        path_body.closeSubpath()

        return {
            "chassis": path_body,
            MouseButton.LEFT: path_left,
            MouseButton.RIGHT: path_right,
            MouseButton.MIDDLE: wheel_rect,
            MouseButton.XBUTTON2: path_side2,
            MouseButton.XBUTTON1: path_side1,
        }

    def _get_button_at(self, x: float, y: float) -> Optional[MouseButton]:
        paths = self._get_geometry_paths()
        pt = QPointF(x, y)

        # Check wheel first
        if paths[MouseButton.MIDDLE].contains(pt):
            return MouseButton.MIDDLE

        for btn in (MouseButton.XBUTTON1, MouseButton.XBUTTON2, MouseButton.LEFT, MouseButton.RIGHT):
            if paths[btn].contains(pt):
                return btn

        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        paths = self._get_geometry_paths()
        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2

        # 1. Draw outer soft shadow
        shadow_gradient = QRadialGradient(cx, cy + 30, 140)
        shadow_gradient.setColorAt(0, QColor(0, 0, 0, 70))
        shadow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_gradient))
        painter.drawEllipse(QRectF(cx - 100, cy - 70, 200, 250))

        # 2. Draw mouse palm rest / chassis body
        body_gradient = QLinearGradient(cx - 80, cy, cx + 80, cy + 100)
        body_gradient.setColorAt(0, QColor(38, 38, 48))
        body_gradient.setColorAt(1, QColor(25, 25, 32))
        painter.setPen(QPen(QColor(60, 60, 75), 1.5))
        painter.setBrush(QBrush(body_gradient))
        painter.drawPath(paths["chassis"])

        # Draw decorative logo glow on palm rest
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(80, 80, 105, 50))
        painter.drawEllipse(QRectF(cx - 18, cy + 45, 36, 46))
        painter.setPen(QPen(QColor(130, 130, 160, 180), 2))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(QRectF(cx - 20, cy + 55, 40, 25), Qt.AlignmentFlag.AlignCenter, "MP")

        # 3. Helper to draw interactive button
        def draw_part(button_type: MouseButton, is_rect=False):
            is_active = (self.active_press_button == button_type)
            is_selected = (self.selected_button == button_type)
            is_hovered = (self.hovered_button == button_type)

            # Colors
            if is_active:
                fill_color = QColor(52, 199, 89, 220) # Apple Green flash on press
                border_color = QColor(70, 220, 110)
            elif is_selected:
                fill_color = QColor(0, 113, 227, 210) # Apple Blue selected
                border_color = QColor(64, 169, 255)
            elif is_hovered:
                fill_color = QColor(58, 58, 72)
                border_color = QColor(100, 100, 130)
            else:
                fill_color = QColor(42, 42, 54)
                border_color = QColor(65, 65, 80)

            pen = QPen(border_color, 2.0 if (is_selected or is_active) else 1.2)
            brush = QBrush(fill_color)
            painter.setPen(pen)
            painter.setBrush(brush)

            if is_rect:
                painter.drawRoundedRect(paths[button_type], 7, 7)
                # Wheel ridges
                painter.setPen(QPen(QColor(255, 255, 255, 80), 1.5))
                rect = paths[button_type]
                y_start = rect.top() + 8
                while y_start < rect.bottom() - 6:
                    painter.drawLine(int(rect.left() + 4), int(y_start), int(rect.right() - 4), int(y_start))
                    y_start += 7
            else:
                painter.drawPath(paths[button_type])

        # Draw buttons
        draw_part(MouseButton.LEFT)
        draw_part(MouseButton.RIGHT)
        draw_part(MouseButton.MIDDLE, is_rect=True)
        draw_part(MouseButton.XBUTTON2)
        draw_part(MouseButton.XBUTTON1)

        # 4. Text labels on buttons
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        painter.setPen(QColor(240, 240, 245))
        
        # Left label
        painter.drawText(QRectF(cx - 70, cy - 85, 60, 20), Qt.AlignmentFlag.AlignCenter, "TRÁI")
        # Right label
        painter.drawText(QRectF(cx + 10, cy - 85, 60, 20), Qt.AlignmentFlag.AlignCenter, "PHẢI")

        # Side labels
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QRectF(cx - 95, cy - 35, 75, 20), Qt.AlignmentFlag.AlignRight, "Hông 2 (Fwd)")
        painter.drawText(QRectF(cx - 95, cy + 10, 75, 20), Qt.AlignmentFlag.AlignRight, "Hông 1 (Back)")
