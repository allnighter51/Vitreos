"""
Storage Tab - Deep Sector Analysis
60% Drive Array | 40% I/O Analytics
"""

from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont
import random

from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font, get_color
from src.ui.vitreos_widgets import VitreosWinFrame, VitreosCircularGauge, VitreosSegmentedBar


class SectorScanWidget(QWidget):
    """ASCII character block visualization for disk I/O."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.activity = 0.0
        self.blocks = ['░', '▒', '▓', '█']
        self.grid_data = [[0 for _ in range(40)] for _ in range(8)]
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(100)
    
    def set_activity(self, activity: float) -> None:
        """Set I/O activity level (0-100)."""
        self.activity = activity
    
    def _animate(self) -> None:
        """Animate sector scan."""
        # Scroll grid left
        for row in self.grid_data:
            row.pop(0)
            # Add new column based on activity
            if self.activity > 50:
                row.append(random.randint(2, 3))
            elif self.activity > 20:
                row.append(random.randint(1, 2))
            else:
                row.append(random.randint(0, 1))
        
        self.update()
    
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background
        painter.fillRect(0, 0, width, height, get_color('bg_card'))
        
        # Draw grid
        cell_width = width / 40
        cell_height = height / 8
        
        font = get_font('mono', 10)
        painter.setFont(font)
        
        for row_idx, row in enumerate(self.grid_data):
            for col_idx, val in enumerate(row):
                x = int(col_idx * cell_width)
                y = int(row_idx * cell_height)
                
                # Color based on intensity
                if val == 3:
                    color = get_color('primary_purple')
                elif val == 2:
                    color = get_color('purple_dim')
                elif val == 1:
                    color = get_color('text_secondary')
                else:
                    color = get_color('text_darker')
                
                painter.setPen(color)
                painter.drawText(x, y + int(cell_height * 0.8), self.blocks[val])


class StorageTab(QWidget):
    """Storage tab with 60/40 asymmetric layout."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.drive_widgets: Dict[str, tuple] = {}
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Left 60%: Drive Array
        left_panel = VitreosWinFrame(
            title="DRIVE_ARRAY",
            accent_color="primary_purple"
        )
        
        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(12, 12, 12, 12)
        self.left_layout.setSpacing(8)
        
        # Background watermark
        fs_label = QLabel("FILE SYSTEM: [DETECTING...]")
        fs_label.setFont(get_font('mono', 24))
        fs_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darkest']}; opacity: 0.3;")
        fs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(fs_label)
        
        self.drives_layout = QVBoxLayout()
        self.drives_layout.setSpacing(12)
        self.left_layout.addLayout(self.drives_layout)
        
        self.left_layout.addStretch()
        left_panel.set_content_layout(self.left_layout)
        main_layout.addWidget(left_panel, 6)
        
        # Right 40%: I/O Analytics
        right_panel = VitreosWinFrame(
            title="IO_ANALYTICS",
            accent_color="cyan"
        )
        
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)
        
        # Partition health gauge
        health_label = QLabel("PARTITION HEALTH")
        health_label.setFont(get_font('mono', FONT_SIZES['label']))
        health_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        right_layout.addWidget(health_label)
        
        gauge_row = QHBoxLayout()
        self.health_gauge = VitreosCircularGauge(segments=40)
        gauge_row.addWidget(self.health_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        right_layout.addLayout(gauge_row)
        
        self.health_status = QLabel("100% HEALTHY")
        self.health_status.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.health_status.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        self.health_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.health_status)
        
        # SMART status
        smart_label = QLabel("SMART STATUS")
        smart_label.setFont(get_font('mono', FONT_SIZES['label']))
        smart_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        right_layout.addWidget(smart_label)
        
        smart_grid = QGridLayout()
        smart_grid.setSpacing(6)
        
        self.smart_labels = {}
        smart_attrs = [
            ('TEMP', 'temp', '°C'),
            ('POWER ON', 'power_on', 'hrs'),
            ('REALLOCATED', 'reallocated', 'sectors'),
            ('PENDING', 'pending', 'sectors'),
        ]
        
        for i, (label, key, unit) in enumerate(smart_attrs):
            attr_widget = QWidget()
            attr_widget.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
            """)
            attr_layout = QVBoxLayout(attr_widget)
            attr_layout.setContentsMargins(6, 6, 6, 6)
            attr_layout.setSpacing(2)
            
            attr_label = QLabel(label)
            attr_label.setFont(get_font('mono', FONT_SIZES['micro']))
            attr_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            attr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            attr_layout.addWidget(attr_label)
            
            value_label = QLabel(f"0 {unit}")
            value_label.setFont(get_font('mono', FONT_SIZES['small']))
            value_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            attr_layout.addWidget(value_label)
            
            self.smart_labels[key] = value_label
            smart_grid.addWidget(attr_widget, i // 2, i % 2)
        
        right_layout.addLayout(smart_grid)
        right_layout.addStretch()
        right_panel.set_content_layout(right_layout)
        main_layout.addWidget(right_panel, 4)
    
    def update_stats(self, data: Dict[str, Any]) -> None:
        """Update storage display from telemetry."""
        storage_data = data.get('storage', {})
        drives = storage_data.get('drives', [])
        
        for drive in drives:
            mountpoint = drive.get('mountpoint', '/')
            device = drive.get('device', 'Unknown')
            used_gb = drive.get('usedGB', 0)
            total_gb = drive.get('totalGB', 0)
            percent = drive.get('percent', 0)
            
            if mountpoint not in self.drive_widgets:
                # Create new drive widget
                drive_container = QWidget()
                drive_container.setStyleSheet(f"""
                    background: {VITREOS_COLORS['bg_card']};
                    border: 1px solid {VITREOS_COLORS['border_secondary']};
                """)
                drive_layout = QVBoxLayout(drive_container)
                drive_layout.setContentsMargins(12, 12, 12, 12)
                drive_layout.setSpacing(6)
                
                # Header
                header_row = QHBoxLayout()
                drive_label = QLabel(f"{device} ({mountpoint})")
                drive_label.setFont(get_font('mono', FONT_SIZES['label']))
                drive_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
                header_row.addWidget(drive_label)
                header_row.addStretch()
                
                usage_label = QLabel(f"{used_gb:.1f} / {total_gb:.1f} GB")
                usage_label.setFont(get_font('mono', FONT_SIZES['small']))
                usage_label.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
                header_row.addWidget(usage_label)
                drive_layout.addLayout(header_row)
                
                # Sector scan
                sector_scan = SectorScanWidget()
                drive_layout.addWidget(sector_scan)
                
                # Usage bar
                usage_bar = VitreosSegmentedBar(segments=24, height=6, color='primary_purple')
                drive_layout.addWidget(usage_bar)
                
                self.drives_layout.addWidget(drive_container)
                self.drive_widgets[mountpoint] = (usage_label, usage_bar, sector_scan)
            else:
                usage_label, usage_bar, sector_scan = self.drive_widgets[mountpoint]
                usage_label.setText(f"{used_gb:.1f} / {total_gb:.1f} GB")
                usage_bar.set_value(percent, 100)
                sector_scan.set_activity(percent)
        
        # Update health gauge (use first drive)
        if drives:
            first_drive = drives[0]
            health = 100 - first_drive.get('percent', 0) * 0.2  # Simulate health
            self.health_gauge.set_value(health, 100, 'green')
            self.health_status.setText(f"{health:.0f}% HEALTHY")
            
            # Update SMART (placeholder)
            self.smart_labels['temp'].setText("35 °C")
            self.smart_labels['power_on'].setText("1234 hrs")
            self.smart_labels['reallocated'].setText("0 sectors")
            self.smart_labels['pending'].setText("0 sectors")


__all__ = ['StorageTab']
