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

# 階段代碼 → 中文顯示。上帝聲明這五個值涵蓋全場。
PHASE_LABEL = {
    "setup": "開局", "night": "夜晚", "day": "白天",
    "vote": "投票", "endgame": "終局",
    # 主持端實際還用了這幾個代碼（宣告的五個沒有涵蓋全場）。
    # 補進來，但保留 phase_label 的未知標記 —— 那個標記正是它們被發現的原因。
    "dawn": "天亮", "speech": "發言輪", "pk": "PK",
    "game_over": "終局",
}


def phase_label(p):
    """未知的階段值一律原樣輸出並標記，不猜一個中文。

    靜默猜測會讓紀錄端的筆誤消失在版面裡；標出來，reporter 才看得見、才通報得了。
    """
    p = (p or "").strip()
    if not p:
        return "—"
    if p in PHASE_LABEL:
        return PHASE_LABEL[p]
    # 已經是中文散文的階段（「開局完成・第一夜前」）本來就讀得懂，原樣輸出。
    # 未知標記的用途是攔住會把英文代碼印進中文報表的值（R18），不是攔中文。
    if any(ord(c) > 0x2E80 for c in p):
        return p
    return "%s（未知代碼）" % p

# 身份宣告 —— 玩家在發言最後一行自己填的 `【宣告】<值>`，上帝原樣搬進逐字稿標題。
# 這是封閉列舉：不在表內的值一律當成沒填（靜默降級），絕不猜測玩家的意思。
CLAIM_TOKENS = ("預言家", "女巫", "獵人", "神職", "平民", "好人", "狼人", "不表態")
CLAIM_CLASS = {
    "預言家": "c-seer", "女巫": "c-witch", "獵人": "c-hunter",
    "神職": "c-god", "平民": "c-vill", "好人": "c-good", "狼人": "c-wolf",
}
# 悍跳 = 狼人宣稱自己是神職。宣稱「平民」「好人」的狼只是普通說謊，不算悍跳。
GOD_CLAIMS = {"預言家", "女巫", "獵人", "神職"}

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
    """從 00-players.md 的表格取座位與顯示名。

    本局已取消暱稱，表格只有座位一欄 —— 這時值是空字串，
    畫面上那一行就不顯示。舊局歸檔的兩欄格式仍然讀得出來。
    """
    out = {}
    for m in re.finditer(r"^\|\s*(P[1-9])\s*\|(?:\s*([^|]*?)\s*\|)?", md, re.M):
        out[m.group(1)] = (m.group(2) or "").strip().strip("*")
    return out


def norm_claim(raw):
    """把宣告值正規化。不在封閉列舉內就回 None —— 靜默降級，不猜。"""
    if not raw:
        return None
    v = raw.strip()
    return v if v in CLAIM_TOKENS else None


def parse_speech_rounds(md):
    """從 03-speeches-dayN.md 取 [(輪次標籤 or None, [(座位, 暱稱, 內文, 宣告), ...]), ...]。

    標題形如 `## P6・風鈴【宣告：預言家】`。
    歷史歸檔的逐字稿可能在每一輪之前多一行 `## 第 1 輪`（舊局留下的格式）；
    現行的發言輪不會產生這種標題 —— 沒有時整份就是一組、標籤為 None，輸出照常。

    只從標題剝掉 `【宣告：X】` 這一個 token，其餘**原樣留在暱稱欄**——
    舊局的標題帶有 `【跳預言家】`、`（最後一位）` 這類公開原文，
    砍掉它們就是吃掉已公開的內容。
    """
    groups = [(None, [])]
    parts = re.split(r"^##\s*(?:\d+\.\s*)?", md, flags=re.M)[1:]
    for p in parts:
        head, _, body = p.partition("\n")
        head = head.strip()
        rm = re.match(r"^第\s*(\S+?)\s*輪\s*$", head)
        if rm:
            groups.append(("第 %s 輪" % rm.group(1), []))
            continue
        m = re.match(r"(P[1-9])[・·．\s]*(.*)", head)
        if not m:
            continue
        rest = m.group(2)
        cm = re.search(r"【宣告[:：]\s*([^】]*)】", rest)
        claim = norm_claim(cm.group(1)) if cm else None
        if cm:
            rest = (rest[:cm.start()] + rest[cm.end():])
        rest = rest.replace("（PK 發言）", "").replace("(PK 發言)", "")
        # 逐字稿檔尾可能接著非發言內容（例如規則變更公告）。那種段落用的是
        # 單井號或三井號標題，不會被 `## ` 的切分吃掉，於是整段落進**最後一則
        # 發言的內文**裡 —— 發言則數仍然正確，所以計數檢查看不出來。
        # 在這裡把內文截到第一個標題行或水平線為止，玩家自己的發言不含這兩種行。
        cut = re.search(r"^(?:#{1,6}\s|-{3,}\s*$)", body, re.M)
        if cut:
            body = body[:cut.start()]
        body = body.strip().strip("-").strip()
        if claim is None:
            # 上帝漏抄進標題時的兜底：掃正文最後那一行玩家自己寫的宣告。
            fb = re.search(r"^【宣告】\s*(\S+)\s*$", body, re.M)
            claim = norm_claim(fb.group(1)) if fb else None
        groups[-1][1].append((m.group(1), rest.strip(), body, claim))
    return [g for g in groups if g[1]]


def parse_speeches(md):
    """攤平版本 —— 不需要輪次分組的地方（例如收集宣告）用這個。"""
    out = []
    for _label, items in parse_speech_rounds(md):
        out.extend(items)
    return out


def speech_rounds(pub, day, is_pk):
    """取該天該輪的發言，回傳與 parse_speech_rounds 相同的結構。

    **優先讀 `03-speeches-dayN.json`** —— 那是 reporter 併檔時同一份資料的
    機器可讀版本（`reporter-collect/collect.py` 產出），省掉一次 Markdown 解析。
    `game-archive/` 的歷史對局沒有它，所以 Markdown 那條路徑必須永遠留著。

    宣告的正規化留在這裡做（`norm_claim`），封閉列舉只有 `CLAIM_TOKENS` 一份 ——
    collect.py 刻意只搬運玩家原本寫了什麼，不自己判斷合不合法。
    """
    stem = "03-speeches-day%d%s" % (day, "-pk" if is_pk else "")
    data = load_json(os.path.join(pub, stem + ".json"))
    items = data.get("speeches") if isinstance(data, dict) else None
    if items:
        return [(None, [(s.get("seat", ""), s.get("nick", ""), s.get("body", ""),
                         norm_claim(s.get("claim_raw")))
                        for s in items])]
    return parse_speech_rounds(read(os.path.join(pub, stem + ".md")))


def collect_claims(pub):
    """掃全部天數的逐字稿，回傳 {座位: [(天, 是否PK, 宣告), ...]}。

    去重規則：與該座位上一筆相同就跳過（宣稱沒變不重複畫），
    改變才新增一筆 —— 所以改口在報表上看得出來。
    「不表態」不收錄，那是「沒有宣稱」而不是一種宣稱。
    """
    claims = {}
    for d in range(1, 10):
        for is_pk in (False, True):
            for _label, items in speech_rounds(pub, d, is_pk):
                for seat, _nick, _body, claim in items:
                    if not claim or claim == "不表態":
                        continue
                    lst = claims.setdefault(seat, [])
                    if lst and lst[-1][2] == claim:
                        continue
                    lst.append((d, is_pk, claim))
    return claims


def parse_reasons(md):
    """從「## 投票理由」段落取 {投票者: 理由原文}。

    上帝寫過兩種版面：理由與票型同表（三欄），以及票型表只有兩欄、
    理由另立一節（每則以 `**P2・青禾 → P5**` 起頭）。後者若不解析，
    票型表會因為欄數不足而整段被丟掉 —— 連同唱票結果一起靜默消失。
    """
    m = re.search(r"##\s*投票理由[^\n]*\n(.*?)(?=\n##|\Z)", md, re.S)
    if not m:
        return {}
    out = {}
    for blk in re.split(r"\n(?=\*\*\s*P[1-9])", m.group(1)):
        head = re.match(r"\*\*\s*(P[1-9])[^*]*\*\*\s*\n(.*)", blk.strip(), re.S)
        if head:
            out[head.group(1)] = head.group(2).strip()
    return out


def parse_votes(md):
    """從 04-votes-dayN.md 的票型表取 [(投票者, 投給, 理由)]。

    票型表可能是兩欄（投票者｜投給）或三欄（多一欄理由）。兩欄時
    理由去「## 投票理由」段落取 —— 用欄數當門檻會讓整張表消失。
    """
    reasons = parse_reasons(md)
    out = []
    for line in md.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        m = re.match(r"(P[1-9])", cells[0])
        if not m:
            continue
        tgt = re.search(r"(P[1-9])", cells[1])
        reason = cells[2] if len(cells) >= 3 and cells[2] else reasons.get(m.group(1), "")
        out.append((m.group(1), tgt.group(1) if tgt else "棄票", reason))
    return out


def parse_tally(md):
    """取唱票結果段落原文。"""
    # 上帝寫過兩種標題：單一的「## 唱票結果」，以及拆成「## 得票」＋「## 裁決」。
    # 兩種都要認 —— 只認一種的後果是整段唱票結果靜默消失，而票型表照常產出，
    # 所以從輸出量完全看不出來（同 R7）。
    out = []
    for head in ("唱票結果", "得票", "裁決"):
        m = re.search(r"##\s*" + head + r"\s*\n(.*?)(?=\n##|\Z)", md, re.S)
        if m and m.group(1).strip():
            out.append(m.group(1).strip())
    return "\n\n".join(out)


def parse_pk_votes(md):
    """從 04-votes-dayN.md 的「## PK」段落取 [(投票者, 投給)] 與唱票摘要原文。

    PK 重投表只有「投票者／對象」兩欄、沒有理由欄，且 PK 者本身不列入重投，
    跟主票表的三欄格式不同，需要獨立解析，否則會漏掉整個 PK 環節。
    """
    m = re.search(r"^##\s*PK.*?\n(.*)", md, re.S | re.M)
    if not m:
        return [], ""
    section = re.split(r"\n##\s", m.group(1))[0]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 2:
            continue
        voter = re.match(r"(P[1-9])", cells[0])
        target = re.search(r"(P[1-9])", cells[1])
        if not voter or not target:
            continue
        rows.append((voter.group(1), target.group(1)))
    summary_m = re.search(r"\*\*(PK[^\*]*)\*\*", section)
    return rows, (summary_m.group(1) if summary_m else "")


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
/* 欄數綁定座位數（--cols 由 seat_grid 依實際人數寫入），不用 auto-fill。
   auto-fill 會依可用寬度自己算欄數：1040px 內容寬 ÷ (118+10) = 8 欄，
   9 個座位就會剩最後一個獨自落到第二列。窄螢幕退成 3 欄 ——
   3 整除 9，同樣不會出現落單的那一格。 */
.seats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
@media (min-width:1000px){
  .seats{grid-template-columns:repeat(var(--cols,9),minmax(0,1fr))}
}
.seat{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:11px 12px}
.seat .n{font-size:17px;font-weight:700}
.seat .nick{font-size:13px;color:var(--muted)}
/* .seat .role 已由 .tag.role-true 取代 —— 真實身分改成標籤，才能跟宣告標籤排在同一列。 */
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
.banner{margin:18px 0 4px;padding:12px 16px;border-radius:8px;font-size:16px;
  border:1px solid var(--line)}
.banner b{font-size:19px}
.banner.good{background:rgba(47,111,79,.12);color:var(--good)}
.banner.evil{background:rgba(168,58,44,.12);color:var(--evil)}
.night{border-left:3px solid var(--accent);padding-left:13px;margin-bottom:16px}
.night h3{margin:0 0 7px;font-size:15px}
.kv{font-size:13px;color:var(--muted)}
.kv b{color:var(--ink)}
.claims{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.claims .tag{margin-left:0}
.tag.c-seer{background:rgba(41,128,185,.16);color:#2980b9}
.tag.c-witch{background:rgba(142,68,173,.16);color:#8e44ad}
.tag.c-hunter{background:rgba(211,84,0,.16);color:#d35400}
.tag.c-god{background:rgba(201,167,92,.20);color:var(--accent)}
.tag.c-vill{background:rgba(127,140,141,.20);color:#7f8c8d}
.tag.c-good{background:rgba(47,111,79,.16);color:var(--good)}
.tag.c-wolf{background:rgba(168,58,44,.16);color:var(--evil)}
/* 真實身分：有外框。宣告：無框。一眼分得出哪個是事實、哪個是他自己說的。 */
.tag.role-true{background:transparent;border:1px solid currentColor;font-weight:800}
.tag.hj{box-shadow:inset 3px 0 0 var(--evil)}
.tag.hj::after{content:" ↯";color:var(--evil)}
@media (prefers-color-scheme:dark){
  :root:not([data-theme=light]) .tag.c-seer{color:#6bb3e0}
  :root:not([data-theme=light]) .tag.c-witch{color:#c08fe0}
  :root:not([data-theme=light]) .tag.c-hunter{color:#f0975a}
  :root:not([data-theme=light]) .tag.c-vill{color:#a8b2b3}
}
footer{margin-top:50px;padding-top:14px;border-top:1px solid var(--line);
  color:var(--muted);font-size:12px}
"""


def claim_tag(seat, day, is_pk, claim, roles, show_roles):
    """一枚身份宣告標籤。

    宣告文字必須 quoted() —— 它是從公開逐字稿標題原樣抄來的字串，
    與發言內文、投票理由同性質，不是 reporter 生成的判斷。
    class 屬性留在 QUOTE 標記外，否則屬性會被 escape 而壞掉樣式。
    """
    cls = CLAIM_CLASS.get(claim, "c-good")
    # 悍跳閘門用 show_roles（= spoiler or result）而不是 spoiler：result 一有值
    # 代表勝負已公告、底牌已揭，那時公開版本來就列全員身份，再藏悍跳沒有意義。
    hj = show_roles and roles.get(seat) == WOLF and claim in GOD_CLAIMS
    return '<span class="tag %s%s">D%s%s %s</span>' % (
        cls, " hj" if hj else "", day, "PK" if is_pk else "", quoted(claim))


def role_tag(role):
    """一枚真實身分標籤。加外框以便和宣告標籤區分 —— 有框的是事實，無框的是他自己說的。

    文字由 roles.json 來、不是公開檔抄的，所以**不包 quoted()**；
    它只出現在 show_roles 為真時（劇透版，或勝負已公告的終局公開版），
    那兩種情境防劇透掃描本來就不作用。
    """
    return '<span class="tag role-true" style="color:%s">%s</span>' % (
        ROLE_COLOR.get(role, "#888"), esc(role))


def seat_grid(seats, alive, dead_reason, roles, spoiler, show_roles, claims):
    # 欄數 = 實際座位數，換板子（人數不同）也不會有落單的那一格。
    out = ['<div class="seats" style="--cols:%d">' % (len(seats) or 9)]
    for s in sorted(seats, key=lambda x: int(x[1:])):
        cls = "seat" if s in alive else "seat dead"
        out.append('<div class="%s">' % cls)
        out.append('<div class="n">%s</div>' % esc(s))
        if seats.get(s):
            out.append('<div class="nick">%s</div>' % quoted(seats[s]))
        # 真實身分永遠是這一列的第一枚標籤，宣告依天數排在它後面。
        # 一眼就能對照「他是什麼」與「他說他是什麼」，順序固定才不必每次重新找。
        cl = claims.get(s) or []
        row = []
        if show_roles and roles.get(s):
            row.append(role_tag(roles[s]))
        for day, is_pk, c in cl:
            row.append(claim_tag(s, day, is_pk, c, roles, show_roles))
        if row:
            out.append('<div class="claims">%s</div>' % "".join(row))
        if cl:
            if show_roles and roles.get(s) == WOLF and any(
                    c in GOD_CLAIMS for _d, _p, c in cl):
                out.append('<div class="fate">悍跳</div>')
        if spoiler and dead_reason.get(s):
            out.append('<div class="fate">%s</div>' % esc(dead_reason[s]))
        out.append("</div>")
    out.append("</div>")
    return "\n".join(out)


def night_panel(nights):
    out = []
    for n in nights:
        out.append('<div class="night"><h3>第 %s 夜</h3>' % esc(n.get("night", "?")))
        # 上帝寫過兩種 schema：巢狀的 wolf_action，以及扁平的
        # wolf_proposals / wolf_target / wolf_rounds。兩種都要讀得到 ——
        # 只認一種的後果是整行靜默消失，而腳本不會報錯。
        wa = n.get("wolf_action") or {}
        rounds = []
        for key in ("round1", "round2"):
            if wa.get(key):
                rounds.append("%s：%s" % (
                    "首輪" if key == "round1" else "次輪",
                    "、".join("%s→%s" % (k, v) for k, v in sorted(wa[key].items()))))
        # 扁平寫法有兩種：單輪一致時是 wolf_proposals；跑到第二輪時改成
        # wolf_proposals_round1 / _round2。兩者都要認 —— 只認前者的話，
        # 恰好是「狼隊意見分歧」這種最值得看的夜晚，提案那一行會整段空白。
        if not rounds:
            for key, label in (("wolf_proposals_round1", "首輪"),
                               ("wolf_proposals_round2", "次輪")):
                if n.get(key):
                    rounds.append("%s：%s" % (label, "、".join(
                        "%s→%s" % (k, v) for k, v in sorted(n[key].items()))))
        if not rounds and n.get("wolf_proposals"):
            rounds.append("、".join("%s→%s" % (k, v)
                                    for k, v in sorted(n["wolf_proposals"].items())))
        target = (wa.get("resolved_target") or n.get("wolf_target")
                  or n.get("wolf_kill"))
        method = wa.get("method") or ""
        if not method and n.get("wolf_rounds"):
            method = "%s 輪成立" % n["wolf_rounds"]
        # 兩行分開印，各自有內容才印 —— 合成一行的話，沒有提案的夜晚會留下
        # 「狼隊提案 」這種空白開頭，看起來像壞掉而不像「這一夜沒有這一項」。
        if rounds:
            out.append('<div class="kv">狼隊提案 %s</div>' % esc(" ｜ ".join(rounds)))
        if target:
            out.append('<div class="kv">成立目標 <b>%s</b>%s</div>'
                       % (esc(target), esc("（%s）" % method if method else "")))
        # 新版狼隊長制才有的欄位。舊版的夜晚沒有這些鍵，整段跳過，輸出不變。
        # 這裡刻意用「鍵在不在」而不是「值真不真」來決定要不要顯示 ——
        # 空的隊友暗號與留空的白天分工都是合法且有意義的紀錄，
        # 把它們當成沒有，等於把「他沒有指派」畫成「這件事不存在」。
        if n.get("ruleset"):
            out.append('<div class="kv">適用版本 <b>%s</b></div>' % esc(n["ruleset"]))
        # 隊長欄同樣有兩種拼法：wolf_captain 與 wolf_leader（＋來源 wolf_leader_source）。
        captain = n.get("wolf_captain") or n.get("wolf_leader")
        if captain:
            src = {"random": "上帝隨機指定",
                   "succession": "由接班順位接手"}.get(n.get("wolf_leader_source"), "")
            out.append('<div class="kv">狼隊長 <b>%s</b>%s</div>'
                       % (esc(captain), esc("（%s）" % src if src else "")))
        # 暗號的值有兩種形狀：字串（舊）與字串陣列（新）。兩種都要攤平，
        # 否則陣列會被 %s 印成 Python 的 list 字面值，那不是中文報表該有的東西。
        sig_key = "teammate_signals" if "teammate_signals" in n else (
            "wolf_signals" if "wolf_signals" in n else None)
        if sig_key:
            sig = n.get(sig_key) or {}
            txt = "；".join(
                "%s：%s" % (k, "、".join(v) if isinstance(v, (list, tuple)) else v)
                for k, v in sorted(sig.items())) if sig else "無提交"
            out.append('<div class="kv">隊友暗號 %s</div>' % esc(txt))
        if "succession" in n and n.get("succession") is not None:
            sc = n["succession"]
            # 陣列要攤平，否則 %s 會印出 Python 的 list 字面值（含引號與方括號）。
            if isinstance(sc, (list, tuple)):
                # 空陣列是「只剩一隻狼，沒有人可以接班」——那是一個成立的局面，
                # 不是「隊長沒交」。兩者畫成同一句話會誤導判讀。
                txt = " → ".join(sc) if sc else "無（無其他存活狼人）"
            else:
                txt = str(sc) or "未提交"
            if n.get("succession_default"):
                txt += "（隊長未提交，由上帝依座位號補齊）"
            out.append('<div class="kv">接班順位 %s</div>' % esc(txt))
        # 第三種拼法：assignments。鍵名每一局都可能換，一律相容 ——
        # 只認一種的代價是整行靜默消失，而腳本不會報錯。
        da_key = next((k for k in ("day_assignments", "day_roles", "assignments")
                       if k in n), None)
        if da_key:
            da = n.get(da_key)
            if isinstance(da, dict) and da:
                # 值也可能是座位陣列（day_roles 的形狀），一併攤平。
                txt = "、".join(
                    "%s：%s" % (k, "、".join(v) if isinstance(v, (list, tuple)) else v)
                    for k, v in sorted(da.items()))
            else:
                txt = da if isinstance(da, str) and da.strip() else "未指派"
            out.append('<div class="kv">白天分工 %s</div>' % esc(txt))
        se = n.get("seer") or {}
        if se.get("target"):
            # 紀錄端未必記行動者。缺了就省略座位號，不要印「?」——
            # 問號看起來像資料損壞，但「沒記」與「壞了」是兩回事。
            who = se.get("actor") or se.get("by")
            out.append('<div class="kv">預言家%s查驗 <b>%s</b> → <b>%s</b></div>'
                       % (esc(" %s " % who if who else " "), esc(se["target"]),
                          esc(se.get("result") or "—")))
        wi = n.get("witch") or {}
        if wi.get("action"):
            # "none"／"skip" 代表不用藥。沒有這一行的話，未落在對照表的值會被
            # 原樣印進 HTML，畫面上出現「使用 none」這種不是中文的字樣。
            label = {"antidote": "解藥", "poison": "毒藥",
                     "none": "不用藥", "skip": "不用藥",
                     "no_action": "不用藥"}.get(wi["action"], wi["action"])
            who = esc(" %s " % (wi.get("actor") or wi.get("by"))
                      if (wi.get("actor") or wi.get("by")) else " ")
            # target 可能是 null（不用藥的那一夜）。用 .get(k, 預設) 取不到預設，
            # 因為鍵存在、值是 None —— 那個 None 會直接被印進 HTML。
            tgt = wi.get("target") or ""
            if "不用" in label or "不用藥" == label:
                out.append('<div class="kv">女巫%s<b>%s</b></div>' % (who, esc(label)))
            else:
                out.append('<div class="kv">女巫%s使用 <b>%s</b> → %s</div>'
                           % (who, esc(label), esc(tgt or "—")))
        # 開槍同樣用鍵的有無當閘門：null 代表「這一夜結算過，沒有觸發開槍」，
        # 那是一項真實的紀錄，不是「這件事不存在」。
        hs_key = next((k for k in ("hunter_shot", "hunter") if k in n), None)
        if hs_key:
            hs = n.get(hs_key)
            if isinstance(hs, dict):
                hs = "%s → %s" % (hs.get("actor") or hs.get("by") or "?",
                                  hs.get("target") or "—")
            out.append('<div class="kv">獵人開槍 <b>%s</b></div>'
                       % esc(hs if hs else "未觸發"))
        deaths = n.get("deaths") or []
        out.append('<div class="kv">結果 <b>%s</b></div>'
                   % esc(n.get("outcome") or n.get("note")
                          or ("、".join(deaths) if deaths else "平安夜")))
        out.append("</div>")
    return "\n".join(out)


def public_nights(nights):
    """公開版的夜晚結果：只有「誰死了」，不含死因、不含任何夜間行動。

    界線與座位格一致 —— 死亡是上帝已經公告過的公開資訊，死因不是。
    """
    out = []
    for n in nights:
        deaths = n.get("deaths") or []
        who = "、".join(deaths) if deaths else "平安夜，無人死亡"
        out.append('<div class="kv">第 %s 夜　<b>%s</b></div>'
                   % (esc(n.get("night", "?")), esc(who)))
    return '<div class="panel">%s</div>' % "\n".join(out)


def parse_timeline(text):
    """把 01-timeline.md 切成 [(標題, [條目, ...]), ...]。

    標題認 '## ' 與 '# ' 兩種層級（紀錄端的寫法會演化，見 R7/R8/R14）；
    條目認 '- ' 與 '* '。整份是公開檔原文，渲染時一律包 quoted()。

    第三種寫法是**表格**（| 天數 | 階段 | 事件 |）——只認清單的話整個時間軸會
    靜默消失（同 R19：那一塊不是空的，是根本不存在，逐塊確認也看不見它缺席）。
    表格以第一欄分組，其餘欄位以「—— 」串成條目。
    """
    if not text:
        return []
    out = []
    cur = None
    groups = {}
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            # 表頭與分隔列不是事件。分隔列全是 --- 之類的符號。
            if len(cells) < 2 or all(re.fullmatch(r"[-: ]*", c) for c in cells):
                continue
            if cells[0] in ("天數", "時間", "階段"):
                continue
            key = cells[0]
            if key not in groups:
                groups[key] = (key, [])
                out.append(groups[key])
            groups[key][1].append("　—— ".join(c for c in cells[1:] if c))
            continue
        m = re.match(r"^#{1,3}\s+(.*)$", s)
        if m:
            title = m.group(1).strip()
            # 檔案自己的大標（「時間軸」）不當成一個階段。
            if title in ("時間軸", "時間線"):
                cur = None
                continue
            cur = (title, [])
            out.append(cur)
            continue
        m = re.match(r"^[-*]\s+(.*)$", s)
        if m:
            # 第四種寫法：只有檔案大標，條目直接掛在底下，沒有任何階段小標。
            # 沒有這個預設分組的話，整份時間軸會靜默消失（同 R21）。
            if cur is None:
                cur = ("紀錄", [])
                out.append(cur)
            cur[1].append(m.group(1).strip())
    return [(t, items) for t, items in out if items]


def timeline_panel(entries):
    out = []
    for title, items in entries:
        out.append('<div class="kv"><b>%s</b></div>' % quoted(title))
        out.append("<ul>%s</ul>"
                   % "".join("<li>%s</li>" % quoted(i) for i in items))
    return '<div class="panel">%s</div>' % "\n".join(out)


def collect_intros(pub, seats):
    """讀 intro-inbox/ 的九份自介。回傳 [(座位, 內文), ...]，依座位號排序。

    每檔的第一行是 '# Pn・暱稱' 標題，其餘為內文。缺檔就跳過 ——
    自介是玩家自己落檔的，沒落檔是合法狀態，不是資料損壞（R15：缺資料省略，不填問號）。
    """
    d = os.path.join(pub, "intro-inbox")
    if not os.path.isdir(d):
        return []
    out = []
    for seat in seats:
        text = read(os.path.join(d, "%s.md" % seat))
        if not text:
            continue
        lines = [l.rstrip() for l in text.splitlines()]
        body = "\n".join(l for l in lines if l.strip() and not l.startswith("#"))
        if body.strip():
            out.append((seat, body.strip()))
    return out


def build(game_dir, spoiler, roles, alive, dead_reason, seats, day, phase, nights,
          result=None, potions=None):
    # result 有值 = 勝負已定。此時底牌本來就已公開，公開版也顯示身份。
    # 夜間行動與死因不在此列 —— 那是夜間原始資料，終局後仍不進公開版。
    show_roles = bool(spoiler or result)
    pub = os.path.join(game_dir, "public")
    claims = collect_claims(pub)
    title = "狼人殺戰況" + ("・上帝視角" if spoiler else "")
    h = ["<title>%s</title><style>%s</style>" % (title, CSS)]
    h.append('<div class="wrap"><header><h1>%s</h1>' % title)
    h.append('<div class="sub">產生時間 %s ｜ 資料來源 %s</div></header>'
             % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), esc(game_dir)))
    if result:
        h.append('<div class="banner %s"><b>%s陣營獲勝</b>%s</div>'
                 % ("evil" if result.get("winner") == WOLF else "good",
                    esc(result.get("winner", "?")),
                    ("　—— %s（第 %s 天）" % (esc(result.get("reason", "")),
                                              esc(result.get("day", "?")))
                     if result.get("reason") else "")))
    h.append('<div class="bar">')
    h.append('<div class="chip">第 <b>%s</b> 天</div>' % esc(day))
    h.append('<div class="chip">階段 <b>%s</b></div>' % esc(phase_label(phase)))
    h.append('<div class="chip">存活 <b>%d</b> / %d</div>' % (len(alive), len(seats) or 9))
    if show_roles:
        wolves = [s for s in seats if roles.get(s) == WOLF]
        wa = [s for s in wolves if s in alive]
        h.append('<div class="chip">狼 <b>%d</b> / %d 存活</div>' % (len(wa), len(wolves)))
    # 藥水與開槍狀態只進劇透版（02-render.md 的版面規格）。
    # 用「鍵在不在」決定顯示，不用「值真不真」—— False 是有意義的值（尚未使用），
    # 若照真假寫，整排狀態會在最該顯示的開局階段整個消失（L27／R12）。
    if spoiler and isinstance(potions, dict):
        # 獵人開槍的鍵名紀錄端有兩種拼法（hunter_fired / hunter_shot_used），
        # 兩種都認 —— 只認一種時那一格會靜默消失（R14／R17）。
        for keys, label in ((("antidote_used",), "解藥"),
                            (("poison_used",), "毒藥"),
                            (("hunter_fired", "hunter_shot_used"), "獵人開槍")):
            key = next((k for k in keys if k in potions), None)
            if key:
                h.append('<div class="chip">%s <b>%s</b></div>'
                         % (esc(label), "已使用" if potions[key] else "未使用"))
    h.append("</div>")
    h.append("<h2>座位</h2>")
    h.append(seat_grid(seats, alive, dead_reason, roles, spoiler, show_roles, claims))
    tl = parse_timeline(read(os.path.join(pub, "01-timeline.md")))
    if tl:
        h.append("<h2>時間軸</h2>")
        h.append(timeline_panel(tl))
    intros = collect_intros(pub, seats)
    if intros:
        h.append("<h2>自我介紹</h2>")
        for seat, body in intros:
            tag = role_tag(roles[seat]) if (show_roles and roles.get(seat)) else ""
            h.append("<details><summary>%s・%s%s</summary>"
                     '<div class="body"><p>%s</p></div></details>'
                     % (esc(seat), quoted(seats.get(seat, "")), tag, quoted(body)))
    if nights:
        if spoiler:
            h.append("<h2>夜間行動</h2>")
            h.append(night_panel(nights))
        else:
            h.append("<h2>夜晚結果</h2>")
            h.append(public_nights(nights))
    def mark(s):
        if show_roles and roles.get(s):
            c = "e" if roles[s] == WOLF else "g"
            return '%s<span class="tag %s">%s</span>' % (esc(s), c, esc(roles[s]))
        return esc(s)

    def speech_block(seat, nick, body, claim=None):
        # 順序與座位格一致：真實身分在前，宣告在後。
        tag = ""
        if show_roles and roles.get(seat):
            tag += role_tag(roles[seat])
        if claim and claim != "不表態":
            tag += '<span class="tag %s">%s</span>' % (
                CLAIM_CLASS.get(claim, "c-good"), quoted(claim))
        return ("<details><summary>%s・%s%s</summary>"
                '<div class="body"><p>%s</p></div></details>'
                % (esc(seat), quoted(nick), tag, quoted(body)))

    for d in range(1, 10):
        rounds = speech_rounds(pub, d, False)
        vt = read(os.path.join(pub, "04-votes-day%d.md" % d))
        pk_rounds = speech_rounds(pub, d, True)
        if not rounds and not vt and not pk_rounds:
            continue
        h.append("<h2>第 %d 天</h2>" % d)
        for label, items in rounds:
            # 只有歷史歸檔的舊逐字稿才有輪次標籤；現行發言輪是單一組、label 為 None，輸出不變。
            if label:
                h.append("<h3>%s</h3>" % esc(label))
            for seat, nick, body, claim in items:
                h.append(speech_block(seat, nick, body, claim))
        rows = parse_votes(vt)
        if rows:
            h.append('<div class="panel"><div class="scroll"><table>')
            h.append("<tr><th>投票者</th><th>投給</th><th>理由</th></tr>")
            for voter, target, reason in rows:
                h.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                         % (mark(voter), mark(target), quoted(reason)))
            h.append("</table></div>")
            tally = parse_tally(vt)
            if tally:
                h.append('<div class="kv" style="margin-top:10px">%s</div>' % quoted(tally))
            h.append("</div>")
        pk_votes, pk_summary = parse_pk_votes(vt)
        if pk_rounds or pk_votes:
            h.append("<h3>PK</h3>")
            for _label, pk_items in pk_rounds:
                for seat, nick, body, claim in pk_items:
                    h.append(speech_block(seat, nick, body, claim))
            if pk_votes:
                h.append('<div class="panel"><div class="scroll"><table>')
                h.append("<tr><th>投票者</th><th>投給</th></tr>")
                for voter, target in pk_votes:
                    h.append("<tr><td>%s</td><td>%s</td></tr>" % (mark(voter), mark(target)))
                h.append("</table></div>")
                if pk_summary:
                    h.append('<div class="kv" style="margin-top:10px">%s</div>' % quoted(pk_summary))
                h.append("</div>")
    if spoiler:
        tail = "此為劇透版，含全員底牌與夜間行動。存放於受保護目錄，玩家讀不到。"
    elif result:
        tail = "此為終局公開版。勝負已定，底牌已於終局公布，故一併列出；夜間行動仍不收錄。"
    else:
        tail = "此為公開版，只含玩家本來就讀得到的資訊。"
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
    args = sys.argv[1:]
    spoiler_only = "--spoiler-only" in args
    positional = [a for a in args if not a.startswith("--")]
    game_dir = (positional[0] if positional else "game-state").rstrip("/\\")
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
    # 勝負已定才有值。它是「公開版要不要揭底牌」的唯一開關 ——
    # 上帝只在勝負判定達成時才寫入，所以對局中的任何一次渲染都不可能誤揭。
    result = potions.get("result") or None

    dead_reason = {}
    for d in potions.get("dead", []) or []:
        if isinstance(d, dict):
            dead_reason[d.get("seat", "")] = d.get("cause", "")
        elif isinstance(d, str):
            dead_reason[d] = ""

    if not seats:
        print("錯誤：讀不到 %s/00-players.md，無法產生報表。" % pub)
        return 1

    def write_spoiler():
        # 防劇透掃描只作用於公開版，劇透版本來就不掃 —— 這裡沒有漏掉步驟。
        doc = build(game_dir, True, roles, alive, dead_reason, seats, day, phase, nights,
                    result, potions)
        path = os.path.join(sec, "report-spoiler.html")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(strip_markers(doc))
        return path

    if spoiler_only:
        # 結果尚未公告的時刻（夜間收尾、勝負判定當下）只走這條 ——
        # 公開版會標示死者與底牌，早於公告寫出就等於搶在上帝之前公布。
        out_spo = write_spoiler()
        print("劇透版：%s（%d 位元組）" % (out_spo, os.path.getsize(out_spo)))
        print("（--spoiler-only：未產生公開版）")
        return 0

    pub_doc = build(game_dir, False, roles, alive, dead_reason, seats, day, phase, nights,
                    result, potions)
    if result:
        # 終局揭底是刻意的，此時掃描必然整片命中，跳過它。
        hits = []
    else:
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

    out_spo = write_spoiler()

    print("公開版：%s（%d 位元組）" % (out_pub, os.path.getsize(out_pub)))
    print("劇透版：%s（%d 位元組）" % (out_spo, os.path.getsize(out_spo)))
    print("防劇透掃描：%s" % ("跳過（終局揭底）" if result else "0 命中"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
