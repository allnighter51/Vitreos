#!/usr/bin/env python3
"""
Vitreos Network Tab - Tactical Network Monitoring
Phase 1: 3-Frame Mission Control Layout
"""
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QScrollArea, QSizePolicy, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QPaintEvent
import psutil
from src.ui.vitreos_widgets import VitreosWinFrame, clear_layout
from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font


class NetworkTab(QWidget):
    """Network monitoring with 3-frame tactical layout"""
    
    adapter_changed = pyqtSignal(str)  # Signal to notify telemetry worker
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Bandwidth history for waveform
        self.download_history: List[float] = [0.0] * 60
        self.upload_history: List[float] = [0.0] * 60
        self.peak_download = 0.0
        self.peak_upload = 0.0
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Build 3-frame tactical layout"""
        layout = QGridLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Frame 1: Adapter Control (Top Left)
        self.adapter_frame = self._create_adapter_frame()
        layout.addWidget(self.adapter_frame, 0, 0, 1, 1)
        
        # Frame 2: Bandwidth Engine (Top Right)
        self.bandwidth_frame = self._create_bandwidth_frame()
        layout.addWidget(self.bandwidth_frame, 0, 1, 1, 1)
        
        # Frame 3: Network Hogs (Bottom, Full Width)
        self.hogs_frame = self._create_hogs_frame()
        layout.addWidget(self.hogs_frame, 1, 0, 1, 2)
        
        # Set column/row stretching
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)
        
        self.setStyleSheet(f"NetworkTab {{ background: {VITREOS_COLORS['bg_primary']}; }}")
    
    def _create_adapter_frame(self) -> VitreosWinFrame:
        """Frame 1: Adapter Control with live status"""
        frame = VitreosWinFrame(title="ADAPTER_CONTROL", accent_color="cyan")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Adapter dropdown
        adapter_label = QLabel("ACTIVE INTERFACE:")
        adapter_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        adapter_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        layout.addWidget(adapter_label)
        
        self.adapter_combo = QComboBox()
        self.adapter_combo.setFont(get_font('mono', 8))
        self.adapter_combo.setStyleSheet(f"""
            QComboBox {{
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
                padding: 6px;
                color: {VITREOS_COLORS['cyan']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {VITREOS_COLORS['cyan']};
            }}
        """)
        self.adapter_combo.currentTextChanged.connect(self._on_adapter_changed)
        layout.addWidget(self.adapter_combo)
        
        # Populate adapters
        self._populate_adapters()
        
        # Live status labels
        self.ip_label = QLabel("IP: --")
        self.ip_label.setFont(get_font('mono', 8))
        self.ip_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.ip_label)
        
        self.mac_label = QLabel("MAC: --")
        self.mac_label.setFont(get_font('mono', 8))
        self.mac_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.mac_label)
        
        self.type_label = QLabel("TYPE: --")
        self.type_label.setFont(get_font('mono', 8))
        self.type_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.type_label)
        
        layout.addStretch()
        
        frame.content_widget.setLayout(layout)
        return frame
    
    def _create_bandwidth_frame(self) -> VitreosWinFrame:
        """Frame 2: Bandwidth Engine with waveform and digital readouts"""
        frame = VitreosWinFrame(title="BANDWIDTH_ENGINE", accent_color="primary_purple")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Waveform graph
        self.waveform_widget = BandwidthWaveform()
        self.waveform_widget.setMinimumHeight(120)
        layout.addWidget(self.waveform_widget)
        
        # Digital readouts
        readouts_layout = QGridLayout()
        readouts_layout.setSpacing(8)
        
        # Download
        dl_label = QLabel("DOWNLOAD")
        dl_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        dl_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        readouts_layout.addWidget(dl_label, 0, 0)
        
        self.download_value = QLabel("0.00 Mbps")
        self.download_value.setFont(get_font('mono', 11))
        self.download_value.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        readouts_layout.addWidget(self.download_value, 1, 0)
        
        # Upload
        ul_label = QLabel("UPLOAD")
        ul_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        ul_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        readouts_layout.addWidget(ul_label, 0, 1)
        
        self.upload_value = QLabel("0.00 Mbps")
        self.upload_value.setFont(get_font('mono', 11))
        self.upload_value.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        readouts_layout.addWidget(self.upload_value, 1, 1)
        
        # Peak tracking
        peak_label = QLabel("SESSION PEAK")
        peak_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        peak_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        readouts_layout.addWidget(peak_label, 2, 0, 1, 2)
        
        self.peak_value = QLabel("DL: 0.00 | UL: 0.00 Mbps")
        self.peak_value.setFont(get_font('mono', 9))
        self.peak_value.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        readouts_layout.addWidget(self.peak_value, 3, 0, 1, 2)
        
        layout.addLayout(readouts_layout)
        
        frame.content_widget.setLayout(layout)
        return frame
    
    def _create_hogs_frame(self) -> VitreosWinFrame:
        """Frame 3: Network Hogs (Top 5 processes)"""
        frame = VitreosWinFrame(title="NETWORK_HOGS", accent_color="warning_orange", badge="TOP 5")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        
        # Scrollable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {VITREOS_COLORS['bg_primary']};
                border: none;
            }}
        """)
        
        self.hogs_container = QWidget()
        self.hogs_layout = QVBoxLayout(self.hogs_container)
        self.hogs_layout.setSpacing(4)
        self.hogs_layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder entries
        for i in range(5):
            hog_widget = self._create_hog_entry(f"Process {i+1}", 0, 0.0, 0.0)
            self.hogs_layout.addWidget(hog_widget)
        
        self.hogs_layout.addStretch()
        scroll.setWidget(self.hogs_container)
        layout.addWidget(scroll)
        
        frame.content_widget.setLayout(layout)
        return frame
    
    def _create_hog_entry(self, name: str, pid: int, download: float, upload: float) -> QWidget:
        """Create a single network hog entry"""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
                padding: 6px;
            }}
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)
        
        # Process name
        name_label = QLabel(name)
        name_label.setFont(get_font('mono', 9))
        name_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        name_label.setMinimumWidth(200)
        layout.addWidget(name_label)
        
        # PID
        pid_label = QLabel(f"PID:{pid}")
        pid_label.setFont(get_font('mono', 8))
        pid_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        pid_label.setFixedWidth(80)
        layout.addWidget(pid_label)
        
        layout.addStretch()
        
        # Download
        dl_label = QLabel(f"↓ {download:.2f} Mbps")
        dl_label.setFont(get_font('mono', 9))
        dl_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        dl_label.setFixedWidth(120)
        layout.addWidget(dl_label)
        
        # Upload
        ul_label = QLabel(f"↑ {upload:.2f} Mbps")
        ul_label.setFont(get_font('mono', 9))
        ul_label.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        ul_label.setFixedWidth(120)
        layout.addWidget(ul_label)
        
        return widget
    
    def _populate_adapters(self) -> None:
        """Populate adapter dropdown with system interfaces"""
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            for interface, addr_list in addrs.items():
                if interface in stats and stats[interface].isup:
                    self.adapter_combo.addItem(interface)
            
            # Set default to first active adapter
            if self.adapter_combo.count() > 0:
                self.adapter_combo.setCurrentIndex(0)
        except Exception as e:
            print(f"[NETWORK] Error populating adapters: {e}")
            self.adapter_combo.addItem("No Adapters Found")
    
    def _on_adapter_changed(self, adapter_name: str) -> None:
        """Handle adapter selection change"""
        print(f"[NETWORK] Adapter changed to: {adapter_name}")
        self.adapter_changed.emit(adapter_name)
        self._update_adapter_info(adapter_name)
    
    def _update_adapter_info(self, adapter_name: str) -> None:
        """Update adapter info labels"""
        try:
            addrs = psutil.net_if_addrs()
            if adapter_name in addrs:
                for addr in addrs[adapter_name]:
                    if addr.family == 2:  # AF_INET (IPv4)
                        self.ip_label.setText(f"IP: {addr.address}")
                    elif addr.family == 17:  # AF_LINK (MAC)
                        self.mac_label.setText(f"MAC: {addr.address}")
                
                # Determine type (Ethernet/WiFi)
                if 'eth' in adapter_name.lower() or 'ethernet' in adapter_name.lower():
                    self.type_label.setText("TYPE: ETHERNET")
                elif 'wi-fi' in adapter_name.lower() or 'wlan' in adapter_name.lower():
                    self.type_label.setText("TYPE: WiFi")
                else:
                    self.type_label.setText("TYPE: UNKNOWN")
        except Exception as e:
            print(f"[NETWORK] Error updating adapter info: {e}")
    
    def update_ping_stats(self, stats: Dict[str, Any]) -> None:
        """Update bandwidth stats and waveform"""
        download = stats.get('downloadMbps', 0)
        upload = stats.get('uploadMbps', 0)
        
        # Update digital readouts
        self.download_value.setText(f"{download:.2f} Mbps")
        self.upload_value.setText(f"{upload:.2f} Mbps")
        
        # Update peak tracking
        if download > self.peak_download:
            self.peak_download = download
        if upload > self.peak_upload:
            self.peak_upload = upload
        
        self.peak_value.setText(f"DL: {self.peak_download:.2f} | UL: {self.peak_upload:.2f} Mbps")
        
        # Update waveform history
        self.download_history.append(download)
        self.upload_history.append(upload)
        if len(self.download_history) > 60:
            self.download_history.pop(0)
            self.upload_history.pop(0)
        
        self.waveform_widget.set_data(self.download_history, self.upload_history)
        
        # Update network hogs if present
        if 'networkHogs' in stats and stats['networkHogs']:
            self.update_bandwidth_hogs(stats['networkHogs'])
    
    def set_primary_adapter(self, adapter_name: str) -> None:
        """Set the primary adapter as default selection."""
        index = self.adapter_combo.findText(adapter_name)
        if index >= 0:
            self.adapter_combo.setCurrentIndex(index)
    
    def update_bandwidth_hogs(self, hogs: List[Dict[str, Any]]) -> None:
        """Update network hogs list (top 5)"""
        # Safely clear existing entries
        clear_layout(self.hogs_layout)

        # Add new entries (limit to 5)
        for hog in hogs[:5]:
            name = hog.get('name', 'Unknown')
            pid = hog.get('pid', 0)
            download = hog.get('download_mbps', 0.0)
            upload = hog.get('upload_mbps', 0.0)
            
            hog_widget = self._create_hog_entry(name, pid, download, upload)
            self.hogs_layout.addWidget(hog_widget)
        
        self.hogs_layout.addStretch()


class BandwidthWaveform(QWidget):
    """High-density waveform graph for bandwidth visualization"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.download_data: List[float] = [0.0] * 60
        self.upload_data: List[float] = [0.0] * 60
        self.setMinimumHeight(100)
    
    def set_data(self, download: List[float], upload: List[float]) -> None:
        """Update waveform data"""
        self.download_data = download[-60:]  # Last 60 samples
        self.upload_data = upload[-60:]
        self.update()
    
    def paintEvent(self, a0: QPaintEvent) -> None:
        """Draw waveform graph"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background
        painter.fillRect(0, 0, width, height, QColor(VITREOS_COLORS['bg_card']))
        
        # Grid lines
        painter.setPen(QPen(QColor(VITREOS_COLORS['border_secondary']), 1))
        for i in range(0, height, 20):
            painter.drawLine(0, i, width, i)
        
        # Find max value for scaling
        max_val = max(max(self.download_data + self.upload_data, default=1), 1)
        
        # Draw download waveform (cyan)
        painter.setPen(QPen(QColor(VITREOS_COLORS['cyan']), 2))
        for i in range(1, len(self.download_data)):
            x1 = int((i - 1) * width / 60)
            y1 = int(height - (self.download_data[i - 1] / max_val * height))
            x2 = int(i * width / 60)
            y2 = int(height - (self.download_data[i] / max_val * height))
            painter.drawLine(x1, y1, x2, y2)
        
        # Draw upload waveform (orange)
        painter.setPen(QPen(QColor(VITREOS_COLORS['warning_orange']), 2))
        for i in range(1, len(self.upload_data)):
            x1 = int((i - 1) * width / 60)
            y1 = int(height - (self.upload_data[i - 1] / max_val * height))
            x2 = int(i * width / 60)
            y2 = int(height - (self.upload_data[i] / max_val * height))
            painter.drawLine(x1, y1, x2, y2)


