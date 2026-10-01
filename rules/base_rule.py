"""
KyteRename - Base Rule & Data Model
"""
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict

class TargetScope(Enum):
    BASE_ONLY = "base_only"      # 僅主檔名 (預設)
    EXT_ONLY = "ext_only"        # 僅副檔名 (例如 .JPG -> .jpg)
    FULL_NAME = "full_name"      # 完整檔名 (含副檔名)

@dataclass
class FileEntry:
    path: Path
    original_base: str            # 不含副檔名，如 'DSC_0001'
    extension: str                # 含點號副檔名，如 '.jpg'
    size_bytes: int = 0
    mtime: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_meta_loaded: bool = False

    @property
    def original_name(self) -> str:
        return f"{self.original_base}{self.extension}"

    @property
    def parent_dir(self) -> Path:
        return self.path.parent

class BaseRule:
    def __init__(self, scope: TargetScope = TargetScope.BASE_ONLY, is_enabled: bool = True):
        self.scope = scope
        self.is_enabled = is_enabled

    def apply(self, text: str, entry: FileEntry) -> str:
        raise NotImplementedError("子類必須實作 apply 方法")
