from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath

from ..vitreos_theme import VITREOS_COLORS, get_color, get_font, FONT_SIZES
from ..vitreos_widgets import VitreosWinFrame, VitreosSegmentedBar, apply_phosphor_glow
from ..factory import v_vbox, v_hbox, v_label, v_widget

import math

class VitreosNetworkGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.segments_x = 45
        self.segments_y = 10
        self.gap = 2
        self.target_history = [0.0] * self.segments_x
        self.display_history = [0.0] * self.segments_x
        self.max_history_value = 1.0  # Initial max to avoid div by zero
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_frame)
        self.timer.start(30)
        
    def add_data_point(self, value: float):
        self.target_history.pop(0)
        self.target_history.append(value)
        
        # Shift display history as well so it scrolls instantly, then smoothly adjusts
        self.display_history.pop(0)
        self.display_history.append(self.display_history[-1])
        
    def animate_frame(self):
        changed = False
        for i in range(self.segments_x):
            diff = self.target_history[i] - self.display_history[i]
            if abs(diff) > 0.001:
                self.display_history[i] += diff * 0.25
                changed = True
                
        # Dynamically scale the graph based on recent maximums
        current_max = max(self.target_history)
        if current_max > self.max_history_value:
            self.max_history_value = current_max
        elif current_max < self.max_history_value * 0.5:
            # Gradually decay the max value if usage drops
            self.max_history_value = max(1.0, self.max_history_value * 0.95)
            changed = True
            
        if changed:
            self.update()
        
    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        w = self.width()
        h = self.height()
        
        # Border box
        painter.setPen(get_color('border_secondary'))
        painter.drawRect(0, 0, w - 1, h - 1)
        
        # Inner padding
        pad = 6
        draw_w = w - pad * 2
        draw_h = h - pad * 2
        
        seg_w = (draw_w - (self.segments_x - 1) * self.gap) / self.segments_x
        seg_h = (draw_h - (self.segments_y - 1) * self.gap) / self.segments_y
        
        points = []
        
        # 1. Draw the blocks
        for i in range(self.segments_x):
            x = pad + i * (seg_w + self.gap)
            val = self.display_history[i]
            
            norm_val = val / self.max_history_value if self.max_history_value > 0 else 0
            # Clamp for safety
            norm_val = max(0.0, min(1.0, norm_val))
            
            # Calculate top center for the continuous line
            top_y = pad + draw_h - (norm_val * draw_h)
            cx = x + seg_w / 2
            points.append((cx, top_y))
            
            filled_y = int(norm_val * self.segments_y)
            if val > 0 and filled_y == 0:
                filled_y = 1
            
            for j in range(filled_y):
                y = pad + draw_h - (j + 1) * (seg_h + self.gap) + self.gap
                rect = QRectF(x, y, seg_w, seg_h)
                
                intensity = int(100 + 155 * (j / self.segments_y))
                color = get_color('primary_purple', intensity)
                painter.fillRect(rect, color)
                
        # 2. Draw the smooth continuous line on top
        if len(points) > 1:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            path = QPainterPath()
            path.moveTo(points[0][0], points[0][1])
            
            # Create cubic bezier curve for smoothness
            for i in range(1, len(points)):
                p1 = points[i-1]
                p2 = points[i]
                
                # Control points for horizontal easing
                cp1_x = p1[0] + (p2[0] - p1[0]) / 2
                cp1_y = p1[1]
                cp2_x = p1[0] + (p2[0] - p1[0]) / 2
                cp2_y = p2[1]
                
                path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, p2[0], p2[1])
                
            pen = QPen(get_color('purple_glow'), 2)
            # Add a slight blur/glow effect to the pen by drawing it twice (alpha blending)
            glow_pen = QPen(get_color('primary_purple', 100), 4)
            painter.setPen(glow_pen)
            painter.drawPath(path)
            
            painter.setPen(pen)
            painter.drawPath(path)

class NetInterface(VitreosWinFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="NET_INTERFACE", accent_color="green", parent=parent)
        self._setup_content()
    
    def _setup_content(self) -> None:
        # TOP BUTTONS
        self.btn_eth = QLabel(" ஃ ETH")
        self.btn_eth.setFont(get_font('mono', FONT_SIZES['small']))
        self.btn_eth.setStyleSheet(f"""
            color: {VITREOS_COLORS['green']};
            border: 1px solid {VITREOS_COLORS['green']};
            padding: 4px 12px;
        """)
        apply_phosphor_glow(self.btn_eth, 'green', 6.0)
        
        self.btn_vpn = QLabel(" 🔒 VPN")
        self.btn_vpn.setFont(get_font('mono', FONT_SIZES['small']))
        self.btn_vpn.setStyleSheet(f"""
            color: {VITREOS_COLORS['text_secondary']};
            border: 1px solid {VITREOS_COLORS['border_secondary']};
            padding: 4px 12px;
        """)
        
        top_btns = v_hbox(spacing=12, items=[self.btn_eth, self.btn_vpn, 'stretch'])
        
        # STATUS
        self.lbl_title = v_label("NETWORK I/O", font_size='value_large', color='text_primary')
        self.lbl_title.setStyleSheet("letter-spacing: 2px;")
        
        self.conn_dot = QLabel("■")
        self.conn_dot.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        self.conn_dot.setFont(get_font('mono', FONT_SIZES['micro']))
        self.conn_text = v_label("Connected", font_size='small', color='green')
        
        status_row = v_hbox(items=[self.lbl_title, 'stretch', self.conn_dot, self.conn_text])
        self.lbl_nic = v_label("Intel i225-V - 2.5Gb/s", font_size='small', color='text_secondary')
        
        # GRAPH
        self.graph = VitreosNetworkGraph()
        
        # DL / UL PANELS
        self.dl_val_lbl = QLabel("951.8")
        self.dl_val_lbl.setFont(get_font('display', 32))
        self.dl_val_lbl.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']}; border: none;")
        apply_phosphor_glow(self.dl_val_lbl, 'primary_purple')
        
        dl_unit = v_label("Mb/s", font_size='small', color='purple_dim')
        dl_unit.setStyleSheet("border: none; padding-top: 14px;")
        
        dl_val_box = QWidget()
        dl_val_box.setStyleSheet("border: none;")
        dl_val_box.setLayout(v_hbox(margins=0, spacing=4, items=[self.dl_val_lbl, dl_unit, 'stretch']))
        
        self.dl_bar = VitreosSegmentedBar(segments=14, height=4, color='primary_purple')
        self.dl_bar.alert_threshold = 0.8
        
        dl_panel = QWidget()
        dl_panel.setStyleSheet(f"border: 1px solid {VITREOS_COLORS['border_secondary']};")
        dl_lbl = v_label("↓ DOWNLOAD", font_size='tiny', color='text_secondary')
        dl_lbl.setStyleSheet("border: none;")
        dl_panel.setLayout(v_vbox(margins=10, spacing=4, items=[dl_lbl, dl_val_box, self.dl_bar]))
        
        self.ul_val_lbl = QLabel("104.9")
        self.ul_val_lbl.setFont(get_font('display', 32))
        self.ul_val_lbl.setStyleSheet(f"color: {VITREOS_COLORS['cyan']}; border: none;")
        apply_phosphor_glow(self.ul_val_lbl, 'cyan')
        
        ul_unit = v_label("Mb/s", font_size='small', color='cyan')
        ul_unit.setStyleSheet("border: none; padding-top: 14px; opacity: 0.5;")
        
        ul_val_box = QWidget()
        ul_val_box.setStyleSheet("border: none;")
        ul_val_box.setLayout(v_hbox(margins=0, spacing=4, items=[self.ul_val_lbl, ul_unit, 'stretch']))
        
        self.ul_bar = VitreosSegmentedBar(segments=14, height=4, color='cyan')
        self.ul_bar.alert_threshold = 1.0 # Never warn for upload usually in this UI
        
        ul_panel = QWidget()
        ul_panel.setStyleSheet(f"border: 1px solid {VITREOS_COLORS['border_secondary']};")
        ul_lbl = v_label("↑ UPLOAD", font_size='tiny', color='text_secondary')
        ul_lbl.setStyleSheet("border: none;")
        ul_panel.setLayout(v_vbox(margins=10, spacing=4, items=[ul_lbl, ul_val_box, self.ul_bar]))
        
        dl_ul_row = v_hbox(margins=0, spacing=12, items=[dl_panel, ul_panel])
        
        # BOTTOM STATS
        def create_stat_panel(title, val_text):
            p = QWidget()
            p.setStyleSheet(f"border: 1px solid {VITREOS_COLORS['border_secondary']};")
            l1 = v_label(title, font_size='micro', color='text_secondary', align=Qt.AlignmentFlag.AlignCenter)
            l1.setStyleSheet("border: none; letter-spacing: 1px;")
            l2 = v_label(val_text, font_size='value_large', color='primary_purple', align=Qt.AlignmentFlag.AlignCenter)
            l2.setStyleSheet("border: none;")
            apply_phosphor_glow(l2, 'primary_purple', 4.0)
            p.setLayout(v_vbox(margins=8, spacing=4, items=[l1, l2]))
            return p, l2
            
        p_lat, self.stat_lat = create_stat_panel("LATENCY", "4ms")
        p_loss, self.stat_loss = create_stat_panel("PACKET LOSS", "0.00%")
        p_speed, self.stat_speed = create_stat_panel("LINE SPEED", "2.5 Gb/s")
        
        bottom_row = v_hbox(margins=0, spacing=12, items=[p_lat, p_loss, p_speed])
        
        # ASSEMBLE
        layout = v_vbox(margins=16, spacing=16, items=[
            top_btns,
            v_vbox(margins=0, spacing=2, items=[status_row, self.lbl_nic]),
            self.graph,
            dl_ul_row,
            bottom_row,
            'stretch'
        ])
        self.set_content_layout(layout)
        
    def update_data(self, data: Dict[str, Any]) -> None:
        primary_nic = data.get('primaryNic', 'Unknown')
        if primary_nic != 'Unknown':
            self.lbl_nic.setText(f"{primary_nic}")
            self.conn_text.setText("Connected")
            self.conn_text.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
            self.conn_dot.setStyleSheet(f"color: {VITREOS_COLORS['green']};")
        else:
            self.lbl_nic.setText("NO ADAPTER FOUND")
            self.conn_text.setText("Offline")
            self.conn_text.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
            self.conn_dot.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        
        dl = data.get('downloadMbps', 0)
        ul = data.get('uploadMbps', 0)
        lat = data.get('latency', 0)
        
        # Update the graph with total throughput
        self.graph.add_data_point(dl + ul)
        
        # Assuming typical 1Gbps maximums for scaling the bars visually
        # If user has a 2.5Gbps, we could scale to 2500
        max_speed = 1000.0
        
        self.dl_val_lbl.setText(f"{dl:.1f}")
        self.ul_val_lbl.setText(f"{ul:.1f}")
        self.dl_bar.set_value(dl, max_speed)
        self.ul_bar.set_value(ul, max_speed)
        
        if lat >= 100:
            self.stat_lat.setText(f"⚠ {lat:.0f}ms")
            self.stat_lat.setStyleSheet(f"color: {VITREOS_COLORS['warning_orange']}; border: none;")
            apply_phosphor_glow(self.stat_lat, 'warning_orange', 4.0)
        else:
            self.stat_lat.setText(f"{lat:.0f}ms")
            self.stat_lat.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']}; border: none;")
            apply_phosphor_glow(self.stat_lat, 'primary_purple', 4.0)
            
        loss = data.get('packetLoss', 0)
        if loss > 0:
            self.stat_loss.setText(f"⚠ {loss:.2f}%")
            self.stat_loss.setStyleSheet(f"color: {VITREOS_COLORS['critical_red']}; border: none;")
            apply_phosphor_glow(self.stat_loss, 'critical_red', 4.0)
        else:
            self.stat_loss.setText(f"{loss:.2f}%")
            self.stat_loss.setStyleSheet(f"color: {VITREOS_COLORS['primary_purple']}; border: none;")
            apply_phosphor_glow(self.stat_loss, 'primary_purple', 4.0)
        self.stat_speed.setText(f"{data.get('linkSpeed', '2.5 Gb/s')}")

