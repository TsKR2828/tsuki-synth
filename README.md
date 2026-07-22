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
| Tuner (measured dry audio, A0-C8, confidence/refusal states) | Done |
| Harmonic Editor (Custom sub-engine, 8 partials) | Done |
| Responsive UI (resizable 420x700 ~ 900x1200) | Done |
| Custom LookAndFeel (dark theme, arc knobs) | Done |
| MIDI Keyboard (on-screen) | Done |
| CLI Score Renderer (strict JSON -> WAV/FLAC + manifest) | Done (80/80 schema-valid; 73/73 release corpus verified) |
| **VST3 build** | **Passed** (current x64 binary 7.42 MiB) |
| **Standalone build** | **Passed** (current x64 binary 7.30 MiB) |
| **Standalone launch** | **Passed** (smoke test OK) |
| **DAW plugin host validation** | **Passed for v0.2.0 (historical)** — Cubase AI 12, MIDI OK, 56 APVTS params verified. Manual DAW re-validation after the current deep-fix round is still pending (see `TODO.md`) |
| State save/load | Done (skipNextProgramChange + reattachListener fix) |
| Version display | Done (v0.2.0 in title bar) |
| EN/中文 localization | Done |
| Standalone REC recording | Done |

**Version**: `v0.2.0` — the active deep-audit branch and exact verification state are documented in `docs/DEEP_FIX_VERIFICATION_2026-07-17.zh-TW.md`.

## Overview

TsukiSynth is a multi-engine software synthesizer plugin based on **Physical Modeling (Modal Synthesis)**. The Cimbalom (string), Tongue Drum (beam), and Water Gong (plate) engines calculate vibration mode frequencies and decay from physical parameters (material density, plate thickness, string length, strike position). These are **physically verifiable**: rendered frequency, amplitude, and decay are checked by an automated harness against theoretical predictions (see [Physical Verification](#physical-verification) below). The FM Piano engine and the effect chain are outside this verification domain — see the same section for the full scope declaration.

The prototypes originated from [piano-play](https://github.com/TsKR2828/piano-play) and other Web Audio experiments. The codebase has been rewritten in C++ / JUCE as VST3 and AU format for use in DAWs (Cubase, Logic Pro, FL Studio, Reaper, etc.).

## Core Direction

TsukiSynth is positioned as a **Physical Modeling synthesizer** with semantic parameters, not a general-purpose wavetable or subtractive synth. The core differentiators:

- **Physical Modeling main body** — Modal Synthesis from real material properties (density, Young's modulus, damping); physically verifiable for the string/beam/plate engines (see [Physical Verification](#physical-verification))
- **Semantic parameters** — "material = steel", "hammer = felt" instead of abstract oscillator/filter knobs
- **AI JSON Score Pipeline** — AI can directly generate sound design via JSON score files
- **VTuber / worldview sound design** — targeted at character UI sounds, world-themed sound libraries
- **WAV export** — CLI batch rendering for sound library generation without a DAW

## Physical Verification

TsukiSynth's physical claims are scoped and machine-checked, not aspirational — see `ROADMAP_PHYSICS.md` §0 for the full verification-domain table. Summary:

| Component | Verification domain | Status |
|---|---|---|
| Cimbalom / Piano (StringModel) | ✅ In domain — struck rigid string, incl. inharmonicity | Physically verifiable |
| Tongue Drum (BeamModel) | ✅ In domain — fixed-free cantilever by default; explicit free-free suspended bar | Physically verifiable |
| Water Gong (PlateModel) | ✅ In domain — Kirchhoff circular plate (clamped + free-edge) | Physically verifiable |
| Custom Harmonics | ⚠️ Half-domain — additive synthesis, ratios checkable but not physically derived | Not a physical-accuracy claim |
| FM Piano | ❌ Out of domain — explicitly non-physical synthesis | Not covered |
| Effect Chain (Reverb/Delay/Comp/Dist) | ❌ Out of domain — verification always runs with FX off | Not covered |
| Chromatic scaling (size → timbre, MIDI → pitch) | ⚠️ Hybrid — physics shapes the spectral content, equal temperament sets f0 | Not "fully physical"; do not describe as such |

For the in-domain engines, `tools/physics_verify.py` compares rendered audio with theory using a ±5-cent frequency gate, ±3.0 dB partial-amplitude gate, +6.0 ±1.0 dB velocity-doubling gate and a measured/model T60 ratio gate. `tools/verify_score.py` separately keeps a ±12-cent dump-mode check because a multi-string course's first dumped string is intentionally detuned; it also checks rest RMS ≤ −50 dBFS, clipping, manifests and same-environment SHA256 determinism. The 2026-07-17 `--full` run has no checked failures; three ultra-short rubber cases are reported as `UNVERIFIED/N/A`, not as passes. The latest release corpus is 73/73 PASS with one pre-existing, visible FX-art exemption and no new exemptions. See the [deep-fix verification report](docs/DEEP_FIX_VERIFICATION_2026-07-17.zh-TW.md).

These numbers are quality claims a deaf user (or an AI) can check visually/numerically — via spectrum plots and pass/fail diffs — without relying on how anything sounds.

## Plugin Formats

| Format | Target DAWs | Status |
|--------|-------------|--------|
| VST3 | Cubase, FL Studio, Ableton, Reaper, Studio One | **Built** (current x64 binary 7.42 MiB) |
| Standalone | No DAW required | **Built** (current x64 binary 7.30 MiB) |
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
[Engine Output] -> Distortion -> Compressor -> Delay -> Reverb -> [Macro Output] -> Output
```

- **Distortion**: Overdrive / Bitcrush / Wavefold with instability control
- **Compressor**: Peak-based, linked stereo detection, auto makeup gain
- **Delay**: Stereo with LP-filtered feedback, R channel offset for width
- **Reverb**: Schroeder (8 comb + 4 allpass), stereo spread

## Analyzer

- **Oscilloscope**: Lock-free AudioFIFO pipeline, 30Hz refresh, zero-crossing trigger, engine-colored waveform
- **Spectrum**: FFT-based SpectrumView (2048-sample Hann window, log-frequency 30Hz–20kHz, smoothed dB), toggle button in AnalyzerPanel
- **Tuner**: dry pre-FX audio measurement; TARGET and MEASURED are separate; A0–C8 at 44.1/48/96/192 kHz; cent delta, confidence, and explicit `Uncertain`/out-of-range states. It is target-aware monophonic and does not claim polyphonic pitch separation.

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
cmake -B build -G "Visual Studio 17 2022"
cmake --build build --config Release --target TsukiSynthCLI TsukiSynth_VST3 TsukiSynth_Standalone TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest
ctest --test-dir build -C Release --output-on-failure
```

### Output
- VST3: `build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3` (current x64 binary 7.42 MiB)
- Standalone: `build/TsukiSynth_artefacts/Release/Standalone/TsukiSynth.exe` (current x64 binary 7.30 MiB)

### Verified Build Environment
- VS 2022 Build Tools 17.14.31, MSVC 19.44, Windows SDK 10.0.26100.0
- CMake 4.3.2, JUCE 8.0.12

## Version Roadmap

| Version | Milestone | Key Items |
|---------|-----------|-----------|
| v0.1 | Playable Build | 3 engines, effects, presets, CLI — **Done** |
| v0.2 | Polish | DAW validation, standalone listening test, factory preset tuning |
| v0.3 | Physics hardening | external specimen validation, calibrated amplitudes, coupled-body/damper work |
| v0.4 | AI Sound Library | CLI batch export pipeline, sound library metadata, AI workflow docs |
| v0.5 | Advanced Sound Design | creative features only with explicit out-of-physical-domain labels |
| v1.0 | Product Release | Installer, user manual, demo videos, commercial licensing |

## License

TBD (personal use / MIT / commercial evaluation in progress)

## Links

- Web prototype: https://github.com/TsKR2828/piano-play
- GitHub: https://github.com/TsKR2828/tsuki-synth
- JUCE: https://juce.com/
