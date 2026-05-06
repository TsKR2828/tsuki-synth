# TsukiSynth — 接續開發上下文

> 複製本文件內容到新對話視窗，即可無縫接續。

---

## 專案一句話

物理建模（Modal Synthesis）多引擎 VST3/AU 合成器插件 + AI JSON 音效生成器。

## GitHub

https://github.com/TsKR2828/tsuki-synth

## 本機路徑

```
C:\Users\admin\Desktop\Claude\VoiceMusic\tsuki-synth\
```

## 目前進度

**Phase 0 完成** — 規劃文件 + JSON schema + 範例已全部 push 到 main。

下一步是 **Phase 1：環境建置 + JUCE 骨架**。

## 關鍵文件

| 檔案 | 內容 |
|------|------|
| `README.md` | 專案總覽、引擎規格、目錄結構、AI Score Pipeline 說明 |
| `ROADMAP.md` | 10 Phase 開發計畫（含物理建模 MVP 規格、公式、驗收標準、Research References） |
| `data/materials.json` | 9 種材質物理參數（density, youngs_modulus, poisson_ratio, damping） |
| `scores/schema/score.schema.json` | JSON Schema 驗證定義 |
| `scores/examples/*.score.json` | 3 個 AI 生成範例（akashic_bell, rabbit_warning, restraint_metal_click） |
| `sound_library/sound_names.json` | 音色庫索引 |
| `sound_library/tags.json` | 分類法（category/mood/energy/world） |

## 技術架構

- **語言**：C++17
- **框架**：JUCE 7.x
- **建構**：CMake 3.22+
- **DSP 參考**：DaisySP (MIT)、STK (MIT-like)
- **架構參考**：RipplerX (GPL-3, 只讀不抄)
- **平台**：先 Windows (VS2022)，後 macOS

## 引擎列表

| # | 引擎 | 合成方式 | 物理模型 |
|---|------|---------|---------|
| 1 | FM Piano | FM 合成 | — (不做物理建模) |
| 2 | Cimbalom | Modal Synthesis | 1D 弦模型 + inharmonicity + sympathetic |
| 3 | Chromatic: 空靈鼓 | Modal Synthesis | Euler-Bernoulli 梁 |
| 4 | Chromatic: 水鑼 | Modal Synthesis | Kirchhoff 圓板 (Bessel zeros) |
| 5 | Chromatic: 自訂泛音 | 手動加法合成 | — (使用者自填 ratio) |

## 物理建模核心公式（弦 MVP）

```
f(n) = (n/2L) × √(T/μ) × √(1 + B×n²)     // 模態頻率 + 剛性修正
τ(n) = 1 / (α + β×f(n)² + γ×f(n))          // 物理衰減
a(n) = sin(nπ × x_hit/L) × velocity         // 擊打位置激發
output = Σ a(n) × exp(-t/τ(n)) × sin(2πf(n)t)  // DSP
```

## Phase 1 任務（下一步）

| 任務 | 說明 |
|------|------|
| 1.1 | 安裝 Visual Studio 2022 + CMake（使用者操作） |
| 1.2 | 建立 JUCE 專案骨架 CMakeLists.txt |
| 1.3 | PluginProcessor：接收 MIDI → 發正弦波 |
| 1.4 | 確認 VST3 可在 Reaper/Cubase 中載入 |

**交付標準**：在 DAW 中掛載插件、按 MIDI 鍵盤能聽到聲音。

## Phase 10 (AI Score Pipeline) 要點

- `score.json`：AI 直接寫物理參數（材質/尺寸/打法）→ 引擎渲染 → WAV
- Standalone CLI 批次渲染：`tsukisynth-cli --batch scores/*.score.json`
- 用途：VTuber 音效、UI 音效、BGM motif、世界觀素材庫

## 原型來源（Web Audio 版）

| 原型 | 路徑 | GitHub |
|------|------|--------|
| FM Piano + Piano Roll | `C:\Users\admin\Desktop\Claude\Synth\synth.html` | https://github.com/TsKR2828/piano-play |
| Cimbalom 揚琴 | `C:\Users\admin\Downloads\cimbalom.html` | — |
| Chromatic Synth | `C:\Users\admin\Downloads\chromatic-synth (1).html` | — |

## 重要決策

- 授權：建議 MIT（保留商業可能），不碰 GPL 程式碼
- 單一插件 + 引擎切換（非多個獨立 .vst3）
- 先 Windows → 日後加 macOS
- AAX 最低優先
- 不自動 commit，月月自己審完再決定

## 要求 Claude 遵守的規則

1. 改檔案時預設留 unstaged，不自動 commit/push
2. 每次只完成當前批次任務，不自行擴張範圍
3. 不要刪除 legacy prototype
4. 進 Phase 1 後建 branch 開發，不直接改 main
