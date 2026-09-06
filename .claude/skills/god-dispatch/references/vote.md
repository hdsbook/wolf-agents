# 訊息模板・投票

**上帝對玩家的訊息一律從模板渲染，不自由撰寫。** 插槽以 `{{...}}` 標示，
渲染後不得增添模板以外的句子。完整 action 索引與渲染規則在 `../SKILL.md`。

批次渲染：`python .claude/skills/god-dispatch/scripts/render.py <action> <payload.json>`

---

## `ask_vote` —— 收票（並行）

```
【上帝私訊・第 {{day}} 天・投票階段】{{seat}}，請執行 `/player-vote` 投出你的一票。

■ 當前局面
天數：第 {{day}} 天
存活 {{alive_count}} 人：{{alive_list}}

■ 完整發言逐字稿
`game-state/public/03-speeches-day{{day}}.md`
（併檔若還沒跟上，原文在 `game-state/public/speech-inbox/`）

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
