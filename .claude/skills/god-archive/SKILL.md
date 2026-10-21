---
name: god-archive
description: 狼人殺・把結束的一局從 game-state/ 搬進 game-archive/NNN-日期/，清出乾淨的骨架給下一局。終局後執行，或開局發現殘留時先執行。僅 GOD 執行。 觸發詞：歸檔、把這局收起來、收尾清場、準備開下一局。
---

# /god-archive —— 歸檔一局

## 什麼時候跑

| 時機 | 情況 |
|---|---|
| **終局後** | `/god-endgame` 走完，戰報、稽核、MVP、最終報表都寫好了 |
| **開局前** | `/god-open` 第 0 步的殘留檢查發現 `game-state/` 還有上一局 |

## 為什麼歸檔＝解除保護

對局中，上帝視角放在 `game-state/secret/`，由 hook 擋下非 god／reporter 的存取。

**歸檔的動作就是把資料搬出保護區。** 語意上正好等於「這一局結束了，底牌公開了」——
所以存取控制規則永遠只需要認得 `game-state/secret/` 一個路徑，
**不必為歷史對局寫任何例外規則**。

## 步驟

### 1. 決定局號與目錄

看 `game-archive/INDEX.md` 的最後一列，局號 +1（三位數，`001`、`002`…）。
目錄名為 `NNN-YYYYMMDD`，日期取**開局日**（不是歸檔日）。

### 2. 確認這一局真的結束了

- `public/99-reveal.md` 存在（底牌已公布）
- `public/99-audit.md` 存在（稽核已完成）

**開局前的殘留歸檔可能兩者都沒有** —— 那表示上一局沒跑完就中斷了。
照樣歸檔，但在 `SUMMARY.md` 註明「未完成的對局」。

### 3. 搬移

```
game-state/public/   → game-archive/NNN-日期/public/
game-state/secret/   → game-archive/NNN-日期/god-view/     ← 更名
game-state/report/   → game-archive/NNN-日期/report/
.claude/hooks/access.log
                     → game-archive/NNN-日期/god-view/access.log（複製，然後清空原檔）
```

**`access.log` 要一起歸檔。** 它是這一局的稽核證據，留在原地會與下一局混在一起。
複製過去之後把原檔清空，下一局從乾淨的紀錄開始。

### 4. 寫 SUMMARY.md

| 欄位 | 來源 |
|---|---|
| 日期、板子、時長、勝方 | `99-reveal.md` |
| MVP 與票數 | `99-mvp.md` |
| 稽核結論 | `99-audit.md` |
| 全員底牌表 | `99-reveal.md` |
| **這一局的系統性教訓** | 你自己的判斷 —— 這是這份檔案最有價值的一段 |

最後附一張目錄內容表，說明 `god-view/` 已無保密性。

### 5. 追加 INDEX.md 一列

```
| NNN | 日期 | 板子 | 勝方 | MVP | 稽核 | 目錄連結 |
```

### 6. 重建乾淨骨架

```
game-state/
├── README.md      保留（說明目錄結構，不屬於任何一局）
├── public/
├── secret/
└── report/
```

三個目錄各放一個 `.gitkeep`。

### 6.5 roster 會隨著清空一起消失 —— 問使用者要不要留

`game-state/public/roster.json` 記的是「哪個 session id 佔著哪個角色」。
它就放在 `public/` 底下，**所以第 6 步清空 `game-state/` 時會連它一起清掉**，
不需要另外動手。

要注意的是**你自己也在那份 roster 裡**：清掉之後你立刻失去 `secret/` 的存取。
**所以務必等歸檔完全做完（第 3~6 步都結束）再清。**

若使用者打算沿用現在這些視窗繼續開下一局，可以先備份再寫回：

```
這一局已歸檔到 game-archive/NNN-日期/。
roster.json 在 game-state/public/ 底下，清空 game-state/ 會一起清掉。
你要沿用現在這 11 個視窗的話，我把它備份起來、清完再寫回；
要換一批全新的 session，那就讓它跟著清掉，開局時大家重跑 /ur。
```

備份寫回時，**`roster-sessions.json` 要跟 `roster.json` 一起**備份寫回 ——
少了它，hook 認不出上帝，玩家的 SendMessage 會一律以 `SENDMSG_UNVERIFIED` 放行。

**問使用者，不要自己決定。** 兩種都可以，但清掉之後你需要 `secret/` 的話，
得請他重跑一次 `/ur god`。

### 7. 驗證

- [ ] `game-archive/NNN-日期/` 內容完整（public、god-view、report、SUMMARY.md）
- [ ] `game-state/` 只剩 README 與三個空目錄
- [ ] **專案內 grep 不到任何殘留的當局底牌**
- [ ] `INDEX.md` 新增了一列且連結可用
- [ ] roster.json 已依使用者的答覆處理（跟著清掉或備份寫回），沒有自己替他決定

## 回報使用者

歸檔到哪個目錄、這一局的一句話總結、以及 `game-state/` 已就緒可開下一局。
