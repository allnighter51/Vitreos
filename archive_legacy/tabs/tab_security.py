#!/usr/bin/env python3
"""
Vitreos Security Tab - Security Monitoring & Event Logging
"""
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal


class SecurityTab(QWidget):
    """Security monitoring with shield status and event logging"""
    
    monitoring_toggled = pyqtSignal(bool)
    clear_logs_requested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.monitoring_active = False
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the security monitoring layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("🔒 Security Monitor")
        header_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 16px;
            font-weight: bold;
            color: #bc13fe;
        """)
        layout.addWidget(header_label)
        
        # Shield status panel
        shield_frame = QFrame()
        shield_frame.setStyleSheet("""
            QFrame {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        shield_layout = QHBoxLayout(shield_frame)
        
        self.honeypot_label = QLabel("🍯 Honeypot: INACTIVE")
        self.honeypot_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            color: #888;
        """)
        
        self.login_label = QLabel("👤 Login Monitor: INACTIVE")
        self.login_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            color: #888;
        """)
        
        self.usb_label = QLabel("🔌 USB Shield: INACTIVE")
        self.usb_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            color: #888;
        """)
        
        shield_layout.addWidget(self.honeypot_label)
        shield_layout.addWidget(self.login_label)
        shield_layout.addWidget(self.usb_label)
        shield_layout.addStretch()
        
        layout.addWidget(shield_frame)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.toggle_btn = QPushButton("🛡️ ACTIVATE SECURITY")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff00, stop:1 #00cc00);
                border: 2px solid #00f2ff;
                border-radius: 6px;
                padding: 10px 20px;
                font-family: 'Consolas';
                font-size: 12px;
                font-weight: bold;
                color: #000000;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #33ff33, stop:1 #00ff00);
            }
        """)
        self.toggle_btn.clicked.connect(self.on_toggle_clicked)  # type: ignore
        
        self.clear_btn = QPushButton("🧹 Clear Logs")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(188, 19, 254, 0.3);
                border: 2px solid #bc13fe;
                border-radius: 6px;
                padding: 10px 20px;
                font-family: 'Consolas';
                font-size: 12px;
                font-weight: bold;
                color: #ffffff;
            }
            QPushButton:hover {
                background: rgba(188, 19, 254, 0.5);
            }
        """)
        self.clear_btn.clicked.connect(self.on_clear_clicked)  # type: ignore
        
        control_layout.addWidget(self.toggle_btn)
        control_layout.addWidget(self.clear_btn)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # Security events table
        events_label = QLabel("📋 Security Events")
        events_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 14px;
            font-weight: bold;
            color: #bc13fe;
            margin-top: 10px;
        """)
        layout.addWidget(events_label)
        
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(4)
        self.events_table.setHorizontalHeaderLabels(["Time", "Type", "Description", "Severity"])  # type: ignore
        self.events_table.setStyleSheet("""
            QTableWidget {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 8px;
                font-family: 'Consolas';
                font-size: 11px;
                color: #00f2ff;
                gridline-color: rgba(188, 19, 254, 0.3);
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background: rgba(188, 19, 254, 0.3);
            }
            QHeaderView::section {
                background: rgba(188, 19, 254, 0.5);
                color: #ffffff;
                font-weight: bold;
                padding: 5px;
                border: none;
            }
        """)
        
        if header := self.events_table.horizontalHeader():
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(0, 120)
            header.resizeSection(1, 120)
            header.resizeSection(3, 100)
        
        layout.addWidget(self.events_table)
    
    def on_toggle_clicked(self) -> None:
        """Handle security toggle button click"""
        self.monitoring_active = not self.monitoring_active
        
        if self.monitoring_active:
            self.toggle_btn.setText("🛡️ DEACTIVATE SECURITY")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ff0000, stop:1 #cc0000);
                    border: 2px solid #ff8c00;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-family: 'Consolas';
                    font-size: 12px;
                    font-weight: bold;
                    color: #ffffff;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ff3333, stop:1 #ff0000);
                }
            """)
        else:
            self.toggle_btn.setText("🛡️ ACTIVATE SECURITY")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #00ff00, stop:1 #00cc00);
                    border: 2px solid #00f2ff;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-family: 'Consolas';
                    font-size: 12px;
                    font-weight: bold;
                    color: #000000;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #33ff33, stop:1 #00ff00);
                }
            """)
        
        self.monitoring_toggled.emit(self.monitoring_active)  # type: ignore
    
    def on_clear_clicked(self) -> None:
        """Handle clear logs button click"""
        self.clear_logs_requested.emit()  # type: ignore
        self.events_table.setRowCount(0)
    
    def update_shield_status(self, status: Dict[str, Any]) -> None:
        """Update shield status indicators"""
        honeypot_active = status.get('honeypot', False)
        login_active = status.get('login_monitor', False)
        usb_active = status.get('usb_shield', False)
        
        self.honeypot_label.setText(f"🍯 Honeypot: {'ACTIVE' if honeypot_active else 'INACTIVE'}")
        self.honeypot_label.setStyleSheet(f"""
            font-family: 'Consolas';
            font-size: 12px;
            color: {'#00ff00' if honeypot_active else '#888'};
        """)
        
        self.login_label.setText(f"👤 Login Monitor: {'ACTIVE' if login_active else 'INACTIVE'}")
        self.login_label.setStyleSheet(f"""
            font-family: 'Consolas';
            font-size: 12px;
            color: {'#00ff00' if login_active else '#888'};
        """)
        
        self.usb_label.setText(f"🔌 USB Shield: {'ACTIVE' if usb_active else 'INACTIVE'}")
        self.usb_label.setStyleSheet(f"""
            font-family: 'Consolas';
            font-size: 12px;
            color: {'#00ff00' if usb_active else '#888'};
        """)
    
    def add_security_event(self, event: str) -> None:
        """Add a security event to the table"""
        from datetime import datetime
        
        # Parse event string (format: "TYPE: Description [SEVERITY]")
        parts = event.split(":")
        event_type = parts[0].strip() if len(parts) > 0 else "UNKNOWN"
        
        description = ":".join(parts[1:]).strip() if len(parts) > 1 else event
        
        # Extract severity
        severity = "INFO"
        if "[CRITICAL]" in description:
            severity = "CRITICAL"
            description = description.replace("[CRITICAL]", "").strip()
        elif "[WARNING]" in description:
            severity = "WARNING"
            description = description.replace("[WARNING]", "").strip()
        elif "[HIGH]" in description:
            severity = "HIGH"
            description = description.replace("[HIGH]", "").strip()
        
        # Add row
        row = self.events_table.rowCount()
        self.events_table.insertRow(row)
        
        time_item = QTableWidgetItem(datetime.now().strftime("%H:%M:%S"))
        type_item = QTableWidgetItem(event_type)
        desc_item = QTableWidgetItem(description)
        severity_item = QTableWidgetItem(severity)
        
        # Color code severity
        if severity == "CRITICAL":
            severity_item.setForeground(Qt.GlobalColor.red)  # type: ignore
        elif severity == "HIGH":
            severity_item.setForeground(Qt.GlobalColor.yellow)  # type: ignore
        elif severity == "WARNING":
            severity_item.setForeground(Qt.GlobalColor.yellow)  # type: ignore
        
        self.events_table.setItem(row, 0, time_item)
        self.events_table.setItem(row, 1, type_item)
        self.events_table.setItem(row, 2, desc_item)
        self.events_table.setItem(row, 3, severity_item)
        
        # Auto-scroll to bottom
        self.events_table.scrollToBottom()
