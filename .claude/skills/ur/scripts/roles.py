"""角色代號的唯一來源。claim_role.py 與 .claude/hooks/policy.py 都從這裡 import。

放在 skills/ur/scripts/ 而不是 hooks/：玩家 session 要執行 claim_role.py，
而 .claude/hooks/ 對玩家是受保護路徑；反過來 hook 讀這裡不受限制。
只用標準庫、不做任何 I/O，讓兩邊 import 都安全。
"""
import re

NON_PLAYER = ("god", "reporter", "maintainer")
PLAYERS = tuple("p%d" % i for i in range(1, 10))
VALID_ROLES = NON_PLAYER + PLAYERS

# 對局進行中，玩家 session 不得改認領的角色（claim_role.py）
PRIVILEGED_CLAIM = NON_PLAYER


def is_player(role):
    return role in PLAYERS


def normalize_role(raw):
    """god / reporter / maintainer / p1~p9；P3、3 這些寫法都接受。無法解析回傳 None。"""
    r = (raw or "").strip().lower()
    if r in NON_PLAYER:
        return r
    m = re.fullmatch(r"p?([1-9])", r)
    return "p" + m.group(1) if m else None
