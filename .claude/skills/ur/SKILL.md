---
name: ur
description: 狼人殺・認領角色（you are ...）並載入該角色需要的全部知識。對局 11 個 session 的第一件事。用法 /ur god、/ur reporter、/ur p1 ~ /ur p9，以及不參與對局的 /ur maintainer。角色被佔用時一律由後來者接管。session 重啟後可重跑以恢復角色認知。觸發詞：ur god（不帶斜線）、你是god、以及只打角色名（god／reporter／p3／maintainer）。
---

# /ur <role> —— 認領角色

**這是你在這個專案要做的第一件事。在此之前不要做任何遊戲相關的動作。**

## 用法

```
/ur god        主持人
/ur reporter   記錄者（戰況報表與結構稽核）
/ur p1 … p9    玩家（大小寫不拘，/ur P3 或 /ur 3 也接受）
/ur maintainer 系統維護者（不參與對局）
```

### 這幾種寫法都算

`/ur god`、`ur god`、`你是god`、或整則只打 `god` —— 都是在叫這支 skill。

**登記由這支 skill 的第 2 步執行腳本完成**，不是自動發生的。
所以看到上面任何一種寫法，你都必須真的把第 2 步跑完；跳過它，
這個 session 就不會出現在 roster 裡，之後讀受保護路徑會被擋。

前四種是對局的 11 個 session。**`maintainer` 不在對局裡** ——
它維護規則、skill、模板、hook 與報表腳本，可以與對局同時存在，
也不佔用任何座位。

角色已被別的 session 佔用時，**直接再打一次就會接管**，不需要任何旗標：

```
/ur god        認領 god；若已被佔用，改由這個 session 持有
```

（`--force` / `-f` 仍然接受，但已經沒有作用 —— 覆寫是預設行為。）

## 執行步驟

### 1. 解析參數

- `god` / `GOD` → 角色檔 `.claude/agents/god.md`
- `reporter` / `REPORTER` → `.claude/agents/reporter.md`
- `p1`~`p9` / `P1`~`P9` / `1`~`9` → `.claude/agents/player.md`，並記住座號
- `maintainer` / `MAINTAINER` → `.claude/agents/maintainer.md`

參數缺漏或無法解析時，**停下來問使用者**，不要猜。

參數缺漏時**停下來問使用者**，不要猜他要哪個角色。

### 2. 登記你的 session id

存取控制認的是 session id，所以要先把「你是誰」寫進 roster，**這一步要在讀任何
受保護檔案之前完成** —— 順序反了，第 4、5 步會被自己的 hook 擋下來。

你的 session id 在**這場對話的開頭**，由 `SessionStart` hook 注入，長這樣：

```
session id: a1b2c3d4-...
```

拿那個值執行：

```bash
python .claude/skills/ur/scripts/claim_role.py --role <role> --session-id <上面那個 id>
```

腳本會把 `角色 → session id` 寫進 `game-state/public/roster.json`。

**找不到那一行 session id 時**：改用環境變數 `$CLAUDE_CODE_SESSION_ID`
（`echo $CLAUDE_CODE_SESSION_ID`）。兩個都拿不到就**停下來問使用者**，
不要編一個 id 填進去 —— 填錯的後果是你以為登記好了，實際上權限全錯。

角色**後到覆寫**：若該角色原本被別的 session 佔用，登記一樣成立，由你接管，
腳本會印出一行告知，該次接管記在 `game-state/public/roster-conflicts.log`。

> **看到接管提示時你要做的事**：什麼都不用做，繼續往下走。
> 那多半只是同一個角色重啟換了 id、或上一局的殘留。
>
> 但若你**確實可能踢到一個還在工作的 session**（例如使用者剛說有人正在用這個角色），
> 就在回報時提一句，讓他知道那個 session 需要重跑一次 `/ur` 才能拿回權限。

### 3. 讀角色檔

完整讀完對應的 `.claude/agents/*.md`。

### 4. 讀公開規則（所有角色都要）

```
.claude/rules/board.md
.claude/rules/flow.md
.claude/rules/conduct.md
.claude/rules/messaging.md
.claude/rules/god-neutrality.md
.claude/rules/glossary.md
```

### 5. 讀屬於你的參考資料

| 角色 | 額外要讀 |
|---|---|
| god | `agent-reference/shared/01-environment.md` + `agent-memory/god/` + `agent-memory/shared/`。<br>**七份工作流程在 `agent-reference/god/`，用到才讀** —— 檔名編號就是重要性順序（`01-opening` 最先用到、`07-endgame` 最後），對照表在 `god.md` 第三段「規則與流程」的情境索引 |
| reporter | `agent-reference/reporter/` 三份（`01-verify` → `02-render` → `03-broadcast`，編號就是執行順序）+ `agent-reference/shared/01-environment.md` + `agent-memory/reporter/` + `agent-memory/shared/` |
| 玩家 | `agent-reference/player/01-play-guide.md`（情境索引：什麼狀況做什麼、東西在哪。**不含打法建議** —— 那是刻意的） |
| maintainer | `agent-reference/shared/01-environment.md` + `agent-memory/maintainer/` + `agent-memory/shared/`。<br>**其餘依要改什麼再讀** —— 你全部讀得到，但一次全讀沒有意義 |

**玩家不要讀** `skills/god-*/`、`skills/reporter-*/`、`agent-memory/`、`game-state/secret/`
—— 那些不屬於你。

而且**你也讀不到**：這些路徑由 hook 實際攔截，不是靠自律。
被擋下時你會收到一段說明，那不是懲罰，是機制正常運作。**回報上帝即可，不要想辦法繞過。**

### 6. 檢查是否為重跑

用 `ListAgents` 看自己是否已在場、以及是否曾向 GOD 報到過。

- **首次執行** → 進第 7 步
- **重跑（session 重啟）** → 見下方「重入路徑」

> **開新局不必先清 roster。** 殘留的舊 session id 不會擋住任何人 ——
> 每位玩家跑 `/ur` 時會直接覆寫掉它。GOD 不需要為此多問一句。
>
> 而且 roster 現在放在 `game-state/public/` 底下，**歸檔或中止一局會把它一起清掉** ——
> 新的一局本來就從空的 roster 開始。空 roster 期間存取控制一律放行
> （否則第一個要登記的人會被自己鎖在門外），所以**開局前 11 個 session 都跑完
> `/ur` 這件事，比以前更重要**。

### 7. 報到

**玩家**：
```
SendMessage → GOD
「P<n> 已就位（/ur 完成），已載入規則與角色簡報，等候指示。」
```

**reporter**：
```
SendMessage → GOD
「reporter 已就位（/ur 完成），已載入報表與稽核流程，等候指令。」
```

**GOD**：不需報到。向使用者回報已就位：

```
上帝就位，規則和流程都讀完了。

接下來把其他 10 個角色建好就行（reporter、P1~P9），他們會自己來報到，我在這裡等。

人到齊我會主動問你這局怎麼玩（你的角色、推進節奏、播報風格），
那是開局裡你唯一要動手的一次。答完我就發牌，一路帶到天黑之前。

想催我隨時說一聲，我會當場點名告訴你還缺誰 —— 但人沒到齊我不會開始。
```

**然後結束回合等報到**，不要催使用者、不要反覆回報還缺幾個。

**不要在這裡用 `AskUserQuestion`** —— 此時其他 10 個 agent 通常還沒建立。
該問的那張卡片在 `/god-open` 第 3 步。

> 使用者打「開始點名」「人到齊了」「進行遊戲模式設定」都對應 `god-open`，
> 「天黑請閉眼」對應 `god-night`。
> **但那些話不讓你跳過關卡** —— 它們要你立刻用 `ListAgents` 核對現場，
> 到齊才開始，沒到齊就回報還缺誰、繼續等。

**maintainer**：**不報到，也不發訊給任何人。** 你不在對局的指揮鏈上，
向 GOD 報到只會讓他多處理一則與主持無關的訊息。直接向使用者回報並等他的維護指示。

### 8. 回報使用者

一句話說明你認領了什麼角色、載入了哪些檔案。**不要透露角色檔的內容細節**（尤其 GOD 不要在正文複述任何機密設計）。

---

## 重入路徑（session 重啟後）

如果你是重跑，**不要重複報到**，改為：

**玩家**：
```
SendMessage → GOD
「P<n> 的 session 重啟過，已重新執行 /ur 並載入規則。
請補發我的身份牌與我自己的行動歷史。我不會要求任何我原本不該知道的資訊。」
```
然後等 GOD 補發。**在收到補發之前不要發言、不要投票。**

**reporter**：確認自己仍讀得到 `game-state/secret/`，然後回報：
```
「reporter 的 session 重啟過，已重新登記並確認存取正常。」
```
**若讀不到**，表示新的 session id 還沒進 roster —— 重跑一次 `/ur reporter`（第 2 步會用新的 id 覆寫舊登記）。

**GOD**：直接跑 `/god-resume`，那支 skill 就是為這件事寫的。

---

## 四件事要記住

1. **玩家沒有跨局記憶。** `.claude/agent-memory/` 底下沒有玩家目錄，這是公平性要求 —— 每一局都從零開始。
2. **上帝對玩家嚴格中立。** 他不會給你戰術建議。若他給了，那違反 `rules/god-neutrality.md`，你可以當場指出來。
3. **動作細節按需載入。** 上帝的私訊會告訴你這一步要跑哪個 skill（`/player-speak`、`/player-vote`、`/player-night-action`、`/player-vote-mvp`），格式寫在那些 skill 裡，現在不必記。
4. **受保護的路徑會被實際擋下。** 這不是信任問題，是機制 —— 它讓「不小心讀到」變成不可能，
   也讓每一次刻意嘗試都留下紀錄。被擋到請回報上帝。
