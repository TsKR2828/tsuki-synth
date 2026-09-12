# WF0909-C10B-audit：稽核並入庫 C10B 修正回合的誠實撤回（估計器＝舊版、gain-fidelity 掃描、文件）

> 稽核專用卡（無工兵）　稽核：Opus　共同規約：`WF0907_README.md`
> 背景：WF0909-C10B 第一版估計器（柔化質心）被稽核抓到「以期望 f0 為中心柔化＝把量測值往目標拉」的假改善；
> 修正回合已把 `measure_pitch_cents()` **撤回到與 `measure_pitch_cents_legacy()` 位元組相同**，另試 mean-shift 變體亦否決，
> 並新增 `measurement_selfcal.py::gain_fidelity_scan()`（期望值固定、真值偏離的軸）與 `test_gain_fidelity_no_regression_vs_legacy`，
> 文件（設計文件 §9.4/§9.5、裁決包 §5、HANDOVER §4、`reports/c10b_estimator_before_after.md`）改寫為「尚未達成」。
> 修正回合因整卡目標（≤1 cent）未達而回 RED，所以這批誠實成果從未進稽核。**規劃者裁決（2026-09-09）**：把「誠實工具與記錄」與「1-cent 達標」分開，本卡只稽核前者。

## 稽核要做的
1. `git diff -- tools/melody_verify.py`（unstaged）：確認產品路徑 `measure_pitch_cents()` 與 `measure_pitch_cents_legacy()` 數值等價
   （親自跑 `tests/test_measurement_selfcal.py::test_measure_pitch_cents_matches_legacy_after_revert`，並自己寫 20 個隨機合成訊號比對兩函式輸出位元相同）。
   docstring 若保留五個候選的數字表，核對與 `reports/gate_outputs/wf0909_C10B_estimator.txt` step 2 一致。
2. `python tools/measurement_selfcal.py`（預期 exit 1，開發網格 1.1721 c）與 `--holdout`（預期 1.0840 c）——確認數字可重現、且 `HOLDOUT_T_ONSET_S=0.0507` 真的不對齊 hop（0.0507×48000/256 非整數）。
3. gain-fidelity 掃描：確認它把「期望值固定、真值偏 ±12 c」這條軸真的量進去（挑 MIDI 37 手算：真值 +12 c → 舊估計器應量到約 +8.6 c，增益 0.72）。
4. 牙齒：把 `measure_pitch_cents` 換回柔化版（或任意把增益壓低的 mutant）→ `test_gain_fidelity_no_regression_vs_legacy` 必須紅；還原。
5. `python tools/melody_verify.py --selftest` 5/5；`PYTHONPATH=tools python -m pytest tests/test_stem_verify.py tests/test_measurement_selfcal.py -q` 全綠（C10B 撤回後 stem 測試應回綠——第三輪 D8/P4b 的 2 failed 就是被柔化版弄紅的，請確認現在綠）。
6. 文件措辭：任何地方**不得**出現「量測器已自證」；HANDOVER §4 第 2 點、設計文件 §9.5、裁決包 §5 三處一致寫「尚未達成、待月月裁決 A／或架構外方法」。
7. `reports/c10b_estimator_before_after.md`「修正回合」章節：真實音檔重跑數字（selftest、sentinel、H6 25/25、corpus 30 檔強域、給愛麗絲、月光 v4）要有命令與輸出可對；「零迴歸」的主張只能寫成「與 C10B 之前逐檔相同」（這是可證的），不能寫成「更準」。

PASS 時 stage：`tools/melody_verify.py`、`tools/measurement_selfcal.py`、`tests/test_measurement_selfcal.py`、`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md`、
`reports/decision_packets/C10_selfcal_domain.zh-TW.md`、`HANDOVER.md`、`reports/c10b_estimator_before_after.md`、`reports/gate_outputs/wf0909_C10B_estimator.txt`。
