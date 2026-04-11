"""
Vitreos Monitoring Modules - Dashboard Widgets
Individual monitoring components for the 2x3 grid layout
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font, get_color
from src.ui.vitreos_widgets import VitreosWinFrame, VitreosSegmentedBar, VitreosVerticalBar
from src.core.vitreos_telemetry import TelemetryWorker


# ═══════════════════════════════════════════════════════════════════════════
# CPU MONITOR - Comprehensive CPU Dashboard
# ═══════════════════════════════════════════════════════════════════════════

class CpuMonitor(VitreosWinFrame):
    """CPU monitoring widget with per-core activity grid."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="CPU_MONITOR",
            accent_color="cyan",
            badge="OC",
            badge_color="warning_orange",
            parent=parent
        )
        
        self.detected_cores = 16  # Default, will be updated dynamically
        self._setup_content()
    
    def _setup_content(self) -> None:
        """Build CPU monitor layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # CPU Name (dynamic)
        self.name_label = QLabel("DETECTING CPU...")
        self.name_label.setFont(get_font('mono', FONT_SIZES['title']))
        self.name_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        layout.addWidget(self.name_label)
        
        self.specs_label = QLabel("INITIALIZING...")
        self.specs_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        self.specs_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.specs_label)
        
        # Total Load Bar
        load_layout = QVBoxLayout()
        load_layout.setSpacing(4)
        
        load_header = QHBoxLayout()
        load_label = QLabel("TOTAL LOAD")
        load_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        load_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        load_header.addWidget(load_label)
        load_header.addStretch()
        
        self.load_value_label = QLabel("0%")
        self.load_value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.load_value_label.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
        load_header.addWidget(self.load_value_label)
        
        load_layout.addLayout(load_header)
        
        self.load_bar = VitreosSegmentedBar(segments=22, height=6)
        load_layout.addWidget(self.load_bar)
        
        layout.addLayout(load_layout)
        
        # Package Temp Bar
        temp_layout = QVBoxLayout()
        temp_layout.setSpacing(4)
        
        temp_header = QHBoxLayout()
        temp_label = QLabel("PACKAGE TEMP")
        temp_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        temp_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        temp_header.addWidget(temp_label)
        temp_header.addStretch()
        
        self.temp_value_label = QLabel("0°C")
        self.temp_value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.temp_value_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        temp_header.addWidget(self.temp_value_label)
        
        temp_layout.addLayout(temp_header)
        
        self.temp_bar = VitreosSegmentedBar(segments=22, height=6, color='cyan')
        temp_layout.addWidget(self.temp_bar)
        
        layout.addLayout(temp_layout)
        
        # Per-core grid
        cores_label = QLabel("PER-CORE ACTIVITY")
        cores_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        cores_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(cores_label)
        
        self.cores_grid = QGridLayout()
        self.cores_grid.setSpacing(3)
        self.core_bars: List[VitreosVerticalBar] = []
        self.core_widgets: List[QWidget] = []
        
        # Create initial grid (will be rebuilt dynamically)
        self._rebuild_core_grid()
        
        layout.addLayout(self.cores_grid)
        layout.addStretch()
        
        self.set_content_layout(layout)
    
    def _rebuild_core_grid(self) -> None:
        """Rebuild core grid based on detected core count."""
        # Clear existing widgets
        for widget in self.core_widgets:
            self.cores_grid.removeWidget(widget)
            widget.deleteLater()
        self.core_bars.clear()
        self.core_widgets.clear()
        
        # Calculate grid dimensions
        cols = 4
        rows = (self.detected_cores + cols - 1) // cols
        
        for i in range(self.detected_cores):
            row = i // cols
            col = i % cols
            
            core_widget = QWidget()
            core_widget.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_primary']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
            """)
            core_layout = QVBoxLayout(core_widget)
            core_layout.setContentsMargins(4, 4, 4, 4)
            core_layout.setSpacing(2)
            
            core_label = QLabel(f"C{i}")
            core_label.setFont(get_font('mono', FONT_SIZES['micro']))
            core_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            core_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            core_layout.addWidget(core_label)
            
            bar = VitreosVerticalBar(segments=7, width=12)
            core_layout.addWidget(bar, alignment=Qt.AlignmentFlag.AlignCenter)
            self.core_bars.append(bar)
            
            self.cores_grid.addWidget(core_widget, row, col)
            self.core_widgets.append(core_widget)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update CPU monitor with fresh data."""
        # Update CPU name dynamically
        cpu_name = data.get('name', 'Unknown CPU')
        if hasattr(self, 'name_label'):
            self.name_label.setText(cpu_name.upper())
        
        # Update specs with physical/logical core split
        physical_cores = data.get('physicalCores', 0)
        logical_threads = data.get('logicalThreads', 0)
        if hasattr(self, 'specs_label'):
            if physical_cores > 0 and logical_threads > 0:
                # Phase 4: Display format - "8 PHYSICAL CORES | 16 LOGICAL THREADS"
                self.specs_label.setText(f"{physical_cores} PHYSICAL CORES | {logical_threads} LOGICAL THREADS")
            else:
                core_count = data.get('coreCount', 0)
                self.specs_label.setText(f"{core_count} LOGICAL CORES")
        
        # Rebuild core grid if core count changed
        core_count = data.get('coreCount', 0)
        if core_count != self.detected_cores:
            self.detected_cores = core_count
            self._rebuild_core_grid()
        
        # Total load
        total_load = data.get('totalLoad', 0)
        self.load_value_label.setText(f"{total_load:.0f}%")
        self.load_bar.set_value(total_load, 100)
        
        # Temperature
        temp = data.get('temp', 0)
        self.temp_value_label.setText(f"{temp:.0f}°C")
        self.temp_bar.set_value(temp, 100)
        
        # Update temp color if critical
        if temp > 85:
            self.temp_value_label.setStyleSheet(f"color: {VITREOS_COLORS['critical_red']};")
        else:
            self.temp_value_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        
        # Per-core usage
        cores = data.get('cores', [])
        for i, bar in enumerate(self.core_bars):
            if i < len(cores):
                bar.set_value(cores[i], 100)


# ═══════════════════════════════════════════════════════════════════════════
# GPU MONITOR - Dynamic Hardware Detection
# ═══════════════════════════════════════════════════════════════════════════

class GpuMonitor(VitreosWinFrame):
    """GPU monitoring widget with dynamic hardware detection."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="GPU_MONITOR",
            accent_color="warning_orange",
            badge="GPU",
            badge_color="warning_orange",
            parent=parent
        )
        
        self._setup_content()
    
    def _setup_content(self) -> None:
        """Build GPU monitor layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # GPU Name (dynamic)
        self.name_label = QLabel("DETECTING GPU...")
        self.name_label.setFont(get_font('mono', FONT_SIZES['title']))
        self.name_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        layout.addWidget(self.name_label)
        
        self.specs_label = QLabel("INITIALIZING...")
        self.specs_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        self.specs_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.specs_label)
        
        # GPU Usage Bar
        usage_layout = QVBoxLayout()
        usage_layout.setSpacing(4)
        
        usage_header = QHBoxLayout()
        usage_label = QLabel("GPU USAGE")
        usage_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        usage_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        usage_header.addWidget(usage_label)
        usage_header.addStretch()
        
        self.usage_value_label = QLabel("0%")
        self.usage_value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.usage_value_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        usage_header.addWidget(self.usage_value_label)
        
        usage_layout.addLayout(usage_header)
        
        self.usage_bar = VitreosSegmentedBar(segments=22, height=6, color='warning_orange')
        usage_layout.addWidget(self.usage_bar)
        
        layout.addLayout(usage_layout)
        
        # VRAM Bar
        vram_layout = QVBoxLayout()
        vram_layout.setSpacing(4)
        
        vram_header = QHBoxLayout()
        vram_label = QLabel("VRAM USAGE")
        vram_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        vram_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        vram_header.addWidget(vram_label)
        vram_header.addStretch()
        
        self.vram_value_label = QLabel("0.0 / 12.0 GB")
        self.vram_value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.vram_value_label.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
        vram_header.addWidget(self.vram_value_label)
        
        vram_layout.addLayout(vram_header)
        
        self.vram_bar = VitreosSegmentedBar(segments=22, height=6, color='purple_dim')
        vram_layout.addWidget(self.vram_bar)
        
        layout.addLayout(vram_layout)
        
        # Stats grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(8)
        
        self.stat_labels = {}
        stats = [
            ('CORE CLOCK', 'coreClock', 'MHz'),
            ('MEM CLOCK', 'memClock', 'MHz'),
            ('POWER', 'power', 'W'),
            ('TEMP', 'temp', '°C'),
        ]
        
        for i, (label, key, unit) in enumerate(stats):
            row = i // 2
            col = i % 2
            
            stat_widget = QWidget()
            stat_widget.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
                padding: 8px;
            """)
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setSpacing(4)
            
            stat_label = QLabel(label)
            stat_label.setFont(get_font('mono', FONT_SIZES['micro']))
            stat_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            stat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(stat_label)
            
            value_label = QLabel(f"0 {unit}")
            value_label.setFont(get_font('mono', FONT_SIZES['value_large']))
            value_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            
            self.stat_labels[key] = value_label
            stats_grid.addWidget(stat_widget, row, col)
        
        layout.addLayout(stats_grid)
        layout.addStretch()
        
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update GPU monitor with fresh data."""
        # Update GPU name dynamically
        gpu_name = data.get('name', 'NO GPU')
        if hasattr(self, 'name_label'):
            # Clean up name (remove "NVIDIA GeForce" prefix for brevity)
            display_name = gpu_name.replace('NVIDIA GeForce ', '').replace('GeForce ', '').upper()
            self.name_label.setText(display_name)
        
        # Update specs dynamically
        vram_total = data.get('vramTotal', 0)
        if hasattr(self, 'specs_label') and vram_total > 0:
            # Determine architecture from name or VRAM size
            if 'RTX 40' in gpu_name or vram_total >= 24:
                arch = "ADA LOVELACE"
            elif 'RTX 30' in gpu_name or (vram_total >= 8 and vram_total < 24):
                arch = "AMPERE"
            elif 'RTX 20' in gpu_name:
                arch = "TURING"
            elif 'GTX 16' in gpu_name:
                arch = "TURING"
            else:
                arch = "UNKNOWN"
            
            self.specs_label.setText(f"{vram_total:.0f}GB GDDR6 | {arch}")
        
        # GPU Usage
        usage = data.get('usage', 0)
        self.usage_value_label.setText(f"{usage:.0f}%")
        self.usage_bar.set_value(usage, 100)
        
        # VRAM (use percentage from telemetry)
        vram_used = data.get('vramUsed', 0)
        vram_percent = data.get('vramPercent', 0)
        self.vram_value_label.setText(f"{vram_used:.1f} / {vram_total:.1f} GB")
        self.vram_bar.set_value(vram_percent, 100)
        
        # Stats
        core_clock = data.get('coreClock', 0)
        self.stat_labels['coreClock'].setText(f"{core_clock} MHz")
        
        mem_clock = data.get('memClock', 0)
        self.stat_labels['memClock'].setText(f"{mem_clock} MHz")
        
        power = data.get('power', 0)
        self.stat_labels['power'].setText(f"{power:.0f} W")
        
        temp = data.get('temp', 0)
        self.stat_labels['temp'].setText(f"{temp:.0f} °C")
        
        # Use status flag from telemetry for color
        status = data.get('status', 'normal')
        if status == 'critical':
            self.stat_labels['temp'].setStyleSheet(f"color: {VITREOS_COLORS['critical_red']};")
        elif status == 'warning':
            self.stat_labels['temp'].setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        else:
            self.stat_labels['temp'].setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")


# ═══════════════════════════════════════════════════════════════════════════
# PLACEHOLDER MODULES (To be implemented)
# ═══════════════════════════════════════════════════════════════════════════

class ThermalCtrl(VitreosWinFrame):
    """Thermal monitoring widget with sensor matrix."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="THERMAL_CTRL", accent_color="cyan", parent=parent)
        self._setup_content()
    
    def _setup_content(self) -> None:
        """Build thermal monitor layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Sensor Matrix Header
        header = QLabel("SENSOR MATRIX")
        header.setFont(get_font('mono', FONT_SIZES['label']))
        header.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        layout.addWidget(header)
        
        # CPU Temperature
        cpu_layout = QVBoxLayout()
        cpu_layout.setSpacing(4)
        
        cpu_header = QHBoxLayout()
        cpu_label = QLabel("CPU PACKAGE")
        cpu_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        cpu_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        cpu_header.addWidget(cpu_label)
        cpu_header.addStretch()
        
        self.cpu_temp_label = QLabel("0°C")
        self.cpu_temp_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.cpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        cpu_header.addWidget(self.cpu_temp_label)
        
        cpu_layout.addLayout(cpu_header)
        
        self.cpu_temp_bar = VitreosSegmentedBar(segments=22, height=6, color='cyan')
        cpu_layout.addWidget(self.cpu_temp_bar)
        
        layout.addLayout(cpu_layout)
        
        # GPU Temperature
        gpu_layout = QVBoxLayout()
        gpu_layout.setSpacing(4)
        
        gpu_header = QHBoxLayout()
        gpu_label = QLabel("GPU CORE")
        gpu_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        gpu_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        gpu_header.addWidget(gpu_label)
        gpu_header.addStretch()
        
        self.gpu_temp_label = QLabel("0°C")
        self.gpu_temp_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.gpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        gpu_header.addWidget(self.gpu_temp_label)
        
        gpu_layout.addLayout(gpu_header)
        
        self.gpu_temp_bar = VitreosSegmentedBar(segments=22, height=6, color='warning_orange')
        gpu_layout.addWidget(self.gpu_temp_bar)
        
        layout.addLayout(gpu_layout)
        
        # Thermal Status Grid
        status_grid = QGridLayout()
        status_grid.setSpacing(8)
        
        self.status_labels = {}
        sensors = [
            ('CPU MAX', 'cpu_max', '°C'),
            ('GPU MAX', 'gpu_max', '°C'),
            ('MOBO', 'mobo', '°C'),
            ('CASE', 'case', '°C'),
        ]
        
        for i, (label, key, unit) in enumerate(sensors):
            row = i // 2
            col = i % 2
            
            sensor_widget = QWidget()
            sensor_widget.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
                padding: 8px;
            """)
            sensor_layout = QVBoxLayout(sensor_widget)
            sensor_layout.setSpacing(4)
            
            sensor_label = QLabel(label)
            sensor_label.setFont(get_font('mono', FONT_SIZES['micro']))
            sensor_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            sensor_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sensor_layout.addWidget(sensor_label)
            
            value_label = QLabel(f"0{unit}")
            value_label.setFont(get_font('mono', FONT_SIZES['value_large']))
            value_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sensor_layout.addWidget(value_label)
            
            self.status_labels[key] = value_label
            status_grid.addWidget(sensor_widget, row, col)
        
        layout.addLayout(status_grid)
        layout.addStretch()
        
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update thermal monitor with sensor data."""
        # CPU Temperature (from cpu data)
        cpu_temp = data.get('cpuTemp', 0)
        self.cpu_temp_label.setText(f"{cpu_temp:.0f}°C")
        self.cpu_temp_bar.set_value(cpu_temp, 100)
        
        if cpu_temp > 85:
            self.cpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['critical_red']};")
        elif cpu_temp > 75:
            self.cpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        else:
            self.cpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        
        # GPU Temperature (from gpu data)
        gpu_temp = data.get('gpuTemp', 0)
        self.gpu_temp_label.setText(f"{gpu_temp:.0f}°C")
        self.gpu_temp_bar.set_value(gpu_temp, 100)
        
        if gpu_temp > 85:
            self.gpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['critical_red']};")
        elif gpu_temp > 75:
            self.gpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        else:
            self.gpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        
        # Status grid (use same temps for now)
        self.status_labels['cpu_max'].setText(f"{cpu_temp:.0f}°C")
        self.status_labels['gpu_max'].setText(f"{gpu_temp:.0f}°C")
        
        # Placeholder for mobo/case (not in telemetry yet)
        self.status_labels['mobo'].setText("N/A")
        self.status_labels['case'].setText("N/A")


class StorageArray(VitreosWinFrame):
    """Storage monitoring widget with drive array."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="STORAGE_ARRAY", accent_color="primary_purple", parent=parent)
        self.drive_widgets: Dict[str, tuple] = {}  # mountpoint -> (label, bar)
        self._setup_content()
    
    def _setup_content(self) -> None:
        """Build storage monitor layout."""
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)
        
        header = QLabel("DRIVE ARRAY")
        header.setFont(get_font('mono', FONT_SIZES['label']))
        header.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        self.main_layout.addWidget(header)
        
        # Drives will be added dynamically
        self.drives_layout = QVBoxLayout()
        self.drives_layout.setSpacing(8)
        self.main_layout.addLayout(self.drives_layout)
        
        self.main_layout.addStretch()
        self.set_content_layout(self.main_layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update storage array with drive data."""
        drives = data.get('drives', [])
        
        # Create/update drive widgets
        for drive in drives:
            mountpoint = drive.get('mountpoint', '/')
            device = drive.get('device', 'Unknown')
            used_gb = drive.get('usedGB', 0)
            total_gb = drive.get('totalGB', 0)
            percent = drive.get('percent', 0)
            
            if mountpoint not in self.drive_widgets:
                # Create new drive widget
                drive_layout = QVBoxLayout()
                drive_layout.setSpacing(4)
                
                drive_header = QHBoxLayout()
                drive_label = QLabel(f"{device} ({mountpoint})")
                drive_label.setFont(get_font('mono', FONT_SIZES['tiny']))
                drive_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
                drive_header.addWidget(drive_label)
                drive_header.addStretch()
                
                usage_label = QLabel(f"{used_gb:.1f} / {total_gb:.1f} GB")
                usage_label.setFont(get_font('mono', FONT_SIZES['small']))
                usage_label.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
                drive_header.addWidget(usage_label)
                
                drive_layout.addLayout(drive_header)
                
                drive_bar = VitreosSegmentedBar(segments=22, height=6, color='primary_purple')
                drive_layout.addWidget(drive_bar)
                
                self.drives_layout.addLayout(drive_layout)
                self.drive_widgets[mountpoint] = (usage_label, drive_bar)
            else:
                # Update existing drive widget
                usage_label, drive_bar = self.drive_widgets[mountpoint]
                usage_label.setText(f"{used_gb:.1f} / {total_gb:.1f} GB")
                drive_bar.set_value(percent, 100)


class MemoryArray(VitreosWinFrame):
    """Memory monitoring widget with RAM usage."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="MEMORY_ARRAY", accent_color="purple_dim", parent=parent)
        self._setup_content()
    
    def _setup_content(self) -> None:
        """Build memory monitor layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        header = QLabel("RAM USAGE")
        header.setFont(get_font('mono', FONT_SIZES['label']))
        header.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        layout.addWidget(header)
        
        # Memory Usage Bar
        mem_layout = QVBoxLayout()
        mem_layout.setSpacing(4)
        
        mem_header = QHBoxLayout()
        mem_label = QLabel("SYSTEM MEMORY")
        mem_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        mem_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        mem_header.addWidget(mem_label)
        mem_header.addStretch()
        
        self.mem_value_label = QLabel("0.0 / 0.0 GB")
        self.mem_value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.mem_value_label.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
        mem_header.addWidget(self.mem_value_label)
        
        mem_layout.addLayout(mem_header)
        
        self.mem_bar = VitreosSegmentedBar(segments=22, height=6, color='purple_dim')
        mem_layout.addWidget(self.mem_bar)
        
        layout.addLayout(mem_layout)
        
        # Memory Stats Grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(8)
        
        self.stat_labels = {}
        stats = [
            ('USED', 'used', 'GB'),
            ('FREE', 'free', 'GB'),
            ('PERCENT', 'percent', '%'),
            ('TOTAL', 'total', 'GB'),
        ]
        
        for i, (label, key, unit) in enumerate(stats):
            row = i // 2
            col = i % 2
            
            stat_widget = QWidget()
            stat_widget.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
                padding: 8px;
            """)
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setSpacing(4)
            
            stat_label = QLabel(label)
            stat_label.setFont(get_font('mono', FONT_SIZES['micro']))
            stat_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            stat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(stat_label)
            
            value_label = QLabel(f"0 {unit}")
            value_label.setFont(get_font('mono', FONT_SIZES['value_large']))
            value_label.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            
            self.stat_labels[key] = value_label
            stats_grid.addWidget(stat_widget, row, col)
        
        layout.addLayout(stats_grid)
        layout.addStretch()
        
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update memory monitor with RAM data."""
        used_gb = data.get('usedGB', 0)
        total_gb = data.get('totalGB', 0)
        percent = data.get('percent', 0)
        free_gb = total_gb - used_gb
        
        # Main bar
        self.mem_value_label.setText(f"{used_gb:.1f} / {total_gb:.1f} GB")
        self.mem_bar.set_value(percent, 100)
        
        # Stats grid
        self.stat_labels['used'].setText(f"{used_gb:.1f} GB")
        self.stat_labels['free'].setText(f"{free_gb:.1f} GB")
        self.stat_labels['percent'].setText(f"{percent:.0f}%")
        self.stat_labels['total'].setText(f"{total_gb:.1f} GB")


class NetInterface(VitreosWinFrame):
    """Network monitoring widget - networking-only telemetry (no process hogs)."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="NET_INTERFACE", accent_color="green", parent=parent)
        self.telemetry_worker: Optional[TelemetryWorker] = None
        self.download_history: List[float] = [0.0] * 60
        self.upload_history: List[float] = [0.0] * 60
        self._setup_content()
    
    def _setup_content(self) -> None:
        """Build optimized network layout (40% top info, 60% waveform)."""
        from PyQt6.QtWidgets import QComboBox
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Top 40%: Adapter Info + NIC Matrix
        top_section = QVBoxLayout()
        top_section.setSpacing(4)  # Tightened from 8px to 4px
        
        # Adapter dropdown
        adapter_label = QLabel("ACTIVE INTERFACE")
        adapter_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        adapter_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        top_section.addWidget(adapter_label)
        
        self.adapter_combo = QComboBox()
        self.adapter_combo.setFont(get_font('mono', 8))
        self.adapter_combo.setStyleSheet(f"""
            QComboBox {{
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
                padding: 6px;
                color: {VITREOS_COLORS['green']};;
            }}
        """)
        self.adapter_combo.currentTextChanged.connect(self._on_adapter_changed)
        top_section.addWidget(self.adapter_combo)
        
        # NIC Matrix (4x4 grid) - centered with border
        nic_label = QLabel("NIC MATRIX")
        nic_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        nic_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        top_section.addWidget(nic_label)
        
        # Matrix container with border and fixed max height
        nic_container = QWidget()
        nic_container.setMaximumHeight(120)  # Fixed max height to prevent crushing
        nic_container.setStyleSheet(f"""
            background: {VITREOS_COLORS['bg_card']};
            border: 1px solid {VITREOS_COLORS['border_secondary']};
        """)
        nic_container_layout = QVBoxLayout(nic_container)
        nic_container_layout.setContentsMargins(8, 8, 8, 8)
        
        nic_grid = QGridLayout()
        nic_grid.setSpacing(3)
        nic_grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nic_widgets: List[QWidget] = []
        
        for i in range(16):
            row, col = i // 4, i % 4
            nic_cell = NICMicroWaveform()
            nic_grid.addWidget(nic_cell, row, col)
            self.nic_widgets.append(nic_cell)
        
        nic_container_layout.addLayout(nic_grid)
        top_section.addWidget(nic_container)
        layout.addLayout(top_section)
        
        # Bottom 60%: Bandwidth Waveform
        bandwidth_label = QLabel("BANDWIDTH WAVEFORM")
        bandwidth_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        bandwidth_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        layout.addWidget(bandwidth_label)
        
        self.waveform = BandwidthWaveform()
        self.waveform.setMinimumHeight(180)
        layout.addWidget(self.waveform, 3)  # Stretch factor 3 for 60% height
        
        # Centered readouts - NUCLEAR FIX: No addStretch, perfect centering
        readouts = QHBoxLayout()
        readouts.setSpacing(0)  # Remove spacing, let alignment handle it
        readouts.setContentsMargins(0, 8, 0, 0)
        readouts.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the entire layout
        
        # Download
        dl_layout = QVBoxLayout()
        dl_layout.setSpacing(2)
        dl_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        dl_label = QLabel("DOWNLOAD")
        dl_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        dl_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        dl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dl_label.setFixedWidth(100)  # Fixed width for alignment
        dl_layout.addWidget(dl_label)
        
        self.download_value = QLabel("0.00 Mbps")
        self.download_value.setFont(get_font('mono', 13))
        self.download_value.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        self.download_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.download_value.setFixedWidth(100)
        dl_layout.addWidget(self.download_value)
        readouts.addLayout(dl_layout)
        
        # Upload
        ul_layout = QVBoxLayout()
        ul_layout.setSpacing(2)
        ul_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        ul_label = QLabel("UPLOAD")
        ul_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        ul_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        ul_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ul_label.setFixedWidth(100)
        ul_layout.addWidget(ul_label)
        
        self.upload_value = QLabel("0.00 Mbps")
        self.upload_value.setFont(get_font('mono', 13))
        self.upload_value.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        self.upload_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.upload_value.setFixedWidth(100)
        ul_layout.addWidget(self.upload_value)
        readouts.addLayout(ul_layout)
        
        # Latency
        lat_layout = QVBoxLayout()
        lat_layout.setSpacing(2)
        lat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lat_label = QLabel("LATENCY")
        lat_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        lat_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        lat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lat_label.setFixedWidth(100)
        lat_layout.addWidget(lat_label)
        
        self.latency_value = QLabel("0 ms")
        self.latency_value.setFont(get_font('mono', 13))
        self.latency_value.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        self.latency_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.latency_value.setFixedWidth(100)
        lat_layout.addWidget(self.latency_value)
        readouts.addLayout(lat_layout)
        
        layout.addLayout(readouts)
        
        self.set_content_layout(layout)
    
    def _on_adapter_changed(self, adapter_name: str) -> None:
        """Sync adapter change with telemetry worker."""
        if self.telemetry_worker and adapter_name:
            self.telemetry_worker.set_active_adapter(adapter_name)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update network monitor - networking telemetry only."""
        # Populate adapter dropdown if empty
        if self.adapter_combo.count() == 0:
            interfaces = data.get('interfaces', [])
            for iface in interfaces:
                self.adapter_combo.addItem(iface['name'])
            
            # Set primary adapter
            primary = data.get('primaryNic', '')
            if primary:
                idx = self.adapter_combo.findText(primary)
                if idx >= 0:
                    self.adapter_combo.setCurrentIndex(idx)
        
        # Update NIC matrix
        interfaces = data.get('interfaces', [])
        for i, nic_widget in enumerate(self.nic_widgets):
            if i < len(interfaces):
                iface = interfaces[i]
                status = iface.get('status', 'idle')
                nic_widget.set_status(status)
            else:
                nic_widget.set_status('idle')
        
        # Update bandwidth
        download = data.get('downloadMbps', 0)
        upload = data.get('uploadMbps', 0)
        
        self.download_value.setText(f"{download:.2f} Mbps")
        self.upload_value.setText(f"{upload:.2f} Mbps")
        
        # Update waveform history
        self.download_history.append(download)
        self.upload_history.append(upload)
        if len(self.download_history) > 60:
            self.download_history.pop(0)
            self.upload_history.pop(0)
        
        self.waveform.set_data(self.download_history, self.upload_history)
        
        # Update latency
        latency = data.get('latency', 0)
        self.latency_value.setText(f"{latency:.0f} ms")
        
        # Signal Silencing: No network hogs processing


class NICMicroWaveform(QWidget):
    """Micro waveform for NIC matrix (4x4 grid)."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.status = 'idle'
        self.setFixedSize(40, 30)
    
    def set_status(self, status: str) -> None:
        """Set NIC status: 'active' (cyan) or 'idle' (amber)."""
        self.status = status
        self.update()
    
    def paintEvent(self, event) -> None:
        """Draw micro waveform."""
        from PyQt6.QtGui import QPainter, QPen, QColor
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(0, 0, self.width(), self.height(), QColor(VITREOS_COLORS['bg_card']))
        
        # Border
        painter.setPen(QPen(QColor(VITREOS_COLORS['border_secondary']), 1))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        
        # Waveform color
        if self.status == 'active':
            color = QColor(VITREOS_COLORS['cyan'])
        else:
            color = QColor(VITREOS_COLORS['warning_orange'])
        
        painter.setPen(QPen(color, 1))
        
        # Draw simple waveform pattern
        import random
        random.seed(id(self))  # Consistent pattern per widget
        
        for x in range(0, self.width(), 2):
            y = self.height() // 2 + random.randint(-8, 8)
            painter.drawLine(x, self.height() // 2, x, y)


class BandwidthWaveform(QWidget):
    """Dual-colored bandwidth waveform graph."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.download_data: List[float] = [0.0] * 60
        self.upload_data: List[float] = [0.0] * 60
    
    def set_data(self, download: List[float], upload: List[float]) -> None:
        """Update waveform data."""
        self.download_data = download[-60:]
        self.upload_data = upload[-60:]
        self.update()
    
    def paintEvent(self, event) -> None:
        """Draw dual-colored waveform."""
        from PyQt6.QtGui import QPainter, QPen, QColor
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background
        painter.fillRect(0, 0, width, height, QColor(VITREOS_COLORS['bg_card']))
        
        # Grid lines
        painter.setPen(QPen(QColor(VITREOS_COLORS['border_secondary']), 1))
        for i in range(0, height, 20):
            painter.drawLine(0, i, width, i)
        
        # Find max for scaling
        max_val = max(max(self.download_data + self.upload_data, default=1), 1)
        
        # Draw download (cyan)
        painter.setPen(QPen(QColor(VITREOS_COLORS['cyan']), 2))
        for i in range(1, len(self.download_data)):
            x1 = int((i - 1) * width / 60)
            y1 = int(height - (self.download_data[i - 1] / max_val * height))
            x2 = int(i * width / 60)
            y2 = int(height - (self.download_data[i] / max_val * height))
            painter.drawLine(x1, y1, x2, y2)
        
        # Draw upload (orange)
        painter.setPen(QPen(QColor(VITREOS_COLORS['warning_orange']), 2))
        for i in range(1, len(self.upload_data)):
            x1 = int((i - 1) * width / 60)
            y1 = int(height - (self.upload_data[i - 1] / max_val * height))
            x2 = int(i * width / 60)
            y2 = int(height - (self.upload_data[i] / max_val * height))
            painter.drawLine(x1, y1, x2, y2)


# ═══════════════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'CpuMonitor',
    'GpuMonitor',
    'ThermalCtrl',
    'StorageArray',
    'MemoryArray',
    'NetInterface',
]


