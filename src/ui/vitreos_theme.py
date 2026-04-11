"""
Vitreos Design System - Theme Engine
Based on Figma V4 UI specifications with Liquid Glass aesthetic
"""

from typing import Dict, Optional
from PyQt6.QtGui import QFont, QFontDatabase, QColor
from PyQt6.QtCore import Qt
import os


# ═══════════════════════════════════════════════════════════════════════════
# COLOR PALETTE - Extracted from Figma V4 Design Tokens
# ═══════════════════════════════════════════════════════════════════════════

VITREOS_COLORS: Dict[str, str] = {
    # Primary Accent (Purple)
    'primary_purple': '#A855F7',
    'purple_glow': '#7C3AED',
    'purple_dim': '#6B3FA0',
    'purple_dark': '#5B2D8E',
    'purple_darker': '#3D1F6B',
    'purple_underline': '#A855F7',  # Active tab underline
    
    # Warning/Alert
    'warning_orange': '#FF6B00',
    'critical_red': '#FF4444',
    
    # Secondary Accents
    'cyan': '#06B6D4',
    'green': '#22C55E',
    
    # Backgrounds (Figma V4 dark mode)
    'bg_primary': '#0D0D0D',      # Main app background
    'bg_secondary': '#0A0A0A',    # Darker variant
    'bg_darker': '#080808',       # Darkest variant (V4 addition)
    'bg_card': '#111111',         # Card background
    'bg_titlebar': '#141414',     # Title bar
    'bg_frame': '#0F0F0F',        # Frame background
    
    # Borders (Figma V4 dark mode - RESTRAINED)
    'border_primary': '#333333',  # Main borders (inactive modules)
    'border_secondary': '#1E1E1E', # Subtle borders
    'border_dim': '#1A1A1A',      # Dimmer borders
    'border_active': '#6B3FA0',   # Active module border (dimmed purple)
    
    # Text (Figma V4 dark mode)
    'text_primary': '#E2E8F0',    # Bright text (V4 addition)
    'text_bright': '#E2E8F0',     # Alias for text_primary
    'text_sub': '#888888',        # Secondary headings (V4 addition)
    'text_secondary': '#555555',  # Medium gray
    'text_dim': '#444444',        # Dim text
    'text_darker': '#333333',     # Darker text
    'text_darkest': '#2A2A2A',    # Darkest text
    'text_dead': '#222222',       # Nearly invisible text (V4 addition)
    
    # Segments (LED bars)
    'segment_off': '#1C1C1C',     # Inactive segment
    'segment_dim': '#1A1A1A',     # Dim segment
}


# ═══════════════════════════════════════════════════════════════════════════
# TYPOGRAPHY - Font Specifications
# ═══════════════════════════════════════════════════════════════════════════

VITREOS_FONTS: Dict[str, str] = {
    'mono': 'Share Tech Mono',
    'display': 'VT323',
    'fallback_mono': 'Consolas',
    'fallback_display': 'Courier New',
}

FONT_SIZES: Dict[str, int] = {
    'logo': 44,
    'title': 14,
    'value_large': 13,
    'value_medium': 11,
    'label': 10,
    'small': 9,
    'tiny': 8,
    'micro': 7,
}


# ═══════════════════════════════════════════════════════════════════════════
# FONT LOADING - Google Fonts Integration
# ═══════════════════════════════════════════════════════════════════════════

def load_google_fonts() -> Dict[str, bool]:
    """
    Load Google Fonts into Qt Font Database.
    Uses absolute paths to ensure fonts are found regardless of launch directory.
    
    Returns:
        Dict with font names and load status
    """
    status = {}
    
    # Get absolute path to fonts directory
    # Go up from src/ui/ to project root, then into assets/fonts/
    current_file = os.path.abspath(__file__)
    ui_dir = os.path.dirname(current_file)
    src_dir = os.path.dirname(ui_dir)
    project_root = os.path.dirname(src_dir)
    font_dir = os.path.join(project_root, 'assets', 'fonts')
    
    print(f"[VITREOS THEME] Looking for fonts in: {font_dir}")
    
    fonts_to_load = {
        'Share Tech Mono': 'ShareTechMono-Regular.ttf',
        'VT323': 'VT323-Regular.ttf',
    }
    
    for font_name, font_file in fonts_to_load.items():
        font_path = os.path.join(font_dir, font_file)
        
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                status[font_name] = True
                print(f"[VITREOS THEME] Loaded font: {font_name} from {font_path}")
            else:
                status[font_name] = False
                print(f"[VITREOS THEME] Failed to load font: {font_name}")
        else:
            status[font_name] = False
            print(f"[VITREOS THEME] Font file not found: {font_path}")
    
    return status


def get_font(font_type: str = 'mono', size: int = 10, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """
    Get a configured QFont with fallback support.
    
    Args:
        font_type: 'mono' or 'display'
        size: Font size in points
        weight: Font weight
    
    Returns:
        Configured QFont object
    """
    if font_type == 'display':
        primary = VITREOS_FONTS['display']
        fallback = VITREOS_FONTS['fallback_display']
    else:
        primary = VITREOS_FONTS['mono']
        fallback = VITREOS_FONTS['fallback_mono']
    
    # Try primary font first
    font = QFont(primary, size, weight)
    
    # Check if font is available, fallback if not
    available_families = QFontDatabase.families()
    if primary not in available_families:
        # Use high-quality system fallback
        if 'Segoe UI Variable' in available_families:
            font = QFont('Segoe UI Variable', size, QFont.Weight.DemiBold)
        elif 'Segoe UI' in available_families:
            font = QFont('Segoe UI', size, QFont.Weight.DemiBold)
        else:
            font = QFont(fallback, size, weight)
    
    font.setStyleHint(QFont.StyleHint.Monospace if font_type == 'mono' else QFont.StyleHint.SansSerif)
    return font


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL STYLESHEET - QSS with Liquid Glass Effects
# ═══════════════════════════════════════════════════════════════════════════

VITREOS_STYLESHEET = f"""
/* ═══════════════════════════════════════════════════════════════════════ */
/* VITREOS GLOBAL STYLESHEET - Liquid Glass Theme (Figma V4)              */
/* ═══════════════════════════════════════════════════════════════════════ */

QMainWindow {{
    background: {VITREOS_COLORS['bg_primary']};
    color: {VITREOS_COLORS['text_primary']};
    font-family: '{VITREOS_FONTS['mono']}', '{VITREOS_FONTS['fallback_mono']}';
    font-size: 10pt;
}}

/* ─────────────────────────────────────────────────────────────────────── */
/* SCROLLBARS - Minimal Dark Style                                         */
/* ─────────────────────────────────────────────────────────────────────── */

QScrollBar:vertical {{
    background: {VITREOS_COLORS['bg_secondary']};
    width: 8px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {VITREOS_COLORS['border_primary']};
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background: {VITREOS_COLORS['primary_purple']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {VITREOS_COLORS['bg_secondary']};
    height: 8px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {VITREOS_COLORS['border_primary']};
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {VITREOS_COLORS['primary_purple']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ─────────────────────────────────────────────────────────────────────── */
/* BUTTONS - Minimal Cyberpunk Style                                       */
/* ─────────────────────────────────────────────────────────────────────── */

QPushButton {{
    background: {VITREOS_COLORS['bg_card']};
    color: {VITREOS_COLORS['text_secondary']};
    border: 1px solid {VITREOS_COLORS['border_secondary']};
    padding: 6px 12px;
    font-family: '{VITREOS_FONTS['mono']}';
    font-size: 9pt;
    letter-spacing: 0.1em;
}}

QPushButton:hover {{
    background: {VITREOS_COLORS['border_primary']};
    color: {VITREOS_COLORS['primary_purple']};
    border: 1px solid {VITREOS_COLORS['primary_purple']};
}}

QPushButton:pressed {{
    background: {VITREOS_COLORS['bg_primary']};
    border: 1px solid {VITREOS_COLORS['purple_glow']};
}}

/* ─────────────────────────────────────────────────────────────────────── */
/* LABELS - Text Styling                                                   */
/* ─────────────────────────────────────────────────────────────────────── */

QLabel {{
    background: transparent;
    color: {VITREOS_COLORS['text_secondary']};
    font-family: '{VITREOS_FONTS['mono']}';
}}

/* ─────────────────────────────────────────────────────────────────────── */
/* TEXT EDIT / LIST WIDGETS - Terminal Style                               */
/* ─────────────────────────────────────────────────────────────────────── */

QTextEdit, QListWidget {{
    background: {VITREOS_COLORS['bg_secondary']};
    color: {VITREOS_COLORS['text_dim']};
    border: 1px solid {VITREOS_COLORS['border_secondary']};
    font-family: '{VITREOS_FONTS['mono']}';
    font-size: 9pt;
    selection-background-color: {VITREOS_COLORS['purple_dark']};
}}

/* ─────────────────────────────────────────────────────────────────────── */
/* TOOLTIPS - Glowing Info Boxes                                           */
/* ─────────────────────────────────────────────────────────────────────── */

QToolTip {{
    background: {VITREOS_COLORS['bg_card']};
    color: {VITREOS_COLORS['primary_purple']};
    border: 1px solid {VITREOS_COLORS['primary_purple']};
    padding: 4px;
    font-family: '{VITREOS_FONTS['mono']}';
    font-size: 8pt;
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS - Color Utilities
# ═══════════════════════════════════════════════════════════════════════════

def hex_to_qcolor(hex_color: str, alpha: int = 255) -> QColor:
    """
    Convert hex color string to QColor with optional alpha.
    
    Args:
        hex_color: Hex color string (e.g., '#A855F7')
        alpha: Alpha value (0-255)
    
    Returns:
        QColor object
    """
    color = QColor(hex_color)
    color.setAlpha(alpha)
    return color


def get_color(color_name: str, alpha: int = 255) -> QColor:
    """
    Get QColor from VITREOS_COLORS palette.
    
    Args:
        color_name: Key from VITREOS_COLORS dict
        alpha: Alpha value (0-255)
    
    Returns:
        QColor object
    """
    hex_color = VITREOS_COLORS.get(color_name, '#FFFFFF')
    return hex_to_qcolor(hex_color, alpha)


def rgba_string(color_name: str, alpha: float = 1.0) -> str:
    """
    Get rgba() CSS string from color name.
    
    Args:
        color_name: Key from VITREOS_COLORS dict
        alpha: Alpha value (0.0-1.0)
    
    Returns:
        rgba() string for CSS
    """
    color = get_color(color_name)
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"


def get_glow_stylesheet(color_name: str, intensity: int = 8) -> str:
    """
    Generate text-shadow CSS for glow effect.
    
    Args:
        color_name: Key from VITREOS_COLORS dict
        intensity: Glow radius in pixels
    
    Returns:
        CSS text-shadow string
    """
    hex_color = VITREOS_COLORS.get(color_name, '#FFFFFF')
    return f"text-shadow: 0 0 {intensity}px {hex_color};"


# ═══════════════════════════════════════════════════════════════════════════
# THEME INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

def initialize_theme() -> bool:
    """
    Initialize the Vitreos theme system.
    Loads fonts and prepares the design system.
    
    Returns:
        True if initialization successful
    """
    print("[VITREOS THEME] Initializing design system...")
    
    # Load Google Fonts
    font_status = load_google_fonts()
    
    # Check if at least one font loaded
    if not any(font_status.values()):
        print("[VITREOS THEME] WARNING: No custom fonts loaded, using fallbacks")
    
    print("[VITREOS THEME] Theme initialization complete")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'VITREOS_COLORS',
    'VITREOS_FONTS',
    'FONT_SIZES',
    'VITREOS_STYLESHEET',
    'load_google_fonts',
    'get_font',
    'hex_to_qcolor',
    'get_color',
    'rgba_string',
    'get_glow_stylesheet',
    'initialize_theme',
]
