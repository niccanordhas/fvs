"""
main.py
"""

import sys
from PyQt5.QtWidgets import QApplication

from src.app import FlutterVersionSwitcher


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlutterVersionSwitcher()
    window.show()
    sys.exit(app.exec_())
