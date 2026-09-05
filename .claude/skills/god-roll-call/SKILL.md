---
name: god-roll-call
description: 狼人殺・開局點名與通訊自我測試。確認 11 個 session 全部在線並驗證 SendMessage 雙向正常，未收齊不得發牌。僅 GOD 執行。
---

# /roll-call —— 點名與通訊測試

**開局第一件事。未通過不得進入發牌。**

這一步存在的理由：整場遊戲完全建立在 `SendMessage` 上。若有任何一條線不通，問題會在第三天才浮現，而那時已經無法補救。

## 執行步驟

### 1. 清點在場者

```
ListAgents
```

確認以下 11 個名稱都在列且非 offline：

```
GOD（你自己）  reporter  P1 P2 P3 P4 P5 P6 P7 P8 P9
```

**記下每個 session 的 ref**（例如 `P1 [3998b6]`）—— 之後每階段開始前要比對，ref 變動代表該 session 重啟過。

缺人時：向使用者回報缺哪幾個，**停下來等他建立並改名**，不要自行往下跑。

### 2. 並行發送 ping

用 `dispatch ping` 模板，**一個回合內並行發給全部 10 個對象**（9 玩家 + reporter）。

模板在 `.claude/agent-reference/god/message-templates.md` 的 `ping` 節。

### 3. 收齊回覆

每個對象應回覆「<name> 就位」。

- **全部收齊** → 進第 4 步
- **有缺** → 對缺席者重發一次；仍無回應則向使用者回報是哪幾個、並停下

### 4. 回報使用者

```
點名結果：11 / 11
ListAgents 在場：11
ping 送出：10　｜　ack 收回：10
SendMessage 雙向測試：正常
各 session ref：GOD[xxxxxx] reporter[xxxxxx] P1[xxxxxx] …
```

有異常就照實列出，**不要含糊帶過**。

### 5. 建立基準

把 11 個 ref 寫進 `game-state/public/02-status.md` 的「session 基準」區塊。
往後每階段開始前用 `ListAgents` 比對，ref 變動 → 要求該 session 重跑 `/join-as`。

## 中立性提醒

ping 訊息只做通訊測試，**不得包含任何遊戲資訊、規則說明或身份暗示**。
模板已經寫死，照渲染即可。

## 下一步

點名通過後執行 `/god-setup` 開局。
