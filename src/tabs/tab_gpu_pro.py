"""
GPU Pro Tab - Overclocker's Hub
70% Control Panel | 30% Thermal Density Map
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QMouseEvent, QPaintEvent

from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font, get_color
from src.core.vitreos_logger import v_debug
from src.ui.vitreos_widgets import VitreosWinFrame, VitreosBarcode, HazardBadge


class NeonSlider(QWidget):
    """High-fidelity slider with phosphor glow effect."""
    
    valueChanged = pyqtSignal(int)
    
    def __init__(self, min_val: int = -200, max_val: int = 200, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.value = 0
        self.setFixedHeight(40)
        self.setMinimumWidth(300)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def set_value(self, value: int) -> None:
        self.value = max(self.min_val, min(self.max_val, value))
        self.update()
        self.valueChanged.emit(self.value)
    
    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0 is None:
            return
        self._update_from_mouse(a0.pos().x())
    
    def mouseMoveEvent(self, a0: QMouseEvent) -> None:
        if a0.buttons() & Qt.MouseButton.LeftButton:
            self._update_from_mouse(a0.pos().x())
    
    def _update_from_mouse(self, x: int) -> None:
        width = self.width()
        ratio = max(0, min(1, x / width))
        new_value = int(self.min_val + ratio * (self.max_val - self.min_val))
        self.set_value(new_value)
    
    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background track
        track_y = height // 2 - 2
        painter.fillRect(0, track_y, width, 4, get_color('bg_card'))
        
        # Filled track with phosphor glow
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        filled_width = int(width * ratio)
        
        # Glow effect (3 layers)
        for i in range(3):
            alpha = 80 - (i * 20)
            glow_height = 4 + (i * 2)
            glow_y = track_y - i
            painter.fillRect(0, glow_y, filled_width, glow_height, get_color('primary_purple', alpha))
        
        # Main track
        painter.fillRect(0, track_y, filled_width, 4, get_color('primary_purple'))
        
        # Thumb
        thumb_x = filled_width - 6
        thumb_y = height // 2 - 8
        painter.fillRect(thumb_x, thumb_y, 12, 16, get_color('primary_purple'))
        
        # Thumb glow
        painter.setPen(QPen(get_color('purple_glow', 150), 2))
        painter.drawRect(thumb_x - 2, thumb_y - 2, 16, 20)


class ThermalDensityBar(QWidget):
    """Vertical barcode that changes color based on temperature."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.temp = 0
        self.setFixedWidth(40)
        self.setMinimumHeight(60)
    
    def set_temp(self, temp: float) -> None:
        self.temp = temp
        self.update()
    
    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Determine color based on temp
        if self.temp > 85:
            color = get_color('critical_red')
        elif self.temp > 75:
            color = get_color('warning_orange')
        elif self.temp > 50:
            color = get_color('cyan')
        else:
            color = get_color('text_dim')
        
        # Draw vertical bars
        pattern = [3, 2, 4, 2, 3, 2, 5, 2]
        y = 0
        for i, bar_height in enumerate(pattern * (height // 30 + 1)):
            if y >= height:
                break
            
            if i % 2 == 0:
                painter.fillRect(0, y, width, bar_height, color)
            
            y += bar_height


class GPUProTab(QWidget):
    """GPU Pro tab with 70/30 asymmetric layout."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Left 70%: Control Panel
        left_panel = VitreosWinFrame(
            title="OVERCLOCK_CONTROL",
            accent_color="warning_orange",
            badge="⚠",
            badge_color="critical_red"
        )
        
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(12)
        
        # GPU Name (populated from telemetry)
        self.gpu_label = QLabel("DISCOVERING GPU...")
        self.gpu_label.setFont(get_font('mono', FONT_SIZES['title']))
        self.gpu_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        left_layout.addWidget(self.gpu_label)
        
        # Warning badge
        warning = HazardBadge("⚠ OVERCLOCKING VOIDS WARRANTY")
        left_layout.addWidget(warning)
        
        # Power Limit Slider
        power_label = QLabel("POWER LIMIT OFFSET")
        power_label.setFont(get_font('mono', FONT_SIZES['label']))
        power_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        left_layout.addWidget(power_label)
        
        power_row = QHBoxLayout()
        self.power_slider = NeonSlider(min_val=-50, max_val=50)
        self.power_slider.valueChanged.connect(self._on_power_changed)
        power_row.addWidget(self.power_slider)
        
        self.power_value = QLabel("+0 W")
        self.power_value.setFont(get_font('mono', FONT_SIZES['value_large']))
        self.power_value.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        self.power_value.setFixedWidth(80)
        power_row.addWidget(self.power_value)
        left_layout.addLayout(power_row)
        
        # Core Clock Slider
        core_label = QLabel("CORE CLOCK OFFSET")
        core_label.setFont(get_font('mono', FONT_SIZES['label']))
        core_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        left_layout.addWidget(core_label)
        
        core_row = QHBoxLayout()
        self.core_slider = NeonSlider(min_val=-200, max_val=200)
        self.core_slider.valueChanged.connect(self._on_core_changed)
        core_row.addWidget(self.core_slider)
        
        self.core_value = QLabel("+0 MHz")
        self.core_value.setFont(get_font('mono', FONT_SIZES['value_large']))
        self.core_value.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
        self.core_value.setFixedWidth(80)
        core_row.addWidget(self.core_value)
        left_layout.addLayout(core_row)
        
        # Memory Clock Slider
        mem_label = QLabel("MEMORY CLOCK OFFSET")
        mem_label.setFont(get_font('mono', FONT_SIZES['label']))
        mem_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        left_layout.addWidget(mem_label)
        
        mem_row = QHBoxLayout()
        self.mem_slider = NeonSlider(min_val=-500, max_val=500)
        self.mem_slider.valueChanged.connect(self._on_mem_changed)
        mem_row.addWidget(self.mem_slider)
        
        self.mem_value = QLabel("+0 MHz")
        self.mem_value.setFont(get_font('mono', FONT_SIZES['value_large']))
        self.mem_value.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        self.mem_value.setFixedWidth(80)
        mem_row.addWidget(self.mem_value)
        left_layout.addLayout(mem_row)
        
        # Apply button
        apply_btn = QLabel("[ APPLY SETTINGS ]")
        apply_btn.setFont(get_font('mono', FONT_SIZES['label']))
        apply_btn.setStyleSheet(f"""
            color: {VITREOS_COLORS['green']};
            background: {VITREOS_COLORS['bg_card']};
            border: 1px solid {VITREOS_COLORS['green']};
            padding: 8px;
        """)
        apply_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Use `a0` parameter name to match PyQt6 stub signature for mousePressEvent
        apply_btn.mousePressEvent = lambda a0: self._apply_settings()
        left_layout.addWidget(apply_btn)
        
        # Status
        self.status_label = QLabel("STATUS: IDLE")
        self.status_label.setFont(get_font('mono', FONT_SIZES['small']))
        self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        left_layout.addWidget(self.status_label)
        
        left_layout.addStretch()
        left_panel.set_content_layout(left_layout)
        main_layout.addWidget(left_panel, 7)
        
        # Right 30%: Thermal Density Map
        right_panel = VitreosWinFrame(
            title="THERMAL_DENSITY",
            accent_color="critical_red"
        )
        
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)
        
        density_label = QLabel("HOTSPOT MAP")
        density_label.setFont(get_font('mono', FONT_SIZES['label']))
        density_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        right_layout.addWidget(density_label)
        
        # Thermal density bars
        self.density_bars = []
        zones = ['GPU CORE', 'VRAM', 'VRM', 'PCB', 'BACKPLATE']
        
        for zone in zones:
            zone_layout = QHBoxLayout()
            zone_layout.setSpacing(8)
            
            bar = ThermalDensityBar()
            self.density_bars.append(bar)
            zone_layout.addWidget(bar)
            
            zone_label = QLabel(zone)
            zone_label.setFont(get_font('mono', FONT_SIZES['tiny']))
            zone_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            zone_layout.addWidget(zone_label, 1)
            
            right_layout.addLayout(zone_layout)
        
        right_layout.addStretch()
        right_panel.set_content_layout(right_layout)
        main_layout.addWidget(right_panel, 3)
    
    def _on_power_changed(self, value: int) -> None:
        sign = "+" if value >= 0 else ""
        self.power_value.setText(f"{sign}{value} W")
    
    def _on_core_changed(self, value: int) -> None:
        sign = "+" if value >= 0 else ""
        self.core_value.setText(f"{sign}{value} MHz")
    
    def _on_mem_changed(self, value: int) -> None:
        sign = "+" if value >= 0 else ""
        self.mem_value.setText(f"{sign}{value} MHz")
    
    def _apply_settings(self) -> None:
        self.status_label.setText("STATUS: APPLYING...")
        self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        # Placeholder for NVML apply logic
        v_debug(f"GPU PRO Apply: Power={self.power_slider.value}, Core={self.core_slider.value}, Mem={self.mem_slider.value}")
    
    def update_stats(self, data: Dict[str, Any]) -> None:
        """Update thermal density map from telemetry."""
        gpu_data = data.get('gpu', {})
        temp = gpu_data.get('temp', 0)
        # Update GPU label from telemetry name
        try:
            gpu_name = gpu_data.get('name', None)
            if gpu_name:
                display_name = gpu_name.replace('NVIDIA GeForce ', '').replace('GeForce ', '').upper()
            else:
                display_name = 'NO GPU'
            # Determine architecture shorthand if available
            if 'RTX 40' in (gpu_name or ''):
                arch = 'ADA LOVELACE'
            elif 'RTX 30' in (gpu_name or ''):
                arch = 'AMPERE'
            elif 'RTX 20' in (gpu_name or ''):
                arch = 'TURING'
            else:
                arch = ''
            label_text = f"{display_name} // {arch}" if arch else display_name
            self.gpu_label.setText(label_text)
        except Exception:
            pass
        
        # Update density bars with simulated hotspot temps
        for i, bar in enumerate(self.density_bars):
            hotspot_temp = temp + (i * 2)  # Simulate different zone temps
            bar.set_temp(hotspot_temp)


__all__ = ['GPUProTab']
