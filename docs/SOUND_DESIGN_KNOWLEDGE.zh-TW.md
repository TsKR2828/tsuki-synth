# 音效設計職業知識庫：把「靠感覺」翻成可判定門檻（draft，待 Opus 稽核）

> 起草：2026-08-28。狀態：**研究彙整草稿，未實作、未 commit（R7）**。
> 要解決的問題（月月核實過的缺口）：AI 不懂「什麼是音效、好音效聽起來是什麼樣子」——
> 但音效設計是成熟職業，一定有教材/審核標準把「好/壞」講成可操作的規則。
> 本文件的任務不是重新發明美學，是**把職業教材裡本來就存在、但寫成文字/經驗法則的判準，
> 翻成聾人與 AI 都能執行的量測門檻**，體例比照 `EARFREE_MELODY_GATE_DESIGN.zh-TW.md`
> 的可判定精神：每條規則要嘛給得出數字與量測方法，要嘛老實標「候選/未量化」。

---

## 0. 方法論與誠實標註（R4）

本輪研究用 WebSearch + WebFetch，時間框限一次 session。以下**逐條標明**每個來源是
「親眼 WebFetch 開啟成功（200）」還是「只在 WebSearch 摘要看到、原頁面 403 擋下拒絕當
一手來源」。凡標「未親眼開啟」的內容，本文件一律不當作判準依據，只列為候選線索。

**成功開啟（可引用）：**

| # | 來源 | 開啟方式 | 內容摘要 |
|---|---|---|---|
| S1 | Ric Viers, *The Sound Effects Bible*（2008, Michael Wiese Productions）全文 | archive.org 全文 txt，WebFetch 200 | 業界公認的音效錄製/設計/剪輯教科書；第 15 章〈剪輯十誡〉、第 16 章〈檔名與 metadata〉、第 17 章〈疊層〉 |
| S2 | [SFX Engine — The Ultimate Guide to the Impact Sound Effect](https://sfxengine.com/blog/impact-sound-effect) | WebFetch 200 | 撞擊音三層結構（transient/body/tail）的產業實務描述 |
| S3 | [Get That Pro Sound — Sound Design Techniques Series Part 3: Layering](https://getthatprosound.com/sound-design-techniques-tools-series-10-key-ways-and-best-plugins-part-3-layering-plugins/) | WebFetch 200 | 疊層時「每層佔不同頻段」的原則、以底鼓 sub/thump/tick 三段為例 |
| S4 | [SFX Engine — Best Practices for Game UI Sounds](https://sfxengine.com/blog/best-practices-for-game-ui-sounds) | WebFetch 200 | UI 音效時長分級（micro-interaction 100–300ms）、頻段分工建議 |
| S5 | [VNDev Wiki — Guide: Balancing a Game's Loudness](https://vndev.wiki/Guide:Balancing_a_Game's_Loudness) | WebFetch 200 | 引用 Game Audio Network Guild（GANG）+ Sony/Nintendo/Microsoft 的遊戲響度建議、EBU R128、ATSC A85 |
| S6 | [exceed7 — Tiny Ambience: How to get a seamlessly looping clip](https://exceed7.com/tiny-ambience/advanced/seamless-loop.html) | WebFetch 200 | 零交越（zero-crossing）接縫法、crossfade 調整法、Audacity/iZotope RX 工具指名 |
| S7 | [MasteringTheMix — Understanding the Different Frequency Ranges](https://www.masteringthemix.com/blogs/learn/understanding-the-different-frequency-ranges) | WebFetch 200 | 7 段頻譜劃分（sub-bass 到 brilliance/air）逐段問題與處理建議 |
| S8 | [MixAnalytic — Transient Detection Guide](https://mixanalytic.com/guides/transient-detection) | WebFetch 200 | 壓縮器 attack time 常用 10–30ms 當「放過 transient」的實務門檻；40–250Hz 為底鼓/貝斯「厚度」頻段 |
| S9 | [Krotos Studio — How Pro Sound Designers Work with Effects](https://krotos.studio/blog/how-professionals-work-with-sound-effects) | WebFetch 200 | 「先鋪底再修細節」的專業疊層工作流；素材來源哲學（真實錄音 > 純合成） |

**只在 WebSearch 摘要見到、原頁面 403 擋下（列為候選，不當判準依據）：**

| 候選線索 | 擋下的原頁面 | 為何列入 |
|---|---|---|
| Envato/AudioJungle 技術規格：44.1kHz/16-bit、MP3 320kbps、單檔 ≤10 分鐘、音效包 ≤50 檔、>2 秒需浮水印 | `help.author.envato.com` 兩篇官方頁面，WebFetch 均 403 | 若屬實，是最具體的市場審核硬指標，但本輪未能一手驗證，需下次直接登入或用瀏覽器工具開啟後補證 |
| AudioJungle 常見退件：「boxy、殘響過多、樂器聽起來太遠」= mud 在中低頻堆積 | `forums.envato.com` 論壇串，WebFetch 403 | 與 S7 的 mud 頻段定義（250–500Hz）方向一致，可交叉支持，但退件案例本身未親見 |
| 學術「Punch」感知模型（*A Perceptual Model of Punch Based on Weighted Transient Loudness*，AES/JAES 論文） | ResearchGate 頁面 403 | 只確認論文標題與存在，完全未讀到方法論或公式，**不引用其任何數字** |
| GDC Vault 音效設計相關演講（*Audio Bootcamp: Technical Sound Design*、*Next Level Creature Sound Design*、*Creating Sound Effects and Sound Textures from Examples* 等） | GDC Vault 需會員權限，未開啟任何一場的內容 | 只確認題目真實存在、是業界正式研討會場次，**內容一概未見，不引用** |
| Zapsplat〈The secret of looping no one told me〉 | `zapsplat.com`，WebFetch 403 | 已由 S6 的技術內容覆蓋，不需要單獨引用 |

---

## 1. 分層結構：transient / body / tail（S1 §17、S2、S3、S9 交叉支持）

這是本輪研究裡**跨最多獨立來源、一致度最高**的原則，可信度最高：

- **Transient（起音）**：撞擊/事件最初幾毫秒的高頻能量爆發，決定聲音能不能在混音裡「切出來」
  被聽見（S2：「the initial, sharp attack... lasts only a few milliseconds」）。
- **Body（本體）**：中低頻為主的「份量」段，傳達物體的質量與力道（S2：「packed with low and
  mid-range frequencies」；S3 以底鼓為例：sub boom + low-mid thump + mid-high tick）。
- **Tail（尾音）**：衰減/環境反射段，把聲音放進一個空間裡，決定「這一聲發生在哪裡」
  （S2：小房間短促、大空間長混響）。

**可量測翻譯（本文件提出，不是來源原文——標「衍生判準」）：**

| 判準 | 量測方法 | 用途 |
|---|---|---|
| 三段能量分離度 | 對音檔取 Hilbert envelope，切三段窗（起音窗 0–20ms／本體窗 20ms–衰減點／尾音窗 衰減點以後），比較各窗頻譜質心（spectral centroid）是否遞減（transient 質心 > body 質心 > tail 質心屬正常「上到下」能量分佈） | 偵測「三層混成一坨、沒有分工」的糊音效——如果三段頻譜質心幾乎相同，代表沒有做出 S2/S3 講的頻段分工 |
| Attack window 佔比 | 前 20ms 能量（RMS）／全音檔總能量 | 見第 2 節「punch」量化 |

**誠實侷限**：S2/S3 都沒有給出「transient 應該幾毫秒、body 應該多少 dB」的硬數字，
三段切法的邊界本身是類比與經驗判斷，不是頻譜上一刀切得乾淨的物理量。上面「衍生判準」
是本文件為了讓它可執行而做的操作化定義，**不是來源本身的量化結論**，套用前需要月月核准
邊界常數（20ms 起音窗、質心遞減方向）是否合理。

---

## 2. 頻譜佔位：mud / boxy / presence / air（S7 為主，S8 交叉支持）

S7（MasteringTheMix）給出目前本輪能找到最完整、可直接當頻段表使用的劃分：

| 頻段 | Hz 範圍 | 過量時的問題 | 來源用詞 |
|---|---|---|---|
| Sub-bass | 20–60 Hz | 「更多是用感覺的，不是用聽的」；過量會 boomy | S7 |
| Bass | 60–250 Hz | 過量會 muddy（節奏組基頻所在） | S7 |
| Low-mids | 250–500 Hz | **muffled / boxy**、與其他樂器互相遮蔽（masking） | S7 |
| Midrange | 500 Hz–2 kHz | 過量顯得廉價；500Hz 附近 boxy；缺乏會顯薄 | S7 |
| High-mids | 2–6 kHz | 過量刺耳、齒音誇張；此區人耳最敏感 | S7 |
| Highs (air/brilliance) | 6–20 kHz | 6–8kHz 過量齒音/刺耳；12kHz 以上加「空氣感」 | S7 |

S8（MixAnalytic）獨立提到「40–250Hz 是底鼓/貝斯的厚度（thump）頻段」，與 S7 的 bass 頻段
（60–250Hz）方向一致，可視為交叉驗證（不是同一數字，是同一結論的兩個獨立來源，40Hz vs
60Hz 下緣的差異視為合理的來源間誤差帶）。

**可量測翻譯：「muddy」的量化偵測器**

```
mud_ratio = energy(250–500 Hz) / energy(20–20000 Hz)
```

- 若 `mud_ratio` 明顯高於同類音效庫的分布中位數 → 標記「候選 muddy」，交給人耳複核。
- **本文件不設絕對閾值**（例如「> 15% 就是 muddy」）：S7/S8 都沒有給出這種絕對數字，
  muddy 是相對於「這個音效在混音裡該有多少低中頻」的相對判斷，不是頻段能量的絕對值問題。
  能做的是**橫向比較同類別音效**、抓離群值，而不是宣稱一個放諸四海皆準的百分比門檻。

---

## 3. Punch（打擊感）的量化嘗試（S2、S8 交叉支持；學術模型未驗證）

- S2/S8 都把「punch」與 attack transient 的強度、速度掛鉤（來源用詞：「the faster and louder
  the transient, the more punch」——注意這句是本輪從一般搜尋摘要得到的通用共識描述，非單一
  S2/S8 逐字引用，列為**方向性共識**而非逐字引用）。
- S8 給出一個可操作的**代理數字**：壓縮器 attack time 常用 **10–30ms** 讓 transient「先透過去」
  再開始壓縮——這隱含業界默認 transient 段落大約落在數十毫秒級。

**可量測翻譯（衍生判準）：**

```
attack_energy_ratio = RMS(0–20ms) / RMS(全長)
```

- 用 0–20ms 當起音窗（取 S8「10–30ms」區間下緣，並非來源明文的「起音窗定義」，
  是本文件借用壓縮器 attack time 的常用值反推出來的操作化窗口，**標為候選常數**）。
- 同類別音效（例如「劍擊」對「劍擊」）比較 `attack_energy_ratio`，比值明顯偏低的候選判定
  「punch 不足」，仍需人耳複核是否為刻意的悶擊設計（例如拳頭打肉的悶感本來就該低 punch）。

**誠實侷限**：學術上確實存在對「punch」的感知模型論文（見第 0 節候選清單），但本輪未能
讀到其方法論，**上面兩個判準是本文件從相鄰、能驗證的來源（壓縮器實務經驗值）反推出來的
操作化代理，不是那篇論文的結論**，不能宣稱這是「已被學術驗證的 punch 度量」。

---

## 4. 類別時長慣例表（S4 為主）

S4（SFX Engine — Best Practices for Game UI Sounds）明確給出 UI 音效的時長分級：

| 類別 | 建議時長 | 頻段分工建議（來源原文方向） | 來源 |
|---|---|---|---|
| Micro-interaction（hover、click、游標移動） | **100–300 ms**，需極短，不能拖延下一步操作 | 應比其他 UI 聲音更安靜，避免遮蔽 confirm/error | S4 |
| 強力確認音（confirm） | 未給出精確 ms，落在 micro-interaction 之上 | **200–500 Hz** 段，「powerful confirmations」 | S4 |
| 資訊性提示 | 同上 | **1–5 kHz**，「informational clarity」 | S4 |
| 高優先警示（error/alert） | 同上，且建議搭配 duck 其他音軌 | **8 kHz 以上**，「grab attention」 | S4 |

**誠實侷限**：S4 只細分了 UI 音效這一類，沒有覆蓋 one-shot 撞擊音、loop 環境音床、
過場音效等其他常見遊戲音效類別的時長慣例——本輪搜尋沒找到同等權威、給出具體數字的
對應表，**這是本知識庫目前最大的空白**，需要下一輪針對「ambience bed 標準時長」「one-shot
武器音效時長分布」單獨深挖（候選方向：查 Wwise/FMOD 官方文件的音效資產管理章節，
本輪未及查證）。

---

## 5. 循環無縫標準：zero-crossing + crossfade（S6）

S6 給出具體、可直接寫成程式的技術步驟：

1. **零交越接縫**：迴圈起點與終點都必須落在波形振幅為 0 的瞬間，「the jump of value between
   seams continues smoothly to the other side」——這是避免接縫喀聲（click/pop）的**充分條件**，
   來源明講喀聲的物理成因是「a fragment of square wave」（瞬間值跳動 = 高頻方波成分）。
2. **Crossfade 校正**：若零交越點附近仍聽得出接縫，S6 建議（a）調整 crossfade 的 ease curve
   偏向一側，或（b）拉長 crossfade 長度——但同時警告拉太長會讓環境音「聽起來假」。
3. **驗證方式**：S6 給的驗證法本身是感知式的（「閉眼聽，排除播放頭視覺偏見」），**沒有給出
   量化的自動驗證數字**。

**可量測翻譯（本文件的操作化，S6 沒有直接提供）：**

```
loop_seam_check:
  1. sample_at_loop_start ≈ 0 (振幅接近零，容差待定)
  2. sample_at_loop_end   ≈ 0
  3. d(amplitude)/dt 在接縫前後應連續（一階差分不應在接縫處出現離群尖峰）
  4. 頻譜連續性：接縫前後各取一小窗做 FFT，比較頻譜差異（避免「振幅為零但頻譜突變」的隱性喀聲）
```

第 4 點是本文件補的——S6 只談振幅零交越，沒有處理「振幅剛好過零但頻率內容突變」這種
邊緣情況（例如打點在一個轉調瞬間），這是本文件基於數位訊號處理常識加的**候選補強**，
未經任何來源明文背書，需要在 TsukiSynth 實作前另外驗證。

---

## 6. 響度規範：遊戲 vs 影視（S5）

S5 明確引用 Game Audio Network Guild（經 Sony/Nintendo/Microsoft 認可）的建議值：

| 平台類型 | 目標 LUFS | 容許範圍 | Peak 上限 |
|---|---|---|---|
| 主機/電腦遊戲 | **-24 LUFS**（integrated） | ±2 LU（-26 ~ -22） | -1 dB True Peak |
| 掌機/手機遊戲 | **-16 LUFS** | -18 ~ -14（S5 註明「無向上放寬」） | -1 dB True Peak |
| 歐洲電視（EBU R128，對照組） | -23 LUFS | — | — |
| 美國電視（ATSC A85，對照組） | -24 LUFS | — | — |

- 掌機/手機目標較響的理由（S5）：「更常在戶外、環境噪音較高的地方被玩」。
- S5 特別註明：這些數字**沒有針對 SFX/UI/對白/音樂分別列出獨立目標**，是整體遊戲會話
  （建議 30 分鐘至 2 小時）的 integrated LUFS，個別音效層的響度分配仍是「不要讓音樂蓋過
  台詞、不要讓 SFX 嚇到玩家」這種質化要求，**沒有找到逐類別的量化子目標**——這是第二個
  明顯的知識空白。

**可直接落地的判準**：任一 SFX 素材輸出前檢查其 integrated LUFS 與 True Peak，若素材本身
（非整體遊戲會話）就已經逼近或超過 -1 dBTP，視為技術缺陷（削波風險），此判準不受
「沒有逐類別子目標」的空白影響，可以直接用。

---

## 7. 市場審核標準（候選為主，S1 §16 為唯一一手佐證）

- **命名/metadata**（S1 第 16 章，一手來源）：Viers 書中列出三種音效庫命名系統——
  category-based（依類別分資料夾/前綴）、effect-based（依效果描述）、numeric-based
  （純編號 + 資料庫查表）。這是教科書層級的建議，不是特定平台的審核規則。
- **平台技術硬指標**（Envato/AudioJungle：44.1kHz/16-bit、MP3 320kbps、單檔≤10分鐘、
  音效包≤50檔、>2秒需浮水印）：**列在第 0 節候選表，本輪未能一手驗證**，不當作本知識庫
  的正式判準，只作為「這類平台存在具體技術硬指標」的方向性證據。
- **退件常見原因**（「boxy、殘響過多、聽起來太遠」= 中低頻堆積）：同樣未一手驗證，但與
  第 2 節 S7 的 mud/boxy 頻段定義（250–500Hz）方向一致，可以合理推測「mud_ratio 偵測器」
  對篩掉這類退件案例有實際幫助——**這是推測，不是已證實的因果關係**。

**下一輪待補**：直接用瀏覽器工具（而非 WebFetch）登入或繞過 403，一手讀取
`help.author.envato.com` 的官方技術規格頁與 Pond5 contributor portal 的對應頁面，
把候選表升級成正式判準。

---

## 8. TsukiSynth 適配：哪些判準可以直接寫成 Python 檢查器

以下按「現在就能寫、判準來源夠硬」排序：

| 優先度 | 檢查器 | 判準來源 | 輸入 | 輸出 | 備註 |
|---|---|---|---|---|---|
| 高 | `loudness_check.py` | S5（一手，GANG 建議值） | 渲染 WAV | integrated LUFS + True Peak，PASS/FAIL 對照 -24±2（主機）或使用者指定平台 | 需要 `pyloudnorm` 或等效庫；沒有 SFX 逐類別子目標，先做整體會話級/單檔 True Peak 兩種模式 |
| 高 | `loop_seam_check.py` | S6（一手）+ 本文件第 5 節補強 | 標記為 loop 的 WAV | 接縫振幅、一階差分尖峰、接縫頻譜差異三項數字，UNVERIFIED 若無法判定連續性 | 沿用 melody_verify 的 fail-closed 哲學：判不準就標 UNVERIFIED 不猜 |
| 中 | `spectral_band_report.py` | S7（一手） | 任意 WAV | 七段頻譜能量分佈報表（不下絕對判準，只報數字） | 先做「報表」不做「判準」，等月月看過同類素材的分布再決定要不要轉阻斷式（沿用 M5/C3 慣例：先 informational 上線） |
| 中 | `attack_energy_ratio.py` | S8（一手）+ 本文件第 3 節衍生 | 任意 WAV | 0–20ms RMS / 全長 RMS | 候選窗口 20ms 需要月月核准；同類別橫向比較才有意義，單一數字不能單獨判定 |
| 低 | `duration_class_check.py` | S4（一手，僅覆蓋 UI 類別） | WAV + 宣告類別（如 "ui_click"） | 是否落在 100–300ms（僅 UI micro-interaction 有硬數字） | 覆蓋範圍窄，其餘類別（one-shot/ambience/loop）需先補第 4 節的空白才能做 |
| 低 | `mud_ratio_compare.py` | S7+S8 交叉 | 同類別 WAV 一批 | 250–500Hz 能量佔比的批次分布，標離群值 | 相對判準，不設絕對閾值（見第 2 節） |

**共通設計原則（沿用 EARFREE_MELODY_GATE_DESIGN 的慣例）**：
1. 所有新常數（20ms 起音窗、mud_ratio 離群定義、loop 接縫容差）**先 informational 上線印
   數字，不阻斷產線**，等月月看過本專案實際素材的分布後再決定是否核准轉阻斷式。
2. 判不準（SNR 太低、類別未知、無同類樣本可比較）一律標 `UNVERIFIED`，不強行給 PASS/FAIL。
3. 每個檢查器都要有「哨兵反例」：例如刻意做一個接縫在波峰的 loop 素材，`loop_seam_check`
   必須 FAIL 它，否則檢查器本身不算活著（沿用 melody_verify 的自我驗證慣例）。

---

## 9. 誠實侷限（本節不能省）

1. **這些判準是下限過濾器，不是美學裁判**。所有能量測的東西（響度、頻段分佈、接縫連續性、
   起音能量比）抓的是**技術性瑕疵**（削波、糊音、喀聲、時長不合場合），完全不處理「這個音
   聽起來像不像一把好劍」「這個腳步聲有沒有角色個性」——這類判斷本輪找到的所有來源
   （包括教科書 S1）都還是交給人耳與經驗，沒有一個聲稱能自動化。
2. **多數數字是經驗法則的區間，不是物理定律**。S7 的頻段表、S4 的時長分級、S5 的 LUFS
   目標，都是「業界常見做法」而非「唯一正確答案」——恐怖遊戲刻意做糊、刻意做刺耳，是
   合理的藝術選擇，判準只能標「偏離常態」，不能標「錯」。
3. **本輪研究覆蓋不完整**，明確的空白：
   - one-shot / ambience bed / loop 環境音的時長慣例（S4 只覆蓋 UI）。
   - SFX/對白/音樂分軌的響度子目標（S5 只給整體會話級目標）。
   - 市場審核的一手技術硬指標（Envato/Pond5 官方頁面本輪 403，未驗證）。
   - 學術上是否存在被驗證過的「punch」量化模型（論文存在，內容未讀到）。
4. **本文件裡「衍生判準」段落的常數（20ms 起音窗、mud_ratio 相對比較法、loop 頻譜連續性
   檢查）都是本文件在無法從來源直接搬數字的情況下自行操作化的結果，不是來源原文結論**，
   套用到 TsukiSynth 產線前，逐一標成「候選常數」走 informational 上線流程，不得直接當
   阻斷式判準使用。
5. 本文件標題已註明 **draft，待 Opus 稽核**——尤其要覆核第 0 節「未親眼開啟」候選表
   是否被本文件其他章節誤當一手引用使用（自查：第 7 節已刻意標註為候選，未見誤用）。

---

## Opus 稽核記錄（2026-08-28）

稽核者：Opus 子代理，懷疑立場。方法：對 §0 表列來源逐一**重新 WebFetch 親自打開**，
拿回傳的逐字原文比對本文件引用，不採信本文件自述的「已開啟」。未動 `src/`、`tests/`、
`scores/`，未 git add/commit/push（R7）。本節為追加，未修改上方任何原有內容。

### A. 抽驗 5 條原則（逐字核對結果）

| # | 本文件章節 | 核對結論 | 來源逐字證據（本次親自取得） |
|---|---|---|---|
| P1 | §1 transient/body/tail 三層 | **通過** | S2 原文：transient 為 "that initial, sharp 'attack'… often lasting only a few milliseconds"；body "packed with low and mid-range frequencies"；tail "tells us _where_ the impact happened"。S3 原文："Each layer will ideally occupy its own range of frequencies"、"a sub boom, a low-mid range thump and a mid-high frequency thwack or tick"。**兩份來源本次確認皆無任何 Hz/ms/dB 數字**——本文件 §1 誠實侷限「S2/S3 都沒有給出硬數字」屬實 |
| P2 | §2 七段頻譜表 | **通過（一處收窄未標註，見 A3）** | S7 逐字：20–60Hz "boomy"／60–250Hz "Too much in this area quickly causes muddiness"／250–500Hz "sound muffled or boxy"／500Hz–2kHz "Too much around 500 Hz can make your mix sound boxy" + "honk"／2–6kHz "harsh or edgy"／6–20kHz "piercing or shrill"。逐列相符 |
| P3 | §3 attack 10–30ms、40–250Hz | **通過** | S8 逐字："use a slower attack of 10-30 ms so the transient passes before gain reduction"、"The 40-250 Hz thump that gives kick and bass their weight" |
| P4 | §4 UI 時長/頻段分工 | **通過（數字完全吻合）** | S4 逐字："Microinteraction sounds should be extremely brief, typically between 100-300 milliseconds"、"reserve the 200-500Hz range for powerful confirmations, 1-5kHz for informational clarity, and 8kHz+ for high-priority alerts" |
| P5 | §6 遊戲響度 LUFS | **通過（兩處精度流失，見 A5）** | S5 逐字："Sony, Nintendo and Microsoft, through the Game Audio Network Guild, also recommend -24 LUFS for console games and -16 LUFS for portable games"、"They shouldn't go beyond -1 dB"；並確認 S5 **未**給 SFX/對白/音樂分軌子目標 |
| P6 | §5 loop 零交越 | **來源內容通過，但推論過強，見 A2** | S6 逐字："the most meticulous way of joining is to join where both end of the clips you are working on are at 0…"、"you hear a pop in audio, which is actually a fragment of square wave"、"try changing the ease curve to bias more towards one side… or make the fade crossed for longer duration"。本次亦確認 S6 **驗證方式純感知式、無數值判準**，且**只談振幅、完全未談跨接縫的頻譜連續性**——本文件 §5 自承「第 4 點是本文件補的」屬實 |

另核 S1（*The Sound Effects Bible* archive.org 全文）目錄：ch15 "The Ten Sound Editing
Commandments"、ch16 "File Naming and Metadata" 皆存在；三種命名法 "Category-Based /
Effect-Based / Numeric-Based File Names" 逐字存在，§7 的一手引用成立。

### B. 自創判準是否偽裝成文獻（本輪重點）

**整體結論：沒有系統性偽裝。** §1、§3、§5 三處自創判準都主動標了「衍生判準」／
「本文件的操作化，S6 沒有直接提供」／「標為候選常數」，§8 表格備註欄也逐列標了待核准。
§9.5 的自查結論（§0 的 403 候選未被其他章節誤當一手引用）本次複核**屬實**——
§7 確實把 Envato 技術規格明寫成候選、不當判準。以下是仍需修的個案：

- **A1（中）§3 的引號句沒有出處。** 本文件寫「來源用詞：「the faster and louder the
  transient, the more punch」」，同一句話又自承「非單一 S2/S8 逐字引用」「從一般搜尋摘要
  得到」。本次親自打開 S2 全文，**查無此句**。依 §0 自訂規則（WebSearch 摘要不得當一手
  來源），這句既然來自搜尋摘要就不該套引號、更不該冠「來源用詞」。建議刪除引號與
  「來源用詞」四字，改寫成本文件的概括，或整句刪掉——§3 的判準靠 S8 的 10–30ms 已足夠。
- **A2（中）§5 把零交越稱為「充分條件」是超譯，且與本文件自己矛盾。** S6 原文只說它是
  "the most meticulous way of joining"，從未宣稱充分。本文件 §5 第 2 點（「若零交越點附近
  仍聽得出接縫」）與第 4 點（振幅為零但頻譜突變的隱性喀聲）**兩處都在證明它不充分**。
  建議把「充分條件」改為「必要的第一道條件／業界首選作法」。
- **A3（低中）§2 的 `mud_ratio` 是全文唯一沒掛「衍生判準」標籤的自創公式。** §1/§3/§5 都
  標了，§2 只寫「可量測翻譯」。且分子取 250–500Hz，而 S7 講 mud 的逐字原句是 "build-up in
  the low mids, roughly **200 to 500 Hz**"——本文件把下緣收窄到 250Hz（改採 S7 頻段表的
  low-mids 邊界）是合理的工程選擇，但**這個選擇本身沒有標明是本文件做的**。建議補標籤 +
  補一句「200 vs 250Hz 下緣為本文件取用頻段表邊界的結果」。
- **A4（低）§0 的 S1 列把第 17 章標成〈疊層〉。** 實際目錄第 17 章標題是 **"Sound Design"**，
  layering 是章內小節。建議改成「第 17 章〈Sound Design〉內的疊層小節」。
- **A5（低）§6 表格兩處精度流失。** (a)「掌機/手機 -16 LUFS，容許範圍 -18 ~ -14」本身就是
  對稱 ±2，與同格註記「S5 註明『無向上放寬』」自相矛盾，本次 fetch 也未取回該註記，
  建議刪除或標未溯源。(b) ATSC A85 列印「-24 LUFS」但 S5 原文是 "-24 LUFS for the
  **'Anchor Element'**"，而 EBU R128 的 -23 是 "for the whole program"——兩者量測對象不同，
  並排成對照組會誤導，建議補上 anchor element 限定詞。

### C. 誠實侷限節在場檢查

**在場且充分。** §9 五條（下限過濾器非美學裁判／經驗區間非物理定律／三項明確空白／
衍生常數須走 informational 流程／自查 §0 候選未被誤用）齊備；此外 §1、§3、§4、§6 各自
帶章內誠實侷限段，§0 把「親眼開啟」與「403 未讀」分表列。這部分不需修改。

**未稽核項**：S9（Krotos）、S6 以外的 403 候選表未重新嘗試開啟；§8 的六支檢查器均未實作，
本次不評其可行性。

**裁決建議**：A1、A2 修完即可解除 draft 標記；A3–A5 屬精度修飾，不阻斷。
