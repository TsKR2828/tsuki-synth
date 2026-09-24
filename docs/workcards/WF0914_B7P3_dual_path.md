# 施工卡 WF0914-B7P3：B7 Phase 3 雙路徑比對 + Phase 2 裁決包

> lane：C++（只跑既有 build-wf 產物與 Python 工具，**不改任何 `src/`**）
> 前置：WF0914-B7P1 已 PASS。先讀 B7.md §6 Phase 2/3、§8 開頭「兩案並列」、§12；
> B7P1 的完成報告與證據檔（確認走了 §1.2 哪個分支）。

## 0. 一句話目標

執行 B7.md §6 步驟 11（雙路徑一致性檢查）＋把 Phase 2 的甲/乙案整理成正式裁決包。
**本卡不判 PASS/FAIL、不定門檻、不替月月選案**（B7.md §8：裁決前工兵不得自選）。

## 1. 雙路徑比對（B7P1 走「是」分支才有完整 Pa 可比；「否」分支則比對到 W_bridge 為止，報告明寫）

1. 選測試音：至少 C2/C4/C7 三音高 × 三力度（MIDI 40/77/108 對應的 score velocity；
   換算用 B7P1 落地的同一條 proxy 規則），引擎 Cimbalom 與 Piano、exciter=Felt。
2. 對每組跑 `--dump-modes`（build-wf CLI），同一份 JSON 讀出 Path B `"absolute_pressure_per_force"` /
   `acoustic_transfer[]` 與 Path C 對應欄位。
3. 記錄：逐 partial 與總量的 **實際差異倍率**（C/B），不平均掉方向性；嘗試歸因
   （B7.md §11 第三點的方向：能量守恆簡化高估 F_peak？S？σ 近似？），標明哪些是推測。
4. 產出 `reports/b7_dual_path_comparison.md`：數字表 + 歸因分析 + 「差異門檻待月月裁決」。
   原始 JSON 存 `output/wf0914/B7P3/`，關鍵數字進證據檔 `reports/gate_outputs/wf0914_B7P3_dualpath.txt`。

## 2. 裁決包 `reports/decision_packets/B7_phase2_and_open_items.zh-TW.md`

體例照 K02 裁決包。必含四節，全部「看數字就能選」：
1. **驗收基準 (a) 甲/乙案**：從 B7.md §8 開頭整段轉寫（甲=分音域相對動態範圍 GATE、乙=標 BLOCKED），
   補上本輪新事實（B7P1 實際落地到哪、雙路徑實測差異量級），每案代價/前提列表。**不選**。
2. **S 的採用記錄**：B7P1 §1.2 走了哪個分支、判定證據（參數溯源鏈原文）、月月是否追認。
3. **proxy 代決追認**：B7P1 §1.1 的查證結果與代決內容，附 ScoreParser 實際定義的引文。
4. **雙路徑差異數字**：§1 的表格摘要 + 「門檻由月月定」。

## 3. GATE

- `git diff` 只含上列 reports 檔案與（若有）B7.md/TODO.md 的狀態行同步。
- 每個寫進報告的數字都能對回 `output/wf0914/B7P3/` 的原始 JSON（稽核會抽查重跑至少一組渲染）。
- 位元不變：本卡只讀不寫 `src/`，不需重跑 8 首基準（稽核可抽驗 `git diff -- src/` 為空）。
