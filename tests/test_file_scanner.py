import sys
import unittest
import tempfile
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.file_scanner import scan_path

class TestFileScanner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="kyte_scanner_test_"))
        
        # 建立測試目錄階層
        # root/
        #   file1.txt
        #   file2.JPG
        #   file3.png
        #   subfolder/
        #     file4.txt
        #     file5.jpg
        self.sub_dir = self.temp_dir / "subfolder"
        self.sub_dir.mkdir()

        (self.temp_dir / "file1.txt").write_text("1", encoding="utf-8")
        (self.temp_dir / "file2.JPG").write_text("22", encoding="utf-8")
        (self.temp_dir / "file3.png").write_text("333", encoding="utf-8")
        (self.sub_dir / "file4.txt").write_text("4444", encoding="utf-8")
        (self.sub_dir / "file5.jpg").write_text("55555", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scan_single_file(self):
        """測試掃描單一檔案"""
        file_path = self.temp_dir / "file1.txt"
        entries = scan_path(str(file_path))
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].original_base, "file1")
        self.assertEqual(entries[0].extension, ".txt")
        self.assertEqual(entries[0].size_bytes, 1)

    def test_scan_non_recursive(self):
        """測試非遞迴掃描目錄 (只掃第一層，不包含子目錄檔案)"""
        entries = scan_path(str(self.temp_dir), recursive=False)
        self.assertEqual(len(entries), 3)
        names = [e.original_name for e in entries]
        self.assertIn("file1.txt", names)
        self.assertIn("file2.JPG", names)
        self.assertIn("file3.png", names)

    def test_scan_recursive(self):
        """測試遞迴掃描目錄 (包含子資料夾)"""
        entries = scan_path(str(self.temp_dir), recursive=True)
        self.assertEqual(len(entries), 5)
        names = [e.original_name for e in entries]
        self.assertIn("file1.txt", names)
        self.assertIn("file4.txt", names)
        self.assertIn("file5.jpg", names)

    def test_scan_with_ext_filter(self):
        """測試副檔名過濾器 (大小寫不敏感)"""
        # 只過濾 .jpg
        entries = scan_path(str(self.temp_dir), recursive=True, ext_filter=[".jpg"])
        self.assertEqual(len(entries), 2)
        names = [e.original_name for e in entries]
        self.assertIn("file2.JPG", names)
        self.assertIn("file5.jpg", names)

        # 支援無 dot 的格式傳入: ['txt']
        entries_txt = scan_path(str(self.temp_dir), recursive=False, ext_filter=["txt"])
        self.assertEqual(len(entries_txt), 1)
        self.assertEqual(entries_txt[0].original_name, "file1.txt")

    def test_scan_non_existent_path(self):
        """測試路徑不存在時的安全防呆回傳空列表"""
        entries = scan_path("D:/non_existent_path_xyz_123")
        self.assertEqual(entries, [])

    def test_scan_sorting(self):
        """測試掃描結果依照檔名小寫自然排序"""
        entries = scan_path(str(self.temp_dir), recursive=False)
        names = [e.original_name.lower() for e in entries]
        self.assertEqual(names, sorted(names))

if __name__ == "__main__":
    unittest.main()
