#!/usr/bin/env python3
"""
Vitreos Processes Tab - Process Management & Optimization
"""
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal


class ProcessesTab(QWidget):
    """Process monitoring with purge protocol and eSports optimization"""
    
    purge_requested = pyqtSignal(list)
    tuning_requested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the processes management layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header with Purge Protocol button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("⚙️ Process Manager")
        title_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 16px;
            font-weight: bold;
            color: #bc13fe;
        """)
        
        self.purge_btn = QPushButton("🔥 PURGE PROTOCOL")
        self.purge_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff0000, stop:1 #cc0000);
                border: 2px solid #ff8c00;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: 'Consolas';
                font-size: 12px;
                font-weight: bold;
                color: #ffffff;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff3333, stop:1 #ff0000);
            }
            QPushButton:pressed {
                background: #990000;
            }
        """)
        self.purge_btn.clicked.connect(self.on_purge_clicked)  # type: ignore
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.purge_btn)
        
        layout.addLayout(header_layout)
        
        # Process table
        self.proc_table = QTableWidget()
        self.proc_table.setColumnCount(4)
        self.proc_table.setHorizontalHeaderLabels(["Process Name", "PID", "RAM (MB)", "CPU %"])  # type: ignore
        self.proc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.proc_table.setStyleSheet("""
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
        
        if header := self.proc_table.horizontalHeader():
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(1, 80)
            header.resizeSection(2, 100)
            header.resizeSection(3, 80)
        
        layout.addWidget(self.proc_table)
        
        # eSports optimization buttons
        esports_layout = QHBoxLayout()
        
        esports_label = QLabel("🎮 eSports Optimization:")
        esports_label.setStyleSheet("""
            font-family: 'Consolas';
            font-size: 12px;
            font-weight: bold;
            color: #00f2ff;
        """)
        
        self.tuning_btn = QPushButton("⚡ Apply Gaming Tuning")
        self.tuning_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #bc13fe, stop:1 #8a0fbf);
                border: 2px solid #00f2ff;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: 'Consolas';
                font-size: 11px;
                font-weight: bold;
                color: #ffffff;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d016ff, stop:1 #bc13fe);
            }
            QPushButton:pressed {
                background: #6a0a8f;
            }
        """)
        self.tuning_btn.clicked.connect(self.on_tuning_clicked)  # type: ignore
        
        esports_layout.addWidget(esports_label)
        esports_layout.addWidget(self.tuning_btn)
        esports_layout.addStretch()
        
        layout.addLayout(esports_layout)
    
    def on_purge_clicked(self) -> None:
        """Handle purge protocol button click"""
        selected_rows = self.proc_table.selectionModel().selectedRows()  # type: ignore
        pids: List[int] = []
        for index in selected_rows:
            pid_item = self.proc_table.item(index.row(), 1)
            if pid_item:
                pids.append(int(pid_item.text()))
        
        if pids:
            self.purge_requested.emit(pids)  # type: ignore
    
    def on_tuning_clicked(self) -> None:
        """Handle tuning button click"""
        self.tuning_requested.emit()  # type: ignore
    
    def update_processes(self, processes: List[Dict[str, Any]]) -> None:
        """Update the process table with new data"""
        self.proc_table.setRowCount(len(processes))
        
        for row, proc in enumerate(processes):
            name_item = QTableWidgetItem(proc.get('name', 'Unknown'))
            pid_item = QTableWidgetItem(str(proc.get('pid', 0)))
            ram_item = QTableWidgetItem(f"{proc.get('memory_mb', 0):.1f}")
            cpu_item = QTableWidgetItem(f"{proc.get('cpu_percent', 0):.1f}")
            
            # Color code high resource usage
            cpu_pct = proc.get('cpu_percent', 0)
            if cpu_pct > 50:
                cpu_item.setForeground(Qt.GlobalColor.red)  # type: ignore
            elif cpu_pct > 25:
                cpu_item.setForeground(Qt.GlobalColor.yellow)  # type: ignore
            
            self.proc_table.setItem(row, 0, name_item)
            self.proc_table.setItem(row, 1, pid_item)
            self.proc_table.setItem(row, 2, ram_item)
            self.proc_table.setItem(row, 3, cpu_item)
