#!/usr/bin/env python3
# pyright: reportUnusedImport=false
"""
Vitreos - High-End System Sentinel
'Intelligence through Transparency.'
Advanced Desktop Interface with Liquid Glass Aesthetics
"""
import sentry_sdk

sentry_sdk.init(
    dsn="https://0b52971c70bd329a23fa7f76920ec924@o4511182257324032.ingest.us.sentry.io/4511191659839488",  # Get this from Settings > Projects > Vitreos > Client Keys
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    # This ensures Sentry links the error to the correct commit in GitHub
    environment="production", 
)
import sys
import json
import os
import time
import threading
import psutil
import requests
import platform
import winreg
import subprocess
import ctypes
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple, Deque, TYPE_CHECKING, Union, cast
from collections import deque
import statistics

# TYPE_CHECKING block for strict mode compliance
if TYPE_CHECKING:
    from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QThread, QObject, QEvent
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                QLabel, QPushButton, QFrame, QGridLayout,
                                QTextEdit, QLineEdit, QCheckBox, QGroupBox,
                                QProgressBar, QSystemTrayIcon, QMenu,
                                QStatusBar, QMessageBox, QDialog,
                                QTableWidget, QTableWidgetItem, QHeaderView, QPlainTextEdit)
    from PyQt6.QtGui import (QIcon, QPixmap, QPalette, QColor,
                           QLinearGradient, QBrush, QPainter, QPen,
                           QPaintEvent, QMouseEvent, QCloseEvent, QFont)
    import pynvml  # type: ignore

# PyQt imports first (before logging handler definition)
PYQT6_AVAILABLE: bool = False
try:
    from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QThread, QObject, QEvent
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                QLabel, QPushButton, QFrame, QGridLayout,
                                QTextEdit, QLineEdit, QCheckBox, QGroupBox,
                                QProgressBar, QSystemTrayIcon, QMenu,
                                QStatusBar, QMessageBox, QDialog,
                                QTableWidget, QTableWidgetItem, QHeaderView, QPlainTextEdit)
    from PyQt6.QtGui import (QIcon, QPixmap, QPalette, QColor,
                           QLinearGradient, QBrush, QPainter, QPen,
                           QPaintEvent, QMouseEvent, QCloseEvent, QFont)
    PYQT6_AVAILABLE: bool = True  # type: ignore[no-redef]
except ImportError:
    pass

# Configure logging BEFORE creating handler
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Logging handler with PyQt signal support (after UI initialization)
class UILoggingHandler(QObject, logging.Handler):
    """Logging handler that emits PyQt signals for UI display"""
    
    log_signal = pyqtSignal(str)
    
    def __init__(self) -> None:
        QObject.__init__(self)
        logging.Handler.__init__(self)
        self.setFormatter(logging.Formatter('%(levelname)-8s | %(message)s'))
    
    def emit(self, record: logging.LogRecord) -> None:
        """Format record and emit PyQt signal for UI thread to display"""
        try:
            msg = self.format(record)
            # Try to emit signal if main window exists
            try:
                self.log_signal.emit(msg)
            except RuntimeError:
                # Signal may fail if called before main loop starts
                pass
        except Exception:
            self.handleError(record)

# Create and register the UI logging handler
ui_log_handler = UILoggingHandler()
logger.addHandler(ui_log_handler)

# Resource path helper for PyInstaller bundles
def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works in development and PyInstaller bundles"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

# Try to import advanced GPU monitoring
NVML_AVAILABLE: bool = False
try:
    import pynvml  # type: ignore
    NVML_AVAILABLE: bool = True  # type: ignore[no-redef]
    if PYQT6_AVAILABLE:
        logger.info("GPU monitoring (NVML) imports successful")
except ImportError:
    if PYQT6_AVAILABLE:
        logger.warning("GPU monitoring (NVML) not available - using fallback mode")

# Try to import WMI for security monitoring
WMI_AVAILABLE: bool = False
try:
    import wmi  # type: ignore[reportMissingImports]
    WMI_AVAILABLE: bool = True  # type: ignore[no-redef]
except ImportError:
    logger.warning("WMI module not available - USB detection will use PowerShell fallback")


from vitreos_shield import VitreosShield
from vitreos_tweaks import SystemTweaker
# Type alias for configuration dictionary
ConfigDict = Dict[str, Union[str, bool]]
# CCE Process Watchdog Blacklist
BLACKLISTED_PROCESSES = [
    'cheatengine-x86_64.exe',
    'cheat engine.exe',
    'wireshark.exe',
    'x64dbg.exe',
    'ollydbg.exe',
    'ida.exe',
    'ida64.exe',
    'processhacker.exe'
]

# Smart Blocklists for Purge Protocol
CRITICAL_SYSTEM_PROCESSES = {
    'svchost.exe', 'explorer.exe', 'system', 'registry', 'smss.exe',
    'csrss.exe', 'wininit.exe', 'services.exe', 'lsass.exe', 'winlogon.exe',
    'fontdrvhost.exe', 'dwm.exe', 'spoolsv.exe', 'taskhostw.exe',
    'runtimebroker.exe', 'searchapp.exe', 'startmenuexperiencehost.exe',
    'sihost.exe', 'conhost.exe', 'cmd.exe', 'python.exe', 'pythonw.exe',
    'system idle process', 'memory compression', 'wmiapsrv.exe',
    'ctfmon.exe', 'securityhealthservice.exe', 'dashost.exe', 'dllhost.exe'
}
PROTECTED_APPS = {
    'discord.exe', 'spotify.exe', 'steam.exe', 'steamwebhelper.exe',
    'chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe',
    'r5apex.exe', 'obs64.exe', 'code.exe', 'discordptb.exe', 'discordcanary.exe'
}
KNOWN_BLOATWARE = {
    'lghub.exe', 'lghub_agent.exe', 'lghub_updater.exe', 'icue.exe',
    'corsair.service.exe', 'corsair.service.displayadapter.exe', 
    'synapse3.exe', 'razercentral.exe', 'rzsynapse.exe', 'rzsdkservice.exe',
    'wallpaper32.exe', 'wallpaper64.exe', 'epicgameslauncher.exe',
    'eadesktop.exe', 'eabackgroundservice.exe', 'battle.net.exe',
    'agent.exe', 'riotclientservices.exe', 'gog galaxy.exe',
    'overwolf.exe', 'overwolflauncher.exe', 'onedrive.exe',
    'dropbox.exe', 'googledrivefs.exe', 'adobeupdate.exe', 
    'creative cloud.exe', 'ccxprocess.exe', 'acrotray.exe', 'adobeipcbroker.exe',
    'armourycrateservice.exe', 'lightingservice.exe', 'asuscertservice.exe', 
    'gamingservices.exe', 'ccleaner.exe', 'mcafee.exe', 'norton.exe', 
    'webex.exe', 'skype.exe', 'teams.exe', 'zoom.exe', 'yourphone.exe', 
    'xboxapp.exe', 'gamebar.exe', 'nzxtcam.exe', 'cam_v4.exe',
    'nahimic.exe', 'rtss.exe', 'originwebhelperui.exe', 'widgets.exe',
    'msedgewebview2.exe', 'jusched.exe', 'steelseriesgg.exe', 'steelseriesengine.exe'
}
PERFORMANCE_TARGETS = {
    'r5apex.exe', 'csgo.exe', 'valorant.exe', 'overwatch.exe', 
    'cod.exe', 'photoshop.exe', 'premiere.exe', 'code.exe', 'devenv.exe'
}
EFFICIENCY_TARGETS = {
    'discord.exe', 'spotify.exe', 'chrome.exe', 'firefox.exe', 
    'msedge.exe', 'brave.exe', 'steam.exe', 'steamwebhelper.exe', 
    'epicgameslauncher.exe', 'nvcontainer.exe', 'slack.exe'
}


@dataclass
class SystemStats:
    cpu_temp: float = 0.0
    cpu_usage: float = 0.0
    gpu_temp: float = 0.0
    gpu_usage: float = 0.0
    gpu_vram_used: float = 0.0
    gpu_vram_total: float = 0.0
    gpu_vram_percent: float = 0.0
    gpu_fan_speed: float = 0.0
    gpu_power_draw: float = 0.0
    thermal_prediction: float = 0.0
    ram_usage: float = 0.0
    disk_usage: float = 0.0
    network_speed: float = 0.0
    network_jitter: float = 0.0
    power_draw: float = 0.0

@dataclass
class SecurityEvent:
    timestamp: str
    event_type: str
    description: str
    severity: str


class SparklineWidget(QWidget):
    """A compact widget for rendering sparkline graphs."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(40)
        self.data: Deque[float] = deque(maxlen=60)

    def add_point(self, value: float) -> None:
        """Add a new data point and refresh the graph."""
        self.data.append(value)
        self.update()  # Trigger a repaint

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Render segmented LED progress bar with ghost background."""
        if not self.data:
            return
        painter = QPainter(self)
        rect = self.rect()
        percentage = self.data[-1] / 100.0 if self.data else 0.0
        
        # Determine color based on value
        value = self.data[-1]
        active_color = QColor("#ff8c00") if value > 70 else QColor("#bc13fe")
        ghost_color = QColor(188, 19, 254, 26)  # 10% opacity purple
        
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw segments with 2px width and 1px gap
        segment_width = 2
        gap = 1
        step = segment_width + gap
        fill_width = int(rect.width() * percentage)
        
        for x in range(0, rect.width(), step):
            if x + segment_width <= fill_width:
                # Active segment
                painter.setBrush(QBrush(active_color))
            else:
                # Ghost segment
                painter.setBrush(QBrush(ghost_color))
            painter.drawRect(x, 0, segment_width, rect.height())

class LiquidGlassCard(QFrame):
    """Professional liquid glass card with physics-based styling"""
    
    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.title: str = title
        self.setMinimumSize(200, 150)
        
        # Glass styling properties
        self.glass_color: QColor = QColor(255, 255, 255, 12)
        self.border_color: QColor = QColor(255, 255, 255, 25)
        self.bevel_color: QColor = QColor(255, 255, 255, 25)
        self.sparkline: SparklineWidget = SparklineWidget()
        
        # UI components - typed explicitly
        self.title_label: QLabel
        self.value_label: QLabel
        self.unit_label: QLabel
        self.status_label: QLabel
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup the card layout and styling"""
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Title label with professional styling
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #ffffff
                font-size: 14px
                font-weight: 600
                text-transform: uppercase
                letter-spacing: 0.5px
            }
        """)
        
        # Value display
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet("""
            QLabel {
                color: #00f2ff
                font-size: 32px
                font-weight: 700
                font-family: 'Segoe UI', Arial, sans-serif
            }
        """)
        
        # Unit label
        self.unit_label = QLabel("")
        self.unit_label.setStyleSheet("""
            QLabel {
                color: #888888
                font-size: 12px
                font-weight: 400
            }
        """)
        
        # Status indicator
        self.status_label = QLabel("Normal")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #4ade80
                font-size: 11px
                font-weight: 500
            }
        """)
        
        # Add widgets to layout
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.unit_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.sparkline)
        
        # Set frame properties for glass effect
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setAutoFillBackground(False)
        
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
        
    def update_value(self, value: Union[float, int, str, None], unit: str = "", status: str = "Normal", color: str = "#00f2ff") -> None:
        """Update card with new values - handles float or string input"""
        try:
            # Convert value to float safely
            if isinstance(value, str):
                val_float: float = float(value)
            else:
                val_float = float(value) if value is not None else 0.0
            
            # Format for display
            self.value_label.setText(f"{val_float:.1f}")
            self.sparkline.add_point(val_float)
        except (ValueError, TypeError):
            self.value_label.setText(str(value) if value is not None else "0")
        
        self.unit_label.setText(unit)
        self.status_label.setText(status)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {color}
                font-size: 32px
                font-weight: 700
                font-family: 'Segoe UI', Arial, sans-serif
            }}
        """)

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
        
        # Draw each core as vertical segmented LED stack
        for row in range(4):
            for col in range(4):
                idx = row * 4 + col
                load = self.thread_loads[idx]
                
                # Cell position
                x = col * cell_w + 5
                y = row * cell_h + 5
                bar_width = cell_w - 10
                bar_height = cell_h - 10
                
                # Determine color based on load
                active_color = QColor("#ff8c00") if load > 70 else QColor("#bc13fe")
                ghost_color = QColor(188, 19, 254, 26)  # 10% opacity purple
                
                # Draw vertical segments (8 segments per core)
                num_segments = 8
                segment_height = 2
                gap = 1
                step = segment_height + gap
                
                filled_segments = int((load / 100.0) * num_segments)
                
                painter.setPen(Qt.PenStyle.NoPen)
                
                for seg in range(num_segments):
                    seg_y = y + bar_height - (seg + 1) * step
                    
                    if seg < filled_segments:
                        # Active segment
                        painter.setBrush(QBrush(active_color))
                    else:
                        # Ghost segment
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
        self.usage = usage
        if usage >= 85 and not self.warning_active:
            self.warning_active = True
            self.flicker_timer.start(500)
        elif usage < 85 and self.warning_active:
            self.warning_active = False
            self.flicker_timer.stop()
        self.update()
    
    def toggle_flicker(self) -> None:
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
        
        # Determine color based on usage
        ring_color = QColor("#ff8c00") if (self.warning_active and self.flicker_state) else (QColor("#ff8c00") if self.usage > 70 else QColor("#bc13fe"))
        ghost_color = QColor(188, 19, 254, 26)  # 10% opacity purple
        
        # Draw ghost ring (background)
        pen = QPen(ghost_color, 3)
        pen.setDashPattern(cast(Any, [2, 4]))  # type: ignore[reportUnknownMemberType]
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Draw active arc
        span_angle = int((self.usage / 100.0) * 360 * 16)
        pen = QPen(ring_color, 3)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawArc(center_x - radius + 10, center_y - radius + 10, (radius - 10) * 2, (radius - 10) * 2, 90 * 16, -span_angle)
        
        # Center text
        painter.setPen(QPen(ring_color))
        font: QFont = painter.font()
        font.setPointSize(14)
        font.setFamily("Courier New")
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.usage)}%")

class SystemPulseLog(QWidget):
    """Hyper-dense Cyberdeck HUD sidebar with 1:1 Figma fidelity."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(240)  # Increased from 220 to 240 for breathing room
        self.log_messages: Deque[str] = deque(maxlen=100)
        self.led_states: Dict[str, str] = {'CPU': '#bc13fe', 'MEM': '#bc13fe', 'GPU': '#ff8c00', 'NET': '#00ff00'}
        self.setStyleSheet("background-color: #121214; border-right: 1px solid #2a2a2e;")
        
    def add_log(self, message: str) -> None:
        """Add log with unified format: [TIMESTAMP] [TAG] MESSAGE"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Extract tag if present, otherwise default to INFO
        if ' - ' in message and ' - ' in message:
            parts = message.split(' - ', 1)
            level = parts[0].strip()
            msg_content = parts[1] if len(parts) > 1 else message
            
            # Map log levels to tags
            tag_map = {
                'INFO': '[INFO]',
                'DEBUG': '[DEBUG]',
                'WARNING': '[WARN]',
                'ERROR': '[WARN]',
                'CRITICAL': '[WARN]'
            }
            tag = tag_map.get(level, '[INFO]')
        else:
            # Parse existing tags from message
            if '[' in message and ']' in message:
                tag_start = message.find('[')
                tag_end = message.find(']', tag_start)
                if tag_end > tag_start:
                    tag = message[tag_start:tag_end+1]
                    msg_content = message[tag_end+1:].strip()
                else:
                    tag = '[INFO]'
                    msg_content = message
            else:
                tag = '[INFO]'
                msg_content = message
        
        # Unified format with fixed-width tag alignment
        formatted_msg = f"[{timestamp}] {tag.ljust(7)} {msg_content}"
        self.log_messages.append(formatted_msg)
        self.update()
    
    def paintEvent(self, a0: QPaintEvent | None) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        painter.fillRect(rect, QColor("#121214"))
        y_offset = 0
        
        # Sub-Header: ■ SYSTEM_PULSE.LOG and PID
        painter.setPen(QColor(188, 19, 254, 153))
        header_font: QFont = QFont("Consolas", 8)
        painter.setFont(header_font)
        painter.drawText(5, y_offset + 12, "■ SYSTEM_PULSE.LOG")
        painter.drawText(rect.width() - 70, y_offset + 12, "PID: 31337")
        y_offset += 18
        
        # Separator
        painter.setPen(QColor("#2a2a2e"))
        painter.drawLine(0, y_offset, rect.width(), y_offset)
        y_offset += 8
        
        # Logo with Neon Glow and Scanlines (CENTERED)
        logo_y_start = y_offset
        logo_height = 35
        
        # Scanlines behind logo - FULL WIDTH
        painter.setPen(QColor(255, 255, 255, 13))
        for i in range(logo_y_start, logo_y_start + logo_height, 2):
            painter.drawLine(0, i, rect.width(), i)
        
        # Calculate center position for logo
        logo_text = "VITREOS"
        logo_font: QFont = QFont("Consolas", 16, QFont.Weight.Bold)
        painter.setFont(logo_font)
        fm = painter.fontMetrics()
        logo_width = fm.horizontalAdvance(logo_text)
        logo_x = (rect.width() - logo_width) // 2
        
        # Neon glow effect (multiple passes)
        for blur in [8, 6, 4, 2]:
            painter.setPen(QColor(188, 19, 254, 30))
            painter.drawText(logo_x - blur//2, y_offset + 22, logo_text)
            painter.drawText(logo_x + blur//2, y_offset + 22, logo_text)
        
        # Main logo text (CENTERED)
        painter.setPen(QColor("#bc13fe"))
        painter.drawText(logo_x, y_offset + 22, logo_text)
        y_offset += logo_height
        
        # Status LEDs (6x6px, CENTERED, labels below)
        led_size = 6
        led_spacing = 20
        total_led_width = (len(self.led_states) - 1) * led_spacing + led_size
        led_start_x = (rect.width() - total_led_width) // 2
        led_y = y_offset
        
        for idx, (name, color) in enumerate(self.led_states.items()):
            led_x = led_start_x + idx * led_spacing
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(led_x, led_y, led_size, led_size)
        
        # LED labels below squares (CENTERED)
        painter.setPen(QColor("#888888"))
        label_font: QFont = QFont("Consolas", 6)
        painter.setFont(label_font)
        for idx, name in enumerate(self.led_states.keys()):
            led_x = led_start_x + idx * led_spacing
            # Center each label under its LED
            label_width = len(name) * 4
            label_x = led_x + (led_size - label_width) // 2
            painter.drawText(label_x, led_y + led_size + 9, name)
        y_offset += 20
        
        # Separator
        painter.setPen(QColor("#2a2a2e"))
        painter.drawLine(0, y_offset, rect.width(), y_offset)
        y_offset += 3
        
        # Semantic Log Feed (Ultra-high density)
        log_font: QFont = QFont("Consolas", 8)
        painter.setFont(log_font)
        line_height = 11
        
        for msg in list(self.log_messages)[-35:]:
            if y_offset > rect.height() - 45:
                break
            
            # Parse and render with semantic tags
            self._render_log_line(painter, msg, 3, y_offset, rect.width())
            y_offset += line_height
        
        # Terminal Footer
        footer_y = rect.height() - 38
        painter.setPen(QColor("#2a2a2e"))
        painter.drawLine(0, footer_y, rect.width(), footer_y)
        footer_y += 3
        
        # Prompt with solid cursor
        painter.setPen(QColor("#bc13fe"))
        prompt_font: QFont = QFont("Consolas", 8)
        painter.setFont(prompt_font)
        painter.drawText(5, footer_y + 12, "root@vitreos:~#")
        painter.fillRect(98, footer_y + 3, 8, 11, QColor("#bc13fe"))
        footer_y += 18
        
        # Status bar separator
        painter.setPen(QColor("#2a2a2e"))
        painter.drawLine(0, footer_y, rect.width(), footer_y)
        footer_y += 2
        
        # Metadata footer
        painter.setPen(QColor("#666666"))
        footer_font: QFont = QFont("Consolas", 7)
        painter.setFont(footer_font)
        painter.drawText(5, footer_y + 10, "UTF-8 | LF | BASH")
        painter.drawText(rect.width() - 50, footer_y + 10, datetime.now().strftime("%H:%M:%S"))
    
    def _render_log_line(self, painter: QPainter, msg: str, x: int, y: int, width: int) -> None:
        """Render a single log line with semantic solid block tags (Figma style)."""
        # Extract timestamp and dim it
        if msg.startswith('[') and ']' in msg:
            timestamp_end = msg.find(']') + 1
            timestamp = msg[:timestamp_end]
            remaining = msg[timestamp_end:].strip()
            
            # Render dimmed timestamp
            painter.setPen(QColor(188, 19, 254, 102))
            painter.drawText(x, y, timestamp)
            x_offset = x + len(timestamp) * 6 + 3
        else:
            remaining = msg
            x_offset = x
        
        # Extract tag and message
        if remaining.startswith('[') and ']' in remaining:
            tag_end = remaining.find(']') + 1
            tag = remaining[:tag_end]
            message = remaining[tag_end:].strip()
        else:
            tag = ''
            message = remaining
        
        # Render solid block tags (Figma style)
        if tag in ['[INFO]', '[DEBUG]']:
            # Dark purple background, white text
            painter.fillRect(x_offset, y - 9, 42, 11, QColor(60, 10, 80))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(x_offset + 2, y, tag.ljust(7))
            x_offset += 46
            
            painter.setPen(QColor("#cccccc"))
            painter.drawText(x_offset, y, message)
        
        elif tag == '[WARN]':
            # Red background, white text
            painter.fillRect(x_offset, y - 9, 42, 11, QColor("#ff0000"))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(x_offset + 2, y, tag.ljust(7))
            x_offset += 46
            
            painter.setPen(QColor("#cccccc"))
            painter.drawText(x_offset, y, message)
        
        elif tag == '[FAN]':
            # Orange background, white text
            painter.fillRect(x_offset, y - 9, 42, 11, QColor("#ff8c00"))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(x_offset + 2, y, tag.ljust(7))
            x_offset += 46
            
            painter.setPen(QColor("#cccccc"))
            painter.drawText(x_offset, y, message)
        
        elif tag == '[OK]':
            # Green background, black text
            painter.fillRect(x_offset, y - 9, 42, 11, QColor("#00ff00"))
            painter.setPen(QColor("#000000"))
            painter.drawText(x_offset + 2, y, tag.ljust(7))
            x_offset += 46
            
            painter.setPen(QColor("#cccccc"))
            painter.drawText(x_offset, y, message)
        
        elif tag in ['[CPU]', '[SYS]', '[NET]', '[GPU]', '[SEC]']:
            # Purple outlined text
            painter.setPen(QColor("#bc13fe"))
            painter.drawText(x_offset, y, tag.ljust(7))
            x_offset += 46
            
            painter.setPen(QColor("#cccccc"))
            painter.drawText(x_offset, y, message)
        
        else:
            # Default gray text
            painter.setPen(QColor("#888888"))
            painter.drawText(x_offset, y, remaining)

class VitreosModule(QFrame):
    """Windows-style module container with header bar and decorative controls."""
    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.title = title
        self.content_widget: Optional[QWidget] = None
        self.hazard_sticker: Optional[QLabel] = None
        self.is_minimized: bool = False
        self.setup_ui()
        
    def setup_ui(self) -> None:
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            VitreosModule {
                background-color: #121214
                border: 1px solid rgba(188, 19, 254, 0.5)
                border-radius: 0px
            }
            VitreosModule:hover {
                border: 1px solid rgba(188, 19, 254, 1.0)
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header bar
        header = QFrame()
        header.setFixedHeight(22)
        header.setStyleSheet("""
            QFrame {
                background-color: #1a1a1e
                border-bottom: 1px solid #bc13fe
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(5, 0, 5, 0)
        header_layout.setSpacing(0)
        
        # Title with :: prefix
        title_label = QLabel(f":: {self.title}")
        title_label.setStyleSheet("""
            QLabel {
                color: #bc13fe
                font-family: 'Consolas', monospace
                font-size: 9pt
                font-weight: bold
                background: transparent
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Hazard sticker (initially hidden)
        self.hazard_sticker = QLabel("")
        self.hazard_sticker.setStyleSheet("""
            QLabel {
                background: transparent
                font-family: 'Consolas', monospace
                font-size: 7pt
                font-weight: bold
                padding: 2px 4px
                margin-right: 5px
            }
        """)
        self.hazard_sticker.hide()
        header_layout.addWidget(self.hazard_sticker)
        
        # Decorative bracketed controls
        btn_minimize = QLabel("[_]")
        btn_minimize.setStyleSheet("color: #666666; font-family: 'Consolas'; font-size: 8pt; background: transparent;")
        btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_minimize.mousePressEvent = lambda e: self.toggle_minimize()  # type: ignore
        
        btn_close = QLabel("[X]")
        btn_close.setStyleSheet("color: #666666; font-family: 'Consolas'; font-size: 8pt; background: transparent;")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.mousePressEvent = lambda e: self.close_module()  # type: ignore
        
        header_layout.addWidget(btn_minimize)
        header_layout.addSpacing(5)
        header_layout.addWidget(btn_close)
        
        layout.addWidget(header)
        
        # Content area
        self.content_container = QWidget()
        self.content_container.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(5)
        
        layout.addWidget(self.content_container)
    
    def set_content(self, widget: QWidget) -> None:
        """Set the content widget for this module."""
        self.content_widget = widget
        self.content_layout.addWidget(widget)
    
    def toggle_minimize(self) -> None:
        """Toggle minimize/maximize state."""
        if self.content_container:  # type: ignore[reportUnnecessaryComparison]
            self.is_minimized = not self.is_minimized
            self.content_container.setVisible(not self.is_minimized)
            logger.info(f"[SYS] Module {self.title} {'minimized' if self.is_minimized else 'restored'}")
    
    def close_module(self) -> None:
        """Hide the module and log to pulse."""
        self.hide()
        logger.warning(f"[SYS] Module {self.title} detached from grid")
    
    def show_hazard_sticker(self, text: str, bg_color: str, text_color: str = "#000000") -> None:
        """Display a hazard sticker with custom styling."""
        if self.hazard_sticker:  # type: ignore[reportUnnecessaryComparison]
            self.hazard_sticker.setText(text)
            self.hazard_sticker.setStyleSheet(f"""
                QLabel {{
                    background: {bg_color}
                    color: {text_color}
                    font-family: 'Consolas', monospace
                    font-size: 7pt
                    font-weight: bold
                    padding: 2px 4px
                    margin-right: 5px
                    border: 1px solid {text_color}
                }}
            """)
            self.hazard_sticker.show()
    
    def hide_hazard_sticker(self) -> None:
        """Hide the hazard sticker."""
        if self.hazard_sticker:  # type: ignore[reportUnnecessaryComparison]
            self.hazard_sticker.hide()

class CPUMonitorModule(QWidget):
    """CPU monitoring with 16-core grid, load bar, clock, and power."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.cpu_thread_matrix = CPUThreadMatrix()
        self.setStyleSheet("background: transparent;")
        self.parent_module: Optional[VitreosModule] = None
        self.avg_clock: float = 0.0
        self.setup_ui()
        
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Thread matrix
        layout.addWidget(self.cpu_thread_matrix)
        
        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(5)
        
        self.load_label = QLabel("LOAD: 0%")
        self.load_label.setStyleSheet("color: #00f2ff; font-family: 'Consolas'; font-size: 10pt; font-weight: bold; background: transparent;")
        
        self.clock_label = QLabel("CLOCK: 0 MHz")
        self.clock_label.setStyleSheet("color: rgba(188, 19, 254, 0.6); font-family: 'Consolas'; font-size: 8pt; background: transparent;")
        
        self.power_label = QLabel("POWER: 0 W")
        self.power_label.setStyleSheet("color: rgba(255, 140, 0, 0.6); font-family: 'Consolas'; font-size: 8pt; background: transparent;")
        
        stats_layout.addWidget(self.load_label, 0, 0)
        stats_layout.addWidget(self.clock_label, 0, 1)
        stats_layout.addWidget(self.power_label, 1, 0, 1, 2)
        
        layout.addLayout(stats_layout)
    
    def update_stats(self, cpu_usage: float, cpu_temp: float, cpu_loads: List[float], cpu_clock: float = 0.0) -> None:
        self.cpu_thread_matrix.update_threads(cpu_loads, cpu_temp)
        self.load_label.setText(f"LOAD: {cpu_usage:.1f}%")
        
        # Update clock display and hazard sticker
        if cpu_clock > 0:
            self.avg_clock = cpu_clock
            self.clock_label.setText(f"CLOCK: {int(cpu_clock)} MHz")
            
            # Show OVERCLOCKED sticker if clock > 5000 MHz
            if self.parent_module is not None and cpu_clock > 5000:  # type: ignore[reportUnnecessaryComparison]
                self.parent_module.show_hazard_sticker("[ OVERCLOCKED ]", "#ffff00", "#000000")
            elif self.parent_module:  # type: ignore[reportUnnecessaryComparison]
                self.parent_module.hide_hazard_sticker()

class GPUMonitorModule(QWidget):
    """GPU monitoring with circular HUD, VRAM, clocks, and temperature."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.gpu_circular_hud = GPUCircularHUD()
        self.setStyleSheet("background: transparent;")
        self.parent_module: Optional[VitreosModule] = None
        self.setup_ui()
        
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        layout.addWidget(self.gpu_circular_hud)
        
        # Stats
        stats_layout = QGridLayout()
        stats_layout.setSpacing(5)
        
        self.vram_label = QLabel("VRAM: 0%")
        self.vram_label.setStyleSheet("color: #00f2ff; font-family: 'Consolas'; font-size: 10pt; font-weight: bold; background: transparent;")
        
        self.temp_label = QLabel("TEMP: 0°C")
        self.temp_label.setStyleSheet("color: rgba(255, 140, 0, 0.6); font-family: 'Consolas'; font-size: 8pt; background: transparent;")
        
        self.clock_label = QLabel("CLOCK: 0 MHz")
        self.clock_label.setStyleSheet("color: rgba(188, 19, 254, 0.6); font-family: 'Consolas'; font-size: 8pt; background: transparent;")
        
        stats_layout.addWidget(self.vram_label, 0, 0)
        stats_layout.addWidget(self.temp_label, 0, 1)
        stats_layout.addWidget(self.clock_label, 1, 0, 1, 2)
        
        layout.addLayout(stats_layout)
    
    def update_stats(self, gpu_usage: float, gpu_temp: float, vram_percent: float) -> None:
        self.gpu_circular_hud.update_usage(gpu_usage)
        self.vram_label.setText(f"VRAM: {vram_percent:.1f}%")
        self.temp_label.setText(f"TEMP: {gpu_temp:.0f}°C")
        
        # Show HOT sticker if temp > 82°C
        if self.parent_module is not None and gpu_temp > 82:  # type: ignore[reportUnnecessaryComparison]
            self.parent_module.show_hazard_sticker("[ HOT ]", "#ff0000", "#000000")
        elif self.parent_module:  # type: ignore[reportUnnecessaryComparison]
            self.parent_module.hide_hazard_sticker()

class MemoryArrayModule(QWidget):
    """Memory monitoring with DIMM visualization and capacity stats."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setup_ui()
        
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.usage_label = QLabel("RAM: 0%")
        self.usage_label.setStyleSheet("color: #00f2ff; font-family: 'Consolas'; font-size: 12pt; font-weight: bold; background: transparent;")
        layout.addWidget(self.usage_label)
        
        self.capacity_label = QLabel("CAPACITY: 0 GB / 0 GB")
        self.capacity_label.setStyleSheet("color: rgba(188, 19, 254, 0.6); font-family: 'Consolas'; font-size: 8pt; background: transparent;")
        layout.addWidget(self.capacity_label)
        
        layout.addStretch()
    
    def update_stats(self, ram_usage: float) -> None:
        self.usage_label.setText(f"RAM: {ram_usage:.1f}%")
        import psutil
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        used_gb = mem.used / (1024**3)
        self.capacity_label.setText(f"CAPACITY: {used_gb:.1f} GB / {total_gb:.1f} GB")

class DiskArrayModule(QWidget):
    """Storage monitoring with drive list and usage bars."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setup_ui()
        
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.disk_label = QLabel("DISK: 0%")
        self.disk_label.setStyleSheet("color: #00f2ff; font-family: 'Consolas'; font-size: 12pt; font-weight: bold; background: transparent;")
        layout.addWidget(self.disk_label)
        
        self.drives_label = QLabel("DRIVES: Scanning...")
        self.drives_label.setStyleSheet("color: rgba(188, 19, 254, 0.6); font-family: 'Consolas'; font-size: 8pt; background: transparent;")
        layout.addWidget(self.drives_label)
        
        layout.addStretch()
    
    def update_stats(self, disk_usage: float) -> None:
        self.disk_label.setText(f"DISK: {disk_usage:.1f}%")

class NetworkInterfaceModule(QWidget):
    """Network monitoring with waveform and bandwidth stats."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.network_waveform = NetworkWaveform()
        self.setStyleSheet("background: transparent;")
        self.setup_ui()
        
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        layout.addWidget(self.network_waveform)
        
        self.stats_label = QLabel("NET: 0.00 Mbps")
        self.stats_label.setStyleSheet("color: #00f2ff; font-family: 'Consolas'; font-size: 10pt; font-weight: bold; background: transparent;")
        layout.addWidget(self.stats_label)
    
    def update_stats(self, speed_mbps: float) -> None:
        """Update network stats with current speed in Mbps."""
        self.network_waveform.add_point(speed_mbps)
        self.stats_label.setText(f"NET: {speed_mbps:.2f} Mbps")

class ThermalControlModule(QWidget):
    """Thermal monitoring with fan tachometers and prediction."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.cpu_fan_value: float = 0.0
        self.gpu_fan_value: float = 0.0
        self.parent_module: Optional[VitreosModule] = None
        self.setup_ui()
        
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.cpu_temp_label = QLabel("CPU: 0°C")
        self.cpu_temp_label.setStyleSheet("color: #00f2ff; font-family: 'Consolas'; font-size: 11pt; font-weight: bold; background: transparent;")
        layout.addWidget(self.cpu_temp_label)
        
        self.gpu_temp_label = QLabel("GPU: 0°C")
        self.gpu_temp_label.setStyleSheet("color: #ff8c00; font-family: 'Consolas'; font-size: 11pt; font-weight: bold; background: transparent;")
        layout.addWidget(self.gpu_temp_label)
        
        self.prediction_label = QLabel("PREDICT: 0°C")
        self.prediction_label.setStyleSheet("color: rgba(188, 19, 254, 0.6); font-family: 'Consolas'; font-size: 8pt; background: transparent;")
        layout.addWidget(self.prediction_label)
        
        # Fan tachometer bars
        fan_container = QWidget()
        fan_container.setStyleSheet("background: transparent;")
        fan_layout = QVBoxLayout(fan_container)
        fan_layout.setSpacing(3)
        
        cpu_fan_label = QLabel("CPU FAN:")
        cpu_fan_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-family: 'Consolas'; font-size: 8pt; background: transparent;")
        fan_layout.addWidget(cpu_fan_label)
        
        self.cpu_fan_bar = ThermalBar()
        fan_layout.addWidget(self.cpu_fan_bar)
        
        gpu_fan_label = QLabel("GPU FAN:")
        gpu_fan_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-family: 'Consolas'; font-size: 8pt; background: transparent;")
        fan_layout.addWidget(gpu_fan_label)
        
        self.gpu_fan_bar = ThermalBar()
        fan_layout.addWidget(self.gpu_fan_bar)
        
        layout.addWidget(fan_container)
        layout.addStretch()
    
    def update_stats(self, cpu_temp: float, gpu_temp: float, prediction: float, cpu_fan: float = 0.0, gpu_fan: float = 0.0) -> None:
        self.cpu_temp_label.setText(f"CPU: {cpu_temp:.0f}°C")
        self.gpu_temp_label.setText(f"GPU: {gpu_temp:.0f}°C")
        self.prediction_label.setText(f"PREDICT: {prediction:.0f}°C")
        
        # Update fan bars
        if cpu_fan > 0:
            self.cpu_fan_value = cpu_fan
        else:
            self.cpu_fan_value = min(100, cpu_temp * 1.2)
            
        if gpu_fan > 0:
            self.gpu_fan_value = gpu_fan
        else:
            self.gpu_fan_value = min(100, gpu_temp * 1.2)
            
        self.cpu_fan_bar.set_value(self.cpu_fan_value)
        self.gpu_fan_bar.set_value(self.gpu_fan_value)
        
        # Show MAX_RPM sticker if either fan is at 100%
        if self.parent_module is not None and (self.cpu_fan_value >= 100 or self.gpu_fan_value >= 100):  # type: ignore[reportUnnecessaryComparison]
            self.parent_module.show_hazard_sticker("[ MAX_RPM ]", "#bc13fe", "#000000")
        elif self.parent_module:  # type: ignore[reportUnnecessaryComparison]
            self.parent_module.hide_hazard_sticker()

class ThermalBar(QWidget):
    """Horizontal segmented LED bar for thermal/fan display."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(8)
        self.setMaximumHeight(8)
        self.value: float = 0.0
        
    def set_value(self, value: float) -> None:
        self.value = value
        self.update()
        
    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Render 1px high horizontal segmented LED bar."""
        painter = QPainter(self)
        rect = self.rect()
        percentage = self.value / 100.0
        
        # Determine color based on value
        active_color = QColor("#ff8c00") if self.value > 70 else QColor("#bc13fe")
        ghost_color = QColor(188, 19, 254, 26)  # 10% opacity purple
        
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw segments with 2px width and 1px gap
        segment_width = 2
        gap = 1
        step = segment_width + gap
        fill_width = int(rect.width() * percentage)
        
        for x in range(0, rect.width(), step):
            if x + segment_width <= fill_width:
                # Active segment
                painter.setBrush(QBrush(active_color))
            else:
                # Ghost segment
                painter.setBrush(QBrush(ghost_color))
            painter.drawRect(x, 0, segment_width, rect.height())

class NetworkWaveform(QWidget):
    """Network area chart with vertical segmented LED bars."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.data: Deque[float] = deque(maxlen=60)  # Store speed in Mbps
        self.max_speed: float = 10.0  # Auto-scaling max speed
    
    def add_point(self, speed_mbps: float) -> None:
        """Add network speed data point in Mbps."""
        self.data.append(speed_mbps)
        # Calculate a dynamic max based on the highest value in the current data window
        current_max = max(self.data) if self.data else 0.1
        # Add 20% headroom, but never drop below 1.0 Mbps scale
        self.max_speed = max(1.0, current_max * 1.2)
        self.update()
    
    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Render network speed chart with vertical segmented LED bars."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        
        # Draw background
        painter.fillRect(rect, QColor(10, 10, 12))
        
        if not self.data:
            # Show "No Data" message
            painter.setPen(QPen(QColor("#666666")))
            font: QFont = painter.font()
            font.setPointSize(10)
            font.setFamily("Consolas")
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Waiting for network data...")
            return
        
        graph_h = rect.height() - 30
        max_val = self.max_speed
        
        # Draw segmented vertical bars for each data point
        num_points = len(self.data)
        bar_width = max(2, rect.width() // num_points)
        gap = 1
        
        painter.setPen(Qt.PenStyle.NoPen)
        
        for i, speed in enumerate(self.data):
            x = i * bar_width
            normalized_val = min(1.0, speed / max_val) if max_val > 0 else 0.0
            bar_h = int(graph_h * normalized_val)
            
            # Determine color based on percentage (70% threshold)
            percentage = normalized_val * 100
            active_color = QColor("#ff8c00") if percentage > 70 else QColor("#bc13fe")
            ghost_color = QColor(188, 19, 254, 26)  # 10% opacity purple
            
            # Draw vertical segmented bar (2px segments, 1px gaps)
            segment_height = 2
            seg_gap = 1
            step = segment_height + seg_gap
            
            for seg_y in range(0, graph_h, step):
                if graph_h - seg_y <= bar_h:
                    # Active segment
                    painter.setBrush(QBrush(active_color))
                else:
                    # Ghost segment
                    painter.setBrush(QBrush(ghost_color))
                painter.drawRect(x, graph_h - seg_y - segment_height, bar_width - gap, segment_height)
        
        # Draw speed indicator at bottom
        painter.setPen(QPen(QColor("#00f2ff")))
        font = painter.font()
        font.setPointSize(8)
        font.setFamily("Consolas")
        font.setBold(True)
        painter.setFont(font)
        
        current_speed = self.data[-1] if self.data else 0.0
        speed_text = f"CURRENT: {current_speed:.2f} Mbps | MAX: {max_val:.2f} Mbps"
        painter.drawText(5, rect.height() - 10, speed_text)

class SecurityMonitor:
    """Advanced security monitoring with USB and startup detection"""
    
    def __init__(self) -> None:
        self.known_usb_devices: set[str] = set()
        self.known_startup_entries: set[str] = set()
        self.security_events: Deque[SecurityEvent] = deque(maxlen=100)
        self.monitoring_active: bool = False
        
    def start_monitoring(self) -> None:
        """Start security monitoring"""
        self.monitoring_active = True
        self.known_usb_devices = self.get_current_usb_devices()
        self.known_startup_entries = self.get_startup_entries()
        
        # Start monitoring threads
        threading.Thread(target=self.monitor_usb_devices, daemon=True).start()
        threading.Thread(target=self.monitor_startup_changes, daemon=True).start()
        
    def get_current_usb_devices(self) -> set[str]:
        """Get current USB devices"""
        try:
            result: subprocess.CompletedProcess[str] = subprocess.run(
                [r'C:\Windows\System32\wbem\wmic.exe', 'path', 'Win32_USBControllerDevice', 'get', 'Dependent'], 
                capture_output=True, text=True, timeout=5)
            return set(result.stdout.split())
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            print(f"USB device detection error: {e}")
            return set()
            
    def get_startup_entries(self) -> set[str]:
        """Get current startup registry entries"""
        entries: set[str] = set()
        try:
            # Check common startup locations
            startup_keys: List[str] = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunServices",
            ]
            
            for key in startup_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_READ) as reg_key:
                        i: int = 0
                        while True:
                            try:
                                name: str
                                name, value, _ = winreg.EnumValue(reg_key, i)
                                entries.add(f"{name}:{value}")
                                i += 1
                            except WindowsError:
                                break
                except Exception:
                    pass
                    
        except Exception:
            pass
        return entries
        
    def monitor_usb_devices(self) -> None:
        """Monitor USB device changes"""
        while self.monitoring_active:
            try:
                current_devices: set[str] = self.get_current_usb_devices()
                new_devices: set[str] = current_devices - self.known_usb_devices
                removed_devices: set[str] = self.known_usb_devices - current_devices
                
                if new_devices:
                    self.add_security_event("USB_INSERTION", f"New USB device detected: {len(new_devices)} device(s)", "WARNING")
                    
                if removed_devices:
                    self.add_security_event("USB_REMOVAL", f"USB device removed: {len(removed_devices)} device(s)", "INFO")
                    
                self.known_usb_devices = current_devices
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"USB monitoring error: {e}")
                time.sleep(10)
                
    def monitor_startup_changes(self) -> None:
        """Monitor startup registry changes"""
        while self.monitoring_active:
            try:
                current_entries: set[str] = self.get_startup_entries()
                new_entries: set[str] = current_entries - self.known_startup_entries
                
                if new_entries:
                    for entry in new_entries:
                        self.add_security_event("STARTUP_CHANGE", f"New startup entry: {entry}", "WARNING")
                        
                self.known_startup_entries = current_entries
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Startup monitoring error: {e}")
                time.sleep(60)
                
    def add_security_event(self, event_type: str, description: str, severity: str) -> None:
        """Add security event to log"""
        event = SecurityEvent(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event_type=event_type,
            description=description,
            severity=severity
        )
        self.security_events.append(event)
        logger.warning(f"[SEC] {event_type}: {description}")
        
    def get_recent_events(self, limit: int = 20) -> List[SecurityEvent]:
        """Get recent security events"""
        return list(self.security_events)[-limit:]

class AlertManager(QObject):
    """Manages system alerts for critical events."""
    def __init__(self, tray_icon: Optional[QSystemTrayIcon], db_connection: Any) -> None:
        super().__init__()
        self.tray_icon: Optional[QSystemTrayIcon] = tray_icon
        self.db: Any = db_connection
        self.alert_states: Dict[str, Dict[str, Optional[float]]] = {}

    def check_and_alert(self, metric_name: str, current_value: float, threshold: float, duration_sec: int = 5) -> None:
        """Check a metric and trigger an alert if it exceeds a threshold for a set duration."""
        if metric_name not in self.alert_states:
            self.alert_states[metric_name] = {'breached_at': None}

        state: Dict[str, Optional[float]] = self.alert_states[metric_name]

        if current_value > threshold:
            breached_at: Optional[float] = state.get('breached_at')
            if breached_at is None:
                state['breached_at'] = time.time()
            elif time.time() - breached_at >= duration_sec:
                self.trigger_alert(metric_name, current_value)
                state['breached_at'] = None # Reset after alert
        else:
            state['breached_at'] = None

    def trigger_alert(self, metric_name: str, value: float) -> None:
        """Trigger a system notification and log to the database."""
        message: str = f"CRITICAL ALERT: {metric_name} has exceeded threshold with value: {value}"
        logger.critical(f"[WARN] {message}")

        if self.tray_icon:
            self.tray_icon.showMessage(
                "Vitreos Critical Alert",
                message,
                QSystemTrayIcon.MessageIcon.Critical,  # type: ignore
                3000
            )

        if self.db:
            self.db.log_event('CRITICAL_ALERT', message, 'CRITICAL')


class NetworkAnalyzer:
    """Advanced network monitoring with jitter and bandwidth analysis"""
    
    def __init__(self) -> None:
        self.ping_history: Deque[float] = deque(maxlen=100)
        self.bandwidth_history: Deque[float] = deque(maxlen=50)
        self.current_bandwidth_hogs: Dict[str, int] = {}
        
    def measure_ping_jitter(self) -> Tuple[float, float]:
        """Measure network ping and jitter"""
        try:
            # Use Google DNS as ping target with absolute path
            result: subprocess.CompletedProcess[str] = subprocess.run(
                [r'C:\Windows\System32\ping.exe', '-n', '5', '8.8.8.8'], 
                capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines: List[str] = result.stdout.split('\n')
                times: List[float] = []
                for line in lines:
                    if 'time=' in line:
                        try:
                            time_ms: float = float(line.split('time=')[1].split('ms')[0])
                            times.append(time_ms)
                        except (ValueError, IndexError):
                            pass
                
                if len(times) >= 3:
                    jitter: float = statistics.stdev(times) if len(times) > 1 else 0.0
                    return statistics.mean(times), jitter
                    
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            print(f"Ping measurement error: {e}")
        return 0.0, 0.0
        
    def analyze_bandwidth_hogs(self) -> None:
        """Analyze which processes are using the most bandwidth"""
        try:
            # Get network connections and map to processes
            connections: List[Any] = psutil.net_connections(kind='inet')
            process_bandwidth: Dict[str, int] = {}
            
            for conn in connections:
                if conn.pid and conn.status == 'ESTABLISHED':
                    try:
                        process: psutil.Process = psutil.Process(conn.pid)
                        name: str = process.name()
                        if not name:  # Skip empty process names
                            name = f"PID_{conn.pid}"
                        if name in process_bandwidth:
                            process_bandwidth[name] += 1
                        else:
                            process_bandwidth[name] = 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                        pass
                        
            # Sort by connection count (proxy for bandwidth usage) - return all active connections
            sorted_hogs: List[Tuple[str, int]] = sorted(process_bandwidth.items(), key=lambda x: x[1], reverse=True)
            self.current_bandwidth_hogs = dict(sorted_hogs)
            
        except (OSError, ValueError) as e:
            print(f"Bandwidth analysis error: {e}")
            
    def get_bandwidth_summary(self) -> Dict[str, Any]:
        """Get bandwidth usage summary"""
        try:
            net_io: Any = psutil.net_io_counters(pernic=False)  # type: ignore
            mb_recv: float = net_io.bytes_recv / (1024 * 1024)  # type: ignore
            mb_sent: float = net_io.bytes_sent / (1024 * 1024)  # type: ignore
            
            return {
                'downloaded': mb_recv,
                'uploaded': mb_sent,
                'hogs': self.current_bandwidth_hogs
            }
        except Exception:
            return {'downloaded': 0.0, 'uploaded': 0.0, 'hogs': {}}

class PredictiveThermalAlert:
    """Predictive thermal throttling alerts using linear regression"""
    
    def __init__(self) -> None:
        self.temp_history: Deque[float] = deque(maxlen=60)  # Last 2 minutes at 2-second intervals
        self.load_history: Deque[float] = deque(maxlen=60)
        
    def add_reading(self, temp: float, load: float) -> None:
        """Add new temperature and load reading"""
        self.temp_history.append(temp)
        self.load_history.append(load)
        
    def predict_throttling_time(self) -> Optional[float]:
        """Predict time until thermal throttling"""
        if len(self.temp_history) < 10:
            return None
            
        # Simple linear regression
        temps: List[float] = list(self.temp_history)
        
        n: int = len(temps)
        sum_x: int = sum(range(n))
        sum_y: float = sum(temps)
        sum_xy: float = sum(i * temp for i, temp in enumerate(temps))
        sum_x2: int = sum(i * i for i in range(n))
        
        # Calculate slope
        try:
            denominator: int = n * sum_x2 - sum_x * sum_x
            # Avoid division by zero
            if denominator == 0:
                return None
                
            slope: float = (n * sum_xy - sum_x * sum_y) / denominator
            
            # Predict time until 85°C (thermal throttling threshold)
            current_temp: float = temps[-1]
            if slope > 0:  # Heating up
                time_to_throttle: float = (85 - current_temp) / slope
                if time_to_throttle > 0:
                    return max(0.0, time_to_throttle * 2)  # Convert to seconds (2s intervals)
        except (ZeroDivisionError, ValueError) as e:
            print(f"Thermal prediction error: {e}")
            return None
            
        return None

class PurgeConfirmationDialog(QDialog):
    """Interactive confirmation dialog for Purge Protocol with checkbox selection"""
    
    def __init__(self, targets: List[Tuple[int, str, float, bool]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.targets = targets
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.resize(650, 700)
        self.is_dragging: bool = False
        self.drag_position: Optional[QPoint] = None
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup dialog UI with Cyberdeck styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #08080a
                border: 2px solid #bc13fe
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("[ REVIEW PURGE TARGETS ]")
        title.setStyleSheet("""
            QLabel {
                color: #ff8c00
                font-family: 'Courier New', monospace
                font-size: 14pt
                font-weight: bold
                padding: 10px
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Utility buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        
        btn_select_all = QPushButton("☑ Select All")
        btn_select_all.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 1px solid #00f2ff
                color: #00f2ff
                font-family: 'Courier New', monospace
                font-size: 9pt
                font-weight: bold
                padding: 8px 12px
            }
            QPushButton:hover {
                background-color: #00f2ff
                color: #000000
            }
        """)
        btn_select_all.clicked.connect(self.select_all)  # type: ignore
        
        btn_unselect_all = QPushButton("☐ Unselect All")
        btn_unselect_all.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 1px solid #666666
                color: #666666
                font-family: 'Courier New', monospace
                font-size: 9pt
                font-weight: bold
                padding: 8px 12px
            }
            QPushButton:hover {
                background-color: #666666
                color: #000000
            }
        """)
        btn_unselect_all.clicked.connect(self.unselect_all)  # type: ignore
        
        btn_bloatware_only = QPushButton("🎯 Bloatware Only")
        btn_bloatware_only.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 1px solid #bc13fe
                color: #bc13fe
                font-family: 'Courier New', monospace
                font-size: 9pt
                font-weight: bold
                padding: 8px 12px
            }
            QPushButton:hover {
                background-color: #bc13fe
                color: #000000
            }
        """)
        btn_bloatware_only.clicked.connect(self.select_bloatware)  # type: ignore
        
        button_row.addWidget(btn_select_all)
        button_row.addWidget(btn_unselect_all)
        button_row.addWidget(btn_bloatware_only)
        button_row.addStretch()
        
        layout.addLayout(button_row)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Kill", "Process", "RAM (MB)"])  # type: ignore[arg-type]
        self.table.setRowCount(len(self.targets))
        
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 100)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent
                border: 1px solid #bc13fe
                color: #00f2ff
                font-family: 'Consolas', monospace
                font-size: 9pt
                gridline-color: rgba(188, 19, 254, 0.3)
            }
            QTableWidget::item {
                padding: 6px
            }
            QHeaderView::section {
                background-color: #1a1a1e
                color: #bc13fe
                font-family: 'Courier New', monospace
                font-weight: bold
                font-size: 9pt
                padding: 8px
                border: none
                border-bottom: 2px solid #bc13fe
            }
        """)
        
        # Disable sorting during population
        self.table.setSortingEnabled(False)
        
        # Populate table
        for row, (pid, name, mem_mb, is_bloat) in enumerate(self.targets):
            # Checkbox column - only check if known bloatware
            check_item: QTableWidgetItem = QTableWidgetItem()
            if is_bloat:
                check_item.setCheckState(Qt.CheckState.Checked)
            else:
                check_item.setCheckState(Qt.CheckState.Unchecked)
            check_item.setData(Qt.ItemDataRole.UserRole, pid)
            check_item.setData(Qt.ItemDataRole.UserRole + 1, is_bloat)
            check_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, check_item)
            
            # Process name
            name_item: QTableWidgetItem = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, name_item)
            
            # RAM usage - use setData for numeric sorting
            ram_item = QTableWidgetItem()
            ram_item.setData(Qt.ItemDataRole.DisplayRole, round(mem_mb, 1))
            ram_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, ram_item)
        
        # Enable sorting and sort by RAM descending
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(2, Qt.SortOrder.DescendingOrder)
        
        layout.addWidget(self.table)
        
        # Save Rules checkbox
        self.save_checkbox = QCheckBox("💾 Save these rules persistently (Apply on Boot)")
        self.save_checkbox.setChecked(True)
        self.save_checkbox.setStyleSheet("""
            QCheckBox {
                color: #00f2ff
                font-family: 'Courier New', monospace
                font-size: 10pt
                font-weight: 600
                spacing: 8px
                padding: 10px
            }
            QCheckBox::indicator {
                width: 20px
                height: 20px
                border: 2px solid #00f2ff
                border-radius: 4px
                background-color: transparent
            }
            QCheckBox::indicator:checked {
                background-color: #00f2ff
                border-color: #00f2ff
            }
        """)
        layout.addWidget(self.save_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        btn_cancel = QPushButton("[CANCEL]")
        btn_cancel.setFixedHeight(40)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 2px solid #666666
                color: #666666
                font-family: 'Courier New', monospace
                font-size: 11pt
                font-weight: bold
            }
            QPushButton:hover {
                background-color: #666666
                color: #000000
            }
        """)
        btn_cancel.clicked.connect(self.reject)  # type: ignore
        
        btn_execute = QPushButton("[EXECUTE PURGE]")
        btn_execute.setFixedHeight(40)
        btn_execute.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 2px solid #ff8c00
                color: #ff8c00
                font-family: 'Courier New', monospace
                font-size: 11pt
                font-weight: bold
            }
            QPushButton:hover {
                background-color: #ff8c00
                color: #000000
            }
        """)
        btn_execute.clicked.connect(self.accept)  # type: ignore
        
        button_layout.addWidget(btn_cancel)
        button_layout.addWidget(btn_execute)
        
        layout.addLayout(button_layout)
    
    def get_selected_pids(self) -> List[int]:
        """Return list of PIDs that are checked for termination"""
        selected_pids: List[int] = []
        for row in range(self.table.rowCount()):
            check_item = self.table.item(row, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                pid = check_item.data(Qt.ItemDataRole.UserRole)
                if pid is not None:
                    selected_pids.append(pid)
        return selected_pids
    
    def select_all(self) -> None:
        """Select all checkboxes"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
    
    def unselect_all(self) -> None:
        """Unselect all checkboxes"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
    
    def select_bloatware(self) -> None:
        """Select only known bloatware, unselect everything else"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                is_bloat = item.data(Qt.ItemDataRole.UserRole + 1)
                if is_bloat:
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)


    def mousePressEvent(self, a0: Optional[QMouseEvent]) -> None:
        if a0 is None:
            return
        """Handle mouse press for dragging."""
        if event is not None and a0.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()
            a0.accept()
    
    def mouseMoveEvent(self, a0: Optional[QMouseEvent]) -> None:
        if a0 is None:
            return
        """Handle mouse move for dragging."""
        if event is not None and self.is_dragging and self.drag_position is not None:
            self.move(a0.globalPosition().toPoint() - self.drag_position)
            a0.accept()
    
    def mouseReleaseEvent(self, a0: Optional[QMouseEvent]) -> None:
        if a0 is None:
            return
        """Handle mouse release to stop dragging."""
        if event is not None:
            self.is_dragging = False
            a0.accept()

class TuningConfirmationDialog(QDialog):
    """Interactive confirmation dialog for eSports tuning operations with RAM/CPU metrics"""
    
    def __init__(self, title: str, targets: List[Tuple[int, str, float, float, str, bool]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.targets = targets  # (PID, Name, RAM_MB, CPU_%, Target_State, Is_Recommended)
        self.title_text = title
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.resize(800, 700)  # Wider for additional columns
        self.is_dragging: bool = False
        self.drag_position: Optional[QPoint] = None
        self.save_checkbox: QCheckBox
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup dialog UI with Cyberdeck styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #08080a
                border: 2px solid #bc13fe
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(self.title_text)
        title.setStyleSheet("""
            QLabel {
                color: #ff8c00
                font-family: 'Courier New', monospace
                font-size: 14pt
                font-weight: bold
                padding: 10px
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Utility buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        
        btn_select_all = QPushButton("☑ Select All")
        btn_select_all.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 1px solid #00f2ff
                color: #00f2ff
                font-family: 'Courier New', monospace
                font-size: 9pt
                font-weight: bold
                padding: 8px 12px
            }
            QPushButton:hover {
                background-color: #00f2ff
                color: #000000
            }
        """)
        btn_select_all.clicked.connect(self.select_all)  # type: ignore
        
        btn_unselect_all = QPushButton("☐ Unselect All")
        btn_unselect_all.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 1px solid #666666
                color: #666666
                font-family: 'Courier New', monospace
                font-size: 9pt
                font-weight: bold
                padding: 8px 12px
            }
            QPushButton:hover {
                background-color: #666666
                color: #000000
            }
        """)
        btn_unselect_all.clicked.connect(self.unselect_all)  # type: ignore
        
        button_row.addWidget(btn_select_all)
        button_row.addWidget(btn_unselect_all)
        button_row.addStretch()
        
        layout.addLayout(button_row)
        
        # Table with 6 columns
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Select", "PID", "Process", "RAM (MB)", "CPU (%)", "Target State"])  # type: ignore[arg-type]
        self.table.setRowCount(len(self.targets))
        
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 80)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent
                border: 1px solid #bc13fe
                color: #00f2ff
                font-family: 'Consolas', monospace
                font-size: 9pt
                gridline-color: rgba(188, 19, 254, 0.3)
            }
            QTableWidget::item {
                padding: 6px
            }
            QHeaderView::section {
                background-color: #1a1a1e
                color: #bc13fe
                font-family: 'Courier New', monospace
                font-weight: bold
                font-size: 9pt
                padding: 8px
                border: none
                border-bottom: 2px solid #bc13fe
            }
        """)
        
        # Disable sorting during population
        self.table.setSortingEnabled(False)
        
        # Populate table with 6-tuple data
        for row, (pid, name, ram_mb, cpu_pct, target_state, is_recommended) in enumerate(self.targets):
            # Checkbox column
            check_item: QTableWidgetItem = QTableWidgetItem()
            if is_recommended:
                check_item.setCheckState(Qt.CheckState.Checked)
            else:
                check_item.setCheckState(Qt.CheckState.Unchecked)
            check_item.setData(Qt.ItemDataRole.UserRole, pid)
            check_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, check_item)
            
            # PID column
            pid_item: QTableWidgetItem = QTableWidgetItem()
            pid_item.setData(Qt.ItemDataRole.DisplayRole, pid)
            pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, pid_item)
            
            # Process name
            name_item: QTableWidgetItem = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, name_item)
            
            # RAM (MB) - use numeric data for sorting
            ram_item: QTableWidgetItem = QTableWidgetItem()
            ram_item.setData(Qt.ItemDataRole.DisplayRole, round(ram_mb, 1))
            ram_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, ram_item)
            
            # CPU (%) - use numeric data for sorting
            cpu_item: QTableWidgetItem = QTableWidgetItem()
            cpu_item.setData(Qt.ItemDataRole.DisplayRole, round(cpu_pct, 1))
            cpu_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, cpu_item)
            
            # Target state
            state_item: QTableWidgetItem = QTableWidgetItem(target_state)
            state_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, state_item)
        
        # Enable sorting and sort by RAM descending
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(3, Qt.SortOrder.DescendingOrder)
        
        layout.addWidget(self.table)
        
        # Save Rules checkbox
        self.save_checkbox = QCheckBox("💾 Save these rules persistently (Apply on Boot)")
        self.save_checkbox.setChecked(True)
        self.save_checkbox.setStyleSheet("""
            QCheckBox {
                color: #00f2ff
                font-family: 'Courier New', monospace
                font-size: 10pt
                font-weight: 600
                spacing: 8px
                padding: 10px
            }
            QCheckBox::indicator {
                width: 20px
                height: 20px
                border: 2px solid #00f2ff
                border-radius: 4px
                background-color: transparent
            }
            QCheckBox::indicator:checked {
                background-color: #00f2ff
                border-color: #00f2ff
            }
        """)
        layout.addWidget(self.save_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        btn_cancel = QPushButton("[CANCEL]")
        btn_cancel.setFixedHeight(40)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 2px solid #666666
                color: #666666
                font-family: 'Courier New', monospace
                font-size: 11pt
                font-weight: bold
            }
            QPushButton:hover {
                background-color: #666666
                color: #000000
            }
        """)
        btn_cancel.clicked.connect(self.reject)  # type: ignore
        
        btn_execute = QPushButton("[EXECUTE]")
        btn_execute.setFixedHeight(40)
        btn_execute.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 2px solid #ff8c00
                color: #ff8c00
                font-family: 'Courier New', monospace
                font-size: 11pt
                font-weight: bold
            }
            QPushButton:hover {
                background-color: #ff8c00
                color: #000000
            }
        """)
        btn_execute.clicked.connect(self.accept)  # type: ignore
        
        button_layout.addWidget(btn_cancel)
        button_layout.addWidget(btn_execute)
        
        layout.addLayout(button_layout)
    
    def get_selected_pids(self) -> List[int]:
        """Return list of PIDs that are checked"""
        selected_pids: List[int] = []
        for row in range(self.table.rowCount()):
            check_item = self.table.item(row, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                pid = check_item.data(Qt.ItemDataRole.UserRole)
                if pid is not None:
                    selected_pids.append(pid)
        return selected_pids
    
    def get_results(self) -> Tuple[List[int], bool]:
        """Return tuple of (selected PIDs, save_to_database flag)"""
        return (self.get_selected_pids(), self.save_checkbox.isChecked())
    
    def select_all(self) -> None:
        """Select all checkboxes"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
    
    def unselect_all(self) -> None:
        """Unselect all checkboxes"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)


    def mousePressEvent(self, a0: Optional[QMouseEvent]) -> None:
        if a0 is None:
            return
        """Handle mouse press for dragging."""
        if event is not None and a0.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()
            a0.accept()
    
    def mouseMoveEvent(self, a0: Optional[QMouseEvent]) -> None:
        if a0 is None:
            return
        """Handle mouse move for dragging."""
        if event is not None and self.is_dragging and self.drag_position is not None:
            self.move(a0.globalPosition().toPoint() - self.drag_position)
            a0.accept()
    
    def mouseReleaseEvent(self, a0: Optional[QMouseEvent]) -> None:
        if a0 is None:
            return
        """Handle mouse release to stop dragging."""
        if event is not None:
            self.is_dragging = False
            a0.accept()

class SecurityMonitorThread(QThread):
    """Background thread for advanced security monitoring (USB, Webcam, Registry)"""
    
    security_event = pyqtSignal(str, str, str)  # event_type, description, severity
    
    def __init__(self) -> None:
        super().__init__()
        self.is_running: bool = False
        self.known_usb_devices: set[str] = set()
        self.last_webcam_check: float = 0.0
        
    def run(self) -> None:
        """Main security monitoring loop"""
        self.is_running = True
        logger.info("[SEC] Security monitor thread started")
        
        # Initialize known USB devices
        self.known_usb_devices = self.get_usb_devices()
        
        while self.is_running:
            try:
                # USB Device Detection (every 3 seconds)
                current_devices: set[str] = self.get_usb_devices()
                new_devices: set[str] = current_devices - self.known_usb_devices
                removed_devices: set[str] = self.known_usb_devices - current_devices
                
                if new_devices:
                    for device in new_devices:
                        self.security_event.emit("USB_CONNECTED", f"New USB device: {device}", "WARNING")
                        logger.warning(f"[SEC] USB device connected: {device}")
                
                if removed_devices:
                    for device in removed_devices:
                        self.security_event.emit("USB_DISCONNECTED", f"USB device removed: {device}", "INFO")
                
                self.known_usb_devices = current_devices
                
                # Webcam/Microphone Detection (every 5 seconds)
                if time.time() - self.last_webcam_check > 5.0:
                    webcam_active: bool = self.check_webcam_active()
                    mic_active: bool = self.check_microphone_active()
                    
                    if webcam_active:
                        self.security_event.emit("WEBCAM_ACTIVE", "Webcam is currently in use", "WARNING")
                        logger.warning("[SEC] Webcam detected as active")
                    
                    if mic_active:
                        self.security_event.emit("MICROPHONE_ACTIVE", "Microphone is currently in use", "WARNING")
                        logger.warning("[SEC] Microphone detected as active")
                    
                    self.last_webcam_check = time.time()
                
                time.sleep(3.0)
                
            except Exception as e:
                logger.error(f"[SEC] Security monitor error: {e}")
                time.sleep(5.0)
    
    def get_usb_devices(self) -> set[str]:
        """Get list of connected USB devices using WMI"""
        devices: set[str] = set()
        if not WMI_AVAILABLE:
            logger.debug("WMI not available, using PowerShell fallback for USB detection")
            try:
                result: subprocess.CompletedProcess[str] = subprocess.run(
                    ['powershell', '-Command', "Get-PnpDevice | Where-Object {$_.InstanceId -like '*USB*'} | Select-Object -ExpandProperty FriendlyName"],
                    capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            devices.add(line.strip())
            except Exception as e:
                logger.debug(f"USB detection fallback error: {e}")
            return devices
        
        try:
            import wmi  # type: ignore[reportMissingImports]
            c = wmi.WMI()  # type: ignore[reportUnknownMemberType, reportUnknownVariableType]
            for _ in c.Win32_PnPEntity():  # type: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType]
                if _.DeviceID and 'USB' in _.DeviceID:  # type: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                    device_name: str = _.Name if _.Name else _.DeviceID  # type: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                    devices.add(device_name)  # type: ignore[reportUnknownArgumentType]
        except Exception as e:
            logger.debug(f"USB detection error: {e}")
        return devices
    
    def check_webcam_active(self) -> bool:
        """Check if webcam is currently active via Registry"""
        try:
            key_path: str = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\NonPackaged"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                i: int = 0
                while True:
                    try:
                        subkey_name: str = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ) as subkey:
                            try:
                                last_used_stop, _ = winreg.QueryValueEx(subkey, "LastUsedTimeStop")
                                if last_used_stop == 0:
                                    return True
                            except WindowsError:
                                pass
                        i += 1
                    except WindowsError:
                        break
        except Exception as e:
            logger.debug(f"Webcam check error: {e}")
        return False
    
    def check_microphone_active(self) -> bool:
        """Check if microphone is currently active via Registry"""
        try:
            key_path: str = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone\NonPackaged"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                i: int = 0
                while True:
                    try:
                        subkey_name: str = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ) as subkey:
                            try:
                                last_used_stop, _ = winreg.QueryValueEx(subkey, "LastUsedTimeStop")
                                if last_used_stop == 0:
                                    return True
                            except WindowsError:
                                pass
                        i += 1
                    except WindowsError:
                        break
        except Exception as e:
            logger.debug(f"Microphone check error: {e}")
        return False
    
    def stop(self) -> None:
        """Stop the security monitoring thread"""
        self.is_running = False
        logger.info("[SEC] Security monitor thread stopping")


class HardwareMonitorWorker(QObject):
    """Worker thread for hardware monitoring - runs in separate thread"""
    
    # Signal emits dict with all hardware stats
    stats_updated = pyqtSignal(dict)
    
    # New signals for extended data types
    processes_updated = pyqtSignal(list)  # List of (pid, name, memory_mb) tuples
    gpu_advanced_updated = pyqtSignal(dict)  # Dict with gpu_clock, gpu_power, gpu_fan_percent
    storage_updated = pyqtSignal(dict)  # Dict with per-drive stats and I/O counters
    network_updated = pyqtSignal(dict)  # Dict with downloaded and uploaded data
    
    def __init__(self) -> None:
        super().__init__()
        self.is_running: bool = False
        self.gpu_handle: Optional[Any] = None
        # Thermal prediction: store last 10 CPU temp readings
        self.cpu_temp_history: Deque[float] = deque(maxlen=10)
        # Heartbeat Regulator
        self.polling_interval: float = 2.0
        # Combat Mode
        self.combat_mode_active: bool = False
        self.user_polling_interval: float = 2.0
        # Disk I/O tracking state
        self.last_disk_io: Optional[Any] = None
        # Network I/O tracking state (per-NIC)
        self.last_net_io: Optional[Dict[str, Any]] = None
        self.selected_nic: Optional[str] = None
        self.available_nics: List[str] = []
        # Network analyzer for ping/jitter
        self.network_analyzer: NetworkAnalyzer = NetworkAnalyzer()
        
    def setup_gpu(self) -> None:
        """Initialize GPU handle by finding first device that supports power usage"""
        try:
            logger.debug("Initializing NVIDIA GPU Handle...")
            
            if not NVML_AVAILABLE:
                logger.warning("NVML not available - GPU monitoring disabled")
                self.gpu_handle = None
                return
            
            cast(Any, pynvml.nvmlInit()  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType])  # type: ignore[attr-defined]
            logger.info("NVML initialized successfully")
            
            device_count: int = cast(int, pynvml.nvmlDeviceGetCount()  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType])  # type: ignore[attr-defined]
            logger.info(f"Found {device_count} NVIDIA GPU device(s)")
            
            # Loop through devices to find one that supports power usage
            for i in range(device_count):
                try:
                    handle: Any = cast(Any, pynvml.nvmlDeviceGetHandleByIndex(i)  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType, reportCallIssue])  # type: ignore[attr-defined]
                    device_name: str = str(cast(str, pynvml.nvmlDeviceGetName(handle)  # type: ignore))  # type: ignore[attr-defined]
                    logger.debug(f"FOUND GPU: {device_name}")
                    
                    # Test if this device supports power usage query
                    try:
                        cast(int, pynvml.nvmlDeviceGetPowerUsage(handle)  # type: ignore)  # type: ignore[attr-defined]
                        logger.info(f"SUCCESS: Found GPU {device_name}. Power Support: True")
                        self.gpu_handle = handle
                        return
                    except Exception as power_err:
                        error_type: str = type(power_err).__name__
                        logger.warning(f"POWER SUPPORTED: False ({error_type})")
                        continue
                
                except Exception:
                    pass
                except Exception as e:
                    error_type = type(e).__name__
                    logger.warning(f"Cannot access GPU {i} ({error_type}): {e}")
                    continue
            
            # If we get here, no device supports power usage
            logger.warning("No GPU with power support found - using fallback mode")
            
            if device_count > 0:
                # Use first device anyway for temp/usage data
                self.gpu_handle = cast(Any, pynvml.nvmlDeviceGetHandleByIndex(0)  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType, reportCallIssue])  # type: ignore[attr-defined]
                logger.info("Using first GPU for basic monitoring (no power/fan data)")
            else:
                self.gpu_handle = None
                logger.warning("No NVIDIA GPU devices found")
        
        except Exception:
            pass
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"GPU initialization failed ({error_type}): {e}")
            self.gpu_handle = None
    

    def check_apex_active(self) -> bool:
        """Check if Apex Legends is the active foreground window"""
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            window_title = buff.value.lower()
            
            for proc in psutil.process_iter(['name']):
                if 'r5apex.exe' in proc.info['name'].lower():
                    if 'apex' in window_title or 'r5apex' in window_title:
                        return True
            return False
        except:
            return False
    
    def collect_top_processes(self) -> List[Tuple[int, str, float, float]]:
        """Collect top 15 memory-consuming processes (>10MB) excluding critical system processes"""
        try:
            processes: List[Tuple[int, str, float, float]] = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    proc_info: Dict[str, Any] = proc.info
                    proc_name: str = proc_info['name'].lower()
                    mem_mb: float = proc_info['memory_info'].rss / (1024 * 1024)
                    
                    # Filter: >10MB and NOT in critical system processes
                    if mem_mb > 10.0 and proc_name not in CRITICAL_SYSTEM_PROCESSES:
                        cpu_pct: float = proc_info['cpu_percent'] if proc_info['cpu_percent'] else 0.0
                        processes.append((proc_info['pid'], proc_info['name'], mem_mb, cpu_pct))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by memory usage descending and return top 15
            return sorted(processes, key=lambda x: x[2], reverse=True)[:15]
        except Exception as e:
            logger.error(f"Error collecting top processes: {e}")
            return []
    
    def collect_gpu_advanced(self) -> Dict[str, Any]:
        """Collect detailed GPU statistics"""
        gpu_data: Dict[str, Any] = {
            'gpu_clock_mhz': 0.0,
            'gpu_power_watts': 0.0,
            'gpu_fan_percent': 0.0,
            'gpu_hotspot_temp': 0.0,
            'gpu_throttling': ''
        }
        
        if not (NVML_AVAILABLE and self.gpu_handle is not None):
            return gpu_data
        
        try:
            handle: Any = self.gpu_handle
            
            # GPU Clock Speed
            try:
                clock: int = cast(int, pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)  # type: ignore)  # type: ignore[attr-defined]
                gpu_data['gpu_clock_mhz'] = float(clock)
            except Exception as e:
                error_type: str = type(e).__name__
                logger.debug(f"GPU clock speed error ({error_type}): {e}")
                gpu_data['gpu_clock_mhz'] = 0.0
            
            # Power Draw
            try:
                power: int = cast(int, pynvml.nvmlDeviceGetPowerUsage(handle)  # type: ignore)  # type: ignore[attr-defined]
                gpu_data['gpu_power_watts'] = float(power) / 1000.0  # Convert milliwatts to watts
            except Exception as e:
                error_type = type(e).__name__
                logger.debug(f"GPU power draw error ({error_type}): {e}")
                gpu_data['gpu_power_watts'] = 0.0
            
            # Fan Speed (if available)
            try:
                fan: int = cast(int, pynvml.nvmlDeviceGetFanSpeed(handle)  # type: ignore)  # type: ignore[attr-defined]
                gpu_data['gpu_fan_percent'] = float(fan)
            except Exception as e:
                error_type = type(e).__name__
                logger.debug(f"GPU fan speed error ({error_type}): {e}")
                gpu_data['gpu_fan_percent'] = 0.0

            # Hotspot Temperature (safely check if constant exists)
            try:
                hotspot_constant = getattr(pynvml, 'NVML_TEMPERATURE_GPU_HOTSPOT', None)
                if hotspot_constant is not None:
                    hotspot_temp: int = cast(int, pynvml.nvmlDeviceGetTemperature(handle, hotspot_constant)  # type: ignore)  # type: ignore[attr-defined]
                    gpu_data['gpu_hotspot_temp'] = float(hotspot_temp)
                else:
                    gpu_data['gpu_hotspot_temp'] = 0.0
            except Exception as e:
                error_type = type(e).__name__
                logger.debug(f"GPU hotspot temp error ({error_type}): {e}")
                gpu_data['gpu_hotspot_temp'] = 0.0

            # Throttling Status
            try:
                throttling: int = cast(int, pynvml.nvmlDeviceGetCurrentClocksThrottleReasons(handle)  # type: ignore)  # type: ignore[attr-defined]
                reasons: List[str] = []
                if throttling & pynvml.nvmlClocksThrottleReasonGpuIdle:  # type: ignore[attr-defined]
                    reasons.append("Idle")
                if throttling & pynvml.nvmlClocksThrottleReasonHwSlowdown:  # type: ignore[attr-defined]
                    reasons.append("HW Slowdown")
                if throttling & pynvml.nvmlClocksThrottleReasonSwPowerCap:  # type: ignore[attr-defined]
                    reasons.append("Power Cap")
                if throttling & pynvml.nvmlClocksThrottleReasonHwThermalSlowdown:  # type: ignore[attr-defined]
                    reasons.append("Thermal")
                gpu_data['gpu_throttling'] = ", ".join(reasons) if reasons else "None"
            except Exception as e:
                error_type = type(e).__name__
                logger.debug(f"GPU throttling error ({error_type}): {e}")
                gpu_data['gpu_throttling'] = "N/A"
                
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error collecting advanced GPU data ({error_type}): {e}")
        
        return gpu_data
    
    def calculate_thermal_prediction(self, current_temp: float) -> float:
        """
        Calculate predicted CPU temperature 30 seconds from now based on trend.
        Uses last 10 readings to calculate trend slope.
        """
        try:
            # Add current reading to history
            self.cpu_temp_history.append(current_temp)
            
            # Need at least 2 readings to calculate trend
            if len(self.cpu_temp_history) < 2:
                logger.debug(f"DEBUG: Thermal History size: {len(self.cpu_temp_history)}/10. Prediction pending.")
                return current_temp  # Return current if not enough history
            
            # Calculate simple linear trend: (temp_now - temp_oldest) / time_points
            temps: List[float] = list(self.cpu_temp_history)
            n: int = len(temps)
            
            # Calculate trend using least squares regression
            sum_x: int = sum(range(n))
            sum_y: float = sum(temps)
            sum_xy: float = sum(i * temp for i, temp in enumerate(temps))
            sum_x2: int = sum(i * i for i in range(n))
            
            # Slope calculation: (n*sum_xy - sum_x*sum_y) / (n*sum_x2 - sum_x^2)
            denominator: int = n * sum_x2 - sum_x * sum_x
            if denominator == 0:
                logger.debug("Thermal prediction: no trend detected (flat temperature)")
                return current_temp  # No trend
            
            slope: float = (n * sum_xy - sum_x * sum_y) / denominator
            
            # Predict temperature at t=30 seconds (we update every 2 seconds, so 15 time units ahead)
            # Assuming roughly 2-second intervals between readings
            predicted_temp: float = current_temp + (slope * 15)
            
            # Clamp to reasonable range (shouldn't jump more than 20°C in 30 seconds)
            predicted_temp = max(current_temp - 5, min(predicted_temp, current_temp + 20))
            
            if len(self.cpu_temp_history) >= 5:
                logger.debug(f"Thermal trend: slope={slope:.3f}, predicted_30s={predicted_temp:.1f}°C")
            
            return round(predicted_temp, 1)
            
        except Exception as e:
            error_type: str = type(e).__name__
            logger.error(f"Error calculating thermal prediction ({error_type}): {e}")
            return current_temp
    
    def collect_storage_data(self) -> Dict[str, Any]:
        """Collect storage and disk I/O statistics"""
        storage_data: Dict[str, Any] = {
            'drives': {},
            'io_counters': {},
        }
        
        try:
            # Get all mounted disk partitions
            partitions: List[Any] = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage: Any = psutil.disk_usage(partition.mountpoint)
                    storage_data['drives'][partition.device] = {
                        'mountpoint': partition.mountpoint,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'percent': round(usage.percent, 1),
                    }
                except (OSError, PermissionError) as e:
                    logger.debug(f"Cannot access {partition.device}: {e}")
                    continue
            
            # Get disk I/O counters (overall)
            try:
                io: Any = psutil.disk_io_counters()
                if io:
                    storage_data['io_counters'] = {
                        'read_bytes': io.read_bytes,
                        'write_bytes': io.write_bytes,
                        'read_count': io.read_count,
                        'write_count': io.write_count,
                    }
            except Exception as e:
                logger.debug(f"Cannot get disk I/O counters: {e}")
        
        except Exception as e:
            logger.error(f"Error collecting storage data: {e}")
        
        return storage_data
    
    def run(self) -> None:
        """Main monitoring loop running in separate thread"""
        self.is_running = True
        logger.info("Hardware monitor worker thread started")
        
        loop_count: int = 0
        while self.is_running:
            try:
                # Combat Mode Check
                apex_active = self.check_apex_active()
                if apex_active and not self.combat_mode_active:
                    self.combat_mode_active = True
                    self.user_polling_interval = self.polling_interval
                    self.polling_interval = 5.0
                    logger.warning("[SYS] COMBAT_MODE_ACTIVE: Polling throttled to 5s")
                elif not apex_active and self.combat_mode_active:
                    self.combat_mode_active = False
                    self.polling_interval = self.user_polling_interval
                    logger.info("[SYS] COMBAT_MODE_DEACTIVATED: Polling restored")
                
                # Blacklist Check
                for proc in psutil.process_iter(['name']):
                    try:
                        proc_name = proc.info['name'].lower()
                        for blacklisted in BLACKLISTED_PROCESSES:
                            if blacklisted.lower() in proc_name:
                                logger.critical(f"[SEC] BLACKLISTED_PROCESS_DETECTED: {proc.info['name']}")
                                break
                    except:
                        pass
                
                stats_dict: Dict[str, float] = {}
                
                # CPU and RAM
                stats_dict['cpu_usage'] = float(psutil.cpu_percent(interval=None))
                stats_dict['ram_usage'] = float(psutil.virtual_memory().percent)
                
                # Disk
                try:
                    if platform.system() == 'Windows':
                        drive = os.path.splitdrive(os.path.expanduser('~'))[0] + '\\'
                    else:
                        drive = '/'
                    stats_dict['disk_usage'] = float(psutil.disk_usage(drive).percent)
                except (OSError, ValueError) as e:
                    logger.error(f"Disk usage error in worker: {e}")
                    stats_dict['disk_usage'] = 0.0
                
                # Temperature
                try:
                    if hasattr(psutil, "sensors_temperatures"):
                        temps_fn = getattr(psutil, "sensors_temperatures", None)
                        temps: Any = temps_fn() if temps_fn is not None else None
                        if temps is not None and 'coretemp' in temps:
                            stats_dict['cpu_temp'] = float(temps['coretemp'][0].current)
                        elif temps is not None and 'cpu_thermal' in temps:
                            stats_dict['cpu_temp'] = float(temps['cpu_thermal'][0].current)
                        else:
                            stats_dict['cpu_temp'] = 45.0
                    else:
                        stats_dict['cpu_temp'] = 45.0
                except (OSError, AttributeError, IndexError) as e:
                    logger.error(f"Temperature reading error in worker: {e}")
                    stats_dict['cpu_temp'] = 45.0
                
                # Thermal Prediction (based on temperature trend) - ALWAYS calculate
                stats_dict['thermal_prediction'] = float(self.calculate_thermal_prediction(stats_dict.get('cpu_temp', 45.0)))
                
                # GPU data
                if NVML_AVAILABLE and self.gpu_handle is not None:
                    try:
                        handle = self.gpu_handle
                        
                        # Temperature
                        stats_dict['gpu_temp'] = float(cast(int, pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)  # type: ignore))  # type: ignore[attr-defined]
                        
                        # Usage
                        utilization = cast(Any, pynvml.nvmlDeviceGetUtilizationRates(handle)  # type: ignore)  # type: ignore[attr-defined]
                        stats_dict['gpu_usage'] = float(utilization.gpu)
                        
                        # VRAM
                        memory = cast(Any, pynvml.nvmlDeviceGetMemoryInfo(handle)  # type: ignore)  # type: ignore[attr-defined]
                        stats_dict['gpu_vram_used'] = float(memory.used) / 1024 / 1024 / 1024
                        stats_dict['gpu_vram_total'] = float(memory.total) / 1024 / 1024 / 1024
                        stats_dict['gpu_vram_percent'] = (float(memory.used) / float(memory.total)) * 100
                        
                        # Fan speed
                        try:
                            fan_speed = cast(int, pynvml.nvmlDeviceGetFanSpeed(handle)  # type: ignore)  # type: ignore[attr-defined]
                            stats_dict['gpu_fan_speed'] = float(fan_speed)
                        except Exception as e:
                            error_type = type(e).__name__
                            logger.error(f"GPU fan speed error ({error_type}): {e}")
                            stats_dict['gpu_fan_speed'] = 0.0
                        
                        # Power Draw (milliwatts -> watts)
                        try:
                            power_mw = cast(int, pynvml.nvmlDeviceGetPowerUsage(handle)  # type: ignore)  # type: ignore[attr-defined]
                            stats_dict['gpu_power_draw'] = float(power_mw) / 1000.0  # Convert mW to W
                        except Exception as e:
                            error_type = type(e).__name__
                            logger.error(f"GPU power draw error ({error_type}): {e}")
                            stats_dict['gpu_power_draw'] = 0.0
                        
                        # Log hardware poll at TRACE level
                        logger.debug(f"TRACE: Hardware Poll - CPU: {stats_dict['cpu_usage']:.1f}%, GPU: {stats_dict['gpu_power_draw']:.1f}W, Fan: {stats_dict['gpu_fan_speed']:.1f}%")
                    except Exception as e:
                        error_type = type(e).__name__
                        logger.error(f"GPU monitoring error in worker ({error_type}): {e}")
                        # Fallback values
                        stats_dict['gpu_temp'] = float(stats_dict.get('cpu_temp', 45.0) + 5.0)
                        stats_dict['gpu_usage'] = float(stats_dict.get('cpu_usage', 0))
                        stats_dict['gpu_vram_percent'] = 30.0
                        stats_dict['gpu_fan_speed'] = 0.0
                        stats_dict['gpu_power_draw'] = 0.0
                else:
                    # Fallback values if GPU not available
                    stats_dict['gpu_temp'] = float(stats_dict.get('cpu_temp', 45.0) + 5.0)
                    stats_dict['gpu_usage'] = float(stats_dict.get('cpu_usage', 0))
                    stats_dict['gpu_vram_percent'] = 30.0
                    stats_dict['gpu_fan_speed'] = 0.0
                    stats_dict['gpu_power_draw'] = 0.0
                
                # Emit signal with all stats
                self.stats_updated.emit(stats_dict)
                
                # Collect extended data every 2 iterations = 4 seconds to reduce overhead
                loop_count += 1
                if loop_count % 2 == 0:
                    processes: List[Tuple[int, str, float, float]] = self.collect_top_processes()
                    if processes:
                        self.processes_updated.emit(processes)
                    
                    gpu_advanced: Dict[str, Any] = self.collect_gpu_advanced()
                    self.gpu_advanced_updated.emit(gpu_advanced)
                    
                    storage: Dict[str, Any] = self.collect_storage_data()
                    # Calculate real-time disk I/O MB/s
                    try:
                        current_io = psutil.disk_io_counters()
                        if current_io and self.last_disk_io:
                            read_delta = current_io.read_bytes - self.last_disk_io.read_bytes
                            write_delta = current_io.write_bytes - self.last_disk_io.write_bytes
                            # Convert to MB/s (divide by interval and convert bytes to MB)
                            storage['io_read_mbs'] = (read_delta / self.polling_interval) / (1024 * 1024)
                            storage['io_write_mbs'] = (write_delta / self.polling_interval) / (1024 * 1024)
                        else:
                            storage['io_read_mbs'] = 0.0
                            storage['io_write_mbs'] = 0.0
                        self.last_disk_io = current_io
                    except Exception as e:
                        logger.debug(f"Disk I/O rate calculation error: {e}")
                        storage['io_read_mbs'] = 0.0
                        storage['io_write_mbs'] = 0.0
                    self.storage_updated.emit(storage)
                    
                    # Ping/Jitter Analysis
                    avg_ping, jitter = 0.0, 0.0
                    try:
                        avg_ping, jitter = self.network_analyzer.measure_ping_jitter()
                    except Exception as e:
                        logger.debug(f"Ping/jitter measurement error: {e}")
                    
                    # Collect network data (multi-adapter support)
                    try:
                        # Get all network interfaces
                        current_net_io = psutil.net_io_counters(pernic=True)
                        
                        # Initialize available NICs list and select first active one
                        if not self.available_nics:
                            self.available_nics = list(psutil.net_if_addrs().keys())
                            # Select first active NIC with traffic
                            for nic in self.available_nics:
                                if nic in current_net_io and current_net_io[nic].bytes_recv > 0:
                                    self.selected_nic = nic
                                    logger.info(f"[NET] Selected primary adapter: {nic}")
                                    break
                            # Fallback to first available if none have traffic
                            if not self.selected_nic and self.available_nics:
                                self.selected_nic = self.available_nics[0]
                        
                        # Calculate deltas for all adapters
                        net_stats: Dict[str, Dict[str, float]] = {}
                        
                        if current_net_io and self.last_net_io:
                            for adapter_name, current_stats in current_net_io.items():
                                if adapter_name in self.last_net_io:
                                    last_stats = self.last_net_io[adapter_name]
                                    
                                    # Calculate deltas
                                    rx_delta = current_stats.bytes_recv - last_stats.bytes_recv
                                    tx_delta = current_stats.bytes_sent - last_stats.bytes_sent
                                    
                                    # Convert to MB/s
                                    rx_mbs = (rx_delta / self.polling_interval) / (1024 * 1024)
                                    tx_mbs = (tx_delta / self.polling_interval) / (1024 * 1024)
                                    
                                    net_stats[adapter_name] = {
                                        'rx': max(0.0, rx_mbs),  # Prevent negative values
                                        'tx': max(0.0, tx_mbs),
                                        'total_rx_mb': current_stats.bytes_recv / (1024 * 1024),
                                        'total_tx_mb': current_stats.bytes_sent / (1024 * 1024)
                                    }
                        
                        # Store current state for next iteration
                        self.last_net_io = current_net_io
                        
                        # Emit only selected NIC data to save performance
                        if self.selected_nic and self.selected_nic in net_stats:
                            selected_stats = net_stats[self.selected_nic]
                            
                            # Get bandwidth hogs
                            network_hogs: List[Tuple[str, int]] = []
                            try:
                                self.network_analyzer.analyze_bandwidth_hogs()
                                hogs_dict = self.network_analyzer.current_bandwidth_hogs
                                network_hogs = [(name, count) for name, count in hogs_dict.items()]
                            except Exception as e:
                                logger.debug(f"Bandwidth hogs error: {e}")
                            
                            network_data: Dict[str, Any] = {
                                'adapter': self.selected_nic,
                                'rx_mbs': selected_stats['rx'],
                                'tx_mbs': selected_stats['tx'],
                                'downloaded': selected_stats['total_rx_mb'],
                                'uploaded': selected_stats['total_tx_mb'],
                                'ping': avg_ping,
                                'jitter': jitter,
                                'network_hogs': network_hogs,
                                'all_adapters': net_stats  # Include all for advanced view
                            }
                            self.network_updated.emit(network_data)
                        elif current_net_io:
                            # Fallback: emit aggregate data if no NIC selected
                            total_rx = sum(s.bytes_recv for s in current_net_io.values()) / (1024 * 1024)
                            total_tx = sum(s.bytes_sent for s in current_net_io.values()) / (1024 * 1024)
                            network_data = {
                                'adapter': 'Aggregate',
                                'rx_mbs': 0.0,
                                'tx_mbs': 0.0,
                                'downloaded': total_rx,
                                'uploaded': total_tx,
                                'ping': avg_ping,
                                'jitter': jitter,
                                'network_hogs': [],
                                'all_adapters': {}
                            }
                            self.network_updated.emit(network_data)
                    except Exception as e:
                        error_type: str = type(e).__name__
                        logger.debug(f"Network data collection error ({error_type}): {e}")
                
                # Sleep to match polling interval
                time.sleep(self.polling_interval)
                
            except Exception as e:
                logger.error(f"Hardware monitor worker error: {e}")
                time.sleep(2.0)
    
    def stop(self) -> None:
        """Stop the monitoring loop"""
        self.is_running = False
        logger.info("Hardware monitor worker thread stopping")

class VitreosArchitect(QMainWindow):
    """Main application window with advanced liquid glass aesthetics"""
    
    def __init__(self) -> None:
        super().__init__()
        logger.info("Initializing Vitreos Architect application")
        
        # Check PyQt6 availability
        if not PYQT6_AVAILABLE:
            logger.critical("PyQt6 is not available - application cannot start")
            self.show_error_dialog("PyQt6 is required for the Vitreos interface.\n\nRun 'install_requirements.bat' to install it.")
            sys.exit(1)
            
        # Application state

        # Initialize Active Threat Mitigation
        self.shield = VitreosShield(alert_callback=self._trigger_shield_alert)
        self.shield.start()
        self.is_running: bool = False
        self.stats: SystemStats = SystemStats()
        self.config: ConfigDict = self.load_config()
        
        # Hardware monitoring worker and thread
        self.monitor_worker: Optional[HardwareMonitorWorker] = None
        self.monitor_thread: Optional[QThread] = None
        
        # Frameless window dragging state
        self.is_dragging: bool = False
        self.drag_position: Optional[QPoint] = None
        self.header_widget: Optional[QFrame] = None
        
        # System tray icon
        self.tray_icon: Optional[QSystemTrayIcon] = None
        
        # Database for hardware history
        from vitreos_db import VitreosDB
        self.database: VitreosDB = VitreosDB()
        self.db_write_counter: int = 0  # Counter for 60-second throttling
        
        # Advanced monitoring systems
        self.security_monitor: SecurityMonitor = SecurityMonitor()
        self.network_analyzer: NetworkAnalyzer = NetworkAnalyzer()
        self.predictive_alert: PredictiveThermalAlert = PredictiveThermalAlert()
        self.alert_manager: AlertManager = AlertManager(self.tray_icon, self.database)
        
        # Security monitoring thread
        self.security_thread: Optional[SecurityMonitorThread] = None
        self.security_monitoring_active: bool = False
        
        # Remote tab checkboxes
        self.alert_usb_connected: QCheckBox
        self.alert_webcam_active: QCheckBox
        
        # HUD mode state
        self.hud_mode_active: bool = False
        self.normal_geometry: Optional[Any] = None  # Store normal window geometry when entering HUD mode
        self.mini_mode_button: Optional[QPushButton] = None  # Reference to mini mode button for text updates
        
        # UI Components - explicitly typed
        self.status_bar: QStatusBar
        self.webhook_input: QLineEdit
        self.console_output: QPlainTextEdit
        self.pulse_log_widget: SystemPulseLog
        
        # Module content widgets
        self.cpu_content: CPUMonitorModule
        self.gpu_content: GPUMonitorModule
        self.mem_content: MemoryArrayModule
        self.disk_content: DiskArrayModule
        self.net_content: NetworkInterfaceModule
        self.thermal_content: ThermalControlModule
        
        # Monitoring cards - explicitly typed
        self.cpu_temp_card: LiquidGlassCard
        self.gpu_temp_card: LiquidGlassCard
        self.cpu_usage_card: LiquidGlassCard
        self.gpu_usage_card: LiquidGlassCard
        self.gpu_vram_card: LiquidGlassCard
        self.gpu_fan_card: LiquidGlassCard
        self.ram_card: LiquidGlassCard
        self.disk_card: LiquidGlassCard
        self.power_card: LiquidGlassCard
        self.predictive_card: LiquidGlassCard
        self.ping_card: LiquidGlassCard
        self.jitter_card: LiquidGlassCard
        self.download_card: LiquidGlassCard
        self.uploaded_card: LiquidGlassCard
        self.gpu_clock_card: LiquidGlassCard
        self.gpu_power_card: LiquidGlassCard
        self.gpu_temp_pro_card: LiquidGlassCard
        self.gpu_memory_pro_card: LiquidGlassCard
        self.gpu_hotspot_card: LiquidGlassCard
        self.read_bytes_card: LiquidGlassCard
        self.write_bytes_card: LiquidGlassCard
        self.read_count_card: LiquidGlassCard
        self.write_count_card: LiquidGlassCard
        
        # New segmented widgets
        self.cpu_thread_matrix: CPUThreadMatrix
        self.gpu_circular_hud: GPUCircularHUD
        self.network_waveform: NetworkWaveform
        
        # Tournament features
        self.polling_slider: Any
        self.polling_label: Any
        self.generate_report_btn: Any
        self.security_breach: bool = False
        self.breach_flicker_timer: QTimer = QTimer(self)
        self.breach_flicker_state: bool = False
        self.breach_flicker_timer.timeout.connect(self.toggle_breach_flicker)  # type: ignore
        
        # Tables - explicitly typed
        self.hogs_table: QTableWidget
        self.processes_table: QTableWidget
        self.drives_table: QTableWidget
        self.events_table: QTableWidget
        self.logbook_list_widget: QTextEdit
        
        # Progress bars and other widgets
        self.vram_progress_bar: QProgressBar
        self.security_toggle: QPushButton
        self.clear_events_btn: QPushButton
        self.webhook_test_btn: QPushButton
        self.remote_webhook_url_input: QLineEdit
        self.alert_high_temp: QCheckBox
        self.alert_high_gpu: QCheckBox
        self.alert_high_cpu: QCheckBox
        self.alert_disk_full: QCheckBox
        self.startup_checkbox: QCheckBox
        
        # Setup window
        logger.info("Setting up application window")
        self.setup_window()
        logger.info("UI initialization started")
        self.setup_ui()
        logger.info("UI initialized successfully")
        self.setup_system_tray()
        logger.info("System tray initialized")
        self.setup_monitoring()
        logger.info("Monitoring systems initialized")
        
        # Setup logbook file tailing
        self.setup_logbook_tailing()
        
    def show_error_dialog(self, message: str) -> None:
        """Show error dialog for missing dependencies"""
        msg: QMessageBox = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(message)
        msg.setWindowTitle("Missing Dependencies")
        msg.exec()
        
    def setup_window(self) -> None:
        """Setup main window properties"""
        self.setWindowTitle("Vitreos • Architect Edition")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # Set window icon from resource path
        icon_path: str = resource_path("logo.ico")
        window_icon: QIcon = QIcon(icon_path)
        if not window_icon.isNull():
            self.setWindowIcon(window_icon)
        else:
            # Fallback to system theme
            self.setWindowIcon(QIcon.fromTheme("system-monitor"))
        
        # Remove window frame for cyberdeck aesthetic
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Cyberdeck Background - Absolute dark
        palette: QPalette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(8, 8, 10))  # #08080a
        self.setPalette(palette)
        
        # Center window
        self.center_window()
        
    def setup_system_tray(self) -> None:
        """Setup system tray icon with context menu"""
        try:
            # Create tray icon
            self.tray_icon = QSystemTrayIcon(self)
            
            # Load icon from resource path (works in PyInstaller bundles)
            icon_path = resource_path("logo.ico")
            icon = QIcon(icon_path)
            
            # Fallback to theme or colored pixmap if resource not found
            if icon.isNull():
                icon = QIcon.fromTheme("vitreos-icon")
            
            if icon.isNull():
                # Create a simple colored pixmap as last resort
                pixmap = QPixmap(64, 64)
                pixmap.fill(QColor(0, 242, 255))  # Cyan color
                icon = QIcon(pixmap)
            
            self.tray_icon.setIcon(icon)
            
            # Create context menu
            tray_menu = QMenu(self)
            
            show_action = tray_menu.addAction("Show")  # type: ignore[reportUnknownMemberType]
            if show_action is not None:
                show_action.triggered.connect(self.show_window)  # type: ignore[arg-type]
            
            hide_action = tray_menu.addAction("Hide")  # type: ignore[reportUnknownMemberType]
            if hide_action is not None:
                hide_action.triggered.connect(self.hide_window)  # type: ignore[arg-type]
            
            tray_menu.addSeparator()
            
            exit_action = tray_menu.addAction("Exit")  # type: ignore[reportUnknownMemberType]
            if exit_action is not None:
                exit_action.triggered.connect(self.exit_application)  # type: ignore[arg-type]
            
            self.tray_icon.setContextMenu(tray_menu)
            
            # Handle tray icon click (show/hide on single click)
            self.tray_icon.activated.connect(self.on_tray_icon_activated)  # type: ignore
            
            self.tray_icon.show()
            logger.info("System tray icon initialized")
        except Exception as e:
            logger.error(f"Failed to initialize system tray: {e}")
    
    def on_tray_icon_activated(self, reason: Any) -> None:
        """Handle tray icon activation"""
        from PyQt6.QtWidgets import QSystemTrayIcon as STI
        if reason == STI.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide_window()
            else:
                self.show_window()
    
    def show_window(self) -> None:
        """Show the window from tray"""
        self.showNormal()
        self.activateWindow()
    
    def hide_window(self) -> None:
        """Hide the window to tray"""
        self.hide()
    
    def exit_application(self) -> None:
        """Exit the application completely"""
        logger.info("Exit action triggered from tray")
        # Stop the hardware monitor worker thread
        if self.monitor_worker:
            self.monitor_worker.stop()
        if self.monitor_thread is not None and self.monitor_thread.isRunning():
            self.monitor_thread.quit()
            self.monitor_thread.wait()
        
        # Hide tray icon
        if self.tray_icon:
            self.tray_icon.hide()
        
        # Save config and exit
        self.is_running = False
        self.security_monitor.monitoring_active = False
        self.save_config()
        
        # Force quit the application
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
        
    def center_window(self) -> None:
        """Center window on screen"""
        screen: Optional[Any] = QApplication.primaryScreen()
        if screen is not None:
            screen_geometry: Any = screen.geometry()
            window: Any = self.geometry()
            x: int = int((screen_geometry.width() - window.width()) / 2)
            y: int = int((screen_geometry.height() - window.height()) / 2)
            self.move(x, y)
        
    def setup_ui(self) -> None:
        """Setup the main user interface with tab navigation"""
        # Main widget and layout
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #08080a;")
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left Column: System Pulse Log
        pulse_log_widget = SystemPulseLog()
        self.pulse_log_widget = pulse_log_widget
        main_layout.addWidget(pulse_log_widget)
        
        # Right side: Main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(5)
        
        # Header with title and controls
        header_widget = self.create_header()
        content_layout.addWidget(header_widget)
        
        # Tab widget for navigation
        from PyQt6.QtWidgets import QTabWidget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bc13fe
                background-color: #08080a
            }
            QTabBar::tab {
                background-color: #1a1a1e
                color: #888888
                border: 1px solid #2a2a2e
                padding: 8px 16px
                margin-right: 2px
                font-family: 'Courier New', 'Consolas', monospace
                font-size: 9pt
            }
            QTabBar::tab:selected {
                background-color: #bc13fe
                color: #ffffff
                font-weight: bold
            }
            QTabBar::tab:hover {
                background-color: #2a2a2e
                color: #00f2ff
            }
        """)
        
        content_layout.addWidget(self.tab_widget)
        main_layout.addWidget(content_widget)
        
        # Create all tabs
        self.create_vitals_tab()
        self.create_network_tab()
        self.create_processes_tab()
        self.create_gpu_pro_tab()
        self.create_storage_tab()
        self.create_security_tab()
        self.create_logbook_tab()
        self.create_console_tab()
        self.create_remote_tab()
        self.create_settings_tab()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #08080a
                color: #00f2ff
                border-top: 2px solid #bc13fe
                font-family: 'Courier New', 'Consolas', monospace
                font-size: 8pt
            }
        """)
        self.setStatusBar(self.status_bar)
        
        self.setCentralWidget(main_widget)
        
        # Apply cyberdeck stylesheet with scanline effect and global transparency
        self.setStyleSheet("""
            QMainWindow {
                background: #08080a
                background-image: linear-gradient(0deg, transparent 50%, rgba(188, 19, 254, 0.03) 50%)
                background-size: 100% 4px
            }
            QWidget {
                background-color: transparent
                font-family: 'Consolas', 'Courier New', monospace
            }
            QLabel {
                background: transparent
                font-family: 'Consolas', 'Courier New', monospace
                font-size: 8pt
                color: rgba(255, 255, 255, 0.6)
            }
            VitreosModule QWidget {
                background: transparent
            }
            QGroupBox {
                background: transparent
            }
        """)
        
    def create_header(self) -> QFrame:
        """Create the header with title and controls"""
        # Create a widget to serve as the drag handle
        header_widget = QFrame()
        header_widget.setStyleSheet("""
            QFrame {
                background-color: transparent
                border: none
            }
        """)
        header_widget.setCursor(Qt.CursorShape.OpenHandCursor)
        self.header_widget = header_widget
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title section
        title_layout = QVBoxLayout()
        title_label = QLabel("[VITREOS::CYBERDECK]")
        title_label.setStyleSheet("""
            QLabel {
                color: #bc13fe
                font-family: 'Courier New', 'Consolas', monospace
                font-size: 14pt
                font-weight: bold
                letter-spacing: 2px
            }
        """)
        
        subtitle_label = QLabel(">INFORMATION_OVERLOAD")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #00f2ff
                font-family: 'Courier New', 'Consolas', monospace
                font-size: 8pt
                font-weight: normal
            }
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        # Controls section
        controls_layout = QHBoxLayout()
        
        # Mini Mode (HUD) button
        self.mini_mode_button = QPushButton("[_]")
        self.mini_mode_button.setFixedSize(35, 20)
        self.mini_mode_button.setStyleSheet("""
            QPushButton {
                background-color: #08080a
                border: 1px solid #bc13fe
                border-radius: 0px
                color: #bc13fe
                font-family: 'Courier New', 'Consolas', monospace
                font-size: 8pt
                font-weight: bold
            }
            QPushButton:hover {
                background-color: #bc13fe
                color: #08080a
            }
        """)
        self.mini_mode_button.clicked.connect(self.toggle_hud_mode)  # type: ignore
        
        # Minimize button
        minimize_btn = QPushButton("[-]")
        minimize_btn.setFixedSize(35, 20)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #08080a
                border: 1px solid #00f2ff
                border-radius: 0px
                color: #00f2ff
                font-family: 'Courier New', 'Consolas', monospace
                font-size: 8pt
                font-weight: bold
            }
            QPushButton:hover {
                background-color: #00f2ff
                color: #08080a
            }
        """)
        minimize_btn.clicked.connect(self.hide_window)  # type: ignore
        
        # Close button
        close_btn = QPushButton("[X]")
        close_btn.setFixedSize(35, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #08080a
                border: 1px solid #ff8c00
                border-radius: 0px
                color: #ff8c00
                font-family: 'Courier New', 'Consolas', monospace
                font-size: 8pt
                font-weight: bold
            }
            QPushButton:hover {
                background-color: #ff8c00
                color: #08080a
            }
        """)
        close_btn.clicked.connect(self.close)  # type: ignore
        
        controls_layout.addWidget(self.mini_mode_button)
        controls_layout.addWidget(minimize_btn)
        controls_layout.addWidget(close_btn)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addLayout(controls_layout)
        
        return header_widget
    
    def toggle_hud_mode(self) -> None:
        """Toggle between normal and mini HUD mode"""
        if self.hud_mode_active:
            self.restore_from_hud()
        else:
            self.enter_hud_mode()
    
    def enter_hud_mode(self) -> None:
        """Enter mini overlay mode - shrink window, hide tabs"""
        self.hud_mode_active = True
        
        # Store current geometry
        self.normal_geometry = self.geometry()
        
        # Hide tabs and sidebar
        if hasattr(self, 'tab_widget'):
            self.tab_widget.hide()
        self.status_bar.hide()
        
        # Update button text (null-safe)
        if self.mini_mode_button:
            self.mini_mode_button.setText("□")  # Show maximize symbol
            self.mini_mode_button.setToolTip("Restore to normal size")
        
        # Shrink window to 300x150
        screen = QApplication.primaryScreen()
        if screen is not None:
            screen_geometry = screen.geometry()
            # Position in bottom-right corner
            x = screen_geometry.width() - 320
            y = screen_geometry.height() - 170
            self.setGeometry(x, y, 300, 150)
        
        # Set window to stay on top
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.show()
        
        logger.info("Entered HUD mode")
    
    def restore_from_hud(self) -> None:
        """Restore normal mode from HUD overlay"""
        self.hud_mode_active = False
        
        # Remove stay-on-top flag
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        
        # Show tabs and status bar
        if hasattr(self, 'tab_widget'):
            self.tab_widget.show()
        self.status_bar.show()
        
        # Update button text (null-safe)
        if self.mini_mode_button:
            self.mini_mode_button.setText("⊞")  # Show minimize symbol
            self.mini_mode_button.setToolTip("Enter HUD mode")
        
        # Restore previous geometry
        if self.normal_geometry:
            self.setGeometry(self.normal_geometry)
        
        self.show()
        
        logger.info("Exited HUD mode")
        
    def create_vitals_tab(self) -> None:
        """Create the Vitals tab with 3x2 hardware grid"""
        vitals_widget = QWidget()
        vitals_layout = QVBoxLayout(vitals_widget)
        vitals_layout.setSpacing(10)
        vitals_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab title
        tab_title = QLabel("VITALS - Real-time System Health")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff
                font-size: 18px
                font-weight: 700
                margin-bottom: 15px
            }
        """)
        vitals_layout.addWidget(tab_title)
        
        # Create 3x2 hardware grid with tight spacing
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)
        grid_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create module windows for 3x2 grid
        # Top Row: Processing (CPU, GPU, Memory)
        self.cpu_window = VitreosModule("CPU_MONITOR")
        cpu_content = CPUMonitorModule()
        cpu_content.parent_module = self.cpu_window
        self.cpu_window.set_content(cpu_content)
        self.cpu_content = cpu_content
        
        self.gpu_window = VitreosModule("GPU_MONITOR")
        gpu_content = GPUMonitorModule()
        gpu_content.parent_module = self.gpu_window
        self.gpu_window.set_content(gpu_content)
        self.gpu_content = gpu_content
        
        self.mem_window = VitreosModule("MEM_ARRAY")
        mem_content = MemoryArrayModule()
        self.mem_window.set_content(mem_content)
        self.mem_content = mem_content
        
        # Bottom Row: I/O (Network, Thermal, Disk)
        self.net_window = VitreosModule("NET_INTERFACE")
        net_content = NetworkInterfaceModule()
        self.net_window.set_content(net_content)
        self.net_content = net_content
        
        self.thermal_window = VitreosModule("THERMAL_CTRL")
        thermal_content = ThermalControlModule()
        thermal_content.parent_module = self.thermal_window
        self.thermal_window.set_content(thermal_content)
        self.thermal_content = thermal_content
        
        self.disk_window = VitreosModule("DISK_ARRAY")
        disk_content = DiskArrayModule()
        self.disk_window.set_content(disk_content)
        self.disk_content = disk_content
        
        # Place modules in 3x2 grid - Spatial Hierarchy:
        # Top Row (Processing): CPU -> GPU -> Memory
        grid_layout.addWidget(self.cpu_window, 0, 0)      # Top Left
        grid_layout.addWidget(self.gpu_window, 0, 1)      # Top Middle
        grid_layout.addWidget(self.mem_window, 0, 2)      # Top Right
        
        # Bottom Row (I/O): Network -> Thermal -> Disk
        grid_layout.addWidget(self.net_window, 1, 0)      # Bottom Left
        grid_layout.addWidget(self.thermal_window, 1, 1)  # Bottom Middle
        grid_layout.addWidget(self.disk_window, 1, 2)     # Bottom Right
        
        vitals_layout.addLayout(grid_layout)
        self.tab_widget.addTab(vitals_widget, "Vitals")
        
    def create_network_tab(self) -> None:
        """Create the Network tab with advanced connectivity monitoring"""
        network_widget = QWidget()
        network_layout = QVBoxLayout(network_widget)
        
        # Tab title
        tab_title = QLabel("NETWORK - Connectivity & Traffic Analysis")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff
                font-size: 18px
                font-weight: 700
                margin-bottom: 15px
            }
        """)
        network_layout.addWidget(tab_title)
        
        # Adapter selector
        from PyQt6.QtWidgets import QComboBox
        adapter_container = QWidget()
        adapter_layout = QHBoxLayout(adapter_container)
        adapter_layout.setContentsMargins(0, 0, 0, 5)
        
        adapter_label = QLabel("[ADAPTER_SELECT]")
        adapter_label.setStyleSheet("""
            QLabel {
                color: #bc13fe
                font-family: 'Consolas', monospace
                font-size: 9pt
                font-weight: bold
            }
        """)
        
        self.network_adapter_combo = QComboBox()
        self.network_adapter_combo.setStyleSheet("""
            QComboBox {
                background-color: #08080a
                border: 1px solid #bc13fe
                border-radius: 0px
                color: #00f2ff
                font-family: 'Consolas', monospace
                font-size: 8pt
                padding: 3px 8px
                min-width: 200px
            }
            QComboBox:hover {
                border: 1px solid #00f2ff
            }
            QComboBox::drop-down {
                border: none
                width: 20px
            }
            QComboBox::down-arrow {
                image: none
                border-left: 4px solid transparent
                border-right: 4px solid transparent
                border-top: 6px solid #bc13fe
                margin-right: 5px
            }
            QListView {
                background-color: #08080a
                border: 1px solid #bc13fe
                outline: none
            }
            QListView::item {
                color: #00f2ff
                padding: 4px
            }
            QListView::item:hover, QListView::item:selected {
                background-color: #bc13fe
                color: #ffffff
            }
        """)
        self.network_adapter_combo.addItem("Detecting adapters...")
        self.network_adapter_combo.currentTextChanged.connect(lambda text: setattr(self.monitor_worker, 'selected_nic', text) if self.monitor_worker and text != "Detecting adapters..." else None)  # type: ignore
        
        adapter_layout.addWidget(adapter_label)
        adapter_layout.addWidget(self.network_adapter_combo)
        adapter_layout.addStretch()
        
        network_layout.addWidget(adapter_container)
        
        # Network Waveform Area
        self.network_waveform = NetworkWaveform()
        self.network_waveform.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border: 1px solid #bc13fe; border-radius: 0px;")
        network_layout.addWidget(self.network_waveform)
        
        # Network monitoring grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        
        # Network cards
        self.ping_card = LiquidGlassCard("Ping (ms)")
        self.ping_card.update_value(0, "ms", "Stable", "#00f2ff")
        
        self.jitter_card = LiquidGlassCard("Jitter (ms)")
        self.jitter_card.update_value(0, "ms", "Stable", "#4ade80")
        
        self.download_card = LiquidGlassCard("Downloaded")
        self.download_card.update_value(0, "GB", "Normal", "#00d2ff")
        
        self.uploaded_card = LiquidGlassCard("Uploaded")
        self.uploaded_card.update_value(0, "GB", "Normal", "#ff6b6b")
        
        # Bandwidth hogs table
        hogs_group = QGroupBox("Bandwidth Hogs")
        hogs_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                border-radius: 12px
                padding: 15px
                margin: 0
            }
            QGroupBox::title {
                color: #ffffff
                font-size: 12px
                font-weight: 600
                subcontrol-origin: margin
                subcontrol-position: top left
                padding: 0 5px
            }
        """)
        
        hogs_layout = QVBoxLayout(hogs_group)
        self.hogs_table = QTableWidget()
        self.hogs_table.setColumnCount(2)
        self.hogs_table.setHorizontalHeaderLabels(["Process", "Connections"])  # type: ignore[arg-type]
        self.hogs_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        header = self.hogs_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[arg-type]
        self.hogs_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                color: #ffffff
                font-size: 12px
            }
            QTableWidget::item {
                padding: 5px
            }
            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.1)
                color: #ffffff
                font-weight: 600
            }
        """)
        hogs_layout.addWidget(self.hogs_table)
        
        # Add to grid
        grid_layout.addWidget(self.ping_card, 0, 0)
        grid_layout.addWidget(self.jitter_card, 0, 1)
        grid_layout.addWidget(self.download_card, 1, 0)
        grid_layout.addWidget(self.uploaded_card, 1, 1)
        grid_layout.addWidget(hogs_group, 0, 2, 2, 1)
        
        network_layout.addLayout(grid_layout)
        self.tab_widget.addTab(network_widget, "Network")
    
    def on_adapter_changed(self, adapter_name: str) -> None:
        """Handle network adapter selection change."""
        if self.monitor_worker and adapter_name != "Detecting adapters...":
            self.monitor_worker.selected_nic = adapter_name
            logger.info(f"[NET] Switched to adapter: {adapter_name}")
    
    def create_processes_tab(self) -> None:
        """Create the Processes tab with Purge Protocol controls"""
        processes_widget = QWidget()
        processes_layout = QVBoxLayout(processes_widget)
        
        # Tab title
        tab_title = QLabel("PROCESSES - Purge Protocol")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff
                font-size: 18px
                font-weight: 700
                margin-bottom: 15px
            }
        """)
        processes_layout.addWidget(tab_title)
        
        # Purge Protocol Button (Large, Centered)
        purge_btn = QPushButton("⚠ INITIATE PURGE PROTOCOL")
        purge_btn.setFixedHeight(60)
        purge_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 2px solid #ff8c00
                border-radius: 0px
                color: #ff8c00
                font-family: 'Courier New', monospace
                font-size: 14pt
                font-weight: bold
                padding: 15px
            }
            QPushButton:hover {
                background-color: #ff8c00
                color: #000000
            }
        """)
        purge_btn.clicked.connect(self.execute_purge_protocol)  # type: ignore
        processes_layout.addWidget(purge_btn)
        
        # Target processes table
        table_group = QGroupBox("Target Processes")
        table_group.setStyleSheet("""
            QGroupBox {
                background-color: transparent
                border: 1px solid #bc13fe
                border-radius: 0px
                padding: 15px
                margin-top: 10px
            }
            QGroupBox::title {
                color: #bc13fe
                font-family: 'Courier New', monospace
                font-size: 10pt
                font-weight: bold
                subcontrol-origin: margin
                subcontrol-position: top left
                padding: 0 5px
            }
        """)
        
        table_layout = QVBoxLayout(table_group)
        self.processes_table = QTableWidget()
        self.processes_table.setColumnCount(4)
        self.processes_table.setHorizontalHeaderLabels(["PID", "Target", "RAM (MB)", "CPU %"])  # type: ignore[arg-type]
        header = self.processes_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[arg-type]
        
        self.processes_table.setStyleSheet("""
            QTableWidget {
                background-color: transparent
                border: none
                color: #00f2ff
                font-family: 'Consolas', monospace
                font-size: 9pt
                gridline-color: transparent
            }
            QTableWidget::item {
                padding: 6px
                border-bottom: 1px solid rgba(188, 19, 254, 0.2)
            }
            QHeaderView::section {
                background-color: transparent
                color: #bc13fe
                font-family: 'Courier New', monospace
                font-weight: bold
                font-size: 9pt
                padding: 8px
                border: none
                border-bottom: 2px solid #bc13fe
            }
        """)
        
        table_layout.addWidget(self.processes_table)
        processes_layout.addWidget(table_group)
        
        # eSports Optimization Suite
        esports_container = QWidget()
        esports_layout = QHBoxLayout(esports_container)
        esports_layout.setSpacing(10)
        
        # Left Panel: CPU Priority Engine
        priority_group = QGroupBox("CPU Priority Engine")
        priority_group.setStyleSheet("""
            QGroupBox {
                background-color: transparent
                border: 1px solid #00f2ff
                border-radius: 0px
                padding: 15px
                margin-top: 10px
            }
            QGroupBox::title {
                color: #00f2ff
                font-family: 'Courier New', monospace
                font-size: 10pt
                font-weight: bold
                subcontrol-origin: margin
                subcontrol-position: top left
                padding: 0 5px
            }
        """)
        
        priority_layout = QVBoxLayout(priority_group)
        priority_label = QLabel("Boost games to High Priority, throttle background apps to Below Normal.")
        priority_label.setStyleSheet("color: #888888; font-family: 'Consolas'; font-size: 8pt;")
        priority_label.setWordWrap(True)
        priority_layout.addWidget(priority_label)
        
        priority_btn = QPushButton("⚡ OPTIMIZE PRIORITIES")
        priority_btn.setFixedHeight(50)
        priority_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 1px solid #00f2ff
                border-radius: 0px
                color: #00f2ff
                font-family: 'Courier New', monospace
                font-size: 11pt
                font-weight: bold
            }
            QPushButton:hover {
                background-color: #00f2ff
                color: #000000
            }
        """)
        priority_btn.clicked.connect(self.optimize_cpu_priorities)  # type: ignore
        priority_layout.addWidget(priority_btn)
        
        # Right Panel: Core Affinity Isolator
        affinity_group = QGroupBox("Core Affinity Isolator")
        affinity_group.setStyleSheet("""
            QGroupBox {
                background-color: transparent
                border: 1px solid #bc13fe
                border-radius: 0px
                padding: 15px
                margin-top: 10px
            }
            QGroupBox::title {
                color: #bc13fe
                font-family: 'Courier New', monospace
                font-size: 10pt
                font-weight: bold
                subcontrol-origin: margin
                subcontrol-position: top left
                padding: 0 5px
            }
        """)
        
        affinity_layout = QVBoxLayout(affinity_group)
        affinity_label = QLabel("Force background apps to last 2 CPU threads to dedicate L3 Cache to games.")
        affinity_label.setStyleSheet("color: #888888; font-family: 'Consolas'; font-size: 8pt;")
        affinity_label.setWordWrap(True)
        affinity_layout.addWidget(affinity_label)
        
        affinity_btn = QPushButton("🔒 ISOLATE BACKGROUND APPS")
        affinity_btn.setFixedHeight(50)
        affinity_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent
                border: 1px solid #bc13fe
                border-radius: 0px
                color: #bc13fe
                font-family: 'Courier New', monospace
                font-size: 11pt
                font-weight: bold
            }
            QPushButton:hover {
                background-color: #bc13fe
                color: #000000
            }
        """)
        affinity_btn.clicked.connect(self.isolate_core_affinity)  # type: ignore
        affinity_layout.addWidget(affinity_btn)
        
        esports_layout.addWidget(priority_group)
        esports_layout.addWidget(affinity_group)
        
        processes_layout.addWidget(esports_container)
        processes_layout.addStretch()
        
        self.tab_widget.addTab(processes_widget, "Processes")
    
    def create_gpu_pro_tab(self) -> None:
        """Create the GPU Pro tab with detailed NVIDIA statistics"""
        gpu_widget = QWidget()
        gpu_layout = QVBoxLayout(gpu_widget)
        
        # Tab title
        tab_title = QLabel("GPU PRO - Advanced NVIDIA Statistics")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff
                font-size: 18px
                font-weight: 700
                margin-bottom: 15px
            }
        """)
        gpu_layout.addWidget(tab_title)
        
        # GPU stats grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        
        # GPU Clock Speed
        self.gpu_clock_card = LiquidGlassCard("Clock Speed")
        self.gpu_clock_card.update_value(0, "MHz", "Idle", "#00f2ff")
        
        # GPU Power Draw
        self.gpu_power_card = LiquidGlassCard("Power Draw")
        self.gpu_power_card.update_value(0, "W", "Idle", "#ff9800")
        
        # GPU Fan Speed
        self.gpu_fan_card = LiquidGlassCard("Fan Speed")
        self.gpu_fan_card.update_value(0, "%", "Quiet", "#4ade80")
        
        # GPU Temperature (from existing vitals)
        self.gpu_temp_pro_card = LiquidGlassCard("Temperature")
        self.gpu_temp_pro_card.update_value(0, "°C", "Cool", "#00d2ff")
        
        # GPU Memory (from existing vitals)
        self.gpu_memory_pro_card = LiquidGlassCard("VRAM Usage")
        self.gpu_memory_pro_card.update_value(0, "%", "Normal", "#6366f1")

        # GPU Hotspot
        self.gpu_hotspot_card = LiquidGlassCard("Hotspot Temp")
        self.gpu_hotspot_card.update_value(0, "°C", "Cool", "#00d2ff")
        
        # Add to grid
        grid_layout.addWidget(self.gpu_clock_card, 0, 0)
        grid_layout.addWidget(self.gpu_power_card, 0, 1)
        grid_layout.addWidget(self.gpu_fan_card, 0, 2)
        grid_layout.addWidget(self.gpu_temp_pro_card, 1, 0)
        grid_layout.addWidget(self.gpu_memory_pro_card, 1, 1)
        grid_layout.addWidget(self.gpu_hotspot_card, 1, 2)

        # VRAM Progress Bar
        self.vram_progress_bar = QProgressBar()
        self.vram_progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.1)
                border: 1px solid rgba(255, 255, 255, 0.2)
                border-radius: 8px
                color: #ffffff
                font-size: 12px
                font-weight: 600
                text-align: center
            }
            QProgressBar::chunk {
                background-color: #6366f1
                border-radius: 6px
            }
        """)
        grid_layout.addWidget(self.vram_progress_bar, 2, 0, 1, 3)
        
        gpu_layout.addLayout(grid_layout)
        gpu_layout.addStretch()
        
        self.tab_widget.addTab(gpu_widget, "GPU Pro")
    
    def create_storage_tab(self) -> None:
        """Create the Storage tab with disk usage and I/O statistics"""
        storage_widget = QWidget()
        storage_layout = QVBoxLayout(storage_widget)
        
        # Tab title
        tab_title = QLabel("STORAGE - Disk Usage & I/O Activity")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff
                font-size: 18px
                font-weight: 700
                margin-bottom: 15px
            }
        """)
        storage_layout.addWidget(tab_title)
        
        # Drives overview table
        drives_group = QGroupBox("Disk Drives")
        drives_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                border-radius: 12px
                padding: 15px
            }
            QGroupBox::title {
                color: #ffffff
                font-size: 12px
                font-weight: 600
                subcontrol-origin: margin
                subcontrol-position: top left
                padding: 0 5px
            }
        """)
        
        drives_layout = QVBoxLayout(drives_group)
        self.drives_table = QTableWidget()
        self.drives_table.setColumnCount(5)
        self.drives_table.setHorizontalHeaderLabels(["Drive", "Total (GB)", "Used (GB)", "Free (GB)", "Usage %"])  # type: ignore[arg-type]
        header = self.drives_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[arg-type]
        
        self.drives_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                color: #ffffff
                font-size: 12px
            }
            QTableWidget::item {
                padding: 8px
            }
            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.1)
                color: #ffffff
                font-weight: 600
                padding: 8px
            }
        """)
        
        drives_layout.addWidget(self.drives_table)
        storage_layout.addWidget(drives_group)
        
        # I/O Statistics
        io_group = QGroupBox("I/O Activity")
        io_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                border-radius: 12px
                padding: 15px
            }
            QGroupBox::title {
                color: #ffffff
                font-size: 12px
                font-weight: 600
                subcontrol-origin: margin
                subcontrol-position: top left
                padding: 0 5px
            }
        """)
        
        io_layout = QGridLayout(io_group)
        io_layout.setSpacing(20)
        
        self.read_bytes_card = LiquidGlassCard("Total Read")
        self.read_bytes_card.update_value(0, "GB", "Normal", "#4ade80")
        
        self.write_bytes_card = LiquidGlassCard("Total Written")
        self.write_bytes_card.update_value(0, "GB", "Normal", "#ff6b6b")
        
        self.read_count_card = LiquidGlassCard("Read Ops")
        self.read_count_card.update_value(0, "", "Normal", "#00d2ff")
        
        self.write_count_card = LiquidGlassCard("Write Ops")
        self.write_count_card.update_value(0, "", "Normal", "#ff9800")
        
        io_layout.addWidget(self.read_bytes_card, 0, 0)
        io_layout.addWidget(self.write_bytes_card, 0, 1)
        io_layout.addWidget(self.read_count_card, 1, 0)
        io_layout.addWidget(self.write_count_card, 1, 1)
        
        storage_layout.addWidget(io_group)
        storage_layout.addStretch()
        
        self.tab_widget.addTab(storage_widget, "Storage")
    
    def create_security_tab(self) -> None:
        """Create the Security tab with advanced monitoring"""
        security_widget = QWidget()
        security_layout = QVBoxLayout(security_widget)
        
        # Tab title
        tab_title = QLabel("SECURITY - PC Integrity Monitoring")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff
                font-size: 18px
                font-weight: 700
                margin-bottom: 15px
            }
        """)
        security_layout.addWidget(tab_title)
        
        # Security controls
        controls_layout = QHBoxLayout()
        
        self.security_toggle = QPushButton("🛡️ Start Security Monitoring")
        self.security_toggle.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1)
                border: 1px solid rgba(255, 255, 255, 0.2)
                border-radius: 8px
                padding: 10px 20px
                color: #ffffff
                font-size: 12px
                font-weight: 600
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2)
                border-color: #4ade80
            }
        """)
        self.security_toggle.clicked.connect(self.toggle_security_monitoring)  # type: ignore
        
        self.clear_events_btn = QPushButton("🧹 Clear Events")
        self.clear_events_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1)
                border: 1px solid rgba(255, 255, 255, 0.2)
                border-radius: 8px
                padding: 10px 20px
                color: #ffffff
                font-size: 12px
                font-weight: 600
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2)
                border-color: #ff4444
            }
        """)
        self.clear_events_btn.clicked.connect(self.clear_security_events)  # type: ignore
        
        controls_layout.addWidget(self.security_toggle)
        controls_layout.addWidget(self.clear_events_btn)
        controls_layout.addStretch()
        
        security_layout.addLayout(controls_layout)
        
        # Security events table
        events_group = QGroupBox("Security Events")
        events_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                border-radius: 12px
                padding: 15px
                margin: 0
            }
            QGroupBox::title {
                color: #ffffff
                font-size: 12px
                font-weight: 600
                subcontrol-origin: margin
                subcontrol-position: top left
                padding: 0 5px
            }
        """)
        
        events_layout = QVBoxLayout(events_group)
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(4)
        self.events_table.setHorizontalHeaderLabels(["Time", "Type", "Description", "Severity"])  # type: ignore[arg-type]
        header = self.events_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[arg-type]
        self.events_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                color: #ffffff
                font-size: 12px
            }
            QTableWidget::item {
                padding: 5px
            }
            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.1)
                color: #ffffff
                font-weight: 600
            }
        """)
        events_layout.addWidget(self.events_table)
        
        security_layout.addWidget(events_group)
        self.tab_widget.addTab(security_widget, "Security")
        
    def create_logbook_tab(self) -> None:
        """Create the Logbook tab with historical data"""
        logbook_widget = QWidget()
        logbook_layout = QVBoxLayout(logbook_widget)
        
        # Tab title
        tab_title = QLabel("LOGBOOK - Historical Data & Analytics")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff
                font-size: 18px
                font-weight: 700
                margin-bottom: 15px
            }
        """)
        logbook_layout.addWidget(tab_title)
        
        # Log text area
        self.logbook_list_widget = QTextEdit()
        self.logbook_list_widget.setReadOnly(True)
        self.logbook_list_widget.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                border-radius: 8px
                color: #ffffff
                font-family: 'Courier New', monospace
                font-size: 11px
                padding: 10px
            }
        """)
        logbook_layout.addWidget(self.logbook_list_widget)
        
        # Generate Report Button
        self.generate_report_btn = QPushButton("📊 GENERATE_REPORT")
        self.generate_report_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 242, 255, 0.2)
                border: 1px solid #00f2ff
                border-radius: 0px
                color: #00f2ff
                font-family: 'Courier New'
                font-size: 11pt
                font-weight: bold
                padding: 10px
            }
            QPushButton:hover {
                background-color: rgba(0, 242, 255, 0.3)
            }
        """)
        self.generate_report_btn.clicked.connect(self.generate_stability_report)  # type: ignore
        logbook_layout.addWidget(self.generate_report_btn)
        
        logbook_layout.addStretch()
        
        self.tab_widget.addTab(logbook_widget, "Logbook")
        
        
    def create_console_tab(self) -> None:
        """Create the Console tab with live debug terminal"""
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        
        # Tab title
        tab_title = QLabel("CONSOLE - Live Debug Terminal")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff
                font-size: 18px
                font-weight: 700
                margin-bottom: 15px
            }
        """)
        console_layout.addWidget(tab_title)
        
        # Test Webhook button (single action)
        webhook_test_container = QWidget()
        webhook_test_layout = QHBoxLayout(webhook_test_container)
        webhook_test_layout.setContentsMargins(0, 0, 0, 10)
        
        self.webhook_test_btn = QPushButton("🧪 Test Discord Webhook")
        self.webhook_test_btn.setFixedHeight(40)
        self.webhook_test_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 242, 255, 0.1)
                border: 1px solid #00f2ff
                border-radius: 6px
                padding: 10px 20px
                color: #00f2ff
                font-family: 'Courier New', monospace
                font-size: 11pt
                font-weight: 600
            }
            QPushButton:hover {
                background-color: rgba(0, 242, 255, 0.2)
                border-color: #00f2ff
            }
        """)
        self.webhook_test_btn.clicked.connect(self.test_webhook)  # type: ignore
        
        webhook_test_layout.addWidget(self.webhook_test_btn)
        webhook_test_layout.addStretch()
        console_layout.addWidget(webhook_test_container)
        
        # --- THE CMD TERMINAL (BULLETPROOF FIX) ---
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setMinimumHeight(300)  # THIS PREVENTS IT FROM DISAPPEARING
        self.console_output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0a0a0a
                color: #00ff00
                border: 1px solid rgba(0, 255, 0, 0.2)
                border-radius: 6px
                font-family: 'Consolas', 'Courier New', monospace
                font-size: 12px
                padding: 10px
                margin-top: 15px
            }
        """)
        self.console_output.setPlaceholderText("Waiting for debug output...")
        
        # Add widget with stretch factor 1
        console_layout.addWidget(self.console_output, 1)
        
        self.tab_widget.addTab(console_widget, "Console")
    
    def create_remote_tab(self) -> None:
        """Create the Remote tab for Discord Webhook and alert configuration"""
        remote_widget = QWidget()
        remote_layout = QVBoxLayout(remote_widget)
        
        # Tab title
        tab_title = QLabel("REMOTE - Discord Integration & Alerts")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff
                font-size: 18px
                font-weight: 700
                margin-bottom: 15px
            }
        """)
        remote_layout.addWidget(tab_title)
        
        # Discord webhook configuration group
        webhook_group = QGroupBox("Discord Webhook Configuration")
        webhook_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                border-radius: 12px
                padding: 15px
            }
            QGroupBox::title {
                color: #ffffff
                font-size: 12px
                font-weight: 600
                subcontrol-origin: margin
                subcontrol-position: top left
                padding: 0 5px
            }
        """)
        
        webhook_layout = QVBoxLayout(webhook_group)
        webhook_layout.setSpacing(10)
        
        # Webhook URL label
        webhook_label = QLabel("Webhook URL:")
        webhook_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 600;")
        webhook_layout.addWidget(webhook_label)
        
        # Webhook URL input (also assign to self.webhook_input for compatibility)
        self.remote_webhook_url_input = QLineEdit()
        self.webhook_input = self.remote_webhook_url_input  # Alias for setup_monitoring
        self.remote_webhook_url_input.setPlaceholderText("https://discord.com/api/webhooks/...")
        self.remote_webhook_url_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                border-radius: 6px
                color: #ffffff
                padding: 8px
            }
            QLineEdit:focus {
                border: 1px solid #00f2ff
            }
        """)
        webhook_layout.addWidget(self.remote_webhook_url_input)
        
        # Save webhook button
        save_webhook_btn = QPushButton("Save Webhook")
        save_webhook_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 242, 255, 0.2)
                border: 1px solid #00f2ff
                border-radius: 6px
                color: #00f2ff
                font-weight: 600
                padding: 8px
            }
            QPushButton:hover {
                background-color: rgba(0, 242, 255, 0.3)
            }
        """)
        webhook_layout.addWidget(save_webhook_btn)
        
        remote_layout.addWidget(webhook_group)
        
        # Alert configuration group
        alert_group = QGroupBox("Alert Triggers")
        alert_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                border-radius: 12px
                padding: 15px
            }
            QGroupBox::title {
                color: #ffffff
                font-size: 12px
                font-weight: 600
                subcontrol-origin: margin
                subcontrol-position: top left
                padding: 0 5px
            }
        """)
        
        alert_layout = QVBoxLayout(alert_group)
        alert_layout.setSpacing(10)
        
        # Alert checkboxes
        self.alert_high_temp = QCheckBox("Alert on High Temperature (>85°C)")
        self.alert_high_temp.setStyleSheet("color: #ffffff; font-size: 12px;")
        alert_layout.addWidget(self.alert_high_temp)
        
        self.alert_high_gpu = QCheckBox("Alert on High GPU Usage (>90%)")
        self.alert_high_gpu.setStyleSheet("color: #ffffff; font-size: 12px;")
        alert_layout.addWidget(self.alert_high_gpu)
        
        self.alert_high_cpu = QCheckBox("Alert on High CPU Usage (>95%)")
        self.alert_high_cpu.setStyleSheet("color: #ffffff; font-size: 12px;")
        alert_layout.addWidget(self.alert_high_cpu)
        
        self.alert_disk_full = QCheckBox("Alert on Disk Full (>95%)")
        self.alert_disk_full.setStyleSheet("color: #ffffff; font-size: 12px;")
        alert_layout.addWidget(self.alert_disk_full)
        
        remote_layout.addWidget(alert_group)
        remote_layout.addStretch()
        
        self.tab_widget.addTab(remote_widget, "Remote")
        
    def create_settings_tab(self) -> None:
        """Create the Settings tab with configuration options"""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab title
        tab_title = QLabel("SETTINGS - Application Configuration")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff
                font-size: 18px
                font-weight: 700
                margin-bottom: 15px
            }
        """)
        settings_layout.addWidget(tab_title)
        
        # Settings group
        settings_group = QGroupBox("System Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                border-radius: 12px
                padding: 15px
                margin: 0
            }
            QGroupBox::title {
                color: #ffffff
                font-size: 12px
                font-weight: 600
                subcontrol-origin: margin
                subcontrol-position: top left
                padding: 0 5px
            }
        """)
        
        settings_group_layout = QVBoxLayout(settings_group)
        settings_group_layout.setSpacing(15)
        
        # Start with Windows checkbox
        self.startup_checkbox = QCheckBox("Start with Windows")
        self.startup_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff
                font-size: 12px
                font-weight: 500
                spacing: 8px
            }
            QCheckBox::indicator {
                width: 18px
                height: 18px
                border: 1px solid rgba(255, 255, 255, 0.2)
                border-radius: 4px
                background-color: rgba(255, 255, 255, 0.05)
            }
            QCheckBox::indicator:checked {
                background-color: #00f2ff
                border-color: #00f2ff
            }
            QCheckBox::indicator:hover {
                border-color: #00f2ff
            }
        """)
        
        # Load startup state from registry
        self.startup_checkbox.setChecked(self.is_startup_enabled())
        self.startup_checkbox.stateChanged.connect(self.on_startup_checkbox_changed)  # type: ignore
        
        settings_group_layout.addWidget(self.startup_checkbox)
        
        # Heartbeat Regulator
        from PyQt6.QtWidgets import QSlider
        
        heartbeat_group = QGroupBox("Heartbeat Regulator")
        heartbeat_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                border-radius: 0px
                padding: 15px
            }
            QGroupBox::title {
                color: #ffffff
                font-size: 12px
                font-weight: 600
            }
        """)
        
        heartbeat_layout = QVBoxLayout(heartbeat_group)
        
        self.polling_slider = QSlider(Qt.Orientation.Horizontal)
        self.polling_slider.setRange(1, 50)
        self.polling_slider.setValue(20)
        self.polling_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #08080a
                height: 8px
                border: 1px solid #bc13fe
                border-radius: 0px
            }
            QSlider::handle:horizontal {
                background: #bc13fe
                width: 20px
                height: 20px
                margin: -6px 0
                border-radius: 0px
            }
        """)
        
        self.polling_label = QLabel("[SAMP_FREQ: 2000ms]")
        self.polling_label.setStyleSheet("color: #bc13fe; font-family: 'Courier New'; font-size: 10pt; font-weight: bold;")
        
        self.polling_slider.valueChanged.connect(self.on_polling_slider_changed)  # type: ignore
        
        heartbeat_layout.addWidget(self.polling_label)
        heartbeat_layout.addWidget(self.polling_slider)
        settings_group_layout.addWidget(heartbeat_group)
        
        # UI Accent Color Theming
        theme_group = QGroupBox("UI Accent Color")
        theme_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05)
                border: 1px solid rgba(255, 255, 255, 0.1)
                border-radius: 0px
                padding: 15px
            }
            QGroupBox::title {
                color: #ffffff
                font-size: 12px
                font-weight: 600
            }
        """)
        
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_slider = QSlider(Qt.Orientation.Horizontal)
        self.theme_slider.setRange(0, 360)
        self.theme_slider.setValue(280)  # Default purple hue
        self.theme_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:0.17 #ffff00, stop:0.33 #00ff00,
                    stop:0.5 #00ffff, stop:0.67 #0000ff, stop:0.83 #ff00ff, stop:1 #ff0000)
                height: 12px
                border: 1px solid #bc13fe
                border-radius: 0px
            }
            QSlider::handle:horizontal {
                background: #ffffff
                width: 24px
                height: 24px
                margin: -6px 0
                border-radius: 0px
                border: 2px solid #bc13fe
            }
        """)
        
        self.theme_label = QLabel("[ACCENT_HUE: 280°]")
        self.theme_label.setStyleSheet("color: #bc13fe; font-family: 'Courier New'; font-size: 10pt; font-weight: bold;")
        
        self.theme_slider.valueChanged.connect(self.on_theme_slider_changed)  # type: ignore
        
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_slider)
        settings_group_layout.addWidget(theme_group)
        
        settings_layout.addWidget(settings_group)
        settings_layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "Settings")
    
    def is_startup_enabled(self) -> bool:
        """Check if the scheduled task exists"""
        try:
            import subprocess
            # Check if the scheduled task exists
            result = subprocess.run(['schtasks', '/query', '/tn', 'VitreosSentinel'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return result.returncode == 0
        except:
            return False
    
    def on_startup_checkbox_changed(self, state: int) -> None:
        """Handle startup checkbox state change using Scheduled Tasks"""
        import subprocess
        app_path = os.path.abspath(sys.argv[0])
        try:
            if state:
                # Create a Scheduled Task to run on logon with Highest Privileges
                cmd = ['schtasks', '/create', '/tn', 'VitreosSentinel', '/tr', f'"{app_path}"', '/sc', 'onlogon', '/rl', 'highest', '/f']
                subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.update_console("[SYS] Added Vitreos to Scheduled Tasks (Silent Admin Autorun).")
            else:
                cmd = ['schtasks', '/delete', '/tn', 'VitreosSentinel', '/f']
                subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.update_console("[SYS] Removed Vitreos from Scheduled Tasks.")
        except Exception as e:
            self.update_console(f"[WARN] Failed to modify Scheduled Tasks: {e}")
        
    def setup_monitoring(self) -> None:
        """Setup advanced system monitoring with worker thread"""
        # Load configuration - handle type conversion
        webhook_value = self.config.get('webhook_url', '')
        if hasattr(self, 'webhook_input') and self.webhook_input is not None:  # type: ignore[reportUnnecessaryComparison]
            if isinstance(webhook_value, bool):
                self.webhook_input.setText('')
            else:
                self.webhook_input.setText(str(webhook_value))
        
        # Connect logging handler to console output
        log_signal: Any = ui_log_handler.log_signal
        if log_signal is not None:
            log_signal.connect(self.update_console)  # type: ignore[arg-type]
        
        # Apply saved process rules in background
        self.apply_saved_process_rules()
        
        # Create and start hardware monitoring worker thread
        self.monitor_worker = HardwareMonitorWorker()
        self.monitor_thread = QThread()
        
        # Move worker to thread
        self.monitor_worker.moveToThread(self.monitor_thread)
        
        # Connect signals
        self.monitor_worker.stats_updated.connect(self.on_stats_updated)  # type: ignore
        self.monitor_worker.processes_updated.connect(self.on_processes_updated)  # type: ignore
        self.monitor_worker.gpu_advanced_updated.connect(self.on_gpu_advanced_updated)  # type: ignore
        self.monitor_worker.storage_updated.connect(self.on_storage_updated)  # type: ignore
        self.monitor_worker.network_updated.connect(self.on_network_updated)  # type: ignore
        self.monitor_thread.started.connect(self.monitor_worker.setup_gpu)  # type: ignore
        self.monitor_thread.started.connect(self.monitor_worker.run)  # type: ignore
        
        # Start the thread
        self.monitor_thread.start()
        
        self.is_running = True
        
    def on_stats_updated(self, stats_dict: Dict[str, float]) -> None:
        """Receive hardware stats from worker thread and update UI modules"""
        try:
            # Update stats object
            self.stats.cpu_usage = float(stats_dict.get('cpu_usage', 0.0))
            self.stats.ram_usage = float(stats_dict.get('ram_usage', 0.0))
            self.stats.disk_usage = float(stats_dict.get('disk_usage', 0.0))
            self.stats.cpu_temp = float(stats_dict.get('cpu_temp', 45.0))
            self.stats.thermal_prediction = float(stats_dict.get('thermal_prediction', 45.0))
            self.stats.gpu_temp = float(stats_dict.get('gpu_temp', 0.0))
            self.stats.gpu_usage = float(stats_dict.get('gpu_usage', 0.0))
            self.stats.gpu_vram_used = float(stats_dict.get('gpu_vram_used', 0.0))
            self.stats.gpu_vram_total = float(stats_dict.get('gpu_vram_total', 0.0))
            self.stats.gpu_vram_percent = float(stats_dict.get('gpu_vram_percent', 0.0))
            self.stats.gpu_fan_speed = float(stats_dict.get('gpu_fan_speed', 0.0))
            self.stats.gpu_power_draw = float(stats_dict.get('gpu_power_draw', 0.0))
            
            # Route stats to specific modules
            cpu_loads = [self.stats.cpu_usage] * 16
            # Get CPU frequency if available
            try:
                cpu_freq = psutil.cpu_freq()
                cpu_clock = cpu_freq.current if cpu_freq else 0.0
            except:
                cpu_clock = 0.0
            self.cpu_content.update_stats(self.stats.cpu_usage, self.stats.cpu_temp, cpu_loads, cpu_clock)
            self.gpu_content.update_stats(self.stats.gpu_usage, self.stats.gpu_temp, self.stats.gpu_vram_percent)
            self.mem_content.update_stats(self.stats.ram_usage)
            self.disk_content.update_stats(self.stats.disk_usage)
            self.net_content.update_stats(self.stats.network_speed)
            self.thermal_content.update_stats(self.stats.cpu_temp, self.stats.gpu_temp, self.stats.thermal_prediction, self.stats.gpu_fan_speed, self.stats.gpu_fan_speed)
            
            # Database write every 60 seconds
            self.db_write_counter += 1
            if self.db_write_counter >= 30:
                self.database.log_stats(stats_dict=stats_dict)
                self.db_write_counter = 0
                logger.debug("[SYS] Database write completed")
            
            self.predictive_alert.add_reading(self.stats.cpu_temp, self.stats.cpu_usage)
            self.alert_manager.check_and_alert("CPU Temperature", self.stats.cpu_temp, 80.0)
            self.alert_manager.check_and_alert("GPU Usage", self.stats.gpu_usage, 90.0)
            self.alert_manager.check_and_alert("Disk Usage", self.stats.disk_usage, 95.0)
            
            # Update status bar
            self.status_bar.showMessage(f"Last Update: {datetime.now().strftime('%H:%M:%S')} | CPU: {self.stats.cpu_usage:.1f}% | GPU: {self.stats.gpu_usage:.1f}%")
            
        except Exception as e:
            logger.error(f"Error updating stats from worker: {e}")
    
    def update_console(self, message: str) -> None:
        """Update console output with log messages (connected from UILoggingHandler)"""
        try:
            if not hasattr(self, 'console_output'):
                return
            
            console = cast(Any, self.console_output)
            if console is None:
                return
            
            console.appendPlainText(message)
            
            if hasattr(self, 'pulse_log_widget') and self.pulse_log_widget is not None:  # type: ignore[reportUnnecessaryComparison]
                self.pulse_log_widget.add_log(message[:50])
            
            # Auto-scroll to bottom
            scrollbar: Optional[Any] = console.verticalScrollBar()
            if scrollbar is not None:
                scrollbar.setValue(scrollbar.maximum())
            
            # Keep only last 200 lines to prevent memory bloat
            doc: Optional[Any] = console.document()
            if doc is not None and doc.blockCount() > 200:
                cursor = console.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                # Delete first 50 lines
                for _ in range(50):
                    cursor.select(cursor.SelectionType.BlockUnderCursor)
                    cursor.removeSelectedText()
        except Exception as e:
            logger.error(f"Error updating console: {e}")
    
    def on_processes_updated(self, processes_list: List[Tuple[int, str, float, float]]) -> None:
        """Handle process data updates from worker thread"""
        try:
            if not hasattr(self, 'processes_table'):
                return
            
            # Disable sorting during update
            self.processes_table.setSortingEnabled(False)
            
            # Clear and repopulate table
            self.processes_table.setRowCount(len(processes_list))
            
            for row, (pid, name, mem_mb, cpu_pct) in enumerate(processes_list):
                # PID column
                pid_item = QTableWidgetItem(str(pid))
                pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.processes_table.setItem(row, 0, pid_item)
                
                # Target name column
                name_item: QTableWidgetItem = QTableWidgetItem(name)
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.processes_table.setItem(row, 1, name_item)
                
                # RAM (MB) column
                ram_item = QTableWidgetItem(f"{mem_mb:.1f}")
                ram_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                ram_item.setData(Qt.ItemDataRole.UserRole, mem_mb)
                self.processes_table.setItem(row, 2, ram_item)
                
                # CPU % column
                cpu_item = QTableWidgetItem(f"{cpu_pct:.1f}")
                cpu_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                cpu_item.setData(Qt.ItemDataRole.UserRole, cpu_pct)
                self.processes_table.setItem(row, 3, cpu_item)
            
            # Re-enable sorting
            self.processes_table.setSortingEnabled(True)
            
        except Exception as e:
            logger.error(f"Error updating processes table: {e}")
    
    def on_gpu_advanced_updated(self, gpu_data: Dict[str, Any]) -> None:
        """Handle advanced GPU data updates from worker thread"""
        try:
            gpu_clock: float = float(gpu_data.get('gpu_clock_mhz', 0.0))
            gpu_power: float = float(gpu_data.get('gpu_power_watts', 0.0))
            gpu_fan: float = float(gpu_data.get('gpu_fan_percent', 0.0))
            gpu_hotspot: float = float(gpu_data.get('gpu_hotspot_temp', 0.0))
            
            # Update GPU module clock display
            if hasattr(self, 'gpu_content'):
                self.gpu_content.clock_label.setText(f"CLOCK: {int(gpu_clock)} MHz")
            
            # Update GPU Pro tab cards
            if hasattr(self, 'gpu_clock_card'):
                status: str = "Boost" if gpu_clock > 1800 else "Normal" if gpu_clock > 1000 else "Idle"
                color: str = "#ff8c00" if gpu_clock > 1800 else "#00f2ff"
                self.gpu_clock_card.update_value(gpu_clock, "MHz", status, color)
            
            if hasattr(self, 'gpu_power_card'):
                status = "High" if gpu_power > 200 else "Normal" if gpu_power > 50 else "Idle"
                color = "#ff8c00" if gpu_power > 200 else "#00f2ff"
                self.gpu_power_card.update_value(gpu_power, "W", status, color)
            
            if hasattr(self, 'gpu_fan_card'):
                status = "Max" if gpu_fan >= 100 else "High" if gpu_fan > 70 else "Normal"
                color = "#ff8c00" if gpu_fan >= 100 else "#00f2ff"
                self.gpu_fan_card.update_value(gpu_fan, "%", status, color)
            
            if hasattr(self, 'gpu_hotspot_card') and gpu_hotspot > 0:
                status = "Critical" if gpu_hotspot > 95 else "Hot" if gpu_hotspot > 85 else "Normal"
                color = "#ff0000" if gpu_hotspot > 95 else "#ff8c00" if gpu_hotspot > 85 else "#00f2ff"
                self.gpu_hotspot_card.update_value(gpu_hotspot, "°C", status, color)
            
        except Exception as e:
            logger.error(f"Error updating GPU advanced data: {e}")
    
    def on_storage_updated(self, storage_data: Dict[str, Any]) -> None:
        """Handle storage data updates from worker thread"""
        try:
            # Update drives table
            if hasattr(self, 'drives_table'):
                drives: Dict[str, Any] = storage_data.get('drives', {})
                self.drives_table.setSortingEnabled(False)
                self.drives_table.setRowCount(len(drives))
                
                for row, (device, info) in enumerate(drives.items()):
                    # Drive name
                    drive_item: QTableWidgetItem = QTableWidgetItem(info['mountpoint'])
                    drive_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    self.drives_table.setItem(row, 0, drive_item)
                    
                    # Total GB
                    total_item: QTableWidgetItem = QTableWidgetItem(str(info['total_gb']))
                    total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.drives_table.setItem(row, 1, total_item)
                    
                    # Used GB
                    used_item: QTableWidgetItem = QTableWidgetItem(str(info['used_gb']))
                    used_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.drives_table.setItem(row, 2, used_item)
                    
                    # Free GB
                    free_item: QTableWidgetItem = QTableWidgetItem(str(info['free_gb']))
                    free_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.drives_table.setItem(row, 3, free_item)
                    
                    # Usage %
                    usage_item: QTableWidgetItem = QTableWidgetItem(f"{info['percent']}%")
                    usage_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    if info['percent'] > 90:
                        usage_item.setForeground(QColor("#ff0000"))
                    elif info['percent'] > 75:
                        usage_item.setForeground(QColor("#ff8c00"))
                    self.drives_table.setItem(row, 4, usage_item)
                
                self.drives_table.setSortingEnabled(True)
            
            # Update I/O cards
            io_counters: Dict[str, Any] = storage_data.get('io_counters', {})
            if io_counters:
                read_gb: float = io_counters.get('read_bytes', 0) / (1024**3)
                write_gb: float = io_counters.get('write_bytes', 0) / (1024**3)
                read_count: int = io_counters.get('read_count', 0)
                write_count: int = io_counters.get('write_count', 0)
                
                if hasattr(self, 'read_bytes_card'):
                    self.read_bytes_card.update_value(read_gb, "GB", "Normal", "#4ade80")
                if hasattr(self, 'write_bytes_card'):
                    self.write_bytes_card.update_value(write_gb, "GB", "Normal", "#ff6b6b")
                if hasattr(self, 'read_count_card'):
                    self.read_count_card.update_value(read_count / 1000, "K", "Normal", "#00d2ff")
                if hasattr(self, 'write_count_card'):
                    self.write_count_card.update_value(write_count / 1000, "K", "Normal", "#ff9800")
            
            # Update I/O rate display
            io_read_mbs: float = storage_data.get('io_read_mbs', 0.0)
            io_write_mbs: float = storage_data.get('io_write_mbs', 0.0)
            if io_read_mbs > 0 or io_write_mbs > 0:
                logger.debug(f"Disk I/O: Read {io_read_mbs:.2f} MB/s, Write {io_write_mbs:.2f} MB/s")
            
        except Exception as e:
            logger.error(f"Error updating storage data: {e}")
    
    def on_network_updated(self, network_data: Dict[str, Any]) -> None:
        """Handle network data updates from worker thread with hogs table auto-sort."""
        try:
            # Update adapter combo box if needed
            if hasattr(self, 'network_adapter_combo'):
                current_adapters = [self.network_adapter_combo.itemText(i) 
                                  for i in range(self.network_adapter_combo.count())]
                all_adapters = list(network_data.get('all_adapters', {}).keys())
                
                # Populate combo box with available adapters
                if all_adapters and current_adapters == ["Detecting adapters..."]:
                    self.network_adapter_combo.clear()
                    for adapter in all_adapters:
                        self.network_adapter_combo.addItem(adapter)
                    # Set to selected adapter
                    selected = network_data.get('adapter', '')
                    if selected:
                        index = self.network_adapter_combo.findText(selected)
                        if index >= 0:
                            self.network_adapter_combo.setCurrentIndex(index)
            
            # Calculate combined speed (RX + TX) in Mbps
            rx_mbs = network_data.get('rx_mbs', 0.0)
            tx_mbs = network_data.get('tx_mbs', 0.0)
            total_speed_mbps = (rx_mbs + tx_mbs) * 8  # Convert MB/s to Mbps
            
            # Update network waveform with current speed
            if hasattr(self, 'network_waveform'):
                self.network_waveform.add_point(total_speed_mbps)
            
            # Update vitals tab network module
            if hasattr(self, 'net_content'):
                self.net_content.update_stats(total_speed_mbps)
            
            # Update Ping/Jitter cards with status logic
            ping = network_data.get('ping', 0.0)
            jitter = network_data.get('jitter', 0.0)
            
            if hasattr(self, 'ping_card'):
                if ping > 150:
                    self.ping_card.update_value(ping, "ms", "LATTICE_CRITICAL", "#ff8c00")
                elif ping > 50:
                    self.ping_card.update_value(ping, "ms", "High", "#ffd700")
                else:
                    self.ping_card.update_value(ping, "ms", "STABLE", "#4ade80")
            
            if hasattr(self, 'jitter_card'):
                if jitter > 20:
                    self.jitter_card.update_value(jitter, "ms", "High", "#ff8c00")
                elif jitter > 10:
                    self.jitter_card.update_value(jitter, "ms", "Moderate", "#ffd700")
                else:
                    self.jitter_card.update_value(jitter, "ms", "STABLE", "#4ade80")
            
            # Update network tab cards
            if hasattr(self, 'download_card'):
                downloaded_mb = network_data.get('downloaded', 0.0)
                if downloaded_mb > 1024:
                    self.download_card.update_value(downloaded_mb / 1024, "GB", "Normal", "#00d2ff")
                else:
                    self.download_card.update_value(downloaded_mb, "MB", "Normal", "#00d2ff")
            
            if hasattr(self, 'uploaded_card'):
                uploaded_mb = network_data.get('uploaded', 0.0)
                if uploaded_mb > 1024:
                    self.uploaded_card.update_value(uploaded_mb / 1024, "GB", "Normal", "#ff6b6b")
                else:
                    self.uploaded_card.update_value(uploaded_mb, "MB", "Normal", "#ff6b6b")
            
            # Update Bandwidth Hogs Table with Auto-Sort and Alpha Hog highlighting
            if hasattr(self, 'hogs_table'):
                hogs_data = network_data.get('network_hogs', [])
                
                # Disable sorting during update to prevent flicker
                self.hogs_table.setSortingEnabled(False)
                
                # Clear and repopulate table
                self.hogs_table.setRowCount(len(hogs_data))
                
                for row, (process_name, conn_count) in enumerate(hogs_data):
                    # Process name column
                    process_item = QTableWidgetItem(process_name)
                    process_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    self.hogs_table.setItem(row, 0, process_item)
                    
                    # Connection count column
                    count_item = QTableWidgetItem(str(conn_count))
                    count_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    count_item.setData(Qt.ItemDataRole.UserRole, conn_count)  # Store numeric value for sorting
                    self.hogs_table.setItem(row, 1, count_item)
                
                # Only sort programmatically on the first load, then let the user click headers
                if self.hogs_table.rowCount() > 0 and not self.hogs_table.isSortingEnabled():
                    self.hogs_table.setSortingEnabled(True)
                    self.hogs_table.sortByColumn(1, Qt.SortOrder.DescendingOrder)
                else:
                    self.hogs_table.setSortingEnabled(True)
                
                # Highlight the Alpha Hog (top row after sorting) in Safety Orange
                if self.hogs_table.rowCount() > 0:
                    for col in range(self.hogs_table.columnCount()):
                        item = self.hogs_table.item(0, col)
                        if item:
                            item.setBackground(QColor("#ff8c00"))  # Safety Orange
                            item.setForeground(QColor("#000000"))  # Black text
            
        except Exception as e:
            logger.error(f"Error updating network UI: {e}")
            
    def get_advanced_temperatures(self) -> None:
        """Get advanced temperature data"""
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps_fn = getattr(psutil, "sensors_temperatures", None)
                temps: Any = temps_fn() if temps_fn is not None else None
                if temps is not None and 'coretemp' in temps:
                    self.stats.cpu_temp = temps['coretemp'][0].current
                elif temps is not None and 'cpu_thermal' in temps:
                    self.stats.cpu_temp = temps['cpu_thermal'][0].current
                else:
                    self.stats.cpu_temp = 45.0
            else:
                self.stats.cpu_temp = 45.0
        except (OSError, AttributeError, IndexError) as e:
            logger.error(f"Temperature reading error: {e}")
            self.stats.cpu_temp = 45.0
            
    def analyze_network(self) -> None:
        """Analyze network performance"""
        try:
            # Ping and jitter
            avg_ping, jitter = self.network_analyzer.measure_ping_jitter()
            self.stats.network_speed = avg_ping
            self.stats.network_jitter = jitter
            
            # Bandwidth analysis
            bandwidth_data = self.network_analyzer.get_bandwidth_summary()
            
            # Update network cards
            self.ping_card.update_value(avg_ping, "ms", "Stable" if avg_ping < 50 else "High", 
                                      "#4ade80" if avg_ping < 50 else "#ffd700")
            self.jitter_card.update_value(jitter, "ms", "Stable" if jitter < 10 else "High",
                                        "#4ade80" if jitter < 10 else "#ffd700")
            
            down = bandwidth_data['downloaded']
            up = bandwidth_data['uploaded']
            
            if down > 1024:
                self.download_card.update_value(down / 1024, "GB", "Normal", "#00d2ff")
            else:
                self.download_card.update_value(down, "MB", "Normal", "#00d2ff")
                
            if up > 1024:
                self.uploaded_card.update_value(up / 1024, "GB", "Normal", "#ff6b6b")
            else:
                self.uploaded_card.update_value(up, "MB", "Normal", "#ff6b6b")
            
            # Update bandwidth hogs table
            self.update_bandwidth_hogs_table(bandwidth_data['hogs'])
            
        except Exception as e:
            print(f"Network analysis error: {e}")
            
    def update_bandwidth_hogs_table(self, hogs: Dict[str, int]) -> None:
        """Update the bandwidth hogs table"""
        self.hogs_table.setRowCount(len(hogs))
        for i, (process, count) in enumerate(hogs.items()):
            self.hogs_table.setItem(i, 0, QTableWidgetItem(process))
            self.hogs_table.setItem(i, 1, QTableWidgetItem(str(count)))
            
    def estimate_power_draw(self) -> None:
        """Estimate system power consumption"""
        try:
            # Simple power estimation based on CPU/GPU usage
            cpu_power: float = self.stats.cpu_usage * 0.1  # Rough estimation
            gpu_power: float = self.stats.gpu_usage * 0.2  # Rough estimation
            base_power: float = 50.0  # Base system power
            
            self.stats.power_draw = base_power + cpu_power + gpu_power
            
        except Exception:
            self.stats.power_draw = 100.0
            
    def update_ui(self) -> None:
        """Update the UI with current statistics"""
        # Update CPU Thread Matrix
        if hasattr(self, 'cpu_thread_matrix'):
            cpu_loads = [self.stats.cpu_usage] * 16
            self.cpu_thread_matrix.update_threads(cpu_loads, self.stats.cpu_temp)
        
        # Update GPU Circular HUD
        if hasattr(self, 'gpu_circular_hud'):
            self.gpu_circular_hud.update_usage(self.stats.gpu_usage)
        
        # Update Network Waveform
        if hasattr(self, 'network_waveform'):
            self.network_waveform.add_point(self.stats.cpu_usage)
        
        # Update GPU cards
        gpu_status: str
        gpu_color: str
        gpu_status, gpu_color = self.get_status_and_color(self.stats.gpu_temp, 65.0, 85.0)
        self.gpu_temp_card.update_value(self.stats.gpu_temp, "°C", gpu_status, gpu_color)
        self.gpu_vram_card.update_value(self.stats.gpu_vram_percent, "%", gpu_status, gpu_color)
        self.gpu_fan_card.update_value(self.stats.gpu_fan_speed, "%", "Normal", "#ffd700")
        
        # Update CPU usage card
        usage_status: str
        usage_color: str
        usage_status, usage_color = self.get_status_and_color(self.stats.cpu_usage, 70.0, 90.0)
        self.cpu_usage_card.update_value(self.stats.cpu_usage, "%", usage_status, usage_color)
        
        # Update RAM card
        ram_status: str
        ram_color: str
        ram_status, ram_color = self.get_status_and_color(self.stats.ram_usage, 80.0, 95.0)
        self.ram_card.update_value(self.stats.ram_usage, "%", ram_status, ram_color)
        
        # Update Disk card
        disk_status: str
        disk_color: str
        disk_status, disk_color = self.get_status_and_color(self.stats.disk_usage, 80.0, 95.0)
        self.disk_card.update_value(self.stats.disk_usage, "%", disk_status, disk_color)
        
        # Update Power card
        power_status: str
        power_color: str
        power_status, power_color = self.get_status_and_color(self.stats.gpu_power_draw, 150.0, 250.0)
        self.power_card.update_value(self.stats.gpu_power_draw, "W", power_status, power_color)
        
        # Update Predictive card (show predicted temperature)
        pred_status: str = "STABLE"
        pred_color: str = "#4ade80"
        if self.stats.thermal_prediction >= 85:
            pred_status = "CRITICAL"
            pred_color = "#ff4444"
        elif self.stats.thermal_prediction >= 75:
            pred_status = "WARNING"
            pred_color = "#ffd700"
        
        self.predictive_card.update_value(self.stats.thermal_prediction, "°C", pred_status, pred_color)
        
        # Update Security events table
        self.update_security_events_table()
        
        # Update status bar
        self.status_bar.showMessage(f"Last Update: {datetime.now().strftime('%H:%M:%S')} | CPU: {self.stats.cpu_usage:.1f}% | GPU: {self.stats.gpu_usage:.1f}%")
        
    def update_security_events_table(self) -> None:
        """Update the security events table"""
        events = self.security_monitor.get_recent_events(20)
        self.events_table.setRowCount(len(events))
        
        for i, event in enumerate(events):
            self.events_table.setItem(i, 0, QTableWidgetItem(event.timestamp))
            self.events_table.setItem(i, 1, QTableWidgetItem(event.event_type))
            self.events_table.setItem(i, 2, QTableWidgetItem(event.description))
            
            # Set severity color
            severity_item = QTableWidgetItem(event.severity)
            if event.severity == "CRITICAL":
                severity_item.setForeground(QColor("#ff4444"))
            elif event.severity == "WARNING":
                severity_item.setForeground(QColor("#ffd700"))
            else:
                severity_item.setForeground(QColor("#4ade80"))
            self.events_table.setItem(i, 3, severity_item)
            
    def get_status_and_color(self, value: float, warning_threshold: float, critical_threshold: float) -> Tuple[str, str]:
        """Get status text and color based on thresholds"""
        if value >= critical_threshold:
            return "CRITICAL", "#ff4444"
        elif value >= warning_threshold:
            return "WARNING", "#ffd700"
        else:
            return "NORMAL", "#4ade80"
            
    def toggle_security_monitoring(self) -> None:
        """Toggle advanced security monitoring"""
        if not self.security_monitoring_active:
            self.security_thread = SecurityMonitorThread()
            self.security_thread.security_event.connect(self.on_security_event)  # type: ignore
            self.security_thread.start()
            self.security_monitoring_active = True
            self.security_toggle.setText("??? Stop Security Monitoring")
            self.update_console("[SEC] Advanced security monitoring started")
        else:
            if self.security_thread:
                self.security_thread.stop()
                self.security_thread.wait()
                self.security_thread = None
            self.security_monitoring_active = False
            self.security_toggle.setText("??? Start Security Monitoring")
            self.update_console("[SEC] Advanced security monitoring stopped")
    
    def on_security_event(self, event_type: str, description: str, severity: str) -> None:
        """Handle security events from SecurityMonitorThread"""
        try:
            if hasattr(self, 'events_table'):
                self.events_table.insertRow(0)
                timestamp: str = datetime.now().strftime("%H:%M:%S")
                self.events_table.setItem(0, 0, QTableWidgetItem(timestamp))
                self.events_table.setItem(0, 1, QTableWidgetItem(event_type))
                self.events_table.setItem(0, 2, QTableWidgetItem(description))
                severity_item: QTableWidgetItem = QTableWidgetItem(severity)
                if severity == "WARNING":
                    severity_item.setForeground(QColor("#ff8c00"))
                elif severity == "CRITICAL":
                    severity_item.setForeground(QColor("#ff0000"))
                self.events_table.setItem(0, 3, severity_item)
                if self.events_table.rowCount() > 100:
                    self.events_table.removeRow(100)
            if event_type == "USB_CONNECTED" and hasattr(self, 'alert_usb_connected') and self.alert_usb_connected.isChecked():
                self.send_webhook_alert(f"🔔 {event_type}", description, severity="WARNING", fields=[{"name": "Event", "value": event_type, "inline": True}])
            elif event_type in ["WEBCAM_ACTIVE", "MICROPHONE_ACTIVE"] and hasattr(self, 'alert_webcam_active') and self.alert_webcam_active.isChecked():
                self.send_webhook_alert(f"🔔 {event_type}", description, severity="CRITICAL", fields=[{"name": "Event", "value": event_type, "inline": True}])
        except Exception as e:
            logger.error(f"Error handling security event: {e}")
    
    def send_webhook_alert(self, title: str, message: str, severity: str = "INFO", fields: list[dict[str, Any]] | None = None) -> None:
        """Send rich embed alert to Discord webhook with severity colors and structured fields"""
        webhook_url = self.webhook_input.text().strip()
        if not webhook_url:
            logger.warning("[WARN] No webhook URL configured")
            return
        
        try:
            # Dynamic color based on severity
            if severity == "CRITICAL":
                color_int = 0xFF0000  # Red
            elif severity == "WARNING":
                color_int = 0xFFA500  # Orange
            elif severity == "SUCCESS":
                color_int = 0x00FF00  # Green
            else:  # INFO - use local UI theme color
                import colorsys
                hue = getattr(self, 'theme_slider', None)
                if hue and hasattr(hue, 'value'):
                    h = hue.value() / 360.0
                    r, g, b = colorsys.hsv_to_rgb(h, 0.8, 1.0)
                    color_int = (int(r * 255) << 16) + (int(g * 255) << 8) + int(b * 255)
                else:
                    color_int = 0xBC13FE  # Default purple
            
            # Build Discord embed with explicit typing
            embed: dict[str, Any] = {
                "title": f"🔔 {title}",
                "description": message,
                "color": color_int,
                "footer": {"text": "Vitreos System Sentinel"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            if fields:
                embed["fields"] = fields
            
            payload: dict[str, Any] = {"embeds": [embed]}
            response = requests.post(webhook_url, json=payload, timeout=5)
            
            if response.status_code == 204:
                logger.info(f"[OK] Webhook embed sent: {title} [{severity}]")
            else:
                logger.warning(f"[WARN] Webhook failed: {response.status_code}")
        except Exception as e:
            logger.error(f"[WARN] Webhook error: {e}")

    def clear_security_events(self) -> None:
        """Clear security events"""
        self.security_monitor.security_events.clear()
        self.update_security_events_table()
        
    def execute_purge_protocol(self) -> None:
        """Execute Purge Protocol with intelligent heuristic scanning and interactive confirmation"""
        try:
            # 1. Scan ALL processes >10MB, filter out protected, flag known bloatware
            targets: List[Tuple[int, str, float, bool]] = []
            my_pid = os.getpid()
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    name = proc.info['name']
                    if not name:
                        continue
                    
                    name_lower = name.lower()
                    pid = proc.info['pid']
                    mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
                    
                    # Skip self and low-memory processes
                    if pid == my_pid or mem_mb < 2.0:
                        continue
                    
                    # Skip critical system processes and protected apps
                    if name_lower in CRITICAL_SYSTEM_PROCESSES or name_lower in PROTECTED_APPS:
                        continue
                    
                    # Flag if known bloatware
                    is_bloat = name_lower in KNOWN_BLOATWARE
                    targets.append((pid, name, mem_mb, is_bloat))
                except:
                    continue
            
            if not targets:
                self.update_console("[SYS] PURGE PROTOCOL: System is clean. No targets found.")
                return
            
            # 2. Sort: known bloatware first, then by memory descending
            targets.sort(key=lambda x: (not x[3], -x[2]))
            
            # 3. Open Confirmation Dialog
            dialog = PurgeConfirmationDialog(targets, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_pids = dialog.get_selected_pids()
                killed_count = 0
                freed_mb = 0.0
                for pid in selected_pids:
                    try:
                        p: psutil.Process = psutil.Process(pid)
                        mem = p.memory_info().rss / (1024 * 1024)
                        p.kill()
                        p.wait(timeout=1)
                        freed_mb += mem
                        killed_count += 1
                    except:
                        pass
                self.update_console(f"[SYS] PURGE COMPLETE: Terminated {killed_count} tasks. Freed {freed_mb:.1f} MB.")
                self.show_status_message(f"⚠ PURGE COMPLETE: {killed_count} tasks terminated, {freed_mb:.1f} MB freed", "#ff8c00")
            
        except Exception as e:
            logger.error(f"[SYS] PURGE FAILED: {e}")
            self.show_status_message(f"❌ PURGE FAILED: {str(e)}", "#ff4444")
    
    def optimize_cpu_priorities(self) -> None:
        """Set games to High Priority and background apps to Below Normal."""
        import psutil
        targets: List[Tuple[int, str, float, float, str, bool]] = []
        my_pid: int = os.getpid()

        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                name: str = proc.info['name'].lower()
                pid: int = proc.info['pid']
                mem: float = proc.info['memory_info'].rss / (1024*1024)
                cpu_pct: float = proc.cpu_percent(interval=0.0)
                
                if pid == my_pid or mem < 10.0 or name in CRITICAL_SYSTEM_PROCESSES:
                    continue

                if name in PERFORMANCE_TARGETS:
                    targets.append((pid, name, mem, cpu_pct, "Boost ⚡ (HIGH Priority)", True))
                elif name in EFFICIENCY_TARGETS:
                    targets.append((pid, name, mem, cpu_pct, "Throttle 🛑 (LOW Priority)", True))
                else:
                    targets.append((pid, name, mem, cpu_pct, "Throttle 🛑 (LOW Priority)", False))
            except:
                continue

        if not targets:
            self.update_console("[SYS] PRIORITY ENGINE: No target apps currently running.")
            return

        dialog: TuningConfirmationDialog = TuningConfirmationDialog("[ REVIEW PRIORITY OPTIMIZATIONS ]", targets, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_pids, save_to_db = dialog.get_results()
            success_count: int = 0
            for pid in selected_pids:
                try:
                    p: psutil.Process = psutil.Process(pid)
                    name: str = p.name().lower()
                    if name in PERFORMANCE_TARGETS:
                        p.nice(psutil.HIGH_PRIORITY_CLASS if hasattr(psutil, 'HIGH_PRIORITY_CLASS') else -10)
                        if save_to_db: self.database.save_process_rule(name, 'PRIORITY', 'HIGH')
                    else:
                        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if hasattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS') else 10)
                        if save_to_db: self.database.save_process_rule(name, 'PRIORITY', 'BELOW_NORMAL')
                    success_count += 1
                except psutil.AccessDenied:
                    self.update_console(f"[WARN] Access Denied: Could not change priority for PID {pid}")
                except:
                    pass
            self.update_console(f"[SYS] PRIORITY ENGINE: Successfully optimized {success_count} processes.")

    def isolate_core_affinity(self) -> None:
        """Force background efficiency apps to the last 2 logical cores."""
        import psutil
        cpu_count: Optional[int] = psutil.cpu_count()
        if cpu_count is None or cpu_count < 4:
            self.update_console("[WARN] CORE ISOLATOR: Requires at least 4 logical cores.")
            return

        restricted_cores: List[int] = [cpu_count - 2, cpu_count - 1]
        targets: List[Tuple[int, str, float, float, str, bool]] = []
        my_pid: int = os.getpid()

        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                name: str = proc.info['name'].lower()
                pid: int = proc.info['pid']
                mem: float = proc.info['memory_info'].rss / (1024*1024)
                cpu_pct: float = proc.cpu_percent(interval=0.0)
                
                if pid == my_pid or mem < 10.0 or name in CRITICAL_SYSTEM_PROCESSES or name in PERFORMANCE_TARGETS:
                    continue

                # Target both efficiency apps AND known bloatware for core isolation
                is_target: bool = name in EFFICIENCY_TARGETS or name in KNOWN_BLOATWARE
                targets.append((pid, name, mem, cpu_pct, f"Isolate 🔒 (Cores {restricted_cores})", is_target))
            except:
                continue

        if not targets:
            self.update_console("[SYS] CORE ISOLATOR: No background targets currently running.")
            return

        dialog: TuningConfirmationDialog = TuningConfirmationDialog(f"[ REVIEW CORE ISOLATION: CORES {restricted_cores} ]", targets, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_pids: List[int] = dialog.get_selected_pids()
            success_count: int = 0
            for pid in selected_pids:
                try:
                    p: psutil.Process = psutil.Process(pid)
                    name: str = p.name().lower()
                    p.cpu_affinity(restricted_cores)
                    if save_to_db: self.database.save_process_rule(name, 'AFFINITY', ','.join(map(str, restricted_cores)))
                    success_count += 1
                except psutil.AccessDenied:
                    self.update_console(f"[WARN] Access Denied: Could not isolate PID {pid}")
                except:
                    pass
            self.update_console(f"[SYS] CORE ISOLATOR: Successfully isolated {success_count} processes to cores {restricted_cores}.")
    



    def test_webhook(self) -> None:
        """Test Discord webhook connection"""
        webhook_url = self.webhook_input.text().strip()
        
        if not webhook_url:
            self.show_status_message("Please enter a Discord webhook URL", "#ff4444")
            return
            
        if "discord.com/api/webhooks/" not in webhook_url:
            self.show_status_message("Please enter a valid Discord webhook URL", "#ff4444")
            return
            
        try:
            # Type-safe webhook embed structure
            test_embed: Dict[str, Any] = {
                "embeds": [{
                    "title": "🧪 Vitreos Architect Test",
                    "description": "Testing advanced sentinel connectivity",
                    "color": 65280,
                    "fields": [
                        {"name": "Status", "value": "✅ Connection Successful", "inline": True},
                        {"name": "Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True},
                        {"name": "Features", "value": "Sentinel, GPU, Network, Intelligence", "inline": True}
                    ],
                    "footer": {"text": "Vitreos System Sentinel"}
                }]
            }
            
            response = requests.post(webhook_url, json=test_embed)
            if response.status_code == 204:
                self.show_status_message("✅ Discord connection test successful!", "#4ade80")
            else:
                self.show_status_message(f"❌ Webhook test failed: {response.status_code}", "#ff4444")
                
        except Exception as e:
            self.show_status_message(f"❌ Connection error: {str(e)}", "#ff4444")
            
    def show_status_message(self, message: str, color: str) -> None:
        """Show temporary status message"""
        self.status_bar.showMessage(message)
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: rgba(255, 255, 255, 0.05)
                color: {color}
                border-top: 1px solid rgba(255, 255, 255, 0.1)
                font-size: 11px
                font-weight: 600
            }}
        """)
    
    def apply_saved_process_rules(self) -> None:
        """Apply saved process tuning rules from database on startup"""
        import psutil
        try:
            rules: Dict[str, Tuple[str, str]] = self.database.get_all_process_rules()
            if not rules:
                logger.info("[SYS] No saved process rules to apply")
                return
            
            applied_count: int = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name: str = proc.info['name'].lower()
                    if name in rules:
                        rule_type, rule_value = rules[name]
                        p: psutil.Process = psutil.Process(proc.info['pid'])
                        
                        if rule_type == 'PRIORITY':
                            if rule_value == 'HIGH':
                                p.nice(psutil.HIGH_PRIORITY_CLASS if hasattr(psutil, 'HIGH_PRIORITY_CLASS') else -10)
                            elif rule_value == 'BELOW_NORMAL':
                                p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if hasattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS') else 10)
                            applied_count += 1
                            logger.debug(f"Applied PRIORITY rule to {name}: {rule_value}")
                        
                        elif rule_type == 'AFFINITY':
                            cores: List[int] = [int(c) for c in rule_value.split(',')]
                            p.cpu_affinity(cores)
                            applied_count += 1
                            logger.debug(f"Applied AFFINITY rule to {name}: cores {cores}")
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except Exception as e:
                    logger.debug(f"Error applying rule: {e}")
                    continue
            
            if applied_count > 0:
                logger.info(f"[SYS] Applied {applied_count} saved process rules on startup")
                self.update_console(f"[OK] Applied {applied_count} saved tuning rules")
        
        except Exception as e:
            logger.error(f"Failed to apply saved process rules: {e}")
    
    def setup_logbook_tailing(self) -> None:
        """Setup real-time logbook file tailing"""
        self.logbook_timer: QTimer = QTimer(self)
        self.logbook_timer.timeout.connect(self.update_logbook)  # type: ignore
        self.logbook_timer.start(2000)  # Update every 2 seconds
        self.logbook_last_position: int = 0
        logger.info("Logbook tailing initialized")
    
    def update_logbook(self) -> None:
        """Tail the log file and update logbook widget"""
        try:
            log_file_path: str = "vitreos_system.log"
            if not os.path.exists(log_file_path):
                return
            
            with open(log_file_path, 'r', encoding='utf-8') as f:
                f.seek(self.logbook_last_position)
                new_lines: str = f.read()
                if new_lines:
                    if hasattr(self, 'logbook_list_widget'):
                        self.logbook_list_widget.append(new_lines)
                        # Auto-scroll to bottom
                        scrollbar = self.logbook_list_widget.verticalScrollBar()
                        if scrollbar:
                            scrollbar.setValue(scrollbar.maximum())
                self.logbook_last_position = f.tell()
        except Exception as e:
            logger.debug(f"Logbook tailing error: {e}")
        
        # Reset after 3 seconds
        QTimer.singleShot(3000, self.reset_status_style)  # type: ignore[arg-type]
        
    def reset_status_style(self) -> None:
        """Reset status bar style"""
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: rgba(255, 255, 255, 0.05)
                color: #888888
                border-top: 1px solid rgba(255, 255, 255, 0.1)
                font-size: 11px
            }
        """)
        

    def on_polling_slider_changed(self, value: int) -> None:
        """Handle polling slider changes and update UI label"""
        interval_ms = value * 100
        interval_sec = value * 0.1
        
        # Update label
        if hasattr(self, 'polling_label') and self.polling_label is not None:
            self.polling_label.setText(f"[SAMP_FREQ: {interval_ms}ms]")
        
        # Update worker thread
        if self.monitor_worker:
            self.monitor_worker.user_polling_interval = interval_sec
            if not self.monitor_worker.combat_mode_active:
                self.monitor_worker.polling_interval = interval_sec
                logger.info(f"[SYS] Polling interval updated to {interval_ms}ms")
        
        # Update Label UI
        color = "#ff8c00" if interval_ms < 300 else "#bc13fe"
        self.polling_label.setText(f"[SAMP_FREQ: {interval_ms}ms]")
        self.polling_label.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 10pt; font-weight: bold;")
    
    def toggle_breach_flicker(self) -> None:
        """Toggle security breach border flicker"""
        self.breach_flicker_state = not self.breach_flicker_state
        if self.breach_flicker_state:
            self.setStyleSheet("""
                QMainWindow {
                    background: #08080a
                    border: 3px solid #ff8c00
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background: #08080a
                }
            """)
    
    def generate_stability_report(self) -> None:
        """Generate CCE stability report to desktop"""
        try:
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            report_path = os.path.join(desktop, 'CCE_Stability_Report.txt')
            
            with open(report_path, 'w') as f:
                f.write("=" * 60 + "\n")
                f.write("VITREOS SYSTEM SENTINEL - STABILITY REPORT\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("SYSTEM VITALS SUMMARY\n")
                f.write("-" * 60 + "\n")
                f.write(f"CPU Temperature: {self.stats.cpu_temp:.1f}°C\n")
                f.write(f"GPU Temperature: {self.stats.gpu_temp:.1f}°C\n")
                f.write(f"CPU Usage: {self.stats.cpu_usage:.1f}%\n")
                f.write(f"GPU Usage: {self.stats.gpu_usage:.1f}%\n")
                f.write(f"RAM Usage: {self.stats.ram_usage:.1f}%\n")
                f.write(f"Disk Usage: {self.stats.disk_usage:.1f}%\n\n")
                
                f.write("SYSTEM PULSE LOG\n")
                f.write("-" * 60 + "\n")
                if hasattr(self, 'pulse_log_widget'):
                    for msg in self.pulse_log_widget.log_messages:
                        f.write(msg + "\n")
                
                f.write("\n\nSECURITY EVENTS\n")
                f.write("-" * 60 + "\n")
                events = self.security_monitor.get_recent_events(50)
                for event in events:
                    f.write(f"[{event.timestamp}] {event.event_type}: {event.description}\n")
                
                f.write("\n\nHARDWARE ANOMALIES\n")
                f.write("-" * 60 + "\n")
                if self.stats.cpu_temp > 85:
                    f.write(f"⚠ CPU Temperature Critical: {self.stats.cpu_temp:.1f}°C\n")
                if self.stats.gpu_temp > 85:
                    f.write(f"⚠ GPU Temperature Critical: {self.stats.gpu_temp:.1f}°C\n")
                if self.security_breach:
                    f.write("⚠ SECURITY BREACH DETECTED\n")
                
                f.write("\n" + "=" * 60 + "\n")
                f.write("END OF REPORT\n")
                f.write("=" * 60 + "\n")
            
            self.show_status_message(f"✅ Report saved to Desktop", "#4ade80")
            logger.info(f"[SYS] Stability report generated: {report_path}")
            
        except Exception as e:
            self.show_status_message(f"❌ Report error: {str(e)}", "#ff4444")
            logger.error(f"Error generating report: {e}")
    
    def load_config(self) -> ConfigDict:
        """Load configuration from file"""
        config_file = 'mercury_config.json'
        default_config: ConfigDict = {
            'webhook_url': '',
            'temp_monitoring': True,
            'usage_monitoring': True,
            'network_monitoring': True
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    loaded_config: Any = json.load(f)
                    return cast(ConfigDict, loaded_config)
        except:
            pass
            
        return default_config
    
    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            # Update webhook URL from input
            if hasattr(self, 'webhook_input') and self.webhook_input is not None:  # type: ignore[reportUnnecessaryComparison]
                self.config['webhook_url'] = self.webhook_input.text().strip()
            
            with open('mercury_config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
        
    def changeEvent(self, a0: Optional[QEvent]) -> None:
        """Handle window state changes for minimizing to tray"""
        if a0 is not None and a0.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            # When the window is minimized, hide it and show the tray icon
            if self.tray_icon and self.tray_icon.isVisible():
                self.hide()
                a0.accept()
                return

        super().changeEvent(a0)
    
    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:
        """Handle window close event - minimize to tray instead of exiting"""
        # Check if this is a real close or minimize to tray
        if self.tray_icon is not None and self.tray_icon.isVisible():
            # Minimize to tray instead of closing
            logger.debug("Close button clicked - hiding to tray")
            self.hide()
            if a0 is not None:
                a0.ignore()
        else:
            # Exit application
            logger.info("Closing application (no tray available)")
            self.is_running = False
            self.security_monitor.monitoring_active = False
            
            # Remove UI logging handler to prevent RuntimeError on shutdown
            try:
                logging.getLogger().removeHandler(ui_log_handler)
            except ValueError:
                pass  # Handler already removed
            
            # Hide tray icon immediately
            if self.tray_icon:
                self.tray_icon.hide()
            
            # Stop the hardware monitor worker thread
            if self.monitor_worker:
                self.monitor_worker.stop()
            if self.monitor_thread is not None and self.monitor_thread.isRunning():
                self.monitor_thread.quit()
                self.monitor_thread.wait()
            
            self.save_config()
            if a0 is not None:
                a0.accept()
    
    def mousePressEvent(self, a0: Optional[QMouseEvent]) -> None:
        if a0 is None:
            return
        """Handle mouse press - check if in header area for dragging"""
        if a0 is not None and self.header_widget is not None:
            # Get header height and check if click is within header area
            header_height: int = self.header_widget.height()
            # Use local coordinates for accurate detection
            click_y: float = a0.position().y()
            
            if click_y <= header_height:
                self.is_dragging = True
                # Store the offset between click position and window position
                self.drag_position = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()
                a0.accept()
                return
        
        super().mousePressEvent(a0)
    
    def mouseMoveEvent(self, a0: Optional[QMouseEvent]) -> None:
        if a0 is None:
            return
        """Handle mouse move - drag window if in drag mode"""
        if a0 is not None and self.is_dragging and self.drag_position is not None:
            # Move window so that the click point stays under the cursor
            self.move(a0.globalPosition().toPoint() - self.drag_position)
            a0.accept()
        else:
            super().mouseMoveEvent(a0)
    
    def mouseReleaseEvent(self, a0: Optional[QMouseEvent]) -> None:
        if a0 is None:
            return
        """Handle mouse release - stop dragging"""
        if a0 is not None and self.is_dragging:
            self.is_dragging = False
            a0.accept()
        else:
            super().mouseReleaseEvent(a0)


    def on_theme_slider_changed(self, value: int) -> None:
        """Handle theme color slider adjustments."""
        self.update_theme_color(value)

    def update_theme_color(self, hue: int) -> None:
        """Update the application accent color dynamically across all UI elements."""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 1.0, 1.0)
        hex_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        try:
            # Update slider labels
            self.theme_label.setStyleSheet(f"color: {hex_color}; font-family: 'Courier New'; font-size: 10pt; font-weight: bold;")
            self.polling_label.setStyleSheet(f"color: {hex_color}; font-family: 'Courier New'; font-size: 10pt; font-weight: bold;")
            
            # Update module borders
            for module in [self.cpu_window, self.gpu_window, self.mem_window, 
                          self.net_window, self.thermal_window, self.disk_window]:
                if module:
                    module.setStyleSheet(f"""
                        VitreosModule {{
                            background-color: #121214
                            border: 1px solid {hex_color}
                            border-radius: 0px
                        }}
                        VitreosModule:hover {{
                            border: 1px solid {hex_color}
                        }}
                    """)
            
            # Update tab widget active tab color
            if hasattr(self, 'tab_widget'):
                self.tab_widget.setStyleSheet(f"""
                    QTabWidget::pane {{
                        border: 1px solid {hex_color}
                        background-color: #08080a
                    }}
                    QTabBar::tab {{
                        background-color: #1a1a1e
                        color: #888888
                        border: 1px solid #2a2a2e
                        padding: 8px 16px
                        margin-right: 2px
                        font-family: 'Courier New', 'Consolas', monospace
                        font-size: 9pt
                    }}
                    QTabBar::tab:selected {{
                        background-color: {hex_color}
                        color: #ffffff
                        font-weight: bold
                    }}
                    QTabBar::tab:hover {{
                        background-color: #2a2a2e
                        color: #00f2ff
                    }}
                """)
            
            logger.debug(f"[SYS] Theme color updated to {hex_color}")
        except AttributeError as e:
            logger.debug(f"[SYS] Theme update partial: {e}")

    def _trigger_shield_alert(self, title: str, message: str, severity: str, fields: list[dict[str, Any]]) -> None:
        """Callback for shield alerts to trigger Discord webhook."""
        self.send_webhook_alert(title, message, severity, fields)


    def on_tweak_ultimate_performance(self) -> None:
        """Execute Ultimate Performance power plan unlock"""
        self.log_to_console("[TWEAK] Unlocking Ultimate Performance power plan...")
        success, message = SystemTweaker.enable_ultimate_performance()
        status = "SUCCESS" if success else "FAILED"
        self.log_to_console(f"[TWEAK] [{status}] {message}")
    
    def on_tweak_disable_gamedvr(self) -> None:
        """Execute Game DVR disable"""
        self.log_to_console("[TWEAK] Disabling Game DVR and Xbox Game Bar...")
        success, message = SystemTweaker.disable_game_dvr()
        status = "SUCCESS" if success else "FAILED"
        self.log_to_console(f"[TWEAK] [{status}] {message}")
    
    def on_tweak_disable_telemetry(self) -> None:
        """Execute telemetry disable"""
        self.log_to_console("[TWEAK] Disabling Windows telemetry...")
        success, message = SystemTweaker.disable_telemetry()
        status = "SUCCESS" if success else "FAILED"
        self.log_to_console(f"[TWEAK] [{status}] {message}")
    
    def on_tweak_flush_cache(self) -> None:
        """Execute DNS flush and cache clear"""
        self.log_to_console("[TWEAK] Flushing DNS and clearing temp caches...")
        success, message = SystemTweaker.flush_dns_and_cache()
        status = "SUCCESS" if success else "FAILED"
        self.log_to_console(f"[TWEAK] [{status}] {message}")
    
    def on_tweak_system_repair(self) -> None:
        """Execute SFC & DISM repair (async)"""
        self.log_to_console("[TWEAK] Starting SFC & DISM system repair (this will take several minutes)...")
        
        # Create worker thread for long-running operation
        from PyQt6.QtCore import QThread
        
        class RepairWorker(QThread):
            def __init__(self, parent_app: "VitreosArchitect") -> None:
                super().__init__()
                self.parent_app = parent_app
            
            def run(self) -> None:
                success, message = SystemTweaker.run_system_repair()
                status = "SUCCESS" if success else "FAILED"
                self.parent_app.log_to_console(f"[TWEAK] [{status}] System Repair Complete")
                self.parent_app.log_to_console(f"[TWEAK] Details: {message}")
        
        self.repair_worker = RepairWorker(self)
        self.repair_worker.start()
    

    def on_gpu_fan_slider_changed(self, value: int) -> None:
        """Handle fan slider value change"""
        if hasattr(self, 'gpu_fan_value_label'):
            self.gpu_fan_value_label.setText(f"{value}%")
        
        # Apply fan speed if slider is moved manually
        if value > 0:
            self.set_gpu_fan_speed(value)
    
    def on_gpu_fan_reset(self) -> None:
        """Reset GPU fan to automatic control"""
        self.log_to_console("[GPU] Resetting fan control to automatic mode...")
        
        if not NVML_AVAILABLE:
            self.log_to_console("[GPU] [FAILED] NVML not available")
            return
        
        try:
            import pynvml
            pynvml.nvmlInit()  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType]
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType, reportCallIssue]
            
            # Reset to default (auto) fan control
            pynvml.nvmlDeviceSetDefaultFanSpeed_v2(handle)  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType, reportCallIssue]
            
            self.log_to_console("[GPU] [SUCCESS] Fan control reset to automatic")
            
            # Reset slider to 0
            if hasattr(self, 'gpu_fan_slider'):
                self.gpu_fan_slider.setValue(0)
            
            pynvml.nvmlShutdown()  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType]
            
        except Exception as e:
            self.log_to_console(f"[GPU] [WARNING] Fan reset failed: {str(e)}")
            self.log_to_console("[GPU] Your GPU/driver may not support fan control")
    
    def set_gpu_fan_speed(self, speed_pct: int) -> None:
        """
        Set GPU fan speed override using pynvml
        Args:
            speed_pct: Fan speed percentage (0-100)
        """
        if not NVML_AVAILABLE:
            self.log_to_console("[GPU] [FAILED] NVML not available for fan control")
            return
        
        try:
            import pynvml
            pynvml.nvmlInit()  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType]
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType, reportCallIssue]
            
            # Set fan speed (some GPUs require fan index, default to 0)
            try:
                # Try newer API first
                pynvml.nvmlDeviceSetFanSpeed_v2(handle, 0, speed_pct)  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType, reportCallIssue]
            except AttributeError:
                # Fallback to older API
                pynvml.nvmlDeviceSetFanControlPolicy(handle, 0, 1)  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType, reportCallIssue]  # Manual mode
                pynvml.nvmlDeviceSetFanSpeed(handle, speed_pct)  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType, reportCallIssue]
            
            self.log_to_console(f"[GPU] [SUCCESS] Fan speed set to {speed_pct}%")
            pynvml.nvmlShutdown()  # type: ignore[reportMissingTypeStubs, reportUnknownMemberType]
            
        except Exception as e:
            # Many laptop GPUs and locked drivers don't support fan control
            self.log_to_console(f"[GPU] [WARNING] Fan control not supported: {str(e)}")
            self.log_to_console("[GPU] This is normal for laptop GPUs or locked drivers")
    

    def on_purge_shader_cache(self) -> None:
        """Purge DirectX shader caches (async)"""
        self.log_to_console("[STORAGE] Starting DirectX shader cache purge...")
        
        from PyQt6.QtCore import QThread
        import shutil
        import os
        
        class ShaderPurgeWorker(QThread):
            def __init__(self, parent_app: "VitreosArchitect") -> None:
                super().__init__()
                self.parent_app = parent_app
            
            def run(self) -> None:
                total_freed_mb = 0
                
                # Target directories
                localappdata = os.environ.get("LOCALAPPDATA", "")
                targets = [
                    os.path.join(localappdata, "D3DSCache"),
                    os.path.join(localappdata, "NVIDIA Corporation", "NV_Cache"),
                    os.path.join(localappdata, "AMD", "DxCache"),
                ]
                
                for target in targets:
                    if os.path.exists(target):
                        try:
                            # Calculate size before deletion
                            size_mb = sum(
                                os.path.getsize(os.path.join(dirpath, filename))
                                for dirpath, _, filenames in os.walk(target)
                                for filename in filenames
                            ) / (1024 * 1024)
                            
                            # Purge
                            shutil.rmtree(target, ignore_errors=True)
                            total_freed_mb += size_mb
                            
                            self.parent_app.log_to_console(f"[STORAGE] Purged: {target} ({size_mb:.2f} MB)")
                        except Exception as e:
                            self.parent_app.log_to_console(f"[STORAGE] [WARNING] Failed to purge {target}: {str(e)}")
                
                self.parent_app.log_to_console(f"[STORAGE] [SUCCESS] Shader cache purge complete. Freed: {total_freed_mb:.2f} MB")
        
        self.shader_purge_worker = ShaderPurgeWorker(self)
        self.shader_purge_worker.start()
    
    def on_purge_temp_files(self) -> None:
        """Purge Windows Temp and AppData temp files (async)"""
        self.log_to_console("[STORAGE] Starting Windows Temp & AppData purge...")
        
        from PyQt6.QtCore import QThread
        import shutil
        import os
        
        class TempPurgeWorker(QThread):
            def __init__(self, parent_app: "VitreosArchitect") -> None:
                super().__init__()
                self.parent_app = parent_app
            
            def run(self) -> None:
                total_freed_mb = 0
                
                # Target directories
                temp = os.environ.get("TEMP", "")
                win_temp = os.path.join("C:", os.sep, "Windows", "Temp")
                targets = [temp, win_temp]
                
                for target in targets:
                    if os.path.exists(target):
                        try:
                            # Calculate size before deletion
                            size_mb = 0
                            for dirpath, _, filenames in os.walk(target):
                                for filename in filenames:
                                    try:
                                        filepath = os.path.join(dirpath, filename)
                                        size_mb += os.path.getsize(filepath) / (1024 * 1024)
                                        os.remove(filepath)
                                    except Exception:
                                        pass  # Skip locked files
                            
                            total_freed_mb += size_mb
                            self.parent_app.log_to_console(f"[STORAGE] Purged: {target} ({size_mb:.2f} MB)")
                        except Exception as e:
                            self.parent_app.log_to_console(f"[STORAGE] [WARNING] Failed to purge {target}: {str(e)}")
                
                self.parent_app.log_to_console(f"[STORAGE] [SUCCESS] Temp file purge complete. Freed: {total_freed_mb:.2f} MB")
        
        self.temp_purge_worker = TempPurgeWorker(self)
        self.temp_purge_worker.start()
    

    def log_to_console(self, message: str) -> None:
        """Log message to console output terminal"""
        if hasattr(self, 'console_output'):
            self.console_output.appendPlainText(message)
        logger.info(message)
def main() -> None:
    """Main application entry point"""
    logger.info("Starting Vitreos Architect")
    app: QApplication = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window: VitreosArchitect = VitreosArchitect()
    window.show()
    logger.info("Application window displayed - ready for user interaction")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    # Set application user model ID for Windows taskbar integration
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("cce.vitreos.sentinel.1.0")
    except Exception as e:
        logger.warning(f"Could not set app user model ID: {e}")
    
    logger.info("=" * 60)
    logger.info("Vitreos - High-End System Sentinel")
    logger.info("=" * 60)
    main()
