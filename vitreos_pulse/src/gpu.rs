use pyo3::PyResult;
use nvml_wrapper::Nvml;
use nvml_wrapper::Device;
use nvml_wrapper::enum_wrappers::device::{Clock, TemperatureSensor};
use std::sync::Arc;
use parking_lot::Mutex;

#[derive(Clone, Debug)]
pub struct GpuMetrics {
    pub name: String,
    pub usage: u32,
    pub vram_used_gb: f32,
    pub vram_total_gb: f32,
    pub vram_percent: f32,
    pub core_clock: u32,
    pub mem_clock: u32,
    pub power: f32,
    pub temp: u32,
    pub fan_speed: u32,
    pub status: String,
}

impl Default for GpuMetrics {
    fn default() -> Self {
        Self {
            name: "NO GPU DETECTED".to_string(),
            usage: 0,
            vram_used_gb: 0.0,
            vram_total_gb: 0.0,
            vram_percent: 0.0,
            core_clock: 0,
            mem_clock: 0,
            power: 0.0,
            temp: 0,
            fan_speed: 0,
            status: "unavailable".to_string(),
        }
    }
}

pub struct GpuMonitor {
    nvml: Option<Arc<Mutex<Nvml>>>,
    device_index: u32,
    gpu_name: String,
    vram_total_gb: f32,
}

impl GpuMonitor {
    pub fn new() -> Self {
        Self {
            nvml: None,
            device_index: 0,
            gpu_name: String::new(),
            vram_total_gb: 0.0,
        }
    }

    /// Discover GPU hardware (blocking)
    pub fn discover(&mut self) -> PyResult<()> {
        match Nvml::init() {
            Ok(nvml) => {
                // Get first GPU device
                match nvml.device_by_index(0) {
                    Ok(device) => {
                        // Get GPU name
                        if let Ok(name) = device.name() {
                            self.gpu_name = Self::clean_gpu_name(&name);
                        }
                        
                        // Get VRAM total
                        if let Ok(memory_info) = device.memory_info() {
                            self.vram_total_gb = memory_info.total as f32 / (1024.0 * 1024.0 * 1024.0);
                        }
                        
                        self.nvml = Some(Arc::new(Mutex::new(nvml)));
                        println!("[PULSE] GPU detected: {} ({:.0}GB)", self.gpu_name, self.vram_total_gb);
                    }
                    Err(e) => {
                        eprintln!("[PULSE] No GPU found: {}", e);
                    }
                }
            }
            Err(e) => {
                eprintln!("[PULSE] NVML init failed: {}", e);
            }
        }
        
        Ok(())
    }

    /// Collect GPU metrics (hot loop - optimized)
    pub fn collect(&self) -> GpuMetrics {
        let Some(ref nvml) = self.nvml else {
            return GpuMetrics::default();
        };
        
        let nvml = nvml.lock();
        let Ok(device) = nvml.device_by_index(self.device_index) else {
            return GpuMetrics::default();
        };
        
        // Utilization
        let usage = device.utilization_rates()
            .map(|u| u.gpu)
            .unwrap_or(0);
        
        // Memory
        let (vram_used_gb, vram_percent) = device.memory_info()
            .map(|info| {
                let used_gb = info.used as f32 / (1024.0 * 1024.0 * 1024.0);
                let percent = (info.used as f32 / info.total as f32) * 100.0;
                (used_gb, percent)
            })
            .unwrap_or((0.0, 0.0));
        
        // Temperature
        let temp = device.temperature(TemperatureSensor::Gpu)
            .unwrap_or(0);
        
        // Power (convert mW to W)
        let power = device.power_usage()
            .map(|p| p as f32 / 1000.0)
            .unwrap_or(0.0);
        
        // Clocks
        let core_clock = device.clock_info(Clock::Graphics)
            .unwrap_or(0);
        let mem_clock = device.clock_info(Clock::Memory)
            .unwrap_or(0);
        
        // Fan speed
        let fan_speed = device.fan_speed(0)
            .unwrap_or(0);
        
        // Status based on temperature
        let status = if temp > 85 {
            "critical"
        } else if temp > 75 {
            "warning"
        } else {
            "normal"
        }.to_string();
        
        GpuMetrics {
            name: self.gpu_name.clone(),
            usage,
            vram_used_gb,
            vram_total_gb: self.vram_total_gb,
            vram_percent,
            core_clock,
            mem_clock,
            power,
            temp,
            fan_speed,
            status,
        }
    }

    /// Clean GPU name (remove vendor prefixes)
    fn clean_gpu_name(name: &str) -> String {
        name.replace("NVIDIA ", "")
            .replace("GeForce ", "")
            .replace("AMD ", "")
            .replace("Radeon ", "")
            .trim()
            .to_string()
    }
}
