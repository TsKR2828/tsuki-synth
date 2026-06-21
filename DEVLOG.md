# TsukiSynth 開發日誌

---

## 2026-06-17 — Plugin UI 完善：Piano 分頁 + 雙語 Tooltip + 修正

本輪完成三項 TODO 待開發事項 + 兩項 bug 修正，分支 `Codex-fix-bug`。

### Piano 第 4 引擎分頁
- 確認 JUCE 8 APVTS 存 **denormalized** 值（讀 `juce_AudioProcessorValueTreeState.cpp` 源碼：`flushToTree` 寫 `unnormalisedValue`）→ 安全追加 "Piano" 在 index 3。
- `PluginProcessor.cpp`：engine 選項 3→4；processBlock/allNotesOff 路由 eng==3 到 cimbalomSynth；state save/load 加 `engine_index` / `chr_sub_engine_index` 明確 int 備援。
- `PluginEditor.h/cpp`：`tabPiano` 按鈕、`updateEngine` eng==3、`resized()` 四等分 tab、Piano 共用 Cimbalom 控件。
- `Presets.h`：兩個物理鋼琴 preset 移到 engine=3。
- `TsukiLookAndFeel.h`：`Clr::piano (0xff8ba0c4)` 鋼藍色。

### 水鑼預設改為 free-edge（物理正確）
- 水鑼是吊掛的板→自由邊。`ChromaticEngine.h` + `ScoreParser.h` `plateFreeEdge` 預設 `true`。
- `water_gong_clamped.score.json` 加明確 `"plate_free_edge": false`。
- `physics_verify.py` water_gong 測試加明確 `"plate_free_edge": False`。

### 雙語 Tooltip（小白框）
- `UiLocale::tooltip()` → 回傳 `"ENGLISH  /  中文"` 格式。
- `TsukiLookAndFeel.h`：`drawTooltip` 覆寫（暖白圓角框 `#f5f0e8`、深色文字 `#1a1a2e`、CJK 字型 14.4pt）+ `getTooltipBounds`（自動定位、最寬 400px）。
- `PluginEditor.h`：`juce::TooltipWindow tooltipWindow { this, 350 }`（350ms 延遲）。
- `PluginEditor.cpp`：`setupKnob` / `setupCombo` 加 `setTooltip`；tab 按鈕 + preset 按鈕加 `setTooltip`；`refreshLocalizedText` 切語言時更新所有 tooltip。

### Bug 修正
- **標題列 Piano 字幕**：eng==3 掉入 "FM PIANO" → 修正為 "PIANO ENGINE | PHYSICAL MODELING STRING"。
- **參數計數**：eng==3 顯示 7 → 修正為 6（Piano 共用 Cimbalom 6 控件）。

### 文件衛生
- `DEV-LOG.md`（英文舊日誌）內容併入本檔 `DEVLOG.md`，刪除舊檔。
- TODO.md / ROADMAP.md / CONTEXT.md 全部更新至 2026-06-17 狀態。

---

## 2026-06-16 — 物理精確化大改 + 驗證閉環（企劃目標轉向）

**企劃目標確立：聾人 + AI 不靠聽感、靠物理理論精確模擬聲音。** 整段工作圍繞此目標三支柱：**可重現性、物理可驗證性、樂器物理正確性**。分支 `Codex-fix-bug`，本輪疊在 Codex `b5a370d` 上的 commit（已 push）：

### 起點：通盤審查 + Codex 平行修復
- 全 `src/` 審查找出 8 bug（增益不一致 / glide block-size 依賴 / FM 相位精度 / buildCustomModes break / 尾音 strand / MIDI 未夾範圍…），交付 `tests/audit_repro.cpp`（零依賴自我驗證，23 checks）。
- 月月把審查交給 Codex 平行實作 → `b5a370d` + PR #4（我的 audit 修復 + dynamic tail length + 線性 release + 牆面反射物理 + FLAC + API deprecation 修正）。本輪逐行覆核：高品質無 regression。

### `13a98cb` 決定性化（落差 A）+ cimbalom 釘音 + 等 RMS
- **Determinism**：`NoiseGen` 原用 `random_device` → 同 score 每次不同。改決定性種子 + `setSeed()`，各引擎 `midiNote^velocity` 每音重設。**同 score 兩次渲染 SHA256：DIFFERENT → IDENTICAL**。
- **Cimbalom 釘音**：弦剛性 actual f1=target·√(1+B)（A4 +11c）→ 除掉，f0 釘 MIDI（保比例+多弦失諧）。A4 +11.2c→+0.1c。
- **等 RMS 校準**：魔術增益 0.15/0.2/1.0 → 等 RMS（Cim 0.070 / FM 0.100 / Chromatic 每-sub-engine outputGain）。跨引擎 RMS 差 8dB→0.2dB。

### 物理驗證閉環（落差 D）`cdb244a`/`e04f24f`/`3cfcb7c`/`1cd2352`
- `tools/physics_verify.py`：render→FFT→比對物理預測→報 f0 cents + 泛音 %。三模式：預設 partials（功率質心測 f0，對多弦 beating 穩健）、`--levels`（電平）、`--t60`（衰減，用 --dump-modes ground truth）。
- CLI `--dump-modes <score.json>`：印每事件 voiced/MIDI-tuned 模態 JSON（單一真相源）。

### 樂器物理升級 `a733419`/`26e8d74`/`9541d9c`/`b22e394`
- **Q1 水鑼→真 clamped Kirchhoff 板**：膜 Bessel 零點近似 → 真板特徵值 Ω=λ²(Leissa)，f∝Ω。泛音 1:2.54:4.56(膜)→1:2.08:3.41:3.89:5.00(板)。**水鑼音色會變**。
- **Q2 物理 piano 引擎**：score/CLI `"piano"` = StringModel 敲剛性鋼弦 + 鋼琴校準(felt/strike 1/8)；stiff-string stretch=鋼琴拉伸調音。FM Piano 保留為標註非物理合成。
- **plugin 物理鋼琴 presets**：Cimbalom 的 "Grand Piano / Bright Upright (Physical)"（零結構風險，保舊存檔相容）。
- **free-edge 鑼選項**：`plate_free_edge:true` 切自由邊(吊掛真鑼)，預設仍 clamped；A/B 範例 score 已附。
- **docs**（`ece1f9a`）：校正物理標示（水鑼=Bessel/膜近似→現真板、FM=合成非物理、CLI 不套 macro）。

### 驗收
- 全 6 引擎 harness（cimbalom/tongue_drum/water_gong/water_gong_free/fm/piano）**ALL WITHIN TOLERANCE**；CLI + Standalone build exit 0。

### 延後（需月月決策）
- **plugin 第 4 引擎 Piano 分頁**：改 APVTS engine 3→4 有舊 DAW 存檔向後相容風險（正規化值映射）→ 需先確認 APVTS 存 denormalized 才安全 append。物理鋼琴已用 preset + CLI 雙路徑交付。
- free-edge Ω 精確值複查、進階 piano（槌非線性/音板/damper）、plugin 內 FM↔modal 響度由耳朵再平衡。

### 文件衛生
- DEVLOG.md（本檔，中文）與 DEV-LOG.md（英文）並存 → 建議擇一收斂。

---

## 2026-05-31 — Tuner 結構修正

**NSDF Peak Selection 修正** (`src/analyzer/TunerView.h`)：
- NSDF 改為從 lag 2 開始計算，偵測 zero-lag lobe 邊界
- 找到 NSDF 首次 ≤ 0 的交叉點 → searchStart = max(minLag, zeroLagEnd)
- peak 搜尋完全跳過 zero-lag positive lobe，消除假基頻選取
- 移除 octave-down correction：乾淨週期訊號在 2x lag 有幾乎同強 peak，會無條件把頻率砍半

**低頻範圍擴展**：
- `maxLag` 從 `sampleRate/50`（~50 Hz 下限）改為 `sampleRate/20`（~20 Hz）
- 分析量從 `analysisSize/2` 改為 `numSamples * 3/4`
- pullBuffer 4096 → 8192（應對 96k sample rate 每 tick ~4800 samples）
- 44.1k 可測到 ~27 Hz、96k 可測到 ~31 Hz，涵蓋 C1 (32.7 Hz)

**Dry Signal 路由** (`PluginProcessor.h/cpp`, `AnalyzerPanel.h`)：
- 新增 `AudioFIFO analyzerDryFifo { 8192 }` — effectChain 之前推入 mono mix
- AnalyzerPanel 改雙 FIFO 建構：scope/spectrum 用 post-FX，tuner 用 dry
- Tuner 不受 delay/reverb 尾音和 output gain 影響

**Sample Rate 同步** (`PluginEditor.cpp`)：
- Editor timerCallback 每 tick 呼叫 `analyzerPanel.setSampleRate(proc.getSampleRate())`
- Host 切換 44.1k → 48k → 96k 時 tuner/spectrum 自動追蹤

---

## 2026-05-30 — Body Resonance + Preset 分層 + Engine-filtered Preset

**Body Resonance Layer** (`src/dsp/BodyResonance.h` — 新檔)：
- 程序式低頻共鳴：2 個 resonant bandpass (~120 Hz Q=1.8, ~280 Hz Q=1.4)
- LP smoother 500 Hz 壓制 harshness + envelope follower (~5ms attack, ~80ms release)
- `setAmount(float)` 控制混合量（0=off, 1=max），由 `macro_body` APVTS 驅動
- Cimbalom / Chromatic 引擎在 startNote 中初始化，renderNextBlock 中加算

**Raw / Body Preset 分層** (`src/Presets.h`)：
- 既有 12 個 Cimbalom/Chromatic preset 全部加上 `macro_body = 0.0f`（Raw）
- 新增 4 個 Body-enhanced preset：
  - Steel Dulcimer Body (0.75)、Copper Warm Body (0.80)
  - Crystal Tongue Body (0.70)、Bronze Gong Body (0.85)
- 合計 25 個 factory preset（原 21 + 4 Body）

**Engine-filtered Preset List** (`PluginEditor.cpp`)：
- `getPresetEngine()` helper 依 preset params 查 engine 值
- `rebuildPresetCombo()` 只顯示目前引擎 tab 對應的 factory preset
- `presetIdToIndex` vector 做 combo ID → 真實 preset index 對照
- User preset 在所有引擎 view 都顯示（分隔線後方）
- 切換引擎 tab 自動重建 preset list

---

## 2026-05-30 — Tuner View 實作 + 修正

**TunerView 實作** (`src/analyzer/TunerView.h` — 新檔)：
- McLeod NSDF 音高偵測 + parabolic interpolation
- 顯示：音名（大字）+ 頻率 Hz + cent offset（±50¢ 刻度尺）
- AnalyzerPanel 加入 TUNER tab（SCOPE / SPECTRUM / TUNER 三切換）
- 中英文 UI 標籤（「調音器」/「TUNER」）

**初版修正**：
- 八度高 bug（C4→C5）：threshold 0.7→0.93、globalMax 0.3→0.5、RMS 0.005→0.02
- 結尾 B7 bug：RMS 門檻提高至 0.02，低能量訊號直接判定 No signal

---

## 2026-05-30 — FM Piano P0-P2 完成

**P0：最優先修正** (commit `7769f95`)：
- 統一 APVTS default 與 FMParams default
- 補 `score.schema.json` FM 參數
- 補 Vibraphone / Brass factory preset（20 個 → 6 Cim + 6 Chr + 8 FM）
- `fm_brightness` UI 語意改名 "TONE DECAY" / "音色衰減"

**P1：讓 FM Piano 像樂器** (commit `5b024a3`)：
- velocity-to-index 曲線（velIndexScale 0.45~1.25）
- 分開 attackIndex / bodyIndex（per-type atkScales[] + bdyScales[]）
- 依 sound type 切換 body resonance（per-type bodyF1/F2 + bodyD1/D2）

**P2：E.Piano 3-stack 補強** (unstaged)：
- 3 並行 FM 運算子：Body (1:1) + Tine/Bell (14:1) + Shimmer (3:1, +4 cents)
- 輸出 = 60% stacks + 40% original
- 新 "Layered E.Piano" preset + 中文翻譯「層疊電鋼琴」

---

## 2026-05-15 — v0.2.0：Codex Audit + DAW 驗證 + i18n

**Codex 代碼審查 8/8 修正** (commit `0769e5a`)：
- 4× P1（Critical）：score pipeline 修正、engine switch tail-off 修正
- 4× P2（Robustness）：WavWriter atomic write、ScoreParser guard、SafePointer

**DAW 驗證**：VST3 在 Cubase 載入測試通過

**國際化** (`src/UiLocale.h`)：
- 英文 / 繁體中文雙語 UI（標籤、ComboBox items、preset 名稱、按鈕、對話框）
- LanguageToggle 按鈕即時切換
- APVTS parameter ID 完全不受語系影響

**MIDI 鍵盤 Range Indicator**：
- 各引擎 sweet spot 色帶（Cim C2-C7 / Chr C3-C6 / FM C1-C7）

**Standalone 錄音**：
- WAV 錄音功能（REC / STOP 按鈕，存到 Documents/TsukiSynth/Recordings）

---

## 2026-05-08 — Phase 8 完成：出廠預設 + 收尾

**Factory Presets（12 組出廠音色）：**

| # | 名稱 | 引擎 | 特色 |
|---|------|------|------|
| 0 | Steel Hammered Dulcimer | Cimbalom | 經典揚琴音色（Steel + Wood hammer） |
| 1 | Copper Warm Strings | Cimbalom | 溫暖厚實（Copper + Felt hammer） |
| 2 | Glass Wind Chimes | Cimbalom | 風鈴效果（Glass + Metal + 高失諧） |
| 3 | Muted Felt Piano | Cimbalom | 悶棉音色（Cotton hammer + 高擊打位置） |
| 4 | Crystal Tongue Drum | Chromatic | 空靈鼓（Aluminum + Tongue Drum） |
| 5 | Bronze Water Gong | Chromatic | 水鑼（Bronze + pitch glide 0.6） |
| 6 | Wooden Kalimba | Chromatic | 拇指琴（Spruce + Tongue Drum） |
| 7 | Ethereal Steel Bells | Chromatic | 空靈鐘聲（Custom harmonics + Delay） |
| 8 | Acoustic Piano | FM Piano | FM 鋼琴（ratio=1, index=5, bright=0.7） |
| 9 | Electric Rhodes | FM Piano | Rhodes 電鋼琴（ratio=1 + delay） |
| 10 | DX7 Crystal Bell | FM Piano | DX7 水晶鈴（ratio=7, index=8） |
| 11 | Church Organ | FM Piano | 管風琴（ratio=1, feedback=0.5） |

**Preset 系統：**
- `src/Presets.h` — 靜態預設陣列，raw parameter values
- PluginProcessor 實作 `getNumPrograms/setCurrentProgram/getProgramName`
- 使用 `param->convertTo0to1(raw)` + `setValueNotifyingHost()` 正確轉換參數值
- DAW preset browser 相容（VST3 program change）
- PluginEditor 頂部 Preset ComboBox（與 Engine selector 並排）

**目前插件總覽：**
- 3 個合成引擎（Cimbalom / Chromatic / FM Piano）
- 28 個可自動化 APVTS 參數
- 7 個效果參數（Reverb / Delay / Compressor）
- 12 個出廠預設
- VST3 + Standalone 雙格式輸出

---

## 2026-05-08 — Phase 6 完成：效果鏈

**新增效果模組（`src/effects/`）：**
- `SimpleReverb.h` — Freeverb-style Schroeder reverb
  - 8 parallel comb filters with LP damping in feedback loop
  - 4 serial allpass filters for diffusion
  - Stereo spread: R channel delay offset +23 samples
  - Parameters: room size, damping, wet/dry mix
- `StereoDelay.h` — Stereo delay effect
  - 複用 DelayLine module (circular buffer + linear interpolation)
  - One-pole LP filter in feedback path (~4kHz cutoff) for warm repeats
  - R channel 10% longer delay for spatial width
  - Parameters: time (50~2000ms), feedback (0~0.95), mix
- `Compressor.h` — Peak compressor/limiter
  - Linked stereo detection (max of L/R) to prevent image shift
  - Fixed attack 5ms / release 100ms for clean operation
  - Auto makeup gain (compensates for average gain reduction)
  - Parameters: threshold (-40~0 dB), ratio (1~20)
- `EffectChain.h` — Global chain orchestrator
  - Processing order: Compressor → Delay → Reverb
  - Reads APVTS atomic parameters per block
  - Stereo-aware processing (mono fallback supported)

**PluginProcessor 更新：**
- Effect chain integrated in processBlock (after synth engine render)
- 7 new APVTS parameters: fx_reverb_mix, fx_reverb_size, fx_delay_time, fx_delay_feedback, fx_delay_mix, fx_comp_threshold, fx_comp_ratio
- effectChain.prepare() called in prepareToPlay

**PluginEditor 更新：**
- Window height increased to 580px to accommodate effect section
- Bottom section: EFFECTS label + divider, always visible regardless of engine
- 3 rows: Reverb (mix + room), Delay (time + feedback + mix), Compressor (threshold + ratio)

**目前總參數量：** 1 global + 6 cimbalom + 7 chromatic + 7 fm piano + 7 effects = **28 parameters**

---

## 2026-05-08 — Phase 5 完成：FM Piano 引擎

**新增引擎：**
- `src/engines/FMPianoEngine.h` — 2-operator FM 合成
  - 核心公式：output = sin(carrierPhase + I(t) * sin(modulatorPhase + fb*lastMod))
  - Modulator self-feedback：產生更豐富的泛音（organ、brass 音色的關鍵）
  - Index envelope：獨立的指數衰減控制 brightness（與 amplitude ADSR 分離）
  - Velocity 雙重感應：影響 gain（音量）+ modulation index（亮度）
  - Note-dependent brightness：高音符的 index 衰減更快（自然鋼琴行為）
  - 8 種 Sound Type preset 控制 ADSR 形狀：
    - Piano (fast decay, low sustain)
    - E.Piano (medium decay)
    - Vibraphone (long decay, low sustain)
    - Bell (very long decay, no sustain)
    - Organ (instant to full sustain)
    - Pad (full sustain, for long notes)
    - Bass (fast decay)
    - Brass (medium sustain)

**PluginProcessor 更新：**
- 三引擎架構完成：cimbalomSynth + chromaticSynth + fmPianoSynth
- Engine 選擇器擴展為 3 選項（Cimbalom / Chromatic / FM Piano）
- 新增 7 個 FM 參數：fm_type, fm_ratio, fm_index, fm_brightness, fm_feedback, fm_attack, fm_release
- fm_ratio 使用 skewed range (0.4) 讓低 ratio 區間（鋼琴常用的 1.0~2.0）有更高解析度

**PluginEditor 更新：**
- 三引擎面板切換完成
- FM Piano 面板：Type 選擇器 + Ratio/Index、Brightness/Feedback、Attack/Release 三行佈局
- 副標題：「FM Piano Engine | Frequency Modulation Synthesis」

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
