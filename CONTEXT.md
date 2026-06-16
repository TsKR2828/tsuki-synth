# TsukiSynth — Session Handoff Context

> Copy this into a new conversation to continue seamlessly.
>
> **⚠️ This is TsukiSynth (月亮旋律), NOT haguruma-engine (齒輪引擎). Independent projects.**

---

## One-liner

Physical-modeling (modal synthesis) multi-engine VST3/Standalone synth + AI JSON
sound generator (CLI score → WAV).

## 🎯 Project goal (月月, 2026-06)

**Deaf people + AI verify and simulate sound by PHYSICAL THEORY, not by ear.**
Three pillars: **reproducibility, physical verifiability, instrument-physics
correctness.** The CLI/score path (no listening) is the primary interface; the
verification harness (`tools/physics_verify.py`) is the "ruler".

## GitHub / branch / local

- Repo: https://github.com/TsKR2828/tsuki-synth
- **Active branch: `Codex-fix-bug`** (pushed). Built on Codex `b5a370d` (PR #4).
- Local path: `C:\Users\admin\Desktop\Claude\tsuki-synth`

## Current state (2026-06-16)

All audit bugs fixed; physics-accuracy pass done. **All 6 engines pass the
verification harness; CLI + Standalone build clean.**

| Area | State |
|------|-------|
| Determinism | ✅ NoiseGen seeded; same score → byte-identical render |
| Verification | ✅ `tools/physics_verify.py` (partials / `--levels` / `--t60`) |
| CLI introspection | ✅ `--dump-modes <score.json>` (model's exact partials, JSON) |
| Cimbalom tuning | ✅ pinned to MIDI pitch (stiff-string √(1+B) comp) |
| Engine levels | ✅ equal-RMS calibrated (cross-engine 8 dB → 0.2 dB) |
| Water gong | ✅ true **clamped Kirchhoff plate** (was membrane approx); optional free-edge via `plate_free_edge` |
| Physical piano | ✅ CLI engine `"piano"` (struck stiff steel string) + plugin Cimbalom presets |
| FM Piano | kept as labelled **non-physical** FM synth voice |

## Engines

| # | Engine | Physics |
|---|--------|---------|
| Cimbalom | modal | stiff string + inharmonicity + multi-string beating |
| Chromatic: Tongue Drum | modal | free-free Euler-Bernoulli beam |
| Chromatic: Water Gong | modal | clamped Kirchhoff plate (Ω=λ², Leissa); free-edge optional |
| Chromatic: Custom | additive | user ratio/amplitude |
| FM Piano | FM | 2-op (non-physical; labelled) |
| **piano** (CLI/score) | modal | struck stiff steel string (StringModel) |

## Build environment

- JUCE 8.0.12 (submodule `libs/JUCE`); CMake; MSVC. Build dir `build/`,
  generator **Visual Studio 18 2026**.
- This machine: load `D:\Visual_Studio\VC\Auxiliary\Build\vcvars64.bat` before `cl`/cmake.
- Python 3.13 with numpy + scipy (for the harness).

## Build & verify commands

```powershell
# build (after vcvars64)
cmake --build build --config Release --target TsukiSynthCLI TsukiSynth_Standalone

# physics verification (ear-free)
python tools/physics_verify.py                 # all engines: f0 cents + partials
python tools/physics_verify.py --levels        # per-engine RMS/peak
python tools/physics_verify.py --t60           # modal decay vs model
python tools/physics_verify.py --engines water_gong water_gong_free   # A/B

# inspect a score's predicted physics
build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe --dump-modes <score.json>
```

## Key files

| File | Content |
|------|---------|
| `tools/physics_verify.py` | render → FFT → compare-to-theory harness (the "ruler") |
| `tests/audit_repro.cpp` | the 2026-06 audit bugs as executable checks |
| `src/physics/{String,Beam,Plate}Model.h` | the physics (string / beam / clamped+free plate) |
| `src/engines/CimbalomEngine.h` | struck stiff string (also backs the physical piano) |
| `src/engines/ChromaticEngine.h` | tongue drum / water gong / custom; `tuneChromaticModesToMidi` |
| `src/score/ScoreRenderer.h` | CLI render + `dumpModes`; **no Macro feel-layer (pure physics)** |
| `src/PluginProcessor.cpp` | 3 plugin engines, FX chain, dynamic tail length |
| `data/materials.json` | 14 materials (density / Young's / Poisson / damping) |

## Pending — needs 月月 decision

1. **Plugin 4th "Piano" engine tab** — requires APVTS state-compat check:
   confirm the `engine` choice is stored **denormalized** (then appending "Piano"
   at index 3 is safe for old DAW projects; if normalized, old states remap to
   the wrong engine). Physical piano already ships via Cimbalom preset + CLI.
2. **Water gong character** — A/B clamped (default) vs free-edge
   (`scores/examples/water_gong_{clamped,free}.score.json`).
3. **In-plugin loudness balance** (FM vs modal) — CLI is equal-RMS; confirm by ear.

## Rules for Claude

1. This is TsukiSynth, not haguruma-engine.
2. Default: leave files unstaged, don't commit/push unless asked (this session
   was an explicit exception — `Codex-fix-bug` is pushed).
3. Work on a branch, not main.
4. Don't delete legacy prototypes.
5. For physics changes, **verify with `physics_verify.py`** before claiming done;
   don't hardcode physical constants you can't confirm against a reference.
