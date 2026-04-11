"""
Vitreos Sentinel - Vitals Tab Module
Real-time hardware monitoring with 6 module widgets
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore import Qt
from vitreos_core_ui import VitreosModule


class VitalsTab(QWidget):
    """Vitals tab with 6 hardware monitoring modules in 3x2 grid"""
    
    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet("background: transparent;")
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("⚡ SYSTEM VITALS")
        title.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 24px;
            font-weight: bold;
            color: #00f2ff;
            padding: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 3x2 Grid for modules
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Create 6 modules
        self.cpu_module = VitreosModule("CPU", "⚙️")
        self.gpu_module = VitreosModule("GPU", "🎮")
        self.memory_module = VitreosModule("MEMORY", "💾")
        self.network_module = VitreosModule("NETWORK", "🌐")
        self.thermal_module = VitreosModule("THERMAL", "🌡️")
        self.disk_module = VitreosModule("DISK", "💿")
        
        # Add to grid (3 columns, 2 rows)
        grid.addWidget(self.cpu_module, 0, 0)
        grid.addWidget(self.gpu_module, 0, 1)
        grid.addWidget(self.memory_module, 0, 2)
        grid.addWidget(self.network_module, 1, 0)
        grid.addWidget(self.thermal_module, 1, 1)
        grid.addWidget(self.disk_module, 1, 2)
        
        layout.addLayout(grid)
        layout.addStretch()
    
    def update_stats(self, stats: dict) -> None:
        """Update all module displays with new hardware stats"""
        # CPU Module
        cpu_percent = stats.get('cpu_percent', 0)
        cpu_freq = stats.get('cpu_freq', 0)
        self.cpu_module.set_primary_value(f"{cpu_percent:.1f}%")
        self.cpu_module.set_secondary_value(f"{cpu_freq:.0f} MHz")
        self._update_cpu_hazard(cpu_percent)
        
        # GPU Module
        gpu_temp = stats.get('gpu_temp', 0)
        gpu_util = stats.get('gpu_util', 0)
        self.gpu_module.set_primary_value(f"{gpu_temp}°C")
        self.gpu_module.set_secondary_value(f"{gpu_util}% Load")
        self._update_gpu_hazard(gpu_temp)
        
        # Memory Module
        ram_percent = stats.get('ram_percent', 0)
        ram_used = stats.get('ram_used_gb', 0)
        ram_total = stats.get('ram_total_gb', 0)
        self.memory_module.set_primary_value(f"{ram_percent:.1f}%")
        self.memory_module.set_secondary_value(f"{ram_used:.1f}/{ram_total:.1f} GB")
        self._update_memory_hazard(ram_percent)
        
        # Network Module
        net_sent = stats.get('net_sent_mb', 0)
        net_recv = stats.get('net_recv_mb', 0)
        self.network_module.set_primary_value(f"↑ {net_sent:.1f} MB")
        self.network_module.set_secondary_value(f"↓ {net_recv:.1f} MB")
        
        # Thermal Module
        cpu_temp = stats.get('cpu_temp', 0)
        self.thermal_module.set_primary_value(f"{cpu_temp:.1f}°C")
        self.thermal_module.set_secondary_value(f"GPU: {gpu_temp}°C")
        self._update_thermal_hazard(cpu_temp, gpu_temp)
        
        # Disk Module
        disk_percent = stats.get('disk_percent', 0)
        disk_used = stats.get('disk_used_gb', 0)
        disk_total = stats.get('disk_total_gb', 0)
        self.disk_module.set_primary_value(f"{disk_percent:.1f}%")
        self.disk_module.set_secondary_value(f"{disk_used:.0f}/{disk_total:.0f} GB")
        self._update_disk_hazard(disk_percent)
    
    def _update_cpu_hazard(self, cpu_percent: float) -> None:
        """Update CPU hazard sticker based on usage"""
        if cpu_percent > 95:
            self.cpu_module.set_hazard_level("CRITICAL", "#ff3333")
        elif cpu_percent > 80:
            self.cpu_module.set_hazard_level("WARNING", "#ff8c00")
        elif cpu_percent > 60:
            self.cpu_module.set_hazard_level("ELEVATED", "#ffcc00")
        else:
            self.cpu_module.set_hazard_level("NORMAL", "#00ff88")
    
    def _update_gpu_hazard(self, gpu_temp: float) -> None:
        """Update GPU hazard sticker based on temperature"""
        if gpu_temp > 85:
            self.gpu_module.set_hazard_level("CRITICAL", "#ff3333")
        elif gpu_temp > 75:
            self.gpu_module.set_hazard_level("WARNING", "#ff8c00")
        elif gpu_temp > 65:
            self.gpu_module.set_hazard_level("ELEVATED", "#ffcc00")
        else:
            self.gpu_module.set_hazard_level("NORMAL", "#00ff88")
    
    def _update_memory_hazard(self, ram_percent: float) -> None:
        """Update memory hazard sticker based on usage"""
        if ram_percent > 95:
            self.memory_module.set_hazard_level("CRITICAL", "#ff3333")
        elif ram_percent > 85:
            self.memory_module.set_hazard_level("WARNING", "#ff8c00")
        elif ram_percent > 70:
            self.memory_module.set_hazard_level("ELEVATED", "#ffcc00")
        else:
            self.memory_module.set_hazard_level("NORMAL", "#00ff88")
    
    def _update_thermal_hazard(self, cpu_temp: float, gpu_temp: float) -> None:
        """Update thermal hazard sticker based on max temperature"""
        max_temp = max(cpu_temp, gpu_temp)
        
        if max_temp > 90:
            self.thermal_module.set_hazard_level("CRITICAL", "#ff3333")
        elif max_temp > 80:
            self.thermal_module.set_hazard_level("WARNING", "#ff8c00")
        elif max_temp > 70:
            self.thermal_module.set_hazard_level("ELEVATED", "#ffcc00")
        else:
            self.thermal_module.set_hazard_level("NORMAL", "#00ff88")
    
    def _update_disk_hazard(self, disk_percent: float) -> None:
        """Update disk hazard sticker based on usage"""
        if disk_percent > 95:
            self.disk_module.set_hazard_level("CRITICAL", "#ff3333")
        elif disk_percent > 85:
            self.disk_module.set_hazard_level("WARNING", "#ff8c00")
        elif disk_percent > 75:
            self.disk_module.set_hazard_level("ELEVATED", "#ffcc00")
        else:
            self.disk_module.set_hazard_level("NORMAL", "#00ff88")
