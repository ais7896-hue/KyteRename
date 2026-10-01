"""
KyteRename - Preview Table Model & View (QTableView 虛擬化雙欄預覽)
"""
from typing import List, Set
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import QTableView, QHeaderView
from rules.base_rule import FileEntry

class PreviewTableModel(QAbstractTableModel):
    HEADERS = ["原始檔名", "新檔名預覽", "狀態"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries: List[FileEntry] = []
        self.preview_names: List[str] = []
        self.duplicate_indices: Set[int] = set()
        self.disk_conflict_indices: Set[int] = set()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.entries)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self.entries):
            return None

        entry = self.entries[row]
        new_name = self.preview_names[row] if row < len(self.preview_names) else entry.original_name
        is_dup = row in self.duplicate_indices
        is_disk_conflict = row in self.disk_conflict_indices
        is_changed = (new_name != entry.original_name)

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return entry.original_name
            elif col == 1:
                return new_name
            elif col == 2:
                if is_dup:
                    return "⚠️ 名稱重複"
                if is_disk_conflict:
                    return "⚠️ 檔案已存在"
                if is_changed:
                    return "✓ 待更名"
                return "無變更"

        elif role == Qt.ItemDataRole.ForegroundRole:
            if is_dup or is_disk_conflict:
                return QBrush(QColor("#FF4D4F")) # 紅色衝突警告
            if col == 1 and is_changed:
                return QBrush(QColor("#52C41A")) # 綠色變更提示
            if col == 2:
                return QBrush(QColor("#52C41A") if is_changed else QColor("#8C8C8C"))
            return QBrush(QColor("#D9D9D9"))

        elif role == Qt.ItemDataRole.BackgroundRole:
            if is_dup or is_disk_conflict:
                return QBrush(QColor(60, 20, 20, 180)) # 淡淡的紅色半透明底色
            if col == 1 and is_changed:
                return QBrush(QColor(20, 45, 25, 120)) # 淡淡的綠色半透明底色
            return None

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 2:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        return None

    def update_data(
        self,
        entries: List[FileEntry],
        preview_names: List[str],
        duplicates: Set[int],
        disk_conflicts: Set[int]
    ):
        self.beginResetModel()
        self.entries = entries
        self.preview_names = preview_names
        self.duplicate_indices = duplicates
        self.disk_conflict_indices = disk_conflicts
        self.endResetModel()

    def update_previews(self, preview_names: List[str], duplicates: Set[int], disk_conflicts: Set[int]):
        """僅更新預覽名稱與狀態，避免重構整個列表"""
        self.preview_names = preview_names
        self.duplicate_indices = duplicates
        self.disk_conflict_indices = disk_conflicts
        if self.entries:
            top_left = self.index(0, 1)
            bottom_right = self.index(len(self.entries) - 1, 2)
            self.dataChanged.emit(top_left, bottom_right, [
                Qt.ItemDataRole.DisplayRole,
                Qt.ItemDataRole.ForegroundRole,
                Qt.ItemDataRole.BackgroundRole
            ])

class PreviewTable(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_model = PreviewTableModel(self)
        self.setModel(self.table_model)

        self.setShowGrid(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)

        # 欄位寬度自動延展
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(2, 110)

        # 垂直表頭自定義
        self.verticalHeader().setDefaultSectionSize(30)
        self.verticalHeader().setVisible(False)
