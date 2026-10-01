# KyteRename

> 規則式即時預覽批次重新命名工具（Rule-based Batch File Renamer with Real-time Preview）
> 專為創作者、工程師與重度檔案整理者打造的現代 Windows 桌面工具。

---

## ✨ 核心特色

- **雙欄即時預覽（Virtual Scroll）**：
  採用 Qt `QAbstractTableModel` 虛擬化雙欄表格，拖入萬級檔案依然順暢無延遲，共用垂直滾輪軸。
- **正則語法與動態反向引用**：
  支援正規表達式搜尋取代、群組反向引用（`$1`, `$2` 或 `\1`, `\2`），原檔名即時顯示琥珀金高亮匹配 Delegate。
- **相片與音樂中繼資料變數（Metadata Tags）**：
  背景非同步漸進讀取相機 EXIF 拍攝時間/解析度 (`{exif_date}`, `{resolution}`)、音樂 ID3 歌手/專輯/音軌 (`{artist}`, `{album}`, `{track}`)、檔案屬性 (`{parent}`, `{date}`, `{n}`)。
- **智慧自動補零流水號（Serial Rule）**：
  支援自訂起始值、補零位數、遞增步長，可選擇插入頭尾或全名替換。
- **中文拼音與非法字元清洗**：
  內建中文轉全拼/首字母簡拼（`pypinyin`），以及 Windows 非法字元（`\/:*?"<>|`）與裝飾符號（`【】★`）一鍵過濾清洗。
- **安全拓撲排序（Topological Rename DAG）**：
  自動以拓撲逆序解析連鎖改名依賴（如 `A->B, B->C`），最小暫存檔破圈，NTFS 大小寫不敏感兩階段改名，超長路徑 `\\?\` 防護。
- **歷史快照與逆向拓撲還原（Ctrl+Z）**：
  支援保留歷史快照 JSON，隨時可一鍵或按 `Ctrl+Z` 還原，還原過程同樣實施逆向拓撲防覆蓋。
- **KyteView 原生跨進程無縫聯動**：
  選中檔案按下 `Space` 即刻透過 Windows Named Pipe 喚起 KyteView 快速預覽，清單按 `↑` / `↓` 鍵移動時預覽即時切換且**絕不丟失焦點**。
- **外觀模式與深淺切換（Appearance Mode）**：
  比照 KyteView 旗艦級外觀，支援「跟隨系統 (System)」、「深色模式 (Dark)」、「淺色模式 (Light)」，動態即時無縫換膚。

---

## ⌨️ 快捷鍵一覽

| 快捷鍵 | 功能說明 |
| :--- | :--- |
| `Space` | 在 KyteView 中快速預覽 / 關閉預覽 (Toggle) |
| `↑` / `↓` | 移動選取檔案，若 KyteView 開啟中則無縫同步預覽 |
| `Delete` | 從待更名清單中移除選取項目（支援多選批次移除） |
| `Ctrl + F` | 聚焦至上方搜尋與過濾列 |
| `Ctrl + Z` | 復原上一次的批次改名（安全逆向拓撲還原） |
| `Ctrl + A` | 全選清單中的所有檔案項目 |

---

## 🚀 快速開始

### 環境需求
- Windows 10 / 11 64-bit
- Python 3.10+

### 安裝依賴
```bash
pip install -r requirements.txt
```

### 啟動應用程式
```bash
python main.py
```
*支援 CLI 參數啟動導入目錄或檔案：`python main.py "D:\Photos"`*

---

## 📦 打包發布 (Phase 6)

### 一鍵編譯免安裝版與安裝精靈
本專案內建自動化建置腳本，自動檢測環境、呼叫 PyInstaller 編譯無黑窗獨立程式，並透過 Inno Setup 產生安裝包：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

- **免安裝綠色版**：產出於 `dist/KyteRename/KyteRename.exe`
- **安裝精靈 Setup**：產出於 `dist/KyteRename_Setup_1.0.0.exe`（自動整合 Windows 右鍵選單「使用 KyteRename 批次整理」）

---

## 📄 授權條款

MIT License.
