"""
KyteRename - File Scanner (高效目錄掃描器)
"""
import os
from pathlib import Path
from typing import List, Optional
from rules.base_rule import FileEntry

def scan_path(
    target_path: str,
    recursive: bool = False,
    ext_filter: Optional[List[str]] = None
) -> List[FileEntry]:
    """
    掃描目標路徑（可為單一資料夾或複數檔案），回傳 FileEntry 列表
    使用 os.scandir 以獲得最佳 I/O 效能
    """
    results: List[FileEntry] = []
    p = Path(target_path)

    if not p.exists():
        return results

    # 若傳入為單檔
    if p.is_file():
        ext = p.suffix
        if ext_filter and ext.lower() not in [e.lower() for e in ext_filter]:
            return results
        stat = p.stat()
        results.append(FileEntry(
            path=p,
            original_base=p.stem,
            extension=ext,
            size_bytes=stat.st_size,
            mtime=stat.st_mtime
        ))
        return results

    # 若傳入為目錄
    filter_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in ext_filter} if ext_filter else None

    def _scan_dir(dir_path: str):
        try:
            with os.scandir(dir_path) as it:
                for entry in it:
                    if entry.is_file(follow_symlinks=False):
                        ext = os.path.splitext(entry.name)[1]
                        if filter_set and ext.lower() not in filter_set:
                            continue
                        try:
                            stat = entry.stat()
                            results.append(FileEntry(
                                path=Path(entry.path),
                                original_base=os.path.splitext(entry.name)[0],
                                extension=ext,
                                size_bytes=stat.st_size,
                                mtime=stat.st_mtime
                            ))
                        except (PermissionError, FileNotFoundError):
                            continue
                    elif recursive and entry.is_dir(follow_symlinks=False):
                        _scan_dir(entry.path)
        except (PermissionError, FileNotFoundError):
            pass

    _scan_dir(str(p))
    # 預設按原始名稱排序
    results.sort(key=lambda x: x.original_name.lower())
    return results
