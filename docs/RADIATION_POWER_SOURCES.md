# 輻射功率鏈公式溯源（B6 Phase 0）

> 建立：2026-08-28
> 對應 `docs/workcards/B6.md` §4.2/§6 Phase 0 交付物。
> 體例比照 `docs/BRIDGE_ADMITTANCE_SOURCES.md`。
>
> **本文件不改任何程式碼、不改任何容差。** 純文獻/推導溯源。

---

## 0. 白話

B6.md 自己已經誠實承認：`EXTERNAL_ANCHOR_SOURCES.md`／`BRIDGE_ADMITTANCE_SOURCES.md`
給的 `fc`／`fga`／`η` 只是輻射「骨架」的三個數字，缺一條把「音板振動能量」
接成「輻射瓦特數」的公式。本文件做兩件事：

1. **查 `fc` 公式裡 `H` 到底是什麼**——結果：**`H` 根本不是一個獨立變數**。
   原始論文寫的是 `D̄ₓᴴ`（D 上加橫槓、下標 x、**上標 H**），`H` 是「homogenised
   （肋條均質化）」的縮寫上標，不是乘進公式的第二個物理量。B6.md §4.1 把它
   讀成「`Dx · H` 兩個東西相乘」是**誤讀**，需要更正。
2. **查兩篇 Ege & Boutillon 論文有沒有給輻射功率鏈公式**——逐段查證後結果是
   **沒有**。兩篇論文都只做到「輻射制度骨架」（`fc`/`fga`/頻散曲線比較），
   沒有推導或引用 `W_rad = σρ₀c₀S⟨v²⟩` 或 `η_rad = ρ₀c₀σ/(ωρs)` 這兩條式子。
   本文件改用「這兩條式子本身是不是標準定義的代數結果」這個角度去查證，
   結果是：**它們可以從兩個更基礎的標準定義（輻射效率的定義、SEA 損耗因子
   的定義）直接代數推出，不是憑空捏造，但也不是能指出頁碼的逐字引用。**
   量級自洽檢查（§3）通過。

---

## 1. 缺口定義

B6.md §4.2 需要溯源或推導出：

```
輻射功率：      W_rad(f) = σ(f) · ρ₀c₀ · S · ⟨v²⟩(f)
輻射損耗因子：  η_rad(f) = ρ₀c₀ · σ(f) / (ω · ρs)
```

以及 §4.1 `fc` 公式裡 `H` 的確切定義。

---

## 2. 逐步溯源

### 2.1 `H` 的確切定義（查到，§4.1 需要更正）

**查證方法**：直接讀 `arXiv:1305.3057`（Ege & Boutillon, *J. Sound Vib.* 332
(2013)）§5.1「Radiation regimes」的原文與其定義段落 §2.1。透過 ar5iv
（arXiv 的 HTML 全文轉譯）逐段取得原文，非摘要轉述。

**原文（§5.1，緊接 Fig. 8 之前，公式編號 (29)）**：

> "…with `fc` defined as the lowest frequency corresponding to coincidence
> in this orthotropic plate:
> `fc = ca² / (2π · (D̄ₓᴴ)^(1/2))`"

**`D̄ₓᴴ` 的定義（§2.1，先於 §5.1 給出）**：

> "the plates that compose the piano soundboard are characterised by
> their surface densities `μ = ρh = M/A`… their rigidities
> `D = Eh³/(12(1−ν²))`… **or dynamical rigidities `D̄ = D/μ`**."

即：`D̄`（上標橫槓，讀作 "D-bar"）是一個**單一符號**，定義為「彎曲剛度除以
面密度」（`D̄ = D/μ`，`μ` 即 `ρs`）。下標 `x` 指方向（正交異向板的 x 方向），
**上標 `H` 是 "homogenised" 的縮寫**，標示這是「肋條均質化後」的等效值
（§2.1 描述的均質化程序），**不是第二個要相乘的物理量**。論文原文緊鄰段落
也提到「dynamical rigidities are larger in the xx-directions: ≈150（切角區，
usually ribless）和 100 m⁴s⁻²（均質化中央區）」——單位是 `m⁴·s⁻²`，這正是
`D/μ` 的量綱（`D` 單位 N·m，`μ` 單位 kg/m²，`D/μ` = `m⁴/s²`），**不是
`D·H` 這種乘積該有的量綱**，量綱本身就證明 `H` 不可能是獨立相乘的變數。

**換算成 repo 慣用符號**：`D̄ = Dx/ρs`，所以

```
fc = ca² / (2π · √(Dx/ρs))  =  (ca²/2π) · √(ρs/Dx)
```

這正是結構聲學教科書的**標準重合頻率公式** `fc = c₀²/(2π)·√(m''/B)`
（`m''`=面密度，`B`=彎曲剛度）的形式——與 Cremer/Heckl/Ungar 等教科書一致，
不是 Ege & Boutillon 自創的變體。**B6.md §4.1 寫的 `fc = ca²/(2π·√(Dx·H))`
需要更正為 `fc = ca²/(2π·√(Dx/ρs))`（等價於 `(ca²/2π)·√(ρs/Dx)`）**——
原式把除法誤植成乘法，且 `H` 應直接刪除、換成已知的 `ρs`（B5 落地後即為
`ρs`／`H` 這個符號在 B6.md 裡本來就懷疑「可能是 ρs」，本次查證證實了這個
懷疑，且進一步發現連「乘除關係」本身都要更正）。

**查證管道記錄**：ar5iv HTML 全文（`ar5iv.labs.arxiv.org/html/1305.3057`），
兩次獨立 fetch 分別鎖定 §5.1 與公式 (29) 前後段落、以及 §2.1 的 `D̄` 定義段，
確認一致。未使用摘要或第二手轉述。

### 2.2 輻射功率鏈公式（查無逐字出處，改走推導路線）

**查證範圍**：`arXiv:1305.3057` 全文（含 §5「Some features of the acoustical
radiation」全部子節）與 `arXiv:1210.5688`（Ege & Boutillon, ISMA 2010）全文，
逐段檢索關鍵詞「radiation efficiency」「radiated power」「mean square
velocity」「loss factor」「η」在輻射脈絡下的用法。

**結果：兩篇論文都沒有**：
- `1305.3057` §5 只做頻散曲線比較（結構波數 vs 聲學波數，公式 (33)/(34)），
  判斷「哪個頻率範圍輻射有效（supersonic）」，**沒有量化的 `σ(f)`／`W_rad`
  公式**，只有「這個範圍輻射效率高/低」的定性陳述。
- `1210.5688` 全文只處理**機械導納**（`G_C`、`Y_C` 等），`η`
  只以「量到的音板總損耗因子」（`η≈2%`）與「模態重疊指標
  `μ(f)=n(f)·η·f`」兩種脈絡出現，**沒有把 `η` 拆成 `η_i`/`η_rad`，也沒有
  給輻射功率或輻射損耗因子的公式**。文中僅一句提及「未來可能應用於
  treble range 的聲輻射」，屬於展望，非本文推導內容。

**結論**：`W_rad = σρ₀c₀S⟨v²⟩` 與 `η_rad = ρ₀c₀σ/(ωρs)` **不在這兩篇論文裡**，
B6.md §4.2「這兩篇論文的主題正是輻射制度，找到機率不低」的預期**沒有成立**，
必須誠實記錄查無。

**改走的路線：這兩條式子是不是標準定義的直接代數結果？**

查了公開的結構聲學二手資料（`WebSearch`，非教科書全文——Cremer/Heckl/Ungar
原文本次仍未取得，ScienceDirect Topics「Damping Loss Factor」頁面回傳
403，未能讀取）。多個獨立搜尋結果一致把 `σ` 的定義寫成：

```
σ(f) ≡ W_rad(f) / (ρ₀c₀ · S · ⟨v²⟩(f))
```

即：**這條式子不是一個需要獨立驗證的「經驗公式」，它就是輻射效率 `σ` 的
定義本身**——査到的多個工程／聲學資料（noise control engineering 領域的
慣例說法）用詞幾乎一致，這是這個領域公認的定義，不是本文件自行認定。
把它反過來寫成 `W_rad = σρ₀c₀S⟨v²⟩` 只是移項，不是新增假設。

`η_rad = ρ₀c₀σ/(ωρs)` 則可由兩個標準定義相乘/代入得到（**本文件的推導，
非直接查到的逐字引用**）：

1. **SEA／結構聲學慣用的損耗因子定義**：`η ≡ P_diss / (ω·E)`（單位時間耗散
   功率除以角頻率與儲存的振動能量）——這是統計能量分析（SEA）文獻裡對
   任何一種損耗通道（結構內耗、輻射、邊界耦合……）通用的定義方式，
   `BRIDGE_ADMITTANCE_SOURCES.md` §2.3 用 `T60=ln(1000)/α` 換算損耗率的做法
   也是同一套框架下的等價操作。
2. **平板振動的儲能慣例**：`E = M·⟨v²⟩ = ρs·S·⟨v²⟩`（面密度 × 面積 × 空間
   均方速度，質量乘均方速度，SEA 對「一個振動子系統」總機械能的標準寫法）。

代入 `η_rad = W_rad/(ω·E)`：

```
η_rad = [σ·ρ₀c₀·S·⟨v²⟩] / [ω · ρs·S·⟨v²⟩]
       = σ·ρ₀c₀ / (ω·ρs)
```

`S` 與 `⟨v²⟩` 完全消掉，代數上就是 B6.md §4.2 寫的那條式子。**這個推導
是本文件做的，不是從某篇文獻逐字抄來的**——如果 Cremer/Heckl/Ungar 或
Fahy & Gardonio 原文有這條式子（大概率有，這是結構聲學的標準結果），
本文件仍未親眼看到那一頁，必須誠實標註「推導自標準定義，非逐字引用」。

**時間箱記錄**：兩篇 arXiv 論文各 2 次針對性 fetch（H 定義 1 次 + 全文/§5
輻射公式檢索 1 次，`1210.5688` 同樣 2 次）+ 3 次 WebSearch（開放講義/公開
PDF 搜尋）+ 1 次 ScienceDirect Topics fetch（403 失敗）。已達 B6.md §6 步驟
5 建議的「一到兩次專注嘗試」上限，不再繼續無限期搜尋教科書全文。

---

## 3. 量級核對（自洽性檢查，非外部驗證）

用 §2.2 推導出的 `η_rad = σρ₀c₀/(ωρs)`，代入 `EXTERNAL_ANCHOR_SOURCES.md`
§3 的骨架數字（`fc≈1.8 kHz`、`fga≈1.3 kHz`、`η_total≈2%±1%`）與雲杉音板
的典型面密度（`BRIDGE_ADMITTANCE_SOURCES.md` §5：`h=9mm`、`ρ_spruce=400
kg/m³` ⇒ `ρs = ρh = 3.6 kg/m²`），檢查算出來的 `η_rad(f)` 是否落在
「不超過 `η_total≈0.02`」這個物理上必要的範圍內（因為 `η_total = η_i +
η_rad`，`η_rad` 不能大於 `η_total`，否則 `η_i` 會變負數，代表哪裡出錯）：

`ρ₀=1.2 kg/m³`、`c₀=340 m/s`（沿用 `ca`），`σ(f)` 用 §4.4 近似式。

| f (Hz) | σ(f)（§4.4 近似） | ω=2πf | η_rad(f) = ρ₀c₀σ/(ωρs) | vs η_total≈0.02 |
|---|---|---|---|---|
| 500 | (500/1800)² ≈ 0.0772 | 3141.6 | 0.00279 | 遠小於，合理（低頻輻射弱） |
| 1000 | (1000/1800)² ≈ 0.3086 | 6283.2 | 0.00558 | 明顯小於，合理 |
| 1300 (=fga) | (1300/1800)² ≈ 0.5216 | 8168.1 | 0.00615 | 小於，仍合理 |
| 1800 (=fc) | 1.0（σ 上限） | 11309.7 | 0.01002 | 約為 η_total 的一半，合理 |

**通過自洽檢查**：算出的 `η_rad(f)` 在整個模型有效範圍內（`f<fga`）都
**小於** `η_total≈0.02`，且隨頻率增加而增加（符合輻射佔比隨頻率上升的
物理直覺），在 `f=fc` 處達到約一半——量級站得住，沒有出現 `η_i` 必須變
負數的矛盾。這是**自洽性檢查，不是外部量測驗證**：用的 `ρs` 是典型值
非實測、`σ(f)` 是 §4.4 標註為近似的替代式，兩者疊加的誤差沒有單獨量化。

**額外發現（對 Phase 1 實作有直接影響）**：`fga≈1.3 kHz` **小於**
`fc≈1.8 kHz`（兩者出自同一組骨架數字）。因為 B6.md §4.1 已定義「`f≥fga`
時模型本身失效、不輸出預測」，這代表**在模型宣稱有效的整個頻率範圍內
（`f<fga<fc`），永遠不會進入 `σ(f)=1`（`f≥fc`）那個分支**——`radiationEfficiency()`
的 `f>=fc` 分支在目前這組骨架數字下對任何合格 partial 都不會被觸發，
只有 `f<fc` 的次臨界二次方分支會被實際用到。這不影響函式本身要不要實作
那個分支（`f=fga` 到 `f=fc` 之間萬一某些其他材質/几何組合改變了 `fc`／
`fga` 的相對大小，分支還是要在），但寫測試（§7 `testRadiationEfficiencyShape`）
時要注意：用 B6.md 骨架數字建構的手算案例，`fc<f<fga` 這個「恆等於 1」
的中間态在目前的雲杉／琴橋參數下**實際不可達**，反而 `f=fga` 本身可能
已經 `>fc`，測試時該用真正滿足 `fc<fga` 的參數組合（人造測試值即可，
不必是真實材質）才能覆蓋到那個分支。

---

## 4. 這個模型抓不到什麼

1. **`W_rad`／`η_rad` 兩條式子沒有本專案親眼驗證過的逐字出處頁碼**——
   §2.2 是本文件的代數推導，依賴兩個「標準到幾乎所有結構聲學/SEA 文獻
   都這樣用」的定義（`σ` 的定義、SEA 損耗因子定義 `η=P/(ωE)`），但
   Cremer/Heckl/Ungar 或 Fahy & Gardonio 的教科書原文本次仍未取得。
   若未來取得這兩本書其中之一，應該用書上的原始推導替換本文件 §2.2，
   而不是繼續依賴本文件的代數重建。
2. **§4.4 的 `σ(f)=(f/fc)²`（次臨界）近似式不是 Ege & Boutillon 論文給的
   曲線**，是「緊緻聲源輻射電阻 ∝ (ka)² ∝ f²」這個聲學通識的類比套用。
   monopole 的 `(ka)²` 律本身是教科書標準結果（任一聲學教科書小聲源輻射
   章節都有，例如 Kinsler & Frey、Fahy），但**平板次臨界輻射效率的真實
   頻率相依性比單純 `f²` 複雜**（Maidanik 1962 的邊緣輻射理論指出真實
   曲線在遠低於 `fc` 處由板的邊界/角落輻射主導，頻率相依性與純 `f²`
   monopole 類比不完全相同，且曲線在接近 `fc` 前常有一個峰值再趨於 1，
   不是單調的 `(f/fc)²` 平滑上升）。§3 的自洽檢查只證明**量級**合理，
   不能證明 §4.4 這個平滑二次方形狀本身精確。
3. **本文件未取得 Cremer/Heckl/Ungar《Structure-Borne Sound》或
   Fahy & Gardonio《Sound and Structural Vibration》原文**——两本都是
   付費教科書，本輪仍是「查無開放全文」，與
   `BRIDGE_ADMITTANCE_SOURCES.md` §6 #8 的既有紀錄一致，沒有新進展。
4. **§4.2 的能量守恆捷徑（`fraction_radiated=η_rad/(η_i+η_rad)`）本身是
   標準 SEA 的功率分配假設**（多個損耗通道按各自損耗因子占比分配耗散
   能量），**但把音板當成單一集總 SEA 子系統會丟失
   `BRIDGE_ADMITTANCE_SOURCES.md` §4 第 1 點已經指出的「相鄰半音 T60
   相差 5 倍」的峰谷結構**——這個捷徑给出的是頻率平滑的平均輻射功率，
   不是逐音準確值，跟 B1 的 `Y∞` 集總近似犯的是同一種、已知且被接受的
   簡化。
5. **`η_i` 的拆分沒有查到獨立來源**——見 §5 的建議，本文件認為「借用
   材質 `eta` 欄位」不是最乾淨的做法，但也沒有查到能直接給
   `η_i(f)`／`η_rad(f)` 拆分比例的文獻，最終建議見 §5。

---

## 5. 對 Phase 1 的具體建議（新參數／判斷）

**`fc` 公式更正**（見 §2.1，非新參數，是既有公式的更正）：

```
fc = ca² / (2π · √(Dx / ρs))     // 不是 √(Dx · H)
```

`ρs`（面密度）B5 落地後應該已經是現成量，不需要新查一個「H」。

**σ(f) 形狀**：採用 §4.4 的近似式，維持該處程式碼註解已經寫的「工程近似、
非逐字引用」標註不變，本文件的查證**沒有找到更精確的公式**，符合 B6.md
§6 步驟 5 的「查無」情況——但本文件對它的物理量級有信心（§3、§4.2 已
說明理由），**建議選 (a)：使用 §4.4 近似式，不需要因為查無就拆卡**。

**η_rad(f) 公式**：建議採用 §2.2 推導出的 `η_rad(f) = ρ₀c₀σ(f)/(ωρs)`，
程式碼註解需要明寫「推導自標準定義（輻射效率定義 + SEA 損耗因子定義），
非逐字引用某本教科書的頁碼」，與 §4.4 近似式的既有標註方式一致，不要
寫得看起来像是查到了某篇論文的原始公式。

**`η_i` 拆分（比 B6.md §4.2 原建議更推薦的做法）**：**不建議借用
`materials.json` 弦材質的 `eta` 欄位**（那是為弦內耗溯源的量，跟音板
結構內耗是不同物理機制，借用正當性弱，B6.md 自己也這樣質疑）。改為
**用已有的 `η_total≈0.02±0.01`（音板總損耗因子，`BRIDGE_ADMITTANCE_SOURCES.md`
§2.1 已有文獻出處）減去用 §2.2 公式算出的 `η_rad(f)`，得到
`η_i(f) = η_total − η_rad(f)`**——這樣不需要引入任何新的、正當性存疑的
借用值，且 §3 已經證明這個減法在雲杉典型參數下不會讓 `η_i(f)` 變負數
（自洽）。**代價**：`η_total` 只有一個「數 kHz 內近似無強系統性變化」的
單一數字（`ρ ± 0.01` 的不確定度頗大），`η_i(f)` 因此繼承同樣大小的不確定
度，跟借用材質 `eta` 的方案比，不確定度可能一樣大甚至更大——但至少物理
意義是清楚的（兩個損耗因子的差），不像借用弦材質 `eta` 那樣需要额外解釋
「為什麼弦的內耗參數可以套到板」。這個取捨是否可接受，仍建議在 Phase 1
實作時把兩種做法的 `η_i(f)` 差異量化寫進程式碼註解，讓下一輪工兵或月月
可以看到具體數字再確認。

**測試建構議**：§3 已指出用真實雲杉/琴橋參數時 `fc<f<fga` 那個「恆等於 1」
分支不可達，`testRadiationEfficiencyShape()` 的 `fc≤f<fga` 案例應該用
人造的 `fc`/`fga` 數值（例如故意設 `fc=1000, fga=2000`）而不是硬套雲杉的
`1.8kHz`/`1.3kHz`，否則測不到那個分支。

---

## 6. 引用清單

| # | 出處 | 取得狀態 | 本文件用到什麼 |
|---|---|---|---|
| 1 | Ege & Boutillon, *Vibroacoustics of the piano soundboard: reduced models, mobility synthesis, and acoustical radiation regime*, J. Sound Vib. 332 (2013)（arXiv:1305.3057） | ✅ 開放全文（本輪透過 ar5iv HTML 轉譯逐段查證，非摘要） | §2.1 `D̄ₓᴴ` 定義（§2.1 原文）與 `fc` 公式 (29)（§5.1 原文）；§2.2 確認 §5 全節無輻射功率公式 |
| 2 | Ege & Boutillon, *Synthetic description of the piano soundboard mechanical mobility*, ISMA 2010（arXiv:1210.5688） | ✅ 開放全文（同上方法查證） | §2.2 確認全文無 `W_rad`/`η_rad` 公式，`η` 僅以量測總損耗因子與模態重疊指標形式出現 |
| 3 | 聲學輻射效率 `σ` 的標準定義（noise control engineering 領域慣用寫法，多個獨立公開來源一致） | ⚠️ 二手轉述（WebSearch），非教科書原文逐字引用 | §2.2 `σ ≡ W_rad/(ρ₀c₀S⟨v²⟩)` 的定義本身 |
| 4 | Cremer, Heckl & Ungar, *Structure-Borne Sound* | ❌ 本輪仍未取得全文（教科書，付費） | 沿用 `BRIDGE_ADMITTANCE_SOURCES.md` §6 #8 既有紀錄，本文件無新進展 |
| 5 | Fahy & Gardonio, *Sound and Structural Vibration* | ❌ 未查（教科書，付費，本輪未嘗試新管道） | 未使用 |
| 6 | ScienceDirect Topics「Damping Loss Factor」頁面 | ❌ HTTP 403，無法讀取 | 未使用（原欲核對 `η_rad` 公式的二手整理頁） |
| 7 | monopole 輻射電阻 `∝(ka)²` 的聲學通識 | 📖 教科書通識（例如 Kinsler & Frey *Fundamentals of Acoustics*、Fahy *Foundations of Engineering Acoustics* 小聲源輻射章節），未逐字查證特定版本頁碼 | §4 第 2 點：作為 §4.4 `f²` 近似的物理類比依據，沿用 B6.md §4.4 原有標註方式 |

---

## 7. 狀態

- [x] `fc` 公式裡 `H` 的確切定義查到並確認：**`H` 不是獨立變數，是 `D̄ₓᴴ`
      符號裡 "homogenised" 的上標**，`fc` 公式本身需要從
      `ca²/(2π√(Dx·H))` 更正為 `ca²/(2π√(Dx/ρs))`（§2.1）
- [x] 逐段查證 `arXiv:1305.3057` §5 全節與 `arXiv:1210.5688` 全文，
      確認**兩篇論文都沒有**給出或等價於 `W_rad=σρ₀c₀S⟨v²⟩` 或
      `η_rad=ρ₀c₀σ/(ωρs)` 的公式（§2.2）
- [x] 改走「這兩條式子是否為標準定義的代數結果」路線，推導出兩條式子
      **可以**從輻射效率定義＋SEA 損耗因子定義代數推出（§2.2），
      但**沒有**取得可標頁碼的逐字出處
- [x] 用雲杉典型參數做量級自洽檢查，`η_rad(f) < η_total` 在整個模型
      有效範圍內成立，未發現矛盾（§3）
- [x] 發現並記錄「`fga<fc`（同一組骨架數字），模型有效範圍內
      `σ(f)=1` 分支實際不可達」這個對 Phase 1 測試設計有直接影響的事實（§3）
- [x] 評估 §4.4 近似式：**建議可用**，量級站得住，`monopole (ka)²` 類比
      成立，但明確指出真實次臨界輻射曲線（Maidanik 邊緣輻射理論）比
      單純 `f²` 複雜，§4.4 只是平滑近似（§4 第 2 點）
- [x] 評估 §4.2「能量守恆捷徑」：**標準 SEA 功率分配假設，可用**，但繼承
      音板集總近似已知的峰谷結構丟失問題（§4 第 4 點）
- [x] 評估 `η_i` 借用材質 `eta`：**不建議**，改建議 `η_i=η_total−η_rad(f)`
      自洽減法，理由與代價已寫明（§5）
- [ ] Cremer/Heckl/Ungar、Fahy & Gardonio 教科書原文本輪仍未取得——
      若未來借到書，應優先用書上原始推導取代本文件 §2.2 的代數重建
- [ ] ScienceDirect Topics 頁面 403，未能核對其對 `η_rad` 公式的整理
      （非關鍵，§2.2 的推導不依賴這個頁面，只是原本想找的輔助佐證）
- [x] **時間箱已達 B6.md 建議上限**（2 篇論文各 2 次針對性 fetch + 3 次
      WebSearch + 1 次失敗 fetch），本文件的查證到此為止，不繼續無限期搜尋

**給 Phase 1 的結論（摘要）**：**選 (a)，不建議拆卡**。`fc` 公式更正後
即可用；`σ(f)` 用 §4.4 近似式（標註不變）；`η_rad(f)` 用 §2.2 推導式
（新標註「推導自標準定義」）；`η_i(f)` 建議用 `η_total−η_rad(f)` 取代
「借用材質 eta」。所有這些都不是「查到文獻逐字公式」，必須在
`RadiationModel.h` 程式碼註解裡如實區分「§2.1 直接查到、§2.2 推導、§4.4
工程近似」三種不同溯源等級，不能混為一談。

---

## §5 補記（2026-08-28，B6 Phase 3/4 落地）：絕對校準路徑，與 §5 原文的骨架建議完全獨立

月月已就 §6 Phase 2 的三個候選方案裁決（見 `reports/decision_packets/
B6_calibration_choice.md`「裁決記錄」節）：**方案 B 先行，方案 C 立卡排隊
（`docs/workcards/B7.md`）**。本節記錄 Phase 3/4 依裁決落地後的實作細節。
**這是全新、額外新增的絕對校準路徑，與 §5 原文（Phase 1 的 `σ(f)`/
`η_rad(f)`/`η_i(f)` 建議）完全獨立、互不覆寫、互不消費彼此**——見下方
「為什麼刻意不消費 §5 原文的骨架」一節。

### 訊號分接點與校準常數

- **訊號分接點**：新增 `DiagnosticOverrides::capturePhysicsOnlyModes` 旗標
  （`src/dsp/DiagnosticOverrides.h`），比照既有 `bodyAmountOverride`／
  `disableExciterNoise`／`numStringsOverride` 的「診斷旗標，正常渲染路徑
  零影響」模式。旗標開啟時，`CimbalomVoice::noteOn()`（僅 CLI/
  `ScoreRenderer` 變體，不是 `startNote()` 即時播放路徑）額外擷取每個
  partial「創作層之前」的振幅——即 `spectralTilt`（程式碼明確標註為
  CREATIVE/HEURISTIC LAYER）與 `loudnessCompensationGain`／多弦正規化增益
  （`gain=noteComp/√N`）都尚未乘上去，但 `HammerImpulse::
  forceSpectrumMagnitude()`（槌頭力頻譜，物理量）已經乘上去的中間值。
  這個值只有 `ScoreRenderer::dumpModes()` 會讀取（透過
  `CimbalomVoice::getPhysicsOnlyModeAmplitudes()`），也只有 `dumpModes()`
  會把旗標設成 `true`；`render()`/`renderEvent()` 從未觸碰這個旗標，
  維持預設 `false`，§9 位元不變性驗證即是證明這一點。
- **校準常數**：`RadiationModel::kPascalsPerUnitPhysicsAmplitude = 1.0f`
  ——沿用 `EXTERNAL_ANCHOR_SOURCES.md` §1「數位 1.0 ≡ 1 Pa ≡ 94 dB SPL
  @1.05m」慣例，但釘在上述純物理訊號點，而不是最終渲染輸出（方案 A 會把
  `loudnessCompensationGain` 這種創作層數值一起算進物理主張，違反本 repo
  一貫的創作/物理分離原則，見裁決包 §2 對方案 A 風險的說明）。**這是
  月月裁決的方案 B 慣例錨定，不是實測值，也不是從任何文獻/物理定律推導
  出來的**——`RadiationModel::kPascalsPerUnitPhysicsAmplitude` 與
  `pressurePerForce()` 自己的程式碼文件已完整記載這一點（R4 溯源等級：
  「裁決常數」，見 `RadiationModel.h` class 文件新增的第四種溯源等級）。

### 為什麼刻意不消費 §5 原文（Phase 1）的 `σ(f)`／`η_rad(f)` 骨架

`acoustic_transfer[]`／`pressurePerForce()` **刻意不把 `radiationEfficiency()`
（σ(f)）或 `radiationLossFactor()`（η_rad(f)）當成 Pa/N 計算裡的乘數**，
只用 `criticalFrequency()`／`acousticCutoffFrequency()` 算出的 `fc`/`fga`
當作「這個 partial 在不在模型有效範圍內」的**閘門**（f≥fga 就不輸出）。
理由：

1. `σ(f)` 是 §4.4 標註為「工程近似、非文獻曲線」的量，量級可信但形狀不保證
   精確（§4 第 2 點）；`absolute_pressure_per_force` 是要拿去跟真實試體
   PASS/FAIL 比對的量——把一個形狀不確定度未量化的近似式，乘進一個要做
   絕對數字判定的 claim 裡，會讓 FAIL 的時候無法區分「校準常數錯了」還是
   「σ(f) 形狀錯了」還是「基礎物理（弦模態/槌頭力鏈）錯了」，混淆了三種
   完全不同來源的不確定度，違反本文件與 `RadiationModel.h` 一貫的
   「溯源等級不可混為一談」原則。
2. `σ(f)`（`radiated_power_relative`）本來就已經是獨立輸出的**資訊性**
   欄位（Phase 1，不進 `model_observables` 的 specimen_verify.py 判定路徑），
   讓它繼續獨立存在、不被下游任何判定消費，才符合它原本「僅供人工/未來
   工作檢視趨勢」的定位（B6.md §5）。
3. 這個設計選擇也是刻意在 Option B（校準捷徑）與 Option C（B7，完整第一
   原理力鏈，會需要 `S`／真實輻射面積等才能正確接上 σ(f)/η_rad(f)）之間
   劃清界線——Option B 不應該「半調子」地借用 Option C 才需要的物理骨架，
   否則兩張卡的職責會混在一起，且會讓 Option B 的絕對數字看起來比它實際
   站得住的證據更有把握。

### `imag_pa_n = 0.0` 的明確聲明（非相位主張，R9 域外標註）

`acoustic_transfer[].pressure_per_force_imag_pa_n` **固定寫 `0.0`**。
**這不是相位主張**——本模型完全沒有相位模型（弦/槌頭時域波形相位、
音板耦合相位、輻射傳播相位，一概沒有實作）。`imag=0.0` 純粹是 schema
形狀佔位值，讓 `pressure_per_force_real_pa_n` 單獨承載一個「非負量級」
主張（且 `pressurePerForce()` 對非正輸入 fail-closed 到 sentinel，保證
輸出永遠 `>0`，不會用負號隱含 180° 相位）。`specimen_verify.py` 的
`radiation_directivity` claim（會把 real/imag 一起讀成相位角）仍然被
`"radiation_directivity"` 未加入 `model_observables` 這件事擋住，不會
因為 `acoustic_transfer` 有了 real/imag 欄位就意外被解鎖。程式碼
（`ScoreRenderer.h::dumpModes()`／`RadiationModel::pressurePerForce()`）
的相關註解都已明寫這一點；`tests/test_specimen_verify.py` 的既有哨兵測試
（`RealDumpModesRadiationSentinelTests`）持續驗證 `radiation_directivity`／
`complex_phase` 不會被誤加進 `model_observables`（見 §7 補記）。

---

## §7 補記（2026-08-28，B6 Phase 3/4 狀態）

- [x] 月月已就 Phase 2 裁決：**方案 B 先行**（本節記錄的落地內容），
      **方案 C 立卡排隊**（`docs/workcards/B7.md`，`reports/decision_packets/
      B6_calibration_choice.md`「裁決記錄」節）
- [x] 新增純物理訊號分接點（`DiagnosticOverrides::capturePhysicsOnlyModes`
      ＋ `CimbalomVoice::getPhysicsOnlyModeAmplitudes()`），
      `render()`/`renderEvent()`/`ModalResonator` 零改動——單元級證明
      （`testPhysicsOnlyCaptureDoesNotAffectRender()`，旗標開關下
      `getAllStringModes()` 位元相同）與 corpus 級證明（§9 位元不變性，
      8 首代表曲目 SHA256 前後全同）雙重驗證通過
- [x] `RadiationModel::kPascalsPerUnitPhysicsAmplitude`／`pressurePerForce()`
      落地，R4 註解明寫「月月裁決的方案 B 慣例錨定，非實測、非推導」；
      刻意不消費 `σ(f)`／`η_rad(f)`（理由見上方新節）
- [x] `dumpModes()` 加 `"absolute_pressure_per_force"` 至
      `model_observables`；合格事件加 `acoustic_transfer[]`
      （`radius_m`/`azimuth_deg`/`elevation_deg` 寫死 1.05/0/0；
      `imag_pa_n` 固定 0.0 且明確非相位主張；`f≥fga` 的 partial 不輸出；
      非合格引擎（beam/tongue_drum/plate/water_gong/custom/fm）或缺
      D/ρs 的事件輸出空陣列 `[]`，不是省略整個鍵）
- [x] `radiation_directivity`／`complex_phase` 確認仍未被誤加進
      `model_observables`（既有哨兵測試 `RealDumpModesRadiationSentinelTests`
      持續守；三則既有測試已同步更新以反映 Phase 3/4 現況——
      `absolute_pressure_per_force`／`acoustic_transfer` 從「禁止出現」改為
      「預期出現」，`radiation_directivity`／`complex_phase` 依舊禁止）
- [x] C++ 單元測試：`testPressurePerForceCalibration()`（手算對照 + 反例：
      doubled-calibration-constant mutant、零/負/NaN/+Inf 全部 fail-closed）、
      `testPhysicsOnlyCaptureDoesNotAffectRender()`（旗標開關下渲染路徑
      位元相同的單元級證明 + 正控制：physics-only 振幅確實不同於
      render-path 振幅，證明創作層乘數真的被排除，不是複製貼上把兩者
      混在一起）
- [x] Python 端 `Phase4SelfConsistencyTests`（`tests/test_specimen_verify.py`）：
      真實 CLI `--dump-modes` 輸出（A4/steel/velocity=0.5，
      `kCimbalomAttackEnergyRefA4` 同一錨點，`strike_position` 從錨點的
      0.3 微調到 0.31——理由：0.3 是低分母有理數，`StringModel::
      calculateModes()` 的 `sin(n·π·strikePosition)` 模態形狀公式在
      n=10/20/30 產生真實的物理振幅零點，`specimen_verify.py` 對
      dump 全部 partials 做無條件的「必須可比對」檢查（`predicted_by_index`
      構造階段，早於任何 claim 判定），振幅零點會讓整個 bundle
      REFUSED——這是既有、與 B6 無關的模型/harness 交互作用，本卡依
      B6.md §3 規定不得修改 `specimen_verify.py`，改用不撞到有理數重合的
      鄰近撞針位置迴避，已於測試檔內完整記錄理由）原封不動複製成
      `SYNTHETIC_TEST_ONLY` 標記的 v2 bundle，`absolute_spl` claim
      判 **PASS**；反例（其中一個 measured 點 `transfer_level_db_re_20upa_per_n`
      故意 +10dB）判 **FAIL**（實測誤差精確等於 10.0 dB，見
      `reports/gate_outputs/b6_specimen_selftest.txt`）
- [x] GATE 全套：三 build target exit 0、ctest 3/3、pytest 全數 passed、
      `--full` 與 Phase 1 基準零差異、§9 位元不變 8/8、corpus
      `verify_score.py --all`、specimen selftest（PASS/FAIL 各一）——
      詳細數字見 `TODO.md`/`ROADMAP_PHYSICS.md` B6 條目與
      `reports/gate_outputs/` 下對應檔案

---

## §3 補記（2026-08-28 Opus 稽核實測）：fc 與 fga 幾乎重合，σ=1 分支的活動窗極窄

以實際生效的引擎參數（wood_spruce：E=12 GPa、ν=0.37、ρ=450 kg/m³、h=9 mm →
D=844.63 N·m、ρs=4.05 kg/m²）代入 Phase 1 落地的公式：

- `fc = 1274.01 Hz`、`fga = 1307.69 Hz`（fc/fga = 0.974）
- 「`fc ≤ f < fga` → σ=1」的重合飽和分支只有 **33.7 Hz 活動窗**（佔模型
  有效頻寬約 2.6%）；實測 dump 中帶 `radiated_power_relative` 的最高 partial
  為 1300.97 Hz，恰落在此窄縫。
- 換言之，**97%+ 的輸出值走的是 §4.4 的 (f/fc)² 工程近似**——整個欄位的
  可信度幾乎完全押在該近似上（其「保量級不保形狀」的侷限本文件 §4 已載明）。
- 另一層意義：均質板模型撐過重合頻率沒多久就失效（fc 略小於 fga，
  σ=1 飽和分支窗＝fga−fc＝33.7 Hz——模型還沒真正走遠就碰到 fga 這個
  「無預測」邊界）。此組實測數字供 Phase 2 校準裁決時參考。

（註：本文件 §3 原表用的骨架數字 fc≈1.8 kHz 來自 Ege & Boutillon 的鋼琴音板
參數；上述 1274 Hz 是本引擎 wood_spruce/9mm 實際參數的結果，兩者不同屬正常，
非矛盾。）
