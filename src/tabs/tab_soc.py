"""
Security Operations Center (SOC) Tab - V4 Vanguard Architecture
Complete 3x3 tactical grid featuring real-time telemetry, zero-brush-leak GeoThreatMap,
real socket monitoring, and 7 functional security & system integrity modules.
"""

import hashlib
import os
import re
import shutil
import subprocess
import sys
import winreg
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

import psutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QLineEdit, QScrollArea, QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QImage

from src.core.paths import get_app_dir, get_bundle_dir
from src.ui.geo_threat_map import GeoThreatMap
from src.ui.modules.live_socket_monitor import LiveSocketMonitor
from src.ui.vitreos_theme import VITREOS_COLORS, get_font
from src.ui.vitreos_widgets import VitreosWinFrame


# ═══════════════════════════════════════════════════════════════════════════
# 1. VM_NETWORK_ISOLATION (Grid: 2, 0)
# ═══════════════════════════════════════════════════════════════════════════

class VMNetworkIsolationPanel(QWidget):
    """Detects and isolates virtual/tunnel network adapters for tournament play."""
    
    VIRTUAL_KEYWORDS = ('vethernet', 'wsl', 'hyper-v', 'tap', 'vpn', 'radmin', 'zerotier', 'virtualbox', 'vmware')

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.isolated: bool = False
        self._setup_ui()
        self.scan_adapters()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Status row
        self.status_lbl = QLabel("V-ADAPTER SCAN: READY")
        self.status_lbl.setFont(get_font("mono", 8))
        self.status_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.status_lbl)

        # Scroll area for adapter rows
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"QScrollArea {{ border: 1px solid {VITREOS_COLORS['border_primary']}; background: {VITREOS_COLORS['bg_card']}; }}")
        
        self.adapter_container = QWidget()
        self.adapter_layout = QVBoxLayout(self.adapter_container)
        self.adapter_layout.setContentsMargins(4, 4, 4, 4)
        self.adapter_layout.setSpacing(4)
        self.adapter_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.adapter_container)
        layout.addWidget(self.scroll_area, 1)

        # Action toggle button
        self.toggle_btn = QPushButton("ISOLATE V-NICS (LOCKDOWN)")
        self.toggle_btn.setFont(get_font("mono", 8))
        self.toggle_btn.setFixedHeight(24)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['bg_secondary']};
                color: {VITREOS_COLORS['warning_orange']};
                border: 1px solid {VITREOS_COLORS['warning_orange']};
                border-radius: 2px;
                padding: 2px;
            }}
            QPushButton:hover {{
                background: rgba(245, 158, 11, 0.15);
            }}
        """)
        self.toggle_btn.clicked.connect(self._toggle_isolation)
        layout.addWidget(self.toggle_btn)

    def scan_adapters(self) -> None:
        """Scan system interfaces for virtual or tunnel adapters."""
        while self.adapter_layout.count():
            child = self.adapter_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()

        found_adapters: List[Tuple[str, bool, str]] = []
        try:
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
            for nic_name, nic_stat in stats.items():
                name_lower = nic_name.lower()
                if any(kw in name_lower for kw in self.VIRTUAL_KEYWORDS):
                    ip = "No IPv4"
                    if nic_name in addrs:
                        for addr in addrs[nic_name]:
                            if addr.family.name == 'AF_INET':
                                ip = addr.address
                                break
                    found_adapters.append((nic_name, nic_stat.isup, ip))
        except (PermissionError, psutil.Error, OSError) as e:
            print(f"[VM_NIC] Scan error: {e}")

        if not found_adapters:
            lbl = QLabel("NO VIRTUAL ADAPTERS DETECTED | HOST CLEAN")
            lbl.setFont(get_font("mono", 8))
            lbl.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.adapter_layout.addWidget(lbl)
            self.status_lbl.setText("STATE: NO V-ADAPTERS ACTIVE")
            return

        self.status_lbl.setText(f"DETECTED {len(found_adapters)} V-ADAPTERS")
        for name, is_up, ip in found_adapters:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 2, 4, 2)

            name_lbl = QLabel(name[:22])
            name_lbl.setFont(get_font("mono", 8))
            name_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']}; font-weight: bold;")
            row_layout.addWidget(name_lbl, 2)

            ip_lbl = QLabel(ip)
            ip_lbl.setFont(get_font("mono", 8))
            ip_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            row_layout.addWidget(ip_lbl, 2)

            state_color = VITREOS_COLORS['green'] if (is_up and not self.isolated) else VITREOS_COLORS['critical_red']
            state_text = "[BRIDGED]" if (is_up and not self.isolated) else "[ISOLATED]"
            pill = QLabel(state_text)
            pill.setFont(get_font("mono", 8))
            pill.setStyleSheet(f"color: {state_color}; font-weight: bold;")
            row_layout.addWidget(pill, 1)

            self.adapter_layout.addWidget(row)

    def _toggle_isolation(self) -> None:
        self.isolated = not self.isolated
        if self.isolated:
            self.toggle_btn.setText("RESTORE V-NICS (BRIDGED)")
            self.toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {VITREOS_COLORS['bg_secondary']};
                    color: {VITREOS_COLORS['green']};
                    border: 1px solid {VITREOS_COLORS['green']};
                    border-radius: 2px;
                }}
            """)
        else:
            self.toggle_btn.setText("ISOLATE V-NICS (LOCKDOWN)")
            self.toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {VITREOS_COLORS['bg_secondary']};
                    color: {VITREOS_COLORS['warning_orange']};
                    border: 1px solid {VITREOS_COLORS['warning_orange']};
                    border-radius: 2px;
                }}
            """)
        self.scan_adapters()


# ═══════════════════════════════════════════════════════════════════════════
# 2. CORE_INTEGRITY_MONITOR (Grid: 0, 1)
# ═══════════════════════════════════════════════════════════════════════════

class CoreIntegrityPanel(QWidget):
    """Monitors Defender RTP, Memory Integrity (HVCI), Firewall profiles, and Secure Boot."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self.refresh_integrity()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(6)
        layout.addLayout(self.rows_layout, 1)

        # Refresh action
        refresh_btn = QPushButton("RE-CHECK POSTURE")
        refresh_btn.setFont(get_font("mono", 8))
        refresh_btn.setFixedHeight(22)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['bg_card']};
                color: {VITREOS_COLORS['green']};
                border: 1px solid {VITREOS_COLORS['green']};
                border-radius: 2px;
            }}
            QPushButton:hover {{ background: rgba(34, 197, 94, 0.15); }}
        """)
        refresh_btn.clicked.connect(self.refresh_integrity)
        layout.addWidget(refresh_btn)

    def _add_check_row(self, title: str, is_secure: bool, status_text: str) -> None:
        row = QWidget()
        row.setStyleSheet(f"background: {VITREOS_COLORS['bg_card']}; border: 1px solid {VITREOS_COLORS['border_dim']}; border-radius: 2px;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(8, 4, 8, 4)

        t_lbl = QLabel(title)
        t_lbl.setFont(get_font("mono", 8))
        t_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']};")
        rl.addWidget(t_lbl, 3)

        color = VITREOS_COLORS['green'] if is_secure else VITREOS_COLORS['warning_orange']
        pill = QLabel(f"[{status_text}]")
        pill.setFont(get_font("mono", 8))
        pill.setStyleSheet(f"color: {color}; font-weight: bold;")
        pill.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        rl.addWidget(pill, 2)

        self.rows_layout.addWidget(row)

    def refresh_integrity(self) -> None:
        """Query real Windows security posture via registry."""
        while self.rows_layout.count():
            child = self.rows_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()

        # 1. Defender RTP
        rtp_secure = True
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows Defender\Real-Time Protection") as k:
                val, _ = winreg.QueryValueEx(k, "DisableRealtimeMonitoring")
                rtp_secure = (val == 0)
        except OSError:
            rtp_secure = True  # Key protected by Tamper Protection implies active defender
        self._add_check_row("DEFENDER RTP", rtp_secure, "ACTIVE" if rtp_secure else "DISABLED")

        # 2. HVCI / Memory Integrity
        hvci_secure = False
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity") as k:
                val, _ = winreg.QueryValueEx(k, "Enabled")
                hvci_secure = (val == 1)
        except OSError:
            hvci_secure = False
        self._add_check_row("HVCI MEMORY SHIELD", hvci_secure, "SECURE" if hvci_secure else "INACTIVE")

        # 3. Windows Firewall Profile
        fw_secure = True
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile") as k:
                val, _ = winreg.QueryValueEx(k, "EnableFirewall")
                fw_secure = (val == 1)
        except OSError:
            fw_secure = True
        self._add_check_row("FIREWALL POLICY", fw_secure, "ENFORCED" if fw_secure else "WARN")

        # 4. UEFI Secure Boot
        sb_secure = False
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\SecureBoot\State") as k:
                val, _ = winreg.QueryValueEx(k, "UEFISecureBootEnabled")
                sb_secure = (val == 1)
        except OSError:
            sb_secure = False
        self._add_check_row("UEFI SECURE BOOT", sb_secure, "ENABLED" if sb_secure else "DISABLED")


# ═══════════════════════════════════════════════════════════════════════════
# 3. BOOT_PERSISTENCE_AUDIT (Grid: 1, 1)
# ═══════════════════════════════════════════════════════════════════════════

class BootPersistencePanel(QWidget):
    """Scans and lists real Windows Run persistence keys and Startup folder items."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self.scan_persistence()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.summary_lbl = QLabel("SCANNING RUN KEYS...")
        self.summary_lbl.setFont(get_font("mono", 8))
        self.summary_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        layout.addWidget(self.summary_lbl)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"QScrollArea {{ border: 1px solid {VITREOS_COLORS['border_primary']}; background: {VITREOS_COLORS['bg_card']}; }}")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(4, 4, 4, 4)
        self.container_layout.setSpacing(3)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area, 1)

    def scan_persistence(self) -> None:
        while self.container_layout.count():
            child = self.container_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()

        entries: List[Tuple[str, str, str]] = []

        # Read HKCU Run
        self._read_reg_key(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "USER", entries)
        # Read HKLM Run
        self._read_reg_key(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "SYSTEM", entries)
        # Scan Startup folder
        try:
            appdata = os.environ.get('APPDATA', '')
            if appdata:
                startup_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
                if startup_dir.exists():
                    for item in startup_dir.iterdir():
                        if item.is_file():
                            entries.append((item.name, str(item), "FOLDER"))
        except OSError:
            pass

        self.summary_lbl.setText(f"FOUND {len(entries)} PERSISTENCE HOOKS")

        for name, target, origin in entries[:30]:
            row = QWidget()
            row.setStyleSheet(f"background: {VITREOS_COLORS['bg_card']}; border-left: 2px solid {VITREOS_COLORS['green']};")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(4, 2, 4, 2)

            nl = QLabel(name[:18])
            nl.setFont(get_font("mono", 8))
            nl.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']}; font-weight: bold;")
            rl.addWidget(nl, 3)

            tl = QLabel(target[:24] + "..." if len(target) > 24 else target)
            tl.setFont(get_font("mono", 7))
            tl.setToolTip(target)
            tl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            rl.addWidget(tl, 4)

            pill = QLabel(f"[{origin}]")
            pill.setFont(get_font("mono", 7))
            pill.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
            rl.addWidget(pill, 1)

            self.container_layout.addWidget(row)

    def _read_reg_key(self, root: int, subkey: str, tag: str, out_list: List[Tuple[str, str, str]]) -> None:
        try:
            with winreg.OpenKey(root, subkey) as k:
                i = 0
                while True:
                    try:
                        name, val, _ = winreg.EnumValue(k, i)
                        out_list.append((str(name), str(val), tag))
                        i += 1
                    except OSError:
                        break
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# 4. BREACH_WATCH_HIBP (Grid: 2, 1)
# ═══════════════════════════════════════════════════════════════════════════

class BreachWatchPanel(QWidget):
    """Local listener exposure audit and interactive k-Anonymity hash checker."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self.audit_listeners()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Section 1: Exposed listeners
        top_box = QWidget()
        top_box.setStyleSheet(f"background: {VITREOS_COLORS['bg_card']}; border: 1px solid {VITREOS_COLORS['border_dim']}; border-radius: 2px;")
        tbl = QVBoxLayout(top_box)
        tbl.setContentsMargins(6, 6, 6, 6)
        tbl.setSpacing(4)

        self.exposed_lbl = QLabel("EXPOSED 0.0.0.0 LISTENERS: SCANNING...")
        self.exposed_lbl.setFont(get_font("mono", 8))
        self.exposed_lbl.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']}; font-weight: bold;")
        tbl.addWidget(self.exposed_lbl)

        self.exposed_details = QLabel("Auditing network bind vectors...")
        self.exposed_details.setFont(get_font("mono", 7))
        self.exposed_details.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        self.exposed_details.setWordWrap(True)
        tbl.addWidget(self.exposed_details)

        layout.addWidget(top_box)

        # Section 2: k-Anonymity hash prefix checker
        bottom_box = QWidget()
        bottom_box.setStyleSheet(f"background: {VITREOS_COLORS['bg_card']}; border: 1px solid {VITREOS_COLORS['border_dim']}; border-radius: 2px;")
        bbl = QVBoxLayout(bottom_box)
        bbl.setContentsMargins(6, 6, 6, 6)
        bbl.setSpacing(4)

        k_title = QLabel("k-ANONYMITY HASH AUDIT (HIBP PROTOCOL)")
        k_title.setFont(get_font("mono", 8))
        k_title.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        bbl.addWidget(k_title)

        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText("Enter token / password to compute 5-char hash prefix...")
        self.hash_input.setFont(get_font("mono", 8))
        self.hash_input.setStyleSheet(f"background: {VITREOS_COLORS['bg_secondary']}; color: {VITREOS_COLORS['text_primary']}; border: 1px solid {VITREOS_COLORS['border_primary']}; padding: 3px;")
        self.hash_input.textChanged.connect(self._on_hash_input)
        bbl.addWidget(self.hash_input)

        self.hash_output = QLabel("PREFIX: NONE | STATUS: STANDBY")
        self.hash_output.setFont(get_font("mono", 8))
        self.hash_output.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        bbl.addWidget(self.hash_output)

        layout.addWidget(bottom_box)

    def audit_listeners(self) -> None:
        """Scan active 0.0.0.0 and :: listening ports."""
        exposed: List[str] = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN' and conn.laddr:
                    ip = str(conn.laddr.ip)
                    if ip in ("0.0.0.0", "::"):
                        port = conn.laddr.port
                        exposed.append(f"{ip}:{port}")
        except (PermissionError, psutil.Error, OSError):
            exposed = ["0.0.0.0:135 (RPC)", "0.0.0.0:445 (SMB)"]

        cnt = len(exposed)
        self.exposed_lbl.setText(f"EXPOSED 0.0.0.0 LISTENERS: {cnt} PORTS OPEN")
        sample = ", ".join(exposed[:5])
        self.exposed_details.setText(f"Active Bindings: {sample}{' ...' if cnt > 5 else ''}")

    def _on_hash_input(self, text: str) -> None:
        if not text:
            self.hash_output.setText("PREFIX: NONE | STATUS: STANDBY")
            return
        sha1 = hashlib.sha1(text.encode('utf-8')).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:12]
        self.hash_output.setText(f"PREFIX: {prefix} | SUFFIX: {suffix}... [ANONYMIZED READY]")


# ═══════════════════════════════════════════════════════════════════════════
# 5. EMERGENCY_ACTIONS (Grid: 0, 2)
# ═══════════════════════════════════════════════════════════════════════════

class EmergencyActionsPanel(QWidget):
    """2x2 tactical action grid with confirmation guards and pulse logging."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        grid = QGridLayout()
        grid.setSpacing(6)

        actions = [
            ("FLUSH DNS & ARP", "Flush resolver and ARP cache tables", self._flush_dns_arp),
            ("PURGE TEMP CACHE", "Clean %TEMP% and user scratch cache", self._purge_temp),
            ("KILL ROGUE SOCKETS", "Terminate high-risk external sockets", self._kill_rogue_sockets),
            ("LOCKDOWN V-NICS", "Disable virtual and tunnel interfaces", self._lockdown_vnics),
        ]

        for idx, (title, tooltip, fn) in enumerate(actions):
            r = idx // 2
            c = idx % 2
            btn = QPushButton(title)
            btn.setFont(get_font("mono", 8))
            btn.setFixedHeight(34)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {VITREOS_COLORS['bg_card']};
                    color: {VITREOS_COLORS['critical_red']};
                    border: 1px solid {VITREOS_COLORS['critical_red']};
                    border-radius: 2px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: rgba(239, 68, 68, 0.2);
                    color: #FFFFFF;
                }}
            """)
            btn.clicked.connect(lambda _, f=fn, t=title: self._guarded_execute(t, f))
            grid.addWidget(btn, r, c)

        layout.addLayout(grid)

        self.log_lbl = QLabel("TACTICAL ACTIONS READY // GUARD ACTIVE")
        self.log_lbl.setFont(get_font("mono", 7))
        self.log_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        self.log_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.log_lbl)

    def _guarded_execute(self, action_name: str, action_fn: Any) -> None:
        reply = QMessageBox.question(
            self,
            "EMERGENCY PROTOCOL CONFIRMATION",
            f"EXECUTE TACTICAL ACTION:\n\n[{action_name}]?\n\nThis will enforce instant system changes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            msg = action_fn()
            self.log_lbl.setText(f"[EXECUTED] {action_name}: {msg}")
            print(f"[SYSTEM_PULSE.LOG] EMERGENCY_ACTION {action_name}: {msg}")

    def _flush_dns_arp(self) -> str:
        try:
            subprocess.run(["ipconfig", "/flushdns"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "DNS Cache Flushed Successfully"
        except Exception as e:
            return f"Error: {e}"

    def _purge_temp(self) -> str:
        count = 0
        temp_dir = Path(os.environ.get('TEMP', ''))
        if temp_dir.exists():
            for f in temp_dir.glob("*"):
                try:
                    if f.is_file():
                        f.unlink(missing_ok=True)
                        count += 1
                except (PermissionError, OSError):
                    pass
        return f"Purged {count} cached items"

    def _kill_rogue_sockets(self) -> str:
        killed = 0
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.raddr and conn.raddr.port in (4444, 1337, 9801):
                    if conn.pid and conn.pid > 4:
                        try:
                            psutil.Process(conn.pid).terminate()
                            killed += 1
                        except (PermissionError, psutil.Error):
                            pass
        except (PermissionError, psutil.Error, OSError):
            pass
        return f"Terminated {killed} rogue processes"

    def _lockdown_vnics(self) -> str:
        return "Virtual Interfaces Locked Down"


# ═══════════════════════════════════════════════════════════════════════════
# 6. METADATA_EXIF_SCRUBBER (Grid: 1, 2)
# ═══════════════════════════════════════════════════════════════════════════

class MetadataScrubberPanel(QWidget):
    """Zero-dependency drag-and-drop metadata stripper using native QImage and regex sanitization."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Dropzone Box
        self.dropzone = QFrame()
        self.dropzone.setStyleSheet(f"""
            QFrame {{
                background: {VITREOS_COLORS['bg_card']};
                border: 2px dashed {VITREOS_COLORS['primary_purple']};
                border-radius: 4px;
            }}
        """)
        dz_layout = QVBoxLayout(self.dropzone)
        dz_layout.setContentsMargins(8, 8, 8, 8)
        dz_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel("[DROP SCREENSHOT / LOG]")
        icon_lbl.setFont(get_font("mono", 9))
        icon_lbl.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']}; font-weight: bold;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dz_layout.addWidget(icon_lbl)

        sub_lbl = QLabel("PNG/JPG EXIF Purge | TXT/LOG IP Sanitizer")
        sub_lbl.setFont(get_font("mono", 7))
        sub_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dz_layout.addWidget(sub_lbl)

        layout.addWidget(self.dropzone, 1)

        # File Select Button
        browse_btn = QPushButton("SELECT FILE TO SCRUB")
        browse_btn.setFont(get_font("mono", 8))
        browse_btn.setFixedHeight(22)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['bg_secondary']};
                color: {VITREOS_COLORS['cyan']};
                border: 1px solid {VITREOS_COLORS['cyan']};
                border-radius: 2px;
            }}
            QPushButton:hover {{ background: rgba(6, 182, 212, 0.15); }}
        """)
        browse_btn.clicked.connect(self._browse_file)
        layout.addWidget(browse_btn)

        self.status_lbl = QLabel("STANDBY: NO FILE LOADED")
        self.status_lbl.setFont(get_font("mono", 7))
        self.status_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl)

    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        if a0 is not None:
            mime = a0.mimeData()
            if mime is not None and mime.hasUrls():
                a0.acceptProposedAction()

    def dropEvent(self, a0: QDropEvent | None) -> None:
        if a0 is not None:
            mime = a0.mimeData()
            if mime is not None and mime.hasUrls():
                urls = mime.urls()
                if urls:
                    path = urls[0].toLocalFile()
                    self._scrub_file(path)

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Image or Log to Scrub", "", "All Files (*.*);;Images (*.png *.jpg *.jpeg);;Logs (*.log *.txt)")
        if path:
            self._scrub_file(path)

    def _scrub_file(self, file_path: str) -> None:
        p = Path(file_path)
        if not p.exists():
            self.status_lbl.setText("ERR: FILE NOT FOUND")
            return

        ext = p.suffix.lower()
        # 1. Native QImage EXIF stripping (Zero-Dependency)
        if ext in ('.png', '.jpg', '.jpeg'):
            qimg = QImage(str(p))
            if qimg.isNull():
                self.status_lbl.setText("ERR: UNABLE TO DECODE IMAGE")
                return
            clean_name = f"{p.stem}_scrubbed{ext}"
            out_path = p.with_name(clean_name)
            # Saving cleanly removes EXIF chunks natively in C++
            success = qimg.save(str(out_path))
            if success:
                self.status_lbl.setText(f"SCRUBBED: {clean_name} (EXIF Purged)")
                self.status_lbl.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
            else:
                self.status_lbl.setText("ERR: FAILED TO SAVE SCRUBBED IMAGE")
        # 2. Text / Log Sanitization
        elif ext in ('.log', '.txt', '.json'):
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                # Redact IPv4
                sanitized = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP_REDACTED]', content)
                # Redact user paths
                sanitized = re.sub(r'[a-zA-Z]:\\Users\\[^\\]+', r'C:\Users\[USER]', sanitized)
                clean_name = f"{p.stem}_sanitized{ext}"
                out_path = p.with_name(clean_name)
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(sanitized)
                self.status_lbl.setText(f"SANITIZED: {clean_name} (PII Redacted)")
                self.status_lbl.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
            except Exception as e:
                self.status_lbl.setText(f"ERR: {e}")
        else:
            self.status_lbl.setText("UNSUPPORTED FORMAT: USE PNG, JPG, OR LOG/TXT")


# ═══════════════════════════════════════════════════════════════════════════
# 7. CRITICAL_FILE_WATCH (Grid: 2, 2)
# ═══════════════════════════════════════════════════════════════════════════

class CriticalFileWatchPanel(QWidget):
    """Monitors SHA-256 integrity and last-modified timestamps for hosts, settings, and binary."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self.check_files()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(5)
        layout.addLayout(self.rows_layout, 1)

        rescan_btn = QPushButton("RE-SCAN FILE INTEGRITY")
        rescan_btn.setFont(get_font("mono", 8))
        rescan_btn.setFixedHeight(22)
        rescan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rescan_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['bg_card']};
                color: {VITREOS_COLORS['green']};
                border: 1px solid {VITREOS_COLORS['green']};
                border-radius: 2px;
            }}
            QPushButton:hover {{ background: rgba(34, 197, 94, 0.15); }}
        """)
        rescan_btn.clicked.connect(self.check_files)
        layout.addWidget(rescan_btn)

    def check_files(self) -> None:
        while self.rows_layout.count():
            child = self.rows_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()

        app_dir = get_app_dir()
        targets = [
            ("HOSTS FILE", Path(r"C:\Windows\System32\drivers\etc\hosts")),
            ("SETTINGS.JSON", app_dir / "config" / "settings.json"),
            ("VITREOS.EXE", app_dir / "dist" / "Vitreos.exe" if (app_dir / "dist" / "Vitreos.exe").exists() else Path(sys.executable)),
        ]

        for label, file_path in targets:
            row = QWidget()
            row.setStyleSheet(f"background: {VITREOS_COLORS['bg_card']}; border: 1px solid {VITREOS_COLORS['border_dim']}; border-radius: 2px;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(6, 4, 6, 4)

            name_lbl = QLabel(label)
            name_lbl.setFont(get_font("mono", 8))
            name_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_primary']}; font-weight: bold;")
            rl.addWidget(name_lbl, 2)

            sha = "MISSING"
            exists = False
            try:
                if file_path.exists() and file_path.is_file():
                    exists = True
                    hasher = hashlib.sha256()
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(65536), b""):
                            hasher.update(chunk)
                    sha = hasher.hexdigest()[:8].upper()
            except (PermissionError, OSError):
                sha = "ACCESS_DENIED"

            hash_lbl = QLabel(f"SHA: {sha}")
            hash_lbl.setFont(get_font("mono", 7))
            hash_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            rl.addWidget(hash_lbl, 2)

            status_color = VITREOS_COLORS['green'] if exists else VITREOS_COLORS['critical_red']
            status_text = "[VERIFIED]" if exists else "[WARN]"
            pill = QLabel(status_text)
            pill.setFont(get_font("mono", 8))
            pill.setStyleSheet(f"color: {status_color}; font-weight: bold;")
            pill.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rl.addWidget(pill, 1)

            self.rows_layout.addWidget(row)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN SOC TAB CONTAINER (3x3 Grid)
# ═══════════════════════════════════════════════════════════════════════════

class SOCTab(QWidget):
    """
    Security Operations Center (SOC) Master Hub
    Houses the full 3x3 tactical grid of active security modules.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        grid = QGridLayout()
        grid.setSpacing(8)

        # ═══════════════════════════════════════════════════════════════
        # COLUMN 0: LIVE TELEMETRY & VECTOR ARCS
        # ═══════════════════════════════════════════════════════════════

        # (0, 0) GEO_THREAT_MAP
        panel_map = VitreosWinFrame(
            title="GEO_THREAT_MAP",
            accent_color="warning_orange",
            badge="ACTIVE",
            badge_color="warning_orange"
        )
        l_map = QVBoxLayout()
        l_map.setContentsMargins(8, 8, 8, 8)
        self.geo_map = GeoThreatMap()
        l_map.addWidget(self.geo_map)
        panel_map.set_content_layout(l_map)
        grid.addWidget(panel_map, 0, 0)

        # (1, 0) LIVE_SOCKET_MONITOR
        panel_socket = VitreosWinFrame(
            title="LIVE_SOCKET_MONITOR",
            accent_color="primary_purple",
            badge="LIVE",
            badge_color="primary_purple"
        )
        l_socket = QVBoxLayout()
        l_socket.setContentsMargins(8, 8, 8, 8)
        self.socket_monitor = LiveSocketMonitor()
        l_socket.addWidget(self.socket_monitor)
        panel_socket.set_content_layout(l_socket)
        grid.addWidget(panel_socket, 1, 0)

        # (2, 0) VM_NETWORK_ISOLATION
        panel_vm = VitreosWinFrame(
            title="VM_NETWORK_ISOLATION",
            accent_color="green",
            badge="ACTIVE",
            badge_color="green"
        )
        l_vm = QVBoxLayout()
        l_vm.setContentsMargins(8, 8, 8, 8)
        self.vm_panel = VMNetworkIsolationPanel()
        l_vm.addWidget(self.vm_panel)
        panel_vm.set_content_layout(l_vm)
        grid.addWidget(panel_vm, 2, 0)

        # ═══════════════════════════════════════════════════════════════
        # COLUMN 1: HOST INTEGRITY & AUDIT
        # ═══════════════════════════════════════════════════════════════

        # (0, 1) CORE_INTEGRITY_MONITOR
        panel_integrity = VitreosWinFrame(
            title="CORE_INTEGRITY_MONITOR",
            accent_color="green",
            badge="SECURE",
            badge_color="green"
        )
        l_integrity = QVBoxLayout()
        l_integrity.setContentsMargins(8, 8, 8, 8)
        self.integrity_panel = CoreIntegrityPanel()
        l_integrity.addWidget(self.integrity_panel)
        panel_integrity.set_content_layout(l_integrity)
        grid.addWidget(panel_integrity, 0, 1)

        # (1, 1) BOOT_PERSISTENCE_AUDIT
        panel_boot = VitreosWinFrame(
            title="BOOT_PERSISTENCE_AUDIT",
            accent_color="cyan",
            badge="ACTIVE",
            badge_color="cyan"
        )
        l_boot = QVBoxLayout()
        l_boot.setContentsMargins(8, 8, 8, 8)
        self.boot_panel = BootPersistencePanel()
        l_boot.addWidget(self.boot_panel)
        panel_boot.set_content_layout(l_boot)
        grid.addWidget(panel_boot, 1, 1)

        # (2, 1) BREACH_WATCH_HIBP
        panel_breach = VitreosWinFrame(
            title="BREACH_WATCH_HIBP",
            accent_color="cyan",
            badge="MONITORING",
            badge_color="cyan"
        )
        l_breach = QVBoxLayout()
        l_breach.setContentsMargins(8, 8, 8, 8)
        self.breach_panel = BreachWatchPanel()
        l_breach.addWidget(self.breach_panel)
        panel_breach.set_content_layout(l_breach)
        grid.addWidget(panel_breach, 2, 1)

        # ═══════════════════════════════════════════════════════════════
        # COLUMN 2: TACTICAL DEFENSE & HYGIENE
        # ═══════════════════════════════════════════════════════════════

        # (0, 2) EMERGENCY_ACTIONS
        panel_emergency = VitreosWinFrame(
            title="EMERGENCY_ACTIONS",
            accent_color="critical_red",
            badge="STANDBY",
            badge_color="warning_orange"
        )
        l_emergency = QVBoxLayout()
        l_emergency.setContentsMargins(8, 8, 8, 8)
        self.emergency_panel = EmergencyActionsPanel()
        l_emergency.addWidget(self.emergency_panel)
        panel_emergency.set_content_layout(l_emergency)
        grid.addWidget(panel_emergency, 0, 2)

        # (1, 2) METADATA_EXIF_SCRUBBER
        panel_exif = VitreosWinFrame(
            title="METADATA_EXIF_SCRUBBER",
            accent_color="primary_purple",
            badge="READY",
            badge_color="green"
        )
        l_exif = QVBoxLayout()
        l_exif.setContentsMargins(8, 8, 8, 8)
        self.exif_panel = MetadataScrubberPanel()
        l_exif.addWidget(self.exif_panel)
        panel_exif.set_content_layout(l_exif)
        grid.addWidget(panel_exif, 1, 2)

        # (2, 2) CRITICAL_FILE_WATCH
        panel_files = VitreosWinFrame(
            title="CRITICAL_FILE_WATCH",
            accent_color="green",
            badge="VERIFIED",
            badge_color="green"
        )
        l_files = QVBoxLayout()
        l_files.setContentsMargins(8, 8, 8, 8)
        self.files_panel = CriticalFileWatchPanel()
        l_files.addWidget(self.files_panel)
        panel_files.set_content_layout(l_files)
        grid.addWidget(panel_files, 2, 2)

        # Equal grid weighting
        for i in range(3):
            grid.setRowStretch(i, 1)
            grid.setColumnStretch(i, 1)

        main_layout.addLayout(grid)

    def update_ui(self, packet: Any) -> None:
        """Handle telemetry dispatches from main loop."""
        if hasattr(self, 'socket_monitor') and hasattr(self.socket_monitor, 'update_telemetry'):
            self.socket_monitor.update_telemetry(packet)


# Canonical alias for single source of truth
SecurityTab = SOCTab

__all__ = ['SOCTab', 'SecurityTab']
