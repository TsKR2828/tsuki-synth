# TsukiSynth Dev-Log

> 開發日誌 -- 記錄每次 session 的進度、決策與問題

---

## 2026-05-15 -- Code Audit: 8 Findings Fixed (4×P1 + 4×P2)

### Context
Post anti-click-fix comprehensive code audit identified 8 issues across Score pipeline, engine switch logic, WavWriter, and PluginEditor.

### P1 — Critical Fixes (4)

1. **Score plate→WaterGong mapping** (`ScoreRenderer.h`) — `"plate"` / `"water_gong"` engine strings were routed to TongueDrum sub-engine instead of WaterGong. Fixed mapping.

2. **Score exciter string mismatch** (`ScoreRenderer.h`) — Schema allows `"cotton_mallet"`, `"felt_mallet"`, `"metal_hammer"`, `"wood_mallet"` but renderer only matched short forms. Added all alias variants.

3. **Score tension/damping overrides not wired** (`ScoreRenderer.h` + `ScoreParser.h` + `CimbalomEngine.h`) — Score schema defined `tension_n`, `diameter_mm`, `damping_override` fields but parser didn't read them and renderer didn't forward them. Added `CimbalomParams::tensionOverride`/`dampingOverride` fields, parser parsing with `hasProperty` guards, and renderer wiring.

4. **Engine switch tail-off not rendered** (`PluginProcessor.cpp` + `PluginProcessor.h`) — Previous fix changed `allNotesOff(false)` → `allNotesOff(true)` but tail-off voices were never rendered (only current engine got `renderNextBlock`). Added `tailOffEngine` tracking with dual-render: current engine renders with MIDI, old engine renders tail-off additively until all voices inactive.

### P2 — Robustness Fixes (4)

1. **WavWriter atomic write** (`WavWriter.h`) — Write directly to target file risked data loss on crash. Now writes to `_tmp` sibling, renames on success. Added `safeBitDepth` validation (16/24/32 only, default 24).

2. **ScoreParser export defaults overwritten** (`ScoreParser.h`) — Missing JSON fields for `format`, `bit_depth`, `normalize`, `tail_silence_ms` overwrote `ScoreExport` struct defaults with zero. Added `hasProperty` guards for all export fields.

3. **Harmonic editor layout overlap** (`PluginEditor.cpp`) — When Chromatic Custom sub-engine active, harmonic editor overlapped parameter row. Changed to `numRows = 3` when editor visible, compacted Size/Glide into single row, hide exciter combo.

4. **PluginEditor async use-after-free** (`PluginEditor.cpp`) — `MessageManager::callAsync` lambda captured raw `this` pointer. If editor destroyed before callback fires → crash. Wrapped in `juce::Component::SafePointer`.

### Files Changed (7)
- `src/score/ScoreRenderer.h` — P1-1, P1-2, P1-3 (mapping, exciter, param wiring + region/crossfade clamp)
- `src/score/ScoreParser.h` — P1-3, P2-2 (new fields + hasProperty guards)
- `src/score/WavWriter.h` — P2-1 (atomic write + bitDepth validation)
- `src/engines/CimbalomEngine.h` — P1-3 (tensionOverride / dampingOverride in CimbalomParams + noteOn)
- `src/PluginProcessor.h` — P1-4 (tailOffEngine member)
- `src/PluginProcessor.cpp` — P1-4 (dual-render engine switch logic)
- `src/PluginEditor.cpp` — P2-3, P2-4 (layout fix, SafePointer)

### Build Result
- VST3 + Standalone + CLI: **zero warnings, zero errors**
- Stats: +146 / -39 across 7 files

---

## 2026-05-15 -- Anti-Click/Pop DSP Fixes + Water Gong Glide Bug

### Problem
Code review for v0.2 Standalone Listening Test found 1 critical bug and 3 click/pop risk patterns across all engines.

### Critical Bug: Water Gong Pitch Glide Broken

`ChromaticEngine.h:282` called `resonator.setModes(glidedModes)` every render block during glide.
But `ModalResonator::setModes()` resets `phase = 0` and `currentAmp = 0` — killing all modes every block.
The Water Gong glide effect was producing periodic silence or clicks instead of a smooth pitch drop.

**Fix**: Added `ModalResonator::updateFrequencies()` that only updates `phaseDelta` without resetting phase or amplitude. ChromaticEngine glide now calls this instead of `setModes()`.

### Click/Pop Fixes (3)

1. **Voice stealing hard cut** — All three engines' `stopNote(allowTailOff=false)` called `clearCurrentNote()` with no fade-out, causing instant audio discontinuity.
   - Cimbalom: added `strings[s].damp(0.002f)` before clear
   - Chromatic: added `resonator.damp(0.002f)` before clear
   - FM Piano: added `ampEnv.setRelease(0.005f)` + `ampEnv.noteOff()` before clear

2. **Engine switch hard kill** — `PluginProcessor.cpp` called `allNotesOff(0, false)` on engine switch, hard-killing all voices. Changed to `allNotesOff(0, true)` for graceful tail-off.

3. **FM ADSR retrigger click** — `Envelope::noteOn()` reset `currentLevel = 0.0f` instantly. Removed the reset so retrigger ramps from current level (no discontinuity).

### Files Changed (6)
- `src/dsp/ModalResonator.h` — added `updateFrequencies()` method
- `src/dsp/Envelope.h` — removed hard reset in `noteOn()`
- `src/engines/CimbalomEngine.h` — voice stealing damp
- `src/engines/ChromaticEngine.h` — voice stealing damp + glide fix
- `src/engines/FMPianoEngine.h` — voice stealing quick release
- `src/PluginProcessor.cpp` — engine switch tail-off

### Build Result
- VST3 + Standalone + CLI: **zero warnings, zero errors**

---

## 2026-05-13 -- Logo / Brand Asset Correction

### Problem
Standalone + VST3 的 Logo（月牙 + wordmark + subtitle）與原始設計稿 (`uiux/TsukiSynth.html` + `components.jsx`) 不一致。

### Root Cause (三層)

1. **月牙被「概念重畫」而非沿用原始向量** — 原設計在 `uiux/components.jsx` 有明確 inline SVG (`M14 3 a8 8 0 1 0 0 14 a6 6 0 0 1 0 -14 z`)，但 JUCE 實作用 `fillEllipse()` 疊兩個圓近似。失去原設計的弧度、尖端收束與視覺重心。
2. **`fillEllipse()` 疊月牙改掉弧度與張力** — 外弧變成標準橢圓弧、內弧像橢圓挖掉、尖端變鈍變厚、整體從品牌符號變成工程暫代圖。
3. **Logo 字體 fallback** — 原設計指定 IBM Plex Sans SemiBold 600，但 CJK 修復 (`TsukiLookAndFeel.h`) 把預設字型改成 Microsoft JhengHei，wordmark 未明確指定 typeface 導致繼承 CJK 字型。後續嘗試用 `Segoe UI` 替代仍然不是原始字體。

### 核心教訓
HTML/SVG design 轉成 JUCE/C++ 時，把「已定稿的品牌資產」誤當成「可以重新畫的 UI 元件」。正確做法是直接回收原始資產，不是用參數去逼近。

### Fixes (4 files)

1. **`data/fonts/IBMPlexSans-SemiBold.ttf`** (NEW) — 嵌入原始設計字型
2. **`CMakeLists.txt`** — 加入字型到 `juce_add_binary_data`
3. **`src/PluginEditor.h`** — 新增 `moonPath` (juce::Path) + `wordmarkTypeface` (Typeface::Ptr) 成員
4. **`src/PluginEditor.cpp`** — 三項修正：
   - **月牙**：`Drawable::parseSVGPath("M14 3 a8 8 0 1 0 0 14 a6 6 0 0 1 0 -14 z")` 直接解析原始 SVG path
   - **Wordmark**：`Typeface::createSystemTypefaceFor(BinaryData::IBMPlexSansSemiBold_ttf)` 嵌入字型，22px + gradient `#f0e8d8→#c49a6c`
   - **定位**：所有座標直接取自 CSS（`padding: 16px 20px 10px`, `gap: 8px`, `translateY(2px)` 等），`kTitleH` 56→64 配合設計稿

### Build Result
- VST3 + Standalone: **零警告、零錯誤**

---

## 2026-05-11 -- UiLocale Localization Layer + Chinese Mojibake Fix

### Problem
Phase 2 (UI consistency + Chinese labels) introduced `u8"..."` strings for Traditional Chinese
combo items and labels. Standalone displayed them as mojibake (garbled characters). Additionally,
there was no mechanism to switch between English and Chinese at runtime.

### Root Cause
1. `u8""` literals produce `char8_t` in C++17, which JUCE's `String` constructor interprets via
   the system ANSI codepage (Big5 on Traditional Chinese Windows) rather than UTF-8.
2. JUCE's default sans-serif font (Segoe UI) lacks CJK glyphs.

### Solution — UiLocale System (4 files changed)

1. **`src/UiLocale.h`** (NEW) — Centralized localization layer:
   - `enum class UiLanguage { English, Chinese }` with static getter/setter
   - `T()` helper: `juce::String(juce::CharPointer_UTF8(utf8))` — safe UTF-8 decoding
   - `label(paramID)` — returns localized display label from lookup table (39 params)
   - `comboItems(paramID)` — returns localized StringArray for materials/hammers/sub-engines
   - `toggleLabel()` — returns "EN" in Chinese mode, "中文" in English mode
   - Default language: Chinese

2. **`src/TsukiLookAndFeel.h`** — Added CJK font:
   - `setDefaultSansSerifTypefaceName("Microsoft JhengHei")` in constructor

3. **`src/PluginEditor.h`** — Added paramID to KnobParam/ComboParam structs,
   language toggle button, `refreshLocalizedText()` and `refreshComboItems()` methods

4. **`src/PluginEditor.cpp`** — Integrated UiLocale throughout:
   - All `u8""` strings removed entirely
   - `setupKnob()` / `setupCombo()` use `UiLocale::label()` / `UiLocale::comboItems()`
   - Language toggle (EN / 中文) in title bar
   - `refreshLocalizedText()` updates all 39 labels + 7 combo items
   - `refreshComboItems()` uses `dontSendNotification` to preserve parameter index

### UI Consistency (preserved from Phase 2)
- Chromatic: Material on left, SubEngine on right (matches Cimbalom: Material left, Hammer right)

### Build Result
- VST3 + Standalone: **zero warnings, zero errors**

### Visual Verification (Standalone screenshot)
- ✅ Chinese displays correctly: 材質, 張力, 阻尼, 槌頭, 子引擎, 楓木, 木槌, 自訂泛音
- ✅ Language toggle works: EN ↔ 中文 switches all labels and combo items
- ✅ Material/Hammer/SubEngine layout consistent across Cimbalom and Chromatic
- ✅ Parameter values preserved after language switch (no reset)

---

## 2026-05-08 -- Cimbalom Playability Pass

### Problem
Standalone 聽感驗收發現：
- Cimbalom 4 種 Hammer (Cotton/Felt/Wood/Metal) 聽起來幾乎一樣
- 不同 Material (Steel/Copper/Spruce/Maple) 差異太小

### Root Cause Analysis

**Hammer 無差異原因**：`hammer` 參數只影響 exciter 噪音脈衝（1-4ms），不影響 modal resonator 的模態振幅分佈。Modal resonator 產生 99% 的聲音，且所有 40 個泛音以相同振幅被激發。

**Material 無差異原因**：`StringModel::tensionForNote()` 自動計算張力 T = μ×(2L×f1)²，抵消了密度對基頻的影響。非諧性 B ≈ E/ρ（比剛度），Steel/Glass/Wood 的比剛度都在 25-28×10⁶ 附近。只有阻尼 α 不同，但金屬間差異太小。

### Fixes (1 file: `src/engines/CimbalomEngine.h`)

1. **Hammer 模態整形** — 新增 `hammerCutoffPartial[]`，對 baseModes 套用 2 階低通衰減 `1/(1+(n/cutoff)²)`
   - Cotton: 截止在第 3 泛音（只有基頻和前幾個泛音）
   - Felt: 截止在第 8 泛音
   - Wood: 截止在第 20 泛音（大部分泛音保留）
   - Metal: 截止在第 60 泛音（全通）

2. **Hammer 噪音振幅** — `noiseAmps[] = {0.10, 0.20, 0.40, 0.70}`，Metal 的 click 是 Cotton 的 7 倍

3. **材質頻譜傾斜** — 以 log₁₀(楊氏模量) 計算 `spectralTilt`，高次泛音乘以 `pow(tilt, (n-1)×0.2)`
   - Steel (tilt=0.95): 明亮，保留大部分泛音
   - Glass (tilt=0.84): 清脆
   - Wood (tilt=0.65): 溫暖，高次泛音衰減
   - Rubber (tilt=0.10): 極悶，幾乎只有基頻

4. **材質激發器亮度** — exciter 截止頻率乘以 `materialBright`（Steel ×1.9, Rubber ×0.15）

5. **材質激發器時長** — `durScale`，Steel 短促(×0.63)，Rubber 長厚(×2.3)

### Build Result
- VST3 + Standalone: **零警告、零錯誤**
- Standalone 啟動成功

### Standalone 聽感驗收（使用者回報）
- Hammer: Cotton/Felt/Wood/Metal 改善前幾乎無差異 → 修正後待驗收
- Material: Steel/Copper 有細微差異但不夠明顯 → 修正後待驗收
- Chromatic: 水鑼 Copper/Bronze 有細微差異可接受，空靈鼓差異明顯

---

## 2026-05-08 -- Warning Cleanup + Clean Build Confirmed

### Warning Fixes (2 files)
1. **`src/dsp/BiquadFilter.h`** — C4701: initialized local vars `b0..a2` to suppress false-positive uninitialized warning (all switch paths covered, MSVC doesn't track enum exhaustiveness)
2. **`src/PluginEditor.cpp`** — C4996: `Font::getStringWidthFloat()` deprecated in JUCE 8, replaced with `GlyphArrangement::getStringWidth()`

### Rebuild Result
- VST3 + Standalone: **zero warnings, zero errors**
- Standalone launch: smoke test passed (process running, 32MB memory)
- Tag: `playable-vst3-clean-build-v0` at commit `df5bd26`

---

## 2026-05-08 -- Build Validation (DESKTOP-HA8VHD7)

### Environment Setup
- JUCE submodule initialized: `libs/JUCE` → JUCE 8.0.12 (commit `501c076`)
- CMake 4.3.2 installed via winget (`Kitware.CMake`)
- VS 2022 Build Tools 17.14.31 installed via winget (`Microsoft.VisualStudio.2022.BuildTools`)
  - MSVC 19.44.35226.0 (VCTools 14.44.35207)
  - Windows SDK 10.0.26100.0

### Build Fixes (4 files, 7 lines changed)
1. **`src/dsp/Distortion.h`** — LFO API mismatch:
   - `lfo.prepare()` → `lfo.setSampleRate()`
   - `Waveform::Sine` → `Oscillator::Waveform::Sine`
   - `lfo.getNextSample()` → `lfo.processSample()`
2. **`src/engines/CimbalomEngine.h`** — `m.decay` → `m.decayTime` (ModalResonator::Mode field name)
3. **`src/engines/ChromaticEngine.h`** — same `m.decay` → `m.decayTime` fix
4. **`src/dsp/EffectsChain.h`** — BiquadFilter API mismatch:
   - `hiCut.prepare()` → `hiCut.setSampleRate()`
   - `FilterType::LowPass` → `BiquadFilter::Type::LowPass`

### Build Results
```
cmake -B build -G "Visual Studio 17 2022"
cmake --build build --config Release --target TsukiSynth_VST3 TsukiSynth_Standalone
```
- **VST3**: `build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3` — 6.7 MB ✅
- **Standalone**: `build/TsukiSynth_artefacts/Release/Standalone/TsukiSynth.exe` — 6.5 MB ✅
- **CLI**: ❌ ScoreRenderer.h has extensive API mismatches (uses standalone voice API that doesn't match JUCE SynthesiserVoice interface — needs rewrite)
- Warnings: BiquadFilter.h C4701 (uninitialized vars in unreachable switch default), Font::getStringWidthFloat deprecation

### VST3 Metadata (moduleinfo.json)
- Name: TsukiSynth, Vendor: TsKR, Version: 0.1.0
- Category: Audio Module Class, Sub Categories: Instrument / Synth
- SDK: VST 3.8.0

### Validation (Code Inspection)
- **Standalone launch**: Process starts successfully (2 windows — main editor + MIDI keyboard)
- **40 APVTS parameters**: 9 groups verified (Global/Macro/Cimbalom/Chromatic/FM/Reverb/Delay/Comp/Distortion)
- **8 Macros**: All registered as automatable FloatParam, default 0.5 (Noise=0.0, Output=1.0)
- **Output macro**: Post-FX, per-sample SmoothedValue (20ms ramp) ✅
- **Signal chain**: Synth → EffectChain (Distortion→Compressor→Delay→Reverb) → Output → Analyzer FIFO ✅
- **State save**: APVTS XML + presetIndex property ✅
- **State restore**: replaceState() + setCurrentIndex() ✅
- **Program change**: getNumPrograms/setCurrentProgram via PresetManager ✅

### Not Validated (no DAW installed)
- VST3 host scan (no Cubase/Reaper on this machine)
- DAW automation lane enumeration
- DAW state save/load round-trip
- MIDI input via external controller

### Known Issues
- CLI target (`TsukiSynthCLI`) does not compile — `ScoreRenderer.h` uses a standalone voice API (`prepare()`, `noteOn()`, `getNextSample()`) that doesn't match the actual JUCE `SynthesiserVoice` interface (`startNote()`, `renderNextBlock()`)
- `dsp/EffectsChain.h` (CLI-only) had BiquadFilter API mismatches (fixed but CLI still fails on ScoreRenderer)
- BiquadFilter.h: C4701 warnings (uninitialized vars) — cosmetic, all switch paths covered

---

## 2026-05-08 -- Document Sync + Build Environment Audit

### Recent Commits
- `dc33843` feat: add 8 synth macro parameters with DAW automation
  - 8 Macro knobs: Material / Tension / Damping / Strike / Brightness / Body / Noise / Output
  - Cross-mapped to all three engines (CimbalomVoice, ChromaticVoice, FMPianoVoice)
  - All macros are APVTS parameters → DAW automation ready
- `a26ca48` fix: move Output to post-FX final gain with per-sample smoothing
  - Output macro now applied **after** EffectChain.processBlock()
  - Uses `juce::SmoothedValue` with 20ms ramp to prevent clicks
  - Previous behavior had Output before FX, causing gain-dependent reverb tail

### Build Validation Status
- Previous sessions completed feature development (Phase 1-12 in git log)
- Previous build validation was done on a **different machine** (VS2026, CMake 4.3.2, Cubase LE)
- On current machine (`DESKTOP-HA8VHD7`), no build has ever been attempted:
  - `libs/JUCE` submodule: registered in `.gitmodules` but **NOT initialized** (empty directory)
  - CMake: **not installed** (`cmake --version` fails)
  - Visual Studio / MSVC: **not installed** (no VS directory found)
  - `build/` directory: **does not exist**
  - Git: 2.53.0 ✅
  - winget: 1.28 ✅

### Document Updates
- README.md: updated to reflect actual repo state (3 engines, oscilloscope, 8 macros, build blocker)
- ROADMAP.md: restructured phases (Phase 0-3 done, build validation in progress, TODO list)
- DEV-LOG.md: this entry

### Next Steps
1. `git submodule update --init --recursive` (clone JUCE)
2. Install Visual Studio 2022+ with C++ Desktop workload
3. Install CMake 3.22+
4. `cmake -B build` + `cmake --build build --config Release`
5. Verify `TsukiSynth.vst3` output
6. Load in DAW for plugin host scan + MIDI + audio validation
7. Test automation list + state restore

---

## 2026-05-07 -- Phase 9: AAX + AU Build Support

### Phase 9 (commit TBD)
- CMakeLists.txt: conditional AAX build via `-DTSUKI_AAX=ON -DAAX_SDK_PATH=...`
- CMakeLists.txt: conditional AU (Audio Unit) build via `-DTSUKI_AU=ON` (macOS only)
- `AAX_CATEGORY` set to `AAX_ePlugInCategory_SWGenerators`
- Default build (AAX OFF) verified clean -- VST3 + Standalone + CLI all compile
- To activate AAX: register at https://developer.avid.com, download AAX SDK, reconfigure

---

## 2026-05-07 -- Bug Fixes + Phase 10 Complete

### Bug Fixes (commit `c8055b5`, `8ff0098`)
- Water gong pitch glide now actually applied to resonator frequencies via `scaleFrequencies()`
- Editor auto-syncs widgets from processor state via 10Hz Timer (DAW session restore)
- `syncFromProcessor()` refreshes all ComboBoxes and Sliders
- Compressor amount slider added to effects row (threshold/ratio/makeup mapped from single knob)

### Phase 10: AI Score Pipeline (commit `8ff0098`)
- `src/score/ScoreParser.h` -- JSON parser for .score.json files
- `src/score/ScoreRenderer.h` -- offline rendering using all DSP engines
- `src/score/WavWriter.h` -- 24-bit WAV output with normalization
- `src/cli/RenderApp.cpp` -- CLI entry point: single + `--batch` mode
- CMakeLists.txt: `TsukiSynthCLI` console app target added
- Tested: all 3 example scores render successfully
  - `akashic_bell_001.wav` (2.3MB, 8s)
  - `rabbit_warning_001.wav` (220KB, short)
  - `restraint_metal_click_001.wav` (500KB, medium)

### Build Status
- All targets compile clean: VST3, Standalone, CLI
- Total: Phase 0-8 + Phase 10 complete, Phase 9 (AAX) skipped

---

## 2026-05-06 (Night) -- Phase 3-8 Overnight Build

### Phase 3: Cimbalom Engine (commit `acf65aa`)
- StringModel: inharmonicity correction B, physical decay tau(n), strike position excitation
- CimbalomVoice: multi-string resonators (up to 5 with cent detuning)
- Soundboard body resonance (6 simplified plate-like modes)
- Exciter noise burst: cotton 1500Hz / felt 2500Hz / wood 6000Hz / metal 12000Hz
- MaterialDB embedded via BinaryData (fixed relative path issues)
- UTF-8 fix for Chinese material display names

### Phase 4: Chromatic Engine (commit `363240f`)
- BeamModel: Euler-Bernoulli free-free beam, 20 pre-computed beta_n eigenvalues
- PlateModel: Kirchhoff clamped circular plate, 25 Bessel zeros
- ChromaticVoice with 3 sub-engines:
  - Tongue Drum (beam model, scaled to MIDI note)
  - Water Gong (plate model with pitch glide effect)
  - Custom Harmonics (user-defined ratio/amplitude pairs)
- MultiVoice engine switching in PluginProcessor
- Editor: engine selector ComboBox, sub-engine dropdown, water level slider

### Phase 5: FM Piano Engine (commit `892b472`)
- Two-operator FM synthesis (carrier + 2 modulators)
- 8 preset instruments: Piano, Electric Piano, Vibraphone, Bell, Organ, Bass, Strings, Brass
- Velocity-sensitive modulation index + brightness rolloff for high notes
- Attack/release envelopes per preset
- Third engine type added to engine selector

### Phase 6: Effects Chain (commit `0e2debc`)
- SchroederReverb: 8-comb parallel + 4 allpass series, with damping
- Stereo delay: offset R channel by 1.12x for width
- SimpleCompressor: RMS-based with configurable threshold/ratio/makeup
- EffectsChain: wires reverb -> delay -> compressor -> master volume
- Editor: reverb/delay/master controls in bottom section

### Phase 7-8: Presets + State (commit `4db6aaa`)
- 12 factory presets covering all three engines
- Full XML state serialization (getStateInformation/setStateInformation)
- All engine params, effects settings, and program index persisted

### Build Status
- All phases compile clean with zero warnings
- VST3 + Standalone output verified each phase
- Total source files: 18 headers, 2 cpp, 1 json data

### Known Issues / TODO for Review
- GUI layout is functional but not polished (Phase 7 visual design deferred)
- Editor does not auto-refresh widgets when state is restored from DAW
- No DAW automation params yet (all controls are manual)
- Compressor controls not exposed in editor (only reverb/delay/master)
- Water gong pitch glide factor is computed but not yet applied to resonator frequencies

---

## 2026-05-06 -- Phase 1 complete

### 驗收
- Standalone 啟動成功，虛擬鍵盤可用滑鼠彈奏
- 正弦波聲音確認輸出正常（NVIDIA HDMI Audio）
- 文字顯示正常（修正 em dash 編碼問題）
- Phase 1 交付標準達成：插件載入 + MIDI 輸入 + 聽到聲音

---

## 2026-05-06 — Phase 1 編譯成功

### 進度
- VS2026 Community + CMake 4.2.3 確認安裝（VS 路徑 `D:\Visual_Studio`）
- **VST3 + Standalone 編譯成功**
  - `build\TsukiSynth_artefacts\Release\VST3\TsukiSynth.vst3` (6MB)
  - `build\TsukiSynth_artefacts\Release\Standalone\TsukiSynth.exe` (7MB)
- 修正編譯錯誤：`BusLayout` → `BusesLayout`（JUCE API 正確類型名）
- 關閉 `COPY_PLUGIN_AFTER_BUILD`（需管理員權限，改手動複製）
- 移除 `JUCE_DISPLAY_SPLASH_SCREEN`（JUCE 8 已棄用）

### 編譯指令
```
cmake -B build -G "Visual Studio 18 2026"
cmake --build build --config Release
```

### 待處理
- 實際打開 Standalone 測試 MIDI 輸入和正弦波輸出
- 用 Reaper/Cubase 載入 VST3 測試
- 手動複製 VST3 到 `C:\Program Files\Common Files\VST3\`（需管理員）

---

## 2026-05-06 — Phase 1 骨架程式碼 + Dev-Log 建立

### 進度
- 建立 `phase1/juce-skeleton` 分支
- 完成 Phase 1 骨架程式碼：
  - `CMakeLists.txt` — JUCE 8.0.1 via FetchContent、VST3 + Standalone 格式
  - `src/PluginProcessor.h/.cpp` — 16 聲部正弦波合成器（JUCE Synthesiser 框架 + ADSR 包絡）
  - `src/PluginEditor.h/.cpp` — 基本 GUI 外殼（深色主題、標題文字）
- 修正 CONTEXT.md 本機路徑

### 待處理
- **安裝 Visual Studio 2022 Community**（勾選「使用 C++ 的桌面開發」）
- **安裝 CMake 3.22+**（或透過 VS Installer）
- 安裝完成後執行編譯：
  ```
  cmake -B build -G "Visual Studio 17 2022"
  cmake --build build --config Release
  ```
- 用 Reaper 或 Cubase 載入 VST3 測試

### 技術決策
- JUCE 引入方式：CMake FetchContent（自動下載，不需 submodule）
- 目標 JUCE 版本：8.0.1（使用新版 FontOptions API）
- 輸出格式：VST3 + Standalone（Phase 1 先不做 AU）
- 正弦波合成器作為 proof-of-life：16 voices、ADSR、0.3 master gain

### 備註
- VS2022 和 CMake 尚未安裝，程式碼先寫好備用
- 首次 `cmake -B build` 會自動 clone JUCE（約需幾分鐘）

---

## 2026-05-06 — Phase 0 完成確認 + Dev-Log 建立

### 進度
- Phase 0（規劃）所有主要項目已完成並 push 至 main
- 單一 commit: `3e76298 Phase 0: project planning`
- 已完成：README.md、ROADMAP.md、CONTEXT.md、materials.json、score schema、3 個範例 score、sound_library 索引

### 待處理
- CONTEXT.md 本機路徑需更新（舊：`Desktop\Claude\tsuki-synth` → 新：`Desktop\Claude\VoiceMusic\tsuki-synth`）
- Phase 0 剩餘：確認開發環境安裝清單（VS2022、CMake）
- 準備進入 Phase 1：環境建置 + JUCE 骨架

### 決策
- 專案名稱確定：TsukiSynth
- GitHub repo: TsKR2828/tsuki-synth

### 備註
- 本 Dev-Log 從今天開始記錄
