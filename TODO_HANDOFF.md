# TsukiSynth — Deep-fix Handoff

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
cmake --build build --config Release --target TsukiSynthCLI TsukiSynth_VST3 TsukiSynth_Standalone TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest
ctest --test-dir build -C Release --output-on-failure
python -m unittest tests\test_physics_verify.py tests\test_consonance_contract.py tests\test_verify_score_contract.py -v
python tools\tuner_audit_v2.py
python tools\physics_verify.py --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --selftest
python tools\physics_verify.py --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --full
python tools\verify_score.py --all --quiet --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe
python tools\check_piece_consonance.py scores\originals\rules_v2_demo\rules_v2_demo_001.score.json --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --out reports\rules_v2_demo_consonance_check.md
```

See `docs/DEEP_FIX_VERIFICATION_2026-07-17.zh-TW.md` for methods, results and remaining distance to the final goal.
