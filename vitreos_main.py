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
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from collections import deque
import statistics

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Resource path helper for PyInstaller bundles
def resource_path(relative_path):
    """Get absolute path to resource, works in development and PyInstaller bundles"""
    if hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    # Running as script in development
    return os.path.join(os.path.abspath("."), relative_path)

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                QLabel, QPushButton, QFrame, QGridLayout, QScrollArea,
                                QTextEdit, QLineEdit, QComboBox, QCheckBox, QGroupBox,
                                QProgressBar, QSystemTrayIcon, QMenu, QMenuBar, QToolBar,
                                QStatusBar, QMessageBox, QFileDialog, QDialog, QTabWidget,
                                QTableWidget, QTableWidgetItem, QHeaderView)
    from PyQt6.QtCore import Qt, QTimer, QSize, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal, QThread, QObject
    from PyQt6.QtGui import (QIcon, QPixmap, QPalette, QColor, QFont, QFontMetrics, 
                           QLinearGradient, QBrush, QPainter, QPen, QRegion, QCursor)
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    PYQT6_AVAILABLE = True
    logger.info("PyQt6 imports successful")
except ImportError:
    PYQT6_AVAILABLE = False
    logger.warning("PyQt6 not available - GUI components will not be loaded")

# Try to import advanced GPU monitoring
try:
    import pynvml
    NVML_AVAILABLE = True
    logger.info("GPU monitoring (NVML) imports successful")
except ImportError:
    NVML_AVAILABLE = False
    logger.warning("GPU monitoring (NVML) not available - using fallback mode")

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
        
    def update_value(self, value, unit: str = "", status: str = "Normal", color: str = "#00f2ff"):
        """Update card with new values - handles float or string input"""
        try:
            # Convert value to float safely
            if isinstance(value, str):
                val_float = float(value)
            else:
                val_float = float(value) if value is not None else 0.0
            
            # Format for display
            self.value_label.setText(f"{val_float:.1f}")
        except (ValueError, TypeError):
            self.value_label.setText(str(value) if value is not None else "0")
        
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

class HardwareMonitorWorker(QObject):
    """Worker thread for hardware monitoring - runs in separate thread"""
    
    # Signal emits dict with all hardware stats
    stats_updated = pyqtSignal(dict)
    
    # New signals for extended data types
    processes_updated = pyqtSignal(list)  # List of (pid, name, memory_mb) tuples
    gpu_advanced_updated = pyqtSignal(dict)  # Dict with gpu_clock, gpu_power, gpu_fan_percent
    storage_updated = pyqtSignal(dict)  # Dict with per-drive stats and I/O counters
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.gpu_handle = None
        # Thermal prediction: store last 5 CPU temp readings
        self.cpu_temp_history = deque(maxlen=5)
        
    def setup_gpu(self):
        """Initialize GPU handle once"""
        try:
            if NVML_AVAILABLE:
                pynvml.nvmlInit()
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                logger.info("GPU initialized successfully in worker thread")
        except Exception as e:
            logger.error(f"GPU initialization error in worker: {e}")
            self.gpu_handle = None
    
    def collect_top_processes(self) -> List[Tuple[int, str, float]]:
        """Collect top 10 memory-consuming processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    mem_mb = proc.info['memory_percent']
                    if mem_mb > 0.1:  # Filter out trivial memory usage
                        processes.append((proc.info['pid'], proc.info['name'], mem_mb))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by memory usage and return top 10
            return sorted(processes, key=lambda x: x[2], reverse=True)[:10]
        except Exception as e:
            logger.error(f"Error collecting top processes: {e}")
            return []
    
    def collect_gpu_advanced(self) -> Dict[str, float]:
        """Collect detailed GPU statistics"""
        gpu_data = {
            'gpu_clock_mhz': 0.0,
            'gpu_power_watts': 0.0,
            'gpu_fan_percent': 0.0,
        }
        
        if not (NVML_AVAILABLE and self.gpu_handle is not None):
            return gpu_data
        
        try:
            handle = self.gpu_handle
            
            # GPU Clock Speed
            try:
                clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                gpu_data['gpu_clock_mhz'] = float(clock)
            except Exception:
                gpu_data['gpu_clock_mhz'] = 0.0
            
            # Power Draw
            try:
                power = pynvml.nvmlDeviceGetPowerUsage(handle)
                gpu_data['gpu_power_watts'] = float(power) / 1000.0  # Convert milliwatts to watts
            except Exception:
                gpu_data['gpu_power_watts'] = 0.0
            
            # Fan Speed (if available)
            try:
                fan = pynvml.nvmlDeviceGetFanSpeed(handle)
                gpu_data['gpu_fan_percent'] = float(fan)
            except Exception:
                gpu_data['gpu_fan_percent'] = 0.0
                
        except Exception as e:
            logger.error(f"Error collecting advanced GPU data: {e}")
        
        return gpu_data
    
    def calculate_thermal_prediction(self, current_temp: float) -> float:
        """
        Calculate predicted CPU temperature 30 seconds from now based on trend.
        Uses last 5 readings to calculate trend slope.
        """
        try:
            # Add current reading to history
            self.cpu_temp_history.append(current_temp)
            
            # Need at least 2 readings to calculate trend
            if len(self.cpu_temp_history) < 2:
                return current_temp  # Return current if not enough history
            
            # Calculate simple linear trend: (temp_now - temp_oldest) / time_points
            temps = list(self.cpu_temp_history)
            n = len(temps)
            
            # Calculate trend using least squares regression
            x_values = list(range(n))  # Time points [0, 1, 2, 3, 4]
            
            sum_x = sum(x_values)
            sum_y = sum(temps)
            sum_xy = sum(x * y for x, y in zip(x_values, temps))
            sum_x2 = sum(x * x for x in x_values)
            
            # Slope calculation: (n*sum_xy - sum_x*sum_y) / (n*sum_x2 - sum_x^2)
            denominator = n * sum_x2 - sum_x * sum_x
            if denominator == 0:
                return current_temp  # No trend
            
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            
            # Predict temperature at t=30 seconds (we update every 2 seconds, so 15 time units ahead)
            # Assuming roughly 2-second intervals between readings
            predicted_temp = current_temp + (slope * 15)
            
            # Clamp to reasonable range (shouldn't jump more than 20°C in 30 seconds)
            predicted_temp = max(current_temp - 5, min(predicted_temp, current_temp + 20))
            
            return round(predicted_temp, 1)
            
        except Exception as e:
            logger.error(f"Error calculating thermal prediction: {e}")
            return current_temp
    
    def collect_storage_data(self) -> Dict[str, Any]:
        """Collect storage and disk I/O statistics"""
        storage_data = {
            'drives': {},
            'io_counters': {},
        }
        
        try:
            # Get all mounted disk partitions
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
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
                io = psutil.disk_io_counters()
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
    
    def run(self):
        """Main monitoring loop running in separate thread"""
        self.is_running = True
        logger.info("Hardware monitor worker thread started")
        
        while self.is_running:
            try:
                stats_dict = {}
                
                # CPU and RAM
                stats_dict['cpu_usage'] = float(psutil.cpu_percent(interval=0.5))
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
                    stats_dict['disk_usage'] = 0
                
                # Temperature
                try:
                    if hasattr(psutil, "sensors_temperatures"):
                        temps_fn = getattr(psutil, "sensors_temperatures", None)
                        if temps_fn is not None:
                            temps = temps_fn()
                        else:
                            temps = None
                        if temps and 'coretemp' in temps:
                            stats_dict['cpu_temp'] = float(temps['coretemp'][0].current)
                        elif temps and 'cpu_thermal' in temps:
                            stats_dict['cpu_temp'] = float(temps['cpu_thermal'][0].current)
                        else:
                            stats_dict['cpu_temp'] = 45.0
                    else:
                        stats_dict['cpu_temp'] = 45.0
                except (OSError, AttributeError, IndexError) as e:
                    logger.error(f"Temperature reading error in worker: {e}")
                    stats_dict['cpu_temp'] = 45.0
                
                # Thermal Prediction (based on temperature trend)
                stats_dict['thermal_prediction'] = float(self.calculate_thermal_prediction(stats_dict['cpu_temp']))
                
                # GPU data
                if NVML_AVAILABLE and self.gpu_handle is not None:
                    try:
                        handle = self.gpu_handle
                        
                        # Temperature
                        stats_dict['gpu_temp'] = float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
                        
                        # Usage
                        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        stats_dict['gpu_usage'] = float(utilization.gpu)
                        
                        # VRAM
                        memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        stats_dict['gpu_vram_used'] = float(memory.used) / 1024 / 1024 / 1024
                        stats_dict['gpu_vram_total'] = float(memory.total) / 1024 / 1024 / 1024
                        stats_dict['gpu_vram_percent'] = (float(memory.used) / float(memory.total)) * 100
                        
                        # Fan speed
                        try:
                            fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
                            stats_dict['gpu_fan_speed'] = float(fan_speed)
                        except Exception as e:
                            logger.error(f"GPU fan speed error: {e}")
                            stats_dict['gpu_fan_speed'] = 0.0
                        
                        # Power Draw (milliwatts -> watts)
                        try:
                            power_mw = pynvml.nvmlDeviceGetPowerUsage(handle)
                            stats_dict['gpu_power_draw'] = float(power_mw) / 1000.0  # Convert mW to W
                        except Exception as e:
                            logger.error(f"GPU power draw error: {e}")
                            stats_dict['gpu_power_draw'] = 0.0
                        
                        logger.debug(f"Hardware check - GPU Temp: {stats_dict['gpu_temp']}°C, GPU Usage: {stats_dict['gpu_usage']}%, VRAM: {stats_dict['gpu_vram_percent']:.1f}%, Fan: {stats_dict['gpu_fan_speed']}%")
                    except Exception as e:
                        logger.error(f"GPU monitoring error in worker: {e}")
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
                
                logger.debug(f"Hardware check - CPU: {stats_dict['cpu_usage']:.1f}%, RAM: {stats_dict['ram_usage']:.1f}%, Disk: {stats_dict['disk_usage']:.1f}%, CPU Temp: {stats_dict['cpu_temp']:.1f}°C")
                
                # Emit signal with all stats
                self.stats_updated.emit(stats_dict)
                
                # Emit new extended data signals (every 2 iterations = 4 seconds to reduce overhead)
                if int(time.time() * 10) % 2 == 0:  # Collect extended data less frequently
                    processes = self.collect_top_processes()
                    if processes:
                        self.processes_updated.emit(processes)
                    
                    gpu_advanced = self.collect_gpu_advanced()
                    self.gpu_advanced_updated.emit(gpu_advanced)
                    
                    storage = self.collect_storage_data()
                    self.storage_updated.emit(storage)
                
                # Sleep to match 2-second update interval
                time.sleep(2.0)
                
            except Exception as e:
                logger.error(f"Hardware monitor worker error: {e}")
                time.sleep(2.0)
    
    def stop(self):
        """Stop the monitoring loop"""
        self.is_running = False
        logger.info("Hardware monitor worker thread stopping")

class VitreosArchitect(QMainWindow):
    """Main application window with advanced liquid glass aesthetics"""
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing Vitreos Architect application")
        
        # Check PyQt6 availability
        if not PYQT6_AVAILABLE:
            logger.critical("PyQt6 is not available - application cannot start")
            self.show_error_dialog("PyQt6 is required for the Vitreos interface.\n\nRun 'install_requirements.bat' to install it.")
            sys.exit(1)
            
        # Application state
        self.is_running = False
        self.stats = SystemStats()
        self.config = self.load_config()
        
        # Hardware monitoring worker and thread
        self.monitor_worker = None
        self.monitor_thread = None
        
        # Frameless window dragging state
        self.is_dragging = False
        self.drag_position = None
        self.header_widget = None
        
        # System tray icon
        self.tray_icon = None
        
        # Advanced monitoring systems
        self.security_monitor = SecurityMonitor()
        self.network_analyzer = NetworkAnalyzer()
        self.predictive_alert = PredictiveThermalAlert()
        
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
        
        # Set window icon from resource path
        icon_path = resource_path("logo.ico")
        window_icon = QIcon(icon_path)
        if not window_icon.isNull():
            self.setWindowIcon(window_icon)
        else:
            # Fallback to system theme
            self.setWindowIcon(QIcon.fromTheme("system-monitor"))
        
        # Remove window frame for true glass effect
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Premium Glass Background - Solid dark color for stability
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(26, 26, 46))  # #1a1a2e solid
        self.setPalette(palette)
        
        # Fix invisible background - enable proper background rendering
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        
        # Center window
        self.center_window()
        
    def setup_system_tray(self):
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
            
            show_action = tray_menu.addAction("Show")
            if show_action is not None:
                show_action.triggered.connect(self.show_window)
            
            hide_action = tray_menu.addAction("Hide")
            if hide_action is not None:
                hide_action.triggered.connect(self.hide_window)
            
            tray_menu.addSeparator()
            
            exit_action = tray_menu.addAction("Exit")
            if exit_action is not None:
                exit_action.triggered.connect(self.exit_application)
            
            self.tray_icon.setContextMenu(tray_menu)
            
            # Handle tray icon click (show/hide on single click)
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            
            self.tray_icon.show()
            logger.info("System tray icon initialized")
        except Exception as e:
            logger.error(f"Failed to initialize system tray: {e}")
    
    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        from PyQt6.QtWidgets import QSystemTrayIcon as STI
        if reason == STI.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide_window()
            else:
                self.show_window()
    
    def show_window(self):
        """Show the window from tray"""
        self.showNormal()
        self.activateWindow()
    
    def hide_window(self):
        """Hide the window to tray"""
        self.hide()
    
    def exit_application(self):
        """Exit the application completely"""
        logger.info("Exit action triggered from tray")
        # Stop the hardware monitor worker thread
        if self.monitor_worker is not None:
            self.monitor_worker.stop()
        if self.monitor_thread is not None and self.monitor_thread.isRunning():
            self.monitor_thread.quit()
            self.monitor_thread.wait()
        
        # Hide tray icon
        if self.tray_icon is not None:
            self.tray_icon.hide()
        
        # Save config and exit
        self.is_running = False
        self.security_monitor.monitoring_active = False
        self.save_config()
        
        # Force quit the application
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
        
    def center_window(self):
        """Center window on screen"""
        screen = QApplication.primaryScreen()
        if screen is not None:
            screen_geometry = screen.geometry()
            window = self.geometry()
            x = int((screen_geometry.width() - window.width()) / 2)
            y = int((screen_geometry.height() - window.height()) / 2)
            self.move(x, y)
        
    def setup_ui(self):
        """Setup the main user interface with tabs"""
        # Main widget and layout
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #1a1a2e;")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header with title and controls
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
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
        
        # Create tabs in correct order
        self.create_vitals_tab()          # 1
        self.create_network_tab()         # 2
        self.create_processes_tab()       # 3 - NEW
        self.create_gpu_pro_tab()         # 4 - NEW
        self.create_security_tab()        # 5
        self.create_storage_tab()         # 6 - NEW
        self.create_logbook_tab()         # 7
        self.create_remote_tab()          # 8 - NEW
        self.create_console_tab()         # 9
        self.create_settings_tab()        # 10
        
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
        # Create a widget to serve as the drag handle
        header_widget = QFrame()
        header_widget.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        header_widget.setCursor(Qt.CursorShape.OpenHandCursor)
        self.header_widget = header_widget
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
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
        
        return header_widget
        
    def create_vitals_tab(self):
        """Create the Vitals tab with core system monitoring"""
        vitals_widget = QWidget()
        vitals_layout = QVBoxLayout(vitals_widget)
        vitals_layout.setSpacing(10)
        vitals_layout.setContentsMargins(10, 10, 10, 10)
        
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
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        
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
        header = self.hogs_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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
    
    def create_processes_tab(self):
        """Create the Processes tab showing top memory-consuming processes"""
        processes_widget = QWidget()
        processes_layout = QVBoxLayout(processes_widget)
        
        # Tab title
        tab_title = QLabel("PROCESSES - Memory & Resource Usage")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 15px;
            }
        """)
        processes_layout.addWidget(tab_title)
        
        # Top processes table
        table_group = QGroupBox("Top 10 Memory-Consuming Processes")
        table_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
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
        
        table_layout = QVBoxLayout(table_group)
        self.processes_table = QTableWidget()
        self.processes_table.setColumnCount(3)
        self.processes_table.setHorizontalHeaderLabels(["PID", "Process Name", "Memory %"])
        header = self.processes_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.processes_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-weight: 600;
                padding: 8px;
            }
        """)
        
        table_layout.addWidget(self.processes_table)
        processes_layout.addWidget(table_group)
        processes_layout.addStretch()
        
        self.tab_widget.addTab(processes_widget, "Processes")
    
    def create_gpu_pro_tab(self):
        """Create the GPU Pro tab with detailed NVIDIA statistics"""
        gpu_widget = QWidget()
        gpu_layout = QVBoxLayout(gpu_widget)
        
        # Tab title
        tab_title = QLabel("GPU PRO - Advanced NVIDIA Statistics")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 15px;
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
        
        # Add to grid
        grid_layout.addWidget(self.gpu_clock_card, 0, 0)
        grid_layout.addWidget(self.gpu_power_card, 0, 1)
        grid_layout.addWidget(self.gpu_fan_card, 0, 2)
        grid_layout.addWidget(self.gpu_temp_pro_card, 1, 0)
        grid_layout.addWidget(self.gpu_memory_pro_card, 1, 1)
        
        gpu_layout.addLayout(grid_layout)
        gpu_layout.addStretch()
        
        self.tab_widget.addTab(gpu_widget, "GPU Pro")
    
    def create_storage_tab(self):
        """Create the Storage tab with disk usage and I/O statistics"""
        storage_widget = QWidget()
        storage_layout = QVBoxLayout(storage_widget)
        
        # Tab title
        tab_title = QLabel("STORAGE - Disk Usage & I/O Activity")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 15px;
            }
        """)
        storage_layout.addWidget(tab_title)
        
        # Drives overview table
        drives_group = QGroupBox("Disk Drives")
        drives_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
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
        
        drives_layout = QVBoxLayout(drives_group)
        self.drives_table = QTableWidget()
        self.drives_table.setColumnCount(5)
        self.drives_table.setHorizontalHeaderLabels(["Drive", "Total (GB)", "Used (GB)", "Free (GB)", "Usage %"])
        header = self.drives_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.drives_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-weight: 600;
                padding: 8px;
            }
        """)
        
        drives_layout.addWidget(self.drives_table)
        storage_layout.addWidget(drives_group)
        
        # I/O Statistics
        io_group = QGroupBox("I/O Activity")
        io_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
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
        header = self.events_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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
    
    def create_remote_tab(self):
        """Create the Remote tab for Discord Webhook and alert configuration"""
        remote_widget = QWidget()
        remote_layout = QVBoxLayout(remote_widget)
        
        # Tab title
        tab_title = QLabel("REMOTE - Discord Integration & Alerts")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 15px;
            }
        """)
        remote_layout.addWidget(tab_title)
        
        # Discord webhook configuration group
        webhook_group = QGroupBox("Discord Webhook Configuration")
        webhook_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
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
        webhook_layout.setSpacing(10)
        
        # Webhook URL label
        webhook_label = QLabel("Webhook URL:")
        webhook_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 600;")
        webhook_layout.addWidget(webhook_label)
        
        # Webhook URL input
        self.remote_webhook_url_input = QLineEdit()
        self.remote_webhook_url_input.setPlaceholderText("https://discord.com/api/webhooks/...")
        self.remote_webhook_url_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: #ffffff;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #00f2ff;
            }
        """)
        webhook_layout.addWidget(self.remote_webhook_url_input)
        
        # Save webhook button
        save_webhook_btn = QPushButton("Save Webhook")
        save_webhook_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 242, 255, 0.2);
                border: 1px solid #00f2ff;
                border-radius: 6px;
                color: #00f2ff;
                font-weight: 600;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 242, 255, 0.3);
            }
        """)
        webhook_layout.addWidget(save_webhook_btn)
        
        remote_layout.addWidget(webhook_group)
        
        # Alert configuration group
        alert_group = QGroupBox("Alert Triggers")
        alert_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
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
        
    def create_settings_tab(self):
        """Create the Settings tab with configuration options"""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab title
        tab_title = QLabel("SETTINGS - Application Configuration")
        tab_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 15px;
            }
        """)
        settings_layout.addWidget(tab_title)
        
        # Settings group
        settings_group = QGroupBox("System Settings")
        settings_group.setStyleSheet("""
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
        
        settings_group_layout = QVBoxLayout(settings_group)
        settings_group_layout.setSpacing(15)
        
        # Start with Windows checkbox
        self.startup_checkbox = QCheckBox("Start with Windows")
        self.startup_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-size: 12px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 0.05);
            }
            QCheckBox::indicator:checked {
                background-color: #00f2ff;
                border-color: #00f2ff;
            }
            QCheckBox::indicator:hover {
                border-color: #00f2ff;
            }
        """)
        
        # Load startup state from registry
        self.startup_checkbox.setChecked(self.is_startup_enabled())
        self.startup_checkbox.stateChanged.connect(self.on_startup_checkbox_changed)
        
        settings_group_layout.addWidget(self.startup_checkbox)
        settings_layout.addWidget(settings_group)
        settings_layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "Settings")
    
    def is_startup_enabled(self):
        """Check if app is registered for Windows startup"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r'Software\Microsoft\Windows\CurrentVersion\Run')
            try:
                value, _ = winreg.QueryValueEx(key, "Vitreos")
                return True
            except WindowsError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"Error reading startup registry: {e}")
            return False
    
    def on_startup_checkbox_changed(self, state):
        """Handle startup checkbox state change"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r'Software\Microsoft\Windows\CurrentVersion\Run',
                               0, winreg.KEY_WRITE)
            try:
                if state:  # Checked
                    # Get the path to the current executable
                    app_path = sys.argv[0]
                    if not os.path.isabs(app_path):
                        app_path = os.path.abspath(app_path)
                    winreg.SetValueEx(key, "Vitreos", 0, winreg.REG_SZ, 
                                    f'"{app_path}"')
                    logger.info("Added Vitreos to Windows startup")
                else:  # Unchecked
                    winreg.DeleteValue(key, "Vitreos")
                    logger.info("Removed Vitreos from Windows startup")
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"Error modifying startup registry: {e}")
            self.show_status_message(f"Error updating startup settings: {str(e)}", "#ff4444")
        
    def setup_monitoring(self):
        """Setup advanced system monitoring with worker thread"""
        # Load configuration
        self.webhook_input.setText(self.config.get('webhook_url', ''))
        
        # Create and start hardware monitoring worker thread
        self.monitor_worker = HardwareMonitorWorker()
        self.monitor_thread = QThread()
        
        # Move worker to thread
        self.monitor_worker.moveToThread(self.monitor_thread)
        
        # Connect signals
        self.monitor_worker.stats_updated.connect(self.on_stats_updated)
        self.monitor_worker.processes_updated.connect(self.on_processes_updated)
        self.monitor_worker.gpu_advanced_updated.connect(self.on_gpu_advanced_updated)
        self.monitor_worker.storage_updated.connect(self.on_storage_updated)
        self.monitor_thread.started.connect(self.monitor_worker.setup_gpu)
        self.monitor_thread.started.connect(self.monitor_worker.run)
        
        # Start the thread
        self.monitor_thread.start()
        
        self.is_running = True
        
    def on_stats_updated(self, stats_dict):
        """Receive hardware stats from worker thread and update UI"""
        try:
            # Update stats object
            self.stats.cpu_usage = stats_dict.get('cpu_usage', 0)
            self.stats.ram_usage = stats_dict.get('ram_usage', 0)
            self.stats.disk_usage = stats_dict.get('disk_usage', 0)
            self.stats.cpu_temp = stats_dict.get('cpu_temp', 45.0)
            self.stats.thermal_prediction = stats_dict.get('thermal_prediction', 45.0)
            self.stats.gpu_temp = stats_dict.get('gpu_temp', 0)
            self.stats.gpu_usage = stats_dict.get('gpu_usage', 0)
            self.stats.gpu_vram_used = stats_dict.get('gpu_vram_used', 0)
            self.stats.gpu_vram_total = stats_dict.get('gpu_vram_total', 0)
            self.stats.gpu_vram_percent = stats_dict.get('gpu_vram_percent', 0)
            self.stats.gpu_fan_speed = stats_dict.get('gpu_fan_speed', 0)
            self.stats.gpu_power_draw = stats_dict.get('gpu_power_draw', 0)
            
            # Update UI
            self.update_ui()
            
            # Predictive thermal analysis
            self.predictive_alert.add_reading(self.stats.cpu_temp, self.stats.cpu_usage)
            
        except Exception as e:
            logger.error(f"Error updating stats from worker: {e}")
    
    def on_processes_updated(self, processes_list: List[Tuple[int, str, float]]):
        """Handle process data updates from worker thread"""
        try:
            self.processes_table.setRowCount(0)
            for idx, (pid, name, mem_percent) in enumerate(processes_list):
                self.processes_table.insertRow(idx)
                self.processes_table.setItem(idx, 0, QTableWidgetItem(str(pid)))
                self.processes_table.setItem(idx, 1, QTableWidgetItem(name))
                mem_item = QTableWidgetItem(f"{mem_percent:.2f}%")
                mem_item.setForeground(QColor("#00f2ff"))
                self.processes_table.setItem(idx, 2, mem_item)
        except Exception as e:
            logger.error(f"Error updating processes table: {e}")
    
    def on_gpu_advanced_updated(self, gpu_data: Dict[str, float]):
        """Handle advanced GPU data updates from worker thread"""
        try:
            gpu_clock = gpu_data.get('gpu_clock_mhz', 0.0)
            gpu_power = gpu_data.get('gpu_power_watts', 0.0)
            gpu_fan = gpu_data.get('gpu_fan_percent', 0.0)
            
            # Update cards with defensive .get()
            if hasattr(self, 'gpu_clock_card'):
                status = "Idle" if gpu_clock < 1000 else "Active"
                self.gpu_clock_card.update_value(int(gpu_clock), "MHz", status, "#00f2ff")
            
            if hasattr(self, 'gpu_power_card'):
                status = "Low" if gpu_power < 100 else "High"
                self.gpu_power_card.update_value(gpu_power, "W", status, "#ff9800")
            
            if hasattr(self, 'gpu_fan_card'):
                status = "Quiet" if gpu_fan < 50 else "Active"
                self.gpu_fan_card.update_value(int(gpu_fan), "%", status, "#4ade80")
            
            # Also update the GPU Pro tab's temperature and memory cards
            if hasattr(self, 'gpu_temp_pro_card'):
                self.gpu_temp_pro_card.update_value(int(self.stats.gpu_temp), "°C", 
                                                   "Cool" if self.stats.gpu_temp < 70 else "Warm", "#00d2ff")
            
            if hasattr(self, 'gpu_memory_pro_card'):
                self.gpu_memory_pro_card.update_value(self.stats.gpu_vram_percent, "%", 
                                                     "Normal", "#6366f1")
            
        except Exception as e:
            logger.error(f"Error updating GPU advanced data: {e}")
    
    def on_storage_updated(self, storage_data: Dict[str, Any]):
        """Handle storage data updates from worker thread"""
        try:
            # Update drives table
            drives = storage_data.get('drives', {})
            self.drives_table.setRowCount(0)
            
            for idx, (device, drive_info) in enumerate(drives.items()):
                self.drives_table.insertRow(idx)
                
                device_item = QTableWidgetItem(device)
                total_item = QTableWidgetItem(str(drive_info.get('total_gb', 0)))
                used_item = QTableWidgetItem(str(drive_info.get('used_gb', 0)))
                free_item = QTableWidgetItem(str(drive_info.get('free_gb', 0)))
                percent_item = QTableWidgetItem(f"{drive_info.get('percent', 0):.1f}%")
                
                # Color code based on usage
                usage_percent = drive_info.get('percent', 0)
                if usage_percent >= 90:
                    percent_item.setForeground(QColor("#ff4444"))
                elif usage_percent >= 75:
                    percent_item.setForeground(QColor("#ffd700"))
                else:
                    percent_item.setForeground(QColor("#4ade80"))
                
                self.drives_table.setItem(idx, 0, device_item)
                self.drives_table.setItem(idx, 1, total_item)
                self.drives_table.setItem(idx, 2, used_item)
                self.drives_table.setItem(idx, 3, free_item)
                self.drives_table.setItem(idx, 4, percent_item)
            
            # Update I/O statistics
            io_counters = storage_data.get('io_counters', {})
            read_bytes = io_counters.get('read_bytes', 0) / (1024**3)  # Convert to GB
            write_bytes = io_counters.get('write_bytes', 0) / (1024**3)  # Convert to GB
            read_count = io_counters.get('read_count', 0)
            write_count = io_counters.get('write_count', 0)
            
            if hasattr(self, 'read_bytes_card'):
                self.read_bytes_card.update_value(read_bytes, "GB", "Normal", "#4ade80")
            if hasattr(self, 'write_bytes_card'):
                self.write_bytes_card.update_value(write_bytes, "GB", "Normal", "#ff6b6b")
            if hasattr(self, 'read_count_card'):
                self.read_count_card.update_value(int(read_count), "", "Normal", "#00d2ff")
            if hasattr(self, 'write_count_card'):
                self.write_count_card.update_value(int(write_count), "", "Normal", "#ff9800")
        
        except Exception as e:
            logger.error(f"Error updating storage data: {e}")
            
    def get_advanced_temperatures(self):
        """Get advanced temperature data"""
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps_fn = getattr(psutil, "sensors_temperatures", None)
                if temps_fn is not None:
                    temps = temps_fn()
                else:
                    temps = None
                if temps and 'coretemp' in temps:
                    self.stats.cpu_temp = temps['coretemp'][0].current
                elif temps and 'cpu_thermal' in temps:
                    self.stats.cpu_temp = temps['cpu_thermal'][0].current
                else:
                    self.stats.cpu_temp = 45.0
            else:
                self.stats.cpu_temp = 45.0
        except (OSError, AttributeError, IndexError) as e:
            logger.error(f"Temperature reading error: {e}")
            self.stats.cpu_temp = 45.0
            
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
        power_status, power_color = self.get_status_and_color(self.stats.gpu_power_draw, 150, 250)
        self.power_card.update_value(self.stats.gpu_power_draw, "W", power_status, power_color)
        
        # Update Predictive card (show predicted temperature)
        pred_status = "STABLE"
        pred_color = "#4ade80"
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
        
    def changeEvent(self, event):
        """Handle window state changes"""
        from PyQt6.QtCore import QEvent
        
        # Check if window is being minimized
        if self.isMinimized():
            logger.debug("Window minimized - hiding to tray")
            self.hide()
            event.accept()
            return
        
        super().changeEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event - minimize to tray instead of exiting"""
        # Check if this is a real close or minimize to tray
        if self.tray_icon is not None and self.tray_icon.isVisible():
            # Minimize to tray instead of closing
            logger.debug("Close button clicked - hiding to tray")
            self.hide()
            event.ignore()
        else:
            # Exit application
            logger.info("Closing application (no tray available)")
            self.is_running = False
            self.security_monitor.monitoring_active = False
            
            # Hide tray icon immediately
            if self.tray_icon is not None:
                self.tray_icon.hide()
            
            # Stop the hardware monitor worker thread
            if self.monitor_worker is not None:
                self.monitor_worker.stop()
            if self.monitor_thread is not None and self.monitor_thread.isRunning():
                self.monitor_thread.quit()
                self.monitor_thread.wait()
            
            self.save_config()
            event.accept()
    
    def mousePressEvent(self, event):
        """Handle mouse press - check if in header area for dragging"""
        if self.header_widget is not None:
            # Get header height and check if click is within header area
            header_height = self.header_widget.height()
            # Use local coordinates for accurate detection
            click_y = event.position().y()
            
            if click_y <= header_height:
                self.is_dragging = True
                # Store the offset between click position and window position
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move - drag window if in drag mode"""
        if self.is_dragging:
            # Move window so that the click point stays under the cursor
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release - stop dragging"""
        if self.is_dragging:
            self.is_dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

def main():
    """Main application entry point"""
    logger.info("Starting Vitreos Architect")
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = VitreosArchitect()
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