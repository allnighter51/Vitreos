from typing import Optional, List, Union, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLayoutItem, QLayout
from PyQt6.QtCore import Qt
from .vitreos_theme import VITREOS_COLORS, FONT_SIZES, get_font

def v_label(text: str, font_size: Union[str, int] = 'medium', color: str = 'text_primary', align: Any = None) -> QLabel:
    lbl = QLabel(text)
    
    # Resolve font size
    f_size = FONT_SIZES.get(font_size, 10) if isinstance(font_size, str) else font_size
    lbl.setFont(get_font('mono', f_size))
    
    # Resolve color
    hex_color = VITREOS_COLORS.get(color, color)
    lbl.setStyleSheet(f"color: {hex_color};")
    
    if align is not None:
        lbl.setAlignment(align)
    return lbl

def _add_items(layout: Union[QVBoxLayout, QHBoxLayout], items: List[Any]) -> None:
    for item in items:
        if isinstance(item, str) and item == 'stretch':
            layout.addStretch()
        elif isinstance(item, QWidget):
            layout.addWidget(item)
        elif isinstance(item, QLayoutItem):
            layout.addItem(item)
        elif isinstance(item, QLayout):
            layout.addLayout(item)

def v_vbox(margins: int = 0, spacing: int = 0, items: Optional[List[Any]] = None) -> QVBoxLayout:
    layout = QVBoxLayout()
    layout.setContentsMargins(margins, margins, margins, margins)
    layout.setSpacing(spacing)
    if items:
        _add_items(layout, items)
    return layout

def v_hbox(margins: int = 0, spacing: int = 0, items: Optional[List[Any]] = None) -> QHBoxLayout:
    layout = QHBoxLayout()
    layout.setContentsMargins(margins, margins, margins, margins)
    layout.setSpacing(spacing)
    if items:
        _add_items(layout, items)
    return layout

def v_widget(bg: str = 'bg_primary') -> QWidget:
    w = QWidget()
    hex_color = VITREOS_COLORS.get(bg, bg)
    w.setStyleSheet(f"background: {hex_color}; border: 1px solid {VITREOS_COLORS.get('border_secondary', '#333333')};")
    return w
