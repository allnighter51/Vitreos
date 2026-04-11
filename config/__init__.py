"""Vitreos configuration package"""

from .settings import load_settings, save_settings
from .webhooks import load_webhook_configs, save_webhook_configs

__all__ = ['load_settings', 'save_settings', 'load_webhook_configs', 'save_webhook_configs']


