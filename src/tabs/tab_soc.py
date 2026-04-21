from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore import Qt
from src.ui.geo_threat_map import GeoThreatMap
from src.ui.vitreos_widgets import VitreosWinFrame
from src.ui.modules.live_socket_monitor import LiveSocketMonitor


class SOCTab(QWidget):
    """Security Operations Center Tab containing the GeoThreatMap and other modules."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        
    def _create_placeholder(self, title: str) -> VitreosWinFrame:
        frame = VitreosWinFrame(
            title=title,
            accent_color="cyan",
            badge="OFFLINE",
            badge_color="text_dim"
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        lbl = QLabel(f"{title} module offline.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #7d8b99; font-family: 'Inter'; font-size: 11px;")
        layout.addWidget(lbl)
        frame.set_content_layout(layout)
        return frame

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        grid = QGridLayout()
        grid.setSpacing(12)
        
        # Column 1
        # 1. GEO_THREAT_MAP
        map_panel = VitreosWinFrame(
            title="GEO_THREAT_MAP",
            accent_color="warning_orange",
            badge="SOC_ACTIVE",
            badge_color="warning_orange"
        )
        map_layout = QVBoxLayout()
        map_layout.setContentsMargins(12, 12, 12, 12)
        self.geo_map = GeoThreatMap()
        map_layout.addWidget(self.geo_map)
        map_panel.set_content_layout(map_layout)
        grid.addWidget(map_panel, 0, 0)
        
        # 2. LIVE_SOCKET_MONITOR
        socket_panel = VitreosWinFrame(
            title="LIVE_SOCKET_MONITOR",
            accent_color="primary_purple",
            badge="ACTIVE",
            badge_color="primary_purple"
        )
        socket_layout = QVBoxLayout()
        socket_layout.setContentsMargins(12, 12, 12, 12)
        self.socket_monitor = LiveSocketMonitor()
        socket_layout.addWidget(self.socket_monitor)
        socket_panel.set_content_layout(socket_layout)
        grid.addWidget(socket_panel, 1, 0)
        
        # 3. VM_NETWORK_ISOLATION
        grid.addWidget(self._create_placeholder("VM_NETWORK_ISOLATION"), 2, 0)
        
        # Column 2
        # 1. CORE_INTEGRITY_MONITOR
        grid.addWidget(self._create_placeholder("CORE_INTEGRITY_MONITOR"), 0, 1)
        
        # 2. BOOT_PERSISTENCE_AUDIT
        grid.addWidget(self._create_placeholder("BOOT_PERSISTENCE_AUDIT"), 1, 1)
        
        # 3. BREACH_WATCH_HIBP
        grid.addWidget(self._create_placeholder("BREACH_WATCH_HIBP"), 2, 1)
        
        # Column 3
        # 1. PANIC_HUB // EMERGENCY_ACTIONS
        grid.addWidget(self._create_placeholder("EMERGENCY_ACTIONS"), 0, 2)
        
        # 2. METADATA/EXIF_SCRUBBER
        grid.addWidget(self._create_placeholder("METADATA_EXIF_SCRUBBER"), 1, 2)
        
        # 3. CRITICAL_FILE_WATCH
        grid.addWidget(self._create_placeholder("CRITICAL_FILE_WATCH"), 2, 2)
        
        # Make rows and columns stretch equally
        for i in range(3):
            grid.setRowStretch(i, 1)
            grid.setColumnStretch(i, 1)
            
        layout.addLayout(grid)

__all__ = ['SOCTab']
