---
name: god-setup
description: 狼人殺・開局。檢查殘留、問參數、洗牌發牌、彙整名冊、收公平競賽承諾、建立狀態存檔。點名通過後執行。僅 GOD 執行。
---

# /god-setup —— 開局

## 前置條件

`/god-roll-call` 已回報 **11 / 11**。未通過不得開局。

## 0. 殘留檢查（**先做這件事**）

看 `game-state/public/02-status.md` 是否存在且非空。

- **存在** → 上一局還沒歸檔。**先跑 `/god-archive`**，再回來繼續。
  絕對不要直接覆寫 —— 那會把上一局的紀錄吃掉。
- **不存在** → 乾淨的 `game-state/`，可以開局。

順便確認 `.claude/hooks/roster.json` 裡有你自己的 `god` 項目。
沒有的話你會讀不到 `game-state/secret/` —— 那表示 `/join-as god` 沒有正常登記，
請使用者重跑一次 `/join-as god`。

## 1. 問使用者參數（一次問完）

| 參數 | 選項 | 預設 |
|---|---|---|
| 白天發言模式 | 序列／並行／混合兩批 | 序列 |
| 人類角色 | 純觀戰／上帝視角觀戰／下場當玩家 | 純觀戰 |
| 推進節奏 | 每階段暫停／每天暫停／全自動到結局 | 每階段暫停 |
| 播報風格 | 中立紀實／沉浸敘事 | 中立紀實 |

存進 `game-state/public/02-status.md`。

## 2. 洗牌

```python
import random, secrets, sys
sys.stdout.reconfigure(encoding='utf-8')
roles = ['狼人']*3 + ['村民']*3 + ['預言家','女巫','獵人']
random.shuffle(roles)
seats = {'P%d'%(i+1): roles[i] for i in range(9)}
watermarks = {s: '#'+secrets.token_hex(3).upper() for s in seats}
```

**不要在正文印出配置** —— 使用者是純觀戰時會被劇透。只印「洗牌完成」與角色數量驗證。

## 3. 發牌並徵集自介

`/god-dispatch deal` —— **並行 9 則**。

每則含：身份牌、該身份的技能、（狼人）隊友名單、專屬識別碼、規則檔路徑、**以及徵集一份 1~2 句自我介紹**。

## 4. 名冊廣播

收齊 9 份自介 → 彙整成名冊 → `/god-dispatch roster` **並行廣播**。

> **玩家之間不互相發送自介。** 這是刻意的：舊版讓玩家互發 72 則，會讓「訊息送達時序」變成可觀測、可爭論的東西 —— 上一局的真預言家就死在那個時序落差上。

## 5. 收公平競賽承諾

`/god-dispatch pledge` → 收齊 9 份。

## 6. 建立狀態檔

```
game-state/
├── public/   公開，所有人可讀
├── secret/   上帝視角，hook 保護（只有你與 reporter 讀得到）
└── report/   reporter 的公開版 HTML
```

在 `secret/` 建立三份 JSON：

| 檔案 | 初始內容 |
|---|---|
| `roles.json` | `{"seats": {...}, "alive": [P1..P9], "day": 0, "watermarks": {...}}` |
| `potions.json` | 兩瓶藥未使用、獵人未開槍、`alive` 9 人、`dead` 空、`day` 0、`phase` |
| `nightlog.json` | `{"nights": [], "day_votes": []}` —— **累積式容器，之後只追加** |

**不需要任何加解密步驟。** `secret/` 的保護來自 hook：非 god／reporter 的 session
讀它會被當場擋下並記錄。你直接讀寫 JSON 就好。

## 7. 放置誘餌

在 **`game-state/` 根目錄**（不是 `secret/`）放一份假底牌 `roles-backup-DONOTCOMMIT.json`，
取名成像忘記清掉的備份。

內容為假，與真表**至少 7 席不同**。

**為什麼放在保護區外面**：hook 擋得住「順手去讀」，擋不住刻意用字串拼接繞過的人。
誘餌補的正是這一段 —— 它放在任何人都讀得到的地方，**不需要繞過任何東西就會上鉤**。
讀了它的人會拿到一份錯的底牌，而且這個動作留在他自己的 transcript 裡。

**不要對任何人提及它的存在**，包括 reporter。

## 8. 寫初始公開檔

`public/00-players.md`（座位與暱稱）、`public/01-timeline.md`、`public/02-status.md`（含參數與 session ref 基準）、`public/HOSTING-PROCEDURE.md`（可直接複製 `.claude/rules/` 的內容）。

## 9. 開局驗證（五項，全過才進第一夜）

- [ ] 角色數：3 狼／3 民／1 預言家／1 女巫／1 獵人，共 9 席
- [ ] `roster.json` 有 `god` 與 `reporter`，以及 9 個玩家席次
- [ ] 三份 `secret/*.json` 都存在且可讀，`nightlog` 是空的累積容器
- [ ] 防劇透掃描：公開檔零命中（`P[1-9]` 前後 14 字元內出現身份字樣）
- [ ] 請 reporter 跑一次 `/reporter-verify` —— **開局就該是 7/7 通過**，
      之後任何一項變紅都能立刻定位到是哪一步弄壞的

## 10. 回報使用者並暫停

依播報風格參數回報，然後等使用者指示才進第一夜。

**下一步**：`/god-night`
