# A13 裁決包 — partial（泛音）GATE 的主張域

> 產出：2026-09-08（工作卡 `docs/workcards/WF0907_R1_A13_partial_gate.md`，
> 卡上標示的日期為 2026-09-07，本輪實際執行跨日到 2026-09-08；**所有外部來源的存取日期一律 2026-09-08**）
> 分支 `fix/deep-physics-audit-20260716`　執行：研究 lane（Opus）
> 對象：`TODO.md` A13 —— 要不要立 partial GATE、主張多強、容差多少
> 依據：`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.4 第 1 點
>
> **本文件只提供外部證據、引擎數字與各選項代價，不替月月做決定。**
> **本輪未改任何 `src/` `tools/` 檔案、未 build、未 commit；只跑了唯讀的 `--dump-modes`。**

---

## 0. 白話導讀（先讀這段就夠做決定）

一句話結論：**partial 的「頻率」可以立 GATE 而且不必發明新容差；partial 的
「振幅」外部世界自己都量不準，現階段立振幅 GATE 只會做出一盞假綠燈。**

**先講兩個從頭用到尾的單位／術語（沒有樂理或統計背景也看得懂）：**

- **cents（音分）** = 衡量「兩個音高差多遠」的尺。鋼琴上相鄰兩個鍵（一個半音）
  = **100 cents**。所以本文件常出現的 **±5 cents 大約是一個半音的二十分之一**，
  是很小的音高差；**0.99 cents 更小，約一個半音的百分之一**。
- **RMS** = 一堆誤差值的「平均大小」（先平方再開根號，所以正負誤差不會互相抵銷、
  不會假性變好看）。「RMS 0.99 cents」的意思是：那一組泛音的誤差**平均起來**
  大約是 0.99 cents。旁邊常一起寫的「最大 1.82 cents」則是那組裡**最糟的那一個**。
  **算 RMS 時「分母是幾筆」很重要**：只算看得清楚的那幾筆，跟把看不清楚的那幾筆
  當成「誤差 0」一起算，後者會讓數字假性變好看。本文件一律採前者（見 §2.2-A2 的註）。

再講白一點，用三層說明：

1. **什麼是 partial？** 敲一根琴弦，它不是只發出一個音高，而是同時發出一疊
   頻率——最低的那個叫基頻，上面那些叫泛音（partial）。鋼琴弦有硬度，所以
   泛音不是基頻的整數倍，而是被推高一點點，這個「被推高多少」用一個數字 `B`
   描述。這是鋼琴聽起來像鋼琴的關鍵之一。

2. **頻率好辦。** 1964 年 Fletcher 那篇 JASA 論文，在一台真鋼琴上逐一量了
   partial 的頻率，並拿理論公式去對，**在高音實心弦上理論與實測的差距只有
   RMS 0.99 cents、最大 1.82 cents**（本文件 §2.2-A2 依該論文 Table VI 原始數字
   自行換算，只取掃描檔上看得清楚的 6 筆）。也就是說「partial 頻率」在學界是一個**量得準、對得上**的東西。
   TsukiSynth 用的公式（`f_n = n·f₁·√(1+B·n²)`）跟那篇論文、跟 2013 年
   Rigaud 那篇 JASA、跟 2020 年 Aalto 大學那篇 Applied Sciences 用的
   **是同一條公式**，不是自創的。

3. **振幅很麻煩。** 泛音「有多大聲」取決於琴槌、擊點、三根弦互相耦合、
   響板共振、麥克風擺哪裡——**2025 年**一篇用最新神經網路做鋼琴模擬的論文
   （§2.3-B3），自己在摘要裡承認**「預測頻譜高頻部分的能量比較有挑戰性」**。
   本文件在振幅這一側查到的**最新一篇就是這篇 2025**（本文件唯一的 2026 年
   **物理**來源 §2.4-C1 談的是頻率比值、不是振幅，而且方法學不足，見 §5-K6；
   另有一條 2026 年來源 §2.5-D2，但那是**社群**貼文，不是物理證據）。
   連 2025 年的最新研究都還卡在這一關，我們沒有理由現在就宣稱「泛音振幅已驗證」。

**兩個要一起知道的事實（都是本輪跑出來的數字，不是猜的）：**

- **好消息**：TsukiSynth 的泛音頻率公式與文獻一致，而且引擎自己會輸出
  預測值（`--dump-modes`），所以「渲染出來的聲音有沒有照自己的模型走」
  這件事**可以驗、而且不用發明新容差**（沿用現行 ±5 cents 那把尺即可，
  理由見 §4-B）。
- **壞消息（請注意，這條會影響 A14）**：把引擎預測的 `B` 拿去跟真鋼琴比，
  **A4 高 2.46 倍、G5 高 2.44 倍、F♯6 高 5.01 倍、G6 高 5.17 倍、D7 高 5.39 倍**
  （**F♯6 與 D7 是 2026-09-08 第四輪新增的兩顆**，見 §3.2／§3.3；本文件其他地方把
  這個範圍寫成「2.4～5.4 倍」，指的就是這五個數字）。原因已經查清楚了：**引擎的弦
  比真鋼琴短（只有 72～83%），而且本 corpus 的 score 把所有音的弦徑都寫成
  1.0 mm**（真鋼琴由 0.99 mm 一路變細到 0.79 mm）。這兩件事合起來剛好精準
  解釋那五個倍數（§3.3 有逐項驗算，誤差 <0.5%）。
  **但是——修這個會改變所有既有渲染輸出，直接觸發 Rule 10，所以本輪
  只報告、不動手。**
- **第四輪新增的第三件事**：引擎的 `B` 在 **F♯6／G6／D7 三顆都超出文獻所述的
  典型上界 10⁻²**（A3，Rigaud 2013：`B` 典型範圍 [10⁻⁵, 10⁻²]），
  分別是 1.54×10⁻²／1.73×10⁻²／3.88×10⁻²。原先文件只發現 G6 一顆超界。

因此建議（詳見 §4）：**選 B+，也就是「只驗 partial 頻率的內部一致性」＋
「另外寫一份不當 GATE 的文獻對照報告」**。理由：頻率驗得起來，而弦幾何
那條偏差如果直接綁進 GATE，卡片一開就是紅燈，而唯一的解法要動引擎 → R10。

---

## 1. 問題

`stem_verify` 目前只驗基頻與起音；`--dump-modes` 給出的 partial 只被拿來
**預判**「別顆音的泛音會不會污染基頻帶」，**從來沒有實測過任何 partial 的
頻率或振幅**（`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.4 第 1 點）。
所以現在**不可以**宣稱「泛音已驗證」。

要決定的是：

- 要不要立 partial GATE？
- 主張要多強：只驗頻率？連振幅一起驗？
- 容差多少——**而且 R2 明訂新容差不可由工程端自訂**，所以容差的出處必須
  來自外部（文獻量測精度）或既有已裁定的門檻，不可以是我們自己挑一個好過的數字。

---

## 2. 外部證據表（分級）

### 2.1 分級說明

| 級別 | 意義 |
|---|---|
| **P1 物理證據** | 同儕審查論文／教科書／量測報告的原文數字，本輪親自打開原文核對 |
| **P2 物理證據（僅摘要）** | 只取得摘要或索引頁，原文付費牆／403 |
| **C 社群證據** | 論壇／使用者討論 —— **只能當「使用者觀感／需求證據」，不是物理證據** |

> 存取日期一律 **2026-09-08**。凡標「未取得原文」者，其內容不得用於任何數字主張。

### 2.2 A 組：學界怎麼量 partial 頻率與 `B`、精度多少

| # | 出處 | 級別 | 關鍵數字 | ≤15 字原文引述 |
|---|---|---|---|---|
| A1 | Fletcher, H. (1964). *Normal Vibration Frequencies of a Stiff Piano String*. JASA 36(1), 203–209. 全文 PDF：<http://www.jbsand.dk/div/StivStreng.pdf>（掃描版，本輪逐頁轉圖親自判讀） | **P1** | ① **量測誤差**：低階 partial 的變異可由 **0.2～0.3 cps 的觀測誤差**解釋；② **`B` 的精度**：pinned／clamped 兩種邊界推得的 `B` 差距「不比觀測誤差大多少」，**最高音 key 78 為 10%、key 58 以下小於 4%**；③ **分析器通帶只有 4 cps 寬**；④ 逐弦實測 `B`：key 31（≈E♭3，f₁=152.8 Hz）**B=0.000444**；key 59（**=G5**，f₁=776.7 Hz）B 欄平均 **0.00167**（見 §5 已知缺口 K1 的印刷不一致警告） | 「an observational error of 0.2 or 0.3 cps will account for the variation」（p.207） |
| A2 | 同上，Table VI「Comparison of calculated and observed values of partial frequencies」 | **P1** | 剛性弦模型 vs 實測的一致度（本文件自行換算為 cents，**只取掃描檔上 calc/obs 兩欄都看得清楚的列**）：**實心弦 No.54（f₁=581.5 Hz）6 組（n=5,6,7,9,10,11）：RMS 0.99 cents、最大 1.82 cents**；**纏繞低音弦 No.23（f₁=97.3 Hz）14 組（n=5,6,9–20）：RMS 3.81 cents、最大 10.92 cents**（見下方註） | 「how close the calculated values of the frequencies agree with those observed」（p.209，Table VI 的說明句） |
| A3 | Rigaud, F., David, B., Daudet, L. (2013). *A parametric model and estimation techniques for the inharmonicity and tuning of the piano*. JASA 133(5), 3107. 作者自存 PDF：<https://www.institut-langevin.espci.fr/IMG/pdf/2013_a_parametric_model_and_estimation_techniques_for_the_inharmonicity_and_tuning_of_the_piano.pdf> | **P1** | ① **`B` 的典型範圍 [10⁻⁵, 10⁻²]**；② **`B` 估計精度**：NMF 法相對真值平均偏差 **合成音 0.33%、真實音 0.76%**；PFD 法 **0.78% / 3.3%**（評估區間 A0–G3）；③ 用的公式與 TsukiSynth 相同：`f_n = n F₀ √(1+Bn²)`、`B = π³Ed⁴/(64TL²)`；④ 調音伸展：中音區 ±5 cents，低音到 −30、高音到 +30 cents | 「typical values for B are in the range [10−5, 10−2]」（Sec. II.A） |
| A4 | Hodgkinson, M., Wang, J., Timoney, J., Lazzarini, V. (2009). *Handling Inharmonic Series with Median-Adjustive Trajectories*. DAFx-09, Como. 全文 PDF：<https://www.dafx.de/paper-archive/2009/papers/paper_94.pdf> | **P1** | Table 1：64 次分析的 **RMS error —— PFD 0.001067、MAT 0.00049268**（`B` 估計的 RMS 誤差）；並指出鋼琴鍵盤上端非諧性急遽上升 | 「the dramatic inharmonicity increase towards the upper end of the piano keyboard」 |
| A5 | Tuovinen, J., Hu, J., Välimäki, V. (2019). *Toward Automatic Tuning of the Piano*. SMC 2019, 143–150. 機構庫頁：<https://research.aalto.fi/en/publications/toward-automatic-tuning-of-the-piano/>（PDF 檔本身 403，**未取得原文全文**，數字取自該頁摘要） | **P2** | 半自動調音系統與**專業調音師的差距：A0–G5 為 2.5 cents (RMS)、G♯5–C8 為 8.1 cents (RMS)**，並指出高音區「調音師本身也不太一致」 | 「deviations of 2.5 cents (RMS) for keys A0–G5 and 8.1 cents (RMS) for G#5–C8」（機構庫摘要頁） |
| A6 | Rauhala, J., Lehtonen, H.-M., Välimäki, V. (2007). *Fast automatic inharmonicity estimation algorithm*. JASA 121(5), EL184. <https://pubs.aip.org/asa/jasa/article/121/5/EL184/538552/> | **P2** | 出版社 **403，未取得原文**。其精度由 A3 轉述（PFD：合成 0.78%、真實 3.3%）——**該數字以 A3 為出處，不以本條為出處** | 未取得原文 |
| A7 | Fletcher, H. *Errata: Normal Vibration Frequencies of a Stiff Piano String*. JASA 36, 1214 (1964). <https://ui.adsabs.harvard.edu/abs/1964ASAJ...36.1214F/abstract> | **P2** | **未取得原文**。存在勘誤這件事本身與 §5 K1 的印刷不一致有關，列出以供追查 | 未取得原文 |

> **A2 的 RMS 計算方式（2026-09-07 第二次複核更正）**：Fletcher 1964 Table VI 是掃描檔，
> 有幾列的 obs 欄糊掉（String No.54 的 n=4、n=8；String No.23 的 n=4、n=8），另有幾列原文本來就沒有 obs
> （兩根弦的 n=1–3；String No.54 的 n≥12 該欄未列）。
> **先前版本把「糊掉／沒有 obs」的列當成誤差 0 一起除**，得到「8 個 partial RMS 0.86」與「16 個 partial RMS 3.85」——
> 這會讓一致度**假性變好看**，而且 3.85 連用該方式也復現不出來（補零到 16 組只得 3.565）。
> 本輪改為**只算兩欄都可判讀的列**，並把筆數寫出來：
> No.54 = 6 組 → RMS **0.99** cents／最大 **1.82** cents；No.23 = 14 組 → RMS **3.81** cents／最大 **10.92** cents。
> 換算式 `cents = 1200·log₂(obs/calc)`，逐筆數字在 `output\wf0907\R1\r1_numbers_addendum.txt`。
> **對結論無影響**：0.99 cents 仍遠優於 §4-B 要沿用的 ±5 cents 門檻。

### 2.3 B 組：partial 振幅為什麼難

| # | 出處 | 級別 | 關鍵數字 | ≤15 字原文引述 |
|---|---|---|---|---|
| B1 | Fletcher, H., Blackham, E. D., Stratton, R. (1962). *Quality of Piano Tones*. JASA 34(6), 749–761. **作者機構自存全文 PDF：<https://physics.byu.edu/download/publication/1504>**（BYU 物理系 Fletcher 著作頁 <https://physics.byu.edu/department/publications/fletcher> 的連結；2026-09-08 追補時取得全文，見文末「追補記錄」。出版社頁 <https://pubs.aip.org/asa/jasa/article-abstract/34/6/749/600921/> 仍為 403） | **P1（2026-09-08 由 P2 升級）** | ① 摘要（p.749）：泛音電平隨頻率**每升高 100 cps 下降 2 dB** 時音質最好；中央 C 以下的泛音必須非諧才像鋼琴；② **partial 頻率量測精度（p.752）：電子計數器精度約 0.1%，換算 ≈ 1.73 cents**（`1200·log₂(1.001)=1.730`）——**2026-09-07 第二次複核更正：先前誤寫「≈17.3 cents、遠差於 A1/A2」，那是 1% 的值（`1200·log₂(1.01)=17.23`），差了十倍**；正確的 1.73 cents 與 A1/A2 是**同一量級**，因此**不能**用它論證「年代越早精度越差」；③ **唯一查到的「振幅偏多少才有差」數字（p.761）：第五、六個以上的單一 partial 整個拿掉都察覺不到；但把它抬高 4～5 dB 就明顯聽得出來**——**這是聽感門檻，不是量測精度，本專案不採信聽感（見 §4 選項 C）**；④ p.761 給三個受測音的「像鋼琴」振幅斜率**可接受區間**（**音名寫法說明——2026-09-09 補註，同日第二次引用複核再修**：掃描檔文字層裡這三個音名**沒有一個是乾淨的**。p.761 結語句逐字為 `The midpoints on the limits of G", G, and G` + **U+FFFD**（抽字層抽不出的替換字元）+ `E. are, respectively, 2, 8, and 32 db per partial`；三個小節**標題**逐字則是 `Tone G"`／`Tone Cs`／`Tone G` + **U+FFFD** + `E.`。也就是說：**第三個音名在結語句與小節標題都是殘字，中間那個小節標題另外被 OCR 讀成 `Cs`**。本列以下寫的 **G″／G／G₂** 是**本文件自訂的正規化寫法，不是文字層原樣**；三組數字與三個音名的對應以結語句的順序為準——結語句的中點 2／8／32 dB 依序對上三個小節的 2.5→1.5／13.0→5.0／40→7.5 dB/partial，**不以小節標題為準**）：G″ **2.5→1.5** dB/partial、G **13.0→5.0** dB/partial、G₂ **40→7.5** dB/partial，三者中點分別為 **2／8／32** dB/partial。**2026-09-07 第二次複核更正：先前把音名誤寫成「G♭ 音」「C♯ 音」（原文無此二音），並把區間寬度寫成「5～32 dB」（原文無此數字）**；三個區間的實際**寬度**是 **1.0／8.0／32.5 dB** | 「decrease in level at the rate of 2 db per 100-cps increase」（p.749 摘要）<br>「measure frequency with an accuracy of about 0.1%」（p.752）<br>「A single partial above the fifth or sixth could be eliminated」（p.761）<br>「raised 4 or 5 db from its position in the series, it was distinctly noticeable」（p.761）<br>「Piano-like quality had limits from 40 to 7.5 db per partial」（p.761；該小節標題在文字層作 `Tone G`+U+FFFD+`E.`，非本文件寫的 G₂）<br>「The midpoints on the limits of G", G, and」（p.761 逐字，直引號；緊接其後的第三個音名在文字層是 U+FFFD 殘字，**引述在此截斷、不補寫**） |
| B2 | Shah, S., Välimäki, V. (2020). *Automatic Tuning of High Piano Tones*. **Applied Sciences 10(6), 1983**（開放取用）。全文 PDF：<https://pdfs.semanticscholar.org/2e4e/f5be26f612b18ef5aee96a4ff2b117b2e8fc.pdf> | **P1** | ① 高音區「**第三個 partial 之後每個 partial 振幅都極低、可以忽略**」；② 聽測結果：**對齊第一組 partial（m1）評分 75.0，比專業調音師 68.7 還高**；③ Railsback 曲線在高音區的差異圖縱軸達 ±60 cents；④ 用的公式同樣是 `f_n = n f₀ √(1+Bn²)` | 「beyond the third partial, every partial is of very low amplitude」（Sec. 5） |
| B3 | Simionato, R., Fasciani, S. (2025). *Sines, transient, noise neural modeling of piano notes*. **Frontiers in Signal Processing 4**, DOI 10.3389/frsip.2024.1494864（開放取用）：<https://www.frontiersin.org/journals/signal-processing/articles/10.3389/frsip.2024.1494864/full> | **P1** | 2025 年最新的可微分頻譜模型，摘要自承：模型能對上目標的 partial **分布**，但**預測頻譜高頻部分的能量比較有挑戰**；感知測驗顯示起音段建模仍有限制 | 「predicting the energy in the higher part of the spectrum presents more challenges」（摘要） |
| B4 | Ege, K., Boutillon, X. (2010). *Vibrational and acoustical characteristics of the piano soundboard*. ISMA 2010 / arXiv:1212.3068：<https://arxiv.org/pdf/1212.3068> | **P1** | 直立鋼琴響板：**模態密度 0.05～0.01 modes/Hz**、平均損耗因子 **約 2%**、**550 Hz 以下平均模態間距約 22 Hz**；線性響應比非線性成分高 **至少 50 dB** | 「The modal density of the spruce board varies between 0.05 and 0.01 modes/Hz」（摘要） |
| B5 | Weinreich, G. (1977). *Coupled piano strings*. JASA 62(6), 1474–1484. <https://pubs.aip.org/asa/jasa/article-pdf/62/6/1474/11470322/1474_1_online.pdf> | **P2** | 出版社 **403，未取得原文**。索引頁摘要層級可知該文處理琴橋導納造成的弦間耦合、拍音與 aftersound（雙衰減）。**本文件不引用其任何數字** | 未取得原文 |
| B6 | Conklin, H. A. (1996). *Design and tone in the mechanoacoustic piano. Part III*. JASA 100(3), 1286–1298. <https://pubs.aip.org/asa/jasa/article-abstract/100/3/1286/558293/> | **P2** | 付費牆，**未取得原文**。摘要層級：鋼琴音中存在「phantom partials」（縱向模態產生的額外譜峰），其與正常 partial 的頻率關係隨非諧性而變 | 未取得原文 |
| B7 | Anderson, B. E., Strong, W. J. (2005). *The Effect of Inharmonic Partials on Pitch of Piano Tones*. JASA 117, 3268–3272. 機構庫頁：<https://scholarsarchive.byu.edu/facpub/1002>（PDF 連結 403，**只取得摘要**） | **P2** | 摘要指出他們對九顆真鋼琴音做了「frequencies, relative amplitudes, and decay rates of their partials」的分析；非諧性造成的**感知音高上移由低音約 2.5 個半音到高音約 1/8 半音** | 「pitch increase ranged from approximately two and a half semitones」（摘要） |
| B8 | Simionato, R., Fasciani, S., Holm, S. (2024). *Physics-informed differentiable method for piano modeling*. **Frontiers in Signal Processing 3**, DOI 10.3389/frsip.2023.1276748（開放取用）：<https://www.frontiersin.org/journals/signal-processing/articles/10.3389/frsip.2023.1276748/full>　**（2026-09-08 第四輪新增）** | **P1** | ① **頻率側的量化誤差**：該模型預測**第一 partial** 的平均 cent 偏差最大 **4.46×10⁻¹ cents**（Table 1），作者自評「相對於半音 100 cents 可視為感知上可忽略」；② **前九個 partial 預測準確、更高階誤差變大**；③ 高頻段 partial 生成較不準，**高 velocity 尤其明顯**；④ 高階 partial 的衰減時間被**低估** | 「a max value of 4.46 ⋅ 10–1」（Sec. 5）<br>「The models accurately predict the first nine partials」<br>「the generation of partials is less accurate」<br>「a slight underestimation of the decay time for the higher partials」 |

### 2.4 C 組：最貼近本專案的揚琴外部量測

| # | 出處 | 級別 | 關鍵數字 | ≤15 字原文引述 |
|---|---|---|---|---|
| C1 | Sinin, A. E., Hamdan, S., Chu, Y. J., Said, K. A. M., Musib, A. F. (2026). *The Yangqin: Acoustical Study of a Chinese Dulcimer*. **BioResources 21(1), 1084–1097**（開放取用）。全文 PDF：<https://bioresources.cnr.ncsu.edu/wp-content/uploads/2025/12/BioRes_21_1_1084_Sinin_HJSM_Yangqin_Acoustic_Study_Chinese_Dulcimer_24951-1.pdf>（本輪親自解析全文） | **P1（方法學等級低，見右）** | **Table 3 的 `f/f₀` 只報到小數兩位**，且被判定為「諧音」的判準極寬：course 6 partial 4 的 1.97 標為「=2」（相當於 **26 cents** 偏差）、course 1 partial 2 的 **1.82 也標為「=2」（相當於 163 cents**）。全文**未報告 FFT 的取樣率、視窗長度或頻率解析度**。器材：PicoScope 3000 系列示波器 + Adobe Audition，**單一台樂器**，麥克風距琴 20 cm | 「the deviation (D=d/f0) ranges from 6% (course no 6) to 70%」（摘要） |

> **對 `docs/EXTERNAL_ANCHOR_SOURCES.md` 的一項更正（本輪未動該檔，記入 open_items）**：
> 該檔 §5.1 寫「非校準、**非消音室**」，但本輪讀到的原文寫的是
> 「All recordings were conducted in an anechoic chamber」（p.1087）。
> 其餘侷限（單一樂器、`D` 不是標準 `B`、偏差大得不尋常）本輪複核後**維持成立**，
> 而且新增一條：**該表的頻率比值精度只有兩位小數、判準寬達 26～163 cents**，
> 因此**這份資料完全不足以支撐任何 cents 級的 partial 容差**。

### 2.5 D 組：社群證據（使用者觀感／需求，非物理證據）

| # | 出處 | 日期 | 讚數/回應 | 內容摘要 | ≤15 字原文引述 |
|---|---|---|---|---|---|
| D1 | Modartt（Pianoteq）官方論壇，討論串「Uneven partials」：<https://forum.modartt.com/viewtopic.php?id=4075> | 首帖 2015-10-25 19:39 | 論壇未顯示讚數 | 使用者 **scherbakov.al** 用 TuneLab 測真鋼琴，發現部分 partial 的位置與公式算的**對不上**，要求 Pianoteq 開放**逐 partial ±5 cents**的手動調整。Pianoteq 作者 **Philippe Guillaume** 回覆：partial 高度由物理定律決定（弦的非諧性 + 響板阻抗），**沒有其他控制項** | scherbakov.al：「height of some partials does not coincide with those calculated」<br>Philippe Guillaume：「There are no other controls for the partials height.」 |
| D2 | Modartt 論壇，「Research: The Missing Stretch Physics in Pianoteq Steinway D」：<https://forum.modartt.com/viewtopic.php?pid=1006232> | **2026-01-04**（首帖時間戳顯示為 `04-01-2026 22:00`；該論壇用 **DD-MM-YYYY**，由 D1 首帖 `25-10-2015` 可確認格式） | 僅一位社群回應（sigasa） | 使用者 **Lemuel** 用 Fletcher 非諧性公式 + Steinway Model D 實際弦長（A0 2.010 m、C8 0.049 m）算出三套 88 鍵調音表，主張 Pianoteq 預設等律缺少伸展物理。**Modartt 官方未在該串回應** | Lemuel：「Mathematically perfect tuning actually sounds wrong on real pianos」 |
| D3 | Piano World 論壇，「Tuning Unisons in the High Treble」：<https://forum.pianoworld.com/ubbthreads.php/topics/1378463/> | 2010-01-08 起 | 論壇未顯示讚數 | 職業調音師談最高音區（key 83–88）：那一段**衰減極短、音色本來就差**，很多琴「怎麼調都不會好」，作法是聽「顏色」變化而不是對特定 partial | BDB（01/08/10）：「Many pianos do not have good tone in that area.」<br>Patrick Wingren：「Don't beat yourself out trying to set everything perfect」 |
| D4 | KVR Audio，DSP 論壇「Piano Physics」：<https://www.kvraudio.com/forum/viewtopic.php?t=301913> | 2010-11 | 論壇未顯示讚數 | 開發者討論：要做到真實必須處理縱向模態才有鋼琴特有的非諧性；**保持弦「不走音」與把琴橋/共鳴體濾波器做好，被點名為最難的兩件事**。**本條由 WebFetch 摘要取得，未逐字核對全文，引述僅供方向參考** | asomers（2010-11-12，經摘要）：「necessary to model the longitudinal modes of the piano string」 |
| D5 | **Reddit（r/piano、r/synthesizers、r/audioengineering）** | — | — | **本機環境無法取得**：`WebFetch` 對 `reddit.com` 與 `old.reddit.com` 皆回傳「Claude Code is unable to fetch」，`WebSearch` 對 `reddit.com` 網域回傳 400（該網域不開放給搜尋 user agent）。`.json` 變體同樣被擋。**因此 Reddit 一條都沒取得，本文件不引用任何 Reddit 內容** | 未取得原文 |

**C 組（社群）能支持的結論，只有一條**：使用者在意的是 partial 的**頻率／音準**
（D1 要求的是「±5 cents 的位置調整」、D2 整篇在算 cents），**沒有一條**在抱怨
partial 的**振幅**對不對。這與 §4 建議「先驗頻率、暫不驗振幅」的方向一致——
但這只是需求證據，**不能拿來當物理理由**。

---

## 3. 引擎現況數字（本輪實跑，未改任何程式碼）

### 3.1 產生方式（可重現）

```
# 產生探針 score（velocity 0.45、steel、diameter_mm 1.0，與 fur_elise corpus 同參數；reverb wet 0）
output\wf0907\R1\r1_partial_probe.score.json

# 唯讀 dump（不渲染、不寫任何 repo 檔）
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --dump-modes ^
    output\wf0907\R1\r1_partial_probe.score.json > output\wf0907\R1\dump_modes_a4_g5_g6.txt

# 換算腳本輸出
output\wf0907\R1\r1_numbers.txt
```

三根弦中取**中間那根**（= 標稱音高那根）。**本 corpus 的預設值**是每顆音三根弦、
總展寬 **10.0 cents**（±5 cents），A4/G5/G6 實測皆同。

> **這不是寫死的常數，是可覆寫的預設值**（複核指正，本輪確認）：
> `src/score/ScoreParser.h:78` `int numStrings = 3;`（score 欄位預設）、
> `src/engines/CimbalomEngine.h:65-66` `numStrings = 3` / `detuningCents = 5.0f`，
> 另有 `src/cli/RenderApp.cpp` 的 `--num-strings`（診斷用覆寫，範圍 [1,5]）。
> 也就是說：下面 §4-B 容差理由①講的「物理地板」，是**本 corpus 這組預設值下的**
> 地板，不是引擎在任何設定下都成立的常數。若哪天 score 改成單弦或改變展寬，
> 這條理由要重新評估。

### 3.2 模型預測的 partial（中間弦）

**A4（MIDI 69）** — 擬合 `B = 1.361×10⁻³`

| n | 頻率 (Hz) | f_n/f₁ | 相對 n·f₁ (cents) | 振幅（dB 相對該音最大 partial） |
|---|---|---|---|---|
| 1 | 440.000 | 1.0000 | 0.0 | **0.0** |
| 2 | 881.792 | 2.0041 | +3.5 | −10.0 |
| 3 | 1327.157 | 3.0163 | +9.4 | −16.4 |
| 4 | 1777.851 | 4.0406 | +17.5 | −22.5 |
| 5 | 2235.595 | 5.0809 | +27.8 | −28.7 |
| 6 | 2702.066 | 6.1411 | +40.2 | −35.4 |
| 7 | 3178.885 | 7.2247 | +54.7 | −43.7 |
| 8 | 3667.614 | 8.3355 | +71.1 | −∞（amp = 0） |

**G5（MIDI 79）** — 擬合 `B = 4.321×10⁻³`

| n | 頻率 (Hz) | f_n/f₁ | 相對 n·f₁ (cents) | 振幅 (dB) |
|---|---|---|---|---|
| 1 | 783.991 | 1.0000 | 0.0 | −9.1 |
| 2 | 1578.069 | 2.0129 | +11.1 | **0.0** |
| 3 | 2392.108 | 3.0512 | +29.3 | −19.4 |
| 4 | 3235.575 | 4.1271 | +54.1 | −9.6 |
| 5 | 4117.372 | 5.2518 | +85.1 | −21.9 |
| 6 | 5045.709 | 6.4359 | +121.4 | −28.3 |
| 7 | 6028.044 | 7.6889 | +162.5 | −30.8 |

**G6（MIDI 91）** — 擬合 `B = 1.728×10⁻²`

| n | 頻率 (Hz) | f_n/f₁ | 相對 n·f₁ (cents) | 振幅 (dB) |
|---|---|---|---|---|
| 1 | 1567.982 | 1.0000 | 0.0 | −10.9 |
| 2 | 3214.894 | 2.0503 | +43.0 | **0.0** |
| 3 | 5013.458 | 3.1974 | +110.3 | −4.3 |
| 4 | 7025.850 | 4.4808 | +196.5 | −15.7 |
| 5 | 9302.037 | 5.9325 | +296.1 | −14.9 |
| 6 | 11880.328 | 7.5768 | +404.0 | −23.1 |

**F♯6（MIDI 90）** — 擬合 `B = 1.540×10⁻²`　**（2026-09-08 第四輪新增；先前三輪從未跑過這顆）**

| n | 頻率 (Hz) | f_n/f₁ | 相對 n·f₁ (cents) | 振幅 (dB) |
|---|---|---|---|---|
| 1 | 1479.978 | 1.0000 | 0.0 | −4.1 |
| 2 | 3026.538 | 2.0450 | +38.5 | **0.0** |
| 3 | 4701.554 | 3.1768 | +99.1 | −10.9 |
| 4 | 6558.761 | 4.4317 | +177.4 | −14.8 |
| 5 | 8642.243 | 5.8394 | +268.7 | −16.7 |
| 6 | 10986.586 | 7.4235 | +368.6 | −22.9 |
| 7 | 13618.077 | 9.2015 | +473.4 | −34.8 |

**D7（MIDI 98）** — 擬合 `B = 3.880×10⁻²`　**（2026-09-08 第四輪新增）**

| n | 頻率 (Hz) | f_n/f₁ | 相對 n·f₁ (cents) | 振幅 (dB) |
|---|---|---|---|---|
| 1 | 2349.318 | 1.0000 | 0.0 | **0.0** |
| 2 | 4954.909 | 2.1091 | +91.9 | −24.5 |
| 3 | 8032.265 | 3.4190 | +226.3 | −0.9 |
| 4 | 11738.290 | 4.9965 | +385.1 | −7.7 |
| 5 | 16176.501 | 6.8856 | +554.0 | −38.4 |

> **這兩張表回答了 §5-K8 的一半（只有一半，請照這個範圍讀）**：
> 22 顆弱基頻高音裡，F♯6 先前**兩份來源（`stem_verify_fur_elise_run.txt`、`EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.4）都沒量過**、D7 被歸為「另一類」。
> 第四輪的 `--dump-modes` 顯示：
> - **F♯6 的最大 partial 是 n=2（3026.5 Hz，比值 2.0450）**——與 G5／G6 同型，
>   即「模型自己就預測基頻不是最大的那個」。
> - **D7 的最大 partial 是 n=1（基頻本身）**——**模型預測與 `stem_verify` 的乾聲實測
>   （主導即基頻、+4.7 cents）方向一致**，獨立支持「D7 屬『整體太安靜』而非『基頻缺失』」的既有判定。
>
> **但這仍然是「模型說的」，不是「聲音裡量到的」**（K7 不變）：本輪同樣沒有對渲染 WAV 做 FFT。
> 要把 K8 完全關掉，仍須對 F♯6 做乾聲渲染實測——那是選項 B 的工程，本研究卡不做。

> **與 §8.4 第 3 點的實測交叉核對（獨立確認）**：`stem_verify_fur_elise_run.txt` 發現 2
> 記錄 G5 乾聲主導頻率 **1571.5 Hz、比值 2.0044**、G6 主導 **3214.9 Hz、比值 2.0503**。
> 本輪 `--dump-modes` 給的 G6 第二 partial = **3214.894 Hz、比值 2.0503**，**完全吻合**；
> G5 三根弦的第二 partial 為 1573.5 / 1578.1 / 1582.6 Hz，實測 1571.5 Hz 落在該叢集的
> 最低側附近。
>
> **這句話只能推到哪裡（複核指正後收斂，請照這個範圍讀）**：
> `stem_verify_fur_elise_run.txt:66` 記載那 22 顆的組成是 **G5 ×19、D7 ×1、G6 ×1、F♯6 ×1**。
> 本輪與該檔的交叉核對**只涵蓋其中 20 顆（G5 ×19 + G6 ×1）**，對這 20 顆可以說：
> **主導頻率就是模型預測的第二 partial，不是雜訊、不是錯的音——引擎在照自己的模型走。**
> 另外兩顆**不成立或未量**：
> - **D7 ×1**：`stem_verify_fur_elise_run.txt` 與 `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md`
>   §8.4 第 3 點都明寫「主導即基頻（+4.7 cents）」，屬**「整體太安靜」而非「基頻缺失」**
>   ——這顆的主導頻率**不是**第二 partial。
> - **F♯6 ×1**：兩份來源**都沒有量**它的主導頻率，本輪也沒跑（§5-K7：本輪只跑 A4/G5/G6）。
>   狀態是**未知**，不得併入上述結論。

### 3.3 與真鋼琴 `B` 的對照（**本節是 A14 的關鍵輸入**）

參考琴：Fletcher 1964 那台 Hamilton 直立鋼琴（Table I 給了每一鍵的弦徑 `d` 與弦長 `l`）。
用該論文所給的實心鋼弦公式 `B = 3.95×10¹⁰ · d²/(l⁴·f₀²)`（`d`、`l` 用 cm，`f` 用 Hz；
本輪先用 key 31 驗證此公式：算得 4.21×10⁻⁴ vs 該論文 Table III 實測 **4.44×10⁻⁴**，
**吻合到 5%**，故可信）。

| 音 | 鍵號 | 引擎 `B` | Hamilton 直立琴 `B` | 引擎/真琴 | 引擎弦長 | 真琴弦長 | 引擎弦徑 | 真琴弦徑 |
|---|---|---|---|---|---|---|---|---|
| A4 | 49 | 1.361×10⁻³ | 5.53×10⁻⁴ | **2.46×** | 35.00 cm | 43.6 cm | 1.00 mm | 0.99 mm |
| G5 | 59 | 4.321×10⁻³ | 1.77×10⁻³（Table IV 實測平均 **1.67×10⁻³**） | **2.44×** | 19.64 cm | 23.8 cm | 1.00 mm | 0.94 mm |
| F♯6 | 70 | 1.540×10⁻²（**第四輪新增**） | 3.07×10⁻³ | **5.01×** | 10.41 cm | 14.35 cm | 1.00 mm | 0.85 mm |
| G6 | 71 | 1.728×10⁻² | 3.34×10⁻³ | **5.17×** | 9.82 cm | 13.65 cm | 1.00 mm | 0.85 mm |
| D7 | 78 | 3.880×10⁻²（**第四輪新增**） | 7.20×10⁻³ | **5.39×** | 6.56 cm | 9.15 cm | 1.00 mm | 0.84 mm |
| C8 | 88 | （未跑） | 2.44×10⁻² | — | 3.68 cm | 4.90 cm | 1.00 mm | 0.79 mm |

**偏差的來源已完全解釋（誤差 <0.5%）**：`B ∝ d²/(L⁴f²)`，所以

- A4：`(1.00/0.99)² × (43.6/35.00)⁴ = 2.457`　vs 實際比值 **2.459** ✔
- G5：`(1.00/0.94)² × (23.8/19.64)⁴ = 2.441`　vs 實際比值 **2.442** ✔
- F♯6：`(1.00/0.85)² × (14.35/10.41)⁴ = 4.998`　vs 實際比值 **5.011** ✔（第四輪新增）
- G6：`(1.00/0.85)² × (13.65/9.82)⁴ = 5.168`　vs 實際比值 **5.174** ✔
- D7：`(1.00/0.84)² × (9.15/6.56)⁴ = 5.364`　vs 實際比值 **5.386** ✔（第四輪新增）

也就是說，偏差 **100% 來自兩個建模選擇**，不是隨機誤差：

1. `src/physics/StringModel.h:366` `lengthFromMidiNote()`：弦長 = `0.35 m × 2^(−半音差/12)`，
   即**每高八度弦長減半**。真鋼琴大致也是這樣，但**基準太短**——引擎的弦只有真琴的
   **72～83%**。
2. score 對所有音固定寫 `diameter_mm: 1.0`（`scores/classical/fur_elise/fur_elise_complete.score.json`
   905 顆音全部如此）。真鋼琴弦徑由 0.99 mm（A4）遞減到 0.79 mm（C8）。

引擎 **F♯6（1.54×10⁻²）／G6（1.73×10⁻²）／D7（3.88×10⁻²）三顆都超出 A3 所述的典型範圍上界 10⁻²**
（A4 1.36×10⁻³、G5 4.32×10⁻³ 仍在範圍內）。**第四輪更正：先前只寫「G6 一顆超界」，
實際上一路往上三顆都超，且 D7 超出上界近 4 倍。**

> **參考琴幾何的出處（第四輪親自重抓確認）**：F♯6＝key 70（`d`=0.085 cm、`l`=14.35 cm）、
> D7＝key 78（`d`=0.084 cm、`l`=9.15 cm），與既有的 key 49／59／71 一樣取自
> Fletcher 1964 Table I。本輪重新下載 <http://www.jbsand.dk/div/StivStreng.pdf>
> （存取日期 2026-09-08）並用 PyMuPDF 自行抽取文字核對這五列，逐格相符；
> 表格標題原文：「Dimensions of solid strings in Hamilton upright piano (new model)」。

> ⚠️ **Rule 10 警示**：`lengthFromMidiNote()` 的基準長度或弦徑對照表只要動一個字，
> 全部 73 檔 corpus 的渲染輸出都會變。**本輪不提出任何修改，只把數字擺出來。**

### 3.4 振幅側的對照

以 B1（Fletcher 1962；**2026-09-08 追補已取得全文，該句在 p.749 摘要獲逐字確認**）的
「每 100 cps 降 2 dB」當粗略尺規：

| 音 | n1→n2 頻率差 | 該規則預期 | 引擎實際 | 差距 |
|---|---|---|---|---|
| A4 | 440 cps | −8.8 dB | **−10.0 dB** | 1.2 dB（很接近） |
| G5 | 784 cps | −15.7 dB | **+9.1 dB**（第二 partial 反而較大） | **約 25 dB** |
| G6 | 1568 cps | −31.4 dB | **+10.9 dB** | **約 42 dB** |

**這張表怎麼讀（重要）**：

- B1 那條「2 dB/100 cps」是 1962 年為了讓合成音**聽起來像鋼琴**而找到的最佳值，
  **不是**一條普世的物理定律。**2026-09-08 追補取得全文後，這個結論不但沒變，還更硬**：
  該論文 p.761 明說第五、六個以上的單一 partial **整個拿掉都察覺不到**，
  抬高 **4～5 dB** 才明顯——也就是它給的是**聽感門檻**；而且它給各音的「像鋼琴」
  振幅斜率**可接受區間**本身就很寬：Tone G″ 2.5→1.5、Tone G 13.0→5.0、
  Tone G₂ 40→7.5 dB/partial（寬度 **1.0／8.0／32.5 dB**，中點 2／8／32）。
  （**音名 G″／G／G₂ 是本文件的正規化寫法**，掃描檔文字層的原樣殘缺，見 §2.3-B1 ④ 的說明。）
  **不可以拿它當 GATE 容差。**
- 但 B2（**已取得全文**）獨立說了高音區「第三個 partial 之後振幅都極低」，
  而引擎 G6 的第三 partial 反而是第二大（−4.3 dB）。兩條線索方向一致：
  **引擎在高音區的能量分佈偏向高階 partial，與文獻描述的真鋼琴不同。**
- 這與 §3.3 是**同一件事**：`B` 偏大 → 高階 partial 被推得更高更散 → 能量分佈改變。
  **A14 的判定應該以 §3.3 的弦幾何為主線，而不是只看電平。**

---

## 4. 選項與建議

### 選項 A：不立 partial GATE，只在文件宣告「未驗證」

| 項目 | 內容 |
|---|---|
| **主張強度** | 最低。維持 §8.4 現狀：「泛音的頻率與振幅**不在主張範圍內**」 |
| **工具改動** | 零 |
| **風險** | **假綠燈風險 = 0**（沒有燈）。但 §3.3 那個 2.4～5.4 倍偏差會**繼續沒人看著**；未來若有人拿 spectrogram 對比真鋼琴，我們沒有先手 |
| **適用時機** | 若月月希望本輪完全不擴張主張域 |

### 選項 B：只驗 partial 頻率（**內部一致性**：渲染 WAV vs `--dump-modes` 預測）

| 項目 | 內容 |
|---|---|
| **主張強度** | 「引擎渲染出來的聲音，其 partial 頻率符合引擎自己宣告的模型」。**這不等於「符合真鋼琴」**——措辭必須寫清楚 |
| **容差來源（請月月核這一行）** | **±5 cents，沿用 `melody_verify` 既有的產品門檻**（月月既有裁定，`EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.4 第 2 點），**不是新容差**。理由三條：<br>① **在本 corpus 的預設設定下**（每音三根弦、unison 展寬 **10.0 cents（±5）**，§3.1 實測；此為 `ScoreParser.h`／`CimbalomEngine.h` 的**可覆寫預設值**，非寫死常數），任何比 ±5 cents 更緊的門檻在物理上量不到；<br>② 文獻的「模型 vs 實測」一致度為 RMS 0.99 cents／最大 1.82 cents（A2，實心高音弦，6 組可判讀），**遠優於 ±5**，所以 ±5 不是在放水；**第四輪補一條同方向的現代數字**：2024 年一篇物理知情可微分鋼琴模型（B8）報告其**第一 partial** 的平均 cent 偏差最大 **0.446 cents**，同樣遠優於 ±5；<br>③ 一套半自動調音系統與**一位**專業調音師的成果之間，偏差本身就有 2.5 cents RMS（A0–G5）／8.1 cents RMS（G♯5–C8）（A5，**僅摘要**；原文比較的是 CRI 系統 vs 該位調音師，**不是調音師彼此之間的一致度**），±5 cents 落在人類調音實務可及的量級內 |
| **前置** | **必須先完成 C10**（量測器合成哨兵自證 ≤1 cent）。沒有 C10，這條 GATE 站在一把未校驗的尺上 |
| **工程量估計** | 中。`stem_verify` / `melody_verify` 需要：① 讀 `--dump-modes` 的逐 partial 預測；② 在乾聲軌對每個預測頻率開窄帶找峰；③ 三弦叢集要當成一個目標（取叢集質心或最近峰）；④ 只驗**振幅高於本底 N dB** 的 partial，其餘明確**拒答**而非通過（拒答理由靠 C11）。粗估 1～2 張施工卡 |
| **風險** | **假綠燈中等**：驗的是「引擎符合自己」，所以就算 §3.3 那個 2.4～5.4 倍偏差存在，這條 GATE 也會全綠。**必須在文件與對外措辭裡寫死這一點**，否則會被誤讀成「泛音已對上真鋼琴」 |

### 選項 C：頻率 + 振幅一起驗

| 項目 | 內容 |
|---|---|
| **主張強度** | 最高：「partial 的頻率與相對振幅都經量測」 |
| **容差來源** | **查不到可用的外部數字**。本輪找遍 A/B 兩組：<br>• B1 的「2 dB/100 cps」是 1962 年的**聽感最佳值**（2026-09-08 追補已取得全文，**結論不變且更硬**：該文給的唯一「差多少才有差」是 **4～5 dB 的聽感門檻**，且第五、六個以上的 partial 拿掉都察覺不到；本專案不採信聽感，**因此它不能當容差**）；<br>• B3（2025 最新神經網路模型）自承高頻能量預測「presents more challenges」，**沒有給出可當門檻的 dB 數字**；<br>• B4 顯示響板在 550 Hz 以下平均每 **22 Hz** 就有一個模態、損耗因子 ~2%，代表 partial 落在共振峰或谷會差很多 dB；<br>• B5（弦耦合造成的雙衰減）、B6（phantom partials）**都未取得原文**；<br>• **B8（2024，第四輪新增）**：頻率側給得出 0.446 cents 的量化誤差，**振幅側只給定性結論**（高頻 partial 生成較不準、高 velocity 尤其明顯、高階 partial 衰減時間被低估），**沒有任何可當門檻的 dB 數字**——這是「連 2024 年的論文都只敢定性描述振幅」的第二個獨立佐證。<br>**結論：現階段任何振幅容差都只能由工程端自訂 → 直接違反 R2** |
| **工程量估計** | 大。除了選項 B 的全部，還要處理：三弦拍音造成的振幅隨時間起伏、量測窗長選擇、本底判定、正規化基準 |
| **風險** | **假綠燈高**。若容差設寬到能過（例如 ±10 dB），這盞燈的資訊量趨近於零；若設緊，會因為量測方法而非物理而紅燈 |
| **建議** | **現在不要做。** 若未來要做，前置是取得 B5/B6 原文 + 一份自己的量測重複性研究 |

### 選項 B+（**本文件的建議**）＝ 選項 B ＋ 一份**不當 GATE**的文獻對照報告

| 項目 | 內容 |
|---|---|
| **內容** | ① 照選項 B 立「內部一致性」partial 頻率 GATE（前置 C10）；<br>② 另外產出一份**報告**（不是 GATE、不擋 CI）：把引擎每個音的 `B` 與 §3.3 的 Fletcher 參考值並排，列出比值。這份報告**只呈現數字，不設通過條件** |
| **為什麼不把 ② 也做成 GATE** | 因為現在對照結果是 **2.4～5.4 倍**，一旦設成 GATE 就是開卡即紅燈，而唯一能讓它變綠的手段是改 `lengthFromMidiNote()` 或改所有 score 的弦徑 → **直接觸發 R10**，且會改變全部 73 檔 corpus 的渲染。**這是月月的決策，不是工程端可以順手做的事** |
| **可發布措辭（建議草案，請月月核）** | 「partial 的**頻率**已驗：渲染輸出符合引擎宣告的剛性弦模型（±5 cents，量測器自證 ≤1 cent）。partial 的**振幅**未驗。引擎的非諧性係數與參考鋼琴的比值另有報告，**尚未對齊**。」<br>**不可**寫成「泛音已驗證」或「泛音與真鋼琴一致」 |

### 一句話建議

**選 B+**：立 partial **頻率**的內部一致性 GATE（容差沿用既有 ±5 cents、前置 C10），
**不立**振幅 GATE（外部找不到可溯源的容差，會違反 R2），
**另外**把 `B` 對照真鋼琴的 2.4～5.4 倍偏差寫成報告交給月月裁決（因為修它會觸發 R10）。

### 容差數字的出處（**單獨一行，請月月核**）

> **±5 cents = 本專案既有裁定的產品門檻**（`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.4 第 2 點），
> **不是新容差、不是外部標準**。外部文獻只用來證明「這個門檻不算放水」：
> Fletcher 1964 JASA 36(1) 203–209 的模型-實測一致度為 **RMS 0.99 cents／最大 1.82 cents**
> （實心高音弦 String No.54，本文件依其 Table VI 原始數字換算、只取 6 組可判讀列，見 §2.2-A2；
> **先前版本寫 0.86 是把糊掉的列當誤差 0 一起除的結果，已更正**），
> 而一套半自動調音系統與**一位**專業調音師的成果之間，偏差就有
> **2.5 cents RMS（A0–G5）／8.1 cents RMS（G♯5–C8）**
> （Tuovinen 2019，**僅摘要**；原文原句為 “a tuning close to that of a professional tuner
> is achieved with a deviation of 2.5 cents (RMS) …”，比較對象是 **CRI 系統 vs 該位調音師**，
> **不是「調音師彼此之間的一致度」**——月月核這一行時請特別注意這個區別）。

---

## 5. 已知缺口（誠實清單）

| # | 缺口 | 影響 |
|---|---|---|
| **K1** | **Fletcher 1964 Table IV 有印刷不一致**：`B` 欄逐列為 0.00160/0.00175/0.00166/0.00166、平均列印 **0.00167**，但下方兩行卻印 **B=0.000167**（差十倍）。用該論文自己的式 (26b) `B=(2/F)(Δf/n³)=2×0.650/776.7` 反算得 **0.001674**，且本文件用最小平方法直接擬合其 9 個實測 partial 得 **1.682×10⁻³**——**兩者都支持 0.00167**，故 §3.3 採 0.00167。該論文有一份 Errata（JASA 36, 1214）**本輪未取得原文**，無法確認是否就是修這一處 | 不影響結論（§3.3 另有 Fletcher 公式獨立算得 1.77×10⁻³，一致） |
| **K2** | **Reddit 完全未取得**。`WebFetch` 對 reddit.com / old.reddit.com 被本機環境封鎖，`WebSearch` 對該網域回傳 400。因此「使用者到底在意頻率還是振幅」只有 4 條非 Reddit 社群證據支撐（D1–D4）。**2026-09-08 第四輪第三度確認**：`WebFetch` 對 `old.reddit.com` 回「Claude Code is unable to fetch」，另用一般關鍵字 `WebSearch`（不限網域）搜「reddit r/piano inharmonicity partials」，回傳結果**零筆 reddit.com 連結** | 社群結論的樣本偏小，且集中在 Pianoteq／調音師社群 |
| **K3** | **付費牆／403 未取得原文**：Weinreich 1977（弦耦合、雙衰減）、Conklin 1996 **Part I／II／III**（Part III = phantom partials；**2026-09-08 第三輪追補**：Part I 的 `article-pdf` 直連回 HTTP 403、Part II 付費牆，兩篇同樣未取得）、**Galembo & Askenfelt 1999**（IEEE 付費牆，自存版未找到；**第三輪追補**）、Rauhala 2007、Anderson & Strong 2005 全文、Tuovinen 2019 全文、Acta Acustica 2021 低非諧性低音弦。<br>**2026-09-08 追補更正**：原本列在本欄的 **Fletcher/Blackham/Stratton 1962（B1）已取得全文**（BYU 自存 PDF），故自本欄移除；讀完全文後 K4 的缺口**依然成立**（見 K4） | 振幅側仍缺 **B5/B6** 兩篇原文，這是選項 C 現在做不了的直接原因之一 |
| **K4** | 沒有找到**任何**公開文獻報告「同一顆鋼琴音重複敲擊時，各 partial 振幅的重複性有多少 dB」。這是設計振幅 GATE 的必要前提，**查不到就是查不到**。<br>**2026-09-08 追補確認**：讀完 B1 全文後仍然查不到——B1 給的 4～5 dB 是**聽感可察覺門檻**，不是量測重複性；它甚至說第五、六個以上的 partial 拿掉都察覺不到，方向與「量測重複性」無關 | 選項 C 缺物理地板 |
| **K5** | §3.3 的參考琴是**一台 1964 年的 Hamilton 直立鋼琴**（Fletcher 用的那台），不是平台琴、更不是揚琴。`B` 隨琴款差異可達數倍。**「引擎高 2.4～5.4 倍」這句話的正確讀法是「相對於這一台參考琴」**，不是「相對於所有鋼琴」 | A14 判定時必須帶上這個限制詞 |
| **K6** | 揚琴那份（C1）的方法學不足以支撐 cents 級容差（`f/f₀` 只兩位小數、判準寬達 26～163 cents、未報告 FFT 解析度）。**旗艦引擎 Cimbalom 目前沒有可用的外部 partial 頻率錨點** | 若未來要把 partial GATE 擴到 cimbalom，得先找到新的量測來源 |
| **K7** | 已跑 A4/G5/G6/**F♯6/D7**（第四輪由三顆擴為五顆）、velocity 0.45、steel 1.0 mm 單一組合，但仍**只看模型預測（`--dump-modes`），沒有對渲染 WAV 做 FFT 實測**（那正是選項 B 要做的工程） | §3.2 的表是「模型說的」，不是「聲音裡量到的」——**本文件任何一句都不得被讀成「已實測 partial」**。第四輪擴顆數並未改變這條缺口的性質 |
| **K8**（第四輪部分收斂） | §8.4 那 22 顆「基頻極弱」的高音（G5 ×19、D7 ×1、G6 ×1、F♯6 ×1）中，20 顆（G5+G6）有**渲染實測**主導頻率可與模型預測對照。**第四輪補上 F♯6 與 D7 的模型預測**：F♯6 最大 partial = n=2（與 G5/G6 同型）、D7 最大 partial = n=1（與 `stem_verify` 乾聲實測「主導即基頻」一致）。**但 F♯6 至今仍沒有任何渲染實測數字**（只有模型預測） | 缺口由「F♯6 完全未知」縮小為「F♯6 只有模型側、缺實測側」。A14 若要對 22 顆下統一判定，**仍須補 F♯6 的乾聲渲染實測**，且 D7 仍應當成另一類問題 |

---

## 附錄 A：來源清單（存取日期一律 2026-09-08）

**P1（已取得原文並親自核對）**

1. Fletcher, H. (1964). *Normal Vibration Frequencies of a Stiff Piano String*. JASA 36(1), 203–209. <http://www.jbsand.dk/div/StivStreng.pdf>（掃描 PDF，本輪逐頁轉圖判讀 Table I/III/IV/V/VI 與 Fig. 1）
2. Rigaud, F., David, B., Daudet, L. (2013). *A parametric model and estimation techniques for the inharmonicity and tuning of the piano*. JASA 133(5), 3107–3118. <https://www.institut-langevin.espci.fr/IMG/pdf/2013_a_parametric_model_and_estimation_techniques_for_the_inharmonicity_and_tuning_of_the_piano.pdf>
3. Hodgkinson, M., Wang, J., Timoney, J., Lazzarini, V. (2009). *Handling Inharmonic Series with Median-Adjustive Trajectories*. DAFx-09. <https://www.dafx.de/paper-archive/2009/papers/paper_94.pdf>
4. Shah, S., Välimäki, V. (2020). *Automatic Tuning of High Piano Tones*. Applied Sciences 10(6), 1983. <https://pdfs.semanticscholar.org/2e4e/f5be26f612b18ef5aee96a4ff2b117b2e8fc.pdf>
5. Simionato, R., Fasciani, S. (2025). *Sines, transient, noise neural modeling of piano notes*. Frontiers in Signal Processing 4. <https://www.frontiersin.org/journals/signal-processing/articles/10.3389/frsip.2024.1494864/full>
6. Ege, K., Boutillon, X. (2010). *Vibrational and acoustical characteristics of the piano soundboard*. arXiv:1212.3068. <https://arxiv.org/pdf/1212.3068>
7. Sinin, A. E. et al. (2026). *The Yangqin: Acoustical Study of a Chinese Dulcimer*. BioResources 21(1), 1084–1097. <https://bioresources.cnr.ncsu.edu/wp-content/uploads/2025/12/BioRes_21_1_1084_Sinin_HJSM_Yangqin_Acoustic_Study_Chinese_Dulcimer_24951-1.pdf>
8. Roy, E. (2024). *Investigating the Inharmonicity of Piano Strings*. Edinburgh Student Journal of Science, DOI 10.2218/esjs.9815. <https://journals.ed.ac.uk/esjs/article/download/9815/12844/35937>（**學生期刊，僅用於引用 Fletcher 的 `B = 3.95×10¹⁰·d²/(l⁴f₀²)` 公式形式**；本文件另用 Fletcher 自己的 Table III 數字獨立驗證該公式，見 §3.3）

9. **（2026-09-08 由 P2 升級至 P1）** Fletcher, H., Blackham, E. D., Stratton, R. (1962). *Quality of Piano Tones*. JASA 34(6), 749–761. 作者機構自存全文 PDF：<https://physics.byu.edu/download/publication/1504>（索引頁 <https://physics.byu.edu/department/publications/fletcher>）。出版社頁仍 403。本輪逐頁核對 p.749 摘要、p.752 量測方法、p.761 振幅門檻與各音振幅斜率區間

**P2（僅摘要／未取得原文——不得用於數字主張）**

10. Weinreich, G. (1977). *Coupled piano strings*. JASA 62(6), 1474–1484.（403）
11. Conklin, H. A. (1996). *Design and tone in the mechanoacoustic piano. Part III*. JASA 100(3), 1286–1298.（付費牆）
12. Rauhala, J., Lehtonen, H.-M., Välimäki, V. (2007). *Fast automatic inharmonicity estimation algorithm*. JASA 121(5), EL184.（403）
13. Tuovinen, J., Hu, J., Välimäki, V. (2019). *Toward Automatic Tuning of the Piano*. SMC 2019, 143–150. <https://research.aalto.fi/en/publications/toward-automatic-tuning-of-the-piano/>（PDF 403，只取得機構庫摘要）
14. Anderson, B. E., Strong, W. J. (2005). *The Effect of Inharmonic Partials on Pitch of Piano Tones*. JASA 117, 3268–3272. <https://scholarsarchive.byu.edu/facpub/1002>（PDF 403，只取得摘要）
15. Fletcher, H. *Errata: Normal Vibration Frequencies of a Stiff Piano String*. JASA 36, 1214 (1964).（未取得原文）

**C（社群／論壇——使用者觀感證據，非物理證據）**

16. Modartt 論壇「Uneven partials」（首帖 2015-10-25）：<https://forum.modartt.com/viewtopic.php?id=4075>（本輪已取得逐字原文）
17. Modartt 論壇「Research: The Missing Stretch Physics in Pianoteq Steinway D」（**2026-01-04**，論壇顯示 `04-01-2026 22:00`，DD-MM-YYYY）：<https://forum.modartt.com/viewtopic.php?pid=1006232>
18. Piano World 論壇「Tuning Unisons in the High Treble」（2010-01-08 起）：<https://forum.pianoworld.com/ubbthreads.php/topics/1378463/>
19. KVR Audio「Piano Physics」（2010-11）：<https://www.kvraudio.com/forum/viewtopic.php?t=301913>（**摘要取得，未逐字核對**）
20. Reddit（r/piano / r/synthesizers / r/audioengineering）：**本機環境無法存取，零條取得**

**M（商業產品官方文件——廠商公開主張，非物理量測；2026-09-08 第三輪追補）**

21. Modartt, *Pianoteq User Manual*（線上版，英文）：<https://www.modartt.com/user_manual?lang=en&product=pianoteq>（本輪 WebFetch 取得逐字原文）

**P2（僅摘要／未取得原文——不得用於數字主張；2026-09-08 第三輪追補）**

22. Galembo, A., Askenfelt, A. (1999). *Signal representation and estimation of spectral parameters by inharmonic comb filters with application to the piano*. IEEE Trans. Speech and Audio Processing 7(2), 197–203. <https://ieeexplore.ieee.org/abstract/document/748124/>（IEEE 付費牆；KTH DiVA 等自存版本本輪搜尋未找到，**未取得原文**）
23. Conklin, H. A. (1996). *Design and tone in the mechanoacoustic piano*. **Part I** JASA 99(6), 3286–3296 <https://pubs.aip.org/asa/jasa/article/99/6/3286/751275/>；**Part II** JASA 100(2), 695–708 <https://pubs.aip.org/asa/jasa/article/100/2/695/558197/>（Part I 的 `article-pdf` 直連本輪回 **HTTP 403**，Part II 付費牆，**兩篇皆未取得原文**；Part III 見第 11 條）

**P1（2026-09-08 第四輪新增；編號接在既有清單之後，前 23 條的編號一律不動，以免文件內既有的「附錄 A 第 N 條」交叉指涉失效）**

24. Simionato, R., Fasciani, S., Holm, S. (2024). *Physics-informed differentiable method for piano modeling*. Frontiers in Signal Processing 3, DOI 10.3389/frsip.2023.1276748. <https://www.frontiersin.org/journals/signal-processing/articles/10.3389/frsip.2023.1276748/full>（開放取用；本輪 WebFetch 兩次取得，第二次專門核對 Table 1 與 cent deviation 的上下文。**與第 5 條（B3，2025）為同一組作者的另一篇，兩者不是獨立團隊**）

## 附錄 B：本輪產生的暫存檔（`output\` 已 gitignore）

- `output\wf0907\R1\r1_partial_probe.score.json` — 探針 score（A4/G5/G6、velocity 0.45）
- `output\wf0907\R1\dump_modes_a4_g5_g6.txt` — `--dump-modes` 原始輸出
- `output\wf0907\R1\r1_numbers.txt` — 所有 cents／`B`／dB 換算的完整輸出
- （2026-09-08 追補輪）`output\wf0907\R1\dump_modes_A4_G5_G6.txt` — 第二位 Opus 獨立重跑的 `--dump-modes` 原始輸出
- （2026-09-08 追補輪）`output\wf0907\R1\fletcher_vs_engine_B.txt` — **過程記錄，其比值不採用**：
  該檔用 log 內插取參考琴 `B`，跨過 Fletcher 自述的「sudden breaks」，得 1.31／2.59／5.86×；
  本文件 §3.3 採用的是 Table I 逐鍵幾何算法（2.46／2.44／5.17×）。理由見文末追補記錄 §一。
- （2026-09-08 追補輪）`output\wf0907\R1\fletcher1962_quality.txt` — Fletcher 1962 全文抽取文字
- （2026-09-08 **第四輪**）`output\wf0907\R1\r1_r4_probe.score.json` — 五顆音探針 score（A4/G5/G6/**F♯6/D7**）
- （2026-09-08 **第四輪**）`output\wf0907\R1\r4_dump_modes_5notes.json` — 五顆音 `--dump-modes` 原始輸出
- （2026-09-08 **第四輪**）`output\wf0907\R1\r4_numbers.txt` — 第四輪逐項換算（partial 表、擬合 `B`、閉式 `B`、弦長、`B` 比值、文獻範圍檢查）
- （2026-09-08 **第四輪**）`output\wf0907\R1\r4_fletcher1964_tableI.txt` — 本輪重新下載 Fletcher 1964 PDF 後自行抽取的全文（核對 Table I 的 key 49/59/70/71/78）
- （2026-09-08 **第四輪**）`output\wf0907\R1\A13_backup_before_round4_20260908.md` — 本輪動筆前的文件備份
- （2026-09-08 追補輪）`output\wf0907\R1\r1_numbers_addendum.txt` — 獨立複驗的逐項換算輸出
  （含 Table VI 兩根弦的可判讀組數與 RMS、Table IV 兩種 `B` 的逐項殘差）

## 附錄 C：規則遵循

- **R2**：未調寬任何容差、未自訂新容差。選項 B 的 ±5 cents 明確標示為**既有裁定門檻**，出處單獨列行。
- **R3**：未縮小任何 GATE 範圍。
- **R4**：未 hardcode 任何常數；查不到的（振幅重複性、揚琴頻率解析度、Reddit）一律寫「查不到／未取得原文」。
- **R6**：未動 `src/`。
- **R7**：未 commit、未 push、未 checkout/stash/reset。
- **R10**：§3.3 發現的弦幾何偏差**已標為 R10 觸發項，本輪不落地任何修改**，交月月裁決。
- 研究卡鐵律：未引用 TsukiSynth 自身文件當外部證據（§2 全部為外部來源；repo 文件只在 §1/§3 當「我們現況」引用）。

---

## 複核修正記錄（2026-09-07）

> 引用複核（另一位 Opus）逐條打開原始來源後提出 8 條 findings，全部處理如下。
> 本輪修正**未新增任何來源**，也未新增任何數字主張；所有改動都是「收斂主張」或「更正標示」。
> 修正時本輪親自重抓了 Tuovinen 2019 機構庫頁與 Modartt `pid=1006232` 兩個網頁確認，
> 並親自讀了 `src/score/ScoreParser.h`、`src/engines/CimbalomEngine.h`、`src/cli/RenderApp.cpp`
> 與 `reports/gate_outputs/stem_verify_fur_elise_run.txt` 確認。**未改任何 `src/` `tools/` 檔案。**

| # | 嚴重度 | 複核指出的問題 | 本輪怎麼改 |
|---|---|---|---|
| 1 | **blocker** | §4-B 容差理由③ 與 §4「容差數字的出處」把 Tuovinen 2019 的 2.5／8.1 cents RMS 寫成「**專業調音師之間**的一致度」。原文比較的是 **CRI 半自動調音系統 vs（一位）專業調音師**，不是調音師彼此。錯的版本剛好落在「請月月核這一行」上 | 兩處全部改寫為「一套半自動調音系統與**一位**專業調音師的成果之間，偏差就有 2.5 cents RMS（A0–G5）／8.1 cents RMS（G♯5–C8）」，並在「請月月核這一行」該段補上原文原句 “a tuning close to that of a professional tuner is achieved with a deviation of 2.5 cents (RMS) …” 與一句明示「**不是**調音師彼此之間的一致度」。§2.2-A5 原本就寫對，維持不動。本輪重新 WebFetch 該機構庫頁確認 |
| 2 | major | §0 寫「G5 高 2.6 倍」「那 2.5／2.6／5.2 倍」，與 §3.3 表格的 2.44× 不符；文件裡沒有任何一處算得出 2.6 | §0 改為逐音精確值「**A4 高 2.46 倍、G5 高 2.44 倍、G6 高 5.17 倍**」並註明後文的範圍寫法就是指這三個數字；全文 5 處「2.5～5.2 倍」一律改為「**2.4～5.2 倍**」（因下界實為 2.44，四捨五入到 2.5 會偏高）。改動處：§0、§4-A 風險、§4-B 風險、§4-B+、§4 一句話建議、§5-K5 |
| 3 | major | §3.2 註腳把 20 顆的觀察外推成 22 顆，且被文件自己引的來源推翻（D7 主導即基頻） | 該註腳整段改寫，明確切成三塊：**可推的 20 顆（G5 ×19 + G6 ×1）**維持「主導 = 模型預測的第二 partial」；**D7 ×1** 標明「主導即基頻 +4.7 cents，屬『整體太安靜』，**不是**第二 partial」；**F♯6 ×1** 標明「兩份來源都沒量、本輪也沒跑，狀態未知，不得併入結論」。另在 §5 新增 **K8** 把這個缺口列成正式已知缺口，並寫明 A14 要下統一判定前至少得補量 F♯6、且 D7 要當另一類問題 |
| 4 | major | D2（Modartt「Missing Stretch Physics」）日期標成 2026-04-01，實為 **2026-01-04**（論壇為 DD-MM-YYYY） | §2.5-D2 與附錄 A 第 17 條兩處都改為 **2026-01-04**，並附上判定依據（原始時間戳 `04-01-2026 22:00`；格式由 D1 的 `25-10-2015` 反證為日-月-年）。本輪重新 WebFetch 該頁確認三則時間戳。該條的引文內容經複核逐字核對無誤，不動 |
| 5 | minor | §2.2-A2 的支持引述雖真、頁碼雖對，但該句談的是 Fig.1／Eq.(28c) 對**纏繞低音弦 `B` 值**的吻合，不是該列標題所指的 **Table VI（partial 頻率計算 vs 實測）** | 引述換成同頁 Table VI 自己的說明句：「how close the calculated values of the frequencies agree with those observed」（p.209，Table VI 的說明句）。A2 的數字（RMS 0.86 c／最大 1.82 c／RMS 3.85 c／最大 10.9 c）經複核獨立重算通過，不動<br>**（2026-09-07 第二次引用複核推翻其中兩個 RMS：兩個最大值正確，但 0.86／3.85 是把掃描檔上糊掉的列當誤差 0 一起除的結果，已改為 0.99／3.81，見文末第二次修正記錄第 4 條）** |
| 6 | minor | §3.1 寫「引擎對每顆音**固定**給三根弦、總展寬 10.0 cents」，但三弦與 ±5 cents 都是**可覆寫的預設值**；這是 §4-B 容差理由①「物理地板」的立論基礎 | §3.1 改為「**本 corpus 的預設值**是每顆音三根弦、總展寬 10.0 cents」，並新增一段引用 `src/score/ScoreParser.h:78`、`src/engines/CimbalomEngine.h:65-66`、`src/cli/RenderApp.cpp` 的 `--num-strings`，明說「這不是寫死的常數」，且點出若 score 改變設定則該理由需重新評估。§4-B 理由① 同步改為「**在本 corpus 的預設設定下**……此為可覆寫預設值，非寫死常數」 |
| 7 | minor | §0 寫「連 **2026** 年的最新研究都還在這一關卡著」，但振幅側最新來源是 **2025** 年的 B3；唯一的 2026 年來源 C1 談的是頻率比值 | §0 第 3 點改為「連 **2025** 年的最新研究都還卡在這一關」，並補一句說明「本文件在振幅這一側查到的最新一篇就是這篇 2025；唯一的 2026 年來源 §2.4-C1 談的是頻率比值、不是振幅，而且方法學不足（§5-K6）」<br>（**2026-09-07 第二次引用複核再修**：D2 也是 2026 年來源，故該句已限定為「唯一的 2026 年『物理』來源」，見第二次修正記錄第 6 條） |
| 8 | minor | §0 通篇用 cents 與 RMS 下結論，卻從未定義這兩個詞；共同規約要求 §0 要讓月月看完就能選 | §0 在「一句話結論」之後、三層說明之前，新增一個「先講兩個從頭用到尾的單位／術語」小段，用非樂理語言定義 **cents**（一個半音 = 100 cents，所以 ±5 cents ≈ 半音的 1/20、0.86 cents ≈ 半音的 1/100）與 **RMS**（正負不互相抵銷的平均大小，並說明旁邊常一起寫的「最大值」是什麼） |

**本輪未處理、原樣留在 `open_items` 的事項**（不屬於這 8 條 findings）：
`docs/EXTERNAL_ANCHOR_SOURCES.md` §5.1 的「非消音室」更正（該檔不在本卡可動範圍）、
D4（KVR）僅由 WebFetch 摘要取得未逐字核對（文件內已標註）、
以及 §3.3 弦幾何偏差的 **R10 觸發**（維持只報告、不落地）。

---

## 裁決記錄（2026-09-08，規劃者依月月 2026-09-07 委託代決，月月可推翻）

- **選 B+**：立 partial **頻率**內部一致性 GATE（渲染 WAV vs `--dump-modes` 預測，容差沿用既有 ±5 cents）；
  **不立**振幅 GATE（外部找不到可溯源的容差，R2）；`B` 對真鋼琴 2.4～5.2 倍的偏差寫成**不當 GATE 的報告**。
- **前置 C10 的現況**：量測器自證得 1.1721 cents（> 1 cent），裁決包 `C10_selfcal_domain.zh-TW.md` 的 A/B 是月月的裁決項，
  規劃者**不代決**。在月月裁決前，partial 頻率工具以 **informational** 身分實作（不擋 CI、不宣稱 GATE）；
  月月選 A 即可翻成 GATE，選 B 則估計器重做後再翻。
- 本裁決包 §5-K8 指出 22 顆弱基頻音中 F♯6 未量、D7 屬另一類；A14 已判為引擎缺陷（見 A14 裁決記錄），
  修完 B-2 後這 22 顆要重量，partial 工具即為重量的工具。
- 落地：WF0908-P1 施工卡（`docs/workcards/WF0908_P1_partial_verify.md`）。
- 未處理：弦長／弦徑造成的 `B` 偏差（`StringModel::lengthFromMidiNote()` 0.35 m@A4、corpus 固定 diameter_mm=1.0）
  屬 R10 全 corpus 改動，留給月月另裁。

---

## 追補記錄（2026-09-08，第二位研究 Opus 獨立重跑本卡）

> 本卡在第一輪已完成並經引用複核與裁決。本輪由另一位研究 Opus **從零獨立重做一遍**，
> 目的是「不採信既有結論、親自把數字與來源再驗一次」。
> **本輪未改任何 `src/` `tools/` 檔案、未 build、未 commit、未動 §4 的任何選項或建議、
> 未動上方的「裁決記錄」。** 只做了下列兩件事：獨立複驗、以及一條來源等級的更正。

### 一、獨立複驗結果（全部一致，無異議）

本輪自行重建探針 score 並重跑 `--dump-modes`（同樣 A4/G5/G6、velocity 0.45、
steel、`diameter_mm` 1.0），再自行用最小平方法擬合 `f_n = n·F·√(1+B·n²)`：

| 項目 | 本輪獨立算得 | 文件既有值 | 判定 |
|---|---|---|---|
| A4 擬合 `B` | 1.361×10⁻³ | 1.361×10⁻³ | 一致 |
| G5 擬合 `B` | 4.321×10⁻³ | 4.321×10⁻³ | 一致 |
| G6 擬合 `B` | 1.728×10⁻² | 1.728×10⁻² | 一致 |
| G5 第二 partial 相對 2·f₁ | +11.10 cents | +11.10 cents | 一致 |
| G6 第二 partial 頻率／比值 | 3214.894 Hz／2.0503 | 3214.894 Hz／2.0503 | 一致（且與 `stem_verify` 實測 3214.9／2.0503 吻合） |
| A4/G5/G6 第一 partial 相對該音最大 partial | 0.0／−9.1／−10.9 dB | 同 | 一致 |
| 擬合殘差 | 三音皆 < 0.001 cents | — | `--dump-modes` 的 partial 完全就是該式的解，非近似 |

外部來源方面，本輪另行下載 **Fletcher 1964 全文（BYU 自存 PDF）**並獨立重算：

- Table VI 實心弦 No.54（f₁=581.5 Hz）可判讀的 6 組「calc vs obs」→ **最大 1.82 cents、RMS 0.99 cents**；
  纏繞弦 No.23 可判讀 14 組 → 最大 **10.92 cents、RMS 3.81 cents**。
  **最大值與文件原本的 1.82／10.9 吻合，但兩個 RMS 與文件原本的 0.86／3.85 不合**
  ——2026-09-07 第二次複核據此更正文件（見文末「複核修正記錄（2026-09-07，第二次引用複核）」第 4 條）。
- Table III（key 31）以其自報 `F=152.8`／`B=0.000444` 重算：partial 2–15 殘差在 **±1.1 cents** 內，
  n=16/17 為 −4.0／−9.6 cents（該表 `Δf/n³` 欄本身就顯示這兩列是離群值，
  與 Fletcher 自述「n>16 訊號太弱、觀測誤差大」相符）。
- Table IV（key 59）以 `B=0.00167` 重算 9 個 partial：**最大殘差 2.44 cents**——
  這獨立支持 §5-K1 對「0.00167 vs 0.000167 印刷不一致」的判定：改用 0.000167 時逐項殘差為
  0.97／4.65／11.95／20.88／32.79／45.98／58.59／80.49／**98.86** cents（n=1…9），
  **最大 98.9 cents 出現在 n=9**，不可能是原意。
  （**2026-09-07 第二次複核更正**：本段先前寫「暴增到 +80 cents」，80.49 其實是 n=8 的值，
  最大值在 n=9 的 98.86；證據檔 `r1_numbers_addendum.txt` 記的一直是「98.9 c」。K1 的結論不受影響。）

=> **§2 的來源、§3 的引擎數字本輪複驗通過，§4 的建議與容差出處本輪無異議。**
> **但有兩項不是「全部吻合」，2026-09-07 第二次複核已補揭露，請照這個範圍讀**：
> ① §2.2-A2 兩個 RMS（0.86／3.85）復現不出來，已更正為 0.99／3.81（上一小節）；
> ② 本輪證據檔 `output\wf0907\R1\fletcher_vs_engine_B.txt` 算出的引擎/真琴 `B` 比值是
> **1.31×(A4)／2.59×(G5)／5.86×(G6)**，與 §3.3、§0 的頭條 **2.46／2.44／5.17 不同**。
> 原因是兩種取「參考琴 `B`」的方法不同，**不是引擎數字有兩套**：
> - §3.3（**本文件採用、較可信**）：用 Fletcher 1964 **Table I 的逐鍵幾何**（弦徑 `d`、弦長 `l`）
>   代入該論文自己的式 `B = 3.95×10¹⁰·d²/(l⁴f₀²)`，A4/G5/G6 三鍵都有各自的 `d`、`l`。
> - 本輪證據檔：只用 Fletcher **實測到的少數幾個 `B`** 做 log 內插補到 A4 與 G6。
>   但 Fletcher 自己在 p.206 寫 Fig. 1 的 `B` 曲線有「**sudden breaks**」（弦徑跳號造成，
>   原句：「The sudden breaks in the curve are due to sudden changes in the gauge」，
>   並註明 key No. 58 是唯一的例外），log 內插跨過這些跳變並不合法，
>   因此該檔的 1.31／5.86 **不採用**，僅保留為過程記錄。G5（key 59）是唯一有實測值的一鍵，
>   兩法都用實測 `B`，差別只在取 1.67×10⁻³（實測平均）或 1.77×10⁻³（幾何式），比值 2.59 vs 2.44。
> **對結論無影響**：三個比值在兩種算法下都遠大於 1，§3.3「引擎 `B` 明顯偏大」與 §4-B+ 的建議不變。

### 二、一條更正：B1（Fletcher 1962）**已取得全文**，來源等級由 P2 升為 P1

第一輪把 Fletcher/Blackham/Stratton 1962 標為「403、未取得原文，只有摘要」。
本輪找到**作者機構（BYU 物理系）的公開自存 PDF**並完整讀完：
<https://physics.byu.edu/download/publication/1504>（索引頁 <https://physics.byu.edu/department/publications/fletcher>；
存取日期 2026-09-08）。

已更新的位置：§2.3-B1 列、§3.4 的兩處註記、§4 選項 C 的容差來源、§5-K3／K4、附錄 A 第 9 條。

**全文帶進來的三個新數字，方向與原結論一致、並使原結論更硬**：

1. **p.752**：「measure frequency with an accuracy of about 0.1%」——1962 年那套方法的
   partial 頻率量測精度約 **0.1%**。
   **2026-09-07 第二次複核更正**：本段先前把它換算成「≈17.3 cents」並據此推論
   「年代越早的量測精度越差，所以 ±5 cents 站得住」，**換算錯了十倍**——
   `1200·log₂(1.001) = 1.73 cents`（17.23 是 1% 的值）。
   1.73 cents 與 A1/A2 同量級，也小於 ±5，**這兩個推論在正確數字下都不成立，已刪除**。
   ±5 cents 的正當性只靠 §4-B 的三條理由（尤其 ① 三弦展寬的物理地板與 ② A2 的 0.99 cents），
   **不靠這一條**。
2. **p.761**：「A single partial above the fifth or sixth could be eliminated」——
   第五、六個以上的**單一 partial 整個拿掉都察覺不到**；
   「raised 4 or 5 db from its position in the series, it was distinctly noticeable」——
   抬高 **4～5 dB** 才明顯。**這是聽感門檻，不是量測精度。**
3. **p.761**：三個受測音「像鋼琴」的振幅斜率可接受區間為
   **Tone G″ 2.5→1.5**、**Tone G 13.0→5.0**、**Tone G₂ 40→7.5** dB/partial，
   中點分別是 **2／8／32** dB/partial。
   （**音名為本文件的正規化寫法**；文字層原樣殘缺，見 §2.3-B1 ④。）
   **2026-09-07 第二次複核更正**：本段與 §2.3-B1 先前把音名寫成「G♭ 音」「C♯ 音」
   （**原文全篇沒有這兩個音**），並把區間寬度寫成「**5～32 dB**」（**原文沒有這個數字、也推不出來**）。
   三個區間的實際寬度是 **1.0／8.0／32.5 dB**，已全部改正。

**對決策的影響：沒有改變，只是把選項 C 的否決理由從「查不到原文」換成
「原文查到了，但它給的是聽感門檻（4～5 dB 才察覺得到、第五六個以上的 partial 拿掉都察覺不到），
以及最寬達 32.5 dB 的『像鋼琴』區間；本專案不採信聽感（Rule 1）、
也不能拿這種寬區間當容差（R2）」。** §5-K4「找不到 partial 振幅量測重複性」的缺口
在讀完全文後**依然成立**。

### 三、本輪未做／不建議在本卡內做的事

- 未重跑 F♯6（§5-K8 的缺口維持原狀，屬 A14／WF0908-P1 範圍）。
- 未嘗試再取 Weinreich 1977、Conklin 1996 Part III 原文（本輪 WebFetch 對 `pubs.aip.org` 仍為 403）。
- Reddit 依然零條：本輪確認 `WebFetch` 對 `reddit.com`／`old.reddit.com` 回「unable to fetch」，
  `WebSearch` 對 `reddit.com` 網域回 400。**K2 維持成立。**
- 本輪順帶注意到 `docs/EXTERNAL_ANCHOR_SOURCES.md` §5.1 對揚琴那篇的「非消音室」記述
  與第一輪的更正意見一致（該檔不在本卡可動範圍，維持在 `open_items`）。

---

## 複核修正記錄（2026-09-07，第二次引用複核）

> 第二位引用複核 Opus 逐條打開原始來源、逐條重算數字後提出 **6 條 findings**（2 blocker、1 major、3 minor），
> 全部處理如下。**本輪未新增任何來源、未新增任何有利於本專案的數字主張；
> 所有改動都是「更正算錯的數字」「還原被寫錯的原文內容」或「補揭露兩份證據不一致」，方向一律是把主張變弱。**
> 本輪親自重讀了 `output\wf0907\R1\fletcher1962_quality.txt`（Fletcher 1962 全文抽取）與
> Fletcher 1964 全文抽取檔的 Table IV／Table VI／p.206 段落，並用 Python 重算每一個被質疑的數字，
> 逐項結果寫進 `output\wf0907\R1\r1_numbers_addendum.txt` 的「2026-09-07 第二次引用複核」段。
> **未改任何 `src/` `tools/` 檔案、未 build、未 commit。§4 的三個選項、建議與「裁決記錄」一字未動。**

| # | 嚴重度 | 複核指出的問題 | 本輪怎麼改 |
|---|---|---|---|
| 1 | **blocker** | §2.3-B1 ② 把 Fletcher 1962 p.752「accuracy of about 0.1%」換算成「≈17.3 cents」，**錯了十倍**（正確為 ≈1.73 cents）。這個錯數字撐起兩個推論：「遠差於 A1/A2」與追補記錄「年代越早精度越差，所以 ±5 cents 站得住」——在正確數字下兩者都不成立 | 兩處（§2.3-B1 ②、追補記錄 §二.1）全部改為 **≈1.73 cents**，並寫出算式 `1200·log₂(1.001)=1.730`、同時標明 `1200·log₂(1.01)=17.23` 是 1% 的值，明說錯在哪。**「遠差於 A1/A2」與「年代越早精度越差」兩句推論直接刪除**，改寫成「1.73 cents 與 A1/A2 同量級，**不能**用它論證早期量測較差」。並在追補記錄補一句：±5 cents 的正當性只靠 §4-B 的三條理由，**不靠這一條**。原文引述本身無誤（本輪在 `fletcher1962_quality.txt` 第 433 行逐字核對），故引述欄不動 |
| 2 | **blocker** | §2.3-B1 ④ 把 Fletcher 1962 p.761 的振幅斜率區間**寫錯了音名也寫錯了數值**：原文三個音是 **Tone G″／Tone G／Tone G₂**，文件寫成「G♭ 音」「C♯ 音」（原文全篇沒有這兩個音）；且宣稱「區間寬達 **5～32 dB**」，這個數字原文沒有、也推不出來 | 兩處（§2.3-B1 ④、§3.4 註）＋追補記錄 §二.3 全部改寫，照原文列出三個音與三個區間：**G″ 2.5→1.5**、**G 13.0→5.0**、**G₂ 40→7.5** dB/partial，中點 **2／8／32**；**「5～32 dB」整個刪除**，改為三個區間的**實際寬度 1.0／8.0／32.5 dB**。§2.3-B1 引述欄補上兩句原文：「Piano-like quality had limits from 40 to 7.5 db per partial」與「The midpoints on the limits of G″, G, and G₂」。§4 選項 C 的否決理由改為「聽感門檻 + 最寬達 32.5 dB 的區間」，**否決結論不變** |
| 3 | major | 追補記錄斷言「§2、§3 的數字本輪**全部**複驗通過」，但本輪自己列為證據的 `fletcher_vs_engine_B.txt` 給的比值是 **1.31／2.59／5.86×**，與 §3.3、§0 的頭條 **2.46／2.44／5.17×** 明顯不同（A4 差近一倍），文件與回報都沒揭露這個分歧 | 「全部複驗通過」改為「**§2 的來源、§3 的引擎數字本輪複驗通過**」，並緊接著加一段**明確揭露兩項不吻合**：① §2.2-A2 的兩個 RMS（見第 4 條）；② 兩種取「參考琴 `B`」方法的差異——**§3.3 的 Table I 逐鍵幾何法為本文件採用值**，`fletcher_vs_engine_B.txt` 的 **log 內插法不採用**，理由是 Fletcher p.206 自述 Fig.1 的 `B` 曲線有「sudden breaks」（弦徑跳號造成），內插跨過跳變不合法（本輪在 Fletcher 1964 全文第 425–434 行逐字核對該句）。附錄 B 也把該檔標為「**過程記錄，其比值不採用**」。並註明 G5（key 59）是唯一有實測 `B` 的一鍵，兩法差別只在 1.67×10⁻³ vs 1.77×10⁻³。**結論不變**：三個比值在兩種算法下都遠大於 1 |
| 4 | minor | §2.2-A2「纏繞低音弦 No.23 …… 16 個 partial：RMS **3.85** cents」復現不出來，且與本輪證據檔（14 組、RMS 3.81）不符 | 本輪重算後發現**問題比複核指出的更大**：0.86 與 3.85 都是**把掃描檔上糊掉／原文沒有 obs 的列當成「誤差 0」一起除**的結果（除以 8 得 0.858、除以 16 得 3.565——連 3.85 用這個方式也復現不出來），這種算法會讓一致度**假性變好看**。因此**兩個 RMS 一起改**為只算兩欄都可判讀的列：**No.54 = 6 組 → RMS 0.99 cents／最大 1.82 cents**；**No.23 = 14 組 → RMS 3.81 cents／最大 10.92 cents**。§2.2 表下新增一段註說明這個計數約定與更正理由，§0 白話段的「0.86」與「RMS 是什麼」的例子、§4-B 理由②、§4「容差數字的出處」那一行全部同步改為 **0.99**，並在 §0 加一句「算 RMS 時分母是幾筆很重要」。**兩個最大值（1.82／10.92）複核已獨立確認，不動。對結論無影響**：0.99 cents 仍遠優於 ±5 cents |
| 5 | minor | 追補記錄寫「0.000167 會使殘差暴增到 **+80 cents**」，與本輪證據檔的 98.9 cents 不一致（80.49 是 n=8 的值，最大值在 n=9） | 改為列出 `B=0.000167` 的**逐項殘差** 0.97／4.65／11.95／20.88／32.79／45.98／58.59／80.49／**98.86** cents（n=1…9），並明寫「**最大 98.9 cents 出現在 n=9**」，同時註明先前的 80.49 是 n=8 的值。**K1 的結論（0.00167 才是原意）不受影響**——本輪用 `B=0.00167` 重算最大殘差仍為 2.44 cents |
| 6 | minor | §0 稱「**唯一的 2026 年來源** §2.4-C1」，但同文件的 D2（Modartt 討論串）標的是 2026-01-04，也是 2026 年來源 | §0 該句改為「本文件唯一的 2026 年**物理**來源 §2.4-C1……；另有一條 2026 年來源 §2.5-D2，但那是**社群**貼文，不是物理證據」。D2 的日期（2026-01-04）與內容經前一輪複核確認無誤，不動 |

**本輪未處理、原樣留在 `open_items` 的事項**（不屬於這 6 條 findings）：
`docs/EXTERNAL_ANCHOR_SOURCES.md` §5.1 的「非消音室」更正（該檔不在本卡可動範圍）、
K2（Reddit 零條）、K3（Weinreich 1977／Conklin 1996 Part III 原文仍未取得）、
K8（F♯6 未量、D7 屬另一類）、以及 §3.3 弦幾何偏差的 **R10 觸發**（維持只報告、不落地）。

**對決策的淨影響：零。** 六條全部是引用與算術的準確性問題，
沒有一條動到 §4 的選項比較、建議（B+）或容差出處（±5 cents = 既有裁定門檻）。
第 1 條與第 2 條反而**刪掉了兩個原本被拿來替 ±5 cents 與「否決振幅 GATE」加分的錯誤論據**，
使這兩個結論改為只靠仍然成立的理由支撐。

---

## 追補記錄（2026-09-08，第三輪：第三位研究 Opus 獨立重跑本卡）

> 本輪目的：**獨立複驗**（不採信前兩輪自報）＋ 補齊卡上點名但先前缺席的來源。
> **未改任何 `src/` `tools/` 檔案、未 build、未 commit、未調任何容差。**
> 只跑了唯讀的 `--dump-modes`；本輪產生的證據檔在 `output\wf0907\R1\`（已 gitignore）。

### 一、引擎數字：逐項重算，全部一致

用同一支現成 binary 重跑同一份探針 score，輸出與前一輪的
`dump_modes_a4_g5_g6.txt`**逐位元組相同**（`diff` 無差異），再由該 JSON 重新算一次
§3.2／§3.3 的每一個數字（腳本輸出：`output\wf0907\R1\r1_thirdround_verify.txt`）：

| 複驗項 | 結果 |
|---|---|
| §3.2 三張表的 partial 頻率、`f_n/f₁`、`cents vs n·f₁`、`dB 相對最大 partial` | **逐格一致**（A4 −9.95→表列 −10.0、G5 p4 −9.63→−9.6 等，差異僅在四捨五入） |
| §3.2 的 `B` | 本輪改用 `r=(f₂/2f₁)²、B=(r−1)/(4−r)` 獨立反解：A4 **1.3608×10⁻³**、G5 **4.3211×10⁻³**、G6 **1.7284×10⁻²**；與文件的最小平方擬合值**一致到四位有效數字** |
| §3.3 幾何式 `(d_e/d_r)²·(L_r/L_e)⁴` | A4 **2.457**（文件 2.457）、G5 **2.439**（文件 2.441）、G6 **5.165**（文件 5.168）——差異 <0.1%，來自文件把弦長寫成 19.64／9.82 cm（四捨五入後再代入）。**結論不受影響** |
| Fletcher 實心弦式手算 key49 | **5.5337×10⁻⁴**（文件寫 5.53×10⁻⁴）✔ |
| 引擎弦長 | `0.35·2^(−半音差/12)` → A4 **35.00**／G5 **19.64**／G6 **9.82** cm ✔，並親自讀 `src/physics/StringModel.h:366` 確認該式與 0.35 m 基準 |
| §3.1 引用的三處程式行號 | 親自開檔確認：`src/score/ScoreParser.h:78` = `int numStrings = 3;`、`src/engines/CimbalomEngine.h:65-66` = `numStrings = 3` / `detuningCents = 5.0f` ✔（兩處的 `diameterMm` 預設值為 **0.8**，score 寫 1.0 屬覆寫，與文件敘述相容） |

### 二、外部引用：抽驗六條，逐字全中

| 條目 | 複驗方式 | 結果 |
|---|---|---|
| **A5** Tuovinen 2019 | 本輪重新 WebFetch 機構庫頁 | 原句為「a tuning close to that of a professional tuner is achieved with a deviation of 2.5 cents (RMS) between the keys A0 and G5 and 8.1 cents (RMS) between G#5 and C8, where the tuner's results are not very consistent」——**確認比較對象是「CRI 系統 vs 一位調音師」，第一次複核的更正正確** |
| **A3** Rigaud 2013 | 本輪重抓 PDF（作者自存版）並在本機抽出文字比對 | 「are in the range [10−5, 10−2]」✔；「truth of 0.33 % on synthetic samples and 0.76 % on real」✔ |
| **B1** Fletcher 1962 | 比對本機全文抽取檔 `fletcher1962_quality.txt` | 「the rate of 2 db per 100-cps increase」✔、「about 0.1%」✔、「or sixth could be eliminated」✔、「raised 4 or 5 db from its position in the series」✔、「Piano-like quality had limits from 40 to 7.5 db per」✔、「The midpoints on the limits of G", G, and G」＋U+FFFD＋「E. are」✔（末條的第三個音名為掃描 OCR 殘缺字元，其餘逐字相符） |
| **B2** Shah & Välimäki 2020 | 比對本機全文抽取檔 | 「third partial, every partial is of very low amplitude and can be neglected」✔ |
| **B3** Simionato & Fasciani 2025 | 本輪重新 WebFetch 期刊全文頁 | 「Results show the model matches the partial distribution of the target while predicting the energy in the higher part of the spectrum presents more challenges.」✔，年份 2025 ✔ |
| **D1** Modartt「Uneven partials」 | 本輪重新 WebFetch | 首帖日期 **25-10-2015** ✔；OP「the height of some partials does not coincide with those calculated」✔；Philippe Guillaume「There are no other controls for the partials height.」✔ |

**抽驗六條、零條不符。** 未抽驗到的條目（A1/A2 掃描判讀、A4、B4、C1、D2–D4）維持前兩輪的標示不變。

### 三、補齊卡上點名、先前缺席的來源

工作卡 §1-A 點名 **Galembo & Askenfelt 1999**、§1-A 點名 **Conklin 1996 Part I–III**、
§1-B 點名「**Pianoteq 的 inharmonicity 參數**」，前兩輪的文件裡：Galembo 完全沒有、
Conklin 只有 Part III、Pianoteq 只有論壇沒有官方文件。本輪處理：

**（新增，M 級＝商業產品官方文件）M1 — Modartt《Pianoteq User Manual》**
<https://www.modartt.com/user_manual?lang=en&product=pianoteq>（存取日期 2026-09-08，本輪 WebFetch 逐字取得）

- 原文①：「takes into account the inharmonicity of the strings」
- 原文②：「If `Harmonic stretching` is checked, then inharmonicity is ignored」

**這條能支持什麼、不能支持什麼（重要）**：它是**現售物理建模鋼琴的官方公開主張**，
證明「商業產品也把 partial 位置當成由弦的非諧性決定、而不是 `n·f₀` 的整數倍」——
與 §4 選項 B「驗 partial 頻率要對 `f_n = n·f₁·√(1+B·n²)`、不能對整數倍」方向一致。
**但它是廠商文件、不是量測報告，等級低於 P1／P2，不提供任何容差數字，
也不得被讀成「Pianoteq 的 partial 已被第三方驗證」。**

**（未取得，已列入 §5-K3 與附錄 A 第 22、23 條）**

- **Galembo & Askenfelt 1999**（IEEE Trans. SAP 7(2), 197–203）：IEEE 付費牆；本輪另搜
  KTH DiVA 等自存版本**沒有找到**。→ **未取得原文，本文件不引用其任何內容。**
- **Conklin 1996 Part I／II**：Part I 的 `article-pdf` 直連本輪回 **HTTP 403**，Part II 付費牆。
  → **未取得原文。**（Part III 前兩輪即為付費牆，狀態不變。）

### 四、對決策的淨影響：零

本輪沒有推翻任何數字、沒有改任何容差、沒有改 §4 的三個選項或建議（**B+**），
也沒有改「容差出處 = ±5 cents 既有裁定門檻」那一行。
新增的 M1 只是替選項 B 的**方向**多一條旁證；新記錄的兩項「未取得原文」則是
把 §5-K3 的缺口寫得更完整——**缺口變大不是壞事，是把先前沒說的話補上。**

### 五、本輪未做

- 未量 F♯6／D7 的**渲染實測**主導頻率（§5-K7／K8 的缺口原樣保留）：那需要渲染 WAV + FFT，
  屬選項 B 的工程或 A14／C13 的範圍，本研究卡不做。
- 未動 `docs/EXTERNAL_ANCHOR_SOURCES.md` §5.1 的「非消音室」更正（該檔不在本卡可動範圍，
  留在 `open_items`）。
- 未取得 Reddit（環境封鎖，§5-K2 不變）。

---

## 追補記錄（2026-09-08，第四輪：第四位研究 Opus 獨立重跑本卡）

> 本輪目的與前三輪相同：**不採信既有結論，親自把引擎數字與外部來源再驗一次**，
> 並優先去補前三輪自己列出來的缺口（K2、K7、K8）。
> **未改任何 `src/` `tools/` 檔案、未 build、未 commit、未調任何容差、未動 §4 的三個選項與建議、
> 未動「裁決記錄」與前三輪的兩份「複核修正記錄」**（那些是歷史紀錄，照原文保留，
> 因此它們段落內仍寫「2.4～5.2 倍」——那是當時的正確值，不是本輪漏改）。
> 本輪只跑了唯讀的 `--dump-modes`；證據檔在 `output\wf0907\R1\`（已 gitignore）。

### 一、把 K8 的缺口補掉一半：第一次跑出 F♯6 與 D7 的模型預測

前三輪都只跑 A4/G5/G6，`§5-K8` 因此寫著「F♯6 從未被量過」。
本輪自建五顆音探針 score（`r1_r4_probe.score.json`，同樣 velocity 0.45、steel、`diameter_mm` 1.0、
reverb wet 0）跑 `--dump-modes`，結果：

| 音 | 擬合 `B` | 最大 partial 落在 | 與既有實測的關係 |
|---|---|---|---|
| **F♯6**（MIDI 90） | 1.540×10⁻² | **n=2**（3026.538 Hz、比值 2.0450） | 與 G5／G6 同型；**但 F♯6 至今仍沒有任何渲染實測數字**，只補上模型側 |
| **D7**（MIDI 98） | 3.880×10⁻² | **n=1**（基頻本身） | **模型預測與 `stem_verify` 乾聲實測「主導即基頻 +4.7 cents」方向一致**，獨立支持「D7 是另一類問題」的既有判定 |

=> `§5-K8` 由「F♯6 完全未知」收斂為「F♯6 只有模型側、缺實測側」；**K7 的性質不變**
（全部仍是模型預測，沒有對渲染 WAV 做 FFT）。

### 二、把 §3.3 的 `B` 對照從三顆擴到五顆，並更正一句話

用 Fletcher 1964 **Table I** 的 key 70（`d`=0.085 cm、`l`=14.35 cm）與 key 78（`d`=0.084 cm、`l`=9.15 cm），
代入該論文自己的實心弦式 `B = 3.95×10¹⁰·d²/(l⁴f₀²)`：

| 音 | 引擎 `B` | 參考琴 `B` | 引擎/真琴 | 幾何預測式 `(d_e/d_r)²·(L_r/L_e)⁴` |
|---|---|---|---|---|
| A4 | 1.361×10⁻³ | 5.53×10⁻⁴ | 2.459× | 2.457 |
| G5 | 4.321×10⁻³ | 1.77×10⁻³ | 2.442× | 2.441 |
| **F♯6** | **1.540×10⁻²** | **3.07×10⁻³** | **5.011×** | **4.998** |
| G6 | 1.728×10⁻² | 3.34×10⁻³ | 5.169× | 5.167 |
| **D7** | **3.880×10⁻²** | **7.20×10⁻³** | **5.386×** | **5.364** |

兩顆新音同樣被弦幾何**完全解釋**（差 <0.5%），沒有出現第三種機制。

**本輪的一項更正**：§3.3 原本寫「引擎 G6 的 `B` 超出 A3 所述典型範圍上界 10⁻²（A4/G5 仍在範圍內）」，
**這句話在只有三顆音時成立，擴到五顆後不完整**——實際上 **F♯6（1.54×10⁻²）／G6（1.73×10⁻²）／
D7（3.88×10⁻²）三顆都超界**，D7 超出上界近 4 倍。已改。
連帶 §0 與全文「範圍」寫法由 **2.4～5.2 倍**改為 **2.4～5.4 倍**（下界 2.44 未變，上界由 5.17 變 5.39）。

**這對 A14 的意義（本文件仍不做判定，只提供輸入）**：偏差不是只在 G6 那一顆爆掉，
而是**沿著音高單調變大**（2.46 → 2.44 → 5.01 → 5.17 → 5.39），
與「引擎弦長基準 0.35 m 偏短 + score 固定 1.0 mm 弦徑」這兩個建模選擇的方向完全吻合。

### 三、新增一條 P1 外部來源（B8），並用它替兩個既有結論加一條獨立佐證

`WebSearch` 過程中撞見一篇前三輪沒有的開放取用論文，本輪親自 WebFetch 兩次確認：

**B8 — Simionato, Fasciani & Holm (2024), *Physics-informed differentiable method for piano modeling*,
Frontiers in Signal Processing 3, DOI 10.3389/frsip.2023.1276748**
（<https://www.frontiersin.org/journals/signal-processing/articles/10.3389/frsip.2023.1276748/full>，
存取日期 2026-09-08）

- 頻率側：「a max value of 4.46 ⋅ 10–1」（Sec. 5，指**第一 partial** 的平均 cent 偏差，
  即 **0.446 cents**；作者自評相對半音 100 cents「可視為感知上可忽略」）
  → **替 §4-B 的容差理由② 補一條現代數字**：1964 年的 0.99 cents 與 2024 年的 0.446 cents
  同樣遠優於 ±5 cents，所以沿用 ±5 不是放水。
- 振幅側：「The models accurately predict the first nine partials」、
  「the generation of partials is less accurate」（高頻段，高 velocity 尤甚）、
  「a slight underestimation of the decay time for the higher partials」
  → **全部是定性描述，沒有任何可當門檻的 dB 數字**。這是「連 2024 年的論文在振幅側也只敢定性」的
  第二個獨立佐證（第一個是既有的 B3，2025 年），**§4 選項 C（振幅 GATE）的否決理由更硬**。

注意這是**同一組作者**的另一篇（B3 是 2025 年那篇），兩篇互為佐證但**不是獨立團隊**——這一點必須揭露。

### 四、K2（Reddit）第三度確認仍然取不到

本輪自己試：`WebFetch` 對 `old.reddit.com` 回「Claude Code is unable to fetch」；
另用**不限網域**的一般關鍵字搜尋（"reddit r/piano inharmonicity partials high treble synthesized piano sounds fake"），
回傳的 8 條連結**沒有任何一條是 reddit.com**。
=> **K2 維持成立，Reddit 依然零條。**

### 五、既有數字的獨立重算：全部一致

用同一支現成 binary、自建的新探針 score 重跑後重算（`output\wf0907\R1\r4_numbers.txt`）：

| 複驗項 | 本輪結果 | 文件既有值 | 判定 |
|---|---|---|---|
| A4／G5／G6 擬合 `B` | 1.36106×10⁻³／4.3211×10⁻³／1.72844×10⁻² | 1.361×10⁻³／4.321×10⁻³／1.728×10⁻² | 一致 |
| 同上，改用閉式 `B=(r−1)/(4−r)`（`r=(f₂/2f₁)²`）反解 | 1.36081×10⁻³／4.32113×10⁻³／1.72844×10⁻² | — | 與擬合值一致到四位有效數字 |
| 擬合殘差 | 五顆音皆 < 0.0005 cents | 「< 0.001 cents」 | 一致 |
| §3.2 三張表的頻率／比值／cents／dB | 逐格重算 | — | 一致（差異僅四捨五入） |
| 三弦 f₁ 叢集總展寬 | 五顆音**皆為 10.00 cents** | 10.0 cents | 一致 |
| 引擎弦長 `0.35·2^(−(midi−69)/12)` | A4 35.00／G5 19.64／G6 9.82／F♯6 10.41／D7 6.56 cm | 前三顆同 | 一致（並親自讀 `src/physics/StringModel.h:366` 確認該式） |
| Fletcher 實心弦式 key 49 | 5.534×10⁻⁴ | 5.53×10⁻⁴ | 一致 |
| Fletcher 1964 Table I 的 key 49/59/70/71/78 | 本輪重新下載該 PDF、用 PyMuPDF 自行抽取文字逐格核對 | — | 一致 |

### 六、本輪未做

- 未對任何音做**渲染 WAV 的 FFT 實測**（K7 不變；F♯6 的實測缺口仍在，屬選項 B／C13 的工程）。
- 未再嘗試 Weinreich 1977、Conklin 1996 Part I–III、Galembo & Askenfelt 1999、Rauhala 2007 的原文
  （前三輪已逐一確認付費牆／403，本輪不重複耗時；K3 維持原狀）。
- 未動 `docs/EXTERNAL_ANCHOR_SOURCES.md` §5.1 的「非消音室」更正（該檔不在本卡可動範圍，留在 `open_items`）。
- **未改變 §4 的任何選項、建議（B+）或容差出處那一行。** 本輪對決策的淨影響：
  **建議不變，但支撐 B+ 的證據更強（B8 的 0.446 cents），反對選項 C 的理由也更強（B8 振幅側只有定性）**；
  同時把「偏差只在 G6 一顆爆掉」這個可能誤導 A14 的印象更正為「沿音高單調變大、三顆超界」。

---

## 複核修正記錄（2026-09-09，WF0908-P5）

> 卡：`docs/workcards/WF0908_P5_research_cleanup.md` §1 的 R1 那一列
> （「B1 標『未取得原文』，但 BYU 機構庫 scholarsarchive.byu.edu 可能有全文 → 試抓」）。

| # | finding | 處理 |
|---|---|---|
| 1 | B1（Fletcher, Blackham & Stratton 1962《Quality of Piano Tones》）被標為「未取得原文」，應試 BYU 機構庫 | **finding 已不成立（前一輪已處理），但本輪仍照卡跑了一次獨立驗證**。B1 早在 **2026-09-08 追補輪**就升級為 **P1**，全文取自 **BYU 物理系自存 PDF** <https://physics.byu.edu/download/publication/1504>，振幅側 dB 敘述（②③④）也已寫進 §2.3-B1。本輪的新增值只有兩項：(a) 補跑卡上指名的 `scholarsarchive.byu.edu` 管道並記錄結果（見下）；(b) 自己重下 PDF 重新核對引述，並補上一條 OCR 誠實註記（見下） |

### (a) 卡上指名的 `scholarsarchive.byu.edu` 管道：**查無**

- 試過的 URL：`https://scholarsarchive.byu.edu/do/search/?q=Quality%20of%20Piano%20Tones&start=0&context=52055`
  → **HTTP 500 Internal Server Error**（存取 2026-09-09）。
- 另以 `WebSearch` 查 `scholarsarchive.byu.edu Fletcher Blackham Stratton "Quality of Piano Tones"`
  與 `"Quality of Piano Tones" Fletcher 1962 full text PDF byu`（皆 2026-09-09）：
  **兩次都沒有任何 `scholarsarchive.byu.edu` 的命中**；BYU 端唯一命中的一律是 `physics.byu.edu`
  （`/download/publication/1504` 與索引頁 `/docs/publication/1503`）。
- **結論**：`scholarsarchive.byu.edu` 上**查不到**這篇；本文件已在用的 `physics.byu.edu` 就是 BYU 的自存路徑，
  兩者是不同系統，**沒有更好的來源可換**。出版社頁 <https://pubs.aip.org/asa/jasa/article-abstract/34/6/749/600921/> 維持 403。

### (b) 本輪自己重下 PDF、重新核對（不是沿用 2026-09-08 的抽取檔）

- 重新下載 <https://physics.byu.edu/download/publication/1504>（2026-09-09），
  本機檔 **SHA256 `45dae554ab9c24520b854bd8f6d55e3f14f2d511044afd2984d877b5b4f44128`**、**13 頁**，
  以 PyMuPDF 自行抽字層後逐字 `find`，**§2.3-B1 引述欄的六句全部命中**：
  「decrease in level at the rate of 2 db per 100-cps increase」（摘要）、
  「measure frequency with an accuracy of about 0.1%」、
  「A single partial above the fifth or sixth could be eliminated」、
  「raised 4 or 5 db from its position in the series」、
  「Piano-like quality had limits from 40 to 7.5 db per partial」、
  「The midpoints on the limits of G", G, and G」＋ **U+FFFD** ＋「E. are」
  （**逐字**：直引號、第三個音名含一個抽不出的 U+FFFD 替換字元）。
  三個振幅斜率區間 **2.5→1.5／13.0→5.0／40→7.5 dB/partial** 亦逐格命中。
- **新增的一條誠實註記**：三個小節的**標題**在文字層讀作 `Tone G"`／**`Tone Cs`**／`Tone G`＋U+FFFD＋`E.`，
  中間那個是 OCR 殘缺（結語句寫的是 `G`）。§2.3-B1 ④ 已就地補註：**音名以結語句為準，不以小節標題為準**。
  這一條只影響「音名怎麼抄」的可稽核性，**不影響任何數字，也不影響 §4 的任何結論**。
- 附帶：`WebFetch` 對這個 PDF 本身**無法讀出內文**（回報掃描檔文字層破碎），
  **可用的路徑是「先下載、再自己抽字層」**——這一點記在這裡供後續複核員省時間。

### 本輪沒有做的事

- **§4 的選項、建議（B+）、容差來源那一行，一個字都沒動。**
- **§2／§3 的任何數字都沒動**；未新增任何來源（`sources_count` 不變）。
- 未再嘗試 Weinreich 1977、Conklin 1996 Part I–III、Galembo & Askenfelt 1999、Rauhala 2007
  （前幾輪已確認付費牆／403，K3 維持原狀）。
- 未動 `docs/EXTERNAL_ANCHOR_SOURCES.md`（屬 WF0908-P4 範圍）。
- 未碰 `src/`、`tools/`、`tests/`；未跑 cmake、未渲染音訊、未 `git add`／`commit`／`push`。
  動筆前備份在 `output/wf0908/P5/A13_partial_gate_domain.zh-TW.md`。

---

## 追補記錄（2026-09-09 第二次，WF0908-P5 修正回合）

> 只改 §2.3-B1 那一列的「音名寫法」相關文字（含引述欄）＋ §3.4 註／附錄逐句核對段的兩處標註；
> **§2／§3 的任何數字、§4 的任何結論與選項都沒有動，來源數不變。**

| # | 嚴重度 | finding | 處理 |
|---|---|---|---|
| 1 | minor | 上一輪在 §2.3-B1 補了「小節標題 OCR 殘缺、音名以 p.761 結語句為準」的誠實註記，**但同一列宣稱逐字的「≤15 字原文引述」欄仍寫著 「The midpoints on the limits of G″, G, and G₂」**——兩者不同步；而且引述欄的第三個音名 `G₂` 是本文件自訂的正規化寫法，**不是文字層原樣** | **已改**。引述欄改為 「The midpoints on the limits of G", G, and」（直引號、**逐字**），並註明「緊接其後的第三個音名在文字層是 U+FFFD 殘字，**引述在此截斷、不補寫**」。同欄另一句 「Piano-like quality had limits from 40 to 7.5 db per partial」 的括號改為註明該小節標題在文字層作 `Tone G`＋U+FFFD＋`E.`，非本文件寫的 `G₂` |
| 2 | 連帶 | §2.3-B1 ④ 原本寫「原文音名為 **Tone G″／Tone G／Tone G₂**」，等於宣稱那是原文寫法 | **已改**為明說：**這三個是本文件的正規化寫法**；文字層原樣為——結語句 `The midpoints on the limits of G", G, and G` ＋ **U+FFFD** ＋ `E. are, respectively, 2, 8, and 32 db per partial`，小節標題 `Tone G"`／`Tone Cs`／`Tone G`＋**U+FFFD**＋`E.`；並寫明音名歸屬以結語句順序為準（中點 2／8／32 dB 依序對上 2.5→1.5／13.0→5.0／40→7.5） |
| 3 | 連帶 | §3.4 註與附錄逐句核對段也用 `G″／G／G₂`，未標明是正規化寫法；且附錄兩處把殘字寫成 `•.`（自造符號） | **已改**。兩處加上「音名為本文件正規化寫法，見 §2.3-B1 ④」的括號；殘字一律改寫成明示的 **U+FFFD** |

**本輪自己重跑的驗證（存取／核對日 2026-09-09）**：
用上一輪自行下載的同一份 PDF 之文字層 `output/wf0907/R1/fletcher1962_quality.txt` 逐字 `find`，
p.761 結語句與三個小節標題的原樣與上表所寫**完全一致**（第三個音名在兩處都是同一個 U+FFFD 殘字，
中間那個小節標題另外被 OCR 讀成 `Cs`）。三個振幅斜率區間 **2.5→1.5／13.0→5.0／40→7.5 dB/partial** 逐格命中，未改。

**本輪的邊界**：只改本 `.md`；未碰 `src/`、`tools/`、`tests/`；未跑 cmake、未渲染音訊、未 `git add`／`commit`／`push`。
動筆前備份在 `output/wf0908/P5_fix/A13_partial_gate_domain.zh-TW.md`。
