---
name: god-dispatch
description: 狼人殺・上帝對玩家發訊的唯一管道。從固定模板渲染訊息，確保中立性與格式一致。GOD 每次要對玩家發訊都必須經由它。僅 GOD 執行。
---

# /dispatch <action> —— 從模板渲染訊息

**上帝對玩家的所有訊息一律經由這裡。不自由撰寫。**

## 為什麼

上一局的上帝在私訊中夾帶了戰術建議（「值得思考的目標」「幾個可以思考的點」「首夜救人是常見打法」），還在轉述時加了形容詞替玩家標記重點。

**那不是主持，那是教學。** 而且因為是每次即興寫的，偏袒是**隨機的** —— 比穩定的偏袒更難察覺。

從模板渲染，就沒有夾帶的縫隙。

## 東西在哪裡

模板與渲染器都在 **`.claude/message-templates/`**，**玩家也讀得到** ——
那是刻意的：公版訊息由玩家自己渲染，而且 `god-neutrality.md` 本來就讓玩家
拿模板監督你，模板藏起來那條監督權就是空的。

模板裡只有插槽沒有值，所以公開它不洩漏任何東西。

## 兩種傳遞方式

| 方式 | 用在哪些 action | 你的上下文裡會有什麼 |
|---|---|---|
| **參數廣播** | 不含機密的公版訊息 | 只有參數與一則**九個人完全相同**的短訊息 |
| **直送** | 含機密的訊息 | 完整訊息本文（無法避免，內容本來就是機密） |

| action | 用途 | 發送方式 | 模板檔 |
|---|---|---|---|
| `notice` | **參數廣播的那一則**（九個人完全相同） | 並行・直送 | `notice.md` |
| `roster` | 名冊廣播 | 並行・**參數廣播** | `open.md` |
| `dawn` | 天亮公告 | 並行・**參數廣播** | `day.md` |
| `ask_speak` | 指派發言 | 依序，一位一位・**參數廣播** | `day.md` |
| `ask_claim` | 補問漏填的身份宣告 | 單點・**參數廣播** | `day.md` |
| `ask_vote` | 收票 | 並行・**參數廣播** | `vote.md` |
| `tally` | 唱票公告 | 並行・**參數廣播** | `vote.md` |
| `eliminated` | 通知出局者 | 單點・**參數廣播** | `vote.md` |
| `game_over` | 終局公布 | 並行・**參數廣播** | `endgame.md` |
| `ask_mvp` | 賽後 MVP | 並行・**參數廣播** | `endgame.md` |
| `abort` | 對局中止 | 並行・**參數廣播** | `abort.md` |
| `deal` | 發牌（身份牌） | 並行（9 玩家）・直送 | `open.md` |
| `night_wolf_open` | 狼人睜眼＋告知隊長＋收暗號 | 並行（狼隊）・直送 | `night.md` |
| `night_wolf_relay` | 隊友暗號轉給隊長 | 單點（隊長）・直送 | `night.md` |
| `night_wolf_plan` | 隊長的決定轉達其他狼 | 並行（非隊長）・直送 | `night.md` |
| `night_seer` | 預言家查驗 | 單點・直送 | `night.md` |
| `night_seer_result` | 查驗結果 | 單點・直送 | `night.md` |
| `night_witch` | 女巫用藥 | 單點・直送 | `night.md` |
| `hunter_shot` | 獵人開槍 | 單點・直送 | `hunter.md` |

不確定某個 action 有哪些插槽：

```bash
python .claude/message-templates/render.py --list
```

## 參數廣播：怎麼做

### 兩步

```bash
# 1. 把這一則的欄位值寫成一個參數檔（用 Write 直接寫，不需要腳本）
#    game-state/public/mailbox/d2-vote/params.json

# 2. 渲染那一則指路訊息 —— 只渲染一次
python .claude/message-templates/render.py notice --params <notice 的參數>
```

然後**把第 2 步印出來的那個字串，原封不動送給每一位**。

### 為什麼只渲染一次

`notice` 模板**沒有 `{{seat}}`** —— 座位由玩家自己代入命令列。
所以九個人拿到的字完全相同，你的上下文裡只會出現一份。

**不要為了「比較親切」而在 notice 裡加上收件人的名字或任何因人而異的欄位** ——
那會讓它變成九份不同的訊息，這一整套優化就沒了。

### 參數檔長什麼樣

`common` 是大家一樣的、`recipients` 只寫每個人不一樣的：

```json
{
  "common": { "day": "2", "alive_count": "8", "hunter_shot_line": null },
  "recipients": [
    { "to": "P6", "your_position": "1" },
    { "to": "P7", "your_position": "2" }
  ]
}
```

只有一位收件人時可以直接攤平，不必包 `common`／`recipients`。

### 參數檔用腳本產：`params.py`

`dawn`、`ask_speak`、`ask_vote`、`tally`（連同 `eliminated`）四種不要手寫，跑：

```bash
python .claude/skills/god-dispatch/params.py dawn  --day N [--dead Px,Py] [--start Px --direction 順序|逆序]
python .claude/skills/god-dispatch/params.py speak --day N --n <位次> [--pk Px,Py]
python .claude/skills/god-dispatch/params.py vote  --day N [--pk Px,Py]
python .claude/skills/god-dispatch/params.py tally --day N --votes <票.json> [--pk Px,Py] [--write-nightlog]
```

它寫好 `mailbox/<tag>/params.json`，並印出**收件人清單**。照清單送，不要自己列：

- **收件人只取 `secret/roles.json` 的 `alive`**，不從 roster 取。夜間死者另列
  `eliminated_recipients`，送 `eliminated`（`d{N}-nout`），不送天亮公告
- **唱票剝掉「槍口：」行**，只在終端機印 `hunter_declarations`
- **票數必須等於投票人數**，對不上就拒絕產檔

起始位與方向省略時由腳本隨機決定。腳本**不改存活名單**，死亡與出局結算仍由你寫。
其餘 action（`roster`、`ask_claim`、`game_over`、`ask_mvp`、`abort`）照下面的格式手寫。

### 這幾個欄位不要自己填 —— 腳本會算

| 欄位 | 從哪裡算出來 |
|---|---|
| `alive_count` | 數 `alive_list` 裡的座位。**你自己填了但與它算的不一致，會直接拒絕渲染** |
| `your_position`／`n` | 這位玩家在 `speech_order` 裡的位置 |
| `total` | `speech_order` 裡的座位總數 |

**所以大部分公版訊息的參數是扁平的，根本不需要 `recipients` 陣列** ——
每個人不一樣的那幾個欄位，腳本從 `speech_order` 就推得出來。

`dawn` 是最好的例子：參數扁平只有 277 字，而且**你完全不必渲染它**，
玩家各自渲染出自己的順位。舊做法是你生成 8 份完整訊息共 2568 字。

> 沒給 `speech_order` 就不推導 —— 寧可讓「插槽沒填」的檢查擋下來，
> 也不要猜一個看起來合理的值。你手動填的值永遠優先。

三條規則：

- recipient 的欄位**覆蓋** `common` 的同名欄位
- `to` 同時填進 `{{seat}}`（模板沒有 `{{seat}}` 就自動忽略）
- 值寫 `null` → **整行省略**。`{{leader_note}}`、`{{assignments}}`、
  `{{hunter_shot_line}}`、`{{timeout_note}}` 這類「留空就整行不要」的插槽用它。
  想留白但保留該行，寫空字串 `""`

參數檔放在 `game-state/public/mailbox/<tag>/params.json`，`tag` 帶階段
（`d2-dawn`／`d2-speak-3`／`d2-vote`／`open-roster`／`end-gameover`…），
**避免玩家渲染出上一輪的內容**。

`ask_speak` 是依序一位一位的，`filed_list` 每輪都會變，所以它**每一輪各寫一份參數檔**。

### 玩家那一端

他照 notice 裡的指令跑：

```bash
python .claude/message-templates/render.py dawn --seat P3 --params game-state/public/mailbox/d2-dawn/params.json
```

印出來就是完整訊息，四要素一項都不少。渲染失敗他會回報你，**不會自己猜內容**。

## 機密的那八則：inline JSON，仍然由玩家自己渲染

`deal`、`night_*`、`hunter_shot` 走這條。**它們的參數本身就是機密**
（身份牌、隊友名單、查驗結果、今晚被刀者），而且**收件人有時也是機密**
—— 收到 `night_seer` 的人就是預言家，收到 `hunter_shot` 的人就是獵人。

所以參數**不能放進公開的 mailbox**。但這不代表要你自己渲染 ——
**把 JSON 寫進點對點私訊就好，渲染還是玩家做。**

```
【上帝私訊・發牌】P<n>，請自己渲染你的身份牌。參數是機密，不要外洩。

python .claude/message-templates/render.py deal --seat P<n> --params '<這位的 JSON>'

跑不動就對照公開模板自己把值代進去，做法見 `/player-inbox`。
```

`render.py --params` **同時接受檔案路徑與 JSON 字串**，所以這一條不需要任何額外機制。

**你自己不要先渲染一遍再貼全文。** 那等於把同一份內容產出兩次，
九個人就是十八次 —— 舊做法的發牌訊息每則 1953 字，而其中真正機密的
只有 41～130 字，其餘全是玩家自己讀得到的公開內容。

> 落檔（`--out`）受同一條限制，而且是**腳本強制**的：
> 可落檔的清單硬編在 `render.py` 的 `FILE_OK` 裡，對其餘 action 一律拒絕、
> 一個檔都不產生。打錯一個 action 名就被擋下來，不必依賴你有沒有讀到這張表。

## 渲染後必跑的四項檢查

1. **白名單對應**：每一段都能對應到 `rules/god-neutrality.md` 白名單的六類之一
2. **禁用詞掃描 0 命中**：
   ```
   參考思路  值得思考  供你權衡  可以思考的點  你需要處理
   建議你    常見打法  供你判斷  幾個可以思考  你的處境
   ```
3. **逐字稿是原文**：與 `game-state/public/03-speeches-dayN.md` 逐字相同，**不摘要**
4. **無形容詞化轉述**：不出現「他直接對你喊話」「最鋒利的一擊」這類替玩家標記重點的句子

**第 2 項由腳本代跑**（連同插槽完整性、以及參數裡有沒有模板用不到的欄位）。
**第 1、3、4 項機器判不了，你自己看。**

任一項不過 → **不要送出**，回頭修模板。

> 參數廣播的訊息本文你不會看到 —— 那正是重點。第 1、3、4 項改成**看參數**：
> 你填進去的值有沒有夾帶評價、有沒有摘要別人的發言。模板本身是固定的，
> 唯一能夾帶東西的地方就是你填的那些值。

## 模板不夠用怎麼辦

**去改對應的那一份 `.claude/message-templates/*.md`**（對所有人一致生效），
不要這一次多寫幾句。

改完跑一次 `--selftest`，確認每個 action 都還取得出模板本文：

```bash
python .claude/message-templates/render.py --selftest
```

> **模板本文是標題之後的第一個圍欄區塊。** 內文本身含有 ``` 的模板（例如 `deal`
> 要玩家建立檔案、`notice` 要玩家跑指令），外層必須用四個反引號 ```` 包起來，
> 否則會被切在半路。

改完在該階段的公開紀錄中記一筆，讓玩家知道模板變過。

## 逐字稿過長時

**不要濃縮。** 改為給公開檔路徑：

```
完整逐字稿在 `game-state/public/03-speeches-day{{day}}.md`，請自行讀取後再發言。
```

濃縮就是選擇，選擇就是偏袒。

## 這條約束不適用於誰

- **對人類使用者的回報**：不經 dispatch，風格依開局參數（中立紀實／沉浸敘事），摘要與分析都是好的
- **終局之後**：底牌公開後可以輕鬆交流、評點、回應致意
