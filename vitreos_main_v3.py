"""
Vitreos V3 - Pure Python PyQt6 Architecture
Main Application Window with Figma-Accurate Layout
"""

import sys
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QGridLayout, QVBoxLayout
)
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QMouseEvent

from vitreos_theme import VITREOS_COLORS, VITREOS_STYLESHEET, initialize_theme
from vitreos_widgets import SystemPulseLog, VitreosWinFrame
from vitreos_telemetry import TelemetryWorker
from vitreos_modules import (
    CpuMonitor, GpuMonitor, ThermalCtrl, StorageArray, MemoryArray, NetInterface
)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN WINDOW - Frameless with Liquid Glass Effect
# ═══════════════════════════════════════════════════════════════════════════

class VitreosMainWindow(QMainWindow):
    """
    Main application window with frameless design and custom layout.
    Matches Figma specifications with 232px sidebar + 2x3 grid dashboard.
    """
    
    def __init__(self):
        super().__init__()
        
        # Window properties
        self.setWindowTitle("VITREOS // SYSTEM SENTINEL v2.1")
        self.setGeometry(100, 100, 1400, 900)
        
        # Frameless window with transparency
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Drag support
        self.drag_position: Optional[QPoint] = None
        
        # Telemetry worker
        self.telemetry_worker: Optional[TelemetryWorker] = None
        
        # Initialize UI
        self._setup_ui()
        self._apply_styling()
        self._start_telemetry()
        
        print("[VITREOS] Main window initialized")
    
    def _setup_ui(self) -> None:
        """Build the main window layout."""
        # Central widget with Liquid Glass background
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        
        # Main horizontal layout: Sidebar + Dashboard
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left: SystemPulseLog (232px fixed width)
        self.sidebar = SystemPulseLog()
        main_layout.addWidget(self.sidebar)
        
        # Right: Dashboard grid
        dashboard_widget = QWidget()
        dashboard_widget.setObjectName("DashboardWidget")
        dashboard_layout = self._create_dashboard_grid()
        dashboard_widget.setLayout(dashboard_layout)
        main_layout.addWidget(dashboard_widget, 1)
    
    def _create_dashboard_grid(self) -> QGridLayout:
        """
        Create 2x3 grid layout for monitoring modules.
        
        Layout:
        Row 1: [StorageArray] [CpuMonitor] [ThermalCtrl]
        Row 2: [MemoryArray]  [GpuMonitor] [NetInterface]
        """
        grid = QGridLayout()
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(8)
        
        # Row 1
        self.storage_module = StorageArray()
        grid.addWidget(self.storage_module, 0, 0)
        
        self.cpu_module = CpuMonitor()
        grid.addWidget(self.cpu_module, 0, 1)
        
        self.thermal_module = ThermalCtrl()
        grid.addWidget(self.thermal_module, 0, 2)
        
        # Row 2
        self.memory_module = MemoryArray()
        grid.addWidget(self.memory_module, 1, 0)
        
        self.gpu_module = GpuMonitor()
        grid.addWidget(self.gpu_module, 1, 1)
        
        self.network_module = NetInterface()
        grid.addWidget(self.network_module, 1, 2)
        
        # Column stretch: 1fr 1.1fr 1fr (middle column slightly wider)
        grid.setColumnStretch(0, 10)
        grid.setColumnStretch(1, 11)
        grid.setColumnStretch(2, 10)
        
        # Row stretch: equal
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        
        return grid
    
    def _apply_styling(self) -> None:
        """Apply Liquid Glass styling to main window."""
        self.setStyleSheet(f"""
            #CentralWidget {{
                background: rgba(13, 13, 13, 0.85);
                border: 2px solid {VITREOS_COLORS['border_primary']};
                border-radius: 0px;
            }}
            #DashboardWidget {{
                background: transparent;
            }}
        """)
    
    def _start_telemetry(self) -> None:
        """Initialize and start the telemetry worker thread."""
        self.telemetry_worker = TelemetryWorker()
        
        # Connect signals
        self.telemetry_worker.data_ready.connect(self._update_modules)
        self.telemetry_worker.log_message.connect(self._handle_log)
        
        # Start worker
        self.telemetry_worker.start()
        
        print("[VITREOS] Telemetry worker started")
    
    def _update_modules(self, data: Dict[str, Any]) -> None:
        """
        Update all monitoring modules with fresh telemetry data.
        
        Args:
            data: Hardware telemetry dictionary from TelemetryWorker
        """
        try:
            # CPU Module
            if 'cpu' in data:
                self.cpu_module.update_data(data['cpu'])
            
            # GPU Module (RTX 4090)
            if 'gpu' in data:
                self.gpu_module.update_data(data['gpu'])
            
            # Thermal Module
            if 'thermal' in data:
                self.thermal_module.update_data(data['thermal'])
            
            # Storage Module
            if 'storage' in data:
                self.storage_module.update_data(data['storage'])
            
            # Memory Module
            if 'memory' in data:
                self.memory_module.update_data(data['memory'])
            
            # Network Module
            if 'network' in data:
                self.network_module.update_data(data['network'])
        
        except Exception as e:
            print(f"[VITREOS] Error updating modules: {e}")
    
    def _handle_log(self, level: str, message: str, color: str) -> None:
        """
        Handle log messages from telemetry worker.
        
        Args:
            level: Log level (OK, WARN, CPU, GPU, etc.)
            message: Log message
            color: Color name from VITREOS_COLORS
        """
        self.sidebar.append_log(level, message, color)
    
    # ───────────────────────────────────────────────────────────────────────
    # FRAMELESS WINDOW DRAG SUPPORT
    # ───────────────────────────────────────────────────────────────────────
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Enable window dragging on mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle window dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Reset drag position on mouse release."""
        self.drag_position = None
    
    # ───────────────────────────────────────────────────────────────────────
    # CLEANUP
    # ───────────────────────────────────────────────────────────────────────
    
    def closeEvent(self, event) -> None:
        """Clean shutdown of telemetry worker."""
        print("[VITREOS] Shutting down...")
        
        if self.telemetry_worker:
            self.telemetry_worker.stop()
            self.telemetry_worker.wait(2000)  # Wait up to 2 seconds
        
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════
# APPLICATION ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Launch the Vitreos application."""
    app = QApplication(sys.argv)
    
    # Initialize theme system
    initialize_theme()
    
    # Apply global stylesheet
    app.setStyleSheet(VITREOS_STYLESHEET)
    
    # Create and show main window
    window = VitreosMainWindow()
    window.show()
    
    print("[VITREOS] Application started")
    print("[VITREOS] Press Ctrl+C in terminal to exit")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
