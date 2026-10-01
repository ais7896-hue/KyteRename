"""
KyteRename - Serial Rule (流水號重新編號)
"""
from enum import Enum
from .base_rule import BaseRule, TargetScope, FileEntry

class SerialPosition(Enum):
    SUFFIX = "suffix"    # 加在尾端: name_001
    PREFIX = "prefix"    # 加在開端: 001_name
    REPLACE = "replace"  # 替換整個名稱: 001

class SerialRule(BaseRule):
    def __init__(
        self,
        start: int = 1,
        step: int = 1,
        padding: int = 3,
        position: SerialPosition = SerialPosition.SUFFIX,
        separator: str = "_",
        scope: TargetScope = TargetScope.BASE_ONLY,
        is_enabled: bool = True
    ):
        super().__init__(scope, is_enabled)
        self.start = start
        self.step = step
        self.padding = padding
        self.position = position
        self.separator = separator

    def apply(self, text: str, entry: FileEntry, index: int = 0) -> str:
        if not self.is_enabled:
            return text

        current_num = self.start + (index * self.step)
        num_str = f"{current_num:0{self.padding}d}"

        if self.position == SerialPosition.SUFFIX:
            sep = self.separator if text else ""
            return f"{text}{sep}{num_str}"
        elif self.position == SerialPosition.PREFIX:
            sep = self.separator if text else ""
            return f"{num_str}{sep}{text}"
        elif self.position == SerialPosition.REPLACE:
            return num_str

        return text
