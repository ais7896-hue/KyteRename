"""
KyteRename - Search & Filter Bar (檔案清單即時過濾、狀態切換與統計)
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QButtonGroup
)

class SearchBar(QWidget):
    """
    檔案清單即時搜尋與過濾列
    - 支援文字即時搜尋 (大小寫不敏感)
    - 支援三態過濾: 全部 (All) / 僅看待更名 (Modified) / 僅看衝突 (Conflicts)
    - 顯示目前篩選筆數與總筆數
    """
    search_changed = Signal(str)
    filter_mode_changed = Signal(str)  # "all", "changed", "conflict"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(8)

        # 搜尋輸入框
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("🔍 搜尋檔案名稱... (Ctrl+F)")
        self.edit_search.setClearButtonEnabled(True)
        self.edit_search.setFixedHeight(28)
        self.edit_search.setStyleSheet("""
            QLineEdit {
                background-color: #1A1D21;
                border: 1px solid #2E3238;
                border-radius: 6px;
                padding: 3px 8px;
                color: #E2E4E8;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #177DDC;
                background-color: #21252B;
            }
        """)
        self.edit_search.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.edit_search, stretch=1)

        # 快速過濾標籤組 (全部 / 待更名 / 衝突)
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.btn_all = QPushButton("全部")
        self.btn_all.setCheckable(True)
        self.btn_all.setChecked(True)
        self.btn_all.setFixedHeight(26)

        self.btn_changed = QPushButton("✓ 待更名")
        self.btn_changed.setCheckable(True)
        self.btn_changed.setFixedHeight(26)

        self.btn_conflict = QPushButton("⚠️ 衝突項目")
        self.btn_conflict.setCheckable(True)
        self.btn_conflict.setFixedHeight(26)

        chip_qss = """
            QPushButton {
                background-color: #1E2227;
                border: 1px solid #333842;
                border-radius: 4px;
                padding: 2px 8px;
                color: #A0AEC0;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #282C34;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: #177DDC;
                border: 1px solid #177DDC;
                color: #FFFFFF;
                font-weight: bold;
            }
        """
        for b in (self.btn_all, self.btn_changed, self.btn_conflict):
            b.setStyleSheet(chip_qss)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(b)
            self.btn_group.addButton(b)

        self.btn_all.clicked.connect(lambda: self.filter_mode_changed.emit("all"))
        self.btn_changed.clicked.connect(lambda: self.filter_mode_changed.emit("changed"))
        self.btn_conflict.clicked.connect(lambda: self.filter_mode_changed.emit("conflict"))

        # 筆數統計標籤
        self.lbl_count = QLabel("共 0 筆")
        self.lbl_count.setStyleSheet("color: #71717A; font-size: 11px; padding-left: 2px;")
        layout.addWidget(self.lbl_count)

    def update_counts(self, visible_count: int, total_count: int, conflict_count: int = 0, changed_count: int = 0):
        """更新統計數據與按鈕標題"""
        if visible_count == total_count:
            self.lbl_count.setText(f"共 {total_count} 筆")
        else:
            self.lbl_count.setText(f"顯示 {visible_count} / {total_count} 筆")

        self.btn_changed.setText(f"✓ 待更名 ({changed_count})")
        if conflict_count > 0:
            self.btn_conflict.setText(f"⚠️ 衝突 ({conflict_count})")
            self.btn_conflict.setStyleSheet("""
                QPushButton {
                    background-color: #381A1A;
                    border: 1px solid #5C2223;
                    border-radius: 4px;
                    padding: 2px 8px;
                    color: #FF7875;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #4C2020;
                    color: #FFA39E;
                }
                QPushButton:checked {
                    background-color: #E03131;
                    border: 1px solid #E03131;
                    color: #FFFFFF;
                    font-weight: bold;
                }
            """)
        else:
            self.btn_conflict.setText("⚠️ 衝突 (0)")
            chip_qss = """
                QPushButton {
                    background-color: #1E2227;
                    border: 1px solid #333842;
                    border-radius: 4px;
                    padding: 2px 8px;
                    color: #A0AEC0;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #282C34;
                    color: #FFFFFF;
                }
                QPushButton:checked {
                    background-color: #177DDC;
                    border: 1px solid #177DDC;
                    color: #FFFFFF;
                    font-weight: bold;
                }
            """
            self.btn_conflict.setStyleSheet(chip_qss)

    def focus_search(self):
        """聚焦到搜尋列並全選文字"""
        self.edit_search.setFocus()
        self.edit_search.selectAll()

    def clear_search(self):
        """清空搜尋列"""
        self.edit_search.clear()
        self.btn_all.setChecked(True)
        self.filter_mode_changed.emit("all")
