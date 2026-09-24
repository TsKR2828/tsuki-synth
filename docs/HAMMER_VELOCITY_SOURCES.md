# 槌頭速度映射溯源（B7 Phase 0 第 1 項）

> 建立：2026-09-14　工兵：Sonnet（WF0914-B7P0）
> 對應 `docs/workcards/B7.md` §2.2／§4.2／§6 Phase 0 第 1 項交付物、
> `docs/B7_PHASE0_DATA.zh-TW.md` §2.1（表 A）／§4.3。
> 體例比照 `docs/RADIATION_POWER_SOURCES.md`。
>
> **本文件是轉寫，不是新研究**：不做任何新的 WebSearch/WebFetch，不引用
> `docs/B7_PHASE0_DATA.zh-TW.md`（下稱 `B7_PHASE0_DATA`）與 `docs/workcards/B7.md`
> 之外的任何數字。所有原文逐字引述、頁碼、溯源等級皆照抄上述兩份文件，
> 未做任何新的核對或推導。

---

## 0. 白話

B7 這條力鏈最上游的環節——「琴鍵按多重（MIDI velocity）→ 槌頭飛多快
（真實 m/s）」——原本查無顯式映射函數（B7.md §2.2 第一版的結論）。
`docs/workcards/WF0907_R4_B7_phase0_data.md`（研究卡）補搜之後，在
Goebl (2003) 博士論文裡找到一條**論文自己寫出來的封閉形式公式**，並用
另外兩篇期刊論文的三個獨立對照點驗證這條公式「自洽」（不是「準確」——
差別見 §3）。

```
hammerVelocityMps(midiVelocity) = 2 ^ ((midiVelocity - 52) / 25)
```

**這條公式現在有出處、可以抄進文件**，但**還不能直接落地進 `src/`**：
它會改動 `ScoreParser.h` 已登記、且已被 `physics_verify.py` 1d 判定中的
「振幅正比於 velocity」關係，屬於 README Rule 10 的情境（見 §5）。
本文件只完成「補公式、補出處」這一步，落地留給 B7P1。

---

## 1. 映射公式與出處

**封閉形式（原文已核，非本專案自創）**：

```
hammerVelocityMps(midiVelocity) = 2 ^ ((midiVelocity - 52) / 25)
```

**出處**：Goebl, W. (2003), *The Role of Timing and Intensity in the
Production and Perception of Melody in Expressive Piano Performance*,
博士論文, Univ. Graz / OFAI TR-2003-28。

**原文逐字引述（正式寫法，MIDI velocity 對槌速取對數）**：

> Ch.3 §3.7（p.78）式 (3.2)：**"was chosen to be MIDIvel = 52 + 25 · log2(fhv)"**
> （`fhv` = final hammer velocity, m/s；反解即上面的封閉形式）

**同一式在同一本論文裡另外出現三次，寫法一致**（`B7_PHASE0_DATA` §2.1
A13 列，四處合計）：

- Ch.2 §2.3 註 23（p.40）：**"a logarithmic map was always used:
  MIDIvelocity = 52 + 25 · log2(FHV)"**
- Ch.4 註 5：**"MIDI velocity = 52 + 25 · log2(hammer velocity)"**
- Ch.4 註 14：**"Using the same velocity map as in Experiment I–III"**
  （後接同一式）

四處一致，排除「單一處印刷錯誤」的可能，且註 14 明說整個知覺實驗系列
都用同一張 map。

**性質（必須跟著寫進程式註解，不寫就是誤導）**：原文用詞是
**"was chosen to be"**（被選定為）——這是 **Bösendorfer SE290 電腦控制
平台鋼琴系統在該研究中採用的 velocity map（一個裝置慣例）**，**不是從
物理第一原理推出來的自然律**。

---

## 2. 三個錨點與兩個實測極值

| 項目 | 數值 | 條件 | 出處 | 有沒有套 +14% 槌速校正 |
|---|---|---|---|---|
| MIDI **40 → 0.7 m/s**、**60 → 1.25 m/s** | 表情演奏中等力度區間 | Goebl, Bresin & Galembo, *JASA* 118(2), 1154–1165 (2005), General Discussion，**p.1163**（2026-09-09 第二次複核更正頁碼，`B7_PHASE0_DATA` 上一版誤寫 p.1162） | 原文：**"between 40 and 60 MIDI velocity units (0.7–1.25 m/s)"** | **有**（該篇槌速資料全部 +14%，見 §3） |
| MIDI **77 → 2.0 m/s** | 同步對齊用的「較大聲」門檻 | Goebl & Bresin, *JASA* 114(4), 2273–2283 (2003), §II.C 末段（p.2275） | 原文：**"hammer velocity over 2 m/s or 77 MIDI velocity units"** | **沒有**（該篇未套用，見 §3） |
| 實測**下限 0.18 m/s**（pressed touch）／**上限 6.8 m/s**（struck touch） | 三台平台鋼琴、兩位鋼琴家、兩種觸鍵；極 soft 只能用按壓觸鍵達成、極 loud 只能用擊打觸鍵達成 | Goebl, Bresin & Galembo (2005)，**p.1163**（同上更正） | 原文：**"minimum 0.18 m / s or 50.0"**（後接 dB-pSPL）與 **"maximum 6.8 m / s or 110.4 dB-pSPL"** | **有** |
| 上面那條映射式本身 | — | Goebl (2003) 博士論文 | 式 (3.2) | **沒有** |

**A12 的交叉檢查（`B7_PHASE0_DATA` §2.1 已算，本文件轉寫）**：把上表三個
MIDI 值代入映射式：

| 輸入 | 映射式算出 | 論文獨立報的值 | 一致？ |
|---|---|---|---|
| MIDI 40 | 0.717 m/s | 0.7 m/s | 相符（印刷精度內） |
| MIDI 60 | 1.248 m/s | 1.25 m/s | 相符 |
| MIDI 77 | 2.000 m/s | 2.0 m/s | 相符 |
| MIDI 110 | 4.993 m/s | Askenfelt「forte ≈ 5 m/s」（`B7_PHASE0_DATA` A6/A5） | 相符 |
| MIDI 127 | 8.000 m/s | 實測最大 6.8 m/s | **高於實測極值 18%**（見 §4） |
| 槌速 0.18 m/s（最弱實測） | 反解 MIDI −9.85 | — | **落在 MIDI 0 以下**（見 §4） |

---

## 3. ⚠️ 必須跟著寫進程式註解的三件事（不寫就是誤導）

### (1) 兩組來源之間有一個 +14% 的槌速刻度差，是原文自己講明的

Goebl, Bresin & Galembo (2005) **註 9**（`B7_PHASE0_DATA` 逐字核對，
**p.1164**）：

> "the hammer velocity data was corrected for that resulting in values
> in-"（原文在此換行）"creased by 14%."
> 緊接下一句：**"This correction was not applied in Goebl and Bresin
> 2003."**
> 校正理由（同註）：**"differences in radius between the accelerometer
> placement on the hammer shank"**（後接 "and striking point at the
> hammer crown"）——加速度計裝在槌桿、打擊點在槌冠，半徑不同。

所以上表的三個錨點**不是同一把尺量出來的**：

| 錨點 | 出處 | 有沒有套 +14% 校正 |
|---|---|---|
| MIDI 40 → 0.7、MIDI 60 → 1.25 | Goebl et al. **2005** | **有** |
| MIDI 77 → 2 | Goebl & Bresin **2003** | **沒有**（註 9 明說未套用） |
| 極值 0.18／6.8 | Goebl et al. **2005** | **有** |
| 映射式本身 | Goebl **2003 博士論文** | **沒有**（`B7_PHASE0_DATA` 在該論文全文檢索
`increased by`／`radius` 字面零命中，判定未套此校正——**這是「檢索不到」
的推論，不是原文明寫「未套用」**） |

**因此 → 不可以寫「三個獨立量測點交叉驗證全中、殘差 0.5%」。**

正確寫法：**「三個對照點與本式相符到印刷精度，但兩組來源之間存在原文
言明的 ≥14% 系統性刻度差，且三個對照點很可能本來就是用同一條 map 換算
出來的（兩篇論文都沒有寫這些 m/s 是怎麼換算來的，吻合到印刷精度，最省事
的解釋是同一條 map 反算出來——這是 `B7_PHASE0_DATA` 的推論，原文沒有
這樣寫）。**

**系統性偏差 ≥ 殘差**：算出來的殘差是 ≤0.5%（0.717 vs 0.7、1.248 vs
1.25、2.000 vs 2），而兩組來源自己的槌速刻度就差 14%。**殘差比刻度差
小一個量級，代表殘差量到的是「同一條 map 的自洽」，不是準確度。**

**可用精度下限**：以 **±14%** 為底（若峰值聲壓正比於槌速一次方，約
**±1.14 dB**：`20·log10(1.14) = 1.138`）。**這是量級說明，不是新容差**
——本文件不提出任何 GATE 門檻數字（Rule 2）。

### (2) 定義域

**MIDI 20–120（≈0.41–6.6 m/s）有實測支撐**；兩端外為外推。落地時建議
在 MIDI < 20 與 > 120 clamp 到實測極值 **0.18 / 6.8 m/s**（體例比照
`HammerImpulse.h` 既有的 `interpAnchorsFlat()`）。見 §4 細節。

### (3) 性質

原文寫的是 **"was chosen to be"**——這是 Bösendorfer SE 系統的**裝置
慣例**，不是物理定律；它的可信度來自與三個獨立量測點一致，不是來自
「論文說了算」。

---

## 4. 定義域外的已知失效行為

- **MIDI 127 由此式得 8.0 m/s**，比實測最大 6.8 m/s **高 18%**——公式
  在上端外推會高估。
- **槌速 0.18 m/s（最弱實測）反解得 MIDI −9.85**，落在 MIDI 0 以下——
  **此式表示不了極弱按壓觸鍵**，這是它的已知邊界，不是實作 bug。
- 兩端建議 clamp 到 A3 的實測極值 0.18 / 6.8 m/s，而不是任由公式外推
  （`B7.md` §4.2 已同樣建議）。

---

## 5. 尚未裁決的兩個前置（本文件不裁決，供 B7P1 處理）

**(a) 引擎的 0–1 力度 proxy 到底對應哪一種定義，尚未裁決**：
`B7_PHASE0_DATA` §3.4 指出引擎裡至少有三條不同的 velocity 路徑——

| 路徑 | velocity 從哪來 | 與 MIDI 0–127 的關係 |
|---|---|---|
| 插件（live MIDI） | `juce::Synthesiser::startNote(note, velocity, …)` | JUCE 慣例 = MIDI / 127 |
| score / CLI | `src/score/ScoreParser.h:313`，`readNumber(*e, "velocity", velocity, 0.0, 1.0)` | 與 MIDI 沒有換算定義 |
| MIDI 轉譜器 | `tools/midi_to_tsukisynth.py::velocity_for()`：`profile.base_velocity × (source_velocity / 90.0)`，clamp 到 0.12–0.92 | 不是 MIDI/127，是 `/90` 再乘 profile 基準並夾限 |

映射式的 `MIDI` 值該對應哪一條路徑，本文件不裁決，留給 B7P1。

**(b) 落地會動到既有已判定 GATE 與既有渲染輸出**：
`src/score/ScoreParser.h:295–308` 的註解登記「`ModalResonator::excite()`
是 `currentAmp = baseAmp * velocity`，振幅正比於 velocity」，且明寫
**"This is not just a design intent -- it is machine-verified"**，指向
`tools/physics_verify.py` 的 1d 判定（`ROADMAP_PHYSICS.md` 已登記為
**已判定 GATE**）。把 velocity→槌速換成本文件這條指數律，等於改寫既有
的 velocity→振幅關係，會動到 1d 這條已判定 GATE，且必然改變既有 score
的渲染輸出——**這是 README Rule 10 的情境：必須停下寫前後對照報告，
不得自行落地**。本文件不落地任何程式碼，只完成溯源。

---

## 6. 量測力度時的兩條硬性注意事項（`B7_PHASE0_DATA` §2.2／§3.2 轉寫）

**(1) CLI 預設 `normalize=true`，絕對不能直接量 WAV 峰值。**
`--render` 會把輸出峰值拉到 0.95，任何「velocity 改變 → 音量差幾 dB」的
量測**必須讀渲染 manifest 的 `pre_normalize_peak` 欄**（`src/cli/
RenderApp.cpp` 寫出，`tools/verify_score.py` 也是讀這一欄）。直接量 WAV
得到的是正規化後的值。

**(2) 引擎 piano 的「動態範圍」隨音高變 10.6 dB，成因未查。**
在同一個（本專案自選的）下限 velocity 0.02 → 1.00 之間，`B7_PHASE0_DATA`
§3.2 實測：

| 音 | 0.02 → 1.00 的動態範圍 |
|---|---|
| C2 | **49.52 dB** |
| C4 | **60.08 dB** |
| C7 | **49.78 dB** |

**成因至今未追查，本文件不主張成因。** 兩個直接後果：
(a) 任何動態範圍 GATE 必須分音域寫，寫成單一全域數字會在 C2／C7 被打臉；
(b) 「引擎動態範圍 = 60.1 dB」不是引擎的客觀性質，是「下限選在 0.02」的
產物（下限 0.01 → 67.4 dB、0.05 → 51.9 dB，`B7_PHASE0_DATA` §3.2）。
GATE 必須先訂死下限並說明理由，否則可被調成任何值。

---

## 7. 引用清單

| # | 出處 | 取得方式（依 `B7_PHASE0_DATA`） | 本文件用到什麼 |
|---|---|---|---|
| 1 | Goebl, W. (2003), *The Role of Timing and Intensity…*, 博士論文, Univ. Graz / OFAI TR-2003-28 | 原文全文（`B7_PHASE0_DATA` 重新下載完整 PDF，`pdftotext` 逐字核對） | §1 映射式（Ch.3 式 3.2）、§1 四處出現記錄（`B7_PHASE0_DATA` A12/A13） |
| 2 | Goebl, Bresin & Galembo, *JASA* 118(2), 1154–1165 (2005) | 原文全文 | §2 三錨點中的兩個（MIDI 40/60）與兩個實測極值（0.18/6.8）、§3 註 9 的 +14% 校正逐字引述（`B7_PHASE0_DATA` A1/A3，註 9） |
| 3 | Goebl & Bresin, *JASA* 114(4), 2273–2283 (2003) | 原文全文 | §2 第三個錨點（MIDI 77 → 2 m/s）（`B7_PHASE0_DATA` A2） |
| 4 | Askenfelt & Jansson, "From touch to string vibrations"，KTH 五講義 | 原文全文（`B7_PHASE0_DATA` 第三輪直接 WebFetch） | §2 交叉檢查表 MIDI 110 對照點（`B7_PHASE0_DATA` A5/A6） |
| 5 | `src/score/ScoreParser.h:295–308`／`:313` | 本專案原始碼（本文件唯讀查看，未改動） | §5(a)(b) 引擎既有 velocity 路徑與已判定 GATE 的引用 |
| 6 | `tools/midi_to_tsukisynth.py::velocity_for()` | 本專案原始碼（唯讀） | §5(a) 轉譜器路徑 |
| 7 | `B7_PHASE0_DATA.zh-TW.md` §2.1（表 A）／§3.2／§3.4／§4.3 | 本專案既有研究卡產出（本文件的唯一轉寫來源） | 全文件 |
| 8 | `docs/workcards/B7.md` §2.2／§4.2 | 本專案既有施工卡 | 全文件（結構與措辭比對） |

---

## 8. 狀態

- [x] 映射公式已找到、出處已核（Goebl 2003 博士論文式 3.2，四處一致）
- [x] 三個錨點與兩個實測極值已轉寫，附出處與頁碼
- [x] +14% 槌速刻度差已完整轉寫，措辭已改為「系統性偏差 ≥ 殘差」，
      **未寫**「三點交叉驗證全中、殘差 0.5%」這種會誤導的說法
- [x] 定義域（MIDI 20–120）與域外已知失效行為（MIDI 127 高估 18%、
      MIDI < 0 表示不了極弱觸鍵）已記錄
- [x] 引擎 0–1 力度 proxy 對應哪條路徑——**尚未裁決**，本文件保留為
      open item，不自行裁決
- [x] 落地會動到 `physics_verify.py` 1d 已判定 GATE 與既有渲染輸出——
      **README Rule 10 情境**，本文件不落地任何程式碼，只完成溯源
- [x] 兩條量測注意事項（`pre_normalize_peak`、動態範圍隨音高變 10.6 dB
      且成因未查）已轉寫，未新增任何未溯源主張

**本文件不做的事**：不落地 `HammerImpulse.h` 新函式（B7P1 範圍）、不寫
Rule 10 前後對照報告（同上）、不裁決引擎 proxy 對應哪條路徑（規劃者/月月
範圍）、不引用本文件之外的任何新數字。
