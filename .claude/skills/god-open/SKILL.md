---
name: god-open
description: 狼人殺・開局。等全員報到 → 問參數 → 點名與通訊測試（同時指派暱稱）→ 洗牌發牌 → 廣播名冊 → 建立狀態存檔。從 GOD 就位到第一夜之前全部在這一支。僅 GOD 執行。 觸發詞：開局、開新局、發牌、開始點名、進行遊戲模式設定、設定遊戲模式、人到齊了 —— 這些指的是**發牌之前**；若牌已經發完，「開局」是指進第一夜（god-night）。
---

# /god-open —— 開局

從你就位到第一夜之前，全部在這一支。
**使用者只在第 3 步的參數卡片被打擾一次**，其餘由你自己推進。

```
第 0 步  殘留檢查（有殘留 → /god-archive）
第 1 步  收滿 10 則報到
第 3 步  參數卡片  ★ 使用者唯一要動手的一次
第 4-5 步 抽暱稱 → ping
第 7-8 步 洗牌 → 發牌
第 13 步 回報 + 「天黑請閉眼」→ /god-night
```

---

## 0. 前置檢查

可以在等報到的空檔先做。

- `game-state/public/02-status.md` 存在且非空 → **先跑 `/god-archive`**，不要覆寫
- `game-state/public/roster.json` 要有你的 `god` 項；沒有就請使用者在你這個 session 重跑角色認領（否則你讀不到 `secret/`）

## 1. 收報到 —— 門檻 10 則

9 位玩家 + reporter＝10。**你自己不向自己報到。**

不需要使用者下指令。玩家與 reporter 載入完會陸續自己報到，每則報到都會喚醒你。
收滿 10 則才進第 2 步。

**在這裡結束回合是合法的**（見 `agent-reference/god/02-round.md`「你還會在什麼時候暫停」）。
安靜等著，不要催使用者、不要反覆回報進度。

### 使用者催你的時候

他說「人到齊了」「開始」「開始點名」時，**立刻跑第 2 步的 `ListAgents` 核對**：

- **到齊** → 往下走；沒收到報到的那幾位記一筆，第 5 步的 ping 會補驗
- **沒到齊** → 回報還缺哪幾個，繼續等

**他能改變的是你何時確認，不是要不要確認。** 少一個人就開局，那個人整場收不到身份牌。

## 2. 清點在場者

```
ListAgents
```

11 個名稱都在且非 offline：`GOD` `reporter` `P1`~`P9`。

**記下每個 session 的 ref**（如 `P1 [3998b6]`），第 6 步寫進 `02-status.md`，
之後每階段比對用。缺人 → 回報缺誰，停下等使用者處理。

## 3. 問參數

**`AskUserQuestion` 一次問完四題**（四題是上限，不要加第五題）。
預設值放第一個選項並標「（建議）」：

| header | options |
|---|---|
| 開局確認 | 現在開局（建議）／先不開局 |
| 人類角色 | 上帝視角觀戰（建議）／純觀戰／下場當玩家 |
| 推進節奏 | 全自動到結局（建議）／每天暫停／每階段暫停 |
| 播報風格 | 沉浸敘事（建議）／中立紀實 |

`description` 講人話（「純觀戰」＝「我一張底牌都不會給你看」）。
推進節奏三個值的說明要與 `agent-reference/god/02-round.md`「依節奏參數決定是否暫停」一致。

**選「先不開局」就停在這裡** —— 不發 ping、不洗牌、不發牌。記著後三題答案，
跟他說隨時可以繼續。此時還沒寫任何檔案。

參數先記在手上，第 6 步寫進 `02-status.md`。

## 4. 抽暱稱

```python
import random, sys
sys.stdout.reconfigure(encoding='utf-8')
pool = ['阿松','白帆','青禾','大河','雨田','山彥','湖心','林間','石頭','風鈴','雲杉','冬陽']
picked = random.sample(pool, 9)
nicknames = {'P%d' % (i+1): picked[i] for i in range(9)}
print(nicknames)
```

由你指派，玩家不自選、不更換。名單池可增補，新名字須**與身份無關聯、兩字可辨識、彼此不同字**。

抽在洗牌之前，所以印出來不劇透 —— 這時你也還不知道底牌。

## 5. ping —— 出站通訊測試

`/god-dispatch ping` **並行 10 則**（9 玩家各帶自己的暱稱 + reporter 用 `ping_reporter`）。
模板在 `.claude/skills/god-dispatch/references/message-templates.md`。

報到驗的是入站，ping 驗的是出站，兩者不互相保證。

回覆格式：玩家「P<n>・<暱稱> 就位」，reporter「reporter 就位」。

- 有缺 → 重發一次；仍無回應則回報是哪幾個並停下
- 回錯暱稱 → 重發該則並記一筆。**以你指派的為準**

## 6. 寫下座位、暱稱與基準

- `public/00-players.md` —— 座位與暱稱（此時沒有身份欄）
- `public/02-status.md` —— 三個參數 ＋ 11 個 session ref 基準

**現在就寫，不要拖到後面。**

## 7. 洗牌

```python
import random, secrets, sys
sys.stdout.reconfigure(encoding='utf-8')
roles = ['狼人']*3 + ['村民']*3 + ['預言家','女巫','獵人']
random.shuffle(roles)
seats = {'P%d'%(i+1): roles[i] for i in range(9)}
watermarks = {s: '#'+secrets.token_hex(3).upper() for s in seats}
```

**不要在正文印出配置**（使用者可能是純觀戰）。只印「洗牌完成」與角色數量驗證。

## 8. 發牌

先建立空的 `public/intro-inbox/`，再 `/god-dispatch deal` **並行 9 則**。

每則含：身份牌、技能、（狼人）隊友、識別碼、規則檔路徑、**暱稱（複述第 4 步的，不重取）**、
公平競賽承諾要求、他自己要寫的自介檔路徑。

**收齊條件：9 份「已落檔＋承諾」，且 `intro-inbox/` 裡真的有 9 個檔。**

- 自介內文不進你手上。玩家若還是貼給你，不轉貼、不摘要、不寫檔
- 缺的重發該則，**不要代填、不要代寫檔案**
- 回報說落檔但檔案不在 → 重發

## 9. 名冊廣播

`/god-dispatch roster` 並行廣播：**座位暱稱表 ＋ `intro-inbox/` 路徑與已落檔檔名清單**。

**不貼任何一句自介內文**（同逐字稿規矩，見 `rules/god-neutrality.md`）。
玩家之間不互相發送。

## 10. 建立狀態檔

`secret/` 三份 JSON：

| 檔案 | 初始內容 |
|---|---|
| `roles.json` | `{"seats": {...}, "alive": [P1..P9], "day": 0, "watermarks": {...}}` |
| `potions.json` | 兩瓶藥未使用、獵人未開槍、`alive` 9、`dead` 空、`day` 0、`phase`、**`"result": null`** |
| `nightlog.json` | `{"nights": [], "day_votes": []}` —— 累積式容器，之後只追加 |

> **`result` 保持 `null` 直到勝負達成。** 它是 `render.py` 判斷公開版要不要揭底牌的唯一開關 ——
> 一有值，公開版就會列出全員身份並跳過防劇透掃描。
> 形如 `{"winner": "好人|狼人", "reason": "屠邊（平民全滅）", "day": 3}`。

不需要加解密，`secret/` 由 hook 保護。

其餘公開檔：`public/01-timeline.md`、`public/HOSTING-PROCEDURE.md`（複製 `.claude/rules/`）。
`00-players.md` 與 `02-status.md` 第 6 步已寫好，這裡不必補。

## 11. 開局驗證（五項全過才進第一夜）

- [ ] 角色數 3 狼／3 民／1 預言家／1 女巫／1 獵人，共 9 席
- [ ] `roster.json` 有 `god`、`reporter` 與 9 個玩家席次
- [ ] 三份 `secret/*.json` 存在可讀，`nightlog` 是空容器
- [ ] 防劇透掃描零命中（`P[1-9]` 前後 14 字內出現身份字樣）
- [ ] reporter 跑 `/reporter-verify` 回報 **7/7 通過**

## 12. 通知 reporter

```
SendMessage → reporter
「開局已完成，請執行 /reporter-build。」
```

兩份都產（不加 `spoiler`）。

**送完不要結束回合** —— reporter 不會回你，直接進第 13 步。

## 13. 回報使用者並暫停

依播報風格回報，然後等他選了才進第一夜。

**這次暫停不受節奏參數影響，「全自動到結局」也照停** —— 這是最後一個能重發牌的檢查點。

台詞放在最前面：

```
九個人都入座了，牌也發下去了，誰是誰只有他們自己知道。

天要黑了 —— 你說一句「天黑請閉眼」，第一夜就開始。
```

再用 `AskUserQuestion` 讓它可以點：

```
question: 天黑請閉眼？
header:   第一夜
options:
  - label: 天黑請閉眼（建議）
    description: 狼人睜眼、預言家查驗、女巫決定用不用藥。過了這一步就不能重發牌了。
  - label: 先等一下
    description: 這是最後一個能重發牌的機會，我等你。
```

---

## 中立性

ping 與發牌以外，開局不對玩家說多餘的話。訊息一律走模板。

**暱稱池不得有與身份、陣營或技能沾邊的字**，指派必須隨機 ——
不依座位順序、不依你對哪個 session 的印象。

對使用者的語氣見 `agent-reference/god/04-reporting.md`。異常照實講：誰沒報到、誰回錯暱稱、哪條線不通。

**下一步**：`/god-night`
