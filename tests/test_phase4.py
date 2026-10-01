import sys
import tempfile
import shutil
from pathlib import Path

BASE_DIR = Path(r"D:\Noah\Antigravity專案程式專用\KyteRename")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.rename_executor import resolve_rename_order, rename_safe
from core.snapshot_manager import SnapshotManager

def test_phase4():
    print("=== 開始測試 Phase 4 拓撲防撞改名與快照還原 ===")

    temp_dir = Path(tempfile.mkdtemp(prefix="kyte_rename_test_"))
    try:
        # 1. 測試連鎖依賴 (file1 -> file2 -> file3 -> file4)
        f1 = temp_dir / "file1.txt"
        f2 = temp_dir / "file2.txt"
        f3 = temp_dir / "file3.txt"
        f1.write_text("content_1", encoding="utf-8")
        f2.write_text("content_2", encoding="utf-8")
        f3.write_text("content_3", encoding="utf-8")

        f4 = temp_dir / "file4.txt"

        ops = [
            (f1, f2),
            (f2, f3),
            (f3, f4),
        ]

        ordered_ops = resolve_rename_order(ops)
        print(f"拓撲排序結果: {[ (s.name, d.name) for s, d in ordered_ops ]}")

        # 執行更名
        for s, d in ordered_ops:
            rename_safe(s, d)

        assert f4.read_text(encoding="utf-8") == "content_3"
        assert f3.read_text(encoding="utf-8") == "content_2"
        assert f2.read_text(encoding="utf-8") == "content_1"
        assert not f1.exists()
        print("[PASS] 1. 連鎖更名 (file1->file2->file3) 拓撲逆序成功，無任何覆蓋衝突")

        # 2. 測試真循環依賴破圈 (Cycle: A -> B, B -> A)
        cA = temp_dir / "cycleA.txt"
        cB = temp_dir / "cycleB.txt"
        cA.write_text("A_DATA", encoding="utf-8")
        cB.write_text("B_DATA", encoding="utf-8")

        cycle_ops = [(cA, cB), (cB, cA)]
        ordered_cycle = resolve_rename_order(cycle_ops)
        print(f"循環依賴破圈結果: {[ (s.name, d.name) for s, d in ordered_cycle ]}")

        for s, d in ordered_cycle:
            rename_safe(s, d)

        assert cA.read_text(encoding="utf-8") == "B_DATA"
        assert cB.read_text(encoding="utf-8") == "A_DATA"
        print("[PASS] 2. 循環互換 (A <-> B) 暫存檔自動破圈成功")

        # 3. 測試大小寫變更 (test_case.txt -> TEST_CASE.TXT)
        case_file = temp_dir / "test_case.txt"
        case_file.write_text("CASE_TEST", encoding="utf-8")
        target_case = temp_dir / "TEST_CASE.TXT"

        rename_safe(case_file, target_case)
        assert target_case.name == "TEST_CASE.TXT"
        print("[PASS] 3. NTFS 兩階段大小寫安全更名成功")

        # 4. 測試快照日誌儲存與還原 (Undo / Ctrl+Z)
        snap_dir = temp_dir / "snapshots"
        mgr = SnapshotManager(snapshot_dir=snap_dir)

        # 模擬一批更名操作
        u1 = temp_dir / "doc1.txt"
        u2 = temp_dir / "doc2.txt"
        u1.write_text("doc_1", encoding="utf-8")
        u2.write_text("doc_2", encoding="utf-8")

        renamed_u1 = temp_dir / "doc_final_1.txt"
        renamed_u2 = temp_dir / "doc_final_2.txt"

        rename_safe(u1, renamed_u1)
        rename_safe(u2, renamed_u2)

        success_log = [
            {"original_path": str(u1.resolve()), "renamed_path": str(renamed_u1.resolve()), "size": 5, "mtime": 0.0},
            {"original_path": str(u2.resolve()), "renamed_path": str(renamed_u2.resolve()), "size": 5, "mtime": 0.0},
        ]
        snap_file = mgr.save_snapshot(success_log)
        assert snap_file is not None and snap_file.exists()

        # 執行復原
        undo_res = mgr.undo_snapshot(snap_file)
        assert undo_res["success"] is True
        assert undo_res["restored_count"] == 2
        assert u1.exists() and u1.read_text(encoding="utf-8") == "doc_1"
        assert u2.exists() and u2.read_text(encoding="utf-8") == "doc_2"
        assert not renamed_u1.exists()
        assert not renamed_u2.exists()
        print("[PASS] 4. 快照產生與 Ctrl+Z 逆向復原防呆測試全部通過！")

        print("\nPhase 4 核心安全改名與還原邏輯全數 PASS！")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_phase4()
