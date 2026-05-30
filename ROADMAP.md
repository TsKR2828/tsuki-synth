# TsukiSynth — Development Roadmap

> Last updated: 2026-05-31
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
| — | DAW validation (host scan / automation / state) | Pending |
| v0.2 | Codex audit fixes + i18n + recorder + range indicator | **Done** |
| — | FM Piano P0-P2 (defaults / velocity / 3-stack E.Piano) | **Done** (unstaged) |
| — | Body Resonance Layer + Raw/Body preset split | **Done** (unstaged) |
| — | Engine-filtered preset list | **Done** (unstaged) |
| — | Tuner View (NSDF pitch detection) | **Done** (unstaged) |
| — | Tuner structural fix (zero-lag skip, dry FIFO, SR sync, low-freq) | **Done** (unstaged) |

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

## Brand Asset Correction (2026-05-13)

**Problem**: Logo rendering (moon crescent + wordmark + subtitle) diverged from the HTML/JSX design mockup in `uiux/`.

**Root cause** (three layers):
1. Moon crescent used `fillEllipse` + `addCentredArc` approximation instead of the original SVG path
2. Arc approximation changes the design's curves/tension/tips — not a parameter drift, a shape replacement
3. Wordmark font fell back to system font (Microsoft JhengHei from CJK LookAndFeel) instead of IBM Plex Sans SemiBold

**Fixes** (`PluginEditor.cpp/h`, `CMakeLists.txt`):
- Moon: `Drawable::parseSVGPath("M14 3 a8 8 0 1 0 0 14 a6 6 0 0 1 0 -14 z")` — exact path from `uiux/components.jsx`
- Font: IBM Plex Sans SemiBold embedded via `juce_add_binary_data` → `Typeface::createSystemTypefaceFor`
- Wordmark: `GlyphArrangement` → `Path` → gradient fill (`#f0e8d8` → `#c49a6c`), matching CSS exactly
- All coordinates sourced from `uiux/TsukiSynth.html` CSS with inline comments tracing each value
- `kTitleH` adjusted from 56 → 64 (CSS: 16 + 22 + 4 + 12 + 10)

**New file**: `data/fonts/IBMPlexSans-SemiBold.ttf` (306 KB, OFL license)

**Lesson**: Brand assets (SVG paths, fonts, colours) must be embedded directly from the design source, never approximated through code. The HTML/JSX design files in `uiux/` are the single source of truth.

---

## Version Roadmap

| Version | Milestone | Status |
|---------|-----------|--------|
| v0.1 | Playable Build — 3 engines, effects, presets, analyzer, CLI | **Done** |
| v0.2 | Polish — DAW validation, listening test, factory preset tuning | Next |
| v0.3 | Sonic Identity — Sample Layer v0, world-themed preset library | Planned |
| v0.4 | AI Sound Library — CLI batch export, metadata, AI workflow docs | Planned |
| v0.5 | Advanced Sound Design — Granular mode, mod matrix lite, preset tags | Planned |
| v1.0 | Product Release — Installer, manual, demo videos, licensing | Planned |

---

## v0.2 Polish Pass (2026-05-15 — 2026-05-31)

### Codex Audit + i18n + Recorder (2026-05-15, commit `0769e5a`)
- 8/8 audit findings fixed (4 P1 critical + 4 P2 robustness)
- Bilingual UI: English / Traditional Chinese (`UiLocale.h`)
- Language toggle button, all labels/combos/preset names/dialogs translated
- MIDI keyboard range indicator per engine
- Standalone WAV recorder (REC/STOP, saves to Documents/TsukiSynth/Recordings)
- 18 → 21 factory presets

### FM Piano P0-P2 (2026-05-30, unstaged)
- P0: unified APVTS/FMParams defaults, Vibraphone/Brass presets, `fm_brightness` → "TONE DECAY"
- P1: velocity-to-index curve, attack/body index split, per-type body resonance
- P2: E.Piano 3-stack mode (Body 1:1 + Tine 14:1 + Shimmer 3:1), "Layered E.Piano" preset
- 21 → 25 factory presets (8 FM total)

### Body Resonance + Preset Split (2026-05-30, unstaged)
- `BodyResonance.h`: procedural low-freq body (2 bandpass + LP + envelope), driven by `macro_body`
- All existing Cimbalom/Chromatic presets marked Raw (`macro_body=0`)
- 4 new Body-enhanced presets (macro_body 0.70–0.85)
- Engine-filtered preset list: ComboBox only shows presets matching current engine tab
- 25 factory presets total

### Tuner View (2026-05-30 — 2026-05-31, unstaged)
- `TunerView.h`: McLeod NSDF pitch detection with parabolic interpolation
- AnalyzerPanel: SCOPE / SPECTRUM / TUNER three-tab switching
- Structural fix: zero-lag lobe skip, removed faulty octave-down correction
- Dry signal routing: `analyzerDryFifo` feeds tuner pre-FX mono signal
- Sample rate sync: editor timer continuously updates analyzer SR from host
- Low-frequency range extended to ~20 Hz (was ~50 Hz), covers C1 (32.7 Hz)

---

## Anti-Click/Pop DSP Fixes (2026-05-15)

**Critical bug fixed**: Water Gong pitch glide was calling `setModes()` (which resets phase/amplitude) every render block. Added `ModalResonator::updateFrequencies()` for phase-preserving frequency updates.

**Voice stealing**: All three engines now apply a micro-damp (0.002s) before `clearCurrentNote()` on hard stop.

**Engine switch**: Changed `allNotesOff(0, false)` → `allNotesOff(0, true)` for graceful tail-off.

**FM retrigger**: `Envelope::noteOn()` no longer resets `currentLevel` to 0, avoiding click on retrigger.

---

## Code Audit — 8 Findings Fixed (2026-05-15)

**4× P1 (Critical):**
- Score pipeline: plate→WaterGong mapping, exciter string aliases, tension/damping override wiring
- Engine switch: `tailOffEngine` dual-render so old engine voices actually decay instead of being silently discarded

**4× P2 (Robustness):**
- WavWriter: atomic temp→rename write pattern + bitDepth validation
- ScoreParser: `hasProperty` guards for export defaults
- PluginEditor: harmonic editor layout fix + `SafePointer` for async callbacks

---

## TODO: v0.2 — Polish

### Standalone Listening Test
- Launch standalone, play all 3 engines via on-screen MIDI keyboard
- Verify: each engine produces distinct timbre, effects chain audible, no clicks/pops
- **Specifically test**: Water Gong pitch glide (was broken, now fixed), retrigger clicks, engine switch clicks
- A/B compare with Web Audio prototypes (piano-play)

### DAW Validation
1. Copy VST3 to `C:\Program Files\Common Files\VST3\` (admin)
2. DAW plugin scan → verify detected (Cubase / Reaper)
3. MIDI input → audio output → verify all 3 engines
4. Automation lanes → verify 56 APVTS parameters listed
5. State save/load → verify preset recall across DAW sessions

### Factory Presets v1
- Review and tune 12 factory presets with actual audio output
- A/B compare with Web Audio prototypes
- Consider adding more presets per engine (target: 6 per engine = 18)

### UI / UX Polish
- Preset browser: preview/audition before loading
- Modal distribution visualization
- Keyboard range indicator
- Version number display

---

## TODO: v0.3 — Sonic Identity

### Sample Layer v0
- Single-shot WAV playback layer alongside modal engines
- Use case: attack transients (hammer impact, pick noise) that physical modeling handles poorly
- Implementation: JUCE `AudioFormatReader` + ADSR envelope, triggered alongside engine voice
- One sample slot per engine, velocity-mapped amplitude

### World-Themed Preset Library
- 6 worlds x 6 presets = 36 factory presets (expanding from current 12)
- Worlds: Akasha (空) / Moon (月) / Rabbit (兎) / Gear (歯車) / Water (水) / Ritual (祭)
- Each world uses distinct material/engine combinations for cohesive sonic identity
- Aligned with score examples in `scores/examples/`

---

## TODO: v0.4+ — Backlog

### Planned (v0.4–v0.5)
- CLI batch export pipeline with sound library metadata output
- AI workflow documentation (JSON score → WAV pipeline tutorial)
- Granular mode (stretch/freeze on sample layer)
- Modulation matrix lite (2-4 slots, macro → any param)
- Preset tag search UI (mood/energy/world taxonomy from `tags.json`)

### Nice-to-Have (unscheduled)
- Simple mixer (per-engine volume/pan before FX chain)
- Pattern presets (short sequence patterns bundled with sound)
- Sample import (user WAV for sample layer)
- Built-in WAV export from GUI (not just CLI)
- Theme/skin system
- MIDI Learn

### Not Planned
These overlap with existing tools (Serum, Vital, Kontakt) and are outside TsukiSynth's core direction:
- Wavetable synthesis — not the project's modeling approach
- Full multisample engine — Kontakt/Decent Sampler territory
- Spectral resynthesis — research scope, not product scope
- Full modular routing — complexity vs. semantic parameter philosophy
- Built-in sequencer — DAW responsibility

---

## Product Documentation (v1.0)
- User manual (parameter reference, preset creation guide)
- Sound design guide (material → timbre relationships)
- AI Score Pipeline tutorial
- Build instructions for contributors

### AAX Format (low priority)
- Avid Developer account registration
- AAX SDK download and integration
- Pro Tools validation

---

## Source File Inventory (39 source files + 1 font)

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

data/fonts/IBMPlexSans-SemiBold.ttf   <- brand wordmark font (embedded via BinaryData)
```

## Parameter Name Reference (EN / 中文)

| Parameter | 中文 | Notes |
|-----------|------|-------|
| Material | 材質 | Steel, Brass, Copper, Aluminum, Wood, Glass, etc. |
| Hammer | 槌頭 | Cotton / Felt / Wood / Metal |
| Strike Position | 敲擊位置 | 0.0 (edge) ~ 1.0 (center) |
| Diameter | 弦徑 | String diameter in mm |
| Strings | 弦數 | Strings per course (1–5) |
| Detuning | 離調 | Multi-string beating spread |
| Sub-Engine | 子引擎 | Tongue Drum / Water Gong / Custom |
| Exciter | 激勵器 | Exciter hardness (0–3) |
| Thickness | 厚度 | Plate/beam thickness in mm |
| Size | 尺寸 | Beam length or plate radius in mm |
| Pitch Glide | 音高滑移 | Water Gong immersion effect |
| FM Ratio | FM 比率 | Carrier:modulator frequency ratio |
| Mod Index | 調變指數 | FM modulation depth |
| Brightness | 明亮度 | Overtone/modulation brightness |
| Feedback | 回授 | Modulator self-feedback |

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
