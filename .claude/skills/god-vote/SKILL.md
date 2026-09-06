---
name: god-vote
description: 狼人殺・白天投票、唱票、平票 PK 與出局結算。含票數核對與勝負判定。僅 GOD 執行。 觸發詞：開始投票、請投票、唱票、進入投票階段。
---

# /god-vote —— 投票

## 1. 收票

**參數廣播**：把欄位值寫成 `game-state/public/mailbox/d{N}-vote/params.json`，
再 `/god-dispatch notice` 渲染**一次**指路訊息，把同一個字串送給每一位。

附：存活名單、公開逐字稿路徑、發言階段的票型指向、規則提醒（平票 PK、逾時棄票、獵人可開槍）。

## 2. 唱票

收齊後**核對三件事**：

```python
assert len(votes) == len(alive)          # 票數總和 = 存活人數
tally = Counter(votes.values())
top = tally.most_common()
tie = len(top) > 1 and top[1][1] == top[0][1]
```

- 票數總和 = 存活人數（含棄票）
- 每張票的對象都在存活名單中
- 有無平票

**用程式算，不要心算。**

## 3. 公布

**參數廣播**：把欄位值寫成 `game-state/public/mailbox/d{N}-tally/params.json`，
再 `/god-dispatch notice` 渲染**一次**指路訊息，把同一個字串送給每一位。
參數含完整票型**與所有投票理由的原文**。

同時寫進 `public/04-votes-dayN.md`。

**落檔後立刻通知 reporter**：

```
SendMessage → reporter
「第 N 天票型已公布，請執行 /reporter-build。」
```

**兩份都產。** 票型與理由已經用 `tally` 並行公告給全場，公開版跟上不會洩漏任何東西。
這一則不要省 —— 有 PK 時，從這裡到第 7 步的收尾中間隔著 PK 發言、二次投票與出局結算，
報表會停在天亮狀態很久。

## 4. 平票 → PK

1. 宣布進入 PK，列出平票對象
2. 平票者**各再發言一次**（用 `ask_speak` 模板，標明是 PK 發言）
   - **後發言者有後手優勢**，這是規則的一部分，照順序跑即可
3. **其餘玩家重新投票**（平票者本人不投）
4. 收齊後再唱一次票，把 PK 發言追加進 `03-speeches-dayN.md`、二次票型追加進 `04-votes-dayN.md`
5. **落檔後通知 reporter**：
   ```
   SendMessage → reporter
   「第 N 天 PK 已唱票，請執行 /reporter-build。」
   ```
6. **PK 再度平票 → 本輪流局，無人出局**

> 上一局實際發生過一次 PK 二度平票流局。好人因此白讓一輪，那是決定勝負的三個瞬間之一 —— **流局是真實且代價高昂的結果，不要為了「有個結論」而擅自加碼裁決。**

## 5. 出局結算

1. 通知出局者：參數寫進 `game-state/public/mailbox/d{N}-out/params.json`，再 `/god-dispatch notice` 送他一個人
2. **出局者若為獵人** → `/god-dispatch hunter_shot` 詢問開槍對象，並結算被帶走的人
3. **身份一律不公布**

## 6. 檢查勝負

```python
if not wolves_alive:                          好人勝
elif not gods_alive or not villagers_alive:   狼人屠邊勝
else:                                         天數 +1
```

**投出最後一名平民的瞬間就是屠邊。** 這是最容易漏掉的結局。

**達成勝負時，先做兩件事再進 `/god-endgame`：**

1. 把結果寫進 `secret/potions.json` 的 `result` 欄位：
   `{"winner": "好人|狼人", "reason": "屠邊（平民全滅）", "day": N}`
2. ```
   SendMessage → reporter
   「勝負已達成，請執行 /reporter-build spoiler。」
   ```
   **只產劇透版** —— `game_over` 這時還沒公告，公開版一旦揭底，玩家會從報表先看到底牌。

## 7. 收尾

1. 把票型**追加**進 `secret/nightlog.json` 的 `day_votes` 陣列（**累積式，不可覆寫**）
2. 更新 `secret/potions.json`（存活/死亡名單、獵人開槍狀態、天數、階段）
3. 更新 `public/02-status.md` 與 `01-timeline.md`，寫上 `04-votes-dayN.md`
4. **通知 reporter 重建報表**：
   ```
   SendMessage → reporter
   「第 N 天投票已結算，請執行 /reporter-build。」
   ```
**下一步**：未分勝負則天數 +1 回 `/god-night`
