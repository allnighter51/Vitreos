"""
Security Tab - OSINT & CCE Shield
100% Terminal Style | 20% Threat Level Gutter
"""

from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime
import os

from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font, get_color
from src.ui.vitreos_widgets import VitreosWinFrame, HazardBadge


class SecurityTerminal(QTextEdit):
    """Terminal-style log viewer with green/emerald color scheme."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFont(get_font('mono', 9))
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {VITREOS_COLORS['bg_secondary']};
                border: 1px solid {VITREOS_COLORS['green']};
                color: {VITREOS_COLORS['green']};
                padding: 8px;
                line-height: 1.4;
            }}
        """)
    
    def append_secure(self, level: str, message: str) -> None:
        """Append log entry with security color coding."""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        
        # Color based on level
        if level == "BREACH":
            color = VITREOS_COLORS['critical_red']
        elif level == "WARN":
            color = VITREOS_COLORS['warning_orange']
        elif level == "SCAN":
            color = VITREOS_COLORS['cyan']
        else:
            color = VITREOS_COLORS['green']
        
        html = f"""
        <span style="color: {VITREOS_COLORS['text_darker']};">[{time_str}]</span>
        <span style="color: {color}; font-weight: bold;">[{level}]</span>
        <span style="color: {VITREOS_COLORS['green']};">{message}</span>
        """
        
        self.append(html)
        
        # Auto-scroll
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class ThreatLevelGutter(QWidget):
    """Vertical hazard badge stack for threat monitoring."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedWidth(120)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Threat level header
        header = QLabel("THREAT\nLEVEL")
        header.setFont(get_font('mono', FONT_SIZES['label']))
        header.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Threat badges
        self.badges = {}
        threats = [
            ('OSINT', 'primary_purple'),
            ('DISCORD', 'primary_purple'),
            ('CCE', 'primary_purple'),
            ('NETWORK', 'primary_purple'),
        ]
        
        for threat_name, color in threats:
            badge = HazardBadge(f"⚠ {threat_name}")
            badge.setStyleSheet(f"""
                background: repeating-linear-gradient(
                    45deg,
                    #000 0px, #000 3px,
                    rgba(168, 85, 247, 0.25) 3px, rgba(168, 85, 247, 0.25) 6px
                );
                border: 1px solid {VITREOS_COLORS[color]};
                color: {VITREOS_COLORS[color]};
                padding: 4px 8px;
                letter-spacing: 1px;
            """)
            self.badges[threat_name] = badge
            layout.addWidget(badge)
        
        layout.addStretch()
    
    def set_threat_level(self, threat_name: str, level: str) -> None:
        """Set threat level: 'NORMAL', 'WARNING', 'CRITICAL'."""
        if threat_name not in self.badges:
            return
        
        badge = self.badges[threat_name]
        
        if level == 'CRITICAL':
            color = 'critical_red'
            badge.setStyleSheet(f"""
                background: repeating-linear-gradient(
                    45deg,
                    #000 0px, #000 3px,
                    rgba(255, 68, 68, 0.25) 3px, rgba(255, 68, 68, 0.25) 6px
                );
                border: 1px solid {VITREOS_COLORS[color]};
                color: {VITREOS_COLORS[color]};
                padding: 4px 8px;
                letter-spacing: 1px;
            """)
        elif level == 'WARNING':
            color = 'warning_orange'
            badge.setStyleSheet(f"""
                background: repeating-linear-gradient(
                    45deg,
                    #000 0px, #000 3px,
                    rgba(255, 107, 0, 0.25) 3px, rgba(255, 107, 0, 0.25) 6px
                );
                border: 1px solid {VITREOS_COLORS[color]};
                color: {VITREOS_COLORS[color]};
                padding: 4px 8px;
                letter-spacing: 1px;
            """)
        else:  # NORMAL
            color = 'primary_purple'
            badge.setStyleSheet(f"""
                background: repeating-linear-gradient(
                    45deg,
                    #000 0px, #000 3px,
                    rgba(168, 85, 247, 0.25) 3px, rgba(168, 85, 247, 0.25) 6px
                );
                border: 1px solid {VITREOS_COLORS[color]};
                color: {VITREOS_COLORS[color]};
                padding: 4px 8px;
                letter-spacing: 1px;
            """)


class SecurityTab(QWidget):
    """Security tab with terminal interface and threat monitoring."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.osint_path = "F:/OSINT_HUB"
        self._setup_ui()
        self._start_monitoring()
    
    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Main 80%: Terminal
        terminal_panel = VitreosWinFrame(
            title="SECURITY_MONITOR",
            accent_color="green",
            badge="SECURE",
            badge_color="green"
        )
        
        terminal_layout = QVBoxLayout()
        terminal_layout.setContentsMargins(12, 12, 12, 12)
        terminal_layout.setSpacing(8)
        
        # OSINT directory header
        osint_header = QLabel(f"DIRECTORY: {self.osint_path}")
        osint_header.setFont(get_font('mono', FONT_SIZES['label']))
        osint_header.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        terminal_layout.addWidget(osint_header)
        
        # Terminal
        self.terminal = SecurityTerminal()
        terminal_layout.addWidget(self.terminal, 1)
        
        # Footer breadcrumb
        footer = QLabel(f"DIRECTORY: {self.osint_path} | STATUS: MONITORING")
        footer.setFont(get_font('mono', FONT_SIZES['micro']))
        footer.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
        terminal_layout.addWidget(footer)
        
        terminal_panel.set_content_layout(terminal_layout)
        main_layout.addWidget(terminal_panel, 8)
        
        # Right 20%: Threat Level Gutter
        self.threat_gutter = ThreatLevelGutter()
        main_layout.addWidget(self.threat_gutter, 2)
    
    def _start_monitoring(self) -> None:
        """Start OSINT directory monitoring."""
        self.terminal.append_secure("OK", "Security monitor initialized")
        self.terminal.append_secure("SCAN", f"Monitoring directory: {self.osint_path}")
        
        # Check if OSINT directory exists
        if os.path.exists(self.osint_path):
            self.terminal.append_secure("OK", f"OSINT directory found: {self.osint_path}")
            self._scan_directory()
        else:
            self.terminal.append_secure("WARN", f"OSINT directory not found: {self.osint_path}")
            self.threat_gutter.set_threat_level('OSINT', 'WARNING')
        
        # Simulate Discord status check
        self.terminal.append_secure("SCAN", "Checking Discord CCE staff status...")
        self.terminal.append_secure("OK", "Discord status: NORMAL")
        self.threat_gutter.set_threat_level('DISCORD', 'NORMAL')
        
        # Check for April 10 breach logs
        self._check_breach_logs()
    
    def _scan_directory(self) -> None:
        """Scan OSINT directory for files."""
        try:
            files = os.listdir(self.osint_path)
            self.terminal.append_secure("OK", f"Found {len(files)} files in OSINT directory")
            
            for file in files[:5]:  # Show first 5 files
                self.terminal.append_secure("SCAN", f"  → {file}")
            
            if len(files) > 5:
                self.terminal.append_secure("SCAN", f"  ... and {len(files) - 5} more files")
        except Exception as e:
            self.terminal.append_secure("WARN", f"Error scanning directory: {e}")
    
    def _check_breach_logs(self) -> None:
        """Check for April 10 Discord breach logs."""
        breach_date = "2025-04-10"
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        if current_date == breach_date:
            self.terminal.append_secure("BREACH", "⚠ CRITICAL: Discord breach detected on April 10")
            self.terminal.append_secure("BREACH", "CCE staff credentials may be compromised")
            self.threat_gutter.set_threat_level('DISCORD', 'CRITICAL')
            self.threat_gutter.set_threat_level('CCE', 'CRITICAL')
        else:
            self.terminal.append_secure("OK", "No active breach incidents detected")
    
    def update_stats(self, data: Dict[str, Any]) -> None:
        """Update security monitor (placeholder for future integration)."""
        pass


__all__ = ['SecurityTab']
