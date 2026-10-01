# KyteRename — 規則式即時預覽批次重新命名工具 計劃書

## 專案定位

PowerToys Bulk Rename 的精緻替代品：拖入資料夾 → 左欄原名 / 右欄即時預覽新名稱，1 秒批次處理千個檔案，支援 EXIF 元資料變數、正則表達式、復原快照。

**核心效能目標：1000 個檔案預覽更新 < 100ms，改名操作不阻塞 UI（子執行緒執行），復原 < 500ms。**

---

## 技術選型

| 層級 | 技術 | 理由 |
|------|------|------|
| GUI 框架 | **PySide6** | 高效能原生渲染，QTableView 虛擬化支援 |
| EXIF 讀取 | **Pillow (PIL)** | 內建 `_getexif()`，JPEG/TIFF EXIF；已是專案依賴 |
| ID3/媒體標籤 | **mutagen** | 支援 MP3/FLAC/OGG/M4A/AIFF 等全格式 ID3+Vorbis Comment，輕量無需 FFmpeg |
| 中繼資料補強 | **`os.stat`** | 讀取建立日期、修改日期，純內建 |
| 拼音轉換 | **pypinyin** | 中文轉拼音（可選功能），純 Python 實作，打包 +2MB |
| 正則 | Python 內建 `re` | 零依賴 |
| 跨進程通訊 | **標準庫 `multiprocessing.connection` (AF_PIPE)** | 原生 Windows Named Pipe，零依賴免 pywin32，高穩定度 |
| 打包 | **PyInstaller** + Inno Setup | 與 KyteView / KyteShelf 一致 |

---

## 架構設計

```
KyteRename/
├── main.py                     # 入口：啟動主視窗
├── core/
│   ├── file_scanner.py         # 遞迴掃描資料夾，回傳 List[FileEntry]
│   ├── rule_engine.py          # 規則計算引擎：輸入舊名+元資料 → 新名稱
│   ├── metadata_reader.py      # 非同步讀取 EXIF / ID3 / 系統中繼資料
│   ├── rename_executor.py      # 執行批次改名（子執行緒，拓撲排序與安全過渡）
│   ├── snapshot_manager.py     # 快照管理：儲存/載入 undo 日誌，支援逆向拓撲還原
│   └── kyte_ipc.py             # 原生 Named Pipe 跨進程伺服器/用戶端（與 KyteView 聯動）
├── ui/
│   ├── main_window.py          # 主視窗：雙欄預覽 + 規則面板
│   ├── rule_panel.py           # 規則設定面板（各 Rule Widget）
│   ├── preview_table.py        # QTableView 雙欄（原名/新名，虛擬化，正則高亮 Delegate）
│   ├── template_picker.py      # 快捷模板選取器（下拉或 Sidebar）
│   ├── conflict_dialog.py      # 命名衝突/覆蓋確認對話框
│   └── undo_history_dialog.py  # 復原歷程查詢視窗
├── rules/
│   ├── base_rule.py            # 抽象 Rule 介面：apply(name, ctx, scope) -> new_name
│   ├── replace_rule.py         # 字串取代（含正則模式與高亮匹配）
│   ├── prefix_suffix_rule.py   # 前後綴增刪
│   ├── serial_rule.py          # 流水號填補（001, 002...，可自訂起始/步長/位數）
│   ├── case_rule.py            # 大小寫轉換（全大/全小/首字大寫）
│   ├── metadata_rule.py        # 中繼資料變數展開（{date}, {width}, {artist}...）
│   ├── sanitize_rule.py        # 去除特殊符號、非法字元
│   ├── pinyin_rule.py          # 中文轉拼音（可選）
│   └── trim_rule.py            # 去除多餘空格/頭尾空白
├── templates/
│   └── presets.json            # 預設模板定義（JSON，可由使用者新增）
├── config/
│   └── settings.py             # 使用者設定（主題、預設排序、歷程保留數量）
├── tests/
│   └── test_rule_engine.py
└── requirements.txt
```

---

## 核心資料流

```
使用者拖入資料夾
    ↓
file_scanner.py → List[FileEntry(path, ext, metadata)]
    ↓
metadata_reader.py 背景執行緒批次預讀元資料（每完成一批發送 Qt Signal）
    ↓
rule_engine.py: 對每個 FileEntry 應用 Rule 鏈（支援 Scope：主檔名/副檔名/全檔名）
    → apply_chain([Rule1, Rule2, ...], entry) → new_name
    ↓
preview_table.py 虛擬化呈現（QAbstractTableModel.dataChanged + Regex Delegate 高亮）
    ↓
使用者確認 → rename_executor.py（QThread）
    → resolve_rename_order 拓撲破圈排序 → rename_safe 安全改名
    → 產生 snapshot_YYYYMMDD_HHMMSS.json
    ↓
Ctrl+Z → snapshot_manager.py 逆向拓撲安全還原
```

---

## 規則引擎與作用域設計

```python
from enum import Enum
from pathlib import Path

class TargetScope(Enum):
    BASE_ONLY = "base_only"      # 僅主檔名（預設）
    EXT_ONLY = "ext_only"        # 僅副檔名（例如統一 .JPG -> .jpg）
    FULL_NAME = "full_name"      # 完整檔名（含副檔名）

class FileEntry:
    path: Path
    original_base: str       # 不含副檔名
    extension: str           # 如 .jpg
    metadata: dict           # EXIF/ID3/系統 metadata
    is_meta_loaded: bool = False

class BaseRule:
    def __init__(self, scope: TargetScope = TargetScope.BASE_ONLY):
        self.scope = scope

    def apply(self, name: str, ctx: FileEntry) -> str:
        raise NotImplementedError

class RuleEngine:
    def __init__(self, rules: list[BaseRule]):
        self.rules = rules

    def preview(self, entry: FileEntry) -> str:
        base = entry.original_base
        ext = entry.extension

        for rule in self.rules:
            if rule.scope == TargetScope.BASE_ONLY:
                base = rule.apply(base, entry)
            elif rule.scope == TargetScope.EXT_ONLY:
                ext = rule.apply(ext, entry)
            elif rule.scope == TargetScope.FULL_NAME:
                full = rule.apply(f"{base}{ext}", entry)
                p = Path(full)
                base, ext = p.stem, p.suffix

        return f"{base}{ext}"

    def preview_all(self, entries: list[FileEntry]) -> list[str]:
        return [self.preview(e) for e in entries]
```

---

## 中繼資料變數系統

| 變數 | 說明 | 範例輸出 | 未載入完成時預設 |
|------|------|---------|------------------|
| `{date}` | 建立日期 YYYYMMDD | `20261001` | 即時由 stat 取得 |
| `{datetime}` | 建立日期時間 | `20261001_143000` | 即時由 stat 取得 |
| `{exif_date}` | EXIF 拍攝日期（相機時間） | `20260815` | `[讀取中...]` |
| `{width}` | 圖片寬度（px） | `1920` | `[讀取中...]` |
| `{height}` | 圖片高度（px） | `1080` | `[讀取中...]` |
| `{resolution}` | 解析度簡寫 | `1080p` / `4K` | `[讀取中...]` |
| `{artist}` | MP3 ID3 演出者 | `Taylor_Swift` | `[讀取中...]` |
| `{album}` | MP3 ID3 專輯 | `Midnights` | `[讀取中...]` |
| `{track}` | ID3 音軌號 | `03` | `[讀取中...]` |
| `{year}` | ID3 年份 / EXIF 年份 | `2026` | `[讀取中...]` |
| `{ext}` | 原副檔名（不含點） | `jpg` | 即時取得 |
| `{n}` | 流水號（受 SerialRule 控制） | `001` | 即時計算 |
| `{parent}` | 上層資料夾名 | `vacation` | 即時取得 |

---

## 分階段開發計劃

### Phase 1 — 骨架 + 雙欄預覽（2天）

**目標：拖入資料夾，左右欄即時顯示檔名，支援虛擬化與平滑滾動**

- [ ] 主視窗 **QTableView**（欄 0 = 原名，欄 1 = 新名），支援拖曳資料夾，共用滾軸與 QAbstractTableModel 虛擬化
- [ ] `file_scanner.py`：使用 `os.scandir` 高效掃描，支援篩選副檔名與排序
- [ ] 基礎 `RuleEngine`：Pipeline 架構，支援 TargetScope（主檔名/副檔名/全檔名）
- [ ] `replace_rule.py`：字串搜尋取代（含大小寫敏感開關）
- [ ] `prefix_suffix_rule.py`：前綴/後綴新增或刪除
- [ ] 預覽右欄即時更新：100ms Debounce 避免高頻計算卡頓
- [ ] 衝突偵測：若新名稱重複 → 右欄即時以紅色高亮標示

---

### Phase 2 — 中繼資料變數 + 漸進式預覽 + 流水號（2天）

**目標：支援動態變數、背景執行緒池漸進式回呼、補零流水號**

- [ ] `metadata_reader.py`：
  - Pillow 讀取 JPEG/TIFF EXIF（拍攝時間、解析度）
  - `mutagen` 讀取 MP3/FLAC ID3（演出者、專輯、音軌號、年份）
  - `os.stat()` 即時讀取建立/修改時間
  - 背景批次回傳（每 50 筆觸發 Qt Signal），Model 僅刷新局部 rows
- [ ] `metadata_rule.py`：變數展開器，未讀取完顯示 `[讀取中...]`，讀取失敗優雅 Fallback
- [ ] `serial_rule.py`：流水號，可設定起始值、步長、補零位數與排序依據
- [ ] `trim_rule.py`：去除多餘空格
- [ ] `case_rule.py`：大寫/小寫/首字母大寫

---

### Phase 3 — 正則表達式 + 匹配高亮 + 特殊處理（2天）

- [ ] `replace_rule.py` 擴充：正則模式取代（`re.sub`），支援群組引用 `\1`
- [ ] **正則匹配即時高亮（Delegate）**：左欄原檔名由 `QStyledItemDelegate` 動態繪製黃色高亮背景，匹配結果一目了然
- [ ] `sanitize_rule.py`：
  - 去除 Windows 非法字元（`\/:*?"<>|`）
  - 去除不可見字元、特殊符號
  - 多空格壓縮為單空格
- [ ] `pinyin_rule.py`（可選）：中文字元 → 拼音（pypinyin）
- [ ] 規則面板支援拖曳調整 Rule 套用順序

---

### Phase 4 — 預設模板 + 安全批次改名與逆向復原防呆（2天）

**核心安全防護機制**

- [ ] `templates/presets.json`：相機照片、音樂整理、去除特殊符號、流水號編號、副檔名統一小寫等預設模板
- [ ] `template_picker.py`：模板選取 Sidebar
- [ ] **改名執行器 (`rename_executor.py`)**：
  - Windows Extended-Length Path (`\\?\`) 保護超長路徑
  - `resolve_rename_order()` 拓撲逆序解連鎖依賴，極小化暫存檔
  - `rename_safe()` 兩階段解決 NTFS 大小寫不敏感衝突
  - 單檔 try/except 保護，鎖定檔案跳過並標黃，不中斷整批
- [ ] **復原防呆 (`snapshot_manager.py`)**：
  - 快照記錄：舊路徑、新路徑、檔案大小、修改時間戳記
  - Ctrl+Z 還原：執行 Pre-flight 檢查，並對還原操作實施**逆向拓撲排序**，防止還原時再次發生連鎖覆蓋
  - 保留最近 10 次快照歷史

---

### Phase 5 — UX 打磨 + 原生 Named Pipe 跨進程生態（1-2天）

- [ ] 搜尋列：即時過濾左欄檔案
- [ ] 作用域切換器（UI Radio：僅主檔名 / 僅副檔名 / 全部）
- [ ] 改名進度對話框（QProgressDialog），支援中途取消
- [ ] 深色/淺色主題切換（與 KyteView / KyteShelf 一致）
- [ ] **KyteView × KyteRename 原生 IPC 聯動**：
  - 採用 Python 標準庫 `multiprocessing.connection` 原生 Named Pipe
  - KyteRename 選中檔案按 Space → 調用 KyteView 快速預覽
  - KyteView 右鍵選單 →「使用 KyteRename 批次整理」喚起並導入目錄

---

### Phase 6 — 打包與分發（1天）

- [ ] PyInstaller 打包 `.exe`
- [ ] Inno Setup 製作安裝程式
- [ ] 官網頁面與購買授權對接

---

## 關鍵演算法實作細節

### 1. 拓撲排序消除連鎖碰撞（DAG + 最小破圈）

```python
import os, uuid

def resolve_rename_order(ops: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    解決 file1 -> file2, file2 -> file3 連鎖覆蓋。
    以拓撲排序將葉節點優先改名；僅在真循環（A->B, B->A）時使用最小暫存檔破圈。
    """
    mapping = dict(ops)
    src_set = set(mapping.keys())
    dst_set = set(mapping.values())
    
    if not (src_set & dst_set):
        return ops

    ordered = []
    pending = dict(ops)
    
    while pending:
        # 找出目標不會衝撞任何未執行 src 的操作
        ready = [src for src, dst in pending.items() if dst not in pending]
        if ready:
            for src in ready:
                ordered.append((src, pending.pop(src)))
        else:
            # 發生環狀循環依賴，僅對第一個節點暫存破圈
            src, dst = next(iter(pending.items()))
            tmp = src + f".kyte_{uuid.uuid4().hex[:6]}.tmp"
            ordered.append((src, tmp))
            pending[tmp] = dst
            del pending[src]
            
    return ordered
```

### 2. Windows NTFS 安全改名與長路徑保護

```python
def to_extended_path(p: str) -> str:
    abs_p = os.path.abspath(p)
    return abs_p if abs_p.startswith("\\\\?\\") else f"\\\\?\\{abs_p}"

def rename_safe(src: str, dst: str):
    ext_src = to_extended_path(src)
    ext_dst = to_extended_path(dst)
    
    # 處理 NTFS 僅大小寫變更（如 test.jpg -> test.JPG）
    if ext_src.lower() == ext_dst.lower() and ext_src != ext_dst:
        tmp = ext_src + f".kyte_{uuid.uuid4().hex[:6]}.tmp"
        os.rename(ext_src, tmp)
        os.rename(tmp, ext_dst)
    else:
        os.rename(ext_src, ext_dst)
```

### 3. 原生 Named Pipe 跨進程通訊（零第三方依賴）

```python
from multiprocessing.connection import Listener, Client
import threading

PIPE_ADDRESS = r'\\.\pipe\KyteRename'

def start_ipc_server(on_file_received_callback):
    """KyteRename 啟動後在背景監聽 KyteView 發送的指令與檔案路徑"""
    def _loop():
        with Listener(PIPE_ADDRESS, family='AF_PIPE') as listener:
            while True:
                with listener.accept() as conn:
                    try:
                        msg = conn.recv()
                        on_file_received_callback(msg)
                    except EOFError:
                        pass
    threading.Thread(target=_loop, daemon=True).start()

def request_kyteview_preview(file_path: str):
    """按 Space 時將選中檔案發給 KyteView 彈出預覽"""
    try:
        with Client(r'\\.\pipe\KyteView', family='AF_PIPE') as conn:
            conn.send({"action": "preview", "path": file_path})
    except (FileNotFoundError, ConnectionRefusedError):
        pass  # KyteView 未啟動則忽略
```

---

## 依賴清單

```txt
# 核心框架
PySide6>=6.7.0

# 中繼資料讀取
Pillow>=10.3.0          # JPEG/TIFF EXIF 讀取
mutagen>=1.47.0         # MP3/FLAC/M4A ID3 標籤

# 可選功能
pypinyin>=0.51.0        # 中文轉拼音

# 備註：IPC 使用 Python 標準庫 multiprocessing.connection 原生 Named Pipe，無需 pywin32。
```

---

## 開發順序建議

```
Phase 1（雙欄預覽骨架 + Scope 作用域）
  → Phase 2（元資料變數 + 漸進式預覽 + 流水號）
  → Phase 4（拓撲排序安全改名 + 逆向防呆快照）  ← 核心安全基石
  → Phase 3（正則 + 即時匹配高亮 Delegate）
  → Phase 4 模板 Picker
  → Phase 5 UX 打磨 + 原生 Named Pipe 聯動
  → Phase 6 打包
```
