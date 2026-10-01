"""
KyteRename - Metadata Worker (背景漸進式非同步讀取執行緒)
"""
from typing import List, Tuple, Dict, Any
from PySide6.QtCore import QThread, Signal
from rules.base_rule import FileEntry
from core.metadata_reader import read_file_metadata

class MetadataWorker(QThread):
    # 發送批次更新信號: List[Tuple[row_index, metadata_dict]]
    batch_ready = Signal(list)
    finished_all = Signal()

    def __init__(self, entries: List[FileEntry], parent=None):
        super().__init__(parent)
        self.entries = entries
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        batch = []
        for idx, entry in enumerate(self.entries):
            if self._is_cancelled:
                break
            if not entry.is_meta_loaded:
                try:
                    meta = read_file_metadata(entry.path)
                    batch.append((idx, meta))
                except Exception:
                    batch.append((idx, {}))

            if len(batch) >= 25:
                self.batch_ready.emit(batch)
                batch = []

        if batch and not self._is_cancelled:
            self.batch_ready.emit(batch)

        if not self._is_cancelled:
            self.finished_all.emit()
