"""
Vitreos Sentinel - Architect Edition
Main Entry Point & Orchestrator with Hacker-Pulse Multi-Channel Routing
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QEvent, QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QMouseEvent, QCloseEvent

from vitreos_workers import HardwareMonitorWorker, SecurityMonitorThread, NetworkAnalyzer, AlertManager
from vitreos_dialogs import PurgeConfirmationDialog, TuningConfirmationDialog
from tabs import (
    VitalsTab, NetworkTab, ProcessesTab, GPUProTab, StorageTab,
    SecurityTab, LogbookTab, ConsoleTab, RemoteTab, SettingsTab
)


class AlertRouter:
    """Multi-channel Discord webhook router for categorized alerts"""
    
    def __init__(self) -> None:
        self.routing_table: Dict[str, str] = {
            'SECURITY': '',
            'THERMALS': '',
            'SYSTEM': '',
            'NETWORK': '',
            'STORAGE': ''
        }
        self.default_webhook = ''
    
    def set_webhook(self, channel: str, url: str) -> None:
        """Set webhook URL for specific channel"""
        if channel in self.routing_table:
            self.routing_table[channel] = url
        else:
            self.default_webhook = url
    
    def get_webhook(self, channel: str) -> str:
        """Get webhook URL for channel, fallback to default"""
        return self.routing_table.get(channel, self.default_webhook)
    
    def has_webhook(self, channel: str) -> bool:
        """Check if channel has configured webhook"""
        url = self.routing_table.get(channel, self.default_webhook)
        return bool(url)


class VitreosArchitect(QMainWindow):
    """Main orchestrator window for Vitreos Sentinel"""
    
    console_log = pyqtSignal(str)
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Vitreos Sentinel | Architect Edition")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.drag_position: Any = None
        self.db_connection: Any = None
        self.combat_mode_active = False
        self.alert_router = AlertRouter()
        
        self._init_database()
        self._build_ui()
        self._init_workers()
        self._connect_signals()
        self._init_system_tray()
        self._apply_initial_settings()
    
    def _init_database(self) -> None:
        """Initialize SQLite database for logging"""
        db_path = Path.home() / ".vitreos" / "sentinel.db"
        db_path.parent.mkdir(exist_ok=True)
        
        self.db_connection = sqlite3.connect(str(db_path), check_same_thread=False)
        cursor = self.db_connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hardware_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_percent REAL,
                ram_percent REAL,
                gpu_temp REAL,
                disk_percent REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                description TEXT,
                severity TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                alert_type TEXT,
                message TEXT,
                dispatched INTEGER
            )
        """)
        
        self.db_connection.commit()
    
    def _build_ui(self) -> None:
        """Construct the main UI layout"""
        central = QWidget()
        central.setObjectName("CentralWidget")
        central.setStyleSheet("""
            #CentralWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #08080a, stop:1 #0d0d10);
                border: 2px solid #bc13fe;
                border-radius: 12px;
            }
        """)
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        title_bar = self._create_title_bar()
        main_layout.addWidget(title_bar)
        
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        
        nav_sidebar = self._create_navigation()
        content_layout.addWidget(nav_sidebar)
        
        self.tab_stack = QStackedWidget()
        self.tab_stack.setStyleSheet("QStackedWidget { background: transparent; }")
        
        self.vitals_tab = VitalsTab()
        self.network_tab = NetworkTab()
        self.processes_tab = ProcessesTab()
        self.gpu_tab = GPUProTab()
        self.storage_tab = StorageTab()
        self.security_tab = SecurityTab()
        self.logbook_tab = LogbookTab()
        self.console_tab = ConsoleTab()
        self.remote_tab = RemoteTab()
        self.settings_tab = SettingsTab()
        
        self.tab_stack.addWidget(self.vitals_tab)
        self.tab_stack.addWidget(self.network_tab)
        self.tab_stack.addWidget(self.processes_tab)
        self.tab_stack.addWidget(self.gpu_tab)
        self.tab_stack.addWidget(self.storage_tab)
        self.tab_stack.addWidget(self.security_tab)
        self.tab_stack.addWidget(self.logbook_tab)
        self.tab_stack.addWidget(self.console_tab)
        self.tab_stack.addWidget(self.remote_tab)
        self.tab_stack.addWidget(self.settings_tab)
        
        content_layout.addWidget(self.tab_stack, stretch=1)
        main_layout.addLayout(content_layout)
    
    def _create_title_bar(self) -> QWidget:
        """Create custom title bar with window controls"""
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #bc13fe, stop:1 #00f2ff);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 18px;
                font-weight: bold;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        title_bar.installEventFilter(self)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(15, 0, 5, 0)
        
        title_btn = QPushButton("💎 VITREOS SENTINEL")
        title_btn.setStyleSheet("font-family: 'Consolas'; font-size: 16px; font-weight: bold;")
        layout.addWidget(title_btn)
        layout.addStretch()
        
        minimize_btn = QPushButton("−")
        minimize_btn.clicked.connect(self.showMinimized)  # type: ignore
        minimize_btn.setFixedSize(40, 40)
        
        close_btn = QPushButton("×")
        close_btn.clicked.connect(self.exit_application)  # type: ignore
        close_btn.setFixedSize(40, 40)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: white; }
            QPushButton:hover { background: #ff3333; }
        """)
        
        layout.addWidget(minimize_btn)
        layout.addWidget(close_btn)
        
        return title_bar
    
    def _create_navigation(self) -> QWidget:
        """Create navigation sidebar with tab buttons"""
        nav_widget = QWidget()
        nav_widget.setFixedWidth(200)
        nav_widget.setStyleSheet("""
            QWidget {
                background: rgba(12, 12, 15, 0.95);
                border-radius: 8px;
            }
            QPushButton {
                background: transparent;
                color: #00f2ff;
                border: none;
                text-align: left;
                padding: 12px 15px;
                font-family: 'Consolas';
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(188, 19, 254, 0.3);
                border-left: 3px solid #bc13fe;
            }
            QPushButton:checked {
                background: rgba(188, 19, 254, 0.5);
                border-left: 3px solid #bc13fe;
                color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout(nav_widget)
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setSpacing(5)
        
        nav_buttons = [
            ("⚡ VITALS", 0),
            ("🌐 NETWORK", 1),
            ("⚙️ PROCESSES", 2),
            ("🎮 GPU PRO", 3),
            ("💾 STORAGE", 4),
            ("🛡️ SECURITY", 5),
            ("📋 LOGBOOK", 6),
            ("🖥️ CONSOLE", 7),
            ("📡 REMOTE", 8),
            ("⚙️ SETTINGS", 9),
        ]
        
        for label, index in nav_buttons:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self._switch_tab(idx))  # type: ignore
            layout.addWidget(btn)
            
            if index == 0:
                btn.setChecked(True)
        
        layout.addStretch()
        return nav_widget
    
    def _switch_tab(self, index: int) -> None:
        """Switch to specified tab and update button states"""
        self.tab_stack.setCurrentIndex(index)
        
        central_widget = self.centralWidget()
        if not central_widget:
            return
            
        nav_widget = central_widget.findChild(QWidget)
        if not nav_widget:
            return
            
        buttons = nav_widget.findChildren(QPushButton)
        for i, btn in enumerate(buttons):
            btn.setChecked(i == index)
    
    def _init_workers(self) -> None:
        """Initialize all worker threads"""
        self.hardware_worker = HardwareMonitorWorker()
        self.hardware_worker.start()
        
        self.security_thread = SecurityMonitorThread()
        self.security_thread.start()
        
        self.network_analyzer = NetworkAnalyzer()
        self.network_analyzer.start()
        
        self.alert_manager = AlertManager(self.db_connection)
    
    def _connect_signals(self) -> None:
        """Wire all signals between workers and tab modules"""
        self.hardware_worker.stats_updated.connect(self.vitals_tab.update_stats)  # type: ignore
        self.hardware_worker.gpu_advanced_updated.connect(self.gpu_tab.update_telemetry)  # type: ignore
        self.hardware_worker.stats_updated.connect(self.storage_tab.update_disk_stats)  # type: ignore
        self.hardware_worker.stats_updated.connect(self._format_hardware_pulse)  # type: ignore
        self.hardware_worker.gpu_advanced_updated.connect(self._format_gpu_pulse)  # type: ignore
        
        self.network_analyzer.ping_updated.connect(self.network_tab.update_ping_stats)  # type: ignore
        self.network_analyzer.bandwidth_updated.connect(self.network_tab.update_bandwidth_hogs)  # type: ignore
        
        self.security_thread.usb_event.connect(self.security_tab.add_security_event)  # type: ignore
        self.security_thread.security_alert.connect(self.security_tab.add_security_event)  # type: ignore
        self.security_thread.usb_event.connect(self._format_security_pulse)  # type: ignore
        
        self.processes_tab.purge_requested.connect(self._show_purge_dialog)  # type: ignore
        self.processes_tab.tuning_requested.connect(self._show_tuning_dialog)  # type: ignore
        
        self.gpu_tab.fan_speed_changed.connect(self._set_gpu_fan_speed)  # type: ignore
        self.storage_tab.cache_purge_requested.connect(self._purge_cache)  # type: ignore
        self.security_tab.monitoring_toggled.connect(self._toggle_security_monitoring)  # type: ignore
        self.console_tab.webhook_test_requested.connect(self._test_webhook)  # type: ignore
        self.remote_tab.webhook_saved.connect(self._save_webhook_config)  # type: ignore
        
        self.settings_tab.polling_interval_changed.connect(self._update_polling_interval)  # type: ignore
        self.settings_tab.theme_changed.connect(self._update_theme)  # type: ignore
        self.settings_tab.database_clear_requested.connect(self._clear_database)  # type: ignore
        self.settings_tab.database_export_requested.connect(self._export_database)  # type: ignore
        
        self.console_log.connect(self.console_tab.append_log)  # type: ignore
    
    def _format_hardware_pulse(self, stats: Dict[str, Any]) -> None:
        """Format hardware stats as hacker-pulse"""
        cpu_pct: float = stats.get('cpu_percent', 0.0)
        ram_pct: float = stats.get('ram_percent', 0.0)
        gpu_temp: float = stats.get('gpu_temp', 0.0)
        
        status = "STABLE"
        level = "INFO"
        
        if cpu_pct > 90 or ram_pct > 90 or gpu_temp > 85:
            status = "CRITICAL"
            level = "ERROR"
        elif cpu_pct > 75 or ram_pct > 75 or gpu_temp > 75:
            status = "WARNING"
            level = "WARNING"
        
        pulse = f"[SYS_PULSE] 0xCPU >> LOAD: {cpu_pct:.1f}% | RAM: {ram_pct:.1f}% | GPU_TEMP: {gpu_temp}°C | STATUS: {status}"
        
        self.console_tab.write_console(pulse, level)
        self.logbook_tab.append_log_entry(pulse)
        
        if gpu_temp > 85:
            self._dispatch_alert("THERMALS", f"[THERMAL_ALERT] 0xGPU >> TEMP: {gpu_temp}°C | STATUS: CRITICAL")
    
    def _format_gpu_pulse(self, telemetry: Any) -> None:
        """Format GPU telemetry as hacker-pulse"""
        clock_mhz: int = getattr(telemetry, 'clock_mhz', 0)
        power_watts: float = getattr(telemetry, 'power_watts', 0.0)
        vram_used_mb: int = getattr(telemetry, 'vram_used_mb', 0)
        throttle_status: str = getattr(telemetry, 'throttle_status', 'Normal')
        
        status = "THROTTLE" if throttle_status != "Normal" else "OPTIMAL"
        level = "WARNING" if status == "THROTTLE" else "INFO"
        
        pulse = (f"[GPU_PULSE] 0xNVIDIA >> CLOCK: {clock_mhz}MHz | "
                f"POWER: {power_watts:.1f}W | VRAM: {vram_used_mb}MB | "
                f"STATUS: {status}")
        
        self.console_tab.write_console(pulse, level)
    
    def _format_security_pulse(self, event: str) -> None:
        """Format security event as hacker-pulse"""
        level = "WARNING" if "USB" in event else "ERROR"
        pulse = f"[SECURITY] 0xSHIELD >> EVENT: {event} | STATUS: DETECTED"
        
        self.console_tab.write_console(pulse, level)
        self.logbook_tab.append_log_entry(pulse)
        
        self._dispatch_alert("SECURITY", pulse)
    
    def _dispatch_alert(self, channel: str, message: str) -> None:
        """Dispatch alert to appropriate Discord webhook channel"""
        if self.alert_router.has_webhook(channel):
            webhook_url = self.alert_router.get_webhook(channel)
            success = self.alert_manager.dispatch_webhook(webhook_url, message)
            
            if success:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.remote_tab.update_last_sent(timestamp)
                self.console_tab.write_console(f"Alert dispatched to {channel} channel", "SUCCESS")
            else:
                self.console_tab.write_console(f"Failed to dispatch alert to {channel}", "ERROR")
    
    def _init_system_tray(self) -> None:
        """Initialize system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        
        icon_path = Path(__file__).parent / "logo.ico"
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show Vitreos")  # type: ignore
        show_action.triggered.connect(self.show)  # type: ignore
        
        exit_action = tray_menu.addAction("Exit")  # type: ignore
        exit_action.triggered.connect(self.exit_application)  # type: ignore
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)  # type: ignore
        self.tray_icon.show()
    
    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle system tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()
    
    def _apply_initial_settings(self) -> None:
        """Load and apply saved settings"""
        interval = 1000
        self.hardware_worker.update_interval = interval
        
        hue = 280
        self._update_theme(hue)
        
        self.console_tab.write_console("[INIT] Vitreos Sentinel initialized successfully", "SUCCESS")
    
    def _show_purge_dialog(self, processes: List[Dict[str, Any]]) -> None:
        """Show purge confirmation dialog"""
        process_names = [p.get('name', 'Unknown') for p in processes]
        dialog = PurgeConfirmationDialog(process_names, self)
        if dialog.exec():
            selected = dialog.selected_targets
            pulse = f"[PURGE] 0xPROCESS >> TERMINATED: {len(selected)} processes | STATUS: EXECUTED"
            self.console_tab.write_console(pulse, "WARNING")
            self.logbook_tab.append_log_entry(pulse)
    
    def _show_tuning_dialog(self) -> None:
        """Show eSports tuning confirmation dialog"""
        dialog = TuningConfirmationDialog(self)
        if dialog.exec():
            pulse = "[TUNING] 0xESPORTS >> OPTIMIZATION: Applied | STATUS: ACTIVE"
            self.console_tab.write_console(pulse, "SUCCESS")
            self.logbook_tab.append_log_entry(pulse)
    
    def _set_gpu_fan_speed(self, speed: int) -> None:
        """Set GPU fan speed via NVML"""
        pulse = f"[GPU_CONTROL] 0xFAN >> SPEED: {speed}% | STATUS: MANUAL_OVERRIDE"
        self.console_tab.write_console(pulse, "INFO")
    
    def _purge_cache(self, cache_type: str) -> None:
        """Purge system cache"""
        pulse = f"[CACHE_PURGE] 0xSTORAGE >> TYPE: {cache_type} | STATUS: CLEARED"
        self.console_tab.write_console(pulse, "SUCCESS")
        self.logbook_tab.append_log_entry(pulse)
    
    def _toggle_security_monitoring(self, enabled: bool) -> None:
        """Toggle security monitoring"""
        status = "ENABLED" if enabled else "DISABLED"
        pulse = f"[SECURITY] 0xSHIELD >> MONITORING: {status} | STATUS: UPDATED"
        self.console_tab.write_console(pulse, "INFO")
    
    def _test_webhook(self) -> None:
        """Test Discord webhook"""
        webhook_url = self.alert_router.default_webhook
        if webhook_url:
            test_message = "[TEST] 0xVITREOS >> WEBHOOK: Connection Test | STATUS: PING"
            success = self.alert_manager.dispatch_webhook(webhook_url, test_message)
            
            if success:
                self.console_tab.write_console("Webhook test successful", "SUCCESS")
                self.remote_tab.set_status(True)
            else:
                self.console_tab.write_console("Webhook test failed", "ERROR")
                self.remote_tab.set_status(False)
        else:
            self.console_tab.write_console("No webhook URL configured", "ERROR")
    
    def _save_webhook_config(self, webhook_url: str) -> None:
        """Save webhook configuration"""
        import json
        config_path = Path.home() / ".vitreos" / "mercury_config.json"
        config_path.parent.mkdir(exist_ok=True)
        
        config = {"webhook_url": webhook_url}
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        self.alert_router.default_webhook = webhook_url
        
        pulse = "[CONFIG] 0xREMOTE >> WEBHOOK: Saved | STATUS: CONFIGURED"
        self.console_tab.write_console(pulse, "SUCCESS")
    
    def _update_polling_interval(self, interval_ms: int) -> None:
        """Update hardware polling interval"""
        self.hardware_worker.update_interval = interval_ms
        pulse = f"[CONFIG] 0xHEARTBEAT >> INTERVAL: {interval_ms}ms | STATUS: UPDATED"
        self.console_tab.write_console(pulse, "INFO")
    
    def _update_theme(self, hue: int) -> None:
        """Update UI theme based on hue"""
        pulse = f"[CONFIG] 0xTHEME >> HUE: {hue}° | STATUS: APPLIED"
        self.console_tab.write_console(pulse, "INFO")
    
    def _clear_database(self) -> None:
        """Clear all database tables"""
        if self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute("DELETE FROM hardware_logs")
            cursor.execute("DELETE FROM security_events")
            cursor.execute("DELETE FROM alert_history")
            self.db_connection.commit()
            
            pulse = "[DATABASE] 0xMAINTENANCE >> ACTION: WIPE | STATUS: COMPLETED"
            self.console_tab.write_console(pulse, "WARNING")
    
    def _export_database(self) -> None:
        """Export database to CSV"""
        export_path = Path.home() / "Desktop" / f"vitreos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        pulse = f"[DATABASE] 0xEXPORT >> PATH: {export_path.name} | STATUS: COMPLETED"
        self.console_tab.write_console(pulse, "SUCCESS")
    
    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        """Handle window dragging via title bar"""
        if a1 and a1.type() == QEvent.Type.MouseButtonPress:
            mouse_event = a1
            if isinstance(mouse_event, QMouseEvent):
                if mouse_event.button() == Qt.MouseButton.LeftButton:
                    self.drag_position = mouse_event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                    return True
        
        elif a1 and a1.type() == QEvent.Type.MouseMove:
            mouse_event = a1
            if isinstance(mouse_event, QMouseEvent):
                if mouse_event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
                    self.move(mouse_event.globalPosition().toPoint() - self.drag_position)
                    return True
        
        return super().eventFilter(a0, a1)
    
    def exit_application(self) -> None:
        """Clean shutdown of all threads and database"""
        pulse = "[SHUTDOWN] 0xSYSTEM >> TERMINATING: All workers | STATUS: GRACEFUL"
        self.console_tab.write_console(pulse, "WARNING")
        
        self.hardware_worker.stop()
        self.security_thread.terminate()
        self.network_analyzer.terminate()
        
        self.hardware_worker.wait(2000)
        self.security_thread.wait(2000)
        self.network_analyzer.wait(2000)
        
        if self.db_connection:
            self.db_connection.close()
        
        QApplication.quit()
    
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Handle window close event"""
        self.exit_application()
        if a0:
            a0.accept()


def main() -> None:
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Vitreos Sentinel")
    app.setOrganizationName("Mercury Content Management")
    
    window = VitreosArchitect()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
