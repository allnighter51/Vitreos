"""
Vitreos Monitoring Modules - Dashboard Widgets
Individual monitoring components for the 2x3 grid layout
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QPen, QColor
import random

from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font, get_color
from src.ui.vitreos_widgets import (
    VitreosWinFrame, VitreosSegmentedBar, VitreosVerticalBar,
    VitreosCircularGauge, VitreosBarcode, HazardBadge, OCBadge
)
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
            parent=parent
        )
        
        self.detected_cores = 16
        self._setup_content()
    
    def _setup_content(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(9, 9, 9, 9)  # Reduced by 25% from 12px
        layout.setSpacing(6)  # Reduced by 25% from 8px
        
        # Header with OC badge
        header_row = QHBoxLayout()
        header_row.setSpacing(6)
        
        self.name_label = QLabel("DETECTING CPU...")
        self.name_label.setFont(get_font('mono', FONT_SIZES['title']))
        self.name_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        header_row.addWidget(self.name_label)
        
        header_row.addStretch()
        
        # OC Badge with diagonal hazard stripes
        self.oc_badge = OCBadge("OC")
        header_row.addWidget(self.oc_badge)
        
        layout.addLayout(header_row)
        
        self.specs_label = QLabel("INITIALIZING...")
        self.specs_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        self.specs_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.specs_label)
        
        load_layout = QVBoxLayout()
        load_layout.setSpacing(3)  # Reduced by 25%
        
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
        
        temp_layout = QVBoxLayout()
        temp_layout.setSpacing(3)  # Reduced by 25%
        
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
        
        cores_label = QLabel("PER-CORE ACTIVITY")
        cores_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        cores_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(cores_label)
        
        self.cores_grid = QGridLayout()
        self.cores_grid.setSpacing(2)  # Reduced by 25% from 3px
        self.core_bars: List[VitreosVerticalBar] = []
        self.core_widgets: List[QWidget] = []
        
        self._rebuild_core_grid()
        
        layout.addLayout(self.cores_grid)
        layout.addStretch()
        
        self.set_content_layout(layout)
    
    def _rebuild_core_grid(self) -> None:
        for widget in self.core_widgets:
            self.cores_grid.removeWidget(widget)
            widget.deleteLater()
        self.core_bars.clear()
        self.core_widgets.clear()
        
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
            core_layout.setContentsMargins(3, 3, 3, 3)  # Reduced by 25%
            core_layout.setSpacing(1)  # Reduced by 25%
            
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
        cpu_name = data.get('name', 'Unknown CPU')
        if hasattr(self, 'name_label'):
            self.name_label.setText(cpu_name.upper())
        
        physical_cores = data.get('physicalCores', 0)
        logical_threads = data.get('logicalThreads', 0)
        if hasattr(self, 'specs_label'):
            if physical_cores > 0 and logical_threads > 0:
                self.specs_label.setText(f"{physical_cores} PHYSICAL CORES | {logical_threads} LOGICAL THREADS")
            else:
                core_count = data.get('coreCount', 0)
                self.specs_label.setText(f"{core_count} LOGICAL CORES")
        
        core_count = data.get('coreCount', 0)
        if core_count != self.detected_cores:
            self.detected_cores = core_count
            self._rebuild_core_grid()
        
        total_load = data.get('totalLoad', 0)
        self.load_value_label.setText(f"{total_load:.0f}%")
        self.load_bar.set_value(total_load, 100)
        
        temp = data.get('temp', 0)
        self.temp_value_label.setText(f"{temp:.0f}°C")
        self.temp_bar.set_value(temp, 100)
        
        if temp > 85:
            self.temp_value_label.setStyleSheet(f"color: {VITREOS_COLORS['critical_red']};")
        else:
            self.temp_value_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        
        cores = data.get('cores', [])
        for i, bar in enumerate(self.core_bars):
            if i < len(cores):
                bar.set_value(cores[i], 100)


# ═══════════════════════════════════════════════════════════════════════════
# GPU MONITOR - Figma V4 Design
# ═══════════════════════════════════════════════════════════════════════════

class GpuMonitor(VitreosWinFrame):
    """GPU monitoring widget with Figma V4 design."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="GPU_MONITOR",
            accent_color="warning_orange",
            badge="⚠",
            badge_color="critical_red",
            parent=parent
        )
        self._setup_content()
    
    def _setup_content(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(9, 9, 9, 9)  # Reduced by 25%
        layout.setSpacing(3)  # Reduced by 25%
        
        self.name_label = QLabel("NVIDIA RTX 3060")
        self.name_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.name_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        layout.addWidget(self.name_label)
        
        self.subtitle_label = QLabel("AMPERE // 12GB GDDR6")
        self.subtitle_label.setFont(get_font('mono', FONT_SIZES['micro']))
        self.subtitle_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.subtitle_label)
        
        header_row = QHBoxLayout()
        self.driver_label = QLabel("DRIVER: 000.00 WHQL")
        self.driver_label.setFont(get_font('mono', 7))
        self.driver_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
        header_row.addWidget(self.driver_label)
        header_row.addStretch()
        
        self.hazard_badge = HazardBadge("⚠ HOT")
        header_row.addWidget(self.hazard_badge)
        layout.addLayout(header_row)
        
        gauge_row = QHBoxLayout()
        gauge_row.setSpacing(6)
        
        self.vram_gauge = VitreosCircularGauge(segments=40)
        self.vram_gauge.setFixedSize(60, 60)
        gauge_row.addWidget(self.vram_gauge)
        
        self.barcode = VitreosBarcode(height=30)
        gauge_row.addWidget(self.barcode, 1)
        layout.addLayout(gauge_row)
        
        stats_grid = QGridLayout()
        stats_grid.setSpacing(4)
        
        self.stat_labels = {}
        stats = [
            ('CORE CLK', 'coreClock', 'MHz', 'primary_purple'),
            ('MEM CLK', 'memClock', 'MHz', 'cyan'),
            ('POWER', 'power', 'W', 'warning_orange'),
            ('TEMP', 'temp', '°C', 'critical_red'),
        ]
        
        for i, (label, key, unit, color) in enumerate(stats):
            stat_widget = QWidget()
            stat_widget.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
            """)
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(4, 4, 4, 4)
            stat_layout.setSpacing(2)
            
            stat_label = QLabel(label)
            stat_label.setFont(get_font('mono', 7))
            stat_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            stat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(stat_label)
            
            value_label = QLabel(f"0 {unit}")
            value_label.setFont(get_font('mono', FONT_SIZES['small']))
            value_label.setStyleSheet(f"color: {VITREOS_COLORS[color]};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            
            self.stat_labels[key] = value_label
            stats_grid.addWidget(stat_widget, 0, i)
        
        layout.addLayout(stats_grid)
        
        load_header = QHBoxLayout()
        load_label = QLabel("GPU LOAD")
        load_label.setFont(get_font('mono', FONT_SIZES['micro']))
        load_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        load_header.addWidget(load_label)
        load_header.addStretch()
        self.load_value = QLabel("0%")
        self.load_value.setFont(get_font('mono', FONT_SIZES['tiny']))
        self.load_value.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
        load_header.addWidget(self.load_value)
        layout.addLayout(load_header)
        
        self.load_bar = VitreosSegmentedBar(segments=24, height=6, color='primary_purple')
        layout.addWidget(self.load_bar)
        
        vram_header = QHBoxLayout()
        vram_label = QLabel("VRAM USAGE")
        vram_label.setFont(get_font('mono', FONT_SIZES['micro']))
        vram_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        vram_header.addWidget(vram_label)
        vram_header.addStretch()
        self.vram_value = QLabel("0.0 / 12.0 GB")
        self.vram_value.setFont(get_font('mono', FONT_SIZES['tiny']))
        self.vram_value.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
        vram_header.addWidget(self.vram_value)
        layout.addLayout(vram_header)
        
        self.vram_bar = VitreosSegmentedBar(segments=24, height=6, color='purple_dim')
        layout.addWidget(self.vram_bar)
        
        bw_header = QHBoxLayout()
        bw_label = QLabel("MEM BANDWIDTH")
        bw_label.setFont(get_font('mono', FONT_SIZES['micro']))
        bw_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        bw_header.addWidget(bw_label)
        bw_header.addStretch()
        self.bw_value = QLabel("0 GB/s")
        self.bw_value.setFont(get_font('mono', FONT_SIZES['tiny']))
        self.bw_value.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        bw_header.addWidget(self.bw_value)
        layout.addLayout(bw_header)
        
        self.bw_bar = VitreosSegmentedBar(segments=24, height=6, color='warning_orange')
        layout.addWidget(self.bw_bar)
        
        fan_label = QLabel("FAN ARRAY")
        fan_label.setFont(get_font('mono', FONT_SIZES['micro']))
        fan_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        layout.addWidget(fan_label)
        
        fan_row = QHBoxLayout()
        fan_row.setSpacing(4)
        
        self.fan_labels = {}
        for fan_id in ['FAN 1', 'FAN 2', 'REAR']:
            fan_card = QWidget()
            fan_card.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
            """)
            fan_layout = QVBoxLayout(fan_card)
            fan_layout.setContentsMargins(4, 4, 4, 4)
            fan_layout.setSpacing(2)
            
            fan_name = QLabel(fan_id)
            fan_name.setFont(get_font('mono', 7))
            fan_name.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            fan_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fan_layout.addWidget(fan_name)
            
            fan_rpm = QLabel("0 RPM")
            fan_rpm.setFont(get_font('mono', FONT_SIZES['tiny']))
            fan_rpm.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
            fan_rpm.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fan_layout.addWidget(fan_rpm)
            
            self.fan_labels[fan_id] = fan_rpm
            fan_row.addWidget(fan_card)
        
        layout.addLayout(fan_row)
        
        self.footer_label = QLabel("PCIe 4.0 ×16 — NVML 12.3")
        self.footer_label.setFont(get_font('mono', 7))
        self.footer_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.footer_label)
        
        layout.addStretch()
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        gpu_name = data.get('name', 'NO GPU')
        display_name = gpu_name.replace('NVIDIA GeForce ', '').replace('GeForce ', '').upper()
        self.name_label.setText(display_name)
        
        vram_total = data.get('vramTotal', 12)
        if 'RTX 40' in gpu_name or vram_total >= 24:
            arch = "ADA LOVELACE"
        elif 'RTX 30' in gpu_name:
            arch = "AMPERE"
        elif 'RTX 20' in gpu_name:
            arch = "TURING"
        else:
            arch = "AMPERE"
        self.subtitle_label.setText(f"{arch} // {vram_total:.0f}GB GDDR6")
        
        driver = data.get('driver', '000.00')
        self.driver_label.setText(f"DRIVER: {driver} WHQL")
        
        core_clock = data.get('coreClock', 0)
        self.stat_labels['coreClock'].setText(f"{core_clock} MHz")
        
        mem_clock = data.get('memClock', 0)
        self.stat_labels['memClock'].setText(f"{mem_clock} MHz")
        
        power = data.get('power', 0)
        self.stat_labels['power'].setText(f"{power:.0f} W")
        
        temp = data.get('temp', 0)
        self.stat_labels['temp'].setText(f"{temp:.0f} °C")
        
        usage = data.get('usage', 0)
        self.load_value.setText(f"{usage:.0f}%")
        self.load_bar.set_value(usage, 100)
        
        vram_used = data.get('vramUsed', 0)
        vram_percent = data.get('vramPercent', 0)
        self.vram_value.setText(f"{vram_used:.1f} / {vram_total:.1f} GB")
        self.vram_bar.set_value(vram_percent, 100)
        self.vram_gauge.set_value(vram_percent, 100, 'purple_dim')
        
        bandwidth = data.get('memBandwidth', 0)
        self.bw_value.setText(f"{bandwidth:.0f} GB/s")
        self.bw_bar.set_value(bandwidth, 500)
        
        fan_speed = data.get('fanSpeed', 0)
        fan_rpm = int(fan_speed * 30)
        self.fan_labels['FAN 1'].setText(f"{fan_rpm} RPM")
        self.fan_labels['FAN 2'].setText(f"{fan_rpm} RPM")
        self.fan_labels['REAR'].setText(f"{int(fan_rpm * 0.8)} RPM")


# ═══════════════════════════════════════════════════════════════════════════
# PLACEHOLDER MODULES
# ═══════════════════════════════════════════════════════════════════════════

class ThermalCtrl(VitreosWinFrame):
    """Thermal monitoring widget with sensor matrix."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="THERMAL_CTRL", accent_color="cyan", parent=parent)
        self._setup_content()
    
    def _setup_content(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(9, 9, 9, 9)  # Reduced by 25%
        layout.setSpacing(4)  # Reduced by 25%
        
        self.status_label = QLabel("SEARCHING...")
        self.status_label.setFont(get_font('mono', FONT_SIZES['title']))
        self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.status_label)
        
        # CPU Temperature
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
        layout.addLayout(cpu_header)
        
        self.cpu_temp_bar = VitreosSegmentedBar(segments=24, height=6, color='cyan')
        layout.addWidget(self.cpu_temp_bar)
        
        # GPU Temperature
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
        layout.addLayout(gpu_header)
        
        self.gpu_temp_bar = VitreosSegmentedBar(segments=24, height=6, color='warning_orange')
        layout.addWidget(self.gpu_temp_bar)
        
        # Thermal Status Grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(6)
        
        self.status_labels = {}
        sensors = [
            ('CPU MAX', 'cpu_max', '°C', 'cyan'),
            ('GPU MAX', 'gpu_max', '°C', 'warning_orange'),
            ('CPU AVG', 'cpu_avg', '°C', 'text_secondary'),
            ('GPU AVG', 'gpu_avg', '°C', 'text_secondary'),
        ]
        
        for i, (label, key, unit, color) in enumerate(sensors):
            sensor_widget = QWidget()
            sensor_widget.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
            """)
            sensor_layout = QVBoxLayout(sensor_widget)
            sensor_layout.setContentsMargins(6, 6, 6, 6)
            sensor_layout.setSpacing(2)
            
            sensor_label = QLabel(label)
            sensor_label.setFont(get_font('mono', FONT_SIZES['micro']))
            sensor_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            sensor_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sensor_layout.addWidget(sensor_label)
            
            value_label = QLabel(f"0{unit}")
            value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
            value_label.setStyleSheet(f"color: {VITREOS_COLORS[color]};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sensor_layout.addWidget(value_label)
            
            self.status_labels[key] = value_label
            stats_grid.addWidget(sensor_widget, i // 2, i % 2)
        
        layout.addLayout(stats_grid)
        layout.addStretch()
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        cpu_temp = data.get('cpuTemp', 0)
        gpu_temp = data.get('gpuTemp', 0)
        
        if cpu_temp > 0 or gpu_temp > 0:
            self.status_label.setText("ONLINE")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        else:
            self.status_label.setText("OFFLINE")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        
        self.cpu_temp_label.setText(f"{cpu_temp:.0f}°C")
        self.cpu_temp_bar.set_value(cpu_temp, 100)
        
        if cpu_temp > 85:
            self.cpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['critical_red']};")
        elif cpu_temp > 75:
            self.cpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        else:
            self.cpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        
        self.gpu_temp_label.setText(f"{gpu_temp:.0f}°C")
        self.gpu_temp_bar.set_value(gpu_temp, 100)
        
        if gpu_temp > 85:
            self.gpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['critical_red']};")
        elif gpu_temp > 75:
            self.gpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        else:
            self.gpu_temp_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        
        self.status_labels['cpu_max'].setText(f"{cpu_temp:.0f}°C")
        self.status_labels['gpu_max'].setText(f"{gpu_temp:.0f}°C")
        self.status_labels['cpu_avg'].setText(f"{cpu_temp:.0f}°C")
        self.status_labels['gpu_avg'].setText(f"{gpu_temp:.0f}°C")


# ═══════════════════════════════════════════════════════════════════════════
# DRIVE CARD WIDGET - Single physical drive representation (Figma V4)
# ═══════════════════════════════════════════════════════════════════════════

class DriveCardWidget(QWidget):
    """Single drive card matching Figma V4 StorageArray DriveRow spec."""

    def __init__(self, drive_type: str, model: str, serial: str,
                 temp: int, used_gb: float, total_gb: float,
                 read_speed: float, write_speed: float,
                 max_read: int, max_write: int,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build(drive_type, model, serial, temp,
                    used_gb, total_gb, read_speed, write_speed, max_read, max_write)

    def _build(self, drive_type: str, model: str, serial: str,
               temp: int, used_gb: float, total_gb: float,
               read_speed: float, write_speed: float,
               max_read: int, max_write: int) -> None:
        # Figma: bg #0A0A0A, 1px border #1E1E1E, 2px left border #A855F7
        self.setStyleSheet("""
            DriveCardWidget {
                background: #0A0A0A;
                border: 1px solid #1E1E1E;
                border-left: 2px solid #A855F7;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(4)

        # ── Row 1: type badge | model | temp ──────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        type_badge = QLabel(f'[ {drive_type} ]')
        type_badge.setFont(get_font('mono', FONT_SIZES['micro']))
        type_badge.setStyleSheet("""
            color: #A855F7;
            background: #1A1A1A;
            border: 1px solid #2A2A2A;
            padding: 0px 3px;
        """)
        row1.addWidget(type_badge)

        model_label = QLabel(model)
        model_label.setFont(get_font('mono', FONT_SIZES['small']))
        model_label.setStyleSheet('color: #888888;')
        row1.addWidget(model_label)
        row1.addStretch()

        temp_color = '#FF6B00' if temp > 45 else '#A855F7'
        self.temp_label = QLabel(f'{temp}°C')
        self.temp_label.setFont(get_font('mono', FONT_SIZES['small']))
        self.temp_label.setStyleSheet(f'color: {temp_color};')
        row1.addWidget(self.temp_label)
        root.addLayout(row1)

        # ── Row 2: serial ─────────────────────────────────────────────────
        sn_label = QLabel(f'S/N: {serial}')
        sn_label.setFont(get_font('mono', FONT_SIZES['micro']))
        sn_label.setStyleSheet('color: #333333;')
        root.addWidget(sn_label)

        # ── Row 3: capacity bar (purple) ──────────────────────────────────
        used_pct = (used_gb / total_gb * 100) if total_gb > 0 else 0
        free_gb  = total_gb - used_gb

        cap_labels = QHBoxLayout()
        used_lbl = QLabel(f'{used_gb:.0f} GB used')
        used_lbl.setFont(get_font('mono', FONT_SIZES['micro']))
        used_lbl.setStyleSheet('color: #444444;')
        cap_labels.addWidget(used_lbl)
        cap_labels.addStretch()
        free_lbl = QLabel(f'{free_gb:.0f} GB free')
        free_lbl.setFont(get_font('mono', FONT_SIZES['micro']))
        free_lbl.setStyleSheet('color: #333333;')
        cap_labels.addWidget(free_lbl)
        root.addLayout(cap_labels)

        self.cap_bar = VitreosSegmentedBar(segments=20, height=5,
                                           hex_color='#A855F7', alert_threshold=1.1)
        self.cap_bar.set_value(used_pct, 100)
        root.addWidget(self.cap_bar)

        # ── Row 4: read | write bars (50/50 split) ────────────────────────
        io_row = QHBoxLayout()
        io_row.setSpacing(8)

        # Left: MAX READ (cyan)
        read_col = QVBoxLayout()
        read_col.setSpacing(2)
        read_hdr = QHBoxLayout()
        read_lbl = QLabel('MAX READ')
        read_lbl.setFont(get_font('mono', FONT_SIZES['micro']))
        read_lbl.setStyleSheet('color: #333333;')
        read_hdr.addWidget(read_lbl)
        read_hdr.addStretch()
        self.read_val = QLabel(f'{max_read} <span style="color:#1E4A5A; font-size:6pt;">MB/s</span>')
        self.read_val.setFont(get_font('mono', FONT_SIZES['small']))
        self.read_val.setStyleSheet('color: #06B6D4;')
        self.read_val.setTextFormat(Qt.TextFormat.RichText)
        read_hdr.addWidget(self.read_val)
        read_col.addLayout(read_hdr)
        self.read_bar = VitreosSegmentedBar(segments=12, height=4,
                                            hex_color='#06B6D4', alert_threshold=1.1)
        self.read_bar.set_value(read_speed, 7000)
        read_col.addWidget(self.read_bar)
        io_row.addLayout(read_col)

        # Right: MAX WRITE (orange)
        write_col = QVBoxLayout()
        write_col.setSpacing(2)
        write_hdr = QHBoxLayout()
        write_lbl = QLabel('MAX WRITE')
        write_lbl.setFont(get_font('mono', FONT_SIZES['micro']))
        write_lbl.setStyleSheet('color: #333333;')
        write_hdr.addWidget(write_lbl)
        write_hdr.addStretch()
        self.write_val = QLabel(f'{max_write} <span style="color:#4A2500; font-size:6pt;">MB/s</span>')
        self.write_val.setFont(get_font('mono', FONT_SIZES['small']))
        self.write_val.setStyleSheet('color: #FF6B00;')
        self.write_val.setTextFormat(Qt.TextFormat.RichText)
        write_hdr.addWidget(self.write_val)
        write_col.addLayout(write_hdr)
        self.write_bar = VitreosSegmentedBar(segments=12, height=4,
                                             hex_color='#FF6B00', alert_threshold=1.1)
        self.write_bar.set_value(write_speed, 7000)
        write_col.addWidget(self.write_bar)
        io_row.addLayout(write_col)

        root.addLayout(io_row)

    def refresh(self, temp: int, used_gb: float, total_gb: float,
                read_speed: float, write_speed: float) -> None:
        """Update live values without rebuilding the widget."""
        used_pct   = (used_gb / total_gb * 100) if total_gb > 0 else 0
        temp_color = '#FF6B00' if temp > 45 else '#A855F7'
        self.temp_label.setStyleSheet(f'color: {temp_color};')
        self.temp_label.setText(f'{temp}°C')
        self.cap_bar.set_value(used_pct, 100)
        self.read_bar.set_value(read_speed, 7000)
        self.write_bar.set_value(write_speed, 7000)


# ═══════════════════════════════════════════════════════════════════════════
# STORAGE ARRAY - Figma V4 DISK_ARRAY Module
# ═══════════════════════════════════════════════════════════════════════════

class StorageArray(VitreosWinFrame):
    """DISK_ARRAY module rebuilt to Figma V4 spec."""

    # Static mock drives shown before telemetry arrives
    _MOCK_DRIVES = [
        dict(drive_type='NVMe', model='Samsung 990 Pro',  serial='S6EVNX0T841256B',
             temp=38, used_gb=512,  total_gb=1000, read_speed=6900, write_speed=6200,
             max_read=6900, max_write=6200),
        dict(drive_type='NVMe', model='WD Black SN850X', serial='23456F7G8H9I0J1K',
             temp=41, used_gb=1800, total_gb=2000, read_speed=7000, write_speed=6600,
             max_read=7000, max_write=6600),
        dict(drive_type='HDD',  model='Seagate Barracuda', serial='ZA1B2C3D4E5F6G7H',
             temp=32, used_gb=3200, total_gb=4000, read_speed=180,  write_speed=160,
             max_read=220,  max_write=200),
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title='DISK_ARRAY', accent_color='primary_purple', parent=parent)
        self._drive_cards: Dict[str, DriveCardWidget] = {}
        self._setup_content()

    def _setup_content(self) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        # ── Header: title + READ/WRITE legend ─────────────────────────────
        header = QHBoxLayout()
        title_lbl = QLabel('STORAGE ARRAY')
        title_lbl.setFont(get_font('mono', FONT_SIZES['title']))
        title_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        header.addWidget(title_lbl)
        header.addStretch()

        read_badge = QLabel('● READ')
        read_badge.setFont(get_font('mono', FONT_SIZES['micro']))
        read_badge.setStyleSheet("""
            color: #06B6D4;
            background: #0A1A1A;
            border: 1px solid rgba(6,182,212,0.33);
            padding: 1px 5px;
        """)
        header.addWidget(read_badge)

        write_badge = QLabel('● WRITE')
        write_badge.setFont(get_font('mono', FONT_SIZES['micro']))
        write_badge.setStyleSheet("""
            color: #FF6B00;
            background: #1A0500;
            border: 1px solid rgba(255,107,0,0.33);
            padding: 1px 5px;
        """)
        header.addWidget(write_badge)
        outer.addLayout(header)

        # ── Drive cards ───────────────────────────────────────────────────
        self.drives_layout = QVBoxLayout()
        self.drives_layout.setSpacing(8)
        outer.addLayout(self.drives_layout)

        # Populate with mock data until telemetry arrives
        for d in self._MOCK_DRIVES:
            card = DriveCardWidget(**d)
            self._drive_cards[d['serial']] = card
            self.drives_layout.addWidget(card)

        outer.addStretch()

        # ── Footer: RAID status ───────────────────────────────────────────
        footer = QWidget()
        footer.setStyleSheet("""
            background: #0A0A0A;
            border: 1px solid #1E1E1E;
            border-left: 2px solid #333333;
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(8, 4, 8, 4)

        raid_left = QHBoxLayout()
        raid_left.setSpacing(4)
        arrow = QLabel('▷')
        arrow.setFont(get_font('mono', FONT_SIZES['small']))
        arrow.setStyleSheet('color: #3A3A3A;')
        raid_left.addWidget(arrow)
        raid_text = QLabel('NO RAID CONFIGURED')
        raid_text.setFont(get_font('mono', FONT_SIZES['small']))
        raid_text.setStyleSheet('color: #3A3A3A; letter-spacing: 1px;')
        raid_left.addWidget(raid_text)
        footer_layout.addLayout(raid_left)
        footer_layout.addStretch()

        ahci_label = QLabel('AHCI')
        ahci_label.setFont(get_font('mono', FONT_SIZES['micro']))
        ahci_label.setStyleSheet('color: #222222;')
        footer_layout.addWidget(ahci_label)

        outer.addWidget(footer)
        self.set_content_layout(outer)

    def update_data(self, data: Dict[str, Any]) -> None:
        drives = data.get('drives', [])
        if not drives:
            return
        # Live update: refresh existing cards by mountpoint key
        for drive in drives:
            key = drive.get('mountpoint', drive.get('device', ''))
            if key in self._drive_cards:
                self._drive_cards[key].refresh(
                    temp=int(drive.get('temp', 0)),
                    used_gb=drive.get('usedGB', 0),
                    total_gb=drive.get('totalGB', 1),
                    read_speed=drive.get('readSpeed', 0),
                    write_speed=drive.get('writeSpeed', 0),
                )


class MemoryArray(VitreosWinFrame):
    """Memory monitoring widget with circular gauge."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="MEMORY_ARRAY", accent_color="purple_dim", parent=parent)
        self._setup_content()
    
    def _setup_content(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(9, 9, 9, 9)  # Reduced by 25%
        layout.setSpacing(4)  # Reduced by 25%
        
        # Header with gauge
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        
        self.ram_gauge = VitreosCircularGauge(segments=40)
        header_row.addWidget(self.ram_gauge)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.status_label = QLabel("SEARCHING...")
        self.status_label.setFont(get_font('mono', FONT_SIZES['title']))
        self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        info_layout.addWidget(self.status_label)
        
        self.usage_label = QLabel("0.0 / 0.0 GB")
        self.usage_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.usage_label.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
        info_layout.addWidget(self.usage_label)
        
        header_row.addLayout(info_layout)
        header_row.addStretch()
        layout.addLayout(header_row)
        
        # Main bar
        bar_header = QHBoxLayout()
        bar_label = QLabel("SYSTEM MEMORY")
        bar_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        bar_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        bar_header.addWidget(bar_label)
        bar_header.addStretch()
        self.percent_label = QLabel("0%")
        self.percent_label.setFont(get_font('mono', FONT_SIZES['small']))
        self.percent_label.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
        bar_header.addWidget(self.percent_label)
        layout.addLayout(bar_header)
        
        self.mem_bar = VitreosSegmentedBar(segments=24, height=6, color='purple_dim')
        layout.addWidget(self.mem_bar)
        
        # Stats grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(6)
        
        self.stat_labels = {}
        stats = [
            ('USED', 'used', 'GB', 'purple_dim'),
            ('FREE', 'free', 'GB', 'cyan'),
            ('CACHED', 'cached', 'GB', 'text_secondary'),
            ('AVAILABLE', 'available', 'GB', 'green'),
        ]
        
        for i, (label, key, unit, color) in enumerate(stats):
            stat_widget = QWidget()
            stat_widget.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
            """)
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(6, 6, 6, 6)
            stat_layout.setSpacing(2)
            
            stat_label = QLabel(label)
            stat_label.setFont(get_font('mono', FONT_SIZES['micro']))
            stat_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            stat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(stat_label)
            
            value_label = QLabel(f"0 {unit}")
            value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
            value_label.setStyleSheet(f"color: {VITREOS_COLORS[color]};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            
            self.stat_labels[key] = value_label
            stats_grid.addWidget(stat_widget, i // 2, i % 2)
        
        layout.addLayout(stats_grid)
        layout.addStretch()
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        used_gb = data.get('usedGB', 0)
        total_gb = data.get('totalGB', 0)
        percent = data.get('percent', 0)
        
        if total_gb > 0:
            self.status_label.setText("ONLINE")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        else:
            self.status_label.setText("OFFLINE")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        
        self.usage_label.setText(f"{used_gb:.1f} / {total_gb:.1f} GB")
        self.percent_label.setText(f"{percent:.0f}%")
        self.mem_bar.set_value(percent, 100)
        self.ram_gauge.set_value(percent, 100, 'purple_dim')
        
        free_gb = total_gb - used_gb
        self.stat_labels['used'].setText(f"{used_gb:.1f} GB")
        self.stat_labels['free'].setText(f"{free_gb:.1f} GB")
        self.stat_labels['cached'].setText(f"{data.get('cachedGB', 0):.1f} GB")
        self.stat_labels['available'].setText(f"{data.get('availableGB', free_gb):.1f} GB")


class NetInterface(VitreosWinFrame):
    """Network monitoring widget with barcode signal visualizer."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="NET_INTERFACE", accent_color="green", parent=parent)
        self._setup_content()
    
    def _setup_content(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(9, 9, 9, 9)  # Reduced by 25%
        layout.setSpacing(4)  # Reduced by 25%
        
        # Status header
        self.status_label = QLabel("SEARCHING...")
        self.status_label.setFont(get_font('mono', FONT_SIZES['title']))
        self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.status_label)
        
        # Barcode signal visualizer
        signal_label = QLabel("SIGNAL STRENGTH")
        signal_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        signal_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        layout.addWidget(signal_label)
        
        self.signal_barcode = VitreosBarcode(height=60)
        layout.addWidget(self.signal_barcode)
        
        # Throughput stats
        stats_grid = QGridLayout()
        stats_grid.setSpacing(6)
        
        self.stat_labels = {}
        stats = [
            ('DOWNLOAD', 'download', 'Mbps', 'cyan'),
            ('UPLOAD', 'upload', 'Mbps', 'warning_orange'),
            ('LATENCY', 'latency', 'ms', 'green'),
            ('PACKETS', 'packets', '/s', 'purple_dim'),
        ]
        
        for i, (label, key, unit, color) in enumerate(stats):
            stat_widget = QWidget()
            stat_widget.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
            """)
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(6, 6, 6, 6)
            stat_layout.setSpacing(2)
            
            stat_label = QLabel(label)
            stat_label.setFont(get_font('mono', FONT_SIZES['micro']))
            stat_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            stat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(stat_label)
            
            value_label = QLabel(f"0 {unit}")
            value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
            value_label.setStyleSheet(f"color: {VITREOS_COLORS[color]};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            
            self.stat_labels[key] = value_label
            stats_grid.addWidget(stat_widget, i // 2, i % 2)
        
        layout.addLayout(stats_grid)
        
        # Throughput bars
        dl_header = QHBoxLayout()
        dl_label = QLabel("DOWNLOAD")
        dl_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        dl_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        dl_header.addWidget(dl_label)
        dl_header.addStretch()
        self.dl_value = QLabel("0.00 Mbps")
        self.dl_value.setFont(get_font('mono', FONT_SIZES['small']))
        self.dl_value.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        dl_header.addWidget(self.dl_value)
        layout.addLayout(dl_header)
        
        self.dl_bar = VitreosSegmentedBar(segments=24, height=6, color='cyan')
        layout.addWidget(self.dl_bar)
        
        ul_header = QHBoxLayout()
        ul_label = QLabel("UPLOAD")
        ul_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        ul_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        ul_header.addWidget(ul_label)
        ul_header.addStretch()
        self.ul_value = QLabel("0.00 Mbps")
        self.ul_value.setFont(get_font('mono', FONT_SIZES['small']))
        self.ul_value.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        ul_header.addWidget(self.ul_value)
        layout.addLayout(ul_header)
        
        self.ul_bar = VitreosSegmentedBar(segments=24, height=6, color='warning_orange')
        layout.addWidget(self.ul_bar)
        
        layout.addStretch()
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        primary_nic = data.get('primaryNic', 'Unknown')
        if primary_nic != 'Unknown':
            self.status_label.setText(f"ONLINE // {primary_nic}")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        else:
            self.status_label.setText("OFFLINE")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        
        download = data.get('downloadMbps', 0)
        upload = data.get('uploadMbps', 0)
        latency = data.get('latency', 0)
        
        self.dl_value.setText(f"{download:.2f} Mbps")
        self.ul_value.setText(f"{upload:.2f} Mbps")
        
        self.dl_bar.set_value(download, 100)
        self.ul_bar.set_value(upload, 100)
        
        self.stat_labels['download'].setText(f"{download:.2f} Mbps")
        self.stat_labels['upload'].setText(f"{upload:.2f} Mbps")
        self.stat_labels['latency'].setText(f"{latency:.0f} ms")
        self.stat_labels['packets'].setText(f"{data.get('packetsPerSec', 0):.0f} /s")


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
