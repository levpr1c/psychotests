#!/usr/bin/env python3
"""Entry point for the psychological tests TUI application."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
