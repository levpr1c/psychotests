#!/usr/bin/env python3
"""Психологические тесты — TUI приложение."""

from src.app import PsychoApp
from src.models.database import init_db


def main():
    init_db()
    app = PsychoApp()
    app.run()


if __name__ == "__main__":
    main()
