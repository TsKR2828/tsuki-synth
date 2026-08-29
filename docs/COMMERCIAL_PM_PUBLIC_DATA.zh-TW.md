# 商業物理建模合成器公開驗證資料調查（B7 前置研究）

> 建立：2026-08-28
> 對應：`reports/decision_packets/B6_calibration_choice.md` 裁決記錄第 3 點——
> 月月指示調查「商業物理建模公司（如 Modartt/Pianoteq）有無公開釋出的驗證數據/
> 白皮書/學術論文」，作為 B7（第一原理力鏈）驗收基準 (a) 文獻音壓範圍 GATE 的
> 溯源候選。
>
> **本文件不改任何程式碼、不改任何容差。純網路調查與誠實記錄。**
> **假說結論先講**：月月的假說（「要取信消費者，商業公司應該會釋出一部分資料」）
> **本輪調查沒有被證實**——四家商業物理建模廠商（Modartt、Audio Modeling、AAS、
> Arturia）逐一查過，**沒有一家公開釋出「模型輸出 vs. 真實樂器量測」的比對數據、
> 白皮書或可稽核的學術論文**。唯一可查證的「第三方認可」（Steinway 對 Pianoteq
> 的官方授權）連 Pianoteq 自己的使用者論壇都在問「這個授權到底代表什麼」，且
> 查無官方正面回答。反而是**跟商業公司完全無關的學界**（INRIA/巴黎高等理工／
> KTH）找到了真正有公開全文、有方法學細節的鋼琴物理建模與量測論文。

---

## 0. 一句話結論（給 B7 裁決用）

| 調查對象 | 找到什麼 | 能不能當 B7 GATE 的文獻出處 |
|---|---|---|
| Modartt / Philippe Guillaume | 專利 1 件（無驗證數據）、科普書 1 本、Steinway 等 8 家授權（用途不明） | ❌ 不能——查無可稽核的比對數據 |
| Audio Modeling（SWAM） | 行銷頁 + 課程，無技術文件 | ❌ 不能 |
| AAS（Chromaphone／String Studio） | 產品頁描述「用什麼元件」，無技術文件 | ❌ 不能 |
| Arturia（Piano V／PhI） | 行銷頁「PhI physical modeling technology」，無技術文件 | ❌ 不能 |
| Chabassier, Chaigne & Joly (2013), JASA | **開放全文可讀**，INRIA 學界鋼琴全模型論文，有 DOI | ⚠️ **值得下一輪深讀**，非商業公司但方法學等級高，可能是更好的參照對象 |
| Roginska et al. (2013), POMA | 真實平台鋼琴 pp/mf/ff 三種力度的**近場**輻射量測（450 點） | ⚠️ 有真實 dB SPL 數字，但量測距離不是 1 m（貼近琴身 2 吋），需要換算/重新評估 |
| Askenfelt & Jansson（KTH 公開講義） | **MIDI velocity → 真實槌速 m/s** 的量測數字（B6 裁決記錄點名要找的東西） | ✅ **可直接用**，見 §3 |
| 決策包裡「pp≈60 dB / ff≈100 dB SPL @1m」這組數字 | 本輪**查無**任何鋼琴專屬、標明 1 m 距離的權威出處 | ❌ **仍是「未溯源」**，見 §4 |

---

## 1. Modartt / Pianoteq

### 1.1 Philippe Guillaume 的學術背景（查到，但沒有可稽核的鋼琴驗證論文）

- Guillaume 原本是鋼琴調音師/修復師，30 歲重新攻讀數學，取得法國教師資格
  （Agrégation）與應用數學博士學位，後成為 **INSA Toulouse 數學系教授兼系主任**，
  ResearchGate 個人頁顯示 29 篇著作、被引用 1320 次（頁面本身因 403 未能直接
  讀取列表，數字轉引自 WebSearch 摘要，**未逐篇核實**）。
- **唯一確認查到、與音樂聲學直接相關的公開出版品**：*Music and Acoustics: From
  Instrument to Computer*（Philippe Guillaume 著，ISTE/Wiley，ISBN
  9781905209262）——這是一本涵蓋聲音傳播、傅立葉分析、心理聲學、數位訊號處理、
  MP3 壓縮等主題的**教科書**，不是一篇針對 Pianoteq 模型的同行評審驗證論文。
- **多輪搜尋（WebSearch 關鍵字含「Guillaume INSA piano soundboard paper」
  「Guillaume Pommier Pianoteq citation」「Guillaume DAFx/ICMC piano
  mathematical model」）均未找到一篇可標出期刊名／DOI、專門發表 Pianoteq
  物理模型或其驗證方法的同行評審論文。** 這件事本身就是本文件要誠實記錄的
  發現之一：**Modartt 官網「about」頁也完全沒有提到任何已發表論文**（見 §1.3）。

### 1.2 專利 US 7,915,515 B2——查到的最正式的技術文件，但明確不含驗證數據

| 項目 | 內容 |
|---|---|
| 發明人 | Philippe Guillaume |
| 受讓人 | Modartt |
| 連結 | https://patents.google.com/patent/US7915515B2/en |
| 技術架構 | 兩階段：(1) **離線 presynthesis 模組**——用有限元素法從使用者量測的物理參數
  （音板阻抗、弦張力偏差）算出時域衰減正弦波的頻率/阻尼係數，存成查表；
  (2) **即時合成模組**——MIDI 觸發，用查表出來的係數做加法合成 |
| **驗證數據** | **專利文件本身沒有任何模型輸出 vs. 真實鋼琴量測的比對數據、SPL 數字或校準方法說明**。唯一出現的「量測」字眼是：「exciting signals can be measured directly on a piano … using an automatic and adjustable mechanical device」——但這是**拿真實鋼琴的音板阻抗當模型的輸入參數**，不是拿模型輸出去跟真實錄音比對的**驗證**。專利本文只用「able to reproduce, with a high degree of fidelity」這種主張式語句，沒有附上任何支持這句話的量化資料。 |

**這是本輪最直接的一條「誠實記錄」**：即使是法律上要求技術揭露最嚴格的專利
文件，Modartt 也沒有選擇附上輸出比對數據——這比行銷頁面更能說明「這家公司
對外公開到什麼程度為止」。

### 1.3 Modartt 官網——純行銷語言，無技術白皮書

- `modartt.com/about`：只有 Guillaume 的人物傳記式敘述（調音師→數學教授→
  寫出鋼琴數學模型），**完全沒有提到任何已發表論文，也沒有任何驗證方法論的
  陳述**。
- `modartt.com/pianoteq_features`：描述「每個音符即時生成，不是樣本迴圈」
  「精確模擬弦的運動」「washer duplex scale 的閃亮泛音」等**功能性/感受性
  描述**，沒有任何一張比對圖、一組比對數字、一篇引用文獻。
- 使用者手冊（`modartt.com/user_manual`）同樣是操作手冊性質，非技術驗證文件。
- **結論**：官方管道（官網、使用手冊、專利）三個地方都查過，**沒有一處提供
  「模型輸出 vs. 真實鋼琴」的可稽核比對資料**。

### 1.4 Steinway 等品牌「授權/認可」——查到事實，但無法證實其代表酸聲學比對

**查到的事實**（多來源一致，可信）：Steinway Model D、Steinway Model B 兩款
Pianoteq 預設音色頁面明確標示 "authorized by Steinway & Sons"；另外
Bechstein、Petrof、Blüthner、Steingraeber、Grotrian、Hohner 等鋼琴廠牌也出現
在授權清單。

**查不到的事實**（本輪誠實記錄「查無」）：Modartt 自己的使用者論壇上有一串
主題直接問「approved 到底是什麼意思？是聲音比對過，還是只是商標授權？」
（`forum.modartt.com/viewtopic.php?id=7639`）。本輪讀了這串討論，**裡面只有
使用者的猜測**（有人猜是「聲音跟真琴一模一樣」，有人猜是「品質達標+商標
授權」），**沒有 Modartt 或 Steinway 任何一方的官方澄清**。多次 WebSearch
同樣沒有找到 Steinway 或 Modartt 發布的、說明授權審核流程/標準的公開聲明。

**誠實結論**：「Steinway 授權」是可以查證的**事實**，但「這代表 Steinway
原廠比對過聲學數據」是月月假說裡的**推論**，本輪**沒有找到支持這個推論的
一手證據**。比較保守的讀法：這更像是**商標授權 + 主觀試彈認可**（品牌方派
鋼琴技師或藝術家試彈判斷「像不像」），而不是一份可稽核的聲學比對報告。
不建議把「Steinway authorized」直接寫成「B7 的權威驗證依據」。

### 1.5 有沒有正式的雙盲測試？查無

多次搜尋「Pianoteq blind test」「Pianoteq vs acoustic double blind」，
只找到 Modartt 使用者論壇（`viewtopic.php?id=6860`、`id=4578`）與外部論壇
（VI-CONTROL、PianoClack）上的**非正式**比較——使用者自己錄真琴與 Pianoteq
對比、業餘/半專業評審的主觀試聽，**沒有一篇符合學術方法論（隨機化、統計
顯著性、同行評審）的正式雙盲測試報告**。有一則描述提到 Modartt「用消音室
錄音去比對建模結果的頻率」，但這句話出自二手轉述（WebSearch 摘要），
**未能追到原始出處逐字確認**，本文件不採信為可稽核證據。

---

## 2. 其他物理建模廠商——同樣查無技術白皮書

逐一查了月月點名的三家，結果模式與 Modartt 高度一致：**產品頁描述「用什麼
建模方法/元件」，但沒有技術白皮書、沒有比對數據、沒有可稽核論文。**

| 廠商／產品 | 技術主張（行銷語言） | 查到的技術文件 |
|---|---|---|
| **Audio Modeling / SWAM** | "Synchronous Waves Acoustic Modelling"，由 Stefano Lucato 構思、Emanuele Parravicini 開發；強調「物理建模 + 行為建模」需要演奏者即時 MIDI 輸入才能重現真實感 | ❌ 官網（audiomodeling.com）與搜尋均只查到行銷頁、教學課程（Sound on Sound、Ask.Video），**無技術白皮書** |
| **AAS（Applied Acoustics Systems）／Chromaphone、String Studio** | 「完全不用取樣，即時求解物理方程式」，Chromaphone 3 提供 8 種「聲學物件」（弦/板/膜/樑/桿/管） | ❌ `applied-acoustics.com` 產品頁與使用手冊只描述「有哪些元件可以組合」，**無技術論文或驗證數據** |
| **Arturia／Piano V（PhI 技術）** | 官網 `arturia.com/technology/phi` 稱「先進數學演算法重現原始樂器的每個振動細節」，9 款鋼琴模型 | ❌ 只有行銷頁面，**查無技術白皮書 PDF 或任何比對圖表** |

**這三家跟 Modartt 的共通模式**：都用「物理建模」「即時求解方程式」這類
**技術詞彙**做行銷包裝，但**沒有一家把方程式、參數擬合方法、或模型輸出
vs. 真實樂器量測的比對結果公開發表**。這與月月的假說（「要取信消費者會
釋出資料」）方向相反——**這幾家公司選擇的取信手段是「品牌授權」（Modartt）
或「聽起來很專業的技術詞彙」（其餘三家），不是「公開可驗證的比對數據」**。

---

## 3. 學界開放資源——找到比商業公司更有用的東西

### 3.1 Chabassier, Chaigne & Joly (2013)——與商業公司無關，但方法學等級最高

| 項目 | 內容 |
|---|---|
| 全稱 | J. Chabassier, A. Chaigne, P. Joly, *Modeling and simulation of a grand piano*, **J. Acoust. Soc. Am. 134(1), 648–665 (2013)** |
| DOI | **10.1121/1.4809649** |
| 開放全文 | ✅ 兩個管道確認可下載：HAL（`inria.hal.science/hal-00873089`、`hal-00768234`，INRIA 官方典藏）與作者鏡像 PDF（`perso.ensta.fr/~touze/PDF/Batwoman/chabassier-jasa.pdf`，本輪已成功下載 2.9 MB 全文，但本次工具鏈未能把 PDF 正文解析成可讀文字，**內容細節待下一輪用本機 PDF 閱讀工具重讀**） |
| 涵蓋範圍（來自搜尋摘要與 INRIA 團隊頁） | 時域全鋼琴模型：弦（含內耗、勁度、幾何非線性）+ 槌弦非線性耗散接觸力 + 音板（正交異向 Reissner–Mindlin 板，肋條/琴橋視為局部不均質）+ 弦-音板耦合（同時傳遞橫波與縱波） |
| 背景系列 | 這篇是系列研究的一部分：INRIA Research Report RR-8097（Part 1，模型描述）與 RR-8181（Part 2，數值結果，摘要提到「與量測比對」但本輪未逐頁確認比對的量與數字） |
| 作者背景 | Juliette Chabassier（INRIA Magique-3D／Makutu 團隊研究員）、Antoine Chaigne（ENSTA/巴黎高等理工聲學）、Patrick Joly（INRIA）——**與 Modartt 完全無關的獨立學界團隊** |

**本文件的誠實標註**：本輪**確認這篇論文存在、有 DOI、開放全文可下載**，
但**尚未完整讀到其驗證方法論與量化比對結果的具體數字**（工具鏈這輪無法把
下載到的 PDF 轉成可讀文字）。**建議 B7 開工前，下一輪先把這篇 PDF 用可解析
PDF 文字的工具（例如本機安裝 `pdftotext`／`poppler-utils`）重新讀一遍**——
這篇論文的方法學等級（同行評審、開放全文、INRIA 官方典藏、有完整力鏈的
時域模型）明顯高於本文件 §1、§2 查到的所有商業公司資料，**是比「Modartt
的行銷語言」更值得當 B7 方法學參照的對象**。

### 3.2 Roginska et al. (2013)——真的有 pp/mf/ff 的 dB SPL 量測，但不是 1 m 距離

| 項目 | 內容 |
|---|---|
| 全稱 | A. Roginska et al., *High resolution radiation pattern measurements of a grand piano — the effect of attack velocity*, **Proceedings of Meetings on Acoustics, Vol. 19, 035006 (2013)** |
| 內容 | 對一台平台鋼琴的 Middle C，分別以 pp／mf／ff 三種力度量測，**450 個空間點**（琴身上方 2 吋高度、寬 38 吋每 2 吋一點、長 88 吋每 8 吋一點）記錄輻射壓力分布 |
| **與 B6 決策包數字的關係** | 決策包寫的是「**1 m 處** pp≈60 dB / ff≈100 dB SPL」——這篇論文的量測點**貼在琴身上方 2 吋（近場）**，不是 1 m 遠場，**兩者的距離基準不同，不能直接拿來對號入座**，需要額外做近場→1m 遠場的聲學衰減換算（且鋼琴是分布聲源，這個換算本身不是簡單的點聲源 6dB/倍距離律，需另外處理） |
| 取得狀態 | ⚠️ 本輪只讀到摘要/會議資訊，**未取得全文與逐一數字**（POMA 論文通常在 AIP scitation 平台，本輪未成功 fetch） |

### 3.3 Askenfelt & Jansson（KTH 公開講義）——B6 裁決記錄點名要補搜的東西，本輪找到了

`reports/decision_packets/B6_calibration_choice.md` 裁決記錄第 2 點明確要求
補搜「MIDI velocity→真實槌速 m/s 對應（Askenfelt & Jansson 方向）」。本輪
直接查到並確認可開放讀取：

| 出處 | 連結 | 內容 |
|---|---|---|
| A. Askenfelt & E. Jansson, *From touch to string vibration: The motions of the key and the hammer* | `speech.kth.se/music/5_lectures/askenflt/motions.html` | ✅ 開放全文（KTH 官方講義頁） |
| 同系列 *String contact duration and dynamic level* | `speech.kth.se/music/5_lectures/askenflt/stricont.html` | ✅ 開放全文 |

**取得的數字（本輪已核實，可直接引用）**：

- **鍵速（mf）**：最大速度約 **0.3–0.5 m/s**
- **鍵速（f）**：峰值很少超過 **1 m/s**（約 4 km/h）
- **槌速換算關係**：槌頭行程約為鍵行程的 **5 倍**，且發生在幾乎相同時間內，
  因此槌頭速度約為鍵速度的 **5 倍**
- **槌速（f，推算上限）**：約 **5 m/s**（約 18 km/h）
- **弦接觸時間**：低音約 4 ms、高音treble不到 1 ms；在 p–ff 這個常用動態範圍內，
  接觸時間相對 mf 的變化約 **±20%**
- **本文件明確查無的部分**：這兩頁 KTH 講義**完全沒有提供任何聲壓級（SPL）
  數字**——它們是純粹的**運動學/力學**量測（鍵速、槌速、接觸時間），
  不涉及聲學輻射量測。**不可**把這份資料拿來當 SPL GATE 的出處，只能用在
  「velocity → 槌速 m/s」這一段。

---

## 4. 對 B6 決策包「pp≈60 dB / ff≈100 dB SPL @1m」這組數字的溯源結果——仍是未溯源

`reports/decision_packets/B6_calibration_choice.md` 第 150–151 行寫的
「文獻音壓範圍 GATE（真實鋼琴 1m 處 pp≈60 dB / ff≈100 dB SPL，需補溯源）」，
本輪**沒有找到**任何鋼琴專屬、且明確標示「1 m 距離」的權威出處直接支持這兩個
數字。查到的相關但**不精確吻合**的資料如下，如實列出：

| 資料 | 內容 | 為什麼不能直接當出處 |
|---|---|---|
| 一般音樂動態記號對應表（多個二手來源，含疑似轉引自 Pierce《Science of Musical Sound》） | fff≈100 dB SPL、f≈80 dB SPL、一般背景音 50–60 dB SPL | **不是鋼琴專屬量測**，是「動態記號」的通用對應表，且未標示量測距離；`pp` 沒有給出對應的具體數字 |
| Roginska et al. (2013)（§3.2） | 真實鋼琴 pp/mf/ff 三級的**近場**（貼近琴身 2 吋）SPL 量測 | **距離不是 1 m**，不能直接引用其數字當「1 m 處」的依據，需要額外換算且換算方法本身待確認 |
| 「音樂會平台鋼琴 fortissimo 時輻射聲功率約 0.1 W」（多個二手來源提及） | 給的是聲功率（W），不是聲壓級（dB SPL @ 某距離） | 聲功率換算成某距離的 SPL 需要知道指向性/輻射模式，這正是 `EXTERNAL_ANCHOR_SOURCES.md` §1 那個校準到絕對聲壓的樂器指向性資料庫（41 種樂器，但**不含鋼琴**）想解決卻解決不了的缺口 |
| 部落格/評測類網站（instrumentinsight.com 等） | 「pp 20–30 dB，ff 約 100 dB」 | ⚠️ **非學術/非量測來源**，本文件不採信為 GATE 出處，僅記錄存在此類非權威說法供對照 |

**誠實結論**：B7 驗收基準 (a) 的「pp≈60 dB / ff≈100 dB @1m」這組具體數字，
**本輪查證後仍應標記為「未溯源」**，不建議直接沿用當 GATE 門檻，除非能找到
鋼琴專屬、標明量測距離（1 m 或可換算到 1 m）的權威文獻——**§3.1 的
Chabassier et al. (2013) 全文（如果內文含絕對 SPL 數字）或 §3.2 的 Roginska
et al. (2013) 全文（如果能做近場→1m 的合理換算）是接下來最值得深挖的兩條線**，
比繼續在商業公司行銷頁裡找數字更有希望。

---

## 5. 對 B7 §6 步驟建議

1. **不要把 Modartt/Pianoteq 的任何公開素材當成 B7 的驗收依據來源**——
   本輪窮盡了官網、使用手冊、專利、論壇四個管道，沒有一個提供可稽核的
   模型輸出 vs. 真實鋼琴比對數據。「Steinway authorized」這件事實可以在
   文件裡提一句當背景，但不能寫成「已通過原廠聲學驗證」。
2. **下一輪優先重讀 Chabassier, Chaigne & Joly (2013)（DOI 10.1121/1.4809649）
   全文**——本輪已確認 PDF 可下載，只是這次的工具鏈沒能把它轉成可讀文字。
   這篇論文很可能是本次調查裡最接近「有公開全文、有真實比對方法論」的
   鋼琴物理建模參照。
3. **B7 的 pp/ff SPL GATE 數字建議不要單獨沿用 B6 裁決包原文那組（60/100 dB
   @1m）**，改成：等 Chabassier et al. 全文讀完後看它有沒有給絕對 SPL；
   若沒有，退而求其次評估 Roginska et al. (2013) 的近場數字能否合理換算到
   1 m；兩者都沒有的話，如實記錄「查無鋼琴專屬 1m SPL 文獻」，改用其他
   GATE 設計（例如相對動態範圍 dB 差，而非絕對 dB 值）。
4. **Askenfelt & Jansson 的槌速數字（§3.3）可以直接採用**，用於 B7 前置資料
   「MIDI velocity → 真實槌速 m/s」這一塊——`f` 時鍵速峰值約 1 m/s、槌速約
   5 m/s 這組數字有開放全文可稽核，符合 Rule 1 標準。
5. **MAPS 資料集使用前需先查清楚哪些子集是真實 Disklavier 錄音、哪些是
   「Virtual Piano software」合成音**（本輪只確認官方頁面說兩者都有，但
   沒有查到逐一子集的對照表）——如果把合成音當「真實鋼琴外部錨」使用，
   會犯跟 `EXTERNAL_ANCHOR_SOURCES.md` 已經自我糾正過的同一類錯誤
   （拿沒查清楚的東西當「查無」或「已驗證」）。**這件事本輪未查清，留給
   下一輪**。

---

## 6. 引用清單

| # | 出處 | 取得狀態 | 本文件用到什麼 |
|---|---|---|---|
| 1 | US Patent 7,915,515 B2（Guillaume / Modartt） | ✅ 開放全文（Google Patents） | §1.2 全部 |
| 2 | Modartt 官網 `about`、`pianoteq_features`、`user_manual` | ✅ 開放 | §1.1、§1.3 |
| 3 | Modartt 使用者論壇 `viewtopic.php?id=7639`（Steinway approved 討論串） | ✅ 開放 | §1.4 |
| 4 | P. Guillaume, *Music and Acoustics: From Instrument to Computer*, ISTE/Wiley, ISBN 9781905209262 | ⚠️ 僅查到書目資訊，未取得全文內容 | §1.1 |
| 5 | J. Chabassier, A. Chaigne, P. Joly, *Modeling and simulation of a grand piano*, J. Acoust. Soc. Am. 134(1), 648–665 (2013), DOI 10.1121/1.4809649 | ✅ PDF 已下載（2.9 MB，透過 HAL 鏡像），**內文尚未解析成可讀文字** | §3.1 |
| 6 | A. Roginska et al., *High resolution radiation pattern measurements of a grand piano — the effect of attack velocity*, Proc. Meetings on Acoustics 19, 035006 (2013) | ⚠️ 僅摘要/會議資訊 | §3.2、§4 |
| 7 | A. Askenfelt & E. Jansson, *From touch to string vibration*（KTH 公開講義，`motions.html`、`stricont.html`） | ✅ 開放全文 | §3.3 |
| 8 | Emiya, Badeau, David, MAPS 資料庫官方頁（`adasp.telecom-paris.fr`） | ✅ 開放（但子集細節未查清） | §5 第 5 點 |
| 9 | Audio Modeling／AAS／Arturia 官網與產品頁（`audiomodeling.com`、`applied-acoustics.com`、`arturia.com/technology/phi`） | ✅ 開放（僅行銷內容） | §2 |
| 10 | 各類鋼琴動態記號 dB SPL 二手轉述（含疑似 Pierce《Science of Musical Sound》轉引） | ⚠️ 二手來源，未取得原書逐字核對 | §4 |

---

## 7. 狀態

- [x] 查證 Modartt/Philippe Guillaume 學術背景與著作，**查無**可稽核的鋼琴模型
      驗證同行評審論文（§1.1）
- [x] 讀專利 US 7,915,515 B2 全文，確認**不含**模型輸出 vs. 真實鋼琴的比對數據
      （§1.2）——本文件最直接的一條誠實記錄
- [x] 查 Modartt 官網三處管道，確認皆為行銷/操作文件，無技術白皮書（§1.3）
- [x] 查證 Steinway 等品牌授權為真實事實，但**查無**官方對「授權代表什麼」的
      澄清聲明，不採信為聲學驗證依據（§1.4）
- [x] 確認查無正式雙盲測試報告，僅有非正式社群比較（§1.5）
- [x] 逐一查 Audio Modeling／AAS／Arturia 三家，皆為行銷頁，無技術白皮書（§2）
- [x] 找到 Chabassier, Chaigne & Joly (2013) JASA 論文，確認 DOI 與開放全文
      可下載，**內文細節待下一輪重讀**（§3.1）
- [x] 找到 Roginska et al. (2013) POMA 論文，確認有真實 pp/mf/ff SPL 量測，
      但量測距離為近場、非 1 m（§3.2）
- [x] 找到並核實 Askenfelt & Jansson 的鍵速/槌速數字，可直接供 B7 前置資料
      使用（§3.3）
- [x] 對 B6 決策包「pp≈60/ff≈100 dB @1m」逐項溯源，**結論：仍未溯源**，
      列出四類查到但不精確吻合的候選資料並說明各自侷限（§4）
- [ ] Chabassier et al. (2013) PDF 全文尚未成功解析成可讀文字，下一輪需用
      `pdftotext`/`poppler-utils` 或等效工具重讀
- [ ] Roginska et al. (2013) 全文（AIP scitation 平台）本輪未成功 fetch
- [ ] MAPS 資料集哪些子集為真實 Disklavier 錄音、哪些為虛擬鋼琴合成音，
      本輪未查清子集對照表
- [ ] ResearchGate 上 Philippe Guillaume 的 29 篇著作列表因 403 未能逐篇核實，
      不排除其中有本輪搜尋關鍵字沒有命中的鋼琴相關論文

---

## 8. 稽核記錄（2026-08-28，獨立複核）

獨立稽核抽 3 條引用**親自開連結重新核實**（不看本文件既有描述，重新問頁面），
外加 1 條「只有行銷話術」的抽查。結果：**抽查的引用全部屬實，沒有一條是編造或
灌水；本文件對「查無」的誠實記錄也全部站得住**。

**引用 #1｜US Patent 7,915,515 B2**（`patents.google.com/patent/US7915515B2/en`）
— ✅ 核實通過。標題 *Device for producing signals representative of sounds of a
keyboard and stringed instrument*，發明人 Philippe Guillaume、受讓人 Modartt，
與 §1.2 表格一致。兩階段架構（離線 presynthesis 用有限元素法算衰減正弦波的
頻率/阻尼係數存表 + MIDI 觸發的即時加法合成）確認屬實。**§1.2 最關鍵的那句
「專利本身沒有任何模型輸出 vs. 真實鋼琴的比對數據、SPL 數字或校準方法」——
本輪重新問過頁面，答覆同樣是「查無任何 SPL 量測、校準資料或 measured-vs-modeled
比對圖」。** §1.2 引用的兩句原文亦逐字對上：「exciting signals can be measured
directly on a piano of traditional construction by using an automatic and
adjustable mechanical device for depression of the notes of the piano」與
「able to reproduce, with a high degree of fidelity」。

**引用 #7｜Askenfelt & Jansson, KTH 講義 `motions.html`** — ✅ 核實通過，且是
本文件唯一標為「可直接引用」的數字來源，逐項對上原文：mf 鍵速
"the maximum velocities are approximately 0.3 - 0.5 m/s"；f 鍵速
"Even in forte the peak velocity does seldom exceed 1 m/s"；5 倍關係
"The hammer must travel a distance which is approximately five times longer
than the travel of the key in essentially the same time. Consequently, the
hammer velocities are about five times higher than the key velocities."；
f 槌速 "In the forte example, the maximum hammer velocity is about 5 m/s"。
**§3.3 最後那條自我設限「這兩頁完全沒有提供任何 SPL 數字，不可拿來當 SPL GATE
的出處」——本輪重新問過，頁面確實無任何 dB/SPL 數字，該自我設限成立。**
（註：`speech.kth.se` 裸網域本輪 DNS 解析失敗，需走 `www.speech.kth.se`；
建議下次把 §3.3 的連結補上 `www.`。）

**引用 #5｜Chabassier, Chaigne & Joly (2013), DOI 10.1121/1.4809649** — ✅ DOI
解析核實通過：`doi.org/10.1121/1.4809649` 302 轉向到
`pubs.aip.org/jasa/article/**134/1/648**/614365/**Modeling-and-simulation-of-a-grand-piano**`，
期刊／卷／期／起始頁與標題全部與 §3.1、§6 表格一致。**未逐字核實**的部分如實
標記：AIP 頁面本身回 403（擋爬），故作者全名與結束頁 665 本輪未從一手頁面確認，
僅由 DOI 轉向字串確認到起始頁 648。另外 §3.1 說的「HAL 管道可下載」本輪**失敗**
（`inria.hal.science/hal-00873089` 回 Anubis "Access Denied"），但作者鏡像
`perso.ensta.fr/~touze/PDF/Batwoman/chabassier-jasa.pdf` **確實下載成功、確實是
2.9 MB**，與本文件記載一字不差；而且本輪的工具鏈**同樣無法把該 PDF 解析成文字**
（本機未安裝 poppler／`pdftoppm`），**§3.1 與 §7 那條未完成項目的技術理由因此
被獨立重現，不是託辭**。

**「只有行銷話術」抽查｜Arturia PhI**（`arturia.com/technology/phi`）— ✅ §2
表格屬實。重新問頁面的結果：無方程式、無參數擬合方法、無同行評審引用、無
measured-vs-modeled 比對圖，主張句僅為 "Physical modelling is a process of
recreating the physical reactions and unique interplay of both physical and
electronic components using mathematical models and algorithms to create a
realistic reproduction."；頁面口頭提及 Stanford／IRCAM 但**未附任何實際引用或
連結**——與 §2「用技術詞彙做行銷包裝、不公開比對數據」的判讀一致。

**稽核結論**：本文件的「假說未被證實」「仍是未溯源」「本輪查無」這幾類誠實記錄
（§0 結論列、§1.2、§1.5、§3.1 的未讀完標註、§4 全節、§7 四條未打勾）在抽查範圍內
**全部與一手頁面相符**，沒有把「查無」寫成「已驗證」，也沒有把二手轉述升格成
可稽核出處。唯一的維護建議是 §3.3／§6 的 KTH 連結補 `www.` 前綴。本稽核不改任何
程式碼、不改任何容差、不改任何 GATE。

---

## 9. 稽核記錄 II（2026-08-28，Opus 第二輪獨立複核）

第二輪稽核**不看本文件既有描述、也不看 §8 的第一輪記錄**，重新抽 3 條引用
親自開連結問頁面，外加 1 條「只有行銷話術」抽查。結果：**抽查的引用全部屬實，
沒有一條編造或灌水；本文件的「查無／未溯源」誠實記錄全部站得住。**

**引用 #1｜US Patent 7,915,515 B2**（`patents.google.com/patent/US7915515B2/en`）
— ✅ 核實通過。標題 *Device for producing signals representative of sounds of a
keyboard and stringed instrument*，發明人 Philippe Guillaume、受讓人 Modartt，
與 §1.2 表格一致。本輪重新問頁面「專利內有無任何模型輸出 vs. 真實鋼琴的量化
比對數據（SPL 數字、measured-vs-modeled 圖、校準資料）」，答覆為**無**——
§1.2 那句最關鍵的誠實記錄獨立成立。原文亦對上：「exciting signals can be
measured directly on a piano of traditional construction by using an automatic
and adjustable mechanical device for depression of the notes」、
「reproduce, with a high degree of fidelity, the characteristic sonority of any
mechanical real stringed keyboard instrument」。

**引用 #7｜Askenfelt & Jansson, KTH 講義 `motions.html`** — ✅ 核實通過，
§3.3 四個數字逐字對上一手頁面：
mf 鍵速 "At mezzo forte (cf. Fig. 9), the maximum velocities are approximately
0.3 - 0.5 m/s."；f 鍵速 "Even in forte the peak velocity does seldom exceed
1 m/s (about 4 km/h)."；5 倍關係 "The hammer must travel a distance which is
approximately five times longer than the travel of the key in essentially the
same time. Consequently, the hammer velocities are about five times higher than
the key velocities."；f 槌速 "In the forte example, the maximum hammer velocity
is about 5 m/s (18 km/h)."
**§3.3 的自我設限「這兩頁完全沒有 SPL 數字，不可當 SPL GATE 出處」——本輪
重新問過，頁面確認全篇只有運動學（位置／速度／加速度），無任何 dB 或 SPL
數字，該設限成立。** 連結需走 `www.speech.kth.se`（裸網域本輪同樣不通），
與 §8 的維護建議一致，建議 §3.3／§6 補上 `www.` 前綴。

**引用 #5｜Chabassier, Chaigne & Joly (2013), DOI 10.1121/1.4809649** — ✅ DOI
解析核實通過：`doi.org/10.1121/1.4809649` 302 轉向
`pubs.aip.org/jasa/article/134/1/648/614365/Modeling-and-simulation-of-a-grand-piano`，
標題／期刊／卷 134／期 1／起始頁 648 全部與 §3.1、§6 表格一致。
**未逐字核實**部分如實標記：AIP 頁面擋爬，結束頁 665 與作者全名本輪未從一手
頁面確認，僅由 DOI 轉向字串確認到起始頁。§7 那條「PDF 尚未解析成可讀文字」
的未完成標註本輪未再嘗試，維持未複核。

**「只有行銷話術」抽查｜Arturia PhI**（`arturia.com/technology/phi`）— ✅ §2
表格屬實。本輪重新問頁面：**無方程式、無參數擬合方法、無同行評審引用、無
measured-vs-modeled 比對圖**。主張句僅為 "Physical modelling is a process of
recreating the physical reactions and unique interplay of both physical and
electronic components using mathematical models and algorithms to create a
realistic reproduction."。頁面確實提到 Stanford 與 IRCAM，但**只有兩枚機構
logo（無超連結）與一句籠統敘述**，未附任何具體論文、方法或可查證來源——
與 §2「用技術詞彙做行銷包裝、不公開比對數據」的判讀完全一致。

**稽核結論**：本文件最核心的誠實性主張——§0 的「假說未被證實」、§1.2 的
「連專利都不附比對數據」、§1.5 的「查無正式雙盲測試」、§4 全節的
「pp≈60 / ff≈100 dB @1m 仍是未溯源」、§7 的四條未打勾——在本輪抽查範圍內
**全部與一手頁面相符**。沒有把「查無」寫成「已驗證」，沒有把二手轉述升格為
可稽核出處，也沒有把「Steinway authorized」誇大成聲學驗證。
本稽核不改任何程式碼、不改任何容差、不改任何 GATE。
