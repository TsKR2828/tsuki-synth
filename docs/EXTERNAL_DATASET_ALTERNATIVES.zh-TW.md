# 外部聲學資料集替代方案調查 —— 找「可商用」的真實樂器對照資料

> 建立：2026-09-09　　本文所有外部來源的**存取日期一律為 2026-09-09**（另有註明者除外）
> 起因：月月 2026-09-09 指示「看一下有沒有其他資料集參考，沒有的話先私下對照參考」
> 前一份相關文件：`docs/EXTERNAL_DATASET_A8.zh-TW.md`（TU Berlin 資料集的下載與授權查證）
> **本文件不改任何程式碼、不改任何容差、不宣稱任何「模型與實測吻合」。**
> 本文件也**沒有下載任何新資料**，只做授權與內容查證。

---

## §0 一句話結論（白話版）

**找到了替代品，但不是原本想要的那一種。**

想要的是「**有拿校準器量過、知道真實有多少分貝**」而且「**可以拿去賣**」的樂器錄音——
**這種東西不存在，我翻遍了都沒有，數量是 0。**

但是找到了兩個**很有用的替代路線**：

1. **要「有多大聲」的絕對數字** → 有一篇 2018 年的期刊論文（Weinzierl 等人，登在美國聲學學會期刊），
   它**是 CC BY 4.0，可以商用**，而且它**確實用了校準器**（B&K 4230 活塞發聲器，94 分貝 @ 1 千赫）。
   論文裡有一張表，列了 **40 種樂器最小聲到最大聲各是幾分貝**，裡面**有定音鼓、豎琴、吉他**。
   → 它是「**紙上的數字表**」，不是聲音檔。但數字表就是我們要的東西，而且合法可商用。
   ※ 有趣的是：這篇 CC BY 論文，跟我們手上那份**禁商用**的 TU Berlin 資料集，是**同一批量測**。
     也就是說：**聲音檔不能商用，但論文裡整理好的數字可以。**

2. **要「聽起來像什麼、衰減多久、泛音落在哪」** → **愛荷華大學樂器樣本庫（Iowa MIS）**最好用。
   它寫明「**可以用在任何專案，沒有限制**」，而且**有鑼、有大鑼（tam-tam）、有泰國鑼、有鋼琴單音**，
   還把**麥克風型號、離多遠、在不在無響室**都列出來了。**這是本次調查最推薦的一個。**
   缺點：**它沒有校準**，只知道「相對大小聲」，不知道「絕對幾分貝」。

**另外三件月月需要知道的事：**

- 目前 repo 用的 **TU Berlin 資料集確實是禁商用**（CC BY-NC-SA），我重新查證過一次，
  結論和 `EXTERNAL_DATASET_A8.zh-TW.md` 一樣。**維持「只私下對照參考、不進產品」的做法是對的。**
- **揚琴／鋼舌鼓／handpan 完全沒有公開可商用的量測資料**。一個都沒有。這是硬缺口，只能自己量或自己錄。
- 學術網站 **Zenodo 在 2026-09-09 當天整站掛掉（504）**，有三筆資料我只能透過別的管道拿到授權欄位，
  沒能親眼看到它們自己的網頁。這幾筆我都標成「**未取得原文**」，不當定論。

---

## §1 逐候選表

### 1.0 看表前先看這裡：欄位是什麼意思

| 欄位 | 白話解釋 |
|---|---|
| **是否校準絕對聲壓** | 有沒有用「校準器」（一個會發出已知大小聲的小罐子）對過，讓錄音檔裡的數字能直接換算成真實的分貝。**沒有校準 = 只知道相對大小聲，不知道絕對大小聲。** |
| **商用可否** | 我們把 TsukiSynth 拿去賣的時候，能不能合法用它。「NC」= NonCommercial = 禁商用。 |
| **對哪個引擎有用** | `FMPianoEngine`＝鋼琴；`CimbalomEngine`＝揚琴；`ChromaticEngine` 底下有 `TongueDrum`（鋼舌鼓，用梁模型）和 `WaterGong`（水鑼，用圓板模型）。 |
| **分級** | **A**＝可商用＋有校準＋有我們要的樂器（理想）｜**B**＝可商用、內容有用、但沒校準｜**C**＝授權不明或有疑慮｜**D**＝禁商用或內容無關 |

---

### 1.1 【B+ 最推薦】University of Iowa Musical Instrument Samples（愛荷華大學 MIS）

| 項目 | 內容 |
|---|---|
| **內容** | 單音錄音，逐半音，每個音有 pp／mf／ff 三種力度。1997 年起持續累積。 |
| **樂器（跟我們有關的）** | **鑼／大鑼**：20 吋 wind gong、22／28／40 吋 tam-tam（各 pp/mf/ff＋弓拉版）、**泰國鑼 C4–C5 逐半音**（有音高！）<br>**鋼琴**：Steinway & Sons model B，A0–C8 全音域，pp／mf／ff<br>另有 marimba、vibraphone、crotales、cymbals 等 |
| **是否校準絕對聲壓** | **未校準。** 全站沒有任何校準器／Pa／dB SPL 的敘述。<br>但有一句重要的：錄音時「input volume levels were not changed during the recording session」→ **同一場錄音內的相對大小聲是可信的**，只是沒有絕對基準。 |
| **器材／距離（有記錄！）** | 鑼／大鑼：無響室、**5 feet**（約 1.52 m）、Earthworks QTC40、Metric Halo 2882、24-bit 44.1 kHz stereo、2013-03-20、演奏者 Andrew Thierauf<br>鋼琴：**非**無響室（`stereo, non-anechoic recording`），Neumann KM 84，左麥在低音弦上方 8 吋、右麥在高音弦上方 8 吋，16-bit 44.1 kHz |
| **授權原文** | 「may be downloaded and used for any projects, without restrictions」<br>（<https://theremin.music.uiowa.edu/MIS.html>，2026-09-09） |
| **商用可否** | **可以。** 但注意：這是**網頁上的一句聲明**，不是正式授權書（沒有 CC 標章、沒有 LICENSE 檔）。<br>→ 建議存證：把該頁存成 PDF ＋ 記下存取日期，萬一日後改口有依據。 |
| **對哪個引擎有用** | `ChromaticEngine::WaterGong`（大鑼＋泰國鑼，**泰國鑼有音高，最適合對照模態頻率**）<br>`FMPianoEngine`（鋼琴逐半音三力度 → 可量 inharmonicity B 與 T60）<br>`ChromaticEngine::TongueDrum` **無直接對應**（沒有鋼舌鼓） |
| **分級** | **B+**（若不是缺校準，這會是 A） |

---

### 1.2 【A：唯一可商用的「校準」來源，但是紙上的數字表不是聲音檔】Weinzierl et al. 2018, JASA

| 項目 | 內容 |
|---|---|
| **正式名稱** | Weinzierl, S., Lepa, S., Schultz, F., Detzner, E., von Coler, H., Behler, G. (2018).<br>“Sound power and timbre as cues for the dynamic strength of orchestral instruments,”<br>*J. Acoust. Soc. Am.* 144(3), 1347–1355. DOI: `10.1121/1.5053113` |
| **內容** | **TABLE I：40 種樂器的「聲功率位準」（LW，單位分貝）**，分成 pp 最小值、ff 最大值、以及加權平均。 |
| **樂器（跟我們有關的）** | **Timpani（定音鼓）**：Hand crank 型 ff 最大 108 dB／pp 最小 60 dB；Pedal 型 108／58<br>**Harp（豎琴）**：91／54　**Guitar（吉他）**：88／59<br>（**沒有**鋼琴、**沒有**鑼、**沒有**揚琴——它是管弦樂團編制） |
| **是否校準絕對聲壓** | **是，有明確原文證據。**<br>「a pistonphone calibrator (B&K 4230, 94 dB @ 1 kHz) was used」<br>量測法：ISO 3745 包絡面法，32 顆 Sennheiser KE4-211-2 麥克風，半徑約 **r = 2.1 m** 的準球面陣列，TU Berlin 無響室（V = 1070 m³，下限頻率 63 Hz） |
| **授權原文** | 「licensed under a Creative Commons Attribution (CC BY) license」（論文首頁版權列，PDF 第 1 頁）<br>Crossref 交叉驗證：`license = https://creativecommons.org/licenses/by/4.0/`（content-version: vor） |
| **商用可否** | **可以（CC BY 4.0，只要標示出處）。** |
| **對哪個引擎有用** | `RadiationModel` / 全域響度合理性檢查。<br>**Timpani 是「被敲的樂器」**，最接近我們的舌鼓／鑼在能量級數上的量級。 |
| **重要提醒（不要搞混）** | 表裡是**聲功率位準 LW**（樂器總共放出多少聲功率），**不是**「站在幾公尺外聽到幾分貝」（那叫聲壓位準 Lp）。<br>兩者換算需要量測面積，**不能直接拿去跟我們算出來的 Pa 或 Pa/N 比大小**。<br>它能回答的是：「我們的數量級有沒有離譜」——**不能證明模型正確**。 |
| **分級** | **A**（但它是論文表格，不是可下載的資料集） |
| **取得方式** | TU Berlin DepositOnce 開放全文 PDF：<br><https://api-depositonce.tu-berlin.de/server/api/core/bitstreams/d7d0f7af-e49b-4b86-8e7d-4293aef0440a/content>（約 1 MB，已於 2026-09-09 成功取得） |

---

### 1.3 【A− 同一批人的第二篇 CC BY 論文】Ackermann et al. 2024, JASA

| 項目 | 內容 |
|---|---|
| **正式名稱** | Ackermann, D., Brinkmann, F., Weinzierl, S. (2024). “Musical instruments as dynamic sound sources,” *J. Acoust. Soc. Am.* DOI: `10.1121/10.0025463` |
| **是否校準絕對聲壓** | **是（沿用同一套校準流程）**：「The calibrated single-tone directivities in the dynamic range of fortissimo」 |
| **授權原文** | 「licensed under a Creative Commons Attribution (CC BY) license」（PDF 版權列）<br>Crossref 交叉驗證：`https://creativecommons.org/licenses/by/4.0/` |
| **商用可否** | **可以（CC BY 4.0）。** |
| **關鍵限制** | 「The data supporting the findings of this study are available from the corresponding author on reasonable request.」<br>→ **論文文字與圖表可商用，但底層資料要寫信要**，而且要到的資料很可能又回到 CC BY-NC-SA 的那份。 |
| **分級** | **A−**（可用，但資料不公開） |

---

### 1.4 【B 可商用、鋼琴專用】Salamander Grand Piano v3

| 項目 | 內容 |
|---|---|
| **內容** | Yamaha C5 平台鋼琴多重取樣。**16 段力度層**，**每小三度取樣一個音**（不是逐半音）。<br>另有 hammer noise（榔頭雜音）逐半音、string resonance（弦共振）三層。 |
| **是否校準絕對聲壓** | **未校準。** |
| **器材／距離（有記錄）** | 「Two AKG c414 disposed in an AB position ~12cm above the strings.」48 kHz / 24-bit |
| **授權原文** | 倉庫 `LICENSE` 檔第 1–3 行：「Creative Commons Legal Code / Attribution 3.0 Unported」<br><https://raw.githubusercontent.com/sfzinstruments/SalamanderGrandPiano/master/LICENSE>（2026-09-09） |
| **商用可否** | **可以（CC BY 3.0，需標示 Alexander Holm）。** |
| **對哪個引擎有用** | `FMPianoEngine`。**16 段力度層**是它勝過 Iowa（只有 3 段）的地方，適合看「敲得越用力，泛音怎麼變」。 |
| **下載大小** | GitHub 倉庫約 **714 MB**（GitHub API 回報 730,959 KB，2026-09-09） |
| **分級** | **B** |

---

### 1.5 【B 可商用、公有領域】Versilian Community Sample Library（VCSL）

| 項目 | 內容 |
|---|---|
| **樂器（跟我們有關的）** | **Gong 1**（7 檔，29.3 MB，力度 p/mf/f/fff＋scrape）、**Gong 2**（6 檔，2.4 MB）<br>**Slit Drum**（＝木製 log drum，6 檔，1.4 MB，Hi／Lo 各 3 velocity）<br>**Grand Piano, Steinway B**（352 檔，1,277.7 MB，逐半音 × vl2/vl3/vl4）、Grand Piano Kawai、Upright Piano Yamaha／Knight<br>Kalimba／Mbira（21.3 MB，**懸臂梁振動，跟舌鼓的舌片同一類物理**）、Balafon、Marimba、Vibraphone、Tubular Bells |
| **是否校準絕對聲壓** | **未校準。** 且鋼琴部分**連相對音量都被破壞了**：<br>「The sustain and non-sustain articulations for this instrument have been normalized.」<br>（`Chordophones/Zithers/Grand Piano, Steinway B/NORMALIZED.txt`，2026-09-09）<br>→ **正規化只改「整體音量」，不改「衰減速度」與「泛音頻率」**，所以 T60 與 inharmonicity 還是可以量，但**跨力度的音量比較不能用**。 |
| **器材／距離** | **無記錄。** 倉庫沒有麥克風型號或距離的說明檔。 |
| **授權原文** | 倉庫 `LICENSE` 檔第 1–3 行：「Creative Commons Legal Code / CC0 1.0 Universal」<br>README：「you can do whatever you want with these sounds (even make commercial software)」<br><https://github.com/sgossner/VCSL>（2026-09-09） |
| **商用可否** | **可以（CC0＝等同公有領域，連署名都不用）。這是本次調查授權最寬鬆的一個。** |
| **對哪個引擎有用** | `WaterGong`（Gong 1/2，但**無音高標示**）、`FMPianoEngine`、`TongueDrum`（Kalimba/Mbira 當梁模型旁證；Slit Drum 是**木**的不是**鋼**的，只能當形狀類比） |
| **下載大小** | 全庫約 **5,875 MB**；只抓 Gong 1＋Gong 2＋Slit Drum 約 **33 MB** |
| **分級** | **B** |

---

### 1.6 【B− 可商用但有轉售限制】Philharmonia Orchestra Sound Samples

| 項目 | 內容 |
|---|---|
| **樂器（跟我們有關的）** | 打擊組含 **tam-tam** 與 **Thai gong**（依 Philharmonia 官方樂器頁與樣本頁分類） |
| **是否校準絕對聲壓** | **未校準**，且**完全沒有器材／距離記錄**。 |
| **授權原文** | 「You are free to use these samples as you wish, including releasing them as part of a commercial work.」<br>限制：「they must not be sold or made available 'as is'」<br><https://philharmonia.co.uk/resources/sound-samples/>（2026-09-09） |
| **商用可否** | **可以**，但**不可以把樣本本身當商品賣、也不可以原封不動再散布**。<br>→ 拿來當「私下對照的耳朵參考」完全沒問題；**不要把檔案放進 repo 或安裝包**。 |
| **對哪個引擎有用** | `WaterGong` |
| **分級** | **B−**（缺器材記錄，且散布受限） |

---

### 1.7 【B− 有鑼的模態量測，但授權欄位空白】BYU Spatial Audio Library — Gamelan gong directivity dataset

| 項目 | 內容 |
|---|---|
| **內容** | Bellows, S. D., Harwood, D. T., Gee, K. L., Shepherd, M. R. (2023). “Gamelan gong directivity dataset,” BYU ScholarsArchive.<br>檔案：`gong_data.mat`（563 kB）<br>對應論文：“Directional characteristics of two gamelan gongs,” *JASA* 154(3), 1921–1931, DOI `10.1121/10.0021055` |
| **為什麼重要** | 這是本次調查**唯一一筆針對「鑼」的學術級量測資料**，而且是**模態／指向性**——正是 `PlateModel` 要對照的東西。 |
| **是否校準絕對聲壓** | **未取得原文。** 資料頁沒有摘要也沒有量測說明；對應的 JASA 論文在 Crossref 查不到任何授權欄位（`LICENSE: (none)`），研判非開放取用，我沒有取得全文。 |
| **授權原文** | **查不到。** 該資料頁**沒有任何授權欄位**，只有「Recommended Citation」。<br>（同系列的其他樂器頁面有寫「These data ... are available for general usage.」，<br>但**鑼這一頁沒有這句話**——不能替它假設。）<br><https://scholarsarchive.byu.edu/directivity/17/>（2026-09-09） |
| **商用可否** | **不明。** 我在 2026-09-09 嘗試從命令列下載 `gong_data.mat`，被伺服器擋下（HTTP 403）。 |
| **建議** | 若要用，**先寫信問** `directivity@byu.edu`（同系列頁面公告的聯絡信箱），明講「商業產品的模型驗證對照用」。 |
| **分級** | **C**（內容 A 級，授權 C 級） |

---

### 1.8 【B 可商用的鋼琴 inharmonicity 數字】Dalmont 2021, Acta Acustica

| 項目 | 內容 |
|---|---|
| **正式名稱** | Dalmont, J.-P. (2021). “Piano bass strings with reduced inharmonicity: theory and experiments,” *Acta Acustica* 5, 9. DOI: `10.1051/aacus/2021002` |
| **內容** | 鋼琴**低音纏弦**的 inharmonicity 係數 B 實測值與理論。 |
| **是否校準絕對聲壓** | **不適用**（它量的是頻率不是音量）。 |
| **授權原文** | Crossref：`license = https://creativecommons.org/licenses/by/4.0`（content-version: vor）<br>※ 期刊網頁本身在 2026-09-09 回 HTTP 403（擋自動抓取），**論文頁原文未取得**，授權以 Crossref 出版商登錄值為準。 |
| **商用可否** | **可以（CC BY 4.0）**，依 Crossref 登錄值。 |
| **對哪個引擎有用** | `FMPianoEngine` 與 `CimbalomEngine`（揚琴也是纏弦／裸弦混用，低音弦 inharmonicity 行為可類比） |
| **分級** | **B**（授權欄位未親見期刊頁原文，降一級） |

---

### 1.9 【C 內容對，授權不對】Sinin et al. 2026 揚琴研究（BioResources）

| 項目 | 內容 |
|---|---|
| **正式名稱** | Sinin, A. E., Hamdan, S., Jia, Y., Said, K. A. M., Musib, A. F. (2026). “The Yangqin: Acoustical Study of a Chinese Dulcimer,” *BioResources* 21(1), 1084–1097. DOI: `10.15376/biores.21.1.1084-1097` |
| **內容** | **這是唯一一份揚琴的量測研究。** Table 3 有低音琴橋 9 個 course 的各次泛音頻率；Table 4 有基頻 f0、斜率 m、偏差 D。<br>結論：「the deviation ranged from 6% (course no 6) to 70% (course no 7)」——**揚琴的泛音偏離諧音非常嚴重**（比鋼琴大一到兩個數量級）。 |
| **是否校準絕對聲壓** | **未校準。** 縱軸單位是 `Intensity (dBu)`——**dBu 是電壓單位，不是聲壓單位**，無法換算成真實分貝。 |
| **器材／距離（有記錄）** | 「An omnidirectional polar pattern microphone (Behringer condenser microphone) was positioned 20 cm in front the Yangqin」，無響室，PicoScope 3000 示波器擷取 |
| **授權原文** | 論文 PDF **本身沒有印任何授權聲明**（15 頁全文已檢查）。<br>期刊政策頁寫：「users can use, reuse, and build upon the material in the journal for **non-commercial purposes**」<br><https://bioresources.cnr.ncsu.edu/about-the-journal/editorial-policies/>（2026-09-09）<br>同頁另有：「The journal retains no copyright.」（版權留在作者手上） |
| **商用可否** | **依期刊政策：不可以（明文寫 non-commercial）。**<br>※ 一個一般性的觀察（**不是法律意見**）：純量測數字通常被視為「事實」而非「著作」；<br>但**表格、圖、文字的排版與敘述是著作**。若月月要動用這篇的數字，<br>**建議只當自己閱讀後的知識，不要複製它的表格或圖進 repo 或產品**，必要時寫信問作者。 |
| **對哪個引擎有用** | `CimbalomEngine`（唯一的揚琴實測參考） |
| **分級** | **C**（內容無可取代，授權明文禁商用） |

---

### 1.10 【D 禁商用】已排除的候選（逐一附授權原文）

| 名稱 | 內容／樂器 | 是否校準 | 授權原文（≤15 字）＋出處 | 商用 | 為何排除 |
|---|---|---|---|---|---|
| **TU Berlin 樂器指向性資料庫**（現用） | 41 種樂器 3305 個單音、指向性、聲功率。含 Timpani，**無**鋼琴／鑼／揚琴／舌鼓 | **是**：「a value of 1 corresponds to a pressure of 1 Pascal」（`0_Documentation.pdf` 第 5 節） | 「The database is provided under a Creative Commons BY-NC-SA licence」（`0_Documentation.pdf` 第 2 頁，2026-09-09 由 DepositOnce 取得純文字版）<br>※ 另注意：DepositOnce **典藏頁的權利欄位寫的是「In Copyright」**（`dc.rights.uri = http://rightsstatements.org/vocab/InC/1.0/`，API 查得），與說明檔的 CC BY-NC-SA **又不一致**。<br>DOI `10.14279/depositonce-19858` | **否** | NC。維持「私下對照參考、不進產品」 |
| **MAPS**（鋼琴，Telecom ParisTech） | 鋼琴單音／和弦／樂曲，Disklavier＋虛擬鋼琴 | 未提及 | 「License: Creative Commons」連向 `by-nc-sa/2.0/fr/deed.en_US`<br><https://adasp.telecom-paris.fr/resources/2010-07-08-maps-database/>（2026-09-09） | **否** | NC |
| **MAESTRO**（Google Magenta） | 200 小時 Yamaha Disklavier 演奏＋MIDI | 未提及 | 「under a Creative Commons Attribution Non-Commercial Share-Alike 4.0 (CC BY-NC-SA 4.0) license」<br><https://magenta.tensorflow.org/datasets/maestro>（2026-09-09） | **否** | NC。且是**連續演奏**不是單音，本來就不能抽泛音 |
| **Good-sounds**（MTG／UPF） | 12 種樂器單音與音階 | 未提及 | 「The Good-sounds.org dataset is provided with a CC BY-NC 4.0 license」<br><https://www.upf.edu/web/mtg/good-sounds>（2026-09-09）<br>※ **衝突**：DataCite 對 `10.5281/zenodo.4588740` 登錄的是 `cc-by-4.0`。**保守採信作者自己的頁面（NC）。** | **否** | NC（依作者頁）；且無鑼／鋼琴／揚琴 |
| **RWC Music Database**（AIST） | 50 種樂器單音 | 未提及 | 「The databases may be used only for research purposes.」<br><https://staff.aist.go.jp/m.goto/RWC-MDB/>（2026-09-09，經搜尋結果轉述，**條款頁原文未親見**） | **否** | 僅限研究 |
| **ARTSOUNDSCAPES**（Zenodo） | 史前／民族樂器無響室錄音 | 未取得原文 | DataCite：`cc-by-nc-4.0`（`10.5281/zenodo.11046468`）<br>※ Zenodo 網頁 2026-09-09 全站 504，**未取得原文** | **否** | NC |
| **OrchideaSOL**（IRCAM） | 管弦樂器單音＋擴展技法 | 未提及 | 「It requires a free subscription to Ircam Forum.」<br><https://www.orch-idea.org/datasets/>（2026-09-09）<br>※ **衝突**：DataCite 對 `10.5281/zenodo.3740399` 登錄 `cc-by-4.0`。**採信 Ircam 官方頁（需訂閱）。** | **不明／否** | 需 Ircam Forum 訂閱，非自由授權 |
| **NSynth**（Google Magenta） | 30 萬個單音，1006 種音色 | 未提及 | 「made available by Google Inc. under a Creative Commons Attribution 4.0 International (CC BY 4.0) license」<br><https://magenta.tensorflow.org/datasets/nsynth>（2026-09-09） | **可以** | **授權沒問題，但內容不能用**：只有 **16 kHz**（8 kHz 以上全被砍掉，鑼與鋼琴的高階泛音全消失）、每段只有 **4 秒**（衰減被截斷，**量不出 T60**）、而且來源是**商業音源庫**不是真樂器量測 |
| **TinySOL**（IRCAM／Zenodo） | 14 種管弦樂器單音 | 未提及 | DataCite：`cc-by-4.0`（`10.5281/zenodo.3685367`）<br>※ Zenodo 網頁 2026-09-09 504，**未取得原文** | **可以** | **授權沒問題，但沒有我們要的樂器**：14 種全是弦樂／木管／銅管／手風琴，**無鋼琴、無打擊、無揚琴** |
| **PCMIR**（Mendeley Data） | 7 種波斯樂器，**含 santur（桑圖爾，揚琴的近親）** | 未提及 | DataCite：`cc-by-4.0`（`10.17632/bpyxwkv9wj`） | **可以** | 是**演奏片段**不是單音量測，且無器材／距離記錄。**只列不建議**，但若要找揚琴家族的音色手感，這是唯一可商用的 |
| **Freesound（CC0／CC BY 篩選）** | 使用者上傳的各式聲音，可用授權篩選器只看 CC0／CC BY | 未校準 | 「CC0 and CC BY licenses allow use and distribution ... for both non-commercial and commercial purposes」（Freesound 說明，2026-09-09，**經搜尋結果轉述**） | **可以（限 CC0／CC BY）** | 品質與器材完全不受控，**只列不建議**；可當「有沒有鋼舌鼓聲音可聽」的最後手段 |
| **Zenodo「Cimbalom」CC0 三筆** | `10.5281/zenodo.10322715` 等 | — | DataCite：`cc0-1.0`；描述：「Source: Objaverse 1.0 / Sketchfab」 | — | **是 3D 模型不是聲音**（博物館藏品掃描）。列出來是為了避免日後有人再被這個標題誤導 |

---

## §2 建議

### 2.1 結論：**有可用的，但要分兩條路走**

原本的問題是「有沒有校準到絕對聲壓、又可商用的資料集」。
**這種資料集的數量是 0。** 沒有找到，不是我沒找到，是它目前不存在於公開領域。

但可以用**兩份東西**組合起來，達到接近的效果：

#### 路線 A：要「絕對分貝」的合理性檢查 → 用 Weinzierl 2018 的 TABLE I

- **拿什麼**：`10.1121/1.5053113` 的 PDF（約 1 MB）
- **下載處**：<https://api-depositonce.tu-berlin.de/server/api/core/bitstreams/d7d0f7af-e49b-4b86-8e7d-4293aef0440a/content>
- **為什麼可以**：CC BY 4.0，且有 B&K 4230 校準器原文證據
- **只能拿它做什麼**：確認我們的輸出「**數量級沒有離譜**」。
  具體地說：定音鼓（被敲的樂器）ff 最大 108 dB、pp 最小 58 dB 聲功率位準。
- **絕對不能拿它做什麼**：不能直接跟我們的 `Pa` 或 `Pa/N` 比大小（單位不同：LW vs Lp），
  **不能宣稱「模型與實測吻合」**。

#### 路線 B：要「泛音落在哪、衰減多久、聽起來對不對」→ 用 Iowa MIS

- **拿什麼（建議只抓這三包，不要全抓）**：
  1. `tamtam.ff.zip` / `tamtam.mf.zip` / `tamtam.pp.zip` — 22/28/40 吋大鑼
  2. `thaigong.ff.zip` / `thaigong.mf.zip` / `thaigong.pp.zip` — **泰國鑼 C4–C5 逐半音，有音高**（對 `WaterGong` 最有價值）
  3. 鋼琴單音（`Piano.pp.*` / `Piano.mf.*` / `Piano.ff.*`，A0–C8）
- **下載大小**（依網頁標示的單檔大小估算，**尚未實際下載**）：
  - 泰國鑼 ff 立體聲 13 個音各 1.2–3.4 MB → 單一力度約 **30 MB**，三種力度約 **90 MB**
  - 大鑼 ff 立體聲每檔約 2.6 MB，4 件樂器 → 單一力度約 **10 MB**
  - 鋼琴 88 音 × 3 力度，單檔 1.2–13 MB → 約 **1.3 GB**（若只要中音域可大幅縮減）
- **入口**：<https://theremin.music.uiowa.edu/MISgongtamtams.html>、<https://theremin.music.uiowa.edu/MISpiano.html>
- **搭配**：鋼琴若要更多力度層，加 Salamander Grand Piano v3（CC BY 3.0，714 MB，16 段力度）

### 2.2 對 TU Berlin 那份的處置：**維持現狀，不變**

我在 2026-09-09 重新查證了一次資料集**自己的說明檔**，結果與 `EXTERNAL_DATASET_A8.zh-TW.md` 一致：
**CC BY-NC-SA，禁商用。**（原文：「The database is provided under a Creative Commons BY-NC-SA licence」）

→ **維持「只私下對照參考、資料檔不進版控、不進產品」**，這是正確的做法。

**額外發現一件事值得記一筆**：TU Berlin 這份東西的授權說法**目前有三個版本互相矛盾**——
arXiv 預印本說 CC BY-SA、資料集說明檔說 CC BY-NC-SA、DepositOnce 典藏頁的權利欄位說 In Copyright。
**以資料檔自己的說明檔為準（最嚴、也最貼近實際使用的那一份）**，也就是禁商用。

### 2.3 建議的先後順序（如果時間有限）

1. **先做**：下載 Weinzierl 2018 PDF（1 MB，5 分鐘），把 TABLE I 的 Timpani 那兩個數字記下來當合理性上下界。
2. **再做**：下載 Iowa 泰國鑼三包（約 90 MB），因為**它是唯一「有音高的鑼單音、可商用、有距離記錄」的東西**。
3. **有空再做**：Iowa 鋼琴 ／ Salamander，用來校 `FMPianoEngine` 的 inharmonicity 與 T60。
4. **不急**：寫信問 BYU 那份 gamelan gong 資料能不能商用。

---

## §3 已知缺口

以下是**確認找不到**的東西。這些不是「還沒找」，是「已經找過而且沒有」：

| 缺口 | 查證方式 | 結論 |
|---|---|---|
| **可商用＋校準到絕對聲壓的樂器音訊資料集** | Zenodo／DataCite／Crossref／WebSearch 多輪 | **0 個。** 唯一校準的公開音訊資料集（TU Berlin）是 NC |
| **揚琴／cimbalom 的公開可商用單音量測或錄音** | DataCite 搜尋 17 筆命中全部無關（3D 模型、醫學論文）；Crossref CC BY 篩選無命中 | **0 個。** 唯一實測研究（Sinin 2026）期刊政策禁商用 |
| **鋼舌鼓（steel tongue drum）的公開模態量測資料** | Crossref CC BY 篩選、DataCite、WebSearch | **0 個。** 唯一相關文獻是 ICSV27 2021 會議論文，其 PDF 在 2026-09-09 回 HTTP 403，**未取得原文** |
| **Handpan／Hang 的公開可商用量測資料** | 同上 | **0 個。** 相關文獻多為 2015 年前，且非開放授權 |
| **鑼／大鑼的可商用學術級量測資料** | BYU ScholarsArchive、Crossref、Zenodo | **1 個候選但授權不明**（BYU gamelan gong，見 §1.7）。<br>可商用的鑼**錄音**有（Iowa／VCSL／Philharmonia），但**沒有模態量測表** |
| **鋼琴逐音 T60 衰減時間的公開量測表** | WebSearch、Crossref | **未找到現成的表。** 只能自己從 Iowa／Salamander 的單音錄音量 |

### 3.1 本次調查的技術限制（誠實記錄）

- **Zenodo 在 2026-09-09 全站回 HTTP 504**（網頁與 API 皆是，多次重試）。
  受影響：TinySOL、OrchideaSOL、Good-sounds、ARTSOUNDSCAPES、Pyramic 五筆的**網頁授權欄位原文未取得**，
  只能改用 DataCite 的登錄 metadata。**這些筆的授權我都標了「未取得原文」。**
- **HTTP 403 擋下、未取得原文**的來源：ICSV27 鋼舌鼓論文（unige.iris.cineca.it）、
  Acta Acustica 全文頁、BYU `gong_data.mat` 下載。
- **OpenAIR 無響室錄音庫**（`openair.hosted.york.ac.uk`）在 2026-09-09 顯示 **"Account Suspended"**，**無法查證**。
- **RWC 與 Freesound** 的授權我只取得**搜尋結果的轉述**，**未親見條款頁原文**，已在表中註明。
- 依既有指示，**未嘗試 Reddit**。

---

## 附錄：來源清單（全部存取日期 2026-09-09）

### A. 已親自取得原文並引述

| # | 來源 | URL | 用途 |
|---|---|---|---|
| S1 | Iowa MIS 首頁（授權聲明、器材、無響室） | <https://theremin.music.uiowa.edu/MIS.html> | §1.1 |
| S2 | Iowa 鑼／大鑼頁（距離 5 feet、QTC40、曲目清單） | <https://theremin.music.uiowa.edu/MISgongtamtams.html> | §1.1 |
| S3 | Iowa 鋼琴頁（Steinway B、KM 84、非無響室） | <https://theremin.music.uiowa.edu/MISpiano.html> | §1.1 |
| S4 | Weinzierl et al. 2018 JASA 全文 PDF（CC BY、B&K 4230、TABLE I） | <https://api-depositonce.tu-berlin.de/server/api/core/bitstreams/d7d0f7af-e49b-4b86-8e7d-4293aef0440a/content> | §1.2 |
| S5 | Ackermann et al. 2024 JASA 全文 PDF（CC BY、calibrated、data on request） | <https://api-depositonce.tu-berlin.de/server/api/core/bitstreams/b197268a-bbdb-4c1e-8e5c-fae30ca93ba6/content> | §1.3 |
| S6 | TU Berlin 資料集說明檔純文字版（CC BY-NC-SA、1.0 = 1 Pa） | <https://api-depositonce.tu-berlin.de/server/api/core/bitstreams/f0de8a01-9b33-4fdf-a049-7222eaf2a252/content> | §1.10 |
| S7 | DepositOnce 典藏紀錄 metadata（`dc.rights.uri = In Copyright`） | `https://api-depositonce.tu-berlin.de/server/api/core/items/b194da8b-e98c-4761-9100-2b0bb6ba93e8` | §1.10 |
| S8 | Salamander Grand Piano `LICENSE`（CC BY 3.0 Unported） | <https://raw.githubusercontent.com/sfzinstruments/SalamanderGrandPiano/master/LICENSE> | §1.4 |
| S9 | Salamander README（Yamaha C5、AKG C414、12 cm） | <https://raw.githubusercontent.com/sfzinstruments/SalamanderGrandPiano/master/README.md> | §1.4 |
| S10 | VCSL `LICENSE`（CC0 1.0 Universal） | <https://raw.githubusercontent.com/sgossner/VCSL/master/LICENSE> | §1.5 |
| S11 | VCSL README（「even make commercial software」） | <https://raw.githubusercontent.com/sgossner/VCSL/master/README.md> | §1.5 |
| S12 | VCSL 檔案樹（Gong 1/2、Slit Drum、Steinway B 的檔數與位元組） | `https://api.github.com/repos/sgossner/VCSL/git/trees/master?recursive=1` | §1.5 |
| S13 | VCSL `NORMALIZED.txt`（鋼琴已正規化） | `https://raw.githubusercontent.com/sgossner/VCSL/master/Chordophones/Zithers/Grand Piano, Steinway B/NORMALIZED.txt` | §1.5 |
| S14 | Philharmonia 樣本頁（可商用、不可原封轉售） | <https://philharmonia.co.uk/resources/sound-samples/> | §1.6 |
| S15 | BYU Directivity 系列首頁（含 Gamelan gong 條目） | <https://scholarsarchive.byu.edu/directivity/> | §1.7 |
| S16 | BYU Gamelan gong 資料頁（無授權欄位） | <https://scholarsarchive.byu.edu/directivity/17/> | §1.7 |
| S17 | BYU Trumpet 頁（「available for general usage」——**同系列他頁**） | <https://scholarsarchive.byu.edu/directivity/13/> | §1.7 |
| S18 | Sinin et al. 2026 揚琴論文 PDF（20 cm、dBu、Table 3/4、6–70%） | <https://bioresources.cnr.ncsu.edu/wp-content/uploads/2025/12/BioRes_21_1_1084_Sinin_HJSM_Yangqin_Acoustic_Study_Chinese_Dulcimer_24951-1.pdf> | §1.9 |
| S19 | BioResources 編輯政策（non-commercial purposes） | <https://bioresources.cnr.ncsu.edu/about-the-journal/editorial-policies/> | §1.9 |
| S20 | MAPS 官方資源頁（CC BY-NC-SA 2.0 FR） | <https://adasp.telecom-paris.fr/resources/2010-07-08-maps-database/> | §1.10 |
| S21 | MAESTRO 官方頁（CC BY-NC-SA 4.0） | <https://magenta.tensorflow.org/datasets/maestro> | §1.10 |
| S22 | NSynth 官方頁（CC BY 4.0、16 kHz、4 秒、商業音源庫） | <https://magenta.tensorflow.org/datasets/nsynth> | §1.10 |
| S23 | Good-sounds 官方頁（CC BY-NC 4.0） | <https://www.upf.edu/web/mtg/good-sounds> | §1.10 |
| S24 | Orchidea 官方資料集頁（需 Ircam Forum 訂閱；另有 tam tam 集） | <https://www.orch-idea.org/datasets/> | §1.10 |
| S25 | Crossref 授權查詢（1.5053113 / 10.0025463 / 10.0021055 / aacus2021002 等） | `https://api.crossref.org/works/{DOI}` | §1.2 §1.3 §1.7 §1.8 |
| S26 | DataCite 授權查詢（TinySOL / OrchideaSOL / ARTSOUNDSCAPES / Good-sounds / PCMIR / Cimbalom） | `https://api.datacite.org/dois/{DOI}` | §1.10 |

### B. 未取得原文（已在文中標註，不作定論）

| 來源 | 狀況 |
|---|---|
| Zenodo 全部記錄頁 | HTTP 504（全站，多次重試，網頁與 API 皆同） |
| ICSV27 2021 鋼舌鼓論文 PDF（unige.iris.cineca.it） | HTTP 403（含改用瀏覽器 User-Agent 重試） |
| Acta Acustica `aacus200053` 全文頁 | HTTP 403（頁面要求啟用 JS） |
| BYU `gong_data.mat` 下載 | HTTP 403 |
| OpenAIR 無響室錄音庫 | 頁面顯示 "Account Suspended" |
| RWC 條款頁 | 僅取得搜尋結果轉述，未親見 |
| Freesound 授權說明頁 | 僅取得搜尋結果轉述，未親見 |
