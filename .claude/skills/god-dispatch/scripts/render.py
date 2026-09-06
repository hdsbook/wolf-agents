# -*- coding: utf-8 -*-
"""批次渲染上帝發給玩家的訊息。

用法：
    python .claude/skills/god-dispatch/scripts/render.py --list
    python .claude/skills/god-dispatch/scripts/render.py <action> <payload.json>
    python .claude/skills/god-dispatch/scripts/render.py --selftest

payload.json：
    {
      "common":     { "day": "2", "alive_count": "7", "alive_list": "P1、P2、…" },
      "recipients": [ { "to": "P1", "your_position": "1" },
                      { "to": "P3", "your_position": "2" } ]
    }

規則
    * recipient 的欄位覆蓋 common 的同名欄位。
    * "to" 同時填入 {{seat}}（recipient 另給 seat 時以 seat 為準）。
    * 值為 null → **整行省略**（給 leader_note、assignments 這類選填行用）。
    * 值為 ""   → 留空但保留該行。

腳本會擋下三件事，任一不過就整批不輸出（渲染四項檢查的第 2 項與插槽完整性）：
    1. 有插槽沒填（渲染後還留著 {{...}}）
    2. 命中中立性禁用詞
    3. payload 給了模板沒有的欄位（通常是打錯欄位名）

檢查 1／3／4（白名單對應、逐字稿是原文、無形容詞化轉述）仍然要你自己看。
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'references')

BANNED = ['參考思路', '值得思考', '供你權衡', '可以思考的點', '你需要處理',
          '建議你', '常見打法', '供你判斷', '幾個可以思考', '你的處境']

# --out 只允許這些 action。其餘的**內容或收件人本身含機密**，只能直送：
#   deal（身份牌）、night_*（隊友、查驗結果、今晚被刀者）、
#   hunter_shot（收到的人就是獵人 —— 收件人本身就是機密）。
# 信箱在 game-state/public/ 底下，全場都讀得到，所以這份白名單是硬性的：
# 它是「底牌不會落到公開區」這件事的機制，不是文件上的約定。
FILE_OK = {'roster', 'dawn', 'ask_speak', 'ask_claim', 'ask_vote',
           'tally', 'eliminated', 'game_over', 'ask_mvp', 'abort'}

SLOT = re.compile(r'\{\{([a-z_]+)\}\}')

LF = chr(10)


def load_all():
    """回傳 {action: (模板本文, 註記, 檔名)}。"""
    out = {}
    for fn in sorted(os.listdir(REF)):
        if not fn.endswith('.md'):
            continue
        with io.open(os.path.join(REF, fn), encoding='utf-8') as f:
            lines = f.read().split('\n')
        i = 0
        while i < len(lines):
            m = re.match(r'## `([a-z_]+)`', lines[i])
            if not m:
                i += 1
                continue
            action = m.group(1)
            # 模板 = 標題之後第一個圍欄區塊。CommonMark：N 個反引號開，需 >= N 才關。
            i += 1
            while i < len(lines) and not re.match(r'^`{3,}\s*$', lines[i]):
                i += 1
            if i >= len(lines):
                die('%s：找不到模板圍欄' % action)
            n = len(re.match(r'^(`+)', lines[i]).group(1))
            i += 1
            body = []
            while i < len(lines):
                m2 = re.match(r'^(`{3,})\s*$', lines[i])
                if m2 and len(m2.group(1)) >= n:
                    break
                body.append(lines[i])
                i += 1
            if i >= len(lines):
                die('%s：模板圍欄沒有收尾' % action)
            i += 1
            # 註記 = 緊接其後的引用行
            note = []
            while i < len(lines) and not lines[i].startswith('## '):
                if lines[i].startswith('>'):
                    note.append(lines[i])
                elif lines[i].strip() and not note:
                    pass
                i += 1
            if action in out:
                die('action 重複定義：%s' % action)
            out[action] = ('\n'.join(body).strip('\n'), '\n'.join(note).strip(), fn)
    return out


def die(msg):
    print('✗ ' + msg)
    sys.exit(1)


def render(template, values):
    """回傳 (訊息, 未填插槽清單)。值為 None 的插槽 → 整行省略。"""
    kept = []
    for line in template.split('\n'):
        slots = SLOT.findall(line)
        if any(s in values and values[s] is None for s in slots):
            continue
        kept.append(SLOT.sub(
            lambda m: values[m.group(1)] if m.group(1) in values and values[m.group(1)] is not None
            else m.group(0), line))
    text = '\n'.join(kept)
    return text, sorted(set(SLOT.findall(text)))


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return
    tpls = load_all()

    if args[0] == '--list':
        print('可用的 action（共 %d 個）\n' % len(tpls))
        byfile = {}
        for a, (_, _, fn) in tpls.items():
            byfile.setdefault(fn, []).append(a)
        for fn in sorted(byfile):
            print('  references/%s' % fn)
            for a in sorted(byfile[fn]):
                slots = sorted(set(SLOT.findall(tpls[a][0])))
                print('      %-18s 插槽：%s' % (a, '、'.join(slots) or '（無）'))
        return

    if args[0] == '--selftest':
        for a in sorted(tpls):
            body, note, fn = tpls[a]
            if not body.strip():
                die('%s 模板是空的' % a)
            print('  %-18s %3d 行　%2d 個插槽　註記 %s　（%s）'
                  % (a, body.count('\n') + 1, len(set(SLOT.findall(body))),
                     '有' if note else '無', fn))
        print('\n%d 個 action 全部取得模板本文 ✓' % len(tpls))
        return

    out_dir = None
    if '--out' in args:
        i = args.index('--out')
        if i + 1 >= len(args):
            die('--out 後面要接目錄')
        out_dir = args[i + 1]
        args = args[:i] + args[i + 2:]

    action = args[0]
    if action not in tpls:
        die('沒有這個 action：%s（用 --list 看清單）' % action)
    if len(args) < 2:
        die('缺少 payload.json')
    if out_dir and action not in FILE_OK:
        print('✗ `%s` 不可以落檔 —— 它的內容或收件人本身含機密。' % action)
        print('  信箱在 game-state/public/ 底下，全場都讀得到。')
        print('  這一則請直送（不加 --out）。')
        print('  可落檔的 action：%s' % '、'.join(sorted(FILE_OK)))
        sys.exit(1)

    body, note, fn = tpls[action]
    with io.open(args[1], encoding='utf-8') as f:
        payload = json.load(f)
    common = payload.get('common', {})
    recipients = payload.get('recipients') or []
    if not recipients:
        die('payload 沒有 recipients')

    known = set(SLOT.findall(body))
    problems = []
    rendered = []
    for r in recipients:
        to = r.get('to')
        if not to:
            problems.append('有一位 recipient 沒有 to 欄位')
            continue
        vals = dict(common)
        vals.update({k: v for k, v in r.items() if k != 'to'})
        # 自動補的 seat 不算使用者給的欄位（廣播型模板可能根本沒有 {{seat}}）
        unknown = sorted(k for k in vals if k not in known)
        vals.setdefault('seat', to)
        if unknown:
            problems.append('%s：payload 有模板用不到的欄位 %s' % (to, '、'.join(unknown)))
        text, missing = render(body, vals)
        if missing:
            problems.append('%s：插槽沒填 %s' % (to, '、'.join('{{%s}}' % s for s in missing)))
        hits = [w for w in BANNED if w in text]
        if hits:
            problems.append('%s：命中禁用詞 %s' % (to, '、'.join(hits)))
        rendered.append((to, text))

    if problems:
        print('✗ 這一批不要送出，先修好以下 %d 項：\n' % len(problems))
        for p in problems:
            print('  - ' + p)
        sys.exit(1)

    if out_dir:
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        for to, text in rendered:
            path = os.path.join(out_dir, to + '.md')
            with io.open(path, 'w', encoding='utf-8', newline=LF) as f:
                f.write(text.rstrip() + LF)
        print('# %s —— %d 則已落檔 → %s' % (action, len(rendered), out_dir))
        print('# 收件人：%s' % '、'.join(to for to, _ in rendered))
        if note:
            print('#')
            print('# 模板註記（渲染前請確認你照做了）')
            for line in note.split(LF):
                print('# ' + line)
        print('#')
        print('# 自動檢查：插槽完整 ✓　禁用詞 0 命中 ✓')
        print('# 仍要你自己看：白名單對應、逐字稿是原文、無形容詞化轉述')
        print('#')
        print('# 下一步：/god-dispatch notice —— 把每個人的 {{mailbox_file}}')
        print('#         指向 %s 底下他自己那一個檔。' % out_dir)
        return

    print('# %s —— %d 則（模板：references/%s）' % (action, len(rendered), fn))
    if note:
        print('\n# 模板註記（渲染前請確認你照做了）')
        for line in note.split('\n'):
            print('# ' + line)
    print('\n# 自動檢查：插槽完整 ✓　禁用詞 0 命中 ✓')
    print('# 仍要你自己看：白名單對應、逐字稿是原文、無形容詞化轉述\n')
    for to, text in rendered:
        print('===== → %s =====' % to)
        print(text)
        print()


if __name__ == '__main__':
    main()
