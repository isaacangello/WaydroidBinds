#!/usr/bin/env python3
"""Waydroid Binds — GUI (PySide6).

Uso:
    python3 gui/main.py            # modo normal
    python3 gui/main.py --dry-run  # simula os comandos sem executar
"""

import sys
from pathlib import Path

from backend import TaskRunner
from main_window import MainWindow
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv if a != "--dry-run"]

    app = QApplication(args)
    app.setApplicationName("Waydroid Binds")
    app.setApplicationDisplayName("Waydroid Binds")
    app.setOrganizationName("WaydroidBinds")

    icon_path = Path(__file__).resolve().parent / "resources" / "waydroid-binds.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    runner = TaskRunner(dry_run=dry_run)
    window = MainWindow(runner)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
