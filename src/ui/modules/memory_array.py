from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import QWidget, QGridLayout, QFrame, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt
from ..vitreos_theme import VITREOS_COLORS
from ..vitreos_widgets import VitreosWinFrame, VitreosSegmentedBar, VitreosCircularGauge
from ..factory import v_vbox, v_hbox, v_label, v_widget


def _short_locator(raw: str) -> str:
    """
    Shorten a WMI DeviceLocator string to fit in the slot widget label.
    Examples:
        'ChannelA-DIMM0'  -> 'CHA-D0'
        'DIMM_A2'         -> 'A2'
        'BANK 0'          -> 'BNK0'
        'P0-DIMMA2'       -> 'A2'
    Always returns something useful, max ~6 chars.
    """
    import re
    s = raw.strip()
    # Already short enough
    if len(s) <= 6:
        return s.upper()
    u = s.upper()
    # ChannelX-DIMMn  →  CHA-D0 / CHB-D1
    m = re.match(r'CHANNEL\s*([AB])[-_\s]*DIMM\s*(\d+)', u)
    if m:
        return f'CH{m.group(1)}-D{m.group(2)}'
    # DIMM_A2 / DIMM-B1 / DIMMA2 → A2
    m = re.search(r'DIMM[_\-\s]*([AB])(\d+)', u)
    if m:
        return f'{m.group(1)}{m.group(2)}'
    # P0-DIMMA2 / NODE0-DIMMA1
    m = re.search(r'DIMM([AB]\d+)', u)
    if m:
        return m.group(1)
    # BANK n
    m = re.match(r'BANK\s*(\d+)', u)
    if m:
        return f'BNK{m.group(1)}'
    # Generic: keep first 6 chars
    return u[:6]


class DimmSlotWidget(QWidget):
    """Visual representation of a single physical DIMM slot."""

    def __init__(self, slot_label: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.slot_label = slot_label
        self.capacity_gb = 0.0

        self.stick = QFrame()
        self.stick.setFixedSize(48, 120)
        self.stick.setStyleSheet(self._empty_style())
        self.stick.setToolTip('')

        self.lbl_slot = v_label(slot_label, font_size='micro', color='text_darker',
                                align=Qt.AlignmentFlag.AlignCenter)
        self.lbl_cap = v_label('EMPTY', font_size='tiny', color='text_dim',
                               align=Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addWidget(self.stick, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_slot)
        layout.addWidget(self.lbl_cap)

    # ── styles ─────────────────────────────────────────────────────────────
    def _empty_style(self) -> str:
        return (f"background: transparent; "
                f"border: 2px dashed {VITREOS_COLORS['border_secondary']}; "
                f"border-radius: 4px;")

    def _populated_style(self) -> str:
        return (f"background: qlineargradient(x1:0,y1:0,x2:0,y2:1, "
                f"stop:0 {VITREOS_COLORS['primary_purple']}, "
                f"stop:1 {VITREOS_COLORS['purple_dim']}); "
                f"border: 1px solid {VITREOS_COLORS['border_primary']}; "
                f"border-radius: 4px;")

    # ── public API ──────────────────────────────────────────────────────────
    def set_slot(self, info: Dict[str, Any]) -> None:
        """Update widget from a slot dict. Pass {} to mark as empty."""
        try:
            cap = info.get('capacityGB') or info.get('capacity')
            self.capacity_gb = float(cap) if cap else 0.0
        except Exception:
            self.capacity_gb = 0.0

        if self.capacity_gb > 0:
            self.stick.setStyleSheet(self._populated_style())
            self.lbl_cap.setText(f"{int(self.capacity_gb)} GB")
            self.lbl_cap.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
            # Tooltip shows full detail
            mfr  = info.get('manufacturer', '')
            part = info.get('partNumber', '')
            spd  = info.get('speed', 0)
            tip_parts = []
            if mfr:  tip_parts.append(mfr)
            if part: tip_parts.append(part)
            if spd:  tip_parts.append(f"{spd} MT/s")
            raw_loc = info.get('locator', self.slot_label)
            tip_parts.insert(0, raw_loc)
            self.stick.setToolTip('\n'.join(tip_parts))
            self.setToolTip('\n'.join(tip_parts))
        else:
            self.stick.setStyleSheet(self._empty_style())
            self.lbl_cap.setText('EMPTY')
            self.lbl_cap.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            self.stick.setToolTip('Empty slot')
            self.setToolTip('Empty slot')

    def update_label(self, label: str) -> None:
        self.slot_label = label
        self.lbl_slot.setText(label)


class DimmArray(QWidget):
    """
    Dynamically built DIMM slot row.

    Slot count and labels come directly from hardware telemetry
    (Win32_PhysicalMemoryArray for count, Win32_PhysicalMemory DeviceLocator
    for labels). No A1/A2/B1/B2 guessing — whatever WMI says is what we show.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._slot_widgets: List[DimmSlotWidget] = []
        self._current_total = 0

        # Outer layout: sticks row + footer
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(6)

        # Sticks row container (rebuilt when slot count changes)
        self._sticks_container = QWidget()
        self._sticks_layout = QHBoxLayout(self._sticks_container)
        self._sticks_layout.setContentsMargins(0, 0, 0, 0)
        self._sticks_layout.setSpacing(8)
        self._outer.addWidget(self._sticks_container)

        # Footer: Effective Speed | Channel Mode
        self.lbl_eff  = v_label('-- MT/s',  font_size='value_medium', color='purple_dim')
        self.lbl_chan = v_label('UNKNOWN',   font_size='value_medium', color='cyan')
        w_eff  = v_widget(bg='bg_card')
        w_chan = v_widget(bg='bg_card')
        w_eff.setLayout(v_vbox(margins=6, spacing=4, items=[
            v_label('EFFECTIVE SPEED', font_size='micro', color='text_darker'), self.lbl_eff]))
        w_chan.setLayout(v_vbox(margins=6, spacing=4, items=[
            v_label('CHANNEL MODE', font_size='micro', color='text_darker'), self.lbl_chan]))
        self._outer.addLayout(v_hbox(spacing=8, items=[w_eff, w_chan]))

        # Build a default 4-slot placeholder on first show
        self._rebuild(4, [])

    # ── internal helpers ────────────────────────────────────────────────────
    def _rebuild(self, total_slots: int, populated: List[Dict[str, Any]]) -> None:
        """Recreate slot widgets to match total_slots, populated with real data."""
        # Clear existing
        for w in self._slot_widgets:
            self._sticks_layout.removeWidget(w)
            w.setParent(None)  # type: ignore[arg-type]
            w.deleteLater()
        self._slot_widgets.clear()

        # Build a locator → info map from populated sticks
        pop_map: Dict[str, Dict[str, Any]] = {}
        for s in populated:
            loc = str(s.get('locator') or '').strip()
            if loc:
                pop_map[loc] = s

        # Sort populated locators so their order is stable
        pop_locators = sorted(pop_map.keys())

        # Determine all slot labels:
        # - Populated slots: use their real WMI locator (shortened for display)
        # - Empty slots: placeholder labels SLOT N
        #
        # If total_slots matches exactly the populated count, every slot is filled.
        # If total_slots > populated count, we add empty placeholders at the end.
        all_labels: List[str] = []
        for loc in pop_locators:
            all_labels.append(_short_locator(loc))

        for i in range(len(pop_locators), total_slots):
            all_labels.append(f'SLOT {i + 1}')

        # Create widgets
        for i, label in enumerate(all_labels):
            w = DimmSlotWidget(label)
            # Try to match a populated slot to this position
            if i < len(pop_locators):
                real_loc = pop_locators[i]
                w.set_slot(pop_map[real_loc])
            else:
                w.set_slot({})
            self._slot_widgets.append(w)
            self._sticks_layout.addWidget(w)

        self._current_total = total_slots

    # ── public API ──────────────────────────────────────────────────────────
    def update_slots(self, slots_info: List[Dict[str, Any]],
                     total_slots: int = 0) -> None:
        """
        Update from telemetry.

        Args:
            slots_info:  List of populated slot dicts from Win32_PhysicalMemory.
                         Each must have 'locator' (raw DeviceLocator string).
            total_slots: Total physical slots on the board from
                         Win32_PhysicalMemoryArray.MemoryDevices.
                         0 means unknown — infer from populated count.
        """
        populated = [s for s in slots_info if s]

        # Determine total slot count
        if total_slots <= 0:
            n = len(populated)
            # Round up to nearest power of 2 (1→1, 2→2, 3→4, 4→4, ...)
            total_slots = max(n, 1)
            if total_slots > 2:
                total_slots = 4  # most common dual-channel configs are 2 or 4

        # Only rebuild widgets when slot count changes (avoid flicker)
        if total_slots != self._current_total:
            self._rebuild(total_slots, populated)
        else:
            # Just refresh data in existing widgets
            pop_map: Dict[str, Dict[str, Any]] = {}
            for s in populated:
                loc = str(s.get('locator') or '').strip()
                if loc:
                    pop_map[loc] = s
            pop_locators = sorted(pop_map.keys())

            for i, w in enumerate(self._slot_widgets):
                if i < len(pop_locators):
                    w.set_slot(pop_map[pop_locators[i]])
                    w.update_label(_short_locator(pop_locators[i]))
                else:
                    w.set_slot({})

    def set_effective_speed(self, speed_mt: int) -> None:
        self.lbl_eff.setText(f"{speed_mt} MT/s" if speed_mt else '-- MT/s')

    def set_channel_mode(self, mode: str) -> None:
        self.lbl_chan.setText(mode.upper() if mode else 'UNKNOWN')


class MemoryArray(VitreosWinFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="MEMORY_ARRAY", accent_color="purple_dim", parent=parent)
        self._setup_content()

    def _setup_content(self) -> None:
        self.ram_gauge = VitreosCircularGauge(segments=40)
        self.lbl_status = v_label("SEARCHING...", font_size='title', color='text_dim')
        self.lbl_usage  = v_label("0.0 / 0.0 GB", font_size='value_medium', color='purple_dim')

        self.lbl_pct = v_label("0%", font_size='small', color='purple_dim')
        self.mem_bar = VitreosSegmentedBar(segments=24, height=6, color='purple_dim')
        self.dimm_array = DimmArray()

        stats_grid = QGridLayout()
        self.stat_labels: Dict[str, Any] = {}
        for i, (l, k, u, c) in enumerate([
            ('USED',      'used',      'GB', 'purple_dim'),
            ('FREE',      'free',      'GB', 'cyan'),
            ('CACHED',    'cached',    'GB', 'text_secondary'),
            ('AVAILABLE', 'available', 'GB', 'green'),
        ]):
            lbl_val = v_label(f"0 {u}", font_size='value_medium', color=c,
                              align=Qt.AlignmentFlag.AlignCenter)
            w = v_widget(bg='bg_card')
            w.setLayout(v_vbox(margins=6, spacing=2, items=[
                v_label(l, font_size='micro', color='text_darker',
                        align=Qt.AlignmentFlag.AlignCenter), lbl_val]))
            self.stat_labels[k] = lbl_val
            stats_grid.addWidget(w, i // 2, i % 2)

        self.set_content_layout(v_vbox(margins=9, spacing=4, items=[
            v_hbox(spacing=8, items=[
                self.ram_gauge,
                v_vbox(spacing=2, items=[self.lbl_status, self.lbl_usage]),
                'stretch'
            ]),
            v_hbox(items=[v_label("SYSTEM MEMORY", font_size='tiny'), 'stretch', self.lbl_pct]),
            self.mem_bar,
            self.dimm_array,
            stats_grid,
            'stretch'
        ]))

    def update_data(self, data: Dict[str, Any]) -> None:
        u   = data.get('usedGB',  data.get('used',  0))
        tg  = data.get('totalGB', data.get('total', 0))
        pct = data.get('percent', 0)

        self.lbl_status.setText("ONLINE" if tg > 0 else "OFFLINE")
        self.lbl_status.setStyleSheet(
            f"color: {VITREOS_COLORS['green' if tg > 0 else 'text_dim']};")
        self.lbl_usage.setText(f"{u:.1f} / {tg:.1f} GB")
        self.lbl_pct.setText(f"{pct:.0f}%")
        self.mem_bar.set_value(pct, 100)
        self.ram_gauge.set_value(pct, 100, 'purple_dim')

        if 'slots' in data:
            self.dimm_array.update_slots(
                data.get('slots', []),
                total_slots=int(data.get('totalSlots', 0))
            )
            self.dimm_array.set_effective_speed(int(data.get('effectiveSpeed', 0)))
            self.dimm_array.set_channel_mode(str(data.get('channel', 'UNKNOWN')))

        free = tg - u
        self.stat_labels['used'].setText(f"{u:.1f} GB")
        self.stat_labels['free'].setText(f"{free:.1f} GB")
        self.stat_labels['cached'].setText(f"{data.get('cachedGB', 0):.1f} GB")
        self.stat_labels['available'].setText(f"{data.get('availableGB', free):.1f} GB")
