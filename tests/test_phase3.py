import sys
from pathlib import Path

BASE_DIR = Path(r"D:\Noah\Antigravity專案程式專用\KyteRename")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rules.base_rule import TargetScope, FileEntry
from rules.replace_rule import ReplaceRule
from rules.sanitize_rule import SanitizeRule
from rules.pinyin_rule import PinyinRule, PinyinMode
from core.rule_engine import RuleEngine

def run_phase3_tests():
    print("=== 開始測試 Phase 3 正則強化、去特殊符號與拼音規則 ===")

    # 1. 測試 ReplaceRule 的正則群組引用 ($1 / \1)
    entry1 = FileEntry(path=Path("D:/Photos/IMG_2026.jpg"), original_base="IMG_2026", extension=".jpg")
    rule_regex_group = ReplaceRule(
        find_str=r"(IMG)_(\d+)",
        replace_str="Photo_$2",
        is_regex=True
    )
    engine = RuleEngine([rule_regex_group])
    assert engine.preview(entry1) == "Photo_2026.jpg"
    print("[PASS] 1. 正則群組引用 ($1 / \\1) 替換成功")

    # 2. 測試正則驗證器 validate_pattern
    valid, err = ReplaceRule.validate_pattern(r"\d+", is_regex=True)
    assert valid is True and err is None
    invalid, err = ReplaceRule.validate_pattern(r"[0-9", is_regex=True)
    assert invalid is False and err is not None
    print("[PASS] 2. 正則表達式語法合法性即時驗證通過")

    # 3. 測試 SanitizeRule 去除 Windows 非法字元
    entry_illegal = FileEntry(path=Path("D:/test/file:name*test?<.txt"), original_base="file:name*test?<", extension=".txt")
    rule_sanitize = SanitizeRule(remove_illegal=True, remove_symbols=False)
    engine.set_rules([rule_sanitize])
    assert engine.preview(entry_illegal) == "filenametest.txt"
    print("[PASS] 3. Windows 非法字元 (:*?\"<>|) 自動清洗成功")

    # 4. 測試 SanitizeRule 去除常見裝飾性符號 (【】★等)
    entry_symbols = FileEntry(path=Path("D:/test/【高清】★年度大作★.mp4"), original_base="【高清】★年度大作★", extension=".mp4")
    rule_symbols = SanitizeRule(remove_illegal=True, remove_symbols=True)
    engine.set_rules([rule_symbols])
    assert engine.preview(entry_symbols) == "高清年度大作.mp4"
    print("[PASS] 4. 裝飾性特殊符號 (【】★等) 自動清洗成功")

    # 5. 測試 PinyinRule (中文轉拼音)
    entry_pinyin = FileEntry(path=Path("D:/music/晴天.mp3"), original_base="晴天", extension=".mp3")
    
    # 5.1 全拼小寫
    rule_py_full = PinyinRule(mode=PinyinMode.FULL, separator="_")
    engine.set_rules([rule_py_full])
    assert engine.preview(entry_pinyin) == "qing_tian.mp3"
    print("[PASS] 5.1 中文轉全拼小寫 (qing_tian) 成功")

    # 5.2 詞首大寫
    rule_py_cap = PinyinRule(mode=PinyinMode.CAPITALIZE, separator="_")
    engine.set_rules([rule_py_cap])
    assert engine.preview(entry_pinyin) == "Qing_Tian.mp3"
    print("[PASS] 5.2 中文轉詞首大寫 (Qing_Tian) 成功")

    # 5.3 首字母簡拼
    rule_py_first = PinyinRule(mode=PinyinMode.FIRST_LETTER)
    engine.set_rules([rule_py_first])
    assert engine.preview(entry_pinyin) == "qt.mp3"
    print("[PASS] 5.3 中文轉首字母簡拼 (qt) 成功")

    print("\nPhase 3 規則單元測試全數 PASS！")

if __name__ == "__main__":
    run_phase3_tests()
