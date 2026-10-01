"""
KyteRename - Main Window (雙欄預覽、拖曳資料夾、衝突防呆與批次操作)
"""
import os
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QSplitter, QMessageBox, QStatusBar
)

from core.file_scanner import scan_path
from core.rule_engine import RuleEngine
from rules.base_rule import FileEntry, BaseRule
from ui.preview_table import PreviewTable
from ui.rule_panel import RulePanel

DARK_STYLE = """
QMainWindow {
    background-color: #141414;
}
QWidget {
    color: #E6E6E6;
    font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #303030;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 14px;
    font-weight: bold;
    color: #A6B2C0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
}
QLineEdit {
    background-color: #1F1F1F;
    border: 1px solid #3A3A3A;
    border-radius: 5px;
    padding: 5px 8px;
    color: #FFFFFF;
}
QLineEdit:focus {
    border: 1px solid #177DDC;
}
QPushButton {
    background-color: #1F1F1F;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #2A2A2A;
    border: 1px solid #4A4A4A;
}
QPushButton#btn_primary {
    background-color: #177DDC;
    border: 1px solid #177DDC;
    color: #FFFFFF;
    font-weight: bold;
}
QPushButton#btn_primary:hover {
    background-color: #1668B8;
}
QPushButton#btn_primary:disabled {
    background-color: #2A3B4C;
    border: 1px solid #2A3B4C;
    color: #6D8093;
}
QTableView {
    background-color: #1A1A1A;
    alternate-background-color: #202020;
    border: 1px solid #2D2D2D;
    border-radius: 6px;
    gridline-color: #2D2D2D;
    selection-background-color: #173853;
}
QHeaderView::section {
    background-color: #262626;
    color: #CCCCCC;
    padding: 6px;
    border: none;
    border-right: 1px solid #333333;
    border-bottom: 1px solid #333333;
    font-weight: bold;
}
QStatusBar {
    background-color: #1A1A1A;
    border-top: 1px solid #262626;
    color: #8C8C8C;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KyteRename — 規則式即時預覽批次重新命名")
        self.resize(1100, 720)
        self.setAcceptDrops(True)
        self.setStyleSheet(DARK_STYLE)

        self.entries: List[FileEntry] = []
        self.rule_engine = RuleEngine()
        self.current_rules: List[BaseRule] = []

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 頂部操作列
        top_bar = QHBoxLayout()
        self.btn_open_folder = QPushButton("📂 開啟資料夾")
        self.btn_open_files = QPushButton("📄 新增檔案")
        self.btn_clear = QPushButton("🗑️ 清空列表")

        self.lbl_tip = QLabel("（亦可直接將檔案或資料夾拖曳至此視窗）")
        self.lbl_tip.setStyleSheet("color: #7A7A7A; font-size: 12px;")

        top_bar.addWidget(self.btn_open_folder)
        top_bar.addWidget(self.btn_open_files)
        top_bar.addWidget(self.btn_clear)
        top_bar.addWidget(self.lbl_tip)
        top_bar.addStretch()

        self.btn_apply = QPushButton("🚀 執行重新命名")
        self.btn_apply.setObjectName("btn_primary")
        self.btn_apply.setEnabled(False)
        top_bar.addWidget(self.btn_apply)

        main_layout.addLayout(top_bar)

        # 中間 Splitter（左邊 QTableView，右邊 RulePanel）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table = PreviewTable(self)
        self.rule_panel = RulePanel(self)

        splitter.addWidget(self.table)
        splitter.addWidget(self.rule_panel)
        splitter.setStretchFactor(0, 7) # 表格佔 70%
        splitter.setStretchFactor(1, 3) # 規則佔 30%
        main_layout.addWidget(splitter, stretch=1)

        # 狀態列
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就緒：請拖入檔案或資料夾開始重新命名")

        # 事件連接
        self.btn_open_folder.clicked.connect(self._on_open_folder)
        self.btn_open_files.clicked.connect(self._on_open_files)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        self.rule_panel.rules_changed.connect(self._on_rules_changed)

    # 拖曳支援
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if paths:
            self._load_paths(paths)

    def _on_open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "選取要重新命名的資料夾")
        if folder:
            self._load_paths([folder])

    def _on_open_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "選取要重新命名的檔案")
        if files:
            self._load_paths(files)

    def _on_clear(self):
        self.entries.clear()
        self.table.table_model.update_data([], [], set(), set())
        self._update_status()

    def _load_paths(self, paths: List[str]):
        loaded_entries: List[FileEntry] = []
        for p in paths:
            loaded_entries.extend(scan_path(p, recursive=False))

        # 去除已重複載入的檔案路徑
        existing_paths = {e.path.resolve() for e in self.entries}
        for e in loaded_entries:
            if e.path.resolve() not in existing_paths:
                self.entries.append(e)
                existing_paths.add(e.path.resolve())

        self._refresh_previews(full_reset=True)

    def _on_rules_changed(self, rules: List[BaseRule]):
        self.current_rules = rules
        self.rule_engine.set_rules(rules)
        self._refresh_previews(full_reset=False)

    def _refresh_previews(self, full_reset: bool = False):
        if not self.entries:
            self.table.table_model.update_data([], [], set(), set())
            self._update_status()
            return

        new_names = self.rule_engine.preview_all(self.entries)
        duplicates, disk_conflicts = RuleEngine.detect_conflicts(self.entries, new_names)

        if full_reset:
            self.table.table_model.update_data(self.entries, new_names, duplicates, disk_conflicts)
        else:
            self.table.table_model.update_previews(new_names, duplicates, disk_conflicts)

        self._update_status(duplicates, disk_conflicts)

    def _update_status(self, duplicates=None, disk_conflicts=None):
        count = len(self.entries)
        duplicates = duplicates or set()
        disk_conflicts = disk_conflicts or set()

        if count == 0:
            self.status_bar.showMessage("就緒：請拖入檔案或資料夾開始重新命名")
            self.btn_apply.setEnabled(False)
            return

        # 計算有變更的數量
        previews = self.table.table_model.preview_names
        changed_count = sum(1 for e, n in zip(self.entries, previews) if e.original_name != n)

        has_conflicts = len(duplicates) > 0 or len(disk_conflicts) > 0
        self.btn_apply.setEnabled(changed_count > 0 and not has_conflicts)

        msg = f"共 {count} 個檔案 | {changed_count} 個待更名"
        if duplicates:
            msg += f" | ⚠️ {len(duplicates)} 個名稱衝突（請修正規則）"
        if disk_conflicts:
            msg += f" | ⚠️ {len(disk_conflicts)} 個目標檔案已存在於磁碟"

        self.status_bar.showMessage(msg)

    def _on_apply_clicked(self):
        msg = "Phase 1 預覽架構運作正常！\n執行實體改名與快照復原功能將於 Phase 4 完整就緒。"
        QMessageBox.information(self, "準備執行", msg)
