# A14 裁決包：高音弱基頻是物理正確還是引擎缺陷

> 工作卡：`docs/workcards/WF0907_R2_A14_weak_fundamental.md`（研究 lane，執行 Opus）
> 日期：2026-09-07；**2026-09-08 獨立複核 + 新增 L1 來源後修訂**
> 外部來源存取日期：初版一律 2026-09-07；本次修訂新增／複驗的來源一律 **2026-09-08**
> 引擎數字取自 `build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe`（唯讀使用，未重建）
> 工作樹 branch `fix/deep-physics-audit-20260716`，HEAD `98f346f`
> 本卡未改任何 `src/` `tools/` 檔案；暫存輸出在 `output\wf0907\R2\`（已 gitignore）
>
> **2026-09-08 修訂摘要**（複核紀錄見附錄 C）：
> 1. §3 全部引擎數字重跑，**逐格重現**（§3.1 五音 FFT、§3.5 三組掃描斜率、§3.3 τc 與 x 值）。
> 2. §2 每一條 L1/L2/L3 引述重新開原文核對，**全部命中、無不實引用**。
> 3. **新增 L1-16～L1-22：Russell & Rossing (1998) 全文開放 PDF** —— 這批把 §5 的缺口 3
>    （高音區基頻 vs 泛音的量測依據）從「只有 L2 業界媒體」升級為 **L1 量測證據**，
>    並補上缺口 2 的一半（真槌有效激發頻帶的量測值 f_max）。**判定結論不變，但論據變硬。**
> 4. 新增 §3.7：把引擎的力脈衝有效激發頻帶換算成與該論文同定義的 f_max，與量測值直接對照。
> 5. 書目更正：舊版寫的「Hall (1987)」正確書目是 **Hall & Askenfelt (1988), JASA 83(4), 1627–1638**。
>
> **2026-09-08 第二次獨立複核修訂**（複核紀錄見附錄 D）：
> 1. 引擎數字**第三次**獨立重跑：五音 FFT、三組掃描斜率、τc/x、dump 逐 partial 全部逐格重現；
>    重新渲染的 WAV 與前一輪 **SHA256 全部 IDENTICAL**（8/8）。
> 2. **取得 Fletcher, Blackham & Stratton (1962) 全文**（BYU 機構庫，非付費牆路徑）——
>    §5 缺口 3 的「殘留」與缺口 4 **同時關閉**。該文給出真鋼琴（消聲室、逐音量測）
>    **G5 / G6 的逐 partial dB 表與逐音 B 值**，正好是 A14 卡上的兩顆音。見新增的 §3.9、§3.10。
> 3. **取得 Chaigne & Askenfelt (1994) I 全文**（Kent State 課程站鏡像）——
>    這是引擎 `HammerImpulse.h` 檔頭引用的來源。核對結果：**該文並未把力脈衝寫成半正弦**，
>    反而明文把「接觸時間預先給定」列為 1970 年代舊模型的缺點。見新增的 §3.11（溯源查核）。
> 4. 三處數值／書目更正：§3.7 的 D7 列（該論文 Table I **有** D7 逐音值）、
>    §2 對 Table I 的「單調上升」描述（實際非單調）、§3.8 的 G5 B 值（4.32×10⁻³，舊寫 3.2×10⁻³）。
> 5. **判定結論不變（仍是選項 B），但 §4 的 B-1 從「沒有靶、不准動」升級為「有可引用的驗收靶」。**
>
> **2026-09-08 第三次獨立複核修訂**（複核紀錄見附錄 E）：
> 1. 引擎數字**第四次**獨立重跑（自寫腳本、不沿用前兩輪任何腳本）：五音峰值 dBFS、三組掃描斜率、
>    τc/x/等效 k、`--dump-modes` 逐 partial、由比值反解的 B 與音分——**全部逐格重現**；
>    重新渲染的 5 個 WAV 與前一輪 SHA256 **5/5 IDENTICAL**。
> 2. §2 的 L1／L2／L3 引述**再次逐條開原文核對**（PDF 自行下載 + pypdf 抽文字層 + 逐字 grep；
>    網頁自行 curl + 去標籤 + 逐字 grep），**全數命中、無不實引用**。
> 3. **新增 L1-33：Fletcher 同篇的 A0（27.5 Hz）與 G1（48.6 Hz）兩張表** ——
>    這兩顆音的基頻分別比該音最強 partial 低 **27 dB / 26 dB**
>    （A0：基頻 dB 欄 −23、該表最強是第 20 partial 的 **+4**，故相對差 27 dB；G1：基頻 −26、最強 0）。
>    意義：「弱基頻是低音現象」這條，現在可以**完全在同一台琴、同一次量測、同一種量法**裡走完
>    A0 → G6 的完整曲線，不必再借 Russell & Rossing 的 A0 數字跨論文比較。
> 4. **新增 L3-4～L3-6：Pianoteq 論壇「高音區太亮／太薄」三條**（卡上 §1-C 明確要求的那一項，前兩輪未取得）。
>    其中一條使用者自述的解法是「**把基頻音量調大一點**」——與 §4 的 B-1 方向一致（僅使用者觀感，非物理證據）。
> 5. **更正一處事實錯誤**：§5 缺口 4 原寫「Fletcher 只給五顆 G 加一顆 A0」，
>    實際是**七顆音**（A0 27.5／G1 48.6／G2 98／G3 193.5／G4 393／G5 779／G6 1568 Hz）。
> 6. 缺口狀態更新：Hall & Askenfelt (1988) 本輪改走**直接 PDF 路徑**（非摘要頁）仍 **403**（Cloudflare 挑戰），
>    第四次失敗；Reddit 經查證為**本環境的永久性封鎖**（見缺口 5 改寫），不是暫時抓取失敗。
> 7. **判定結論不變（仍是選項 B）。**

---

## §0 一句話結論

**部分合理，但主因是引擎缺陷 —— 建議判「缺陷」，走選項 B。**

「鋼琴最高音區聽起來單薄、像敲東西」在真鋼琴確實存在（社群與業界文獻都有），
**但那是最頂端一個八度左右的現象，不是 G5（784 Hz）**；而且本引擎的成因並不是那個物理現象，
是**槌頭力脈衝模型的數學零點正好砸在高音基頻上**：G5 的基頻被這個公式壓掉 **約 −34 dB**
（float32 −33.67／float64 −34.50，見 §3.3 精度註記），
而同一顆音的第二泛音只被壓約 −31 dB，所以第二泛音才會反超。

**第二關鍵的外部數字（2026-09-07 初版寫成「最關鍵」，2026-09-08 第二次複核降為佐證，L1 量測）**
——Russell & Rossing 對一整套 Steinway model D
原廠調音槌做的力脈衝量測（Acustica/Acta Acustica 84 (1998) 967–975，全文開放）：

> "In the upper two octaves, the fundamentals completely dominate the sound spectra"
> （最高的兩個八度，基頻**完全支配**整個聲音頻譜）
> — https://www.acs.psu.edu/drussell/publications/pianohammer.pdf（存取 2026-09-08）

同一篇同時給出反向的對照：**弱基頻是低音的現象**——

> "the fundamental is as much as 25 dB lower than the strongest partial"（A0 弦，基頻比最強泛音低達 25 dB）

**這一條直接回答了 A14 的第一個問題：真鋼琴高音區的基頻不但不弱，而且是壓倒性的強。**
本引擎 G5 的第二泛音比基頻高 7.4 dB、G6 高 8.2 dB，方向與量測相反。

**最關鍵的一個外部數字（2026-09-08 第二次複核新增，L1 逐音量測，比上面那條更硬）**——
Fletcher, Blackham & Stratton 在消聲室裡對一台鋼琴逐音量到的 partial 電平表
（*JASA* 34(6) 749–761, 1962；BYU 機構庫全文 PDF
https://physics.byu.edu/download/publication/1504，存取 2026-09-08），
**剛好包含 A14 卡上的 G5 與 G6**：

（引擎欄位取 `--dump-modes` 的激發振幅，四顆音同一種量法；§3.1 的渲染 FFT 值方向相同。）

| 量測音（原文 Table） | 基頻 | **量測**：第2 partial 相對基頻 | **本引擎**同一顆音 | 差距 |
|---|---|---|---|---|
| G3（Table IV） | 193.5 Hz | **+7 dB**（第2 partial 反而較強） | −1.8 dB | 8.8 dB，**同屬「兩者相當」區** |
| G4（Table V） | 393 Hz | −19 dB | −14.0 dB | 5.0 dB，**吻合** |
| **G5（Table VI）** | 779 Hz | **−22 dB** | **+8.2 dB** | **30 dB，且正負號相反** |
| **G6（Table VII）** | 1568 Hz | **−38 dB** | **+13.5 dB** | **51 dB，且正負號相反** |

同一篇還給出一條與上表方向一致的滾降律（用法邊界見 L1-23）：

> "the partials decrease in level at the rate of 2 db per 100-cps increase"
> （partial 每往上 100 cps，電平降 2 dB）
> — 同上 PDF（存取 2026-09-08）

**（2026-09-08 第三次複核補上，同一篇、同一台琴、同一次量測）** 把同文更低的兩顆音也放進來，
「基頻多弱」這件事就有了完整曲線：**A0（27.5 Hz）基頻比該音最強 partial 低 27 dB、
G1（48.6 Hz）低 26 dB**，往上到 G4/G5/G6 則**基頻自己就是最強的那一根**。
（A0 這一格是 2026-09-08 複核更正：Fletcher Table I 的 dB 欄最大值是第 20 partial 的 **+4 dB**、
不是 0 dB，基頻欄是 −23，相對差因此是 **27 dB**；更正方向是**加強**結論——基頻比原先寫的更弱。）
→ **真鋼琴的弱基頻是低音的事，而且從低音到高音一路變強、沒有回頭**（詳見 §2 L1-33、§3.9）。

**白話**：真鋼琴的「第二泛音比基頻強」只發生在 G3（193 Hz）以下的低音；
到 G5 已經是基頻壓倒第二泛音 22 dB，到 G6 是 38 dB。
**而這台引擎在 G3、G4 兩顆音上跟量測差 5～9 dB（算對得上），到 G5、G6 就整個翻過去、差 30～51 dB。**
「同一條程式在低音對、在高音錯得離譜」本身就是缺陷的指紋——物理現象不會在一個八度之內轉向。

**機制上最關鍵的一個外部數字**——Donald E. Hall（KTH《鋼琴聲學五講》）量測：

> "measured contact times in the middle range are quite similar to half of the period with which the string would vibrate alone"
> （中音域量到的接觸時間，大約等於該弦自由振動週期的一半）
> — https://www.speech.kth.se/music/5_lectures/hall/hall.html（存取 2026-09-07）

**這句話帶著一個限定條件，必須連著讀：Hall 量的是「中音域」（middle range）**，
原文並沒有說「所有音域的 τc 都等於基頻半週期」。
（**2026-09-09 修正**：本段先前把限定詞剝掉、寫成通則「真鋼琴的槌弦接觸時間 τc ≈ 基頻半週期」，
那與本文件 §3.3 自己的第 2 點自相矛盾——§3.3 明寫真鋼琴高音區的接觸時間相對於基頻週期本來就是「長」的，
`x = 2·f₁·τc > 1` 在真鋼琴是**常態**。§3 的數字本輪一個都沒動，只改 §0 的說法。）

正確的讀法是三步：

1. **基準只在中音域成立**：中音域 τc ≈ 基頻半週期，換算成 §3.3 的無因次量就是 **x ≈ 1**。
2. **引擎的 G5 已經遠超這個基準**：本引擎 G5 的 τc 是 **1.856 ms**，G5 的基頻半週期是 **0.638 ms**，
   **2.9 倍**（§3.3 的 `x = 2·f₁·τc = 2.910`）。也就是說 G5 這一格離「中音域 ≈ 1 倍」已經很遠。
3. **但「差 2.9 倍」本身不是判缺陷的理由**——因為真鋼琴高音區本來就 x > 1（§3.3 第 2 點），
   沒有一條全音域通用的「τc = 半週期」物理律可以違反。**真正的缺陷在模型的適用域**：
   §3.3 的結論是「半正弦自由脈衝這個模型，在 x ≳ 1 的區域本身就不成立」
   （真槌在接觸期間會被弦端反射波再打一次，力波形不是乾淨的半正弦，實際頻譜沒有那種深零點），
   而引擎是把一個只在 x < 1 有效的公式**外插到 x = 1.2～7.1**（§3.3 表五個音全部 x > 1：C4 1.231／A4 1.845／G5 2.910／G6 5.063／D7 7.120）。

**所以這一段的結論是**：2.9 倍是「引擎已經走進模型失效區」的指標，
不是「引擎違反了一條全音域通用的物理律」——那條通用的律並不存在。
判缺陷的依據仍然是前面那三組東西（§3.6 的梳齒、§3.5 的 τc 對照組、§3.9 的 G5/G6 逐音量測差 30～51 dB），
不是這 2.9 倍本身。

**一句白話**：這台琴的高音區，等於整台琴都裝著中音區那顆比較大的槌頭去敲很短的弦；
真鋼琴的高音其實也是「槌子相對於弦偏慢」，差別在**真鋼琴的力譜沒有那個洞**，
而引擎用的數學公式在高音的基頻上打出一個「洞」。這不是真鋼琴的行為。

---

## §1 問題（A14 原始證據）

`reports/gate_outputs/stem_verify_fur_elise_run.txt` 發現 2：乾聲單音實測（piano 引擎）

| 音 | 宣告基頻 | 整軌峰值 | 主導頻率 | 比值 | 基頻相對 |
|---|---|---|---|---|---|
| G5 | 784.0 Hz | −46.7 dBFS | 1571.5 Hz | 2.0044 | 低 21.9 dB |
| G6 | 1568.0 Hz | −54.5 dBFS | 3214.9 Hz | 2.0503 | 低 24.0 dB |
| D7 | 2349.3 Hz | −64.5 dBFS | 2358.0 Hz | 1.0029 | （主導即基頻） |

擋住 22 顆音的判定（G5×19、D7×1、G6×1、F#6×1）。三個待答問題：

1. 真鋼琴高音區基頻本來就這麼弱嗎？
2. 整體電平掉這麼多正常嗎？
3. 比值 > 2 是不是 stiffness inharmonicity 的正常表現？

---

## §2 外部證據（分級）

分級規約依 `WF0907_R_research_common.md`：
**L1 = 論文／教科書／量測報告（物理證據）**、**L2 = 業界技術媒體（可參考，非量測）**、
**L3 = 社群討論（只算「使用者觀感／需求證據」，不是物理證據）**。

### L1：物理證據

| # | 來源 | 主張 | ≤15 字原文引述 | URL |
|---|---|---|---|---|
| L1-1 | Askenfelt & Jansson,《From touch to string vibration: String contact duration and dynamic level》（KTH 五講） | 真鋼琴接觸時間：低音 ~4 ms、最高音 <1 ms | "contact durations decrease from about 4 ms in the bass" | https://www.speech.kth.se/music/5_lectures/askenflt/stricont.html |
| L1-2 | 同上 | 接觸時間相對於基頻週期的比例，低音短、**高音反而長** | "the opposite situation prevails in the treble" | 同上 |
| L1-3 | 同上 | 低音區接觸時間僅佔基頻週期約 10% | "contact duration is only about 10 % of the fundamental period" | 同上 |
| L1-4 | **Donald E. Hall,《The hammer and the string》（KTH 五講）** | **中音域 τc ≈ 基頻半週期** | "contact times in the middle range are quite similar to half of the period" | https://www.speech.kth.se/music/5_lectures/hall/hall.html |
| L1-5 | 同上 | 理想理論預測的頻譜「不隨頻率下降」，只有擊弦點造成的「洞」 | "the harmonic strengths do not fall off at all toward higher frequencies (0 dB/oct)" | 同上 |
| L1-6 | 同上 | 槌在弦上停留有限時間，期間力可以「複雜地變化」 | "the force exerted by the hammer upon the string may change in a complex way" | 同上 |
| L1-7 | **Woodhouse,《Euphonics》12.2 Hitting strings: the piano** | **真槌的力波形不是半正弦**：弦端反射波在接觸期間回來，力會二次跳升 | "it jumps up again when the first reflected pulse arrives back" | https://euphonics.org/11-2-hitting-strings-the-piano-and-its-relatives/ |
| L1-8 | 同上 | 之後多重反射進來，波形更複雜 | "the pattern grows more complicated as multiple reflections arrive" | 同上 |
| L1-9 | Woodhouse,《Euphonics》2.2.6 Frequency spectrum of a hammer tap | 標準理想模型就是半週期餘弦力脈衝 | "a half-cycle of a cosine wave, at the (radian) frequency" | https://euphonics.org/2-2-6-frequency-spectrum-of-a-hammer-tap/ |
| L1-10 | Woodhouse,《Euphonics》12.1.2 | 有限長脈衝的作用是**低通濾波**（設計上是「濾掉高頻」，不是「在基頻打洞」） | "the finite-length impulse has the effect of a low-pass filter" | https://euphonics.org/12-1-2-the-maximum-bandwidth-of-a-bouncing-hammer/ |
| L1-11 | **Conklin,《Piano design factors: Where should the hammer hit the string?》（KTH 五講）** | 真鋼琴擊弦比 d/L 低音略小於 1/8，到 A4 緩降，**A4 之上急降** | "d/L in the bass is a little less than 1/8, and it decreases gradually up to around A4" | https://www.speech.kth.se/music/5_lectures/conklin/whereshould.html |
| L1-12 | 同上 | 中高音的擊弦比是「第一泛音能量最大」與「音色最優雅」的折衷 | "a compromise between maximum first partial energy and the most graceful tone" | 同上 |
| L1-13 | 同上 | 縮短擊弦距離會讓音色變薄，因為基頻能量變少 | "makes the tone sound thinner because less fundamental energy is present" | 同上 |
| L1-14 | Askenfelt & Jansson,《Bass, middle and treble》（KTH 五講） | 高音區泛音少但頻率高；低音泛音多但不超過 4 kHz | "The treble contains only few partials, but these reach high frequencies" | https://www.speech.kth.se/music/5_lectures/askenflt/basmidtr.html |
| L1-15 | Gràcia & Sanz-Perela (2016), *The wave equation for stiff strings and piano tuning*, arXiv:1603.05516（原文 PDF 已取得並逐字擷取） | 鋼琴弦的非諧性係數 B 典型值約 10⁻³ | "its typical values for a piano string are about 10−3" | https://arxiv.org/pdf/1603.05516 |

**L1-16～L1-22（2026-09-08 新增；同一篇，原文 PDF 開放取得並逐字擷取）**
Russell, D. & Rossing, T. (1998),《Testing the Nonlinearity of Piano Hammers Using Residual Shock Spectra》,
*ACUSTICA / acta acustica* **84**, 967–975。量測對象：Steinway model D（274 cm）原廠調音整套槌、
1972 Steinway model B 硬化槌、未整音軟槌；撞速 1–6 m/s。存取 2026-09-08。
https://www.acs.psu.edu/drussell/publications/pianohammer.pdf

| # | 主張 | ≤15 字原文引述 |
|---|---|---|
| **L1-16** | **最高兩個八度：基頻完全支配頻譜**（直接推翻「高音基頻本來就弱」） | "In the upper two octaves, the fundamentals completely dominate the sound spectra" |
| **L1-17** | **弱基頻是低音現象**：A0 基頻比最強泛音低達 25 dB | "the fundamental is as much as 25 dB lower than the strongest partial" |
| **L1-18** | **高音區槌弦接觸時間是「好幾個週期」**（即 x = 2·f·τc ≫ 1 在真琴是常態） | "in the treble register the hammer-string contact time is several periods" |
| **L1-19** | 中音域接觸時間約半週期、低音只佔基頻週期一小部分（與 L1-4 互相獨立佐證） | "in the middle register it is about half the period" |
| **L1-20** | **真槌力波形不是自由半正弦**：弦近端反射波會在脈衝形狀上造成凹谷 | "reflections from the near end of the string can cause valleys in the pulse shape" |
| **L1-21** | 槌與弦之間常有**多次接觸** | "there are often multiple contacts between hammer and string" |
| **L1-22** | **低音區 f_max 遠高於基頻；高音區 f_max 反而落在基頻附近**（有效激發帶與音階的交叉點在高音端） | "in the treble region the values of f max surround the fundamental" |

補充可引用數字（同篇，供 §3.7 與 B-1 使用）：

- 有效激發帶峰值頻率的擬合式與逐音係數（Table I）：`f_max = a·v^b`
  （原文："The data can be fit fairly well to an equation of the form f max = av b"）。
  **2026-09-08 第二次複核更正**：初版寫「a 由 763.2 **單調**升到 1306.9」——原文 Table I **不是單調**，
  低音端先降後升（A0 763.2 → D1 732.3 → **A1 639.7** → D2 746.6 → … → A6 1147.0 → **D7 1261.9** → F7 1306.9）。
  正確說法是「整體由低音向高音上升，低音端有一個凹陷」。
  b 的**全表範圍**是 0.36–0.64，但原文自己的描述是
  "the exponent b ranges between 0.4 and 0.5 for most of the voiced Steinway hammers"，
  並補 "There is a slight increase in values of b from bass to treble"。
- **Table I 有 D7 的逐音值**（初版誤寫「未逐音給值」）：D7（第 78 鍵）**a = 1261.9、b = 0.64**。
- 實測點（Fig. 7）：Hammer A0 在 1 m/s → **f_max = 775 Hz**、4 m/s → **1370 Hz**；
  Hammer F7 在 1 m/s → **1300 Hz**、4 m/s → **3038 Hz**。
- 對照該弦基頻（原文，2026-09-08 複核補回被截短的開頭）：
  "The fundamental frequency of the F7 string is 2794 Hz, which lies between the values of f max shown in Figure 7."
  （原引述寫成 "The F7 string is 2794 Hz, …"，數字與條件都沒改，但引號內文字不是逐字，已改回原文。）
  → **F7 的 f_max/f₀ ≈ 0.47（弱奏）～1.09（強奏），也就是「有效激發帶剛好罩住基頻」。**
- 高音槌強烈激發基頻、只弱激發一兩個泛音（原文）：
  "a treble hammer would strongly excite the fundamental, but weakly excite only one or two harmonics"
- 氈的非線性指數（與引擎 B4 的 α 錨點可對照）：
  "a smooth increase from p ' 2 in the bass, to p ' 4 in the treble"
  （原文 PDF 的 `≈` 抽字為 `'`；語意為 p 由低音約 2 平滑升到高音約 4）。

**使用邊界（必須一併記住，否則會過度解讀）**：該論文量的是**槌打剛性力感測器**，不是打弦；
作者自己在同一段列了三個因此不能直接外推的理由（L1-20 反射凹谷、L1-21 多次接觸、槌柄振動）。
所以下面 §3.7 的對照只能用在**趨勢與交叉點位置**，不能拿 f_max 當成可以直接寫進程式的目標常數。

**L1-23～L1-29（2026-09-08 第二次複核新增；同一篇，全文 PDF 已取得並逐字擷取）**
Fletcher, H., Blackham, E. D. & Stratton, R. (1962),《Quality of Piano Tones》,
*Journal of the Acoustical Society of America* **34**(6), 749–761。
量測對象：一台狀況良好的直立鋼琴，置於**消聲室**內；用分析儀在音的衰減起點取 partial 結構，
再用 100 音合成器重建、由八人評審團做 A-B 盲測，**評審分不出真假才算分析正確**。
取得管道：Brigham Young University 機構庫（Fletcher 任職單位）全文 PDF，**非付費牆路徑**。
存取 2026-09-08。https://physics.byu.edu/download/publication/1504
（AIP 官方頁 `pubs.aip.org/asa/jasa/article-abstract/34/6/749/600921` 2026-09-08 仍回 403，故走機構庫。）

| # | 主張 | ≤15 字原文引述 |
|---|---|---|
| **L1-23** | **partial 電平的滾降律：每上升 100 cps 降 2 dB**（本報告目前唯一可引用的「輸出頻譜滾降靶」） | "the partials decrease in level at the rate of 2 db per 100-cps increase" |
| **L1-24** | 中央 C 以下的 partial 必須非諧才像鋼琴（= 非諧性在低音才重要） | "The partials below middle C must be inharmonic in frequency to be piano-like" |
| **L1-25** | 衰減時間：低音可達 20 秒、最高音不到 1 秒 | "The decay can be as long as 20 sec for the lower notes" |
| **L1-26** | 逐音量測的對象與方法（消聲室 + 直立琴 + 衰減起點分析） | "produced on a good upright piano which was placed in the anechoic chamber" |
| **L1-27** | 非諧性公式與本引擎 `StringModel` 用的是**同一條**（$f_n=n f_0\sqrt{1+Bn^2}$、$B=\pi^3 Q d^4/64 l^2 T$），因此 B 值可直接比 | "B=-3Qd4/64 lT"（OCR 缺 π³ 上標，公式形狀與引擎一致） |
| **L1-28** | **779 Hz（≈G5）逐 partial 電平（Table VI）**：0 / −22 / −24 / −36 / −31 dB，**B = 0.0002** | "1 779 779 779.1 0" 與 "2 1558 1562 1558.6 --22" |
| **L1-29** | **1568 Hz（=G6）逐 partial 電平（Table VII）**：0 / −38 / −28 dB，**B = 0.0002** | "1 1568 1568 1568.2 0" 與 "2 3136 3134 3137 --38" |

> **音名對照的誠實聲明**：原文用的是 Helmholtz 式音名（G‴、G″、G′…），
> 掃描 PDF 的文字層把上標撇號抽掉了，因此**本報告一律以原文表格裡的基頻數字認音**
> （98 / 193.5 / 393 / 779 / 1568 Hz → 科學音高 G2 / G3 / G4 / G5 / G6），
> 不依賴 OCR 出來的音名字串。所有引述的 dB 與 B 值都直接抄自表格數字列。

同篇另外三張表（供 §3.9 的跨音域趨勢用，原文逐格數字）：
G2（98 Hz, B=0.00015）partial 1/2 = −1/0 dB；G3（193.5 Hz, B=0.00005）partial 1/2 = −7/0 dB；
G4（393 Hz, B=0.0004）partial 1/2 = 0/−19 dB。
**這五張表合起來就是「弱基頻是低音現象、到高音完全反轉」的逐音量測證據鏈**，
而且用的是與本引擎相同的 B 定義，可以逐音對照。

| # | 主張（**2026-09-08 第三次複核新增**） | ≤15 字原文引述 |
|---|---|---|
| **L1-33** | **同篇還有更低的兩顆音，把「基頻多弱」直接量出來**：A0（27.5 Hz, B=0.00053）基頻 dB 欄 **−23**、該表最強的是**第 20 partial 的 +4 dB**（故基頻比最強 partial 低 **27 dB**）；G1（48.6 Hz, B=0.00028）基頻 **−26 dB**、該表最強的是第 3 partial（0 dB） | "1 27.5 27.5 27.51 --23"、"20 550 605 605 + 4" 與 "1 48.6 49 48.6 --26" |

> **量法註記（2026-09-08 複核更正）**：Fletcher 的 dB 欄是**相對電平**、參考點未在文中明寫。
> Table II–VII（G1–G6）六張表的最大值**恰好都是 0 dB**，所以「0 dB = 該音最強 partial」在那六張表成立；
> **但 Table I（A0）不成立**——該表最大值是第 20 partial 的 **+4 dB**（原文 "20 550 605 605 + 4"）。
> 因此凡是要講「基頻相對該音最強 partial 低幾 dB」，都必須**先在該表找最大值再相減**，不能直接讀基頻那一格。

> **L1-33 為什麼重要**：在此之前，「真鋼琴低音基頻很弱」這件事是引 Russell & Rossing 的
> "as much as 25 dB"（L1-17，**另一篇、另一台琴、另一種量法**）。
> 現在同一台琴、同一次消聲室量測、同一張 dB 欄的定義，
> 從 A0（基頻比最強 partial 低 27 dB）→ G1（−26）→ G2（−1）→ G3（−7）→ G4（0，第2 partial −19）
> → G5（0，第2 −22）→ G6（0，第2 −38）**一條曲線走完**。
> **跨論文比較的那一層不確定性因此被拿掉了。**

同篇還給出高音區「每個 partial 之間應該差幾 dB」的評審容許帶（供 §4 的驗收指標用）：

- 最高的那顆測試音："Piano-like quality had limits from 40 to 7.5 db per partial"
  （每個 partial 之間差 7.5–40 dB 都還像鋼琴；中位 32 dB），
  且 "The fundamental alone has a piano-like quality"（只留基頻仍像鋼琴）。
- 三顆測試音的中位值分別是 2、8、32 dB per partial，原文："each being four times that of the preceding tone"。
- **用法邊界**：這是「合成音要像鋼琴」的**聽感容許帶**（八人評審團），
  對本專案是「外部可引用的靶」，**不是 ISO/業界標準、也不能由工程端逕自當成新容差（R2）**。

**L1-30～L1-32（2026-09-08 第二次複核新增；全文 PDF 已取得並逐字擷取）**
Chaigne, A. & Askenfelt, A. (1994),《Numerical simulations of piano strings. I.
A physical model for a struck string using finite difference methods》,
*JASA* **95**(2), 1112–1118。取得管道：Kent State 課程站鏡像 PDF（非付費牆路徑），存取 2026-09-08。
https://www.math.kent.edu/~zheng/62262/piano_wave.pdf
**這一篇就是引擎 `src/physics/HammerImpulse.h` 檔頭引用的來源**，所以它的內容同時是溯源查核（見 §3.11）。

| # | 主張 | ≤15 字原文引述 |
|---|---|---|
| **L1-30** | 該文的槌力**不是**半正弦，而是非線性冪次律 $F=K\lvert y\rvert^p$ 動態解出 | "the force F/(t) is a result of a nonlinear interaction process" |
| **L1-31** | **接觸時間是模型的「輸出」，不是預先給定的參數** | "This yields, among other things, the contact duration" |
| **L1-32** | 該文明文把「接觸時間預先給定」列為 1970 年代舊模型的缺點 | "was set beforehand as a known parameter" |

### L2：業界技術媒體（可參考，不是量測報告）

| # | 來源 | 主張 | ≤15 字原文引述 | URL |
|---|---|---|---|---|
| L2-1 | *Sound On Sound*,「Recording Real Pianos」 | **最低音**的基頻可以比最強泛音低達 25 dB（弱基頻是**低音**現象） | "the fundamental can be as much as 25dB below its strongest harmonics" | https://www.soundonsound.com/techniques/recording-real-pianos |
| L2-2 | 同上 | **最高音區反過來：第一個泛音比基頻低約 20 dB，波形近乎正弦** | "typically 20dB below its fundamental, producing an almost sinusoidal sound wave" | 同上 |
| L2-3 | Timbre & Orchestration Resource,「Keyboard｜Piano Essentials」 | 最高八度衰減更快、要很大力才彈得出真正的 ff | "In the top octave, the decay is more rapid" | https://timbreandorchestration.org/isfee/extreme-orchestration/keyboard/piano |

### L3：社群（使用者觀感證據，不是物理證據）

| # | 討論串 / 日期 / 可見資訊 | 發言（原文引述） |
|---|---|---|
| L3-1 | Piano World Forums,「Top Octave on a Piano」，2004-06-10～12（列印檢視頁看不到讚數） | Jeffrey（原 po，06/10/04）："a 'striking' or 'clicking' sound, like a hammer on wood" |
| L3-2 | 同上 | Axtremus（06/11/04）："no 'tone' of which to speak in the top few notes" |
| L3-3 | Modartt / Pianoteq 使用者論壇,「Model B High Notes」，首帖 2016-05-10（該論壇無公開讚數） | Alex Cremers（2016-05-14）："Some high notes are not only out of tune but also a bit too clunky" |
| **L3-4** | **Modartt / Pianoteq 論壇,「Brittleness of high notes...」，2017-10-17（無公開讚數）**（2026-09-08 第三次複核新增） | chriswarren（原 po，17-10-2017 11:41）："reduce the harsh brittleness of the upper treble" |
| **L3-5** | 同上串 | honjr（17-10-2017 13:10）："the harshness (to my ears) is largely due to overtone inharmonicity" |
| **L3-6** | **Modartt / Pianoteq 論壇,「Four areas for possible improvement」，2015-03-09（無公開讚數）**（2026-09-08 第三次複核新增） | NathanShirley（09-03-2015 07:22）："increasing the fundamental tone's volume a bit helps significantly" |

社群證據的用法（依鐵律 3）：只能證明「**最頂端幾個音**聽起來像敲木頭」是真實存在的使用者觀感，
且 L3-1/L3-2 都把它當成**這台琴需要調整的問題**在討論，不是當成「鋼琴本來就該這樣」。
**它不能拿來替 G5（784 Hz）辯護** —— G5 是高音譜表上方一點的音，離「top few notes」還有兩個半八度。

**（2026-09-08 第三次複核）L3-1 的完整原文更值得記一筆**：Axtremus 那句的完整版是
"I've heard pianos so bad that to my ears there is no 'tone' of which to speak in the top few notes, just wooden 'tok tok tok'"
——原文用的是 **"pianos so bad"**（爛琴），**不是**「鋼琴本來就這樣」。上面那段用法說明因此比原本寫的還站得住。

**L3-4～L3-6 的用法（這是卡上 §1-C 明確要求的那一項，前兩輪未取得，本輪補上）**：
Pianoteq 是**同類的物理建模鋼琴**，所以它的使用者抱怨與本專案是同一種東西的觀感證據——
但**仍然只是觀感，不是物理量測**，不得用來支撐任何 dB 數字。
可以合理讀出的只有兩點：(1)「物理建模鋼琴的高音區聽起來不對」是同業普遍收到的回饋；
(2) L3-6 那位使用者自己找到的補救方向是「**把基頻音量調大**、把槌調軟」——
**恰好就是 §4 的 B-1（基頻不該被壓掉）與 B-2（τc 音高律）兩個環節**。
這條**不能當成 B-1/B-2 正確的證據**（社群不是物理證據），只能當成「方向不孤僻」的旁證。

### 未取得原文（誠實登記，依鐵律 1 / R4）

| 來源 | 狀況 |
|---|---|
| ~~Fletcher, Blackham & Stratton (1962), *Quality of Piano Tones*, *JASA* **34**(6), 749–761~~ | **2026-09-08 第二次複核已取得全文**（BYU 機構庫，AIP 頁仍 403）→ 升級為 L1-23～L1-29。初版寫「每 100 cps 降 2 dB 未核實不採用」的那個數字，**現已在原文摘要與正文逐字核實，本輪起採用** |
| ~~Chaigne & Askenfelt (1994), *Numerical simulations of piano strings* I~~ | **2026-09-08 第二次複核已取得 Part I 全文**（Kent State 鏡像）→ 升級為 L1-30～L1-32、§3.11 |
| Chaigne & Askenfelt (1994) *Numerical simulations of piano strings* **II**, JASA 95(3) 1631–1640 | 仍**未取得原文**（Part II 才有逐音參數表 K/p/質量；Part I 只有數值方法） |
| **Hall & Askenfelt (1988)**, *Piano string excitation V: Spectra for real hammers and strings*, *JASA* **83**(4), 1627–1638, DOI 10.1121/1.395917 | 目標頁 HTTP 403（2026-09-08 再試仍 403），**未取得原文**。**書目更正**：初版誤記為「Hall (1987)」 |
| Conklin (1996) *Design and tone in the mechanoacoustic piano* Part II | **未取得原文** |
| Giordano,《Physics of the Piano》 | 未取得可引用全文；nanohub 投影片 PDF 文字層無相關內容，**未取得原文** |
| Acta Acustica (2021)《Piano bass strings with reduced inharmonicity》 | HTML 與 PDF 皆 403，**未取得原文**（B 值範圍改引 L1-15） |
| R. W. Young (1952)《Inharmonicity of Plain Wire Piano Strings》逐音 B 值表 | PTG 鏡像重導向失敗、afn.org DNS 已不存在，**未取得原文** |
| Stulov (2003)《String vibration spectra excited by different piano hammers》 | 2026-09-08 新查到的候選（Semantic Scholar 有索引），**本輪未取得可引用原文**，未引用 |
| Meyer《Acoustics and the Performance of Music》音域 SPL 表 | 2026-09-08 再查一輪（含 KTH 五講「dynamic level」該頁），**仍查不到可存取版本**，見 §5 缺口 1 |
| Meyer,《Acoustics and the Performance of Music》各音域 SPL 表 | **查不到可存取版本**；「同力度下 C7 vs C4 的 SPL 差」這個數字**本輪沒查到**（見 §5 缺口 1） |
| Reddit r/piano | 本執行環境無法抓取 reddit.com / old.reddit.com（工具回「unable to fetch」），改用 Piano World 與 Pianoteq 論壇 |

---

## §3 引擎現況數字（實測，未改碼）

### 3.1 復現與擴充

單音 score（piano 引擎、steel、Ø1.0 mm、velocity 0.45、duration 1.0 s、效果全關、`normalize: false`、24-bit），
渲染後以 numpy 做 Hann 窗 FFT：

| 音 | MIDI | 峰值 dBFS | 主導頻率 | 主導/基頻 | 基頻 T60 | FFT 第2泛音−第1泛音 |
|---|---|---|---|---|---|---|
| C4 | 60 | −26.67 | 260.3 Hz | 0.9951 | 2.87 s | −8.77 dB |
| A4 | 69 | −27.58 | 442.0 Hz | 1.0046 | 1.72 s | −8.72 dB |
| **G5** | 79 | **−42.63** | **1582.7 Hz** | **2.0188** | 0.97 s | **+7.41 dB** |
| **G6** | 91 | **−53.30** | **3205.5 Hz** | **2.0443** | 0.48 s | **+8.23 dB** |
| D7 | 98 | −60.41 | 2356.1 Hz | 1.0029 | 0.32 s | −17.14 dB |

方向與 A14 原始證據完全一致（G5/G6 第二泛音反超、D7 只是太安靜）。
dB 數值與原證據不同是**量法不同**（原證據比的是「基頻帶能量 vs 整軌峰值」，本表比的是「第2泛音 vs 第1泛音」）。

### 3.2 逐環節拆解（本卡的核心結果）

`--dump-modes` 的每個模態振幅可以被下式**完全復現**（預測值與 dump 值符合到 4–5 位有效數字）：

```
amp(n) = |sin(n·π·0.125)|            <- 擊弦點（StringModel::calculateModes，固定 1/8）
       × spectralTilt^((pn−1)·0.2)   <- 創意層（steel: 0.95026，第2泛音只差 −0.09 dB）
       × H(f_n, τc)                  <- 槌頭力脈衝頻譜（HammerImpulse::forceSpectrumMagnitude）
       × gain                        <- noteComp / √弦數（整組同乘，不改相對比例）
```

各環節對「基頻變弱」的貢獻：

| 環節 | 第2泛音 − 第1泛音 的貢獻 | 隨音高變化？ | 判斷 |
|---|---|---|---|
| 擊弦點 `sin(nπ/8)` | 固定 **+5.34 dB** | 否（全鍵盤都 0.125） | 不是元凶（且方向與真琴一致，見 L1-11） |
| spectralTilt | −0.09 dB | 幾乎不變 | 不是元凶 |
| **槌頭力脈衝 H(f, τc)** | **C4 −13.3 / A4 −15.3 / G5 +3.0 / G6 +8.2 dB** | **是，劇烈** | **元凶** |
| noteComp | 0 dB（整組同乘） | 是（但只改總電平） | 元凶之二（見 3.4） |
| T60 / 琴橋損耗 B1 | 0 dB（不改初始振幅） | 是 | 只影響「能量」，不影響「峰值比例」 |

`H(f, τc) = |cos(ωτc/2)| / |1 − (ωτc/π)²|`。令 **x = 2·f·τc**，這個函數在 **x = 3, 5, 7 …** 有**深零點**。

| 音 | τc（B4 求解器） | 基頻半週期 | **x = 2·f₁·τc** | **H(f₁)** | **H(f₂ 實際)**（註） | dump 第2−第1 |
|---|---|---|---|---|---|---|
| C4 | 2.354 ms | 1.911 ms | 1.231 | −3.22 dB | −16.52 dB | −8.05 dB |
| A4 | 2.097 ms | 1.136 ms | 1.845 | −7.83 dB | −23.10 dB | −10.03 dB |
| **G5** | 1.856 ms | 0.638 ms | **2.910**（幾乎正中零點 x=3） | **−33.67 dB** | −30.67 dB | **+8.24 dB** |
| **G6** | 1.615 ms | 0.319 ms | **5.063**（幾乎正中零點 x=5） | **−50.13 dB** | −41.91 dB | **+13.47 dB** |
| D7 | 1.515 ms | 0.213 ms | **7.120**（幾乎正中零點 x=7） | −50.00 dB | −74.82 dB | −19.66 dB |

（**註，2026-09-08 複核更正欄名**）第 6 欄原標「H(2f₁)」，但欄內數字實際是取在**引擎的非諧第 2 partial 真實頻率 f₂ 上**，
不是整數倍 2f₁。兩者在零點鄰域可以差很多：D7 的 f₂/f₁ = 2.109，
**H(f₂ 實際) = −74.8 dB，而 H(2f₁) = −46.5 dB，差 28 dB**（C4/A4/G5 三格兩種取法只差 0.04 dB 以內，G6 差 1.8 dB）。
欄名已改為 **H(f₂ 實際)**，避免被讀成整數倍取值。

**這就是全部答案**：τc 沒有隨音高縮短得夠快，x 一路長大，基頻從主瓣掉進旁瓣零點。

> **數值精度註記（2026-09-08 複核補上）**：τc 與 x 這兩欄用 float64 獨立重算，與上表**完全一致**
> （C4 1.231 / A4 1.845 / G5 2.910 / G6 5.063 / D7 7.120，等效 k = 0.2116）。
> 但 **H(f₁) 這一欄在零點附近對浮點精度極度敏感**：float64 重算得 G5 −34.50 dB、G6 −47.91 dB、D7 −48.44 dB，
> 與上表（引擎 float32 路徑）的 −33.67 / −50.13 / −50.00 dB 差 0.8～2.2 dB。
> **這個差異本身就是「基頻正踩在零點上」的證據**（遠離零點的 C4/A4 兩格只差 0.02 dB），
> 對結論沒有影響，但引用時請寫「約 −34 dB」而不要引用到小數點後兩位。

### 3.3 τc 音高律 vs 文獻

| 模型 | A0(27.5 Hz) | C4 | A4 | C8(4186 Hz) | C2→C7 等效指數 k（τc ∝ f^−k） |
|---|---|---|---|---|---|
| 現行 B4 `pianoHammerTauC()`（2026-08-27 落地） | 3.26 ms | 2.35 ms | 2.10 ms | **1.46 ms** | **0.212** |
| B4 之前的 `keytrackScale()`（k=0.32） | 4.96 ms | 2.41 ms | 2.04 ms | 0.99 ms | 0.320 |
| 文獻 L1-1（4 ms → <1 ms 全音域） | ~4 ms | — | — | **<1 ms** | ≈0.276 |
| 文獻 L1-4（τc ≈ 基頻半週期） | 18.2 ms | 1.91 ms | 1.14 ms | 0.12 ms | 1.0（局部） |

**兩個獨立的問題**：

1. **τc keytrack 太平**：B4 的等效指數 0.212 **比 B4 之前的 0.320 還平**，也比文獻 L1-1 的 ≈0.276 平。
   C8 給到 1.46 ms，文獻說 <1 ms。**B4 在這一項上讓高音變差了**
   （B4 卡的動機是另一件事：把力度指數換成鋼琴氈的接觸律，本報告不否定該動機）。
2. **但是把 τc 調對還不夠**：就算完全照 L1-1 的 4 ms→1 ms，C8 的 x 仍然是 8.4，一樣在旁瓣裡。
   L1-2 已經說了：**真鋼琴高音區的接觸時間相對於基頻週期本來就是「長」的**。
   所以「x > 1」在真鋼琴是**常態**，而真鋼琴的高音基頻並沒有被打洞（L2-2：頂端第一泛音比基頻低 20 dB）。
   **結論：半正弦自由脈衝這個模型，在 x ≳ 1 的區域本身就不成立**——因為真槌在接觸期間會被弦端反射波
   再打一次（L1-7、L1-8），力波形不是乾淨的半正弦，實際頻譜沒有那種深零點。
   引擎現在是把一個只在「x < 1」有效的公式外插到 x = 7。

### 3.4 響度補償已經飽和

`ModalResonator::loudnessCompensationGain()` 的 clamp 是 [0.25, 4.0]（±12 dB）。
反解 dump 振幅得到的 noteComp：

| MIDI | 61 | 64 | **67** | 69 | 79 | 91 | 98 |
|---|---|---|---|---|---|---|---|
| noteComp | 2.767 | 3.324 | **4.000（飽和）** | 4.000 | 4.001 | 3.997 | 3.994 |

**從 MIDI 67（G4）開始，跨音域響度補償就頂到上限、完全失去補償能力。**
所以高音電平掉下去之後沒有任何機制救得回來。

### 3.5 整體電平斜率（同 velocity 0.45，MIDI 37→87，每音 2.5 s 間隔，乾聲不正規化）

| score | 峰值斜率（37→87） | RMS 斜率（37→87） | RMS 全域極差 |
|---|---|---|---|
| **piano（felt，現況）** | **−22.10 dB** | **−27.46 dB** | 30.47 dB |
| cimbalom（wood_mallet、strike 0.3，預設） | −2.01 dB | −3.74 dB | 5.70 dB |
| **piano 引擎 + `exciter: wood` + strike 0.125（只換 τc）** | **−2.16 dB** | **−4.48 dB** | 6.41 dB |

**這是決定性的對照組**：第一列與第三列**同一個引擎、同一個弦模型、同一個擊弦點 0.125、
同一套阻尼與響度補償，唯一的差別是槌頭 τc**。τc 一換，22 dB 的電平斜坡就消失成 2 dB。

（TODO D8 記載「cimbalom 同域僅 4.4 dB」，本輪 cimbalom 實測 −3.74 dB RMS，量級一致；
piano 的 −27.46 dB 比 cimbalom 差 24 dB，但還沒到 tongue_drum 的 40.3 dB。）

電平斷崖的位置也對得上：MIDI 69→80 之間掉 **−15.6 dB**（−27.58 → −43.19 dBFS），
正是 x 從 1.85 長到 3.0（穿越第一個零點）的那一段。

### 3.6 非單調「梳齒」是決定性的人工痕跡

跨鍵盤掃描 `--dump-modes` 顯示第2泛音超過第1泛音的音是：
**MIDI 37–52（低音，與文獻方向一致）與 MIDI 79–81（G5 附近，與文獻相反）**。
更關鍵的是同一顆音內部也亂：G6 的第3泛音比基頻高 **+9.10 dB**，第4泛音又掉到 −1.04 dB；
MIDI 64 的第2泛音掉到 −28.30 dB、MIDI 76 掉到 −22.42 dB（那是第2泛音落進零點）。
**沒有任何量測到的鋼琴頻譜長這樣**——L2-2 說最高音區近乎正弦、L1-14 說高音「泛音少」，
都不是「第3泛音比基頻大 9 dB、第2泛音在鄰音之間忽大忽小 20 dB」。

### 3.7 引擎的「有效激發帶」vs 量測的 f_max（2026-09-08 新增，本卡最硬的一組對照）

L1-22 給了一個可以直接對照的量：**residual shock spectrum 的峰值頻率 f_max**，
物理意義是「這顆槌最會激發哪個頻段」。它的定義是力譜乘上角頻率（原文：
"obtained by multiplying the power spectrum (Fourier transform of the force pulse) by ω"），
所以可以用**完全相同的定義**套到引擎的 H(f, τc) 上，得到引擎的等效 f_max。

引擎側算法：對 `f·H(f, τc)` 在 1 Hz–12 kHz 掃描取極大值，τc 由 `pianoHammerTauC()` 逐音求解
（本卡以 Python 重寫同一條公式，數值與原始碼逐項對答案）。

| 音 | 基頻 f₀ | **量測 f_max（Russell & Rossing）** | 量測 f_max/f₀ | **引擎等效 f_max**（v=0.2 / 0.45 / 0.9） | 引擎 f_max/f₀ |
|---|---|---|---|---|---|
| A0 | 27.5 Hz | 775 Hz @1 m/s、1370 Hz @4 m/s | **28 – 50** | 152 / 210 / 275 Hz | 5.5 – 10.0 |
| F7 | 2794 Hz | 1300 Hz @1 m/s、3038 Hz @4 m/s | **0.47 – 1.09** | 304 / 456 / 645 Hz | **0.11 – 0.23** |
| **D7** | 2349 Hz | **1262 Hz @1 m/s、3064 Hz @4 m/s**（Table I 逐音擬合 a=1261.9、b=0.64；2026-09-08 更正，初版誤寫「未逐音給值」） | **0.54 – 1.30** | 301 / 451 / 638 Hz | **0.13 – 0.27** |
| C8 | 4186 Hz | 同上 | ≈1 | 313 / 469 / 663 Hz | 0.07 – 0.16 |

**兩件事一次看清楚**：

1. **交叉點錯了約三個八度。** 量測（L1-22 + Fig. 9）說：低音區 f_max 遠高於音階線、
   **高音區 f_max 才降到與音階線交錯**。引擎的等效 f_max 全鍵盤只在 **200–660 Hz** 之間游走，
   跟音階線的交叉點大約落在 **A4（440 Hz）**——也就是說引擎從 A4 往上，
   槌的「有效激發帶」就已經整個掉到基頻底下了，而真琴要到最高兩個八度才會接近這個狀態。
2. **F7 差了 4–9 倍。** 量測 F7 的 f_max 剛好罩住基頻（0.47–1.09 倍），
   引擎只有 0.11–0.23 倍。這正是 §3.2「基頻掉進零點」的另一種說法，
   但這一次是**跟一組真琴量測值比出來的倍數**，不是只靠引擎內部自洽論證。

**這組對照的邊界**（誠實登記，勿超譯）：
(a) 量測是槌打**剛性感測器**、不是打弦，作者自列三個外推限制（見 §2 使用邊界）；
(b) 引擎的 velocity 是 0–1 正規化 MIDI proxy、**不是 m/s**（原始碼註解已明載），
    所以速度軸不能逐點對齊，只能比「同一顆槌在合理力度範圍內的帶寬位置」；
(c) 引擎的 f_max 是本卡用相同定義**推導**出來的，不是文獻數字，不得當成文獻引用。
即使把 (a)(b)(c) 全部打折，**「交叉點差三個八度」這個量級不可能由這三項誤差解釋掉。**

### 3.8 順帶查到（不屬於 A14 判定，但登記）

- **非諧性比值方向正確、但高音的量級不正確**：G5 dump 的 f₂/f₁ = 2.01287、G6 = 2.05034。
  **2026-09-08 第二次複核數值更正**：初版由這兩個比值反推的 B 值（3.2×10⁻³ / 1.27×10⁻²）
  是用線性近似 `f₂/f₁ ≈ 2(1+2B)` 算的，該近似式係數錯了。
  用引擎與文獻共用的定義 `fₙ = n·f₁·√(1+B n²)`（`StringModel.h:324`，與 L1-27 同式）反解，
  正確值是 **G5 B = 4.32×10⁻³、G6 B = 1.73×10⁻²**（診斷用 1.0 mm 弦徑；引擎預設 0.8 mm 時為 2.77×10⁻³ / 1.11×10⁻²）。
  **「比值 > 2」的方向本身是正確的**（A14 原本的猜測在這一點成立），
  **但量級不對**——詳見新增的 §3.10（與 L1-28/L1-29 的逐音量測 B 直接對照，高音差 14–55 倍）。
  成因指向 `StringModel::lengthFromMidiNote()` 每八度弦長減半的假設
  （真鋼琴高音弦比等比例縮短要長，正是為了壓低 B）——**這是另一件事，不在 A14 範圍，登記為 open item**。
- **擊弦點固定 0.125 與真琴不符**（L1-11：A4 之上 d/L 急降），但這個偏差會讓基頻**偏強**不是偏弱，
  所以它不是 A14 的成因；同樣登記為 open item。
- **（2026-09-08 新增）B4 的槌氈非線性指數 α 在高音端可能偏低。**
  引擎 `kPianoHammerAlpha` 的三個錨點是 C2 = 2.3、C4 = 2.5、**C7 = 3.0**
  （來源：Woodhouse Euphonics §12.2.1 Table 2，轉引 Hall & Askenfelt）。
  **2026-09-08 複核更正——這裡原本寫「Russell & Rossing (1998) 量了多台鋼琴的整音槌」，是誤植。**
  該句在 Russell & Rossing PDF 裡的上下文是**在介紹 Hall & Askenfelt 的動態量測法**：
  "In addition to their static measurements, Hall and Askenfelt [5, 10] also devised a dynamic method
  of measuring the nonlinearity in the hammer compliance… Measurements made for voiced hammers
  from several pianos show a smooth increase from p ' 2 in the bass, to p ' 4 in the treble."
  → **量測者是 Hall & Askenfelt，Russell & Rossing 只是轉述**。
  而引擎 `kPianoHammerAlpha` 的來源（Woodhouse Table 2）**也是轉引 Hall & Askenfelt**，
  所以這**不是兩個獨立來源的對照，是同一組量測的兩次轉引**，原本寫的「在高音差約 1.0」
  只能算「同一組量測在兩份二手文獻裡被轉述成不同的數字」，**證據力比原本弱**。
  Russell & Rossing **自己的** p 量測在別處（Figure 5，13 顆整音槌 + 6 顆硬槌；文中 D2 槌 p = 2.2），
  而且他們自述 "Exponent values agree well with results of Hall and Askenfelt [5, 10]"，
  **沒有給高音端的逐音 p 數字**，因此無法用來當「高音 p 到底是 3.0 還是 4.0」的獨立仲裁。
  α 影響 τc 的力度指數 2/(α+1)−1，因此也會影響高音區的接觸時間律。
  **這不是 A14 的成因**（把 α 從 3.0 改到 4.0 只改變 τc 隨力度的斜率，不會把 x 從 7 拉回 1），
  但它與 B-2 同一個環節，登記為 open item 供 B4 卡回頭覆核；本卡未對此下任何判定。

---

### 3.9 引擎 vs 真鋼琴逐音量測：第2 partial 相對基頻（2026-09-08 第二次複核新增）

這是本卡目前**最直接**的一組對照：同一個物理量（第2 partial 相對基頻的 dB）、
同一組音名（G2–G6，五顆 G）、量測側是消聲室裡的真鋼琴逐音分析（L1-26～L1-29）。
引擎側取 `--dump-modes` 的激發振幅（steel、Ø1.0 mm、velocity 0.45），量法五顆音一致。

| 音 | 基頻（量測／引擎） | **量測 p2−p1** | **引擎 p2−p1** | 差 | 引擎的 x = 2f₁τc |
|---|---|---|---|---|---|
| G2 | 98 / 97.7 Hz | **+1 dB** | +3.2 dB | 2.2 dB ✅ | 0.57 |
| G3 | 193.5 / 195.4 Hz | **+7 dB** | −1.8 dB | 8.8 dB ⚠ | 0.98 |
| G4 | 393 / 390.9 Hz | **−19 dB** | −14.0 dB | 5.0 dB ✅ | 1.69 |
| **G5** | **779 / 781.7 Hz** | **−22 dB** | **+8.2 dB** | **30 dB ❌ 符號相反** | **2.91** |
| **G6** | **1568 / 1563.5 Hz** | **−38 dB** | **+13.5 dB** | **51 dB ❌ 符號相反** | **5.06** |

**（2026-09-08 第三次複核新增）把量測側往低音再延伸兩顆音**，同一台琴、同一次量測、同一張 dB 欄：

| 量測音 | 基頻 | **基頻相對該音最強 partial** | 最強的是第幾 partial |
|---|---|---|---|
| **A0** | 27.5 Hz | **−27 dB**（基頻欄 −23、最強欄 +4） | 第 20 |
| **G1** | 48.6 Hz | **−26 dB** | 第 3 |
| G2 | 98 Hz | −1 dB | 第 2 |
| G3 | 193.5 Hz | −7 dB | 第 2 |
| G4 | 393 Hz | **0 dB（基頻最強）** | 第 1 |
| G5 | 779 Hz | **0 dB** | 第 1 |
| G6 | 1568 Hz | **0 dB** | 第 1 |

**這張表是本卡最乾淨的一條證據**：真鋼琴的基頻由「比最強泛音低 27／26 dB」（A0／G1）
一路爬到「自己就是最強」（G4 以上），**沒有任何一顆音在高音端回頭**。
（嚴格說不是逐音單調：G2 是 −1、G3 回到 −7，中間有一個小凹；
但**整體走向只有一個方向**，而且 A14 的爭點在 G5/G6，那兩顆量測值都是「基頻自己最強」。）
A14 原本的假設（「真鋼琴高音區基頻本來就弱」）在這張表上**沒有立足點**。

**三件事一次看清楚**：

1. **量測側本身就證明了「弱基頻是低音現象」**：G2/G3 的第2 partial 比基頻**強** 1–7 dB，
   到 G4 就翻成基頻強 19 dB，G5 是 22 dB，G6 是 38 dB。
   （G2→G3 這一段是 +1→+7，不是單調；**G3 以上則是單調往「基頻越來越強」走、沒有回頭**。）
2. **引擎在 G2–G4 三顆音上與量測相差只有 2–9 dB**（同一條程式、同一組常數），
   到 G5/G6 突然差 30/51 dB **而且符號相反**。
   物理現象不會在一個八度內轉向；會這樣轉向的是**公式的零點**。
   最後一欄給出轉向點：x 穿過 3（第一個深零點）就在 G4→G5 之間。
3. **引擎在 G3 那一格偏離 8.8 dB 且方向相反**（量測 +7、引擎 −1.8），
   這格**不是** A14 要判的東西，但誠實登記：低音端引擎的第2 partial 偏弱一點。

**次要佐證（同篇，但用法不同，不可與上表混為一談）**：
L1-23 的「每 100 cps 降 2 dB」是該文**合成端**的最佳品質律（評審團判定），不是分析端的量測值。
拿它預測第2 partial 相對基頻（Δf ≈ f₁）得：G4 −7.9、G5 −15.6、G6 −31.4 dB，
**與上表量測欄同號、量級相近（差 7 dB 內）**，與引擎的 +8.2 / +13.5 仍然相反。
兩條互相獨立的線索指向同一個方向。

### 3.10 非諧性 B 與音分：方向對、量級在高音錯 14–87 倍（2026-09-08 第二次複核新增）

L1-27 確認 Fletcher 的非諧性定義與引擎 `StringModel.h:324` **是同一條式子**
（`fₙ = n·f₁·√(1+B n²)`，B 的封閉式也同形），所以 B 值可以逐音直接比。

| 音 | **量測 B**（L1-28/L1-29 及同篇 Table III–V） | **引擎 B**（Ø1.0 mm ／ Ø0.8 mm 預設） | 倍數（1.0 mm） | 量測 f₂ 偏離 2×（cent） | **引擎 f₂ 偏離 2×（cent）** |
|---|---|---|---|---|---|
| G2 | 1.5×10⁻⁴ | 6.8×10⁻⁵ | 0.5× | 0.4 | 0.2 |
| G3 | 5×10⁻⁵ | 2.7×10⁻⁴ ／ 1.7×10⁻⁴ | 5.4× | 0.1 | 0.7 |
| G4 | 4×10⁻⁴ | 1.08×10⁻³ ／ 6.9×10⁻⁴ | 2.7× | 1.0 | 2.8 |
| **G5** | **2×10⁻⁴** | **4.32×10⁻³ ／ 2.77×10⁻³** | **21×**（0.8 mm 時 14×） | 0.5 | **11.1** |
| **G6** | **2×10⁻⁴** | **1.73×10⁻² ／ 1.11×10⁻²** | **87×**（0.8 mm 時 55×） | 0.5 | **43.0** |

**白話**：真鋼琴的高音弦，非諧性其實**很小**（第2 partial 只比整數 2 倍高不到 1 音分）；
本引擎的 G6 高了 **43 音分**——是本專案自己那把 ±5 cent 尺的 **8.6 倍**。

**這一格的意義比看起來大**：A14 原本的猜測是「比值 > 2 與 stiffness inharmonicity 方向一致 → 可能完全正確」。
方向確實一致，**但量級不是**。所以：

- **對 A14 的判定**：不改變（弱基頻的成因是 §3.2 的力脈衝零點，不是 B）。
- **對 C13（harmonic-aware 判定）**：這是**前置警告**——
  C13 若直接拿引擎自己 `--dump-modes` 預測的 partial 頻率當靶，等於用一把**在 G6 偏 43 音分**的尺量自己，
  會自動通過而測不出東西。C13 開卡前應先處理這件事（登記為 open item，非本卡裁決範圍）。
- **同時關閉 §5 缺口 4**：初版說「Young (1952) 逐音 B 值表沒拿到，所以只能粗判」——
  現在有 Fletcher 同篇的逐音 B 值（且與引擎同定義），不再需要 Young。

**邊界**：Fletcher 量的是**一台直立鋼琴**（原文明載 "a good upright piano"）。
直立琴弦較短，非諧性**通常高於**平台琴，所以上表的量測欄若當成「真琴上限」用，
引擎超標的倍數只會更大，不會更小。單一台琴、單一次量測，不能當成全體鋼琴的分佈。

### 3.11 溯源查核：引擎檔頭引用 vs 原文實際內容（2026-09-08 第二次複核新增）

`src/physics/HammerImpulse.h` 檔頭寫：

> 「槌頭接觸弦/梁/板期間，接觸力近似半正弦脈衝（Chaigne & Askenfelt 1994, JASA 95(2),
> "Numerical simulations of piano strings I"；該文以力-時間曲線半高寬定義接觸時間 tau_c…）」

本輪取得該文全文後逐段核對，結果如下（**這是溯源查核，不是對 A14 的物理判定**）：

| 檔頭的主張 | 原文實際內容 | 判定 |
|---|---|---|
| 「接觸力近似半正弦脈衝」 | 原文的力是**非線性冪次律動態解**：`F=K·|y|^p`（L1-30），全文未出現半正弦力脈衝模型 | **原文沒有這句** |
| 「該文以力-時間曲線半高寬定義接觸時間 tau_c」 | 原文的接觸時間是**互動過程的輸出**："This yields, among other things, the contact duration"（L1-31）；不是由半高寬定義、也不是輸入參數 | **與原文相反** |
| （引申）把 τc 當成先給定的已知量 | 原文明文把這個作法列為 1970 年代 Hiller & Ruiz 舊模型的缺點："was set beforehand as a known parameter"（L1-32） | **原文批評的正是這個作法** |

**半正弦力脈衝這個模型本身是有出處的**——Woodhouse《Euphonics》2.2.6（L1-9）確實寫
"a half-cycle of a cosine wave"，而且 §12.1.2（L1-10）說它的作用是**低通濾波**。
所以問題不是「半正弦是憑空捏造」，而是**檔頭把它掛在一篇沒有這樣寫、而且立場相反的論文底下**。

另有一條獨立佐證，指出半正弦對應的是**線性**槌：
Russell & Rossing 用聚氨酯彈性體做的**實驗用線性槌**，其力脈衝
"very closely approximated by a half-sine pulse, indicating a linear behavior"，
而且該槌 "the pulse duration remained essentially constant over the velocity range"；
真鋼琴氈槌則全部 "the pulse duration decreased with increasing velocity"。
**換句話說：半正弦力脈衝 = 線性槌的行為，鋼琴氈槌不是線性的（p ≈ 2–4，L1 補充數字）。**

**這一節的用途與界線**：
(a) 它**不改變** A14 的判定（判定的證據是 §3.9 的量測對照與 §3.2 的零點拆解，不依賴這一節）；
(b) 它是 **R4 溯源問題**，屬於文件/註解層，修正方式是改註解、不是改數值——
    但依規約「不改 `src/`」，本卡只登記，**列為 open item 交給 B-1/B-2 施工卡順手更正檔頭引用**；
(c) 不得因此推論「引擎其他常數也不可信」——本輪只查了這一段檔頭。

## §4 選項與建議（給月月看的白話版）

### 三個選項

**選項 A —— 判「物理正確」，關掉 A14，C13 改用「看泛音」的判定法**
- 意思：承認「真鋼琴高音基頻本來就弱」，不改引擎，只改驗證工具的判斷方式。
- **不建議**。理由：
  1. 弱基頻在真鋼琴是**低音**的現象，高音區文獻說的是**反過來**。
     **2026-09-08 起這一條有 L1 量測撐著，不再只靠業界媒體**：
     L1-16「最高兩個八度基頻**完全支配**頻譜」、L1-17「A0 基頻比最強泛音低達 25 dB」、
     L1-22「高音區 f_max 落在基頻附近」、以及「高音槌強烈激發基頻、只弱激發一兩個泛音」。
     舊有的 L2-1／L2-2（Sound On Sound）現在只是佐證，不再是唯一依據。
  2. G5 是 784 Hz，不是「最頂端幾個音」。社群講的「像敲木頭」是最頂端一個八度、而且被當成琴需要調整的問題（L3-1/L3-2）。
  3. 引擎的頻譜是「梳齒狀忽大忽小」（§3.6），這是公式零點造成的人工痕跡，不是任何真琴的樣子。
  4. 如果選 A，等於把一個可證明的建模錯誤寫進「已驗證」的範圍——違反本專案「不宣稱未量測的東西」的原則。

**選項 B —— 判「引擎缺陷」，立 Rule 10 施工卡（建議）**
- 意思：承認高音區的聲音是算錯的，開一張正式的修改卡，修完必須做前後對照報告給月月裁決。
- 要改的環節，**按優先序**：
  - **B-1（必要）槌頭力脈衝在 x > 1 之後不該保留深零點。**
    根因是把「只在接觸時間短於半週期時成立」的半正弦自由脈衝公式，外插到接觸時間是半週期 7 倍的高音區。
    文獻（L1-7、L1-8）明確說真槌的力波形因為弦端反射波回來而完全不同。
    **2026-09-08 更新——這一項的資料狀態變了**：
    現在有 L1-16～L1-22（Russell & Rossing 1998，全文開放）給出**真槌有效激發頻帶 f_max 的逐音量測**
    （`f_max = a·v^b`，a 從 A0 的 763 Hz 升到 F7 的 1307 Hz；A0 與 F7 兩顆槌的實測點見 §2），
    而且 §3.7 已經把引擎換算到**同一個定義**下直接比出來：引擎的交叉點差了約三個八度、F7 差 4–9 倍。
    → **「要往哪個方向改、改多少量級」現在有可引用的靶了。**
    **但仍然不足以直接寫死一條替代曲線**，因為：
    (a) 該量測是槌打**剛性感測器**、不是打弦，作者自列三個外推限制（L1-20/L1-21 + 槌柄振動）；
    (b) 引擎 velocity 是 0–1 正規化 proxy、不是 m/s，速度軸無法逐點對齊；
    (c) 「滾降斜率（dB/oct）」本身仍然沒有可存取的原文（Hall & Askenfelt 1988 仍在付費牆後）。
    → **建議**：B-1 施工卡把 f_max 當成**驗收指標**（改完要求高音區 f_max/f₀ 落回 O(1)），
    而不是當成寫進程式的常數；替代曲線的具體形式仍須先補 §5 缺口 2。
    **2026-09-08 第二次複核再更新——驗收靶從「只有方向」升級為「有逐音數字」**：
    Fletcher, Blackham & Stratton (1962) 全文已取得（L1-23～L1-29），
    給出真鋼琴 **G4/G5/G6 逐音的第2 partial 相對基頻 dB 值（−19／−22／−38）**，
    正好覆蓋 A14 卡上的兩顆音，而且是**輸出頻譜**這一層——
    也就是 GATE 真正量得到的那一層，不需要再把力譜形狀反推出來。
    → **B-1 的驗收條件因此可以寫成可量測的數字，而不是只寫「零點要消失」。**
    **但「用什麼形狀取代半正弦」這個問題仍然沒有答案**：
    (c) 那一條（力譜滾降 dB/oct 的原文）**維持未取得**，Hall & Askenfelt 1988 本輪第三次嘗試仍 403。
    另補一條反向證據（Russell & Rossing）：半正弦力脈衝對應的是**線性槌**
    （聚氨酯實驗槌 "indicating a linear behavior"、脈衝長度不隨速度變），
    真鋼琴氈槌是非線性的（p ≈ 2–4），脈衝長度隨速度縮短。**所以替代形狀不會是另一條固定波形，
    而應該是「接觸時間隨力度變」的那一族**——這正是 B-2 已經在做的事，兩項有交集。
  - **B-2（必要）τc 的音高律修到文獻範圍。**
    現行 B4 求解器全音域只從 3.26 ms 走到 1.46 ms（等效 k = 0.212），文獻 L1-1 是 4 ms → <1 ms（k ≈ 0.276）。
    這一項有明確的文獻靶（L1-1、L1-4），可以直接做。
    **注意**：B4（2026-08-27）在這一項上比 B4 之前的 k = 0.32 還退步，這件事本身值得回頭看 B4 卡。
  - **B-3（不要單獨做）響度補償 clamp 從 MIDI 67 就飽和。**
    不要去調 ±12 dB 這個 clamp——那是掩蓋症狀，而且 R2 明文禁止調寬容差。
    B-1/B-2 修好之後 noteComp 會自己退出飽和；**修完要回頭量一次確認它不再頂到上限**。
- **Rule 10 影響範圍（已實際掃過 83 個 score 檔）**：
  - `pianoHammerTauC()` 只在 Cimbalom/Piano 路徑的 Felt 檔位被呼叫，受影響的 score 檔只有 **5 個**：
    `scores/classical/fur_elise/fur_elise_complete.score.json`（905 事件全是 piano）、
    `scores/examples/physical_piano.score.json`、
    `scores/library/akashic/akashic_action_001.score.json`、
    `scores/library/ocean/ocean_action_001.score.json`、
    `scores/originals/ai_radiance/ai_radiance_m3.score.json`。
  - B6 位元不變 8 首代表曲裡，**只有 `physical_piano.score.json` 會變**，其餘 7 首應維持 IDENTICAL
    ——這剛好可以當成「改動有沒有外溢」的檢查。
  - **但若 B-1 去動共用的 `forceSpectrumMagnitude()` 或 `keytrackScale()`，影響範圍會炸開到全部樂器**
    （cimbalom 3300+ 事件、string 28000+ 事件、tongue_drum、water_gong…）。
    **施工卡必須明文要求改動範圍收在 Felt/piano 路徑內，或另外做全 corpus 前後對照。**

**選項 C —— 分開處理（比值歸比值、電平歸電平）**
- 實測結論是：**比值與電平是同一個根因**（都是 H(f, τc)），拆開處理沒有意義。
  唯一真的可以拆出來的是 §3.8 那兩項（G6 的 B 偏高、擊弦點固定 0.125），它們**不是** A14 的成因。
- 所以 C 實質上會退化成 B，**不建議**單獨走 C。

### 我的建議

**選 B**，並且分兩段走：

1. **先做 B-2（τc 音高律）**——文獻靶明確、可立刻施工、影響範圍只有 5 個 score 檔。
   做完先量一次：G5 的 x 會從 2.910 降到多少、基頻壓抑改善多少、MIDI 37→87 斜率剩多少。
2. **B-1 仍然先不要動手改公式**，但**可以先立卡並寫驗收指標**（2026-09-08 修正建議）。
   可以先定下的驗收條件（全部有 L1 依據、不需要新常數）。
   **每條下面那行「白話」是給月月核准用的，不看術語也能判斷改對了沒**：
   - 高音區（MIDI ≥ 79）**第一泛音不得高於基頻**（L1-16、L1-22）；
     **白話**：G5 以上每顆音，「這顆音的音高本身」要是最大聲的那一根，
     不可以像現在這樣被上面那一根泛音蓋過去。真鋼琴量測就是這樣（G4/G5/G6 三顆都是基頻最強）。
   - 引擎等效 f_max/f₀ 在高音區要落回 **O(1)**，不是現在的 0.1–0.2（§3.7）；
     **白話**：把槌子想成一支「刷子」，f_max 是它刷得最用力的那個頻率。
     真鋼琴的高音槌，刷得最用力的地方**剛好落在那顆音的音高附近**（比值大約 1）。
     現在引擎的槌子刷在**只有音高十分之一的地方**（比值 0.1–0.2），
     等於用低音的刷子去刷高音弦——所以那顆音高本身沒被刷起來。改完這個比值要回到「大約 1」。
   - 全鍵盤梳齒式非單調（§3.6）必須消失；
     **白話**：現在從最低音一路彈到最高音，音量是**忽大忽小、像鋸齒一樣跳**的
     （不是平滑地變小）。這種鋸齒是公式踩到零點造成的計算痕跡，真鋼琴不會這樣。
     改完後把整個鍵盤同力度掃一遍，音量曲線要是平順的，不可以再出現忽大忽小。
   - **（2026-09-08 第二次複核新增，有逐音量測靶）** 第2 partial 相對基頻，
     G4 應在 −19 dB 附近、G5 −22 dB、G6 −38 dB（L1-28/L1-29 的真琴量測值），
     現況是 −14.0 / **+8.2** / **+13.5**。
     **白話**：這一行是「第二根泛音比音高本身弱幾 dB」。真鋼琴量出來是弱 19／22／38 dB
     （負號＝比較弱），數字越負代表音高本身越突出。引擎的 G5、G6 是**正號**，
     代表泛音反而比音高本身還大聲——這就是月月聽不到、也是 A14 這張卡在吵的那件事。
     **這組數字只能當「改對了沒有」的參考靶，不得由工程端逕自定成 GATE 容差（R2）**——
     要不要立成 GATE、容差多少，是 A13 主張域那張卡要月月裁決的事。
   - **（2026-09-08 第三次複核新增，量測規約）** 上面那條靶**必須用 `--dump-modes` 的振幅欄量**，
     不要用渲染後的 FFT 量。
     **白話**：同一顆音有兩種「量音量」的方式。一種是叫引擎直接印出它自己算出來的每根泛音強度
     （`--dump-modes`），這個數字每次跑都一模一樣；另一種是把聲音檔渲染出來再用頻譜分析軟體去量，
     這個會因為分析設定不同而差最多約 6.5 dB。驗收要用前者，否則「有沒有改好」會被量法誤差淹掉。理由：第三次複核用另一支自寫 FFT 腳本重量，
     方向與符號全部一致，但 G6 那一格差到 **3.4 dB**（窗寬／FFT 長度一動，
     零點鄰域取到的峰就換；且非諧使第2 partial 不落在整數 2f₁ 上）。
     **2026-09-08 複核更新**：再加第三支獨立腳本後，最大偏差出現在 **D7＝6.5 dB**（其次 C4 4.5 dB、G6 3.6 dB），
     所以這個量法自由度要按 **最大約 6.5 dB** 估，不是原先寫的 ±3 dB。
     `--dump-modes` 那一欄沒有這個自由度、逐位可重現（附錄 E.1）。
     **B-1 施工卡請把這條寫進量測方法，否則「改好了沒」會被量法本身最大約 6.5 dB 的噪音蓋掉。**
   替代曲線的**具體形式**仍要等 §5 缺口 2 的原文；在那之前任何「把零點填平」的寫法
   都是憑空造常數（R4）。如果最後真的找不到可引用的原文，就誠實寫「未溯源」，
   把「用什麼形狀取代半正弦」這一個子問題掛回 A 類等月月裁決——
   但**「現況是錯的」這個判定本身已經不需要再等任何文獻**。

**A14 本身的判定文字建議寫成**（2026-09-08 第二次複核修訂版，判定不變、依據更硬、
並把「比值」那一句從「一致」修正為「方向一致但量級不對」）：

> 部分合理。「比值 > 2」的**方向**與 stiffness inharmonicity 一致、「高音區泛音少」與文獻一致；
> **但**「G5/G6 基頻比第二泛音弱 8～13 dB」與「MIDI 69→80 電平掉 15.6 dB」判定為**引擎缺陷**，
> 根因為半正弦力脈衝模型被外插到接觸時間 ≫ 基頻半週期的區域（x = 2·f·τc 高達 7.1），
> 且 τc 的音高律比文獻平（k = 0.212 vs ≈0.276）。
> 判定依據為真鋼琴逐音量測（Fletcher, Blackham & Stratton 1962, JASA 34(6) 749–761）：
> 同樣是第2 partial 相對基頻，量測值 G4 −19 / G5 −22 / G6 −38 dB，
> 本引擎 −14.0 / **+8.2** / **+13.5** dB——**G2–G4 相差 2–9 dB（對得上），G5/G6 相差 30/51 dB 且符號相反**。
> 另登記（不在 A14 判定範圍、但由同一批量測發現）：引擎的非諧性 B 在高音區偏高 14–87 倍，
> G6 的第2 partial 比真琴量測偏高 **43 音分**，會影響 C13 的靶。

---

## §5 已知缺口（誠實登記）

1. **「同力度下 C7 vs C4 的 SPL 差（dB）」這個數字，本輪沒查到可引用的原文。**
   Meyer《Acoustics and the Performance of Music》的音域 SPL 表找不到可存取版本；
   KTH 五講與 Euphonics 都沒有給這個數字。
   → 因此本報告**不敢說「真鋼琴 A4→G5 應該只掉 X dB」**，
   只能用**引擎自己的對照組**（§3.5：同引擎換 τc 後斜率從 22 dB 變 2 dB）與
   **非單調梳齒**（§3.6）來論證這是缺陷。這兩條論證不依賴那個缺失的數字，但補上會更硬。

2. **真實鋼琴槌力脈衝的頻譜滾降形狀（dB/oct）仍然沒拿到原文——但缺口縮小了一半。**
   - **已補上的一半（2026-09-08）**：Russell & Rossing (1998) 全文開放，給出力脈衝的**實測波形**
     （硬 A3 槌 4 m/s：最大力 183 N、半寬 0.24 ms，與 half-sine／sine-squared／skewed versed-sine
     三種形狀比對）與**有效激發帶 f_max 的逐音量測**。這足以判斷「引擎往哪個方向錯、錯幾倍」（§3.7）。
   - **（2026-09-08 第二次複核）缺口再縮小，但沒有關閉**：
     現在有了**輸出端**的逐音靶（Fletcher 的 partial 電平表，見缺口 3），
     所以「改對了沒有」可以量；但**力脈衝本身該長什麼形狀**仍然沒有原文。
     新增一條可引用的**反向界定**（Russell & Rossing）：
     半正弦力脈衝對應的是線性槌（"indicating a linear behavior"、脈衝長度不隨速度變），
     真鋼琴氈槌是非線性的（p ≈ 2–4）、脈衝長度隨速度縮短。
     這**排除掉**「換另一條固定波形」這個解法，但沒有指定該換成什麼。
   - **仍然缺的一半**：可以直接寫成程式的**滾降斜率（dB/oct）**。
     Hall & Askenfelt (1988)《Piano string excitation V: Spectra for real hammers and strings》,
     *JASA* **83**(4), 1627–1638（DOI 10.1121/1.395917）正是講這個，
     但 pubs.aip.org 目標頁回 **HTTP 403**，2026-09-08 再試仍 403。
     **（第三次複核追加，第四次嘗試）** 本輪改走**直接 PDF 路徑**
     `pubs.aip.org/asa/jasa/article-pdf/83/4/1627/11775670/1627_1_online.pdf`
     （不是先前用的摘要頁），仍回 **403，且內容是 Cloudflare 的 "Just a moment..." 挑戰頁**。
     → 這代表它是**機器人挑戰**、不是單純付費牆或壞連結；換 User-Agent 無效。
     以本環境的工具**判定為取不到**，不再重試；要拿到只能靠館際/機構帳號（月月決定要不要花這個力氣）。
     Chaigne & Askenfelt (1994) **Part I 已於 2026-09-08 取得**（Kent State 鏡像，見 L1-30～L1-32），
     但 Part I 只有數值方法、沒有滾降數字；**Part II（逐音參數表）仍在付費牆後**。
   → **B-1「改成什麼形狀」開工前仍須先補這一篇**，否則替代曲線會變成未溯源常數（違反 R4）。
   可嘗試管道：作者自存版、機構庫、ResearchGate 全文、圖書館館際；或改用
   Woodhouse《Euphonics》12.2 的模擬力波形圖（若能取得可引用的數值）。

3. ~~**「真鋼琴高音區基頻 vs 第二 partial」只有 L2 業界媒體撐著。**~~
   **2026-09-08：這個缺口已關閉。** Russell & Rossing (1998) 是 L1 量測報告，明文寫
   "In the upper two octaves, the fundamentals completely dominate the sound spectra"、
   "a treble hammer would strongly excite the fundamental, but weakly excite only one or two harmonics"，
   方向與本引擎（第二泛音高於基頻 7–8 dB）相反。**判定不再依賴 Sound On Sound。**
   - ~~**殘留**：仍然沒有拿到逐 partial 的 dB 數值表。~~
     **2026-09-08 第二次複核：殘留部分也關閉了。**
     Fletcher, Blackham & Stratton (1962)《Quality of Piano Tones》, *JASA* **34**(6), 749–761
     **全文已取得**——AIP 頁仍 403，但 **BYU 機構庫**（Fletcher 的任職單位）有公開 PDF：
     https://physics.byu.edu/download/publication/1504（存取 2026-09-08）。
     該文含消聲室逐音量測的 partial 電平表，**涵蓋 A14 卡上的 G5 與 G6**（Table VI/VII）。
     初版存疑的「partials 每增加 100 cps 下降 2 dB」也在原文摘要與正文 §「(4)」逐字核實，
     **本輪起採用**（用法邊界見 L1-23 與 §3.9 末段：那是合成端的最佳品質律，不是分析端量測值）。
     → 「高音第二泛音應比基頻低幾 dB」這個精確靶**現在有了**：G5 −22 dB、G6 −38 dB。

4. ~~**Young (1952) 逐音 B 值表沒拿到**（PTG 鏡像重導向失敗、afn.org DNS 已不存在）。~~
   **2026-09-08 第二次複核：這個缺口以另一條路關閉。** 不再需要 Young——
   Fletcher 同篇每一張 partial 表的標題就直接給了該音的 **B 值**（L1-27～L1-29），
   而且用的是與引擎 `StringModel.h:324` **相同的定義**，可以逐音直接比（§3.10）。
   結果：引擎在 G5/G6 的 B 高出量測 **14–87 倍**，G6 的第2 partial 偏高 43 音分。
   **仍未取得**的是 Young (1952) 那種涵蓋全 88 鍵的 B 值表；
   **（2026-09-08 第三次複核更正）** 初版與第二輪都寫「Fletcher 只給五顆 G 加一顆 A0」，
   **這是錯的**：該文逐音表共 **七顆音**——A0（27.5 Hz, B=0.00053）、**G1（48.6 Hz, B=0.00028）**、
   G2（98, 0.00015）、G3（193.5, 0.00005）、G4（393, 0.0004）、G5（779, 0.0002）、G6（1568, 0.0002）。
   漏掉的 G1 已補進 §2 的 L1-33 與 §3.9。
   即使如此，樣本仍是**單一台直立琴、七顆音**，
   所以「弦長模型該怎麼改」仍然不足以定案（那是 open item，不是 A14 判定項）。

5. **Reddit 在本執行環境是「永久封鎖」，不是暫時抓取失敗**（2026-09-08 第三次複核查清）。
   三條路徑都試過：`www.reddit.com/...json` 回 **HTTP 403「Blocked」**；
   `old.reddit.com/...json` 回 **200 但內容是登入牆頁面**（"Welcome to Reddit"）；
   `WebSearch` 限定 `reddit.com` 直接被工具拒絕，訊息為
   "The following domains are not accessible to our user agent: ['reddit.com']"。
   → **這條缺口在本環境內無法靠重試關閉**，除非月月自己去 r/piano 取資料。
   替代做法：本輪已改用 **Pianoteq 官方論壇**補足卡上 §1-C 要的那一項（L3-4～L3-6），
   社群證據現在有 Piano World（2004）一串 + Pianoteq 三串（2015/2016/2017），皆無公開讚數。

6. **本卡沒有做實體鋼琴量測。** 若月月希望完全排除爭議，
   最小可行的實體量測是：同一台真鋼琴、同一力度彈 C4 / A4 / G5 / G6 / D7，
   量「第1泛音 vs 第2泛音的 dB 差」與「峰值的相對差」。
   有這五組數字就能直接把 §3.1 那張表判死或判活（對應 D7 實體量測流程）。

---

## 附錄 A：來源清單

**存取日期**：第 1–13 項為 2026-09-07（初版）；第 14 項為 **2026-09-08**（修訂新增）。
第 1–13 項於 2026-09-08 全部重新開啟原文複核一次，引述**全數命中**（見附錄 C）。

**L1 物理證據（12 個獨立來源；第 15、16 項為 2026-09-08 第二次複核新增）**
1. Askenfelt & Jansson,《From touch to string vibration — String contact duration and dynamic level》, KTH *Five Lectures on the Acoustics of the Piano*. https://www.speech.kth.se/music/5_lectures/askenflt/stricont.html
2. Askenfelt & Jansson,《Bass, middle and treble》, 同書. https://www.speech.kth.se/music/5_lectures/askenflt/basmidtr.html
3. Donald E. Hall,《The hammer and the string》, 同書. https://www.speech.kth.se/music/5_lectures/hall/hall.html
4. Harold A. Conklin Jr.,《Piano design factors — Where should the hammer hit the string?》, 同書. https://www.speech.kth.se/music/5_lectures/conklin/whereshould.html
5. *Five Lectures on the Acoustics of the Piano* 目錄頁（確認講者與章節）. https://www.speech.kth.se/music/5_lectures/contents.html
6. Jim Woodhouse,《Euphonics》12.2 *Hitting strings: the piano and its relatives*. https://euphonics.org/11-2-hitting-strings-the-piano-and-its-relatives/
7. Jim Woodhouse,《Euphonics》12.1.2 *The maximum bandwidth of a bouncing hammer*. https://euphonics.org/12-1-2-the-maximum-bandwidth-of-a-bouncing-hammer/
8. Jim Woodhouse,《Euphonics》2.2.6 *Frequency spectrum of a hammer tap*. https://euphonics.org/2-2-6-frequency-spectrum-of-a-hammer-tap/
9. X. Gràcia & T. Sanz-Perela (2016),《The wave equation for stiff strings and piano tuning》, arXiv:1603.05516（原文 PDF 已下載並逐字擷取）. https://arxiv.org/pdf/1603.05516

14. **D. Russell & T. Rossing (1998),《Testing the Nonlinearity of Piano Hammers Using Residual Shock Spectra》, *ACUSTICA / acta acustica* 84, 967–975（全文開放 PDF，已下載並逐字擷取；存取 2026-09-08）. https://www.acs.psu.edu/drussell/publications/pianohammer.pdf**
15. **H. Fletcher, E. D. Blackham & R. Stratton (1962),《Quality of Piano Tones》, *JASA* **34**(6), 749–761（BYU 機構庫全文 PDF，已下載並逐字擷取；存取 2026-09-08 第二次複核新增）. https://physics.byu.edu/download/publication/1504**
16. **A. Chaigne & A. Askenfelt (1994),《Numerical simulations of piano strings. I》, *JASA* **95**(2), 1112–1118（Kent State 課程站鏡像全文 PDF，已下載並逐字擷取；存取 2026-09-08 第二次複核新增）. https://www.math.kent.edu/~zheng/62262/piano_wave.pdf**

**L2 業界技術媒體（2 個）**
10. *Sound On Sound*,《Recording Real Pianos》. https://www.soundonsound.com/techniques/recording-real-pianos
11. Timbre and Orchestration Resource,《Keyboard｜Piano Essentials》. https://timbreandorchestration.org/isfee/extreme-orchestration/keyboard/piano

**L3 社群（4 串；第 17、18 項為 2026-09-08 第三次複核新增）**
12. Piano World Forums,《Top Octave on a Piano》, 2004-06-10～12. https://forum.pianoworld.com/ubbthreads.php/ubb/printthread/Board/1/main/23738/type/thread.html
13. Modartt / Pianoteq user forum,《Model B High Notes》, 首帖 2016-05-10. https://forum.modartt.com/viewtopic.php?id=4487
17. **Modartt / Pianoteq user forum,《Brittleness of high notes...》, 2017-10-17（存取 2026-09-08）. https://forum.modartt.com/viewtopic.php?id=5325**
18. **Modartt / Pianoteq user forum,《Four areas for possible improvement》, 2015-03-09（存取 2026-09-08）. https://forum.modartt.com/viewtopic.php?id=3820**

**未取得原文的來源見 §2 末表。**

---

## 附錄 B：引擎數字怎麼重跑

所有暫存檔在 `output\wf0907\R2\`（gitignore）。指令（repo 根目錄）：

```
# 1. 產生診斷 score（單音 + 半音掃描 + 換槌對照）
python output\wf0907\R2\gen_scores.py

# 2. 渲染（用現成 binary，不重建）
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe output\wf0907\R2\a14_single_g5.score.json --output output\wf0907\R2
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --dump-modes output\wf0907\R2\a14_single_g5.score.json

# 3. FFT 分析與掃描斜率
python output\wf0907\R2\analyze.py
python output\wf0907\R2\sweep.py
```

診斷 score 的關鍵設定：`velocity 0.45`、`duration 1.0`、`material steel`、`diameter_mm 1.0`、
reverb/delay/distortion 全 0、`normalize: false`、`bit_depth 24`。

「只換 τc」的對照組是在同一個 `piano` 引擎事件裡明寫
`"strike_position": 0.125, "exciter": "wood"`
（`ScoreRenderer.h` 的 piano 分支只會把 `wood_mallet` 改寫成 `felt`、把 0.3 改寫成 0.125，
明寫 `wood` 與 0.125 都不會被改寫，所以擊弦點與其餘一切維持不變，唯一變數就是 τc）。

§3.2 的逐環節拆解是把 `StringModel::calculateModes()`、`spectralTilt`、
`HammerImpulse::pianoHammerTauC()`、`HammerImpulse::forceSpectrumMagnitude()`
用 Python 重寫一次，與 `--dump-modes` 的 `amp` 欄位對答案（符合到 4–5 位有效數字）。
這同時證明手上的 CLI binary 確實實作了現行原始碼的這條鏈。

---

## 裁決記錄（2026-09-08，規劃者依月月 2026-09-07 委託代決，月月可推翻）

- **判定：選項 B「部分合理，主因是引擎缺陷」**。判定文字採 §4「A14 本身的判定文字建議」原文。
- **B-2 先做（Rule 10 卡）**：`HammerImpulse::pianoHammerTauC()` 的音高律改為錨定在**已溯源的量測接觸時間曲線**
  （本檔既有 `keytrackScale()`：Askenfelt & Jansson A0 4 ms → C8 ~0.8 ms 擬合 k=0.32，A4=2.0 ms），
  力度律保留 B4 的 `g(note,v)/g(note,0.5)` 形狀。**不新增任何常數**（R4）。
  影響 5 個 score 檔；8 首代表曲只有 `physical_piano` 會變。改動落地前必須產出前後對照報告，**由月月做 Rule 10 放行**。
- **B-1 不動**：真槌力譜滾降形狀原文未取得（Hall & Askenfelt 1988 403、Chaigne & Askenfelt Part II 付費牆）；
  拿到前不得填替代曲線。登記 D 類補搜。
- **B-3 不動 clamp**；B-2 完成後量 noteComp 是否退出飽和。
- 落地：WF0908-P2 施工卡（`docs/workcards/WF0908_P2_a14_tauc_rule10.md`）。
- 順帶登記（不在 A14 範圍）：擊弦點固定 0.125、G6 的 B 偏高一個量級（弦長假設）——併入 A13 裁決記錄的「未處理」。

**2026-09-08 第二次獨立複核後的裁決增補（判定本身不變，只增補依據與待辦；月月可推翻）**

- **判定維持選項 B**，且依據升級：從「引擎內部自洽論證 + 業界媒體 + 一篇槌打感測器的量測」
  升級為**真鋼琴逐音 partial 電平量測的直接對照**（Fletcher 1962，涵蓋 G5/G6 本人）。
  §3.9 顯示引擎在 G2–G4 與量測差 2–9 dB、在 G5/G6 差 30/51 dB 且符號相反。
- **B-1 維持不動**（滾降形狀原文仍未取得），但**驗收條件可以先寫死**：
  §4 已補上逐音數字靶（G4 −19 / G5 −22 / G6 −38 dB）。
  **提醒**：這組數字是「參考靶」，**不得由工程端逕自定為 GATE 容差（R2）**，
  要立成 GATE 需走 A13 主張域那張卡由月月裁決。
- **新增待辦（不在 A14 判定範圍，登記給對應的卡）**：
  1. **C13 前置警告**：引擎 G6 的第2 partial 比真琴量測偏高 **43 音分**（§3.10），
     是本專案 ±5 cent 門檻的 8.6 倍。C13 若拿引擎自己的 `--dump-modes` 當靶會自我通過，測不出東西。
  2. **溯源更正（R4，文件層）**：`src/physics/HammerImpulse.h` 檔頭把「半正弦力脈衝」
     掛在 Chaigne & Askenfelt (1994) I 名下，**原文沒有這樣寫、而且立場相反**（§3.11）。
     正確出處應改成 Woodhouse《Euphonics》2.2.6 / 12.1.2。
     本卡不改 `src/`，**請 B-1 或 B-2 施工卡順手更正檔頭引用**（純註解、不動數值）。
  3. **弦長模型**：`StringModel::lengthFromMidiNote()` 每八度減半導致高音 B 偏高 14–87 倍（§3.10）。
     併入既有的 open item，需要全 88 鍵的 B 量測表才能定案（Young 1952 仍未取得）。

**2026-09-08 第三次獨立複核後的裁決增補（判定本身仍不變；月月可推翻）**

- **判定維持選項 B。** 本輪把引擎數字第四次獨立重跑、把 30 餘條引述第三次逐條開原文核對，
  **沒有任何一格翻案**（附錄 E.1、E.2）。
- **依據再硬一階**：新增 L1-33（Fletcher 同篇的 A0／G1 兩表，基頻比該音最強 partial 低 27／26 dB），
  使「弱基頻是低音現象」**完全在同一台琴、同一次量測內**從 A0 走到 G6，
  不再需要跨論文拼接（先前這一步是借 Russell & Rossing 的 A0 數字）。
- **新增待辦（量測方法層，交給 B-1 施工卡）**：驗收靶一律用 `--dump-modes` 振幅欄，
  **不得用渲染 FFT**——後者在高音零點鄰域有**最大約 6.5 dB** 的量法自由度
  （2026-09-08 複核更正，原寫 ±3 dB；附錄 E.1 末段、§4 已補進驗收條件）。
- **兩個缺口確認關不掉，且已知原因**：
  Hall & Askenfelt (1988) 第四次嘗試（改直接 PDF 路徑）仍被 Cloudflare 挑戰擋下；
  Reddit 為本環境**永久封鎖**（已改用 Pianoteq 論壇補足卡上 §1-C，見 L3-4～L3-6）。
  **B-1「換成什麼形狀」維持不動**。
- **文件更正一處**（附錄 E.3）：§5 缺口 4 的「Fletcher 只給五顆 G 加一顆 A0」是錯的，實際七顆音，已更正。

---

## 附錄 C：2026-09-08 獨立複核紀錄

複核者：Opus（WF0907-R2 重跑），環境同初版（Windows、`python`、現成 CLI binary，未重建、未改 `src/` `tools/`）。

### C.1 引擎數字（全部重跑，逐格比對）

| 項目 | 初版數字 | 複核重跑 | 結果 |
|---|---|---|---|
| §3.1 五音 FFT（peak dBFS／主導頻率／比值／第2−第1 dB） | 見 §3.1 表 | `python output\wf0907\R2\analyze.py` | **20 格全部逐位一致** |
| §3.5 piano 掃描 MIDI 37→87 | peak −22.10／rms −27.46 dB | 同腳本重跑 | **一致** |
| §3.5 cimbalom 對照 | peak −2.01／rms −3.74 dB | 重算 | **一致** |
| §3.5 piano+wood 對照 | peak −2.16／rms −4.48 dB | 重算 | **一致** |
| §3.3 τc 逐音（A0/C4/A4/G5/G6/D7/C8） | 3.26／2.354／2.097／1.856／1.615／1.515／1.46 ms | 由 `HammerImpulse.h` 公式以 float64 獨立重寫 | **一致** |
| §3.3 x = 2·f·τc | 1.231／1.845／2.910／5.063／7.120 | 同上 | **一致** |
| §3.3 等效 k（C2→C7） | 0.212 | 同上 | **一致（0.2116）** |
| §3.3 H(f₁) 一欄 | −33.67／−50.13／−50.00 dB | float64：−34.50／−47.91／−48.44 dB | **差 0.8–2.2 dB**，零點鄰域精度效應，見 §3.3 註記；不影響結論 |

原始碼側複核：`src/physics/HammerImpulse.h` 的 `forceSpectrumMagnitude()` 確為
`|cos(ωτc/2)| / |1 − (ωτc/π)²|`（與 §3.2 所寫一致）、`keytrackScale()` 確為 k = 0.32、
`pianoHammerTauC()` 確為 `kTauCFelt · g(note,v)/g(69,0.5)` 且 `kTauCFelt = 0.0020`。
§3.2 對程式鏈的描述**與原始碼相符**。

### C.2 引用複核（依鐵律 1，逐條重開原文）

| 條目 | 結果 |
|---|---|
| L1-1、L1-2、L1-3（KTH stricont） | **命中**，原文並給出更完整句："the contact durations decrease from about 4 ms in the bass to less than 1 ms in the highest treble." |
| L1-4、L1-5、L1-6（KTH hall） | **命中** |
| L1-7、L1-8（Euphonics 12.2） | **命中**，完整句："The force then ramps downwards, before it jumps up again when the first reflected pulse arrives back from the nearer end of the string." |
| L1-11、L1-12、L1-13（KTH conklin） | **命中** |
| L1-14（KTH basmidtr） | **命中** |
| L1-15（arXiv 1603.05516） | **命中**（PDF 全文擷取，abs 頁無此句、須用 PDF） |
| L2-1、L2-2（Sound On Sound） | **命中**；L2-2 原文全句為 "The first partial above the top C is typically 20dB below its fundamental, producing an almost sinusoidal sound wave at these upper reaches." |
| L2-3（Timbre & Orchestration） | **命中** |
| L3-1、L3-2（Piano World 2004） | **命中**（Jeffrey 06/10/04、Axtremus 06/11/04） |
| L3-3（Modartt 2016） | **命中**（Alex Cremers，14-05-2016 09:46） |
| **結論** | **13 條全數命中，未發現引用不實。** |

### C.3 本輪新查但**未取得**的來源（誠實登記）

> **附錄 C 是第一輪（2026-09-08 上午）的紀錄，保留原樣不修改。**
> 下面兩條的狀態已被**第二輪**改變，最新狀態見附錄 D.2：
> Fletcher (1962) 與 Chaigne & Askenfelt (1994) I **已取得全文**。

- Hall & Askenfelt (1988) JASA 83(4) 1627–1638：pubs.aip.org **403**。（第二輪再試仍 403）
- Fletcher, Blackham & Stratton (1962) JASA 34(6) 749–761：摘要頁 **403**。
  搜尋摘要提及的「每 100 cps 降 2 dB」**未核實、不採用**。
  → **此條已於第二輪推翻**：改走 BYU 機構庫取得全文並逐字核實，該數字**本輪起採用**（見 D.2）。
- Meyer《Acoustics and the Performance of Music》音域 SPL 表：**仍查不到**（§5 缺口 1 維持開啟）。
- Stulov (2003) 槌別弦振頻譜：只見索引頁，**未取得全文**。
- Reddit（reddit.com／old.reddit.com）：本執行環境 2026-09-08 再試，**仍回 unable to fetch**（§5 缺口 5 維持）。

### C.4 §3.7 對照表的重算指令

```
# 引擎等效 f_max：對 f·H(f, tau_c) 於 1 Hz–12 kHz 取極大
# tau_c 由 HammerImpulse::pianoHammerTauC() 的公式以 Python 重寫（見 C.1）
```
該計算完全在複核者的暫存腳本內完成，未寫入 repo，也未改動任何 `src/` `tools/` 檔案。
量測側數字全部取自附錄 A 第 14 項的開放 PDF（Table I、Fig. 7、Fig. 9 與正文）。

---

## 附錄 D：2026-09-08 第二次獨立複核紀錄

複核者：Opus（WF0907-R2 再次重跑），環境同前（Windows、`python`、現成 CLI binary
`build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe`，**未重建、未對 `build\` 跑 cmake**、
未改任何 `src/` `tools/` 檔案）。暫存輸出在 `output\wf0907\R2\verify2\`（已 gitignore）。

### D.1 引擎數字：重新渲染 + 重新分析（不是重跑前一輪的腳本）

本輪**重新呼叫 CLI 渲染**五顆單音與三組掃描，並用**另寫的**分析腳本（獨立實作 24-bit 讀檔、
Hann 窗 FFT、band-peak 搜尋）計算，不沿用 `output\wf0907\R2\analyze.py`。

| 項目 | 報告記載 | 本輪重跑 | 結果 |
|---|---|---|---|
| §3.1 C4 峰值／主導頻率／比值／p2−p1 | −26.67／260.3 Hz／0.9951／−8.77 | 同 | **一致** |
| §3.1 A4 | −27.58／442.0／1.0046／−8.72 | 同 | **一致** |
| §3.1 G5 | −42.63／1582.7／2.0188／**+7.41** | 同 | **一致** |
| §3.1 G6 | −53.30／3205.5／2.0443／**+8.23** | 同 | **一致** |
| §3.1 D7 | −60.41／2356.1／1.0029／−17.14 | 同 | **一致** |
| §3.5 piano 掃描 37→87 | peak −22.10／rms −27.46／極差 30.47 | 同 | **一致** |
| §3.5 cimbalom | peak −2.01／rms −3.74／極差 5.70 | 同 | **一致** |
| §3.5 piano+wood | peak −2.16／rms −4.48／極差 6.41 | 同 | **一致** |
| **渲染重現性** | — | 重新渲染的 8 個 WAV 與前一輪逐檔比 SHA256 | **8/8 IDENTICAL** |
| §3.3 τc（A0/C4/A4/G5/G6/D7/C8） | 3.2623／2.3535／2.0967／1.8560／1.6146／1.5154／1.4581 ms | 由 `HammerImpulse.h` 公式以 Python float64 第三次獨立重寫 | **一致** |
| §3.3 x = 2f₁τc | 1.2315／1.8451／**2.9101**／**5.0632**／**7.1204** | 同 | **一致** |
| §3.3 等效 k（C2→C7） | 0.2116 | 同 | **一致** |
| §3.7 引擎等效 f_max（A0／F7／D7／C8） | 152–275／304–645／301–638／313–663 Hz | 同 | **一致** |
| §3.2 dump 逐 partial（C4/A4/G5/G6/D7 的 p2−p1） | −8.05／−10.03／**+8.24**／**+13.47**／−19.66 | `--dump-modes` 重取 | **一致** |

**唯一與報告不同的一格（已在 §3.3 註記，本輪確認為量法差異、非錯誤）**：
§3.3 的第 6 欄（**2026-09-08 複核已把欄名由 `H(2f₁)` 改為 `H(f₂ 實際)`**，因為舊欄名與欄內取值定義不符）
是在**實際非諧 partial 頻率**上取值（D7 的 f₂/f₁ = 2.109），
本輪若改用**整數 2f₁** 取值會得到不同的 dB（D7：−46.7 而非 −74.8）。
兩者都對，差別只在「第二 partial 的頻率取哪一個」；在零點鄰域這個差異會被放大到數十 dB，
**這件事本身就是「基頻／泛音正踩在零點上」的旁證**。引用該欄時務必說明取值定義。

### D.2 新取得的原文（本輪最主要的貢獻）

| 來源 | 前一輪狀態 | 本輪結果 |
|---|---|---|
| Fletcher, Blackham & Stratton (1962), *JASA* 34(6) 749–761 | 未取得（AIP 403） | **已取得全文**（BYU 機構庫 PDF）→ L1-23～L1-29、§3.9、§3.10；關閉 §5 缺口 3 殘留與缺口 4 |
| Chaigne & Askenfelt (1994) Part I, *JASA* 95(2) 1112–1118 | 未取得（付費牆） | **已取得全文**（Kent State 鏡像 PDF）→ L1-30～L1-32、§3.11 |
| Hall & Askenfelt (1988), *JASA* 83(4) 1627–1638 | 403 | **仍 403**（第三次嘗試）；作者自存版、機構庫、Russell 的參考書目頁皆無全文連結 |
| Chaigne & Askenfelt (1994) Part II | 付費牆 | **仍未取得** |
| Meyer《Acoustics and the Performance of Music》音域 SPL 表 | 查不到 | **仍查不到**（本輪另試「radiation efficiency / 同力度跨音域 dB」等切入角，只找到定性描述）→ §5 缺口 1 維持開啟 |
| Young (1952) 逐音 B 值表 | 未取得 | **仍未取得**，但已由 Fletcher 同篇的逐音 B 值取代其在本卡的用途 |
| Stulov (2003) | 只見索引頁 | **仍未取得全文** |
| Reddit | 抓不到 | **本輪未再嘗試**（§5 缺口 5 維持） |

### D.3 引用複核（本輪新來源逐條開原文核對）

| 條目 | 結果 |
|---|---|
| L1-16～L1-22（Russell & Rossing） | **7 條全部在 PDF 文字層命中**（本輪以 pypdf 抽全文後逐字 grep，非依賴摘要） |
| Russell & Rossing Table I（a、b 逐音值） | **命中**，並**發現前一輪兩處描述不精確**：a 非單調（低音端有凹陷）、D7 有逐音值（初版寫「未給」）→ 已於 §2、§3.7 更正 |
| L1-23～L1-29（Fletcher 1962） | **全部命中**（摘要 + Table III–VII 數字列） |
| L1-30～L1-32（Chaigne & Askenfelt I） | **全部命中** |
| 前一輪已核的 L1-1～L1-15、L2、L3 | 本輪抽驗 L1-1／L1-2（KTH stricont）**再次命中**；其餘沿用附錄 C 的複核結果，未重複開啟 |
| **結論** | **未發現引用不實**；發現並更正 3 處數值／描述誤差（皆已在正文標明「2026-09-08 第二次複核更正」） |

### D.4 本輪自行發現並更正的三處誤差（誠實登記）

1. **§3.8 的 B 值**：初版由 f₂/f₁ 反推 B 時用了係數錯誤的線性近似（`≈2(1+2B)`），
   正確式是 `2√((1+4B)/(1+B))`。G5 B 由 3.2×10⁻³ 更正為 **4.32×10⁻³**（1.0 mm）。
2. **§2 對 Russell & Rossing Table I 的描述**：「a 單調上升」→ 實際非單調。
3. **§3.7 的 D7 列**：「未逐音給值」→ Table I **有** D7（a=1261.9、b=0.64）。

三處都**不改變任何結論**，但依鐵律必須登記。

### D.5 本輪的重跑指令

```
# 重新渲染（用現成 binary，不重建；輸出到 verify2，不覆蓋前一輪）
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe output\wf0907\R2\a14_single_g5.score.json --output output\wf0907\R2\verify2
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --dump-modes output\wf0907\R2\a14_single_g5.score.json
# 分析腳本與 τc/f_max 重算腳本在複核者的暫存目錄內，未寫入 repo。
# PDF 全文以 pypdf 抽文字層後逐字 grep 核對引述，抽出的 .txt 亦僅存於暫存目錄。
```

**本輪未新增、未修改任何 `src/` `tools/` `scores/` 檔案；未執行 git commit / push / checkout /
stash / reset；未對 `build\` 執行 cmake。** 新產生的檔案只有
`output\wf0907\R2\verify2\`（gitignore）與本檔的修訂。

---

## 附錄 E：2026-09-08 第三次獨立複核紀錄

複核者：Opus（WF0907-R2 第三次重跑）。環境同前（Windows、`python`、現成 CLI binary
`build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe`，**未重建、未對 `build\` 跑 cmake**、
未改任何 `src/` `tools/` `scores/` 檔案；未執行 git commit / push / checkout / stash / reset）。
本輪暫存輸出：渲染在 `output\wf0907\R2\verify3\`（已 gitignore）；
分析腳本、PDF 與抽出的文字層只存在複核者的 scratchpad，未寫入 repo。

**本輪的方法差異（為什麼不是「再跑一次同一支腳本」）**：
引擎側**全部重寫**（自寫 24-bit WAV 讀檔、Hann 窗 FFT、band-peak 搜尋、τc/H(f) 的 float64 重實作），
不呼叫 `output\wf0907\R2\analyze.py` / `sweep.py` 也不沿用第二輪的腳本；
外部側**全部自行下載原始檔**（PDF 用 curl 抓、pypdf 抽文字層、逐字 grep；
網頁用 curl 抓 HTML、自行去標籤、逐字 grep），不依賴任何摘要器的轉述。

### E.1 引擎數字（第四次獨立重跑）

| 項目 | 報告記載 | 本輪自寫腳本 | 結果 |
|---|---|---|---|
| §3.1 峰值 dBFS（C4/A4/G5/G6/D7） | −26.67／−27.58／−42.63／−53.30／−60.41 | 同 | **5/5 逐位一致** |
| §3.1 主導/基頻比值（D7） | 1.0029 | 1.0029 | **一致** |
| §3.5 piano 掃描 37→87 | peak −22.10／rms −27.46／極差 30.47 | 同 | **一致** |
| §3.5 cimbalom | peak −2.01／rms −3.74／極差 5.70 | 同 | **一致** |
| §3.5 piano+wood | peak −2.16／rms −4.48／極差 6.41 | 同 | **一致** |
| §3.2/§3.9 dump p2−p1（C4/A4/G5/G6/D7） | −8.05／−10.03／**+8.24**／**+13.47**／−19.66 | 同 | **一致** |
| §3.6 G6 第3泛音相對基頻 | +9.10 dB | +9.10 dB | **一致** |
| §3.8 f₂/f₁（G5／G6） | 2.01287／2.05034 | 同 | **一致** |
| §3.10 由比值反解 B（G5／G6, Ø1.0 mm） | 4.32×10⁻³／1.73×10⁻² | 4.322×10⁻³／1.7285×10⁻² | **一致** |
| §3.10 f₂ 偏離 2× 的音分（G5／G6） | 11.1／43.0 cent | 11.1／43.0 cent | **一致** |
| §3.3 τc（A0/C4/A4/G5/G6/D7/C8） | 3.2623／2.3535／2.0967／1.8560／1.6146／1.5154／1.4581 ms | 同（float64 第三次獨立重寫） | **一致** |
| §3.3 x = 2f₁τc | 1.2315／1.8451／**2.9101**／**5.0632**／**7.1204** | 同 | **一致** |
| §3.3 等效 k（C2→C7） | 0.2116 | 0.2116 | **一致** |
| §3.3 H(f₁) float64 註記值（G5/G6/D7） | −34.50／−47.91／−48.44 dB | 同 | **一致** |
| **渲染重現性** | — | 5 個單音 WAV 對 `verify2` 逐檔比 SHA256 | **5/5 IDENTICAL** |

**本輪發現的一個量法敏感度（不是錯誤，但引用時要知道）**：
§3.1 最後一欄「FFT 第2泛音−第1泛音」**對 FFT 長度與 band-peak 搜尋窗寬敏感**。
本輪自寫腳本（2¹⁷ 點、±6% 搜尋窗）得 C4 −6.09／A4 −10.24／G5 **+6.58**／G6 **+4.83**／D7 −23.56 dB，
與報告的 −8.77／−8.72／**+7.41**／**+8.23**／−17.14 相比，**符號與方向全部一致，但 G6 差到 3.4 dB**。

> **2026-09-08 複核修正——敏感度比這裡原本寫的「±3 dB」更大。**
> 複核員與本輪各以第三支獨立腳本（2¹⁷ 點 Hann、±6% band-peak、以 `--dump-modes` 的實際 f₁/f₂ 為中心）
> 重量同一批 WAV，兩邊逐格一致，得
> **C4 −4.26／A4 −11.07／G5 +6.12／G6 +4.63／D7 −23.68 dB**。
> 對比 §3.1 表列值，**最大偏差在 D7 = 6.5 dB、其次 C4 = 4.5 dB、G6 = 3.6 dB**。
> → **本文件其他地方凡寫「±3 dB」的敏感度，一律改讀為「最大約 6.5 dB」。**
> 方向與符號仍然三支腳本全部一致（G5/G6 第2泛音高於基頻、C4/A4/D7 低於基頻），**結論不受影響**。
原因是高音區 partial 落在零點鄰域、且非諧使第2 partial 不在整數 2f₁ 上，窗寬一動取到的峰就換。
→ **結論不受影響**（G5/G6 第2泛音高於基頻這件事，兩種量法都成立），
但**§3.9 與 §4 的驗收靶請一律用 `--dump-modes` 那一欄**（該欄逐位可重現、無窗寬自由度），
不要引用 §3.1 的 FFT 欄當數字靶。這一點建議寫進 B-1 施工卡的量測規約。

### E.2 引用複核（本輪逐條重開原文，方法見上）

| 來源 | 本輪核對方式 | 結果 |
|---|---|---|
| Russell & Rossing (1998)（L1-16～L1-22 + 補充數字） | 自行下載 PDF（HTTP 200, 198,688 bytes）→ pypdf 抽全文 → 逐字 grep | **全部命中**。含 "In the upper two octaves, the fundamentals completely dominate the sound spectra"、"the fundamental is as much as 25 dB lower than the strongest partial"、"in the treble register the hammer-string contact time is several periods"、"in the treble region the values of f max surround the fundamental"、"a treble hammer would strongly excite the fundamental, but weakly excite only one or two harmonics"、"very closely approximated by a half-sine pulse, indicating a linear behavior"、"smooth increase from p ≈ 2 in the bass, to p ≈ 4 in the treble" |
| Fletcher, Blackham & Stratton (1962)（L1-23～L1-29） | 自行下載 BYU PDF（HTTP 200, 1,646,516 bytes）→ pypdf → 逐字 grep 表格數字列 | **全部命中**。G5 表 "1 779 779 779.1 0" / "2 1558 1562 1558.6 --22"；G6 表 "1 1568 1568 1568.2 0" / "2 3136 3134 3137 --38"；G2 −1/0、G3 −7/0、G4 0/−19 皆逐格核對；"the partials decrease in level at the rate of 2 db per 100-cps increase"、"produced on a good upright piano which was placed in the anechoic chamber" 命中 |
| **同篇 A0／G1 兩表（本輪新增 L1-33）** | 同上 | **命中**："1 27.5 27.5 27.51 --23"（A0, B=0.00053）、"1 48.6 49 48.6 --26"（G1, B=0.00028） |
| **Fletcher 的 dB 欄定義** | 同上（本輪特地查證，因為整條論證都靠這一欄） | **確認是 partial 的相對電平**：原文述分析儀 "draws horizontal lines whose lengths are proportional to the relative levels of the partials"。**2026-09-08 複核更正**：原寫「§3.9 的讀法（0 dB = 該音最強 partial）正確」——這條只對 Table II–VII（G1–G6）成立，**Table I（A0）不成立**，該表最大值是第 20 partial 的 **+4 dB**（"20 550 605 605 + 4"）。A0 的相對差已改為 27 dB |
| Chaigne & Askenfelt (1994) I（L1-30～L1-32、§3.11 溯源查核） | 自行下載 Kent State PDF（HTTP 200, 1,069,470 bytes）→ pypdf → 逐字 grep | **全部命中**，且**獨立確認關鍵否定事實**：全文 grep `half-sine` / `half sine` / `sinusoidal pulse` 命中數 **0**。"the force F/(t) is a result of a nonlinear interaction process"、"This yields, among other things, the contact duration"、"was set beforehand as a known parameter" 皆命中，最後一句的上下文確為批評 Hiller & Ruiz 舊模型 → **§3.11 的溯源判定成立** |
| KTH 五講 4 頁（L1-1～L1-6、L1-11～L1-14） | 自行 curl HTML（4 頁皆 200）→ 去標籤 → 逐字 grep | **全部命中**（8 條）。含 "contact durations decrease from about 4 ms in the bass to less than 1 ms in the highest treble."、"quite similar to half of the period"、"the harmonic strengths do not fall off at all toward higher frequencies (0 dB/oct)"、"d/L in the bass is a little less than 1/8"、"the treble contains only few partials" |
| Euphonics 3 頁（L1-7～L1-10） | 同上（3 頁皆 200） | **全部命中**。含 "it jumps up again when the first reflected pulse arrives back from the nearer end of the string"、"a half-cycle of a cosine wave"、"the finite-length impulse has the effect of a low-pass filter" |
| Gràcia & Sanz-Perela (2016)（L1-15） | 自行下載 arXiv PDF（200, 525,598 bytes）→ pypdf → grep | **命中** |
| Sound On Sound（L2-1、L2-2） | 自行 curl（200）→ 去標籤 → grep | **命中**。L2-2 全句 "The first partial above the top C is typically 20dB below its fundamental, producing an almost sinusoidal sound wave at these upper reaches." |
| Piano World（L3-1、L3-2） | curl 被 Cloudflare **proof-of-work 挑戰**擋下（回 202 + 挑戰頁）；改用 `WebFetch` 取得 | **命中**，發文者與日期一致（Jeffrey 06/10/04 11:58 PM、Axtremus 06/11/04 05:55 AM）。並取得 L3-1 更完整原文（見 §2 補記） |
| Modartt / Pianoteq（L3-3） | 自行 curl（200）→ grep | **命中**，日期 14-05-2016 09:46 |
| **Modartt 新增兩串（L3-4～L3-6）** | 自行 curl（皆 200）→ grep | **命中**，發文者與日期見 §2 表 |
| **結論** | — | **本輪核對 30 餘條引述，全數命中，未發現任何引用不實。** |

### E.3 本輪自行發現並更正的一處事實錯誤（誠實登記）

- **§5 缺口 4 原寫「Fletcher 只給五顆 G 加一顆 A0」→ 錯，實際是七顆音**（漏掉 G1, 48.6 Hz, B=0.00028）。
  已在 §5 缺口 4 更正，並把漏掉的兩顆低音（A0/G1）補進 §2 的 L1-33 與 §3.9 的量測表。
  **這個更正的方向是加強、不是削弱結論**：補進來的兩顆音基頻分別比該音最強 partial 低 27 dB／26 dB，
  把「弱基頻是低音現象」的量測曲線補得更完整。

### E.4 本輪新取得 / 仍未取得

| 來源 | 前輪狀態 | 本輪結果 |
|---|---|---|
| **Pianoteq 論壇「高音區太薄／太亮」使用者回饋**（卡上 §1-C 明確要求） | 前兩輪未取得 | **已取得兩串**（2015、2017）→ L3-4～L3-6 |
| **Fletcher 同篇 A0／G1 兩張表** | 前兩輪未使用 | **已取得並逐格核對** → L1-33 |
| Hall & Askenfelt (1988) | 403（第三次） | **仍 403（第四次）**。本輪改走直接 PDF 路徑仍被 Cloudflare "Just a moment..." 擋；判定為本環境取不到，**不再重試** |
| Chaigne & Askenfelt (1994) Part II | 付費牆 | **仍未取得**（本輪未再嘗試，狀態沿用） |
| Meyer 音域 SPL 表（§5 缺口 1） | 查不到 | **仍查不到**。本輪另以「same dynamic level 跨音域 SPL 差 / treble weaker dB」等切入角再搜一輪，只找到定性敘述，**沒有可引用的 dB 數字** → 缺口 1 維持開啟 |
| Young (1952) 逐音 B 值表 | 未取得 | **仍未取得**（用途已由 Fletcher 取代） |
| Stulov (2003) | 未取得 | **本輪未再嘗試**，狀態沿用 |
| Reddit | 「抓不到」 | **查清為永久封鎖**（三條路徑的實際回應碼見 §5 缺口 5），非暫時失敗 |

### E.5 本輪對判定的結論

- **§0 的判定與 §4 的建議（選項 B）本輪未做任何更動**，因為所有支撐它的數字與引述都通過了獨立重驗。
- 本輪讓論據**更硬的一點**：「弱基頻是低音現象」現在可以在**同一台琴、同一次量測**內
  從 A0 走到 G6（L1-33 + §3.9），不再需要跨論文拼接。
- 本輪讓論據**更誠實的兩點**：(1) §3.1 的 FFT 欄有量法敏感度（**2026-09-08 複核更正為最大約 6.5 dB**，原寫 ±3 dB），驗收靶要用 dump 欄（E.1 末段）；
  (2) §5 缺口 4 的事實錯誤已更正（E.3）。
- **仍然沒有變的缺口**：真槌力譜的滾降形狀（缺口 2）與跨音域 SPL 數字（缺口 1）——
  **B-1「改成什麼形狀」在補上這兩者之前，維持不動**。

---

## 複核修正記錄（2026-09-07）

> 由第二位 Opus 做引用複核後提出 6 條 findings，本節逐條記錄**怎麼改的**。
> **判定結論未變**：仍是選項 B（判引擎缺陷），仍建議先做 B-2。
> 六條裡沒有任何一條動搖 §3.9 的量測對照或 §3.2 的零點拆解——那兩條才是判定的支撐。

| # | 嚴重度 | 位置 | 複核員說什麼 | 我怎麼改 |
|---|---|---|---|---|
| 1 | major | §0（前言 3.）、§2 L1-33、§3.9 量測表、附錄 E.2 | Fletcher Table I（A0）的最強 partial 是第 20 根的 **+4 dB**，不是 0 dB；所以基頻相對最強 partial 是 **−27 dB**（不是 −23），而且「0 dB = 該音最強 partial」這個讀法對 Table I 不成立 | **已更正，共 8 處**。我自己重下 BYU PDF（HTTP 200, 1,646,516 bytes）以 pypdf 抽文字層逐格核對，確認 Table I 逐列有 "20 550 605 605 + 4"，最大值確為 +4；同時把 Table II–VII（G1–G6）六張表也逐格掃過，**最大值確實都是 0 dB**，所以問題只在 A0 一張表。改法：(a) 所有「A0 −23 dB」改成「相對該音最強 partial 低 **27 dB**」並在括號註明「基頻欄 −23、最強欄 +4」；(b) §3.9 表格 A0 那一列的「最強的是第 5 partial」改為「第 20」；(c) 在 L1-33 底下新增一段**量法註記**，明寫「Fletcher 的 dB 欄參考點未在文中明寫，六張表恰好最大值是 0、但 Table I 不是，凡要算相對差都必須先在該表找最大值」；(d) 附錄 E.2「dB 欄定義」那一列的結論由「§3.9 的讀法正確」改為「只對 Table II–VII 成立，Table I 不成立」。**方向是加強不是削弱**：基頻比原先寫的更弱 4 dB |
| 2 | major | §3.8（α 錨點那一段）+ 上一輪回報的 open_item | 「a smooth increase from p≈2 in the bass, to p≈4 in the treble」的量測者是 **Hall & Askenfelt**，Russell & Rossing 只是在介紹他們的動態量測法時轉述；引擎 α 的來源（Woodhouse Table 2）**也是轉引 Hall & Askenfelt**，所以「差約 1.0」不是兩個獨立來源的對照 | **已更正**。我自己重下 russell.pdf（HTTP 200, 198,688 bytes）逐字核上下文，確認原文是 "In addition to their static measurements, Hall and Askenfelt [5, 10] also devised a dynamic method… Measurements made for voiced hammers from several pianos show a smooth increase from p≈2 in the bass, to p≈4 in the treble."；並確認 Russell & Rossing **自己的** p 量測在 Figure 5（13 顆整音槌，文中 D2 槌 p = 2.2），且自述 "Exponent values agree well with results of Hall and Askenfelt [5, 10]"、**未給高音端逐音 p 值**。§3.8 已改寫成「這是同一組量測的兩次轉引，不是獨立對照，證據力比原本弱」，並註明 Russell & Rossing 無法當高音 p 的獨立仲裁。**本卡本來就沒有對 α 下判定**（原文即寫「這不是 A14 的成因」），此更正不改任何結論，但 open_item 的措辭已同步修正 |
| 3 | minor | §2（Russell & Rossing 補充數字） | 引號內 "The F7 string is 2794 Hz, …" 不是逐字原文 | **已改回逐字原文**："The fundamental frequency of the F7 string is 2794 Hz, which lies between the values of f max shown in Figure 7."（我在 russell.txt 第 760–766 行逐字核對）。並在該行括號註明「原引述截短了開頭，數字與條件皆未改」 |
| 4 | minor | §3.1 表最後一欄的量法敏感度（附錄 E.1 自陳「±3 dB」） | 實際敏感度比 ±3 dB 大 | **已改為「最大約 6.5 dB」，共 4 處**（§4 B-1 量測規約、§3.9 註、E.1 末段、E.5）。我用第三支獨立腳本（2¹⁷ 點 Hann、±6% band-peak、以 `--dump-modes` 的實際 f₁/f₂ 為中心）重量同一批 WAV，得 **C4 −4.26／A4 −11.07／G5 +6.12／G6 +4.63／D7 −23.68 dB**，與複核員數字**逐格相同**；對 §3.1 表列值最大偏差 **D7 = 6.5 dB**、C4 4.5 dB、G6 3.6 dB。符號與方向三支腳本全部一致，**結論不受影響**，驗收靶原本就已規定用 `--dump-modes` 欄 |
| 5 | minor | §3.3 表欄位標題 | 欄名寫 `H(2f₁)`，欄內其實是取在非諧的實際 f₂ 上，兩者在零點鄰域差數十 dB | **已把欄名改為 `H(f₂ 實際)`**，並在表下加一段註記寫出兩種取法的差：我以 float64 用 `--dump-modes` 的實際 f₂ 重算，得 D7 **H(f₂ 實際) = −73.5 dB vs H(2f₁) = −46.5 dB（差 27 dB）**、G6 差 1.8 dB、C4/A4/G5 三格差 0.04 dB 以內，與複核員一致。附錄 D.1 呼應該欄的那一段也已同步標注欄名已改 |
| 6 | minor | §4 選項 B 的 B-1 驗收條件 | §0、§4 主體白話可讀，但 B-1 那份驗收清單有術語（f_max/f₀、梳齒式非單調、dump-modes）月月無法自行判讀 | **已為 5 條驗收條件各補一段「白話」**：把 f_max 比喻成「槌子這支刷子刷得最用力的頻率，真琴剛好刷在音高上（比值≈1），引擎刷在只有音高十分之一的地方」；把梳齒非單調寫成「從低音彈到高音音量忽大忽小像鋸齒，真鋼琴不會這樣」；把 `--dump-modes` vs 渲染 FFT 寫成「叫引擎自己印數字 vs 渲染出來再量，後者會差最多約 6.5 dB」；把 −19/−22/−38 dB 那條寫成「第二根泛音比音高本身弱幾 dB，負號＝比較弱，引擎的 G5/G6 是正號代表泛音反而比較大聲」 |

### 本次複核**未**改動的東西（避免誤會）

- **§0 的判定文字、§4 的三個選項與「選 B、先做 B-2」的建議**：完全未動。
- **§3.2 的逐環節拆解、§3.3 的 τc／x 數值、§3.5 掃描斜率、§3.9 的 G2–G6 逐音對照**：完全未動（複核員也未提出異議，且六條 findings 中沒有一條指向這些）。
- **§5 的五個已知缺口**：狀態不變，仍然開啟（Meyer SPL 表、Hall & Askenfelt 1988 全文、真槌力譜滾降形狀等）。本輪**沒有為了關掉 finding 而補任何新來源**。
- **`src/`、`tools/`、`scores/`**：本輪一個字都沒改，只改這份 `.md`。

### 由 finding 2 衍生、要交給 B4 卡的措辭更正

原 open_item 寫「kPianoHammerAlpha 的 C7 錨點 3.0 與 **Russell & Rossing 量測**的高音端 p≈4 差約 1.0」，
正確說法是：**兩個數字同源（都轉引 Hall & Askenfelt 1988），差 1.0 是兩份二手文獻的轉述差異，
不是引擎與獨立量測的差異**。要真正裁決高音端 α 該是 3.0 還是 4.0，
仍需 Hall & Askenfelt (1988) 原文——那正是 §5 缺口 2 尚未取得的那一篇。

---

## 附錄 F：複核修正記錄（2026-09-09，WF0908-P5）

> 卡：`docs/workcards/WF0908_P5_research_cleanup.md` §1 的 R2 那一列。
> **只改 §0 一處，§2／§3／§4／§5 與所有數字一個字都沒動。**

| # | finding | 處理 |
|---|---|---|
| 1 | §0「機制上最關鍵的一個外部數字」那一段，把 Hall 原句的 **middle range（中音域）** 限定條件剝掉，寫成通則「真鋼琴的槌弦接觸時間 τc ≈ 基頻半週期」，與 §3.3 第 2 點（真鋼琴高音區 x > 1 是常態、半正弦模型在 x ≳ 1 本身不成立）自相矛盾 | **已改**。§0 該段改回限定版，並把結論改寫成三步：(1) τc ≈ 半週期只是**中音域**基準（x ≈ 1）；(2) 引擎 G5 的 2.9 倍（x = 2.910）已遠超該基準；(3) **但這不是判缺陷的理由**——真鋼琴高音本來就 x > 1，缺陷在於「把只在 x < 1 有效的公式外插到 x = 1.2～7.1」，即 §3.3 講的模型適用域問題。並明寫「判缺陷的依據仍然是 §3.6／§3.5／§3.9，不是這 2.9 倍」。白話段同步改寫 |

**本輪重新核對的原文（存取 2026-09-09）**：
Hall 那句仍為 <https://www.speech.kth.se/music/5_lectures/hall/hall.html>，
引述維持 ≤15 字的 “contact times in the middle range are quite similar to half of the period”
（§2 表 L1-4 那一列本來就寫著「中音域」，本輪不動它）。

**本輪的邊界**：只改本 `.md` 的 §0 與本附錄；未碰 `src/`、`tools/`、`tests/`、`scores/`；
未渲染任何音訊、未跑 cmake、未 `git add`／`commit`／`push`。
**判定不變：仍是選項 B。**

---

## 附錄 F-2：複核修正記錄（2026-09-09 第二次，WF0908-P5 修正回合）

> 卡：`docs/workcards/WF0908_P5_research_cleanup.md`。**只改 §0 的兩句與本附錄；§2／§3／§4／§5 的數字仍然一個字都沒動。**

| # | 嚴重度 | finding | 處理 |
|---|---|---|---|
| 1 | **blocker** | 上一輪新寫的 §0 第 2 步把 G5 的無因次量寫成 `x = 5.06`，但 **5.063 是 G6 的值，G5 是 2.910**（§3.3 表第 399 行、§3.9 表、以及 §3.3 下方的 float64 複核註記三處都寫 G5 = 2.910）。同一句自己也寫著「2.9 倍」，`1.856 / 0.638 = 2.909` 也對得上 2.910——**5.06 是本輪新增文字裡的數字錯置**，且與被它指名引用的 §3.3 直接矛盾 | **已改**。§0 第 2 步改為 `x = 2·f₁·τc = 2.910`；附錄 F 表格裡把同一個錯值再寫一次的那句（「引擎 G5 的 2.9 倍（x = 5.06）」）同步改為 `x = 2.910` |
| 2 | 連帶 | 同段第 3 步寫「引擎是把只在 x < 1 有效的公式**外插到 x = 5～7**」。5～7 只涵蓋 G6（5.063）與 D7（7.120），漏掉 C4 1.231／A4 1.845／G5 2.910——這幾個也都 > 1，同樣落在外插區 | **已改**為「外插到 **x = 1.2～7.1**（§3.3 表五個音全部 x > 1：C4 1.231／A4 1.845／G5 2.910／G6 5.063／D7 7.120）」；附錄 F 內的同一句同步改。**五個數字全部照抄 §3.3 現有的表，未新增任何計算** |

**本輪的邊界**：只改本 `.md` 的 §0 兩句、附錄 F 表格內兩處引文，加上本附錄 F-2；
未碰 `src/`、`tools/`、`tests/`、`scores/`；未渲染音訊、未跑 cmake、未 `git add`／`commit`／`push`。
動筆前備份在 `output/wf0908/P5_fix/A14_weak_fundamental_ruling.zh-TW.md`。
**判定不變：仍是選項 B。**

---

## 落地記錄（2026-09-10）

月月 2026-09-10 裁決：**放行**選項 B（B-2）patch，`git apply reports/a14_tauc_keytrack_b2.patch`，
落地卡 `docs/workcards/WF0908_P2_a14_tauc_rule10.md`，整合工兵 Sonnet 執行、證據檔
`reports/gate_outputs/wf0910_A14_apply.txt`。

- **patch sha256**：`5f5cce8d137bede2b2c70e3ef47793f7d01ff1c0dfabf144c7b867e6b9d489d`
  （`reports/a14_tauc_keytrack_b2.patch`）。
- **位元不變（8 首代表曲）**：7/8 IDENTICAL；只有 `physical_piano` 改變——
  舊 sha256 `607d0d3bc578136ff8ebb0bd5c428582d2c2db6ede3989286284539399d52f71` →
  新 sha256 `1233b53f1e8660bcb46277da814c62190c8f283e20d57ae8297fb865878fc55b`
  （與本檔 §附錄／`reports/a14_tauc_keytrack_before_after.md` 事前記錄的預期值完全一致）。
  新基準另存為 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`（`sha256_before_post_d8.txt` 保留存檔）。
- **GATE 結果一行摘要**：三 build target + 五測試 target 全 exit 0；`ctest` 4/4 Passed（含 §A14-1～§A14-4 四項新單元測試 PASS）；
  `physics_verify.py --full` → NO CHECKED FAILURES（F3 piano velocity 判定仍 PASS，僅既有 3 筆 rubber UNVERIFIED）；
  受影響 5 檔 `verify_score.py` 全 PASS；`pytest tests -q` 263 passed / 1 skipped / 3 xfailed；
  HostProbe PASS (0 failures)。全套細節見 `reports/gate_outputs/wf0910_A14_apply.txt`。
