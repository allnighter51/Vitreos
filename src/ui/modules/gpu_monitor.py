# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportArgumentType=false, reportUnusedVariable=false
"""
Vitreos Monitoring Modules - Dashboard Widgets
Individual monitoring components for the 2x3 grid layout
"""

from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QScrollArea, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPaintEvent

from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font
from src.ui.vitreos_widgets import (
    VitreosWinFrame, VitreosSegmentedBar, VitreosVerticalBar,
    VitreosCircularGauge, VitreosBarcode, ConnectionStatus, HazardBadge, OCBadge, apply_phosphor_glow
)

# Explicitly ensure no mock drives are present at module load
_MOCK_DRIVES: list = []

class GpuCard(QWidget):
    """Individual GPU card displaying metrics for a single GPU."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.gpu_detected = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16) # Bottom margin separates multiple GPUs
        layout.setSpacing(8)
        
        # 1. TOP ROW: Gauge (Left) + Info (Right)
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        
        # Gauge
        self.vram_gauge = VitreosCircularGauge(segments=40)
        self.vram_gauge.setFixedSize(100, 100) # Larger gauge for new layout
        self.vram_gauge.inner_text = "0.0\nGB VRAM\n/ 0 GB" 
        top_row.addWidget(self.vram_gauge)
        
        # Info Box
        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(2)
        
        self.name_label = QLabel("DISCOVERING GPU...")
        self.name_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.name_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']}; letter-spacing: 1px;")
        info_vbox.addWidget(self.name_label)
        
        self.subtitle_label = QLabel("DISCOVERING...")
        self.subtitle_label.setFont(get_font('mono', FONT_SIZES['micro']))
        self.subtitle_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        info_vbox.addWidget(self.subtitle_label)
        
        self.driver_label = QLabel("DRIVER: 000.00 WHQL")
        self.driver_label.setFont(get_font('mono', 7))
        self.driver_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
        info_vbox.addWidget(self.driver_label)
        
        # Hazard badge holder
        self.badge_holder = QWidget()
        badge_layout = QHBoxLayout(self.badge_holder)
        badge_layout.setContentsMargins(0, 4, 0, 4)
        self.hazard_badge = OCBadge("⚠ HOT PROFILE ACTIVE")
        self.hazard_badge.hide()
        badge_layout.addWidget(self.hazard_badge)
        badge_layout.addStretch()
        info_vbox.addWidget(self.badge_holder)
        
        self.barcode = VitreosBarcode(height=24)
        info_vbox.addWidget(self.barcode)
        
        info_vbox.addStretch()
        top_row.addLayout(info_vbox)
        layout.addLayout(top_row)
        
        # 2. STATS GRID (3-line format)
        stats_grid = QGridLayout()
        stats_grid.setSpacing(4)
        
        self.stat_labels = {}
        stats = [
            ('CORE CLK', 'coreClock', 'MHz', 'primary_purple'),
            ('MEM CLK', 'memClock', 'MHz', 'primary_purple'),
            ('POWER', 'power', 'W', 'primary_purple'),
            ('TEMP', 'temp', '°C', 'primary_purple'), 
        ]
        
        for i, (label, key, unit, color) in enumerate(stats):
            stat_widget = QWidget()
            stat_widget.setStyleSheet(f"background: {VITREOS_COLORS['bg_card']}; border: 1px solid {VITREOS_COLORS['border_secondary']};")
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(4, 4, 4, 4)
            stat_layout.setSpacing(0)
            
            stat_label = QLabel(label)
            stat_label.setFont(get_font('mono', 7))
            stat_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            stat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(stat_label)
            
            value_label = QLabel("0")
            value_label.setFont(get_font('mono', FONT_SIZES['value_large']))
            value_label.setStyleSheet(f"color: {VITREOS_COLORS[color]};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            
            unit_label = QLabel(unit)
            unit_label.setFont(get_font('mono', FONT_SIZES['micro']))
            unit_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(unit_label)
            
            self.stat_labels[key] = value_label
            stats_grid.addWidget(stat_widget, 0, i)
            
        layout.addLayout(stats_grid)
        
        # 3. BARS
        def add_bar(label_text: str, value_color: str) -> tuple[QLabel, VitreosSegmentedBar]:
            row = QHBoxLayout()
            label = QLabel(label_text)
            label.setFont(get_font('mono', FONT_SIZES['micro']))
            label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
            row.addWidget(label)
            row.addStretch()
            val = QLabel("0")
            val.setFont(get_font('mono', FONT_SIZES['tiny']))
            val.setStyleSheet(f"color: {VITREOS_COLORS[value_color]};")
            row.addWidget(val)
            layout.addLayout(row)
            bar = VitreosSegmentedBar(segments=24, height=6, color=value_color)
            layout.addWidget(bar)
            return val, bar
            
        self.load_value, self.load_bar = add_bar("GPU LOAD", "primary_purple")
        self.vram_value, self.vram_bar = add_bar("VRAM USAGE", "primary_purple")
        self.bw_value, self.bw_bar = add_bar("MEM BANDWIDTH", "warning_orange")
        
        # 4. FAN ARRAY
        fan_row = QHBoxLayout()
        fan_row.setSpacing(4)
        
        self.fan_labels = {}
        for fan_id in ['FAN 1', 'FAN 2', 'REAR']:
            fan_card = QWidget()
            fan_card.setStyleSheet(f"background: {VITREOS_COLORS['bg_card']}; border: 1px solid {VITREOS_COLORS['border_secondary']};")
            fan_layout = QVBoxLayout(fan_card)
            fan_layout.setContentsMargins(4, 4, 4, 4)
            fan_layout.setSpacing(0)
            
            fan_name = QLabel(fan_id)
            fan_name.setFont(get_font('mono', 7))
            fan_name.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            fan_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fan_layout.addWidget(fan_name)
            
            fan_rpm = QLabel("0")
            fan_rpm.setFont(get_font('mono', FONT_SIZES['small']))
            fan_rpm.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple'] if 'FAN' in fan_id else 'cyan'};")
            fan_rpm.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fan_layout.addWidget(fan_rpm)
            
            fan_unit = QLabel("RPM")
            fan_unit.setFont(get_font('mono', FONT_SIZES['micro']))
            fan_unit.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            fan_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fan_layout.addWidget(fan_unit)
            
            self.fan_labels[fan_id] = fan_rpm
            fan_row.addWidget(fan_card)
            
        layout.addLayout(fan_row)
        
        self.footer_label = QLabel("PCIe 4.0 ×16 — NVML 12.3")
        self.footer_label.setFont(get_font('mono', 7))
        self.footer_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.footer_label)

    def update_data(self, data: Dict[str, Any]) -> None:
        gpu_name = data.get('name', 'NO GPU')
        
        if not self.gpu_detected and gpu_name != 'NO GPU' and 'Discovering' not in gpu_name:
            self.gpu_detected = True
            
        display_name = gpu_name.replace('NVIDIA GeForce ', '').replace('GeForce ', '').upper()
        # Add NVIDIA prefix back if it's an NVML card to match Image 2
        if data.get('is_nvml', False) and 'NVIDIA' not in display_name:
            display_name = f"NVIDIA {display_name}"
        self.name_label.setText(display_name)
        
        vram_total = data.get('vramTotal', 12)
        if 'RTX 40' in gpu_name or vram_total >= 24:
            arch = "ADA LOVELACE"
        elif 'RTX 30' in gpu_name:
            arch = "AMPERE"
        elif 'RTX 20' in gpu_name:
            arch = "TURING"
        else:
            arch = "INTEGRATED GRAPHICS" if not data.get('is_nvml', True) else "AMPERE"
            
        mem_type = "GDDR6X" if '4090' in gpu_name or '4080' in gpu_name else "GDDR6"
        self.subtitle_label.setText(f"{arch} // {vram_total:.0f}GB {mem_type}")
        
        driver = data.get('driver', 'Unknown')
        self.driver_label.setText(f"DRIVER: {driver} WHQL")
        
        core_clock = data.get('coreClock', 0)
        self.stat_labels['coreClock'].setText(f"{core_clock}")
        
        mem_clock = data.get('memClock', 0)
        self.stat_labels['memClock'].setText(f"{mem_clock}")
        
        power = data.get('power', 0)
        self.stat_labels['power'].setText(f"{power:.0f}")
        
        temp = data.get('temp', 0)
        try:
            tval = float(temp)
            self.stat_labels['temp'].setText(f"{tval:.1f}" if tval > 0 else "--")
            if tval > 75:
                self.hazard_badge.show()
            else:
                self.hazard_badge.hide()
        except Exception:
            self.stat_labels['temp'].setText("--")
            self.hazard_badge.hide()
            
        usage = data.get('usage', 0)
        self.load_value.setText(f"{usage:.0f}%")
        self.load_bar.set_value(usage, 100)
        
        vram_used = data.get('vramUsed', 0)
        vram_percent = data.get('vramPercent', 0)
        self.vram_value.setText(f"{vram_used:.1f} / {vram_total:.0f} GB")
        self.vram_bar.set_value(vram_percent, 100)
        
        self.vram_gauge.inner_text = f"{vram_used:.1f}\nGB VRAM\n/ {vram_total:.0f} GB"
        self.vram_gauge.set_value(vram_percent, 100, 'primary_purple')
        
        bandwidth = data.get('memBandwidth', 0)
        self.bw_value.setText(f"{bandwidth:.0f} GB/s")
        self.bw_bar.set_value(bandwidth, 1000)
        
        fan_speed = data.get('fanSpeed', 0)
        fan_rpm = int(fan_speed * 30)
        self.fan_labels['FAN 1'].setText(f"{fan_rpm}")
        self.fan_labels['FAN 2'].setText(f"{fan_rpm}")
        self.fan_labels['REAR'].setText(f"{int(fan_rpm * 0.8)}")


class GpuMonitor(VitreosWinFrame):
    """GPU monitoring widget with dynamic multi-GPU support and new Figma V5 design."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="GPU_MONITOR",
            accent_color="warning_orange",
            badge=None,
            badge_color="warning_orange",
            parent=parent
        )
        self.gpu_cards: List[GpuCard] = []
        self._setup_content()
    
    def _setup_content(self) -> None:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ 
                width: 4px; 
                background: {VITREOS_COLORS['bg_primary']}; 
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {VITREOS_COLORS['primary_purple']};
                border-radius: 2px;
            }}
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(9, 9, 9, 9)
        self.cards_layout.setSpacing(0)
        self.cards_layout.addStretch()
        
        self.scroll_area.setWidget(self.scroll_content)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
        self.set_content_layout(main_layout)
    
    def update_data(self, data: List[Dict[str, Any]] | Dict[str, Any]) -> None:
        if isinstance(data, dict):
            data = [data]
            
        # Ensure we have enough cards
        while len(self.gpu_cards) < len(data):
            card = GpuCard(self)
            self.gpu_cards.append(card)
            # Insert before the stretch
            self.cards_layout.insertWidget(len(self.gpu_cards) - 1, card)
            
        # Update cards and remove excess
        for i, card in enumerate(self.gpu_cards):
            if i < len(data):
                card.show()
                card.update_data(data[i])
            else:
                card.hide()
        
        # Update main window badge if ANY GPU is hot
        is_hot = False
        for gpu in data:
            try:
                if float(gpu.get('temp', 0)) > 75:
                    is_hot = True
            except:
                pass
                
        if is_hot:
            self.set_badge("HOT PROFILE ACTIVE", "warning_orange")
        else:
            self.set_badge(None)
