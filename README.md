# TsukiSynth — Multi-Engine VST3/AU Plugin

[![Physics Verification](https://github.com/TsKR2828/tsuki-synth/actions/workflows/physics.yml/badge.svg)](https://github.com/TsKR2828/tsuki-synth/actions/workflows/physics.yml)

> Physical Modeling / Modal Synthesis multi-engine software synthesizer — VST3 / AU plugin
>
> **This is an independent project. It has no relation to haguruma-engine or any other project.**

## Current Status

| Component | Status |
|-----------|--------|
| Cimbalom Engine (Modal Synthesis, String) | Done |
| Chromatic Engine (Beam / Plate / Custom) | Done |
| FM Piano Engine (2-op FM Synthesis) | Done |
| Effect Chain (Reverb / Delay / Compressor / Distortion) | Done |
| Oscilloscope (lock-free FIFO) | Done |
| 8 Macro Parameters (DAW automation) | Done |
| Preset Manager (27 factory + user save/load) | Done |
| Preset selector (`presetCombo` drop-down: current engine's factory presets + user presets, prev/next stepping; **no category filter** — the visual browser popup `PresetBrowser.h` was removed on 2026-05-22, `1954418`) | Done |
| Spectrum Analyzer (FFT, log-freq, toggle) | Done |
| Tuner (measured dry audio, A0-C8, confidence/refusal states, hold-after-release) | Done |
| Reverb profile / IR loading (scene JSON → params, WAV → convolution) | Done (2026-08-06) |
| **Managed IR library** (F-03: presets store IR by content hash, three-state missing-file handling, single source of truth for UI/audio IR status) | Done (2026-09-09) |
| Host tail-length contract (`getTailLengthSeconds()` reports the physical engine's worst-case modal T60, not the FM release) | Done (2026-09-07) |
| Brightness EQ (creative high shelf: score `effects.eq` + plugin BRIGHTNESS panel) | Done (2026-08-06) |
| Standalone Score console (render score.json / open report, no DAW; bundles CLI) | Done (2026-08-06) |
| Scene→Reverb tool (`tools/scene_reverb.py`, Sabine/Eyring → authored T60) | Done (2026-08-05) |
| Hover magnifier + enlarged tooltips (visual accessibility) | Done (2026-08-06) |
| Harmonic Editor (Custom sub-engine, 8 partials) — embedded in the main editor as 8 ratio + 8 amplitude knobs (`chrRatios[8]`/`chrAmps[8]`, shown when Custom is selected); the separate `HarmonicEditor.h` component was removed on 2026-05-22 (`1954418`) | Done |
| Responsive UI (resizable 420x700 ~ 900x1200) | Done |
| Custom LookAndFeel (dark theme, arc knobs) | Done |
| MIDI Keyboard (on-screen) | Done |
| CLI Score Renderer (strict JSON -> WAV/FLAC + provenance manifest) | **Passed** — fresh Release build emits and verifies manifest v4, including recursive layer dependencies |
| **VST3 build** | **Passed** — fresh Release build from current source |
| **Standalone build** | **Passed** — fresh Release build from current source |
| **Standalone launch** | **Passed** — current Release build smoke-tested |
| **DAW plugin host validation** | **Passed** — real Cubase LE AI Elements 12 export verified by `melody_verify` 5/5 and bit-identical project save/reload (2026-08-22, L3b); `TsukiSynthHostProbe` H1–H8 cover scan, instantiation, MIDI render determinism, automation, DAW state, variable host block size (bit-identical), user-preset round-trip and tail-length contract, plus the D12 legacy IR-state migration scenarios, the plugin state/preset version checks and a per-preset check of all 27 factory presets (215 PASS / 0 failures on the 2026-09-25 WF0925 integration build, re-confirmed by the WF0925b integration run from a working directory outside the repo; 89 before WF0925). Deployment note (checked 2026-09-25): the copy installed on the maintainer's machine is the 2026-09-10 23:46 build, placed in a sub-folder (`Common Files\VST3\TsukiSynth_VST3_2026-09-10\TsukiSynth.vst3`); it predates the WF0914 plugin changes (D12 state migration, D9c IR make-up gain), Cubase's plug-in cache was last written 2026-08-22 and still points at the old top-level path, and older copies remain under `Program Files (x86)` and `%APPDATA%\VST3`. The L3b real-host pass above tested the build of that time, not the current source — redeploy is pending the maintainer's go-ahead |
| State save/load | Done (skipNextProgramChange + reattachListener fix) |
| Version display | Done (v0.3.0 in title bar) |
| EN/中文 localization | Done |
| Standalone REC recording | Done |

**Version**: `v0.3.0` — the active deep-audit branch is `fix/deep-physics-audit-20260716`. B1–B6 are merged to `main` (the last of them, B5/B6, with the 2026-08-30 merge `64afb49`). The 2026-09-07~11 audit-closure batch (five commits, `5c9cdb3`…`49b8542`: managed IR library, tail-length contract, schema contract sync, layered `--dump-modes`, sample-accurate water-gong glide, A14 hammer-contact pitch law, D8 tongue-drum exciter fix, measurement self-calibration), the 2026-09-14 handover update `a38bd6a` and the CI fix `766d21d` are **pushed and merged to `main`** (`b56747d` 2026-09-14, `3f9b90a` 2026-09-15); the Physics Verification workflow is green on both `766d21d` and `3f9b90a` (Windows / Linux / macOS legs). The 2026-09-14~16 WF0914 batch (B7 Phase 0 + partial Phase 1, D9c IR make-up gain, D12 legacy IR-state migration, D13/D15 claim-domain narrowing, D14 `stem_verify` memory fix, decision packets and GATE evidence) was committed on 2026-09-25 as seven commits per the maintainer's ruling (`a09058c`…`18430c4`) — **not pushed yet**. The follow-up 2026-09-25 WF0925 batch (plugin real-time/state/IR-library hardening, D9c make-up-gain guard test, HostProbe working-directory independence and CI wiring, D16/D11-F5/D1 research reports, THIRD_PARTY_NOTICES and release/legal drafts) is **staged, not committed**; its integration run is all green with the 8 reference renders bit-identical (8/8). The same-day WF0925b follow-up (CI multi-line step exit-code checks, small verification-tool fixes, documentation sync, a before/after study of removing the tongue-drum ×2 damping factor, and text fixes to the product candidates) is also **staged, not committed** — 239 staged files in total, no source (`src/`) changes; its integration run is all green (307 tests = 301 passed + 1 skipped + 5 xfailed, 8/8 bit-identical). Exact verification state: `HANDOVER.md` (start here for a new session) and `TODO.md`.

## Overview

TsukiSynth is a multi-engine software synthesizer plugin based on **Physical Modeling (Modal Synthesis)**. The Cimbalom (string), Tongue Drum (beam), and Water Gong (plate) engines calculate vibration mode frequencies and decay from physical parameters (material density, plate thickness, string length, strike position). The automated harness verifies rendered output against the implemented equations and independently anchors pitch/eigenvalue relationships. Amplitude and T60 checks currently establish implementation conformance, not external specimen accuracy; calibrated radiated-pressure and laboratory validation remain open. The FM Piano engine and the effect chain are outside this verification domain — see the same section for the full scope declaration.

The prototypes originated from [piano-play](https://github.com/TsKR2828/piano-play) and other Web Audio experiments. The codebase has been rewritten in C++ / JUCE as VST3 and AU format for use in DAWs (Cubase, Logic Pro, FL Studio, Reaper, etc.).

### Why this project is unusual

TsukiSynth is built by a Deaf developer working with an AI assistant, neither of whom can listen to the audio to judge correctness by ear. Because "does it sound right" is not an available check, the project instead proves correctness through physics theory and a chain of hearing-free verification: physical equations predict what a rendered waveform's pitch, decay, and amplitude *should* be, and automated tools compare the actual rendered audio against those predictions — spectrum plots, pass/fail diffs, and numeric deltas the developer can read visually instead of hearing. Final aesthetic judgment (does it sound *good*) is separately delegated to an external professional listening pass; physical/positional correctness is carried entirely by the automated GATE chain described below. See [Physical Verification](#physical-verification) and [Hearing-Free Melody Verification](#hearing-free-melody-verification).

## Core Direction

TsukiSynth is positioned as a **Physical Modeling synthesizer** with semantic parameters, not a general-purpose wavetable or subtractive synth. The core differentiators:

- **Physical Modeling main body** — Modal Synthesis from real material properties (density, Young's modulus, damping), with machine-checkable model conformance and explicit external-validation gaps (see [Physical Verification](#physical-verification))
- **Semantic parameters** — "material = steel", "hammer = felt" instead of abstract oscillator/filter knobs
- **AI JSON Score Pipeline** — AI can directly generate sound design via JSON score files
- **VTuber / worldview sound design** — targeted at character UI sounds, world-themed sound libraries
- **WAV export** — CLI batch rendering for sound library generation without a DAW

## Physical Verification

TsukiSynth's physical claims are scoped and machine-checked, not aspirational — see `ROADMAP_PHYSICS.md` §0 for the full verification-domain table. Summary:

| Component | Verification domain | Status |
|---|---|---|
| Cimbalom / Piano (StringModel) | ✅ In domain — struck rigid string, incl. inharmonicity; amplitude includes a documented creative layer (`spectralTilt`, see `CimbalomEngine.h` comments) — frequency/decay are unaffected; kept and scope-fenced per 月月's 2026-07-23 ruling | Physically verifiable |
| Tongue Drum (BeamModel) | ✅ In domain — fixed-free cantilever by default; explicit free-free suspended bar | Physically verifiable |
| Water Gong (PlateModel) | ✅ In domain — Kirchhoff circular plate (clamped + free-edge). Claim domain narrowed by 月月's 2026-09-15 ruling (D13 option B): it models a plain free-edge plate, **not** a bossed gong, so no mode near 2.0× f0 is a domain limit, not a calculation error — see `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §1 | Physically verifiable (within that domain) |
| Custom Harmonics | ⚠️ Half-domain — additive synthesis, ratios checkable but not physically derived | Not a physical-accuracy claim |
| FM Piano | ❌ Out of domain — explicitly non-physical synthesis | Not covered |
| Effect Chain (Reverb/Delay/Comp/Dist) | ❌ Out of domain — verification always runs with FX off | Not covered |
| Chromatic scaling (size → timbre, MIDI → pitch) | ⚠️ Hybrid — physics shapes the spectral content, equal temperament sets f0 | Not "fully physical"; do not describe as such |

For the in-domain engines, `tools/physics_verify.py` compares rendered audio with theory using a ±5-cent frequency gate, ±3.0 dB partial-amplitude gate, +6.0 ±1.0 dB velocity-doubling gate and a measured/model T60 ratio gate; T60 fits must also capture at least 8.0 dB of clean decay. `tools/verify_score.py` measures a multi-string course by its amplitude-weighted centroid with a ±5-cent gate, and also checks rest RMS ≤ −50 dBFS, clipping, manifests and same-environment SHA256 determinism. Manifest v4 binds the WAV, renderer executable, root score and every recursively referenced layer by SHA256, plus a canonical dependency-tree digest and configure-time commit/dirty/toolchain metadata. The 2026-08-02 fresh-build `--full` run has no checked failures; three ultra-short rubber cases are reported as `UNVERIFIED/N/A`, not as passes. A new four-shard full-corpus run passed 75/75 with the one pre-existing visible FX-art exemption and no failures. Both results were re-confirmed on 2026-09-25 against the WF0914 tree (`--full` NO CHECKED FAILURES, corpus 75/75, 8/8 reference renders bit-identical to the post-A14 baseline). The VST3 last passed pluginval L10 across six sample rates and adversarial block sizes, plus the pinned Steinberg SDK 3.8 validator (47/47), on **2026-08-06**; neither has been re-run since the 2026-09 plugin changes (tail-length cache, managed IR state, D12 migration, D9c make-up gain). See `DEVLOG.md` and `TODO.md`.

These numbers are model-conformance evidence a deaf user (or an AI) can check visually/numerically — via spectrum plots and pass/fail diffs — without relying on how anything sounds. They are not yet a substitute for calibrated external-instrument measurements.

### Physics chain status (2026-09-25)

The string/cimbalom/piano damping law has been extended in stages, each gated on the commands above and, where the render output changes, on a before/after Rule 10 report:

| Stage | What it adds | Status | Report |
|---|---|---|---|
| B1 | Bridge/soundboard admittance — a frequency-independent loss channel from the driving-point admittance of an infinite soundboard plate, wired into Cimbalom/Piano decay only | Done (2026-08-21) | `reports/b1_b2_bridge_damping_before_after.md` |
| B2 | Broadband-damping cleanup — corpus-wide re-verification and loudness-anchor remeasurement after B1 | Done (2026-08-21) | `reports/b1_b2_bridge_damping_before_after.md` |
| B3 | String damping law rewritten to Cuesta & Valette's zero-free-parameter three-mechanism model (air/viscoelastic/thermoelastic loss), replacing two previously unsourced fit constants | Done (2026-08-26, merged to `main`) | `reports/string_damping_firstprinciples_before_after.md` |
| B4 | Hammer/felt contact solved per-note from a nonlinear force law instead of a fixed contact-time constant | Done (2026-08-27) | `reports/b4_hammer_contact_before_after.md` |
| B5 | Orthotropic wood-material schema (9 independent elastic constants per species, from the USDA Wood Handbook) added to `materials.json` | Schema committed (`88bdfac`, 2026-08-28; merged to `main` 2026-08-30), zero consumption — `PlateModel`/`BeamModel` still read a single scalar E/ν; no render output changed | `reports/b5_schema_noop_proof.md` |
| B6 | Radiation-efficiency skeleton (`RadiationModel.h`, σ(f)/η_rad(f)) exposing diagnostic-only `radiated_power_relative`/`absolute_pressure_per_force`/`acoustic_transfer[]` fields in `--dump-modes` | Done (2026-08-28) — Phase 0-1 skeleton, Phase 2 scope decision (方案 B, physics-only signal-tap calibration), Phase 3/4 landed the calibrated tap; diagnostic path only, `render()`/`ModalResonator` untouched (verified bit-identical 8/8) | — |
| A14 B-2 | Felt-hammer contact-time pitch law re-anchored to the measured Askenfelt & Jansson curve (`keytrackScale`, k=0.32) instead of the K/α/mass-derived shape (k≈0.212) that pushed treble fundamentals into a force-spectrum null (G5 −34 dB). Velocity law unchanged, no new constants | Done (2026-09-10, maintainer-approved Rule 10) — only 5 piano scores change; 7/8 reference renders bit-identical | `reports/a14_tauc_keytrack_before_after.md` |
| D8 | Tongue-drum "finger" exciter (4–11 ms soft hammer) replaced by `wood_mallet` in the two Moonlight tongue-drum scores; MIDI 37→87 level slope 41 → 5.5 dB, energy below 200 Hz 97% → 18%. Score change only, engine untouched | Done (2026-09-09, maintainer decision) | `reports/d8_tongue_drum_exciter_before_after.md` |
| B7 | First-principles force chain (MIDI velocity → hammer speed → Hertz peak force → bridge power → Pa at 1.05 m), Cimbalom/Piano with felt exciter only, as an independent cross-check of the B6 calibration | **Partial** — Phase 0 (sources) done; Phase 1 partial: five pure functions + their tests landed in `HammerImpulse.h`/`RadiationModel.h` (the chain stops at bridge power; radiating area `S` stays UNVERIFIED), but the `--dump-modes` field was withdrawn after the velocity-proxy check was overturned; Phase 2/3 BLOCKED (source gap). 月月's 2026-09-15 ruling (path C + criterion (a) option 乙) makes this the legitimate end point of the round. Not wired into any render path (8/8 bit-identical) | `reports/decision_packets/B7_phase2_and_open_items.zh-TW.md` §6 |
| D9c | *Effect chain, outside the verification domain — listed here because it changes what a DAW user hears.* IR-convolution reverb wet is multiplied by a fixed `kIrWetMakeupGain = 26.9` (+28.58 dB), a DECIDED CONVENTION (not a physical constant) averaged from 4 IRs, closing the structural IR-vs-algorithmic wet gap (residual −0.13…+0.11 dB). **In a DAW, IR-mode wet level changes** for existing projects; dry signal, algorithmic mode and CLI/score renders are untouched (8/8 bit-identical) | Done (2026-09-16 maintainer decision, D9 option A) | `reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md`, `reports/gate_outputs/wf0914_D9c_ir_makeup_gain.txt` |

Full detail and the current decision backlog are in `HANDOVER.md` and `TODO.md`.

## Hearing-Free Melody Verification

Because neither the developer nor the AI can rely on listening, a second verification chain checks *where in time and at what pitch* notes actually land — independent of the acoustic-model checks above:

- **L1 `tools/melody_verify.py`** — compares a rendered WAV against its source score event-by-event (onset ±10ms, pitch within 5 cents), plus 8 fail-closed refusal rules (masking, overtone contamination, course self-beating, bed energy, low-frequency resolution limits, etc.) so it reports `UNVERIFIED` rather than a false pass when a case is outside its proven domain. Five adversarial sentinels (time-shift/transpose/delete-note/phantom-note must FAIL, unmodified must PASS) guard against a rubber-stamp checker. `--html` renders a piano-roll overlay so a Deaf reviewer can inspect the result visually.
- **L2 `TsukiSynthHostProbe`** — a CMake test target that loads the built `.vst3` from disk and drives it like a real host (H1–H8 plus the D12 legacy IR-state migration scenarios, state/preset version checks and all 27 factory presets: 215 checks PASS, 0 failures on the 2026-09-25 WF0925 integration run; H8 looks for `data/materials.json` in the working directory, then under `$TSUKI_REPO_ROOT`, then in the executable's parent folders, so it no longer has to be started from the repo root), the first automated proof that the plugin's live audio path (not just the offline CLI renderer) places notes correctly.
- **L3 Cubase real-host verification** — `tools/cubase_scan_verify.py` parses Cubase's own scan-cache XML (5/5 PASS), and a supervised end-to-end pass (project build, MIDI import, tempo-aligned export, reverb zeroed) fed back through `melody_verify.py` scored 5/5 with onset ≤2.5ms / pitch ≤0.4 cents, and reload → re-export reproduced bit-identical audio (SHA256 match).

The regression corpus this all runs against is **75 score files** (`scores/examples/` + `scores/classical/` + `scores/originals/ai_radiance/` + `scores/library/`), currently passing 75/75 with zero newly-registered exemptions per full run.

### Verification commands

```powershell
# C++ invariants, causality, semantic determinism and tuner coverage
ctest --test-dir build -C Release --output-on-failure

# Python metrology/counterexample contracts and the complete physics matrix
# (pytest, as in CI: 307 tests = 301 passed + 1 skipped + 5 xfailed on the 2026-09-25 WF0925b integration run;
#  `unittest discover` misses the pytest-style files; the release workflow now uses pytest too)
python -m pytest tests -q
python tools\physics_verify.py --selftest
python tools\physics_verify.py --full

# Full score corpus; release CI runs indexes 0..3 in parallel
python tools\verify_score.py --all --shard-index 0 --shard-count 4 `
  --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe

# MSVC AddressSanitizer regression build
cmake -B build-asan -DTSUKI_BUILD_TESTS=ON -DTSUKI_ENABLE_SANITIZERS=ON
cmake --build build-asan --config RelWithDebInfo --target TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest TsukiSynthSpectrumViewTest
tools\run_asan_ctest.ps1
```

The exact P1–P7 methods and results are recorded in [the 2026-08-02 verification report](docs/P1_P7_VERIFICATION_2026-08-02.zh-TW.md). For a real instrument specimen, follow [the specimen protocol](docs/SPECIMEN_VALIDATION_PROTOCOL.zh-TW.md). `tools/specimen_pipeline.py` now turns synchronized repeated CSV records into a self-contained v2 bundle: calibrated H1/coherence, complex phase, automatic modal T60, Pa/N, SPL at a declared RMS force, complex directivity points, uncertainty records and SHA256 provenance. `tools/specimen_verify.py` implements all corresponding comparators. The synth's Mode Dump v2 (`--dump-modes`) emits modal frequency, relative modal amplitude and T60 for the in-domain engines, and — for the string/cimbalom/piano branch only — the diagnostic B6 fields `radiated_power_relative`, `absolute_pressure_per_force` and `acoustic_transfer[]` (see the B6 row above). It explicitly lists `complex_phase`, `absolute_spl` and `radiation_directivity` as unsupported observables. So phase and directivity claims remain honestly `UNVERIFIED` (the model has no phase or spatial-radiation operator), and a pressure-per-force comparison stays `UNVERIFIED` until a calibrated specimen measurement exists to compare it with; measured data alone is never promoted to PASS.

```powershell
# Copy and fill specimens/templates/measurement_v2.template.json and
# specimens/templates/acquisition.template.json, then:
python tools\specimen_pipeline.py path\to\acquisition.json --out path\to\new-bundle
python tools\specimen_verify.py path\to\new-bundle\measurement.json `
  --json-out path\to\new-bundle\verification-report.json
```

## Plugin Formats

| Format | Target DAWs | Status |
|--------|-------------|--------|
| VST3 | Cubase, FL Studio, Ableton, Reaper, Studio One | **Built** (x64 binary 7.58 MiB, 7,947,776 B — 2026-09-25 WF0925 integration build) |
| Standalone | No DAW required | **Built** (x64 binary 7.46 MiB, 7,819,776 B — 2026-09-25 WF0925 integration build) |

The Standalone doubles as a self-contained tool: the title-bar **Score** button opens a
console that renders a `score.json` to WAV (spawning the bundled `TsukiSynthCLI.exe` —
the single verified render path, output to `Desktop\TsukiSynth_Renders`), opens the
output folder, and opens/generates the score's HTML verification report (generation
needs Python and a repo checkout). Distribute `TsukiSynth.exe` and `TsukiSynthCLI.exe`
in the same folder.
| AU (Audio Unit) | Logic Pro, GarageBand, MainStage | CMake option ready |
| AAX | Pro Tools | CMake option ready (requires Avid SDK) |

## Sound Engines

### Engine 1: Cimbalom (Hungarian Dulcimer) — Physical Modeling (physically verifiable)
- **Modal Synthesis string model** + multi-string beating + damper (CC#64)
- From physical parameters (material density, string diameter, tension, length) calculates N vibration modes with inharmonicity correction
- Strike position affects modal amplitude distribution
- Material stiffness controls overtone spectral tilt (stiffer → brighter, more harmonics)
- Hammer hardness shapes modal excitation spectrum (cotton = warm fundamental, metal = full spectrum)
- Parameters: string material (9 types), diameter, hammer hardness (cotton/felt/wood/metal), strike position, strings per course (1-5), detuning

### Engine 2: Chromatic Synth — Physical Modeling (hybrid pitch mapping)
- Three-in-one engine: Tongue Drum / Water Gong / Custom Harmonics
- Tongue Drum: **Euler-Bernoulli beam model** (non-harmonic modes from eigenvalue formula) — physically verifiable
- Water Gong: **Kirchhoff circular plate model** (plate characteristic roots and Bessel/modified-Bessel radial modes; free or clamped edge) — physically verifiable
- Custom: user-editable ratio/amplitude via the **Harmonic Editor** (8 partials; ratio + amplitude knobs embedded in the main editor, shown when Custom is selected, APVTS-driven) — additive synthesis, ratios checkable but not physically derived
- `frequency_mode: "midi"` is a **hybrid**: physics shapes the modal ratios/decay while equal temperament sets f0. `frequency_mode: "geometry"` retains the absolute material/geometry prediction for metrology.
- Parameters: sub-engine, material, exciter hardness, strike position, thickness, size, pitch glide, 8 harmonic ratios, 8 harmonic amplitudes

### Engine 3: FM Piano — Frequency Modulation (non-physical synthesis, outside verification domain)
- 2-operator FM synthesis with self-feedback
- 8 sound type presets: Piano, E.Piano, Vibraphone, Bell, Organ, Pad, Bass, Brass
- **E.Piano 3-stack mode**: parallel body (1:1) + tine/bell (14:1) + shimmer (3:1, +4 cents) for DX7-inspired timbre
- Velocity-sensitive modulation index + note-dependent brightness decay
- Two-stage modulation envelope: fast attack transient + slow body decay
- Parameters: sound type, FM ratio, mod index, tone decay, feedback, attack, release

## Macro Parameters

8 global macro knobs that cross-map to all three engines via DAW automation:

| Macro | Cimbalom | Chromatic | FM Piano |
|-------|----------|-----------|----------|
| Material | sustain scaling | sustain scaling | slight ratio detune |
| Tension | mode frequency | mode frequency | ratio scale |
| Damping | decay speed | decay speed | release time |
| Strike | strike position blend | strike position blend | attack time |
| Brightness | exciter cutoff | exciter cutoff | index scale |
| Body | detuning spread | resonator size | feedback scale |
| Noise | exciter amplitude | exciter amplitude | noise injection |
| Output | post-FX final gain (SmoothedValue) | same | same |

Output is applied **after** the effect chain with per-sample `juce::SmoothedValue` to prevent clicks.

## Effect Chain (outside verification domain — physical verification always runs with FX off)

```
[Engine Output] -> Distortion -> Compressor -> Delay -> Reverb -> Brightness EQ -> [Macro Output] -> Output
```

- **Distortion**: Overdrive / Bitcrush / Wavefold with instability control
- **Compressor**: Peak-based, linked stereo detection, auto makeup gain
- **Delay**: Stereo with LP-filtered feedback, R channel offset for width
- **Reverb**: two modes — algorithmic Schroeder (8 comb + 4 allpass, room-size knob or authored T60 seconds) or IR convolution (load a .wav impulse response via the panel's Load button; also accepts a `scene_reverb.py` JSON profile, which sets T60 + wet on the algorithmic engine). Since D9c (2026-09-16 decision) the IR wet signal is multiplied by a fixed `kIrWetMakeupGain = 26.9` (+28.58 dB, a decided convention, not a physical constant) so IR and algorithmic modes sit at the same wet level; projects saved before D9c will hear a louder IR-mode wet
- **Brightness EQ**: RBJ high shelf (`fx_eq_freq`/`fx_eq_gain`, score `global.effects.eq`); documented creative layer added 2026-08-06 to compensate the perceived darkening after damping physicalization; 0 dB = hard bypass (bit-identical renders)

## Analyzer

- **Oscilloscope**: Lock-free AudioFIFO pipeline, 30Hz refresh, zero-crossing trigger, engine-colored waveform
- **Spectrum**: FFT-based SpectrumView (2048-sample Hann window, log-frequency 30Hz–20kHz, smoothed dB), toggle button in AnalyzerPanel
- **Tuner**: dry pre-FX audio measurement; TARGET and MEASURED are separate; A0–C8 at 44.1/48/96/192 kHz; cent delta, confidence, and explicit `Uncertain`/out-of-range states. It is target-aware monophonic and does not claim polyphonic pitch separation. After note release the last successful detection stays on screen for 10 s, dimmed and labelled LAST (explicitly a held value, not a live measurement).

## Preset System

- 27 factory presets (8 Cimbalom + 8 Chromatic + 9 FM + 2 Physical Piano) compiled as static arrays
- User preset save/load (`.tsukipreset` XML files in AppData), stable UUID identity and atomic replacement
- Preset **drop-down** (`presetCombo`) listing the current engine's factory presets, then user presets after a separator, with prev/next buttons. There is no category filter: the earlier visual browser popup with All / Cimbalom / Chromatic / FM / User filters (`PresetBrowser.h`) was removed on 2026-05-22 (`1954418`)
- DAW program change compatible (VST3 `getNumPrograms` / `setCurrentProgram`)
- Dirty indicator + Init button
- Full state serialization (`getStateInformation` / `setStateInformation`), restoring preset ID and dirty state without synchronous user-preset disk reads in program loading

## Tech Stack

| Item | Technology |
|------|-----------|
| Language | C++17 |
| Framework | JUCE 8.0.12 (git submodule) |
| Build | CMake 3.22+ |
| Synthesis | Modal Synthesis (Physical Modeling) + FM Synthesis |
| DSP Reference | DaisySP (MIT), STK (MIT-like) |
| GUI | Custom LookAndFeel (arc knobs, gradient faces, engine-colored accents) |
| Brand Assets | IBM Plex Sans SemiBold embedded via BinaryData; SVG moon path from design mockup |
| Material Data | JSON embedded via BinaryData (density, Young's modulus, Poisson ratio, damping) |
| Platform | Plugin (VST3/Standalone): built and validated on Windows (MSVC) only so far. CLI renderer: built in CI on three platforms — Windows MSVC / Linux GCC 13.3 / macOS AppleClang — for the cross-platform tolerance check (the Linux leg is labelled `ubuntu-24.04-clang` in `physics.yml` but actually compiles with GCC) |

## Directory Structure

```
tsuki-synth/
├── README.md
├── HANDOVER.md                   <- start here for a new session (current state)
├── TODO.md                       <- task list and decision backlog
├── ROADMAP_PHYSICS.md            <- physics acceptance rules (sole acceptance basis)
├── ROADMAP.md
├── DEVLOG.md
├── THIRD_PARTY_NOTICES.txt       <- third-party components and licence texts (JUCE, VST3 SDK, codecs, fonts)
├── CONTEXT.md                    <- historical snapshot (2026-08-06); see HANDOVER.md
├── TODO_HANDOFF.md               <- historical snapshot (2026-07-17); see HANDOVER.md
├── CMakeLists.txt
├── libs/
│   └── JUCE/                     <- git submodule (JUCE 8.0.12)
├── src/
│   ├── PluginProcessor.h/.cpp    <- main audio processor (APVTS, 3 synths, effect chain, state incl. D12 legacy IR migration)
│   ├── PluginEditor.h/.cpp       <- GUI editor (540x850, tab switching, preset bar with presetCombo drop-down,
│   │                                embedded 8-partial ratio/amplitude knobs for the Custom sub-engine)
│   ├── ParameterLayout.h/.cpp    <- GUI-free APVTS parameter layout (shared by the plugin and HostProbe)
│   ├── PresetManager.h           <- factory + user preset load/save/dirty tracking
│   ├── Presets.h                 <- 27 factory preset definitions (static arrays)
│   ├── IRLibrary.h               <- managed, content-hash (SHA-256) IR library for user impulse responses (F-03)
│   ├── ScoreConsole.h            <- Standalone-only Score console (launches the bundled TsukiSynthCLI)
│   ├── HoverMagnifier.h          <- accessibility hover magnifier for small text controls
│   ├── TsukiLookAndFeel.h        <- custom knobs, combos, tabs, colour palette
│   ├── UiLocale.h                <- EN/中文 localization layer
│   ├── BuildProvenance.h.in      <- configure-time commit/dirty/toolchain metadata (render manifests)
│   ├── engines/
│   │   ├── CimbalomEngine.h      <- string physical modeling (40 modes, multi-string beating)
│   │   ├── ChromaticEngine.h     <- beam/plate/custom three-in-one
│   │   └── FMPianoEngine.h       <- 2-operator FM with 8 sound types
│   ├── dsp/
│   │   ├── ModalResonator.h      <- core: N-mode decaying sine renderer
│   │   ├── AudioFIFO.h           <- lock-free FIFO for analyzer
│   │   ├── BiquadFilter.h        <- IIR biquad (LP/HP/BP/Notch)
│   │   ├── BodyResonance.h       <- procedural body resonance (two band-pass filters, per voice)
│   │   ├── Compressor.h          <- peak compressor (dsp-level)
│   │   ├── DelayLine.h           <- circular buffer + linear interpolation
│   │   ├── DiagnosticOverrides.h <- diagnostic-only CLI overrides for differential renders (not in the render contract)
│   │   ├── Distortion.h          <- overdrive / bitcrush / wavefold
│   │   ├── EffectsChain.h        <- offline (CLI/score) effects chain, same DSP classes and order as the plugin
│   │   ├── Envelope.h            <- ADSR + ExpDecay
│   │   ├── LFO.h                 <- low-frequency oscillator
│   │   ├── NoiseGen.h            <- white + pink noise
│   │   ├── MidiNoteTracker.h      <- tuner MIDI/retrigger/sustain state
│   │   ├── Oscillator.h          <- phase accumulator (sin/saw/square/tri)
│   │   └── Reverb.h              <- (legacy, replaced by effects/SimpleReverb)
│   ├── effects/
│   │   ├── EffectChain.h         <- plugin chain: Distortion -> Comp -> Delay -> Reverb (algorithmic or IR convolution,
│   │   │                            IR wet × kIrWetMakeupGain, D9c) -> Brightness EQ
│   │   ├── Compressor.h          <- peak compressor with linked stereo
│   │   ├── StereoDelay.h         <- stereo delay with LP feedback
│   │   └── SimpleReverb.h        <- Schroeder reverb (8 comb + 4 allpass)
│   ├── physics/
│   │   ├── StringModel.h         <- string mode frequency (inharmonicity, physical decay)
│   │   ├── BeamModel.h           <- Euler-Bernoulli beam (tongue drum)
│   │   ├── PlateModel.h          <- Kirchhoff circular plate (Bessel zeros)
│   │   ├── BesselPortable.h      <- portable Bessel J/I series (fallback where libc++ lacks std::cyl_bessel_*)
│   │   ├── HammerImpulse.h       <- hammer/exciter force-pulse spectrum, felt contact solver (B4), A14 pitch law, B7 pure functions
│   │   ├── RadiationModel.h      <- radiation-efficiency skeleton + calibrated pressure-per-force tap (B6), B7 pure functions
│   │   └── MaterialDB.h          <- transactional JSON material database loader (14 materials)
│   ├── analyzer/
│   │   ├── AnalyzerPanel.h       <- Scope / Spectrum / Tuner tabs
│   │   ├── PitchDetector.h       <- bounded target-aware dry-audio pitch estimator
│   │   ├── TunerView.h           <- target/measured/confidence UI
│   │   ├── OscilloscopeView.h    <- real-time waveform display (30Hz, zero-crossing trigger)
│   │   └── SpectrumView.h        <- FFT spectrum (2048-sample, log-freq, smoothed dB)
│   ├── score/
│   │   ├── ScoreParser.h         <- JSON score file parser
│   │   ├── ScoreRenderer.h       <- offline rendering using DSP engines (+ Mode Dump v2 / --dump-modes)
│   │   ├── EventIdentity.h       <- stable semantic event identity (deterministic noise seeding)
│   │   ├── SampleRateContract.h  <- single source of truth for supported sample rates
│   │   └── WavWriter.h           <- 24-bit WAV output with normalization
│   └── cli/
│       └── RenderApp.cpp         <- CLI entry point (single + --batch mode)
├── data/
│   ├── materials.json            <- 14 material physical parameters (9 exposed in UI)
│   └── fonts/
│       └── IBMPlexSans-SemiBold.ttf  <- brand wordmark font (embedded via BinaryData)
├── scores/
│   ├── schema/
│   │   └── score.schema.json     <- JSON Schema validation
│   ├── examples/                 <- 13 focused examples / regression scores
│   ├── classical/                <- 14 scores (Für Elise, Vivaldi Four Seasons)
│   ├── originals/                <- ai_radiance (5 scores) + rules_v2_demo (1)
│   ├── tests/                    <- test fixtures (e.g. melody_sentinel)
│   └── library/                  <- 43 production short scores (6 worlds)
├── sound_library/
│   ├── sound_names.json          <- sound library index
│   └── tags.json                 <- taxonomy (category/mood/energy/world)
├── tests/                        <- C++ regression tests (audit/tuner/physics_models/spectrum_view, host_probe) + pytest suite
├── tools/                        <- verification and pipeline scripts (physics_verify, verify_score, melody_verify, stem_verify, ...); `tools/installer/` = Inno Setup script draft (never compiled)
├── docs/                         <- design docs, source-traceability docs, workcards; `docs/legal/` = JUCE licence review and buyer EULA draft
├── reports/                      <- decision packets, Rule 10 before/after reports, GATE outputs
└── uiux/                         <- HTML/CSS UI reference mockup
```

The regression corpus walked by `verify_score.py --all` is examples + classical + originals/ai_radiance + library = 75 score files (`originals/rules_v2_demo` and `tests/` are not part of it).

## AI JSON Score Pipeline

TsukiSynth supports **AI-driven sound generation** via JSON score files.

Composition and accessibility reference:

- `docs/AI_PERFORMANCE_PLAYBOOK.zh-TW.md` — **AI 演奏手冊（從這裡開始）**：SOP、引擎選擇、參數快查、驗收流程、地雷清單
- `docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` — AI／聾人物理作曲、音符斷點、休止與樂句呼吸規範
- `docs/DEEP_FIX_VERIFICATION_2026-07-17.zh-TW.md` — 本分支修正、測試方法、結果與距離最終目標的落差
- `scores/classical/vivaldi_four_seasons/` — Vivaldi《四季》4 首協奏曲、12 樂章物理字串轉譯
- `scores/originals/ai_radiance/` — 原創四樂章多引擎組曲《光之驗算》
- `tools/midi_to_tsukisynth.py` — MIDI tempo map／note-off／休止轉換工具
- `tools/compose_ai_radiance.py` — 可重現的演算法作曲與物理配器生成器

Physical modeling parameters are semantic (material, size, strike position). AI can directly generate JSON scores:

```bash
# AI generates score.json -> TsukiSynth renders to WAV
tsukisynth-cli scores/examples/akashic_bell.score.json

# Batch render (pass a directory, not a wildcard)
tsukisynth-cli --batch scores/examples/ --output exports/wav/
```

Use cases: VTuber sound effects, character UI sounds, short BGM motifs, worldview sound libraries.

## Build Instructions

### Prerequisites
- **Windows**: Visual Studio 2022 Build Tools (VCTools workload), CMake 3.22+
- **macOS**: Xcode 14+, CMake 3.22+
- JUCE 8.x (as git submodule, auto-fetched)

### Steps
```bash
git submodule update --init --recursive
pip install -r tools/requirements-physics.txt   # Python deps for the physics verification harness
cmake -B build -DCMAKE_BUILD_TYPE=Release -DTSUKI_BUILD_TESTS=ON
cmake --build build --config Release --target TsukiSynthCLI TsukiSynth_VST3 TsukiSynth_Standalone TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest TsukiSynthSpectrumViewTest TsukiSynthHostProbe
ctest --test-dir build -C Release --output-on-failure
```

Always rebuild the five test targets (`TsukiSynthAuditTest`, `TsukiSynthTunerTest`, `TsukiSynthPhysicsModelsTest`, `TsukiSynthSpectrumViewTest`, `TsukiSynthHostProbe`) immediately before `ctest` — a stale binary from an earlier build will silently report against old code, and a registered test whose exe was never built shows up as "Not Run" (see `HANDOVER.md` §2, "X4 規約"; the 2026-09-07~14 CI red was exactly this: `spectrum_view_repro` is registered with ctest but `TsukiSynthSpectrumViewTest` was missing from the build list, fixed in `766d21d`). `ctest` runs the four registered tests (audit / tuner / physics_models / spectrum_view); `TsukiSynthHostProbe` is deliberately not registered with ctest and is run by hand after the VST3 is built (see the quick reference below).

### Quick reference (see `HANDOVER.md` §9 for the full list)

| Task | Command |
|---|---|
| Full physics GATE | `python tools/physics_verify.py --full` |
| Score corpus (4 shards) | `python tools/verify_score.py --all --shard-index N --shard-count 4 --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe` |
| Hearing-free melody check | `python tools/melody_verify.py <score> [--wav W] [--html H]` (`--selftest` runs the adversarial sentinels) |
| Live-plugin position check (L2) | `build/Release/TsukiSynthHostProbe.exe build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3 <outdir>` (any working directory works while the exe stays in the repo's `build` folder; for a copy outside the repo set `TSUKI_REPO_ROOT`; expect 215 PASS, 0 failures) |
| Cubase scan-cache check (L3a) | `python tools/cubase_scan_verify.py` |
| Cross-platform check | `python tools/crossplatform_verify.py --selftest` (CI runs this on push, blocking) |
| Python unit/contract tests | `python -m pytest tests -q` (baseline 307: 301 passed + 1 skipped + 5 xfailed) |
| MIDI ↔ score transcription check | `python tools/score_vs_midi_verify.py <midi> <score> [--json J]` (`--selftest` runs the mutation sentinels; the Für Elise pair also runs in CI via pytest) |
| Per-event dry-stem check | `python tools/stem_verify.py <score> [--limit N] [--jobs N] [--json J]` |
| Partial-level check (informational, not a GATE) | `python tools/partial_verify.py <stem report.json> [--json J] [--html H]` |
| Measurement self-calibration | `python tools/measurement_selfcal.py [--holdout]` |

### Output
- VST3: `build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3`
- Standalone: `build/TsukiSynth_artefacts/Release/Standalone/TsukiSynth.exe`
- CLI: `build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`

The binaries already present in a checkout may predate the current source. Rebuild before treating their manifests or test results as evidence for this revision.

### Verified Build Environment
- VS 2022 Build Tools 17.14.31, MSVC 19.44, Windows SDK 10.0.26100.0
- CMake 4.3.2, JUCE 8.0.12

## Version Roadmap

| Version | Milestone | Key Items |
|---------|-----------|-----------|
| v0.1 | Playable Build | 3 engines, effects, presets, CLI — **Done** |
| v0.2 | Polish | DAW validation, standalone listening test, factory preset tuning |
| v0.3 | Physics hardening | bridge admittance (B1-B2, done) + first-principles string damping (B3, done) + hammer contact solver (B4, done) + wood orthotropy schema (B5, committed 2026-08-28, zero consumption) + radiation-efficiency skeleton (B6, done — physics-only signal-tap calibration landed 2026-08-28) + first-principles force chain (B7, partial — legitimate end point per the 2026-09-15 ruling) |
| v0.4 | AI Sound Library | CLI batch export pipeline, sound library metadata, AI workflow docs; product line = re-rendered public-domain/CC-BY classical arrangements as full multi-engine pieces, not sound-effect packs (see `docs/PRODUCT_MARKET_NOTES.zh-TW.md`) |
| v0.5 | Advanced Sound Design | creative features only with explicit out-of-physical-domain labels |
| v1.0 | Product Release | Installer, user manual, demo videos, commercial licensing |

## License

Proprietary — all rights reserved (commercial rights retained). See [LICENSE](LICENSE).
JUCE 8 is used under the Starter tier (free, revenue < USD 20k, closed-source
distribution permitted); the 2026-09-25 review (`docs/legal/JUCE8_LICENSE_REVIEW.zh-TW.md`)
found no splash-screen or attribution requirement. The VST3 SDK inside JUCE 8 is MIT.
Third-party components and their licence texts: [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt).

## Links

- Web prototype: https://github.com/TsKR2828/piano-play
- GitHub: https://github.com/TsKR2828/tsuki-synth
- JUCE: https://juce.com/

---

## Audit record — 2026-08-28 (independent claim spot-check)

An independent audit pass re-derived five factual claims in this file from the
repository itself (source constants, the LICENSE file, the JUCE submodule, the
preset array, the binaries on disk, the gate-output evidence), rather than from
any prior report. Result: **3 verified, 2 stale.** Nothing overstated; both
defects understate or mis-attribute, they do not inflate.

**Verified against the repo**

- **GATE constants** (§ Physical Verification): ±5 cent = `physics_verify.py`
  `F0_TOL_CENTS = 5.0`; ±3.0 dB partial amplitude = `AMPS_DB_TOL = 3.0`;
  +6.0 ±1.0 dB velocity doubling = `VELOCITY_DB_TARGET = 6.0` /
  `VELOCITY_DB_TOL = 1.0`; T60 ratio gate = `T60_RATIO_TOLERANCE = (0.80, 1.25)`;
  ≥ 8.0 dB clean decay = `T60_MIN_SPAN_DB = 8.0`; rest RMS ≤ −50 dBFS =
  `verify_score.py` `REST_RMS_LIMIT_DBFS = -50.0`. All five match verbatim.
- **License**: `LICENSE` is "Proprietary — All Rights Reserved" as stated. The
  claim "the VST3 SDK inside JUCE 8 is MIT" is confirmed by the pinned
  submodule's own `libs/JUCE/LICENSE.md` (VST3 listed as MIT). JUCE's free tier
  is indeed named **Starter**. (Not verified: the exact revenue figure's tier
  attribution on juce.com, whose live page now describes the JUCE 9 EULA while
  this project pins JUCE 8.0.12 — the 8.0.12 pin itself is confirmed in
  `libs/JUCE/CMakeLists.txt`.)
- **Scope honesty**: FM Piano is consistently declared out of the verification
  domain (status table, Overview, Engine 3 heading). B5's "zero consumption" is
  true in source: `MaterialDB.h` parses `orthotropic` into a struct its own
  comment marks 死資料, and `PlateModel.h` / `BeamModel.h` read only the scalar
  `material.youngsModulus`. 27 factory presets counted structurally in
  `src/Presets.h` (not taken from its comment): 27.

**Stale / to correct**

1. **Corpus attribution and pass count** (§ Hearing-Free Melody Verification):
   "75 score files (`scores/examples/` + `scores/library/`)" — those two
   directories hold 13 + 43 = **56**. `verify_score.py::find_all_scores()` also
   walks `scores/classical/` (14) and `scores/originals/ai_radiance/` (5),
   which is what makes 75. The "**73/73**" figure is stale: the newest
   in-repo shard evidence (`reports/gate_outputs/b6_corpus_phase34_shard0-3.txt`
   and `b6_corpus_phase4_shard0-3.txt`) reads 19/19 + 19/19 + 19/19 + 18/18 =
   **75/75, 0 failed**, one registered exemption still visible. The same stale
   73/73 also appears in `CONTEXT.md` and § Physical Verification above.
2. **B6 status**: the Physics-chain table says "Phase 0-1 done … Phase 2
   awaiting a scope decision", but `TODO.md` records B6 as Done (2026-08-28)
   with Phase 2 decided (方案 B) and Phase 3/4 landed, and the working tree's
   `src/score/ScoreRenderer.h` already emits `absolute_pressure_per_force` and
   `acoustic_transfer[]`. The README understates work that ships in the same
   unstaged batch.
3. **Binary sizes** (§ Plugin Formats): stated 7.42 MiB VST3 / 7.30 MiB
   Standalone; the binaries actually in `build/` measure **7.53 MiB**
   (7,891,968 B) and **7.40 MiB** (7,764,480 B).

Not corrected here — these are the maintainer's call, and this audit changes no
code, no tolerance and no gate.

---

## Audit record II — 2026-08-28 (second, independent claim spot-check)

A second audit pass re-derived five factual claims from the repository itself,
without trusting either the file's own wording or the first audit record above.
Result: **3 confirmed verbatim, 2 stale — both stale items understate or
mis-attribute; nothing in this file is inflated.**

**Confirmed against the repo**

- **GATE constant list** (§ Physical Verification) — all six re-read from source
  this round: `physics_verify.py` `F0_TOL_CENTS = 5.0` (L429),
  `AMPS_DB_TOL = 3.0` (L1467), `VELOCITY_DB_TARGET = 6.0` /
  `VELOCITY_DB_TOL = 1.0` (L1131-1132), `T60_RATIO_TOLERANCE = (0.80, 1.25)`
  (L69), `T60_MIN_SPAN_DB = 8.0` (L1979); `verify_score.py`
  `REST_RMS_LIMIT_DBFS = -50.0` (L145). Every number in the prose matches its
  constant exactly.
- **License** — `LICENSE` opens "TsukiSynth — Proprietary License (All Rights
  Reserved)", matching the § License claim.
- **Scope honesty (FM out-of-domain / B5 zero consumption)** — FM Piano is
  declared out of domain consistently in the status table, the Overview and the
  Engine 3 heading. B5's "zero consumption" is true in source: `orthotropic` is
  parsed only in `src/physics/MaterialDB.h` (whose own comment marks it 死資料),
  and `PlateModel.h` L71 / `BeamModel.h` L88 read only the scalar
  `material.youngsModulus`. No engine reads the orthotropic struct.
  27 factory presets counted structurally out of the `FactoryPreset presets[]`
  array in `src/Presets.h`: 27.

**Stale — independently reproduced**

1. **Corpus count and attribution** (§ Hearing-Free Melody Verification, and
   the same figure in § Physical Verification). Replaying
   `verify_score.py::find_all_scores()`'s own four roots gives
   examples 13 + classical 14 + originals/ai_radiance 5 + library 43 = **75**.
   The README attributes the 75 to "`scores/examples/` + `scores/library/`",
   which is only 13 + 43 = 56 — the classical and ai_radiance roots are missing
   from the sentence. The "**73/73**" pass figure is stale: the newest in-repo
   shard evidence (`reports/gate_outputs/b6_corpus_phase4_shard0-3.txt`) reads
   19/19 + 19/19 + 19/19 + 18/18 = **75/75, 0 failed**, with one registered
   exemption visible in shard 0.
2. **B6 status** (Physics-chain table and the v0.3 roadmap row). Both still say
   "Phase 0-1 done … Phase 2 awaiting a scope decision", but `TODO.md` L219
   records B6 as `[x]` Done and L290 states "B6 Phase 3/4 皆 Done" as the
   satisfied precondition for B7; `src/score/ScoreRenderer.h` already emits
   `absolute_pressure_per_force` (L401 region) and `acoustic_transfer[]` (L447).
   The README understates work that ships in the same unstaged batch.
3. **Binary sizes** (§ Plugin Formats) — measured this round:
   VST3 `TsukiSynth.vst3` = 7,891,968 B (**7.53 MiB**, stated 7.42);
   Standalone `TsukiSynth.exe` = 7,764,480 B (**7.40 MiB**, stated 7.30).

**New this round — undocumented tooling**

Three verification tools exist in the working tree but are not wired into any CI
workflow. Until they are listed in the Verification-commands quick reference and
wired into a runner, they are tools that *can* run, not gates that *will* run:
`tools/score_vs_midi_verify.py` (MIDI↔score transcription GATE, 11 checks,
mutation-sentinel 5/5), `tools/melody_roll_video.py` (scrolling piano-roll video
of `melody_verify`'s own verdicts; `--theme neon` since 2026-08-30) and
`tools/stem_verify.py` (2026-08-30, decision-packet Option A: per-event dry stem
rendering + linear-superposition proof; 21 sentinels). On Für Elise complete the
stem path cut refusals from 862/905 to 212/905 and established the superposition
proof (residual −118.60 dBFS vs −85 dBFS budget). **Claim limits are binding:**
pitch verdicts are valid on dry signal only (reverb colours `melody_verify`'s
band centroid by up to 9.5 cents), pitch and onset must be claimed as separate
dimensions, and no partial frequency or amplitude has ever been measured — see
`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.

This audit changes no code, no tolerance and no gate; the corrections above are
the maintainer's call.

**Follow-up (2026-09-25 status check):** the stale items in both audit records
are closed in the text above — the corpus sentence names all four roots and
75/75, the B6 row reads Done, the binary sizes were re-measured (7.58 / 7.46 MiB
on the 2026-09-25 build), and the
quick reference now lists `score_vs_midi_verify` / `stem_verify` /
`partial_verify` / `measurement_selfcal`. `score_vs_midi_verify` is no longer
outside CI: `tests/test_score_vs_midi_verify.py::EndToEndFurEliseTests` asserts
905/905 on the Für Elise pair and runs in the blocking pytest step of
`physics.yml`. `CONTEXT.md` still carries 73/73 but is now marked as a
historical snapshot.
