# WF0909-C10B：改善音高估計器到 ≤1 cent 自證，並重跑所有既有音高證據（月月裁決 B）

> lane：Python　工兵：Sonnet（effort high）　共同規約：`WF0907_README.md`
> 依據：`reports/decision_packets/C10_selfcal_domain.zh-TW.md`；**月月 2026-09-09 裁決：B「改估計器重跑證據」**。
> 前置：WF0908-C10b 已把 C10 的重構與 `tools/measurement_selfcal.py` 稽核入庫。

## 0. 一句話目標

`melody_verify.measure_pitch_cents()`（stem_verify / partial_verify 共用）在合成哨兵上的最大誤差從 1.1721 cents 降到 **≤ 1.0 cent**，
且在**獨立的 hold-out 網格**上也 ≤ 1.0 cent（防止對開發網格過擬合）；然後把設計文件 §7/§8 引用過的每一份音高證據重跑，
逐檔比對 verdict 變化並寫進報告。**容差 ±5 cents / ±10 ms 一個字都不改**；1 cent 是月月裁定的量測器自證門檻，也不改。

## 1. 現況（規劃者已核實）

- 現行法：1.25 s 視窗、Hann/2048/hop-256 STFT 的頻帶質心（course-centroid）。系統偏差集中在 MIDI 37（~69 Hz）與 MIDI 100（~2638 Hz）附近，
  乾淨訊號 −6 dBFS 就有，與電平無關；相鄰半音無平滑趨勢 → bin 對齊造成的質心偏差（`C10_selfcal_domain` §0）。
- 哨兵工具 `tools/measurement_selfcal.py`：1170 格點（MIDI 36..100 × 諧波/非諧 B=1e-4,1e-3 × −6/−30/−60 dBFS），含 ±3 cents 靈敏度反例。
- 既有音高證據（全部要重跑，見 §3 清單）。

## 2. 設計

### 2.1 估計器候選（工兵擇一，理由寫進證據檔）
- (a) 帶內峰值的**拋物線內插**（log-magnitude 三點）取代質心；(b) **相位差法**（相鄰 frame 的相位進展反推瞬時頻率，對 bin 對齊不敏感）；
  (c) 加長視窗 / zero-padding 提高 bin 密度後再質心。
- 硬性要求：**只換頻率估計的數學，不動**帶選擇（`band_of`）、起音精修、Ra–Re 拒答規則、course/detune 處理。
- 新函式簽名與舊的相同；舊實作保留為 `measure_pitch_cents_legacy()` 供前後比對（不在產品路徑呼叫）。

### 2.2 過擬合防護（必做）
- **hold-out 網格** `tools/measurement_selfcal.py --holdout`：f0 = MIDI 36..100 每個半音**再偏移 +37 cents 與 −23 cents**（非四分音、非 bin 中心），
  B ∈ {3e-4, 2e-3}，電平 −12/−45 dBFS，起音時間用另一組非 hop 整數倍的值。開發時**不得**看 hold-out 結果調參；
  只在最後跑一次。開發網格 ≤1.0 且 hold-out ≤1.0 才算過。
- 靈敏度反例（±3 cents）兩個網格都要過。

### 2.3 重跑既有證據（§3 清單），每份產生 `<原檔名>.recheck_c10b.txt`，內含：舊 verdict 計數 / 新 verdict 計數 / 逐顆變化清單（PASS→FAIL、FAIL→PASS、UNVERIFIED 變動），
  並在總報告 `reports/c10b_estimator_before_after.md` 彙整（§0 白話導讀）。**任何 PASS→FAIL 都要逐顆解釋**（是舊估計器的假綠燈，還是新估計器的問題）。

## 3. 要重跑的證據（用 `build\` 的 CLI；WAV 若在 repo 內就直接用，否則依原記錄的命令重渲）
1. `python tools/melody_verify.py --selftest`（現況 5/5）。
2. `scores/tests/melody_sentinel.score.json` 完整 melody_verify（l1 哨兵）。
3. `PYTHONPATH=tools python -m pytest tests/test_stem_verify.py tests/test_measurement_selfcal.py -q`。
4. 給愛麗絲鋼琴版 stem_verify 乾聲全曲（`--analysis-dry` 預設，905 事件，約 10 分鐘 `--jobs 3`）——對照 `reports/gate_outputs/wf0907_C12_dry.txt` 的 8/34/864 與 §8.1 的 883/905。
5. 月光 v4 殘餘 38 FAIL 那份（`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §7 引用的 score/WAV；找不到 WAV 就依原命令重渲）。
6. `reports/gate_outputs/l3b_cubase_live.txt` 引用的 Cubase 匯出 WAV（若在 repo/reports 內）→ melody_verify 5/5 應維持。
7. HostProbe H6 五個 block size 的 WAV（`output/` 若已清就跳過，記明）。
8. corpus melody sweep（`melody_corpus_sweep_informational.txt`，81 檔）——**只重跑其中 30 檔「強域全綠」那組**，確認全部維持 PASS；48 檔弱域不重跑（記明理由：拒答率由規則決定，非估計器）。
9. `tools/partial_verify.py`（WF0908-P1 產物）在給愛麗絲上的統計前後對照（informational）。

## 4. 文件
- 設計文件 §9 改寫：新方法、開發/hold-out 數字、「量測器自證 ≤1 cent 已達成（日期）」；§7/§8 引用的數字若改變，就地更新並註明「C10B 重量」。
- `C10_selfcal_domain.zh-TW.md` 加裁決記錄：月月選 B，結果數字。
- `HANDOVER.md` §4 第 2 點的 5-cent 描述補「量測器自證 ≤1 cent」。

## 5. 禁止
- 不改任何容差；不改拒答規則；不改 stem_verify / partial_verify 的判定邏輯（它們只透過同一函式受益）。
- 不刪任何舊證據檔；新結果另存。
- 若試了三種方法都達不到 ≤1.0（含 hold-out），**停下**：回報三種方法各自的數字表，status=RED。

## 6. GATE（`reports/gate_outputs/wf0909_C10B_estimator.txt`）
1. `measurement_selfcal.py` 開發網格 exit 0（max ≤1.0）＋ `--holdout` exit 0 ＋ 靈敏度反例。
2. §3 九項重跑輸出與前後對照表。3. `python -m pytest tests -q` 全綠。
4. `git diff --stat` 只含 `tools/melody_verify.py`、`tools/measurement_selfcal.py`、`tests/test_measurement_selfcal.py`、設計文件、裁決包、HANDOVER、報告、證據檔。
