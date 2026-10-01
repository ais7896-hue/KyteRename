"""
KyteRename - Pinyin Rule (中文轉拼音，支援全拼與首字母簡拼)
"""
import re
from enum import Enum
import pypinyin
from .base_rule import BaseRule, TargetScope, FileEntry

class PinyinMode(Enum):
    FULL = "full"            # 全拼: ni_hao
    FIRST_LETTER = "first"   # 首字母簡拼: nh
    CAPITALIZE = "cap"       # 首字大寫全拼: Ni_Hao

class PinyinRule(BaseRule):
    def __init__(
        self,
        mode: PinyinMode = PinyinMode.FULL,
        separator: str = "_",
        scope: TargetScope = TargetScope.BASE_ONLY,
        is_enabled: bool = True
    ):
        super().__init__(scope, is_enabled)
        self.mode = mode
        self.separator = separator

    def apply(self, text: str, entry: FileEntry, index: int = 0) -> str:
        if not self.is_enabled or not text:
            return text

        # 檢查是否含有中文字元
        if not re.search(r'[\u4e00-\u9fa5]', text):
            return text

        if self.mode == PinyinMode.FIRST_LETTER:
            # 取首字母
            res_list = pypinyin.lazy_pinyin(text, style=pypinyin.Style.FIRST_LETTER)
            return "".join(res_list)
        elif self.mode == PinyinMode.CAPITALIZE:
            # 每個詞首字母大寫
            res_list = pypinyin.lazy_pinyin(text, style=pypinyin.Style.NORMAL)
            return self.separator.join([w.capitalize() for w in res_list])
        else:
            # 標準全拼小寫
            res_list = pypinyin.lazy_pinyin(text, style=pypinyin.Style.NORMAL)
            return self.separator.join(res_list)
