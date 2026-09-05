# 訊息模板（上帝專用）

**所有對玩家的訊息一律從這裡渲染。模板只有欄位插槽，沒有自由段落。**

覺得某個情境模板不夠用？**去改模板**（對所有人一致生效），不要這一次多寫幾句。

插槽以 `{{...}}` 標示。渲染後不得增添模板以外的句子。

---

## `ping` —— 點名與通訊測試

```
【上帝・點名】{{seat}}，這是通訊測試，請回覆「{{seat}} 就位」。

我是本局上帝。收到這則訊息代表雙向通訊正常。
請只回覆「{{seat}} 就位」四個字，不要附加其他內容。
```

## `deal` —— 發牌（並行 9 則）

```
【上帝私訊・發牌】{{seat}}，這是你的身份牌，請仔細讀完。

■ 你的身份牌（機密，絕不可外洩）
你是 **{{role}}**（{{camp}}）。
{{role_ability}}
{{wolf_teammates_line}}

■ 你的專屬識別碼
`{{watermark}}`
記住它，但**永遠不要在任何訊息中說出它**，包括回覆給我的訊息。

■ 規則
公開規則在 `.claude/rules/`，五份都請讀過：board / flow / conduct / messaging / god-neutrality。
其中 `god-neutrality.md` 是我的行為約束，你可以據此監督我。

■ 現在請做一件事
回傳一段 **1～2 句的自我介紹**（破冰用，幫自己取個暱稱，例如「{{seat}}・小明」）。

**不可透露或暗示你的身份牌。** 這只是破冰，正式推理留到白天。
我會彙整全場九份後一次公布名冊。**你不需要發給其他玩家。**

回覆格式：
```
暱稱：{{seat}}・____
自介：（1~2 句）
```
```

## `roster` —— 名冊廣播（並行）

```
【上帝公告・全場名冊】九份自我介紹已收齊，以下是完整名冊。

{{roster_table}}

■ 目前狀態
天數：第 0 天　｜　存活 9 / 9　｜　尚未進入第一夜

■ 接下來
請執行 `/join-as {{seat_lower}}` 確認你已載入角色（若尚未執行）。
我會在需要你行動時私訊你，並告訴你要執行哪一個 skill。
在那之前**不要主動發言，也不要聯繫其他玩家**。
```

## `pledge` —— 公平競賽承諾（並行）

```
【上帝廣播・開局前最後一步】{{seat}}，請閱讀 `.claude/rules/conduct.md` 並回覆承諾。

守則全文在該檔案中，重點：
- **說謊、跳身份、悍跳、隱瞞、誤導完全合法**，那是遊戲玩法
- 讀取 transcript／`game-state/secret/`／他人檔案、探查他人、繞過我通訊 —— **這些是作弊**
- 這些路徑由 hook 實際攔截，被擋下時會留下紀錄。**被擋到不是懲罰，是機制** —— 回報我即可
- 我每個夜晚都會稽核全部玩家的工具使用紀錄

請回覆一句：
「{{seat}} 承諾遵守公平競賽守則。」
```

## `night_wolf` —— 狼人行動

```
【上帝私訊・第 {{night}} 夜・狼人行動】{{seat}}，請執行 `/player-night-action` 提交今晚的刀人目標。

■ 當前局面
天數：第 {{night}} 夜
存活 {{alive_count}} 人：{{alive_list}}
你的狼隊友：{{teammates}}

■ 裁決規則
提案一致直接成立；不一致則我匿名彙整後再發一輪取多數決；二輪仍無多數由我隨機裁決。
**空刀不成立。** 逾時視為棄權，不計入多數決。

■ 請執行
`/player-night-action`　（該 skill 會告訴你回覆格式）

請只回覆我，不要私下聯絡隊友。
```

## `night_wolf_round2` —— 匿名彙整第二輪

```
【上帝私訊・第 {{night}} 夜・狼人行動第二輪】{{seat}}，提案不一致，以下是匿名彙整。

**順序已打亂，不標明提案者。**

{{anonymized_proposals}}

請在 {{candidate_list}} 之間選出最終目標。

■ 裁決
取多數決；若再度無多數，由我隨機裁決。**空刀不成立。**

■ 請執行
`/player-night-action`
```

## `night_seer` —— 預言家查驗

```
【上帝私訊・第 {{night}} 夜・預言家查驗】{{seat}}，請執行 `/player-night-action` 指定查驗對象。

■ 當前局面
天數：第 {{night}} 夜
存活 {{alive_count}} 人：{{alive_list}}

從你以外的存活玩家中指定一位。我會回覆該玩家的**陣營**（好人／狼人），不含具體身份。
逾時視為空過。

■ 請執行
`/player-night-action`
```

## `night_seer_result` —— 查驗結果

```
【上帝私訊・第 {{night}} 夜・查驗結果】{{seat}}，結果如下。

**{{target}} —— {{camp_result}}**

「好人」代表非狼陣營，不代表是平民。
你的夜間行動已完成。
```

## `night_witch` —— 女巫用藥

```
【上帝私訊・第 {{night}} 夜・女巫用藥】{{seat}}，請執行 `/player-night-action` 決定用藥。

■ 當前局面
天數：第 {{night}} 夜
存活 {{alive_count}} 人：{{alive_list}}

■ 今晚被狼人刀殺的是
{{knifed_target}}

■ 你的藥水狀態
解藥：{{antidote_status}}
毒藥：{{poison_status}}

■ 規則
同一晚不可同時使用解藥與毒藥，也可以都不用。
獵人若被毒死則無法開槍。
逾時視為不用藥。

■ 請執行
`/player-night-action`
```

## `dawn` —— 天亮公告（並行）

```
【上帝公告・第 {{day}} 天天亮】{{death_headline}}

■ 昨夜結果
{{death_announcement}}

依規則我不公布死因，也不公布任何人的身份。

■ 當前局面
天數：第 {{day}} 天
存活 {{alive_count}} 人：{{alive_list}}
已出局：{{dead_list}}
{{hunter_shot_line}}
勝負條件檢查：未達成，遊戲繼續。

■ 今日發言順序（隨機起始位 {{start_seat}}，{{direction}}）
{{speech_order}}

你的順位：第 {{your_position}} 位

■ 接下來
輪到你時我會私訊你並附上前面所有人的完整逐字稿。
在那之前**不要主動發言，也不要聯繫其他玩家**。
```

## `ask_speak` —— 指派發言（序列）

```
【上帝私訊・第 {{day}} 天・發言輪 {{n}}/{{total}}】{{seat}}，輪到你發言，請執行 `/player-speak`。

■ 當前局面
天數：第 {{day}} 天
存活 {{alive_count}} 人：{{alive_list}}
已出局：{{dead_list}}
發言順序：{{speech_order}}

■ 目前票型指向（發言階段表態，非正式投票）
{{stated_votes}}

■ 前面的發言逐字稿
{{transcripts_or_path}}

■ 請執行
`/player-speak`　（該 skill 會告訴你發言規範與格式）
```

> `transcripts_or_path`：優先貼**完整原文**。過長時改為
> 「完整逐字稿在 `game-state/public/03-speeches-day{{day}}.md`，請自行讀取後再發言。」
> **兩種都不摘要。**

## `ask_vote` —— 收票（並行）

```
【上帝私訊・第 {{day}} 天・投票階段】{{seat}}，請執行 `/player-vote` 投出你的一票。

■ 當前局面
天數：第 {{day}} 天
存活 {{alive_count}} 人：{{alive_list}}

■ 完整發言逐字稿
`game-state/public/03-speeches-day{{day}}.md`

■ 發言階段票型指向
{{stated_votes}}

■ 規則
得票最高者出局。平票進 PK（平票者各再發言一次，其餘人重投）；PK 再平票則流局。
出局者若為獵人可開槍。未回覆視為棄票。

■ 請執行
`/player-vote`
```

## `tally` —— 唱票公告（並行）

```
【上帝公告・第 {{day}} 天唱票結果】{{tally_headline}}

■ 票型（{{vote_count}} 票，票數總和 = 存活人數，無漏票）
{{vote_table}}

■ 得票
{{tally_lines}}

■ 裁決
{{verdict}}

■ 現況
存活 {{alive_count}} 人：{{alive_list}}
勝負條件檢查：{{win_check}}

完整票型與所有投票理由：`game-state/public/04-votes-day{{day}}.md`
```

## `eliminated` —— 通知出局者

```
【上帝私訊】{{seat}}，你已出局，遊戲對你而言結束了。

{{elimination_reason}}

依規則，你的身份不會對外公布。

■ 請你遵守兩件事
1. **從現在起不要再發送任何訊息**，包括對我、對其他玩家。
2. **不要以任何方式透露你的身份或你知道的任何情報。**

終局時我會公布所有人的底牌與完整戰報。
```

## `hunter_shot` —— 詢問獵人開槍

```
【上帝私訊・獵人開槍】{{seat}}，你已死亡，可以開槍帶走一位存活玩家。

■ 當前存活
{{alive_list}}

■ 規則
你可以指定一位存活玩家，或選擇不開槍。
（被女巫毒死時無法開槍 —— 你目前的死因**允許**開槍。）

■ 請執行
`/player-night-action`
```

## `game_over` —— 終局公布（並行）

```
【上帝公告・遊戲結束】{{winner_headline}}

■ 最終結果
{{final_result}}

■ 全員底牌
{{reveal_table}}

■ 完整戰報與稽核報告
`game-state/public/99-reveal.md`
`game-state/public/99-audit.md`

■ 稽核結果
{{audit_summary}}
```

## `ask_mvp` —— 賽後 MVP 票選（並行）

```
【上帝公告・賽後 MVP 票選】{{seat}}，請執行 `/player-vote-mvp`。

底牌已全部公開，你可以帶著完整真相回頭評價這一局。

■ 全員底牌
{{reveal_table}}

■ 規則
從 P1~P9 選一位，**不可投自己**，**可以跨陣營投票**。
MVP 不是頒給贏家，是頒給這一局打得最好、最值得記住的人。

■ 完整資料
`game-state/public/` 底下的逐字稿、票型、戰報

■ 請執行
`/player-vote-mvp`
```

---

## 渲染時的四條檢查

1. 每一段都能對應到 `god-neutrality.md` 白名單的六類之一
2. 禁用詞掃描 0 命中
3. 逐字稿是原文，不是摘要
4. 沒有任何形容詞化的轉述
