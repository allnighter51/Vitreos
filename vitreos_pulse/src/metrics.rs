use pyo3::PyResult;
use std::collections::HashMap;

use crate::cpu::{CpuMetrics, CpuMonitor};
use crate::gpu::{GpuMetrics, GpuMonitor};
use crate::memory::{MemoryMetrics, MemoryMonitor};
use crate::network::{NetworkMetrics, NetworkMonitor};
use crate::storage::{StorageMetrics, StorageMonitor};

/// Complete telemetry snapshot
pub struct TelemetrySnapshot {
    pub cpu: CpuMetrics,
    pub gpu: GpuMetrics,
    pub memory: MemoryMetrics,
    pub network: NetworkMetrics,
    pub storage: StorageMetrics,
}

/// Core metrics engine with pre-allocated buffers
pub struct MetricsEngine {
    cpu_monitor: CpuMonitor,
    gpu_monitor: GpuMonitor,
    memory_monitor: MemoryMonitor,
    network_monitor: NetworkMonitor,
    storage_monitor: StorageMonitor,
    
    // Pre-allocated buffers to avoid allocations in hot loop
    cpu_buffer: CpuMetrics,
    gpu_buffer: GpuMetrics,
    memory_buffer: MemoryMetrics,
    network_buffer: NetworkMetrics,
    storage_buffer: StorageMetrics,
}

impl MetricsEngine {
    pub fn new() -> Self {
        Self {
            cpu_monitor: CpuMonitor::new(),
            gpu_monitor: GpuMonitor::new(),
            memory_monitor: MemoryMonitor::new(),
            network_monitor: NetworkMonitor::new(),
            storage_monitor: StorageMonitor::new(),
            
            // Initialize buffers with default values
            cpu_buffer: CpuMetrics::default(),
            gpu_buffer: GpuMetrics::default(),
            memory_buffer: MemoryMetrics::default(),
            network_buffer: NetworkMetrics::default(),
            storage_buffer: StorageMetrics::default(),
        }
    }

    /// Bootstrap hardware discovery (blocking, call once at startup)
    pub fn bootstrap(&mut self) -> PyResult<()> {
        self.cpu_monitor.discover()?;
        self.gpu_monitor.discover()?;
        self.network_monitor.discover()?;
        Ok(())
    }

    /// Collect all metrics (hot loop - zero allocations)
    pub fn collect_all(&self) -> TelemetrySnapshot {
        TelemetrySnapshot {
            cpu: self.cpu_monitor.collect(),
            gpu: self.gpu_monitor.collect(),
            memory: self.memory_monitor.collect(),
            network: self.network_monitor.collect(),
            storage: self.storage_monitor.collect(),
        }
    }

    /// Set active network adapter
    pub fn set_active_adapter(&mut self, adapter_name: String) {
        self.network_monitor.set_active_adapter(adapter_name);
    }
}
