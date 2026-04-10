"""
Vitreos Shield - Active Threat Mitigation Module
Ransomware Honeypot & Login Failure Monitoring
"""
import subprocess
import psutil
import logging
import threading
from pathlib import Path
from typing import Callable, Any, List, Dict, cast
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

win32evtlog: Any = None
win32evtlogutil: Any = None
win32con: Any = None

try:
    import win32evtlog as _win32evtlog
    import win32evtlogutil as _win32evtlogutil
    import win32con as _win32con
    win32evtlog = _win32evtlog
    win32evtlogutil = _win32evtlogutil
    win32con = _win32con
    w32_status = True
except ImportError:
    w32_status = False

logger = logging.getLogger(__name__)


class HoneypotSentinel(FileSystemEventHandler):
    """Monitors honeypot directory for ransomware-like file access patterns."""
    
    def __init__(self, alert_callback: Callable[[str, str, str, List[Dict[str, Any]]], None]) -> None:
        super().__init__()
        self.alert_callback = alert_callback
        self.honeypot_path = Path(r"C:\Users\Public\Documents\~vitreos_cache")
        self.observer: Any = None
        self._setup_honeypot()
    
    def _setup_honeypot(self) -> None:
        """Create honeypot directory with decoy files."""
        try:
            self.honeypot_path.mkdir(parents=True, exist_ok=True)
            
            decoys = [
                ("passwords.txt", "# Confidential System Credentials\nAdmin: [REDACTED]\n"),
                ("financial_data.txt", "Account Numbers:\n1234-5678-9012-3456\n"),
                ("backup_keys.txt", "Recovery Keys:\nBITLOCKER_KEY_2024\n"),
                ("credentials.docx", "Microsoft Office Document Placeholder\n")
            ]
            
            for filename, content in decoys:
                filepath = self.honeypot_path / filename
                if not filepath.exists():
                    filepath.write_text(content, encoding="utf-8")
            
            subprocess.run(['attrib', '+h', str(self.honeypot_path)], capture_output=True)
            logger.info(f"[SHIELD] Honeypot armed at {self.honeypot_path}")
        except Exception as e:
            logger.error(f"[SHIELD] Honeypot setup failed: {e}")
    
    def start(self) -> None:
        """Start monitoring honeypot directory."""
        try:
            self.observer = Observer()
            self.observer.schedule(self, str(self.honeypot_path), recursive=False)
            self.observer.start()
            logger.info("[SHIELD] Honeypot monitoring active")
        except Exception as e:
            logger.error(f"[SHIELD] Failed to start honeypot: {e}")
    
    def stop(self) -> None:
        """Stop monitoring."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """Triggered when honeypot file is modified."""
        if event.is_directory:
            return
        self._handle_breach(str(event.src_path), "MODIFIED")
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        """Triggered when honeypot file is deleted."""
        if event.is_directory:
            return
        self._handle_breach(str(event.src_path), "DELETED")
    
    def _handle_breach(self, filepath: str, action: str) -> None:
        """Handle honeypot breach - identify and terminate malicious process."""
        try:
            filename = Path(filepath).name
            logger.warning(f"[SHIELD] HONEYPOT BREACH: {filename} was {action}")
            
            culprit_pid: Any = None
            culprit_name = "Unknown"
            
            for proc in psutil.process_iter(['pid', 'name', 'open_files']):
                try:
                    open_files = proc.info.get('open_files')
                    if open_files:
                        for file in open_files:
                            if filepath.lower() in file.path.lower():
                                culprit_pid = proc.info['pid']
                                culprit_name = proc.info['name']
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            termination_status = "NOT_FOUND"
            if culprit_pid:
                try:
                    process = psutil.Process(culprit_pid)
                    process.kill()
                    termination_status = "TERMINATED"
                    logger.critical(f"[SHIELD] Killed process {culprit_name} (PID: {culprit_pid})")
                except Exception as e:
                    termination_status = f"FAILED: {e}"
                    logger.error(f"[SHIELD] Failed to kill PID {culprit_pid}: {e}")
            
            fields: List[Dict[str, Any]] = [
                {"name": "File", "value": filename, "inline": True},
                {"name": "Action", "value": action, "inline": True},
                {"name": "Process", "value": culprit_name, "inline": True},
                {"name": "PID", "value": str(culprit_pid) if culprit_pid else "Unknown", "inline": True},
                {"name": "Status", "value": termination_status, "inline": False}
            ]
            
            self.alert_callback(
                "🛡️ RANSOMWARE HONEYPOT TRIGGERED",
                f"Unauthorized access to decoy file detected. Process {termination_status.lower()}.",
                "CRITICAL",
                fields
            )
        except Exception as e:
            logger.error(f"[SHIELD] Breach handler error: {e}")


class LoginSentinel:
    """Monitors Windows Event Log for failed login attempts."""
    
    def __init__(self, alert_callback: Callable[[str, str, str, List[Dict[str, Any]]], None]) -> None:
        self.alert_callback = alert_callback
        self.failure_threshold = 5
        self.time_window = timedelta(minutes=10)
        self.last_check = datetime.now()
        self.running = False
        self.thread: Any = None
    
    def start(self) -> None:
        """Start monitoring login failures."""
        if not w32_status:
            logger.warning("[SHIELD] Win32 libraries not available, login monitoring disabled")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("[SHIELD] Login failure monitoring active")
    
    def stop(self) -> None:
        """Stop monitoring."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self.running:
            try:
                self._check_failed_logins()
            except Exception as e:
                logger.error(f"[SHIELD] Login monitor error: {e}")
            import time
            time.sleep(60)
    
    def _check_failed_logins(self) -> None:
        """Check Windows Security Event Log for Event ID 4625."""
        if not win32evtlog:
            return
            
        try:
            hand = win32evtlog.OpenEventLog(None, "Security")
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            failed_attempts = 0
            cutoff_time = datetime.now() - self.time_window
            
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            for event in events:
                if event.EventID == 4625:
                    event_time = event.TimeGenerated
                    if event_time > cutoff_time:
                        failed_attempts += 1
            
            win32evtlog.CloseEventLog(hand)
            
            if failed_attempts >= self.failure_threshold:
                fields: List[Dict[str, Any]] = [
                    {"name": "Failed Attempts", "value": str(failed_attempts), "inline": True},
                    {"name": "Time Window", "value": f"{self.time_window.seconds // 60} minutes", "inline": True},
                    {"name": "Threshold", "value": str(self.failure_threshold), "inline": True}
                ]
                
                self.alert_callback(
                    "🔐 BRUTE FORCE DETECTED",
                    f"Multiple failed login attempts detected ({failed_attempts} failures).",
                    "CRITICAL",
                    fields
                )
                
                self.last_check = datetime.now()
        except Exception as e:
            logger.error(f"[SHIELD] Failed login check error: {e}")


class VitreosShield:
    """Coordinator for all active threat mitigation systems."""
    
    def __init__(self, alert_callback: Callable[[str, str, str, List[Dict[str, Any]]], None]) -> None:
        self.alert_callback = alert_callback
        self.honeypot = HoneypotSentinel(alert_callback)
        self.login_sentinel = LoginSentinel(alert_callback)
        logger.info("[SHIELD] Vitreos Shield initialized")
    
    def start(self) -> None:
        """Activate all shield components."""
        try:
            self.honeypot.start()
            self.login_sentinel.start()
            logger.info("[SHIELD] All defense systems online")
        except Exception as e:
            logger.error(f"[SHIELD] Failed to start shield: {e}")
    
    def stop(self) -> None:
        """Deactivate all shield components."""
        try:
            self.honeypot.stop()
            self.login_sentinel.stop()
            logger.info("[SHIELD] Shield systems deactivated")
        except Exception as e:
            logger.error(f"[SHIELD] Error stopping shield: {e}")
