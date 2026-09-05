"""
/ur 的角色登記腳本 —— 把 session id 寫進 game-state/public/roster.json。

python .claude/skills/ur/scripts/claim_role.py --role god --session-id <id>
- session id 來自 SessionStart hook 會將本 session 的 id 注入上下文（`session id: <id>`）。
- 角色來自使用者輸入的參數。

後到覆寫：角色已被佔用時一律由後來者接管，接管紀錄寫進
`game-state/public/roster-conflicts.log`。
"""
import sys
import os
import re
import json
import argparse
import datetime

# Windows 主控台預設非 UTF-8，中文輸出會變成無效位元組
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# .claude/skills/ur/scripts/claim_role.py → 上四層是專案根
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

PUBLIC_DIR = os.path.join(PROJECT_DIR, "game-state", "public")
ROSTER = os.path.join(PUBLIC_DIR, "roster.json")
CONFLICT_LOG = os.path.join(PUBLIC_DIR, "roster-conflicts.log")

VALID_ROLES = ["god", "reporter", "maintainer"] + ["p%d" % i for i in range(1, 10)]


def normalize_role(raw):
    """god / reporter / maintainer / p1~p9；P3、3 這些寫法都接受。"""
    r = (raw or "").strip().lower()
    if r in ("god", "reporter", "maintainer"):
        return r
    m = re.fullmatch(r"p?([1-9])", r)
    if m:
        return "p" + m.group(1)
    return None


def load_roster():
    try:
        with open(ROSTER, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser(description="登記角色與 session id")
    ap.add_argument("--role", required=True, help="god / reporter / maintainer / p1~p9")
    ap.add_argument("--session-id", required=True,
                    help="本 session 的 id，來自對話開頭注入的那一行")
    args = ap.parse_args()

    role = normalize_role(args.role)
    if not role:
        print("無法解析角色「%s」。可用：%s" % (args.role, "、".join(VALID_ROLES)))
        return 2

    session_id = args.session_id.strip()
    if not session_id:
        print("session id 是空的 —— 請用對話開頭那一行『session id: ...』的值。")
        return 2

    roster = load_roster()
    held = roster.get(role)

    if held == session_id:
        print("角色 %s 已經登記為這個 session，無需變更。" % role)
        return 0

    if held:
        line = "%s  角色 %s 原由 %s 佔用，已由 %s 覆寫接管\n" % (
            datetime.datetime.now().isoformat(timespec="seconds"),
            role, held, session_id)
        try:
            os.makedirs(PUBLIC_DIR, exist_ok=True)
            with open(CONFLICT_LOG, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass
        print("角色 %s 原由 session %s 佔用，已由你接管（後到覆寫）。\n"
              "若那個 session 仍在線上，它從現在起失去這個角色的全部權限，\n"
              "需要重跑一次 /ur %s 才能拿回來。\n"
              "此事已記入 game-state/public/roster-conflicts.log。" % (role, held, role))

    roster[role] = session_id
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with open(ROSTER, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=2)

    print("已登記：%s → %s" % (role, session_id))
    print("roster：%s" % ROSTER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
