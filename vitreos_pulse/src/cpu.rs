use pyo3::PyResult;
use sysinfo::{System, CpuExt, SystemExt};
use std::sync::Arc;
use parking_lot::Mutex;

#[derive(Clone, Debug)]
pub struct CpuMetrics {
    pub name: String,
    pub total_load: f32,
    pub temp: f32,
    pub clock: u32,
    pub per_core_load: Vec<f32>,
    pub core_count: usize,
    pub physical_cores: usize,
    pub logical_threads: usize,
    pub package_power: f32,
    pub vid: f32,
}

impl Default for CpuMetrics {
    fn default() -> Self {
        Self {
            name: "Unknown CPU".to_string(),
            total_load: 0.0,
            temp: 0.0,
            clock: 0,
            per_core_load: Vec::new(),
            core_count: 0,
            physical_cores: 0,
            logical_threads: 0,
            package_power: 0.0,
            vid: 0.0,
        }
    }
}

pub struct CpuMonitor {
    system: Arc<Mutex<System>>,
    cpu_name: String,
    physical_cores: usize,
    logical_threads: usize,
}

impl CpuMonitor {
    pub fn new() -> Self {
        let mut system = System::new_all();
        system.refresh_cpu();
        
        Self {
            system: Arc::new(Mutex::new(system)),
            cpu_name: String::new(),
            physical_cores: 0,
            logical_threads: 0,
        }
    }

    /// Discover CPU hardware (blocking)
    pub fn discover(&mut self) -> PyResult<()> {
        let system = self.system.lock();
        
        // Get CPU brand from first CPU
        if let Some(cpu) = system.cpus().first() {
            self.cpu_name = Self::clean_cpu_name(cpu.brand());
        }
        
        self.logical_threads = system.cpus().len();
        self.physical_cores = system.physical_core_count().unwrap_or(self.logical_threads / 2);
        
        Ok(())
    }

    /// Collect CPU metrics (hot loop - optimized)
    pub fn collect(&self) -> CpuMetrics {
        let mut system = self.system.lock();
        system.refresh_cpu();
        
        let cpus = system.cpus();
        let total_load = system.global_cpu_info().cpu_usage();
        
        // Pre-allocate vector with exact capacity (logical thread loads)
        let mut per_core_load = Vec::with_capacity(cpus.len());
        for cpu in cpus {
            per_core_load.push(cpu.cpu_usage());
        }

        // Aggregate logical-thread loads into physical-core averages when SMT present
        let mut per_physical_load: Vec<f32> = Vec::new();
        if self.physical_cores > 0 && self.logical_threads > 0 {
            let threads_per_physical = self.logical_threads / self.physical_cores;
            if threads_per_physical >= 1 {
                for i in 0..self.physical_cores {
                    let start = i * threads_per_physical;
                    let end = ((i + 1) * threads_per_physical).min(per_core_load.len());
                    let mut sum: f32 = 0.0;
                    let mut count: usize = 0;
                    for j in start..end {
                        sum += per_core_load[j];
                        count += 1;
                    }
                    if count > 0 {
                        per_physical_load.push(sum / (count as f32));
                    } else {
                        per_physical_load.push(0.0);
                    }
                }
            } else {
                per_physical_load = per_core_load.clone();
            }
        } else {
            per_physical_load = per_core_load.clone();
        }
        
        // Get CPU frequency (MHz)
        let clock = cpus.first()
            .map(|cpu| cpu.frequency() as u32)
            .unwrap_or(0);
        
        CpuMetrics {
            name: self.cpu_name.clone(),
            total_load,
            // Sysinfo on Windows often doesn't provide temperature; leave as 0.0 when unknown
            temp: 0.0,
            clock,
            // Expose per-physical-core averages to the consumer (matches user expectation for 7900X=12, 5700X=8)
            per_core_load: per_physical_load,
            // Report core_count as physical core count (not logical threads)
            core_count: self.physical_cores,
            physical_cores: self.physical_cores,
            logical_threads: self.logical_threads,
            package_power: 0.0, // Placeholder - requires platform-specific query
            vid: 0.0, // Placeholder
        }
    }

    /// Clean CPU name (remove junk suffixes)
    fn clean_cpu_name(name: &str) -> String {
        let mut cleaned = name.to_string();
        
        // Force clean cut after specific CPU model numbers
        if let Some(pos) = cleaned.find("5700X") {
            cleaned = cleaned[..pos + 5].to_string();
        } else if let Some(pos) = cleaned.find("5800X") {
            cleaned = cleaned[..pos + 5].to_string();
        } else if let Some(pos) = cleaned.find("5900X") {
            cleaned = cleaned[..pos + 5].to_string();
        } else if let Some(pos) = cleaned.find("7900X") {
            cleaned = cleaned[..pos + 5].to_string();
        } else if let Some(pos) = cleaned.find("7700X") {
            cleaned = cleaned[..pos + 5].to_string();
        }
        
        // Remove common junk
        let junk_patterns = [
            "(R)", "(TM)", "(tm)", "(r)",
            "with Radeon Graphics", "with Radeon Vega Graphics",
            "CPU @", "Processor", "8-Core", "16-Core", "12-Core"
        ];
        
        for pattern in &junk_patterns {
            cleaned = cleaned.replace(pattern, "");
        }
        
        // Clean up multiple spaces
        cleaned.split_whitespace().collect::<Vec<_>>().join(" ")
    }
}
