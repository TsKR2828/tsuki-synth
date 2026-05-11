# TsukiSynth — TODO

> Last updated: 2026-05-08
> Branch: `phase1/juce-skeleton`
> Tag: `playable-vst3-clean-build-v0`

---

## Current Status

| Item | Status |
|------|--------|
| VST3 build | ✅ Passed (zero warnings) |
| Standalone build | ✅ Passed (zero warnings) |
| Standalone launch | ✅ Smoke test OK |
| Cimbalom hammer DSP | ✅ Hammer spectral shaping (Cotton/Felt/Wood/Metal now shape modal spectrum) |
| Cimbalom material DSP | ✅ Material spectral tilt + exciter brightness/duration |
| Standalone 聽感驗收 | ⏳ Hammer/material 改善後待二次驗收 |
| DAW validation | ⏳ Pending (no DAW on current machine) |
| CLI build | ❌ Known issue (ScoreRenderer API mismatch) |

---

## Next: Standalone 聽感二次驗收

- [ ] Hammer: Cotton vs Felt vs Wood vs Metal 差異是否明顯
- [ ] Material: Steel vs Copper vs Glass vs Spruce vs Rubber 差異是否明顯
- [ ] Spruce vs Maple 是否有可辨識差異

## After: DAW Validation (needs home machine with DAW)

- [ ] Copy VST3 to `C:\Program Files\Common Files\VST3\`
- [ ] DAW scan: load TsukiSynth in Cubase / Reaper
- [ ] MIDI input: play notes via controller or DAW piano roll
- [ ] Audio output: confirm sound from all 3 engines
- [ ] Automation: verify 40 APVTS parameters visible in DAW lanes
- [ ] Automation: verify Output macro is smooth (no clicks on rapid change)
- [ ] State restore: save DAW session, reload, verify all parameters recalled
- [ ] Preset: switch factory presets via DAW program change

## After DAW Validation

### Factory Presets v1
- [ ] Review and tune 12 factory presets with actual audio output
- [ ] A/B compare with Web Audio prototypes

### Preset Browser
- [ ] Visual preset browser in editor (currently ComboBox only)
- [ ] Category filtering (by engine, mood, material)

### Spectrum Analyzer
- [ ] FFT-based spectrum display (AnalyzerPanel has slot for SpectrumView)
- [ ] Switchable Scope / Spectrum views

### UI / UX Polish
- [ ] Responsive resizing (currently fixed 540x850)
- [ ] Harmonic editor for Custom sub-engine
- [ ] Version number display

---

## Known Issues (low priority)

- CLI target (`TsukiSynthCLI`) does not compile — `ScoreRenderer.h` voice API mismatch with JUCE `SynthesiserVoice`. Not blocking plugin usage.
- `dsp/Reverb.h` is legacy, replaced by `effects/SimpleReverb.h` — can be removed when CLI is fixed.
- `dsp/EffectsChain.h` is CLI-only, separate from `effects/EffectChain.h` used by plugin.
