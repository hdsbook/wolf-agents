---
name: god-vote
description: 狼人殺・白天投票、唱票、平票 PK 與出局結算。含票數核對與勝負判定。僅 GOD 執行。 觸發詞：開始投票、請投票、唱票、進入投票階段。
---

# /god-vote —— 投票

一輪對局的流程見 `agent-reference/god/02-round.md`，平票與獵人的裁決見 `05-arbitration.md`。本 skill 只管「投票（階段 6）＋出局結算＋勝負檢查」。

## 1. 收票

**參數廣播**：用 `params.py vote --day N` 產 `game-state/public/mailbox/d{N}-vote/params.json`
（PK 重投加 `--pk`，平票者自動排除），只送它印出的 `recipients`。再 `/god-dispatch notice` 渲染**一次**指路訊息，把同一個字串送給每一位。

附：存活名單、公開逐字稿路徑、發言階段的票型指向、規則提醒（平票 PK、逾時棄票、獵人可開槍）。

## 2. 唱票

收齊後把每人回覆的**原文**存成一個 JSON（`{"P1": "投票：P7\n理由：…", …}`，逾時寫 `null`），跑：

```bash
python .claude/skills/god-dispatch/params.py tally --day N --votes <票.json> [--pk Px,Py] --write-nightlog
```

它會**核對三件事，任一不過就不產檔**：

- 票數總和 = 投票人數（存活人數，含棄票；PK 時扣掉平票者）
- 每張票的對象都在存活名單中（PK 時只能投平票者）
- 有無平票 → 平票印出 `next`（進 PK）；PK 再平 → 流局

**「槍口：」行一律不進公開票型**，只出現在終端機的 `hunter_declarations`，
`--write-nightlog` 把它寫進 `nightlog.json` 的 `hunter_declaration`。

**用程式算，不要心算。** 存活名單由你在結算時更新，腳本不改 `roles.json`。

## 3. 公布

**參數廣播**：第 2 步的 `tally` 已經產好 `game-state/public/mailbox/d{N}-tally/params.json`
（出局者的 `d{N}-out` 也一併產好），再 `/god-dispatch notice` 渲染**一次**指路訊息，把同一個字串送給每一位。
參數含完整票型**與所有投票理由的原文**。

同時寫進 `public/04-votes-dayN.md`。

落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter。這一則照抄：

```
SendMessage → reporter
「第 N 天票型已公布，請執行 /reporter-build。」
```

**這一則不要省**（有 PK 時報表會停在天亮狀態很久）。

## 4. 平票 → PK

1. 宣布進入 PK，列出平票對象
2. 平票者**各再發言一次**（用 `ask_speak` 模板，標明是 PK 發言）
   - **後發言者有後手優勢**，這是規則的一部分，照順序跑即可
3. **其餘玩家重新投票**（平票者本人不投）
4. 收齊後再唱一次票，二次票型追加進 `04-votes-dayN.md`。
   PK 發言你不寫檔 —— 由 reporter 用 `/reporter-collect <N> pk` 併進 `03-speeches-dayN-pk.md`（見 `/god-day`〈平票 PK 怎麼跑〉）
5. 落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter。這一則照抄：
   ```
   SendMessage → reporter
   「第 N 天 PK 已唱票，請執行 /reporter-build。」
   ```
6. **PK 再度平票 → 本輪流局，無人出局**

**流局是真實且代價高昂的結果，不要為了「有個結論」而擅自加碼裁決**（實例見 `05-arbitration.md`「白天投票平票」）。

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

**投出最後一名平民的瞬間就是屠邊。** 這是最容易漏掉的結局（見 `05-arbitration.md`「勝負判定」）。

**達成勝負時，先做兩件事再進 `/god-endgame`：**

1. 把結果寫進 `secret/potions.json` 的 `result` 欄位：
   `{"winner": "好人|狼人", "reason": "屠邊（平民全滅）", "day": N}`
2. 落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter。這一則照抄：
   ```
   SendMessage → reporter
   「勝負已達成，請執行 /reporter-build spoiler。」
   ```

## 7. 收尾

1. 把票型**追加**進 `secret/nightlog.json` 的 `day_votes` 陣列（**累積式，不可覆寫**）
2. 更新 `secret/potions.json`（存活/死亡名單、獵人開槍狀態、天數、階段）
3. 更新 `public/02-status.md` 與 `01-timeline.md`，寫上 `04-votes-dayN.md`
4. 落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter。這一則照抄：
   ```
   SendMessage → reporter
   「第 N 天投票已結算，請執行 /reporter-build。」
   ```
**下一步**：未分勝負則天數 +1 回 `/god-night`
