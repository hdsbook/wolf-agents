"""SessionStart hook —— 把這個 session 自己的 id 注入上下文。

Agent 平常看不到自己的 session id，但 `roster.json` 是用 id 當鍵的。
沒有這一行，「session 重啟後 id 變了、登記掉了」是一個**靜默失敗** ——
agent 一切如常，直到第一次讀 `game-state/secret/` 被 hook 擋下才發現。
有了這一行，它可以自己比對 roster 並主動要求重跑 `/ur`。

這一行也是 `/ur` 登記步驟的輸入：`claim_role.py` 要靠它才知道要把哪個 id
寫進 `game-state/public/roster.json`。

誰能碰什麼仍然全部由 policy.py 依 roster 決定。**但 roster 現在由 agent 自己
執行的腳本維護、又放在人人可寫的公開區，所以它擋的是意外，不是刻意** ——
見 `.claude/skills/ur/scripts/claim_role.py` 的說明。
"""
import sys
import os
import json

# Windows 主控台預設非 UTF-8，中文輸出會變成無效位元組讓 client 解析失敗
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        data = {}

    # stdin 是 hook 協定保證帶的；env 只是備援（某些啟動路徑可能沒有）
    sid = data.get("session_id") or os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if sid:
        print("session id: %s" % sid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
