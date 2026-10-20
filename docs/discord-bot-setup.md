# Discord bot 設定步驟

> 這份文件教你：①在 Discord Developer Portal 建立 bot、②打開 Message Content Intent、③拿到 bot token、④把 bot 邀進你自己的伺服器、⑤把設定放進 `.env`。
> 請先完成 `docs/discord-server-setup.md`（你需要自己的伺服器和 `CHANNEL_ID`）。
>
> 說明：Discord 偶爾會改畫面文字。如果你看到的名稱跟這裡有一點不同，找意思相近的選項即可。括號裡的英文是英文介面的寫法。

名詞：

- **Discord Developer Portal（開發者後台）**：Discord 官方給開發者建立 bot 的網站。
- **Application（應用程式）**：後台裡的一個專案，bot 是它底下的一個功能。
- **bot**：Discord 上的「程式帳號」，可以像人一樣收發訊息。
- **bot token**：這個 bot 的**登入密碼**。

---

## ⛔ 先讀這一段：bot token 的規則

bot token 是一長串英數字（長得像 `MTIzNDU2Nzg5...` 加上很多點與字元）。**拿到它的人可以完全控制你的 bot**，用你的 bot 發訊息、讀它看得到的所有內容。

所以：

1. **不能貼給任何人**：同學、朋友、老師、客服都不行。
2. **不能貼進這個對話**：不要貼給 Claude，也不要貼到任何聊天軟體、論壇、Google 文件。需要幫忙時，只說「我拿到 token 了」就好，不用貼內容。
3. **不能 commit 進 git**：token 只放在 `.env` 檔，而 `.env` 已經被 `.gitignore` 擋住。
4. **不要截圖**：截圖時不要拍到 token。
5. **萬一外洩了**：立刻回到 Developer Portal 的 Bot 頁面按 **Reset Token**（步驟見第三節），舊的 token 馬上失效，然後把新的放進 `.env`。有疑慮就重設，重設沒有任何損失。

---

## 一、建立 application 和 bot

1. 打開瀏覽器，進入 `https://discord.com/developers/applications`。
2. 如果要你登入，用建立伺服器的**同一個 Discord 帳號**登入。
3. 點右上角藍紫色的 **「New Application」**（新增應用程式）。
4. 輸入名稱，例如 `食物熱量機器人`，勾選同意條款（Developer Terms of Service），點 **「Create」**（建立）。
5. 你會進到這個 application 的管理頁面。左邊有一排選單：General Information、Installation、OAuth2、**Bot**⋯⋯。點左邊的 **「Bot」**。

> 新的 application 通常會自動附帶一個 bot。如果 Bot 頁面一開始就看到 token 相關區塊，就是已經有了；如果有一個「Add Bot」按鈕，點它並確認。

### 建議的兩個設定（同在 Bot 頁面）

- **Public Bot**：把它**關掉**。這樣只有你自己能把這個 bot 邀進伺服器，別人不能拿去用。
- **Requires OAuth2 Code Grant**：保持**關閉**（預設就是關）。

> 如果關閉 Public Bot 時看到錯誤訊息，通常是 Installation 頁面的 Install Link 設定造成的。到左邊 **Installation** 頁面，把 **Install Link** 改成 **None**，再回來關閉 Public Bot。

---

## 二、打開 Message Content Intent（一定要做）

**為什麼要做：** Discord 預設不讓 bot 看到訊息的**內容**和**附件**（為了保護隱私）。這個 agent 要靠附件拿到照片，所以必須手動打開這個開關。沒打開的話，bot 可以連上線，但每一則訊息看起來都是空的，會像「完全沒反應」，而且不會出現明顯的錯誤訊息，很難找原因。

步驟：

1. 還在左邊選單的 **「Bot」** 頁面，往下捲動。
2. 找到區塊 **「Privileged Gateway Intents」**（特權閘道意圖）。
3. 找到 **「MESSAGE CONTENT INTENT」**，把右邊的開關**打開**（變成藍色）。
4. 另外兩個（Presence Intent、Server Members Intent）**保持關閉**，這個專案用不到。
5. 頁面最下面會浮出一個提示列，點 **「Save Changes」**（儲存變更）。

> 注意：bot 如果加入了 100 個以上的伺服器，這個開關需要 Discord 審核。你的 bot 只在自己的伺服器，不會遇到這個問題。

---

## 三、拿到 bot token

> ⚠️ 再提醒一次：做這一步時，旁邊不要開螢幕分享、不要錄影，也不要有人看著你的螢幕。

1. 還在 **「Bot」** 頁面，往上找到 **「Token」** 區塊。
2. 點 **「Reset Token」**（重設 Token）。
3. 跳出確認視窗，點 **「Yes, do it!」**。如果要你輸入密碼或兩步驟驗證碼，照做。
4. 畫面會顯示一串新的 token，旁邊有 **「Copy」**（複製）按鈕，點它。

> **token 只會顯示這一次。** 離開頁面或重新整理後就看不到了，只能再 Reset 一次。所以複製完要馬上做下面「放進 `.env`」那一節，不要先貼到別處。

---

## 四、把 bot 邀進你的伺服器

### 4-1. 產生邀請連結

1. 在左邊選單點 **「OAuth2」**。
2. 往下捲，找到 **「OAuth2 URL Generator」**（OAuth2 網址產生器）。
3. 在 **「Scopes」**（範圍）區塊，只勾選 **`bot`**。其他都不要勾（特別是不要勾 `applications.commands`，這個專案沒有斜線指令）。
4. 勾了 `bot` 之後，下面會出現 **「Bot Permissions」**（Bot 權限）區塊。只勾這四項：

   | 要勾的權限 | 用途 |
   |---|---|
   | **View Channels**（檢視頻道） | 能看到頻道裡的訊息 |
   | **Send Messages**（發送訊息） | 能回覆「處理中」和結果，也能編輯自己發的訊息 |
   | **Read Message History**（讀取訊息歷史） | 回覆時要指定「回覆哪一則訊息」，需要這個權限 |
   | **Add Reactions**（新增反應） | 收到照片時，對那則訊息加上 ⏳ 表示收到 |

   **其他一律不要勾**，尤其不要勾 Administrator（管理員）。權限越少，萬一出事影響越小。
5. 最下面會出現 **「Generated URL」**（產生的網址）。點旁邊的 **「Copy」**。

### 4-2. 用連結加入伺服器

1. 打開瀏覽器新分頁，貼上剛才複製的網址，按 Enter。
2. 畫面會問「要把 bot 加到哪個伺服器」。下拉選單裡選**你自己建的那個伺服器**（例如 `食物熱量測試`）。
3. 點 **「繼續」**（Continue）。
4. 確認畫面列出的權限就是上面那四項，點 **「授權」**（Authorize）。
5. 如果出現「我不是機器人」的驗證，照指示完成。

### 4-3. 確認 bot 進來了

回到 Discord，看伺服器右邊的成員清單，應該會出現 bot 的名字，旁邊有個 **「BOT」** 標籤。此時它是**離線**（灰色）的，因為程式還沒有啟動，這是正常的。

### 4-4. 如果你的 `# 食物照片` 是私人頻道

在頻道名稱旁邊點齒輪（編輯頻道）→ **「權限」**（Permissions）→ **「新增成員或身分組」**，選 bot，並確認它有上面四項權限。如果是公開頻道（建議這樣），這一步不用做。

---

## 五、把設定放進 `.env`

`.env` 是放在專案資料夾（`C:\Users\PC02\likeme`）裡的一個純文字檔，專門放不能公開的設定。已經被 `.gitignore` 擋住，不會被 commit。

### 5-1. 用記事本建立 `.env`

1. 開啟 Windows 的「記事本」。
2. 貼上下面四行，把等號右邊換成你自己的值：

   ```
   DISCORD_TOKEN=（貼上你剛複製的 token）
   CHANNEL_ID=（貼上你記在記事本裡的頻道編號）
   CLAUDE_MODEL=sonnet
   DATA_DIR=C:\Users\PC02\foodbot-data
   ```

   - 等號兩邊**不要加空格**、**不要加引號**。
   - `DATA_DIR` 是存照片和 Excel 的資料夾，**放在專案資料夾之外**。這個資料夾不存在也沒關係，之後程式會自己建立。
3. 點左上角 **「檔案」→「另存新檔」**。
4. 存檔位置選 `C:\Users\PC02\likeme`。
5. **「存檔類型」** 下拉選單改成 **「所有檔案 (*.*)」**。
6. **「檔案名稱」** 輸入 `.env`（前面有一個點，後面沒有任何副檔名）。
7. 點 **「存檔」**。

> 常見的錯誤：如果「存檔類型」沒改成「所有檔案」，記事本會存成 `.env.txt`，程式就讀不到。檢查方法：在檔案總管的「檢視」→「顯示」→ 勾選「副檔名」，確認檔名是 `.env`，不是 `.env.txt`。

### 5-2. 確認 `.env` 不會被 commit

1. 在專案資料夾空白處按 Shift ＋ 滑鼠右鍵 →「在此處開啟 PowerShell 視窗」（或「在終端機中開啟」）。
2. 輸入下面這行，按 Enter：

   ```
   git status
   ```

3. 看輸出的 **Untracked files**（未追蹤的檔案）清單。**清單裡不應該出現 `.env`**。如果出現了，先不要 commit，告訴我。

### 5-3. 把記事本裡的暫存內容清掉

關掉剛才暫存 `CHANNEL_ID` 的記事本視窗，並且**不要儲存**那份暫存檔。確認 token 沒有留在任何你不需要的地方（剪貼簿、筆記、聊天記錄）。

---

## 做完後的檢查

- [ ] Developer Portal 裡有你的 application，Bot 頁面的 **Message Content Intent 是開的，且已按 Save Changes**。
- [ ] Public Bot 已關閉。
- [ ] 邀請 bot 時**只勾了** View Channels、Send Messages、Read Message History、Add Reactions 四項權限。
- [ ] 你的伺服器成員清單裡看得到 bot（離線是正常的）。
- [ ] `C:\Users\PC02\likeme\.env` 存在，檔名不是 `.env.txt`，裡面四行都有值。
- [ ] `git status` 沒有顯示 `.env`。
- [ ] token 沒有貼給任何人，也沒有貼進任何對話。

全部打勾之後，Discord 這邊就設定完了。接下來就可以開始寫程式。
