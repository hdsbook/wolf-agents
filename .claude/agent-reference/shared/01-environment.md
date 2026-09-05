# 環境事實（實測，非推測）

這些是這台機器上的穩定事實，不是會演化的教訓。先讀完能省下很多時間。

| 項目 | 事實 | 影響 |
|---|---|---|
| OS | Windows 11，PowerShell 與 Git Bash 皆可用 | Bash heredoc 可用；PowerShell 沒有 `head`/`tail` |
| Python | 可用，標準庫完整 | 洗牌、渲染、稽核腳本都用 Python，且只用標準庫 |
| Python stdout 編碼 | Windows 預設非 UTF-8 | **腳本開頭必加 `sys.stdout.reconfigure(encoding='utf-8')`**，否則中文全變亂碼 |
| Bash 工具 cwd | 每次呼叫後重設回主目錄 | 每個指令自帶 `cd`，或全用絕對路徑 |
| 文字模式讀檔 | CRLF 會被正規化成 LF | 位元組數對不上通常是這個原因，不是紀錄損壞 |
| hook 輸出中文 | 主控台預設非 UTF-8 | 腳本開頭必加 `sys.stdout.reconfigure(encoding="utf-8")`，否則 deny 理由會變成無效位元組讓 client 解析失敗 |
| hook 攔截 Bash | 檢查的是**整條指令字串** | 一條指令裡只要有一段碰到保護區，整條都會被擋 —— 把驗證片段拆成另一次呼叫 |
| session 重啟 | session id 會變 | 存取控制記的是 id，重啟後必須重跑 `/ur`，否則讀不到自己該讀的東西 |

## 跨 session 訊息的兩個陷阱

**一、`uds:` 開頭的位址就是上帝的位址。**
玩家回覆上帝時會複製 `from` 欄位，所以他們的 `SendMessage` 目標會長成 `uds:\.\pipe\LOCAL\cc-msg-...`。
**稽核時若把它當成「非 GOD」，會誤報全場玩家違規。** 這是實際踩過的坑。

**二、訊息是逐一送達的，不是同時廣播。**
即使在同一個回合送出九則訊息，各玩家的接收時刻仍有先後差異。
**不要設計任何依賴「同時收到」的機制**，也不要讓玩家有機會用收訊時序互相指控 —— 上一局真預言家就是死於這個時序落差。

## Session 重啟

`SendMessage` 的回傳可能出現 `messaging a new session for the first time under a previously used name`，代表對方 session 重啟過。

**但靠這行字是偶然發現的，不可靠。** 應在每階段開始前用 `ListAgents` 比對各 session 的 ref 是否變動，變動就要求該 session 重跑 `/ur`。
