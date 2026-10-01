"""
KyteRename - Prefix Suffix Rule (前後綴增刪)
"""
from .base_rule import BaseRule, TargetScope, FileEntry

class PrefixSuffixRule(BaseRule):
    def __init__(
        self,
        prefix: str = "",
        suffix: str = "",
        scope: TargetScope = TargetScope.BASE_ONLY,
        is_enabled: bool = True
    ):
        super().__init__(scope, is_enabled)
        self.prefix = prefix
        self.suffix = suffix

    def apply(self, text: str, entry: FileEntry, index: int = 0) -> str:
        if not self.is_enabled:
            return text
        return f"{self.prefix}{text}{self.suffix}"
