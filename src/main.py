# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportConstantRedefinition=false, reportIncompatibleMethodOverride=false, reportArgumentType=false, reportPossiblyUnboundVariable=false, reportUnusedVariable=false, reportUnknownLambdaType=false
"""
Vitreos V3 - Pure Python PyQt6 Architecture
Main Application Window with Figma-Accurate Layout
"""

import sys
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QGridLayout, QVBoxLayout, QLabel, QSizeGrip, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, QPoint, QTimer, QEvent
from PyQt6.QtGui import QMouseEvent, QResizeEvent, QKeyEvent, QCloseEvent, QIcon

from src.ui.vitreos_theme import VITREOS_COLORS, VITREOS_STYLESHEET, initialize_theme, get_font, FONT_SIZES
from src.ui.vitreos_widgets import apply_phosphor_glow
from src.ui.vitreos_sidebar import VitreosSidebar
from src.ui.vitreos_effects import CRTOverlay, GlitchTransition
from src.core.vitreos_telemetry_pull import PullBasedTelemetry, PULSE_AVAILABLE
from src.core.vitreos_presence import PresenceWorker  # type: ignore[import-not-found]
from src.core.vitreos_bridge import translate_to_legacy_format  # type: ignore[import-not-found]
from src.ui.modules import (
    CpuMonitor, GpuMonitor, ThermalCtrl, StorageArray, MemoryArray, NetInterface
)

# Import tab modules for 10-tab navigation
try:
    from src.tabs import (  # type: ignore[import-not-found]
        NetworkTab, ProcessesTab, GPUProTab, SecurityTab,
        StorageTab, TweaksTab, ConsoleTab, RemoteTab, SettingsTab, SOCTab
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

    def enterEvent(self, a0: QEvent) -> None:
        self.setStyleSheet(
            f"background: {self._hover_color};"
            f" border: 1px solid {self._hover_color};"
        )
        super().enterEvent(a0)

    def leaveEvent(self, a0: QEvent) -> None:
        self._set_idle()
        super().leaveEvent(a0)


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
        
        # Auto-initialize runtime directories (data/ and config/) next to executable
        from src.core.paths import ensure_app_dirs, get_bundle_dir
        ensure_app_dirs()

        # Window properties
        self.setWindowTitle("VITREOS // SYSTEM SENTINEL v2.1")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Window icon from bundled assets
        icon_path = get_bundle_dir() / "assets" / "logo.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
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
        
        # Pre-initialize Storage Tab for background telemetry
        self.storage_tab: Optional[QWidget] = None
        
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
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(32)
        top_bar.setStyleSheet(f"""
            QWidget#TopBar {{
                background: {VITREOS_COLORS['bg_secondary']};
                border: none;
                border-bottom: 1px solid {VITREOS_COLORS['border_primary']};
                margin: 0px;
                padding: 0px;
            }}
        """)
        
        # Top bar layout (ZERO SPACING)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(0)  # CRITICAL: No spacing between zones
        
        # ═══════════════════════════════════════════════════════════════════
        # ZONE A: BRANDING CONTAINER (310px - The Anchor to match sidebar)
        # ═══════════════════════════════════════════════════════════════════
        branding_container = QFrame()
        branding_container.setObjectName("branding_container")
        branding_container.setFixedWidth(310)  # CRITICAL: Matches sidebar width
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
        logo_label.setFont(get_font('display', 14)) # Slightly smaller to fit everything
        logo_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        logo_label.setStyleSheet(f"""
            color: {VITREOS_COLORS['primary_purple']};
            letter-spacing: 2px;
            background: transparent;
        """)
        # Apply glow ONLY to the text label, not container
        apply_phosphor_glow(logo_label, 'primary_purple', blur_radius=8.0)
        branding_layout.addWidget(logo_label)
        
        # 1.5 Version Label
        version_label = QLabel("v2.1")
        version_label.setFont(get_font('mono', FONT_SIZES['micro']))
        version_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        version_label.setStyleSheet(f"""
            color: {VITREOS_COLORS['primary_purple']};
            opacity: 0.5;
            letter-spacing: 1px;
            background: transparent;
        """)
        branding_layout.addWidget(version_label)
        
        # 2. Expanding Spacer
        branding_layout.addStretch(1)
        
        # We removed the clock and controls from here to place them on the far right
        
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
                border-bottom: 1px solid {VITREOS_COLORS['border_primary']};
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
            ('NETWORK', 'text_dim'),
            ('PROCESSES', 'text_dim'),
            ('GPU PRO', 'text_dim'),
            ('SOC', 'text_dim'),
            ('STORAGE', 'text_dim'),
            ('LOGBOOK', 'text_dim'),
            ('REMOTE', 'text_dim'),
            ('CONSOLE', 'text_dim'),
            ('SETTINGS', 'text_dim'),
        ]
        
        for tab_name, accent_color in TAB_CONFIG:
            btn = QLabel(tab_name)
            btn.setFont(get_font('mono', FONT_SIZES['tiny']))
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn.setFixedHeight(32)  # 32px to sit flush
            btn.setMinimumWidth(85)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Use specific colors for active states
            active_color = 'primary_purple'
            if tab_name == 'NETWORK': active_color = 'green'
            elif tab_name == 'PROCESSES': active_color = 'cyan'
            elif tab_name == 'GPU PRO': active_color = 'warning_orange'
            elif tab_name == 'SOC': active_color = 'warning_orange'
            elif tab_name == 'STORAGE': active_color = 'purple_dim'
            elif tab_name == 'LOGBOOK': active_color = 'text_primary'
            elif tab_name == 'REMOTE': active_color = 'cyan'
            elif tab_name == 'CONSOLE': active_color = 'green'
            elif tab_name == 'SETTINGS': active_color = 'text_primary'
            
            # Store accent color as property
            btn.setProperty('accent_color', active_color)
            
            def make_handler(name: str):
                def handler(a0: QMouseEvent) -> None:
                    self._on_tab_clicked(name)
                return handler
            btn.mousePressEvent = make_handler(tab_name)  # type: ignore[method-assign]
            
            self.tab_buttons[tab_name] = btn
            nav_layout.addWidget(btn)
            
            self._update_tab_style(tab_name)
        
        nav_layout.addStretch()
        
        # ═══════════════════════════════════════════════════════════════════
        # RIGHT TRAY (Clock & Window Controls)
        # ═══════════════════════════════════════════════════════════════════
        tray_widget = QWidget()
        tray_widget.setObjectName("tray_widget")
        tray_widget.setStyleSheet(f"""
            QWidget#tray_widget {{
                background: {VITREOS_COLORS['bg_secondary']};
                border: none;
                border-bottom: 1px solid {VITREOS_COLORS['border_primary']};
            }}
        """)
        tray_layout = QHBoxLayout(tray_widget)
        tray_layout.setContentsMargins(16, 0, 8, 0)
        tray_layout.setSpacing(8)
        
        self.clock_label = QLabel()
        self.clock_label.setFont(get_font('mono', FONT_SIZES['micro']))
        self.clock_label.setStyleSheet(f"color: {VITREOS_COLORS['text_dim']}; background: transparent;")
        tray_layout.addWidget(self.clock_label)
        
        # Start clock timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()
        
        # Window Controls Container (darker box)
        controls_container = QFrame()
        controls_container.setObjectName("window_controls")
        controls_container.setStyleSheet(f"""
            QFrame#window_controls {{
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_dim']};
                border-radius: 2px;
            }}
        """)
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(4, 0, 4, 0)
        controls_layout.setSpacing(2)
        
        min_btn = QPushButton("─")
        min_btn.setObjectName("min_btn")
        min_btn.setFixedSize(20, 20)
        min_btn.setFont(get_font('mono', 9))
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        min_btn.setStyleSheet(f"""
            QPushButton#min_btn {{ background: transparent; color: {VITREOS_COLORS['text_secondary']}; border: none; padding: 0px; }}
            QPushButton#min_btn:hover {{ color: {VITREOS_COLORS['text_primary']}; }}
        """)
        min_btn.clicked.connect(self._on_minimize)
        controls_layout.addWidget(min_btn)
        
        max_btn = QPushButton("□")
        max_btn.setObjectName("max_btn")
        max_btn.setFixedSize(20, 20)
        max_btn.setFont(get_font('mono', 10))
        max_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        max_btn.setStyleSheet(f"""
            QPushButton#max_btn {{ background: transparent; color: {VITREOS_COLORS['text_secondary']}; border: none; padding: 0px; }}
            QPushButton#max_btn:hover {{ color: {VITREOS_COLORS['text_primary']}; }}
        """)
        max_btn.clicked.connect(self._on_maximize)
        controls_layout.addWidget(max_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(20, 20)
        close_btn.setFont(get_font('mono', 10))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton#close_btn {{ background: transparent; color: {VITREOS_COLORS['critical_red']}; border: none; padding: 0px; }}
            QPushButton#close_btn:hover {{ background: {VITREOS_COLORS['critical_red']}; color: {VITREOS_COLORS['bg_card']}; border-radius: 2px; }}
        """)
        close_btn.clicked.connect(self._on_close)
        controls_layout.addWidget(close_btn)
        
        tray_layout.addWidget(controls_container)
        
        top_bar_layout.addWidget(nav_container, 1)
        top_bar_layout.addWidget(tray_widget)
        # Make top bar draggable for frameless window behaviour
        top_bar.setCursor(Qt.CursorShape.SizeAllCursor)
        # Use `a0` parameter name to match PyQt6 stubs and satisfy Pylance
        top_bar.mousePressEvent = lambda a0: self._top_bar_mouse_press(a0)  # type: ignore[method-assign]
        top_bar.mouseMoveEvent = lambda a0: self._top_bar_mouse_move(a0)  # type: ignore[method-assign]
        top_bar.mouseReleaseEvent = lambda a0: self._top_bar_mouse_release(a0)  # type: ignore[method-assign]
        
        return top_bar
    
    def _update_clock(self) -> None:
        """Update micro-clock display."""
        from datetime import datetime
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        self.clock_label.setText(f"{time_str}")
    
    def _on_minimize(self) -> None:
        self.showMinimized()
        
    def _on_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def _on_close(self) -> None:
        self.close()

    # ---------- Top-bar drag handlers for frameless window ----------
    def _top_bar_mouse_press(self, a0: QMouseEvent) -> None:
        """Start window drag when user presses left mouse on top bar."""
        try:
            if a0.button() == Qt.MouseButton.LeftButton:
                # store offset between window top-left and mouse
                self.drag_position = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()
                a0.accept()
        except Exception:
            pass

    def _top_bar_mouse_move(self, a0: QMouseEvent) -> None:
        """Move window while dragging the top bar."""
        try:
            if self.drag_position is not None and (a0.buttons() & Qt.MouseButton.LeftButton):
                self.move(a0.globalPosition().toPoint() - self.drag_position)
                a0.accept()
        except Exception:
            pass

    def _top_bar_mouse_release(self, a0: QMouseEvent) -> None:
        """End window drag."""
        self.drag_position = None
    
    # Consolidated debug toggle handler (accepts optional bool from clicked signal)
    def _on_debug_toggled(self, enabled: bool = False) -> None:
        debug_btn = getattr(self, 'debug_btn', None)
        is_checked = debug_btn.isChecked() if debug_btn is not None else bool(enabled)
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
        """Update tab with clean minimalist design matching image."""
        btn = self.tab_buttons[tab_name]
        is_active = (tab_name == self.active_tab)
        accent_color = btn.property('accent_color')
        
        if is_active:
            # Active: Highlighted text, subtle background, bottom accent border
            btn.setStyleSheet(f"""
                QLabel {{
                    color: {VITREOS_COLORS[accent_color]};
                    background: rgba(255, 255, 255, 0.03);
                    border-top: none;
                    border-left: none;
                    border-right: 1px solid {VITREOS_COLORS['border_dim']};
                    border-bottom: 2px solid {VITREOS_COLORS[accent_color]};
                    padding: 0px 10px;
                    letter-spacing: 1px;
                }}
            """)
        else:
            # Inactive: Dim text, transparent background, right separator
            btn.setStyleSheet(f"""
                QLabel {{
                    color: {VITREOS_COLORS['text_dim']};
                    background: transparent;
                    border-top: none;
                    border-left: none;
                    border-right: 1px solid {VITREOS_COLORS['border_dim']};
                    border-bottom: 1px solid {VITREOS_COLORS['border_primary']};
                    padding: 0px 10px;
                    letter-spacing: 1px;
                }}
                QLabel:hover {{
                    color: {VITREOS_COLORS['text_secondary']};
                    background: rgba(255, 255, 255, 0.01);
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
            print("[VITREOS] ERROR: vitreos_pulse module not available")
            return
        
        try:
            print("[VITREOS] Initializing telemetry...")
            self.telemetry = PullBasedTelemetry()
            print("[VITREOS] Telemetry object created")
            
            # Connect data signal to update modules
            self.telemetry.data_ready.connect(self._update_modules)
            print("[VITREOS] Connected data_ready signal")
            
            # Connect log signal to sidebar batch handler (5-second batches)
            self.telemetry.log_ready.connect(self.sidebar.handle_pulse_log_batch)
            print("[VITREOS] Connected log_ready signal")
            
            # Connect error signal
            self.telemetry.error_occurred.connect(lambda msg: self.sidebar.append_log("ERR", msg, "critical_red"))
            print("[VITREOS] Connected error_occurred signal")
            
            # Connect network module for adapter sync
            self.network_module.telemetry_worker = self.telemetry  # type: ignore[attr-defined]
            print("[VITREOS] Connected network module")
            
            # Start telemetry
            print("[VITREOS] Starting telemetry worker...")
            self.telemetry.start()
            print("[VITREOS] Telemetry started successfully")
            
            # Pre-initialize Storage Tab and connect to telemetry
            if TABS_AVAILABLE:
                try:
                    from src.tabs import StorageTab
                    self.storage_tab = StorageTab()
                    self.telemetry.data_ready.connect(self.storage_tab.update_stats)
                    print("[VITREOS] Storage Tab initialized and connected to telemetry")
                except Exception as e:
                    print(f"[VITREOS] Failed to initialize Storage Tab: {e}")
                    import traceback
                    traceback.print_exc()
            
            self.sidebar.append_log("SYS", "Telemetry engine initialized", "primary_purple")
        
        except Exception as e:
            error_msg = f"Telemetry init failed: {e}"
            self.sidebar.append_log("ERR", error_msg, "critical_red")
            print(f"[VITREOS] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
    
    def _start_presence(self) -> None:
        """Initialize Discord Rich Presence worker (starts disabled)"""
        self.presence_worker = PresenceWorker()
    
    def _load_verbose_mode(self) -> None:
        """Load verbose mode state from the root config package safely."""
        try:
            from config.settings import load_settings  # type: ignore[import-not-found]
            settings = load_settings()
            self.verbose_mode = settings.get('monitoring', {}).get('verbose_mode', False)
        except Exception:
            self.verbose_mode = False
    
    def _save_verbose_mode(self) -> None:
        """Save verbose mode state via the root config package."""
        try:
            from config.settings import load_settings, save_settings  # type: ignore[import-not-found]
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
        import traceback as _traceback
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
            
            # GPU data is now a list; take the first one for primary metrics
            gpu_data_list = data.get('gpu', [])
            primary_gpu = gpu_data_list[0] if isinstance(gpu_data_list, list) and len(gpu_data_list) > 0 else {}
            gpu_load = primary_gpu.get('usage', 0)
            
            cpu_temp = data.get('cpu', {}).get('temp', 0)
            gpu_temp = primary_gpu.get('temp', 0)
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
            
            # Update V3 modules — each isolated so one crash cannot block others
            if 'cpu' in data:
                try:
                    self.cpu_module.update_data(data['cpu'])
                except Exception as _me:
                    print(f"[VITREOS][ERR] cpu_module.update_data: {_me}")
                    _traceback.print_exc()
            
            if 'gpu' in data:
                try:
                    self.gpu_module.update_data(data['gpu'])
                except Exception as _me:
                    print(f"[VITREOS][ERR] gpu_module.update_data: {_me}")
                    _traceback.print_exc()
            
            # Update presence worker if enabled
            if self.presence_worker and self.presence_enabled:
                self.presence_worker.update_hardware_stats(data)
            
            # Thermal module: pull temps from cpu/gpu sub-dicts
            thermal_data = {
                'cpuTemp': data.get('cpu', {}).get('temp', 0),
                'gpuTemp': primary_gpu.get('temp', 0),
            }
            try:
                self.thermal_module.update_data(thermal_data)
            except Exception as _me:
                print(f"[VITREOS][ERR] thermal_module.update_data: {_me}")
                _traceback.print_exc()
            
            if 'storage' in data:
                try:
                    self.storage_module.update_data(data['storage'])
                except Exception as _me:
                    print(f"[VITREOS][ERR] storage_module.update_data: {_me}")
                    _traceback.print_exc()
            
            if 'memory' in data:
                try:
                    self.memory_module.update_data(data['memory'])
                except Exception as _me:
                    print(f"[VITREOS][ERR] memory_module.update_data: {_me}")
                    _traceback.print_exc()
            
            if 'network' in data:
                try:
                    self.network_module.update_data(data['network'])
                except Exception as _me:
                    print(f"[VITREOS][ERR] network_module.update_data: {_me}")
                    _traceback.print_exc()
            
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
            import traceback as _tb2
            print(f"[VITREOS][ERR] _update_modules outer exception: {e}")
            _tb2.print_exc()
    
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
    
    def resizeEvent(self, a0: QResizeEvent) -> None:
        """Handle window resize to update overlay positions."""
        super().resizeEvent(a0)
        if hasattr(self, 'crt_overlay'):
            self.crt_overlay.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, 'glitch_overlay'):
            self.glitch_overlay.setGeometry(0, 0, self.width(), self.height())
    
    def keyPressEvent(self, a0: QKeyEvent) -> None:
        """Escape key: reserved for future use."""
        super().keyPressEvent(a0)

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
        
        elif tab_name == 'SOC' and TABS_AVAILABLE:
            try:
                self.active_tab_widget = SOCTab()
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                if self.active_tab_widget:
                    self.active_tab_widget.show()
            except Exception:
                pass
        
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
            # Use pre-initialized Storage Tab from cache
            if self.storage_tab:
                self.active_tab_widget = self.storage_tab
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                if self.active_tab_widget:
                    self.active_tab_widget.show()
            else:
                # Fallback: show storage module
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
    
    def closeEvent(self, a0: QCloseEvent) -> None:
        """Clean shutdown of telemetry and presence workers."""
        
        if self.telemetry:
            self.telemetry.stop()
        
        if self.presence_worker and self.presence_enabled:
            self.presence_worker.stop()
            self.presence_worker.wait(2000)
        
        a0.accept()


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


