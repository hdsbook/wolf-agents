# 存取控制 hook

**這是這套系統防作弊的實作。不是約定，是會實際擋下工具呼叫的機制。**

## 三個檔案


| 檔案                     | 角色                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------ |
| `policy.py`            | **規則集中在這裡。** 哪些路徑受保護、誰通得過、怎麼判斷遞迴掃描                                                   |
| `guard_secrets.py`     | `PreToolUse` hook。比對身分決定放行或拒絕，拒絕時寫 `access.log`                                      |
| `inject_session_id.py` | `SessionStart` hook。把 session 自己的 id 注入上下文，為了讓初始化角色時，每個session對應的角色能紀錄到 roster.json。 |


**登記不在這裡。** roster 由 `/ur` skill 的
`.claude/skills/ur/scripts/claim_role.py` 寫入 `game-state/public/roster.json`。

> **所以 roster 不是可信來源。** 它由 agent 自己執行的腳本維護，而且就放在人人可寫的
> 公開區 —— 任何 session 都能把自己登記成 `god`。腳本無法區分「使用者叫我跑」與
> 「我自己想跑」，那不是實作沒做好，是 agent 的執行環境裡這兩者沒有可觀測的差別。
>
> 換句話說，**這一層現在擋的是意外，不是刻意**。刻意規避由公開守則、終局稽核與
> `access.log` 承擔。

## 產生的檔案


| 檔案                     | 位置                   | 內容                                   |
| ---------------------- | -------------------- | ------------------------------------ |
| `access.log`           | `.claude/hooks/`     | 每一次被擋下的嘗試：時間、session、角色、工具、命中規則、完整參數 |
| `roster.json`          | `game-state/public/` | `角色 → session id`。**純文字，任何人都能讀寫**    |
| `roster-sessions.json` | `game-state/public/` | `角色 → {session_id, name, ref, socket}`。SendMessage 規則用它認上帝 |
| `roster-conflicts.log` | `game-state/public/` | 角色接管的紀錄（後到覆寫）；對局中玩家試圖認領特權角色的**拒絕**紀錄也在這裡 |

## SendMessage：玩家只能發給上帝

`guard_secrets.py` 對 `SendMessage` 只看收件人 `to`，**不掃訊息內文**
（玩家回報「我讀 secret 被擋」是正當的）。p1～p9 的 `to` 必須是上帝的
名稱、ref、`名稱 [ref]` 或 `uds:...cc-msg-...` 位址之一，對照 `roster-sessions.json` 的 `god` 項；
其餘一律擋下並寫 `access.log`（規則 `SENDMSG`）。

god 沒有登記名稱／ref 時無從比對 —— **放行但記一筆 `SENDMSG_UNVERIFIED`**，
寧可留證據給終局稽核，也不要因為缺資料把整局卡死。其他角色不受此限。

## 對局中禁止玩家認領特權角色

`claim_role.py` 在 `game-state/secret/roles.json` 存在時，拒絕「已登記為 p1～p9 的 session」
改認領 god／reporter／maintainer。新的 session（例如上帝重啟）仍可接管，
但會印出警告並在衝突紀錄標「對局進行中」。


## 保護矩陣


| 路徑                                         | god | reporter | 玩家／未註冊 |
| ------------------------------------------ | --- | -------- | ------ |
| `game-state/secret/**`                     | ✅   | ✅        | ❌      |
| `~/.claude/projects/**`、任何 `*.jsonl`       | ✅   | ❌        | ❌      |
| `.claude/skills/god-*`                     | ✅   | ❌        | ❌      |
| `.claude/skills/reporter-*`                | ✅   | ✅        | ❌      |
| `.claude/agent-memory/**`                  | ✅   | ✅        | ❌      |
| `.claude/agent-reference/god/**`           | ✅   | ❌        | ❌      |
| `.claude/settings.json`、`.claude/hooks/**` | ✅   | ❌        | ❌      |


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

`roster.json` 不存在時**一律放行** —— 那表示還沒有人執行 `/ur`，這一局還沒開始，
否則第一個要建立 roster 的人自己就被鎖在外面。

**這個放行區間比以前長，也比以前容易回到。** roster 現在放在
`game-state/public/`，歸檔或中止一局會把它一起清掉，而且任何 session 都刪得掉它。
所以「11 個 session 全部跑完 `/ur` 之後才開局」是實際的前提，不只是流程潔癖。

## 誠實邊界

hook 由 Claude Code client 執行，**刻意繞過仍有可能** —— 例如用字串拼接組出路徑
讓比對抓不到。**這不是作業系統層級的權限控制。**

被真正堵死的是那條**不需要任何作弊意圖就會外洩**的路。
剩下的刻意規避由公開守則與終局稽核負責。
**攔截紀錄是當下就落檔的，所以稽核晚一點做不會遺失任何證據。**

## 改規則怎麼改

改 `policy.py` 的 `RULES` 與 `PROTECTED_ABS`，**兩張表要一起改** ——
前者管直接命中，後者管遞迴祖先。改完跑一次測試（餵 JSON 進 `guard_secrets.py`
比對放行／拒絕），不要只靠讀。