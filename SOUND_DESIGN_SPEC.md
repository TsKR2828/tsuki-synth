# TsukiSynth 音效設計規格補充

> 來源：音效設計師回饋（2026-05-07）
> 狀態（2026-07-17）：metadata、distortion、glide、trim 與嚴格 score 契約已整合；
> 本文末尾的 tags 範例仍是分類提案，不代表每個 key 都是 renderer 欄位。

---

## 一、主大類（業界通用分類法）

現有 `tags.json` 的 categories 以發聲體分類（bell/chime/gong），不符合音效設計師的搜尋習慣。
以下為業界主流的**功能導向**主大類，應作為最上層分類：

| 主類 Key | 中文 | 英文 | 說明 |
|----------|------|------|------|
| `ambience` | 環境氛圍 | Ambience | 背景層、空間填充 |
| `creature` | 生物 | Creature | 怪物、動物、非人類角色 |
| `magic` | 魔法 | Magic / Fantasy | 施法、精靈、能量 |
| `ui` | 介面音效 | UI / Interface | 按鈕、通知、系統回饋 |
| `whoosh` | 轉場 | Whoosh / Transition | 場景切換、劃過、漸入漸出 |
| `impact` | 撞擊 | Impact / Hit | 重擊 boom / 打擊 hit / 爆破 impact |
| `foley` | 動作聲 | Foley / Movement | 腳步、衣物、物件操作 |
| `mechanical` | 機械 | Industrial / Mechanical | 齒輪、金屬、工業 |

### 與現有分類的對應關係

```
業界主類              現有 tags.json
─────────────────────────────────────
ambience         ←   ambient
impact           ←   bell, gong, drum（部分）
mechanical       ←   mechanical
ui               ←   alert
whoosh           ←   （新增）
magic            ←   （新增）
creature         ←   （新增）
foley            ←   （新增）
```

### 建議做法

保留現有 categories 作為**子類 (subcategory)**，新增主大類作為上層：

```json
{
  "primary_type": "impact",
  "subcategory": "bell"
}
```

---

## 二、聲音類型：OneShot / Loop / Variant

一個完整的**聲音家族 (Sound Family)** 包含三種類型：

| 類型 | 說明 | 用途 |
|------|------|------|
| **OneShot** | 單次發聲，有明確起始與結束 | 旋律拼接、觸發式音效 |
| **Loop** | 可無縫循環的片段 | 剪輯對秒數、背景層 |
| **Variant** | 基於原始音效的衍生版（加 FX / noise / 參數微調） | 豐富素材庫、避免重複感 |

### Schema 擴充建議

`score.schema.json` 的 `meta` 區塊新增：

```json
{
  "sound_type": "oneshot | loop | variant",
  "family_id": "akashic_bell",
  "loop_bpm": 120,
  "loop_bars": 4
}
```

`sound_names.json` 每筆素材新增：

```json
{
  "sound_type": "oneshot",
  "family_id": "akashic_bell",
  "variant_description": null
}
```

---

## 三、Character（聽感描述詞）

獨立於 mood（情緒）的另一個維度 — 描述聲音的**物理質感**：

| Character | 中文 | 聽感描述 |
|-----------|------|---------|
| `punch` | 衝擊 | 短促有力、低頻集中 |
| `soft` | 柔和 | 輕觸、圓潤 |
| `dark` | 暗沉 | 低頻主導、高頻被削 |
| `bright` | 明亮 | 高頻突出、穿透力強 |
| `pulse` | 脈衝 | 節奏感、反覆律動 |
| `stomp` | 重踏 | 大力撞擊、有重量 |
| `airy` | 空氣感 | 輕飄、有呼吸空間 |
| `metallic` | 金屬 | 硬質反射、高頻泛音豐富 |
| `glitch` | 故障 | 數位錯誤、不穩定碎裂 |

### 與現有 mood 的區別

```
mood     = 情緒意圖（sacred / ominous / playful）→ 用於敘事選擇
character = 物理聽感（punch / metallic / airy）  → 用於音色搜尋
```

兩者正交，可組合：一個音效可以是 `mood: ominous` + `character: metallic`。

---

## 四、命名規則

### 業界慣例格式

```
{Type}_{Character}_{SoundType}_{Pitch/BPM}.wav
```

| 欄位 | 來源 | 範例 |
|------|------|------|
| Type | 主大類 | Impact / UI / Whoosh / Magic |
| Character | 聽感 | Metallic / Dark / Bright / Punch |
| SoundType | oneshot / loop / variant | OneShot / 120BPM / Var01 |
| Pitch/BPM | 音高或速度 | C1 / 120BPM / 30S（剪輯用時長） |

### 範例

```
Impact_Metallic_OneShot_C2.wav        ← 單音撞擊
Whoosh_Airy_OneShot.wav               ← 單次轉場
Ambience_Dark_120BPM.wav              ← 循環氛圍
Magic_Bright_Var01.wav                ← 魔法音效變體
UI_Soft_OneShot.wav                   ← 介面提示音
```

### 與 TsukiSynth 世界觀命名的共存方案

保留內部 ID（`akashic_bell_001`）作為開發用識別碼，另設 `export_filename` 遵循業界規則：

```json
{
  "id": "akashic_bell_001",
  "export_filename": "Magic_Metallic_OneShot_C5",
  "display_name": "Akashic Bell"
}
```

---

## 五、功能需求

以下為回饋中提到的音效處理功能，需反映在 score schema 或引擎能力中：

### 5.1 播放起始位置（Playback Offset）

> 「決定音效從前面、中間、或後面開始播」

用途：同一段素材取不同段落使用。

```json
{
  "playback": {
    "start_position": 0.0,
    "end_position": 1.0
  }
}
```

`start_position`: 0.0 = 從頭，0.5 = 從中間，0.75 = 從後段起。

### 5.2 音效混合 / 接續（Sound Layering）

> 「前段中段是 A，後段是 B」

用途：組合兩個不同音色，形成更複雜的音效。

```json
{
  "layers": [
    { "source": "akashic_bell_001", "region": [0.0, 0.6], "gain": 1.0 },
    { "source": "restraint_metal_click_001", "region": [0.5, 1.0], "gain": 0.8 }
  ],
  "crossfade_ms": 50
}
```

### 5.3 失真效果（Distortion）

> 「讓音變得不穩定」

效果鏈新增 distortion 模組：

```json
{
  "effects": {
    "distortion": {
      "type": "overdrive | bitcrush | wavefold",
      "drive": 0.6,
      "instability": 0.3,
      "wet": 0.5
    }
  }
}
```

- `instability`: 隨機微調參數造成不穩定感（LFO 調制 drive）

### 5.4 滑音（Portamento / Glide）

> 「把音連在一起，決定要上滑還是下滑」

事件層級新增 glide 參數：

```json
{
  "time": 0.5,
  "engine": "plate",
  "note": "E5",
  "glide": {
    "from_note": "C5",
    "duration_ms": 120,
    "curve": "linear | exponential"
  }
}
```

或用於連續事件間的自動銜接：

```json
{
  "legato": true,
  "glide_ms": 80
}
```

---

## 六、整合優先級建議

| 優先 | 項目 | 影響範圍 | 狀態 |
|------|------|---------|------|
| P0 | 主大類分類法 | tags.json, sound_names.json | ✅ 已整合 |
| P0 | OneShot/Loop/Variant 類型 | score schema, sound_names.json | ✅ 已整合 |
| P1 | Character 聽感維度 | tags.json, sound_names.json | ✅ 已整合 |
| P1 | 命名規則（export_filename） | sound_names.json, export pipeline | ✅ 已整合 |
| P2 | Distortion 效果 | score schema, EffectsChain.h, Distortion.h | ✅ 已實作 |
| P2 | Glide / Portamento | score schema, ScoreRenderer.h, 三引擎 | ✅ 已實作 |
| P3 | 播放位置裁切 | ScoreParser.h, ScoreRenderer.h | ✅ 已實作 |
| P3 | 音效混合 (Layering) | CLI pipeline | 待實作（需 Phase C2） |

---

## 七、tags.json 改版草案

```json
{
  "$schema": "TsukiSynth Tag Taxonomy v2",

  "primary_types": {
    "ambience": "環境氛圍 — 背景層、空間填充",
    "creature": "生物 — 怪物、動物、非人類角色",
    "magic": "魔法 — 施法、精靈、能量",
    "ui": "介面音效 — 按鈕、通知、系統回饋",
    "whoosh": "轉場 — 場景切換、劃過",
    "impact": "撞擊 — 重擊 / 打擊 / 爆破",
    "foley": "動作聲 — 腳步、衣物、物件操作",
    "mechanical": "機械 — 齒輪、金屬、工業"
  },

  "subcategories": {
    "bell": "鐘聲 — 圓板模型，長殘響",
    "chime": "風鈴 — 梁模型，清脆短音",
    "gong": "鑼 — 圓板模型，深沉共鳴",
    "drum": "鼓類 — 目前僅作 metadata；尚無真圓膜物理 engine",
    "string": "弦類 — 弦模型",
    "alert": "警告提示 — 短促高頻",
    "motif": "短旋律 — 多音符序列"
  },

  "sound_types": ["oneshot", "loop", "variant"],

  "characters": {
    "punch": "衝擊 — 短促有力",
    "soft": "柔和 — 輕觸圓潤",
    "dark": "暗沉 — 低頻主導",
    "bright": "明亮 — 高頻突出",
    "pulse": "脈衝 — 節奏律動",
    "stomp": "重踏 — 大力有重量",
    "airy": "空氣感 — 輕飄",
    "metallic": "金屬 — 硬質高頻泛音",
    "glitch": "故障 — 數位碎裂"
  },

  "moods": {
    "sacred": "神聖、莊嚴",
    "mystical": "神秘、魔法感",
    "tense": "緊張、警戒",
    "ominous": "不祥、黑暗",
    "playful": "活潑、可愛",
    "calm": "平靜、療癒",
    "epic": "壯闊、史詩",
    "melancholic": "憂鬱、感傷"
  },

  "energy_levels": ["very-low", "low", "medium", "high", "very-high"],

  "use_cases": [
    "VTuber scene transition",
    "VTuber reaction / emote",
    "chat notification",
    "donation / superchat alert",
    "UI button click",
    "UI confirmation",
    "game action feedback",
    "BGM motif / loop element",
    "ambient background",
    "intro / outro jingle"
  ],

  "worlds": {
    "akashic": "阿卡西 — 靈性、紀錄、光",
    "rabbit": "兔兔 — 可愛、活潑、偶爾暴走",
    "restraint": "拘束 — 暗黑、金屬、束縛",
    "forest": "森林 — 木質、自然、風",
    "ocean": "海洋 — 水聲、深沉、波動",
    "clockwork": "齒輪 — 精密、機械、蒸汽龐克"
  }
}
```

---

*目前已整合的 renderer 契約以 `scores/schema/score.schema.json` 與
`src/score/ScoreParser.h` 為準：`primary_type`、`sound_type`、`family_id`、`character`、
`mood`、`use_case` 等已受嚴格驗證；本節其他 taxonomy 只作索引設計參考。不存在真
`membrane` engine，`drum` 不得被誤寫成事件的 engine。*
