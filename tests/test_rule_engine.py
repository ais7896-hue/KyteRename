import sys
import unittest
from pathlib import Path

# 將 KyteRename 根目錄動態加入 sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rules.base_rule import TargetScope, FileEntry
from rules.replace_rule import ReplaceRule
from rules.prefix_suffix_rule import PrefixSuffixRule
from core.rule_engine import RuleEngine

class TestRuleEngine(unittest.TestCase):
    def setUp(self):
        self.entry1 = FileEntry(path=Path("D:/Photos/IMG_001.JPG"), original_base="IMG_001", extension=".JPG")

    def test_base_replace(self):
        """測試 1: 基礎主檔名取代"""
        rule_replace = ReplaceRule(find_str="IMG", replace_str="Photo", scope=TargetScope.BASE_ONLY)
        engine = RuleEngine([rule_replace])
        res = engine.preview(self.entry1)
        self.assertEqual(res, "Photo_001.JPG")

    def test_ext_replace(self):
        """測試 2: 副檔名作用域取代"""
        rule_ext = ReplaceRule(find_str="JPG", replace_str="jpg", scope=TargetScope.EXT_ONLY)
        engine = RuleEngine([rule_ext])
        res = engine.preview(self.entry1)
        self.assertEqual(res, "IMG_001.jpg")

    def test_prefix_suffix(self):
        """測試 3: 前後綴增加"""
        rule_prefix = PrefixSuffixRule(prefix="2026_", suffix="_v1", scope=TargetScope.BASE_ONLY)
        engine = RuleEngine([rule_prefix])
        res = engine.preview(self.entry1)
        self.assertEqual(res, "2026_IMG_001_v1.JPG")

    def test_pipeline_chain(self):
        """測試 4: Pipeline 規則串聯 (先取代，再加前後綴)"""
        rule_replace = ReplaceRule(find_str="IMG", replace_str="Photo", scope=TargetScope.BASE_ONLY)
        rule_prefix = PrefixSuffixRule(prefix="2026_", suffix="_v1", scope=TargetScope.BASE_ONLY)
        engine = RuleEngine([rule_replace, rule_prefix])
        res = engine.preview(self.entry1)
        self.assertEqual(res, "2026_Photo_001_v1.JPG")

    def test_regex_replace(self):
        """測試 5: 正則表達式取代"""
        rule_regex = ReplaceRule(find_str=r"\d+", replace_str="FINAL", is_regex=True)
        engine = RuleEngine([rule_regex])
        res = engine.preview(self.entry1)
        self.assertEqual(res, "IMG_FINAL.JPG")

    def test_conflict_detection(self):
        """測試 6: 命名重複衝突偵測"""
        entries = [
            FileEntry(path=Path("D:/Photos/a.jpg"), original_base="a", extension=".jpg"),
            FileEntry(path=Path("D:/Photos/b.jpg"), original_base="b", extension=".jpg"),
            FileEntry(path=Path("D:/Photos/c.jpg"), original_base="c", extension=".jpg"),
        ]
        new_names = ["same.jpg", "same.jpg", "unique.jpg"]
        dups, _ = RuleEngine.detect_conflicts(entries, new_names)
        self.assertIn(0, dups)
        self.assertIn(1, dups)
        self.assertNotIn(2, dups)

def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRuleEngine)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == "__main__":
    unittest.main()
