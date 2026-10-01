# KyteRename

規則式即時預覽批次重新命名工具（Rule-based Batch File Renamer with Real-time Preview）

## 核心定位
拖入資料夾，左欄原名、右欄「即時預覽改名後結果」，1 秒完成千個檔案更名。支援 EXIF/ID3 中繼資料變數、正則表達式、拓撲防撞與 Ctrl+Z 快照安全復原。

## 技術選型
- **GUI 框架**：PySide6（QTableView 雙欄虛擬化，極致順暢）
- **中繼資料讀取**：Pillow (EXIF)、mutagen (ID3)
- **跨進程通訊**：Windows 原生 Named Pipe（與 KyteView 聯動，按 Space 鍵直接預覽）
- **安全防護**：連鎖改名拓撲排序、NTFS 大小寫不敏感隔離、Windows MAX_PATH 長路徑防護

## 快速開始

### 環境需求
Python 3.10+

### 安裝依賴
```bash
pip install -r requirements.txt
```

### 啟動應用程式
```bash
python main.py
```

## 開發計劃
詳見 [KyteRename_plan.md](KyteRename_plan.md)。
