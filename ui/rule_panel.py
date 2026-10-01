"""
KyteRename - Rule Panel (全功能規則面板，支援變數模板、流水號、大小寫與空白修剪)
"""
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QRadioButton, QButtonGroup, QGroupBox, QSpinBox,
    QComboBox, QPushButton, QScrollArea, QFrame
)
from rules.base_rule import TargetScope, BaseRule
from rules.replace_rule import ReplaceRule
from rules.prefix_suffix_rule import PrefixSuffixRule
from rules.metadata_rule import MetadataRule
from rules.serial_rule import SerialRule, SerialPosition
from rules.case_rule import CaseRule, CaseMode
from rules.trim_rule import TrimRule

class RulePanel(QWidget):
    rules_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._init_debounce()

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # 使用滾動區域包覆規則面板，防止選項變多時視窗放不下
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # 1. 作用目標 (Target Scope)
        scope_box = QGroupBox("作用目標")
        scope_layout = QHBoxLayout(scope_box)
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

        # 2. 中繼資料與變數模板 (Metadata)
        meta_box = QGroupBox("中繼資料變數模板")
        meta_layout = QVBoxLayout(meta_box)

        row_meta_enable = QHBoxLayout()
        self.chk_meta = QCheckBox("啟用變數命名模板")
        row_meta_enable.addWidget(self.chk_meta)
        meta_layout.addLayout(row_meta_enable)

        self.edit_template = QLineEdit()
        self.edit_template.setPlaceholderText("例如: {exif_date}_{resolution}_{original}")
        self.edit_template.setText("{original}")
        self.edit_template.setEnabled(False)
        meta_layout.addWidget(self.edit_template)

        # 快捷變數標籤按鈕
        tag_layout_1 = QHBoxLayout()
        self.btn_tag_date = QPushButton("+ {date}")
        self.btn_tag_exif = QPushButton("+ {exif_date}")
        self.btn_tag_res = QPushButton("+ {resolution}")
        self.btn_tag_parent = QPushButton("+ {parent}")
        tag_layout_1.addWidget(self.btn_tag_date)
        tag_layout_1.addWidget(self.btn_tag_exif)
        tag_layout_1.addWidget(self.btn_tag_res)
        tag_layout_1.addWidget(self.btn_tag_parent)
        meta_layout.addLayout(tag_layout_1)

        tag_layout_2 = QHBoxLayout()
        self.btn_tag_artist = QPushButton("+ {artist}")
        self.btn_tag_album = QPushButton("+ {album}")
        self.btn_tag_track = QPushButton("+ {track}")
        self.btn_tag_n = QPushButton("+ {n}")
        tag_layout_2.addWidget(self.btn_tag_artist)
        tag_layout_2.addWidget(self.btn_tag_album)
        tag_layout_2.addWidget(self.btn_tag_track)
        tag_layout_2.addWidget(self.btn_tag_n)
        meta_layout.addLayout(tag_layout_2)

        layout.addWidget(meta_box)

        # 3. 流水號 (Serial)
        serial_box = QGroupBox("重新編號（流水號）")
        serial_layout = QVBoxLayout(serial_box)

        self.chk_serial = QCheckBox("啟用流水號編號")
        serial_layout.addWidget(self.chk_serial)

        row_serial_params = QHBoxLayout()
        row_serial_params.addWidget(QLabel("起始值:"))
        self.spin_serial_start = QSpinBox()
        self.spin_serial_start.setRange(0, 999999)
        self.spin_serial_start.setValue(1)
        row_serial_params.addWidget(self.spin_serial_start)

        row_serial_params.addWidget(QLabel("位數(補零):"))
        self.spin_serial_padding = QSpinBox()
        self.spin_serial_padding.setRange(1, 10)
        self.spin_serial_padding.setValue(3)
        row_serial_params.addWidget(self.spin_serial_padding)

        row_serial_params.addWidget(QLabel("間隔步長:"))
        self.spin_serial_step = QSpinBox()
        self.spin_serial_step.setRange(1, 100)
        self.spin_serial_step.setValue(1)
        row_serial_params.addWidget(self.spin_serial_step)
        serial_layout.addLayout(row_serial_params)

        row_serial_pos = QHBoxLayout()
        row_serial_pos.addWidget(QLabel("放置位置:"))
        self.combo_serial_pos = QComboBox()
        self.combo_serial_pos.addItem("加在尾端 (Suffix)", SerialPosition.SUFFIX)
        self.combo_serial_pos.addItem("加在開端 (Prefix)", SerialPosition.PREFIX)
        self.combo_serial_pos.addItem("整名替換 (Replace)", SerialPosition.REPLACE)
        row_serial_pos.addWidget(self.combo_serial_pos)

        row_serial_pos.addWidget(QLabel("分隔符:"))
        self.edit_serial_sep = QLineEdit("_")
        self.edit_serial_sep.setMaximumWidth(45)
        row_serial_pos.addWidget(self.edit_serial_sep)
        serial_layout.addLayout(row_serial_pos)

        layout.addWidget(serial_box)

        # 4. 文字搜尋與取代
        replace_box = QGroupBox("搜尋與取代")
        replace_layout = QVBoxLayout(replace_box)

        row_find = QHBoxLayout()
        row_find.addWidget(QLabel("搜尋："))
        self.edit_find = QLineEdit()
        self.edit_find.setPlaceholderText("要取代的文字")
        row_find.addWidget(self.edit_find)
        replace_layout.addLayout(row_find)

        row_replace = QHBoxLayout()
        row_replace.addWidget(QLabel("替換為："))
        self.edit_replace = QLineEdit()
        self.edit_replace.setPlaceholderText("留空則為刪除")
        row_replace.addWidget(self.edit_replace)
        replace_layout.addLayout(row_replace)

        row_opts = QHBoxLayout()
        self.chk_case = QCheckBox("區分大小寫")
        self.chk_regex = QCheckBox("正則 (Regex)")
        row_opts.addWidget(self.chk_case)
        row_opts.addWidget(self.chk_regex)
        replace_layout.addLayout(row_opts)

        layout.addWidget(replace_box)

        # 5. 前後綴增刪
        prefix_box = QGroupBox("前後綴增刪")
        prefix_layout = QVBoxLayout(prefix_box)
        row_prefix = QHBoxLayout()
        row_prefix.addWidget(QLabel("加前綴："))
        self.edit_prefix = QLineEdit()
        self.edit_prefix.setPlaceholderText("例如: [Final]_")
        row_prefix.addWidget(self.edit_prefix)
        prefix_layout.addLayout(row_prefix)

        row_suffix = QHBoxLayout()
        row_suffix.addWidget(QLabel("加後綴："))
        self.edit_suffix = QLineEdit()
        self.edit_suffix.setPlaceholderText("例如: _v2")
        row_suffix.addWidget(self.edit_suffix)
        prefix_layout.addLayout(row_suffix)
        layout.addWidget(prefix_box)

        # 6. 大小寫轉換與空白修剪
        format_box = QGroupBox("字體樣式與空白修剪")
        format_layout = QVBoxLayout(format_box)

        row_case = QHBoxLayout()
        row_case.addWidget(QLabel("大小寫轉換："))
        self.combo_case = QComboBox()
        self.combo_case.addItem("維持原樣", None)
        self.combo_case.addItem("全部小寫 (lower)", CaseMode.LOWER)
        self.combo_case.addItem("全部大寫 (UPPER)", CaseMode.UPPER)
        self.combo_case.addItem("詞首大寫 (Title Case)", CaseMode.TITLE)
        self.combo_case.addItem("句首大寫 (Capitalize)", CaseMode.CAPITALIZE)
        row_case.addWidget(self.combo_case)
        format_layout.addLayout(row_case)

        row_trim = QHBoxLayout()
        self.chk_trim_ends = QCheckBox("去除頭尾空白")
        self.chk_collapse_spaces = QCheckBox("連續空格壓縮為單一空格")
        row_trim.addWidget(self.chk_trim_ends)
        row_trim.addWidget(self.chk_collapse_spaces)
        format_layout.addLayout(row_trim)

        layout.addWidget(format_box)

        layout.addStretch()
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        # 事件連接
        self.scope_group.idToggled.connect(self._on_input_changed)
        self.chk_meta.toggled.connect(self._on_meta_toggled)
        self.edit_template.textChanged.connect(self._on_input_changed)

        for btn, tag in [
            (self.btn_tag_date, "{date}"),
            (self.btn_tag_exif, "{exif_date}"),
            (self.btn_tag_res, "{resolution}"),
            (self.btn_tag_parent, "{parent}"),
            (self.btn_tag_artist, "{artist}"),
            (self.btn_tag_album, "{album}"),
            (self.btn_tag_track, "{track}"),
            (self.btn_tag_n, "{n}")
        ]:
            btn.clicked.connect(lambda _, t=tag: self._insert_template_tag(t))

        self.chk_serial.toggled.connect(self._on_input_changed)
        self.spin_serial_start.valueChanged.connect(self._on_input_changed)
        self.spin_serial_padding.valueChanged.connect(self._on_input_changed)
        self.spin_serial_step.valueChanged.connect(self._on_input_changed)
        self.combo_serial_pos.currentIndexChanged.connect(self._on_input_changed)
        self.edit_serial_sep.textChanged.connect(self._on_input_changed)

        self.edit_find.textChanged.connect(self._on_input_changed)
        self.edit_replace.textChanged.connect(self._on_input_changed)
        self.chk_case.stateChanged.connect(self._on_input_changed)
        self.chk_regex.stateChanged.connect(self._on_input_changed)

        self.edit_prefix.textChanged.connect(self._on_input_changed)
        self.edit_suffix.textChanged.connect(self._on_input_changed)

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

    def _on_meta_toggled(self, checked: bool):
        self.edit_template.setEnabled(checked)
        self._on_input_changed()

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

        # 1. 中繼資料模板規則
        if self.chk_meta.isChecked() and self.edit_template.text():
            rules.append(MetadataRule(
                template=self.edit_template.text(),
                scope=scope
            ))

        # 2. 搜尋取代規則
        find_text = self.edit_find.text()
        if find_text:
            rules.append(ReplaceRule(
                find_str=find_text,
                replace_str=self.edit_replace.text(),
                is_regex=self.chk_regex.isChecked(),
                case_sensitive=self.chk_case.isChecked(),
                scope=scope
            ))

        # 3. 前後綴規則
        prefix = self.edit_prefix.text()
        suffix = self.edit_suffix.text()
        if prefix or suffix:
            rules.append(PrefixSuffixRule(
                prefix=prefix,
                suffix=suffix,
                scope=scope
            ))

        # 4. 流水號重新編號
        if self.chk_serial.isChecked():
            rules.append(SerialRule(
                start=self.spin_serial_start.value(),
                step=self.spin_serial_step.value(),
                padding=self.spin_serial_padding.value(),
                position=self.combo_serial_pos.currentData(),
                separator=self.edit_serial_sep.text(),
                scope=scope
            ))

        # 5. 空白修剪規則
        trim_ends = self.chk_trim_ends.isChecked()
        collapse = self.chk_collapse_spaces.isChecked()
        if trim_ends or collapse:
            rules.append(TrimRule(
                trim_ends=trim_ends,
                collapse_spaces=collapse,
                scope=scope
            ))

        # 6. 大小寫轉換規則
        case_mode = self.combo_case.currentData()
        if case_mode is not None:
            rules.append(CaseRule(
                mode=case_mode,
                scope=scope
            ))

        self.rules_changed.emit(rules)
