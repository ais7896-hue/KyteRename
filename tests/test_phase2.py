import sys
import unittest
from pathlib import Path

# 將 KyteRename 根目錄動態加入 sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rules.base_rule import TargetScope, FileEntry
from rules.serial_rule import SerialRule, SerialPosition
from rules.case_rule import CaseRule, CaseMode
from rules.trim_rule import TrimRule
from rules.metadata_rule import MetadataRule
from core.rule_engine import RuleEngine

class TestPhase2Rules(unittest.TestCase):
    def setUp(self):
        self.entry1 = FileEntry(path=Path("D:/Photos/IMG.jpg"), original_base="IMG", extension=".jpg")
        self.entry2 = FileEntry(path=Path("D:/Photos/IMG2.jpg"), original_base="IMG2", extension=".jpg")
        self.entry_case = FileEntry(path=Path("D:/test/my_COOL_PHOTO.JPEG"), original_base="my_COOL_PHOTO", extension=".JPEG")
        self.entry_trim = FileEntry(path=Path("D:/test/  hello   world  test  .txt"), original_base="  hello   world  test  ", extension=".txt")

    def test_serial_suffix(self):
        """1. 測試 SerialRule (補零流水號後綴)"""
        rule_serial = SerialRule(start=1, step=1, padding=3, position=SerialPosition.SUFFIX)
        engine = RuleEngine([rule_serial])
        self.assertEqual(engine.preview(self.entry1, index=0), "IMG_001.jpg")
        self.assertEqual(engine.preview(self.entry2, index=1), "IMG2_002.jpg")

    def test_serial_replace(self):
        """2. 測試 SerialRule 替換模式 (Position.REPLACE)"""
        rule_serial_replace = SerialRule(start=10, step=5, padding=4, position=SerialPosition.REPLACE)
        engine = RuleEngine([rule_serial_replace])
        self.assertEqual(engine.preview(self.entry1, index=0), "0010.jpg")
        self.assertEqual(engine.preview(self.entry2, index=1), "0015.jpg")

    def test_case_ext_lower(self):
        """3. 測試 CaseRule 副檔名轉小寫"""
        rule_case_ext = CaseRule(mode=CaseMode.LOWER, scope=TargetScope.EXT_ONLY)
        engine = RuleEngine([rule_case_ext])
        self.assertEqual(engine.preview(self.entry_case), "my_COOL_PHOTO.jpeg")

    def test_case_base_title(self):
        """4. 測試 CaseRule 詞首大寫 (Title Case)"""
        rule_case_title = CaseRule(mode=CaseMode.TITLE, scope=TargetScope.BASE_ONLY)
        engine = RuleEngine([rule_case_title])
        self.assertEqual(engine.preview(self.entry_case), "My_Cool_Photo.JPEG")

    def test_trim_spaces(self):
        """5. 測試 TrimRule 多餘空白壓縮與首尾修剪"""
        rule_trim = TrimRule(trim_ends=True, collapse_spaces=True)
        engine = RuleEngine([rule_trim])
        self.assertEqual(engine.preview(self.entry_trim), "hello world test.txt")

    def test_metadata_template(self):
        """6. 測試 MetadataRule 變數替換"""
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
        engine = RuleEngine([rule_meta])
        self.assertEqual(engine.preview(meta_entry), "20261001_4K_DSC_005.JPG")

    def test_metadata_placeholder(self):
        """7. 測試未載入元資料時的漸進式佔位符 [讀取中...]"""
        unloaded_entry = FileEntry(path=Path("D:/DCIM/DSC_006.JPG"), original_base="DSC_006", extension=".JPG", is_meta_loaded=False)
        rule_meta = MetadataRule(template="{exif_date}_{original}")
        engine = RuleEngine([rule_meta])
        res_unloaded = engine.preview(unloaded_entry)
        self.assertIn("[讀取中...]", res_unloaded)
        self.assertIn("DSC_006.JPG", res_unloaded)

def run_phase2_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase2Rules)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == "__main__":
    unittest.main()
