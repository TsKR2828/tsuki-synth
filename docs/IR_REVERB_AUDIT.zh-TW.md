# IR / 卷積殘響現況稽核

> 稽核範圍：純讀碼 + 文件，未改動任何程式。分支 `fix/deep-physics-audit-20260716`，
> HEAD `88bdfac`。所有行號對應此 commit。
> 稽核目的：回答「讀 IR 檔調 Reverb」這個做法是否合理，以及與專業卷積殘響慣例的落差在哪。

## §0 白話結論（先回答月月）

**「讀 IR 檔案來做 reverb」這件事本身沒有錯**——JUCE 的 `dsp::Convolution`就是設計來吃一個
WAV 當脈衝響應的，這是所有卷積殘響外掛的核心機制，方向沒問題。

但**目前的實作方式，站在專業卷積殘響慣例來看，確實只做了「接上引擎」這一步，
沒有做「把它做成一個可用的殘響工具」該有的配套**。具體說：

- 訊號流是對的：載入 IR → 取代演算法殘響 → 手動 dry/wet 混音，這個骨架合理，也沒有明顯的
  DSP 錯誤（详见 §1）。
- 但音樂人熟悉的卷積殘響外掛（Waves IR-1、Altiverb 等）通常會給：可調 predelay、IR 頭尾
  trim、direct on/off、IR 增益校準——這些**一個都沒有**。使用者能做的只有「換一個 IR 檔」和
  「轉那顆共用的 Reverb Mix 旋鈕」，Room Size 和 T60 兩顆旋鈕在 IR 模式下**完全失效但 UI
  沒有變灰、沒有任何提示**，這才是音樂人會皺眉的地方——不是「不能用」，是「用起來像半成品，
  而且會誤導」。
- 更根本的落差：這個專案花了大量物理推導做「演算法殘響」的 T60（Sabine/Eyring，見
  `docs/SCENE_REVERB_DESIGN.zh-TW.md`），但 IR 這條路完全在那套誠實分層之外——IR 不進 score
  schema、CLI 渲染路徑、`melody_verify.py` 驗證鏈，也不進使用者自訂 preset（`.tsukipreset`）。
  它是一個「只活在外掛 GUI 手動操作那一刻」的孤立功能，存起來的 preset 檔案重新載入後
  IR 会静默消失、退回演算法殘響——這是本次稽核發現的唯一一個**可被稱為 bug**的問題
  （§2 表格「IR 進 preset」列），其餘多是「功能不完整」而非「功能寫錯」。

一句話：**方向對、地基沒問題，但只搭了骨架、没装内装，且骨架的裂缝（preset 遺失 IR）目前
没人告诉使用者**。是否要补内装、要补到什么程度，是取舍题（§4），不是对错题。

## §1 訊號流實況圖

### 1.1 外掛（Plugin）路徑 —— 唯一支援 IR 的路徑

```
使用者按 Load（*.wav）
  └─ PluginEditor.cpp:673  proc.loadReverbIRFile(file, error)
       └─ PluginProcessor.cpp:760 loadReverbIRFile()
            1. 用 AudioFormatReader 讀檔頭，算 seconds = lengthInSamples / sampleRate
            2. seconds > 30.0 直接拒絕（註解：「matches the score schema's reverb.decay ceiling」——
               但這個 30s 上限是原始檔案長度，不是 trim 之後的可聽長度）
            3. effectChain.loadImpulseResponse(file)  →  EffectChain.h:89
                 convolution.loadImpulseResponse(file,
                     Stereo::yes,     // 立體聲載入
                     Trim::yes,       // 修掉頭尾靜音
                     0,               // size=0 → 用原始長度，不強制裁切/延長
                     /*Normalise 用預設值 Normalise::yes*/)  // 未顯式傳，等於「有」正規化
            4. reverbIRPath / reverbIRName / reverbIRSeconds 存進 processor 成員變數
               （reverbIRSeconds 用的是「原始檔長」，不是 trim 後的長度——tail 估計因此偏保守，
               不會截斷，但也不精確）
            5. switchModeToIR=true 時，把 fx_reverb_mode 參數扳成 1（IR）

每個音訊 block（EffectChain.h:108 processBlock）：
  irMode = (fx_reverb_mode >= 0.5) && hasImpulseResponse() && numSamples <= maxBlock
  鏈：Distortion → Compressor → Delay → 〔算法 Reverb 或 IR 二選一〕→ 高頻補償 Shelf
  - irMode == false：Delay 輸出直接進 SimpleReverb（room size / T60 兩顆參數在這裡生效）
  - irMode == true ：
      a) 先把 Delay 輸出複製一份存進 dryBuffer（這是「乾訊號」快照，取樣點在 Delay 之後、
         Reverb 之前——即 IR 模式下完全跳過 SimpleReverb，兩者互斥、不是並聯）
      b) juce::dsp::Convolution::process() 對 buffer 做原地卷積（濕訊號）
      c) 逐樣本用 fx_reverb_mix（同一顆旋鈕，算法/IR 共用）做
         dry*(1-mix) + wet*mix 交叉淡化
  - Room Size / T60 兩顆參數在 irMode==true 時被程式完全忽略（EffectChain.h:141/151/153-156），
    但 PluginEditor 沒有把這兩顆旋鈕 setEnabled(false)，UI 上看起來仍是「活的」。
  - Convolution 用預設建構子 `juce::dsp::Convolution convolution;`（EffectChain.h:232）
    ＝ zero-latency、uniform-partitioned 演算法。JUCE 文件原話建議「reverb 用途的長 IR」
    改用 NonUniform 建構子（headSize ≥ 256）以省 CPU，這裡沒有採用。

State（DAW session）：
  PluginProcessor.cpp:699  getStateInformation() 把 reverbIRPath 寫進 state（"reverb_ir_path"）
  PluginProcessor.cpp:739  setStateInformation() 讀回 reverb_ir_path，檔案還在就重新
                            loadReverbIRFile(..., switchModeToIR=false)；檔案不在就靜默退回算法殘響
  → DAW 存檔/開檔這條路徑「有」把 IR 路徑存進去，行為正確。

User Preset（.tsukipreset，PresetManager.h）：
  saveUserPreset() 只 apvts.copyState() —— 只存 APVTS 參數（含 fx_reverb_mode 這個 0/1 開關），
  不存 reverbIRPath / reverbIRName。
  loadUserState() 只 apvts.replaceState()，完全沒有處理 IR 路徑。
  → 若使用者存一個「IR 模式」的 user preset，重載後 fx_reverb_mode 仍是 1，
    但 hasImpulseResponse()==false ⇒ EffectChain 的 irMode 判斷式失敗
    ⇒ 靜默退回算法殘響（用當時的 T60/Size 參數值，很可能不是原本設計的聲音）。
    使用者不會收到任何錯誤或警告。這是本次稽核唯一判定為「bug」等級的落差。
```

### 1.2 CLI / Score 渲染路徑 —— 完全沒有 IR

```
scores/schema/score.schema.json:58  global.effects.reverb 只允許 { decay, wet } 兩個鍵
                                     （additionalProperties:false，沒有 ir_path 之類的欄位）
  ↓
src/score/ScoreRenderer.h:1260-1262  fxp.reverbEnabled/reverbWet/reverbDecaySeconds
                                     直接對應 schema 的 decay/wet
  ↓
src/dsp/EffectsChain.h（CLI 專用、與外掛的 src/effects/EffectChain.h 是兩個不同檔案！）
  只 include SimpleReverb.h，完全沒有 juce::dsp::Convolution / IR 的任何蹤跡
  reverb.setDecayTime(p.reverbDecaySeconds) / reverb.setMix(...)  ← 純算法路徑

tools/scene_reverb.py + docs/SCENE_REVERB_DESIGN.zh-TW.md（場景→殘響物理推導，Sabine/Eyring）
  輸出也只是 global.effects.reverb.{decay,wet} 這兩個數字，同樣不碰 IR。

⇒ 結論：IR 卷積殘響是「外掛 GUI 手動操作限定」的功能，CLI 批次渲染 / score 驅動的整條
  生產線完全用不到它，也沒有管道把 IR 接進去（schema 沒開這個欄位）。
```

### 1.3 驗證鏈交界（melody_verify.py / HostProbe）

```
tools/melody_verify.py:301-313
  rev = fx.get("reverb") or {}
  reverb_decay = float(rev.get("decay") or 0.0)        ← 直接讀 score 檔的 reverb.decay 數字
  effective_tail = max(dry_T60, reverb_decay)          ← 兩者取較大值當「有效殘響」

  這個 reverb_decay 100% 來自 score JSON 裡 authored 的算法 T60 數值，跟「有沒有載入 IR」
  完全無關——因為 CLI 渲染路徑本來就不會載 IR（見 1.2）。所以理論上：
    - CLI 批次驗證：不可能失準，因為 IR 從未參與這條路徑。
    - 外掛內手動載入 IR 後再用某種方式餵給驗證鏈：目前找不到這樣的路徑存在
      （melody_verify 只吃 score.json + CLI 渲染出的 wav，不吃外掛即時狀態）。

tests/host_probe.cpp:94-95
  L2 HostProbe 用的 sentinel score 明確聲明「reverb/delay wet = 0」的 FX-FREE 渲染，
  刻意避開任何殘響（含 IR）對音高判定的干擾。
  ⇒ 目前的三層驗證（L1 melody_verify / L2 HostProbe / L3a Cubase 掃描，依 memory 記錄）
    沒有任何一層實際跑過 IR 卷積路徑——這不是「失準」，而是「完全沒被驗證覆蓋」。
    IR 這條路徑目前唯一的品保手段是使用者手動試聽。
```

## §2 與專業卷積殘響慣例對照表

| 專業慣例項目 | 現況 | 判定 |
|---|---|---|
| **Dry/Wet 混合** | 有，逐樣本平滑（`mixScratch` + smoothed `fx_reverb_mix`），演算法/IR 共用同一顆旋鈕 | 已有 |
| **Direct off（純送 aux 用）** | 沒有獨立開關；IR 模式下 dry 訊號永遠混入，無法做「100% wet 送 aux bus」的送收架構 | 缺 |
| **Predelay（可調的送前延遲）** | 沒有任何 predelay 參數；IR 本身內含的預延遲原封不動保留，但使用者無法額外加/減 | 缺 |
| **IR 增益正規化** | 有：`loadImpulseResponse` 第 5 參數用 JUCE 預設值 `Normalise::yes`（未顯式覆寫，等同啟用），不同 IR 檔换用時響度不會亂跳 | 已有 |
| **採樣率轉換** | 有：JUCE `Convolution` 文件明載「載入時視需要自動 resample」，`prepare()` 給的 spec.sampleRate 就是目標值，換 IR 檔取樣率不同不會出錯 | 已有 |
| **IR 頭尾 Trim** | 有基本版：`Trim::yes` 自動修掉頭尾靜音；但**没有使用者可調的 trim（start/end 拖曳）**，无法手动去掉不要的 predelay 或截短拖尾省 CPU | 部分有／缺可調版本 |
| **Early reflections / Tail 分離控制** | 沒有；IR 整段當一個黑盒子卷積，無法分開調 ER 增益與 tail 增益 | 缺（進階功能，多數平價外掛也沒有） |
| **CPU 優化（長 IR）** | 用 JUCE 預設建構子＝zero-latency uniform-partitioned；JUCE 文件建議 reverb 用途長 IR 改用 `NonUniform` 建構子省 CPU，這裡沒採用。30s 上限的 IR 若真的拿來用，CPU 負擔會偏高 | 缺 |
| **延遲補償（PDC）** | 不適用——用的是 zero-latency 建構子，JUCE 保證延遲=0，沒有可補償的延遲 | 不適用 |
| **UI：模式切換時停用失效控制項** | 沒有；Room Size / T60 兩顆旋鈕在 IR 模式下完全不生效但畫面上仍可操作、無變灰或提示 | 缺 |
| **狀態持久化：IR 路徑進 preset** | DAW session state 有存（`reverb_ir_path`），但**使用者自訂 preset（.tsukipreset）沒存**，重載後靜默退回演算法殘響且無警告 | **缺（bug 等級）** |
| **參數自動化下的載入時機競態** | `loadImpulseResponse` 是 wait-free、背景執行緒載入，`irMode` 判斷式含 `hasImpulseResponse()`，載入完成前自動退回算法殘響，不會產生未初始化卷積的爆音 | 已有 |

## §3 音樂人可能說「不是這樣用」的原因分析

依據 §1/§2 的實況，音樂人的疑慮大概率落在以下幾點（依可能性排序，非月月要的排序）：

1. **「殘響模式」和「殘響 profile」共用一顆 Load 按鈕，載 `.wav` 是真 IR、載 `.json` 是換算法
   T60/wet 數值**（PluginEditor.cpp:673-676）。这两件事在音乐人的心智模型里是完全不同的操作
   （一个是"给我一个空间的声学指纹"，一个是"帮我调旋钮"），用同一颗按钮、只靠副檔名分流，
   容易讓人誤以为「JSON 也是某种 IR」或反过来，是最直觉的「这样搞混了」抱怨来源。
2. **IR 模式下 Room Size / T60 两颗旋钮沒有變灰**——如果音樂人轉了 T60 旋鈕預期聲音改變、
   結果毫無反應，會直覺認為「這個 IR 實作有問題／控制項沒接對」，即使背後邏輯其實是刻意
   互斥設計。這是最容易讓人下「不是這樣用」判斷的體驗落差。
3. **沒有 predelay、沒有 direct-off、沒有 ER/tail 分離**——如果這位音樂人習慣 Altiverb /
   Waves IR-1 這類專業卷積外掛，會預期至少有 predelay 可調；一個「只有 Load + Mix」的卷積
   殘響，功能密度遠低於業界常態，容易被評為「半成品」而不是「用法不對」，但外行表述上常常
   會說成「這不是卷積殘響該有的用法」。
4. **無法真正拿掉 dry 訊號做純送收（aux send）架構**——如果音樂人的工作習慣是把卷積殘響
   放在一個 return 軌、輸入軌 100% wet，這裡的架構（insert 式、dry 永遠混入）沒辦法支援，
   對「認真用卷積殘響混音」的人來說是結構性的落差，而不是參數調校問題。
5. **這個功能完全脫離專案自己的物理驗證文化**——`SCENE_REVERB_DESIGN.zh-TW.md` 那套
   Sabine/Eyring 有公式、有引用、有誠實分層；IR 這條路徑相比之下沒有等同的「這個 IR 適合
   什麼空間／這是誰量測的／頻率響應如何」的說明或分類，對照之下顯得像臨時外掛的功能，
   不像這個專案一貫的嚴謹風格——這可能是音樂人「這不對勁」直覺的深層原因，即使他們說不清楚
   具體是哪個技術細節。

## §4 三個選項（工程量估計，不做決定）

### 選項 A：只改 UI 說法（不動 DSP/資料流）

- 內容：IR 模式下把 Room Size / T60 旋鈕 `setEnabled(false)` 並變灰；Load 按鈕依副檔名顯示
  不同 tooltip/文案，明確區分「載入空間脈衝響應」vs「載入殘響 profile 數值」；面板標題或
  tooltip 加一行「此為簡化卷積殘響：無 predelay/trim/ER 分離」的誠實聲明。
- 工程量：**小**。只動 `PluginEditor.cpp` 幾處 `setEnabled` 呼叫與文案字串（`UiLocale` 對照
  表新增 1-2 條），不碰 DSP、不碰 state schema。半天內可完成，風險極低。
- **不解決**：user preset 遺失 IR 這個 bug 級落差、CPU 優化、predelay/trim/ER 分離等結構性缺口。

### 選項 B：補配套（讓 IR 模式達到「堪用的基本卷積殘響」水準）

- 內容至少包含：
  1. 修 user preset 遺失 IR 的 bug——`saveUserPreset`/`loadUserState` 需要把 `reverbIRPath`
     一併存讀（.tsukipreset 的 XML 結構要加一個屬性或子節點，並處理「preset 裡的路徑在
     這台機器不存在」的降級提示，比照 setStateInformation 現有的靜默降級邏輯，但至少要有
     使用者可見的警告，不能沿用現在「完全無聲」的行為）。
  2. 加一顆 predelay 參數（IR 模式與算法模式分開，或共用现有的「無」→ 新增一顆新 APVTS
     參數，UI 加一顆旋鈕，DSP 端在 IR 卷積前插一段簡單延遲線）。
  3. Convolution 建構子改用 `NonUniform`（headSize 建議 ≥256，依 JUCE 文件），需要重新量測
     長 IR 情境下的 CPU 佔用是否確實改善，並跑一次現有的效能相關測試（若有）。
  4. Room Size/T60 旋鈕在 IR 模式下 disable（同選項 A 第一項，屬於必要子集）。
- 工程量：**中至中大**。涉及 preset 檔案格式版本升級（需处理旧 preset 向后相容）、
  新增一顆 DSP 參數與其自動化/平滑處理、Convolution 建構子替換後的重新測試。
  估計數天工作量（含測試），且動到 preset 檔案格式屬於「碰使用者資料相容性」的變更，
  按專案既有文化（`feedback_no_overwrite_originals`、fail-closed 驗證習慣）應該要有明確的
  版本遷移與回歸測試，不是單純加欄位就結束。
- **不包含**（更進階、通常評估為超出「堪用」門檻）：ER/tail 分離控制、direct-off 送收架構、
  IR 頭尾可調 trim UI（拖曳式，而非现有的自動修靜音）——這些是選項 B 之上的加碼項，
  若要做，工程量會再上一個量級（需要新的 DSP 分析/分段卷積或至少 IR 波形顯示 UI）。

### 選項 C：維持現狀

- 內容：不動任何程式或文案，僅在文件（如本稽核報告）留下已知落差紀錄，供未來決策參考。
- 工程量：**零**。
- 風險：user preset 遺失 IR 的靜默降級行為持續存在——任何存了 IR 模式 preset 的使用者，
  換一台機器或清過快取後重載 preset，會拿到一個「聽起來不一樣、但沒有任何警告」的結果。
  這是三個選項裡唯一會被歸類為「使用者可感知資料遺失且無提示」的殘留風險，其餘落差
  （predelay、ER 分離等）維持現狀只是「功能還沒做」，性質上比較輕。

---

*本報告為讀碼稽核，未修改 `src/` 或任何既有檔案。所有行號/檔名引用可用
`grep -n` 於上列路徑重現。*

---

## 附錄 Z：Opus 事實對碼稽核記錄（2026-08-28，懷疑立場）

同基準 `fix/deep-physics-audit-20260716` @ `88bdfac`，純讀碼。這份文件的價值全在事實正確，
所以下面把 §1 的訊號流逐行、§2 的每一列、以及被引用的每個行號都重新開檔核對過。

### Z.1 對得上的（逐項通過）

**訊號流（§1.1）全部正確**，逐行核對 `src/effects/EffectChain.h`：

| 文件宣稱 | 核對結果 | 證據 |
|---|---|---|
| 鏈序 Distortion → Compressor → Delay →〔算法 Reverb 或 IR 二選一〕→ 高頻補償 Shelf | 通過 | `EffectChain.h:174-179`（逐樣本）、`:186-207`（IR 區塊）、`:209-224`（shelf） |
| `irMode` 三條件（mode ≥ 0.5 && `hasImpulseResponse()` && `numSamples <= maxBlock`） | 逐字通過 | `EffectChain.h:132-135` |
| **取代而非並聯**：IR 模式完全跳過 `SimpleReverb` | 通過 | `EffectChain.h:178-179`（`if (! irMode) reverb.processStereo`） |
| dry 快照取樣點在 Delay 之後、Reverb 之前 | 通過 | `EffectChain.h:190-192`，緊接在跳過 reverb 的逐樣本迴圈之後 |
| 逐樣本 `dry*(1-mix) + wet*mix` | 通過 | `EffectChain.h:200-206` |
| Room Size / T60 在 IR 模式被完全忽略，UI 未變灰 | 兩半都通過 | `EffectChain.h:141/153-156`；`PluginEditor.cpp` 全檔**零** `setEnabled` 呼叫（唯一相關的 `refreshReverbModeButton` 只改按鈕文字與 tooltip，`:642-654`） |
| `Trim::yes`、`size = 0`、`Normalise` 未顯式傳＝預設 `yes` | 三項通過 | `EffectChain.h:91-94`；JUCE 簽章預設值 `Normalise::yes` 在 `libs/JUCE/modules/juce_dsp/frequency/juce_Convolution.h:240-242` |
| 預設建構子＝zero-latency、uniform-partitioned | 通過（JUCE 原文） | `juce_Convolution.h:94-98`：「The default operation of this class uses zero latency and a uniform partitioned algorithm.」宣告在 `EffectChain.h:232` |
| `loadImpulseResponse` 是 wait-free | 通過（JUCE 原文） | `juce_Convolution.h:103-105` |
| 30s 上限、且用**原始檔長**非 trim 後長度 | 通過 | `PluginProcessor.cpp:785-792`（`seconds` 由 `lengthInSamples/sampleRate` 算）、`:798`；tail 估計用它：`:438-441` |
| DAW state 存讀 `reverb_ir_path` | 通過 | `PluginProcessor.cpp:699-700`、`:739-746`（`switchModeToIR=false`） |
| user preset 只 `copyState()`／`replaceState()`，不碰 IR 路徑 | 通過 | `PresetManager.h:136`（save）、`:380`（load）；全檔無 `reverbIR` 字樣 |
| CLI/Score 路徑完全沒有 IR | 通過 | `scores/schema/score.schema.json:58-64`（reverb 僅 `decay`/`wet`、`additionalProperties:false`）；`src/score/ScoreRenderer.h:1260-1262`；`src/dsp/EffectsChain.h` 無 `Convolution`（reverb 只走 `SimpleReverb`，`:73/:77/:98`） |
| `PluginEditor.cpp:673-676` 用副檔名分流 `.wav`→IR／其餘→profile | 逐字通過 | 同行號 |
| HostProbe sentinel 宣告 FX-FREE 並歸零 Reverb Mix | 通過 | `tests/host_probe.cpp:94-100` |

**§2 表格「專業慣例」抽驗兩條，兩條的 JUCE 依據都成立（逐字開原始碼確認）：**
1. 「CPU 優化（長 IR）」列引用的 JUCE 建議 —— `juce_Convolution.h:146-148` 原文：
   「A requiredHeadSize of 256 samples or greater will improve the efficiency of the processing
   for IR sizes of 4096 samples or greater (recommended for reverberation IRs).」
   文件寫的「headSize ≥ 256、reverb 用途長 IR」與原文一致。**引用成立。**
2. 「採樣率轉換」列引用的「載入時視需要自動 resample」—— `juce_Convolution.h:229-231` 原文：
   「loads an impulse response from an audio file… performs some resampling and pre-processing
   as well if needed.」**引用成立。**

### Z.2 對不上的（findings）

**Z2-I1〔重大，必修〕§2「Direct off」列與 §3 第 4 點的 DSP 事實是錯的。**
文件寫「IR 模式下 dry 訊號永遠混入，無法做『100% wet 送 aux bus』」。實況：
- `fx_reverb_mix` 的 `Range(0.0f, 1.0f)`（`PluginProcessor.cpp:147-148`），`m = 1.0` 時
  `EffectChain.h:203-205` 的 `dryL[i]*(1.0f - m)` 係數歸零 ⇒ **輸出就是 100% wet**。
- `convolution.process(ctx)` 在非 bypass 時是純濕：JUCE 的 Mixer 把 `volumeDry` 目標設 0、
  `volumeWet` 目標設 1（`libs/JUCE/modules/juce_dsp/frequency/juce_Convolution.cpp:1191-1197`）。
- 算法路徑同理：`SimpleReverb.h:154-156` `dry = 1.0f - mix`，mix=1 時 dry 也是 0。

也就是說「拿不掉 dry」這個判斷不成立。真正站得住的限制是**這是合成器的 insert，沒有
return/aux 送收路由可言**——理由完全不同，結論的份量也小得多。§0 白話結論那句
「站在專業慣例來看只做了接上引擎這一步」不受影響，但這一列必須改寫，否則月月會據此
去做一個本來就不需要的「direct off 開關」。

**Z2-I2〔重大，稽核漏抓〕ALGO ↔ IR 兩個模式的濕訊號電平沒有校準，切模式會跳音量。**
`SimpleReverb` 的濕訊號額外乘了 **0.15**（`SimpleReverb.h:155-156`：`outL * mix * 0.15f`），
IR 路徑的濕訊號**沒有任何等效縮放**（`EffectChain.h:203-205` 直接用卷積輸出）。
同一顆 `fx_reverb_mix` 值，按下 ALGO/IR 切換鈕前後的殘響響度會差一大截。
§2 有「IR 增益正規化：已有」這一列，但它只保證「換不同 IR 檔之間」響度穩定
（`Normalise::yes`），完全沒涵蓋「兩個 reverb 模式之間」。
這一條比表格裡列的 predelay、ER/tail 分離都更接近音樂人「一按就覺得不對」的直覺落差，
卻整份稽核沒提到。建議補進 §2 表格（判定：缺）並列入 §4 選項 A 的必要子集
（一顆固定補償增益，工程量與「旋鈕變灰」同級）。

**Z2-I3〔R2/R3 違規〕Waves IR-1 / Altiverb 的功能集全篇零引用。**
§0、§2、§3 反覆以這兩個產品當「專業慣例」基準（predelay、trim、direct on/off、增益校準
「這些一個都沒有」），但沒有任何來源；`grep -rn 'Altiverb|Waves|IR-1' docs/` 只命中本檔自己，
repo 內沒有對應的 SOURCES 或研究筆記。依 R2/R3 應標「未溯源」或補上實際看過的來源後再引用。
（對照組：同一份文件裡的兩條 JUCE 依據我逐字驗證通過，見 Z.1 —— 該有的嚴謹度它做得到，
所以這是選擇性的鬆懈，不是能力問題。）

**Z2-I4〔中，精確度〕§1.1 對「preset 遺失 IR」這個 bug 的失效模式描述不準。**
文件寫「重載後 `fx_reverb_mode` 仍是 1，但 `hasImpulseResponse()==false` ⇒ 靜默退回算法殘響」。
這只在**全新 instance／本次 session 從未載過任何 IR** 時成立。因為
`EffectChain::irLoaded` 一旦 `true` 就再也不會變回 `false`——`clearImpulseResponse()`
（`EffectChain.h:98-101`）**全 repo 沒有任何呼叫端**（grep 唯一命中是宣告本身）。
所以在同一 session 內載入一個 IR 模式的 user preset，會沿用「當下碰巧還留在記憶體裡的那顆 IR」，
真正的病徵是**preset 召回不確定（拿到別的 IR）**，而不是「必定退回算法殘響」。
bug 判定成立、嚴重度不變，但失效模式比文件寫的更難預測、也更難被使用者察覺。
§4 選項 C 的描述（「換一台機器或清過快取後重載」）反而較準，兩處自相矛盾，請統一。
順帶：`clearImpulseResponse()` 是死碼，修 bug 時應一併決定要不要接上。

**Z2-I5〔輕〕§1.3 引用 `melody_verify.py` 的程式碼框漏掉 wet 閘門。**
實際 `tools/melody_verify.py:302-303` 是
`reverb_decay = (float(rev.get("decay") or 0.0) if float(rev.get("wet") or 0.0) > 0 else 0.0)`，
且 `effective_tail = max(dry_T60, reverb_decay)` 實際是函式 `effective_t60(i)`（`:305-313`）。
用程式碼框呈現卻是改寫版，容易被當成逐字引用。結論（IR 從未參與這條路徑）不受影響。

**Z2-I6〔輕〕路徑寫法**：`PresetManager.h` 實際在 `src/PresetManager.h`（不是 `src/presets/`）；
文中未給目錄，`grep` 重現時會多繞一下。

### Z.3 稽核結論

訊號流圖（§1）與所有行號引用**逐行正確**，這是這份文件最核心、也最該被信任的部分，
複核零錯。preset 遺失 IR 的 bug 判定成立。
但 §2/§3 有一條 DSP 事實錯誤（Z2-I1，會誤導出一個不必要的功能）、
一條該抓沒抓到的實際落差（Z2-I2，模式切換跳音量）、
以及一組未溯源的第三方產品引用（Z2-I3）。**建議修完 Z2-I1～I3 再拿去做選項 A/B/C 的決策。**
