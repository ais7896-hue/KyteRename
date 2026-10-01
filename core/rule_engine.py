"""
KyteRename - Rule Engine (Pipeline 規則鏈與衝突偵測)
"""
from pathlib import Path
from typing import List, Set, Tuple
from collections import Counter
from rules.base_rule import BaseRule, TargetScope, FileEntry

class RuleEngine:
    def __init__(self, rules: List[BaseRule] = None):
        self.rules: List[BaseRule] = rules or []

    def set_rules(self, rules: List[BaseRule]):
        self.rules = rules

    def preview(self, entry: FileEntry, index: int = 0) -> str:
        """對單一檔案應用所有啟用的規則鏈"""
        base = entry.original_base
        ext = entry.extension

        for rule in self.rules:
            if not rule.is_enabled:
                continue

            if rule.scope == TargetScope.BASE_ONLY:
                base = rule.apply(base, entry, index=index)
            elif rule.scope == TargetScope.EXT_ONLY:
                ext_str = rule.apply(ext.lstrip("."), entry, index=index)
                ext = f".{ext_str}" if ext_str else ""
            elif rule.scope == TargetScope.FULL_NAME:
                full = rule.apply(f"{base}{ext}", entry, index=index)
                p = Path(full)
                base = p.stem
                ext = p.suffix

        return f"{base}{ext}"

    def preview_all(self, entries: List[FileEntry]) -> List[str]:
        """批次計算所有檔案的新名稱"""
        return [self.preview(e, idx) for idx, e in enumerate(entries)]

    @staticmethod
    def detect_conflicts(entries: List[FileEntry], new_names: List[str]) -> Tuple[Set[int], Set[int]]:
        duplicates: Set[int] = set()
        disk_conflicts: Set[int] = set()

        if len(entries) != len(new_names):
            return duplicates, disk_conflicts

        path_counter = Counter()
        target_paths = []
        for entry, new_name in zip(entries, new_names):
            target_path = (entry.parent_dir / new_name).resolve()
            target_paths.append(target_path)
            path_counter[str(target_path).lower()] += 1

        for idx, target_path in enumerate(target_paths):
            if path_counter[str(target_path).lower()] > 1:
                duplicates.add(idx)

        for idx, (entry, target_path) in enumerate(zip(entries, target_paths)):
            if idx in duplicates:
                continue
            if entry.path.resolve() == target_path:
                continue
            if target_path.exists() and str(entry.path.resolve()).lower() != str(target_path).lower():
                disk_conflicts.add(idx)

        return duplicates, disk_conflicts
