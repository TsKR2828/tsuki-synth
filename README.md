# TsukiSynth — Multi-Engine VST3/AU Plugin

> Physical Modeling / Modal Synthesis 多引擎軟體合成器 — VST3 / AU 插件

## 概述

TsukiSynth 是一款基於 **物理建模（Physical Modeling）** 的多引擎軟體合成器插件。核心引擎使用 Modal Synthesis — 從材質密度、板厚、弦長、擊打位置等物理參數，自動計算振動模態頻率與衰減，產生物理正確的合成音色。

原型源自 [piano-play](https://github.com/TsKR2828/piano-play) 等 Web Audio 實驗，以 C++ / JUCE 重寫為 VST3 與 AU 格式，供 DAW（Cubase、Logic Pro、FL Studio、Reaper 等）直接使用。

## 支援格式

| 格式 | 對應 DAW | 狀態 |
|------|----------|------|
| VST3 | Cubase, FL Studio, Ableton, Reaper, Studio One | 計畫中 |
| AU (Audio Unit) | Logic Pro, GarageBand, MainStage | 計畫中 |
| AAX | Pro Tools | 評估中（需 Avid SDK 審核） |
| Standalone | 獨立執行，無需 DAW | 計畫中 |

## 音色引擎

### Engine 1: FM Piano
- FM 合成鋼琴音色
- 原型來源：`Synth/synth.html`
- 演算法：雙振盪器 FM + ADSR 包絡 + 高頻衰減

### Engine 2: Cimbalom（匈牙利揚琴）— Physical Modeling
- **Modal Synthesis 弦模型** + 多弦 beating + 共鳴弦 + 響板耦合
- 原型來源：`cimbalom.html`
- 演算法：從物理參數（材質密度、弦徑、張力、弦長）計算 N 個振動模態，含剛性修正 (inharmonicity)
- 擊打位置影響各模態振幅分佈
- 特色參數：弦材質（steel/copper/aluminum）、弦直徑、張力、擊打位置、槌頭材質

### Engine 3: Chromatic Synth（色彩合成器）— Physical Modeling
- 三合一引擎：空靈鼓 / 水鑼 / 自訂泛音
- 原型來源：`chromatic-synth.html`
- 演算法：
  - 空靈鼓：**Euler-Bernoulli 梁模型**（非諧波模態由物理公式計算）
  - 水鑼：**Kirchhoff 圓板模型**（Bessel 函數零點計算模態 + 浸水物理 pitch glide）
  - 自訂泛音：使用者可編輯 ratio/amplitude 的手動模式（保留彈性）

### 全域效果鏈
```
[Engine Output] → Compressor → Delay (w/ feedback) → Wall Reflection Sim → Master Gain → Reverb → Output
```

Wall Reflection（牆壁反射模擬）：
- 距離 → 控制 early reflection delay time（聲速 343m/s 往返計算）
- 材質 → LP filter cutoff（玻璃 16kHz → 地毯 300Hz）

## 技術堆疊

| 項目 | 技術 |
|------|------|
| 語言 | C++17 |
| 框架 | JUCE 7.x |
| 建構 | CMake 3.22+ |
| 合成方式 | Modal Synthesis（物理建模）+ FM Synthesis |
| DSP 參考 | DaisySP (MIT)、STK (MIT-like) |
| GUI | JUCE Component（旋鈕/滑桿/引擎切換/模態視覺化） |
| 材質資料 | JSON 格式材質數據庫（density, Young's modulus, Poisson ratio, damping） |
| 平台 | Windows (MSVC), macOS (Clang) |

## 目錄結構（規劃）

```
Synth-VST/
├── README.md                 ← 本文件
├── ROADMAP.md                ← 開發進度報告
├── CMakeLists.txt            ← 頂層 CMake
├── libs/
│   └── JUCE/                 ← JUCE 子模組
├── src/
│   ├── PluginProcessor.h/.cpp    ← 主音頻處理器
│   ├── PluginEditor.h/.cpp       ← GUI 編輯器
│   ├── engines/
│   │   ├── FMPianoEngine.h/.cpp
│   │   ├── CimbalomEngine.h/.cpp  ← 弦物理建模
│   │   └── ChromaticEngine.h/.cpp ← 梁/圓板物理建模
│   ├── dsp/
│   │   ├── Oscillator.h         ← 低階正弦/波表振盪器
│   │   ├── ModalResonator.h     ← 核心：N 模態共振器
│   │   ├── Envelope.h           ← ADSR / exponential decay
│   │   ├── Filter.h             ← Biquad IIR
│   │   ├── Delay.h              ← Feedback delay line
│   │   └── Reverb.h             ← FreeVerb 或 convolution wrapper
│   ├── physics/
│   │   ├── StringModel.h        ← 弦模態頻率計算
│   │   ├── BeamModel.h          ← 梁模態頻率計算 (Euler-Bernoulli)
│   │   ├── PlateModel.h         ← 圓板模態計算 (Bessel zeros)
│   │   └── MaterialDB.h         ← 材質數據庫載入/查詢
│   └── utils/
│       ├── MidiUtils.h
│       └── ParamLayout.h
├── data/
│   └── materials.json           ← 材質物理參數 (density, E, ν, damping)
├── scores/                      ← AI JSON 樂譜 (Phase 10)
│   ├── schema/
│   │   └── score.schema.json    ← JSON Schema 驗證定義
│   └── examples/
│       ├── akashic_bell.score.json
│       ├── rabbit_warning.score.json
│       └── restraint_metal_click.score.json
├── sound_library/               ← 音色庫索引 + 分類法
│   ├── sound_names.json         ← 音色名稱/標籤/世界觀/用途
│   └── tags.json                ← 分類法定義 (category/mood/energy/world)
├── exports/
│   └── wav/                     ← 渲染輸出的 WAV 檔案
├── resources/
│   └── gui/                     ← 圖片/字型資源
├── presets/
│   └── factory/                 ← 出廠預設音色 (.json)
└── builds/
    ├── windows/
    └── macos/
```

## AI JSON Score Pipeline

TsukiSynth 除了作為 VST/AU 插件，也支援 **AI 驅動的音效生成**。

物理建模參數是語義化的（材質、尺寸、敲擊位置），AI 可直接生成 JSON 樂譜：

```bash
# AI 生成 score.json → TsukiSynth 渲染為 WAV
tsukisynth-cli render scores/examples/akashic_bell.score.json

# 批次渲染
tsukisynth-cli --batch scores/examples/*.score.json --output exports/wav/
```

用途：VTuber 音效、角色 UI 音效、短 BGM motif、個人世界觀音色庫。

### score.json 欄位說明

| 區塊 | 必要 | 內容 |
|------|------|------|
| `$schema` | — | 格式版本，固定為 `"TsukiSynth Score v1"` |
| `meta` | ✅ | 素材 ID、名稱、作者、描述、標籤、情緒、用途、世界觀、變體來源 |
| `global` | ✅ | BPM、sample rate、master volume、全域效果 (reverb/delay/wall) |
| `events` | ✅ | 發聲事件陣列 — 每個事件包含 time、duration、engine、note、velocity、params |
| `export` | ✅ | 輸出設定 — filename、format (wav/flac)、bit depth、normalize、tail silence |

`events[].params` 承載引擎專屬的物理參數（material、thickness、radius、strike_position、exciter、damping 等），由物理建模引擎解讀並自動計算模態。

完整 JSON Schema：[`scores/schema/score.schema.json`](scores/schema/score.schema.json)

### 範例：akashic_bell.score.json

`akashic_bell.score.json` 是 TsukiSynth Score v1 的第一個範例，展示 AI 如何描述一個物理建模音效。它包含素材描述（meta）、全域效果（global）、兩個發聲事件（events）與 WAV 匯出設定（export）。同一面青銅板在不同位置被敲擊，激發不同模態組合，產生豐富的泛音層次。

### Sound Naming System

`score.json` 負責聲音生成配方。`sound_names.json` 負責素材命名、分類、用途、情緒與世界觀管理。兩者透過 `meta.id` 關聯。

詳見 [ROADMAP.md](ROADMAP.md) Phase 10。

## 建構指南（待實作後更新）

### 前置需求
- **Windows**: Visual Studio 2022 (Community), CMake 3.22+
- **macOS**: Xcode 14+, CMake 3.22+
- JUCE 7.x（作為 git submodule 引入）

### 編譯步驟
```bash
git clone --recurse-submodules https://github.com/TsKR2828/synth-vst.git
cd synth-vst
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

產出檔案位於：
- Windows: `build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3`
- macOS: `build/TsukiSynth_artefacts/Release/AU/TsukiSynth.component`

## 授權

待定（個人使用 / GPL / 商業授權評估中）

## 相關連結

- Web 版原型：https://github.com/TsKR2828/piano-play
- JUCE 框架：https://juce.com/
- VST3 SDK 說明：https://steinbergmedia.github.io/vst3_dev_portal/
