# TsukiSynth — Session Handoff Context

> Copy this into a new conversation to continue seamlessly.

---

## One-liner

Physical Modeling (Modal Synthesis) multi-engine VST3/AU synthesizer plugin + AI JSON sound generator.

## GitHub

https://github.com/TsKR2828/tsuki-synth

## Local Path

```
C:\Users\User.DESKTOP-HA8VHD7\Documents\Claude\tsuki-synth\
```

## Current Progress

**VST3 + Standalone clean build passed** on `DESKTOP-HA8VHD7` (2026-05-08).
Tag: `playable-vst3-clean-build-v0`, branch: `phase1/juce-skeleton`.

All feature code (Phase 0-3) is complete. DAW validation pending (no DAW on current machine).

## Build Environment

| Item | Version |
|------|---------|
| JUCE | 8.0.12 (git submodule at `libs/JUCE`) |
| CMake | 4.3.2 |
| VS Build Tools | 17.14.31, MSVC 19.44 |
| Windows SDK | 10.0.26100.0 |

## Build Commands

```bash
git submodule update --init --recursive
cmake -B build -G "Visual Studio 17 2022"
cmake --build build --config Release --target TsukiSynth_VST3 TsukiSynth_Standalone
```

## Key Files

| File | Content |
|------|---------|
| `README.md` | Project overview, engine specs, directory structure |
| `ROADMAP.md` | Phase 0-3 done, build validation done, DAW validation pending |
| `DEV-LOG.md` | Per-session progress log |
| `TODO.md` | Prioritized task list |
| `CMakeLists.txt` | JUCE submodule, VST3 + Standalone + CLI targets |
| `src/PluginProcessor.h/.cpp` | Main processor (APVTS, 3 synths, effect chain, 40 params) |
| `src/PluginEditor.h/.cpp` | GUI editor (540x850, tabs, preset bar, MIDI keyboard) |
| `src/engines/` | CimbalomEngine, ChromaticEngine, FMPianoEngine |
| `src/effects/EffectChain.h` | Distortion -> Compressor -> Delay -> Reverb |
| `src/PresetManager.h` | 12 factory + user presets, dirty tracking |
| `data/materials.json` | 9 material physical parameters |

## Engines

| # | Engine | Synthesis | Physical Model |
|---|--------|-----------|----------------|
| 1 | Cimbalom | Modal Synthesis | 1D string + inharmonicity + multi-string beating |
| 2 | Chromatic: Tongue Drum | Modal Synthesis | Euler-Bernoulli beam |
| 3 | Chromatic: Water Gong | Modal Synthesis | Kirchhoff circular plate (Bessel zeros) |
| 4 | Chromatic: Custom | Additive | User-defined ratio/amplitude |
| 5 | FM Piano | FM Synthesis | 2-operator with self-feedback, 8 presets |

## APVTS Parameters (40 total)

Global(1) + Macro(8) + Cimbalom(6) + Chromatic(7) + FM(7) + Reverb(2) + Delay(3) + Compressor(2) + Distortion(4)

## Signal Chain

```
Engine -> Distortion -> Compressor -> Delay -> Reverb -> Output (SmoothedValue 20ms) -> Analyzer FIFO
```

## Known Issues

- CLI target (`TsukiSynthCLI`) does not compile — `ScoreRenderer.h` voice API mismatch. Not blocking plugin.
- DAW validation not yet done (no DAW on current machine).

## Rules for Claude

1. Leave files unstaged by default, don't auto commit/push
2. Only do the current batch task, don't expand scope
3. Don't delete legacy prototypes
4. Work on branch, not directly on main
