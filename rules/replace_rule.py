"""
KyteRename - Replace Rule (字串搜尋與取代，支援 Regex 群組引用 $1/\1 與語法驗證)
"""
import re
from typing import Optional, Tuple
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

    @staticmethod
    def validate_pattern(pattern_str: str, is_regex: bool) -> Tuple[bool, Optional[str]]:
        """驗證正則表示式是否合法，回傳 (is_valid, error_message)"""
        if not is_regex or not pattern_str:
            return True, None
        try:
            re.compile(pattern_str)
            return True, None
        except re.error as e:
            return False, str(e)

    def apply(self, text: str, entry: FileEntry, index: int = 0) -> str:
        if not self.is_enabled or not self.find_str:
            return text

        if self.is_regex:
            try:
                flags = 0 if self.case_sensitive else re.IGNORECASE
                # 友善支援: 將使用者直覺輸入的 $1, $2 自動轉換為 Python re 的 \1, \2
                rep_str = re.sub(r'\$([0-9])', r'\\\1', self.replace_str)
                return re.sub(self.find_str, rep_str, text, flags=flags)
            except re.error:
                return text
        else:
            if self.case_sensitive:
                return text.replace(self.find_str, self.replace_str)
            else:
                pattern = re.escape(self.find_str)
                return re.sub(pattern, lambda m: self.replace_str, text, flags=re.IGNORECASE)
