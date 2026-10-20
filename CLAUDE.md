# CLAUDE.md

這是一支在本機執行的 Discord agent：指定頻道有人傳食物照片，它用 `claude -p` 判斷並估熱量，記進 Excel、存下照片，再回覆上傳者。

## 開始任何工作前

先讀 `docs/architecture.md`，所有設計決定（回覆格式、排隊、額度上限、Excel 欄位、防護）都以它為準。需求原文在 `docs/requirements.md`。如果要做的事和文件衝突，先停下來跟使用者確認，並更新文件，不要自行偏離。

## 四段防護

安全防護共四段，全部集中在 `src/foodbot/guards.py`，內容見架構文件第 12 節：

1. 防護 1：`claude -p` 看不到 `DATA_DIR`
2. 防護 2：上傳者打的字只能當資料
3. 防護 3：食物名稱當檔名前先清洗
4. 防護 4：寫進 Excel 的文字防公式

規則：

- 每一段都要用固定格式的註解圈起來，之後教學會逐段開關對照：

  ```python
  # ===== 防護 N 開始：（一句話說明） =====
  ...
  # ===== 防護 N 結束 =====
  ```

- 開關是 `guards.py` 最上方的四個常數 `GUARD_1_ON`～`GUARD_4_ON`，**一開始全部是 `True`**。沒有使用者明確要求，不可以改成 `False`。
- 每一段旁邊保留「關掉時的對照寫法」，由開關決定走哪一邊。
- 開關不放進 `.env`。
- 不可以為了方便，把防護邏輯散落到 `guards.py` 以外的檔案。

## 不可以 commit 的東西

- **`.env` 絕對不可以進 git。** 裡面有 `DISCORD_TOKEN`。只有 `.env.example`（值留空）可以 commit。
- **`DATA_DIR` 裡的所有東西都不要 commit**：照片、`records.xlsx`、`pending.jsonl`、`usage.json`。
- commit 前先看 `git status` 和 `git diff --staged`，確認沒有上述檔案。不要用 `git add -A` 或 `git add .` 蓋掉這個檢查。
- 不要在終端機輸出、紀錄或錯誤訊息裡印出 token。
- 萬一 token 已經被 commit，先通知使用者去 Discord Developer Portal 重設 token，再處理 git 歷史。
