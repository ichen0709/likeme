"""讀 .env 並檢查；缺任何一項就說明哪裡有問題並停止。不會印出 token。"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 額度與上限（架構文件第 13 節；故意不放 .env）
DAILY_LIMIT_PER_USER = 15
DAILY_LIMIT_TOTAL = 100
MAX_IMAGES_PER_MESSAGE = 4
QUEUE_MAX = 10
CLAUDE_TIMEOUT_SECONDS = 120
MAX_IMAGE_BYTES = 10 * 1024 * 1024
HINT_MAX_CHARS = 200


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    discord_token: str = field(repr=False)
    channel_id: int
    claude_model: str
    data_dir: Path

    @property
    def photos_dir(self) -> Path:
        return self.data_dir / "photos"

    @property
    def records_path(self) -> Path:
        return self.data_dir / "records.xlsx"

    @property
    def pending_path(self) -> Path:
        return self.data_dir / "pending.jsonl"

    @property
    def usage_path(self) -> Path:
        return self.data_dir / "usage.json"


def load_config() -> Config:
    load_dotenv()
    missing = [k for k in ("DISCORD_TOKEN", "CHANNEL_ID", "CLAUDE_MODEL", "DATA_DIR")
               if not os.environ.get(k, "").strip()]
    if missing:
        raise ConfigError(f".env 缺少設定：{', '.join(missing)}（請參考 .env.example）")
    channel_raw = os.environ["CHANNEL_ID"].strip()
    if not channel_raw.isdigit():
        raise ConfigError("CHANNEL_ID 必須是純數字")
    data_dir = Path(os.environ["DATA_DIR"].strip()).expanduser()
    try:
        (data_dir / "photos").mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ConfigError(f"DATA_DIR 無法建立：{data_dir}（{e.strerror}）") from None
    return Config(
        discord_token=os.environ["DISCORD_TOKEN"].strip(),
        channel_id=int(channel_raw),
        claude_model=os.environ["CLAUDE_MODEL"].strip(),
        data_dir=data_dir.resolve(),
    )


def load_config_or_exit() -> Config:
    try:
        return load_config()
    except ConfigError as e:
        print(f"設定錯誤：{e}", file=sys.stderr)
        raise SystemExit(1) from None
