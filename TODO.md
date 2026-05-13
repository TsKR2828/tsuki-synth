# TsukiSynth — TODO

> Last updated: 2026-05-13
> Branch: `feature/ui-enhancements`

---

## Current Status

| Item | Status |
|------|--------|
| VST3 build | ✅ Passed (zero warnings) |
| Standalone build | ✅ Passed (zero warnings) |
| Standalone launch | ✅ Smoke test OK |
| CLI build | ✅ Fixed (standalone voice API + juce_dsp) |
| CLI batch render | ✅ 4/4 scores rendered |
| Cimbalom hammer DSP | ✅ Hammer spectral shaping |
| Cimbalom material DSP | ✅ Material spectral tilt + exciter brightness/duration |
| Spectrum Analyzer | ✅ FFT SpectrumView + SCOPE/SPECTRUM toggle |
| Preset Browser | ✅ Visual popup + category filter (All/Cimbalom/Chromatic/FM/User) |
| Harmonic Editor | ✅ 8-partial ratio/amplitude editor (16 new APVTS params) |
| Responsive UI | ✅ Resizable 420x700 ~ 900x1200 |
| Standalone 聽感驗收 | ⏳ Hammer/material 改善後待二次驗收 |
| DAW validation | ⏳ Pending (no DAW on current machine) |

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
- [ ] Automation: verify 56 APVTS parameters visible in DAW lanes
- [ ] Automation: verify Output macro is smooth (no clicks on rapid change)
- [ ] State restore: save DAW session, reload, verify all parameters recalled
- [ ] Preset: switch factory presets via DAW program change

## After DAW Validation

### Factory Presets v1
- [ ] Review and tune 12 factory presets with actual audio output
- [ ] A/B compare with Web Audio prototypes

### UI / UX Polish
- [ ] Preset browser: preview/audition before loading
- [ ] Modal distribution visualization
- [ ] Keyboard range indicator
- [ ] Version number display

---

## Known Issues (low priority)

- `dsp/Reverb.h` is legacy, replaced by `effects/SimpleReverb.h` — can be removed when confirmed unused.
- `dsp/EffectsChain.h` is CLI-only, separate from `effects/EffectChain.h` used by plugin.
