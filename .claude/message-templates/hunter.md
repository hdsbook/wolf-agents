# 訊息模板・獵人開槍（夜間、天亮、投票三處都會用到）

**上帝對玩家的訊息一律從模板渲染，不自由撰寫。** 插槽以 `{{...}}` 標示，
渲染後不得增添模板以外的句子。

**這個目錄玩家也讀得到**，而且公版訊息就是由玩家自己渲染的：

```bash
python .claude/message-templates/render.py <action> --seat P<你的座位> --params <參數>
```

玩家端的說明在 `/player-inbox`；上帝端的 action 索引與渲染規則在
`.claude/skills/god-dispatch/SKILL.md`。

---

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
