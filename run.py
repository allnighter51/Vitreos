#!/usr/bin/env python3
"""
Vitreos V3 - Production Entry Point
Silent boot with global stdout redirect
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.core.vitreos_silent import initialize_silent_terminal
initialize_silent_terminal()

from src.main import main

if __name__ == "__main__":
    main()
