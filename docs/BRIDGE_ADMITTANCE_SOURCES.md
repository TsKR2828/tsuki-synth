# 琴橋導納（bridge admittance）溯源與可實作公式

> 建立：2026-08-15
> 起因：`reports/damping_broadband_findings.md` §4 證明阻尼寬頻化缺一個
> 「頻率無關的損耗通道」，並指出補一個常數不夠、需要琴橋導納模型。
> 本文件是 `ROADMAP_PHYSICS.md` Rule 4 要求的溯源交付物：每個要進程式的
> 數字都標明「文獻 / 推導 / 量測 / 抓不到」。
> 體例比照 `docs/MATERIALS_SOURCES.md` 與 `docs/EIGENVALUE_SOURCES.md`。
>
> **本文件不改任何程式碼、不改任何容差。** 它只回答一個問題：
> 那個缺掉的損耗通道，有沒有可溯源、可實作的公式？**有。**

---

## 0. 白話（先讀這一段）

弦被敲了以後為什麼會停下來？有幾條路會把能量帶走：空氣摩擦、材料自己的內耗、
往外輻射成聲音——這三條程式裡都有。**還有第四條，程式裡沒有：能量從弦端經過
琴橋流進共鳴板。**

真實揚琴/鋼琴的低音之所以只響十幾秒而不是兩分鐘，主因就是這第四條。
之前那個固定的阻尼常數一直在偷偷兼差扮演它；把材料內耗改對之後，兼差消失，
低音就沒東西攔得住了（C2 從 39 秒變 129 秒）。

好消息是：**這第四條有現成的閉式公式，不用去實驗室量。** 它需要的東西
程式裡幾乎都有了——弦的張力、弦長、共鳴板的材質與厚度。只要多一個
「共鳴板多厚」的參數，就能算出來。

壞消息是：這條公式算出來的是**平滑的平均值**。真實鋼琴上相鄰半音的衰減
時間可以差 5 倍（共鳴板共振的峰谷造成），平滑公式抓不到那個。要抓那個
得做完整的共鳴板模態模型。所以這是**分兩階段**的事，本文件只解決第一階段。

---

## 1. 缺口的物理定義

現行三項阻尼律（`StringModel.h` / `BeamModel.h` / `PlateModel.h`，
寬頻化後）：

```
1/T60(f) = eta·f/2.2  +  beta_air·f²  +  gamma_radiation·f
             內部摩擦       空氣黏滯        聲輻射
```

三項在 `f → 0` 時全部趨近 0，所以低音端 T60 發散。缺的第四項是弦端
透過支撐（琴橋 / 共鳴板 / 框架）流失的能量。

---

## 2. 三個環節，逐一溯源

### 2.1 共鳴板的特徵導納 `Y∞`（**文獻，閉式**）

無限大薄板在驅動點的機械導納（mobility，速度／力，單位 s/kg = m·s⁻¹·N⁻¹）：

```
Y∞ = 1 / (8 · sqrt(D · ρs))

  D  = E·h³ / (12·(1 − ν²))     板的彎曲剛度 (N·m)
  ρs = ρ·h                      面密度 (kg/m²)
```

**性質（這是關鍵）**：無限板的驅動點導納是**純實數且與頻率無關**。
正因為如此，它正好就是 §1 缺的那個「頻率無關的損耗通道」。

**來源**：
- 這是薄板振動的經典結果（Cremer, Heckl & Ungar, *Structure-Borne Sound*；
  Skudrzyk 的 mean-value theorem 用它當漸近特徵值）。
- Ege & Boutillon 給出代數上完全等價的另一種寫法：
  `Y_C = (1/(4h²))·sqrt(3(1−ν²)/(E·ρ))`。
  **本文件已獨立驗證兩式相等**：
  `8·sqrt(D·ρs) = 8h²·sqrt(Eρ/(12(1−ν²)))`，取倒數並把 `1/sqrt(12) = 2/sqrt(3)`
  代入即得 Ege & Boutillon 的形式。兩者是同一條公式。
- 該文獻明確把此值認定為鋼琴音板的**漸近特徵導納**，並用它合成出與
  Giordano / Wogram / Conklin / Nakamura 的實測相符的導納曲線
  （在 1–1.5 kHz 過渡區之外）。

**文獻實測值（用來核對量級，不直接進程式）**：

| 來源 | 量 | 值 |
|---|---|---|
| Ege & Boutillon（直立鋼琴，實測合成） | 平均阻抗 100–1000 Hz | ≈ 800 kg·s⁻¹ |
| 同上 | 平均導納 100–1000 Hz | ≈ 1.3 × 10⁻³ s/kg（= −57.7 dB re 1 m/s/N） |
| 同上 | 音板質量 / 漸近模態密度 / 平均損耗因子 | M = 9 kg／n∞ = 1/19.5 modes·Hz⁻¹／η ≈ 2% |
| Giordano 1998（直立鋼琴，實測） | 琴橋處低頻阻抗 | 1–2 × 10³ kg·s⁻¹ |
| 同上 | 肋條之間低頻阻抗 | 0.6–0.7 × 10³ kg·s⁻¹ |
| Wogram（引自 Ege & Boutillon） | 平均阻抗 100–1000 Hz | ≈ 10³ kg·s⁻¹ |
| 同上 | 10 kHz 處 | ≈ 160 kg·s⁻¹ |

**用雲杉材質參數代入公式的自我核對**（`E_L = 11.5 GPa`, `ρ = 400 kg/m³`,
`ν = 0.30`）：

| 板厚 h | `Y∞` | dB re 1 m/s/N |
|---|---|---|
| 8 mm | 3.01 × 10⁻³ s/kg | −50.4 |
| 10 mm | 1.93 × 10⁻³ s/kg | −54.3 |

實測的 1.3 × 10⁻³ 落在同量級、比裸板公式低約 2 倍——**方向正確且可解釋**：
真實音板有肋條（ribs），等效彎曲剛度比裸板高，導納因此更低。

### 2.2 弦端損耗率 `α`（**推導**，非抄錄）

弦的特徵阻抗（`euphonics.org` §5.1 明確定義，與經典教科書一致）：

```
Z₀ = sqrt(T · μ)        T = 張力 (N)，μ = 線密度 (kg/m)
```

推導（弱耦合，`|Z₀·Y| ≪ 1`，單一極化，忽略 agrafe 端運動）：

1. 弦端被導納 `Y` 終止時的行波反射係數
   `r = (1 − Z₀Y)/(1 + Z₀Y)`。
2. 一次反射的能量保留比 `|r|² ≈ 1 − 4·Re(Z₀Y) = 1 − 4·Z₀·G`（`G ≡ Re Y`）。
3. 琴橋端每秒反射次數 = 基頻 `f₁ = (1/2L)·sqrt(T/μ)`。
4. 能量衰減率 `1/τ_E = 4·Z₀·G·f₁`；振幅衰減率是一半：`α = 2·Z₀·G·f₁`。
5. 代入 `Z₀·f₁ = sqrt(Tμ)·(1/2L)·sqrt(T/μ) = T/(2L)`：

```
α = (T / L) · G          [振幅衰減率, s⁻¹]
```

**注意 `μ` 與 `f₁` 都消掉了——結果只剩張力、弦長與導納，與頻率無關。**
這正是 §1 需要的性質。

**交叉驗證**：這個結果與弦-音板耦合文獻中引用的 `α_n = (T/L)·G(ω)` 形式
一致（本輪由反射係數獨立推導得到，非抄錄）。定性上也與 Chaigne (ICA 2010)
的敘述相符：「導納的實部主導能量從弦傳到音板與弦的衰減時間，虛部主要影響
弦的失諧」。

### 2.3 轉成 repo 的阻尼律形式（**代數**）

`ModalResonator` 的慣例是 T60（振幅衰減 −60 dB，比例 1/1000）：
`a(t) = a₀·e^(−αt)`，`e^(−α·T60) = 10⁻³` ⇒ `T60 = ln(1000)/α`。

```
1/T60_bridge = (T · G) / (ln(1000) · L)        ln(1000) = 6.907755278982137
```

`6.907755278982137` **不是新常數**——`ModalResonator::excite()` 已經用同一個
字面值（`6.9078f`），`tools/physics_verify.py` 也已登記為 `MODAL_DECAY_LN1000`。

加進現行律：

```
1/T60(f) = eta·f/2.2 + beta_air·f² + gamma_radiation·f + T·G/(ln(1000)·L)
                                                          ^^^^^^^^^^^^^^^^
                                                          新增，頻率無關
```

---

## 3. 量級核對（**文獻實值，2026-08-15 修訂**）

> **修訂說明**：本節初版用的是本文件自行估計的 `L`／`T`。同日取得
> Euphonics §12.2.1 Table 1（逐音鋼琴弦參數，源自 Conklin 與
> Hall & Askenfelt）後改用文獻實值，數字因此變動。逐音資料見
> `docs/HAMMER_CONTACT_SOURCES.md` §2。該表已通過自洽檢查：由表列的
> `T/L`、總質量與弦長回推的 `f₁`，與表列標稱頻率在 C1–C8 全部吻合到
> 0.15% 以內。

`T/L` 直接是該表的一列（"Tension over length"，kN/m，為**全部弦的總和**，
故除以弦數得逐弦值）。`G = 1.3 × 10⁻³ s/kg` 為 §2.1 的直立鋼琴實測平均。
`T60_combined` = 現行寬頻化模型（`reports/damping_broadband_findings.md`
§3.1 的實測值）與本項並聯：`1/T60 = 1/T60_現行 + 1/T60_bridge`。

| 音 | 逐弦 T/L (N/m) | `T60_bridge` 單獨 | `T60_combined` | Wogram 實測 | 現行模型（無本項） |
|---|---|---|---|---|---|
| C2 | 1250.0 | 4.25 s | **4.12 s** | — | **128.75 s** |
| C3 | 1050.0 | 5.06 s | **4.67 s** | ≈ 11.4 s | 60.39 s |
| C4 | 1073.3 | 4.95 s | **4.18 s** | ≈ 5.1 s | 26.86 s |
| C5 | 1920.0 | 2.77 s | 2.21 s | — | 11.00 s |
| C6 | 3510.0 | 1.51 s | 1.10 s | — | 4.04 s |
| C7 | 6713.3 | 0.79 s | 0.49 s | — | 1.32 s |
| C8 | 12650.0 | 0.42 s | 0.20 s | — | 0.39 s |

**怎麼讀這張表**：

1. **低音發散被完全治好。** C2 由 128.75 s 收到 4.12 s，C3 由 60.39 s 收到
   4.67 s。這正是本項存在的理由。
2. **C4 對得很準。** 單獨項 4.95 s vs Wogram 實測 5.1 s（差 3%）。
   反解「要多大的 G 才剛好等於實測」得 `G = 1.262 × 10⁻³ s/kg`，
   與文獻平均 `1.3 × 10⁻³` 差 3%——這是本文件最強的一個對照點。
3. **C3 仍偏短 2.4 倍**（4.67 vs 11.4 s）。原因可指認：逐弦 `T/L` 在
   C2–C4 幾乎是常數（1250／1050／1073 N/m，這是鋼琴 scaling 的設計結果），
   所以用**單一平均 `G`** 必然給出幾乎相同的 T60；而實測顯示低音的 T60
   明顯較長 ⇒ **真實的 `G` 在低音區比平均值小**（反解 C3 需要
   `5.77 × 10⁻⁴ s/kg`，約平均值的一半）。這與文獻一致：低音琴橋座落在
   音板較厚／肋條較密的區域，導納本來就較低。
4. **高音端本項不是主角。** C7/C8 現行模型已經給出 1.32／0.39 s，
   內部摩擦在那裡本來就主導；本項讓它再短一些。

**這仍是量級核對，不是驗證**：
1. `G` 用的是直立鋼琴音板的實測平均，且已知它沿音域變化（見第 3 點）；
   本文件不擬合任何逐音 `G(note)`——那會變成可調旋鈕，違反 Rule 4。
2. Wogram 只有 C3／C4／G4 三個資料點，且是 T20×3 的換算值。
3. TsukiSynth 引擎自己用 `T = μ(2Lf₁)²` 定張力，與上表的真實鋼琴 scaling
   不同；真正的檢驗必須在引擎內實作後跑 `--t60` 與 corpus，數字以那邊為準。

---

## 4. 這個模型**抓不到**什麼（實作前必須知道）

1. **相鄰半音的巨大落差抓不到。** Wogram 量到 F#4 的 T20 = 3.5 s 但
   G4 只有 0.7 s（5:1）。那是音板共振峰谷造成的，任何**平滑**的導納值
   （包括本文的 `Y∞`）在原理上都不可能重現。要重現得做完整的共鳴板模態
   模型——也就是 `TODO.md` 的 coupled-body 項本身。**本文件是那一項的
   第一階段，不是它的替代品。**
2. **高頻區的模型換檔抓不到。** Ege & Boutillon 指出約 `f_lim ≈ 1.1 kHz`
   以上，音板不再表現得像均質板，而是變成被肋條界定的波導集合
   （`f_lim` 由肋條間距 p ≈ 12.8–13 cm 決定）；Giordano 也在約 1.1 kHz
   看到同一個轉折。平滑常數導納在那之上會系統性偏離。
3. **`Y` 的虛部被丟掉了。** §2.2 只用實部 `G`。虛部會造成弦的頻率牽引
   （detuning），本模型不含，不得宣稱涵蓋。
4. **只有一個極化方向。** 真實琴橋要 2×2 導納矩陣（Woodhouse）；本模型
   是單方向的純量近似。
5. **揚琴/cimbalom 沒有對應實測。** 找不到揚琴琴橋導納的公開量測。
   若用 §2.1 公式從揚琴自己的面板材質與厚度算，那是**方程層**的主張
   （比照 `ROADMAP_PHYSICS.md` §0 對 `frequency_mode: geometry` 的定位），
   **不是 specimen-level 主張**。

---

## 5. 實作需要新增的參數（供裁決，本輪未實作）

| 參數 | 型態 | 需要理由 | 有沒有現成來源 |
|---|---|---|---|
| 共鳴板材質 | 既有 material key | 算 `D`、`ρs` | ✅ `materials.json` 已有木料 |
| 共鳴板厚度 `h` | 新增，公尺 | 算 `D`、`ρs` | ⚠️ 需登記典型值（鋼琴音板 8–10 mm 有文獻） |
| 弦長 `L`、張力 `T` | 既有 | 算 `T/L` | ✅ `StringModel` 已有（`T = μ(2Lf₁)²`） |
| 耦合折減係數 | **不新增** | — | ❌ 刻意不加。加了就變成可調的擬合旋鈕，違反 Rule 4 |

**2026-08-27 月月確認現值**：`h = 9mm`／材質 `wood_spruce` 經月月裁決 (i) 確認維持（裁決包 `reports/decision_packets/A11_soundboard_sensitivity.md`）；「可注入」子問題一併就地關閉，引擎/renderer 層維持寫死。

**Beam / Plate 引擎**：同一條物理也適用（舌鼓的舌片根部、鑼的懸掛點），
但 §2.2 的推導是針對**行波弦**做的，梁與板要各自重推，不得直接套用。
本輪不推。

---

## 5b. 正交異向板驅動點導納（2026-08-28 Codex 溯源命中）

> **2026-08-28 Opus 稽核：一過一未過。** 原文見
> `docs/research_inbox/codex_20260828_findings.md` §3。
>
> | 條目 | 狀態 |
> |---|---|
> | 公式一（輪胎論文 Eq.(28)，`Y_dp`） | **公式待原文複核**——原文取不到（見下方「取得嘗試紀錄」）。**這是本節唯一真正給出 `Y_dp` 的來源，所以整個 §5b 的核心公式目前仍未溯源。** |
> | 公式二（Park/Hong/Kil Eq.(3)，`H_c`） | **Opus 已核（2026-08-28）**，公式、頁碼、Cremer 引述、參考文獻頁全部相符 |
>
> 因此本節整體**仍不得寫入程式碼、不得用於任何 GATE 判定**，
> 也不構成 §5「實作需要新增的參數」表格的核准。

§2.1 目前的 `Y∞ = 1/(8√(D·ρs))` 是**各向同性**薄板公式。`docs/workcards/B5.md`
§11 (a) 記載的既有阻擋是：`orthotropic` 資料塊已入庫（9 個獨立正交異向常數），
但**沒有任何已溯源的「正交異向板無限板點導納」公式**可以消費這批資料
——`D` 的計算因此在 B5 卡裡刻意不做正交異向化。Codex 補搜回報找到兩篇
可能解開這個阻擋的文獻：

- 公式一（**公式待原文複核，2026-08-28 Opus 取不到全文**）：
  Muggleton JM, Mace BR, Brennan MJ, *Vibrational response prediction of a
  pneumatic tyre using an orthotropic two-plate wave model*,
  **Journal of Sound and Vibration 264(4):929–950, 2003**，
  DOI 10.1016/S0022-460X(02)01190-2，Codex 標注 p.938 Eq.(28)：

  ```
  Y_dp = 1 / (8·(ρ²h²·Dxx·Dyy)^(1/4))
       = 1 / (8·√(ρh)·(Dxx·Dyy)^(1/4))
       = 1 / (8·√(m·D_eff))     其中 m = ρh，D_eff = √(Dxx·Dyy)
  ```

  即形式上與各向同性版 `Y∞ = 1/(8√(D·ρs))` 完全類比，只是把單一 `D`
  換成 `Dxx`、`Dyy` 兩個正交彎曲剛度的幾何平均 `D_eff`。
  Codex 註記的限制：**Kirchhoff 正交異向薄板、點驅動、無限板高頻漸近**；
  結果為純實數、不隨頻率變化；**非有限板逐模態曲線**——跟本文件 §2.1
  各向同性版的性質與限制完全對應（同屬「平均值」而非峰谷結構）。

  **【2026-08-28 Opus 取得嘗試紀錄・未通過】**
  - ScienceDirect 頁面（S0022460X02011902）為付費牆，未取得全文。
  - Hindawi/Wiley 那種開放管道不適用；OpenAlex 查詢 DOI 回報
    `oa_status: "closed"`、`any_repository_has_fulltext: false`，
    唯一的機構庫位置 `eprints.soton.ac.uk/10105/` 亦標記為非 OA，
    實際存取回 HTTP 403。
  - ISVR 出版清單頁（`resource.isvr.soton.ac.uk/staff/pubs/pubs218.htm`）
    有著錄此文（第 82 筆）但**未附 PDF 連結**。
  - **已從公開後設資料確認的部分**：作者三人、期刊 JSV、
    **卷期頁 264(4):929–950 (2003)** ——因此 Codex 標注的 p.938
    **落在頁碼範圍內、屬合理**，但**該頁確實有沒有 Eq.(28)、
    係數是不是 8、指數是不是 1/4，全部未經本 repo 親眼核對**。
  - **僅有的旁證（不能當成核過）**：上述三行寫法在代數上互相恆等
    （`(ρ²h²DxxDyy)^(1/4) = √(ρh)·(DxxDyy)^(1/4) = √(m·√(DxxDyy))`），
    且令 `Dxx = Dyy = D` 時退化為教科書的各向同性結果
    `Y∞ = 1/(8√(Dm))`——**自洽性通過**。但自洽不等於出處正確：
    一個抄錯係數的式子若同時抄錯兩處也可能自洽，且此式極可能是
    抄自 Cremer/Heckl/Ungar 的標準結果而非該輪胎論文的原創。
  - **裁決：維持「公式待原文複核」**，不得升級為「已驗證公式」。
    後續途徑：館際互借取得 JSV 264(4) p.938，或改用
    Cremer/Heckl/Ungar *Structure-Borne Sound*（本文件 §6 引用 #8，
    同樣未取得全文）作為一手出處——後者其實才是這條式子的正統來源。

- 公式二（**Opus 已核 2026-08-28**）：Park D-H, Hong S-Y, Kil H-G,
  *Vibrational energy flow models of finite orthotropic plates*,
  **Shock and Vibration 10(2):97–113, 2003**（IOS Press；作者單位
  首爾大學造船海洋工程系／水原大學機械工程系），DOI 10.1155/2003/428705。
  Gold OA (CC BY)，Opus 取得存檔版 PDF（18 頁）逐字核對，**全部相符**：
  - **p.98 Eq.(3)**：`H_c = √(D_xc · D_yc)` ✓ 公式與頁碼皆相符。
    原文語境：`H_c` 是運動方程式 Eq.(1) 裡的**複數等效扭轉剛度**
    （complex effective torsional stiffness），在「板厚固定、橫向位移
    很小、變形為彈性」的前提下，可**假設**為兩向彎曲剛度的幾何平均。
  - **同頁（p.98）確有該引述**，原文逐字為：
    "Despite of its preconditions, Cremer and Heckl [4] showed that
    Eq. (3) is a very good approximation for many practical orthotropic
    plates. It can be also seen in their work that the driving point
    impedance of an orthotropic plate is very nearly equal to that of
    an homogeneous plate whose bending stiffness is equal to the
    geometric mean of the bending stiffnesses in the two coordinate
    direction." ✓
    （小差異：正文寫的是「Cremer and Heckl」兩人，
    參考文獻 [4] 才是三人 Cremer/Heckl/Ungar。）
  - **參考文獻 [4] 位於印刷頁 p.110** ✓：
    "L. Cremer, M. Heckl and E.E. Ungar, Structure-Borne Sound,
    Springer-Verlag, Berlin, 1973."——與本文件 §6 引用 #8 是同一本。
  - **⚠️ 這篇能證明什麼、不能證明什麼（重要）**：它證明的是
    **「幾何平均代換」這個做法有出處**，以及 Cremer/Heckl 對驅動點阻抗
    講過「非常接近」。它**沒有給出任何 `Y_dp` 的閉式公式**——
    Eq.(3) 是扭轉剛度不是導納，且該文全篇處理的是**有限板的能量流
    (EFA)**，不是無限板點導納。**所以公式一不能靠公式二背書。**

**對本文件與 B5 的意義（公式一未過稽核，以下全部維持假設語氣）**：這將解開
`docs/workcards/B5.md` §11 (a) 的小階段阻擋——B5 已入庫的 orthotropic
資料自此有了一條可溯源的消費公式**候選**：把 §2.1 的 `D = E·h³/(12(1−ν²))`
換成正交異向的 `Dxx`、`Dyy`，再取幾何平均代入形式相同的 `Y∞` 公式。
**但這僅止於登記溯源，不代表可以動工**：

- 實作（把 `Dxx`/`Dyy` 接進 `BeamModel.h`/`PlateModel.h` 或琴橋導納模型）
  是**模型結構改動**，屬於未來的新工作卡，不在本文件範圍，也不在
  B5 範圍（B5 §11 已明確排除 (a)(b) 兩個小階段）。
- **關鍵：真正給出 `Y_dp` 的那一篇（公式一）沒核過。** 2026-08-28 Opus
  核過的是公式二，而公式二只支持「幾何平均代換合理」，**不含導納公式**。
  所以 B5 §11 (a) 的阻擋**尚未解除**——現況是「有一條很可能正確、
  且自洽、但出處未經親眼核對的候選公式」，不是「已溯源」。
  在取得 JSV 264(4) p.938 或 Cremer/Heckl/Ungar 原書之前，
  **不得引用為「已驗證公式」，不得寫進程式碼**。
- 即使公式本身成立，正交異向版本繼承了各向同性版本 §4 列出的全部
  限制（抓不到峰谷結構、高頻換檔、虛部、單一極化方向），且新增一條
  自身限制：無限板高頻漸近對**低頻**（舌鼓/鑼的基頻常在低頻）的適用性
  未經確認。公式二本身也帶了一條前置條件（p.98 原文）：幾何平均代換
  假設**板厚固定、橫向位移很小、變形為彈性**——舌鼓的舌片是變厚度/
  懸臂結構，鑼被大力敲擊時是大振幅非線性，**兩個前置條件在本專案的
  目標樂器上都不見得成立**。

## 6. 引用清單

| # | 出處 | 取得狀態 | 本文件用到什麼 |
|---|---|---|---|
| 1 | Ege & Boutillon, *Vibroacoustics of the piano soundboard: reduced models, mobility synthesis, and acoustical radiation regime*, J. Sound Vib. 332 (2013) 4261–4279（arXiv:1305.3057） | ✅ 開放全文 | 特徵導納形式、`f_lim ≈ 1.1 kHz`、`f_c ≈ 1.8 kHz`、`η ≈ 2%±1%`、模態密度 0.06 modes/Hz |
| 2 | Ege & Boutillon, *Synthetic description of the piano soundboard mechanical mobility*（ISMA 2010；arXiv:1210.5688） | ✅ 開放全文 | `Y_C = (1/4h²)√(3(1−ν²)/(Eρ))`、M = 9 kg、n∞ = 1/19.5、平均阻抗 800 kg/s、平均導納 1.3e−3 s/kg、轉引 Giordano/Wogram 數值 |
| 3 | Giordano, *Mechanical impedance of a piano soundboard*, JASA 103(4) (1998) 2128–2133 | ⚠️ 摘要可得，全文付費 | 琴橋 1–2×10³ kg/s、肋間 0.6–0.7×10³ kg/s、1.1 kHz 均質板→波導轉折（經 #2 與摘要轉引） |
| 4 | Chaigne, *Linear string-soundboard coupling in pianos*, ICA 2010, Sydney | ✅ 開放全文 | 導納定義 `Y = V(x_B,ω)/F(L,ω)`、實部主導衰減／虛部主導失諧的定性陳述 |
| 5 | Woodhouse, *On the synthesis of guitar plucks*, Acta Acustica 90 (2004) 928–944 | ✅ 開放全文 | 導納的模態展開式、2×2 導納矩陣需求（§4 侷限 4 的依據） |
| 6 | Woodhouse, *Euphonics* §5.1 線上教材 | ✅ 開放 | `Z₀ = √(Tμ)`；耦合強度 ∝ `Y·Z₀` |
| 7 | Wogram, *The strings and the soundboard*（KTH 講座系列） | 已引於 `damping_broadband_findings.md` §4.1 | C3/C4/G4/F#4 的 T20 實測，§3 對照與 §4 侷限 1 的依據 |
| 8 | Cremer, Heckl & Ungar, *Structure-Borne Sound*, Springer-Verlag, Berlin, 1973 / Skudrzyk mean-value theorem | 📖 教科書（未線上取得全文） | `Y∞ = 1/(8√(D·ρs))` 的經典出處；亦是 §5b 正交異向版的正統一手來源（經 #10 p.98 轉引） |
| 9 | Muggleton, Mace & Brennan, *Vibrational response prediction of a pneumatic tyre using an orthotropic two-plate wave model*, J. Sound Vib. **264(4) (2003) 929–950**, DOI 10.1016/S0022-460X(02)01190-2 | ❌ 付費牆，OpenAlex 標 `closed`、無任何機構庫全文（2026-08-28 Opus 實測） | §5b 公式一 `Y_dp`（Codex 標 p.938 Eq.(28)）——**公式待原文複核，未核過** |
| 10 | Park, Hong & Kil, *Vibrational energy flow models of finite orthotropic plates*, Shock and Vibration **10(2) (2003) 97–113**, DOI 10.1155/2003/428705 | ✅ Gold OA (CC BY)，2026-08-28 Opus 已取得全文並逐字核對 | §5b 公式二：p.98 Eq.(3) `H_c = √(D_xc·D_yc)`；同頁 Cremer & Heckl 驅動點阻抗引述；p.110 參考文獻 [4] |

**抓不到的**：Giordano 1998 的原始逐頻率導納曲線（付費牆）。本文件因此
**沒有**數位化任何論文圖表——所有進到 §2 的東西都是閉式公式或文獻正文
明列的數字，不含讀圖誤差。

---

## 7. 狀態

- [x] 找到可實作、可溯源的閉式公式鏈（§2.1 → §2.2 → §2.3）
- [x] 量級可行性估算通過（§3）
- [x] 侷限誠實列出（§4）
- [ ] **實作**——未動任何程式碼。實作會改變所有既有 score 的衰減 ⇒
      觸發 Rule 10（需前後對照報告）+ Rule 6（三 target 重建 + `--full`）
      + corpus 73 檔重驗。**待月月裁決是否開工。**
- [ ] 共鳴板厚度 `h` 的預設值與其文獻依據（實作時一併登記）
- [ ] 第二階段（音板模態 / 峰谷結構）——本文件不涵蓋，維持在
      `TODO.md` 的 coupled-body 條目
