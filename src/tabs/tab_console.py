#!/usr/bin/env python3
# pyright: reportUnknownParameterType=false, reportMissingTypeArgument=false, reportUnknownVariableType=false, reportUnknownMemberType=false
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
        
        # Task 3: Set maximum block count for history preservation (1000 lines)
        self.console_display.setMaximumBlockCount(1000)
        
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
        
        # Load historical logs from database
        self.load_historical_logs()
        
        self.write_console("Awaiting hardware telemetry...", "INFO")
    
    def load_historical_logs(self) -> None:
        """Load last 50 historical logs from database (migrated from Logbook)"""
        try:
            from src.core.vitreos_db import VitreosDB
            
            # Create temporary database connection to query logs
            db = VitreosDB()
            logs = db.get_recent_logs(limit=50)
            db.close()
            
            if logs:
                self.write_console(f"Loaded {len(logs)} historical log entries from database", "SUCCESS")
                self.write_console("─" * 60, "INFO")
                
                # Display logs in reverse order (oldest first)
                for log in reversed(logs):
                    timestamp = log['timestamp']
                    cpu_usage = log['cpu_usage']
                    cpu_temp = log['cpu_temp']
                    gpu_usage = log['gpu_usage']
                    gpu_temp = log['gpu_temp']
                    ram_usage = log['ram_usage']
                    
                    log_line = (
                        f"{timestamp} | "
                        f"CPU: {cpu_usage:.1f}% @ {cpu_temp:.0f}°C | "
                        f"GPU: {gpu_usage:.0f}% @ {gpu_temp:.0f}°C | "
                        f"RAM: {ram_usage:.1f}%"
                    )
                    
                    # Use cyan color for historical logs
                    self.write_console(log_line, "INFO")
                
                self.write_console("─" * 60, "INFO")
                self.write_console("Historical logs loaded. Live monitoring active.", "SUCCESS")
            else:
                self.write_console("No historical logs found in database", "INFO")
        
        except Exception as e:
            self.write_console(f"Failed to load historical logs: {e}", "ERROR")
    
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
        from datetime import datetime
        
        # Color mapping
        color_map = {
            "ERROR": "#ff0000",      # Red
            "WARNING": "#ff8c00",    # Orange
            "SUCCESS": "#00ff00",    # Green
            "DEBUG": "#888888",      # Gray
            "INFO": "#00f2ff",       # Cyan
            "TELEMETRY": "#ffaa00",  # Amber for raw telemetry
            "NAV": "#00f2ff",        # Cyan for navigation
            "VITREOS": "#00f2ff",    # Cyan for app events
            "INPUT": "#ffff00",      # Yellow for user interactions
        }
        
        color = color_map.get(level, "#00f2ff")
        
        # Task 3: Add timestamp to every entry for history preservation
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Create formatted text
        cursor = self.console_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)  # type: ignore
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        
        # Format: [HH:MM:SS] [LEVEL] message
        cursor.insertText(f"[{timestamp}] [{level}] {text}\n", fmt)
        
        # Auto-scroll to bottom
        self.console_display.verticalScrollBar().setValue(  # type: ignore
            self.console_display.verticalScrollBar().maximum()  # type: ignore
        )
    
    def append_log(self, message: str) -> None:
        """Alias method for compatibility with orchestrator signal connections"""
        self.write_console(message, "INFO")
    
    def write_app_event(self, message: str) -> None:
        """Write app event to console (cyan text) - for [NAV] and [VITREOS] logs"""
        # Determine level from message prefix
        if message.startswith("[NAV]"):
            level = "NAV"
            text = message[5:].strip()  # Remove [NAV] prefix
        elif message.startswith("[VITREOS]"):
            level = "VITREOS"
            text = message[9:].strip()  # Remove [VITREOS] prefix
        elif message.startswith("[INPUT]"):
            level = "INPUT"
            text = message[7:].strip()  # Remove [INPUT] prefix
        elif message.startswith("[TELEMETRY]"):
            level = "TELEMETRY"
            text = message[12:].strip()  # Remove [TELEMETRY] prefix
        elif message.startswith("[DEBUG]"):
            level = "DEBUG"
            text = message[7:].strip()  # Remove [DEBUG] prefix
        else:
            level = "INFO"
            text = message
        
        self.write_console(text, level)
    
    def write_raw(self, data: dict) -> None:
        """Write raw telemetry packet to console (amber text)"""
        # Format raw telemetry data
        cpu_load = data.get('cpu', {}).get('totalLoad', 0)
        gpu_temp = data.get('gpu', {}).get('temp', 0)
        gpu_usage = data.get('gpu', {}).get('usage', 0)
        vram_used = data.get('gpu', {}).get('vramUsed', 0)
        vram_total = data.get('gpu', {}).get('vramTotal', 0)
        mem_used = data.get('memory', {}).get('usedGB', 0)
        mem_total = data.get('memory', {}).get('totalGB', 0)
        
        raw_packet = (
            f"CPU: {cpu_load:.1f}% | "
            f"GPU: {gpu_usage:.0f}% @ {gpu_temp:.0f}°C | "
            f"VRAM: {vram_used:.1f}/{vram_total:.1f}GB | "
            f"RAM: {mem_used:.1f}/{mem_total:.1f}GB"
        )
        
        self.write_console(raw_packet, "TELEMETRY")


