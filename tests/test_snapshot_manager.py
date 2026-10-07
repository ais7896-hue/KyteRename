import sys
import unittest
import tempfile
import shutil
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.snapshot_manager import SnapshotManager

class TestSnapshotManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="kyte_snap_mgr_test_"))
        self.mgr = SnapshotManager(snapshot_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_empty_operations(self):
        """測試空操作清單不建立快照"""
        res = self.mgr.save_snapshot([])
        self.assertIsNone(res)

    def test_save_and_get_latest_snapshot(self):
        """測試快照儲存與取得最新快照"""
        ops1 = [{"original_path": "a.txt", "renamed_path": "b.txt"}]
        snap1 = self.mgr.save_snapshot(ops1)
        self.assertIsNotNone(snap1)
        self.assertTrue(snap1.exists())

        latest = self.mgr.get_latest_snapshot()
        self.assertEqual(latest, snap1)

    def test_cleanup_old_snapshots_limit(self):
        """測試超過 max_snapshots (預設 15) 時自動清理舊快照"""
        self.mgr.max_snapshots = 3

        snaps = []
        for i in range(5):
            s = self.mgr.save_snapshot([{"original_path": f"src_{i}.txt", "renamed_path": f"dst_{i}.txt"}])
            snaps.append(s)
            time.sleep(0.01)

        remaining = list(self.temp_dir.glob("snapshot_*.json"))
        self.assertEqual(len(remaining), 3)
        # 最舊的 2 個快照應被刪除
        self.assertFalse(snaps[0].exists())
        self.assertFalse(snaps[1].exists())
        # 最新的 3 個快照應存在
        self.assertTrue(snaps[2].exists())
        self.assertTrue(snaps[3].exists())
        self.assertTrue(snaps[4].exists())

    def test_undo_non_existent_snapshot(self):
        """測試沒有快照時 undo 回傳錯誤資訊而非 crash"""
        res = self.mgr.undo_snapshot(Path("non_existent_snapshot.json"))
        self.assertFalse(res["success"])
        self.assertEqual(res["error_code"], "no_snapshot")

    def test_undo_corrupted_json(self):
        """測試損毀的 JSON 快照檔防呆"""
        corrupted = self.temp_dir / "snapshot_bad.json"
        corrupted.write_text("{bad_json...", encoding="utf-8")

        res = self.mgr.undo_snapshot(corrupted)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_code"], "read_failed")

    def test_undo_file_missing_graceful_handling(self):
        """測試檔案已被使用者刪除時的單檔還原失敗記錄與容錯"""
        src = self.temp_dir / "orig.txt"
        dst = self.temp_dir / "target.txt"

        snap = self.mgr.save_snapshot([{
            "original_path": str(src.resolve()),
            "renamed_path": str(dst.resolve()),
            "size": 10,
            "mtime": 0.0
        }])

        # 不產生 dst 檔案，模擬目標檔案已被移走
        res = self.mgr.undo_snapshot(snap)
        self.assertTrue(res["success"])
        self.assertEqual(res["restored_count"], 0)
        self.assertEqual(res["failed_count"], 1)
        self.assertIn("已被移動或刪除", res["failed_details"][0]["reason"])

if __name__ == "__main__":
    unittest.main()
