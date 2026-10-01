"""
KyteRename - Settings Dialog (卡片分頁式設定對話框，具備黑曜石深色質感)
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QCheckBox, QComboBox, QSpinBox, QLabel, QPushButton,
    QMessageBox, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt
from config.settings import SettingsManager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KyteRename 設定")
        self.setFixedSize(480, 440)
        self.mgr = SettingsManager()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #282C34;
                border-radius: 6px;
                background-color: #1A1D21;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #16181B;
                color: #A0AEC0;
                padding: 7px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #282C34;
                border-bottom: none;
                margin-right: 2px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #1A1D21;
                color: #58A6FF;
                font-weight: bold;
                border-top: 2px solid #177DDC;
            }
            QTabBar::tab:hover:!selected {
                background-color: #21252B;
                color: #FFFFFF;
            }
        """)

        # 分頁 1：改名行為
        self.tab_behavior = self._build_behavior_tab()
        self.tabs.addTab(self.tab_behavior, "改名行為")

        # 分頁 2：快照與復原
        self.tab_snapshot = self._build_snapshot_tab()
        self.tabs.addTab(self.tab_snapshot, "快照與復原")

        # 分頁 3：介面與生態
        self.tab_integration = self._build_integration_tab()
        self.tabs.addTab(self.tab_integration, "介面與生態")

        layout.addWidget(self.tabs)

        # 底部操作按鈕
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_close = QPushButton("關閉")
        self.btn_close.setObjectName("btn_primary")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def _build_behavior_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setVerticalSpacing(12)

        self.chk_recursive = QCheckBox("拖入資料夾時掃描所有子目錄")
        self.chk_recursive.setChecked(bool(self.mgr.get("recursive_scan")))
        self.chk_recursive.toggled.connect(lambda v: self.mgr.set("recursive_scan", v))
        form.addRow("遞迴掃描：", self.chk_recursive)

        self.combo_conflict = QComboBox()
        self.combo_conflict.addItem("彈出視窗詢問 (Ask)", "ask")
        self.combo_conflict.addItem("自動略過不改 (Skip)", "skip")
        self.combo_conflict.addItem("自動增補後綴 _1 (Suffix)", "suffix")

        cur_policy = self.mgr.get("conflict_policy", "ask")
        idx = self.combo_conflict.findData(cur_policy)
        self.combo_conflict.setCurrentIndex(max(0, idx))
        self.combo_conflict.currentIndexChanged.connect(
            lambda: self.mgr.set("conflict_policy", self.combo_conflict.currentData())
        )
        form.addRow("衝突處理策略：", self.combo_conflict)

        self.chk_sanitize = QCheckBox(r'預先過濾 Windows 非法字元 (\/:*?"<>|)')
        self.chk_sanitize.setChecked(bool(self.mgr.get("auto_sanitize_illegal")))
        self.chk_sanitize.toggled.connect(lambda v: self.mgr.set("auto_sanitize_illegal", v))
        form.addRow("字元安全：", self.chk_sanitize)

        self.chk_confirm = QCheckBox("點擊執行時彈出清單確認對話框")
        self.chk_confirm.setChecked(bool(self.mgr.get("confirm_before_apply")))
        self.chk_confirm.toggled.connect(lambda v: self.mgr.set("confirm_before_apply", v))
        form.addRow("防呆提示：", self.chk_confirm)

        layout.addLayout(form)
        layout.addStretch()
        return widget

    def _build_snapshot_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setVerticalSpacing(12)

        self.spin_history = QSpinBox()
        self.spin_history.setRange(5, 50)
        self.spin_history.setValue(int(self.mgr.get("max_snapshot_history", 15)))
        self.spin_history.valueChanged.connect(lambda v: self.mgr.set("max_snapshot_history", v))
        form.addRow("歷史保留上限：", self.spin_history)

        self.combo_mode = QComboBox()
        self.combo_mode.addItem("系統 AppData (標準安裝模式)", "appdata")
        self.combo_mode.addItem("軟體資料夾 snapshots/ (便攜模式)", "portable")
        cur_mode = self.mgr.get("snapshot_dir_mode", "appdata")
        self.combo_mode.setCurrentIndex(0 if cur_mode == "appdata" else 1)
        self.combo_mode.currentIndexChanged.connect(self._on_snapshot_mode_changed)
        form.addRow("儲存位置：", self.combo_mode)

        layout.addLayout(form)

        group = QGroupBox("歷史維護")
        grp_layout = QVBoxLayout(group)
        btn_clear = QPushButton("🗑️ 立即清空所有歷史還原快照")
        btn_clear.clicked.connect(self._clear_snapshots)
        grp_layout.addWidget(btn_clear)
        layout.addWidget(group)

        layout.addStretch()
        return widget

    def _on_snapshot_mode_changed(self):
        new_mode = self.combo_mode.currentData()
        old_mode = self.mgr.get("snapshot_dir_mode", "appdata")

        if new_mode != old_mode:
            # 詢問是否遷移舊快照
            reply = QMessageBox.question(
                self,
                "快照目錄變更",
                "偵測到快照儲存位置變更，是否自動將既有的歷史快照檔案遷移至新目錄？\n\n（建議遷移，以保留先前的還原記錄）",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                moved = self.mgr.migrate_snapshots(old_mode, new_mode)
                QMessageBox.information(self, "遷移完成", f"已成功遷移 {moved} 筆歷史快照檔案。")

            self.mgr.set("snapshot_dir_mode", new_mode)

    def _build_integration_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setVerticalSpacing(12)

        self.chk_win_size = QCheckBox("記錄離開時的視窗大小與分隔比例")
        self.chk_win_size.setChecked(bool(self.mgr.get("remember_window_size")))
        self.chk_win_size.toggled.connect(lambda v: self.mgr.set("remember_window_size", v))
        form.addRow("視窗狀態：", self.chk_win_size)

        self.chk_rules = QCheckBox("啟動時保留上次編輯的改名規則 (建議關閉)")
        self.chk_rules.setChecked(bool(self.mgr.get("remember_last_rules")))
        self.chk_rules.toggled.connect(lambda v: self.mgr.set("remember_last_rules", v))
        form.addRow("規則記憶：", self.chk_rules)

        self.chk_preview = QCheckBox("選中清單項目按 Space 呼叫 KyteView 快速預覽")
        self.chk_preview.setChecked(bool(self.mgr.get("enable_space_preview")))
        self.chk_preview.toggled.connect(lambda v: self.mgr.set("enable_space_preview", v))
        form.addRow("軟體聯動：", self.chk_preview)

        layout.addLayout(form)
        layout.addStretch()
        return widget

    def _clear_snapshots(self):
        ret = QMessageBox.question(
            self, "確認清理",
            "確定要清空所有改名還原快照嗎？\n清空後將無法再執行歷史還原！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            snap_dir = self.mgr.get_snapshot_dir()
            count = 0
            for f in snap_dir.glob("snapshot_*.json"):
                try:
                    f.unlink()
                    count += 1
                except Exception:
                    pass
            QMessageBox.information(self, "完成", f"已成功清除 {count} 筆快照記錄。")
