import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# 將 KyteRename 根目錄動態加入 sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.rename_executor import resolve_rename_order, rename_safe
from core.snapshot_manager import SnapshotManager

class TestPhase4Execution(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="kyte_rename_test_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_chained_dependency_topological_sort(self):
        """1. 測試連鎖依賴 (file1 -> file2 -> file3 -> file4) 拓撲逆序成功"""
        f1 = self.temp_dir / "file1.txt"
        f2 = self.temp_dir / "file2.txt"
        f3 = self.temp_dir / "file3.txt"
        f4 = self.temp_dir / "file4.txt"
        f1.write_text("content_1", encoding="utf-8")
        f2.write_text("content_2", encoding="utf-8")
        f3.write_text("content_3", encoding="utf-8")

        ops = [
            (f1, f2),
            (f2, f3),
            (f3, f4),
        ]

        ordered_ops = resolve_rename_order(ops)
        for s, d in ordered_ops:
            rename_safe(s, d)

        self.assertEqual(f4.read_text(encoding="utf-8"), "content_3")
        self.assertEqual(f3.read_text(encoding="utf-8"), "content_2")
        self.assertEqual(f2.read_text(encoding="utf-8"), "content_1")
        self.assertFalse(f1.exists())

    def test_cycle_dependency_breaking(self):
        """2. 測試真循環依賴破圈 (Cycle: A -> B, B -> A)"""
        cA = self.temp_dir / "cycleA.txt"
        cB = self.temp_dir / "cycleB.txt"
        cA.write_text("A_DATA", encoding="utf-8")
        cB.write_text("B_DATA", encoding="utf-8")

        cycle_ops = [(cA, cB), (cB, cA)]
        ordered_cycle = resolve_rename_order(cycle_ops)

        for s, d in ordered_cycle:
            rename_safe(s, d)

        self.assertEqual(cA.read_text(encoding="utf-8"), "B_DATA")
        self.assertEqual(cB.read_text(encoding="utf-8"), "A_DATA")

    def test_case_only_rename(self):
        """3. 測試大小寫變更 (test_case.txt -> TEST_CASE.TXT) NTFS 安全更名"""
        case_file = self.temp_dir / "test_case.txt"
        case_file.write_text("CASE_TEST", encoding="utf-8")
        target_case = self.temp_dir / "TEST_CASE.TXT"

        rename_safe(case_file, target_case)
        self.assertEqual(target_case.name, "TEST_CASE.TXT")

    def test_snapshot_and_undo(self):
        """4. 測試快照日誌儲存與還原 (Undo / Ctrl+Z)"""
        snap_dir = self.temp_dir / "snapshots"
        mgr = SnapshotManager(snapshot_dir=snap_dir)

        u1 = self.temp_dir / "doc1.txt"
        u2 = self.temp_dir / "doc2.txt"
        u1.write_text("doc_1", encoding="utf-8")
        u2.write_text("doc_2", encoding="utf-8")

        renamed_u1 = self.temp_dir / "doc_final_1.txt"
        renamed_u2 = self.temp_dir / "doc_final_2.txt"

        rename_safe(u1, renamed_u1)
        rename_safe(u2, renamed_u2)

        success_log = [
            {"original_path": str(u1.resolve()), "renamed_path": str(renamed_u1.resolve()), "size": 5, "mtime": 0.0},
            {"original_path": str(u2.resolve()), "renamed_path": str(renamed_u2.resolve()), "size": 5, "mtime": 0.0},
        ]
        snap_file = mgr.save_snapshot(success_log)
        self.assertIsNotNone(snap_file)
        self.assertTrue(snap_file.exists())

        undo_res = mgr.undo_snapshot(snap_file)
        self.assertTrue(undo_res["success"])
        self.assertEqual(undo_res["restored_count"], 2)
        self.assertTrue(u1.exists())
        self.assertEqual(u1.read_text(encoding="utf-8"), "doc_1")
        self.assertTrue(u2.exists())
        self.assertEqual(u2.read_text(encoding="utf-8"), "doc_2")
        self.assertFalse(renamed_u1.exists())
        self.assertFalse(renamed_u2.exists())

def test_phase4():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase4Execution)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == "__main__":
    unittest.main()
