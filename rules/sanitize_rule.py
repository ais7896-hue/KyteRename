"""
KyteRename - Sanitize Rule (清除 Windows 非法字元與裝飾性特殊符號)
"""
import re
from .base_rule import BaseRule, TargetScope, FileEntry

# Windows 檔案系統絕對禁止的字元: \ / : * ? " < > | 以及 0x00-0x1F 控制字元
WINDOWS_ILLEGAL_PATTERN = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
# 常見下載/網頁檔名中多餘的裝飾性標籤與符號 (如 ★、■、【】、《》等)
DECORATIVE_SYMBOLS = re.compile(r'[★☆■□▲△▼▽◆◇●○【】〖〗〔〕『』「」《》~`^]+')

class SanitizeRule(BaseRule):
    def __init__(
        self,
        remove_illegal: bool = True,
        remove_symbols: bool = False,
        replace_with: str = "",
        scope: TargetScope = TargetScope.BASE_ONLY,
        is_enabled: bool = True
    ):
        super().__init__(scope, is_enabled)
        self.remove_illegal = remove_illegal
        self.remove_symbols = remove_symbols
        self.replace_with = replace_with

    def apply(self, text: str, entry: FileEntry, index: int = 0) -> str:
        if not self.is_enabled:
            return text

        res = text
        if self.remove_illegal:
            res = WINDOWS_ILLEGAL_PATTERN.sub(self.replace_with, res)

        if self.remove_symbols:
            res = DECORATIVE_SYMBOLS.sub(self.replace_with, res)

        # 整理多餘空白 (連續空格壓縮為單一空格，去除首尾空白)
        res = re.sub(r'\s+', ' ', res).strip()
        return res
