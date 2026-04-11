"""
Vitreos Pulse - Pull-Based Telemetry with 1Hz Log Throttling
Decouples hardware polling from UI updates and log rendering

Architecture:
- Rust: Background thread polls hardware at variable rate (8-100ms)
- Python UI: QTimer pulls latest snapshot at 60Hz (16.6ms) for gauges
- Python Logs: QTimer flushes buffered logs at 1Hz (1000ms) for text rendering
"""

from typing import Dict, Any, Optional
from collections import deque
from datetime import datetime
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

from src.core.vitreos_logger import v_debug, v_info, v_error

try:
    import vitreos_pulse
    PULSE_AVAILABLE = True
except ImportError:
    PULSE_AVAILABLE = False
    v_error("vitreos_pulse not available - falling back to Python telemetry")


class PullBasedTelemetry(QObject):
    """
    Pull-based telemetry manager with 1Hz throttled log buffer.
    
    Update Strategy:
    - Hardware Polling (Rust): Variable 8-100ms (slider-controlled)
    - UI Gauges (Python): Fixed 60Hz (16.6ms) for smooth rendering
    - Log Dispatch (Python): Throttled 1Hz (1000ms) batch flush
    
    The log buffer acts as a "Collector" that accumulates events at high speed,
    then a "Dispatcher" that flushes them to the UI in batches at 1Hz.
    """
    
    # Signals
    data_ready = pyqtSignal(dict)  # Fires at 60Hz for gauges/graphs
    log_ready = pyqtSignal(str)    # Fires at 1Hz for SYSTEM_PULSE (batched)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        if not PULSE_AVAILABLE:
            raise RuntimeError("vitreos_pulse module not available")
        
        # Initialize Rust engine
        self.pulse = vitreos_pulse.VitreosPulse()
        
        # QTimer for UI updates (synchronized with hardware polling)
        self.ui_timer = QTimer()
        # Default to Rust polling rate where possible (fallback to 16ms / ~60Hz)
        try:
            polling_ms = int(vitreos_pulse.get_polling_rate())
        except Exception:
            polling_ms = 16
        self.ui_timer.setInterval(polling_ms)
        self.ui_timer.timeout.connect(self._pull_metrics)
        
        # QTimer for log flush (5000ms = 5 seconds)
        self.log_flush_timer = QTimer()
        self.log_flush_timer.setInterval(5000)  # 5000ms = 5 seconds (Deep Freeze)
        self.log_flush_timer.timeout.connect(self._flush_logs_to_ui)
        
        # Log buffer (deque with max 100 lines to prevent memory bloat)
        self.log_buffer = deque(maxlen=100)
        
        # Performance tracking
        self.update_counter = 0
        self.last_debug_time = datetime.now()
        
        # Significant event tracking (for log filtering)
        self._last_cpu_load = 0
        self._last_gpu_load = 0
        self._last_cpu_temp = 0
        self._last_gpu_temp = 0
        self._network_peak = 0
        
        v_info("Pull-based telemetry initialized (Synced UI / 5s logs)")
    
    def start(self) -> None:
        """Start telemetry system (bootstrap + timers)"""
        try:
            # Bootstrap hardware discovery (blocking, one-time)
            self.pulse.bootstrap()
            self._buffer_log("OK", "Hardware discovery complete", "green")
            
            # Start UI update timer (60Hz)
            self.ui_timer.start()
            
            # Start log flush timer (1Hz)
            self.log_flush_timer.start()
            
            self._buffer_log("SYS", "Telemetry active (Synced UI / Variable HW / 5s logs)", "primary_purple")
            
            v_info("Telemetry started - UI: Synced, Logs: 5s")
        except Exception as e:
            v_error(f"Bootstrap failed: {e}")
            self.error_occurred.emit(f"Bootstrap failed: {e}")
    
    def stop(self) -> None:
        """Stop telemetry system"""
        self.ui_timer.stop()
        self.log_flush_timer.stop()
        vitreos_pulse.stop_polling()
        self._buffer_log("SYS", "Telemetry stopped", "text_dim")
        self._flush_logs_to_ui()
        v_info("Telemetry stopped")
    
    def _pull_metrics(self) -> None:
        """
        Pull latest metrics from Rust cache (called at synchronized rate by QTimer).
        This runs at the same rate as hardware polling for maximum efficiency.
        """
        try:
            # Pull cached snapshot from Rust (non-blocking, <0.1ms)
            data = self.pulse.get_latest_metrics()
            
            # Emit to UI gauges/graphs (only if data is available)
            if data:
                # Diagnostic: print first few CPU payloads to help verify backend
                if self.update_counter < 5:
                    try:
                        cpu = data.get('cpu', {})
                        total = cpu.get('totalLoad')
                        temp = cpu.get('temp')
                        cores = cpu.get('cores', [])
                        core_count = cpu.get('coreCount')
                        phys = cpu.get('physicalCores')
                        logical = cpu.get('logicalThreads')
                        print(f"[TELEMETRY DEBUG] CPU payload: totalLoad={total} temp={temp} cores_len={len(cores)} coreCount={core_count} physicalCores={phys} logicalThreads={logical}")
                    except Exception:
                        print("[TELEMETRY DEBUG] CPU payload:", data.get('cpu'))

                self.data_ready.emit(data)

                # Check for significant events and buffer logs (zero UI cost)
                self._check_significant_events(data)
            
            self.update_counter += 1
        
        except Exception as e:
            v_error(f"Metrics pull error: {e}")
            self.error_occurred.emit(f"Metrics pull error: {e}")
    
    def _check_significant_events(self, data: Dict[str, Any]) -> None:
        """
        Check for significant hardware events and buffer logs.
        This runs at synchronized rate but logs are NOT emitted yet (zero UI cost).
        Logs are accumulated in the buffer and flushed at 5-second intervals.
        """
        cpu_load = data.get('cpu', {}).get('totalLoad', 0)
        gpu_load = data.get('gpu', {}).get('usage', 0)
        cpu_temp = data.get('cpu', {}).get('temp', 0)
        gpu_temp = data.get('gpu', {}).get('temp', 0)
        download_mbps = data.get('network', {}).get('downloadMbps', 0)
        
        # Event 1: CPU Load Spike (>25% change)
        if abs(cpu_load - self._last_cpu_load) > 25:
            self._buffer_log("CPU", f"Load spike: {self._last_cpu_load:.0f}% → {cpu_load:.0f}%", "warning_orange")
            self._last_cpu_load = cpu_load
        
        # Event 2: GPU Load Spike (>25% change)
        if abs(gpu_load - self._last_gpu_load) > 25:
            self._buffer_log("GPU", f"Load spike: {self._last_gpu_load:.0f}% → {gpu_load:.0f}%", "warning_orange")
            self._last_gpu_load = gpu_load
        
        # Event 3: CPU Temperature Threshold (>5°C change)
        if abs(cpu_temp - self._last_cpu_temp) > 5:
            color = "critical_red" if cpu_temp > 85 else "warning_orange" if cpu_temp > 75 else "cyan"
            self._buffer_log("CPU", f"Temp change: {self._last_cpu_temp:.0f}°C → {cpu_temp:.0f}°C", color)
            self._last_cpu_temp = cpu_temp
        
        # Event 4: GPU Temperature Threshold (>5°C change)
        if abs(gpu_temp - self._last_gpu_temp) > 5:
            color = "critical_red" if gpu_temp > 85 else "warning_orange" if gpu_temp > 75 else "warning_orange"
            self._buffer_log("GPU", f"Temp change: {self._last_gpu_temp:.0f}°C → {gpu_temp:.0f}°C", color)
            self._last_gpu_temp = gpu_temp
        
        # Event 5: Network Peak Reached
        if download_mbps > self._network_peak:
            self._network_peak = download_mbps
            self._buffer_log("NET", f"New peak: {download_mbps:.1f} Mbps", "green")
    
    def _buffer_log(self, level: str, message: str, color: str) -> None:
        """
        Buffer a log message (zero UI cost).
        Logs are accumulated in a deque and flushed at 5-second intervals.
        
        Format: [HH:MM:SS] [LEVEL] message
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        
        # Store as tuple for color information
        self.log_buffer.append((log_line, color))
    
    def _flush_logs_to_ui(self) -> None:
        """
        The 5-second Dispatcher - Flushes the entire buffer in one batch.
        This minimizes Qt's setText/append calls and prevents UI lag.
        """
        if not self.log_buffer:
            return
        
        # Build batch string with color metadata
        # Format: "color1|line1\ncolor2|line2\n..."
        batch_lines = []
        for log_line, color in self.log_buffer:
            batch_lines.append(f"{color}|{log_line}")
        
        combined_logs = "\n".join(batch_lines)
        
        self.log_ready.emit(combined_logs)
        
        v_debug(f"Flushed {len(self.log_buffer)} log entries to UI")
        self.log_buffer.clear()
    
    def set_polling_rate(self, interval_ms: int) -> None:
        """
        Set hardware polling rate and synchronize UI timer.
        
        Args:
            interval_ms: Polling interval in milliseconds (100-5000ms)
                100ms  = 10 FPS (high performance)
                1000ms = 1 FPS (balanced)
                5000ms = 0.2 FPS (minimal overhead)
        """
        try:
            vitreos_pulse.set_polling_rate(interval_ms)
            fps = 1000.0 / interval_ms
            self._buffer_log("SYS", f"Hardware polling: {interval_ms}ms ({fps:.1f} FPS)", "cyan")
            v_info(f"Polling rate set to {interval_ms}ms ({fps:.1f} FPS)")
        except Exception as e:
            v_error(f"Failed to set polling rate: {e}")
            self.error_occurred.emit(f"Failed to set polling rate: {e}")
    
    def set_ui_refresh_rate(self, interval_ms: int) -> None:
        """
        Set UI refresh rate (synchronized with hardware polling).
        
        Args:
            interval_ms: UI refresh interval in milliseconds (100-5000ms)
        """
        try:
            self.ui_timer.setInterval(interval_ms)
            fps = 1000.0 / interval_ms
            self._buffer_log("SYS", f"UI refresh: {interval_ms}ms ({fps:.1f} FPS)", "cyan")
            v_info(f"UI refresh rate set to {interval_ms}ms ({fps:.1f} FPS)")
        except Exception as e:
            v_error(f"Failed to set UI refresh rate: {e}")
            self.error_occurred.emit(f"Failed to set UI refresh rate: {e}")
    
    def get_polling_rate(self) -> int:
        """Get current hardware polling rate (milliseconds)"""
        try:
            return vitreos_pulse.get_polling_rate()
        except:
            return 1000  # Default fallback
    
    def set_active_adapter(self, adapter_name: str) -> None:
        """Set active network adapter for monitoring"""
        try:
            self.pulse.set_active_adapter(adapter_name)
            self._buffer_log("NET", f"Adapter: {adapter_name}", "cyan")
            v_info(f"Network adapter set to {adapter_name}")
        except Exception as e:
            v_error(f"Failed to set adapter: {e}")
            self.error_occurred.emit(f"Failed to set adapter: {e}")


__all__ = ['PullBasedTelemetry', 'PULSE_AVAILABLE']
