"""
Vitreos Sentinel - Tabs Package
Modular tab components for the main application
"""

from .tab_vitals import VitalsTab
from .tab_network import NetworkTab
from .tab_processes import ProcessesTab
from .tab_gpu_pro import GPUProTab
from .tab_storage import StorageTab
from .tab_security import SecurityTab
from .tab_logbook import LogbookTab
from .tab_console import ConsoleTab
from .tab_remote import RemoteTab
from .tab_settings import SettingsTab

__all__ = [
    'VitalsTab',
    'NetworkTab',
    'ProcessesTab',
    'GPUProTab',
    'StorageTab',
    'SecurityTab',
    'LogbookTab',
    'ConsoleTab',
    'RemoteTab',
    'SettingsTab'
]
