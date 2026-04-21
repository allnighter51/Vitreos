from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QScrollArea, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from src.ui.vitreos_theme import VITREOS_COLORS, get_font

INITIAL_DATA = [
    {"process": "powershell.exe", "ip": "103.214.189.70", "port": "4444", "geo": "CN", "threat": "High"},
    {"process": "svchost.exe", "ip": "5.181.48.91", "port": "8080", "geo": "RU", "threat": "High"},
    {"process": "unknown.exe", "ip": "42.119.3.14", "port": "9801", "geo": "VN", "threat": "Medium"},
    {"process": "chrome.exe", "ip": "142.250.185.46", "port": "443", "geo": "US", "threat": "Low"},
    {"process": "discord.exe", "ip": "162.159.135.234", "port": "443", "geo": "US", "threat": "Low"},
    {"process": "steam.exe", "ip": "208.64.202.87", "port": "27036", "geo": "US", "threat": "Low"},
    {"process": "WudfHost.exe", "ip": "13.89.179.10", "port": "443", "geo": "US", "threat": "Low"},
    {"process": "chrome.exe", "ip": "104.18.24.47", "port": "443", "geo": "US", "threat": "Low"}
]

THREAT_COLORS = {
    "High": VITREOS_COLORS.get("critical_red", "#FF4444"),
    "Medium": VITREOS_COLORS.get("warning_orange", "#FF6B00"),
    "Low": VITREOS_COLORS.get("green", "#22C55E")
}

THREAT_ORDER = {"High": 0, "Medium": 1, "Low": 2}

class LiveSocketMonitor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = [dict(item) for item in INITIAL_DATA]
        self._setup_ui()
        self._update_view()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header section: Summary and Search
        header_layout = QHBoxLayout()
        
        self.summary_label = QLabel()
        self.summary_label.setFont(get_font("mono", 10))
        self.summary_label.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by name or IP...")
        self.search_input.setFont(get_font("mono", 9))
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {VITREOS_COLORS['bg_secondary']};
                color: {VITREOS_COLORS['text_primary']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
                padding: 4px;
            }}
            QLineEdit:focus {{
                border: 1px solid {VITREOS_COLORS['primary_purple']};
            }}
        """)
        self.search_input.textChanged.connect(self._update_view)
        
        header_layout.addWidget(self.summary_label)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        
        layout.addLayout(header_layout)

        # Table Header
        table_header = QWidget()
        th_layout = QHBoxLayout(table_header)
        th_layout.setContentsMargins(4, 4, 4, 4)
        
        headers = ["Process Name", "Destination IP", "Port", "Geo Location", "Threat Level"]
        stretches = [2, 2, 1, 1, 1]
        
        for h, stretch in zip(headers, stretches):
            lbl = QLabel(h)
            lbl.setFont(get_font("mono", 9))
            lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_sub']}; font-weight: bold;")
            th_layout.addWidget(lbl, stretch)
            
        layout.addWidget(table_header)

        # Scroll Area for rows
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {VITREOS_COLORS['border_secondary']};
                background: transparent;
            }}
        """)
        
        self.rows_widget = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_widget)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(2)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.rows_widget)
        layout.addWidget(self.scroll_area)

    def _clear_rows(self):
        while self.rows_layout.count():
            child = self.rows_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _update_view(self):
        self._clear_rows()
        
        search_term = self.search_input.text().lower()
        
        # Sort data
        self.data.sort(key=lambda x: (THREAT_ORDER[x["threat"]], x["process"]))
        
        counts = {"High": 0, "Medium": 0, "Low": 0}
        
        for item in self.data:
            counts[item["threat"]] += 1
            
            # Filter
            if search_term and (search_term not in item["process"].lower() and search_term not in item["ip"].lower()):
                continue
                
            row = QWidget()
            row.setObjectName("SocketRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 4, 4, 4)
            
            bg_color = VITREOS_COLORS['bg_card']
            threat_color = THREAT_COLORS[item["threat"]]
            
            row.setStyleSheet(f"""
                QWidget#SocketRow {{
                    background: {bg_color};
                    border-left: 3px solid {threat_color};
                    border-bottom: 1px solid {VITREOS_COLORS['border_secondary']};
                }}
            """)
            
            stretches = [2, 2, 1, 1]
            fields = ["process", "ip", "port", "geo"]
            
            for field, stretch in zip(fields, stretches):
                lbl = QLabel(item[field])
                lbl.setFont(get_font("mono", 9))
                if field == "process":
                    lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']}; font-weight: bold; background: transparent; border: none;")
                else:
                    lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']}; background: transparent; border: none;")
                row_layout.addWidget(lbl, stretch)
                
            # Threat Level ComboBox
            combo = QComboBox()
            combo.addItems(["High", "Medium", "Low"])
            combo.setCurrentText(item["threat"])
            combo.setFont(get_font("mono", 9))
            combo.setStyleSheet(f"""
                QComboBox {{
                    background: {VITREOS_COLORS['bg_secondary']};
                    color: {threat_color};
                    border: 1px solid {VITREOS_COLORS['border_secondary']};
                    padding: 2px;
                }}
                QComboBox::drop-down {{ border: none; }}
                QComboBox QAbstractItemView {{
                    background: {VITREOS_COLORS['bg_secondary']};
                    color: {VITREOS_COLORS['text_primary']};
                    selection-background-color: {VITREOS_COLORS['primary_purple']};
                }}
            """)
            # Need to capture the current item for the lambda
            combo.currentTextChanged.connect(lambda text, itm=item: self._on_threat_changed(itm, text))
            row_layout.addWidget(combo, 1)
            
            self.rows_layout.addWidget(row)
            
        self.summary_label.setText(
            f"High: <font color='{THREAT_COLORS['High']}'>{counts['High']}</font> | "
            f"Medium: <font color='{THREAT_COLORS['Medium']}'>{counts['Medium']}</font> | "
            f"Low: <font color='{THREAT_COLORS['Low']}'>{counts['Low']}</font>"
        )

    def _on_threat_changed(self, item: Dict, new_threat: str):
        if item["threat"] != new_threat:
            item["threat"] = new_threat
            self._update_view()
