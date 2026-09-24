# 施工卡 WF0914-D13：水鑼 2.0× partial 缺口的物理分析 + 裁決包

> lane：研究（**不碰 `src/`、`tools/`、`tests/`**——任何引擎改動會改渲染＝R10，另立卡）
> 先讀：`TODO.md` D13 原始登記、`src/physics/PlateModel.h`（只讀：現行自由邊平板模態表）、
> `docs/EXTERNAL_DATASET_SUPPLEMENT.zh-TW.md`（Iowa 泰國鑼那段）、
> `external_data/` 裡若有泰國鑼實測資料則用之（gitignored，先 `ls` 確認有什麼）。

## 0. 一句話目標

D13 登記：水鑼引擎（自由邊平板模型）在 2.0× 基頻**沒有 partial**，而真實泰國鑼（乳突鑼）
最強泛音正是 2.000×。本卡把「為什麼」與「能怎麼辦」寫成物理分析＋裁決包，不動引擎。

## 1. 分析內容

1. **現況量化**：列出現行 PlateModel 自由邊平板的模態頻率比（讀程式碼實際數字），
   確認 2.0× 附近最近的模態在哪、差多少 cents。
2. **實測對照**：Iowa 泰國鑼資料（或 A8 supplement 已記錄的數字）中 2.000× 泛音的相對強度；
   若 `external_data/` 有音檔，可用 `build\` 現成工具做頻譜量測（方法與數字進證據檔）。
3. **物理歸因（文獻支撐）**：乳突鑼 vs 自由邊平板的差異——中央乳突（boss）與弧形邊對模態的影響。
   候選文獻：Rossing 的鑼類研究（*Science of Percussion Instruments*、JASA 論文）、
   Fletcher & Rossing 鑼章節。規則同 D10：只引親自讀到的內容，逐字＋頁碼。
   關鍵問題：**2.0× 是乳突鑼幾何造成的模態調諧**（文獻怎麼說）。
4. 產出 `docs/GONG_PARTIAL_ANALYSIS.zh-TW.md`：上述三塊＋誠實標注哪些是文獻、哪些是推測。

## 2. 裁決包 `reports/decision_packets/D13_gong_2x_partial.zh-TW.md`

至少三案並列（不選）：
- A：找到可溯源的乳突鑼模態表 → 立新卡把水鑼引擎換/加乳突鑼模態集（R10，全 corpus 水鑼曲會變）；
- B：維持自由邊平板，主張域收窄——文件明寫「水鑼引擎模擬的是自由邊平板，非乳突鑼；
  2.0× 缺失是模型域限制」（體例比照 C10 選 A 的主張域收窄）；
- C：其他（分析中若浮現，如 score 層 layered 補 2.0× 音——需檢查這是否違反物理模擬原則，誠實評估）。
每案代價/前提/會動到的 GATE 列清楚。

## 3. GATE

- `git diff` 只含上列 docs/reports 檔案。
- 引文可溯源（稽核抽查 fetch）；量測數字可對回 `output/wf0914/D13/` 與證據檔
  `reports/gate_outputs/wf0914_D13_*.txt`。
