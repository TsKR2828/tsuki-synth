# TsukiSynth Dev-Log

> 開發日誌 -- 記錄每次 session 的進度、決策與問題

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
