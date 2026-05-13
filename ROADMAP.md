# TsukiSynth — Development Roadmap

> Last updated: 2026-05-13
>
> This document tracks the real project status based on actual repo state,
> not planned/estimated phases.

---

## Phase Summary

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 | Planning / schema / example scores | **Done** |
| Phase 1 | JUCE / VST3 skeleton + DSP modules | **Done** |
| Phase 2 | Three sound engines (Cimbalom / Chromatic / FM Piano) | **Done** |
| Phase 3 | Oscilloscope + 8 Macro parameters + Preset Manager | **Done** |
| — | Build validation (VST3 + Standalone) | **Done** |
| — | Cimbalom playability pass (hammer + material DSP) | **Done** |
| Phase 4 | UI Enhancements (Spectrum / Preset Browser / Harmonic Editor / Responsive) | **Done** |
| — | CLI build fix (standalone voice API + juce_dsp link) | **Done** |
| — | DAW validation (host scan / automation / state) | Pending (no DAW on current machine) |

---

## Phase 0: Planning ✅

- Project structure, README, ROADMAP
- `data/materials.json` (9 materials with density, Young's modulus, Poisson ratio, damping)
- `scores/schema/score.schema.json` (JSON Schema draft 2020-12)
- 3 example score files
- `sound_library/sound_names.json` + `tags.json` taxonomy
- CONTEXT.md for session handoff

## Phase 1: JUCE / VST3 Skeleton + DSP Modules ✅

**Skeleton:**
- `CMakeLists.txt` — JUCE as git submodule, VST3 + Standalone + CLI targets
- `PluginProcessor` — APVTS-based, 3 `juce::Synthesiser` instances (16 voices each)
- `PluginEditor` — 540x850 window, tab switching, preset bar, MIDI keyboard
- AAX/AU conditional build support (`-DTSUKI_AAX=ON`, `-DTSUKI_AU=ON`)

**DSP modules (all header-only, `src/dsp/`):**
- `ModalResonator` — core N-mode decaying sine renderer with excite/damp API
- `Oscillator`, `Envelope` (ADSR + ExpDecay), `BiquadFilter`, `DelayLine`
- `NoiseGen` (white + pink), `LFO`, `Distortion`, `AudioFIFO`

**Physics modules (`src/physics/`):**
- `StringModel` — string mode frequency with inharmonicity correction
- `BeamModel` — Euler-Bernoulli free-free beam (20 eigenvalues)
- `PlateModel` — Kirchhoff clamped circular plate (25 Bessel zeros)
- `MaterialDB` — JSON loader, embedded via BinaryData

## Phase 2: Three Sound Engines ✅

**Cimbalom Engine (`CimbalomEngine.h`):**
- Modal Synthesis string model, 40 modes per voice
- Multi-string beating (1-5 strings per course, adjustable detuning)
- Material spectral tilt: log₁₀(E)-based overtone rolloff (stiff → bright, soft → warm)
- Hammer force spectrum shaping: 2nd-order LP on mode amplitudes (cotton cutoff=3rd partial, metal=60th)
- Exciter noise burst with material-dependent brightness and hammer-dependent amplitude
- Damper via note-off + CC#64 sustain pedal
- 6 parameters: Material, Strike Position, Diameter, Hammer, Strings, Detuning

**Chromatic Engine (`ChromaticEngine.h`):**
- Three sub-engines: Tongue Drum (beam) / Water Gong (plate) / Custom (manual ratio)
- Water Gong pitch glide (frequency drop simulating water immersion)
- 7 parameters: Sub-Engine, Material, Exciter, Strike Position, Thickness, Size, Pitch Glide

**FM Piano Engine (`FMPianoEngine.h`):**
- 2-operator FM with modulator self-feedback
- 8 sound type presets controlling ADSR shape
- Velocity-sensitive mod index + note-dependent brightness decay
- 7 parameters: Sound Type, FM Ratio, Mod Index, Brightness, Feedback, Attack, Release

**Effect Chain (`effects/EffectChain.h`):**
- Processing order: Distortion → Compressor → Delay → Reverb
- Distortion: Overdrive / Bitcrush / Wavefold with instability
- Compressor: peak-based, linked stereo, auto makeup
- Delay: stereo with LP feedback, R channel offset
- Reverb: Schroeder (8 comb + 4 allpass)
- 11 effect parameters total

## Phase 3: Oscilloscope + Macro Panel + Preset Manager ✅

**Oscilloscope (`analyzer/`):**
- `AudioFIFO` — lock-free single-producer single-consumer ring buffer (4096 samples)
- `OscilloscopeView` — 30Hz timer, zero-crossing trigger, engine-colored waveform
- `AnalyzerPanel` — container with slot for future SpectrumView

**8 Macro Parameters (DAW automatable):**
- Material / Tension / Damping / Strike / Brightness / Body / Noise / Output
- Cross-mapped to all three engines (center 0.5 = neutral)
- Output is **post-FX** final gain with per-sample `SmoothedValue` (commit `a26ca48`)

**Preset Manager (`PresetManager.h` + `Presets.h`):**
- 12 factory presets (4 per engine, static arrays)
- User preset save/load (`.tsukipreset` XML files, AppData directory)
- DAW program change support (`getNumPrograms` / `setCurrentProgram`)
- Full state serialization (XML via ValueTree)
- Dirty tracking + Init button

**Custom LookAndFeel (`TsukiLookAndFeel.h`):**
- Dark theme with gold/teal/purple engine accents
- Custom rotary knobs (arc track + gradient face + indicator)
- Custom combo boxes, tabs, popup menus
- Moon crescent wordmark in title bar

**CLI Score Renderer:**
- `ScoreParser` / `ScoreRenderer` / `WavWriter`
- Single file + `--batch` mode
- 36 example scores (6 worlds x 6)
- `TsukiSynthCLI` CMake target

---

## Cimbalom Playability Pass ✅ (2026-05-08)

**Problem**: Hammer types (Cotton/Felt/Wood/Metal) sounded nearly identical; materials had insufficient timbral differentiation.

**Root cause**: Hammer only affected a 1-4ms noise burst, not the modal resonator excitation. Material differences were cancelled by auto-tension (T = μ×(2L×f1)²).

**Fixes** (1 file: `CimbalomEngine.h`):
- Hammer spectral shaping: `hammerCutoffPartial[] = {3, 8, 20, 60}` — 2nd-order LP on mode amplitudes
- Hammer-dependent noise amplitude: `noiseAmps[] = {0.10, 0.20, 0.40, 0.70}`
- Material spectral tilt: `pow(tilt, (partialN-1)*0.2)` from log₁₀(Young's modulus)
- Material-dependent exciter brightness and duration

---

## Build Validation ✅ (2026-05-08)

**Status**: VST3 + Standalone clean build passed. Zero warnings, zero errors. Tag: `playable-vst3-clean-build-v0`.

### Build Environment

| Item | Status |
|------|--------|
| JUCE submodule (`libs/JUCE`) | ✅ JUCE 8.0.12 (commit `501c076`) |
| CMake | ✅ 4.3.2 |
| Visual Studio / MSVC | ✅ Build Tools 17.14.31, MSVC 19.44 |
| VST3 output | ✅ 6.7 MB |
| Standalone output | ✅ 6.5 MB |
| CLI output | ✅ Batch render verified (4/4 scores) |

### DAW Validation (pending — needs DAW on home machine)

1. Copy VST3 to `C:\Program Files\Common Files\VST3\` (needs admin)
2. Load in DAW (Cubase / Reaper) — verify plugin scan, MIDI input, audio output
3. Test automation list — verify all 40 APVTS parameters appear in DAW lanes
4. Test state restore — save/load DAW session, verify preset recall

### Known Issues

- (Resolved 2026-05-13) CLI target now compiles and renders — standalone DSP API added to all three engines, `juce_dsp` linked, `ScoreRenderer.h` `baseDir` member added.

### Previous Build History

The code was previously built and verified on a different machine:
- VS2026 Community (D:\Visual_Studio, MSVC 14.50.35717)
- CMake 4.3.2
- Cubase LE AI Elements 12
- VST3 + Standalone confirmed working (see DEV-LOG.md / DEVLOG.md)

---

## Phase 4: UI Enhancements ✅ (2026-05-13)

**Branch**: `feature/ui-enhancements`

**CLI Build Fix:**
- Added standalone DSP API (`prepare`, `noteOn`, `noteOff`, `isActive`, `getNextSample`) to all three engine voices
- Added `juce::juce_dsp` to CMakeLists CLI target
- Fixed `ScoreRenderer.h` missing `baseDir` member
- Verified batch render: 4/4 scores rendered successfully

**Spectrum Analyzer (`analyzer/SpectrumView.h`):**
- FFT-based spectrum view (2048-sample Hann window, order 11)
- Log-frequency X axis (30Hz–20kHz), dB Y axis (-80 to 0)
- Smoothed magnitudes (factor 0.7), filled path rendering, 30Hz timer
- Integrated into `AnalyzerPanel` with SCOPE/SPECTRUM toggle button
- Sample rate forwarded from processor, accent color shared with oscilloscope

**Preset Browser (`PresetBrowser.h`):**
- Visual popup panel replacing ComboBox preset selector
- Category filter buttons: All / Cimbalom / Chromatic / FM / User
- Scrollable preset list with current-preset highlight
- `PresetNameButton` with hover state and dropdown arrow

**Harmonic Editor (`HarmonicEditor.h`):**
- 8-partial ratio/amplitude visual editor for Chromatic Custom sub-engine
- 16 new APVTS parameters: `chr_ratio_0`~`chr_ratio_7`, `chr_amp_0`~`chr_amp_7`
- `ChromaticEngine.h` `buildCustomModes()` reads from APVTS instead of hardcoded arrays
- Visible only when Chromatic engine + Custom sub-engine selected
- `chr_sub_engine` parameter listener for auto-show/hide

**Responsive UI:**
- `setResizable(true, true)` with limits 420x700 ~ 900x1200
- Existing `resized()` layout already handles flexible engine area

---

## TODO (after UI enhancements)

### Factory Presets v1
- Review and tune 12 factory presets with actual audio output
- A/B compare with Web Audio prototypes
- Consider adding more presets per engine

### UI / UX Polish
- Preset browser: preview/audition before loading
- Modal distribution visualization
- Keyboard range indicator
- Version number display

### Product Documentation
- User manual (parameter reference, preset creation guide)
- Sound design guide (material → timbre relationships)
- AI Score Pipeline tutorial
- Build instructions for contributors

### AAX Format (low priority)
- Avid Developer account registration
- AAX SDK download and integration
- Pro Tools validation

---

## Source File Inventory (39 files)

```
src/PluginProcessor.h          src/PluginProcessor.cpp
src/PluginEditor.h             src/PluginEditor.cpp
src/PresetManager.h            src/Presets.h
src/PresetBrowser.h            src/HarmonicEditor.h
src/TsukiLookAndFeel.h         src/UiLocale.h

src/engines/CimbalomEngine.h   src/engines/ChromaticEngine.h
src/engines/FMPianoEngine.h

src/dsp/ModalResonator.h       src/dsp/AudioFIFO.h
src/dsp/BiquadFilter.h         src/dsp/Compressor.h
src/dsp/DelayLine.h            src/dsp/Distortion.h
src/dsp/Envelope.h             src/dsp/LFO.h
src/dsp/NoiseGen.h             src/dsp/Oscillator.h
src/dsp/Reverb.h

src/effects/EffectChain.h      src/effects/Compressor.h
src/effects/StereoDelay.h      src/effects/SimpleReverb.h

src/physics/StringModel.h      src/physics/BeamModel.h
src/physics/PlateModel.h       src/physics/MaterialDB.h

src/analyzer/AnalyzerPanel.h   src/analyzer/OscilloscopeView.h
src/analyzer/SpectrumView.h

src/score/ScoreParser.h        src/score/ScoreRenderer.h
src/score/WavWriter.h

src/cli/RenderApp.cpp
```

## APVTS Parameter Count

| Group | Count | Parameters |
|-------|-------|-----------|
| Global | 1 | engine |
| Macro | 8 | macro_material, macro_tension, macro_damping, macro_strike, macro_brightness, macro_body, macro_noise, macro_output |
| Cimbalom | 6 | cim_material, cim_hammer, cim_strike_pos, cim_diameter, cim_num_strings, cim_detuning |
| Chromatic | 7 | chr_sub_engine, chr_material, chr_exciter, chr_strike_pos, chr_thickness, chr_size, chr_pitch_glide |
| Chromatic Harmonics | 16 | chr_ratio_0~7, chr_amp_0~7 |
| FM Piano | 7 | fm_type, fm_ratio, fm_index, fm_brightness, fm_feedback, fm_attack, fm_release |
| Reverb | 2 | fx_reverb_mix, fx_reverb_size |
| Delay | 3 | fx_delay_time, fx_delay_feedback, fx_delay_mix |
| Compressor | 2 | fx_comp_threshold, fx_comp_ratio |
| Distortion | 4 | fx_dist_type, fx_dist_drive, fx_dist_instability, fx_dist_mix |
| **Total** | **56** | |
