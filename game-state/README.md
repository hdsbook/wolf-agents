# game-state —— 進行中的這一局

**這個目錄永遠代表「當前對局」。** 上一局的資料在 `../game-archive/`。

| 目錄 | 內容 | 誰讀得到 |
|---|---|---|
| `public/` | 公開紀錄：名冊、時間軸、狀態、發言逐字稿、票型 | **所有人** |
| `secret/` | 上帝視角：底牌、每夜行動、藥水狀態、劇透版報表 | **只有 god 與 reporter** |
| `report/` | 公開版 HTML 儀表板 | **所有人** |

`secret/` 由 `.claude/hooks/guard_secrets.py` 攔截保護 —— 這不是約定，是會實際擋下工具呼叫的機制。

## 檔案是唯一真相來源

不以任何人的記憶為準。`public/02-status.md` 永遠記載「現在停在哪、下一步做什麼」，
是上帝失憶後接續主持的唯一入口。

## public/ 的檔案

| 檔案 | 內容 |
|---|---|
| `00-players.md` | 座位名冊 |
| `01-timeline.md` | 每階段的公開播報流水帳 |
| `02-status.md` | **最關鍵**：天數、存活名單、當前階段、下一步 |
| `03-speeches-dayN.md` | 每天的發言逐字稿（全文，不摘要） |
| `04-votes-dayN.md` | 每天的票型與唱票結果 |
| `99-reveal.md` / `99-audit.md` / `99-mvp.md` | 終局才產生 |

## secret/ 的檔案

| 檔案 | 內容 |
|---|---|
| `roles.json` | 座位對應身份、存活名單 |
| `nightlog.json` | **累積式**：`nights` 陣列 + `day_votes` 陣列。**永遠追加，不整份覆寫** |
| `potions.json` | 女巫用藥、獵人開槍狀態、勝負判定 |
| `report-spoiler.html` | reporter 產出的劇透版儀表板 |
