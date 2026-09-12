# 外部資料集補充登記：Weinzierl 2018 JASA ＋ Iowa MIS 泰國鑼

> 建立：2026-09-09　卡：`docs/workcards/WF0909_P6_a8_supplement.md`（研究卡，執行 Opus）
> **本文所有外部來源的存取日期一律為 2026-09-09。**
> 前情：`docs/EXTERNAL_DATASET_A8.zh-TW.md`（TU Berlin 資料集，禁商用）、
> `docs/EXTERNAL_DATASET_ALTERNATIVES.zh-TW.md`（替代方案調查，找到本文這兩個來源）。
> **本文件不改任何程式碼、不改任何容差、不宣稱任何「模型與實測吻合」。**
> 資料檔存放於 `external_data/`，**已在 `.gitignore`，不進版控**；repo 只留授權原文、SHA256 與比對數字。

---

## §0 一句話結論（給月月）

**兩個「可以拿去賣」的來源都下載進來了，也都各自查證過授權原文；它們補上了 TU Berlin 那份禁商用資料補不了的洞，但同時也各露出一個新缺口。**

- **Weinzierl 2018（論文 PDF，CC BY 4.0，可商用）**：這是目前唯一一份「有拿校準器校準過、又可商用」的絕對音量數字表。
  它讓我們第一次能說：TsukiSynth 算出來的絕對量**沒有離譜**（詳見 §2.1）。
  **新缺口**：這張表裡**沒有鋼琴**（我把全文都搜過了，「piano」只出現在參考文獻的標題裡）。
  卡上原本寫的「拿 TABLE I 鋼琴聲功率級來對照」**做不到**，我改用表裡**唯一的敲擊樂器「定音鼓」**當量級參照，並如實標明這是替代品。
- **Iowa MIS 泰國鑼（錄音檔，網站明寫「沒有限制」，可商用）**：這是本專案第一次拿到**有音高的真鑼**錄音。
  **新缺口（也是本卡最重要的發現）**：真泰國鑼**最強的那個泛音**落在基頻的 **2.000 倍**（幾乎是完美的八度）；
  我們 `water_gong` 引擎**最強的那個泛音**落在 **1.738 倍**，而且引擎**在 2.000 倍上根本沒有任何一根**——
  上下最近的兩根是 **1.7384 倍**（低 **243 音分**）與 **2.3286 倍**（高 **263 音分**）。
  （**音分是什麼**：鋼琴上相鄰兩鍵＝1 個半音＝**100 音分**；1 個全音＝2 個半音＝200 音分。
  所以 243 音分 ≈ **2.4 個半音**、263 音分 ≈ **2.6 個半音**，換句話說**兩根都差了兩個琴鍵以上**。）
  **兩者差很多，而且不是誤差等級的差，是形狀假設不同造成的。**
  泰國鑼是中間凸一個「乳突」的鑼；我們的引擎模擬的是一片**平的圓板**。
  → **這不是紅燈、不是 GATE、不代表引擎壞掉**，它代表的是：**`water_gong` 目前的物理模型不是泰國鑼的模型**。
  月月要不要為此做什麼，是後續決策，本卡不動任何程式。

**兩件跟卡上寫的不一樣、必須先講的事**（不影響結論，但必須誠實登記）：

| 卡上寫 | 實際 |
|---|---|
| Weinzierl PDF「約 1 MB」 | 實際 **2,094,542 bytes（約 2.09 MB）** |
| Iowa 泰國鑼三包「約 90 MB」 | 實際三包合計 **35,977,875 bytes（約 36.0 MB）**。「三包」對得上（ff／mf／pp 三個力度各一包），只是總量比預估小 |

---

## §1 兩來源登記表

### 1.1 Weinzierl et al. 2018, JASA（論文 PDF）

| 項目 | 內容 |
|---|---|
| **正式名稱** | Weinzierl, S., Lepa, S., Schultz, F., Detzner, E., von Coler, H., Behler, G. (2018). “Sound power and timbre as cues for the dynamic strength of orchestral instruments,” *J. Acoust. Soc. Am.* **144**(3), 1347–1355. |
| **DOI** | `10.1121/1.5053113` |
| **本機路徑** | `external_data/weinzierl_2018_jasa/weinzierl_2018_jasa_1.5053113.pdf`（gitignore） |
| **大小 / SHA256** | 2,094,542 bytes ／ `d3e07db54505dc73c929d61202bced4ef0488b2649eb6e1634741126af3dc91b` |
| **取得 URL** | `https://api-depositonce.tu-berlin.de/server/api/core/bitstreams/d7d0f7af-e49b-4b86-8e7d-4293aef0440a/content`（TU Berlin DepositOnce 開放全文，2026-09-09 下載成功，HTTP 200，`Content-Disposition: filename="1.5053113.pdf"`） |
| **授權原文（A 級：PDF 本體）** | 「licensed under a Creative Commons Attribution (CC BY) license」<br>（本機 PDF 第 2 頁＝期刊 p.1347，摘要下方版權列，接 `http://creativecommons.org/licenses/by/4.0/`） |
| **授權交叉驗證（B 級）** | Crossref API `https://api.crossref.org/works/10.1121/1.5053113`（2026-09-09 本機 curl 實打）回 `license = https://creativecommons.org/licenses/by/4.0/`，`content-version` 有 `vor` 與 `tdm` 兩筆 |
| **商用可否** | **可以（CC BY 4.0，需標示出處）。** |
| **校準狀態** | **有校準，且有 A 級原文。**<br>原文：「a pistonphone calibrator (B&K 4230, 94 dB @ 1 kHz) was used」（PDF p.5＝期刊 p.1350，§II A） |
| **量測設定（A 級原文）** | 「radius of approximately r = 2.1 m, and 32 Sennheiser KE4-211-2」（PDF p.3＝期刊 p.1348）<br>「the fully anechoic chamber at TU Berlin has a lower limiting frequency」（同頁，接 `f = 63 Hz`，自由容積 `V = 1070 m³`）<br>方法：ISO 3745 包絡面法 |
| **對哪個引擎有用** | `RadiationModel` ／ B6「方案 B」的**絕對量級合理性檢查**。<br>表裡唯一的敲擊樂器是 **Timpani（定音鼓）**——它是**膜**，不是我們的梁／板／弦，只能當「敲擊類樂器大概多大聲」的量級參照。 |
| **不可用於** | **不可**當 GATE、**不可**當 specimen 證據、**不可**把它的數字寫成 `src/` 常數。（理由同 A8 §4.1 選項 A。） |

> **本卡順帶查到的一件事，直接關係到 A8 §4.2 那個「1.05 m」**：
> 這篇論文的 p.1348（PDF p.3）有一句 A 級原文：
> 「of the sound radiating parts of d0 > r/2 = 1.05 m」
> （完整句：「None of the musical instruments recorded exhibited a characteristic dimension of the sound radiating parts of d0 > r/2 = 1.05 m.」）
> 也就是說：**「1.05 m」這個數字確實出現在原始文獻裡，但它是「陣列半徑的一半」，是用來檢查「樂器本身夠不夠小」的門檻，
> 不是麥克風擺放的距離。** 這正好解釋了本專案當初為什麼會把 1.05 m 誤記成「照抄那個資料庫」。
> **A8 §4.2 選 X（只改說法、不動數字）是對的**，本卡的新證據支持該裁決，見 A8 §4.2 的裁決記錄。

### 1.2 University of Iowa Musical Instrument Samples — 泰國鑼三包（錄音檔）

| 項目 | 內容 |
|---|---|
| **來源頁** | `https://theremin.music.uiowa.edu/MISgongtamtams.html`（列出 ff／mf／pp 三個 zip 的那一頁）<br>總說明頁：`https://theremin.music.uiowa.edu/MIS.html` |
| **本機路徑** | `external_data/iowa_mis_thai_gong/`（gitignore） |
| **檔案（三包）** | `thaigong.ff.zip` 14,996,504 bytes ／ SHA256 `790bf82f3ebf654ce02df488131a425b8dcbd334e807e27e28a69e506392b3a7`<br>`thaigong.mf.zip` 11,998,206 bytes ／ SHA256 `59e081df62f5539e0086947a6f818e4e770156ac063ade843bf4f4472e6f588d`<br>`thaigong.pp.zip` 8,983,165 bytes ／ SHA256 `cc8d543dd8555e4eed259f461e2f9e6b74949686e8cba00fda70c5b1bcca8bda`<br>（每包 13 個 `.aif`，C4–C5 逐半音；**逐檔 SHA256 見附錄 A**） |
| **伺服器回報 `Last-Modified`** | 三包皆 2016-06-07（HTTP HEAD，2026-09-09） |
| **授權原文（B 級：官網聲明，非正式授權書）** | 「may be downloaded and used for any projects, without restrictions」<br>（`https://theremin.music.uiowa.edu/MIS.html`，2026-09-09，本機 curl 抓原始 HTML 逐字比對）<br>完整句：「Since 1997, these recordings have been freely available on this website and may be downloaded and used for any projects, without restrictions.」 |
| **商用可否** | **可以。** 但這是**網頁上的一句話**，不是 CC 標章、不是 LICENSE 檔。<br>→ 已於 2026-09-09 記下逐字原文與存取日期；若日後要放進出貨物，建議先把該頁存成 PDF 存證。 |
| **校準狀態** | **未校準。** 全站沒有任何校準器／Pa／dB SPL 的敘述（`MIS.html` 與該樂器頁皆已逐字檢查）。<br>→ **只能拿來比「頻率比值」與「相對衰減」，不能拿來比絕對音量。** |
| **器材／距離（網頁表格逐欄抄錄，2026-09-09）** | Instrument = `Gongs & Tamtams`；Performer = `Andrew Thierauf`；Date = `March 20, 2013`；Location = `Anechoic Chamber`；Technicians = `Daniel Frantz and Will Huff`；**Distance = `5 feet`**（約 1.52 m）；**Microphone = `Earthworks QTC40`**；Interface = `Metric Halo 2882`；Format = `24-bit, 44.1 kHz, stereo` |
| **實際檔案格式（本機 `soundfile` 讀出）** | AIFF、`PCM_24`、44,100 Hz、**2 聲道**。`thaigong.C4.ff.aif` 13.364 s；`thaigong.G4.ff.aif` 10.767 s |
| **對哪個引擎有用** | `ChromaticEngine::WaterGong`（**本專案第一次拿到有音高的真鑼**）。<br>`TongueDrum` 無對應；`FMPianoEngine`／`CimbalomEngine` 無對應。 |
| **一個必須登記的網站不一致** | 上面那張器材表**同時出現在「Pre-2012」與「Post-2012」兩個頁面**，內容一字不差（都寫 2013-03-20）。<br>本卡下載的三包是掛在 **Pre-2012** 頁的 `thaigong.{ff,mf,pp}.zip`。<br>→ **無法從網頁確定這三包與 2013 那場錄音是不是同一批。** 這是已知缺口，見 §3。 |

---

## §2 首批數字（**informational，不判 PASS／FAIL，不證明模型正確**）

### 2.0 看數字前必讀：這一節在比什麼、不在比什麼

| | §2.1 | §2.2 |
|---|---|---|
| **比的東西** | 「大概多大聲」的**量級** | 「泛音落在哪」的**頻率比值** |
| **能得到的結論** | 引擎的絕對量沒有落到荒謬的地方 | 引擎的板模型和真泰國鑼的泛音結構**不一樣** |
| **不能得到的結論** | 引擎的絕對量是對的 | 引擎壞掉了／該改參數 |
| **為什麼** | 單位不同（Pa vs Pa/N）、激發方式不同、樂器不同 | 樂器形狀不同（平板 vs 乳突鑼），本來就不該一樣 |

### 2.1 Weinzierl TABLE I（相關列）vs 本專案 B6 方案 B 的量級

**TABLE I 逐格抄錄**（本機 PDF 第 7–8 頁＝期刊 p.1352–1353，以 PyMuPDF 逐字座標重建列對齊，避免 `pdftotext` 的欄位錯位；原始重建輸出見證據檔）：

| Instrument | LW_ff_max (dB) | LW_pp_min (dB) | LW_ff_av | LW_pp_av |
|---|---|---|---|---|
| Timpani — Hand crank | **108** | **60** | （空白） | （空白） |
| Timpani — Pedal | **108** | **58** | （空白） | （空白） |
| Harp | **91** | **54** | （空白） | （空白） |
| Guitar | **88** | **59** | （空白） | （空白） |

> **`LW_ff_av` / `LW_pp_av` 這兩欄對這四種樂器是空的**，論文表頭自己解釋了原因：
> 「These values could only be calculated for the modern and classical instruments that appear in these symphonies」
> （PDF p.7 表頭，指貝多芬交響曲的音高分布加權）。**不要去補這兩格。**
>
> **這張表沒有鋼琴、沒有鑼、沒有揚琴。** 全文搜尋 `piano` 只命中一筆參考文獻標題
> （“Structural contributions to phantom partial generation in the piano”），不是量測列。
> 卡上寫的「Weinzierl TABLE I 鋼琴聲功率級」**不存在**；本節改用 **Timpani（表中唯一的敲擊樂器）** 當量級參照。

**換算成「在那個量測面上會量到幾分貝」**（用論文自己的式 (4)）：

論文式 (4) 原文：`LW = Lp + 10 log10 (S1/S0) [dB]`，「with S1 = 54.63 m2 and S0 = 1 m2」（PDF p.5＝期刊 p.1350）。
所以 `Lp = LW − 10·log10(54.63) = LW − 17.374 dB`。（`54.63 m² = 4πr²` 反推等效球半徑 **2.085 m**，與論文寫的 `r ≈ 2.1 m` 一致。）

| 樂器 | LW_ff_max | **Lp_ff（量測面平均，dB re 20 µPa）** | p_ff (Pa) | LW_pp_min | **Lp_pp (dB)** | p_pp (Pa) |
|---|---|---|---|---|---|---|
| Timpani, hand crank | 108 | **90.63** | 0.6797 | 60 | 42.63 | 0.00271 |
| Timpani, pedal | 108 | **90.63** | 0.6797 | 58 | 40.63 | 0.00215 |
| Harp | 91 | 73.63 | 0.0960 | 54 | 36.63 | 0.00136 |
| Guitar | 88 | 70.63 | 0.0680 | 59 | 41.63 | 0.00241 |

（腳本 `output/wf0909/P6/weinzierl_lw_to_lp.py`，本機實跑，輸出見證據檔。）

**擺在一起看（唯一能講的一句話）**：

| | Weinzierl 2018（真樂器、有校準、CC BY） | TsukiSynth B6 方案 B（`--dump-modes`） |
|---|---|---|
| 數字帶 | Timpani ff **90.6 dB**；Harp ff 73.6；Guitar ff 70.6（量測面平均）<br>pp 端 36.6 – 42.6 dB | **80.14 – 102.23 dB re 20 µPa**（A8 §3.3 的六個代表音） |
| 單位 | **Pa**（真的量到的壓力） | **Pa/N**（每 1 個「慣例牛頓」的壓力比值） |
| 激發 | 定音鼓＝敲擊（膜）；豎琴／吉他＝撥弦 | 敲擊（鋼琴槌／揚琴槌） |
| 幾何 | 32 麥克風球面平均，半徑 ≈ 2.085 m | `radius_m = 1.05`（本專案自訂慣例） |

> **唯一能講的一句話**：TsukiSynth 的 80–102 dB 這個帶子，**跨在**真敲擊樂器 ff 的 90.6 dB 上，
> 也就是說**校準常數沒有把數字送到「0.001 Pa」或「10⁵ Pa」那種荒謬的地方**。
> **除此之外它什麼都沒證明。** 單位不同、激發不同、樂器不同、幾何不同——**四樣都不同，不能比大小。**

**一個順帶的自洽檢查（注意：不是獨立驗證）**：
A8 §3.1 從 TU Berlin **資料檔**算出的吉他 ff 正前方麥克風（Mic#04）SPL 是 58.69–77.03 dB（最大 77.03）；
本文從 **Weinzierl 論文** 換算出的吉他 ff 量測面平均是 70.63 dB。單一正前方麥克風比 32 麥平均高 6.4 dB，
方向上與「樂器有指向性、正前方比較大聲」一致——**但這兩個數字來自同一批量測**（論文與資料集是同一個計畫），
所以**這是自洽檢查，不是獨立驗證**，不得當成兩個來源互相佐證。

### 2.2 Iowa 泰國鑼 FFT vs `water_gong --dump-modes`（同音高）

**引擎側命令**（唯讀，用 `build\` 現成 binary，未重建）：

```
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --dump-modes scores\examples\water_gong_free.score.json
```

輸出 `output/wf0909/P6/water_gong_free_modes.json`（gitignore）。
該 score 的兩個事件為 `water_gong`／`plate_free_edge=true`／`material=bronze`／`thickness_mm=4.0`／`radius_mm=150`／`strike_position=0.3`，音高 C4 與 G4。
`dump-modes` 自報 `unsupported_observables = [complex_phase, absolute_spl, radiation_directivity]`——**引擎自己就說不支援絕對 SPL**，
所以本節只比**頻率比值**，這也正好是 Iowa（未校準）唯一能比的東西。

**Iowa 側方法**（腳本 `output/wf0909/P6/analyze_iowa_gong.py`，本機實跑）：
雙聲道相加成單聲道 → 取 **0.15–2.15 s**（避開起音敲擊瞬態）→ Hann 窗 → 補零 ×8 的 rFFT（頻率解析 **0.0421 Hz/bin**）
→ 取 6 kHz 以下、比最大峰低 40 dB 以內的局部極大（3 Hz 保護帶）→ 拋物線內插取峰值頻率 → 依振幅取前 8 個、再依頻率排序。

#### C4

| # | **Iowa 真泰國鑼 C4 ff** | 比值 | 相對振幅 | | **`water_gong` C4** | 比值 |
|---|---|---|---|---|---|---|
| 1 | **266.366 Hz** | **1.0000** | 0.00 dB | | **261.626 Hz** | **1.0000** |
| 2 | 427.443 Hz | 1.6047 | −21.60 dB | | 454.817 Hz | 1.7384 |
| 3 | **532.756 Hz** | **2.0001** | **−6.49 dB** | | 609.232 Hz | 2.3286 |
| 4 | 538.924 Hz | 2.0232 | −11.43 dB | | 1026.953 Hz | 3.9253 |
| 5 | 547.264 Hz | 2.0546 | −12.36 dB | | 1071.727 Hz | 4.0964 |
| 6 | 1381.324 Hz | 5.1858 | −21.08 dB | | 1762.971 Hz | 6.7385 |
| 7 | 1597.532 Hz | 5.9975 | −13.30 dB | | 1927.647 Hz | 7.3679 |
| 8 | 1726.539 Hz | 6.4818 | −11.48 dB | | — | — |

#### G4

| # | **Iowa 真泰國鑼 G4 ff** | 比值 | 相對振幅 | | **`water_gong` G4** | 比值 |
|---|---|---|---|---|---|---|
| 1 | **395.056 Hz** | **1.0000** | 0.00 dB | | **391.995 Hz** | **1.0000** |
| 2 | 588.361 Hz | 1.4893 | −29.30 dB | | 681.455 Hz | 1.7384 |
| 3 | **790.069 Hz** | **1.9999** | **−14.67 dB** | | 912.816 Hz | 2.3286 |
| 4 | 804.013 Hz | 2.0352 | −33.40 dB | | 1538.692 Hz | 3.9253 |
| 5 | 983.339 Hz | 2.4891 | −30.72 dB | | 1605.776 Hz | 4.0964 |
| 6 | 2329.722 Hz | 5.8972 | −33.65 dB | | 2641.472 Hz | 6.7385 |
| 7 | 2423.276 Hz | 6.1340 | −22.89 dB | | 2888.207 Hz | 7.3680 |
| 8 | 2480.151 Hz | 6.2780 | −32.61 dB | | — | — |

> 兩張表的 Iowa 側都列滿方法所寫的 **8 個峰**；`water_gong` 側 C4／G4 都只有 **7 列**，
> 是因為 `--dump-modes` 對這兩顆音**總共就只自報 7 個部分音**（`partials=7`，見證據檔 G6），不是本文件截斷。
> （2026-09-09 稽核回合補列：G4 表初版漏列第 8 列 2480.151 Hz，與同節方法敘述「依振幅取前 8 個」不一致，已補上。
> 該峰比基頻弱 32.61 dB，不參與本節任何結論。）

**三個可以直接讀出來的事實（只陳述量到的東西）**：

1. **真泰國鑼有一個幾乎完美的八度泛音，而且它就是最強的那個泛音。**
   C4 是 **2.0001 倍**（−6.49 dB，是所有泛音裡最強的）、G4 是 **1.9999 倍**（−14.67 dB，同樣最強）——
   兩顆音各自獨立量出來，都落在 2.000 的萬分之一以內。
   引擎 `water_gong` **在 2.000 倍上沒有任何一根**：把 2.000 夾在中間的是第 2 個部分音 **1.7384 倍**
   （比值差 0.2616 ＝ **低 243 音分**）與第 3 個部分音 **2.3286 倍**（比值差 0.3286 ＝ **高 263 音分**）。
   **兩根都差了兩個半音以上**（1 個半音＝100 音分：243 音分＝**2.43 個半音**、263 音分＝**2.63 個半音**），
   **不是誤差等級的差。**
   （2026-09-09 複核更正一：本文件初版此處寫「最接近的是 2.3286」，**算錯了**——
   1.7384 離 2.000 比 2.3286 更近。結論不受影響，但數字已改對。
   **複核更正二（2026-09-09 稽核回合）**：第一次更正時把音分換成音程也**寫錯了**——
   原寫「兩根都差了兩個全音以上」，但 2 個全音＝400 音分，而 243／263 音分只有 1.21／1.32 個全音，
   **不到**兩個全音；正確說法是「兩個**半音**以上」。音分數字 243／263 本身無誤，錯的只是音程換算的措辭。）
2. **引擎最強的泛音（第 2 個部分音，1.7384 倍）在真鑼上找不到對應。** 真鑼 C4 在 1.6047 有一個峰但**弱 21.6 dB**，
   G4 在 1.4893 有一個峰但**弱 29.3 dB**——**位置不合、強度也不合。**
3. **真鑼在 2 倍附近是一叢峰不是一根**（C4：532.756／538.924／547.264 Hz，彼此差 1.2%、1.6%）。
   引擎的模態表在該區域**只給一根**。這是「簡併模態被實體不對稱撕開」的典型長相——
   **但本卡沒有量測該鑼的幾何，不能斷定成因**，只登記「量到一叢，不是一根」。

**這代表什麼（也代表不了什麼）**：

- 引擎 `water_gong` 走的是 `PlateModel` 的**自由邊平板**特徵值。上表 `--dump-modes` 實際輸出的比值是
  **1 : 1.7384 : 2.3286 : 3.9253**；本專案自己的 score 說明寫的是四捨五入版
  「`ratios 1 : 1.73 : 2.33 : 3.91`」（`scores/examples/water_gong_free.score.json` 的 `meta.description` 逐字，
  2026-09-09 親自開檔核對）——**前三項一致，第四項 3.91 與引擎實算的 3.9253 差 0.015**，
  屬 score 說明字串的四捨五入誤差，**不影響 §2.2 的任何結論**（本節只用第 2、3 個部分音）。
  該說明字串同時自報其來源為「`Approximate eigenvalues (Leissa nu~0.33)`」。
  **泰國鑼是中間凸一顆乳突（boss／nipple）的鑼，不是平板。** 幾何假設不同，泛音比值當然不同。
- 所以這**不是紅燈、不是 GATE、也不是「引擎算錯了」**。它是一個**主張域（domain）問題**：
  **`water_gong` 現在的模型不宣稱自己是泰國鑼的模型**，而我們手上第一次有的真鑼資料**剛好就是泰國鑼**。
- **本卡不改任何程式、不改任何參數、不建議調任何數字。** 要不要處理、怎麼處理，是月月的後續決策（§3 列了選項）。

**音高偏移（附帶登記）**：Iowa 的鑼不是 A440 標準音高——C4 量到 266.366 Hz，比 A440 的 C4（261.626 Hz）高 **31.1 cent**；
G4 量到 395.056 Hz，比 391.995 Hz 高 **13.5 cent**。做任何未來比對時要記得這件事。

---

## §3 已知缺口（誠實列，含查不到的）

1. **Weinzierl TABLE I 沒有鋼琴、沒有鑼、沒有揚琴、沒有舌鼓。**
   它是管弦樂團編制。能拿來當量級參照的只有 Timpani，而 Timpani 是**膜**——
   本專案的 score schema 明確拒收 `membrane`（見 `docs/EXTERNAL_ANCHOR_SOURCES.md` §1.1）。
   **這是「用最近似的東西當量級參照」，不是同類比較。**
2. **`LW`（聲功率）不是 `Lp`（聲壓）。** §2.1 的換算用的是論文自己的式 (4)，
   得到的是**「在那個 54.63 m² 球面上的能量平均」**，不是「站在幾公尺外會聽到幾分貝」。
   要得到後者需要知道指向性與距離，本卡沒有做。
3. **Iowa 沒有校準，所以絕對音量永遠拿不到。** 它只能回答「泛音在哪、衰減多久」，
   不能回答「多大聲」。**兩個來源加起來仍然湊不出「有校準的、我們要的樂器」**——
   `EXTERNAL_DATASET_ALTERNATIVES.zh-TW.md` §0 的結論（這種東西數量是 0）**沒有被本卡推翻。**
4. **Iowa 那三包 zip 與網頁器材表對不對得上，無法從網頁確定。**
   器材表（2013-03-20、5 feet、QTC40）**一字不差地同時掛在 Pre-2012 與 Post-2012 兩個頁面**；
   本卡下載的是 Pre-2012 頁的三包，伺服器 `Last-Modified` 是 2016-06-07。
   **另有一處網站自相矛盾（2026-09-09 複核時新增登記）**：總說明頁 `MIS.html` 寫
   「Beginning in 2011, recordings have been made at 24/96」（逐字），但鑼的器材表寫 `24-bit, 44.1 kHz`，
   而本卡實際讀出的檔案是 **44,100 Hz**——檔案與器材表一致、與總說明頁那句不一致。
   **這使「三包到底屬於哪一場錄音」更不確定，不是更確定。**
   **要確認只能寫信問** `Lawrence Fritts`（MIS 建置者，網頁署名）。本卡未發信（AI 不代發信）。
5. **「真鑼為什麼幾乎諧音、平板為什麼不諧音」——本卡未取得可引用的原文。**
   2026-09-09 搜尋到疑似相關的 JASA 短文（“Acoustical and vibrometry analysis of a large Balinese gamelan gong”，
   pubs.aip.org），但該頁 **HTTP 403，未取得原文**，也未取得可引用的 DOI 授權欄位。
   → 本文件 §2.2 因此**只陳述量到的頻率**，**不宣稱**任何「乳突鑼的物理機制」。
   （`EXTERNAL_DATASET_ALTERNATIVES.zh-TW.md` §1.7 記錄的 BYU 鑼指向性資料集，授權欄空白、下載回 403，本卡同樣未取得。）
6. **本卡只做了 C4 與 G4 各一顆音、只用 ff。** 三包裡還有 13 音 × 3 力度 = 39 個檔沒分析。
   衰減時間（T60）、力度對泛音的影響**都還沒量**。要不要做是後續決策。
7. **§2.2 的 FFT 參數是本卡自己訂的**（0.15–2.15 s 窗、−40 dB 門檻、3 Hz 保護帶）。
   換一組參數，弱峰的取捨可能不同；**強峰（2.000 倍那一根）不受影響**。
   **2026-09-09 複核時做了參數敏感度測試**（換窗函數 Hann→Blackman–Harris、門檻 −40→−45 dB、
   另加 40 Hz 高通擋室內低頻，並改用 0.20–1.20 s／0.50–4.50 s／1.0–6.0 s 三個不同分析窗）：
   該根泛音的比值落在 **1.9999–2.0002**（C4 四組、G4 三組），且在每一組乾淨的設定裡**都是最強的泛音**。
   **一個必須登記的例外**：G4 用 1.0–6.0 s 窗時，鑼已衰減到低於室內低頻噪聲，
   演算法會把 **42.6 Hz 的低頻噪聲**誤選為基頻——**這是分析腳本的已知失效模式，不是資料的性質**；
   加上高通後其餘各組皆穩定。逐組數字見 `reports/gate_outputs/wf0909_P6_supplement.txt` §G10。

### 月月可以選的後續（本卡不做，只列）

| 選項 | 做法 | 代價 |
|---|---|---|
| **不做** | 把 §2.2 當成「已登記的已知落差」，`water_gong` 維持現狀（它本來就沒宣稱自己是泰國鑼） | 0。**建議先選這個。** |
| **改文件** | 在 `water_gong` 的說明裡寫明「模型是自由邊平板，不是乳突鑼」 | 一張小卡，不動程式 |
| **改模型** | 讓 `PlateModel` 支援乳突鑼幾何 | 大工程，且**需要先有可引用的物理來源**（§3 第 5 點目前是空的），還會觸發 R10 |

---

## §附錄 A：Iowa 三包逐檔 SHA256（本機 `zipfile` 讀出，未解壓到磁碟）

### `thaigong.ff.zip`

| 檔名 | bytes | SHA256 |
|---|---|---|
| `thaigong.A4.ff.aif` | 1,572,826 | `bbe527a60673d9579f75aae8998d722b46882fdce6836087b8c3e6fd57fde94b` |
| `thaigong.Ab4.ff.aif` | 3,034,114 | `f30cfcebb73140c45dc2d4ba71b7f3fa63763efb784484aaf66c520dac48af78` |
| `thaigong.B4.ff.aif` | 2,301,256 | `5a51d3b51289149aacebee31afe2f04041eca1c5ee02c1058742c7d09c618aa8` |
| `thaigong.Bb4.ff.aif` | 1,786,708 | `7d3eb5347bb25072b1800ba34607a4733d9d5c8a4532206ca08d0b8e1a4a37c3` |
| `thaigong.C4.ff.aif` | 3,536,200 | `999030e294b5f6c0ee5e39bf54fd66883936b8b231022496f617c9326d517bdb` |
| `thaigong.C5.ff.aif` | 2,302,318 | `d780a39ff9bb05a6a3b15ee29302c59f3a3962b9aa138736e6d0cc25111069c0` |
| `thaigong.D4.ff.aif` | 4,656,130 | `90020697855869bd863c45b069ed0613451729e0fda5bb3053d9ba216aa3ae8a` |
| `thaigong.Db4.ff.aif` | 3,595,618 | `808147893be73b1e05e711d51f10db0d3d5b3085d325c1352008e3bf3259da42` |
| `thaigong.E4.ff.aif` | 3,492,358 | `046e00b3b0ef537196d6c840a04e7786f9ed39ecbf93ce87bccb148048aa2f9c` |
| `thaigong.Eb4.ff.aif` | 4,673,284 | `ddb74fca92fb212020802598fe206a7eebb163cbb24ce8f37157c1faeb711f16` |
| `thaigong.F4.ff.aif` | 2,874,586 | `d904acb9bd4346ac29d88d58c4cf6c4a48447f9ad00f32721d3daaf151f20b75` |
| `thaigong.G4.ff.aif` | 2,849,170 | `205e59c6dddf48f684854e71bc45a0b4e02fad02d03934b670a099f03783b3fb` |
| `thaigong.Gb4.ff.aif` | 3,668,458 | `291984016694632dcbba63e3661972d90c2cc1f581b8fa015c89b76b276144f9` |

### `thaigong.mf.zip`

| 檔名 | bytes | SHA256 |
|---|---|---|
| `thaigong.A4.mf.aif` | 1,355,896 | `cc780aaa7e11fbed353efdd4c026b7012ea47e7c69175a699d235130a65e50be` |
| `thaigong.Ab4.mf.aif` | 1,661,116 | `ffab2fdd0b5d5634c0f779e6e2176388cf70bbb19b62bd28cce0588a9224cd4b` |
| `thaigong.B4.mf.aif` | 1,788,256 | `44c0a4ac64abe6ded2f92f3838e395a0452606633a963fe9f1227ac04d88014e` |
| `thaigong.Bb4.mf.aif` | 1,259,188 | `5aa9e640f303f820c9d4515b6d1cbb79e4e410ae2e0cb209bc1b8be4e8ddc7dc` |
| `thaigong.C4.mf.aif` | 3,319,426 | `a7a6d95e8e8e0af436e8db69b68df050c19717cebce5d99386b9f35996c2fb61` |
| `thaigong.C5.mf.aif` | 1,478,914 | `46bd3c3f14e0fd24d631183f17c0ca24b82910444a23d4ab25112434b4ac5f46` |
| `thaigong.D4.mf.aif` | 3,587,728 | `d747b433905c2995c095c26338997fe0216ba630dbd7e2e65ff6ef90fc0297d6` |
| `thaigong.Db4.mf.aif` | 3,607,648 | `6cfc2361a235b36076a82f989fed55d8ea335ffa85932b9182b416256cd30b29` |
| `thaigong.E4.mf.aif` | 3,125,854 | `6b6607377683e92f241b745353e2bca5d22c53817f782819cf2d1cccfc28d859` |
| `thaigong.Eb4.mf.aif` | 4,172,908 | `107f18235fa5a84b854fa2acecb8a4b684b8ea9ec1e91458e7a8c4de5fc1cd89` |
| `thaigong.F4.mf.aif` | 2,648,044 | `65085c1053b1634dc2f5b2ef399f0a70d8dc9c9fd36bd94865a1f3086e1b079d` |
| `thaigong.G4.mf.aif` | 1,966,366 | `0c6fa496137eaf27dac83d27d7350611f2d1ef48e0041f2e42d890039b166d69` |
| `thaigong.Gb4.mf.aif` | 2,769,328 | `71715ad6bceea675aa60c6dc29f5bc92979801790476ada4f8b76b6093a6991b` |

### `thaigong.pp.zip`

| 檔名 | bytes | SHA256 |
|---|---|---|
| `thaigong.A4.pp.aif` | 1,274,014 | `a9f6b0d0b8df315fee71fe6e5fd4e42012adad6e9399ba08648e69966a1e7543` |
| `thaigong.Ab4.pp.aif` | 1,665,802 | `8f43d43f64760b9cb488d864171c3b5bfe627e56fea9027ce84f726315626bac` |
| `thaigong.B4.pp.aif` | 1,419,718 | `f7bf4b0b7e39726c86b153618f32bce43c10e31c775e0ab811151ea57126175d` |
| `thaigong.Bb4.pp.aif` | 1,287,790 | `6c1e290828a13857b2571ffdaa93fd9b22b9eeed225a92828dc23631e51c55a2` |
| `thaigong.C4.pp.aif` | 2,861,692 | `410779e0db4655acccafa30a306405aa686d66824c22c90aca4362f01fa6b4d0` |
| `thaigong.C5.pp.aif` | 919,888 | `db3fb6db16ae89efcec7d2ce070d325e524e2d0c53ec4421c601a25239e0da20` |
| `thaigong.D4.pp.aif` | 2,695,228 | `85fced57db161aaf26368ffd0ac1d1fa7c6d6e348f702a1e4ac6a5d27534d92f` |
| `thaigong.Db4.pp.aif` | 2,153,548 | `5be98abedbda6d836611e34c1cbe0625b78b26a8906b78c1ca95fbef5a15ade8` |
| `thaigong.E4.pp.aif` | 2,383,576 | `3529d1591555044c9aa3c13cc7cbeca6ff911817a0d4490c1cba8fc695de8cee` |
| `thaigong.Eb4.pp.aif` | 3,576,802 | `6c76574cbb2357366420f8dc448efc1888d778230e624cc7cb817ec90ad71a69` |
| `thaigong.F4.pp.aif` | 2,056,048 | `4b58b68a19a9c259ab490321237b48120dd2a50d42cf217a38f6342cf4231958` |
| `thaigong.G4.pp.aif` | 1,584,532 | `258285d1a22a10f72e762c0dcda6805894d3e78f39ed803bd279a9beb32f60e8` |
| `thaigong.Gb4.pp.aif` | 2,051,548 | `bae2ed5f6aa4efaf26976deceaf4632f1562a6b3499a3a6f5f61edc3fe003cd5` |

---

## §附錄 B：來源清單（全部存取日期 2026-09-09）

| # | 等級 | 來源 | URL | 取得狀態 |
|---|---|---|---|---|
| S1 | **A**（PDF 本體） | Weinzierl et al. 2018, JASA 144(3), 1347–1355, DOI `10.1121/1.5053113` | `https://api-depositonce.tu-berlin.de/server/api/core/bitstreams/d7d0f7af-e49b-4b86-8e7d-4293aef0440a/content` | ✅ 全文 PDF 已下載並逐頁檢查 |
| S2 | **B**（出版商登錄） | Crossref metadata for `10.1121/1.5053113` | `https://api.crossref.org/works/10.1121/1.5053113` | ✅ 本機 curl 實打，`license` 欄逐字讀出 |
| S3 | **B**（官網聲明） | University of Iowa MIS 總說明頁 | `https://theremin.music.uiowa.edu/MIS.html` | ✅ 原始 HTML 已抓，授權句逐字比對 |
| S4 | **B**（官網表格） | Iowa MIS — Gongs/Tamtams（Pre-2012，三包 zip 所在頁） | `https://theremin.music.uiowa.edu/MISgongtamtams.html` | ✅ 原始 HTML 已抓，器材表逐欄抄錄 |
| S5 | **B**（官網表格） | Iowa MIS — Gongs/Tamtams（Post-2012，用於比對器材表是否一致） | `https://theremin.music.uiowa.edu/MIS-Pitches-2012/MISGongsTamTams2012.html` | ✅ 原始 HTML 已抓 |
| S6 | — | JASA “Acoustical and vibrometry analysis of a large Balinese gamelan gong” | `https://pubs.aip.org/asa/jasa/article/128/1/EL8/655833/...` | ❌ **HTTP 403，未取得原文**，未用於任何主張 |

**內部參照（不是外部證據，依研究卡規約不得當外部佐證）**：
`docs/EXTERNAL_DATASET_A8.zh-TW.md` §3.1／§3.2／§3.3、
`docs/EXTERNAL_DATASET_ALTERNATIVES.zh-TW.md` §0／§1.1／§1.2／§1.7、
`scores/examples/water_gong_free.score.json`。

---

## §附錄 C：本卡產生的本機檔案（皆在 gitignore 的 `output/` 或 `external_data/` 下，不進版控）

| 路徑 | 內容 |
|---|---|
| `external_data/weinzierl_2018_jasa/weinzierl_2018_jasa_1.5053113.pdf` | 論文全文 |
| `external_data/iowa_mis_thai_gong/thaigong.{ff,mf,pp}.zip` | 泰國鑼三包 |
| `output/wf0909/P6/water_gong_free_modes.json` | `--dump-modes` 原始輸出 |
| `output/wf0909/P6/iowa_extract/thaigong.{C4,G4}.ff.aif` | 本卡分析用的兩個解壓檔 |
| `output/wf0909/P6/analyze_iowa_gong.py` | Iowa FFT 分析腳本 |
| `output/wf0909/P6/iowa_gong_partials.json` | FFT 結果 |
| `output/wf0909/P6/weinzierl_lw_to_lp.py` | LW→Lp 換算腳本 |

證據檔（**進版控**）：`reports/gate_outputs/wf0909_P6_supplement.txt`
