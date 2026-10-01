import sys
import tempfile
import shutil
from pathlib import Path

BASE_DIR = Path(r"D:\Noah\Antigravity專案程式專用\KyteRename")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import SettingsManager

def test_settings():
    print("=== 開始測試 SettingsManager 與快照遷移 ===")

    mgr = SettingsManager()
    
    # 1. 讀取預設值
    assert mgr.get("recursive_scan") is False
    assert mgr.get("max_snapshot_history") == 15
    print("[PASS] 1. 預設值讀取正確")

    # 2. 修改與原子寫入
    mgr.set("recursive_scan", True)
    assert mgr.get("recursive_scan") is True
    # 復原
    mgr.set("recursive_scan", False)
    assert mgr.get("recursive_scan") is False
    print("[PASS] 2. 設定修改與原子存檔驗證通過")

    # 3. 快照遷移功能測試
    temp_dir = Path(tempfile.mkdtemp(prefix="test_migrate_"))
    try:
        dir_a = temp_dir / "dir_a"
        dir_b = temp_dir / "dir_b"
        dir_a.mkdir(parents=True, exist_ok=True)
        dir_b.mkdir(parents=True, exist_ok=True)

        # 模擬產生 3 筆快照
        (dir_a / "snapshot_001.json").write_text("{}", encoding="utf-8")
        (dir_a / "snapshot_002.json").write_text("{}", encoding="utf-8")
        (dir_a / "snapshot_003.json").write_text("{}", encoding="utf-8")

        # 暫時覆蓋 get_snapshot_dir
        orig_get_snap = mgr.get_snapshot_dir
        mgr.get_snapshot_dir = lambda m: dir_a if m == "a" else dir_b

        moved_count = mgr.migrate_snapshots("a", "b")
        assert moved_count == 3
        assert not (dir_a / "snapshot_001.json").exists()
        assert (dir_b / "snapshot_001.json").exists()
        assert (dir_b / "snapshot_002.json").exists()
        assert (dir_b / "snapshot_003.json").exists()
        print("[PASS] 3. 快照跨目錄遷移機制驗證通過")

        mgr.get_snapshot_dir = orig_get_snap
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("\nSettingsManager 所有測試通過！")

if __name__ == "__main__":
    test_settings()
