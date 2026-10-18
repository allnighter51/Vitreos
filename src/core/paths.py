"""
Vitreos Core Path Resolution Helper
Provides unified path resolution across development and PyInstaller frozen executable environments.
Strictly adheres to the Dumb UI Doctrine (pathlib only, zero metrics math/formatting).
"""

import os
import shutil
import sys
from pathlib import Path


def get_bundle_dir() -> Path:
    """
    Return the directory containing read-only bundled resources.
    In a PyInstaller frozen bundle, returns Path(sys._MEIPASS).
    In development mode, returns the project root Path.
    """
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass is not None:
            return Path(meipass).resolve()
        return Path(sys.executable).parent.resolve()
    return Path(__file__).resolve().parents[2]


def get_app_dir() -> Path:
    """
    Return the persistent application directory for reading/writing mutable state.
    In a PyInstaller frozen bundle, returns Path(sys.executable).parent.
    In development mode, returns the project root Path.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.resolve()
    return Path(__file__).resolve().parents[2]


def ensure_app_dirs() -> None:
    """
    Ensure mutable runtime directories ('data/' and 'config/') exist in get_app_dir().
    On first launch of a frozen build, seed default config files from get_bundle_dir() / 'config'
    into get_app_dir() / 'config' if they do not yet exist.
    """
    app_dir = get_app_dir()
    bundle_dir = get_bundle_dir()

    data_dir = app_dir / "data"
    config_dir = app_dir / "config"

    data_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    # Seed default config files if missing in app_dir
    bundle_config = bundle_dir / "config"
    if bundle_config.exists() and bundle_config.is_dir():
        for item in bundle_config.glob("*.json"):
            target_file = config_dir / item.name
            if not target_file.exists():
                try:
                    shutil.copy2(item, target_file)
                except Exception as e:
                    print(f"[PATH] Warning: Could not copy default config {item.name}: {e}")
