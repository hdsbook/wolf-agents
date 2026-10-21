# -*- coding: utf-8 -*-
"""上帝端：產生公版廣播的參數檔（天亮／發言／收票／唱票）。僅 GOD 執行。

不必再手寫 params.json，也不必手算票數。四個子命令：

    python .claude/skills/god-dispatch/params.py dawn  --day 2 --dead P3,P9 [--start P8 --direction 逆序] [--hunter-shot-line 文字]
    python .claude/skills/god-dispatch/params.py speak --day 2 --n 3 [--pk]
    python .claude/skills/god-dispatch/params.py vote  --day 2 [--pk P4,P7]
    python .claude/skills/god-dispatch/params.py tally --day 2 --votes 票.json [--pk P4,P7] [--write-nightlog]

每個子命令都會寫進 game-state/public/mailbox/<tag>/params.json，
並印出一段 JSON：`tag`、參數檔路徑、**收件人清單**、以及要注意的事。

內建三條（第 007 局的教訓 G-G、G-H）：
  1. 收件人只取 secret/roles.json 的 `alive`，絕不從 roster 取。
     夜間死者另外列在 `eliminated_recipients`，發 `eliminated`，不發 dawn。
  2. 唱票時只公開「投票」與「理由」兩行；「槍口：」行一律剝掉，
     只印在終端機（`hunter_declarations`），加 --write-nightlog 才寫進 nightlog.json。
  3. 票數必須等於投票人數（存活人數，PK 時扣掉平票者），少一張、多一張都拒絕產檔。

**這支腳本不改 roles.json／potions.json 的存活名單** —— 出局結算仍是你的事，
它只負責把你已經確定的局面變成參數檔。

--votes 的格式：一個 JSON 檔，鍵是座位、值是該玩家回覆的**原文**：
    {"P1": "投票：P7\\n理由：……", "P2": "投票：棄票\\n理由：……"}
逾時沒回的人，值寫 null（記為棄票、理由「逾時未回覆」）。漏寫某個座位會被拒絕 ——
那通常是你漏收，不是他逾時。
"""
import argparse
import json
import os
import random
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

LF = chr(10)
SEATS = ["P%d" % i for i in range(1, 10)]
GODS = {"預言家", "女巫", "獵人"}
VILLAGER = {"村民", "平民"}
WOLF = "狼人"


def die(msg):
    print("✗ " + msg)
    sys.exit(1)


def seat_list(text):
    if not text or text.strip() in ("", "無", "none"):
        return []
    out = [s.strip().upper() for s in re.split(r"[,、\s]+", text) if s.strip()]
    for s in out:
        if s not in SEATS:
            die("看不懂的座位：%s" % s)
    return out


def by_seat(seats):
    return sorted(seats, key=lambda s: int(s[1:]))


def load(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        die("找不到 %s" % path)
    except json.JSONDecodeError as e:
        die("%s 不是合法 JSON：%s" % (path, e))


class State:
    def __init__(self, root):
        self.root = root
        self.pub = os.path.join(root, "public")
        self.sec = os.path.join(root, "secret")
        self.roles_j = load(os.path.join(self.sec, "roles.json"))
        self.roles = self.roles_j.get("seats", {})
        self.alive = by_seat(self.roles_j.get("alive") or [])
        if not self.alive:
            die("roles.json 的 alive 是空的")

    @property
    def dead(self):
        return [s for s in SEATS if s in self.roles and s not in self.alive]

    def mailbox(self, tag, params):
        d = os.path.join(self.pub, "mailbox", tag)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "params.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(params, f, ensure_ascii=False, indent=2)
            f.write(LF)
        return p.replace(os.sep, "/")

    def dawn_order(self, day):
        p = os.path.join(self.pub, "mailbox", "d%s-dawn" % day, "params.json")
        order = load(p).get("speech_order", "")
        return [s.strip() for s in order.split("→") if s.strip()]


def fmt(seats):
    return " ".join(seats) if seats else "無"


def report(**kw):
    print(json.dumps(kw, ensure_ascii=False, indent=2))


def win_check(roles, alive):
    """屠邊制：神職全滅或平民全滅 → 狼勝；狼全滅 → 好人勝。"""
    alive_roles = [roles.get(s) for s in alive]
    if WOLF not in alive_roles:
        return "達成：好人陣營獲勝（狼人全數出局）。"
    if not any(r in GODS for r in alive_roles):
        return "達成：狼人陣營獲勝（屠邊・神職全滅）。"
    if not any(r in VILLAGER for r in alive_roles):
        return "達成：狼人陣營獲勝（屠邊・平民全滅）。"
    return "未達成，遊戲繼續。"


# ── dawn ────────────────────────────────────────────────────────────
def cmd_dawn(st, a):
    tonight = by_seat(seat_list(a.dead))
    for s in tonight:
        if s in st.alive:
            die("%s 仍在 roles.json 的 alive 裡 —— 先完成夜間死亡結算再產天亮公告" % s)
    if tonight:
        headline = "昨夜 %s 出局" % "、".join(tonight)
        announce = "昨夜出局的是：%s。" % "、".join(tonight)
    else:
        headline, announce = "平安夜", "昨夜是平安夜，無人死亡。"

    start = a.start or random.choice(st.alive)
    if start not in st.alive:
        die("起始位 %s 不在存活名單" % start)
    direction = a.direction or random.choice(["順序", "逆序"])
    if direction not in ("順序", "逆序"):
        die("--direction 只能是 順序 或 逆序")
    ring = st.alive if direction == "順序" else list(reversed(st.alive))
    i = ring.index(start)
    order = ring[i:] + ring[:i]

    params = {
        "day": str(a.day),
        "death_headline": headline,
        "death_announcement": announce,
        "alive_list": fmt(st.alive),
        "dead_list": fmt(st.dead),
        "hunter_shot_line": a.hunter_shot_line,
        "start_seat": start,
        "direction": direction,
        "speech_order": " → ".join(order),
    }
    tag = "d%s-dawn" % a.day
    out = {"tag": tag, "params": st.mailbox(tag, params), "action": "dawn",
           "recipients": st.alive, "speech_order": order}
    if tonight:
        otag = "d%s-nout" % a.day
        out["eliminated_tag"] = otag
        out["eliminated_params"] = st.mailbox(
            otag, {"elimination_reason": "你在第 %s 夜出局。" % a.day})
        out["eliminated_recipients"] = tonight
    report(**out)


# ── speak ───────────────────────────────────────────────────────────
def cmd_speak(st, a):
    order = st.dawn_order(a.day)
    rnd = "pk" if a.pk else "seq"
    if a.pk:
        order = by_seat(seat_list(a.pk))
    if not 1 <= a.n <= len(order):
        die("--n 要在 1～%d 之間" % len(order))
    seat = order[a.n - 1]
    if seat not in st.alive:
        die("%s 不在存活名單（順序：%s）" % (seat, " → ".join(order)))
    inbox = os.path.join(st.pub, "speech-inbox")
    filed, missing = [], []
    for s in order[:a.n - 1]:
        name = "d%s-%s-%s.md" % (a.day, rnd, s)
        (filed if os.path.isfile(os.path.join(inbox, name)) else missing).append(name)
    filed_list = LF.join(filed) if filed else "（你是本日第一位，還沒有人落檔）"
    params = {"day": str(a.day), "alive_list": fmt(st.alive), "dead_list": fmt(st.dead),
              "speech_order": " → ".join(order), "filed_list": filed_list}
    tag = "d%s-%s-%d" % (a.day, "pkspeak" if a.pk else "speak", a.n)
    out = {"tag": tag, "params": st.mailbox(tag, params), "action": "ask_speak",
           "recipients": [seat], "speech_file": "game-state/public/speech-inbox/d%s-%s-%s.md" % (a.day, rnd, seat)}
    if missing:
        out["warning"] = "前面這幾位沒有落檔，必讀清單已略過。若他們不是逾時棄權，先別送：" + "、".join(missing)
    report(**out)


# ── vote ────────────────────────────────────────────────────────────
def cmd_vote(st, a):
    pk = seat_list(a.pk)
    voters = [s for s in st.alive if s not in pk]
    tag = "d%s-%s" % (a.day, "pkvote" if pk else "vote")
    report(tag=tag, params=st.mailbox(tag, {"day": str(a.day), "alive_list": fmt(st.alive)}),
           action="ask_vote", recipients=voters, expected_votes=len(voters))


# ── tally ───────────────────────────────────────────────────────────
VOTE_RE = re.compile(r"^\s*(?:PK)?投票\s*[:：]\s*(\S+)")
WHY_RE = re.compile(r"^\s*理由\s*[:：]\s*(.*)$")
GUN_RE = re.compile(r"^\s*槍口\s*[:：]\s*(\S+)")


def parse_reply(seat, text, pk, alive):
    if text is None:
        return "棄票", "逾時未回覆", None
    vote = why = gun = None
    for line in str(text).splitlines():
        m = VOTE_RE.match(line)
        if m and vote is None:
            vote = m.group(1).strip("。．.").upper()
            continue
        m = WHY_RE.match(line)
        if m and why is None:
            why = m.group(1).strip()
            continue
        m = GUN_RE.match(line)
        if m:
            gun = m.group(1).strip("。．.").upper()
    if vote is None:
        die("%s 的回覆找不到「投票：」那一行，請補問，不要自己猜" % seat)
    if vote != "棄票":
        if vote not in SEATS:
            die("%s 投給看不懂的對象：%s" % (seat, vote))
        if vote not in alive:
            die("%s 投給不在存活名單的 %s" % (seat, vote))
        if pk and vote not in pk:
            die("%s 的 PK 票投給非平票者 %s" % (seat, vote))
    return vote, (why or "（未附理由）").replace("|", "｜").replace(LF, " "), gun



def cmd_tally(st, a):
    pk = seat_list(a.pk)
    voters = [s for s in st.alive if s not in pk]
    raw = load(a.votes)
    extra = sorted(set(raw) - set(voters), key=lambda s: SEATS.index(s) if s in SEATS else 99)
    lack = [s for s in voters if s not in raw]
    if extra:
        die("這些人不該投票（已出局或為平票者）：%s" % "、".join(extra))
    if lack:
        die("漏收這些人的票（逾時請寫 null）：%s" % "、".join(lack))

    rows, count, guns = [], {}, []
    for s in voters:
        vote, why, gun = parse_reply(s, raw[s], pk, st.alive)
        rows.append("| %s | %s | %s |" % (s, vote, why))
        count.setdefault(vote, []).append(s)
        if gun:
            guns.append({"seat": s, "target": gun, "day": int(a.day) if str(a.day).isdigit() else a.day})
    total = sum(len(v) for v in count.values())
    if total != len(voters):
        die("票數 %d ≠ 投票人數 %d" % (total, len(voters)))

    cands = sorted(((k, v) for k, v in count.items() if k != "棄票"),
                   key=lambda kv: (-len(kv[1]), SEATS.index(kv[0])))
    lines = ["%s：%d 票（%s）" % (k, len(v), "、".join(v)) for k, v in cands]
    if "棄票" in count:
        lines.append("棄票：%d 人（%s）" % (len(count["棄票"]), "、".join(count["棄票"])))

    out_seat, next_step = None, None
    if not cands:
        headline, verdict = "全員棄票", "全員棄票，本輪無人出局。"
    else:
        top = len(cands[0][1])
        tied = [k for k, v in cands if len(v) == top]
        if len(tied) == 1:
            out_seat = tied[0]
            headline = "%s 出局" % out_seat
            verdict = "%s 得票最高（%d 票），%s，%s 出局。" % (
                out_seat, top, "PK 結果" if pk else "無平票", out_seat)
        elif pk:
            headline = "PK 再度平票・流局"
            verdict = "%s 再度平票（各 %d 票），本輪流局，無人出局。" % ("、".join(tied), top)
        else:
            headline = "平票・進入 PK"
            verdict = "%s 平票（各 %d 票），進入 PK。" % ("、".join(tied), top)
            next_step = {"pk": tied}

    alive_after = [s for s in st.alive if s != out_seat]
    params = {
        "day": str(a.day),
        "tally_headline": headline,
        "vote_count": str(total),
        "vote_table": LF.join(["| 投票人 | 投給 | 理由 |", "|---|---|---|"] + rows),
        "tally_lines": LF.join(lines),
        "verdict": verdict,
        "alive_list": fmt(alive_after),
        "win_check": win_check(st.roles, alive_after),
    }
    tag = "d%s-%s" % (a.day, "pktally" if pk else "tally")
    out = {"tag": tag, "params": st.mailbox(tag, params), "action": "tally",
           "recipients": st.alive, "tally": {k: len(v) for k, v in cands},
           "eliminated": out_seat}
    if next_step:
        out["next"] = "PK：平票者 %s 各再發言一次（speak --pk），其餘人重投（vote --pk）" % "、".join(next_step["pk"])
    if out_seat:
        vtag = "d%s-out" % a.day
        out["eliminated_tag"] = vtag
        out["eliminated_params"] = st.mailbox(vtag, {
            "elimination_reason": "你在第 %s 天投票中以 %d 票出局。" % (a.day, len(count[out_seat]))})
        out["eliminated_recipients"] = [out_seat]
        out["todo"] = "roles.json／potions.json 的存活名單由你更新；腳本沒有改。"
        if st.roles.get(out_seat) == "獵人":
            out["hunter"] = "出局者是獵人：先問開槍，結算後勝負要重新判定（win_check 是開槍前的結果）。"
    if guns:
        out["hunter_declarations"] = guns  # 機密：只在這裡，不進公開參數檔
        if a.write_nightlog:
            p = os.path.join(st.sec, "nightlog.json")
            nl = load(p)
            nl["hunter_declaration"] = guns[-1]
            with open(p, "w", encoding="utf-8") as f:
                json.dump(nl, f, ensure_ascii=False, indent=2)
                f.write(LF)
            out["nightlog"] = "hunter_declaration 已寫入"
    report(**out)


def main():
    ap = argparse.ArgumentParser(description="上帝端：產公版廣播參數檔")
    ap.add_argument("--state", default="game-state", help="對局目錄（預設 game-state）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("dawn")
    p.add_argument("--day", required=True)
    p.add_argument("--dead", default="", help="昨夜出局者，逗號分隔；平安夜省略")
    p.add_argument("--start", help="起始位（省略 = 隨機）")
    p.add_argument("--direction", help="順序／逆序（省略 = 隨機）")
    p.add_argument("--hunter-shot-line", default=None)

    p = sub.add_parser("speak")
    p.add_argument("--day", required=True)
    p.add_argument("--n", type=int, required=True, help="本日第幾位")
    p.add_argument("--pk", help="PK 發言時給平票者，逗號分隔（依座位序）")

    p = sub.add_parser("vote")
    p.add_argument("--day", required=True)
    p.add_argument("--pk", help="PK 重投時給平票者（他們不投）")

    p = sub.add_parser("tally")
    p.add_argument("--day", required=True)
    p.add_argument("--votes", required=True)
    p.add_argument("--pk")
    p.add_argument("--write-nightlog", action="store_true")

    a = ap.parse_args()
    st = State(a.state)
    {"dawn": cmd_dawn, "speak": cmd_speak, "vote": cmd_vote, "tally": cmd_tally}[a.cmd](st, a)


if __name__ == "__main__":
    main()
