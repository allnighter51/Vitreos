import threading
import time
import json
import warnings
import importlib
import psutil
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List

import os # Added for path manipulation
import sys # Added for sys.path manipulation

# Add project root to sys.path to allow importing @workspace modules
# Assumes src/main.py is run from the project root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the new config loaders
try:
    import requests
    from requests import Response
except ImportError:
    requests = None  # type: ignore
    Response = None  # type: ignore

try:
    import win32evtlog  # type: ignore
    from win32evtlog import EVENTLOG_FORWARDS_READ, EVENTLOG_SEQUENTIAL_READ, EVENTLOG_BACKWARDS_READ, EVENT_ID_LOGON_FAILURE, EVENT_ID_LOGON_TYPE_INTERACTIVE  # type: ignore
except ImportError:
    win32evtlog = None  # type: ignore

from config.settings import load_settings as load_app_settings  # type: ignore
from config.webhooks import load_webhook_configs  # type: ignore


class DiscordBridge:
    """Discord message updater with PATCH-first strategy."""

    def __init__(self, webhook_url: str, settings_path: str):
        self.webhook_url = webhook_url
        self.settings_path = settings_path
        self.current_message_id = self._load_message_id()

    def _load_message_id(self) -> Optional[str]:
        """Load current Discord message ID from settings file."""
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data: Dict[str, Any] = json.load(f)
                discord_data: Dict[str, Any] = data.get('discord', {})
                message_id: Optional[str] = discord_data.get('message_id')
                if message_id:
                    print(f"Loaded existing Discord message ID: {message_id}")
                return message_id
        except FileNotFoundError:
            print(f"Settings file not found at {self.settings_path}. Cannot load message ID.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.settings_path}. Cannot load message ID.")
        except Exception as e: # Catch other potential file I/O errors
            print(f"An unexpected error occurred while loading message ID: {e}")
        
        print("No Discord message ID found or loaded. Will attempt to POST a new message.")
        return None

    # This method is for saving the message ID to the settings file
    def save_message_id(self, new_id: str) -> None:
        """Save updated message ID back to settings file."""
        try:
            with open(self.settings_path, 'r') as f:
                data: Dict[str, Any] = json.load(f)
            
            if 'discord' not in data:
                data['discord'] = {}
            data['discord']['message_id'] = new_id
            
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.current_message_id = new_id
            print(f"Saved new Discord message ID: {new_id}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Failed to save message ID to settings file {self.settings_path}: {e}")
        except Exception as e: # Catch other potential file I/O errors
            print(f"An unexpected error occurred while saving message ID: {e}")

    def _post_new_embed(self, embed_data: Dict[str, Any]) -> Optional[str]:
        """POST a new message and return its ID."""
        if not requests:
            return None
        try:
            response: Response = requests.post(
                self.webhook_url,
                json={'embeds': [embed_data]}
            )
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            response_data: Dict[str, Any] = response.json()
            new_id: str = response_data['id']
            self.save_message_id(new_id)
            return new_id
        except requests.exceptions.RequestException as e:
            print(f"POST failed: {e}")
        except json.JSONDecodeError:
            print(f"Failed to decode JSON response after POST.")
        return None

    def update_embed(self, embed_data: Dict[str, Any]) -> Optional[str]:
        """PATCH an existing message or POST a new one if no ID exists/PATCH fails."""
        if not requests:
            print("Requests library not available. Cannot send Discord updates.")
            return None

        if self.current_message_id:
            try:
                response: Response = requests.patch(
                    f"{self.webhook_url}/messages/{self.current_message_id}",
                    json={'embeds': [embed_data]}
                )
                response.raise_for_status()
                return self.current_message_id # PATCH successful, ID remains the same
            except requests.exceptions.RequestException as e:
                print(f"PATCH failed (message ID {self.current_message_id}): {e}. Attempting to POST a new message.")
                self.current_message_id = None # Invalidate current ID
        
        # If no current_message_id or PATCH failed, try to POST a new message
        return self._post_new_embed(embed_data)


# Global state
heartbeat_event: threading.Event = threading.Event()
discord_bridge: Optional['DiscordBridge'] = None
last_security_event_time: float = 0.0

def heartbeat_loop(bridge: Optional['DiscordBridge']) -> None:
    """Main monitoring loop with patched Discord updates."""
    global discord_bridge
    
    print("Initializing monitors...")
    
    discord_bridge = bridge # Assign the passed bridge instance
    
    # Initial embed build (needs initial CPU for description)
    cpu_initial = psutil.cpu_percent(interval=None)
    initial_embed = _build_initial_embed(cpu_initial)
    last_update_time = time.time() - 3.0 # Ensure immediate first update
    
    while heartbeat_event.is_set():
        try:
            current_time = time.time()
            
            if (current_time - last_update_time) >= 3.0: # Removed undefined 'first_run'
                cpu_pct = psutil.cpu_percent(interval=None)
                # Build embed with latest stats
                embed_data = _build_embed(initial_embed, current_time, cpu_pct)
                new_id = discord_bridge.update_embed(embed_data) if discord_bridge else None
                last_update_time = current_time
                
                if new_id: # This condition was previously `if not first_run and new_id:`
                    print(f"Updated Discord heartbeat at {datetime.now().strftime('%H:%M:%S')}")
            
            # CPU monitoring check (every 3s via heartbeat)
            if 'embed_data' in locals() and embed_data is not None:
                _check_cpu_threshold(cpu_pct, embed_data)
            
        except Exception as e:
            print(f"Loop error: {e}")
        
        time.sleep(0.1)


def _build_initial_embed(cpu_pct: float) -> Dict[str, Any]:
    """Create the initial Discord embed structure."""
    return {
        "title": "Vitreos System Monitor",
        # NOTE: The original code had a redundant psutil.cpu_percent call here.
        # Using the passed cpu_pct for consistency.
        "description": f"<@everyone> Live Feed Started | CPU: {cpu_pct:.1f}%",
        "color": 0x00FF00,
        "fields": [
            # NOTE: The original code had a redundant psutil.cpu_percent call here.
            # Using the passed cpu_pct for consistency.
            {"name": "CPU Usage", "value": f"{cpu_pct:.1f}%", "inline": True},
            {"name": "VRAM Usage", "value": "Loading...", "inline": True},
            {"name": "GPU Temp", "value": "Loading...", "inline": True},
            {"name": "Security Events", "value": f"No events (last: {datetime.now()})", "inline": False}
        ],
        "timestamp": datetime.now(UTC).isoformat(),
        "footer": {
            "text": f"Vitreos • Last update: {datetime.now().strftime('%H:%M:%S')}"
        }
    }


def _build_embed(initial: Dict[str, Any], current_time: float, cpu_pct: float) -> Dict[str, Any]:
    """Build full embed with real-time data."""
    gpu: Dict[str, str] = _get_gpu_stats_bundle()

    return {
        "title": "Vitreos System Monitor",
        "description": f"<@everyone> Live Feed Active | CPU: {cpu_pct:.1f}%",
        "color": initial.get('color', 0x00FF00),
        "fields": [
            {"name": "CPU Usage", "value": f"{cpu_pct:.1f}%", "inline": True},
            {"name": "VRAM Usage", "value": gpu["vram"], "inline": True},
            {"name": "GPU Temp (°C)", "value": gpu["temp"], "inline": True},
            {"name": "GPU Fan (%)", "value": gpu["fan"], "inline": True},
            {"name": "Security Events", "value": get_security_status(), "inline": False}
        ], # The timestamp should be an ISO 8601 string
        "timestamp": datetime.now(UTC).isoformat(),
        "footer": {
            "text": f"Vitreos • Last update: {datetime.now().strftime('%H:%M:%S')}"
        }
    }


def _get_gpu_stats_bundle() -> Dict[str, str]:
    """Collect GPU stats in one NVML session to reduce overhead."""
    result: Dict[str, str] = {"vram": "N/A", "temp": "N/A", "fan": "N/A"}
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="The pynvml package is deprecated.*",
                category=FutureWarning,
            )
            pynvml = importlib.import_module("pynvml")  # type: ignore
        pynvml.nvmlInit()  # type: ignore
        handle: Any = pynvml.nvmlDeviceGetHandleByIndex(0)  # type: ignore

        info: Any = pynvml.nvmlDeviceGetMemoryInfo(handle)  # type: ignore
        percent: float = (info.used / info.total * 100) if info.total > 0 else 0

        temp: int = pynvml.nvmlDeviceGetTemperature(handle, 0)  # type: ignore
        fan: int = pynvml.nvmlDeviceGetFanSpeed(handle)  # type: ignore

        result["vram"] = f"{percent:.1f}%"
        result["temp"] = f"{temp:.1f}°C"
        result["fan"] = f"{fan}%" if fan else "N/A"
    except Exception:
        return result
    finally:
        try:
            import pynvml  # type: ignore
            pynvml.nvmlShutdown()  # type: ignore
        except Exception:
            pass # Ignore errors during shutdown
    return result


def _check_security_events() -> None:
    """
    Checks Windows Event Log for failed login attempts.
    Updates last_security_event_time if an event is found.
    """
    global last_security_event_time

    if not win32evtlog:
        # print("win32evtlog not available. Security monitoring disabled.") # Too chatty
        return

    try:
        # Open the Security event log
        hand: Any = win32evtlog.OpenEventLog(None, "Security")  # type: ignore
        flags: int = EVENTLOG_BACKWARDS_READ | EVENTLOG_SEQUENTIAL_READ  # type: ignore
        
        # Read up to the last 100 records (adjust as needed)
        events: List[Any] = win32evtlog.ReadEventLog(hand, flags, 0, 100)  # type: ignore
        
        for event in events:
            # Event ID 4625 is for failed logins
            if event.EventID == 4625:  # type: ignore
                # Check if it's an interactive login failure (Type 2, 10, 11)
                # This part requires parsing event.StringInserts, which is more complex.
                # For simplicity, we'll just mark any 4625 as a security event for now.
                last_security_event_time = time.time()
                print(f"[SECURITY ALERT] Failed login attempt detected at {datetime.fromtimestamp(last_security_event_time).strftime('%H:%M:%S')}")
                break # Only need to find one recent event
        win32evtlog.CloseEventLog(hand)  # type: ignore
    except Exception as e:
        print(f"[ERROR] Failed to check security events: {e}")

def get_security_status() -> str:
    """Check security event status."""
    global last_security_event_time
    
    current = datetime.now().isoformat()
    
    if last_security_event_time == 0.0:
        return f"No events (last: {current})"
    
    elapsed = time.time() - last_security_event_time
    minutes = int(elapsed / 60)
    seconds = int(elapsed % 60)
    
    return f"{minutes}m {seconds}s since last event | Last: {datetime.fromtimestamp(last_security_event_time).strftime('%H:%M:%S')}"


def _check_cpu_threshold(cpu_pct: float, embed_data: Dict[str, Any]) -> None:
    """Apply color logic and check thresholds."""
    global heartbeat_event
    
    safe: int = 0x00FF00
    warning: int = 0xFFA500
    critical: int = 0xFF0000
    alert_triggered: bool = False
    
    if cpu_pct > 90:
        embed_data['description'] = f"<@everyone> CRITICAL: High CPU usage detected: {cpu_pct:.1f}%"
        alert_triggered = True
    
    if last_security_event_time != 0.0:
        if not alert_triggered: # Avoid overwriting CPU alert if both happen
            embed_data['description'] = f"<@everyone> CRITICAL: Security Event detected at {datetime.fromtimestamp(last_security_event_time).strftime('%H:%M:%S')}"
        else:
            embed_data['description'] += f" | Security Event detected at {datetime.fromtimestamp(last_security_event_time).strftime('%H:%M:%S')}"
        alert_triggered = True

    if alert_triggered:
        embed_data['color'] = critical
        embed_data['description'] += f" • Last update: {datetime.now().strftime('%H:%M:%S')}"

def start_monitors() -> None:
    """Entry point for Vitreos monitoring service."""
    
    # Load application settings and webhook configurations
    # NOTE: As currently implemented in @workspace/config/settings.py and @workspace/config/webhooks.py,
    # these functions expect 'settings.json' and 'webhooks.json' to be in the current working directory.
    # If your config files are in a 'config/' subdirectory, these calls will likely fail to find them
    # unless the CWD is changed or the config modules are modified.
    app_settings: Dict[str, Any] = load_app_settings()
    webhook_configs: Dict[str, Any] = load_webhook_configs()

    # Determine the Discord webhook URL from app_settings (prioritizing nested then flat)
    discord_data: Dict[str, Any] = app_settings.get('discord', {})
    discord_webhook_url: str = (
        discord_data.get('webhook_url', '')
        or app_settings.get('webhook_url', '')
    )

    # The path for DiscordBridge to save its message_id.
    # This path is relative to the project root, where src/main.py is expected to be run from.
    discord_bridge_settings_path: str = os.path.join(project_root, 'config', 'settings.json')

    discord_bridge_instance: Optional[DiscordBridge] = None
    if discord_webhook_url:
        discord_bridge_instance = DiscordBridge(discord_webhook_url, discord_bridge_settings_path)
    
    print("Vitreos Monitoring Service Starting...")
    print(f"Settings file for message ID: {discord_bridge_settings_path}")
    print(f"Webhook: {discord_webhook_url[:50]}..." if discord_webhook_url else "Webhook: Not configured")
    print("-" * 60)
    
    heartbeat_event.set() # Set the event before starting the thread
    t: threading.Thread = threading.Thread(target=heartbeat_loop, args=(discord_bridge_instance,)) # Pass only the bridge instance
    t.daemon = True
    t.start()
    
    print("Heartbeat thread started. Press Ctrl+C to stop.")
    print("-" * 60)
    
    # Keep main thread alive for CLI operations
    try:
        while heartbeat_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    finally:
        heartbeat_event.clear()


def run_cli_loop() -> None:
    """CLI-compatible loop (press Ctrl+C to exit)."""
    start_monitors()


# CLI entry point
if __name__ == "__main__":
    run_cli_loop()
