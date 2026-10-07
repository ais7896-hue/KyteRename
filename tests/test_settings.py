import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# 將 KyteRename 根目錄動態加入 sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import SettingsManager

class TestSettingsManager(unittest.TestCase):
    def setUp(self):
        self.mgr = SettingsManager()

    def test_default_values(self):
        """1. 讀取預設值"""
        self.assertFalse(self.mgr.get("recursive_scan"))
        self.assertEqual(self.mgr.get("max_snapshot_history"), 15)

    def test_set_and_persist(self):
        """2. 修改與寫入"""
        orig_val = self.mgr.get("recursive_scan")
        try:
            self.mgr.set("recursive_scan", True)
            self.assertTrue(self.mgr.get("recursive_scan"))
        finally:
            self.mgr.set("recursive_scan", orig_val)
        self.assertEqual(self.mgr.get("recursive_scan"), orig_val)

    def test_migrate_snapshots(self):
        """3. 快照跨目錄遷移機制"""
        temp_dir = Path(tempfile.mkdtemp(prefix="test_migrate_"))
        try:
            dir_a = temp_dir / "dir_a"
            dir_b = temp_dir / "dir_b"
            dir_a.mkdir(parents=True, exist_ok=True)
            dir_b.mkdir(parents=True, exist_ok=True)

            (dir_a / "snapshot_001.json").write_text("{}", encoding="utf-8")
            (dir_a / "snapshot_002.json").write_text("{}", encoding="utf-8")
            (dir_a / "snapshot_003.json").write_text("{}", encoding="utf-8")

            orig_get_snap = self.mgr.get_snapshot_dir
            self.mgr.get_snapshot_dir = lambda m: dir_a if m == "a" else dir_b

            try:
                moved_count = self.mgr.migrate_snapshots("a", "b")
                self.assertEqual(moved_count, 3)
                self.assertFalse((dir_a / "snapshot_001.json").exists())
                self.assertTrue((dir_b / "snapshot_001.json").exists())
                self.assertTrue((dir_b / "snapshot_002.json").exists())
                self.assertTrue((dir_b / "snapshot_003.json").exists())
            finally:
                self.mgr.get_snapshot_dir = orig_get_snap
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

def test_settings():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSettingsManager)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == "__main__":
    unittest.main()
