#!/usr/bin/env python3
"""
Vitreos Processes Tab - Tactical Process Management
Features: High-density grid, Affinity Lock, Entropy Scanner, Thermal Pressure Index
"""
import math
import psutil
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainter, QBrush

try:
    from src.ui.vitreos_theme import VITREOS_COLORS, get_font
except ImportError:
    from src.ui.vitreos_theme import VITREOS_COLORS, get_font


class TPIBar(QWidget):
    """Vertical 5-segment TPI (Thermal Pressure Index) bar"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.value = 0.0  # 0-100
        self.setFixedSize(12, 30)
    
    def set_value(self, value: float) -> None:
        self.value = max(0, min(100, value))
        self.update()
    
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        segment_height = 5
        gap = 1
        filled_segments = int((self.value / 100) * 5)
        
        for i in range(5):
            y = (4 - i) * (segment_height + gap)  # Bottom to top
            
            if i < filled_segments:
                # Critical red for high TPI
                if self.value > 75:
                    color = QColor(VITREOS_COLORS['critical_red'])
                elif self.value > 50:
                    color = QColor(VITREOS_COLORS['warning_orange'])
                else:
                    color = QColor(VITREOS_COLORS['cyan'])
            else:
                color = QColor(VITREOS_COLORS['segment_off'])
            
            painter.fillRect(0, y, 12, segment_height, QBrush(color))


class ProcessesTab(QWidget):
    """Tactical process monitoring with affinity lock and entropy scanning"""
    
    log_message = pyqtSignal(str, str, str)  # (level, message, color)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.processes_data = []
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the tactical grid layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header with tactical controls
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("TACTICAL_GRID")
        title_label.setFont(get_font('mono', 11))
        title_label.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']};")
        
        self.lock_btn = QPushButton("LOCK TO PHYSICAL")
        self.lock_btn.setFont(get_font('mono', 8))
        self.lock_btn.setFixedHeight(24)
        self.lock_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['bg_secondary']};
                border: 1px solid {VITREOS_COLORS['cyan']};
                color: {VITREOS_COLORS['cyan']};
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background: {VITREOS_COLORS['cyan']};
                color: {VITREOS_COLORS['bg_primary']};
            }}
        """)
        self.lock_btn.clicked.connect(self.on_affinity_lock)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.lock_btn)
        
        layout.addLayout(header_layout)
        
        # High-density process table
        self.proc_table = QTableWidget()
        self.proc_table.setColumnCount(6)
        self.proc_table.setHorizontalHeaderLabels(["NAME", "PID", "CPU %", "RAM (MB)", "TPI", "ENTROPY"])
        self.proc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.proc_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setShowGrid(False)
        self.proc_table.setFont(get_font('mono', 8))
        
        # Vitreos aesthetic styling
        self.proc_table.setStyleSheet(f"""
            QTableWidget {{
                background: {VITREOS_COLORS['bg_primary']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
                color: {VITREOS_COLORS['text_primary']};
                gridline-color: {VITREOS_COLORS['border_primary']};
            }}
            QTableWidget::item {{
                padding: 2px 4px;
                border-bottom: 1px solid {VITREOS_COLORS['border_primary']};
            }}
            QTableWidget::item:selected {{
                background: {VITREOS_COLORS['primary_purple']};
                color: {VITREOS_COLORS['text_primary']};
            }}
            QHeaderView::section {{
                background: {VITREOS_COLORS['bg_secondary']};
                color: {VITREOS_COLORS['text_primary']};
                font-weight: bold;
                padding: 4px;
                border: none;
                border-bottom: 1px solid {VITREOS_COLORS['border_secondary']};
                border-right: 1px solid {VITREOS_COLORS['border_primary']};
            }}
        """)
        
        # Column sizing
        if header := self.proc_table.horizontalHeader():
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # NAME
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # PID
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # CPU%
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # RAM
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # TPI
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)    # ENTROPY
            header.resizeSection(1, 60)   # PID
            header.resizeSection(2, 60)   # CPU%
            header.resizeSection(3, 80)   # RAM
            header.resizeSection(4, 50)   # TPI
            header.resizeSection(5, 70)   # ENTROPY
        
        layout.addWidget(self.proc_table)
    
    def on_affinity_lock(self) -> None:
        """Lock selected process to physical cores only (0,2,4,6,8,10,12,14)"""
        selection_model = self.proc_table.selectionModel()
        if selection_model is None:
            return
        
        selected_rows = selection_model.selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row >= len(self.processes_data):
            return
        
        proc_data = self.processes_data[row]
        pid = proc_data['pid']
        name = proc_data['name']
        
        try:
            proc = psutil.Process(pid)
            # Ryzen 5700X: Physical cores are 0,2,4,6,8,10,12,14 (even indices)
            physical_cores = [0, 2, 4, 6, 8, 10, 12, 14]
            proc.cpu_affinity(physical_cores)
            
            # Emit cyan log
            self.log_message.emit("PROC", f"Affinity Lock applied to {name} (Physical Cores Only)", "cyan")
        except psutil.AccessDenied:
            self.log_message.emit("WARN", f"Access denied for {name} (PID {pid})", "warning_orange")
        except psutil.NoSuchProcess:
            self.log_message.emit("WARN", f"Process {name} no longer exists", "warning_orange")
        except Exception as e:
            self.log_message.emit("ERR", f"Affinity lock failed: {e}", "critical_red")
    
    def calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy H(X) = -Σ P(xi) * log2(P(xi))"""
        if not text:
            return 0.0
        
        # Count character frequencies
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate probabilities and entropy
        length = len(text)
        entropy = 0.0
        
        for count in freq.values():
            p = count / length
            if p > 0:
                entropy -= p * math.log2(p)
        
        return entropy
    
    def update_processes(self, processes: List[Dict[str, Any]]) -> None:
        """Update the tactical grid with process data"""
        self.processes_data = processes
        self.proc_table.setRowCount(len(processes))
        
        for row, proc in enumerate(processes):
            # NAME
            name = proc.get('name', 'Unknown')
            name_item = QTableWidgetItem(name)
            name_item.setFont(get_font('mono', 8))
            
            # PID
            pid = proc.get('pid', 0)
            pid_item = QTableWidgetItem(str(pid))
            pid_item.setFont(get_font('mono', 8))
            pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # CPU %
            cpu_pct = proc.get('cpu_percent', 0)
            cpu_item = QTableWidgetItem(f"{cpu_pct:.1f}")
            cpu_item.setFont(get_font('mono', 8))
            cpu_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Color code high CPU
            if cpu_pct > 50:
                cpu_item.setForeground(QColor(VITREOS_COLORS['critical_red']))
            elif cpu_pct > 25:
                cpu_item.setForeground(QColor(VITREOS_COLORS['warning_orange']))
            else:
                cpu_item.setForeground(QColor(VITREOS_COLORS['cyan']))
            
            # RAM (MB)
            ram_mb = proc.get('memory_mb', 0)
            ram_item = QTableWidgetItem(f"{ram_mb:.0f}")
            ram_item.setFont(get_font('mono', 8))
            ram_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # TPI (Thermal Pressure Index) - visual bar widget
            tpi = proc.get('tpi', 0)
            tpi_item = QTableWidgetItem("")  # Empty text, widget will be set
            tpi_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Create TPI bar widget
            tpi_bar = TPIBar()
            tpi_bar.set_value(tpi)
            
            # ENTROPY
            entropy = self.calculate_entropy(name)
            entropy_str = f"{entropy:.2f}"
            
            # Flag suspicious entropy (H > 4.0 - adjusted threshold)
            if entropy > 4.0:
                entropy_str = f"! {entropy_str}"
            
            entropy_item = QTableWidgetItem(entropy_str)
            entropy_item.setFont(get_font('mono', 8))
            entropy_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if entropy > 4.0:
                entropy_item.setForeground(QColor(VITREOS_COLORS['warning_orange']))
            else:
                entropy_item.setForeground(QColor(VITREOS_COLORS['text_dim']))
            
            # Set items
            self.proc_table.setItem(row, 0, name_item)
            self.proc_table.setItem(row, 1, pid_item)
            self.proc_table.setItem(row, 2, cpu_item)
            self.proc_table.setItem(row, 3, ram_item)
            self.proc_table.setItem(row, 4, tpi_item)
            self.proc_table.setItem(row, 5, entropy_item)
            
            # Set TPI bar widget in cell
            self.proc_table.setCellWidget(row, 4, tpi_bar)
            
            # Set row height
            self.proc_table.setRowHeight(row, 20)


