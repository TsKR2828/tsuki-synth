# TsukiSynth AI 演奏手冊 — 你現在就能彈

> 讀者：**任何 AI session**（Fable / Opus / Codex / 其他），不需要先前對話的記憶。
> 讀完本文件你就知道：**你可以直接用 JSON 譜曲、改編樂曲、渲染成 WAV，全程不需要 DAW、不需要耳朵。**
>
> 姊妹文件：
> - `docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` — 作曲語法細節（樂句/休止/聲部規範）
> - `ROADMAP_PHYSICS.md` — 開發驗收規則（§1 強制規則適用於你）
>
> 建立：2026-07-16。參數名稱與預設值均核對自 `src/score/ScoreParser.h` 與 `src/engines/`，
> 若與程式碼衝突，**以程式碼為準並回報**。

---

## 0. 能力聲明：這件事已經被做成過，不是實驗

| 成品 | 規模 | 位置 |
|---|---|---|
| Vivaldi《四季》改編 | 4 協奏曲 12 樂章、28,376 事件 | `scores/classical/vivaldi_four_seasons/` |
| Beethoven 月光奏鳴曲改編 | 3 樂章全曲 | `scores/examples/moonlight_sonata_complete.score.json` |
| 《光之驗算》AI 原創組曲 | 4 樂章、308 事件、5,083 模態全數機器驗證 | `scores/originals/ai_radiance/` |
| 範例音效庫 | 43 份短 score（6 世界觀） | `scores/library/` |
| 作曲規範 v2 示範曲 | 全管線驗證綠 + 13/13 音程合規的標準範本 | `scores/originals/rules_v2_demo/`（含 `.report.html`） |

渲染在**相同程式版本、build、平台與浮點執行環境**內是決定性的：同一份 score
重複渲染會得到相同 SHA-256。跨編譯器／CPU 的 bit-exact 尚未建立保證；因此交接時
需一併記錄 commit、CLI 版本、sample rate、bit depth 與 `global.random_seed`。

## 1. 30 秒上手

```powershell
# CLI 不存在才需要 build（本機需先載入 vcvars64）：
#   D:\Visual_Studio\VC\Auxiliary\Build\vcvars64.bat
#   cmake --build build --config Release --target TsukiSynthCLI

# 渲染單首
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe my_piece.score.json --output exports\wav

# 批次（傳目錄，不是萬用字元）
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --batch scores\examples --output exports\wav

# 看某 score 的物理預測（渲染前檢查參數有沒有生效）
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --dump-modes my_piece.score.json
```

最小可渲染 score：

```json
{
  "$schema": "TsukiSynth Score v1",
  "meta": { "title": "Test", "id": "test" },
  "global": { "bpm": 60, "sample_rate": 48000, "master_volume": 0.8,
    "random_seed": 60717,
    "effects": { "reverb": { "decay": 2, "wet": 0 },
                 "delay": { "time_ms": 0, "feedback": 0, "wet": 0 },
                 "distortion": { "type": "overdrive", "drive": 0, "instability": 0, "wet": 0 } } },
  "events": [
    { "time": 0.0, "duration": 2.0, "engine": "piano", "note": "C4", "velocity": 0.8,
      "params": { "material": "steel" } }
  ],
  "export": { "filename": "test", "format": "wav", "bit_depth": 24,
              "normalize": false, "tail_silence_ms": 500 }
}
```

`note` 接受音名（`"C#4"`）或 MIDI 數字（`60`）。`sample_rate` 支援 44100 / 48000 / 88200 / 96000。

## 2. SOP A — 改編既有樂曲

1. **找公共領域來源**：Mutopia Project 或 IMSLP 的 MIDI。記下版本與授權（Mutopia 多為 CC BY-SA，衍生 JSON 要保留 attribution，寫進 `meta.description`）。
2. **轉檔**：`python tools/midi_to_tsukisynth.py`——它會自動處理 tempo map（tick→絕對秒）、90% note-off 補償、換弓/同音反覆斷點、逐聲部 rests 與 phrases。**不要手算這些，工具已經會。**
3. **配器**：為每個 MIDI track 選引擎與物理參數（§4 選擇表 + §7 四季配器先例）。
4. **渲染 + 驗收**（§6）。
5. **歸檔**：古典作品放 `scores/classical/<作品名>/`，每樂章獨立成檔（整套一次渲染會炸記憶體）。

## 3. SOP B — 原創作曲

依 `AI_PHYSICAL_COMPOSITION_GUIDE` §11 的十步流程，核心順序是：

**用途/世界觀 → 樂句與休止骨架 → 聲部 profile → 音高和聲 → 換算絕對秒 → 90% 補償 → rests/phrases → 最後才調物理參數。**

先塞滿音符再想結構 = 前人已踩過的雷（產出短促且不和諧）。骨架先行。

## 4. 引擎選擇表（配器的第一個決定）

| engine 值（別名） | 物理 | 泛音性質 | 適合角色 | 建議音域 |
|---|---|---|---|---|
| `"piano"` | 敲擊剛性鋼弦（驗證域內） | **諧波**+輕微拉伸 | 主旋律、和聲、鋼琴曲改編首選 | A0–C8 |
| `"cimbalom"`（`"string"`） | 敲擊弦+多弦 beating | **諧波**+拉伸 | attack 骨架、旋律記憶、揚琴/撥彈感 | C2–C7 |
| `"fm"` | 2-op FM（**域外**，非物理） | ratio=1 時**諧波** | pad、穩定和聲層、電鋼琴 | C1–C7 |
| `"tongue_drum"`（`"beam"`） | Euler-Bernoulli 固支－自由懸臂梁（可明確選 free-free） | **非諧**（1 : 6.27 : 17.55…） | 空靈點綴、節奏、UI 音 | C3–C6 |
| `"water_gong"`（`"plate"`） | Kirchhoff 圓板，score 預設自由邊 | **非諧** | 低頻地平線、鑼/鐘、氛圍 | C3–C6（低音區慎用密度） |
| `"custom"` | 加法合成（半域內） | 自訂 `ratio_0..7`/`amp_0..7` | 頻譜特效、王冠式亮點 | 依設計 |

**和聲鐵律：非諧引擎（tongue_drum / water_gong）不要堆三和弦。** 它們的泛音不在整數位置，和弦會互相打架——這是物理，不是你寫錯。讓諧波引擎（piano / cimbalom / fm）承擔和聲，非諧引擎擔任色彩、節奏、單音點綴。真實世界的甘美朗和鐘樂也是這樣配器的。

每個引擎的 MIDI 60 **參考協和音程表**已用 Sethares dissonance curve 算好：
`reports/consonance_tables.md`。它用來起草，不取代成品驗收；寫完要用
`python tools/check_piece_consonance.py <score>` 讀取每個 event 的真實
`--dump-modes` 重算（示範曲 13/13 PASS、0 UNVERIFIED）。

## 5. 參數快查（全部核對自 ScoreParser.h）

**通用 params**（modal 引擎）：
`material`（見 `data/materials.json`：steel/bronze/copper/aluminum/glass/bamboo…）、`strike_position`（0–1）、`exciter`、`damping_override`（0–10000，控制衰減快慢，快速反覆的救星）、`detuning_cents`（0–50）、`num_strings`（1–5，弦類）。

**尺寸類**：預設 `frequency_mode: "midi"` 時，`note` 決定 f0，尺寸／材質仍會改變
模態比例、衰減與依模態質量得到的振幅；`frequency_mode: "geometry"` 時則不做 MIDI
對齊，絕對頻率由材料與幾何直接預測。geometry 模式仍保留 `note` 作為事件識別與
激發資料，但不可把它當實際 f0。
`diameter_mm`（弦徑 0.1–50）、`thickness_mm`（0.1–1000）、`radius_mm`（板）、`length_mm` / `width_mm`（梁）、`plate_free_edge`（bool，預設 true=吊掛自由邊）。

梁可用 `beam_boundary: "cantilever"`（預設，固支－自由舌片）或 `"free_free"`
（懸掛自由梁）。所有 modal 引擎可用 `frequency_mode: "midi" | "geometry"`。

**FM params**（沒寫 = 用引擎預設，預設值核對自 `FMPianoEngine.h:42`）：

| 參數 | 範圍 | 預設 | 語意 |
|---|---|---|---|
| `fm_preset` | 0–7 | 0 | Piano/EPiano/Vibraphone/Bell/Organ/Pad/Bass/Brass |
| `fm_ratio` | 0.25–16 | **1.0**（=完整諧波列） | 2.0 會變奇次諧波（空心單簧管感），別誤信「預設 2.0」的舊說法 |
| `fm_index` | 0–25 | 4.5 | 越高越亮、泛音越多 |
| `fm_brightness` | 0–1 | 0.6 | 實為 **TONE DECAY**：越高音色衰減越快 |
| `fm_feedback` | 0–1 | 0.02 | 泛音更雜亂/銅管感 |
| `fm_attack` / `fm_release` | 1–5000 / 10–10000 ms | 5 / 500 | — |

**velocity（0–1）是線性激發力**：×2 = +6.02 dB（機器驗證過的物理律）。在 FM 引擎它同時改音色（越大力越亮）。

**glide 區塊**（事件層級）：`{ "glide": { "from_note": "C4", "duration_ms": 300, "curve": "..." } }`。

**effects**（global 層級）：reverb / delay / distortion / wall——**全部在物理驗證域外**。藝術用可以，驗證渲染時 wet 全設 0。

## 6. 驗收 SOP — 不用耳朵的品管

你**不得**用「聽起來不錯」交差（你沒有耳朵，月月的耳朵也不參與驗收）。標準流程：

1. **整曲驗收（主工具）**：
   ```powershell
   python tools/verify_score.py <score.json>        # 單曲：schema/模態/休止 RMS/峰值/決定性，exit 0 = 過
   python tools/verify_score.py --all               # 全 corpus 回歸；數量以當次輸出為準
   python tools/verify_score.py --html <score.json> # 視覺驗證報告（頻譜圖/f0 對照/響度/樂句）
   ```
   合格範本：`scores/originals/rules_v2_demo/rules_v2_demo_001.report.html`。
2. **和聲合規**：`python tools/check_piece_consonance.py <score.json>`（逐事件重算；
   `reports/consonance_tables.md` 只是固定 probe 的設計參考）。FM／Custom 會明列
   `UNVERIFIED-DOMAIN`；checker 不推算宣告 duration 之後的共鳴尾巴。
3. **參數生效檢查**：CLI `--dump-modes` 看每事件模態。嚴格 parser 會拒絕未知 key、
   不屬於該 engine 的參數、假 `membrane` engine 與無效 enum；dump-modes 再確認合法
   參數真的改變了預期模態。
4. **parser error 是整份 score 失敗**：不再以跳過壞事件的方式輸出不完整作品。
5. **響度**：`tools/loudness.py`（BS.1770-4 LUFS）；velocity→dB 對照表見作曲指南 §4.6。
6. **物理改動**（如果你動了 `src/`）：先跑 `python tools/physics_verify.py --selftest`，
   再跑 `python tools/physics_verify.py --full` 與 CTest。判讀必須是「checked 項目無
   FAIL」；低於量測解析度者要誠實列為 `UNVERIFIED/N/A`，不能叫做全綠或 PASS。

已知豁免機制：`scores/verify_exemptions.json`（如 moonlight 的殘響尾巴屬藝術意圖豁免）——新增豁免需月月批准，不得自行加。驗收清單完整版：`AI_PHYSICAL_COMPOSITION_GUIDE` §12。

## 7. 演奏心得（前人的成功與踩雷，含本專案實際數據）

**改編鋼琴曲：優先用 `"piano"` 引擎**（驗證域內、真實非諧拉伸）。月光目前是 FM 版（歷史原因——當時物理 piano 還不存在），FM 版可留作「TsukiSynth 色彩版」。

**月光的 FM 配方**（三樂章對比，可直接借用）：慢而柔的樂章 → index 低（3.9）、brightness 低（0.30）、release 長（950ms）；快而亮的樂章 → index 高（5.6）、brightness 高（0.62）、release 短（150ms）。原理：快速樂段用長殘響會糊成一團。

**四季的五聲部弦配器**（假管弦樂的成功先例——用同一引擎、遞增的物理參數做出聲部層次）：

| 聲部 | diameter_mm | strike_position | damping_override |
|---|---:|---:|---:|
| 主奏 | 0.55 | 0.18 | 0.34 |
| 第一小提琴 | 0.62 | 0.22 | 0.40 |
| 第二小提琴 | 0.68 | 0.24 | 0.44 |
| 中提琴 | 0.90 | 0.28 | 0.48 |
| 大提琴 | 1.45 | 0.32 | 0.52 |

越低的聲部：弦越粗、敲點越靠中、阻尼越大。`exciter: "bow"` 在本引擎是「柔激發」詮釋，不是連續運弓——所以這是物理弦詮釋版，不是小提琴模仿。

**光之驗算的引擎角色分配**（原創配器的思考框架）：與其問「這像什麼樂器」，問四件事——attack 歸哪個 body？decay 歸哪個 body？哪個阻尼常數定義樂句邊界？音結束後允許哪些非諧模態殘留？該作品的答案：cimbalom 擔任 attack 與旋律記憶、tongue drum 擔任空靈回聲、FM 擔任精確頻譜的 pad、water gong 擔任低頻地平線、custom 擔任頻譜閃光。308 事件配了 **248 個明確休止**——密度比你直覺的低得多，這是它結構清晰的原因。

**通用手感**：
- **衰減 vs 密度**：低音殘響長。在同一音區快速反覆前，確認上一音衰得夠多，否則用 `damping_override` 縮短。渲染後看波形/RMS 曲線判斷，不要猜。**注意：2026-07 材質阻尼物理化之後金屬材質的 T60 大幅變長**（鋼在 MIDI 60 約 27 秒！）——寫鋼材質時 `damping_override` 幾乎是必需品，除非你就是要鐘的效果。時值規則見作曲指南 v2。
- **槌硬度現在是物理量**（半正弦力脈衝接觸時間）：cotton 6ms / felt 2ms /
  wood 0.5ms / metal 0.2ms 是 velocity=0.5 的基準；實際接觸時間依 Hertz 近似
  `velocity^(-1/5)` 調整並限制在基準的 0.8–1.2 倍。越硬／擊速越高通常接觸越短，
  模態振幅由 `|F(2πf_n)|` 決定，可用 `--dump-modes` 驗證。
- **音域分層**：低音區留稀疏（長 T60 會疊），密集音型放中高音區。
- **休止是結構**：不做假的低 velocity 音符當休止；`events` 留空 + `rests` 標註。
- **長低音撐不撐得住**是物理問題：物理引擎的衰減由材質阻尼決定，不能像 FM 用 release 硬拉。渲染後量實際 T60，不夠長就換引擎或改配器。

## 8. 地雷清單（每一條都有人踩過）

1. **時間是絕對秒**。`bpm` 只是人類註記，renderer 不用它排程。從拍換算秒要自己過 tempo map。
2. **90% note-off**：制音發生在 `time + duration × 0.9`。想在 T 秒制音 → `duration = (T - time) / 0.9`。
3. **參數名拼錯或放錯 engine = parser 拒絕**。修正後再用 `--dump-modes` 確認生效。
4. **預設值查程式碼，不要腦補**。實例：曾有 AI 斷言 fm_ratio 預設 2.0 並據此分析泛音結構——實際是 1.0（`FMPianoEngine.h:43`），而且這個幻覺被 `physics_verify.py` 的偶次諧波檢查直接證偽。你對程式行為的任何主張都應該可以指到檔案行號。
5. **非諧引擎堆和弦**（見 §4 鐵律）。
6. **驗證渲染 FX 全關**；有 reverb 的版本是藝術品不是物理證據。
7. **授權**：改編公共領域作品也要保留來源版本的 attribution（CC BY-SA 的傳染性）。
8. **不 commit、不 push**，檔案留 unstaged 給月月審（全 repo 通則）。
9. 對外/對月月回報成果時：引用數字（事件數、峰值、f0 偏差、休止數），**禁止用聽感形容詞當結論**。你可以描述設計意圖（「第三樂章配亮是為了速度感」），但不能用「聽起來很好」驗收。
