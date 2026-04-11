#!/usr/bin/env python3
"""
Vitreos Remote Tab - Discord Rich Presence Configuration
Phase 3: CustomRP Integration with Tournament Mode
"""
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox, QGridLayout, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.vitreos_widgets import VitreosWinFrame
from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font


class RemoteTab(QWidget):
    """Discord Rich Presence configuration with CustomRP integration"""
    
    presence_config_changed = pyqtSignal(dict)  # Emits config changes
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Build CustomRP integration layout"""
        layout = QGridLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Frame 1: Presence Controls (Top Left)
        self.controls_frame = self._create_controls_frame()
        layout.addWidget(self.controls_frame, 0, 0)
        
        # Frame 2: Custom Status (Top Right)
        self.status_frame = self._create_status_frame()
        layout.addWidget(self.status_frame, 0, 1)
        
        # Frame 3: Live Preview (Bottom, Full Width)
        self.preview_frame = self._create_preview_frame()
        layout.addWidget(self.preview_frame, 1, 0, 1, 2)
        
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)
        
        self.setStyleSheet(f"RemoteTab {{ background: {VITREOS_COLORS['bg_primary']}; }}")
    
    def _create_controls_frame(self) -> VitreosWinFrame:
        """Frame 1: Presence Controls with toggles"""
        frame = VitreosWinFrame(title="PRESENCE_CONTROLS", accent_color="primary_purple")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Toggle: Enable Presence
        self.enable_check = QCheckBox("ENABLE DISCORD PRESENCE")
        self.enable_check.setFont(get_font('mono', 9))
        self.enable_check.setStyleSheet(f"""
            QCheckBox {{
                color: {VITREOS_COLORS['text_primary']};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {VITREOS_COLORS['primary_purple']};
                background: {VITREOS_COLORS['bg_card']};
            }}
            QCheckBox::indicator:checked {{
                background: {VITREOS_COLORS['primary_purple']};
            }}
        """)
        self.enable_check.stateChanged.connect(self._on_config_changed)
        layout.addWidget(self.enable_check)
        
        # Toggle: Show Hardware Stats
        self.hardware_check = QCheckBox("SHOW HARDWARE STATS")
        self.hardware_check.setFont(get_font('mono', 9))
        self.hardware_check.setChecked(True)
        self.hardware_check.setStyleSheet(self.enable_check.styleSheet())
        self.hardware_check.stateChanged.connect(self._on_config_changed)
        layout.addWidget(self.hardware_check)
        
        # Toggle: Show Active Tab
        self.tab_check = QCheckBox("SHOW ACTIVE TAB")
        self.tab_check.setFont(get_font('mono', 9))
        self.tab_check.setChecked(True)
        self.tab_check.setStyleSheet(self.enable_check.styleSheet())
        self.tab_check.stateChanged.connect(self._on_config_changed)
        layout.addWidget(self.tab_check)
        
        # Toggle: Tournament Mode (CCE Branding)
        self.tournament_check = QCheckBox("TOURNAMENT MODE (CCE)")
        self.tournament_check.setFont(get_font('mono', 9))
        self.tournament_check.setStyleSheet(f"""
            QCheckBox {{
                color: {VITREOS_COLORS['warning_orange']};
                font-weight: bold;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {VITREOS_COLORS['warning_orange']};
                background: {VITREOS_COLORS['bg_card']};
            }}
            QCheckBox::indicator:checked {{
                background: {VITREOS_COLORS['warning_orange']};
            }}
        """)
        self.tournament_check.stateChanged.connect(self._on_config_changed)
        layout.addWidget(self.tournament_check)
        
        layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("● DISCONNECTED")
        self.status_label.setFont(get_font('mono', 9))
        self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.status_label)
        
        frame.content_widget.setLayout(layout)
        return frame
    
    def _create_status_frame(self) -> VitreosWinFrame:
        """Frame 2: Custom Status Message"""
        frame = VitreosWinFrame(title="CUSTOM_STATUS", accent_color="cyan")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Status message input
        status_label = QLabel("STATUS MESSAGE:")
        status_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        layout.addWidget(status_label)
        
        self.status_input = QLineEdit()
        self.status_input.setPlaceholderText("Custom status message...")
        self.status_input.setFont(get_font('mono', 9))
        self.status_input.setStyleSheet(f"""
            QLineEdit {{
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
                padding: 8px;
                color: {VITREOS_COLORS['cyan']};
            }}
        """)
        layout.addWidget(self.status_input)
        
        # Large image key
        image_label = QLabel("LARGE IMAGE KEY:")
        image_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        image_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        layout.addWidget(image_label)
        
        self.image_input = QLineEdit()
        self.image_input.setPlaceholderText("vitreos_logo")
        self.image_input.setFont(get_font('mono', 9))
        self.image_input.setStyleSheet(self.status_input.styleSheet())
        layout.addWidget(self.image_input)
        
        layout.addStretch()
        
        # Apply button
        apply_btn = QPushButton("APPLY CUSTOM STATUS")
        apply_btn.setFont(get_font('mono', 9))
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['primary_purple']};
                border: 1px solid {VITREOS_COLORS['primary_purple']};
                padding: 8px;
                color: {VITREOS_COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background: {VITREOS_COLORS['purple_glow']};
            }}
        """)
        layout.addWidget(apply_btn)
        
        frame.content_widget.setLayout(layout)
        return frame
    
    def _create_preview_frame(self) -> VitreosWinFrame:
        """Frame 3: Live Discord Preview"""
        frame = VitreosWinFrame(title="DISCORD_PREVIEW", accent_color="green", badge="LIVE")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Preview box (mimics Discord profile)
        preview_container = QWidget()
        preview_container.setFixedWidth(300)
        preview_container.setStyleSheet(f"""
            QWidget {{
                background: #2B2D31;
                border: 1px solid {VITREOS_COLORS['border_primary']};
                padding: 16px;
            }}
        """)
        
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setSpacing(8)
        
        # App name
        app_label = QLabel("Playing Vitreos")
        app_label.setFont(get_font('mono', 10))
        app_label.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        preview_layout.addWidget(app_label)
        
        # Details (hardware stats)
        self.preview_details = QLabel("CPU: 45% | GPU: 73°C")
        self.preview_details.setFont(get_font('mono', 9))
        self.preview_details.setStyleSheet("color: #B5BAC1;")
        preview_layout.addWidget(self.preview_details)
        
        # State (active tab)
        self.preview_state = QLabel("Analyzing: VITALS")
        self.preview_state.setFont(get_font('mono', 9))
        self.preview_state.setStyleSheet("color: #B5BAC1;")
        preview_layout.addWidget(self.preview_state)
        
        # Image placeholder
        image_placeholder = QLabel("[VITREOS LOGO]")
        image_placeholder.setFont(get_font('mono', 8))
        image_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_placeholder.setFixedSize(80, 80)
        image_placeholder.setStyleSheet(f"""
            background: {VITREOS_COLORS['bg_card']};
            border: 1px solid {VITREOS_COLORS['primary_purple']};
            color: {VITREOS_COLORS['text_dim']};
        """)
        preview_layout.addWidget(image_placeholder)
        
        # Buttons
        button_label = QLabel("▶ Get Vitreos")
        button_label.setFont(get_font('mono', 8))
        button_label.setStyleSheet(f"""
            background: #5865F2;
            color: #FFFFFF;
            padding: 6px 12px;
            border-radius: 4px;
        """)
        preview_layout.addWidget(button_label)
        
        layout.addWidget(preview_container)
        layout.addStretch()
        
        frame.content_widget.setLayout(layout)
        return frame
    
    def _on_config_changed(self) -> None:
        """Handle configuration change"""
        config = {
            'enabled': self.enable_check.isChecked(),
            'show_hardware': self.hardware_check.isChecked(),
            'show_active_tab': self.tab_check.isChecked(),
            'tournament_mode': self.tournament_check.isChecked(),
        }
        self.presence_config_changed.emit(config)
        
        # Update preview
        if config['show_hardware']:
            self.preview_details.setText("CPU: 45% | GPU: 73°C")
        else:
            self.preview_details.setText("Monitoring System")
        
        if config['show_active_tab']:
            self.preview_state.setText("Analyzing: VITALS")
        else:
            self.preview_state.setText("Hardware Sentinel")
    
    def set_connection_status(self, connected: bool) -> None:
        """Update connection status indicator"""
        if connected:
            self.status_label.setText("● CONNECTED")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        else:
            self.status_label.setText("● DISCONNECTED")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
    
    def update_preview(self, cpu: int, gpu_temp: int, tab: str) -> None:
        """Update live preview with current stats"""
        if self.hardware_check.isChecked():
            self.preview_details.setText(f"CPU: {cpu}% | GPU: {gpu_temp}°C")
        
        if self.tab_check.isChecked():
            self.preview_state.setText(f"Analyzing: {tab}")


