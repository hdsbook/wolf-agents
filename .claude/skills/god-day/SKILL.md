---
name: god-day
description: 狼人殺・天亮公布與序列發言輪。含隨機發言順序、逐字稿即時存檔、勝負檢查。僅 GOD 執行。
---

# /god-day —— 天亮

## 階段 4・天亮公布

### 1. 獵人優先

若昨夜死者含獵人且尚未詢問 → 先 `/god-dispatch hunter_shot`，結算後才公布完整名單。

### 2. 隨機決定發言順序

```python
import random
start = random.randrange(len(alive))
direction = random.choice(['順','逆'])
```

**必須隨機，而且要公告是隨機決定的。** 上一局有玩家被質疑「挑了全天最安全的發言位」，而事實是順序由上帝隨機指派、玩家無法選擇 —— 公告這點能避免無謂的爭議。

### 3. 公告

`/god-dispatch dawn` —— **並行**發給所有存活者，內容一致。

- **只報死了誰，不報死因，不公布身份**
- 無人死亡則公布「平安夜」

### 4. 檢查勝負

```python
if not wolves_alive:                          好人勝
elif not gods_alive or not villagers_alive:   狼人屠邊勝
else:                                         繼續
```

**用程式算，不要心算。** 屠邊最容易被忽略 —— 上一局遊戲就是在投出最後一名平民的那一刻結束的，而全場沒有人算到。

達成勝負 → 直接進 `/god-endgame`。

---

## 階段 5・序列發言輪

### 規則

**序列制**：輪到第 N 位時，附上**前面所有人的完整逐字稿**。

### 每一位的流程

1. `/god-dispatch ask_speak` —— 附完整逐字稿（原文）與目前票型指向
2. 收到發言
3. **立即**追加寫入 `public/03-speeches-dayN.md`（不要等整輪結束）
4. 向使用者轉述該位的發言（依播報風格）
5. 進下一位

### 逐字稿過長時

**不要濃縮。** 改為給公開檔路徑：

> 完整逐字稿在 `game-state/public/03-speeches-dayN.md`，請自行讀取後再發言。

**濃縮就是選擇，選擇就是偏袒。** 這是上一局後期偏袒滲入的縫隙。

### 並行模式

若使用者選了「並行發言」，改為一次發給所有人、收齊後統一公布。
**互動品質會下降**（無法對線、無法反駁），但每輪只要一次往返。

---

## 收尾

1. 整輪結束後在 `03-speeches-dayN.md` 追加票型指向彙整與核心爭點
2. 更新 `secret/potions.json`（天數、階段、存活／死亡名單）
3. 更新 `02-status.md`（下一步：投票）與 `01-timeline.md`
4. **通知 reporter 重建報表**：
   ```
   SendMessage → reporter
   「第 N 天已天亮結算，請執行 /reporter-build。」
   ```
5. 依節奏參數決定是否暫停

**下一步**：`/god-vote`
