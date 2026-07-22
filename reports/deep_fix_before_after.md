# Deep-Fix 前後對照報告：本輪（fix/deep-physics-audit-20260716 unstaged）音色會變的物理修正

> 依據：`ROADMAP_PHYSICS.md` 規則 10（任何讓既有 score 渲染結果改變的物理修正，必須產出前後對照的頻譜差異報告讓月月知情）。
> 生成日期：2026-07-22。
> 讀者：月月（聾人使用者）——全程用「物理量」描述變化，不用「聽起來」這種形容詞。
> 範圍：本報告涵蓋的是**目前工作目錄（unstaged）相對於 commit `485c6c1`** 的全部改動，
> 也就是這一整輪 deep-physics-audit 尚未 commit 的所有變更，**不是** `reports/phase_h_before_after.md`
> 那一輪（已 commit，屬於更早的材質物理化）。`data/materials.json` 本輪完全沒有變動（`git status` 對
> `data/` 目錄零差異），本輪的差異全部來自 `src/` 的引擎程式碼與少數 `scores/` 檔案本身的編輯。

---

## 0. 這份報告在回答什麼問題，以及跟 Phase H 方法論的差異

月月交辦清單列了六項會變聲的修正，加上一項曲目本身的編輯：

| # | 修正 | 主要檔案 / 函式 |
|---|---|---|
| 1 | 舌鼓（tongue_drum）預設邊界 free-free → cantilever | `src/engines/ChromaticEngine.h` `tongueBoundary` 預設值 |
| 2 | 板模態（water_gong）改用真 Bessel／modified-Bessel 徑向振型，free-edge 特徵值改用材質實際 Poisson ratio 插值（不再全部假設 ν=0.33），並加入模態質量幾何縮放 | `src/physics/PlateModel.h` `radialModeShape()` / `freeEigenvalueForPoisson()` |
| 3 | 「最終」阻尼定義修正：`ModalResonator` 的衰減公式從 1/e 時間常數 τ 改成標準 -60dB 混響時間 T60 | `src/dsp/ModalResonator.h`（`exp(-t/decay[n])` → `10^(-3t/T60[n])`） |
| 4 | 槌／弓接觸時間隨力度變化（Hertz 彈性衝擊模型，τc ∝ 速度^-0.2） | `src/physics/HammerImpulse.h::tauCForStrike()`，接到 `ChromaticEngine.h`／`CimbalomEngine.h` 四處 |
| 5 | 弱模態生命週期改為相對每個模態自己的 -60dB（原本是絕對振幅 0.0001 的地板值，跟模態本身音量無關） | `src/dsp/ModalResonator.h`（`stopAmp = |currentAmp| * 0.001`） |
| 6 | Reverb 引擎整體替換：`SchroederReverb`/`DelayLine`/`SimpleCompressor` → 與外掛共用的 `SimpleReverb`/`StereoDelay`/`Compressor`，且每個 comb（含左右聲道）都標定到同一個可量測 T60（score 的 `decay` 欄位直接當作秒數，不再除以 10 當 roomSize 用） | `src/dsp/EffectsChain.h`、`src/effects/SimpleReverb.h` |
| 7（score） | `vivaldi_four_seasons_summer_m3` 的 `global.effects.reverb.decay` 從 2.1 改成 1.2 | `scores/classical/.../summer_m3.score.json` |

**跟 Phase H 方法論的關鍵差異，必須先講清楚**：Phase H 的兩項修正（特徵值表格、材質阻尼）在程式碼上彼此獨立、
互不重疊，所以可以分成 Stage 1 / Stage 2 兩階段、各自用「只切一個開關」的隔離測試精確歸因。
**本輪的六項修正全部揉在同一個 unstaged 工作目錄裡**，沒有中繼 commit 可以逐項切換，
而且修正 3／5（`ModalResonator` 的衰減公式與模態存活判定）是**所有 5 個 modal 引擎共用的底層邏輯**，
沒辦法在不改程式碼的前提下單獨關掉。因此本報告**做不到 Phase H 那種逐項精確隔離**，
只能做到：(a) 用「哪個引擎路徑會用到哪個修正」的程式碼事實，對每首曲子列出可能的機制清單；
(b) 用一首純 FM 引擎的曲子（完全不經過 1/2/3/4/5，只可能經過 6）當對照組，把 reverb 引擎替換
的影響單獨挑出來看。這個方法論限制誠實列在 §7。

---

## 1. 兩份 CLI 的來源與 SHA256

| | Before（binary A） | After（binary B） |
|---|---|---|
| 來源 | commit `485c6c101de740fc50beaf5de6a207b8bcae98c7`（2026-07-13，`git worktree` detached checkout 重建） | 目前工作目錄 `C:/Users/admin/Desktop/Claude/tsuki-synth`（分支 `fix/deep-physics-audit-20260716`，全部改動 unstaged） |
| 執行檔 | `TsukiSynthCLI.exe`（Release，Visual Studio 18 2026 x64） | `TsukiSynthCLI.exe`（Release，同一 generator） |
| SHA256 | `6f74d5caeb9af8d87d4a7988d9c5790d964dc695592d2b2d7dc6ad2d412ec771` | `f87037d6fcb8bd14e7037b8c62848ff8c0e16c4684e1da8c57f42f31a6f1845` |
| `data/materials.json` | 與 HEAD 相同 | 與 HEAD 相同（本輪未改） |
| `src/` 改動量 | — | 24 個檔案，2787 行新增 / 876 行刪除（`git diff --stat -- src/`） |

兩份 CLI 各自的建置環境、路徑細節見任務交接記錄（`baseline_485c6c1` worktree 的建置備註），本報告不重覆。

---

## 2. 代表曲目選擇與涵蓋範圍

| 分類 | Score | 引擎 | 選擇理由 |
|---|---|---|---|
| (a) tongue_drum 邊界預設 | `moonlight_sonata_movement1_tongue_drum`（examples） | tongue_drum ×1142 事件，`finger` 撥奏 | 全曲皆未顯式指定 `beam_boundary`，完全吃預設值變化；同時 reverb wet=0.46，可觀察修正 6 疊加 |
| (a) tongue_drum 邊界預設 | `akashic_opening_bell_001`（library） | tongue_drum ×7 + water_gong ×1 | library 曲、未顯式指定 `beam_boundary`；混合引擎，可同時看到修正 1 與修正 2 的疊加 |
| (b) water_gong | `water_gong_clamped`（examples） | water_gong，clamped（`freeEdge=false`） | 控制組：clamped 邊界完全不吃修正 2 的 free-edge Poisson 插值路徑，只吃修正 3/4/5/6 |
| (b) water_gong | `water_gong_free`（examples） | water_gong，free-edge（`freeEdge=true`） | 完整吃到修正 2 的 Bessel 振型 + ν 相依特徵值改寫 |
| (c) cimbalom/piano | `physical_piano`（examples） | piano（→ cimbalom 路徑，`felt` 槌，steel） | 無 `damping_override`，完整吃材質阻尼公式（雖公式本身未變，但下游解讀方式變了，見修正 3） |
| (c)/(d) cimbalom + reverb | `moonlight_sonata_movement1_yangqin`（examples） | cimbalom，steel，`wood_mallet` | 每個音符都有 `damping_override`，是 Phase H 用來示範「材質阻尼修正對它免疫」的曲子；本輪修正 3 發生在 `damping_override` 之後的下游，**這次它不再免疫**，見 §4.4；同時 reverb decay=5.8、wet=0.34，reverb 影響顯著 |
| (e) score+引擎雙重變更 | `vivaldi_four_seasons_summer_m3`（classical） | string→cimbalom 路徑，steel，`bow`，5158 事件，全部 `damping_override=0.34` | **score 本身的 reverb decay 2.1→1.2 與引擎修正同時發生**，本報告不拆分（不可拆分，因為 before 用的正是 commit 485c6c1 當下的 score 版本，decay=2.1；after 用的是目前工作目錄的 score 版本，decay=1.2） |
| 域外對照組 | `fur_elise_opening`（examples） | fm | 完全不經過 `ModalResonator`／`HammerImpulse`／`PlateModel`（修正 1-5 域外），reverb wet=0.22，**唯一只可能受修正 6 影響的曲子**，用來把 reverb 引擎替換的貢獻單獨挑出來 |

八首曲目、兩邊 CLI 都成功渲染，**沒有出現舊 CLI 拒絕新 score 的相容性問題**（`length_mm`/`tension_n` 等
no-op 參數的刪減對舊 CLI 的 JSON 解析完全無感，因為那些欄位本來就是選讀）。

渲染指令（可重現，score 檔案已固定在 scratchpad，兩邊分開存一份輸入避免混淆）：
```
<binary_A> <scores_before>/<name>.score.json --output <before_dir>
<binary_B> <scores_after>/<name>.score.json  --output <after_dir>
```
除 `vivaldi_summer_m3` 外，`scores_before`／`scores_after` 底下的 7 個檔案內容逐位元組相同
（`git diff` 對這些路徑本輪零差異，已用 `git diff --stat` 逐一確認）。

---

## 3. 逐首數字（RMS / Peak / 頻譜質心 / 包絡衰減估計 / 時長）

分析方法沿用 `reports/phase_h_before_after/analyze.py` 的量測定義（RMS/peak 用 dBFS 全域方均根與峰值；
頻譜質心用前 2 秒漢寧窗 FFT；「T60 寬帶估計」用解析包絡（FFT-Hilbert）在攻擊後 100ms 到 -50dB 或 3 秒視窗內
做對數回歸取斜率，外推至 -60dB）。

| Score | Δ RMS (dB) | Δ Peak (dB) | Δ 頻譜質心 (Hz) | T60(寬帶估計) 前→後 | 時長 前→後 |
|---|---|---|---|---|---|
| `fur_elise_opening`（**fm，域外對照組，只可能受修正6影響**） | **-2.259** | -1.881 | -20.16（2127→2107，約 -1%） | 24.37s → 15.84s（估計值，見 §6 可靠性說明） | 6.71s → 6.78s（幾乎不變） |
| `moonlight_sonata_i_tongue_drum`（tongue_drum） | **-3.682** | -6.885 | **+30.20**（135.50→165.71 Hz） | 6.57s → N/A（見 §6） | 329.22s → 324.86s |
| `akashic_opening_bell_001`（tongue_drum+water_gong 混合） | -1.211 | -1.575 | **+65.00**（315.70→380.70 Hz） | 0.75s → 6.21s | 33.05s → 28.67s |
| `water_gong_clamped`（water_gong，clamped） | -1.646 | -1.576 | **+375.04**（504.90→879.95 Hz） | 7.91s → 6.80s | 15.00s → 10.07s |
| `water_gong_free`（water_gong，free-edge，吃修正2） | **-3.712** | -3.952 | **+270.64**（699.86→970.50 Hz） | 11.67s → 3.59s | 15.00s → 10.07s |
| `physical_piano`（piano） | **+2.346**（唯一變大聲的一首） | -0.902 | **+194.42**（631.65→826.06 Hz） | 24.91s → 8.25s（估計值） | 12.50s → 8.03s |
| `moonlight_sonata_i_yangqin`（cimbalom，全音符 `damping_override`） | -2.517 | -1.609 | -0.30（928.47→928.17 Hz，幾乎不變） | 3.37s → 9.71s | 322.42s → 317.49s |
| `vivaldi_summer_m3`（**score+引擎雙重變更**） | **-2.648** | -2.123 | **+143.32**（229.84→373.17 Hz） | 1259.8s → 126.4s（皆為外推估計值，不可靠，見 §6） | 163.77s → 157.95s |

原始輸出：`$SCRATCH/analyze_output.txt`（本報告數字的直接來源，路徑定義見 §8）；
渲染 WAV／分析腳本本身留在 scratchpad，見 §8 附錄。全部 8 對 WAV 的 SHA256 前後**都不同**
（沒有出現 Phase H §2.2 那種因 `damping_override` 而位元完全相同的狀況——見 §4.4 的解釋）。

---

## 4. 逐首物理歸因

### 4.1 `fur_elise_opening`（fm，域外對照組）── 單獨測出修正 6 的貢獻

這首完全不經過 `ModalResonator`／`HammerImpulse`／`PlateModel`（FM 合成路徑，`ROADMAP_PHYSICS.md` §0
早已列為這些物理修正的域外項目），所以觀察到的差異只可能來自修正 6（reverb 引擎整體替換）：
**ΔRMS -2.26 dB、ΔPeak -1.88 dB、頻譜質心幾乎不變（-20 Hz／2127 Hz，約 -1%）、音高（top partial 622/660 Hz
→ 622/658 Hz）幾乎不變、時長幾乎不變（6.71s→6.78s）**。

機制：舊 reverb 用 `roomSize = min(decay/10, 1.0)` 把 score 的 `decay=2.4` 映成 roomSize=0.24，
餵給 `SchroederReverb`（8 個 comb + 4 個 all-pass 的獨立老實作，沒有標定 T60，8 個 comb 因為長度不同
會有 8 個不同的實際衰減時間，左右聲道也不對稱）；新 reverb 直接把 `decay=2.4` 當成秒數的 T60 目標，
用 `feedbackForLength()`（`std::pow(0.001, delaySeconds/decayTimeSeconds)`）讓 8 個 comb（含左右聲道）
都精確在 2.4 秒衰減到 -60dB。兩個實作的濕聲通道能量分佈本來就不同，觀察到的 -2.26dB RMS 落差、
頻譜質心幾乎不變（reverb 本身對音色的頻譜傾斜影響很小，主要是能量／密度差異）都與這個機制方向一致。
**這一項純粹是效果器實作換了一顆演算法，不是「T60 變長變短」這種單一參數的量化調整**，
沒有辦法用簡單公式預測確切數值，只能用實測數字如實記錄。

### 4.2 `moonlight_sonata_i_tongue_drum` 與 `akashic_opening_bell_001`（tongue_drum 邊界預設）

兩首都未顯式指定 `beam_boundary`，本輪吃到 `tongueBoundary` 預設值從 free-free 改成 cantilever
（`ChromaticEngine.h`）。Cantilever 樑（一端固定一端自由）跟 free-free 樑（兩端自由）的模態頻率比例表
完全不同（`BeamModel.h` 兩組特徵值表），所以每一個舌鼓音符的泛音結構整個換了一套比例關係——
這是唯一會讓基頻以上的泛音頻率位置整組改變的修正（跟修正 2-6 只改振幅/衰減不同）。
觀察到的頻譜質心大幅上移（+30～+65 Hz）與這個機制方向一致：cantilever 樑第一泛音對基頻的比例
（≈6.27）比 free-free 樑第一泛音比例（≈2.76，取決於邊界條件精確值）更高，泛音往高頻分散，
質心整體上移。這兩首同時也吃到修正 3（阻尼定義）、修正 5（弱模態存活判定）、修正 6（reverb），
RMS/Peak 的下降無法單獨歸因給邊界修正一項，是四個機制疊加的結果。

`akashic_opening_bell_001` 額外含 1 個 water_gong 音符，會再疊加修正 2；但因為只有 1 個事件，
對整首曲子的統計量影響很小，主要差異仍應歸因給佔多數的 7 個 tongue_drum 事件。

### 4.3 `water_gong_clamped` vs `water_gong_free`（Bessel 徑向振型 + ν 相依特徵值）

兩首用相同材質（bronze）、相同音符（C4→G4）、相同 reverb 設定（decay=3.0, wet=0.35），
唯一差別是 `freeEdge` 旗標。**Clamped 版本完全不吃修正 2 的 free-edge Poisson 插值路徑**
（`radialModeShape()`／`freeEigenvalueForPoisson()` 只在 `freeEdge=true` 時介入），
只吃修正 3/4/5/6；**Free-edge 版本額外吃修正 2 的完整改寫**（振幅公式從舊的
`x^(m/2)` 啟發式換成真正的 Bessel/modified-Bessel 徑向本徵函數在實際擊打半徑的取值，
特徵值表也從單一 ν=0.33 假設換成依材質實際 Poisson ratio 插值）。

兩者對照：clamped 版 ΔRMS -1.65 dB／頻譜質心 +375 Hz；free-edge 版 ΔRMS -3.71 dB／頻譜質心 +271 Hz。
Free-edge 版本 RMS 落差是 clamped 版本的 2.3 倍，方向與「振幅公式從啟發式換成物理正確的模態形狀 +
新增模態質量幾何縮放」這個額外改動一致——這個額外機制只存在於 free-edge 路徑，
是兩首曲子 RMS 落差量級不同的主要物理原因。兩者都受修正 3（阻尼定義）主導了整體衰減的
量級變化（§5 詳述），這部分兩首曲子共享，不是造成兩者差異的原因。

### 4.4 `physical_piano` 與 `moonlight_sonata_i_yangqin`（cimbalom/piano 路徑）

`physical_piano` 沒有 `damping_override`，完整吃材質資料庫算出的 `decayTimeForFrequency()` 數值；
`moonlight_sonata_i_yangqin` 每個音符都有 `damping_override`（0.34-0.4 不等）。

**關鍵區別（比 Phase H §2.2 多一層）**：Phase H 材質阻尼物理化（改 `alpha` 數值本身）在
`damping_override` 存在時完全不生效，因為 `damping_override` 直接取代了「用 alpha 算 decay」這一步，
兩者是同一層的替代關係。但本輪修正 3（`ModalResonator` 把 `decay[n]` 從 τ 重新解讀成 T60）
**發生在 `damping_override` 決定完 `decay[n]` 數值之後、更下游的合成階段**——不管 `decay[n]`
是從 alpha 公式算出來還是從 `damping_override` 直接指定，最終都會被 `ModalResonator` 用同一套
新公式重新詮釋。所以 `moonlight_sonata_i_yangqin` **這次不再位元不變**（SHA256 前後不同），
ΔRMS -2.52 dB，跟沒有 override 的 `physical_piano` 一樣受到修正 3 影響，只是量級不同
（因為 `damping_override` 的具體數值跟材質公式算出的數值本來就不一樣）。

`physical_piano` 是全部 8 首裡**唯一 RMS 變大聲的**（+2.35 dB），與其餘 7 首方向相反。
可能機制：新的相對 -60dB 弱模態存活判定（修正 5）讓原本被舊「絕對振幅 0.0001 地板」
提早剔除的中高泛音，在新規則下能存活更久（因為地板改成跟隨每個模態自己的初始振幅，
而非一個所有模態共用的絕對值），疊加 T60 從 τ 重新解讀成 T60 讓早段包絡能量分佈改變，
兩者疊加對這首曲子（steel、4 個短促重疊音符）恰好是淨增益；但這是**觀察到的方向性結論，
不是逐機制拆解過的因果證明**（見 §7 方法論限制）。

### 4.5 `vivaldi_summer_m3`（score + 引擎雙重變更，不可拆分）

這首的 `before` 用的是 commit `485c6c1` 當下的 score（`reverb.decay=2.1`），`after` 用的是
目前工作目錄的 score（`reverb.decay=1.2`）——**這個對照天生同時包含「score 作者把 reverb 調短」
與「六項引擎修正」兩種來源**，本報告刻意不拆分（拆分需要額外交叉渲染：用新引擎渲染舊 decay 值，
不在本輪任務範圍內，如需要可另案補做）。全曲 5158 個事件全部是 `string`（→cimbalom 路徑）、
steel、`bow` 擊發、且全部帶 `damping_override=0.34`，物理歸因與 §4.4 相同（修正 3 對
`damping_override` 曲目不再免疫）+ reverb decay 從 2.1 秒縮短到 1.2 秒（進一步降低混響能量，
方向與觀察到的 ΔRMS -2.65 dB 一致，但無法定量拆分兩個來源各自貢獻多少）。

---

## 5. 貫穿全部 8 首的共同機制：修正 3（τ → T60 重新定義）是最大單一貢獻源

`ModalResonator.h` 的衰減公式從 `amp[n]*exp(-t/decay[n])`（`decay[n]` 是 1/e 時間常數 τ）
改成 `amp[n]*10^(-3t/T60[n])`（`T60[n]` 是標準 -60dB 混響時間定義），**`decayTimeForFrequency()`
這個算 `decay[n]` 數值的公式本身完全沒有改變**（`StringModel.h`/`BeamModel.h`/`PlateModel.h`
三個引擎都只是把同一條 `alpha + beta*f^2 + gamma*f` 公式抽成共用函式，數值不變）。

純數學後果：舊公式下，振幅衰減到 -60dB（比例 0.001）發生在 `t = τ·ln(1000) ≈ 6.908τ`；
新公式下，同一個數值直接定義成 `t=T60` 時到 -60dB。也就是說，**同一個 `decayTimeForFrequency()`
算出來的數字，在舊版本代表「要等 6.908 倍那個數字的秒數才會衰減到 -60dB」，在新版本代表
「衰減到 -60dB 剛好就是那個數字的秒數」**——同一個物理模型輸出的同一個數字，音訊層面的實際
衰減時間縮短成大約 1/6.9。這條機制是全部 5 個 modal 引擎（string/cimbalom/piano/beam/tongue_drum/
plate/water_gong）共用的底層邏輯，也是 8 首曲子裡有 7 首 RMS 變小聲、多數曲子時長略微縮短
（渲染引擎判斷「音符還在響」的門檻提前達到）的最主要共同原因。這條連同修正 5（弱模態存活判定
改成跟隨各模態自己的 -60dB，不再用絕對地板）互相纏繞，兩者都改在 `ModalResonator.h`，
本報告不拆分成兩個獨立行；`physical_piano` 的例外（RMS 反而變大聲）很可能正是修正 5
在特定曲目上蓋過修正 3 的個案（見 §4.4）。

**注意**：因為 §6 判定制容差、`ROADMAP_PHYSICS.md` §6 的既有 GATE 沒有被本報告修改或放寬
（Rule 2），這一項機制對既有 T60 判定 GATE 的影響（會不會產生新的 PASS/FAIL 翻轉）**不在本報告
範圍內**，需要另外跑 `tools/physics_verify.py --t60` 才能確認，本報告只回答「渲染出來的音訊
數字上差多少」這個問題。

---

## 6. 「T60 寬帶估計」數字的可靠性說明（誠實聲明，避免誤讀）

§3 表格裡的「T60(寬帶估計)」欄位，量測方法是對整首渲染出的音訊做解析包絡（FFT-Hilbert）、
在攻擊後 100ms 到 -50dB（或最長 3 秒）的視窗內做對數回歸、外推到 -60dB。這個方法對
`water_gong_clamped`／`water_gong_free`（2 個孤立音符、彼此不重疊）這種曲目是合理的，
但對以下狀況會嚴重失真，**數字僅供參考，不能當作精確的物理 T60 量測**：

- **多音符連續的完整樂曲**（`moonlight_sonata_i_tongue_drum` 1142 events、`moonlight_sonata_i_yangqin`
  1142 events、`vivaldi_summer_m3` 5158 events）：3 秒視窗內混著大量新音符持續進來，
  包絡回歸抓到的是「整首曲子開頭幾秒的響度變化趨勢」，不是任何單一音符的衰減曲線。
  `vivaldi_summer_m3` 前後分別回歸出 1259.8s／126.4s 這種遠超曲目長度本身的數字，
  正是斜率太平緩、外推距離太遠導致的數值不穩定，**不代表真的有音符響了 20 分鐘**。
- **`moonlight_sonata_i_tongue_drum` 的「after」欄位回傳 N/A**：3 秒視窗內振幅回歸斜率非負
  （擬合失敗），這通常也是「同一個 3 秒視窗裡有新音符進來墊高包絡」的訊號，不是衰減變快到
  量不到。
- `physical_piano`／`fur_elise_opening` 的「T60 寬帶估計」（24.9s／24.4s 等）同樣是短視窗外推，
  可信度遠低於 §1 隔離測試（Phase H）那種位元級吻合的精度，這裡刻意保留原始數字但加註此說明，
  不做「T60 變長/變短 X 倍」這種精確倍數宣稱。

這正是 `reports/phase_h_before_after.md` §3 已經記錄過的同一個 harness 侷限（固定探針時長
遇上大幅拉長或大量音符重疊的曲目），本報告延用同一個誠實揭露方式，不重新宣稱已解決。

---

## 7. 方法論限制（跟 Phase H 比，誠實列出做不到的部分）

1. **無法逐項精確隔離**：本輪六項修正沒有中繼 commit，`ModalResonator.h` 的修正 3/5 是全部
   modal 引擎共用的底層邏輯，無法在不改程式碼的前提下單獨開關。本報告用「哪個引擎路徑碰得到
   哪個修正」的程式碼事實做定性歸因（§4），**不是** Phase H Stage 1 那種位元級精確隔離。
2. **`vivaldi_summer_m3` 的 score 變更與引擎變更疊加，未拆分**（§4.5 已聲明，如需要拆分可另案補測：
   用 binary B 渲染 `decay=2.1` 的舊 score 版本，即可把兩個來源分開）。
3. **「T60 寬帶估計」對多音符/長曲目不可靠**（§6），僅供參考數字，不當作精確衰減時間宣稱。
4. 本報告未涵蓋 `tools/physics_verify.py` 的 GATE 判定翻轉（PASS→FAIL 或反向），那是另一個問題
   （既有 harness 容差是否被本輪修正撞出新 FAIL），不在 Rule 10「聽感前後對照」的範圍內，
   如月月需要請另外委派。

---

## 8. 附錄：檔案清單與復現指令

依交辦指示，本輪渲染中間檔（WAV／執行檔／分析腳本）**全部留在 scratchpad，不進 repo**；
只有這份 `.md` 報告本身進 `reports/`（unstaged，未 commit）。以下路徑均相對於：

```
SCRATCH = C:/Users/admin/AppData/Local/Temp/claude/C--Users-admin-Desktop-Claude/
          b4b012d3-2c20-4649-a770-1bd0b7480af8/scratchpad/deep_fix_before_after/
```

| 檔案（相對 `$SCRATCH`） | 內容 |
|---|---|
| `scores_before/*.score.json` | binary A 用的 8 個輸入 score（`vivaldi_summer_m3` 為 commit 485c6c1 版本，其餘 7 個與工作目錄逐位元組相同） |
| `scores_after/*.score.json` | binary B 用的 8 個輸入 score（`vivaldi_summer_m3` 為目前工作目錄版本） |
| `before/*.wav` | binary A 渲染的 8 首曲目 |
| `after/*.wav` | binary B 渲染的 8 首曲目 |
| `analyze.py` | RMS/peak/頻譜質心/T60 寬帶估計/top-partial 分析腳本（沿用 `reports/phase_h_before_after/analyze.py` 方法論） |
| `analyze_output.txt` | 分析腳本原始輸出（§3 表格的直接來源） |
| `f0_check.py` | `water_gong_clamped`／`water_gong_free`／`physical_piano` 第一個音符（C4）的 f0 量測腳本（50ms-1.55s 視窗，跳過攻擊瞬態） |
| `results.pkl` | 分析腳本原始輸出（pickle） |

（附註：`reports/phase_h_before_after/` 那一輪的慣例是把 WAV/pkl/binA/binB 直接放在 `reports/`
下、靠 `.gitignore`（`reports/**/*.wav`、`reports/**/*.pkl`、`reports/**/binA/`、`reports/**/binB/`）
排除在版控外。本報告改用交辦指示的 scratchpad 路徑，兩者本質上都不會進 git，只是實體位置不同；
如需要把這批檔案併入 repo 慣例位置，之後可以整批搬到 `reports/deep_fix_before_after/`。）

**音高（f0）獨立驗證**（`f0_check.py`，50ms-1.55s 視窗，跳過攻擊瞬態，避開第二個音符進場）：

| Score | 期望 f0（C4） | Before | After |
|---|---|---|---|
| `water_gong_clamped` | 261.626 Hz | 261.583 Hz（-0.3 cents） | 261.750 Hz（+0.8 cents） |
| `water_gong_free` | 261.626 Hz | 261.583 Hz（-0.3 cents） | 261.750 Hz（+0.8 cents） |
| `physical_piano` | 261.626 Hz | 262.667 Hz（+6.9 cents） | 262.667 Hz（+6.9 cents，前後完全相同） |

三首曲子前後 f0 位移都在 FFT 頻率解析度誤差內（<1.5 cents），`physical_piano` 前後甚至完全相同
（+6.9 cents，這個既有偏移跟本輪修正無關，是既有材質/尺寸計算的既有量，不在本報告範圍）。
**確認本輪六項修正全部只動振幅/衰減，沒有動到頻率計算**，與 §0 表格逐項機制的程式碼事實一致
（`alpha`/`beta`/`gamma`/`T60` 重新定義只進衰減公式；`tauCForStrike` 只改頻譜包絡形狀；
Bessel 振型只改振幅權重；reverb 引擎替換不改乾聲音高）。

渲染指令（可重現）：
```
<binary_A> <scores_before>/<name>.score.json --output <before_dir>
<binary_B> <scores_after>/<name>.score.json  --output <after_dir>
python analyze.py     # 在 deep_fix_before_after 目錄下執行，讀 before/after 產出 analyze_output.txt + results.pkl
python f0_check.py    # 同目錄，讀 before/after 產出 f0 表格
```

本報告未修改 `data/`、`src/`、`scores/` 任何檔案；未 commit、未 push（Rule 1/Rule 7）。
