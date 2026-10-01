"""
KyteRename - Trim Rule (多餘空白修剪與清理)
"""
import re
from .base_rule import BaseRule, TargetScope, FileEntry

class TrimRule(BaseRule):
    def __init__(
        self,
        trim_ends: bool = True,
        collapse_spaces: bool = True,
        remove_all_spaces: bool = False,
        scope: TargetScope = TargetScope.BASE_ONLY,
        is_enabled: bool = True
    ):
        super().__init__(scope, is_enabled)
        self.trim_ends = trim_ends
        self.collapse_spaces = collapse_spaces
        self.remove_all_spaces = remove_all_spaces

    def apply(self, text: str, entry: FileEntry, index: int = 0) -> str:
        if not self.is_enabled:
            return text

        if self.remove_all_spaces:
            return "".join(text.split())

        res = text
        if self.collapse_spaces:
            res = re.sub(r"\s+", " ", res)
        if self.trim_ends:
            res = res.strip()

        return res
