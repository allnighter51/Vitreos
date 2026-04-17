"""
Vitreos Pulse - Rust Telemetry Bridge
High-performance hardware monitoring via Rust extension module

Performance: 125Hz polling (8ms intervals) with <1ms execution time
"""

from typing import Dict, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal
import time
from src.core.vitreos_logger import v_debug, v_info, v_error

try:
    import vitreos_pulse
    PULSE_AVAILABLE = True
except ImportError:
    PULSE_AVAILABLE = False
    v_info("vitreos_pulse not available - falling back to Python telemetry")


class RustTelemetryWorker(QThread):
    """
    QThread wrapper for Rust telemetry engine.
    Supports 125Hz polling without blocking Python GIL.
    """
    
    data_ready = pyqtSignal(dict)
    log_message = pyqtSignal(str, str, str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        self.running = False
        self.pulse = None
        # Enforce 1Hz polling for Rust worker to match system-wide policy
        self.poll_interval = 1.0  # 1s = 1Hz
        self.debug_counter = 0
        
        if not PULSE_AVAILABLE:
            raise RuntimeError("vitreos_pulse module not available")
        
        # Initialize Rust engine
        self.pulse = vitreos_pulse.VitreosPulse()
        
        v_info("Rust telemetry engine initialized")
    
    def run(self) -> None:
        """Main telemetry loop - runs in background thread."""
        self.running = True
        self.log_message.emit("SYS", "Rust telemetry worker started (125Hz mode)", "primary_purple")
        
        # Bootstrap hardware discovery (blocking, one-time)
        try:
            self.pulse.bootstrap()
            self.log_message.emit("OK", "Hardware discovery complete", "green")
        except Exception as e:
            self.error_occurred.emit(f"Bootstrap failed: {e}")
            return
        
        while self.running:
            try:
                start_time = time.perf_counter()
                
                # Collect all metrics from Rust (non-blocking)
                data = self.pulse.get_metrics()
                
                # Debug logging every 3 seconds
                self.debug_counter += 1
                # Periodic debug logging suppressed to avoid console spam
                
                # Emit to main thread
                self.data_ready.emit(data)
                
                # Sleep for remaining time to maintain 125Hz
                elapsed = time.perf_counter() - start_time
                sleep_time = max(0, self.poll_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    # Warn if we're falling behind
                    if self.debug_counter % 125 == 0:  # Every second
                        v_debug(f"Poll warning: took {elapsed*1000:.2f}ms (target: {self.poll_interval*1000:.2f}ms)")
            
            except Exception as e:
                self.error_occurred.emit(f"Telemetry error: {e}")
                time.sleep(0.1)
    
    def stop(self) -> None:
        """Stop the telemetry worker gracefully."""
        self.running = False
        self.log_message.emit("SYS", "Rust telemetry worker stopping...", "text_dim")
    
    def set_active_adapter(self, adapter_name: str) -> None:
        """Set the active network adapter for monitoring."""
        if self.pulse:
            self.pulse.set_active_adapter(adapter_name)
            self.log_message.emit("NET", f"Adapter switched to: {adapter_name}", "cyan")


__all__ = ['RustTelemetryWorker', 'PULSE_AVAILABLE']
