# TsukiSynth AI／聾人物理作曲文件

> 版本：2.0（新增 §13–§16，ROADMAP_PHYSICS.md M9）  
> 日期：2026-07-12（§1–§12 原文 2026-06-21，未更動）  
> 適用格式：`TsukiSynth Score v1`

## 1. 核心目的

TsukiSynth 的樂譜不只描述「要聽見什麼」，也描述「什麼物體在什麼時刻，以什麼方式振動」。

這份格式同時服務兩種讀者：

1. **AI 作曲系統**：能從世界觀、音高、時間、材質、激發方式與物理尺寸建立可渲染作品。
2. **聾人／非聽覺工作者**：不必依賴試聽，也能從頻率、事件時間、音符終點、休止、樂句和材質語義判斷作品結構。

因此一份合格的 score JSON 必須同時具備：

- 可被目前 C++ renderer 直接渲染的 `events`
- 可視化音高與頻率
- 明確的 note-on 與預期 note-off
- 不靠猜測的休止與呼吸區間
- 可追溯的物理引擎參數
- 來源、授權與編輯決策

> 目前 39,803 個 events 中約 28% 缺少 performance 區塊。performance 是建議提供的輔助資料，非必填。

## 2. 從現有成品歸納出的作曲語法

專案現有正式音色庫以用途和世界觀先行，再決定樂理與物理參數。

| 用途 | 常見事件設計 |
|---|---|
| UI click | 1 個短事件，約 0.06–0.30 秒，低殘響 |
| notification | 1–3 音，上行常表示確認或亮起 |
| action / impact | 低頻瞬態加高頻共鳴，兩層常錯開 20–50 ms |
| transition | 跨音域序列、長殘響、清楚起點與尾巴 |
| ambient | 低 velocity、稀疏事件、長共鳴與較大空間 |
| loop | 固定拍點骨架，加少量變化避免機械重複 |

世界觀主要由「材質＋音域＋事件密度＋空間」形成：

| 世界 | 核心語彙 |
|---|---|
| Akashic | 青銅、玻璃、純四／純五度、長殘響 |
| Rabbit | 鋁片、木片、高音域、快速跳進 |
| Restraint | 鋼鐵、低音、三全音、短衝擊與失真 |
| Forest | 竹木、柔觸、散落節奏、低力度 |
| Ocean | 尼龍、玻璃、低頻長音、glide |
| Clockwork | 黃銅、規律脈衝、短 delay、重複音 |

## 3. JSON 的兩層真相

### 3.1 聲音層

`events` 是 renderer 的聲音真相。每個事件至少包含：

```json
{
  "time": 0.0,
  "duration": 0.269855,
  "engine": "string",
  "note": "E5",
  "velocity": 0.755,
  "params": {
    "material": "steel",
    "diameter_mm": 0.55,
    "strike_position": 0.18,
    "exciter": "bow",
    "damping_override": 0.34
  }
}
```

### 3.2 可理解層

`performance`、`rests`、`phrases`、`tempo_map` 和 `time_signatures` 是 AI 與非聽覺讀者的結構真相。

```json
{
  "performance": {
    "track": "solo",
    "role": "solo_violin",
    "midi_note": 76,
    "frequency_hz": 659.255,
    "source_duration_sec": 0.26087,
    "intended_release_time": 0.24287,
    "articulation": "detached_bow",
    "articulation_gap_ms": 18.0,
    "phrase_end": false,
    "breath_after_ms": 18.0
  }
}
```

目前 renderer 會忽略這些輔助欄位，但它們讓作品可被分析、審核與視覺化。

> **注意：** performance、rests、phrases 欄位是**可選的非聽覺註解**，渲染器不一定讀取這些欄位（schema 明確標示 "renderer may ignore"）。它們的功能是提供人類/AI 可讀的結構後設資料，但不構成強制驗證契約。

## 4. 音高與物理計算

### 4.1 MIDI 音高到頻率

所有引擎以十二平均律目標頻率為基準：

```text
frequency_hz = 440 × 2 ^ ((midi_note - 69) / 12)
```

例如：

```text
A4 = MIDI 69 = 440.000 Hz
E5 = MIDI 76 = 659.255 Hz
C6 = MIDI 84 = 1046.502 Hz
```

JSON 同時保留 `note`、`midi_note` 與 `frequency_hz`，避免只靠音名或聽覺確認。

### 4.2 String / Cimbalom

字串引擎會依 MIDI 音高自動推導有效弦長與張力。主要可控參數：

- `material`：密度、楊氏係數與基礎阻尼
- `diameter_mm`：弦徑；越粗通常越有重量與非諧性
- `strike_position`：激發位置，改變泛音振幅
- `exciter`：激發硬度
- `damping_override`：模態衰減速度

### 4.3 Beam / Tongue Drum

梁模型適合短促、清脆、非整數泛音的音色：

- 木片、竹片、鋁片通知音
- 節奏型短音
- UI click

主要尺寸為 `length_mm`、`width_mm`、`thickness_mm`。

### 4.4 Plate / Water Gong

圓板模型適合鐘、鑼、深層共鳴和長尾：

- `radius_mm` 越大，物理共鳴體感越深
- `thickness_mm` 影響剛性與泛音分布
- `plate_free_edge` 控制自由邊界或夾持邊界

> **重要：** Modal 引擎會先用物理尺寸計算自然振型頻率，再用 chromatic scaling 將所有 mode 對齊到 MIDI 音高。尺寸主要影響**音色**（泛音比例、衰減速率），而非基頻。Score 的 note 欄位決定實際發聲音高。

### 4.5 FM

FM 適合穩定旋律、鋼琴與 pad。它不是物理模態引擎，但可作為清晰旋律層或校對層。

### 4.6 velocity 數字對照響度 dB 表（ROADMAP_PHYSICS.md M6-6a）

這一節給**聾人讀者**：不必聽，只要看數字就能知道一個音會多大聲。

**物理鏈**：`velocity`（0.0–1.0，score JSON 裡的力度數字）在渲染時被當成「激發力的比例」
直接乘上模態的基礎振幅（`ModalResonator::excite()`：`currentAmp = baseAmp * velocity`，
見 `src/dsp/ModalResonator.h`）。振幅與 velocity 成**線性**關係——不是查表、不是曲線，
乘 2 倍力度，波形振幅就乘 2 倍。

**振幅是線性的，但「響度 dB」是對數的**，換算公式：

```text
ΔdB = 20 × log10( velocity_新 / velocity_舊 )
```

所以只要記住一條規則：**velocity 每乘以 2 倍，響度多 +6.02 dB**（`20×log10(2) = 6.0206`）。
不需要每次都算 log，下面這張表直接查：

| velocity 比例變化 | 響度變化 (dB) |
|---|---|
| ×2.0（例：0.2 → 0.4） | +6.0 dB |
| ×1.5 | +3.5 dB |
| ×1.0（不變） | 0.0 dB |
| ×0.75 | −2.5 dB |
| ×0.5（例：0.8 → 0.4） | −6.0 dB |
| ×0.25 | −12.0 dB |

這條「velocity ×2 = +6 dB」的線性律**不是文件宣稱，是機器驗證過的**：
`tools/physics_verify.py` 的 `--levels`/`--full` 判定（ROADMAP_PHYSICS.md M1-1d）
對每個 modal 引擎實測 velocity 加倍前後的電平差，容差 **+6.0 ± 1.0 dB**，
5 個 modal 引擎（cimbalom / tongue_drum / water_gong / water_gong_free / piano）
全部 PASS（FM 因非物理模態引擎，標註豁免，見 §6 M1-1d GATE 證據）。這是同一份驗證，
M6 不重新定義,只是把它翻成給聾人讀的響度對照表。

**用法**：作曲時若某一聲部聽感（或視覺化響度曲線）覺得太大聲/太小聲，直接照上表換算
`velocity` 數字即可，不需要用耳朵試錯。想知道整曲/逐樂句實際多大聲，見
`verify_score.py` 輸出的 LUFS 與逐樂句 RMS（§12.1）。

## 5. 時間、音符斷點與喘息

### 5.1 時間使用絕對秒數

`global.bpm` 是人類標記；目前 renderer 不會用 BPM 自動推算事件時間。

所以：

```text
event.time     = 真正進音時間（秒）
event.duration = renderer 使用的事件長度（秒）
```

若從 MIDI 或 MusicXML 轉換，必須先通過 tempo map，把 tick／拍轉成秒。

### 5.2 Renderer 的 90% note-off

目前 renderer 在事件長度的 90% 處啟動制音：

```text
renderer_note_off = event.time + event.duration × 0.9
```

若希望制音精確發生在 `intended_release_time`：

```text
event.duration =
    (intended_release_time - event.time) / 0.9
```

《四季》JSON 已套用此補償。這是避免休止被提前或延後吞掉的關鍵。

### 5.3 不建立假的休止音符

休止不是音高事件。正確做法是：

- `events` 中沒有聲音
- `rests` 明確記錄靜默區間
- 前一音的 `performance.breath_after_ms` 告知空隔長度

```json
{
  "track": "solo",
  "role": "solo_violin",
  "time": 12.521739,
  "duration": 0.521739,
  "approx_quarter_beats": 1.0,
  "kind": "rest"
}
```

休止分類：

| kind | 意義 |
|---|---|
| `entrance_rest` | 聲部尚未進入 |
| `breath` | 小於約 350 ms 的換弓／換氣空隔 |
| `rest` | 明確短休止 |
| `long_rest` | 2 秒以上或多小節等待 |

### 5.4 斷奏與換弓

機器可讀 MIDI 常保留音符長度和休止，卻不一定把譜面上的 staccato 轉成較短 note-off。

本專案採用以下物理解釋：

- 原譜已有休止：完全保留，不再縮短
- 音符重疊：視為延續、和弦或聲部交疊
- 相鄰音剛好接觸：加入極短換弓空隔
- 快速同音反覆：加入較明顯的重新激發空隔
- 慢樂章：換弓空隔較長，但長線條不任意截斷

這些空隔不是裝飾資料；它們決定制音器何時作用，也決定物理共鳴會不會把下一句糊掉。

## 6. 樂句

`phrases` 將每個聲部分成可閱讀區域：

```json
{
  "track": "solo",
  "role": "solo_violin",
  "number": 7,
  "start": 32.347826,
  "end": 38.086957,
  "breath_after_ms": 521.739
}
```

聾人編曲者可以直接從這些資料判斷：

- 樂句在哪裡開始與結束
- 哪個聲部正在活動
- 呼吸有多長
- 段落密度是否過高
- 下一個主題是否留出足夠空間

## 7. 聲部映射

《四季》轉譯使用五個物理字串聲部：

| MIDI track | 角色 | 弦徑 | 激發位置 | 阻尼 |
|---|---|---:|---:|---:|
| solo | 主奏小提琴 | 0.55 mm | 0.18 | 0.34 |
| violinone | 第一小提琴 | 0.62 mm | 0.22 | 0.40 |
| violintwo | 第二小提琴 | 0.68 mm | 0.24 | 0.44 |
| viola | 中提琴 | 0.90 mm | 0.28 | 0.48 |
| cello | 大提琴／低音通奏 | 1.45 mm | 0.32 | 0.52 |

所有聲部使用：

```json
{
  "engine": "string",
  "material": "steel",
  "exciter": "bow"
}
```

注意：目前 StringModel 本質上是被激發後衰減的模態弦，不是連續運弓模型。`bow` 在現階段代表柔性激發與延長阻尼設計。因此《四季》是 **TsukiSynth 物理弦詮釋版**，不是聲學小提琴取樣替代品。

## 8. 《四季》來源與授權

作品本身於 1725 年出版，已屬公共領域。本次機器可讀轉譯採用 Mutopia Project 的 Performers' Facsimiles 版本：

- [Spring / La primavera](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=301)
- [Summer / L'estate](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=336)
- [Autumn / L'autunno](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=350)
- [Winter / L'inverno](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=351)
- [IMSLP 四季作品與四首協奏曲索引](https://imslp.org/wiki/Le_quattro_stagioni_(Vivaldi,_Antonio))

Mutopia 排版與 MIDI 採 **Creative Commons Attribution-ShareAlike 3.0**。衍生 JSON 保留相同授權及 attribution。

## 9. 《四季》輸出

共 4 首協奏曲、12 個樂章、28,376 個可渲染事件。

| 季節 | RV | 樂章 |
|---|---|---|
| 春 | RV 269 | Allegro / Largo / Danza pastorale |
| 夏 | RV 315 | Allegro non molto / Adagio–Presto / Presto |
| 秋 | RV 293 | Allegro / Adagio molto / Allegro |
| 冬 | RV 297 | Allegro non molto / Largo / Allegro |

索引：

```text
scores/classical/vivaldi_four_seasons/
└── vivaldi_four_seasons.catalog.json
```

每個樂章獨立成檔，避免一次渲染整套作品造成過高記憶體與 CPU 負擔。

## 10. 轉換工具

```powershell
python tools/midi_to_tsukisynth.py four-seasons `
  --source-dir <Mutopia MIDI 解壓目錄> `
  --output-dir scores/classical/vivaldi_four_seasons
```

工具會：

1. 解析所有聲部 note-on／note-off
2. 依 tempo map 換算絕對秒數
3. 建立 note-off 90% 補償
4. 加入物理換弓與快速同音斷點
5. 計算逐聲部休止
6. 建立樂句與呼吸區間
7. 寫入頻率、MIDI 音高與物理參數
8. 驗證事件排序和預期 release time

## 11. AI 新作的標準流程

1. 定義用途、世界觀、情緒、總長度與聲部數。
2. 決定調性、拍號、速度與樂句長度。
3. 先寫節奏骨架與休止，不要先塞滿音符。
4. 為每個聲部定義 `track_profile`。
5. 產生音高與和聲。
6. 將拍點換算成絕對秒數。
7. 計算每音的 `intended_release_time`。
8. 套用 renderer 90% duration 補償。
9. 產生 `rests` 和 `phrases`。
10. 最後才加入材質、敲擊位置、glide 與效果。

## 12. 驗收清單

- [ ] JSON 可解析
- [ ] `events` 依 `time` 排序
- [ ] 所有音高介於 MIDI 0–127
- [ ] `frequency_hz` 符合十二平均律
- [ ] `time + duration × 0.9` 等於預期 release time
- [ ] 原譜休止沒有被共鳴或錯誤 duration 吞掉
- [ ] 快速同音有可辨識斷點
- [ ] 樂句尾有 `breath_after_ms`
- [ ] 長休止被標成 `long_rest`
- [ ] 每個聲部具有物理參數
- [ ] 來源、授權與編輯決策完整
- [ ] 以 24-bit WAV 渲染並檢查峰值／靜默區間

### 12.1 機器蓋章（M3 強制規則）

以上清單是人工／AI 自我檢查用的提示，**不能取代機器驗證**。任何新作的最後一步，
必須實際執行：

```powershell
python tools/verify_score.py <score.json>
```

只有 **exit code 0** 才算完成。這個工具會實際渲染音訊並機器比對：schema 合法性、
events 排序、MIDI／頻率是否符合平均律、`--dump-modes` 全事件模態掃描（無空集、無
NaN/Inf、頻率範圍、f0 偏差 cents）、休止區間的渲染 RMS 是否真的低於門檻（不是「看
duration 覺得夠長」）、峰值與削波、以及決定性（兩次渲染 SHA256 一致）。這些是本清單
前 12 條「用眼睛/邏輯檢查」無法取代的實測項——尤其是休止有沒有被共鳴吞掉，只有實際
渲染後量測才知道。

若 `verify_score.py` 回報 FAIL，禁止自行放寬工具內的容差常數去讓它變綠；要嘛修
score，要嘛依 `ROADMAP_PHYSICS.md` §1 規則記錄豁免原因、交給月月裁決。

「記錄豁免原因」現在有機器可讀的落地方式：`scores/verify_exemptions.json` 是一份
月月批准過的豁免登記表（檔名 + check 名稱前綴 + 理由），`verify_score.py` 會自動
套用並在報告中印出 `[EXEMPT]`（原始 FAIL 訊息不隱藏，只重分類），最終總結標成
`-> PASS (with N registered exemption(s))` 而不是悄悄變成一般 PASS。新增豁免前仍需
月月核准並附實測理由，不得自行加項。

**響度數字（ROADMAP_PHYSICS.md M6-6c）**：`verify_score.py` 的 console 輸出與
`--html` 報告都會印出整曲 **Integrated LUFS**（ITU-R BS.1770-4，K-weighting + 兩級
gating）與**逐樂句/逐區段 RMS (dBFS)**——這是純資訊行，§6 容差登記表沒有登記 LUFS
容差，所以它**不影響 exit code**，只是把「這一段多大聲」變成可讀數字，不需要耳朵。

---

## 13. 非諧引擎和聲規則（ROADMAP_PHYSICS.md M9-9a）

月月的觀察：AI 自由創作「短暫且不和諧」。§13–§16 是這個觀察的**可測量、可重現**
對策——不靠耳朵，靠 `tools/consonance.py` 算出的 Sethares (1993) dissonance-curve
局部極小值（完整數據見 `reports/consonance_tables.md`，本節只引用結論）。

### 13.1 為什麼非諧引擎不能套用鋼琴和聲直覺

tongue_drum（free-free 梁）與 water_gong（圓板）的泛音比例**不是**整數倍數：

| 引擎 | 前 4 個部分音比例（f_n / f_1） |
|---|---|
| tongue_drum | 1.000 : 2.757 : 5.404 : 8.933 |
| water_gong（clamped） | 1.000 : 2.081 : 3.414 : 3.893 |
| cimbalom（近諧波，僅刻度張力伸張） | 1.000 : 2.001 : 3.004 : 4.009 |

鋼琴和聲的協和規則（三和弦、五度圈）建立在「部分音幾乎整數倍」的前提上——當基頻
音程對齊時，兩個音的泛音會大量重合（同頻或近同頻），刺耳的拍音（beating）才會
減到最低。tongue_drum / water_gong 的部分音不是整數倍，同一個「聽起來和諧」的
音程（例如純五度 700 cents）套用在這兩個引擎上，並不保證泛音對齊——必須**重新
用該引擎自己的部分音頻譜跑一次 dissonance curve**才知道哪個音程是它自己的局部
極小值。這不是猜測，是 `tools/consonance.py` 逐引擎算出來的：

### 13.2 各引擎「12-TET 可達成」的建議音程（局部極小值 ±10 cents 內）

以下只列出**剛好落在半音（100 cents 整數倍）附近、renderer 實際能演奏**的
局部極小值（renderer 只支援 12-TET MIDI 音高，見 §4.1，無法演奏任意 cents）。
完整（含非半音對齊的）局部極小值清單見 `reports/consonance_tables.md` §2。

| 引擎（自身音程） | 可用半音音程 | 對應局部極小值 (cents) | dissonance 值 |
|---|---|---:|---:|
| cimbalom | 純五度 (700c) | 705 | 0.0535 |
| cimbalom | 八度 (1200c) | 1200 | 0.0274（比純五度更低，八度才是 cimbalom 自身最協和的可達成半音音程） |
| cimbalom | 大三度 (400c) | 390（邊界內） | 0.1713（明顯較弱，備用） |
| cimbalom | 增四/減五 (600c) | 590（邊界內） | 0.1037（比大三度更協和，違反鋼琴直覺！） |
| tongue_drum | 純五度 (700c) | 695 | 0.0126 |
| water_gong | 八度 (1200c) | 1200 | 0.0383（water_gong 自身表裡唯一另外落在半音上的局部極小值——其餘 235/570/660/735/860/965/1085 cents 都不對齊任何 12-TET 半音，renderer 無法精確演奏，是這個引擎的一個誠實限制，見 13.2 附註） |
| piano（FM 域外不算，這是 modal piano） | 純五度 (700c) | 705 | 0.0159 |
| piano | 八度 (1200c) | 1200 | 0.0040 |

**明確不建議的音程**（局部極大值，同份報告列出）：所有引擎的**小二度 (100c)
附近**都是各自曲線的最高點之一（cimbalom 附近極大值 0.37、water_gong 附近 0.30、
tongue_drum 附近 0.26），是各引擎自身表裡最不協和的區域之一——非諧引擎的半音
音簇比鋼琴上聽起來更刺耳，不要在同時發聲的和弦裡使用。

**反直覺的重點**：cimbalom 的大三度（400c，dissonance 0.17）比它自己的增四度
（600c，dissonance 0.10）還不協和——這是物理事實（弦的伸張非諧性造成的部分音
偏移），不是筆誤。**要用哪個音程，查表決定，不要套用鋼琴和聲的直覺。**

### 13.3 跨引擎（同時發聲）音程規則

當兩個不同引擎同時發聲，要查**跨引擎表**（`reports/consonance_tables.md` §3），
不是分別查兩個引擎的自身表——因為部分音對齊的方式不一樣。已算出且 renderer
可達成（12-TET 半音）的跨引擎建議音程：

| 引擎 A（低音，固定） | 引擎 B（高音，被移調） | 建議音程 (cents) | dissonance |
|---|---|---:|---:|
| cimbalom | tongue_drum | 700（純五度） | 0.0344 |
| cimbalom | tongue_drum | 1200（八度） | 0.0419 |
| cimbalom | water_gong | 300（小三度，邊界） | 0.1841 |
| cimbalom | water_gong | 1200（八度） | 0.0503 |
| tongue_drum | water_gong | 700（純五度） | 0.0533 |
| tongue_drum | water_gong | 800（小六度） | 0.0221 |
| tongue_drum | water_gong | **1000（小七度）** | **0.0071（三個可達成半音音程裡最協和的一個）** |

最後一行是本份分析最反直覺的發現：**tongue_drum 和 water_gong 同時發聲時，在
「12-TET 可達成」的音程裡，小七度（1000 cents）比純五度、比小六度都更協和**——
比鋼琴直覺會選的純五度（0.0533）低了一個量級。（該跨引擎曲線真正的全域最低點
落在 1160 cents 附近，dissonance≈0.0039，但 1160 不對齊任何 12-TET 半音，
renderer 演奏不出來，所以不列進「可達成」的建議集——見 §13.2 water_gong
的同類限制。）這正是月月提到的「gamelan、鐘樂有自己一套音程規則」——非諧色彩
引擎彼此搭配時，直覺的協和音程不一定是物理上最協和的，必須查表。

**重要限制**：以上「引擎 A 固定、引擎 B 移調」的方向是 `tools/consonance.py`
實際算的方向；把兩個引擎的高低對調（例如讓 tongue_drum 變成低音、cimbalom
變成高音）**沒有被這份表驗證過**，`tools/check_piece_consonance.py` 會把這種
情形標成 `UNVALIDATED-DIRECTION`，不會假裝它也合格。寫曲時請維持上表「引擎 A
在下、引擎 B 在上」的方向。

### 13.4 具體驗收方式

新曲寫完後，兩支工具都要跑：

```powershell
python tools/consonance.py                                   # 重新產生協和度表（若模型/引擎有變動）
python tools/check_piece_consonance.py <your_score.score.json>
```

`check_piece_consonance.py` 會列出每一對「宣告時間重疊」的音符，判定它們的音程
是否落在對應表格±10 cents 的建議範圍內，PASS/VIOLATION 逐條列出，寫進
`reports/<score>_consonance_check.md`。**不是自己聽過覺得順耳就交差。**

---

## 14. 聲部配器建議（ROADMAP_PHYSICS.md M9-9c）

### 14.1 為什麼要分角色

§13 顯示：近諧波引擎（cimbalom、piano）自身的協和度曲線行為跟傳統調性和聲接近
（純五度、八度是最深的谷），適合擔任「和聲」；genuinely 非諧的引擎（tongue_drum、
water_gong）自身谷值很淺（dissonance 數值普遍比 cimbalom 低一個量級，見
`reports/consonance_tables.md` §2 的縱向比較），代表它們的部分音本來就分散、
不太會跟自己形成強烈拍音——這個特性更適合拿來做**單一音色的節奏/色彩點綴**，而
不是拿來堆多聲部和弦（堆了也「和諧」，但因為部分音本來就稀疏分散，聽感上不會有
「和聲進行」的效果，會浪費它的物理特性）。

### 14.2 建議分工表

| 角色 | 適合引擎 | 理由（來自表格的數字） |
|---|---|---|
| 和聲（同時多聲部、和弦、和聲進行） | cimbalom、piano | 自身局部極小值行為接近整數比，純五度/八度 dissonance < 0.03–0.05，是全部引擎裡最低的區間 |
| 色彩/節奏（單旋律點綴、標記、脈衝） | tongue_drum、water_gong、water_gong_free | 自身局部極小值密集但普遍偏低（tongue_drum 全域 <0.026、water_gong <0.04），部分音分散帶來獨特音色而非和聲張力 |
| 跨引擎同時發聲 | 依 §13.3 跨引擎表，只用已驗證方向與音程 | 沒查表就疊加＝物理上無法保證不打架 |

`scores/originals/rules_v2_demo/rules_v2_demo_001.score.json`（M9-9d 示範作）
具體套用了這個分工：cimbalom 擔任唯一的和聲/旋律骨幹，tongue_drum 只在段落開場
標記一下（不連續 ostinato），water_gong 只在匯聚點覆蓋長音（結構標記）。詳見該
資料夾的 README.md。

---

## 15. 長程結構模板（ROADMAP_PHYSICS.md M9-9c）

### 15.1 為什麼要先定骨架

§11「AI 新作的標準流程」第 2–3 步已經要求「先寫節奏骨架與休止，不要先塞滿音符」。
這裡把它具體化成幾個可以直接套用、用 JSON `phrases[]` 描述的骨架模板。月月觀察
「AI 逐音生成缺乏長程結構，樂句短是通病」——這幾個模板都是先決定**整體形狀**，
再往裡面填音符，而不是逐音即興。

### 15.2 AABA

四個對稱區塊：A（呈示）、A（重複，力度變化）、B（對比，通常換和聲中心或密度）、
A（再現，通常力度回落）。JSON 骨架範例（只列 phrases[]，不含實際 events）：

```json
{
  "phrases": [
    {"track": "harmony", "role": "A",  "number": 1, "start": 0.0,  "end": 20.0, "breath_after_ms": 300},
    {"track": "harmony", "role": "A2", "number": 2, "start": 20.3, "end": 40.0, "breath_after_ms": 400},
    {"track": "harmony", "role": "B",  "number": 3, "start": 40.4, "end": 64.0, "breath_after_ms": 400},
    {"track": "harmony", "role": "A3", "number": 4, "start": 64.4, "end": 82.0, "breath_after_ms": 500}
  ]
}
```

要點：A2 與 A 用**同一個音程/音高骨架**（同一組 §13.2 選定的音程），只變力度
（§4.6 velocity→dB 表的乾淨倍率，例如 ×1.5=+3.5dB）；B 段換和聲中心時，換的音程
也要是同一份 §13.2 表裡的登記音程（`rules_v2_demo` 用 cimbalom 自身局部極小值
之一的 +500 cents／純四度把 A 段根音移到 B 段根音，而不是隨便選一個新根音）。

### 15.3 頑固低音 / Ostinato

單一聲部（通常是色彩引擎，§14 分工）重複固定的節奏/音高單元，上方疊加會變化的
和聲層。骨架：

```json
{
  "phrases": [
    {"track": "ostinato", "role": "pulse_cell", "number": 1, "start": 0.0, "end": 90.0, "breath_after_ms": 0}
  ]
}
```

ostinato 本身只有一個「phrase」（因為它自己不變），變化發生在同時疊加的和聲層
的 phrases 裡。**時值規則（§16）在這裡特別重要**：ostinato 重複同一個音高，
密度不能超過該引擎/音域的密度上限（§16.2 表）。

### 15.4 Chaconne（頑固低音 + 變奏）

跟 15.3 類似，但低音 ostinato 本身也緩慢變化（每 N 次循環移調或改變一個音）。
骨架用巢狀 phrases：外層 phrase 標記每一輪變奏的起訖，內層（同一 track 的下一批
phrases）標記每輪內部的細分：

```json
{
  "phrases": [
    {"track": "bass_ostinato", "role": "variation_1", "number": 1, "start": 0.0,  "end": 12.0, "breath_after_ms": 200},
    {"track": "bass_ostinato", "role": "variation_2", "number": 2, "start": 12.2, "end": 24.0, "breath_after_ms": 200},
    {"track": "bass_ostinato", "role": "variation_3", "number": 3, "start": 24.2, "end": 36.0, "breath_after_ms": 300}
  ]
}
```

每輪變奏之間的移調音程，一樣要查 §13.2/§13.3——變奏常見的手法是把低音移高一個
「該引擎自身的局部極小值音程」（例如 cimbalom 移一個純五度或八度），維持整輪
變奏內的協和關係可預測、可驗證。

### 15.5 三個模板的共同驗收

不論套用哪個模板，寫完都要跑：

```powershell
python tools/check_piece_consonance.py <score.json>   # §13 音程合規
python tools/verify_score.py <score.json>             # M3 全套機器驗證
```

---

## 16. 時值規則（ROADMAP_PHYSICS.md M9-9b）

### 16.1 規則本體：T60/3 = 衰減 20dB 所需時間

`--dump-modes` 的 `decay` 欄位是 **T60**（衰減 60dB 所需時間；M5 已用音訊實測
驗證 measured/model 比值落在 1.00–1.28，`ModalResonator::excite()` 的
`decayCoeff = exp(-6.9078f/(decayTime*sampleRate))` 定義了這件事）。單一指數
衰減的 dB 值對時間**線性**，所以衰減 20dB 所需時間精確等於 **T60 / 3**——不是
新常數，是既有已驗證 T60 欄位的代數推論。

**規則**：同一個音高要再次擊發前，至少讓上一擊經過 T60/3 秒（衰減 20dB 以上）
再重新激發，避免共鳴堆疊變濁——這是月月觀察「短暫且不和諧」其中一個可測量成因
（連續同音快速反覆，前一次的共鳴還沒衰減乾淨就疊加新的一擊，數學上會拉高中頻
的能量密度，聽起來「濁」）。

### 16.2 各引擎/音域的最小重擊間距與密度上限

數字來自 `reports/consonance_tables.md` §4（`tools/consonance.py` 自動產生，
來源是各引擎在 MIDI 48/60/72 的 `--dump-modes` T60 欄位）：

| 引擎 | 音域 (MIDI) | T60 (s) | 最小重擊間距 = T60/3 (s) | 密度上限 (音符/秒) |
|---|---:|---:|---:|---:|
| cimbalom | 48 | 1.982 | 0.660 | 1.51 |
| cimbalom | 60 | 1.948 | 0.649 | 1.54 |
| cimbalom | 72 | 1.840 | 0.613 | 1.63 |
| tongue_drum | 48/60/72 | 1.218 | 0.406 | 2.46 |
| water_gong | 48/60/72 | 1.188 | 0.396 | 2.53 |
| water_gong_free | 48/60/72 | 1.229 | 0.410 | 2.44 |
| piano | 48 | 1.982 | 0.660 | 1.51 |
| piano | 60 | 1.948 | 0.649 | 1.54 |
| piano | 72 | 1.840 | 0.613 | 1.63 |

（FM 不在表內——它是 ADSR 包絡，不是模態衰減，§0 驗證域聲明已標註 FM 域外。
tongue_drum/water_gong/water_gong_free 在這三個測試音域裡 T60 沒有隨音高變化，
是模型量到的真實結果，不是簡化假設。）

### 16.3 用法

寫曲時，任何「同一引擎、同一音高」的連續事件，起始時間差要 ≥ 對應音域的
「最小重擊間距」欄；一段時間內同一音高的密度不要超過「密度上限」欄。不同音高
交替演奏（琶音、旋律線）不受此規則直接限制（各自衰減互不干擾），但若把整條
琶音線的整體事件密度也控制在密度上限之內，可以額外確保不會整體混濁——
`scores/originals/rules_v2_demo/rules_v2_demo_001.score.json` 的 cimbalom
琶音統一用 0.75 秒 onset 間距（見該曲 README），超過所有音域 0.66 秒的門檻，
是刻意選的保守值。

### 16.4 驗收

這份時值規則的來源（T60 表）本身已經是 M5 GATE 驗證過的機器量測值，§16 只是
把它換算成「下次同音間隔要多久」的作曲決策數字；沒有新的驗收指令，直接沿用
`python tools/consonance.py`（重新產生本節表格）與已有的 M5 GATE
（`python tools/physics_verify.py --t60`）。

