# A8：TU Berlin 樂器指向性資料庫 — 下載登記、授權查證與首批對照數字

> 建立：2026-09-07（作業日跨到 2026-09-08）　卡：`docs/workcards/WF0907_R5_A8_dataset.md`
> 存取日期（本文所有外部來源）：**2026-09-07 / 2026-09-08**
> 本文件不改任何程式碼、不改任何容差、不宣稱任何「模型與實測吻合」。
> 資料檔存放於 `external_data/tu_berlin_directivity/`，**已加入 `.gitignore`，不進版控**。

---

## §0 一句話結論（給月月）

資料集下載完成了，但**查出兩件跟我們原本以為的不一樣的事**，兩件都會影響後續：

1. **授權不是 CC BY-SA 4.0，是 CC BY-NC-SA 4.0——「NC」= 禁止商業用途。**
   我們自己的 `docs/EXTERNAL_ANCHOR_SOURCES.md` 寫的「CC BY-SA 4.0」是照 arXiv 預印本抄的，
   而**資料檔本身**（說明 PDF ＋ 每一個 SOFA 檔的 metadata 欄位）寫的是 `cc by-nc-sa 4.0`。
   TsukiSynth 想保留商業選項 → **這份資料不能當成產品的一部分，只能當私下的對照參考**（§4 有四個選項）。
2. **他們的麥克風其實架在離樂器 2.06 公尺處，不是我們文件與程式碼裡寫的 1.05 公尺。**
   我們程式裡有一個叫「假設聽的距離」的數字（`src/physics/RadiationModel.h:291`，值 1.05），
   註解說它是「照抄這個資料庫」——但我打開資料檔裡記錄麥克風擺哪裡的那一欄
   （SOFA 檔＝這個資料庫的檔案格式，`ReceiverPosition`＝「收音點位置」欄位），
   32 顆麥克風的距離欄一律寫 **2.06 公尺**。
   聲音每離遠一倍會小 6 分貝，1.05 → 2.06 剛好差 **5.86 分貝**。
   這是**引用寫錯**，不是程式算錯（1.05 本來就是我們自己訂的慣例，不是量出來的），
   但**「說它來自那個資料庫」這句話必須更正**，否則以後拿這個資料庫來對照，整整會差 5.86 分貝。

首批對照數字有了（§3）：真實古典吉他用力撥的單音，正前方麥克風，44 個音落在
**58.7 – 77.0 分貝（dB SPL，即一般講「多大聲」的那個分貝；量測點在 2.06 公尺處）**。
TsukiSynth 現在算出來的對應數字是 **0.20 – 2.59 Pa/N**
（`Pa/N`＝「每施 1 單位力，產生多少聲壓」；換算成分貝是 80 – 102 分貝）。
**這兩欄不能直接比大小**：一邊是真的量到的聲壓，一邊是「每 1 個我們自己定義的牛頓」的比值，
而且真樂器是**撥弦**、我們模擬的是**敲擊**。
它只證明「兩邊在同一個數量級的世界裡」，**不證明模型正確**。
（本節出現的詞如果看不懂，§4.0 有白話對照表。）

---

## §1 問題

`TODO.md` A8 問的是兩件事：

1. 這份「校準到絕對聲壓」的外部量測資料庫，要不要下載到本機？
2. 它的授權（原本以為是 CC BY-SA 4.0）跟 TsukiSynth「保留商業選項」相不相容？

月月 2026-09-07 裁決：**下載**，只當外部參照，repo 內只留 DOI + SHA256 + 比對數字，資料檔不進版控。
本卡執行這個裁決，並在執行過程中**親自打開資料檔查證**授權與量測幾何——結果推翻了問題 2 的前提（見 §0、§2）。

---

## §2 外部證據表（分級）

分級定義（依 `WF0907_R_research_common.md`）：
**A＝資料檔本身的 metadata / 隨檔說明**（最高，因為它就是我們要用的東西）｜
**B＝經同儕審查的論文／機構典藏庫記錄**｜**C＝預印本**｜**D＝社群觀感**（本卡未使用）。

### 2.1 授權：**五個來源（E1–E5），四種說法**

| # | 等級 | 來源 | 存取日期 | ≤15 字原文引述 | 說什麼 |
|---|---|---|---|---|---|
| E1 | **A** | 資料集隨附說明 `0_Documentation.pdf`（Version 3, February 2, 2024）第 2 頁 | 2026-09-07（本機檔案，SHA256 見附錄 A） | 「The database is provided under a Creative Commons BY-NC-SA licence」 | **CC BY-NC-SA** |
| E2 | **A** | 每一個 SOFA 檔的 global attribute `License`（例：`Acoustic_guitar_modern_e2_singleTones.sofa`） | 2026-09-07（本機檔案） | 「cc by-nc-sa 4.0」 | **CC BY-NC-SA 4.0** |
| E3 | **B** | JAES 論文摘要（Ackermann, Brinkmann, Weinzierl, *J. Audio Eng. Soc.* 72(3):170–179, 2024-03）<br>https://aes2.org/publications/elibrary-page/?id=22388 | 2026-09-07 | 「The data is available under the CC BY-NC 4.0 license.」 | **CC BY-NC**（無 SA） |
| E4 | **B** | DepositOnce 典藏記錄 `dc.rights.uri`（item uuid `b194da8b-…`，API 直接讀出） | 2026-09-07 | 「http://rightsstatements.org/vocab/InC/1.0/」 | **In Copyright**（完全沒有給 CC 授權） |
| E5 | **C** | arXiv 預印本 2307.02110（2023-07-05）PDF 摘要與 §2 | 2026-09-07 | 「The data is available under the CC BY-SA 4.0 licence.」 | **CC BY-SA 4.0**（← 我們原本抄的那句） |

**判讀**：E5（預印本，2023）是五者中唯一給出「不含 NC 的 CC 授權」的一份，也是**最舊**的一份；
E1/E2 是**跟著資料檔一起發佈的**（2024-02，Version 3），對「這批檔案能怎麼用」最有拘束力。
E3 是同一群作者在期刊上的正式說法，同樣含 NC。E4 顯示典藏庫的欄位根本沒填 CC
（同一個典藏庫的其他資料集會正確填 `creativecommons.org/licenses/by/4.0/`、`by-nc-sa/4.0/`、`by-nc-nd/3.0/de/` 等。
**可原樣重跑的實測**（2026-09-08）：
`GET https://api-depositonce.tu-berlin.de/server/api/discover/search/objects?query=Musical%20Instruments%20directivities&dsoType=item`
回 `totalElements = 437`，第一頁預設 20 筆的 `dc.rights.uri` 分布為
**CC 授權網址 14 筆**（`by/4.0/`×10、`by/3.0/de/`×1、`by-nc-sa/4.0/`×1、`by-nc-nd/2.0/`×1、`by-nc-nd/3.0/de/`×1）、
**In Copyright 6 筆**，0 筆空白。所以這不是系統性缺欄，而是這一筆沒給 CC。
**更正**：本文件 2026-09-07 初版曾寫「10 筆裡有 7 筆填 CC、3 筆填 In Copyright」，
該次查詢的完整 URL 沒有記下來、**無法重現**，該敘述已作廢，以上列實測為準。
此旁證**不影響 NC 結論**——NC 結論只靠 E1/E2/E3。）

> **五份來源（E1–E5）裡有三份（E1／E2／E3）明寫 NC，其中兩份（E1／E2）就寫在我們手上的檔案裡 → 必須當 NC 處理。**
> （另外兩份：E4 完全沒給 CC 授權、E5 是最舊的預印本說 BY-SA；**沒有任何一份說「可以商用」**。）

CC BY-NC-SA 4.0 的三個條款原文（https://creativecommons.org/licenses/by-nc-sa/4.0/ ，存取 2026-09-07）：

- BY：「You must give appropriate credit, provide a link to the license, and indicate if changes were made.」
- NC：「You may not use the material for commercial purposes.」
- SA：「If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.」

### 2.2 校準慣例（這一條原本的敘述是對的）

| # | 等級 | 來源 | 存取日期 | ≤15 字原文引述 |
|---|---|---|---|---|
| E6 | **A** | `0_Documentation.pdf` §2 Recordings（第 5 頁） | 2026-09-07 | 「a value of 1 corresponds to a pressure of 1 Pascal」 |
| E7 | **C** | arXiv 2307.02110 §1.2 | 2026-09-07 | 「a digital amplitude of 1 corresponds to a pressure of 1 Pascal」 |
| E8 | **C** | arXiv 2307.02110 §1.2（同句後半） | 2026-09-07 | 「resp. a sound pressure level of Lp = 94 dB」 |

**注意**：`Lp = 94 dB` 這半句**只在論文裡**，隨檔說明 PDF 只寫到「1 ≡ 1 Pa」。
而且**這句話裡沒有任何距離**——94 dB 是「1 Pa 換算成 dB SPL」的數學等式（20·log₁₀(1 / 2×10⁻⁵) = 93.98），
不是「在 1.05 m 處」。我們自己的文件把「1.0 ≡ 1 Pa ≡ 94 dB」和一個半徑焊在一起，是**兩件事被合併了**。

### 2.3 量測幾何：資料檔說 2.06 m，論文說「直徑 2.1 m」

| # | 等級 | 來源 | 存取日期 | ≤15 字原文引述 / 讀到的值 |
|---|---|---|---|---|
| E9 | **A** | SOFA 變數 `ReceiverPosition`，屬性 `Type='spherical'`、`Units='degree, degree, metre'`；32 列的第 3 欄 | 2026-09-07 | 全部 32 顆 = `2.06`（公尺） |
| E10 | **A** | `0_Documentation.pdf` §3 Audio Features 式 (4)：包絡面面積 | 2026-09-07 | 「with spherical surface areas S1 = 54.63 m2」 |
| E11 | **C** | arXiv 2307.02110 §1.2 | 2026-09-07 | 「pentakis dodecahedron with a di- ameter of 2.1 m」 |

由 E10 反推半徑：`r = √(54.63 / 4π) = 2.085 m`。
→ **E9（2.06 m）與 E10（2.085 m）互相支持；E11 的「diameter」若讀成「radius」也吻合（2.1 m）。**
唯一不吻合的是「把 2.1 當直徑再除以 2 得到 1.05 m」這個推算，
也就是 `docs/EXTERNAL_ANCHOR_SOURCES.md:42` 目前寫的那一格。

**結論**：量測面半徑應記為 **2.06 m**（以資料檔為準）。

### 2.4 其他從資料檔親自讀到的 metadata（全部 A 級）

| 項目 | 讀到的值 | 讀法 |
|---|---|---|
| SOFA 慣例 | `SOFAConventions = FreeFieldDirectivityTF`，`Version = 2.1`，`DataType = TF` | global attrs |
| 麥克風數 | `R = 32`；座標為球座標（方位角°、仰角°、半徑 m） | `ReceiverPosition` |
| 取樣率 | 44.1 kHz（說明 PDF：「All data were measured with a sampling frequency of fS = 44.1 kHz」） | 說明 PDF 第 3 頁 |
| 「正前方」是哪一顆 | `SourceView.Reference`：「Normal of the soundboard aimed slightly above Mic#04」 | SOFA 屬性 |
| Mic#04 座標 | 方位 0.00°、仰角 −10.81°、半徑 2.06 m | `ReceiverPosition[3]` |
| 調音頻率 | `SourceTuningFrequency = 443.0` Hz（不是 440） | SOFA 變數 |
| 單音檔的數值意義 | 「Contains the sound pressure (RMS) of the fundamental note and harmonics/overtones in Pa.」 | `1a` 檔 `Comment` 屬性 |
| 吉他實體 | 「Instrument: Masaru Kohno (1985) model "Concert"」；高三弦尼龍、低三弦纏繞弦 | `SourceManufacturer` |
| 演奏者 | `Musician = Hanjo Maempel` | global attr |
| 檔內自稱的 DOI | `Reference = dx.doi.org/10.14279/depositonce-5861.3` | global attr |

---

## §3 引擎／repo 現況數字（informational，**不判 PASS/FAIL**）

### 3.1 真實吉他（TU Berlin，量測值）

單音指向性檔（`1a`）本身就是**每個部分音的 RMS 聲壓（Pa）**，
所以「整個音的 RMS」＝各部分音平方和開根號。取 Mic#04（正前方、音板法線方向），半徑 2.06 m：

| 音 | f₀ (Hz) | 部分音數 | Mic#04 RMS (Pa) | **dB SPL @2.06 m** | 換算到 1.05 m（1/r）|
|---|---|---|---|---|---|
| E2（低） | 82.70 | 241 | 0.03215 | **64.12** | 69.98 |
| E4（中） | 332.62 | 60 | 0.04011 | **66.04** | 71.90 |
| B5（高） | 999.24 | 20 | 0.07714 | **71.72** | 77.58 |

44 個音（全部 `dynamic = ff`）在 Mic#04 的範圍：**最小 58.69 dB（G5）、最大 77.03 dB（A3）、平均 68.90 dB、全距 18.34 dB**。
（原始表格 `output/wf0907/R5/guitar_spl.json`；腳本 `output/wf0907/R5/analyze_guitar.py`。）

**獨立交叉檢查**（腳本 `output/wf0907/R5/analyze_recordings.py`，2026-09-08 重跑逐格一致）：
另外把 1.10 GB（1.02 GiB）的原始錄音檔（`2_Acoustic_guitar_modern_recordings.zip`，
內含單邊複數頻譜）依說明 PDF 式 (1) 還原成雙邊頻譜、IFFT 回時域，直接算 Mic#04 全訊號 RMS：

| 音 | 1a 部分音法 (dB) | 錄音 IFFT 全訊號 RMS (dB) | 差 | 同音 pp 的錄音 RMS (dB) | ff − pp |
|---|---|---|---|---|---|
| E2 | 64.12 | 61.67 | +2.45 | 52.03 | **9.6 dB** |
| E4 | 66.04 | 62.21 | +3.83 | 50.77 | **11.4 dB** |
| B5 | 71.72 | 70.45 | +1.27 | 56.88 | **13.6 dB** |

兩種算法方向一致、差 1–4 dB，符合預期（`1a` 是穩態段抽取，錄音全訊號含衰減尾與靜音，RMS 會被拉低）。
**「穩態段抽取」這句以前沒有標出處，第五輪補上 A 級直接證據**：`1a` 每個 SOFA 檔的 global attribute
`History` 原文（≤15 字引述）「extracted from the steady state of the original recording」
（本機檔案 `Acoustic_guitar_modern_e2_singleTones.sofa`，存取 2026-09-08；見附錄 H 的 X4）。
**副產品**：ff 與 pp 的差 9.6–13.6 dB，是 `docs/workcards/B7.md` velocity→力度映射可以參考的外部數字（撥弦，非敲擊）。

### 3.2 豎琴（TU Berlin，量測值，同樣 Mic#04 / 2.06 m）

| 音 | f₀ (Hz) | Mic#04 RMS (Pa) | dB SPL @2.06 m |
|---|---|---|---|
| B0（最低） | 31.36 | 0.01373 | 56.73 |
| E4（中） | 330.26 | 0.09206 | 73.26 |
| F7 | 3126.19 | 0.00065 | 30.27 |

78 個音：21.85 – 82.05 dB，平均 67.09 dB。
（附帶發現：`1a` 裡豎琴音域是 **B0–F#7**，比說明 PDF Table 1 標的 C1–F4 寬很多——見 §5。
**2026-09-08 第五輪更正**：本文件先前三處寫「B0–F7」，**最高音其實是 F#7**（MIDI 102）；
上表挑的三個代表音維持不變（F7 是 MIDI 101），只是它**不是**最高的那一個。改法與證據見附錄 H 的 X6。）

### 3.3 TsukiSynth B6 方案 B 的絕對量（本機 CLI 實跑）

命令（唯讀，用現成 binary，未重建）：

```
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --dump-modes scores\examples\physical_piano.score.json
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --dump-modes scores\examples\moonlight_sonata_movement1_yangqin.score.json
```

`dump-modes` 自報：
`model_observables = [modal_frequency_hz, relative_modal_amplitude, modal_t60_s, radiated_power_relative, absolute_pressure_per_force]`、
`unsupported_observables = [complex_phase, absolute_spl, radiation_directivity]`
——**引擎自己就明說「absolute_spl 不支援」**，這一點跟 §3.1 的量測 SPL 是兩種東西，必須記住。

把每個事件 `acoustic_transfer[]` 各 partial 的 `pressure_per_force_real_pa_n` 取平方和開根號：

| score | 音 | f₀ (Hz) | partial 數 | 進 `acoustic_transfer` 的 partial 數 | 平方和 (Pa/N) | dB re 20 µPa | 檔內 `radius_m` |
|---|---|---|---|---|---|---|---|
| physical_piano | C4 | 260.87 | 40 | 4 | 0.40932 | 86.22 | 1.05 |
| physical_piano | E4 | 328.68 | 40 | 3 | 0.32111 | 84.11 | 1.05 |
| physical_piano | C5 | 521.74 | 25 | 2 | 0.20331 | 80.14 | 1.05 |
| yangqin（cimbalom） | midi 29 | 43.53 | 40 | 29 | 2.58571 | 102.23 | 1.05 |
| yangqin（cimbalom） | midi 56 | 207.05 | 40 | 6 | 1.43020 | 97.09 | 1.05 |
| yangqin（cimbalom） | midi 87 | 1240.92 | 12 | 1 | 0.60585 | 89.63 | 1.05 |

（腳本 `output/wf0907/R5/analyze_engine.py`；原始 dump 在 `output/wf0907/R5/*_modes.json`。）

### 3.4 兩張表擺在一起是什麼意思（**這一段很重要**）

| | TU Berlin | TsukiSynth B6 方案 B |
|---|---|---|
| 量的種類 | **Pa**（量到的絕對聲壓） | **Pa/N**（每 1 個「慣例牛頓」的 Pa） |
| 「1 N」是什麼 | — | `RadiationModel.h` 自己寫：「whatever drove this model's own dimensionless physics-only amplitude to read 1.0」——**不是量測或推導出來的力** |
| 激發方式 | **撥弦**（吉他／豎琴） | **敲擊**（鋼琴槌／揚琴槌） |
| 半徑 | 2.06 m（資料檔） | 1.05 m（裁決慣例，引用來源有誤，見 §0-2） |
| 涵蓋的部分音 | 全部（20–241 個） | 只有 f < f_ga 的（鋼琴 C4：40 個裡只有 4 個進表） |
| 能不能對著比大小 | **不能** | **不能** |

**這張表只證明量級，不證明模型。** 兩邊落在 58–102 dB 這個帶子裡，
代表 B6 的校準常數沒有把數字送到「0.001 Pa」或「10⁵ Pa」那種荒謬的地方；
除此之外它什麼都沒證明。若真要做有意義的比對，缺的東西列在 §5。

---

## §4 選項與建議（給月月選）

### 4.0 這一節會用到的詞（白話，先看這個再看下面的表）

| 詞 | 白話意思 |
|---|---|
| **GATE** | 專案的「驗收關卡」——一條跑得出數字的命令，數字達標才算過。**「不能當 GATE」＝這份資料不能拿來當驗收依據。** |
| **specimen 證據** | 「實體標本證據」——拿真的那件樂器量出來的數字。吉他／豎琴不是我們要模擬的樂器，所以**不算**我們引擎的實體證據。 |
| **`dump-modes`** | 我們自己的命令列工具的一個開關，會把某首曲子每個音的物理參數印成一張表（不出聲音、不影響成品音訊）。 |
| **`radius_m`** | 上面那張表裡的一欄，寫「假設在離樂器幾公尺處聽」。目前是 1.05。 |
| **`pressure_per_force_*`** | 同一張表裡的另一欄，寫「每施 1 單位力產生多少聲壓」。**它不會隨 `radius_m` 變**——算這一欄的程式（`RadiationModel::pressurePerForce()`，`src/physics/RadiationModel.h:328-336`）從頭到尾沒有用到半徑，改半徑只會改上一列那一欄的字。（本文件 2026-09-08 初版曾在這裡與 §4.2 選項 Y 寫「會隨 `radius_m` 一起變」，**是錯的，已更正**，見附錄 G #1。） |
| **R10** | 專案十條規則的第 10 條：**任何會讓既有曲子渲染結果改變的修改，必須停下來寫前後對照報告，不可以自己直接改。** |
| **schema 欄位** | 輸出檔（JSON）裡的一個「格子」。新增格子＝要同時改程式、改格式定義、改測試，工程量最大。 |
| **SOFA 檔** | 這個外部資料庫用的檔案格式（副檔名 `.sofa`），一個檔裝一件樂器一個音：麥克風擺在哪、量到多大聲、授權是什麼，全部寫在裡面。 |
| **`ReceiverPosition`** | SOFA 檔裡「收音點（麥克風）擺在哪裡」的那一欄。我們就是從這一欄讀到 2.06 公尺的。 |
| **dB SPL / `re 20 µPa`** | 就是平常講的「多少分貝」。`re 20 µPa` 只是把基準點寫清楚（20 微帕＝人耳勉強聽得到的壓力），數字意思跟 dB SPL 一樣。 |
| **Pa／`Pa/N`** | `Pa`（帕）＝聲音的壓力大小，量到多少就是多少。`Pa/N`（帕每牛頓）是**比值**：「每施 1 單位力會產生多少 Pa」。**兩者單位不同，不能對著比大小。** |
| **`kMeasurementRadiusM`** | 程式碼裡存放「假設聆聽距離」那個數字的名字，就在 `src/physics/RadiationModel.h` 第 291 行，目前寫死 `1.05`。**§4.2 說的「改數字」就是改這一個。** |
| **「那條寫死 1.05 的測試」** | 一條自動檢查（`tests/physics_models_repro.cpp` 第 533 行），內容是「這個距離必須等於 1.05」。距離一改，它就會亮紅燈——**不是壞掉，是它在盡責提醒「有人改了約定」**，所以要連它一起改。 |
| **「標本比對小工具」** | `tools/specimen_verify.py` 第 184 行。它負責問「我們算的這一筆，跟外面量的那一筆，是不是站在同一個位置量的？」它就是拿這個距離當比對用的鑰匙。距離一改，**以前用 1.05 記下來的舊紀錄就配不上新輸出**。 |
| **「§1 的 1.05 m 消音室陣列慣例」** | 程式碼註解裡的一句英文原文（`RadiationModel.h:285-290`：「`docs/EXTERNAL_ANCHOR_SOURCES.md` §1's 1.05 m anechoic-array convention」），意思是「1.05 公尺這個距離是從那個外部資料庫的消音室麥克風陣列來的」。**這句話本身就是要更正的那個錯誤**——資料庫其實是 2.06 公尺。 |

### 4.1 授權怎麼辦（NC 的問題）

TsukiSynth 若日後要賣，「非商業」這條就會咬到。四個選項：

| 選項 | 做法 | 好處 | 壞處 |
|---|---|---|---|
| **A. 純私下 sanity-check** | 資料只留在本機（已 gitignore），只用來看「量級有沒有離譜」，**結論寫成散文，不把它的數字寫進程式常數、不寫進要出貨的規格** | 風險最低；今天就能用 | 價值最低；**不能當驗收關卡（GATE），也不能當實體標本證據（見 §4.0）** |
| **B. 寫信要商業授權** | email 作者 `david.ackermann@tu-berlin.de`（此信箱寫在 SOFA 的 `AuthorContact` 屬性與論文通訊欄），說明用途、請求商業使用許可或釐清 NC 範圍 | 一旦拿到書面同意，整份資料可用，A8 徹底關掉 | 要等；可能被拒 |
| **C. 換授權相容的資料集** | 同一個典藏庫的兩份無 NC 資料集（**2026-09-09 重新打 API 逐字複驗，見下方「選項 C 的兩個候選」**）：**E13 BRAS**、**E14 Loudspeaker Orchestra**。但這兩份**都不是樂器指向性**（一個是房間聲學模擬基準、一個是喇叭陣列錄音），等於重新找 | 沒有 NC 問題 | 目前沒找到第二份「校準到絕對 Pa 的樂器」資料庫 |
| **D. 不用外部資料集，走實體試體量測** | `ROADMAP_PHYSICS.md` §0 意義下的 specimen-level 證據本來就要這條路 | 唯一能真正關掉「所有正確答案都是自己算的」這個結構弱點 | 要錢、要器材、要時間 |

> **建議：先 A、同時做 B。** A 今天就成立（資料已在本機、已 gitignore、本文件已登記），
> B 只花一封信的成本，而且 §0-2 那個 2.06 m 的更正**本來就不需要授權**——
> 它是「更正我們自己文件裡的引用錯誤」，引用事實不受 NC 限制。
> C 目前找不到替代品，D 是長期正解但不是這張卡能解的。
> **不建議**：把這份資料的任何數字寫成 `src/` 裡的常數、或寫進未來要出貨的文件當賣點。

#### 裁決記錄（2026-09-09）　**月月選 A**

> 記錄者：WF0909-P6（研究卡）。本節只記錄裁決本身與它產生的規則，**不重新論證**。

**裁決經過**：月月 2026-09-09 指示「看一下有沒有其他資料集參考，沒有的話先私下對照參考」。
→ 依此做了替代方案調查（`docs/EXTERNAL_DATASET_ALTERNATIVES.zh-TW.md`，2026-09-09），
結論是「**可商用＋校準到絕對聲壓＋有我們要的樂器**」三個條件同時成立的資料集**數量是 0**。
→ 條件「沒有的話」成立 → **A8 授權問題的裁決 = 選項 A（私下對照參考）。**

**選 A 之後生效的四條規則**（以下每一條都是這次裁決的直接後果，違反就是違反月月的裁決）：

| # | 規則 | 白話 |
|---|---|---|
| A-1 | 資料檔只留本機 `external_data/`，**已 gitignore，不進版控** | 那些下載來的檔案永遠不上傳、不隨產品出貨 |
| A-2 | **不得**把這份資料的任何數字寫成 `src/` 裡的常數 | 程式碼裡不會出現任何從它抄來的數字 |
| A-3 | **不得**寫進要出貨的文件或當賣點 | 不在使用手冊、宣傳、規格書裡提它的數字 |
| A-4 | **不得**當 GATE、不得當 specimen 證據 | 它不能拿來當驗收關卡，也不算「實體標本證據」 |

repo 內可以留、而且已經留的東西：**DOI、SHA256、授權原文引述、以及由它算出來的比對數字**（本文件 §2／§3）。
這些是「引用事實」，不受 NC 限制。

**選項 B（寫信要商業授權）＝ 月月可自行決定的後續，AI 不代發信。**
需要時，收件人與素材都在本文件 §4.1 選項 B 那一列（`david.ackermann@tu-berlin.de`）。
**本卡沒有寄任何信，也不會替月月寄。**

**2026-09-09 新增的兩個可商用來源（不改變本裁決）**：
`docs/EXTERNAL_DATASET_SUPPLEMENT.zh-TW.md` 登記了 Weinzierl 2018 JASA（CC BY 4.0）與 Iowa MIS 泰國鑼（網站聲明無限制）。
它們是**另外兩份可商用的來源**，**不是**這份 TU Berlin 資料的替代品（一個是論文數字表、一個沒有校準），
所以**上面四條 A-1～A-4 仍然完整適用於 TU Berlin 這份資料**。

#### 選項 C 的兩個候選：URL＋存取日期＋逐字原文（2026-09-09 重新查證）

上一版把這兩筆的出處丟到附錄 B，正文只寫「都是 CC BY-SA 4.0」。**本輪把出處搬回這裡並自己重打一次 API**：

| 代號 | 資料集名稱（API `name` 欄逐字） | 授權欄逐字原文 | 我打的 URL | 存取日期 |
|---|---|---|---|---|
| **E13** | 「BRAS - Benchmark for Room Acoustical Simulation」 | `dc.rights.uri` = 「https://creativecommons.org/licenses/by-sa/4.0/」（**`dc.rights` 欄不存在／無文字值**） | `https://api-depositonce.tu-berlin.de/server/api/core/items/38410727-febb-4769-8002-9c710ba393c4`（人可讀頁 <https://depositonce.tu-berlin.de/handle/11303/7506.3>；DOI <http://dx.doi.org/10.14279/depositonce-6726.3>） | **2026-09-09** |
| **E14** | 「Database: Recordings of a Loudspeaker Orchestra with Multi-Channel Microphone Arrays for the Evaluation of Spatial Audio Method」 | `dc.rights.uri` = 「https://creativecommons.org/licenses/by-sa/4.0/」（**同樣無 `dc.rights` 文字欄**） | `https://api-depositonce.tu-berlin.de/server/api/core/items/bf819762-b4b4-455b-a556-7fdb19350e7b`（人可讀頁 <https://depositonce.tu-berlin.de/handle/11303/16995.3>；DOI <https://doi.org/10.14279/depositonce-15774.3>） | **2026-09-09** |

**兩個必須跟著寫的但書**：

1. **「CC BY-SA 4.0」這句話的證據等級是「典藏庫 metadata 欄位」，不是「資料集自己的 LICENSE 檔」。**
   本輪**沒有**下載這兩份資料集去核對它們檔案裡印的授權——A8 主資料集就正是「四個來源四種說法」（§2.1），
   所以**在真的要用之前，必須比照 §2.1 的做法把資料檔內的授權欄也開來看**。
2. **兩份都不是樂器指向性資料**，換過去等於整個 A8 的用途重來一次。選項 C 目前仍是「有授權、沒用途」。

### 4.2 2.06 m vs 1.05 m 怎麼辦

這件事**與授權無關**，是我們自己文件寫錯了。三個選項：

| 選項 | 做法 | 影響 |
|---|---|---|
| **X. 只改「說法」，一個數字都不動** | 把三處寫錯的話改對：(1) `EXTERNAL_ANCHOR_SOURCES.md` §1 那句「直徑 2.1 m（半徑 1.05 m）」→ 改成「半徑 2.06 m，出處是資料檔裡記錄麥克風位置的那一欄」；(2) 程式碼註解裡那句「§1 的 1.05 m 消音室陣列慣例」（見 §4.0 詞彙表）→ 改成「1.05 m 是本專案自己訂的觀測距離，跟外部資料庫的 2.06 m 無關」；(3) 同一份程式碼另一句註解寫「1.0 ≡ 1 Pa **在 1.05 m 處** ≡ 94 dB SPL」→ 要把「在 1.05 m 處」拿掉，因為資料庫原文只說「1 ≡ 1 Pa」，**根本沒提距離**（見 §2.2） | **音訊零改變、參數表零改變**——只改文字敘述，不動任何數值。**最保守的一條。** |
| **Y. 真的把那個距離從 1.05 改成 2.06** | 讓我們假設的聆聽距離真的對齊外部資料庫（改的就是 §4.0 詞彙表講的 `kMeasurementRadiusM`） | **音訊完全不變。** 參數表裡只有「假設聆聽距離」那一欄從 `1.05` 變成 `2.06`，**「每單位力的聲壓」那一欄一個數字都不會變**（見 §4.0 詞彙表）。**但仍然不能直接動**，因為會連帶弄壞兩樣東西：(a)「那條寫死 1.05 的測試」會亮紅燈；(b)「標本比對小工具」拿這個距離當比對鑰匙，改完之後**以前用 1.05 記下來的舊紀錄就配不上新輸出**（兩者都見 §4.0 詞彙表）。嚴格講**不觸發第 10 條規則**（那條管的是音訊變不變），但既然要連測試與舊紀錄一起改 → **必須另開一張卡** |
| **Z. 兩者都留** | 加第二個觀測點（1.05 m 與 2.06 m 各印一份） | **要在輸出檔裡新增格子（schema 欄位）**，程式＋格式定義＋測試都要改，工程量最大 |

> **建議：選 X。** 因為 1.05 m 本來就是「我們自己拍板決定的一個約定」，不是誰量出來的
> （程式碼註解自己就寫得很清楚，原文引述：「a DECIDED CONVENTION」，出自 `src/physics/RadiationModel.h`），
> 所以留著 1.05 沒有物理錯誤，錯的只是「說它來自那個資料庫」這句話。
> 把話改對，比改數字安全得多。
> **Y 一定要做的話，必須另開卡**（要一起改測試與標本比對基準）——本卡不改 `src/`，也不觸發 R10。

#### 裁決記錄（2026-09-09）　**規劃者裁決選 X**，已由 WF0908-P4／WF0909-P4b 落地

> 記錄者：WF0909-P6（研究卡）。

**裁決**：2.06 m vs 1.05 m 這一題**不需要月月裁決**——它不是取捨，是「我們自己文件寫錯了」。
規劃者依本節建議採 **選項 X（只改說法，一個數字都不動）**，交由兩張施工卡落地：

| 卡 | 範圍 | 本卡收尾時（2026-09-09）親自跑 `git status --porcelain` 看到的狀態 |
|---|---|---|
| `docs/workcards/WF0908_P4_a8_citation_fix.md` | `docs/EXTERNAL_ANCHOR_SOURCES.md` §1 表格＋§5.1；`src/physics/RadiationModel.h` 註解 | 兩檔皆 ` M`（**已改，unstaged**）；證據檔 `reports/gate_outputs/wf0908_P4_a8.txt` 已存在 |
| `docs/workcards/WF0909_P4b_citation_fix_finish.md` | 補完 P4 第 3 項（`docs/RADIATION_POWER_SOURCES.md`）＋`docs/workcards/B7.md` §4.6＋`src/physics/HammerImpulse.h` 檔頭，並把 P4 兩檔一併納入稽核 | 三檔皆已出現在工作樹（`docs/RADIATION_POWER_SOURCES.md` ` M`、`docs/workcards/B7.md` `MM`、`src/physics/HammerImpulse.h` ` M`）；**證據檔 `reports/gate_outputs/wf0909_P4b_citation.txt` 尚未產生** |

**所以本節的狀態是「X 已裁決、改動已在工作樹、但尚未經稽核 stage」，不是「已完成」。**
最終是否落地，以那兩張卡的稽核結果為準；本卡**沒有**碰上表任何一個檔案。
（提醒：這幾張卡與本卡同時在同一個工作樹作業，上表是本卡收尾那一刻的快照，稽核時請自己重跑一次 `git status`。）

**選 X 之後生效的規則**：`kMeasurementRadiusM = 1.05`（`src/physics/RadiationModel.h`）**維持不動**；
凡是提到 1.05 m 的地方，都必須寫明它是**本專案自訂的觀測距離**，**不得**再宣稱它來自 TU Berlin 資料庫。
選項 Y（真的改成 2.06）與選項 Z（兩者都留）**都沒有被採用**；要做必須另開卡。

**2026-09-09 本卡新增的一條支持證據（A 級，來自原始論文全文）**：
Weinzierl et al. 2018 JASA 的 p.1348（本機 PDF 第 3 頁）有一句原文——
「of the sound radiating parts of d0 > r/2 = 1.05 m」
（完整句：「None of the musical instruments recorded exhibited a characteristic dimension of the sound radiating parts of d0 > r/2 = 1.05 m.」）
→ **「1.05 m」確實印在原始文獻裡，但它的身分是「陣列半徑 r ≈ 2.1 m 的一半」，是用來檢查「樂器本身夠不夠小」的門檻，
不是麥克風距離。** 這解釋了本專案當初為什麼會把 1.05 m 誤記成「照抄那個資料庫」，
也再次確認**選 X（改說法、不改數字）是正確的處理方式**。
出處與取得方式見 `docs/EXTERNAL_DATASET_SUPPLEMENT.zh-TW.md` §1.1。

---

## §5 已知缺口（誠實列，含查不到的）

1. **DOI 打架，而且資料檔裡印的那個是死的。**
   - 說明 PDF 與每個 SOFA 檔的 `Reference` 屬性印的是 `10.14279/depositonce-5861.3`——
     實測 `https://doi.org/10.14279/depositonce-5861.3` **回 404**（2026-09-07 驗證）。
   - 能解析的是 `10.14279/depositonce-19858` → `https://depositonce.tu-berlin.de/handle/11303/21058`（Version 3，本卡下載的就是它）。
   - 舊版 `10.14279/depositonce-5861.2` → `handle/11303/6305.2`（Version 2，錄音是 wav 格式）。
   - **引用時請用 `10.14279/depositonce-19858`。**
2. **DepositOnce 典藏記錄沒有給 CC 授權**（`dc.rights.uri = rightsstatements.org/vocab/InC/1.0/`），
   只有資料檔內部與論文給。也就是說「哪一份文件在法律上算數」**我們無法從公開資訊判定**——
   這是 §4.1 選項 B（寫信問）的主要理由。**未取得法律意見；本文件不是法律建議。**
3. **`SteadyPart` 欄位是空的。** 說明 PDF 說它「indicates the range of the manually determined stationary portion in samples」，
   但吉他錄音檔這個欄位全是 `[0, 0]`——**第五輪把抽驗改成全檔普查：`2_Acoustic_guitar_modern_recordings.zip`
   內 88 個 `.sofa`（ff 44 ＋ pp 44）的 `SteadyPart` 唯一值就是 `0`，88/88**（原文寫「抽驗 12 個 ff 檔」，已升級為全檔）。
   → §3.1 的錄音交叉檢查只好用全訊號 RMS，數字會被衰減尾與靜音拉低。**這是資料集的缺陷，不是我們算錯。**
4. **想用 `3_Audio_Features.csv` 反推包絡面半徑，失敗。**
   用說明 PDF 式 (3)(4)（`Lw = L̄p + 10log₁₀(S1/S0)`）反推，44 個吉他音推出的半徑散在
   **0.97 – 1.67 m（平均 1.26 m）**，不是常數 → 反推無效（因為我拿去當 `L̄p` 的是穩態部分音平方和，
   本來就低估全錄音的 `L̄p`，且低估量隨音高變動）。
   **所以半徑的結論只靠 E9 + E10 兩個直接讀到的值，不靠這個反推。**
   （**2026-09-08 第六輪更正**：本文件先前在這裡寫「`3_Audio_Features.csv` 的欄名是 `features1 … features133`
   這種無語意的佔位名、資料集內找不到欄位定義表、只能推測第 7 欄是聲功率級、未取得原文確認」——**這三句都是錯的**。
   那個 CSV 的**第 1 列**才是 `features1 … features133` 佔位名，**第 2 列就是完整的 133 個真欄名**，
   第 7 欄白紙黑字寫 `SoundPower in dB`（A 級直接證據，原文引述：「SoundPower in dB」，
   出自 `external_data/tu_berlin_directivity/3_Audio_Features.csv` 第 2 列第 7 欄，2026-09-08 讀取）。
   也就是說**欄位定義表就在檔案自己裡面**，不必去猜、也不必去翻沒下載的 `5_Tools.zip`。
   我用這一欄重跑了上面那組反推，得 **min 0.968／max 1.674／mean 1.262 m**，
   與原本寫的 0.97–1.67／1.26 **逐格相同**——**數值沒有被改寫，被改寫的只有「我們有多確定」這句話**。
   證據與可重跑腳本見附錄 I 的 Y1。）
5. **`1a` 只有 ff。** 吉他 44 個單音指向性檔全部 `dynamic = ff`；pp 只存在於 `2_*_recordings.zip`。
   說明 PDF Table 1 標吉他 pp 音域 C2–B5，但 `1a` 裡沒有 pp 檔。
   （**第五輪新增，Table 1 的 pp 欄本身也對不上資料**：`2_` 錄音裡真的存在的 pp 檔是
   **MIDI 40–83＝E2–B5，44 個、連號無缺**，跟 ff 完全一樣，**不是 Table 1 寫的 C2–B5**。
   同時確認 `1a` 的吉他 44 檔也正好是 MIDI 40–83，**與 Table 1 的 ff 欄一致**。證據見附錄 H 的 X5。
   Table 1 的欄位語意由其圖說原文釘死：「for the playing dynamics pianissimo (pp) and fortissimo (ff)」
   ——所以那兩欄確實是 pp／ff，不是「錄音／指向性」。）
6. **豎琴音域對不上。** `1a` 有 **B0–F#7**（MIDI 23–102，其中 24、26 兩號缺，共 78 音），
   說明 PDF Table 1 寫 C1–F4。**未取得說明**。
   （**第五輪更正**：先前寫「B0–F7」，最高音實為 F#7＝MIDI 102；證據見附錄 H 的 X6。
   另記一個資料本身的怪處：F#7（MIDI 102）檔內的基頻是 **2993.95 Hz**，
   **比低半音的 F7（MIDI 101）的 3126.19 Hz 還低**——這是資料集自己的基頻標定異常，
   不是我們算錯，**高音區的 `N[0]` 不宜當基頻真值使用**。）
7. **對 TsukiSynth 的本質限制沒有變**（`EXTERNAL_ANCHOR_SOURCES.md` §1.1 已經講過，本卡再確認一次）：
   這個資料庫**沒有揚琴、沒有鋼琴、沒有舌鼓、沒有鑼**。吉他／豎琴是**撥弦**，
   TsukiSynth 的 Cimbalom/Piano 是**敲擊**；Beam（tongue_drum）與 Plate（water_gong）**完全沒有對應樂器**。
   → 它**不能**成為任何引擎的 specimen-level 證據。
8. **沒有下載的部分**：另外 **40 個**樂器錄音壓縮檔（**51,163,473,525 位元組 = 51.16 GB**）、
   `1c` OpenDAFF、`1d` GLL、`4_Pictures.zip`、`5_Tools.zip`（Matlab）。
   數字來源（可原樣重跑）：`GET https://api-depositonce.tu-berlin.de/server/api/core/bundles/8d6f2969-ee21-4fee-835a-dcecb28dd080/bitstreams?size=200`
   （2026-09-08 實測）回 `totalElements = 50`，其中檔名以 `2_` 開頭的錄音壓縮檔 **42 個**、
   非錄音檔 8 個（`0_Documentation.pdf`、`1a`、`1b`、`1c`、`1d`、`3_Audio_Features.csv`、`4_Pictures.zip`、`5_Tools.zip`）；
   扣掉已下載的吉他與豎琴兩個，剩 40 個。
   **注意「42 個錄音檔」≠「42 種樂器」**：`0_Documentation.pdf` 第 1 頁寫的是
   「A collection of 3305 single notes of 41 musical instruments」（41 種）。
   卡的目標子集是撥弦（吉他＋豎琴），已全數取得。
9. **孔徑／低頻限制**：消音室下限 `fc = 63 Hz`。
   **這個數字只出現在 arXiv 預印本（C 級），隨資料集發佈的 `0_Documentation.pdf` 裡沒有這句話。**
   我用 PyMuPDF 對本機 `0_Documentation.pdf`（8 頁，SHA256 `f6bf92e4…9d45`，見附錄 A）做全文掃描：
   `63` 只出現 1 次且是「54.63 m2」，`cut`／`chamber`／`1070` 各 0 次，`anechoic` 3 次但都沒有頻率下限。
   ⇒ 見附錄 B 的 E12（arXiv 原句：「a lower cut-off frequency of fc = 63 Hz」）。
   §3.1 的 E2（82.7 Hz）勉強在範圍內，§3.2 的豎琴 B0（31.4 Hz）**低於這個下限**，
   那個 56.73 dB 不可信，本文列出只為顯示音域，**不得引用**。
   （順帶一提：我們自己的 `docs/EXTERNAL_ANCHOR_SOURCES.md:46`「消音室下限 `fc = 63 Hz`」
   位在一張**逐格都沒有標出處**的表裡（§1，該表把預印本、期刊、資料檔的說法混在一起講），
   讀者無法分辨哪一格來自哪一份——這正是本卡在 §2 拆開的同一種「來源被合併」問題。
   **已記入 open_items 等月月裁決，本卡未改該檔。**）

---

## §附錄 A：檔案登記表（SHA256）

下載來源一律為 DepositOnce REST bitstream 端點
`https://api-depositonce.tu-berlin.de/server/api/core/bitstreams/<uuid>/content`，
下載日 **2026-09-07 – 2026-09-08**，存放於 `external_data/tu_berlin_directivity/`（已 gitignore）。
「登記大小」欄同時比對過典藏庫 API 自報的 `sizeBytes`，逐檔一致。

| 檔名 | 位元組大小 | 與典藏庫 API `sizeBytes` 比對 | SHA256 | bitstream uuid |
|---|---:|---|---|---|
| `0_Documentation.pdf` | 1,107,344 | 一致 | `f6bf92e4c06a0740790f088bf98532db71efc5b348d644a40dc7e54107169d45` | `8d25bc14-a882-4f45-be0d-7e0c0035221c` |
| `1a_DirectivitiesSingleTones_SOFA.zip` | 45,126,485 | 一致 | `98525ac61faf13d57b4f4225d362851b50447e34fcb093aabd91cd1bee73a058` | `94c03246-dce3-4d50-8c14-70973d056e3d` |
| `1b_Directivities3rdOctave_SOFA.zip` | 473,039 | 一致 | `1e817125a488e16a0b136d1f1474e18ac343d2aad43757ec49eb5de8ccb86318` | `11bc7c3e-1092-494c-8999-3595e05b207c` |
| `2_Acoustic_guitar_modern_recordings.zip` | 1,095,042,381 | 一致 | `7d87091f33b5a7a5912983a3f963abc694957c0a153d7ffb4ea48aa8fc04d1c0` | `fff8b867-d786-43de-853f-cfcb61e4546e` |
| `2_Double_action_harp_modern_recordings.zip` | 2,621,077,413 | 一致 | `551369c92cef5c4ef826e0ef13c061733974f403a199489c5fc4b651e242b6d0` | `6009c849-870a-47b1-8c54-7b68ef105c40` |
| `3_Audio_Features.csv` | 7,900,263 | 一致 | `6fc7085c5d2454f7a205329490c48b67b01e6d68fb0535ced158680c3edbb68b` | `51186d50-5128-43ec-a49a-4b555adf3206` |
| `license.txt` | 2,681 | 一致 | `19636d65d238893bbbf36e7e92395f396c4362217491e208ddc527b59eba6aad` | `5fc335d1-7b59-45a8-90eb-095ec4e0911f` |

**子集合計：3,770,729,606 位元組（3.77 GB）**。
典藏品的 **ORIGINAL bundle**（uuid `8d6f2969-ee21-4fee-835a-dcecb28dd080`）共 **50 個 bitstream、55,037,492,445 位元組（55.04 GB）**
（2026-09-08 以附錄 B 的 bitstreams API 逐筆加總所得）；`license.txt` 不在這個 bundle 內，是典藏庫另外掛的存放授權檔。
本卡只取撥弦子集。

> **來源完整性（2026-09-08 第三輪新增）**：上表的 SHA256 只證明「本機這 7 個檔前後沒被改過」，
> 不證明「下載到的位元組跟典藏庫的原檔一樣」。第三輪補做了後者——
> 典藏庫 bitstream API 每個檔都自報一個 MD5（`checkSum.value`），把本機檔重算 MD5 去對，**6/6 相符**
> （`license.txt` 不在 ORIGINAL bundle 內、API 沒給校驗值，故為 6 而非 7）。逐檔數值見 §附錄 F 的 W2。

## §附錄 B：來源清單

| 代號 | 來源 | URL | 存取日期 | 等級 |
|---|---|---|---|---|
| E1, E6, E10 | Weinzierl et al., *A Database of Anechoic Microphone Array Measurements of Musical Instruments — Recordings, Directivities, and Audio Features*, Version 3, 2024-02-02（隨資料集發佈的 `0_Documentation.pdf`） | DepositOnce bitstream `8d25bc14-a882-4f45-be0d-7e0c0035221c`（本機副本，SHA256 見附錄 A） | 2026-09-07 | A |
| E2, E9 | SOFA 檔 global attributes / `ReceiverPosition`（`1a_DirectivitiesSingleTones_SOFA.zip`、`1b_Directivities3rdOctave_SOFA.zip`） | 同上（本機副本） | 2026-09-07 | A |
| E3 | Ackermann, Brinkmann, Weinzierl, "A Database with Directivities of Musical Instruments", *J. Audio Eng. Soc.* 72(3):170–179, 2024-03，DOI 10.17743/jaes.2022.0128 | https://aes2.org/publications/elibrary-page/?id=22388 | 2026-09-07 | B（僅摘要；全文付費牆） |
| E4 | DepositOnce item metadata（`dc.rights.uri`、`dc.identifier.uri`、bitstream 清單） | https://depositonce.tu-berlin.de/handle/11303/21058 ／ DOI https://doi.org/10.14279/depositonce-19858 | 2026-09-07 | B |
| E5, E7, E8, E11, **E12** | Ackermann, Brinkmann, Weinzierl, *A Database with Directivities of Musical Instruments*, arXiv:2307.02110（2023-07-05） | https://arxiv.org/pdf/2307.02110 ／ https://arxiv.org/abs/2307.02110 | 2026-09-07 / **2026-09-08 全文重取確認** | C（預印本，全文開放） |
| **E12**（新增，§5 第 9 點用） | 同上 arXiv 全文 §1「Measurement Setup」：消音室容積與低頻下限。原句 ≤15 字引述：「a lower cut-off frequency of fc = 63 Hz」（前文為「volume of approximately 1070 m3 and」） | https://arxiv.org/pdf/2307.02110 | 2026-09-08 | C（**此句僅見於預印本，隨檔說明 PDF 無**） |
| **E13**（新增，§4.1 選項 C 用） | DepositOnce item「BRAS - Benchmark for Room Acoustical Simulation」，handle `11303/7506.3`，uuid `38410727-febb-4769-8002-9c710ba393c4`。API 讀出的 `dc.rights.uri` 原文（≤15 字）：「https://creativecommons.org/licenses/by-sa/4.0/」（`dc.rights` 欄為空） | `https://api-depositonce.tu-berlin.de/server/api/core/items/38410727-febb-4769-8002-9c710ba393c4` ／ 人可讀頁 https://depositonce.tu-berlin.de/handle/11303/7506.3 ／ DOI http://dx.doi.org/10.14279/depositonce-6726.3 | 2026-09-08 | B |
| **E14**（新增，§4.1 選項 C 用） | DepositOnce item「Database: Recordings of a Loudspeaker Orchestra with Multi-Channel Microphone Arrays for the Evaluation of Spatial Audio Method」，handle `11303/16995.3`，uuid `bf819762-b4b4-455b-a556-7fdb19350e7b`。API 讀出的 `dc.rights.uri` 原文（≤15 字）：「https://creativecommons.org/licenses/by-sa/4.0/」（`dc.rights` 欄為空） | `https://api-depositonce.tu-berlin.de/server/api/core/items/bf819762-b4b4-455b-a556-7fdb19350e7b` ／ 人可讀頁 https://depositonce.tu-berlin.de/handle/11303/16995.3 ／ DOI https://doi.org/10.14279/depositonce-15774.3 | 2026-09-08 | B |
| — | CC BY-NC-SA 4.0 授權條款頁 | https://creativecommons.org/licenses/by-nc-sa/4.0/ | 2026-09-07 | B |
| — | DepositOnce 存放授權 `license.txt`（**是投稿者→典藏庫的合約，不是使用者授權**，本卡確認過內文） | bitstream `5fc335d1-7b59-45a8-90eb-095ec4e0911f` | 2026-09-07 | A |
| — | DepositOnce discover API（確認「其他資料集有正確填 CC 授權」，§2.1 判讀段） | `https://api-depositonce.tu-berlin.de/server/api/discover/search/objects?query=Musical%20Instruments%20directivities&dsoType=item` | 2026-09-08（**完整 URL，可原樣重跑**） | B |
| — | DepositOnce bitstream 清單（ORIGINAL bundle 的 50 個檔名／`sizeBytes`，供附錄 A 與 §5 第 8 點） | `https://api-depositonce.tu-berlin.de/server/api/core/bundles/8d6f2969-ee21-4fee-835a-dcecb28dd080/bitstreams?size=200` | 2026-09-08（**完整 URL，可原樣重跑**） | B |
| — | 舊版本 DOI 解析驗證（5861.2 → handle 11303/6305.2；5861.3 → HTTP 404） | https://doi.org/10.14279/depositonce-5861.2 等 | 2026-09-07 | B |

**署名（CC BY-NC-SA 4.0 的 BY 要求）**

> **2026-09-09（WF0908-P5）逐字重抄**：下面這段的來源是**說明 PDF 第 2 頁「If you use this database, please cite:」區塊的第二條**，
> 本輪用 PyMuPDF 打開本機檔 `external_data/tu_berlin_directivity/0_Documentation.pdf`（SHA256 見上表）重新抄一次。
> 上一版少抄了典藏編號 `5861`、並把 `DepositOnce:` 的冒號寫成逗號；已補正。

**（i）照抄說明 PDF 的引用格式（逐字，只把換行接起來）**：

> Weinzierl, S., Vorländer, M., Ackermann, D., Behler, G., Brinkmann, F., Coler, H. v.,
> Detzner, E., Krämer, J., Lindau, A., Pollow, M., Schulz, F., Shabtai, N. R. (2024).
> Musical Instruments - A data base with recordings, directivities, and features of classical
> musical instruments. DepositOnce: Technische Universität Berlin, 5861, Version 3. DOI:
> https://doi.org/10.14279/depositonce-5861.3
>
> —— 抄自 `0_Documentation.pdf` **p.2**（區塊標題原文：「If you use this database, please cite:」）。

**（ii）本專案實際使用的署名字串**（＝上式，只換掉那個死掉的 DOI）：

Weinzierl, S., Vorländer, M., Ackermann, D., Behler, G., Brinkmann, F., Coler, H. v., Detzner, E., Krämer, J.,
Lindau, A., Pollow, M., Schulz, F., Shabtai, N. R. (2024). *Musical Instruments - A data base with recordings,
directivities, and features of classical musical instruments*. DepositOnce: Technische Universität Berlin, 5861, Version 3.
DOI: https://doi.org/10.14279/depositonce-19858 　授權：https://creativecommons.org/licenses/by-nc-sa/4.0/

**（iii）這份資料集同時存在三個不同的「標題」，抄的時候要知道自己抄的是哪一個**（2026-09-09 新增，全部本輪逐字取得）：

| 哪一個標題 | 逐字原文 | 抄自哪裡 |
|---|---|---|
| **引用格式用的資料集題名**（上面 (i)(ii) 用的就是這個） | 「Musical Instruments - A data base with recordings, directivities, and features of classical musical instruments」 | `0_Documentation.pdf` **p.2** 的 “please cite” 區塊 |
| **說明 PDF 自己的封面題名** | 「A Database of Anechoic Microphone Array Measurements of Musical Instruments」＋副題「Recordings, Directivities, and Audio Features」＋「Version 3」 | `0_Documentation.pdf` **p.1** 封面（本輪 PyMuPDF 抽字） |
| **SOFA 檔內記的資料庫名** | 「A Database of Anechoic Microphone Array Measurements of Musical Instruments」 | SOFA global attribute **`DatabaseName`**（本輪以 h5py 開 `1b_Directivities3rdOctave_SOFA.zip` 內的 `Acoustic_guitar_modern_3rdOctave.sofa` 讀出）。同檔的 `Title` 是**單檔題名**「Directivity measurement: Acoustic guitar modern」，**不是資料集題名**，不可拿來當書目 |

> **附帶查到、與授權判讀一致的一格**：同一個 SOFA 檔的 global attribute **`License` = 「cc by-nc-sa 4.0」**
> （逐字，小寫），`Reference` = 「dx.doi.org/10.14279/depositonce-5861.3」，`AuthorContact` = 「david.ackermann@tu-berlin.de」。
> 這是 §2.1 授權判讀的**第五個**同向證據（資料檔本身），與說明 PDF 的 “provided under a Creative Commons BY-NC-SA licence” 一致。

**兩處與說明 PDF 的差異，逐一交代**：
(a) 第六位作者寫 `Coler, H. v.`——這是**說明 PDF 引用格式的原樣**（本輪重新確認）。
    同一份 PDF 的**封面**卻寫 `Henrik von Coler`，典藏庫 metadata 寫 `Coler, Henrik von`；三者同一人，此處以 PDF 指定的引用格式為準。
(b) 說明 PDF 印的 DOI `10.14279/depositonce-5861.3` **實測 404**（§5 第 1 點），
    故 (ii) 改用可解析的 `10.14279/depositonce-19858`；這是**刻意的替換**，(i) 保留原樣以便對照。
（本文件只引用其 metadata 與由其計算出的統計量，**未再散布任何原始資料檔**。）

## §附錄 C：本卡產生的本機檔案（皆在 gitignore 的 `output/` 下，不進版控）

| 路徑 | 內容 |
|---|---|
| `output/wf0907/R5/analyze_guitar.py` | 吉他 44 音 Mic#04 RMS→dB SPL 計算 |
| `output/wf0907/R5/analyze_harp.py` | 豎琴 78 音同上 |
| `output/wf0907/R5/analyze_engine.py` | `dump-modes` 的 `acoustic_transfer[]` 彙整 |
| `output/wf0907/R5/analyze_recordings.py` | **§3.1 的錄音 IFFT 交叉檢查**（式(1) 單邊→雙邊→IFFT→Mic#04 全訊號 RMS；ff/pp 各 3 音）。2026-09-08 補寫並重跑，數字與 §3.1 表逐格一致 |
| `output/wf0907/R5/guitar_recording_rms.json` | 上一列腳本的輸出（Pa、dB、樣本數、`SteadyPart`） |
| `output/wf0907/R5/crosscheck_lw.py` | §5 第 4 點的（失敗的）包絡面半徑反推 |
| `output/wf0907/R5/guitar_spl.json` | 吉他逐音數字 |
| `output/wf0907/R5/*_modes.json` | CLI `--dump-modes` 原始輸出 |
| `output/wf0907/R5/audit6/v6_radius.py` | 第六輪：確認 `3_Audio_Features.csv` 第 2 列＝真欄名列、第 7 欄＝`SoundPower in dB`（見附錄 I 的 Y1） |
| `output/wf0907/R5/audit6/v6_radius2.py` | 第六輪：**自己重寫**的半徑反推＋吉他 SPL 重驗（min 0.968／max 1.674／mean 1.262 m；SPL 58.69／77.03／68.90 dB），與本文件原數字逐格相同 |

---

## §附錄 D：複核修正記錄（2026-09-07 → 2026-09-08）

引用複核員（另一位 Opus）提出 4 條 findings，逐條處理如下。**沒有補進任何新的假來源**；
改不掉的地方一律改成「未取得原文／作廢」，或標明真正的出處等級。

| # | 嚴重度 | 複核指出的問題 | 我怎麼改 | 我自己重驗的證據 |
|---|---|---|---|---|
| 1 | **blocker** | §5 第 9 點寫「說明與論文都指出消音室下限 `fc = 63 Hz`」，但隨檔 `0_Documentation.pdf` 根本沒有這句 → 引用不實 | **改掉主張的出處**：明寫「這個數字只出現在 arXiv 預印本（C 級），隨檔說明 PDF 沒有這句話」，並在附錄 B 新增來源列 **E12** 記下 arXiv 原句與 URL。63 Hz 這個數字本身保留（它可溯源），變的是「誰說的」。另加一句提醒 `docs/EXTERNAL_ANCHOR_SOURCES.md:46` 有同樣的合併錯誤，**本卡未改該檔，記入 open_items** | (a) 我用 PyMuPDF 重掃本機 `0_Documentation.pdf`（SHA256 `f6bf92e4…9d45`，與附錄 A 一致，8 頁）：`63` 命中 1 次＝「54.63 m2」，`cut`/`chamber`/`1070` 各 0 次，`anechoic` 3 次皆無頻率下限。(b) 重取 arXiv 2307.02110 全文 PDF 並抽字，命中「volume of approximately 1070 m3 and a lower cut-off frequency of fc = 63 Hz」 |
| 2 | major | §5 第 8 點「其餘 **48 種**樂器的錄音」無來源且與典藏庫檔案清單矛盾 | **48 → 40**，並改成講「錄音壓縮檔個數」而不是「樂器種數」，同時把可原樣重跑的 bitstreams API URL 與位元組數寫進本文；另補一句「42 個錄音檔 ≠ 42 種樂器，說明 PDF 寫 41 種」。附錄 A 尾句也改精確：50 個 bitstream 是 **ORIGINAL bundle** 的數，`license.txt` 不在其中 | 我自己打 `…/core/bundles/8d6f2969-…/bitstreams?size=200`：`totalElements=50`，`2_` 開頭 42 個、非錄音 8 個，扣掉已下載 2 個 → **剩 40 個、51,163,473,525 位元組**；50 檔合計 **55,037,492,445** 位元組，與附錄 A 的 55.04 GB 一致 |
| 3 | major | §2.1 判讀段「discover API 查同關鍵字 10 筆，7 CC / 3 InC」沒有可回溯的 URL（附錄 B 把 query 省略成 `query=…`），違反引用鐵律第 1 條 | **原敘述作廢並在文中明寫「無法重現、已作廢」**，換成我自己重跑、附完整 URL 的實測值；附錄 B 該列改成完整 URL，並拆成 discover 與 bitstreams 兩列。同時明寫「此旁證不影響 NC 結論（NC 只靠 E1/E2/E3）」 | 我跑 `…/discover/search/objects?query=Musical%20Instruments%20directivities&dsoType=item`：`totalElements=437`，第一頁 20 筆中 **CC 網址 14 筆、In Copyright 6 筆、空白 0 筆**。（複核員自己也跑不出「10 筆 7/3」——三方三種結果，故原句作廢） |
| 4 | minor | (a) §4 選項表對沒有樂理／程式基礎的讀者仍有未解釋術語；(b) §3.1 的錄音 IFFT 交叉檢查是全文唯一沒登記腳本路徑的數字 | (a) 新增 **§4.0 白話詞彙表**（GATE／specimen 證據／`dump-modes`／`radius_m`／`pressure_per_force_*`／R10／schema 欄位），並把 §4.1 A 選項、§4.2 Y/Z 選項的句子就地改成白話。(b) **補寫腳本 `output/wf0907/R5/analyze_recordings.py`** 並登記進附錄 C（含輸出 `guitar_recording_rms.json`） | 重跑該腳本，與 §3.1 表**逐格一致**：ff 61.67 / 62.21 / 70.45 dB，pp 52.03 / 50.77 / 56.88 dB，ff−pp 9.64 / 11.44 / 13.57 dB；`SteadyPart` 三檔皆 `[[0,0]]`，佐證 §5 第 3 點 |

**本次修正沒有碰的東西**：`src/`、`tools/`、`scores/`、任何容差、`ROADMAP_PHYSICS.md`；
`docs/EXTERNAL_ANCHOR_SOURCES.md` 也沒有再動（§1 表格那一格是上一輪就改好的，本輪零改動）。
§0 的兩個結論（**授權含 NC**、**半徑 2.06 m**）在本輪複核中**沒有被推翻，也沒有改變**。

---

## §附錄 E：獨立重驗記錄（2026-09-08，第二輪，逐條自己重跑）

本輪**不採信附錄 A–D 的任何自報數字**，全部重算／重讀一次。結論：**逐項一致，零修正**。

| # | 重驗的主張 | 我怎麼驗 | 結果 |
|---|---|---|---|
| V1 | 附錄 A 的 7 個 SHA256 與位元組大小 | `python hashlib.sha256` 逐檔重算（含 1.10 GB 吉他與 2.62 GB 豎琴壓縮檔，全檔非抽樣） | **7/7 逐字元相同**，大小逐檔相同 |
| V2 | 檔案大小與典藏庫 API 自報 `sizeBytes` | 重打 `…/core/bundles/8d6f2969-…/bitstreams?size=200` | 7 檔中在 ORIGINAL bundle 的 6 檔 `sizeBytes` 全部一致；bitstream uuid 全部一致 |
| V3 | §5 第 8 點：`totalElements=50`、42 個 `2_` 錄音檔、剩 40 個、51,163,473,525 位元組、50 檔合計 55,037,492,445 位元組 | 同上 API 重跑並重新加總 | **五個數字全部相同**；非錄音 8 檔檔名亦相同 |
| V4 | §2.1 判讀段的 discover API 分布 | 重打 `…/discover/search/objects?query=Musical%20Instruments%20directivities&dsoType=item` | `totalElements=437`；第一頁 20 筆＝`by/4.0/`×10、`InC`×6、`by-nc-sa/4.0/`×1、`by/3.0/de/`×1、`by-nc-nd/2.0/`×1、`by-nc-nd/3.0/de/`×1 → **CC 14／InC 6／空白 0，完全相同** |
| V5 | E2：SOFA 的 `License` 屬性 | 用 h5py 重開 `Acoustic_guitar_modern_e2_singleTones.sofa` 印出全部 global attrs | `License = b'cc by-nc-sa 4.0'` ✅ |
| V6 | E9：半徑 2.06 m、Mic#04 座標 | 重讀 `ReceiverPosition`（32×3，`Type='spherical'`、`Units='degree, degree, metre'`） | 32 顆半徑唯一值 **2.06**；Mic#04 = `[0.00, −10.81, 2.06]` ✅ |
| V7 | §2.4 其他 metadata | 同一次 dump | `SOFAConventions=FreeFieldDirectivityTF`、`Version=2.1`、`DataType=TF`、`SourceTuningFrequency=443.0`、`Musician='Hanjo Maempel'`、`Reference='dx.doi.org/10.14279/depositonce-5861.3'`、`AuthorContact='david.ackermann@tu-berlin.de'`、`Comment`＝部分音 RMS 聲壓（Pa）、`SourceView.Reference`＝「Normal of the soundboard aimed slightly above Mic#04」 ✅ 全部一致 |
| V8 | E1／E6／E10：說明 PDF 的三句 | PyMuPDF 重抽本機 `0_Documentation.pdf`（8 頁，SHA256 見 V1） | 「The database is provided under a Creative Commons BY-NC-SA licence」1 次；「a value of 1 corresponds to a pressure of 1 Pascal」1 次；「S1 = 54.63 m2」1 次 ✅ |
| V9 | §5 第 9 點：說明 PDF **沒有** `fc = 63 Hz` | 同一次全文掃描 | `cut-off` 0 次、`1070` 0 次、`63` 僅 1 次（＝「54.63 m2」）、`anechoic`（不分大小寫）3 次且皆無頻率下限 ✅ 與附錄 D#1 的更正相符 |
| V10 | E5／E7／E8／E11／E12：arXiv 五句 | 重新取回 arXiv:2307.02110 全文 PDF 並抽字 | 「The data is available under the CC BY-SA 4.0 licence.」／「a digital ampli-tude of 1 corresponds to a pressure of 1 Pascal resp. a sound pressure level of Lp = 94 dB」／「pentakis dodecahedron with a di-ameter of 2.1 m」／「volume of approximately 1070 m3 and a lower cut-off frequency of fc = 63 Hz」 ✅ 四處全部命中 |
| V11 | E3：JAES 摘要的授權句 | 重取 https://aes2.org/publications/elibrary-page/?id=22388 | 「The data is available under the CC BY-NC 4.0 license.」；作者 Ackermann／Brinkmann／Weinzierl，*JAES* **72(3):170–179，2024-03** ✅ |
| V12 | E4：典藏記錄的 `dc.rights.uri` | 重打 `…/api/pid/find?id=hdl:11303/21058` | `dc.rights.uri = http://rightsstatements.org/vocab/InC/1.0/`、`dc.rights` 空、item uuid `b194da8b-e98c-4761-9100-2b0bb6ba93e8` ✅ |
| V13 | §5 第 1 點：三個 DOI 的解析結果 | 逐個實打 `https://doi.org/…` | `…-5861.3` → **HTTP 404**；`…-5861.2` → 200，該 item `handle = 11303/6305.2`；`…-19858` → 200，item uuid `b194da8b-…` ✅ 三條全部如文所述 |
| V14 | CC BY-NC-SA 4.0 三條款原文 | 重取 https://creativecommons.org/licenses/by-nc-sa/4.0/ | BY／NC／SA 三句逐字相同 ✅ |
| V15 | §3.1 吉他 44 音數字 | 重跑 `output/wf0907/R5/analyze_guitar.py` | E2 = 0.03215 Pa／64.12 dB、E4 = 0.04011／66.04、B5 = 0.07714／71.72；44 音 **min 58.69（G5）／max 77.03（A3）／mean 68.90／spread 18.34 dB** ✅ 逐格相同 |
| V16 | §3.2 豎琴 78 音數字 | 重跑 `analyze_harp.py` | B0 = 56.73、E4 = 73.26、F7 = 30.27；78 音 min 21.85／max 82.05／mean 67.09 ✅ |
| V17 | §3.1 錄音 IFFT 交叉檢查與 ff−pp | 讀回 `guitar_recording_rms.json` | ff 61.67／62.21／70.45 dB，pp 52.03／50.77／56.88 dB，ff−pp **9.64／11.44／13.57 dB**；三檔 `SteadyPart` 皆 `[[0,0]]` ✅ 與 §5 第 3 點相符 |
| V18 | §3.3 引擎數字 | 用**現成** binary `build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe` 的既有 dump 重跑 `analyze_engine.py`（未重建、未渲染音訊） | piano C4 = 0.40932 Pa/N／86.22 dB、E4 = 0.32111／84.11、C5 = 0.20331／80.14；yangqin midi29 = 2.58571／102.23、midi56 = 1.43020／97.09、midi87 = 0.60585／89.63；`radius_m` 全為 1.05；`unsupported_observables` 含 `absolute_spl` ✅ 逐格相同 |
| V19 | §0-2 的程式碼引用 | 直接開 `src/physics/RadiationModel.h`（唯讀，未改） | `:291 static constexpr float kMeasurementRadiusM = 1.05f;`；`:285` 註解確實寫「`docs/EXTERNAL_ANCHOR_SOURCES.md` §1's 1.05 m anechoic-array convention」；`:246` 確實寫「it is a DECIDED CONVENTION」 ✅ §0-2 與 §4.2 的前提成立 |
| V20 | 附錄 B 署名段的作者名單與題名格式 | 查典藏記錄 `dc.contributor.author`；並在說明 PDF 內找到出版方自訂的引用格式 | 12 位作者姓名與順序完全相同；署名用的題名「Musical Instruments - A data base with recordings, directivities, and features of classical musical instruments」**就是說明 PDF 自己指定的引用格式**（非本文件自創） ✅ |

**本輪沒有動到**：`src/`、`tools/`、`scores/`、任何容差、任何 GATE 腳本、`build\`（只讀既有 exe 的既有輸出，未跑 cmake）。
**本輪唯一寫入的檔案**：本文件（新增此附錄 E）。`.gitignore` 與 `docs/EXTERNAL_ANCHOR_SOURCES.md` 的既有一行改動維持原樣，未再變更。

---

## §附錄 F：第三輪獨立重驗（2026-09-08，另一位 Opus，逐條自己重跑）

本輪同樣**不採信本文件既有的任何自報數字**，把 §2–§5 與附錄 A 的每一條可驗證主張自己再跑一次。
結論：**14 條主張逐條成立、零推翻**；新增 1 條更強的證據（W2）、修掉 2 個署名格式問題（見附錄 B 署名段）、
新記 2 個提醒（W8 的抽字陷阱、W15 的程式註解同源錯誤）。

| # | 重驗的主張 | 我怎麼驗（可原樣重跑） | 結果 |
|---|---|---|---|
| W1 | 附錄 A 的 7 個 SHA256 與位元組大小 | `python hashlib.sha256` 全檔重算（含 1.10 GB／2.62 GB 兩個壓縮檔，非抽樣），耗時 3.1 s | **7/7 逐字元相同**，大小 7/7 相同 |
| W2 | **（新增，本輪才做）** 本機檔＝典藏庫原檔？ | 典藏庫 bitstream API 每筆自報 `checkSum.value`（MD5）；本機 6 檔重算 MD5 對照：`0_Documentation.pdf` `3f64b828…a92d`、`1a…zip` `e1d201a6…9cf2`、`1b…zip` `18c10043…25e7`、`2_Acoustic_guitar…zip` `bae71e7f…462d`、`2_Double_action_harp…zip` `f2fe3ce5…af80`、`3_Audio_Features.csv` `c56740e9…90c3` | **6/6 MATCH**。`license.txt` 不在 ORIGINAL bundle、API 無校驗值，故只有 6 檔可對。→ 下載**未損毀、未被中途竄改** |
| W3 | §5 第 8 點的五個數字 | `GET https://api-depositonce.tu-berlin.de/server/api/core/bundles/8d6f2969-ee21-4fee-835a-dcecb28dd080/bitstreams?size=200` 重跑並重新加總 | `totalElements=50`；`2_` 開頭 **42**；扣掉已下載 2 個剩 **40** 個 = **51,163,473,525** 位元組；50 檔合計 **55,037,492,445** 位元組；非錄音 8 檔檔名（`0_Documentation.pdf`／`1a`／`1b`／`1c`／`1d`／`3_Audio_Features.csv`／`4_Pictures.zip`／`5_Tools.zip`）亦相同 ✅ |
| W4 | §2.1 判讀段的 discover API 分布 | `GET …/discover/search/objects?query=Musical%20Instruments%20directivities&dsoType=item` | `totalElements=437`；第一頁 20 筆＝`by/4.0/`×10、InC×6、`by-nc-sa/4.0/`×1、`by/3.0/de/`×1、`by-nc-nd/2.0/`×1、`by-nc-nd/3.0/de/`×1 → **CC 14／InC 6／空白 0** ✅ 完全相同 |
| W5 | E2：SOFA 的 `License` 屬性；以及吉他 44／豎琴 78 檔 | 用 h5py 直接從 `1a…zip` 內開 `Acoustic_guitar_modern_e2_singleTones.sofa` | `License = b'cc by-nc-sa 4.0'` ✅；`1a` 內共 **1469** 個 `.sofa`，吉他 **44**、豎琴 **78** ✅ |
| W6 | E9 與 §2.4 的 metadata | 同一次 dump 讀 `ReceiverPosition` 與全部 global attrs | `ReceiverPosition` 形狀 `(32,3)`、`Type='spherical'`、`Units='degree, degree, metre'`，**32 顆半徑唯一值 2.06**、Mic#04 = `[0.00, −10.81, 2.06]` ✅；`SOFAConventions=FreeFieldDirectivityTF`、`Version=2.1`、`DataType=TF`、`SourceTuningFrequency=443.0`、`Musician='Hanjo Maempel'`、`Reference='dx.doi.org/10.14279/depositonce-5861.3'`、`AuthorContact='david.ackermann@tu-berlin.de'`、`SourceManufacturer` 含「Masaru Kohno (1985) model "Concert"」、`Comment`＝部分音 RMS 聲壓（Pa）✅ 全部一致（補記一個本文未寫的欄位：`SOFAConventionsVersion=1.1`，與 `Version=2.1` 是兩個不同欄位） |
| W7 | E1／E6／E10 三句在說明 PDF 裡；以及 §5 第 9 點「PDF 沒有 63 Hz」 | PyMuPDF 重抽本機 `0_Documentation.pdf`（8 頁，SHA256 見 W1） | 「The database is provided under a Creative Commons BY-NC-SA licence」1 次、「a value of 1 corresponds to a pressure of 1 Pascal」1 次、「S1 = 54.63 m2」1 次 ✅；`cut-off` 0 次、`1070` 0 次、`63` 僅 1 次（＝54.63）、`anechoic` 3 次皆無頻率下限 ✅ |
| W8 | E5／E7／E8／E11／E12：arXiv 四句 | 重新取回 arXiv:2307.02110 全文 PDF（10 頁）並抽字 | 四句全部命中：「The data is available under the CC BY-SA 4.0 licence.」／「a digital amplitude of 1 corresponds to a pressure of 1 Pascal resp. a sound pressure level of Lp = 94 dB」／「pentakis dodecahedron with a diameter of 2.1 m」／「volume of approximately 1070 m3 and a lower cut-off frequency of fc = 63 Hz」✅。**同時 `CC BY-NC` 在 arXiv 全文命中 0 次**（佐證 §2.1 的 E5 判讀）。<br>**重跑陷阱（本輪新記）**：PDF 抽出的字含連字 `ﬀ`，直接搜 `cut-off` 會得到 0 命中而誤判「查無此句」；必須先把 `ﬀ/ﬁ/ﬂ` 正規化並移除斷行連字號再搜 |
| W9 | E3：JAES 摘要 | 重取 https://aes2.org/publications/elibrary-page/?id=22388 | 「The data is available under the CC BY-NC 4.0 license.」；作者 Ackermann／Brinkmann／Weinzierl，*JAES* **72(3):170–179，2024-03** ✅ |
| W10 | E4：典藏記錄的授權欄與作者 | `GET …/api/core/items/b194da8b-e98c-4761-9100-2b0bb6ba93e8` | `handle=11303/21058`、`dc.rights.uri=http://rightsstatements.org/vocab/InC/1.0/`、**`dc.rights` 欄不存在**、`dc.identifier.uri` 同時列 handle 與 `doi.org/10.14279/depositonce-19858`、作者 **12 位**且順序與附錄 B 署名段相同 ✅（補記：`dc.date.issued = 2017-04-10`，是典藏記錄的首次發布日，不是 Version 3 的日期） |
| W11 | §5 第 1 點：三個 DOI 的解析 | 逐個 `curl -L https://doi.org/…` 看最終 URL 與狀態碼 | `…-5861.3` → **404**；`…-5861.2` → 200 → item `50133366-…`，其 `handle=11303/6305.2` ✅；`…-19858` → 200 → item `b194da8b-…` ✅ 三條如文所述 |
| W12 | CC BY-NC-SA 4.0 三條款原文 | 重取 https://creativecommons.org/licenses/by-nc-sa/4.0/ | BY／NC／SA 三句與 §2.1 所引**逐字相同** ✅ |
| W13 | §3.3 引擎數字 | 用現成 binary `build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe` **重新 `--dump-modes`**（不是讀舊 dump），輸出到 `output/wf0907/R5/verify2/`，再重算平方和 | piano C4 `0.40932 Pa/N`／86.22 dB、E4 `0.32111`／84.11、C5 `0.20331`／80.14；yangqin midi29 `2.58571`／102.23、midi56 `1.43020`／97.09、midi87 `0.60585`／89.63；`radius_m` 全為 `1.05`；`unsupported_observables` 含 `absolute_spl` ✅ 逐格相同（未渲染音訊、未跑 cmake、未碰 `build\`） |
| W14 | §3.1／§3.2 的量測側數字 | 重跑 `analyze_guitar.py`、`analyze_harp.py` | 吉他 44 音 **min 58.69（G5）／max 77.03（A3）／mean 68.90／spread 18.34 dB**；豎琴 78 音 min 21.85／max 82.05／mean 67.09；三個代表音（E2 64.12／E4 66.04／B5 71.72；B0 56.73／E4 73.26／F7 30.27）✅ 逐格相同 |
| W15 | §0-2 與 §4.2 的程式碼引用 | 唯讀開 `src/physics/RadiationModel.h`（未改） | `:291 kMeasurementRadiusM = 1.05f`、`:285` 註解引「`EXTERNAL_ANCHOR_SOURCES.md` §1's 1.05 m anechoic-array convention」、`:246`「it is a DECIDED CONVENTION」✅。<br>**本輪新發現（記入 open_items，本卡不改 `src/`）**：同檔 `:249` 的註解寫「digital amplitude 1.0 corresponds to 1 Pa **at 1.05 m**, i.e. 94 dB SPL」並掛在 `EXTERNAL_ANCHOR_SOURCES.md` §1 名下——這正是 §2.2 指出的「1 Pa ≡ 94 dB」與「某個半徑」被焊在一起的**同一個錯誤，出現在程式註解裡**。§4.2 選項 X 若要做完整，這一行也要一起改（只改註解，不改數值 → 不觸發 R10） |
| W16 | 附錄 B 對 `license.txt` 的定性 | 直接讀本機 `license.txt` | 開頭即「DEPOSIT LICENSE (November 23rd 2015) — Agreement for the publication of research data on the institutional repository of TU Berlin」，內文是投稿者把權利授予 TU Berlin 圖書館 → **確為投稿者→典藏庫的合約，不是給使用者的授權** ✅ |

**本輪的判定**：§0 的兩個結論（**授權含 NC**、**量測半徑 2.06 m**）第三次獨立查證後**仍然成立**；
§3 的所有數字第三次重算後**逐格相同**；附錄 A 的檔案登記在本輪由「自我一致」升級為**與典藏庫原檔位元組相同**（W2）。

**本輪唯一寫入的檔案**：本文件（附錄 A 尾註一段、附錄 B 署名段兩處格式更正、以及本附錄 F）。
**本輪沒有動到**：`src/`、`tools/`、`scores/`、`.gitignore`、`docs/EXTERNAL_ANCHOR_SOURCES.md`、任何容差、任何 GATE 腳本；
`build\` 只讀既有 exe（跑 `--dump-modes`，不出聲音檔），未跑 cmake。
本輪產生的本機檔：`output/wf0907/R5/verify2/piano.json`、`output/wf0907/R5/verify2/yq.json`（皆在 gitignore 的 `output/` 下）。

---

## §附錄 G：複核修正記錄（2026-09-07）

> 本輪＝第四輪（引用複核員第二次提交 findings 後的修正回合，作業日 2026-09-08，卡建立日 2026-09-07）。
> 複核員提出 4 條 findings（1 blocker、1 major、2 minor），**逐條處理如下，全部照收，零反駁**。
> 沒有補進任何新的假來源：新增的兩個來源（E13／E14）都是我自己打 DepositOnce API 讀出來的，附完整 URL 與存取日期。

| # | 嚴重度 | 複核指出的問題 | 我怎麼改 | 我自己重驗的證據 |
|---|---|---|---|---|
| 1 | **blocker** | §4.2 選項 Y 寫「改 `kMeasurementRadiusM` → `radius_m` 與 `pressure_per_force` 兩欄都會變（差 5.86 dB）」，§4.0 詞彙表也寫「`pressure_per_force_*` 會隨 `radius_m` 一起變」。**與程式碼相反**：`pressure_per_force` 根本不隨半徑改變，5.86 dB 被套到了一個不適用的欄位上 | **兩處都改掉**。§4.0 詞彙表那一格改成「**它不會隨 `radius_m` 變**」並註明程式位置與「初版寫錯、已更正」；§4.2 選項 Y 的「影響」欄整格重寫成：音訊完全不變、只有 `radius_m` 那一欄的字從 `1.05` 變 `2.06`、**Pa/N 一個數字都不會變**；同時把 Y 真正的代價寫清楚（會弄紅一條測試、會讓輸出對不上以 1.05 m 記錄的標本檔），並**更正 R10 的定性**：嚴格說**不觸發 R10**（R10 針對音訊渲染結果改變），但仍必須另立卡。附帶把選項 X 補完整（加上 `RadiationModel.h:249` 那句也要改），並在 X 的「影響」欄改寫成「渲染輸出零改變、參數表零改變」 | 我自己唯讀開 `src/physics/RadiationModel.h`：`pressurePerForce(float physicsOnlyAmplitude)`（`:328-336`）**簽章與函式體都沒有半徑**，body 只有 `kPascalsPerUnitPhysicsAmplitude * physicsOnlyAmplitude`。全 repo `grep -rn kMeasurementRadiusM`（排除 `build\` 與本文件）在程式碼裡只有 **4 個位置**命中（`tests` 那條佔 533/534 兩行，是同一條斷言的敘述字串）：`RadiationModel.h:291`（定義）、`:306`（註解）、`src/score/ScoreRenderer.h:486`（把它當字串印進 `radius_m` 欄位）、`tests/physics_models_repro.cpp:533`（斷言它等於 1.05f）。`ScoreRenderer.h:478` 取 `paPerN` 時只傳 amplitude，`:503` 印出的 `pressure_per_force_real_pa_n` 與半徑無關。→ **複核員完全正確，我上一輪寫錯了。**（複核員只點出 :291/:306/:486 三處；我重跑 grep 時多命中測試檔那一處，正是 Y 的真代價之一。） |
| 2 | major | §4.1 選項 C 具名兩份外部資料集並斷言授權為 CC BY-SA 4.0，但**沒有 URL、沒有存取日期、沒有原文引述**，附錄 B 也沒有這兩筆 → 違反引用鐵律第 1 條（內容為真，缺的是標示） | **補齊標示**：選項 C 那一格改成指名 **E13／E14** 兩個代號，並在附錄 B 新增 E13、E14 兩列，各附 item uuid、API URL、人可讀 handle 頁、DOI、存取日期 2026-09-08、以及 `dc.rights.uri` 的原文引述；同時把「這兩份是什麼」寫白話（房間聲學模擬基準／喇叭陣列錄音） | 我自己打 `…/api/core/items/38410727-…` 與 `…/api/core/items/bf819762-…`：`dc.rights.uri` 皆為 `https://creativecommons.org/licenses/by-sa/4.0/`、`dc.rights` 皆空；handle 分別 `11303/7506.3`、`11303/16995.3`；DOI 分別 `10.14279/depositonce-6726.3`、`10.14279/depositonce-15774.3` ✅。**另補一個複核員沒提到的辨別點**：同關鍵字下還有一筆**論文**「A Benchmark for Room Acoustical Simulation. Concept and Database」（handle `11303/12452`）授權是 **CC BY-NC-ND 4.0**（含 NC）——BY-SA 的是**資料集**那一筆，不是論文，所以 E13 特地寫死 handle 與 uuid |
| 3 | minor | §0 給月月的結論仍夾雜未解釋的術語（`absolute_pressure_per_force`、`Pa/N`、`SOFA` 的 `ReceiverPosition` 欄位、`RadiationModel.h:291`），而白話詞彙表在 §4.0，月月會先讀到 §0 | **§0 第 2 點與對照數字段整段改寫成白話**：把「SOFA 檔的 `ReceiverPosition` 欄位」就地解釋成「資料檔裡記錄麥克風擺哪裡的那一欄」、把 `RadiationModel.h:291` 改成「我們程式裡一個叫『假設聽的距離』的數字」、把 `dB SPL` 就地解釋成「一般講多大聲的那個分貝」、把 `Pa/N` 就地解釋成「每施 1 單位力產生多少聲壓」、把 5.86 dB 的由來（離遠一倍小 6 分貝）講出來，並在段末指路 §4.0。**§4.0 詞彙表另補 4 個詞**：`SOFA 檔`、`ReceiverPosition`、`dB SPL / re 20 µPa`、`Pa／Pa/N` | 改後 §0 全段不再出現未就地解釋的英文術語；`absolute_pressure_per_force` 這個變數名已從 §0 移除（它在 §3.3 表格裡仍在，該處是技術段落並有表頭說明） |
| 4 | minor | §2.1 標題寫「四個來源，三種說法」，但表格是 **E1–E5 五列、四種說法**；第 72 行又寫「四份來源裡有三份含 NC」——只有默默把 E4 排除在外才自洽 | 標題改成「**五個來源（E1–E5），四種說法**」；結論句改成「**五份來源裡有三份（E1／E2／E3）明寫 NC**」並加一句把另外兩份交代掉（E4 完全沒給 CC、E5 是最舊的預印本說 BY-SA，**沒有任何一份說可以商用**）；判讀段的「E5 是**四者**中唯一沒有 NC 的」改成「五者中唯一給出不含 NC 的 CC 授權的一份」 | 逐列數過：E1(BY-NC-SA)／E2(BY-NC-SA 4.0)／E3(BY-NC)／E4(In Copyright)／E5(BY-SA 4.0)＝5 列 4 種；含 NC 者 E1/E2/E3＝3 列 ✅。**NC 結論本身未變**（只靠 E1/E2/E3，本輪未重跑但前三輪已各驗一次） |

**本輪沒有動到**：`src/`、`tools/`、`tests/`、`scores/`、`build\`（本輪連 CLI 都沒跑）、任何容差、任何 GATE 腳本、
`.gitignore`、`docs/EXTERNAL_ANCHOR_SOURCES.md`、`ROADMAP_PHYSICS.md`。
**本輪唯一寫入的檔案**：本文件（§0、§2.1、§4.0、§4.1、§4.2、附錄 B、本附錄 G）。
**§0 的兩個核心結論（授權含 NC、量測半徑 2.06 m）本輪沒有被推翻，也沒有改變**；
被推翻的是「改半徑會讓 Pa/N 一起變」這條**我自己上一輪寫的**推論。

---

## §附錄 H：第五輪獨立重驗（2026-09-08，第三位 Opus，全部自己重跑）

本輪的規則跟前三輪一樣：**不採信本文件任何自報數字，也不重用前幾輪留下的腳本**
（§3.1 的錄音 IFFT、吉他／豎琴 dB 表都是本輪自己重寫程式重算的，腳本 `output/wf0907/R5/audit5/v5_local.py`）。
結論：**§0 的兩個核心結論（授權含 NC、量測半徑 2.06 m）再度成立、零推翻**；
授權鏈、SHA256／MD5、API 數字、引擎數字**全部逐格相同**；
**找到 3 個先前沒抓到的小問題並已就地更正**（X5／X6／X7），另補 2 條先前缺標出處的 A 級引述（X4）。

| # | 重驗的主張 | 我怎麼驗（可原樣重跑） | 結果 |
|---|---|---|---|
| X1 | 附錄 A 的 7 個 SHA256、位元組大小，以及附錄 F 的 W2（本機檔＝典藏庫原檔） | 自寫腳本 `hashlib` 全檔重算 SHA256 **與** MD5（含 1.10 GB／2.62 GB 兩個壓縮檔，非抽樣），再對典藏庫 bitstream API 自報的 `checkSum.value` | **SHA256 7/7 逐字元相同**；大小 7/7 相同；**MD5 6/6 與典藏庫相符**（`license.txt` 不在 ORIGINAL bundle，API 無校驗值）✅ |
| X2 | 授權鏈 E1／E2／E3／E4／E5（NC 結論） | (a) PyMuPDF 重抽本機 `0_Documentation.pdf`（8 頁）；(b) h5py 直接從 `1a…zip` 內開 SOFA 讀 global attrs；(c) WebFetch `https://aes2.org/publications/elibrary-page/?id=22388`；(d) `curl …/api/core/items/b194da8b-e98c-4761-9100-2b0bb6ba93e8`；(e) `curl https://arxiv.org/pdf/2307.02110` 後自己抽字 | E1「The database is provided under a Creative Commons BY-NC-SA licence」命中 1 次 ✅；E2 `License = 'cc by-nc-sa 4.0'` ✅；E3「The data is available under the CC BY-NC 4.0 license.」＋ 作者 Ackermann／Brinkmann／Weinzierl、JAES 72、pp. 170–179、2024-03-06 ✅；E4 `dc.rights.uri = http://rightsstatements.org/vocab/InC/1.0/`、`dc.rights` 空、`handle = 11303/21058`、`dc.date.issued = 2017-04-10` ✅；E5「The data is available under the CC BY-SA 4.0 licence」命中 1 次、**`CC BY-NC` 在 arXiv 全文命中 0 次** ✅。**五份四說、三份含 NC 的結構完全不變** |
| X3 | §2.3 的半徑 2.06 m（E9／E10／E11） | 重讀 `ReceiverPosition`（`Type='spherical'`、`Units='degree, degree, metre'`、shape 32×3）；PDF 抽「S1 = 54.63 m2」；arXiv 抽「pentakis dodecahedron with a diameter of 2.1 m」 | 32 顆半徑唯一值 **2.06**、Mic#04 = `[0.00, −10.81, 2.06]` ✅；`√(54.63/4π) = 2.085 m` ✅；arXiv 原句命中 ✅。`20·log₁₀(2.06/1.05) = 5.855 dB`，§0 的「5.86 dB」正確 ✅ |
| X4 | **（本輪補標出處）** §3.1 那句「`1a` 是穩態段抽取」先前沒有引述來源 | 讀 `1a` SOFA 的 global attr `History` | 原文「The sound pressure of fundamental note and harmonics were extracted from the steady state of the original recording.」→ **A 級直接證據，已補進 §3.1** ✅。同時補進 §5 第 5 點的 Table 1 圖說原文「for the playing dynamics pianissimo (pp) and fortissimo (ff)」，用來釘死那兩欄的語意 |
| X5 | **（本輪新發現，已更正 §5 第 5 點）** Table 1 的吉他 pp 音域 C2–B5 | 逐檔讀 `2_Acoustic_guitar_modern_recordings.zip` 內 88 個 SOFA 的 `MIDINote` 與 `Description` | ff 44 檔＝**MIDI 40–83 連號**；**pp 也是 44 檔＝MIDI 40–83 連號**（＝E2–B5），**不是 Table 1 寫的 C2–B5**；`1a` 吉他 44 檔亦為 MIDI 40–83。→ Table 1 的 pp 欄與資料本身不符，**這是資料集的文件缺陷，不是我們讀錯** |
| X6 | **（本輪新發現，已更正 §3.2／§5 第 6 點）** 本文件三處寫豎琴 `1a` 音域「B0–F7」 | 逐檔讀 `1a` 內 78 個豎琴 SOFA 的 `MIDINote` | 實為 **MIDI 23–102（B0–F#7）**，中間只缺 24、26 兩號，共 78 檔。**最高音是 F#7 不是 F7**，本文件先前敘述有誤，已改。另記資料本身的異常：`F#7`(MIDI 102) 的 `N[0]` = **2993.95 Hz**，**低於** `F7`(MIDI 101) 的 3126.19 Hz |
| X7 | **（本輪升級，已更正 §5 第 3 點）** `SteadyPart` 全零，原文只寫「抽驗 12 個 ff 檔」 | 改成全檔普查：88 個吉他錄音 SOFA 全讀 | **88/88（ff 44 ＋ pp 44）的 `SteadyPart` 唯一值就是 0** → 主張由抽樣升級為全檔 ✅ |
| X8 | §3.1 吉他 44 音的 dB 表 | **自己重寫**（不呼叫 `analyze_guitar.py`）：`1a` 各音 Mic#04 的複數 TF 取模、對部分音平方和開根號、`20log₁₀(p/2e-5)` | E2 `0.03215 Pa／64.12 dB`（241 partials）、E4 `0.04011／66.04`（60）、B5 `0.07714／71.72`（20）；44 音 **min 58.69（G5）／max 77.03（A3）／mean 68.90**，全距 18.34 dB ✅ **逐格相同**；44/44 檔 `Description` 皆含 `dynamic = ff` ✅ |
| X9 | §3.2 豎琴 78 音的 dB 表 | 同上自寫程式 | B0 `56.73`、E4 `73.26`、F7 `30.27`；78 音 **min 21.85／max 82.05／mean 67.09** ✅ 逐格相同 |
| X10 | §3.1 的錄音 IFFT 交叉檢查（ff／pp 各 3 音） | **自己重寫** IFFT：依說明 PDF 式 (1) 由單邊 `XS` 造雙邊（`k=0` 與 `k=N/2` 不折半、`0<k<N/2` 折半、`k>N/2` 取共軛折半），`numpy.fft.ifft` 回時域後算 Mic#04 全訊號 RMS | ff `61.67／62.21／70.45 dB`、pp `52.03／50.77／56.88 dB`、**ff−pp = 9.64／11.44／13.57 dB** ✅ **與 §3.1 表逐格相同**。（重跑陷阱：`numpy.fft.ifft` 已含 1/N，**不可再乘 N**；乘了會整體高出 `20log₁₀(N)`≈97–101 dB） |
| X11 | §3.3 引擎數字與 `unsupported_observables` | 用**現成** binary `build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe` **重新** `--dump-modes` 兩首 score（未重建、未跑 cmake、未渲染音訊），輸出到 `output/wf0907/R5/audit5/`，再自寫程式重算平方和 | piano C4 `0.40932 Pa/N`／86.22 dB（40 partials，4 進表）、E4 `0.32111`／84.11（3）、C5 `0.20331`／80.14（2）；yangqin midi29 `2.58571`／102.23（29）、midi56 `1.43020`／97.09（6）、midi87 `0.60585`／89.63（1）；所有 `radius_m` 皆 `1.05`；`unsupported_observables` 確含 `absolute_spl` ✅ **逐格相同** |
| X12 | §4.2／§4.0 的程式碼主張（`pressure_per_force` 不隨半徑變） | 唯讀開 `src/physics/RadiationModel.h`、`src/score/ScoreRenderer.h`、`tests/physics_models_repro.cpp`、`tools/specimen_verify.py`；`grep -rn kMeasurementRadiusM src tests tools` | `RadiationModel.h:291` 定義 `1.05f`；`:285-290` 註解確實寫「`docs/EXTERNAL_ANCHOR_SOURCES.md` §1's 1.05 m anechoic-array convention」；`:249` 確實寫「1.0 corresponds to 1 Pa at 1.05 m, i.e. 94 dB SPL」；**`pressurePerForce()`（:328-336）函式體只有 `kPascalsPerUnitPhysicsAmplitude * physicsOnlyAmplitude`，完全沒有半徑** ✅；`ScoreRenderer.h:486` 只把它印進 `radius_m` 字串；`tests/physics_models_repro.cpp:533` 斷言等於 `1.05f`；`tools/specimen_verify.py:184` 拿 `radius_m` 當比對鍵 ✅ **附錄 G #1 的更正正確，§4.2 選項 Y 的代價敘述正確** |
| X13 | §5 第 8 點的五個數字、附錄 A 的 uuid／`sizeBytes` | `curl …/api/core/bundles/8d6f2969-…/bitstreams?size=200` | `totalElements = 50`；`2_` 開頭 **42**；扣掉已下載 2 個剩 **40 個＝51,163,473,525 位元組**；50 檔合計 **55,037,492,445 位元組**；非錄音 8 檔檔名相同；6 個已下載檔的 uuid 與 `sizeBytes` 全部相同 ✅ |
| X14 | §2.1 判讀段的 discover API 分布 | `curl …/discover/search/objects?query=Musical%20Instruments%20directivities&dsoType=item` | `totalElements = 437`；第一頁 20 筆＝`by/4.0/`×10、InC×6、`by-nc-sa/4.0/`×1、`by/3.0/de/`×1、`by-nc-nd/2.0/`×1、`by-nc-nd/3.0/de/`×1 → **CC 14／InC 6／空白 0** ✅ 完全相同 |
| X15 | §5 第 1 點：三個 DOI 的解析 | `curl -sL -o /dev/null -w "%{http_code} %{url_effective}"` 逐個實打 | `…-5861.3` → **404**；`…-5861.2` → 200 → item `50133366-e4a3-453d-8df6-cd577225a3d1`；`…-19858` → 200 → item `b194da8b-…` ✅ 三條如文所述 |
| X16 | §2.1 的 CC BY-NC-SA 4.0 三條款原文 | WebFetch https://creativecommons.org/licenses/by-nc-sa/4.0/ | BY／NC／SA 三句與 §2.1 所引**逐字相同** ✅ |
| X17 | ~~§5 第 4 點：資料集內找不到 `3_Audio_Features.csv` 的欄位定義表~~ **← 這一列的結論是錯的，2026-09-08 第六輪推翻，見附錄 I 的 Y1** | PyMuPDF 讀完 `0_Documentation.pdf` §3 全文；再看 CSV 表頭 | PDF §3 部分正確：§3 確實只給式 (2)(3)(4) 與「features were calculated using the TimbreToolbox」，沒有欄位對照表。**但「CSV 表頭確為 `features1,features2,…`」是只讀了第 1 列就下的結論——第 2 列才是真正的欄名列（133 個全部有語意，第 7 欄＝`SoundPower in dB`）。原主張不成立，已作廢** ❌ |
| X18 | E13／E14（§4.1 選項 C） | `curl …/api/core/items/38410727-…` 與 `…/bf819762-…` | 兩者 `dc.rights.uri` 皆 `https://creativecommons.org/licenses/by-sa/4.0/`、`dc.rights` 皆空；handle `11303/7506.3`／`11303/16995.3`；題名與 DOI 與附錄 B 所載相同 ✅ |

**本輪沒有動到**：`src/`、`tools/`、`tests/`、`scores/`、`.gitignore`、`docs/EXTERNAL_ANCHOR_SOURCES.md`、
`ROADMAP_PHYSICS.md`、任何容差、任何 GATE 腳本；`build\` 只讀既有 exe 跑 `--dump-modes`（不出聲音檔），**未跑 cmake**。
**本輪唯一寫入的 repo 檔案**：本文件（§3.1 補一句出處、§3.2 與 §5 第 3／5／6 點更正、以及本附錄 H）。
本輪產生的本機檔（皆在 gitignore 的 `output/` 下）：`output/wf0907/R5/audit5/v5_local.py`、`v5_local.json`、
`piano.json`、`yq.json`、`item.json`、`bs.json`、`disc.json`、`arxiv.pdf`。

---

## §附錄 I：複核修正記錄（2026-09-07）（第六輪，處理引用複核員的三條 findings）

> 複核員（另一位 Opus）親自打開檔案複核第五輪的成果，開出 1 blocker ＋ 2 minor。
> 三條全部處理完畢，逐條記錄如下。**本輪沒有新增任何外部來源，只有推翻一條自己先前的錯誤敘述。**

### Y1（blocker，已改）§5 第 4 點與附錄 H X17：`3_Audio_Features.csv` 的欄位定義

- **複核員指出的錯誤**：本文件寫「欄名是 `features1 … features133` 這種無語意佔位名」「資料集內找不到欄位定義表」
  「只能推測第 7 欄是聲功率級 `Lw`，未取得原文確認」——三句都與檔案本身相反；
  而附錄 H 的 X17 只讀了 CSV 第 1 列就把這個錯誤主張「複核通過」。
- **我自己重新查證（未採信複核員自報）**：用 `csv.reader` 讀 `external_data/tu_berlin_directivity/3_Audio_Features.csv`，
  逐列印出長度與內容。結果：全檔 **3,307 列**（第 1 列佔位名、第 2 列欄名、其後 **3,305 筆資料**），
  **每一列都是 133 欄**；**第 2 列的 133 個欄名沒有任何一個是空的**，全部有語意
  （開頭 `FILE, Label, Group, Era, Dynamic, Pitch, SoundPower in dB, TEE_Att, …`，
  結尾 `…, ERBgam_SpecCrest_median, ERBgam_SpecCrest_iqr`）。
  **第 7 欄（0-based index 6）的原文就是「SoundPower in dB」**（A 級直接證據，≤15 字原文引述，
  出處：該 CSV 第 2 列第 7 欄，2026-09-08 讀取）。第 3 列第 7 欄的值 `80.3351300125487` 與 dB 級聲功率完全對齊。
  另外 `Group` 欄的分布為 `Woodwind 1295／String 908／Brass 794／Plucked 256／Voice 52`，
  可再確認第 3 欄的語意確實是「樂器族」。
- **數值有沒有被改寫？沒有。** 我另外**自己重寫**反推腳本（`output/wf0907/R5/audit6/v6_radius2.py`，可原樣重跑）：
  直接從 `1a…zip` 內開 44 個吉他 SOFA，依說明 PDF 式 (3) 對 32 支麥克風取能量平均得 `L̄p`，
  取 CSV 中 44 筆 `Acoustic_guitar_modern_et_ff_*` 的 `SoundPower in dB` 當 `Lw`，
  以 `S1 = 10^((Lw − L̄p)/10)`、`r = √(S1/4π)` 反推，得
  **min 0.968 ／ max 1.674 ／ mean 1.262 m（n = 44）**——與本文件原本寫的 **0.97–1.67／1.26 逐格相同**。
  （用 `Data.Real` 與用 `Data.Real + i·Data.Imag` 的模，兩種算法結果到小數第三位完全一致。）
  同一支腳本也順手重驗了 §3.1 的吉他 SPL：**min 58.69 ／ max 77.03 ／ mean 68.90 dB**，
  以及 44 個檔的 `ReceiverPosition` 半徑唯一值 **2.06**，全部與本文件既有數字相同。
- **改了什麼**：
  1. §5 第 4 點刪掉那三句錯誤敘述，改寫成「第 1 列才是佔位名、第 2 列就是完整欄名列、第 7 欄白紙黑字寫 `SoundPower in dB`」，
     並明寫「**數值沒有被改寫，被改寫的只有『我們有多確定』這句話**」。
  2. 附錄 H 的 X17 那一列**標示為結論錯誤並作廢**（原標題加刪除線、結果欄由 ✅ 改為 ❌，並寫明錯在「只讀第 1 列」）。
  3. 連帶作廢第五輪回報 `open_items` 裡「欄位定義可能在未下載的 `5_Tools.zip` 裡」這條線索——**不需要下載它**。
     （§5 第 8 點仍照實列 `5_Tools.zip` 未下載，那句本身沒錯，只是不再是欄位定義的線索。）

### Y2（minor，不改檔、改為列入 open_items）`docs/EXTERNAL_ANCHOR_SOURCES.md` 還有兩處過期敘述

- **複核員指出**：該檔 §1 表格那一格已照卡改成「已下載子集」（合規），但同一份文件裡
  第 137 行「**本文件未下載任何資料檔。**」與第 227 行檢核項「`- [ ] 資料集未下載；BY-SA 授權與 repo 的相容性未評估——待月月裁決`」
  現在都是過期敘述；第五輪的 `open_items` 只提了「半徑 1.05 m」與「fc = 63 Hz」兩格，漏了這兩行。
- **我自己重新查證**：`grep -n` 該檔，兩行確實仍在，內容與複核員所述逐字相同。
- **處理方式：不改。** 本卡（`WF0907_R5_A8_dataset.md` §1 第 7 點）**只授權改 §1 表格那一格**，
  改這兩行會超出卡的範圍（違反共同規約 §1「只碰你這張卡列出的檔案」與「發現需要改別的檔案 → 記進 `open_items`」）。
  → **已補進本輪回報的 `open_items`，與原本那兩格併成同一條，交月月裁決是否另立卡一次修完。**

### Y3（minor，已改）§4.2 選項 X／Y 的儲存格太難讀

- **複核員指出**：§4.0 詞彙表沒有收錄 `kMeasurementRadiusM`、`tests/physics_models_repro.cpp:533`、
  `tools/specimen_verify.py:184` 這三個識別碼，X／Y 兩格卻直接丟出來；選項 X 那格還夾了一整句英文註解原文，
  是全文最難讀的地方，而這正好是月月要做選擇的那一格。
- **改了什麼**：
  1. §4.0 詞彙表**新增 4 列**白話解釋：`kMeasurementRadiusM`（＝存放「假設聆聽距離」的那個數字，目前 1.05）、
     「那條寫死 1.05 的測試」、「標本比對小工具」、「§1 的 1.05 m 消音室陣列慣例」（＝要更正的那句英文註解本身）。
  2. §4.2 的 X／Y 兩格改用白話重寫：X 改成「只改『說法』，一個數字都不動」並把三處要改的話逐條用中文說明；
     Y 改成「真的把那個距離從 1.05 改成 2.06」，把兩個副作用改寫成「那條寫死 1.05 的測試會亮紅燈」與
     「舊紀錄配不上新輸出」，識別碼全部退到 §4.0 詞彙表。
  3. §4.2 底下的建議段把「裁決常數」改成「我們自己拍板決定的一個約定」，
     並保留 ≤15 字原文引述「a DECIDED CONVENTION」與出處檔名（引用鐵律第 1 條）。
- **注意**：X／Y／Z 三個選項的**實質內容與代價一個字都沒有變**，只換了說法。

### 本輪的邊界

- **改到的 repo 檔案：只有本文件**（§4.0 新增 4 列、§4.2 的 X／Y 兩格與建議段重寫、§5 第 4 點更正、附錄 H X17 作廢、本附錄 I）。
- **沒有動**：`src/`、`tools/`、`tests/`、`scores/`、`.gitignore`、`docs/EXTERNAL_ANCHOR_SOURCES.md`、
  `ROADMAP_PHYSICS.md`、任何容差、任何 GATE 腳本。**未跑 cmake、未渲染任何音訊、未 `git add`／`commit`／`push`。**
- **本輪產生的本機檔**（在 gitignore 的 `output/` 下）：`output/wf0907/R5/audit6/v6_radius.py`、`v6_radius2.py`。
- **沒有新增任何外部來源**（`sources_count` 與第五輪相同）；本輪唯一新增的證據是**資料集自己檔案內的一句原文**。

---

## §附錄 J：複核修正記錄（2026-09-09，WF0908-P5）

> 卡：`docs/workcards/WF0908_P5_research_cleanup.md` §1 的兩列 R5。
> `docs/EXTERNAL_ANCHOR_SOURCES.md` 由 **WF0908-P4** 處理，**本輪一個字都沒碰**。

| # | finding | 處理 | 改到哪 |
|---|---|---|---|
| 1 | 附錄 B 署名區塊的**資料集標題**是編出來的書目字串 | **部分成立，已改**。本輪打開本機的 `0_Documentation.pdf` 逐字比對：那串題名**確實逐字出現在 PDF p.2 的「If you use this database, please cite:」區塊**，不是編的；但上一版**漏抄典藏編號 `5861`、並把 `DepositOnce:` 寫成 `DepositOnce,`**。已改成：(i) 先原樣照抄 PDF 的引用格式（附「抄自 p.2 哪個區塊」）、(ii) 再列本專案實際使用的版本（只換掉 404 的 DOI）、(iii) 新增一張表列出**三個並存的標題**（引用格式題名／PDF 封面題名／SOFA `DatabaseName`）各自的逐字原文與抄自何處，並警告 SOFA 的 `Title` 是單檔題名、不可當書目 | 附錄 A 下方的署名區塊 |
| 2 | §4.1 選項 C 的兩個 CC BY-SA 主張**無 URL、無引述** | **已改**。在 §4.1 建議段後新增「選項 C 的兩個候選：URL＋存取日期＋逐字原文」表，把 E13／E14 的 API URL、人可讀頁、DOI、`dc.rights.uri` 逐字值與**存取日期 2026-09-09** 全部寫進正文；並新增兩個但書：(a) 證據等級只到「典藏庫 metadata」，**本輪未下載這兩份資料核對檔內授權**，要用之前必須比照 §2.1 再查一次；(b) 兩份都不是樂器指向性資料 | §4.1 |

### 本輪自己重跑的查證（不是沿用上一版）

| 查什麼 | 怎麼查 | 結果 |
|---|---|---|
| 說明 PDF 的引用格式原文 | PyMuPDF 開 `external_data/tu_berlin_directivity/0_Documentation.pdf`，逐頁抽字，定位 `please cite` 在 **page index 1（＝ p.2）** | **逐字命中**，見署名區塊 (i) |
| 說明 PDF 的封面題名 | 同上，抽 page 0 | 「A Database of Anechoic Microphone Array Measurements of Musical Instruments / Recordings, Directivities, and Audio Features / Version 3」 |
| SOFA 的資料庫名與授權 | `zipfile` 解出 `1b_Directivities3rdOctave_SOFA/Acoustic_guitar_modern_3rdOctave.sofa`，`h5py` 讀 global attributes | `DatabaseName` = 封面題名；`Title` = 「Directivity measurement: Acoustic guitar modern」；`License` = 「cc by-nc-sa 4.0」；`Reference` = 「dx.doi.org/10.14279/depositonce-5861.3」 |
| E13／E14 的授權 | 自己重打兩支 DepositOnce items API（URL 見 §4.1 表） | 兩者 `dc.rights.uri` 都是 `https://creativecommons.org/licenses/by-sa/4.0/`，`dc.rights` 文字欄皆不存在——**與上一版記載一致** |

### 一個順帶發現（記錄，不改結論）

`0_Documentation.pdf` 的 **PDF metadata `title` 欄**寫的是
「Recordings of a loudspeaker orchestra with multi-channel microphone arrays for the evaluation of spatial audio methods」，
**與這份文件的實際內容無關**（那是 E14 那份資料集的題名，疑為同一個 LaTeX 模板留下的殘留）。
**本文件不採用 PDF metadata 的 `title` 欄當書目**，只採用封面與 “please cite” 區塊的可見文字。

### 本輪的邊界

- **改到的 repo 檔案：只有本文件**（署名區塊、§4.1、本附錄 J）。
- **沒有動**：`src/`、`tools/`、`tests/`、`scores/`、`docs/EXTERNAL_ANCHOR_SOURCES.md`（P4 的範圍）、
  任何容差、任何 GATE 腳本、§0–§3 的所有數字、附錄 A 的 SHA256 表。
- **未跑 cmake、未渲染任何音訊、未 `git add`／`commit`／`push`。**
- 動筆前備份在 `output/wf0908/P5/EXTERNAL_DATASET_A8.zh-TW.md`（gitignore 下）。
