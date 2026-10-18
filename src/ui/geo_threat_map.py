"""
Geo Threat Map - Tactical Global Coordinate Projection
V4 Vanguard Edition with strict QPainter brush isolation and anti-aliased vector arcs.
"""

import json
import math
import os
from typing import List, Tuple, Dict, Any
from pathlib import Path

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QPolygonF, QPixmap
from PyQt6.QtCore import Qt, QTimer, QPointF, QSize

from src.core.paths import get_bundle_dir


def load_geojson_polygons() -> List[List[Tuple[float, float]]]:
    """Load world map boundary polygons from bundled world.geojson."""
    geojson_path = get_bundle_dir() / "assets" / "world.geojson"
    if not geojson_path.exists():
        return []
        
    try:
        with open(geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        polygons: List[List[Tuple[float, float]]] = []
        for feature in data.get("features", []):
            geom = feature.get("geometry", {})
            if not geom:
                continue
                
            geom_type = geom.get("type")
            coords = geom.get("coordinates", [])
            
            if geom_type == "Polygon":
                for ring in coords:
                    polygons.append([(float(pt[0]), float(pt[1])) for pt in ring])
            elif geom_type == "MultiPolygon":
                for poly in coords:
                    for ring in poly:
                        polygons.append([(float(pt[0]), float(pt[1])) for pt in ring])
        return polygons
    except Exception as e:
        print(f"[GEO_MAP] Error loading GeoJSON: {e}")
        return []


# Tactical Threat Sources (#22C55E = Safe/Low, #06B6D4/#A855F7 = Active, #EF4444 = High)
THREAT_SOURCES: List[Dict[str, Any]] = [
    {"lat": 55.75, "lon": 37.61, "color": "#EF4444", "level": "HIGH"},     # Moscow
    {"lat": 39.90, "lon": 116.40, "color": "#EF4444", "level": "HIGH"},    # Beijing
    {"lat": -23.55, "lon": -46.63, "color": "#22C55E", "level": "LOW"},    # Sao Paulo
    {"lat": 51.50, "lon": -0.12, "color": "#22C55E", "level": "LOW"},      # London
    {"lat": 35.68, "lon": 139.76, "color": "#06B6D4", "level": "ACTIVE"},  # Tokyo
    {"lat": -33.86, "lon": 151.20, "color": "#A855F7", "level": "ACTIVE"}, # Sydney
]

HOST_LAT = 33.91
HOST_LON = -81.26


class GeoThreatMap(QWidget):
    """
    Tactical Equirectangular Threat Map
    Renders live animated telemetry trajectory arcs with strict NoBrush path isolation.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(400, 220)
        
        # Parse GeoJSON into list of lon/lat rings
        self.geo_polygons = load_geojson_polygons()
        
        # Off-screen surface for the static map
        self.map_surface: QPixmap | None = None
        self.last_size = QSize()
        
        # Animation state
        self.tick = 0
        self.packet_progress = 0.0
        
        # Main update loop (50ms tick = ~20 FPS vector cycle)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)

    def update_animation(self) -> None:
        self.tick += 1
        
        # Packet travels from 0.0 to 1.0
        self.packet_progress += 0.025
        if self.packet_progress > 1.0:
            self.packet_progress = 0.0
            
        self.update()

    def lat_lon_to_xy(self, lat: float, lon: float, w: int, h: int) -> QPointF:
        """Map global coords to widget dimensions using Equirectangular projection."""
        x = (lon + 180.0) / 360.0 * w
        y = (90.0 - lat) / 180.0 * h
        return QPointF(x, y)

    def render_map_surface(self, w: int, h: int) -> None:
        """Render background grid and GeoJSON landmasses to off-screen pixmap."""
        pixmap = QPixmap(w, h)
        pixmap.fill(QColor("#0D0E12"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Coordinate Grid
        painter.setPen(QPen(QColor("#1A1D24"), 1))
        for i in range(24):
            x = int(i * w / 24)
            painter.drawLine(x, 0, x, h)
        for i in range(12):
            y = int(i * h / 12)
            painter.drawLine(0, y, w, y)
            
        # 2. GeoJSON Landmasses
        painter.setPen(QPen(QColor("#242A35"), 1))
        painter.setBrush(QBrush(QColor("#131720")))
        
        for poly_coords in self.geo_polygons:
            polygon = QPolygonF()
            for lon, lat in poly_coords:
                polygon.append(self.lat_lon_to_xy(lat, lon, w, h))
            painter.drawPolygon(polygon)
            
        painter.end()
        self.map_surface = pixmap

    def resizeEvent(self, a0: Any) -> None:
        super().resizeEvent(a0)
        w = self.width()
        h = self.height()
        if self.last_size != QSize(w, h):
            self.render_map_surface(w, h)
            self.last_size = QSize(w, h)

    def paintEvent(self, a0: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        
        # 1. Background Surface
        if self.map_surface and not self.map_surface.isNull():
            painter.drawPixmap(0, 0, self.map_surface)
        else:
            painter.fillRect(0, 0, w, h, QColor("#0D0E12"))
            
        # 2. Host Marker (Pulsing Center Target)
        host_pos = self.lat_lon_to_xy(HOST_LAT, HOST_LON, w, h)
        
        painter.save()
        cycle = self.tick % 16
        if cycle < 5:
            radius = 4
        elif cycle < 10:
            radius = 7
        else:
            radius = 11
            
        # Radar Pulse Ring
        pulse_color = QColor("#A855F7")
        pulse_color.setAlpha(180)
        painter.setPen(QPen(pulse_color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(host_pos, radius, radius)
        
        # Center Target Point
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(host_pos, 2, 2)
        
        # Crosshair lines
        painter.setPen(QPen(QColor("#C084FC"), 1))
        painter.drawLine(QPointF(host_pos.x() - 6, host_pos.y()), QPointF(host_pos.x() + 6, host_pos.y()))
        painter.drawLine(QPointF(host_pos.x(), host_pos.y() - 6), QPointF(host_pos.x(), host_pos.y() + 6))
        painter.restore()
        
        # 3. Vector Trajectory Arcs
        t_stepped = math.floor(self.packet_progress * 10) / 10.0
        
        for idx, threat in enumerate(THREAT_SOURCES):
            painter.save()
            
            t_local = (t_stepped + idx * 0.15) % 1.0
            t_local = math.floor(t_local * 10) / 10.0
            
            src_pos = self.lat_lon_to_xy(threat["lat"], threat["lon"], w, h)
            color = QColor(threat["color"])
            
            # Bezier control point
            ctrl_x = (src_pos.x() + host_pos.x()) / 2.0
            ctrl_y = min(src_pos.y(), host_pos.y()) - h * 0.22
            ctrl_pos = QPointF(ctrl_x, ctrl_y)
            
            path = QPainterPath()
            path.moveTo(src_pos)
            path.quadTo(ctrl_pos, host_pos)
            
            # CRITICAL GUARD: Ensure brush is strictly NoBrush before drawing path
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            # Pass 1: Subtle Outer Glow Path (width=3.0, alpha=40)
            glow_color = QColor(color)
            glow_color.setAlpha(40)
            glow_pen = QPen(glow_color, 3.0, Qt.PenStyle.SolidLine)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(glow_pen)
            painter.drawPath(path)
            
            # Pass 2: Crisp 1.5px Core Vector Line
            pen_style = Qt.PenStyle.DashLine if threat.get("level") == "HIGH" else Qt.PenStyle.SolidLine
            core_pen = QPen(color, 1.5, pen_style)
            core_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(core_pen)
            painter.drawPath(path)
            
            # Origin Target Reticle (Source)
            painter.setPen(QPen(color, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(src_pos, 3, 3)
            
            # Packet Marker (Moving Along Arc)
            u = 1.0 - t_local
            px = u * u * src_pos.x() + 2 * u * t_local * ctrl_pos.x() + t_local * t_local * host_pos.x()
            py = u * u * src_pos.y() + 2 * u * t_local * ctrl_pos.y() + t_local * t_local * host_pos.y()
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(px, py), 2.5, 2.5)
            
            # Impact Reticle Glow on Host Arrival
            if t_local >= 0.9:
                impact_radius = 6 if (self.tick % 2) == 0 else 10
                impact_color = QColor(color)
                impact_color.setAlpha(160)
                painter.setPen(QPen(impact_color, 1.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(host_pos, impact_radius, impact_radius)
                
            painter.restore()
