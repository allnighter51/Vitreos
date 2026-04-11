#!/usr/bin/env python3
"""
Vitreos Vitals Tab - System Overview Dashboard
"""
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget, QGridLayout
from src.ui.vitreos_core_ui import VitreosModule


class VitalsTab(QWidget):
    """System vitals overview with 6 monitoring modules"""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the vitals dashboard layout"""
        layout = QGridLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create 6 monitoring modules in 3x2 grid
        self.cpu_module = VitreosModule("CPU", "🔥", self)
        self.gpu_module = VitreosModule("GPU", "⚡", self)
        self.memory_module = VitreosModule("Memory", "💾", self)
        self.network_module = VitreosModule("Network", "🌐", self)
        self.thermal_module = VitreosModule("Thermal", "🌡️", self)
        self.disk_module = VitreosModule("Disk", "💿", self)
        
        # Add to grid layout
        layout.addWidget(self.cpu_module, 0, 0)
        layout.addWidget(self.gpu_module, 0, 1)
        layout.addWidget(self.memory_module, 0, 2)
        layout.addWidget(self.network_module, 1, 0)
        layout.addWidget(self.thermal_module, 1, 1)
        layout.addWidget(self.disk_module, 1, 2)
    
    def update_stats(self, stats: Dict[str, Any]) -> None:
        """Update all vitals modules with new statistics"""
        # CPU Module
        cpu_pct = stats.get('cpu_percent', 0)
        self.cpu_module.set_primary_value(f"{cpu_pct}%")
        self.cpu_module.set_secondary_value(f"{stats.get('cpu_freq', 0):.0f} MHz")
        
        if cpu_pct > 90:
            self.cpu_module.set_hazard_level("CRITICAL", "#ff0000")
        elif cpu_pct > 70:
            self.cpu_module.set_hazard_level("WARNING", "#ff8c00")
        elif cpu_pct > 50:
            self.cpu_module.set_hazard_level("ELEVATED", "#ffff00")
        else:
            self.cpu_module.set_hazard_level("STABLE", "#00ff00")
        
        # GPU Module
        gpu_usage = stats.get('gpu_usage', 0)
        self.gpu_module.set_primary_value(f"{gpu_usage}%")
        self.gpu_module.set_secondary_value(f"{stats.get('gpu_temp', 0)}°C")
        
        if gpu_usage > 90:
            self.gpu_module.set_hazard_level("CRITICAL", "#ff0000")
        elif gpu_usage > 70:
            self.gpu_module.set_hazard_level("WARNING", "#ff8c00")
        else:
            self.gpu_module.set_hazard_level("STABLE", "#00ff00")
        
        # Memory Module
        mem_pct = stats.get('memory_percent', 0)
        mem_used = stats.get('memory_used', 0) / (1024**3)  # Convert to GB
        self.memory_module.set_primary_value(f"{mem_pct}%")
        self.memory_module.set_secondary_value(f"{mem_used:.1f} GB Used")
        
        if mem_pct > 90:
            self.memory_module.set_hazard_level("CRITICAL", "#ff0000")
        elif mem_pct > 75:
            self.memory_module.set_hazard_level("WARNING", "#ff8c00")
        else:
            self.memory_module.set_hazard_level("STABLE", "#00ff00")
        
        # Network Module
        net_sent = stats.get('net_sent_mbps', 0)
        net_recv = stats.get('net_recv_mbps', 0)
        self.network_module.set_primary_value(f"{net_recv:.1f} Mbps")
        self.network_module.set_secondary_value(f"↑ {net_sent:.1f} Mbps")
        self.network_module.set_hazard_level("ACTIVE", "#00f2ff")
        
        # Thermal Module
        cpu_temp = stats.get('cpu_temp', 0)
        self.thermal_module.set_primary_value(f"{cpu_temp}°C")
        self.thermal_module.set_secondary_value(f"GPU: {stats.get('gpu_temp', 0)}°C")
        
        if cpu_temp > 85:
            self.thermal_module.set_hazard_level("CRITICAL", "#ff0000")
        elif cpu_temp > 75:
            self.thermal_module.set_hazard_level("WARNING", "#ff8c00")
        elif cpu_temp > 65:
            self.thermal_module.set_hazard_level("ELEVATED", "#ffff00")
        else:
            self.thermal_module.set_hazard_level("STABLE", "#00ff00")
        
        # Disk Module
        disk_pct = stats.get('disk_percent', 0)
        disk_free = stats.get('disk_free', 0) / (1024**3)  # Convert to GB
        self.disk_module.set_primary_value(f"{disk_pct}%")
        self.disk_module.set_secondary_value(f"{disk_free:.1f} GB Free")
        
        if disk_pct > 95:
            self.disk_module.set_hazard_level("CRITICAL", "#ff0000")
        elif disk_pct > 85:
            self.disk_module.set_hazard_level("WARNING", "#ff8c00")
        else:
            self.disk_module.set_hazard_level("STABLE", "#00ff00")


