from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import QWidget, QGridLayout, QFrame
from PyQt6.QtCore import Qt
from ..vitreos_theme import VITREOS_COLORS
from ..vitreos_widgets import VitreosWinFrame, VitreosSegmentedBar, VitreosCircularGauge
from ..factory import v_vbox, v_hbox, v_label, v_widget

class DimmSlotWidget(QWidget):
    def __init__(self, slot_id: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.slot_id = slot_id
        self.capacity_gb = 0.0
        
        self.stick = QFrame()
        self.stick.setFixedSize(48, 120)
        self.stick.setStyleSheet(self._empty_style())
        
        self.lbl_slot = v_label(self.slot_id, font_size='micro', color='text_darker', align=Qt.AlignmentFlag.AlignCenter)
        self.lbl_cap = v_label("EMPTY", font_size='tiny', color='text_secondary', align=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(v_vbox(margins=4, spacing=4, items=[self.stick, self.lbl_slot, self.lbl_cap]))
        self.layout().setAlignment(self.stick, Qt.AlignmentFlag.AlignCenter)

    def _empty_style(self): return f"background: transparent; border: 2px dashed {VITREOS_COLORS['border_secondary']}; border-radius:4px;"
    def _populated_style(self): return f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {VITREOS_COLORS['primary_purple']}, stop:1 {VITREOS_COLORS['purple_dim']}); border: 1px solid {VITREOS_COLORS['border_primary']}; border-radius:4px;"

    def set_slot(self, info: Dict[str, Any]) -> None:
        try: self.capacity_gb = float(info.get('capacityGB', info.get('capacity')))
        except: self.capacity_gb = 0.0
        
        if self.capacity_gb > 0:
            self.stick.setStyleSheet(self._populated_style())
            self.lbl_cap.setText(f"{int(self.capacity_gb)} GB")
            self.lbl_cap.setStyleSheet(f"color: {VITREOS_COLORS['purple_dim']};")
        else:
            self.stick.setStyleSheet(self._empty_style())
            self.lbl_cap.setText('EMPTY')
            self.lbl_cap.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")

class DimmArray(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.order = ['A1', 'A2', 'B1', 'B2']
        self.slots = {loc: DimmSlotWidget(loc) for loc in self.order}
        
        self.lbl_eff = v_label('-- MT/s', font_size='value_medium', color='purple_dim')
        w_eff = v_widget(bg='bg_card')
        w_eff.setLayout(v_vbox(margins=6, spacing=6, items=[v_label('EFFECTIVE SPEED', font_size='micro', color='text_darker'), self.lbl_eff]))
        
        self.lbl_chan = v_label('UNKNOWN', font_size='value_medium', color='cyan')
        w_chan = v_widget(bg='bg_card')
        w_chan.setLayout(v_vbox(margins=6, spacing=6, items=[v_label('CHANNEL MODE', font_size='micro', color='text_darker'), self.lbl_chan]))
        
        self.setLayout(v_vbox(margins=6, spacing=6, items=[
            v_hbox(spacing=12, items=list(self.slots.values())),
            v_hbox(spacing=8, items=[w_eff, w_chan])
        ]))

    def update_slots(self, slots_info: List[Dict[str, Any]]) -> None:
        if not slots_info:
            for k in self.order: self.slots[k].set_slot({})
            return
            
        mappings = {}
        for s in slots_info:
            loc = str(s.get('locator', s.get('DeviceLocator', ''))).upper()
            for k in self.order:
                if k in loc:
                    mappings[k] = s
                    break
        for k in self.order:
            self.slots[k].set_slot(mappings.get(k, {}))

    def set_effective_speed(self, speed_mt: int) -> None: self.lbl_eff.setText(f"{speed_mt} MT/s" if speed_mt else '-- MT/s')
    def set_channel_mode(self, mode: str) -> None: self.lbl_chan.setText(mode.upper() if mode else 'UNKNOWN')

class MemoryArray(VitreosWinFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="MEMORY_ARRAY", accent_color="purple_dim", parent=parent)
        self._setup_content()
    
    def _setup_content(self) -> None:
        self.ram_gauge = VitreosCircularGauge(segments=40)
        self.lbl_status = v_label("SEARCHING...", font_size='title', color='text_dim')
        self.lbl_usage = v_label("0.0 / 0.0 GB", font_size='value_medium', color='purple_dim')
        
        self.lbl_pct = v_label("0%", font_size='small', color='purple_dim')
        self.mem_bar = VitreosSegmentedBar(segments=24, height=6, color='purple_dim')
        self.dimm_array = DimmArray()
        
        stats_grid = QGridLayout()
        self.stat_labels = {}
        for i, (l, k, u, c) in enumerate([('USED', 'used', 'GB', 'purple_dim'), ('FREE', 'free', 'GB', 'cyan'), ('CACHED', 'cached', 'GB', 'text_secondary'), ('AVAILABLE', 'available', 'GB', 'green')]):
            lbl_val = v_label(f"0 {u}", font_size='value_medium', color=c, align=Qt.AlignmentFlag.AlignCenter)
            w = v_widget(bg='bg_card')
            w.setLayout(v_vbox(margins=6, spacing=2, items=[v_label(l, font_size='micro', color='text_darker', align=Qt.AlignmentFlag.AlignCenter), lbl_val]))
            self.stat_labels[k] = lbl_val
            stats_grid.addWidget(w, i // 2, i % 2)
            
        self.set_content_layout(v_vbox(margins=9, spacing=4, items=[
            v_hbox(spacing=8, items=[self.ram_gauge, v_vbox(spacing=2, items=[self.lbl_status, self.lbl_usage]), 'stretch']),
            v_hbox(items=[v_label("SYSTEM MEMORY", font_size='tiny'), 'stretch', self.lbl_pct]), self.mem_bar,
            self.dimm_array, stats_grid, 'stretch'
        ]))
        
    def update_data(self, data: Dict[str, Any]) -> None:
        u = data.get('usedGB', data.get('used', 0))
        tg = data.get('totalGB', data.get('total', 0))
        pct = data.get('percent', 0)
        
        self.lbl_status.setText("ONLINE" if tg > 0 else "OFFLINE")
        self.lbl_status.setStyleSheet(f"color: {VITREOS_COLORS['green' if tg > 0 else 'text_dim']};")
        self.lbl_usage.setText(f"{u:.1f} / {tg:.1f} GB")
        self.lbl_pct.setText(f"{pct:.0f}%")
        self.mem_bar.set_value(pct, 100)
        self.ram_gauge.set_value(pct, 100, 'purple_dim')
        
        if 'slots' in data:
            self.dimm_array.update_slots(data.get('slots', []))
            self.dimm_array.set_effective_speed(int(data.get('effectiveSpeed', 0)))
            self.dimm_array.set_channel_mode(str(data.get('channel', 'UNKNOWN')))
            
        free = tg - u
        self.stat_labels['used'].setText(f"{u:.1f} GB")
        self.stat_labels['free'].setText(f"{free:.1f} GB")
        self.stat_labels['cached'].setText(f"{data.get('cachedGB', 0):.1f} GB")
        self.stat_labels['available'].setText(f"{data.get('availableGB', free):.1f} GB")
