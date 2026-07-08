# TsukiSynth — TODO

> Last updated: 2026-07-07
> Branch: `Codex-fix-bug`
> **Goal: deaf people + AI verify/simulate sound by physical theory, not by ear.**

---

## Current Status

| Item | Status |
|------|--------|
| VST3 / Standalone / CLI build | ✅ exit 0 |
| Code audit (8 bugs) | ✅ fixed (Codex `b5a370d` + this session) |
| Deterministic render (same score → byte-identical) | ✅ NoiseGen seeding |
| Physics verification harness (`tools/physics_verify.py`) | ✅ all 6 engines PASS |
| CLI `--dump-modes` (single source of truth) | ✅ |
| Cimbalom MIDI-pitch tuning (stiff-string comp) | ✅ A4 +11c → +0.1c |
| Equal-RMS engine calibration | ✅ cross-engine 8 dB → 0.2 dB |
| Water gong = true clamped Kirchhoff plate | ✅ (was membrane approx) |
| Physical piano engine (CLI `"piano"`) | ✅ struck stiff steel string |
| Physical piano presets (plugin, on Cimbalom) | ✅ Grand / Bright Upright |
| Free-edge gong option (`plate_free_edge`) | ✅ default free-edge (physical: hung gong) |
| Plugin 4th "Piano" engine tab | ✅ APVTS stores denormalized (safe append) |
| Water gong default = free-edge | ✅ physically correct (hung plate, edges free) |
| Bilingual tooltip popups | ✅ warm white box, EN / 中文 on hover |
| Title bar subtitle for Piano engine | ✅ "PIANO ENGINE \| PHYSICAL MODELING STRING" |

---

## Resolved (was "Needs 月月 decision")

All three items resolved without ear-based verification — physics-based answers:

- [x] **Plugin 4th "Piano" engine tab** — confirmed APVTS stores **denormalized**
      (read JUCE 8 source: `flushToTree` writes `unnormalisedValue`). Appending
      "Piano" at index 3 is safe. Belt-and-suspenders: explicit `engine_index`
      int property in state save/load.
- [x] **Water gong default** — changed to **free-edge** (`plateFreeEdge = true`).
      Physical reasoning: a water gong is a hung plate with edges free. Clamped
      is the unphysical case. A/B scores still available for comparison.
- [x] **In-plugin loudness balance** — already verified by `physics_verify.py
      --levels` (cross-engine 0.2 dB). No ear-based action needed.

## Refinements (optional)

- [ ] Free-edge plate Ω values are approximate (Leissa ν≈0.33) — verify against a
      reference table before treating as precise.
- [ ] Advanced piano physics: hammer-felt nonlinearity, dedicated soundboard
      modes, damper pedal.
- [ ] `--t60` decay measurement is informational (audio decay fitting is noisy).

## Still pending

- [ ] DAW validation (host scan / automation / state round-trip) on a real DAW.
- [ ] `push` remaining commits for `Codex-fix-bug`; decide merge → master when ready.
- [ ] **CI workflow created, `--full` blocker now resolved — only `push` left** (`ROADMAP_PHYSICS.md` M1 task 1f):
      `.github/workflows/physics.yml` added 2026-07-02 (Windows runner, MSVC,
      builds CLI + Standalone + VST3, runs `physics_verify.py --full`).
      2026-07-05 update: M1 task 1e (`--full` flag) now exists and passes
      locally (`reports/gate_outputs/full_FINAL_gate.txt` → ALL WITHIN
      TOLERANCE), so the workflow's harness step will no longer fail with
      "unrecognized arguments." The only remaining blocker is the first push
      to GitHub to trigger the workflow at least once (M1 GATE requires "CI
      workflow 在 GitHub 上綠燈一次以上") — this is a `push`, so per rule 7
      (不 commit/push) it is 月月's call, not something to do automatically.
      README badge already points at `TsKR2828/tsuki-synth` (confirmed via
      `git remote -v`), not a placeholder.

## 月月待裁決（Phase D, 2026-07-07）

已解決、從清單移除的項目（不再需要裁決）：
- ~~`moonlight_sonata_complete` 休止超標~~ → 已登記為 `rests.rms` 豁免（`scores/verify_exemptions.json`，2026-07-07 月月經 Fable 批准），`verify_score.py` 重跑 exit 0。
- ~~5 首大型 Vivaldi 樂章 `--dump-modes` 逾時~~ → **真根因已找到並修復（2026-07-08）**：不是檔案太大，是 `ScoreRenderer::dumpModes()` 用 `juce::String` 累加輸出，每次 append 整段重配置複製 = O(n²)——3000 events 的 dump 光字串複製就 >600s。改用 `juce::MemoryOutputStream`（攤銷 O(1) append）後，最大的 summer_m3（5158 events）dump 只要 **7.2 秒**。timeout 1800s 保留作為安全網但已不再需要。四季 12 樂章全部重跑 **ALL CHECKS PASSED**（`reports/gate_outputs/corpus_phase_d_{autumn,spring,summer,winter}.log`）。
- ~~cimbalom/piano 共用增益常數的 piano RMS 偏離約 1.4 dB~~ → 已接受此妥協。

真正還剩的裁決/待完成項：

- [x] **M2 `--amps` 殘差 → 月月裁決（2026-07-09）：選 (b)，授權 C++ 層級儀器化
      追查**。下一輪（Phase E）：新增 `--dump-signal-stage` 除錯旗標，定位
      tongue_drum p2 的 -12.6 dB 未歸因殘差與各引擎 p3-p5 的 -3~-8 dB。
      容差 ±3.0 dB 照舊不動。根因基線見
      `reports/gate_outputs/amps_rootcause_analysis.md`。
- [x] **M2 力脈衝音色改變 → 保留**（2026-07-09 月月委任 Fable 決定）：物理正確
      （軟槌打中音域本來就發不出亮音）、有完整前後對照報告
      （`reports/m2_before_after_report.md`），且 Phase E 還會在此基礎上繼續修，
      不宜回退。
- [x] **CI 紅燈連動 → 採「M1 範圍綠燈 + amps 非阻斷可視化」**（2026-07-09 月月委任
      Fable 決定）：`physics_verify.py` 新增 `--skip-amps`（僅配合 `--full`，
      不影響 `--amps` GATE 本身）；`.github/workflows/physics.yml` 主 GATE 步驟改跑
      `--full --skip-amps`，另加 `continue-on-error` 的 `--amps` 步驟讓 M2 數字
      每次 CI 都看得到但不擋綠燈；verify_score 步驟改跑 5 檔跨引擎 smoke 子集
      （全 corpus 是本地 release gate，證據已歸檔）。**2d 通過後要把 --skip-amps
      拿掉、刪掉非阻斷步驟**——已寫在 workflow 註解裡。
- [x] ~~四季 12 樂章重跑~~ → **完成（2026-07-08）**：dumpModes O(n²) 修復後 12/12
      全部 ALL CHECKS PASSED。corpus 總計 **73/73：72 乾淨 PASS + 1 登記豁免
      （moonlight）、0 FAIL**。**M3 GATE 正式達成**：單次 `--all` → exit 0、
      `73/73 passed (1 exemption), 0 failed`
      （`reports/gate_outputs/verify_all_corpus_phase_d.log`）。M3 已標 Done。
- [ ] **CI 綠燈與 `--amps` 殘差連動（重要）** — `.github/workflows/physics.yml`
      跑的是 `physics_verify.py --full`，而 `--full` 現在含 2d 振幅判定（M2）。
      只要 2d 還 FAIL（見上方第一項），**push 上去 CI 必定紅燈**。月月的選項：
      (a) 先解決/接受 2d 再 push；(b) 授權 CI 改跑 M1 範圍（例如 `--full --skip-amps`
      之類的新旗標——這是 CI 範圍定義問題，需要月月點頭才能做，避免違反規則 3 的
      精神）；(c) 接受紅燈先 push 留紀錄。
- [ ] **M8 工程收尾** — DAW（Cubase）驗證四項（host scan / MIDI / automation /
      state round-trip）尚未執行；`Codex-fix-bug` merge → master 的時機仍待月月
      裁決（通常會在 push/CI 綠燈之後）。

## Housekeeping

- ~~Two dev logs coexist: `DEVLOG.md` (zh, current) + `DEV-LOG.md` (en) — converge one.~~ ✅ Merged into `DEVLOG.md`.
- `dsp/Reverb.h` / `dsp/EffectsChain.h` are CLI-side; `effects/*` are plugin-side
  (intentionally separate implementations).
