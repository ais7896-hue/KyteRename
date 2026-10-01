import sys
from pathlib import Path

# 將 KyteRename 加入 sys.path
BASE_DIR = Path(r"D:\Noah\Antigravity專案程式專用\KyteRename")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rules.base_rule import TargetScope, FileEntry
from rules.replace_rule import ReplaceRule
from rules.prefix_suffix_rule import PrefixSuffixRule
from core.rule_engine import RuleEngine

def run_tests():
    print("=== 開始測試 Phase 1 規則引擎與資料模型 ===")
    
    # 測試 1: 基礎主檔名取代
    entry1 = FileEntry(path=Path("D:/Photos/IMG_001.JPG"), original_base="IMG_001", extension=".JPG")
    rule_replace = ReplaceRule(find_str="IMG", replace_str="Photo", scope=TargetScope.BASE_ONLY)
    engine = RuleEngine([rule_replace])
    res1 = engine.preview(entry1)
    assert res1 == "Photo_001.JPG", f"Expected Photo_001.JPG, got {res1}"
    print("[PASS] 測試 1: 基礎主檔名取代")

    # 測試 2: 副檔名統一小寫/取代 (TargetScope.EXT_ONLY)
    rule_ext = ReplaceRule(find_str="JPG", replace_str="jpg", scope=TargetScope.EXT_ONLY)
    engine.set_rules([rule_ext])
    res2 = engine.preview(entry1)
    assert res2 == "IMG_001.jpg", f"Expected IMG_001.jpg, got {res2}"
    print("[PASS] 測試 2: 副檔名作用域取代")

    # 測試 3: 前後綴增刪 (PrefixSuffixRule)
    rule_prefix = PrefixSuffixRule(prefix="2026_", suffix="_v1", scope=TargetScope.BASE_ONLY)
    engine.set_rules([rule_prefix])
    res3 = engine.preview(entry1)
    assert res3 == "2026_IMG_001_v1.JPG", f"Expected 2026_IMG_001_v1.JPG, got {res3}"
    print("[PASS] 測試 3: 前後綴增加")

    # 測試 4: Pipeline 規則串聯 (先取代，再加前後綴)
    engine.set_rules([rule_replace, rule_prefix])
    res4 = engine.preview(entry1)
    assert res4 == "2026_Photo_001_v1.JPG", f"Expected 2026_Photo_001_v1.JPG, got {res4}"
    print("[PASS] 測試 4: Pipeline 規則串聯")

    # 測試 5: 正則表達式取代
    rule_regex = ReplaceRule(find_str=r"\d+", replace_str="FINAL", is_regex=True)
    engine.set_rules([rule_regex])
    res5 = engine.preview(entry1)
    assert res5 == "IMG_FINAL.JPG", f"Expected IMG_FINAL.JPG, got {res5}"
    print("[PASS] 測試 5: 正則表達式取代")

    # 測試 6: 衝突偵測
    entries = [
        FileEntry(path=Path("D:/Photos/a.jpg"), original_base="a", extension=".jpg"),
        FileEntry(path=Path("D:/Photos/b.jpg"), original_base="b", extension=".jpg"),
        FileEntry(path=Path("D:/Photos/c.jpg"), original_base="c", extension=".jpg"),
    ]
    # 將 a 和 b 都改成 same.jpg
    new_names = ["same.jpg", "same.jpg", "unique.jpg"]
    dups, _ = RuleEngine.detect_conflicts(entries, new_names)
    assert 0 in dups and 1 in dups, f"Expected indices 0 and 1 in duplicates, got {dups}"
    assert 2 not in dups, f"Index 2 should not be in duplicates"
    print("[PASS] 測試 6: 命名重複衝突偵測")

    print("\n所有單元測試通過！")

if __name__ == "__main__":
    run_tests()
