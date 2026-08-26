# TsukiSynth《月亮旋律》FM Piano 調整補強書

> **2026-07-17 domain note:** this remains a historical FM sound-design document. FM Piano is
> deliberately outside TsukiSynth's physical-instrument verification domain and must never be
> used as evidence for “樂器物理正確”. Current parameter/schema/preset behavior is defined by
> `FMPianoEngine.h`, `ScoreParser.h`, `score.schema.json`, and stable-ID `PresetManager.h`.

版本：v1.0  
用途：給開發者、Claude Code、Codex 審查與後續音色調整使用  
目標：把目前的 FM Piano 從「憑感覺亂轉參數」改成「有參考母本、有一致預設、有可調方向」的樂器引擎。

---

## 0. 一句話結論

目前 TsukiSynth 的 `FM Piano` 可以保留為 **DX7-inspired 的輕量 FM 樂器**，先不要追求 Yamaha DX7 完整相容。

更實際的做法是：

1. 先修掉參數命名、預設值、schema、preset 缺漏這些會造成混亂的問題。
2. 用成熟 FM Piano 成品當參考，不要靠聽感盲調。
3. 先做「2-op 可用版」，再做「E.Piano 3-stack 補強版」。
4. 所有宣傳、UI、文件都避免寫成 DX7-compatible。

---

## 1. 目前審查結論整理

### 1.1 大方向

Opus 4.6 的方向可以當成「2-op FM 音色 recipe」使用，但目前 TsukiSynth 的 `FM Piano` 比 Yamaha DX7 簡化很多。

目前定位應該是：

```txt
DX7-inspired
FM-inspired
Lightweight FM Piano
```

避免使用：

```txt
DX7-compatible
DX7 clone
Full DX7 engine
```

---

## 2. 目前主要差異

### 2.1 架構差異最大

目前 TsukiSynth 的 FM Piano 是：

```txt
單一 carrier
+
單一 modulator
+
hammer noise
+
180 / 340 Hz body resonance
```

也就是 2-op FM 加上一些鋼琴感補強。

DX7 則是：

```txt
6 個 sine operators
32 種 algorithms
每個 operator 有自己的 envelope
可讓 harmonic structure 隨時間變化
```

因此目前引擎很難完整重現 DX7 的 E.Piano、Bell、Vibe 類音色。

---

### 2.2 目前只有一個 `fm_ratio`

目前一次只能設定一個 modulator / carrier ratio。

這代表 TsukiSynth 現在無法同時做：

```txt
1:1 body
+
14:1 tine / bell attack
+
detuned shimmer stack
```

但這類多層結構正是 FM electric piano 很重要的聲音來源。

---

### 2.3 `fm_brightness` 名稱容易誤導

目前程式中的 `fm_brightness` 看起來像亮度，但實際行為更像：

```txt
bodyIndex 的 decay speed
```

也就是它影響的是 FM body modulation 衰減速度，而不是直接把聲音變亮。

真正更接近「直接放大 FM index」的是：

```txt
macro_brightness
```

這會造成幾個問題：

1. UI 使用者會以為轉高就是更亮。
2. preset 作者會誤判參數。
3. AI JSON 產生器會用錯方向。
4. 審查者容易把這顆旋鈕當成真正的 tone brightness。

---

### 2.4 feedback 與 DX7 不等價

目前 feedback 是作用在唯一的 modulator 上。

UI 顯示範圍是：

```txt
0.0 ~ 1.0
```

內部最高約轉成：

```txt
0.7
```

DX7 的 feedback 則是：

```txt
0 ~ 7
```

而且位置取決於 algorithm。  
所以目前的 feedback 只能說是 DX-inspired feedback amount，不能說是 DX7 algorithm feedback。

---

### 2.5 Factory FM preset 數量不一致

目前 engine 支援 8 個 sound type：

```txt
Piano
E.Piano
Vibraphone
Bell
Organ
Pad
Bass
Brass
```

但 factory preset registry 目前只有 6 個 FM preset，缺：

```txt
Vibraphone
Brass
```

這會讓 UI / preset / engine 支援表現得像半成品。

---

### 2.6 APVTS 與 FMParams 預設值不一致

目前 DAW plugin 的 APVTS default 與 CLI / ScoreRenderer 使用的 `FMParams` default 不一致。

差異範例：

```txt
APVTS:
fm_ratio = 1.0
fm_brightness = 0.6

FMParams:
ratio = 2.0
brightness = 0.5
```

結果是：

```txt
plugin 開起來的預設聲
和
score render 的預設聲
可能不同
```

這會讓調音、測試、demo、bug report 全部變麻煩。

---

## 3. 目前 factory FM preset 數值

以下是目前已知 preset 數值整理。

| Preset | ratio | index | brightness | feedback | attack | release |
|---|---:|---:|---:|---:|---:|---:|
| Acoustic Piano | 1.0 | 4.5 | 0.77 | 0.02 | 5ms | 500ms |
| Electric Rhodes | 1.0 | 3.5 | 0.50 | 0.05 | 5ms | 400ms |
| DX7 Crystal Bell | 7.0 | 8.0 | 0.20 | 0.00 | 3ms | 1500ms |
| Church Organ | 1.0 | 2.0 | 0.00 | 0.50 | 50ms | 200ms |
| Ambient Pad | 2.0 | 3.0 | 0.35 | 0.30 | 800ms | 3000ms |
| FM Bass | 1.0 | 6.0 | 0.80 | 0.08 | 3ms | 150ms |

---

## 4. 最重要的開發方向

### 4.1 不要靠聽感盲調

FM Piano 到處都有成熟成品。  
目前最有效率的方法是：

```txt
拿成熟 FM Piano / DX7 E.Piano 音色當參考母本
再壓縮成 TsukiSynth 能吃的參數
```

也就是：

```txt
Dexed / DX7 factory preset / 其他 FM Piano 成品
↓
聽 reference
↓
轉成 TsukiSynth 2-op recipe
↓
必要時加 3-stack 補強
```

---

### 4.2 可以抄的不是程式碼，是音色結構

可以參考：

```txt
DX7 E.PIANO 1
DX7 VIBE 1
DX7 Bell / Tubular Bell
Dexed 內建或 sysex 音色
其他 FM Piano preset
```

但要注意：

```txt
不要直接搬 GPL code
不要宣稱完整 DX7 相容
不要把 6-op patch 逐欄硬塞進 2-op engine
```

真正要抄的是：

```txt
attack 像什麼
body 留多久
金屬感在哪個瞬間出現
尾音是乾淨、玻璃、木頭、鐘，還是 pad
velocity 變大時聲音怎麼變
```

---

## 5. 調音人話表

這張表給沒有 FM 背景的人使用。

| 聽起來像什麼 | 可能原因 | 優先調整 |
|---|---|---|
| 像電話鈴 | ratio 太高、index 太高、release 太長 | 降 ratio 或 index |
| 像鐘，不像電鋼琴 | 高 ratio 層太重、body 太少 | 降高 ratio 音量，加 body |
| 像風琴 | envelope 太平，index 沒有衰減 | 加快 index decay |
| 太刺耳 | index 太高、feedback 太高、高頻層太大 | 降 index / feedback |
| 太薄 | body index 太低、release 太短、低中頻不足 | 加 body / 延長 decay |
| 敲擊感不夠 | attack index 不夠、hammer noise 太少 | 加 attack layer |
| 尾音很假 | release 太直、body resonance 不合 | 調 release / resonance |
| 聲音糊成一團 | feedback 太高、低頻 resonance 太多 | 降 feedback / body resonance |
| 沒有力度表情 | velocity 只控制音量 | 加 velocity-to-index |
| 每個 preset 都像同一顆聲音 | body resonance 固定、stack 太少 | 依 sound type 切 character |

---

## 6. P0：最優先修正

P0 是「現在就該修」的項目。  
這些不是音色美化，而是基礎一致性。

---

### P0-1. 統一 APVTS default 與 FMParams default

#### 問題

plugin 與 score renderer 預設值不一致。

#### 影響

```txt
同一個 preset / score
在 DAW 和 CLI 裡可能聽起來不一樣
```

#### 建議修法

選一組共同 default。  
建議先用 Acoustic Piano 方向當預設：

```txt
fm_ratio = 1.0
fm_index = 4.5
fm_brightness = 0.6 ~ 0.77
fm_feedback = 0.02
fm_attack = 0.005
fm_release = 0.5
```

#### 驗收條件

```txt
PluginProcessor.cpp 的 APVTS default
和
FMPianoEngine.h 的 FMParams default
保持一致
```

#### 測試建議

```txt
FMParams defaults match APVTS defaults
```

---

### P0-2. 補 `score.schema.json` 的 FM 參數

#### 問題

Parser 已支援 FM 參數，但 schema 沒列出來。

#### 影響

```txt
AI / 驗證工具不知道 FM 可以控制什麼
```

#### 應補欄位

```json
{
  "fm_ratio": {
    "type": "number",
    "minimum": 0.25,
    "maximum": 16.0
  },
  "fm_index": {
    "type": "number",
    "minimum": 0.0,
    "maximum": 12.0
  },
  "fm_brightness": {
    "type": "number",
    "minimum": 0.0,
    "maximum": 1.0
  },
  "fm_feedback": {
    "type": "number",
    "minimum": 0.0,
    "maximum": 1.0
  },
  "fm_attack": {
    "type": "number",
    "minimum": 0.001,
    "maximum": 5.0
  },
  "fm_release": {
    "type": "number",
    "minimum": 0.01,
    "maximum": 10.0
  }
}
```

#### 驗收條件

```txt
含 fm_ratio / fm_index / fm_feedback 的 score JSON 可以通過 schema validation
```

---

### P0-3. 補 Vibraphone 與 Brass factory preset

#### 問題

engine 支援 8 個 sound type，factory preset 只有 6 個。

#### 建議新增 preset

##### Vibraphone

```txt
name = Vibraphone
ratio = 3.0
index = 4.2
brightness = 0.35
feedback = 0.02
attack = 0.008
release = 1.2
```

音色方向：

```txt
短 attack
金屬但柔和
尾音乾淨
body resonance 很輕或關閉
```

##### Brass

```txt
name = FM Brass
ratio = 1.0
index = 5.8
brightness = 0.65
feedback = 0.12
attack = 0.035
release = 0.35
```

音色方向：

```txt
略有咬字
比 organ 更有 attack
避免過度刺耳
```

#### 驗收條件

```txt
supported sound type count == factory FM preset count
```

---

### P0-4. 修正 `fm_brightness` 的 UI 語意

#### 問題

目前 `fm_brightness` 不是直接亮度，名稱會誤導。

#### 建議短期做法

保留 parameter ID：

```txt
fm_brightness
```

避免破壞 preset / DAW session。

但 UI 顯示名稱改成：

```txt
Tone Decay
```

或：

```txt
Body Decay
```

tooltip 寫：

```txt
Controls how quickly the FM body modulation fades.
```

#### 驗收條件

```txt
UI 不再讓使用者以為 fm_brightness 是直接亮度
既有 preset 仍可正常讀取
```

---

## 7. P1：讓 FM Piano 比較像樂器

P1 是讓聲音變得比較能用的補強。

---

### P1-1. 加 velocity-to-index

#### 問題

FM Piano 很吃力度。  
如果 velocity 只控制音量，聲音會很死。

#### 建議行為

```txt
輕彈：
聲音圓一點
FM index 低一點
hammer noise 少一點

重彈：
聲音亮一點
attack 明顯一點
hammer noise 多一點
```

#### 建議公式方向

```cpp
index *= map(velocity, 0.0f, 1.0f, 0.45f, 1.25f);
attackIndex *= map(velocity, 0.0f, 1.0f, 0.5f, 1.6f);
hammerNoise *= map(velocity, 0.0f, 1.0f, 0.2f, 1.4f);
```

#### 驗收條件

```txt
同一個 preset 在 velocity 40 / 80 / 120 時有明顯表情差異
但音量差距不會大到失控
```

---

### P1-2. 分開 attackIndex 與 bodyIndex

#### 問題

FM Piano 的敲擊瞬間與尾音主體本來就不同。  
目前如果只靠一個 index，很容易變成：

```txt
attack 對了，body 太刺
body 對了，attack 太鈍
```

#### 建議

內部拆成：

```txt
attackIndex
bodyIndex
```

UI 可以先不新增兩顆旋鈕，而是由 preset / sound type 自動決定比例。

#### 建議比例

| Sound Type | attackScale | bodyScale | 方向 |
|---|---:|---:|---|
| Piano | 1.2 | 0.55 | 敲擊明顯，主體柔和 |
| E.Piano | 1.6 | 0.45 | tine attack 更突出 |
| Bell | 1.4 | 0.80 | 金屬泛音保留久一點 |
| Pad | 0.4 | 0.70 | attack 慢，body 較長 |
| Bass | 1.1 | 0.80 | punch 與 body 都保留 |

#### 驗收條件

```txt
E.Piano 的 attack 比目前更清楚
但 release 不會一路刺到尾巴
```

---

### P1-3. 依 sound type 切換 body resonance

#### 問題

目前 180 / 340 Hz body resonance 比較像 acoustic body。  
所有 sound type 都吃同一套 resonance，會讓 preset 個性變少。

#### 建議

| Sound Type | Resonance 建議 |
|---|---|
| Piano | 180 / 340 Hz |
| E.Piano | 220 / 440 / 880 Hz 輕量 |
| Bell | 關閉或極輕 |
| Organ | 關閉 |
| Pad | 寬鬆低頻，不要明顯共振 |
| Bass | 90 / 180 Hz |
| Vibraphone | 低量、較乾淨 |
| Brass | 關閉或很輕 |

#### 驗收條件

```txt
Bell 不會像木箱
Organ 不會像鋼琴箱體
Bass 有低頻支撐但不糊
```

---

## 8. P2：E.Piano 3-stack 補強

P2 是讓 Electric Piano 明顯升級的項目。  
這一步才會讓 TsukiSynth 的 FM Piano 從「簡化玩具感」變成「比較像成品樂器」。

---

### P2-1. 為 E.Piano 做 3-stack mode

#### 原因

DX7 E.Piano 這類聲音通常不是單一 FM ratio 能完成的。  
它需要至少分成：

```txt
body
tine / bell attack
shimmer
```

#### 建議 stack

##### Stack A：Body

```txt
ratio = 1.0
index = 2.2
level = 0.75
decay = 650ms
feedback = 0.02
```

用途：

```txt
保留電鋼琴本體
避免聲音只剩敲擊金屬感
```

##### Stack B：Tine / Bell Attack

```txt
ratio = 14.0
index = 4.5
level = 0.30
decay = 80ms
feedback = 0.00
```

用途：

```txt
提供敲下去一瞬間的亮金屬感
```

##### Stack C：Soft Shimmer

```txt
ratio = 3.0
index = 1.4
level = 0.18
detune = +4 cents
decay = 900ms
feedback = 0.00
```

用途：

```txt
讓尾音帶一點玻璃感
避免太乾
```

---

### P2-2. 3-stack 資料結構草案

```cpp
struct FMStackParams
{
    float ratio = 1.0f;
    float index = 1.0f;
    float level = 1.0f;
    float detuneCents = 0.0f;

    float attackMs = 5.0f;
    float decayMs = 300.0f;
    float sustain = 0.0f;
    float releaseMs = 500.0f;

    float feedback = 0.0f;
};
```

#### 開發限制

```txt
只先套用在 E.Piano
其他 sound type 保持舊 single-stack
不要做完整 DX7 algorithm system
不要加 32 algorithms
不要加 sysex import
```

#### 驗收條件

```txt
新的 E.Piano preset 比舊 Electric Rhodes 更有 tine attack
尾音比舊版更自然
CPU 成本可接受
既有 preset 不受影響
```

---

## 9. 參考母本建議

### 9.1 優先參考音色

| 參考音色 | 用途 |
|---|---|
| DX7 E.PIANO 1 | Electric Piano 主參考 |
| DX7 VIBE 1 | Vibraphone preset 參考 |
| DX7 Bell / Tubular Bell | 金屬高 ratio 校正 |
| Dexed E.Piano 類 preset | A/B 聽感參考 |
| 其他 FM Piano preset | 找可用 recipe |

---

### 9.2 抄音色時看什麼

不要一開始看一堆 DX7 參數。  
先聽這幾個部分：

```txt
1. note 開頭是不是有金屬敲擊感
2. attack 是木頭、玻璃、鐘，還是鐵片
3. body 留多久
4. 尾音是乾淨還是會抖
5. velocity 大時是變亮、變吵，還是只變大聲
6. 低音區會不會糊
7. 高音區會不會像電話鈴
```

---

## 10. 建議新增的調音流程

### 10.1 最小可行流程

```txt
1. 選一個成熟 FM Piano 成品當 reference
2. 渲染同一段 MIDI
3. TsukiSynth 用目前 preset 渲染同一段 MIDI
4. 兩邊 A/B 聽
5. 用調音人話表判斷問題
6. 只調 1~2 顆參數
7. 重複比較
```

---

### 10.2 測試 MIDI 建議

用很短的 MIDI 就夠。

```txt
C3 velocity 50
C3 velocity 100
C4 velocity 50
C4 velocity 100
C5 velocity 50
C5 velocity 100
簡單和弦 Cmaj7
短旋律 4 小節
```

目的：

```txt
確認低音不糊
確認中音像樂器
確認高音不變電話鈴
確認 velocity 有表情
確認和弦不會炸成一團
```

---

## 11. Claude Code 任務包

以下可以直接貼給 Claude Code。

---

### 任務包 A：修 FM 預設一致性

```txt
Fix TsukiSynth FM parameter consistency.

Scope:
- Compare APVTS default values in PluginProcessor.cpp with FMParams defaults in FMPianoEngine.h.
- Make them consistent.
- Add tests ensuring APVTS defaults and FMParams defaults stay aligned.
- Do not redesign the FM engine.
- Do not change existing preset names unless necessary.

Suggested default direction:
- fm_ratio = 1.0
- fm_index = 4.5
- fm_brightness = 0.6 or 0.77
- fm_feedback = 0.02
- fm_attack = 0.005
- fm_release = 0.5

Acceptance:
- Plugin default FM sound and ScoreRenderer default FM sound use the same parameter values.
- Tests pass.
```

---

### 任務包 B：補 score schema 與 factory preset

```txt
Update TsukiSynth FM score schema and factory preset registry.

Scope:
- Add parser-supported FM fields to scores/schema/score.schema.json.
- Ensure fm_ratio, fm_index, fm_brightness, fm_feedback, fm_attack, fm_release are documented in schema.
- Add missing factory FM presets for Vibraphone and Brass.
- Ensure supported FM sound types and factory FM presets are not accidentally out of sync.

Suggested new presets:

Vibraphone:
- ratio = 3.0
- index = 4.2
- brightness = 0.35
- feedback = 0.02
- attack = 0.008
- release = 1.2

FM Brass:
- ratio = 1.0
- index = 5.8
- brightness = 0.65
- feedback = 0.12
- attack = 0.035
- release = 0.35

Acceptance:
- Existing score JSON still validates.
- New score JSON with FM parameters validates.
- FM factory preset count matches supported FM sound types.
```

---

### 任務包 C：修 UI 命名

```txt
Clarify FM brightness parameter naming in UI.

Scope:
- Keep the existing parameter ID fm_brightness for compatibility.
- Change user-facing label or tooltip so it reflects current behavior: body/tone modulation decay, not direct brightness.
- Do not break existing presets or saved sessions.

Suggested UI label:
- Tone Decay
or
- Body Decay

Suggested tooltip:
- Controls how quickly the FM body modulation fades.

Acceptance:
- The UI no longer implies fm_brightness directly increases brightness.
- Existing presets still load.
```

---

### 任務包 D：加 velocity-to-index

```txt
Improve FM Piano velocity response.

Scope:
- Make velocity affect FM index, attack index, and hammer noise amount.
- Keep volume velocity behavior usable.
- Do not add new UI controls yet unless necessary.
- Apply behavior carefully by sound type if needed.

Suggested direction:
- Low velocity: rounder, softer, less hammer noise.
- High velocity: brighter, clearer attack, more hammer noise.

Acceptance:
- Rendering the same note at velocity 40 / 80 / 120 produces audible timbral differences.
- High velocity should not become harsh or clipped.
- Existing presets remain usable.
```

---

### 任務包 E：分離 attackIndex / bodyIndex

```txt
Split FM Piano modulation into attackIndex and bodyIndex internally.

Scope:
- Do not expose many new UI parameters.
- Use sound type or preset rules to derive attackIndex/bodyIndex from fm_index.
- Keep old presets compatible.
- Start with simple scale factors.

Suggested scale factors:
- Piano: attackScale 1.2, bodyScale 0.55
- E.Piano: attackScale 1.6, bodyScale 0.45
- Bell: attackScale 1.4, bodyScale 0.80
- Pad: attackScale 0.4, bodyScale 0.70
- Bass: attackScale 1.1, bodyScale 0.80

Acceptance:
- E.Piano attack becomes clearer.
- Body tail does not stay overly harsh.
- Existing FM presets still render.
```

---

### 任務包 F：E.Piano 3-stack prototype

```txt
Prototype a lightweight multi-stack FM mode for Electric Piano only.

Goal:
Create a more convincing DX7-inspired electric piano sound without implementing full DX7 compatibility.

Scope:
- Do not implement full DX7 compatibility.
- Do not add 32 algorithms.
- Do not add sysex import.
- Add an internal 3-stack FM mode for E.Piano:
  1. 1:1 body stack
  2. 14:1 tine/bell attack stack
  3. soft shimmer stack
- Keep old single-stack mode available for other sound types.
- Add one new preset demonstrating the layered E.Piano sound.

Suggested stacks:

Body stack:
- ratio = 1.0
- index = 2.2
- level = 0.75
- decay = 650ms
- feedback = 0.02

Tine/Bell attack stack:
- ratio = 14.0
- index = 4.5
- level = 0.30
- decay = 80ms
- feedback = 0.00

Soft shimmer stack:
- ratio = 3.0
- index = 1.4
- level = 0.18
- detune = +4 cents
- decay = 900ms
- feedback = 0.00

Acceptance:
- Existing FM presets still render.
- New E.Piano preset has clearer bell/tine attack than old Electric Rhodes.
- CPU usage remains acceptable.
- No claim of DX7 compatibility is added anywhere.
```

---

## 12. Codex 審查任務包

以下給 Codex 做只讀審查。

```txt
Review TsukiSynth FM Piano implementation only.

Do not modify files.

Check the following:
1. Are APVTS FM defaults and FMParams defaults consistent?
2. Are parser-supported FM JSON fields all listed in score.schema.json?
3. Does the factory preset registry include all supported FM sound types?
4. Does fm_brightness UI wording match its actual behavior?
5. Does feedback wording avoid implying Yamaha DX7-compatible feedback?
6. Are existing presets preserved after changes?
7. Are new FM presets reasonable and not clipping?
8. If velocity-to-index was added, does it avoid harsh high-velocity output?
9. If attackIndex/bodyIndex split was added, does it preserve old preset compatibility?
10. If E.Piano 3-stack was added, is it limited to E.Piano and not presented as full DX7 compatibility?

Return only confirmed issues with file paths and line references.
Avoid speculative rewrite suggestions.
```

---

## 13. 建議版本順序

### v0.1：整理一致性

```txt
APVTS default = FMParams default
score.schema.json 補 FM 欄位
補 Vibraphone / Brass preset
修 fm_brightness UI 命名
```

### v0.2：讓樂器比較可彈

```txt
velocity-to-index
attackIndex/bodyIndex split
sound type resonance
```

### v0.3：Electric Piano 升級

```txt
E.Piano 3-stack mode
DX7-inspired Electric Piano preset
A/B reference workflow
```

### v0.4：再考慮進階功能

```txt
reference WAV compare tool
更多 FM preset
preset morph
JSON score 中指定 stack
```

暫時不要做：

```txt
完整 DX7 6-op
32 algorithms
sysex import
DX7 patch converter
```

這些會讓專案變大，而且目前月亮旋律還沒需要那麼重。

---



---

# 16. Analyzer / Tuner 補強：用工具抓走音，不靠耳朵猜

## 16.1 結論

這個功能要做，而且優先度很高。

TsukiSynth 已經有 `SpectrumView`，代表專案已經有「看頻率」的基礎。  
但目前 SpectrumView 比較適合看音色分布、泛音結構、能量變化，不適合單獨拿來精準判斷走音。

要抓「準不準」，最實用的功能是：

```txt
Tuner View
```

也就是像吉他調音器一樣，直接顯示：

```txt
目前偵測到的基頻是多少 Hz
最近的 MIDI note 是什麼
偏差幾 cent
```

---

## 16.2 SpectrumView 可以做什麼

SpectrumView 適合拿來看：

```txt
1. 基頻大概在哪裡
2. 泛音分布是否正常
3. 高頻是不是太刺
4. 低頻是不是太糊
5. 材質切換後頻譜形狀是否合理
6. FM ratio / index 是否造成過度 inharmonicity
```

例如彈 A4 時，理論上應看到：

```txt
基頻：440 Hz
第二泛音：880 Hz
第三泛音：1320 Hz
第四泛音：1760 Hz
```

如果泛音大量偏離整數倍，代表聲音帶有明顯 inharmonicity。  
少量偏離可以是物理建模感，偏太多就會變成鐘、電話鈴或怪異金屬聲。

---

## 16.3 SpectrumView 目前的限制

如果目前 FFT size 是：

```txt
2048 samples
```

在 44100 Hz sample rate 下，頻率解析度約為：

```txt
44100 / 2048 ≈ 21.5 Hz
```

這代表它很難分辨：

```txt
440 Hz
443 Hz
450 Hz
```

對音準判斷來說，這太粗。

如果要讓 SpectrumView 更適合看準音，可以增加高解析模式：

| FFT Size | 約略解析度 @ 44100 Hz | 用途 |
|---:|---:|---|
| 2048 | 21.5 Hz | 即時頻譜、看大概能量 |
| 4096 | 10.8 Hz | 比較細的頻譜 |
| 8192 | 5.4 Hz | 可粗略抓音準 |
| 16384 | 2.7 Hz | 較適合觀察走音 |

但要注意：

```txt
FFT size 越大，時間反應越慢
```

所以高解析 SpectrumView 適合分析長音，不適合看快速 attack。

---

## 16.4 Tuner View 才是抓走音主力

建議在 `AnalyzerPanel` 裡新增一個 tab：

```txt
SCOPE
SPECTRUM
TUNER
```

TUNER 顯示內容：

```txt
┌──────────────┐
│     A4       │
│   440.0 Hz   │
│    +0 cent   │
│   ══════●    │
└──────────────┘
```

最低功能：

```txt
1. 偵測目前基頻 frequencyHz
2. 換算最近 MIDI note
3. 顯示 note name，例如 A4 / C3 / F#5
4. 顯示 cent 偏差
5. 顯示簡單指針
```

---

## 16.5 Tuner 計算公式

### frequency → MIDI note

```cpp
midiNote = 69 + 12 * log2(frequencyHz / 440.0);
```

### 最近的 MIDI note

```cpp
nearestMidi = round(midiNote);
```

### cent 偏差

```cpp
centOffset = (midiNote - nearestMidi) * 100.0;
```

### MIDI note → note name

```txt
0 = C
1 = C#
2 = D
3 = D#
4 = E
5 = F
6 = F#
7 = G
8 = G#
9 = A
10 = A#
11 = B
```

octave：

```cpp
octave = nearestMidi / 12 - 1;
```

例如：

```txt
MIDI 69 = A4
frequency = 440 Hz
centOffset = 0
```

---

## 16.6 基頻偵測方法建議

第一版不需要做很複雜。

建議順序：

```txt
v1：autocorrelation / YIN-like pitch detection
v2：增加 confidence
v3：增加 smoothing
v4：針對低音與高音優化
```

不要只用 SpectrumView 的最高 peak 當基頻。  
因為 FM / Piano / Bell 類音色常常會出現：

```txt
泛音比基頻更大
```

如果只抓最大 peak，很容易把 880 Hz 誤判成 A5，而不是 A4。

---

## 16.7 Tuner UI 建議

### 顯示欄位

```txt
Detected Note: A4
Frequency: 440.0 Hz
Offset: +0 cent
Confidence: 0.92
```

### 指針規則

```txt
-50 cent     0     +50 cent
   |---------●---------|
```

顏色或狀態可簡化成：

```txt
abs(offset) <= 5 cent：準
abs(offset) <= 15 cent：可接受
abs(offset) > 15 cent：偏明顯
```

不一定要一開始做顏色。  
先把數字做出來最重要。

---

## 16.8 對 FM Piano 的實際用途

Tuner 可以直接回答這幾個問題：

### 問題 1：彈 A4 有沒有真的在 440 Hz？

如果顯示：

```txt
A4
440.0 Hz
+0 cent
```

代表基頻準。

如果顯示：

```txt
A4
443.0 Hz
+12 cent
```

代表偏高。

---

### 問題 2：切換材質後，基頻有沒有跑掉？

測試方式：

```txt
同一個 MIDI note
切 Piano / E.Piano / Bell / Pad / Bass / Brass
看 Tuner 顯示的基頻與 cent offset
```

如果同一顆 MIDI note 在不同材質下基頻跳動太多，代表：

```txt
sound type / material / physical model 影響了 pitch
```

這通常不是好事。

---

### 問題 3：FM ratio / index 是否讓基頻辨識困難？

如果 Tuner 顯示不穩，例如：

```txt
A4 → A5 → E5 → A4
```

可能代表：

```txt
1. 泛音比基頻太強
2. high ratio layer 太大
3. attack 太金屬
4. pitch detection 需要避開 attack 前幾十毫秒
```

這時不是立刻判斷「走音」，而是要看：

```txt
穩定段 sustain / decay 的基頻是否正確
```

---

## 16.9 SpectrumView 的補強方向

SpectrumView 仍然值得補強，但它不是 Tuner 的替代品。

建議新增：

```txt
FFT size 選項：
2048 / 4096 / 8192 / 16384

Log frequency axis：
30 Hz - 20 kHz

Peak hold：
顯示最近一段時間的 peak

Note grid：
標出 C / A / octave 參考線

Cursor readout：
滑鼠移到 peak 時顯示 frequency Hz
```

其中最重要的是：

```txt
FFT size 選項
Cursor readout
```

---

## 16.10 開發優先順序

### P0：Tuner View

```txt
新增 AnalyzerPanel / TUNER tab
顯示 note / Hz / cent
能偵測單音長音
```

### P1：SpectrumView 高解析模式

```txt
FFT size 可切 2048 / 4096 / 8192 / 16384
顯示目前解析度 Hz/bin
```

### P2：Pitch confidence / smoothing

```txt
避免 attack 瞬間亂跳
避免泛音被誤判成基頻
顯示 confidence
```

### P3：A/B reference mode

```txt
未來可顯示 reference note / current note 差異
幫助校正 FM Piano preset
```

---

## 16.11 Claude Code 任務包：Tuner View

```txt
Add a Tuner tab to TsukiSynth AnalyzerPanel.

Goal:
Provide a simple tuner view for detecting pitch accuracy without relying only on hearing or the spectrum view.

Scope:
- Add a TUNER tab beside existing analyzer views such as SCOPE and SPECTRUM.
- Detect fundamental frequency from the audio signal.
- Convert detected frequency to nearest MIDI note.
- Display:
  - note name, e.g. A4
  - detected frequency in Hz
  - cent offset from nearest equal-tempered note
  - optional confidence value
- Add a simple horizontal tuner indicator from -50 cent to +50 cent.
- Do not rely only on the highest FFT peak, because FM sounds may have stronger harmonics than the fundamental.
- It is acceptable for v1 to work best on sustained monophonic notes.

Acceptance:
- Playing A4 should show approximately A4 / 440 Hz / 0 cent.
- Playing C4, C5, A3 should show the correct nearest note.
- Switching FM sound types should not cause the detected fundamental to jump wildly during the stable part of the note.
- The tuner should avoid displaying unstable values during silence.
- Existing Scope and Spectrum views should keep working.
```

---

## 16.12 Claude Code 任務包：SpectrumView 高解析模式

```txt
Improve SpectrumView for pitch and harmonic inspection.

Scope:
- Add selectable FFT sizes:
  - 2048
  - 4096
  - 8192
  - 16384
- Display the current frequency resolution in Hz/bin.
- Keep 2048 as the low-latency default if needed.
- Add a cursor or peak readout showing frequency in Hz.
- Do not replace the new Tuner tab; SpectrumView is for harmonic inspection, Tuner is for pitch accuracy.

Acceptance:
- At 44100 Hz sample rate, the UI should show approximate frequency resolution:
  - 2048: about 21.5 Hz/bin
  - 4096: about 10.8 Hz/bin
  - 8192: about 5.4 Hz/bin
  - 16384: about 2.7 Hz/bin
- Spectrum view remains responsive at lower FFT sizes.
- Higher FFT sizes provide visibly finer frequency inspection.
```

---

## 16.13 Codex 審查任務包：Analyzer / Tuner

```txt
Review TsukiSynth Analyzer / Tuner implementation only.

Do not modify files.

Check:
1. Does the Tuner avoid relying only on the highest FFT peak?
2. Does it correctly convert frequency to MIDI note and cent offset?
3. Does it suppress unstable output during silence?
4. Does it behave reasonably on sustained monophonic notes?
5. Does the SpectrumView FFT size selector correctly update FFT size?
6. Does the UI display correct Hz/bin resolution?
7. Do existing Scope and Spectrum views still work?
8. Is the Tuner clearly presented as pitch detection, while SpectrumView remains harmonic inspection?
9. Are there any obvious performance problems with 8192 / 16384 FFT sizes?
10. Are there tests or at least manual validation steps for A4 = 440 Hz?

Return only confirmed issues with file paths and line references.
Avoid speculative rewrite suggestions.
```

---

## 16.14 手動測試流程

### 基本音準測試

```txt
1. 開啟 TUNER tab
2. 播放 A4，velocity 80，長音 2 秒
3. 確認顯示接近：
   A4 / 440 Hz / 0 cent
4. 播放 C4 / C5 / A3
5. 確認 note name 正確
```

### 材質切換測試

```txt
1. 固定播放 A4
2. 切換 Piano / E.Piano / Bell / Pad / Bass / Brass
3. 觀察穩定段 cent offset
4. 如果某個 sound type 讓基頻偏移明顯，檢查該 sound type 的 pitch / tension / ratio 計算
```

### FM Piano 測試

```txt
1. 播放 E.Piano A4
2. 避開 attack 前 50~100ms
3. 觀察 decay / sustain 段是否穩定接近 A4
4. 若 Tuner 在 A4 / A5 間跳動，檢查 high ratio layer 是否太強
```

### SpectrumView 測試

```txt
1. 切到 SPECTRUM tab
2. FFT size 設 2048，觀察 A4 peak
3. 切 8192 / 16384
4. 確認 peak 顯示更細
5. 檢查 Hz/bin 顯示是否正確
```

---

## 16.15 這項功能對月亮旋律的價值

Tuner / Analyzer 補強可以直接解決：

```txt
1. 不知道 FM Piano 有沒有走音
2. 不知道是基頻錯還是泛音怪
3. 不知道材質切換有沒有影響 pitch
4. 不知道參數調怪是音準問題還是音色問題
5. 不想只靠耳朵猜
```

因此這項功能應該排在 FM Piano 補強的前段。

建議優先順序：

```txt
1. Tuner View
2. APVTS / FMParams default 一致
3. score.schema.json 補 FM 參數
4. factory preset 補齊
5. SpectrumView 高解析模式
6. velocity-to-index
7. attackIndex / bodyIndex
8. E.Piano 3-stack
```



---

# 17. 老師回饋整理：普通、地基音色、低頻不夠沉

## 17.1 回饋來源整理

目前收到兩類很重要的音樂人回饋。

### A 老師回饋

```txt
我覺得音色蠻普通的
簡單暴力
現在蠻缺這種地基音色
```

### B 老師回饋

```txt
可惜低音不夠沉
也不夠飽滿
這個應該不太可能用調的
跟聲音音色本質有關
```

這兩段都要收進開發判斷。  
A 老師指出目前音色的可用價值。  
B 老師指出目前引擎在低頻體積感上的限制。

---

## 17.2 A 老師回饋解讀

### 「音色蠻普通的」

這句不能直接理解成負評。

在音樂製作語境裡，「普通」常常代表：

```txt
乾淨
直接
沒有過度設計
沒有塞滿效果
可以拿來當底層素材
```

對合成器 preset 來說，這是重要優點。

很多華麗 preset 單獨聽很驚豔，但進編曲後會卡住空間。  
地基音色要能疊、能混、能加工，所以不能一開始就被效果塞滿。

---

### 「簡單暴力」

這句代表聲音特徵很直接。

可以理解成：

```txt
attack 明確
聲音輪廓清楚
沒有太多修飾
能量出來得快
```

這跟 modal / physical style engine 的特性吻合。  
聲音是由模態、材質、敲擊條件長出來，不是靠大量後製包裝。

---

### 「現在蠻缺這種地基音色」

這句最重要。

它代表 TsukiSynth 目前的聲音有一個可保留定位：

```txt
地基音色
raw material
可加工的底層素材
乾淨的物理建模原料
```

這比「聽起來很華麗」更有開發價值。  
月亮旋律可以把這點寫成設計方向：

```txt
TsukiSynth 不追求每個 preset 一打開就像成品混音，
而是提供音高正確、節拍正確、材質清楚、可被編曲加工的地基音色。
```

---

## 17.3 A 老師回饋轉成工程需求

A 老師的回饋可以轉成以下規格。

### 保留乾淨底層聲音

避免預設音色塞太多：

```txt
heavy reverb
heavy chorus
heavy delay
過度 stereo widening
過度 EQ smile curve
過度壓縮
```

Factory preset 應保留 raw / dry 版本。

---

### Preset 分成 Raw 與 Polished

建議未來 preset 命名可以分層：

```txt
Cimbalom Raw
Cimbalom Wide
Cimbalom Soft Room
Struck String Keyboard Raw
Struck String Keyboard Warm Body
FM Bell Raw
FM Bell Space
```

核心原則：

```txt
Raw preset 給編曲與混音使用
Polished preset 給 demo 與快速試聽使用
```

---

### 地基音色驗收條件

```txt
1. 單音清楚
2. 和弦不糊
3. 低頻不亂堆
4. 中頻有主體
5. 高頻不過度刺耳
6. 乾聲可用
7. 加外部效果後仍有加工空間
```

---

## 17.4 B 老師回饋解讀

B 老師指出：

```txt
低音不夠沉
低音不夠飽滿
可能不是 JSON 參數能解決
跟聲音音色本質有關
```

這是非常重要的工程回饋。

它代表問題可能不在：

```txt
某個 note 寫錯
某個 velocity 寫錯
某個 release 寫錯
某個 JSON 參數太小
```

而在：

```txt
目前引擎缺少低頻 body / air / resonance / coupling 的表現
```

---

## 17.5 為什麼低音不夠沉

目前 modal style engine 的優點是：

```txt
泛音可控
attack 清楚
音高容易驗證
材質容易參數化
```

但低音的「沉」與「飽滿」通常還需要：

```txt
body resonance
soundboard / body coupling
low-mid resonance
寬頻空氣感
非線性飽和
低頻能量維持
```

單純的乾淨模態輸出可能會出現：

```txt
音高正確
泛音也正確
但體積感不足
```

這時不能只叫使用者調 JSON。  
因為 JSON 只是在現有模型內改參數，缺的東西仍然缺。

---

## 17.6 這不代表模型方向錯

B 老師的回饋不是推翻物理建模方向。

它比較像是在說：

```txt
目前 struck string / modal core 已經能產生清楚的弦聲，
但低頻體積感需要另一層 body 補強。
```

所以處理方向應該是：

```txt
保留 modal core 負責音高、泛音、敲擊反應
新增 body / resonance layer 補低頻厚度與空氣感
```

---

## 17.7 Sample Layer 的用途要擴大

原本 ROADMAP 的 Sample Layer v0 可能偏向補：

```txt
hammer impact
pick noise
attack transient
```

現在應擴大成：

```txt
attack transient
+
body resonance
+
low-frequency body support
```

也就是：

```txt
Modal engine：負責可驗證的音高與模態結構
Body/Sample layer：負責低頻體積、空氣、琴身感
```

這樣可以保留物理建模的核心，也能補掉低頻薄的問題。

---

## 17.8 Body Layer 最小規格

### 目標

新增一層很輕的 body 補強，不做完整鋼琴響板。

```txt
不是完整 soundboard simulation
不是大型 sample library
不是新鋼琴引擎
```

只是補：

```txt
low body
low-mid resonance
air / size impression
```

---

### 可行做法 A：Procedural Body Resonance

用濾波器或共振器補固定頻段。

```txt
low body band：80 ~ 180 Hz
low-mid body band：180 ~ 450 Hz
wood / box resonance：250 ~ 800 Hz
```

優點：

```txt
檔案小
可參數化
適合 AI 控制
不需要 sample 授權
```

缺點：

```txt
真實感有限
需要小心避免低頻糊
```

---

### 可行做法 B：Tiny Body Sample Layer

使用非常短、非常少量的 body resonance sample。

用途：

```txt
低頻體積
琴身空氣
attack 後的 body bloom
```

優點：

```txt
有效補厚度
比純濾波更有真實感
```

限制：

```txt
必須處理授權
不能讓專案變成 sample library
需要控制檔案大小
```

---

### 可行做法 C：Convolution / IR Body

用 impulse response 表現琴身或箱體。

優點：

```txt
自然
可以模擬空間與箱體
```

限制：

```txt
CPU 成本較高
工程複雜度較高
第一版先不做
```

---

## 17.9 建議採用順序

### P0：先用 procedural body resonance

```txt
新增簡單 body layer
不引入 sample
不增加外部檔案
可以直接參數化
```

### P1：再做 tiny body sample layer

```txt
只支援很小的 body sample
只用於低頻/低中頻補強
可關閉
預設混合比例保守
```

### P2：最後才考慮 IR

```txt
未來再評估
不放進近期目標
```

---

## 17.10 對 B 老師的回覆建議

可以這樣回：

```txt
你說的應該是對的，這比較像模態引擎本身的低頻 body 不夠，不是單純 JSON 參數能解。
我會先保留目前清楚的弦聲核心，再補一層 body resonance / low body layer，讓低音有體積感。
之後我再丟一版請你聽低頻有沒有比較能撐住。
```

這比直接說「我調 JSON」更準。

---

## 17.11 Claude Code 任務包：Body Layer 補強

```txt
Add a lightweight body resonance layer to TsukiSynth struck-string / cimbalom-style engines.

Goal:
Improve low-end weight and fullness without implementing a full piano soundboard or large sample library.

Context:
Music feedback indicates that current low notes are not deep or full enough, and this may be related to the sound character of the engine rather than score JSON parameters.

Scope:
- Reuse existing modal / struck-string engine output.
- Add an optional procedural body resonance layer.
- Focus on low and low-mid support.
- Keep CPU and binary size low.
- Make the layer parameterized and easy to disable.
- Preserve existing raw sound as an option.

Suggested parameters:
- body_amount: 0.0 ~ 1.0
- body_low_freq: default around 120 Hz
- body_low_mid_freq: default around 280 Hz
- body_decay: short to medium
- body_damping: 0.0 ~ 1.0

Do not implement:
- full piano soundboard simulation
- global sympathetic resonance
- large sample library
- convolution IR in this task
- pedal resonance

Acceptance:
- Existing Cimbalom presets can still render with the old raw character.
- New body-enhanced preset has more low-end weight than the raw preset.
- Low notes feel fuller without becoming muddy.
- Body layer can be disabled.
- Tuner still detects correct pitch during stable note segments.
```

---

## 17.12 Claude Code 任務包：Raw / Body Preset 分層

```txt
Split struck-string presets into Raw and Body-enhanced variants.

Goal:
Preserve the clean foundation sound praised by musicians while also offering fuller low-end versions.

Scope:
- Keep existing raw preset behavior.
- Add body-enhanced variants where appropriate.
- Avoid heavy reverb/delay/chorus in factory presets.
- Use naming that makes the distinction clear.

Suggested names:
- Cimbalom Raw
- Cimbalom Body
- Struck String Keyboard Raw
- Struck String Keyboard Warm Body

Acceptance:
- Raw presets remain dry and clean.
- Body presets have more low/low-mid fullness.
- Preset names clearly communicate their role.
```

---

## 17.13 Codex 審查任務包：老師回饋轉工程需求

```txt
Review whether the implementation correctly translates musician feedback into engineering changes.

Do not modify files.

Check:
1. Are raw / dry foundation sounds preserved?
2. Did the new body layer avoid replacing the existing modal core?
3. Can the body layer be disabled?
4. Does the body layer target low and low-mid support rather than adding heavy effects?
5. Are preset names clear about Raw vs Body-enhanced variants?
6. Is low-end fullness improved without obvious muddiness or clipping?
7. Does pitch detection still work on body-enhanced sounds?
8. Were large sample libraries, full soundboard simulation, and convolution IR avoided in this task?
9. Are existing Cimbalom presets backward-compatible?

Return only confirmed issues with file paths and line references.
Avoid speculative redesign suggestions.
```

---

## 17.14 新優先順序調整

根據 A / B 老師回饋，TsukiSynth 的近期優先順序調整為：

```txt
1. Tuner View：先能驗證音準
2. Raw foundation preset：保留乾淨地基音色
3. Struck String Keyboard：用現有 Cimbalom 架構擴展鍵盤敲擊弦
4. Body Resonance Layer：補低頻沉度與飽滿度
5. SpectrumView 高解析：看泛音與材質
6. FM Piano：保留為 synth / legacy flavor
7. E.Piano 3-stack：有餘力再做
```

核心判斷：

```txt
A 老師確認了 raw foundation sound 的價值。
B 老師指出 low body / fullness 是下一個要補的引擎層問題。
```

TsukiSynth 不需要把每個 preset 都做得華麗。  
它更需要同時提供：

```txt
乾淨可加工的 Raw 聲音
+
有低頻體積的 Body-enhanced 聲音
```

## 14. 最小調參 cheat sheet

如果只想先把聲音調到能用，可以照這張表。

### Electric Piano

```txt
ratio = 1.0
index = 3.5 ~ 4.2
brightness/body decay = 0.45 ~ 0.55
feedback = 0.02 ~ 0.06
attack = 0.005
release = 0.7 ~ 1.0
```

聲音太鐘：

```txt
降 index
降高 ratio layer
加 body
```

聲音太悶：

```txt
加 attackIndex
加 velocity-to-index
少量加 index
```

聲音太刺：

```txt
降 feedback
降 index
縮短 high ratio decay
```

---

### Vibraphone

```txt
ratio = 3.0
index = 3.8 ~ 4.5
brightness/body decay = 0.25 ~ 0.40
feedback = 0.00 ~ 0.03
attack = 0.006 ~ 0.012
release = 1.0 ~ 1.8
```

聲音太像電話鈴：

```txt
降 index
降 feedback
縮短 release
```

聲音太短：

```txt
加 release
但不要加太多 body resonance
```

---

### Bell

```txt
ratio = 7.0
index = 6.5 ~ 8.0
brightness/body decay = 0.15 ~ 0.25
feedback = 0.00
attack = 0.003
release = 1.5 ~ 2.5
```

聲音太刺：

```txt
降 index
降 output
加一點高頻柔化
```

---

### FM Bass

```txt
ratio = 1.0
index = 5.0 ~ 6.5
brightness/body decay = 0.65 ~ 0.85
feedback = 0.04 ~ 0.10
attack = 0.003
release = 0.12 ~ 0.25
```

聲音太糊：

```txt
降 body resonance
降 release
降 feedback
```

聲音太薄：

```txt
加 index
加低頻 resonance
```

---

## 15. 最後決策

TsukiSynth FM Piano 的正確補強方向：

```txt
保留輕量 FM 架構
修一致性
用成品音色當參考
補 preset
讓參數名稱誠實
加 velocity 表情
分開 attack/body
E.Piano 再加 3-stack
```

不要把月亮旋律變成 DX7 clone。  
它應該成為：

```txt
適合 AI JSON score pipeline 的月亮系輕量 FM 樂器
```

核心目標是：

```txt
聲音可用
preset 可理解
JSON 可控制
Plugin 與 CLI 一致
後續可以慢慢長大
```
