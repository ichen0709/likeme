"""辨識圖片格式、存照片、組檔名（架構文件第 9 節）。清洗在 guards.py（防護 3）。"""

from datetime import datetime
from pathlib import Path

from . import guards


def sniff_image(data: bytes) -> str | None:
    """看檔案開頭的特徵碼，回傳 jpg／png／webp／gif；不是圖片回傳 None。"""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    return None


def save_photo(photos_dir: Path, when: datetime, short_name: str, data: bytes, ext: str) -> Path:
    """存進 photos_dir，檔名 `YYYY-MM-DD hh-mm-ss 簡稱.副檔名`；撞名加 -2、-3。"""
    photos_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{when:%Y-%m-%d %H-%M-%S} {guards.sanitize_filename_part(short_name)}"
    n = 1
    while True:
        suffix = "" if n == 1 else f"-{n}"
        path = photos_dir / f"{stem}{suffix}.{ext}"
        guards.confirm_inside(photos_dir, path)
        try:
            with open(path, "xb") as f:  # 已存在就失敗，絕不蓋掉別人的照片
                f.write(data)
            return path
        except FileExistsError:
            n += 1
