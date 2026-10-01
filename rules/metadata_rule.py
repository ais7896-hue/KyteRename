"""
KyteRename - Metadata Rule (中繼資料變數展開器)
"""
import re
from .base_rule import BaseRule, TargetScope, FileEntry

# 匹配 {var_name} 變數
VAR_PATTERN = re.compile(r"\{([a-zA-Z0-9_]+)\}")

class MetadataRule(BaseRule):
    def __init__(
        self,
        template: str = "{original}",
        scope: TargetScope = TargetScope.BASE_ONLY,
        is_enabled: bool = True
    ):
        super().__init__(scope, is_enabled)
        self.template = template

    def apply(self, text: str, entry: FileEntry, index: int = 0) -> str:
        if not self.is_enabled or not self.template:
            return text

        def _replace_var(match: re.Match) -> str:
            var_name = match.group(1).lower()

            if var_name == "original":
                return text
            if var_name == "n":
                return f"{index + 1}"

            # 若 metadata 尚未載入完成
            if not entry.is_meta_loaded:
                return "[讀取中...]"

            # 從 metadata 讀取
            val = entry.metadata.get(var_name)
            if val is not None:
                return str(val)

            # Fallback 策略：若無 exif_date 則退回到檔案系統 date
            if var_name == "exif_date":
                return entry.metadata.get("date", "")
            if var_name == "exif_datetime":
                return entry.metadata.get("datetime", "")

            return ""

        return VAR_PATTERN.sub(_replace_var, self.template)
