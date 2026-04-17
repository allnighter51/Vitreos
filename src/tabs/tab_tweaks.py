#!/usr/bin/env python3
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportIncompatibleMethodOverride=false, reportConstantRedefinition=false, reportUnboundVariable=false, reportPossiblyUnboundVariable=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportMissingTypeArgument=false, reportArgumentType=false, reportUnusedImport=false, reportUnusedVariable=false
"""
Vitreos Tweaks Tab - System Optimizations
Replaces Logbook with OS-level performance tweaks
"""
from typing import Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.core.vitreos_tweaks import SystemTweaker
from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font


class TweakWorker(QThread):
    """Background worker for blocking tweak operations"""
    
    finished = pyqtSignal(bool, str)
    
    def __init__(self, tweak_func):
        super().__init__()
        self.tweak_func = tweak_func
    
    def run(self):
        success, message = self.tweak_func()
        self.finished.emit(success, message)


class TweaksTab(QWidget):
    """System optimization and performance tweaks"""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.tweaker = SystemTweaker()
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the tweaks layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("⚡ SYSTEM TWEAKS")
        header.setFont(get_font('mono', 16))
        header.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']}; font-weight: bold;")
        layout.addWidget(header)
        
        # Description
        desc = QLabel("OS-level optimizations for maximum performance. Use with caution.")
        desc.setFont(get_font('mono', FONT_SIZES['small']))
        desc.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(desc)
        
        # Tweak buttons grid
        tweaks_grid = QGridLayout()
        tweaks_grid.setSpacing(12)
        
        # Row 0: Power Plan
        power_btn = self._create_tweak_button(
            "🔋 ULTIMATE PERFORMANCE",
            "Unlock Windows Ultimate Performance power plan",
            self.on_ultimate_performance
        )
        tweaks_grid.addWidget(power_btn, 0, 0)
        
        # Row 0: Game DVR
        gamedvr_btn = self._create_tweak_button(
            "🎮 DISABLE GAME DVR",
            "Disable Xbox Game Bar and DVR for FPS boost",
            self.on_disable_game_dvr
        )
        tweaks_grid.addWidget(gamedvr_btn, 0, 1)
        
        # Row 1: Telemetry
        telemetry_btn = self._create_tweak_button(
            "🔒 DISABLE TELEMETRY",
            "Stop Windows telemetry and DiagTrack service",
            self.on_disable_telemetry
        )
        tweaks_grid.addWidget(telemetry_btn, 1, 0)
        
        # Row 1: DNS/Cache
        dns_btn = self._create_tweak_button(
            "🧹 FLUSH DNS & CACHE",
            "Clear DNS cache and Windows temp directories",
            self.on_flush_dns
        )
        tweaks_grid.addWidget(dns_btn, 1, 1)
        
        # Row 2: System Repair (full width)
        repair_btn = self._create_tweak_button(
            "🔧 SYSTEM REPAIR (SFC + DISM)",
            "Run system file checker and DISM repair (SLOW)",
            self.on_system_repair
        )
        tweaks_grid.addWidget(repair_btn, 2, 0, 1, 2)
        
        layout.addLayout(tweaks_grid)
        
        # Output console
        console_label = QLabel("OUTPUT CONSOLE")
        console_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        console_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        layout.addWidget(console_label)
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(get_font('mono', 9))
        self.console.setStyleSheet(f"""
            QTextEdit {{
                background: {VITREOS_COLORS['bg_secondary']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
                color: {VITREOS_COLORS['cyan']};
                padding: 8px;
            }}
        """)
        layout.addWidget(self.console, 1)
        
        # Initial message
        self.log_message("TWEAKS", "System optimization engine initialized", "primary_purple")
        self.log_message("WARN", "These tweaks modify system settings. Use at your own risk.", "warning_orange")
    
    def _create_tweak_button(self, title: str, desc: str, callback) -> QPushButton:
        """Create a styled tweak button"""
        btn = QPushButton(f"{title}\n{desc}")
        btn.setFont(get_font('mono', 9))
        btn.setMinimumHeight(60)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['bg_card']};
                border: 2px solid {VITREOS_COLORS['border_primary']};
                color: {VITREOS_COLORS['text_primary']};
                padding: 10px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {VITREOS_COLORS['border_primary']};
                border: 2px solid {VITREOS_COLORS['warning_orange']};
            }}
            QPushButton:pressed {{
                background: {VITREOS_COLORS['warning_orange']};
                color: {VITREOS_COLORS['bg_primary']};
            }}
        """)
        btn.clicked.connect(callback)
        return btn
    
    def log_message(self, level: str, message: str, color: str = 'cyan') -> None:
        """Append message to console"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_hex = VITREOS_COLORS.get(color, VITREOS_COLORS['cyan'])
        
        html = f"""
        <span style="color: {VITREOS_COLORS['text_darker']};">[{timestamp}]</span>
        <span style="color: {color_hex}; font-weight: bold;">[{level}]</span>
        <span style="color: {VITREOS_COLORS['text_dim']};">{message}</span>
        """
        
        self.console.append(html)
        scrollbar = self.console.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())
    
    def on_ultimate_performance(self):
        """Enable Ultimate Performance power plan"""
        self.log_message("EXEC", "Activating Ultimate Performance mode...", "warning_orange")
        success, message = self.tweaker.enable_ultimate_performance()
        
        if success:
            self.log_message("OK", message, "green")
        else:
            self.log_message("FAIL", message, "critical_red")
    
    def on_disable_game_dvr(self):
        """Disable Xbox Game DVR"""
        self.log_message("EXEC", "Disabling Xbox Game DVR and Game Bar...", "warning_orange")
        success, message = self.tweaker.disable_game_dvr()
        
        if success:
            self.log_message("OK", message, "green")
        else:
            self.log_message("FAIL", message, "critical_red")
    
    def on_disable_telemetry(self):
        """Disable Windows telemetry"""
        self.log_message("EXEC", "Disabling Windows telemetry...", "warning_orange")
        success, message = self.tweaker.disable_telemetry()
        
        if success:
            self.log_message("OK", message, "green")
        else:
            self.log_message("FAIL", message, "critical_red")
    
    def on_flush_dns(self):
        """Flush DNS and clear cache"""
        self.log_message("EXEC", "Flushing DNS and clearing cache...", "warning_orange")
        success, message = self.tweaker.flush_dns_and_cache()
        
        if success:
            self.log_message("OK", message, "green")
        else:
            self.log_message("FAIL", message, "critical_red")
    
    def on_system_repair(self):
        """Run system repair (blocking operation)"""
        self.log_message("EXEC", "Starting system repair (SFC + DISM). This will take several minutes...", "warning_orange")
        
        # Run in background thread
        self.repair_worker = TweakWorker(self.tweaker.run_system_repair)
        self.repair_worker.finished.connect(self.on_repair_finished)
        self.repair_worker.start()
    
    def on_repair_finished(self, success: bool, message: str):
        """Handle repair completion"""
        if success:
            self.log_message("OK", "System repair completed", "green")
            for line in message.split('\n'):
                if line.strip():
                    self.log_message("INFO", line, "cyan")
        else:
            self.log_message("FAIL", message, "critical_red")


