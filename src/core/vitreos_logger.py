"""
Vitreos Logging System - Production-Grade Silent Boot
Replaces print() with structured logging that can be toggled via DEBUG_MODE
"""

import os
from typing import Optional
from datetime import datetime

# Global debug mode (set via environment variable or config)
DEBUG_MODE = os.getenv('VITREOS_DEBUG', 'false').lower() == 'true'

# Log levels
class LogLevel:
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    CRITICAL = 4

# Current log level (only logs at or above this level are printed)
CURRENT_LOG_LEVEL = LogLevel.DEBUG if DEBUG_MODE else LogLevel.ERROR


def v_print(msg: str, level: int = LogLevel.INFO, prefix: str = "VITREOS") -> None:
    """
    Vitreos print - structured logging with level filtering.
    
    Args:
        msg: Log message
        level: Log level (DEBUG, INFO, WARN, ERROR, CRITICAL)
        prefix: Log prefix (default: VITREOS)
    
    Examples:
        v_print("Telemetry started", LogLevel.INFO)
        v_print("GPU init failed", LogLevel.ERROR)
    """
    if level >= CURRENT_LOG_LEVEL:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        level_str = {
            LogLevel.DEBUG: "DEBUG",
            LogLevel.INFO: "INFO",
            LogLevel.WARN: "WARN",
            LogLevel.ERROR: "ERROR",
            LogLevel.CRITICAL: "CRITICAL",
        }.get(level, "INFO")
        
        print(f"[{timestamp}] [{prefix}] [{level_str}] {msg}")


def v_debug(msg: str, prefix: str = "VITREOS") -> None:
    """Debug-level log (only shown when DEBUG_MODE=true)"""
    v_print(msg, LogLevel.DEBUG, prefix)


def v_info(msg: str, prefix: str = "VITREOS") -> None:
    """Info-level log"""
    v_print(msg, LogLevel.INFO, prefix)


def v_warn(msg: str, prefix: str = "VITREOS") -> None:
    """Warning-level log"""
    v_print(msg, LogLevel.WARN, prefix)


def v_error(msg: str, prefix: str = "VITREOS") -> None:
    """Error-level log"""
    v_print(msg, LogLevel.ERROR, prefix)


def v_critical(msg: str, prefix: str = "VITREOS") -> None:
    """Critical-level log"""
    v_print(msg, LogLevel.CRITICAL, prefix)


def set_debug_mode(enabled: bool) -> None:
    """Enable or disable debug mode at runtime"""
    global DEBUG_MODE, CURRENT_LOG_LEVEL
    DEBUG_MODE = enabled
    CURRENT_LOG_LEVEL = LogLevel.DEBUG if enabled else LogLevel.ERROR
    v_info(f"Debug mode {'ENABLED' if enabled else 'DISABLED'}")


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return DEBUG_MODE


__all__ = [
    'v_print', 'v_debug', 'v_info', 'v_warn', 'v_error', 'v_critical',
    'set_debug_mode', 'is_debug_mode', 'LogLevel', 'DEBUG_MODE'
]
