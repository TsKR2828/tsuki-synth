# TsukiSynth — Multi-Engine VST3/AU Plugin

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
| Preset Manager (12 factory + user save/load) | Done |
| Custom LookAndFeel (dark theme, arc knobs) | Done |
| MIDI Keyboard (on-screen) | Done |
| CLI Score Renderer (JSON -> WAV) | Code done (CLI build broken — known issue) |
| **VST3 build** | **Passed** (6.7 MB, zero warnings) |
| **Standalone build** | **Passed** (6.5 MB, zero warnings) |
| **Standalone launch** | **Passed** (smoke test OK) |
| **DAW plugin host validation** | Pending (no DAW on current machine) |

**Tag**: `playable-vst3-clean-build-v0` — VST3 + Standalone clean build, zero warnings, zero errors.

## Overview

TsukiSynth is a multi-engine software synthesizer plugin based on **Physical Modeling (Modal Synthesis)**. The core engines calculate vibration mode frequencies and decay from physical parameters (material density, plate thickness, string length, strike position), producing physically correct synthesized timbres.

The prototypes originated from [piano-play](https://github.com/TsKR2828/piano-play) and other Web Audio experiments. The codebase has been rewritten in C++ / JUCE as VST3 and AU format for use in DAWs (Cubase, Logic Pro, FL Studio, Reaper, etc.).

## Plugin Formats

| Format | Target DAWs | Status |
|--------|-------------|--------|
| VST3 | Cubase, FL Studio, Ableton, Reaper, Studio One | **Built** (6.7 MB) |
| Standalone | No DAW required | **Built** (6.5 MB) |
| AU (Audio Unit) | Logic Pro, GarageBand, MainStage | CMake option ready |
| AAX | Pro Tools | CMake option ready (requires Avid SDK) |

## Sound Engines

### Engine 1: Cimbalom (Hungarian Dulcimer) — Physical Modeling
- **Modal Synthesis string model** + multi-string beating + damper (CC#64)
- From physical parameters (material density, string diameter, tension, length) calculates N vibration modes with inharmonicity correction
- Strike position affects modal amplitude distribution
- Material stiffness controls overtone spectral tilt (stiffer → brighter, more harmonics)
- Hammer hardness shapes modal excitation spectrum (cotton = warm fundamental, metal = full spectrum)
- Parameters: string material (9 types), diameter, hammer hardness (cotton/felt/wood/metal), strike position, strings per course (1-5), detuning

### Engine 2: Chromatic Synth — Physical Modeling
- Three-in-one engine: Tongue Drum / Water Gong / Custom Harmonics
- Tongue Drum: **Euler-Bernoulli beam model** (non-harmonic modes from eigenvalue formula)
- Water Gong: **Kirchhoff circular plate model** (Bessel function zeros + pitch glide simulating water immersion)
- Custom: user-editable ratio/amplitude manual mode
- Parameters: sub-engine, material, exciter hardness, strike position, thickness, size, pitch glide

### Engine 3: FM Piano — Frequency Modulation
- 2-operator FM synthesis with self-feedback
- 8 sound type presets: Piano, E.Piano, Vibraphone, Bell, Organ, Pad, Bass, Brass
- Velocity-sensitive modulation index + note-dependent brightness decay
- Parameters: sound type, FM ratio, mod index, brightness, feedback, attack, release

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

## Effect Chain

```
[Engine Output] -> Distortion -> Compressor -> Delay -> Reverb -> [Macro Output] -> Output
```

- **Distortion**: Overdrive / Bitcrush / Wavefold with instability control
- **Compressor**: Peak-based, linked stereo detection, auto makeup gain
- **Delay**: Stereo with LP-filtered feedback, R channel offset for width
- **Reverb**: Schroeder (8 comb + 4 allpass), stereo spread

## Analyzer

- **Oscilloscope**: Lock-free AudioFIFO pipeline, 30Hz refresh, zero-crossing trigger, engine-colored waveform
- **Spectrum**: Planned (AnalyzerPanel has slot for SpectrumView)

## Preset System

- 12 factory presets (4 per engine) compiled as static arrays
- User preset save/load (`.tsukipreset` XML files in AppData)
- DAW program change compatible (VST3 `getNumPrograms` / `setCurrentProgram`)
- Dirty indicator + Init button
- Full state serialization (`getStateInformation` / `setStateInformation`)

## Tech Stack

| Item | Technology |
|------|-----------|
| Language | C++17 |
| Framework | JUCE 8.0.12 (git submodule) |
| Build | CMake 3.22+ |
| Synthesis | Modal Synthesis (Physical Modeling) + FM Synthesis |
| DSP Reference | DaisySP (MIT), STK (MIT-like) |
| GUI | Custom LookAndFeel (arc knobs, gradient faces, engine-colored accents) |
| Material Data | JSON embedded via BinaryData (density, Young's modulus, Poisson ratio, damping) |
| Platform | Windows (MSVC), macOS (Clang) planned |

## Directory Structure

```
tsuki-synth/
├── README.md
├── ROADMAP.md
├── DEV-LOG.md / DEVLOG.md
├── CONTEXT.md
├── CMakeLists.txt
├── libs/
│   └── JUCE/                     <- git submodule (JUCE 8.0.12)
├── src/
│   ├── PluginProcessor.h/.cpp    <- main audio processor (APVTS, 3 synths, effect chain)
│   ├── PluginEditor.h/.cpp       <- GUI editor (540x850, tab switching, preset bar)
│   ├── PresetManager.h           <- factory + user preset load/save/dirty tracking
│   ├── Presets.h                 <- 12 factory preset definitions (static arrays)
│   ├── TsukiLookAndFeel.h        <- custom knobs, combos, tabs, colour palette
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
│   │   └── MaterialDB.h          <- JSON material database loader (9 materials)
│   ├── analyzer/
│   │   ├── AnalyzerPanel.h       <- container for oscilloscope + future spectrum
│   │   └── OscilloscopeView.h    <- real-time waveform display (30Hz, zero-crossing trigger)
│   ├── score/
│   │   ├── ScoreParser.h         <- JSON score file parser
│   │   ├── ScoreRenderer.h       <- offline rendering using DSP engines
│   │   └── WavWriter.h           <- 24-bit WAV output with normalization
│   └── cli/
│       └── RenderApp.cpp         <- CLI entry point (single + --batch mode)
├── data/
│   └── materials.json            <- 14 material physical parameters (9 exposed in UI)
├── scores/
│   ├── schema/
│   │   └── score.schema.json     <- JSON Schema validation
│   └── examples/                 <- 36+ score files (6 worlds x 6)
├── sound_library/
│   ├── sound_names.json          <- sound library index
│   └── tags.json                 <- taxonomy (category/mood/energy/world)
├── uiux/                         <- HTML/CSS UI reference mockup
└── presets/
    └── factory/                  <- (reserved for future preset files)
```

## AI JSON Score Pipeline

TsukiSynth supports **AI-driven sound generation** via JSON score files.

Physical modeling parameters are semantic (material, size, strike position). AI can directly generate JSON scores:

```bash
# AI generates score.json -> TsukiSynth renders to WAV
tsukisynth-cli render scores/examples/akashic_bell.score.json

# Batch render
tsukisynth-cli --batch scores/examples/*.score.json --output exports/wav/
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
cmake -B build -G "Visual Studio 17 2022"
cmake --build build --config Release --target TsukiSynth_VST3 TsukiSynth_Standalone
```

### Output
- VST3: `build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3` (6.7 MB)
- Standalone: `build/TsukiSynth_artefacts/Release/Standalone/TsukiSynth.exe` (6.5 MB)

### Verified Build Environment
- VS 2022 Build Tools 17.14.31, MSVC 19.44, Windows SDK 10.0.26100.0
- CMake 4.3.2, JUCE 8.0.12

## License

TBD (personal use / MIT / commercial evaluation in progress)

## Links

- Web prototype: https://github.com/TsKR2828/piano-play
- GitHub: https://github.com/TsKR2828/tsuki-synth
- JUCE: https://juce.com/
