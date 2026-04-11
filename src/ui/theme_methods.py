"""Theme methods for Vitreos settings tab"""

import logging

logger = logging.getLogger(__name__)

class ThemeMethods:
    """Mixin class for theme-related methods"""
    
    def on_theme_slider_changed(self, value: int) -> None:
        """Handle theme color slider changes"""
        self.theme_label.setText(f"[ACCENT_HUE: {value}°]")
        self.update_theme_color(value)
    
    def update_theme_color(self, hue_value: int) -> None:
        """Update application theme with new accent color"""
        try:
            import colorsys
            h: float = hue_value / 360.0
            s: float = 0.8
            v: float = 1.0
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            accent_color: str = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            self.theme_label.setStyleSheet(f"color: {accent_color}; font-family: 'Courier New'; font-size: 10pt; font-weight: bold;")
            self.polling_label.setStyleSheet(f"color: {accent_color}; font-family: 'Courier New'; font-size: 10pt; font-weight: bold;")
            logger.info(f"[SYS] Theme updated to hue {hue_value}°")
            self.update_console(f"[SYS] Theme color updated to hue {hue_value}°")
        except Exception as e:
            logger.error(f"Failed to update theme: {e}")