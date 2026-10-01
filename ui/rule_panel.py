"""
KyteRename - Rule Panel (規則配置面板，100ms Debounce 即時回饋)
"""
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QRadioButton, QButtonGroup, QGroupBox, QFrame
)
from rules.base_rule import TargetScope, BaseRule
from rules.replace_rule import ReplaceRule
from rules.prefix_suffix_rule import PrefixSuffixRule

class RulePanel(QWidget):
    # 當規則變更且 debounce 時間結束後發送訊號
    rules_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._init_debounce()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # 1. 作用範圍 (Target Scope)
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

        # 2. 前綴與後綴
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

        # 3. 搜尋與取代
        replace_box = QGroupBox("文字搜尋與取代")
        replace_layout = QVBoxLayout(replace_box)

        row_find = QHBoxLayout()
        row_find.addWidget(QLabel("搜尋："))
        self.edit_find = QLineEdit()
        self.edit_find.setPlaceholderText("要取代的字串")
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
        self.chk_regex = QCheckBox("正規表達式 (Regex)")
        row_opts.addWidget(self.chk_case)
        row_opts.addWidget(self.chk_regex)
        replace_layout.addLayout(row_opts)

        layout.addWidget(replace_box)

        layout.addStretch()

        # 連接事件
        self.scope_group.idToggled.connect(self._on_input_changed)
        self.edit_prefix.textChanged.connect(self._on_input_changed)
        self.edit_suffix.textChanged.connect(self._on_input_changed)
        self.edit_find.textChanged.connect(self._on_input_changed)
        self.edit_replace.textChanged.connect(self._on_input_changed)
        self.chk_case.stateChanged.connect(self._on_input_changed)
        self.chk_regex.stateChanged.connect(self._on_input_changed)

    def _init_debounce(self):
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(100) # 100ms 體感即時且不連發
        self.debounce_timer.timeout.connect(self._emit_rules)

    def _on_input_changed(self):
        self.debounce_timer.start()

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

        # 1. 搜尋取代規則
        find_text = self.edit_find.text()
        if find_text:
            rules.append(ReplaceRule(
                find_str=find_text,
                replace_str=self.edit_replace.text(),
                is_regex=self.chk_regex.isChecked(),
                case_sensitive=self.chk_case.isChecked(),
                scope=scope
            ))

        # 2. 前後綴規則
        prefix = self.edit_prefix.text()
        suffix = self.edit_suffix.text()
        if prefix or suffix:
            rules.append(PrefixSuffixRule(
                prefix=prefix,
                suffix=suffix,
                scope=scope
            ))

        self.rules_changed.emit(rules)
