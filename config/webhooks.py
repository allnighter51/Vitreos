"""Webhook configuration loader for Vitreos"""

import json
from pathlib import Path
from typing import Dict, Any


def load_webhook_configs() -> Dict[str, Any]:
    """Load webhook configurations from webhooks.json"""
    webhooks_path = Path(__file__).parent / "webhooks.json"
    
    default_webhooks = {
        "channels": {
            "SECURITY": "",
            "THERMALS": "",
            "SYSTEM": "",
            "NETWORK": "",
            "STORAGE": ""
        },
        "default_webhook": "",
        "enable_alerts": True
    }
    
    try:
        if webhooks_path.exists():
            with open(webhooks_path, 'r', encoding='utf-8') as f:
                loaded_webhooks = json.load(f)
                # Merge with defaults
                for key in default_webhooks:
                    if key not in loaded_webhooks:
                        loaded_webhooks[key] = default_webhooks[key]
                return loaded_webhooks
        else:
            # Create default webhooks file
            with open(webhooks_path, 'w', encoding='utf-8') as f:
                json.dump(default_webhooks, f, indent=2)
            return default_webhooks
    except Exception as e:
        print(f"Error loading webhooks: {e}")
        return default_webhooks


def save_webhook_configs(webhooks: Dict[str, Any]) -> bool:
    """Save webhook configurations to webhooks.json"""
    webhooks_path = Path(__file__).parent / "webhooks.json"
    
    try:
        with open(webhooks_path, 'w', encoding='utf-8') as f:
            json.dump(webhooks, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving webhooks: {e}")
        return False


def some_function():
    """Placeholder function referenced in src/main.py"""
    pass
