"""
Vitreos Sentinel - Dialogs Module
Cyberdeck-styled confirmation dialogs for system operations
"""

from typing import Optional, List, Dict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QCheckBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QWidget
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent


class PurgeConfirmationDialog(QDialog):
    """Cyberdeck-styled confirmation for system cleanup"""
    
    def __init__(self, targets: List[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 300)
        self.selected_targets: List[str] = []
        self._drag_pos = QPoint()
        
        layout = QVBoxLayout(self)
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: #0d0d0f;
                border: 2px solid #bc13fe;
                border-radius: 10px;
            }
        """)
        frame_layout = QVBoxLayout(self.frame)
        
        title = QLabel("🧹 PURGE PROTOCOL")
        title.setStyleSheet("color: #bc13fe; font-weight: bold; font-size: 18px; border: none;")
        frame_layout.addWidget(title)
        
        self.checks: Dict[str, QCheckBox] = {}
        for target in targets:
            cb = QCheckBox(f"Clear {target}")
            cb.setChecked(True)
            cb.setStyleSheet("color: white; border: none; font-family: 'Consolas';")
            self.checks[target] = cb
            frame_layout.addWidget(cb)
            
        btn_layout = QHBoxLayout()
        confirm = QPushButton("EXECUTE")
        confirm.setStyleSheet("background: #bc13fe; color: black; font-weight: bold; border-radius: 5px; height: 30px;")
        confirm.clicked.connect(self.accept_purge)  # type: ignore
        
        cancel = QPushButton("ABORT")
        cancel.setStyleSheet("background: #333; color: white; border-radius: 5px; height: 30px;")
        cancel.clicked.connect(self.reject)  # type: ignore
        
        btn_layout.addWidget(cancel)
        btn_layout.addWidget(confirm)
        frame_layout.addLayout(btn_layout)
        layout.addWidget(self.frame)

    def accept_purge(self) -> None:
        """Accept dialog and store selected targets"""
        self.selected_targets = [t for t, cb in self.checks.items() if cb.isChecked()]
        self.accept()

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        """Handle mouse press for window dragging"""
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        """Handle mouse move for window dragging"""
        if a0 and a0.buttons() == Qt.MouseButton.LeftButton:
            self.move(a0.globalPosition().toPoint() - self._drag_pos)


class TuningConfirmationDialog(QDialog):
    """eSports Optimization Confirmation Dialog"""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 400)
        self._drag_pos = QPoint()
        
        layout = QVBoxLayout(self)
        self.frame = QFrame()
        self.frame.setStyleSheet("background-color: #0d0d0f; border: 2px solid #00f2ff; border-radius: 10px;")
        frame_layout = QVBoxLayout(self.frame)
        
        title = QLabel("⚡ ESPORTS TUNING ENGINE")
        title.setStyleSheet("color: #00f2ff; font-weight: bold; font-size: 18px; border: none;")
        frame_layout.addWidget(title)
        
        desc = QLabel("Recommended optimizations based on current load:")
        desc.setStyleSheet("color: #888; border: none;")
        frame_layout.addWidget(desc)
        
        self.table = QTableWidget(5, 2)
        self.table.setHorizontalHeaderLabels(["Optimization", "Benefit"])  # type: ignore
        
        # Safe header access
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.table.setStyleSheet("color: white; border: 1px solid #333; gridline-color: #333;")
        
        # Fill with optimization data
        opts = [
            ("CPU Priority", "High"),
            ("Memory Purge", "240MB"),
            ("GPU Power", "Max"),
            ("DPC Latency", "Low"),
            ("Network", "Stable")
        ]
        for i, (opt, ben) in enumerate(opts):
            self.table.setItem(i, 0, QTableWidgetItem(opt))
            self.table.setItem(i, 1, QTableWidgetItem(ben))
        
        frame_layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        confirm = QPushButton("APPLY TWEAKS")
        confirm.setStyleSheet("background: #00f2ff; color: black; font-weight: bold; border-radius: 5px; height: 35px;")
        confirm.clicked.connect(self.accept)  # type: ignore
        
        cancel = QPushButton("CANCEL")
        cancel.setStyleSheet("background: #333; color: white; border-radius: 5px; height: 35px;")
        cancel.clicked.connect(self.reject)  # type: ignore
        
        btn_layout.addWidget(cancel)
        btn_layout.addWidget(confirm)
        frame_layout.addLayout(btn_layout)
        layout.addWidget(self.frame)

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        """Handle mouse press for window dragging"""
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        """Handle mouse move for window dragging"""
        if a0 and a0.buttons() == Qt.MouseButton.LeftButton:
            self.move(a0.globalPosition().toPoint() - self._drag_pos)
