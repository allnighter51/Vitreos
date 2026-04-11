"""
Vitreos V3 - Pure Python PyQt6 Architecture
Main Application Window with Figma-Accurate Layout
"""

import sys
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QGridLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QSizeGrip, QFrame
)
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QMouseEvent, QEnterEvent

from src.ui.vitreos_theme import VITREOS_COLORS, VITREOS_STYLESHEET, initialize_theme, get_font, FONT_SIZES
from src.ui.vitreos_widgets import SystemPulseLog, VitreosWinFrame, ChromaticLogo, apply_phosphor_glow
from src.ui.vitreos_sidebar import VitreosSidebar
from src.ui.vitreos_effects import CRTOverlay, GlitchTransition
from src.core.vitreos_telemetry_pull import PullBasedTelemetry, PULSE_AVAILABLE
from src.core.vitreos_presence import PresenceWorker
from src.core.vitreos_bridge import translate_to_legacy_format
from src.ui.vitreos_modules import (
    CpuMonitor, GpuMonitor, ThermalCtrl, StorageArray, MemoryArray, NetInterface
)

# Import tab modules for 10-tab navigation
try:
    from src.tabs import (
        VitalsTab, NetworkTab, ProcessesTab, GPUProTab, SecurityTab,
        StorageTab, TweaksTab, ConsoleTab, RemoteTab, SettingsTab
    )
    TABS_AVAILABLE = True
except ImportError as e:
    TABS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
# MICRO CONTROL - 5x5px window control button (no lambda monkey-patching)
# ═══════════════════════════════════════════════════════════════════════════

class MicroControl(QLabel):
    """5x5px hover-reactive window control square."""

    def __init__(self, hover_color: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._hover_color = hover_color
        self.setFixedSize(5, 5)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_idle()

    def _set_idle(self) -> None:
        self.setStyleSheet(
            f"background: {VITREOS_COLORS['bg_card']};"
            f" border: 1px solid {VITREOS_COLORS['border_primary']};"
        )

    def enterEvent(self, event) -> None:
        self.setStyleSheet(
            f"background: {self._hover_color};"
            f" border: 1px solid {self._hover_color};"
        )
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent | None) -> None:
        self._set_idle()
        super().leaveEvent(event)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN WINDOW - Frameless with Liquid Glass Effect
# ═══════════════════════════════════════════════════════════════════════════

class VitreosMainWindow(QMainWindow):
    """
    Main application window with frameless design and custom layout.
    Matches Figma specifications with 232px sidebar + 2x3 grid dashboard.
    """
    
    def __init__(self):
        super().__init__()
        
        # Window properties
        self.setWindowTitle("VITREOS // SYSTEM SENTINEL v2.1")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Frameless window (SOLID STATE - No transparency)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Use native OS cursor
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setMouseTracking(True)
        
        # Drag support
        self.drag_position: Optional[QPoint] = None
        
        # Telemetry worker (pull-based with Rust engine)
        self.telemetry: Optional[PullBasedTelemetry] = None
        
        # Presence worker (Discord Rich Presence)
        self.presence_worker: Optional[PresenceWorker] = None
        self.presence_enabled = False
        
        # Tab widgets (for 10-tab navigation)
        self.active_tab_widget: Optional[QWidget] = None
        
        # Task 1: Tab Cache - "Stay-Alive" system for background tabs
        self.tab_cache: Dict[str, QWidget] = {}
        
        # Master Debug: Verbose Mode
        self.verbose_mode = False
        self._load_verbose_mode()
        
        # Initialize UI
        self._setup_ui()
        self._apply_styling()
        self._start_telemetry()
        self._start_presence()
    
    def _setup_ui(self) -> None:
        """Build the main window layout with Master Axis Intersection."""
        # Central widget with solid matte background
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        
        # Main vertical layout: Top Bar + Content (ZERO SPACING)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # Critical: Zero-gap enforcement
        
        # Top: Global Top Bar (232px branding + tabs)
        self.top_bar = self._create_top_bar()
        main_layout.addWidget(self.top_bar)
        
        # NOTE: Removed redundant global meridian to declutter header separators
        
        # Bottom: Horizontal layout (Sidebar + Dashboard) - ZERO SPACING
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)  # Critical: Zero-gap enforcement
        
        # Left: Tactical Sidebar (232px fixed)
        self.sidebar = VitreosSidebar()
        content_layout.addWidget(self.sidebar)
        
        # The Sidebar Divider (Explicit 1px vertical line)
        self.sidebar_divider = QFrame()
        self.sidebar_divider.setFixedWidth(1)
        self.sidebar_divider.setStyleSheet(f"background-color: {VITREOS_COLORS['border_primary']}; border: none;")
        content_layout.addWidget(self.sidebar_divider)
        
        # Right: Dashboard grid
        dashboard_widget = QWidget()
        dashboard_widget.setObjectName("DashboardWidget")
        self.dashboard_grid = self._create_dashboard_grid()
        dashboard_widget.setLayout(self.dashboard_grid)
        content_layout.addWidget(dashboard_widget, 1)
        
        main_layout.addWidget(content_widget, 1)
        
        # CRT Post-Processing Overlay
        self.crt_overlay = CRTOverlay(central)
        self.crt_overlay.setGeometry(0, 0, self.width(), self.height())
        self.crt_overlay.raise_()
        
        # Glitch Transition Overlay
        self.glitch_overlay = GlitchTransition(central)
        self.glitch_overlay.setGeometry(0, 0, self.width(), self.height())
        self.glitch_overlay.raise_()
        
        # Add resize grip in bottom-right corner
        self.size_grip = QSizeGrip(central)
        self.size_grip.setFixedSize(16, 16)
        self.size_grip.setStyleSheet(f"""
            QSizeGrip {{
                background: {VITREOS_COLORS['border_primary']};
                border: 1px solid {VITREOS_COLORS['primary_purple']};
            }}
        """)
        # Position grip in bottom-right
        grip_layout = QHBoxLayout()
        grip_layout.addStretch()
        grip_layout.addWidget(self.size_grip)
        main_layout.addLayout(grip_layout)
    
    def _create_top_bar(self) -> QWidget:
        """
        Create the global top bar with pixel-perfect 232px alignment.
        
        Structure:
        - Zone A: Branding container (232px fixed) with Logo → Space → Pulse Log
        - Zone B: Navigation container (flexible) with tab buttons
        """
        top_bar = QWidget()
        top_bar.setFixedHeight(32)
        top_bar.setStyleSheet(f"""
            QWidget {{
                background: {VITREOS_COLORS['bg_secondary']};
                border: none;
                margin: 0px;
                padding: 0px;
            }}
        """)
        
        # Top bar layout (ZERO SPACING)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(0)  # CRITICAL: No spacing between zones
        
        # ═══════════════════════════════════════════════════════════════════
        # ZONE A: BRANDING CONTAINER (232px - The Anchor)
        # ═══════════════════════════════════════════════════════════════════
        branding_container = QFrame()
        branding_container.setObjectName("branding_container")
        branding_container.setFixedWidth(232)  # CRITICAL: Matches sidebar width
        branding_container.setFrameShape(QFrame.Shape.NoFrame)  # Eliminate invisible borders
        branding_container.setLineWidth(0)  # Zero internal frame width
        branding_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        branding_container.setStyleSheet(f"""
            QFrame#branding_container {{
                background: transparent;
                border: none;
                border-right: 1px solid {VITREOS_COLORS['border_primary']};
                margin: 0px;
                padding: 0px;
            }}
        """)
        
        # Horizontal layout: Logo → Space → Pulse Log
        branding_layout = QHBoxLayout(branding_container)
        branding_layout.setContentsMargins(10, 5, 10, 5)
        branding_layout.setSpacing(0)
        
        # 1. VITREOS Logo (Left-aligned) - Text-only glow
        logo_label = QLabel("VITREOS")
        logo_label.setFont(get_font('display', 18))
        logo_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        logo_label.setStyleSheet(f"""
            color: {VITREOS_COLORS['primary_purple']};
            letter-spacing: 2px;
            background: transparent;
        """)
        # Apply glow ONLY to the text label, not container
        apply_phosphor_glow(logo_label, 'primary_purple', blur_radius=8.0)
        branding_layout.addWidget(logo_label)
        
        # 2. Expanding Spacer (The "Blank Space")
        branding_layout.addStretch(1)
        
        # 3. Sys Pulse Log (Right-aligned, ending at pixel 232) - Text-only glow
        pulse_log_label = QLabel("● PULSE")
        pulse_log_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        pulse_log_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        pulse_log_label.setStyleSheet(f"""
            color: {VITREOS_COLORS['green']};
            letter-spacing: 1px;
            background: transparent;
        """)
        # Apply glow ONLY to the text label, not container
        apply_phosphor_glow(pulse_log_label, 'green', blur_radius=4.0)
        branding_layout.addWidget(pulse_log_label)
        
        top_bar_layout.addWidget(branding_container)
        
        # ═══════════════════════════════════════════════════════════════════
        # ZONE B: NAVIGATION CONTAINER (Tabs)
        # ═══════════════════════════════════════════════════════════════════
        nav_container = QFrame()
        nav_container.setObjectName("nav_container")
        nav_container.setFrameShape(QFrame.Shape.NoFrame)
        nav_container.setLineWidth(0)
        nav_container.setStyleSheet(f"""
            QFrame#nav_container {{
                background: {VITREOS_COLORS['bg_secondary']};
                border: none;
                margin: 0px;
                padding: 0px;
            }}
            QFrame#nav_container QPushButton {{
                border: none;
                margin: 0px;
                padding: 0px;
                background: transparent;
            }}
        """)
        
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        
        # Tab buttons
        self.active_tab = 'VITALS'
        self.tab_buttons: Dict[str, QLabel] = {}
        
        # Tab configuration with accent colors
        TAB_CONFIG = [
            ('VITALS', 'primary_purple'),
            ('NETWORK', 'green'),
            ('PROCESSES', 'cyan'),
            ('GPU PRO', 'warning_orange'),
            ('SECURITY', 'critical_red'),
            ('STORAGE', 'purple_dim'),
            ('TWEAKS', 'primary_purple'),
            ('CONSOLE', 'green'),
            ('REMOTE', 'cyan'),
            ('SETTINGS', 'text_secondary'),
        ]
        
        for tab_name, accent_color in TAB_CONFIG:
            btn = QLabel(tab_name)
            btn.setFont(get_font('mono', FONT_SIZES['tiny']))
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn.setFixedHeight(31)  # 31px to sit flush
            btn.setMinimumWidth(70)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Store accent color as property
            btn.setProperty('accent_color', accent_color)
            
            def make_handler(name: str):
                def handler(a0: QMouseEvent | None) -> None:
                    self._on_tab_clicked(name)
                return handler
            btn.mousePressEvent = make_handler(tab_name)  # type: ignore[method-assign]
            
            self.tab_buttons[tab_name] = btn
            nav_layout.addWidget(btn)
            
            self._update_tab_style(tab_name)
        
        nav_layout.addStretch()
        
        # Right: System tray compartment
        tray_widget = QWidget()
        tray_widget.setStyleSheet(f"""
            background: {VITREOS_COLORS['bg_secondary']};
            border-left: 1px solid {VITREOS_COLORS['border_primary']};
        """)
        tray_layout = QHBoxLayout(tray_widget)
        tray_layout.setContentsMargins(12, 0, 12, 0)
        tray_layout.setSpacing(8)
        
        # Micro-clock
        self.clock_label = QLabel()
        self.clock_label.setFont(get_font('mono', FONT_SIZES['tiny']))
        self.clock_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']};")
        tray_layout.addWidget(self.clock_label)
        # Apply phosphor glow and monospaced styling to clock label
        self.clock_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']}; background: transparent; letter-spacing: 1px;")
        apply_phosphor_glow(self.clock_label, 'primary_purple', blur_radius=6.0)
        
        # Start clock timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()
        
        # Debug toggle
        self.debug_btn = QPushButton("◉")
        self.debug_btn.setFixedSize(16, 16)
        self.debug_btn.setFont(get_font('mono', 8))
        self.debug_btn.setCheckable(True)
        self.debug_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
                color: {VITREOS_COLORS['text_dim']};
            }}
            QPushButton:checked {{
                background: {VITREOS_COLORS['warning_orange']};
                border: 1px solid {VITREOS_COLORS['warning_orange']};
                color: {VITREOS_COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background: {VITREOS_COLORS['border_primary']};
                color: {VITREOS_COLORS['warning_orange']};
                border: 1px solid {VITREOS_COLORS['warning_orange']};
            }}
        """)
        self.debug_btn.clicked.connect(self._on_debug_toggled)
        tray_layout.addWidget(self.debug_btn)
        
        # Window controls — Visible Minimize and Close buttons (far top-right)
        min_btn = QPushButton("-")
        min_btn.setFixedSize(20, 18)
        min_btn.setFont(get_font('mono', FONT_SIZES['micro']))
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        min_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {VITREOS_COLORS['text_dim']};
                border: none;
            }}
            QPushButton:hover {{
                color: {VITREOS_COLORS['primary_purple']};
                background: rgba(168,85,247,0.04);
            }}
        """)
        min_btn.clicked.connect(self._on_minimize)
        tray_layout.addWidget(min_btn)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setFont(get_font('mono', FONT_SIZES['micro']))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {VITREOS_COLORS['text_dim']};
                border: none;
            }}
            QPushButton:hover {{
                color: {VITREOS_COLORS['critical_red']};
                background: rgba(255,68,68,0.04);
            }}
        """)
        close_btn.clicked.connect(self._on_close)
        tray_layout.addWidget(close_btn)
        
        nav_layout.addWidget(tray_widget)
        
        top_bar_layout.addWidget(nav_container, 1)
        # Make top bar draggable for frameless window behaviour
        top_bar.setCursor(Qt.CursorShape.SizeAllCursor)
        # Use `a0` parameter name to match PyQt6 stubs and satisfy Pylance
        top_bar.mousePressEvent = lambda a0: self._top_bar_mouse_press(a0)
        top_bar.mouseMoveEvent = lambda a0: self._top_bar_mouse_move(a0)
        top_bar.mouseReleaseEvent = lambda a0: self._top_bar_mouse_release(a0)
        
        return top_bar
    
    def _update_clock(self) -> None:
        """Update micro-clock display."""
        from datetime import datetime
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        day_abbrev = now.strftime("%a")
        # Format: CLOCK_ HH:MM:SS (Day)
        self.clock_label.setText(f"CLOCK_ {time_str} ({day_abbrev})")
    
    def _on_minimize(self) -> None:
        self.showMinimized()
    
    def _on_close(self) -> None:
        self.close()

    # ---------- Top-bar drag handlers for frameless window ----------
    def _top_bar_mouse_press(self, a0: QMouseEvent | None) -> None:
        """Start window drag when user presses left mouse on top bar."""
        try:
            if a0 is not None and a0.button() == Qt.MouseButton.LeftButton:
                # store offset between window top-left and mouse
                self.drag_position = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()
                a0.accept()
        except Exception:
            pass

    def _top_bar_mouse_move(self, a0: QMouseEvent | None) -> None:
        """Move window while dragging the top bar."""
        try:
            if self.drag_position is not None and a0 is not None and (a0.buttons() & Qt.MouseButton.LeftButton):
                self.move(a0.globalPosition().toPoint() - self.drag_position)
                a0.accept()
        except Exception:
            pass

    def _top_bar_mouse_release(self, a0: QMouseEvent | None) -> None:
        """End window drag."""
        self.drag_position = None
    
    # Consolidated debug toggle handler (accepts optional bool from clicked signal)
    def _on_debug_toggled(self, enabled: bool | None = None) -> None:
        is_checked = self.debug_btn.isChecked() if enabled is None else bool(enabled)
        self.verbose_mode = is_checked
        self._save_verbose_mode()

        status = "ENABLED" if is_checked else "DISABLED"
        color = "warning_orange" if is_checked else "text_dim"
        self.sidebar.append_log("DEBUG", f"Verbose Mode {status}", color)
        self.send_to_console(f"[VITREOS] Verbose Mode {status}")

        if is_checked:
            self.send_to_console("[DEBUG] All user interactions and telemetry polls will be logged")
    
    def _on_tab_clicked(self, tab_name: str) -> None:
        if tab_name != self.active_tab:
            self.active_tab = tab_name
            
            # Update all tab styles with dynamic accents
            for name in self.tab_buttons.keys():
                self._update_tab_style(name)
            
            tab_file = tab_name.lower().replace(' ', '_')
            log_msg = f"[NAV] Switching to Tab: {tab_name} | Logic Path: src/tabs/tab_{tab_file}.py"
            
            self.send_to_console(log_msg)
            self._on_tab_changed(tab_name)
    
    def _update_tab_style(self, tab_name: str) -> None:
        """Update tab with dynamic reactive HUD accents (3-sided box)."""
        btn = self.tab_buttons[tab_name]
        is_active = (tab_name == self.active_tab)
        accent_color = btn.property('accent_color')
        
        if is_active:
            # Active: 3-sided box with dynamic accent color + 2px neon underline
            btn.setStyleSheet(f"""
                QLabel {{
                    color: {VITREOS_COLORS[accent_color]};
                    background: {VITREOS_COLORS['bg_secondary']};
                    border-top: 1px solid {VITREOS_COLORS[accent_color]};
                    border-left: 1px solid {VITREOS_COLORS[accent_color]};
                    border-right: 1px solid {VITREOS_COLORS[accent_color]};
                    border-bottom: 2px solid {VITREOS_COLORS[accent_color]};
                    padding: 6px 8px 0px 8px;
                    letter-spacing: 1px;
                }}
            """)
        else:
            # Inactive: 3-sided box with dimmed borders
            btn.setStyleSheet(f"""
                QLabel {{
                    color: {VITREOS_COLORS['text_darker']};
                    background: {VITREOS_COLORS['bg_secondary']};
                    border-top: 1px solid {VITREOS_COLORS['border_dim']};
                    border-left: 1px solid {VITREOS_COLORS['border_dim']};
                    border-right: 1px solid {VITREOS_COLORS['border_dim']};
                    border-bottom: none;
                    padding: 6px 8px 2px 8px;
                    letter-spacing: 1px;
                }}
                QLabel:hover {{
                    color: {VITREOS_COLORS['text_secondary']};
                    border-top: 1px solid {VITREOS_COLORS['border_primary']};
                    border-left: 1px solid {VITREOS_COLORS['border_primary']};
                    border-right: 1px solid {VITREOS_COLORS['border_primary']};
                }}
            """)
    
    def _create_dashboard_grid(self) -> QGridLayout:
        """
        Create 3x2 Strategic Grid for Mission Control aesthetic.
        
        Layout:
        Row 0: [GPU_MONITOR] [CPU_MONITOR] [MEMORY_ARRAY]
        Row 1: [NET_INTERFACE] [THERMAL_CTRL] [STORAGE_ARRAY]
        """
        grid = QGridLayout()
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(8)
        
        # Row 0
        self.gpu_module = GpuMonitor()
        self.gpu_module.setMinimumSize(360, 400)
        self.gpu_module.setMaximumHeight(450)
        grid.addWidget(self.gpu_module, 0, 0)
        
        self.cpu_module = CpuMonitor()
        self.cpu_module.setMinimumSize(360, 400)
        self.cpu_module.setMaximumHeight(450)
        grid.addWidget(self.cpu_module, 0, 1)
        
        self.memory_module = MemoryArray()
        self.memory_module.setMinimumSize(360, 400)
        self.memory_module.setMaximumHeight(450)
        grid.addWidget(self.memory_module, 0, 2)
        
        # Row 1
        self.network_module = NetInterface()
        self.network_module.setMinimumSize(360, 400)
        self.network_module.setMaximumHeight(450)
        grid.addWidget(self.network_module, 1, 0)
        
        self.thermal_module = ThermalCtrl()
        self.thermal_module.setMinimumSize(360, 400)
        self.thermal_module.setMaximumHeight(450)
        grid.addWidget(self.thermal_module, 1, 1)
        
        self.storage_module = StorageArray()
        self.storage_module.setMinimumSize(360, 400)
        self.storage_module.setMaximumHeight(450)
        grid.addWidget(self.storage_module, 1, 2)
        
        # Equal stretching
        for col in range(3):
            grid.setColumnStretch(col, 1)
        for row in range(2):
            grid.setRowStretch(row, 1)
        
        return grid
    
    def _apply_styling(self) -> None:
        """Apply RESTRAINED styling with solid matte background."""
        self.setStyleSheet(f"""
            #CentralWidget {{
                background: {VITREOS_COLORS['bg_secondary']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
            }}
            #DashboardWidget {{
                background: {VITREOS_COLORS['bg_secondary']};
            }}
        """)
    
    def _start_telemetry(self) -> None:
        """Initialize and start the pull-based telemetry system."""
        if not PULSE_AVAILABLE:
            self.sidebar.append_log("ERR", "Rust telemetry engine not available", "critical_red")
            return
        
        try:
            self.telemetry = PullBasedTelemetry()
            
            # Connect data signal to update modules
            self.telemetry.data_ready.connect(self._update_modules)
            
            # Connect log signal to sidebar batch handler (5-second batches)
            self.telemetry.log_ready.connect(self.sidebar.handle_pulse_log_batch)
            
            # Connect error signal
            self.telemetry.error_occurred.connect(lambda msg: self.sidebar.append_log("ERR", msg, "critical_red"))
            
            # Connect network module for adapter sync
            self.network_module.telemetry_worker = self.telemetry  # type: ignore[attr-defined]
            
            # Start telemetry
            self.telemetry.start()
            
            self.sidebar.append_log("SYS", "Telemetry engine initialized", "primary_purple")
        
        except Exception as e:
            self.sidebar.append_log("ERR", f"Telemetry init failed: {e}", "critical_red")
    
    def _start_presence(self) -> None:
        """Initialize Discord Rich Presence worker (starts disabled)"""
        self.presence_worker = PresenceWorker()
    
    def _load_verbose_mode(self) -> None:
        """Load verbose mode state from the root config package safely."""
        try:
            from config.settings import load_settings
            settings = load_settings()
            self.verbose_mode = settings.get('monitoring', {}).get('verbose_mode', False)
        except Exception:
            self.verbose_mode = False
    
    def _save_verbose_mode(self) -> None:
        """Save verbose mode state via the root config package."""
        try:
            from config.settings import load_settings, save_settings
            settings = load_settings()
            if 'monitoring' not in settings:
                settings['monitoring'] = {}
            settings['monitoring']['verbose_mode'] = self.verbose_mode
            save_settings(settings)
        except Exception:
            pass
    
    
    def _update_modules(self, data: Dict[str, Any]) -> None:
        """
        Update all monitoring modules with fresh telemetry data.
        Also updates active tab widget if present.
        
        Args:
            data: Hardware telemetry dictionary from TelemetryWorker
        """
        try:
            # Verbose Mode: Log telemetry poll (amber)
            if self.verbose_mode and hasattr(self, '_update_counter'):
                if self._update_counter % 5 == 0:  # Every 5 seconds to avoid spam
                    cpu_load = data.get('cpu', {}).get('totalLoad', 0)
                    gpu_temp = data.get('gpu', {}).get('temp', 0)
                    self.send_to_console(f"[TELEMETRY] Poll #{self._update_counter}: CPU {cpu_load:.0f}% | GPU {gpu_temp:.0f}°C")
            # Initialize tracking variables
            if not hasattr(self, '_update_counter'):
                self._update_counter = 0
                self._last_cpu_load = 0
                self._last_gpu_load = 0
                self._last_cpu_temp = 0
                self._last_gpu_temp = 0
                self._network_peak = 0
            
            self._update_counter += 1
            
            # Extract current metrics
            cpu_load = data.get('cpu', {}).get('totalLoad', 0)
            gpu_load = data.get('gpu', {}).get('usage', 0)
            cpu_temp = data.get('cpu', {}).get('temp', 0)
            gpu_temp = data.get('gpu', {}).get('temp', 0)
            download_mbps = data.get('network', {}).get('downloadMbps', 0)
            
            # TACTICAL FILTER: Only log significant events to sidebar
            
            # Event 1: CPU Load Spike (>25% change)
            if abs(cpu_load - self._last_cpu_load) > 25:
                self.sidebar.append_log("CPU", f"Load spike: {self._last_cpu_load:.0f}% → {cpu_load:.0f}%", "warning_orange")
                self._last_cpu_load = cpu_load
            
            # Event 2: GPU Load Spike (>25% change)
            if abs(gpu_load - self._last_gpu_load) > 25:
                self.sidebar.append_log("GPU", f"Load spike: {self._last_gpu_load:.0f}% → {gpu_load:.0f}%", "warning_orange")
                self._last_gpu_load = gpu_load
            
            # Event 3: CPU Temperature Threshold (>5°C change)
            if abs(cpu_temp - self._last_cpu_temp) > 5:
                color = "critical_red" if cpu_temp > 85 else "warning_orange" if cpu_temp > 75 else "cyan"
                self.sidebar.append_log("CPU", f"Temp change: {self._last_cpu_temp:.0f}°C → {cpu_temp:.0f}°C", color)
                self._last_cpu_temp = cpu_temp
            
            # Event 4: GPU Temperature Threshold (>5°C change)
            if abs(gpu_temp - self._last_gpu_temp) > 5:
                color = "critical_red" if gpu_temp > 85 else "warning_orange" if gpu_temp > 75 else "warning_orange"
                self.sidebar.append_log("GPU", f"Temp change: {self._last_gpu_temp:.0f}°C → {gpu_temp:.0f}°C", color)
                self._last_gpu_temp = gpu_temp
            
            # Event 5: Network Peak Reached
            if download_mbps > self._network_peak:
                self._network_peak = download_mbps
                self.sidebar.append_log("NET", f"New peak: {download_mbps:.1f} Mbps", "green")
            
            # Update V3 modules
            if 'cpu' in data:
                self.cpu_module.update_data(data['cpu'])
            
            if 'gpu' in data:
                self.gpu_module.update_data(data['gpu'])
            
            # Update presence worker if enabled
            if self.presence_worker and self.presence_enabled:
                self.presence_worker.update_hardware_stats(data)
            
            if 'thermal' in data:
                # Thermal module needs CPU and GPU temps from their respective sources
                thermal_data = {
                    'cpuTemp': data.get('cpu', {}).get('temp', 0),
                    'gpuTemp': data.get('gpu', {}).get('temp', 0),
                }
                self.thermal_module.update_data(thermal_data)
            
            if 'storage' in data:
                self.storage_module.update_data(data['storage'])
            
            if 'memory' in data:
                self.memory_module.update_data(data['memory'])
            
            if 'network' in data:
                self.network_module.update_data(data['network'])
            
            # Task 2: Background Signal Routing - Update ALL cached tabs, not just active one
            if TABS_AVAILABLE and self.tab_cache:
                legacy_data = translate_to_legacy_format(data)
                
                for tab_name, tab_widget in self.tab_cache.items():
                    try:
                        if tab_name == 'CONSOLE' and hasattr(tab_widget, 'write_raw'):
                            tab_widget.write_raw(data)  # type: ignore[attr-defined]
                        
                        if tab_name == 'PROCESSES' and 'processes' in data and hasattr(tab_widget, 'update_processes'):
                            tab_widget.update_processes(data['processes'])  # type: ignore[attr-defined]
                        
                        if hasattr(tab_widget, 'update_stats'):
                            tab_widget.update_stats(legacy_data)  # type: ignore[attr-defined]
                        elif hasattr(tab_widget, 'update_data'):
                            tab_widget.update_data(legacy_data)  # type: ignore[attr-defined]
                        elif hasattr(tab_widget, 'update_ping_stats'):
                            tab_widget.update_ping_stats(legacy_data)  # type: ignore[attr-defined]
                    except Exception:
                        pass
        
        except Exception as e:
            pass
    
    def _handle_log(self, level: str, message: str, color: str) -> None:
        """
        Handle log messages from telemetry worker.
        
        Args:
            level: Log level (OK, WARN, CPU, GPU, etc.)
            message: Log message
            color: Color name from VITREOS_COLORS
        """
        self.sidebar.append_log(level, message, color)
    
    def send_to_console(self, message: str) -> None:
        """
        Send app event message to Console tab (cached or active).
        This makes Console the "Master Log" for all [NAV] and [VITREOS] events.
        
        Args:
            message: Log message with [NAV] or [VITREOS] prefix
        """
        # Send to cached Console tab if it exists
        if 'CONSOLE' in self.tab_cache and hasattr(self.tab_cache['CONSOLE'], 'write_app_event'):
            self.tab_cache['CONSOLE'].write_app_event(message)  # type: ignore[attr-defined]
    
    def resizeEvent(self, event) -> None:
        """Handle window resize to update overlay positions."""
        super().resizeEvent(event)
        if hasattr(self, 'crt_overlay'):
            self.crt_overlay.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, 'glitch_overlay'):
            self.glitch_overlay.setGeometry(0, 0, self.width(), self.height())
    
    def keyPressEvent(self, event) -> None:
        """Escape key: reserved for future use."""
        super().keyPressEvent(event)

    def _on_tab_changed(self, tab_name: str) -> None:
        """
        Handle tab navigation changes - swap dashboard content.
        Logic Bridge: Dynamically loads tab modules from tabs/ directory.
        
        Args:
            tab_name: Name of the selected tab
        """
        # Trigger glitch transition
        if hasattr(self, 'glitch_overlay'):
            self.glitch_overlay.trigger_glitch()
        
        # Verbose Mode: Log user interaction (yellow)
        if self.verbose_mode:
            self.send_to_console(f"[INPUT] User switched to {tab_name} tab")
        
        log_msg = f"[VITREOS] Switching to tab: {tab_name}"
        print(log_msg)
        self.send_to_console(log_msg)
        
        # Update presence worker with active tab
        if self.presence_worker and self.presence_enabled:
            self.presence_worker.set_active_tab(tab_name)
        
        # Remove active tab widget if exists
        if self.active_tab_widget:
            self.dashboard_grid.removeWidget(self.active_tab_widget)
            self.active_tab_widget.hide()
            self.active_tab_widget = None
        
        # Hide all V3 modules
        self.storage_module.hide()
        self.cpu_module.hide()
        self.thermal_module.hide()
        self.memory_module.hide()
        self.gpu_module.hide()
        self.network_module.hide()
        
        # Show modules or load tab based on selection
        if tab_name == 'VITALS':
            # Default 2x3 grid with V3 modules
            self.storage_module.show()
            self.cpu_module.show()
            self.thermal_module.show()
            self.memory_module.show()
            self.gpu_module.show()
            self.network_module.show()
        
        elif tab_name == 'NETWORK' and TABS_AVAILABLE:
            # Task 1: Check cache first, create only if needed
            if 'NETWORK' in self.tab_cache:
                self.active_tab_widget = self.tab_cache['NETWORK']
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                if self.active_tab_widget:
                    self.active_tab_widget.show()
            else:
                try:
                    self.active_tab_widget = NetworkTab()
                    self.tab_cache['NETWORK'] = self.active_tab_widget
                    
                    if self.telemetry:
                        self.active_tab_widget.adapter_changed.connect(self.telemetry.set_active_adapter)  # type: ignore[attr-defined]
                    
                    self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                    if self.active_tab_widget:
                        self.active_tab_widget.show()
                except Exception:
                    self.network_module.show()
        
        elif tab_name == 'SECURITY' and TABS_AVAILABLE:
            try:
                self.active_tab_widget = SecurityTab()
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                if self.active_tab_widget:
                    self.active_tab_widget.show()
            except Exception:
                self.network_module.show()
        
        elif tab_name == 'GPU PRO' and TABS_AVAILABLE:
            try:
                self.active_tab_widget = GPUProTab()
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                if self.active_tab_widget:
                    self.active_tab_widget.show()
            except Exception:
                self.gpu_module.show()
        
        elif tab_name == 'PROCESSES' and TABS_AVAILABLE:
            # Task 1: Check cache first, create only if needed
            if 'PROCESSES' in self.tab_cache:
                self.active_tab_widget = self.tab_cache['PROCESSES']
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                if self.active_tab_widget:
                    self.active_tab_widget.show()
            else:
                try:
                    self.active_tab_widget = ProcessesTab()
                    self.tab_cache['PROCESSES'] = self.active_tab_widget
                    self.active_tab_widget.log_message.connect(self._handle_log)  # type: ignore[attr-defined]
                    self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                    if self.active_tab_widget:
                        self.active_tab_widget.show()
                except Exception:
                    self.cpu_module.show()
                    self.memory_module.show()
        
        elif tab_name == 'STORAGE' and TABS_AVAILABLE:
            try:
                self.active_tab_widget = StorageTab()
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                if self.active_tab_widget:
                    self.active_tab_widget.show()
            except Exception:
                self.storage_module.show()
        
        elif tab_name == 'TWEAKS' and TABS_AVAILABLE:
            try:
                self.active_tab_widget = TweaksTab()
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                if self.active_tab_widget:
                    self.active_tab_widget.show()
            except Exception:
                pass
        
        elif tab_name == 'CONSOLE' and TABS_AVAILABLE:
            # Task 1: Check cache first, create only if needed
            if 'CONSOLE' in self.tab_cache:
                self.active_tab_widget = self.tab_cache['CONSOLE']
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                if self.active_tab_widget:
                    self.active_tab_widget.show()
            else:
                try:
                    self.active_tab_widget = ConsoleTab()
                    self.tab_cache['CONSOLE'] = self.active_tab_widget
                    self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                    if self.active_tab_widget:
                        self.active_tab_widget.show()
                except Exception:
                    pass
        
        elif tab_name == 'REMOTE' and TABS_AVAILABLE:
            if 'REMOTE' in self.tab_cache:
                self.active_tab_widget = self.tab_cache['REMOTE']
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                if self.active_tab_widget:
                    self.active_tab_widget.show()
            else:
                try:
                    self.active_tab_widget = RemoteTab()
                    self.tab_cache['REMOTE'] = self.active_tab_widget
                    self.active_tab_widget.presence_config_changed.connect(self._on_presence_config_changed)  # type: ignore[attr-defined]
                    if self.presence_worker:
                        self.presence_worker.status_changed.connect(self.active_tab_widget.set_connection_status)  # type: ignore[attr-defined]
                    self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                    if self.active_tab_widget:
                        self.active_tab_widget.show()
                except Exception:
                    pass
        
        elif tab_name == 'SETTINGS' and TABS_AVAILABLE:
            # Load SettingsTab and connect to telemetry
            try:
                self.active_tab_widget = SettingsTab()
                
                # Connect settings slider to telemetry rates (SYNCHRONIZED)
                if self.telemetry:
                    self.active_tab_widget.polling_rate_changed.connect(self.telemetry.set_polling_rate)
                    self.active_tab_widget.ui_refresh_rate_changed.connect(self.telemetry.set_ui_refresh_rate)
                
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                if self.active_tab_widget:
                    self.active_tab_widget.show()
            except Exception as e:
                pass
        
        else:
            if tab_name == 'NETWORK':
                self.network_module.show()
            elif tab_name == 'GPU PRO':
                self.gpu_module.show()
                self.thermal_module.show()
            elif tab_name == 'STORAGE':
                self.storage_module.show()
            elif tab_name == 'PROCESSES':
                self.cpu_module.show()
                self.memory_module.show()
    
    def _on_presence_config_changed(self, config: Dict[str, Any]) -> None:
        """Handle Discord Rich Presence configuration changes from Remote tab"""
        if not self.presence_worker:
            return
        
        enabled = config.get('enabled', False)
        show_hardware = config.get('show_hardware', True)
        show_active_tab = config.get('show_active_tab', True)
        tournament_mode = config.get('tournament_mode', False)
        
        self.presence_worker.set_config(show_hardware, show_active_tab, tournament_mode)
        
        if enabled and not self.presence_enabled:
            self.presence_worker.start()
            self.presence_enabled = True
        elif not enabled and self.presence_enabled:
            self.presence_worker.stop()
            self.presence_worker.wait(2000)
            self.presence_enabled = False
    
    # ───────────────────────────────────────────────────────────────────────
    # FRAMELESS WINDOW DRAG SUPPORT (Removed - handled by navbar)
    # ───────────────────────────────────────────────────────────────────────
    
    # ───────────────────────────────────────────────────────────────────────
    # CLEANUP
    # ───────────────────────────────────────────────────────────────────────
    
    def closeEvent(self, event) -> None:
        """Clean shutdown of telemetry and presence workers."""
        
        if self.telemetry:
            self.telemetry.stop()
        
        if self.presence_worker and self.presence_enabled:
            self.presence_worker.stop()
            self.presence_worker.wait(2000)
        
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════
# APPLICATION ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Launch the Vitreos application."""
    app = QApplication(sys.argv)
    
    initialize_theme()
    app.setStyleSheet(VITREOS_STYLESHEET)
    
    window = VitreosMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


