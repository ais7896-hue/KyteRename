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
    @staticmethod
    def apply_conflict_policy(
        entries: List[FileEntry],
        new_names: List[str],
        policy: str = "ask"
    ) -> Tuple[List[str], Set[int], Set[int]]:
        """
        依策略處理衝突:
        - 'ask': 維持計算結果，回傳 (new_names, duplicates, disk_conflicts)
        - 'skip': 衝突項目還原為 original_name，不進行改名
        - 'suffix': 衝突項目自動增補後綴 _1, _2 等直到完全不重複且不存在於磁碟
        """
        if policy == "skip":
            resolved_names = list(new_names)
            dups, disk_c = RuleEngine.detect_conflicts(entries, resolved_names)
            for idx in dups | disk_c:
                resolved_names[idx] = entries[idx].original_name
            dups2, disk_c2 = RuleEngine.detect_conflicts(entries, resolved_names)
            return resolved_names, dups2, disk_c2

        elif policy == "suffix":
            parent_occupied = {}
            for entry in entries:
                p = entry.parent_dir
                if p not in parent_occupied:
                    disk_files = set()
                    if p.exists() and p.is_dir():
                        try:
                            disk_files = {f.name.lower() for f in p.iterdir()}
                        except Exception:
                            pass
                    parent_occupied[p] = disk_files

            final_names = []
            planned_per_dir = {}
            for i, (entry, name) in enumerate(zip(entries, new_names)):
                p = entry.parent_dir
                if p not in planned_per_dir:
                    planned_per_dir[p] = set()

                stem = Path(name).stem
                suffix = Path(name).suffix
                cand_name = name
                cand_lower = cand_name.lower()

                counter = 1
                while True:
                    is_planned_dup = cand_lower in planned_per_dir[p]
                    is_disk_dup = (cand_lower in parent_occupied[p]) and (cand_lower != entry.original_name.lower())
                    if not is_planned_dup and not is_disk_dup:
                        break
                    cand_name = f"{stem}_{counter}{suffix}"
                    cand_lower = cand_name.lower()
                    counter += 1

                planned_per_dir[p].add(cand_lower)
                final_names.append(cand_name)

            dups, disk_c = RuleEngine.detect_conflicts(entries, final_names)
            return final_names, dups, disk_c

        # 預設 'ask'
        dups, disk_c = RuleEngine.detect_conflicts(entries, new_names)
        return list(new_names), dups, disk_c

