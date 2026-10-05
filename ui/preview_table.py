"""
KyteRename - Preview Table Model, Proxy & View (雙欄預覽、搜尋過濾、排序、正則高亮與右鍵選單)
"""
import re
import subprocess
from pathlib import Path
from typing import List, Set, Optional

from PySide6.QtCore import (
    QTimer,
    Qt, QAbstractTableModel, QModelIndex, QRect, QSortFilterProxyModel, Signal
)
from PySide6.QtGui import QColor, QBrush, QPainter, QCursor, QAction
from PySide6.QtWidgets import (
    QTableView, QHeaderView, QStyledItemDelegate, QStyleOptionViewItem,
    QMenu, QApplication
)

from rules.base_rule import FileEntry
from core.kyte_ipc import update_kyteview_preview_async

class HighlightDelegate(QStyledItemDelegate):
    """在原始檔名儲存格上動態繪製正則/搜尋命中區段的高亮標記"""
    def __init__(self, parent=None, is_dark: bool = True):
        super().__init__(parent)
        self.pattern: Optional[re.Pattern] = None
        self.is_dark_theme: bool = is_dark

    def set_pattern(self, pattern: Optional[re.Pattern]):
        self.pattern = pattern

    def set_dark_theme(self, is_dark: bool):
        self.is_dark_theme = is_dark

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

            if self.is_dark_theme:
                highlight_bg = QColor(245, 166, 35, 110)    # 琥珀金半透明底
                highlight_border = QColor(255, 195, 80, 210) # 亮金邊框
            else:
                highlight_bg = QColor(254, 240, 138, 180)    # 淺色系柔和琥珀黃底
                highlight_border = QColor(234, 179, 8, 220)  # 鮮明黃金邊框

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

    def __init__(self, parent=None, is_dark: bool = True):
        super().__init__(parent)
        self.entries: List[FileEntry] = []
        self.preview_names: List[str] = []
        self.duplicate_indices: Set[int] = set()
        self.disk_conflict_indices: Set[int] = set()
        self.is_dark_theme: bool = is_dark

    def set_dark_theme(self, is_dark: bool):
        """更新深淺色主題並即時刷新所有儲存格顏色"""
        self.is_dark_theme = is_dark
        if self.entries:
            top_left = self.index(0, 0)
            bottom_right = self.index(len(self.entries) - 1, len(self.HEADERS) - 1)
            self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.ForegroundRole, Qt.ItemDataRole.BackgroundRole])

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
                return QBrush(QColor("#FF4D4F" if self.is_dark_theme else "#DC2626"))
            if col == 1 and is_changed:
                return QBrush(QColor("#52C41A" if self.is_dark_theme else "#15803D"))
            if col == 2:
                if is_changed:
                    return QBrush(QColor("#52C41A" if self.is_dark_theme else "#15803D"))
                else:
                    return QBrush(QColor("#8C8C8C" if self.is_dark_theme else "#6B7280"))
            return QBrush(QColor("#E2E4E8" if self.is_dark_theme else "#1F2937"))

        elif role == Qt.ItemDataRole.BackgroundRole:
            if is_dup or is_disk_conflict:
                return QBrush(QColor(60, 20, 20, 180) if self.is_dark_theme else QColor(254, 226, 226, 220))
            if col == 1 and is_changed:
                return QBrush(QColor(20, 45, 25, 120) if self.is_dark_theme else QColor(220, 252, 231, 180))
            return None

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 2:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        elif role == Qt.ItemDataRole.UserRole:
            # 返回原始資料供代理模型過濾與排序
            return {
                "entry": entry,
                "new_name": new_name,
                "is_changed": is_changed,
                "is_conflict": (is_dup or is_disk_conflict),
                "row": row
            }

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
                Qt.ItemDataRole.BackgroundRole,
                Qt.ItemDataRole.UserRole
            ])


class PreviewSortFilterProxyModel(QSortFilterProxyModel):
    """支援文字關鍵字搜尋、待更名過濾、衝突項目過濾與自定義排序"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
        self.filter_mode = "all"  # "all", "changed", "conflict"

    def _refresh_filter(self):
        if hasattr(self, "invalidateRowsFilter"):
            self.invalidate()
        else:
            self.invalidateFilter()

    def set_search_text(self, text: str):
        self.search_text = (text or "").strip().lower()
        self._refresh_filter()

    def set_filter_mode(self, mode: str):
        self.filter_mode = mode
        self._refresh_filter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model: PreviewTableModel = self.sourceModel()
        if not model or source_row >= len(model.entries):
            return False

        entry = model.entries[source_row]
        new_name = model.preview_names[source_row] if source_row < len(model.preview_names) else entry.original_name
        is_changed = (new_name != entry.original_name)
        is_conflict = (source_row in model.duplicate_indices or source_row in model.disk_conflict_indices)

        # 狀態過濾
        if self.filter_mode == "changed" and not is_changed:
            return False
        if self.filter_mode == "conflict" and not is_conflict:
            return False

        # 關鍵字搜尋過濾
        if self.search_text:
            orig_match = self.search_text in entry.original_name.lower()
            new_match = self.search_text in new_name.lower()
            if not orig_match and not new_match:
                return False

        return True


class PreviewTable(QTableView):
    request_preview = Signal(Path)       # 觸發預覽 (Space 或右鍵)
    request_remove = Signal(list)        # 觸發移除 (Delete 或右鍵，傳出 source_indices: List[int])

    def __init__(self, parent=None):
        super().__init__(parent)
        from core.settings_manager import SettingsManager
        is_dark = SettingsManager().is_dark()

        self.table_model = PreviewTableModel(self, is_dark=is_dark)
        self.proxy_model = PreviewSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.table_model)
        self.setModel(self.proxy_model)

        # 支援點選標頭排序
        self.setSortingEnabled(True)

        # 綁定正則即時高亮 Delegate
        self.highlight_delegate = HighlightDelegate(self, is_dark=is_dark)
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

        # 右鍵選單配置
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # 游標行切換即時同步 KyteView (30ms Debounce 防抖，不失焦)
        self.nav_timer = QTimer(self)
        self.nav_timer.setSingleShot(True)
        self.nav_timer.setInterval(30)
        self.nav_timer.timeout.connect(self._on_nav_debounced)
        self.selectionModel().currentChanged.connect(self._on_current_changed)

    def set_search_pattern(self, pattern: Optional[re.Pattern]):
        """更新高亮 Pattern 並觸發左欄重新繪製"""
        self.highlight_delegate.set_pattern(pattern)
        self.viewport().update()

    def set_dark_theme(self, is_dark: bool):
        """即時同步主題顏色至 TableModel 與 HighlightDelegate"""
        self.table_model.set_dark_theme(is_dark)
        self.highlight_delegate.set_dark_theme(is_dark)
        self.viewport().update()

    def get_selected_source_indices(self) -> List[int]:
        """取得目前所有選中行的 source model 索引 (降序排列，方便直接刪除)"""
        selected_proxy_indexes = self.selectionModel().selectedRows()
        source_indices = []
        for p_idx in selected_proxy_indexes:
            s_idx = self.proxy_model.mapToSource(p_idx)
            if s_idx.isValid():
                source_indices.append(s_idx.row())
        return sorted(list(set(source_indices)), reverse=True)

    def get_current_target_entry(self) -> Optional[FileEntry]:
        """精確獲取當前選中或焦點所在的 FileEntry (自動處理 Proxy 與 Source 映射)"""
        indices = self.get_selected_source_indices()
        if indices and 0 <= indices[-1] < len(self.table_model.entries):
            return self.table_model.entries[indices[-1]]
        curr = self.currentIndex()
        if curr.isValid():
            s_idx = self.proxy_model.mapToSource(curr)
            if s_idx.isValid() and 0 <= s_idx.row() < len(self.table_model.entries):
                return self.table_model.entries[s_idx.row()]
        return None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            indices = self.get_selected_source_indices()
            if indices:
                self.request_remove.emit(indices)
                event.accept()
                return
        elif event.key() == Qt.Key.Key_Space:
            entry = self.get_current_target_entry()
            if entry:
                self.request_preview.emit(entry.path)
                event.accept()
                return

        super().keyPressEvent(event)

    def _show_context_menu(self, pos):
        """彈出右鍵快捷操作選單"""
        selected_indices = self.get_selected_source_indices()
        if not selected_indices:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1E2227;
                border: 1px solid #333842;
                border-radius: 6px;
                padding: 4px;
                color: #E2E4E8;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #177DDC;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #333842;
                margin: 4px 6px;
            }
        """)

        # 單選或首個項目資訊
        first_entry = self.table_model.entries[selected_indices[-1]]
        first_new_name = (
            self.table_model.preview_names[selected_indices[-1]]
            if selected_indices[-1] < len(self.table_model.preview_names)
            else first_entry.original_name
        )

        # 1. KyteView 快速預覽
        act_preview = menu.addAction("👁️ 在 KyteView 中預覽 (Space)")
        act_preview.triggered.connect(lambda: self.request_preview.emit(first_entry.path))

        # 2. 在檔案總管中顯示
        act_reveal = menu.addAction("🔍 在檔案總管中顯示")
        act_reveal.triggered.connect(lambda: self._reveal_in_explorer(first_entry.path))

        menu.addSeparator()

        # 3. 複製功能群組
        copy_menu = menu.addMenu("📋 複製資訊")
        copy_menu.setStyleSheet(menu.styleSheet())

        act_copy_orig_name = copy_menu.addAction("複製原始檔名")
        act_copy_orig_name.triggered.connect(lambda: QApplication.clipboard().setText(first_entry.original_name))

        act_copy_new_name = copy_menu.addAction("複製預覽新檔名")
        act_copy_new_name.triggered.connect(lambda: QApplication.clipboard().setText(first_new_name))

        act_copy_orig_path = copy_menu.addAction("複製原始完整路徑")
        act_copy_orig_path.triggered.connect(lambda: QApplication.clipboard().setText(str(first_entry.path.resolve())))

        new_full_path = str((first_entry.parent_dir / first_new_name).resolve())
        act_copy_new_path = copy_menu.addAction("複製預覽新完整路徑")
        act_copy_new_path.triggered.connect(lambda: QApplication.clipboard().setText(new_full_path))

        menu.addSeparator()

        # 4. 從列表移除
        remove_text = f"❌ 從列表移除 ({len(selected_indices)} 個項目) [Delete]" if len(selected_indices) > 1 else "❌ 從列表移除 [Delete]"
        act_remove = menu.addAction(remove_text)
        act_remove.triggered.connect(lambda: self.request_remove.emit(selected_indices))

        # 5. 全選
        act_select_all = menu.addAction("🔄 全選 (Ctrl+A)")
        act_select_all.triggered.connect(self.selectAll)

        menu.exec(QCursor.pos())

    def _on_current_changed(self, current, previous):
        if current.isValid():
            self.nav_timer.start()

    def _on_nav_debounced(self):
        entry = self.get_current_target_entry()
        if entry:
            update_kyteview_preview_async(entry.path)

    @staticmethod
    def _reveal_in_explorer(file_path: Path):
        """呼叫 Windows Explorer 亮顯指定檔案"""
        try:
            p_str = str(file_path.resolve())
            if file_path.exists():
                subprocess.Popen(f'explorer.exe /select,"{p_str}"')
            else:
                parent_str = str(file_path.parent.resolve())
                subprocess.Popen(f'explorer.exe "{parent_str}"')
        except Exception:
            pass
