# 存取控制 hook

**這是這套系統防作弊的實作。不是約定，是會實際擋下工具呼叫的機制。**

## 三個檔案

| 檔案 | 角色 |
|---|---|
| `policy.py` | **規則集中在這裡。** 哪些路徑受保護、誰通得過、怎麼判斷遞迴掃描 |
| `register_role.py` | `UserPromptSubmit` hook。攔下 `/join-as <role>`，把 session id 登記進 `roster.json` |
| `guard_secrets.py` | `PreToolUse` hook。比對身分決定放行或拒絕，拒絕時寫 `access.log` |

規則只寫在 `policy.py` 一處 —— 註冊與攔截兩邊若各有一份認知，遲早會漂移。

## 三個產生的檔案

| 檔案 | 內容 |
|---|---|
| `roster.json` | `角色 → session id`。**純文字，使用者可以直接編輯** |
| `access.log` | 每一次被擋下的嘗試：時間、session、角色、工具、命中規則、完整參數 |
| `roster-conflicts.log` | 被拒絕的角色認領（角色先到先得） |

## 保護矩陣

| 路徑 | god | reporter | 玩家／未註冊 |
|---|---|---|---|
| `game-state/secret/**` | ✅ | ✅ | ❌ |
| `~/.claude/projects/**`、任何 `*.jsonl` | ✅ | ❌ | ❌ |
| `.claude/skills/god-*` | ✅ | ❌ | ❌ |
| `.claude/skills/reporter-*` | ✅ | ✅ | ❌ |
| `.claude/agent-memory/**` | ✅ | ✅ | ❌ |
| `.claude/agent-reference/god/**` | ✅ | ❌ | ❌ |
| `.claude/settings.json`、`.claude/hooks/**` | ✅ | ❌ | ❌ |

`.claude/rules/`、`game-state/public/`、`game-state/report/`、`game-archive/`
**不受限，所有人可讀** —— 公開性是刻意的。

## 兩種攔截

**直接命中**：路徑字串裡出現受保護片段。大小寫與正反斜線都會正規化，
`cat game-state/secret/roles.json` 和 `Read D:\Projects\...\SECRET\...` 一樣擋。

**遞迴祖先**：掃描範圍會遞迴進入保護區。用真正的路徑前綴運算判斷 ——
`Grep path=game-state` 會擋（它會掃進 `secret/`），`Grep path=game-state/public` 放行。
子字串比對分不清這兩者，所以這裡不能用子字串。

Bash 只有在指令出現遞迴徵兆（`find`、`-r`、`**` 等）時才做祖先判斷。
否則 `git status .` 這種無害指令會因為 token `.` 被誤擋。

## Bootstrap

`roster.json` 不存在時**一律放行** —— 那表示還沒有人執行 `/join-as`，這一局還沒開始，
否則第一個要建立 roster 的人自己就被鎖在外面。

roster 一旦存在，刪除它需要動到 `.claude/hooks/`，而那本身是受保護的。

## 誠實邊界

hook 由 Claude Code client 執行，**刻意繞過仍有可能** —— 例如用字串拼接組出路徑
讓比對抓不到。**這不是作業系統層級的權限控制。**

被真正堵死的是那條**不需要任何作弊意圖就會外洩**的路。
剩下的刻意規避由公開守則、每夜稽核、以及 `game-state/` 根目錄那份誘餌底牌負責。

## 改規則怎麼改

改 `policy.py` 的 `RULES` 與 `PROTECTED_ABS`，**兩張表要一起改** ——
前者管直接命中，後者管遞迴祖先。改完跑一次測試（餵 JSON 進 `guard_secrets.py`
比對放行／拒絕），不要只靠讀。
