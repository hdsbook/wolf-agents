# -*- coding: utf-8 -*-
"""狼人殺戰況報表產生器 —— 由 /reporter-build 執行。

產出兩份自足 HTML：
  game-state/report/index.html          公開版（所有人可讀）
  game-state/secret/report-spoiler.html 劇透版（hook 保護）

用法：
    python render.py [game_dir]
    game_dir 預設 game-state/；歸檔對局傳 game-archive/NNN-日期/ 亦可
    （歸檔目錄的機密目錄名為 god-view/，腳本會自動辨識）
"""
import sys
import os
import re
import json
import html
import datetime

sys.stdout.reconfigure(encoding="utf-8")

ROLE_COLOR = {
    "狼人": "#c0392b", "預言家": "#2980b9", "女巫": "#8e44ad",
    "獵人": "#d35400", "村民": "#7f8c8d", "平民": "#7f8c8d",
}
WOLF = "狼人"

# 逐字引用區的標記 —— 防劇透掃描會把這些區段整段排除。
# 理由：玩家的發言與投票理由本來就充滿「預言家」「狼」等字眼，而那些是
# 已經公開的原文，不是 reporter 生成的內容。對它們掃描只會產生假陽性。
QUOTE_OPEN = "<!--QUOTE-->"
QUOTE_CLOSE = "<!--/QUOTE-->"


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def parse_players(md):
    """從 00-players.md 的表格取座位與暱稱。"""
    out = {}
    for m in re.finditer(r"^\|\s*(P[1-9])\s*\|\s*([^|]+?)\s*\|", md, re.M):
        out[m.group(1)] = m.group(2).strip().strip("*")
    return out


def parse_speeches(md):
    """從 03-speeches-dayN.md 取 [(座位, 暱稱, 內文)]。"""
    out = []
    parts = re.split(r"^##\s*\d+\.\s*", md, flags=re.M)[1:]
    for p in parts:
        head, _, body = p.partition("\n")
        m = re.match(r"(P[1-9])[・·．\s]*(.*)", head.strip())
        if not m:
            continue
        body = body.strip().strip("-").strip()
        out.append((m.group(1), m.group(2).strip(), body))
    return out


def parse_votes(md):
    """從 04-votes-dayN.md 的票型表取 [(投票者, 投給, 理由)]。"""
    out = []
    for line in md.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        m = re.match(r"(P[1-9])", cells[0])
        if not m:
            continue
        tgt = re.search(r"(P[1-9])", cells[1])
        out.append((m.group(1), tgt.group(1) if tgt else "棄票", cells[2]))
    return out


def parse_tally(md):
    """取唱票結果段落原文。"""
    m = re.search(r"##\s*唱票結果\s*\n(.*?)(?=\n##|\Z)", md, re.S)
    return m.group(1).strip() if m else ""


def esc(s):
    return html.escape(str(s))


def quoted(s):
    """包成逐字引用區：內容原樣呈現，且不納入防劇透掃描。"""
    return QUOTE_OPEN + esc(s).replace("\n\n", "</p><p>").replace("\n", "<br>") + QUOTE_CLOSE


CSS = """
:root{
  --bg:#f7f6f3; --panel:#ffffff; --ink:#1c1b19; --muted:#6b6862;
  --line:#e0ddd6; --accent:#8a6d3b; --good:#2f6f4f; --evil:#a83a2c;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme=light]){
    --bg:#16150f; --panel:#1f1e17; --ink:#ece8dd; --muted:#9a958a;
    --line:#33312a; --accent:#c8a75c; --good:#6fbf92; --evil:#e0705f;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.75 "Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:28px 20px 80px}
header{border-bottom:2px solid var(--accent);padding-bottom:14px;margin-bottom:22px}
h1{margin:0 0 6px;font-size:26px;letter-spacing:.04em}
.sub{color:var(--muted);font-size:13px}
.bar{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 26px}
.chip{background:var(--panel);border:1px solid var(--line);border-radius:999px;
  padding:6px 14px;font-size:13px}
.chip b{color:var(--accent)}
h2{font-size:17px;margin:34px 0 12px;padding-left:10px;
  border-left:3px solid var(--accent)}
.seats{display:grid;grid-template-columns:repeat(auto-fill,minmax(118px,1fr));gap:10px}
.seat{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:11px 12px}
.seat .n{font-size:17px;font-weight:700}
.seat .nick{font-size:13px;color:var(--muted)}
.seat .role{font-size:12px;margin-top:5px;font-weight:700}
.seat.dead{opacity:.45}
.seat.dead .n::after{content:" X";color:var(--evil)}
.seat .fate{font-size:11px;color:var(--muted);margin-top:3px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:14px 16px;margin-bottom:12px}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:520px}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:rgba(138,109,59,.09);white-space:nowrap}
details{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  margin-bottom:9px;padding:0 14px}
details[open]{padding-bottom:12px}
summary{cursor:pointer;padding:11px 0;font-weight:700;list-style:none}
summary::-webkit-details-marker{display:none}
.body p{margin:0 0 11px}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:4px;
  margin-left:7px;vertical-align:middle;font-weight:700}
.tag.g{background:rgba(47,111,79,.16);color:var(--good)}
.tag.e{background:rgba(168,58,44,.16);color:var(--evil)}
.night{border-left:3px solid var(--accent);padding-left:13px;margin-bottom:16px}
.night h3{margin:0 0 7px;font-size:15px}
.kv{font-size:13px;color:var(--muted)}
.kv b{color:var(--ink)}
footer{margin-top:50px;padding-top:14px;border-top:1px solid var(--line);
  color:var(--muted);font-size:12px}
"""


def seat_grid(seats, alive, dead_reason, roles, spoiler):
    out = ['<div class="seats">']
    for s in sorted(seats, key=lambda x: int(x[1:])):
        cls = "seat" if s in alive else "seat dead"
        out.append('<div class="%s">' % cls)
        out.append('<div class="n">%s</div>' % esc(s))
        out.append('<div class="nick">%s</div>' % quoted(seats[s]))
        if spoiler and roles.get(s):
            r = roles[s]
            out.append('<div class="role" style="color:%s">%s</div>'
                       % (ROLE_COLOR.get(r, "#888"), esc(r)))
        if spoiler and dead_reason.get(s):
            out.append('<div class="fate">%s</div>' % esc(dead_reason[s]))
        out.append("</div>")
    out.append("</div>")
    return "\n".join(out)


def night_panel(nights):
    out = []
    for n in nights:
        out.append('<div class="night"><h3>第 %s 夜</h3>' % esc(n.get("night", "?")))
        wa = n.get("wolf_action") or {}
        if wa:
            rounds = []
            for key in ("round1", "round2"):
                if wa.get(key):
                    rounds.append("%s：%s" % (
                        "首輪" if key == "round1" else "次輪",
                        "、".join("%s→%s" % (k, v) for k, v in sorted(wa[key].items()))))
            out.append('<div class="kv">狼隊提案 %s<br>成立目標 <b>%s</b>（%s）</div>'
                       % (esc(" ｜ ".join(rounds)), esc(wa.get("resolved_target", "—")),
                          esc(wa.get("method", ""))))
        se = n.get("seer") or {}
        if se.get("target"):
            out.append('<div class="kv">預言家 %s 查驗 <b>%s</b> → <b>%s</b></div>'
                       % (esc(se.get("actor", "?")), esc(se["target"]),
                          esc(se.get("result", "?"))))
        wi = n.get("witch") or {}
        if wi.get("action"):
            label = {"antidote": "解藥", "poison": "毒藥"}.get(wi["action"], wi["action"])
            out.append('<div class="kv">女巫 %s 使用 <b>%s</b> → %s</div>'
                       % (esc(wi.get("actor", "?")), esc(label), esc(wi.get("target", "—"))))
        deaths = n.get("deaths") or []
        out.append('<div class="kv">結果 <b>%s</b></div>'
                   % esc(n.get("outcome") or ("、".join(deaths) if deaths else "平安夜")))
        out.append("</div>")
    return "\n".join(out)


def build(game_dir, spoiler, roles, alive, dead_reason, seats, day, phase, nights):
    pub = os.path.join(game_dir, "public")
    title = "狼人殺戰況" + ("・上帝視角" if spoiler else "")
    h = ["<title>%s</title><style>%s</style>" % (title, CSS)]
    h.append('<div class="wrap"><header><h1>%s</h1>' % title)
    h.append('<div class="sub">產生時間 %s ｜ 資料來源 %s</div></header>'
             % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), esc(game_dir)))
    h.append('<div class="bar">')
    h.append('<div class="chip">第 <b>%s</b> 天</div>' % esc(day))
    h.append('<div class="chip">階段 <b>%s</b></div>' % esc(phase))
    h.append('<div class="chip">存活 <b>%d</b> / %d</div>' % (len(alive), len(seats) or 9))
    if spoiler:
        wolves = [s for s in seats if roles.get(s) == WOLF]
        wa = [s for s in wolves if s in alive]
        h.append('<div class="chip">狼 <b>%d</b> / %d 存活</div>' % (len(wa), len(wolves)))
    h.append("</div>")
    h.append("<h2>座位</h2>")
    h.append(seat_grid(seats, alive, dead_reason, roles, spoiler))
    if spoiler and nights:
        h.append("<h2>夜間行動</h2>")
        h.append(night_panel(nights))
    for d in range(1, 10):
        sp = read(os.path.join(pub, "03-speeches-day%d.md" % d))
        vt = read(os.path.join(pub, "04-votes-day%d.md" % d))
        if not sp and not vt:
            continue
        h.append("<h2>第 %d 天</h2>" % d)
        for seat, nick, body in parse_speeches(sp):
            tag = ""
            if spoiler and roles.get(seat):
                cls = "e" if roles[seat] == WOLF else "g"
                tag = '<span class="tag %s">%s</span>' % (cls, esc(roles[seat]))
            h.append("<details><summary>%s・%s%s</summary>"
                     '<div class="body"><p>%s</p></div></details>'
                     % (esc(seat), quoted(nick), tag, quoted(body)))
        rows = parse_votes(vt)
        if rows:
            h.append('<div class="panel"><div class="scroll"><table>')
            h.append("<tr><th>投票者</th><th>投給</th><th>理由</th></tr>")

            def mark(s):
                if spoiler and roles.get(s):
                    c = "e" if roles[s] == WOLF else "g"
                    return '%s<span class="tag %s">%s</span>' % (esc(s), c, esc(roles[s]))
                return esc(s)

            for voter, target, reason in rows:
                h.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                         % (mark(voter), mark(target), quoted(reason)))
            h.append("</table></div>")
            tally = parse_tally(vt)
            if tally:
                h.append('<div class="kv" style="margin-top:10px">%s</div>' % quoted(tally))
            h.append("</div>")
    tail = ("此為劇透版，含全員底牌與夜間行動。存放於受保護目錄，玩家讀不到。"
            if spoiler else "此為公開版，只含玩家本來就讀得到的資訊。")
    h.append("<footer>%s</footer></div>" % tail)
    return "\n".join(h)


SPOILER_WORDS = "狼人|預言家|女巫|獵人|平民|村民|查驗|毒藥|解藥"


def spoiler_scan(doc):
    """回傳命中清單。逐字引用區整段排除 —— 那些是已公開的玩家原文。"""
    stripped = re.sub(re.escape(QUOTE_OPEN) + ".*?" + re.escape(QUOTE_CLOSE),
                      " ", doc, flags=re.S)
    hits = []
    for m in re.finditer(r"P[1-9]", stripped):
        lo, hi = max(0, m.start() - 14), min(len(stripped), m.end() + 14)
        window = stripped[lo:hi]
        w = re.search(SPOILER_WORDS, window)
        if w:
            hits.append((m.group(0), w.group(0), window.replace("\n", " ")))
    return hits


def strip_markers(doc):
    return doc.replace(QUOTE_OPEN, "").replace(QUOTE_CLOSE, "")


def main():
    game_dir = (sys.argv[1] if len(sys.argv) > 1 else "game-state").rstrip("/\\")
    pub = os.path.join(game_dir, "public")
    sec = os.path.join(game_dir, "secret")
    if not os.path.isdir(sec):
        sec = os.path.join(game_dir, "god-view")

    seats = parse_players(read(os.path.join(pub, "00-players.md")))
    roles_j = load_json(os.path.join(sec, "roles.json"))
    potions = load_json(os.path.join(sec, "potions.json"))
    nightlog = load_json(os.path.join(sec, "nightlog.json"))

    roles = roles_j.get("seats", {})
    alive = potions.get("alive") or roles_j.get("alive") or list(seats)
    day = potions.get("day", roles_j.get("day", "—"))
    phase = potions.get("phase", "—")
    nights = nightlog.get("nights", [])

    dead_reason = {}
    for d in potions.get("dead", []) or []:
        if isinstance(d, dict):
            dead_reason[d.get("seat", "")] = d.get("cause", "")
        elif isinstance(d, str):
            dead_reason[d] = ""

    if not seats:
        print("錯誤：讀不到 %s/00-players.md，無法產生報表。" % pub)
        return 1

    pub_doc = build(game_dir, False, roles, alive, dead_reason, seats, day, phase, nights)
    hits = spoiler_scan(pub_doc)
    if hits:
        print("防劇透掃描：%d 命中 —— 未產生公開版。" % len(hits))
        for seat, word, ctx in hits[:10]:
            print("  %s 附近出現「%s」：…%s…" % (seat, word, ctx.strip()))
        return 2

    out_pub = os.path.join(game_dir, "report", "index.html")
    os.makedirs(os.path.dirname(out_pub), exist_ok=True)
    with open(out_pub, "w", encoding="utf-8") as f:
        f.write(strip_markers(pub_doc))

    spo_doc = build(game_dir, True, roles, alive, dead_reason, seats, day, phase, nights)
    out_spo = os.path.join(sec, "report-spoiler.html")
    with open(out_spo, "w", encoding="utf-8") as f:
        f.write(strip_markers(spo_doc))

    print("公開版：%s（%d 位元組）" % (out_pub, os.path.getsize(out_pub)))
    print("劇透版：%s（%d 位元組）" % (out_spo, os.path.getsize(out_spo)))
    print("防劇透掃描：0 命中")
    return 0


if __name__ == "__main__":
    sys.exit(main())
