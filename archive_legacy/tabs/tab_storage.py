#!/usr/bin/env python3
"""
Vitreos Storage Tab - Disk Monitoring & I/O Statistics
"""
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from vitreos_core_ui import LiquidGlassCard


class StorageTab(QWidget):
    """Storage monitoring with I/O statistics and cache management"""
    
    cache_purge_requested = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the storage monitoring layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("💿 Storage Monitor")
        header_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 16px;
            font-weight: bold;
            color: #bc13fe;
        """)
        layout.addWidget(header_label)
        
        # Drives table
        self.drives_table = QTableWidget()
        self.drives_table.setColumnCount(5)
        self.drives_table.setHorizontalHeaderLabels(["Drive", "Total", "Used", "Free", "Usage %"])  # type: ignore
        self.drives_table.setStyleSheet("""
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
        
        if header := self.drives_table.horizontalHeader():
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(0, 80)
            header.resizeSection(4, 100)
        
        layout.addWidget(self.drives_table)
        
        # I/O Statistics cards
        io_label = QLabel("📊 I/O Statistics")
        io_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 14px;
            font-weight: bold;
            color: #bc13fe;
            margin-top: 10px;
        """)
        layout.addWidget(io_label)
        
        io_layout = QGridLayout()
        io_layout.setSpacing(15)
        
        self.read_bytes_card = LiquidGlassCard("Read Bytes", "-- MB", "Total Read", self)
        self.write_bytes_card = LiquidGlassCard("Write Bytes", "-- MB", "Total Write", self)
        self.read_ops_card = LiquidGlassCard("Read Ops", "-- /s", "Operations", self)
        self.write_ops_card = LiquidGlassCard("Write Ops", "-- /s", "Operations", self)
        self.read_speed_card = LiquidGlassCard("Read Speed", "-- MB/s", "Current", self)
        self.write_speed_card = LiquidGlassCard("Write Speed", "-- MB/s", "Current", self)
        
        io_layout.addWidget(self.read_bytes_card, 0, 0)
        io_layout.addWidget(self.write_bytes_card, 0, 1)
        io_layout.addWidget(self.read_ops_card, 1, 0)
        io_layout.addWidget(self.write_ops_card, 1, 1)
        io_layout.addWidget(self.read_speed_card, 2, 0)
        io_layout.addWidget(self.write_speed_card, 2, 1)
        
        layout.addLayout(io_layout)
        
        # Cache purge buttons
        cache_layout = QHBoxLayout()
        
        cache_label = QLabel("🧹 Cache Management:")
        cache_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            font-weight: bold;
            color: #00f2ff;
        """)
        
        self.temp_purge_btn = QPushButton("Clear Temp Files")
        self.temp_purge_btn.setStyleSheet("""
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
        self.temp_purge_btn.clicked.connect(lambda: self.cache_purge_requested.emit("temp"))  # type: ignore
        
        self.prefetch_purge_btn = QPushButton("Clear Prefetch")
        self.prefetch_purge_btn.setStyleSheet("""
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
        self.prefetch_purge_btn.clicked.connect(lambda: self.cache_purge_requested.emit("prefetch"))  # type: ignore
        
        cache_layout.addWidget(cache_label)
        cache_layout.addWidget(self.temp_purge_btn)
        cache_layout.addWidget(self.prefetch_purge_btn)
        cache_layout.addStretch()
        
        layout.addLayout(cache_layout)
    
    def update_disk_stats(self, stats: Dict[str, Any]) -> None:
        """Update disk statistics display"""
        # Update drives table
        drives = stats.get('drives', [])
        self.drives_table.setRowCount(len(drives))
        
        for row, drive in enumerate(drives):
            drive_item = QTableWidgetItem(drive.get('drive', ''))
            total_item = QTableWidgetItem(f"{drive.get('total_gb', 0):.1f} GB")
            used_item = QTableWidgetItem(f"{drive.get('used_gb', 0):.1f} GB")
            free_item = QTableWidgetItem(f"{drive.get('free_gb', 0):.1f} GB")
            usage_item = QTableWidgetItem(f"{drive.get('usage_percent', 0):.1f}%")
            
            # Color code usage
            usage_pct = drive.get('usage_percent', 0)
            if usage_pct > 90:
                usage_item.setForeground(Qt.GlobalColor.red)  # type: ignore
            elif usage_pct > 75:
                usage_item.setForeground(Qt.GlobalColor.yellow)  # type: ignore
            
            self.drives_table.setItem(row, 0, drive_item)
            self.drives_table.setItem(row, 1, total_item)
            self.drives_table.setItem(row, 2, used_item)
            self.drives_table.setItem(row, 3, free_item)
            self.drives_table.setItem(row, 4, usage_item)
        
        # Update I/O cards
        io_stats = stats.get('io', {})
        self.read_bytes_card.set_value(f"{io_stats.get('read_mb', 0):.1f} MB")
        self.write_bytes_card.set_value(f"{io_stats.get('write_mb', 0):.1f} MB")
        self.read_ops_card.set_value(f"{io_stats.get('read_ops', 0)}")
        self.write_ops_card.set_value(f"{io_stats.get('write_ops', 0)}")
        self.read_speed_card.set_value(f"{io_stats.get('read_speed_mbps', 0):.2f} MB/s")
        self.write_speed_card.set_value(f"{io_stats.get('write_speed_mbps', 0):.2f} MB/s")
