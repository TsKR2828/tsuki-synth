# D1 梁／板阻尼文獻補搜（含 D4 舌鼓 ICSV27、D6 Wood Handbook Table 5–15）

> 卡號：WF0925-L1（研究 lane）　日期：2026-09-25　執行：Claude（研究卡）
> 範圍：`TODO.md`「D. 還要補搜的資料」的 D1（本檔主體）、D4（§6）、D6（§7）。
> 規則：R4——**只引用本卡自己 fetch 到全文的來源裡的數字**，逐字引述（每條英文引述少於 15 字）＋URL＋頁碼；
> 只看到摘要或搜尋引擎摘要的，標「僅摘要」且不引數字；找不到就寫找不到。
> 本卡**沒有改任何程式、沒有渲染任何音訊**。§3 的數字是「描述用、非 GATE」的推導，不是新容差、不是判定門檻。
> **程式行號一律指 HEAD 18430c4**（工作樹裡 `ChromaticEngine.h`、`PlateModel.h` 有其他 lane 未 commit 的修改，行號會差 8 行；
> `BeamModel.h`、`MaterialDB.h`、`data/materials.json`、`src/score/` 與 HEAD 相同）。
> 本卡分兩輪完成：第一輪被 session 用量上限中斷；第二輪（接手）重新核對了全部來源檔雜湊、71 條引文、
> 關鍵表格數字（渲染原頁目視），更正行號與一處頁碼，並補上 §3.4（厚度依賴）與 handpan／舌鼓的補搜。核對紀錄在證據檔 §8。
> 證據（逐條 URL、fetch 結果、引文自我核對、計算輸出）：`reports/gate_outputs/wf0925_L1_sources.txt`。
> 受版權保護的論文全文**沒有**存進 repo（只在本機暫存區讀取；證據檔只記 SHA256 與頁碼）。

---

## §0 一句話結論（先看這裡）

1. **D1 文獻面已補到能取得的上限**：拿到 8 份和梁／板阻尼直接相關的全文（Chaigne & Lambourg 2001、
   Ege 等 2009、Arcas & Chaigne 2010、Chaigne & Doutaut 1997、Humbert 等 2017、Cross & Lifshitz 2001、
   Zeng 等 2022、Irvine 2010），外加 Euphonics 三頁與 Wood Handbook。
   文獻對「金屬梁／板在空氣中為什麼衰減」的講法很一致：**是幾種機制相加，每種有自己的規律**——
   熱彈性（金屬才有，跟厚度平方成反比，在音頻範圍幾乎是固定的衰減速度）、
   黏性空氣（隨頻率的平方根慢慢變大）、
   聲輻射（低於「重合頻率」時很小，接近它時暴增，超過後大致持平）、
   支撐／接點損耗（很難算，論文都是量出來或刻意用細線吊起來避開）。
2. **BeamModel 的 `*2`**：
   - **反對把它當物理項**——沒有任何一份來源用「材料損耗乘一個固定倍數」來描述梁的額外阻尼；
     上面四種機制沒有一種的頻率形狀是「材料項 ×2」那種「跟頻率成正比」的樣子。
   - **無法判斷它的量該不該拿掉**——鋼舌片在 262 Hz：已知機制的描述用合計區間是 0.11～0.36 /s，
     模型拿掉 `*2` 是 0.26 /s、保留是 0.42 /s；而支撐（舌片接鼓身）這一塊文獻給不出數字。
     鋁舌片反過來：光熱彈性一項（0.38～0.54 /s）就比保留 `*2` 的模型（0.23 /s）還多。
   - 真正能定量的只有實測（`TODO.md` D7）或 D4 那篇舌鼓論文，兩者都還沒有。
   - 結論是「文獻不能替 `*2` 的去留提供錨點」，選項與代價列在 §4，**不替月月選**。
3. **附帶發現（跟 `*2` 無關但更根本）**：模型的三個阻尼項在頻率趨近 0 時全部變 0；
   Chaigne & Lambourg、Chaigne & Doutaut、Humbert 三篇都放了「跟頻率無關的常數項」，
   理由是實測的衰減在低頻會停在一個正值。這跟弦在 B1 之前低音 T60 發散是同一種結構缺口（§2.6）。
4. **第二個附帶發現（接手輪補）：模型的衰減完全不看舌片厚度**。引擎在調音到 MIDI 之後，只用「發聲頻率＋材料」重算 T60；
   文獻的每一種機制都跟厚度 h 有關（熱彈性 ∝1/h²、輻射與重合頻率 ∝1/h）。出貨的月光空靈鼓樂譜用了 2.0／2.6／3.2 mm 三種厚度，
   同一個音高在模型裡衰減一樣，文獻則指向熱彈性差 2.56 倍。任何「固定倍數」（包括 `*2`）都表達不了這件事（§3.4）。
5. **D6 完成**：從美國林務局官方站抓到 FPL-GTR-282 第 5 章，Table 5–15 在第 5–36 頁，全表轉錄在 §7。
6. **D4 仍拿不到**：13 條路徑（機構庫、ResearchGate、IIAV 大會網站、Wayback、ORCID、OpenAlex 等）＋接手輪再試 2 條，
   全部失敗，清單在 §6。搜尋引擎摘要裡的頻率數字**本卡不採用**。handpan／鋼盤另查 3 份：兩份拿到全文但**沒有任何阻尼數字**，
   一份（York 碩士論文）檔案太大抓不下來，只有摘要（§5 缺口 1）。

---

## §1 問題

- `src/physics/BeamModel.h:52-56` 的衰減律：`1/T60 = 2·(eta·f/2.2) + beam_plate_beta_air·f² + beam_plate_gamma_radiation·f`。
  第一項的 `* 2.0f` 是舊的「梁比弦衰減快」經驗加權；阻尼寬頻化後變成「全音域一律 2 倍」且沒有錨點
  （`reports/damping_broadband_findings.md` §5；`TODO.md`「BeamModel `*2` 阻尼加權去留」，前置是 D1）。
- `beam_plate_beta_air`、`beam_plate_gamma_radiation` 兩欄在 `data/materials.json` 仍是查無出處的擬合值
  （`src/physics/MaterialDB.h` 檔頭）。`PlateModel`（水鑼）用同一條律但沒有 `*2`（HEAD `src/physics/PlateModel.h:39-50`）。
- 這條律在引擎裡是**調音到 MIDI 之後**、用發聲頻率重算的：score 路徑 HEAD `src/engines/ChromaticEngine.h:346-347`、
  外掛路徑 `:211-212`（外掛另乘巨集旋鈕係數 `matScale·dmpScale`，定義在 `:205-206`），兩者都呼叫 `decayTimeForMode()`（`:692-698`）。
  所以 T60 只取決於「發聲頻率＋材料」，**舌片長、寬、厚都不進衰減**。（D8 裁決包 §3.1 的模態 T60 表與此一致：
  MIDI 37 = 69.30 Hz 的 68.68 s 正是這條律在 69.30 Hz 的值。）
- 弦的空氣阻尼公式（Cuesta & Valette）內建圓截面，不適用矩形截面的舌片與板。
- 本卡要回答：(a) 矩形截面梁在空氣中的阻尼模型；(b) 板的輻射阻尼在重合頻率上下的行為；
  (c) 實測損耗因子範圍；(d) 這些證據對 `*2` 去留是支持、反對還是無法判斷。

---

## §2 外部證據

### 2.1 來源分級

| 代號 | 來源 | 等級 | 取得狀態 | 用在哪 |
|---|---|---|---|---|
| S1 | A. Chaigne, C. Lambourg, *Time-domain simulation of damped impacted plates. I. Theory and experiments*, JASA 109(4) 1422–1432 (2001) | A（同儕審查＋實測） | ✅ 全文（作者首頁連結的自存 PDF） | 熱彈性、輻射、常數項、鋁／玻璃／碳纖／雲杉板實測 |
| S2 | K. Ege, X. Boutillon, B. David, *High-resolution modal analysis*, JSV 325 (2009) 852–869（arXiv:0909.0885） | A | ✅ 全文（arXiv） | 重合頻率公式、重合頻率以上的漸近輻射衰減、鋁板實測 |
| S3 | K. Arcas, A. Chaigne, *On the quality of plate reverberation*, Applied Acoustics 71 (2010) 147–156 | A | ✅ 全文（作者首頁連結的自存 PDF） | 金屬板四種損耗、熱彈性公式＋鋼／鋁／銅常數表、接點損耗 |
| S4 | A. Chaigne, V. Doutaut, *Numerical simulations of xylophones. I.*, JASA 101(1) 539–557 (1997) | A | ✅ 全文（同上） | 木琴條（梁）實測衰減律 `a0 + a2 f²`、支撐繩損耗、輻射小 |
| S5 | T. Humbert 等, *Wave turbulence in vibrating plates: the effect of damping*（arXiv:1709.09438, EPL 草稿） | A | ✅ 全文（arXiv） | 0.5 mm 鋼板實測衰減 ∝ f^0.6、邊界損耗 |
| S6 | M. C. Cross, R. Lifshitz, *Elastic wave transmission at an abrupt junction in a thin plate…*, PRB 64 085324 (2001)（arXiv:cond-mat/0011501） | A（理論） | ✅ 全文（arXiv） | 「從同厚度板切出來的梁」的支撐損耗上限 |
| S7 | Y. Zeng 等, *Air Damping Analysis of a Micro-Coriolis Mass Flow Sensor*, Sensors 22(2) 673 (2022)，CC BY 4.0 | A（微米尺度） | ✅ 全文（PMC8778587） | 矩形截面梁的黏性空氣阻尼式（轉引 Maali 等）、空氣常數 |
| S8 | T. Irvine, *Damping Properties of Materials*, Rev. D (2010)（vibrationdata 教學講義；表 1–2 自稱取自 Cremer & Heckl 1988） | B（二手彙編） | ✅ 全文 | 金屬損耗因子表 |
| S9–S11 | J. Woodhouse, Euphonics §2.2.7、§10.3.3、§4.3（線上教科書） | B | ✅ 網頁原文 | 音叉阻尼量級、支撐加阻尼、有限板在臨界頻率以下仍會輻射 |
| S12 | USDA FPL, *Wood Handbook* FPL-GTR-282 (2021) Ch.5（Senalik & Farber） | A（政府出版、公領域） | ✅ 官方 PDF | 木材內耗（§2.5）、D6 Table 5–15（§7） |
| S13 | 同上 FPL-GTR-190 (2010) Ch.5（Kretschmann），非官方鏡像 | 對照用 | ✅ PDF | 只用來確認兩版 Table 5–15 相同 |
| S14 | A. Chaigne, C. Touzé, O. Thomas, *Nonlinear vibrations and chaos in gongs and cymbals*, AST 26(5) (2005) | A | ✅ 全文 | **沒有阻尼數字**，只說阻尼係數「由實驗取得」，本檔不引數字 |
| S15 | M. Schäfer 等, *Physical Modeling of Vibrating Plates*, DAGA 2019 | C（合成用模型） | ✅ 全文 | 只有「頻率無關＋頻率相關」兩個唯象阻尼參數，**沒有物理數值**，不引 |
| S16 | T. D. Rossing, A. Morrison, U. Hansen, F. Rohner, S. Schärer, *Acoustics of the HANG: A hand-played steel instrument*, ISMA 2007（8 頁） | A（會議全文） | ✅ 全文（接手輪） | handpan 的祖型 Hang 的模態與輻射；**全文沒有任何衰減／阻尼數字**，不引 |
| S17 | P. Bryde, L. Mahadevan, *Localization in musical steelpans*（arXiv:2212.14465，17 頁） | B（arXiv 預印本，只做關鍵字搜尋未細讀） | ✅ 全文（接手輪） | 鋼盤音區的局部化；**全文沒有出現 damping／decay 字樣**，不引 |

**只拿到摘要／搜尋摘要、本檔不引任何數字的**：Zoghaib & Mattei 2013（*Damping analysis of a free aluminum plate*，
HAL 被防爬蟲擋，只拿到 HAL API 的書目）、Hosaka 等 1995（付費）、Sader 1998（未取得）、
Xie/Thompson/Jones 2005（*radiation efficiency of baffled plates and strips*，403/405）、Judge 等 2007（未取得）、
Sumali & Carne（OSTI，連線憑證錯誤）、Naeli & Brand（Georgia Tech 庫 403）；
接手輪新增：E. Alon 2015 York 碩士論文 *Analysis and Synthesis of the Handpan Sound*（全文 PDF 超過 WebFetch 10 MB 上限，
只拿到論文頁摘要；摘要提到演奏方式影響「decay time」但沒有數字）、Van Eysden & Sader 2007（JAP 101 044908，墨爾本大學頁面憑證錯誤；
依題名是 Sader 1998 矩形懸臂梁黏性流體響應推廣到任意模態階數，**是否涵蓋舌片的高 β 範圍未知**，只是 §5 缺口 4 的候選）。逐條見證據檔。

### 2.2 熱彈性（金屬梁／板特有）

- S1 p.1422：「metallic plates will be subjected to thermoelastic damping」。
- S1 p.1423 式 (6)（圖像核對）：鬆弛時間 τ = ρCh²/(κπ²)，並說「the thermoelastic losses decrease as the thickness h of the plate increases」。
- S1 p.1427（鋁板 a1 厚 2 mm、a3 厚 4 mm）：平均衰減「about four times greater for plate a1 than for plate a3」——厚度差 2 倍、衰減差約 4 倍，對應 1/h²。
- S1 Table II p.1431（圖像核對）：鋁的熱彈性擬合常數 R1 = 8.45×10⁻³、c1 = 8.0×10⁻⁴ rad m² s⁻¹。
- S3 p.152：「Thermoelasticity is the dominant internal damping in thin metallic plates」；
  「We also ignore viscoelasticity since it is negligible in most structural metals」。
- S3 p.152 式 (21)（圖像核對）：α(ω) ≈ ω²R1C1 / (2(ω²h² + C1²/h²))，高頻漸近值 α∞ = R1C1/(2h²)
  ——**過了轉折頻率之後，衰減速度與頻率無關**。
- S3 Table 2 p.153（0.5 mm 板，圖像核對）：

  | 材料 | R1 | C1 (rad m²/s) | α∞ (rad/s，即 1/s) | f₀.₅ (Hz) | f₀.₉₅ (Hz) |
  |---|---|---|---|---|---|
  | Steel 1 | 9.416×10⁻³ | 0.14965×10⁻³ | 2.79 | 95 | 415 |
  | Steel 2（SAE 1010） | 9.664×10⁻³ | 0.1855×10⁻³ | 3.55 | 118 | 514 |
  | Copper | 5.691×10⁻³ | 1.148×10⁻³ | 13.00 | 731 | 3187 |
  | Aluminum | 9.975×10⁻³ | 0.976×10⁻³ | 19.28 | 621 | 2708 |

- S2 p.25（5 mm 鋁板）：熱彈性「0.14 s-1 for this aluminium plate」以下，
  「very small compared with radiation damping in this frequency range of interest」。
- S5 p-3（0.5 mm 鋼板）：Zener 模型給出與頻率無關的小值，「roughly estimated at 0.8s-1 for our plate」。
  注意 S5 的 γ 是**能量**衰減率（p-3：「This energy decrease can fitted for each frequency by an exponential law」），
  換成振幅是約 0.4 /s；S3 同厚度鋼的 α∞ 是 2.79～3.55 /s，**兩篇差約 7～9 倍**，本卡不裁定哪個對（§5 缺口 5）。

### 2.3 黏性空氣（矩形截面梁）

- S7 式 (7)–(10)、(23)（由 PMC 的 MathML 逐符號轉錄）：
  - β = ρωL_c²/(4μ)（式 7）；β₁ = (π/4)ρL_c²ωΓ′（式 8）
  - Γ′ = b₁√(1/(2β)) + b₂/(2β)，「with b 1 = 3.8 and b 2 = 2.7」（式 9；S7 註明轉引 Maali 等，
    並寫明只在 1 < β < 1000 的範圍「a relatively simple expression can be found for」Γ′）
  - β₁ = (b₁/4)πL_c√(2ρμω) + (b₂/2)πμ（式 10）；Q = ωρ_l/β₁（式 23）
  - S7 Table 2：空氣密度 1.2 kg/m³、空氣黏度 1.81×10⁻⁵ kg/(m·s)。
- **本卡推導**（R4「推導」類；取 L_c = 梁寬 b、ρ_l = ρ_s·b·h，振幅衰減 α = ω/(2Q)）：
  α_air = (b₁π/8)·√(2ρμω)/(ρ_s·h) + (b₂π/4)·μ/(ρ_s·b·h)。
  白話：第一項**跟梁寬無關、跟厚度成反比、隨 √f 變大**；第二項跟頻率無關。
  **對照模型**：`beam_plate_beta_air·f²` 是隨 f² 變大——形狀跟這條式子不同。
- **適用範圍警告**：舌片預設寬 2 cm，β 在 131 Hz 就是 5.4×10³、在 4186 Hz 是 1.7×10⁵（證據檔 B3），
  **遠超過 S7 驗證過的 1..1000**；§3 的黏性空氣數字是外插，只能看量級。
- 旁證：S7 摘要「the Q factor increases when the resonance frequency increases」（一大氣壓下）——
  頻率越高、空氣造成的相對損耗越小，跟 f² 項「越高頻越重」的方向相反。

### 2.4 聲輻射與重合（臨界）頻率（板）

- 重合頻率公式，S2 p.24 式 (25)（圖像核對）：f_c = (c_a²/(2πh))·√(12ρ(1−ν²)/E)，c_a ≈ 343 m/s。
  本卡用 repo 的鋁／玻璃材料值重算，跟論文印的 f_c 對得上（鋁 2 mm 算 6013 Hz／S1 印 6 kHz；
  鋁 4 mm 3006 Hz／3 kHz；鋁 5 mm 2405 Hz／S2「about 2.4 kHz」；玻璃 2 mm 5979 Hz／5.8 kHz），證據檔 B2-check。
- **重合頻率以下**：
  - S1 p.1424（吊起來的板）：低頻域「viscoelastic and/or thermoelastic losses are the main causes of damping」。
  - S1 p.1425 式 (20)(21)（圖像核對）：無限板在 Ω = ω/ω_c < 1 時，輻射修正項是實數（本卡對公式的解讀：不產生衰減）。
  - S11：有限大小的板「can always radiate some sound even at frequencies well below critical」——
    有限大小的板在臨界頻率以下仍會漏一點，靠邊緣與角落；S3 p.153 式 (26) 給了 Maidanik 的估算式，
    但前提是「簡支、有障板、模態很密」，**跟一根窄舌片不符，本卡不代算**。
  - S5：0.5 mm 鋼板重合頻率約 20 kHz（「coincidence frequency for acoustic radiation can be estimated in the vicinity of 20 kHz」），
    量到的衰減率隨頻率呈冪次律，「an exponent close to 0.6」（±0.05）。
- **接近與超過重合頻率**：
  - S2 p.24：衰減從約 4 /s 升到約 15 /s，原因是「the sudden increase in acoustical radiation when the frequency approaches the coincidence frequency」；
    「for a finite plate, the increase in radiation efficiency is gradual」。Table 7（p.25，圖像核對）：2069～2098 Hz 五個模態 α = 10.3～18.8 /s。
  - S2 p.25 圖 16 說明（圖像核對）：「damping factor α of an infinite plate above the coincidence frequency」的漸近值 α∞ = ρ_a c_a/(ρh)，ρ_a = 1.2 kg/m³。
    **注意：這是一個與頻率無關的衰減速度**。
  - S1 p.1424：重合頻率以上「the damping is mainly governed by radiation for low dissipative materials」；
    p.1427「the radiation clearly becomes the dominant damping mechanism above the critical frequency」；
    玻璃板 p.1429：「a noticeable increase around the critical frequency followed by an almost constant value」（150 s⁻¹，圖像核對）。
  - S3 p.153 式 (25)（圖像核對）：α_rad = (ρ_a c_a/(ρh))·σ（σ 為輻射效率）；「For frequencies above fc, the plate radiates efficiently」。
- **對照模型**：`beam_plate_gamma_radiation·f` 在重合頻率上下都是一條直線，沒有「以下很小、附近暴增、以上持平」的形狀。

### 2.5 支撐／接點損耗

- S1 p.1424：論文把板用細線吊起來，在這種情況下「there is no damping due to coupling at the boundaries」——也就是**刻意把這一項排除掉才量材料**。
- S3 p.152：「We consider four main sources of damping in metallic plates」（熱彈性、自由場輻射、多孔材料近場輻射、接點）；
  「the losses at the attachment points cannot be easily modeled」，只能用「實測總量減模型」估；
  p.155：為了避免大的接點損耗，「the plate is usually attached to its supports on punctual locations」。
- S2 p.23：同一塊板換吊法，衰減就變；尼龍線吊法「more strongly transmitted to the suspension frame by the nylon lines」。
- S5 p-3：「A part of the energy is also dissipated at the clamped boundary」（夾在橡膠墊之間）。
- S4 p.546：木琴條的吊繩摩擦只在「significant for frequencies below the fundamental of the lowest bar only」。
- S10：「it is difficult to support the test sample with adding [原文如此] significant extra damping」——支撐本身就會加阻尼。
- S8 p.6：「boundaries and bearings contribute damping」。
- **S6（最接近舌鼓幾何的理論）**：把梁當成從一塊板切出來，支撐也是「also treated as thin plates of the same thickness」——
  這正是舌鼓「舌片從鼓面切出來」的幾何。結論（p.34）：「L/w for the fundamental compression mode, torsion mode, and flexural-bending mode」，
  即彎曲模態 Q ∼ L/w。但前提是「suppose that all the energy communicated to the support modes is lost」，
  作者也說（p.5）「In practice this expression for the dissipation may be an overestimate」。
  **套到預設舌片**（L = 0.078～0.220 m、w = 0.02 m，L/w ≈ 3.9～11）會得到 Q 只有個位數，這顯然不是會響好幾秒的舌鼓——
  意思是鼓身把大部分能量又還給舌片，**真正的損耗取決於鼓身自己的阻尼與輻射**，文獻給不出數字（§5 缺口 2）。

### 2.6 「與頻率無關的常數項」

- S1 p.1424：黏彈模型在 ω→0 時損耗變 0，但「experimental decay factors usually tend to a constant」正值，
  所以加了「an arbitrary viscous damping term」R_f；式 (42)（p.1429，圖像核對）裡這一項以 R_f/2 出現在衰減率中，與頻率無關。
  Table II（p.1431，圖像核對）：R_f = 鋁 0.032、玻璃 0.88、碳纖 0.8、木 2.4 s⁻¹。
- S4 p.546 式 (18)(19)（圖像核對）：木琴條實測衰減「described by an empirical law of the form」α(f) = 1/t_d = a₀ + a₂f²，
  其中 a₀ 是常數項（γ_B = 2a₀）。Table I（p.544）：Padouk 條 γ_B = 12.44 s⁻¹、Rosewood 條 γ_B = 51.58 s⁻¹。
- S3 式 (21)：熱彈性在音頻範圍就是常數 α∞（§2.2）；S5：Zener 熱彈性「frequency-independent」。
- **對照模型**：`BeamModel`／`PlateModel` 三項在 f→0 全部 →0，沒有常數項；低音舌片 T60 因此很長（鋼 131 Hz：保留 `*2` 35 s、拿掉 60 s，§3）。
  這和弦在 B1 之前「低音 T60 發散、缺一條頻率無關的損耗通道」是同一種缺口。

### 2.7 實測損耗因子／衰減範圍（本卡取得的全部數字）

| 對象 | 數字（原文單位） | 出處 |
|---|---|---|
| 鋁，彎曲損耗因子 | ≈ 10⁻⁴ | S8 Table 2 p.2（圖像核對；S8 自稱取自 Cremer & Heckl 1988） |
| 鋼，縱向損耗因子 | 0.2～3 (10⁻⁴)；**彎曲欄空白** | 同上 |
| 鐵，縱向／彎曲 | 1～4 (10⁻⁴)／2～6 (10⁻⁴) | 同上 |
| 黃銅，縱向／彎曲 | 0.2～1 (10⁻³)／< 10⁻³ | 同上 |
| 銅（多晶），縱向／彎曲 | ≈ 2 (10⁻³)／≈ 2 (10⁻³) | 同上 |
| 音叉（阻尼比 ζ） | 「Tuning fork: ζ_n ≈ 10⁻⁴」（損耗因子 η = 2ζ，同頁） | S9 |
| 鋁板 1.9 mm（AU4G，300×300 mm，橡皮筋吊） | 「Without the block of foam, damping factors are around 3 s-1」 | S2 p.15–16 |
| 鋁板 5 mm（1000×1619 mm） | 約 4 s⁻¹（1685–1697 Hz）→ 10.3～18.8 s⁻¹（2069–2098 Hz，近 f_c≈2.4 kHz） | S2 p.24–25 |
| 鋁板 2 mm／4 mm | 平均衰減前者約為後者 4 倍（熱彈性 1/h²）；超過 f_c 後輻射主導 | S1 p.1427 |
| 玻璃板 2 mm | f_c 以下衰減隨頻率「an almost linear relationship」（S1 說比例阻尼成立，即固定損耗因子，式 40）；約為同尺寸鋁板「nearly ten times greater」；f_c 以上約 150 s⁻¹ | S1 p.1429 |
| 碳纖板／雲杉板 | 「constant Q values around 250」／Q「nearly equal to 80」 | S1 p.1429–1430 |
| 雲杉板（Euphonics） | 「For the quarter-cut plate, the values were η₁ = 0.0051」，η₃ = 0.0216、η₄ = 0.0164 | S10 |
| 木材（對數衰減率） | 「ranges from about 0.1 for hot, moist wood to」「less than 0.02 for hot, dry wood」 | S12 p.5–21 |
| 木琴條（Padouk／Rosewood） | α = a₀ + a₂f²；γ_B = 12.44／51.58 s⁻¹；黏彈常數 9.16×10⁻⁸／2.35×10⁻⁷ s | S4 p.544、546 |
| 0.5 mm 鋼板（2×1 m，一邊夾住） | 衰減率 ∝ f^0.6±0.05；熱彈性約 0.8 s⁻¹（能量） | S5 p-2、p-3 |

- 木材換算（本卡推導，δ = πη 的小阻尼關係）：對數衰減率 0.02～0.1 → η ≈ 0.0064～0.032；
  repo 的 `wood_spruce 0.007`、`wood_maple 0.012`、`wood_birch 0.014`、`wood_oak 0.016` 都在這範圍內。
- S10 同頁也說「Stiff materials like ceramics or hardened steel tend to have low damping」。

---

## §3 引擎現況數字 vs 文獻機制量級（描述用、非 GATE）

> 以下全部由 `output/wf0925/L1/calc_d1.py` 算出（輸出全文貼在證據檔）。衰減一律換成振幅衰減速度 α = ln(1000)/T60（1/s），
> 越大＝越快安靜。§3.1–3.3 的幾何用**外掛路徑**預設舌片：寬 0.02 m（HEAD `src/engines/ChromaticEngine.h:179`）、
> 厚 0.003 m（`:180` 的後備值；`chr_thickness` 參數預設也是 3.0 mm，`src/ParameterLayout.cpp:91-92`）；材料值用 `data/materials.json`。
> score 路徑的幾何由樂譜決定，§3.4 另算出貨樂譜實際用的三種厚度。
> 這些**不是判定門檻**，只是把「模型的每一項」和「文獻每種機制」放在同一把尺上看量級。

### 3.1 BeamModel 四個分項（鋼，`eta=2e-4`、`beta_air=1.2e-7`、`gamma_rad=2e-5`）

| 頻率 | 材料項×2 | 材料項×1 | β_air·f² 項 | γ_rad·f 項 | T60（保留 ×2） | T60（拿掉 ×2） | ×2 多出來的部分佔總衰減 |
|---|---|---|---|---|---|---|---|
| 130.8 Hz（C3） | 0.164 | 0.082 | 0.014 | 0.018 | 35.15 s | 60.38 s | 41.8% |
| 261.6 Hz（C4） | 0.329 | 0.164 | 0.057 | 0.036 | 16.39 s | 26.86 s | 39.0% |
| 523.2 Hz | 0.657 | 0.329 | 0.227 | 0.072 | 7.22 s | 11.00 s | 34.4% |
| 1046.5 Hz | 1.314 | 0.657 | 0.908 | 0.145 | 2.92 s | 4.04 s | 27.8% |
| 4186 Hz | 5.257 | 2.629 | 14.525 | 0.578 | 0.34 s | 0.39 s | 12.9% |

- C4 鋼 16.39 s、鋁 30.13 s 與 09-14 整合卡 `--full` 的 `tongue_drum material=steel T60(model)=16.390s`、`aluminum 30.135s` 一致
  （`reports/gate_outputs/wf0914_integration_raw/06_physics_verify_full.txt:477,480`）。
- `*2` 主要影響**基頻與低音**（佔總衰減 39～42%）；到 4 kHz 以上被 `β_air·f²` 蓋過，只剩一成多。
- 鋁、黃銅、青銅的同表在證據檔 §A（黃銅／青銅因材料項本來就大，1 kHz 以下 `*2` 佔總衰減約 43～48%）。

### 3.2 文獻機制在同一片舌片上的量級（厚 3 mm）

| 機制 | 鋼 | 鋁 | 算法 |
|---|---|---|---|
| 熱彈性 α∞ | 0.078～0.100 /s（音頻範圍固定；轉折頻率 2.7～3.3 Hz） | 0.376～0.541 /s（轉折 17 Hz） | S3 式 (21)＋Table 2（鋼 1／鋼 2／鋁）；鋁另用 S1 Table II 擬合常數 |
| 黏性空氣（外插） | 131 Hz 0.012、262 Hz 0.017、1046 Hz 0.034、4186 Hz 0.068 /s | 262 Hz 0.050、4186 Hz 0.197 /s | S7 式 (10)(23)；β 超出驗證範圍 |
| 重合頻率 f_c | 4086 Hz | 4008 Hz | S2 式 (25) |
| f_c 以上無限板輻射 α∞ | 17.6 /s（T60 0.39 s） | 50.8 /s（T60 0.14 s） | S2 圖 16：ρ_a c_a/(ρh) |
| 材料表損耗因子換成 α（262 Hz） | 縱向 0.2～3×10⁻⁴ → 0.016～0.247 /s | 彎曲 ≈10⁻⁴ → 0.082 /s | S8 Table 2；α = πfη |

**並排看 262 Hz（C4）的鋼舌片**：
- 模型：拿掉 `*2` = 0.257 /s，保留 = 0.421 /s。
- 文獻已知機制合計（熱彈性＋黏性空氣＋材料表縱向損耗）＝ 0.11～0.36 /s。
  **沒算進去的**：支撐／鼓身耦合（§2.5，無數字）、窄舌片在 f_c 以下的輻射（無可用公式）。
  而且熱彈性和材料表數字可能部分重疊（表值怎麼量的、含不含熱彈性，S8 沒寫）。
- 所以 ×1 落在區間內、×2 略高於區間上緣，但缺的兩塊只會往上加——**量級上無法判斷**。

**並排看 262 Hz 的鋁舌片**：模型拿掉 `*2` = 0.147 /s、保留 = 0.229 /s；光熱彈性一項就是 0.38～0.54 /s。
文獻指向「鋁舌片在低音其實該衰減得更快」，而且該多出來的是**不隨頻率變的常數**，不是 `*2` 那種跟頻率成正比的量；
到 4186 Hz 則反過來，模型的材料項 ×2（2.63 /s）遠大於熱彈性（0.54 /s）。

**高頻（f_c 附近）**：鋼在 f_c = 4086 Hz 時，模型的 `γ_rad` 項只有 0.56 /s，`β_air·f²` 項是 13.8 /s；
無限板在 f_c 以上的輻射漸近值是 17.6 /s。也就是說，**現在 `β_air·f²` 在 4 kHz 附近「碰巧」扮演了輻射的量級**，
但它在 f_c 以下比黏性空氣外插值大（262 Hz 約 3 倍、1046 Hz 約 27 倍、4186 Hz 約 210 倍）、在 f_c 以上還繼續隨 f² 長，形狀和文獻不符。
預設舌片的第 2、3 模態（懸臂比值約 6.27、17.5）在中高音很容易超過 f_c，這一段對音色影響可能比 `*2` 大（未渲染驗證）。

### 3.3 PlateModel（水鑼）附帶

- 同一條律、沒有 `*2`，低階預設半徑 0.15 m、厚 0.003 m（HEAD `src/physics/PlateModel.h:32-33`）。§3.2 的熱彈性、f_c、輻射量級對 3 mm 鋼／鋁板同樣成立。
- 文獻對板的描述最完整（S1、S2、S3、S5 都是板）：f_c 以下由熱彈性（金屬）或黏彈（玻璃、木）主導、f_c 以上輻射主導並大致持平、再加一個頻率無關的常數項。
  現行 `eta·f + β·f² + γ·f` 三項都不是這個形狀。這屬於 D1 範圍內「Beam/Plate 仍未溯源」的缺口，不涉及 `*2`。

### 3.4 厚度依賴：出貨樂譜的三種舌片（接手輪補；描述用、非 GATE）

- **模型端**：T60 只看「發聲頻率＋材料」（§1 最後一條）。同一個音高，舌片 2 mm 或 3.2 mm，模型算出來的衰減一模一樣。
- **文獻端**：每一種機制都看厚度。
  S1 p.1427 鋁板 2 mm 對 4 mm 平均衰減「about four times greater for plate a1 than for plate a3」；
  S3 p.152「Increasing the thickness of the plate reduces the damping」；
  熱彈性 α∞ = R1C1/(2h²)（S3 式 21，∝1/h²）；重合頻率 f_c ∝ 1/h（S2 式 25）；f_c 以上輻射 α∞ = ρ_a c_a/(ρh)（S2 圖 16，∝1/h）；
  黏性空氣第一項 ∝ 1/h（§2.3 推導）。
- 出貨的 `scores/examples/moonlight_sonata_movement1_tongue_drum.score.json`（與 HEAD 相同，長度一律 100 mm、`frequency_mode` 未指定＝調到 MIDI）
  實際用了三組舌片。下表由 `calc_d1.py` 的 C 節算出（輸出全文在證據檔 §6）：

| 組 | 材料／厚／寬 | 音域 | 事件數 | 模型 T60（×2／×1）低音端→高音端 | 熱彈性 α∞（/s） | f_c | 高於 f_c 的模態 |
|---|---|---|---|---|---|---|---|
| 低音群 | 鋼 3.2 mm／30 mm | MIDI 29–44（43.7–103.8 Hz） | 176 | 110.6／197.2 s → 45.0／78.1 s | S3：0.069～0.088；S5 換算：0.010 | 3831 Hz | 無（第 3 模態最高 1822 Hz） |
| 主體群 | 鋼 2.6 mm／24 mm | MIDI 45–76（110.0–659.3 Hz） | 952 | 42.3／73.3 s → 5.40／7.98 s | S3：0.104～0.133；S5 換算：0.015 | 4715 Hz | 最高音的第 3 模態（11568 Hz） |
| 高音群 | 鋁 2.0 mm／18 mm | MIDI 78–87（740.0–1244.5 Hz） | 14 | 8.18／11.29 s → 3.91／5.02 s | S3：1.22；S1：0.85 | 6013 Hz | 第 3 模態；最高音連第 2 模態（7799 Hz） |

  （「S5 換算」＝把 S5 的 0.5 mm 鋼板熱彈性振幅值 0.4 /s 依 1/h² 換到該厚度，是本卡推導；它跟 S3 差 7～9 倍，見 §2.2、§5 缺口 5。
  外掛預設 3.0 mm 與 score 未指定時的預設 2.0 mm（HEAD `src/score/ScoreParser.h:70,73`）的同組數字也在證據檔 §6 C 節。）

**怎麼讀這張表**：
1. **厚度差造成的差距，模型完全沒有**：3.2 mm 和 2.0 mm 之間，文獻的熱彈性差 (3.2/2.0)² = 2.56 倍、f_c 與輻射差 1.6 倍；模型是 0。
   這是「固定倍數」表達不了的東西——不論倍數是 1 還是 2。
2. **低音群最低的音**：MIDI 29 的模型衰減（×2）是 0.062 /s，**比 S3 算出來的鋼熱彈性單獨一項（0.069～0.088 /s）還小**；
   照 S3，這些音連保留 `*2` 都還衰減得太慢（T60 110.6 s）。但照 S5 換算（0.010 /s），×1、×2 都已經比熱彈性大。
   兩篇文獻分歧 7～9 倍，所以**無法判斷**；能確定的只有：低音區真正缺的是「不隨頻率變的常數項」，`*2`（跟頻率成正比）在 44 Hz 能補的量很小。
3. **高過 f_c 的模態**：主體群最高音的第 3 模態（11568 Hz）模型衰減 127 /s，其中 111 /s 來自 `β_air·f²`；
   文獻的無限板輻射漸近值在這個厚度是 20.3 /s，而且窄舌片的輻射效率只會更低（無公式，§5 缺口 3）。
   鋁高音群最高音的第 2 模態（7799 Hz）模型 39.3 /s、漸近值 76.2 /s。也就是說，**f_c 以上模型有時比文獻上限還大、有時還小，看頻率與材料**；
   這一段的主角是 `β_air·f²`，不是 `*2`。
4. 對裁決的意義：如果將來走 §4.2 的選項 C（機制分解），衰減函式要能拿到舌片厚度（目前 `decayTimeForMode()` 只收頻率與材料），
   是介面層的改動；這點 A、B 兩個選項都不需要。

---

## §4 文獻對 BeamModel `*2` 去留的證據

### 4.1 逐條證據

| # | 證據 | 對「保留 `*2`」 | 說明 |
|---|---|---|---|
| 1 | 八份全文沒有任何一份用「材料損耗 × 固定倍數」描述梁／板的額外阻尼（S1–S7 都是按機制分開建模） | **反對**（作為物理項） | `*2` 找不到可引的來源 |
| 2 | 金屬的熱彈性在音頻範圍是**固定**衰減速度、∝1/h²（S1、S3、S5） | **反對**（形狀） | `*2` 加的是 ∝f 的量；熱彈性不隨 f 長 |
| 3 | 鋁的熱彈性量級（3 mm：0.38～0.54 /s）大於模型保留 `*2` 的低音總衰減（262 Hz：0.23 /s） | 方向上**支持「低音要更多阻尼」**，但不支持 `*2` 這個形式 | 同時在 4 kHz 模型又比熱彈性大 5 倍 |
| 4 | S8 表：鋁彎曲損耗 ≈10⁻⁴，正好等於 repo 的 `eta`；`*2` 等效成 2×10⁻⁴ | **反對**（若把 `*2` 當材料值） | S8 是二手表、單一數字、沒寫厚度與頻率 |
| 5 | S8 表：鋼縱向 0.2～3×10⁻⁴；`*2` 等效 4×10⁻⁴，超出上緣（彎曲欄空白） | 弱**反對** | 縱向不等於彎曲，只能當參考 |
| 6 | 支撐／接點損耗在金屬板上真的存在、難建模、要量（S1、S2、S3、S5、S10、S8）；從板切出來的梁上限可以大到 Q∼L/w（S6） | **支持「梁裝在樂器上會比材料表衰減得快」這個直覺** | 但大小取決於鼓身，文獻給不出「2」這個數 |
| 7 | 鋼 262 Hz：已知機制描述用合計 0.11～0.36 /s，模型 ×1 = 0.257、×2 = 0.421；支撐與窄條輻射未計 | **無法判斷** | 缺的兩塊只會往上加 |
| 8 | 音叉（鋼製、兩支懸臂）阻尼比量級「Tuning fork: ζ_n ≈ 10⁻⁴」→ η ≈ 2×10⁻⁴（S9；只是「量級舉例」，不是量測）；模型鋼舌片 262 Hz 的等效總損耗因子 ×1 ≈ 3.1×10⁻⁴、×2 ≈ 5.1×10⁻⁴ | **無法判斷** | 兩者都在同一量級內；音叉刻意做成平衡、少漏能量到手柄，和舌片接鼓身不同 |
| 9 | 舌鼓本身的衰減實測（D4 論文、或 D7 自己量） | **無法判斷** | 本卡拿不到（§6） |
| 10 | 文獻的每種機制都隨厚度變（S1、S2、S3），模型衰減完全不看厚度；出貨樂譜三種厚度之間熱彈性差 2.56 倍（§3.4） | **反對**（形式） | 任何固定倍數都無法表達厚度依賴；這條同樣反對 ×1，不是只反對 ×2 |
| 11 | 出貨樂譜最低音（鋼 3.2 mm、43.7 Hz）：模型 ×2 = 0.062 /s，S3 熱彈性單獨 = 0.069～0.088 /s，S5 換算 = 0.010 /s（§3.4） | **無法判斷** | 取決於 S3／S5 哪個對；若 S3 對，低音連 ×2 都不夠，缺的是常數項而不是倍數 |

**總結**：文獻**反對把 `*2` 當成物理機制**，**無法判斷**它代表的總量該不該留；
文獻**支持的是另一條路**：把梁／板阻尼拆成「熱彈性常數項＋黏性空氣＋重合頻率輻射＋支撐（鼓身）損耗」，
而且這幾項都跟舌片厚度有關——這是現行律不論 ×1 或 ×2 都缺的（#10）。

### 4.2 之後可以選的方向（給裁決包用；本卡不替月月選）

| 選項 | 做什麼 | 渲染會不會變（R10） | 文獻支持度 | 還缺什麼 |
|---|---|---|---|---|
| A 保留並改標 | `*2` 不動，註解與主張域改寫成「DECIDED CONVENTION，經驗係數，無文獻錨點」 | 不變（8/8 位元不變） | 無支持、也無量級反證 | 月月點頭；`docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` 要加一條 |
| B 拿掉 | 把 `* 2.0f` 刪掉 | **所有 tongue_drum／beam 事件都變**（鋼 C4 T60 16.39→26.86 s、C3 35.15→60.38 s） | 無直接支持（×1 一樣沒有錨點） | R10 前後對照報告、corpus 重驗 |
| C 換成機制分解 | 熱彈性常數項（S3 式 21，材料要補熱常數）＋黏性空氣（S7，需找高 β 範圍的式子）＋f_c 輻射（S2/S3）＋支撐項 | **全部變**，且改動大 | 形式有文獻支持（S1、S3、S4、S5） | 支撐／鼓身損耗的來源（類比 B1 琴橋導納）、窄條輻射、舌鼓實測；衰減函式要能拿到舌片厚度（§3.4 第 4 點）；工作量大 |

- 這張表只列事實；A／B 之間文獻分不出高下，C 是長期路線。
- AI 不需要裁決就能做的下一步：在 scratch 副本跑 A→B 的 R10 前後數字（不落地），附在裁決包裡。本卡沒有做（研究卡不渲染）。

---

## §5 已知缺口（誠實登記）

1. **舌鼓／handpan 的實測衰減：0 份**。D4 拿不到（§6）；網路上的延音秒數都來自廠商頁面，不可引。
   接手輪另查 handpan／鋼盤：S16（Hang，ISMA 2007）與 S17（鋼盤，arXiv）拿到全文，**都沒有衰減數字**；
   Alon 2015 York 碩士論文（handpan 分析與合成，CC BY-NC-ND 2.5）全文 PDF 超過 WebFetch 10 MB 上限，只有摘要。
   摘要提到演奏方式會影響「decay time」，所以它可能有 handpan 的衰減量測（**未證實**，本卡沒看到內文）；月月有空可用瀏覽器手動下載
   （`https://etheses.whiterose.ac.uk/id/eprint/12260/1/EyalMSc.pdf`）。
   D8 裁決包 §5 缺口 5 的「68.68 s 是否離譜無法舉證」狀態不變。
2. **舌片接鼓身的支撐損耗：沒有數字**。S6 只給「全部能量都跑掉」時的上限（Q∼L/w），而舌鼓顯然不是這樣；
   需要的是鼓身（殼）導納——與弦的 B1 琴橋導納同類問題。本卡未找到針對舌鼓殼體的來源。
3. **窄條（舌片寬 ≪ 波長）在 f_c 以下的輻射：沒有可用公式**。Xie/Thompson/Jones 2005 專講「strips」，但 403/405，只有搜尋摘要。
4. **黏性空氣在高 β（舌片是 10³～10⁵）的式子沒取得**。S7 的近似只驗證到 β < 1000；Sader 1998 原文未取得；
   接手輪找到 Van Eysden & Sader 2007 的作者機構頁 PDF，但該站憑證錯誤（self signed certificate），抓不到。
5. **兩篇文獻對 0.5 mm 鋼板熱彈性差 7～9 倍**（S3 Table 2 vs S5 的 0.8 s⁻¹ 能量衰減率），本卡不裁定；鋼的熱彈性數字因此帶這麼大的不確定度。
6. **S8 的金屬表是二手**（標示取自 Cremer & Heckl 1988，原書未取得），而且沒寫量測厚度、頻率；鋼的彎曲損耗欄是空的。
7. **Zoghaib & Mattei 2013（自由鋁板的阻尼分解，含邊緣空氣剪切）**：HAL 全文被防爬蟲擋，只拿到書目。它是最對題的一篇，值得月月有空時用瀏覽器手動下載。
8. `beam_plate_beta_air`／`beam_plate_gamma_radiation` 的 14 組數字**仍然查無出處**；本卡的結論是「它們的頻率形狀與文獻不符」，不是「找到了正確值」。

---

## §6 D4：ICSV27 2021 舌鼓論文全文

- 書目（取自 IIAV 大會網站的投稿摘要清單，已 fetch）：#1117，*EXPERIMENTAL CHARACTERIZATION OF THE STEEL TONGUE DRUM*，
  Bocanegra Cifuentes Johan Augusto, Borelli Davide（Italy），主題 T14「Musical and virtual acoustics」。
  ORCID 公開紀錄只有 Scopus EID `2-s2.0-85117493987`，**沒有 DOI**。
- 試過的路徑（全部失敗；逐條狀態碼在證據檔）：

| # | 路徑 | 結果 |
|---|---|---|
| 1 | `https://unige.iris.cineca.it/bitstream/11567/1063604/1/full_paper_1117_20210430223100647.pdf` | 403（WebFetch 與 curl 皆然） |
| 2 | `https://unige.iris.cineca.it/handle/11567/1063604`、`/retrieve/handle/11567/1063604` | 403 |
| 3 | `http://hdl.handle.net/11567/1063604` | 500 |
| 4 | `https://iris.unige.it/`（新網域） | 連線失敗 |
| 5 | ResearchGate 論文頁與作者自存 PDF 連結 | 403 |
| 6 | `https://www.iiav.org/content/archives_icsv_web/icsv27/` 大會封存頁 | 200，但沒有論文集連結（只有摘要清單） |
| 7 | IIAV 猜測路徑 `…/archives_icsv_last/2021_icsv27/…/full_paper_1117_….pdf` | 404（路徑是本卡猜的，已註明） |
| 8 | docplayer 轉載頁 | DNS 解析失敗 |
| 9 | Wayback Machine（可用性 API＋CDX） | 無 PDF 快照；只有 ResearchGate 的兩張圖檔 |
| 10 | OpenAlex、Crossref 書目搜尋 | 沒收錄 |
| 11 | Semantic Scholar API | 429（兩次） |
| 12 | scholar.archive.org、core.ac.uk | 防爬蟲驗證頁／403 |
| 13 | academia.edu 作者頁 | 403 |
| 14 | 接手輪：第 1 條網址用 WebFetch 再試一次 | 仍 403 |
| 15 | 接手輪：兩組新的 WebSearch（題名＋作者＋ICSV27；作者＋舌鼓＋開放取用） | 只回到第 1、5 條同樣的網址，沒有新的公開副本 |

- 搜尋引擎摘要裡出現的頻率與長度數字、「fixed-free rod」描述：**僅摘要，本卡不採用**（與 D8 裁決包 §5 缺口 1、8 的處理一致）。
- 建議：月月若願意，可用瀏覽器直接開第 1 條網址（該站可能只擋自動抓取），或寫信向作者索取；本卡不寄信。

---

## §7 D6：Wood Handbook Table 5–15（溫度對力學性質的影響）

- 來源：USDA Forest Service, Forest Products Laboratory, *Wood Handbook—Wood as an Engineering Material*, **FPL-GTR-282 (2021)**，
  Chapter 5 *Mechanical Properties of Wood*（C. Adam Senalik, Benjamin Farber）。
  官方下載：`https://research.fs.usda.gov/download/treesearch/62244.pdf`（Treesearch 紀錄 62244）。美國政府出版品，公領域。
- 位置：**第 5–36 頁**；前一頁 5–35 起的「Reversible Effects」段。GTR-190（2010，Kretschmann）同頁同表，數字相同（S13 對照，非官方鏡像）。
- 前導文字（p.5–35/5–36）：「In general, the mechanical properties of wood decrease」受熱時下降、受冷時上升；
  在固定含水率且約 150 °C 以下，「mechanical properties are approximately linearly related」與溫度。
- **Table 5–15. Approximate middle-trend effects of temperature on mechanical properties of clear wood at various moisture conditions**
  （相對於 20 °C (68 °F) 的變化；逐格由官方 PDF 渲染圖核對，文字層的負號會掉，故以圖為準）

| Property | Moisture condition (%) | −50 °C (−58 °F) (%) | +50 °C (+122 °F) (%) |
|---|---|---|---|
| MOE parallel to grain | 0 | +11 | −6 |
|  | 12 | +17 | −7 |
|  | >FSP | +50 | — |
| MOE perpendicular to grain | 6 | — | −20 |
|  | 12 | — | −35 |
|  | ≥20 | — | −38 |
| Shear modulus | >FSP | — | −25 |
| Bending strength | ≤4 | +18 | −10 |
|  | 11–15 | +35 | −20 |
|  | 18–20 | +60 | −25 |
|  | >FSP | +110 | −25 |
| Tensile strength parallel to grain | 0–12 | — | −4 |
| Compressive strength parallel to grain | 0 | +20 | −10 |
|  | 12–45 | +50 | −25 |
| Shear strength parallel to grain | >FSP | — | −25 |
| Tensile strength perpendicular to grain | 4–6 | — | −10 |
|  | 11–16 | — | −20 |
|  | ≥18 | — | −30 |
| Compressive strength perpendicular to grain at proportional limit | 0–6 | — | −20 |
|  | ≥10 | — | −35 |

  註 a（原文）：>FSP indicates moisture content greater than fiber saturation point.
- 下一頁（5–37）有 Table 5–16（鋸材彎曲性質隨溫度的百分比變化式），本卡只記位置不轉錄。
  （第一輪寫成「同頁」，接手輪對 PDF 文字層逐頁搜尋更正：Table 5–16 出現在第 37 頁，第 36 頁沒有。）
- **對 TsukiSynth 的意義（描述用推導，非 GATE）**：12% 含水率、順紋 MOE 在 +50 °C 是 −7%、−50 °C 是 +17%，
  換成每度約 −0.23～−0.24%；頻率 ∝ √E，所以約 −0.12%/°C（約 −2 cent/°C）。
  但 repo 目前**沒有任何消費者**：B5 的 `orthotropic` schema 是死資料，score／UI 也沒有溫度輸入（`docs/WOOD_ANISOTROPY_SOURCES.md` §6）。
  `docs/WOOD_ANISOTROPY_SOURCES.md` 的 :157（§5「本文件未取得該線性關係的逐項係數表」）與 :198（§8 勾選項
  「溫度相依的逐項係數表（Table 5–15）未取得」）可在交接卡改成已取得、指向本檔 §7（本卡不動該檔）。

---

## 附錄 A：來源清單（存取日期一律 2026-09-25）

| 代號 | URL | 取得方式與結果 |
|---|---|---|
| S1 | 作者首頁 `https://sites.google.com/view/achaigne-homepage/home-page/publications` → `https://www.dropbox.com/s/9fccwknzcmoxq8i/chaigne_plate_jasa01.pdf` | WebFetch 全文 PDF（141,466 bytes），頁 1422–1432 |
| S2 | `https://arxiv.org/pdf/0909.0885` | WebFetch 全文 PDF（3,388,249 bytes） |
| S3 | 同作者首頁 → `https://www.dropbox.com/s/xo45kyknt5aja4g/AA_Arcas_Chaigne.pdf` | WebFetch 全文 PDF（958,151 bytes），頁 147–156 |
| S4 | 同作者首頁 → `https://www.dropbox.com/s/uskhd4mmf96kgn6/chaigne_xylo_jasa97.pdf` | WebFetch 全文 PDF（402,514 bytes），頁 539–557 |
| S5 | `https://arxiv.org/pdf/1709.09438` | WebFetch 全文 PDF（1,779,719 bytes） |
| S6 | `https://arxiv.org/pdf/cond-mat/0011501` | WebFetch 全文 PDF（598,230 bytes） |
| S7 | `https://pmc.ncbi.nlm.nih.gov/articles/PMC8778587/`；全文 XML `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8778587/fullTextXML` | WebFetch＋Europe PMC API 全文（CC BY 4.0） |
| S8 | `http://vibrationdata.com/tutorials_alt/damping.pdf` | WebFetch 全文 PDF（40,105 bytes） |
| S9 | `https://euphonics.org/2-2-7-vibration-damping/` | 網頁原文 |
| S10 | `https://euphonics.org/10-3-3-material-damping-and-complex-moduli/` | 網頁原文 |
| S11 | `https://euphonics.org/4-3-sound-radiation/` | 網頁原文 |
| S12 | `https://research.fs.usda.gov/download/treesearch/62244.pdf`（紀錄頁 `https://research.fs.usda.gov/treesearch/62244`） | WebFetch 官方 PDF（5,244,804 bytes） |
| S13 | `https://www.precisebits.com/PDF/USFS_mechanical_properties_of_wood.pdf` | WebFetch PDF（2,226,339 bytes），非官方鏡像，只做對照 |
| S14 | 同作者首頁 → `https://www.dropbox.com/s/v14wqhm3ddqr8ca/Gongs_cymbals_ASJ26_05.pdf` | WebFetch 全文；無阻尼數字 |
| S15 | `https://pub.dega-akustik.de/DAGA_2019/data/articles/000460.pdf` | WebFetch 全文；無物理阻尼數值 |
| S16 | `https://www.hangblog.org/panart/2-S2-4-IsmaRossing.pdf` | WebFetch 全文 PDF（1,211,536 bytes，8 頁）；無阻尼數字（接手輪） |
| S17 | `https://arxiv.org/pdf/2212.14465` | WebFetch 全文 PDF（6,710,296 bytes，17 頁）；無阻尼數字（接手輪） |

- 每個檔的 SHA256、每條英文引述的所在頁（71 條，自動核對 71/71 找到原文）、失敗路徑的狀態碼，都在 `reports/gate_outputs/wf0925_L1_sources.txt`。
- 接手輪另做反向核對：文件裡每一段含英文的「」引述，都要對得上已核對清單（`output/wf0925/L1/check_doc_quotes.py`，結果在證據檔 §8）。
- 公式、表格數字、希臘字母與負號是從 PDF 渲染圖逐格目視核對（標「圖像核對」），因為 PDF 文字層會把它們弄丟。

## 附錄 B：描述用計算怎麼重現

```
python output/wf0925/L1/calc_d1.py      # §3 全部數字（含 §3.4 的 C 節；output/ 已 gitignore；輸出全文已貼進證據檔）
python output/wf0925/L1/verify_quotes.py  # 引文自我核對；需要本機暫存的來源檔，別台機器無法重跑
python output/wf0925/L1/check_doc_quotes.py  # 反向核對：文件內每段英文引述都在已核清單裡、且少於 15 字
```
