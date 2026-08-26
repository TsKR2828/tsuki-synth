# A4 免耳裁決包 — 亮度 EQ 應急層去留

> 產出：2026-08-24（分支 `fix/deep-physics-audit-20260716`）
> 溯源腳本：同目錄 `a4_eq_ab.py`（複製 score 到暫存目錄做 EQ 開/關版本、
> 同一顆現有 `build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe` 渲染、
> Welch PSD 量測；**本輪未動 src、未 build、原 score 檔一個位元都沒改**）
> 對象：`TODO.md` A4 —— `global.effects.eq` 高頻 shelf（2026-08-06 加入的
> 亮度補償應急層）在 8/6 激發端修正與 B1/B2 琴橋阻尼落地後還需不需要。
>
> **本文件只提供數字與各選項代價，不替月月做決定。**

---

## 0. 白話導讀（先讀這段就夠做決定）

一句話結論：**這個 EQ 目前是「零使用」狀態——repo 裡沒有任何一首曲子
真的開著它；而按文件建議值打開它，只會動到全曲能量不到 0.25% 的頻段。**

背景：8/6 那天月月審聽說「低音變大、高音變小」，當時同題開了三條線——
(1) 亮度 EQ = 頻譜補償**應急**、(2) 阻尼寬頻化 = 長期物理、(3) 激發端
根因修正。現在 (2) 已由 B1/B2 琴橋阻尼落地（A1' 月月 2026-08-22 裁決接受，
`4ef2c50`/`bef60fc`），(3) 也在 8/6 夜落地（τc keytrack + 攻擊能量正規化
amount=0.78 月月審聽定案）。A4 問的是：應急層 (1) 還要不要留、文件建議值
還對不對。

這輪量測回答的問題是：**「如果現在照文件建議把 EQ 打開，聲音會差多少？」**

- 先講最重要的事實：**全 repo 沒有任何 score 寫了 `eq` 區塊**
  （grep 整個 `scores/` 只有 schema 定義那一筆）。EQ 預設 gain 0 =
  硬 bypass，渲染位元與沒有這個功能完全相同（8/6 當天已用
  `akashic_opening_bell_001` SHA256 驗證過）。所以**不管選哪個選項，
  現有 73 檔 corpus 的渲染輸出一個位元都不會變**。
- 唯一「使用中」的是一行文件：`docs/AI_PERFORMANCE_PLAYBOOK.zh-TW.md:139`
  的起手式建議「金屬打擊系 +4~+8 dB @ 2 kHz」。這行是 8/6 修正**之前**
  寫的，它假設的「整體變暗」病因現在已經被 (2)(3) 兩條線修掉了。
- 實測照建議值 +6 dB @ 2 kHz 打開，三首金屬打擊代表曲的變化：
  - 8 kHz 倍頻程能量 +5.6~+6.0 dB —— **EQ 本身如規格運作，沒壞**；
  - 但 2 kHz 以上頻段只佔全曲能量 **0.0015% / 0.116% / 0.213%**
    （三首各自的佔比）—— 它在放大一個幾乎沒有能量的頻段；
  - 所以整曲 RMS 變化只有 **−0.02 ~ −0.19 dB**，頻譜質心只移動
    **+0.4% ~ +3.7%**（例：曼音朗月光 392.2 → 406.6 Hz）。
- 一個要知道的副作用：三首都開著 `normalize: true`，EQ 墊高峰值後
  正規化會把**整首**往下拉——水鑼低頻段因此整體 −0.33 dB。
  也就是「開亮度 EQ」在正規化曲目上實際是「高頻 +6、全曲 −0.2~−0.3」
  的交換。

白話總結：這個 EQ 是一支沒壞、但已經沒人在用、而且原病因已被物理修法
治好的拐杖。留著它不影響任何現有輸出；拆掉它也不影響任何現有輸出，
但要動 plugin 參數（存檔相容性風險）。真正的選擇是「文件那行建議
要不要改」與「程式碼要不要背著這層」。

---

## 1. 這個 EQ 是什麼（事實回顧，全部可溯源）

| 項目 | 內容 | 出處 |
|---|---|---|
| 加入時間/原因 | 2026-08-06 批二：月月審聽「全體音色低音偏大、高音偏小」（機制 = Phase H 阻尼物理化 + round-2 T60 語意修正疊加），裁決「短期補償 + 長期物理兩者都做」的**短期**那半 | `TODO.md` 2026-08-06 裁決落地節、`DEVLOG.md` 同日批二 |
| 實作 | RBJ cookbook highShelf（`BiquadFilter.h` Type::HighShelf），放在離線效果鏈**最末端**（Distortion → Compressor → Delay → Reverb → EQ），`abs(gain) < 0.005 dB` 時整段不執行 = 硬 bypass | `src/dsp/BiquadFilter.h:31-43`、`src/dsp/EffectsChain.h:86-105` |
| score 介面 | `global.effects.eq.{high_shelf_freq_hz(100–16000, 預設2000), high_shelf_gain_db(−24~+24, 預設0)}` | `scores/schema/score.schema.json:93-99`、`src/score/ScoreParser.h:270,681-684` |
| plugin 介面 | `fx_eq_freq`/`fx_eq_gain` 參數 + BRIGHTNESS 面板 | `src/PluginProcessor.cpp` |
| 驗證器接線 | `verify_score.py`：bypass 複本把 eq 歸零、nonzero-fx 偵測 | `tools/verify_score.py:435,458` |
| 定位 | documented creative 層，**不入物理主張**（比照 spectralTilt 劃界） | `DEVLOG.md` 8/6 批二 |
| 8/6 當日驗證 | gain 0 → `akashic_opening_bell_001` SHA256 位元一致；+6 dB → 3k–12k 帶 +5.67 dB、100–1k 帶 +0.01 dB | `TODO.md:268` |
| **現行使用量** | **repo 內 0 首 score 使用**（`grep -r high_shelf_gain scores/` 只中 schema） | 本輪 grep |
| 文件建議值 | 「起手式：金屬打擊系 +4~+8 dB @ 2 kHz 自行審聽」 | `docs/AI_PERFORMANCE_PLAYBOOK.zh-TW.md:139` |

當初病因後來發生的事：

- **2026-08-06 夜**：激發端根因修正（τc keytrack f^−0.32 + noteOn 攻擊能量
  正規化 amount=0.78 月月三輪審聽定案）。C2~C7 掃音 RMS spread 從
  27.3/29.7/36.3 dB 收到 8.65/8.19/8.62 dB。
- **B1/B2（2026-08 中）**：琴橋導納 + 阻尼寬頻化落地，月月 2026-08-22
  Rule 10 裁決「接受」（`4ef2c50`/`bef60fc`）。
- 也就是說：**當初讓 EQ 有存在理由的兩條「等修好」線，都已經修好並經
  月月裁決放行。**

---

## 2. 量測方法

- 代表曲（涵蓋文件建議值針對的三個金屬打擊 modal 引擎）：
  1. `scores/library/akashic/akashic_opening_bell_001.score.json`
     （tongue_drum + water_gong；8/6 當天做位元一致驗證用的同一首）
  2. `scores/examples/moonlight_sonata_movement1_yangqin.score.json`（cimbalom）
  3. `scores/examples/water_gong_clamped.score.json`（water_gong）
- 三版本：`eq_off`（原檔原樣 = 現行出貨狀態）、`eq_on6`（+6 dB @ 2 kHz，
  playbook 例值）、`eq_on4`（+4 dB，建議區間下緣）。原檔複製到暫存目錄
  後才加 eq 區塊，**repo 內原檔零改動**（git status 可證）。
- 渲染：現有 Release CLI `--batch`（未重建，未動 src）；三批各 3/3 成功。
- 量測：24-bit 正確解碼（soundfile）、雙聲道平均為 mono、Welch PSD
  `nperseg=16384`、48 kHz。指標：整曲 RMS/peak dBFS、頻譜質心、
  各倍頻程（63~16k）能量差、≥2k/≥4k/≥8k 累積能量差與佔比。

---

## 3. 數據

### 3.1 +6 dB @ 2 kHz（playbook 例值）vs 關閉

| 指標 | akashic_opening_bell | 月光曼音(yangqin) | water_gong_clamped |
|---|---|---|---|
| 曲長 | 29.6 s | 317.5 s | 10.1 s |
| 整曲 RMS（關） | −21.00 dBFS | −23.89 dBFS | −20.52 dBFS |
| 整曲 RMS 差（開−關） | **−0.02 dB** | **−0.02 dB** | **−0.19 dB** |
| Peak 差 | +0.03 dB | +0.34 dB | −0.09 dB |
| 頻譜質心（關→開） | 226.0 → 226.8 Hz (+0.4%) | 392.2 → 406.6 Hz (+3.7%) | 564.1 → 583.7 Hz (+3.5%) |
| ≥2 kHz 能量差 | +3.88 dB | +4.03 dB | +3.50 dB |
| ≥4 kHz 能量差 | +5.75 dB | +5.74 dB | +5.42 dB |
| ≥8 kHz 能量差 | +5.97 dB | +5.91 dB | +5.67 dB |
| **≥2 kHz 佔全曲能量（關）** | **0.0015%** | **0.116%** | **0.213%** |
| ≥2 kHz 佔全曲能量（開） | 0.0037% | 0.295% | 0.499% |

各倍頻程能量差（開−關，dB）：

| 倍頻程中心 | 63 | 125 | 250 | 500 | 1k | 2k | 4k | 8k | 16k |
|---|---|---|---|---|---|---|---|---|---|
| akashic_bell | −0.03 | −0.02 | −0.02 | +0.01 | +0.42 | +2.53 | +5.30 | +5.94 | +5.97 |
| 月光 yangqin | −0.09 | −0.09 | −0.08 | −0.06 | +0.22 | +2.08 | +5.27 | +5.87 | +5.91 |
| water_gong | **−0.33** | **−0.33** | **−0.33** | −0.30 | −0.09 | +1.67 | +5.22 | +5.62 | +5.67 |

三首的能量分布（EQ 關、佔全曲 %），說明為什麼 shelf 動不了整體：

| 倍頻程中心 | 63 | 125 | 250 | 500 | 1k | 2k | 4k~16k 合計 |
|---|---|---|---|---|---|---|---|
| akashic_bell | 0.02 | 47.7 | 51.3 | 0.88 | 0.04 | 0.05 | <0.001 |
| 月光 yangqin | 4.6 | 14.9 | 34.9 | 32.4 | 11.3 | 0.70 | 0.026 |
| water_gong | 0.01 | 0.03 | 29.4 | 36.9 | 32.0 | 1.75 | 0.008 |

### 3.2 +4 dB @ 2 kHz（建議區間下緣）vs 關閉

| 指標 | akashic_bell | 月光 yangqin | water_gong |
|---|---|---|---|
| 整曲 RMS 差 | −0.01 dB | −0.01 dB | −0.06 dB |
| 頻譜質心 | 226.0 → 226.5 Hz | 392.2 → 400.8 Hz | 564.1 → 576.1 Hz |
| ≥2k / ≥4k / ≥8k 能量差 | +2.59 / +3.84 / +3.98 dB | +2.68 / +3.83 / +3.94 dB | +2.41 / +3.69 / +3.85 dB |
| 8 kHz 倍頻程差 | +3.96 dB | +3.92 dB | +3.82 dB |

### 3.3 water_gong 低頻 −0.33 dB 的機制（誠實交代，不是 EQ 濾波器的錯）

RBJ high shelf 在直流處數學上恰為 0 dB，不會削低頻。−0.33 dB 來自
`export.normalize: true`：EQ 墊高了含高頻內容的峰值樣本 → 峰值正規化把
**整首**等比例往下拉。三首代表曲（以及 corpus 慣例）都開 normalize，
所以「開 EQ」在實務上是「高頻 +6 dB、全曲整體 −0.02~−0.33 dB」的交換，
低頻聲部會被連帶壓小最多 0.33 dB（akashic/yangqin 兩首峰值樣本高頻
成分少，只被拉 0.02~0.09 dB）。

---

## 4. 三個選項與各自的量化後果

### 選項一：維持現狀（功能留著、playbook 建議值 +4~+8 dB 不動）

- 對現有 73 檔 corpus 渲染輸出：**零改變**（0 首使用，gain 0 = 位元一致）。
- 後果在「未來照文件操作的人」身上：照建議開 +6 dB 得到的是
  §3.1 那組數字——8k 帶 +5.9 dB，但整曲 RMS ≈ 0、質心 +0.4~3.7%，
  外加 normalize 曲目全曲 −0.02~−0.33 dB 的隱性代價（文件目前沒寫這點）。
- 風險：文件那行寫於 8/6 修正之前；「抵銷整體變暗」的病因描述已過時，
  照做的人是在治一個已經治好的病。

### 選項二：調整建議值／文件（功能留著、改寫 playbook:139）

- 對現有渲染輸出：**零改變**（同上）。
- 可改的內容（數字上的差異）：
  - 把「起手式 +4~+8 dB」降級為「預設不開；僅在成品仍覺得暗時作為
    creative 微調」——因為病因線 (2)(3) 都已落地。
  - 若保留數字建議，+4 dB 的效果是 +6 dB 的約 2/3（8k 帶 +3.8~4.0 vs
    +5.6~6.0 dB，§3.2 實測）。
  - 補寫 normalize 交互：開 shelf 會讓正規化後全曲 −0.02~−0.33 dB
    （視峰值樣本的高頻含量）。
- 成本：只動一行文件 + 可能一段 DEVLOG；程式碼零改動、零風險。

### 選項三：移除應急層（拆 schema/parser/引擎/plugin/驗證器接線）

- 對現有渲染輸出：**零改變**（0 首使用；gain 0 位元一致已於 8/6 驗證）。
- 要拆的面：`score.schema.json` eq 區塊、`ScoreParser.h`（讀取+驗證兩處）、
  `EffectsChain.h`/`BiquadFilter.h` HighShelf、`ScoreRenderer.h` 接線、
  `verify_score.py` bypass/nonzero-fx 邏輯、plugin 端 `fx_eq_freq`/
  `fx_eq_gain` 參數與 BRIGHTNESS 面板、playbook:139。
- 量化風險：
  - **plugin 參數移除 = 存檔相容性風險**——任何在 DAW 專案裡動過
    BRIGHTNESS 面板的既有 session，重開時參數消失（A9 的 Cubase
    專案存讀位元全等主張是在「參數集不變」前提下做的）。
  - 已寫入外部（repo 外）score 的 `eq` 區塊會從「有效」變「schema 驗證
    失敗」——repo 內 0 首，但無法保證月月手上沒有。
  - 換得的是：少一層要維護/驗證的 creative 路徑（verify_score 的 eq
    歸零複本邏輯可一併刪）。
- 註：此選項屬 src 改動，本輪（禁動 src）只列後果，未實作。

---

## 5. 這份包沒有回答的事（誠實邊界）

- **聽感**：≥2 kHz 佔比 0.0015~0.213% 是能量說法；人耳對 2~5 kHz 最敏感，
  +6 dB 的尾音「空氣感」在能量上微小但**不保證**聽不出來。本包的立場是
  把能量數字交出來，聽感判斷本來就是月月審聽的領域——而 A4 的前提是
  病因已修，所以「還暗不暗」如果要驗，得是月月聽現行版本說了算。
- 只測了三首代表曲（涵蓋三個金屬 modal 引擎與文件建議值的適用對象）；
  沒測 piano/FM/custom——但文件建議值本來就只指名金屬打擊系，且
  FM/Custom 在 8/6 已明文域外。
- 8/6 修正「之前」的引擎本輪無法重渲染（需要回退並重 build，違反本輪禁 build），
  所以「EQ 當時補的暗到底多暗」引用的是 8/6 當天的存檔數字
  （C2~C7 spread 27.3~36.3 dB），不是本輪重測。

---

## 6. 復現路徑

```
python reports/decision_packets/a4_eq_ab.py <可寫暫存目錄>
```

本輪實際產物（暫存，不進版控）：
`C:\Users\admin\AppData\Local\Temp\claude\C--Users-admin-Desktop-Claude\05dce887-3f84-45b0-b043-e4bd719826ff\scratchpad\a4\`
（`eq_off/ eq_on/ eq_on4/` 三組 score + `render_off/ render_on/ render_on4/`
九個 WAV + `a4_metrics.json` / `a4_metrics_plus4.json` 原始量測值）
