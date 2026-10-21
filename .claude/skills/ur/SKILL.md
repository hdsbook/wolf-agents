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
/ur maintainer 系統維護者（不參與對局、不佔座位，可與對局同時存在）
```

`/ur god`、`ur god`、`你是god`、或整則只打 `god` 都算。**登記要真的跑第 2 步的腳本**，
跳過它這個 session 就不在 roster 裡，之後讀受保護路徑會被擋。

角色已被別的 session 佔用時，**直接再打一次就會接管**（`--force`／`-f` 仍接受，但已無作用）。

## 執行步驟

### 1. 解析參數

- `god` → `.claude/agents/god.md`
- `reporter` → `.claude/agents/reporter.md`
- `p1`~`p9`／`P1`~`P9`／`1`~`9` → `.claude/agents/player.md`，並記住座號
- `maintainer` → `.claude/agents/maintainer.md`

參數缺漏或無法解析時，**停下來問使用者**，不要猜。

### 2. 登記你的 session id

**這一步要在讀任何受保護檔案之前完成** —— 順序反了，第 4、5 步會被自己的 hook 擋下來。

1. session id 在**這場對話的開頭**，由 `SessionStart` hook 注入：`session id: a1b2c3d4-...`。
   找不到就用 `echo $CLAUDE_CODE_SESSION_ID`；兩個都拿不到就**停下來問使用者**，不要編一個 —— 填錯會以為登記好了、實際權限全錯。
2. 呼叫 `ListAgents`，第一行寫 `This session is <名稱> [<ref>]`，抄下名稱與 ref。
3. **單獨**執行登記（不要和讀檔串在同一條指令 —— hook 檢查的是整條指令字串，登記與讀檔要分兩次呼叫）：

```bash
python .claude/skills/ur/scripts/claim_role.py --role <role> --session-id <id> --name "<名稱>" --ref <ref>
```

腳本把 `角色 → session id` 寫進 `game-state/public/roster.json`，名稱、ref 與訊息位址寫進
`roster-sessions.json` —— 上帝靠它把 session 名稱對到座位，hook 靠它認得「發給上帝」的各種寫法。
**玩家的 SendMessage 只能發給上帝**，所以 god 自己的 `--name`／`--ref` 一定要帶。

**對局進行中**，已登記為玩家的 session 不能改認領 god／reporter／maintainer，腳本會拒絕並記進衝突紀錄。

**後到覆寫**：原本被佔用時登記照樣成立，腳本印一行告知，接管記在 `game-state/public/roster-conflicts.log`。
看到接管提示什麼都不用做（多半只是同角色重啟換了 id、或上一局殘留）；但若你**可能踢到一個還在工作的 session**，回報時提一句，讓那個 session 重跑 `/ur`。

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
| god | `agent-reference/shared/01-environment.md` + `agent-memory/god/INDEX.md` + `agent-memory/shared/INDEX.md`。<br>`agent-reference/god/` 七份工作流程**用到才讀**，情境索引在 `god.md`〈需要時查閱〉 |
| reporter | `agent-reference/reporter/01-verify` → `02-render` → `03-broadcast` + `agent-reference/shared/01-environment.md` + `agent-memory/reporter/INDEX.md` + `agent-memory/shared/INDEX.md` |
| 玩家 | `agent-reference/player/01-play-guide.md`（情境索引，**不含打法建議** —— 那是刻意的） |
| maintainer | `agent-reference/shared/01-environment.md` + `agent-memory/maintainer/INDEX.md` + `agent-memory/shared/INDEX.md`。其餘依要改什麼再讀 |

教訓**只讀 INDEX.md**，需要時再讀 `lessons/` 底下的單則。

**玩家不要讀** `skills/god-*/`、`skills/reporter-*/`、`agent-memory/`、`agent-reference/` 中不屬於你的部分、`game-state/secret/`。
這些由 hook 實際攔截，被擋下**回報上帝即可，不要想辦法繞過**。

### 6. 檢查是否為重跑

用 `ListAgents` 看自己是否已在場、是否曾向 GOD 報到過。首次 → 第 7 步；重跑 → 下方「重入路徑」。

> **開新局不必先清 roster。** 殘留 id 會被各人的 `/ur` 覆寫；roster 在 `game-state/public/`，歸檔或中止會一起清掉。
> 空 roster 期間存取控制一律放行（否則第一個登記的人會被鎖在門外），所以**開局前 11 個 session 都要跑完 `/ur`**。

### 7. 報到

**玩家**：`SendMessage → GOD`「P<n> 已就位（/ur 完成），已載入規則與角色簡報，等候指示。」

**reporter**：`SendMessage → GOD`「reporter 已就位（/ur 完成），已載入報表與稽核流程，等候指令。」

**GOD**：不需報到。向使用者回報：

```
上帝就位，規則和流程都讀完了。

接下來把其他 10 個角色建好就行（reporter、P1~P9），他們會自己來報到，我在這裡等。

人到齊我會主動問你這局怎麼玩（你的角色、推進節奏、播報風格），
那是開局裡你唯一要動手的一次。答完我就發牌，一路帶到天黑之前。

想催我隨時說一聲，我會當場點名告訴你還缺誰 —— 但人沒到齊我不會開始。
```

然後**結束回合等報到**，不催使用者、不反覆回報缺幾個、**不在這裡用 `AskUserQuestion`**（那張卡片在 `/god-open` 第 3 步）。
使用者說「開始點名」「人到齊了」「進行遊戲模式設定」對應 `god-open`、「天黑請閉眼」對應 `god-night` ——
**但那些話不讓你跳過關卡**：立刻用 `ListAgents` 核對，到齊才開始，沒到齊就回報缺誰、繼續等。

**maintainer**：**不報到、不發訊給任何人**（你不在對局的指揮鏈上），直接向使用者回報並等維護指示。

### 8. 回報使用者

一句話說明你認領了什麼角色、載入了哪些檔案。**不要透露角色檔的內容細節**（尤其 GOD 不要在正文複述任何機密設計）。

---

## 重入路徑（session 重啟後）

**不要重複報到**，改為：

**玩家**：`SendMessage → GOD`「P<n> 的 session 重啟過，已重新執行 /ur 並載入規則。請補發我的身份牌與我自己的行動歷史。我不會要求任何我原本不該知道的資訊。」
**收到補發之前不要發言、不要投票。**

**reporter**：確認仍讀得到 `game-state/secret/`，回報「reporter 的 session 重啟過，已重新登記並確認存取正常。」
讀不到表示新 id 還沒進 roster —— 重跑 `/ur reporter`（第 2 步會用新 id 覆寫舊登記）。

**GOD**：直接跑 `/god-resume`。

---

## 四件事要記住

1. **玩家沒有跨局記憶。** `agent-memory/` 底下沒有玩家目錄，這是公平性要求。
2. **上帝對玩家嚴格中立。** 他給了戰術建議就違反 `rules/god-neutrality.md`，可以當場指出。
3. **動作細節按需載入。** 上帝會告訴你跑哪個 skill（`/player-inbox`、`/player-speak`、`/player-vote`、`/player-night-action`、`/player-vote-mvp`）。
4. **受保護的路徑會被實際擋下。** 它讓「不小心讀到」變成不可能，也讓每一次刻意嘗試都留下紀錄。被擋到請回報上帝。
