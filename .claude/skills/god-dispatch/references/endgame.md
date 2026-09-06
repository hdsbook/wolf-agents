# 訊息模板・終局

**上帝對玩家的訊息一律從模板渲染，不自由撰寫。** 插槽以 `{{...}}` 標示，
渲染後不得增添模板以外的句子。完整 action 索引與渲染規則在 `../SKILL.md`。

批次渲染：`python .claude/skills/god-dispatch/scripts/render.py <action> <payload.json>`

---

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
`game-state/public/` 底下的逐字稿與票型。
戰報 `99-reveal.md` 由記錄者撰寫中，**可能還沒好** —— 不必等它，
你手上的逐字稿與這張底牌表已經足夠。

■ 請執行
`/player-vote-mvp`
```

> 戰報那一句是因為 MVP 票選與戰報撰寫是**同時**進行的（見 `/god-endgame` 第 2 步）。
> 不要為了讓戰報先寫完而延後發這則 —— 那正是舊版排成一條直線的地方。
