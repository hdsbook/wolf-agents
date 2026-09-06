# -*- coding: utf-8 -*-
"""把上帝的訊息從固定模板渲染出來。**上帝與玩家共用這一支。**

## 玩家：把上帝給你的參數渲染成完整訊息

上帝廣播時只給你「哪一個模板」與「參數」，訊息本文由你自己渲染 ——
這樣他不必把九份幾乎相同的長訊息生成出來再逐一送出。

    python .claude/message-templates/render.py <action> --seat P3 --params <參數>

`<參數>` 可以是一個 JSON 檔的路徑，也可以是直接貼上的 JSON 字串。
**上帝的訊息裡會寫好完整指令，照抄執行即可。**

渲染不出來（缺參數、找不到你的座位、JSON 壞掉）→ **回報上帝，不要自己猜內容。**

## 上帝：批次渲染

    python .claude/message-templates/render.py <action> --params p.json           # 印出全部
    python .claude/message-templates/render.py <action> --params p.json --out DIR # 寫成檔案

## 參數的兩種寫法

完整寫法，`common` 是大家一樣的、`recipients` 只寫每個人不一樣的：

    {"common": {"day": "2"}, "recipients": [{"to": "P1", "your_position": "1"}]}

只有一位收件人時可以直接攤平，不必包 `common`／`recipients`：

    {"day": "2", "night": "1", "teammates": "Px、Py"}

三條規則：
  * recipient 的欄位覆蓋 common 的同名欄位
  * `to`／`--seat` 同時填進 `{{seat}}`（模板沒有 `{{seat}}` 就自動忽略）
  * 值寫 `null` → **整行省略**；想留白但保留該行，寫空字串 `""`

有三個欄位不必填，腳本會算（手填的值永遠優先）：
  * `alive_count`      ← 數 `alive_list` 裡的座位
  * `your_position`/`n` ← 這位玩家在 `speech_order` 裡的位置
  * `total`            ← `speech_order` 裡的座位總數

## 自動擋下的三件事（任一不過就整批不輸出）

  1. 有插槽沒填（渲染後還留著 `{{...}}`）
  2. 命中中立性禁用詞
  3. 參數裡有模板用不到的欄位 —— 專治打錯欄位名

檢查 1／3／4（白名單對應、逐字稿是原文、無形容詞化轉述）機器判不了，仍要人看。
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

REF = os.path.dirname(os.path.abspath(__file__))

LF = chr(10)

BANNED = ['參考思路', '值得思考', '供你權衡', '可以思考的點', '你需要處理',
          '建議你', '常見打法', '供你判斷', '幾個可以思考', '你的處境']

# --out 只允許這些 action 落檔。其餘的**內容或收件人本身含機密**：
#   deal（身份牌）、night_*（隊友、查驗結果、今晚被刀者）、
#   hunter_shot（收到的人就是獵人 —— 收件人本身就是機密）。
# 落檔的目的地在 game-state/public/ 底下，全場都讀得到，所以這份白名單是硬性的：
# 它是「底牌不會落到公開區」這件事的機制，不是文件上的約定。
#
# 注意這條限制只管**落檔**。把參數放進點對點訊息、由玩家自己渲染，
# 不經過公開區，所以含機密的 action 走那條路是安全的。
FILE_OK = {'roster', 'dawn', 'ask_speak', 'ask_claim', 'ask_vote',
           'tally', 'eliminated', 'game_over', 'ask_mvp', 'abort'}

SLOT = re.compile(r'\{\{([a-z_]+)\}\}')


def die(msg):
    print('✗ ' + msg)
    sys.exit(1)


def load_all():
    """回傳 {action: (模板本文, 註記, 檔名)}。"""
    out = {}
    for fn in sorted(os.listdir(REF)):
        if not fn.endswith('.md'):
            continue
        with io.open(os.path.join(REF, fn), encoding='utf-8') as f:
            lines = f.read().split(LF)
        i = 0
        while i < len(lines):
            m = re.match(r'## `([a-z_]+)`', lines[i])
            if not m:
                i += 1
                continue
            action = m.group(1)
            # 模板 = 標題之後第一個圍欄區塊。
            # CommonMark：N 個反引號開的區塊，要 >= N 個反引號才關得掉 ——
            # 內文本身含有 ``` 的模板（例如 deal）外層用四個反引號包住。
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
            note = []
            while i < len(lines) and not lines[i].startswith('## '):
                if lines[i].startswith('>'):
                    note.append(lines[i])
                i += 1
            if action in out:
                die('action 重複定義：%s' % action)
            out[action] = (LF.join(body).strip(LF), LF.join(note).strip(), fn)
    return out


def render(template, values):
    """回傳 (訊息, 未填插槽清單)。值為 None 的插槽 → 整行省略。"""
    kept = []
    for line in template.split(LF):
        slots = SLOT.findall(line)
        if any(s in values and values[s] is None for s in slots):
            continue
        kept.append(SLOT.sub(
            lambda m: values[m.group(1)] if m.group(1) in values and values[m.group(1)] is not None
            else m.group(0), line))
    text = LF.join(kept)
    return text, sorted(set(SLOT.findall(text)))


def load_params(raw):
    """`--params` 可以是檔案路徑，也可以是直接貼上的 JSON 字串。"""
    text = raw
    if not raw.lstrip().startswith('{'):
        if not os.path.exists(raw):
            die('找不到參數檔：%s' % raw)
        with io.open(raw, encoding='utf-8') as f:
            text = f.read()
    try:
        data = json.loads(text)
    except ValueError as e:
        die('參數不是合法的 JSON：%s' % e)
    if not isinstance(data, dict):
        die('參數的最外層要是一個物件')
    if 'recipients' not in data and 'common' not in data:
        # 攤平寫法：整個物件就是 common，收件人由 --seat 指定
        return dict(data), None
    return dict(data.get('common') or {}), data.get('recipients')


def derive(vals, seat, known):
    """補上能從其他欄位算出來的插槽 —— 上帝就不必逐一列出每個人的值。

    只推導**算得出來、且只有一個答案**的欄位。沒給 `speech_order` 就不推導，
    寧可讓「插槽沒填」的檢查擋下來，也不要猜一個看起來合理的值。
    """
    order = re.findall(r'P[1-9]', vals.get('speech_order') or '')
    pos = str(order.index(seat) + 1) if seat in order else None
    if pos:
        for k in ('your_position', 'n'):
            if k in known and k not in vals:
                vals[k] = pos
    if order and 'total' in known and 'total' not in vals:
        vals['total'] = str(len(order))
    if 'alive_count' in known and 'alive_count' not in vals and vals.get('alive_list'):
        vals['alive_count'] = str(len(re.findall(r'P[1-9]', vals['alive_list'])))


def build_batch(action, body, common, recipients):
    """回傳 (rendered, problems)。rendered 是 [(收件人, 訊息), ...]。"""
    known = set(SLOT.findall(body))
    problems = []
    rendered = []
    for r in recipients:
        to = r.get('to')
        if not to:
            problems.append('有一位收件人沒有 to 欄位')
            continue
        vals = dict(common)
        vals.update({k: v for k, v in r.items() if k != 'to'})
        # 自動補的 seat 不算使用者給的欄位（廣播型模板可能根本沒有 {{seat}}）
        unknown = sorted(k for k in vals if k not in known)
        vals.setdefault('seat', to)
        derive(vals, to, known)
        if unknown:
            problems.append('%s：參數有模板用不到的欄位 %s' % (to, '、'.join(unknown)))
        text, missing = render(body, vals)
        if missing:
            problems.append('%s：插槽沒填 %s' % (to, '、'.join('{{%s}}' % s for s in missing)))
        hits = [w for w in BANNED if w in text]
        if hits:
            problems.append('%s：命中禁用詞 %s' % (to, '、'.join(hits)))
        rendered.append((to, text))
    return rendered, problems


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    tpls = load_all()

    if args[0] == '--list':
        print('可用的 action（共 %d 個）' % len(tpls))
        print('')
        byfile = {}
        for a, (_, _, fn) in tpls.items():
            byfile.setdefault(fn, []).append(a)
        for fn in sorted(byfile):
            print('  %s' % fn)
            for a in sorted(byfile[fn]):
                slots = sorted(set(SLOT.findall(tpls[a][0])))
                print('      %-18s 插槽：%s' % (a, '、'.join(slots) or '（無）'))
        return 0

    if args[0] == '--selftest':
        for a in sorted(tpls):
            body, note, fn = tpls[a]
            if not body.strip():
                die('%s 模板是空的' % a)
            print('  %-18s %3d 行　%2d 個插槽　註記 %s　（%s）'
                  % (a, body.count(LF) + 1, len(set(SLOT.findall(body))),
                     '有' if note else '無', fn))
        print('')
        print('%d 個 action 全部取得模板本文 ✓' % len(tpls))
        return 0

    def opt(name):
        if name in args:
            i = args.index(name)
            if i + 1 >= len(args):
                die('%s 後面要接值' % name)
            return args[i + 1]
        return None

    out_dir = opt('--out')
    seat = opt('--seat')
    params_raw = opt('--params')

    positional = []
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a in ('--out', '--seat', '--params'):
            skip = True
            continue
        if a.startswith('--'):
            continue
        positional.append(a)

    if not positional:
        die('要指定 action（用 --list 看清單）')
    action = positional[0]
    if action not in tpls:
        die('沒有這個 action：%s（用 --list 看清單）' % action)

    if params_raw is None:
        # 舊寫法：render.py <action> <params.json>
        if len(positional) >= 2:
            params_raw = positional[1]
        else:
            die('缺少參數 —— 用 --params <檔案或 JSON 字串>')

    if out_dir and action not in FILE_OK:
        print('✗ `%s` 不可以落檔 —— 它的內容或收件人本身含機密。' % action)
        print('  落檔的目的地在 game-state/public/ 底下，全場都讀得到。')
        print('  這一則把參數放進點對點訊息、讓玩家自己渲染就好（不加 --out）。')
        print('  可落檔的 action：%s' % '、'.join(sorted(FILE_OK)))
        return 1

    body, note, fn = tpls[action]
    common, recipients = load_params(params_raw)

    # ── 玩家模式：只渲染自己那一則 ──────────────────────────────────
    if seat and not out_dir:
        if recipients:
            mine = [r for r in recipients if r.get('to') == seat]
            if not mine:
                die('參數裡找不到 %s 的那一份。請回報上帝，不要自己猜內容。' % seat)
            recipients = mine[:1]
        else:
            recipients = [{'to': seat}]
        rendered, problems = build_batch(action, body, common, recipients)
        if problems:
            print('✗ 渲染不出來，請把下面這幾行原文回報上帝，不要自己補內容：')
            print('')
            for p in problems:
                print('  - ' + p)
            return 1
        print(rendered[0][1])
        return 0

    # ── 上帝模式：批次 ──────────────────────────────────────────────
    if not recipients:
        if seat:
            recipients = [{'to': seat}]
        elif 'seat' not in set(SLOT.findall(body)):
            # 模板沒有 {{seat}} → 每個人拿到的字完全一樣，渲染一次就夠。
            # `notice` 就是這一類：上帝渲染一次，把同一個字串送給所有人。
            recipients = [{'to': '全體'}]
        else:
            die('參數裡沒有 recipients，也沒有給 --seat')

    rendered, problems = build_batch(action, body, common, recipients)
    if problems:
        print('✗ 這一批不要送出，先修好以下 %d 項：' % len(problems))
        print('')
        for p in problems:
            print('  - ' + p)
        return 1

    if out_dir:
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        for to, text in rendered:
            with io.open(os.path.join(out_dir, to + '.md'), 'w',
                         encoding='utf-8', newline=LF) as f:
                f.write(text.rstrip() + LF)
        print('# %s —— %d 則已落檔 → %s' % (action, len(rendered), out_dir))
        print('# 收件人：%s' % '、'.join(to for to, _ in rendered))
    else:
        print('# %s —— %d 則（模板：%s）' % (action, len(rendered), fn))

    if note:
        print('#')
        print('# 模板註記（送出前請確認你照做了）')
        for line in note.split(LF):
            print('# ' + line)
    print('#')
    print('# 自動檢查：插槽完整 ✓　禁用詞 0 命中 ✓')
    print('# 仍要你自己看：白名單對應、逐字稿是原文、無形容詞化轉述')

    if not out_dir:
        print('')
        for to, text in rendered:
            print('===== → %s =====' % to)
            print(text)
            print('')
    return 0


if __name__ == '__main__':
    sys.exit(main())
