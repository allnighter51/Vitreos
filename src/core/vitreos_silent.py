"""
Vitreos Silent Terminal - Production-Grade Console Control
Redirects stdout to null device unless DEBUG_MODE is active
"""

import sys
import os
from typing import Optional


class SilentTerminal:
    """
    Redirects stdout to nothing unless DEBUG_MODE is active.
    This nukes all print() calls across the entire app and dependencies.
    """
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self._original_stdout = sys.__stdout__
        self._original_stderr = sys.__stderr__
    
    def write(self, text: str) -> None:
        """Write to stdout only if debug mode is enabled"""
        if self.debug_mode:
            self._original_stdout.write(text)
    
    def flush(self) -> None:
        """Flush stdout only if debug mode is enabled"""
        if self.debug_mode:
            self._original_stdout.flush()
    
    def enable_debug(self) -> None:
        """Enable debug mode (restore stdout)"""
        self.debug_mode = True
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
    
    def disable_debug(self) -> None:
        """Disable debug mode (silence stdout)"""
        self.debug_mode = False
        sys.stdout = self
        sys.stderr = self


# Global silent terminal instance
_silent_terminal: Optional[SilentTerminal] = None


def initialize_silent_terminal() -> None:
    """
    Initialize silent terminal based on VITREOS_DEBUG environment variable.
    Call this at the very start of main.py before any imports.
    """
    global _silent_terminal
    
    # Check for debug mode via environment variable
    debug_mode = os.getenv("VITREOS_DEBUG", "false").lower() == "true"
    
    _silent_terminal = SilentTerminal(debug_mode)
    
    if not debug_mode:
        # Redirect stdout/stderr to silent terminal
        sys.stdout = _silent_terminal
        sys.stderr = _silent_terminal
        
        # Also suppress Qt warnings in production
        os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    if _silent_terminal:
        return _silent_terminal.debug_mode
    return False


def set_debug_mode(enabled: bool) -> None:
    """Enable or disable debug mode at runtime"""
    if _silent_terminal:
        if enabled:
            _silent_terminal.enable_debug()
        else:
            _silent_terminal.disable_debug()


__all__ = ['initialize_silent_terminal', 'is_debug_mode', 'set_debug_mode', 'SilentTerminal']
