"""
Vitreos Monitoring Modules - Dashboard Widgets
Individual monitoring components for the 2x3 grid layout
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font, get_color
from vitreos_widgets import VitreosWinFrame, VitreosSegmentedBar, VitreosVerticalBar


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
        
        self._setup_content()
    
    def _setup_content(self) -> None:
        """Build CPU monitor layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # CPU Name
        name_label = QLabel("AMD RYZEN 9 7950X")
        name_label.setFont(get_font('mono', FONT_SIZES['title']))
        name_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        layout.addWidget(name_label)
        
        specs_label = QLabel("16C/32T | ZEN 4 | 5nm")
        specs_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        specs_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(specs_label)
        
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
        
        for i in range(16):  # 16 cores
            row = i // 4
            col = i % 4
            
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
        
        layout.addLayout(self.cores_grid)
        layout.addStretch()
        
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update CPU monitor with fresh data."""
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
# GPU MONITOR - RTX 4090 Dashboard
# ═══════════════════════════════════════════════════════════════════════════

class GpuMonitor(VitreosWinFrame):
    """GPU monitoring widget optimized for RTX 4090."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="GPU_MONITOR",
            accent_color="warning_orange",
            badge="4090",
            badge_color="warning_orange",
            parent=parent
        )
        
        self._setup_content()
    
    def _setup_content(self) -> None:
        """Build GPU monitor layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # GPU Name
        name_label = QLabel("NVIDIA RTX 4090")
        name_label.setFont(get_font('mono', FONT_SIZES['title']))
        name_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        layout.addWidget(name_label)
        
        specs_label = QLabel("24GB GDDR6X | ADA LOVELACE")
        specs_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        specs_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(specs_label)
        
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
        
        self.vram_value_label = QLabel("0.0 / 24.0 GB")
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
        # GPU Usage
        usage = data.get('usage', 0)
        self.usage_value_label.setText(f"{usage:.0f}%")
        self.usage_bar.set_value(usage, 100)
        
        # VRAM
        vram_used = data.get('vramUsed', 0)
        vram_total = data.get('vramTotal', 24)
        self.vram_value_label.setText(f"{vram_used:.1f} / {vram_total:.1f} GB")
        vram_percent = (vram_used / vram_total * 100) if vram_total > 0 else 0
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
        
        # Hazard sticker logic - change color if temp > 85°C
        if temp > 85:
            self.stat_labels['temp'].setStyleSheet(f"color: {VITREOS_COLORS['critical_red']};")
        else:
            self.stat_labels['temp'].setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")


# ═══════════════════════════════════════════════════════════════════════════
# PLACEHOLDER MODULES (To be implemented)
# ═══════════════════════════════════════════════════════════════════════════

class ThermalCtrl(VitreosWinFrame):
    """Thermal monitoring widget."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="THERMAL_CTRL", accent_color="cyan", parent=parent)
        layout = QVBoxLayout()
        label = QLabel("Thermal monitoring")
        label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(label)
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        pass


class StorageArray(VitreosWinFrame):
    """Storage monitoring widget."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="STORAGE_ARRAY", accent_color="primary_purple", parent=parent)
        layout = QVBoxLayout()
        label = QLabel("Storage monitoring")
        label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(label)
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        pass


class MemoryArray(VitreosWinFrame):
    """Memory monitoring widget."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="MEMORY_ARRAY", accent_color="purple_dim", parent=parent)
        layout = QVBoxLayout()
        label = QLabel("Memory monitoring")
        label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(label)
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        pass


class NetInterface(VitreosWinFrame):
    """Network monitoring widget."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="NET_INTERFACE", accent_color="green", parent=parent)
        layout = QVBoxLayout()
        label = QLabel("Network monitoring")
        label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(label)
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        pass


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
