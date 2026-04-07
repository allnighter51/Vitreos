#!/usr/bin/env python3
"""
Vitreos - High-End System Sentinel
'Intelligence through Transparency.'
Advanced Desktop Interface with Liquid Glass Aesthetics
"""

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
import ctypes.wintypes
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from collections import deque
import statistics

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                QLabel, QPushButton, QFrame, QGridLayout, QScrollArea,
                                QTextEdit, QLineEdit, QComboBox, QCheckBox, QGroupBox,
                                QProgressBar, QSystemTrayIcon, QMenu, QMenuBar, QToolBar,
                                QStatusBar, QMessageBox, QFileDialog, QDialog, QTabWidget,
                                QTableWidget, QTableWidgetItem, QHeaderView)
    from PyQt6.QtCore import Qt, QTimer, QSize, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal
    from PyQt6.QtGui import (QIcon, QPixmap, QPalette, QColor, QFont, QFontMetrics, 
                           QLinearGradient, QBrush, QPainter, QPen, QRegion, QCursor)
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False

# Try to import advanced GPU monitoring
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

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

class LiquidGlassCard(QFrame):
    """Professional liquid glass card with physics-based styling"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.setMinimumSize(200, 150)
        
        # Glass styling properties
        self.glass_color = QColor(255, 255, 255, 12)  # rgba(255, 255, 255, 0.05) * 255
        self.border_color = QColor(255, 255, 255, 25)  # rgba(255, 255, 255, 0.1) * 255
        self.bevel_color = QColor(255, 255, 255, 25)   # Top-left inner shadow
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the card layout and styling"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Title label with professional styling
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)
        
        # Value display
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet("""
            QLabel {
                color: #00f2ff;
                font-size: 32px;
                font-weight: 700;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        # Unit label
        self.unit_label = QLabel("")
        self.unit_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                font-weight: 400;
            }
        """)
        
        # Status indicator
        self.status_label = QLabel("Normal")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #4ade80;
                font-size: 11px;
                font-weight: 500;
            }
        """)
        
        # Add widgets to layout
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.unit_label)
        layout.addWidget(self.status_label)
        
        # Set frame properties for glass effect
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setAutoFillBackground(False)
        
    def paintEvent(self, event):
        """Custom paint event for liquid glass effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create glass gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, 20))    # Top: very light
        gradient.setColorAt(0.5, QColor(255, 255, 255, 8))    # Middle: transparent
        gradient.setColorAt(1, QColor(255, 255, 255, 15))     # Bottom: light
        
        # Draw main glass body
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(self.border_color, 1))
        painter.drawRoundedRect(rect, 16, 16)
        
        # Draw top-left bevel (inner shadow effect)
        bevel_rect = rect.adjusted(2, 2, -2, -2)
        painter.setPen(QPen(self.bevel_color, 1))
        painter.drawRoundedRect(bevel_rect, 16, 16)
        
        # Draw floating shadow effect (blue/purple tint)
        shadow_color = QColor(26, 26, 46, 80)  # #1a1a2e with transparency
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_color))
        shadow_rect = rect.adjusted(0, 0, 0, 4)
        painter.drawRoundedRect(shadow_rect, 16, 16)
        
        super().paintEvent(event)
        
    def update_value(self, value: float, unit: str = "", status: str = "Normal", color: str = "#00f2ff"):
        """Update card with new values"""
        self.value_label.setText(f"{value:.1f}")
        self.unit_label.setText(unit)
        self.status_label.setText(status)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 32px;
                font-weight: 700;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)

class SecurityMonitor:
    """Advanced security monitoring with USB and startup detection"""
    
    def __init__(self):
        self.known_usb_devices = set()
        self.known_startup_entries = set()
        self.security_events = deque(maxlen=100)
        self.monitoring_active = False
        
    def start_monitoring(self):
        """Start security monitoring"""
        self.monitoring_active = True
        self.known_usb_devices = self.get_current_usb_devices()
        self.known_startup_entries = self.get_startup_entries()
        
        # Start monitoring threads
        threading.Thread(target=self.monitor_usb_devices, daemon=True).start()
        threading.Thread(target=self.monitor_startup_changes, daemon=True).start()
        
    def get_current_usb_devices(self):
        """Get current USB devices"""
        try:
            result = subprocess.run(['wmic', 'path', 'Win32_USBControllerDevice', 'get', 'Dependent'], 
                                  capture_output=True, text=True, timeout=5)
            return set(result.stdout.split())
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            print(f"USB device detection error: {e}")
            return set()
            
    def get_startup_entries(self):
        """Get current startup registry entries"""
        entries = set()
        try:
            # Check common startup locations
            startup_keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunServices",
            ]
            
            for key in startup_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_READ) as reg_key:
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(reg_key, i)
                                entries.add(f"{name}:{value}")
                                i += 1
                            except WindowsError:
                                break
                except:
                    pass
                    
        except:
            pass
        return entries
        
    def monitor_usb_devices(self):
        """Monitor USB device changes"""
        while self.monitoring_active:
            try:
                current_devices = self.get_current_usb_devices()
                new_devices = current_devices - self.known_usb_devices
                removed_devices = self.known_usb_devices - current_devices
                
                if new_devices:
                    self.add_security_event("USB_INSERTION", f"New USB device detected: {len(new_devices)} device(s)", "WARNING")
                    
                if removed_devices:
                    self.add_security_event("USB_REMOVAL", f"USB device removed: {len(removed_devices)} device(s)", "INFO")
                    
                self.known_usb_devices = current_devices
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"USB monitoring error: {e}")
                time.sleep(10)
                
    def monitor_startup_changes(self):
        """Monitor startup registry changes"""
        while self.monitoring_active:
            try:
                current_entries = self.get_startup_entries()
                new_entries = current_entries - self.known_startup_entries
                
                if new_entries:
                    for entry in new_entries:
                        self.add_security_event("STARTUP_CHANGE", f"New startup entry: {entry}", "WARNING")
                        
                self.known_startup_entries = current_entries
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Startup monitoring error: {e}")
                time.sleep(60)
                
    def add_security_event(self, event_type: str, description: str, severity: str):
        """Add security event to log"""
        event = SecurityEvent(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event_type=event_type,
            description=description,
            severity=severity
        )
        self.security_events.append(event)
        
    def get_recent_events(self, limit: int = 20):
        """Get recent security events"""
        return list(self.security_events)[-limit:]

class NetworkAnalyzer:
    """Advanced network monitoring with jitter and bandwidth analysis"""
    
    def __init__(self):
        self.ping_history = deque(maxlen=100)
        self.bandwidth_history = deque(maxlen=50)
        self.current_bandwidth_hogs = {}
        
    def measure_ping_jitter(self):
        """Measure network ping and jitter"""
        try:
            # Use Google DNS as ping target
            result = subprocess.run(['ping', '-n', '5', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                times = []
                for line in lines:
                    if 'time=' in line:
                        try:
                            time_ms = float(line.split('time=')[1].split('ms')[0])
                            times.append(time_ms)
                        except (ValueError, IndexError):
                            pass
                
                if len(times) >= 3:
                    avg_ping = statistics.mean(times)
                    jitter = statistics.stdev(times) if len(times) > 1 else 0
                    return avg_ping, jitter
                    
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            print(f"Ping measurement error: {e}")
        return 0, 0
        
    def analyze_bandwidth_hogs(self):
        """Analyze which processes are using the most bandwidth"""
        try:
            # Get network connections and map to processes
            connections = psutil.net_connections(kind='inet')
            process_bandwidth = {}
            
            for conn in connections:
                if conn.pid and conn.status == 'ESTABLISHED':
                    try:
                        process = psutil.Process(conn.pid)
                        name = process.name()
                        if not name:  # Skip empty process names
                            name = f"PID_{conn.pid}"
                        if name in process_bandwidth:
                            process_bandwidth[name] += 1
                        else:
                            process_bandwidth[name] = 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                        pass
                        
            # Sort by connection count (proxy for bandwidth usage)
            sorted_hogs = sorted(process_bandwidth.items(), key=lambda x: x[1], reverse=True)
            self.current_bandwidth_hogs = dict(sorted_hogs[:10])
            
        except (OSError, ValueError) as e:
            print(f"Bandwidth analysis error: {e}")
            
    def get_bandwidth_summary(self):
        """Get bandwidth usage summary"""
        try:
            net_io = psutil.net_io_counters()
            mb_recv = net_io.bytes_recv / (1024 * 1024)
            mb_sent = net_io.bytes_sent / (1024 * 1024)
            
            return {
                'downloaded': mb_recv,
                'uploaded': mb_sent,
                'hogs': self.current_bandwidth_hogs
            }
        except:
            return {'downloaded': 0, 'uploaded': 0, 'hogs': {}}

class PredictiveThermalAlert:
    """Predictive thermal throttling alerts using linear regression"""
    
    def __init__(self):
        self.temp_history = deque(maxlen=60)  # Last 2 minutes at 2-second intervals
        self.load_history = deque(maxlen=60)
        
    def add_reading(self, temp: float, load: float):
        """Add new temperature and load reading"""
        self.temp_history.append(temp)
        self.load_history.append(load)
        
    def predict_throttling_time(self):
        """Predict time until thermal throttling"""
        if len(self.temp_history) < 10:
            return None
            
        # Simple linear regression
        temps = list(self.temp_history)
        loads = list(self.load_history)
        
        n = len(temps)
        sum_x = sum(range(n))
        sum_y = sum(temps)
        sum_xy = sum(i * temp for i, temp in enumerate(temps))
        sum_x2 = sum(i * i for i in range(n))
        
        # Calculate slope and intercept
        try:
            denominator = n * sum_x2 - sum_x * sum_x
            # Avoid division by zero
            if denominator == 0:
                return None
                
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n
            
            # Predict time until 85°C (thermal throttling threshold)
            current_temp = temps[-1]
            if slope > 0:  # Heating up
                time_to_throttle = (85 - current_temp) / slope
                if time_to_throttle > 0:
                    return max(0, time_to_throttle * 2)  # Convert to seconds (2s intervals)
        except (ZeroDivisionError, ValueError) as e:
            print(f"Thermal prediction error: {e}")
            return None
            
        return None

class VitreosArchitect(QMainWindow):
    """Main application window with advanced liquid glass aesthetics"""
    
    def __init__(self):
        super().__init__()
        
        # Check PyQt6 availability
        if not PYQT6_AVAILABLE:
            self.show_error_dialog("PyQt6 is required for the Vitreos interface.\n\nRun 'install_requirements.bat' to install it.")
            sys.exit(1)
            
        # Application state
        self.is_running = False
        self.stats = SystemStats()
        self.config = self.load_config()
        
        # Advanced monitoring systems
        self.security_monitor = SecurityMonitor()
        self.network_analyzer = NetworkAnalyzer()
        self.predictive_alert = PredictiveThermalAlert()
        
        # Setup window
        self.setup_window()
        self.setup_ui()
        self.setup_monitoring()
        
    def show_error_dialog(self, message: str):
        """Show error dialog for missing dependencies"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(message)
        msg.setWindowTitle("Missing Dependencies")
        msg.exec()
        
    def setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("Vitreos • Architect Edition")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # Set window icon
        self.setWindowIcon(QIcon.fromTheme("system-monitor"))
        
        # Remove window frame for true glass effect
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Premium Glass Background - Semi-transparent dark slate
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(15, 15, 25, 200)) # Premium Deep Tint
        self.setPalette(palette)
        
        # Fix invisible background - enable proper background rendering
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        
        # Center window
        self.center_window()
        
    def center_window(self):
        """Center window on screen"""
        screen = QApplication.primaryScreen().geometry()
        window = self.geometry()
        x = int((screen.width() - window.width()) / 2)
        y = int((screen.height() - window.height()) / 2)
        self.move(x, y)
        
    def setup_ui(self):
        """Setup the main user interface with tabs"""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header with title and controls
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)
        
        # Tab widget for different monitoring areas
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px 16px;
                margin: 0 4px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #00f2ff;
                color: #00f2ff;
            }
        """)
        
        # Create tabs
        self.create_vitals_tab()
        self.create_network_tab()
        self.create_security_tab()
        self.create_logbook_tab()
        self.create_console_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: rgba(255, 255, 255, 0.05);
                color: #888888;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                font-size: 11px;
            }
        """)
        self.setStatusBar(self.status_bar)
        
        self.setCentralWidget(main_widget)
        
        # Apply glass stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: transparent;
            }
            QWidget {
                background-color: transparent;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
    def create_header(self):
        """Create the header with title and controls"""
        header_layout = QHBoxLayout()
        
        # Title section
        title_layout = QVBoxLayout()
        title_label = QLabel("💎 VITREOS")
        title_label.setStyleSheet("""
            QLabel {
                color: #00f2ff;
                font-size: 24px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 3px;
            }
        """)
        
        subtitle_label = QLabel("Intelligence through Transparency")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                font-weight: 400;
            }
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        # Controls section
        controls_layout = QHBoxLayout()
        
        # Minimize button
        minimize_btn = QPushButton("—")
        minimize_btn.setFixedSize(30, 30)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.4);
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff4444;
                border-color: #ff6666;
            }
        """)
        close_btn.clicked.connect(self.close)
        
        controls_layout.addWidget(minimize_btn)
        controls_layout.addWidget(close_btn)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addLayout(controls_layout)
        
        return header_layout
        
    def create_vitals_tab(self):
        """Create the Vitals tab with core system monitoring"""
        vitals_widget = QWidget()
        vitals_layout = QVBoxLayout(vitals_widget)
        
        # Tab title
        tab_title = QLabel("VITALS - Real-time System Health")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 15px;
            }
        """)
        vitals_layout.addWidget(tab_title)
        
        # Create monitoring grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        
        # Create advanced monitoring cards
        self.cpu_temp_card = LiquidGlassCard("CPU Temperature")
        self.cpu_temp_card.update_value(0, "°C", "Normal", "#00f2ff")
        
        self.gpu_temp_card = LiquidGlassCard("GPU Temperature") 
        self.gpu_temp_card.update_value(0, "°C", "Normal", "#7c32ff")
        
        self.cpu_usage_card = LiquidGlassCard("CPU Usage")
        self.cpu_usage_card.update_value(0, "%", "Normal", "#00d2ff")
        
        self.gpu_usage_card = LiquidGlassCard("GPU Usage")
        self.gpu_usage_card.update_value(0, "%", "Normal", "#ff6b6b")
        
        self.gpu_vram_card = LiquidGlassCard("VRAM Usage")
        self.gpu_vram_card.update_value(0, "GB", "Normal", "#4ade80")
        
        self.gpu_fan_card = LiquidGlassCard("GPU Fan Speed")
        self.gpu_fan_card.update_value(0, "%", "Normal", "#ffd700")
        
        self.ram_card = LiquidGlassCard("Memory Usage")
        self.ram_card.update_value(0, "%", "Normal", "#4ade80")
        
        self.disk_card = LiquidGlassCard("Disk Usage")
        self.disk_card.update_value(0, "%", "Normal", "#ffd700")
        
        self.power_card = LiquidGlassCard("Power Draw")
        self.power_card.update_value(0, "W", "Normal", "#ff4444")
        
        self.predictive_card = LiquidGlassCard("Thermal Prediction")
        self.predictive_card.update_value(0, "s", "Stable", "#4ade80")
        
        # Add cards to grid
        grid_layout.addWidget(self.cpu_temp_card, 0, 0)
        grid_layout.addWidget(self.gpu_temp_card, 0, 1)
        grid_layout.addWidget(self.cpu_usage_card, 0, 2)
        grid_layout.addWidget(self.gpu_usage_card, 1, 0)
        grid_layout.addWidget(self.gpu_vram_card, 1, 1)
        grid_layout.addWidget(self.gpu_fan_card, 1, 2)
        grid_layout.addWidget(self.ram_card, 2, 0)
        grid_layout.addWidget(self.disk_card, 2, 1)
        grid_layout.addWidget(self.power_card, 2, 2)
        grid_layout.addWidget(self.predictive_card, 3, 0, 1, 3)
        
        vitals_layout.addLayout(grid_layout)
        self.tab_widget.addTab(vitals_widget, "Vitals")
        
    def create_network_tab(self):
        """Create the Network tab with advanced connectivity monitoring"""
        network_widget = QWidget()
        network_layout = QVBoxLayout(network_widget)
        
        # Tab title
        tab_title = QLabel("NETWORK - Connectivity & Traffic Analysis")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 15px;
            }
        """)
        network_layout.addWidget(tab_title)
        
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
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
                margin: 0;
            }
            QGroupBox::title {
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
        """)
        
        hogs_layout = QVBoxLayout(hogs_group)
        self.hogs_table = QTableWidget()
        self.hogs_table.setColumnCount(2)
        self.hogs_table.setHorizontalHeaderLabels(["Process", "Connections"])
        self.hogs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hogs_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-weight: 600;
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
        
    def create_security_tab(self):
        """Create the Security tab with advanced monitoring"""
        security_widget = QWidget()
        security_layout = QVBoxLayout(security_widget)
        
        # Tab title
        tab_title = QLabel("SECURITY - PC Integrity Monitoring")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 15px;
            }
        """)
        security_layout.addWidget(tab_title)
        
        # Security controls
        controls_layout = QHBoxLayout()
        
        self.security_toggle = QPushButton("🛡️ Start Security Monitoring")
        self.security_toggle.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 10px 20px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #4ade80;
            }
        """)
        self.security_toggle.clicked.connect(self.toggle_security_monitoring)
        
        self.clear_events_btn = QPushButton("🧹 Clear Events")
        self.clear_events_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 10px 20px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #ff4444;
            }
        """)
        self.clear_events_btn.clicked.connect(self.clear_security_events)
        
        controls_layout.addWidget(self.security_toggle)
        controls_layout.addWidget(self.clear_events_btn)
        controls_layout.addStretch()
        
        security_layout.addLayout(controls_layout)
        
        # Security events table
        events_group = QGroupBox("Security Events")
        events_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
                margin: 0;
            }
            QGroupBox::title {
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
        """)
        
        events_layout = QVBoxLayout(events_group)
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(4)
        self.events_table.setHorizontalHeaderLabels(["Time", "Type", "Description", "Severity"])
        self.events_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.events_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-weight: 600;
            }
        """)
        events_layout.addWidget(self.events_table)
        
        security_layout.addWidget(events_group)
        self.tab_widget.addTab(security_widget, "Security")
        
    def create_logbook_tab(self):
        """Create the Logbook tab with historical data"""
        logbook_widget = QWidget()
        logbook_layout = QVBoxLayout(logbook_widget)
        
        # Tab title
        tab_title = QLabel("LOGBOOK - Historical Data & Analytics")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 15px;
            }
        """)
        logbook_layout.addWidget(tab_title)
        
        # Logbook content would go here
        # For now, just a placeholder
        placeholder = QLabel("Historical data visualization coming soon...")
        placeholder.setStyleSheet("color: #888888; font-size: 14px;")
        logbook_layout.addWidget(placeholder)
        logbook_layout.addStretch()
        
        self.tab_widget.addTab(logbook_widget, "Logbook")
        
    def create_console_tab(self):
        """Create the Console tab with active control"""
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        
        # Tab title
        tab_title = QLabel("CONSOLE - Active Control & Testing")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 15px;
            }
        """)
        console_layout.addWidget(tab_title)
        
        # Discord webhook configuration group
        webhook_group = QGroupBox("Discord Webhook Configuration")
        webhook_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
                margin: 0;
            }
            QGroupBox::title {
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
        """)
        
        webhook_layout = QVBoxLayout(webhook_group)
        
        # Discord webhook input
        webhook_label = QLabel("Discord Webhook URL")
        webhook_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 500;")
        
        self.webhook_input = QLineEdit()
        self.webhook_input.setPlaceholderText("Enter Discord webhook URL...")
        self.webhook_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #00f2ff;
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        
        webhook_layout.addWidget(webhook_label)
        webhook_layout.addWidget(self.webhook_input)
        
        console_layout.addWidget(webhook_group)
        
        # Console controls grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        # Control buttons
        self.kill_zombie_btn = QPushButton("💀 Kill Zombie Processes")
        self.kill_zombie_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #ff4444;
            }
        """)
        self.kill_zombie_btn.clicked.connect(self.kill_zombie_processes)
        
        self.webhook_test_btn = QPushButton("🧪 Test Webhook")
        self.webhook_test_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #00f2ff;
            }
        """)
        self.webhook_test_btn.clicked.connect(self.test_webhook)
        
        self.screenshot_btn = QPushButton("📸 Take Screenshot")
        self.screenshot_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #4ade80;
            }
        """)
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        
        self.reset_config_btn = QPushButton("🔄 Reset Configuration")
        self.reset_config_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #ff4444;
            }
        """)
        self.reset_config_btn.clicked.connect(self.reset_configuration)
        
        # Add buttons to grid
        grid_layout.addWidget(self.kill_zombie_btn, 0, 0)
        grid_layout.addWidget(self.webhook_test_btn, 0, 1)
        grid_layout.addWidget(self.screenshot_btn, 1, 0)
        grid_layout.addWidget(self.reset_config_btn, 1, 1)
        
        console_layout.addLayout(grid_layout)
        console_layout.addStretch()
        
        self.tab_widget.addTab(console_widget, "Console")
        
    def setup_monitoring(self):
        """Setup advanced system monitoring"""
        # Load configuration
        self.webhook_input.setText(self.config.get('webhook_url', ''))
        
        # Start monitoring timer
        self.monitoring_timer = QTimer()
        self.monitoring_timer.timeout.connect(self.update_monitoring)
        self.monitoring_timer.start(2000)  # Update every 2 seconds
        
        self.is_running = True
        
    def update_monitoring(self):
        """Update all advanced monitoring data"""
        if not self.is_running:
            return
            
        try:
            # Get system statistics
            self.stats.cpu_usage = psutil.cpu_percent(interval=1)
            self.stats.ram_usage = psutil.virtual_memory().percent
            
            # Get disk usage from system drive
            try:
                # For Windows, use C: drive; for others, use root
                import platform
                if platform.system() == 'Windows':
                    drive = os.path.splitdrive(os.path.expanduser('~'))[0] + '\\'
                else:
                    drive = '/'
                self.stats.disk_usage = psutil.disk_usage(drive).percent
            except (OSError, ValueError) as e:
                print(f"Disk usage error: {e}")
                self.stats.disk_usage = 0
            
            # Get temperatures
            self.get_advanced_temperatures()
            
            # Get GPU data (if available)
            if NVML_AVAILABLE:
                self.get_gpu_data()
            else:
                # Fallback values
                self.stats.gpu_temp = self.stats.cpu_temp + 5.0
                self.stats.gpu_usage = self.stats.cpu_usage
                self.stats.gpu_vram_percent = 30.0
                self.stats.gpu_fan_speed = 50.0
                
            # Network analysis
            self.analyze_network()
            
            # Power estimation
            self.estimate_power_draw()
            
            # Predictive thermal analysis
            self.predictive_alert.add_reading(self.stats.cpu_temp, self.stats.cpu_usage)
            
            # Update UI
            self.update_ui()
            
        except Exception as e:
            print(f"Advanced monitoring error: {e}")
            
    def get_advanced_temperatures(self):
        """Get advanced temperature data"""
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if 'coretemp' in temps:
                    self.stats.cpu_temp = temps['coretemp'][0].current
                elif 'cpu_thermal' in temps:
                    self.stats.cpu_temp = temps['cpu_thermal'][0].current
                else:
                    self.stats.cpu_temp = 45.0
            else:
                self.stats.cpu_temp = 45.0
        except (OSError, AttributeError, IndexError) as e:
            print(f"Temperature reading error: {e}")
            self.stats.cpu_temp = 45.0
            
    def get_gpu_data(self):
        """Get advanced GPU data using pynvml"""
        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            # Temperature
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            self.stats.gpu_temp = temp
            
            # Usage
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            self.stats.gpu_usage = utilization.gpu
            
            # VRAM
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            self.stats.gpu_vram_used = memory.used / 1024 / 1024 / 1024  # GB
            self.stats.gpu_vram_total = memory.total / 1024 / 1024 / 1024  # GB
            self.stats.gpu_vram_percent = (memory.used / memory.total) * 100
            
            # Fan speed
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
                self.stats.gpu_fan_speed = fan_speed
            except (AttributeError, TypeError):
                self.stats.gpu_fan_speed = 0
                
        except Exception as e:
            print(f"GPU monitoring error: {e}")
            # Fallback values
            self.stats.gpu_temp = self.stats.cpu_temp + 5.0
            self.stats.gpu_usage = self.stats.cpu_usage
            self.stats.gpu_vram_percent = 30.0
            self.stats.gpu_fan_speed = 50.0
            
    def analyze_network(self):
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
            
    def update_bandwidth_hogs_table(self, hogs: dict):
        """Update the bandwidth hogs table"""
        self.hogs_table.setRowCount(len(hogs))
        for i, (process, count) in enumerate(hogs.items()):
            self.hogs_table.setItem(i, 0, QTableWidgetItem(process))
            self.hogs_table.setItem(i, 1, QTableWidgetItem(str(count)))
            
    def estimate_power_draw(self):
        """Estimate system power consumption"""
        try:
            # Simple power estimation based on CPU/GPU usage
            cpu_power = self.stats.cpu_usage * 0.1  # Rough estimation
            gpu_power = self.stats.gpu_usage * 0.2  # Rough estimation
            base_power = 50  # Base system power
            
            self.stats.power_draw = base_power + cpu_power + gpu_power
            
        except:
            self.stats.power_draw = 100.0
            
    def update_ui(self):
        """Update the UI with current statistics"""
        # Update CPU card
        cpu_status, cpu_color = self.get_status_and_color(self.stats.cpu_temp, 60, 80)
        self.cpu_temp_card.update_value(self.stats.cpu_temp, "°C", cpu_status, cpu_color)
        
        # Update GPU cards
        gpu_status, gpu_color = self.get_status_and_color(self.stats.gpu_temp, 65, 85)
        self.gpu_temp_card.update_value(self.stats.gpu_temp, "°C", gpu_status, gpu_color)
        self.gpu_usage_card.update_value(self.stats.gpu_usage, "%", gpu_status, gpu_color)
        self.gpu_vram_card.update_value(self.stats.gpu_vram_percent, "%", gpu_status, gpu_color)
        self.gpu_fan_card.update_value(self.stats.gpu_fan_speed, "%", "Normal", "#ffd700")
        
        # Update CPU usage card
        usage_status, usage_color = self.get_status_and_color(self.stats.cpu_usage, 70, 90)
        self.cpu_usage_card.update_value(self.stats.cpu_usage, "%", usage_status, usage_color)
        
        # Update RAM card
        ram_status, ram_color = self.get_status_and_color(self.stats.ram_usage, 80, 95)
        self.ram_card.update_value(self.stats.ram_usage, "%", ram_status, ram_color)
        
        # Update Disk card
        disk_status, disk_color = self.get_status_and_color(self.stats.disk_usage, 80, 95)
        self.disk_card.update_value(self.stats.disk_usage, "%", disk_status, disk_color)
        
        # Update Power card
        power_status, power_color = self.get_status_and_color(self.stats.power_draw, 150, 250)
        self.power_card.update_value(self.stats.power_draw, "W", power_status, power_color)
        
        # Update Predictive card
        prediction = self.predictive_alert.predict_throttling_time()
        if prediction and prediction < 300:  # Less than 5 minutes
            self.predictive_card.update_value(prediction, "s", "WARNING", "#ffd700")
        else:
            self.predictive_card.update_value(0, "s", "STABLE", "#4ade80")
        
        # Update Security events table
        self.update_security_events_table()
        
        # Update status bar
        self.status_bar.showMessage(f"Last Update: {datetime.now().strftime('%H:%M:%S')} | CPU: {self.stats.cpu_usage:.1f}% | GPU: {self.stats.gpu_usage:.1f}%")
        
    def update_security_events_table(self):
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
            
    def get_status_and_color(self, value: float, warning_threshold: float, critical_threshold: float):
        """Get status text and color based on thresholds"""
        if value >= critical_threshold:
            return "CRITICAL", "#ff4444"
        elif value >= warning_threshold:
            return "WARNING", "#ffd700"
        else:
            return "NORMAL", "#4ade80"
            
    def toggle_security_monitoring(self):
        """Toggle security monitoring"""
        if self.security_monitor.monitoring_active:
            self.security_monitor.monitoring_active = False
            self.security_toggle.setText("🛡️ Start Security Monitoring")
            self.security_toggle.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    padding: 10px 20px;
                    color: #ffffff;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                    border-color: #4ade80;
                }
            """)
        else:
            self.security_monitor.start_monitoring()
            self.security_toggle.setText("🛑 Stop Security Monitoring")
            self.security_toggle.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    padding: 10px 20px;
                    color: #ffffff;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                    border-color: #ff4444;
                }
            """)
            
    def clear_security_events(self):
        """Clear security events"""
        self.security_monitor.security_events.clear()
        self.update_security_events_table()
        
    def kill_zombie_processes(self):
        """Kill not responding processes"""
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    if proc.info['status'] == psutil.STATUS_ZOMBIE:
                        proc.kill()
                        killed_count += 1
                except:
                    pass
                    
            self.show_status_message(f"Killed {killed_count} zombie processes", "#4ade80")
        except Exception as e:
            self.show_status_message(f"Error killing processes: {str(e)}", "#ff4444")
            
    def take_screenshot(self):
        """Take a screenshot and send to Discord"""
        try:
            # This would need implementation for actual screenshot capture
            # For now, just show a message
            self.show_status_message("Screenshot functionality coming soon", "#ffd700")
        except Exception as e:
            self.show_status_message(f"Screenshot error: {str(e)}", "#ff4444")
            
    def reset_configuration(self):
        """Reset all configuration to defaults"""
        try:
            self.config = {
                'webhook_url': '',
                'temp_monitoring': True,
                'usage_monitoring': True,
                'network_monitoring': True
            }
            with open('mercury_config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
            self.show_status_message("Configuration reset to defaults", "#4ade80")
        except Exception as e:
            self.show_status_message(f"Reset error: {str(e)}", "#ff4444")
            
    def test_webhook(self):
        """Test Discord webhook connection"""
        webhook_url = self.webhook_input.text().strip()
        
        if not webhook_url:
            self.show_status_message("Please enter a Discord webhook URL", "#ff4444")
            return
            
        if "discord.com/api/webhooks/" not in webhook_url:
            self.show_status_message("Please enter a valid Discord webhook URL", "#ff4444")
            return
            
        try:
            test_embed = {
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
            
    def show_status_message(self, message: str, color: str):
        """Show temporary status message"""
        self.status_bar.showMessage(message)
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: rgba(255, 255, 255, 0.05);
                color: {color};
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        
        # Reset after 3 seconds
        QTimer.singleShot(3000, self.reset_status_style)
        
    def reset_status_style(self):
        """Reset status bar style"""
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: rgba(255, 255, 255, 0.05);
                color: #888888;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                font-size: 11px;
            }
        """)
        
    def load_config(self):
        """Load configuration from file"""
        config_file = 'mercury_config.json'
        default_config = {
            'webhook_url': '',
            'temp_monitoring': True,
            'usage_monitoring': True,
            'network_monitoring': True
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
        except:
            pass
            
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Update webhook URL from input
            self.config['webhook_url'] = self.webhook_input.text().strip()
            
            with open('mercury_config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.is_running = False
        self.security_monitor.monitoring_active = False
        self.save_config()
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = VitreosArchitect()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()