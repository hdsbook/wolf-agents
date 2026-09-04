# 狼人殺・9 人標準局

這個專案是一場由 11 個獨立 Claude session 進行的狼人殺：
**1 個上帝（GOD）、9 個玩家（P1~P9）、1 個金鑰保管人（helper）。**

## 你該做的第一件事

執行 `/join-as <role>` 認領你的角色：

```
/join-as god        主持人
/join-as helper     金鑰保管人
/join-as p1 … p9    玩家
```

該角色需要知道的一切，會由這個 skill 載入。**在此之前不要做任何遊戲相關的動作。**

## 規則放在哪裡

公開規則在 `.claude/rules/`，任何人都可以讀、也可以在爭議時引用：

| 檔案 | 內容 |
|---|---|
| `board.md` | 板子配置與角色技能 |
| `flow.md` | 流程與裁決標準 |
| `conduct.md` | 公平競賽守則（說謊 vs 作弊的界線） |
| `messaging.md` | 通訊規範 |
| `god-neutrality.md` | 上帝中立性契約 —— 玩家可據此監督主持人 |

對局狀態在 `game-state/`：`public/` 是公開紀錄，`secret/` 是加密的上帝視角。
