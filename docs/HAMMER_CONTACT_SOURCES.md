# 槌頭非線性接觸模型溯源

> 建立：2026-08-15
> 對應 `TODO.md` Verification gap：「Replace the velocity proxy with a
> parameterized nonlinear contact solver using hammer mass, compliance and
> geometry」。
> 體例比照 `docs/MATERIALS_SOURCES.md`／`docs/EIGENVALUE_SOURCES.md`。
>
> **本文件不改任何程式碼、不改任何容差。** 它只回答：真正的槌-弦接觸模型
> 需要哪些數字，以及那些數字拿不拿得到。**拿得到，而且是這幾個缺口裡
> 資料最齊的一個。**

---

## 0. 白話

現在程式模擬「槌子打到弦」的方式是：**先規定**槌子貼在弦上多久
（棉槌 6 ms、氈槌 2 ms、木槌 0.5 ms、金屬槌 0.2 ms），再依高音縮短一點。
那個「多久」是查表填進去的。

真實物理是反過來的：槌頭的氈是一塊**被壓得越扁就越硬**的東西，
接觸多久是**算出來的結果**，不是事先規定的——它由槌子多重、氈多硬、
打多用力共同決定。

好消息：這個「壓得越扁越硬」的關係，文獻上有實測的數字，而且逐音都有。
所以這一項可以從「查表」升級成「算出來」。

順帶查到一件事：**程式目前的力度規則其實對應到「金屬撞金屬」的硬度曲線，
不是鋼琴氈的。** 見 §4。

---

## 1. 現行實作 vs 文獻模型

| | 現行 `src/physics/HammerImpulse.h` | 文獻模型 |
|---|---|---|
| 接觸時間 τc | **規定值**：四檔硬度查表 + `tauCForNote()` 的 `f^-0.32` keytrack | **解出來的**：由 `m`、`K`、`α`、撞擊速度決定 |
| 力脈衝形狀 | 規定為半正弦，其傅立葉轉換當激發頻譜 | 由 `F = K·δ^α` 與槌質量的運動方程解出 |
| 力度相依 | `tauCForStrike()`：`τc ∝ v^-0.2` | `τc ∝ v^(−(α−1)/(α+1))`，隨 `α` 變 |

現行做法在 `HammerImpulse.h` 檔頭已誠實標為「normalised speed proxy」。
本文件提供把它換成真解算器所需的全部常數。

---

## 2. 逐音參數（**文獻，可直接進程式**）

### 2.1 槌氈非線性剛度 `F = K·δ^α`

`δ` = 氈的壓縮量 (m)，`F` = 接觸力 (N)。

| 音 | C2 | C4 | C7 |
|---|---|---|---|
| 量值 `K` | 4 × 10⁸ | 4.5 × 10⁹ | 1 × 10¹² |
| 指數 `α` | 2.3 | 2.5 | 3.0 |

**`K` 的單位隨 `α` 而變**（`N·m^-α`），因為指數不同；這是該表原文明確
標註的性質，不是筆誤。低音到高音跨了 **2500 倍的 K**，這是槌頭在音域上
差異的主要來源。

**來源**：Hall & Askenfelt 的量測，經 Chaigne & Askenfelt 用於模擬研究；
本表轉引自 Woodhouse 的 *Euphonics* §12.2.1 Table 2。
**只有三個音有值**——C2／C4／C7。中間音需要內插，內插方式必須在實作時
明確登記（`α` 隨音高單調上升、`log K` 近似線性，是最保守的假設）。

### 2.2 逐音弦與槌參數

| | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 |
|---|---|---|---|---|---|---|---|---|
| 標稱頻率 (Hz) | 32.7 | 65.4 | 131 | 262 | 523 | 1047 | 2093 | 4186 |
| 弦數 | 1 | 1 | 2 | 3 | 3 | 3 | 3 | 3 |
| 弦長 (mm) | 1013 | 925 | 830 | 639 | 324 | 181 | 96 | 51 |
| 芯線直徑 (mm) | 1.21 | 1.21 | 1.08 | 1.00 | 0.94 | 0.85 | 0.82 | 0.76 |
| 纏繞外徑 (mm) | 5.80 | 3.76 | 1.80 | — | — | — | — | — |
| 總質量 (g) | 189 | 73 | 30.7 | 11.7 | 5.3 | 2.4 | 1.15 | 0.54 |
| 敲擊比 (打擊點/弦長) | 0.135 | 0.135 | 0.130 | 0.125 | 0.12 | 0.10 | 0.09 | 0.08 |
| **槌質量 (g)** | 12 | 11 | 10 | 9 | 8 | 7 | 6 | 5 |
| 槌/弦質量比 | 0.06 | 0.15 | 0.33 | 0.77 | 1.52 | 2.91 | 5.22 | 9.24 |
| **張力/弦長 (kN/m)** | 0.81 | 1.25 | 2.10 | 3.22 | 5.76 | 10.53 | 20.14 | 37.95 |

**來源**：Woodhouse, *Euphonics* §12.2.1 Table 1。槌質量取自 Conklin 與
Hall & Askenfelt；質量由鋼 7800 kg/m³、銅 8960 kg/m³ 算出；彎曲剛度由
鋼芯直徑與 210 GPa 楊氏模數算出。

**自洽檢查（本文件執行）**：由「張力/弦長」「總質量」「弦長」回推
`f₁ = (1/2L)·√(T/μ)`，C1–C8 與表列標稱頻率吻合到 **0.15% 以內**
（例：C4 回推 262.3 Hz vs 標稱 262 Hz）。**「總質量」與「張力/弦長」
都是全部弦的總和**，逐弦值要除以弦數——這是自洽檢查確認的讀法，
不是猜的。

> 這張表也被 `docs/BRIDGE_ADMITTANCE_SOURCES.md` §3 用來取代原本的估算值。

---

## 3. 由 §2 可推導出的東西（**推導**）

質量 `m` 的槌以速度 `v` 撞上 `F = K·δ^α` 的接觸彈簧：

```
½mv² = K·δmax^(α+1)/(α+1)   ⇒   δmax = [(α+1)·m·v² / (2K)]^(1/(α+1))
τc ∝ δmax / v               ⇒   τc ∝ [m/K]^(1/(α+1)) · v^((2/(α+1)) − 1)
```

亦即：

```
τc(v) ∝ v^(−(α−1)/(α+1))
```

| `α` | 力度指數 | 說明 |
|---|---|---|
| 1.5 | **v^−0.200** | 純赫茲接觸（金屬對金屬球面） |
| 2.3 | v^−0.394 | 鋼琴氈，低音（C2） |
| 2.5 | v^−0.429 | 鋼琴氈，中音（C4） |
| 3.0 | v^−0.500 | 鋼琴氈，高音（C7） |

---

## 4. 一個具體發現：現行的力度指數對應到錯的材料

`HammerImpulse::tauCForStrike()` 用 `τc ∝ v^-0.2`。由 §3 的表可見，
**`-0.2` 正好是 `α = 1.5` 的值，也就是純赫茲彈性接觸（金屬球對金屬面）**。
但實測的鋼琴槌氈是 `α = 2.3~3.0`，對應 `v^-0.39 ~ v^-0.50`。

也就是說：現行力度→接觸時間的敏感度，比實測的鋼琴氈**弱了約 2 倍**。

**這不是可以順手改的一行。** 改動會直接撞上 §6 容差登記表的
「velocity ×2 電平」判定（`+6.0206 ± 1.0 dB` 物理律）：2026-08-06 那一輪
就是因為能量預估帶進實際 `τc(velocity)` 而被 `--full` F3 抓到
tongue_drum `+4.72 dB` 次線性 FAIL，最後改用 `velocity=0.5` 的 Hertz 錨
才全綠。把指數從 -0.2 加深到 -0.43 會讓同一個機制更強，**必須連同
「能量正規化層要不要跟著改」一起設計**，不能單獨動。

同理，keytrack 也會從擬合值變成推導值：

| | C2 | C4 | C7 |
|---|---|---|---|
| 由 §3 用實測 `m`/`K`/`α` 推導的相對 τc | 1.000 | 0.726 | 0.451 |
| 現行 `tauCForNote()` 的 `f^-0.32` | 1.000 | 0.641 | 0.330 |

方向與量級一致，現行擬合略陡。**這意味著 2026-08-06 那個 `f^-0.32`
擬合抓到的是真的物理，只是係數是配出來的**；本文件的資料可以把它換成
從 `m`、`K`、`α` 推導的版本。

---

## 5. 遲滯（hysteresis）：**參數已取得**（2026-08-15 補）

真實槌氈在壓縮與回彈時走不同的曲線（能量耗散）。Stulov 的遲滯模型把氈
視為非線性、有歷史相依（hereditary）的材料，鬆弛核為指數型：

```
R(t) = (ε/τ₀)·exp(−t/τ₀)
```

模擬用的參數組：

| 符號 | 意義 | 值 |
|---|---|---|
| `F₀` | 瞬時剛度（彈性參數） | 8800 N/mm |
| `p` | 非線性指數（彈性參數） | 3.95 |
| `ε` | 歷史相依幅度參數 | 0.992 |
| `τ₀` | 鬆弛時間（歷史相依參數） | 2.0 µs |

**`τ₀ = 2.0 µs` 遠小於接觸時間（該文的 1.6 ms）**——這是一個重要的實作
提示：鬆弛在單次接觸內幾乎瞬間完成，數值積分不需要為它縮小時間步長。

**注意 `p = 3.95` 與 §2.1 的 `α = 2.3~3.0` 不是同一組數字**：Stulov 的
`p` 是**含遲滯模型**裡的彈性指數，§2.1 的 `α` 是**純冪律**擬合的等效指數。
兩者不可互換代入，也不可混用同一個 `K`／`F₀`。

純冪律（無遲滯，§2.1）是文獻常用的簡化，仍建議作為第一階段。

---

## 6. 實作需要新增什麼（供裁決，本輪未實作）

| 項目 | 狀態 |
|---|---|
| `K(note)`、`α(note)` | ✅ 三個錨點有文獻值；**內插規則需登記** |
| 槌質量 `m(note)` | ✅ C1–C8 文獻值 |
| 敲擊比 | ✅ C1–C8 文獻值（現行引擎已有 strike position 參數） |
| 接觸解算器 | ❌ 需新寫：槌質量的運動方程 + 弦端反作用力，取代規定的半正弦 |
| 遲滯參數 | ✅ 已取得（§5，Stulov：`F₀`/`p`/`ε`/`τ₀`） |
| 非鋼琴引擎（beam/plate）的 `K`、`α` | ⚠️ **本文件未搜尋**，狀態未知 |

> **2026-08-15 更正**：本節初版寫「非鋼琴引擎完全沒有文獻」。那句話**沒有
> 經過實際搜尋**，是從「搜鋼琴時沒撞見」推論的，不符合本 repo 的舉證標準。
> 正確的陳述是：**本文件未針對舌鼓／鑼的槌具接觸參數做過文獻搜尋，狀態未知。**
> （同日對舌鼓與鑼的**模態**文獻確實搜過並找到結果，見
> `docs/EXTERNAL_ANCHOR_SOURCES.md` §5；但那是模態量測，不是槌具接觸參數。）

**這仍然是真正的風險**：這批資料是**鋼琴專屬**的。Cimbalom/Piano 路徑
可以直接受惠；Chromatic（tongue drum / water gong）在確認有對應量測之前，
不得把鋼琴槌氈的常數搬過去——那會違反 Rule 4。

---

## 7. 引用清單

| # | 出處 | 取得狀態 | 用到什麼 |
|---|---|---|---|
| 1 | Woodhouse, *Euphonics* §12.2.1「Parameter values for piano simulations」 | ✅ 開放（表格為圖片，本文件逐格轉錄） | §2.1 Table 2 的 K/α；§2.2 Table 1 的逐音弦與槌參數 |
| 2 | Chaigne & Askenfelt, *Numerical simulations of piano strings I*, JASA 95(2) 1994 | ✅ 開放全文（掃描 OCR） | 確認 `K`、`p` 與弦阻尼係數 `b1`/`b3` 是由實驗資料以曲線擬合求得；本文件未從此掃描件取任何數值（OCR 表格不可靠） |
| 3 | Hall & Askenfelt（經 #1／#2 轉引） | 間接 | K/α 與槌質量的原始量測來源 |
| 4 | Conklin（經 #1 轉引） | 間接 | 槌質量估計 |
| 5 | Stulov，槌氈遲滯模型 | ⚠️ 僅知存在，參數未取得 | §5 |
| 6 | Askenfelt & Jansson（KTH），接觸時間量測 | 已引於 `HammerImpulse.h` 檔頭 | 現行 τc 錨點的既有依據 |

**沒有從任何論文圖表數位化取值**——§2 兩張表都是原文的數值表格，逐格轉錄。

---

## 8. 狀態

- [x] 取得可實作的接觸律與逐音常數（§2）
- [x] 推導力度／音高相依關係並與現行實作對照（§3、§4）
- [x] 指出現行 `v^-0.2` 對應 `α=1.5`（純赫茲）而非鋼琴氈 `α=2.3~3.0`（§4）
- [x] 遲滯參數取得（§5，Stulov `F₀=8800 N/mm`、`p=3.95`、`ε=0.992`、`τ₀=2.0 µs`）
- [ ] beam／plate 引擎的槌具接觸參數**未搜尋**，狀態未知（§6，**這是本項最大的阻擋**）
- [x] **實作**——完成（2026-08-27，B4，月月裁決 (b) 重定義 F3 主張域後收尾）。
      `src/physics/HammerImpulse.h`（§2 三常數表＋內插＋`pianoHammerTauC()`，錨定
      `kTauCFelt`@A4/v=0.5）＋ `src/engines/CimbalomEngine.h` 4 呼叫點 Felt 分支；
      非 Felt／Chromatic 位元不變已證（`reports/gate_outputs/b4_nonfelt_invariance.txt`）。
      Rule 6 三 build＋ctest／pytest 全綠（`b4_build_{cli,standalone,vst3}.txt`、
      `b4_ctest.txt`、`b4_pytest.txt`、`b4_selftest.txt`）；§6 velocity 列重新驗證＝
      F3 主張域二分（固定 tau_c 路徑不動、tau_c(v) 路徑改模型自洽判定，容差數值不變）：
      FAIL 存證 `b4_gate_full_FAIL.txt`＋`b4_f3_alpha_monotonicity.txt`、裁決包
      `reports/decision_packets/B4_f3_velocity_ruling.md`、重定義後
      `b4_gate_full_after_f3_redefine.txt`＋哨兵 `b4_f3_redefine_sentinel.txt`；
      corpus 重驗 `b4_corpus_all.txt`；Rule 10 前後對照
      `reports/b4_hammer_contact_before_after.md`。

---

## 9. 槌力譜滾降（B-1 依據）文獻搜尋（WF0914-D10，2026-09-14）

> 目標：A14 裁決包點名的兩篇缺口文獻——**Hall & Askenfelt 1988**（JASA 83(4):1627,
> *Piano string excitation V: Spectra for real hammers and strings*）與
> **Chaigne & Askenfelt 1994 Part II**（JASA 95(3):1631）——的**真槌力譜滾降**資料
> （dB/octave 或等價頻譜圖數值）。**本節只記文獻，不提案實作，不改 `src/`。**
> 逐頁 fetch 證據存 `output/wf0914/D10/fetched_excerpts.md`。

### 9.1 管道逐項記錄（依 WF0914_D10 卡 §1 順序）

1. **KTH STL-QPSR / 五講義**（speech.kth.se，本 repo 既有引用來源）：
   逐頁查驗 `hall/compare.html`、`hall/theory.html`、`hall/complica.html`、
   `hall/further.html`、`askenflt/stricont.html`、`askenflt/coda.html`。
   `hall/compare.html` 有一條相關但**不是**槌力頻譜本身的引句（見 9.1a）；
   其餘頁面皆未出現「dB」「octave」等關鍵詞用於描述槌力頻譜滾降。
   另嘗試 citeseerx 上的 STL-QPSR 報告（Askenfelt 1991
   *Measuring the motion of the piano hammer during string contact*），該連結
   301 重導向到 `web.archive.org`，**本環境工具回報無法 fetch `web.archive.org`**，
   未能取得內容——誠實記錄為「查過但工具不可達」，非「沒查」。
2. **arXiv / HAL**：以「Chaigne Askenfelt HAL open archive」「hal.science Boutillon piano
   hammer」搜尋，未找到 HAL 上的 Chaigne & Askenfelt 或 Boutillon 全文連結；
   arXiv 搜到的相關論文（*Numerical Modeling of Collisions in Musical Instruments* 等）
   內容與槌力頻譜滾降無關，未引用。
3. **Google Scholar 連到的作者頁/機構典藏**：
   - Hall & Askenfelt 1988 直接 PDF（`pubs.aip.org/.../1627_1_online.pdf`）：
     **本輪第 4 次嘗試仍 403**，付費牆狀態未變（與 A14 裁決包記錄一致）。
   - *Reconstruction of piano hammer force from string velocity*（JASA 140(5):3504,
     2016）：AIP 直接 PDF 與 ResearchGate 頁面**皆 403**，未取得。
   - Stulov 個人頁（`homes.ioc.ee/stulov/klaver2.pdf` 及該網域首頁）：
     **皆 404**，網站已下線/搬遷，§5 既有的 Stulov 遲滯參數（F₀/p/ε/τ₀）
     維持原引用狀態，本輪未能補上更多佐證來源。
   - **D. Russell 個人頁（賓州州大，作者自存檔）**：找到並成功 fetch 全文——見 9.2。
     **此來源非本卡新發現**：同一篇文獻（同一 URL）已於 A14 裁決包
     `reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md` L1-16～L1-22
     （2026-09-08）引用並逐條摘錄，含同一份 Table I、同樣的 Fig.7 A0/F7 數字、
     同一句 L1-20 弦端反射造成凹谷的引句。本卡在該既有引用的基礎上，補摘
     A14 未逐字擷取、但與 B-1（力譜/震波譜計算式、Fig.3/Fig.6 波形比較）
     直接相關的段落，**不是兩個獨立來源，避免被重複計數**。
4. **Woodhouse《Euphonics》**：查驗 2.2.6「Frequency spectrum of a hammer tap」，
   給出的是**半正弦脈衝本身**（現行被取代對象）的理論頻譜公式
   `F(ω) = (kAΩ/π)·cos(πω/2Ω)/(Ω²−ω²)`，力集中在「below about 2.5 Ω」；
   這是理論模型公式，不是真槌實測滾降數字，故不算命中。
5. **替代文獻**：命中 **Russell & Rossing 1998**（Acustica/acta acustica 84:967-975），
   peer-reviewed、開放（作者自存檔）、提供真槌力脈衝波形與半正弦/正弦平方/歪斜
   versed-sine 脈衝的殘餘震波譜（residual shock spectrum）比對，符合本管道要求。

**9.1a Hall 講義頁引句**（性質：弦振動**輸出**頻譜，非槌**力**頻譜本身，已標註區別）：
> "If we compare a 12 dB/oct curve, we can see that the measured spectra are much steeper,
> especially for pianissimo playing" ——`hall/compare.html`

### 9.2 補摘：Russell & Rossing (1998) 與力譜/震波譜計算式相關的段落

> **非新來源**——本節整理的是 A14 裁決包 L1-16～L1-22（2026-09-08）已引用文獻的**補充摘錄**，
> 只補 A14 沒有逐字擷取、但與 D10 卡主題（B-1 力譜滾降）直接相關的部分（殘餘震波譜計算式、
> Fig.3/Fig.6 脈衝波形與滾降量化比較）。A14 已摘錄過的 Table I、Fig.7、L1-20 等內容不在此重複，
> 需要時見 A14 裁決包本文。

**出處**：D. Russell and T. Rossing, "Testing the Nonlinearity of Piano Hammers Using
Residual Shock Spectra," *Acustica · acta acustica*, Vol. 84 (1998), pp. 967–975.
**URL**（作者自存檔，開放，與 A14 L1-16 同一 URL）：https://www.acs.psu.edu/drussell/publications/pianohammer.pdf
**取得狀態**：✅ 全文 PDF（9 頁）本卡再次完整 fetch（A14 於 09-08 已 fetch 過同一篇）。

**數據與逐字引文**（本卡補摘部分，不重複 A14 已摘錄的 L1-16～L1-22）：

- p.970，Fig.3：硬 A3 槌（4 m/s）實測力脈衝（虛線）與 (a) 半正弦、(b) 正弦平方、
  (c) 歪斜 versed-sine 三種理論脈衝比較。
- p.970：**只有聚氨酯彈性體（線性、非氈）實驗槌，才「非常接近半正弦脈衝，顯示線性
  行為」**：
  > "the impulse obtained from an experimental hammer with a polyurethane elastomer head
  > could be very closely approximated by a half-sine pulse, indicating a linear behavior."

  且真氈槌接觸時間隨速度增加而縮短，聚氨酯槌則否：
  > "for all real piano hammers measured in this study the pulse duration decreased with
  > increasing velocity" 對照聚氨酯槌 "the pulse duration remained essentially constant
  > over the velocity range of 1-5 m/s."

  → 這與 A14 裁決包已引的 Woodhouse *Euphonics* 結論（半正弦=線性槌行為，鋼琴氈槌非
  線性）**方向一致的獨立第二篇文獻佐證**。
- p.971，Fig.6：A3 硬槌 4 m/s 的殘餘震波譜（∝ ω|F(ω)|，式號見下方適用域段落的完整
  說明——原文式（3）／（4）兩個編號都與這個運算有關）與三種理論脈衝的
  震波譜疊圖比較，**可直接引用的量化差異數字**：
  > "the value of fmax predicted by the skewed versed-sine pulse is about 140 Hz higher
  > than the measured value, and the sine-squared pulse prediction is about 230 Hz to
  > high. In both cases the amplitude is about 20% too low."
- p.971，Table I：13 顆已調音（voiced）Steinway model D 琴槌，`fmax = a·v^b` 擬合值，
  涵蓋 A0（琴鍵位置 1）到 F7（位置 81），`b` 值範圍 0.36–0.64、隨音高略升
  （逐格轉錄存 `output/wf0914/D10/fetched_excerpts.md` §8）。
- p.972，Fig.7：
  > "For hammer A0, fmax is 775 Hz at 1 m/s and 1370 Hz at 4 m/s. For hammer F7, fmax is
  > 1300 Hz at 1 m/s and 3038 Hz at 4 m/s."

**適用域與限制（原文自陳）**：

- 這是**槌打在剛性力規頭**（非真弦）上量得的力脈衝/震波譜。作者明白指出真實槌-弦
  交互作用會因弦端反射波使力脈衝出現「valleys」，與剛性面量測不同：
  > "reflections from the near end of the string can cause valleys in the pulse shape
  > ... so that it differs considerably from the smooth sine-squared-like pulse shape
  > obtained when the hammer hits a rigid object." (p.969)
- **震波譜不是力頻譜本身**，是力頻譜乘上角頻率。原文（p.968 §3.1）給出兩個式子：
  一般型（加速度震波譜）標號 **Eq.(3)**：`Ra(ω) = ω|Fa(jω)|`；套用到力脈衝、除以受測
  系統質量 M 的特化式標號 **Eq.(4)**：`Ra(ω) = (ω/M)|F(jω)|`。原文緊接著說明
  > "Equation (3) allows the residual shock spectrum to be obtained for a shock pulse
  > that may be measured, but not expressed mathematically."

  且在描述實際量測作法時（p.969 §4.1）寫：
  > "The residual shock spectrum was obtained by multiplying the power spectrum (Fourier
  > transform of the force pulse) by ω, as per Eq.(3)."

  也就是原文自己在實驗方法段落**用 Eq.(3) 稱呼**這個「乘 ω」的運算（M 視為常數時
  Eq.(3)/(4) 等效，原文 p.968 自陳 "If the mass of the system is constant then a
  measurement of ω|F(ω)| may still be considered to be a measure of the acceleration
  amplitude."）。故本文件標註**原文式（3）／（4）**，不單獨斷言其中一個編號指涉
  Fig.6/Fig.7 的量測結果；兩者形狀相差一個 `+6 dB/oct` 的 `ω` 加權因子。**若要換算回
  力頻譜滾降，需先扣掉這個加權——本文件不做這個換算**，換算出的數字會是未溯源的
  推導常數（違反 R4）。
- 未給出顯式的 **dB/octave 斜率數字**，只給出 fmax（峰值頻率）與少數比較點的 Hz/
  百分比差異。

**與現行半正弦模型的差異點（本文件整理，非原文結論）**：

- 現行 `HammerImpulse.h` 半正弦力脈衝對應的正是本文 Fig.3(a) 的比較基準；本文獨立確認
  半正弦只精確對應**線性（聚氨酯）槌**，不對應真氈槌。
- Table I 的 `fmax(v)` 冪律擬合提供一組**開放、可核對的量化資料**（真槌撞剛性面時震波
  譜峰值頻率隨速度的冪律變化）。**這不是本卡新提案**——A14 裁決包 :687 已建議
  「B-1 施工卡把 f_max 當成驗收指標」，:938 已裁定「B-1 不動：真槌力譜滾降形狀原文
  未取得……拿到前不得填替代曲線」。Table I 本身**不是**弦-槌交互作用下的力頻譜滾降
  本身；套用到 B-1 前需要額外物理轉換（去 ω 加權、從剛性面外推到真弦邊界條件），
  本文件不越權做這個轉換。

### 9.3 仍未取得的部分（誠實記錄）

- **Hall & Askenfelt 1988**（JASA 83(4):1627）原文全文：本輪第 4 次嘗試（含直接 PDF
  連結）**仍 403**，付費牆狀態未變。
- **Chaigne & Askenfelt 1994 Part II**（JASA 95(3):1631）：本輪未找到開放全文
  （AIP abstract-only、Semantic Scholar 僅摘要、ResearchGate 頁面未見開放 PDF）；
  未嘗試登入 ResearchGate 請求全文（依規約「要登入才能拿的來源直接跳過記錄」）。
- ***Reconstruction of piano hammer force from string velocity***（JASA 140(5):3504,
  2016）：AIP 與 ResearchGate 頁面皆 403，未取得。
- Stulov 遲滯模型原論文的補充來源（`homes.ioc.ee`）：網域整頁 404，未能補上。
- **結論**：真槌力譜滾降的**顯式 dB/octave 數字**，本卡窮盡管道後**仍未取得**，
  Hall & Askenfelt 1988 與 Chaigne & Askenfelt 1994 Part II 的付費牆狀態與 A14
  裁決包（2026-09-08）記錄一致、未變。本卡在 A14 已引用的 Russell & Rossing (1998)
  （L1-16～L1-22）中補摘了與力譜/震波譜計算式直接相關、A14 未逐字擷取過的段落（見
  9.2）——**這是對既有來源的補摘，不是新來源**。**B-1 維持 A14 已裁定的等文獻狀態
  不變**（A14 :938）；本卡沒有新增任何改變該裁定的材料，也不建議以 9.2 補摘的資料
  直接推導滾降斜率（會產生未溯源的換算常數，違反 R4）。是否要為取得 Hall &
  Askenfelt 1988 / Chaigne & Askenfelt Part II 花費館際/機構帳號等額外力氣，
  A14 :814 已把這個取捨交給月月決定，本卡沒有新資訊可以改變這個待決狀態。
