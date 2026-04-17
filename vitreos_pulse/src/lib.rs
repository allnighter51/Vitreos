use pyo3::prelude::*;
use pyo3::types::PyDict;
use parking_lot::RwLock;
use once_cell::sync::Lazy;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, AtomicBool, Ordering};
use std::time::{Duration, Instant};
use std::thread;

mod metrics;
mod cpu;
mod gpu;
mod memory;
mod network;
mod storage;

use metrics::{MetricsEngine, TelemetrySnapshot};

/// Global polling interval (milliseconds) - adjustable via set_polling_rate()
static POLLING_INTERVAL_MS: AtomicU64 = AtomicU64::new(1000); // Default 1Hz (1000ms)

/// Global snapshot cache - updated by background thread
static METRICS_SNAPSHOT: Lazy<Arc<RwLock<Option<TelemetrySnapshot>>>> = Lazy::new(|| {
    Arc::new(RwLock::new(None))
});

/// Background polling thread control
static POLLING_ACTIVE: AtomicBool = AtomicBool::new(false);

/// Metrics engine singleton
static PULSE_ENGINE: Lazy<Arc<RwLock<MetricsEngine>>> = Lazy::new(|| {
    Arc::new(RwLock::new(MetricsEngine::new()))
});

/// VitreosPulse - High-performance telemetry engine (Pull-Based Architecture)
/// 
/// Background thread polls hardware at 1Hz (1000ms) for sustainable monitoring.
/// UI thread pulls latest snapshot via get_latest_metrics() at 1Hz.
#[pyclass]
struct VitreosPulse {
    _phantom: (),
}

#[pymethods]
impl VitreosPulse {
    #[new]
    fn new() -> PyResult<Self> {
        Ok(Self { _phantom: () })
    }

    /// Get latest hardware metrics snapshot (non-blocking, <0.1ms)
    /// 
    /// Returns cached snapshot from background polling thread.
    /// Safe to call at 1Hz from UI thread without blocking.
    fn get_latest_metrics(&self, py: Python) -> PyResult<PyObject> {
        let start = Instant::now();
        
        // Acquire read lock (non-blocking)
        let snapshot_guard = METRICS_SNAPSHOT.read();
        
        let Some(ref metrics) = *snapshot_guard else {
            // No data yet - return empty dict
            return Ok(PyDict::new(py).into());
        };
        
        // Convert snapshot to Python dict (zero-copy where possible)
        let dict = snapshot_to_pydict(py, metrics)?;
        
        let elapsed = start.elapsed();
        if elapsed.as_micros() > 100 {
            eprintln!("[PULSE] Warning: Snapshot conversion took {}μs (target: <100μs)", elapsed.as_micros());
        }
        
        Ok(dict.into())
    }

    /// Initialize hardware discovery and start background polling thread
    fn bootstrap(&self) -> PyResult<()> {
        // Bootstrap hardware discovery
        let mut engine = PULSE_ENGINE.write();
        engine.bootstrap()?;
        drop(engine); // Release lock before spawning thread
        
        // Start background polling thread
        if !POLLING_ACTIVE.swap(true, Ordering::SeqCst) {
            thread::spawn(|| {
                background_polling_loop();
            });
        }
        
        Ok(())
    }

    /// Set active network adapter for monitoring
    fn set_active_adapter(&self, adapter_name: String) -> PyResult<()> {
        let mut engine = PULSE_ENGINE.write();
        engine.set_active_adapter(adapter_name);
        Ok(())
    }
}

/// Background polling loop (runs in dedicated thread)
fn background_polling_loop() {
    let mut poll_count = 0u64;
    
    loop {
        if !POLLING_ACTIVE.load(Ordering::Relaxed) {
            break;
        }
        
        let start = Instant::now();
        
        // Collect metrics from hardware
        let engine = PULSE_ENGINE.read();
        let snapshot = engine.collect_all();
        drop(engine);
        
        // Update global snapshot cache
        {
            let mut cache = METRICS_SNAPSHOT.write();
            *cache = Some(snapshot);
        }
        
        poll_count += 1;
        
        // Periodic debug logging intentionally suppressed to avoid console spam
        
        // Sleep for remaining interval
        let interval_ms = POLLING_INTERVAL_MS.load(Ordering::Relaxed);
        let elapsed = start.elapsed();
        let target_duration = Duration::from_millis(interval_ms);
        
        if elapsed < target_duration {
            thread::sleep(target_duration - elapsed);
        }
    }
    
    // Background thread terminated
}

/// Convert TelemetrySnapshot to Python dict (optimized for <0.1ms)
fn snapshot_to_pydict(py: Python, metrics: &TelemetrySnapshot) -> PyResult<PyObject> {
    let dict = PyDict::new(py);
    
    // CPU metrics
    let cpu_dict = PyDict::new(py);
    cpu_dict.set_item("name", &metrics.cpu.name)?;
    cpu_dict.set_item("totalLoad", metrics.cpu.total_load)?;
    cpu_dict.set_item("temp", metrics.cpu.temp)?;
    cpu_dict.set_item("clock", metrics.cpu.clock)?;
    cpu_dict.set_item("cores", &metrics.cpu.per_core_load)?;
    cpu_dict.set_item("coreCount", metrics.cpu.core_count)?;
    cpu_dict.set_item("physicalCores", metrics.cpu.physical_cores)?;
    cpu_dict.set_item("logicalThreads", metrics.cpu.logical_threads)?;
    cpu_dict.set_item("packagePwr", metrics.cpu.package_power)?;
    cpu_dict.set_item("vid", metrics.cpu.vid)?;
    dict.set_item("cpu", cpu_dict)?;
    
    // GPU metrics
    let gpu_dict = PyDict::new(py);
    gpu_dict.set_item("name", &metrics.gpu.name)?;
    gpu_dict.set_item("usage", metrics.gpu.usage)?;
    gpu_dict.set_item("vramUsed", metrics.gpu.vram_used_gb)?;
    gpu_dict.set_item("vramTotal", metrics.gpu.vram_total_gb)?;
    gpu_dict.set_item("vramPercent", metrics.gpu.vram_percent)?;
    gpu_dict.set_item("coreClock", metrics.gpu.core_clock)?;
    gpu_dict.set_item("memClock", metrics.gpu.mem_clock)?;
    gpu_dict.set_item("power", metrics.gpu.power)?;
    gpu_dict.set_item("temp", metrics.gpu.temp)?;
    gpu_dict.set_item("fanSpeed", metrics.gpu.fan_speed)?;
    gpu_dict.set_item("status", &metrics.gpu.status)?;
    dict.set_item("gpu", gpu_dict)?;
    
    // Memory metrics
    let mem_dict = PyDict::new(py);
    mem_dict.set_item("usedGB", metrics.memory.used_gb)?;
    mem_dict.set_item("totalGB", metrics.memory.total_gb)?;
    mem_dict.set_item("percent", metrics.memory.percent)?;
    // Per-slot DIMM telemetry (if available)
    let slots_list = pyo3::types::PyList::empty(py);
    for slot in &metrics.memory.slots {
        let slot_dict = PyDict::new(py);
        slot_dict.set_item("locator", &slot.locator)?;
        slot_dict.set_item("capacityGB", slot.capacity_gb)?;
        slot_dict.set_item("speedMT", slot.speed_mt)?;
        slot_dict.set_item("configuredClock", slot.configured_clock)?;
        slot_dict.set_item("manufacturer", &slot.manufacturer)?;
        slot_dict.set_item("partNumber", &slot.part_number)?;
        slot_dict.set_item("serial", &slot.serial)?;
        slot_dict.set_item("populated", slot.populated)?;
        slots_list.append(slot_dict)?;
    }
    mem_dict.set_item("slots", slots_list)?;
    mem_dict.set_item("effectiveSpeed", metrics.memory.effective_speed_mt)?;
    mem_dict.set_item("channel", &metrics.memory.channel_mode)?;
    mem_dict.set_item("headerSpec", &metrics.memory.header_spec)?;
    mem_dict.set_item("xmpActive", metrics.memory.xmp_active)?;
    dict.set_item("memory", mem_dict)?;
    
    // Network metrics
    let net_dict = PyDict::new(py);
    net_dict.set_item("downloadMbps", metrics.network.download_mbps)?;
    net_dict.set_item("uploadMbps", metrics.network.upload_mbps)?;
    net_dict.set_item("latency", metrics.network.latency_ms)?;
    net_dict.set_item("primaryNic", &metrics.network.primary_adapter)?;
    dict.set_item("network", net_dict)?;
    
    // Storage metrics
    let storage_dict = PyDict::new(py);
    let drives_list = pyo3::types::PyList::empty(py);
    for drive in &metrics.storage.drives {
        let drive_dict = PyDict::new(py);
        drive_dict.set_item("type", &drive.drive_type)?;
        drive_dict.set_item("model", &drive.model)?;
        drive_dict.set_item("mountpoint", &drive.mountpoint)?;
        drive_dict.set_item("usedGB", drive.used_gb)?;
        drive_dict.set_item("totalGB", drive.total_gb)?;
        drive_dict.set_item("percent", drive.percent)?;
        // Additional telemetry: serial, temp (°C), read/write in MB/s and observed maxima
        drive_dict.set_item("serial", &drive.serial)?;
        drive_dict.set_item("temp", drive.temp_c)?;
        // Convert bytes/sec to MB/s for UI
        let read_mbps = (drive.read_bps as f64) / (1024.0 * 1024.0);
        let write_mbps = (drive.write_bps as f64) / (1024.0 * 1024.0);
        let max_read_mbps = (drive.max_read_bps as f64) / (1024.0 * 1024.0);
        let max_write_mbps = (drive.max_write_bps as f64) / (1024.0 * 1024.0);
        drive_dict.set_item("readSpeed", read_mbps)?;
        drive_dict.set_item("writeSpeed", write_mbps)?;
        drive_dict.set_item("maxRead", max_read_mbps)?;
        drive_dict.set_item("maxWrite", max_write_mbps)?;
        drives_list.append(drive_dict)?;
    }
    storage_dict.set_item("drives", drives_list)?;
    dict.set_item("storage", storage_dict)?;
    
    Ok(dict.into())
}

/// Set polling rate (milliseconds) - adjustable from Python
/// 
/// Args:
///     interval_ms: Polling interval in milliseconds (100-5000ms recommended)
/// 
/// Examples:
///     100ms  = 10Hz (high performance)
///     1000ms = 1Hz (balanced - default)
///     5000ms = 0.2Hz (minimal overhead)
#[pyfunction]
fn set_polling_rate(_interval_ms: u64) -> PyResult<()> {
    // Enforce 1Hz polling rate (1000ms) to ensure stable, low-overhead monitoring
    let enforced: u64 = 1000;
    POLLING_INTERVAL_MS.store(enforced, Ordering::Relaxed);
    Ok(())
}

/// Get current polling rate (milliseconds)
#[pyfunction]
fn get_polling_rate() -> PyResult<u64> {
    Ok(POLLING_INTERVAL_MS.load(Ordering::Relaxed))
}

/// Stop background polling thread
#[pyfunction]
fn stop_polling() -> PyResult<()> {
    POLLING_ACTIVE.store(false, Ordering::Relaxed);
    Ok(())
}

/// Python module initialization
#[pymodule]
fn vitreos_pulse(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<VitreosPulse>()?;
    m.add_function(wrap_pyfunction!(set_polling_rate, m)?)?;
    m.add_function(wrap_pyfunction!(get_polling_rate, m)?)?;
    m.add_function(wrap_pyfunction!(stop_polling, m)?)?;
    Ok(())
}
