# TsukiSynth AI／聾人物理作曲文件

> 版本：1.0  
> 日期：2026-06-21  
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

