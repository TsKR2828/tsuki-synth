# 水鑼 2.0× partial 缺口的物理分析

> 建立：2026-09-14　卡：`docs/workcards/WF0914_D13_gong_partial.md`（研究 lane，執行 Sonnet）
> **本文件不改任何程式碼、不改任何容差、不宣稱任何「模型與實測吻合」。**
> D13 原始登記見 `HANDOVER.md` §7（工作卡寫「TODO.md D13 原始登記」，但 `TODO.md` 本身
> 沒有以「D13」為標籤的條目；登記文字實際落在 `HANDOVER.md` §7——見本文件末「與卡文的落差」）：
> 「D13 水鑼引擎在 2.0× 無 partial 而真泰國鑼最強泛音在 2.000×（自由邊平板 vs 乳突鑼）」。
> 本文件的 §2（實測對照）大量沿用 WF0909-P6（Opus）已完成的量測，
> 已標明出處，不重複下載或重新分析 Iowa 音檔；§1（現況量化）與 §3（文獻歸因）為本卡新增。
>
> **修訂記錄（2026-09-14 稽核回合）**：稽核抓出三處錯誤，本次修訂已逐一修正並重新核證：
> (1) §2 對照表把「1.7384× 是引擎自己最強泛音」誤標成「第 2 弱」，與同段正文自相矛盾——
> 已改正為「第 2 根，亦為引擎最強」（重跑 `--dump-modes` 逐值核對）；
> (2) §3.1 誤稱文獻無 boss 鋼板鑼的模態序列與引擎「順序相同」——已用完整 Table 1 七模態
> Hz 值＋重跑 `--dump-modes` 逐值核對，改正為順序不同（`(1,1)`/`(4,0)` 對調，
> `PlateModel.h:204-205` 本身已註明此分支交叉）；
> (3) §3.1 鑼緣段引文頁碼誤標 p.106，已用 PyMuPDF 逐頁核對 PDF 頁尾字串改正為 p.105，
> 並補記原文 "less affect" 被逐字引用時靜默訂正為 "less effect" 一事。

---

## §0 一句話結論

水鑼引擎（`PlateModel`，自由邊 Kirchhoff 圓板）在 2.0× 基頻**確實沒有任何模態**——上下最近的
兩根分別低 242.66 音分（約 2.4 個半音）與高 263.39 音分（約 2.6 個半音），這不是捨入誤差，
是模態表結構性的空缺。真泰國鑼錄音（Iowa MIS）最強泛音落在 2.000× 的萬分之一以內（WF0909-P6
已量）。**兩者的落差有可追溯的物理成因**：乳突鑼的中央「boss」（乳突/凸起）對其鄰近的兩個
nodal-ring 模態有「質量負載」（mass loading）效應，文獻記錄這個效應可以把「第一、二個 nodal-ring
模態」拉近到八度（2:1）關係（McLachlan 1997，引用 Rossing & Shepherd 1982）；水鑼引擎模擬的
自由邊平板**沒有 boss、也沒有鑼緣（rim）**，結構上不具備這個機制，2.0× 附近沒有模態因此是
模型域（domain）的自然結果，不是計算錯誤。

---

## §1 現況量化（讀 `src/physics/PlateModel.h` 實際數字，本卡新算）

### 1.1 模態表來源

`PlateModel::freeEigenvalueForPoisson()`（`src/physics/PlateModel.h:230-262`）對自由邊
（completely-free）圓形 Kirchhoff 板，依材質 Poisson ratio 內插出 7 個特徵值 `omega[0..6]`，
對應模態 `(2,0) (0,1) (3,0) (1,1) (4,0) (2,1) (0,2)`（`m`=nodal diameters 數，`n`=nodal
circles 數）。這組數字本身的出處已在檔頭註解標明：「Leissa, Vibration of Plates, NASA
SP-160 (1969), Table 2.5」——但 nu=0.33 那一列**不是整列都是文獻值**：七個特徵值中 6 個
（`(2,0) (0,1) (3,0) (1,1) (2,1) (0,2)`）與 Table 2.5 完全一致，是文獻值；僅 `(4,0)`
一項（21.527217）是本專案依 Leissa eq.2.14（自由邊平板精確特徵方程式）從第一原理獨立
重解出的值——Table 2.5 印的 21.6 是 Leissa 自己標註「僅 2% 內為真」的大 n 漸近公式
（eq.2.15/2.16）近似值，不是精確解，`PlateModel.h:117-138` 檔頭註解已詳述這段換算與
兩次獨立重解的核對過程。nu=0.33 以外的列（其餘 Poisson ratio）則整組都是本專案對自由邊
平板特徵方程式重解出的 nu 插值表（同檔案 `M7 7c` 註解）。**本卡不重新驗證這組數字的
正確性**（那是 `PlateModel.h` 既有的 M7 卡工作），只讀出來算比值。（**R4 溯源精確化，
本輪稽核**：本卡前一輪把 nu=0.33 整列籠統稱為「文獻值」，高估了文獻背書的範圍，已如上
改正為「6/7 文獻值、(4,0) 為本專案重解值」。§1.3 用到的兩個關鍵鄰居模態 `(0,1)` 與
`(3,0)` 都在這 6 個與 Table 2.5 完全一致的文獻值之列，`(4,0)` 本身離 2.0× 還有
1241.23 音分，不是夾住 2.0× 的鄰居——這項精確化因此**不影響** §0／§1 的 2.0× 缺口
結論。）

模態頻率 `freq ∝ omega`（線性，`calculateModes()` 註解：「f ∝ lambda^2 = Omega (true
Kirchhoff plate dispersion)」），所以模態間的**頻率比值只取決於 `omega[i]/omega[0]`**，與半徑
`R`、厚度 `h`、材質剛度 `stiffness` 無關——這代表以下結論對**任何**尺寸的自由邊水鑼引擎音符
都成立，不是某個特定音高才有的巧合。

### 1.2 水鑼 score 實際用的材質

`scores/examples/water_gong_free.score.json` 的兩個事件都用 `"material": "bronze"`
（`plate_free_edge: true`）。`bronze` 的 Poisson ratio 在 `data/materials.json:22` 逐字為
`"poisson_ratio": 0.34`。以下用這個值計算。

### 1.3 比值與 2.0× 的音分差（本卡跑的腳本：`output/wf0914/D13/plate_mode_ratios.py`）

| 模態 (m,n) | omega (nu=0.34) | 頻率比 (÷基頻) | 與 2.000 的音分差 |
|---|---:|---:|---:|
| (2,0) 基頻 | 5.229136 | 1.000000 | −1200.00 |
| **(0,1)** | 9.090469 | **1.738427** | **−242.66** |
| **(3,0)** | 12.176775 | **2.328640** | **+263.39** |
| (1,1) | 20.525822 | 3.925280 | +1167.35 |
| (4,0) | 21.420716 | 4.096416 | +1241.23 |
| (2,1) | 35.236681 | 6.738528 | +2102.92 |
| (0,2) | 38.528075 | 7.367962 | +2257.52 |

完整命令與輸出見證據檔 `reports/gate_outputs/wf0914_D13_plate_ratios.txt`。

**確認**：2.0× 基頻夾在第 2 個模態 `(0,1)`（比值 1.738427，低 **242.66 音分**）與第 3 個模態
`(3,0)`（比值 2.328640，高 **263.39 音分**）之間，兩者都超過 2 個半音（100 音分/半音），
**這個區間內模態表完全是空的**。本卡另跑了 nu=0.33（§1.1 已精確化：`(0,1)`／`(3,0)` 這兩個
鄰居模態本身即為 Leissa Table 2.5 的文獻值，非本專案用的 bronze 0.34）做交叉檢查，結果同構
（−257.63／+262.04 音分），確認這不是 bronze 這個材質特有的巧合，
是自由邊平板特徵值序列本身的結構特徵：`(2,0)→(0,1)` 與 `(0,1)→(3,0)` 這兩段音程本來就不是
八度，不會因為換材質而剛好補上 2.0×（Poisson ratio 只在 0.20–0.49 之間內插，音分差的變動
幅度遠小於補齊 240+ 音分缺口所需要的量）。

> **與 WF0909-P6 數字的差異說明**：`docs/EXTERNAL_DATASET_SUPPLEMENT.zh-TW.md` §0／§2.2 記的是
> `--dump-modes` 對 C4/G4 兩個具體音符的**實際渲染輸出**（243／263 音分，整數四捨五入），
> 本卡是從 `PlateModel.h` 原始程式碼常數直接算比值（242.66／263.39 音分，未經 CLI 渲染管線）。
> 兩者一致到小數點後一位，差異純屬四捨五入與計算路徑不同（原始特徵值 vs 渲染後 FFT 讀值），
> **不是兩個不同的結論**，互相印證。

---

## §2 實測對照（沿用 WF0909-P6 已完成的量測，不重跑）

> 完整方法、逐組參數敏感度測試、授權原文、SHA256 見
> `docs/EXTERNAL_DATASET_SUPPLEMENT.zh-TW.md` §1.2／§2.2／§3（Iowa MIS 泰國鑼三包，
> 已於 2026-09-09 下載並逐字查證「may be downloaded and used for any projects, without
> restrictions」）。本卡只摘要與本卡結論直接相關的數字，**未重新分析音檔、未重新下載**。

**真泰國鑼（Iowa MIS，Andrew Thierauf 演奏，anechoic chamber，2013-03-20 器材表登記，
未校準絕對音量、可比頻率比值）**：

| 音 | Iowa 真鑼最強泛音比值 | 相對強度 | `water_gong` 引擎同音高最強泛音比值 |
|---|---:|---:|---:|
| C4 | **2.0001** | −6.49 dB（8 個泛音中最強） | 1.7384（第 2 根，亦為引擎最強） |
| G4 | **1.9999** | −14.67 dB（8 個泛音中最強） | 1.7384（第 2 根，亦為引擎最強） |

（WF0909-P6 §3 第 7 點記錄了參數敏感度測試：換窗函數、門檻、分析窗，2.000× 那根泛音的比值
穩定落在 1.9999–2.0002，且在每組乾淨設定裡都是最強泛音——不是分析參數挑出來的巧合。）

**對照結論**：真泰國鑼在 2.000× 有一個幾乎完美的八度泛音、而且是全曲最強的泛音；水鑼引擎
在同一位置（1.7384× 與 2.3286× 之間）**完全沒有模態**，引擎自己最強的泛音（1.7384×）在真鑼
錄音裡找不到對應強度的峰（C4 側該位置的峰弱 21.6 dB，G4 側弱 29.3 dB）。§1 的原始特徵值計算
與這裡的渲染後量測結果一致，確認缺口不是渲染管線的問題，是模態表本身的結構特徵。

---

## §3 物理歸因（文獻支撐）

### 3.1 找到並實際 fetch 到的文獻

**McLachlan, N. (1997). "Finite Element Analysis and Gong Acoustics," *Acoustics Australia*
25(3), 103–107.**（開放取用期刊，PDF 已於本卡 2026-09-14 實際 fetch 全文並逐頁讀取；
URL：`https://www.acoustics.asn.au/journal/1997/1997_25_3_McLachlan.pdf`）

這篇論文做了三組東西的頻譜比對：無 boss 的旋壓鋼板鑼（有鑼緣 rim）、有 boss 的旋壓鋼板鑼、
有 boss 的鑄造矽青銅鑼，並用 FEA 分別探討「boss 尺寸」與「鑼緣（rim）深度/角度」兩個幾何
特徵各自對模態頻率的獨立影響。

**逐字引文（p.103）**：
> 「a boss is a raised hemispherical dome in the centre of the gong's surface」
（boss 的定義：鑼面中央的半球形凸起——即水鑼登記文字裡說的「乳突」）

**逐字引文（p.103，材質認定）**：
> 「The third spectrum is of a gong which was cast with a boss in silica bronze」

**逐字引文（p.104，Fig.1 圖說）**：
> 「iii) Cast silica bronze gong (225 mm diameter ... 5 mm thick hemispherical boss)」

（**修訂記錄（本輪稽核）**：以上兩處確認 Table 1 那顆有 boss 的鑄造鑼材質是矽青銅
（silica bronze），不是磷青銅（phosphor bronze）。本卡前一輪四處誤稱「鑄造磷青銅鑼」，
已全部改正為矽青銅。「phosphor bronze」一詞出現在 p.105 正文的 FEA 模型材質參數句
（"Models used parameters for phosphor bronze (Young's modulus (Y) of 103 GPa, Poisson ratio (P)
of 0.34 ...)"）與 p.106 Figure 4 圖說（"...for phosphor bronze models based on the bronze gong
described in figure 1"）——兩處都是論文用有限元素法計算模態時的模型材質設定，
不是 Table 1 這顆實體鑼的材質，兩者不可混淆。）

**逐字引文（p.105，Discussion，緊接 Table 1 之後）**：
> 「Doubling the thickness of the boss slightly raises the frequencies of modes with nodal
> diameters, but lowers the frequency of modes with nodal rings, including the 1,1 mode.
> This may be attributed to increased stiffness for the former modes and increased mass
> loading for the latter. **A similar mass loading effect reported by Rossing [11] was
> proposed as the mechanism by which a boss could bring the first two modes with nodal
> rings into an octave relationship.**」

（**頁碼修訂（本輪稽核）**：本卡前一輪把這段標為「p.104–105」，經稽核重新下載 PDF 逐頁核對，
此段文字完整落在 p.105（頁尾字串「Vol. 25 (1997) No.3 - 105」出現在含此段文字的那一頁），
p.104 該頁沒有這段，已更正為單一頁碼 p.105。下方 §4 表格裡「McLachlan 1997 p.104-105」一項
指涉的是 Table 1 本身跨頁列印，不是這段逐字引文，維持原狀不動。）

（`[11]` 在該論文參考文獻表（p.107）為 T.D. Rossing and R.B. Shepherd, "Acoustics of
Gamelan Instruments," *Percussive Notes*, 19(3), 73–83 (1982)——本卡**未能取得這篇 1982
原始文獻的全文**，只取得 McLachlan 1997 對它的轉述，見 §3.3 缺口列表。）

**Table 1 的量測數字支持這句話**（p.104，鑄造矽青銅鑼一列，該鑼有 boss）：
第一個模態是 `(2,0)` 與 `(0,1)`（第一個 nodal-ring 模態）**簡併重合**在 298 Hz（比值 1）；
第二個列出的模態是 `(1,1)`（第二個 nodal-ring 模態）在 597 Hz，**比值 2.00，與「just ratio」
2/1 的偏差是 0%**——文獻自己量到的數字，就是「第一、二個 nodal-ring 模態」精確落在八度。

同一張表也記錄了**沒有 boss**（旋壓鋼板、但有 100 mm 深鑼緣）的鑼完整七模態頻率（p.104，
Table 1「Steel f(Hz)」列，本卡 2026-09-14 用 PyMuPDF 逐頁重抽 PDF 文字核對）：
`(2,0)`=252 Hz、`(0,1)`=422 Hz（比值 1.67）、`(3,0)`=498 Hz（比值 1.98）、`(4,0)`=622–662 Hz
（比值 2.47–2.63，本卡由 Hz 值直接算——表格另有一列 f/f(1) 比值在 PDF 文字抽取時因掃描
OCR 跨欄錯位，此處不採用該列，只信任 Hz 原始值與比值直接計算）、`(1,1)`=738 Hz（比值 2.93）、
`(2,1)`=984 Hz、`(0,2)`=1223 Hz——文獻表格欄位順序是
`(2,0)→(0,1)→(3,0)→(4,0)→(1,1)→(2,1)→(0,2)`。

**這個順序與水鑼引擎的實際順序不同，不是相同**：本卡重跑
`build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe --dump-modes
scores/examples/water_gong_free.score.json`，C4 的七個 partial 依實際輸出頻率排序為
261.626 / 454.817 / 609.232 / **1026.953**(3.9253×，(1,1)) / **1071.727**(4.0964×，(4,0)) /
1762.971 / 1927.647 Hz，即引擎順序是 `(2,0)→(0,1)→(3,0)→(1,1)→(4,0)→(2,1)→(0,2)`——`(1,1)`
與 `(4,0)` 這一對，引擎裡 `(1,1)` 先、文獻鋼板鑼裡 `(4,0)` 先，**順序對調**。這不是本卡的新
發現：`src/physics/PlateModel.h:204-205` 本身就有註解「Free-edge branches can cross as
Poisson ratio changes (notably (1,1)/(4,0))」，本卡的重跑只是拿實際 bronze（nu=0.34）數字
驗證了這個已知分支交叉確實發生，且與文獻旋壓鋼板鑼（有鑼緣，物理上是不同的邊界條件，
比值本來就不會一樣：引擎 (1,1)=3.9253×／(4,0)=4.0964×，文獻鋼板鑼 (4,0)≈2.47–2.63×／
(1,1)≈2.93×，量級都不同）方向相反——兩者除了同樣有「(1,1)/(4,0) 順序不固定」這個共通的
不穩定性之外，不能拿來互相印證比值。文中另段（Discussion，**p.105**，非 p.106——本卡以
PDF 頁尾逐頁核對：「Vol. 25 (1997) No.3 - 105」出現在含此段文字的那一頁）指出鑼緣（rim）
對兩類模態的影響方向不同：
> 「The frequencies predicted for modes with nodal diameters only (2,0, 3,0, 4,0 etc.)
> increase dramatically with the introduction of even a small rim due to increased
> stiffness in the plane of vibration... The introduction of a rim had less effect on the
> three modes with nodal circles shown in the figure.」
>
> （逐字核對備註：本卡 2026-09-14 重新 fetch 並用 PyMuPDF 抽取原文，PDF 原文此處實際作
> 「had less **affect** on」——原文本身的文法錯字（此處文法上應為名詞 effect），上面引文
> 已靜默訂正為 effect，特此誠實標注，不影響引文內容本身的意思。）

### 3.2 這對水鑼引擎意味著什麼（本卡的推論，非文獻直接陳述）

水鑼引擎的 `PlateModel`（`freeEdge=true` 分支）是**完全自由邊的平板**——沒有 boss（沒有中央
質量負載）、沒有鑼緣（沒有邊緣勁度增強）。文獻記錄的兩個能把特定模態對拉近八度關係的機制
（boss 造成的 nodal-ring 模態質量負載、rim 造成的 nodal-diameter 模態勁度提升）**在自由邊
平板模型裡都不存在**。這解釋了「為什麼引擎的模態序列結構性地沒有 2.0× 附近的模態」——不是
某個係數算錯，是模型的幾何假設（無 boss、無 rim 的裸平板）本來就不包含產生該八度關係的物理
機制。

**本卡誠實標注：以下是推論，不是文獻直接證明**——McLachlan 1997 研究的是印尼/爪哇風格鑼
（gamelan、tamtam），不是泰國乳突鑼；文中沒有針對泰國鑼的專門數據，也沒有明說「乳突鑼的
2.0× 泛音就是 boss 質量負載機制的產物」。本卡只能說：**同屬「boss+平板」構造的鑼類**，
文獻記錄了 boss 質量負載可以把特定模態對調到八度關係這個**機制的存在**，且量測數字
（Table 1 矽青銅鑼 0.00% 偏差的八度）與這個機制一致；把這個機制**直接套用到泰國鑼**是
合理的類比（同屬 boss+盤面構造），但不是逐字驗證。

### 3.3 查過但沒查到 / 查不到全文的文獻（誠實列）

1. **Rossing & Shepherd (1982), "Acoustics of Gamelan Instruments," *Percussive Notes*
   19(3), 73–83** — McLachlan 1997 的 `[11]`，本卡未找到可免費全文取用的來源，
   只有 McLachlan 對其結論的轉述（§3.1 已逐字引）。
2. **Rossing & Fletcher (1982), "Acoustics of a Tamtam," *Bull. Australian Acoustical Soc.*
   10(1), 21–25** — 同樣是紙本年代的期刊，本卡搜尋未找到可免費全文。
3. **「Acoustical and vibrometry analysis of a large Balinese gamelan gong,"
   *J. Acoust. Soc. Am.* 128(1), EL8**（`pubs.aip.org/asa/jasa/article/128/1/EL8/655833`）
   ——`docs/EXTERNAL_DATASET_SUPPLEMENT.zh-TW.md` §3 第 5 點已記錄 2026-09-09 曾嘗試、
   HTTP 403；本卡 2026-09-14 **再次嘗試，同樣 HTTP 403，未取得全文**。這篇的搜尋結果摘要
   （非全文，本卡**不引用**其任何具體數字）提到 Rossing & Shepherd 發現「兩個主要軸對稱
   模態」有接近 2:1 的頻率關係、且都在 boss 上有波腹（antinode）——**這個說法本卡只在
   搜尋引擎摘要層級看到，沒有 fetch 到原文逐字，依 R4／WF0914_README §2.3 不得引用其
   具體數字**，此處只記錄「查過、查不到全文」，不採用其內容作為結論依據。
4. **Iowa MIS 錄音的鑼本身是否確實有 boss（乳突）**——本卡 2026-09-14 重新 fetch Iowa
   `MISgongtamtams.html` 頁面，**頁面本身沒有任何關於鑼形狀/是否有 boss 的描述文字**
   （只有音名/力度的錄音列表）。「泰國鑼＝乳突鑼」是常識性/常見稱呼上的關聯（例如
   Wikipedia「Gong」條目有一張「Nakhon Nayok 佛寺乳突鑼」的照片說明，`en.wikipedia.org/
   wiki/Gong`，本卡 2026-09-14 fetch 確認頁面文字「Bossed or nipple gongs have a raised
   centre boss or knob」「Nipple gongs at Wat Chulaphonwararam...Nakhon Nayok」），
   但**這不是對 Iowa 錄音那個特定樣本的直接驗證**——本卡沒有 Iowa 那顆鑼的照片或器材描述
   可以確認它有 boss。這是繼承自 D13 原始登記與 WF0909-P6 的既有假設，**本卡未能獨立驗證**，
   誠實列為缺口。

---

## §4 誠實標注表（哪些是文獻、哪些是推測）

| 陳述 | 等級 |
|---|---|
| 水鑼引擎自由邊平板在 2.0× 附近無模態，最近兩根低 242.66c／高 263.39c | **本卡實算**（§1，程式碼常數直接算） |
| 真泰國鑼（Iowa 錄音）最強泛音在 2.000×（C4/G4 各自 ≤0.0002 的比值誤差） | **WF0909-P6 實測**（本卡沿用，未重跑） |
| boss 的質量負載效應可把「第一、二個 nodal-ring 模態」拉近八度關係 | **文獻逐字引用**（McLachlan 1997 p.104-105，含 Table 1 實測數字） |
| 自由邊平板（無 boss、無 rim）結構上不具備上述機制，因此 2.0× 附近無模態是模型域的自然結果 | **本卡推論**（由前兩項邏輯推出，非文獻直接陳述） |
| McLachlan 1997 的機制可以直接套用解釋「泰國乳突鑼」的 2.0× 泛音 | **類比推論，非逐字驗證**（McLachlan 研究印尼鑼，非泰國鑼；Rossing & Shepherd 1982 原文未取得） |
| Iowa 錄音的那顆鑼確實是乳突鑼 | **未獨立驗證的既有假設**（繼承自 D13 登記，Iowa 網頁本身無描述） |

---

## 與卡文的落差（誠實記錄，不影響結論）

卡文寫「先讀：`TODO.md` D13 原始登記」，但 `TODO.md` 全文搜尋不到以「D13」為標籤的條目；
D13 的登記文字實際位於 `HANDOVER.md` §7（見本文件開頭）。文字內容與卡文 §0 描述完全一致
（自由邊平板 vs 乳突鑼、2.0× 缺失），**不影響本卡執行**，只是卡文標註的檔案位置與 repo 現況
不符，依規約記錄於此，未停工。
