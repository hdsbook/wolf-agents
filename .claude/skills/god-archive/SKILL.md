---
name: god-archive
description: 狼人殺・把結束的一局從 game-state/ 搬進 game-archive/NNN-日期/，清出乾淨的骨架給下一局。終局後執行，或開局發現殘留時先執行。僅 GOD 執行。
---

# /god-archive —— 歸檔一局

## 什麼時候跑

| 時機 | 情況 |
|---|---|
| **終局後** | `/god-endgame` 走完，戰報、稽核、MVP、最終報表都寫好了 |
| **開局前** | `/god-setup` 的殘留檢查發現 `game-state/` 還有上一局 |

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
game-state/roles-backup-DONOTCOMMIT.json
                     → game-archive/NNN-日期/god-view/roles-decoy-FAKE.json
.claude/hooks/access.log
                     → game-archive/NNN-日期/god-view/access.log（複製，然後清空原檔）
```

**`access.log` 要一起歸檔。** 它是這一局的稽核證據，留在原地會與下一局混在一起。
複製過去之後把原檔清空，下一局從乾淨的紀錄開始。

**誘餌檔一定要改名。** 留著原名歸檔，日後回顧的人會把那份假底牌當成真的 ——
上一局就差點發生（檔名寫著 backup，內容卻是假的）。

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

### 7. 驗證

- [ ] `game-archive/NNN-日期/` 內容完整（public、god-view、report、SUMMARY.md）
- [ ] `game-state/` 只剩 README 與三個空目錄
- [ ] **專案內 grep 不到任何殘留的當局底牌**
- [ ] `INDEX.md` 新增了一列且連結可用

## 回報使用者

歸檔到哪個目錄、這一局的一句話總結、以及 `game-state/` 已就緒可開下一局。
