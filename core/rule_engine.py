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

    def preview(self, entry: FileEntry) -> str:
        """對單一檔案應用所有啟用的規則鏈"""
        base = entry.original_base
        ext = entry.extension

        for rule in self.rules:
            if not rule.is_enabled:
                continue

            if rule.scope == TargetScope.BASE_ONLY:
                base = rule.apply(base, entry)
            elif rule.scope == TargetScope.EXT_ONLY:
                # 確保副檔名格式整齊（若使用者改名後無點號，補上點號）
                ext_str = rule.apply(ext.lstrip("."), entry)
                ext = f".{ext_str}" if ext_str else ""
            elif rule.scope == TargetScope.FULL_NAME:
                full = rule.apply(f"{base}{ext}", entry)
                p = Path(full)
                base = p.stem
                ext = p.suffix

        return f"{base}{ext}"

    def preview_all(self, entries: List[FileEntry]) -> List[str]:
        """批次計算所有檔案的新名稱"""
        return [self.preview(e) for e in entries]

    @staticmethod
    def detect_conflicts(entries: List[FileEntry], new_names: List[str]) -> Tuple[Set[int], Set[int]]:
        """
        偵測兩種衝突：
        1. 批次內重複：相同父目錄下，有兩個或以上檔案更名為同一個名字
        2. 目標已存在：改名後的目標檔案在硬碟上已存在且不是自己
        回傳 (duplicate_indices, disk_exists_indices)
        """
        duplicates: Set[int] = set()
        disk_conflicts: Set[int] = set()

        if len(entries) != len(new_names):
            return duplicates, disk_conflicts

        # 1. 偵測批次內相同目錄重複
        path_counter = Counter()
        target_paths = []
        for entry, new_name in zip(entries, new_names):
            target_path = (entry.parent_dir / new_name).resolve()
            target_paths.append(target_path)
            # 大小寫不敏感比對（Windows 特性）
            path_counter[str(target_path).lower()] += 1

        for idx, target_path in enumerate(target_paths):
            if path_counter[str(target_path).lower()] > 1:
                duplicates.add(idx)

        # 2. 偵測硬碟實體衝突 (排除本身未更名的情況)
        for idx, (entry, target_path) in enumerate(zip(entries, target_paths)):
            if idx in duplicates:
                continue
            # 若路徑沒變，不是衝突
            if entry.path.resolve() == target_path:
                continue
            # 如果目標在磁碟已存在（且大小寫與來源不完全相同），屬於真實衝突
            if target_path.exists() and str(entry.path.resolve()).lower() != str(target_path).lower():
                disk_conflicts.add(idx)

        return duplicates, disk_conflicts
