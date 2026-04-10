#!/usr/bin/env python3
"""
Vitreos Network Tab - Network Monitoring & Bandwidth Analysis
"""
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QTableWidget, QTableWidgetItem, QHeaderView)
from vitreos_core_ui import LiquidGlassCard, NetworkWaveform


class NetworkTab(QWidget):
    """Network monitoring with adapter selection and bandwidth analysis"""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the network monitoring layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Adapter selection header
        header_layout = QHBoxLayout()
        
        adapter_label = QLabel("Network Adapter:")
        adapter_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            font-weight: bold;
            color: #bc13fe;
        """)
        
        self.adapter_combo = QComboBox()
        self.adapter_combo.setStyleSheet("""
            QComboBox {
                background: rgba(12, 12, 15, 0.95);
                border: 2px solid rgba(188, 19, 254, 0.5);
                border-radius: 6px;
                padding: 5px 10px;
                font-family: 'Consolas';
                font-size: 11px;
                color: #00f2ff;
                min-width: 300px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #bc13fe;
            }
        """)
        
        header_layout.addWidget(adapter_label)
        header_layout.addWidget(self.adapter_combo)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Network waveform visualization
        self.waveform = NetworkWaveform("Network Traffic", self)
        layout.addWidget(self.waveform)
        
        # Statistics cards
        stats_layout = QHBoxLayout()
        
        self.ping_card = LiquidGlassCard("Ping", "-- ms", "Latency", self)
        self.jitter_card = LiquidGlassCard("Jitter", "-- ms", "Variance", self)
        self.download_card = LiquidGlassCard("Download", "-- Mbps", "Receive Rate", self)
        self.upload_card = LiquidGlassCard("Upload", "-- Mbps", "Send Rate", self)
        
        stats_layout.addWidget(self.ping_card)
        stats_layout.addWidget(self.jitter_card)
        stats_layout.addWidget(self.download_card)
        stats_layout.addWidget(self.upload_card)
        
        layout.addLayout(stats_layout)
        
        # Bandwidth hogs table
        hogs_label = QLabel("🔍 Bandwidth Hogs")
        hogs_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 14px;
            font-weight: bold;
            color: #bc13fe;
            margin-top: 10px;
        """)
        layout.addWidget(hogs_label)
        
        self.hogs_table = QTableWidget()
        self.hogs_table.setColumnCount(4)
        self.hogs_table.setHorizontalHeaderLabels(["Process", "PID", "Download", "Upload"])  # type: ignore
        self.hogs_table.setStyleSheet("""
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
        
        if header := self.hogs_table.horizontalHeader():
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(1, 80)
            header.resizeSection(2, 120)
            header.resizeSection(3, 120)
        
        layout.addWidget(self.hogs_table)
    
    def update_adapters(self, adapters: List[str]) -> None:
        """Update the list of available network adapters"""
        self.adapter_combo.clear()
        self.adapter_combo.addItems(adapters)  # type: ignore
    
    def update_ping_stats(self, stats: Dict[str, Any]) -> None:
        """Update ping and network statistics"""
        ping = stats.get('ping', 0)
        jitter = stats.get('jitter', 0)
        download = stats.get('download_mbps', 0)
        upload = stats.get('upload_mbps', 0)
        
        self.ping_card.set_value(f"{ping:.1f} ms")
        self.jitter_card.set_value(f"{jitter:.1f} ms")
        self.download_card.set_value(f"{download:.2f} Mbps")
        self.upload_card.set_value(f"{upload:.2f} Mbps")
        
        # Update waveform with download speed
        self.waveform.add_point(download)
    
    def update_bandwidth_hogs(self, hogs: List[Dict[str, Any]]) -> None:
        """Update the bandwidth hogs table"""
        self.hogs_table.setRowCount(len(hogs))
        
        for row, hog in enumerate(hogs):
            name_item = QTableWidgetItem(hog.get('name', 'Unknown'))
            pid_item = QTableWidgetItem(str(hog.get('pid', 0)))
            download_item = QTableWidgetItem(f"{hog.get('download_mbps', 0):.2f} Mbps")
            upload_item = QTableWidgetItem(f"{hog.get('upload_mbps', 0):.2f} Mbps")
            
            self.hogs_table.setItem(row, 0, name_item)
            self.hogs_table.setItem(row, 1, pid_item)
            self.hogs_table.setItem(row, 2, download_item)
            self.hogs_table.setItem(row, 3, upload_item)
