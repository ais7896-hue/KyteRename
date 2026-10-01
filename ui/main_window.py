"""
KyteRename - Main Window (雙欄預覽、安全拓撲改名、進度對話框與 Ctrl+Z 快照復原)
"""
import os
from pathlib import Path
from typing import List, Tuple

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QSplitter, QMessageBox, QStatusBar, QDialog,
    QProgressDialog
)

from core.file_scanner import scan_path
from core.rule_engine import RuleEngine
from core.metadata_worker import MetadataWorker
from core.rename_executor import RenameWorker
from core.snapshot_manager import SnapshotManager
from rules.base_rule import FileEntry, BaseRule
from ui.preview_table import PreviewTable
from ui.rule_panel import RulePanel


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ARROW_UP_PATH = str(ASSETS_DIR / "arrow_up.png").replace("\\", "/")
ARROW_UP_HOVER_PATH = str(ASSETS_DIR / "arrow_up_hover.png").replace("\\", "/")
ARROW_DOWN_PATH = str(ASSETS_DIR / "arrow_down.png").replace("\\", "/")
ARROW_DOWN_HOVER_PATH = str(ASSETS_DIR / "arrow_down_hover.png").replace("\\", "/")

DARK_STYLE_TEMPLATE = """
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

/* 捲動區域與內部面板徹底深色化 */
QScrollArea, #rule_scroll_area, #rule_panel_content {
    background-color: #16181B;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background-color: #16181B;
}

/* 垂直與水平捲動條微調（極簡沉浸深色風格） */
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

QScrollBar:horizontal {
    background-color: #16181B;
    height: 7px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background-color: #2E3238;
    border-radius: 3px;
    min-width: 25px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #434952;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
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
QLineEdit, QComboBox {
    background-color: #21252B;
    border: 1px solid #333842;
    border-radius: 5px;
    padding: 5px 8px;
    color: #F0F2F5;
    selection-background-color: #177DDC;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #177DDC;
}
QComboBox QAbstractItemView {
    background-color: #21252B;
    border: 1px solid #333842;
    selection-background-color: #177DDC;
    color: #F0F2F5;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #333842;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    background-color: #282D36;
}
QComboBox::drop-down:hover {
    background-color: #177DDC;
}
QComboBox::down-arrow {
    image: url("__ARROW_DOWN__");
    width: 11px;
    height: 11px;
}
QComboBox::down-arrow:hover {
    image: url("__ARROW_DOWN_HOVER__");
}

/* 數字調節框 (QSpinBox) — 高對比立體上下箭頭按鈕 */
QSpinBox {
    background-color: #21252B;
    border: 1px solid #333842;
    border-radius: 5px;
    padding: 4px 6px;
    padding-right: 24px;
    color: #F0F2F5;
    selection-background-color: #177DDC;
}
QSpinBox:focus {
    border: 1px solid #177DDC;
}
QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 22px;
    height: 14px;
    background-color: #2C323B;
    border-left: 1px solid #3E4654;
    border-bottom: 1px solid #3E4654;
    border-top-right-radius: 4px;
}
QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 22px;
    height: 14px;
    background-color: #2C323B;
    border-left: 1px solid #3E4654;
    border-bottom-right-radius: 4px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #177DDC;
}
QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
    background-color: #125EA6;
}
QSpinBox::up-arrow {
    image: url("__ARROW_UP__");
    width: 10px;
    height: 10px;
}
QSpinBox::up-arrow:hover {
    image: url("__ARROW_UP_HOVER__");
}
QSpinBox::down-arrow {
    image: url("__ARROW_DOWN__");
    width: 10px;
    height: 10px;
}
QSpinBox::down-arrow:hover {
    image: url("__ARROW_DOWN_HOVER__");
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
QPushButton#btn_undo {
    background-color: #262B33;
    border: 1px solid #38404D;
    color: #F0A020;
    font-weight: 500;
}
QPushButton#btn_undo:hover {
    background-color: #323A45;
    border-color: #F0A020;
}
QPushButton#btn_undo:disabled {
    background-color: #1C2026;
    border-color: #272C33;
    color: #555E6B;
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
QMessageBox, QProgressDialog {
    background-color: #1A1D21;
}
QMessageBox QLabel, QProgressDialog QLabel {
    color: #F0F2F5;
    font-size: 13px;
    background-color: transparent;
}
QMessageBox QPushButton, QProgressDialog QPushButton {
    background-color: #282C34;
    border: 1px solid #3A404D;
    border-radius: 5px;
    padding: 6px 18px;
    color: #FFFFFF;
    min-width: 65px;
}
QMessageBox QPushButton:hover, QProgressDialog QPushButton:hover {
    background-color: #177DDC;
    border-color: #177DDC;
}
QProgressBar {
    border: 1px solid #333842;
    border-radius: 5px;
    text-align: center;
    background-color: #16181B;
    color: #FFFFFF;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #177DDC;
    border-radius: 4px;
}
"""

DARK_STYLE = (
    DARK_STYLE_TEMPLATE
    .replace("__ARROW_UP__", ARROW_UP_PATH)
    .replace("__ARROW_UP_HOVER__", ARROW_UP_HOVER_PATH)
    .replace("__ARROW_DOWN__", ARROW_DOWN_PATH)
    .replace("__ARROW_DOWN_HOVER__", ARROW_DOWN_HOVER_PATH)
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KyteRename — 規則式即時預覽批次重新命名")
        self.resize(1180, 760)
        self.setMinimumSize(780, 520)
        self.setAcceptDrops(True)
        self.setStyleSheet(DARK_STYLE)

        self.entries: List[FileEntry] = []
        self.rule_engine = RuleEngine()
        self.current_rules: List[BaseRule] = []
        self.meta_worker: MetadataWorker = None
        self.rename_worker: RenameWorker = None
        self.snapshot_manager = SnapshotManager()

        self._init_ui()
        self._init_shortcuts()
        self._update_undo_button_state()

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
        self.btn_undo = QPushButton("↩️ 復原上次改名 (Ctrl+Z)")
        self.btn_undo.setObjectName("btn_undo")

        top_bar.addWidget(self.btn_open_folder)
        top_bar.addWidget(self.btn_open_files)
        top_bar.addWidget(self.btn_clear)
        top_bar.addWidget(self.btn_undo)
        top_bar.addStretch()

        self.btn_apply = QPushButton("🚀 執行重新命名")
        self.btn_apply.setObjectName("btn_primary")
        self.btn_apply.setEnabled(False)
        top_bar.addWidget(self.btn_apply)

        main_layout.addLayout(top_bar)

        # 中間 Splitter
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
        self.btn_undo.clicked.connect(self._on_undo_clicked)
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        self.rule_panel.rules_changed.connect(self._on_rules_changed)

    def _init_shortcuts(self):
        # 註冊 Ctrl+Z 快速復原
        shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        shortcut_undo.activated.connect(self._on_undo_clicked)

    def _update_undo_button_state(self):
        has_snapshot = (self.snapshot_manager.get_latest_snapshot() is not None)
        self.btn_undo.setEnabled(has_snapshot)

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
        previews = self.table.table_model.preview_names
        changed_ops: List[Tuple[Path, Path]] = []
        for entry, new_name in zip(self.entries, previews):
            if entry.original_name != new_name:
                dst = entry.parent_dir / new_name
                changed_ops.append((entry.path, dst))

        if not changed_ops:
            QMessageBox.information(self, "提示", "目前沒有需要更名的檔案。")
            return

        reply = QMessageBox.question(
            self,
            "確認執行重新命名",
            f"即將對 {len(changed_ops)} 個檔案執行重新命名。\n\n改名完成後會自動產生安全快照，隨時可按 Ctrl+Z 完整還原。\n是否確定執行？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 建立進度對話框
        progress_dialog = QProgressDialog("正在執行安全批次改名...", "取消", 0, len(changed_ops), self)
        progress_dialog.setWindowTitle("處理中")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setMinimumDuration(0)

        self.rename_worker = RenameWorker(changed_ops, self)

        self.rename_worker.progress.connect(lambda cur, tot, name: (
            progress_dialog.setValue(cur),
            progress_dialog.setLabelText(f"正在更名 ({cur}/{tot}): {name}")
        ))

        progress_dialog.canceled.connect(self.rename_worker.cancel)

        def _on_rename_finished(result: dict):
            progress_dialog.close()

            # 儲存快照
            if result["success_ops"]:
                self.snapshot_manager.save_snapshot(result["success_ops"])

            self._update_undo_button_state()

            # 重新掃描並更新當前列表的檔案資訊
            updated_paths = [op["renamed_path"] for op in result["success_ops"]]
            # 加上未變更的檔案
            for e, n in zip(self.entries, previews):
                if e.original_name == n and e.path.exists():
                    updated_paths.append(str(e.path.resolve()))

            self.entries.clear()
            self._load_paths(list(set(updated_paths)))

            msg = f"更名完成！\n\n成功: {result['success_count']} 個檔案"
            if result["failed_count"] > 0:
                msg += f"\n失敗: {result['failed_count']} 個檔案（因鎖定或權限不足已略過）"
            msg += "\n\n隨時可點擊「復原上次改名」或按 Ctrl+Z 還原。"

            QMessageBox.information(self, "執行結果", msg)

        self.rename_worker.finished_batch.connect(_on_rename_finished)
        self.rename_worker.start()

    def _on_undo_clicked(self):
        reply = QMessageBox.question(
            self,
            "確認復原改名",
            "確定要復原上一次的改名操作嗎？\n所有更名檔案將依據快照逆向拓撲還原回原始名稱。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        undo_result = self.snapshot_manager.undo_snapshot()
        self._update_undo_button_state()

        if undo_result["success"]:
            # 重新載入列表
            current_dirs = list({str(e.parent_dir) for e in self.entries if e.parent_dir.exists()})
            self.entries.clear()
            if current_dirs:
                self._load_paths(current_dirs)
            else:
                self._refresh_previews(full_reset=True)

            QMessageBox.information(self, "復原完成", f"{undo_result['message']}！")
        else:
            QMessageBox.warning(self, "復原失敗", undo_result["message"])
