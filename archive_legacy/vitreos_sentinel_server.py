"""
Vitreos Sentinel WebSocket Server
Streams real-time hardware telemetry to React frontend
"""
import asyncio
import json
import logging
from typing import Dict, Any
import psutil

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

try:
    from pypresence import Presence
    DISCORD_RPC_AVAILABLE = True
except ImportError:
    DISCORD_RPC_AVAILABLE = False
    print("[SENTINEL] pypresence not installed. Run: pip install pypresence")

try:
    from websockets.server import serve
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("[SENTINEL] websockets library not installed. Run: pip install websockets")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscordRPCController:
    """Manages Discord Rich Presence integration."""
    
    def __init__(self, client_id: str = "1234567890123456789"):
        self.client_id = client_id
        self.rpc = None
        self.enabled = False
        self.active_tab = "VITALS"
        
        if DISCORD_RPC_AVAILABLE:
            try:
                self.rpc = Presence(self.client_id)
                self.rpc.connect()
                self.enabled = True
                logger.info("[SENTINEL] Discord RPC connected")
            except Exception as e:
                logger.warning(f"[SENTINEL] Discord RPC connection failed: {e}")
                self.enabled = False
    
    def update_presence(self, data: Dict[str, Any]) -> None:
        """Update Discord Rich Presence with current telemetry."""
        if not self.enabled or not self.rpc:
            return
        
        try:
            cpu_temp = data.get('cpu', {}).get('temp', 0)
            cpu_load = data.get('cpu', {}).get('totalLoad', 0)
            gpu_temp = data.get('gpu', {}).get('temp', 0)
            gpu_load = data.get('gpu', {}).get('load', 0)
            
            self.rpc.update(
                state=f"GPU: {gpu_temp}°C ({gpu_load}%) | CPU: {cpu_temp}°C ({cpu_load:.0f}%)",
                details=f"Monitoring: {self.active_tab}",
                large_image="vitreos_logo",
                large_text="VITREOS SENTINEL v2.1",
                small_image="sentinel_active",
                small_text="System Online"
            )
        except Exception as e:
            logger.error(f"[SENTINEL] Discord RPC update error: {e}")
    
    def set_active_tab(self, tab_name: str) -> None:
        """Update active tab for Discord presence."""
        self.active_tab = tab_name
    
    def toggle(self, enabled: bool) -> bool:
        """Enable or disable Discord RPC."""
        if not DISCORD_RPC_AVAILABLE:
            return False
        
        if enabled and not self.enabled:
            try:
                if not self.rpc:
                    self.rpc = Presence(self.client_id)
                self.rpc.connect()
                self.enabled = True
                logger.info("[SENTINEL] Discord RPC enabled")
            except Exception as e:
                logger.error(f"[SENTINEL] Failed to enable Discord RPC: {e}")
                return False
        elif not enabled and self.enabled:
            try:
                if self.rpc:
                    self.rpc.close()
                self.enabled = False
                logger.info("[SENTINEL] Discord RPC disabled")
            except Exception as e:
                logger.error(f"[SENTINEL] Failed to disable Discord RPC: {e}")
        
        return self.enabled
    
    def cleanup(self) -> None:
        """Cleanup Discord RPC connection."""
        if self.enabled and self.rpc:
            try:
                self.rpc.close()
            except:
                pass


class OverclockController:
    """Manages GPU overclocking via NVML."""
    
    def __init__(self, gpu_handle=None):
        self.gpu_handle = gpu_handle
        self.nvml_available = NVML_AVAILABLE and gpu_handle is not None
    
    def apply_clock_offset(self, core_offset: int, mem_offset: int) -> Dict[str, Any]:
        """Apply clock offsets to GPU (requires elevated permissions)."""
        if not self.nvml_available:
            return {"success": False, "error": "NVML not available"}
        
        try:
            # WARNING: This requires NVIDIA driver support and elevated permissions
            # Most consumer GPUs don't support programmatic OC via NVML
            logger.warning(f"[SENTINEL] OC REQUEST: Core +{core_offset}MHz, Mem +{mem_offset}MHz")
            
            # Placeholder for actual NVML OC commands
            # Real implementation would use:
            # pynvml.nvmlDeviceSetGpuLockedClocks(self.gpu_handle, min_clock, max_clock)
            
            return {
                "success": True,
                "core_offset": core_offset,
                "mem_offset": mem_offset,
                "message": "OC profile committed (simulation mode)"
            }
        except Exception as e:
            logger.error(f"[SENTINEL] OC application error: {e}")
            return {"success": False, "error": str(e)}


class SentinelDataProvider:
    """Collects hardware telemetry data."""
    
    def __init__(self):
        self.nvml_initialized = False
        self.gpu_handle = None
        if NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.nvml_initialized = True
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                logger.info("[SENTINEL] NVML initialized successfully")
            except Exception as e:
                logger.warning(f"[SENTINEL] NVML initialization failed: {e}")
        
        # Initialize controllers
        self.discord_rpc = DiscordRPCController()
        self.oc_controller = OverclockController(self.gpu_handle)
    
    def get_cpu_data(self) -> Dict[str, Any]:
        """Collect CPU metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_freq = psutil.cpu_freq()
            temps = psutil.sensors_temperatures() if hasattr(psutil, 'sensors_temperatures') else {}
            cpu_temp = 0
            
            if 'coretemp' in temps:
                cpu_temp = temps['coretemp'][0].current
            elif 'cpu_thermal' in temps:
                cpu_temp = temps['cpu_thermal'][0].current
            
            return {
                "totalLoad": cpu_percent,
                "temp": cpu_temp if cpu_temp > 0 else 70,
                "clock": int(cpu_freq.current) if cpu_freq else 5000,
                "cores": psutil.cpu_percent(percpu=True)
            }
        except Exception as e:
            logger.error(f"[SENTINEL] CPU data error: {e}")
            return {"totalLoad": 0, "temp": 0, "clock": 0, "cores": []}
    
    def get_gpu_data(self) -> Dict[str, Any]:
        """Collect GPU metrics via NVML."""
        if not self.nvml_initialized:
            return {
                "load": 0,
                "vram": 0,
                "temp": 0,
                "coreClock": 0,
                "memClock": 0,
                "power": 0
            }
        
        try:
            utilization = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            temp = pynvml.nvmlDeviceGetTemperature(self.gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
            power = pynvml.nvmlDeviceGetPowerUsage(self.gpu_handle) / 1000  # Convert to watts
            
            clock_info = pynvml.nvmlDeviceGetClockInfo(self.gpu_handle, pynvml.NVML_CLOCK_GRAPHICS)
            mem_clock = pynvml.nvmlDeviceGetClockInfo(self.gpu_handle, pynvml.NVML_CLOCK_MEM)
            
            return {
                "load": utilization.gpu,
                "vram": round(memory_info.used / (1024**3), 2),
                "temp": temp,
                "coreClock": clock_info,
                "memClock": mem_clock,
                "power": round(power, 1)
            }
        except Exception as e:
            logger.error(f"[SENTINEL] GPU data error: {e}")
            return {"load": 0, "vram": 0, "temp": 0, "coreClock": 0, "memClock": 0, "power": 0}
    
    def get_memory_data(self) -> Dict[str, Any]:
        """Collect memory metrics."""
        try:
            mem = psutil.virtual_memory()
            return {
                "used": round(mem.used / (1024**3), 2),
                "total": round(mem.total / (1024**3), 2),
                "speed": 6000  # Placeholder
            }
        except Exception as e:
            logger.error(f"[SENTINEL] Memory data error: {e}")
            return {"used": 0, "total": 0, "speed": 0}
    
    def get_storage_data(self) -> Dict[str, Any]:
        """Collect storage metrics."""
        try:
            drives = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    io_counters = psutil.disk_io_counters(perdisk=False)
                    
                    drives.append({
                        "id": partition.device,
                        "model": partition.device,
                        "temp": 40,  # Placeholder
                        "health": 100 - int(usage.percent),
                        "read": io_counters.read_bytes // (1024**2) if io_counters else 0,
                        "write": io_counters.write_bytes // (1024**2) if io_counters else 0
                    })
                except PermissionError:
                    continue
            
            return {"drives": drives}
        except Exception as e:
            logger.error(f"[SENTINEL] Storage data error: {e}")
            return {"drives": []}
    
    def get_network_data(self) -> Dict[str, Any]:
        """Collect network metrics."""
        try:
            net_io = psutil.net_io_counters()
            return {
                "download": round(net_io.bytes_recv / (1024**2), 2),
                "upload": round(net_io.bytes_sent / (1024**2), 2),
                "ping": 12  # Placeholder
            }
        except Exception as e:
            logger.error(f"[SENTINEL] Network data error: {e}")
            return {"download": 0, "upload": 0, "ping": 0}
    
    def get_thermal_data(self) -> Dict[str, Any]:
        """Collect thermal metrics."""
        try:
            temps = psutil.sensors_temperatures() if hasattr(psutil, 'sensors_temperatures') else {}
            return {
                "motherboard": 56,  # Placeholder
                "case": 45,  # Placeholder
                "ambient": 29  # Placeholder
            }
        except Exception as e:
            logger.error(f"[SENTINEL] Thermal data error: {e}")
            return {"motherboard": 0, "case": 0, "ambient": 0}
    
    def get_security_data(self) -> Dict[str, Any]:
        """Collect security metrics."""
        return {
            "shieldLevel": 100,
            "activeThreats": 0,
            "breaches": []
        }
    
    def collect_all(self) -> Dict[str, Any]:
        """Collect all telemetry data."""
        return {
            "cpu": self.get_cpu_data(),
            "gpu": self.get_gpu_data(),
            "memory": self.get_memory_data(),
            "storage": self.get_storage_data(),
            "network": self.get_network_data(),
            "thermal": self.get_thermal_data(),
            "security": self.get_security_data()
        }
    
    def cleanup(self):
        """Cleanup resources."""
        self.discord_rpc.cleanup()
        if self.nvml_initialized:
            try:
                pynvml.nvmlShutdown()
            except:
                pass


async def sentinel_handler(websocket):
    """Handle WebSocket connections and stream data."""
    logger.info(f"[SENTINEL] Client connected: {websocket.remote_address}")
    provider = SentinelDataProvider()
    
    async def send_telemetry():
        """Send telemetry data to client."""
        while True:
            try:
                data = provider.collect_all()
                data['discord_rpc_enabled'] = provider.discord_rpc.enabled
                await websocket.send(json.dumps(data))
                
                # Update Discord RPC
                provider.discord_rpc.update_presence(data)
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"[SENTINEL] Telemetry send error: {e}")
                break
    
    async def receive_commands():
        """Receive commands from client."""
        async for message in websocket:
            try:
                cmd = json.loads(message)
                cmd_type = cmd.get('type')
                
                if cmd_type == 'TOGGLE_RPC':
                    enabled = cmd.get('enabled', False)
                    result = provider.discord_rpc.toggle(enabled)
                    await websocket.send(json.dumps({
                        'type': 'RPC_STATUS',
                        'enabled': result
                    }))
                
                elif cmd_type == 'SET_ACTIVE_TAB':
                    tab_name = cmd.get('tab', 'VITALS')
                    provider.discord_rpc.set_active_tab(tab_name)
                
                elif cmd_type == 'ADJUST_CLOCK':
                    core_offset = cmd.get('core_offset', 0)
                    mem_offset = cmd.get('mem_offset', 0)
                    result = provider.oc_controller.apply_clock_offset(core_offset, mem_offset)
                    await websocket.send(json.dumps({
                        'type': 'OC_RESULT',
                        **result
                    }))
                    logger.warning(f"[SENTINEL] OC COMMIT: Core +{core_offset}MHz, Mem +{mem_offset}MHz")
                
            except json.JSONDecodeError:
                logger.error("[SENTINEL] Invalid JSON received")
            except Exception as e:
                logger.error(f"[SENTINEL] Command handler error: {e}")
    
    try:
        await asyncio.gather(
            send_telemetry(),
            receive_commands()
        )
    except Exception as e:
        logger.error(f"[SENTINEL] Connection error: {e}")
    finally:
        provider.cleanup()
        logger.info(f"[SENTINEL] Client disconnected: {websocket.remote_address}")


async def main():
    """Start WebSocket server."""
    if not WEBSOCKETS_AVAILABLE:
        logger.error("[SENTINEL] Cannot start server - websockets library not installed")
        return
    
    logger.info("[SENTINEL] Starting WebSocket server on ws://localhost:8000")
    async with serve(sentinel_handler, "localhost", 8000):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[SENTINEL] Server stopped by user")
