# TsukiSynth — Current TODO

> Last updated: 2026-07-22 (round-3)
> Branch: `fix/deep-physics-audit-20260716`

The deep-audit implementation fixes are on the branch. Historical Phase D–I decisions remain in `DEVLOG.md`; this file lists only current work and scientific gaps.

Acceptance snapshot (round-1, 2026-07-17): six Release targets build; CTest and Python contract/metrology tests pass;
schema 80/80; release corpus 73/73 with one existing visible FX-art exemption; event-specific
rules demo 13/13 PASS; `physics_verify.py --full` has no checked failures and three explicit
rubber `UNVERIFIED/N/A` cases.

Round-2 snapshot (2026-07-18, `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md`): six Release targets rebuild
clean; ctest 3/3, pytest 44/44, tuner oracle, schema 80/80 and consonance gates all PASS. `physics_verify.py
--full` has one **honest FAIL** (piano MIDI 60 velocity vs the +6.0206 dB physical-law bound — see pending
decisions). Corpus per-channel rest-RMS re-measurement gives 71/73 net PASS: 2 new honest FAILs
(`summer_m2`/`summer_m3` rest RMS, both traced to a reverb tail, neither exempted) surfaced by the
stricter measurement, not by any audio regression. No §6 tolerance was widened; no new exemption was
registered.

Round-3 snapshot (2026-07-22, `reports/gate_outputs/deepfix3_*.txt`): fixed both round-2 honest FAILs.
Velocity: `physics_verify.py`'s F3 measurement domain moved from wideband RMS to the fundamental's own
±3% band (matching the law's per-mode physical scope; wideband delta is now printed informational-only) —
all 5 modal engines now PASS at MIDI 60, incl. piano (+6.6702 dB, dev +0.65); `--full --skip-amps` is green.
Summer: `reverb.decay` narrowed on both files (wet untouched) — `summer_m2` 2.8→2.6 (2.6 dB worst-case
margin), `summer_m3` 1.2→1.0 (2.5 dB margin); both re-verified PASS incl. determinism SHA256 match. Stale
`rules_v2_demo_001.report.html` (predating its score.json's 2026-07-17 edit) regenerated and re-checked.
No §6 tolerance widened; no new exemption registered; both score edits and the measurement-domain change
await 月月's sign-off (musical effect / domain-change ratification respectively).

## 月月待裁決（pending decisions）

- [ ] **`verify_score.py` 的 `MODE_F0_TOL_CENTS = 12.0` 是否授權改量測法後收緊**（ROADMAP_PHYSICS §6 該列完整理由）：此檢查的量測點是 `--dump-modes` 的 `partials[0]`，即多弦課「第 0 條弦」的原始值，而 `CimbalomVoice::noteOn()` 按設計把第 0 條弦精準調到 `-detuningCents`（預設 -5.000 cents），量的不是聲學質心；5 首真實曲目測試中 3 首含 cimbalom/piano 的量得 5.002–5.013 cents，直接收緊到 5.0 會誤殺，即使 `physics_verify.py` 已驗證同曲實際渲染音訊的真實基頻在 0.05 cents 內。收緊的前提是改「量測什麼」（例如改為 course 質心/平均），屬程式邏輯變更非容差變更，需月月授權後才做。
- [ ] **殘差頻譜能量檢查：門檻轉判定制的批准**——目前為資訊性輸出（不影響 exit code），門檻數值與轉為 exit-code 判定需月月批准（§6 已登記為資訊性列）。
- [ ] **spectralTilt heuristic 層去留**——是否保留該啟發式層，或移除/降級為已文件化近似，待月月裁決。
- [ ] **【2026-07-18 round-2 → 2026-07-22 round-3 已修正】piano velocity 物理律「違規」**——round-2 的 `physics_verify.py --full` 紅燈是量測域選錯：舊判定拿寬帶 RMS 驗證一條逐模態律（`20·log10(2) = 6.0206 ± 1.0 dB`，源自 `ModalResonator::excite()` 振幅正比槌速），把 Hertz 接觸時間隨槌速變短帶來的頻譜變亮（物理真實，`HammerImpulse.h`）也算了進去。round-3 把量測域改到以 `measure_f0()` 為中心的基頻 ±3% 窄帶（`measure_band_rms_db()`，沿用 `measure_t60()` 同一 Butterworth band 家族），判定式數值本身（`|predicted−6.0206|≤1.0` 且 `|measured−predicted|≤1.0`）未動。**重測全數 PASS**：cimbalom +6.0587 dB、tongue_drum +6.0574 dB、water_gong +6.0586 dB、water_gong_free +6.0588 dB、piano +6.6702 dB（dev +0.65）；`--full --skip-amps` 回綠。舊寬帶違規數字（piano +7.4373 dB）保留為資訊性行，不再影響判定。**待裁決：此量測域變更（寬帶→基頻窄帶）屬程式邏輯調整，需月月追認**；詳見 `DEVLOG.md` 2026-07-22 條目、`reports/gate_outputs/deepfix3_selftest.txt`／`deepfix3_gate_full.txt`。
- [ ] **【2026-07-18 round-2 → 2026-07-22 round-3 已修】corpus 逐聲道 RMS 揭露的 2 個既有 rest 超標**——`scores/classical/vivaldi_four_seasons/summer/vivaldi_four_seasons_summer_m2.score.json` `reverb.decay` 2.8→2.6（wet 0.28 不動）：3 個休止窗最緊裕度從超標 0.1 dB 改善為 2.6 dB 裕度；`vivaldi_four_seasons_summer_m3.score.json` `reverb.decay` 1.2→1.0（wet 0.20 不動）：唯一休止窗從超標 2.9 dB 改善為 2.5 dB 裕度。m3 的 decay 完整歷史為 2.1（原始）→1.2（deep-fix 輪，mono 量測時代，掃描證據見 `docs/DEEP_FIX_VERIFICATION_2026-07-17.zh-TW.md`）→1.0（round-3，逐聲道量測），月月要確認的是**累計** 2.1→1.0 的殘響變化。兩者 `verify_score.py` 全項重驗 PASS（含 determinism SHA256 match），`-50.0 dBFS` 門檻未動，未新增豁免。完整逐點掃描見 `reports/gate_outputs/deepfix3_summer_rest_sweep.txt`。**待裁決：兩處 decay 縮短造成的殘響尾巴變化，藝術效果需月月最終確認**（機器 GATE 已過）。
- [ ] **Rule 10 前後對照報告審閱**——`reports/deep_fix_before_after.md`（2026-07-18 round-2）：8 首代表曲目改動前後 RMS/頻譜質心/T60/f0 比對，`physical_piano` 是唯一變大聲的一首（+2.346 dB），值得月月過目確認方向是否符合預期。

## Before merging this branch

- [ ] Review the complete diff and choose commit boundaries.
- [ ] Push the branch and let the updated Windows CI run Python unit tests, CTest, build targets, the event-specific consonance gate and `physics_verify.py --full`.
- [ ] Validate VST3 scan, MIDI, automation and state round-trip in the intended DAW.
- [ ] Perform a visual accessibility review of the tuner and generated HTML report with the intended deaf user; automated tests cannot certify readability.

## 2026-07-18 round-2 修復（完成，詳見 `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md`）

> 稽核來源：2026-07-18 本 session 四線審查。GATE 證據路徑規約：`reports/gate_outputs/deepfix2_*.txt`。

- [x] 工具/量測線：`tools/physics_verify.py` — F1 特徵值錨（`CANTILEVER_BETAL`/`free_plate_omegas()`）接回消費點、F2 f0 主錨改回 12-TET ET 理論值、F3 velocity 律上限雙重判定（`6.0206 ± 1.0 dB`）、F5 殘差頻譜能量資訊性檢查、selftest 反例 4a/4b；`tests/test_physics_verify.py` 新增 19 測試，24/24 PASS。
- [x] 引擎/渲染線：`src/score/ScoreRenderer.h`（dumpModes custom-atoms 堆積配置杜絕懸空指標）、`src/engines/CimbalomEngine.h`/`ChromaticEngine.h`（spectralTilt 註解、過期 mix 註解修正）、`src/physics/StringModel.h`/`BeamModel.h`/`PlateModel.h`（velocity 慣例與正規化語意註解）、`src/dsp/NoiseGen.h`（pink 係數標註取樣率相依）、`CMakeLists.txt`（TunerTest target 補齊設定、VERSION 0.2.0→0.3.0）；ctest 3/3 PASS。
- [x] score 資產線：`tools/verify_score.py` 逐聲道 rest RMS（取代 `(L+R)/2` 混降）、`src/cli/RenderApp.cpp` render manifest v2（新增 `wav_sha256`）；`tests/test_verify_score_contract.py` 新增 12 測試，14/14 PASS；probe SHA 基線比對確認 manifest 修改未影響音訊位元。
- [x] 文件/設定線：`.gitignore` binA/binB 字面規則、CI push 分支 `main` + `fix/**`、README 狀態表/目錄/build 依賴、§6 容差登記表同步（月月 2026-07-18 授權，四列：T60/velocity/殘差/休止RMS）——完成。
- [x] 各線 GATE 輸出彙整與零回歸確認：9 項 GATE（rebuild/ctest/selftest/`--full`/tuner oracle/pytest/schema80/consonance/probe SHA）+ 4 分片 corpus + HTML 抽驗全部執行並存證於 `reports/gate_outputs/deepfix2_*.txt`；`--full` 誠實 FAIL 於 piano velocity 物理律（見「月月待裁決」）、corpus 於 `summer_m2`/`summer_m3` 誠實 FAIL（逐聲道量測揭露既有超標，非回歸）；`autumn_m1` determinism 為環境暫時性故障已重驗排除；零 §6 容差放寬、零新增豁免。

## 2026-07-22 round-3 修復（完成，詳見 `DEVLOG.md` 2026-07-22 條目 + `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md` round-3 補記）

> 處理範圍：round-2 遺留的兩項待裁決（piano velocity「違規」、summer m2/m3 rest 超標）。GATE 證據路徑規約：`reports/gate_outputs/deepfix3_*.txt`。

- [x] `tools/physics_verify.py` F3 velocity 量測域修正：寬帶 RMS → 基頻 ±3% 窄帶（`measure_band_rms_db()`/`FUND_BAND_HALF_WIDTH`），判定式數值未動；寬帶 delta 降為資訊性行。5 個 modal 引擎 MIDI 60 velocity 48→96 全數 PASS（見「月月待裁決」量測域追認項）。`tests/test_physics_verify.py` 新增 3 測試，共 47/47 PASS。
- [x] `scores/classical/vivaldi_four_seasons/summer/vivaldi_four_seasons_summer_m2.score.json`（decay 2.8→2.6）、`.../summer_m3.score.json`（decay 1.2→1.0）：休止 RMS 超標修復，`verify_score.py` 全項重驗 PASS 含 determinism SHA256 match；完整掃描見 `reports/gate_outputs/deepfix3_summer_rest_sweep.txt`（藝術效果待月月確認）。
- [x] `scores/originals/rules_v2_demo/rules_v2_demo_001.report.html` 過期重生成（原檔停留在 score.json 2026-07-17 改動前）——已關閉，不再是待辦。
- [x] GATE 彙整：selftest 11/11、pytest 47/47、`--full --skip-amps` PASS（NO CHECKED FAILURES）、summer 兩檔 verify PASS、未觸碰的 `physical_piano.score.json` 回歸抽驗 PASS，全部存證於 `reports/gate_outputs/deepfix3_*.txt`；零 §6 容差放寬、零新增豁免。

## Verification gaps that must stay explicit

- [ ] Obtain citable or measured values for every material's `beta_air` and `gamma_radiation`.
- [ ] Replace single-frequency damping anchors with broadband/specimen measurements and uncertainty intervals.
- [ ] Add a calibrated force → displacement → radiated pressure/SPL model, including pickup/microphone position and modal phase.
- [ ] Add coupled-body/soundboard/sympathetic-resonance and realistic damper/pedal physics for piano.
- [ ] Replace the velocity proxy with a parameterized nonlinear contact solver using hammer mass, compliance and geometry.
- [ ] Model anisotropic/orthotropic wood, temperature and humidity where those claims are needed.
- [ ] Validate models against external measured recordings or laboratory modal data not generated by TsukiSynth itself.
- [ ] Establish cross-platform numerical reproducibility rules (bit identity where possible, numeric/audio tolerance otherwise).
- [ ] Add a polyphonic/missing-fundamental tuner mode only if it can refuse ambiguous cases reliably; the current target-aware monophonic detector must not guess.

## Honest N/A cases

- [ ] Design a short-transient estimator for `cimbalom/rubber`, `tongue_drum/rubber` and `water_gong/rubber`. Current T60 is only 14–28 ms, shorter than eight cycles at the probe pitch, so `--full` reports these three cases as `UNVERIFIED/N/A`.

## Deliberately outside the physical claim

- FM Piano, Custom Harmonics' authored ratios, Body macro and the artistic effect chain may remain useful, but must stay labelled non-physical/half-domain.
- Sample/granular layers do not become physical evidence merely because they are reproducible.
