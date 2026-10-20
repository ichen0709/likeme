# likeme：Discord 食物照片熱量記錄 agent

在你自己的電腦上執行。指定頻道有人傳食物照片，agent 用 `claude -p` 判斷並估熱量，記進 Excel、存下照片，再回覆上傳者。設計細節見 [docs/architecture.md](docs/architecture.md)，需求見 [docs/requirements.md](docs/requirements.md)。

## 設定

1. 複製 `.env.example` 成 `.env`，填入四項：

   | 項目 | 意思 |
   |---|---|
   | `DISCORD_TOKEN` | bot 的登入密碼，**絕對不要 commit、不要貼給別人** |
   | `CHANNEL_ID` | 只聽哪一個頻道（純數字） |
   | `CLAUDE_MODEL` | `claude -p` 用的模型，例如 `sonnet` |
   | `DATA_DIR` | 照片與 Excel 放哪，建議放在 repo 之外 |

2. Discord Developer Portal：Bot 頁面打開 **Message Content Intent**；邀請 bot 時給「檢視頻道、發送訊息、讀取訊息歷史、新增反應」。
3. 電腦上要有可用的 `claude` 指令（已登入）。

## 啟動

```
uv sync
uv run foodbot
```

（等同 `uv run python -m foodbot.main`。）關掉終端機 agent 就停止，關機期間傳的照片不會補處理。

## 測試

```
uv run pytest
```

## 四段防護在哪裡

全部集中在 `src/foodbot/guards.py`，每段用固定格式的註解圈起來。開關是檔案最上方的 `GUARD_1_ON`～`GUARD_4_ON`，目前**全部是 `True`**；關掉時走每段裡 `else` 那一邊的對照寫法。

| 段 | 內容 | 位置（大約行號） |
|---|---|---|
| 防護 1 | `claude -p` 只看得到那一張照片，看不到 `DATA_DIR` | `guards.py` 第 24～57 行 |
| 防護 2 | 上傳者打的字只能當資料，不能變成指令 | `guards.py` 第 60～100 行 |
| 防護 3 | 食物名稱當檔名前先清洗 | `guards.py` 第 103～131 行 |
| 防護 4 | 寫進 Excel 的文字防公式 | `guards.py` 第 134～149 行 |

找各段用：`grep -n "===== 防護" src/foodbot/guards.py`

## 資料位置（`DATA_DIR` 底下）

`photos/` 照片、`records.xlsx` 紀錄、`pending.jsonl` Excel 被占用時的暫存、`usage.json` 每日張數。這些都不可以 commit。
