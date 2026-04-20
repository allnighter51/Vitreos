#!/usr/bin/env python3
"""
Vitreos V3 - Production Entry Point
Silent boot with global stdout redirect
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Silent terminal removed - using standard logger
from src.main import main

if __name__ == "__main__":
    main()
