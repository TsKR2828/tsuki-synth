# B4 Rule 10 前後對照報告：槌氈接觸時間換非線性接觸求解器（規定值 → 解出值）

> 產出：2026-08-27（施工卡 `docs/workcards/B4.md` §9／§10）
> 範圍：**只有 B4**——Cimbalom/Piano/String 路徑、且 exciter 有效映為
> `ExciterType::Felt`（felt / felt_mallet / finger / finger_tap / rubber_mallet；
> piano 引擎預設 exciter 經 wood_mallet→felt 覆寫）時的接觸時間 `tau_c`，
> 從「硬度查表 2.0 ms × 經驗 keytrack × 固定 v^−0.2」換成由實測接觸律
> `F = K·δ^α`＋槌質量＋撞速解出的 `pianoHammerTauC(note, v)`。
> Cotton/Wood/Metal 三檔與 Chromatic 引擎（舌鼓/鑼）完全不動。
> before 基線＝B3 落地後、B4 未動的工作樹（HEAD f67050b 乾淨，2026-08-27 00:04–00:07 採樣）。
> 方法腳本與原始資料：`reports/gate_outputs/b4_method/`（同一支腳本、同一組參數，
> before/after 各跑一次，見該目錄 README.md；before 檔全程未覆寫，
> before 渲染 WAV 保留於 `%TEMP%\b4_render_before` 且 SHA256 逐一核對相符）。
> **本輪含一項 GATE 判定域修改**：F3 velocity 主張域依月月 2026-08-27 裁決 (b)
> 重新界定（誠實專節 §6，容差數值未動）。

---

## §0 白話導讀卡（§9 白話導讀）

**一句話結論：鋼琴氈槌的「接觸時間」從拍腦袋的經驗擬合換成從實測接觸定律解出來
之後，低音變亮一點、高音的力度反應變得非常敏感（C7 力度加倍 ≈ +19 dB，舊版約
+6 dB）；音高（f0）與衰減（T60）一個位元都沒變，非氈槌路徑與 68 首不相關曲目
逐位元不變，73 首驗證曲全數通過。**

之前的狀況：Felt 檔位的接觸時間是「查表 2.0 ms × 音高 keytrack（量測擬合）×
固定 v^−0.2 力度縮放」。其中 v^−0.2 對應的是**純赫茲接觸（金屬對金屬，α=1.5）**，
不是鋼琴氈；音高關係也是對量測值的冪次擬合，不是從接觸物理推出來的
（`docs/HAMMER_CONTACT_SOURCES.md` §4）。B4 把它換成：文獻實測的逐音
`F = K·δ^α` 錨點（C2/C4/C7）＋逐音槌質量表（C1–C8）＋能量守恆推出的比例關係

```
tau_c(note, v) ∝ [m(note)/K(note)]^(1/(α+1)) · v^(2/(α+1) − 1)
```

絕對量級錨定在既有已溯源的 `kTauCFelt = 2.0 ms`（Askenfelt & Jansson 量測）
@ A4、velocity 0.5——所以**中音域中力度幾乎不動，改變的是全音域的「相對形狀」**
（內插規則與錨定選擇的完整登記見 §5，這兩項是本卡的建模決策，供你覆核）。

**為什麼高音的力度感會變得比以前明顯**（施工卡 §9 指定說明）：力度加倍時，
弦收到的力本身 +6.02 dB（這條不變）；但接觸時間也會隨力度縮短，把力脈衝的
頻譜整形 H(f) 往高頻推。**低音（C2）的基頻遠低於整形滾降區**，接觸時間怎麼變
基頻都收到幾乎一樣的份額，所以力度反應 ≈ +6.2 dB，跟舊版沒差多少。**高音
（C7）的基頻本來就深入滾降區**（2093 Hz 已越過力譜第一零點），而新公式在
C7 的力度指數是 −0.500（舊版固定 −0.2，等於敏感度變陡 2.5 倍）——力度一變、
接觸時間大幅伸縮，基頻份額跟著大幅擺動，疊上 +6.02 dB 後合計 **+19.1 dB**。
這正是真實鋼琴「高音重擊突然變亮變衝」的機制；它超出了 GATE 舊主張
「一律 ≈+6 dB」的假設範圍，因此觸發了 §6 的主張域裁決。

聽感上會變什麼：**低音的氈槌音色變亮**（`ocean_action_001` 的 D1 重擊接觸
時間 4.0→2.5 ms，整曲頻譜質心 +24.8%）；**中音幾乎不動**（A4 錨點完全重合；`ai_radiance` 兩首
質心 +0.06%／+0.30%）；**高音安靜彈時基頻明顯變虛、重彈時亮度暴增**
（C7 v=48/127 時基頻絕對振幅 −26.3 dB，力度敏感度見上）。**任何音的音高與
衰減時間完全不變**（§3／§2 模型級零差證明）。

**你要做的裁決**：接受這批改變，或指名回退。F3 velocity 的主張域已照你的
裁決 (b) 改為「渲染必須與模型自身預測吻合」（詳見 §6 誠實專節——容差數值
未放寬、其他引擎判定逐字未動、C7 +19 dB 的美學驗收仍歸你與外部試聽）。
所有檔案未 commit（R7），你保有完整否決權。

---

## §1 受影響清單（§9「先用腳本掃出清單」）

`scan_affected_scores.py`（判定條件見腳本 docstring 與 b4_method/README.md §1）
before/after 各跑一次，**兩次掃描結果一致**：73 首 corpus 中 **5 首受影響、
68 首不受影響**（`affected_scores_{before,after}.{md,json}`）。

| # | score | Felt 事件 | engine/exciter | 備註 |
|---|---|---|---|---|
| 1 | `scores/examples/physical_piano.score.json` | 4 | piano/(預設→felt) | C4/E4/G4/C5 |
| 2 | `scores/originals/ai_radiance/ai_radiance_complete.score.json` | 16 | cimbalom/felt_mallet | 經 layers 引用 m3 |
| 3 | `scores/originals/ai_radiance/ai_radiance_m3.score.json` | 16 | cimbalom/felt_mallet | 7 個音高 F4–F5 |
| 4 | `scores/library/akashic/akashic_action_001.score.json` | 1 | string/finger | D5，另有同音 plate 事件 |
| 5 | `scores/library/ocean/ocean_action_001.score.json` | 1 | string/rubber_mallet | D1（MIDI 26，錨點範圍外→flat 夾住） |

其餘 68 首（含全部 vivaldi、moonlight、Chromatic 曲）不受影響，
位元不變性證據見 §7。

---

## §2 受影響 5 首整曲對照：RMS／質心／T60（§9 指定量）

### 2a. 整曲 RMS 與頻譜質心

before/after 用各自當下工作樹的 CLI 完整渲染到 repo 外目錄
（`affected_render_{before,after}.csv`；RMS＝整曲混單聲道 20·log10(RMS)、
質心＝整曲無窗 rfft 振幅加權，與 B3 報告同一把尺）。
**注意：5 首的 export 都是 `normalize: true`（峰值正規化）**，所以 RMS 欄
反映的是正規化後的波形結構差，不是絕對電平差；音色變化看質心欄。

| 曲目 | RMS 前 (dBFS) | RMS 後 | ΔRMS (dB) | 質心前 (Hz) | 質心後 | Δ質心 |
|---|---|---|---|---|---|---|
| physical_piano | −18.285 | −18.579 | −0.294 | 789.91 | 842.61 | **+6.67%** |
| ai_radiance_complete | −25.741 | −25.746 | −0.005 | 2353.09 | 2354.50 | +0.06% |
| ai_radiance_m3 | −20.634 | −20.585 | +0.049 | 781.48 | 783.81 | +0.30% |
| akashic_action_001 | −22.259 | −22.249 | +0.010 | 1094.64 | 1180.46 | **+7.84%** |
| ocean_action_001 | −23.156 | −23.199 | −0.043 | 196.27 | 244.88 | **+24.77%** |

**逐曲歸因**（tau_c 新舊值來自 §5 的鏡像重算，已對實測自我驗證）：

- **ocean +24.8%（最大變化）**：唯一 felt 事件是 D1（MIDI 26）重擊
  （v=0.85）。D1 在 K/α 錨點範圍外，flat 夾在 C2 錨（α=2.3），接觸時間
  4.0→2.5 ms（該力度下）——變短，力譜滾降上移，第 2–5 partial 收到的
  份額大增（同機制的 C2 量化表見 §4），整曲質心被推高。基頻本身只 +0.10 dB。
- **akashic +7.8%**：felt 事件 D5/v=0.35 輕擊，接觸時間 1.96→2.21 ms——
  變長，**基頻 −6.1 dB**（高音輕彈變虛的方向），同帶的 plate 事件
  （不受 B4 影響）相對浮出，質心上移。
- **physical_piano +6.7%**：C4–C5 中高音、v=0.8–0.85 重擊，接觸時間縮短
  （C4 2.15→1.84 ms），基頻 +0.7～+1.7 dB、高次 partial 更亮。
- **ai_radiance m3/complete +0.30%/+0.06%**：16 個 felt 事件全在 F4–F5、
  v=0.42–0.46——正好貼著 A4/v=0.5 錨點，新舊公式在錨點重合（設計如此），
  接觸時間只動 ±2%（A4 2.03→2.08 ms），整曲幾乎不動。

### 2b. T60：模型級精確零差（22 個 felt 事件全取樣）

`t60_f0_felt_events.py`：受影響曲目（layers 型 complete 的 felt 內容即 m3
的事件，由 m3 列覆蓋）全部 **22 個 felt 事件**，用同一顆 after CLI 對
「原譜（felt→新求解器）」與「換激發器副本（cotton_mallet→舊 tauCForNote
路徑）」各 `--dump-modes` 一次，逐弦逐 partial 比對：

- **全部 22 事件：freq 與 decay 逐 partial 在 dump 輸出上逐值精確相等；amp
  全部不同**（證明換激發器真的切換了激發路徑，等式不是「兩邊跑到同一條路」
  的假象）。
- 這就是「before T60 = after T60」的**封閉證據鏈**：(1) 新舊程式裡 tau_c 都
  只進振幅加權 `forceSpectrumMagnitude()`，freq/decay 由
  `StringModel::decayTimeForFrequency()` 計算、無 tau_c 輸入（git diff 可查，
  B4 未碰任何 decay 程式）；(2) 非 Felt 路徑 before/after 位元不變
  （§7 nonfelt 檔）；(3) 本表證明 after 裡 felt 與非 Felt 路徑的 freq/decay
  相等。三段相接：before-felt ≡ after-felt，精確為零差。

代表值（模型基頻 T60，中央弦；「前」值由上述證據鏈確立、數值見證＝換激發器
dump 的 decay 欄；全表 `t60_f0_felt_events_after.csv`）：

| 曲 | 音 | f0 (Hz) | T60 前 | T60 後 | 差 |
|---|---|---|---|---|---|
| physical_piano | C4 | 261.6260 | 2.8737 s | 2.8737 s | **0（精確）** |
| physical_piano | C5 | 523.2510 | 1.4506 s | 1.4506 s | **0（精確）** |
| ai_radiance_m3 | A4 | 440.0000 | 1.4643 s | 1.4643 s | **0（精確）** |
| ai_radiance_m3 | F4 | 349.2280 | 1.8344 s | 1.8344 s | **0（精確）** |
| akashic_action_001 | D5 | 587.3300 | 1.0732 s | 1.0732 s | **0（精確）** |
| ocean_action_001 | D1 | 36.7080 | 1.1241 s | 1.1241 s | **0（精確）** |

### 2c. T60：音訊級取樣交叉核對（before/after WAV 同窗同帶同尺）

`audio_t60_sample.py`：直接在保留的 before WAV 與新渲染的 after WAV 上，
以 ±3% 帶通＋Hilbert 包絡對數斜率（physics_verify 同族方法）量取樣窗的
衰減斜率換算 T60。**帶內含 reverb/delay 或同音其他事件時，量到的是「混合帶
包絡斜率」而非單模態 T60**——但 before/after 用同一窗、同一帶、同一渲染
決定性，仍是有效的變化偵測器（全表含擬合跨度 `audio_t60_sample.csv`）：

| 曲 / 取樣 | 帶 (Hz) | T60 前 (s) | T60 後 (s) | Δ |
|---|---|---|---|---|
| physical_piano C4 sustain（單音純帶） | 261.6 | 2.5417 | 2.5537 | +0.47% |
| physical_piano E4 sustain（單音純帶） | 329.6 | 1.5735 | 1.5761 | +0.17% |
| physical_piano G4 sustain（單音純帶） | 392.0 | 2.6291 | 2.6344 | +0.20% |
| physical_piano C5 sustain（單音純帶） | 523.3 | 1.7746 | 1.7755 | +0.05% |
| physical_piano C5 曲尾 | 523.3 | 2.0427 | 2.0435 | +0.04% |
| ai_radiance_m3 F4 末事件衰減 | 349.2 | 5.1721 | 5.1729 | +0.02% |
| ai_radiance_m3 F4 帶曲尾 | 349.2 | 4.5974 | 4.5981 | +0.02% |
| akashic D5 sustain（string+plate 混帶） | 587.3 | 7.2247 | 10.2869 | **+42.4%\*** |
| akashic D5 曲尾（混帶） | 587.3 | 2.3030 | 2.1321 | **−7.4%\*** |
| ocean D1 帶曲尾（plate 主導混帶） | 36.7 | 4.7960 | 4.7657 | −0.63% |

\* **akashic 兩列不是任何模態衰減變了**（該曲唯一弦事件的模型 decay 逐 partial
精確零差，見 2b）：D5 帶內同時有 felt 弦（B4 後基頻 −6.1 dB）與同音 plate
事件（位元不變）＋reverb，弦份額下沉後混合包絡的權重移動，斜率跟著移——
這是**振幅改變的顯影，不是衰減律改變**。單音純帶的 6 列（physical_piano、
m3）全部 ≤0.5%，與 2b 的精確零差一致。ai_radiance_complete 為 layers 型，
未另取樣（felt 內容=m3，整曲級證據見 2a 與 §8 SHA）。

---

## §3 f0 零差異自我核對（§9 指定：tau_c 不改模態頻率）

理論主張：tau_c 只進幅度頻譜整形，不進模態頻率。實測三路交叉，全部零差：

1. **錨點探針（felt 路徑本身，before vs after 直接比）**：
   `anchor_partials_{before,after}.csv` 的 `center_string_f0_hz` 欄——
   C2 65.4060 / C4 261.6260 / C7 2093.0040 Hz，兩檔六列**逐字相同**
   （v=48/127 與 96/127 各一列）。
2. **22 個 felt 事件逐 partial**（§2b 同一批 dump）：felt vs 換激發器副本
   的 freq 欄**全 partial 精確相等**，closed chain 同 §2b ⟹ before=after。
3. **非 Felt 參照**：`nonfelt_invariance_{before,after}.txt` 中央弦 f0
   440.0000 Hz（32 partials）逐位元相同。

---

## §4 C2/C4/C7 × v48/v96 前 5 partial 相對振幅前後對照（§9 核心證據表）

單事件 piano 探針（無 params 覆寫＝Felt 路徑）、`--dump-modes` 中央弦，
dB re fundamental（`anchor_partials_{before,after}.csv`，原始 amp 欄同存）。

**before（B4 前）**：

| note | vel | p1 | p2 | p3 | p4 | p5 |
|---|---|---|---|---|---|---|
| C2 | 48/127 | 0.00 | +3.60 | +2.86 | −1.37 | −10.65 |
| C2 | 96/127 | 0.00 | +4.01 | +4.06 | +1.29 | −4.67 |
| C4 | 48/127 | 0.00 | −11.32 | −12.08 | −25.37 | −25.39 |
| C4 | 96/127 | 0.00 | −5.29 | −14.64 | −19.06 | −20.88 |
| C7 | 48/127 | 0.00 | −23.26 | −14.21 | −15.49 | −22.50 |
| C7 | 96/127 | 0.00 | −2.87 | −24.47 | −20.40 | −19.19 |

**after（B4 後）**：

| note | vel | p1 | p2 | p3 | p4 | p5 |
|---|---|---|---|---|---|---|
| C2 | 48/127 | 0.00 | +4.00 | +4.03 | +1.22 | −4.81 |
| C2 | 96/127 | 0.00 | +4.53 | +5.54 | +4.34 | +1.05 |
| C4 | 48/127 | 0.00 | −12.35 | −12.18 | −23.18 | −27.51 |
| C4 | 96/127 | 0.00 | −1.95 | −32.72 | −13.21 | −39.90 |
| C7 | 48/127 | 0.00 | **+18.06** | +11.13 | +7.12 | +2.24 |
| C7 | 96/127 | 0.00 | **+11.29** | +5.74 | −1.31 | −5.70 |

**解讀**：

- **C2 全面變亮**（p4 +2.6 dB、p5 +5.7～+5.8 dB 相對增益）：新接觸時間
  3.7→3.0 ms（v=0.5），滾降上移——這就是 ocean D1 質心 +24.8% 的機制。
- **C4 的 v96 列出現 ±19 dB 級的格間跳動**（p3 −14.6→−32.7、p5 −20.9→−39.9、
  p4 −19.1→−13.2）：力譜零點被新的 tau_c(v) 掃過個別 partial——before 採樣
  README 預告的「零點掃過 p2」現象如期出現，只是落點在 p3/p5。這是形狀
  重分布，不是能量憑空消失（基頻絕對振幅 v96 只 +0.26 dB）。
- **C7 兩列的正值不是高音變亮，主要是基頻下沉**：C7 新接觸時間比舊 keytrack
  更長（1.21→1.45 ms @v=0.5），基頻更深入滾降區——**基頻絕對振幅 v48
  −26.3 dB（0.01761→0.00085）、v96 −13.7 dB（0.02041→0.00422）**，於是
  相對表上 p2–p5 全部翻正。兩個 velocity 檔的基頻降幅差 12.6 dB，正是 §0
  「高音力度感變明顯」在 partial 層的直接顯影（力度敏感度數字見 §6）。

---

## §5 內插規則與絕對量級錨定（§4.2／§4.3／§10 指定登記段，供月月覆核）

**這兩項是 B4 卡新增的建模決策，不是文獻原文**（文獻只給三個 K/α 錨點、
八個質量錨點、與比例關係），完成報告依卡明寫如下：

1. **內插規則：`alpha` 與 `log10(K)` 對 MIDI note 分段線性內插、範圍外
   flat 外推（夾在最近錨點）；槌質量對質量本身分段線性、範圍外同樣 flat。**
   - 獨立變數 = MIDI note（等價 log2(frequency)）；K **必須**在 log10 域內插
     （三錨點跨 3.4 個數量級且量綱隨 α 而變，對 K 本身線性內插已被單元測試
     的反例釘死成會 FAIL 的迴歸——`tests/physics_models_repro.cpp`
     `testPianoHammerContactSolver()` 第 6 條，C2–C7 中點兩種內插差 >10×）。
   - flat 外推的理由：文獻只保證「α 隨音高單調上升、log K 近似線性」，flat
     不違反單調性；線性外推可能沖出已知量測範圍（`HammerImpulse.h` 註解同文）。
2. **絕對量級錨定：`tau_c_piano(note, v) = kTauCFelt × g(note,v) / g(69, 0.5)`
   ——錨在既有已溯源的 `kTauCFelt = 2.0 ms`（Askenfelt & Jansson 量測）
   @ A4（MIDI 69）、velocity = 0.5。** 文獻推導只到比例關係、無絕對前置係數
   （解出它需要接觸運動方程的相位積分，文件未提供，Rule 4 禁止編造）；錨定
   使新公式在 A4/v=0.5 與舊校準**完全重合**，其餘音高/力度的相對形狀才是
   物理推導接手的部分。
3. **工程安全 clamp `[0.3 ms, 8 ms]`**（`kPianoTauCMinS/MaxS`）：現有四檔查表
   Cotton(6ms)–Metal(0.2ms) 涵蓋帶留餘裕，只防極端組合病態值；**非文獻值、
   非 §6 登記容差**，正常音域（單元測試覆蓋）不觸及——程式註解已同文標示，
   不得成為事實上的容差放寬。
4. velocity 定義沿用既有 `jlimit(0.02, 1.0)` 正規化 proxy（架構限制，B4 不解決）。

實際造成的 tau_c 曲線（`tauc_curve_mirror.py` 鏡像重算，**先通過三重自我
驗證**：A4/v=0.5 錨點恆等、C2/C4/C7 力度指數 −0.394/−0.429/−0.500（與 C++
單元測試同一恆等式）、鏡像 H 比值對 anchor CSV 實測 p1_amp 比值 C2/C4 誤差
≤0.001 dB（C7 前後兩檔最大 0.036 dB，旁瓣陡峭區，僅列示不斷言）——鏡像
忠實於實作）：

| note | MIDI | α | K (N·m^−α) | m (kg) | 舊 tau_c @v=0.5 | 新 tau_c | 新/舊 | 力度指數 新（舊 −0.2） |
|---|---|---|---|---|---|---|---|---|
| C1 | 24 | 2.300 | 4.0e8 | 0.0120 | 4.595 ms | 3.130 ms | 0.681 | −0.394 |
| D1 | 26 | 2.300 | 4.0e8 | 0.0118 | 4.428 ms | 3.116 ms | 0.704 | −0.394 |
| C2 | 36 | 2.300 | 4.0e8 | 0.0110 | 3.681 ms | 3.048 ms | 0.828 | −0.394 |
| C4 | 60 | 2.500 | 4.5e9 | 0.0090 | 2.362 ms | 2.250 ms | 0.952 | −0.429 |
| **A4** | **69** | 2.625 | 1.74e10 | 0.00825 | **2.000 ms** | **2.000 ms** | **1.000（錨點）** | −0.448 |
| D5 | 74 | 2.694 | 3.68e10 | 0.00783 | 1.823 ms | 1.878 ms | 1.030 | −0.459 |
| C7 | 96 | 3.000 | 1.0e12 | 0.0060 | 1.214 ms | 1.448 ms | 1.192 | −0.500 |
| C8 | 108 | 3.000 | 1.0e12 | 0.0050 | 0.973 ms | 1.383 ms | 1.422 | −0.500 |

（C1/C8 兩列同時展示 flat 夾住行為：α/K 夾在 C2、C7 錨值；質量表自有
C1–C8 錨點所以仍逐音變化。）方向摘要：**低音接觸變短（變亮）、中音錨點
不動、高音接觸變長（輕彈變柔）＋力度敏感度全面變陡（最深 −0.500）**。

---

## §6 F3 velocity 主張域重定義——誠實專節（月月 2026-08-27 裁決 (b)）

**這一節記錄本輪唯一一項 GATE 判定語意修改。它動的是「主張的適用域」，
不是容差數值；依規則這是月月保留的權力，已由裁決包
`reports/decision_packets/B4_f3_velocity_ruling.md` 三選一裁定為 (b)。**

- **撞牆事實（停工時完整記錄，`b4_gate_full_FAIL.txt`／
  `b4_f3_alpha_monotonicity.txt`）**：B4 落地後 `--full` 的 F3 velocity
  檢查在 piano（Felt 路徑）三錨點的**模型自身預測 delta**（velocity
  0.378→0.756，f0 ±3% 帶）：

  | 錨點 | α | predicted_delta | 對 6.0206 dB 固定律的偏差 | 渲染實測 | 實測−預測 |
  |---|---|---|---|---|---|
  | C2 (36) | 2.3 | **+6.25 dB** | +0.23（過） | +6.2 | <0.1 |
  | C4 (60) | 2.5 | **+7.79 dB** | **+1.77（破 ±1.0）** | +7.8 | <0.1 |
  | C7 (96) | 3.0 | **+19.12 dB** | **+13.10（破 ±1.0）** | +18.9 | ≈0.2 |

  偏差隨 α 嚴格單調（C7>C4>C2）；渲染與模型自身預測吻合 <0.2 dB
  （match_ok 全過、law_ok 破）——引擎忠實執行公式，破的是「+6 dB 定律」
  這條主張本身。依卡 §12 停工、未自行處置，交裁決。
- **舊主張語意**（重定義前，全引擎一體適用）：f0 自帶 ±3% 帶內，
  (i) 渲染 delta 與 dump 重建的模型預測吻合（match_ok，±1.0 dB）**且**
  (ii) 模型預測本身落在固定律 6.0206±1.0 dB 內（law_ok）。
- **新主張語意**（重定義後）：**6.0206 dB 律本來就是「接觸時間不隨力度變」
  假設下的推論**——固定 tau_c 時 H(2πf0·tau_c) 在 lo/hi 兩渲染間相消，帶內
  delta 才化簡成純力學倍增。因此把 (ii) 的固定律主張**限縮到固定 tau_c 域**：
  - **tau_c(v)/Felt 域**（`probe_tauc_velocity_solved()`：Cimbalom 家族引擎
    × 有效 Felt exciter，即 `pianoHammerTauC()` 唯一接線的那條路；判定式是
    C++ 派發規則的無參數鏡像，fail-closed——讀不懂的 score 一律歸入**更嚴**
    的固定律域）：只判 match_ok（渲染 vs 模型自身預測），**容差沿用同一個
    `VELOCITY_DB_TOL = ±1.0 dB`，未放寬**；`predicted_delta` 與它對固定律
    參考值的偏差在**每一個** tau_c(v) 探針上（PASS 或 FAIL）誠實列印存證。
  - **其他所有引擎/exciter**：雙判定 (i)+(ii) **逐字元未動**——重定義後的
    `--full`（`b4_gate_full.txt`）裡 cimbalom(Wood)/tongue_drum/water_gong/
    water_gong_free 四列仍是 +6.1 dB 全 PASS、fm 仍 EXEMPT。
- **檢查的自證能力未被弱化**（`--selftest` 新增 4c，
  `b4_f3_redefine_sentinel.txt`）：(1) 正控制：與模型預測一致的 +19.12 dB
  合成渲染在新域 PASS（裁決 (b) 的要點）；(2) 反例：偷偷保留舊固定行為
  （渲染 +6.02）對上 +19.12 預測必 FAIL；(3) NaN fail-closed；(4) 域邊界
  五引擎逐一驗證只有 Felt 路徑落入新域；(5) 固定律在舊域仍拒收 +19.12。
  另做突變哨兵：把新判定函式猴補成永真後，整套 selftest 如預期轉 FAIL
  （exit 1）、其餘 12 條哨兵不受牽連。
- **R2 遵守聲明**：`VELOCITY_DB_TOL` 數值未動、匹配容差未放寬、力度指數
  未縮回 −0.2 假裝解出；改的只有裁決 (b) 授權的主張域語意。先例：2026-07-22
  F3 寬帶→窄帶域修正（同類「主張域」修改，同樣走裁決）。
- **誠實提醒（照裁決包原文）**：C7 +19 dB 是文獻公式推出來的行為，「聽起來
  對不對」屬美學範疇，最終由你與外部專業試聽把關；本報告只保證「程式忠實
  執行了溯源公式，且驗證器仍有偵錯能力」。

---

## §7 非 Felt／Chromatic／68 首不受影響——位元不變性（施工卡 §6 步驟 7）

1. **非 Felt 三檔探針**（cimbalom A4/v=0.5 × wood/cotton/metal，
   `nonfelt_invariance_{before,after}.txt`＋獨立重跑記錄
   `b4_nonfelt_invariance.txt`）：渲染 WAV SHA256、`--dump-modes` stdout
   SHA256、中央弦 32 partial amp，**除標題 label 行外逐位元相同**
   （wood `48748d25…`/cotton `b0d1afc4…`/metal `63ad3d9f…`，前後同值）。
2. **Chromatic 引擎零接觸**：`git diff` 唯二引擎/物理改動為
   `src/physics/HammerImpulse.h`（純新增）與 `src/engines/CimbalomEngine.h`
   （4 個呼叫點的 Felt 分支）；`ChromaticEngine.h` 0 行變動，且其 exciter
   走 `chromaticExciterHardness()`，與新函式無接線。
3. **68 首不受影響曲目的整曲 sentinel**（`unaffected_sentinels_check.py`，
   `unaffected_sentinels_after.txt`）：B4-before 的整曲 SHA256 基線直接取
   `b3_method/rep_pieces_after.csv`（B3-after 乾淨樹＝B4-before 同一狀態），
   6 首全部 B4-無關、涵蓋弦路徑三個非 Felt 檔位與 Chromatic，B4 後重渲染
   **SHA256 全部逐位元相同**：vivaldi_summer_m2/m3、vivaldi_autumn_m2
   （string/bow→Cotton）、moonlight_yangqin（cimbalom/wood_mallet→Wood）、
   ai_radiance_m1（cimbalom Wood＋Metal＋Chromatic 混編）、
   akashic_opening_bell（純 Chromatic 哨兵，含 tongue_drum/felt_mallet——
   正是「felt 家族 exciter 落在 Chromatic 引擎上不受影響」的實證）。
4. **corpus 全量**：`verify_score.py --all` 73/73 PASS、零新增 FAIL、零新增
   豁免（唯一豁免＝既有登記的 moonlight 休止 RMS 一筆；`b4_corpus_all.txt`）。

---

## §8 SHA256 改變＝預期行為聲明（§9 決定性聲明）

**受影響 5 首的渲染 WAV SHA256 全部改變——這是預期行為**（Felt 接觸時間
曲線變了 ⇒ 模態激發振幅權重變了），不是回歸；前後值逐首列於
`affected_render_{before,after}.csv`（例：physical_piano `ace07c6b…`→
`607d0d3b…`，ai_radiance_complete `c4f8b1ce…`→`979e00ae…`）。渲染本身
仍是決定性的：corpus 檢查含 determinism 雙渲染比對 73/73 全過（§7.4）；
`anchor_partials_after.csv` 於 F3 裁決落地後由同一 binary 重跑一次，與裁決前
產出**逐位元相同**（CLI 未變，裁決 (b) 只改 Python 判定端）。不受影響的
68 首與非 Felt 路徑 SHA256 不變（§7）。

---

## §9 GATE 完成狀態（證據皆在 `reports/gate_outputs/`）

| GATE | 結果 | 證據 |
|---|---|---|
| 開工前基線 `--full` | NO CHECKED FAILURES | `b4_baseline_full.txt` |
| CLI / VST3 / Standalone build | 三者成功 | `b4_build_{cli,vst3,standalone}.txt` |
| X4 規約：三測試 target 先重建 | 完成（兩輪：實作輪＋F3 裁決輪） | `b4_x4_rebuild_tests.txt`、`b4_f3_redefine_x4_rebuild.txt` |
| ctest | 3/3 Passed（含 §7 新增 `testPianoHammerContactSolver` 7 條，含反例） | `b4_ctest.txt`、`b4_f3_redefine_ctest.txt` |
| pytest | 128 passed（含 F3 域拆分單元測試） | `b4_pytest.txt`、`b4_f3_redefine_pytest.txt` |
| `--selftest` | 13/13 PASS（含新 4c 哨兵）；突變版如預期 FAIL exit 1 | `b4_selftest.txt`、`b4_f3_redefine_sentinel.txt` |
| `--full`（實作後、裁決前）| F3 FAIL（誠實存證，§12 停工） | `b4_gate_full_FAIL.txt`、`b4_f3_alpha_monotonicity.txt` |
| 月月裁決 | **(b) 重定義 F3 主張域**（2026-08-27） | `reports/decision_packets/B4_f3_velocity_ruling.md` |
| `--full`（裁決落地後） | **NO CHECKED FAILURES**（3 筆既有 rubber UNVERIFIED 不變） | `b4_gate_full.txt`（=`b4_gate_full_after_f3_redefine.txt`） |
| F3 三錨點單獨複驗 | 3/3 PASS＋誠實列印 predicted/偏差 | `b4_f3_redefine_alpha_recheck.txt` |
| corpus 全量 | **73/73 PASS**、零新增豁免 | `b4_corpus_all.txt` |
| 非 Felt/Chromatic/68 首位元不變 | 全部逐位元相同 | §7 各檔 |

---

## 附：方法與再現

before/after 各自用當下工作樹的 CLI，同一支腳本同參數只換 `--label`：
`scan_affected_scores.py`（§1）、`render_affected_pieces.py`（§2a，渲染在
repo 外）、`anchor_partials.py`（§3/§4）、`nonfelt_invariance.py`（§7）；
報告階段另增 `t60_f0_felt_events.py`（§2b/§3）、`audio_t60_sample.py`
（§2c）、`unaffected_sentinels_check.py`（§7）、`tauc_curve_mirror.py`
（§2a 歸因/§5 曲線表，含三重自我驗證）。逐欄位定義、封閉證據鏈與
before 檔保全說明見 `reports/gate_outputs/b4_method/README.md`。
RMS/質心定義為本目錄自我一致基準，不可與 B2/B3 報告的對應欄直接對減。
