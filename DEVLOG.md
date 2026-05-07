# TsukiSynth 開發日誌

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
