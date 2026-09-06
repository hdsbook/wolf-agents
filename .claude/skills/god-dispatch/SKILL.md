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

## 可用的 action

**模板按階段拆成七份，一次只讀你這一步用得到的那一份。** 不要整包讀進來。

| action | 用途 | 發送方式 | 模板檔 |
|---|---|---|---|
| `notice` | **指路** —— 告訴玩家他的信在哪 | 並行・直送 | `references/notice.md` |
| `deal` | 通訊測試 + 指派暱稱 + 發牌 + 自介落檔與公平競賽承諾 | 並行（9 玩家）・直送 | `references/open.md` |
| `roster` | 名冊廣播 | 並行・**落檔** | `references/open.md` |
| `night_wolf_open` | 狼人睜眼＋告知隊長＋收暗號 | 並行（狼隊）・直送 | `references/night.md` |
| `night_wolf_relay` | 隊友暗號轉給隊長，請他拍板 | 單點（隊長）・直送 | `references/night.md` |
| `night_wolf_plan` | 隊長的決定轉達其他狼 | 並行（非隊長）・直送 | `references/night.md` |
| `night_seer` | 預言家查驗 | 單點・直送 | `references/night.md` |
| `night_seer_result` | 查驗結果 | 單點・直送 | `references/night.md` |
| `night_witch` | 女巫用藥 | 單點・直送 | `references/night.md` |
| `dawn` | 天亮公告 | 並行・**落檔** | `references/day.md` |
| `ask_speak` | 指派發言 | 依序，一位一位・**落檔** | `references/day.md` |
| `ask_claim` | 補問漏填的身份宣告 | 單點・**落檔** | `references/day.md` |
| `ask_vote` | 收票 | 並行・**落檔** | `references/vote.md` |
| `tally` | 唱票公告 | 並行・**落檔** | `references/vote.md` |
| `eliminated` | 通知出局者 | 單點・**落檔** | `references/vote.md` |
| `hunter_shot` | 獵人開槍 | 單點・直送 | `references/hunter.md` |
| `game_over` | 終局公布 | 並行・**落檔** | `references/endgame.md` |
| `ask_mvp` | 賽後 MVP | 並行・**落檔** | `references/endgame.md` |
| `abort` | 對局中止 | 並行・**落檔** | `references/abort.md` |

`hunter.md` 單獨一份，是因為它在夜間結算、天亮、投票出局**三個階段都會用到** ——
放進任何一份階段檔，另外兩個階段就得為了一則模板讀進整份。

不確定某個 action 在哪一份、有哪些插槽：

```bash
python .claude/skills/god-dispatch/scripts/render.py --list
```

它會連每個 action 的插槽名一起列出來，**不必開檔**。

## 落檔＋指路：公版內容不進你的上下文

標**落檔**的那些 action，**不要把內容送給玩家**。改成兩步：

```bash
# 1. 寫進信箱。stdout 只回你一張清單，訊息本文你從頭到尾看不到
python .claude/skills/god-dispatch/scripts/render.py dawn payload.json --out game-state/public/mailbox/d2-dawn/

# 2. 指路。九個人拿到的除了座位與檔名之外完全相同
/god-dispatch notice
```

**順序不可顛倒** —— 先有檔才能指路。

信箱路徑是 `game-state/public/mailbox/<tag>/<座位>.md`，`tag` 帶階段
（`d2-dawn`／`d2-speak-3`／`d2-vote`／`open-roster`／`end-gameover`…），
**避免玩家讀到上一輪的信**。即使九個人內容完全相同也一人一檔 ——
玩家只要記一條規則，不必分辨哪些是共用檔。

`ask_speak` 是依序一位一位的，`filed_list` 每輪都會變，所以它**每一輪各跑一次**。

### 為什麼是這幾則，以及為什麼腳本會擋你

判準不是「公版還是私訊」，是**含不含機密** —— 而且**收件人本身就可能是機密**：
`night_seer` 發給誰，就等於公布了預言家是誰；`hunter_shot` 同理。

信箱在 `game-state/public/` 底下，**全場都讀得到**。所以可落檔的清單
**硬編在 `render.py` 的 `FILE_OK` 裡**，對其餘 action 一律拒絕、一個檔都不產生。
這讓「底牌不會落到公開區」變成機制，不是文件上的約定 —— 打錯一個 action 名就被擋下。

## 批次渲染（廣播一律用這個）

並行發 9 則時，一則一則手工填插槽既慢又容易漏一個。用腳本一次產出全部：

```bash
python .claude/skills/god-dispatch/scripts/render.py <action> <payload.json>
```

payload 只有兩個欄位 —— `common` 放大家一樣的，`recipients` 只寫每個人不一樣的：

```json
{
  "common": {
    "day": "2", "alive_count": "8",
    "alive_list": "…", "hunter_shot_line": null
  },
  "recipients": [
    { "to": "P6", "your_position": "1" },
    { "to": "P7", "your_position": "2" }
  ]
}
```

三條規則：

- recipient 的欄位**覆蓋** `common` 的同名欄位
- `to` 同時填進 `{{seat}}`（模板沒有 `{{seat}}` 就自動忽略）
- 值寫 `null` → **整行省略**。`{{leader_note}}`、`{{assignments}}`、
  `{{hunter_shot_line}}`、`{{wolf_teammates_line}}` 這類「留空就整行不要」的插槽用它。
  想留白但保留該行，寫空字串 `""`

輸出是一段一段的 `===== → P6 =====`，照著並行送出即可。
**腳本會先把該 action 的模板註記印在最前面** —— 那些是渲染時的但書（例如
`{{leader_note}}` 只有兩種值、只剩一狼時要整段省略），送出前確認你照做了。

### 腳本會擋下三件事

任一不過就**整批不輸出**，exit code 1：

1. 有插槽沒填（渲染後還留著 `{{...}}`）
2. 命中中立性禁用詞
3. payload 給了模板沒有的欄位 —— 這條專治**打錯欄位名**：
   打錯的那個沒生效，真正的插槽卻空著，人眼很難看出來

## 渲染後必跑的四項檢查

1. **白名單對應**：每一段都能對應到 `rules/god-neutrality.md` 白名單的六類之一
2. **禁用詞掃描 0 命中**：
   ```
   參考思路  值得思考  供你權衡  可以思考的點  你需要處理
   建議你    常見打法  供你判斷  幾個可以思考  你的處境
   ```
3. **逐字稿是原文**：與 `game-state/public/03-speeches-dayN.md` 逐字相同，**不摘要**
4. **無形容詞化轉述**：不出現「他直接對你喊話」「最鋒利的一擊」這類替玩家標記重點的句子

**第 2 項由腳本代跑**（連同插槽完整性）。**第 1、3、4 項機器判不了，你自己看。**

任一項不過 → **不要送出**，回頭修模板。

## 模板不夠用怎麼辦

**去改對應的那一份 `references/*.md`**（對所有人一致生效），不要這一次多寫幾句。

改完跑一次 `--selftest`，確認 18 個 action 都還取得出模板本文：

```bash
python .claude/skills/god-dispatch/scripts/render.py --selftest
```

> **模板本文是標題之後的第一個圍欄區塊。** 內文本身含有 ``` 的模板（例如 `deal`
> 要玩家建立檔案），外層必須用四個反引號 ```` 包起來，否則會被切在半路。

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
