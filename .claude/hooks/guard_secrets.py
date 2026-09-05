"""PreToolUse hook —— 依角色攔截對受保護路徑的存取。

放行則靜默結束；攔截則回 permissionDecision=deny，並把該次嘗試寫進 access.log。
access.log 是稽核證據：它比事後 grep transcript 直接得多。
"""
import sys
import os
import json
import datetime

# Windows 主控台預設非 UTF-8，中文輸出會變成無效位元組讓 client 解析失敗
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import policy


def load_roster():
    try:
        with open(policy.ROSTER, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def role_of(session_id, roster):
    for role, sid in roster.items():
        if sid == session_id:
            return role
    return None


def log(entry):
    try:
        with open(policy.ACCESS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0  # 解析不了就不擋，避免把整個 session 卡死

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    session_id = data.get("session_id", "")

    roster = load_roster()

    # Bootstrap：roster 還不存在＝還沒有人執行 /join-as＝這一局還沒開始。
    # 此時一律放行，否則第一個要建立 roster 的人自己就被鎖在外面。
    # roster 一旦存在，刪除它需要動到 .claude/hooks/，而那本身是受保護的。
    if not roster:
        return 0

    role = role_of(session_id, roster)

    allowed, code, frag = policy.evaluate(role, tool_name, tool_input)
    if allowed:
        return 0

    reason = policy.DENY_MESSAGE.get(code, "這個路徑受保護。")
    log({
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        "session_id": session_id,
        "role": role or "UNREGISTERED",
        "tool": tool_name,
        "rule": code,
        "matched": frag,
        "input": str(tool_input)[:400],
    })

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "【存取控制】%s\n"
                "你目前的身分：%s。這次嘗試已記錄於 .claude/hooks/access.log。\n"
                "如果你認為這是誤擋，請回報上帝，不要自行想辦法繞過 —— 繞過本身構成作弊。"
                % (reason, role or "尚未執行 /join-as")
            ),
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
