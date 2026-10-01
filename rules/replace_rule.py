"""
KyteRename - Replace Rule (字串搜尋與取代，支援 Regex 與大小寫切換)
"""
import re
from .base_rule import BaseRule, TargetScope, FileEntry

class ReplaceRule(BaseRule):
    def __init__(
        self,
        find_str: str = "",
        replace_str: str = "",
        is_regex: bool = False,
        case_sensitive: bool = True,
        scope: TargetScope = TargetScope.BASE_ONLY,
        is_enabled: bool = True
    ):
        super().__init__(scope, is_enabled)
        self.find_str = find_str
        self.replace_str = replace_str
        self.is_regex = is_regex
        self.case_sensitive = case_sensitive

    def apply(self, text: str, entry: FileEntry) -> str:
        if not self.is_enabled or not self.find_str:
            return text

        if self.is_regex:
            try:
                flags = 0 if self.case_sensitive else re.IGNORECASE
                return re.sub(self.find_str, self.replace_str, text, flags=flags)
            except re.error:
                # 正則語法不合法時靜默略過，防止 UI 計算崩潰
                return text
        else:
            if self.case_sensitive:
                return text.replace(self.find_str, self.replace_str)
            else:
                pattern = re.escape(self.find_str)
                return re.sub(pattern, lambda m: self.replace_str, text, flags=re.IGNORECASE)
