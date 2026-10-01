"""
KyteRename — 入口程式
"""
import sys
import os
from pathlib import Path

# 將專案根目錄加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from config.settings import SettingsManager
from ui.styles import get_theme_stylesheet
from ui.main_window import MainWindow

def main():
    # 支援 High DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("KyteRename")
    app.setOrganizationName("KyteSuite")
    ico_path = PROJECT_ROOT / "assets" / "icon.ico"
    if ico_path.exists():
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(ico_path)))
    settings = SettingsManager()
    app.setStyleSheet(get_theme_stylesheet(settings.is_dark()))

    window = MainWindow(initial_paths=sys.argv[1:])
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
