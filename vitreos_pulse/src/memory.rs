use sysinfo::{System, SystemExt};
use std::sync::Arc;
use parking_lot::Mutex;

#[derive(Clone, Debug)]
pub struct MemoryMetrics {
    pub used_gb: f32,
    pub total_gb: f32,
    pub percent: f32,
}

impl Default for MemoryMetrics {
    fn default() -> Self {
        Self {
            used_gb: 0.0,
            total_gb: 0.0,
            percent: 0.0,
        }
    }
}

pub struct MemoryMonitor {
    system: Arc<Mutex<System>>,
}

impl MemoryMonitor {
    pub fn new() -> Self {
        Self {
            system: Arc::new(Mutex::new(System::new_all())),
        }
    }

    /// Collect memory metrics (hot loop - optimized)
    pub fn collect(&self) -> MemoryMetrics {
        let mut system = self.system.lock();
        system.refresh_memory();
        
        let total_bytes = system.total_memory();
        let used_bytes = system.used_memory();
        
        let total_gb = total_bytes as f32 / (1024.0 * 1024.0 * 1024.0);
        let used_gb = used_bytes as f32 / (1024.0 * 1024.0 * 1024.0);
        let percent = (used_bytes as f32 / total_bytes as f32) * 100.0;
        
        MemoryMetrics {
            used_gb,
            total_gb,
            percent,
        }
    }
}
