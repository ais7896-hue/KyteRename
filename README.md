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

## 📁 專案架構

```text
KyteRename/
├── main.py                      # 主程式進入點與 CLI 參數解析
├── config/                      # 設定管理模組
│   └── settings.py              # 偏好設定與規則範本持久化
├── core/                        # 核心重新命名與資料引擎
│   ├── file_scanner.py          # 非同步目錄與檔案掃描器
│   ├── rule_engine.py           # 規則流水線即時預覽計算引擎
│   ├── rename_executor.py       # 拓撲排序 (DAG) 安全批次改名執行器
│   ├── snapshot_manager.py      # 歷史快照紀錄與逆向拓撲還原 (Ctrl+Z)
│   ├── metadata_reader.py       # EXIF 相機資訊與 ID3 音樂標籤解析
│   ├── metadata_worker.py       # 背景執行緒非同步中繼資料讀取
│   ├── kyte_ipc.py              # KyteView Named Pipe 跨進程預覽連動
│   ├── license.py               # 授權驗證管理
│   └── updater.py               # 版本檢查與自動更新
├── rules/                       # 模組化改名規則集
│   ├── base_rule.py             # 規則抽象基底類別 (BaseRule)
│   ├── replace_rule.py          # 關鍵字與正規表達式取代（含反向引用）
│   ├── serial_rule.py           # 智慧自動補零流水號規則
│   ├── metadata_rule.py         # EXIF / ID3 / 檔案屬性動態變數替換
│   ├── prefix_suffix_rule.py    # 前綴與後綴插入規則
│   ├── trim_rule.py             # 字元裁切與範圍移除規則
│   ├── case_rule.py             # 大小寫格式轉換規則
│   ├── pinyin_rule.py           # 中文轉全拼 / 首字母簡拼規則
│   └── sanitize_rule.py         # 非法字元與裝飾符號清洗規則
├── ui/                          # 使用者介面模組
│   ├── main_window.py           # 主視窗佈局與快捷鍵綁定
│   ├── preview_table.py         # QAbstractTableModel 萬級檔案虛擬滾動雙欄表格
│   ├── rule_panel.py            # 左側規則堆疊與參數調整面板
│   ├── search_bar.py            # 頂部即時搜尋與過濾列
│   ├── settings_dialog.py       # 偏好設定對話框
│   ├── license_dialog.py        # 授權註冊對話框
│   └── styles.py                # 深淺色自適應現代 QSS 樣式表
├── i18n/                        # 多國語系字典 (zh_TW / en_US)
├── tests/                       # 單元測試與各階段整合測試
├── msix/                        # Microsoft Store MSIX 封裝清單與資產
├── scoop/ & winget/             # 套件管理器發布清單
├── KyteRename.spec              # PyInstaller 打包設定檔
└── setup.iss                    # Inno Setup 安裝精靈腳本
```

---

## 📦 打包發布 (Phase 6)

### 一鍵編譯免安裝版與安裝精靈

本專案內建自動化建置腳本，自動檢測環境、呼叫 PyInstaller 編譯無黑窗獨立程式，並透過 Inno Setup 產生安裝包：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

- **免安裝綠色版**：產出於 `dist/KyteRename/KyteRename.exe`
- **安裝精靈 Setup**：產出於 `dist/KyteRename_Setup_1.1.1.exe`（自動整合 Windows 右鍵選單「使用 KyteRename 批次整理」）

---

## 📄 授權條款

本專案採用 [Personal & Non-Commercial License](LICENSE) 條款發布。
原始碼僅供個人學習、研究與檢閱用途。未經授權，嚴格禁止任何形式之商業用途、轉售、重新打包、再發布或散布。商業使用或官方打包版本請向原作者取得正式授權。
