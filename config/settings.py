"""
KyteRename - Settings Manager (單例模式、原子儲存、雙模路徑與快照遷移)
"""
import os
import json
import sys
import shutil
import winreg
from pathlib import Path
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal
from i18n import i18n

def get_system_theme() -> str:
    """讀取 Windows 系統深淺色外觀設定 (AppsUseLightTheme)"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if val == 1 else "dark"
    except Exception:
        return "dark"


class SettingsManager(QObject):
    settings_changed = Signal(str, object)
    theme_changed = Signal(str)
    _instance = None

    DEFAULT_SETTINGS = {
        # 改名行為
        "recursive_scan": False,
        "conflict_policy": "ask",          # "ask" | "skip" | "suffix"
        "auto_sanitize_illegal": True,
        "confirm_before_apply": True,

        # 快照防呆
        "max_snapshot_history": 15,
        "snapshot_dir_mode": "appdata",    # "appdata" | "portable"

        # 外觀主題與多語言
        "theme_mode": "system",            # "system" | "dark" | "light"
        "language": "system",              # "system" | "zh_TW" | "en_US"

        # 介面記憶
        "remember_window_size": True,
        "remember_last_rules": False,
        "window_geometry": "",
        "splitter_sizes": [650, 350],

        # 生態聯動
        "enable_space_preview": True,

        # 自動更新
        "last_update_check_time": 0.0,
        "skipped_version": ""
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__()
        self._initialized = True
        self.config_dir = self._resolve_config_dir()
        self.config_path = self.config_dir / "config.json"
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load()

    def _resolve_config_dir(self) -> Path:
        """解析儲存目錄：支援綠色便攜與 AppData 標準模式"""
        exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
        # 只要同層有 portable.flag 或已存在 config.json 就走便攜模式
        if (exe_dir / "portable.flag").exists() or (exe_dir / "config.json").exists():
            return exe_dir

        appdata = os.getenv("APPDATA")
        base = Path(appdata) if appdata else Path.home()
        path = base / "KyteRename"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_snapshot_dir(self, mode: Optional[str] = None) -> Path:
        """根據模式取得快照儲存目錄"""
        if mode is None:
            mode = self.get("snapshot_dir_mode", "appdata")

        if mode == "portable":
            exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
            snap_dir = exe_dir / "snapshots"
        else:
            snap_dir = self.config_dir / "snapshots"

        snap_dir.mkdir(parents=True, exist_ok=True)
        return snap_dir

    def migrate_snapshots(self, old_mode: str, new_mode: str) -> int:
        """切換儲存模式時遷移現有快照"""
        if old_mode == new_mode:
            return 0

        src_dir = self.get_snapshot_dir(old_mode)
        dst_dir = self.get_snapshot_dir(new_mode)

        if not src_dir.exists():
            return 0

        moved = 0
        for f in src_dir.glob("snapshot_*.json"):
            dst_file = dst_dir / f.name
            try:
                shutil.move(str(f), str(dst_file))
                moved += 1
            except Exception:
                pass
        return moved

    def load(self):
        """載入設定檔"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.settings.update(data)
            except Exception as e:
                print(f"[Settings] 載入失敗，採用預設值: {e}")
        i18n.apply_language(self.get("language", "system"))

    def save(self):
        """原子寫入 (Atomic Write)：寫入 tmp 檔後 replace，防止斷電損壞"""
        tmp_path = self.config_path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.config_path)
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            print(f"[Settings] 儲存失敗: {e}")

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    @property
    def theme_mode(self) -> str:
        return self.get("theme_mode", "system")

    @property
    def effective_theme(self) -> str:
        mode = self.theme_mode
        if mode == "system":
            return get_system_theme()
        return mode

    def is_dark(self) -> bool:
        return self.effective_theme == "dark"

    def set(self, key: str, value):
        if self.settings.get(key) != value:
            old_effective = self.effective_theme
            self.settings[key] = value
            self.save()
            self.settings_changed.emit(key, value)
            if key == "language":
                i18n.apply_language(value)
            elif key == "theme_mode":
                new_effective = self.effective_theme
                if old_effective != new_effective:
                    self.theme_changed.emit(new_effective)
