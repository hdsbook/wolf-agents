"""
/ur 的角色登記腳本 —— 把 session id 寫進 game-state/public/roster.json。

python .claude/skills/ur/scripts/claim_role.py --role god --session-id <id>
- session id 來自 SessionStart hook 會將本 session 的 id 注入上下文（`session id: <id>`）。
- 角色來自使用者輸入的參數。

後到覆寫：角色已被佔用時一律由後來者接管，接管紀錄寫進
`game-state/public/roster-conflicts.log`。

**唯一的例外**：對局進行中（`game-state/secret/roles.json` 已存在），
已登記為玩家（p1~p9）的 session 不得改認領 god／reporter／maintainer ——
拒絕並寫進衝突紀錄。玩家 session 重啟換了 id 不受影響（新 id 不是玩家）。

另外把 session 的名稱、ref 與訊息位址寫進 `roster-sessions.json`，
讓上帝與 hook 認得「發給上帝」的各種寫法（`God`、`God [70503a]`、`uds:...`）。
名稱與 ref 由 agent 從 ListAgents 第一行抄來；訊息位址由環境變數自動取得。
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
SESSIONS = os.path.join(PUBLIC_DIR, "roster-sessions.json")
ROLES_FILE = os.path.join(PROJECT_DIR, "game-state", "secret", "roles.json")

# 角色代號的唯一來源（hook 的 policy.py 也 import 同一份）。
# 明確加路徑：python -I 不會把腳本所在目錄放進 sys.path。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roles import VALID_ROLES, PRIVILEGED_CLAIM, is_player, normalize_role  # noqa: E402


def log_conflict(text):
    try:
        os.makedirs(PUBLIC_DIR, exist_ok=True)
        with open(CONFLICT_LOG, "a", encoding="utf-8") as f:
            f.write("%s  %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), text))
    except Exception:
        pass


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_roster():
    return load_json(ROSTER)


def main():
    ap = argparse.ArgumentParser(description="登記角色與 session id")
    ap.add_argument("--role", required=True, help="god / reporter / maintainer / p1~p9")
    ap.add_argument("--session-id", required=True,
                    help="本 session 的 id，來自對話開頭注入的那一行")
    ap.add_argument("--name", default="", help="本 session 的名稱（ListAgents 第一行 This session is <名稱> [ref]）")
    ap.add_argument("--ref", default="", help="本 session 的 ref（同一行方括號裡的值）")
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
    in_game = os.path.exists(ROLES_FILE)
    current = [r for r, sid in roster.items() if sid == session_id and r != role]

    if in_game and role in PRIVILEGED_CLAIM and any(is_player(r) for r in current):
        log_conflict("拒絕：對局進行中，玩家 %s（session %s）試圖認領 %s" % (
            "、".join(current), session_id, role))
        print("拒絕：對局進行中，已登記為玩家（%s）的 session 不能認領 %s。\n"
              "此事已記入 game-state/public/roster-conflicts.log，上帝會看到。\n"
              "若這是誤會，請回報上帝。" % ("、".join(current), role))
        return 3

    if held == session_id:
        record_session(role, session_id, args)
        print("角色 %s 已經登記為這個 session，無需變更（名稱／ref 已更新）。" % role)
        return 0

    if held:
        log_conflict("角色 %s 原由 %s 佔用，已由 %s 覆寫接管%s" % (
            role, held, session_id, "（對局進行中）" if in_game else ""))
        if in_game and role in PRIVILEGED_CLAIM:
            print("注意：對局進行中接管特權角色 %s。若不是該角色的 session 重啟，"
                  "請立刻告知使用者。" % role)
        print("角色 %s 原由 session %s 佔用，已由你接管（後到覆寫）。\n"
              "若那個 session 仍在線上，它從現在起失去這個角色的全部權限，\n"
              "需要重跑一次 /ur %s 才能拿回來。\n"
              "此事已記入 game-state/public/roster-conflicts.log。" % (role, held, role))

    roster[role] = session_id
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with open(ROSTER, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=2)

    record_session(role, session_id, args)
    print("已登記：%s → %s" % (role, session_id))
    if not (args.name and args.ref):
        print("提醒：沒有帶 --name／--ref。請用 ListAgents 第一行的值再跑一次，"
              "否則上帝與 hook 認不出你的 session 名稱。")
    print("roster：%s" % ROSTER)
    return 0


def record_session(role, session_id, args):
    """名稱、ref、訊息位址寫進 roster-sessions.json；沒帶的欄位保留舊值。"""
    data = load_json(SESSIONS)
    old = data.get(role) if isinstance(data.get(role), dict) else {}
    if old.get("session_id") != session_id:
        old = {}
    sock = os.environ.get("CLAUDE_CODE_MESSAGING_SOCKET", "")
    data[role] = {
        "session_id": session_id,
        "name": args.name.strip() or old.get("name", ""),
        "ref": args.ref.strip().strip("[]") or old.get("ref", ""),
        "socket": sock or old.get("socket", ""),
        "claimed_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with open(SESSIONS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    sys.exit(main())
