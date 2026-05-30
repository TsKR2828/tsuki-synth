# TsukiSynth 交接文件

> 日期：2026-05-31
> 狀態：全部 unstaged，未 commit
> Build：Standalone ✅ VST3 ✅

---

## 本輪已完成

### 1. Tuner 結構修正 ✅

**NSDF peak selection 修正** (`src/analyzer/TunerView.h`)
- NSDF 從 lag 2 開始計算，找到 zero-lag lobe 的第一個負值交叉點
- `searchStart = max(minLag, zeroLagEnd)` — peak 搜尋完全跳過 zero-lag lobe
- 移除 octave-down correction（乾淨週期訊號在 2x lag 有幾乎同強的 peak，會無條件把頻率砍半）
- 第一個高於 globalMax × 0.93 的 peak → 基頻，再做 parabolic interpolation

**低頻範圍擴展**
- `maxLag` 從 `sampleRate/50`（~50 Hz 下限）改為 `sampleRate/20`（~20 Hz 下限）
- 分析量從 `analysisSize/2` 改為 `numSamples * 3/4`，更充分利用可用數據
- pullBuffer 從 4096 加大到 8192（應對 96k sample rate 每 tick ~4800 samples）
- 頻率接受下限改為 `>= 18 Hz`
- 44.1k: 可測到 ~27 Hz (低於 C1)。96k: ~31 Hz (涵蓋 C1)

**Dry signal 路由** (`PluginProcessor.h/cpp`, `AnalyzerPanel.h`)
- 新增 `AudioFIFO analyzerDryFifo { 8192 }` — 在 effectChain 之前推入 mono mix
- `AnalyzerPanel` 改為雙 FIFO 建構：scope/spectrum 用 post-FX，tuner 用 dry
- Tuner 讀到的是乾淨引擎輸出，不受 delay/reverb 尾音、output gain 影響

**Sample rate 同步** (`PluginEditor.cpp`)
- Editor `timerCallback` 每 tick 呼叫 `analyzerPanel.setSampleRate(proc.getSampleRate())`
- Host 切換 sample rate（44.1k → 48k → 96k）時，tuner/spectrum 自動追蹤

### 2. 前一輪已完成（同一批 unstaged）

- **Body Resonance Layer** — `src/dsp/BodyResonance.h`（新檔），Cimbalom/Chromatic 引擎加入
- **Raw / Body Preset 分層** — 既有 preset 加 `macro_body=0`，新增 4 個 Body-enhanced preset
- **Engine-filtered preset list** — preset ComboBox 依目前引擎 tab 過濾顯示
- **FM Piano 3-stack E.Piano** — Layered E.Piano preset
- **FM Piano velocity/type 調整** — velocity-to-index、attack/body scale split

---

## Unstaged 檔案總覽

```
修改（tracked）：
 M README.md
 M src/PluginEditor.cpp          — 雙 FIFO 建構、sample rate sync、engine-filtered preset
 M src/PluginEditor.h            — presetIdToIndex member
 M src/PluginProcessor.cpp       — dry FIFO push（pre-FX mono mix）
 M src/PluginProcessor.h         — analyzerDryFifo 宣告
 M src/Presets.h                 — Body preset、macro_body=0、getPresetEngine()
 M src/UiLocale.h                — Body preset 中文翻譯
 M src/analyzer/AnalyzerPanel.h  — 雙 FIFO 建構子
 M src/engines/ChromaticEngine.h — BodyResonance 整合
 M src/engines/CimbalomEngine.h  — BodyResonance 整合
 M src/engines/FMPianoEngine.h   — 3-stack、velocity 調整

新增（untracked）：
?? src/analyzer/SpectrumView.h   — FFT 頻譜 view（2K/4K/8K 可切換）
?? src/analyzer/TunerView.h      — NSDF 調音器（本輪主要修正對象）
?? src/dsp/BodyResonance.h       — 程序式低頻共鳴（2 bandpass + LP + envelope）
?? scores/examples/epiano_3stack_test.score.json
```

---

## 調音器目前的 detection 流程

`TunerView.h` `detectPitch()`:

1. 計算 NSDF `2*r(τ)/m(τ)` — lag 從 2 到 `min(sr/20, N*3/4)`
2. 找 zero-lag lobe 結束點（NSDF 首次 ≤ 0）
3. 從 `max(minLag, zeroLagEnd)` 開始收集 positive lobe 的 peak
4. 全域最大值 < 0.5 → 放棄（噪音）
5. 取第一個 ≥ globalMax × 0.93 的 peak → bestLag
6. Parabolic interpolation（`bestLag > 2 && bestLag < maxLag`）
7. 回傳 `sampleRate / refined`

**沒有 octave correction** — 已移除。zero-lag lobe skip 解決了原本的八度高 bug。

---

## 待驗證（下一步）

### 最優先：Standalone 實測調音器

啟動 Standalone，切到 TUNER tab，彈奏以下音符確認：

| 測試音 | 預期 Hz   | 預期音名 |
|--------|-----------|----------|
| A4     | ~440      | A4       |
| A3     | ~220      | A3       |
| A2     | ~110      | A2       |
| C4     | ~261.6    | C4       |
| C5     | ~523.3    | C5       |
| C1     | ~32.7     | C1       |
| 音符結尾 | No signal | —      |

重點確認：
- 不會八度偏移（不會把 A4 顯示成 A3 或 A5）
- 音符結尾不會跳到 B7
- C1 低音在 FM Piano 引擎可偵測
- cent offset 在 ±5¢ 以內為綠色

### 次優先

- DAW 驗證：VST3 複製到 `C:\Program Files (x86)\Common Files\VST3\`，Cubase 載入
- 切換 host sample rate（48k / 96k）確認調音器頻率不漂移
- Body preset 實際試聽

---

## Build 指令

```powershell
# Standalone + VST3
cmake --build build --config Release --target TsukiSynth_Standalone TsukiSynth_VST3

# CLI batch render
cmake --build build --config Release --target TsukiSynthCLI
& build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --batch scores\examples --output exports\wav
```

---

## Git 歷史（最近）

```
5b024a3 feat(fm): P1 — velocity-to-index, attack/body scale split, per-type body resonance
7769f95 fix(fm): P0 — unify defaults, add FM schema params, add Vibraphone/Brass presets
0769e5a feat: v0.2.0 — 18 presets, Codex audit 8/8 fixed, DAW validation
```

本輪所有變更均 unstaged，尚未 commit。
