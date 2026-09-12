# B7 Phase 0 資料補搜：velocity→槌速映射、鋼琴 SPL 範圍、音板輻射面積 S

> 建立：2026-09-08（WF0907-R4 研究卡）
> 對應：`docs/workcards/WF0907_R4_B7_phase0_data.md`、`docs/workcards/B7.md` §2.2／§6 Phase 0
> **本文件不改任何程式碼、不改任何容差、不改 `B7.md`。純外部查證 + 唯讀引擎量測。**
>
> **引用規約**：每個外部主張都附 URL、存取日期、以及一句原文引述（英文原文，加引號）。
> 打不開的來源一律寫「未取得原文」，不憑記憶補內容。
> **全部外部來源的存取日期都是 2026-09-08**（除非該列另行標示）。
>
> **本輪關鍵進展（相對第一版）**：Goebl 博士論文（OFAI TR-2003-28）第一版下載中斷、
> 只拿到損毀的半截 PDF；本輪重新下載成功（2,946,357 bytes，完整）並全文檢索，
> **在裡面找到了一條顯式、封閉形式的 MIDI velocity ↔ 真實槌速換算式**——
> 這正是 B7 §2.2 當時列為「本卡最重要待補項」的那一項。詳見 §2.1 的 A12。
>
> **第三輪（2026-09-08 獨立複驗回合）**：本輪的工作是「不採信前一版的自報」——
> 把三條吃重的引述（A12／B9／C9）從本地 PDF 文字層**重新逐字撈出來核對**、
> 把文件裡每一條算術**不看原文重算一次**、把引擎數字**重跑一次**，
> 並補搜「平台琴音板面積」與「1 m 處 SPL」這兩個仍缺的格子。
> 結果：**前一版的引述與算術全部通過複驗**（詳見 §3.7），
> 另外**新增四個外部來源、撤下一條搜尋摘要編出來的假數字**（見 §2.5 與文末「第三輪獨立複驗記錄」）。
> **兩個仍缺的格子這輪還是沒補起來**——這件事本身也是結論。
>
> **第四輪（2026-09-08 補搜回合）**：重心放在連續三輪都空著的第三塊（平台琴音板面積）。
> **結果：這一格第一次有了數字**——Baldwin 官方規格頁給出六台平台琴的音板面積（0.87–1.68 m²，見 §2.3 C16），
> 且同廠 47 吋直立琴的 1.2774 m² 與 Ege 論文實測的 1.2649 m² **只差 0.99%**（C17），
> 代表這組廠商數字與論文量測對得起來。**但等級是「廠商規格」不是「同儕審查論文」，必須標明。**
> 另補到 Steinway B/D 厚度的正式出處（C18，同時把上一輪丟掉的 X2 收回來），
> 並丟掉一筆搜尋摘要遞來的「2–4 m²」（X3）。**「1 m 處 SPL」第四輪仍然查無**（§5 已收斂成三條需月月出手的管道）。
> 複驗方面本輪多做一步：渲染輸出這次**比對到 SHA256 位元一致**（§3.8）。

---

## 0. 一句話結論（給月月看的白話版）

**三塊資料裡，第一塊（「琴鍵按多重 → 槌頭飛多快」）這次不但查到了，還查到一條可以直接抄進程式的公式；
第二塊（「真鋼琴有多大聲」）只查到「貼著琴身 10 公分」的數字，查不到「1 公尺遠」的權威數字；
第三塊（「音板有多大面積在發聲」）翻了七篇論文，平台鋼琴的還是查不到——
但**直立鋼琴**的面積在兩篇論文裡都印出來了（1.2649 m²）。
**注意（2026-09-08 第五輪更正措辭）**：那兩篇是**同一個研究群量同一台直立琴**（Atlas 牌，0.91 m × 1.39 m × 8 mm），
**不是兩組獨立量測**，只能算「同一筆數字在兩處印得一致」，不能當成互相佐證（詳見 §2.3「C7／C9 更正說明」）。**

換句話說：**B7 這條鏈的頭（力度→槌速）現在真的可以接了，尾（換算成 1 公尺處的分貝要拿什麼驗）還是接不上。**

那條公式長這樣（Goebl 2003 博士論文式 (3.2)）：

```
MIDI velocity = 52 + 25 × log2(槌速 m/s)      反過來寫：  槌速 = 2^((MIDI − 52) / 25)
```

**為什麼可以相信它**：同一批研究者在兩篇期刊論文裡另外報過三個「MIDI 值 ↔ 槌速」對照點
（MIDI 40 → 0.7、MIDI 60 → 1.25、MIDI 77 → 2.0 m/s）。把那三個數字丟進上面這條式子，
算出來是 **0.717 / 1.248 / 2.000**——三個全中。而且 MIDI 110 算出 **4.99 m/s**，
剛好對上另一位研究者（Askenfelt）獨立量到的「forte 約 5 m/s」。**這不是本文件湊出來的擬合式，
是論文自己寫出來的式子，而且經得起三個獨立數字的交叉檢查。**

### ⚠️ 但是：查到公式 ≠ 明天就能動工（2026-09-07 複核回合補上的白話警語）

**這條公式現在還「接不上」程式，有兩個具體的攔路石，兩個都不是本文件能決定的：**

1. **程式裡「力度」有三種算法。** 你在鋼琴 App 上彈一顆音、你寫在樂譜檔裡的數字、
   還有把 MIDI 檔轉成樂譜的那支小工具，三個地方算出來的「力度」是**三個不一樣的數**。
   公式裡的「MIDI 值」要對應到哪一個，沒人定過。**不先定就代進去，等於拿蘋果當橘子用。**
2. **程式裡已經有一條「力度→音量」的規矩，而且它是已經通過驗收的。**
   現在的規矩是「力度加倍、音量固定漲一格」；換成這條新公式，那條規矩就會被改掉，
   **連帶所有已經做好的曲子，渲染出來的聲音都會變。**
   照專案規則（Rule 10），碰到這種情況必須**停下來、寫一份「改之前 vs 改之後」的對照報告**，
   不可以自己直接改下去。

**白話總結：這條公式值得採用，但它是「下一張卡要處理的工程」，不是「補完資料就結案」。**
（技術細節見 §3.4；對選項 1 的影響見 §4.2 第 4 點。）

另外本輪還做了兩件事：

1. **獨立重跑**了上一版的引擎量測（不是沿用舊數字），三個力度點的峰值完全重現到小數第 12 位。
2. **拿這條文獻公式去對引擎**：如果把引擎的 0–1 力度當成 MIDI/127 來讀，
   **引擎在中上力度（proxy 0.3–1.0）跟文獻公式差 1.4–4.6 dB，算相當接近；
   但在最小力度（proxy 0.02）差了 30 dB——引擎的最弱音比文獻公式預期的弱 30 分貝。**
   這是一個具體、可查的落差，不是感覺（見 §3.5）。

### 第三輪（2026-09-08）幫月月做了什麼、結論有沒有變

**結論沒有變，但現在它比上一版更站得住。** 這輪做的是三件「找自己麻煩」的事：

1. **重新查一次自己的引用**。那條公式、那組「同一顆音的槌速＋分貝」、那個音板尺寸，
   全部從論文檔案裡重新一個字一個字撈出來對過——**三條全部對得上**（§3.7）。
   而且發現那條公式在同一本論文裡**出現了四次**（原本只記到兩次），
   四次寫法一致，代表不是印錯或一次性的隨手設定。
2. **重新算一次每個數字**。不看上一版的答案，全部重算——**全部一樣**。
3. **再去找那兩塊還缺的資料**，多翻了六個新來源。
   **平台鋼琴的音板面積，還是查不到**；**1 公尺處的分貝，還是查不到**。

另外這輪**丟掉了一個假數字**：搜尋引擎的摘要告訴我「平台琴音板超過 20 平方英尺」，
我照規矩去原文核對，**那句話根本不在那個網頁裡**——所以這個數字不寫進來（§2.5）。
這正是本專案規則要擋的東西：**摘要說有，不算有；原文看到才算有。**

### 第四輪（2026-09-08 再開一輪）：第三塊資料終於有數字了，但等級要看清楚

**這輪唯一的新進展，是「平台鋼琴的音板有多大面積」這一格第一次填進了真實數字——
但填進去的是「鋼琴廠自己公布的規格表」，不是論文。**

Baldwin（美國鋼琴廠）把每一台琴的**音板面積**直接寫在官網規格裡，本輪逐頁核對到六台平台琴：

| 琴長 | 官網原文 | 換算 |
|---|---|---|
| 4'10"（148 cm） | “Soundboard Area: Sq. In. 1,348” | **0.87 m²** |
| 5'0" | “Soundboard Area: Sq. In. 1,620” | **1.05 m²** |
| 5'5" | “Soundboard Area: Sq. In. 1,900” | **1.23 m²** |
| 5'10" | “Soundboard Area: Sq. In. 1,988” | **1.28 m²** |
| 6'3" | “Soundboard Area: Sq. In. 2,209” | **1.43 m²** |
| 6'11" | “Soundboard Area: Sq. In. 2,604” | **1.68 m²** |

**為什麼這組數字可以稍微相信**：同一家廠也公布直立琴的音板面積，其中 47 吋直立琴是 **1.2774 m²**；
而論文（Ege & Boutillon）實際量的那台 120 cm 直立琴是 **1.2649 m²**——
**兩者只差 1%**。也就是說，廠商規格表跟論文量測在同一格上對得起來，這組數字不是隨口寫的行銷字。

**但必須同時講清楚三件事，否則會被誤用：**

1. **這是廠商規格，不是同儕審查論文。** 等級比 Ege 的量測低一階，B7 若採用要在程式註解裡標明。
2. **它是「板子的面積」，不是「有效輻射面積」。** 物理上真正在輻射的面積會小於板面積，兩者不是同一件事。
3. **音樂會用的九尺演奏琴（如 Steinway D）還是沒有數字**——本輪查到最大的只到 6'11"。
   照這六台的趨勢外推是**猜**，本文件不做。

**另外兩件事**：
(1) 上一輪被丟掉的 X2（「Steinway 音板中央 9 mm、邊緣 6 mm」）**這輪找到真正的出處了**
（Boutillon/Ege/Paulello 的論文原文一句話），所以那個數字現在可以用了（見 C18）。
(2) **「1 公尺處是幾分貝」這一格，第四輪還是空的**——這已經是連續四輪查不到，
    可以認定「免費管道查得到的東西已經查完了」，剩下的只能靠月月用機構帳號或寫信要資料（見 §5）。

---

## 1. 問題（B7 卡開工前缺的三塊）

| 缺口 | B7 卡裡的位置 | 缺的具體東西 |
|---|---|---|
| A. velocity → 真實槌速 (m/s) | §4.2 (a) | 一個**顯式**的映射（表格或擬合式），把 MIDI velocity（0–127）或引擎的 0–1 proxy 換成 m/s |
| B. 真鋼琴 SPL 範圍 | §8 驗收基準 (a) | 「1 m 處 pp≈60 dB / ff≈100 dB SPL」這組數字的**權威出處**（既有文件已標為「未溯源」） |
| C. 音板有效輻射面積 `S` | §4.5 (d) | 一個有出處的 `S`（m²），或能推出 `S` 的板子尺寸／質量／面密度 |

本輪另加一項卡片指定的次要工作：D. 社群對「鋼琴有多大聲」的觀感證據（**分級標示，非物理證據**）。

---

## 2. 外部證據表（分級）

**溯源等級定義**：
`原文全文` = 本輪親自取得 PDF/HTML 全文並逐字核對；
`轉引` = 有全文，但該數字是原作者轉引他人量測；
`業界技術文件` = 廠商／專業媒體的技術文章，有量測方法與校準敘述但非同儕審查；
`僅摘要` = 只讀到摘要/搜尋摘要，未取得全文；
`未取得原文` = 來源存在但本輪打不開（403／anti-bot／付費牆等），**其中的任何數字一律不採用**；
`社群` = 論壇/使用者發言，只當使用者觀感證據，不是物理證據。

### 2.1 表 A：MIDI velocity ↔ 真實槌速（m/s）

| # | 數值 | 條件（樂器／力度／量法） | 來源 | 溯源等級 |
|---|---|---|---|---|
| **A12** | **`MIDIvel = 52 + 25 · log2(fhv)`**，`fhv` = final hammer velocity (m/s)。**反解：`fhv = 2^((MIDI − 52) / 25)`** | Bösendorfer SE290 電腦控制平台鋼琴；作者自述這是「本研究採用的 velocity map」，用來把 SE 系統量到的真實槌速換成 MIDI 值 | Goebl, *The Role of Timing and Intensity…*, 博士論文, Univ. Graz / OFAI TR-2003-28 (2003)。**Ch.3 §3.7（p.78）式 (3.2)**，原文：**“was chosen to be MIDIvel = 52 + 25 · log2(fhv)”**。同一式另出現於 **Ch.2 §2.3 註 23**（頁碼由 PDF 頁首序推定為 p.40）：**“a logarithmic map was always used: MIDIvelocity = 52 + 25 · log2(FHV)”** | **原文全文**（本輪重新下載完整 PDF，`pdftotext` 逐字核對） |
| A1 | **MIDI 40–60 ↔ 0.7–1.25 m/s** | Bösendorfer SE290／Yamaha Disklavier／Steinway 平台琴；「表情演奏中等力度」的典型區間；槌軸加速度計積分測最大槌速 | Goebl, Bresin & Galembo, *JASA* **118**(2), 1154–1165 (2005), General Discussion（**p.1163**；**2026-09-09 第二次複核更正頁碼**：上一版寫 p.1162，實際該句落在 1162 頁尾註腳之後、1163 頁尾註腳之前，故為 p.1163）。原文：**“between 40 and 60 MIDI velocity units (0.7–1.25 m/s)”** | **原文全文**（本輪重新 grep 核對） |
| A2 | **MIDI 77 ↔ 2 m/s** | 同一組實驗設備；用於同步對齊的「較大聲」門檻 | Goebl & Bresin, *JASA* **114**(4), 2273–2283 (2003), §II.C 末段（p.2275）。原文：**“hammer velocity over 2 m/s or 77 MIDI velocity units”** | **原文全文**（本輪重新 grep 核對） |
| A3 | **槌速實測全域下限 0.18 m/s（pressed touch）／上限 6.8 m/s（struck touch）** | 三台平台鋼琴、兩位鋼琴家、兩種觸鍵；**極soft 只能用按壓觸鍵達成、極loud 只能用擊打觸鍵達成** | Goebl et al. (2005), **p.1163**（**2026-09-09 第二次複核更正頁碼**，上一版寫 p.1162）。原文：**“minimum 0.18 m / s or 50.0”**（後接 `dB-pSPL`）與 **“maximum 6.8 m / s or 110.4 dB-pSPL”** | **原文全文**（本輪重新 grep 核對；PDF 為雙欄，兩句在文字層被鄰欄文字插斷，已逐字還原） |
| A4 | **0.11 m/s (pp) – 6.83 m/s (ff)** | Boutillon 的槌速量測範圍 | Woodhouse, *Euphonics* §11.2。原文（本輪重新核對）：**“measured hammer striking speeds in the range from 0.11 m/s”**（…）**“to 6.83 m/s (fortissimo)”**。原始出處書目（本輪取得完整條目）：**X. Boutillon, “Model for piano hammers: experimental determination and digital simulation”, *JASA* 83, 746–754 (1988)** | **轉引**（Euphonics 全文親讀；Boutillon 1988 原文本輪未取得） |
| A6 | **f 觸鍵 ≈ 5 m/s FHV、p 觸鍵 ≈ 1 m/s FHV** | Askenfelt & Jansson 1991 的量測，由 Goebl 論文轉引並標出頁碼 | Goebl et al. (2005), Introduction。原文：**“1 m / s FHV, Askenfelt and Jansson, 1991, p. 2385”** | **轉引**（Goebl 全文親讀） |
| A7 | Disklavier 螺線管的複製上限：**G6 可到 3.5 m/s、C1 只到 2.4 m/s** | 自動演奏機構的**再生**能力上限，不是人類演奏上限 | Goebl & Bresin (2003), §III.B。原文：**“accelerated up to 3.5 m/s, whereas a C1”**（…）**“only up to 2.4 m/s”** | **原文全文**（**注意：這是機器限制，不可當作真實槌速範圍**） |
| A8 | 模型用槌速 **4.5 m/s** | Steinway D 全鋼琴時域模擬所採用的擊弦速度 | Chabassier, Chaigne & Joly, *JASA* **134**(1), 648–665 (2013), §V。原文：**“hammer strikes the strings with a velocity of 4.5”** | **原文全文**（作者鏡像 PDF） |
| A9 | **MIDI velocity 沒有物理單位，解讀權在接收端** | MIDI 1.0 Detailed Specification 96.1（MMA），Channel Voice Message 定義節 | 第三方鏡像 PDF。原文：**“Interpretation of the Velocity byte is left up to the receiving instrument.”** 同節另有 **“A value of 64 (40H) would correspond to a mezzo-forte note”** | **原文全文（第三方鏡像）**——非 MMA 官方伺服器 |
| **A5** | **forte 最大槌速 ≈ 5 m/s；槌速 ≈ 鍵速 ×5；mf 鍵速 0.3–0.5 m/s；forte 鍵速峰值很少超過 1 m/s** | 平台琴動作機構，加速度計量測（Askenfelt & Jansson） | Askenfelt & Jansson, "From touch to string vibrations"，KTH 五講義，`speech.kth.se/music/5_lectures/askenflt/motions.html`。原文（**2026-09-08 第五輪逐字重取，補回被截掉的後半句**）：**“In the forte example, the maximum hammer velocity is about 5 m/s (18 km/h), not very far from the highest velocity observed during the experiments.”**；**“the hammer velocities are about five times higher than the key velocities.”**；**“At mezzo forte (cf. Fig. 9), the maximum velocities are approximately 0.3 - 0.5 m/s.”**；**“Even in forte the peak velocity does seldom exceed 1 m/s (about 4 km/h).”** | **原文全文**——**2026-09-08 第三輪升級**：上一版寫「未重複 fetch、沿用 repo 記錄、不計入來源數」，本輪**直接 WebFetch 該講義頁逐字取得**，故改列為正式外部來源並計入 `sources_count`。**意義**：A12 在 MIDI 110 算出 4.99 m/s 的那個交叉檢查，現在靠的是本輪親自打開的外部頁面，不再是 repo 內部記錄 |
| **A13** | **A12 那條式子在同一本論文裡出現 4 次，寫法一致** | 同 A12 來源，本輪全文搜尋 `52 + 25` / `log2` / `MIDIvel` 三個模式 | Goebl (2003) 博士論文：**Ch.2 註 23**（“a logarithmic map was always used: MIDIvelocity = 52 + 25 · log2(FHV )”）、**Ch.3 式 (3.2)**（“was chosen to be MIDIvel = 52 + 25 · log2(fhv )”）、**Ch.4 註 5**（“MIDI velocity= 52 + 25 · log2(hammer velocity)”）、**Ch.4 註 14**（“Using the same velocity map as in Experiment I–III”，後接同一式） | **原文全文**——**2026-09-08 第三輪新增**。上一版只記到兩處。**意義**：四處一致，排除「單一處印刷錯誤」的可能；且註 14 明說整個知覺實驗系列都用同一張 map |
| A11 | Repp, *JASA* **93**(2), 1136–1144 (1993) | 跨音高與槌速錄單音、分析峰值 rms | 僅 PubMed 摘要 | **僅摘要**——不採用任何數字 |

#### A12 的交叉檢查（本文件算的，算式與輸入全部列出，可複核）

把 A12 的式子反解後代入，跟 A1／A2／A6 這三筆**由不同論文、不同段落獨立報出**的數字比對：

| 輸入 | A12 算出 | 論文獨立報的值 | 一致？ |
|---|---|---|---|
| MIDI 40 | **0.717 m/s** | 0.7 m/s（A1） | ✅ |
| MIDI 60 | **1.248 m/s** | 1.25 m/s（A1） | ✅ |
| MIDI 77 | **2.000 m/s** | 2 m/s（A2） | ✅ |
| MIDI 110 | **4.993 m/s** | Askenfelt「forte ≈ 5 m/s」（A6） | ✅ |
| MIDI 127 | **8.000 m/s** | 實測最大 6.8 m/s（A3） | ⚠️ 高於實測極值 18% |
| 槌速 0.18 m/s（A3 最弱） | MIDI **−9.85** | — | ⚠️ **落在 MIDI 0 以下**（此式無法表示極弱按壓觸鍵） |

**結論**：A12 在 **MIDI 約 20–120（槌速約 0.41–6.6 m/s）** 這個區間內與所有獨立數字一致；
**兩端外面（MIDI < 20 與 > 120）此式沒有實測支撐，且 MIDI ≤ 0 對應到 A3 的最弱實測值，
表示 A12 這條式子本身涵蓋不了「按壓式極弱音」**——這是它的已知邊界，落地時必須寫進註解。

**同時要誠實標明 A12 的性質**：原文寫的是 **“was chosen to be”**（被選定為），
也就是說這是 **Bösendorfer SE 系統在該研究中採用的 velocity map（一個裝置慣例）**，
不是從物理第一原理推出來的自然律。

#### ⚠️ 上表那排「✅」被兩件事削弱（2026-09-09 複核補上；**一個數字都沒改**）

上一版在這裡寫「證據強度來自交叉一致」。**這句話說得太滿**，兩個理由：

**(1) 兩篇來源之間有一個 +14% 的槌速校正差，而且是原文自己講明的。**

Goebl, Bresin & Galembo (2005) 的**註 9** 寫著（本輪逐字核對，見下方出處欄）：

> “the hammer velocity data was corrected for that resulting in values in-”（原文在此換行）“creased by 14%.”
> 緊接著的下一句：“This correction was not applied in Goebl and Bresin 2003.”
> 校正的理由（同註）：“differences in radius between the accelerometer placement on the hammer shank”（後接 “and striking point at the hammer crown”）。

出處：Goebl, Bresin & Galembo, *JASA* **118**(2), 1154–1165 (2005) 註 9，**p.1164**（**2026-09-09 第二次複核補頁碼**：註 9 的文字層位置在頁尾 `…1163` 之後、頁尾 `1164 J. Acoust…` 之前，緊接在註 8「B&K 4230」之後）。
本輪核對方式：本機全文抽取檔 `output/wf0907/R4/goebl_2005_flat.txt`（第五輪下載的同一份 PDF 之文字層）逐字 `find`，**存取／核對日 2026-09-09**。

所以上表的三個錨點**不是同一把尺量出來的**：

| 錨點 | 出處 | 有沒有套 +14% 校正 |
|---|---|---|
| MIDI 40 → 0.7 m/s、MIDI 60 → 1.25 m/s（A1） | Goebl et al. **2005** | **有**（該篇槌速資料全部 +14%） |
| MIDI 77 → 2 m/s（A2） | Goebl & Bresin **2003** | **沒有**（註 9 明說未套用） |
| 極值 0.18 / 6.8 m/s（A3） | Goebl et al. **2005** | **有** |
| **A12 那條式子本身** | Goebl **2003 博士論文** | **沒有**（本輪在該論文全文檢索四個字串，**2026-09-09 第二次複核逐字重跑並改寫措辭**：`increased by`、`radius` **字面零命中**；`14%` 命中兩處，都是無關的 `0.0053% or 0.014%` 時間漂移；**`crown` 字面有一處命中，但與 +14% 校正無關**——上下文是 Bösendorfer 光閘量測的 “the second time when the hammer crown just starts to contact the strings”。也就是說：**論文全篇沒有出現「因加速度計位置與打擊點半徑不同而把槌速調高 14%」這件事**，故判定該論文未套此校正。**這是「檢索不到」的推論，不是原文明寫「未套用」**；原文明寫「未套用」的是 Goebl et al. (2005) 註 9 那一句） |

**(2) 三個錨點很可能不是三次獨立量測，而是同一張 map 反算出來的。**
A12 的式子在 MIDI 40／60／77 算出 **0.717／1.248／2.000 m/s**，
與兩篇論文印出來的 **0.7／1.25／2** 逐格吻合到印刷精度。
**兩篇論文都沒有寫這些 m/s 是怎麼換算來的**；吻合到這種程度，最省事的解釋是它們本來就是用同一條 map 換出來的。
（**這是本文件的推論，原文沒有這樣寫**——依 R4 標明為推論，不當證據用。）
若真是如此，上表的三個「✅」就是同一件事重複三遍，不是三次獨立驗證。

**誠實版的結論（取代上一版的「證據強度來自交叉一致」）**：

- A12 這條式子**存在、寫法一致**這件事有 P1 證據（同一本論文四處一致，見 A13）。這一點不變。
- 但**系統性偏差 ≥ 殘差**：上表算出來的殘差是 **≤0.5%**（0.717 vs 0.7、1.248 vs 1.25、2.000 vs 2），
  而兩組來源自己的槌速刻度就差 **14%**。**殘差比刻度差小一個量級，代表殘差量到的是「同一條 map 的自洽」，不是準確度。**
- 因此**不可以說「A12 準到 0.5%」**。落地時可用精度的下限應以 **±14%** 為底
  （若峰值聲壓正比於槌速一次方，約 **±1.14 dB**：`20·log10(1.14) = 1.138`）。
  **這是量級說明，不是新容差**——本文件不提出任何 GATE 門檻數字（Rule 2）。

### 2.2 表 B：真鋼琴 SPL

| # | 數值 | 條件（距離／力度／量法） | 來源 | 溯源等級 |
|---|---|---|---|---|
| B1 | **50.0 dB-pSPL（最弱）～ 110.4 dB-pSPL（最強），動態範圍 60.4 dB** | 三台平台鋼琴；**單音**；麥克風**置於琴弦上方約 10 cm**；以 **B&K 4230 聲級校準器**校準（型號取自原文註 8；**上一版另寫的「1 kHz／94 dB」不在論文裡，那是該型號的廠商規格，2026-09-07 複核已刪除**） | Goebl et al. (2005)：**50.0／110.4 dB-pSPL 這兩個數字在 p.1163**（與 A3 同一句）、**“placed about 10 cm above the strings” 在 §II.B（p.1157）**、**註 8 的 “Brüel & Kjær sound level calibrator type 4230” 在 p.1164**（**2026-09-09 第二次複核更正頁碼**：上一版一律寫 p.1162，三句其實分屬三頁）。原文：**“placed about 10 cm above the strings”**；**“Brüel & Kjær sound level calibrator type 4230”** | **原文全文** |
| **B9** | **C4（MIDI note 60）forte 一擊：槌速 3.765 m/s ↔ peak SPL 101.13 dB**；同一顆音由 Disklavier 再生：**2.794 m/s ↔ 98.53 dB** | **同一個鍵、同一台琴、同一支麥克風（約 10 cm）**；原始演奏 vs 機器再生 | Goebl 博士論文，**Fig. 2.18（p.45）**。圖內標註原文：**“maxHv: 3.765 m/s”**／**“SPL: 101.13 dB”**、**“maxHv: 2.794 m/s”**／**“SPL: 98.53 dB”**；圖說原文：**“A forte attack (C4, MIDI note number 60) played by one pianist”** | **原文全文**——**這是本輪唯一一組「同一顆音、同時有槌速與絕對 dB」的配對數字** |
| **B10** | Fig. 2.17 = 「peak SPL (dB) vs MIDI velocity」曲線，**縱軸刻度 60–110 dB、橫軸 MIDI 0–120**，分 C1/G2/C4/C5/G6 五個音 | 同 B1 設備，麥克風約 10 cm | Goebl 博士論文 Fig. 2.17（p.44）。圖說原文：**“Peak sound-pressure level (dB) against MIDI velocity as recorded by the computer-controlled pianos”** | **原文全文（僅刻度範圍，曲線座標無法從文字層取出）** |
| **B11** | Fig. 2.20 = 全鍵盤（C0–C8）× MIDI velocity 10–110 的等力度峰值位準圖；**縱軸是相對 dB（0 至 −48 dB），不是絕對 SPL**；麥克風 **ORTF 對、距琴弦約 1.5 m** | Bösendorfer SE290-3，4947 顆音全掃 | Goebl 博士論文 §2.4（p.50–51）。原文：**“about 1.5 meters from the strings”**；圖說：**“MIDI velocity ranged from 10 to 110 in steps of 2 units”** | **原文全文**——**距離最接近 1 m 的一組，但縱軸是相對值，換不出絕對 SPL** |
| B2 | 「音越高、同 MIDI velocity 下輻射越大聲」 | 同一組設備，麥克風約 10 cm | Goebl & Bresin (2003), §III.B。原文：**“The higher the pitch, the louder the radiated sound at the same MIDI velocity.”** | **原文全文** |
| **B12** | **鋼琴要 5 公尺以外才能當點聲源；音板正上方的聲場接近「面聲源」，理想上 SPL 不隨距離變**；p→mf→ff 每級約 6 dB；量測用 B&K 4230 校準 | DPA 麥克風技術文章，10 支 omni 直線陣列、32-bit/96 kHz、ProTools | DPA Microphones, *Piano sound fields and miking implications*。原文（本輪由原始 HTML 逐字核對，非摘要）：**“In the far field (>5 meters away), the piano can usually be thought of as a point source.”**；**“the sound field above the soundboard approaches that of a plane source”**；**“the difference between p (piano) and mf (mezzo forte) is approximately 6 dB”**；**“The microphones were calibrated using an acoustic calibrator (B&K 4230).”** | **業界技術文件**——有校準與方法敘述，非同儕審查。**引用它只用來支持「近場不可用 6 dB/倍距律外推」這個定性結論，不採用其 dB 數字當 GATE** |
| B3 | Roginska et al. 2013 (POMA 19:035006)，pp/mf/ff 450 點輻射量測，量測面在無蓋琴身上方約 5 cm | Yamaha Disklavier DC7M4Pro | AIP 三個管道全部 **HTTP 403** | **未取得原文**——條件敘述來自搜尋摘要，**任何 dB 數字一律不採用** |
| B4 | Chabassier et al. (2013) 全文**有沒有絕對 SPL？→ 沒有** | 全文檢索 `dB`／`SPL`／`Pa`／`sound level` | 同 A8 來源。原文：**“measured in the nearfield at a comparable location”**，未給任何 dB SPL 絕對值 | **原文全文（負面結果）** |
| B5 | 41 種樂器指向性資料庫**不含鋼琴** | 32 聲道球形陣列 | arXiv:2307.02110，全文檢索 `piano` 零命中。原文自述涵蓋 **“41 modern and historical musical instruments”** | **原文全文（負面結果）** |
| B6 | 樂器聲功率位準表（Meyer / Burghauser & Spelda 系列）**不含鋼琴** | — | Rindel, Forum Acusticum 2014，Table II 無 piano 列。原文：**“the typical dynamic range is somewhat smaller, around 25 to 30 dB”**（泛指單一樂器） | **原文全文（負面結果）** |
| B7 | ISO 23591:2021 Annex A Table A.1 **可能含鋼琴，預覽版無數值** | 標準本文 | iteh 預覽 PDF 只查到分類語句：**“Grand piano belongs to the group of loud acoustic music instruments”** | **原文全文（僅目錄/定義節）**——數值未取得 |
| B8 | 「音樂廳 ff 時鋼琴輻射聲功率約 0.1 W」 | 多個二手轉述 | 本輪與上輪皆**未找到**一手出處 | **查不到** |
| **B13** | **平台鋼琴「琴身內部、琴弦上方 20 cm 以內」峰值可超過 130 dB SPL；另有文獻宣稱槌頭正上方 136 dB SPL** | 距離明確（8 英吋 ≈ 20 cm）但仍是**極近場**；作者本人把外推標為「理論上」 | Robjohns, H., *Q. How loud is a concert grand piano?*, **Sound On Sound**, 2025-01。原文：**“can exceed 130dB SPL peak at less than eight inches (20cm) over the strings”**；**“claim peak levels of 136dB SPL immediately above the hammers”**；**“it would be close to 142dB at four inches, and 148dB at two inches — in theory!”** | **業界技術文件**——**2026-09-08 第三輪新增**。**用途只有一個**：它與 B12 一起佐證「權威數字全部集中在近場，而且連業界作者自己都把倍距外推寫成『in theory』」。**其 dB 數字不得當 GATE**（無校準紀錄、無量測報告，且它自己也是轉引） |
| **B14** | **「一般鋼琴練習時，在**近距離**用聲級計量，讀數在 60–70 dB 之間跳」** | **距離只寫 “close range”，沒有定義量測面、沒有校準紀錄、沒有力度標示** | NASM–PAMA, *Protecting Your Hearing Health — Student Information Sheet*（美國音樂院校協會／表演藝術醫學協會聯合宣導單），西伊利諾大學鏡像 PDF `wiu.edu/cofac/music/pdf/NASM-PAMA.pdf`。原文：**“a sound level meter fluctuates between a reading of 60 and 70 decibels”**（前句為 “Take for instance a typical practice session on the piano. When taken at close range to the instrument…”） | **協會宣導文件**——**2026-09-08 第四輪新增**。**價值不在數字，在於它示範了「60 dB 這種數字在業界怎麼流傳」**：沒有距離、沒有校準、沒有力度定義。**明確不得當 GATE**，也**不能**用來替裁決包那句「1 m 處 pp≈60 dB」補溯源 |
| **B15** | TU Berlin／RWTH Aachen 無響室 41 件樂器量測資料庫（含聲功率校準）**不含鋼琴** | 32 聲道球形陣列，無響室 | *A Database of Anechoic Microphone Array Measurements of Musical Instruments*，TU Berlin DepositOnce 開放全文 PDF（5 頁）。本輪全文檢索 `piano`／`Piano` **0 命中** | **原文全文（負面結果）**——**2026-09-08 第四輪新增**。與 B5（arXiv:2307.02110）是同一組資料的另一篇論文，**兩篇都不含鋼琴**，等於獨立再確認一次 |

**表 B 的結論（第四輪維持不變）**：
**「1 m 處 pp≈60 dB / ff≈100 dB SPL」這組數字，仍然查不到權威出處，維持「未溯源」。**

本輪新增的是三件事：

1. **一組同一顆音的絕對配對數字（B9）**：C4 forte、槌速 3.765 m/s、10 cm 處 101.13 dB。
   這是目前為止唯一能同時餵給 B7 §4.3（力）與 §4.6（壓）的錨點。
2. **一組 1.5 m 的量測（B11）**——距離最接近卡片要的 1 m，**但縱軸只有相對 dB**，
   所以**不能**拿來當絕對 SPL GATE。這一點必須寫清楚，免得下一位工兵誤用。
3. **「不可外推」這件事現在有外部出處了（B12）**：DPA 明說鋼琴要 **>5 m** 才近似點聲源，
   而且音板正上方（也就是 B1/B9 的 10 cm 麥克風位置）「接近面聲源」——**面聲源的 SPL 理想上不隨距離下降**，
   所以在那個位置根本沒有「每倍距離 −6 dB」這回事。上一版只是本文件自己的判斷，現在有外部技術文件背書。
   因此把 B1 的 10 cm 數字用 6 dB/倍距律換到 1 m（會得到 30.0 / 90.4 dB）**明確不成立**，
   本文件不採用該換算，只保留它作為「pp 端連量級都對不上 60 dB」的反證。

#### B9 的一個附帶物理推論（本文件的算術，已標明輸入）

B9 兩點是**同一顆 C4、同一支麥克風**，所以可以看局部指數：

```
20 · log10(3.765 / 2.794) = 2.59 dB      實測差 101.13 − 98.53 = 2.60 dB
```

→ **在 forte 附近、同一顆音上，峰值聲壓約正比於槌速的一次方（p ∝ v^1.0）。**

但拿 A3 的兩個全域極值算，指數完全不同：

```
20 · log10(6.8 / 0.18) = 31.5447 dB   實測差 110.4 − 50.0 = 60.4 dB   →  指數 = 60.4 / 31.5447 = 1.9147  →  p ∝ v^1.91
```

**兩者不衝突，但也不能混用**：A3 的兩端是**不同鍵 + 不同觸鍵法**的合成極值，
B9 是同一鍵的兩點。**B7 若要用指數律，只能用 B9 那種同鍵配對；A3 的 60.4 dB 只能當
「整台琴能做出多大動態」的參考，不是單鍵的力度曲線。** 上一版把 A3 的 60.4 dB
直接拿去跟引擎的單鍵動態範圍比對（見 §4.2 選項 1），這個比對**依然可以做，但必須加註這個差異**。

### 2.3 表 C：音板有效輻射面積 `S`

| # | 數值 | 條件 | 來源 | 溯源等級 |
|---|---|---|---|---|
| C1 | **直立鋼琴音板 0.91 m × 1.39 m × 8 mm** → 面積 **1.265 m²**（矩形，面積為本文件之乘法） | Atlas 廠牌直立琴，**原文明說是矩形音板** | Ege, Boutillon & Rébillat, arXiv:1212.2323。原文：**“An upright piano (Atlas brand) with a rectangular soundboard”**（後接尺寸 0.91 m × 1.39 m × 8 mm） | **原文全文** |
| C2 | 音板寬 **≈140 cm**；長 **60 cm（小型直立）～ >2 m（超大平台）**；板厚 **w ≈ 8±2 mm**；肋間距 10–18 cm。**平台琴音板形狀原文自述像「向後傾斜的 L」** | 通則性描述，非特定琴 | Boutillon & Ege, arXiv:1305.3057 §1。原文：**“The width of the soundboard is more or less 140 cm”**；**“The soundboard of grand pianos looks like a backward slanted ‘L’.”** | **原文全文** |
| C3 | Chabassier 模擬的 Steinway D 音板厚度 **6–9 mm**；**全文未給面積或總質量** | 有限元模型 | 同 A8。原文：**“the thickness varies between 6 and 9 mm in the soundboard”** | **原文全文（面積為負面結果）** |
| C7 | Ege & Boutillon 的音板總質量 `M`（`RADIATION_POWER_SOURCES.md` §5 建議用 `S = M/(ρh)` 反推的那個量）：**arXiv:1212.2323／1305.3057／1212.3068 這三篇裡沒有；但 arXiv:1210.5688 有，`M = 9 kg`（見 C9）** | 同一台直立琴 | 三篇的負面結果為本輪逐篇 grep 複驗（`total mass`／`mass M`／`M = <數字>`／`Lx`／`Ly`）：1212.3068 與 ISMA2010 零命中；1305.3057 只出現**符號定義**「`where M is the total mass of the structure`」，**沒有數值**。正面結果見 C9 | **原文全文（三篇負面 + 一篇正面）**——**2026-09-07 複核更正**：上一版寫「四篇皆查不到 M，`S=M/(ρh)` 路線確認走不通」，**這是錯的**，`M` 就在同一輪下載的 arXiv:1210.5688 正文裡。該路線的正確結論見 C9 下方的「C7/C9 更正說明」 |
| **C8** | arXiv:1305.3057 **Table 1 只列木材力學常數（E_L / E_R / G_LR / ρ），沒有任何面積欄** | 本輪逐表核對 | 同 C2 來源，Table 1 全文自取 | **原文全文（負面結果）**——排除「Table 1 裡也許藏著面積」這個可能 |
| **C9** | **直立琴音板等效板：`Lx = 1.39 m`、`Ly = 0.91 m`、**總質量 `M = 9 kg`** → 面積 **1.2649 m²**（乘法為本文件），面密度 **7.115 kg/m²**（除法為本文件） | 「演奏狀態下的直立鋼琴」音板，消聲室量測；此處的 `M` 是**抹平後的等效等厚均向板**質量（含肋條與琴橋），不是裸雲杉板 | Ege & Boutillon, *Synthetic description of the piano soundboard mechanical mobility*, arXiv:1210.5688。原文：**“of dimensions Lx = 1.39 m, Ly = 0.91 m and total mass M = 9 kg”**；量測對象原文：**“the soundboard of an upright piano in playing condition”** | **原文全文（正面結果）**——**2026-09-07 複核更正**：上一版把這一列寫成「全文無面積數值」的負面結果，**與原文不符**，已改寫 |
| **C10** | *The effect of Mounted Ribs on the Radiation of a Soundboard*, arXiv:1011.5372——**全文無面積數值** | 散射理論模擬 | 全文自取，檢索 `area`／`m2`／`surface` 無面積命中 | **原文全文（負面結果）** |
| **C11** | INRIA Research Report RR-8181（Chabassier et al., *Time domain simulation of a piano*）——**可能載有 Steinway D 音板幾何** | 上一版列為「下一步管道」 | HAL（`inria.hal.science`）本輪回傳 anti-bot 攔截頁（`<title>Making sure you're not a bot!</title>`，12,506 bytes HTML）。**本輪未嘗試繞過該檢測**（規則禁止），故未取得 | **未取得原文**——建議改由月月的機構帳號／校園網路取得 |
| **C12** | **「`M` 是整塊音板（含肋條、琴橋、兩根杉木撐條）的質量，本直立琴約 9 kg」——同一數字的第三篇出處（**同研究群、同一台琴，非獨立量測**），而且是唯一一篇把 `M` 的組成逐項寫出來的** | 同一台直立琴（Ege & Boutillon 研究群）；另給肋間距 13 cm、100–1000 Hz 平均阻抗約 800 kg/s | Ege & Boutillon, *Global and local synthetic descriptions of the piano soundboard*, **Forum Acusticum 2011**, arXiv:1210.5109。原文：**“M is the mass of the whole soundboard (including ribs, bridges and the two fir bars) and almost equal to 9 kg for our upright piano.”** | **原文全文**——**2026-09-08 第三輪新增**。**這一列的價值不在 9 kg 本身**（C9 已有），**而在它用原文一句話證實了 §2.3 對 `M` 的解讀**：上一版是**推論**「這個 `M` 把肋條與琴橋攤了進去，所以不能用生木密度反推」，本輪拿到**作者自己寫的定義句**。負面結果同時成立：本篇全文檢索 `grand` / `m2` / `1.39` / `0.91` 皆 0 命中，**沒有面積數值，也沒有平台琴** |
| **C13** | **現代鋼琴音板厚度「約 6.5–9.5 mm」** | 通則性業界敘述（作者為 Baldwin 前首席工程師） | Conklin, *Piano design factors*（KTH 五講義）soundboards 分頁，`speech.kth.se/music/5_lectures/conklin/soundboards.html`。原文：**“The soundboards of modern pianos usually range in thickness between 6.5 and 9.5 mm approximately.”** | **原文全文**——**2026-09-08 第三輪新增**。**用途**：這是厚度的**第三個獨立來源**（C2 的 8±2 mm、C3 的 6–9 mm、本列 6.5–9.5 mm 三者相容）。**但全頁無面積、無質量、無 dB** |
| **C14** | Wogram, *The strings and the soundboard*（KTH 五講義，音板阻抗與輻射的經典章節）——**全章無面積／尺寸／厚度／質量／dB** | 卡片方向上最該有面積的一章 | `speech.kth.se/music/5_lectures/wogram/index.html` 與 `.../impedance.html`，本輪逐頁核對。唯一的空間數字是量測網格：**“fourteen measuring points … spaced about 12 cm apart”**（是探點間距，不是板子尺寸） | **原文全文（負面結果）**——**2026-09-08 第三輪新增** |
| **C15** | Corradi, Miccoli, Squicciarini & Fazioli, *Modal analysis of a grand piano soundboard at successive manufacturing stages*, **Applied Acoustics 125:113–127 (2017)**——Fazioli 平台琴，**開放 postprint 存在但本輪取不到** | 本輪判斷「最可能載有平台琴音板幾何」的一篇 | `eprints.soton.ac.uk/408405/1/20160514_postprint.pdf`：curl 取回 2,314 bytes 的反機器人 HTML（Anubis，`/.within.website/x/xess/`），WebFetch 回 HTTP 403。**本輪未嘗試繞過該檢測（規則禁止）** | **未取得原文**——**2026-09-08 第三輪新增**。**這是目前最值得月月用一般瀏覽器點一下的一條**（見 §5） |
| **C16** | **平台鋼琴音板面積（廠商規格，六台）**：4'10" **1,348 sq in = 0.8697 m²**／5'0" **1,620 = 1.0452 m²**／5'5" **1,900 = 1.2258 m²**／5'10" **1,988 = 1.2826 m²**／6'3" **2,209 = 1.4252 m²**／6'11" **2,604 = 1.6800 m²** | Baldwin 官網各型號規格區塊；琴長與寬度同頁標明（例：BP211 為 “40" height x 61" width x 6'11" length”）。換算用 1 in = 0.0254 m（**精確定義值**），故 1 sq in = 0.00064516 m²（乘法為本文件） | Baldwin Piano 官方型號頁：`baldwinpiano.com/BP148.html`／`BP152`／`BP165`／`BP178`／`BP190`／`BP211`。六頁原文字串一致為 **“Soundboard Area: Sq. In. <數字>”**（本輪逐頁下載 HTML、剝標籤後逐字比對） | **廠商規格（業界技術文件）**——**2026-09-08 第四輪新增**。**這是三輪半以來第一組真正存在的「平台琴音板面積」數字**。**限制**：非同儕審查、未說明量法（是否含琴橋／截角）、且**是板子面積不是有效輻射面積** |
| **C17** | **同廠直立琴音板面積**：43½" **1,866 sq in = 1.2039 m²**／47" **1,980 = 1.2774 m²**／52" 演奏型直立琴 **2,376 = 1.5329 m²** | 同上，規格區塊逐字取得 | Baldwin 官方型號頁 `B342-B42-Acrosonic.html`／`B442-B42-Acrosonic.html`／`B243-New.html`／`B252-Concert-Vertical.html`，原文同為 **“Soundboard Area: Sq. In. <數字>”**；B252 另有行銷句 **“provides as much total soundboard area as a 6'3\" grand”** | **廠商規格（業界技術文件）**——**2026-09-08 第四輪新增**。**用途是給 C16 做可信度檢查**：47 吋直立琴 **1.2774 m²** vs Ege & Boutillon 實測的 120 cm 直立琴 **1.2649 m²**（C1／C9），**相對差 +0.99%**。**一個廠商規格數字與一篇論文的實測值差 1%，代表這家廠的規格欄不是行銷話術**（算式見 `output/wf0907/R4/round4/round4_evidence.txt` 第 6 節） |
| **C18** | **Steinway B 與 D 的音板木板厚度：中央 9 mm、邊緣 6 mm**；且該研究**確實建了 Steinway B／D 的音板幾何模型**（Fig. 2 就是 Steinway D 音板圖），肋間距 Steinway B **12 cm**／D **12.2 cm**、`fg` 分別 1394／1477 Hz | 兩台 Steinway 平台琴 + 三台直立琴（Atlas 120 cm、Hohner 110 cm、Schimmel 120 cm）的模型比較 | Boutillon, Ege & Paulello, *Comparison of the vibroacoustical characteristics of different pianos*, arXiv:1210.3948。原文：**“In the Steinway B and D, the thickness of the wood panel varies between 9 mm in the centre to 6 mm at the rim.”**；**“three uprights (Atlas, Hohner, Schimmel, respectively of height 120, 110, and 120 cm) and two grands (Steinway B and Steinway D)”** | **原文全文（厚度為正面、面積為負面）**——**2026-09-08 第四輪新增**。**兩個重點**：(1) 上一輪被丟掉的 X2（Steinway 音板 9→6 mm）**現在有出處了**，出處不是廠商頁而是這篇；(2) **面積依然沒有**——論文把 `area A` 列為模型輸入參數（原文 “Geometrical parameters: area A, geometry, boundary conditions…”），致謝欄還寫了 **“the dimension report of the grand pianos”**，**代表作者手上有平台琴的完整尺寸圖，但沒有把 A 的數值印出來**。這解釋了為什麼三輪半都查不到：**資料存在，只是沒公開** |
| C4 | Suzuki, *JASA* **80**(6), 1573–1582 (1986)（6 呎平台琴，標題就是輻射） | 卡片點名的候選來源 | AIP 僅摘要可讀；摘要無面積數字 | **僅摘要**——不採用 |
| C5 | Giordano, *JASA* **103**(4), 2128–2133 (1998) | 卡片點名的候選來源 | AIP 付費牆 | **未取得原文** |
| C6 | Corradi et al., ISMA 2010（Fazioli 平台琴模態分析） | 本輪取得全文 | 全文檢索面積/尺寸零命中 | **原文全文（負面結果）** |

#### C7／C9 更正說明（2026-09-07 複核回合）

上一版把 arXiv:1210.5688 記成「負面結果」，並據此宣告 `S = M/(ρh)` 反推路線「確認走不通」。
**這兩句都是對來源內容的不實描述**，本版更正如下：

1. **該論文確實給出音板等效板的尺寸與總質量**（原文一句：`Lx = 1.39 m, Ly = 0.91 m and total mass M = 9 kg`）。
   `1.39 × 0.91 = 1.2649 m²`，**與 C1 從 arXiv:1212.2323 的 Atlas 直立琴尺寸算出的面積完全相同**——
   兩篇是同一個研究群、同一台直立琴，等於**面積 1.2649 m² 得到第二篇論文的獨立確認**（這是本更正的正面收穫）。
2. 上一版引用的那句 **“the asymptotic value of the admittance depends neither on the excitation point nor on the surface”**
   本身沒有引錯，但它講的是**高頻漸近導納與面積無關**（Skudrzyk 理論的結論），
   **不能推論成「這篇論文沒有面積數值」**。上一版把「模型的某個量與面積無關」誤讀成「文中查無面積」。
3. `S = M/(ρh)` 這條路線的**正確**結論是：
   - 對這台直立琴 **根本不需要反推**——尺寸原文直接給了。
   - 若真的照 `RADIATION_POWER_SOURCES.md` §5 用 `M = 9 kg`、生雲杉密度 `ρ ≈ 400 kg/m³`、`h = 8 mm` 反推，
     會得到 `S = 9/(400×0.008) = 2.812 m²`，**是真值 1.2649 m² 的 2.22 倍**。
     原因是這個 `M` 是**抹平後等效均向板**的質量（把肋條與琴橋的質量都攤進 8 mm 厚的板裡），
     隱含面密度 `9/1.2649 = 7.115 kg/m²`、等效體密度 `889 kg/m³`，遠高於生雲杉。
     **→ 該路線不是「查不到 M 所以走不通」，而是「用生木密度反推會系統性高估約 2.2 倍」。**
   - 對**平台琴**，這條路線仍然用不了——本輪七篇裡沒有任何一篇給出平台琴音板的 `M` 或完整尺寸。
4. **一個對 B5／B7 有用的副產品**：由 `M = 9 kg` 與 `1.2649 m²` 得到的**實測等效面密度
   `ρs = 7.115 kg/m²`**（除法為本文件）。這是**本輪唯一一個有出處的真實音板面密度**。
   對照 repo 現況：`docs/RADIATION_POWER_SOURCES.md` §3 目前用的是
   `h = 9 mm × ρ_spruce = 400 kg/m³ ⇒ ρs = 3.6 kg/m²`（**裸雲杉板的假設值**）。
   兩者差近一倍，因為論文那個 `M` 把肋條與琴橋的質量都攤了進去。
   **本文件不主張哪一個「對」**——用途不同（裸板剛度 vs 整體儲能質量），
   但這個差距大到必須讓規劃者知道，已列入 §5 與 `open_items`。
   （算式與原文引述全在 `output/wf0907/R4/fixround/arx1210_mass_area.txt`。）

**表 C 的結論（2026-09-08 第三輪後更新）**：
**平台鋼琴的音板輻射面積 `S` 仍然查無出處**——這個總結論從第一版到現在**三輪都沒變**。
到目前為止：**直立琴**的面積有兩篇獨立支持（C1 = arXiv:1212.2323 的尺寸、C9 = arXiv:1210.5688 的尺寸＋質量），
**都是 1.2649 m²**，其質量定義另有第三篇（C12）用原文一句話講明；
**平台琴**則**十個來源全部沒有**（C3 Chabassier、C4 Suzuki 僅摘要、C5 Giordano 付費牆、C6 ISMA2010 Fazioli、
C10 arXiv:1011.5372、C11 INRIA RR-8181 未取得、C12 arXiv:1210.5109、C13 Conklin、C14 Wogram、C15 soton 未取得）。

**第三輪特別記一筆**：C6（ISMA 2010，Fazioli 平台琴模態分析）本輪**由本輪自己重新逐字掃過**
（模式：`mm`／`cm`／`area`／`mass`／`kg`／`dimension`／`size`／`thick`／`length`／`width`），
結果 `area` 0 命中、`kg` 0 命中、`dimension` 0 命中、`thick` 0 命中——
**一篇專門做平台琴音板模態分析的論文，從頭到尾沒有寫下板子多大多重**。
這不是本文件找得不夠仔細，是這個領域的論文普遍不報這個量（他們要的是模態頻率與振型，不是輻射面積）。
（掃描輸出在 `output/wf0907/R4/round3/_isma_scan.txt`。）

**第四輪的更新（2026-09-08）**：上面這段「平台琴查無」的結論**在論文層級仍然成立**，
但**在廠商規格層級已經不成立**——C16 給出六台平台琴的音板面積（0.87–1.68 m²），
且 C17 用同一家廠的直立琴數字與 Ege 的論文量測對到 **1% 以內**，證明這組規格欄可信度不低。
C18 另外解釋了論文層級為何一直查不到：**作者手上有平台琴的完整尺寸圖（致謝欄明寫），
只是沒把面積數值印在論文裡**。

B7 §4.5 若要一個 `S`，第四輪後有**三個**誠實選項：
(i) 用直立琴的 **1.2649 m²**（**同一研究群、同一台琴的兩篇論文都印出同一組尺寸**，不是兩組獨立量測；且**是直立琴，屬跨琴種挪用**）；
(ii) 用 C16 中**與目標琴長相符**的廠商規格值（例：5'10" 平台琴 = 1.2826 m²），
     **並在程式註解標明「廠商規格、非同儕審查、是板面積不是有效輻射面積」**；
(iii) 卡在這裡不往下算。
**仍然不得**用 C2 的通則尺寸自行相乘造一個平台琴的 S（C2 原文自己就說平台琴音板是「向後傾斜的 L 形」，
不是矩形），**也不得**把 C16 的六筆外推到九尺演奏琴——本輪查到最大只到 6'11"，再往上是猜。

### 2.4 社群證據（**使用者觀感／需求證據，不是物理證據**）

| # | 出處 | 內容 | 分級 |
|---|---|---|---|
| S1 | Piano World 論壇「Piano decibel levels」（**15 則回覆、11,299 次瀏覽**，本輪重新讀取時的計數；主樓 2009-09-01） | 使用者 **Zooplibob** 用聲級計、在**頭部高度**量自己的 M&H AA 平台琴：**“Open long stick: 100-105 dB”／“Short stick: 95 dB”／“Closed: 90-93 dB”**。另一位使用者 **jazzyprof**（Yamaha C3）談整音後的音量變化，原話：**“Proper voicing by a skilled tech will indeed bring down the volume”** | **社群**——無校準紀錄、無距離定義（「頭部高度」不是可複製的量測面）。只能當「ff 大約落在 90–105 dB 這個量級」的觀感佐證。**上一版曾引用另一句 “I think the only course is to get the piano voiced down.”，本輪重讀該串未能定位到該句，故本版撤下改用上列已核對的引文** |
| S2 | Pianoteq 官方使用者論壇 id=6943，主題「Sound level (loudness) of the pianos what were modelled」（主樓 + **9 則回覆**，編號 2–10） | 使用者 **lo134**（主樓，11-11-2019 20:22）向商業物理建模合成器要絕對聲壓規格，原話（**2026-09-08 第五輪逐字重取**）：**“Is the information about the maximum sound level and dynamic range of each of the reference pianos (or one set of number in general if all the pianos are very similar) available?”**；同一主樓另一句寫出他要這個數字的用途：**“I need the maximum sound level (SPL level) and dynamic range of the reference pianos.”**。本輪重讀確認：**串上沒有任何 Modartt 官方人員給出數字**，9 則回覆全來自一般使用者（Amen Ptah Ra／peterws／Qexl ×4／bm／lo134 ×2） | **社群**——價值在於**證明使用者會問絕對 SPL，而商業廠商沒有公開答案**，支持 §4 的判斷 |

### 2.5 本輪查了、但**不予採用**的東西（2026-09-08 第三輪新增）

研究卡鐵律第 1、4 條要求「查不到就寫查不到」。以下四筆是**主動撤下**的（X1／X2 第三輪、X3 第四輪、X4 第五輪），記在這裡是為了
讓下一位研究員不要再走一次同樣的路，也為了證明本文件的來源是核對過的、不是抄搜尋摘要。

| # | 被丟掉的主張 | 為什麼丟掉 |
|---|---|---|
| **X1** | **「平台鋼琴音板超過 20 平方英尺（≈1.86 m²）」** | 這句話出現在一次 WebSearch 的**摘要**裡，並把出處指向某鋼琴經銷商部落格。本輪照規矩去開那個頁面逐字核對：**正文根本沒有這句話**（該頁只寫 “Grand pianos are measured from the front of the keyboard to the back of the tail”）。**摘要憑空生成了一個數字。** → 不採用，也不列入來源清單的「有效證據」欄 |
| **X2** | 「Steinway Model D 音板中央 9 mm、邊緣漸薄至 6 mm」 | 同樣只見於搜尋摘要。要去核對的廠商頁 `steinway-piano.com` 回**TLS 憑證主機名不符**（憑證屬 `mdgltd.com`），**未取得原文** → 不採用。（厚度這一格已有 C13 這個逐字核對過的來源，不需要它） |
| **X3** | **「平台鋼琴音板面積典型為 2–4 m²」** | **2026-09-08 第四輪丟棄。** 這句話出現在一次 WebSearch 的**摘要**裡（查 Trévisan/Ege/Laulagnet 時），**摘要沒有指名是哪一頁的哪一句**。本輪實際打開該批搜尋結果中可取得的全文（arXiv:1210.3948、arXiv:1305.3057、TU Berlin 資料庫論文），**沒有任何一篇寫過這個區間**；而本輪唯一有數字的來源（C16 廠商規格）給的是 **0.87–1.68 m²**，**與摘要的 2–4 m² 明顯不同量級**。→ 不採用 |
| **X4** | **「鋼琴槌力 f–ff 之間實測約 32 N」** | **2026-09-08 第五輪丟棄。** 這個數字上一版寫在 §3.6 註 2，當作「試算算出的 457 N 是否高估」的對照量級，出處指向 *Reconstruction of piano hammer force from string velocity*, JASA 140:3504 (2016)。但那篇**四輪都沒取得原文**（AIP 403，存下來的 `3504_1_online.pdf` 是 5,619 bytes 的 Cloudflare 攔截頁），數字**只存在於搜尋摘要層級**。依本表對 X1／X3 的同一標準 → **整條刪除**，該論文只保留在 §5 待查表 |

**X2 的後續（2026-09-08 第四輪）**：X2 那個被丟掉的主張（Steinway 音板中央 9 mm、邊緣 6 mm）
**本輪找到了真正的出處**——不是廠商頁，而是 Boutillon/Ege/Paulello 的 arXiv:1210.3948，
原文一句 **“In the Steinway B and D, the thickness of the wood panel varies between 9 mm in the centre to 6 mm at the rim.”**
（見 C18）。**這說明「丟掉沒核到的數字」不等於「那個數字是錯的」，只等於「當時沒有證據」——
下一輪找到證據就可以收回來。**

**這四筆的教訓寫在這裡，是因為它正好是 B7 這張卡最怕的失效模式**：
`S` 與 SPL 這兩個格子空著很難受，而搜尋摘要「剛好」會遞給你一個聽起來合理的數字。
**本文件的立場是：摘要說有不算有，原文看到才算有。**

---

## 3. 引擎／repo 現況數字（本輪唯讀量測）

工具：`build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe`（2026-08-31 建）。
**未改任何 `src/`、`tools/`。** 指令與輸出留在 `output\wf0907\R4\`。

### 3.1 B6 方案 B 的絕對聲壓分接點確實存在（B7 前置條件的客觀證據）

`TsukiSynthCLI.exe --dump-modes scores/examples/physical_piano.score.json` 輸出含：

```
model_observables       : [... "radiated_power_relative", "absolute_pressure_per_force"]
unsupported_observables : ["complex_phase", "absolute_spl", "radiation_directivity"]
events[0].acoustic_transfer[0] : radius_m = 1.05
                                 pressure_per_force_real_pa_n = 0.3065508
                                 pressure_per_force_imag_pa_n = 0.0
```

→ C4 第一分音在 1.05 m 處的 Path B 轉移常數為 **0.3065508 Pa/N**；
`absolute_spl` 仍在 `unsupported_observables`（引擎自己聲明「不主張絕對 SPL」）。

### 3.2 引擎的力度→振幅動態範圍

方法：以 `physical_piano.score.json` 為底稿，單音、關掉全部效果器，只改 `velocity`；
從渲染 manifest 讀 `pre_normalize_peak`（CLI 預設 `normalize=true`，會把峰值拉到 0.95，
**所以絕對不能直接量 WAV 的峰值**）。

| 引擎 velocity proxy | `pre_normalize_peak`（C4） | 相對 v=1.0 |
|---|---|---|
| 0.01 | 0.0000752176 | **−67.39 dB** |
| 0.02 | 0.0001744036 | **−60.08 dB** |
| 0.05 | 0.0004487475 | **−51.88 dB** |
| 0.10 | 0.0022165847 | −38.00 dB |
| 0.20 | 0.0105469050 | −24.45 dB |
| 0.30 | 0.0175656732 | −20.02 dB |
| 0.50 | 0.0512635633 | −10.72 dB |
| 0.60 | 0.0707967430 | −7.92 dB |
| 0.80 | 0.1123687476 | −3.90 dB |
| 1.00 | 0.1761045456 | 0.00 dB |

（0.01／0.05／0.20／0.60 四列為 2026-09-07 複核回合新量，指令與輸出在
`output/wf0907/R4/fixround/velocity_floor_sensitivity.txt`。）

#### ⚠️ 「引擎動態範圍」這個數字不是引擎的性質，是**下限選在哪裡**的產物

上一版寫「C4 全域動態範圍 = 60.08 dB」。**這句話會誤導**：`0.02` 這個下限是本文件自己挑的，
**引擎本身沒有這個地板**——`src/score/ScoreParser.h:313` 對 `velocity` 的合法範圍是
`readNumber(*e, "velocity", velocity, 0.0, 1.0)`，也就是 **0.0–1.0，沒有任何非零最小值**。
換一個下限，同一顆 C4 的「動態範圍」就變成完全不同的數字：

| 選的下限 velocity | 到 1.00 的「動態範圍」 |
|---|---|
| 0.01 | **67.39 dB** |
| 0.02 | **60.08 dB**（上一版用的） |
| 0.05 | **51.88 dB** |
| 0.10 | **38.00 dB** |

**→ 所以「引擎動態範圍 = 60.1 dB」不是一個客觀量測值，是「我選 0.02 當下限」的結果。**
下面 §4.2 選項 1 曾拿這個 60.1 dB 去跟文獻的 60.4 dB 比對，**該比對已在本輪重寫**（見 §4.2）。

若把下限固定在 0.02（純粹為了跨音高可比，**不代表引擎有這個邊界**），三個音的數字是：

| 音 | peak(v=0.02) | peak(v=1.0) | 0.02→1.00 的差 |
|---|---|---|---|
| C2 | 0.0007268016 | 0.2174924761 | **49.52 dB** |
| C4 | 0.0001744036 | 0.1761045456 | **60.08 dB** |
| C7 | 0.0000348971 | 0.0107610738 | **49.78 dB** |

**→ 在同一個（自選的）下限上，跨音高差 10.6 dB。**
成因未在本輪追查，**本文件不主張成因，只報數字**。

**另一個本輪才看清楚的事實**：這個峰值對 velocity **不是線性的**。
把 velocity 加倍，線性律應該是 +6.0206 dB，實測是：

| velocity 加倍 | 峰值變化 |
|---|---|
| 0.01 → 0.02 | +7.30 dB |
| 0.05 → 0.10 | +13.87 dB |
| 0.10 → 0.20 | +13.55 dB |
| 0.30 → 0.60 | +12.11 dB |
| 0.50 → 1.00 | +10.72 dB |

這件事跟 repo 既有的 velocity GATE 有關，見 §3.4。

### 3.3 §3.2 的獨立重跑（本輪新增，不是沿用上一版數字）

上一版的三個代表點，本輪用同一顆 exe **重新渲染、重新讀 manifest**：

| score | 上一版 `pre_normalize_peak` | 本輪重跑 | 一致？ |
|---|---|---|---|
| `v002`（C4, velocity 0.02） | 0.0001744036 | **0.000174403583515** | ✅ 位元級一致 |
| `v030`（C4, velocity 0.30） | 0.0175656732 | **0.017565673217177** | ✅ |
| `v100`（C4, velocity 1.00） | 0.1761045456 | **0.176104545593262** | ✅ |

（輸出在 `output\wf0907\R4\verify\`。）

### 3.4 引擎的 velocity proxy 到底代表什麼——**三條路徑不一致，而且已經有一條機器驗證中的力度律**

這一點會直接決定 A12 那條公式怎麼接，B7 動工前必須先釐清：

| 路徑 | velocity 從哪來 | 與 MIDI 0–127 的關係 |
|---|---|---|
| **插件（live MIDI）** | `juce::Synthesiser::startNote(note, velocity, …)` | JUCE 慣例 = **MIDI / 127** |
| **score / CLI** | score JSON 的 `"velocity"` 欄位，`src/score/ScoreParser.h:313` 讀 0–1 的數（`readNumber(*e, "velocity", velocity, 0.0, 1.0)`） | **與 MIDI 沒有換算定義**，但**不是「隨便一個數」**——同檔 `:295–308` 已為它登記了一條力度律，見下方「⚠️ 這裡已經有一條律」 |
| **MIDI 轉譜器** | `tools/midi_to_tsukisynth.py::velocity_for()`：`profile.base_velocity × (source_velocity / 90.0)`，再加減 articulation 修正，最後 **clamp 到 0.12–0.92** | **不是 MIDI/127**，是 `/90` 再乘 profile 基準並夾限 |

`src/physics/HammerImpulse.h` 檔頭也已自承這一點，原註解：
「`0-1 正規化 MIDI velocity proxy，不是真實 m/s——既有架構限制`」。

#### ⚠️ 這裡已經有一條律，而且它是**已判定通過的 GATE**（2026-09-07 複核回合補上）

上一版說 score/CLI 的 velocity「無定義」，**這句話漏掉了 repo 裡最重要的一件事**：

- `src/score/ScoreParser.h:295–308` 的註解寫明：`ModalResonator::excite()` 是
  `currentAmp = baseAmp * velocity`，**振幅正比於 velocity**，所以 velocity 加倍 =
  `20*log10(2) = +6.0206 dB`；原文並強調
  **“This is not just a design intent -- it is machine-verified”**，
  指向 `tools/physics_verify.py` 的 velocity 判定（`ROADMAP_PHYSICS.md` §6 M1-1d）。
- `tools/physics_verify.py:1134–1136、1213` 確有 `VELOCITY_LO = 48/127`、`VELOCITY_HI = 96/127`、
  `VELOCITY_DB_TARGET = 6.0`、`VELOCITY_LAW_DB = 6.020599913279624`。
- `ROADMAP_PHYSICS.md:173` 已把「1d velocity 線性檢查轉正（modal 引擎 +6.0 ± 1.0 dB）」登記為 **已判定 GATE**。

**本輪實際重跑了這條 GATE**（唯讀，只跑 piano／MIDI 60，輸出存
`output/wf0907/R4/fixround/physics_verify_1d_piano.txt`）：

```
1d velocity judgment : PASS
   engine      MIDI    f0_lo    f0_hi  f0_delta  model_dB  verdict
   piano         60    -44.6    -36.8      +7.8      +7.8  PASS
      tau_c(v) claim domain [2026-08-27 ruling (b)]: Felt-hammer contact time is
      velocity-solved (HammerImpulse::pianoHammerTauC), so the fixed-tau_c 6.0206 dB
      law is not asserted here; JUDGED claim = render matches the model's own prediction.
      Honest report: predicted f0-band delta +7.79 dB, deviation from the fixed-tau_c
      reference +1.77 dB (informational).
      broadband RMS delta = +9.13 dB (informational ...)
```

三件必須看懂的事：

1. **piano 引擎目前不是被「+6.02 dB 固定律」判的**。2026-08-27 的 B4 裁決
   （`reports/decision_packets/B4_f3_velocity_ruling.md`）把 Felt／`tau_c(v)` 路徑切出來，
   改判「渲染要對得上模型自己的預測」。所以 `ScoreParser.h:295–308` 那句
   「對 cimbalom / tongue_drum / water_gong / water_gong_free / **piano** 都判 +6.0 ± 1.0 dB」
   **對 piano 這一項已經過時**（本卡不改該檔，列入 `open_items`）。
2. **但「有一條被判定中的律」這件事仍然成立**——只是 piano 的判定內容是
   「render 對得上 model 自己的預測」。**任何改動 velocity→激發力的公式，都會同時改掉
   render 與 model，1d 必須重新推導與重跑。**
3. §3.2 量到的峰值加倍差（+10.7 ~ +13.9 dB）與這裡的 f0 頻帶差（+7.8 dB）**不是同一個量測**：
   前者是全頻帶時域峰值，後者是基頻 ±3% 頻帶 RMS；GATE 自己也把全頻帶 RMS（+9.13 dB）
   標成 informational。**本文件不主張這兩者哪個「對」，只說明它們是不同的量。**

**→ 這對 §4.2 選項 1 的直接後果**：把 velocity→槌速換成 A12 的指數律
`2^((MIDI−52)/25)`，等於**改寫既有的 velocity→振幅關係**，
會動到 1d 這條已判定 GATE，且必然改變既有 score 的渲染輸出——
**這是 README Rule 10 的情境（必須停下寫前後對照報告，不得自行落地）**。
上一版的選項 1 沒有列出這個代價，本版已補進 §4.2。

**→ 另外，B7 若採用 A12，還必須先決定「A12 的 MIDI 值對應到引擎的哪一條路徑」。
三條路徑現在給出三個不同的數，這不是本卡能裁決的事，列入 `open_items`。**

### 3.5 拿 A12 這條文獻公式去對引擎（本輪新增的核心對照）

假設（兩條都必須明寫，否則此表會被誤讀）：
(i) 引擎 proxy 讀作 `MIDI/127`（即插件路徑的慣例）；
(ii) 峰值聲壓正比於槌速一次方（B9 的同鍵配對支持這一點，**只有兩點**）。

| 引擎 proxy | → MIDI | → A12 槌速 (m/s) | 文獻預測 dB（相對 proxy 1.0） | 引擎實測 dB | 差 |
|---|---|---|---|---|---|
| 0.02 | 2.5 | 0.254 | −29.97 | **−60.08** | **−30.11** |
| 0.10 | 12.7 | 0.336 | −27.53 | −38.00 | −10.48 |
| 0.30 | 38.1 | 0.680 | −21.41 | −20.02 | +1.39 |
| 0.50 | 63.5 | 1.376 | −15.29 | −10.72 | +4.57 |
| 0.80 | 101.6 | 3.956 | −6.12 | −3.90 | +2.21 |
| 1.00 | 127.0 | 8.000 | 0.00 | 0.00 | 0.00 |

**讀法**：

- **proxy 0.3–1.0（MIDI 38–127）：差 1.4–4.6 dB。** 以「文獻公式 + 線性假設 vs 一個完全獨立寫出來的引擎」
  來說，這個吻合度相當好，代表引擎中上力度的力度律**沒有離譜**。
- **proxy 0.02（MIDI 2.5）：差 30.1 dB。** 引擎的最弱音比文獻公式預期弱了 30 分貝。
  **但這個差不能直接判成「引擎錯」**——因為 A12 在 MIDI < 20 本來就沒有實測支撐
  （見 §2.1 交叉檢查表：A3 的最弱實測 0.18 m/s 反解出 MIDI −9.85，落在定義域外）。
  **這格是「兩邊都沒有依據」，不是「引擎偏離文獻」。**
- 這張表**不是** GATE，也**不是** B7 §8 的雙路徑檢查。它是一個量級哨兵。

### 3.6 力鏈量級試算（**本文件的試算，不是引擎輸出，不是驗收結論**）

把 B7 §4.3 的能量守恆閉式解（`δmax = [(α+1)mv²/(2K)]^(1/(α+1))`、`F_peak = K·δmax^α`）
套上 `HammerImpulse.h` 既有的 `K/α/m`（C4：K=4.5e9、α=2.5、m=0.009 kg），
再乘 §3.1 的 0.3065508 Pa/N（全表在 `output\wf0907\R4\fpeak_scale_check.txt`）：

| 音 | v (m/s) | F_peak (N) | p @1.05 m (Pa) | SPL (dB re 20 µPa) |
|---|---|---|---|---|
| C4 | 0.18（文獻最弱） | 2.55 | 0.78 | **91.8** |
| C4 | 1.25（MIDI 60） | 40.6 | 12.5 | **115.9** |
| C4 | 3.765（B9 的 forte 實測點） | 196.30 | 60.18 | **129.57** |
| C4 | 6.80（文獻最強） | 456.8 | 140.0 | **136.9** |

**這個結果明確不合理**：B9 量到真鋼琴 C4 forte（槌速 3.765 m/s）在**貼身 10 cm** 才 101.13 dB，
這裡在 **1.05 m** 就算出 129.57 dB。**同一個槌速、更遠的距離、卻多了 28.4 dB，量級不收斂。**
（3.765 m/s 那一列是本輪新加的，用的就是 B9 的實測槌速，所以這是一個
「同槌速、真實 vs 試算」的直接對比，比上一版拿文獻極值去比更有說服力。）

必須同時聲明三件事，否則這個試算會被誤讀：

1. 它**混用**了 Path C 的 `F_peak` 與 Path B 的轉移常數——B7 §4.4–§4.6 規定 Path C 要自己重算整條鏈，
   所以這**不是** B7 §8 驗收基準 (b) 的正式雙路徑檢查。
2. `F_peak` 用的是 B7 §4.3 自己承認的簡化（把弦當成不動的固定點）。本試算算出 C4 ff 峰值力 **457 N**，
   **這個數字目前沒有任何實測值可以對照**。
   **（2026-09-08 第五輪更正）**：上一版在這裡寫了一個「文獻實測 f–ff 之間約 32 N」的對照量級，
   出處指向 *Reconstruction of piano hammer force from string velocity*, JASA 140, 3504 (2016)。
   該數字**只出現在搜尋摘要層級，原文四輪都被 AIP 403 擋下（`output/wf0907/R4/3504_1_online.pdf` 實際是 5,619 bytes 的
   Cloudflare 攔截頁），沒有任何原文支撐**——依本文件 §2.5 對 X1／X3 採取的同一標準（「摘要說有不算有」），
   **本版把該數字整條刪除**，只保留「這篇論文是取得後最值得拿來校準 `F_peak` 的一篇」這個待查條目（見 §5）。
   在拿到原文之前，**457 N 是高估還是合理，本文件不作任何主張**。
3. `pressure_per_force_real_pa_n` 的語意（每牛頓的什麼力、施在哪裡）本輪未逐行讀 B6 的實作確認，
   直接相乘可能語意不匹配。**這一點必須在 B7 動工時由工兵親自核對。**

### 3.7 第三輪的獨立複驗（2026-09-08，本輪的主要工作）

本輪的前提是**不採信本文件上一版的任何自報**。三件事全部重做：

**(1) 三條吃重的引述，從 PDF 文字層重新逐字撈出來**
（用 `re.finditer` 定位 + 前後 300 字上下文輸出，不是靠記憶或上一版的轉述；
輸出在 `output/wf0907/R4/round3/_verify_a12.txt` 與 `_verify_c9_b9.txt`）：

| 要複驗的主張 | 本輪撈到的原文 | 結果 |
|---|---|---|
| A12 的公式 | “In this work, the mapping between MIDI velocity units and final hammer velocity (m/s) as measured by the Bösendorfer system **was chosen to be MIDIvel = 52 + 25 · log2(fhv ),  (3.2)**” | ✅ 一字不差 |
| B9 的配對數字 | 圖內標註 “**maxHv: 3.765 m/s**” / “**SPL: 101.13 dB**” 與 “**maxHv: 2.794 m/s**” / “**SPL: 98.53 dB**”，圖說 “**A forte attack (C4, MIDI note number 60) played by one pianist**” | ✅ 一字不差 |
| C9 的尺寸與質量 | “we refined the model by considering now the structure as an isotropic rectangular plate, of constant thickness, **of dimensions Lx = 1.39 m, Ly = 0.91 m and total mass M = 9 kg**” | ✅ 一字不差 |
| B11 的 1.5 m 麥克風距離 | “The microphones (two AKG CK91 positioned in an ORTF setup) were positioned aside the grand piano at the open lid **about 1.5 meters from the strings**” | ✅ 一字不差（本輪另補到「置於掀起的琴蓋旁」這個位置細節，上一版沒寫） |

**額外收穫**：搜 A12 時發現該式在論文裡出現**四次**（上一版只記兩次）→ 已新增為 A13。

**(2) 每一條算術，不看上一版答案重算**
（`output/wf0907/R4/round3/arithmetic_recheck.txt`）：

| 算式 | 本輪重算 | 上一版 | 一致？ |
|---|---|---|---|
| A12 反解 MIDI 40／60／77／110／127 | 0.7170／1.2483／2.0000／4.9933／8.0000 m/s | 0.717／1.248／2.000／4.993／8.000 | ✅ |
| A12 正解 0.18 m/s ／ 6.8 m/s | MIDI −9.85 ／ 121.14 | −9.85 ／（未寫）| ✅（並補上 6.8 m/s 落在 MIDI 121.14，正是「MIDI>120 無支撐」這句話的來源）|
| B9 同鍵指數 `20log10(3.765/2.794)` | 2.5908 dB（實測差 2.60） | 2.59 | ✅ |
| A3 全域指數 `60.4 / 20log10(6.8/0.18)` | 60.4 / 31.544728 = **1.9147** | 1.9147 | ✅ |
| C9 面積 `1.39 × 0.91` | **1.2649 m²** | 1.2649 | ✅ |
| 生木密度反推 `9/(400×0.008)` 與高估倍率 | 2.8125 m²，倍率 **2.2235** | 2.812、2.22 | ✅ |
| 等效面密度 `9 / 1.2649` | **7.1152 kg/m²** | 7.115 | ✅ |

**(3) 引擎數字重跑**（唯讀，`output/wf0907/R4/round3/dump_modes_reverify.txt`）：

```
TsukiSynthCLI.exe --dump-modes scores/examples/physical_piano.score.json
model_observables       : [..., 'radiated_power_relative', 'absolute_pressure_per_force']
unsupported_observables : ['complex_phase', 'absolute_spl', 'radiation_directivity']
events[0].acoustic_transfer[0].radius_m                     = 1.05
events[0].acoustic_transfer[0].pressure_per_force_real_pa_n = 0.3065508
```

→ 與 §3.1 完全一致；`absolute_spl` 仍在 `unsupported_observables`（引擎仍未主張絕對 SPL）。

**本輪未重跑的部分（誠實聲明）**：§3.2 的十點力度掃描與 §3.3 的三點重跑**本輪沒有再跑第三次**
——那兩節在上一輪已經是「重跑並比對到小數第 12 位」的結果，本輪把有限的時間用在
**補搜兩個仍缺的格子**與**逐字複驗引述**上。§3.1 這一顆重跑成功，可視為同一顆 exe 行為未變的抽樣證據，
**但不等於 §3.2 全表都重驗過**。

### 3.8 第四輪的獨立複驗（2026-09-08，唯讀）

本輪同樣不採信前三輪的自報，做了三件可被複核的事
（全部輸出在 `output/wf0907/R4/round4/round4_evidence.txt`）：

**(1) 引擎診斷分接點重跑**

```
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --dump-modes scores\examples\physical_piano.score.json
model_observables       : [..., 'radiated_power_relative', 'absolute_pressure_per_force']
unsupported_observables : ['complex_phase', 'absolute_spl', 'radiation_directivity']
events[0].acoustic_transfer[0].radius_m                     = 1.05
events[0].acoustic_transfer[0].pressure_per_force_real_pa_n = 0.3065508
```

→ 與 §3.1／§3.7 完全相同。

**(2) 渲染重跑並比 SHA256（本輪比前三輪多做的一步）**

用上一輪留下的 `output/wf0907/R4/verify/v100.score.json`（C4、velocity 1.00）重新渲染：

```
pre_normalize_peak = 0.176104545593262
wav_sha256         = ac573b65b975440031438befdfe2ae250f374f8d28a9da5b0a107fd49a6ce5f4
```

→ `pre_normalize_peak` 與 §3.2／§3.3 一致到小數第 12 位，**且 WAV 的 SHA256 與上一輪的
`verify/v100/physical_piano.wav.render.json` 完全相同 = 位元級一致**。
（前三輪只比對了數值，沒有比對 SHA；本輪補上這一步。）

**(3) 兩條吃重引述再撈一次原文**

從本地 PDF 文字層重新以正則定位（不看前一版的轉述）：

| 主張 | 本輪撈到的原文 | 結果 |
|---|---|---|
| A12 公式 | “…was chosen to be MIDIvel = 52 + 25 · log2(fhv ), (3.2)” 與 “a logarithmic map was always used: MIDIvelocity = 52 + 25 · log2(FHV )” | ✅ 一致，且本輪同樣數到**四處** |
| C9 尺寸與質量 | “…as an isotropic rectangular plate, of constant thickness, of dimensions Lx = 1.39 m, Ly = 0.91 m and total mass M = 9 kg” | ✅ 一致 |

**本輪未重跑的部分（誠實聲明）**：§3.2 的十點力度掃描、§3.5 的對照表、§3.6 的力鏈試算
**本輪未再重算**（前兩輪已各自重算過一次，且本輪 (2) 證明同一顆 exe 的輸出位元不變）。
本輪的時間用在**補搜第三塊資料**（§2.3 C16–C18）與上述三項抽樣複驗。

---

## 4. 選項與建議（含「可否開工」判定）

### 4.1 三塊資料各自的判定

| 缺口 | 判定 | 理由 |
|---|---|---|
| **A. velocity → 槌速** | **資料齊；但「可開工」要打折** | **有封閉形式公式（A12），三個對照點與它相符到印刷精度。**（**2026-09-09 更正措辭**：不得再寫「三個獨立量測點交叉驗證全中」——見 §2.1 的兩點：兩組來源之間有原文言明的 **+14% 槌速校正差**，且三個對照點很可能就是用同一條 map 換算出來的。**系統性偏差 ≥ 殘差**，殘差小不代表準確度高。） 已知邊界：MIDI < 20 與 > 120 無實測支撐。**兩個前置未解**：(1) 引擎力度有三種定義未裁決；(2) 落地會改動 1d 這條已判定 GATE 與既有渲染輸出＝Rule 10 情境（見 §3.4） |
| **B. SPL 範圍** | **缺（不能用「1 m 處 pp 60 / ff 100 dB」當 GATE）** | 唯一的絕對量測都在 10 cm 近場（B1/B9）；1.5 m 那組（B11）縱軸是相對 dB；且 B12 明說 >5 m 才是遠場 |
| **C. 音板面積 `S`**（**2026-09-08 第四輪改判**） | **論文層級仍缺；廠商規格層級已有數字，可作為「標明等級後的代用值」** | **第四輪新增**：Baldwin 官方規格給出六台平台琴的音板面積 **0.87–1.68 m²**（C16），且同廠 47 吋直立琴的 **1.2774 m²** 與 Ege 論文實測的 **1.2649 m²** 只差 **0.99%**（C17），代表這組規格欄與論文量測對得起來；C18 另證實作者手上有 Steinway B/D 的完整尺寸圖但未印出面積。**仍然缺的是**：(1) 同儕審查來源；(2) 九尺演奏琴的面積；(3)「板面積 → 有效輻射面積」的換算依據。**下述舊判定保留作對照** |
| **C（第三輪原判定，保留備查）** | **缺（平台琴無出處，三輪累計已窮舉 10 個來源）** | 直立琴的 1.2649 m² 在**兩篇論文裡都印出來**（C1 尺寸、C9 尺寸＋`M = 9 kg`）——**2026-09-08 第五輪更正措辭：兩篇是同一研究群、同一台 Atlas 直立琴，不是兩組獨立量測**；`M` 的組成另有第三篇原文定義（C12）；**平台琴十個來源全無**（連專做平台琴音板模態分析的 C6 都沒寫板子多大多重，本輪親自重掃確認）。`S=M/(ρh)` 反推路線：`M` 其實查得到（C9），但用生木密度反推會高估 2.22 倍，且平台琴仍無 `M`（見 §2.3「C7／C9 更正說明」） |

### 4.2 給月月的三個選項（白話）

**選項 1（建議）：velocity→槌速照 A12 落地；驗收基準改成「動態範圍差幾分貝」，不驗絕對音壓。**

- 做什麼：程式裡把力度換成槌速時，用 `槌速 = 2^((MIDI − 52) / 25)` 這條**有出處的公式**；
  驗收不驗「1 公尺處是幾分貝」，改驗「最小力度到最大力度差幾分貝，有沒有落在文獻範圍內」。
- 為什麼可行：velocity→槌速這一段**終於有出處了**（A12），不必再自己編公式。
- **代價與必須寫進 GATE 註解的四件事**：
  1. 這個 GATE **不驗絕對音壓**，B7 §0 說的「一路推到真實 Pa」只完成到一半。
  2. 引擎的「動態範圍」**不是一個客觀數字**——它完全取決於你把最小 velocity 訂在哪
     （0.01→67.4 dB、0.02→60.1 dB、0.05→51.9 dB，見 §3.2）。**GATE 必須先訂死一個下限並說明理由**，
     否則這個基準可以被隨意調成任何值。**上一版寫的「文獻 60.4 dB vs 引擎 60.1 dB 很接近」
     是拿本文件自選的 0.02 湊出來的，2026-09-07 複核已撤回這個理由。**
     另外同一個下限下，跨音高還會再差 10.6 dB（C2 49.5／C4 60.1／C7 49.8 dB），**GATE 必須分音域寫**。
  3. **Goebl 的 60.4 dB 是「不同鍵 + 不同觸鍵法」的合成極值，引擎的數字是同一顆音的範圍。
     這兩件事本質不同，不能對齊。**（見 §2.2 B9 附帶推論。）
     **本文件不提出任何具體容忍數字**（Rule 2：禁止自訂新容差）——只指出
     「這個比對本質不對等」這個事實，**窗口由月月/規劃者裁決**。
  4. **⚠️ 這條公式現在還接不上引擎，而且會踩到既有的判定。** 兩個原因（詳見 §3.4）：
     (a) 引擎的「力度」現在有**三種算法**（插件、score 檔、MIDI 轉譜器各一種），
         沒先講好 A12 的 MIDI 值對應哪一種，代入就是把兩個不同的東西當同一個東西用；
     (b) 引擎裡**已經有一條被機器驗證中的力度律**（velocity 加倍→音量固定變化），
         換成 A12 的指數律會改掉它，也會改掉既有樂曲的渲染結果——
         這是 README **Rule 10**（停下、寫前後對照報告、不得自行落地）的情境。
     **也就是說：選項 1 是「可以選的方向」，不是「明天就能動工」。**

**選項 2：B7 只做 Phase 0，然後停在這裡。**

- 做什麼：把本文件的結果收進 `docs/HAMMER_VELOCITY_SOURCES.md`（B7 §3 指定要新建的檔），
  `S` 那一格誠實寫「查無」，卡標為「Phase 0 完成、Phase 1 阻塞」。
- 為什麼可行：B7 卡自己 §10/§12 就明寫「查不到、誠實記錄、卡在這裡」是合法完成路徑。
- 代價：力鏈不接通，B6 的雙路徑交叉驗證做不了。
- **本輪相對上一版的變化**：因為 A12 找到了，選項 2 的相對吸引力下降了——
  現在三塊裡有一塊是真的齊了，停在這裡會浪費這條公式。

**選項 3（不建議）：硬湊 `S` 與 SPL 門檻，把整條鏈接通。**

- 為什麼不建議：§3.6 的試算顯示，即使把兩條路徑接起來，量級差約 29 dB。
  在 `S` 沒出處、SPL 門檻沒出處的情況下接通，等於**用兩個編出來的數字去湊一個看起來合理的結果**，
  正是 Rule 4 要擋的事。

### 4.3 若走選項 1：映射函數的具體落地形態

**用 A12 的原式，不要用擬合式。**（上一版曾提出一條自己擬合的冪律
`v = 0.00197788 × MIDI^1.5863`——**本版正式撤回該擬合式**，因為現在有論文自己寫出來的封閉解，
而且那條擬合式在 MIDI 127 只給 4.30 m/s，比實測最大 6.8 m/s 低估 37%。）

```
hammerVelocityMps (midiVelocity) = 2 ^ ((midiVelocity - 52) / 25)
```

落地時必須同時做到的四件事：

1. **註明出處，並且註明它落在哪一把尺上**：Goebl (2003) 博士論文 Ch.3 §3.7 式 (3.2)（＝ Ch.2 註 23）。
   **必須同時寫進 §2.1 的 14% 校正差**：本式與 A2（MIDI 77 → 2 m/s）同屬**未校正**刻度；
   而 A1（40 → 0.7、60 → 1.25）與 A3（0.18／6.8）出自 Goebl et al. (2005)，該篇槌速資料**全部 +14%**。
   **註解不得寫「交叉驗證通過、殘差 0.5%」**（2026-09-09 複核更正：那句誤導）。正確寫法是：
   「三個對照點與本式相符到印刷精度，但兩組來源之間存在原文言明的 ≥14% 系統性刻度差，
   且三個對照點很可能本來就是用同一條 map 換算出來的（§2.1 (2)，本專案的推論）——
   **系統性偏差 ≥ 殘差；殘差小只證明自洽，不證明準確**。可用精度下限以 ±14%（≈ ±1.14 dB）為底。」
2. **註明定義域**：**MIDI 20–120 有實測支撐；此區間外為外推。**
   建議在 MIDI < 20 與 > 120 兩端 clamp 到 A3 的實測極值 **0.18 / 6.8 m/s**
   （`HammerImpulse.h` 既有的 `interpAnchorsFlat()` 就是這個 clamp 體例，寫法一致）。
3. **註明性質**：原文是 **“was chosen to be”**——這是 Bösendorfer SE 系統的裝置慣例，
   **不是物理定律**；它的可信度來自與三個獨立量測點一致，不是來自「論文說了算」。
4. **先解決 §3.4 的兩個前置**（白話版已放在 §0 的警語裡）：
   (a) 決定引擎的 0–1 proxy 到底對應 MIDI/127、還是轉譜器那條 `/90` 曲線——
       **沒決定就代入 = 把兩個不同定義的東西當同一個東西用**；
   (b) 這條指數律會取代 `ScoreParser.h:295–308` 登記的「振幅正比於 velocity」關係，
       動到 `physics_verify.py` 1d 這條**已判定 GATE**，並改變既有 score 的渲染輸出。
       **依 README Rule 10：停下、寫前後對照報告、不得自行落地。**

---

## 5. 已知缺口（下一步能去哪找）

| 缺口 | 現況 | 下一步具體管道 |
|---|---|---|
| **1 m 處的絕對 SPL** | **連續四輪查無**。所有絕對量測都在 10 cm；最接近的 1.5 m 那組（B11）縱軸是相對 dB。第四輪另外排除了三條管道：TU Berlin 無響室資料庫的第二篇論文同樣不含鋼琴（B15）、NASM–PAMA 宣導單只有「近距離 60–70 dB」而無距離定義（B14）、AIP 的 POMA/JASA 直連 PDF 仍回 403 | **本文件的判斷：免費管道已經查完了。** 剩下三條都需要月月出手：(1) 向 Goebl 本人（mdw IWK，個人頁面公開）索取 Fig. 2.20 的原始絕對校準值（他有 B&K 4230 校準紀錄）；(2) 用機構帳號取得 Roginska et al. 2013 POMA 全文；(3) 借閱 Meyer《Acoustics and the Performance of Music》的動態範圍表 |
| Goebl 博士論文 Fig. 2.17 / 2.20 的曲線座標 | 圖存在、全文已取得，PDF 文字層無座標 | 用 WebPlotDigitizer 從 PDF 圖抽點（本輪未做，屬下一張卡的工作量） |
| Roginska et al. (2013) POMA 全文 | AIP 403 ×3 管道 | POMA 通常開放取用，走機構代理／ILL；或向 NYU 作者索取 |
| Boutillon (1988) JASA 83:746 原文 | 未取得 | 確認 0.11–6.83 m/s 的量測條件——這是 A4 目前唯一的弱點 |
| *Reconstruction of piano hammer force from string velocity*, JASA 140:3504 (2016) | AIP 403 | 取得後可校準 §3.6 的 `F_peak` 是否高估——判斷 Path C 能否收斂的關鍵 |
| ISO 23591:2021 Table A.1 的鋼琴聲功率 | 預覽版無數值 | 購買標準；或找引用該表且列出鋼琴數值的論文（Rindel 2014 / DAGA 2022 兩篇都不含鋼琴列） |
| Meyer《Acoustics and the Performance of Music》鋼琴動態表 | 未取得書 | 圖書館；本輪搜尋只能查到書存在與轉述，**無法逐字引用** |
| 平台鋼琴音板面積 `S`（**第四輪更新**） | **論文層級仍查無；廠商規格層級已取得六台（0.87–1.68 m²，C16），並以同廠直立琴與 Ege 論文對到 1% 以內（C17）** | 若規劃者接受「廠商規格 + 標明等級」：**現在就可以用 C16 中與目標琴長相符的那一筆**。若要同儕審查來源：仍是下一列那三條管道；另可向 Boutillon/Ege 索取 C18 致謝欄提到的 **“dimension report of the grand pianos”**（Steinway B/D 的尺寸圖，作者手上有但未發表） |
| 平台鋼琴音板面積 `S`（第三輪原記錄，保留備查） | **查無（三輪累計 10 個來源；直立琴有兩篇正面，平台琴全部負面）** | **最優先：Corradi et al. 2017 的 soton 開放 postprint（C15）**——`https://eprints.soton.ac.uk/408405/1/20160514_postprint.pdf`，站台只是擋自動下載，**月月用一般瀏覽器點開就能存**（該研究是 Fazioli 平台琴的完整 FE 建模，最可能寫出板子尺寸與質量）；其次 Suzuki 1986 全文（6 呎平台琴，標題就是輻射）；再次 INRIA RR-8097/RR-8181 |
| INRIA RR-8181 全文 | **HAL 站台 anti-bot 攔截，本輪未嘗試繞過（規則禁止）** | 由月月用機構帳號／一般瀏覽器開 `inria.hal.science` 下載即可 |
| Ege & Boutillon 的音板總質量 `M` | **已找到：`M = 9 kg`（arXiv:1210.5688，直立琴）**——上一版誤報「查不到」，2026-09-07 複核更正 | `RADIATION_POWER_SOURCES.md` §5 的 `S=M/(ρh)` 路線建議加註兩點：(1) 該 `M` 是等效均向板質量，用生雲杉密度反推會高估 2.22 倍；(2) 直立琴不必反推（尺寸原文直接給），平台琴則連 `M` 都沒有 |
| 音板面密度 `ρs` 的取值 | 本輪由 C9 得到**實測等效值 7.115 kg/m²**（直立琴，含肋條與琴橋）；`RADIATION_POWER_SOURCES.md` §3 現用 **3.6 kg/m²**（裸雲杉 9 mm × 400 kg/m³ 的假設值），**兩者差近一倍** | 需規劃者判斷 B5／B7 的哪一步該用哪一個；本卡不主張 |
| 引擎 velocity proxy 的定義 | **三條路徑三種定義（§3.4）** | 需月月/規劃者裁決，B7 動工前必須先定 |
| A12 落地 vs 既有 1d velocity GATE 的衝突 | **本輪已確認衝突存在**（§3.4）：A12 是指數律，`ScoreParser.h:295–308` 登記的是振幅正比於 velocity | 需規劃者按 Rule 10 開一張「前後對照」卡；本卡無權裁決 |
| `ScoreParser.h:295–308` 註解對 piano 已過時 | 該註解說 piano 被判 +6.0 ± 1.0 dB，但 2026-08-27 的 B4 裁決已把 Felt/`tau_c(v)` 路徑改判「render vs model 自身預測」（本輪 GATE 輸出實證） | 本卡不碰 `src/`，列入 `open_items` 交規劃者 |
| §3.6 用到的 `pressure_per_force_real_pa_n` 語意 | 未逐行核對 B6 實作 | B7 動工時第一件事就是讀 `ScoreRenderer.h::dumpModes()` 該欄位的產生程式碼 |

---

## 附錄：本輪來源清單

**外部來源清單（下表共 43 列）**

> **`sources_count` 的算法（2026-09-08 第五輪更正）**
> 上一輪回報 `sources_count = 43`，那其實是**下表的列數**，會高估。本版把帳算清楚：
>
> | 分類 | 列數 | 說明 |
> |---|---|---|
> | 下表列數 | **43** | 含 1 組重複 |
> | 扣掉重複後的**相異作品數** | **42** | 第 20 條與第 43 條是**同一篇** Roginska et al. 2013 POMA，第 43 條只是第四條取得管道，兩條都沒取得任何內容 |
> | 其中**取得原文／全文並逐字核對** | **31** | 第 1–17、24–30、32、34–39 條 |
> | 其中**僅摘要**（不採用任何數字） | **2** | 第 18（Suzuki 1986）、第 21（Repp 1993）條 |
> | 其中**未取得原文**（付費牆／403／反機器人／TLS 錯誤） | **9** | 第 19、20（＝43）、22、23、31、33、40、41、42 條 |
>
> **本輪回報的 `sources_count` 採用「取得原文並逐字核對的相異來源數」＝ 31**，
> 未取得與僅摘要的那 11 篇仍列在表內（研究卡鐵律第 4 條：查不到也要寫下來），但**不計入**。
> 另請注意第 32 條（Riverton 部落格）與第 38 條（TU Berlin 資料庫）雖然計入「已取得」，
> 它們的角色是**反面證據**（證明某個數字不在那頁 / 該資料庫不含鋼琴），不提供任何可用數字。

| # | 來源 | 取得方式 | 存取日期 | 用在哪 |
|---|---|---|---|---|
| 1 | Goebl, Bresin & Galembo, *JASA* 118(2):1154–1165 (2005), "Touch and temporal behavior of grand piano actions"，`https://iwk.mdw.ac.at/goebl/papers/Goebl-Bresin-Galembo_JASA2005_PianoAction.pdf` | PDF 全文 + `pdftotext`（本輪重新逐句 grep 核對） | 2026-09-08 | A1, A3, A6, B1 |
| 2 | Goebl & Bresin, *JASA* 114(4):2273–2283 (2003), "Measurement and reproduction accuracy of computer-controlled grand pianos"，`https://iwk.mdw.ac.at/goebl/papers/Goebl-Bresin_JASA2003_reproAccuracy.pdf` | PDF 全文（本輪重新核對） | 2026-09-08 | A2, A7, B2 |
| **3** | **Goebl, *The Role of Timing and Intensity in the Production and Perception of Melody in Expressive Piano Performance*, PhD diss., Univ. Graz, 2003（= OFAI TR-2003-28），`https://ofai.at/papers/oefai-tr-2003-28.pdf`** | **PDF 全文自取（2,946,357 bytes，本輪重新下載成功）+ `pdftotext`** | **2026-09-08** | **A12, B9, B10, B11**（本輪最關鍵來源） |
| 4 | Woodhouse, *Euphonics* §11.2，`https://euphonics.org/11-2-hitting-strings-the-piano-and-its-relatives/` | HTML 全文 | 2026-09-08 | A4（含 Boutillon 1988 完整書目） |
| 5 | Chabassier, Chaigne & Joly, *JASA* 134(1):648–665 (2013)，`https://perso.ensta-paris.fr/~touze/PDF/Batwoman/chabassier-jasa.pdf` | PDF 全文 | 2026-09-08 | A8, B4, C3 |
| 6 | MIDI 1.0 Detailed Specification 96.1（MMA），第三方鏡像 `https://freqsound.com/SIRA/MIDI%20Specification.pdf` | PDF 全文 | 2026-09-08 | A9 |
| 7 | *A Database with Directivities of Musical Instruments*, arXiv:2307.02110 | PDF 全文 | 2026-09-08 | B5（負面結果） |
| 8 | Rindel, Forum Acusticum 2014，`https://www.odeon.dk/pdf/RehearsalRooms_ForumAcusticum2014_Rindel.pdf` | PDF 全文 | 2026-09-08 | B6（負面結果） |
| 9 | Rindel/Odeon, DAGA 2022，`https://odeon.dk/pdf/C149-DAGA_2022_000171.pdf` | PDF 全文 | 2026-09-08 | B6 佐證（同樣不含鋼琴） |
| 10 | ISO 23591:2021 預覽 PDF，`https://cdn.standards.iteh.ai/samples/76335/defa5ab1787744d9a496ba46df1ec2cb/ISO-23591-2021.pdf` | PDF（預覽版） | 2026-09-08 | B7 |
| 11 | Ege, Boutillon & Rébillat, arXiv:1212.2323 | PDF 全文 | 2026-09-08 | C1 |
| 12 | Boutillon & Ege, arXiv:1305.3057 | PDF 全文 | 2026-09-08 | C2, C8（負面結果）, C7（該篇無 `M`） |
| 13 | Ege & Boutillon, arXiv:1212.3068 | PDF 全文 | 2026-09-08 | C7（負面結果） |
| **14** | **Ege & Boutillon, *Synthetic description of the piano soundboard mechanical mobility*, arXiv:1210.5688** | **PDF 全文自取** | **2026-09-08** | **C9（直立琴尺寸＋`M = 9 kg`，2026-09-07 複核後改列為正面結果）、C7** |
| **15** | ***The effect of Mounted Ribs on the Radiation of a Soundboard*, arXiv:1011.5372** | **PDF 全文自取（本輪新增）** | **2026-09-08** | **C10（負面結果）** |
| 16 | Corradi et al., ISMA 2010，`https://past.isma-isaac.be/downloads/isma2010/papers/isma2010_0202.pdf` | PDF 全文 | 2026-09-08 | C6（負面結果） |
| **17** | **DPA Microphones, *Piano sound fields and miking implications*，`https://www.dpamicrophones.com/mic-university/background-knowledge/piano-sound-fields-and-miking-implications/`** | **HTML（本輪新增）** | **2026-09-08** | **B12（業界技術文件）** |
| 18 | Suzuki, *JASA* 80(6):1573 (1986)，`https://pubs.aip.org/asa/jasa/article-abstract/80/6/1573/664960/` | 僅摘要 | 2026-09-08 | C4 |
| 19 | Giordano, *JASA* 103(4):2128 (1998)，`https://pubs.aip.org/asa/jasa/article/103/4/2128/561409/` | 未取得原文（付費牆） | 2026-09-08 | C5 |
| 20 | Roginska et al., *POMA* 19:035006 (2013)，`https://pubs.aip.org/asa/poma/article/19/1/035006/570446` | 未取得原文（**四條管道全失敗**，第四條見第 43 條） | 2026-09-08 | B3 |
| 21 | Repp, *JASA* 93(2):1136 (1993)，`https://pubmed.ncbi.nlm.nih.gov/8445121/` | 僅摘要 | 2026-09-08 | A11 |
| 22 | *Reconstruction of piano hammer force from string velocity*, *JASA* 140:3504 (2016)，`https://pubs.aip.org/asa/jasa/article/140/5/3504/679284/` | 未取得原文（403；`output/wf0907/R4/3504_1_online.pdf` 實為 5,619 bytes 的 Cloudflare 攔截頁） | 2026-09-08 | §5 待查表——**2026-09-08 第五輪：原本掛在 §3.6 註 2 的「約 32 N」摘要級數字已整條刪除，本條現在只是一條「待取得」記錄，不提供任何數字** |
| **23** | **INRIA Research Report RR-8181（Chabassier et al.），`https://inria.hal.science/file/index/docid/768234/filename/RR-8181.pdf`** | **未取得原文（HAL anti-bot 攔截頁；本輪未嘗試繞過）** | **2026-09-08** | **C11** |
| 24 | **社群** Piano World「Piano decibel levels」，`https://forums.pianoworld.com/ubbthreads.php/topics/1261780/piano-decibel-levels.html` | HTML | 2026-09-08 | S1 |
| 25 | **社群** Modartt/Pianoteq 論壇 id=6943，`https://forum.modartt.com/viewtopic.php?id=6943` | HTML | 2026-09-08 | S2 |
| **26** | **Askenfelt & Jansson, "From touch to string vibrations"，KTH 五講義，`https://www.speech.kth.se/music/5_lectures/askenflt/motions.html`** | **HTML 全文（第三輪直接 fetch，逐字引述）** | **2026-09-08** | **A5（本輪由「不計入」升級為正式外部來源）** |
| **27** | **Ege & Boutillon, *Global and local synthetic descriptions of the piano soundboard*, Forum Acusticum 2011, arXiv:1210.5109，`https://arxiv.org/pdf/1210.5109`** | **PDF 全文自取（997,166 bytes）+ `pdftotext`** | **2026-09-08** | **C12（`M` 組成的原文定義；平台琴與面積為負面結果）** |
| **28** | **Conklin, *Piano design factors*（KTH 五講義）soundboards 分頁，`https://www.speech.kth.se/music/5_lectures/conklin/soundboards.html`** | **HTML 全文** | **2026-09-08** | **C13（厚度第三來源；面積為負面結果）** |
| **29** | **Wogram, *The strings and the soundboard*（KTH 五講義），`https://www.speech.kth.se/music/5_lectures/wogram/index.html`（＋ `impedance.html`）** | **HTML 全文** | **2026-09-08** | **C14（負面結果）** |
| **30** | **Robjohns, H., *Q. How loud is a concert grand piano?*, Sound On Sound, 2025-01，`https://www.soundonsound.com/sound-advice/q-how-loud-concert-grand-piano`** | **HTML 全文** | **2026-09-08** | **B13（業界技術文件；dB 數字不採用）** |
| **31** | **Corradi, Miccoli, Squicciarini & Fazioli, *Modal analysis of a grand piano soundboard at successive manufacturing stages*, Applied Acoustics 125:113–127 (2017)，`https://eprints.soton.ac.uk/408405/1/20160514_postprint.pdf`** | **未取得原文（Anubis 反機器人；curl 取回 2,314 bytes HTML、WebFetch 403。未嘗試繞過）** | **2026-09-08** | **C15——目前最值得月月手動取得的一篇** |
| **32** | 鋼琴經銷商部落格（Riverton Piano, 2026-03-05），`https://blog.rivertonpiano.com/2026/03/05/grand-piano-sizes-explained-what-fits-and-what-sounds-best/` | HTML 全文（**核對後證實搜尋摘要所稱的「over 20 square feet」不在該頁**） | 2026-09-08 | **X1——反例，數字已丟棄，不作為證據** |
| **33** | Steinway Model D 廠商技術規格頁，`http://www.steinway-piano.com/steinway-piano-models/steinway-model-d-technical-specifications/` | **未取得原文（TLS 憑證主機名不符）** | 2026-09-08 | **X2——數字未核對，不採用**（該主張已由第 34 條補上出處） |
| **34** | **Boutillon, Ege & Paulello, *Comparison of the vibroacoustical characteristics of different pianos*, arXiv:1210.3948，`https://arxiv.org/pdf/1210.3948`** | **PDF 全文自取（984,806 bytes）+ `pdftotext`（`-layout` 與 `-raw` 兩種版面各掃一次）** | **2026-09-08** | **C18（Steinway B/D 厚度為正面；面積為負面；致謝欄證實作者持有平台琴尺寸圖）** |
| **35** | **Baldwin Piano 官方平台琴型號規格頁 ×6：`baldwinpiano.com/BP148.html`、`BP152.html`、`BP165.html`、`BP178.html`、`BP190.html`、`BP211.html`** | **HTML 全文自取（各約 24–27 KB），剝標籤後逐頁核對 “Soundboard Area: Sq. In. …” 字串** | **2026-09-08** | **C16（平台琴音板面積六筆）** |
| **36** | **Baldwin Piano 官方直立琴型號規格頁 ×4：`B342-B42-Acrosonic.html`、`B442-B42-Acrosonic.html`、`B243-New.html`、`B252-Concert-Vertical.html`** | **HTML 全文自取，同上逐頁核對** | **2026-09-08** | **C17（直立琴面積，用來對 C16 做可信度檢查）** |
| **37** | **NASM–PAMA, *Protecting Your Hearing Health — Student Information Sheet*，西伊利諾大學鏡像 `https://www.wiu.edu/cofac/music/pdf/NASM-PAMA.pdf`** | **PDF 全文自取（811,257 bytes）+ `pdftotext`** | **2026-09-08** | **B14（協會宣導文件，dB 數字不得當 GATE）** |
| **38** | ***A Database of Anechoic Microphone Array Measurements of Musical Instruments*（TU Berlin DepositOnce 開放全文）** | **PDF 全文自取（992,710 bytes，5 頁）** | **2026-09-08** | **B15（負面結果：全文 `piano` 0 命中）** |
| **39** | Mamou-Mani, *Effets de la mise en charge de la table d'harmonie du piano*（ATIAM 2003–04 實習報告），`http://www.atiam.ircam.fr/Archives/Stages0304/mamou.pdf` | PDF 全文自取（3,251,800 bytes） | 2026-09-08 | **負面結果**：全文無鋼琴音板尺寸／面積／質量（實驗對象是碳纖維試樑，`42 cm` 那根） |
| **40** | Trévisan, Ege & Laulagnet, *A modal approach to piano soundboard vibroacoustic behavior*, *JASA* 141(2):690–709 (2017)，HAL 開放版 `https://hal.science/hal-01456083/file/Trevisan_JASA2017_HAL.pdf` | **未取得原文**（HAL 回 Anubis 反機器人頁，12,602 bytes HTML；本輪未嘗試繞過） | 2026-09-08 | **未取得**——（且該研究對象是**直立琴**，即使取得也不直接補平台琴那一格） |
| **41** | Ege, *La table d'harmonie du piano — Études modales…*（博士論文，2009），舊版 HAL 直連 `http://tel.archives-ouvertes.fr/docs/00/46/17/77/PDF/These_Ege.pdf` | **未取得原文**（同樣被 HAL 反機器人擋下，回 12,563 bytes HTML） | 2026-09-08 | **未取得**——**這是最可能載有 Steinway B/D 面積的一份**（C18 論文的模型就出自這本），見 §5 |
| **42** | Weinzierl 等, *Sound power and timbre as cues for the dynamic strength of orchestral instruments*, *JASA* 144(3):1347 (2018)，AIP 直連 PDF | **未取得原文（403，回 5,769 bytes HTML）** | 2026-09-08 | 第四輪為 SPL 缺口新試的管道，**未取得，任何數字不採用** |
| **43** | **（＝第 20 條同一篇，不另計為相異來源）** Roginska et al. POMA 19:035006 的**第四條**取得管道（AIP `article-pdf/doi/10.1121/1.4800310/...` 直連）＋ 作者 NYU 個人出版頁 `https://wp.nyu.edu/roginska/publications/` | **未取得原文**（AIP 直連回 5,883 bytes HTML——即 `output/wf0907/R4/round4/poma_roginska.pdf`，實為 Cloudflare 攔截頁；NYU 頁面該篇無 PDF 連結，本輪 WebFetch 確認） | 2026-09-08 | B3 的補充記錄——**四條管道全部失敗**。**2026-09-08 第五輪標註：本列與第 20 條指向同一篇，`sources_count` 只算一次** |

**本輪產生的唯讀量測檔（`output\wf0907\R4\`，已 gitignore）**

- `dump_modes_piano.json`——`--dump-modes` 原始輸出（§3.1）
- `engine_dynamic_range.txt`——力度掃描的 `pre_normalize_peak` 與 dB 表（§3.2）
- `verify/`——§3.3 的獨立重跑（v002／v030／v100 重新渲染 + manifest）
- `goebl_map_vs_engine.txt`——**本輪新增**：A12 的正反解全表、與 A1/A2/A6 的交叉檢查、
  B9 兩點的指數推算、以及 §3.5 的引擎對照表（含全部算式與輸入）
- `fpeak_scale_check.txt`——力鏈量級試算全表（§3.6）
- `goebl_diss2.pdf` / `goebl_diss2.txt`——**本輪新增**：完整的 Goebl 博士論文與其文字層
- `dpa_piano.html`——**本輪新增**：B12 的原始 HTML（引文由此逐字核對，非由摘要轉述）
- `arx_1210.5688.*` / `arx_1011.5372.*`——**本輪新增**：C9／C10 兩篇負面結果的全文與文字層
- `dyn/`——掃描用的暫用 score 與渲染輸出（皆由 `physical_piano.score.json` 衍生，未改原檔）
- `B7_PHASE0_DATA.prev_round.md`——本文件上一版的備份（未覆寫遺失）
- `round3/`——**2026-09-08 第三輪新增**：`_verify_a12.txt`／`_verify_c9_b9.txt`（A12／B9／C9／B11 的原文逐字撈取）、
  `arithmetic_recheck.txt`（全部算術的獨立重算）、`dump_modes_reverify.txt` ＋ `r3_dump_modes.json`（引擎重跑）、
  `_5109_scan.txt` ＋ `arx_1210.5109.pdf/.txt`（C12 新來源全文與掃描）、`_isma_scan.txt`（C6 的獨立重掃）、
  `new_sources_round3.txt`（本輪六個新來源的逐字引述與兩筆丟棄記錄）
- `B7_PHASE0_DATA.prev_round3.md`——第三輪動筆前的完整備份
- `round4/`——**2026-09-08 第四輪新增**：`round4_evidence.txt`（本輪全部引述的原文上下文、
  Baldwin 十頁規格的逐字字串、平方英吋→平方公尺的換算與 Ege 對照、引擎重跑結論）、
  `arx_1210.3948.pdf/.txt/_raw.txt`（C18 新來源全文）、`baldwin_BP*.html`／`baldwinU_*.html`（C16／C17 十頁原始 HTML）、
  `nasm_pama.pdf/.txt`（B14）、`tub_anechoic.pdf/.txt`（B15 負面）、`mamou.pdf/.txt`（負面）、
  `trevisan2017.pdf`／`ege_these.pdf`／`jasa144_1347.pdf`／`poma_roginska.pdf`（**四個都是反機器人／403 的 HTML 檔，保留為未取得的證據**）、
  `r4_dump_modes.json`（引擎重跑）、`verify/`（v100 重新渲染 + manifest，SHA256 比對用）
- `B7_PHASE0_DATA.prev_round4.md`——第四輪動筆前的完整備份

**本輪的 `pytest` 現況（README §3 硬性檢查，誠實記錄）**

本卡只新增/改寫 `docs/B7_PHASE0_DATA.zh-TW.md` 一個檔，未碰 `src/` `tools/` `tests/`。
收工前仍照規約跑了 `python -m pytest tests -q`，結果：

```
1 failed, 236 passed, 1 skipped in 55.51s
FAILED tests/test_schema_contract_sync.py::MutationMatrixTests::test_mutations_agree_with_cli
```

**這條紅燈不屬於本卡**：`tests/test_schema_contract_sync.py` 是 untracked 新檔（建立時間 2026-09-08 01:19），
與 `src/score/ScoreParser.h` 的 unstaged 改動同屬 **E8 卡（score 合法性三份契約同步）** 的施工中狀態；
失敗訊息也全是 schema ↔ CLI `--validate` 的一致性斷言。本卡不碰、不修、不繞過，僅記錄現況。
（另注意：README §3 寫的基線是「213 collected」，本輪 collected 已達 238——差額來自其他 lane 新增的測試。）

**2026-09-08 第三輪的重跑（現況已變好，誠實更新）**：收工前再跑一次 `python -m pytest tests -q`，
結果 **`249 passed, 1 skipped in 63.25s`——全綠**。
上兩輪記錄的那條紅燈（`tests/test_schema_contract_sync.py::MutationMatrixTests::test_mutations_agree_with_cli`）
**本輪已不再失敗**；那是 E8 卡（score 合法性三份契約同步）在本卡之外的 lane 收尾的結果，
**不是本卡做的任何事**。本卡仍未碰 `src/`、`tools/`、`tests/` 任何檔案。

**2026-09-07 複核修正回合的重跑**：收工前再跑一次 `python -m pytest tests -q`，
結果 `1 failed, 245 passed, 1 skipped in 66.12s`，**失敗的仍是同一條**
（`tests/test_schema_contract_sync.py::MutationMatrixTests::test_mutations_agree_with_cli`，
訊息為 `phrases.0.start/end/breath_after_ms [minimum]` 的 schema ↔ CLI 不一致）。
collected 由 238 增為 247，同樣來自其他 lane。`git status` 確認本回合只新增
`docs/B7_PHASE0_DATA.zh-TW.md`（untracked），`src/` `tools/` `tests/` 皆非本卡所改。

---

**未使用本 repo 自身文件當外部證據**（研究卡鐵律第 5 條）。
`docs/COMMERCIAL_PM_PUBLIC_DATA.zh-TW.md`、`docs/RADIATION_POWER_SOURCES.md`、`docs/workcards/B7.md`
只用於界定「這輪要查什麼」與交叉對照（表 A 的 A5 已明確標註排除，不計入 `sources_count`）。
§3.4 引用 `src/` 與 `tools/` 的程式碼，屬於「引擎/repo 現況」而非外部證據。

---

## 複核修正記錄（2026-09-07）

本節逐條列出引用複核員提出的五條 findings，以及本輪的實際處置。
**原則：來源真的找不到就改成「未取得原文」或刪掉該主張，不補新的假來源。**

### 1【blocker】C9 把 arXiv:1210.5688 誤述為「全文無面積數值」，C7 據此宣告 `S = M/(ρh)` 路線走不通

**複核員的證據成立，本輪親自複驗確認。**
把本卡上一輪自己下載的 `output/wf0907/R4/arx_1210.5688.pdf` 攤平後檢索，原文明白寫著：

> “we refined the model by considering now the structure as an isotropic rectangular plate,
> of constant thickness, of dimensions Lx = 1.39 m, Ly = 0.91 m and total mass M = 9 kg”

`1.39 × 0.91 = 1.2649 m²`，正是 C1 那塊 Atlas 直立琴音板；`M = 9 kg` 就是 C7 說「檢索不到」的量。

**怎麼改**：

- **C9 列整列重寫**：從「負面結果」改為**正面結果**，列出 `Lx/Ly/M` 與原文引述，
  並註明溯源等級改為「原文全文（正面結果）」。上一版引用的那句
  “depends neither on the excitation point nor on the surface” 本身沒引錯，
  但它講的是「高頻漸近導納與面積無關」，**不能推論成「文中查無面積」**——這一點在新增的
  §2.3「C7／C9 更正說明」裡明寫為誤讀。
- **C7 列重寫**：保留「1212.2323／1305.3057／1212.3068 三篇確實沒有 `M`」這個字面成立的負面結果
  （本輪重新 grep 複驗），但刪掉「四篇皆無、路線確認走不通」的結論，改指向 C9。
- **新增 §2.3「C7／C9 更正說明」**：說明 `S = M/(ρh)` 路線的**正確**結論是
  「不是查不到 `M`，而是用生雲杉密度反推會高估 2.22 倍」——
  `9/(400×0.008) = 2.812 m²` vs 真值 `1.2649 m²`，因為該 `M` 是抹平後等效均向板（含肋條與琴橋）的質量，
  隱含等效密度 889 kg/m³。算式與原文引述存 `output/wf0907/R4/fixround/arx1210_mass_area.txt`。
- **§4.1 表 C 判定列、§5 兩列、附錄第 12/14 條**同步更新。
- **平台琴 `S` 查無** 這個總結論**不變**（C9 找到的是直立琴），但直立琴的 1.2649 m²
  在**兩篇論文裡都印得出來**——這是本次更正的正面收穫，已寫進 §2.3 結論。
  （**2026-09-08 第五輪更正措辭**：原本這裡寫「兩篇獨立出處」，措辭過強——
  兩篇是同一研究群量同一台 Atlas 直立琴，只能算「同一筆數字印得一致」。）
- **§5 給規劃者的建議也一併改寫**：原本要規劃者去 `RADIATION_POWER_SOURCES.md` §5
  加註「路線不通」，改成加註「`M` 找得到，但要用等效面密度，不能用生木密度；且平台琴仍無 `M`」。
- **這次更正還撿到一個真正有用的數**：`M/S = 7.115 kg/m²` 是本輪唯一有出處的**實測音板面密度**，
  而 `RADIATION_POWER_SOURCES.md` §3 現在用的是裸雲杉假設值 `3.6 kg/m²`——**兩者差近一倍**。
  已加進 §2.3 更正說明第 4 點與 §5 缺口表。

### 2【major】把自選的 velocity 下限 0.02 當成「引擎的動態範圍」

**複核員的重跑數字本輪完全重現。** 本輪另外補量 0.01／0.05／0.20／0.60 四點
（`output/wf0907/R4/fixround/velocity_floor_sensitivity.txt`）：

| 選的下限 | 到 1.00 的差 |
|---|---|
| 0.01 | 67.39 dB |
| 0.02 | 60.08 dB |
| 0.05 | 51.88 dB |
| 0.10 | 38.00 dB |

`src/score/ScoreParser.h:313` 的合法範圍是 `0.0–1.0`，**引擎沒有 0.02 這個地板**。

**怎麼改**：

- **§3.2 新增整段警語**（標題就寫「這個數字不是引擎的性質，是下限選在哪裡的產物」），
  附上上表與 `ScoreParser.h:313` 的原始碼片段；力度掃描表補上四個新量測點。
- 原本那句「**C4 全域動態範圍 = 60.08 dB**」刪除，改寫成「在固定下限 0.02 時（純為跨音高可比，
  不代表引擎有此邊界）三個音的差是 49.52／60.08／49.78 dB」。
- **§4.2 選項 1 的「為什麼可行」整句改寫**：刪掉「文獻 60.4 dB vs 引擎 60.1 dB」這個理由
  （已標明為撤回），可行理由改成「velocity→槌速這一段終於有出處」。
  代價從三條擴為四條，第 2 條專講「動態範圍隨下限而變，GATE 必須先訂死下限並說明理由」。
- 順帶記錄了一個新事實：峰值對 velocity **不是線性的**（加倍 = +10.7 ~ +13.9 dB，非 +6.02 dB），
  已列入 §3.2 表格，並在 §3.4 說明它與 GATE 所用量測（基頻帶 RMS）不是同一個量。

### 3【major】沒提 repo 內已存在、且正在被機器驗證的 velocity 律

**複核員指出的三處程式碼本輪全部親自核對成立**：
`src/score/ScoreParser.h:295–308`（“This is not just a design intent -- it is machine-verified”）、
`tools/physics_verify.py:1134–1136、1213`（`VELOCITY_LO/HI`、`VELOCITY_LAW_DB = 6.020599913279624`）、
`ROADMAP_PHYSICS.md:173`（1d 已登記為已判定 GATE）。

本輪**另外實際重跑了這條 GATE**（唯讀，piano／MIDI 60，
`python tools/physics_verify.py --full --skip-amps --engines piano --notes 60`，
輸出存 `output/wf0907/R4/fixround/physics_verify_1d_piano.txt`），得到一個複核員未提及、
但對判斷很重要的細節：**piano 目前不是被「+6.02 dB 固定律」判的**——
2026-08-27 的 B4 裁決（`reports/decision_packets/B4_f3_velocity_ruling.md`）
把 Felt／`tau_c(v)` 路徑切出來改判「render 對得上 model 自己的預測」，
GATE 輸出原文：“the fixed-tau_c 6.0206 dB law is not asserted here”。

**怎麼改**：

- **§3.4 標題改為「三條路徑不一致，而且已經有一條機器驗證中的力度律」**，
  score/CLI 那一列從「**無定義**——就是一個 0–1 的數」改為「與 MIDI 沒有換算定義，
  但不是隨便一個數，同檔 `:295–308` 已為它登記了一條力度律」。
- **§3.4 新增整段**，含 GATE 實跑輸出，並明說結論：採用 A12 的指數律會同時改掉 render 與 model，
  1d 必須重新推導與重跑，且會改變既有 score 的渲染輸出＝**README Rule 10 情境**。
- **§4.2 選項 1 新增第 4 條代價**（就是這件事），**§4.3 落地形態第 4 點**由「三路徑不一致」
  擴為 (a) 三路徑 + (b) Rule 10 衝突。
- **§4.1 表格 A 那列的判定**由「齊（可開工）」改為「資料齊；但『可開工』要打折」，並列出兩個前置。
- 附帶發現：`ScoreParser.h:295–308` 那句「piano 也被判 +6.0 ± 1.0 dB」**對 piano 已過時**
  （被 B4 裁決取代）。本卡不碰 `src/`，已列入 §5 與 `open_items` 交規劃者。

### 4【minor】B1 條件欄的「1 kHz、94 dB」不在論文裡

**複驗成立**：`output/wf0907/R4/goebl_2005_flat.txt` 全文檢索 `94 dB` **零命中**，
`1 kHz` 也零命中；論文只有註 8 的 “Brüel & Kjær sound level calibrator type 4230.”。

**怎麼改**：**直接刪除「1 kHz、94 dB」六個字**（依鐵律第 1 條，沒有出處就不寫），
條件欄改為「以 B&K 4230 聲級校準器校準（型號取自原文註 8；上一版另寫的『1 kHz／94 dB』
不在論文裡，那是該型號的廠商規格，2026-09-07 複核已刪除）」。**未補任何替代來源。**

### 5【minor】(a) 指數應為 1.91 不是 1.92；(b) §4.3 對零程式背景讀者不可讀

(a) 重算：`20*log10(6.8/0.18) = 31.544728152058603`，`60.4 / 31.5447 = 1.9147` → **1.91**。
**怎麼改**：§2.2 B9 附帶推論的算式行改為印出 31.5447 與 1.9147 的完整中間值，結論改為 `p ∝ v^1.91`。

(b) **怎麼改**：在 **§0 新增一段標題為「但是：查到公式 ≠ 明天就能動工」的白話警語**，
用完全不含術語的說法講兩個攔路石（「程式裡『力度』有三種算法」「程式裡已經有一條通過驗收的力度→音量規矩，
改了會讓所有做好的曲子聲音都變」），並指到 §3.4 與 §4.2 第 4 點。
§4.3 原文保留（那是給工兵看的技術細節），但第 4 點已補齊 (b) 這一項。

---

### 附帶：表 C 其餘負面結果的重新複驗（因為 C9 出錯，其餘不能只靠上一版的說法）

既然 C9 被抓到誤述，本輪把表 C 其餘四筆負面結果**全部重新 grep 一遍**
（模式：`total mass`／`mass M`／`M = <數字>`／`Lx`／`Ly`／`area of the`／`m2`）：

| 列 | 論文 | 重驗結果 |
|---|---|---|
| C10 | arXiv:1011.5372 | 七個模式**全部零命中** → 負面結果成立 |
| C8 | arXiv:1305.3057 | 只出現符號定義「`where M is the total mass of the structure`」，**無數值**；`Lx/Ly` 命中皆為波導推導的符號 → 負面結果成立 |
| C7 一部分 | arXiv:1212.3068 | 質量模式零命中 → 負面結果成立 |
| C6 | ISMA 2010 | 七個模式全部零命中 → 負面結果成立 |
| C3 | Chabassier 2013 | 唯一的 `m2` 命中是**琴弦截面積**的表頭（`A (m2)`），不是音板 → 負面結果成立 |

**→ 表 C 只有 C9 一列是錯的，其餘四筆負面結果經重驗後維持。**

### 本修正回合新增的證據檔（`output/wf0907/R4/fixround/`，已 gitignore）

- `velocity_floor_sensitivity.txt`——finding 2：velocity 0.01–1.00 十點的 `pre_normalize_peak`、
  不同下限對應的「動態範圍」、以及真正加倍時的 dB 變化
- `physics_verify_1d_piano.txt`——finding 3：`physics_verify.py --full --skip-amps --engines piano --notes 60` 全文輸出
- `arx1210_mass_area.txt`——finding 1：arXiv:1210.5688 的原文引述段落與本文件的反推算術

上一版全文備份在 `output/wf0907/R4/B7_PHASE0_DATA.prev_round2.md`（覆寫前先備份，未遺失）。

**本修正回合仍未碰 `src/`、`tools/`、`tests/` 任何檔案**；
`physics_verify.py` 與 CLI 皆為唯讀執行，未加 `--keep`，未寫入 repo 版控路徑。

---

## 第三輪獨立複驗記錄（2026-09-08）

本輪沒有收到新的 findings 清單，任務是**以「不採信上一版自報」的態度重跑一遍研究卡**。
逐項記錄做了什麼、結果如何。

### 1. 複驗三條吃重的引述 → **全部通過**

A12（公式）、B9（同一顆音的槌速＋絕對 dB）、C9（音板尺寸＋質量）——
本輪從本地 PDF 文字層用程式定位、輸出前後 300 字上下文、逐字比對，**三條一字不差**（§3.7 表）。
另補驗 B11 的 1.5 m 麥克風位置，也成立，且補到「置於掀起的琴蓋旁」這個上一版沒寫的位置細節。

**這件事的意義**：本文件的三個核心主張，現在是**兩輪、由不同回合各自打開原文核對過**的。
（過去這個 repo 的研究文件被稽核抓到過「引用不實」——本輪的做法就是為了讓這件事不會再發生在這張卡上。）

### 2. 複驗全部算術 → **全部通過**

不看上一版答案，把 A12 正反解、B9 指數、A3 指數、C9 面積／反推倍率／面密度**全部重算**，
結果與上一版一致到列出的位數（§3.7 表；輸出 `output/wf0907/R4/round3/arithmetic_recheck.txt`）。

### 3. 重跑引擎 → **一致**

`--dump-modes` 重跑，`pressure_per_force_real_pa_n = 0.3065508` @ `radius_m = 1.05` 與 §3.1 相同，
`absolute_spl` 仍在 `unsupported_observables`。

### 4. 新增四個外部來源（都逐字核對過）

| 新來源 | 補到哪一格 | 為什麼有價值 |
|---|---|---|
| KTH Askenfelt & Jansson 講義（**本輪直接 fetch**） | A5 | A12 的「MIDI 110 → 4.99 m/s ↔ forte 約 5 m/s」這個交叉檢查，**過去靠的是 repo 內部記錄**（依鐵律第 5 條不能當外部證據），現在靠的是本輪親自打開的外部頁面。**這是把一個交叉檢查點從『不合格證據』升級成『合格證據』** |
| Goebl 論文中該式的**第 3、第 4 次出現** | A13 | 四處寫法一致 → 排除「單一處印刷錯誤」；且註 14 顯示整個知覺實驗系列都用同一張 map |
| arXiv:1210.5109（Forum Acusticum 2011） | C12 | 上一輪是**推論**「`M = 9 kg` 含肋條與琴橋，所以不能用生木密度反推」；本輪拿到**作者自己寫的定義句**（“including ribs, bridges and the two fir bars”）。**推論變成引述** |
| KTH Conklin 講義 soundboards 分頁 | C13 | 音板厚度的第三個獨立來源（6.5–9.5 mm），與 C2、C3 相容 |

另加兩筆**負面結果**（C14 Wogram 全章無面積、C15 soton postprint 被反機器人擋住）與
一筆**業界佐證**（B13 Sound On Sound，佐證「權威數字全在近場、外推只是理論」）。

### 5. 撤下兩筆搜尋摘要遞來的假／未核對數字

X1（「平台琴音板 over 20 square feet」——**該句不在被指涉的網頁裡**）、
X2（Steinway 音板厚度——**廠商頁 TLS 憑證錯誤，未取得原文**）。詳見 §2.5。

### 6. 兩個仍缺的格子：**這輪還是沒補起來**

- **平台琴音板面積 `S`**：本輪多翻了 KTH 兩章講義、arXiv:1210.5109、Fazioli 平台琴論文重掃、
  廠商規格頁、soton postprint，**全部沒有**。三輪累計 10 個來源，平台琴這一格從頭到尾是空的。
  **最可能有答案的一篇（C15）本輪被反機器人擋住——這是唯一一條「換一雙手就能拿到」的路**。
- **1 m 處 SPL**：本輪多找了業界技術媒體與職業噪音暴露方向，**依然只有近場數字**。
  B13 的存在反而強化了原結論：連業界作者自己都把倍距外推寫成 “in theory”。

### 7. 本輪的判定沒有改變

§4.1 三格的判定（A 齊但要打折、B 缺、C 缺）**與上一輪相同**；
§4.2 的三個選項與建議（選項 1）**未改動**。
本輪的貢獻是**讓這些判定背後的證據更硬**，不是改變判定。

**本輪同樣未碰 `src/`、`tools/`、`tests/` 任何檔案**；CLI 為唯讀執行；
`python -m pytest tests -q` 全綠（249 passed, 1 skipped）。

---

## 第四輪獨立複驗與補搜記錄（2026-09-08）

本輪同樣沒有收到 findings 清單，任務一樣是「不採信前一版的自報，再跑一遍」，
但把重心放在**第三塊資料（平台琴音板面積）**——那是連續三輪都空著的格子。

### 1. 補搜結果：**第三塊資料第一次有了數字，但等級是「廠商規格」不是「論文」**

| 新來源 | 補到哪一格 | 為什麼有價值 |
|---|---|---|
| Baldwin 官方六台平台琴規格頁 | **C16** | **第一次拿到「平台琴音板面積」的實際數字**：0.8697／1.0452／1.2258／1.2826／1.4252／1.6800 m²（4'10"–6'11"） |
| Baldwin 官方四台直立琴規格頁 | **C17** | **給 C16 做可信度檢查**：47 吋直立琴 1.2774 m² vs Ege 論文實測 120 cm 直立琴 1.2649 m²，**差 0.99%** |
| arXiv:1210.3948（Boutillon/Ege/Paulello） | **C18** | (a) 補回上一輪被丟掉的 X2（Steinway B/D 厚度 9 mm 中央→6 mm 邊緣，**這次有原文**）；(b) **解釋了為什麼論文層級一直查不到面積**——致謝欄寫明作者有平台琴的尺寸圖，但論文沒印出 `A` 的數值 |
| NASM–PAMA 學生宣導單 | **B14** | 反面教材：業界的「鋼琴 60–70 dB」是這樣流傳的——**沒有距離、沒有校準、沒有力度**。明確不得當 GATE |
| TU Berlin 無響室資料庫論文 | **B15** | 負面結果，且是 B5 的**獨立再確認**（同一組資料的另一篇論文同樣不含鋼琴） |

**丟掉一筆**：X3「平台琴音板 2–4 m²」——只出現在搜尋摘要，本輪打開該批結果中可取得的全文皆無此句，
且與本輪唯一有數字的來源（0.87–1.68 m²）不同量級 → 不採用（§2.5）。

### 2. 四條「這輪打不開」的管道（誠實記錄，未嘗試繞過）

HAL（Trévisan 2017 全文、Ege 2009 博士論文舊版直連）兩次都是 Anubis 反機器人頁；
AIP 兩條直連 PDF（JASA 144:1347、POMA 19:035006）都回 403；
Roginska 那篇連作者 NYU 個人出版頁都沒有掛 PDF——**四條管道全部失敗，數字一個都不採用**。

### 3. 複驗：**引擎輸出這次比對到位元**

前三輪只比對數值；本輪多做一步：重新渲染 v100 後比對 **WAV 的 SHA256**，
結果與上一輪的 manifest **完全相同**（`ac573b65…6ce5f4`），`--dump-modes` 的 `0.3065508 Pa/N @ 1.05 m` 也一致。
A12、C9 兩條吃重引述再從本地 PDF 撈一次，**一字不差**（§3.8）。

### 4. 判定的變化

- **A（velocity→槌速）**：不變（齊，但要打折——三種力度定義未裁決 + Rule 10 衝突）。
- **B（1 m SPL）**：不變（缺）。**但本輪把「還能去哪查」收斂成三條需要月月出手的管道**，
  並判斷**免費管道已經查完**。
- **C（音板面積）**：**這一格改判**——論文層級仍缺，但**廠商規格層級已可用**，
  且有一個 1% 的交叉檢查撐著。B7 §4.5 現在有三個選項而不是兩個（見 §2.3 結論）。

### 5. 本輪的收工檢查

- 只寫 `docs/B7_PHASE0_DATA.zh-TW.md` 一個檔（動筆前已備份為
  `output/wf0907/R4/B7_PHASE0_DATA.prev_round4.md`）；未碰 `src/`、`tools/`、`tests/`。
- CLI 為唯讀執行，輸出全在 `output/wf0907/R4/round4/`（已 gitignore）。
- `python -m pytest tests -q` 結果：**`1 failed, 248 passed, 1 skipped in 62.90s`**，
  失敗的是 `tests/test_dump_modes_layered.py::DumpModesLayeredTests::test_all_corpus_files_flatten_and_place_events_correctly`
  （斷言 `layer offset_s` 3.4938 ≠ 3.5438）。**這條紅燈不屬於本卡**：該檔為 untracked 新檔，
  與 `src/score/ScoreRenderer.h` 的 unstaged 改動同屬 **E9 卡（`--dump-modes` 支援 layered score）**
  的施工中狀態。本卡不碰、不修、不繞過，僅記錄現況（上一輪同一位置紅的是 E8 的檔，後來由 E8 lane 自行收掉）。

---

## 複核修正記錄（2026-09-07）

> 第四輪交出後由另一位 Opus 做**引用複核**（親自打開每個來源、逐字比對）。以下五條 findings
> 我**逐條親自重驗過來源**（不採信複核員自報，也不採信本文件上一版自報），確認全部成立，並照下表修正。
> 本輪**沒有新增任何來源、沒有新增任何數字**——五條全是「把講過頭的話收回來」或「把假引文換成真引文」。

### 重驗方式（每條都做了）

| 來源 | 本輪重取方式 | 結果 |
|---|---|---|
| Modartt 論壇 id=6943 | `curl -L` 取回 **HTTP 200 / 39,451 bytes**，剝標籤後存 `output/wf0907/R4/fix5/modartt6943.txt`，用字串精確比對 | 見第 1 條 |
| KTH Askenfelt 講義 `motions.html` | `curl -L` 取回 **HTTP 200 / 7,233 bytes**，存 `output/wf0907/R4/fix5/kth_motions.txt` | 見第 2 條 |
| ege2013（arXiv:1212.2323）／arXiv:1210.5688 | 本地 `.txt` 文字層 `grep` | 見第 3 條 |
| `output/wf0907/R4/3504_1_online.pdf`、`round4/poma_roginska.pdf` | `head -c` 讀檔頭 | 兩者都是 Cloudflare 的 `<!DOCTYPE html>…Just a moment...` 攔截頁，**不是 PDF** |

### 五條 findings 的處理

| # | 複核員的指控 | 我重驗的結果 | 怎麼改 |
|---|---|---|---|
| **1（blocker）** | §2.4 表 S2 的 lo134「原話」是把同一主樓兩個不同句子拼起來的，全頁 0 命中 | **成立。** 全頁只有兩處 `SPL`，原文分別是 (a) `“…I need the maximum sound level (SPL level) and dynamic range of the reference pianos.”` 與 (b) `“Is the information about the maximum sound level and dynamic range of each of the reference pianos … available?”`。文件印的字串把 (a) 的 `(SPL level)` 塞進 (b) 的句型，**字串比對 `False`**（(a)、(b) 各自比對為 `True`） | **改用 (b) 的完整原句**（含 `(or one set of number in general…) available?` 的後半），並**另列 (a) 的完整句**說明他要這個數字的用途。同時補上主題標題、主樓時間 `11-11-2019 20:22`、以及 9 則回覆的編號（2–10）與回覆者（Amen Ptah Ra／peterws／Qexl ×4／bm／lo134 ×2）——這些我用 regex 逐則掃出來核對過。**實質主張（使用者向商業廠商索取絕對 SPL、無官方數字）不變**，故 §4 的判斷與 §8 驗收基準的結論不受影響 |
| **2（minor）** | §2.1 表 A5 第一句引文把原文逗號改成句號，變成句中截斷卻沒標省略 | **成立。** 原文為 `“…about 5 m/s (18 km/h), not very far from the highest velocity observed during the experiments.”` | **補回被截掉的後半句**，改成完整句引用。同列另三句（`five times higher`／`0.3 - 0.5 m/s`／`1 m/s (about 4 km/h)`）我本輪也重新逐字比對，**全部成立、原樣保留**；`0.3–0.5 m/s` 標為「鍵速」也正確 |
| **3（minor）** | §0 說直立琴面積「拿到了第二篇獨立出處…兩篇論文對得起來」，實際上兩篇是同一研究群、同一台琴 | **成立。** `ege2013.txt` 第 317 行 `“An upright piano (Atlas brand) with a rectangular soundboard (dimensions: 0.91 m × 1.39 m × 8 mm)”`；`arx_1210.5688.txt` `“of dimensions Lx = 1.39 m, Ly = 0.91 m and total mass M = 9 kg”`——**同一組尺寸** | **§0 加上限定句**（明說是同一研究群量同一台 Atlas 直立琴、不是兩組獨立量測），並把同樣講過頭的三處一起改：**§2.3 選項 (i)**、**§4.1 表 C 判定列**、**§2.3 更正說明結尾**。另把 §2.2 表 **C12** 的「第三篇獨立出處」改為「同一數字的第三篇出處（同研究群、同一台琴，非獨立量測）」——複核員沒點名這一處，但它是同一類措辭，一併收乾淨 |
| **4（minor）** | 回報的 `sources_count = 43` 是附錄列數，含重複與非證據列 | **成立。** 第 20 條與第 43 條同為 Roginska et al. 2013 POMA；`round4/poma_roginska.pdf` 實為 **5,883 bytes 的 Cloudflare HTML**，兩條都沒取得任何內容 | **附錄開頭新增「`sources_count` 的算法」小表**，把 43 列拆成：相異作品 **42**、其中取得原文並逐字核對 **31**、僅摘要 **2**、未取得原文 **9**。**本輪回報改用 31**（取得原文並逐字核對的相異來源數）。第 43 條加註「＝第 20 條同一篇，不另計」，第 20 條的取得方式改為「四條管道全失敗」。並在小表下方註明第 32、38 條雖計入「已取得」但角色是**反面證據** |
| **5（minor）** | §3.6 註 2 保留了一個只在搜尋摘要層級看到的數字（JASA 140:3504 的「f–ff 約 32 N」），與本文件自己對 X1／X3 的標準不一致 | **成立。** `3504_1_online.pdf` 是 **5,619 bytes 的 Cloudflare 攔截頁**，四輪都沒取得原文 | **把該數字整條刪除**。§3.6 註 2 改寫為「本試算算出 457 N，**目前沒有任何實測值可以對照**；在拿到原文之前不主張它是高估還是合理」。同時在 **§2.5 丟棄表新增 X4** 記錄這次丟棄的理由（讓下一位研究員不必再走一次），並把 §2.5 的「兩筆／三筆」計數改為「四筆」。附錄第 22 條的「用在哪」改為「§5 待查表，不提供任何數字」 |

### 本輪沒有做的事（明確聲明）

- **沒有新增任何來源**，`sources_count` 從 43 降到 31 是**算法更正**，不是新增或刪除來源；43 列一列都沒刪。
- **沒有改任何物理數字**：A12 的映射式、C16 的六筆廠商面積、C17 的 1% 交叉檢查、§3 的引擎量測值全部原封不動。
  唯一被刪掉的數字是 X4 那個從頭到尾就沒有原文支撐的「32 N」。
- **§4 的建議不變**、**§8 驗收基準 (a) 仍不得成立**（1 m 絕對 SPL 第五輪仍然沒有）。
- 只寫 `docs/B7_PHASE0_DATA.zh-TW.md` 一個檔（動筆前備份為 `output/wf0907/R4/B7_PHASE0_DATA.prev_round5.md`）；
  未碰 `src/`、`tools/`、`tests/`、`B7.md`；未 `git commit` / `git add`。

---

## 複核修正記錄（2026-09-09，WF0908-P5）

> 卡：`docs/workcards/WF0908_P5_research_cleanup.md` §1 的 R4 那一列。
> **只改措辭與加註，物理數字、來源清單、`sources_count`、§3 的引擎量測值一個字都沒動。**

| # | finding | 處理 | 改到哪 |
|---|---|---|---|
| 1 | §4.3（連同 §2.1、§4.1）的三個錨點來自**兩篇有 14% 槌速校正差**的來源，文件未標示；由此得出的「殘差 ≤0.5%、交叉驗證全中」敘述**誤導** | **已改**。三處同步：(a) §2.1 交叉檢查表下新增「⚠️ 上表那排「✅」被兩件事削弱」一節，附 Goebl et al. (2005) 註 9 的 ≤15 字原文引述、核對方式與存取日，並列出四個錨點分別落在「有校正／沒校正」哪一邊；(b) §4.1 表 A 格的「經三個獨立量測點交叉驗證全中」改為「相符到印刷精度」＋更正註；(c) §4.3 第 1 點改寫成「系統性偏差 ≥ 殘差」的誠實版，並明寫落地註解**不得**寫「殘差 0.5%」 | §2.1、§4.1、§4.3 |

### 本輪自己做的查證（不是沿用上一版）

| 查什麼 | 怎麼查 | 結果 |
|---|---|---|
| 「+14%」這句到底在不在原文 | 本機全文抽取檔 `output/wf0907/R4/goebl_2005_flat.txt` 逐字 `find('14%')`，把前後 1600 字元整段印出來讀 | **在**。位於註 9，前後文完整：校正理由（accelerometer 裝在槌桿 vs 打擊點在槌冠，半徑不同）＋「This correction was not applied in Goebl and Bresin 2003.」 |
| A1 的 0.7–1.25 m/s 出自哪一篇 | 在 `goebl_2005_flat.txt` 搜 `40 and 60 MIDI` | **Goebl et al. (2005)**（General Discussion）。原文同時寫 “as measured in Goebl, 2001”——**MIDI 值來自 Goebl 2001，m/s 怎麼換算的原文沒寫**，這正是 §2.1 (2) 的依據 |
| A2 的 2 m/s / MIDI 77 出自哪一篇 | 在 `goebl_bresin_2003_flat.txt` 搜 `77 MIDI` | **Goebl & Bresin (2003)** §II.C，原文 “hammer velocity over 2 m/s or 77 MIDI velocity units” |
| A3 的 0.18 / 6.8 m/s 出自哪一篇 | 在 `goebl_2005_flat.txt` 搜 `0.18 m`，再用頁尾註腳字串定位頁碼 | **Goebl et al. (2005)** **p.1163**（命中位置在頁尾 `1162 J. Acoust…` 之後、頁尾 `…1163` 之前；**2026-09-09 更正**，上一版寫 p.1162） |
| 博士論文有沒有套這個校正 | 在 `goebl_diss2.txt` 搜 `14%`／`crown`／`increased by`／`radius`／`shank and strik` | **沒有**（2026-09-09 逐字重跑）：`increased by`／`radius`／`shank and strik` **零命中**；`14%` 命中 2 處，都是 `0.0053% or 0.014%` 時間漂移；**`crown` 命中 1 處但與校正無關**（“the hammer crown just starts to contact the strings”，光閘量測說明）。**屬「檢索不到」的推論** |
| 殘差與刻度差的量級關係 | `2^((40-52)/25)=0.7168`、`2^((60-52)/25)=1.2483`、`2^((77-52)/25)=2.0000`；`20·log10(1.14)=1.138` | 殘差 ≤0.5%、刻度差 14%（≈1.14 dB）——**系統性偏差比殘差大一個量級** |

### 本輪沒有做的事（明確聲明）

- **沒有新增也沒有刪除任何外部來源**，`sources_count` 不變（上一輪記錄的 31）。
- **沒有改任何數字**：A12 的式子、交叉檢查表的六列算值、表 B／表 C 全部、§3 的引擎量測值原封不動。
- **沒有提出任何容差或門檻**（Rule 2）；「±14%／±1.14 dB」是量級說明，明文標為非容差。
- **§4 的三個選項與建議不變**；**§8 驗收基準 (a) 仍不成立**（1 m 絕對 SPL 仍然沒有出處）。
- 只寫本 `.md` 一個檔（動筆前備份在 `output/wf0908/P5/B7_PHASE0_DATA.zh-TW.md`）；
  未碰 `src/`、`tools/`、`tests/`；未跑 cmake、未渲染音訊、未 `git add`／`commit`／`push`。

---

## 複核修正記錄（2026-09-09 第二次，WF0908-P5 修正回合）

> 只改**頁碼標註**與 **A12 校正檢索那一格的措辭**；**沒有任何數值改變**，來源數不變。

| # | 嚴重度 | finding | 處理 |
|---|---|---|---|
| 1 | minor | §2.1 的 A1／A3（以及 §2.3 的 B1、附錄自查表）把 Goebl et al. (2005) 的三錨點與兩極值標成 **p.1162**，但那段文字（General Discussion 開頭）實際落在 **p.1163**。引述文字與數值本身都真實，只是頁碼差一頁 | **已改**為 **p.1163**，四處同步（§2.1 A1、§2.1 A3、§2.3 B1、附錄自查表 A3 那一列），每處都留下「上一版寫 p.1162」的更正說明 |
| 2 | 連帶 | §2.3 的 B1 用一個 `p.1162 ＋ §II.B` 概括三句話，但三句其實分屬三頁 | **已改**為逐句標頁：**50.0／110.4 dB-pSPL 在 p.1163**（與 A3 同一句）、**“placed about 10 cm above the strings” 在 §II.B（p.1157）**、**註 8 的 “Brüel & Kjær sound level calibrator type 4230” 在 p.1164** |
| 3 | 連帶 | §2.1 (1) 引用 +14% 校正的註 9 時沒標頁碼 | **已補** **p.1164** |
| 4 | minor | §2.1 錨點表最後一列（「A12 那條式子本身」）寫「本輪在該論文全文檢索 `14%`／`crown`／`increased by`／`radius`：…其餘三個字串在校正意義下**零命中**」——但 **`crown` 在博士論文中確有一處字面命中**（與 +14% 校正無關），這個措辭容易被讀成「字面零命中」 | **已改**。該格與附錄自查表的同一列都改寫成逐字串分開講：`increased by`／`radius`／`shank and strik` **字面零命中**；`14%` 命中 2 處，都是 `0.0053% or 0.014%` 時間漂移；**`crown` 字面命中 1 處但與校正無關**（“the second time when the hammer crown just starts to contact the strings”，Bösendorfer 光閘量測說明）。並明寫**結論屬「檢索不到」的推論，不是原文明寫「未套用」**（原文明寫未套用的是 Goebl et al. 2005 註 9 那一句）。**結論本身不變：該博士論文未套 +14% 校正** |

**本輪自己重跑的驗證（核對日 2026-09-09）**：
- 頁碼定位法：在 `output/wf0907/R4/goebl_2005_flat.txt` 逐一找頁尾字串，得
  `…1161`＠40988、`1162 J. Acoust…`＠44874、`…1163`＠51899、`1164 J. Acoust…`＠58944、`…1165`＠67376。
  「between 40 and 60 MIDI velocity units 0.7–1.25 m / s」＠45645、「minimum 0.18 m / s or 50.0」＠46590、
  「maximum 6.8 m / s or 110.4 dB-pSPL」＠46732 —— 三者都在 44874 與 51899 之間，**故為 p.1163**。
  「placed about 10 cm above the strings」＠21045，在 `…1156`＠18319 與 `…1157`＠24631 之間，**故為 p.1157**。
  註 8「Brüel & Kjær sound level calibrator type 4230」＠57945、註 9「resulting in values in-」＠58325，
  都在 51899 與 58944 之間，**故為 p.1164**。
- `goebl_diss2.txt` 逐字重跑：`crown` → 1 命中（＠118486）、`14%` → 2 命中（＠128083、＠142866）、
  `increased by`／`radius`／`shank and strik` → 各 0 命中。

**本輪的邊界**：只改本 `.md`；**沒有新增或刪除來源**、**沒有改任何數值**、**沒有提出任何容差**；
未碰 `src/`、`tools/`、`tests/`；未跑 cmake、未渲染音訊、未 `git add`／`commit`／`push`。
動筆前備份在 `output/wf0908/P5_fix/B7_PHASE0_DATA.zh-TW.md`。
