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
from ui.styles import get_theme_stylesheet, CHECK_WHITE
from i18n import t, i18n

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("settings.title"))
        self.setFixedSize(680, 500)
        self.mgr = SettingsManager()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._init_ui()
        self._load_current_values()
        self._apply_dialog_styles()

    def _get_mailto_url(self) -> str:
        is_en = i18n.current_language == "en_US"
        if is_en:
            return (
                "mailto:support@aisming.com?subject=%5BBug%20Report%5D%20KyteRename%20Support%20-%20Order/License%20Key:%20(Optional)"
                "&body=1.%20OS%20Version:%0A"
                "2.%20Issue%20Description:%0A"
                "3.%20Diagnostics%20(Please%20paste%20content%20after%20clicking%20'Copy%20System%20Diagnostics'):%0A"
            )
        return (
            "mailto:support@aisming.com?subject=%5B%E5%95%8F%E9%A1%8C%E5%9B%9E%E5%A0%B1%5D%20KyteRename%20%E4%BD%BF%E7%94%A8%E8%AB%AE%E8%A9%A2%20-%20%E8%A8%82%E5%96%AE/%E5%BA%8F%E8%99%9F%EF%BC%9A(%E8%8B%A5%E6%9C%89%E8%AB%8B%E5%A1%AB%E5%AF%AB)"
            "&body=1.%20%E4%BD%9C%E6%A5%AD%E7%B3%BB%E7%B5%B1%E7%89%88%E6%9C%AC%EF%BC%9A%0A"
            "2.%20%E7%99%BC%E7%94%9F%E7%9A%84%E5%95%8F%E9%A1%8C%E6%8F%8F%E8%BF%B0%EF%BC%9A%0A"
            "3.%20%E8%A8%BA%E6%96%B7%E8%B3%87%E8%A8%8A%EF%BC%88%E8%AB%8B%E8%B2%BC%E4%B8%8A%E9%BB%9E%E6%93%8A%E3%80%8C%E8%A4%87%E8%A3%BD%E7%B3%BB%E7%B5%B1%E8%A8%BA%E6%96%B7%E8%B3%87%E8%A8%8A%E3%80%8D%E5%BE%8C%E7%9A%84%E5%85%A7%E5%AE%B9%EF%BC%89%EF%BC%9A%0A"
        )

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget()

        # 分頁 1：改名行為
        self.tab_behavior = self._build_behavior_tab()
        self.tabs.addTab(self.tab_behavior, t("settings.tab_behavior"))

        # 分頁 2：快照與復原
        self.tab_snapshot = self._build_snapshot_tab()
        self.tabs.addTab(self.tab_snapshot, t("settings.tab_snapshot"))

        # 分頁 3：介面與生態
        self.tab_integration = self._build_integration_tab()
        self.tabs.addTab(self.tab_integration, t("settings.tab_integration"))

        layout.addWidget(self.tabs)

        # 底部操作列：左側支援連結與診斷資訊，右側取消與儲存按鈕
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 8, 0, 0)
        bottom_bar.setSpacing(10)

        # 支援連結 (KyteView 同款樣式)
        self.lbl_support = QLabel(f"<a href='{self._get_mailto_url()}' style='color: #818cf8; text-decoration: none;'>{t('settings.support_email')}</a>")
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
        self.btn_diag = QPushButton(t("settings.copy_diag"))
        self.btn_diag.setObjectName("btn_dialog_diag")
        self.btn_diag.setFixedHeight(30)
        self.btn_diag.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_diag.setToolTip(t("settings.copy_diag_tooltip"))
        self.btn_diag.clicked.connect(self._copy_diagnostic_info)
        bottom_bar.addWidget(self.btn_diag)

        self.btn_open_license = QPushButton(t("settings.license_btn"))
        self.btn_open_license.setObjectName("btn_dialog_license")
        self.btn_open_license.setFixedHeight(30)
        self.btn_open_license.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_license.setToolTip(t("settings.license_tooltip"))
        self.btn_open_license.clicked.connect(self._on_open_license_clicked)
        bottom_bar.addWidget(self.btn_open_license)

        self.btn_check_update = QPushButton(t("settings.check_update", default="檢查更新"))
        self.btn_check_update.setObjectName("btn_dialog_license")
        self.btn_check_update.setFixedHeight(30)
        self.btn_check_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check_update.clicked.connect(self._on_check_update_clicked)
        bottom_bar.addWidget(self.btn_check_update)

        bottom_bar.addStretch()

        self.btn_cancel = QPushButton(t("settings.cancel"))
        self.btn_cancel.setObjectName("btn_dialog_cancel")
        self.btn_cancel.setFixedHeight(30)
        self.btn_cancel.clicked.connect(self.reject)
        bottom_bar.addWidget(self.btn_cancel)

        self.btn_save = QPushButton(t("settings.save"))
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.setFixedHeight(30)
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

        self.chk_recursive = QCheckBox(t("settings.recursive_scan"))
        form.addRow(t("settings.lbl_recursive"), self.chk_recursive)

        self.combo_conflict = QComboBox()
        self.combo_conflict.addItem(t("settings.conflict_ask"), "ask")
        self.combo_conflict.addItem(t("settings.conflict_skip"), "skip")
        self.combo_conflict.addItem(t("settings.conflict_suffix"), "suffix")
        form.addRow(t("settings.lbl_conflict"), self.combo_conflict)

        self.chk_sanitize = QCheckBox(t("settings.auto_sanitize"))
        form.addRow(t("settings.lbl_sanitize"), self.chk_sanitize)

        self.chk_confirm = QCheckBox(t("settings.confirm_before_apply"))
        form.addRow(t("settings.lbl_confirm"), self.chk_confirm)

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
        form.addRow(t("settings.lbl_max_history"), self.spin_history)

        self.combo_mode = QComboBox()
        self.combo_mode.addItem(t("settings.snapshot_appdata"), "appdata")
        self.combo_mode.addItem(t("settings.snapshot_portable"), "portable")
        form.addRow(t("settings.lbl_snapshot_mode"), self.combo_mode)

        layout.addLayout(form)

        group = QGroupBox(t("settings.grp_history_maintenance"))
        grp_layout = QVBoxLayout(group)
        btn_clear = QPushButton(t("settings.btn_clear_snapshots"))
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
        grp_theme = QGroupBox(t("settings.grp_appearance"))
        grp_theme_layout = QVBoxLayout(grp_theme)
        grp_theme_layout.setSpacing(10)

        theme_btn_row = QHBoxLayout()
        self.rb_theme_system = QRadioButton(t("settings.theme_system"))
        self.rb_theme_dark = QRadioButton(t("settings.theme_dark"))
        self.rb_theme_light = QRadioButton(t("settings.theme_light"))

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

        lbl_theme_hint = QLabel(t("settings.theme_hint"))
        lbl_theme_hint.setStyleSheet("font-size: 11px; color: #71717a;")
        grp_theme_layout.addWidget(lbl_theme_hint)
        layout.addWidget(grp_theme)

        # 2. 語言設定 (Language)
        grp_lang = QGroupBox(t("settings.lbl_language"))
        grp_lang_layout = QVBoxLayout(grp_lang)
        lang_form = QFormLayout()
        lang_form.setVerticalSpacing(12)
        self.combo_language = QComboBox()
        self.combo_language.addItem(t("settings.lang_system"), "system")
        self.combo_language.addItem("繁體中文 (Traditional Chinese)", "zh_TW")
        self.combo_language.addItem("English", "en_US")
        lang_form.addRow(t("settings.lbl_language"), self.combo_language)
        grp_lang_layout.addLayout(lang_form)
        layout.addWidget(grp_lang)

        # 3. 視窗與聯動偏好
        grp_behavior = QGroupBox(t("settings.grp_behavior"))
        grp_behavior_layout = QVBoxLayout(grp_behavior)
        form = QFormLayout()
        form.setVerticalSpacing(12)

        self.chk_win_size = QCheckBox(t("settings.remember_window_size"))
        form.addRow(t("settings.lbl_win_size"), self.chk_win_size)

        self.chk_rules = QCheckBox(t("settings.remember_last_rules"))
        form.addRow(t("settings.lbl_rules"), self.chk_rules)

        self.chk_preview = QCheckBox(t("settings.enable_space_preview"))
        form.addRow(t("settings.lbl_preview"), self.chk_preview)

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
            QCheckBox {{
                color: {text_c};
                spacing: 8px;
                background: transparent;
            }}
            QCheckBox:hover {{
                color: {'#FFFFFF' if is_dark else '#000000'};
            }}
            QCheckBox::indicator {{
                width: 15px;
                height: 15px;
                border: 1.5px solid {'#5A6474' if is_dark else '#9CA3AF'};
                border-radius: 4px;
                background-color: {'#1A1D21' if is_dark else '#FFFFFF'};
            }}
            QCheckBox::indicator:hover {{
                border: 1.5px solid {accent_c};
                background-color: {'#23272E' if is_dark else '#F8FAFC'};
            }}
            QCheckBox::indicator:checked {{
                border: 1.5px solid {accent_c};
                background-color: {accent_c};
                image: url({CHECK_WHITE});
            }}
            QCheckBox::indicator:checked:hover {{
                border: 1.5px solid {'#3B99FC' if is_dark else '#4096FF'};
                background-color: {'#3B99FC' if is_dark else '#4096FF'};
            }}
            QCheckBox::indicator:disabled {{
                border: 1.5px solid {'#333842' if is_dark else '#D1D5DB'};
                background-color: {'#16181B' if is_dark else '#F3F4F6'};
            }}
            QRadioButton {{
                color: {text_c};
                spacing: 8px;
                background: transparent;
            }}
            QRadioButton:hover {{
                color: {'#FFFFFF' if is_dark else '#000000'};
            }}
            QRadioButton::indicator {{
                width: 15px;
                height: 15px;
                border-radius: 8px;
                border: 1.5px solid {'#5A6474' if is_dark else '#9CA3AF'};
                background-color: {'#1A1D21' if is_dark else '#FFFFFF'};
            }}
            QRadioButton::indicator:hover {{
                border: 1.5px solid {accent_c};
                background-color: {'#23272E' if is_dark else '#F8FAFC'};
            }}
            QRadioButton::indicator:checked {{
                border: 4.5px solid {accent_c};
                background-color: #FFFFFF;
            }}
            QRadioButton::indicator:checked:hover {{
                border: 4.5px solid {'#3B99FC' if is_dark else '#4096FF'};
                background-color: #FFFFFF;
            }}
            QRadioButton::indicator:disabled {{
                border: 1.5px solid {'#333842' if is_dark else '#D1D5DB'};
                background-color: {'#16181B' if is_dark else '#F3F4F6'};
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
            QPushButton#btn_dialog_license {{
                background-color: transparent;
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 4px 10px;
                color: {text_c};
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton#btn_dialog_license:hover {{
                background-color: {btn_cancel_hover};
                color: {'#FFFFFF' if is_dark else '#111827'};
            }}
            QPushButton#btn_dialog_cancel {{
                background-color: {btn_cancel_bg};
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 4px 14px;
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
                padding: 4px 14px;
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

        # 支援信箱文字顏色與多語言連結
        mail_color = "#818cf8" if is_dark else "#4f46e5"
        self.lbl_support.setText(
            f"<a href='{self._get_mailto_url()}' style='color: {mail_color}; text-decoration: none;'>{t('settings.support_email')}</a>"
        )

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

        cur_lang = self.mgr.get("language", "system")
        lang_idx = self.combo_language.findData(cur_lang)
        self.combo_language.setCurrentIndex(max(0, lang_idx))

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
                t("settings.migrate_title"),
                t("settings.migrate_msg"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                moved = self.mgr.migrate_snapshots(old_mode, new_mode)
                if moved > 0:
                    QMessageBox.information(self, t("settings.migrate_success_title"), t("settings.migrate_success_msg", count=moved))

        self.mgr.set("recursive_scan", self.chk_recursive.isChecked())
        self.mgr.set("conflict_policy", self.combo_conflict.currentData())
        self.mgr.set("auto_sanitize_illegal", self.chk_sanitize.isChecked())
        self.mgr.set("confirm_before_apply", self.chk_confirm.isChecked())

        self.mgr.set("max_snapshot_history", self.spin_history.value())
        self.mgr.set("snapshot_dir_mode", new_mode)

        selected_theme_id = self.theme_btn_group.checkedId()
        theme_val = {0: "system", 1: "dark", 2: "light"}.get(selected_theme_id, "system")
        self.mgr.set("theme_mode", theme_val)

        new_lang = self.combo_language.currentData()
        self.mgr.set("language", new_lang)

        self.mgr.set("remember_window_size", self.chk_win_size.isChecked())
        self.mgr.set("remember_last_rules", self.chk_rules.isChecked())
        self.mgr.set("enable_space_preview", self.chk_preview.isChecked())

        QMessageBox.information(self, t("settings.save_success_title"), t("settings.save_success_msg"))
        self.accept()


    def _on_open_license_clicked(self):
        diag = LicenseDialog(self)
        diag.exec()

    def _on_check_update_clicked(self):
        parent_win = self.parent()
        if parent_win and hasattr(parent_win, "check_for_updates"):
            parent_win.check_for_updates(silent=False)
        else:
            QMessageBox.information(self, t("settings.check_update", default="檢查更新"), "目前已是最新版本 (v1.1.3)。")
    
    def _copy_diagnostic_info(self):
        """收集軟硬體環境資訊複製至剪貼簿"""
        lines = [
            "```yaml",
            "# KyteRename 系統環境診斷資訊",
            "Software: KyteRename v1.1.3 (64-bit)",
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

        self.btn_diag.setText(t("settings.diag_copied"))
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
            self.btn_diag.setText(t("settings.copy_diag")),
            self.btn_diag.setStyleSheet(diag_default_qss)
        ))

    def _clear_snapshots(self):
        ret = QMessageBox.question(
            self, t("settings.clear_confirm_title"),
            t("settings.clear_confirm_msg"),
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
            QMessageBox.information(self, t("settings.clear_success_title"), t("settings.clear_success_msg", count=count))
