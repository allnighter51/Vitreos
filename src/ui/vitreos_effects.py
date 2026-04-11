"""
CRT Post-Processing Overlay
Optimized Scanlines and Film Grain for Solid State Y2K Aesthetic
"""

from collections import deque
from typing import Optional, Deque, Tuple
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint, QEvent

from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QBrush, QPolygon, QCursor, QPainterPath
from src.ui.vitreos_theme import VITREOS_COLORS

import random
import time


class CRTOverlay(QWidget):
    """Optimized CRT post-processing overlay with cached scanlines."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Make overlay transparent to mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Cached scanline pixmap
        self.scanline_pixmap: Optional[QPixmap] = None
        
        # Film grain animation (reduced frequency)
        self.grain_offset = 0
        self.grain_timer = QTimer(self)
        self.grain_timer.timeout.connect(self._animate_grain)
        self.grain_timer.start(100)  # Reduced to 10 FPS
    
    def _generate_scanline_pixmap(self) -> None:
        """Generate static scanline pixmap (called once)."""
        width = self.width()
        height = self.height()
        
        self.scanline_pixmap = QPixmap(width, height)
        self.scanline_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(self.scanline_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        # Draw scanlines
        scanline_color = QColor(0, 0, 0, 20)  # Increased opacity for solid state
        pen = QPen(scanline_color)
        painter.setPen(pen)
        
        y = 0
        while y < height:
            painter.drawLine(0, y, width, y)
            y += 4
        
        painter.end()
    
    def _animate_grain(self) -> None:
        """Animate film grain (reduced frequency)."""
        self.grain_offset = (self.grain_offset + 1) % 100
        self.update()
    
    def resizeEvent(self, event) -> None:
        """Regenerate scanline pixmap on resize."""
        super().resizeEvent(event)
        self.scanline_pixmap = None  # Force regeneration
    
    def paintEvent(self, event) -> None:
        """Draw optimized CRT effects."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        width = self.width()
        height = self.height()
        
        # Draw cached scanlines
        if self.scanline_pixmap is None or self.scanline_pixmap.size() != self.size():
            self._generate_scanline_pixmap()
        
        if self.scanline_pixmap:
            painter.drawPixmap(0, 0, self.scanline_pixmap)
        
        # Film grain (reduced density)
        random.seed(self.grain_offset)
        grain_color = QColor(255, 255, 255, 12)  # Increased opacity
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grain_color)
        
        # Reduced grain density for performance
        for _ in range(width * height // 4000):  # Half the original density
            x = random.randint(0, width)
            y = random.randint(0, height)
            painter.drawRect(x, y, 1, 1)


class GlitchTransition(QWidget):
    """Glitch effect for tab transitions."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setVisible(False)
        
        self.glitch_active = False
        self.glitch_frame = 0
    
    def trigger_glitch(self) -> None:
        """Trigger 150ms glitch effect."""
        self.glitch_active = True
        self.glitch_frame = 0
        self.setVisible(True)
        
        # Auto-hide after 150ms
        QTimer.singleShot(150, self._end_glitch)
        
        # Animate glitch
        self.glitch_timer = QTimer(self)
        self.glitch_timer.timeout.connect(self._animate_glitch)
        self.glitch_timer.start(30)  # 5 frames over 150ms
    
    def _animate_glitch(self) -> None:
        """Animate glitch frames."""
        self.glitch_frame += 1
        self.update()
        
        if self.glitch_frame >= 5:
            self.glitch_timer.stop()
    
    def _end_glitch(self) -> None:
        """End glitch effect."""
        self.glitch_active = False
        self.setVisible(False)
    
    def paintEvent(self, event) -> None:
        """Draw glitch effect."""
        if not self.glitch_active:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        width = self.width()
        height = self.height()
        
        # Chromatic aberration (red/blue shift)
        if self.glitch_frame % 2 == 0:
            # Red shift
            painter.fillRect(0, 0, width, height, QColor(255, 0, 0, 20))
        else:
            # Blue shift
            painter.fillRect(0, 0, width, height, QColor(0, 0, 255, 20))
        
        # Horizontal displacement lines
        random.seed(self.glitch_frame)
        for _ in range(5):
            y = random.randint(0, height)
            line_height = random.randint(2, 10)
            offset = random.randint(-5, 5)
            
            painter.fillRect(offset, y, width, line_height, QColor(0, 0, 0, 100))


__all__ = ['CRTOverlay', 'GlitchTransition']

