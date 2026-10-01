"""
KyteRename - Search & Filter Bar (檔案清單即時過濾、狀態切換與統計)
支援深淺色動態主題外觀
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QButtonGroup
)
from config.settings import SettingsManager

class SearchBar(QWidget):
    """
    檔案清單即時搜尋與過濾列
    - 支援文字即時搜尋 (大小寫不敏感)
    - 支援三態過濾: 全部 (All) / 僅看待更名 (Modified) / 僅看衝突 (Conflicts)
    - 支援深淺色動態響應
    """
    search_changed = Signal(str)
    filter_mode_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mgr = SettingsManager()
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(8)

        # 搜尋輸入框
        self.edit_search = QLineEdit()
        self.edit_search.setObjectName("search_input")
        self.edit_search.setPlaceholderText("🔍 搜尋檔案名稱... (Ctrl+F)")
        self.edit_search.setClearButtonEnabled(True)
        self.edit_search.setFixedHeight(28)
        self.edit_search.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.edit_search, stretch=1)

        # 快速過濾標籤組 (全部 / 待更名 / 衝突)
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.btn_all = QPushButton("全部")
        self.btn_all.setProperty("class", "filter_chip")
        self.btn_all.setCheckable(True)
        self.btn_all.setChecked(True)
        self.btn_all.setFixedHeight(26)
        self.btn_all.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_changed = QPushButton("✓ 待更名")
        self.btn_changed.setProperty("class", "filter_chip")
        self.btn_changed.setCheckable(True)
        self.btn_changed.setFixedHeight(26)
        self.btn_changed.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_conflict = QPushButton("⚠️ 衝突 (0)")
        self.btn_conflict.setProperty("class", "filter_chip")
        self.btn_conflict.setCheckable(True)
        self.btn_conflict.setFixedHeight(26)
        self.btn_conflict.setCursor(Qt.CursorShape.PointingHandCursor)

        for b in (self.btn_all, self.btn_changed, self.btn_conflict):
            layout.addWidget(b)
            self.btn_group.addButton(b)

        self.btn_all.clicked.connect(lambda: self.filter_mode_changed.emit("all"))
        self.btn_changed.clicked.connect(lambda: self.filter_mode_changed.emit("changed"))
        self.btn_conflict.clicked.connect(lambda: self.filter_mode_changed.emit("conflict"))

        # 筆數統計標籤
        self.lbl_count = QLabel("共 0 筆")
        self.lbl_count.setObjectName("search_count_lbl")
        layout.addWidget(self.lbl_count)

    def update_counts(self, visible_count: int, total_count: int, conflict_count: int = 0, changed_count: int = 0):
        """更新統計數據與按鈕標題"""
        if visible_count == total_count:
            self.lbl_count.setText(f"共 {total_count} 筆")
        else:
            self.lbl_count.setText(f"顯示 {visible_count} / {total_count} 筆")

        self.btn_changed.setText(f"✓ 待更名 ({changed_count})")
        self.btn_conflict.setText(f"⚠️ 衝突 ({conflict_count})")

        is_dark = self.mgr.is_dark()
        if conflict_count > 0:
            if is_dark:
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
                self.btn_conflict.setStyleSheet("""
                    QPushButton {
                        background-color: #FFF1F0;
                        border: 1px solid #FFA39E;
                        border-radius: 4px;
                        padding: 2px 8px;
                        color: #CF1322;
                        font-size: 11px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #FFCCC7;
                        color: #A8071A;
                    }
                    QPushButton:checked {
                        background-color: #F5222D;
                        border: 1px solid #F5222D;
                        color: #FFFFFF;
                        font-weight: bold;
                    }
                """)
        else:
            self.btn_conflict.setStyleSheet("")

    def focus_search(self):
        """聚焦到搜尋列並全選文字"""
        self.edit_search.setFocus()
        self.edit_search.selectAll()

    def clear_search(self):
        """清空搜尋列"""
        self.edit_search.clear()
        self.btn_all.setChecked(True)
        self.filter_mode_changed.emit("all")
