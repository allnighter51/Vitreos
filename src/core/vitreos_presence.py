"""
Vitreos Discord Rich Presence Engine
Phase 2: Live hardware stats in Discord with Tournament Mode
"""

import time
from typing import Dict, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal

try:
    from pypresence import Presence
    PYPRESENCE_AVAILABLE = True
except ImportError:
    PYPRESENCE_AVAILABLE = False
    print("[PRESENCE] pypresence not available - Discord Rich Presence disabled")


class PresenceWorker(QThread):
    """
    Background thread for Discord Rich Presence updates.
    Updates every 15 seconds to avoid rate limits.
    """
    
    status_changed = pyqtSignal(bool)  # Emits connection status
    error_occurred = pyqtSignal(str)  # Error messages
    
    def __init__(self, client_id: str = "1234567890123456789"):
        super().__init__()
        
        self.running = False
        self.connected = False
        self.client_id = client_id
        self.rpc: Optional[Presence] = None
        
        # Configuration
        self.show_hardware = True
        self.show_active_tab = True
        self.tournament_mode = False
        
        # Current state
        self.current_tab = "VITALS"
        self.cpu_usage = 0
        self.gpu_temp = 0
        self.cpu_temp = 0
        self.vram_used = 0.0
        self.vram_total = 12.0
    
    def run(self) -> None:
        """Main presence update loop"""
        if not PYPRESENCE_AVAILABLE:
            self.error_occurred.emit("pypresence not installed")
            return
        
        self.running = True
        
        # Initialize RPC connection
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            self.status_changed.emit(True)
            print("[PRESENCE] Connected to Discord")
        except Exception as e:
            self.error_occurred.emit(f"Connection failed: {e}")
            self.running = False
            return
        
        # Update loop (every 15 seconds)
        while self.running:
            try:
                self._update_presence()
                time.sleep(15.0)
            except Exception as e:
                self.error_occurred.emit(f"Update error: {e}")
                time.sleep(15.0)
    
    def stop(self) -> None:
        """Stop the presence worker gracefully"""
        self.running = False
        
        if self.rpc and self.connected:
            try:
                self.rpc.close()
                self.connected = False
                self.status_changed.emit(False)
                print("[PRESENCE] Disconnected from Discord")
            except:
                pass
    
    def _update_presence(self) -> None:
        """Update Discord Rich Presence with current state"""
        if not self.rpc or not self.connected:
            return
        
        # Build details string
        if self.show_hardware:
            details = f"CPU: {self.cpu_usage}% | GPU: {self.gpu_temp}°C"
        else:
            details = "Monitoring System"
        
        # Build state string
        if self.show_active_tab:
            state = f"Analyzing: {self.current_tab}"
        else:
            state = "Hardware Sentinel"
        
        # Tournament Mode: CCE Branding
        if self.tournament_mode:
            large_image = "cce_logo"
            large_text = "Competitive Cyber Esports"
            small_image = "vitreos_icon"
            small_text = "Vitreos V3"
            buttons = [
                {"label": "Match Codes", "url": "https://cce.gg/dashboard"},
                {"label": "Get Vitreos", "url": "https://github.com/mercurycontentmgmt-svg/vitreos"}
            ]
        else:
            large_image = "vitreos_logo"
            large_text = "Vitreos System Sentinel"
            small_image = "hardware_icon"
            small_text = f"VRAM: {self.vram_used:.1f}/{self.vram_total:.1f}GB"
            buttons = [
                {"label": "Get Vitreos", "url": "https://github.com/mercurycontentmgmt-svg/vitreos"}
            ]
        
        try:
            self.rpc.update(
                details=details,
                state=state,
                large_image=large_image,
                large_text=large_text,
                small_image=small_image,
                small_text=small_text,
                buttons=buttons,
                start=int(time.time())
            )
        except Exception as e:
            print(f"[PRESENCE] Update failed: {e}")
    
    def update_hardware_stats(self, data: Dict[str, Any]) -> None:
        """Update hardware stats from telemetry data"""
        self.cpu_usage = int(data.get('cpu', {}).get('totalLoad', 0))
        self.gpu_temp = int(data.get('gpu', {}).get('temp', 0))
        self.cpu_temp = int(data.get('cpu', {}).get('temp', 0))
        self.vram_used = data.get('gpu', {}).get('vramUsed', 0.0)
        self.vram_total = data.get('gpu', {}).get('vramTotal', 12.0)
    
    def set_active_tab(self, tab_name: str) -> None:
        """Update active tab name"""
        self.current_tab = tab_name
    
    def set_config(self, show_hardware: bool, show_active_tab: bool, tournament_mode: bool) -> None:
        """Update presence configuration"""
        self.show_hardware = show_hardware
        self.show_active_tab = show_active_tab
        self.tournament_mode = tournament_mode


__all__ = ['PresenceWorker']


