"""
Live Socket Monitor - Real-Time Network Connection Tracker
V4 Vanguard Edition with permission-safe psutil polling, PID caching, and zero-rebuild live filtering.
"""

from typing import List, Dict, Tuple, Any, Optional
import psutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QScrollArea, QFrame, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from src.ui.vitreos_theme import VITREOS_COLORS, get_font

THREAT_COLORS = {
    "High": VITREOS_COLORS.get("critical_red", "#EF4444"),
    "Medium": VITREOS_COLORS.get("warning_orange", "#F59E0B"),
    "Low": VITREOS_COLORS.get("green", "#22C55E")
}

THREAT_ORDER = {"High": 0, "Medium": 1, "Low": 2}

# Port Classification Heuristics
HIGH_RISK_PORTS = {4444, 1337, 6667, 9801, 31337, 5555}
MEDIUM_RISK_PORTS = {22, 23, 3389, 5900, 8080, 8443, 8000, 9090}


class LiveSocketMonitor(QWidget):
    """
    Live tactical external socket monitor.
    Monitors active remote connections, eliminating loopbacks, and provides dynamic filtering.
    """
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._proc_cache: Dict[int, str] = {}
        self._current_data: List[Dict[str, str]] = []
        self._row_items: List[Tuple[QWidget, Dict[str, str]]] = []
        
        self._setup_ui()
        
        # Initial poll
        self.poll_sockets()
        
        # Throttled 2500ms poll timer to avoid UI stutter
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_sockets)
        self.poll_timer.start(2500)

    def _get_process_name(self, pid: Optional[int]) -> str:
        """Resolve process name from PID with caching and permission safety."""
        if not pid or pid < 0:
            return "System"
        if pid in self._proc_cache:
            return self._proc_cache[pid]
            
        try:
            name = psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
            name = "System" if pid == 4 else f"PID:{pid}"
            
        self._proc_cache[pid] = name
        return name

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Header section: Summary and Search
        header_layout = QHBoxLayout()
        
        self.summary_label = QLabel("INITIALIZING SOCKET AUDIT...")
        self.summary_label.setFont(get_font("mono", 9))
        self.summary_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by name, IP, or port...")
        self.search_input.setFont(get_font("mono", 9))
        self.search_input.setFixedHeight(26)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {VITREOS_COLORS['bg_secondary']};
                color: {VITREOS_COLORS['text_primary']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
                padding: 2px 6px;
                border-radius: 2px;
            }}
            QLineEdit:focus {{
                border: 1px solid {VITREOS_COLORS['primary_purple']};
            }}
        """)
        # Zero-rebuild live filtering: toggles visibility only
        self.search_input.textChanged.connect(self._apply_filter)
        
        header_layout.addWidget(self.summary_label)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        
        layout.addLayout(header_layout)

        # Table Header
        table_header = QWidget()
        th_layout = QHBoxLayout(table_header)
        th_layout.setContentsMargins(6, 2, 6, 2)
        
        headers = ["PROCESS", "REMOTE DESTINATION", "PORT", "STATE", "THREAT"]
        stretches = [3, 3, 1, 1, 2]
        
        for h, stretch in zip(headers, stretches):
            lbl = QLabel(h)
            lbl.setFont(get_font("mono", 8))
            lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']}; font-weight: bold;")
            th_layout.addWidget(lbl, stretch)
            
        layout.addWidget(table_header)

        # Scroll Area for rows
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {VITREOS_COLORS['border_primary']};
                background: {VITREOS_COLORS['bg_secondary']};
            }}
        """)
        
        self.rows_widget = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_widget)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(2)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.rows_widget)
        layout.addWidget(self.scroll_area)

    def poll_sockets(self) -> None:
        """Poll real active external sockets using permission-safe psutil."""
        new_data: List[Dict[str, str]] = []
        
        try:
            connections = psutil.net_connections(kind='inet')
        except (PermissionError, psutil.Error, OSError):
            connections = []

        seen_targets = set()
        for conn in connections:
            # Must have a remote address (active external session)
            if not conn.raddr:
                continue
                
            ip = str(conn.raddr.ip)
            port = int(conn.raddr.port)
            
            # Filter loopbacks and invalid addresses
            if (ip.startswith("127.") or ip == "::1" or ip == "0.0.0.0" or ip == "::" or ip.startswith("fe80")):
                continue
                
            sig = f"{conn.pid}_{ip}_{port}"
            if sig in seen_targets:
                continue
            seen_targets.add(sig)
            
            proc_name = self._get_process_name(conn.pid)
            
            # Threat Level Classification
            if port in HIGH_RISK_PORTS:
                threat = "High"
            elif port in MEDIUM_RISK_PORTS or port > 49152:
                threat = "Medium"
            else:
                threat = "Low"
                
            status_text = conn.status if conn.status else "ESTABLISHED"
            
            new_data.append({
                "process": proc_name,
                "ip": ip,
                "port": str(port),
                "state": status_text,
                "threat": threat,
            })
            
            if len(new_data) >= 40:  # Cap at top 40 connections for UI responsiveness
                break
                
        # Sort by threat severity then process name
        new_data.sort(key=lambda x: (THREAT_ORDER.get(x["threat"], 2), x["process"].lower()))
        
        self._current_data = new_data
        self._rebuild_rows_if_needed()

    def _rebuild_rows_if_needed(self) -> None:
        """Synchronize row widgets with polled socket data."""
        # Clear old rows
        while self.rows_layout.count():
            child = self.rows_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()
                
        self._row_items.clear()
        
        counts = {"High": 0, "Medium": 0, "Low": 0}
        
        for item in self._current_data:
            counts[item["threat"]] += 1
            
            row = QWidget()
            row.setObjectName("SocketRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(6, 4, 6, 4)
            
            threat_color = THREAT_COLORS.get(item["threat"], "#22C55E")
            
            row.setStyleSheet(f"""
                QWidget#SocketRow {{
                    background: {VITREOS_COLORS['bg_card']};
                    border-left: 3px solid {threat_color};
                    border-bottom: 1px solid {VITREOS_COLORS['border_dim']};
                }}
            """)
            
            # Columns: Process, IP, Port, State, Threat
            proc_lbl = QLabel(item["process"])
            proc_lbl.setFont(get_font("mono", 8))
            proc_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']}; font-weight: bold;")
            row_layout.addWidget(proc_lbl, 3)
            
            ip_lbl = QLabel(item["ip"])
            ip_lbl.setFont(get_font("mono", 8))
            ip_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
            row_layout.addWidget(ip_lbl, 3)
            
            port_lbl = QLabel(item["port"])
            port_lbl.setFont(get_font("mono", 8))
            port_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            row_layout.addWidget(port_lbl, 1)
            
            state_lbl = QLabel(item["state"][:10])
            state_lbl.setFont(get_font("mono", 7))
            state_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            row_layout.addWidget(state_lbl, 1)
            
            threat_pill = QLabel(f"[{item['threat'].upper()}]")
            threat_pill.setFont(get_font("mono", 8))
            threat_pill.setStyleSheet(f"color: {threat_color}; font-weight: bold;")
            threat_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_layout.addWidget(threat_pill, 2)
            
            self.rows_layout.addWidget(row)
            self._row_items.append((row, item))
            
        self.summary_label.setText(
            f"HIGH: <font color='{THREAT_COLORS['High']}'>{counts['High']}</font> | "
            f"MED: <font color='{THREAT_COLORS['Medium']}'>{counts['Medium']}</font> | "
            f"LOW: <font color='{THREAT_COLORS['Low']}'>{counts['Low']}</font> | "
            f"ACTIVE: {len(self._current_data)}"
        )
        
        # Re-apply current search filter without rebuilding
        self._apply_filter(self.search_input.text())

    def _apply_filter(self, search_text: str) -> None:
        """
        Dynamically toggle row visibility without destroying or recreating C++ widgets.
        Zero stutter on keystrokes.
        """
        query = search_text.strip().lower()
        for row_widget, item in self._row_items:
            if not query:
                row_widget.setVisible(True)
            else:
                matches = (
                    query in item["process"].lower() or
                    query in item["ip"].lower() or
                    query in item["port"]
                )
                row_widget.setVisible(matches)

    def update_telemetry(self, packet: Any) -> None:
        """Optional telemetry packet hook."""
        pass
