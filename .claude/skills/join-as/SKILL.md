---
name: join-as
description: 狼人殺・認領角色並載入該角色需要的全部知識。11 個 session 的第一件事。用法 /join-as god、/join-as reporter、/join-as p1 ~ /join-as p9。session 重啟後可重跑以恢復角色認知。
---

# /join-as <role> —— 認領角色

**這是你在這個專案要做的第一件事。在此之前不要做任何遊戲相關的動作。**

## 用法

```
/join-as god        主持人
/join-as reporter   記錄者（戰況報表與結構稽核）
/join-as p1 … p9    玩家（大小寫不拘，/join-as P3 或 /join-as 3 也接受）
```

## 執行步驟

### 1. 解析參數

- `god` / `GOD` → 角色檔 `.claude/agents/god.md`
- `reporter` / `REPORTER` → `.claude/agents/reporter.md`
- `p1`~`p9` / `P1`~`P9` / `1`~`9` → `.claude/agents/player.md`，並記住座號

參數缺漏或無法解析時，**停下來問使用者**，不要猜。

> **這一行指令同時做了一件你看不到的事。** `UserPromptSubmit` hook 會攔下它，
> 把你的 session id 登記進 `.claude/hooks/roster.json`，存取控制才知道你是誰。
> 所以 **`/join-as` 必須由使用者親自輸入**，你自己在對話中提到這串字不會觸發登記。
>
> 角色**先到先得**：若該角色已被別的 session 佔用，登記不會生效，
> 你會在提示中看到一行警告，而且該次嘗試會留在 `roster-conflicts.log`。

### 2. 讀角色檔

完整讀完對應的 `.claude/agents/*.md`。

### 3. 讀公開規則（三種角色都要）

```
.claude/rules/board.md
.claude/rules/flow.md
.claude/rules/conduct.md
.claude/rules/messaging.md
.claude/rules/god-neutrality.md
```

### 4. 讀屬於你的參考資料

| 角色 | 額外要讀 |
|---|---|
| god | `agent-reference/shared/environment.md` + `agent-memory/god/` + `agent-memory/shared/`。<br>**七份工作流程在 `agent-reference/god/`，依 `god.md` 的情境索引用到才讀** |
| reporter | `agent-reference/reporter/` 兩份 workflow + `agent-reference/shared/environment.md` + `agent-memory/reporter/` + `agent-memory/shared/` |
| 玩家 | `agent-reference/player/play-guide.md` |

**玩家不要讀** `skills/god-*/`、`skills/reporter-*/`、`agent-memory/`、`game-state/secret/`
—— 那些不屬於你。

而且**你也讀不到**：這些路徑由 hook 實際攔截，不是靠自律。
被擋下時你會收到一段說明，那不是懲罰，是機制正常運作。**回報上帝即可，不要想辦法繞過。**

### 5. 檢查是否為重跑

用 `ListAgents` 看自己是否已在場、以及是否曾向 GOD 報到過。

- **首次執行** → 進第 6 步
- **重跑（session 重啟）** → 見下方「重入路徑」

### 6. 報到

**玩家**：
```
SendMessage → GOD
「P<n> 已就位（/join-as 完成），已載入規則與角色簡報，等候指示。」
```

**reporter**：
```
SendMessage → GOD
「reporter 已就位（/join-as 完成），已載入報表與稽核流程，等候指令。」
```

**GOD**：不需報到。改為向使用者回報「已就位，準備執行 `/god-roll-call`」，然後**停下來等使用者指示**。

### 7. 回報使用者

一句話說明你認領了什麼角色、載入了哪些檔案。**不要透露角色檔的內容細節**（尤其 GOD 不要在正文複述任何機密設計）。

---

## 重入路徑（session 重啟後）

如果你是重跑，**不要重複報到**，改為：

**玩家**：
```
SendMessage → GOD
「P<n> 的 session 重啟過，已重新執行 /join-as 並載入規則。
請補發我的身份牌與我自己的行動歷史。我不會要求任何我原本不該知道的資訊。」
```
然後等 GOD 補發。**在收到補發之前不要發言、不要投票。**

**reporter**：確認自己仍讀得到 `game-state/secret/`，然後回報：
```
「reporter 的 session 重啟過，已重新登記並確認存取正常。」
```
**若讀不到**，表示新的 session id 還沒進 roster —— 請使用者重跑一次 `/join-as reporter`。

**GOD**：直接跑 `/god-resume`，那支 skill 就是為這件事寫的。

---

## 四件事要記住

1. **玩家沒有跨局記憶。** `.claude/agent-memory/` 底下沒有玩家目錄，這是公平性要求 —— 每一局都從零開始。
2. **上帝對玩家嚴格中立。** 他不會給你戰術建議。若他給了，那違反 `rules/god-neutrality.md`，你可以當場指出來。
3. **動作細節按需載入。** 上帝的私訊會告訴你這一步要跑哪個 skill（`/player-speak`、`/player-vote`、`/player-night-action`、`/player-vote-mvp`），格式寫在那些 skill 裡，現在不必記。
4. **受保護的路徑會被實際擋下。** 這不是信任問題，是機制 —— 它讓「不小心讀到」變成不可能，
   也讓每一次刻意嘗試都留下紀錄。被擋到請回報上帝。
