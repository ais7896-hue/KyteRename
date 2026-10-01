"""
KyteRename - Metadata Reader (高效 EXIF, ID3 與系統屬性讀取器)
"""
import os
import datetime
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image
from PIL.ExifTags import TAGS
import mutagen

def format_size(bytes_size: int) -> str:
    """格式化位元組大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}" if unit != "B" else f"{bytes_size}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"

def read_file_metadata(file_path: Path) -> Dict[str, Any]:
    """讀取單一檔案的完整中繼資料字典"""
    meta: Dict[str, Any] = {}
    p = Path(file_path)
    if not p.exists():
        return meta

    # 1. 基礎檔案系統屬性
    try:
        stat = p.stat()
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
        meta["date"] = mtime.strftime("%Y%m%d")
        meta["datetime"] = mtime.strftime("%Y%m%d_%H%M%S")
        meta["year"] = mtime.strftime("%Y")
        meta["month"] = mtime.strftime("%m")
        meta["day"] = mtime.strftime("%d")
        meta["parent"] = p.parent.name
        meta["ext"] = p.suffix.lstrip(".").lower()
        meta["size"] = format_size(stat.st_size)
    except Exception:
        pass

    ext = p.suffix.lower()

    # 2. 圖片 EXIF & 解析度讀取
    if ext in {".jpg", ".jpeg", ".tiff", ".tif", ".png", ".webp"}:
        try:
            with Image.open(p) as img:
                w, h = img.size
                meta["width"] = str(w)
                meta["height"] = str(h)
                # 解析度簡寫
                if w >= 3840 or h >= 2160:
                    meta["resolution"] = "4K"
                elif w >= 2560 or h >= 1440:
                    meta["resolution"] = "2K"
                elif (w >= 1920 and h >= 1080) or (w >= 1080 and h >= 1920):
                    meta["resolution"] = "1080p"
                elif (w >= 1280 and h >= 720) or (w >= 720 and h >= 1280):
                    meta["resolution"] = "720p"
                else:
                    meta["resolution"] = f"{w}x{h}"

                # 讀取 EXIF
                exif = img.getexif()
                if exif:
                    # 嘗試讀取 DateTimeOriginal (36867) 或 DateTime (306)
                    date_str = exif.get(36867) or exif.get(306)
                    if date_str and isinstance(date_str, str):
                        try:
                            # 格式常為: '2026:08:15 14:30:00'
                            clean_date = date_str.strip().replace("-", ":")
                            dt = datetime.datetime.strptime(clean_date[:19], "%Y:%m:%d %H:%M:%S")
                            meta["exif_date"] = dt.strftime("%Y%m%d")
                            meta["exif_datetime"] = dt.strftime("%Y%m%d_%H%M%S")
                        except Exception:
                            pass
                    # 相機型號 Model (272)
                    model = exif.get(272)
                    if model and isinstance(model, str):
                        meta["camera"] = model.strip().replace(" ", "_")
        except Exception:
            pass

    # 3. 音訊 ID3 / 媒體標籤讀取
    elif ext in {".mp3", ".flac", ".ogg", ".m4a", ".aac", ".wma"}:
        try:
            audio = mutagen.File(p)
            if audio:
                def get_tag(keys: List[str]) -> str:
                    for k in keys:
                        if k in audio:
                            val = audio[k]
                            if isinstance(val, list) and val:
                                return str(val[0]).strip()
                            return str(val).strip()
                    return ""

                artist = get_tag(["artist", "TPE1", "©ART"])
                album = get_tag(["album", "TALB", "©alb"])
                title = get_tag(["title", "TIT2", "©nam"])
                track = get_tag(["tracknumber", "TRCK", "trkn"])
                year = get_tag(["date", "TDRC", "©day", "year"])

                if artist:
                    meta["artist"] = artist
                if album:
                    meta["album"] = album
                if title:
                    meta["title"] = title
                if track:
                    # 處理 '3/12' 格式取前半
                    raw_track = track.split("/")[0].strip()
                    try:
                        meta["track"] = f"{int(raw_track):02d}"
                    except ValueError:
                        meta["track"] = raw_track
                if year:
                    meta["year"] = str(year)[:4]
        except Exception:
            pass

    return meta
