# TsukiSynth — Current Handoff Context

> Last updated: 2026-07-17
> Project: TsukiSynth（與 haguruma-engine 無關）

## Goal

讓聾人與 AI 不依賴聽感，而能用數值、物理模型與可重現測試建立聲音：

1. 可重現：相同 score、seed 與同一建置環境得到相同輸出。
2. 物理可驗：頻率、相對振幅、衰減可由程式對理論 oracle 驗證。
3. 樂器物理正確：弦、舌片梁、圓板使用相符的邊界條件與模態形狀。

## Repository state

- Local path: `C:\Users\admin\Desktop\Claude\tsuki-synth`
- Active branch: `fix/deep-physics-audit-20260716`
- This branch intentionally remains local/uncommitted until the owner decides to commit or push.
- User-owned untracked evidence under `reports/phase_h_before_after/binA/` and `binB/` must not be removed.

## Current implementation

| Area | Current contract |
|---|---|
| Tuner | Measures dry audio, displays TARGET and MEASURED separately, A0–C8 at 44.1/48/96/192 kHz, bounded ±700-cent search, confidence and explicit refusal states |
| Cimbalom / physical piano | Stiff-string modes, multi-string beating, final-frequency damping, deterministic PCG exciter noise |
| Tongue drum | Euler–Bernoulli fixed-free cantilever by default; explicit `beam_boundary: "free_free"` is available for a suspended bar |
| Water gong | Kirchhoff circular plate; score default is free edge, clamped is explicit; free-edge roots depend on Poisson ratio |
| Pitch semantics | `frequency_mode: "midi"` pitch-locks to the note; `"geometry"` keeps the absolute material/geometry prediction |
| Score contract | Unknown keys/engines, wrong types, irrelevant/no-op parameters, unsafe filenames and fake `membrane` aliases fail |
| Reproducibility | `global.random_seed` plus event index selects deterministic noise streams; render manifest records pre-normalization peak/gain/full-scale count |
| Effects | Plugin and CLI share Distortion → Compressor → Delay → Reverb; score delay supports 0–5000 ms; score reverb decay is a measurable T60 |
| Presets | Stable preset IDs, atomic replacement, cached user state, no user-preset disk read from program loading |

## Verification status

- `physics_verify.py --full`: no checked failures. Frequency range, velocity, partial amplitude and measured T60 pass. Three rubber cases are honestly reported `UNVERIFIED/N/A` because T60 (14–28 ms) is shorter than the required eight-cycle measurement window.
- Tuner Python acceptance: 1056 A0–C8 cases pass; 160 outside-range cases are refused; worst independent-oracle error 0.2076 cent.
- C++ regression suites cover tuner, MIDI note/sustain tracking, score parser/renderer, beam/plate shapes, frequency modes, T60, random streams, delay/reverb and effects parity.
- All 80 repository score JSON files pass Draft 2020-12 schema validation.
- Release audio corpus: 73/73 PASS, 0 FAIL; one existing moonlight FX-art rest exemption remains visible, with no new exemptions.
- Rules-v2 consonance validation now uses each event's real dumped modal spectrum; the demo is 13/13 PASS with 0 unverified pairs. The static MIDI 60 table is design reference only.
- Exact commands and remaining limitations are recorded in `docs/DEEP_FIX_VERIFICATION_2026-07-17.zh-TW.md`.

## Verification-domain boundary

- In domain: modal frequency ratios, relative modal amplitude under the implemented strike model, T60 law and deterministic score rendering.
- Half-domain: Custom Harmonics (authored ratios, not instrument physics) and MIDI pitch-lock mode (physical spectrum shape with equal-tempered f0).
- Out of domain: FM Piano, artistic Body macro, compressor/delay/reverb/distortion, and sample/granular ideas.
- Passing implementation-vs-oracle tests proves that code follows its equations. It does not prove that every material constant matches a particular real specimen.

## Standard commands

```powershell
cmake --build build --config Release --target TsukiSynthCLI TsukiSynth_VST3 TsukiSynth_Standalone
ctest --test-dir build -C Release --output-on-failure

python -m unittest tests\test_physics_verify.py tests\test_consonance_contract.py tests\test_verify_score_contract.py -v
python tools\tuner_audit.py
python tools\tuner_audit_v2.py
python tools\physics_verify.py --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --selftest
python tools\physics_verify.py --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --full
python tools\verify_score.py --all --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe
python tools\check_piece_consonance.py scores\originals\rules_v2_demo\rules_v2_demo_001.score.json --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --out reports\rules_v2_demo_consonance_check.md
```

## Remaining scientific/product gaps

- Material `beta_air` and `gamma_radiation` still lack specimen-level traceability; `alpha` is anchored, not broadband calibrated.
- Output amplitude is normalized/dimensionless: no calibrated Newton → Pascal/SPL path, microphone/directivity or spatial phase.
- No soundboard/body coupling, sympathetic resonance, damper/pedal system, anisotropic wood, nonlinear contact solver, temperature/humidity model or measured specimen fitting.
- FM Piano is deliberately non-physical; plugin creative macros are not physical evidence.
- Same-machine SHA256 reproducibility is tested; cross-OS/compiler bit identity is not promised.
- Tuner is target-aware and monophonic; polyphonic/missing-fundamental mixtures may be refused rather than guessed.
- Real DAW automation/state round-trip and deaf-user accessibility still require human/host validation after this branch is built.

## Working rules

1. Work on a branch, never silently on `main`.
2. Do not call N/A an acceptance pass or describe FM/effects as physically verified.
3. Any physics/audio change requires C++ regression tests plus `physics_verify.py --full`.
4. Do not commit, push or delete historical evidence unless the user explicitly asks.
