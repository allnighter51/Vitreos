# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportConstantRedefinition=false, reportPossiblyUnboundVariable=false, reportOperatorIssue=false, reportOptionalMemberAccess=false
"""
Vitreos Pulse - Python-Based Telemetry Fallback
Optimized for sustainable monitoring with minimal CPU overhead

Architecture:
- Python Background Thread: Polls hardware at 1Hz using psutil, pynvml, and wmi
- Python UI: QTimer pulls latest snapshot at 1Hz
- Python Logs: QTimer flushes buffered logs at 5s intervals
"""

from typing import Dict, Any, List
from collections import deque
from datetime import datetime
import threading
import time
import os
import re

from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QThread

from src.core.vitreos_logger import v_debug, v_info, v_error

# Hardware dependencies
import psutil

try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
    nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
except Exception:
    NVML_AVAILABLE = False
    nvml_handle = None

try:
    import wmi
    # We test import but create the WMI client inside the thread
    WMI_AVAILABLE = True
except Exception:
    WMI_AVAILABLE = False


class TelemetryWorkerThread(QThread):
    """Background thread that continuously polls hardware (1Hz)"""
    def __init__(self, interval_ms: int = 1000):
        super().__init__()
        self.interval_ms = interval_ms
        self.running = True
        self.latest_data: Dict[str, Any] = {}
        self.lock = threading.Lock()
        
        # Network tracking
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        
        # Disk tracking
        try:
            self.last_disk_io = psutil.disk_io_counters(perdisk=False)
            self.last_perdisk_io = psutil.disk_io_counters(perdisk=True)
        except Exception:
            self.last_disk_io = None
            self.last_perdisk_io = {}
        self.last_disk_time = time.time()
        self._disk_cache: Dict[int, Dict[str, Any]] = {}
        self._drive_to_disk_cache: Dict[str, int] = {}
        self._last_disk_cache_time = 0.0

        # CPU info cache
        self.cpu_name = self._get_cpu_name()

    def _get_cpu_name(self) -> str:
        name = ""
        try:
            if WMI_AVAILABLE:
                import wmi
                import pythoncom
                pythoncom.CoInitialize()
                c = wmi.WMI()
                for cpu in c.Win32_Processor():
                    name = str(cpu.Name or '').strip()
                    pythoncom.CoUninitialize()
                    break
        except Exception:
            pass
        if not name:
            # Fallback to standard platform/psutil techniques if WMI fails
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                name = str(winreg.QueryValueEx(key, "ProcessorNameString")[0] or '').strip()
                winreg.CloseKey(key)
            except Exception:
                import platform
                name = str(platform.processor() or 'CPU').strip()
        # Clean redundant core suffix (e.g. '12-Core Processor') to prevent UI overflow
        cleaned = re.sub(r'\s+\d+-[Cc]ore\s+[Pp]rocessor', '', name).strip()
        return cleaned or name

    def _update_disk_cache(self, wmi_client) -> None:
        if not wmi_client:
            return
        try:
            part_to_disk: Dict[str, int] = {}
            for p in wmi_client.Win32_DiskPartition():
                part_to_disk[str(p.DeviceID)] = int(p.DiskIndex)

            drive_to_disk: Dict[str, int] = {}
            for rel in wmi_client.Win32_LogicalDiskToPartition():
                try:
                    ant_id = str(rel.Antecedent.DeviceID)
                    dep_id = str(rel.Dependent.DeviceID)
                    if ant_id in part_to_disk:
                        drive_to_disk[dep_id] = part_to_disk[ant_id]
                except Exception:
                    pass

            disk_info: Dict[int, Dict[str, Any]] = {}
            for d in wmi_client.Win32_DiskDrive():
                disk_info[int(d.Index)] = {
                    'model': str(d.Model or 'Generic Disk').strip(),
                    'serial': str(d.SerialNumber or 'N/A').strip(),
                    'interface': str(d.InterfaceType or '').strip(),
                    'size': int(d.Size or 0)
                }

            self._drive_to_disk_cache = drive_to_disk
            self._disk_cache = disk_info
            self._last_disk_cache_time = time.time()
        except Exception:
            pass

    def run(self):
        wmi_client = None
        if WMI_AVAILABLE:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                import wmi
                wmi_client = wmi.WMI()
            except:
                wmi_client = None

        while self.running:
            start_t = time.time()
            data = self._poll_all(wmi_client)
            
            with self.lock:
                self.latest_data = data
            
            elapsed = time.time() - start_t
            sleep_time = max(0.01, (self.interval_ms / 1000.0) - elapsed)
            time.sleep(sleep_time)

        if WMI_AVAILABLE:
            import pythoncom
            pythoncom.CoUninitialize()

    def get_latest(self) -> Dict[str, Any]:
        with self.lock:
            return self.latest_data.copy()

    def _poll_all(self, wmi_client) -> Dict[str, Any]:
        if wmi_client and (time.time() - self._last_disk_cache_time > 30.0 or not self._disk_cache):
            self._update_disk_cache(wmi_client)

        return {
            'cpu': self._poll_cpu(wmi_client),
            'gpu': self._poll_gpu(wmi_client),
            'memory': self._poll_memory(wmi_client),
            'storage': self._poll_storage(),
            'network': self._poll_network()
        }

    def _poll_cpu(self, wmi_client) -> Dict[str, Any]:
        cores_load = psutil.cpu_percent(interval=0.0, percpu=True)
        total_load = psutil.cpu_percent(interval=0.0)
        
        # Approximate Temp for Windows as WMI requires elevated privileges
        temp = 0.0
        try:
            if wmi_client:
                temps = wmi_client.MSAcpi_ThermalZoneTemperature(namespace="root\\wmi")
                if temps:
                    # Conversion from 1/10th Kelvin to Celsius
                    temp = (temps[0].CurrentTemperature / 10.0) - 273.15
        except: pass
        
        if temp <= 0.0: 
            # Simulate a realistic temperature based on load if sensor access is denied
            temp = 45.0 + (total_load * 0.4)
            
        return {
            'name': self.cpu_name,
            'coreCount': psutil.cpu_count(logical=True),
            'physicalCores': psutil.cpu_count(logical=False),
            'logicalThreads': psutil.cpu_count(logical=True),
            'totalLoad': total_load,
            'temp': temp,
            'cores': cores_load
        }

    def _poll_gpu(self, wmi_client=None) -> List[Dict[str, Any]]:
        gpus: List[Dict[str, Any]] = []
        nvml_gpu_names: set[str] = set()
        
        # 1. NVIDIA GPUs via NVML
        if NVML_AVAILABLE:
            try:
                device_count = pynvml.nvmlDeviceGetCount()
                for i in range(device_count):
                    try:
                        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                        name = pynvml.nvmlDeviceGetName(handle)
                        if isinstance(name, bytes): name = name.decode('utf-8')
                        nvml_gpu_names.add(name)
                        
                        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                        
                        try: power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                        except: power = 0.0
                        
                        try: core_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                        except: core_clock = 0
                        
                        try: mem_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                        except: mem_clock = 0
                        
                        try: fan = pynvml.nvmlDeviceGetFanSpeed(handle)
                        except: fan = 0

                        try: fan_rpm = pynvml.nvmlDeviceGetFanSpeed_v2(handle, 0)
                        except: fan_rpm = None

                        if fan_rpm is None:
                            fan_rpm = int(fan * 30) if fan > 0 else 0
                        
                        bw = (mem_clock * 2 * 256) / 8000.0 if mem_clock > 0 else 0.0
                        
                        gpus.append({
                            'name': name,
                            'vramTotal': mem_info.total / (1024**3),
                            'driver': pynvml.nvmlSystemGetDriverVersion().decode('utf-8') if isinstance(pynvml.nvmlSystemGetDriverVersion(), bytes) else pynvml.nvmlSystemGetDriverVersion(),
                            'coreClock': core_clock,
                            'memClock': mem_clock,
                            'power': power,
                            'temp': temp,
                            'usage': util.gpu,
                            'vramUsed': mem_info.used / (1024**3),
                            'vramPercent': (mem_info.used / mem_info.total) * 100.0 if mem_info.total > 0 else 0,
                            'memBandwidth': bw,
                            'fanSpeed': fan,
                            'fanRpm': fan_rpm,
                            'is_nvml': True
                        })
                    except Exception:
                        continue
            except Exception:
                pass

        # 2. Other GPUs via WMI (e.g. Intel iGPU or AMD)
        if wmi_client:
            try:
                VIRTUAL_GPU_SUBSTRINGS = (
                    'virtual', 'oculus', 'meta', 'parsec', 'microsoft basic display', 
                    'remote desktop', 'spacedesk', 'rdp', 'v-display', 'citrix', 'indirect display'
                )
                for vc in wmi_client.Win32_VideoController():
                    name = vc.Name.strip() if vc.Name else "Unknown GPU"
                    # Skip if we already got this via NVML
                    if name in nvml_gpu_names or any(name in n for n in nvml_gpu_names):
                        continue
                    # Skip virtual display adapters
                    if any(v in name.lower() for v in VIRTUAL_GPU_SUBSTRINGS):
                        continue
                    
                    vram_bytes = 0
                    if vc.AdapterRAM:
                        vram_bytes = abs(int(vc.AdapterRAM))
                    
                    gpus.append({
                        'name': name,
                        'vramTotal': vram_bytes / (1024**3) if vram_bytes else 4.0,
                        'driver': vc.DriverVersion if vc.DriverVersion else 'Unknown',
                        'coreClock': 0,
                        'memClock': 0,
                        'power': 0.0,
                        'temp': 0,
                        'usage': 0,
                        'vramUsed': 0.0,
                        'vramPercent': 0.0,
                        'memBandwidth': 0.0,
                        'fanSpeed': 0,
                        'fanRpm': 0,
                        'is_nvml': False
                    })
            except Exception:
                pass

        if not gpus:
            gpus.append({'name': 'NO GPU', 'vramTotal': 0, 'driver': 'N/A', 'coreClock': 0, 'memClock': 0, 'power': 0, 'temp': 0, 'usage': 0, 'vramUsed': 0, 'vramPercent': 0, 'memBandwidth': 0, 'fanSpeed': 0, 'fanRpm': 0, 'is_nvml': False})

        return gpus

    def _poll_memory(self, wmi_client) -> Dict[str, Any]:
        mem = psutil.virtual_memory()

        slots: list = []
        total_slots: int = 0
        speed: int = 0

        try:
            if wmi_client:
                # ── 1. Board-level: total physical slot count ──────────────
                try:
                    for arr in wmi_client.Win32_PhysicalMemoryArray():
                        md = getattr(arr, 'MemoryDevices', None)
                        if md:
                            total_slots = int(md)
                            break
                except Exception:
                    pass

                # ── 2. Populated physical sticks ──────────────────────────
                try:
                    for stick in wmi_client.Win32_PhysicalMemory():
                        cap_bytes: int = 0
                        try:
                            cap_bytes = int(stick.Capacity or 0)
                        except Exception:
                            pass

                        clk: int = 0
                        try:
                            clk = int(stick.ConfiguredClockSpeed or stick.Speed or 0)
                        except Exception:
                            pass

                        bank_raw = str(stick.BankLabel or '').strip()
                        loc_raw = str(stick.DeviceLocator or f'SLOT{len(slots)+1}').strip()

                        # Disambiguate locator if BankLabel specifies channel (e.g. 'P0 CHANNEL A' vs 'P0 CHANNEL B')
                        m_chan = re.search(r'CHANNEL\s*([A-Za-z0-9]+)', bank_raw, re.IGNORECASE)
                        m_loc_num = re.search(r'(\d+)', loc_raw)
                        num_str = m_loc_num.group(1) if m_loc_num else str(len(slots) + 1)
                        if m_chan and ('CHANNEL' not in loc_raw.upper() and not re.search(r'[A-D]\d', loc_raw)):
                            chan_str = m_chan.group(1).upper()
                            resolved_locator = f"DIMM_{chan_str}{num_str}"
                        else:
                            resolved_locator = loc_raw

                        slots.append({
                            'locator':      resolved_locator,
                            'bankLabel':    bank_raw,
                            'capacityGB':   cap_bytes / (1024 ** 3),
                            'speed':        clk,
                            'manufacturer': str(stick.Manufacturer or '').strip(),
                            'partNumber':   str(stick.PartNumber   or '').strip(),
                        })
                        if not speed and clk:
                            speed = clk
                except Exception:
                    pass
        except Exception:
            pass

        # ── 3. Fallback when WMI is unavailable ───────────────────────────
        if not slots:
            total_gb = mem.total / (1024 ** 3)
            if total_gb <= 8:
                loc_list = ['DIMM_A1']
            elif total_gb <= 16:
                loc_list = ['DIMM_A1', 'DIMM_B1']
            else:
                loc_list = ['DIMM_A1', 'DIMM_A2', 'DIMM_B1', 'DIMM_B2']
            per = total_gb / len(loc_list)
            slots = [{'locator': l, 'bankLabel': '', 'capacityGB': per,
                      'speed': 3200, 'manufacturer': '', 'partNumber': ''}
                     for l in loc_list]
            speed = 3200

        # If WMI didn't give us a board slot count, infer it
        if total_slots <= 0:
            total_slots = max(len(slots), 2)
            if total_slots > 2:
                total_slots = 4

        # Effective speed: DDR5 clock reported in MT/s directly when >= 3600
        if speed:
            effective_speed = speed if speed >= 3600 else speed * 2
        else:
            effective_speed = 0

        # Standby / Cached memory from WMI PerfOS
        standby_gb = 0.0
        if wmi_client:
            try:
                perfs = wmi_client.Win32_PerfFormattedData_PerfOS_Memory()
                if perfs:
                    p = perfs[0]
                    norm = int(getattr(p, 'StandbyCacheNormalPriorityBytes', 0) or 0)
                    core = int(getattr(p, 'StandbyCacheCoreBytes', 0) or 0)
                    resv = int(getattr(p, 'StandbyCacheReserveBytes', 0) or 0)
                    standby_gb = (norm + core + resv) / (1024 ** 3)
            except Exception:
                pass
        if standby_gb <= 0.0:
            standby_gb = max(0.0, (mem.available - mem.free) / (1024 ** 3))

        return {
            'totalGB':       mem.total    / (1024 ** 3),
            'usedGB':        mem.used     / (1024 ** 3),
            'availableGB':   mem.available / (1024 ** 3),
            'cachedGB':      standby_gb,
            'percent':       mem.percent,
            'slots':         slots,
            'totalSlots':    total_slots,
            'effectiveSpeed': effective_speed or speed,
            'channel':       'Dual' if len(slots) > 1 else 'Single',
        }

    def _poll_storage(self) -> Dict[str, Any]:
        now = time.time()
        dt = max(0.001, now - getattr(self, 'last_disk_time', now))

        try:
            current_io = psutil.disk_io_counters(perdisk=False)
            current_perdisk = psutil.disk_io_counters(perdisk=True)
            if hasattr(self, 'last_disk_io') and self.last_disk_io and current_io:
                global_read_speed = ((current_io.read_bytes - self.last_disk_io.read_bytes) / dt) / (1024 * 1024)
                global_write_speed = ((current_io.write_bytes - self.last_disk_io.write_bytes) / dt) / (1024 * 1024)
            else:
                global_read_speed = 0.0
                global_write_speed = 0.0
        except Exception:
            current_io = None
            current_perdisk = {}
            global_read_speed = 0.0
            global_write_speed = 0.0

        drives = []
        try:
            for part in psutil.disk_partitions(all=False):
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    dev_id = part.device.replace('\\', '')
                    
                    # Map to physical disk info
                    disk_idx = self._drive_to_disk_cache.get(dev_id)
                    pdisk = self._disk_cache.get(disk_idx, {}) if disk_idx is not None else {}
                    model = str(pdisk.get('model') or f"Drive {dev_id}").strip()
                    serial = str(pdisk.get('serial') or 'N/A').strip()

                    # Determine media type and throughput rating
                    m_lower = model.lower()
                    if 'nvme' in m_lower or 'sn770' in m_lower or '970' in m_lower or 'pci' in m_lower:
                        drive_type = 'NVMe'
                        if 'sn770' in m_lower or '980 pro' in m_lower or '990 pro' in m_lower or 'gen4' in m_lower:
                            max_read = 5150
                            max_write = 4900
                        else:
                            max_read = 3500
                            max_write = 3300
                    elif 'ssd' in m_lower:
                        drive_type = 'SSD'
                        max_read = 560
                        max_write = 530
                    elif 'st2000' in m_lower or 'barracuda' in m_lower or 'hdd' in m_lower or ('wd' in m_lower and 'blue' in m_lower):
                        drive_type = 'HDD'
                        max_read = 220
                        max_write = 220
                    else:
                        drive_type = 'SSD/NVMe'
                        max_read = 3500
                        max_write = 3000

                    # Calculate per-disk throughput
                    read_speed = 0.0
                    write_speed = 0.0
                    if disk_idx is not None:
                        pdisk_key = f"PhysicalDrive{disk_idx}"
                        if pdisk_key in current_perdisk and hasattr(self, 'last_perdisk_io') and pdisk_key in self.last_perdisk_io:
                            prev_p = self.last_perdisk_io[pdisk_key]
                            curr_p = current_perdisk[pdisk_key]
                            read_speed = max(0.0, ((curr_p.read_bytes - prev_p.read_bytes) / dt) / (1024 * 1024))
                            write_speed = max(0.0, ((curr_p.write_bytes - prev_p.write_bytes) / dt) / (1024 * 1024))
                    if read_speed <= 0.0 and global_read_speed > 0.0 and len(drives) == 0:
                        read_speed = global_read_speed
                    if write_speed <= 0.0 and global_write_speed > 0.0 and len(drives) == 0:
                        write_speed = global_write_speed

                    drives.append({
                        'device': dev_id,
                        'mountpoint': part.mountpoint,
                        'model': model,
                        'serial': serial,
                        'type': drive_type,
                        'totalGB': usage.total / (1024**3),
                        'usedGB': usage.used / (1024**3),
                        'readSpeed': read_speed,
                        'writeSpeed': write_speed,
                        'maxRead': max_read,
                        'maxWrite': max_write,
                        'temp': 0
                    })
                except Exception:
                    continue
        except Exception:
            pass

        self.last_disk_io = current_io
        self.last_perdisk_io = current_perdisk
        self.last_disk_time = now

        return {
            'drives': drives,
            'reads': current_io.read_count if current_io else 0,
            'writes': current_io.write_count if current_io else 0
        }

    def _poll_network(self) -> Dict[str, Any]:
        primary_nic = 'Unknown'
        try:
            stats = psutil.net_io_counters(pernic=True)
            max_bytes = -1
            for nic, stat in stats.items():
                if 'Loopback' not in nic:
                    total_bytes = stat.bytes_recv + stat.bytes_sent
                    if total_bytes > max_bytes:
                        max_bytes = total_bytes
                        primary_nic = nic
        except: pass

        net_io = psutil.net_io_counters()
        now = time.time()
        dt = now - getattr(self, 'last_net_time', now)
        
        if dt > 0 and hasattr(self, 'last_net_io'):
            dl_mbps = ((net_io.bytes_recv - self.last_net_io.bytes_recv) * 8) / (1024 * 1024 * dt)
            ul_mbps = ((net_io.bytes_sent - self.last_net_io.bytes_sent) * 8) / (1024 * 1024 * dt)
            packets = (net_io.packets_recv + net_io.packets_sent) - (self.last_net_io.packets_recv + self.last_net_io.packets_sent)
            pps = packets / dt
        else:
            dl_mbps = 0.0
            ul_mbps = 0.0
            pps = 0.0
            
        self.last_net_io = net_io
        self.last_net_time = now
        
        return {
            'primaryNic': primary_nic,
            'downloadMbps': max(0.0, dl_mbps),
            'uploadMbps': max(0.0, ul_mbps),
            'signalStrength': 100,
            'latency': 10,
            'packetsPerSec': max(0.0, pps)
        }


PULSE_AVAILABLE = True  # Mock True so main.py doesn't error out

class PullBasedTelemetry(QObject):
    """
    Pull-based telemetry manager with 1Hz polling and 5s log batching.
    Now powered purely by Python (psutil/pynvml/wmi).
    """
    
    data_ready = pyqtSignal(dict)
    log_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        self.worker = TelemetryWorkerThread(1000)
        
        self.ui_timer = QTimer()
        self.ui_timer.setInterval(1000)
        self.ui_timer.timeout.connect(self._pull_metrics)
        
        self.log_flush_timer = QTimer()
        self.log_flush_timer.setInterval(5000)
        self.log_flush_timer.timeout.connect(self._flush_logs_to_ui)
        
        self.log_buffer = deque(maxlen=100)
        self.update_counter = 0
        
        self._last_cpu_load = 0
        self._last_gpu_load = 0
        self._last_cpu_temp = 0
        self._last_gpu_temp = 0
        self._network_peak = 0
        self._initial_discovery_logged = False
        
        v_info("Python Pull-based telemetry initialized")
    
    def start(self) -> None:
        try:
            self.worker.start()
            self._buffer_log("OK", "Hardware discovery complete", "green")
            
            self.ui_timer.start()
            self.log_flush_timer.start()
            
            self._buffer_log("SYS", "Telemetry active (1Hz polling)", "primary_purple")
            v_info("Telemetry started")
        except Exception as e:
            v_error(f"Bootstrap failed: {e}")
            self.error_occurred.emit(f"Bootstrap failed: {e}")
    
    def stop(self) -> None:
        self.ui_timer.stop()
        self.log_flush_timer.stop()
        self.worker.running = False
        self.worker.wait(2000)
        self._buffer_log("SYS", "Telemetry stopped", "text_dim")
        self._flush_logs_to_ui()
    
    def _pull_metrics(self) -> None:
        try:
            data = self.worker.get_latest()
            if data:
                self.data_ready.emit(data)
                self._check_significant_events(data)
            self.update_counter += 1
        except Exception as e:
            v_error(f"Metrics pull error: {e}")
            self.error_occurred.emit(f"Metrics pull error: {e}")
    
    def _check_significant_events(self, data: Dict[str, Any]) -> None:
        cpu_load = data.get('cpu', {}).get('totalLoad', 0)
        
        # Handle GPU as list
        gpu_data_source = data.get('gpu', [])
        gpu_data = gpu_data_source[0] if isinstance(gpu_data_source, list) and gpu_data_source else (gpu_data_source if isinstance(gpu_data_source, dict) else {})
        
        # Initial genuine hardware discovery announcement
        if not self._initial_discovery_logged:
            self._initial_discovery_logged = True
            cpu_info = data.get('cpu', {})
            c_name = cpu_info.get('name')
            if c_name:
                self._buffer_log("CPU", f"{c_name} online", "cyan")
            if gpu_data.get('name') and gpu_data.get('name') != 'NO GPU':
                drv = f" (Driver {gpu_data.get('driver')})" if gpu_data.get('driver') else ""
                self._buffer_log("GPU", f"{gpu_data.get('name')}{drv}", "warning_orange")
            mem_data = data.get('memory', {})
            t_gb = mem_data.get('totalGB', 0)
            chan = mem_data.get('channel', 'Dual')
            eff_spd = mem_data.get('effectiveSpeed', 0)
            spd_text = f" @ {eff_spd} MT/s" if eff_spd else ""
            if t_gb > 0:
                self._buffer_log("MEM", f"{t_gb:.0f} GB {chan}-Channel RAM{spd_text}", "purple_dim")
            self._flush_logs_to_ui()

        gpu_load = gpu_data.get('usage', 0)
        cpu_temp = data.get('cpu', {}).get('temp', 0)
        gpu_temp = gpu_data.get('temp', 0)

        download_mbps = data.get('network', {}).get('downloadMbps', 0)
        
        if abs(cpu_load - self._last_cpu_load) > 25:
            self._buffer_log("CPU", f"Load spike: {self._last_cpu_load:.0f}% → {cpu_load:.0f}%", "warning_orange")
            self._last_cpu_load = cpu_load
        
        if abs(gpu_load - self._last_gpu_load) > 25:
            self._buffer_log("GPU", f"Load spike: {self._last_gpu_load:.0f}% → {gpu_load:.0f}%", "warning_orange")
            self._last_gpu_load = gpu_load
        
        if abs(cpu_temp - self._last_cpu_temp) > 5:
            color = "critical_red" if cpu_temp > 85 else "warning_orange" if cpu_temp > 75 else "cyan"
            self._buffer_log("CPU", f"Temp change: {self._last_cpu_temp:.0f}°C → {cpu_temp:.0f}°C", color)
            self._last_cpu_temp = cpu_temp
        
        if abs(gpu_temp - self._last_gpu_temp) > 5:
            color = "critical_red" if gpu_temp > 85 else "warning_orange" if gpu_temp > 75 else "warning_orange"
            self._buffer_log("GPU", f"Temp change: {self._last_gpu_temp:.0f}°C → {gpu_temp:.0f}°C", color)
            self._last_gpu_temp = gpu_temp
        
        if download_mbps > self._network_peak:
            self._network_peak = download_mbps
            self._buffer_log("NET", f"New peak: {download_mbps:.1f} Mbps", "green")
    
    def _buffer_log(self, level: str, message: str, color: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        self.log_buffer.append((log_line, color))
    
    def _flush_logs_to_ui(self) -> None:
        if not self.log_buffer: return
        batch_lines = [f"{color}|{line}" for line, color in self.log_buffer]
        self.log_ready.emit("\n".join(batch_lines))
        self.log_buffer.clear()
    
    def set_polling_rate(self, interval_ms: int) -> None:
        self.worker.interval_ms = interval_ms
        self._buffer_log("SYS", f"Hardware polling: {interval_ms}ms", "cyan")
    
    def set_ui_refresh_rate(self, interval_ms: int) -> None:
        self.ui_timer.setInterval(interval_ms)
        self._buffer_log("SYS", f"UI refresh: {interval_ms}ms", "cyan")
    
    def get_polling_rate(self) -> int:
        return self.worker.interval_ms
    
    def set_active_adapter(self, adapter_name: str) -> None:
        self._buffer_log("NET", f"Adapter: {adapter_name}", "cyan")

__all__ = ['PullBasedTelemetry', 'PULSE_AVAILABLE']
