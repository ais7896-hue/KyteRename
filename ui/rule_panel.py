"""
KyteRename - Rule Panel (支援正則群組高亮、中文轉拼音與非法字元清洗)
"""
import re
import re
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QMenu,
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QCheckBox, QRadioButton, QButtonGroup, QGroupBox, QSpinBox,
    QComboBox, QPushButton, QScrollArea, QFrame, QSizePolicy, QMessageBox
)
from rules.base_rule import TargetScope, BaseRule
from rules.replace_rule import ReplaceRule
from rules.prefix_suffix_rule import PrefixSuffixRule
from rules.metadata_rule import MetadataRule
from rules.serial_rule import SerialRule, SerialPosition
from rules.case_rule import CaseRule, CaseMode
from rules.trim_rule import TrimRule
from rules.sanitize_rule import SanitizeRule
from rules.pinyin_rule import PinyinRule, PinyinMode
from core.license import LicenseManager
from i18n import t, i18n

class RulePanel(QWidget):
    rules_changed = Signal(list)
    # 傳遞當前搜尋的 pattern 供左欄即時高亮: Optional[re.Pattern]
    pattern_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._init_debounce()
        i18n.language_changed.connect(self._retranslate_ui)

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setObjectName("rule_scroll_area")

        content = QWidget()
        content.setObjectName("rule_panel_content")
        content.setMinimumWidth(290)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 8, 10, 12)
        layout.setSpacing(10)

        # 1. 作用目標 (Target Scope)
        self.scope_box = QGroupBox(t("rules.scope_title"))
        scope_layout = QHBoxLayout(self.scope_box)
        scope_layout.setContentsMargins(8, 12, 8, 8)
        self.btn_scope_base = QRadioButton(t("rules.scope_base"))
        self.btn_scope_ext = QRadioButton(t("rules.scope_ext"))
        self.btn_scope_full = QRadioButton(t("rules.scope_full"))
        self.btn_scope_base.setChecked(True)

        self.scope_group = QButtonGroup(self)
        self.scope_group.addButton(self.btn_scope_base, 0)
        self.scope_group.addButton(self.btn_scope_ext, 1)
        self.scope_group.addButton(self.btn_scope_full, 2)

        scope_layout.addWidget(self.btn_scope_base)
        scope_layout.addWidget(self.btn_scope_ext)
        scope_layout.addWidget(self.btn_scope_full)
        layout.addWidget(self.scope_box)

        # 2. 智慧標籤
        self.meta_box = QGroupBox(t("rules.meta_title"))
        meta_layout = QVBoxLayout(self.meta_box)
        meta_layout.setContentsMargins(8, 12, 8, 8)
        meta_layout.setSpacing(6)

        self.chk_meta = QCheckBox(t("rules.meta_enable"))
        meta_layout.addWidget(self.chk_meta)

        self.PRESET_ITEMS = [
            ("rules.meta_preset_custom", ""),
            ("rules.meta_preset_photo1", "{exif_date}_{original}"),
            ("rules.meta_preset_photo2", "{exif_date}_{resolution}_{n}"),
            ("rules.meta_preset_music1", "{artist} - {original}"),
            ("rules.meta_preset_music2", "{track}_{artist}_{album}"),
            ("rules.meta_preset_backup", "{parent}_{date}_{original}"),
        ]

        row_preset = QHBoxLayout()
        self.lbl_meta_preset = QLabel(t("rules.meta_preset_label"))
        row_preset.addWidget(self.lbl_meta_preset)
        self.combo_presets = QComboBox()
        for key, val in self.PRESET_ITEMS:
            self.combo_presets.addItem(t(key), val)
        self.combo_presets.setEnabled(False)
        row_preset.addWidget(self.combo_presets, stretch=1)
        meta_layout.addLayout(row_preset)

        self.edit_template = QLineEdit()
        self.edit_template.setPlaceholderText(t("rules.meta_template_placeholder"))
        self.edit_template.setText("{original}")
        self.edit_template.setEnabled(False)
        meta_layout.addWidget(self.edit_template)

        self.lbl_meta_click_tip = QLabel(t("rules.meta_click_tip"))
        self.lbl_meta_click_tip.setStyleSheet("color: #8C94A0; font-size: 11px;")
        meta_layout.addWidget(self.lbl_meta_click_tip)

        tag_grid = QGridLayout()
        tag_grid.setSpacing(5)

        self.TAG_BUTTONS_DEF = [
            ("rules.tag_exif_date", "{exif_date}"),
            ("rules.tag_resolution", "{resolution}"),
            ("rules.tag_file_date", "{date}"),
            ("rules.tag_folder", "{parent}"),
            ("rules.tag_artist", "{artist}"),
            ("rules.tag_album", "{album}"),
            ("rules.tag_track", "{track}"),
            ("rules.tag_original", "{original}"),
            ("rules.tag_serial", "{n}")
        ]

        self.tag_buttons = []
        for i, (key, tag_val) in enumerate(self.TAG_BUTTONS_DEF):
            btn = QPushButton(t(key))
            btn.setProperty("class", "tag_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, val=tag_val: self._insert_template_tag(val))
            tag_grid.addWidget(btn, i // 3, i % 3)
            self.tag_buttons.append((btn, key))

        meta_layout.addLayout(tag_grid)
        layout.addWidget(self.meta_box)

        # 3. 流水號 (Serial)
        self.serial_box = QGroupBox(t("rules.serial_title"))
        serial_layout = QVBoxLayout(self.serial_box)
        serial_layout.setContentsMargins(8, 12, 8, 8)
        serial_layout.setSpacing(6)

        self.chk_serial = QCheckBox(t("rules.serial_enable"))
        serial_layout.addWidget(self.chk_serial)

        grid_serial = QGridLayout()
        grid_serial.setHorizontalSpacing(8)
        grid_serial.setVerticalSpacing(6)

        self.lbl_serial_start = QLabel(t("rules.serial_start"))
        grid_serial.addWidget(self.lbl_serial_start, 0, 0)
        self.spin_serial_start = QSpinBox()
        self.spin_serial_start.setRange(0, 999999)
        self.spin_serial_start.setValue(1)
        self.spin_serial_start.setMinimumWidth(65)
        self.spin_serial_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_serial.addWidget(self.spin_serial_start, 0, 1)

        self.lbl_serial_step = QLabel(t("rules.serial_step"))
        grid_serial.addWidget(self.lbl_serial_step, 0, 2)
        self.spin_serial_step = QSpinBox()
        self.spin_serial_step.setRange(1, 100)
        self.spin_serial_step.setValue(1)
        self.spin_serial_step.setMinimumWidth(65)
        self.spin_serial_step.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_serial.addWidget(self.spin_serial_step, 0, 3)

        self.lbl_serial_padding = QLabel(t("rules.serial_padding"))
        grid_serial.addWidget(self.lbl_serial_padding, 1, 0)
        self.spin_serial_padding = QSpinBox()
        self.spin_serial_padding.setRange(1, 10)
        self.spin_serial_padding.setValue(3)
        self.spin_serial_padding.setMinimumWidth(65)
        self.spin_serial_padding.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_serial.addWidget(self.spin_serial_padding, 1, 1)

        self.lbl_serial_sep = QLabel(t("rules.serial_sep"))
        grid_serial.addWidget(self.lbl_serial_sep, 1, 2)
        self.edit_serial_sep = QLineEdit("_")
        self.edit_serial_sep.setMinimumWidth(65)
        self.edit_serial_sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_serial.addWidget(self.edit_serial_sep, 1, 3)

        self.lbl_serial_pos = QLabel(t("rules.serial_pos"))
        grid_serial.addWidget(self.lbl_serial_pos, 2, 0)
        self.SERIAL_POS_ITEMS = [
            ("rules.serial_pos_suffix", SerialPosition.SUFFIX),
            ("rules.serial_pos_prefix", SerialPosition.PREFIX),
            ("rules.serial_pos_replace", SerialPosition.REPLACE),
        ]
        self.combo_serial_pos = QComboBox()
        for key, val in self.SERIAL_POS_ITEMS:
            self.combo_serial_pos.addItem(t(key), val)
        grid_serial.addWidget(self.combo_serial_pos, 2, 1, 1, 3)

        serial_layout.addLayout(grid_serial)
        self.lbl_serial_hint = QLabel(t("rules.serial_hint"))
        self.lbl_serial_hint.setStyleSheet("color: #6C757D; font-size: 11px;")
        serial_layout.addWidget(self.lbl_serial_hint)

        layout.addWidget(self.serial_box)

        # 4. 文字搜尋與取代 (含正則即時驗證與高亮)
        self.replace_box = QGroupBox(t("rules.replace_title"))
        replace_layout = QVBoxLayout(self.replace_box)
        replace_layout.setContentsMargins(8, 12, 8, 8)
        replace_layout.setSpacing(6)

        grid_rep = QGridLayout()
        grid_rep.setHorizontalSpacing(6)
        grid_rep.setVerticalSpacing(6)

        self.lbl_replace_find = QLabel(t("rules.replace_find"))
        grid_rep.addWidget(self.lbl_replace_find, 0, 0)
        self.edit_find = QLineEdit()
        self.edit_find.setPlaceholderText(t("rules.replace_find_placeholder"))
        grid_rep.addWidget(self.edit_find, 0, 1)

        self.lbl_replace_to = QLabel(t("rules.replace_to"))
        grid_rep.addWidget(self.lbl_replace_to, 1, 0)
        self.edit_replace = QLineEdit()
        self.edit_replace.setPlaceholderText(t("rules.replace_to_placeholder"))
        grid_rep.addWidget(self.edit_replace, 1, 1)

        replace_layout.addLayout(grid_rep)

        row_opts = QHBoxLayout()
        self.chk_case = QCheckBox(t("rules.replace_case"))
        self.chk_regex = QCheckBox(t("rules.replace_regex"))
        row_opts.addWidget(self.chk_case)
        row_opts.addWidget(self.chk_regex)

        self.btn_regex_helper = QPushButton(t("rules.replace_regex_helper"))
        self.btn_regex_helper.setProperty("class", "tag_btn")
        self.btn_regex_helper.setCursor(Qt.CursorShape.PointingHandCursor)
        row_opts.addWidget(self.btn_regex_helper)
        replace_layout.addLayout(row_opts)

        self.lbl_regex_error = QLabel("")
        self.lbl_regex_error.setStyleSheet("color: #FF7875; font-size: 11px;")
        self.lbl_regex_error.setVisible(False)
        replace_layout.addWidget(self.lbl_regex_error)

        layout.addWidget(self.replace_box)

        # 5. 前後綴增刪
        self.prefix_box = QGroupBox(t("rules.prefix_title"))
        prefix_layout = QGridLayout(self.prefix_box)
        prefix_layout.setContentsMargins(8, 12, 8, 8)
        prefix_layout.setHorizontalSpacing(6)
        prefix_layout.setVerticalSpacing(6)

        self.lbl_prefix_add = QLabel(t("rules.prefix_add"))
        prefix_layout.addWidget(self.lbl_prefix_add, 0, 0)
        self.edit_prefix = QLineEdit()
        self.edit_prefix.setPlaceholderText(t("rules.prefix_placeholder"))
        prefix_layout.addWidget(self.edit_prefix, 0, 1)

        self.lbl_suffix_add = QLabel(t("rules.suffix_add"))
        prefix_layout.addWidget(self.lbl_suffix_add, 1, 0)
        self.edit_suffix = QLineEdit()
        self.edit_suffix.setPlaceholderText(t("rules.suffix_placeholder"))
        prefix_layout.addWidget(self.edit_suffix, 1, 1)

        layout.addWidget(self.prefix_box)

        # 6. 中文轉拼音 (Pinyin)
        self.pinyin_box = QGroupBox(t("rules.pinyin_title"))
        pinyin_layout = QVBoxLayout(self.pinyin_box)
        pinyin_layout.setContentsMargins(8, 12, 8, 8)
        pinyin_layout.setSpacing(6)

        self.chk_pinyin = QCheckBox(t("rules.pinyin_enable"))
        pinyin_layout.addWidget(self.chk_pinyin)

        row_py = QHBoxLayout()
        self.lbl_pinyin_format = QLabel(t("rules.pinyin_format"))
        row_py.addWidget(self.lbl_pinyin_format)
        self.PINYIN_MODE_ITEMS = [
            ("rules.pinyin_full", PinyinMode.FULL),
            ("rules.pinyin_cap", PinyinMode.CAPITALIZE),
            ("rules.pinyin_initial", PinyinMode.FIRST_LETTER),
        ]
        self.combo_pinyin_mode = QComboBox()
        for key, val in self.PINYIN_MODE_ITEMS:
            self.combo_pinyin_mode.addItem(t(key), val)
        row_py.addWidget(self.combo_pinyin_mode, stretch=1)
        pinyin_layout.addLayout(row_py)

        layout.addWidget(self.pinyin_box)

        # 7. 字元清洗與大小寫修剪
        self.clean_box = QGroupBox(t("rules.clean_title"))
        clean_layout = QVBoxLayout(self.clean_box)
        clean_layout.setContentsMargins(8, 12, 8, 8)
        clean_layout.setSpacing(6)

        self.chk_sanitize_illegal = QCheckBox(t("rules.clean_illegal"))
        self.chk_sanitize_illegal.setChecked(True)
        clean_layout.addWidget(self.chk_sanitize_illegal)

        self.chk_sanitize_symbols = QCheckBox(t("rules.clean_symbols"))
        clean_layout.addWidget(self.chk_sanitize_symbols)

        row_case = QHBoxLayout()
        self.lbl_case = QLabel(t("rules.case_label"))
        row_case.addWidget(self.lbl_case)
        self.CASE_ITEMS = [
            ("rules.case_keep", None),
            ("rules.case_lower", CaseMode.LOWER),
            ("rules.case_upper", CaseMode.UPPER),
            ("rules.case_title", CaseMode.TITLE),
            ("rules.case_capitalize", CaseMode.CAPITALIZE),
        ]
        self.combo_case = QComboBox()
        for key, val in self.CASE_ITEMS:
            self.combo_case.addItem(t(key), val)
        row_case.addWidget(self.combo_case, stretch=1)
        clean_layout.addLayout(row_case)

        row_trim = QHBoxLayout()
        self.chk_trim_ends = QCheckBox(t("rules.clean_trim_ends"))
        self.chk_collapse_spaces = QCheckBox(t("rules.clean_collapse_spaces"))
        row_trim.addWidget(self.chk_trim_ends)
        row_trim.addWidget(self.chk_collapse_spaces)
        clean_layout.addLayout(row_trim)

        layout.addWidget(self.clean_box)

        layout.addStretch()
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        # 事件連接
        self.scope_group.idToggled.connect(self._on_input_changed)
        self.chk_meta.toggled.connect(self._on_meta_toggled)
        self.combo_presets.currentIndexChanged.connect(self._on_preset_changed)
        self.edit_template.textChanged.connect(self._on_input_changed)

        self.chk_serial.toggled.connect(self._on_input_changed)
        self.spin_serial_start.valueChanged.connect(self._on_input_changed)
        self.spin_serial_padding.valueChanged.connect(self._on_input_changed)
        self.spin_serial_step.valueChanged.connect(self._on_input_changed)
        self.combo_serial_pos.currentIndexChanged.connect(self._on_input_changed)
        self.edit_serial_sep.textChanged.connect(self._on_input_changed)

        self.edit_find.textChanged.connect(self._on_find_changed)
        self.edit_replace.textChanged.connect(self._on_input_changed)
        self.chk_case.stateChanged.connect(self._on_find_changed)
        self.chk_regex.stateChanged.connect(self._on_regex_changed)
        self.btn_regex_helper.clicked.connect(self._show_regex_helper_menu)

        self.edit_prefix.textChanged.connect(self._on_input_changed)
        self.edit_suffix.textChanged.connect(self._on_input_changed)

        self.chk_pinyin.toggled.connect(self._on_pinyin_toggled)
        self.combo_pinyin_mode.currentIndexChanged.connect(self._on_input_changed)

        self.chk_sanitize_illegal.toggled.connect(self._on_input_changed)
        self.chk_sanitize_symbols.toggled.connect(self._on_input_changed)

        self.combo_case.currentIndexChanged.connect(self._on_input_changed)
        self.chk_trim_ends.toggled.connect(self._on_input_changed)
        self.chk_collapse_spaces.toggled.connect(self._on_input_changed)

    def _init_debounce(self):
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(100)
        self.debounce_timer.timeout.connect(self._emit_rules)

    def _on_input_changed(self):
        self.debounce_timer.start()

    def _on_find_changed(self):
        find_text = self.edit_find.text()
        is_regex = self.chk_regex.isChecked()
        case_sensitive = self.chk_case.isChecked()

        # 正則語法即時驗證
        pattern = None
        if find_text:
            if is_regex:
                valid, err = ReplaceRule.validate_pattern(find_text, is_regex=True)
                if not valid:
                    self.lbl_regex_error.setText(t("rules.regex_error", err=err))
                    self.lbl_regex_error.setVisible(True)
                    self.edit_find.setStyleSheet("border: 1px solid #FF7875;")
                else:
                    self.lbl_regex_error.setVisible(False)
                    self.edit_find.setStyleSheet("")
                    flags = 0 if case_sensitive else re.IGNORECASE
                    try:
                        pattern = re.compile(find_text, flags)
                    except re.error:
                        pattern = None
            else:
                self.lbl_regex_error.setVisible(False)
                self.edit_find.setStyleSheet("")
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(re.escape(find_text), flags)
        else:
            self.lbl_regex_error.setVisible(False)
            self.edit_find.setStyleSheet("")

        # 廣播 pattern 供左欄即時高亮
        self.pattern_changed.emit(pattern)
        self._on_input_changed()

    def _on_pinyin_toggled(self, checked: bool):
        if checked:
            lic_mgr = LicenseManager.get_instance()
            if not lic_mgr.is_unlimited():
                reply = QMessageBox.information(
                    self,
                    t("rules.pro_pinyin_title"),
                    t("rules.pro_pinyin_msg"),
                    QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Open
                )
                if reply == QMessageBox.StandardButton.Open:
                    from ui.license_dialog import LicenseDialog
                    LicenseDialog(self.window()).exec()
                self.chk_pinyin.blockSignals(True)
                self.chk_pinyin.setChecked(False)
                self.chk_pinyin.blockSignals(False)
                return
        self._on_input_changed()

    def _on_regex_changed(self, state: int):
        checked = (state == 2)
        if checked:
            lic_mgr = LicenseManager.get_instance()
            if not lic_mgr.is_unlimited():
                reply = QMessageBox.information(
                    self,
                    t("rules.pro_regex_title"),
                    t("rules.pro_regex_msg"),
                    QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Open
                )
                if reply == QMessageBox.StandardButton.Open:
                    from ui.license_dialog import LicenseDialog
                    LicenseDialog(self.window()).exec()
                self.chk_regex.blockSignals(True)
                self.chk_regex.setChecked(False)
                self.chk_regex.blockSignals(False)
                return
        self._on_find_changed()

    def _on_meta_toggled(self, checked: bool):
        self.edit_template.setEnabled(checked)
        self.combo_presets.setEnabled(checked)
        self._on_input_changed()

    def _on_preset_changed(self, index: int):
        val = self.combo_presets.currentData()
        if val:
            self.edit_template.setText(val)

    def _insert_template_tag(self, tag: str):
        if not self.chk_meta.isChecked():
            self.chk_meta.setChecked(True)
        self.edit_template.insert(tag)
        self.edit_template.setFocus()

    def get_current_scope(self) -> TargetScope:
        checked_id = self.scope_group.checkedId()
        if checked_id == 1:
            return TargetScope.EXT_ONLY
        elif checked_id == 2:
            return TargetScope.FULL_NAME
        return TargetScope.BASE_ONLY

    def _show_regex_helper_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #21252B;
                border: 1px solid #3A404D;
                border-radius: 6px;
                padding: 4px;
                color: #E2E4E8;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #177DDC;
                color: #FFFFFF;
            }
        """)

        formulas = [
            (t("rules.regex_f_digits"), r"\d+", ""),
            (t("rules.regex_f_round_brackets"), r"\(.*?\)", ""),
            (t("rules.regex_f_square_brackets"), r"\[.*?\]", ""),
            (t("rules.regex_f_letters"), r"[a-zA-Z]+", ""),
            (t("rules.regex_f_spaces"), r"[\s_]+", " "),
            (t("rules.regex_f_date_reverse"), r"(\d+)_(.*)", "$2_$1")
        ]

        for label, pat, rep in formulas:
            action = menu.addAction(label)
            action.triggered.connect(lambda _, p=pat, r=rep: self._apply_regex_formula(p, r))

        menu.exec(self.btn_regex_helper.mapToGlobal(self.btn_regex_helper.rect().bottomLeft()))

    def _apply_regex_formula(self, pattern: str, replace: str):
        self.chk_regex.setChecked(True)
        self.edit_find.setText(pattern)
        if replace:
            self.edit_replace.setText(replace)
        self.edit_find.setFocus()

    def _emit_rules(self):
        scope = self.get_current_scope()
        rules: list[BaseRule] = []

        # 1. 智慧標籤模板
        if self.chk_meta.isChecked() and self.edit_template.text():
            rules.append(MetadataRule(
                template=self.edit_template.text(),
                scope=scope
            ))

        # 2. 中文轉拼音
        if self.chk_pinyin.isChecked():
            rules.append(PinyinRule(
                mode=self.combo_pinyin_mode.currentData(),
                separator="_",
                scope=scope
            ))

        # 3. 搜尋取代 (含正則)
        find_text = self.edit_find.text()
        if find_text:
            rules.append(ReplaceRule(
                find_str=find_text,
                replace_str=self.edit_replace.text(),
                is_regex=self.chk_regex.isChecked(),
                case_sensitive=self.chk_case.isChecked(),
                scope=scope
            ))

        # 4. 前後綴規則
        prefix = self.edit_prefix.text()
        suffix = self.edit_suffix.text()
        if prefix or suffix:
            rules.append(PrefixSuffixRule(
                prefix=prefix,
                suffix=suffix,
                scope=scope
            ))

        # 5. 流水號重新編號
        if self.chk_serial.isChecked():
            rules.append(SerialRule(
                start=self.spin_serial_start.value(),
                step=self.spin_serial_step.value(),
                padding=self.spin_serial_padding.value(),
                position=self.combo_serial_pos.currentData(),
                separator=self.edit_serial_sep.text(),
                scope=scope
            ))

        # 6. 非法字元清洗
        rem_illegal = self.chk_sanitize_illegal.isChecked()
        rem_symbols = self.chk_sanitize_symbols.isChecked()
        if rem_illegal or rem_symbols:
            rules.append(SanitizeRule(
                remove_illegal=rem_illegal,
                remove_symbols=rem_symbols,
                scope=scope
            ))

        # 7. 空白修剪
        trim_ends = self.chk_trim_ends.isChecked()
        collapse = self.chk_collapse_spaces.isChecked()
        if trim_ends or collapse:
            rules.append(TrimRule(
                trim_ends=trim_ends,
                collapse_spaces=collapse,
                scope=scope
            ))

        # 8. 大小寫轉換
        case_mode = self.combo_case.currentData()
        if case_mode is not None:
            rules.append(CaseRule(
                mode=case_mode,
                scope=scope
            ))

        self.rules_changed.emit(rules)

    def _retranslate_ui(self):
        """當全域語言變更時即時刷新規則面板所有群組標題與控制項文字"""
        self.scope_box.setTitle(t("rules.scope_title"))
        self.btn_scope_base.setText(t("rules.scope_base"))
        self.btn_scope_ext.setText(t("rules.scope_ext"))
        self.btn_scope_full.setText(t("rules.scope_full"))

        self.meta_box.setTitle(t("rules.meta_title"))
        self.chk_meta.setText(t("rules.meta_enable"))
        self.edit_template.setPlaceholderText(t("rules.meta_template_placeholder"))

        self.serial_box.setTitle(t("rules.serial_title"))
        self.chk_serial.setText(t("rules.serial_enable"))
        self.lbl_serial_start.setText(t("rules.serial_start"))
        self.lbl_serial_step.setText(t("rules.serial_step"))
        self.lbl_serial_padding.setText(t("rules.serial_padding"))
        self.lbl_serial_sep.setText(t("rules.serial_sep"))
        self.lbl_serial_pos.setText(t("rules.serial_pos"))
        self.lbl_serial_hint.setText(t("rules.serial_hint"))

        self.replace_box.setTitle(t("rules.replace_title"))
        self.lbl_replace_find.setText(t("rules.replace_find"))
        self.edit_find.setPlaceholderText(t("rules.replace_find_placeholder"))
        self.lbl_replace_to.setText(t("rules.replace_to"))
        self.edit_replace.setPlaceholderText(t("rules.replace_to_placeholder"))
        self.chk_case.setText(t("rules.replace_case"))
        self.chk_regex.setText(t("rules.replace_regex"))
        self.btn_regex_helper.setText(t("rules.replace_regex_helper"))

        self.prefix_box.setTitle(t("rules.prefix_title"))
        self.lbl_prefix_add.setText(t("rules.prefix_add"))
        self.edit_prefix.setPlaceholderText(t("rules.prefix_placeholder"))
        self.lbl_suffix_add.setText(t("rules.suffix_add"))
        self.edit_suffix.setPlaceholderText(t("rules.suffix_placeholder"))

        self.pinyin_box.setTitle(t("rules.pinyin_title"))
        self.chk_pinyin.setText(t("rules.pinyin_enable"))
        self.lbl_pinyin_format.setText(t("rules.pinyin_format"))

        self.clean_box.setTitle(t("rules.clean_title"))
        self.chk_sanitize_illegal.setText(t("rules.clean_illegal"))
        self.chk_sanitize_symbols.setText(t("rules.clean_symbols"))
        self.lbl_case.setText(t("rules.case_label"))
        self.chk_trim_ends.setText(t("rules.clean_trim_ends"))
        self.chk_collapse_spaces.setText(t("rules.clean_collapse_spaces"))

        # 刷新中繼標籤面板標籤與下拉選項
        self.lbl_meta_preset.setText(t("rules.meta_preset_label"))
        self.lbl_meta_click_tip.setText(t("rules.meta_click_tip"))
        self.combo_presets.blockSignals(True)
        for idx, (key, _) in enumerate(self.PRESET_ITEMS):
            self.combo_presets.setItemText(idx, t(key))
        self.combo_presets.blockSignals(False)

        for btn, key in self.tag_buttons:
            btn.setText(t(key))

        # 刷新流水號位置選項
        self.combo_serial_pos.blockSignals(True)
        for idx, (key, _) in enumerate(self.SERIAL_POS_ITEMS):
            self.combo_serial_pos.setItemText(idx, t(key))
        self.combo_serial_pos.blockSignals(False)

        # 刷新拼音模式選項
        self.combo_pinyin_mode.blockSignals(True)
        for idx, (key, _) in enumerate(self.PINYIN_MODE_ITEMS):
            self.combo_pinyin_mode.setItemText(idx, t(key))
        self.combo_pinyin_mode.blockSignals(False)

        # 刷新大小寫選項
        self.combo_case.blockSignals(True)
        for idx, (key, _) in enumerate(self.CASE_ITEMS):
            self.combo_case.setItemText(idx, t(key))
        self.combo_case.blockSignals(False)

    def reset_rules(self):
        """將所有命名規則控制項重設回初始預設值"""
        self.debounce_timer.stop()

        # 1. 作用目標 (預設：僅主檔名)
        self.btn_scope_base.setChecked(True)

        # 2. 智慧標籤
        self.chk_meta.setChecked(False)
        self.combo_presets.setCurrentIndex(0)
        self.edit_template.setText("{original}")

        # 3. 流水號 (預設值：起 1, 增 1, 補 3, 分隔符 _, 尾端)
        self.chk_serial.setChecked(False)
        self.spin_serial_start.setValue(1)
        self.spin_serial_step.setValue(1)
        self.spin_serial_padding.setValue(3)
        self.edit_serial_sep.setText("_")
        self.combo_serial_pos.setCurrentIndex(0)

        # 4. 搜尋與取代
        self.edit_find.clear()
        self.edit_replace.clear()
        self.chk_case.setChecked(False)
        self.chk_regex.setChecked(False)
        self.lbl_regex_error.setVisible(False)
        self.edit_find.setStyleSheet("")

        # 5. 前後綴
        self.edit_prefix.clear()
        self.edit_suffix.clear()

        # 6. 中文轉拼音
        self.chk_pinyin.setChecked(False)
        self.combo_pinyin_mode.setCurrentIndex(0)

        # 7. 字元清洗與修剪 (預設清理非法字元勾選，其餘關閉)
        self.chk_sanitize_illegal.setChecked(True)
        self.chk_sanitize_symbols.setChecked(False)
        self.combo_case.setCurrentIndex(0)
        self.chk_trim_ends.setChecked(False)
        self.chk_collapse_spaces.setChecked(False)

        # 廣播 pattern 清空與發送最新規則
        self.pattern_changed.emit(None)
        self._emit_rules()

