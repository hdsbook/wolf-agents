"""UserPromptSubmit hook —— 從 /join-as <role> 認領中登記 session_id。

Agent 不知道自己的 session_id，所以由 hook 代為登記。
先到先得：角色一旦被某個 session 佔用，別的 session 不得覆寫。
"""
import sys
import os
import json
import re
import datetime

# Windows 主控台預設非 UTF-8，中文輸出會變成無效位元組讓 client 解析失敗
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import policy

JOIN_RE = re.compile(r"/join-as\s+([a-zA-Z0-9_-]+)", re.IGNORECASE)


def normalize_role(raw):
    r = raw.strip().lower()
    if r in ("god", "reporter", "maintainer"):
        return r
    m = re.fullmatch(r"p?([1-9])", r)
    if m:
        return "p" + m.group(1)
    return None


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0

    prompt = data.get("prompt", "") or ""
    session_id = data.get("session_id", "")
    m = JOIN_RE.search(prompt)
    if not m:
        return 0

    role = normalize_role(m.group(1))
    if not role:
        return 0

    try:
        with open(policy.ROSTER, "r", encoding="utf-8") as f:
            roster = json.load(f)
    except Exception:
        roster = {}

    held = roster.get(role)
    if held and held != session_id:
        line = "%s  角色 %s 已由 %s 佔用，%s 的認領被拒絕\n" % (
            datetime.datetime.now().isoformat(timespec="seconds"), role, held, session_id)
        try:
            with open(policy.CONFLICT_LOG, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass
        print("【存取控制】角色 %s 已被另一個 session 佔用，這次認領未生效。"
              "若這是 session 重啟，請使用者直接編輯 .claude/hooks/roster.json。" % role)
        return 0

    roster[role] = session_id
    os.makedirs(os.path.dirname(policy.ROSTER), exist_ok=True)
    with open(policy.ROSTER, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
