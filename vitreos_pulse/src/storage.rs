use sysinfo::{System, DiskExt, SystemExt};
use std::sync::Arc;
use parking_lot::Mutex;
use std::process::Command;
use std::str;
use serde_json::Value;
use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct DriveInfo {
    pub drive_type: String,
    pub model: String,
    pub mountpoint: String,
    pub used_gb: f32,
    pub total_gb: f32,
    pub percent: f32,
    pub serial: String,
    pub temp_c: f32,
    pub read_bps: f32,
    pub write_bps: f32,
    pub max_read_bps: f32,
    pub max_write_bps: f32,
}

#[derive(Clone, Debug)]
pub struct StorageMetrics {
    pub drives: Vec<DriveInfo>,
}

impl Default for StorageMetrics {
    fn default() -> Self {
        Self {
            drives: Vec::new(),
        }
    }
}

pub struct StorageMonitor {
    system: Arc<Mutex<System>>,
    // Track per-drive observed maxima for throughput
    max_read_map: Mutex<HashMap<String, u64>>,
    max_write_map: Mutex<HashMap<String, u64>>,
}

impl StorageMonitor {
    pub fn new() -> Self {
        Self {
            system: Arc::new(Mutex::new(System::new_all())),
            max_read_map: Mutex::new(HashMap::new()),
            max_write_map: Mutex::new(HashMap::new()),
        }
    }

    /// Collect storage metrics (hot loop - optimized)
    pub fn collect(&self) -> StorageMetrics {
        let mut system = self.system.lock();
        // Force full refresh of disk list and data
        system.refresh_disks_list();
        system.refresh_disks();
        
        // Gather optional WMI-based metadata and perf counters on Windows
        let wmi_disks = query_wmi_disks();
        let perf_samples = query_perf_counters();
        let smart_samples = query_ms_storage_smart();

        let mut drives = Vec::new();

        for disk in system.disks() {
            let total_bytes = disk.total_space();
            let available_bytes = disk.available_space();
            let used_bytes = total_bytes.saturating_sub(available_bytes);
            
            let total_gb = total_bytes as f32 / (1024.0 * 1024.0 * 1024.0);
            let used_gb = used_bytes as f32 / (1024.0 * 1024.0 * 1024.0);
            let percent = if total_bytes > 0 {
                (used_bytes as f32 / total_bytes as f32) * 100.0
            } else {
                0.0
            };
            
            // Get disk name and file system type for better identification
            let disk_name = disk.name().to_string_lossy().to_string();
            let fs_type = String::from_utf8_lossy(disk.file_system()).to_string();
            let mount_point = disk.mount_point().to_string_lossy().to_string();
            
            // Default metadata
            let mut drive_type = if disk_name.to_lowercase().contains("nvme") || fs_type.to_lowercase().contains("nvme") {
                "NVMe".to_string()
            } else if disk_name.to_lowercase().contains("ssd") || mount_point.to_uppercase().contains("SSD") {
                "SSD".to_string()
            } else if fs_type.to_lowercase().contains("ntfs") || fs_type.to_lowercase().contains("fat") {
                "HDD".to_string()
            } else {
                "DISK".to_string()
            };

            // Fallback model/serial/temp/read/write from WMI/Perf if available (Windows)
            let mut model = if !disk_name.is_empty() && disk_name != mount_point {
                disk_name.clone()
            } else {
                format!("{}_{}", drive_type, mount_point.replace('\\', "").replace(':', ""))
            };

            let mut serial = String::new();
            let mut temp_c: f32 = 0.0;
            let mut read_bps: f32 = 0.0;
            let mut write_bps: f32 = 0.0;
            let mut max_read_bps: f32 = 0.0;
            let mut max_write_bps: f32 = 0.0;

            // Try to match WMI disk by size (tolerant match)
            if let Some(ref wmi) = wmi_disks {
                if let Some(match_obj) = find_matching_wmi_disk(wmi, total_bytes) {
                    if let Some(m) = match_obj.get("Model").and_then(|v| v.as_str()) {
                        if !m.is_empty() { model = m.to_string(); }
                    }
                    if let Some(s) = match_obj.get("SerialNumber").and_then(|v| v.as_str()) {
                        serial = s.to_string();
                    }
                    if let Some(mt) = match_obj.get("MediaType").and_then(|v| v.as_str()) {
                        let mt_l = mt.to_lowercase();
                        if mt_l.contains("ssd") || mt_l.contains("nvme") {
                            drive_type = "SSD".to_string();
                        } else if mt_l.contains("hdd") || mt_l.contains("fixed") {
                            drive_type = "HDD".to_string();
                        }
                    }
                }
            }

            // Try to extract SMART temperature from MSStorageDriver_FailurePredictData
            if serial.is_empty() {
                // try to populate serial from smart_samples if available
                if let Some(ref smart) = smart_samples {
                    if let Some(smart_obj) = find_matching_smart_entry(smart, &model, total_bytes) {
                        if let Some(inst) = smart_obj.get("InstanceName").and_then(|v| v.as_str()) {
                            // instance found - optionally use it
                        }
                        if let Some(vs) = smart_obj.get("VendorSpecific").and_then(|v| v.as_array()) {
                            if let Some(t) = parse_temp_from_vendor(vs) {
                                temp_c = t;
                            }
                        }
                    }
                }
            } else {
                // we have a serial; still try SMART for temperature
                if let Some(ref smart) = smart_samples {
                    if let Some(smart_obj) = find_matching_smart_entry(smart, &model, total_bytes) {
                        if let Some(vs) = smart_obj.get("VendorSpecific").and_then(|v| v.as_array()) {
                            if let Some(t) = parse_temp_from_vendor(vs) {
                                temp_c = t;
                            }
                        }
                    }
                }
            }
            // Map perf counters by instance index
            if let Some(ref perf) = perf_samples {
                if let Some((r, w)) = find_perf_for_disk(perf, &model, total_bytes) {
                    read_bps = r as f32;
                    write_bps = w as f32;
                }
            }

            // Update per-drive maxima
            let key = format!("{}:{}", mount_point, total_bytes);
            {
                let mut rmap = self.max_read_map.lock();
                let mut wmap = self.max_write_map.lock();
                let r_u = read_bps as u64;
                let w_u = write_bps as u64;
                let prev_r = *rmap.get(&key).unwrap_or(&0u64);
                let prev_w = *wmap.get(&key).unwrap_or(&0u64);
                if r_u > prev_r {
                    rmap.insert(key.clone(), r_u);
                }
                if w_u > prev_w {
                    wmap.insert(key.clone(), w_u);
                }
                max_read_bps = *rmap.get(&key).unwrap_or(&0u64) as f32;
                max_write_bps = *wmap.get(&key).unwrap_or(&0u64) as f32;
            }

            drives.push(DriveInfo {
                drive_type,
                model,
                mountpoint: mount_point,
                used_gb,
                total_gb,
                percent,
                serial,
                temp_c,
                read_bps,
                write_bps,
                max_read_bps,
                max_write_bps,
            });
        }
        
        StorageMetrics { drives }
    }
}

/// Attempt to query WMI Win32_DiskDrive and return parsed JSON objects
fn query_wmi_disks() -> Option<Vec<Value>> {
    if cfg!(target_os = "windows") {
        // Try pwsh first, fallback to powershell
        let cmd = r#"Get-WmiObject Win32_DiskDrive | Select-Object Index,Model,SerialNumber,DeviceID,PNPDeviceID,Size,MediaType | ConvertTo-Json -Depth 3"#;
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

/// Query perf counters for PhysicalDisk read/write bytes/sec and return samples
fn query_perf_counters() -> Option<Vec<Value>> {
    if cfg!(target_os = "windows") {
        let cmd = r#"$r = Get-Counter -Counter '\\PhysicalDisk(*)\\Disk Read Bytes/sec','\\PhysicalDisk(*)\\Disk Write Bytes/sec' -SampleInterval 1 -MaxSamples 1; $r.CounterSamples | Select-Object InstanceName,Path,CookedValue | ConvertTo-Json -Depth 3"#;
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

/// Find matching WMI disk by size (tolerance 1MB)
fn find_matching_wmi_disk<'a>(wmi: &'a Vec<Value>, total_bytes: u64) -> Option<&'a Value> {
    for item in wmi.iter() {
        if let Some(size_v) = item.get("Size") {
            if let Some(size_str) = size_v.as_str() {
                if let Ok(size_val) = size_str.parse::<u64>() {
                    let diff = if size_val > total_bytes { size_val - total_bytes } else { total_bytes - size_val };
                    if diff < 1_048_576 { // 1MB tolerance
                        return Some(item);
                    }
                }
            } else if let Some(size_num) = size_v.as_u64() {
                let diff = if size_num > total_bytes { size_num - total_bytes } else { total_bytes - size_num };
                if diff < 1_048_576 {
                    return Some(item);
                }
            }
        }
    }
    None
}

/// Find perf read/write pair for a disk by matching instance name index or model/size
fn find_perf_for_disk(perf: &Vec<Value>, model: &str, total_bytes: u64) -> Option<(u64, u64)> {
    // Build map from instance index -> (read, write)
    use std::collections::HashMap as StdMap;
    let mut map: StdMap<String, (u64, u64)> = StdMap::new();
    for sample in perf.iter() {
        if let Some(path) = sample.get("Path").and_then(|v| v.as_str()) {
            // Example Path: \\\PhysicalDisk(0 C:)\\Disk Read Bytes/sec
            if let Some(start) = path.find('(') {
                if let Some(end) = path[start+1..].find(')') {
                    let inst = &path[start+1..start+1+end];
                    // Instance may be "0 C:" or "_Total" - we only care numeric prefix
                    let idx = inst.split_whitespace().next().unwrap_or(inst).to_string();
                    let val = sample.get("CookedValue").and_then(|v| v.as_f64()).unwrap_or(0.0) as u64;
                    if path.contains("Disk Read Bytes/sec") {
                        let entry = map.entry(idx).or_insert((0u64, 0u64));
                        entry.0 = val;
                    } else if path.contains("Disk Write Bytes/sec") {
                        let entry = map.entry(idx).or_insert((0u64, 0u64));
                        entry.1 = val;
                    }
                }
            }
        }
    }

    // Try to pick an entry: prefer exact size match via index->WMI if we had WMI available earlier
    // Fallback: if only one non-total instance, return it
    for (k, v) in map.iter() {
        if k == "_Total" { continue; }
        // Return the first numeric instance
        if k.chars().next().map(|c| c.is_digit(10)).unwrap_or(false) {
            return Some((*v).clone());
        }
    }

    // As last resort, return _Total if present
    if let Some(v) = map.get("_Total") {
        return Some(*v);
    }

    None
}

/// Query MSStorageDriver_FailurePredictData for SMART vendor-specific blobs
fn query_ms_storage_smart() -> Option<Vec<Value>> {
    if cfg!(target_os = "windows") {
        let cmd = r#"Get-WmiObject -Namespace root\wmi -Class MSStorageDriver_FailurePredictData | Select-Object InstanceName,VendorSpecific | ConvertTo-Json -Depth 3"#;
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

/// Find a matching SMART entry heuristically by looking for instance names or sizes
fn find_matching_smart_entry<'a>(smart: &'a Vec<Value>, model: &str, total_bytes: u64) -> Option<&'a Value> {
    for item in smart.iter() {
        // InstanceName often contains device identifier; try to match by model substring
        if let Some(inst) = item.get("InstanceName").and_then(|v| v.as_str()) {
            if inst.to_lowercase().contains(&model.to_lowercase()) {
                return Some(item);
            }
        }
    }
    // fallback: return first entry
    smart.get(0)
}

/// Parse a vendor-specific SMART blob for a plausible temperature value (best-effort)
fn parse_temp_from_vendor(vs: &Vec<Value>) -> Option<f32> {
    // Convert to bytes
    let bytes: Vec<u8> = vs.iter().filter_map(|v| v.as_u64().map(|n| n as u8)).collect();
    // Heuristic: scan for a byte in plausible temperature range
    for &b in &bytes {
        if b >= 10 && b <= 85 {
            return Some(b as f32);
        }
    }
    None
}
