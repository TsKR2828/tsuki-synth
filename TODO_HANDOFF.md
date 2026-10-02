# TsukiSynth — Deep-fix Handoff

> ## ⚠ 歷史文件（2026-07-17 快照）——最新狀態看 `HANDOVER.md`／`TODO.md`
>
> **2026-09-25 標註**：這份是 2026-07-17 深修第一輪的交接，之後沒有更新，**不要拿來當現況**。
> 新 session 請從 `HANDOVER.md` 開始，待辦與裁決看 `TODO.md`，驗收規則看 `ROADMAP_PHYSICS.md`。
> 內文保留原樣當歷史紀錄，只修了下方重跑指令的建置行與 Python 測試行（見該段註解）。
>
> 已知過時處（舉例，不是完整清單）：
>
> | 本檔原文 | 現況（2026-09-25 查證；2026-10-03 更新） |
> |---|---|
> | release corpus 73/73 | 75/75（2026-09-25 重跑；2026-10-02 WF1002b 整合卡再確認） |
> | 「cross-platform bit identity is not」（沒提其他） | 仍不承諾位元相同；但 2026-08-22 已登記跨平台容差（C3，`scores/crossplatform_tolerance.json`），CI 每次 push 做 Windows MSVC／Linux GCC／macOS AppleClang 三平台渲染比對 |
> | 「Current branch」 | 分支名稱沒變，但已多次 merge 進 `main`（最近一次 `3f9b90a`，2026-09-15）；之後的成果 2026-09-30～10-03 已 push 到分支（`168688e`），尚未 merge `main` |

> Updated 2026-07-17. Current branch: `fix/deep-physics-audit-20260716`.

## What changed

- Tuner now measures dry audio instead of echoing the MIDI target. It covers A0–C8 across 44.1–192 kHz, reports target/measured Hz, cent error and confidence, and refuses ambiguous/out-of-range input.
- MIDI target tracking is channel/note/retrigger/sustain aware and handles CC120/121/123.
- Beam physics defaults to a fixed-free cantilever for a tongue; free-free is explicit. Plate radial mode shapes obey centre/edge nodes and free-edge roots vary with Poisson ratio.
- Damping is recomputed after final tuning/detuning; hammer contact time varies with strike velocity; weak modes live to their relative −60 dB threshold.
- Score/schema parsing is strict. `membrane` and no-op fields are rejected. `frequency_mode`, `beam_boundary`, `random_seed`, custom partials, mode identity and render manifests are wired end to end.
- Offline effects now use the same DSP classes/order as the plugin. Delay supports the full 5 s contract and advances at zero time/mix. Reverb decay is a per-comb T60.
- Layer paths, working-set budget, trim copies, derived tails, batch sorting/collision preflight and atomic audio writing are hardened.
- Presets use stable IDs and cached states; missing/deleted presets no longer claim the wrong program.
- Material database reload is transactional and rejects non-physical constants.

## Truthful acceptance state

- Checked physical cases pass.
- Rubber short-transient material cases remain three explicit `UNVERIFIED/N/A` ranges.
- Same-machine deterministic rendering is verified; cross-platform bit identity is not.
- FM, creative macros and effects remain outside physical verification.
- Draft 2020-12 schema is 80/80; the latest release corpus is 73/73 PASS with only the existing visible moonlight FX-art exemption.
- Rules-v2 event-specific consonance is 13/13 PASS, 0 violation, 0 unverified.

## Required rerun after further code changes

```powershell
# 2026-09-25 修正：原本只建三個測試 target，照做 ctest 會出現 spectrum_view_repro「Not Run」（09-07～14 CI 紅燈同一個坑）。
# X4 規約：跑 ctest 前必先重建五個測試 target（HostProbe 不在 ctest 內，要另跑，見 README quick reference）。
cmake --build build --config Release --target TsukiSynthCLI TsukiSynth_VST3 TsukiSynth_Standalone TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest TsukiSynthSpectrumViewTest TsukiSynthHostProbe
ctest --test-dir build -C Release --output-on-failure
# 2026-09-25 修正：現行全套 Python 測試用 pytest（原本這行只跑三個檔）。
python -m pytest tests -q
python tools\tuner_audit_v2.py
python tools\physics_verify.py --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --selftest
python tools\physics_verify.py --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --full
python tools\verify_score.py --all --quiet --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe
python tools\check_piece_consonance.py scores\originals\rules_v2_demo\rules_v2_demo_001.score.json --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --out reports\rules_v2_demo_consonance_check.md
```

See `docs/DEEP_FIX_VERIFICATION_2026-07-17.zh-TW.md` for methods, results and remaining distance to the final goal.
