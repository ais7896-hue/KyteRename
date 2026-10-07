"""
KyteRename - Main Window (雙欄預覽、安全拓撲改名、設定對話框與 KyteView Space 聯動)
"""
import os
from pathlib import Path
from typing import List, Tuple

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QFont, QKeySequence, QShortcut, QKeyEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QSplitter, QMessageBox, QStatusBar, QDialog,
    QProgressDialog
)

from config.settings import SettingsManager
from core.file_scanner import scan_path
from core.rule_engine import RuleEngine
from core.metadata_worker import MetadataWorker
from core.rename_executor import RenameWorker
from core.snapshot_manager import SnapshotManager
from core.kyte_ipc import trigger_kyteview_preview_async
from rules.base_rule import FileEntry, BaseRule
from ui.preview_table import PreviewTable
from ui.search_bar import SearchBar
from ui.rule_panel import RulePanel
from ui.settings_dialog import SettingsDialog
from core.license import LicenseManager
from ui.license_dialog import LicenseDialog
from ui.styles import get_theme_stylesheet, DARK_STYLE, LIGHT_STYLE
from i18n import t, i18n



class MainWindow(QMainWindow):
    def __init__(self, initial_paths: List[str] = None):
        super().__init__()
        self.setWindowTitle(t("app.title"))
        self.resize(1180, 760)
        self.setMinimumSize(780, 520)
        self.setAcceptDrops(True)
        self.settings = SettingsManager()
        self.entries: List[FileEntry] = []
        self.rule_engine = RuleEngine()
        self.current_rules: List[BaseRule] = []
        self.meta_worker: MetadataWorker = None
        self.rename_worker: RenameWorker = None

        # 快照目錄連動 Settings
        self.snapshot_manager = SnapshotManager(self.settings.get_snapshot_dir())
        self.license_mgr = LicenseManager.get_instance()
        self.license_mgr.license_changed.connect(lambda _: self._update_license_button())

        self._init_ui()
        self._init_shortcuts()
        self._restore_settings_state()
        self._update_undo_button_state()

        self.apply_theme()
        self.settings.theme_changed.connect(lambda t: self.apply_theme())

        # 監聽快照目錄變更
        self.settings.settings_changed.connect(self._on_settings_changed)
        i18n.language_changed.connect(self._retranslate_ui)

        if initial_paths:
            self._load_paths(initial_paths)

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 頂部操作列
        top_bar = QHBoxLayout()
        self.btn_open_folder = QPushButton(t("toolbar.open_folder"))
        self.btn_open_files = QPushButton(t("toolbar.open_files"))
        self.btn_clear = QPushButton(t("toolbar.clear_list"))
        self.btn_undo = QPushButton(t("toolbar.undo"))
        self.btn_undo.setObjectName("btn_undo")
        self.btn_settings = QPushButton(t("toolbar.settings"))

        top_bar.addWidget(self.btn_open_folder)
        top_bar.addWidget(self.btn_open_files)
        top_bar.addWidget(self.btn_clear)
        top_bar.addWidget(self.btn_undo)
        top_bar.addWidget(self.btn_settings)
        self.btn_license = QPushButton()
        self.btn_license.setObjectName("btn_license")
        self.btn_license.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_license.clicked.connect(self._on_license_clicked)
        top_bar.addWidget(self.btn_license)
        self._update_license_button()
        top_bar.addStretch()

        self.btn_apply = QPushButton(t("toolbar.apply_rename"))
        self.btn_apply.setObjectName("btn_primary")
        self.btn_apply.setEnabled(False)
        top_bar.addWidget(self.btn_apply)

        main_layout.addLayout(top_bar)

        # 中間 Splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左側表格容器 (含即時搜尋列與雙欄預覽)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(6)

        self.search_bar = SearchBar(table_container)
        self.table = PreviewTable(table_container)
        table_layout.addWidget(self.search_bar)
        table_layout.addWidget(self.table, stretch=1)

        self.rule_panel = RulePanel(self)

        self.main_splitter.addWidget(table_container)
        self.main_splitter.addWidget(self.rule_panel)
        self.main_splitter.setStretchFactor(0, 62)
        self.main_splitter.setStretchFactor(1, 38)
        main_layout.addWidget(self.main_splitter, stretch=1)

        # 狀態列
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(t("status.ready"))

        # 事件連接
        self.btn_open_folder.clicked.connect(self._on_open_folder)
        self.btn_open_files.clicked.connect(self._on_open_files)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_undo.clicked.connect(self._on_undo_clicked)
        self.btn_settings.clicked.connect(self._on_settings_clicked)
        self.btn_apply.clicked.connect(self._on_apply_clicked)

        self.rule_panel.rules_changed.connect(self._on_rules_changed)
        self.rule_panel.pattern_changed.connect(self.table.set_search_pattern)

        # 搜尋列與表格連動
        self.search_bar.search_changed.connect(self._on_search_changed)
        self.search_bar.filter_mode_changed.connect(self._on_filter_mode_changed)

        # 表格預覽與移除連動
        self.table.request_preview.connect(self._preview_file)
        self.table.request_remove.connect(self._remove_entries_by_indices)

    def _retranslate_ui(self):
        """當語言改變時更新主視窗各部件文字"""
        self.setWindowTitle(t("app.title"))
        self.btn_open_folder.setText(t("toolbar.open_folder"))
        self.btn_open_files.setText(t("toolbar.open_files"))
        self.btn_clear.setText(t("toolbar.clear_list"))
        self.btn_undo.setText(t("toolbar.undo"))
        self.btn_settings.setText(t("toolbar.settings"))
        self.btn_apply.setText(t("toolbar.apply_rename"))
        self._update_license_button()
        self._update_status()

    def _init_shortcuts(self):
        shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        shortcut_undo.activated.connect(self._on_undo_clicked)

        shortcut_find = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_find.activated.connect(self.search_bar.focus_search)

    def _restore_settings_state(self):
        if self.settings.get("remember_window_size"):
            geo = self.settings.get("window_geometry")
            if geo:
                try:
                    self.restoreGeometry(bytes.fromhex(geo))
                except Exception:
                    pass

            splitter_sizes = self.settings.get("splitter_sizes")
            if splitter_sizes and isinstance(splitter_sizes, list):
                try:
                    self.main_splitter.setSizes(splitter_sizes)
                except Exception:
                    pass

    def closeEvent(self, event):
        if self.settings.get("remember_window_size"):
            self.settings.set("window_geometry", self.saveGeometry().toHex().data().decode())
            if hasattr(self, "main_splitter"):
                self.settings.set("splitter_sizes", self.main_splitter.sizes())
        super().closeEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        # 按 Space 鍵呼叫 KyteView 快速預覽
        if event.key() == Qt.Key.Key_Space:
            if self.settings.get("enable_space_preview"):
                entry = self.table.get_current_target_entry()
                if entry:
                    self._preview_file(entry.path)
                    event.accept()
                    return
        super().keyPressEvent(event)


    def apply_theme(self):
        """根據 SettingsManager 的 effective_theme 即時動態切換深色 / 淺色風格"""
        is_dark = self.settings.is_dark()
        stylesheet = get_theme_stylesheet(is_dark)
        self.setStyleSheet(stylesheet)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
        if hasattr(self, "table") and self.table is not None:
            if hasattr(self.table, "set_dark_theme"):
                self.table.set_dark_theme(is_dark)
            elif hasattr(self.table, "viewport"):
                self.table.viewport().update()

    def _on_settings_changed(self, key: str, val: object):
        if key == "snapshot_dir_mode":
            self.snapshot_manager = SnapshotManager(self.settings.get_snapshot_dir())
            self._update_undo_button_state()
        elif key == "max_snapshot_history":
            self.snapshot_manager.max_snapshots = int(val)
        elif key == "theme_mode":
            self.apply_theme()


    def _update_license_button(self):
        plan = self.license_mgr.get_plan_type()
        days_left = self.license_mgr.get_trial_days_left()
        if plan == "pro":
            self.btn_license.setText(t("license.pro_badge"))
            self.btn_license.setToolTip(t("license.pro_tooltip"))
        elif plan == "trial":
            self.btn_license.setText(t("license.trial_badge", days=days_left))
            self.btn_license.setToolTip(t("license.trial_tooltip"))
        else:
            self.btn_license.setText(t("license.upgrade_badge"))
            self.btn_license.setToolTip(t("license.upgrade_tooltip"))

    def _on_license_clicked(self):
        dialog = LicenseDialog(self)
        dialog.exec()
        self._update_license_button()

    def _on_settings_clicked(self):
        dlg = SettingsDialog(self)
        dlg.exec()

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
        folder = QFileDialog.getExistingDirectory(self, t("dialog.select_folder"))
        if folder:
            self._load_paths([folder])

    def _on_open_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, t("dialog.select_files"))
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

        recursive = bool(self.settings.get("recursive_scan", False))
        loaded_entries: List[FileEntry] = []
        for p in paths:
            loaded_entries.extend(scan_path(p, recursive=recursive))

        existing_paths = {e.path.resolve() for e in self.entries}
        for e in loaded_entries:
            if e.path.resolve() not in existing_paths:
                self.entries.append(e)
                existing_paths.add(e.path.resolve())

        self._refresh_previews(full_reset=True)

        if self.entries:
            self.status_bar.showMessage(t("status.reading_meta", count=len(self.entries)))
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

    def _on_search_changed(self, text: str):
        self.table.proxy_model.set_search_text(text)
        self._update_search_counts()

    def _on_filter_mode_changed(self, mode: str):
        self.table.proxy_model.set_filter_mode(mode)
        self._update_search_counts()

    def _preview_file(self, target_path: Path):
        """呼叫 KyteView 快速預覽指定檔案"""
        if self.settings.get("enable_space_preview"):
            trigger_kyteview_preview_async(target_path)

    def _remove_entries_by_indices(self, indices: List[int]):
        """從列表中批次移除指定檔案 (依降序索引安全刪除)"""
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.entries):
                del self.entries[idx]
        self._refresh_previews(full_reset=True)

    def _refresh_previews(self, full_reset: bool = False):
        if not self.entries:
            self.table.table_model.update_data([], [], set(), set())
            self._update_status()
            self._update_search_counts()
            return

        raw_new_names = self.rule_engine.preview_all(self.entries)
        policy = self.settings.get("conflict_policy", "ask")
        new_names, duplicates, disk_conflicts = RuleEngine.apply_conflict_policy(
            self.entries, raw_new_names, policy=policy
        )

        if full_reset:
            self.table.table_model.update_data(self.entries, new_names, duplicates, disk_conflicts)
        else:
            self.table.table_model.update_previews(new_names, duplicates, disk_conflicts)

        self._update_status(duplicates, disk_conflicts)
        self._update_search_counts()

    def _update_search_counts(self):
        total_count = len(self.entries)
        visible_count = self.table.proxy_model.rowCount()
        previews = self.table.table_model.preview_names
        changed_count = sum(1 for e, n in zip(self.entries, previews) if e.original_name != n)
        conflict_count = len(self.table.table_model.duplicate_indices) + len(self.table.table_model.disk_conflict_indices)
        self.search_bar.update_counts(
            visible_count=visible_count,
            total_count=total_count,
            conflict_count=conflict_count,
            changed_count=changed_count
        )

    def _update_status(self, duplicates=None, disk_conflicts=None):
        count = len(self.entries)
        duplicates = duplicates or set()
        disk_conflicts = disk_conflicts or set()

        if count == 0:
            self.status_bar.showMessage(t("status.ready"))
            self.btn_apply.setEnabled(False)
            return

        previews = self.table.table_model.preview_names
        changed_count = sum(1 for e, n in zip(self.entries, previews) if e.original_name != n)

        has_conflicts = len(duplicates) > 0 or len(disk_conflicts) > 0
        self.btn_apply.setEnabled(changed_count > 0 and not has_conflicts)

        msg = t("status.summary", count=count, changed=changed_count)
        if duplicates:
            msg += f" | {t('status.conflicts', count=len(duplicates))}"
        if disk_conflicts:
            msg += f" | {t('status.disk_conflicts', count=len(disk_conflicts))}"

        self.status_bar.showMessage(msg)

    def _on_apply_clicked(self):
        previews = self.table.table_model.preview_names
        changed_ops: List[Tuple[Path, Path]] = []
        for entry, new_name in zip(self.entries, previews):
            if entry.original_name != new_name:
                dst = entry.parent_dir / new_name
                changed_ops.append((entry.path, dst))

        if not changed_ops:
            QMessageBox.information(self, t("dialog.no_changes_title"), t("dialog.no_changes_msg"))
            return

        # 授權與降級檢查 (7天試用期過後溫和降級)
        if not self.license_mgr.is_unlimited():
            # 1. 批次數量上限檢查 (免費版限 10 檔)
            allowed, limit_msg = self.license_mgr.check_batch_limit(len(changed_ops))
            if not allowed:
                reply = QMessageBox.warning(
                    self,
                    t("license.batch_limit_title"),
                    limit_msg,
                    QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Open
                )
                if reply == QMessageBox.StandardButton.Open:
                    self._on_license_clicked()
                return

            # 2. 進階規則功能檢查 (EXIF/ID3/Metadata、拼音、Regex)
            for rule in self.current_rules:
                rt = rule.__class__.__name__
                params = getattr(rule, "__dict__", {})
                allowed, rule_msg = self.license_mgr.check_rule_allowed(rt, params)
                if not allowed:
                    reply = QMessageBox.warning(
                        self,
                        t("license.pro_feature_title"),
                        rule_msg,
                        QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel,
                        QMessageBox.StandardButton.Open
                    )
                    if reply == QMessageBox.StandardButton.Open:
                        self._on_license_clicked()
                    return

        if self.settings.get("confirm_before_apply", True):
            reply = QMessageBox.question(
                self,
                t("dialog.confirm_rename_title"),
                t("dialog.confirm_rename_msg", count=len(changed_ops)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        progress_dialog = QProgressDialog(t("dialog.progress_title"), t("dialog.progress_cancel"), 0, len(changed_ops), self)
        progress_dialog.setWindowTitle(t("dialog.progress_title"))
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setMinimumDuration(0)

        self.rename_worker = RenameWorker(changed_ops, self)

        self.rename_worker.progress.connect(lambda cur, tot, name: (
            progress_dialog.setValue(cur),
            progress_dialog.setLabelText(t("dialog.renaming_progress", current=cur, total=tot, name=name))
        ))

        progress_dialog.canceled.connect(self.rename_worker.cancel)

        def _on_rename_finished(result: dict):
            progress_dialog.close()

            if result["success_ops"]:
                self.snapshot_manager.save_snapshot(result["success_ops"])
                self.rule_panel.reset_rules()

            self._update_undo_button_state()

            updated_paths = [op["renamed_path"] for op in result["success_ops"]]
            for e, n in zip(self.entries, previews):
                if e.original_name == n and e.path.exists():
                    updated_paths.append(str(e.path.resolve()))

            self.entries.clear()
            self._load_paths(list(set(updated_paths)))

            msg = f"{t('dialog.result_title')}\n\n{t('dialog.result_success', count=result['success_count'])}"
            if result["failed_count"] > 0:
                msg += f"\n{t('dialog.result_failed', count=result['failed_count'])}"
            msg += f"\n\n{t('dialog.result_undo_tip')}"

            QMessageBox.information(self, t("dialog.result_title"), msg)

        self.rename_worker.finished_batch.connect(_on_rename_finished)
        self.rename_worker.start()

    def _on_undo_clicked(self):
        reply = QMessageBox.question(
            self,
            t("dialog.confirm_undo_title"),
            t("dialog.confirm_undo_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        undo_result = self.snapshot_manager.undo_snapshot()
        self._update_undo_button_state()

        if undo_result["success"]:
            current_dirs = list({str(e.parent_dir) for e in self.entries if e.parent_dir.exists()})
            self.entries.clear()
            if current_dirs:
                self._load_paths(current_dirs)
            else:
                self._refresh_previews(full_reset=True)

            msg = t("dialog.undo_success_msg", count=undo_result.get("restored_count", 0))
            QMessageBox.information(self, t("dialog.undo_success_title"), msg)
        else:
            err_code = undo_result.get("error_code")
            if err_code == "no_snapshot" or "無可用的復原快照記錄" in undo_result.get("message", ""):
                err_msg = t("dialog.undo_no_snapshot")
            elif err_code == "read_failed":
                err_msg = t("dialog.undo_failed_msg", err=undo_result.get("error", ""))
            else:
                err_msg = undo_result.get("message") or t("dialog.undo_failed_msg", err="")
            QMessageBox.warning(self, t("dialog.undo_fail_title"), err_msg)
