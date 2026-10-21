---
name: god-day
description: 狼人殺・天亮公布與白天發言輪。發言依上帝公告的順位一個一個進行，由玩家自己落檔，上帝只做流程引導與勝負檢查，逐字稿由 reporter 併檔。僅 GOD 執行。 觸發詞：天亮了、天亮請睜眼、白天開始、開始發言、進入白天。
---

# /god-day —— 天亮

一輪對局的流程與白天的設計理由見 `agent-reference/god/02-round.md`。本 skill 只管「天亮公布（階段 4）與發言輪（階段 5）」。

## 階段 4・天亮公布

### 1. 獵人優先

若昨夜死者含獵人且尚未詢問 → 先 `/god-dispatch hunter_shot`，結算後才公布完整名單。

### 2. 決定發言順序

```python
import random
start = random.randrange(len(alive))
direction = random.choice(['順','逆'])
```

**必須隨機，而且要公告是隨機決定的**（理由見 `02-round.md`「發言順序為什麼要隨機並公告」）。

### 3. 公告

**參數廣播**：用 `params.py dawn` 產 `game-state/public/mailbox/d{N}-dawn/params.json`
（順序隨機、收件人只取存活者，見 `god-dispatch` 的「參數檔用腳本產」），
**只送它印出的 `recipients`**；夜間死者送 `eliminated_recipients` 那一份。
再 `/god-dispatch notice` 渲染**一次**指路訊息，把同一個字串送給每一位。
訊息本文不進你的上下文，玩家自己渲染（含發言順序表）。

- **只報死了誰，不報死因，不公布身份**
- 無人死亡則公布「平安夜」

### 4. 檢查勝負

```python
if not wolves_alive:                          好人勝
elif not gods_alive or not villagers_alive:   狼人屠邊勝
else:                                         繼續
```

**用程式算，不要心算。** 屠邊最容易被忽略（見 `05-arbitration.md`「勝負判定」）。

**達成勝負時，先做兩件事再進 `/god-endgame`：**

1. 把結果寫進 `secret/potions.json` 的 `result` 欄位：
   `{"winner": "好人|狼人", "reason": "屠邊（平民全滅）", "day": N}`
2. 落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter。這一則照抄：
   ```
   SendMessage → reporter
   「勝負已達成，請執行 /reporter-build spoiler。」
   ```

### 5. 天亮落檔並通知 reporter

**這一步必須排在 `dawn` 的指路訊息送出之後**，而且在發言輪之前（理由見 `agent-reference/shared/02-reporter-dispatch.md`）。

1. 更新 `secret/potions.json`（存活／死亡名單、天數、階段）
2. 覆寫 `public/02-status.md`：剛完成＝第 N 天天亮結算，**下一步＝發言輪**
3. 追加 `public/01-timeline.md`
4. 落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter。這一則照抄：
   ```
   SendMessage → reporter
   「第 N 天已天亮公告，請執行 /reporter-build。」
   ```
   送完不要讓出回合，接著派第一位發言。

---

## 階段 5・發言輪

依上帝在階段 4 公告的順位，一個一個發言。

### 每一位的流程

1. **參數廣播**：用 `params.py speak --day N --n <位次>` 產 `game-state/public/mailbox/d{N}-speak-{位次}/params.json`
   （必讀清單由腳本對 `speech-inbox/` 核對；印出 `warning` 時先確認，不要直接送），再 `/god-dispatch notice` 送給他一個人。參數是他的順位、他要寫的 inbox 路徑、
   以及 **`filed_list`：到此為止已回報落檔的完整檔名清單**。
   **不附任何逐字稿。**

   > `filed_list` 每一輪都會變，所以**每一位各寫一份參數檔**，
   > `tag` 用他的位次區隔（`d2-speak-1`、`d2-speak-2`…），避免他渲染出上一位的內容。

   > 這張清單是玩家「有沒有漏讀」的唯一判準，**必須完整且正確**。
   > 你手上有全部的落檔回報，這是你在這個階段唯一真正要維護的狀態。
2. 收到「已落檔」的回報。**回報裡不該有發言內文**；他若還是貼了，
   你照樣不轉貼、不摘要、不寫進任何檔案。
3. 落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter 併檔，**送完立刻進下一位**。這一則照抄：
   ```
   SendMessage → reporter
   「第 N 天第 K 位已落檔，請 /reporter-collect N seq，接著 /reporter-build。不必回覆我。」
   ```
   **本日第一則要附上你公告過的發言順序原文**（reporter 要拿它寫逐字稿檔頭；那是你抽的，它推不出來）。
4. 依播報參數決定要不要向使用者說一句「第 K 位已落檔」。**戰況敘事不由你做**，
   見 `agent-reference/god/04-reporting.md`。

**不要等 reporter。** 下一位讀的是 inbox 原文，不是併好的逐字稿。

### 你在這個階段不做的事

- **不讀發言內容。** 你不需要它 —— 順位是你排的，落檔與否看回報，
  身份宣告由 reporter 從原文搬運。讀了只會讓你有機會不小心轉述。
- **不寫 `03-speeches-dayN.md`。** 那份檔案現在由 `/reporter-collect` 產生。
- **不整理票型指向。** 誰說要投誰寫在逐字稿裡，玩家自己讀得到。

（為什麼是這三條，見 `02-round.md`「發言輪你為什麼不碰文字」。）

### 逾時

未在合理時間內落檔 → 視為棄權，該位不留下發言，**不影響投票權**。
先用 `/god-dispatch` 重發一次澄清訊息，再判棄權。

---

## 平票 PK 怎麼跑

PK 只有兩個人，**依序各發言一次**（用 `ask_speak` 模板，輪次欄與檔名都寫 `pk`）。
規則見 `flow.md` 階段 6。每位落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter：併檔指派 `/reporter-collect <N> pk`，寫進 `03-speeches-dayN-pk.md`。

---

## 通知 reporter

時機、訊息原文、「送完就走」與送不到時的處理，一律見 `agent-reference/shared/02-reporter-dispatch.md`。

**reporter 不會回你** —— 那是它的紀律，不是它掉線了。**送完不要讓出回合。**

---

## 收尾

1. **不要碰 `03-speeches-dayN.md`。** 那份檔案由 `/reporter-collect` 產生與維護，
   你不追加、不修正、不在末尾補彙整或核心爭點（緣由見 `03-recordkeeping.md`「公開檔的寫入時機」）。
2. 更新 `secret/potions.json`（天數、階段；發言輪期間若無死亡則名單不變）
3. 更新 `02-status.md`（下一步：投票）與 `01-timeline.md`，
   並同步「已公開的身份宣告」表 —— 格式見 `agent-reference/god/03-recordkeeping.md`。
   **來源是併好的 `03-speeches-dayN.md` 標題**，純搬運，不是你讀完發言後的歸納。
   若 reporter 還沒併完，這一步可以等它，或留到投票結算後補。
4. 落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter。這一則照抄：
   ```
   SendMessage → reporter
   「第 N 天發言輪已結束，請確認 /reporter-collect 已涵蓋全部落檔，再執行 /reporter-build。」
   ```
5. 依節奏參數決定是否暫停

**下一步**：`/god-vote`
