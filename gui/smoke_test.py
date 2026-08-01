#!/usr/bin/env python3
"""Smoke test da GUI (offscreen). Sai com código 0 se a janela abrir."""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import TaskRunner
from main_window import MainWindow
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication


def main() -> int:
    app = QApplication([])
    runner = TaskRunner(dry_run=True)
    window = MainWindow(runner)
    window.show()
    QTimer.singleShot(800, app.quit)
    app.exec()
    print("smoke OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
