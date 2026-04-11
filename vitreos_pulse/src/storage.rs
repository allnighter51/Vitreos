use sysinfo::{System, DiskExt, SystemExt};
use std::sync::Arc;
use parking_lot::Mutex;

#[derive(Clone, Debug)]
pub struct DriveInfo {
    pub drive_type: String,
    pub model: String,
    pub mountpoint: String,
    pub used_gb: f32,
    pub total_gb: f32,
    pub percent: f32,
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
}

impl StorageMonitor {
    pub fn new() -> Self {
        Self {
            system: Arc::new(Mutex::new(System::new_all())),
        }
    }

    /// Collect storage metrics (hot loop - optimized)
    pub fn collect(&self) -> StorageMetrics {
        let mut system = self.system.lock();
        system.refresh_disks_list();
        system.refresh_disks();
        
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
            
            // Determine drive type from name
            let name = disk.name().to_string_lossy().to_string();
            let drive_type = if name.to_lowercase().contains("nvme") {
                "NVMe"
            } else if name.to_lowercase().contains("ssd") {
                "SSD"
            } else {
                "HDD"
            }.to_string();
            
            drives.push(DriveInfo {
                drive_type,
                model: name.clone(),
                mountpoint: disk.mount_point().to_string_lossy().to_string(),
                used_gb,
                total_gb,
                percent,
            });
        }
        
        StorageMetrics { drives }
    }
}
