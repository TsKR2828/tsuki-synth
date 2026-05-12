# TsukiSynth — Session Handoff Context

> Copy this into a new conversation to continue seamlessly.
>
> **⚠️ This is TsukiSynth (月亮旋律), NOT haguruma-engine (齒輪引擎). These are completely independent projects.**

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

**Cimbalom playability pass done** (2026-05-08):
- Hammer spectral shaping: Cotton/Felt/Wood/Metal now shape modal excitation spectrum (hammerCutoffPartial 3/8/20/60)
- Material spectral tilt: overtone brightness scales with log₁₀(Young's modulus)
- Material-dependent exciter brightness and duration
- Hammer-dependent noise amplitude (noiseAmps 0.10/0.20/0.40/0.70)
- Standalone 聽感二次驗收待確認

**Pending**:
- Standalone 聽感二次驗收（Hammer/Material 改善後）
- DAW validation（需回家用 Cubase/Reaper）

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
| `ROADMAP.md` | Phase 0-3 done, playability pass done, DAW validation pending |
| `DEV-LOG.md` | Per-session progress log |
| `TODO.md` | Prioritized task list |
| `CMakeLists.txt` | JUCE submodule, VST3 + Standalone + CLI targets |
| `src/PluginProcessor.h/.cpp` | Main processor (APVTS, 3 synths, effect chain, 40 params) |
| `src/PluginEditor.h/.cpp` | GUI editor (540x850, tabs, preset bar, MIDI keyboard) |
| `src/engines/CimbalomEngine.h` | Cimbalom: modal string + hammer spectral shaping + material tilt |
| `src/engines/ChromaticEngine.h` | Chromatic: tongue drum / water gong / custom |
| `src/engines/FMPianoEngine.h` | FM Piano: 2-op FM, 8 sound types |
| `src/effects/EffectChain.h` | Distortion -> Compressor -> Delay -> Reverb |
| `src/PresetManager.h` | 12 factory + user presets, dirty tracking |
| `data/materials.json` | 14 material physical parameters (9 exposed in UI) |

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

## Cimbalom DSP Details (recent changes)

Hammer shapes modal excitation spectrum via 2nd-order LP: `1/(1+(n/cutoff)²)`
- Cotton: cutoff = 3rd partial (warm, only fundamental)
- Felt: cutoff = 8th partial
- Wood: cutoff = 20th partial
- Metal: cutoff = 60th partial (full spectrum)

Material spectral tilt: `pow(spectralTilt, (partialN-1)*0.2)`
- spectralTilt = jlimit(0.1, 1.0, (log₁₀(E) - 7.5) / 4.0)
- Steel=0.95, Glass=0.84, Spruce=0.645, Rubber=0.10

Exciter noise: cutoff × materialBright, amplitude × noiseAmps[hammer], duration × durScale

## Known Issues

- CLI target (`TsukiSynthCLI`) does not compile — `ScoreRenderer.h` voice API mismatch. Not blocking plugin.
- DAW validation not yet done (no DAW on current machine).
- Spruce vs Maple 頻譜傾斜接近 (0.645 vs 0.649)，可能需要進一步調整

## Rules for Claude

1. **這是 TsukiSynth，不是 haguruma-engine。兩個專案完全獨立。**
2. Leave files unstaged by default, don't auto commit/push
3. Only do the current batch task, don't expand scope
4. Don't delete legacy prototypes
5. Work on branch, not directly on main
