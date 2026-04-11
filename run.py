#!/usr/bin/env python3
"""
Vitreos V3 - Application Entry Point
Launch the Vitreos hardware monitoring application
"""

# Global Debug Flag
DEBUG_MODE = True

if __name__ == "__main__":
    from src.vitreos_main_v3 import main
    main()
