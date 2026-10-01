import sys
from pathlib import Path

BASE_DIR = Path(r"D:\Noah\Antigravity專案程式專用\KyteRename")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rules.base_rule import TargetScope, FileEntry
from rules.serial_rule import SerialRule, SerialPosition
from rules.case_rule import CaseRule, CaseMode
from rules.trim_rule import TrimRule
from rules.metadata_rule import MetadataRule
from core.rule_engine import RuleEngine

def run_phase2_tests():
    print("=== 開始測試 Phase 2 擴充規則 ===")

    # 1. 測試 SerialRule (補零流水號)
    entry1 = FileEntry(path=Path("D:/Photos/IMG.jpg"), original_base="IMG", extension=".jpg")
    entry2 = FileEntry(path=Path("D:/Photos/IMG2.jpg"), original_base="IMG2", extension=".jpg")

    rule_serial = SerialRule(start=1, step=1, padding=3, position=SerialPosition.SUFFIX)
    engine = RuleEngine([rule_serial])
    assert engine.preview(entry1, index=0) == "IMG_001.jpg"
    assert engine.preview(entry2, index=1) == "IMG2_002.jpg"
    print("[PASS] 1. SerialRule 流水號補零 (001, 002) 測試通過")

    # 2. 測試 SerialRule 替換模式 (Position.REPLACE)
    rule_serial_replace = SerialRule(start=10, step=5, padding=4, position=SerialPosition.REPLACE)
    engine.set_rules([rule_serial_replace])
    assert engine.preview(entry1, index=0) == "0010.jpg"
    assert engine.preview(entry2, index=1) == "0015.jpg"
    print("[PASS] 2. SerialRule 完全替換編號測試通過")

    # 3. 測試 CaseRule (大小寫轉換)
    entry_case = FileEntry(path=Path("D:/test/my_COOL_PHOTO.JPEG"), original_base="my_COOL_PHOTO", extension=".JPEG")
    rule_case_ext = CaseRule(mode=CaseMode.LOWER, scope=TargetScope.EXT_ONLY)
    engine.set_rules([rule_case_ext])
    assert engine.preview(entry_case) == "my_COOL_PHOTO.jpeg"
    print("[PASS] 3. CaseRule 副檔名轉小寫測試通過")

    rule_case_title = CaseRule(mode=CaseMode.TITLE, scope=TargetScope.BASE_ONLY)
    engine.set_rules([rule_case_title])
    assert engine.preview(entry_case) == "My_Cool_Photo.JPEG"
    print("[PASS] 4. CaseRule 詞首大寫 (Title Case) 測試通過")

    # 4. 測試 TrimRule (多餘空格與頭尾空白)
    entry_trim = FileEntry(path=Path("D:/test/  hello   world  test  .txt"), original_base="  hello   world  test  ", extension=".txt")
    rule_trim = TrimRule(trim_ends=True, collapse_spaces=True)
    engine.set_rules([rule_trim])
    assert engine.preview(entry_trim) == "hello world test.txt"
    print("[PASS] 5. TrimRule 多餘空白壓縮與首尾修剪測試通過")

    # 5. 測試 MetadataRule (變數展開)
    meta_entry = FileEntry(
        path=Path("D:/DCIM/DSC_005.JPG"),
        original_base="DSC_005",
        extension=".JPG",
        metadata={
            "exif_date": "20261001",
            "resolution": "4K",
            "artist": "KyteArtist"
        },
        is_meta_loaded=True
    )
    rule_meta = MetadataRule(template="{exif_date}_{resolution}_{original}")
    engine.set_rules([rule_meta])
    assert engine.preview(meta_entry) == "20261001_4K_DSC_005.JPG"
    print("[PASS] 6. MetadataRule 變數替換測試通過")

    # 6. 測試未載入元資料時的漸進式佔位符 "[讀取中...]"
    unloaded_entry = FileEntry(path=Path("D:/DCIM/DSC_006.JPG"), original_base="DSC_006", extension=".JPG", is_meta_loaded=False)
    res_unloaded = engine.preview(unloaded_entry)
    assert "[讀取中...]" in res_unloaded
    assert "DSC_006.JPG" in res_unloaded
    print(f"[PASS] 7. Metadata 漸進式佔位符測試通過 (預覽: {res_unloaded})")

    print("\nPhase 2 所有規則邏輯驗證全部 PASS！")

if __name__ == "__main__":
    run_phase2_tests()
