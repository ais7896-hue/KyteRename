"""
KyteRename - Main Window (雙欄預覽、拖曳資料夾、漸進式元資料預讀與衝突防呆)
"""
import os
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QSplitter, QMessageBox, QStatusBar, QDialog
)

from core.file_scanner import scan_path
from core.rule_engine import RuleEngine
from core.metadata_worker import MetadataWorker
from rules.base_rule import FileEntry, BaseRule
from ui.preview_table import PreviewTable
from ui.rule_panel import RulePanel

DARK_STYLE = """
QMainWindow, QDialog, QMessageBox {
    background-color: #141414;
    color: #E6E6E6;
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
QLineEdit, QSpinBox, QComboBox {
    background-color: #1F1F1F;
    border: 1px solid #3A3A3A;
    border-radius: 5px;
    padding: 5px 8px;
    color: #FFFFFF;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #177DDC;
}
QComboBox QAbstractItemView {
    background-color: #1F1F1F;
    selection-background-color: #177DDC;
    color: #FFFFFF;
}
QPushButton {
    background-color: #1F1F1F;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
    color: #E6E6E6;
}
QPushButton:hover {
    background-color: #2A2A2A;
    border: 1px solid #4A4A4A;
    color: #FFFFFF;
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
QRadioButton, QCheckBox {
    color: #E0E0E0;
    spacing: 6px;
}
QRadioButton:hover, QCheckBox:hover {
    color: #FFFFFF;
}
QMessageBox {
    background-color: #1E1E1E;
}
QMessageBox QLabel {
    color: #FFFFFF;
    font-size: 13px;
    background-color: transparent;
}
QMessageBox QPushButton {
    background-color: #262626;
    border: 1px solid #404040;
    border-radius: 5px;
    padding: 6px 18px;
    color: #FFFFFF;
    min-width: 65px;
}
QMessageBox QPushButton:hover {
    background-color: #177DDC;
    border-color: #177DDC;
}
QScrollArea {
    background: transparent;
    border: none;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KyteRename — 規則式即時預覽批次重新命名")
        self.resize(1150, 750)
        self.setAcceptDrops(True)
        self.setStyleSheet(DARK_STYLE)

        self.entries: List[FileEntry] = []
        self.rule_engine = RuleEngine()
        self.current_rules: List[BaseRule] = []
        self.meta_worker: MetadataWorker = None

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

        self.lbl_tip = QLabel("（可直接將相片、音樂或資料夾拖曳至此視窗）")
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
        splitter.setStretchFactor(0, 65) # 表格佔 65%
        splitter.setStretchFactor(1, 35) # 規則佔 35%
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
        if self.meta_worker and self.meta_worker.isRunning():
            self.meta_worker.cancel()
            self.meta_worker.wait()
        self.entries.clear()
        self.table.table_model.update_data([], [], set(), set())
        self._update_status()

    def _load_paths(self, paths: List[str]):
        if self.meta_worker and self.meta_worker.isRunning():
            self.meta_worker.cancel()
            self.meta_worker.wait()

        loaded_entries: List[FileEntry] = []
        for p in paths:
            loaded_entries.extend(scan_path(p, recursive=False))

        existing_paths = {e.path.resolve() for e in self.entries}
        new_items: List[FileEntry] = []
        for e in loaded_entries:
            if e.path.resolve() not in existing_paths:
                self.entries.append(e)
                new_items.append(e)
                existing_paths.add(e.path.resolve())

        self._refresh_previews(full_reset=True)

        # 啟動非同步中繼資料預讀
        if self.entries:
            self.status_bar.showMessage(f"共 {len(self.entries)} 個檔案 | 背景讀取 EXIF/ID3 中繼資料中...")
            self.meta_worker = MetadataWorker(self.entries, self)
            self.meta_worker.batch_ready.connect(self._on_metadata_batch)
            self.meta_worker.finished_all.connect(self._on_metadata_finished)
            self.meta_worker.start()

    def _on_metadata_batch(self, batch: list):
        for idx, meta in batch:
            if idx < len(self.entries):
                self.entries[idx].metadata = meta
                self.entries[idx].is_meta_loaded = True

        # 僅局部計算與刷新
        self._refresh_previews(full_reset=False)

    def _on_metadata_finished(self):
        self._update_status()

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
        box = QMessageBox(self)
        box.setWindowTitle("準備執行")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText("Phase 2 變數展開與流水號計算正常！\n\n執行實體改名、拓撲防撞與快照復原功能將於 Phase 4 完整就緒。")
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()
