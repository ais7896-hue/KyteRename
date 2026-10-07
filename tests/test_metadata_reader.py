import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.metadata_reader import format_size, read_file_metadata

class TestMetadataReader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="kyte_meta_test_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_format_size(self):
        """測試檔案大小單位格式化 (B, KB, MB, GB, TB)"""
        self.assertEqual(format_size(500), "500B")
        self.assertEqual(format_size(1024), "1.0KB")
        self.assertEqual(format_size(1024 * 1024), "1.0MB")
        self.assertEqual(format_size(1024 * 1024 * 1024), "1.0GB")
        self.assertEqual(format_size(1024 * 1024 * 1024 * 1024), "1.0TB")

    def test_basic_file_system_attributes(self):
        """測試讀取基本檔案系統屬性 (date, year, size, ext 等)"""
        f = self.temp_dir / "sample.txt"
        f.write_text("Hello Metadata!", encoding="utf-8")

        meta = read_file_metadata(f)
        self.assertIn("date", meta)
        self.assertIn("datetime", meta)
        self.assertIn("year", meta)
        self.assertIn("month", meta)
        self.assertIn("day", meta)
        self.assertEqual(meta["parent"], self.temp_dir.name)
        self.assertEqual(meta["ext"], "txt")
        self.assertTrue(meta["size"].endswith("B"))

    def test_image_metadata_and_resolution(self):
        """測試圖片解析度判斷與讀取 (1080p, 4K 等)"""
        # 測試 1080p
        img_1080p = self.temp_dir / "test_1080p.png"
        im = Image.new("RGB", (1920, 1080), color="blue")
        im.save(img_1080p)

        meta = read_file_metadata(img_1080p)
        self.assertEqual(meta.get("width"), "1920")
        self.assertEqual(meta.get("height"), "1080")
        self.assertEqual(meta.get("resolution"), "1080p")

        # 測試 4K
        img_4k = self.temp_dir / "test_4k.jpg"
        im4k = Image.new("RGB", (3840, 2160), color="red")
        im4k.save(img_4k)

        meta_4k = read_file_metadata(img_4k)
        self.assertEqual(meta_4k.get("resolution"), "4K")

    def test_non_existent_file(self):
        """測試不存在檔案時安全返回空字典"""
        meta = read_file_metadata(Path("D:/not_exist_file.xyz"))
        self.assertEqual(meta, {})

    def test_corrupted_or_empty_audio_file(self):
        """測試損毀或假音訊副檔名的例外處理防呆"""
        fake_audio = self.temp_dir / "fake.mp3"
        fake_audio.write_text("not real mp3 content", encoding="utf-8")
        meta = read_file_metadata(fake_audio)
        # 應至少有 basic metadata，而不會 crash 崩潰
        self.assertEqual(meta.get("ext"), "mp3")
        self.assertNotIn("artist", meta)

if __name__ == "__main__":
    unittest.main()
