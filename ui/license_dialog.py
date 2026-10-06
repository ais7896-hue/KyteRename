"""
ui/license_dialog.py
KyteRename 授權啟用與方案狀態視窗：
- 完美支援深色/淺色/跟隨系統模式
- 7 天免費試用期倒數提示 (已過期溫和降級 / 專業版永久授權)
- 輸入序號即時線上驗證與機器碼綁定
- 複製機器碼與前往購買指引
- 客服支援 support@aisming.com
"""
from __future__ import annotations

import webbrowser
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QMessageBox, QApplication, QWidget,
)

from core.license import LicenseManager
from config.settings import SettingsManager
from i18n import t, i18n


class LicenseDialog(QDialog):
    """授權啟用與狀態管理對話框。"""
    PURCHASE_URL = "https://github.com/ais7896-hue/KyteRename"

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.license_mgr = LicenseManager.get_instance()
        self.setWindowTitle(t("license.title"))
        self.setFixedSize(500, 560)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowSystemMenuHint
        )

        self.license_mgr.license_changed.connect(self.refresh_ui_state)
        self._build_ui()
        self.refresh_ui_state()

    def reject(self) -> None:
        super().reject()
        self.close()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)

    def _is_dark_mode(self) -> bool:
        settings = SettingsManager()
        mode = settings.get('theme_mode', 'system').lower()
        if mode == "dark":
            return True
        elif mode == "light":
            return False
        # system
        app = QApplication.instance()
        if app:
            palette = app.palette()
            return palette.window().color().value() < 128
        return False

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # 頂部標題區
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        icon_label = QLabel("🪁")
        icon_label.setStyleSheet("font-size: 34px;")
        header_layout.addWidget(icon_label)

        header_text = QVBoxLayout()
        header_text.setSpacing(3)
        self.title_label = QLabel(t("license.dialog_header_title"))
        self.title_label.setObjectName("DialogHeaderTitle")
        self.subtitle_label = QLabel(t("license.dialog_header_subtitle"))
        self.subtitle_label.setObjectName("DialogHeaderSubtitle")
        header_text.addWidget(self.title_label)
        header_text.addWidget(self.subtitle_label)
        header_layout.addLayout(header_text)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 狀態卡片 (動態更新)
        self.status_card = QFrame()
        self.status_card.setObjectName("StatusCard")
        self.status_layout = QVBoxLayout(self.status_card)
        self.status_layout.setContentsMargins(18, 16, 18, 16)
        self.status_layout.setSpacing(8)

        self.status_badge = QLabel()
        self.status_badge.setObjectName("StatusBadge")
        self.status_layout.addWidget(self.status_badge)

        self.status_desc = QLabel()
        self.status_desc.setObjectName("StatusDesc")
        self.status_desc.setWordWrap(True)
        self.status_layout.addWidget(self.status_desc)

        layout.addWidget(self.status_card)

        # 輸入序號卡片
        self.input_card = QFrame()
        self.input_card.setObjectName("InputCard")
        input_layout = QVBoxLayout(self.input_card)
        input_layout.setContentsMargins(18, 16, 18, 16)
        input_layout.setSpacing(12)

        self.key_label = QLabel(t("license.key_label"))
        self.key_label.setObjectName("KeyLabel")
        input_layout.addWidget(self.key_label)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText(t("license.key_placeholder"))
        self.key_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_input.setFixedHeight(40)
        self.key_input.returnPressed.connect(self._on_activate_clicked)
        input_layout.addWidget(self.key_input)

        self.btn_activate = QPushButton(t("license.btn_activate"))
        self.btn_activate.setObjectName("BtnActivate")
        self.btn_activate.setFixedHeight(38)
        self.btn_activate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_activate.clicked.connect(self._on_activate_clicked)
        input_layout.addWidget(self.btn_activate)

        layout.addWidget(self.input_card)

        # 底部資訊與機器碼
        bottom_box = QVBoxLayout()
        bottom_box.setSpacing(10)

        # 機器碼列
        mid_row = QHBoxLayout()
        self.mid_label = QLabel(f"{t('license.mid_label')}: <code>{self.license_mgr.machine_id[:16]}...</code>")
        self.mid_label.setObjectName("MidLabel")
        mid_row.addWidget(self.mid_label)
        mid_row.addStretch()

        self.btn_copy_mid = QPushButton(t("license.btn_copy_mid"))
        self.btn_copy_mid.setObjectName("BtnCopyMid")
        self.btn_copy_mid.setFixedHeight(26)
        self.btn_copy_mid.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_mid.clicked.connect(self._copy_machine_id)
        mid_row.addWidget(self.btn_copy_mid)
        bottom_box.addLayout(mid_row)

        # 購買與支援列
        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.btn_buy = QPushButton(t("license.btn_buy"))
        self.btn_buy.setObjectName("BtnBuy")
        self.btn_buy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_buy.setFixedHeight(36)
        self.btn_buy.clicked.connect(self._open_buy_url)
        action_row.addWidget(self.btn_buy, 1)

        self.btn_deactivate = QPushButton(t("license.btn_deactivate"))
        self.btn_deactivate.setObjectName("BtnDeactivate")
        self.btn_deactivate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_deactivate.setFixedHeight(36)
        self.btn_deactivate.setVisible(False)
        self.btn_deactivate.clicked.connect(self._on_deactivate_clicked)
        action_row.addWidget(self.btn_deactivate, 1)

        bottom_box.addLayout(action_row)

        # 客服與技術支援列
        mailto_url = (
            "mailto:support@aisming.com?subject=%5B%E5%95%8F%E9%A1%8C%E5%9B%9E%E5%A0%B1%5D%20KyteRename%20%E4%BD%BF%E7%94%A8%E8%AB%AE%E8%A9%A2%20-%20%E8%A8%82%E5%96%AE/%E5%BA%8F%E8%99%9F%EF%BC%9A(%E8%8B%A5%E6%9C%89%E8%AB%8B%E5%A1%AB%E5%AF%AB)"
            "&body=1.%20%E4%BD%9C%E6%A5%AD%E7%B3%BB%E7%B5%B1%E7%89%88%E6%9C%AC%20(%E4%BE%8B%E5%A6%82%20Win11%2023H2)%EF%BC%9A%0A"
            "2.%20%E7%99%BC%E7%94%9F%E7%9A%84%E5%95%8F%E9%A1%8C%E6%8F%8F%E8%BF%B0%EF%BC%9A%0A"
            "3.%20%E6%9B%B4%E5%90%8D%E8%A6%8F%E5%89%87%E8%88%87%E6%AA%94%E6%A1%88%E6%95%B8%E9%87%8F%EF%BC%9A%0A"
            "4.%20%E6%88%AA%E5%9C%96%E6%88%96%E9%8C%AF%E8%AA%A4%E8%A8%8A%E6%81%AF%EF%BC%9A%0A"
        )
        self.support_lbl = QLabel(
            f"{t('license.support_contact')}: <a href='{mailto_url}' style='color: #6366f1; text-decoration: underline;'>support@aisming.com</a>"
        )
        self.support_lbl.setOpenExternalLinks(True)
        self.support_lbl.setObjectName("SupportLabel")
        self.support_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_box.addWidget(self.support_lbl)

        layout.addLayout(bottom_box)
        self._apply_dialog_styles()

    def _apply_dialog_styles(self) -> None:
        is_dark = self._is_dark_mode()

        bg_color = "#18181b" if is_dark else "#f8fafc"
        text_color = "#f4f4f5" if is_dark else "#0f172a"
        sub_color = "#a1a1aa" if is_dark else "#64748b"
        card_bg = "rgba(255, 255, 255, 0.05)" if is_dark else "#ffffff"
        card_border = "rgba(255, 255, 255, 0.10)" if is_dark else "#e2e8f0"
        input_bg = "rgba(0, 0, 0, 0.25)" if is_dark else "#f1f5f9"
        btn_sec_bg = "rgba(255, 255, 255, 0.08)" if is_dark else "#e2e8f0"
        btn_sec_hover = "rgba(255, 255, 255, 0.14)" if is_dark else "#cbd5e1"
        btn_sec_text = "#e4e4e7" if is_dark else "#1e293b"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }}
            QLabel#DialogHeaderTitle {{
                font-size: 18px;
                font-weight: 800;
                color: {text_color};
            }}
            QLabel#DialogHeaderSubtitle {{
                font-size: 12px;
                color: {sub_color};
            }}
            QFrame#StatusCard {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 12px;
            }}
            QLabel#StatusBadge {{
                font-size: 15px;
                font-weight: 700;
            }}
            QLabel#StatusDesc {{
                font-size: 12px;
                color: {sub_color};
                line-height: 1.5;
            }}
            QFrame#InputCard {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 12px;
            }}
            QLabel#KeyLabel {{
                font-size: 13px;
                font-weight: 600;
                color: {text_color};
            }}
            QLineEdit {{
                background-color: {input_bg};
                border: 1px solid {card_border};
                border-radius: 8px;
                color: {text_color};
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 14px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            QLineEdit:focus {{
                border: 1px solid #6366f1;
            }}
            QPushButton#BtnActivate {{
                background-color: #4f46e5;
                color: #ffffff;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                border: none;
            }}
            QPushButton#BtnActivate:hover {{
                background-color: #6366f1;
            }}
            QPushButton#BtnActivate:pressed {{
                background-color: #4338ca;
            }}
            QLabel#MidLabel {{
                font-size: 11px;
                color: {sub_color};
            }}
            QPushButton#BtnCopyMid {{
                background-color: {btn_sec_bg};
                color: {btn_sec_text};
                border: 1px solid {card_border};
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 10px;
            }}
            QPushButton#BtnCopyMid:hover {{
                background-color: {btn_sec_hover};
            }}
            QPushButton#BtnBuy {{
                background-color: {btn_sec_bg};
                color: {btn_sec_text};
                border: 1px solid {card_border};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton#BtnBuy:hover {{
                background-color: {btn_sec_hover};
            }}
            QPushButton#BtnDeactivate {{
                background-color: rgba(239, 68, 68, 0.15);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton#BtnDeactivate:hover {{
                background-color: rgba(239, 68, 68, 0.25);
            }}
            QLabel#SupportLabel {{
                font-size: 11px;
                color: {sub_color};
                padding-top: 4px;
            }}
        """)

    def refresh_ui_state(self) -> None:
        """根據當前授權或試用天數動態更新卡片內容。"""
        plan = self.license_mgr.get_plan_type()
        days_left = self.license_mgr.get_trial_days_left()
        info = self.license_mgr.get_license_info()

        if plan == "pro":
            self.status_badge.setText(t("license.status_pro_badge"))
            self.status_badge.setStyleSheet("font-size: 15px; font-weight: 700; color: #10b981;")
            masked = info.get("masked_key", "")
            act_date = info.get("activated_at", "")
            self.status_desc.setText(t("license.status_pro_desc", key=masked, date=act_date))
            self.input_card.setVisible(False)
            self.btn_buy.setVisible(False)
            self.btn_deactivate.setVisible(True)

        elif plan == "trial":
            self.status_badge.setText(t("license.status_trial_badge", days=days_left))
            self.status_badge.setStyleSheet("font-size: 15px; font-weight: 700; color: #6366f1;")
            self.status_desc.setText(t("license.status_trial_desc"))
            self.input_card.setVisible(True)
            self.btn_buy.setVisible(True)
            self.btn_deactivate.setVisible(False)

        else:
            self.status_badge.setText(t("license.status_expired_badge"))
            self.status_badge.setStyleSheet("font-size: 15px; font-weight: 700; color: #f59e0b;")
            self.status_desc.setText(t("license.status_expired_desc"))
            self.input_card.setVisible(True)
            self.btn_buy.setVisible(True)
            self.btn_deactivate.setVisible(False)

    def _on_activate_clicked(self) -> None:
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, t("dialog.no_changes_title"), t("license.warn_empty_key"))
            return

        self.btn_activate.setEnabled(False)
        self.btn_activate.setText(t("license.activating"))
        QApplication.processEvents()

        success, msg = self.license_mgr.activate_license(key)
        self.btn_activate.setEnabled(True)
        self.btn_activate.setText(t("license.btn_activate"))

        if success:
            QMessageBox.information(self, t("license.activate_success_title"), msg)
            self.key_input.clear()
            self.refresh_ui_state()
        else:
            QMessageBox.critical(self, t("license.activate_fail_title"), msg)

    def _on_deactivate_clicked(self) -> None:
        reply = QMessageBox.question(
            self,
            t("license.confirm_deactivate_title"),
            t("license.confirm_deactivate_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, res_msg = self.license_mgr.deactivate_license()
            QMessageBox.information(self, t("license.deactivate_result_title"), res_msg)
            self.refresh_ui_state()

    def _copy_machine_id(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.license_mgr.machine_id)
            QMessageBox.information(self, t("license.mid_copied_title"), t("license.mid_copied_msg"))

    def _open_buy_url(self) -> None:
        webbrowser.open(self.PURCHASE_URL)
