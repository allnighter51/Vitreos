"""
Vitreos Telemetry Worker - QThread Implementation
Non-blocking hardware monitoring with signal/slot architecture
"""

import time
import warnings
import platform
import subprocess
import statistics
import socket
from typing import Dict, Any, Optional, List
from PyQt6.QtCore import QThread, pyqtSignal
import psutil

# Optional imports with graceful fallback
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    print("[TELEMETRY] pynvml not available - GPU monitoring disabled")

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    print("[TELEMETRY] wmi not available - using fallback CPU detection")

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False
    print("[TELEMETRY] winreg not available - using basic fallback")


# ═══════════════════════════════════════════════════════════════════════════
# TELEMETRY WORKER - Hardware Data Collection Thread
# ═══════════════════════════════════════════════════════════════════════════

class TelemetryWorker(QThread):
    """
    Background thread for hardware telemetry collection.
    Emits data every 1 second without blocking the UI thread.
    """
    
    # Signals
    data_ready = pyqtSignal(dict)  # Emits complete telemetry dict
    log_message = pyqtSignal(str, str, str)  # (level, message, color)
    error_occurred = pyqtSignal(str)  # Error messages
    
    def __init__(self):
        super().__init__()
        
        self.running = False
        self.nvml_initialized = False
        self.gpu_handle = None
        self.debug_counter = 0  # For 3-second debug prints
        
        # Hardware discovery cache
        self.cpu_name = self._discover_cpu_name()
        self.core_count = psutil.cpu_count(logical=True)
        self.gpu_name = None
        self.gpu_vram_total = 0
        
        # Network adapter tracking
        self.active_adapter = None
        self.network_hogs_counter = 0
        self.last_net_io = {}
        self.last_adapter_io = {}  # Per-adapter tracking
        
        # Latency & Jitter tracking
        self.latency_samples: List[float] = []  # Last 10 ping samples
        self.gateway_ip = self._discover_gateway()
        self.dns_target = '1.1.1.1'
        
        # Network hogs tracking
        self.process_connections = {}  # PID -> connection count
        
        # Initialize NVML if available
        if NVML_AVAILABLE:
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=FutureWarning)
                    pynvml.nvmlInit()
                self.nvml_initialized = True
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                
                # Discover GPU name and VRAM
                self.gpu_name = self._discover_gpu_name()
                self.gpu_vram_total = self._discover_gpu_vram()
                
                self.log_message.emit("OK", f"GPU: {self.gpu_name} ({self.gpu_vram_total:.0f}GB)", "green")
            except Exception as e:
                self.log_message.emit("WARN", f"NVML init failed: {e}", "warning_orange")
        
        # Log CPU discovery
        self.log_message.emit("OK", f"CPU: {self.cpu_name} ({self.core_count} cores)", "green")
        
        # Discover primary network adapter
        self.active_adapter = self._get_primary_adapter()
        if self.active_adapter:
            self.log_message.emit("NET", f"Auto-detected Primary Adapter: {self.active_adapter}", "cyan")
        
        # Log network engine initialization
        if self.gateway_ip:
            self.log_message.emit("NET", f"Gateway: {self.gateway_ip} | DNS: {self.dns_target}", "cyan")
        print("[DEBUG] Network Engine: Data Layer Initialized")
    
    def run(self) -> None:
        """Main telemetry loop - runs in background thread."""
        self.running = True
        self.log_message.emit("SYS", "Telemetry worker started", "primary_purple")
        
        while self.running:
            try:
                # Collect all hardware data
                data = self._collect_telemetry()
                
                # Debug logging every 3 seconds
                self.debug_counter += 1
                if self.debug_counter % 3 == 0:
                    cpu_load = data.get('cpu', {}).get('totalLoad', 0)
                    gpu_temp = data.get('gpu', {}).get('temp', 0)
                    vram_used = data.get('gpu', {}).get('vramUsed', 0)
                    vram_total = data.get('gpu', {}).get('vramTotal', 0)
                    print(f"[DEBUG] Telemetry Packet: CPU {cpu_load:.0f}% | GPU {gpu_temp:.0f}°C | VRAM {vram_used:.1f}/{vram_total:.1f}GB")
                
                # Emit to main thread
                self.data_ready.emit(data)
                
                # Sleep for 1 second
                time.sleep(1.0)
            
            except Exception as e:
                self.error_occurred.emit(f"Telemetry error: {e}")
                time.sleep(1.0)
    
    def stop(self) -> None:
        """Stop the telemetry worker gracefully."""
        self.running = False
        self.log_message.emit("SYS", "Telemetry worker stopping...", "text_dim")
        
        # Cleanup NVML
        if self.nvml_initialized:
            try:
                pynvml.nvmlShutdown()
            except:
                pass
    
    # ───────────────────────────────────────────────────────────────────────
    # HARDWARE DISCOVERY METHODS
    # ───────────────────────────────────────────────────────────────────────
    
    def _discover_cpu_name(self) -> str:
        """Discover friendly CPU name using WMI, Registry, or fallback methods."""
        try:
            # Try WMI first (Windows-specific, most accurate)
            if WMI_AVAILABLE:
                try:
                    c = wmi.WMI()
                    for processor in c.Win32_Processor():
                        cpu_name = processor.Name.strip()
                        # Clean up common suffixes and junk
                        cpu_name = self._clean_cpu_name(cpu_name)
                        return cpu_name
                except Exception as e:
                    print(f"[TELEMETRY] WMI CPU detection failed: {e}")
            
            # Try Windows Registry (no WMI dependency)
            if WINREG_AVAILABLE:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                    cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                    winreg.CloseKey(key)
                    # Clean up the name
                    cpu_name = self._clean_cpu_name(cpu_name)
                    print(f"[TELEMETRY] CPU detected via Registry: {cpu_name}")
                    return cpu_name
                except Exception as e:
                    print(f"[TELEMETRY] Registry CPU detection failed: {e}")
            
            # Fallback to platform.processor()
            cpu_name = platform.processor()
            if cpu_name and cpu_name.strip() and 'Family' not in cpu_name:
                # Clean up the name
                cpu_name = self._clean_cpu_name(cpu_name)
                return cpu_name
            
            # Last resort: generic name
            return f"{platform.machine()} Processor"
        except Exception as e:
            print(f"[TELEMETRY] CPU discovery error: {e}")
            return "Unknown CPU"
    
    def _clean_cpu_name(self, name: str) -> str:
        """Clean CPU name by removing junk suffixes and trademarks."""
        # Force clean cut after specific CPU model numbers (5700X, 5800X, etc.)
        if '5700X' in name:
            name = name.split('5700X')[0] + '5700X'
        elif '5800X' in name:
            name = name.split('5800X')[0] + '5800X'
        elif '5900X' in name:
            name = name.split('5900X')[0] + '5900X'
        elif '5950X' in name:
            name = name.split('5950X')[0] + '5950X'
        
        # Phase 4: Explicit split on '8-Core' to ensure clean removal
        if '8-Core' in name:
            name = name.split('8-Core')[0].strip()
        if '16-Core' in name:
            name = name.split('16-Core')[0].strip()
        if '12-Core' in name:
            name = name.split('12-Core')[0].strip()
        
        # Remove common junk
        junk_patterns = [
            '(R)', '(TM)', '(tm)', '(r)',
            'with Radeon Graphics', 'with Radeon Vega Graphics',
            'CPU @', 'Processor'
        ]
        
        cleaned = name
        for pattern in junk_patterns:
            cleaned = cleaned.replace(pattern, '')
        
        # Clean up multiple spaces
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()
    
    def _discover_gpu_name(self) -> str:
        """Discover friendly GPU name via NVML with cleanup."""
        if not self.nvml_initialized or not self.gpu_handle:
            return "Unknown GPU"
        
        try:
            gpu_name = pynvml.nvmlDeviceGetName(self.gpu_handle)
            if isinstance(gpu_name, bytes):
                gpu_name = gpu_name.decode('utf-8')
            
            # Clean up technical prefixes
            gpu_name = gpu_name.replace('NVIDIA ', '').replace('GeForce ', '')
            gpu_name = gpu_name.replace('AMD ', '').replace('Radeon ', '')
            gpu_name = gpu_name.strip()
            
            return gpu_name
        except Exception as e:
            print(f"[TELEMETRY] GPU discovery error: {e}")
            return "Unknown GPU"
    
    def _discover_gpu_vram(self) -> float:
        """Discover GPU VRAM total in GB."""
        if not self.nvml_initialized or not self.gpu_handle:
            return 0.0
        
        try:
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            return memory_info.total / (1024**3)  # Convert to GB
        except Exception as e:
            return 0.0
    
    def _get_primary_adapter(self) -> Optional[str]:
        """Sniff logic: Identify primary network adapter with highest byte-count delta."""
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            io_counters = psutil.net_io_counters(pernic=True)
            
            # Store initial IO counters
            if not self.last_adapter_io:
                self.last_adapter_io = {iface: (io.bytes_sent, io.bytes_recv) 
                                        for iface, io in io_counters.items()}
                time.sleep(0.5)  # Wait for delta
                io_counters = psutil.net_io_counters(pernic=True)
            
            candidates = []
            
            for interface, addr_list in addrs.items():
                # Must be up
                if interface not in stats or not stats[interface].isup:
                    continue
                
                # Must have IPv4 address
                has_ipv4 = False
                for addr in addr_list:
                    if addr.family == 2:  # AF_INET (IPv4)
                        if addr.address and addr.address != '127.0.0.1':
                            has_ipv4 = True
                            break
                
                if not has_ipv4:
                    continue
                
                # Calculate byte delta
                if interface in io_counters and interface in self.last_adapter_io:
                    io = io_counters[interface]
                    last_sent, last_recv = self.last_adapter_io[interface]
                    delta = (io.bytes_sent - last_sent) + (io.bytes_recv - last_recv)
                    candidates.append((interface, delta))
                elif interface in io_counters:
                    io = io_counters[interface]
                    total_traffic = io.bytes_sent + io.bytes_recv
                    candidates.append((interface, total_traffic))
            
            # Update tracking
            self.last_adapter_io = {iface: (io.bytes_sent, io.bytes_recv) 
                                    for iface, io in io_counters.items()}
            
            # Sort by delta (highest first)
            if candidates:
                candidates.sort(key=lambda x: x[1], reverse=True)
                return candidates[0][0]
            
            return None
        except Exception as e:
            print(f"[TELEMETRY] Primary adapter detection failed: {e}")
            return None
    
    def _discover_gateway(self) -> Optional[str]:
        """Discover default gateway IP address."""
        try:
            # Get default gateway from routing table
            gateways = psutil.net_if_addrs()
            # Try to get gateway via socket connection test
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Extract gateway from local IP (assume .1 gateway)
            parts = local_ip.split('.')
            if len(parts) == 4:
                gateway = f"{parts[0]}.{parts[1]}.{parts[2]}.1"
                return gateway
            
            return '192.168.1.1'  # Fallback
        except Exception as e:
            print(f"[TELEMETRY] Gateway discovery failed: {e}")
            return '192.168.1.1'
    
    def _ping_target(self, target: str, timeout: int = 1) -> Optional[float]:
        """Ping a target and return latency in ms (threaded-safe)."""
        try:
            # Windows ping command
            result = subprocess.run(
                ['ping', '-n', '1', '-w', str(timeout * 1000), target],
                capture_output=True,
                text=True,
                timeout=timeout + 0.5
            )
            
            if result.returncode == 0:
                # Parse latency from output
                output = result.stdout
                if 'time=' in output or 'time<' in output:
                    # Extract time value
                    for line in output.split('\n'):
                        if 'time' in line.lower():
                            if 'time=' in line:
                                time_str = line.split('time=')[1].split('ms')[0].strip()
                            elif 'time<' in line:
                                time_str = line.split('time<')[1].split('ms')[0].strip()
                            else:
                                continue
                            try:
                                return float(time_str)
                            except ValueError:
                                continue
            return None
        except Exception as e:
            return None
    
    def _calculate_jitter(self) -> float:
        """Calculate jitter (standard deviation) from last 10 latency samples."""
        if len(self.latency_samples) < 2:
            return 0.0
        try:
            return statistics.stdev(self.latency_samples)
        except statistics.StatisticsError:
            return 0.0
    
    def _get_all_interfaces(self) -> List[Dict[str, Any]]:
        """Get all network interfaces with status and traffic data."""
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            io_counters = psutil.net_io_counters(pernic=True)
            
            interfaces = []
            
            for interface, addr_list in addrs.items():
                # Get IPv4 address
                ipv4 = None
                for addr in addr_list:
                    if addr.family == 2:  # AF_INET
                        ipv4 = addr.address
                        break
                
                # Get status
                is_up = interface in stats and stats[interface].isup
                
                # Get traffic
                traffic = 0
                if interface in io_counters:
                    io = io_counters[interface]
                    traffic = io.bytes_sent + io.bytes_recv
                
                interfaces.append({
                    'name': interface,
                    'ipv4': ipv4 or 'N/A',
                    'status': 'active' if is_up else 'idle',
                    'traffic': traffic,
                    'is_primary': interface == self.active_adapter
                })
            
            return interfaces
        except Exception as e:
            print(f"[TELEMETRY] Interface enumeration failed: {e}")
            return []
    
    def set_active_adapter(self, adapter_name: str) -> None:
        """Set the active network adapter for monitoring."""
        self.active_adapter = adapter_name
        self.log_message.emit("NET", f"Adapter switched to: {adapter_name}", "cyan")
    
    # ───────────────────────────────────────────────────────────────────────
    # DATA COLLECTION METHODS
    # ───────────────────────────────────────────────────────────────────────
    
    def _collect_telemetry(self) -> Dict[str, Any]:
        """
        Collect all hardware telemetry data.
        
        Returns:
            Dictionary with cpu, gpu, memory, storage, network, thermal data
        """
        # Increment network hogs counter
        self.network_hogs_counter += 1
        
        return {
            'cpu': self._get_cpu_data(),
            'gpu': self._get_gpu_data(),
            'memory': self._get_memory_data(),
            'storage': self._get_storage_data(),
            'network': self._get_network_data(),
            'thermal': self._get_thermal_data(),
            'networkHogs': self._get_network_hogs() if self.network_hogs_counter % 5 == 0 else [],
        }
    
    def _get_cpu_data(self) -> Dict[str, Any]:
        """Collect CPU metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_freq = psutil.cpu_freq()
            per_cpu = psutil.cpu_percent(percpu=True)
            
            # Get physical and logical core counts
            physical_cores = psutil.cpu_count(logical=False) or 0
            logical_threads = psutil.cpu_count(logical=True) or 0
            
            # Try to get CPU temperature
            cpu_temp = 0
            try:
                temps = psutil.sensors_temperatures()
                if 'coretemp' in temps:
                    cpu_temp = temps['coretemp'][0].current
                elif 'cpu_thermal' in temps:
                    cpu_temp = temps['cpu_thermal'][0].current
            except (AttributeError, KeyError):
                cpu_temp = 70  # Fallback for Windows
            
            return {
                'name': self.cpu_name,
                'totalLoad': cpu_percent,
                'temp': cpu_temp,
                'clock': int(cpu_freq.current) if cpu_freq else 5000,
                'cores': per_cpu,
                'coreCount': logical_threads,
                'physicalCores': physical_cores,
                'logicalThreads': logical_threads,
                'packagePwr': 142,  # Placeholder - requires specific hardware access
                'vid': 1.31,  # Placeholder
            }
        except Exception as e:
            self.log_message.emit("WARN", f"CPU data error: {e}", "warning_orange")
            return {
                'name': self.cpu_name, 'totalLoad': 0, 'temp': 0, 'clock': 0, 
                'cores': [], 'coreCount': self.core_count, 
                'physicalCores': 0, 'logicalThreads': 0,
                'packagePwr': 0, 'vid': 0
            }
    
    def _get_gpu_data(self) -> Dict[str, Any]:
        """Collect GPU metrics via NVML."""
        if not self.nvml_initialized or not self.gpu_handle:
            return {
                'name': 'NO GPU DETECTED',
                'usage': 0, 'vramUsed': 0, 'vramTotal': 0, 'vramPercent': 0,
                'coreClock': 0, 'memClock': 0, 'power': 0, 'temp': 0,
                'fanSpeed': 0, 'memBandwidth': 0, 'fans': [],
                'status': 'unavailable'
            }
        
        try:
            # Utilization
            utilization = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
            
            # Memory
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            vram_used = memory_info.used / (1024**3)  # GB
            vram_total = self.gpu_vram_total  # Use cached value
            vram_percent = (vram_used / vram_total * 100) if vram_total > 0 else 0
            
            # Temperature
            temp = pynvml.nvmlDeviceGetTemperature(self.gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
            
            # Power
            power = pynvml.nvmlDeviceGetPowerUsage(self.gpu_handle) / 1000  # Watts
            
            # Clocks
            core_clock = pynvml.nvmlDeviceGetClockInfo(self.gpu_handle, pynvml.NVML_CLOCK_GRAPHICS)
            mem_clock = pynvml.nvmlDeviceGetClockInfo(self.gpu_handle, pynvml.NVML_CLOCK_MEM)
            
            # Fan speed
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(self.gpu_handle)
            except:
                fan_speed = 0
            
            # Determine status based on temperature
            if temp > 85:
                status = 'critical'
            elif temp > 75:
                status = 'warning'
            else:
                status = 'normal'
            
            # Log warnings for high temps
            if temp > 85:
                self.log_message.emit("WARN", f"GPU temp elevated: {temp}°C", "critical_red")
            
            return {
                'name': self.gpu_name,
                'usage': utilization.gpu,
                'vramUsed': round(vram_used, 2),
                'vramTotal': round(vram_total, 2),
                'vramPercent': round(vram_percent, 1),
                'coreClock': core_clock,
                'memClock': mem_clock,
                'power': round(power, 1),
                'temp': temp,
                'fanSpeed': fan_speed,
                'memBandwidth': 756,  # Placeholder - requires calculation
                'fans': [
                    {'label': 'FAN 1', 'rpm': 941},
                    {'label': 'FAN 2', 'rpm': 956},
                    {'label': 'REAR', 'rpm': 75},
                ],
                'status': status
            }
        except Exception as e:
            self.log_message.emit("WARN", f"GPU data error: {e}", "warning_orange")
            return {
                'name': self.gpu_name or 'ERROR',
                'usage': 0, 'vramUsed': 0, 'vramTotal': self.gpu_vram_total, 'vramPercent': 0,
                'coreClock': 0, 'memClock': 0, 'power': 0, 'temp': 0,
                'fanSpeed': 0, 'memBandwidth': 0, 'fans': [],
                'status': 'error'
            }
    
    def _get_memory_data(self) -> Dict[str, Any]:
        """Collect memory metrics."""
        try:
            mem = psutil.virtual_memory()
            used_gb = mem.used / (1024**3)
            total_gb = mem.total / (1024**3)
            percent = mem.percent
            
            return {
                'totalUsed': round(used_gb, 2),
                'totalCapacity': round(total_gb, 2),
                'usedGB': round(used_gb, 2),
                'totalGB': round(total_gb, 2),
                'percent': percent,
                'slots': [
                    {'label': 'DIMM.A1', 'capacity': 16, 'speed': 6000, 'used': True},
                    {'label': 'DIMM.A2', 'capacity': 0, 'speed': 0, 'used': False},
                    {'label': 'DIMM.B1', 'capacity': 16, 'speed': 6000, 'used': True},
                    {'label': 'DIMM.B2', 'capacity': 0, 'speed': 0, 'used': False},
                ],
                'effectiveSpeed': 6000,
                'channelMode': 'DUAL 128-bit',
                'xmpActive': True,
            }
        except Exception as e:
            self.log_message.emit("WARN", f"Memory data error: {e}", "warning_orange")
            return {
                'totalUsed': 0, 'totalCapacity': 0, 'usedGB': 0, 'totalGB': 0, 'percent': 0,
                'slots': [], 'effectiveSpeed': 0, 'channelMode': '', 'xmpActive': False
            }
    
    def _get_storage_data(self) -> Dict[str, Any]:
        """Collect storage metrics."""
        try:
            drives = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    io_counters = psutil.disk_io_counters(perdisk=False)
                    
                    drives.append({
                        'type': 'NVMe' if 'nvme' in partition.device.lower() else 'HDD',
                        'model': partition.device,
                        'mountpoint': partition.mountpoint,
                        'device': partition.device,
                        'serial': f'{partition.device}-SERIAL',
                        'temp': 38,
                        'used': int(usage.used) // (1024**2),  # MB
                        'total': int(usage.total) // (1024**2),  # MB
                        'usedGB': usage.used / (1024**3),  # GB
                        'totalGB': usage.total / (1024**3),  # GB
                        'percent': usage.percent,
                        'readSpeed': int(io_counters.read_bytes) // (1024**2) if io_counters else 0,
                        'writeSpeed': int(io_counters.write_bytes) // (1024**2) if io_counters else 0,
                        'maxRead': 7300,
                        'maxWrite': 6600,
                    })
                except PermissionError:
                    continue
            
            return {
                'drives': drives,
                'raidStatus': 'NO RAID CONFIGURED',
            }
        except Exception as e:
            self.log_message.emit("WARN", f"Storage data error: {e}", "warning_orange")
            return {'drives': [], 'raidStatus': 'ERROR'}
    
    def _get_network_data(self) -> Dict[str, Any]:
        """Collect network metrics with latency/jitter tracking."""
        try:
            net_io = psutil.net_io_counters()
            
            # Calculate real-time bandwidth (MB/s converted to Mbps)
            download_mbps = round(net_io.bytes_recv / (1024**2), 2)
            upload_mbps = round(net_io.bytes_sent / (1024**2), 2)
            
            # Ping gateway for latency (non-blocking, quick timeout)
            latency_ms = 0
            if self.gateway_ip:
                ping_result = self._ping_target(self.gateway_ip, timeout=1)
                if ping_result is not None:
                    latency_ms = round(ping_result, 1)
                    
                    # Update latency samples (keep last 10)
                    self.latency_samples.append(latency_ms)
                    if len(self.latency_samples) > 10:
                        self.latency_samples.pop(0)
            
            # Calculate jitter
            jitter = round(self._calculate_jitter(), 2)
            
            # Jitter warning
            if jitter > 5.0:
                self.log_message.emit("NET", f"Jitter Warning: {jitter}ms", "cyan")
            
            # Get all interfaces
            interfaces = self._get_all_interfaces()
            
            return {
                'downloadMbps': download_mbps,
                'uploadMbps': upload_mbps,
                'latencyMs': latency_ms,
                'latency': latency_ms,
                'jitter': jitter,
                'gatewayLatency': latency_ms,
                'dnsLatency': 0,  # Placeholder for DNS ping
                'packetLoss': 0.0,
                'linkSpeed': 2.5,
                'downloadHistory': [850] * 30,  # Placeholder
                'uploadHistory': [90] * 30,  # Placeholder
                'activeInterface': self.active_adapter or 'ETH',
                'primaryNic': self.active_adapter or 'ETH',
                'interfaces': interfaces,
                'sentGB': round(net_io.bytes_sent / (1024**3), 2),
                'recvGB': round(net_io.bytes_recv / (1024**3), 2),
                'packets': round((net_io.packets_sent + net_io.packets_recv) / 1000, 0),
            }
        except Exception as e:
            self.log_message.emit("WARN", f"Network data error: {e}", "warning_orange")
            return {
                'downloadMbps': 0, 'uploadMbps': 0, 'latencyMs': 0, 'latency': 0,
                'jitter': 0, 'gatewayLatency': 0, 'dnsLatency': 0,
                'packetLoss': 0, 'linkSpeed': 0, 'downloadHistory': [], 'uploadHistory': [],
                'activeInterface': 'ETH', 'primaryNic': 'ETH', 'interfaces': [],
                'sentGB': 0, 'recvGB': 0, 'packets': 0
            }
    
    def _get_thermal_data(self) -> Dict[str, Any]:
        """Collect thermal metrics."""
        try:
            temps = []
            fans = []
            
            # Try to get sensor data
            try:
                sensor_temps = psutil.sensors_temperatures()
                for name, entries in sensor_temps.items():
                    for entry in entries:
                        temps.append({
                            'label': entry.label or name,
                            'value': int(entry.current),
                            'max': 100,
                        })
            except (AttributeError, KeyError):
                # Fallback temps for Windows
                temps = [
                    {'label': 'CPU', 'value': 75, 'max': 100},
                    {'label': 'GPU', 'value': 73, 'max': 100},
                    {'label': 'MBD', 'value': 56, 'max': 100},
                ]
            
            # Try to get fan data
            try:
                sensor_fans = psutil.sensors_fans()
                for name, entries in sensor_fans.items():
                    for entry in entries:
                        fans.append({
                            'label': entry.label or name,
                            'rpm': entry.current,
                            'maxRpm': 2000,
                        })
            except (AttributeError, KeyError):
                # Fallback fans for Windows
                fans = [
                    {'label': 'CPU_FAN', 'rpm': 1342, 'maxRpm': 2000},
                    {'label': 'CASE_FAN', 'rpm': 1011, 'maxRpm': 1500},
                ]
            
            return {
                'temps': temps[:5],  # Limit to 5
                'fans': fans[:6],  # Limit to 6
                'ambientTemp': 29,
            }
        except Exception as e:
            self.log_message.emit("WARN", f"Thermal data error: {e}", "warning_orange")
            return {'temps': [], 'fans': [], 'ambientTemp': 0}
    
    def _get_network_hogs(self) -> list:
        """Scrape network connections and identify top 5 bandwidth consumers (runs every 5 seconds)."""
        try:
            connections = psutil.net_connections(kind='inet')
            process_traffic = {}
            
            # Count connections per process
            connection_counts = {}
            for conn in connections:
                if conn.pid and conn.status == 'ESTABLISHED':
                    connection_counts[conn.pid] = connection_counts.get(conn.pid, 0) + 1
            
            # Get current IO counters
            current_io = psutil.net_io_counters(pernic=True)
            
            # Calculate deltas if we have previous data
            total_delta_recv = 0
            total_delta_sent = 0
            
            if self.last_net_io:
                for interface, io in current_io.items():
                    if interface in self.last_net_io:
                        prev_io = self.last_net_io[interface]
                        total_delta_recv += io.bytes_recv - prev_io.bytes_recv
                        total_delta_sent += io.bytes_sent - prev_io.bytes_sent
                
                # Convert to Mbps (5 second interval)
                total_download_mbps = (total_delta_recv * 8) / (5 * 1024 * 1024)
                total_upload_mbps = (total_delta_sent * 8) / (5 * 1024 * 1024)
                
                # Distribute traffic proportionally by connection count
                total_connections = sum(connection_counts.values())
                
                if total_connections > 0:
                    for pid, conn_count in connection_counts.items():
                        try:
                            proc = psutil.Process(pid)
                            proc_name = proc.name()
                            
                            # Proportional distribution
                            weight = conn_count / total_connections
                            
                            if proc_name not in process_traffic:
                                process_traffic[proc_name] = {
                                    'name': proc_name,
                                    'pid': pid,
                                    'download_mbps': 0.0,
                                    'upload_mbps': 0.0,
                                    'remote_ip': None,
                                }
                            
                            process_traffic[proc_name]['download_mbps'] += total_download_mbps * weight
                            process_traffic[proc_name]['upload_mbps'] += total_upload_mbps * weight
                            
                            # Get remote IP from first connection
                            if not process_traffic[proc_name]['remote_ip']:
                                for conn in connections:
                                    if conn.pid == pid and conn.raddr:
                                        process_traffic[proc_name]['remote_ip'] = conn.raddr.ip
                                        break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
            
            # Store current IO for next delta calculation
            self.last_net_io = current_io
            
            # Sort by total traffic and return top 5
            hogs = sorted(
                process_traffic.values(),
                key=lambda x: x['download_mbps'] + x['upload_mbps'],
                reverse=True
            )[:5]
            
            return hogs
        except Exception as e:
            print(f"[TELEMETRY] Network hogs error: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════════════

__all__ = ['TelemetryWorker']
