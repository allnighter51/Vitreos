"""
Vitreos Pulse - Rust Telemetry Bridge
High-performance hardware monitoring via Rust extension module

Performance: 125Hz polling (8ms intervals) with <1ms execution time
"""

from typing import Dict, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal
import time

try:
    import vitreos_pulse
    PULSE_AVAILABLE = True
except ImportError:
    PULSE_AVAILABLE = False
    print("[VITREOS] vitreos_pulse not available - falling back to Python telemetry")


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
        self.poll_interval = 0.008  # 8ms = 125Hz
        self.debug_counter = 0
        
        if not PULSE_AVAILABLE:
            raise RuntimeError("vitreos_pulse module not available")
        
        # Initialize Rust engine
        self.pulse = vitreos_pulse.VitreosPulse()
        
        print("[VITREOS] Rust telemetry engine initialized")
    
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
                if self.debug_counter % 375 == 0:  # 375 polls = 3 seconds at 125Hz
                    cpu_load = data.get('cpu', {}).get('totalLoad', 0)
                    gpu_temp = data.get('gpu', {}).get('temp', 0)
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    print(f"[PULSE] Poll #{self.debug_counter}: CPU {cpu_load:.0f}% | GPU {gpu_temp:.0f}°C | {elapsed_ms:.2f}ms")
                
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
                        print(f"[PULSE] Warning: Poll took {elapsed*1000:.2f}ms (target: {self.poll_interval*1000:.2f}ms)")
            
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
