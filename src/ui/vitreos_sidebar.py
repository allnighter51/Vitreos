"""
Vitreos Tactical Sidebar - Phosphor Glow Logo and Pulse Log
"""

from typing import List, Tuple, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QAbstractItemView, QStyledItemDelegate, QStyleOptionViewItem
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QModelIndex
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath
from datetime import datetime
import random

from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font


# ── Tag → hex color lookup (shared by delegate and append_log) ──────────────
_TAG_COLORS: Dict[str, str] = {
    'CPU':  VITREOS_COLORS['primary_purple'],
    'GPU':  VITREOS_COLORS['warning_orange'],
    'MEM':  VITREOS_COLORS['purple_dim'],
    'NET':  VITREOS_COLORS['green'],
    'SYS':  VITREOS_COLORS['text_secondary'],
    'FAN':  VITREOS_COLORS['warning_orange'],
    'OK':   VITREOS_COLORS['green'],
    'WARN': VITREOS_COLORS['critical_red'],
    'ERR':  VITREOS_COLORS['critical_red'],
}


class LogGlowDelegate(QStyledItemDelegate):
    """Native-render delegate: draws Time / [TAG] (phosphor glow) / Message per row."""

    _ROW_H = 16
    _PAD_X = 6

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> 'QSize':  # type: ignore[override]
        from PyQt6.QtCore import QSize
        return QSize(option.rect.width(), self._ROW_H)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        data = index.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Force Share Tech Mono terminal font; fallback to Consolas
        terminal_font = QFont("Share Tech Mono", 8)
        terminal_font.setStyleHint(QFont.StyleHint.Monospace)
        painter.setFont(terminal_font)
        fm = painter.fontMetrics()

        rect   = option.rect
        y_base = rect.top() + fm.ascent() + (self._ROW_H - fm.height()) // 2
        x      = rect.left() + self._PAD_X

        # 1. Time (flat gray, no glow)
        time_text = "[" + data['time'] + "]"
        painter.setPen(QPen(QColor('#555555'), 1))
        painter.drawText(x, y_base, time_text)
        x += fm.horizontalAdvance(time_text) + 4

        # 2. Tag (directional offset bloom + sharp core)
        level     = data['level']
        tag_text  = "[" + level + "] "
        tag_color = QColor(data['color_hex'])
        tag_w     = fm.horizontalAdvance(tag_text)

        # WARN/ERR: tinted box drawn FIRST so glow text sits on top
        if level in ('WARN', 'ERR'):
            tint = QColor(VITREOS_COLORS['critical_red'])
            tint.setAlpha(40)
            box_rect = QRectF(x - 2, rect.top() + 1, tag_w + 4, self._ROW_H - 2)
            painter.fillRect(box_rect, tint)
            border = QColor(VITREOS_COLORS['critical_red'])
            painter.setPen(QPen(border, 1))
            painter.drawRect(box_rect)

        # Outer bloom: alpha 25, 2px offset in 4 cardinal directions
        outer = QColor(tag_color)
        outer.setAlpha(25)
        painter.setPen(QPen(outer, 1))
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            painter.drawText(x + dx, y_base + dy, tag_text)

        # Inner bloom: alpha 60, 1px offset in all 8 directions
        inner = QColor(tag_color)
        inner.setAlpha(60)
        painter.setPen(QPen(inner, 1))
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (1, 1), (-1, 1), (1, -1)):
            painter.drawText(x + dx, y_base + dy, tag_text)

        # Sharp core at 100% opacity
        tag_color.setAlpha(255)
        painter.setPen(QPen(tag_color, 1))
        painter.drawText(x, y_base, tag_text)

        x += tag_w

        # 3. Message (dim white, clips at widget edge)
        painter.setPen(QPen(QColor('#A0A0A0'), 1))
        painter.drawText(x, y_base, data['msg'])

        painter.restore()

class GlowingStatusLED(QWidget):
    """High-fidelity phosphor LED with multi-pass glow for hardware status indicators."""

    def __init__(self, text: str, color: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.led_text = text
        self.led_color = QColor(color)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet('background: transparent;')
        self.setFixedSize(32, 28)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        dot_size = 5
        dot_x = (self.width() - dot_size) // 2
        dot_y = 4

        font = get_font('mono', FONT_SIZES['micro'])
        painter.setFont(font)
        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(self.led_text)
        text_x = (self.width() - text_w) // 2
        text_y = dot_y + dot_size + fm.ascent() + 2

        # Glow passes (outer → inner)
        for alpha, spread in [(40, 4), (20, 2)]:
            c = QColor(self.led_color)
            c.setAlpha(alpha)
            painter.setPen(QPen(c, spread))
            painter.fillRect(dot_x - spread, dot_y - spread,
                             dot_size + spread * 2, dot_size + spread * 2, c)
            painter.drawText(text_x, text_y, self.led_text)

        # Sharp core dot
        painter.fillRect(dot_x, dot_y, dot_size, dot_size, self.led_color)

        # Sharp core text
        sharp = QColor(self.led_color)
        sharp.setAlpha(255)
        painter.setPen(QPen(sharp, 0))
        painter.drawText(text_x, text_y, self.led_text)


class PhosphorGlowLabel(QLabel):
    """Custom label with text-mask phosphor glow effect."""
    
    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        
        # Enable transparency for proper glow rendering
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setMinimumHeight(80)
        
        # Glow parameters
        self.glow_intensity = 15
        self.glow_color = QColor(VITREOS_COLORS['purple_dim'])
        self.text_color = QColor(VITREOS_COLORS['purple_dim'])
        
        # Flicker animation state
        self.flicker_timer = QTimer(self)
        self.flicker_timer.timeout.connect(self._flicker_glow)
        self.flicker_timer.start(150)
    
    def _flicker_glow(self) -> None:
        """Subtle flicker animation for phosphor glow."""
        self.glow_intensity = 15 + random.randint(-2, 2)
        self.update()
    
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        display_font = QFont("VT323", 44)
        display_font.setBold(True)
        painter.setFont(display_font)

        text = self.text()
        rect = self.rect()
        base_color = QColor("#A855F7")
        dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]

        # Tighten radial bloom: 1px to 4px, alpha fades with radius
        for radius in range(1, 5):
            base_color.setAlpha(int(150 / (radius * 1.2)))
            painter.setPen(base_color)
            for dx, dy in dirs:
                painter.drawText(rect.translated(dx * radius, dy * radius),
                                 Qt.AlignmentFlag.AlignCenter, text)

        # Final pass: sharp core
        base_color.setAlpha(255)
        painter.setPen(base_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)


class VitreosSidebar(QWidget):
    """
    Tactical sidebar with glowing phosphor logo, pulse log, and terminal footer.
    Fixed 260px width, spans from below global header to bottom of window.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setFixedWidth(310)
        self.log_entries: List[Tuple[str, str, str, str]] = []
        self.cursor_visible = True
        
        self._setup_ui()
        self._start_timers()
    
    def _setup_ui(self) -> None:
        """Build tactical sidebar layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Primary "Living" Logo with Phosphor Glow
        logo_container = self._create_glowing_logo()
        layout.addWidget(logo_container)
        
        # 2. SYSTEM_PULSE.LOG Header
        log_header = self._create_log_header()
        layout.addWidget(log_header)
        
        # 3. Log Feed — QListWidget + native glow delegate
        self.log_list = QListWidget()
        self.log_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.log_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.log_list.setSpacing(0)
        self.log_list.setStyleSheet(
            f'QListWidget {{ background: {VITREOS_COLORS["bg_secondary"]}; border: none; }}'
            ' QListWidget::item { padding: 0px; }'
        )
        self.log_list.setItemDelegate(LogGlowDelegate(self.log_list))
        layout.addWidget(self.log_list, 1)
        
        # 4. Persistent Terminal Footer
        terminal_footer = self._create_terminal_footer()
        layout.addWidget(terminal_footer)
        
        self.setStyleSheet(f"""
            VitreosSidebar {{
                background: {VITREOS_COLORS['bg_secondary']};
            }}
        """)
        
        # Tactical Notch: 3x3px square at Master Intersection (top-right corner)
        self.notch = QLabel(self)
        self.notch.setFixedSize(3, 3)
        self.notch.setStyleSheet(f"background: {VITREOS_COLORS['primary_purple']}; border: none;")
        self.notch.move(self.width() - 3, 0)  # Flush at top-right corner
    
    def _create_glowing_logo(self) -> QWidget:
        """Create phosphor glow logo with metadata and status LEDs."""
        logo_widget = QWidget()
        logo_widget.setStyleSheet(f"background: {VITREOS_COLORS['bg_secondary']};")
        
        layout = QVBoxLayout(logo_widget)
        layout.setContentsMargins(9, 12, 9, 12)
        layout.setSpacing(6)
        
        # Glowing VITREOS logo with text-mask glow
        self.logo_label = PhosphorGlowLabel("VITREOS")
        self.logo_label.setFont(get_font('display', 36))
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.logo_label)
        
        # Metadata subtitle
        subtitle = QLabel("-- HARDWARE MONITOR v2.1 --")
        subtitle.setFont(get_font('mono', FONT_SIZES['micro']))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            color: {VITREOS_COLORS['text_darker']};
            letter-spacing: 1px;
        """)
        layout.addWidget(subtitle)
        
        # Status LEDs (CPU, GPU, MEM, NET) — high-fidelity phosphor glow
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(4)
        indicators_layout.setContentsMargins(0, 0, 0, 0)

        for label, color_key in [('CPU', 'primary_purple'), ('GPU', 'warning_orange'),
                                  ('MEM', 'purple_dim'), ('NET', 'green')]:
            led = GlowingStatusLED(label, VITREOS_COLORS[color_key])
            indicators_layout.addWidget(led, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(indicators_layout)
        
        return logo_widget
    
    def _create_log_header(self) -> QWidget:
        """Create SYSTEM_PULSE.LOG header bar."""
        header = QWidget()
        header.setFixedHeight(24)
        header.setStyleSheet(f"""
            background: {VITREOS_COLORS['bg_titlebar']};
            border-top: 1px solid {VITREOS_COLORS['border_secondary']};
            border-bottom: 1px solid {VITREOS_COLORS['border_secondary']};
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(9, 0, 9, 0)
        
        # Left: Indicator + Title
        left_layout = QHBoxLayout()
        left_layout.setSpacing(6)
        
        dot = QLabel("■")
        dot.setFont(get_font('mono', FONT_SIZES['tiny']))
        dot.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
        left_layout.addWidget(dot)
        
        title = QLabel("SYSTEM_PULSE.LOG")
        title.setFont(get_font('mono', FONT_SIZES['tiny']))
        title.setStyleSheet(f"""
            color: {VITREOS_COLORS['primary_purple']};
            letter-spacing: 1px;
        """)
        left_layout.addWidget(title)
        
        layout.addLayout(left_layout)
        layout.addStretch()
        
        # Right: PID
        pid = QLabel("PID: 31337")
        pid.setFont(get_font('mono', FONT_SIZES['micro']))
        pid.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(pid)
        
        return header
    
    def _create_terminal_footer(self) -> QWidget:
        """Create persistent terminal footer with prompt and metadata."""
        footer_container = QWidget()
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(0)
        
        # Terminal prompt
        prompt_widget = QWidget()
        prompt_widget.setFixedHeight(28)
        prompt_widget.setStyleSheet(f"""
            background: {VITREOS_COLORS['bg_secondary']};
            border-top: 1px solid {VITREOS_COLORS['border_secondary']};
        """)
        
        prompt_layout = QHBoxLayout(prompt_widget)
        prompt_layout.setContentsMargins(9, 0, 9, 0)
        
        self.prompt_label = QLabel("root@vitreos:~#")
        self.prompt_label.setFont(get_font('mono', FONT_SIZES['small']))
        self.prompt_label.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
        prompt_layout.addWidget(self.prompt_label)
        
        self.cursor_label = QLabel("█")
        self.cursor_label.setFont(get_font('mono', FONT_SIZES['small']))
        self.cursor_label.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
        prompt_layout.addWidget(self.cursor_label)
        
        prompt_layout.addStretch()
        
        footer_layout.addWidget(prompt_widget)
        
        # Metadata bar
        metadata_bar = QWidget()
        metadata_bar.setFixedHeight(18)
        metadata_bar.setStyleSheet(f"""
            background: {VITREOS_COLORS['bg_frame']};
            border-top: 1px solid {VITREOS_COLORS['border_dim']};
        """)
        
        metadata_layout = QHBoxLayout(metadata_bar)
        metadata_layout.setContentsMargins(9, 0, 9, 0)
        
        left_label = QLabel("UTF-8 | LF | BASH")
        left_label.setFont(get_font('mono', FONT_SIZES['micro']))
        left_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darkest']};")
        metadata_layout.addWidget(left_label)
        
        metadata_layout.addStretch()
        
        self.time_label = QLabel()
        self.time_label.setFont(get_font('mono', FONT_SIZES['micro']))
        self.time_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darkest']};")
        metadata_layout.addWidget(self.time_label)
        
        footer_layout.addWidget(metadata_bar)
        
        return footer_container
    
    def _start_timers(self) -> None:
        """Start cursor blink, clock, and log simulation timers."""
        # Cursor blink
        self.cursor_timer = QTimer(self)
        self.cursor_timer.timeout.connect(self._toggle_cursor)
        self.cursor_timer.start(530)
        
        # Clock update
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()
        
        # Log simulation engine
        self.log_sim_timer = QTimer(self)
        self.log_sim_timer.timeout.connect(self._simulate_log_entry)
        self._schedule_next_log()
    
    def _toggle_cursor(self) -> None:
        """Toggle cursor visibility."""
        self.cursor_visible = not self.cursor_visible
        self.cursor_label.setVisible(self.cursor_visible)
    
    def _update_clock(self) -> None:
        """Update time display."""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        self.time_label.setText(time_str)
    
    def _schedule_next_log(self) -> None:
        """Schedule next log entry with randomized interval."""
        interval = random.randint(200, 1500)
        self.log_sim_timer.start(interval)
    
    def _simulate_log_entry(self) -> None:
        """Generate varied system log entries from message pool."""
        messages = [
            ('SYS', 'Polling hardware sensors...', 'text_dim'),
            ('GPU', 'Driver version: 546.33 WHQL', 'warning_orange'),
            ('GPU', 'RTX 3060 detected - 12GB VRAM', 'warning_orange'),
            ('MEM', f'RAM usage: {random.randint(60, 85)}.{random.randint(0, 9)}%', 'purple_dim'),
            ('CPU', f'P-core freq: {random.randint(4800, 5200)} MHz', 'cyan'),
            ('CPU', f'Package temp: {random.randint(45, 75)}°C', 'cyan'),
            ('NET', f'Packet loss: {random.choice(["0.0", "0.1", "0.0", "0.0"])}%', 'green'),
            ('NET', f'Latency: {random.randint(8, 25)}ms', 'green'),
            ('WARN', f'CPU temp elevated: {random.randint(85, 95)}°C', 'critical_red'),
            ('FAN', f'RPM fluctuation detected: {random.randint(1200, 2400)} RPM', 'warning_orange'),
            ('SYS', 'Telemetry poll complete', 'text_dim'),
            ('GPU', f'Core clock: {random.randint(1500, 1900)} MHz', 'warning_orange'),
            ('GPU', f'Memory clock: {random.randint(7000, 8000)} MHz', 'warning_orange'),
            ('MEM', f'Available: {random.randint(4, 12)}.{random.randint(0, 9)} GB', 'purple_dim'),
            ('CPU', f'Thread count: {random.choice([16, 16, 16, 24, 32])}', 'cyan'),
            ('NET', f'Download: {random.randint(0, 100)}.{random.randint(0, 9)} Mbps', 'green'),
            ('SYS', 'Hardware scan initiated', 'text_dim'),
            ('FAN', f'GPU fan speed: {random.randint(30, 80)}%', 'warning_orange'),
        ]
        
        level, message, color = random.choice(messages)
        self.append_log(level, message, color)
        
        # Schedule next entry
        self._schedule_next_log()
    
    def append_log(self, level: str, message: str, color: str = 'text_dim') -> None:
        """Append a single log entry (called by 1Hz batch flush)"""
        time_str  = datetime.now().strftime('%H:%M:%S')
        color_hex = VITREOS_COLORS.get(color, VITREOS_COLORS['text_dim'])
        tag_color = _TAG_COLORS.get(level, color_hex)

        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, {
            'time':      time_str,
            'level':     level,
            'msg':       message,
            'color_hex': tag_color,
        })
        self.log_list.addItem(item)

        # Trim to 200 entries to prevent unbounded growth
        if self.log_list.count() > 200:
            self.log_list.takeItem(0)

        # Auto-scroll to bottom (smooth, no flicker)
        vbar = self.log_list.verticalScrollBar()
        if vbar:
            vbar.setValue(vbar.maximum())
    
    def handle_pulse_log_batch(self, batch_text: str) -> None:
        """
        Receives a 1Hz batch of logs from telemetry worker.
        Format: "color1|line1\ncolor2|line2\n..."
        
        This minimizes Qt's setText/append calls and prevents UI lag.
        """
        if not batch_text:
            return
        
        # Parse batch (format: "color|[HH:MM:SS] [LEVEL] message")
        lines = batch_text.split('\n')
        
        for line in lines:
            if '|' not in line:
                continue
            
            color, log_line = line.split('|', 1)
            
            # Extract level from log line (format: "[HH:MM:SS] [LEVEL] message")
            try:
                parts = log_line.split(']', 2)
                if len(parts) >= 3:
                    level = parts[1].strip('[').strip()
                    message = parts[2].strip()
                    
                    # Add to log list (single item, no batch processing overhead)
                    time_str = datetime.now().strftime('%H:%M:%S')
                    color_hex = VITREOS_COLORS.get(color, VITREOS_COLORS['text_dim'])
                    tag_color = _TAG_COLORS.get(level, color_hex)
                    
                    item = QListWidgetItem()
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'time': time_str,
                        'level': level,
                        'msg': message,
                        'color_hex': tag_color,
                    })
                    self.log_list.addItem(item)
            except Exception as e:
                # Fallback: add raw line
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, {
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'level': 'SYS',
                    'msg': log_line,
                    'color_hex': VITREOS_COLORS['text_dim'],
                })
                self.log_list.addItem(item)
        
        # Trim to 200 entries
        while self.log_list.count() > 200:
            self.log_list.takeItem(0)
        
        # Auto-scroll to bottom (smooth, no flicker)
        vbar = self.log_list.verticalScrollBar()
        if vbar:
            vbar.setValue(vbar.maximum())
