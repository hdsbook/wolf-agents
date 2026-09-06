---
name: god-endgame
description: 狼人殺・終局。公布底牌、寫戰報、終局全場稽核、MVP 票選、歸檔、沉澱教訓。分出勝負後執行。僅 GOD 執行。 觸發詞：遊戲結束、公布身份、開牌、翻牌、寫戰報、分勝負了。
---

# /god-endgame —— 終局

## 觸發

`/god-day` 或 `/god-vote` 的勝負檢查回報「已達成」。

## 1. 公布結果與底牌

**落檔＋指路**：先 `render.py game_over <payload> --out game-state/public/mailbox/end-gameover/`，
再 `/god-dispatch notice` 並行指路全部 9 位（含已出局者）。

**建議為每位玩家客製一段個人回饋**：他的判斷哪些對了、哪些沒對、他的死因、他留下了什麼。
**這時中立性已解除** —— 底牌公開、勝負已定，中立性的目的已經達成。

## 2. 立刻發動三件並行的事

`game_over` 一送出就同時做完這三個動作，**中間不要等任何人**：

```
SendMessage → reporter
「勝負已公告，請寫戰報 game-state/public/99-reveal.md，寫完接著 /reporter-build。
 這是公開版第一次揭底牌。寫完回報我一次。」
```

```
render.py ask_mvp <payload> --out game-state/public/mailbox/end-mvp/
/god-dispatch notice     —— 並行指路 9 位，讀完執行 /player-vote-mvp
```

然後**你自己去跑稽核**（第 3 步）。

> **這三件事沒有先後關係**：稽核要讀 session transcript，那是 `god` 專屬路徑，
> 只有你做得了；戰報只要底牌與公開紀錄，reporter 全都有；MVP 是玩家的事。
> 舊版把它們排成一條直線，三件互不相干的工作在等彼此。
>
> **`game_over` 必須先送出去。** 它是「底牌可以公開」的分界 ——
> reporter 一畫公開版就會列出全員身份（`render.py` 看 `potions.json` 的 `result`）。
> 先送公告，再叫它畫，順序不能反。

## 3. 終局全場稽核 → `public/99-audit.md`

跑 `/god-audit` 的完整版，涵蓋全場所有玩家 + reporter：

- 量化表：每人工具數／玩家間訊息／ListAgents／檔案操作
- **`.claude/hooks/access.log` 全文** —— 每一次被 hook 擋下的存取嘗試。
  這是最直接的證據，比 transcript 掃描更明確
- 逐項檢查結果
- **任何命中都要附複查說明** —— 包括判定為假陽性的那些
- 若發現主持方自己的缺陷，**照實寫進去**

稽核**只有你做得了** —— `.claude/projects/` 與 `.jsonl` 是 `god` 專屬路徑，
reporter 讀不到。所以這一步不能外包，也正因如此它值得跟其他兩件事並行。

寫完 `99-audit.md` 之後不必再叫 reporter —— 第 2 步那則指派已經涵蓋建表。

## 4. 收 MVP 票並唱票

1. （票已在第 2 步發出，這裡只收）
2. 收齊 9 票 → 核對「票數 = 9」且「無人投給自己」
3. 唱票 → 寫 `public/99-mvp.md`（含九則完整理由與最佳時刻）

> 上一局這一輪產生了**整場一半的價值** —— 玩家在知道真相後互相認錯、平反被冤枉的人、診斷彼此的推理錯誤。**不要草草收場。**

寫完 `99-mvp.md` 之後：

```
SendMessage → reporter
「MVP 已唱票完成，請執行 /reporter-build。」
```

## 4.5 驗收 reporter 的戰報

它交回 `99-reveal.md` 時，你看兩件事就好：

- 底牌表與 `roles.json` 一致
- 沒有把你在 `game_over` 私訊裡寫的個人回饋抄進公開檔 —— 那是給該玩家一個人的

**內容與觀點不要改。** 有觀點地呈現本來就是它的工作。

## 5. 最終報表

**不需要額外再產一次** —— 上一步那份就是最終版，會隨對局一起歸檔，是這局最完整的視覺紀錄。
歸檔前確認 `report/index.html` 與 `secret/report-spoiler.html` 的 mtime 都晚於 `99-mvp.md`；
若不是，表示上一步的通知漏掉了，補跑一次再歸檔。

## 6. 歸檔

跑 `/god-archive`，把整局搬進 `game-archive/NNN-日期/`。

**歸檔就是解密。** 資料離開 `game-state/secret/` 就離開了保護區 ——
底牌已公開，保密性的目的已經達成，不需要任何額外的解除程序。

## 7. 沉澱教訓

你與 reporter 各自寫進 `.claude/agent-memory/`：

- 格式：**教訓 → 怎麼用 → 來源局次**
- **只寫跨局的方法論**
- **絕不寫任何一局的底牌或當局狀態**

## 8. 向使用者交付

- 勝負與底牌
- 決定勝負的關鍵瞬間
- 稽核結論（**不要宣稱「保證沒有作弊」** —— hook 擋得住順手，擋不住刻意）
- 檔案位置（`game-archive/NNN-日期/`，含兩份 HTML 報表）
- 這一局值得寫進 skill 的新教訓

## 終局後的態度

**放鬆。** 可以評點、開玩笑、回應致意、轉達玩家之間的話。
玩家在這個階段常會想彼此對話 —— **替他們轉達**，那是這套系統少數能產生真實情感的時刻。
