"""每日張數計數：每人、全頻道（架構文件第 13 節）。"""

import json
import os
from datetime import date

from .config import DAILY_LIMIT_PER_USER, DAILY_LIMIT_TOTAL, Config


class Usage:
    def __init__(self, cfg: Config):
        self._path = cfg.usage_path
        self._day = date.today()
        self._total = 0
        self._users: dict[str, int] = {}
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if data.get("date") == date.today().isoformat():
                self._total = int(data["total"])
                self._users = {str(k): int(v) for k, v in data["users"].items()}
        except FileNotFoundError:
            pass
        except (ValueError, KeyError, TypeError, AttributeError, OSError):
            print("警告：usage.json 讀不到或已毀損，今天的計數從零開始。")

    def _roll(self) -> None:
        if self._day != date.today():
            self._day, self._total, self._users = date.today(), 0, {}

    def used_total(self) -> int:
        self._roll()
        return self._total

    def used_user(self, user_id: int) -> int:
        self._roll()
        return self._users.get(str(user_id), 0)

    def remaining(self, user_id: int, queued_total: int, queued_user: int) -> tuple[int, bool]:
        """回傳（這個人還能收幾張, 全體額度是否已滿）。已用加上排隊中的都算。"""
        total_left = DAILY_LIMIT_TOTAL - self.used_total() - queued_total
        user_left = DAILY_LIMIT_PER_USER - self.used_user(user_id) - queued_user
        return max(0, min(total_left, user_left)), total_left <= 0

    def increment(self, user_id: int) -> None:
        """每次真的啟動 claude -p 前呼叫。"""
        self._roll()
        self._total += 1
        self._users[str(user_id)] = self._users.get(str(user_id), 0) + 1
        payload = {"date": self._day.isoformat(), "total": self._total, "users": self._users}
        tmp = self._path.with_name(self._path.name + ".tmp")
        try:
            tmp.write_text(json.dumps(payload), encoding="utf-8")
            os.replace(tmp, self._path)
        except OSError as e:
            print(f"警告：usage.json 寫入失敗（{e.strerror}），改用記憶體計數繼續。")
