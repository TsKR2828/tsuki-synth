# WF0908-P1：partial 頻率內部一致性驗證器（A13 選 B+ ＋ C13 harmonic-aware）

> lane：Python　工兵：Sonnet　共同規約：先讀 `WF0907_README.md`（lane/建置目錄/R 規則全部沿用）
> 依據：`reports/decision_packets/A13_partial_gate_domain.zh-TW.md` 裁決記錄（B+）、`TODO.md` C13、
> 設計文件 `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8（月月裁定：音高與起音分開主張；不可宣稱「泛音已驗證」）。

## 0. 一句話目標

新工具 `tools/partial_verify.py`：對乾聲分軌（stem_verify C12 產物）逐事件量前 N 個 partial 的**頻率**，與 `--dump-modes` 預測比對（±5 cents，既有容差），
輸出逐 partial 結果；振幅**只記錄不判定**。**身分是 informational**（前置 C10 待月月裁決），程式與文件都要這樣標。
同一工具提供 harmonic-aware 音高判定（C13）：基頻帶被拒答的事件，改由 partial 頻率反推 f0 並**單獨**給 `pitch_via_partials` 欄位，不得併入 `verdict`。

## 1. 現況（規劃者已核實）

- `tools/stem_verify.py`（C11/C12 之後）：逐事件乾聲分軌 WAV 在 `<out_dir>/stems/`，JSON 有 `provenance`、逐事件 `reason`。**先讀它的 JSON 結構**。
- `--dump-modes` 每事件給 partial 的 `frequency` / `amplitude` / `decayTime`（layered 展開由 E9 提供）。
- 音高估計器已抽成 `melody_verify.measure_pitch_cents(...)`（C10）；量測器自證 1.17 cents（`reports/decision_packets/C10_selfcal_domain.zh-TW.md`）——本工具的 partial 頻率量測**重用同一函式**（把「期望 f0」換成「期望 partial 頻率」），不另寫估計器。
- 容差 ±5 cents 出處：設計文件 §8.4 第 2 點。**不可新設容差**。
- 已知 partial 污染機制：三弦 detune 展寬 ±5 cents（`ScoreParser.h` 預設）、鄰音泛音入帶（Rb）——沿用 melody_verify 既有拒答邏輯，partial 帶碰撞一律拒答並記 reason。

## 2. 設計

- CLI：`python tools/partial_verify.py <stem_verify 報告.json> [--partials N=6] [--json out.json] [--html out.html]`。
  從 stem_verify 報告讀 stems 路徑、乾聲衍生 score、dump-modes（自己再跑一次 `--dump-modes` 於衍生 score，記 sha256）。
- 逐事件逐 partial：期望頻率 = dump 的 `frequency`；量測窗沿用 melody_verify 的起音精修結果；
  結果 `{"n": k, "expected_hz", "measured_cents", "verdict": PASS/FAIL/UNVERIFIED, "reason", "amplitude_db_rel_f1_measured", "amplitude_db_rel_f1_predicted"}`——
  振幅兩欄**只記錄**，schema 註明 `"amplitude_claim": "none"`。
- 事件層：`partials_verified` 計數、`partials_refused` 計數；報告層 `status: "informational"`、`gate_ready: false`、`gate_ready_reason: "C10 pending 月月裁決"`。
- C13：若事件在 stem_verify 中 `verdict == UNVERIFIED` 且 reason 屬「基頻帶能量不足」類，用量到的 ≥2 個 partial 以 `f_n = n·f0·√(1+B·n²)` 最小平方反推 f0（B 取 dump 的 f2/f1 反推，不引外部 B），
  給 `pitch_via_partials_cents` 與 `pitch_via_partials_verdict`；**`verdict` 欄位原值不動**。
- 哨兵（`tests/test_partial_verify.py`）：(a) 合成訊號已知 partial 全 PASS；(b) 把第 3 partial 偏 +8 cents → 只有 n=3 FAIL；(c) 缺 partial → UNVERIFIED 非 PASS；(d) 振幅改 ×10 → 頻率 verdict 不變且振幅欄如實記錄；(e) 報告 `gate_ready` 必為 false（防止有人偷翻）。
- 文件：設計文件 §8 加 §8.6「partial 頻率工具（informational）」；`B` 對照報告（A13 B+ 的②）由本工具 `--b-report` 產生：每音 dump 反推 B vs A13 §3.3 的 Fletcher 參考值，只列比值。

## 3. 步驟

1. 讀 stem_verify JSON 與 C10 的 `measure_pitch_cents` 簽名。
2. 實作 + 哨兵。
3. 實跑：給愛麗絲鋼琴版（C12 的乾聲報告，若無就先跑 `stem_verify.py --limit 60 --json ...`），貼統計：partials 量到幾顆／拒答幾顆／最大 cents；22 顆弱基頻音中在此範圍內者的 `pitch_via_partials`。
4. `--b-report` 產一份 `reports/gate_outputs/wf0908_P1_b_ratio_report.txt`。

## 4. 禁止

- 不改 melody_verify / stem_verify 的判定；不新增容差；不把振幅寫成 verdict；不把 `gate_ready` 設 true。

## 5. GATE（輸出到 `reports/gate_outputs/wf0908_P1_partial.txt`）

1. `pytest tests/test_partial_verify.py -q` 全綠（≥5）。2. 實跑統計。3. `python -m pytest tests -q` 全綠。
4. `git diff --stat` 只含 `tools/partial_verify.py`、`tests/test_partial_verify.py`、設計文件、證據檔。
