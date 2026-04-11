"""
Vitreos Custom Widgets - PyQt6 Implementation
Specialized UI components matching Figma design specifications
"""

from typing import Optional, List, Tuple
from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit
from PyQt6.QtCore import Qt, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPaintEvent, QFont
from datetime import datetime

from vitreos_theme import (
    VITREOS_COLORS, FONT_SIZES, get_color, get_font, hex_to_qcolor
)


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
        alert_threshold: float = 0.8,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.segments = segments
        self.bar_height = height
        self.gap = gap
        self.color_name = color
        self.alert_threshold = alert_threshold
        self.value = 0.0
        self.max_value = 100.0
        
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
    
    def set_value(self, value: float, max_value: float = 100.0) -> None:
        """Update bar value and trigger repaint."""
        self.value = min(value, max_value)
        self.max_value = max_value
        self.update()
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Draw segmented bar with glow effects."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        segment_width = (width - (self.segments - 1) * self.gap) / self.segments
        
        # Calculate filled segments
        fill_ratio = self.value / self.max_value if self.max_value > 0 else 0
        filled_segments = int(fill_ratio * self.segments)
        
        # Determine if in alert zone
        alert_zone = filled_segments >= int(self.segments * self.alert_threshold)
        
        for i in range(self.segments):
            x = i * (segment_width + self.gap)
            rect = QRectF(x, 0, segment_width, self.bar_height)
            
            if i < filled_segments:
                # Active segment
                if alert_zone:
                    color = get_color('warning_orange')
                    glow_color = get_color('warning_orange', 136)  # 88 in hex = 136
                else:
                    color = get_color(self.color_name)
                    glow_color = get_color(self.color_name, 136)
                
                painter.fillRect(rect, color)
                
                # Glow effect
                painter.setPen(QPen(glow_color, 0))
                painter.drawRect(rect)
            else:
                # Inactive segment
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
    
    def paintEvent(self, event: QPaintEvent) -> None:
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
                    glow_color = get_color('warning_orange', 136)
                else:
                    color = get_color(self.color_name)
                    glow_color = get_color(self.color_name, 136)
                
                painter.fillRect(rect, color)
                
                # Glow effect
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
        """Create the 24px title bar with indicators and controls."""
        title_bar = QWidget()
        title_bar.setFixedHeight(24)
        title_bar.setObjectName("TitleBar")
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(8)
        
        # Left side: Indicators + Icon + Title + Badge
        left_layout = QHBoxLayout()
        left_layout.setSpacing(6)
        
        # Indicator dots
        indicator_widget = QWidget()
        indicator_widget.setFixedSize(16, 6)
        indicator_layout = QHBoxLayout(indicator_widget)
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        indicator_layout.setSpacing(2)
        
        # Active dot
        active_dot = QLabel()
        active_dot.setFixedSize(6, 6)
        active_dot.setStyleSheet(f"""
            background: {VITREOS_COLORS[self.accent_color_name]};
            border-radius: 0px;
        """)
        indicator_layout.addWidget(active_dot)
        
        # Inactive dot
        inactive_dot = QLabel()
        inactive_dot.setFixedSize(6, 6)
        inactive_dot.setStyleSheet(f"background: {VITREOS_COLORS['text_darker']}; border-radius: 0px;")
        indicator_layout.addWidget(inactive_dot)
        
        left_layout.addWidget(indicator_widget)
        
        # Icon
        icon_label = QLabel("▶")
        icon_label.setFont(get_font('mono', FONT_SIZES['small']))
        icon_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        left_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(self.title.upper())
        title_label.setFont(get_font('mono', FONT_SIZES['label']))
        title_label.setStyleSheet(f"""
            color: {VITREOS_COLORS[self.accent_color_name]};
            letter-spacing: 1.2px;
        """)
        left_layout.addWidget(title_label)
        
        # Badge (if provided)
        if self.badge:
            badge_label = QLabel(self.badge)
            badge_label.setFont(get_font('mono', FONT_SIZES['tiny']))
            badge_label.setStyleSheet(f"""
                background: repeating-linear-gradient(
                    45deg,
                    #000 0px, #000 3px,
                    rgba(255, 107, 0, 0.25) 3px, rgba(255, 107, 0, 0.25) 6px
                );
                border: 1px solid {VITREOS_COLORS[self.badge_color_name]};
                color: {VITREOS_COLORS[self.badge_color_name]};
                padding: 1px 5px;
                letter-spacing: 1px;
            """)
            left_layout.addWidget(badge_label)
        
        layout.addLayout(left_layout)
        layout.addStretch()
        
        # Right side: PID + Controls
        if self.pid:
            pid_label = QLabel(f"PID:{self.pid}")
            pid_label.setFont(get_font('mono', FONT_SIZES['tiny']))
            pid_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            layout.addWidget(pid_label)
        
        # Minimize button
        min_btn = QPushButton("_")
        min_btn.setFixedSize(14, 14)
        min_btn.setFont(get_font('mono', FONT_SIZES['small']))
        min_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['text_darker']};
                color: {VITREOS_COLORS['text_secondary']};
            }}
            QPushButton:hover {{
                background: {VITREOS_COLORS['border_primary']};
            }}
        """)
        min_btn.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(min_btn)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(14, 14)
        close_btn.setFont(get_font('mono', FONT_SIZES['small']))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['text_darker']};
                color: {VITREOS_COLORS['critical_red']};
            }}
            QPushButton:hover {{
                background: {VITREOS_COLORS['critical_red']};
                color: {VITREOS_COLORS['text_primary']};
            }}
        """)
        close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(close_btn)
        
        return title_bar
    
    def _apply_styling(self) -> None:
        """Apply Liquid Glass styling to frame."""
        self.setStyleSheet(f"""
            VitreosWinFrame {{
                background: {VITREOS_COLORS['bg_primary']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
            }}
            #TitleBar {{
                background: {VITREOS_COLORS['bg_titlebar']};
                border-bottom: 1px solid {VITREOS_COLORS['border_primary']};
            }}
            #ContentArea {{
                background: {VITREOS_COLORS['bg_primary']};
            }}
        """)
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Draw scanline overlay effect."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        # Scanline pattern (starts below title bar)
        scanline_color = QColor(0, 0, 0, 20)  # rgba(0,0,0,0.08)
        pen = QPen(scanline_color)
        painter.setPen(pen)
        
        y = 24  # Start below title bar
        while y < self.height():
            painter.drawLine(0, y, self.width(), y)
            y += 4  # Every 4 pixels
    
    def set_content_layout(self, layout: QVBoxLayout) -> None:
        """Set the content area layout."""
        self.content_widget.setLayout(layout)


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
        
        self.setFixedWidth(232)
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
        self.log_widget.setFont(get_font('mono', FONT_SIZES['small']))
        self.log_widget.setStyleSheet(f"""
            QTextEdit {{
                background: {VITREOS_COLORS['bg_secondary']};
                border: none;
                color: {VITREOS_COLORS['text_dim']};
                padding: 8px;
            }}
        """)
        layout.addWidget(self.log_widget, 1)
        
        # Prompt
        prompt_widget = self._create_prompt()
        layout.addWidget(prompt_widget)
        
        # Bottom bar
        bottom_bar = self._create_bottom_bar()
        layout.addWidget(bottom_bar)
        
        # Apply sidebar styling
        self.setStyleSheet(f"""
            SystemPulseLog {{
                background: {VITREOS_COLORS['bg_secondary']};
                border-right: 1px solid {VITREOS_COLORS['border_primary']};
            }}
        """)
    
    def _create_title_bar(self) -> QWidget:
        """Create title bar with indicator."""
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
        
        # PID
        pid = QLabel("PID: 31337")
        pid.setFont(get_font('mono', FONT_SIZES['tiny']))
        pid.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(pid)
        
        return title_bar
    
    def _create_logo_section(self) -> QWidget:
        """Create VITREOS logo section with status indicators."""
        logo_widget = QWidget()
        logo_widget.setStyleSheet(f"border-bottom: 1px solid {VITREOS_COLORS['border_secondary']};")
        
        layout = QVBoxLayout(logo_widget)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)
        
        # VITREOS logo
        logo = QLabel("VITREOS")
        logo.setFont(get_font('display', FONT_SIZES['logo']))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"""
            color: {VITREOS_COLORS['primary_purple']};
            letter-spacing: 4px;
        """)
        layout.addWidget(logo)
        
        # Subtitle
        subtitle = QLabel("── HARDWARE MONITOR v2.1 ──")
        subtitle.setFont(get_font('mono', FONT_SIZES['tiny']))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            color: {VITREOS_COLORS['purple_darker']};
            letter-spacing: 2px;
        """)
        layout.addWidget(subtitle)
        
        # Status indicators
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(12)
        
        for label, color in [('CPU', 'primary_purple'), ('GPU', 'warning_orange'), 
                             ('MEM', 'purple_dim'), ('NET', 'green')]:
            ind_layout = QVBoxLayout()
            ind_layout.setSpacing(2)
            
            dot = QLabel()
            dot.setFixedSize(6, 6)
            dot.setStyleSheet(f"background: {VITREOS_COLORS[color]}; border-radius: 0px;")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lbl = QLabel(label)
            lbl.setFont(get_font('mono', FONT_SIZES['micro']))
            lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            ind_layout.addWidget(dot, alignment=Qt.AlignmentFlag.AlignCenter)
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
        """Create bottom status bar."""
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(20)
        bottom_bar.setStyleSheet(f"""
            background: {VITREOS_COLORS['bg_frame']};
            border-top: 1px solid {VITREOS_COLORS['border_dim']};
        """)
        
        layout = QHBoxLayout(bottom_bar)
        layout.setContentsMargins(8, 0, 8, 0)
        
        left_label = QLabel("UTF-8 | LF | BASH")
        left_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        left_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darkest']};")
        layout.addWidget(left_label)
        
        layout.addStretch()
        
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
        Append a log entry to the terminal.
        
        Args:
            level: Log level (OK, WARN, CPU, GPU, etc.)
            message: Log message
            color: Color name from VITREOS_COLORS
        """
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        
        color_hex = VITREOS_COLORS.get(color, VITREOS_COLORS['text_dim'])
        
        html = f"""
        <span style="color: {VITREOS_COLORS['text_darker']};">[{time_str}]</span>
        <span style="color: {color_hex};">[{level}]</span>
        <span style="color: {VITREOS_COLORS['text_dim']};">{message}</span>
        """
        
        self.log_widget.append(html)
        
        # Auto-scroll to bottom
        scrollbar = self.log_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


# ═══════════════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'VitreosSegmentedBar',
    'VitreosVerticalBar',
    'VitreosWinFrame',
    'SystemPulseLog',
]
