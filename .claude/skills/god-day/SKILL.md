---
name: god-day
description: 狼人殺・天亮公布與白天發言輪。發言依上帝公告的順位一個一個進行，由玩家自己落檔，上帝只做流程引導與勝負檢查，逐字稿由 reporter 併檔。僅 GOD 執行。 觸發詞：天亮了、天亮請睜眼、白天開始、開始發言、進入白天。
---

# /god-day —— 天亮

## 階段 4・天亮公布

### 1. 獵人優先

若昨夜死者含獵人且尚未詢問 → 先 `/god-dispatch hunter_shot`，結算後才公布完整名單。

### 2. 決定發言順序

```python
import random
start = random.randrange(len(alive))
direction = random.choice(['順','逆'])
```

**必須隨機，而且要公告是隨機決定的。** 上一局有玩家被質疑「挑了全天最安全的發言位」，而事實是順序由上帝隨機指派、玩家無法選擇 —— 公告這點能避免無謂的爭議。

### 3. 公告

**落檔＋指路**：先 `render.py dawn <payload> --out game-state/public/mailbox/d{N}-dawn/`，
再 `/god-dispatch notice` 並行指路。內容一致（含發言順序表），本文不進你的上下文。

- **只報死了誰，不報死因，不公布身份**
- 無人死亡則公布「平安夜」

### 4. 檢查勝負

```python
if not wolves_alive:                          好人勝
elif not gods_alive or not villagers_alive:   狼人屠邊勝
else:                                         繼續
```

**用程式算，不要心算。** 屠邊最容易被忽略 —— 上一局遊戲就是在投出最後一名平民的那一刻結束的，而全場沒有人算到。

**達成勝負時，先做兩件事再進 `/god-endgame`：**

1. 把結果寫進 `secret/potions.json` 的 `result` 欄位：
   `{"winner": "好人|狼人", "reason": "屠邊（平民全滅）", "day": N}`
2. ```
   SendMessage → reporter
   「勝負已達成，請執行 /reporter-build spoiler。」
   ```
   **只產劇透版** —— `game_over` 這時還沒公告，公開版一旦揭底，玩家會從報表先看到底牌。
   劇透版只有你、reporter 與人類觀戰者讀得到，所以它能讓勝負即時可見而不洩漏。

### 5. 天亮落檔並通知 reporter

**這一步必須排在 `dawn` 的指路訊息送出之後**（不是寫檔之後 —— 玩家還沒被通知，公告就還沒發生）。 公開版報表會據 `potions.json`
把死者標成 X —— 先渲染就等於在公告之前先讓玩家看到死亡名單。

1. 更新 `secret/potions.json`（存活／死亡名單、天數、階段）
2. 覆寫 `public/02-status.md`：剛完成＝第 N 天天亮結算，**下一步＝發言輪**
3. 追加 `public/01-timeline.md`
4. ```
   SendMessage → reporter
   「第 N 天已天亮公告，請執行 /reporter-build。」
   ```
   這次**兩份都產**（不加 `spoiler`）—— 死訊已經公告，公開版可以跟上。

不要把這一步併到發言輪之後。中間隔著全場的完整發言，若在那期間 session 重啟，
`02-status.md` 會停在「第 N 夜結束」，讀不出今天誰死了、發言進行到第幾位。

---

## 階段 5・發言輪

依上帝在階段 4 公告的順位，一個一個發言。

### 每一位的流程

1. **落檔＋指路**：`render.py ask_speak <payload> --out game-state/public/mailbox/d{N}-speak-{位次}/`，
   再 `/god-dispatch notice`。內容是他的順位、他要寫的 inbox 路徑、
   以及 **`filed_list`：到此為止已回報落檔的完整檔名清單**。
   **不附任何逐字稿。**

   > `filed_list` 每一輪都會變，所以**每一位各跑一次** `render.py`，
   > `tag` 用他的位次區隔（`d2-speak-1`、`d2-speak-2`…），避免讀到上一位的信。

   > 這張清單是玩家「有沒有漏讀」的唯一判準，**必須完整且正確**。
   > 你手上有全部的落檔回報，這是你在這個階段唯一真正要維護的狀態。
2. 收到「已落檔」的回報。**回報裡不該有發言內文**；他若還是貼了，
   你照樣不轉貼、不摘要、不寫進任何檔案。
3. **`SendMessage` 通知 reporter 併檔，送完立刻進下一位** —— 見下方「通知 reporter」。
   不等它回覆，它也不會回。
4. 依播報參數決定要不要向使用者說一句「第 K 位已落檔」。**戰況敘事不由你做**，
   見 `agent-reference/god/04-reporting.md`。

**不要等 reporter。** 下一位讀的是 inbox 原文，不是併好的逐字稿，
所以併檔落後幾位完全不影響發言輪。

### 你在這個階段不做的事

- **不讀發言內容。** 你不需要它 —— 順位是你排的，落檔與否看回報，
  身份宣告由 reporter 從原文搬運。讀了只會讓你有機會不小心轉述。
- **不寫 `03-speeches-dayN.md`。** 那份檔案現在由 `/reporter-collect` 產生。
- **不整理票型指向。** 誰說要投誰寫在逐字稿裡，玩家自己讀得到。

> 這三條是這次改動的全部重點。上一版你在發言輪要處理同一批文字四次
> （貼逐字稿、收原文、重打進檔、向使用者轉述），九個人跑完接近五十趟往返，
> 而其中**沒有一項需要主持人的判斷**。判斷在裁決與勝負檢查，那些跟文字量無關。

### 逾時

未在合理時間內落檔 → 視為棄權，該位不留下發言，**不影響投票權**。
先用 `/god-dispatch` 重發一次澄清訊息，再判棄權。

---

## 平票 PK 怎麼跑

PK 只有兩個人，**依序各發言一次**（用 `ask_speak` 模板，輪次欄與檔名都寫 `pk`）。
規則見 `flow.md` 階段 6。併檔指派 `/reporter-collect <N> pk`，寫進 `03-speeches-dayN-pk.md`。

---

## 通知 reporter

**直接 `SendMessage`，送完就走，不要等回覆、不要開 subagent。**

**「送完就走」＝在同一個回合內接著做下一件事**，不是把回合結束掉。
reporter 不會回你，你在這裡讓出回合就卡住了 —— 天亮那一則送完要接著派
第一位發言，發言輪那一則送完要接著派下一位。見 `agent-reference/god/02-round.md`。

```
SendMessage → reporter
「第 N 天第 K 位已落檔，請 /reporter-collect N seq，接著 /reporter-build。不必回覆我。」
```

每一位落檔送一則。

**reporter 不會回你** —— 那是它的紀律，不是它掉線了。**它只在發現問題時才出聲**：
`/reporter-verify` 沒過、必讀清單與 inbox 對不上、身份宣告缺漏。
那些是你要處理的異常，其餘一切正常的情況它都安靜做完。

> 上一版這則通知是交給 subagent 送的，為的是不讓 god 停下來等 reporter 回話。
> 改由 reporter 端「不回覆」來解決同一個問題**更便宜也更直接** ——
> 開一個 subagent 只為送一句話，成本比那句話本身高得多。

三個約束：

- **兩份都產**（不加 `spoiler`）。發言是玩家自己寫進公開目錄的原文，公開版跟上不洩漏任何東西。
- **送不到 reporter 時不要重試、不要改用其他管道**，照常跑完發言輪，
  由收尾那次通知補上。**報表可以晚，發言輪不能亂。**
- **本日第一則要附上你公告過的發言順序原文**，reporter 要拿它寫逐字稿檔頭；
  那是你抽的，它推不出來。

---

## 收尾

1. **不要碰 `03-speeches-dayN.md`。** 那份檔案由 `/reporter-collect` 產生與維護，
   你不追加、不修正、不在末尾補彙整或核心爭點。
   （本局第 1 天曾在這裡追加摘要，誤將一則具體身份判斷寫進公開檔案，
   由玩家與 reporter 抓到，教訓見 `agent-memory/god/lessons.md` G11。
   **現在這個錯誤在結構上不可能發生了** —— 你不再是那份檔案的寫入者。）
2. 更新 `secret/potions.json`（天數、階段；發言輪期間若無死亡則名單不變）
3. 更新 `02-status.md`（下一步：投票）與 `01-timeline.md`，
   並同步「已公開的身份宣告」表 —— 格式見 `agent-reference/god/03-recordkeeping.md`。
   **來源是併好的 `03-speeches-dayN.md` 標題**，純搬運，不是你讀完發言後的歸納。
   若 reporter 還沒併完，這一步可以等它，或留到投票結算後補。
4. **通知 reporter 收尾**：
   ```
   SendMessage → reporter
   「第 N 天發言輪已結束，請確認 /reporter-collect 已涵蓋全部落檔，再執行 /reporter-build。」
   ```
5. 依節奏參數決定是否暫停

**下一步**：`/god-vote`
