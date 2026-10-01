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
/* 全域底色與字體 */
QMainWindow, QDialog, QMessageBox {
    background-color: #121315;
    color: #E6E8EA;
}
QWidget {
    color: #E2E4E8;
    font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
    font-size: 13px;
}

/* 捲動區域與內部面板徹底深色化，杜絕原生白色漏光 */
QScrollArea, #rule_scroll_area, #rule_panel_content {
    background-color: #16181B;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background-color: #16181B;
}

/* 捲動條極簡微調 */
QScrollBar:vertical {
    background-color: #16181B;
    width: 7px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #2E3238;
    border-radius: 3px;
    min-height: 25px;
}
QScrollBar::handle:vertical:hover {
    background-color: #434952;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* 精緻卡片式 GroupBox */
QGroupBox {
    border: 1px solid #282C34;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 600;
    color: #58A6FF;
    background-color: #1A1D21;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #16181B;
    border-radius: 4px;
}

/* 輸入框、下拉選單、數字框 */
QLineEdit, QSpinBox, QComboBox {
    background-color: #21252B;
    border: 1px solid #333842;
    border-radius: 5px;
    padding: 5px 8px;
    color: #F0F2F5;
    selection-background-color: #177DDC;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #177DDC;
}
QComboBox QAbstractItemView {
    background-color: #21252B;
    border: 1px solid #333842;
    selection-background-color: #177DDC;
    color: #F0F2F5;
}
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #282C34;
    border: none;
    width: 16px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #353B45;
}

/* 按鈕美化 */
QPushButton {
    background-color: #21252B;
    border: 1px solid #333842;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
    color: #E2E4E8;
}
QPushButton:hover {
    background-color: #282C34;
    border: 1px solid #434952;
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
    background-color: #1F2833;
    border: 1px solid #1F2833;
    color: #556270;
}

/* 快捷標籤 Tag Chips */
QPushButton[class="tag_btn"] {
    background-color: #1B2635;
    border: 1px solid #253A52;
    border-radius: 4px;
    padding: 4px 6px;
    font-size: 11px;
    color: #79BAF2;
    font-weight: 500;
}
QPushButton[class="tag_btn"]:hover {
    background-color: #177DDC;
    border-color: #177DDC;
    color: #FFFFFF;
}

/* 單選與核取方塊 */
QRadioButton, QCheckBox {
    color: #D1D5DB;
    spacing: 7px;
}
QRadioButton:hover, QCheckBox:hover {
    color: #FFFFFF;
}

/* 左側預覽表格 */
QTableView {
    background-color: #16181B;
    alternate-background-color: #1A1D21;
    border: 1px solid #282C34;
    border-radius: 8px;
    gridline-color: #22262C;
    selection-background-color: #1B3854;
}
QHeaderView::section {
    background-color: #1F2328;
    color: #B0B8C4;
    padding: 7px;
    border: none;
    border-right: 1px solid #282C34;
    border-bottom: 1px solid #282C34;
    font-weight: bold;
}
QStatusBar {
    background-color: #16181B;
    border-top: 1px solid #24282E;
    color: #8C94A0;
}

/* 對話框樣式 */
QMessageBox {
    background-color: #1A1D21;
}
QMessageBox QLabel {
    color: #F0F2F5;
    font-size: 13px;
    background-color: transparent;
}
QMessageBox QPushButton {
    background-color: #282C34;
    border: 1px solid #3A404D;
    border-radius: 5px;
    padding: 6px 18px;
    color: #FFFFFF;
    min-width: 65px;
}
QMessageBox QPushButton:hover {
    background-color: #177DDC;
    border-color: #177DDC;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KyteRename — 規則式即時預覽批次重新命名")
        self.resize(1180, 760)
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
        splitter.setStretchFactor(0, 62)
        splitter.setStretchFactor(1, 38)
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
        for e in loaded_entries:
            if e.path.resolve() not in existing_paths:
                self.entries.append(e)
                existing_paths.add(e.path.resolve())

        self._refresh_previews(full_reset=True)

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
