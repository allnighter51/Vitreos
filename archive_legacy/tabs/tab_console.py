#!/usr/bin/env python3
"""
Vitreos Console Tab - Live System Console
"""
from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QPlainTextEdit
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QColor, QFont


class ConsoleTab(QWidget):
    """Matrix-style live console with color-coded logging"""
    
    webhook_test_requested = pyqtSignal()
    clear_console_requested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the console layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Console display
        self.console_display = QPlainTextEdit()
        self.console_display.setReadOnly(True)
        self.console_display.setStyleSheet("""
            QPlainTextEdit {
                background: #000000;
                border: 2px solid #00ff00;
                border-radius: 8px;
                font-family: 'Consolas', 'Courier New';
                font-size: 10px;
                color: #00ff00;
                padding: 10px;
            }
        """)
        
        # Set monospace font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.console_display.setFont(font)
        
        layout.addWidget(self.console_display)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.webhook_test_btn = QPushButton("📡 Test Webhook")
        self.webhook_test_btn.setStyleSheet("""
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
        self.webhook_test_btn.clicked.connect(self.on_webhook_test)  # type: ignore
        
        self.clear_btn = QPushButton("🧹 Clear Console")
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
        self.clear_btn.clicked.connect(self.on_clear_console)  # type: ignore
        
        button_layout.addWidget(self.webhook_test_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Welcome message
        self.write_console("VITREOS SENTINEL CONSOLE v1.0", "INFO")
        self.write_console("System monitoring initialized...", "SUCCESS")
        self.write_console("Awaiting hardware telemetry...", "INFO")
    
    def on_webhook_test(self) -> None:
        """Handle webhook test button click"""
        self.webhook_test_requested.emit()  # type: ignore
    
    def on_clear_console(self) -> None:
        """Handle clear console button click"""
        self.clear_console_requested.emit()  # type: ignore
        self.console_display.clear()
        self.write_console("Console cleared.", "INFO")
    
    def write_console(self, text: str, level: str = "INFO") -> None:
        """Write text to console with color coding based on level"""
        # Color mapping
        color_map = {
            "ERROR": "#ff0000",      # Red
            "WARNING": "#ff8c00",    # Orange
            "SUCCESS": "#00ff00",    # Green
            "DEBUG": "#888888",      # Gray
            "INFO": "#00f2ff",       # Cyan
        }
        
        color = color_map.get(level, "#00f2ff")
        
        # Create formatted text
        cursor = self.console_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)  # type: ignore
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        
        cursor.insertText(f"[{level}] {text}\n", fmt)
        
        # Auto-scroll to bottom
        self.console_display.verticalScrollBar().setValue(  # type: ignore
            self.console_display.verticalScrollBar().maximum()  # type: ignore
        )
    
    def append_log(self, message: str) -> None:
        """Alias method for compatibility with orchestrator signal connections"""
        self.write_console(message, "INFO")
