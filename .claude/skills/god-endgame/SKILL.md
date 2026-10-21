---
name: god-endgame
description: 狼人殺・終局。公布底牌、寫戰報、終局全場稽核、MVP 票選、歸檔、沉澱教訓。分出勝負後執行。僅 GOD 執行。 觸發詞：遊戲結束、公布身份、開牌、翻牌、寫戰報、分勝負了。
---

# /god-endgame —— 終局

完整終局流程與理由見 `agent-reference/god/07-endgame.md`。本 skill 只管「勝負達成之後到交付使用者」的執行步驟。

## 觸發

`/god-day` 或 `/god-vote` 的勝負檢查回報「已達成」。

## 1. 公布結果與底牌

**參數廣播**：把欄位值寫成 `game-state/public/mailbox/end-gameover/params.json`，
再 `/god-dispatch notice` 渲染**一次**指路訊息，把同一個字串送給每一位。
送給全部 9 位（含已出局者）。

**建議為每位玩家客製一段個人回饋**：他的判斷哪些對了、哪些沒對、他的死因、他留下了什麼。
**這時中立性已解除**（見 `07-endgame.md`）。

## 2. 立刻發動三件並行的事

`game_over` 一送出就同時做完這三個動作，**中間不要等任何人**。
**`game_over` 必須先送出去**，再叫 reporter 畫 —— 順序不能反。

落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter。這一則照抄：

```
SendMessage → reporter
「勝負已公告，請寫戰報 game-state/public/99-reveal.md，寫完接著 /reporter-build。
 這是公開版第一次揭底牌。寫完回報我一次。」
```

```
參數 → game-state/public/mailbox/end-mvp/params.json
/god-dispatch notice     —— 渲染一次，送 9 位，他們渲染完執行 /player-vote-mvp
```

然後**你自己去跑稽核**（第 3 步）。

（為什麼三件並行、為什麼 `game_over` 要先送，見 `07-endgame.md`。）

## 3. 終局全場稽核 → `public/99-audit.md`

跑 `/god-audit` 的完整版，涵蓋全場所有玩家 + reporter：

- 量化表：每人工具數／玩家間訊息／ListAgents／檔案操作
- **`.claude/hooks/access.log` 全文** —— 每一次被 hook 擋下的存取嘗試。
  這是最直接的證據，比 transcript 掃描更明確
- 逐項檢查結果
- **任何命中都要附複查說明** —— 包括判定為假陽性的那些
- 若發現主持方自己的缺陷，**照實寫進去**

稽核**只有你做得了**，不能外包（見 `07-endgame.md`）。

寫完 `99-audit.md` 之後不必再叫 reporter —— 第 2 步那則指派已經涵蓋建表。

## 4. 收 MVP 票並唱票

1. （票已在第 2 步發出，這裡只收）
2. 收齊 9 票 → 核對「票數 = 9」且「無人投給自己」
3. 唱票 → 寫 `public/99-mvp.md`（含九則完整理由與最佳時刻）

**不要草草收場**（見 `07-endgame.md`「MVP 票選不要草草收場」）。

寫完 `99-mvp.md` 之後，落檔後依 `agent-reference/shared/02-reporter-dispatch.md` 通知 reporter。這一則照抄：

```
SendMessage → reporter
「MVP 已唱票完成，請執行 /reporter-build。」
```

## 4.5 驗收 reporter 的戰報

它交回 `99-reveal.md` 時，你看兩件事就好：

- 底牌表與 `roles.json` 一致
- 沒有把你在 `game_over` 私訊裡寫的個人回饋抄進公開檔 —— 那是給該玩家一個人的

**內容與觀點不要改。**

## 5. 最終報表

**不需要額外再產一次** —— 第 4 步那份就是最終版，會隨對局一起歸檔。
歸檔前確認 `report/index.html` 與 `secret/report-spoiler.html` 的 mtime 都晚於 `99-mvp.md`；
若不是，表示上一步的通知漏掉了，補跑一次再歸檔。

## 6. 歸檔

跑 `/god-archive`，把整局搬進 `game-archive/NNN-日期/`。
**歸檔就是解密**，不需要任何額外的解除程序（見 `07-endgame.md`）。

## 7. 沉澱教訓

你與 reporter 各自寫進 `.claude/agent-memory/<角色>/`：

1. 先讀索引 `.claude/agent-memory/god/INDEX.md`，確認不是已有的教訓
2. 新增教訓 = 在 `.claude/agent-memory/god/lessons/` 新增一檔，檔名 `<編號>-<短標題>.md`，
   內容四欄：**結論／原因／來源／怎麼用**
3. 在 `INDEX.md` 加一行指向它

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
玩家在這個階段常會想彼此對話 —— **替他們轉達**。
