#!/usr/bin/env python3
"""
Vitreos Core UI Components
Reusable widgets and UI elements for the Vitreos application.
"""
from typing import Optional, Deque, List
from collections import deque

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient, QFont, QPaintEvent


class SparklineWidget(QWidget):
    """A compact widget for rendering sparkline graphs."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(40)
        self.data: Deque[float] = deque(maxlen=60)

    def add_point(self, value: float) -> None:
        """Add a new data point and refresh the graph."""
        self.data.append(value)
        self.update()

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Render segmented LED progress bar with ghost background."""
        if not self.data:
            return
        painter = QPainter(self)
        rect = self.rect()
        percentage = self.data[-1] / 100.0 if self.data else 0.0
        
        value = self.data[-1]
        active_color = QColor("#ff8c00") if value > 70 else QColor("#bc13fe")
        ghost_color = QColor(188, 19, 254, 26)
        
        painter.setPen(Qt.PenStyle.NoPen)
        
        segment_width = 2
        gap = 1
        step = segment_width + gap
        fill_width = int(rect.width() * percentage)
        
        for x in range(0, rect.width(), step):
            if x + segment_width <= fill_width:
                painter.setBrush(QBrush(active_color))
            else:
                painter.setBrush(QBrush(ghost_color))
            painter.drawRect(x, 0, segment_width, rect.height())


class LiquidGlassCard(QFrame):
    """Professional liquid glass card with physics-based styling"""
    
    def __init__(self, title: str, value: str, label: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(200, 150)
        
        # Glass styling properties
        self.glass_color: QColor = QColor(255, 255, 255, 12)
        self.border_color: QColor = QColor(255, 255, 255, 25)
        
        # Set frame properties for glass effect
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setAutoFillBackground(False)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(12, 12, 15, 0.95), stop:1 rgba(8, 8, 10, 0.98));
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 12px;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title label
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            font-weight: bold;
            color: #bc13fe;
        """)
        layout.addWidget(self.title_label)
        
        # Value label
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 28px;
            font-weight: bold;
            color: #00f2ff;
        """)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Label
        self.label_label = QLabel(label)
        self.label_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 10px;
            color: #888;
        """)
        self.label_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_label)
        
        layout.addStretch()
        
    def set_value(self, value: str) -> None:
        """Update the card value"""
        self.value_label.setText(value)
        
    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Segmented glass effect with 2px gaps."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor(self.border_color), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 16, 16)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, 20))
        gradient.setColorAt(1, QColor(255, 255, 255, 8))
        painter.setBrush(QBrush(gradient))
        for y in range(2, rect.height() - 2, 5):
            painter.drawRect(2, y, rect.width() - 4, 3)
        super().paintEvent(a0)


class CPUThreadMatrix(QWidget):
    """4x4 CPU thread grid with segmented bars and PKG_TEMP greeble."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.thread_loads: List[float] = [0.0] * 16
        self.pkg_temp: float = 0.0
        self.warning_active: bool = False
        self.flicker_timer: QTimer = QTimer(self)
        self.flicker_state: bool = False
        self.flicker_timer.timeout.connect(self.toggle_flicker)  # type: ignore
    
    def update_threads(self, loads: List[float], temp: float) -> None:
        """Update thread loads and temperature"""
        self.thread_loads = loads[:16] if len(loads) >= 16 else loads + [0.0] * (16 - len(loads))
        self.pkg_temp = temp
        if temp >= 75 and not self.warning_active:
            self.warning_active = True
            self.flicker_timer.start(500)
        elif temp < 75 and self.warning_active:
            self.warning_active = False
            self.flicker_timer.stop()
        self.update()
    
    def toggle_flicker(self) -> None:
        """Toggle flicker state for warning"""
        self.flicker_state = not self.flicker_state
        self.update()
    
    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Render 4x4 CPU thread grid with vertical segmented LED bars."""
        painter = QPainter(self)
        rect = self.rect()
        border_color = QColor("#ff8c00") if (self.warning_active and self.flicker_state) else QColor("#00f2ff")
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(1, 1, -1, -1))
        
        cell_w = rect.width() // 4
        cell_h = rect.height() // 4
        
        for row in range(4):
            for col in range(4):
                idx = row * 4 + col
                load = self.thread_loads[idx]
                
                x = col * cell_w + 5
                y = row * cell_h + 5
                bar_width = cell_w - 10
                bar_height = cell_h - 10
                
                active_color = QColor("#ff8c00") if load > 70 else QColor("#bc13fe")
                ghost_color = QColor(188, 19, 254, 26)
                
                num_segments = 8
                segment_height = 2
                gap = 1
                step = segment_height + gap
                
                filled_segments = int((load / 100.0) * num_segments)
                
                painter.setPen(Qt.PenStyle.NoPen)
                
                for seg in range(num_segments):
                    seg_y = y + bar_height - (seg + 1) * step
                    
                    if seg < filled_segments:
                        painter.setBrush(QBrush(active_color))
                    else:
                        painter.setBrush(QBrush(ghost_color))
                    
                    painter.drawRect(x, seg_y, bar_width, segment_height)
        
        # PKG_TEMP greeble
        painter.setBrush(QBrush(QColor("#ff8c00")))
        painter.drawRect(rect.width() - 80, 5, 75, 30)
        painter.setPen(QPen(QColor("#ffffff")))
        font: QFont = painter.font()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect.width() - 75, 20, f"PKG {int(self.pkg_temp)}°C")


class GPUCircularHUD(QWidget):
    """Radial GPU usage gauge with segmented rings."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.usage: float = 0.0
        self.warning_active: bool = False
        self.flicker_timer: QTimer = QTimer(self)
        self.flicker_state: bool = False
        self.flicker_timer.timeout.connect(self.toggle_flicker)  # type: ignore
    
    def update_usage(self, usage: float) -> None:
        """Update GPU usage percentage"""
        self.usage = usage
        if usage >= 85 and not self.warning_active:
            self.warning_active = True
            self.flicker_timer.start(500)
        elif usage < 85 and self.warning_active:
            self.warning_active = False
            self.flicker_timer.stop()
        self.update()
    
    def toggle_flicker(self) -> None:
        """Toggle flicker state for warning"""
        self.flicker_state = not self.flicker_state
        self.update()
    
    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Render radial GPU usage gauge with segmented ring."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        radius = min(center_x, center_y) - 10
        
        ring_color = QColor("#ff8c00") if (self.warning_active and self.flicker_state) else (QColor("#ff8c00") if self.usage > 70 else QColor("#bc13fe"))
        ghost_color = QColor(188, 19, 254, 26)
        
        pen = QPen(ghost_color, 3)
        pen.setDashPattern([2, 4])  # type: ignore
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        span_angle = int((self.usage / 100.0) * 360 * 16)
        pen = QPen(ring_color, 3)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawArc(center_x - radius + 10, center_y - radius + 10, (radius - 10) * 2, (radius - 10) * 2, 90 * 16, -span_angle)
        
        painter.setPen(QPen(ring_color))
        font: QFont = painter.font()
        font.setPointSize(14)
        font.setFamily("Courier New")
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.usage)}%")


class ThermalBar(QWidget):
    """Horizontal segmented LED bar for thermal/fan display."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(8)
        self.setMaximumHeight(8)
        self.value: float = 0.0
        
    def set_value(self, value: float) -> None:
        """Set bar value"""
        self.value = value
        self.update()
        
    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Render horizontal segmented LED bar."""
        painter = QPainter(self)
        rect = self.rect()
        percentage = self.value / 100.0
        
        active_color = QColor("#ff8c00") if self.value > 70 else QColor("#bc13fe")
        ghost_color = QColor(188, 19, 254, 26)
        
        painter.setPen(Qt.PenStyle.NoPen)
        
        segment_width = 2
        gap = 1
        step = segment_width + gap
        fill_width = int(rect.width() * percentage)
        
        for x in range(0, rect.width(), step):
            if x + segment_width <= fill_width:
                painter.setBrush(QBrush(active_color))
            else:
                painter.setBrush(QBrush(ghost_color))
            painter.drawRect(x, 0, segment_width, rect.height())


class NetworkWaveform(QWidget):
    """Network area chart with vertical segmented LED bars."""
    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.title = title
        self.setMinimumHeight(150)
        self.data: Deque[float] = deque(maxlen=60)
        self.max_speed: float = 10.0
    
    def add_point(self, speed_mbps: float) -> None:
        """Add network speed data point in Mbps."""
        self.data.append(speed_mbps)
        current_max = max(self.data) if self.data else 0.1
        self.max_speed = max(1.0, current_max * 1.2)
        self.update()
    
    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Render network speed chart with vertical segmented LED bars."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        
        painter.fillRect(rect, QColor(10, 10, 12))
        
        if not self.data:
            painter.setPen(QPen(QColor("#666666")))
            font: QFont = painter.font()
            font.setPointSize(10)
            font.setFamily("Consolas")
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Waiting for network data...")
            return
        
        graph_h = rect.height() - 30
        max_val = self.max_speed
        
        num_points = len(self.data)
        bar_width = max(2, rect.width() // num_points)
        gap = 1
        
        painter.setPen(Qt.PenStyle.NoPen)
        
        for i, speed in enumerate(self.data):
            x = i * bar_width
            normalized_val = min(1.0, speed / max_val) if max_val > 0 else 0.0
            bar_h = int(graph_h * normalized_val)
            
            percentage = normalized_val * 100
            active_color = QColor("#ff8c00") if percentage > 70 else QColor("#bc13fe")
            ghost_color = QColor(188, 19, 254, 26)
            
            segment_height = 2
            seg_gap = 1
            step = segment_height + seg_gap
            
            for seg_y in range(0, graph_h, step):
                if graph_h - seg_y <= bar_h:
                    painter.setBrush(QBrush(active_color))
                else:
                    painter.setBrush(QBrush(ghost_color))
                painter.drawRect(x, graph_h - seg_y - segment_height, bar_width - gap, segment_height)
        
        painter.setPen(QPen(QColor("#00f2ff")))
        font = painter.font()
        font.setPointSize(8)
        font.setFamily("Consolas")
        font.setBold(True)
        painter.setFont(font)
        
        current_speed = self.data[-1] if self.data else 0.0
        speed_text = f"CURRENT: {current_speed:.2f} Mbps | MAX: {max_val:.2f} Mbps"
        painter.drawText(5, rect.height() - 10, speed_text)


class VitreosModule(QFrame):
    """Windows-style module container with header bar and decorative controls."""
    def __init__(self, title: str, icon: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.is_minimized: bool = False
        
        # UI components
        self.hazard_label: QLabel
        self.primary_value: QLabel
        self.secondary_value: QLabel
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup the module layout"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            VitreosModule {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(12, 12, 15, 0.95), stop:1 rgba(8, 8, 10, 0.98));
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet("font-size: 24px;")
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 14px;
            font-weight: bold;
            color: #bc13fe;
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Hazard sticker
        self.hazard_label = QLabel("")
        self.hazard_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 10px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 3px;
        """)
        self.hazard_label.hide()
        header_layout.addWidget(self.hazard_label)
        
        layout.addLayout(header_layout)
        
        # Primary value
        self.primary_value = QLabel("--")
        self.primary_value.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 32px;
            font-weight: bold;
            color: #00f2ff;
        """)
        self.primary_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.primary_value)
        
        # Secondary value
        self.secondary_value = QLabel("")
        self.secondary_value.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            color: #888;
        """)
        self.secondary_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.secondary_value)
        
        layout.addStretch()
    
    def set_primary_value(self, value: str) -> None:
        """Set primary display value"""
        self.primary_value.setText(value)
    
    def set_secondary_value(self, value: str) -> None:
        """Set secondary display value"""
        self.secondary_value.setText(value)
    
    def set_hazard_level(self, level: str, color: str) -> None:
        """Set hazard level indicator"""
        self.hazard_label.setText(level)
        self.hazard_label.setStyleSheet(f"""
            font-family: 'Consolas';
            font-size: 10px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 3px;
            background: {color};
            color: white;
        """)
        self.hazard_label.show()
