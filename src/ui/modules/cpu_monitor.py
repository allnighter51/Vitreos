# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportArgumentType=false, reportUnusedVariable=false
"""
Vitreos Monitoring Modules - Dashboard Widgets
Individual monitoring components for the 2x3 grid layout
"""

from typing import Optional, List, Dict, Any
import re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPaintEvent

from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font
from src.ui.vitreos_widgets import (
    VitreosWinFrame, VitreosSegmentedBar, VitreosVerticalBar,
    VitreosCircularGauge, VitreosBarcode, ConnectionStatus, HazardBadge, OCBadge, apply_phosphor_glow
)

# Explicitly ensure no mock drives are present at module load
_MOCK_DRIVES: list = []

class CpuMonitor(VitreosWinFrame):
    """CPU monitoring widget with per-core activity grid."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="CPU_MONITOR",
            accent_color="cyan",
            parent=parent
        )
        
        # Start with zero cores — UI will build grid on first telemetry packet
        self.detected_cores = 0
        self.cpu_detected = False
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
        self.core_labels: List[QLabel] = []
        # Do NOT build core grid until telemetry provides coreCount
        
        layout.addLayout(self.cores_grid)
        layout.addStretch()
        
        self.set_content_layout(layout)
    
    def _rebuild_core_grid(self) -> None:
        for widget in self.core_widgets:
            self.cores_grid.removeWidget(widget)
            widget.deleteLater()
        self.core_bars.clear()
        self.core_widgets.clear()
        self.core_labels.clear()
        
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
            self.core_labels.append(core_label)
            # Aesthetic: subtle phosphor glow on each core label to preserve neon vibe
            try:
                apply_phosphor_glow(core_label, 'primary_purple', blur_radius=3.0)
            except Exception:
                pass
            
            bar = VitreosVerticalBar(segments=7, width=12)
            core_layout.addWidget(bar, alignment=Qt.AlignmentFlag.AlignCenter)
            self.core_bars.append(bar)
            
            self.cores_grid.addWidget(core_widget, row, col)
            self.core_widgets.append(core_widget)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        raw_name = str(data.get('name', 'Unknown CPU') or 'Unknown CPU')
        cpu_name = re.sub(r'\s+\d+-[Cc]ore\s+[Pp]rocessor', '', raw_name, flags=re.IGNORECASE).strip()
        
        # Header state transition: DETECTING → CPU NAME
        # Transition labels: DETECTING / INITIALIZING -> ACTIVE / RYZEN_CONNECTED
        if not self.cpu_detected and cpu_name != 'Unknown CPU' and 'Discovering' not in cpu_name:
            self.cpu_detected = True
            # Prefer explicit RYZEN_CONNECTED label for AMD Ryzen CPUs
            if 'ryzen' in cpu_name.lower():
                self.name_label.setText('RYZEN_CONNECTED')
            else:
                self.name_label.setText('ACTIVE')
            self.name_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
            self.specs_label.setText('ACTIVE')
        elif self.cpu_detected:
            # Once detected, show the CPU model as subtitle
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
        
        try:
            total_load = float(data.get('totalLoad', 0) or 0)
        except Exception:
            total_load = 0.0
        self.load_value_label.setText(f"{total_load:.0f}%")
        self.load_bar.set_value(total_load, 100)
        
        try:
            temp = float(data.get('temp', 0) or 0)
        except Exception:
            temp = 0.0
        # Format temp (show '--°C' when telemetry reports zero/unavailable)
        if temp is None or temp <= 0:
            self.temp_value_label.setText('--°C')
            self.temp_value_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        else:
            self.temp_value_label.setText(f"{temp:.0f}°C")
            self.temp_value_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        self.temp_bar.set_value(max(0.0, temp), 100)
        
        cores = data.get('cores', []) or []
        for i, bar in enumerate(self.core_bars):
            val = 0.0
            if i < len(cores):
                try:
                    val = float(cores[i] or 0)
                except Exception:
                    val = 0.0
            bar.set_value(val, 100)

            # Aesthetic: apply overload glow when a core exceeds 90%
            core_widget = self.core_widgets[i]
            core_label = self.core_labels[i]
            if val >= 90.0:
                core_widget.setStyleSheet(f"background: {VITREOS_COLORS['bg_primary']}; border: 1px solid {VITREOS_COLORS['critical_red']};")
                try:
                    apply_phosphor_glow(core_label, 'critical_red', blur_radius=6.0)
                except Exception:
                    pass
            else:
                core_widget.setStyleSheet(f"background: {VITREOS_COLORS['bg_primary']}; border: 1px solid {VITREOS_COLORS['border_secondary']};")
                # Remove any existing glow
                try:
                    core_label.setGraphicsEffect(None)
                except Exception:
                    pass
