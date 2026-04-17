# pyright: reportMissingTypeStubs=false, reportConstantRedefinition=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
"""
Vitreos Bootstrap Worker - Asynchronous Hardware Initialization
Offloads heavy I/O operations (WMI, NVML, RPC) to background threads
"""

from typing import Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal
import warnings

# Optional imports with graceful fallback
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    pynvml = None  # type: ignore

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    wmi = None  # type: ignore
    WMI_AVAILABLE = False

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    winreg = None  # type: ignore
    WINREG_AVAILABLE = False


class HardwareBootstrapWorker(QThread):
    """
    Background worker for heavy hardware initialization.
    Discovers CPU name, GPU name, VRAM, and initializes NVML.
    """
    
    # Signals
    bootstrap_complete = pyqtSignal(dict)  # Emits hardware info dict
    bootstrap_failed = pyqtSignal(str)  # Error message
    progress_update = pyqtSignal(str)  # Status messages
    
    def __init__(self):
        super().__init__()
        self.hardware_info: Dict[str, Any] = {}
    
    def run(self) -> None:
        """Execute bootstrap sequence in background thread"""
        try:
            self.progress_update.emit("Discovering CPU...")
            cpu_name = self._discover_cpu_name()
            self.hardware_info['cpu_name'] = cpu_name
            
            self.progress_update.emit("Initializing NVML...")
            nvml_data = self._initialize_nvml()
            self.hardware_info.update(nvml_data)
            
            self.progress_update.emit("Hardware bootstrap complete")
            self.bootstrap_complete.emit(self.hardware_info)
            
        except Exception as e:
            self.bootstrap_failed.emit(f"Bootstrap failed: {e}")
    
    def _discover_cpu_name(self) -> str:
        """Discover friendly CPU name using WMI, Registry, or fallback"""
        try:
            # Try WMI first (Windows-specific, most accurate)
            if WMI_AVAILABLE and wmi is not None:
                try:
                    c = wmi.WMI()
                    for processor in c.Win32_Processor():
                        cpu_name = processor.Name.strip()
                        cpu_name = self._clean_cpu_name(cpu_name)
                        return cpu_name
                except Exception as e:
                    print(f"[BOOTSTRAP] WMI CPU detection failed: {e}")
            
            # Try Windows Registry (no WMI dependency)
            if WINREG_AVAILABLE and winreg is not None:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                    cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                    winreg.CloseKey(key)
                    cpu_name = self._clean_cpu_name(cpu_name)
                    return cpu_name
                except Exception as e:
                    print(f"[BOOTSTRAP] Registry CPU detection failed: {e}")
            
            # Fallback to platform.processor()
            import platform
            cpu_name = platform.processor()
            if cpu_name and cpu_name.strip() and 'Family' not in cpu_name:
                cpu_name = self._clean_cpu_name(cpu_name)
                return cpu_name
            
            return f"{platform.machine()} Processor"
        except Exception as e:
            print(f"[BOOTSTRAP] CPU discovery error: {e}")
            return "Unknown CPU"
    
    def _clean_cpu_name(self, name: str) -> str:
        """Clean CPU name by removing junk suffixes"""
        # Force clean cut after specific CPU model numbers
        if '5700X' in name:
            name = name.split('5700X')[0] + '5700X'
        elif '5800X' in name:
            name = name.split('5800X')[0] + '5800X'
        elif '5900X' in name:
            name = name.split('5900X')[0] + '5900X'
        elif '5950X' in name:
            name = name.split('5950X')[0] + '5950X'
        
        # Remove core count suffixes
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
        
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()
    
    def _initialize_nvml(self) -> Dict[str, Any]:
        """Initialize NVML and discover GPU info"""
        result = {
            'nvml_initialized': False,
            'gpu_handle': None,
            'gpu_name': 'NO GPU DETECTED',
            'gpu_vram_total': 0.0
        }
        
        if not NVML_AVAILABLE or pynvml is None:
            return result
        
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=FutureWarning)
                pynvml.nvmlInit()
            
            result['nvml_initialized'] = True
            gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            result['gpu_handle'] = gpu_handle
            
            # Discover GPU name
            gpu_name = pynvml.nvmlDeviceGetName(gpu_handle)
            if isinstance(gpu_name, bytes):
                gpu_name = gpu_name.decode('utf-8')
            
            gpu_name = gpu_name.replace('NVIDIA ', '').replace('GeForce ', '')
            gpu_name = gpu_name.replace('AMD ', '').replace('Radeon ', '')
            result['gpu_name'] = gpu_name.strip()
            
            # Discover VRAM
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(gpu_handle)
            vram_bytes = int(memory_info.total) if isinstance(memory_info.total, (int, float)) else 0
            result['gpu_vram_total'] = vram_bytes / (1024**3)
            
        except Exception as e:
            print(f"[BOOTSTRAP] NVML init failed: {e}")
        
        return result


class DiscordBootstrapWorker(QThread):
    """
    Background worker for Discord RPC connection.
    Never blocks the main thread with synchronous pipe operations.
    """
    
    # Signals
    connection_ready = pyqtSignal(object)  # Emits connected RPC object
    connection_failed = pyqtSignal(str)  # Error message
    progress_update = pyqtSignal(str)  # Status messages
    
    def __init__(self, client_id: str):
        super().__init__()
        self.client_id = client_id
    
    def run(self) -> None:
        """Attempt Discord RPC connection in background"""
        try:
            from pypresence.presence import Presence
            
            self.progress_update.emit("Connecting to Discord...")
            rpc = Presence(self.client_id)
            rpc.connect()
            
            self.progress_update.emit("Discord RPC connected")
            self.connection_ready.emit(rpc)
            
        except ImportError:
            self.connection_failed.emit("pypresence not installed")
        except Exception as e:
            self.connection_failed.emit(f"Connection failed: {e}")


__all__ = ['HardwareBootstrapWorker', 'DiscordBootstrapWorker']
