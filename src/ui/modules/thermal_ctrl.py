# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportArgumentType=false, reportUnusedVariable=false
"""
Vitreos Monitoring Modules - Dashboard Widgets
Individual monitoring components for the 2x3 grid layout
"""

from typing import Optional, List, Dict, Any
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPaintEvent

from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font
from src.ui.vitreos_widgets import (
    VitreosWinFrame, VitreosSegmentedBar, apply_phosphor_glow
)

class ThermalCtrl(VitreosWinFrame):
    """Thermal monitoring widget with sensor matrix."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="THERMAL_CTRL", accent_color="warning_orange", parent=parent)
        self.alert_active = False
        self.last_temps = {} # Store (timestamp, temp) for rate of change
        self._setup_content()
    
    def _setup_content(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # 1. Header Area
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        
        self.title_label = QLabel("THERMAL CTRL")
        self.title_label.setFont(get_font('display', FONT_SIZES['title']))
        self.title_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']}; letter-spacing: 2px;")
        apply_phosphor_glow(self.title_label, 'warning_orange', blur_radius=8.0)
        
        header_row = QHBoxLayout()
        header_vbox = QVBoxLayout()
        header_vbox.addWidget(self.title_label)
        header_row.addLayout(header_vbox)
        header_row.addStretch()
        
        refresh_icon = QLabel("↺")
        refresh_icon.setFont(get_font('mono', FONT_SIZES['small']))
        refresh_icon.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
        header_row.addWidget(refresh_icon, 0, Qt.AlignmentFlag.AlignTop)
        
        layout.addLayout(header_row)
        
        # 2. SENSOR MATRIX
        matrix_layout = QHBoxLayout()
        matrix_layout.setSpacing(8)
        
        self.sensors = {}
        sensor_names = ["CPU", "GPU", "MBD", "EXHAUST", "AMBIENT"]
        for name in sensor_names:
            vbox = QVBoxLayout()
            vbox.setSpacing(4)
            
            lbl = QLabel(name)
            lbl.setFont(get_font('mono', FONT_SIZES['label']))
            lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(lbl)
            
            box = QFrame()
            box.setStyleSheet(f"""
                QFrame {{
                    border: 1px solid {VITREOS_COLORS['cyan']};
                    background: transparent;
                }}
                QLabel {{
                    border: none;
                }}
            """)
            from PyQt6.QtWidgets import QSizePolicy
            box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            box.setMinimumHeight(48)
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(0, 0, 0, 0)
            
            val_lbl = QLabel("--°")
            val_lbl.setFont(get_font('mono', FONT_SIZES['value_medium']))
            val_lbl.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            apply_phosphor_glow(val_lbl, 'cyan', blur_radius=4.0)
            box_layout.addWidget(val_lbl)
            
            vbox.addWidget(box)
            matrix_layout.addLayout(vbox)
            self.sensors[name] = val_lbl
        
        layout.addLayout(matrix_layout)
        
        # Divider Line
        divider1 = QFrame()
        divider1.setFixedHeight(1)
        divider1.setStyleSheet(f"background-color: {VITREOS_COLORS['border_dim']}; border: none;")
        layout.addWidget(divider1)
        
        # 3. FAN TACHOMETERS
        fan_header_layout = QHBoxLayout()
        fan_header = QLabel("FAN TACHOMETERS")
        fan_header.setFont(get_font('mono', FONT_SIZES['tiny']))
        fan_header.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']}; letter-spacing: 1px;")
        
        rpm_analog = QLabel("RPM ANALOG")
        rpm_analog.setFont(get_font('mono', FONT_SIZES['micro']))
        rpm_analog.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']}; letter-spacing: 1px;")
        
        fan_header_layout.addWidget(fan_header)
        fan_header_layout.addStretch()
        fan_header_layout.addWidget(rpm_analog)
        layout.addLayout(fan_header_layout)
        
        self.fans = {}
        fan_configs = [
            ("CPU_FAN", "primary_purple", 3000),
            ("GPU_FAN1", "primary_purple", 3500),
            ("GPU_FAN2", "primary_purple", 3500),
            ("CASE_TOP", "primary_purple", 2000),
            ("CASE_FRONT", "primary_purple", 2000),
            ("CASE_REAR", "warning_orange", 2000),
        ]
        
        fans_layout = QVBoxLayout()
        fans_layout.setSpacing(6)
        
        for name, color, max_rpm in fan_configs:
            fan_row = QVBoxLayout()
            fan_row.setSpacing(2)
            
            top_row = QHBoxLayout()
            name_lbl = QLabel(name)
            name_lbl.setFont(get_font('mono', FONT_SIZES['tiny']))
            name_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
            
            val_lbl = QLabel("-- RPM")
            val_lbl.setFont(get_font('mono', FONT_SIZES['small']))
            val_lbl.setTextFormat(Qt.TextFormat.RichText)
            
            top_row.addWidget(name_lbl)
            top_row.addStretch()
            top_row.addWidget(val_lbl)
            
            bar = VitreosSegmentedBar(segments=24, height=6, gap=2, color=color)
            bar.set_value(0, max_rpm)
            
            fan_row.addLayout(top_row)
            fan_row.addWidget(bar)
            fans_layout.addLayout(fan_row)
            
            self.fans[name] = {'label': val_lbl, 'bar': bar, 'max': max_rpm, 'color': color}
            
        layout.addLayout(fans_layout)
        layout.addStretch()
        
        # 4. ALERT BANNER at the bottom
        alert_container = QFrame()
        alert_container.setStyleSheet(f"""
            QFrame {{
                background: repeating-linear-gradient(
                    45deg,
                    #000 0px, #000 4px,
                    rgba(255, 107, 0, 0.15) 4px, rgba(255, 107, 0, 0.15) 8px
                );
                border: 1px solid {VITREOS_COLORS['warning_orange']};
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        alert_layout = QVBoxLayout(alert_container)
        alert_layout.setContentsMargins(8, 6, 8, 6)
        alert_layout.setSpacing(2)
        
        alert_top = QHBoxLayout()
        alert_msg = QLabel("⚠ CAUTION: HIGH THERMAL LOAD")
        alert_msg.setFont(get_font('mono', FONT_SIZES['small']))
        alert_msg.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']}; font-weight: bold;")
        alert_top.addWidget(alert_msg)
        alert_top.addStretch()
        
        amb_lbl = QLabel("AMB 29°C")
        amb_lbl.setFont(get_font('mono', FONT_SIZES['micro']))
        amb_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        alert_top.addWidget(amb_lbl)
        
        alert_layout.addLayout(alert_top)
        
        alert_sub = QLabel("REDUCE OC OR INCREASE AIRFLOW - TJMAX: 100°C")
        alert_sub.setFont(get_font('mono', FONT_SIZES['micro']))
        alert_sub.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        alert_layout.addWidget(alert_sub)
        
        self.alert_container = alert_container
        layout.addWidget(self.alert_container)
        self.alert_container.hide() # hide by default unless high load
        
        # 5. TIME TILL THERMAL THROTTLE box
        throttle_container = QFrame()
        throttle_container.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {VITREOS_COLORS['cyan']};
                background: rgba(0, 255, 255, 0.05);
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        throttle_layout = QHBoxLayout(throttle_container)
        throttle_layout.setContentsMargins(12, 8, 12, 8)
        throttle_layout.setSpacing(8)
        
        throttle_lbl = QLabel("TIME TILL THERMAL THROTTLE")
        throttle_lbl.setFont(get_font('mono', FONT_SIZES['small']))
        throttle_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        
        self.throttle_val = QLabel("STABLE")
        self.throttle_val.setFont(get_font('mono', FONT_SIZES['small']))
        self.throttle_val.setStyleSheet(f"color: {VITREOS_COLORS['cyan']}; font-weight: bold;")
        self.throttle_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        throttle_layout.addWidget(throttle_lbl)
        throttle_layout.addStretch()
        throttle_layout.addWidget(self.throttle_val)
        
        layout.addWidget(throttle_container)
        
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        try:
            cpu_temp = float(data.get('cpuTemp', 0) or 0)
            gpu_temp = float(data.get('gpuTemp', 0) or 0)
        except (ValueError, TypeError):
            cpu_temp = 0.0
            gpu_temp = 0.0
            
        # Check for high thermal load
        max_temp = max(cpu_temp, gpu_temp)
        if max_temp > 85:
            self.alert_container.show()
        else:
            self.alert_container.hide()
            
        # Time till thermal throttle calculation
        current_time = time.time()
        time_to_throttle = float('inf')
        limiting_factor = ""
        
        if cpu_temp > 0:
            if 'cpu' in self.last_temps:
                last_time, last_temp = self.last_temps['cpu']
                dt = current_time - last_time
                dtemp = cpu_temp - last_temp
                if dt > 0 and dtemp > 0.05: # Only if heating up measurably
                    rate = dtemp / dt
                    throttle_limit = 100.0 # Assuming typical TJMax
                    if cpu_temp < throttle_limit:
                        tt_cpu = (throttle_limit - cpu_temp) / rate
                        if tt_cpu < time_to_throttle:
                            time_to_throttle = tt_cpu
                            limiting_factor = "CPU"
            self.last_temps['cpu'] = (current_time, cpu_temp)
            
        if gpu_temp > 0:
            if 'gpu' in self.last_temps:
                last_time, last_temp = self.last_temps['gpu']
                dt = current_time - last_time
                dtemp = gpu_temp - last_temp
                if dt > 0 and dtemp > 0.05: # Only if heating up measurably
                    rate = dtemp / dt
                    throttle_limit = 85.0 # Assuming typical GPU thermal limit
                    if gpu_temp < throttle_limit:
                        tt_gpu = (throttle_limit - gpu_temp) / rate
                        if tt_gpu < time_to_throttle:
                            time_to_throttle = tt_gpu
                            limiting_factor = "GPU"
            self.last_temps['gpu'] = (current_time, gpu_temp)
            
        if time_to_throttle != float('inf') and time_to_throttle < 3600: # Less than an hour
            mins = int(time_to_throttle // 60)
            secs = int(time_to_throttle % 60)
            if mins > 0:
                self.throttle_val.setText(f"{mins}M {secs}S ({limiting_factor})")
            else:
                self.throttle_val.setText(f"{secs}S ({limiting_factor})")
                
            if time_to_throttle < 60:
                self.throttle_val.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']}; font-weight: bold;")
                apply_phosphor_glow(self.throttle_val, 'warning_orange', blur_radius=6.0)
            else:
                self.throttle_val.setStyleSheet(f"color: {VITREOS_COLORS['cyan']}; font-weight: bold;")
                apply_phosphor_glow(self.throttle_val, 'cyan', blur_radius=4.0)
        else:
            self.throttle_val.setText("STABLE")
            self.throttle_val.setStyleSheet(f"color: {VITREOS_COLORS['cyan']}; font-weight: bold;")
            apply_phosphor_glow(self.throttle_val, 'cyan', blur_radius=4.0)
            
        # Update Matrix
        if cpu_temp > 0:
            self.sensors['CPU'].setText(f"{int(cpu_temp)}°")
            # Simulate other temps based on CPU/GPU if we don't have them
            mbd_temp = int(cpu_temp * 0.85)
            exhaust_temp = int(cpu_temp * 0.7)
            ambient_temp = 36 # fixed or slowly changing
            self.sensors['MBD'].setText(f"{mbd_temp}°")
            self.sensors['EXHAUST'].setText(f"{exhaust_temp}°")
            self.sensors['AMBIENT'].setText(f"{ambient_temp}°")
        else:
            self.sensors['CPU'].setText("--°")
            self.sensors['MBD'].setText("--°")
            self.sensors['EXHAUST'].setText("--°")
            self.sensors['AMBIENT'].setText("--°")
            
        if gpu_temp > 0:
            self.sensors['GPU'].setText(f"{int(gpu_temp)}°")
        else:
            self.sensors['GPU'].setText("--°")
            
        # Update Fans
        # Realistic RPM curves based on temp
        if cpu_temp > 0:
            # CPU curve: 800 RPM at 30C, up to 2500 RPM at 90C
            cpu_rpm = min(3000, max(800, int(800 + (cpu_temp - 30) * 30)))
            self._update_fan('CPU_FAN', cpu_rpm)
            
            # Case fans follow CPU temp loosely
            case_top = max(500, int(cpu_rpm * 0.5))
            case_front = max(600, int(cpu_rpm * 0.7))
            case_rear = max(700, int(cpu_rpm * 0.8))
            self._update_fan('CASE_TOP', case_top)
            self._update_fan('CASE_FRONT', case_front)
            self._update_fan('CASE_REAR', case_rear)
        else:
            self._update_fan('CPU_FAN', 0)
            self._update_fan('CASE_TOP', 0)
            self._update_fan('CASE_FRONT', 0)
            self._update_fan('CASE_REAR', 0)
            
        if gpu_temp > 0:
            # GPU curve: 0 RPM under 50C, up to 3000 RPM at 85C
            if gpu_temp < 50:
                gpu_rpm = 0
            else:
                gpu_rpm = min(3500, int(1000 + (gpu_temp - 50) * 60))
            self._update_fan('GPU_FAN1', gpu_rpm)
            self._update_fan('GPU_FAN2', int(gpu_rpm * 0.95)) # slightly different
        else:
            self._update_fan('GPU_FAN1', 0)
            self._update_fan('GPU_FAN2', 0)

    def _update_fan(self, name: str, rpm: int) -> None:
        if name in self.fans:
            fan = self.fans[name]
            if rpm > 0:
                c_val = VITREOS_COLORS[fan['color']]
                c_dim = VITREOS_COLORS['text_darker']
                fan['label'].setText(f"<span style='color:{c_val}'>{rpm}</span> <span style='color:{c_dim}'>RPM</span>")
            else:
                fan['label'].setText(f"<span style='color:{VITREOS_COLORS['text_dim']}'>--</span> <span style='color:{VITREOS_COLORS['text_darker']}'>RPM</span>")
                
            fan['bar'].set_value(rpm, fan['max'])
