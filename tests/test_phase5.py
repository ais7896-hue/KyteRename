"""
KyteRename - Phase 5 Unit Tests (搜尋過濾代理模型、衝突解決策略、右鍵與批次刪除)
"""
import sys
import unittest
from pathlib import Path

# 將專案根目錄加入路徑
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication
from rules.base_rule import FileEntry
from core.rule_engine import RuleEngine
from ui.preview_table import PreviewTableModel, PreviewSortFilterProxyModel

app = QApplication.instance() or QApplication(["-platform", "offscreen"])

class TestPhase5(unittest.TestCase):
    def setUp(self):
        self.entries = [
            FileEntry(Path("C:/test/file_alpha.jpg"), "file_alpha", ".jpg"),
            FileEntry(Path("C:/test/file_beta.png"), "file_beta", ".png"),
            FileEntry(Path("C:/test/file_gamma.txt"), "file_gamma", ".txt"),
            FileEntry(Path("C:/test/file_delta.txt"), "file_delta", ".txt"),
        ]

    def test_conflict_policies(self):
        """測試衝突處理策略: ask, skip, suffix"""
        raw_previews = ["photo.jpg", "photo.jpg", "file_gamma.txt", "doc.txt"]

        # 1. 預設 'ask': 保留衝突
        names_ask, dups_ask, disk_ask = RuleEngine.apply_conflict_policy(
            self.entries, raw_previews, policy="ask"
        )
        self.assertEqual(names_ask[0], "photo.jpg")
        self.assertEqual(names_ask[1], "photo.jpg")
        self.assertEqual(dups_ask, {0, 1})

        # 2. 'skip': 衝突項目還原成原名
        names_skip, dups_skip, disk_skip = RuleEngine.apply_conflict_policy(
            self.entries, raw_previews, policy="skip"
        )
        self.assertEqual(names_skip[0], "file_alpha.jpg")
        self.assertEqual(names_skip[1], "file_beta.png")
        self.assertEqual(dups_skip, set())

        # 3. 'suffix': 自動增補 _1, _2 後綴消解衝突
        names_suffix, dups_suffix, disk_suffix = RuleEngine.apply_conflict_policy(
            self.entries, raw_previews, policy="suffix"
        )
        self.assertEqual(names_suffix[0], "photo.jpg")
        self.assertEqual(names_suffix[1], "photo_1.jpg")
        self.assertEqual(dups_suffix, set())
        self.assertEqual(disk_suffix, set())

    def test_proxy_search_and_filter(self):
        """測試 ProxyModel 即時搜尋與狀態篩選"""
        model = PreviewTableModel()
        proxy = PreviewSortFilterProxyModel()
        proxy.setSourceModel(model)

        previews = ["photo_alpha.jpg", "file_beta.png", "doc_gamma.txt", "file_delta.txt"]
        duplicates = {2}
        disk_conflicts = set()

        model.update_data(self.entries, previews, duplicates, disk_conflicts)
        self.assertEqual(proxy.rowCount(), 4)

        # 關鍵字搜尋 "alpha"
        proxy.set_search_text("alpha")
        self.assertEqual(proxy.rowCount(), 1)

        # 清除搜尋
        proxy.set_search_text("")
        self.assertEqual(proxy.rowCount(), 4)

        # 篩選僅看待更名
        proxy.set_filter_mode("changed")
        self.assertEqual(proxy.rowCount(), 2)

        # 篩選僅看衝突
        proxy.set_filter_mode("conflict")
        self.assertEqual(proxy.rowCount(), 1)

        # 重置為全部
        proxy.set_filter_mode("all")
        self.assertEqual(proxy.rowCount(), 4)

    def test_batch_remove_by_indices(self):
        """測試依降序索引安全批次刪除"""
        entries = list(self.entries)
        indices_to_remove = [3, 1]
        for idx in indices_to_remove:
            del entries[idx]

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].original_base, "file_alpha")
        self.assertEqual(entries[1].original_base, "file_gamma")

if __name__ == "__main__":
    unittest.main()
