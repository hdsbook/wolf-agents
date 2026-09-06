# 訊息模板・指路

**上帝對玩家的訊息一律從模板渲染，不自由撰寫。** 插槽以 `{{...}}` 標示，
渲染後不得增添模板以外的句子。完整 action 索引與渲染規則在 `../SKILL.md`。

批次渲染：`python .claude/skills/god-dispatch/scripts/render.py <action> <payload.json>`

---

## `notice` —— 指路訊息（信箱在哪，並行）

```
【上帝・{{headline}}】{{seat}}，你這一步的指令已經放進信箱。

■ 你的信
`{{mailbox_file}}`

**用 `Read` 讀它。** 當前局面、你要做什麼、回覆格式與逾時的預設判定都在裡面。

■ 讀完請執行
{{skill}}

{{timeout_note}}
```

> **這一則是唯一直送的公版訊息，其餘公版內容都在信箱檔裡。**
> 它本身不含任何局面資訊 —— 九個人拿到的除了座位與檔名之外完全相同。
>
> `{{skill}}` —— 純公告（`tally`、`game_over`、`roster` 這類）不需要玩家做事時，
> 填「（這則不需要你回覆）」。
>
> `{{timeout_note}}` —— 該階段沒有逾時判定時，值填 `null`，整行省略。
>
> **檔不存在、或內容看起來不是給你的 → 玩家回報上帝，不要自己推進。**
> 這與發言的必讀清單是同一條紀律：清單是權威，資料夾是現場，對不上就回報。
> 玩家端的說明在 `.claude/agent-reference/player/01-play-guide.md`。
