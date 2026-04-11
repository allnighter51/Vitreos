use sysinfo::{System, NetworkExt, NetworksExt, SystemExt};
use std::sync::Arc;
use parking_lot::Mutex;
use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct NetworkMetrics {
    pub download_mbps: f32,
    pub upload_mbps: f32,
    pub latency_ms: f32,
    pub primary_adapter: String,
}

impl Default for NetworkMetrics {
    fn default() -> Self {
        Self {
            download_mbps: 0.0,
            upload_mbps: 0.0,
            latency_ms: 0.0,
            primary_adapter: "ETH".to_string(),
        }
    }
}

pub struct NetworkMonitor {
    system: Arc<Mutex<System>>,
    active_adapter: String,
    last_rx_bytes: HashMap<String, u64>,
    last_tx_bytes: HashMap<String, u64>,
    last_poll_time: std::time::Instant,
}

impl NetworkMonitor {
    pub fn new() -> Self {
        Self {
            system: Arc::new(Mutex::new(System::new_all())),
            active_adapter: String::new(),
            last_rx_bytes: HashMap::new(),
            last_tx_bytes: HashMap::new(),
            last_poll_time: std::time::Instant::now(),
        }
    }

    /// Discover primary network adapter (blocking)
    pub fn discover(&mut self) -> pyo3::PyResult<()> {
        let mut system = self.system.lock();
        system.refresh_networks_list();
        
        // Find adapter with highest traffic
        let networks = system.networks();
        let mut max_traffic = 0u64;
        let mut primary = String::new();
        
        for (interface_name, data) in networks {
            let total_traffic = data.total_received() + data.total_transmitted();
            if total_traffic > max_traffic {
                max_traffic = total_traffic;
                primary = interface_name.clone();
            }
        }
        
        if !primary.is_empty() {
            self.active_adapter = primary.clone();
            println!("[PULSE] Primary adapter: {}", primary);
        }
        
        Ok(())
    }

    /// Collect network metrics (hot loop - optimized)
    pub fn collect(&self) -> NetworkMetrics {
        let mut system = self.system.lock();
        system.refresh_networks();
        
        let networks = system.networks();
        
        // Get active adapter or fallback to first available
        let adapter_name = if !self.active_adapter.is_empty() {
            &self.active_adapter
        } else {
            networks.iter().next().map(|(name, _)| name.as_str()).unwrap_or("ETH")
        };
        
        let (download_mbps, upload_mbps) = if let Some(data) = networks.get(adapter_name) {
            let rx_bytes = data.total_received();
            let tx_bytes = data.total_transmitted();
            
            // Calculate Mbps (bytes per second * 8 / 1,000,000)
            let rx_mbps = (data.received() as f32 * 8.0) / 1_000_000.0;
            let tx_mbps = (data.transmitted() as f32 * 8.0) / 1_000_000.0;
            
            (rx_mbps, tx_mbps)
        } else {
            (0.0, 0.0)
        };
        
        NetworkMetrics {
            download_mbps,
            upload_mbps,
            latency_ms: 0.0, // Placeholder - requires ICMP ping
            primary_adapter: adapter_name.to_string(),
        }
    }

    /// Set active network adapter
    pub fn set_active_adapter(&mut self, adapter_name: String) {
        self.active_adapter = adapter_name;
    }
}
