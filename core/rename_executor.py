"""
KyteRename - Rename Executor (具備拓撲排序、長路徑與大小寫隔離的安全批次改名執行器)
"""
import os
import uuid
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from PySide6.QtCore import QThread, Signal
from rules.base_rule import FileEntry

def to_extended_path(p: Path | str) -> str:
    """轉換為 Windows Extended-Length Path (\\?\) 前綴，徹底免疫 260 字元 MAX_PATH 限制"""
    abs_p = str(Path(p).resolve())
    if abs_p.startswith("\\\\?\\"):
        return abs_p
    return f"\\\\?\\{abs_p}"

def rename_safe(src: Path, dst: Path):
    """
    安全更名處理：
    1. 支援 Windows 超長路徑
    2. 兩階段處理 Windows NTFS 大小寫不敏感更名 (如 test.jpg -> test.JPG)
    """
    src_str = to_extended_path(src)
    dst_str = to_extended_path(dst)

    # 判斷是否為同目錄且僅大小寫變更
    if os.path.normcase(src_str) == os.path.normcase(dst_str) and src_str != dst_str:
        tmp_str = f"{src_str}.kyte_{uuid.uuid4().hex[:6]}.tmp"
        os.rename(src_str, tmp_str)
        os.rename(tmp_str, dst_str)
    else:
        os.rename(src_str, dst_str)

def resolve_rename_order(ops: List[Tuple[Path, Path]]) -> List[Tuple[Path, Path]]:
    """
    拓撲排序消除連鎖覆蓋 (例如 file1 -> file2, file2 -> file3):
    優先執行目標不存在於待執行來源中的操作 (葉節點逆序推進)。
    僅在發生真循環依賴 (Cycle, 如 A->B 且 B->A) 時，對單一節點使用臨時暫存檔破圈。
    """
    if not ops:
        return []

    # 建立以 normcase 為鍵的映射
    norm_to_pair: Dict[str, Tuple[Path, Path]] = {}
    for src, dst in ops:
        norm_to_pair[os.path.normcase(str(src.resolve()))] = (src, dst)

    src_set = set(norm_to_pair.keys())
    dst_set = {os.path.normcase(str(dst.resolve())) for _, dst in ops}

    # 若無任何連鎖重疊，直接按原順序執行
    if not (src_set & dst_set):
        return ops

    ordered: List[Tuple[Path, Path]] = []
    pending = dict(norm_to_pair)

    while pending:
        # 找出當前 dst 不存在於剩餘 pending 來源的操作 (無衝撞風險)
        ready_keys = [
            k for k, (src, dst) in pending.items()
            if os.path.normcase(str(dst.resolve())) not in pending
        ]

        if ready_keys:
            for k in ready_keys:
                ordered.append(pending.pop(k))
        else:
            # 發生真循環依賴 (Cycle)，抓出第一個節點產生臨時檔破圈
            cycle_key, (src, dst) = next(iter(pending.items()))
            tmp_path = src.parent / f"{src.name}.kyte_{uuid.uuid4().hex[:6]}.tmp"
            # 1. 先將 src 改為 tmp
            ordered.append((src, tmp_path))
            # 2. 將 tmp 排入 pending 待改為 dst
            del pending[cycle_key]
            pending[os.path.normcase(str(tmp_path.resolve()))] = (tmp_path, dst)

    return ordered

class RenameWorker(QThread):
    progress = Signal(int, int, str) # current, total, current_filename
    finished_batch = Signal(dict)    # 包含 success, failed 統計與操作明細

    def __init__(self, operations: List[Tuple[Path, Path]], parent=None):
        super().__init__(parent)
        self.operations = operations
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        # 1. 執行拓撲防撞排序
        ordered_ops = resolve_rename_order(self.operations)
        total = len(ordered_ops)

        success_ops: List[Dict[str, Any]] = []
        failed_ops: List[Dict[str, Any]] = []

        for idx, (src, dst) in enumerate(ordered_ops):
            if self._is_cancelled:
                break

            self.progress.emit(idx + 1, total, src.name)

            try:
                # 記錄改名前檔案狀態（供快照還原使用）
                stat = src.stat() if src.exists() else None
                mtime = stat.st_mtime if stat else 0.0
                size = stat.st_size if stat else 0

                rename_safe(src, dst)

                success_ops.append({
                    "original_path": str(src.resolve()),
                    "renamed_path": str(dst.resolve()),
                    "size": size,
                    "mtime": mtime
                })
            except PermissionError as e:
                failed_ops.append({
                    "src": str(src),
                    "dst": str(dst),
                    "reason": "檔案被其他程式鎖定或權限不足",
                    "detail": str(e)
                })
            except Exception as e:
                failed_ops.append({
                    "src": str(src),
                    "dst": str(dst),
                    "reason": type(e).__name__,
                    "detail": str(e)
                })

        self.finished_batch.emit({
            "total": total,
            "success_count": len(success_ops),
            "failed_count": len(failed_ops),
            "success_ops": success_ops,
            "failed_ops": failed_ops,
            "is_cancelled": self._is_cancelled
        })
