#!/usr/bin/env python3
"""
Vitreos Settings Tab - Application Configuration
"""
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QCheckBox, QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal


class SettingsTab(QWidget):
    """Application settings and configuration"""
    
    polling_interval_changed = pyqtSignal(int)
    theme_changed = pyqtSignal(int)
    startup_toggled = pyqtSignal(bool)
    database_clear_requested = pyqtSignal()
    database_export_requested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the settings layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("⚙️ Settings")
        header_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 16px;
            font-weight: bold;
            color: #bc13fe;
        """)
        layout.addWidget(header_label)
        
        # Performance settings
        perf_frame = QFrame()
        perf_frame.setStyleSheet("""
            QFrame {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        perf_layout = QVBoxLayout(perf_frame)
        
        perf_label = QLabel("⚡ Performance")
        perf_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 14px;
            font-weight: bold;
            color: #00f2ff;
        """)
        perf_layout.addWidget(perf_label)
        
        # Heartbeat regulator
        heartbeat_layout = QHBoxLayout()
        
        heartbeat_label = QLabel("Heartbeat Regulator:")
        heartbeat_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 11px;
            color: #888;
        """)
        
        self.heartbeat_slider = QSlider(Qt.Orientation.Horizontal)
        self.heartbeat_slider.setMinimum(100)
        self.heartbeat_slider.setMaximum(5000)
        self.heartbeat_slider.setValue(1000)
        self.heartbeat_slider.setStyleSheet("""
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
        self.heartbeat_slider.valueChanged.connect(self.on_heartbeat_changed)  # type: ignore
        
        self.heartbeat_value_label = QLabel("1000 ms")
        self.heartbeat_value_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 11px;
            font-weight: bold;
            color: #00f2ff;
            min-width: 70px;
        """)
        
        heartbeat_layout.addWidget(heartbeat_label)
        heartbeat_layout.addWidget(self.heartbeat_slider)
        heartbeat_layout.addWidget(self.heartbeat_value_label)
        
        perf_layout.addLayout(heartbeat_layout)
        
        layout.addWidget(perf_frame)
        
        # Appearance settings
        appearance_frame = QFrame()
        appearance_frame.setStyleSheet("""
            QFrame {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        appearance_layout = QVBoxLayout(appearance_frame)
        
        appearance_label = QLabel("🎨 Appearance")
        appearance_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 14px;
            font-weight: bold;
            color: #00f2ff;
        """)
        appearance_layout.addWidget(appearance_label)
        
        # Theme hue slider
        theme_layout = QHBoxLayout()
        
        theme_label = QLabel("Theme Hue:")
        theme_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 11px;
            color: #888;
        """)
        
        self.theme_slider = QSlider(Qt.Orientation.Horizontal)
        self.theme_slider.setMinimum(0)
        self.theme_slider.setMaximum(360)
        self.theme_slider.setValue(280)  # Default purple hue
        self.theme_slider.setStyleSheet("""
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
        self.theme_slider.valueChanged.connect(self.on_theme_changed)  # type: ignore
        
        self.theme_value_label = QLabel("280°")
        self.theme_value_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 11px;
            font-weight: bold;
            color: #00f2ff;
            min-width: 50px;
        """)
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_slider)
        theme_layout.addWidget(self.theme_value_label)
        
        appearance_layout.addLayout(theme_layout)
        
        layout.addWidget(appearance_frame)
        
        # System settings
        system_frame = QFrame()
        system_frame.setStyleSheet("""
            QFrame {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        system_layout = QVBoxLayout(system_frame)
        
        system_label = QLabel("💻 System")
        system_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 14px;
            font-weight: bold;
            color: #00f2ff;
        """)
        system_layout.addWidget(system_label)
        
        checkbox_style = """
            QCheckBox {
                font-family: 'Consolas';
                font-size: 11px;
                color: #00f2ff;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #bc13fe;
                border-radius: 3px;
                background: rgba(12, 12, 15, 0.95);
            }
            QCheckBox::indicator:checked {
                background: #bc13fe;
            }
        """
        
        self.startup_check = QCheckBox("Launch on Windows Startup")
        self.startup_check.setStyleSheet(checkbox_style)
        self.startup_check.stateChanged.connect(self.on_startup_toggled)  # type: ignore
        
        self.tray_check = QCheckBox("Minimize to System Tray")
        self.tray_check.setStyleSheet(checkbox_style)
        
        system_layout.addWidget(self.startup_check)
        system_layout.addWidget(self.tray_check)
        
        layout.addWidget(system_frame)
        
        # Database maintenance
        db_frame = QFrame()
        db_frame.setStyleSheet("""
            QFrame {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        db_layout = QVBoxLayout(db_frame)
        
        db_label = QLabel("🗄️ Database Maintenance")
        db_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 14px;
            font-weight: bold;
            color: #00f2ff;
        """)
        db_layout.addWidget(db_label)
        
        db_button_layout = QHBoxLayout()
        
        self.db_clear_btn = QPushButton("🧹 Clear Database")
        self.db_clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 0, 0, 0.3);
                border: 2px solid #ff8c00;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: 'Consolas';
                font-size: 11px;
                font-weight: bold;
                color: #ffffff;
            }
            QPushButton:hover {
                background: rgba(255, 0, 0, 0.5);
            }
        """)
        self.db_clear_btn.clicked.connect(self.on_db_clear)  # type: ignore
        
        self.db_export_btn = QPushButton("📤 Export Database")
        self.db_export_btn.setStyleSheet("""
            QPushButton {
                background: rgba(188, 19, 254, 0.3);
                border: 2px solid #bc13fe;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: 'Consolas';
                font-size: 11px;
                font-weight: bold;
                color: #ffffff;
            }
            QPushButton:hover {
                background: rgba(188, 19, 254, 0.5);
            }
        """)
        self.db_export_btn.clicked.connect(self.on_db_export)  # type: ignore
        
        db_button_layout.addWidget(self.db_clear_btn)
        db_button_layout.addWidget(self.db_export_btn)
        db_button_layout.addStretch()
        
        db_layout.addLayout(db_button_layout)
        
        layout.addWidget(db_frame)
        
        layout.addStretch()
    
    def on_heartbeat_changed(self, value: int) -> None:
        """Handle heartbeat slider change"""
        self.heartbeat_value_label.setText(f"{value} ms")
        self.polling_interval_changed.emit(value)  # type: ignore
    
    def on_theme_changed(self, value: int) -> None:
        """Handle theme slider change"""
        self.theme_value_label.setText(f"{value}°")
        self.theme_changed.emit(value)  # type: ignore
    
    def on_startup_toggled(self, state: int) -> None:
        """Handle startup checkbox toggle"""
        self.startup_toggled.emit(state == Qt.CheckState.Checked.value)  # type: ignore
    
    def on_db_clear(self) -> None:
        """Handle database clear button click"""
        self.database_clear_requested.emit()  # type: ignore
    
    def on_db_export(self) -> None:
        """Handle database export button click"""
        self.database_export_requested.emit()  # type: ignore
    
    def load_current_settings(self, settings_dict: Dict[str, Any]) -> None:
        """Load current settings into UI"""
        if 'polling_interval' in settings_dict:
            self.heartbeat_slider.setValue(settings_dict['polling_interval'])
        
        if 'theme_hue' in settings_dict:
            self.theme_slider.setValue(settings_dict['theme_hue'])
        
        if 'startup' in settings_dict:
            self.startup_check.setChecked(settings_dict['startup'])
        
        if 'minimize_to_tray' in settings_dict:
            self.tray_check.setChecked(settings_dict['minimize_to_tray'])
