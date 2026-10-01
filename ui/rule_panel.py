"""
KyteRename - Rule Panel (支援正則群組高亮、中文轉拼音與非法字元清洗)
"""
import re
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QCheckBox, QRadioButton, QButtonGroup, QGroupBox, QSpinBox,
    QComboBox, QPushButton, QScrollArea, QFrame, QSizePolicy
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

class RulePanel(QWidget):
    rules_changed = Signal(list)
    # 傳遞當前搜尋的 pattern 供左欄即時高亮: Optional[re.Pattern]
    pattern_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._init_debounce()

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
        scope_box = QGroupBox("作用目標")
        scope_layout = QHBoxLayout(scope_box)
        scope_layout.setContentsMargins(8, 12, 8, 8)
        self.btn_scope_base = QRadioButton("僅主檔名")
        self.btn_scope_ext = QRadioButton("僅副檔名")
        self.btn_scope_full = QRadioButton("完整檔名")
        self.btn_scope_base.setChecked(True)

        self.scope_group = QButtonGroup(self)
        self.scope_group.addButton(self.btn_scope_base, 0)
        self.scope_group.addButton(self.btn_scope_ext, 1)
        self.scope_group.addButton(self.btn_scope_full, 2)

        scope_layout.addWidget(self.btn_scope_base)
        scope_layout.addWidget(self.btn_scope_ext)
        scope_layout.addWidget(self.btn_scope_full)
        layout.addWidget(scope_box)

        # 2. 智慧標籤
        meta_box = QGroupBox("相片與音樂資訊（智慧標籤）")
        meta_layout = QVBoxLayout(meta_box)
        meta_layout.setContentsMargins(8, 12, 8, 8)
        meta_layout.setSpacing(6)

        self.chk_meta = QCheckBox("啟用相片/音樂資訊命名")
        meta_layout.addWidget(self.chk_meta)

        row_preset = QHBoxLayout()
        row_preset.addWidget(QLabel("情境範本:"))
        self.combo_presets = QComboBox()
        self.combo_presets.addItem("自訂組合", "")
        self.combo_presets.addItem("📷 相片：拍攝日期_原檔名", "{exif_date}_{original}")
        self.combo_presets.addItem("📷 相片：拍攝日期_解析度_序號", "{exif_date}_{resolution}_{n}")
        self.combo_presets.addItem("🎵 音樂：歌手 - 原檔名", "{artist} - {original}")
        self.combo_presets.addItem("🎵 音樂：音軌_歌手_專輯", "{track}_{artist}_{album}")
        self.combo_presets.addItem("📁 備份：資料夾名_修改日期", "{parent}_{date}_{original}")
        self.combo_presets.setEnabled(False)
        row_preset.addWidget(self.combo_presets, stretch=1)
        meta_layout.addLayout(row_preset)

        self.edit_template = QLineEdit()
        self.edit_template.setPlaceholderText("例如: {exif_date}_{original}")
        self.edit_template.setText("{original}")
        self.edit_template.setEnabled(False)
        meta_layout.addWidget(self.edit_template)

        lbl_insert = QLabel("點擊標籤快速插入：")
        lbl_insert.setStyleSheet("color: #8C94A0; font-size: 11px;")
        meta_layout.addWidget(lbl_insert)

        tag_grid = QGridLayout()
        tag_grid.setSpacing(5)

        tags = [
            ("📷 拍攝日期", "{exif_date}"),
            ("📐 解析度", "{resolution}"),
            ("📅 檔案日期", "{date}"),
            ("📁 資料夾名", "{parent}"),
            ("🎤 歌手", "{artist}"),
            ("💿 專輯", "{album}"),
            ("🎵 音軌號", "{track}"),
            ("📄 原檔名", "{original}"),
            ("🔢 流水號", "{n}")
        ]

        for i, (text, tag_val) in enumerate(tags):
            btn = QPushButton(text)
            btn.setProperty("class", "tag_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, t=tag_val: self._insert_template_tag(t))
            tag_grid.addWidget(btn, i // 3, i % 3)

        meta_layout.addLayout(tag_grid)
        layout.addWidget(meta_box)

        # 3. 流水號 (Serial)
        serial_box = QGroupBox("重新編號（流水號）")
        serial_layout = QVBoxLayout(serial_box)
        serial_layout.setContentsMargins(8, 12, 8, 8)
        serial_layout.setSpacing(6)

        self.chk_serial = QCheckBox("啟用流水號編號")
        serial_layout.addWidget(self.chk_serial)

        grid_serial = QGridLayout()
        grid_serial.setHorizontalSpacing(8)
        grid_serial.setVerticalSpacing(6)

        grid_serial.addWidget(QLabel("起始值:"), 0, 0)
        self.spin_serial_start = QSpinBox()
        self.spin_serial_start.setRange(0, 999999)
        self.spin_serial_start.setValue(1)
        self.spin_serial_start.setMinimumWidth(65)
        self.spin_serial_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_serial.addWidget(self.spin_serial_start, 0, 1)

        grid_serial.addWidget(QLabel("每次遞增:"), 0, 2)
        self.spin_serial_step = QSpinBox()
        self.spin_serial_step.setRange(1, 100)
        self.spin_serial_step.setValue(1)
        self.spin_serial_step.setMinimumWidth(65)
        self.spin_serial_step.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_serial.addWidget(self.spin_serial_step, 0, 3)

        grid_serial.addWidget(QLabel("補零位數:"), 1, 0)
        self.spin_serial_padding = QSpinBox()
        self.spin_serial_padding.setRange(1, 10)
        self.spin_serial_padding.setValue(3)
        self.spin_serial_padding.setMinimumWidth(65)
        self.spin_serial_padding.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_serial.addWidget(self.spin_serial_padding, 1, 1)

        grid_serial.addWidget(QLabel("分隔符:"), 1, 2)
        self.edit_serial_sep = QLineEdit("_")
        self.edit_serial_sep.setMinimumWidth(65)
        self.edit_serial_sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_serial.addWidget(self.edit_serial_sep, 1, 3)

        grid_serial.addWidget(QLabel("位置:"), 2, 0)
        self.combo_serial_pos = QComboBox()
        self.combo_serial_pos.addItem("加在尾端 (如: photo_001)", SerialPosition.SUFFIX)
        self.combo_serial_pos.addItem("加在開端 (如: 001_photo)", SerialPosition.PREFIX)
        self.combo_serial_pos.addItem("整名替換 (如: 001)", SerialPosition.REPLACE)
        grid_serial.addWidget(self.combo_serial_pos, 2, 1, 1, 3)

        serial_layout.addLayout(grid_serial)
        lbl_serial_hint = QLabel("💡 預覽效果: photo_001.jpg, photo_002.jpg ...")
        lbl_serial_hint.setStyleSheet("color: #6C757D; font-size: 11px;")
        serial_layout.addWidget(lbl_serial_hint)

        layout.addWidget(serial_box)

        # 4. 文字搜尋與取代 (含正則即時驗證與高亮)
        replace_box = QGroupBox("文字搜尋與取代 (支援正則)")
        replace_layout = QVBoxLayout(replace_box)
        replace_layout.setContentsMargins(8, 12, 8, 8)
        replace_layout.setSpacing(6)

        grid_rep = QGridLayout()
        grid_rep.setHorizontalSpacing(6)
        grid_rep.setVerticalSpacing(6)

        grid_rep.addWidget(QLabel("搜尋："), 0, 0)
        self.edit_find = QLineEdit()
        self.edit_find.setPlaceholderText("要取代的文字或正則 (如: \\d+)")
        grid_rep.addWidget(self.edit_find, 0, 1)

        grid_rep.addWidget(QLabel("替換為："), 1, 0)
        self.edit_replace = QLineEdit()
        self.edit_replace.setPlaceholderText("留空則為刪除，支援 $1 反向引用")
        grid_rep.addWidget(self.edit_replace, 1, 1)

        replace_layout.addLayout(grid_rep)

        row_opts = QHBoxLayout()
        self.chk_case = QCheckBox("區分大小寫")
        self.chk_regex = QCheckBox("正則表達式 (Regex)")
        row_opts.addWidget(self.chk_case)
        row_opts.addWidget(self.chk_regex)
        replace_layout.addLayout(row_opts)

        self.lbl_regex_error = QLabel("")
        self.lbl_regex_error.setStyleSheet("color: #FF7875; font-size: 11px;")
        self.lbl_regex_error.setVisible(False)
        replace_layout.addWidget(self.lbl_regex_error)

        layout.addWidget(replace_box)

        # 5. 前後綴增刪
        prefix_box = QGroupBox("前後綴增刪")
        prefix_layout = QGridLayout(prefix_box)
        prefix_layout.setContentsMargins(8, 12, 8, 8)
        prefix_layout.setHorizontalSpacing(6)
        prefix_layout.setVerticalSpacing(6)

        prefix_layout.addWidget(QLabel("加前綴："), 0, 0)
        self.edit_prefix = QLineEdit()
        self.edit_prefix.setPlaceholderText("例如: [Final]_")
        prefix_layout.addWidget(self.edit_prefix, 0, 1)

        prefix_layout.addWidget(QLabel("加後綴："), 1, 0)
        self.edit_suffix = QLineEdit()
        self.edit_suffix.setPlaceholderText("例如: _v2")
        prefix_layout.addWidget(self.edit_suffix, 1, 1)

        layout.addWidget(prefix_box)

        # 6. 中文轉拼音 (Pinyin)
        pinyin_box = QGroupBox("中文轉拼音")
        pinyin_layout = QVBoxLayout(pinyin_box)
        pinyin_layout.setContentsMargins(8, 12, 8, 8)
        pinyin_layout.setSpacing(6)

        self.chk_pinyin = QCheckBox("啟用中文轉拼音")
        pinyin_layout.addWidget(self.chk_pinyin)

        row_py = QHBoxLayout()
        row_py.addWidget(QLabel("拼音格式:"))
        self.combo_pinyin_mode = QComboBox()
        self.combo_pinyin_mode.addItem("全拼小寫 (如: qing_tian)", PinyinMode.FULL)
        self.combo_pinyin_mode.addItem("首字大寫 (如: Qing_Tian)", PinyinMode.CAPITALIZE)
        self.combo_pinyin_mode.addItem("首字母簡拼 (如: qt)", PinyinMode.FIRST_LETTER)
        row_py.addWidget(self.combo_pinyin_mode, stretch=1)
        pinyin_layout.addLayout(row_py)

        layout.addWidget(pinyin_box)

        # 7. 字元清洗與大小寫修剪
        clean_box = QGroupBox("安全清洗與樣式修剪")
        clean_layout = QVBoxLayout(clean_box)
        clean_layout.setContentsMargins(8, 12, 8, 8)
        clean_layout.setSpacing(6)

        self.chk_sanitize_illegal = QCheckBox(r'自動清理 Windows 非法字元 (\/:*?"<>|)')
        self.chk_sanitize_illegal.setChecked(True)
        clean_layout.addWidget(self.chk_sanitize_illegal)

        self.chk_sanitize_symbols = QCheckBox("去除裝飾性符號 (如: 【】★☆◆等)")
        clean_layout.addWidget(self.chk_sanitize_symbols)

        row_case = QHBoxLayout()
        row_case.addWidget(QLabel("大小寫:"))
        self.combo_case = QComboBox()
        self.combo_case.addItem("維持原樣", None)
        self.combo_case.addItem("全部小寫 (lower)", CaseMode.LOWER)
        self.combo_case.addItem("全部大寫 (UPPER)", CaseMode.UPPER)
        self.combo_case.addItem("詞首大寫 (Title Case)", CaseMode.TITLE)
        self.combo_case.addItem("句首大寫 (Capitalize)", CaseMode.CAPITALIZE)
        row_case.addWidget(self.combo_case, stretch=1)
        clean_layout.addLayout(row_case)

        row_trim = QHBoxLayout()
        self.chk_trim_ends = QCheckBox("去除頭尾空白")
        self.chk_collapse_spaces = QCheckBox("壓縮連續空格")
        row_trim.addWidget(self.chk_trim_ends)
        row_trim.addWidget(self.chk_collapse_spaces)
        clean_layout.addLayout(row_trim)

        layout.addWidget(clean_box)

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
        self.chk_regex.stateChanged.connect(self._on_find_changed)

        self.edit_prefix.textChanged.connect(self._on_input_changed)
        self.edit_suffix.textChanged.connect(self._on_input_changed)

        self.chk_pinyin.toggled.connect(self._on_input_changed)
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
                    self.lbl_regex_error.setText(f"⚠️ 正則表達式語法無效: {err}")
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
