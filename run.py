#!/usr/bin/env python3
import sys
import os

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main import main


if __name__ == "__main__":
    main()


