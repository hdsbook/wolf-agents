# 落檔點與 reporter 指派

> 放在 `shared/`：上帝與 reporter 都讀得到（reporter 讀不到 `agent-reference/god/`），玩家讀不到。
> 內容只有時機、訊息原文與劇透規則，不含任何一局的資料。


**這裡是唯一來源；其他檔案只引用，不複製。** 各 skill 在落檔處只寫一行
「落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter。」，
必要時附上那一則訊息原文讓你照抄；判斷規則（指派哪支、加不加 `spoiler`）只寫在這裡。

### 判準

**判準：剛剛動到 `render.py` 的資料來源了嗎？** 動到就通知。
那六份來源是：`00-players.md`、`03-speeches-dayN.md`、`04-votes-dayN.md`、
`roles.json`、`potions.json`、`nightlog.json`。
（`03-speeches-dayN.md` 現在由 reporter 自己併檔產生 —— 你的觸發點改成
「有人落檔」，實際寫檔的是它。）
（`02-status.md` 與 `01-timeline.md` **不是**來源，`render.py` 不讀它們。）

**指派的時機一律對齊「檔案落地」，不是回合。** 上面六份來源哪一份被寫入，
就是一個觸發點；寫 `01-timeline.md` / `02-status.md` / `99-*.md` 不觸發，
因為 `render.py` 不讀它們。（例外：`99-reveal.md` 由 reporter 自己寫完接著建表，見表中終局列。）

### 完整對照表

`N`＝天數／夜數，`K`＝發言位次。訊息原文照抄。

| # | 落檔點（哪個 skill 的哪一步） | 指派 | 產出 | 訊息原文 |
|---|---|---|---|---|
| 1 | 開局・發牌時（`/god-open` 第 8 步） | `/reporter-init` | 建狀態檔＋驗證＋兩份。**唯一要它回報的一則**（終局戰報另見第 12 列） | 「牌已發下，底牌在 secret/roles.json。請執行 /reporter-init：建其餘狀態檔、跑開局驗證、產兩份報表。做完回報我一次。」 |
| 2 | 夜間收尾（`/god-night` 收尾第 4 件） | `/reporter-build spoiler` | **只有劇透版** | 「第 N 夜已結算，請執行 /reporter-build spoiler。」 |
| 3 | 天亮公告的指路訊息送出後（`/god-day` 第 5 步） | `/reporter-build` | 兩份 | 「第 N 天已天亮公告，請執行 /reporter-build。」 |
| 4 | **發言輪每一位落檔後**（`/god-day` 階段 5 第 3 步） | `/reporter-collect N seq` → `/reporter-build` | 兩份，**送完就走、不等回覆**。本日第一則要附上你公告過的發言順序原文 | 「第 N 天第 K 位已落檔，請 /reporter-collect N seq，接著 /reporter-build。不必回覆我。」 |
| 5 | PK 發言每一位落檔後（`/god-day`〈平票 PK 怎麼跑〉） | `/reporter-collect N pk` → `/reporter-build` | 兩份，寫進 `03-speeches-dayN-pk.md` | 同第 4 列，`seq` 換成 `pk` |
| 6 | 發言輪結束後（`/god-day` 收尾第 4 件） | `/reporter-build` | 兩份 | 「第 N 天發言輪已結束，請確認 /reporter-collect 已涵蓋全部落檔，再執行 /reporter-build。」 |
| 7 | 票型公布並寫檔後（`/god-vote` 第 3 步） | `/reporter-build` | 兩份 | 「第 N 天票型已公布，請執行 /reporter-build。」 |
| 8 | PK 唱票後，僅有 PK 時（`/god-vote` 第 4 步） | `/reporter-build` | 兩份 | 「第 N 天 PK 已唱票，請執行 /reporter-build。」 |
| 9 | 投票結算後（`/god-vote` 第 7 步） | `/reporter-build` | 兩份 | 「第 N 天投票已結算，請執行 /reporter-build。」 |
| 10 | 勝負達成的當下（`/god-day` 第 4 步、`/god-vote` 第 6 步） | `/reporter-build spoiler` | **只有劇透版** | 「勝負已達成，請執行 /reporter-build spoiler。」 |
| 11 | `game_over` 指路訊息送出後（`/god-endgame` 第 2 步） | reporter 寫戰報 `99-reveal.md` → `/reporter-build` | 兩份，**公開版首次揭底牌**。寫完回報你一次 | 「勝負已公告，請寫戰報 game-state/public/99-reveal.md，寫完接著 /reporter-build。這是公開版第一次揭底牌。寫完回報我一次。」 |
| 12 | `99-audit.md` 寫完後（`/god-endgame` 第 3 步） | **不指派** | — | 第 11 列那則已經涵蓋建表 |
| 13 | MVP 唱票、`99-mvp.md` 寫完後（`/god-endgame` 第 4 步） | `/reporter-build` | 兩份（最終版，隨對局歸檔） | 「MVP 已唱票完成，請執行 /reporter-build。」 |

> 第 12 列：舊版此表寫「戰報與稽核寫完後」再派一次，與 `/god-endgame` 實際做法不同；
> 以 skill 為準 —— 戰報由 reporter 寫完自己接著建表，稽核寫完不另外通知。

### 送完就走

**所有指派都是送完就走**：`SendMessage` 出去，不等回覆，直接進下一步。
**「送完就走」的意思是在同一個回合內接著做下一件事，不是把回合結束掉** ——
 reporter 不會回你，你在那裡讓出回合就沒有東西能喚醒你（見 `02-round.md`
「你還會在什麼時候暫停」）。天亮那一則送完要接著派第一位發言，
發言輪那一則送完要接著派下一位。
reporter 只在發現問題時才回你（verify 沒過、清單對不上、宣告缺漏）——
**沉默就是正常**，不要把它的安靜當成掉線而去追問。
**它只在發現問題時才出聲**：`/reporter-verify` 沒過、必讀清單與 inbox 對不上、身份宣告缺漏。
那些是你要處理的異常，其餘一切正常的情況它都安靜做完。
例外只有兩則要它回報：第 1 列（開局初始化）與第 11 列（戰報）。

發言輪尤其如此：**下一位讀的是 inbox 原文，不是併好的逐字稿**，等它沒有任何意義。

**送不到 reporter 時不要重試、不要改用其他管道**，照常跑完發言輪，
由收尾那次通知（第 6 列）補上。**報表可以晚，發言輪不能亂。**

**不要為了送這則通知而開 subagent** —— 開一個 session 只為送一句話，成本比那句話本身高得多。
reporter 不回覆，阻塞本來就不存在。

> 上一版這則通知是交給 subagent 送的，為的是不讓 god 停下來等 reporter 回話。
> 改由 reporter 端「不回覆」來解決同一個問題**更便宜也更直接**。

### 公開版永遠不得早於對應的公告

公開版 `report/index.html` **玩家讀得到**，而它會把死者標成 X；
`potions.json` 的 `result` 一有值，它還會列出全員底牌。

所以**結果尚未公告的那兩個時刻一律加 `spoiler`**：夜間收尾（天亮還沒公告）、
勝負達成當下（`game_over` 還沒發）。天亮那次必須排在 `dawn` 的**指路訊息送出之後**，
終局揭底那次必須排在 `game_over` 的**指路訊息送出之後**。

> 這兩則現在是參數廣播的：先寫 `params.json`、再 `/god-dispatch notice`。
> **觸發點是指路訊息送出的那一刻，不是寫參數檔的那一刻** —— 玩家還沒被通知，公告就還沒發生。

**少打 `spoiler` 這兩個字，等於搶在自己之前把結果公布給全場。**
夜間那次尤其嚴重：死者若是獵人，規則要求先私下問完開槍對象才公布名單。
勝負那次的劇透版只有你、reporter 與人類觀戰者讀得到，所以它能讓勝負即時可見而不洩漏。

- **夜間收尾只產劇透版**：公開版報表會把死者標成 X，而昨夜的結果
  此刻還沒公告出去 —— 少打這兩個字，等於在天亮之前先向全場公布誰死了。
- **勝負達成只產劇透版**：`game_over` 這時還沒公告，公開版一旦揭底，玩家會從報表先看到底牌。
- **天亮那次兩份都產**：死訊已經公告，公開版可以跟上。公開版報表會據 `potions.json`
  把死者標成 X —— 先渲染就等於在公告之前先讓玩家看到死亡名單。
- **發言兩份都產**：發言是玩家自己寫進公開目錄的原文，公開版跟上不洩漏任何東西。
- **票型兩份都產**：票型與理由已經用 `tally` 並行公告給全場，公開版跟上不會洩漏任何東西。

**第 7 列不要省** —— 有 PK 時，從票型公布到投票收尾中間隔著 PK 發言、二次投票與出局結算，
報表會停在天亮狀態很久。

**第 3 列不要併到發言輪之後。** 天亮落檔（`potions.json`、`02-status.md`、`01-timeline.md`）
與這則通知都排在 `dawn` 指路訊息送出之後、發言輪之前 ——
中間隔著全場的完整發言，若在那期間 session 重啟，
`02-status.md` 會停在「第 N 夜結束」，讀不出今天誰死了、發言進行到第幾位。

它會回報七項一致性檢查。**任何一項沒過就停下來先查** —— 那表示紀錄本身壞了，
繼續推進只會讓錯誤擴散到後面每一天。
