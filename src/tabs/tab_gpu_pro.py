#!/usr/bin/env python3
"""
Vitreos GPU Pro Tab - Advanced NVIDIA GPU Monitoring
"""
from typing import Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QSlider, QPushButton, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.vitreos_core_ui import LiquidGlassCard
from src.core.vitreos_workers import GPUTelemetry


class GPUProTab(QWidget):
    """Advanced GPU monitoring with NVML telemetry"""
    
    fan_speed_changed = pyqtSignal(int)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the GPU Pro layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header_label = QLabel("⚡ GPU Pro Telemetry")
        header_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 16px;
            font-weight: bold;
            color: #bc13fe;
        """)
        layout.addWidget(header_label)
        
        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)
        
        self.clock_card = LiquidGlassCard("GPU Clock", "-- MHz", "Core Frequency", self)
        self.power_card = LiquidGlassCard("Power Draw", "-- W", "TDP Usage", self)
        self.fan_card = LiquidGlassCard("Fan Speed", "-- RPM", "Cooling", self)
        self.temp_card = LiquidGlassCard("Temperature", "-- °C", "Core Temp", self)
        self.vram_card = LiquidGlassCard("VRAM Usage", "-- MB", "Memory", self)
        self.hotspot_card = LiquidGlassCard("Hotspot", "-- °C", "Junction Temp", self)
        
        cards_layout.addWidget(self.clock_card, 0, 0)
        cards_layout.addWidget(self.power_card, 0, 1)
        cards_layout.addWidget(self.fan_card, 0, 2)
        cards_layout.addWidget(self.temp_card, 1, 0)
        cards_layout.addWidget(self.vram_card, 1, 1)
        cards_layout.addWidget(self.hotspot_card, 1, 2)
        
        layout.addLayout(cards_layout)
        
        vram_label = QLabel("VRAM Utilization:")
        vram_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            font-weight: bold;
            color: #00f2ff;
        """)
        layout.addWidget(vram_label)
        
        self.vram_bar = QProgressBar()
        self.vram_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 6px;
                text-align: center;
                font-family: 'Consolas';
                font-size: 11px;
                color: #ffffff;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #bc13fe, stop:1 #00f2ff);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.vram_bar)
        
        fan_control_layout = QHBoxLayout()
        
        fan_label = QLabel("🌀 Fan Control:")
        fan_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            font-weight: bold;
            color: #00f2ff;
        """)
        
        self.fan_slider = QSlider(Qt.Orientation.Horizontal)
        self.fan_slider.setMinimum(0)
        self.fan_slider.setMaximum(100)
        self.fan_slider.setValue(0)
        self.fan_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #bc13fe;
                border: 2px solid #00f2ff;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #bc13fe, stop:1 #00f2ff);
                border-radius: 4px;
            }
        """)
        self.fan_slider.valueChanged.connect(self.on_fan_changed)  # type: ignore
        
        self.fan_value_label = QLabel("Auto")
        self.fan_value_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            font-weight: bold;
            color: #00f2ff;
            min-width: 60px;
        """)
        
        self.fan_reset_btn = QPushButton("Reset")
        self.fan_reset_btn.setStyleSheet("""
            QPushButton {
                background: rgba(188, 19, 254, 0.3);
                border: 2px solid #bc13fe;
                border-radius: 6px;
                padding: 5px 15px;
                font-family: 'Consolas';
                font-size: 11px;
                font-weight: bold;
                color: #ffffff;
            }
            QPushButton:hover {
                background: rgba(188, 19, 254, 0.5);
            }
        """)
        self.fan_reset_btn.clicked.connect(self.on_fan_reset)  # type: ignore
        
        fan_control_layout.addWidget(fan_label)
        fan_control_layout.addWidget(self.fan_slider)
        fan_control_layout.addWidget(self.fan_value_label)
        fan_control_layout.addWidget(self.fan_reset_btn)
        
        layout.addLayout(fan_control_layout)
        
        self.throttle_label = QLabel("")
        self.throttle_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 11px;
            color: #ff8c00;
            padding: 5px;
        """)
        self.throttle_label.hide()
        layout.addWidget(self.throttle_label)
        
        layout.addStretch()
    
    def on_fan_changed(self, value: int) -> None:
        """Handle fan slider change"""
        if value == 0:
            self.fan_value_label.setText("Auto")
        else:
            self.fan_value_label.setText(f"{value}%")
        self.fan_speed_changed.emit(value)  # type: ignore
    
    def on_fan_reset(self) -> None:
        """Reset fan to auto mode"""
        self.fan_slider.setValue(0)
    
    def update_telemetry(self, telemetry: GPUTelemetry) -> None:
        """Update GPU telemetry display"""
        self.clock_card.set_value(f"{telemetry.clock_mhz} MHz")
        self.power_card.set_value(f"{telemetry.power_watts:.1f} W")
        self.fan_card.set_value(f"{telemetry.fan_rpm} RPM")
        self.temp_card.set_value(f"{telemetry.temp_c}°C")
        self.vram_card.set_value(f"{telemetry.vram_used_mb} MB")
        self.hotspot_card.set_value(f"{telemetry.hotspot_temp_c:.1f}°C")
        
        vram_percent = int((telemetry.vram_used_mb / telemetry.vram_total_mb) * 100) if telemetry.vram_total_mb > 0 else 0
        self.vram_bar.setValue(vram_percent)
        self.vram_bar.setFormat(f"{telemetry.vram_used_mb} MB / {telemetry.vram_total_mb} MB ({vram_percent}%)")
        
        if telemetry.is_throttling:
            self.throttle_label.setText("⚠️ GPU THROTTLING DETECTED - Check thermals and power limits")
            self.throttle_label.show()
        else:
            self.throttle_label.hide()


