import math
import json
import os
from typing import List, Tuple
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QPolygonF, QPixmap
from PyQt6.QtCore import Qt, QTimer, QPointF, QSize

# Load GeoJSON geometries
GEOJSON_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "world.geojson")

def load_geojson_polygons() -> List[List[Tuple[float, float]]]:
    if not os.path.exists(GEOJSON_FILE):
        return []
        
    try:
        with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        polygons = []
        for feature in data.get("features", []):
            geom = feature.get("geometry", {})
            if not geom:
                continue
                
            geom_type = geom.get("type")
            coords = geom.get("coordinates", [])
            
            if geom_type == "Polygon":
                for ring in coords:
                    polygons.append([(pt[0], pt[1]) for pt in ring])
            elif geom_type == "MultiPolygon":
                for poly in coords:
                    for ring in poly:
                        polygons.append([(pt[0], pt[1]) for pt in ring])
        return polygons
    except Exception as e:
        print(f"Error loading GeoJSON: {e}")
        return []

THREAT_SOURCES = [
    {"lat": 55.75, "lon": 37.61, "color": "#FF00AA"},  # Malicious
    {"lat": 39.90, "lon": 116.40, "color": "#FF00AA"}, # Malicious
    {"lat": -23.55, "lon": -46.63, "color": "#00FF00"}, # Safe
    {"lat": 51.50, "lon": -0.12, "color": "#00FF00"},  # Safe
    {"lat": 35.68, "lon": 139.76, "color": "#FF00AA"}, # Malicious
    {"lat": -33.86, "lon": 151.20, "color": "#00FF00"}, # Safe
]

HOST_LAT = 33.91
HOST_LON = -81.26

class GeoThreatMap(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 300)
        
        # Parse GeoJSON into list of lon/lat rings
        self.geo_polygons = load_geojson_polygons()
        
        # Off-screen surface for the static map
        self.map_surface = None
        self.last_size = QSize()
        
        # Animation state
        self.tick = 0
        self.packet_progress = 0.0
        
        # Main update loop. 800ms cycle for pulse -> 50ms tick (16 ticks)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)

    def update_animation(self):
        self.tick += 1
        
        # Packet travels from 0.0 to 1.0 taking 2 seconds (40 ticks @ 50ms)
        self.packet_progress += 0.025
        if self.packet_progress > 1.0:
            self.packet_progress = 0.0
            
        self.update()

    def lat_lon_to_xy(self, lat: float, lon: float, w: int, h: int) -> QPointF:
        """Map global coords to widget dimensions."""
        # Equirectangular projection
        x = (lon + 180.0) / 360.0 * w
        y = (90.0 - lat) / 180.0 * h
        return QPointF(x, y)

    def render_map_surface(self, w: int, h: int):
        """Render the background grid and GeoJSON polygons to an off-screen surface."""
        self.map_surface = QPixmap(w, h)
        self.map_surface.fill(QColor("#121212"))
        
        painter = QPainter(self.map_surface)
        
        # 1. Grid
        painter.setPen(QPen(QColor("#1A1A1A"), 1))
        for i in range(24):
            x = int(i * w / 24)
            painter.drawLine(x, 0, x, h)
        for i in range(12):
            y = int(i * h / 12)
            painter.drawLine(0, y, w, y)
            
        # 2. GeoJSON Polygons
        painter.setPen(QPen(QColor("#333333"), 1))
        painter.setBrush(QBrush(QColor("#1A1A1A")))
        
        for poly_coords in self.geo_polygons:
            polygon = QPolygonF()
            for lon, lat in poly_coords:
                polygon.append(self.lat_lon_to_xy(lat, lon, w, h))
            painter.drawPolygon(polygon)
            
        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        # Regenerate the map surface if size changes
        if self.last_size != QSize(w, h):
            self.render_map_surface(w, h)
            self.last_size = QSize(w, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        
        # 1. Draw Cached Map Surface
        if self.map_surface and not self.map_surface.isNull():
            painter.drawPixmap(0, 0, self.map_surface)
        else:
            painter.fillRect(0, 0, w, h, QColor("#121212"))
            
        # 2. Host Marker
        host_pos = self.lat_lon_to_xy(HOST_LAT, HOST_LON, w, h)
        
        # Stepped Pulse Effect (3 sizes cycling every 800ms)
        cycle = self.tick % 16
        if cycle < 5:
            radius = 4
        elif cycle < 10:
            radius = 8
        else:
            radius = 12
            
        painter.setPen(QPen(QColor("#8800FF"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(host_pos, radius, radius)
        
        # Host crosshair
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.drawLine(QPointF(host_pos.x() - 4, host_pos.y()), QPointF(host_pos.x() + 4, host_pos.y()))
        painter.drawLine(QPointF(host_pos.x(), host_pos.y() - 4), QPointF(host_pos.x(), host_pos.y() + 4))
        
        # 3. Threat Arcs (Mock State)
        t_stepped = math.floor(self.packet_progress * 10) / 10.0
        
        for idx, threat in enumerate(THREAT_SOURCES):
            # Offset animation so they stagger
            t_local = (t_stepped + idx * 0.15) % 1.0
            t_local = math.floor(t_local * 10) / 10.0
            
            src_pos = self.lat_lon_to_xy(threat["lat"], threat["lon"], w, h)
            color = QColor(threat["color"])
            
            # Quadratic Bezier
            path = QPainterPath()
            path.moveTo(src_pos)
            
            ctrl_x = (src_pos.x() + host_pos.x()) / 2
            ctrl_y = min(src_pos.y(), host_pos.y()) - h * 0.2
            ctrl_pos = QPointF(ctrl_x, ctrl_y)
            
            path.quadTo(ctrl_pos, host_pos)
            
            # Draw arc
            painter.setPen(QPen(color, 1, Qt.PenStyle.DotLine))
            painter.drawPath(path)
            
            # Packet
            u = 1.0 - t_local
            px = u*u*src_pos.x() + 2*u*t_local*ctrl_pos.x() + t_local*t_local*host_pos.x()
            py = u*u*src_pos.y() + 2*u*t_local*ctrl_pos.y() + t_local*t_local*host_pos.y()
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRect(int(px - 1), int(py - 1), 2, 2)
            
            # 4. Endpoints "glitch" 2-frame pulse ring when packet arrives (t >= 0.9)
            if t_local >= 0.9:
                glitch_radius = 6 if (self.tick % 2) == 0 else 10
                painter.setPen(QPen(color, 1))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(host_pos, glitch_radius, glitch_radius)

