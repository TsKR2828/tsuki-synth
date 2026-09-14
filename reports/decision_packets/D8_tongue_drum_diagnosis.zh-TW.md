# D8 裁決包：tongue_drum 音高-響度斜率與缺泛音——根因診斷

> WF0907-R6 研究卡交付　執行：Opus（研究員）　日期：2026-09-07 初版；**2026-09-08 第二位 Opus 獨立複核並修訂**；
> **2026-09-08 第三位 Opus 再次獨立重跑並修訂**（見文末「第三輪獨立複核記錄」與 §3.11）；
> **2026-09-08 第四位 Opus 第四輪獨立重跑並修訂**（見文末「第四輪獨立複核記錄」與 §3.12）
>
> **2026-09-08 第四輪修訂摘要**（全新探針、全新量測腳本，不沿用前三輪任何檔案；**推翻了一條既有結論**）：
> 1. **推翻「梁模型自己還欠一截」**：前三輪由「cimbalom 換 `finger` 只惡化到 23 dB、tongue_drum 卻 47 dB」
>    推論「剩下的那一截是梁模型的短板」。**這條不成立。**根因是：同一個字 `"finger"` 在兩顆引擎被翻譯成
>    **不同硬度**——tongue_drum → Cotton（τc 基準 6.0 ms），cimbalom → Felt（τc 基準 2.0 ms，且改走鋼琴槌氈解算器）。
>    把 cimbalom 也餵同一個 6 ms 檔位（`cotton_mallet`）實測斜率 **43.18 dB（0.3 s 窗）**，
>    **比 tongue_drum 的 37.20 dB 還糟**。→ 這件事幾乎 100 % 是接觸時間問題，梁模型在本案沒有額外欠帳。見 §3.12。
> 2. **新的一級發現：`finger` 的跨引擎對映不一致**（`ScoreRenderer.h` 兩張硬度表，HEAD `:1125` vs `:1138`）。
>    這是可以指名的**參數化不一致**，也讓「40 dB vs 4.4 dB」這個比較從頭到尾都不是同一件事。
> 3. **修正選項 1 的期望值**：整首月光重渲實測，`felt` 版把 200 Hz 以下能量從 97.36 % 降到 **78.06 %**
>    （`wood_mallet` 是 17.53 %）。前三輪把 `felt` 說成「同樣把旋律救回來、又沒有副作用」，
>    **就整首的能量分布而言它只走了約四分之一的路**。取捨敘述已改寫（§4 選項 1）。
> 4. §3.1／§3.2／§3.3／§3.4／§3.5／§3.7／§3.8／§3.9／§3.11 的數字第四輪**全部重現**（多數逐位相同），
>    §2 抽驗的四個「已取得原文」來源今日重開引述全部相符，ICSV27 與 Reddit 兩個缺口維持。
>
> **2026-09-08 第三輪修訂摘要**（全新探針、全新量測腳本，不沿用前兩輪任何檔案）：
> 1. **§3 的引擎數字全部重現**：模態1 振幅 0.232／0.19351／0.05308／0.00951／0.00804／0.00456 與 §3.1 逐位相同；
>    exciter 反事實 34.13／10.48／−7.82 dB 與 §3.7 逐位相同；corpus 43 檔／2463 事件／96.8 % 軟激發與 §3.8 逐位相同。
>    §2 的四個可取得原文來源（Euphonics、Physics Today、Kosmosky、RAV Vast）今日逐句重開，引述全部相符。
> 2. **修正「哪一組幾何才是月光樂譜自己的」**：厚 2.6／寬 24／strike 0.44 是那首的 **952 事件（83.4 %）主力幾何**，
>    厚 3.2／寬 30／strike 0.42 只有 176 事件（15.4 %）。第二輪把前者說成「探針幾何」、後者說成「樂譜自己的幾何」
>    並要求「決策請看後者」，**框架有誤**；兩組都是那首自己的參數，已於 §0／§4 改成並列（結論不變）。
> 3. **選項 1 新增一條先前沒被指出的代價**：換 `wood_mallet` 後，MIDI 37 的**模態 2（6.27×f0）振幅是模態 1 的 2.27 倍（+7.1 dB）**，
>    低音區的基頻不再是最強分音——這正是 A14「弱基頻」那一類的狀況。`felt` 沒有這個問題。見 §4 選項 1「代價」與 §3.11。
> 4. **修正行號基準敘述**：§3.4 原稱 `ChromaticEngine.h` L411 以前的錨點「在 HEAD 與工作樹一致」，實測**有整齊的 +1 行位移**。
>
> **2026-09-08 修訂摘要**（第二輪獨立重跑，用不同的舌片幾何從頭複刻一次，結論不變、範圍改大）：
> 1. **§3.8 的 corpus 影響範圍原本嚴重低估**：舊版只列 8 個檔（照卡上的 `grep -l tongue_drum`）。
>    實際上 `beam` 是同一顆引擎的**別名**（`src/score/ScoreRenderer.h:290`、`:817`），
>    全 corpus 共 **43 個 score 檔、2463 個事件**用到這顆引擎，其中 **96.8 % 用的是軟激發**。
>    這會放大選項 2/4 的 Rule 10 波及面——已於 §3.8 ／ §4 改寫。
> 2. **新增可取得原文的 A 級來源**：Morrison & Rossing 的 handpan 模態比值改由 *Physics Today*（2009）取得逐字原文
>    （舊版只能標「未取得原文」）。見 §2 證據 16、17。
> 3. **新增跨引擎關鍵對照**：cimbalom 也改用 `finger` 後斜率同樣惡化到 23.4 dB（§3.10），
>    直接證明「40 dB vs 4.4 dB」的差距**不是引擎體質差距，是 exciter 設定差距**。
> 4. 第二輪用完全不同的舌片幾何（厚 3.2 ／ 寬 30 ／ strike 0.42，取自同一首月光樂譜的另一組參數）
>    重跑，Python 複刻與 CLI `--dump-modes` 仍逐音符吻合到小數第 5 位（§3.9），
>    §3.4 的環節歸因因此是**兩組獨立幾何各自驗證過**的。
> 依據卡：`docs/workcards/WF0907_R6_D8_tongue_drum.md`、共同規約 `WF0907_README.md`、研究鐵律 `WF0907_R_research_common.md`
> **本卡不改任何程式碼、不改任何 `scores/` 檔案。** 全部實驗檔都寫在 `output\wf0907\R6\`（已 gitignore）。
> 引擎數字一律用現成的 `build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe`（唯讀使用，沒有對 `build\` 跑 cmake）。

---

## §0 一句話結論

**主因不是引擎壞掉，也不是「高音舌片本來就這麼小聲」，而是樂譜裡寫的敲擊工具 `exciter: "finger"`
讓槌頭接觸時間長到 4.3–10.8 毫秒，等於用一塊很軟的東西去按琴——軟到只剩基頻出得來、
而且愈高音愈出不來，光這一項就吃掉 43.2 dB；引擎原本要救回來的「跨音域補償」又被 ±12 dB 上限卡死，
只救回 9.1 dB。**

也就是說：**光把樂譜裡的 `"finger"` 換成 `"wood_mallet"`，一行程式都不用改，斜率就從 40 dB 級掉到個位數。**
四輪獨立量測、兩組舌片幾何、三種量測窗都指向同一個結論：

| 幾何（皆取自月光空靈鼓版樂譜本身） | 量測窗 | `finger`（出貨） | `wood_mallet` | 出處 |
|---|---|---|---|---|
| 厚 2.6／寬 24／strike 0.44（**952 事件＝83.4 %**） | 0–0.3 s | 37.20 dB | **2.67 dB** | §3.11 |
| 厚 2.6／寬 24／strike 0.44 | 0–6.0 s | 47.13 dB | **8.32 dB** | §3.11 |
| 厚 3.2／寬 30／strike 0.42（176 事件＝15.4 %） | 0–0.3 s | 39.31 dB | **2.77 dB** | §3.11 |
| 厚 3.2／寬 30／strike 0.42 | 全檔 RMS | 47.57 dB | **6.71 dB** | §3.10 |

整首月光空靈鼓版**改成 `wood_mallet`** 重渲後，能量分布從「97.4 % 都在 200 Hz 以下」變成
「82.4 % 在 200 Hz–2 kHz 的旋律音域」（§3.5；第四輪重跑得 82.46 %，§3.12(d)）。

**但換槌不是白吃的午餐（2026-09-08 第三輪查出來的）**：`wood_mallet` 在**低音端會讓基頻失去主導**
——MIDI 37 的第二個分音變成比基頻大 2.27 倍（+7.1 dB），低音聽起來會偏「鐘」而不是「鼓」。
折衷的 `felt` 沒有這個副作用（斜率也從 40 dB 級掉到 14–26 dB），但**泛音仍然回不來**。
**2026-09-08 第四輪再補一格**：整首重渲後，200 Hz 以下的能量占比是
`finger` 97.4 % → **`felt` 78.1 %** → **`wood_mallet` 17.5 %**（§3.12(d)）——
也就是 `felt` 只把旋律「拉出來一部分」，`wood_mallet` 才是拉到底。
**所以月月要選的其實是這兩個之一**：`felt`＝旋律部分浮出、基頻保住、沒泛音；
`wood_mallet`＝旋律完全浮出、泛音回來、低音偏鐘感。細節與數字見 §3.11／§3.12 與 §4 選項 1。

**2026-09-08 第二輪加驗（最有力的一條）**：把**揚琴**（cimbalom，原本被當成「沒問題的對照組」）
也改成 `finger`，它的斜率一樣從 7.1 dB 惡化到 **23.4 dB**（§3.10）。
所以 `TODO.md` D8 記載的「空靈鼓 40 dB vs 揚琴 4.4 dB」**是被 exciter 設定混淆的比較**，
不是兩顆引擎的體質差距。

**2026-09-08 第四輪把這條補完（並推翻了原本的尾巴）**：上面那句原本還接著說
「剩下的那一截（47.6 vs 23.4 dB）才是梁模型自己的短板」——**那句話是錯的**。
原因是同一個字 `"finger"` 在兩顆引擎被翻成不同硬度：tongue_drum 拿到 **Cotton（6.0 ms）**、
cimbalom 拿到 **Felt（2.0 ms）**。把揚琴也餵 6 ms（樂譜寫 `cotton_mallet`），
它的斜率是 **43.18 dB**，**比空靈鼓的 37.20 dB 還糟**（同探針、同 0.3 s 窗，§3.12）。
**結論因此更乾淨：這件事幾乎全部是「接觸時間太長」，梁模型在本案沒有額外欠帳。**

需要月月裁決的是：**這是「樂譜設定選錯」還是「引擎的槌具模型套錯樂器」？**
兩件事都成立，但修法不同（§4）。

---

## §1 問題

`TODO.md` D8 與 `exports/products/moonlight_batch1/PRODUCT_SHEET.md`「已知缺陷」第 1 條記載：

- 同 velocity 下 tongue_drum MIDI 37→87 的 RMS 從 −32.8 掉到 −73.1 dBFS（40.3 dB），cimbalom 同域僅 4.4 dB。
- 輸出近純正弦：99.9 % 能量在基頻、無泛音列。
- 後果：月光空靈鼓版 54.2 % 的音在 MIDI≥60，主旋律比低音弱 20–40 dB，QA 判暫緩上架。

要回答的是：**引擎 bug ／ 參數化錯 ／ 還是物理上高音舌片本來就這樣？**

---

## §2 外部證據（分級）

引用鐵律：每條附 URL + 存取日期 + ≤15 字原文引述。打不開的寫「未取得原文」。
分級：**A = 論文／教科書／量測報告（物理證據）**；**B = 製造商技術頁（工程慣例，非量測）**；
**C = 社群／使用者觀感（需求證據，不是物理證據）**。

| # | 級 | 來源 | 存取日期 | 原文引述（≤15 字） | 對本案的意義 |
|---|---|---|---|---|---|
| 1 | A | Euphonics（Jim Woodhouse 線上音樂聲學教科書）§3.3 Marimbas and xylophones　https://euphonics.org/3-3-marimbas-and-xylophones/ | 2026-09-07 | "This can be done by using a soft hammer." | **直接解釋「近純正弦」**：要讓基頻遠大於所有泛音，作法就是「用軟槌」。引擎現在正是這種狀態，所以純正弦不是 DSP 壞掉，是軟槌的必然結果。 |
| 2 | A | 同上 §3.3 | 2026-09-07 | "Recall that in the ideal beam this ratio was 2.76" | 理想自由-自由梁第二模態 = 2.76×基頻；本引擎用的是固定-自由（懸臂）梁，比值 6.27（見 §3.1）。 |
| 3 | A | 同上 §3.3（實測條列） | 2026-09-07 | 木琴棒："1.00, 3.00, 6.16, 10.29"；馬林巴棒："1.00, 3.92, 9.24, 16.27" | **真實打擊棒都被「削底」調過音**，第二模態被拉到 3× 或 4×；沒有任何真實樂器把第二模態放在 6.27×。引擎的 6.27 是「未調音的等截面梁」。 |
| 4 | A | 同上 §3.3 | 2026-09-07 | "removing wood from the underside of the bars" | 調音手段＝改變棒厚度沿長度的分布（undercutting），不是改整體長度。 |
| 5 | A（未取得原文） | *Experimental characterization of the steel tongue drum*, ICSV27, Prague, 2021（= `TODO.md` D4）　https://unige.iris.cineca.it/bitstream/11567/1063604/1/full_paper_1117_20210430223100647.pdf | 2026-09-07 | **未取得原文**（機構庫 HTTP 403；ResearchGate 作者自存版 403；CORE 403；scholar.archive.org 500） | 本輪四條路徑都打不開，與 repo `docs/EXTERNAL_ANCHOR_SOURCES.md` 記載的 403 狀態一致。**不得引用其數字。**（搜尋引擎摘要曾出現「G4 392 Hz、泛音 1179/1960/2745/3531 Hz」與「R²=0.9955 的長度-頻率經驗式」，但我沒能打開原文核對，因此**本卡不把它當證據使用**，只登記為待補。） |
| 6 | A（僅書目） | Morrison & Rossing, *Modes of vibration and sound radiation from the Hang*, Archives of Acoustics 32(3), 551–560 (2007)　https://www.academia.edu/96431023/... | 2026-09-07 | **未取得原文**（academia.edu HTTP 403；semanticscholar 頁面回空；ResearchGate 403） | 已知存在、已知是 handpan 模態與輻射的權威量測；本輪未取得全文，不引用其數字。 |
| 7 | B | RAV Vast 官方術語頁　https://ravvast.com/blogs/news/main-terms-in-the-world-of-steel-tongue-drum | 2026-09-07 | "Each tongue can produce 4–7 harmonic overtones in harmony" | 真實高階鋼舌鼓**每片舌都刻意調出 4–7 個泛音**。引擎現況（finger）是 0 個可聽泛音。 |
| 8 | B | 同上 | 2026-09-07 | "its weight, width, and length determine that note's pitch" | 真鼓調音同時改**重量、寬度、長度**；引擎的 `BeamModel::lengthFromMidiNote()` 只改長度、寬厚固定（見 §3.6）。 |
| 9 | B | 同上 | 2026-09-07 | "Playing with mallets tends to produce a louder, clearer attack" | 槌 vs 手指的差異在真實樂器上也存在，方向與引擎一致（槌＝更大聲更清楚）。 |
| 10 | B | Hluru 專業指南（廠商部落格）　https://www.hluru.net/en-us/blogs/skills-tips/the-professional-guide-to-steel-tongue-drums-decoding-materials-acoustics-and-quality | 2026-09-07 | "the primary overtones (the octave and the perfect fifth) must also be perfectly aligned" | 業界品質定義：**主要泛音是「八度」與「純五度」**。**該頁只用音程名稱，全篇沒有任何數值比值**（2026-09-08 逐句複查確認）——八度＝2×、純五度＝1.5× 是音程的定義換算，**不是這個來源說的**，本卡不把數字算在它頭上。可以確定的只有：它點名的兩個泛音都不是懸臂梁的 6.27×。 |
| 11 | B | Hluru 入門指南　https://www.hluru.net/en-us/blogs/skills-tips/beginners-guide-to-steel-tongue-drum-music-rhythm-resonance-flow | 2026-09-07 | "rubber mallets (which highlight the fundamental tone) or your fingers (which highlight softer overtones)" | 廠商說法與引擎目前的方向**相反**（引擎裡 finger 反而最沒有泛音）。此為觀察到的矛盾，非物理證據。 |
| 12 | B | Wikipedia, *Steel tongue drum*　https://en.wikipedia.org/wiki/Steel_tongue_drum | 2026-09-07 | "The instrument is played with the fingers or with mallets." | 手指與槌都是正常演奏法——所以「用 finger 導致不可用」是模型問題，不是使用者用錯樂器。 |
| 13 | B | 同上 | 2026-09-07 | "tuned by the maker by varying the length of the cuts" | 舌片音高主要靠切口長度（與引擎的長度律方向一致）。 |
| 14 | C（未取得） | r/handpan、r/tonguedrum、r/percussion | 2026-09-07 | **未取得原文**：本環境 WebFetch 對 `www.reddit.com` 與 `old.reddit.com` 皆回 "unable to fetch"，`.json` 端點同樣不通；WebSearch 的 `site:reddit.com` 查詢未回任何 reddit 連結。 | **社群層面的「高音舌片是不是本來就比較小聲」在本輪查不到可引用的原文。**登記為缺口（§5）。 |
| 16 | A | Morrison & Rossing, *The extraordinary sound of the hang*, **Physics Today 62(3), 66–67（2009-03-01）**　https://physicstoday.aip.org/quick-study/the-extraordinary-sound-of-the-hang | 2026-09-08 | "The frequencies of those modes are in the ratio of 1:2:3" | **本輪取得原文的關鍵替代來源**（2007 那篇 Archives of Acoustics 仍 403）。同文另一句："the three lowest-frequency modes ... are all strongly excited."　→ 真實同族鋼製打擊樂器**三個最低模態都被強烈激發**，比值 1:2:3；本引擎在 `finger` 下只剩 1 個模態，且梁比值是 6.27。 |
| 17 | A（二手引用） | McGill MUMT307 專題頁，引 Morrison & Rossing (2009)　https://carrieeex.github.io/MUMT307-project/ | 2026-09-08 | "The harmonic ratio of the most prominent spectral peaks is 1 : 2 : 3" | 獨立第二處覆述證據 16 的比值；同頁另引「rubber mallet or just fingertips ... can excite the fundamental, the second, and the third harmonics」——**真實樂器用手指也照樣激發到第三泛音**，與引擎現況（手指＝沒有泛音）方向相反。 |
| 18 | B | Kosmosky（廠商，創辦人 Alexey Zinchenko，2021-05-07）　https://en.kosmosky.com/news/overtones | 2026-09-08 | "consist in the correct proportions of 1:2:3:4: 5" | 廠商定義的「調得好的舌片」泛音比值是 **1:2:3:4:5**，不是懸臂梁的 6.27:17.55。與證據 10 互相獨立佐證。 |
| 19 | B | Panda Drum（廠商部落格）　https://pandadrum.com/blogs/calm-panda-blog/how-does-a-steel-tongue-drum-work | 2026-09-08 | "autotuned to play a particular note depending on its width and length" | 真鼓調音**同時改寬度與長度**；引擎的 `lengthFromMidiNote()` 只改長度、寬度寫死 0.02 m（`ChromaticEngine.h:179`），score 路徑則連長度都不隨音高變（§3.6）。與證據 8 互相獨立佐證。 |
| 15 | C | Sound Artist, *Handpan Techniques: How to Master Playing High Notes*（2024-09-12）　https://thesoundartist.com/blogs/news/handpan-techniques-how-to-master-playing-high-notes | 2026-09-07 | 全文**未出現**任何「高音較弱／較小聲」的敘述（逐段檢查後為否定結果） | 一份專門講「怎麼彈高音」的教學文完全沒提到高音天生小聲——**弱證據，指向「40 dB 不是玩家公認的正常現象」**。 |
| 20 | B | Handpan.World（調音師部落格，2024-05-13）　https://www.handpan.world/en-us/blogs/handpan-tuning-nachstimmen-klangoptimierung/sound-impedance-the-fine-of-perfect-handpan-tuning | 2026-09-08 | "Betroffene Töne klingen deutlich leiser"（受影響的音明顯比較小聲） | **真實樂器上「某些音明顯較小聲」被業界當成需要調音師處理的缺陷**（成因寫的是聲阻抗／干涉），不是被接受的物理常態。頁面**沒有任何 dB／Hz 數字**，所以只能支持「方向」，不能拿來量化 40 dB。 |
| 21 | A（未取得原文，僅列為線索） | ICSV27 2021 鋼舌鼓論文的搜尋引擎摘要　https://www.researchgate.net/publication/353818565_Experimental_characterization_of_the_steel_tongue_drum | 2026-09-08 | **未取得原文**（四條路徑全 403，見 §5 缺口 1） | 摘要層級反覆出現「a simple model based on the vibration of a rod with fixed-free ends」與「R² = 0.9955」的字樣。若屬實，**會支持引擎現行的 fixed-free（懸臂）選擇**、削弱選項 4 的理由——但**我沒有打開原文，本卡不把它當證據**，只登記為必須先閉合的線索。 |

**§2 小結（可以拿去做判斷的三件事）**

1. 「近純正弦」在物理上**與軟槌一致**（證據 1）——引擎沒有算錯，是被餵了很軟的槌。
2. 真實鋼舌鼓/打擊棒的第二泛音在 **2×、3×、4×** 這種位置（**有給出數字的來源**：證據 3 木琴 3.00×／馬林巴 3.92×、
   證據 16、17 handpan 1:2:3、證據 18 廠商目標 1:2:3:4:5），引擎用的等截面懸臂梁是 **6.27×**——
   這個差異讓泛音一開始就落在軟槌頻譜的深谷裡，**兩個問題其實是同一件事的兩面**。
   （證據 7 RAV Vast 與證據 10 Hluru **只用文字說「泛音是基頻的整數倍」「八度與純五度」，沒有給任何數值比值**，
   2026-09-08 逐句複查後已從本條的數字依據中移除。）
3. 「高音舌片天生小 40 dB」**沒有任何一條外部證據支持**（證據 15 是弱反證，證據 14 未取得）。

---

## §3 引擎現況實測數字（全部可重跑）

重現腳本與原始輸出：`output\wf0907\R6\`（`EVIDENCE_LOG.txt` 有完整表格）。
探針設定：48 kHz、`master_volume 1.0`、`normalize=false`、reverb/delay/distortion 全 wet=0、
velocity 0.5、MIDI {37,47,57,67,77,87} 各間隔 8 秒、時長 6 秒；
舌片參數＝steel / 厚 2.6 mm / 長 100 mm / 寬 24 mm / strike 0.44（取自出貨的月光空靈鼓版樂譜）。

### 3.1 `--dump-modes`（模態表）

| MIDI | 基頻 Hz | 可渲染模態數 | 模態1振幅 | 模態2（頻率／振幅） | 模態1 T60 |
|---|---|---|---|---|---|
| 37 | 69.30 | 10 | 0.23200 | 434.3 Hz / 0.00746 | 68.68 s |
| 47 | 123.47 | 8 | 0.19351 | 773.8 Hz / 0.01100 | 37.39 s |
| 57 | 220.00 | 6 | 0.05308 | 1378.7 Hz / 0.00373 | 19.92 s |
| 67 | 391.99 | 4 | 0.00951 | 2456.6 Hz / 0.00197 | 10.25 s |
| 77 | 698.46 | 3 | 0.00804 | 4377.2 Hz / 0.00069 | 5.01 s |
| 87 | 1244.51 | 2 | 0.00456 | 7799.2 Hz / 0.00011 | 2.29 s |

- 懸臂梁模態比值 **1 : 6.2669 : 17.5475 : 34.386 : 56.843 …**，且在 score 路徑下**與音高無關**
  （`tuneChromaticModesToMidi()` 只把整組頻率同乘一個係數）。
- 模態1 振幅 37→87 掉 **34.13 dB**。

### 3.2 渲染後實測 RMS（dBFS）

| 量測窗 | 37 | 47 | 57 | 67 | 77 | 87 | 斜率 37→87 |
|---|---|---|---|---|---|---|---|
| 0.3 s | −35.99 | −37.68 | −49.11 | −64.46 | −66.72 | −73.30 | **37.31 dB** |
| 1.0 s | −36.30 | −38.23 | −50.10 | −66.22 | −69.75 | −77.78 | **41.48 dB** |
| 6.0 s | −38.33 | −41.51 | −54.96 | −72.71 | −77.25 | −85.55 | **47.22 dB** |
| 峰值 | −32.62 | −33.77 | −44.89 | −59.21 | −56.84 | −59.06 | 26.44 dB |

QA 記載的 40.3 dB 落在 0.3 s 與 1.0 s 窗之間，**現象完全重現**。
（絕對值與 QA 不同是因為我的探針用固定 velocity 0.5 與自訂長度/寬度，不是 QA 的原始探針；
斜率才是本案的量。）

### 3.3 敲擊工具掃描（唯一改的是 `exciter`，其他完全相同）

> **量測窗與幾何**：本節是**第一輪探針幾何**（厚 2.6 ／寬 24 ／strike 0.44）的 **1 s 窗** RMS 斜率。
> 若要看**月光樂譜自己的幾何**（厚 3.2 ／寬 30 ／strike 0.42、全檔 RMS），請看 §3.10——那組才是選項 1 的決策數字。

| 引擎 / exciter | 1 s RMS 斜率 37→87 | 基頻能量占比（MIDI 37 / 87） |
|---|---|---|
| tongue_drum `finger`（**出貨設定**） | **41.48 dB** | 99.28 % / 98.31 % |
| tongue_drum `felt` | 17.88 dB | 99.21 % / 99.15 % |
| tongue_drum `wood_mallet` | **5.53 dB** | 49.61 % / 99.14 % |
| tongue_drum `metal_mallet` | 5.24 dB | 42.45 % / 97.30 % |
| cimbalom `felt` | 22.78 dB | 50.57 % / 91.25 % |
| cimbalom `wood_mallet`（**揚琴出貨設定**） | 6.67 dB | 24.70 % / 74.63 % |

**這張表就是本案的關鍵**：出貨的揚琴樂譜寫 `wood_mallet`（實測 1142 事件中 400 件抽樣皆為
`wood_mallet`），空靈鼓樂譜寫 `finger`。同樣是 `wood_mallet`，兩個引擎的斜率是
**5.53 vs 6.67 dB——幾乎一樣**；同樣是軟槌，tongue 41.48、cimbalom 22.78。
**引擎之間並沒有 40 dB vs 4 dB 的體質差距，樂譜的 `exciter` 設定才有。**
（我的 cimbalom 對照組 6.67 dB 與 QA 記載的 4.4 dB 不完全相同，因為我的探針沒有沿用揚琴樂譜的
`damping_override: 0.4` 與逐音 velocity；差異方向與量級一致，結論不受影響。）

### 3.4 環節貢獻拆解（每一步都對得上 CLI 的 dump 到小數第 4 位）

我用 Python 完整複刻了 `BeamModel` + `HammerImpulse` + `loudnessCompensationGain` 的計算鏈，
複刻出來的模態1振幅與 CLI `--dump-modes` **逐音符吻合**（0.231998 vs 0.23200；0.004562 vs 0.00456）。
因此下表的歸因是可驗證的，不是估計：

| # | 環節 | file:line | 37→87 的貢獻 | 說明 |
|---|---|---|---|---|
| 1 | 舌片幾何／模態形狀振幅 | `src/physics/BeamModel.h:132-168` | **0.00 dB** | score 路徑的長寬厚由樂譜給定、**不隨音高變**，所以原始模態振幅六個音都是 0.292216。`geometryGain`（L163-168）在此路徑是常數。**這一項不是兇手。** |
| 2 | **槌頭力脈衝頻譜 `H(ω, τc)`** | `src/physics/HammerImpulse.h:154-170`，τc 由 `:138-141`＋`:128-136` 決定 | **−43.21 dB**（−4.97 → −48.17 dB） | **唯一的主因。** τc(MIDI 37)=10.84 ms、τc(MIDI 87)=4.30 ms。這個頻譜的轉折點在 1/(2τc)：MIDI 37 是 **46 Hz**，比它自己的基頻 69 Hz 還低——**連基頻都已經在滾降區**，泛音自然全滅。 |
| 3 | 跨音域響度補償 | `src/dsp/ModalResonator.h:159-167` | **+9.08 dB**（×1.41 → ×4.00） | 想救但救不動：**MIDI 57 以上全部撞到 ×4（+12.04 dB）上限**（L166 `jlimit(0.25f, 4.0f, g)`）。MIDI 87 若不夾住應為 **×90.99（+39.2 dB）**，等於**上限自己扣了 27.2 dB**。 |
| 4 | 20 kHz／Nyquist 模態截斷 | `src/dsp/ModalResonator.h:22, 42-49` | **< 0.1 dB**（對 RMS） | 模態數 10→2，但在 `finger` 設定下模態2 早就比模態1 低 30 dB，砍掉它對音量幾乎沒影響。**換成硬槌後這一項才會變重要**（見 §5）。 |
| 5 | T60 隨頻率縮短（D1 未溯源） | `src/physics/BeamModel.h:50-59` | **窗長相關：0 dB（0.3 s）→ +9.9 dB（6 s）** | T60(f0) 從 68.68 s 掉到 2.29 s。它不影響「敲下去那一瞬間多大聲」，但長窗量測時高音早就衰完了。註解自承 `*2` 是「全音域一律 2 倍過阻尼、不再有任何錨點理由」的純經驗係數。 |
| 6 | exciter 噪音爆與 body 層 | `src/engines/ChromaticEngine.h:535-548`、`:396-400` | 峰值層面可見（MIDI 77 峰值高於 67），對 RMS 斜率非主導 | CLI 路徑 body 預設 0.0，可排除。 |
| | **合計（模態1振幅）** | | **−34.13 dB** | 再加環節 5 → 1 s 窗實測 −41.48 dB。 |

> **行號基準（2026-09-08 第三輪重新核對，前一版此段有誤）**：上表行號取自**工作樹**。
> 三個 lane 同時在改這個工作樹，所以行號會漂移，實測如下：
> - `src/engines/ChromaticEngine.h`：工作樹相對 HEAD 有**整齊的 +1 行位移**
>   （`kChromaticAttackEnergyRefA4` HEAD `:35` ／工作樹 `:36`；`bp.length` HEAD `:177` ／工作樹 `:178`；
>   `bp.width` HEAD `:178` ／工作樹 `:179`；`loudnessCompensationGain` 呼叫 HEAD `:243` ／工作樹 `:244`）。
>   **前一版寫「L411 以前的錨點在 HEAD 與工作樹一致」是錯的**，已更正。
> - `src/score/ScoreRenderer.h`：`beam` 別名的兩處在 **HEAD 是 `:290`／`:817`**（本文採用的基準），
>   在**現在的工作樹已漂到 `:290`／`:1081`**（E9 lane 加了 layered dump 的註解區塊）。
> - `src/dsp/ModalResonator.h`、`src/physics/BeamModel.h`、`src/physics/HammerImpulse.h`
>   三個檔在工作樹**完全乾淨**（`git status --porcelain` 無輸出），行號 HEAD＝工作樹。
> 我用的 CLI 是 HEAD 建的 binary；因為 E5 的改動是純新增、不碰上述計算鏈，
> 我的 Python 複刻能逐音符對上 CLI 的 `--dump-modes`，可證明這條鏈在兩邊相同。

### 3.5 整首月光空靈鼓版 A/B（完整 327 秒，只換 `exciter`）

| 版本 | 全檔 RMS | 峰值 | <200 Hz | 200 Hz–2 kHz | >2 kHz |
|---|---|---|---|---|---|
| 出貨版（`finger`） | −35.58 dBFS | −21.56 dBFS | **97.36 %** | 2.64 % | 0.0001 % |
| 實驗版（`wood_mallet`） | −29.98 dBFS | −14.39 dBFS | **17.55 %** | **82.44 %** | 0.0154 % |

出貨版的 97.36 % / 幾乎 0 % 與 QA 記載的「97.4 % 在 200 Hz 以下、2 kHz 以上為 0」**完全對得上**，
證明我的量測鏈與 QA 一致。換槌後主旋律音域從 2.64 % 變成 82.44 %。

### 3.6 兩條路徑的差異（給稽核看的）

- **CLI／score 路徑**（`ChromaticEngine.h:298-400`）：舌片長寬厚**照樂譜寫的固定值**，不隨音高變。
- **外掛（VST3）路徑**（`ChromaticEngine.h:173-186`）：`bp.length = BeamModel::lengthFromMidiNote(midi) * sizeScale`（L178），
  寬固定 0.02 m、厚由旋鈕決定。長度縮短 → 質量變小 → `geometryGain`（`BeamModel.h:163-168`）在 MIDI 87 比 37 **高約 +6.2 dB**。
  也就是**外掛裡的高音會比 CLI 略大聲一點**，但 `H(ω,τc)` 的 43 dB 問題兩邊完全一樣。
  這也解釋了證據 8 的落差：真鼓調音要同時改「重量、寬度、長度」，引擎只改長度。

### 3.7 反事實模擬（模態1振幅斜率，同一套複刻計算）

| 假設 | 斜率 37→87 |
|---|---|
| 現況（finger + keytrack） | 34.13 dB |
| finger，但拿掉 `keytrackScale()` | **53.37 dB（更糟）** |
| 改 `felt` | 10.48 dB |
| 改 `wood_mallet` | −7.82 dB（高音反而較大） |
| 改 `metal_mallet` | −9.05 dB |
| 保持 finger，補償上限 ×4→×16 | 22.08 dB |
| 保持 finger，補償上限拿掉 | 6.99 dB |
| 保持 finger，補償 amount 1.0 且無上限 | −3.23 dB |

**重點**：`keytrackScale()` 目前是在**幫忙**（拿掉會更糟 19 dB），所以它不是兇手；
但它是**鋼琴槌**的經驗式（註解自承擬合 A0 4 ms → C8 0.8 ms），套在鋼舌鼓上沒有來源——見 §5。

### 3.8 corpus 影響範圍（**2026-09-08 修訂：舊版嚴重低估，實際是 43 檔**）

卡上寫的 `grep -l tongue_drum scores -r` **會漏掉大半**：`beam` 是同一顆引擎的**別名**
（`src/score/ScoreRenderer.h:290` 與 `:817` 兩處都是 `ev.engine == "beam" || ev.engine == "tongue_drum"`
→ `ChromaticSubEngine::TongueDrum`）。實際統計：

| 統計項 | 數字 |
|---|---|
| 用到這顆引擎的 `*.score.json` 檔 | **43** |
| 事件總數 | **2463**（別名 `tongue_drum` 2362 + 別名 `beam` 101） |
| 其中用**軟激發**（finger / finger_tap / cotton / felt / rubber / brush，即 τc ≥ 2 ms 檔位） | **2385（96.8 %）** |
| 檔案內容真的出現字串 `tongue_drum` 的檔 | 只有 8 |

**白話**：這顆引擎現在幾乎整個音效庫都在用，而且 96.8 % 的音都是用「軟到出不了泛音」的設定敲的。
**任何動到 `src/` 的修法都會一次改掉這 43 個檔的渲染輸出（Rule 10 全面觸發）。**

<details>
<summary>43 檔完整清單（點開）</summary>

| score 檔 | 事件數 | 引擎別名 | exciter | MIDI 範圍 |
|---|---|---|---|---|
| `scores/examples/moonlight_sonata_movement1_tongue_drum.score.json` | 1142 | tongue_drum×1142 | finger×1142 | 29–87 |
| `scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json` | 1142 | tongue_drum×1142 | finger×1142 | 29–87 |
| `scores/examples/rabbit_warning.score.json` | 2 | beam×2 | hard_plastic×2 | 88–91 |
| `scores/library/akashic/akashic_notify_001.score.json` | 2 | beam×2 | wood_mallet×2 | 88–93 |
| `scores/library/akashic/akashic_opening_bell_001.score.json` | 7 | tongue_drum×7 | finger×5, felt_mallet×2 | 62–76 |
| `scores/library/akashic/akashic_ui_001.score.json` | 1 | beam×1 | hard_plastic×1 | 96 |
| `scores/library/clockwork/clockwork_action_001.score.json` | 1 | beam×1 | metal_hammer×1 | 65 |
| `scores/library/clockwork/clockwork_ambient_001.score.json` | 6 | beam×6 | metal_tip×6 | 77 |
| `scores/library/clockwork/clockwork_loop_001.score.json` | 10 | beam×10 | metal_tip×10 | 77–88 |
| `scores/library/clockwork/clockwork_notify_001.score.json` | 1 | beam×1 | metal_hammer×1 | 76 |
| `scores/library/clockwork/clockwork_notify_var01.score.json` | 1 | beam×1 | metal_hammer×1 | 76 |
| `scores/library/clockwork/clockwork_transition_001.score.json` | 4 | beam×4 | metal_tip×4 | 60–72 |
| `scores/library/clockwork/clockwork_ui_001.score.json` | 1 | beam×1 | metal_tip×1 | 74 |
| `scores/library/forest/forest_action_001.score.json` | 2 | beam×2 | hard_strike×2 | 60–67 |
| `scores/library/forest/forest_ambient_001.score.json` | 6 | beam×6 | finger_tap×6 | 79–90 |
| `scores/library/forest/forest_loop_001.score.json` | 16 | beam×16 | finger_tap×16 | 78–90 |
| `scores/library/forest/forest_notify_001.score.json` | 2 | beam×2 | wood_mallet×2 | 95–100 |
| `scores/library/forest/forest_notify_var01.score.json` | 3 | beam×3 | hard_plastic×3 | 100–104 |
| `scores/library/forest/forest_transition_001.score.json` | 4 | beam×4 | brush×4 | 74–81 |
| `scores/library/forest/forest_ui_001.score.json` | 1 | beam×1 | wood_mallet×1 | 77 |
| `scores/library/ocean/ocean_loop_001.score.json` | 2 | beam×2 | finger_tap×2 | 79–81 |
| `scores/library/ocean/ocean_notify_001.score.json` | 1 | beam×1 | finger_tap×1 | 84 |
| `scores/library/ocean/ocean_notify_var01.score.json` | 1 | beam×1 | rubber_mallet×1 | 72 |
| `scores/library/ocean/ocean_transition_001.score.json` | 1 | beam×1 | cotton_mallet×1 | 74 |
| `scores/library/ocean/ocean_ui_001.score.json` | 1 | beam×1 | finger_tap×1 | 81 |
| `scores/library/rabbit/rabbit_ambient_001.score.json` | 5 | beam×5 | cotton_mallet×5 | 84–93 |
| `scores/library/rabbit/rabbit_loop_001.score.json` | 8 | beam×8 | hard_plastic×8 | 79–88 |
| `scores/library/rabbit/rabbit_notify_001.score.json` | 1 | beam×1 | wood_mallet×1 | 91 |
| `scores/library/rabbit/rabbit_notify_var01.score.json` | 1 | beam×1 | metal_mallet×1 | 91 |
| `scores/library/rabbit/rabbit_transition_001.score.json` | 3 | beam×3 | hard_plastic×3 | 84–93 |
| `scores/library/rabbit/rabbit_ui_001.score.json` | 1 | beam×1 | wood_mallet×1 | 81 |
| `scores/library/restraint/restraint_loop_001.score.json` | 4 | beam×4 | metal_tip×4 | 55–57 |
| `scores/library/restraint/restraint_notify_001.score.json` | 2 | beam×2 | metal_hammer×2 | 64–71 |
| `scores/library/restraint/restraint_notify_var01.score.json` | 2 | beam×2 | metal_hammer×2 | 64–71 |
| `scores/library/restraint/restraint_ui_001.score.json` | 1 | beam×1 | metal_tip×1 | 55 |
| `scores/originals/ai_radiance/ai_radiance_m1.score.json` | 16 | tongue_drum×16 | finger×16 | 78–80 |
| `scores/originals/ai_radiance/ai_radiance_m3.score.json` | 16 | tongue_drum×16 | finger_tap×16 | 77–88 |
| `scores/originals/ai_radiance/ai_radiance_m4.score.json` | 32 | tongue_drum×32 | finger_tap×24, metal_tip×8 | 77–89 |
| `scores/originals/rules_v2_demo/rules_v2_demo_001.score.json` | 6 | tongue_drum×6 | wood_mallet×6 | 96 |
| `scores/tests/test_distortion.score.json` | 1 | beam×1 | metal_hammer×1 | 60 |
| `scores/tests/test_distortion_bitcrush.score.json` | 1 | beam×1 | hard_plastic×1 | 76 |
| `scores/tests/test_engine_levels.score.json` | 1 | tongue_drum×1 | （未指定，預設 hardness 2.0 = wood） | 60 |
| `scores/tests/test_glide.score.json` | 2 | beam×2 | wood_mallet×1, finger_tap×1 | 67–84 |

</details>

（`scores/schema/score.schema.json`、`ai_radiance.catalog.json` 與兩個 `.report.html` 也含字串
"tongue_drum"，但不是事件來源，未列入。重跑腳本：`output\wf0907\R6\corpus_scope.py`。）

### 3.9 第二輪獨立複核（2026-09-08，不同幾何、不同探針、同結論）

第二位 Opus 用**另一組舌片參數**（steel ／厚 3.2 mm ／長 100 mm ／寬 30 mm ／strike 0.42
——同一首月光樂譜裡的另一組，佔 176 個事件）從頭重跑一次，velocity 0.5、6 秒、效果全關：

| 量測 | MIDI 37 | 47 | 57 | 67 | 77 | 87 | 斜率 37→87 |
|---|---|---|---|---|---|---|---|
| `--dump-modes` 模態1振幅 | 0.21730 | 0.18124 | 0.03943 | 0.00706 | 0.00597 | 0.00339 | **36.14 dB** |
| Python 逐段複刻的同一值 | 0.217301 | 0.181242 | 0.039431 | 0.007064 | 0.005972 | 0.003389 | 36.14 dB |
| 渲染 RMS（0–0.3 s 攻擊窗） | −36.56 | −38.25 | −51.69 | −66.89 | −69.32 | −75.70 | **39.14 dB** |
| 渲染 RMS（0–6.0 s 窗） | −38.90 | −42.08 | −57.55 | −75.24 | −79.84 | −87.98 | **49.08 dB** |
| 可渲染模態數 | 10 | 8 | 6 | 4 | 3 | 2 | — |
| `noteComp` 實際值 ／ 若不夾住應為 | 1.77 ／ 1.77 | 3.52 ／ 3.52 | **4.00 ／ 13.01** | **4.00 ／ 51.42** | **4.00 ／ 63.39** | **4.00 ／ 114.73** | — |

- **QA 原始數字被重現**：同樣的 0–0.3 s 攻擊窗下，cimbalom 對照組是 **4.44 dB**（QA 記載 4.4 dB）、
  tongue_drum 是 **39.14 dB**（QA 記載 40.3 dB）→ 可以確定 QA 當時用的就是攻擊窗量測，現象完全重現。
- **`noteComp` 從 MIDI 57 起就撞到 ×4 上限**，MIDI 87 需要 ×114.73 才夠 → **上限自己扣掉 29.2 dB**。
- **卡上「模態截斷造成近純正弦」的假設被證偽**：MIDI 37 明明有 **10 個**可渲染模態，
  基頻仍占 **99.88 %**。真正的原因是 `H(ω,τc)` 把模態2（6.27×f0）壓低 **29.3 dB**，
  跟模態夠不夠**無關**。模態截斷對 RMS 斜率的貢獻 < 0.1 dB。
- **高音的峰值其實是「敲擊噪音」不是樂音**：MIDI 87 用 `--no-exciter-noise` 重渲，峰值從
  −57.49 掉到 −69.38 dBFS（差 **11.9 dB**）→ 那顆音在成品裡聽到的主要是激發噪音爆，不是舌片。

### 3.10 跨引擎關鍵對照（2026-09-08 新增）——證明不是引擎體質差

同一支 CLI、同樣 velocity 0.5、同樣 6 秒、效果全關，**只換 `exciter`**
（**全檔 RMS**，dBFS；證據檔 [3][5][6]。註：證據檔 [4] 的固定 0–6.0 s 窗數字略有不同，
例如 td/finger MIDI 37 為 −38.90、斜率 49.08 dB——因為渲染檔尾端還有一小段尾音，兩者不是同一個窗）：

| 引擎 | exciter | MIDI 37 | 57 | 87 | 斜率 37→87 |
|---|---|---|---|---|---|
| cimbalom | `wood_mallet`（＝揚琴出貨設定） | −40.36 | −43.75 | −47.49 | **7.13 dB** |
| cimbalom | `finger`（＝空靈鼓出貨設定） | −39.86 | −44.14 | −63.27 | **23.41 dB** |
| tongue_drum | `wood_mallet` | −42.08 | −42.80 | −48.78 | **6.71 dB** |
| tongue_drum | `finger`（＝出貨設定） | −40.41 | −57.64 | −87.98 | **47.57 dB** |

**把 cimbalom 也換成 `finger`，它一樣壞掉（7.1 → 23.4 dB）。**
所以 `TODO.md` D8 記載的「tongue_drum 40 dB vs cimbalom 4.4 dB」**是被 exciter 設定混淆的比較**，
不是兩顆引擎的體質差距。

> **⚠ 2026-09-08 第四輪更正**：本節原本在這裡接了一句
> 「tongue_drum 剩下的那一截（47.6 vs 23.4 dB）才是梁模型自己的問題」——**該句已被證偽，予以刪除**。
> 原因是 cimbalom 的 `finger` 並不等於 tongue_drum 的 `finger`：兩張硬度表把同一個字分別翻成
> Felt（2.0 ms）與 Cotton（6.0 ms）（§3.12）。真正等價的對照是給 cimbalom 寫 `cotton_mallet`
> （同樣 6.0 ms 檔位、同樣走 `tauCForNote()`），實測 **43.18 dB（0.3 s 窗）／46.68 dB（6 s 窗）**，
> **比 tongue_drum 的 37.20／47.13 dB 沒有比較好**。
> 「梁在高音只剩 1–2 個模態」是事實（§3.1），但它對 **RMS 斜率**的貢獻 < 0.1 dB（§3.4 環節 4），
> 不能拿來解釋那一截差距。

### 3.11 第三輪獨立重跑（2026-09-08，第三位 Opus，全新探針與量測腳本）

不沿用前兩輪任何檔案，重新產生探針樂譜、重新渲染、重新寫量測腳本，同時跑**兩組幾何**
（g1＝厚 2.6／寬 24／strike 0.44，那首月光的 **952 事件主力幾何**；g2＝厚 3.2／寬 30／strike 0.42，176 事件）
與 cimbalom 對照組（steel／diameter 0.72／strike 0.28／`damping_override` 0.4，＝揚琴版 952 件設定）。
證據：`reports/gate_outputs/wf0907_R6_d8_evidence.txt` 的 `== [12] ==` 段。

| 探針 | 0–0.3 s 斜率 | 0–6.0 s 斜率 | 基頻占比（37／87） |
|---|---|---|---|
| tongue g1 `finger`（出貨） | **37.20 dB** | **47.13 dB** | 99.27 ／ 96.42 % |
| tongue g1 `felt` | 13.73 dB | 23.61 dB | 99.20 ／ 99.15 % |
| tongue g1 `wood_mallet` | **2.67 dB** | **8.32 dB** | 49.61 ／ 99.16 % |
| tongue g2 `finger` | 39.31 dB | 49.21 dB | 99.27 ／ 97.81 % |
| tongue g2 `felt` | 15.74 dB | 25.62 dB | 99.19 ／ 99.14 % |
| tongue g2 `wood_mallet` | 2.77 dB | 8.24 dB | 46.32 ／ 99.12 % |
| cimbalom `wood_mallet`（揚琴出貨） | **4.08 dB** | 4.98 dB | 33.33 ／ 75.77 % |
| cimbalom `finger` | **23.04 dB** | 24.42 dB | 51.29 ／ 88.97 % |

- **§3.1／§3.2／§3.3／§3.7／§3.8 全部重現**：`--dump-modes` 的模態1 振幅
  0.232／0.19351／0.05308／0.00951／0.00804／0.00456、模態2 比值恆為 **6.2669**、
  模態1 振幅斜率 finger 34.13 dB／felt 10.48／wood −7.82，與前輪**逐位相同**；
  corpus 重數同樣得 43 檔／2463 事件／軟激發 2385（96.83 %）／含字串 8 檔。
- **cimbalom 換 `finger` 一樣壞掉**（4.08 → 23.04 dB），第三度確認 §3.10 的跨引擎結論。
- **新發現（決策相關）**：`wood_mallet` 在**低音端會把基頻讓出去**。g1 MIDI 37 的
  **模態 2（6.27×f0 ＝ 434 Hz）振幅是模態 1 的 2.27 倍（+7.1 dB）**，MIDI 47 是 1.90 倍、57 是 1.23 倍；
  到 MIDI 67 以上才反過來（0.32 倍、0.20、0.084）。也就是說換硬槌把「高音太小聲」換成
  「低音的最強分音不是基頻」——這正是 A14「弱基頻」處理的那一類狀況。
  `felt` 沒有這個現象（MIDI 37 模態2／模態1 ＝ 0.068，−23.4 dB）。已寫進 §4 選項 1 的代價欄。

### 3.12 第四輪獨立重跑（2026-09-08，第四位 Opus）——含一條推翻既有結論的新對照

不沿用前三輪任何檔案：自己產探針樂譜、自己渲染、自己寫量測腳本、自己用 Python 從
`BeamModel` + `HammerImpulse` + `loudnessCompensationGain` 重寫一次計算鏈。
證據：`reports/gate_outputs/wf0907_R6_d8_evidence.txt` 的 `== [13] ==` 段。

**(a) 重現（全部相符）**

| 本文主張 | 第四輪獨立量到的 | 判定 |
|---|---|---|
| §3.1 模態1 振幅 0.23200／0.19351／0.05308／0.00951／0.00804／0.00456 | 逐位相同 | **相同** |
| §3.1 模態1 T60 68.68／37.39／19.92／10.25／5.01／2.29 s | 68.675／37.386／19.917／10.251／5.013／2.288 | **相同** |
| §3.1 懸臂比值 6.2669、與音高無關 | 六個音、四種 exciter、兩組幾何全部 6.2669 | **相同** |
| §3.2 g1 `finger` 0.3 s 窗 −35.99…−73.30 | −35.99／−37.68／−49.12／−64.30／−66.66／−73.20 | 差 ≤0.16 dB（`meta.id` 不同→噪音種子不同） |
| §3.3 g1 1 s 窗斜率 finger 41.48／felt 17.88／wood 5.53／metal 5.24 | 41.39／**17.88**／**5.53**／**5.24** | 相符（finger 差 0.09 dB） |
| §3.7 模態1 振幅斜率 finger 34.13／felt 10.48／wood −7.82／metal −9.05 | 34.13／10.48／−7.82／−9.05 | **逐位相同** |
| §3.4 環節 2（H 項）−43.21 dB、環節 3（補償）+9.08 dB、unclamped ×90.99 | −43.20／+9.08／×90.99 | **相同** |
| §3.8 corpus 43 檔／2463 事件／2362+101／軟激發 2385＝96.83 %／含字串 8 檔 | 43／2463／2362+101／2385＝96.83 %／8 | **逐項相同** |
| §3.9 g2 0.3 s 斜率 39.14／模態1 振幅 0.21730…0.00339 | 39.31／0.21730…0.00339 | 相符 |
| §3.11 g1 `wood_mallet` 低音模態2／模態1 ＝2.27／1.90／1.23／0.32／0.20／0.084 | 2.272／1.899／1.231／0.322／0.202／0.084 | **相同** |
| §3.5 整首 `finger` −35.58／−21.56／97.36 %／2.64 %／0.0001 % | −35.58／−21.56／**97.36 %**／2.64 %／0.0001 % | **逐位相同** |
| §3.5 整首 `wood_mallet` −29.98／−14.39／17.55 %／82.44 %／0.0154 % | −29.98／−14.39／17.53 %／82.46 %／0.0154 % | 相符 |
| §3.9 高音峰值主要來自激發噪音（`--no-exciter-noise` 差 11.9 dB，g2） | g1 MIDI 87 峰值 −56.92 → **−66.81**（差 **9.9 dB**） | 相符（幾何不同） |

**(b) 新發現 1（一級）：同一個字 `"finger"`，兩顆引擎翻成不同硬度**

`ScoreRenderer.h` 有**兩張**互相獨立的 exciter 對映表，同一個樂譜字串走不同分支：

| 樂譜寫的字 | cimbalom／piano 走 `cimbalomExciterFromString()`（HEAD `:1119-1151`，工作樹 `:1383-1397`） | tongue_drum／water_gong 走 `chromaticExciterHardness()`（HEAD `:1134-1148`，工作樹 `:1399-1413`） | 一致？ |
|---|---|---|---|
| `finger` / `finger_tap` | `ExciterType::Felt`（HEAD `:1125`）→ **τc 基準 2.0 ms**，且因為是 Felt 檔位而改走鋼琴槌氈非線性解算器 `pianoHammerTauC()`（`CimbalomEngine.h:275-278`） | `0.0f` ＝ Cotton（HEAD `:1138`）→ **τc 基準 6.0 ms**，走 `tauCForNote()` | **✗ 不一致（3 倍）** |
| `cotton` / `cotton_mallet` / `bow` / `bow_slow` / `brush` | Cotton | 0.0（Cotton） | ✓ |
| `felt` / `felt_mallet` / `rubber_mallet` | Felt | 1.0（Felt） | ✓ |
| `wood` / `wood_mallet` / `hard_plastic` / `pluck` / `hard_strike` | Wood | 2.0（Wood，落在預設分支） | ✓ |
| `metal` / `metal_mallet` / `metal_hammer` / `metal_scrape` | Metal | 3.0（Metal） | ✓ |
| `metal_tip` | **Wood**（落到預設分支） | 3.0（Metal） | ✗（corpus 34 事件，方向是「更硬」，非本案病灶） |
| `medium` | **Wood**（預設） | 1.0（Felt） | ✗（corpus 0 事件） |
| `sharp` | **Wood**（預設） | 3.0（Metal） | ✗（corpus 0 事件） |

實測 τc（velocity 0.5，本輪 Python 依 `HammerImpulse.h` 逐行複刻）：

| MIDI | tongue_drum `finger`（Cotton 6 ms） | tongue_drum `felt`（2 ms） | cimbalom `finger`＝`felt`（`pianoHammerTauC`） |
|---|---|---|---|
| 37 | **10.840 ms** | 3.613 ms | 3.008 ms |
| 57 | 7.490 ms | 2.497 ms | 2.334 ms |
| 87 | **4.302 ms** | 1.434 ms | 1.606 ms |

旁證：把同一支探針的 cimbalom 版本分別寫 `finger` 與 `felt`，六個音的 0.3 s／6 s RMS
**逐音相同到 0.01 dB**（0.3 s 窗：−29.64／−30.46／−31.79／−33.92／−42.85 對 −42.86／−50.29）→ 直接證明
在 cimbalom 上 `finger` 就是 `felt`。（兩檔 WAV 的 SHA256 仍不同，因為 `meta.id` 不同→激發噪音種子不同。）

**(c) 新發現 2（一級，推翻 §3.10 的尾巴）：等硬度對照下，揚琴比空靈鼓更糟**

同一支探針、同樣 velocity 0.5、效果全關，**唯一的變因是 exciter 檔位**：

| 引擎 | 樂譜寫的字 | 實際 τc 檔位 | 0.3 s 窗斜率 37→87 | 6 s 窗斜率 |
|---|---|---|---|---|
| tongue_drum g1 | `finger` | Cotton 6.0 ms | **37.20 dB** | 47.13 dB |
| **cimbalom** | **`cotton_mallet`** | **Cotton 6.0 ms** | **43.18 dB** | **46.68 dB** |
| cimbalom | `finger`（＝Felt） | Felt 2.0 ms（鋼琴解算器） | 20.65 dB | 23.57 dB |
| cimbalom | `felt` | 同上 | 20.65 dB | 23.57 dB |
| cimbalom | `wood_mallet`（揚琴出貨） | Wood 0.5 ms | 4.65 dB | 7.52 dB |
| tongue_drum g1 | `wood_mallet` | Wood 0.5 ms | 2.67 dB | 8.32 dB |

**在同一個接觸時間檔位下，兩顆引擎的斜率同級，甚至揚琴更差。**
所以「40 dB 是梁模型的體質」這個假設可以正式否定：**它是接觸時間律的產物，跟梁/弦無關。**
（本輪 cimbalom 探針**未**帶月光揚琴版的 `damping_override: 0.4`，所以絕對值與 §3.11 的
4.08／23.04 dB 略有差異；**同一支探針內部的檔位對照**才是本表要證明的事。）

**(d) 新發現 3（決策相關，修正選項 1 的期望值）：整首下來 `felt` 只走了約四分之一的路**

整首月光空靈鼓版（1142 事件、327 秒）重渲三個版本，只改 `params.exciter`，`normalize=false`：

| 版本 | 全檔 RMS | 峰值 | <200 Hz | 200 Hz–2 kHz | >2 kHz |
|---|---|---|---|---|---|
| 出貨（`finger`） | −35.58 dBFS | −21.56 dBFS | **97.36 %** | 2.64 % | 0.0001 % |
| **`felt`** | −31.62 dBFS | −17.30 dBFS | **78.06 %** | **21.94 %** | 0.0006 % |
| `wood_mallet` | −29.98 dBFS | −14.39 dBFS | **17.53 %** | **82.46 %** | 0.0154 % |

前三輪的 §4 把 `felt` 描述成「同樣把斜率從 40 dB 級拉到 14–26 dB、又沒有副作用」，
就**單音斜率**而言正確，但就**整首的能量分布**而言 `felt` 只把旋律音域從 2.64 % 拉到 21.94 %，
仍有 78 % 的能量壓在 200 Hz 以下。**這一格是月月做取捨時最該看的數字**，已補進 §4 選項 1。

---

## §4 選項與建議

> 先講白話：問題出在「用什麼東西敲」。現在樂譜寫的是「手指」，而引擎把「手指」翻譯成**很軟很軟的槌**
> （接觸 4–11 毫秒）。軟槌只把最低的那個音送出去，愈高的音愈送不出去。
> 換成「木槌」就好了，但那會讓月光空靈鼓版聽起來不一樣（那是音樂決定，不是技術決定）。

### 選項 1（推薦，成本最低）：只改樂譜的 `exciter`，程式一行不動

- **改哪裡**：`scores/examples/moonlight_sonata_movement1_tongue_drum.score.json`（1142 個事件）
  與 `scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json`（1142 個事件）
  的 `params.exciter`，`"finger"` → `"wood_mallet"`（或折衷用 `"felt"`）。
- **預期效果（實測，非估計；三輪、兩組幾何、三種量測窗）**：**兩組幾何都出自要改的那兩首月光樂譜本身**
  （厚 2.6 ／寬 24 ／strike 0.44 ＝ 952 事件 83.4 %；厚 3.2 ／寬 30 ／strike 0.42 ＝ 176 事件 15.4 %），
  結果一致，**不必挑哪一組**：

  | 幾何 | 量測窗 | `finger` | `wood_mallet` | `felt` | 出處 |
  |---|---|---|---|---|---|
  | 2.6／24／0.44 | 0–0.3 s | 37.20 | **2.67** | 13.73 | §3.11 |
  | 2.6／24／0.44 | 0–6.0 s | 47.13 | **8.32** | 23.61 | §3.11 |
  | 2.6／24／0.44 | 1 s（第一輪） | 41.48 | **5.53** | 17.88 | §3.3 |
  | 3.2／30／0.42 | 0–0.3 s | 39.31 | **2.77** | 15.74 | §3.11 |
  | 3.2／30／0.42 | 0–6.0 s | 49.21 | **8.24** | 25.62 | §3.11 |
  | 3.2／30／0.42 | 全檔 RMS | 47.57 | **6.71** | 24.12 | §3.10 |

  整首能量分布 97.4 % 在 200 Hz 以下 → 17.6 %，主旋律音域 2.6 % → 82.4 %；泛音也回來了
  （MIDI 37 基頻占比 99.3 % → 49.6 %）。
- **不需要新的溯源常數**（R4 不觸發）；**不改 `src/`**，所以 **Rule 6 的三 target 重建不觸發**。
- **會改變輸出的曲目**：只改上列兩首月光的話，就**只有這兩首**變——這是選項 1 最大的優點：
  波及面由月月逐檔決定，不像改 `src/` 會一次動到 §3.8 的全部 43 檔。
  若之後想把整個音效庫的軟激發也換掉，範圍是 §3.8 表中 exciter 欄含
  finger / finger_tap / cotton / felt / rubber / brush 的 **16 個檔、2385 個事件**——**建議分批、逐檔裁決**。
  **Rule 10 觸發**（渲染結果一定改變）→ 依規約必須停下，由月月裁決後才落地；本卡已附前後對照數字（§3.5）。
- **代價（兩項，第二項是 2026-09-08 第三輪新查出來的）**：
  1. 音色從「軟綿綿的手指觸感」變成「有金屬敲擊感」。**這是月月的美學決定，我不能替她決定。**
  2. **低音端的基頻會被讓出去**：換 `wood_mallet` 後，MIDI 37 的第二模態（6.27×f0 ＝ 434 Hz）
     **振幅變成基頻的 2.27 倍（+7.1 dB）**，MIDI 47 是 1.90 倍、57 是 1.23 倍（§3.11）。
     等於把「高音太小聲」換成「低音最強的分音不是基頻」——**這是 A14「弱基頻」那一類的問題**，
     不是白吃的午餐。低音區聽起來會偏「鐘／金屬棒」而不是「鼓」。
  **折衷選項 `"felt"`**：斜率 g2 全檔 24.12 dB／g1 第一輪 1 s 窗 17.88 dB／第三輪 g1 0.3 s 窗 13.73 dB、
  6 s 窗 23.61 dB——都遠好過 `finger`，**而且沒有上面第 2 點的副作用**
  （MIDI 37 模態2／模態1 只有 0.068）。代價是**泛音仍然沒回來**（基頻占比全音域 99 %）。
- **`felt` 的兩個新事實（2026-09-08 第四輪，會影響取捨）**：
  1. **整首下來 `felt` 只走了約四分之一的路**：重渲整首月光實測，200 Hz 以下能量
     `finger` 97.36 % → `felt` **78.06 %** → `wood_mallet` **17.53 %**；旋律音域（200 Hz–2 kHz）
     2.64 % → **21.94 %** → **82.46 %**（§3.12(d)）。單音斜率 `felt` 已經好很多，
     但整首的「低音壓住旋律」只緩解了一部分。
  2. **`felt` 其實才是這個字在本專案裡的既有解讀**：同一個 `"finger"` 在揚琴／鋼琴引擎
     早就被翻成 Felt（τc 3.0→1.6 ms），只有空靈鼓引擎把它翻成 Cotton（10.8→4.3 ms）（§3.12(b)）。
     所以把樂譜改寫成 `"felt"`（τc 3.6→1.4 ms）**等於讓空靈鼓拿到跟揚琴一樣的「手指」**——
     這是一個有原則的選擇，不只是折衷。
  **一句話取捨（第四輪更新）**：
  `felt` ＝「手指的觸感留著、旋律浮出來一部分（旋律帶 2.6 %→21.9 %）、基頻保住、沒有泛音」；
  `wood_mallet` ＝「旋律完全浮出來（→82.5 %）、泛音回來，但低音的最強分音變成第二模態、聽起來偏鐘」。

### 選項 2：承認「`finger` 檔位的 τc 未溯源」，把 Chromatic 的槌具接觸重新標定（正統解，但擋在 D2）

- **改哪裡**：`src/physics/HammerImpulse.h:76-79`（四檔 τc 常數）與 `:128-141`（keytrack 與組合式）
  對 **Chromatic 路徑**的取值；或在 `src/score/ScoreRenderer.h:1135-1149` 為 tongue_drum 建立獨立的硬度→τc 對照。
- **問題**：現行四個 τc 值**沒有一個來自鋼舌鼓量測**（`HammerImpulse.h:32-63` 註解自承），而且來源還不同質：
  Cotton 6.0 ms／Felt 2.0 ms／Wood 0.5 ms 三檔引的是**鋼琴槌氈**的量測與範圍
  （Askenfelt & Jansson, KTH；Chaigne & Askenfelt）；
  Metal 0.2 ms 則**不是鋼琴文獻**——註解自承是依 Fletcher & Rossing《The Physics of Musical Instruments》Ch.12
  「槌頭越硬、接觸時間越短」的**一般性描述**推導出來的，並明寫「本檔案未能取得該書 Table 12.1 逐項數值，
  此值……非直接抄錄書中數字」。
  `keytrackScale()` 則是**鋼琴全鍵盤擬合**（`:113-127` 註解自承 A0 4 ms → C8 0.8 ms）。
  鋼舌鼓玩家是**同一根手指／同一支槌敲每一片舌**，鋼琴那種「高音槌比較輕」的 keytrack **在物理上不適用**。
- **需要新溯源常數 → R4 直接擋住**：鋼舌鼓的手指／橡膠槌接觸時間，`TODO.md` D2 明載「未搜尋／狀態未知」，
  本卡也沒查到（§5）。**在拿到量測之前不能填數字。**
- **建議**：不要現在做。先做選項 1 解商品線，把這條列為 D2 的子項。

### 選項 3：放寬 `loudnessCompensationGain` 的 ±12 dB 上限

- **改哪裡**：`src/dsp/ModalResonator.h:166` 的 `juce::jlimit (0.25f, 4.0f, g)`。
- **預期**：上限改 ×16 → 斜率 34.13 → 22.08 dB；完全拿掉 → 6.99 dB（皆為模態1振幅斜率）。
- **不建議**。理由三點：
  1. 這是**補償**不是物理修正，等於用一個更大的補丁蓋住一個模型錯誤（軟槌）；
  2. 上限存在的理由（`src/dsp/ModalResonator.h:155` 註解）是「防止病態模態組合爆增益」，MIDI 87 只剩 2 個模態正是那種病態情況，
     拿掉上限會讓一個只剩兩根正弦的音被放大 91 倍；
  3. 會同時改變 water_gong 與所有既有 corpus 的渲染結果 → 大規模 Rule 10。
- 唯一可考慮的變體：**只在補償被夾住時發出診斷警告**（不改音訊），讓將來的 QA 能自動看見「這個音的補償已飽和」。
  這是純新增，不改既有輸出，可獨立提案。

### 選項 4：換掉梁模型的模態比值（真正的物理升級，最貴）

- **改哪裡**：`src/physics/BeamModel.h:88-97`（懸臂特徵值表）＋ `calculateModes()`。
- **為什麼**：真實鋼舌鼓／打擊棒的第二泛音被調到 **2×／3×／4×**
  （有給出數字的來源：證據 3、16、17、18；證據 7、10 只有文字描述、無數值比值，已不列入），
  引擎的等截面懸臂梁是 **6.27×**。6.27× 幾乎必然落在任何軟槌頻譜的深谷裡——
  **這是「換硬槌才有泛音」的深層原因**。
- **代價**：需要「變截面（undercut）梁」或「加質量塊」的模型與**對應的量測資料**（D4/D7 都沒關）。
  會改變所有 tongue_drum 曲目 → Rule 10 全面觸發。
- **建議**：列為長期項，不在本輪。

### 選項 5（2026-09-08 第四輪新增）：把 `finger` 的跨引擎對映統一（小改動、大波及面）

- **改哪裡**：`src/score/ScoreRenderer.h` 的 `chromaticExciterHardness()`
  （HEAD `:1134-1148`，工作樹 `:1399-1413`）——把 `finger` / `finger_tap` 從 `0.0f`（Cotton）
  改成 `1.0f`（Felt），與同檔 `cimbalomExciterFromString()`（HEAD `:1125`）已有的解讀一致。**一行。**
- **為什麼這是「參數化不一致」而不是物理**：`"finger"` 是同一份樂譜語彙裡的同一個字，
  卻在兩顆引擎被翻成差 3 倍的接觸時間（§3.12(b)）。**沒有任何來源說手指敲鋼舌鼓比敲揚琴軟 3 倍**——
  兩張表都是專案自己寫的映射，其中一張沒有理由。
- **預期效果**：等同於把全 corpus 裡 2372 個 `finger`/`finger_tap` 事件一次改成 `felt` 的效果
  （單音斜率 40 dB 級 → 14–26 dB；整首月光 200 Hz 以下 97.4 % → 78.1 %）。
- **不需要新的溯源常數**（R4 不觸發）——它只是選用已經在用的 `kTauCFelt`，不新增數字。
- **代價（大）**：**改 `src/` → Rule 6 三 target 重建 + Rule 10 全面觸發**，一次改掉 §3.8 的
  **43 個 score 檔／2372 個事件**的渲染輸出，位元不變證明必然失敗。
  相對地，選項 1 只改月月點名的檔案，波及面完全可控。
- **建議**：**先做選項 1**（樂譜層、逐檔可控）。選項 5 登記為「等商品線穩定後、和 D2 重新標定
  一起做的一次性收斂」，**不要為了省事現在改**。若月月只想要「以後新寫的樂譜不要再踩」，
  更便宜的做法是改文件與 converter 預設，不動引擎。

### 我的建議（一句話）

**做選項 1（只改那兩首月光樂譜的 `exciter`），把選項 2／4／5 掛到 D2／D4 底下當長期項，不要動選項 3。**
**`felt` 與 `wood_mallet` 兩版之間，我建議先試 `felt`**——它同樣把斜率從 40 dB 級拉到 14–26 dB，
又不會像 `wood_mallet` 那樣讓低音的基頻失去主導（§3.11 第三點），
而且它就是本專案的揚琴／鋼琴引擎對 `"finger"` 已有的解讀（§3.12(b)）；
**但第四輪要誠實補一句**：整首下來 `felt` 只把旋律音域從 2.6 % 拉到 21.9 %（`wood_mallet` 是 82.5 %），
所以「聽得見旋律」的程度是**部分改善**，不是全解。
若月月聽完覺得「還是不夠出來／還是要有泛音」，再換 `wood_mallet`。
兩版都是改樂譜、不改程式，隨時可以互換。

### 我認為「明顯是模型套錯」的一點（仍留給月月裁決）

`HammerImpulse::keytrackScale()`（`src/physics/HammerImpulse.h:128-136`）是**鋼琴槌質量隨音域遞減**的擬合式
（註解自承「高音區的槌頭更輕、氈更硬」）。鋼舌鼓沒有一排槌，玩家用**同一根手指**敲每一片舌，
所以「τc 隨音高變」在這件樂器上**沒有物理依據**。
不過它目前是在**幫忙**（拿掉會讓斜率從 34 惡化到 53 dB，§3.7），所以**不能單獨拿掉**——
必須跟選項 2（重新標定 τc）綁在一起做。**證據是註解本身＋§3.7 的反事實數字；仍請月月裁決。**

---

## §5 已知缺口（誠實登記，R4）

1. **ICSV27 2021 鋼舌鼓全文仍未取得**（= `TODO.md` D4）。本輪試了四條路徑：機構庫直連 403、
   ResearchGate 作者自存版 403、CORE 403、scholar.archive.org 500。搜尋引擎摘要裡出現的
   「G4 392 Hz + 泛音 1179/1960/2745/3531 Hz」與「R²=0.9955 長度-頻率式」**我沒有核到原文，本卡不採用**。
   這是目前唯一能直接證偽／證實「懸臂 6.27× 是否貼近真鼓」的量測。
2. **Morrison & Rossing (2007) Hang 論文全文未取得**（academia.edu/ResearchGate 皆 403）。
3. **鋼舌鼓的手指／橡膠槌接觸時間（τc、K、α）完全查不到**——與 `TODO.md` D2 記載一致。
   選項 2 沒有這個就不能做（R4）。
4. **社群證據整段缺席**：本環境 WebFetch 對 `www.reddit.com` / `old.reddit.com` 一律 "unable to fetch"，
   `.json` 端點與 `site:reddit.com` 搜尋都失敗。因此「高音舌片是不是玩家公認比較小聲」**沒有可引用的社群原文**。
   唯一相關的是證據 15 的**否定結果**（一份專講高音技巧的教學文完全沒提高音天生小聲），強度弱。
5. **梁／板阻尼未溯源**（= `TODO.md` D1）：`BeamModel::decayTimeForFrequency()` 的 `*2` 加權，
   註解自承是「全音域一律 2 倍過阻尼、不再有任何錨點理由」的純經驗係數。
   它讓 MIDI 37 的 T60 = **68.68 秒**——我查到的鋼舌鼓延音數字全部來自廠商/AI 生成頁面，
   **沒有一份是可引用的量測**，所以「68.68 s 是否離譜」我只能說「看起來偏長但無法舉證」。
6. **本卡沒有做位元不變證明**（`reports/gate_outputs/b6_method/render_b6_scores.py`）——
   因為本卡完全沒有碰 `src/`，依共同規約 §3 該檢查只針對「碰到 `src/` 的卡」。
   若月月採納選項 1（改樂譜），**那張卡必須自己做前後對照與 Rule 10 停手流程**。
7. **鋼舌鼓「切口舌片」的真實模態比值仍無 A 級量測**：本卡拿到的 1:2:3（證據 16、17）是 **handpan（Hang）**
   的量測，那是「碟形殼上的凹陷音區」，**不是切口舌片**，不能直接當鋼舌鼓舌片的目標比值。
   1:2:3:4:5（證據 18）與「八度＋純五度」（證據 10）都是**廠商說法**，不是量測。
   唯一針對切口舌片的量測（ICSV27 那篇）本輪仍 403。→ **選項 4 目前沒有可用的目標比值，不能開工。**
8. **ICSV27 摘要層級出現的「fixed-free rod」線索未能核實**（2026-09-08 第三輪）：多個搜尋引擎摘要都出現
   「a simple model based on the vibration of a rod with fixed-free ends」。若屬實，**這會反過來支持引擎
   現行的懸臂（fixed-free）邊界選擇、削弱選項 4 的理由**——但原文四條路徑全 403，**我沒有核到，
   本卡不採用**。這是本案性價比最高的一條待補：它同時決定選項 4 該不該做。
9. **「某些音特別小聲」在真實樂器上的量化資料仍缺**：找到的最接近來源（證據 20，調音師部落格）
   只說「受影響的音明顯比較小聲」並歸因於聲阻抗／干涉，**全篇沒有任何 dB 或 Hz 數字**，
   只能支持「這被當成缺陷」的方向，不能拿來判斷 40 dB 是否離譜。
10. **QA 原始探針未取得**：`exports/products/moonlight_batch1/` 底下只有 log 與成品，沒有 QA 當時的探針 score，
   所以我的絕對 dBFS 與 QA 的 −32.8/−73.1 不同（我用固定 velocity 0.5 與自訂幾何）。
   **可交叉驗證的是整首月光的頻譜分布：97.36 % vs QA 的 97.4 %，一致。**
11. **（2026-09-08 第四輪新增）`finger` 對映不一致，但沒有任何一邊有來源**：`ScoreRenderer.h` 的兩張表
   把同一個字翻成 Cotton（6 ms）與 Felt（2 ms）（§3.12(b)）。**我查不到任何量測說「手指敲鋼舌鼓的接觸時間」是多少**
   （＝ `TODO.md` D2 的缺口），所以我**無法說哪一邊才是對的**——只能說「兩邊不可能同時對」。
   選項 5 因此只是「讓兩邊一致」，不是「改成正確值」；真正的正確值仍要等 D2 的量測。
12. **（第四輪新增）另外三個字也對映不一致**：`metal_tip`（cimbalom→預設 Wood／chromatic→Metal，corpus 34 事件）、
   `medium`、`sharp`（皆 cimbalom→預設 Wood／chromatic→Felt、Metal，corpus 0 事件）。
   **不是本案病灶**（方向都是「更硬」，不會造成本案的低通問題），但既然量到就登記，供未來收斂表格時一併處理。

---

## 附錄 A：來源清單（存取日期逐條標示：初版 2026-09-07；第二／三輪新增或重驗者標 2026-09-08）

**A 級（物理證據）**

1. Euphonics, §3.3 *Marimbas and xylophones*（Jim Woodhouse）— https://euphonics.org/3-3-marimbas-and-xylophones/ — 已取得原文
2. *Experimental characterization of the steel tongue drum*, ICSV27, Prague 2021 —
   https://unige.iris.cineca.it/bitstream/11567/1063604/1/full_paper_1117_20210430223100647.pdf — **未取得原文（403）**
3. Morrison & Rossing, *Modes of vibration and sound radiation from the Hang*, Archives of Acoustics 32(3) 551–560 (2007) —
   https://www.academia.edu/96431023/Archives_of_Acoustics_32_3_551_560_2007_Modes_of_Vibration_and_Sound_Radiation_from_the_Hang — **未取得原文（403）**

3b. Morrison & Rossing, *The extraordinary sound of the hang*, **Physics Today 62(3), 66–67（2009-03-01）** —
   https://physicstoday.aip.org/quick-study/the-extraordinary-sound-of-the-hang — **已取得原文（2026-09-08）**

3c. McGill MUMT307 專題頁（二手引用 3b） — https://carrieeex.github.io/MUMT307-project/ — 已取得原文（2026-09-08）

**B 級（製造商／百科，工程慣例）**

4. RAV Vast, *Main Terms in the World of Steel Tongue Drum* — https://ravvast.com/blogs/news/main-terms-in-the-world-of-steel-tongue-drum — 已取得原文
5. Hluru, *The Professional Guide to Steel Tongue Drums* — https://www.hluru.net/en-us/blogs/skills-tips/the-professional-guide-to-steel-tongue-drums-decoding-materials-acoustics-and-quality — 已取得原文
6. Hluru, *Beginner's Guide to Steel Tongue Drum Music* — https://www.hluru.net/en-us/blogs/skills-tips/beginners-guide-to-steel-tongue-drum-music-rhythm-resonance-flow — 已取得原文
7. Wikipedia, *Steel tongue drum* — https://en.wikipedia.org/wiki/Steel_tongue_drum — 已取得原文

7b. Kosmosky, *Steel tongue drums' overtones*（Alexey Zinchenko, 2021-05-07） — https://en.kosmosky.com/news/overtones — 已取得原文（2026-09-08）

7c. Panda Drum, *How Does a Steel Tongue Drum Work?* — https://pandadrum.com/blogs/calm-panda-blog/how-does-a-steel-tongue-drum-work — 已取得原文（2026-09-08）

7d. Tapadum, *Steel Tongue Drum Buyer's Guide* — https://tapadum.com/steel-tongue-drum-buyers-guide/ — 已取得原文（2026-09-08）；
   引述："Rubber-tipped mallets give a brighter attack"（軟硬槌差異方向與引擎一致）

7f. Handpan.World, *Sound impedance: The enemy of perfect handpan tuning*（2024-05-13，調音師部落格） —
   https://www.handpan.world/en-us/blogs/handpan-tuning-nachstimmen-klangoptimierung/sound-impedance-the-fine-of-perfect-handpan-tuning
   — 已取得原文（2026-09-08）；引述："Betroffene Töne klingen deutlich leiser"（受影響的音明顯較小聲）。
   頁面**無任何 dB／Hz 數值**，只支持「音量明顯不均被業界視為缺陷」的方向。

7e. UBC PHYS341 wiki, *glockenspiel* — https://wiki.ubc.ca/Course:PHYS341/Archive/2016wTerm2/glockenspiel — 已取得原文（2026-09-08）；
   引述："These overtones are generally not harmonic"（金屬棒泛音非諧，支持「舌鼓應有非諧泛音」的前提）

**C 級（社群／使用者觀感）**

8. Sound Artist, *Handpan Techniques: How to Master Playing High Notes*（2024-09-12）— https://thesoundartist.com/blogs/news/handpan-techniques-how-to-master-playing-high-notes — 已取得原文（否定結果）
9. Sound Artist, *The Acoustics of Handpan & Hang Drum* — https://thesoundartist.com/blogs/news/acoustics-of-the-handpan-hang-drum — 已取得原文
10. r/handpan、r/tonguedrum、r/percussion — **未取得原文（本環境無法連線 reddit）**
11. JSouthAudio, *Modal Analysis of a "Tongue Drum"* — https://jsouthaudio.com/modelling-simulations/modal-analysis-of-a-tongue-drum/ — 已取得原文（2026-09-08 複查）。頁面**有**幾何與材料常數（"20cm in diameter, 10cm high and 3mm thick"、Young's modulus 180e9 Pa、Poisson 0.265、density 8000 kg/m³、頻率搜尋範圍 100–5000 Hz），但**沒有任何模態頻率或振幅結果**（只有模態振型動畫），因此對本案（要的是比值與相對響度）不採用

## 附錄 B：本卡產生的檔案（全部在 gitignore 的 `output\` 底下）

```
output\wf0907\R6\EVIDENCE_LOG.txt            ← 完整數字表（本文 §3 的來源）
output\wf0907\R6\probe_tongue.score.json     ← 探針樂譜（finger）
output\wf0907\R6\probe_cimbalom.score.json   ← 對照組樂譜
output\wf0907\R6\r6_tongue_felt|wood|metal.score.json
output\wf0907\R6\r6_cimb_wood|finger.score.json
output\wf0907\R6\r6_moonlight_tongue_base|wood.score.json  ← 整首 A/B（複製自 scores/，原檔未動）
output\wf0907\R6\*.wav / *.wav.render.json   ← 渲染產物與溯源清單
output\wf0907\R6\dump_tongue.txt / dump_cimbalom.txt
output\wf0907\R6\measured.json / windows.json / exciter_sweep.json / partial_energy.json
```

**2026-09-08 第二輪另外產生**（同樣在 gitignore 的 `output\` 底下）：

```
output\wf0907\R6\scores\d8_{td,cb}_{37,47,57,67,77,87}.score.json    第二輪探針樂譜
output\wf0907\R6\scores_ex\d8ex_{cotton,felt,wood,metal}_*.score.json exciter 掃描
output\wf0907\R6\scores_cb\d8cb_{finger,wood}_*.score.json           跨引擎對照
output\wf0907\R6\render\  render_ex\  render_cb\  render_nonoise\  渲染產物
output\wf0907\R6\modes_d8_*.json                                    --dump-modes 原始輸出
output\wf0907\R6\replicate_beam.py / counterfactual.py              Python 逐段複刻與反事實
output\wf0907\R6\measure.py / measure_ex.py / corpus_scope.py        量測腳本
output\wf0907\R6\D8_packet_backup_20260908_102753.zh-TW.md           修訂前的初版備份
```

**進版控的證據檔**：`reports/gate_outputs/wf0907_R6_d8_evidence.txt`
（[1]–[10] 為 2026-09-08 第二輪：含 CLI 的 SHA256、探針樂譜全文與各段完整輸出；
**[11] 為 2026-09-08 補進版控的第一輪數字表**——本文 §3.1／§3.2／§3.3／§3.4／§3.5／§3.7 的來源，
原本只存在於 gitignore 的 `output\wf0907\R6\EVIDENCE_LOG.txt`，複核指出後已整段複製進版控）。
**可稽核性的誠實說明**：第二輪 [1]–[10] 附了逐條命令、可原樣重跑；
第一輪 [11] 進版控的是**數字表**（探針幾何與設定都寫在表頭），腳本仍留在 gitignore 的 `output\` 底下——
要完全重跑第一輪需照表頭參數重建探針樂譜。第二位複核者已用該表頭參數獨立重跑並確認數字可重現。

**2026-09-08 第三輪另外產生**（同樣在 gitignore 的 `output\` 底下）：

```
output\wf0907\R6\verify3\gen.py            ← 全新探針產生器（兩組幾何 × 三種 exciter + cimbalom 對照）
output\wf0907\R6\verify3\measure.py        ← 全新量測腳本（0.3 s / 6.0 s 窗 RMS、峰值、基頻占比）
output\wf0907\R6\verify3\corpus.py         ← 全新 corpus 重數腳本
output\wf0907\R6\verify3\scores\*.score.json、render\*.wav、dump_g1_*.json、measure.json
output\wf0907\R6\verify3\D8_packet_backup_20260908_152613_round3.zh-TW.md  ← 第三輪修訂前備份
output\wf0907\R6\verify3\evidence_backup_20260908_152613_round3.txt        ← 證據檔修訂前備份
```

**2026-09-08 第四輪另外產生**（同樣在 gitignore 的 `output\` 底下）：

```
output\wf0907\R6\verify4\scores\d8r4_{g1,g2}_{finger,felt,wood_mallet,metal_mallet}.score.json
output\wf0907\R6\verify4\scores\d8r4_cb_{finger,felt,cotton_mallet,wood_mallet}.score.json  ← 等硬度跨引擎對照
output\wf0907\R6\verify4\dump_d8r4_*.json        ← --dump-modes 原始輸出
output\wf0907\R6\verify4\render\*.wav            ← 探針渲染
output\wf0907\R6\verify4\render_nonoise\*.wav    ← --no-exciter-noise 隔離
output\wf0907\R6\verify4\moon\d8r4_moon_{base,felt,wood}.{score.json,wav}  ← 整首 A/B/C（複製自 scores\，原檔未動）
output\wf0907\R6\verify4\measure4.json
output\wf0907\R6\verify4\D8_packet_backup_round4_20260908_202659.zh-TW.md  ← 第四輪修訂前備份
output\wf0907\R6\verify4\evidence_backup_round4_20260908_202659.txt        ← 證據檔修訂前備份
```

**沒有動過**：`src/`、`tools/`、`scores/`、`ROADMAP_PHYSICS.md`、`scores/crossplatform_tolerance.json`。
**沒有執行過**：任何 `git commit` / `git push` / `git checkout` / `git stash` / `git reset`，
也沒有對 `build\` 跑過 cmake。

---

## 複核修正記錄（2026-09-07）

> 第三位 Opus 的**引用複核**回報了 7 條 findings（1 blocker、2 major、4 minor）。
> 以下逐條列出「複核說什麼 → 我親自查證的結果 → 這份文件實際改了什麼」。
> **本輪同樣沒有碰 `src/`、`tools/`、`scores/`，沒有 commit／push，沒有對 `build\` 跑 cmake。**

| # | 級別 | 複核指出的問題 | 我的查證 | 實際修正 |
|---|---|---|---|---|
| 1 | **blocker** | §2 證據 10（Hluru）的「意義」欄自己加了「（比值 2 與 3）」，但該頁沒有任何數值比值；§2 小結 2 與 §4 選項 4 又把「第二泛音在 2×／3×／4×」同時標成「（證據 3、7、10）」，而證據 7（RAV Vast）整頁也沒有比值。 | **成立。** 2026-09-08 我自己重新 WebFetch 兩頁逐句要求列出數值比值：Hluru 回「does **not** state any numeric ratios such as 2:1, 3:1, 3:2, or 1:2:3」，只用音程名稱（"the primary overtones (the octave and the perfect fifth) must also be perfectly aligned"）。RAV Vast 回「No numeric ratios (2x, 3x, 1:2:3, etc.) are provided」，最接近的一句只到 "harmonics are vibrations at whole-number multiples of the fundamental frequency"。 | ①證據 10 的「（比值 2 與 3）」**刪除**，改成明寫「該頁只用音程名稱、全篇沒有任何數值比值；八度＝2×、純五度＝1.5× 是音程定義換算，不是這個來源說的」。②§2 小結 2 與 §4 選項 4 的括號改成**只列真的給出數字的來源**：證據 3（Euphonics 木琴 3.00×／馬林巴 3.92×）、16、17（handpan 1:2:3）、18（廠商 1:2:3:4:5），並明寫證據 7、10 已被移出數字依據。③接手的四條來源我 2026-09-08 也各自重驗過：Physics Today 回 "The frequencies of those modes are in the ratio of 1:2:3"；Kosmosky 回 "consist in the correct proportions of 1:2:3:4: 5"，皆與原引述一致。 |
| 2 | major | §0 第 35、36 行有兩處 code span 內容被吃掉，句子讀不通（「也改成 ，」「所以  D8」）。 | **成立。** 以 UTF-8 讀原檔逐行檢查確認是檔案本身缺字，不是終端編碼；同時我全檔掃了一次同型缺塊，**只有這兩處**。 | 補回 `finger` 與 `TODO.md`：「也改成 `finger`，它的斜率一樣從 7.1 dB 惡化到 23.4 dB」「所以 `TODO.md` D8 記載的……」。 |
| 3 | major | §4 選項 2 寫「現行四個 τc 值的來源全是鋼琴槌氈文獻」，與註解本身不符——Metal 檔自承來源是 Fletcher & Rossing 對打擊槌硬度-接觸時間的一般性描述，且明說非直接抄錄書中數字。 | **成立。** 親自開 `src/physics/HammerImpulse.h:57-63` 確認原文：Metal 0.2 ms「順序依據 Fletcher & Rossing … 一般性描述……本檔案未能取得該書 Table 12.1 逐項數值，此值為在該硬度排序下、緊貼 Wood 值以下的文獻指導推導，非直接抄錄書中數字」。Cotton/Felt/Wood 三檔才是 Askenfelt & Jansson／Chaigne & Askenfelt 的鋼琴槌氈來源。 | §4 選項 2 改寫為「四個 τc 值**沒有一個來自鋼舌鼓量測**，而且來源不同質」，分開列 Cotton/Felt/Wood（鋼琴槌氈量測）與 Metal（F&R 一般性描述下的推導、非抄錄）。**論點方向不變**（都不是鋼舌鼓的量測，選項 2 仍被 R4 擋住），但不再把 Metal 的來源說錯。 |
| 4 | minor | 四個 file:line 錨點有 1–2 行偏移：§3.6 的 L178、證據 19 的 :179、§4 選項 3 的「註解 L157」、§4 選項 2 的「:107-127」。 | **兩條成立、兩條不成立。** 我用 `awk NR` 對現行工作樹逐行核對：`bp.length = BeamModel::lengthFromMidiNote (midiNoteNumber) * sizeScale;` **確實在 `ChromaticEngine.h:178`**、`bp.width = 0.02f;` **確實在 :179**——這兩處原文就是對的，複核的 177／178 是誤判，**不改**。另兩條成立：clamp ±12 dB 的理由註解在 `ModalResonator.h:155`（:157 是 relative_modal_amplitude 那句）；`keytrackScale()` 的註解區塊是 `HammerImpulse.h:113-127`（:107 是 `tauCForStrike` 的函式體）。 | 改 §4 選項 3 的「註解 L157」→「`src/dsp/ModalResonator.h:155` 註解」；改 §4 選項 2 的「:107-127」→「:113-127」。§3.6 的 L178 與證據 19 的 :179 保持原樣（已複驗為正確）。核心錨點（`ModalResonator.h:166` 的 `jlimit(0.25f,4.0f,g)`、`HammerImpulse.h:76-79` 四個 τc、`ScoreRenderer.h:290/:817` 的 `beam` 別名）複核與我皆確認無誤。 |
| 5 | minor | §0 與 §4 選項 1 的招牌數字「41.5 → 5.5 dB」用的是第一輪探針幾何（厚 2.6／寬 24／strike 0.44），不是選項 1 要改的那兩首月光樂譜自己的幾何（厚 3.2／寬 30／strike 0.42）；同幾何實測是 47.57 → 6.71 dB。 | **成立。** 對照進版控的證據檔：`[3]` td（3.2／30／0.42）全檔 RMS 斜率 47.57 dB、`[5]` 同幾何 wood 6.71 dB／felt 24.12 dB；第一輪的 41.48／5.53 是 2.6／24／0.44 的 1 s 窗值。方向與量級一致，**結論不受影響**，但決策數字該用要改的那兩首自己的參數。 | §0 改為「斜率就從 **47.6 dB 掉到 6.7 dB**」並標明幾何與量測窗，同時保留第一輪 41.5 → 5.5 的出處；§4 選項 1 改為「**47.57 dB → 6.71 dB**（`felt` 24.12 dB）」並註明「決策請看前者」，第一輪數字降為附註。另**順手修正 §3.10 的表頭標籤**：那張表的數字取自證據檔 [3][5][6]，是**全檔 RMS**，不是原本寫的「0–6.0 s 窗」（[4] 的 0–6.0 s 窗另有一組略不同的數字，已在表頭註明差異來自檔尾尾音）。 |
| 6 | minor | 進版控的證據檔只有第二輪資料；§3.1／§3.2／§3.3／§3.4／§3.5／§3.7 的第一輪數字只存在於 gitignore 的 `EVIDENCE_LOG.txt`，但附錄 B 卻宣稱「每一條命令與完整輸出，稽核可逐項重跑」。 | **成立。** 複核另外自己補跑確認第一輪數字為真（`--dump-modes` 得 0.23200／0.19351／0.05308／0.00951／0.00804／0.00456，與 §3.1 逐位吻合；Python 複刻鏈重現 τc 10.840→4.302 ms、H −4.97→−48.17、comp ×1.4062→×4.0000、unclamped ×90.99 與 §3.7 全部八列）——**無造假，只是版控層面不可追**。 | ①把第一輪的完整數字表整段複製進版控的 `reports/gate_outputs/wf0907_R6_d8_evidence.txt`，成為新的 **`== [11] 第一輪（2026-09-07）數字表 ==`** 段。②附錄 B 的宣稱改寫：明講 [1]–[10] 附逐條命令可原樣重跑、[11] 進版控的是**數字表**（探針參數寫在表頭）、腳本仍在 gitignore 的 `output\` 底下，並註明複核者已用表頭參數獨立重跑確認可重現。 |
| 7 | minor | 附錄 A 第 11 條說 JSouthAudio 那頁「無任何數值資料（只有定性描述）」，措辭過頭——該頁有幾何與材料常數。 | **成立。** 2026-09-08 我自己 WebFetch 該頁確認：有 "20cm in diameter, 10cm high and 3mm thick"、Young's modulus 180e9、Poisson 0.265、density 8000、頻率搜尋範圍 100–5000 Hz；缺的是模態頻率／振幅結果（只有振型動畫）。 | 改寫為「頁面**有**幾何與材料常數（逐項列出），但**沒有任何模態頻率或振幅結果**，因此對本案（要的是比值與相對響度）不採用」。該來源本來就標明不採用，**無下游影響**。 |

**沒有被本輪修正動到的結論**（複核也未挑戰）：主因仍是 `exciter: "finger"` 造成的 τc 4.3–10.8 ms
與 `H(ω,τc)` 的 −43.2 dB；跨音域補償被 ±12 dB 上限卡死（MIDI 87 需 ×114.73 只給到 ×4）；
跨引擎對照證明「40 dB vs 4.4 dB」是被 exciter 設定混淆的比較；corpus 影響範圍 43 檔／2463 事件；
建議仍是**選項 1（只改樂譜 exciter）**，選項 2/4 擋在 D2/D4，不建議選項 3。


---

## 第三輪獨立複核記錄（2026-09-08，第三位 Opus）

> 這一輪的作法：**完全不看前兩輪的中間檔**，自己寫探針產生器、自己渲染、自己寫量測腳本，
> 再回頭比對本文的數字；同時把 §2 裡「宣稱已取得原文」的來源逐一重開、逐句核對引述。
> **本輪同樣沒有碰 `src/`、`tools/`、`scores/`，沒有 `git commit`／`push`／`checkout`／`stash`／`reset`，
> 也沒有對 `build\` 跑 cmake。**只寫了 `reports/decision_packets/D8_tongue_drum_diagnosis.zh-TW.md`
> 與本卡自己的證據檔 `reports/gate_outputs/wf0907_R6_d8_evidence.txt`（新增 `== [12] ==` 段）。

### 重現結果（全部相符，沒有一項對不上）

| 本文主張 | 第三輪獨立量到的 | 判定 |
|---|---|---|
| §3.1 模態1 振幅 0.23200／0.19351／0.05308／0.00951／0.00804／0.00456 | 0.232／0.19351／0.05308／0.00951／0.00804／0.00456 | **逐位相同** |
| §3.1 模態1 T60 68.68／37.39／19.92／10.25／5.01／2.29 s | 68.675／37.386／19.917／10.251／5.013／2.288 | **相同** |
| §3.1 懸臂比值 6.2669（與音高無關） | 六個音全部 6.2669 | **相同** |
| §3.7 模態1 振幅斜率 finger 34.13／felt 10.48／wood −7.82 dB | 34.13／10.48／−7.82 | **逐位相同** |
| §3.2 g1 `finger` 0.3 s 窗六音 RMS | −35.99／−37.68／−49.12／−64.30／−66.66／−73.20 | 與本文差 ≤0.16 dB（探針 `meta.id` 不同→激發噪音種子不同） |
| §3.9 g2 `finger` 0.3 s 斜率 39.14 dB | 39.31 dB | 相符 |
| §3.10 cimbalom `finger` 斜率惡化 | 4.08 → 23.04 dB（0.3 s 窗） | **第三度確認** |
| §3.8 corpus 43 檔／2463 事件／2362 tongue_drum + 101 beam／軟激發 96.8 %／含字串 8 檔 | 43／2463／2362+101／2385＝96.83 %／8 | **逐項相同** |
| §1 QA「97.4 % 能量在 200 Hz 以下」 | §3.5 的 97.36 %（本文既有），本輪未重渲整首 | 沿用 |

### 引用逐句重開（4 個「已取得原文」的關鍵來源）

| 來源 | 本文引述 | 我今天重開拿到的 | 判定 |
|---|---|---|---|
| Euphonics §3.3 | "This can be done by using a soft hammer." | "This can be done by using a soft hammer, but the grown-up xylophone and marimba enhance this effect by using resonators." | **相符**（本文只截前半句，語意無走樣） |
| Euphonics §3.3 | 木琴 1.00, 3.00, 6.16, 10.29／馬林巴 1.00, 3.92, 9.24, 16.27 | 木琴 1.00, 3.00, 6.16, 10.29, 14.01, 19.66, 24.02；馬林巴 1.00, 3.92, 9.24, 16.27, 24.22, 33.54, 42.97 | **相符** |
| Physics Today (2009) | "The frequencies of those modes are in the ratio of 1:2:3" | 逐字相同；同頁另有 "When struck with the hand, each note area of the hang vibrates in a rich complement of modes. In particular, the three lowest-frequency modes—the fundamental and the second and third harmonics—are all strongly excited." | **相符，且更強**（原文明寫「用手敲」也能激出三個模態，正好對照引擎裡 `finger` 只剩一個模態） |
| Kosmosky | "consist in the correct proportions of 1:2:3:4: 5" | 逐字相同 | **相符** |
| RAV Vast | "Each tongue can produce 4–7 harmonic overtones in harmony" | 逐字相同；並明確回答該頁 **does not provide numeric frequency ratios** | **相符**，且再次確認第一輪複核 finding 1 的修正是對的 |
| ICSV27 全文 | 「403，未取得原文」 | 四條路徑（機構庫 bitstream／ResearchGate publication 頁／ResearchGate 作者自存 PDF／iris handle 301 轉址）**全部 403** | **缺口維持** |
| Reddit | 「本環境無法連線」 | `www.reddit.com/r/handpan/.json` 與 `old.reddit.com` 皆 "unable to fetch"；`site` 搜尋回傳全是商品頁 | **缺口維持** |

### 本輪改了什麼（4 項）

| # | 級別 | 問題 | 修正 |
|---|---|---|---|
| 1 | major | §0／§4 選項 1 把「厚 3.2／寬 30／strike 0.42」說成「月光樂譜自己的幾何」、把「厚 2.6／寬 24／strike 0.44」說成「第一輪探針幾何」，並要求「決策請看前者」。**實際上兩組都出自同一首**，而且 2.6／24／0.44 是 **952 事件（83.4 %）的主力**，3.2／30／0.42 只有 176 事件（15.4 %）。 | §0 改成**兩組幾何並列的表**（三種量測窗都列），不再偏袒少數幾何；§3.11 補上兩組的完整第三輪數字。**結論不變**（兩組都是 40 dB 級 → 個位數）。 |
| 2 | major | §4 選項 1 的「代價」只寫了音色改變，**漏掉一個量得到的副作用**：換 `wood_mallet` 後低音端基頻不再是最強分音。 | 實測 g1 MIDI 37 模態2／模態1 ＝ **2.27（+7.1 dB）**、47 ＝1.90、57 ＝1.23，67 以上才反轉。已寫進 §4 選項 1 代價第 2 點與 §3.11，並指出 `felt`（MIDI 37 比值 0.068）沒有這個副作用 → 給月月一個明確的「保基頻 vs 要泛音」取捨。 |
| 3 | minor | §3.4 的行號基準註記宣稱 `ChromaticEngine.h` L411 以前的錨點「在 HEAD 與工作樹一致」。 | 實測**整齊 +1 行位移**（HEAD `:35/:177/:178/:243` vs 工作樹 `:36/:178/:179/:244`）；另 `ScoreRenderer.h` 的 `beam` 別名在工作樹已從 `:817` 漂到 `:1081`（E9 lane）。已改寫該段並標明 `ModalResonator.h`／`BeamModel.h`／`HammerImpulse.h` 三檔工作樹乾淨、行號 HEAD＝工作樹。 |
| 4 | minor | §2 沒有任何「真實樂器上音量不均被怎麼看待」的來源；ICSV27 的線索沒有被登記。 | 新增證據 20（Handpan.World 調音師頁，明說受影響的音「deutlich leiser」且被當成要處理的缺陷，但無數字）與證據 21（ICSV27 摘要層級的 fixed-free rod 線索，**標明未取得原文、不當證據**）；§5 補上缺口 8、9。 |

### 沒有被本輪動到的結論

主因仍是 `exciter: "finger"` 造成 τc 4.3–10.8 ms、`H(ω,τc)` 吃掉 **−43.2 dB**（我用 `H(ω)=|cos(ωτc/2)|/|1−(ωτc/π)²|`
手算複驗：MIDI 37 f0 69.30 Hz／τc 10.84 ms → H＝0.5644（−4.97 dB）；MIDI 87 f0 1244.51 Hz／τc 4.30 ms →
H＝0.00391（−48.16 dB），差 **43.2 dB**，與 §3.4 相符）；跨音域補償被 ±12 dB 上限卡死（MIDI 87 需 ×90.99–×114.73、只給到 ×4）；
「40 dB vs 4.4 dB」是被 exciter 設定混淆的比較；corpus 影響 43 檔／2463 事件；
建議仍是**選項 1**，選項 2／4 擋在 D2／D4，不建議選項 3。
**新增的只有一句取捨**：選項 1 內部，`felt` 保基頻、`wood_mallet` 要泛音但低音會偏鐘感。


---

## 第四輪獨立複核記錄（2026-09-08，第四位 Opus）

> 作法：**完全不看前三輪的中間檔**，自己產探針、自己渲染、自己寫量測腳本、自己用 Python 依
> `BeamModel.h` / `HammerImpulse.h` / `ModalResonator.h` 逐行重寫一次計算鏈，再回頭比對本文；
> 同時抽驗 §2 裡宣稱「已取得原文」的來源，並重試兩個既有缺口。
> **本輪同樣沒有碰 `src/`、`tools/`、`scores/`，沒有 `git commit`／`push`／`checkout`／`stash`／`reset`，
> 也沒有對 `build\` 跑 cmake。**只寫了 `reports/decision_packets/D8_tongue_drum_diagnosis.zh-TW.md`
> 與本卡自己的證據檔 `reports/gate_outputs/wf0907_R6_d8_evidence.txt`（新增 `== [13] ==` 段）。

### 本輪改了什麼（3 項，其中 1 項推翻既有結論）

| # | 級別 | 問題 | 我的查證 | 修正 |
|---|---|---|---|---|
| 1 | **blocker（推翻）** | §0 與 §3.10 都寫「tongue_drum 剩下的那一截（47.6 vs 23.4 dB）才是梁模型自己的短板」。該推論建立在「cimbalom 也用 `finger`」是等價對照上。 | **不成立。** `ScoreRenderer.h` 有兩張獨立的 exciter 表：`cimbalomExciterFromString()`（HEAD `:1125`）把 `finger` 翻成 **Felt（2.0 ms，且改走 `pianoHammerTauC()`）**；`chromaticExciterHardness()`（HEAD `:1138`）把同一個字翻成 **Cotton（6.0 ms）**。實測 τc：tongue `finger` 10.840→4.302 ms、cimbalom `finger` 3.008→1.606 ms。**真正等價的對照**是給 cimbalom 寫 `cotton_mallet`（同 6 ms 檔位、同 `tauCForNote()`）——實測斜率 **43.18 dB（0.3 s 窗）／46.68 dB（6 s 窗）**，**比 tongue_drum 的 37.20／47.13 dB 沒有比較好**。旁證：cimbalom 的 `finger` 與 `felt` 兩份渲染六個音 RMS 逐音相同到 0.01 dB。 | §0 與 §3.10 該句**刪除並標註為已證偽**；新增 §3.12(b)(c) 完整記錄對映表、τc 表與等硬度對照表；結論改寫為「幾乎全部是接觸時間問題，梁模型在本案沒有額外欠帳」——**方向與主因不變，只是把責任從梁模型移回接觸時間律**。 |
| 2 | major | §4／§0 把 `felt` 描述成「同樣把旋律救回來、又沒有副作用」，但只引用了**單音斜率**。 | 重渲整首月光三版（1142 事件、327 秒、只改 `exciter`、`normalize=false`）：200 Hz 以下能量 `finger` **97.36 %** → `felt` **78.06 %** → `wood_mallet` **17.53 %**；旋律音域 2.64 % → **21.94 %** → **82.46 %**。（`finger`／`wood` 兩列與 §3.5 逐位／近似相同，交叉驗證量測鏈；`felt` 是本輪新增的第三版。） | §0、§4 選項 1、§4 建議三處都補上「`felt` 只走了約四分之一的路」的實測數字，取捨敘述改為「部分改善 vs 全解」。 |
| 3 | minor（新增） | 前三輪沒有把「同一個樂譜字在兩顆引擎意義不同」登記成可行動項。 | 逐字比對兩張表：**只有 `finger`/`finger_tap` 是會造成本案病灶的不一致**（Cotton vs Felt）；另有 `metal_tip`、`medium`、`sharp` 三個字也不一致，但方向都是「更硬」，非病灶。 | 新增 **§4 選項 5**（統一對映，一行改動但 Rule 10 波及 43 檔，**建議不要現在做**）與 §5 缺口 11、12。 |

### 重現結果（全部相符，沒有一項對不上）

完整表格見 §3.12(a)。摘要：`--dump-modes` 的模態1 振幅、T60、6.2669 比值、§3.4 的三個環節數字
（H −43.20 dB／補償 +9.08 dB／unclamped ×90.99）、§3.7 的四個反事實、§3.8 的 corpus 統計
（43 檔／2463 事件／96.83 %／8 檔）、§3.11 的 `wood_mallet` 低音模態比、§3.5 的整首頻譜分布，
**全部由本輪獨立重跑得到相同或差 ≤0.16 dB 的結果**（差異來源：探針 `meta.id` 不同 → 激發噪音種子不同）。

### 引用抽驗（4 個「已取得原文」來源，2026-09-08 今日重開）

| 來源 | 本文引述 | 我今天重開拿到的 | 判定 |
|---|---|---|---|
| Euphonics §3.3　https://euphonics.org/3-3-marimbas-and-xylophones/ | "This can be done by using a soft hammer." ／ 木琴 1.00, 3.00, 6.16, 10.29 ／ 馬林巴 1.00, 3.92, 9.24, 16.27 ／ "Recall that in the ideal beam this ratio was 2.76" | 逐字相同（木琴全列 1.00, 3.00, 6.16, 10.29, 14.01, 19.66, 24.02；馬林巴 1.00, 3.92, 9.24, 16.27, 24.22, 33.54, 42.97） | **相符** |
| Physics Today (2009)　https://physicstoday.aip.org/quick-study/the-extraordinary-sound-of-the-hang | "The frequencies of those modes are in the ratio of 1:2:3" | 逐字相同；同頁 "the three lowest-frequency modes—the fundamental and the second and third harmonics—are all strongly excited." | **相符** |
| RAV Vast　https://ravvast.com/blogs/news/main-terms-in-the-world-of-steel-tongue-drum | "Each tongue can produce 4–7 harmonic overtones in harmony" ／ "its weight, width, and length determine that note's pitch" ／ "Playing with mallets tends to produce a louder, clearer attack" | 三句逐字相同 | **相符** |
| JSouthAudio（附錄 A 第 11 條）　https://jsouthaudio.com/modelling-simulations/modal-analysis-of-a-tongue-drum/ | 「有幾何與材料常數、但沒有任何模態頻率或振幅結果」 | 今日重開：確有 20 cm／10 cm／3 mm、E 180e9、ν 0.265、ρ 8000、搜尋範圍 100–5000 Hz；**確實沒有** Hz 值或比值。另有一句 "The first two of these are clearly a 'flappy' mode as the fundamental of the note, and then a 'twisty' mode present as an overtone."（定性，無數字） | **相符**（附錄 A 的措辭正確） |

### 兩個缺口重試的結果（都維持）

- **ICSV27 2021 全文**：`unige.iris.cineca.it/bitstream/...` **403**；
  `researchgate.net/profile/Davide-Borelli/publication/353818565/.../Experimental-characterization-of-the-steel-tongue-drum.pdf` **403**；
  Semantic Scholar API **429**。搜尋引擎摘要今日再次浮出「G4 tongue 49±1 mm、基頻 392±5 Hz、
  泛音 1179±5／1960±5／2745±5／3531±5 Hz」與「a simple model based on the vibration of a rod
  (with fixed-free ends)」「R² = 0.9955」——**我仍然沒有打開原文，本卡仍不採用**。
  （順帶登記一個**未經證實**的算術觀察，供將來拿到原文時第一時間比對：若上列頻率屬實，
  比值是 1 : 3.008 : 5.000 : 7.003 : 9.008，即**奇數列**，既不是懸臂梁的 1 : 6.27，
  也不是廠商說的 1:2:3:4:5。**這行字不是證據，是待驗的線索。**）
- **Reddit**：`www.reddit.com/r/tonguedrum/.json` 與 `old.reddit.com/r/handpan/search?...` 皆回
  "unable to fetch"；`WebSearch` 針對 reddit 的查詢回傳全是商品頁與 App Store 連結，無任何 reddit 討論串。
  → §5 缺口 4 維持，**本卡仍然沒有可引用的社群原文**。

### 沒有被本輪動到的結論

主因仍是 `exciter: "finger"` 造成 τc 10.84→4.30 ms、`H(ω,τc)` 吃掉 **−43.20 dB**；
跨音域補償被 ±12 dB 上限卡死（MIDI 87 需 ×90.99、只給到 ×4，等於上限自己扣了 27.2 dB）；
模態截斷對 RMS 斜率貢獻 < 0.1 dB；corpus 影響 43 檔／2463 事件；
建議仍是**選項 1（只改樂譜 `exciter`）**，選項 2／4／5 擋在 D2／D4／Rule 10，不建議選項 3。
