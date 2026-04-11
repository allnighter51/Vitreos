"""
Vitreos Settings Tab - Performance Tuning
Includes polling rate slider for dynamic hardware monitoring frequency
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QGroupBox, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font
from src.ui.vitreos_widgets import VitreosWinFrame


class SettingsTab(QWidget):
    """
    Settings tab with performance tuning controls.
    
    Features:
    - Polling rate slider (8-100ms)
    - UI refresh rate display
    - Performance presets
    """
    
    # Signals
    polling_rate_changed = pyqtSignal(int)  # Hardware polling rate (ms)
    ui_refresh_rate_changed = pyqtSignal(int)  # UI refresh rate (ms)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build settings interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Title
        title_label = QLabel("SYSTEM SETTINGS")
        title_label.setFont(get_font('mono', FONT_SIZES['title']))
        title_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        layout.addWidget(title_label)
        
        # Performance Tuning Group
        perf_group = self._create_performance_group()
        layout.addWidget(perf_group)
        
        # UI Settings Group
        ui_group = self._create_ui_group()
        layout.addWidget(ui_group)
        
        layout.addStretch()
    
    def _create_performance_group(self) -> QGroupBox:
        """Create performance tuning controls"""
        group = QGroupBox("PERFORMANCE TUNING")
        group.setFont(get_font('mono', FONT_SIZES['value_medium']))
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {VITREOS_COLORS['text_secondary']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
                border-radius: 0px;
                margin-top: 12px;
                padding-top: 12px;
                background: {VITREOS_COLORS['bg_card']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: {VITREOS_COLORS['primary_purple']};
            }}
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Polling Rate Slider
        slider_label = QLabel("HARDWARE POLLING RATE")
        slider_label.setFont(get_font('mono', FONT_SIZES['small']))
        slider_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        layout.addWidget(slider_label)
        
        # Slider with value display
        slider_row = QHBoxLayout()
        
        self.polling_slider = QSlider(Qt.Orientation.Horizontal)
        self.polling_slider.setMinimum(100)
        self.polling_slider.setMaximum(5000)
        self.polling_slider.setValue(1000)  # Default 1Hz
        self.polling_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.polling_slider.setTickInterval(500)
        self.polling_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {VITREOS_COLORS['border_primary']};
                height: 6px;
                background: {VITREOS_COLORS['bg_primary']};
            }}
            QSlider::handle:horizontal {{
                background: {VITREOS_COLORS['primary_purple']};
                border: 1px solid {VITREOS_COLORS['purple_glow']};
                width: 16px;
                margin: -6px 0;
            }}
            QSlider::handle:horizontal:hover {{
                background: {VITREOS_COLORS['purple_glow']};
            }}
            QSlider::sub-page:horizontal {{
                background: {VITREOS_COLORS['primary_purple']};
            }}
        """)
        self.polling_slider.valueChanged.connect(self._on_polling_slider_changed)
        slider_row.addWidget(self.polling_slider, 1)
        
        # Current value display
        self.polling_value_label = QLabel("1000ms (1.0 FPS)")
        self.polling_value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.polling_value_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        self.polling_value_label.setMinimumWidth(140)
        self.polling_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        slider_row.addWidget(self.polling_value_label)
        
        layout.addLayout(slider_row)
        
        # Preset buttons
        presets_label = QLabel("PRESETS")
        presets_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        presets_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(presets_label)
        
        presets_row = QHBoxLayout()
        presets_row.setSpacing(8)
        
        presets = [
            ("FAST", 100, "10 FPS - High performance"),
            ("MED", 1000, "1 FPS - Balanced"),
            ("SLOW", 3000, "0.3 FPS - Power saving"),
            ("MIN", 5000, "0.2 FPS - Minimal overhead"),
        ]
        
        for label, value, tooltip in presets:
            btn = QPushButton(label)
            btn.setFont(get_font('mono', FONT_SIZES['tiny']))
            btn.setFixedHeight(28)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {VITREOS_COLORS['bg_primary']};
                    border: 1px solid {VITREOS_COLORS['border_primary']};
                    color: {VITREOS_COLORS['text_secondary']};
                    padding: 4px 12px;
                }}
                QPushButton:hover {{
                    background: {VITREOS_COLORS['bg_card']};
                    border: 1px solid {VITREOS_COLORS['primary_purple']};
                    color: {VITREOS_COLORS['primary_purple']};
                }}
                QPushButton:pressed {{
                    background: {VITREOS_COLORS['primary_purple']};
                    color: {VITREOS_COLORS['text_primary']};
                }}
            """)
            btn.clicked.connect(lambda checked, v=value: self.polling_slider.setValue(v))
            presets_row.addWidget(btn)
        
        layout.addLayout(presets_row)
        
        # Info text
        info_label = QLabel(
            "Lower values = more frequent updates but higher CPU usage.\n"
            "Higher values = slower updates but lower CPU usage.\n"
            "UI refresh rate is synchronized with hardware polling."
        )
        info_label.setFont(get_font('mono', FONT_SIZES['micro']))
        info_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        return group
    
    def _create_ui_group(self) -> QGroupBox:
        """Create UI settings controls"""
        group = QGroupBox("UI SETTINGS")
        group.setFont(get_font('mono', FONT_SIZES['value_medium']))
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {VITREOS_COLORS['text_secondary']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
                border-radius: 0px;
                margin-top: 12px;
                padding-top: 12px;
                background: {VITREOS_COLORS['bg_card']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: {VITREOS_COLORS['cyan']};
            }}
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # UI refresh rate (synchronized with hardware polling)
        refresh_row = QHBoxLayout()
        refresh_label = QLabel("UI REFRESH RATE")
        refresh_label.setFont(get_font('mono', FONT_SIZES['small']))
        refresh_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        refresh_row.addWidget(refresh_label)
        refresh_row.addStretch()
        
        self.refresh_value_label = QLabel("1.0 FPS (Synced)")
        self.refresh_value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.refresh_value_label.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        refresh_row.addWidget(self.refresh_value_label)
        
        layout.addLayout(refresh_row)
        
        # Info text
        info_label = QLabel(
            "UI updates are synchronized with hardware polling.\n"
            "Both update at the same rate for maximum efficiency."
        )
        info_label.setFont(get_font('mono', FONT_SIZES['micro']))
        info_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        return group
    
    def _on_polling_slider_changed(self, value: int) -> None:
        """Handle polling rate slider changes"""
        fps = 1000.0 / value
        self.polling_value_label.setText(f"{value}ms ({fps:.1f} FPS)")
        
        # Update UI refresh rate label (synchronized)
        self.refresh_value_label.setText(f"{fps:.1f} FPS (Synced)")
        
        # Emit signals to update hardware polling and UI refresh
        self.polling_rate_changed.emit(value)
        self.ui_refresh_rate_changed.emit(value)
        
        # Color-code based on performance impact
        if value <= 500:
            color = VITREOS_COLORS['warning_orange']  # High performance
        elif value <= 2000:
            color = VITREOS_COLORS['cyan']  # Balanced
        else:
            color = VITREOS_COLORS['green']  # Power saving
        
        self.polling_value_label.setStyleSheet(f"color: {color};")
        self.refresh_value_label.setStyleSheet(f"color: {color};")
    
    def set_polling_rate(self, value: int) -> None:
        """Set polling rate programmatically"""
        self.polling_slider.setValue(value)


__all__ = ['SettingsTab']
