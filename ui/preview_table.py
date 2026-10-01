"""
KyteRename - Preview Table Model & View (QTableView 雙欄預覽與正則匹配即時高亮 Delegate)
"""
import re
from typing import List, Set, Optional
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QRect
from PySide6.QtGui import QColor, QBrush, QPainter
from PySide6.QtWidgets import QTableView, QHeaderView, QStyledItemDelegate, QStyleOptionViewItem
from rules.base_rule import FileEntry

class HighlightDelegate(QStyledItemDelegate):
    """在原始檔名儲存格上動態繪製正則/搜尋命中區段的高亮標記"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern: Optional[re.Pattern] = None

    def set_pattern(self, pattern: Optional[re.Pattern]):
        self.pattern = pattern

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        super().paint(painter, option, index)

        # 僅在第 0 欄 (原檔名) 且有有效搜尋字串時繪製命中底色
        if index.column() == 0 and self.pattern:
            text = index.data(Qt.ItemDataRole.DisplayRole)
            if not text:
                return

            try:
                matches = list(self.pattern.finditer(text))
            except Exception:
                matches = []

            if not matches:
                return

            painter.save()
            fm = option.fontMetrics
            rect = option.rect
            base_x = rect.left() + 6
            y = rect.top() + 4
            h = rect.height() - 8

            highlight_bg = QColor(245, 166, 35, 110)    # 琥珀金半透明底
            highlight_border = QColor(255, 195, 80, 210) # 亮金邊框

            for m in matches:
                start_idx, end_idx = m.start(), m.end()
                if start_idx == end_idx:
                    continue

                pre_text = text[:start_idx]
                match_text = text[start_idx:end_idx]

                x_offset = fm.horizontalAdvance(pre_text)
                match_w = fm.horizontalAdvance(match_text)

                hl_rect = QRect(base_x + x_offset, y, match_w, h)
                painter.setBrush(highlight_bg)
                painter.setPen(highlight_border)
                painter.drawRoundedRect(hl_rect, 3, 3)

            painter.restore()

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
                return QBrush(QColor("#FF4D4F"))
            if col == 1 and is_changed:
                return QBrush(QColor("#52C41A"))
            if col == 2:
                return QBrush(QColor("#52C41A") if is_changed else QColor("#8C8C8C"))
            return QBrush(QColor("#D9D9D9"))

        elif role == Qt.ItemDataRole.BackgroundRole:
            if is_dup or is_disk_conflict:
                return QBrush(QColor(60, 20, 20, 180))
            if col == 1 and is_changed:
                return QBrush(QColor(20, 45, 25, 120))
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

        # 綁定正則即時高亮 Delegate
        self.highlight_delegate = HighlightDelegate(self)
        self.setItemDelegateForColumn(0, self.highlight_delegate)

        self.setShowGrid(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(2, 110)

        self.verticalHeader().setDefaultSectionSize(30)
        self.verticalHeader().setVisible(False)

    def set_search_pattern(self, pattern: Optional[re.Pattern]):
        """更新高亮 Pattern 並觸發左欄重新繪製"""
        self.highlight_delegate.set_pattern(pattern)
        self.viewport().update()
