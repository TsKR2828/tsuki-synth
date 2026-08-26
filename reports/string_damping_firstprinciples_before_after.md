# B3 Rule 10 前後對照報告：弦阻尼律換第一原理（Cuesta & Valette 三機制）

> 產出：2026-08-26（施工卡 `docs/workcards/B3.md` §9）
> 範圍：**只有 B3**——弦（Cimbalom/Piano/String，`StringModel`）阻尼律裡的
> 「空氣黏滯 `beta_air·f²`＋（現稱）聲輻射 `gamma_radiation·f`」兩項，換成
> Cuesta & Valette (1988) 的零自由參數三機制 `Q⁻¹_air + Q⁻¹_visc + Q⁻¹_disl`。
> before 基線＝B1+B2 落地後、B3 未動的工作樹（2026-08-24 採樣）。
> 方法腳本與原始資料：`reports/gate_outputs/b3_method/`（同一支腳本、同一組參數，
> before/after 各跑一次，見該目錄 README.md）。

---

## §0 白話導讀卡（§9 第 1 項）

**一句話結論：弦的「空氣阻力＋所謂聲輻射」兩個湊數字項換成有文獻出處、零自由
參數的物理公式後，代表曲聽感幾乎不動（整曲音量最大差 0.06 dB、音色亮度偏移
≤1%），高音尾巴稍微變長、少數厚弦音效明顯變短，73 首驗證曲全數通過。**

之前的狀況：弦的衰減公式裡有兩項的形狀是 `f²` 和 `f¹`，係數是查無出處的擬合
數字，而第一原理推導（`docs/STRING_DAMPING_SOURCES.md` §3）顯示**物理上根本
沒有 `f²` 這一項**——正確形狀是「空氣黏滯 `f^0.5`＋常數」「黏彈性 `f³`」
「位錯 `f¹`」三項。B3 把這兩個擬合項換成三機制公式，公式裡的每個量
（頻率、弦半徑、張力、密度、楊氏模數）都是已有參數，**零自由參數、
沒有任何新的可調數字**。舊的兩個欄位改名為 `beam_plate_*`，明示只給
Beam/Plate（舌鼓/鑼）用，弦完全不再讀它們。

聽感上會變什麼：**高音的尾巴稍微變長**（舊 `f²` 項在高頻把衰減壓過頭了，
steel C8 的 T60 從 0.18 s 回到 0.24 s），整體亮度微升（六首代表曲頻譜質心
+0.7%～+1.0%）；**極厚的弦（直徑 3 mm 的效果音）尾巴明顯變短**（黏彈項
∝ 半徑⁶，見 §5）。整曲音量幾乎不動。

**你要做的裁決**：接受這批改變，或指名回退。另有一個開放問題在 §3
（位錯常數與既有材質損耗的疊加方式），實測結果落在施工卡預估之內、
未觸發停工條款，預設照文獻公式全部加總，但數字全部攤開由你複核。
所有檔案未 commit，你保有完整否決權。

---

## §1 T60 對照表：3 材質 × 4 音（§9 第 2 項）

模型值，`--dump-modes` 中央弦基頻 decay；probe＝cimbalom、velocity 0.5、
直徑 0.8 mm 錨點慣例（與 B2 報告 §1 同一把尺；
`b3_method/t60_material_grid_{before,after}.csv`）。

| 材質 | 音 | f (Hz) | B1+B2 疊加後（B3 前） | B3 之後 | 比值（後/前） |
|---|---|---|---|---|---|
| steel | C2 | 65.4 | 17.655 s | 15.308 s | 0.867 |
| steel | C4 | 261.6 | 4.2969 s | 4.1425 s | 0.964 |
| steel | C6 | 1046.5 | 0.9714 s | 1.0649 s | 1.096 |
| steel | C8 | 4186.0 | 0.1756 s | 0.2428 s | **1.383** |
| aluminum | C2 | 65.4 | 47.138 s | 21.223 s | **0.450** |
| aluminum | C4 | 261.6 | 11.241 s | 7.6461 s | 0.680 |
| aluminum | C6 | 1046.5 | 2.3721 s | 2.3033 s | 0.971 |
| aluminum | C8 | 4186.0 | 0.3653 s | 0.5020 s | **1.374** |
| rubber | C2 | 65.4 | 0.1119 s | 0.1112 s | 0.994 |
| rubber | C4 | 261.6 | 0.02793 s | 0.02792 s | 0.999 |
| rubber | C6 | 1046.5 | 0.006944 s | 0.006991 s | 1.007 |
| rubber | C8 | 4186.0 | 0.001697 s | 0.001749 s | 1.031 |

**解讀**：

- **steel（實際樂器用的主力材質）**：C2 −13%、C4 −4%、C6 +10%、C8 +38%。
  方向符合形狀修正的預期——舊 `beta_air·f²` 在高頻壓太兇（C8 尾巴被砍太短）、
  在低頻又幾乎沒貢獻；新公式低頻端空氣項較強（`f^0.5`+常數）、高頻端只剩
  黏彈 `f³` 接手。C4 錨點 4.14 s 與 `--t60` GATE 的 cimbalom/piano 模型值一致
  （量測/模型比 1.05，容差 0.5–2.0 內，`b3_gate_outputs/b3_t60.txt`）。
- **aluminum：C2 折半（47.1 s → 21.2 s）是本表最大變化**。歸因見 §2：
  aluminum 密度低（2700），空氣項 `Q⁻¹_air ∝ ρa/ρ` 相對大，低頻端新空氣項
  是舊兩項合計的約 20 倍。**但要誠實補一句：目前 corpus 裡沒有任何一首曲子
  透過弦路徑用 aluminum**——逐檔解析 13 個含 aluminum 的 score，全部走
  `tongue_drum`/`beam`/`custom`（都是 Chromatic/Beam 路徑，B3 不動），
  所以這是「參考網格」的變化，沒有現有曲目受它影響。
- **rubber（高 eta 代表）**：全部 ≤3%。eta=0.3 佔總損耗 99% 以上（§2），
  換掉的兩項本來就是零頭。

---

## §2 三項分解表：eta／新三機制／B1 琴橋（§9 第 3 項）

施工卡 §6 步驟 15 的雙重歸因檢查產物，實作工兵已存
`b3_method/decomposition_after.json`（生成腳本 `decomposition_after_gen.py`），
本節直接轉錄。各項都是對 `1/T60` 的貢獻率（單位 1/s）：
`1/T60 = eta·f/2.2 + (Q⁻¹_air+Q⁻¹_visc+Q⁻¹_disl)·f/2.2 + bridgeLoss`。
括號內百分比＝該項佔總損耗率的份額。

| 材質 | 音 | eta 項 | 新三機制項 | B1 琴橋項 | 合計 1/T60 | T60 |
|---|---|---|---|---|---|---|
| steel | C2 | 0.00595 (9.1%) | 0.01051 (16.1%) | 0.04887 (74.8%) | 0.06533 | 15.31 s |
| steel | C4 | 0.02378 (9.9%) | 0.02212 (9.2%) | 0.19550 (81.0%) | 0.24140 | 4.14 s |
| steel | C6 | 0.09514 (10.1%) | 0.06197 (6.6%) | 0.78198 (83.3%) | 0.93909 | 1.06 s |
| steel | C8 | 0.38055 (9.2%) | 0.61047 (14.8%) | 3.12793 (75.9%) | 4.11895 | 0.243 s |
| aluminum | C2 | 0.00297 (6.3%) | 0.02723 (57.8%) | 0.01692 (35.9%) | 0.04712 | 21.22 s |
| aluminum | C4 | 0.01189 (9.1%) | 0.05122 (39.2%) | 0.06767 (51.7%) | 0.13079 | 7.65 s |
| aluminum | C6 | 0.04757 (11.0%) | 0.11590 (26.7%) | 0.27069 (62.3%) | 0.43416 | 2.30 s |
| aluminum | C8 | 0.19027 (9.6%) | 0.71884 (36.1%) | 1.08275 (54.4%) | 1.99186 | 0.502 s |
| rubber | C2 | 8.919 (99.2%) | 0.06442 (0.72%) | 0.00689 (0.08%) | 8.990 | 0.111 s |
| rubber | C4 | 35.68 (99.6%) | 0.11585 (0.32%) | 0.02757 (0.08%) | 35.82 | 0.0279 s |
| rubber | C6 | 142.7 (99.8%) | 0.22860 (0.16%) | 0.11028 (0.08%) | 143.0 | 0.00699 s |
| rubber | C8 | 570.8 (99.8%) | 0.49383 (0.09%) | 0.44112 (0.08%) | 571.8 | 0.00175 s |

新三機制項的內部組成（air / visc / disl 各佔三機制小計的百分比）：

| 材質 | C2 | C4 | C6 | C8 |
|---|---|---|---|---|
| steel | 84.3 / 0.02 / 15.7 | 69.6 / 0.5 / 29.9 | 46.0 / 11.3 / 42.6 | 9.0 / **73.7** / 17.3 |
| aluminum | **93.9** / 0.01 / 6.1 | 86.9 / 0.2 / 12.9 | 71.1 / 6.1 / 22.8 | 22.0 / **63.3** / 14.7 |
| rubber | 97.4 / ~0 / 2.6 | 94.3 / ~0 / 5.7 | 88.4 / ~0 / 11.6 | 78.6 / 0.02 / 21.4 |

**兩個交叉驗證**（都在 `decomposition_after.json` `_meta`）：

1. **量級分布符合 `docs/STRING_DAMPING_SOURCES.md` §4.2**：低頻空氣主導
   （steel C2 空氣佔三機制 84.3%）、高頻黏彈主導（steel C8 黏彈佔 73.7%）——
   與該文件用獨立參數算的分布同型。PASS。
2. **鏡像重算 vs 實際 binary**：用分解表加總的 `1/T60` 反推 T60，與
   `--dump-modes` 讀出的基頻 decay 逐格比對，12 格最大偏差 **0.0038%**——
   分解表就是引擎實際在算的東西，不是另一套紙上公式。

**歸因結論**：steel 的琴橋項佔 75–83%（B1 的結構未被 B3 動到）；aluminum 低頻
的變化主力是新空氣項（C2 佔 57.8%），不是位錯常數（位錯只佔三機制小計的 6.1%）。

---

## §3 `Q⁻¹_disl` 相對 `eta` 佔比表：全部 14 材質（§9 第 4 項，§11 最大風險攤開）

位錯常數 `Q⁻¹_disl = 1/18000` 是頻率無關的文獻擬合值，它跟 Phase H 已溯源的
材質內部損耗 `eta` 在 `1/T60` 裡**同為 `f¹` 項、直接相加**——物理上可能有
重疊計算的疑慮（原文獻的量測台架量不到我們的 `eta` 定義域，兩者是否完全
獨立無法從文獻判定）。佔比 `(1/18000)/eta` 越大，該材質被「多加」的阻尼
越多。逐材質實測（`data/materials.json` 現值）：

| 材質 | eta | (1/18000)/eta | 施工卡 §11 預估 |
|---|---|---|---|
| **aluminum** | 1e-4 | **55.56%** | ≈55.6%（一致） |
| **steel** | 2e-4 | **27.78%** | ≈27.8%（一致） |
| bronze | 1e-3 | 5.56% | 約 5–7%（一致） |
| brass | 1.5e-3 | 3.70% | 約 5–7%（略低於預估，風險更小） |
| glass | 1.5e-3 | 3.70% | 約 5–7%（略低於預估，風險更小） |
| copper | 2e-3 | 2.78% | （卡未列） |
| wood_spruce | 7e-3 | 0.79% | <1%（一致） |
| iron | 1e-2 | 0.56% | <1%（一致） |
| bamboo | 1e-2 | 0.56% | （卡未列） |
| wood_maple | 1.2e-2 | 0.46% | （卡未列） |
| wood_birch | 1.4e-2 | 0.40% | （卡未列） |
| wood_oak | 1.6e-2 | 0.35% | （卡未列） |
| nylon | 3.5e-2 | 0.16% | （卡未列） |
| rubber | 0.3 | 0.02% | <1%（一致） |

**§12 停工條款對照**：施工卡 §12 規定「佔比實測後發現遠超本卡估算
（例如某材質變化 >2×）」才停工提問。實測 steel 27.78%、aluminum 55.56%，
與卡上估算**逐位一致（比值 1.00×，遠低於 2× 門檻）**——停工條款未觸發，
本卡預設做法（照原文獻公式三項全加總）維持。

**但仍照 §11 要求把問題攤開給你**：aluminum 的 eta 只有 1e-4，位錯常數等於
在它的內部摩擦上再疊 55.6%；合併空氣項形狀變化後，aluminum C2 參考網格
T60 折半（§1）。**目前 corpus 沒有任何弦路徑曲目用 aluminum**（§1 解讀第 2
點，已逐檔驗證），六首代表曲的實測變化也極小（§4），所以本報告**不主張**
需要改加總方式；若你聽感上或未來寫 aluminum 弦曲時覺得阻尼過重，可以裁決
「低 eta 材質的位錯項是否改為 `max(eta, 1/18000)` 或其他組合方式」——
那會是新的一張卡，本卡不擅自决定。

---

## §4 六首代表曲整曲對照（§9 第 5 項）

before/after 都用各自當下的工作樹 CLI 完整渲染到 repo 外目錄
（`b3_method/rep_pieces_{before,after}.csv`；RMS＝整曲混單聲道、
質心＝整曲無窗 rfft 振幅加權，與 before 同一支腳本同一定義）。

| 曲目 | RMS 前 (dBFS) | RMS 後 | ΔRMS (dB) | 質心前 (Hz) | 質心後 | Δ質心 | 該曲弦組合錨點 T60 變化* |
|---|---|---|---|---|---|---|---|
| vivaldi_summer_m2 | −21.149 | −21.155 | −0.006 | 473.3 | 476.6 | +0.70% | −0.1%～−3.7%（5 組） |
| vivaldi_summer_m3 | −16.684 | −16.683 | +0.001 | 457.6 | 461.1 | +0.78% | −0.1%～−3.7%（5 組） |
| moonlight_yangqin | −23.890 | −23.906 | −0.016 | 794.5 | 800.7 | +0.77% | −0.9%～−2.8%（3 組） |
| akashic_opening_bell | −21.004 | −21.004 | **0.000** | 396.3 | 396.3 | **0.00%** | 無弦（null 哨兵） |
| ai_radiance_m1 | −22.319 | −22.380 | −0.061 | 2116.7 | 2133.8 | +0.81% | −2.2%～−3.3%（6 組） |
| vivaldi_autumn_m2 | −26.375 | −26.378 | −0.003 | 459.2 | 463.6 | +0.97% | −0.1%～−3.7%（5 組） |

\* 該曲實際使用的 damping_override 弦參數組合在 MIDI 60 錨點的 T60 變化範圍
（逐組數字見 `b3_method/damping_override_anchor_{before,after}.csv` 與
`damping_override_files_after.md` 的檔→組合對映）。

**解讀**：

- **整曲 RMS 最大差 0.061 dB、頻譜質心一致偏移 +0.7%～+1.0%（變亮）**——
  方向與 §1 的 C6/C8 T60 變長一致（高音尾巴衰減變慢、頻譜高端能量微增），
  幅度遠小於 B2 那輪（±0.6 dB）。聽感差異集中在高音尾長，不在音量。
- **`akashic_opening_bell` 是 null 哨兵**：只有 tongue_drum/water_gong 事件、
  無弦，WAV **SHA256 逐位元相同**
  （`c672c941…594683`，before = after）——證明 B3 的改動範圍確實隔離在弦，
  Beam/Plate 渲染路徑一個位元都沒變。

---

## §5 `damping_override` 錨點保證變化聲明（§9 第 6 項）

**聲明：使用 `damping_override` 的既有樂譜，在 MIDI 60 錨點上的 T60 現在也會
因為新增的 `Q⁻¹_air+Q⁻¹_visc+Q⁻¹_disl` 項而改變，不再是 B2 之前「逐位元保留」
的保證。** `damping_override` 的語意不變（仍然只取代 eta 內部摩擦項、換算尺
不變），但錨點 T60 是「override 項＋三機制項＋琴橋項」的合計，中間那塊從
`beta_air·f²+gamma_radiation·f` 換成了三機制，合計必然移動。這是已知、預期的
副作用（施工卡 §11 明列），引擎註解已同步誠實標示
（`src/engines/CimbalomEngine.h` 行 436-440「HONEST CHANGE NOTE (B3)」）。

**對帳**：施工卡沿用的「32 首」來自 `grep -l` 檔數，其中 2 個是非樂譜
（`scores/schema/score.schema.json`、`scores/originals/rules_v2_demo/README.md`）；
逐檔解析 JSON 認定實際使用 `damping_override` 的樂譜是 **30 首**，去重後
**36 組唯一參數組合**（35 組弦＋1 組 plate null 哨兵）。

受影響最大的組合（MIDI 60 錨點 T60，全表見
`damping_override_anchor_{before,after}.csv`）：

| 組合 | 所在樂譜 | 前 | 後 | 變化 |
|---|---|---|---|---|
| string/steel d=3.0 T=350 ov=0.4 | `restraint_ambient_001` | 1.6739 s | 1.0646 s | **−36.4%** |
| string/steel d=3.0 T=400 ov=0.5 | `restraint_ambient_001` | 1.3818 s | 1.0156 s | **−26.5%** |
| cimbalom/steel d=0.58 ov=0.28 | `ai_radiance_m3` | 2.5240 s | 2.4279 s | −3.8% |
| string/steel d=0.55 ov=0.34 | 四季全 12 首 | 2.2429 s | 2.1599 s | −3.7% |
| cimbalom/steel d=0.52 ov=0.46 | `ai_radiance_m1` | 1.7984 s | 1.7396 s | −3.3% |
| cimbalom/steel d=0.55 ov=0.48 | `moonlight_yangqin`（2 首） | 1.7069 s | 1.6584 s | −2.8% |
| string/nylon d=3.5 ov=0.3 | `ocean_ambient_001` | 2.1120 s | 2.1602 s | +2.3% |
| plate/bronze（null 哨兵） | `akashic_bell` | 7.4864 s | 7.4864 s | **0.0%** |

35 組弦組合的變化：**除 `restraint_ambient_001` 的兩組 3 mm 厚弦外，其餘 33 組
全部落在 −3.81%～+2.28% 之間，中位數 |Δ| = 1.8%**。厚弦組合變化大的原因是黏彈項
∝ 半徑⁶——直徑 3 mm 是錨點慣例 0.8 mm 的 3.75 倍，黏彈損耗即使在 261 Hz 也
成為可觀項；這兩組是拘束具環境音效（非旋律樂器音色），且該曲 corpus 檢查
PASS（`b3_corpus_B.txt`/`b3_corpus_D.txt`）。nylon 組合小幅變長是因為舊
`beta_air·f²` 對粗 nylon 弦的扣分比新公式重。

---

## §6 決定性（determinism）聲明（§9 第 7 項）

**所有含 Cimbalom/Piano/String 事件的既有 score，渲染 WAV 的 SHA256 都會
改變——這是預期行為（阻尼律形狀變了），不是回歸。** 六首代表曲中五首弦曲的
SHA256 全部改變（前後值逐首列於 `rep_pieces_{before,after}.csv`）；唯一不變的
是無弦的 `akashic_opening_bell`（§4 null 哨兵）。渲染本身仍是決定性的：
corpus 檢查含 determinism 雙渲染比對，73/73 全過（§8）。純
Chromatic（tongue_drum/plate/water_gong/custom/beam）與 FM 的檔案位元不變
（三機制項不進入其路徑、`beam_plate_*` 數值未動）。

---

## §7 Beam/Plate 完全不動重申（§9 第 8 項）

**本報告只涵蓋弦（Cimbalom/Piano/String 引擎，`StringModel`）；Beam/Plate
（舌鼓/鑼，`BeamModel`/`PlateModel`）的 `beam_plate_beta_air`/
`beam_plate_gamma_radiation` 完全不動、仍是未溯源狀態（TODO D1）。** 佐證：

1. `git diff src/physics/BeamModel.h src/physics/PlateModel.h` 各只有 3 行
   改動（1 行註解＋2 行欄位參照），**內容全部是 `beta_air`→
   `beam_plate_beta_air`／`gamma_radiation`→`beam_plate_gamma_radiation`
   改名，沒有任何數字或運算子變化**（施工卡 §11 的具體判準）。
   materials.json 的 28 個對應數值逐字未動（僅鍵名加前綴）。
2. `--t60` GATE 的 Chromatic 各列（tongue_drum/water_gong/water_gong_free
   × MIDI 60/72）模型值與量測值**與 B2 基線逐位相同**
   （30.14/12.93/7.49/3.51 s…，`b3_t60.txt` vs `b2_t60_baseline.txt`）。
3. plate/bronze 錨點哨兵 T60 前後同為 7.4864 s（§5 表末列）；
   純 Beam/Plate 曲 `akashic_opening_bell` WAV SHA256 逐位元不變（§4）。
4. 舊 schema fail-closed：materials 檔仍帶 bare `beta_air`/`gamma_radiation`
   時整檔拒載，新增測試含正反例（`b3_ctest.txt`；哨兵存證
   `b3_selftest_sentinel.txt`——先證明抓得到 `r⁶→r²` 冪次抄錯（7 FAIL），
   再證明正確版不誤報（0 failures））。

---

## §8 corpus 四分片結果摘要與 GATE 完成狀態

**corpus 73/73 PASS、零新增 FAIL、零新增豁免**；四分片 19+18+18+18 = 73
（以 `verify_score.py` 自印 `Selected shard N/4: X of 73` 為準）：

| 分片 | 檔數 | 結果 | 證據 |
|---|---|---|---|
| 0/4 | 19 | 19/19 passed（1 check 為既有登記豁免） | `b3_corpus_A.txt` |
| 1/4 | 18 | 18/18 passed | `b3_corpus_B.txt` |
| 2/4 | 18 | 18/18 passed | `b3_corpus_C.txt` |
| 3/4 | 18 | 18/18 passed | `b3_corpus_D.txt` |

唯一豁免＝既有登記的 moonlight 休止 RMS 一筆（FX-bypass 同窗實測
−120.0 dBFS，確認是 reverb/delay 尾巴不是乾模型衰減；非本卡新增）。
歷史敏感檔 `summer_m2`/`summer_m3`、本卡最大錨點變化檔
`restraint_ambient_001`、nylon 變長檔 `ocean_ambient_001` 全部 PASS。

其餘 GATE（證據皆在 `reports/gate_outputs/`）：

| GATE | 結果 | 證據 |
|---|---|---|
| materials.json 合法性 | 合法 JSON，`$schema` 已標 v2 (2026-08-24) | `b3_materials_json_valid.txt` |
| `--full` | NO CHECKED FAILURES（3 筆 rubber UNVERIFIED 為既有：cimbalom/tongue_drum/water_gong × rubber，T60 短於 8 週期量測下限） | `b3_gate_full.txt` |
| `--t60 --notes 60 72` | ALL WITHIN TOLERANCE（cimbalom/piano ratio 1.05，容差 0.5–2.0） | `b3_t60.txt` |
| CLI / Standalone / VST3 build | 三者 exit 0 | `b3_build_{cli,standalone,vst3}.txt` |
| ctest（X4：三 test target 先重建） | 3/3 Passed | `b3_ctest_rebuild.txt` + `b3_ctest.txt` |
| pytest | 121 passed | `b3_pytest.txt` |
| 新測試鑑別力哨兵 | 突變版 7 FAIL → 正確版 0 failures | `b3_selftest_sentinel.txt` |

---

## 附：方法與再現

before/after 各自用當下工作樹的 CLI，同一支腳本同參數只換 `--label`：
`t60_material_grid.py`（§1）、`decomposition_after_gen.py`（§2）、
`render_rep_pieces.py`（§4，渲染在 repo 外工作目錄）、
`damping_override_anchor.py`（§5）。逐欄位定義、機器與慣例見
`reports/gate_outputs/b3_method/README.md`。質心定義為本目錄自我一致基準，
不可拿去與 B2 報告 §4 的質心欄直接對減（README 註記）。
