#!/usr/bin/env python3
"""
Vitreos Remote Tab - Discord Webhook Configuration
"""
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal


class RemoteTab(QWidget):
    """Discord webhook configuration and remote alerting"""
    
    webhook_saved = pyqtSignal(str)
    alert_config_changed = pyqtSignal(dict)
    test_webhook_requested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.webhook_hidden = True
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the remote configuration layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("📡 Remote Dispatch")
        header_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 16px;
            font-weight: bold;
            color: #bc13fe;
        """)
        layout.addWidget(header_label)
        
        # Webhook configuration
        webhook_frame = QFrame()
        webhook_frame.setStyleSheet("""
            QFrame {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        webhook_layout = QVBoxLayout(webhook_frame)
        
        webhook_label = QLabel("Discord Webhook URL:")
        webhook_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            font-weight: bold;
            color: #00f2ff;
        """)
        webhook_layout.addWidget(webhook_label)
        
        url_layout = QHBoxLayout()
        
        self.webhook_input = QLineEdit()
        self.webhook_input.setPlaceholderText("https://discord.com/api/webhooks/...")
        self.webhook_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.webhook_input.setStyleSheet("""
            QLineEdit {
                background: rgba(8, 8, 10, 0.98);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 6px;
                padding: 8px 12px;
                font-family: 'Consolas';
                font-size: 11px;
                color: #00f2ff;
            }
            QLineEdit:focus {
                border: 2px solid #bc13fe;
            }
        """)
        
        self.toggle_visibility_btn = QPushButton("👁️")
        self.toggle_visibility_btn.setFixedWidth(40)
        self.toggle_visibility_btn.setStyleSheet("""
            QPushButton {
                background: rgba(188, 19, 254, 0.3);
                border: 2px solid #bc13fe;
                border-radius: 6px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(188, 19, 254, 0.5);
            }
        """)
        self.toggle_visibility_btn.clicked.connect(self.toggle_webhook_visibility)  # type: ignore
        
        self.save_webhook_btn = QPushButton("💾 Save")
        self.save_webhook_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 255, 0, 0.3);
                border: 2px solid #00ff00;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: 'Consolas';
                font-size: 11px;
                font-weight: bold;
                color: #ffffff;
            }
            QPushButton:hover {
                background: rgba(0, 255, 0, 0.5);
            }
        """)
        self.save_webhook_btn.clicked.connect(self.on_save_webhook)  # type: ignore
        
        url_layout.addWidget(self.webhook_input)
        url_layout.addWidget(self.toggle_visibility_btn)
        url_layout.addWidget(self.save_webhook_btn)
        
        webhook_layout.addLayout(url_layout)
        
        layout.addWidget(webhook_frame)
        
        # Alert triggers
        triggers_label = QLabel("⚠️ Alert Triggers")
        triggers_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 14px;
            font-weight: bold;
            color: #bc13fe;
            margin-top: 10px;
        """)
        layout.addWidget(triggers_label)
        
        triggers_frame = QFrame()
        triggers_frame.setStyleSheet("""
            QFrame {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        triggers_layout = QGridLayout(triggers_frame)
        
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
        
        self.cpu_check = QCheckBox("CPU > 95%")
        self.cpu_check.setStyleSheet(checkbox_style)
        self.cpu_check.stateChanged.connect(self.on_alert_config_changed)  # type: ignore
        
        self.temp_check = QCheckBox("Temperature > 85°C")
        self.temp_check.setStyleSheet(checkbox_style)
        self.temp_check.stateChanged.connect(self.on_alert_config_changed)  # type: ignore
        
        self.disk_check = QCheckBox("Disk > 95%")
        self.disk_check.setStyleSheet(checkbox_style)
        self.disk_check.stateChanged.connect(self.on_alert_config_changed)  # type: ignore
        
        self.usb_check = QCheckBox("USB Insertion")
        self.usb_check.setStyleSheet(checkbox_style)
        self.usb_check.stateChanged.connect(self.on_alert_config_changed)  # type: ignore
        
        self.security_check = QCheckBox("Security Events")
        self.security_check.setStyleSheet(checkbox_style)
        self.security_check.stateChanged.connect(self.on_alert_config_changed)  # type: ignore
        
        self.network_check = QCheckBox("Network Anomalies")
        self.network_check.setStyleSheet(checkbox_style)
        self.network_check.stateChanged.connect(self.on_alert_config_changed)  # type: ignore
        
        triggers_layout.addWidget(self.cpu_check, 0, 0)
        triggers_layout.addWidget(self.temp_check, 0, 1)
        triggers_layout.addWidget(self.disk_check, 1, 0)
        triggers_layout.addWidget(self.usb_check, 1, 1)
        triggers_layout.addWidget(self.security_check, 2, 0)
        triggers_layout.addWidget(self.network_check, 2, 1)
        
        layout.addWidget(triggers_frame)
        
        # Remote status HUD
        status_label = QLabel("📊 Remote Status")
        status_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 14px;
            font-weight: bold;
            color: #bc13fe;
            margin-top: 10px;
        """)
        layout.addWidget(status_label)
        
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        
        self.status_indicator = QLabel("🔴 OFFLINE")
        self.status_indicator.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            font-weight: bold;
            color: #ff0000;
        """)
        
        self.last_sent_label = QLabel("Last Alert: Never")
        self.last_sent_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 11px;
            color: #888;
        """)
        
        self.test_btn = QPushButton("🧪 Test Alert")
        self.test_btn.setStyleSheet("""
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
        self.test_btn.clicked.connect(self.on_test_webhook)  # type: ignore
        
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.last_sent_label)
        status_layout.addStretch()
        status_layout.addWidget(self.test_btn)
        
        layout.addWidget(status_frame)
        
        layout.addStretch()
    
    def toggle_webhook_visibility(self) -> None:
        """Toggle webhook URL visibility"""
        self.webhook_hidden = not self.webhook_hidden
        if self.webhook_hidden:
            self.webhook_input.setEchoMode(QLineEdit.EchoMode.Password)
        else:
            self.webhook_input.setEchoMode(QLineEdit.EchoMode.Normal)
    
    def on_save_webhook(self) -> None:
        """Handle save webhook button click"""
        webhook_url = self.webhook_input.text()
        if webhook_url:
            self.webhook_saved.emit(webhook_url)  # type: ignore
    
    def on_alert_config_changed(self) -> None:
        """Handle alert configuration change"""
        config: Dict[str, Any] = {
            'cpu': self.cpu_check.isChecked(),
            'temperature': self.temp_check.isChecked(),
            'disk': self.disk_check.isChecked(),
            'usb': self.usb_check.isChecked(),
            'security': self.security_check.isChecked(),
            'network': self.network_check.isChecked(),
        }
        self.alert_config_changed.emit(config)  # type: ignore
    
    def on_test_webhook(self) -> None:
        """Handle test webhook button click"""
        self.test_webhook_requested.emit()  # type: ignore
    
    def set_status(self, online: bool) -> None:
        """Update remote status indicator"""
        if online:
            self.status_indicator.setText("🟢 ONLINE")
            self.status_indicator.setStyleSheet("""
                font-family: 'Consolas';
                font-size: 12px;
                font-weight: bold;
                color: #00ff00;
            """)
        else:
            self.status_indicator.setText("🔴 OFFLINE")
            self.status_indicator.setStyleSheet("""
                font-family: 'Consolas';
                font-size: 12px;
                font-weight: bold;
                color: #ff0000;
            """)
    
    def update_last_sent(self, timestamp: str) -> None:
        """Update last alert sent timestamp"""
        self.last_sent_label.setText(f"Last Alert: {timestamp}")
