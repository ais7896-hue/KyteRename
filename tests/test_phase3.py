import sys
import unittest
from pathlib import Path

# 將 KyteRename 根目錄動態加入 sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rules.base_rule import TargetScope, FileEntry
from rules.replace_rule import ReplaceRule
from rules.sanitize_rule import SanitizeRule
from rules.pinyin_rule import PinyinRule, PinyinMode
from core.rule_engine import RuleEngine

class TestPhase3Rules(unittest.TestCase):
    def test_regex_group_reference(self):
        """1. 測試 ReplaceRule 的正則群組引用 ($1 / \\1)"""
        entry1 = FileEntry(path=Path("D:/Photos/IMG_2026.jpg"), original_base="IMG_2026", extension=".jpg")
        rule_regex_group = ReplaceRule(
            find_str=r"(IMG)_(\d+)",
            replace_str="Photo_$2",
            is_regex=True
        )
        engine = RuleEngine([rule_regex_group])
        self.assertEqual(engine.preview(entry1), "Photo_2026.jpg")

    def test_regex_validate_pattern(self):
        """2. 測試正則驗證器 validate_pattern"""
        valid, err = ReplaceRule.validate_pattern(r"\d+", is_regex=True)
        self.assertTrue(valid)
        self.assertIsNone(err)

        invalid, err = ReplaceRule.validate_pattern(r"[0-9", is_regex=True)
        self.assertFalse(invalid)
        self.assertIsNotNone(err)

    def test_sanitize_illegal_characters(self):
        """3. 測試 SanitizeRule 去除 Windows 非法字元 (:*?\"<>|)"""
        entry_illegal = FileEntry(path=Path("D:/test/file:name*test?<.txt"), original_base="file:name*test?<", extension=".txt")
        rule_sanitize = SanitizeRule(remove_illegal=True, remove_symbols=False)
        engine = RuleEngine([rule_sanitize])
        self.assertEqual(engine.preview(entry_illegal), "filenametest.txt")

    def test_sanitize_symbols(self):
        """4. 測試 SanitizeRule 去除常見裝飾性符號 (【】★等)"""
        entry_symbols = FileEntry(path=Path("D:/test/【高清】★年度大作★.mp4"), original_base="【高清】★年度大作★", extension=".mp4")
        rule_symbols = SanitizeRule(remove_illegal=True, remove_symbols=True)
        engine = RuleEngine([rule_symbols])
        self.assertEqual(engine.preview(entry_symbols), "高清年度大作.mp4")

    def test_pinyin_conversion(self):
        """5. 測試 PinyinRule (中文轉全拼、詞首大寫、簡拼)"""
        entry_pinyin = FileEntry(path=Path("D:/music/晴天.mp3"), original_base="晴天", extension=".mp3")

        # 5.1 全拼小寫
        rule_py_full = PinyinRule(mode=PinyinMode.FULL, separator="_")
        engine = RuleEngine([rule_py_full])
        self.assertEqual(engine.preview(entry_pinyin), "qing_tian.mp3")

        # 5.2 詞首大寫
        rule_py_cap = PinyinRule(mode=PinyinMode.CAPITALIZE, separator="_")
        engine.set_rules([rule_py_cap])
        self.assertEqual(engine.preview(entry_pinyin), "Qing_Tian.mp3")

        # 5.3 首字母簡拼
        rule_py_first = PinyinRule(mode=PinyinMode.FIRST_LETTER)
        engine.set_rules([rule_py_first])
        self.assertEqual(engine.preview(entry_pinyin), "qt.mp3")

def run_phase3_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase3Rules)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == "__main__":
    unittest.main()
