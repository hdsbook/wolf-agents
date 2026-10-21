# M25・hook 指令的路徑要用 $CLAUDE_PROJECT_DIR，不要用相對路徑

**結論**：`settings.json` 裡 hook 的 command 一律寫 `python "$CLAUDE_PROJECT_DIR/.claude/hooks/<腳本>"`。

**原因**：hook 在 session 當下的 cwd 執行。Bash 工具的 cwd 會跨呼叫保留，只要某一次 `cd` 進子目錄沒回來，
相對路徑就找不到腳本 —— `guard_secrets.py` 直接失敗，所有受管工具（Bash、Read、Edit、Write…）全部被擋，
連修 settings.json 都做不到。舊的寫死絕對路徑（換機器就壞）改成相對路徑時，在專案根測試一切正常，
所以這個洞測不出來；症狀出現的時機（某次 cd 之後）跟原因（settings.json）離得很遠。

**來源**：2026-10-21，D 階段重構中 maintainer 自己 `cd .claude/agent-memory` 後整個 session 卡住，
靠不在 matcher 裡的 PowerShell 工具修回來。

**怎麼用**：
- 改 hook 路徑後，**從子目錄**再跑一次任何受管工具，確認 hook 還找得到腳本。
- 指令裡需要 cd 時用 `cd X && ...` 的子 shell，或結尾 cd 回專案根。
- 被自己的 hook 鎖住時，matcher 沒涵蓋的工具（目前是 PowerShell）是唯一出口 —— 那同時也代表它是存取控制的漏洞。
