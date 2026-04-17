use sysinfo::{System, SystemExt};
use std::sync::Arc;
use parking_lot::Mutex;
use std::process::Command;
use std::str;
use serde_json::Value;

#[derive(Clone, Debug, Default)]
pub struct DimmSlot {
    pub locator: String,
    pub capacity_gb: f32,
    pub speed_mt: u32,
    pub configured_clock: u32,
    pub manufacturer: String,
    pub part_number: String,
    pub serial: String,
    pub populated: bool,
}

#[derive(Clone, Debug, Default)]
pub struct MemoryMetrics {
    pub used_gb: f32,
    pub total_gb: f32,
    pub percent: f32,
    // Per-slot information collected via WMI on Windows
    pub slots: Vec<DimmSlot>,
    // Derived values
    pub effective_speed_mt: u32,
    pub channel_mode: String,
    pub header_spec: String,
    pub xmp_active: bool,
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
        let percent = if total_bytes > 0 { (used_bytes as f32 / total_bytes as f32) * 100.0 } else { 0.0 };

        // Attempt deep-scan of physical memory via WMI on Windows
        let mut slots: Vec<DimmSlot> = Vec::new();
        if cfg!(target_os = "windows") {
            if let Some(mem_items) = query_wmi_memory() {
                for item in mem_items.iter() {
                    let locator = item.get("DeviceLocator").and_then(|v| v.as_str()).unwrap_or("").to_string();

                    // Capacity might be a string or number
                    let mut capacity_gb: f32 = 0.0;
                    if let Some(cap) = item.get("Capacity") {
                        if let Some(s) = cap.as_str() {
                            if let Ok(v) = s.parse::<u64>() {
                                capacity_gb = v as f32 / (1024.0 * 1024.0 * 1024.0);
                            }
                        } else if let Some(n) = cap.as_u64() {
                            capacity_gb = n as f32 / (1024.0 * 1024.0 * 1024.0);
                        }
                    }

                    let speed_mt = item.get("Speed").and_then(|v| v.as_u64()).unwrap_or(0) as u32;
                    let configured = item.get("ConfiguredClockSpeed").and_then(|v| v.as_u64()).unwrap_or(0) as u32;
                    let manufacturer = item.get("Manufacturer").and_then(|v| v.as_str()).unwrap_or("").to_string();
                    let part = item.get("PartNumber").and_then(|v| v.as_str()).unwrap_or("").to_string();
                    let serial = item.get("SerialNumber").and_then(|v| v.as_str()).unwrap_or("").to_string();

                    let populated = capacity_gb > 0.0;

                    slots.push(DimmSlot {
                        locator,
                        capacity_gb,
                        speed_mt,
                        configured_clock: configured,
                        manufacturer,
                        part_number: part,
                        serial,
                        populated,
                    });
                }
            }
        }

        // Heuristic: determine effective speed and channel mode
        let mut effective_speed: u32 = 0;
        let mut populated_count = 0usize;
        let mut xmp = false;
        for s in slots.iter() {
            if s.populated {
                populated_count += 1;
                if s.configured_clock > 0 {
                    if effective_speed == 0 { effective_speed = s.configured_clock; }
                    else { effective_speed = effective_speed.min(s.configured_clock); }
                } else if s.speed_mt > 0 {
                    if effective_speed == 0 { effective_speed = s.speed_mt; }
                    else { effective_speed = effective_speed.min(s.speed_mt); }
                }
                if s.configured_clock > 0 && s.speed_mt > 0 && s.configured_clock != s.speed_mt {
                    xmp = true;
                }
            }
        }

        let channel_mode = if populated_count <= 1 {
            "SINGLE".to_string()
        } else if populated_count % 2 == 0 {
            "DUAL".to_string()
        } else {
            "MULTI".to_string()
        };

        // Header spec: best-effort (DDR generation inferred from speed)
        let header_spec = if effective_speed > 0 {
            let gen = if effective_speed >= 4800 { 5 } else { 4 };
            format!("DDR{}-{} | CL-- | V--", gen, effective_speed)
        } else {
            "DDR?-? | CL-- | V--".to_string()
        };

        MemoryMetrics {
            used_gb,
            total_gb,
            percent,
            slots,
            effective_speed_mt: effective_speed,
            channel_mode,
            header_spec,
            xmp_active: xmp,
        }
    }
}

/// Query Win32_PhysicalMemory via PowerShell and return parsed JSON objects
fn query_wmi_memory() -> Option<Vec<Value>> {
    if cfg!(target_os = "windows") {
        let cmd = r#"Get-WmiObject Win32_PhysicalMemory | Select-Object DeviceLocator,Capacity,Speed,ConfiguredClockSpeed,Manufacturer,PartNumber,SerialNumber | ConvertTo-Json -Depth 3"#;
        let shells = ["pwsh", "powershell"];
        for sh in shells {
            let output = Command::new(sh)
                .args(["-NoProfile", "-Command", cmd])
                .output();
            if let Ok(out) = output {
                if out.status.success() {
                    if let Ok(txt) = str::from_utf8(&out.stdout) {
                        if let Ok(v) = serde_json::from_str::<Value>(txt) {
                            if v.is_array() {
                                return v.as_array().cloned();
                            } else {
                                return Some(vec![v]);
                            }
                        }
                    }
                }
            }
        }
    }
    None
}
