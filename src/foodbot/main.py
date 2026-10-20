"""程式進入點：讀設定、啟動。"""

import sys

import discord

from .bot import FoodBot
from .config import load_config_or_exit


def main() -> None:
    cfg = load_config_or_exit()
    try:
        FoodBot(cfg).run(cfg.discord_token)
    except discord.LoginFailure:
        print("登入失敗：DISCORD_TOKEN 不正確，請到 Discord Developer Portal 確認或重設。",
              file=sys.stderr)
        raise SystemExit(1) from None
    except discord.PrivilegedIntentsRequired:
        print("請到 Discord Developer Portal 的 Bot 頁面打開 Message Content Intent。",
              file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
