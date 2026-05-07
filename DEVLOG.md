# TsukiSynth 開發日誌

---

## 2026-05-08 — Phase 4 完成：Chromatic Synth（三合一物理建模引擎）

**新增物理模型：**
- `src/physics/BeamModel.h` — Euler-Bernoulli 梁振動模型（空靈鼓 Tongue Drum）
  - Free-free beam eigenvalues：β₁=4.730, β₂=7.853, β₃=10.996, β₄=14.137, β₅=17.279
  - 非諧波模態序列（ratio: 1.000, 2.757, 5.404, 8.933, 13.345）→ 空靈鼓特有的「鐘聲感」
  - MIDI note → 舌片長度自動計算（A4=0.12m 基準，L ∝ 1/√f）
- `src/physics/PlateModel.h` — Kirchhoff 圓板振動模型（水鑼 Water Gong）
  - 20 組 Bessel 函數零點 j(m,n)，涵蓋 m=0~8, n=1~4
  - 2D 擊打位置建模：中心敲擊 → 軸對稱模態(m=0)強，邊緣 → 高 m 模態強
  - MIDI note → 圓板半徑自動計算（A4=0.15m 基準，R ∝ 1/√f）

**新增引擎：**
- `src/engines/ChromaticEngine.h` — ChromaticVoice 三合一引擎
  - Sub-engine 0: Tongue Drum（BeamModel 驅動，12 模態）
  - Sub-engine 1: Water Gong（PlateModel 驅動，20 模態）
  - Sub-engine 2: Custom（使用者自填 ratio/amplitude，8 組泛音）
  - Water Gong pitch glide：持續降低模態頻率模擬浸水效果（最大 15% pitch drop）
  - Exciter 噪音脈衝：4 級硬度（Soft/Medium/Hard/Sharp）→ LP 濾波 + 脈衝寬度

**PluginProcessor 重構：**
- 雙引擎架構：`cimbalomSynth` + `chromaticSynth`，各 16 voice
- 新增全域 `engine` 參數（Cimbalom / Chromatic 切換）
- 新增 7 個 Chromatic 參數（chr_sub_engine, chr_material, chr_strike_pos, chr_thickness, chr_size, chr_exciter, chr_pitch_glide）
- processBlock 引擎路由：切換時自動 allNotesOff 防止殘留音符
- prepareToPlay 同時設定兩個 synth 的 sample rate

**PluginEditor 更新：**
- 引擎選擇器 ComboBox（頂部）
- 參數面板動態切換：選 Cimbalom 顯示弦參數，選 Chromatic 顯示梁/板參數
- APVTS Listener 監聽 engine 參數變化 → MessageThread 安全更新 UI
- 副標題隨引擎切換：「Cimbalom Engine | Physical Modeling String」/「Chromatic Engine | Beam / Plate / Custom」

---

## 2026-05-08 — Phase 3 完成：Cimbalom 引擎（物理建模弦）

**核心完成：**
- `src/engines/CimbalomEngine.h` — CimbalomVoice（取代 Phase 1 的 SineVoice）
  - ModalResonator + StringModel 驅動，MIDI note → 物理弦參數 → 40 模態渲染
  - 多弦 beating：每 course 1~5 條弦，可調失諧量（0~15 cents）
  - Exciter 噪音脈衝：槌硬度（cotton/felt/wood/metal）→ LP 濾波頻寬
  - Damper 控制：note off + CC#64 sustain pedal
- PluginProcessor 改用 APVTS（AudioProcessorValueTreeState）
  - 6 個可自動化參數：Material / Strike Position / Diameter / Hammer / Strings / Detuning
  - 支援 preset save/load（ValueTree → XML）
  - MaterialDB 透過 BinaryData 嵌入（不依賴外部 JSON 路徑）
- PluginEditor 改為參數控制介面（ComboBox + Slider + Label）

**Build 修正：**
- CMakeLists 加 `add_compile_options(/utf-8)` 解決 MSVC codepage 950 與 UTF-8 中文註解衝突
- `juce_add_binary_data` 嵌入 `data/materials.json`
- MaterialDB 新增 `loadFromString()` / `loadFromBinary()` 方法
- `getOrderedKeys()` 靜態方法提供固定材質排序（給 AudioParameterChoice 用）

---

## 2026-05-08 — Phase 1 + Phase 2 完成

### Phase 1：環境建置 + 骨架

**環境確認：**
- Visual Studio 2026 Community（`D:\Visual_Studio`，MSVC 14.50.35717）
- CMake 4.3.2（winget 安裝）
- Cubase LE AI Elements 12（測試用 DAW）

**完成項目：**
- JUCE 8 以 git submodule 加入（`libs/JUCE`，shallow clone）
- `CMakeLists.txt` — VST3 + Standalone 雙格式輸出
- `src/PluginProcessor.h/.cpp` — 16 voice polyphonic sine synth（juce::Synthesiser 架構）
- `src/PluginEditor.h/.cpp` — 最小 GUI（深色背景 + 標題）
- CMake generator：`Visual Studio 18 2026`（VS 裝在非標準路徑 D 槽，需指定 generator instance）
- Build 成功：零錯誤，C4819 warnings 為 JUCE 內部 codepage 問題可忽略

**VST3 驗證：**
- 產出 `TsukiSynth.vst3` 複製到 `C:\Program Files\Common Files\VST3\`
- Cubase 成功載入、MIDI 輸入有聲音輸出 ✅

**備註：**
- `%APPDATA%\VST3\` 路徑在使用者的檔案總管中不易找到（AppData 隱藏），最後手動複製到 Program Files
- CI（GitHub Actions）延後，優先推進功能開發

---

### Phase 2：DSP 模組 + 材質數據庫

**DSP 模組（全部 header-only，`src/dsp/`）：**

| 模組 | 重點設計 |
|------|---------|
| `Oscillator.h` | 相位累加器，Sin/Saw/Square/Triangle 四波形 |
| `Envelope.h` | 雙模式：ADSR（FM Piano 用）+ ExpDecay 內部類（Modal 每模態獨立衰減） |
| `BiquadFilter.h` | Audio EQ Cookbook 係數，LP/HP/BP/Notch |
| `DelayLine.h` | 環狀緩衝 + 線性插值 + feedback + pushSample/popSample API |
| `NoiseGen.h` | White（mt19937）+ Pink（Paul Kellet 6 階 IIR 近似） |
| `LFO.h` | 複用 Oscillator，加 depth / unipolar 控制 |
| `ModalResonator.h` | ⭐ 核心：N 模態衰減正弦波渲染，excite/damp API，自動截斷超出人耳範圍的模態 |

**Physics 模組（`src/physics/`）：**

| 模組 | 重點設計 |
|------|---------|
| `MaterialDB.h` | 用 juce::JSON 解析 `data/materials.json`，map 查詢，9 種材質 |
| `StringModel.h` | 弦模態頻率公式（含 inharmonicity 修正）、物理衰減、擊打位置振幅、MIDI→弦長/張力換算 |

**設計決策：**
- 全部 header-only：DSP 函式短小適合 inline，免改 CMake
- ModalResonator 只負責渲染（接收 Mode 列表），物理計算由 StringModel/BeamModel/PlateModel 分離
- ExpDecay 用每 sample 乘法因子（`exp(-6.9/τ/sr)`）而非每 sample 算 exp，效能好

---

## 2026-05-06 — Phase 0 規劃

- 建立 repo `TsKR2828/tsuki-synth`
- 撰寫 README.md + ROADMAP.md（含完整 10 phase 規劃）
- 建立 `data/materials.json`（9 種材質物理參數）
- 建立 AI Score Pipeline 資料格式先行設計：
  - `scores/schema/score.schema.json`（JSON Schema draft 2020-12）
  - `scores/examples/` — 3 個範例 score
  - `sound_library/sound_names.json` + `tags.json`
