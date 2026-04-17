"""
Vitreos Custom Widgets - PyQt6 Implementation
Specialized UI components matching Figma design specifications
"""

from typing import Optional, List, Tuple
from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QTextEdit, QLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QRectF, QTimer, pyqtSignal, QEvent
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPaintEvent, QFont, QEnterEvent, QMouseEvent
from datetime import datetime

from src.ui.vitreos_theme import (
    VITREOS_COLORS, FONT_SIZES, get_color, get_font, hex_to_qcolor
)


# ═══════════════════════════════════════════════════════════════════════════
# PHOSPHOR GLOW EFFECT - CRT Monitor Bloom Simulation
# ═══════════════════════════════════════════════════════════════════════════

def apply_phosphor_glow(widget: QWidget, color: str = 'primary_purple', blur_radius: float = 8.0) -> None:
    """
    Apply phosphor glow effect to simulate CRT monitor bloom.
    CRITICAL: Only apply to text labels, NOT containers.
    
    Args:
        widget: QWidget to apply glow effect (should be QLabel with text)
        color: Color name from VITREOS_COLORS
        blur_radius: Blur radius in pixels (default 8.0)
    """
    glow = QGraphicsDropShadowEffect()
    glow.setBlurRadius(blur_radius)
    glow.setColor(get_color(color, 180))  # 70% opacity
    glow.setOffset(0, 0)
    widget.setGraphicsEffect(glow)


class StatusGlyphIcon(QLabel):
    """Neon-tinted status glyph icon (CPU, GPU, MEM, NET)."""
    
    # Unicode glyphs for hardware components
    GLYPHS = {
        'CPU': '⚙',  # Gear icon
        'GPU': '▣',  # Graphics chip
        'MEM': '▦',  # Memory bars
        'NET': '⚡',  # Network signal
    }
    
    def __init__(self, glyph_type: str = 'CPU', color: str = 'primary_purple', parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.glyph_type = glyph_type
        self.color_name = color
        
        # Set glyph
        glyph = self.GLYPHS.get(glyph_type, '●')
        self.setText(glyph)
        
        # Styling
        self.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.setFixedSize(20, 20)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            color: {VITREOS_COLORS[color]};
            background: transparent;
        """)
        
        # Apply phosphor glow
        apply_phosphor_glow(self, color, blur_radius=6.0)


class VitreosFrame(QFrame):
    """
    Frame with corner brackets [ ] for "Greeble" aesthetic.
    Draws thin 1px brackets at all four corners.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.bracket_color = QColor(VITREOS_COLORS['purple_darker'])
        self.bracket_color.setAlpha(102)  # 40% opacity
        self.bracket_size = 12  # Length of bracket arms
    
    def paintEvent(self, a0: QPaintEvent) -> None:
        """Draw corner brackets on frame."""
        super().paintEvent(a0)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        pen = QPen(self.bracket_color, 1)
        painter.setPen(pen)
        
        w = self.width()
        h = self.height()
        size = self.bracket_size
        
        # Top-left bracket ┌
        painter.drawLine(0, size, 0, 0)  # Vertical
        painter.drawLine(0, 0, size, 0)  # Horizontal
        
        # Top-right bracket ┐
        painter.drawLine(w - size, 0, w - 1, 0)  # Horizontal
        painter.drawLine(w - 1, 0, w - 1, size)  # Vertical
        
        # Bottom-left bracket └
        painter.drawLine(0, h - size, 0, h - 1)  # Vertical
        painter.drawLine(0, h - 1, size, h - 1)  # Horizontal
        
        # Bottom-right bracket ┘
        painter.drawLine(w - size, h - 1, w - 1, h - 1)  # Horizontal
        painter.drawLine(w - 1, h - size, w - 1, h - 1)  # Vertical


class ChromaticLogo(QWidget):
    """
    VITREOS logo with chromatic aberration effect.
    Overlapping layers: Purple + Cyan with 2px offset.
    Phosphor glow applied ONLY to text, not container.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent; border: none;")
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build chromatic aberration logo with text-only glow."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container for overlapping layers (transparent, no glow)
        logo_container = QWidget()
        logo_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        logo_container.setStyleSheet("background: transparent; border: none;")
        logo_container.setFixedHeight(50)
        
        # Purple channel (offset -2px left) - NO GLOW for sharp ghosting
        self.logo_red = QLabel("VITREOS", logo_container)
        self.logo_red.setFont(get_font('display', 40))
        self.logo_red.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_red.setGeometry(-2, 0, logo_container.width() + 4, 50)
        self.logo_red.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.logo_red.setStyleSheet("""
            color: rgba(168, 85, 247, 0.5);
            letter-spacing: 3px;
            background: transparent;
        """)
        
        # Main logo (center) - THIS LAYER GETS THE PHOSPHOR GLOW
        self.logo_main = QLabel("VITREOS", logo_container)
        self.logo_main.setFont(get_font('display', 40))
        self.logo_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_main.setGeometry(0, 0, logo_container.width(), 50)
        self.logo_main.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.logo_main.setStyleSheet(f"""
            color: {VITREOS_COLORS['primary_purple']};
            letter-spacing: 3px;
            background: transparent;
        """)
        
        # Apply phosphor glow ONLY to the main text label
        apply_phosphor_glow(self.logo_main, 'primary_purple', blur_radius=12.0)
        
        # Cyan channel (offset +2px right) - NO GLOW for sharp ghosting
        self.logo_cyan = QLabel("VITREOS", logo_container)
        self.logo_cyan.setFont(get_font('display', 40))
        self.logo_cyan.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_cyan.setGeometry(2, 0, logo_container.width() + 4, 50)
        self.logo_cyan.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.logo_cyan.setStyleSheet("""
            color: rgba(6, 182, 212, 0.4);
            letter-spacing: 3px;
            background: transparent;
        """)
        
        layout.addWidget(logo_container)
        
        # Subtitle (no glow)
        subtitle = QLabel("── HARDWARE MONITOR v2.1 ──")
        subtitle.setFont(get_font('mono', FONT_SIZES['micro']))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        subtitle.setStyleSheet(f"""
            color: {VITREOS_COLORS['purple_darker']};
            letter-spacing: 1px;
            background: transparent;
        """)
        layout.addWidget(subtitle)


# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM QPAINTER WIDGETS - Figma V4 Components
# ═══════════════════════════════════════════════════════════════════════════

class VitreosCircularGauge(QWidget):
    """40-segment donut chart for VRAM/disk usage."""
    
    def __init__(self, segments: int = 40, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.value = 0.0
        self.max_value = 100.0
        self.segments = segments
        self.color_name = 'purple_dim'
        self.setFixedSize(80, 80)
    
    def set_value(self, value: float, max_value: float = 100.0, color: str = 'purple_dim') -> None:
        self.value = min(value, max_value)
        self.max_value = max_value
        self.color_name = color
        self.update()
    
    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        outer_radius = min(center_x, center_y) - 4
        inner_radius = outer_radius - 8
        
        filled_segments = int((self.value / self.max_value) * self.segments)
        angle_per_segment = 360 / self.segments
        
        for i in range(self.segments):
            start_angle = -90 + (i * angle_per_segment)
            
            if i < filled_segments:
                color = get_color(self.color_name)
            else:
                color = get_color('segment_off')
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            
            rect = QRectF(center_x - outer_radius, center_y - outer_radius,
                         outer_radius * 2, outer_radius * 2)
            painter.drawPie(rect, int(start_angle * 16), int(angle_per_segment * 16))
            
            inner_rect = QRectF(center_x - inner_radius, center_y - inner_radius,
                               inner_radius * 2, inner_radius * 2)
            painter.setBrush(QBrush(get_color('bg_primary')))
            painter.drawEllipse(inner_rect)


class VitreosBarcode(QWidget):
    """Deterministic vertical line pattern for tech-UI aesthetic."""
    
    def __init__(self, height: int = 40, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setMinimumWidth(50)
    
    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        painter.fillRect(0, 0, width, height, get_color('bg_card'))
        
        pattern = [3, 1, 2, 1, 4, 1, 1, 1, 3, 1, 2, 1, 5, 1, 1, 1, 3, 1, 4, 1]
        x = 0
        
        for i, bar_width in enumerate(pattern * (width // 50 + 1)):
            if x >= width:
                break
            
            if i % 2 == 0:
                painter.fillRect(x, 0, bar_width, height, get_color('border_primary'))
            
            x += bar_width


class IconBadge(QLabel):
    """Icon-only badge for widget headers (⚠, ✓, ⚡, etc.)."""
    
    def __init__(self, icon: str = "⚠", color: str = 'warning_orange', parent: Optional[QWidget] = None):
        super().__init__(icon, parent)
        self.icon = icon
        self.color_name = color
        self.setFont(get_font('mono', FONT_SIZES['small']))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(16, 16)
        self.setStyleSheet(f"""
            color: {VITREOS_COLORS[color]};
            background: transparent;
            border: 1px solid {VITREOS_COLORS[color]};
            padding: 0px;
        """)
    
    def set_icon(self, icon: str, color: str = 'warning_orange') -> None:
        """Update icon and color dynamically."""
        self.icon = icon
        self.color_name = color
        self.setText(icon)
        self.setStyleSheet(f"""
            color: {VITREOS_COLORS[color]};
            background: transparent;
            border: 1px solid {VITREOS_COLORS[color]};
            padding: 0px;
        """)


class AlertBanner(QWidget):
    """Full-width alert banner for critical warnings."""
    
    def __init__(self, message: str = "⚠ CAUTION: HIGH THERMAL LOAD", color: str = 'warning_orange', parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.message = message
        self.color_name = color
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build alert banner layout."""
        self.setFixedHeight(24)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)
        
        # Icon
        icon_label = QLabel("⚠")
        icon_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        icon_label.setStyleSheet(f"color: {VITREOS_COLORS[self.color_name]};")
        layout.addWidget(icon_label)
        
        # Message
        msg_label = QLabel(self.message)
        msg_label.setFont(get_font('mono', FONT_SIZES['small']))
        msg_label.setStyleSheet(f"color: {VITREOS_COLORS[self.color_name]}; letter-spacing: 1px;")
        layout.addWidget(msg_label)
        
        layout.addStretch()
        
        # Styling
        self.setStyleSheet(f"""
            AlertBanner {{
                background: repeating-linear-gradient(
                    45deg,
                    #000 0px, #000 3px,
                    rgba(255, 107, 0, 0.15) 3px, rgba(255, 107, 0, 0.15) 6px
                );
                border: 1px solid {VITREOS_COLORS[self.color_name]};
                border-left: 3px solid {VITREOS_COLORS[self.color_name]};
            }}
        """)
    
    def set_message(self, message: str, color: str = 'warning_orange') -> None:
        """Update alert message and color."""
        self.message = message
        self.color_name = color
        # Rebuild UI with new message
        layout = self.layout()
        if layout is not None:
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                if item is None:
                    continue
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()
                else:
                    child = item.layout()
                    if child is not None:
                        clear_layout(child)
        # Rebuild UI after safe cleanup
        self._setup_ui()


class ConnectionStatus(QWidget):
    """Connection status indicator with icon and label."""
    
    def __init__(self, label: str = "ETH", connected: bool = True, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.label_text = label
        self.connected = connected
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build connection status layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Checkmark/X icon
        self.icon_label = QLabel("✓" if self.connected else "✗")
        self.icon_label.setFont(get_font('mono', FONT_SIZES['small']))
        self.icon_label.setStyleSheet(f"""
            color: {VITREOS_COLORS['green'] if self.connected else VITREOS_COLORS['critical_red']};
            background: transparent;
            border: 1px solid {VITREOS_COLORS['green'] if self.connected else VITREOS_COLORS['critical_red']};
            padding: 2px 4px;
        """)
        layout.addWidget(self.icon_label)
        
        # Label
        self.label_widget = QLabel(self.label_text)
        self.label_widget.setFont(get_font('mono', FONT_SIZES['small']))
        self.label_widget.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        layout.addWidget(self.label_widget)
        
        # Status dot
        self.status_dot = QLabel("●")
        self.status_dot.setFont(get_font('mono', FONT_SIZES['small']))
        self.status_dot.setStyleSheet(f"color: {VITREOS_COLORS['green'] if self.connected else VITREOS_COLORS['critical_red']};")
        layout.addWidget(self.status_dot)
        
        # Status text
        self.status_label = QLabel("Connected" if self.connected else "Disconnected")
        self.status_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['green'] if self.connected else VITREOS_COLORS['critical_red']};")
        layout.addWidget(self.status_label)
    
    def set_connected(self, connected: bool) -> None:
        """Update connection status."""
        self.connected = connected
        self.icon_label.setText("✓" if connected else "✗")
        self.icon_label.setStyleSheet(f"""
            color: {VITREOS_COLORS['green'] if connected else VITREOS_COLORS['critical_red']};
            background: transparent;
            border: 1px solid {VITREOS_COLORS['green'] if connected else VITREOS_COLORS['critical_red']};
            padding: 2px 4px;
        """)
        self.status_dot.setStyleSheet(f"color: {VITREOS_COLORS['green'] if connected else VITREOS_COLORS['critical_red']};")
        self.status_label.setText("Connected" if connected else "Disconnected")
        self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['green'] if connected else VITREOS_COLORS['critical_red']};")


class HazardBadge(QLabel):
    """Hazard warning badge with striped background."""
    
    def __init__(self, text: str = "⚠ ALERT", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setFont(get_font('mono', FONT_SIZES['micro']))
        self.setStyleSheet(f"""
            background: repeating-linear-gradient(
                45deg,
                #000 0px, #000 3px,
                rgba(255, 68, 68, 0.25) 3px, rgba(255, 68, 68, 0.25) 6px
            );
            border: 1px solid {VITREOS_COLORS['critical_red']};
            color: {VITREOS_COLORS['critical_red']};
            padding: 2px 6px;
            letter-spacing: 1px;
        """)


class OCBadge(QLabel):
    """Overclocking badge with orange/black diagonal hazard stripes."""
    
    def __init__(self, text: str = "OC", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setFont(get_font('mono', FONT_SIZES['micro']))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            background: repeating-linear-gradient(
                45deg,
                #000 0px, #000 3px,
                {VITREOS_COLORS['warning_orange']} 3px, {VITREOS_COLORS['warning_orange']} 6px
            );
            border: 1px solid {VITREOS_COLORS['warning_orange']};
            color: {VITREOS_COLORS['text_primary']};
            padding: 1px 4px;
            letter-spacing: 1px;
            font-weight: bold;
        """)


class NeonSwitch(QWidget):
    """Custom neon toggle switch for Tweaks tab."""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.checked = False
        self.setFixedSize(40, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, a0: QMouseEvent) -> None:
        self.checked = not self.checked
        self.toggled.emit(self.checked)
        self.update()
    
    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background track
        if self.checked:
            bg_color = get_color('primary_purple', 100)
        else:
            bg_color = get_color('bg_card')
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(get_color('border_primary'), 1))
        painter.drawRoundedRect(0, 0, 40, 20, 10, 10)
        
        # Thumb
        thumb_x = 22 if self.checked else 2
        thumb_color = get_color('primary_purple') if self.checked else get_color('text_dim')
        
        painter.setBrush(QBrush(thumb_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(thumb_x, 2, 16, 16)


# ═══════════════════════════════════════════════════════════════════════════
# SEGMENTED BAR - Horizontal LED Progress Indicator
# ═══════════════════════════════════════════════════════════════════════════

class VitreosSegmentedBar(QWidget):
    """
    Horizontal segmented LED bar with auto-alert coloring.
    Matches Figma SegmentedBar component.
    """
    
    def __init__(
        self,
        segments: int = 22,
        height: int = 6,
        gap: int = 2,
        color: str = 'primary_purple',
        hex_color: Optional[str] = None,
        alert_threshold: float = 0.8,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.segments = segments
        self.bar_height = height
        self.gap = gap
        self.color_name = color
        self.hex_color = hex_color  # Direct hex override
        self.alert_threshold = alert_threshold
        self.value = 0.0
        self.max_value = 100.0
        self.status_override = 'auto'
        
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
    
    def set_value(self, value: float, max_value: float = 100.0, status: str = 'auto') -> None:
        """
        Update bar value and trigger repaint.
        
        Args:
            value: Current value
            max_value: Maximum value for scaling
            status: 'auto' (use threshold), 'normal', 'warning', 'critical'
        """
        self.value = min(value, max_value)
        self.max_value = max_value
        self.status_override = status
        self.update()
    
    def paintEvent(self, a0: QPaintEvent) -> None:
        """Draw segmented bar with glow effects."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        segment_width = (width - (self.segments - 1) * self.gap) / self.segments
        
        # Calculate filled segments
        fill_ratio = self.value / self.max_value if self.max_value > 0 else 0
        filled_segments = int(fill_ratio * self.segments)
        
        # Determine color based on status
        if self.status_override == 'critical':
            alert_zone = True
        elif self.status_override == 'warning':
            alert_zone = True
        elif self.status_override == 'normal':
            alert_zone = False
        else:  # 'auto'
            alert_zone = filled_segments >= int(self.segments * self.alert_threshold)
        
        for i in range(self.segments):
            x = i * (segment_width + self.gap)
            rect = QRectF(x, 0, segment_width, self.bar_height)
            
            if i < filled_segments:
                # Active segment — use hex_color override if provided
                if alert_zone:
                    color = get_color('warning_orange')
                    glow_color = get_color('warning_orange', 136)
                elif self.hex_color:
                    color = QColor(self.hex_color)
                    glow_color = QColor(self.hex_color)
                    glow_color.setAlpha(136)
                else:
                    color = get_color(self.color_name)
                    glow_color = get_color(self.color_name, 136)
                
                painter.fillRect(rect, color)
                painter.setPen(QPen(glow_color, 0))
                painter.drawRect(rect)
            else:
                painter.fillRect(rect, get_color('segment_off'))


# ═══════════════════════════════════════════════════════════════════════════
# VERTICAL SEGMENTED BAR - For CPU Core Grid
# ═══════════════════════════════════════════════════════════════════════════

class VitreosVerticalBar(QWidget):
    """
    Vertical segmented LED bar for per-core CPU usage.
    Matches Figma VerticalSegmentedBar component.
    """
    
    def __init__(
        self,
        segments: int = 7,
        width: int = 12,
        segment_height: int = 5,
        gap: int = 1,
        color: str = 'primary_purple',
        alert_threshold: float = 0.75,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.segments = segments
        self.bar_width = width
        self.segment_height = segment_height
        self.gap = gap
        self.color_name = color
        self.alert_threshold = alert_threshold
        self.value = 0.0
        self.max_value = 100.0
        
        total_height = segments * segment_height + (segments - 1) * gap
        self.setFixedSize(width, total_height)
    
    def set_value(self, value: float, max_value: float = 100.0) -> None:
        """Update bar value and trigger repaint."""
        self.value = min(value, max_value)
        self.max_value = max_value
        self.update()
    
    def paintEvent(self, a0: QPaintEvent) -> None:
        """Draw vertical segmented bar (bottom-to-top fill)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate filled segments
        fill_ratio = self.value / self.max_value if self.max_value > 0 else 0
        filled_segments = int(fill_ratio * self.segments)
        
        # Determine if in alert zone
        alert_zone = filled_segments >= int(self.segments * self.alert_threshold)
        
        # Draw from bottom to top
        for i in range(self.segments):
            y = self.height() - (i + 1) * (self.segment_height + self.gap) + self.gap
            rect = QRectF(0, y, self.bar_width, self.segment_height)
            
            if i < filled_segments:
                # Active segment
                if alert_zone:
                    color = get_color('warning_orange')
                    glow_color = get_color('warning_orange', 136)  # 0x88 alpha
                else:
                    color = get_color(self.color_name)
                    glow_color = get_color(self.color_name, 136)
                
                painter.fillRect(rect, color)
                
                # Glow effect (reduced intensity from Figma: 4px)
                painter.setPen(QPen(glow_color, 0))
                painter.drawRect(rect)
            else:
                # Inactive segment
                painter.fillRect(rect, get_color('segment_dim'))


# ═══════════════════════════════════════════════════════════════════════════
# WIN FRAME - Container with Title Bar and Scanlines
# ═══════════════════════════════════════════════════════════════════════════

class VitreosWinFrame(QFrame):
    """
    Custom window frame with title bar, indicators, and scanline overlay.
    Matches Figma WinFrame component.
    """
    
    minimize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()
    
    def __init__(
        self,
        title: str,
        accent_color: str = 'primary_purple',
        badge: Optional[str] = None,
        badge_color: str = 'warning_orange',
        pid: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.title = title
        self.accent_color_name = accent_color
        self.badge = badge
        self.badge_color_name = badge_color
        self.pid = pid
        
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self) -> None:
        """Build the frame layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title bar
        self.title_bar = self._create_title_bar()
        layout.addWidget(self.title_bar)
        
        # Content area (to be filled by parent)
        self.content_widget = QWidget()
        self.content_widget.setObjectName("ContentArea")
        layout.addWidget(self.content_widget)
    
    def _create_title_bar(self) -> QWidget:
        """Create the 18px title bar with indicators and controls (REDUCED HEIGHT)."""
        title_bar = QWidget()
        title_bar.setFixedHeight(18)  # Reduced from 24px to 18px
        title_bar.setObjectName("TitleBar")
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(6, 0, 3, 0)  # Reduced padding
        layout.setSpacing(4)  # Reduced spacing
        
        # Left side: Indicators + Icon + Title + Badge
        left_layout = QHBoxLayout()
        left_layout.setSpacing(4)  # Reduced spacing
        
        # Indicator dots (micro-square style: 5x5 pixels)
        indicator_widget = QWidget()
        indicator_widget.setFixedSize(12, 5)
        indicator_layout = QHBoxLayout(indicator_widget)
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        indicator_layout.setSpacing(2)
        
        # Active dot (5x5 square)
        active_dot = QLabel()
        active_dot.setFixedSize(5, 5)
        active_dot.setStyleSheet(f"""
            background: {VITREOS_COLORS[self.accent_color_name]};
            border-radius: 0px;
        """)
        indicator_layout.addWidget(active_dot)
        
        # Inactive dot (5x5 square)
        inactive_dot = QLabel()
        inactive_dot.setFixedSize(5, 5)
        inactive_dot.setStyleSheet(f"background: {VITREOS_COLORS['text_darker']}; border-radius: 0px;")
        indicator_layout.addWidget(inactive_dot)
        
        left_layout.addWidget(indicator_widget)
        
        # Icon
        icon_label = QLabel("▶")
        icon_label.setFont(get_font('mono', FONT_SIZES['tiny']))  # Smaller icon
        icon_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        left_layout.addWidget(icon_label)
        
        # Title
        self.title_label = QLabel(self.title.upper())
        self.title_label.setFont(get_font('mono', FONT_SIZES['small']))  # Reduced from label to small
        self.title_label.setStyleSheet(f"""
            color: {VITREOS_COLORS[self.accent_color_name]};
            letter-spacing: 1px;
        """)
        left_layout.addWidget(self.title_label)
        
        # Badge container (for dynamic badge updates)
        self.badge_container = QWidget()
        self.badge_layout = QHBoxLayout(self.badge_container)
        self.badge_layout.setContentsMargins(0, 0, 0, 0)
        self.badge_layout.setSpacing(4)
        
        # Badge (if provided) - now using IconBadge
        if self.badge:
            # Check if badge is an icon (single character) or text
            if len(self.badge) == 1:
                self.badge_widget = IconBadge(self.badge, self.badge_color_name)
            else:
                self.badge_widget = QLabel(self.badge)
                self.badge_widget.setFont(get_font('mono', FONT_SIZES['micro']))
                self.badge_widget.setStyleSheet(f"""
                    background: repeating-linear-gradient(
                        45deg,
                        #000 0px, #000 3px,
                        rgba(255, 107, 0, 0.25) 3px, rgba(255, 107, 0, 0.25) 6px
                    );
                    border: 1px solid {VITREOS_COLORS[self.badge_color_name]};
                    color: {VITREOS_COLORS[self.badge_color_name]};
                    padding: 0px 4px;
                    letter-spacing: 1px;
                """)
            self.badge_layout.addWidget(self.badge_widget)
        
        left_layout.addWidget(self.badge_container)
        
        layout.addLayout(left_layout)
        layout.addStretch()
        
        # Right side: Aesthetic window controls (micro-square style: 5x5 pixels)
        # Minimize glyph
        self.min_label = QLabel("_")
        self.min_label.setFont(get_font('mono', 7))
        self.min_label.setFixedSize(5, 5)  # Micro-square
        self.min_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.min_label.setStyleSheet(f"""
            QLabel {{
                color: {VITREOS_COLORS['text_dim']};
                background: transparent;
            }}
        """)
        self.min_label.setCursor(Qt.CursorShape.PointingHandCursor)
        # Use parameter names that match PyQt6 stubs: `enterEvent` expects `event`, `leaveEvent` expects `a0`.
        self.min_label.enterEvent = lambda event: self._on_min_enter(event)
        self.min_label.leaveEvent = lambda a0: self._on_min_leave(a0)
        layout.addWidget(self.min_label)
        
        # Close glyph
        self.close_label = QLabel("×")
        self.close_label.setFont(get_font('mono', 7))
        self.close_label.setFixedSize(5, 5)  # Micro-square
        self.close_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.close_label.setStyleSheet(f"""
            QLabel {{
                color: {VITREOS_COLORS['text_dim']};
                background: transparent;
            }}
        """)
        self.close_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_label.enterEvent = lambda event: self._on_close_enter(event)
        self.close_label.leaveEvent = lambda a0: self._on_close_leave(a0)
        layout.addWidget(self.close_label)
        
        return title_bar
    
    def _on_min_enter(self, event: QEnterEvent | None) -> None:
        """Handle minimize button hover enter."""
        if self.min_label is not None:
            self.min_label.setStyleSheet(f"""
                QLabel {{
                    color: {VITREOS_COLORS[self.accent_color_name]};
                    background: transparent;
                    text-shadow: 0px 0px 4px {VITREOS_COLORS[self.accent_color_name]};
                }}
            """)
    
    def _on_min_leave(self, event: QEvent | None) -> None:
        """Handle minimize button hover leave."""
        if self.min_label is not None:
            self.min_label.setStyleSheet(f"""
                QLabel {{
                    color: {VITREOS_COLORS['text_dim']};
                    background: transparent;
                }}
            """)
    
    def _on_close_enter(self, event: QEnterEvent | None) -> None:
        """Handle close button hover enter."""
        if self.close_label is not None:
            self.close_label.setStyleSheet(f"""
                QLabel {{
                    color: {VITREOS_COLORS[self.accent_color_name]};
                    background: transparent;
                    text-shadow: 0px 0px 4px {VITREOS_COLORS[self.accent_color_name]};
                }}
            """)
    
    def _on_close_leave(self, event: QEvent | None) -> None:
        """Handle close button hover leave."""
        if self.close_label is not None:
            self.close_label.setStyleSheet(f"""
                QLabel {{
                    color: {VITREOS_COLORS['text_dim']};
                    background: transparent;
                }}
            """)
    
    def _apply_styling(self) -> None:
        """Apply RESTRAINED styling with thin borders to frame."""
        # Use dimmed purple for active modules, #333333 for inactive
        border_color = VITREOS_COLORS['border_active']  # Dimmed purple
        
        self.setStyleSheet(f"""
            VitreosWinFrame {{
                background: {VITREOS_COLORS['bg_primary']};
                border: 1px solid {border_color};
            }}
            #TitleBar {{
                background: {VITREOS_COLORS['bg_titlebar']};
                border-bottom: 1px solid {border_color};
            }}
            #ContentArea {{
                background: {VITREOS_COLORS['bg_primary']};
                border: none;
            }}
        """)
    
    def paintEvent(self, a0: QPaintEvent) -> None:
        """Draw scanline overlay effect (Figma spec: every 2px)."""
        super().paintEvent(a0)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        # Scanline pattern (starts below title bar) - Figma: every 2px
        scanline_color = QColor(0, 0, 0, 20)  # rgba(0,0,0,0.08)
        pen = QPen(scanline_color)
        painter.setPen(pen)
        
        y = 24  # Start below title bar
        while y < self.height():
            painter.drawLine(0, y, self.width(), y)
            y += 4  # Draw line every 4px (creates 2px transparent, 2px line pattern)
    
    def set_content_layout(self, layout: QVBoxLayout) -> None:
        """Set the content area layout."""
        self.content_widget.setLayout(layout)
    
    def set_badge(self, badge: Optional[str], color: str = 'warning_orange') -> None:
        """Dynamically update or remove badge."""
        # Clear existing badge
        for i in reversed(range(self.badge_layout.count())):
            item = self.badge_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        
        if badge:
            # Add new badge
            if len(badge) == 1:
                self.badge_widget = IconBadge(badge, color)
            else:
                self.badge_widget = QLabel(badge)
                self.badge_widget.setFont(get_font('mono', FONT_SIZES['micro']))
                self.badge_widget.setStyleSheet(f"""
                    background: repeating-linear-gradient(
                        45deg,
                        #000 0px, #000 3px,
                        rgba(255, 107, 0, 0.25) 3px, rgba(255, 107, 0, 0.25) 6px
                    );
                    border: 1px solid {VITREOS_COLORS[color]};
                    color: {VITREOS_COLORS[color]};
                    padding: 0px 4px;
                    letter-spacing: 1px;
                """)
            self.badge_layout.addWidget(self.badge_widget)
    
    def add_alert_banner(self, message: str, color: str = 'warning_orange') -> None:
        """Add alert banner below title bar."""
        # Check if alert banner already exists
        if hasattr(self, 'alert_banner'):
            self.alert_banner.set_message(message, color)
        else:
            self.alert_banner = AlertBanner(message, color)
            # Insert after title bar (guard for None and layout types)
            layout = self.layout()
            if layout is not None:
                # Use getattr to safely call layout.insertWidget when available
                insert_fn = getattr(layout, 'insertWidget', None)
                if callable(insert_fn):
                    try:
                        insert_fn(1, self.alert_banner)
                    except Exception:
                        # Fallback to addWidget
                        add_fn = getattr(layout, 'addWidget', None)
                        if callable(add_fn):
                            try:
                                add_fn(self.alert_banner)
                            except Exception:
                                pass
                else:
                    add_fn = getattr(layout, 'addWidget', None)
                    if callable(add_fn):
                        try:
                            add_fn(self.alert_banner)
                        except Exception:
                            pass
    
    def remove_alert_banner(self) -> None:
        """Remove alert banner if it exists."""
        if hasattr(self, 'alert_banner'):
            banner = getattr(self, 'alert_banner', None)
            if banner is not None:
                banner.setParent(None)
                banner.deleteLater()
            try:
                delattr(self, 'alert_banner')
            except Exception:
                pass


def clear_layout(layout: QLayout | None) -> None:
    """Recursively and safely clear all items from a QLayout.

    This helper removes widgets from the layout, calls `deleteLater()` on
    them to ensure Qt frees resources, and descends into nested layouts.

    Args:
        layout: The QLayout instance to clear. If None, this is a no-op.
    """
    if layout is None:
        return

    while layout.count():
        item = layout.takeAt(0)
        if item is None:
            continue

        w = item.widget()
        if w is not None:
            # Remove from parent and schedule for deletion
            w.setParent(None)
            w.deleteLater()
        else:
            child = item.layout()
            if child is not None:
                clear_layout(child)


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM PULSE LOG - Sidebar Terminal Widget
# ═══════════════════════════════════════════════════════════════════════════

class SystemPulseLog(QWidget):
    """
    Fixed-width sidebar with VITREOS logo and scrolling log.
    Matches Figma SystemPulseLog component.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setFixedWidth(260)  # Widened from 232px to 260px
        self.log_entries: List[Tuple[str, str, str, str]] = []  # (time, level, msg, color)
        self.cursor_visible = True
        
        self._setup_ui()
        self._start_timers()
    
    def _setup_ui(self) -> None:
        """Build the sidebar layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title bar
        title_bar = self._create_title_bar()
        layout.addWidget(title_bar)
        
        # Logo section
        logo_section = self._create_logo_section()
        layout.addWidget(logo_section)
        
        # Log area
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log_widget.setFont(get_font('mono', 8))  # Reduced from 9px to 8px
        self.log_widget.setStyleSheet(f"""
            QTextEdit {{
                background: {VITREOS_COLORS['bg_secondary']};
                border: none;
                color: {VITREOS_COLORS['text_dim']};
                padding: 8px;
                line-height: 1.2;
            }}
        """)
        layout.addWidget(self.log_widget, 1)
        
        # Prompt
        prompt_widget = self._create_prompt()
        layout.addWidget(prompt_widget)
        
        # Bottom bar
        bottom_bar = self._create_bottom_bar()
        layout.addWidget(bottom_bar)
        
        # Apply sidebar styling (SOLID STATE)
        self.setStyleSheet(f"""
            SystemPulseLog {{
                background: {VITREOS_COLORS['bg_secondary']};
                border-right: 2px solid {VITREOS_COLORS['primary_purple']};
            }}
        """)
    
    def _create_title_bar(self) -> QWidget:
        """Create title bar with PID display."""
        title_bar = QWidget()
        title_bar.setFixedHeight(24)
        title_bar.setStyleSheet(f"""
            background: {VITREOS_COLORS['bg_titlebar']};
            border-bottom: 1px solid {VITREOS_COLORS['border_primary']};
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(8, 0, 8, 0)
        
        # Indicator dot
        dot = QLabel()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(f"background: {VITREOS_COLORS['primary_purple']}; border-radius: 0px;")
        layout.addWidget(dot)
        
        # Title
        title = QLabel("SYSTEM_PULSE.LOG")
        title.setFont(get_font('mono', FONT_SIZES['label']))
        title.setStyleSheet(f"""
            color: {VITREOS_COLORS['primary_purple']};
            letter-spacing: 1px;
        """)
        layout.addWidget(title)
        layout.addStretch()
        
        # PID with glow effect
        pid = QLabel("PID: 31337")
        pid.setFont(get_font('mono', FONT_SIZES['tiny']))
        pid.setStyleSheet(f"""
            color: {VITREOS_COLORS['green']};
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid {VITREOS_COLORS['green']};
            padding: 2px 6px;
        """)
        apply_phosphor_glow(pid, 'green', blur_radius=6.0)
        layout.addWidget(pid)
        
        return title_bar
    
    def _create_logo_section(self) -> QWidget:
        """Create VITREOS logo section with chromatic aberration and status glyphs."""
        logo_widget = QWidget()
        logo_widget.setStyleSheet(f"border-bottom: 1px solid {VITREOS_COLORS['border_secondary']};")
        
        layout = QVBoxLayout(logo_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Chromatic aberration logo
        self.chromatic_logo = ChromaticLogo()
        layout.addWidget(self.chromatic_logo)
        
        # Status glyph indicators
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(12)
        
        glyph_configs = [
            ('CPU', 'primary_purple'),
            ('GPU', 'warning_orange'),
            ('MEM', 'purple_dim'),
            ('NET', 'green'),
        ]
        
        for glyph_type, color in glyph_configs:
            ind_layout = QVBoxLayout()
            ind_layout.setSpacing(2)
            
            # Glyph icon with phosphor glow
            glyph = StatusGlyphIcon(glyph_type, color)
            ind_layout.addWidget(glyph, alignment=Qt.AlignmentFlag.AlignCenter)
            
            # Label
            lbl = QLabel(glyph_type)
            lbl.setFont(get_font('mono', FONT_SIZES['micro']))
            lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ind_layout.addWidget(lbl)
            
            indicators_layout.addLayout(ind_layout)
        
        layout.addLayout(indicators_layout)
        
        return logo_widget
    
    def _create_prompt(self) -> QWidget:
        """Create terminal prompt with blinking cursor."""
        prompt_widget = QWidget()
        prompt_widget.setFixedHeight(32)
        prompt_widget.setStyleSheet(f"""
            background: {VITREOS_COLORS['bg_secondary']};
            border-top: 1px solid {VITREOS_COLORS['border_secondary']};
        """)
        
        layout = QHBoxLayout(prompt_widget)
        layout.setContentsMargins(8, 0, 8, 0)
        
        self.prompt_label = QLabel("root@vitreos:~#")
        self.prompt_label.setFont(get_font('mono', FONT_SIZES['label']))
        self.prompt_label.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
        layout.addWidget(self.prompt_label)
        
        self.cursor_label = QLabel("█")
        self.cursor_label.setFont(get_font('mono', FONT_SIZES['label']))
        self.cursor_label.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
        layout.addWidget(self.cursor_label)
        
        layout.addStretch()
        
        return prompt_widget
    
    def _create_bottom_bar(self) -> QWidget:
        """Create bottom terminal status bar."""
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(20)
        bottom_bar.setStyleSheet(f"""
            background: {VITREOS_COLORS['bg_frame']};
            border-top: 1px solid {VITREOS_COLORS['border_dim']};
        """)
        
        layout = QHBoxLayout(bottom_bar)
        layout.setContentsMargins(8, 0, 8, 0)
        
        # Left: Terminal prompt
        left_label = QLabel("root@vitreos -#")
        left_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        left_label.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
        apply_phosphor_glow(left_label, 'primary_purple', blur_radius=4.0)
        layout.addWidget(left_label)
        
        layout.addStretch()
        
        # Right: System info
        right_label = QLabel("UTF-8 | LF | BASH")
        right_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        right_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darkest']};")
        layout.addWidget(right_label)
        
        # Separator
        sep = QLabel("|")
        sep.setFont(get_font('mono', FONT_SIZES['tiny']))
        sep.setStyleSheet(f"color: {VITREOS_COLORS['text_darkest']};")
        layout.addWidget(sep)
        
        # Time
        self.time_label = QLabel()
        self.time_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        self.time_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darkest']};")
        layout.addWidget(self.time_label)
        
        return bottom_bar
    
    def _start_timers(self) -> None:
        """Start cursor blink and clock timers."""
        # Cursor blink
        self.cursor_timer = QTimer(self)
        self.cursor_timer.timeout.connect(self._toggle_cursor)
        self.cursor_timer.start(530)
        
        # Clock update
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()
    
    def _toggle_cursor(self) -> None:
        """Toggle cursor visibility."""
        self.cursor_visible = not self.cursor_visible
        self.cursor_label.setVisible(self.cursor_visible)
    
    def _update_clock(self) -> None:
        """Update time display."""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        self.time_label.setText(time_str)
    
    def append_log(self, level: str, message: str, color: str = 'text_dim') -> None:
        """
        Append a log entry to the terminal with text shadow for readability.
        
        Args:
            level: Log level (OK, WARN, CPU, GPU, etc.)
            message: Log message
            color: Color name from VITREOS_COLORS
        """
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        
        color_hex = VITREOS_COLORS.get(color, VITREOS_COLORS['text_dim'])
        
        # Add text shadow for better readability over transparent background
        html = f"""
        <span style="color: {VITREOS_COLORS['text_darker']}; text-shadow: 0px 0px 3px #000;">[{time_str}]</span>
        <span style="color: {color_hex}; text-shadow: 0px 0px 4px {color_hex}, 0px 0px 2px #000; font-weight: bold;">[{level}]</span>
        <span style="color: {VITREOS_COLORS['text_dim']}; text-shadow: 0px 0px 3px #000;">{message}</span>
        """
        
        self.log_widget.append(html)
        
        # Auto-scroll to bottom (guard for optional scrollbar)
        scrollbar = self.log_widget.verticalScrollBar()
        if scrollbar is not None:
            try:
                scrollbar.setValue(scrollbar.maximum())
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'VitreosSegmentedBar',
    'VitreosVerticalBar',
    'VitreosWinFrame',
    'SystemPulseLog',
    'VitreosCircularGauge',
    'VitreosBarcode',
    'IconBadge',
    'AlertBanner',
    'ConnectionStatus',
    'HazardBadge',
    'OCBadge',
    'NeonSwitch',
    'VitreosFrame',
    'ChromaticLogo',
    'StatusGlyphIcon',
    'apply_phosphor_glow',
    'clear_layout',
]


