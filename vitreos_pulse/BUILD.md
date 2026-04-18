# 🦀 Vitreos Pulse | Build Instructions

## Prerequisites

### 1. Install Rust Toolchain
```bash
# Download and install rustup (Rust installer)
# Visit: https://rustup.rs/
# Or run:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify installation
rustc --version
cargo --version
```

### 2. Install Maturin
```bash
pip install maturin
```

### 3. Install NVIDIA CUDA Toolkit (for GPU monitoring)
- Download from: https://developer.nvidia.com/cuda-downloads
- Required for `nvml-wrapper` crate
- Ensure `nvml.dll` is in system PATH

---

## Build Process

### Development Build (Debug)
```bash
cd vitreos_pulse
maturin develop
```

### Production Build (Release - Optimized)
```bash
cd vitreos_pulse
maturin develop --release
```

### Build Wheel for Distribution
```bash
cd vitreos_pulse
maturin build --release
```

---

## Verification

### Run Benchmark Suite
```bash
python test_pulse.py
```

**Expected Output:**
```
✓ BENCHMARK PASSED
  Mean execution: 0.450ms (target: <1ms)
  Sustained rate: 125.3Hz (target: 125Hz)
```

### Quick Test
```python
import vitreos_pulse

pulse = vitreos_pulse.VitreosPulse()
pulse.bootstrap()

data = pulse.get_metrics()
print(f"CPU: {data['cpu']['name']}")
print(f"GPU: {data['gpu']['name']}")
print(f"RAM: {data['memory']['usedGB']:.1f} / {data['memory']['totalGB']:.1f} GB")
```

---

## Integration with Vitreos

### Replace Python Telemetry Worker

**Before (Python):**
```python
from src.core.vitreos_telemetry import TelemetryWorker

self.telemetry_worker = TelemetryWorker()
self.telemetry_worker.start()
```

**After (Rust):**
```python
from src.core.vitreos_telemetry_rust import RustTelemetryWorker, PULSE_AVAILABLE

if PULSE_AVAILABLE:
    self.telemetry_worker = RustTelemetryWorker()
    self.telemetry_worker.start()
else:
    # Fallback to Python implementation
    from src.core.vitreos_telemetry import TelemetryWorker
    self.telemetry_worker = TelemetryWorker()
    self.telemetry_worker.start()
```

---

## Performance Comparison

| Metric | Python (psutil) | Rust (vitreos_pulse) | Improvement |
|--------|----------------|---------------------|-------------|
| Poll Frequency | 1 Hz (1000ms) | 125 Hz (8ms) | **125x faster** |
| Execution Time | ~18ms | <1ms | **18x faster** |
| GIL Blocking | Yes | No | **Non-blocking** |
| CPU Overhead | ~2-3% | <0.5% | **6x lower** |

---

## Troubleshooting

### Error: `nvml-wrapper` build fails
**Solution:** Install NVIDIA CUDA Toolkit and ensure `nvml.dll` is in PATH

### Error: `maturin: command not found`
**Solution:** `pip install maturin`

### Error: `rustc: command not found`
**Solution:** Install Rust toolchain from https://rustup.rs/

### Warning: Poll took >1ms
**Cause:** System under heavy load or thermal throttling
**Solution:** Close background applications or check CPU/GPU temperatures

---

## Architecture Notes

### Zero-Allocation Hot Loop
- Pre-allocated buffers in `MetricsEngine`
- No heap allocations during polling
- Stack-only data structures

### Thread Safety
- `parking_lot::RwLock` for lock-free reads
- `Arc<Mutex<System>>` for sysinfo state
- Python GIL released during Rust execution

### Windows Optimizations
- Direct Windows API calls via `windows` crate
- NVML native bindings (no Python overhead)
- LTO (Link-Time Optimization) enabled

---

## Future Enhancements

1. **Network Latency:** Add ICMP ping via `pnet` crate
2. **CPU Temperature:** Windows WMI integration
3. **Process Monitoring:** Per-process CPU/RAM tracking
4. **Disk I/O:** Real-time read/write speeds
5. **Fan Control:** Direct PWM control via `librehardwaremonitor`

---

**Built for absolute system transparency.**
**v1.0.0 — Rust Edition**
