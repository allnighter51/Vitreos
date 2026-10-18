# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportArgumentType=false, reportUnusedVariable=false, reportOptionalMemberAccess=false
"""
Vitreos Monitoring Modules - Dashboard Widgets
Individual monitoring components for the 2x3 grid layout
"""

from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPaintEvent

from src.ui.vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font
from src.ui.vitreos_widgets import (
    VitreosWinFrame, VitreosSegmentedBar, VitreosVerticalBar,
    VitreosCircularGauge, VitreosBarcode, ConnectionStatus, HazardBadge, OCBadge, apply_phosphor_glow
)

# Explicitly ensure no mock drives are present at module load
_MOCK_DRIVES: list = []

class DriveCardWidget(QWidget):
    """Single drive card matching Figma V4 StorageArray DriveRow spec."""

    def __init__(self, drive_type: str, model: str, serial: str,
                 temp: int, used_gb: float, total_gb: float,
                 read_speed: float, write_speed: float,
                 max_read: int, max_write: int,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        # Defensive placeholders to avoid AttributeError if refresh is called
        # before the widgets are fully constructed (robustness for async updates)
        self.read_val = None
        self.write_val = None
        self.read_bar = None
        self.write_bar = None
        self.temp_label = None
        self.cap_bar = None
        self._build(drive_type, model, serial, temp,
                used_gb, total_gb, read_speed, write_speed, max_read, max_write)

    def _build(self, drive_type: str, model: str, serial: str,
               temp: int, used_gb: float, total_gb: float,
               read_speed: float, write_speed: float,
               max_read: int, max_write: int) -> None:
        # Figma: bg #0A0A0A, 1px border #1E1E1E, 2px left border #A855F7
        self.setStyleSheet("""
            DriveCardWidget {
                background: #0A0A0A;
                border: 1px solid #1E1E1E;
                border-left: 2px solid #A855F7;
            }
        """)
        self.setMinimumHeight(96)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(4)

        # ── Row 1: type badge | model | temp ──────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        type_badge = QLabel(f'[ {drive_type} ]')
        type_badge.setFont(get_font('mono', FONT_SIZES['micro']))
        type_badge.setStyleSheet("""
            color: #A855F7;
            background: #1A1A1A;
            border: 1px solid #2A2A2A;
            padding: 0px 3px;
        """)
        row1.addWidget(type_badge)

        model_label = QLabel(model)
        model_label.setFont(get_font('mono', FONT_SIZES['small']))
        model_label.setStyleSheet('color: #888888;')
        row1.addWidget(model_label)
        row1.addStretch()

        if temp is None or temp <= 0:
            temp_text = '--°C'
            temp_color = VITREOS_COLORS['text_dim']
        else:
            temp_text = f'{temp}°C'
            temp_color = '#FF6B00' if temp > 45 else '#A855F7'
        self.temp_label = QLabel(temp_text)
        self.temp_label.setFont(get_font('mono', FONT_SIZES['small']))
        self.temp_label.setStyleSheet(f'color: {temp_color};')
        row1.addWidget(self.temp_label)
        root.addLayout(row1)

        # ── Row 2: serial ─────────────────────────────────────────────────
        sn_label = QLabel(f'S/N: {serial}')
        sn_label.setFont(get_font('mono', FONT_SIZES['micro']))
        sn_label.setStyleSheet('color: #333333;')
        root.addWidget(sn_label)

        # ── Row 3: capacity bar (purple) ──────────────────────────────────
        used_pct = (used_gb / total_gb * 100) if total_gb > 0 else 0
        free_gb  = total_gb - used_gb

        cap_labels = QHBoxLayout()
        used_lbl = QLabel(f'{used_gb:.0f} GB used')
        used_lbl.setFont(get_font('mono', FONT_SIZES['micro']))
        used_lbl.setStyleSheet('color: #444444;')
        cap_labels.addWidget(used_lbl)
        cap_labels.addStretch()
        free_lbl = QLabel(f'{free_gb:.0f} GB free')
        free_lbl.setFont(get_font('mono', FONT_SIZES['micro']))
        free_lbl.setStyleSheet('color: #333333;')
        cap_labels.addWidget(free_lbl)
        root.addLayout(cap_labels)

        self.cap_bar = VitreosSegmentedBar(segments=20, height=5,
                                           hex_color='#A855F7', alert_threshold=1.1)
        self.cap_bar.set_value(used_pct, 100)
        root.addWidget(self.cap_bar)

        # ── Row 4: read | write bars (50/50 split) ────────────────────────
        io_row = QHBoxLayout()
        io_row.setSpacing(8)

        # Left: MAX READ (cyan)
        read_col = QVBoxLayout()
        read_col.setSpacing(2)
        read_hdr = QHBoxLayout()
        read_lbl = QLabel('MAX READ')
        read_lbl.setFont(get_font('mono', FONT_SIZES['micro']))
        read_lbl.setStyleSheet('color: #333333;')
        read_hdr.addWidget(read_lbl)
        read_hdr.addStretch()
        self.read_val = QLabel(f'{max_read} <span style="color:#1E4A5A; font-size:6pt;">MB/s</span>')
        self.read_val.setFont(get_font('mono', FONT_SIZES['small']))
        self.read_val.setStyleSheet('color: #06B6D4;')
        self.read_val.setTextFormat(Qt.TextFormat.RichText)
        read_hdr.addWidget(self.read_val)
        read_col.addLayout(read_hdr)
        self.read_bar = VitreosSegmentedBar(segments=12, height=4,
                                            hex_color='#06B6D4', alert_threshold=1.1)
        # Use provided max_read as the scaling denominator so the bar reflects actual throughput
        try:
            self.max_read = float(max_read)
        except Exception:
            self.max_read = 7000.0
        self.read_bar.set_value(read_speed, self.max_read)
        read_col.addWidget(self.read_bar)
        io_row.addLayout(read_col)

        # Right: MAX WRITE (orange)
        write_col = QVBoxLayout()
        write_col.setSpacing(2)
        write_hdr = QHBoxLayout()
        write_lbl = QLabel('MAX WRITE')
        write_lbl.setFont(get_font('mono', FONT_SIZES['micro']))
        write_lbl.setStyleSheet('color: #333333;')
        write_hdr.addWidget(write_lbl)
        write_hdr.addStretch()
        self.write_val = QLabel(f'{max_write} <span style="color:#4A2500; font-size:6pt;">MB/s</span>')
        self.write_val.setFont(get_font('mono', FONT_SIZES['small']))
        self.write_val.setStyleSheet('color: #FF6B00;')
        self.write_val.setTextFormat(Qt.TextFormat.RichText)
        write_hdr.addWidget(self.write_val)
        write_col.addLayout(write_hdr)
        self.write_bar = VitreosSegmentedBar(segments=12, height=4,
                                             hex_color='#FF6B00', alert_threshold=1.1)
        try:
            self.max_write = float(max_write)
        except Exception:
            self.max_write = 7000.0
        self.write_bar.set_value(write_speed, self.max_write)
        write_col.addWidget(self.write_bar)
        io_row.addLayout(write_col)

        root.addLayout(io_row)

    def refresh(self, temp: int, used_gb: float, total_gb: float,
                read_speed: float, write_speed: float) -> None:
        """Update live values without rebuilding the widget."""
        used_pct   = (used_gb / total_gb * 100) if total_gb > 0 else 0
        temp_color = '#FF6B00' if temp > 45 else '#A855F7'
        # Display '--°C' when telemetry reports zero/unavailable temperature
        try:
            if temp is None or temp <= 0:
                if self.temp_label is not None:
                    self.temp_label.setStyleSheet(f'color: {VITREOS_COLORS["text_dim"]};')
                    self.temp_label.setText('--°C')
            else:
                if self.temp_label is not None:
                    self.temp_label.setStyleSheet(f'color: {temp_color};')
                    self.temp_label.setText(f'{temp}°C')
        except Exception:
            pass
        self.cap_bar.set_value(used_pct, 100)
        # Update bars using the last-known maxima for proper scaling
        try:
            if self.read_bar is not None:
                self.read_bar.set_value(read_speed, getattr(self, 'max_read', 7000.0))
        except Exception:
            try:
                if self.read_bar is not None:
                    self.read_bar.set_value(read_speed, 7000.0)
            except Exception:
                pass
        try:
            if self.write_bar is not None:
                self.write_bar.set_value(write_speed, getattr(self, 'max_write', 7000.0))
        except Exception:
            try:
                if self.write_bar is not None:
                    self.write_bar.set_value(write_speed, 7000.0)
            except Exception:
                pass
        # Update numeric labels to show current / max (MB/s)
        try:
            if self.read_val is not None:
                self.read_val.setText(f"{int(read_speed)} / {int(getattr(self,'max_read',7000.0))} <span style=\"color:#1E4A5A; font-size:6pt;\">MB/s</span>")
        except Exception:
            pass
        try:
            if self.write_val is not None:
                self.write_val.setText(f"{int(write_speed)} / {int(getattr(self,'max_write',7000.0))} <span style=\"color:#4A2500; font-size:6pt;\">MB/s</span>")
        except Exception:
            pass


class StorageArray(VitreosWinFrame):
    """DISK_ARRAY module rebuilt to Figma V4 spec."""



    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title='DISK_ARRAY', accent_color='primary_purple', parent=parent)
        self._drive_cards: Dict[str, DriveCardWidget] = {}
        self._setup_content()

    def _setup_content(self) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        # ── Header: title + READ/WRITE legend ─────────────────────────────
        header = QHBoxLayout()
        title_lbl = QLabel('STORAGE ARRAY')
        title_lbl.setFont(get_font('mono', FONT_SIZES['title']))
        title_lbl.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        header.addWidget(title_lbl)
        header.addStretch()

        read_badge = QLabel('● READ')
        read_badge.setFont(get_font('mono', FONT_SIZES['micro']))
        read_badge.setStyleSheet("""
            color: #06B6D4;
            background: #0A1A1A;
            border: 1px solid rgba(6,182,212,0.33);
            padding: 1px 5px;
        """)
        header.addWidget(read_badge)

        write_badge = QLabel('● WRITE')
        write_badge.setFont(get_font('mono', FONT_SIZES['micro']))
        write_badge.setStyleSheet("""
            color: #FF6B00;
            background: #1A0500;
            border: 1px solid rgba(255,107,0,0.33);
            padding: 1px 5px;
        """)
        header.addWidget(write_badge)
        outer.addLayout(header)

        # ── Drive cards scroll area ───────────────────────────────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ 
                width: 4px; 
                background: {VITREOS_COLORS['bg_primary']}; 
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{ 
                background: {VITREOS_COLORS['primary_purple']}; 
                border-radius: 2px;
            }}
        """)

        drives_container = QWidget()
        drives_container.setStyleSheet("background: transparent;")
        self.drives_layout = QVBoxLayout(drives_container)
        self.drives_layout.setContentsMargins(0, 0, 4, 0)
        self.drives_layout.setSpacing(6)
        self.drives_layout.addStretch()
        self.scroll_area.setWidget(drives_container)

        outer.addWidget(self.scroll_area, 1)

        # ── Footer: RAID status ───────────────────────────────────────────
        footer = QWidget()
        footer.setStyleSheet("""
            background: #0A0A0A;
            border: 1px solid #1E1E1E;
            border-left: 2px solid #333333;
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(8, 4, 8, 4)

        raid_left = QHBoxLayout()
        raid_left.setSpacing(4)
        arrow = QLabel('▷')
        arrow.setFont(get_font('mono', FONT_SIZES['small']))
        arrow.setStyleSheet('color: #3A3A3A;')
        raid_left.addWidget(arrow)
        raid_text = QLabel('NO RAID CONFIGURED')
        raid_text.setFont(get_font('mono', FONT_SIZES['small']))
        raid_text.setStyleSheet('color: #3A3A3A; letter-spacing: 1px;')
        raid_left.addWidget(raid_text)
        footer_layout.addLayout(raid_left)
        footer_layout.addStretch()

        ahci_label = QLabel('AHCI')
        ahci_label.setFont(get_font('mono', FONT_SIZES['micro']))
        ahci_label.setStyleSheet('color: #222222;')
        footer_layout.addWidget(ahci_label)

        outer.addWidget(footer)
        self.set_content_layout(outer)

    def update_data(self, data: Dict[str, Any]) -> None:
        """
        Update storage drives.

        Accepts either a storage dict (with key 'drives') or a payload that is already
        the storage dict. Dynamically create `DriveCardWidget` instances for new
        drives and refresh existing ones. Remove stale widgets when drives disappear.
        """
        # Accept either top-level storage dict or a wrapper
        storage = data.get('storage') if isinstance(data, dict) and 'storage' in data else data
        drives = storage.get('drives', []) if isinstance(storage, dict) else []

        # Normalize empty drives
        if not drives:
            # If no drives are reported, remove existing cards to avoid stale UI
            if self._drive_cards:
                for key, card in list(self._drive_cards.items()):
                    try:
                        self.drives_layout.removeWidget(card)
                        card.setParent(None)
                        card.deleteLater()
                    except Exception:
                        pass
                self._drive_cards.clear()
                self.update()
                self.repaint()
            return

        existing_keys = set(self._drive_cards.keys())
        seen_keys = set()

        for drive in drives:
            # Key selection: prefer mountpoint, fall back to device or serial
            key = drive.get('mountpoint') or drive.get('device') or drive.get('serial') or str(drive.get('model'))
            seen_keys.add(key)

            drive_type = drive.get('type', 'Unknown')
            model = drive.get('model', 'Unknown')
            serial = drive.get('serial', drive.get('device', ''))

            # numeric values with fallbacks
            temp = int(drive.get('temp', 0) or 0)
            used_gb = float(drive.get('usedGB', drive.get('used', 0) or 0))
            total_gb = float(drive.get('totalGB', drive.get('total', 1) or 1))
            read_speed = float(drive.get('readSpeed', 0) or 0)
            write_speed = float(drive.get('writeSpeed', 0) or 0)
            max_read = int(drive.get('maxRead', 7000))
            max_write = int(drive.get('maxWrite', 6600))

            if key in self._drive_cards:
                # Refresh existing card
                try:
                    self._drive_cards[key].refresh(
                        temp=temp,
                        used_gb=used_gb,
                        total_gb=total_gb,
                        read_speed=read_speed,
                        write_speed=write_speed,
                    )
                except Exception:
                    pass
            else:
                # Create and add new card
                try:
                    card = DriveCardWidget(
                        drive_type=drive_type,
                        model=model,
                        serial=serial,
                        temp=temp,
                        used_gb=used_gb,
                        total_gb=total_gb,
                        read_speed=read_speed,
                        write_speed=write_speed,
                        max_read=max_read,
                        max_write=max_write,
                    )
                except TypeError:
                    # Fallback to positional if signature differs
                    card = DriveCardWidget(drive_type, model, serial, temp, used_gb, total_gb, read_speed, write_speed, max_read, max_write)

                self._drive_cards[key] = card
                self.drives_layout.insertWidget(max(0, self.drives_layout.count() - 1), card)

        # Remove cards for drives that disappeared
        remove_keys = existing_keys - seen_keys
        for k in remove_keys:
            card = self._drive_cards.pop(k, None)
            if card:
                try:
                    self.drives_layout.removeWidget(card)
                    card.setParent(None)
                    card.deleteLater()
                except Exception:
                    pass

        # Force a UI refresh so newly added widgets appear immediately
        try:
            self.drives_layout.update()
        except Exception:
            pass
        try:
            self.update()
            self.repaint()
        except Exception:
            pass


class DimmSlotWidget(QWidget):
    """Visual representation of a single DIMM slot (vertical stick)."""
    def __init__(self, slot_id: str, capacity_gb: Optional[float] = None,
                 populated: bool = False, manufacturer: str = '', part: str = '',
                 serial: str = '', speed_mt: Optional[int] = None,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.slot_id = slot_id
        self.capacity_gb = capacity_gb
        self.populated = populated
        self.manufacturer = manufacturer
        self.part = part
        self.serial = serial
        self.speed_mt = speed_mt or 0
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Vertical stick representation
        self.stick = QFrame()
        self.stick.setFixedSize(48, 120)
        self.stick.setStyleSheet(self._empty_style())
        layout.addWidget(self.stick, alignment=Qt.AlignmentFlag.AlignCenter)

        # Slot label (A1, A2, ...)
        self.slot_label = QLabel(self.slot_id)
        self.slot_label.setFont(get_font('mono', FONT_SIZES['micro']))
        self.slot_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
        self.slot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.slot_label)

        # Capacity / status label
        cap_text = f"{int(self.capacity_gb)} GB" if self.capacity_gb and self.capacity_gb > 0 else "EMPTY"
        self.cap_label = QLabel(cap_text)
        self.cap_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        self.cap_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        self.cap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.cap_label)

        self.setLayout(layout)

    def _empty_style(self) -> str:
        return f"background: transparent; border: 2px dashed {VITREOS_COLORS['border_secondary']}; border-radius:4px;"

    def _populated_style(self) -> str:
        return f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {VITREOS_COLORS['primary_purple']}, stop:1 {VITREOS_COLORS['purple_dim']}); border: 1px solid {VITREOS_COLORS['border_primary']}; border-radius:4px;"

    def set_slot(self, info: Dict[str, Any]) -> None:
        """Update visual state from telemetry slot info."""
        try:
            cap = info.get('capacityGB', None)
            if cap is None:
                cap = info.get('capacity', None)
            self.capacity_gb = float(cap) if cap else 0.0
        except Exception:
            self.capacity_gb = 0.0

        self.manufacturer = info.get('manufacturer', '') or ''
        self.part = info.get('partNumber', '') or ''
        self.serial = info.get('serial', '') or ''
        self.speed_mt = int(info.get('configuredClock', info.get('speedMT', 0)) or 0)

        self.populated = bool(self.capacity_gb and self.capacity_gb > 0)

        if self.populated:
            self.stick.setStyleSheet(self._populated_style())
            self.cap_label.setText(f"{int(self.capacity_gb)} GB")
            self.cap_label.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
            tooltip = f"{self.manufacturer} {self.part} — {self.speed_mt} MT/s\nS/N: {self.serial}"
            self.setToolTip(tooltip)
        else:
            self.stick.setStyleSheet(self._empty_style())
            self.cap_label.setText('EMPTY')
            self.cap_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            self.setToolTip('Empty slot')


class DimmArray(QWidget):
    """Horizontal array of 4 DIMM slots (A1, A2, B1, B2) with footers and XMP bar."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.order = ['A1', 'A2', 'B1', 'B2']
        self.slots: Dict[str, DimmSlotWidget] = {}
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(12)
        for loc in self.order:
            w = DimmSlotWidget(loc)
            self.slots[loc] = w
            row.addWidget(w)
        outer.addLayout(row)

        # Footer panels (Effective Speed | Channel Mode)
        footer = QHBoxLayout()
        footer.setSpacing(8)

        self.eff_widget = QWidget()
        self.eff_widget.setStyleSheet(f"background: {VITREOS_COLORS['bg_card']}; border: 1px solid {VITREOS_COLORS['border_secondary']};")
        eff_layout = QVBoxLayout(self.eff_widget)
        eff_layout.setContentsMargins(6, 6, 6, 6)
        eff_title = QLabel('EFFECTIVE SPEED')
        eff_title.setFont(get_font('mono', FONT_SIZES['micro']))
        eff_title.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
        eff_layout.addWidget(eff_title)
        self.eff_value = QLabel('-- MT/s')
        self.eff_value.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.eff_value.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
        eff_layout.addWidget(self.eff_value)
        footer.addWidget(self.eff_widget)

        self.chan_widget = QWidget()
        self.chan_widget.setStyleSheet(f"background: {VITREOS_COLORS['bg_card']}; border: 1px solid {VITREOS_COLORS['border_secondary']};")
        chan_layout = QVBoxLayout(self.chan_widget)
        chan_layout.setContentsMargins(6, 6, 6, 6)
        chan_title = QLabel('CHANNEL MODE')
        chan_title.setFont(get_font('mono', FONT_SIZES['micro']))
        chan_title.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
        chan_layout.addWidget(chan_title)
        self.chan_value = QLabel('UNKNOWN')
        self.chan_value.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.chan_value.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        chan_layout.addWidget(self.chan_value)
        footer.addWidget(self.chan_widget)

        outer.addLayout(footer)

        # XMP/EXPO indicator bar (hidden by default)
        self.xmp_bar = QFrame()
        self.xmp_bar.setFixedHeight(6)
        self.xmp_bar.setStyleSheet(f"background: {VITREOS_COLORS['warning_orange']}; border-radius: 2px;")
        self.xmp_bar.hide()
        outer.addWidget(self.xmp_bar)

        self.setLayout(outer)

    def update_slots(self, slots_info: List[Dict[str, Any]]) -> None:
        import re

        # Defensive: ensure iterable
        if not slots_info:
            for k in self.order:
                self.slots[k].set_slot({})
            return

        # Normalize locators and prepare items
        processed = []
        for s in slots_info:
            # Support both 'locator' (snapshot) and legacy 'DeviceLocator'
            raw_loc = s.get('locator') or s.get('DeviceLocator') or ''
            loc = str(raw_loc).upper().strip()
            processed.append({'orig': s, 'loc': loc})

        mappings: Dict[str, Dict[str, Any]] = {}
        remaining = []

        # 1) Direct textual match (A1/A2/B1/B2)
        for item in processed:
            loc = item['loc']
            matched = False
            for slot_key in self.order:
                if slot_key in loc:
                    mappings[slot_key] = item['orig']
                    matched = True
                    break
            if not matched:
                remaining.append(item)

        # 2) Channel+DIMM patterns and BANK/DIMM numeric heuristics
        bank_map = {0: 'A1', 1: 'A2', 2: 'B1', 3: 'B2'}
        idx_map = {0: 'A1', 1: 'A2', 2: 'B1', 3: 'B2'}

        rem_copy = list(remaining)
        for item in rem_copy:
            loc = item['loc']
            assigned = False

            # ChannelA / ChannelB + DIMM index -> A1/A2, B1/B2
            m_cha = re.search(r'CHANNEL\s*A', loc)
            m_chb = re.search(r'CHANNEL\s*B', loc)
            m_dimm = re.search(r'DIMM\s*0*([0-9]+)', loc)
            if (m_cha or m_chb) and m_dimm:
                idx = int(m_dimm.group(1))
                target = 'A1' if (m_cha and idx == 0) else ('A2' if (m_cha and idx == 1) else ('B1' if (m_chb and idx == 0) else ('B2' if (m_chb and idx == 1) else None)))
                if target and target not in mappings:
                    mappings[target] = item['orig']
                    remaining.remove(item)
                    assigned = True
                    continue

            # BANK <n> -> map common ordering
            m_bank = re.search(r'BANK\s*0*([0-9]+)', loc)
            if m_bank:
                n = int(m_bank.group(1))
                target = bank_map.get(n)
                if target and target not in mappings:
                    mappings[target] = item['orig']
                    remaining.remove(item)
                    assigned = True
                    continue

            # DIMM<number> fallback -> index mapping
            if m_dimm:
                idx = int(m_dimm.group(1))
                target = idx_map.get(idx)
                if target and target not in mappings:
                    mappings[target] = item['orig']
                    remaining.remove(item)
                    assigned = True
                    continue

        # 3) Numeric trailing tokens like 'SLOT 1' or '1' -> try map
        rem_copy = list(remaining)
        for item in rem_copy:
            loc = item['loc']
            m_num = re.search(r'(?:SLOT|PORT|SLOT:)?\s*0*([0-9]+)\b$', loc)
            if m_num:
                idx = int(m_num.group(1))
                # Many firmware enumerations are 1-based
                idx0 = max(0, idx - 1)
                target = idx_map.get(idx0)
                if target and target not in mappings:
                    mappings[target] = item['orig']
                    remaining.remove(item)
                    continue

        # 4) Final fallback: assign remaining items in deterministic order to remaining slots
        unfilled = [s for s in self.order if s not in mappings]
        remaining_sorted = sorted(remaining, key=lambda x: x['loc'])
        for key, item in zip(unfilled, remaining_sorted):
            mappings[key] = item['orig']

        # 5) Apply to widgets; default to empty dict for missing slots
        for key in self.order:
            info = mappings.get(key, {})
            try:
                self.slots[key].set_slot(info)
            except Exception:
                # Ensure UI stays consistent even if set_slot fails
                try:
                    self.slots[key].set_slot({})
                except Exception:
                    pass

    def set_effective_speed(self, speed_mt: int) -> None:
        if speed_mt and speed_mt > 0:
            self.eff_value.setText(f"{speed_mt} MT/s")
        else:
            self.eff_value.setText('-- MT/s')

    def set_channel_mode(self, mode: str) -> None:
        self.chan_value.setText(mode.upper() if mode else 'UNKNOWN')

    def set_xmp_active(self, active: bool) -> None:
        if active:
            self.xmp_bar.show()
        else:
            self.xmp_bar.hide()


class MemoryArray(VitreosWinFrame):
    """Memory monitoring widget with circular gauge."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="MEMORY_ARRAY", accent_color="purple_dim", parent=parent)
        self._setup_content()
    
    def _setup_content(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(9, 9, 9, 9)  # Reduced by 25%
        layout.setSpacing(4)  # Reduced by 25%
        
        # Header with gauge
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        
        self.ram_gauge = VitreosCircularGauge(segments=40)
        header_row.addWidget(self.ram_gauge)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.status_label = QLabel("SEARCHING...")
        self.status_label.setFont(get_font('mono', FONT_SIZES['title']))
        self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        info_layout.addWidget(self.status_label)
        
        self.usage_label = QLabel("0.0 / 0.0 GB")
        self.usage_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
        self.usage_label.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
        info_layout.addWidget(self.usage_label)
        # Memory spec string (DDR speed / timings / voltage)
        self.spec_label = QLabel("")
        self.spec_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        self.spec_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        info_layout.addWidget(self.spec_label)
        
        header_row.addLayout(info_layout)
        header_row.addStretch()
        layout.addLayout(header_row)
        
        # Main bar
        bar_header = QHBoxLayout()
        bar_label = QLabel("SYSTEM MEMORY")
        bar_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        bar_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        bar_header.addWidget(bar_label)
        bar_header.addStretch()
        self.percent_label = QLabel("0%")
        self.percent_label.setFont(get_font('mono', FONT_SIZES['small']))
        self.percent_label.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
        bar_header.addWidget(self.percent_label)
        layout.addLayout(bar_header)
        
        self.mem_bar = VitreosSegmentedBar(segments=24, height=6, color='purple_dim')
        layout.addWidget(self.mem_bar)

        # DIMM slot row (A1, A2, B1, B2)
        self.dimm_array = DimmArray()
        layout.addWidget(self.dimm_array)
        
        # Stats grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(6)
        
        self.stat_labels = {}
        stats = [
            ('USED', 'used', 'GB', 'purple_dim'),
            ('FREE', 'free', 'GB', 'cyan'),
            ('CACHED', 'cached', 'GB', 'text_secondary'),
            ('AVAILABLE', 'available', 'GB', 'green'),
        ]
        
        for i, (label, key, unit, color) in enumerate(stats):
            stat_widget = QWidget()
            stat_widget.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
            """)
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(6, 6, 6, 6)
            stat_layout.setSpacing(2)
            
            stat_label = QLabel(label)
            stat_label.setFont(get_font('mono', FONT_SIZES['micro']))
            stat_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            stat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(stat_label)
            
            value_label = QLabel(f"0 {unit}")
            value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
            value_label.setStyleSheet(f"color: {VITREOS_COLORS[color]};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            
            self.stat_labels[key] = value_label
            stats_grid.addWidget(stat_widget, i // 2, i % 2)
        
        layout.addLayout(stats_grid)
        layout.addStretch()
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        used_gb = data.get('usedGB', data.get('used', 0))
        total_gb = data.get('totalGB', data.get('total', 0))
        percent = data.get('percent', data.get('percent', 0))
        
        if total_gb > 0:
            self.status_label.setText("ONLINE")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        else:
            self.status_label.setText("OFFLINE")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        
        self.usage_label.setText(f"{used_gb:.1f} / {total_gb:.1f} GB")
        self.percent_label.setText(f"{percent:.0f}%")
        self.mem_bar.set_value(percent, 100)
        self.ram_gauge.set_value(percent, 100, 'purple_dim')

        # New-style memory payload: slots, effectiveSpeed, channel, headerSpec, xmpActive
        if 'slots' in data:
            try:
                slots = data.get('slots', []) or []
                self.dimm_array.update_slots(slots)
                self.dimm_array.set_effective_speed(int(data.get('effectiveSpeed', 0) or 0))
                self.dimm_array.set_channel_mode(str(data.get('channel', 'UNKNOWN')))
                self.dimm_array.set_xmp_active(bool(data.get('xmpActive', False)))
                # Header spec
                header = data.get('headerSpec', '')
                if header:
                    self.spec_label.setText(header)
                else:
                    self.spec_label.setText('')
            except Exception:
                pass
        
        free_gb = total_gb - used_gb
        self.stat_labels['used'].setText(f"{used_gb:.1f} GB")
        self.stat_labels['free'].setText(f"{free_gb:.1f} GB")
        self.stat_labels['cached'].setText(f"{data.get('cachedGB', 0):.1f} GB")
        self.stat_labels['available'].setText(f"{data.get('availableGB', free_gb):.1f} GB")




class NetInterface(VitreosWinFrame):
    """Network monitoring widget with barcode signal visualizer."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="NET_INTERFACE", accent_color="green", parent=parent)
        self.telemetry_worker: Optional[Any] = None  # set by main window after init
        self.connection_status: Optional[ConnectionStatus] = None
        self._setup_content()
    
    def _setup_content(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(9, 9, 9, 9)  # Reduced by 25%
        layout.setSpacing(4)  # Reduced by 25%
        
        # Status header with connection indicator
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        
        self.status_label = QLabel("SEARCHING...")
        self.status_label.setFont(get_font('mono', FONT_SIZES['title']))
        self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        header_row.addWidget(self.status_label)
        
        header_row.addStretch()
        
        # Connection status indicator
        self.connection_status = ConnectionStatus("ETH", connected=False)
        header_row.addWidget(self.connection_status)
        
        layout.addLayout(header_row)
        
        # Barcode signal visualizer
        signal_label = QLabel("SIGNAL STRENGTH")
        signal_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        signal_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        layout.addWidget(signal_label)
        
        self.signal_barcode = VitreosBarcode(height=60)
        layout.addWidget(self.signal_barcode)
        
        # Throughput stats
        stats_grid = QGridLayout()
        stats_grid.setSpacing(6)
        
        self.stat_labels = {}
        stats = [
            ('DOWNLOAD', 'download', 'Mbps', 'cyan'),
            ('UPLOAD', 'upload', 'Mbps', 'warning_orange'),
            ('LATENCY', 'latency', 'ms', 'green'),
            ('PACKETS', 'packets', '/s', 'purple_dim'),
        ]
        
        for i, (label, key, unit, color) in enumerate(stats):
            stat_widget = QWidget()
            stat_widget.setStyleSheet(f"""
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_secondary']};
            """)
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(6, 6, 6, 6)
            stat_layout.setSpacing(2)
            
            stat_label = QLabel(label)
            stat_label.setFont(get_font('mono', FONT_SIZES['micro']))
            stat_label.setStyleSheet(f"color: {VITREOS_COLORS['text_darker']};")
            stat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(stat_label)
            
            value_label = QLabel(f"0 {unit}")
            value_label.setFont(get_font('mono', FONT_SIZES['value_medium']))
            value_label.setStyleSheet(f"color: {VITREOS_COLORS[color]};")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            
            self.stat_labels[key] = value_label
            stats_grid.addWidget(stat_widget, i // 2, i % 2)
        
        layout.addLayout(stats_grid)
        
        # Throughput bars
        dl_header = QHBoxLayout()
        dl_label = QLabel("DOWNLOAD")
        dl_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        dl_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        dl_header.addWidget(dl_label)
        dl_header.addStretch()
        self.dl_value = QLabel("0.00 Mbps")
        self.dl_value.setFont(get_font('mono', FONT_SIZES['small']))
        self.dl_value.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
        dl_header.addWidget(self.dl_value)
        layout.addLayout(dl_header)
        
        self.dl_bar = VitreosSegmentedBar(segments=24, height=6, color='cyan')
        layout.addWidget(self.dl_bar)
        
        ul_header = QHBoxLayout()
        ul_label = QLabel("UPLOAD")
        ul_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        ul_label.setStyleSheet(f"color: {VITREOS_COLORS['text_secondary']};")
        ul_header.addWidget(ul_label)
        ul_header.addStretch()
        self.ul_value = QLabel("0.00 Mbps")
        self.ul_value.setFont(get_font('mono', FONT_SIZES['small']))
        self.ul_value.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']};")
        ul_header.addWidget(self.ul_value)
        layout.addLayout(ul_header)
        
        self.ul_bar = VitreosSegmentedBar(segments=24, height=6, color='warning_orange')
        layout.addWidget(self.ul_bar)
        
        layout.addStretch()
        self.set_content_layout(layout)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        primary_nic = data.get('primaryNic', 'Unknown')
        if primary_nic != 'Unknown':
            self.status_label.setText(f"NETWORK I/O")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
            
            # Update connection status
            if self.connection_status:
                self.connection_status.set_connected(True)
        else:
            self.status_label.setText("OFFLINE")
            self.status_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            
            # Update connection status
            if self.connection_status:
                self.connection_status.set_connected(False)
        
        download = data.get('downloadMbps', 0)
        upload = data.get('uploadMbps', 0)
        latency = data.get('latency', 0)
        
        self.dl_value.setText(f"{download:.2f} Mbps")
        self.ul_value.setText(f"{upload:.2f} Mbps")
        
        self.dl_bar.set_value(download, 100)
        self.ul_bar.set_value(upload, 100)
        
        self.stat_labels['download'].setText(f"{download:.2f} Mbps")
        self.stat_labels['upload'].setText(f"{upload:.2f} Mbps")
        self.stat_labels['latency'].setText(f"{latency:.0f} ms")
        self.stat_labels['packets'].setText(f"{data.get('packetsPerSec', 0):.0f} /s")
