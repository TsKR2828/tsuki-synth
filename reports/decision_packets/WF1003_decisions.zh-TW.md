# WF1003 裁決紀錄：10-03 這輪的決定點與月月裁語

> 日期：2026-10-03。體例比照 `WF1002_addendum_decisions.zh-TW.md`：每題列題目、選項、AI／Fable 的建議、月月裁語、落地狀態。
> 本檔由 WF1003 各卡依序追加；**B2 為第一題**（WF1003-B2 卡寫入，稽核 FAIL 後 2026-10-07 由 WF1004-B2b 重做並把這一節併回）；Q09 由 V 卡追加在後。
> 標 **R10** 的會改外掛聲音；CLI 渲染（物理 GATE 驗的那條路）**本檔每一題都以「不變」為前提**，卡內要實證。

---

## B2　Body 層響度正規化要不要做（N1 裁決時留下的結構問題）

**題目**：外掛的 Body 共鳴層把兩個共振帶通調成「正好對準這顆音自己的基頻與第二個模態」，Body 旋鈕因此同時改音色與音量：
基頻上 Body 0.2～1.0 對應 +6.5～+16.8 dB（預設 0.5 是 +11.9 dB、0.8 是 +15.2 dB）。N1（壓縮器固定補償）落地後，
preset 11 把 Body 調回預設 0.5 仍約 +3.8 dBFS。要不要讓 Body 旋鈕「只改音色、不改音量」？
（出處：`reports/wf1002_preset_overshoot_root_cause.zh-TW.md` §4、§7 B2 列；`reports/wf1002b_n1_compressor_makeup_before_after.zh-TW.md` §2 末段；`HANDOVER.md` §1-5 第一條。）

| 選項 | 做法 | 改哪些聲音（R10） | 工作量 |
|---|---|---|---|
| **A** | 對 Body 層做響度正規化：Body 開／關的音量一致，只留下音色差異 | 6 個開 Body 的工廠 preset（6、7、14、15、25、26）＋所有 Body>0 的使用者音色（Body 預設就是 0.5）會變小聲；CLI 不經過（CLI 的 Body 預設 0，只有診斷旗標 `--body-amount` 會開） | M |
| B | 不做；維持現狀（已有 CLIP 指示燈提醒，使用者自己調低「輸出音量」） | 不改 | 0 |

選項說明：A 就是根因報告 §7 的「B2」；需要一個新的慣例（「正規化到什麼」），依 R4 必須可溯源，不能是手調魔數。
選項 B 是 AI 補列的對照項（`HANDOVER.md` §1-5 只寫「B2＝響度正規化，需新的慣例常數（要月月裁）」，沒有列出不做的選項）。

**Fable 建議**：查不到 Fable 對 B2 的獨立原文。可查到的建議出處是 WF1002 追加裁決包 N1 的「建議」段：「**B1**（拿掉壓縮器補償）先做；
B1 之後 preset 11 把 Body 調回預設 0.5 仍會超過（約 +3.8 dBFS）——Body 這層的結構問題可以之後用 B2 另開卡，CLIP 燈已經會提醒。」
即 B2 是 Fable／裁決包建議「之後另開卡」的那一件事。月月 10-03 的裁語是「照 Fable 的建議」，由規劃者轉成 B2＝A。

**月月裁語（2026-10-03）**：「好，都重跑，開 Dynamic Workflow，你負責規劃，opus5.5 驗證，sonnet5.5 當工兵。你說的裁決兩項，照你的建議規劃。」
→ 規劃者（Fable）轉成 **B2＝A（做 Body 層響度正規化）**。

> **2026-10-03 月月裁決：B2＝A**（WF1003-B2 卡落地）。
> **2026-10-03 稽核 FAIL、改動已還原**：Opus 稽核（`reports/gate_outputs/wf1003_B2_audit.txt`）發現增益 g 沒有上限——Custom Harmonics 深陷波設定下，
> 輸出比改前大 +22.7 dB、峰值 +14.80 dBFS；報告「只回到 Body 關的能量、不會超過」那句在外掛實測被推翻。建議修法＝`g = min(g, 1)`。
> **2026-10-07 重做（WF1004-B2b）**：月月 10-07 裁「兩題都照你的建議去做」＝照 Fable 建議加 `g = min(g, 1)`，裁決記錄見
> `reports/decision_packets/WF1004_decisions.zh-TW.md`；重做版前後對照見 `reports/wf1003_b2_body_normalization_before_after.zh-TW.md`（檔名沿用，內容標 WF1004 重做版），
> 證據 `reports/gate_outputs/wf1003_B2_*.txt`（WF1003 原版，含稽核）＋`wf1004_B2b_*.txt`（重做版）。
> 新慣例登記在 `ROADMAP_PHYSICS.md` §6「外掛 Body 層響度正規化」列（已補上限）。
> **2026-10-07 B2b 稽核 FAIL（驗收標準問題，不是程式問題）→ B2c 重落地**：`reports/gate_outputs/wf1004_B2b_audit.txt`：加上限版 473 組對抗案例輸出全部 ≤ 改前，但舊驗收標準「Body 開峰值 ≤ Body 關」連改前都達不到（改前（未正規化）Body 開對 Body 關的樣本最大差為 +16.58 dB（稽核獨立掃描 +14.98 dB）；+3.98 dB 是加上限後對 Body 關的殘差樣本最大值，不是上界）。
> 月月委託 Fable 裁、採稽核 §8 選項 (1)：驗收標準＝「加上限版逐案例輸出峰值 ≤ 改前」（對每一顆 voice；和弦疊加掃描 159 組 0 違反，但證明層級是單 voice）＋「g ≤ 1 恆成立」；「Body 開可比 Body 關大」如實寫進文件。裁決與理由見 `reports/decision_packets/WF1004_decisions.zh-TW.md` B2b／B2c 一節；
> 程式沿用 B2b patch 一行未改，文件與測試斷言改成實測數字（`reports/gate_outputs/wf1004_B2c_*.txt`）。**上面「只回到 Body 關的能量、不會超過」那句在外掛實測不成立（前 0.3 s 能量樣本最大值 +3.69 dB，非上界），以 B2d 修正後的文件為準（B2c 文件有三類句子經稽核更正，見 `WF1004_decisions.zh-TW.md` 第三段）。**

---

## Q09　Voice pool 要不要從 16 加大到 32（證據門檻制）

**題目**：外掛每個引擎各一個 `juce::Synthesiser`、各 16 顆 voice（`src/PluginProcessor.cpp`）。月光第一樂章舌鼓版（Chromatic 引擎，最多同時 20 顆）
在 16 顆時被搶 64 次（4 次搶到還按著的音；WF1002-C1 實測，`reports/gate_outputs/wf1002_C1_hostprobe.txt`）。要不要把 pool 加大到 32？
（出處：`HANDOVER.md` §1-5「Q09 voice pool」；`docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §10；WF1002 裁定 Q09＝D 當時沒裁要不要加大。）

| 選項 | 做法 | 影響 |
|---|---|---|
| A | 直接加大到 32 | 外掛層：月光舌鼓版不再被搶（聲音改變，R10 範圍）；CLI 不變（CLI 不用這個 pool） |
| B | 維持 16 | 不改 |
| **C（採用的做法）** | **證據門檻制**：先量 16 與 32 的搶音次數與音訊執行緒處理負載，32 全部達標才採用，否則維持 16 並寫明原因 | 由數字決定 |

**Fable 建議**：「照 Fable 的建議」＝月月 10-03 轉述的 Q09 後續做法：pool 16→32，但採證據門檻制——「32 無即時違規（處理時間餘裕仍足）且搶音明顯下降才採用，否則維持 16 並寫明原因」。
（原文：本輪 V 卡任務書的裁決依據段；Fable 的獨立原文查不到，只有規劃者轉述。）

**月月裁語（2026-10-03）**：「好，都重跑，開 Dynamic Workflow，你負責規劃，opus5.5 驗證，sonnet5.5 當工兵。你說的裁決兩項，照你的建議規劃。」
→ 規劃者轉成「Q09 後續＝C：證據門檻制」。

**判準（量測前寫好）**：`reports/gate_outputs/wf1003_V_criteria_preregistered.txt`（C1 搶音減半、C2 零即時違規、C3 最慢區塊 ≤ 預算一半、C4 不該變的不變）。

**落地結果（2026-10-03，V 卡）：維持 16。**

| 判準 | 結果 |
|---|---|
| C1 搶音減半 | 通過：月光舌鼓版 64 → 0 |
| C2 零即時違規 | **不通過**：32 顆 Piano 同時發聲，一個 512 取樣區塊平均 7.3 ms、p99 20.5 ms，預算 10.667 ms，每次重複 148～153 個區塊（約三成）來不及（16 顆時平均 2.4 ms、p99 10.5 ms）；真 VST3(32) 3 輪合計 448 個區塊 |
| C3 餘裕 ≤ 預算一半 | 不通過，但這條的量法（最慢單一區塊）會被作業系統偶發尖峰污染，pool 16 也不過；結論不靠它 |
| C4 不該變的不變 | 通過：給愛麗絲 16／32 輸出逐樣本相同；CLI 不共用 pool |

- 原因一句話：32 對 Chromatic（舌鼓）很輕、也確實消除搶音，但同一個 pool 數字也套在 Piano 上，Piano 滿載 32 顆來不及。
- 順便看到：現行 16 顆 Piano 低音區滿載時 p99 已 10.5 ms（貼著預算）——是 Piano voice 的成本，與 pool 大小無關，建議列入已知限制（要月月裁）。
- 沒量到：FM 引擎、DAW 內與其他音軌同跑、記憶體。數字來自開發機（Ryzen 5 3500X），比例可帶走、絕對值不行。
- **未採用但數字支持、需另裁的選項**：按引擎設不同大小（Chromatic 32、Piano／FM 16）。會改主張域 §10 的字面且 FM 沒量，本卡不擅自做。
- 報告：`reports/wf1003_v_voice_pool.zh-TW.md`；證據：`reports/gate_outputs/wf1003_V_*`（方法 `wf1003_V_method.txt`）。
- 外掛層驗證：ctest 4/4、HostProbe（`TSUKI_Q09V` 未設）[PASS] 231／[FAIL] 0。CLI 不變（CLI 不編 `PluginProcessor.cpp`）。
- 字面：`docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §10 的 16 顆不動（結論＝維持 16），檔尾補記一點。
- **未 commit、未 git add**（R7，等整合卡稽核）。
