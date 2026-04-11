#!/usr/bin/env python3
"""
Vitreos Logbook Tab - System Event Logging
"""
from typing import Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QPlainTextEdit, QCheckBox, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime


class LogbookTab(QWidget):
    """System logbook with search and export functionality"""
    
    report_requested = pyqtSignal()
    clear_logs_clicked = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.auto_scroll = True
        self.max_entries = 10000
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the logbook layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        header_label = QLabel("📖 System Logbook")
        header_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 16px;
            font-weight: bold;
            color: #bc13fe;
        """)
        
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.setStyleSheet("""
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
        """)
        self.auto_scroll_check.stateChanged.connect(self.on_auto_scroll_changed)  # type: ignore
        
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.auto_scroll_check)
        
        layout.addLayout(header_layout)
        
        # Search/filter bar
        search_layout = QHBoxLayout()
        
        search_label = QLabel("🔍 Filter:")
        search_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 11px;
            color: #888;
        """)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 6px;
                padding: 5px 10px;
                font-family: 'Consolas';
                font-size: 11px;
                color: #00f2ff;
            }
            QLineEdit:focus {
                border: 2px solid #bc13fe;
            }
        """)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # Log display
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QPlainTextEdit {
                background: rgba(8, 8, 10, 0.98);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 8px;
                font-family: 'Consolas';
                font-size: 10px;
                color: #00f2ff;
                padding: 10px;
            }
        """)
        layout.addWidget(self.log_display)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.report_btn = QPushButton("📄 Generate Report")
        self.report_btn.setStyleSheet("""
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
        self.report_btn.clicked.connect(self.on_report_clicked)  # type: ignore
        
        self.clear_btn = QPushButton("🧹 Clear Logs")
        self.clear_btn.setStyleSheet("""
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
        self.clear_btn.clicked.connect(self.on_clear_clicked)  # type: ignore
        
        action_layout.addWidget(self.report_btn)
        action_layout.addWidget(self.clear_btn)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
    
    def on_auto_scroll_changed(self, state: int) -> None:
        """Handle auto-scroll checkbox state change"""
        self.auto_scroll = (state == Qt.CheckState.Checked.value)
    
    def on_report_clicked(self) -> None:
        """Handle report generation button click"""
        self.report_requested.emit()  # type: ignore
    
    def on_clear_clicked(self) -> None:
        """Handle clear logs button click"""
        self.clear_logs_clicked.emit()  # type: ignore
        self.log_display.clear()
    
    def append_log_entry(self, message: str) -> None:
        """Append a log entry with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        self.log_display.appendPlainText(log_entry)
        
        # Auto-scroll to bottom if enabled
        if self.auto_scroll:
            self.log_display.verticalScrollBar().setValue(  # type: ignore
                self.log_display.verticalScrollBar().maximum()  # type: ignore
            )
        
        # Buffer management - keep only last N entries
        if self.log_display.document().blockCount() > self.max_entries:  # type: ignore
            cursor = self.log_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)  # type: ignore
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 100)  # type: ignore
            cursor.removeSelectedText()


