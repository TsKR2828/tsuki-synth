# Phase H 前後對照報告：兩項音色會變的物理修正

> 依據：`ROADMAP_PHYSICS.md` 規則 10（音色會變的改動需告知）。
> 生成日期：2026-07-12。
> 授權：月月 2026-07-12 已同意兩項修正都可以做（(1) `PLATE_FREE_OMEGA` (4,0) 更新為文獻一致值；
> (2) materials 阻尼/楊氏模數物理化）。本報告是授權後、跑最終 corpus 之前的前後對照證據。
> 讀者：月月（聾人使用者）——全程用「物理量」描述變化，不用「聽起來」這種形容詞。

---

## 0. 這份報告在回答什麼問題

Phase H 這一輪有兩個獨立、都會改變既有渲染音訊的修正：

1. **特徵值修正**：`src/physics/PlateModel.h` 的 `PLATE_FREE_OMEGA`（free-edge 圓板特徵值表）
   `(m=4, n=0)` 項：`21.83f → 21.527f`。只影響 `water_gong_free`（自由邊緣水鑼）engine 的
   一個泛音比例，其餘引擎、其餘泛音完全不受影響。
2. **材質物理化**：`data/materials.json` 全部 14 種材質的 `damping.alpha`（阻尼常數三項之一）
   從「待溯源」的拍腦袋數字，改成用 `T60 ≈ 2.2/(f·η)` 這條標準阻尼-Q 關係，以文獻損耗因子 `η`
   反推、在 MIDI 60 錨點物理精確的新值；另外 `rubber.youngs_modulus` 從 `1.5e9 Pa`
   （比真實橡膠硬 100-1000 倍，疑似求解器穩定性選值）改成 `5e6 Pa`（真實橡膠量級）。
   這兩項改動同時影響 `cimbalom` / `tongue_drum` / `water_gong` / `water_gong_free` / `piano`
   （所有走 StringModel/BeamModel/PlateModel 的引擎），**FM 合成鋼琴（`fm` engine）完全域外不受影響**
   （`HammerImpulse`/材質資料庫都不在它的渲染路徑上）。

因為兩項修正的來源（一個是特徵值表格，一個是材質資料庫）彼此獨立、影響的引擎/參數也不重疊
（自由邊緣 (4,0) 只在 `freeEdge=true` 的水鑼路徑用到；材質阻尼在全部 5 個 modal 引擎都用到但邏輯上與
特徵值表無關），可以分成兩個階段各自歸因，不會互相污染因果推斷。

**先講結論**：兩項修正都是「方向正確、量級符合物理預期」的改動，且都已用理論公式或獨立數值重解逐點核對過
（見下方 §1/§2）。**同時，材質阻尼修正把幾種材質的 T60 拉長了一個數量級以上（尤其是低損耗金屬：鋼、鋁），
這直接暴露了兩個既有驗證 harness 在極端 T60 下的量測侷限**（§3），以及讓 `rubber` 材質在 f0 判定上開始
FAIL（§4）——這些都不是渲染管線的 bug，是「阻尼常數變得更真實」這個改動的直接、可預期後果，但仍然是
真實的新 FAIL，誠實列出、留給月月/Opus 裁決是否接受現況或做進一步調整。

---

## 1. Stage 1 ── 特徵值修正：`water_gong_free` (m=4,n=0)

完整推導與量測見既有存證 `reports/gate_outputs/phase_h_eig_delta.txt`（本報告直接引用，不重覆造輪子）：

- **改動**：`freeModes[]` 第 5 項 `{ 21.83f, 4, 0 }` → `{ 21.527f, 4, 0 }`（`PlateModel.h`），
  `physics_verify.py` 的 `PLATE_FREE_OMEGA` 鏡射同步改。
- **物理意義**：這個特徵值決定 `water_gong_free`（自由邊緣水鑼）在 (m=4,n=0) 模態的頻率比例；
  `ω ∝ sqrt(λ)`，`sqrt(21.527/21.83) = 0.99306` → 頻率下降 **-1.388%**（約 -24 cents）。
- **隔離驗證**：MIDI 60、bronze 材質探針，只切換這一個數字（其他所有程式碼、材質、渲染路徑完全相同）：

  | Partial | 內容 | 改前 | 改後 | 位移 |
  |---|---|---|---|---|
  | #4（m=1,n=1，對照組） | 未受影響的模態 | 1021.998 Hz | 1021.998 Hz | **0.000%**（不變，證明隔離乾淨） |
  | #5（m=4,n=0，本次修正） | 受影響的模態 | 1087.243 Hz（理論與量測皆同） | 1072.150 Hz（理論 1072.152，量測 1072.150） | **-1.388%**（與理論預測 -1.388% 精確吻合） |

- **結論**：量測位移與理論預測位元級吻合，且其餘所有泛音（partial 1-4）改動前後 0.000% 不變，
  確認修正確實只影響它該影響的那一個模態，沒有波及其他任何頻率。

---

## 2. Stage 2 ── 材質物理化：6 首代表曲目前後對照

方法沿用 M2 前後對照報告（`reports/m2_before_after_report.md`）的方法論：同一份 score，
分別用 **binary A**（HEAD `4c77c54`，`git stash` 取出後單獨編譯，改動前的 `TsukiSynthCLI.exe`）與
**binary B**（目前工作目錄，含本輪兩項修正）渲染，比較 RMS / peak / 頻譜質心 / T60（寬帶包絡估計）/
top-6 FFT partial。

渲染指令（可重現）：
```
<binary> scores/examples/<name>.score.json --output reports/phase_h_before_after/<before|after>
```
六首曲目涵蓋 cimbalom（揚琴 + 鋼琴路徑）、tongue_drum、water_gong 兩種邊界條件、以及 fm（域外對照組）：

| Score | 引擎 | SHA256 相同？ | ΔRMS | ΔPeak | Δ頻譜質心 | T60(寬帶估計) 前→後 |
|---|---|---|---|---|---|---|
| `fur_elise_opening`（**fm，域外對照組**） | fm | **是**（位元完全相同） | 0.000 | 0.000 | 0.00 Hz | 24.37s → 24.37s（不變） |
| `moonlight_sonata_i_yangqin`（cimbalom，steel） | cimbalom | **是**（位元完全相同，見下方說明） | 0.000 | 0.000 | 0.00 Hz | 3.37s → 3.37s（不變） |
| `moonlight_sonata_i_tongue_drum`（tongue_drum，aluminum/steel） | tongue_drum | 否 | **+0.869 dB（變大聲）** | -0.058 dB | **-13.7 Hz（變暗）** | 4.92s → 6.57s（**變長**） |
| `physical_piano`（piano→cimbalom 路徑，steel） | piano | 否 | **+3.589 dB（明顯變大聲）** | 0.000 | **-47.2 Hz（變暗）** | 1.29s → 24.91s（**大幅變長，~19倍**） |
| `water_gong_clamped`（water_gong，bronze） | water_gong | 否 | **+4.817 dB（明顯變大聲）** | 0.000 | **-141.6 Hz（明顯變暗）** | 1.29s → 7.91s（**變長，~6倍**） |
| `water_gong_free`（water_gong，bronze，含 Stage 1 特徵值修正） | water_gong | 否 | **+4.821 dB（明顯變大聲）** | 0.000 | **-79.4 Hz（變暗）** | 2.69s → 11.67s（**變長，~4倍**） |

原始數字：`reports/phase_h_before_after/results.pkl`（可用 `analyze.py` 重新產生）；
WAV 檔案：`reports/phase_h_before_after/{before,after}/*.wav`；分析腳本：
`reports/phase_h_before_after/analyze.py`。

### 2.1 為什麼 `fur_elise_opening` 位元完全相同（預期，非疏漏）

跟 M2 報告的邏輯完全一樣：這首曲子只用 `"engine": "fm"`，材質資料庫（`MaterialDB`/`HammerImpulse`）
完全不在 FM 合成路徑上，ROADMAP_PHYSICS.md §0 早就把它列為域外項目。這是本次改動範圍精準卡在
StringModel/BeamModel/PlateModel 三個物理域內、沒有波及不該碰的東西的交叉驗證。

### 2.2 為什麼 `moonlight_sonata_i_yangqin` 位元完全相同（重要發現，非疏漏）

檢查這首曲子的 score JSON 發現，**全部 1142 個事件都帶 `"damping_override"` 欄位**
（例如 `{"material": "steel", ..., "damping_override": 0.34}`）。`damping_override` 是
per-note 直接覆寫阻尼常數的參數——一旦設定，這個音符的衰減完全不查 `materials.json` 的
`damping.alpha`，本次修正的新 `alpha` 值對它完全不生效。這不是分析疏漏，而是這首曲子的作曲選擇
（逐音手動調過阻尼）剛好讓它對材質阻尼的物理化改動免疫。**這正確地示範了 `damping_override`
這個逃生艙的用途**：如果月月希望某首既有曲子的音色不隨材質物理化改變，幫每個音符加
`damping_override` 就能鎖住舊行為，不需要回退全域修正。

### 2.3 其餘 4 首：RMS 變大聲、頻譜變暗、T60 變長 —— 全部同一個機制

`decayDenom = alpha + beta_air·f² + gamma_radiation·f`（String/Plate）或 `2·alpha + ...`（Beam），
`alpha` 這次全面下修（例如 steel `0.5→0.0238`，降到約 1/21；bronze `0.8→0.1189`，降到約 1/6.7；
aluminum `0.3→0.0119`，降到约 1/25——詳見 `reports/materials_physicalization_proposal.md` §3 表）。
因為 `alpha` 是**與頻率無關**的一項，`beta·f²`/`gamma·f` 兩項維持不變，`alpha` 下修的結果是：

1. **低頻模態（基頻附近）受益最大**：低頻模態原本主要被 `alpha` 主導阻尼，`alpha` 大砍之後這些模態的
   T60 大幅拉長，在固定的渲染/分析窗內累積能量變多 → **RMS 上升**（4 首都是正值，1.3-19x 不等的 T60
   延長對應觀察到的 0.87-4.82 dB RMS 增加）。
2. **高頻模態受益較少**：高頻模態原本就主要被 `beta·f²` 這個沒變的項主導，`alpha` 砍不砍差別不大，
   T60 幾乎不變。
3. **淨效果＝低頻相對變大聲、高頻相對沒變 → 頻譜質心整體下降（變暗）**：4 首曲子的頻譜質心全部下降
   （-13.7 到 -141.6 Hz），跟這個機制的方向完全一致，且下降量級跟該曲子的音域/材質對應的 alpha 下修比例
   吻合（water_gong 兩首用 bronze，alpha 只降到 1/6.7，質心降幅居中；piano 用 steel，alpha 降到 1/21，
   T60 拉長最多、質心降幅也最大）。
4. **音高（f0）不受影響**：4 首曲子的 top partial 頻率位置（`analyze.py` 的 top-6 FFT 表，見
   `reports/phase_h_before_after/results.pkl`）在改動前後幾乎完全對齊（例如 physical_piano 的
   328.5 Hz 基頻 partial 前後都在 328.5 Hz，water_gong_clamped 的 261.5→261.62 Hz 差異在 FFT
   解析度誤差內）——這與 `materials_physicalization_proposal.md` §1.3/§5.2 的推導一致：
   `alpha`/`beta`/`gamma` 只進 `decayDenom`（衰減），不進頻率公式；`youngs_modulus` 只在
   `CimbalomEngine.h` 影響 `spectralTilt`（頻譜滾降形狀），`BeamModel`/`PlateModel` 的
   `tuneChromaticModesToMidi()` 會把 E 的整體縮放效果完全抵消掉，兩者都不動音高。

**結論（Stage 2 整體評估）**：4 首受影響曲目的變化——變大聲（RMS +0.9~+4.8 dB）、變暗
（頻譜質心 -14~-142 Hz）、衰減變長（T60 延長 1.3~19 倍）——全部同一個機制（`alpha` 大砍、
`beta·f²`/`gamma·f` 不變）解釋，音高不受影響，方向與量級跟 `materials_physicalization_proposal.md`
§6 的預測 T60 影響表定性一致（該表用純模型數學算的預測值，本報告是實際渲染音訊的獨立量測驗證）。

---

## 3. 新暴露的問題 1／2：T60 harness 在極端長衰減下失真（cimbalom/piano，多弦拍頻）

`python tools/physics_verify.py --t60 --notes 60 72` 存證：`reports/gate_outputs/phase_h_gate_t60.txt`。

```
engine      MIDI    model     meas  ratio
cimbalom      60   26.85s    7.61s  0.28 << FAIL  (beat 1.51 Hz)
cimbalom      72   14.89s   11.84s   0.80  (beat 3.02 Hz)
piano         60   26.85s    7.61s  0.28 << FAIL  (beat 1.51 Hz)
piano         72   14.89s   12.01s   0.81  (beat 3.02 Hz)
（tongue_drum / water_gong / water_gong_free 全部 MIDI 60/72 皆 1.00，不受影響）
```

**這是新出現的 FAIL，§6 判定制容差 0.5-2.0 沒有被修改（Rule 2）**，需要如實列出：

- `cimbalom`/`piano` 在 MIDI 60 的預測 T60 從舊值躍升到 **26.85s**（steel 的 `alpha` 大砍後的直接後果，
  跟 §2.3 機制一致），但 `T60_PROBE_DUR` 這個 harness 常數固定是 **5.0 秒**（`tools/physics_verify.py`，
  M5-5a 就定死的探針長度）——渲染出來的音訊裡，note-off 前只有約 4.5 秒可用來擬合衰減曲線，
  連 1/5 個真實 T60 週期都不到。
- 更關鍵的是 measure_t60() 對多弦課（cimbalom/piano）額外做的「拍頻週期平均」步驟（M5-5a，用來拉平
  多弦 detuning 造成的包絡起伏，見 `ROADMAP_PHYSICS.md` M5 條目）：這一步的前提隱含假設「在分析窗內，
  拍頻造成的包絡起伏相對衰減本身是小擾動」。但現在衰減慢到幾乎看不出來（5 秒內振幅幾乎沒掉），
  拍頻造成的週期性凹陷（beat notch）在振幅上的相對占比反而變得**跟衰減本身同量級甚至更大**，
  導致對數包絡回歸抓到的斜率被拍頻凹陷帶偏，量出一個比真實模型衰減快得多的假 T60（測到 7.61s，
  是模型值的 28%）。單弦引擎（tongue_drum/water_gong/water_gong_free）沒有這個拍頻平均步驟，
  所以即使它們的 T60 同樣被材質修正拉長，量測依然準確（ratio 精確 1.00）。
- **這不是渲染管線的 bug**：這是 M5-5a 那一版 harness 設計時，隱含假設了「T60 不會比探針時長長太多」，
  而材質阻尼物理化這次把這個假設直接打破（畢竟這正是把數字改得更真實的直接後果——真實的鋼/鋁確實可以
  響很久）。

**需要月月/Opus 決定**（已登記 `TODO.md`，見文件同步章節）：
(a) 接受現況——這 2 個 FAIL 反映的是 harness 測量侷限而非渲染錯誤，登記為已知限制，不動 §6 容差；
(b) 授權下一輪把 `T60_PROBE_DUR` 加長（例如到 30-40 秒）以正確測量新的長 T60，這是 harness 邏輯改動，
不是容差調整，需要重新產生所有 T60 相關 GATE 存證；
(c) 授權下一輪修 `measure_t60()` 的拍頻平均邏輯（例如偵測「拍頻週期數遠少於衰減所需週期數」時改用
不同的估計法）。

---

## 4. 新暴露的問題 2／2：`rubber` 材質在 f0 材質掃描中開始 FAIL

`python tools/physics_verify.py --full` 存證：`reports/gate_outputs/phase_h_gate_full.txt`
（material scan 段落）：

```
cimbalom    material=rubber   f0 measured=255.420 Hz expected=261.626 Hz  -41.6 cents [FAIL]
tongue_drum material=rubber   f0 measured=245.728 Hz expected=261.626 Hz -108.5 cents [FAIL]
water_gong  material=rubber   f0 measured=270.145 Hz expected=261.626 Hz  +55.5 cents [FAIL]
```

**根因（本報告用 binary A vs B 直接排查確認，非猜測）**：`rubber.youngs_modulus` 的物理化
（`1.5e9→5e6 Pa`）搭配 `rubber.damping.alpha` 的物理化（`2.5→35.676`，14.3 倍暴增，因為橡膠的文獻損耗因子
`η≈0.3` 遠高於其他材質）共同把 rubber 材質的 T60 壓到 **0.028 秒（String/Plate）／0.014 秒（Beam）**
——`materials_physicalization_proposal.md` §6 表已預測到這一點，標記為「collapses to a near-instant
thud」。用 `tools/physics_verify.py` 自己的 `measure_f0()` 函式（跳過前 50ms 攻擊瞬態、量測
50ms-1.55s 窗）直接對 binary B 重新探測 rubber 材質：**三個引擎的 `measure_f0()` 全部回傳
`None`（找不到頻率）**——因為 50ms 之後訊號已經完全衰減沒了（T60=28ms，50ms 已經過去接近 2 個 T60，
振幅早已跌破可分辨範圍，甚至可能在浮點運算中直接下溢為 0.0f）。`scan_materials()` 判定邏輯裡有一個
fallback（`measure_f0()` 是 None 時退回 `measure_partials()` 的基頻估計值），而 `measure_partials()`
是對「full 波形」（含攻擊瞬態）做窗函數 FFT，在瞬態噪聲主導、真正的模態頻率幾乎不存在能量的狀況下，
量出來的「基頻」峰值其實是攻擊瞬態噪聲頻譜的偶然峰位，跟真實模態頻率沒有穩定關係——這正好解釋了
為什麼三個引擎測到的偏移方向、量級都不一樣（-41.6 / -108.5 / +55.5 cents，沒有一致方向），因為它們
測到的根本不是同一種東西的一致偏差，是各自瞬態噪聲頻譜的偶然峰位。

**這不是渲染管線的 bug，是「rubber 現在物理上是一個幾乎無音高的瞬時悶響」這個事實，撞上了
「f0 材質掃描假設每個材質都能穩定測到一個基頻」這個 harness 假設**。`ROADMAP_PHYSICS.md` 的材質掃描
判定訊息本身早就預留了這個情況的處理方式（`"Do NOT widen tolerance — record this material as unsupported
for X or fix the model"`），這正是這條路徑該用的時候。

**需要月月/Opus 決定**（已登記 `TODO.md`）：
(a) 接受現況——把 `rubber` 材質正式登記為 `cimbalom`/`tongue_drum`/`water_gong` 這三個引擎 f0
材質掃描的「已知不支援」項目（附上述物理原因：真實橡膠阻尼確實會讓槌擊變成無明確音高的悶響，
這是文獻一致的物理行為，不是模型缺陷）；
(b) 授權下一輪重新檢視 `rubber` 的 `η` 選值是否要往「有明確音高但仍然悶」的方向調整（例如選文獻範圍
`0.1-1` 的低端而非中段），這需要另一輪規則 10。

---

## 5. 已確認「沒有變」的部分（交叉驗證，非疏漏）

- **`--amps` GATE**（`reports/gate_outputs/phase_h_gate_amps.txt`）：全部 5 個 modal 引擎、
  MIDI 60 前 5 個 partial 振幅判定 `RESULT: ALL WITHIN TOLERANCE`——材質阻尼/E 修正沒有動到
  `--dump-modes` 回報的 t=0 振幅，跟 M2 已驗證的槌頭頻譜模型互不影響，符合預期。
- **音高（f0）**：§2.3 已確認 4 首受影響曲目的 top partial 頻率位置改動前後對齊；`--full` 的
  note-range scan（非 rubber 材質、非極端高音）全部維持 PASS。
- **`fur_elise_opening`（fm）與 `moonlight_sonata_i_yangqin`（`damping_override` 全覆蓋）**：
  兩種不同原因的位元級不變，皆已在 §2.1/§2.2 解釋，不是分析疏漏。

## 6. 附帶發現：piano MIDI 108（極高音）f0 判定從 PASS 變 FAIL（供對照，另案追蹤）

`--full` 的 note-range scan 對 `piano` MIDI 108（f0=4186 Hz，piano 引擎宣告範圍的最高音）
在改動後回報 `f0 +5.2 cents [FAIL]`（`reports/gate_outputs/phase_h_gate_full.txt`）。用同一套
`measure_partials()` 方法分別對 binary A／B 重新量測（steel 材質，MIDI 108）：
**binary A：+0.23 cents（PASS，margin 大）；binary B：+7.33 cents（本報告獨立重測，与 GATE
記錄的 +5.2 cents 方向一致，量級相近，差異來自量測窗口的些微不同）**——確認這是材質阻尼修正
（steel `alpha` 大砍、T60 大幅拉長）造成的**新** FAIL，不是既有／無關的問題。推測機制：MIDI 108
是 piano 宣告範圍的最頂端，這裡的固定分析窗（0.05-1.55s）裡，過去高頻泛音很快衰減乾淨，
現在因為 T60 大幅拉長，泛音之間的頻譜洩漏（spectral leakage）在同一個窗內累積更多，
輕微地把基頻的功率質心估計值拉偏了幾個 Hz。跟 §3/§4 一樣，這是「衰減變得更真實」這件事
撞上「固定分析窗口」這個 harness 假設的又一個案例，同樣列入 `TODO.md` 待裁決清單，
不在本報告自行決定是否要縮小 `ENGINE_RANGES['piano']` 或調整分析窗。

---

## 7. 總結

| 修正 | 影響範圍 | 理論吻合度 | 新暴露的 FAIL |
|---|---|---|---|
| Stage 1：`PLATE_FREE_OMEGA` (4,0) 21.83→21.527 | 僅 `water_gong_free` 一個模態 | 位元級吻合（-1.388% 測與算一致） | 無 |
| Stage 2：14 材質 `damping.alpha` + `rubber.youngs_modulus` | `cimbalom`/`tongue_drum`/`water_gong`/`water_gong_free`/`piano`（5 引擎皆用材質資料庫）；`fm` 域外不受影響 | 方向與量級跟預測表一致（RMS↑/頻譜變暗/T60↑，音高不變） | 3 項：(1) cimbalom/piano MIDI60 T60 判定 FAIL（harness 探針時長侷限）、(2) rubber 材質 f0 掃描 3 引擎全 FAIL（rubber 變成無明確音高的瞬時悶響，harness 找不到基頻）、(3) piano MIDI108 f0 判定從 PASS 轉 FAIL（固定分析窗遇上大幅拉長的 T60） |

兩項修正本身都物理站得住腳、都有可重現的理論/獨立數值核對支持。三個新 FAIL 全部誠實列出、
根因追到底（不是渲染 bug，是「阻尼常數變得更真實」這個改動跟既有 harness 的固定假設——5 秒探針、
假設每個材質都能測到基頻、固定 1.55 秒分析窗——互相碰撞的直接後果），已登記 `TODO.md` 供月月/Opus
裁決是否接受現況、或授權下一輪調整 harness 本身。

---

## 8. 附錄：檔案清單

| 檔案 | 內容 |
|---|---|
| `reports/gate_outputs/phase_h_eig_delta.txt` | Stage 1 特徵值修正的隔離驗證證據（既有存證，本報告引用） |
| `reports/phase_h_before_after/binA/TsukiSynthCLI_A.exe` | HEAD `4c77c54`（`git stash` 取出後單獨編譯）的 CLI，Stage 2 對照組 |
| `reports/phase_h_before_after/binB/TsukiSynthCLI_B.exe` | 目前工作目錄（含兩項修正）的 CLI |
| `reports/phase_h_before_after/before/*.wav` | binary A 渲染的 6 首曲目 |
| `reports/phase_h_before_after/after/*.wav` | binary B 渲染的 6 首曲目 |
| `reports/phase_h_before_after/analyze.py` | RMS/peak/頻譜質心/T60/top-partial 分析腳本（可重現） |
| `reports/phase_h_before_after/results.pkl` | 分析腳本的原始輸出 |
| `reports/gate_outputs/phase_h_gate_full.txt` | `--full` GATE（binary B，含 rubber/piano-108 FAIL） |
| `reports/gate_outputs/phase_h_gate_t60.txt` | `--t60` GATE（binary B，含 cimbalom/piano MIDI60 FAIL） |
| `reports/gate_outputs/phase_h_gate_amps.txt` | `--amps` GATE（binary B，全 PASS，確認振幅判定不受影響） |
| `reports/materials_physicalization_proposal.md` | Stage 2 數值來源與預測表（月月已核准執行的提案文件） |
| `docs/MATERIALS_SOURCES.md` / `docs/EIGENVALUE_SOURCES.md` | 兩項修正各自的文獻溯源文件 |

本報告未修改 `data/`、`src/` 任何檔案；未 commit、未 push（Rule 7）。
