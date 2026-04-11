"""Configuration settings loader for Vitreos"""

import json
import os
from pathlib import Path
from typing import Dict, Any


def load_settings() -> Dict[str, Any]:
    """Load application settings from settings.json"""
    settings_path = Path(__file__).parent / "settings.json"
    
    default_settings = {
        "discord": {
            "webhook_url": "",
            "message_id": ""
        },
        "monitoring": {
            "polling_interval_ms": 2000,
            "enable_gpu": True,
            "enable_security": True,
            "enable_network": True
        },
        "theme": {
            "hue": 280,
            "dark_mode": True
        }
    }
    
    try:
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key in default_settings:
                    if key not in loaded_settings:
                        loaded_settings[key] = default_settings[key]
                return loaded_settings
        else:
            # Create default settings file
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, indent=2)
            return default_settings
    except Exception as e:
        print(f"Error loading settings: {e}")
        return default_settings


def save_settings(settings: Dict[str, Any]) -> bool:
    """Save application settings to settings.json"""
    settings_path = Path(__file__).parent / "settings.json"
    
    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


