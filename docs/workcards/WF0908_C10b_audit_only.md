# WF0908-C10b：稽核並入庫 C10 的重構與工具（不含 1-cent 主張）＋ E9b 的 melody_verify layered 支援

> 稽核專用卡（無工兵）　稽核：Opus　共同規約：`WF0907_README.md`
> 背景：C10 卡工兵三次執行皆 BLOCKED（量測器自證 1.1721 cents > 1 cent，等月月選 A/B），因此從未進稽核，
> 但它的**重構**（`measure_pitch_cents` 抽出、抽出前後 JSON 逐位元組相同）與**工具**（`tools/measurement_selfcal.py`、`tests/test_measurement_selfcal.py`、設計文件 §9）
> 不論月月選 A 或 B 都要留在庫裡。整合工兵另在同一檔 `tools/melody_verify.py` 做了 E9b（layered 展開改走 E9 的 dump），整合稽核逐行讀過判定正確但因 C10 混在同檔拒絕 stage。
> **規劃者裁決（2026-09-09）**：把「工具入庫」與「1-cent 主張成立與否」分開；本卡只稽核前者。

## 稽核要做的
1. `git diff -- tools/melody_verify.py`：分辨 C10 hunk（`measure_pitch_cents` 抽出）與 E9b hunk（`expected_f0s_layered()`、`verify()` 的 is_layered 分流、移除 "layer expansion is not implemented" 拒答）。
2. C10 重構的數值不變證明：親自重跑 `reports/gate_outputs/wf0907_C10_selfcal.txt` GATE 1 的 before/after 方法（用 `git show HEAD:tools/melody_verify.py` 另存舊版），逐位元組比對。
3. `python tools/melody_verify.py --selftest`（現況 5/5，卡文寫 12 是舊字）、`PYTHONPATH=tools python -m pytest tests/test_measurement_selfcal.py tests/test_stem_verify.py -q`、`python tools/measurement_selfcal.py`（預期 exit 1、1.1721 cents——這**不是**本卡的 FAIL 條件，只確認工具可跑且數字可重現）。
4. E9b：三個 layered corpus 檔跑 `melody_verify.py`（informational），`--selftest` 仍 5/5；整合稽核提的 minor（layered 事件無 `params` → `is_course()` 用預設 3 弦/5 cents）請確認已在程式註解或設計文件誠實標註，沒有就列 major 交修正回合（修正回合由 Sonnet 工兵做）。
5. 牙齒：把 `measure_pitch_cents` 改成回傳 0 → `measurement_selfcal.py` 的靈敏度反例必須 FAIL；還原。
6. 設計文件 §9 的措辭：不得出現「量測器已自證」；必須寫「1.1721 cents，待月月裁決 C10 A/B」。

PASS 時 stage：`tools/melody_verify.py`、`tools/measurement_selfcal.py`、`tests/test_measurement_selfcal.py`、`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md`、`reports/decision_packets/C10_selfcal_domain.zh-TW.md`、`reports/gate_outputs/wf0907_C10_selfcal.txt`、`reports/gate_outputs/wf0907_C11_reason.txt`。
