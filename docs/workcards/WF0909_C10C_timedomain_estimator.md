# WF0909-C10C：架構外的最後一次嘗試——時域最小平方擬合（NLS）估計 partial 頻率

> lane：Python　工兵：**Opus**（judgment 重，Sonnet 兩輪失敗）　共同規約：`WF0907_README.md`　前置：C10B-audit 已 PASS
> 依據：月月 2026-09-09 裁決 B「改估計器」；C10B 五個 STFT-bin 家族候選全數否決（設計文件 §9.4/§9.5）；稽核結論「真正的選項 C（架構外新方法）尚未找到」。
> **這是最後一次嘗試**：達不到就在裁決包 §5 寫明「B 路線於 STFT 與時域兩族皆試過」，建議月月改選 A。

## 0. 為什麼 bin 家族會卡住（規劃者分析，工兵先驗證這個判斷）
- 現行 STFT 參數 N_FFT=2048 @48 kHz → bin 23.4 Hz；MIDI 37（69.3 Hz）的 `band_of` ±3% 只有 ±2.1 Hz 寬，**比一個 bin 窄十倍**，
  質心/拋物線/相位差都在跟 Hann 主瓣的形狀打架，1.17 c 的系統偏差是這個幾何造成的，不是調參問題。
- 時域方法不看 bin：對帶通後的 1.25 s 片段直接擬合 `Σ_k A_k·exp(−t/τ_k)·cos(2π f_k t + φ_k)`，頻率解析度由片段長度與 SNR 決定（Cramér–Rao 下界在此 SNR 下遠低於 0.1 c）。

## 1. 硬性規格（任一條不滿足＝失敗）
1. **增益保真**：期望 f0 固定、真值偏離 ∈ {0, ±3, ±5, ±12, ±25, ±40} cents，量測值必須 |measured − true| ≤ 1.0 c（**不是** |measured − expected|）。
   這就是 C10B 沒設而被抓的那條軸；`measurement_selfcal.py::gain_fidelity_scan()` 已存在，把它從 informational 升為本卡 GATE 判定條件（門檻同 1.0 c，**不是新容差**，是月月 08-30 裁定的自證門檻沿用到這條軸）。
2. **開發網格與 hold-out 網格**（既有）皆 ≤ 1.0 c；hold-out 只在最後跑一次。
3. **course 語意保留**：三弦 −5/0/+5 c 等振幅合成 → 量到中心 ±1 c；三弦不等振幅（0.5/1/0.5）→ 量到中心 ±1 c（這是現行「course-centroid」主張，不可變成「最強弦的頻率」）。
   實作上：在帶內擬合 **1～3 個正弦**（模型階數由 BIC 或殘差門檻決定，門檻只能從合成資料的殘差分布導出並寫明），回報振幅加權平均頻率。
4. **拒答不變**：`band_of`、Ra–Re、碰撞/delay/fm_ratio 拒答全部維持；本卡只換 `measure_pitch_cents()` 內部的頻率估計數學。擬合不收斂／殘差過大 → 回 UNVERIFIED（fail-closed），不得回一個數字。
5. 起音精修、onset 判定不動。

## 2. 步驤
1. 先重現 §0 的判斷：對 MIDI 37 clean 訊號畫出 band 內 bin 分布（貼數字），確認 band 寬 < 1 bin。
2. 實作 `measure_pitch_cents()` 時域版（scipy `least_squares`，初值來自舊質心；帶通用既有 band；分段 20 ms–1.25 s 同 `PITCH_SEG_S`）。舊版保留 `measure_pitch_cents_legacy()`。
3. 自證：`measurement_selfcal.py`（開發網格）→ 增益保真掃描 → 三弦 course 合成 → 最後 `--holdout`。任一 > 1.0 c → 記數字，**不調參後再跑 hold-out**（hold-out 只能跑一次；若已跑過就寫明「已用過」並停）。
4. 通過才重跑既有證據（沿用 C10B 卡 §3 的九項清單；905 事件全曲 stem_verify 記憶體 28 GB 問題已知——改跑 `--limit 300` 並寫明，全曲另立卡）。每一顆 verdict 變動逐顆列出；**FAIL→PASS 一律先假設是假綠燈**，要用 gain-fidelity 數字證明不是。
5. 文件：設計文件 §9.6、裁決包 §6、HANDOVER §4；`tests/test_measurement_selfcal.py` 加 course 語意與增益保真的硬測試。

## 3. 失敗時的交付
- 裁決包 §6：「B 路線已在 STFT 家族（5 候選）與時域 NLS 皆嘗試，最佳數字為 ___ c（開發）/___ c（hold-out）/___ c（增益保真）」＋建議月月選 A，附 A 的主張域收窄措辭草案。status=RED。

## 4. 禁止
- 不改 ±5 c / ±10 ms / 1 c；不改拒答規則；不動 stem_verify / partial_verify；hold-out 只跑一次。

## 5. GATE（`reports/gate_outputs/wf0909_C10C_nls.txt`）
1. selfcal 開發網格 exit 0；增益保真掃描全部 ≤ 1.0 c；course 合成兩案 ≤ 1.0 c；hold-out exit 0（只一次）。
2. 既有證據重跑對照表。3. `python -m pytest tests -q` 全綠；`--selftest` 5/5。
4. `git diff --stat` 只含 `tools/melody_verify.py`、`tools/measurement_selfcal.py`、`tests/test_measurement_selfcal.py`、設計文件、裁決包、HANDOVER、報告、證據檔。
