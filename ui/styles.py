"""
KyteRename - Theme Styles (深色 Dark 與 淺色 Light 完整質感樣式系統)
"""
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ARROW_UP_DARK = str(ASSETS_DIR / "arrow_up.png").replace("\\", "/")
ARROW_UP_DARK_HOVER = str(ASSETS_DIR / "arrow_up_hover.png").replace("\\", "/")
ARROW_DOWN_DARK = str(ASSETS_DIR / "arrow_down.png").replace("\\", "/")
ARROW_DOWN_DARK_HOVER = str(ASSETS_DIR / "arrow_down_hover.png").replace("\\", "/")

ARROW_UP_LIGHT = str(ASSETS_DIR / "arrow_up_gray.png").replace("\\", "/")
ARROW_UP_LIGHT_HOVER = str(ASSETS_DIR / "arrow_up_gray_hover.png").replace("\\", "/")
ARROW_DOWN_LIGHT = str(ASSETS_DIR / "arrow_down_gray.png").replace("\\", "/")
ARROW_DOWN_LIGHT_HOVER = str(ASSETS_DIR / "arrow_down_gray_hover.png").replace("\\", "/")
CHECK_WHITE = str(ASSETS_DIR / "check_white.png").replace("\\", "/")

DARK_STYLE = f"""
QMainWindow, QDialog, QMessageBox {{
    background-color: #121315;
    color: #E6E8EA;
}}
QWidget {{
    color: #E2E4E8;
    font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
    font-size: 13px;
}}
QScrollArea, #rule_scroll_area, #rule_panel_content {{
    background-color: #16181B;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background-color: #16181B;
}}
QScrollBar:vertical {{
    background-color: #16181B;
    width: 7px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: #2E3238;
    border-radius: 3px;
    min-height: 25px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: #434952;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background-color: #16181B;
    height: 7px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background-color: #2E3238;
    border-radius: 3px;
    min-width: 25px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: #434952;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QGroupBox {{
    border: 1px solid #282C34;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 14px;
    padding-bottom: 8px;
    padding-left: 8px;
    padding-right: 8px;
    font-weight: bold;
    color: #98A2B3;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    color: #98A2B3;
}}
QLineEdit, QComboBox {{
    background-color: #1A1D21;
    border: 1px solid #2E3238;
    border-radius: 6px;
    padding: 5px 8px;
    color: #E2E4E8;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid #177DDC;
    background-color: #21252B;
}}
QComboBox QAbstractItemView {{
    background-color: #1A1D21;
    border: 1px solid #333842;
    selection-background-color: #177DDC;
    color: #E2E4E8;
}}
QSpinBox {{
    background-color: #1A1D21;
    border: 1px solid #2E3238;
    border-radius: 6px;
    padding-left: 4px;
    padding-right: 20px;
    color: #E2E4E8;
    min-height: 26px;
}}
QSpinBox:focus {{
    border: 1px solid #177DDC;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background-color: transparent;
    border: none;
    width: 18px;
}}
QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
}}
QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
}}
QSpinBox::up-arrow {{
    image: url("{ARROW_UP_DARK}");
    width: 10px;
    height: 7px;
}}
QSpinBox::up-arrow:hover {{
    image: url("{ARROW_UP_DARK_HOVER}");
}}
QSpinBox::down-arrow {{
    image: url("{ARROW_DOWN_DARK}");
    width: 10px;
    height: 7px;
}}
QSpinBox::down-arrow:hover {{
    image: url("{ARROW_DOWN_DARK_HOVER}");
}}
QPushButton {{
    background-color: #21252B;
    border: 1px solid #333842;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
    color: #E2E4E8;
}}
QPushButton:hover {{
    background-color: #282C34;
    border: 1px solid #434952;
    color: #FFFFFF;
}}
QPushButton#btn_primary {{
    background-color: #177DDC;
    border: 1px solid #177DDC;
    color: #FFFFFF;
    font-weight: bold;
}}
QPushButton#btn_primary:hover {{
    background-color: #1668B8;
}}
QPushButton#btn_primary:disabled {{
    background-color: #1F2833;
    border: 1px solid #1F2833;
    color: #556270;
}}
QPushButton#btn_undo {{
    background-color: #262B33;
    border: 1px solid #38404D;
    color: #F0A020;
    font-weight: 500;
}}
QPushButton#btn_undo:hover {{
    background-color: #323A45;
    border-color: #F0A020;
}}

QPushButton#btn_license {{
    background-color: rgba(99, 102, 241, 0.18);
    border: 1px solid rgba(99, 102, 241, 0.45);
    color: #c7d2fe;
    font-weight: 600;
    border-radius: 6px;
    padding: 4px 12px;
}}
QPushButton#btn_license:hover {{
    background-color: rgba(99, 102, 241, 0.32);
    border-color: #818cf8;
    color: #ffffff;
}}


QPushButton#btn_license {{
    background-color: #eef2ff;
    border: 1px solid #c7d2fe;
    color: #4338ca;
    font-weight: 600;
    border-radius: 6px;
    padding: 4px 12px;
}}
QPushButton#btn_license:hover {{
    background-color: #e0e7ff;
    border-color: #818cf8;
    color: #312e81;
}}

QPushButton#btn_undo:disabled {{
    background-color: #1C2026;
    border-color: #272C33;
    color: #555E6B;
}}
QPushButton[class="tag_btn"] {{
    background-color: #1B2635;
    border: 1px solid #253A52;
    border-radius: 4px;
    padding: 4px 6px;
    font-size: 11px;
    color: #79BAF2;
    font-weight: 500;
}}
QPushButton[class="tag_btn"]:hover {{
    background-color: #177DDC;
    border-color: #177DDC;
    color: #FFFFFF;
}}
QCheckBox {{
    color: #D1D5DB;
    spacing: 8px;
}}
QCheckBox:hover {{
    color: #FFFFFF;
}}
QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border: 1.5px solid #5A6474;
    border-radius: 4px;
    background-color: #1A1D21;
}}
QCheckBox::indicator:hover {{
    border: 1.5px solid #3B99FC;
    background-color: #23272E;
}}
QCheckBox::indicator:checked {{
    border: 1.5px solid #177DDC;
    background-color: #177DDC;
    image: url({CHECK_WHITE});
}}
QCheckBox::indicator:checked:hover {{
    border: 1.5px solid #3B99FC;
    background-color: #3B99FC;
}}
QCheckBox::indicator:disabled {{
    border: 1.5px solid #333842;
    background-color: #16181B;
}}
QRadioButton {{
    color: #D1D5DB;
    spacing: 8px;
}}
QRadioButton:hover {{
    color: #FFFFFF;
}}
QRadioButton::indicator {{
    width: 15px;
    height: 15px;
    border-radius: 8px;
    border: 1.5px solid #5A6474;
    background-color: #1A1D21;
}}
QRadioButton::indicator:hover {{
    border: 1.5px solid #3B99FC;
    background-color: #23272E;
}}
QRadioButton::indicator:checked {{
    border: 4.5px solid #177DDC;
    background-color: #FFFFFF;
}}
QRadioButton::indicator:checked:hover {{
    border: 4.5px solid #3B99FC;
    background-color: #FFFFFF;
}}
QRadioButton::indicator:disabled {{
    border: 1.5px solid #333842;
    background-color: #16181B;
}}
QTableView {{
    background-color: #16181B;
    alternate-background-color: #1A1D21;
    border: 1px solid #282C34;
    border-radius: 8px;
    gridline-color: #22262C;
    selection-background-color: #1B3854;
    selection-color: #FFFFFF;
    color: #E2E4E8;
}}
QHeaderView::section {{
    background-color: #1F2328;
    color: #B0B8C4;
    padding: 7px;
    border: none;
    border-right: 1px solid #282C34;
    border-bottom: 1px solid #282C34;
    font-weight: bold;
}}
QStatusBar {{
    background-color: #16181B;
    border-top: 1px solid #24282E;
    color: #8C94A0;
}}
QMessageBox, QProgressDialog {{
    background-color: #1A1D21;
}}
QMessageBox QLabel, QProgressDialog QLabel {{
    color: #F0F2F5;
    font-size: 13px;
    background-color: transparent;
}}
QMessageBox QPushButton, QProgressDialog QPushButton {{
    background-color: #282C34;
    border: 1px solid #3A404D;
    border-radius: 5px;
    padding: 6px 18px;
    color: #FFFFFF;
    min-width: 65px;
}}
QMessageBox QPushButton:hover, QProgressDialog QPushButton:hover {{
    background-color: #177DDC;
    border-color: #177DDC;
}}
QProgressBar {{
    border: 1px solid #333842;
    border-radius: 5px;
    text-align: center;
    background-color: #16181B;
    color: #FFFFFF;
    height: 18px;
}}
QProgressBar::chunk {{
    background-color: #177DDC;
    border-radius: 4px;
}}
"""

LIGHT_STYLE = f"""
QMainWindow, QDialog, QMessageBox {{
    background-color: #F5F6F8;
    color: #1F2937;
}}
QWidget {{
    color: #1F2937;
    font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
    font-size: 13px;
}}
QScrollArea, #rule_scroll_area, #rule_panel_content {{
    background-color: #FFFFFF;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background-color: #FFFFFF;
}}
QScrollBar:vertical {{
    background-color: #F5F6F8;
    width: 7px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: #D1D5DB;
    border-radius: 3px;
    min-height: 25px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: #9CA3AF;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background-color: #F5F6F8;
    height: 7px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background-color: #D1D5DB;
    border-radius: 3px;
    min-width: 25px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: #9CA3AF;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QGroupBox {{
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 14px;
    padding-bottom: 8px;
    padding-left: 8px;
    padding-right: 8px;
    font-weight: bold;
    color: #4B5563;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    color: #4B5563;
}}
QLineEdit, QComboBox {{
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 5px 8px;
    color: #1F2937;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid #1677FF;
    background-color: #FFFFFF;
}}
QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    selection-background-color: #1677FF;
    color: #1F2937;
}}
QSpinBox {{
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding-left: 4px;
    padding-right: 20px;
    color: #1F2937;
    min-height: 26px;
}}
QSpinBox:focus {{
    border: 1px solid #1677FF;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background-color: transparent;
    border: none;
    width: 18px;
}}
QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
}}
QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
}}
QSpinBox::up-arrow {{
    image: url("{ARROW_UP_LIGHT}");
    width: 10px;
    height: 7px;
}}
QSpinBox::up-arrow:hover {{
    image: url("{ARROW_UP_LIGHT_HOVER}");
}}
QSpinBox::down-arrow {{
    image: url("{ARROW_DOWN_LIGHT}");
    width: 10px;
    height: 7px;
}}
QSpinBox::down-arrow:hover {{
    image: url("{ARROW_DOWN_LIGHT_HOVER}");
}}
QPushButton {{
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
    color: #374151;
}}
QPushButton:hover {{
    background-color: #F3F4F6;
    border: 1px solid #9CA3AF;
    color: #111827;
}}
QPushButton#btn_primary {{
    background-color: #1677FF;
    border: 1px solid #1677FF;
    color: #FFFFFF;
    font-weight: bold;
}}
QPushButton#btn_primary:hover {{
    background-color: #0958D9;
}}
QPushButton#btn_primary:disabled {{
    background-color: #E5E7EB;
    border: 1px solid #E5E7EB;
    color: #9CA3AF;
}}
QPushButton#btn_undo {{
    background-color: #FFFBE6;
    border: 1px solid #FFE58F;
    color: #D46B08;
    font-weight: 500;
}}
QPushButton#btn_undo:hover {{
    background-color: #FFF1B8;
    border-color: #FAAD14;
}}
QPushButton#btn_undo:disabled {{
    background-color: #F5F5F5;
    border-color: #D9D9D9;
    color: #BFBFBF;
}}
QPushButton[class="tag_btn"] {{
    background-color: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 4px;
    padding: 4px 6px;
    font-size: 11px;
    color: #1D4ED8;
    font-weight: 500;
}}
QPushButton[class="tag_btn"]:hover {{
    background-color: #1677FF;
    border-color: #1677FF;
    color: #FFFFFF;
}}
QCheckBox {{
    color: #374151;
    spacing: 8px;
}}
QCheckBox:hover {{
    color: #111827;
}}
QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border: 1.5px solid #9CA3AF;
    border-radius: 4px;
    background-color: #FFFFFF;
}}
QCheckBox::indicator:hover {{
    border: 1.5px solid #1677FF;
    background-color: #F8FAFC;
}}
QCheckBox::indicator:checked {{
    border: 1.5px solid #1677FF;
    background-color: #1677FF;
    image: url({CHECK_WHITE});
}}
QCheckBox::indicator:checked:hover {{
    border: 1.5px solid #4096FF;
    background-color: #4096FF;
}}
QCheckBox::indicator:disabled {{
    border: 1.5px solid #D1D5DB;
    background-color: #F3F4F6;
}}
QRadioButton {{
    color: #374151;
    spacing: 8px;
}}
QRadioButton:hover {{
    color: #111827;
}}
QRadioButton::indicator {{
    width: 15px;
    height: 15px;
    border-radius: 8px;
    border: 1.5px solid #9CA3AF;
    background-color: #FFFFFF;
}}
QRadioButton::indicator:hover {{
    border: 1.5px solid #1677FF;
    background-color: #F8FAFC;
}}
QRadioButton::indicator:checked {{
    border: 4.5px solid #1677FF;
    background-color: #FFFFFF;
}}
QRadioButton::indicator:checked:hover {{
    border: 4.5px solid #4096FF;
    background-color: #FFFFFF;
}}
QRadioButton::indicator:disabled {{
    border: 1.5px solid #D1D5DB;
    background-color: #F3F4F6;
}}
QTableView {{
    background-color: #FFFFFF;
    alternate-background-color: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    gridline-color: #F3F4F6;
    selection-background-color: #DBEAFE;
    selection-color: #1E3A8A;
    color: #1F2937;
}}
QHeaderView::section {{
    background-color: #F3F4F6;
    color: #4B5563;
    padding: 7px;
    border: none;
    border-right: 1px solid #E5E7EB;
    border-bottom: 1px solid #E5E7EB;
    font-weight: bold;
}}
QStatusBar {{
    background-color: #FFFFFF;
    border-top: 1px solid #E5E7EB;
    color: #6B7280;
}}
QMessageBox, QProgressDialog {{
    background-color: #FFFFFF;
}}
QMessageBox QLabel, QProgressDialog QLabel {{
    color: #1F2937;
    font-size: 13px;
    background-color: transparent;
}}
QMessageBox QPushButton, QProgressDialog QPushButton {{
    background-color: #F3F4F6;
    border: 1px solid #D1D5DB;
    border-radius: 5px;
    padding: 6px 18px;
    color: #1F2937;
    min-width: 65px;
}}
QMessageBox QPushButton:hover, QProgressDialog QPushButton:hover {{
    background-color: #1677FF;
    border-color: #1677FF;
    color: #FFFFFF;
}}
QProgressBar {{
    border: 1px solid #D1D5DB;
    border-radius: 5px;
    text-align: center;
    background-color: #F3F4F6;
    color: #1F2937;
    height: 18px;
}}
QProgressBar::chunk {{
    background-color: #1677FF;
    border-radius: 4px;
}}
"""

def get_theme_stylesheet(is_dark: bool) -> str:
    return DARK_STYLE if is_dark else LIGHT_STYLE
