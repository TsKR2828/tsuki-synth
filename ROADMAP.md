# TsukiSynth 開發進度報告書

> 文件建立日期：2026-05-06
> 最後更新：2026-05-06
> 狀態：Phase 0 — 規劃階段

---

## 一、專案背景

### 起源
2026 年 5 月初，在瀏覽器中以純 JavaScript + Web Audio API 完成了三組合成器原型：

1. **FM Piano**（`Synth/synth.html`）— 11 種合成樂器，含 Piano Roll 編輯器
2. **Cimbalom**（`cimbalom.html`）— 匈牙利揚琴模擬，加法合成 + 多弦共鳴
3. **Chromatic Synth**（`chromatic-synth.html`）— 空靈鼓 / 水鑼 / 自訂泛音三合一

### 動機
音樂相關朋友反饋：合成演算法有特色，但要在實際編曲工作流中使用，必須做成 **VST3 / AU / AAX** 插件格式，才能掛在 DAW 的音軌上被 MIDI 驅動。

### 技術方向演進
初期規劃為直接移植手動泛音比例（additive synthesis）。經研究後決定升級為 **Physical Modeling / Modal Synthesis** 方向 — 用物理方程式計算振動模態，取代手動填寫頻率比例。此方式音色更自然、參數更直覺（材質密度、板厚、擊打位置），且 DSP 成本與原方案相當（底層同為 N 個衰減正弦波）。

### 可行性結論
三個原型全部基於**即時合成**（非 sample-based），DSP 邏輯可以 1:1 翻譯為 C++。不需要錄音素材，編譯體積小（< 10MB），CPU 負擔低。物理建模方向有成熟的開源參考（RipplerX、STK、DaisySP），不需從零推導。

---

## 二、開發階段規劃

### Phase 0：規劃 ✅ 進行中
- [x] 確認技術路線（JUCE + C++17 + CMake）
- [x] 評估三個引擎的移植難度
- [x] 撰寫 README + 本報告
- [x] 研究物理建模方向 + 開源資源盤點
- [ ] 選定專案名稱與 repo（GitHub: `TsKR2828/synth-vst`）
- [ ] 確認開發環境安裝清單

### Phase 1：環境建置 + 骨架
**目標：空殼插件能在 DAW 中載入、接收 MIDI、發出正弦波**

| 任務 | 說明 | 預估 |
|------|------|------|
| 1.1 | 安裝 Visual Studio 2022 + CMake | 0.5 天 |
| 1.2 | 建立 JUCE 專案骨架 (CMakeLists.txt) | 0.5 天 |
| 1.3 | PluginProcessor: 接收 MIDI → 發正弦波 | 1 天 |
| 1.4 | 確認 VST3 可在 Cubase/Reaper 中載入 | 0.5 天 |
| 1.5 | 設定 CI（可選，GitHub Actions） | 1 天 |

**交付標準**：在 DAW 中掛載插件、按 MIDI 鍵盤能聽到聲音。

### Phase 2：低階 DSP 模組 + 材質數據庫
**目標：建立可重用的 DSP 底層元件，以及物理建模所需的材質資料**

| 模組 | 說明 |
|------|------|
| `Oscillator` | 相位累加器 + wavetable（sin/saw/square） |
| `Envelope` | ADSR + exponential decay + per-mode damping |
| `BiquadFilter` | IIR biquad (LP/HP/BP) |
| `DelayLine` | Circular buffer + feedback |
| `NoiseGen` | White/Pink noise generator |
| `LFO` | 低頻振盪器 |
| `ModalResonator` | **核心新增：N 模態共振器**（頻率/衰減/振幅由物理公式驅動） |

**材質數據庫** (`data/materials.json`)：

```json
{
  "steel": {
    "density": 7800,
    "youngs_modulus": 200e9,
    "poisson_ratio": 0.29,
    "damping": { "alpha": 0.5, "beta_air": 1.2e-7, "gamma_radiation": 2e-5 },
    "display_name": "鋼 Steel"
  },
  "copper": {
    "density": 8900,
    "youngs_modulus": 120e9,
    "poisson_ratio": 0.34,
    "damping": { "alpha": 1.2, "beta_air": 1.5e-7, "gamma_radiation": 2.5e-5 },
    "display_name": "銅 Copper"
  },
  "aluminum": {
    "density": 2700,
    "youngs_modulus": 70e9,
    "poisson_ratio": 0.33,
    "damping": { "alpha": 0.3, "beta_air": 0.8e-7, "gamma_radiation": 1.5e-5 },
    "display_name": "鋁 Aluminum"
  },
  "wood_spruce": {
    "density": 450,
    "youngs_modulus": 12e9,
    "poisson_ratio": 0.37,
    "damping": { "alpha": 8.0, "beta_air": 3e-7, "gamma_radiation": 5e-5 },
    "display_name": "雲杉 Spruce"
  },
  "rubber": {
    "density": 1100,
    "youngs_modulus": 0.05e9,
    "poisson_ratio": 0.49,
    "damping": { "alpha": 80.0, "beta_air": 1e-6, "gamma_radiation": 1e-4 },
    "display_name": "橡膠 Rubber"
  }
}
```

欄位說明：
- `density`：kg/m³，影響模態頻率（越重越低）
- `youngs_modulus`：Pa (N/m²)，材質剛性，影響高頻模態分佈
- `poisson_ratio`：無量綱，影響橫向變形與模態耦合
- `damping.alpha`：材質內部阻尼（金屬低、橡��高）
- `damping.beta_air`：空氣黏滯阻尼係數（高頻先衰減）
- `damping.gamma_radiation`：聲輻射損耗

**預估工時**：4-5 天

### Phase 3：Cimbalom 引擎 — Modal Synthesis 方向
**目標：以物理建模取代手寫泛音，作為架構驗證**

選擇 Cimbalom 作為第一個物理建模引擎的原因：
- 弦振動是最簡單的 1D 模態模型（公式直觀）
- 有明確的多物件耦合需求（弦 + 響板）可驗證架構擴展性
- 原型已有完整的參考音色可做 A/B 比對

#### 物理建模 MVP：弦 (String) 模型

**模態頻率計算：**
```
f(n) = (n / 2L) × √(T / μ)

L = 弦長 (m)
T = 張力 (N)
μ = 線密度 = ρ × A = density × π × (d/2)²   (kg/m)
n = 模態序號 1, 2, 3, ...
```

改「材質」→ ρ 變 → μ 變 → 所有 f(n) 正確連動
改「弦徑」→ A 變 → μ 變 → 音高與泛音結構同時改變
改「張力」→ T 變 → 所有 f(n) 等比例升降

**非理想弦修正（inharmonicity）：**
```
f(n)_real = f(n)_ideal × √(1 + B × n²)

B = (π³ × E × d⁴) / (64 × T × L²)   ← 剛性係數
```
這讓高次泛音微微偏高，正是鋼琴/揚琴「不完美諧波」特色的物理來源。

**每模態衰減時間：**
```
τ(n) = 1 / (α + β_air × f(n)² + γ_radiation × f(n))
```
- 高頻模態衰減更快 → 音色隨時間自然變暗（不需手動曲線）

**擊打位置影響模態振幅：**
```
amplitude(n) = sin(n × π × x_hit / L)

x_hit = 擊打位置 (0 ~ L)
```
- 敲正中央 (x=0.5L)：偶數模態消失 → 偏基頻、柔和
- 敲靠端點 (x=0.1L)：所有模態被激發 → 明亮、金屬感

#### Cimbalom 完整架構

```
                    ┌──────────────────┐
  MIDI Note On ───→│  Exciter (槌)     │
                    │  · 硬度 → 噪音頻寬 │
                    │  · 力度 → 初始能量  │
                    └────────┬─────────┘
                             │ force pulse
                    ┌────────▼─────────┐
                    │  String Resonator │ ×N 弦 (微失諧)
                    │  · 材質 → ρ, E    │
                    │  · 弦徑 → μ       │
                    │  · 張力 → T       │
                    │  · 弦長 → L       │
                    │  · 位置 → amp(n)  │
                    │  · 40+ modes      │
                    └────────┬─────────┘
                             │
               ┌─────────────┼─────────────┐
               │             │             │
    ┌──────────▼──┐  ┌───────▼───┐  ┌──────▼──────┐
    │ Sympathetic  │  │ Soundboard │  │ Damper      │
    │ 共鳴弦       │  │ 響板(2D板) │  │ CC#64 控制  │
    │ 八度/五度    │  │ body modes │  │ decay mul   │
    └─────────────┘  └───────────┘  └─────────────┘
               │             │             │
               └─────────────┼─────────────┘
                             ▼
                    [Global FX Chain]
```

#### 使用者介面參數（取代舊版抽象%旋鈕）

| 參數 | 物理意義 | 範圍 | 對音色的影響 |
|------|---------|------|-------------|
| 弦材質 | 選 steel/copper/aluminum | 下拉選單 | 整體音色明暗、衰減速度 |
| 弦直徑 | mm | 0.3 ~ 2.0 | 音高修正、inharmonicity |
| 弦張力 | N | 200 ~ 1500 | 基頻微調 |
| 擊打位置 | 0~1 (比例) | 0.05 ~ 0.95 | 亮/暗/空洞感 |
| 槌硬度 | 材質選擇 | cotton/felt/wood/metal | 噪音瞬態頻寬 |
| 弦數 | 每 course 幾條弦 | 1 ~ 5 | beating 豐厚度 |
| 失諧量 | cent | 0 ~ 15 | chorus 效果 |
| 共鳴弦量 | 0 ~ 100% | — | 環境感 |
| 響板耦合 | 0 ~ 100% | — | 低頻豐厚度 |
| Damper | CC#64 / GUI toggle | on/off | 延音控制 |

**預估工時**：5-6 天

### Phase 4：引擎 — Chromatic Synth（物理建模升級）
**目標：空靈鼓用梁模型、水鑼用圓板模型、自訂泛音保留手動模式**

| 子引擎 | 物理模型 | 模態公式 |
|--------|---------|---------|
| 空靈鼓 Tongue Drum | **Euler-Bernoulli 梁** | f(n) = (β_n²/2πL²) × √(EI/ρA) |
| 水鑼 Water Gong | **圓板 (Kirchhoff)** | f(m,n) ∝ Bessel 零點² / R² × √(D/ρh) |
| 自訂泛音 Custom | 手動模式（保留原設計） | 使用者自填 ratio + amplitude |

空靈鼓的梁模態序列（free-free beam β_n 值）：
```
β_1 = 4.730, β_2 = 7.853, β_3 = 10.996, β_4 = 14.137, β_5 = 17.279
→ ratio: 1.000, 2.757, 5.404, 8.933, 13.345
```
對比原型手寫的 [1, 2, 3, 4.16, 5.43] — 物理建模給出的是正確的非諧波結構。

水鑼的圓板模態（clamped circular plate, Bessel 零點）：
```
j(0,1)=2.405  j(1,1)=3.832  j(2,1)=5.136  j(0,2)=5.520
→ ratio²: 1.000, 2.537, 4.559, 5.267, ...
```

**預估工時**：4-5 天

### Phase 5：引擎 — FM Piano
**目標：移植 FM 合成鋼琴（最複雜的引擎）**

FM Piano 的核心：
```
carrier_freq = fundamental
modulator_freq = fundamental × ratio
output = sin(carrier_freq × t + index × sin(modulator_freq × t))
```

需移植：
- FM 合成核心（carrier + modulator + index envelope）
- 高音域的 brightness 衰減
- Velocity 感應力度曲線
- （可選）synth.html 中其他 10 種音色的部分精選

> 註：FM Piano 不屬於物理建模範疇，維持原始 FM 合成設計。
> 日後可評估是否用 Phase 3 的弦模型做 "Physical Piano" 替代。

**預估工時**：4-5 天

### Phase 6：全域效果鏈
**目標��移植 Reverb、Delay、Wall Reflection**

| 效果 | 實作方式 |
|------|---------|
| Reverb | JUCE 內建 `juce::dsp::Reverb` (Freeverb) 或自寫 Schroeder |
| Delay | DelayLine + feedback + wet/dry mix |
| Wall Reflection | 3-tap delay (距離計算) + LP filter (材質) + send amount |
| Compressor | `juce::dsp::Compressor` |

**預估工時**：2-3 天

### Phase 7：GUI 設計
**目標：製作操作介面**

設計方向：
- 深色木質調（承襲 Cimbalom HTML 的視覺風格）
- 頂部：引擎切換 tabs
- 中部：各引擎專屬參數旋鈕（物理建模引擎顯示物理量而非抽象%）
- 底部：全域效果 + master
- 自訂泛音模式：可拖曳的 harmonic editor
- 物理建模引擎：可視化模態分佈圖（顯示各 partial 的頻率與衰減）

技術選項：
- JUCE 原生 Component（最穩定）
- 或 JUCE + WebView（直接嵌入 HTML UI）— 不推薦，兼容性差

**預估工時**：4-5 天

### Phase 8：預設管理 + 收尾
**目標：出廠預設、preset 存取、最終測試**

- 出廠預設音色（物理建模引擎：預設為常見樂器的物理參數組合）
- Preset save/load（JUCE ValueTree → XML/JSON）
- DAW Automation 對接（所有參數可被 DAW 自動化）
- 多 DAW 測試（Cubase / Reaper / FL Studio / Logic）
- 程式碼文件 + 使用說明

**預估工時**：3 天

### Phase 9（可選）：AAX 格式
- 申請 Avid Developer 帳號
- 下載 AAX SDK
- 額外編譯設定
- Pro Tools 測試

### Phase 10：AI JSON Score Pipeline + Sound Library
**目標：建立 AI 可讀寫的 JSON 樂譜格式，讓 TsukiSynth 可作為獨立素材生成器**

#### 為什麼這是殺手級功能

傳統 VST 的參數是抽象的（cutoff=0.7、resonance=0.4），AI 無法有效推理。
TsukiSynth 的物理建模參數是**語義化的**：

```
AI prompt: "做一個青銅材質的鐘聲，厚 3.5mm、半徑 12cm、用金屬槌敲 1/3 位置"
                ↓ AI 直接輸出 ↓
{
  "engine": "plate",
  "material": "bronze",
  "thickness_mm": 3.5,
  "radius_mm": 120,
  "strike_position": 0.35,
  "exciter": "metal_mallet"
}
```

AI 不需要「理解聲音」— 它只需要理解「材質、尺寸、打法」這些人類語言概念。
物理建模引擎負責把語義轉成正確的聲音。

#### 核心檔案格式

**`score.json`** — 樂譜/音效事件：
```
{
  "meta":   { title, author, tags, mood, use_case },
  "global": { bpm, sample_rate, master_volume, effects },
  "events": [
    {
      "time": 秒,
      "duration": 秒,
      "engine": "string" | "beam" | "plate" | "membrane" | "fm",
      "note": "C5" 或 MIDI number,
      "velocity": 0-1,
      "params": { 物理建模參數（材質、尺寸、位置等）}
    }, ...
  ],
  "export": { filename, format, bit_depth, normalize }
}
```

**`sound_names.json`** — 音色庫索引：
```
{
  "library": [
    {
      "id": "akashic_bell_001",
      "name": "Akashic Bell",
      "name_zh": "阿卡西之鐘",
      "category": "bell",
      "tags": [...],
      "mood": "sacred",
      "use_cases": [...],
      "world": "akashic",
      "score_file": "相對路徑",
      "wav_file": "相對路徑"
    }, ...
  ]
}
```

**`tags.json`** — 分類法定義：
- categories（bell/chime/gong/drum/string/mechanical/ambient/motif）
- moods（sacred/mystical/tense/ominous/playful/calm/epic/melancholic）
- energy levels（very-low ~ very-high）
- use_cases（VTuber/UI/game/BGM 等）
- worlds（自訂世界觀，如 akashic/rabbit/restraint/clockwork）

#### 工作流程

```
                 ┌──────────────┐
                 │  AI (Claude)  │
                 │  "做一個鐘聲"  │
                 └──────┬───────┘
                        │ 生成 JSON
                        ▼
              ┌─────────────────────┐
              │  score.json         │
              │  events + params    │
              └─────────┬───────────┘
                        │ 讀入
                        ▼
              ┌─────────────────────┐
              │  TsukiSynth         │
              │  Standalone Mode    │
              │  物理建模引擎渲染    │
              └─────────┬───────────┘
                        │ 輸出
                        ▼
              ┌─────────────────────┐
              │  exports/wav/       │
              │  akashic_bell_001.wav│
              └─────────┬───────────┘
                        │ 註冊
                        ▼
              ┌─────────────────────┐
              │  sound_names.json   │
              │  音色庫索引更新      │
              └─────────────────────┘
```

**批次模式**：
```bash
tsukisynth-cli --batch scores/examples/*.score.json --output exports/wav/
```
一次渲染整個資料夾的 score 為 WAV。

#### 實作項目

| 任務 | 說明 | 預估 |
|------|------|------|
| 10.1 | JSON schema 定稿 + 驗證器 | 1 天 |
| 10.2 | Standalone CLI 讀取 score.json | 2 天 |
| 10.3 | 離線渲染引擎（reuse 插件 DSP code） | 2 天 |
| 10.4 | WAV 寫出 + normalize + tail padding | 1 天 |
| 10.5 | 批次模式 + sound_names.json 自動更新 | 1 天 |
| 10.6 | 範例 score 庫（10-20 個音效） | 2 天 |

**預估工時**：7-9 天

#### 範例 Score（已建立）

| 檔案 | 說明 | 引擎 | 材質 |
|------|------|------|------|
| `akashic_bell.score.json` | 阿卡西之鐘 — 長殘響場景轉換音 | plate | bronze |
| `rabbit_warning.score.json` | 兔兔警告 — 雙擊短促提示音 | beam | aluminum |
| `restraint_metal_click.score.json` | 拘束扣合 — 金屬衝擊+殘響 | string+plate | steel |

#### JSON Schema 驗證

`scores/schema/score.schema.json` 提供 JSON Schema (draft 2020-12) 定義，可用於：
- AI 生成後自動驗證格式正確性
- IDE 自動補全 + 即時錯誤提示
- CI pipeline 中的 lint 檢查

#### meta 擴充欄位

除基本的 title/author/tags/mood 外，score.json 的 meta 區塊包含以下管理欄位：

| 欄位 | 用途 | 範例 |
|------|------|------|
| `id` | 固定素材 ID，避免只靠 title 辨識 | `"akashic_bell_001"` |
| `category` | 素材功能分類 | `"transition_sfx"` / `"character_ui"` / `"worldview_sfx"` |
| `worldview` | 世界觀歸屬 | `"Akashic Library"` / `"Rabbit"` / `"Restraint"` |
| `variation_of` | 標記是否為某音效的變體 | `"akashic_bell_001"` 或 `null` |

`variation_of` 的用途：AI 可以基於現有音效產生變體（改材質、改力度、改位置），透過此欄位追蹤血統關係。

#### Phase 10 驗收標準

Phase 10 完成時至少達成以下 7 項：

1. ✅ Standalone 模式可讀取一份 `.score.json` 並解析所有欄位
2. ✅ 依照 `events` 的 engine/note/params 呼叫物理建模引擎產生聲音
3. ✅ 正確套用 `global.effects`（reverb/delay/wall）
4. ✅ 依照 `export.filename` 輸出 WAV（支援 16/24/32 bit）
5. ✅ 能批次處理 `scores/examples/` 裡的多份 JSON（`--batch` 模式）
6. ✅ 能讀取 `sound_names.json` 顯示素材名稱、分類與用途
7. ✅ AI 產出的 JSON 可用 `scores/schema/score.schema.json` 驗證格式正確性

---

## 三、時程總覽

```
Phase 0   規劃              ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ← 現在
Phase 1   環境+骨架          ░░░░████░░░░░░░░░░░░░░░░░░░░░░░░░░░░
Phase 2   DSP+材質庫         ░░░░░░░░█████░░░░░░░░░░░░░░░░░░░░░░░
Phase 3   Cimbalom(物理建模)  ░░░░░░░░░░░░░██████░░░░░░░░░░░░░░░░░
Phase 4   Chromatic(物理建模) ░░░░░░░░░░░░░░░░░░█████░░░░░░░░░░░░░
Phase 5   FM Piano           ░░░░░░░░░░░░░░░░░░░░░░█████░░░░░░░░░
Phase 6   效果鏈             ░░░░░░░░░░░░░░░░░░░░░░░░░░████░░░░░░
Phase 7   GUI                ░░░░░░░░░░░░░░░░░░░░░░█████░░░░░░░░░ (並行)
Phase 8   預設+收尾          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░
─── VST 插件完成線 ──────────────────────────────────────────────
Phase 9   AAX(可選)          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░
Phase 10  AI Score Pipeline  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████
```

**Phase 1-8（VST 插件）**：全職 ~4-5 週 / 兼顧 ~7-9 週
**Phase 10（AI Pipeline）**：額外 ~1.5 週
**全部完成**：全職 ~6-7 週 / 兼顧 ~9-11 週

---

## 四、Research References（研究參考資源）

### 核心參考：架構與實作

#### RipplerX ⭐ 最重要
- **repo**: https://github.com/tiagolr/ripplerx
- **授權**: GPL-3.0
- **語言**: C++ / JUCE
- **內容**: 開源物理建模 VST，9 種共振器（String、Beam、Plate、Membrane、Drumhead、Marimba、Open Tube、Close Tube、Squared），雙共振器串/並聯，Material/Tone/Inharmonicity 控制，64 partials per resonator
- **用途**: 架構參考 — 學習 JUCE 物理建模插件如何組織 resonator class、parameter layout、GUI
- **⚠️ 授權風險**: GPL-3 具有傳染性，若 fork 或複製程式碼則整個專案必須 GPL。建議 **只讀不抄** — 研讀設計思路，自行重寫實作。若未來要商業化，不可包含 RipplerX 的程式碼。

#### DaisySP ⭐ DSP 底層首選
- **repo**: https://github.com/electro-smith/DaisySP
- **授權**: MIT ✅（商業友善）
- **語言**: C++
- **內容**: 模組化 DSP 函式庫，包含 Modal Resonator、Karplus-Strong、String Voice、基礎濾波器/包絡/振盪器
- **用途**: 可直接引用或參考其 ModalVoice class 作為我們 ModalResonator 的基礎
- **優點**: MIT 授權無限制、程式碼乾淨、嵌入式設計所以 CPU 效率高

#### STK (Synthesis ToolKit in C++)
- **repo**: https://github.com/thestk/stk
- **授權**: MIT-like permissive（部分演算法有 Stanford/Yamaha 專利，需注意）
- **語言**: C++
- **內容**: Stanford CCRMA 經典工具包，Modal Synthesis + Digital Waveguide + FM 全套
- **用途**: 參考 modal bar / tuned bar / waveguide string 的實作邏輯
- **注意**: 某些 waveguide 算法有專利（已過期或即將過期），modal 部分安全

#### Faust physmodels.lib
- **repo**: https://github.com/grame-cncm/faustlibraries
- **授權**: LGPL（函式庫部分）/ GPL-2（STK 衍生部分）
- **語言**: Faust DSP language → 可編譯為 C++
- **內容**: 完整物理建模語法庫 — 弦、管、板、膜、擊槌、弓弦全套
- **用途**: 快速原型驗證 — 用 Faust 寫幾行可以立即聽到模態合成效果，確認公式正確後再自行用 C++ 重寫
- **注意**: 不建議直接 faust2juce 產生最終插件（GUI 客製化困難），但作為「聽覺驗證工具」很有價值

### 補充參考：材質數據

| 來源 | 說明 |
|------|------|
| [vibrationdata.com/damping.pdf](http://www.vibrationdata.com/tutorials_alt/damping.pdf) | 金屬/木材/玻璃/橡膠的阻尼係數表 |
| [MakeItFrom.com](https://www.makeitfrom.com/) | 楊氏模數、密度、泊松比線上查詢 |
| mesh2faust 原始碼 | 內建材質預設值可參考 |
| [MatWeb](https://www.matweb.com/) | 工程材質資料庫（免費查詢有限） |

### Future Research（暫不納入主開發，長期探索）

以下資源屬於進階物理建模，待基礎版本完成後再評估引入：

| 專案 | 說明 | 為何暫緩 |
|------|------|---------|
| **Vega FEM** (BSD-3) | 有限元素分析 → 從 3D 網格計算模態 | 我們先用解析公式，不需要 FEM |
| **mesh2faust** (GPL-2) | 3D mesh → modal synthesis 自動化 | 依賴 FEM pipeline，Phase 3 不需要 |
| **DiffSound** (Academic) | SIGGRAPH 2024，從音頻反推材質參數 | 研究性質，待基礎版穩定後做 "自動調參" |
| **jaxdiffmodal** (Open) | GPU 加速模態模擬，含 Bessel 計算 | Python/JAX，參考數學即可 |
| **Tao Synth** (GPL) | 質點彈簧 2D/3D 模擬 | 計算量大，不適合 VST 即時 |
| **openpbso** (Academic) | Stanford 剛體碰撞音效 | 偏遊戲音效，非樂器合成 |
| **Wayverb** (Open) | 波導網格房間聲學 | 偏空間模擬，非樂器本體 |

---

## 五、Physical Modeling MVP 規格

### 目標
Phase 3 的最小可行物理模型：**先實作「弦」模型一種**，驗證完整流程後再擴展到梁和板。

### 為什麼選弦作為 MVP

| 模型 | 維度 | 公式複雜度 | 說明 |
|------|------|-----------|------|
| **弦 (String)** ⭐ | 1D | 低 | 公式最簡、諧波結構清晰、直接對應揚琴 |
| 梁 (Beam) | 1D | 中 | 非諧波 β_n 值需查表，但仍有解析解 |
| 矩形板 (Plate) | 2D | 中高 | 雙重模態序號 (m,n)，擊打位置是 2D 座標 |
| 圓板/膜 | 2D | 高 | 需要 Bessel 函數零點 |

### MVP 完整流程

```
使用者輸入:
  材質 = "steel"       → 查表得 ρ=7800, E=200e9, damping
  弦直徑 = 0.8mm       → 計算 μ = ρ × π × (0.0004)²
  弦長 = 0.35m         → L
  張力 = 800N          → T
  擊打位置 = 0.3       → x_hit / L
  MIDI note velocity   → 初始能量

內部計算:
  for n = 1 to N_modes (例如 40):
    f(n) = (n/2L) × √(T/μ) × √(1 + B×n²)    // 含剛性修正
    τ(n) = 1 / (α + β×f(n)² + γ×f(n))        // 物理衰減
    a(n) = sin(nπ × x_hit/L) × velocity       // 位置激發

DSP 輸出 (per sample):
  output = Σ a(n) × exp(-t/τ(n)) × sin(2π × f(n) × t + φ(n))
```

### MVP 驗收標準

1. ✅ 改「材質」下拉，音色明顯且自然地改變（鋼→亮、銅→暗厚、鋁→清脆）
2. ✅ 改「擊打位置」，偶數泛音消長可聽辨（0.5 = 悶、0.1 = 亮）
3. ✅ 高音符的泛音數量自動減少（因高頻模態超出人耳範圍被截斷）
4. ✅ 低音符自然有更長的 sustain（物理衰減公式的結果）
5. ✅ 不需要手動填任何 hardcoded ratio — 全由公式產生

---

## 六、風險與決策點

### 需要決定的事

| # | 問題 | 選項 | 建議 |
|---|------|------|------|
| 1 | 插件名稱 | TsukiSynth / MoonSynth / 其他 | 你決定 |
| 2 | 單一插件 or 多個 | 合一（引擎切換）vs 各自獨立 | 建議合一 |
| 3 | 授權模式 | MIT / GPL / dual | 建議 MIT（保留商業可能）|
| 4 | macOS 支援 | 需要 Mac 或 CI cross-compile | Phase 1 先 Windows only |
| 5 | AAX 優先度 | Pro Tools 市佔在下降 | 最後再做，不急 |
| 6 | RipplerX 程式碼使用方式 | fork / 只讀參考 / 不碰 | 建議只讀參考，自行重寫 |

### 技術風險

| 風險 | 影響 | 緩解方式 |
|------|------|---------|
| JUCE 學習曲線 | Phase 1 卡住 | 我提供完整可編譯程式碼 |
| C++ 編譯環境問題 | 建置失敗 | 詳細的 step-by-step 安裝指南 |
| DAW 相容性 | 某些 DAW 載入異常 | 先以 Reaper（免費試用）測試 |
| CPU 效能 | 40 modes × 5 strings × polyphony | voice stealing + mode count cap |
| 物理參數調校 | 計算結果聽起來不對 | 以原型 HTML 版作為 A/B 參照 |
| 授權汙染 | 誤用 GPL 程式碼 | 嚴格隔離：只讀 RipplerX，DSP 層用 MIT 授權的 DaisySP |

---

## 七、環境安裝清單

開始 Phase 1 前需準備：

### Windows（必要）
- [ ] Visual Studio 2022 Community — [下載](https://visualstudio.microsoft.com/)
  - 安裝時勾選「使用 C++ 的桌面開發」workload
- [ ] CMake 3.22+ — [下載](https://cmake.org/download/) 或透過 VS Installer 附帶
- [ ] Git（已有）

### 測試用 DAW（至少一個）
- [ ] Reaper（免費試用無限期）— [下載](https://www.reaper.fm/)
- [ ] 或使用你已有的 DAW（Cubase 等）

### 可選
- [ ] ASIO4ALL（低延遲音頻驅動）
- [ ] 實體 MIDI 鍵盤（或用 DAW 虛擬鍵盤）

---

## 八、原型→物理建模 演算法對照

### Cimbalom：手寫 vs 物理建模

| 面向 | 原型（手寫加法合成） | 新版（Modal Synthesis） |
|------|--------------------|-----------------------|
| 頻率 | hardcoded [1, 2, 3, 4.02, 5.01, 6.98] | f(n) = (n/2L)√(T/μ)√(1+Bn²) |
| 衰減 | `baseDecay × 0.65^(h×0.5)` | τ(n) = 1/(α + β×f² + γ×f) |
| 振幅 | hardcoded array | sin(nπ × x_hit/L) |
| 改材質 | 無法（需手動重調所有參數） | 自動重算全部模態 |
| 改位置 | 無此功能 | 偶數模態增減 → 音色連續變化 |
| 音域適應 | 每個音符相同的 ratio | 高音自動少模態、低音自動多模態 |

### Water Gong：手寫 vs 圓板物理

| 面向 | 原型 | 物理建模（Phase 4） |
|------|------|-------------------|
| 頻率 | [1, 1.87, 2.76, 4.13, 5.52, 6.98] | Bessel zeros² → [1, 2.54, 4.56, 5.27, 7.03, ...] |
| Pitch glide | 手動 exponential ramp | 浸入水中 → 有效質量增加 → 所有模態頻率依物理下降 |
| 材質差異 | metallic % 旋鈕 | 材質選擇直接影響 damping + inharmonicity |

### FM Piano：維持原設計
FM 合成不屬於物理建模範疇，保持 `sin(ωt + I×sin(rωt))` 架構不變。

---

## 九、下一步行動

1. **你**：確認專案名稱、決定是否現在安裝 VS2022
2. **我**：收到確認後開始寫 Phase 1 的 C++ 程式碼骨架
3. 第一個里程碑：在 DAW 裡載入空殼插件聽到正弦波
4. 第二個里程碑：正弦波替換為物理建模弦 → 聽到真實的揚琴泛音結構

---

*本文件將隨開發進度持續更新。*
