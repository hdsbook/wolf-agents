# -*- coding: utf-8 -*-
"""把玩家自己落檔的發言併成逐字稿，並產出給報表用的機器可讀版本。

用法：
    python .claude/skills/reporter-collect/collect.py <天數> <輪次> [選項]

    <輪次>      seq（發言輪）／pk（PK 發言）

選項：
    --game-dir DIR    對局目錄，預設 game-state
    --header "<原文>" 上帝在併檔指示裡給的那一行（發言順序／發言方式）。
                      **原文照抄，不要自己推斷。** 省略時沿用現有逐字稿裡的那一行。
    --expect P2,P3    上帝給的必讀清單。給了就比對，缺誰會列出來。
    --build           併完直接跑 reporter-build/render.py

產出兩份，同一份資料：
    public/03-speeches-day<N>.md    給人看、給歸檔、爭議時引用的權威版本
    public/03-speeches-day<N>.json  給 render.py 讀的版本，省掉一次 Markdown 解析

## 為什麼是「整份重生成」而不是「追加」

每位落檔後都會跑一次，所以同一份檔會被處理很多次。**每次都從 inbox 重新生成整份**，
於是冪等是結構上保證的，不是靠「寫之前先讀現有內容確認誰已經在裡面」的紀律。

順帶消掉了一整類錯誤：追加式寫法一旦把非發言內容接在檔尾，那段會被併進
最後一則發言的內文，而則數仍然正確 —— 計數檢查在原理上抓不到它。

## 這支腳本不做的事

**不改寫任何一個字。** 不修錯字、不調整段落、不歸納、不刪節。
超長的照原文併進去，只是把字數報出來。
**宣告不做判讀** —— 玩家沒寫就是 `未填`，絕不從發言內容推斷他跳了什麼。
"""
import glob
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

LF = chr(10)

# 宣告的封閉列舉只寫在 reporter-build/render.py 一處（CLAIM_TOKENS）。
# 這裡刻意不複製一份 —— 兩處各有一份就是等著漂移。
# 本腳本只負責「原樣搬運玩家寫了什麼」，正規化留給 render.py。

SEAT_RE = re.compile(r'^(P[1-9])$')
CLAIM_LINE = re.compile(r'^【宣告】\s*(\S+)\s*$', re.M)


def die(msg):
    print('✗ ' + msg)
    sys.exit(1)


def read(path):
    try:
        with io.open(path, encoding='utf-8') as f:
            return f.read()
    except (IOError, OSError):
        return ''


def parse_players(md):
    """座位 → 顯示名。與 reporter-build/render.py 的 parse_players 同一條規則。

    本局已取消暱稱，00-players.md 只有座位一欄 —— 這時值是空字串。
    舊局歸檔的兩欄格式仍然讀得出來，不要拿掉這個容錯。
    """
    out = {}
    for m in re.finditer(r'^\|\s*(P[1-9])\s*\|(?:\s*([^|]*?)\s*\|)?', md, re.M):
        out[m.group(1)] = (m.group(2) or '').strip().strip('*')
    return out


def body_chars(body, claim_raw):
    """正文字數：不含空白與換行，最後那行 `【宣告】<值>` 不計入。"""
    text = body
    if claim_raw:
        text = CLAIM_LINE.sub('', text)
    return len(re.sub(r'\s', '', text))


def seat_num(seat):
    return int(seat[1:])


def order_from(text):
    """從一行文字裡依序抽出座位號，作為排列順序。"""
    seen = []
    for s in re.findall(r'P[1-9]', text or ''):
        if s not in seen:
            seen.append(s)
    return seen


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return 0

    def opt(name, default=None):
        if name in args:
            i = args.index(name)
            if i + 1 >= len(args):
                die('%s 後面要接值' % name)
            return args[i + 1]
        return default

    game_dir = opt('--game-dir', 'game-state')
    header_arg = opt('--header')
    expect_arg = opt('--expect')
    do_build = '--build' in args

    positional = []
    skip = False
    for i, a in enumerate(args):
        if skip:
            skip = False
            continue
        if a in ('--game-dir', '--header', '--expect'):
            skip = True
            continue
        if a.startswith('--'):
            continue
        positional.append(a)

    if len(positional) < 2:
        die('用法：collect.py <天數> <輪次 seq|pk>　（--help 看說明）')
    try:
        day = int(positional[0])
    except ValueError:
        die('天數要是數字：%s' % positional[0])
    rnd = positional[1]
    if rnd not in ('seq', 'pk'):
        die('輪次只能是 seq 或 pk，收到：%s' % rnd)

    pub = os.path.join(game_dir, 'public')
    inbox = os.path.join(pub, 'speech-inbox')
    if not os.path.isdir(inbox):
        die('找不到 %s' % inbox)

    stem = '03-speeches-day%d' % day + ('-pk' if rnd == 'pk' else '')
    md_path = os.path.join(pub, stem + '.md')
    json_path = os.path.join(pub, stem + '.json')

    seats = parse_players(read(os.path.join(pub, '00-players.md')))

    # ── 掃 inbox ────────────────────────────────────────────────────
    problems = []
    found = {}
    pattern = os.path.join(inbox, 'd%d-%s-*.md' % (day, rnd))
    for path in sorted(glob.glob(pattern)):
        name = os.path.basename(path)
        m = re.match(r'^d%d-%s-(P[1-9])\.md$' % (day, rnd), name)
        if not m:
            problems.append('檔名不符規則，沒有併入：%s' % name)
            continue
        seat = m.group(1)
        body = read(path).strip()
        if not body:
            problems.append('%s 的檔是空的（%s）' % (seat, name))
            continue
        if seat in found:
            problems.append('%s 在同一輪有兩份檔，我沒有自己選一份' % seat)
            continue
        cm = None
        for cm in CLAIM_LINE.finditer(body):
            pass                      # 取最後一個，正文才是權威來源
        claim_raw = cm.group(1) if cm else None
        if not claim_raw:
            problems.append('%s 沒有寫最後一行的身份宣告（要請上帝補問）' % seat)
        n = body_chars(body, claim_raw)
        if n > 400:
            problems.append('%s 第 %d 天發言 %d 字，超過 400 字上限' % (seat, day, n))
        found[seat] = {
            'seat': seat,
            'nick': seats.get(seat, ''),
            'claim_raw': claim_raw,
            'body': body,
            'chars': n,
            'source': name,
        }

    if not found:
        die('%s 底下沒有第 %d 天 %s 輪的任何發言檔' % (inbox, day, rnd))

    if expect_arg:
        expected = order_from(expect_arg)
        missing = [s for s in expected if s not in found]
        extra = [s for s in found if s not in expected]
        if missing:
            problems.append('上帝的必讀清單有、inbox 裡沒有：%s' % '、'.join(missing))
        if extra:
            problems.append('inbox 裡有、必讀清單沒有：%s' % '、'.join(extra))

    # ── 排列順序 ────────────────────────────────────────────────────
    # 優先用上帝這次給的那一行；沒給就沿用現有逐字稿裡的；再沒有就照座位號。
    old_md = read(md_path)
    header = header_arg
    if header is None:
        for line in old_md.split(LF)[:6]:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('---'):
                header = line
                break

    if rnd == 'pk':
        order = sorted(found, key=seat_num)          # PK 依座位號
    else:
        order = [s for s in order_from(header or '') if s in found]
        order += sorted((s for s in found if s not in order), key=seat_num)

    speeches = [found[s] for s in order]

    # ── 寫逐字稿（整份重生成）────────────────────────────────────────
    parts = ['# 第 %d 天・%s逐字稿' % (day, 'PK 發言' if rnd == 'pk' else '發言'), '']
    if header:
        parts += [header, '']
    parts += ['---', '']
    for s in speeches:
        claim_label = s['claim_raw'] or '未填'
        head = s['seat'] + ('・' + s['nick'] if s['nick'] else '')
        title = '## %s【宣告：%s】' % (head, claim_label)
        parts += [title, '', s['body'], '']

    with io.open(md_path, 'w', encoding='utf-8', newline=LF) as f:
        f.write(LF.join(parts).rstrip() + LF)

    payload = {
        'day': day,
        'round': rnd,
        'header': header,
        'speeches': speeches,
    }
    with io.open(json_path, 'w', encoding='utf-8', newline=LF) as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write(LF)

    # ── 回報 ────────────────────────────────────────────────────────
    print('第 %d 天・%s：併入 %d 則（%s）' % (day, rnd, len(speeches),
                                             '、'.join(s['seat'] for s in speeches)))
    print('  %s' % md_path)
    print('  %s' % json_path)
    if problems:
        print('')
        print('要回報上帝的 %d 項：' % len(problems))
        for p in problems:
            print('  - ' + p)
    else:
        print('  沒有要回報上帝的事。')

    if do_build:
        here = os.path.dirname(os.path.abspath(__file__))
        build = os.path.join(here, '..', 'reporter-build', 'render.py')
        print('')
        # 先把自己的輸出沖出去 —— 否則子行程的輸出會插到併檔報告前面，
        # 讀起來像是報表先於併檔完成。
        sys.stdout.flush()
        rc = subprocess.call([sys.executable, os.path.normpath(build), game_dir])
        if rc != 0:
            print('✗ 報表沒有產生成功（render.py 回傳 %d）' % rc)
            return rc
    return 0


if __name__ == '__main__':
    sys.exit(main())
