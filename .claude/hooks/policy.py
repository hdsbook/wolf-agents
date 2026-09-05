"""狼人殺・受保護路徑政策（hook 共用）

這個模組定義「誰能碰什麼」，攔截 hook 從這裡取規則。

**角色登記不在這裡。** roster 由 `/ur` skill 的
`.claude/skills/ur/scripts/claim_role.py` 維護，寫在 `game-state/public/roster.json`。
那支腳本刻意**不 import 這個模組** —— 它由玩家 session 執行，而讀取
`.claude/hooks/` 本身受 CONFIG 規則保護，import 會被自己擋下。
代價是角色代號的定義在兩處各有一份，改動時兩邊都要改。
"""
import os
import re

# 專案根目錄 = 本檔案的祖父目錄（.claude/hooks/policy.py → wolf/）
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HOOK_DIR = os.path.join(PROJECT_DIR, ".claude", "hooks")
ACCESS_LOG = os.path.join(HOOK_DIR, "access.log")

# roster 放在公開區 —— 玩家 session 要能自己寫入才登記得了。
# 這也表示**任何 session 都能改它**，見 claim_role.py 的說明。
PUBLIC_DIR = os.path.join(PROJECT_DIR, "game-state", "public")
ROSTER = os.path.join(PUBLIC_DIR, "roster.json")
CONFLICT_LOG = os.path.join(PUBLIC_DIR, "roster-conflicts.log")

VALID_ROLES = ["god", "reporter", "maintainer"] + ["p%d" % i for i in range(1, 10)]

# 完全放行的角色。maintainer 是給「不在對局中、正在維護這套系統的人」用的。
PRIVILEGED = ("god", "maintainer")


def norm(text):
    """正規化成小寫正斜線，讓 Windows 反斜線與大小寫差異不影響比對。"""
    return text.replace("\\", "/").replace("//", "/").lower()


# 每條規則：(代號, 比對片段, 允許的角色)
# 比對片段是正規化後的子字串；命中即視為觸及該保護區。
RULES = [
    ("SECRET",     "game-state/secret",              ("god", "reporter", "maintainer")),
    ("TRANSCRIPT", ".claude/projects",               ("god", "maintainer")),
    ("TRANSCRIPT", ".jsonl",                         ("god", "maintainer")),
    ("GOD_SKILL",  ".claude/skills/god-",            ("god", "maintainer")),
    ("REP_SKILL",  ".claude/skills/reporter-",       ("god", "reporter", "maintainer")),
    ("MEMORY",     ".claude/agent-memory",           ("god", "reporter", "maintainer")),
    ("REF_GOD",    ".claude/agent-reference/god",    ("god", "maintainer")),
    ("REF_REP",    ".claude/agent-reference/reporter", ("god", "reporter", "maintainer")),
    ("REF_SHARED", ".claude/agent-reference/shared", ("god", "reporter", "maintainer")),
    ("CONFIG",     ".claude/settings",               ("god", "maintainer")),
    ("CONFIG",     ".claude/hooks",                  ("god", "maintainer")),
]

# Bash 指令出現這些片段，就視為可能遞迴展開到子目錄，需要做祖先判斷。
# 沒有這道閘門的話，像 `git status .` 這種無害指令會因為 token "." 被誤擋。
RECURSIVE_MARKERS = re.compile(
    r"(^|[\s;|&(])(find|tree|robocopy|xcopy)(\s|$)"
    r"|(^|\s)ls\s+-[a-z]*r"
    r"|--recursive|--include"
    r"|(^|\s)-[a-zA-Z]*[rR][a-zA-Z]*(\s|$)"
    r"|\*\*"
)

# ── 祖先判斷 ────────────────────────────────────────────────────────────
# 保護區的絕對路徑。遞迴型工具若以某個祖先目錄為起點，就會掃進這些地方，
# 因此要用真正的路徑前綴運算判斷 —— 子字串比對分不清
# 「game-state/public」（安全）與「game-state」（會掃進 secret）。
HOME = norm(os.path.expanduser("~"))
_P = norm(PROJECT_DIR)

PROTECTED_ABS = [
    ("SECRET",     _P + "/game-state/secret",             ("god", "reporter", "maintainer")),
    ("TRANSCRIPT", HOME + "/.claude/projects",            ("god", "maintainer")),
    ("GOD_SKILL",  _P + "/.claude/skills/god-",           ("god", "maintainer")),
    ("REP_SKILL",  _P + "/.claude/skills/reporter-",      ("god", "reporter", "maintainer")),
    ("MEMORY",     _P + "/.claude/agent-memory",          ("god", "reporter", "maintainer")),
    ("REF_GOD",    _P + "/.claude/agent-reference/god",   ("god", "maintainer")),
    ("REF_REP",    _P + "/.claude/agent-reference/reporter", ("god", "reporter", "maintainer")),
    ("REF_SHARED", _P + "/.claude/agent-reference/shared", ("god", "reporter", "maintainer")),
    ("CONFIG",     _P + "/.claude/settings",              ("god", "maintainer")),
    ("CONFIG",     _P + "/.claude/hooks",                 ("god", "maintainer")),
]

# 從 Bash 指令抽出像路徑的 token：不是旗標、不是引號包住的搜尋字串
_TOKEN_SPLIT = re.compile(r"[\s;|&()<>]+")


def path_tokens(command):
    out = []
    for t in _TOKEN_SPLIT.split(command):
        t = t.strip("\"'")
        if not t or t.startswith("-"):
            continue
        out.append(t)
    return out


def to_abs(target):
    t = norm(target)
    if re.match(r"^[a-z]:/", t) or t.startswith("/"):
        return t
    if t.startswith("~"):
        return norm(os.path.expanduser(target))
    return norm(os.path.join(PROJECT_DIR, target))


def ancestor_hit(target, role):
    """target 是否為某個此角色無權存取的保護區的祖先目錄。"""
    base = to_abs(target).rstrip("/")
    for code, prot, allowed_roles in PROTECTED_ABS:
        if role in allowed_roles:
            continue
        if prot.startswith(base + "/") or base == "" :
            return code
    return None


def extract_targets(tool_name, tool_input):
    """從 tool_input 取出所有可能指向檔案的字串。

    回傳 (targets, recursive)：
      targets   —— 待比對的字串清單
      recursive —— 這次呼叫是否可能遞迴掃進子目錄
    """
    ti = tool_input if isinstance(tool_input, dict) else {}
    targets = []
    scan_paths = []   # 遞迴掃描的起點，用來做祖先判斷
    recursive = False

    if tool_name in ("Read", "Edit", "Write", "NotebookEdit", "MultiEdit"):
        for k in ("file_path", "notebook_path", "path"):
            if ti.get(k):
                targets.append(str(ti[k]))

    elif tool_name in ("Grep", "Glob"):
        # 這兩個工具本質上就是遞迴的
        recursive = True
        for k in ("path", "pattern", "glob"):
            if ti.get(k):
                targets.append(str(ti[k]))
        # 沒給 path＝掃整個專案，等同以專案根為起點
        scan_paths.append(str(ti.get("path") or PROJECT_DIR))

    elif tool_name == "Bash":
        cmd = str(ti.get("command", ""))
        targets.append(cmd)
        recursive = bool(RECURSIVE_MARKERS.search(cmd))
        if recursive:
            scan_paths.extend(path_tokens(cmd))

    else:
        # 未知工具：把所有字串值都當候選，從嚴處理
        for v in ti.values():
            if isinstance(v, str):
                targets.append(v)

    return targets, scan_paths, recursive


def evaluate(role, tool_name, tool_input):
    """回傳 (allowed, rule_code, detail)。role 為 None 表示未註冊。"""
    targets, scan_paths, recursive = extract_targets(tool_name, tool_input)
    blob = norm(" ".join(targets))

    for code, frag, allowed_roles in RULES:
        if frag in blob:
            if role in allowed_roles:
                return True, None, None
            return False, code, frag

    if recursive:
        for sp in scan_paths:
            code = ancestor_hit(sp, role)
            if code:
                return False, code + "_RECURSIVE", sp

    return True, None, None


DENY_MESSAGE = {
    "SECRET": "game-state/secret/ 是上帝視角資料，只有 god 與 reporter 能存取。",
    "TRANSCRIPT": "session 對話紀錄（.jsonl）只有 god 能讀，那是稽核用途。",
    "GOD_SKILL": ".claude/skills/god-* 屬於主持人，不屬於你。",
    "REP_SKILL": ".claude/skills/reporter-* 屬於 reporter，不屬於你。",
    "MEMORY": ".claude/agent-memory/ 是跨局記憶，玩家沒有跨局記憶（公平性要求）。",
    "REF_GOD": ".claude/agent-reference/god/ 屬於主持人，不屬於你。",
    "REF_REP": ".claude/agent-reference/reporter/ 屬於 reporter，不屬於你。",
    "REF_SHARED": ".claude/agent-reference/shared/ 是主持方的環境筆記，不屬於你。你要的規則在 .claude/rules/，你的情境索引在 .claude/agent-reference/player/。",
    "CONFIG": ".claude/settings.json 與 .claude/hooks/ 是存取控制本身，只有 god 能改。",
    "SECRET_RECURSIVE": "這個掃描範圍會遞迴進入 game-state/secret/。請把範圍縮到 game-state/public/。",
    "TRANSCRIPT_RECURSIVE": "這個掃描範圍會遞迴進入 session 對話紀錄目錄。",
    "GOD_SKILL_RECURSIVE": "這個掃描範圍會遞迴進入主持人的 skill。請把範圍縮小。",
    "REP_SKILL_RECURSIVE": "這個掃描範圍會遞迴進入 reporter 的 skill。請把範圍縮小。",
    "MEMORY_RECURSIVE": "這個掃描範圍會遞迴進入 agent-memory/。請把範圍縮小。",
    "REF_GOD_RECURSIVE": "這個掃描範圍會遞迴進入主持人的參考資料。請把範圍縮小。",
    "REF_REP_RECURSIVE": "這個掃描範圍會遞迴進入 reporter 的參考資料。請把範圍縮小。",
    "REF_SHARED_RECURSIVE": "這個掃描範圍會遞迴進入主持方的環境筆記。請把範圍縮小。",
    "CONFIG_RECURSIVE": "這個掃描範圍會遞迴進入 .claude/ 的受保護區。請把範圍縮到 .claude/rules/。",
}
