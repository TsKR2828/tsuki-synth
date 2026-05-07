# 音色庫擴充計畫（方向 C）

> 目標：為 6 個世界觀各設計一組音效家族，產出可用的素材庫。
> 預計產出：30-36 個 score.json + 對應 sound_names.json 索引更新

---

## 一、設計原則

### 每個世界觀的音效家族結構

```
一個世界觀（world）
├── 場景轉換音 (transition)     × 1 oneshot
├── 通知/提示音 (notification)  × 1 oneshot
├── 角色動作音 (action)         × 1 oneshot
├── 氛圍底層 (ambient)          × 1 oneshot（長音）
├── UI 回饋音 (ui)              × 1 oneshot
└── 變體 (variant)              × 1（從上述任一衍生，改材質/力度/效果）
```

每個世界觀 = **6 個 score.json**，6 個世界觀 = **36 個檔案**

### 材質 × 世界觀 對照

| 世界觀 | 核心材質 | 輔助材質 | 音色方向 |
|--------|---------|---------|---------|
| **akashic** | bronze, glass | brass | 清澈、神聖、長殘響 |
| **rabbit** | aluminum | wood_maple | 明亮、短促、活潑 |
| **restraint** | steel | rubber | 暗沉、金屬衝擊、壓迫 |
| **forest** | wood_spruce, wood_maple | — | 溫暖、有機、木質敲擊 |
| **ocean** | glass, brass | copper | 流動、深沉、水感 glide |
| **clockwork** | steel, brass | copper | 精密、節奏、機械反覆 |

### 引擎分配策略

| 用途 | 推薦引擎 | 原因 |
|------|---------|------|
| 鐘/鑼/轉場 | plate | 圓板模態豐富、殘響長 |
| 木琴/提示 | beam | 清脆非諧波、短衰減 |
| 弦擊/衝擊 | string | 諧波結構明確 |
| 鋼琴/旋律 | fm | 音域寬、音色穩定 |
| 水感 glide | plate (water_gong) | 內建 pitch glide |
| 多音符 motif | 多事件 | 同一 score 內排列多 event |

---

## 二、各世界觀音效設計

### World 1: Akashic（阿卡西）

靈性、紀錄、光。空間感大、殘響長、青銅/玻璃為主。

| # | ID | 名稱 | 類型 | 引擎 | 材質 | 特色 |
|---|---|------|------|------|------|------|
| 1 | `akashic_transition_001` | 阿卡西開門 | transition | plate | bronze | 兩層敲擊+長 reverb decay 8s |
| 2 | `akashic_notify_001` | 紀錄提示 | notification | beam | glass | 短促玻璃琴兩音上行 |
| 3 | `akashic_action_001` | 翻頁 | action | string | brass | 輕撥弦+薄板共鳴 |
| 4 | `akashic_ambient_001` | 圖書館低鳴 | ambient | plate | bronze | 極低 velocity、超長 duration |
| 5 | `akashic_ui_001` | 確認光點 | ui | beam | glass | 單音極短、高音域 |
| 6 | `akashic_transition_var01` | 阿卡西開門（暗） | variant | plate | copper | 同 #1 改材質+加 distortion |

### World 2: Rabbit（兔兔）

可愛、活潑、偶爾暴走。明亮鋁材、木槌、快速雙擊。

| # | ID | 名稱 | 類型 | 引擎 | 材質 | 特色 |
|---|---|------|------|------|------|------|
| 7 | `rabbit_transition_001` | 兔跳轉場 | transition | beam | aluminum | 三音快速下行 |
| 8 | `rabbit_notify_001` | 兔兔叮 | notification | beam | aluminum | 高音單叮+短 reverb |
| 9 | `rabbit_action_001` | 暴走踩踏 | action | string | steel | 重擊低音+快衰減 |
| 10 | `rabbit_ambient_001` | 草地風鈴 | ambient | beam | aluminum | 隨機多音、soft 觸發 |
| 11 | `rabbit_ui_001` | 蘿蔔按鈕 | ui | beam | wood_maple | 木質短觸、柔和 |
| 12 | `rabbit_notify_var01` | 兔兔叮（怒） | variant | beam | steel | 同 #8 改鋼材+高 velocity |

### World 3: Restraint（拘束）

暗黑、金屬、束縛。鋼材為主、短衝擊+壓迫殘響。

| # | ID | 名稱 | 類型 | 引擎 | 材質 | 特色 |
|---|---|------|------|------|------|------|
| 13 | `restraint_transition_001` | 鎖鏈拖行 | transition | string | steel | 多事件快速連擊+delay |
| 14 | `restraint_notify_001` | 警報脈衝 | notification | plate | steel | 低音板+distortion |
| 15 | `restraint_action_001` | 枷鎖落下 | action | string+plate | steel | 同時觸發弦衝擊+板殘響 |
| 16 | `restraint_ambient_001` | 地牢金屬嗡鳴 | ambient | plate | steel | 極低頻長音+instability |
| 17 | `restraint_ui_001` | 釘子確認 | ui | string | steel | 極短高阻尼衝擊 |
| 18 | `restraint_action_var01` | 枷鎖落下（重） | variant | string+plate | steel | 同 #15 加 stomp、更高 velocity |

### World 4: Forest（森林）

木質、自然、風。雲杉/楓木為主、棉槌/felt 觸感。

| # | ID | 名稱 | 類型 | 引擎 | 材質 | 特色 |
|---|---|------|------|------|------|------|
| 19 | `forest_transition_001` | 樹葉風過 | transition | beam | wood_spruce | 多音符散落、隨機時間偏移 |
| 20 | `forest_notify_001` | 鳥鳴提示 | notification | beam | wood_maple | 兩音上行、airy |
| 21 | `forest_action_001` | 木杖敲地 | action | string | wood_spruce | 低音弦、棉槌、短衰減 |
| 22 | `forest_ambient_001` | 森林低語 | ambient | beam | wood_spruce | 極 soft、多重疊長音 |
| 23 | `forest_ui_001` | 種子點擊 | ui | beam | wood_maple | 極短木質叩擊 |
| 24 | `forest_transition_var01` | 樹葉風過（夜） | variant | beam | wood_spruce | 同 #19 加 dark distortion |

### World 5: Ocean（海洋）

水聲、深沉、波動。玻璃/黃銅、water_gong glide 為特色。

| # | ID | 名稱 | 類型 | 引擎 | 材質 | 特色 |
|---|---|------|------|------|------|------|
| 25 | `ocean_transition_001` | 潮汐湧入 | transition | plate (water_gong) | brass | pitch glide 下行+長 reverb |
| 26 | `ocean_notify_001` | 氣泡提示 | notification | beam | glass | 上行 glide、短促 |
| 27 | `ocean_action_001` | 浪擊礁石 | action | plate | glass | 寬板低頻+高 damping |
| 28 | `ocean_ambient_001` | 深海共鳴 | ambient | plate (water_gong) | copper | 超長 glide+低 velocity |
| 29 | `ocean_ui_001` | 水滴確認 | ui | beam | glass | 單音極短+glide 微下彎 |
| 30 | `ocean_transition_var01` | 潮汐湧入（暴風） | variant | plate | brass | 同 #25 加 distortion+高 velocity |

### World 6: Clockwork（齒輪）

精密、機械、蒸汽龐克。鋼/黃銅、規律節奏、短脈衝。

| # | ID | 名稱 | 類型 | 引擎 | 材質 | 特色 |
|---|---|------|------|------|------|------|
| 31 | `clockwork_transition_001` | 發條上緊 | transition | string | steel | 快速重複短音漸快 |
| 32 | `clockwork_notify_001` | 齒輪咬合 | notification | beam | brass | 雙音金屬叩擊 |
| 33 | `clockwork_action_001` | 蒸汽噴射 | action | plate | copper | 寬頻噪音感+快衰減 |
| 34 | `clockwork_ambient_001` | 鐘塔運轉 | ambient | string | brass | 低頻規律脈衝 loop 感 |
| 35 | `clockwork_ui_001` | 按鈕機關 | ui | beam | steel | 短促金屬 click |
| 36 | `clockwork_notify_var01` | 齒輪咬合（故障） | variant | beam | brass | 同 #32 加 glitch distortion |

---

## 三、實作步驟

### Step 1：建立目錄結構

```
scores/
├── examples/          ← 現有 3+1 個範例（保留）
└── library/
    ├── akashic/       ← 6 個 .score.json
    ├── rabbit/        ← 6 個 .score.json
    ├── restraint/     ← 6 個 .score.json
    ├── forest/        ← 6 個 .score.json
    ├── ocean/         ← 6 個 .score.json
    └── clockwork/     ← 6 個 .score.json
```

### Step 2：逐世界觀生成 score.json（按批次）

每批 = 一個世界觀的 6 個檔案。順序：

1. **Akashic**（最熟悉，有現成範例參照）
2. **Rabbit**（已有 rabbit_warning 可參考）
3. **Restraint**（已有 restraint_metal_click）
4. **Forest**（木材新方向，需要小心 damping 參數）
5. **Ocean**（water_gong 引擎特化，需 glide 設計）
6. **Clockwork**（多事件節奏型，最複雜）

### Step 3：更新 sound_names.json

每完成一批就把 6 筆新素材加入索引，含完整 metadata：
- primary_type, subcategory, sound_type, family_id
- character, mood, energy, use_cases
- export_filename（業界命名）
- score_file, wav_file 路徑

### Step 4：驗證

- JSON lint 全部通過
- 欄位值在 tags.json 的 enum 範圍內
- family_id 一致性（同家族的 oneshot 和 variant 共用）
- export_filename 格式正確：`Type_Character_SoundType_Pitch.wav`

### Step 5：commit 策略

每世界觀一個 commit：
```
feat(library): add akashic sound family (6 scores)
feat(library): add rabbit sound family (6 scores)
feat(library): add restraint sound family (6 scores)
feat(library): add forest sound family (6 scores)
feat(library): add ocean sound family (6 scores)
feat(library): add clockwork sound family (6 scores)
```

最後一個 commit 更新 sound_names.json 總索引（或每批就更新）。

---

## 四、物理參數設計指南

### 敲擊位置（strike_position）對音色的影響

| 位置 | 效果 | 適用場景 |
|------|------|---------|
| 0.05-0.15 | 全泛音激發、明亮尖銳 | alert, metallic |
| 0.25-0.35 | 自然平衡 | 大多數場景 |
| 0.45-0.55 | 偶數泛音消失、柔和空洞 | ambient, soft |
| 0.7+ | 邊緣薄音、快衰減 | ui click, short |

### Velocity 對應聽感

| velocity | 聽感 | 適用 |
|----------|------|------|
| 0.1-0.3 | 極輕、背景 | ambient, soft |
| 0.4-0.6 | 自然力度 | 大多數 |
| 0.7-0.85 | 明確有力 | action, transition |
| 0.9-1.0 | 重擊飽滿 | impact, stomp |

### Reverb 設計原則

| 場景類型 | decay | wet | 理由 |
|---------|-------|-----|------|
| 極短 UI click | 0.5-1.0 | 0.1 | 不模糊 |
| 通知提示 | 1.0-2.0 | 0.2-0.3 | 稍有空間 |
| 角色動作 | 1.5-3.0 | 0.2-0.4 | 世界觀氛圍 |
| 場景轉換 | 4.0-8.0 | 0.5-0.7 | 留白、戲劇感 |
| 氛圍底層 | 6.0-15.0 | 0.6-0.8 | 空間填充 |

### Duration 設計

| 用途 | duration (sec) | 尾巴 (tail_silence_ms) |
|------|----------------|----------------------|
| UI click | 0.1-0.3 | 50-100 |
| notification | 0.3-1.0 | 150-300 |
| action | 0.5-2.0 | 200-400 |
| transition | 3.0-8.0 | 300-500 |
| ambient | 8.0-20.0 | 500-1000 |

---

## 五、Variant 設計手法

| 手法 | 改什麼 | 效果 |
|------|--------|------|
| 換材質 | material | 整體音色明暗改變 |
| 改力度 | velocity | 能量感增減 |
| 改位置 | strike_position | 泛音結構改變 |
| 加失真 | distortion | 不穩定/故障感 |
| 加滑音 | glide | 流動/不安定感 |
| 改 reverb | effects.reverb | 空間大小改變 |
| 改尺寸 | thickness/radius/length | 音高和共鳴特性 |

---

## 六、時程估計

| 步驟 | 工作量 | 說明 |
|------|--------|------|
| Step 1 目錄 | 1 分鐘 | mkdir |
| Step 2 ×6 世界觀 | 每世界觀 15-20 分鐘 | 逐檔設計物理參數 |
| Step 3 索引更新 | 每批 5 分鐘 | 36 筆到 sound_names.json |
| Step 4 驗證 | 5 分鐘 | JSON lint + enum 檢查 |
| **總計** | **約 2 小時** | 可一次性完成或分批 |

---

*本計畫確認後即可開始執行。*
