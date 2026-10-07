"""
KyteRename - Snapshot Manager (快照日誌儲存與 Ctrl+Z 逆向拓撲無痛復原)
"""
import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from .rename_executor import resolve_rename_order, rename_safe

class SnapshotManager:
    def __init__(self, snapshot_dir: Optional[Path] = None):
        if snapshot_dir is None:
            # 預設儲存在使用者主目錄下的 .kyte_rename/snapshots
            self.snapshot_dir = Path.home() / ".kyte_rename" / "snapshots"
        else:
            self.snapshot_dir = Path(snapshot_dir)

        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.max_snapshots = 15

    def save_snapshot(self, success_ops: List[Dict[str, Any]]) -> Optional[Path]:
        """將成功改名的操作清單存為 JSON 快照"""
        if not success_ops:
            return None

        now = datetime.datetime.now()
        filename = f"snapshot_{now.strftime('%Y%m%d_%H%M%S_%f')}.json"
        snapshot_path = self.snapshot_dir / filename

        data = {
            "timestamp": now.isoformat(),
            "count": len(success_ops),
            "operations": success_ops
        }

        try:
            snapshot_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            self._cleanup_old_snapshots()
            return snapshot_path
        except Exception:
            return None

    def get_latest_snapshot(self) -> Optional[Path]:
        """取得最新的快照檔案路徑"""
        snapshots = sorted(self.snapshot_dir.glob("snapshot_*.json"), key=os.path.getmtime, reverse=True)
        return snapshots[0] if snapshots else None

    def undo_snapshot(self, snapshot_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        執行復原改名操作：
        讀取快照中的 renamed_path -> original_path，
        並再次實施「逆向拓撲排序」後執行 rename_safe，安全復原至原狀態。
        """
        if snapshot_path is None:
            snapshot_path = self.get_latest_snapshot()

        if not snapshot_path or not snapshot_path.exists():
            return {"success": False, "error_code": "no_snapshot", "snapshot_exists": False, "message": "無可用的復原快照記錄"}

        try:
            data = json.loads(snapshot_path.read_text(encoding="utf-8"))
            operations = data.get("operations", [])
        except Exception as e:
            return {"success": False, "error_code": "read_failed", "error": str(e), "message": f"快照檔案讀取失敗: {e}"}

        # 構建逆向操作：從 renamed_path 還原回 original_path
        reverse_pairs: List[Tuple[Path, Path]] = []
        for op in operations:
            renamed = Path(op["renamed_path"])
            original = Path(op["original_path"])
            reverse_pairs.append((renamed, original))

        # 逆向拓撲排序
        ordered_ops = resolve_rename_order(reverse_pairs)

        restored_count = 0
        failed_ops = []

        for src, dst in ordered_ops:
            if not src.exists():
                failed_ops.append({
                    "file": str(src),
                    "reason": "檔案已被移動或刪除"
                })
                continue

            try:
                rename_safe(src, dst)
                restored_count += 1
            except Exception as e:
                failed_ops.append({
                    "file": str(src),
                    "reason": str(e)
                })

        # 復原完成後，刪除或標記該快照，避免重複復原
        try:
            snapshot_path.unlink(missing_ok=True)
        except Exception:
            pass

        return {
            "success": True,
            "restored_count": restored_count,
            "failed_count": len(failed_ops),
            "failed_details": failed_ops,
            "message": f"成功還原 {restored_count} 個檔案"
        }

    def _cleanup_old_snapshots(self):
        """保留最近 15 筆快照，多餘的自動刪除"""
        snapshots = sorted(self.snapshot_dir.glob("snapshot_*.json"), key=os.path.getmtime, reverse=True)
        for s in snapshots[self.max_snapshots:]:
            try:
                s.unlink(missing_ok=True)
            except Exception:
                pass
