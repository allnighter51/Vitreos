"""
Vitreos V3 - Pure Python PyQt6 Architecture
Main Application Window with Figma-Accurate Layout
"""

import sys
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QGridLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QSizeGrip
)
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QMouseEvent

from src.vitreos_theme import VITREOS_COLORS, VITREOS_STYLESHEET, initialize_theme, get_font, FONT_SIZES
from src.vitreos_widgets import SystemPulseLog, VitreosWinFrame
from src.vitreos_telemetry import TelemetryWorker
from src.vitreos_presence import PresenceWorker
from src.vitreos_bridge import translate_to_legacy_format
from src.vitreos_modules import (
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
    print(f"[VITREOS] Warning: Could not import tabs - {e}")
    TABS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
# NAVIGATION BAR - 10-Tab System
# ═══════════════════════════════════════════════════════════════════════════

class VitreosNavBar(QWidget):
    """
    10-tab navigation bar with active state highlighting.
    Matches legacy_pyqt tab structure.
    """
    
    tab_changed = pyqtSignal(str)  # Emits tab name when clicked
    debug_toggled = pyqtSignal(bool)  # Emits debug mode state
    
    TABS = [
        'VITALS', 'NETWORK', 'PROCESSES', 'GPU PRO', 'SECURITY',
        'STORAGE', 'TWEAKS', 'CONSOLE', 'REMOTE', 'SETTINGS'
    ]
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.active_tab = 'VITALS'
        self.tab_buttons: Dict[str, QLabel] = {}
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build navigation bar layout with window controls."""
        self.setFixedHeight(32)
        self.setStyleSheet(f"""
            VitreosNavBar {{
                background: {VITREOS_COLORS['bg_titlebar']};
                border-bottom: 1px solid {VITREOS_COLORS['border_primary']};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)
        
        # Create tab buttons
        for tab_name in self.TABS:
            btn = QLabel(tab_name)
            btn.setFont(get_font('mono', FONT_SIZES['label']))
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn.setFixedHeight(28)
            btn.setMinimumWidth(80)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Proper event handler binding
            def make_handler(name: str):
                def handler(e) -> None:
                    self._on_tab_clicked(name)
                return handler
            btn.mousePressEvent = make_handler(tab_name)  # type: ignore[method-assign]
            
            self.tab_buttons[tab_name] = btn
            layout.addWidget(btn)
            
            self._update_tab_style(tab_name)
        
        layout.addStretch()
        
        # Debug toggle button (RADAR icon)
        self.debug_btn = QPushButton("◉")
        self.debug_btn.setFixedSize(24, 24)
        self.debug_btn.setFont(get_font('mono', 12))
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
        layout.addWidget(self.debug_btn)
        
        # Window controls (Minimize + Close)
        min_btn = QPushButton("_")
        min_btn.setFixedSize(24, 24)
        min_btn.setFont(get_font('mono', FONT_SIZES['label']))
        min_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
                color: {VITREOS_COLORS['text_secondary']};
            }}
            QPushButton:hover {{
                background: {VITREOS_COLORS['border_primary']};
                color: {VITREOS_COLORS['primary_purple']};
                border: 1px solid {VITREOS_COLORS['primary_purple']};
            }}
        """)
        min_btn.clicked.connect(self._on_minimize)
        layout.addWidget(min_btn)
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setFont(get_font('mono', 14))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VITREOS_COLORS['bg_card']};
                border: 1px solid {VITREOS_COLORS['border_primary']};
                color: {VITREOS_COLORS['critical_red']};
            }}
            QPushButton:hover {{
                background: {VITREOS_COLORS['critical_red']};
                color: {VITREOS_COLORS['text_primary']};
                border: 1px solid {VITREOS_COLORS['critical_red']};
            }}
        """)
        close_btn.clicked.connect(self._on_close)
        layout.addWidget(close_btn)
    
    def _on_minimize(self) -> None:
        """Minimize window."""
        win = self.window()
        if win:
            win.showMinimized()
    
    def _on_close(self) -> None:
        """Close window."""
        win = self.window()
        if win:
            win.close()
    
    def _on_debug_toggled(self) -> None:
        """Handle debug toggle button click."""
        is_checked = self.debug_btn.isChecked()
        self.debug_toggled.emit(is_checked)
    
    def mousePressEvent(self, event) -> None:
        """Enable OS-native window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Use OS-native drag to prevent click-through
            win = self.window()
            if win and win.windowHandle():
                win.windowHandle().startSystemMove()
            event.accept()
    
    def _on_tab_clicked(self, tab_name: str) -> None:
        """Handle tab click."""
        if tab_name != self.active_tab:
            self.active_tab = tab_name
            
            # Update all tab styles
            for name in self.TABS:
                self._update_tab_style(name)
            
            # Debug logging
            tab_file = tab_name.lower().replace(' ', '_')
            log_msg = f"[NAV] Switching to Tab: {tab_name} | Logic Path: src/tabs/tab_{tab_file}.py"
            print(log_msg)
            
            # Send to Console if it's the active tab
            win = self.window()
            if win and hasattr(win, 'send_to_console'):
                win.send_to_console(log_msg)  # type: ignore[attr-defined]
            
            # Emit signal
            self.tab_changed.emit(tab_name)
    
    def _update_tab_style(self, tab_name: str) -> None:
        """Update tab button styling based on active state."""
        btn = self.tab_buttons[tab_name]
        is_active = (tab_name == self.active_tab)
        
        if is_active:
            btn.setStyleSheet(f"""
                QLabel {{
                    color: {VITREOS_COLORS['primary_purple']};
                    background: {VITREOS_COLORS['bg_card']};
                    border: 1px solid {VITREOS_COLORS['primary_purple']};
                    padding: 4px 12px;
                    letter-spacing: 1px;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QLabel {{
                    color: {VITREOS_COLORS['text_secondary']};
                    background: transparent;
                    border: 1px solid transparent;
                    padding: 4px 12px;
                    letter-spacing: 1px;
                }}
                QLabel:hover {{
                    color: {VITREOS_COLORS['text_primary']};
                    background: {VITREOS_COLORS['bg_primary']};
                    border: 1px solid {VITREOS_COLORS['border_secondary']};
                }}
            """)


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
        self.setMinimumSize(1200, 800)  # Minimum size, but resizable
        
        # Frameless window with transparency
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Drag support
        self.drag_position: Optional[QPoint] = None
        
        # Telemetry worker
        self.telemetry_worker: Optional[TelemetryWorker] = None
        
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
        
        print("[VITREOS] Main window initialized")
    
    def _setup_ui(self) -> None:
        """Build the main window layout."""
        # Central widget with Liquid Glass background
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        
        # Main vertical layout: NavBar + Content
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top: Navigation bar
        self.navbar = VitreosNavBar()
        self.navbar.tab_changed.connect(self._on_tab_changed)
        self.navbar.debug_toggled.connect(self._on_debug_toggled)
        main_layout.addWidget(self.navbar)
        
        # Bottom: Horizontal layout (Sidebar + Dashboard)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Left: SystemPulseLog (232px fixed width)
        self.sidebar = SystemPulseLog()
        content_layout.addWidget(self.sidebar)
        
        # Right: Dashboard grid
        dashboard_widget = QWidget()
        dashboard_widget.setObjectName("DashboardWidget")
        self.dashboard_grid = self._create_dashboard_grid()
        dashboard_widget.setLayout(self.dashboard_grid)
        content_layout.addWidget(dashboard_widget, 1)
        
        main_layout.addWidget(content_widget, 1)
        
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
    
    def _create_dashboard_grid(self) -> QGridLayout:
        """
        Create 2x3 grid layout for monitoring modules.
        Fluid scaling with minimum size constraints.
        
        Layout (Re-ordered for tactical density):
        Row 0: [GpuMonitor] [CpuMonitor] [ThermalCtrl]
        Row 1: [StorageArray] [MemoryArray] [NetInterface]
        """
        grid = QGridLayout()
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(8)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Row 0 (Top)
        self.gpu_module = GpuMonitor()
        self.gpu_module.setMinimumSize(380, 420)
        self.gpu_module.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grid.addWidget(self.gpu_module, 0, 0)
        
        self.cpu_module = CpuMonitor()
        self.cpu_module.setMinimumSize(380, 420)
        self.cpu_module.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grid.addWidget(self.cpu_module, 0, 1)
        
        self.thermal_module = ThermalCtrl()
        self.thermal_module.setMinimumSize(380, 420)
        self.thermal_module.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grid.addWidget(self.thermal_module, 0, 2)
        
        # Row 1 (Bottom)
        self.storage_module = StorageArray()
        self.storage_module.setMinimumSize(380, 420)
        self.storage_module.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grid.addWidget(self.storage_module, 1, 0)
        
        self.memory_module = MemoryArray()
        self.memory_module.setMinimumSize(380, 420)
        self.memory_module.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grid.addWidget(self.memory_module, 1, 1)
        
        self.network_module = NetInterface()
        self.network_module.setMinimumSize(380, 420)
        self.network_module.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grid.addWidget(self.network_module, 1, 2)
        
        # Equal column/row stretching for fluid scaling on ultrawide
        for col in range(3):
            grid.setColumnStretch(col, 1)  # Equal stretch for all columns
        for row in range(2):
            grid.setRowStretch(row, 1)  # Equal stretch for all rows
        
        # Add extra stretch columns/rows to prevent clustering
        grid.setColumnStretch(3, 0)  # No stretch beyond grid
        grid.setRowStretch(2, 0)  # No stretch beyond grid
        
        return grid
    
    def _apply_styling(self) -> None:
        """Apply Liquid Glass styling to main window."""
        self.setStyleSheet(f"""
            #CentralWidget {{
                background: rgba(13, 13, 13, 0.85);
                border: 2px solid {VITREOS_COLORS['border_primary']};
                border-radius: 0px;
            }}
            #DashboardWidget {{
                background: transparent;
            }}
        """)
    
    def _start_telemetry(self) -> None:
        """Initialize and start the telemetry worker thread."""
        self.telemetry_worker = TelemetryWorker()
        
        # Connect telemetry worker to network module for adapter sync
        self.network_module.telemetry_worker = self.telemetry_worker
        
        # Connect signals BEFORE starting worker
        self.telemetry_worker.data_ready.connect(self._update_modules)
        self.telemetry_worker.log_message.connect(self._handle_log)
        
        # Add initial log message to verify connection
        self.sidebar.append_log("SYS", "Initializing telemetry worker...", "primary_purple")
        
        # Start worker (will emit log messages from run())
        self.telemetry_worker.start()
        
        print("[VITREOS] Telemetry worker started")
    
    def _start_presence(self) -> None:
        """Initialize Discord Rich Presence worker (starts disabled)"""
        self.presence_worker = PresenceWorker()
        print("[VITREOS] Presence worker initialized (disabled)")
    
    def _load_verbose_mode(self) -> None:
        """Load verbose mode state from config/settings.json."""
        try:
            import json
            with open('config/settings.json', 'r') as f:
                settings = json.load(f)
                self.verbose_mode = settings.get('monitoring', {}).get('verbose_mode', False)
                if self.verbose_mode:
                    print("[VITREOS] Verbose Mode loaded: ENABLED")
        except Exception as e:
            print(f"[VITREOS] Could not load verbose mode: {e}")
            self.verbose_mode = False
    
    def _save_verbose_mode(self) -> None:
        """Save verbose mode state to config/settings.json."""
        try:
            import json
            with open('config/settings.json', 'r') as f:
                settings = json.load(f)
            
            if 'monitoring' not in settings:
                settings['monitoring'] = {}
            settings['monitoring']['verbose_mode'] = self.verbose_mode
            
            with open('config/settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            
            print(f"[VITREOS] Verbose Mode saved: {'ENABLED' if self.verbose_mode else 'DISABLED'}")
        except Exception as e:
            print(f"[VITREOS] Could not save verbose mode: {e}")
    
    def _on_debug_toggled(self, enabled: bool) -> None:
        """Handle debug toggle from navbar."""
        self.verbose_mode = enabled
        self._save_verbose_mode()
        
        status = "ENABLED" if enabled else "DISABLED"
        color = "warning_orange" if enabled else "text_dim"
        self.sidebar.append_log("DEBUG", f"Verbose Mode {status}", color)
        self.send_to_console(f"[VITREOS] Verbose Mode {status}")
        
        if enabled:
            self.send_to_console("[DEBUG] All user interactions and telemetry polls will be logged")
    
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
                        # Send raw telemetry to Console (if cached)
                        if tab_name == 'CONSOLE' and hasattr(tab_widget, 'write_raw'):
                            tab_widget.write_raw(data)  # type: ignore[attr-defined]
                        
                        # Send legacy data to all tabs with update methods
                        if hasattr(tab_widget, 'update_stats'):
                            tab_widget.update_stats(legacy_data)  # type: ignore[attr-defined]
                        elif hasattr(tab_widget, 'update_data'):
                            tab_widget.update_data(legacy_data)  # type: ignore[attr-defined]
                        elif hasattr(tab_widget, 'update_ping_stats'):
                            tab_widget.update_ping_stats(legacy_data)  # type: ignore[attr-defined]
                    except Exception as e:
                        print(f"[VITREOS] Error updating cached tab {tab_name}: {e}")
        
        except Exception as e:
            print(f"[VITREOS] Error updating modules: {e}")
    
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
    
    def _on_tab_changed(self, tab_name: str) -> None:
        """
        Handle tab navigation changes - swap dashboard content.
        Logic Bridge: Dynamically loads tab modules from tabs/ directory.
        
        Args:
            tab_name: Name of the selected tab
        """
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
                # Reuse cached Network tab
                self.active_tab_widget = self.tab_cache['NETWORK']
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                self.active_tab_widget.show()
                log_msg = "[VITREOS] Restored NetworkTab from cache"
                print(log_msg)
                self.send_to_console(log_msg)
            else:
                # Create new Network tab and cache it
                try:
                    self.active_tab_widget = NetworkTab()
                    self.tab_cache['NETWORK'] = self.active_tab_widget  # Cache it
                    
                    # Connect adapter changed signal to telemetry worker
                    if self.telemetry_worker:
                        self.active_tab_widget.adapter_changed.connect(self.telemetry_worker.set_active_adapter)  # type: ignore[attr-defined]
                    
                    # Set primary adapter if detected
                    if self.telemetry_worker and self.telemetry_worker.active_adapter:
                        self.active_tab_widget.set_primary_adapter(self.telemetry_worker.active_adapter)  # type: ignore[attr-defined]
                    
                    self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                    self.active_tab_widget.show()
                    log_msg = "[VITREOS] Loaded NetworkTab from tabs/tab_network.py"
                    print(log_msg)
                    self.send_to_console(log_msg)
                    log_msg2 = "[VITREOS] Telemetry bridge active - tab will receive live data"
                    print(log_msg2)
                    self.send_to_console(log_msg2)
                except Exception as e:
                    print(f"[VITREOS] Error loading NetworkTab: {e}")
                    self.network_module.show()  # Fallback to V3 module
        
        elif tab_name == 'SECURITY' and TABS_AVAILABLE:
            # Load SecurityTab from tabs/
            try:
                self.active_tab_widget = SecurityTab()
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                self.active_tab_widget.show()
                print("[VITREOS] Loaded SecurityTab from tabs/tab_security.py")
            except Exception as e:
                print(f"[VITREOS] Error loading SecurityTab: {e}")
                self.network_module.show()  # Fallback
        
        elif tab_name == 'GPU PRO' and TABS_AVAILABLE:
            # Load GPUProTab from tabs/
            try:
                self.active_tab_widget = GPUProTab()
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                self.active_tab_widget.show()
                print("[VITREOS] Loaded GPUProTab from tabs/tab_gpu_pro.py")
            except Exception as e:
                print(f"[VITREOS] Error loading GPUProTab: {e}")
                self.gpu_module.show()  # Fallback
        
        elif tab_name == 'PROCESSES' and TABS_AVAILABLE:
            # Load ProcessesTab from tabs/
            try:
                self.active_tab_widget = ProcessesTab()
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                self.active_tab_widget.show()
                print("[VITREOS] Loaded ProcessesTab from tabs/tab_processes.py")
            except Exception as e:
                print(f"[VITREOS] Error loading ProcessesTab: {e}")
                self.cpu_module.show()
                self.memory_module.show()
        
        elif tab_name == 'STORAGE' and TABS_AVAILABLE:
            # Load StorageTab from tabs/
            try:
                self.active_tab_widget = StorageTab()
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                self.active_tab_widget.show()
                print("[VITREOS] Loaded StorageTab from tabs/tab_storage.py")
            except Exception as e:
                print(f"[VITREOS] Error loading StorageTab: {e}")
                self.storage_module.show()
        
        elif tab_name == 'TWEAKS' and TABS_AVAILABLE:
            # Load TweaksTab from tabs/
            try:
                self.active_tab_widget = TweaksTab()
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                self.active_tab_widget.show()
                print("[VITREOS] Loaded TweaksTab from tabs/tab_tweaks.py")
            except Exception as e:
                print(f"[VITREOS] Error loading TweaksTab: {e}")
        
        elif tab_name == 'CONSOLE' and TABS_AVAILABLE:
            # Task 1: Check cache first, create only if needed
            if 'CONSOLE' in self.tab_cache:
                # Reuse cached Console tab
                self.active_tab_widget = self.tab_cache['CONSOLE']
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                self.active_tab_widget.show()
                log_msg = "[VITREOS] Restored ConsoleTab from cache"
                print(log_msg)
                self.send_to_console(log_msg)
            else:
                # Create new Console tab and cache it
                try:
                    self.active_tab_widget = ConsoleTab()
                    self.tab_cache['CONSOLE'] = self.active_tab_widget  # Cache it
                    self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                    self.active_tab_widget.show()
                    log_msg = "[VITREOS] Loaded ConsoleTab from tabs/tab_console.py"
                    print(log_msg)
                    self.send_to_console(log_msg)
                except Exception as e:
                    print(f"[VITREOS] Error loading ConsoleTab: {e}")
        
        elif tab_name == 'REMOTE' and TABS_AVAILABLE:
            if 'REMOTE' in self.tab_cache:
                self.active_tab_widget = self.tab_cache['REMOTE']
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                self.active_tab_widget.show()
                log_msg = "[VITREOS] Restored RemoteTab from cache"
                print(log_msg)
                self.send_to_console(log_msg)
            else:
                try:
                    self.active_tab_widget = RemoteTab()
                    self.tab_cache['REMOTE'] = self.active_tab_widget
                    self.active_tab_widget.presence_config_changed.connect(self._on_presence_config_changed)  # type: ignore[attr-defined]
                    if self.presence_worker:
                        self.presence_worker.status_changed.connect(self.active_tab_widget.set_connection_status)  # type: ignore[attr-defined]
                    self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                    self.active_tab_widget.show()
                    log_msg = "[VITREOS] Loaded RemoteTab from tabs/tab_remote.py"
                    print(log_msg)
                    self.send_to_console(log_msg)
                except Exception as e:
                    print(f"[VITREOS] Error loading RemoteTab: {e}")
        
        elif tab_name == 'SETTINGS' and TABS_AVAILABLE:
            # Load SettingsTab from tabs/
            try:
                self.active_tab_widget = SettingsTab()
                self.dashboard_grid.addWidget(self.active_tab_widget, 0, 0, 2, 3)
                self.active_tab_widget.show()
                print("[VITREOS] Loaded SettingsTab from tabs/tab_settings.py")
            except Exception as e:
                print(f"[VITREOS] Error loading SettingsTab: {e}")
        
        else:
            # Fallback for tabs without implementation
            print(f"[VITREOS] Tab '{tab_name}' not yet implemented or tabs unavailable")
            # Show relevant V3 modules as fallback
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
            print("[VITREOS] Discord Rich Presence enabled")
        elif not enabled and self.presence_enabled:
            self.presence_worker.stop()
            self.presence_worker.wait(2000)
            self.presence_enabled = False
            print("[VITREOS] Discord Rich Presence disabled")
    
    # ───────────────────────────────────────────────────────────────────────
    # FRAMELESS WINDOW DRAG SUPPORT (Removed - handled by navbar)
    # ───────────────────────────────────────────────────────────────────────
    
    # ───────────────────────────────────────────────────────────────────────
    # CLEANUP
    # ───────────────────────────────────────────────────────────────────────
    
    def closeEvent(self, event) -> None:
        """Clean shutdown of telemetry and presence workers."""
        print("[VITREOS] Shutting down...")
        
        if self.telemetry_worker:
            self.telemetry_worker.stop()
            self.telemetry_worker.wait(2000)
        
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
    
    # Initialize theme system
    initialize_theme()
    
    # Apply global stylesheet
    app.setStyleSheet(VITREOS_STYLESHEET)
    
    # Create and show main window
    window = VitreosMainWindow()
    window.show()
    
    print("[VITREOS] Application started")
    print("[VITREOS] Press Ctrl+C in terminal to exit")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
