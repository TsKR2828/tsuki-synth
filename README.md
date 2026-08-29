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
| Preset Browser (visual popup + category filter) | Done |
| Spectrum Analyzer (FFT, log-freq, toggle) | Done |
| Tuner (measured dry audio, A0-C8, confidence/refusal states, hold-after-release) | Done |
| Reverb profile / IR loading (scene JSON → params, WAV → convolution) | Done (2026-08-06) |
| Brightness EQ (creative high shelf: score `effects.eq` + plugin BRIGHTNESS panel) | Done (2026-08-06) |
| Standalone Score console (render score.json / open report, no DAW; bundles CLI) | Done (2026-08-06) |
| Scene→Reverb tool (`tools/scene_reverb.py`, Sabine/Eyring → authored T60) | Done (2026-08-05) |
| Hover magnifier + enlarged tooltips (visual accessibility) | Done (2026-08-06) |
| Harmonic Editor (Custom sub-engine, 8 partials) | Done |
| Responsive UI (resizable 420x700 ~ 900x1200) | Done |
| Custom LookAndFeel (dark theme, arc knobs) | Done |
| MIDI Keyboard (on-screen) | Done |
| CLI Score Renderer (strict JSON -> WAV/FLAC + provenance manifest) | **Passed** — fresh Release build emits and verifies manifest v4, including recursive layer dependencies |
| **VST3 build** | **Passed** — fresh Release build from current source |
| **Standalone build** | **Passed** — fresh Release build from current source |
| **Standalone launch** | **Passed** — current Release build smoke-tested |
| **DAW plugin host validation** | **Passed for v0.2.0 (historical)** — Cubase AI 12, MIDI OK, 56 APVTS params verified. Manual DAW re-validation after the current deep-fix round is still pending (see `TODO.md`) |
| State save/load | Done (skipNextProgramChange + reattachListener fix) |
| Version display | Done (v0.3.0 in title bar) |
| EN/中文 localization | Done |
| Standalone REC recording | Done |

**Version**: `v0.3.0` — the active deep-audit branch is `fix/deep-physics-audit-20260716`. B3 (string damping) has been reviewed and merged to `main`; **B4 (hammer contact), B5 (wood orthotropy schema) and B6 (radiation + calibrated physics-only tap, all phases) are committed to the branch and pushed but not yet merged**, pending the maintainer's UI/UX review and a `main`-merge timing decision. Exact verification state: `HANDOVER.md` (start here for a new session) and `TODO.md`.

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
| Water Gong (PlateModel) | ✅ In domain — Kirchhoff circular plate (clamped + free-edge) | Physically verifiable |
| Custom Harmonics | ⚠️ Half-domain — additive synthesis, ratios checkable but not physically derived | Not a physical-accuracy claim |
| FM Piano | ❌ Out of domain — explicitly non-physical synthesis | Not covered |
| Effect Chain (Reverb/Delay/Comp/Dist) | ❌ Out of domain — verification always runs with FX off | Not covered |
| Chromatic scaling (size → timbre, MIDI → pitch) | ⚠️ Hybrid — physics shapes the spectral content, equal temperament sets f0 | Not "fully physical"; do not describe as such |

For the in-domain engines, `tools/physics_verify.py` compares rendered audio with theory using a ±5-cent frequency gate, ±3.0 dB partial-amplitude gate, +6.0 ±1.0 dB velocity-doubling gate and a measured/model T60 ratio gate; T60 fits must also capture at least 8.0 dB of clean decay. `tools/verify_score.py` measures a multi-string course by its amplitude-weighted centroid with a ±5-cent gate, and also checks rest RMS ≤ −50 dBFS, clipping, manifests and same-environment SHA256 determinism. Manifest v4 binds the WAV, renderer executable, root score and every recursively referenced layer by SHA256, plus a canonical dependency-tree digest and configure-time commit/dirty/toolchain metadata. The 2026-08-02 fresh-build `--full` run has no checked failures; three ultra-short rubber cases are reported as `UNVERIFIED/N/A`, not as passes. A new four-shard full-corpus run passed 75/75 with the one pre-existing visible FX-art exemption and no failures. Current VST3 also passes pluginval L10 across six sample rates and adversarial block sizes, plus the pinned Steinberg SDK 3.8 validator (47/47). See `DEVLOG.md` and `TODO.md`.

These numbers are model-conformance evidence a deaf user (or an AI) can check visually/numerically — via spectrum plots and pass/fail diffs — without relying on how anything sounds. They are not yet a substitute for calibrated external-instrument measurements.

### Physics chain status (2026-08-28)

The string/cimbalom/piano damping law has been extended in stages, each gated on the commands above and, where the render output changes, on a before/after Rule 10 report:

| Stage | What it adds | Status | Report |
|---|---|---|---|
| B1 | Bridge/soundboard admittance — a frequency-independent loss channel from the driving-point admittance of an infinite soundboard plate, wired into Cimbalom/Piano decay only | Done (2026-08-21) | `reports/b1_b2_bridge_damping_before_after.md` |
| B2 | Broadband-damping cleanup — corpus-wide re-verification and loudness-anchor remeasurement after B1 | Done (2026-08-21) | `reports/b1_b2_bridge_damping_before_after.md` |
| B3 | String damping law rewritten to Cuesta & Valette's zero-free-parameter three-mechanism model (air/viscoelastic/thermoelastic loss), replacing two previously unsourced fit constants | Done (2026-08-26, merged to `main`) | `reports/string_damping_firstprinciples_before_after.md` |
| B4 | Hammer/felt contact solved per-note from a nonlinear force law instead of a fixed contact-time constant | Done (2026-08-27) | `reports/b4_hammer_contact_before_after.md` |
| B5 | Orthotropic wood-material schema (9 independent elastic constants per species, from the USDA Wood Handbook) added to `materials.json` | Schema staged, zero consumption — `PlateModel`/`BeamModel` still read a single scalar E/ν; no render output changed | `reports/b5_schema_noop_proof.md` |
| B6 | Radiation-efficiency skeleton (`RadiationModel.h`, σ(f)/η_rad(f)) exposing diagnostic-only `radiated_power_relative`/`absolute_pressure_per_force`/`acoustic_transfer[]` fields in `--dump-modes` | Done (2026-08-28) — Phase 0-1 skeleton, Phase 2 scope decision (方案 B, physics-only signal-tap calibration), Phase 3/4 landed the calibrated tap; diagnostic path only, `render()`/`ModalResonator` untouched (verified bit-identical 8/8) | — |

Full detail and the current decision backlog are in `HANDOVER.md` and `TODO.md`.

## Hearing-Free Melody Verification

Because neither the developer nor the AI can rely on listening, a second verification chain checks *where in time and at what pitch* notes actually land — independent of the acoustic-model checks above:

- **L1 `tools/melody_verify.py`** — compares a rendered WAV against its source score event-by-event (onset ±10ms, pitch within 5 cents), plus 8 fail-closed refusal rules (masking, overtone contamination, course self-beating, bed energy, low-frequency resolution limits, etc.) so it reports `UNVERIFIED` rather than a false pass when a case is outside its proven domain. Five adversarial sentinels (time-shift/transpose/delete-note/phantom-note must FAIL, unmodified must PASS) guard against a rubber-stamp checker. `--html` renders a piano-roll overlay so a Deaf reviewer can inspect the result visually.
- **L2 `TsukiSynthHostProbe`** — a CMake test target that loads the built `.vst3` from disk and drives it like a real host (16/16 automated checks PASS), the first automated proof that the plugin's live audio path (not just the offline CLI renderer) places notes correctly.
- **L3 Cubase real-host verification** — `tools/cubase_scan_verify.py` parses Cubase's own scan-cache XML (5/5 PASS), and a supervised end-to-end pass (project build, MIDI import, tempo-aligned export, reverb zeroed) fed back through `melody_verify.py` scored 5/5 with onset ≤2.5ms / pitch ≤0.4 cents, and reload → re-export reproduced bit-identical audio (SHA256 match).

The regression corpus this all runs against is **75 score files** (`scores/examples/` + `scores/classical/` + `scores/originals/ai_radiance/` + `scores/library/`), currently passing 75/75 with zero newly-registered exemptions per full run.

### Verification commands

```powershell
# C++ invariants, causality, semantic determinism and tuner coverage
ctest --test-dir build -C Release --output-on-failure

# Python metrology/counterexample contracts and the complete physics matrix
python -m unittest discover -s tests -p "test_*.py" -v
python tools\physics_verify.py --selftest
python tools\physics_verify.py --full

# Full score corpus; release CI runs indexes 0..3 in parallel
python tools\verify_score.py --all --shard-index 0 --shard-count 4 `
  --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe

# MSVC AddressSanitizer regression build
cmake -B build-asan -DTSUKI_BUILD_TESTS=ON -DTSUKI_ENABLE_SANITIZERS=ON
cmake --build build-asan --config RelWithDebInfo --target TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest
tools\run_asan_ctest.ps1
```

The exact P1–P7 methods and results are recorded in [the 2026-08-02 verification report](docs/P1_P7_VERIFICATION_2026-08-02.zh-TW.md). For a real instrument specimen, follow [the specimen protocol](docs/SPECIMEN_VALIDATION_PROTOCOL.zh-TW.md). `tools/specimen_pipeline.py` now turns synchronized repeated CSV records into a self-contained v2 bundle: calibrated H1/coherence, complex phase, automatic modal T60, Pa/N, SPL at a declared RMS force, complex directivity points, uncertainty records and SHA256 provenance. `tools/specimen_verify.py` implements all corresponding comparators. The current synth Mode Dump still emits only modal frequency, relative modal magnitude and T60, so phase/SPL/radiation claims remain honestly `UNVERIFIED` until the synth gains those physical model observables; measured data alone is never promoted to PASS.

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
| VST3 | Cubase, FL Studio, Ableton, Reaper, Studio One | **Built** (current x64 binary 7.53 MiB) |
| Standalone | No DAW required | **Built** (current x64 binary 7.40 MiB) |

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
- Custom: user-editable ratio/amplitude via **Harmonic Editor** (8 partials with ratio + amplitude sliders, APVTS-driven) — additive synthesis, ratios checkable but not physically derived
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
- **Reverb**: two modes — algorithmic Schroeder (8 comb + 4 allpass, room-size knob or authored T60 seconds) or IR convolution (load a .wav impulse response via the panel's Load button; also accepts a `scene_reverb.py` JSON profile, which sets T60 + wet on the algorithmic engine)
- **Brightness EQ**: RBJ high shelf (`fx_eq_freq`/`fx_eq_gain`, score `global.effects.eq`); documented creative layer added 2026-08-06 to compensate the perceived darkening after damping physicalization; 0 dB = hard bypass (bit-identical renders)

## Analyzer

- **Oscilloscope**: Lock-free AudioFIFO pipeline, 30Hz refresh, zero-crossing trigger, engine-colored waveform
- **Spectrum**: FFT-based SpectrumView (2048-sample Hann window, log-frequency 30Hz–20kHz, smoothed dB), toggle button in AnalyzerPanel
- **Tuner**: dry pre-FX audio measurement; TARGET and MEASURED are separate; A0–C8 at 44.1/48/96/192 kHz; cent delta, confidence, and explicit `Uncertain`/out-of-range states. It is target-aware monophonic and does not claim polyphonic pitch separation. After note release the last successful detection stays on screen for 10 s, dimmed and labelled LAST (explicitly a held value, not a live measurement).

## Preset System

- 27 factory presets (8 Cimbalom + 8 Chromatic + 9 FM + 2 Physical Piano) compiled as static arrays
- User preset save/load (`.tsukipreset` XML files in AppData), stable UUID identity and atomic replacement
- **Visual preset browser** with category filters (All / Cimbalom / Chromatic / FM / User)
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
| Platform | Windows (MSVC), macOS (Clang) planned |

## Directory Structure

```
tsuki-synth/
├── README.md
├── ROADMAP.md
├── DEVLOG.md
├── CONTEXT.md
├── CMakeLists.txt
├── libs/
│   └── JUCE/                     <- git submodule (JUCE 8.0.12)
├── src/
│   ├── PluginProcessor.h/.cpp    <- main audio processor (APVTS, 3 synths, effect chain)
│   ├── PluginEditor.h/.cpp       <- GUI editor (540x850, tab switching, preset bar)
│   ├── PresetManager.h           <- factory + user preset load/save/dirty tracking
│   ├── PresetBrowser.h           <- visual preset browser popup + category filter
│   ├── Presets.h                 <- 27 factory preset definitions (static arrays)
│   ├── HarmonicEditor.h          <- 8-partial ratio/amplitude editor (Custom sub-engine)
│   ├── TsukiLookAndFeel.h        <- custom knobs, combos, tabs, colour palette
│   ├── UiLocale.h                <- EN/中文 localization layer
│   ├── engines/
│   │   ├── CimbalomEngine.h      <- string physical modeling (40 modes, multi-string beating)
│   │   ├── ChromaticEngine.h     <- beam/plate/custom three-in-one
│   │   └── FMPianoEngine.h       <- 2-operator FM with 8 sound types
│   ├── dsp/
│   │   ├── ModalResonator.h      <- core: N-mode decaying sine renderer
│   │   ├── AudioFIFO.h           <- lock-free FIFO for analyzer
│   │   ├── BiquadFilter.h        <- IIR biquad (LP/HP/BP/Notch)
│   │   ├── Compressor.h          <- peak compressor (dsp-level)
│   │   ├── DelayLine.h           <- circular buffer + linear interpolation
│   │   ├── Distortion.h          <- overdrive / bitcrush / wavefold
│   │   ├── Envelope.h            <- ADSR + ExpDecay
│   │   ├── LFO.h                 <- low-frequency oscillator
│   │   ├── NoiseGen.h            <- white + pink noise
│   │   ├── MidiNoteTracker.h      <- tuner MIDI/retrigger/sustain state
│   │   ├── Oscillator.h          <- phase accumulator (sin/saw/square/tri)
│   │   └── Reverb.h              <- (legacy, replaced by effects/SimpleReverb)
│   ├── effects/
│   │   ├── EffectChain.h         <- global chain: Distortion -> Comp -> Delay -> Reverb
│   │   ├── Compressor.h          <- peak compressor with linked stereo
│   │   ├── StereoDelay.h         <- stereo delay with LP feedback
│   │   └── SimpleReverb.h        <- Schroeder reverb (8 comb + 4 allpass)
│   ├── physics/
│   │   ├── StringModel.h         <- string mode frequency (inharmonicity, physical decay)
│   │   ├── BeamModel.h           <- Euler-Bernoulli beam (tongue drum)
│   │   ├── PlateModel.h          <- Kirchhoff circular plate (Bessel zeros)
│   │   └── MaterialDB.h          <- transactional JSON material database loader (14 materials)
│   ├── analyzer/
│   │   ├── AnalyzerPanel.h       <- Scope / Spectrum / Tuner tabs
│   │   ├── PitchDetector.h       <- bounded target-aware dry-audio pitch estimator
│   │   ├── TunerView.h           <- target/measured/confidence UI
│   │   ├── OscilloscopeView.h    <- real-time waveform display (30Hz, zero-crossing trigger)
│   │   └── SpectrumView.h        <- FFT spectrum (2048-sample, log-freq, smoothed dB)
│   ├── score/
│   │   ├── ScoreParser.h         <- JSON score file parser
│   │   ├── ScoreRenderer.h       <- offline rendering using DSP engines
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
│   └── library/                  <- 43 production short scores (6 worlds)
├── sound_library/
│   ├── sound_names.json          <- sound library index
│   └── tags.json                 <- taxonomy (category/mood/energy/world)
├── uiux/                         <- HTML/CSS UI reference mockup
└── presets/
    └── factory/                  <- (reserved for future preset files)
```

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
cmake --build build --config Release --target TsukiSynthCLI TsukiSynth_VST3 TsukiSynth_Standalone TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest
ctest --test-dir build -C Release --output-on-failure
```

Always rebuild the three test targets (`TsukiSynthAuditTest`, `TsukiSynthTunerTest`, `TsukiSynthPhysicsModelsTest`) immediately before `ctest` — a stale binary from an earlier build will silently report against old code (see `HANDOVER.md` §2, "X4 規約").

### Quick reference (see `HANDOVER.md` §6 for the full list)

| Task | Command |
|---|---|
| Full physics GATE | `python tools/physics_verify.py --full` |
| Score corpus (4 shards) | `python tools/verify_score.py --all --shard-index N --shard-count 4 --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe` |
| Hearing-free melody check | `python tools/melody_verify.py <score> [--wav W] [--html H]` (`--selftest` runs the adversarial sentinels) |
| Live-plugin position check (L2) | `build/Release/TsukiSynthHostProbe.exe build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3 <outdir>` |
| Cubase scan-cache check (L3a) | `python tools/cubase_scan_verify.py` |
| Cross-platform check | `python tools/crossplatform_verify.py --selftest` (CI runs this on push, blocking) |
| Python unit/contract tests | `pytest tests -q` |

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
| v0.3 | Physics hardening | bridge admittance (B1-B2, done) + first-principles string damping (B3, done) + hammer contact solver (B4, done) + wood orthotropy schema (B5, staged) + radiation-efficiency skeleton (B6, done — physics-only signal-tap calibration landed 2026-08-28) |
| v0.4 | AI Sound Library | CLI batch export pipeline, sound library metadata, AI workflow docs; product line = re-rendered public-domain/CC-BY classical arrangements as full multi-engine pieces, not sound-effect packs (see `docs/PRODUCT_MARKET_NOTES.zh-TW.md`) |
| v0.5 | Advanced Sound Design | creative features only with explicit out-of-physical-domain labels |
| v1.0 | Product Release | Installer, user manual, demo videos, commercial licensing |

## License

Proprietary — all rights reserved (commercial rights retained). See [LICENSE](LICENSE).
JUCE 8 is used under the Starter tier (free, revenue < USD 20k, closed-source
distribution permitted); review the JUCE 8 EULA attribution clause before any
public release. The VST3 SDK inside JUCE 8 is MIT.

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

Two new verification tools exist in the working tree but appear nowhere in this
file, `HANDOVER.md`, `TODO.md` or any CI workflow (repo-wide grep: zero hits
outside the tools themselves and `tests/`):
`tools/score_vs_midi_verify.py` (MIDI↔score transcription GATE, 11 checks,
mutation-sentinel 5/5) and `tools/melody_roll_video.py` (scrolling piano-roll
video of `melody_verify`'s own verdicts). Until they are listed in the
Verification-commands quick reference and wired into a runner, they are tools
that *can* run, not gates that *will* run.

This audit changes no code, no tolerance and no gate; the corrections above are
the maintainer's call.
