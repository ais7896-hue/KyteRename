"""
KyteRename - Settings Dialog (卡片分頁式設定對話框，含聯絡技術支援與系統診斷資訊複製)
"""
import sys
import platform
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QCheckBox, QComboBox, QSpinBox, QLabel, QPushButton,
    QMessageBox, QFormLayout, QGroupBox, QFrame, QApplication,
    QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QTimer
from config.settings import SettingsManager
from ui.styles import get_theme_stylesheet

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KyteRename 設定")
        self.setFixedSize(530, 460)
        self.mgr = SettingsManager()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._init_ui()
        self._load_current_values()
        self._apply_dialog_styles()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self.tabs = QTabWidget()

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

        # 底部操作列：左側支援連結與診斷資訊，右側取消與儲存按鈕
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 8, 0, 0)
        bottom_bar.setSpacing(12)

        # 支援連結 (KyteView 同款樣式)
        mailto_support = (
            "mailto:support@aisming.com?subject=%5B%E5%95%8F%E9%A1%8C%E5%9B%9E%E5%A0%B1%5D%20KyteRename%20%E4%BD%BF%E7%94%A8%E8%AB%AE%E8%A9%A2%20-%20%E8%A8%82%E5%96%AE/%E5%BA%8F%E8%99%9F%EF%BC%9A(%E8%8B%A5%E6%9C%89%E8%AB%8B%E5%A1%AB%E5%AF%AB)"
            "&body=1.%20%E4%BD%9C%E6%A5%AD%E7%B3%BB%E7%B5%B1%E7%89%88%E6%9C%AC%EF%BC%9A%0A"
            "2.%20%E7%99%BC%E7%94%9F%E7%9A%84%E5%95%8F%E9%A1%8C%E6%8F%8F%E8%BF%B0%EF%BC%9A%0A"
            "3.%20%E8%A8%BA%E6%96%B7%E8%B3%87%E8%A8%8A%EF%BC%88%E8%AB%8B%E8%B2%BC%E4%B8%8A%E9%BB%9E%E6%93%8A%E3%80%8C%E8%A4%87%E8%A3%BD%E7%B3%BB%E7%B5%B1%E8%A8%BA%E6%96%B7%E8%B3%87%E8%A8%8A%E3%80%8D%E5%BE%8C%E7%9A%84%E5%85%A7%E5%AE%B9%EF%BC%89%EF%BC%9A%0A"
        )
        self.lbl_support = QLabel(f"<a href='{mailto_support}' style='color: #818cf8; text-decoration: none;'>✉ 聯絡技術支援</a>")
        self.lbl_support.setOpenExternalLinks(True)
        self.lbl_support.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_support.setStyleSheet("font-size: 11px;")
        bottom_bar.addWidget(self.lbl_support)

        # 垂直分隔線
        v_sep = QFrame()
        v_sep.setObjectName("dialog_v_sep")
        v_sep.setFrameShape(QFrame.Shape.VLine)
        v_sep.setFrameShadow(QFrame.Shadow.Plain)
        v_sep.setFixedHeight(18)
        bottom_bar.addWidget(v_sep)

        # 複製系統診斷資訊按鈕 (KyteView 同款虛線樣式)
        self.btn_diag = QPushButton("📋 複製系統診斷資訊")
        self.btn_diag.setObjectName("btn_dialog_diag")
        self.btn_diag.setFixedHeight(30)
        self.btn_diag.setStyleSheet("""
            QPushButton#btn_dialog_diag {
                background-color: transparent;
                color: #a1a1aa;
                border: 1px dashed #3f3f46;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton#btn_dialog_diag:hover {
                background-color: rgba(99, 102, 241, 0.14);
                color: #818cf8;
                border: 1px solid #818cf8;
            }
        """)
        self.btn_diag.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_diag.setToolTip("收集當前作業系統、軟體版本、螢幕解析度與配置設定複製至剪貼簿，方便回報問題")
        self.btn_diag.clicked.connect(self._copy_diagnostic_info)
        bottom_bar.addWidget(self.btn_diag)

        self.btn_open_license = QPushButton("💎 專業版授權")
        self.btn_open_license.setFixedHeight(30)
        self.btn_open_license.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_license.setToolTip("查看當前 7 天試用天數、輸入序號啟用或管理授權")
        self.btn_open_license.clicked.connect(self._on_open_license_clicked)
        bottom_bar.addWidget(self.btn_open_license)

        bottom_bar.addStretch()

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        bottom_bar.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("💾 儲存設定")
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.clicked.connect(self._on_save_clicked)
        bottom_bar.addWidget(self.btn_save)

        layout.addLayout(bottom_bar)

    def _build_behavior_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setVerticalSpacing(12)

        self.chk_recursive = QCheckBox("拖入資料夾時掃描所有子目錄")
        form.addRow("遞迴掃描：", self.chk_recursive)

        self.combo_conflict = QComboBox()
        self.combo_conflict.addItem("彈出視窗詢問 (Ask)", "ask")
        self.combo_conflict.addItem("自動略過不改 (Skip)", "skip")
        self.combo_conflict.addItem("自動增補後綴 _1 (Suffix)", "suffix")
        form.addRow("衝突處理策略：", self.combo_conflict)

        self.chk_sanitize = QCheckBox(r'預先過濾 Windows 非法字元 (\/:*?"<>|)')
        form.addRow("字元安全：", self.chk_sanitize)

        self.chk_confirm = QCheckBox("點擊執行時彈出清單確認對話框")
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
        form.addRow("歷史保留上限：", self.spin_history)

        self.combo_mode = QComboBox()
        self.combo_mode.addItem("系統 AppData (標準安裝模式)", "appdata")
        self.combo_mode.addItem("軟體資料夾 snapshots/ (便攜模式)", "portable")
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

    def _build_integration_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. 外觀模式 (Appearance Mode)
        grp_theme = QGroupBox("外觀模式 (Appearance Mode)")
        grp_theme_layout = QVBoxLayout(grp_theme)
        grp_theme_layout.setSpacing(10)

        theme_btn_row = QHBoxLayout()
        self.rb_theme_system = QRadioButton("跟隨系統 (System)")
        self.rb_theme_dark = QRadioButton("深色模式 (Dark)")
        self.rb_theme_light = QRadioButton("淺色模式 (Light)")

        self.theme_btn_group = QButtonGroup(self)
        self.theme_btn_group.addButton(self.rb_theme_system, 0)
        self.theme_btn_group.addButton(self.rb_theme_dark, 1)
        self.theme_btn_group.addButton(self.rb_theme_light, 2)
        self.theme_btn_group.idClicked.connect(self._on_theme_radio_clicked)

        theme_btn_row.addWidget(self.rb_theme_system)
        theme_btn_row.addWidget(self.rb_theme_dark)
        theme_btn_row.addWidget(self.rb_theme_light)
        theme_btn_row.addStretch()
        grp_theme_layout.addLayout(theme_btn_row)

        lbl_theme_hint = QLabel("💡 選擇跟隨系統將自動即時響應 Windows 11/10 的深淺色外觀。")
        lbl_theme_hint.setStyleSheet("font-size: 11px; color: #71717a;")
        grp_theme_layout.addWidget(lbl_theme_hint)
        layout.addWidget(grp_theme)

        # 2. 視窗與聯動偏好
        grp_behavior = QGroupBox("視窗與生態聯動")
        grp_behavior_layout = QVBoxLayout(grp_behavior)
        form = QFormLayout()
        form.setVerticalSpacing(12)

        self.chk_win_size = QCheckBox("記錄離開時的視窗大小與分隔比例")
        form.addRow("視窗狀態：", self.chk_win_size)

        self.chk_rules = QCheckBox("啟動時保留上次編輯的改名規則 (建議關閉)")
        form.addRow("規則記憶：", self.chk_rules)

        self.chk_preview = QCheckBox("選中清單項目按 Space 呼叫 KyteView 快速預覽")
        form.addRow("軟體聯動：", self.chk_preview)

        grp_behavior_layout.addLayout(form)
        layout.addWidget(grp_behavior)

        layout.addStretch()
        return widget


    def _on_theme_radio_clicked(self, btn_id: int):
        theme_val = {0: "system", 1: "dark", 2: "light"}.get(btn_id, "system")
        self.mgr.set("theme_mode", theme_val)
        self._apply_dialog_styles()

    def _apply_dialog_styles(self):
        """根據深淺色模式徹底、全面為對話框與所有內部元件設定配色，杜絕任何淺色漏光"""
        is_dark = self.mgr.is_dark()

        # 同步全域主程式樣式
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_theme_stylesheet(is_dark))

        dlg_bg = "#121315" if is_dark else "#F5F6F8"
        tab_pane_bg = "#16181B" if is_dark else "#FFFFFF"
        tab_bg = "#1A1D21" if is_dark else "#F3F4F6"
        tab_active_bg = "#16181B" if is_dark else "#FFFFFF"
        tab_active_color = "#58A6FF" if is_dark else "#1677FF"
        tab_text = "#8C94A0" if is_dark else "#6B7280"
        tab_hover = "#282C34" if is_dark else "#E5E7EB"

        text_c = "#E2E4E8" if is_dark else "#1F2937"
        text_dim = "#8C94A0" if is_dark else "#6B7280"
        border_c = "#282C34" if is_dark else "#E5E7EB"
        input_border = "#2E3238" if is_dark else "#D1D5DB"
        input_bg = "#1A1D21" if is_dark else "#FFFFFF"
        accent_c = "#177DDC" if is_dark else "#1677FF"
        btn_cancel_bg = "#21252B" if is_dark else "#FFFFFF"
        btn_cancel_hover = "#282C34" if is_dark else "#F3F4F6"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {dlg_bg};
                color: {text_c};
            }}
            QWidget {{
                color: {text_c};
                font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
            }}
            QTabWidget::pane {{
                border: 1px solid {border_c};
                border-radius: 8px;
                background-color: {tab_pane_bg};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {tab_bg};
                color: {tab_text};
                border: 1px solid {border_c};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 18px;
                margin-right: 4px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {tab_active_bg};
                color: {tab_active_color};
                border-top: 2px solid {accent_c};
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {tab_hover};
                color: {text_c};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {border_c};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 14px;
                padding-bottom: 8px;
                padding-left: 10px;
                padding-right: 10px;
                background-color: {'rgba(255, 255, 255, 0.02)' if is_dark else '#FFFFFF'};
                color: {text_dim};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 4px;
                color: {text_c};
            }}
            QLabel {{
                color: {text_c};
                background: transparent;
            }}
            QRadioButton, QCheckBox {{
                color: {text_c};
                spacing: 8px;
                background: transparent;
            }}
            QRadioButton:hover, QCheckBox:hover {{
                color: {'#FFFFFF' if is_dark else '#000000'};
            }}
            QComboBox, QSpinBox {{
                background-color: {input_bg};
                color: {text_c};
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 4px 8px;
            }}
            QComboBox:focus, QSpinBox:focus {{
                border: 1px solid {accent_c};
            }}
            QComboBox QAbstractItemView {{
                background-color: {input_bg};
                color: {text_c};
                border: 1px solid {border_c};
                selection-background-color: {accent_c};
                selection-color: #FFFFFF;
            }}
            QPushButton#btn_dialog_cancel {{
                background-color: {btn_cancel_bg};
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 6px 14px;
                color: {text_c};
                font-weight: 500;
            }}
            QPushButton#btn_dialog_cancel:hover {{
                background-color: {btn_cancel_hover};
                color: {'#FFFFFF' if is_dark else '#111827'};
            }}
            QPushButton#btn_primary {{
                background-color: {accent_c};
                border: 1px solid {accent_c};
                border-radius: 6px;
                padding: 6px 14px;
                color: #FFFFFF;
                font-weight: bold;
            }}
            QPushButton#btn_primary:hover {{
                background-color: {'#1668B8' if is_dark else '#0958D9'};
            }}
            QFrame#dialog_v_sep {{
                background-color: {'#3f3f46' if is_dark else '#E5E7EB'};
                border: none;
                width: 1px;
                margin: 0 4px;
            }}
            QPushButton#btn_dialog_diag {{
                background-color: transparent;
                color: {'#a1a1aa' if is_dark else '#4B5563'};
                border: 1px dashed {'#3f3f46' if is_dark else '#D1D5DB'};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton#btn_dialog_diag:hover {{
                background-color: {'rgba(99, 102, 241, 0.14)' if is_dark else 'rgba(99, 102, 241, 0.08)'};
                color: {'#818cf8' if is_dark else '#4F46E5'};
                border: 1px solid {'#818cf8' if is_dark else '#4F46E5'};
            }}
        """)

        # 支援信箱文字顏色
        mail_color = "#818cf8" if is_dark else "#4f46e5"
        mailto_support = (
            "mailto:support@aisming.com?subject=%5B%E5%95%8F%E9%A1%8C%E5%9B%9E%E5%A0%B1%5D%20KyteRename%20%E4%BD%BF%E7%94%A8%E8%AB%AE%E8%A9%A2%20-%20%E8%A8%82%E5%96%AE/%E5%BA%8F%E8%99%9F%EF%BC%9A(%E8%8B%A5%E6%9C%89%E8%AB%8B%E5%A1%AB%E5%AF%AB)"
            "&body=1.%20%E4%BD%9C%E6%A5%AD%E7%B3%BB%E7%B5%B1%E7%89%88%E6%9C%AC%EF%BC%9A%0A"
            "2.%20%E7%99%BC%E7%94%9F%E7%9A%84%E5%95%8F%E9%A1%8C%E6%8F%8F%E8%BF%B0%EF%BC%9A%0A"
            "3.%20%E8%A8%BA%E6%96%B7%E8%B3%87%E8%A8%8A%EF%BC%88%E8%AB%8B%E8%B2%BC%E4%B8%8A%E9%BB%9E%E6%93%8A%E3%80%8C%E8%A4%87%E8%A3%BD%E7%B3%BB%E7%B5%B1%E8%A8%BA%E6%96%B7%E8%B3%87%E8%A8%8A%E3%80%8D%E5%BE%8C%E7%9A%84%E5%85%A7%E5%AE%B9%EF%BC%89%EF%BC%9A%0A"
        )
        self.lbl_support.setText(f"<a href='{mailto_support}' style='color: {mail_color}; text-decoration: none;'>✉ 聯絡技術支援</a>")

    def _load_current_values(self):
        """讀取目前設定並載入至各個表單控制項"""
        # 分頁 1
        self.chk_recursive.setChecked(bool(self.mgr.get("recursive_scan", False)))
        cur_policy = self.mgr.get("conflict_policy", "ask")
        idx = self.combo_conflict.findData(cur_policy)
        self.combo_conflict.setCurrentIndex(max(0, idx))
        self.chk_sanitize.setChecked(bool(self.mgr.get("auto_sanitize_illegal", True)))
        self.chk_confirm.setChecked(bool(self.mgr.get("confirm_before_apply", True)))

        # 分頁 2
        self.spin_history.setValue(int(self.mgr.get("max_snapshot_history", 15)))
        cur_mode = self.mgr.get("snapshot_dir_mode", "appdata")
        self.combo_mode.setCurrentIndex(0 if cur_mode == "appdata" else 1)

        # 分頁 3
        cur_theme = self.mgr.get("theme_mode", "system")
        if cur_theme == "dark":
            self.rb_theme_dark.setChecked(True)
        elif cur_theme == "light":
            self.rb_theme_light.setChecked(True)
        else:
            self.rb_theme_system.setChecked(True)

        self.chk_win_size.setChecked(bool(self.mgr.get("remember_window_size", True)))
        self.chk_rules.setChecked(bool(self.mgr.get("remember_last_rules", False)))
        self.chk_preview.setChecked(bool(self.mgr.get("enable_space_preview", True)))

    def _on_save_clicked(self):
        """點擊儲存按鈕：驗證、遷移資料、寫入設定並回報成功"""
        new_mode = self.combo_mode.currentData()
        old_mode = self.mgr.get("snapshot_dir_mode", "appdata")

        if new_mode != old_mode:
            reply = QMessageBox.question(
                self,
                "快照目錄變更確認",
                "偵測到快照儲存位置已變更，是否自動將既有的歷史快照檔案遷移至新目錄？\n\n（建議遷移，以確保歷史還原功能可正常使用）",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                moved = self.mgr.migrate_snapshots(old_mode, new_mode)
                if moved > 0:
                    QMessageBox.information(self, "遷移成功", f"已成功遷移 {moved} 筆歷史快照至新目錄。")

        self.mgr.set("recursive_scan", self.chk_recursive.isChecked())
        self.mgr.set("conflict_policy", self.combo_conflict.currentData())
        self.mgr.set("auto_sanitize_illegal", self.chk_sanitize.isChecked())
        self.mgr.set("confirm_before_apply", self.chk_confirm.isChecked())

        self.mgr.set("max_snapshot_history", self.spin_history.value())
        self.mgr.set("snapshot_dir_mode", new_mode)

        selected_theme_id = self.theme_btn_group.checkedId()
        theme_val = {0: "system", 1: "dark", 2: "light"}.get(selected_theme_id, "system")
        self.mgr.set("theme_mode", theme_val)

        self.mgr.set("remember_window_size", self.chk_win_size.isChecked())
        self.mgr.set("remember_last_rules", self.chk_rules.isChecked())
        self.mgr.set("enable_space_preview", self.chk_preview.isChecked())

        QMessageBox.information(self, "設定已儲存", "✓ 偏好設定已成功更新並儲存！")
        self.accept()


    def _on_open_license_clicked(self):
        diag = LicenseDialog(self)
        diag.exec()
    def _copy_diagnostic_info(self):
        """收集軟硬體環境資訊複製至剪貼簿"""
        lines = [
            "```yaml",
            "# KyteRename 系統環境診斷資訊",
            "Software: KyteRename v1.0.0 (64-bit)",
            f"Python_Version: {platform.python_version()} ({platform.architecture()[0]})",
            f"OS: {platform.system()} {sys.getwindowsversion().major}.{sys.getwindowsversion().minor} (Build {sys.getwindowsversion().build})",
        ]

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            dpr = screen.devicePixelRatio()
            lines.append(f"Screen_Primary: {geo.width()}x{geo.height()} @ DPR {dpr:.2f} ({int(dpr * 100)}%)")
            lines.append(f"Screen_Count: {len(QApplication.screens())}")

        lines.append(f"Config_Directory: {str(self.mgr.config_dir)}")
        lines.append(f"Snapshot_Mode: {self.mgr.get('snapshot_dir_mode', 'appdata')}")
        lines.append(f"Recursive_Scan: {self.mgr.get('recursive_scan', False)}")
        lines.append(f"Conflict_Policy: {self.mgr.get('conflict_policy', 'ask')}")
        lines.append(f"Space_Preview_Enabled: {self.mgr.get('enable_space_preview', True)}")
        lines.append("```")

        diag_text = "\n".join(lines)
        QApplication.clipboard().setText(diag_text)

        self.btn_diag.setText("✓ 已複製診斷資訊！")
        self.btn_diag.setStyleSheet("""
            QPushButton#btn_dialog_diag {
                background-color: rgba(16, 185, 129, 0.14);
                color: #10b981;
                border: 1px solid #10b981;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        diag_default_qss = """
            QPushButton#btn_dialog_diag {
                background-color: transparent;
                color: #a1a1aa;
                border: 1px dashed #3f3f46;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton#btn_dialog_diag:hover {
                background-color: rgba(99, 102, 241, 0.14);
                color: #818cf8;
                border: 1px solid #818cf8;
            }
        """
        QTimer.singleShot(2500, lambda: (
            self.btn_diag.setText("📋 複製系統診斷資訊"),
            self.btn_diag.setStyleSheet(diag_default_qss)
        ))

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
