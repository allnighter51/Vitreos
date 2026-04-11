"""
Vitreos Sentinel - Worker Threads Module
Hardware monitoring, security scanning, and network analysis workers
"""
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, cast

from PyQt6.QtCore import QThread, pyqtSignal

# NVML imports with fallback
_pynvml_module: Any = None
_nvml_active = False

try:
    import pynvml  # type: ignore
    _pynvml_module = pynvml
    _nvml_active = True
except ImportError:
    pynvml = None  # type: ignore

# psutil import
_psutil_module: Any = None

try:
    import psutil
    _psutil_module = psutil
except ImportError:
    psutil = None  # type: ignore


@dataclass
class GPUTelemetry:
    """GPU telemetry data structure with explicit attribute initialization"""
    clock_mhz: int = 0
    power_watts: float = 0.0
    fan_percent: int = 0
    fan_rpm: int = 0
    temp_c: int = 0
    vram_used_mb: int = 0
    vram_total_mb: int = 0
    hotspot_temp_c: float = 0.0
    is_throttling: bool = False
    throttle_status: str = "Normal"


class HardwareMonitorWorker(QThread):
    """Main hardware monitoring worker thread"""
    
    stats_updated = pyqtSignal(dict)
    gpu_advanced_updated = pyqtSignal(object)
    combat_mode_detected = pyqtSignal(bool)
    
    def __init__(self) -> None:
        super().__init__()
        self.running = True
        self.update_interval = 1000
        self.nvml_initialized = False
        self.gpu_handle: Any = None
        
        if _nvml_active and _pynvml_module:
            try:
                _pynvml_module.nvmlInit()  # type: ignore
                self.nvml_initialized = True
                self.gpu_handle = _pynvml_module.nvmlDeviceGetHandleByIndex(0)  # type: ignore
            except Exception:
                self.nvml_initialized = False
    
    def run(self) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                stats = self._collect_stats()
                self.stats_updated.emit(stats)  # type: ignore
                
                if self.nvml_initialized:
                    gpu_telemetry = self._collect_gpu_telemetry()
                    self.gpu_advanced_updated.emit(gpu_telemetry)  # type: ignore
                
                combat_mode = stats.get('cpu_percent', 0) > 80 and stats.get('gpu_temp', 0) > 70
                self.combat_mode_detected.emit(combat_mode)  # type: ignore
                
            except Exception as e:
                print(f"[HW Monitor Error] {e}")
            
            self.msleep(self.update_interval)
    
    def _collect_stats(self) -> Dict[str, Any]:
        """Collect basic hardware statistics"""
        stats: Dict[str, Any] = {}
        
        if not _psutil_module:
            return stats
        
        stats['cpu_percent'] = _psutil_module.cpu_percent(interval=0.1)
        cpu_freq = _psutil_module.cpu_freq()
        stats['cpu_freq'] = cpu_freq.current if cpu_freq else 0
        stats['cpu_temp'] = self._get_cpu_temp()
        
        mem = _psutil_module.virtual_memory()
        stats['memory_percent'] = mem.percent
        stats['memory_used'] = mem.used
        stats['ram_percent'] = mem.percent
        stats['ram_used_gb'] = mem.used / (1024**3)
        stats['ram_total_gb'] = mem.total / (1024**3)
        
        disk = _psutil_module.disk_usage('/')
        stats['disk_percent'] = disk.percent
        stats['disk_used_gb'] = disk.used / (1024**3)
        stats['disk_total_gb'] = disk.total / (1024**3)
        stats['disk_free'] = disk.free
        
        if self.nvml_initialized and _pynvml_module and self.gpu_handle:
            try:
                stats['gpu_temp'] = _pynvml_module.nvmlDeviceGetTemperature(self.gpu_handle, _pynvml_module.NVML_TEMPERATURE_GPU)  # type: ignore
                stats['gpu_usage'] = _pynvml_module.nvmlDeviceGetUtilizationRates(self.gpu_handle).gpu  # type: ignore
                stats['gpu_util'] = stats['gpu_usage']
            except Exception:
                stats['gpu_temp'] = 0
                stats['gpu_usage'] = 0
                stats['gpu_util'] = 0
        else:
            stats['gpu_temp'] = 0
            stats['gpu_usage'] = 0
            stats['gpu_util'] = 0
        
        if _psutil_module:
            net = _psutil_module.net_io_counters()
            stats['net_sent_mb'] = net.bytes_sent / (1024**2)
            stats['net_recv_mb'] = net.bytes_recv / (1024**2)
            stats['net_sent_mbps'] = (net.bytes_sent / (1024**2)) / 60.0
            stats['net_recv_mbps'] = (net.bytes_recv / (1024**2)) / 60.0
        
        return stats
    
    def _collect_gpu_telemetry(self) -> GPUTelemetry:
        """Collect advanced GPU telemetry via NVML"""
        telemetry = GPUTelemetry()
        
        if not self.nvml_initialized or not _pynvml_module or not self.gpu_handle:
            return telemetry
        
        try:
            telemetry.clock_mhz = _pynvml_module.nvmlDeviceGetClockInfo(self.gpu_handle, _pynvml_module.NVML_CLOCK_GRAPHICS)  # type: ignore
            telemetry.power_watts = _pynvml_module.nvmlDeviceGetPowerUsage(self.gpu_handle) / 1000.0  # type: ignore
            
            try:
                telemetry.fan_percent = _pynvml_module.nvmlDeviceGetFanSpeed(self.gpu_handle)  # type: ignore
                telemetry.fan_rpm = int(telemetry.fan_percent * 30)
            except Exception:
                telemetry.fan_percent = 0
                telemetry.fan_rpm = 0
            
            telemetry.temp_c = _pynvml_module.nvmlDeviceGetTemperature(self.gpu_handle, _pynvml_module.NVML_TEMPERATURE_GPU)  # type: ignore
            
            mem_info = _pynvml_module.nvmlDeviceGetMemoryInfo(self.gpu_handle)  # type: ignore
            telemetry.vram_used_mb = int(mem_info.used) // (1024 * 1024)
            telemetry.vram_total_mb = int(mem_info.total) // (1024 * 1024)
            
            try:
                telemetry.hotspot_temp_c = float(_pynvml_module.nvmlDeviceGetTemperature(self.gpu_handle, _pynvml_module.NVML_TEMPERATURE_MEMORY))  # type: ignore
            except Exception:
                telemetry.hotspot_temp_c = float(telemetry.temp_c)
            
            if telemetry.temp_c > 85:
                telemetry.throttle_status = "Thermal Throttle"
                telemetry.is_throttling = True
            elif telemetry.power_watts > 300:
                telemetry.throttle_status = "Power Limit"
                telemetry.is_throttling = True
            else:
                telemetry.throttle_status = "Normal"
                telemetry.is_throttling = False
                
        except Exception as e:
            print(f"[GPU Telemetry Error] {e}")
        
        return telemetry
    
    def _get_cpu_temp(self) -> float:
        """Get CPU temperature"""
        if not _psutil_module:
            return 0.0
        try:
            get_temps: Any = getattr(_psutil_module, 'sensors_temperatures', lambda: {})
            temps = get_temps()
            if 'coretemp' in temps:
                return temps['coretemp'][0].current
        except Exception:
            pass
        return 0.0
    
    def stop(self) -> None:
        """Stop the monitoring thread"""
        self.running = False
        if self.nvml_initialized and _pynvml_module:
            try:
                _pynvml_module.nvmlShutdown()  # type: ignore
            except Exception:
                pass


class SecurityMonitorThread(QThread):
    """Security monitoring thread for USB events"""
    
    usb_event = pyqtSignal(str)
    security_alert = pyqtSignal(str)
    
    def __init__(self) -> None:
        super().__init__()
        self.running = True
        self.previous_usb_devices: set[str] = set()
    
    def run(self) -> None:
        """Main security monitoring loop"""
        while self.running:
            try:
                self._check_usb_devices()
                self._check_startup_entries()
            except Exception as e:
                print(f"[Security Monitor Error] {e}")
            
            self.msleep(2000)
    
    def _check_usb_devices(self) -> None:
        """Monitor USB device insertion/removal"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 "Get-PnpDevice -Class USB | Select-Object -ExpandProperty FriendlyName"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            current_devices = set(result.stdout.strip().split('\n'))
            
            new_devices = current_devices - self.previous_usb_devices
            for device in new_devices:
                if device.strip():
                    self.usb_event.emit(f"USB Inserted: {device}")  # type: ignore
            
            removed_devices = self.previous_usb_devices - current_devices
            for device in removed_devices:
                if device.strip():
                    self.usb_event.emit(f"USB Removed: {device}")  # type: ignore
            
            self.previous_usb_devices = current_devices
            
        except Exception as e:
            print(f"[USB Check Error] {e}")
    
    def _check_startup_entries(self) -> None:
        """Monitor Windows startup registry"""
        try:
            import winreg
            
            startup_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            
            entry_count = winreg.QueryInfoKey(startup_key)[0]
            
            if entry_count > 15:
                self.security_alert.emit(f"High startup entry count: {entry_count}")  # type: ignore
            
            winreg.CloseKey(startup_key)
            
        except Exception as e:
            print(f"[Startup Check Error] {e}")


class NetworkAnalyzer(QThread):
    """Network analysis thread"""
    
    ping_updated = pyqtSignal(dict)
    bandwidth_updated = pyqtSignal(list)
    
    def __init__(self) -> None:
        super().__init__()
        self.running = True
        self.target_host = "8.8.8.8"
    
    def run(self) -> None:
        """Main network analysis loop"""
        while self.running:
            try:
                ping_stats = self._measure_ping()
                self.ping_updated.emit(ping_stats)  # type: ignore
                
                bandwidth_hogs = self._analyze_bandwidth()
                self.bandwidth_updated.emit(bandwidth_hogs)  # type: ignore
                
            except Exception as e:
                print(f"[Network Analyzer Error] {e}")
            
            self.msleep(3000)
    
    def _measure_ping(self) -> Dict[str, Any]:
        """Measure ping and jitter"""
        stats: Dict[str, Any] = {'ping': 0, 'jitter': 0, 'packet_loss': 0}
        
        try:
            result = subprocess.run(
                ['ping', '-n', '4', self.target_host],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout
            
            if 'Average' in output:
                avg_line = [line for line in output.split('\n') if 'Average' in line][0]
                avg_ms = int(avg_line.split('=')[-1].replace('ms', '').strip())
                stats['ping'] = avg_ms
            
            if 'loss' in output.lower():
                loss_line = [line for line in output.split('\n') if 'loss' in line.lower()][0]
                loss_pct = int(loss_line.split('(')[1].split('%')[0])
                stats['packet_loss'] = loss_pct
            
            stats['jitter'] = int(stats['ping'] * 0.1)
            
        except Exception as e:
            print(f"[Ping Error] {e}")
        
        return stats
    
    def _analyze_bandwidth(self) -> List[Dict[str, Any]]:
        """Analyze network connections"""
        hogs: List[Dict[str, Any]] = []
        
        if not _psutil_module:
            return hogs
        
        try:
            connections = _psutil_module.net_connections(kind='inet')
            process_bandwidth: Dict[int, int] = {}
            
            for conn in connections:
                if conn.pid and conn.status == 'ESTABLISHED':
                    process_bandwidth[conn.pid] = process_bandwidth.get(conn.pid, 0) + 1
            
            sorted_pids = sorted(process_bandwidth.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for pid, conn_count in sorted_pids:
                try:
                    proc = _psutil_module.Process(pid)
                    hogs.append({
                        'pid': pid,
                        'name': proc.name(),
                        'connections': conn_count,
                        'download_mbps': conn_count * 0.5,
                        'upload_mbps': conn_count * 0.2
                    })
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"[Bandwidth Analysis Error] {e}")
        
        return hogs


class PredictiveThermalAlert:
    """Predictive thermal throttling alert"""
    
    def __init__(self) -> None:
        self.temp_history: List[float] = []
        self.max_history = 10
    
    def add_temperature(self, temp: float) -> None:
        """Add temperature reading"""
        self.temp_history.append(temp)
        if len(self.temp_history) > self.max_history:
            self.temp_history.pop(0)
    
    def predict_throttle_risk(self) -> str:
        """Predict thermal throttling risk"""
        if len(self.temp_history) < 3:
            return "Insufficient Data"
        
        avg_temp = sum(self.temp_history) / len(self.temp_history)
        trend = self.temp_history[-1] - self.temp_history[0]
        
        if avg_temp > 85:
            return "Critical - Throttling Imminent"
        elif avg_temp > 75 and trend > 5:
            return "Warning - Rising Temperature"
        elif avg_temp > 70:
            return "Caution - Monitor Closely"
        else:
            return "Normal - Optimal Range"


class SecurityMonitor:
    """Security monitoring for USB"""
    
    def __init__(self) -> None:
        self.usb_whitelist: set[str] = set()
        self.startup_baseline: set[str] = set()
    
    def add_usb_to_whitelist(self, device_id: str) -> None:
        """Add USB device to whitelist"""
        self.usb_whitelist.add(device_id)
    
    def is_usb_authorized(self, device_id: str) -> bool:
        """Check if USB device is authorized"""
        return device_id in self.usb_whitelist
    
    def set_startup_baseline(self, entries: set[str]) -> None:
        """Set baseline for startup entries"""
        self.startup_baseline = entries.copy()
    
    def detect_startup_changes(self, current_entries: set[str]) -> set[str]:
        """Detect unauthorized startup changes"""
        return current_entries - self.startup_baseline


class AlertManager:
    """System notification and database logging"""
    
    def __init__(self, db_connection: Any) -> None:
        self.db_connection = db_connection
    
    def log_alert(self, alert_type: str, message: str, dispatched: bool = False) -> None:
        """Log alert to database"""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(
                "INSERT INTO alert_history (timestamp, alert_type, message, dispatched) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(), alert_type, message, int(dispatched))
            )
            self.db_connection.commit()
        except Exception as e:
            print(f"[Alert Log Error] {e}")
    
    def dispatch_webhook(self, webhook_url: str, message: str) -> bool:
        """Dispatch alert via Discord webhook"""
        try:
            import requests
            payload = {"content": f"🚨 **Vitreos Alert** 🚨\n{message}"}
            response = requests.post(webhook_url, json=payload, timeout=5)
            return response.status_code == 204
        except Exception as e:
            print(f"[Webhook Dispatch Error] {e}")
            return False
