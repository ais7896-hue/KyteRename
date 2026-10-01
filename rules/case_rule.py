"""
KyteRename - Case Rule (大小寫轉換)
"""
from enum import Enum
from .base_rule import BaseRule, TargetScope, FileEntry

class CaseMode(Enum):
    LOWER = "lower"          # 全部小寫: file_name.jpg
    UPPER = "upper"          # 全部大寫: FILE_NAME.JPG
    TITLE = "title"          # 詞首大寫: File_Name.Jpg
    CAPITALIZE = "capitalize" # 僅首字大寫: File_name.jpg

class CaseRule(BaseRule):
    def __init__(
        self,
        mode: CaseMode = CaseMode.LOWER,
        scope: TargetScope = TargetScope.BASE_ONLY,
        is_enabled: bool = True
    ):
        super().__init__(scope, is_enabled)
        self.mode = mode

    def apply(self, text: str, entry: FileEntry, index: int = 0) -> str:
        if not self.is_enabled:
            return text

        if self.mode == CaseMode.LOWER:
            return text.lower()
        elif self.mode == CaseMode.UPPER:
            return text.upper()
        elif self.mode == CaseMode.TITLE:
            return text.title()
        elif self.mode == CaseMode.CAPITALIZE:
            return text.capitalize()

        return text
