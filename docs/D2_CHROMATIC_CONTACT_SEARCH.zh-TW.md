# D2 文獻補搜：Chromatic 引擎（舌鼓／鑼）槌具接觸參數

> **草稿（draft），待 Opus 溯源稽核。**
> **未經月月核准，本文件的任何數值不得寫入 `data/materials.json`、不得寫入程式碼、
> 不得用於任何 GATE 判定。**（此行由 Opus 於 2026-08-28 稽核時補上，原檔頭缺此聲明；
> 見 §6 finding B4。）
> 建立：2026-08-28。對應 `TODO.md` D2：「舌鼓／鑼的槌具接觸參數——**未搜尋，狀態未知**。
> 擋住 B4 對 Chromatic 引擎的適用性」。
> 對應 `docs/HAMMER_CONTACT_SOURCES.md` §6：「這批資料是**鋼琴專屬**的……
> Chromatic（tongue drum / water gong）在確認有對應量測之前，不得把鋼琴槌氈的
> 常數搬過去」。
>
> **本文件不改任何程式碼、不改任何容差。** 它只回答：舌鼓／鑼的槌具接觸模型
> 需要哪些數字，本輪搜尋拿不拿得到。**結論先講：拿不到——這是四個缺口裡
> 資料最薄的一個，不能關閉。**
>
> 搜尋方式：`WebSearch` 多輪查詢 + `WebFetch`／直接下載 PDF 後用 `pymupdf`
> 抽取全文（`WebFetch` 對掃描版 PDF 常回報「無法解析二進位串流」，故對兩份
> 可下載到本機的 PDF 改用本機文字抽取）。凡本文件引用的數字，都標明是從
> 哪一份文件、哪一頁/哪一節**親眼讀到**；讀不到全文的，只列「確認存在」
> 或「間接引用」，不假裝有數字。

---

## 0. 白話

D2 要問的是：舌鼓（tongue drum／handpan／tank drum）跟鑼／鑔鑼（gong／tam-tam）
被槌子或手指打的時候，「槌子壓進去多硬、壓多久」這件事，有沒有人**實測過**、
數字能不能直接搬進 `HammerImpulse.h` 的接觸解算器。

搜尋結果：**沒有**。舌鼓／鑼這兩種樂器本身的「敲了之後怎麼震」（模態、
非線性音高滑移）有人量測過（`docs/EXTERNAL_ANCHOR_SOURCES.md` §5 已找到，
但都卡在付費牆／機構庫，且那是模態量測不是接觸量測）；但「槌子打上去的
那一下接觸力學」——就是 B4 用在鋼琴上的 `F = K·δ^α`、接觸時間 τc 那組
東西——目前搜尋不到舌鼓或鑼的**專屬**量測。

比較接近的東西找到三種，但每一種都有明確的理由不能直接當替代：

1. **馬林巴／木琴槌具接觸**（Chaigne & Doutaut 1997）——確認這篇論文
   對槌-音條接觸用的正是同一種 Hertz 冪律模型，但**論文本文的 K／α
   數字本輪搜尋拿不到**（付費牆，只查到摘要與二手引用確認其存在）。
2. **鼓槌-鼓面（membrane）接觸的一組可用數字**（Bilbao et al. 2012，
   開放全文）——真的讀到 `K = 1.6×10⁸`、`α = 2.54`、槌質量 `0.028 kg`，
   但這是**膜**（張力主導的定音鼓／timpani），不是**板／樑**
   （舌鼓的舌片是懸臂樑、鑼是板）——力學機制不同，不能直接當
   Chromatic 的錨；而且這組數字連是否等於原始量測（Rhaouti, Chaigne,
   Joly 1999 定音鼓論文）都無法確認，論文自己只說「大致對應一個典型鼓的
   設定」。
3. **木琴/鐵琴槌具硬度對接觸時間影響的實測方法**（Bork 1983b，經
   Fletcher & Rossing 1991 轉引）——確認有人用壓電力規實測十支不同硬度
   槌具打樑類樂器的 `F(t)`，並給出「衝擊時間 τc → 最佳激發頻率
   `f_max = 0.85/τc`」這個可直接用的解析關係；**但原始報告是德國 PTB
   未出版內部報告**，書中只轉載一張示意圖，圖上的實際數字本輪
   OCR 不出可信賴的表格，所以只能引用「這個方法與關係式存在」，
   不能引用「哪支槌具的 τc 是幾毫秒」。

以下逐項附出處。

---

## 1. 搜尋範圍與方法

用 `WebSearch`（多輪）+ `WebFetch` 對以下三類做搜尋：

1. 鋼舌鼓／handpan／tank drum：手指或槌具接觸時間、接觸剛度、
   力-變形律的實測研究。
2. 鑼／tam-tam／水鑼的槌（軟頭槌）接觸實測。
3. 一般性 mallet-percussion 接觸文獻（marimba/vibraphone yarn mallet
   的 `K`、`α`、接觸時間實測；Chaigne & Doutaut 一類）。

對搜尋命中的兩份可公開下載的完整 PDF（Fletcher & Rossing 1991《The Physics
of Musical Instruments》全書掃描版；Bilbao, Torin & Chatziioannou 2012
"Numerical Modeling of Collisions in Musical Instruments" arXiv 全文）
改用本機下載 + `pymupdf` 抽取文字後逐頁查證，取代對掃描 PDF 常失敗的
`WebFetch`。其餘來源（JASA、ResearchGate、Springer 書章）**全數撞牆**——
`WebFetch` 回報 403 或登入導向頁，未能取得全文，本文件對這些一律標
「確認存在，全文未取得」，不轉引搜尋摘要裡可能被 AI 摘要工具**改寫過**
的數字。

---

## 2. 找到什麼

### 2.1 鋼舌鼓／handpan：**沒有任何工程量測**

搜尋「steel tongue drum / handpan 接觸時間、剛度、力-變形」只命中
樂器行銷部落格與玩法教學（如「打完手指要立刻離開，不然悶音」），
全是質性的演奏描述，**沒有一篇是儀器量測**。也沒有找到任何論文把
Hertz 冪律接觸模型套用在舌鼓/handpan 的舌片或鋼面上。

`docs/EXTERNAL_ANCHOR_SOURCES.md` §5.1 先前找到的
*Experimental characterization of the steel tongue drum*（ICSV27,
Prague, 2021）是**模態**量測（`TODO.md` D4 待補全文），跟接觸力學是
兩回事；本輪重新確認搜尋引擎能找到的公開摘要中，該文也未提及接觸
剛度或接觸時間。

**結論：這一塊是四個缺口裡最空的，目前沒有任何可引用的數字或方法。**

### 2.2 鑼／tam-tam：找到的是**另一種非線性**，不是槌具接觸非線性

搜尋鑼／tam-tam 的「非線性」文獻，命中的都是鑼**自身**在大振幅下的
幾何非線性（模態耦合、音高滑移），跟槌頭壓縮的接觸非線性是**不同機制**：

- Fletcher & Rossing (1991), *The Physics of Musical Instruments*
  （Springer-Verlag New York, 1991 初版；本文件核對用的完整掃描版
  ISBN 978-0-387-94151-6 實際對應 **1993 年 Springer Study Edition
  印次**，非 1991 年初版本身，見 §6 finding B3——章節/頁碼經核對與本次
  使用的掃描件一致，不受此書目精確度問題影響），
  §20.6「Nonlinear Mode Coupling in Tam-Tams」（原書 p.561）與
  §20.9「Nonlinear Effects in Gongs」（p.566）：中國鑼敲擊後音高會
  滑移（大鑼下滑最多 3 個半音、小鑼上滑約 2 個半音），機制是
  **鑼面板/淺殼自身的 hardening/softening spring 行為**（大鑼中央近似
  平板走 hardening、小鑼中央近似球冠殼走 softening），跟 §3.14
  的板殼幾何非線性是同一件事；書中明確歸因於 Rossing & Fletcher
  (1982, 1983) 與 Fletcher (1985) 的模態耦合分析，**完全沒有涉及槌頭
  本身的接觸力學**。
- 同一批搜尋也命中一篇關於巴里島甘美朗鑼「諧波非線性」的會議論文
  （*An investigation of directional and vibrational characteristics of
  a nonlinear harmonic of a Balinese gamelan gong*, POMA 56, 2024/2025），
  摘要同樣指向「Hertzian nonlinear stiffness 造成 softening」——但這裡的
  「Hertzian」講的也是**鑼面在大振幅下的幾何/材料非線性**，不是「槌頭
  壓縮鑼面」的接觸律；本文件**未取得全文**，僅能確認摘要層級的措辭，
  不確定它是否恰好也報告了槌頭接觸參數，**列為待查**，不當成已找到。

**這是本文件要特別提醒的一點**：任何人以後在 codebase 裡看到「鑼的
非線性」字眼，要先確認講的是槌具接觸非線性（`F=K·δ^α`，D2 要補的）
還是鑼面板殼自身的幾何非線性（`docs/EXTERNAL_ANCHOR_SOURCES.md`／
`BeamModel.h`／`PlateModel.h` 既有機制），兩者不可混用同一組參數。

`docs/EXTERNAL_ANCHOR_SOURCES.md` §5.1 已列出的
*Study of vibration and sound characteristics of a copper gong*
(J. Chinese Inst. Engineers 28(4), 2005) 本輪再次確認**付費牆**，
仍未取得全文；即使取得，該文書名看起來也是模態量測，不保證含槌具
接觸參數。

**結論：沒有找到鑼／tam-tam 專屬的槌具接觸實測數字。**

### 2.3 一般性 mallet-percussion 接觸文獻

這一節找到三個層級不同的東西，由弱到強列出。

#### 2.3.1 Chaigne & Doutaut (1997)：確認存在，數字拿不到

> A. Chaigne, V. Doutaut, "Numerical simulations of xylophones.
> I. Time-domain modeling of the vibrating bars," *J. Acoust. Soc. Am.*
> 101(1), 539–557 (1997).

多個獨立二手來源（Bilbao et al. 2012 的參考文獻 [3]；ResearchGate／
Semantic Scholar 摘要頁）一致確認：這篇論文對**木琴音條-槌具**的作用
力，用的就是「線彈性體的 Hertz 接觸律」（跟 B4 鋼琴槌氈用的同一族
`F = K·δ^α` 模型，只是槌具/音條材料不同）。

**但本文件無法取得該論文全文**（JASA 付費牆、ResearchGate 僅摘要、
`WebFetch` 對 PDF 連結一律 403）。因此：

- ✅ 確認「馬林巴/木琴槌-音條接觸用 Hertz 冪律模型」這個**方法論事實**。
- ❌ 沒有拿到該文獻報告的 `K`、`α` 實際數值、接觸時間量測值，或槌質量。

一篇後續、同課題的論文——Henrique & Antunes,
*Optimal Design and Physical Modelling of Mallet Percussion Instruments*
——多個索引站（Semantic Scholar／ResearchGate／Academia.edu）都能找到
標題與摘要，但本輪 `WebFetch` 對 Academia.edu 連結回報 403、對
Semantic Scholar 頁面回報內容為空，**同樣沒有取得可引用的數字**。

#### 2.3.2 Fletcher & Rossing (1991) §19.7「Mallets」：一個真的可用的解析關係，但沒有可信的數字表

> N. H. Fletcher, T. D. Rossing, *The Physics of Musical Instruments*,
> Springer-Verlag New York, 1991 初版（本文件核對用的掃描版 ISBN
> 978-0-387-94151-6 實際對應 1993 年 Springer Study Edition 印次，
> 非 1991 年初版，見 §6 finding B3；章節/頁碼與本次掃描件一致），
> Chapter 19 "Mallet Percussion Instruments," §19.7 "Mallets"（原書
> pp. 547–549）。

本文件下載到這本書的完整掃描版全文並親自讀了 §19.7。內容：

- **質量匹配的經驗法則**：「槌具與被打物體的動態質量相近時，能量傳遞
  最大；對馬林巴音條的基頻模態而言，動態質量約為音條總質量的 30%」
  （原文："A mallet whose mass nearly equals the dynamic mass of the
  struck vibrator (typically about 30% of the total mass for a marimba
  bar in its fundamental mode) transfers the maximum amount of energy
  to the vibrator."）。**這是一個可轉引的具體數字（30%），但它是「質量
  比」的經驗法則，不是 `K`／`α` 接觸律參數**，且原文沒有標明是哪篇
  原始量測給出的 30% 這個值（書中未在此句附引用）。
- **量測方法**：Bork (1983b) 用壓電力規實測槌具敲擊時的力波形 `F(t)`，
  取其「衝擊譜」（shock spectrum，方法源自 Morrow 1957 與 Kittelson
  1966），對一個形如 `sin²(2πt/τc)` 的脈衝，衝擊譜的峰值頻率滿足
  ```
  f_max = 0.85 / τc
  ```
  （書中式子如此陳述，`τc` 為衝擊持續時間）。書中 Fig. 19.12 用這個方法
  比較了十支硬度不同的槌具（標號 S1、S3、S9、S10、S50、S100 等）在
  槌頭速度 0–3.5 m/s 範圍內 `f_max` 隨速度變化的曲線，並指出：全橡膠槌
  （S1）`f_max` 幾乎不隨力度變（曲線平），硬芯繞紗槌（S10）在高把位
  木琴/鐵琴很好用、可用音域跨兩個八度以上；木芯配橡膠環的槌（S9）則
  在弱擊時 `f_max` 隨力度變化明顯、強擊時被硬芯限制住。
- **原始量測的取得狀態**：Bork (1983b) 全名
  *"Entwicklung von akustischen Optimierungsverfahren für Stabspiele
  und Membraninstrumente"*，是德國 **PTB（Physikalisch-Technische
  Bundesanstalt）Project 5267 的未出版內部報告**（書中原文標註
  "unpublished"）。**這意味著即使想找全文查證圖上數字，管道也極窄
  ——不是一般論文資料庫能查到的東西。**
- Fig. 19.12 的 y 軸刻度與各曲線標號在本文件用的 PDF 是掃描 OCR，
  數字大量錯位／無法可靠對應到哪條曲線是哪支槌具的哪個 `f_max` 值。
  **本文件不把這張圖的任何讀值當成可用數字**——這正是任務指示
  「沒實際看到的數字不准寫，寧缺勿假」要防的情況：圖存在、方法存在、
  但逐點數字讀不出來就是讀不出來。

**這一節對 D2 的意義**：它給了一個**可獨立驗證、不靠查表的解析工具**
（衝擊譜法 `f_max = 0.85/τc`），如果 TsukiSynth 未來要自己對真實舌鼓
或鑼做實測，這是一個文獻上站得住腳的量測方法；但它**不能直接提供
D2 要的數字**。

#### 2.3.3 Bilbao, Torin & Chatziioannou（arXiv 預印本，正式出版 2015）：一組讀得到的數字，但是膜不是板/樑

> S. Bilbao, A. Torin, V. Chatziioannou, "Numerical Modeling of
> Collisions in Musical Instruments," *Acta Acustica united with
> Acustica* **101(1): 155–173 (2015)**。開放全文：arXiv:1405.2589
> （**2026-08-28 finding B2 修正**：先前版本引用卷期寫成「98 (2012)」，
> 那是預印本頁眉本身印著的「Vol. 98 (2012)」投稿模板殘留字樣，並非
> 憑空捏造，但與正式出版卷期不符，正式出版為 101(1): 155–173, 2015；
> **修正範圍（2026-08-28 複驗後更正措辭）**：本節引用區塊與 §4 引用清單
> 改用正式出版卷期；本文件其他段落的行內短引（如「Bilbao et al. 2012」）
> 是對應實際下載閱讀的 arXiv 預印本的年代標記，刻意保留，均指同一篇論文）。

本文件下載並讀了這篇全文（Section 7「The Mallet-Membrane
Interaction」）。文中給出一個完整的槌-膜接觸數值範例（原文
Figure 12 圖說）：

| 參數 | 值 |
|---|---|
| 槌質量 `M` | 0.028 kg |
| 接觸剛度 `K` | 1.6 × 10⁸（單位隨 `α` 而定，`N·m^-α`） |
| 接觸指數 `α` | 2.54 |
| 膜面密度 `ρm` | 0.26 kg/m² |
| 膜張力/單位長 `Tm` | 3325 N/m |
| 膜尺寸 | 0.6 m × 0.6 m 方形膜 |
| 敲擊點 | 距角落 0.1 m |

文中在引入這個模型時寫「power law nonlinearity ... sometimes
chosen[4]」，`[4]` 指向 L. Rhaouti, A. Chaigne, P. Joly,
*"Time-domain modeling and numerical simulation of a kettledrum,"*
JASA 105 (1999) 3545–3562——也就是把這個接觸律用在**定音鼓**上的
原始論文。

**但要誠實標注三件事**：

1. 這組 `M`/`K`/`α`/膜參數本身確實逐字出自 Figure 12 圖說（圖說只列
   參數數值，不含任何敘述句）。「大致對應一個典型的鼓的設定」
   （*"corresponding roughly to a typical drum configuration"*）這句話
   **出自正文 §7.2 Simulations，不在 Figure 12 圖說內**（**2026-08-28
   finding B1 修正**：先前版本誤標這句話的出處為圖說本身；圖說本身
   只列參數）。無論出處是正文還是圖說，**都沒有逐字寫這就是 Rhaouti
   et al. 1999 論文裡量測或擬合出的數字**——有可能是 Bilbao 等人為了
   教學示範另外選的合理數量級。本文件**沒有取得 Rhaouti, Chaigne &
   Joly (1999) 原始論文全文**（同樣付費牆），無法逐一核對這幾個數字是
   否等於該論文的實測值。**這是間接引用，不是一手數字**——出處位置
   標錯不影響這個結論。
2. 這是**膜**（membrane，張力 `T` 主導的波動方程），不是舌鼓的舌片
   （懸臂樑，彎曲剛度 `EI` 主導）也不是鑼的板/淺殼（彎曲剛度主導、
   有預應力）。膜、樑、板三者的恢復力機制不同，槌具接觸端本身的
   力學（槌頭壓縮氈/橡膠的非線性）理論上可以跟被打物體的類型無關
   （槌具軟墊的 `K`/`α` 主要取決於槌具材料，不是取決於被打物體），
   但**這一點是本文件的推論，不是任何一篇引用文獻明講的**——沒有
   文獻直接證明「同一支槌具打膜跟打樑/板，`K`/`α` 不變」。所以就算
   接受這組數字代表某種鼓槌的接觸特性，能不能套到打舌鼓/鑼的槌具
   上，仍是未驗證的假設。
3. `α = 2.54` 這個值恰好落在 B4 鋼琴槌氈實測範圍（`α = 2.3–3.0`）
   附近——這**可能**暗示「軟質槌具打振動面」的接觸指數普遍落在
   2.3–3 這個區間，不管是鋼琴氈還是鼓槌橡膠/氈頭；但這仍然只是
   兩個獨立數據點湊巧接近，**不構成「Chromatic 可以借用鋼琴 α」的
   證據**——B4／HAMMER_CONTACT_SOURCES.md §6 的裁決（不得把鋼琴槌氈
   常數搬到 Chromatic）依然成立，本文件沒有推翻它的理由。

---

## 3. 缺口清單（誠實列出，寧缺勿假）

- [ ] 舌鼓（tongue drum/handpan/tank drum）槌具或手指接觸的 `K`、`α`、
      接觸時間——**完全沒有找到任何工程量測**，連方法論文獻都沒找到。
- [ ] 鑼／tam-tam 槌具接觸的 `K`、`α`、接觸時間——**沒有找到**；
      找到的「鑼的非線性」文獻全部是鑼面板殼自身的幾何非線性，
      跟槌具接觸是不同機制（§2.2）。
- [ ] Chaigne & Doutaut (1997) 木琴音條-槌具的實際 `K`／`α` 數值與
      逐音表——**確認論文存在且用 Hertz 冪律，但全文付費牆未取得**。
- [ ] Henrique & Antunes（mallet percussion optimal design）的實際
      參數表——**確認論文存在，全文未取得**（Academia.edu 403、
      Semantic Scholar 頁面空白）。
- [ ] Bork (1983a/b) 兩份原始報告（分別是 TU Braunschweig 博士論文、
      PTB 未出版內部報告）——**只查到 Fletcher & Rossing (1991) 的
      轉引與一張讀不出數字的圖，原始報告本身的取得管道未知**。
- [ ] Rhaouti, Chaigne & Joly (1999) 定音鼓論文原文——**未取得**，
      無法核對 Bilbao et al. (2012) Fig.12 的槌-膜參數是否等於該文
      實測值（§2.3.3 第 1 點）。
- [ ] 任何材料（不管樑/板/膜）的槌具接觸**遲滯**（hysteresis）參數
      ——本輪完全沒有搜到，B4 §5 的 Stulov 遲滯參數仍然只對鋼琴氈
      成立。
- [ ] `docs/EXTERNAL_ANCHOR_SOURCES.md` §5.1 已知的舌鼓 ICSV27 2021、
      銅鑼 JCIE 2005 兩篇全文依舊未取得（`TODO.md` D4/D5）——但這兩篇
      即使拿到全文，性質是**模態**量測，不是接觸量測，不能自動填上
      D2 的缺口，只是有機會在附錄或方法段落提到敲擊方式（未證實）。

---

## 4. 引用清單

| # | 出處 | 取得狀態 | 用到什麼 |
|---|---|---|---|
| 1 | Fletcher, N. H., Rossing, T. D., *The Physics of Musical Instruments*, Springer-Verlag New York, 1991 | ✅ 取得完整掃描全文，本文件親自讀了 Ch.19/20 | §2.3.2 質量匹配經驗法則、Bork 衝擊譜法與 `f_max=0.85/τc`；§2.2 鑼/tam-tam 非線性機制辨正 |
| 2 | Bilbao, S., Torin, A., Chatziioannou, V., "Numerical Modeling of Collisions in Musical Instruments," *Acta Acustica united with Acustica* 101(1): 155–173 (2015)（arXiv 預印本 1405.2589 頁眉誤植 Vol. 98 (2012)，見 B2） | ✅ 開放全文，本文件親自讀了 Section 7 | §2.3.3 槌-膜接觸數值範例（`M`/`K`/`α`） |
| 3 | Chaigne, A., Doutaut, V., "Numerical simulations of xylophones. I," *JASA* 101(1), 1997 | ❌ 付費牆，僅摘要與二手引用確認存在 | §2.3.1：確認木琴槌-音條用 Hertz 冪律，數字未取得 |
| 4 | Henrique, L., Antunes, J., "Optimal Design and Physical Modelling of Mallet Percussion Instruments" | ❌ Academia.edu 403／Semantic Scholar 頁面空白 | 僅確認標題與研究主題存在 |
| 5 | Bork, I. (1983a), TU Braunschweig 博士論文；Bork, I. (1983b), PTB Project 5267 未出版報告 | ❌ 原始報告未取得，僅有 [1] 的轉引描述與一張讀不出數字的圖 | §2.3.2 |
| 6 | Rhaouti, L., Chaigne, A., Joly, P., "Time-domain modeling and numerical simulation of a kettledrum," *JASA* 105, 1999 | ❌ 付費牆，僅由 [2] 的參考文獻列表確認存在 | §2.3.3 第 1 點提到的方法論來源，數字未核對 |
| 7 | *Study of vibration and sound characteristics of a copper gong*, J. Chinese Inst. Engineers 28(4), 2005 | ❌ 付費牆（`docs/EXTERNAL_ANCHOR_SOURCES.md` §5.1 已知） | 再次確認未取得 |
| 8 | *An investigation of directional and vibrational characteristics of a nonlinear harmonic of a Balinese gamelan gong*, POMA 56 | ❌ 僅讀到搜尋摘要，未取得全文 | §2.2：摘要層級提及 Hertzian 措辭，但指的是鑼面幾何非線性，非槌具接觸；未列入缺口以外的任何主張 |

**沒有從任何論文圖表數位化取值。** §2.3.2 明確排除了唯一一張「看起來
有數字」但讀不出來的圖（Fletcher & Rossing Fig. 19.12）。

---

## 5. D2 能不能關閉的評估

**結論：不能關閉。**

跟 D2 對照的參考基準是 B4 之所以能動工的原因——`HAMMER_CONTACT_SOURCES.md`
§2 有一份**逐音、可直接轉錄進程式**的表格（Woodhouse *Euphonics* 轉引
Hall & Askenfelt 的 C2/C4/C7 三點 `K`/`α`），外加逐音的槌質量表、
弦張力表，還有 §5 的 Stulov 遲滯參數，四樣都是**看得到數字、標得出
量測條件**的東西。

D2 本輪搜尋完全沒有找到對等的東西：

- **舌鼓、鑼各自專屬的接觸量測**：零。連「有人做過但拿不到全文」的
  程度都沒有——找不到任何論文標題顯示有人真的量過舌鼓舌片或鑼面
  被槌具/手指壓縮的力-變形關係。
- **可用的替代錨**：三個候補（Chaigne & Doutaut 木琴、Bilbao 等人的
  槌-膜範例、Bork 的衝擊譜法）沒有一個滿足「數字可信 + 力學機制吻合」
  兩個條件同時成立——Chaigne & Doutaut 力學機制吻合（同為樑類振動體）
  但數字拿不到；Bilbao 等人數字讀得到但力學機制是膜不是樑/板，而且
  連是否為一手實測都存疑；Bork 的方法可信但數字讀不出來。
- 唯一可以現在就用的東西是**方法論**，不是**參數**：如果月月未來想
  自己對一顆真實舌鼓或鑼做接觸量測，Bork/Morrow 的衝擊譜法
  （`f_max = 0.85/τc`，需要壓電力規或高速攝影/加速規反推）是文獻上
  站得住腳的做法；但這是「怎麼量」，不是「量出來是多少」，不能讓
  B4 的解算器直接動工。

**建議的下一步（供裁決，本文件不擅自排優先序）**：

1. 若月月有機構圖書館或館際互借管道，`Chaigne & Doutaut (1997)`
   JASA 全文是目前找到、力學機制與 Chromatic 舌片/鑼面最接近的
   候選——它是唯一一篇明確針對「槌具打樑類振動體」做 Hertz 冪律
   量測與擬合的論文。優先度應該高於再去找舌鼓/鑼的專屬論文，因為
   後者連存在都還沒確認。
2. `Bork (1983a)` 是 TU Braunschweig 的博士論文，德國國家圖書館
   （DNB）或 TIB Hannover 這類機構典藏偶爾能調到未出版學位論文；
   但這條路徑本文件未實際嘗試（超出 WebSearch/WebFetch 能做的範圍），
   純屬猜測性建議。
3. 在拿到任何一組舌鼓/鑼專屬數字之前，**Chromatic 引擎維持現行的
   `HammerImpulse::tauCForNote` 查表式 proxy 不變**——這不是新結論，
   是 `HAMMER_CONTACT_SOURCES.md` §6 既有裁決的延續：B4 的真解算器
   只能留在 Cimbalom/Piano Felt 分支，不得擴大到 Chromatic。

---

## 6. Opus 稽核記錄（2026-08-28）

> 稽核者立場：**預設引用是編造的**。以下每一條都對應本次實際下載、實際打開、
> 實際比對字串的檔案。稽核不改動本文件 §0–§5 任何一個字（只在檔頭補了一行
> 核准聲明，見 B4），本節為追加。

### 6.1 抽查清單與結果

本文件的特殊性在於它**主要是一份「找不到」的報告**，所以稽核重點放在兩件事：
(a) 少數真的有數字的引用是否為真；(b)「找不到」的宣稱有沒有誇大或縮小。

| # | 抽查的引用 | 來源是否存在 | 數字是否相符 | 條件是否被斷章 |
|---|---|---|---|---|
| 1 | §2.3.3 Bilbao et al. (2012) Fig. 12 全套槌-膜參數 | ✅ arXiv:1405.2589 全文取得 | ✅ **七個數字全部逐位相符** | ✅ 未斷章，且本文件主動標明是膜非樑/板 |
| 2 | §2.3.3 「power law nonlinearity … sometimes chosen[4]」與 [4] 的指向 | ✅ | ✅ 原文為 "…a one-sided potential function, sometimes chosen[4] as a power law nonlinearity of the form Φ_{K,α}"；參考文獻 [4] 確為 Rhaouti, Chaigne, Joly, JASA **105 (1999) 3545–3562** | ✅ |
| 3 | §2.3.2 Fletcher & Rossing §19.7 的「動態質量約 30%」引文 | ✅ 全書掃描取得 | ✅ **逐字相符** | ✅ 本文件正確指出書中未附出處 |
| 4 | §2.3.2 `f_max = 0.85/τc` 與衝擊譜法 | ✅ | ✅ 原文（p.548）："for an impulse having a shape given by sin² 2πt/τ, for example, f_max = 0.85/τ, where τ is the impulse duration (Bork, 1983b)"，並註明 (Kittelson, 1966; Morrow, 1957) | ✅ |
| 5 | §2.3.2 Bork (1983a/1983b) 的完整書目與「PTB Project 5267 未出版」 | ✅ | ✅ **逐字相符**（見下） | ✅ |
| 6 | §2.2 Fletcher & Rossing §20.6 / §20.9 的鑼音高滑移數字與機制 | ✅ | ✅ **逐字相符** | ✅ 本文件的「這是鑼面幾何非線性、不是槌具接觸非線性」辨正正確 |
| 7 | §2.3.1 Chaigne & Doutaut (1997) 的存在與卷期頁 | ✅ | ✅ JASA **101(1), 539–557 (1997)**，DOI 10.1121/1.418117；Bilbao et al. 參考文獻 [3] 亦獨立印證 | — |
| 8 | §2.2 Balinese gamelan gong POMA 56 論文的存在 | ✅ 確認存在（Harwood, Pavill & Shepherd, POMA 56(1) 035002） | — | ✅ 本文件標「僅摘要層級、列為待查」，稽核同意 |
| 9 | §2.3.3 第 3 點「B4 鋼琴槌氈 α = 2.3–3.0」內部交叉引用 | ✅ `docs/HAMMER_CONTACT_SOURCES.md` §2.1/§4 確載 α = 2.3 / 2.5 / 3.0 | ✅ | ✅ |
| 10 | §2.1/§2.2 對 `EXTERNAL_ANCHOR_SOURCES.md` §5.1 的引述 | ✅ 該檔 §5.1 確載舌鼓 ICSV27 2021（403）與銅鑼 JCIE 28(4) 2005（付費牆） | ✅ | ✅ |

**逐字比對明細（本次實際讀到的原文）**

- Bilbao et al. (2012), Figure 12 圖說原文：
  *"Force experienced by a mallet, of mass **0.028 kg**, and with stiffness parameters
  **K = 1.6×10⁸** and **α = 2.54**, striking a membrane under different velocities, as
  indicated. The membrane, of dimensions **0.6 × 0.6 m**, with **ρm = 0.26 kg/m²** and
  **Tm = 3325 N/m**, is struck at a location **0.1 m from a corner**."*
  → 本文件 §2.3.3 的七格表格**逐位相符，一個都沒錯**。論文第 7 節標題確為
  "The Mallet-Membrane Interaction"。
- Fletcher & Rossing §19.7（原書 p.547）原文：
  *"A mallet whose mass nearly equals the dynamic mass of the struck vibrator (typically
  about 30% of the total mass for a marimba bar in its fundamental mode) transfers the
  maximum amount of energy to the vibrator."*
  → 與本文件引文**逐字相同**；該句確實未附任何文獻引用（前一句只交叉引到本書
  Sections 2.9、12.4、12.5），本文件的但書成立。§19.7 起於 p.547、§19.8 起於 p.549，
  本文件標的 pp.547–549 正確。
- Fig. 19.12 原文描述：十支槌、槌頭速度軸 **0–3.5 m/s**、槌號 **S1 / S3 / S9 / S10 /
  S50 / S100**；S1 為全橡膠槌、曲線平坦；S10 為硬芯繞紗、可用音域**逾兩個八度**、
  適合木琴/鐵琴高音域；S9 為木芯配橡膠環（glockenspiel 用），弱擊時形變隨力度變、
  強擊時受硬芯限制。→ 本文件 §2.3.2 對這張圖的**文字描述全部正確**，且正確地
  拒絕從圖上讀任何數值。
- Bork 書目原文（原書 p.554 References）：
  *"Bork, I. (1983a). 'Zur Abstimmung und Kopplung von Schwingenden Stäben und
  Hohlraumresonatoren.' Dissertation, Tech. Univ. Carolo-Wilhelmina, Braunschweig."*
  *"Bork, I. (1983b). 'Entwicklung von akustischen Optimierungsverfahren für Stabspiele
  und Membraninstrumente.' PTB report, Project 5267, Braunschweig, Germany
  (unpublished)."*
  → 本文件的德文篇名、PTB、Project **5267**、**unpublished**、TU Braunschweig 博士論文，
  **全部逐字正確**。這是本次稽核中最「像是編的」但查證後完全屬實的一條。
- Fletcher & Rossing §20.9（原書 p.566）原文：
  *"The pitch of the larger gong glides downward as much as **three semitones** after
  striking, whereas that of the smaller gong glides upward by about **two semitones**. …
  The central section of the larger gong is nearly flat, and the **hardening spring**
  behavior, characteristic of flat plates, dominates. The central part of the smaller gong
  … is sufficiently convex to behave as a **spherical cap shell** that has **softening spring**
  behavior at large amplitude (Rossing and Fletcher, 1983; Fletcher, 1985)."*
  並明言此為 **Section 3.14** 板殼非線性的例子。§20.6 起於 p.561（歸因 Rossing and
  Fletcher, 1982）。→ 本文件 §2.2 的數字（3 個半音／2 個半音）、機制（大鑼 hardening、
  小鑼 softening）、章節頁碼（561／566）、§3.14 交叉引用、以及 Rossing & Fletcher
  (1982, 1983) + Fletcher (1985) 的歸因，**全部正確**，且該段確實完全未涉及槌頭接觸力學。

**小結：本文件所有「有數字」的引用（Bilbao 七格、F&R 的 30%、0.85/τc、3/2 個半音、
Bork 的 PTB 5267）全部為真且逐位/逐字相符。沒有任何一條是編造的。**
「寧缺勿假」的自律在本次抽查中站得住腳：本文件明確拒絕從 Fig. 19.12 讀值，
稽核確認那張圖在可取得的掃描件中確實無法可靠讀出逐點數值。

### 6.2 findings

**B1（輕微・引用位置誤標）：§2.3.3 把「大致對應一個典型的鼓的設定」說成是
「Figure 12 圖說原文」，實際上該句在正文 §7.2 Simulations，不在圖說裡。**
原文：*"In this section, the results of a simulation for a square membrane are shown,
corresponding roughly to a typical drum configuration."* Figure 12 的圖說本身只列參數、
不含這句。本文件據此得出的結論（這組數字未被作者聲明等於 Rhaouti et al. 1999 的
實測值，屬間接引用）**仍然成立**，只是出處位置標錯。

**B2（中等・書目錯誤）：§2.3.3 與 §4 把 Bilbao et al. 的卷期寫成
「Acta Acustica 98 (2012)」，正式出版資訊是 Acta Acustica united with Acustica
**101(1): 155–173, 2015**。**
本文件不算憑空捏造——arXiv:1405.2589 的預印本頁眉自己就印著
"ACTA ACUSTICA UNITED WITH ACUSTICA Vol. 98 (2012)"（投稿時的模板殘留，
文中另有 "Received 27 October 2012, accepted 6 December 2012"）。但本文件照抄了
預印本頁眉而未察覺它與正式出版卷期不符。**引用時應寫 101 (2015) 155–173，
或註明「引自 arXiv 預印本，其頁眉卷期與正式出版不符」。**

**B3（輕微・書目錯誤）：ISBN 978-0-387-94151-6 對應的是 Springer Study Edition
（1993 年印次），不是本文件標的 1991 年初版。** 出版者「Springer-Verlag New York」
與 1991 年份本身沒錯，但把 1991 與這組 ISBN 綁在一起不精確。章節、頁碼
（§19.7 pp.547–549、§20.6 p.561、§20.9 p.566）經核對與本次使用的掃描件一致。

**B4（結構・已補）：原檔頭缺「未經月月核准不得入 `materials.json`／程式碼」的聲明。**
原檔頭只有「草稿（draft），待 Opus 溯源稽核」與「不改任何程式碼、不改任何容差」。
稽核時已於檔頭補上明確的核准閘門聲明並標註出處。內容未動。
（對照組：`TAIWAN_WOOD_SPECIES_SOURCES.zh-TW.md` 檔頭原本就有完整聲明。）

**B5（風險提示・非錯誤）：§2.3.2 與 §2.2 所依據的
Fletcher & Rossing 全書「完整掃描版」是第三方個人網頁上的掃描件。**
本次稽核為求可重現，用的是同一份公開掃描件並確認內容一一相符，所以**內容查證是
紮實的**；但它不是權威版本，也可能隨時下架。若日後要把 `f_max = 0.85/τc` 寫進
程式註解或 GATE 依據，建議改引正式版本（Springer, DOI 10.1007/978-0-387-21603-4，
Chapter 19）作為書目。

### 6.3 誠實性檢查（任務第 2 項）

- ✅ **沒有任何一個數字是沒附出處就出現的。** 本文件出現的每個數值
  （0.028 kg、1.6×10⁸、2.54、0.26 kg/m²、3325 N/m、0.6 m、0.1 m、30%、0.85、
  3 個半音、2 個半音、2.3–3.0）都逐一標明了文件、章節/圖號，稽核逐條驗證通過。
- ✅ 拿不到全文的來源（Chaigne & Doutaut、Henrique & Antunes、Bork 原始報告、
  Rhaouti et al.、銅鑼 JCIE 2005、舌鼓 ICSV27 2021、POMA 56）**一律標「確認存在，
  全文未取得」，沒有從搜尋摘要轉引任何數字**——這正是 R4 要求的行為。
- ✅ §2.3.3 主動聲明「同一支槌具打膜與打樑/板 `K`/`α` 不變」是**本文件的推論而非
  任何文獻明講**，這種主動標示推論邊界的做法，稽核給予正面評價。
- ✅ §4 明確寫「沒有從任何論文圖表數位化取值」，並點名排除 Fig. 19.12——稽核確認
  屬實（本次亦無法從該圖讀出可信數值）。
- ✅ §2.3.3 第 3 點對 α=2.54 與鋼琴氈 2.3–3.0 的巧合，明確拒絕升格為「可借用」的
  證據，維持 `HAMMER_CONTACT_SOURCES.md` §6 的既有裁決——**沒有為了讓 D2 好看
  而放寬主張**，符合 R2/R3 精神。

### 6.4 剩餘風險

1. **「零命中」的宣稱本質上無法被證偽。** 本次稽核只能驗證「本文件說找到的東西
   確實存在且數字正確」，無法證明「舌鼓/鑼的槌具接觸量測真的不存在於全世界」。
   §2.1「連方法論文獻都沒找到」是**搜尋結果的陳述，不是文獻不存在的證明**——
   §3 缺口清單用 `[ ]` 未勾選來表達這點是恰當的，但讀者不應把它讀成蓋棺論定。
2. B2 的卷期錯誤若被複製到程式碼註解或後續文件會擴散，建議在採用前先改正。
3. §5 建議 1（優先調 Chaigne & Doutaut 1997 全文）在稽核看來是正確的排序：該文
   確為唯一明確對「槌具打**樑類**振動體」做 Hertz 冪律建模的公開論文，力學機制
   與 Chromatic 舌片最接近。§5 建議 2（調 Bork 1983a 學位論文）本文件已自行標明
   「未實際嘗試、純屬猜測性建議」，稽核同意保留此標示。
4. Bilbao 那組 `K`/`α` 即使力學機制可接受，仍是**間接引用**（作者未聲明它等於
   Rhaouti et al. 1999 的實測值）。本文件已誠實標示，**任何情況下都不得升格為
   一手實測值使用**。

**稽核結論：本文件的「引用是否編造」＝否。所有有數字的引用逐位/逐字屬實，
「找不到」的宣稱沒有誇大也沒有縮小，誠實性檢查全數通過。三個 findings（B1/B2/B3）
都是書目層級的精確度問題，不影響任何實質主張。
§5「D2 不能關閉、Chromatic 維持現行 proxy」的結論，稽核**同意**。**

---

## 7. 修正記錄（2026-08-28，回應 §6 全部 findings）

> 本節記錄針對 §6 findings 的實際修正動作。§6（稽核記錄本身）維持不動，
> 作為歷史紀錄；本節之後 §0–§5 的內容才是目前的正確版本。B4 已在稽核
> 當下於檔頭直接補上核准聲明（見檔頭與 §6 finding B4），不在此重複。

| Finding | 修正內容 | 位置 |
|---|---|---|
| B1 | 更正「大致對應一個典型的鼓的設定」一句的出處：不是 Figure 12 圖說，而是正文 §7.2 Simulations；圖說本身只列參數。原本「間接引用、非一手實測」的結論保留不變。 | §2.3.3 |
| B2 | 卷期由「Acta Acustica 98 (2012)」改為正式出版「Acta Acustica united with Acustica 101(1): 155–173 (2015)」，並註明 arXiv 預印本頁眉本身印著「Vol. 98 (2012)」投稿模板殘留字樣，不是本文件憑空捏造，只是照抄未察覺與正式出版不符。 | §2.3.3、§4 引用清單 |
| B3 | 註明 ISBN 978-0-387-94151-6 實際對應 1993 年 Springer Study Edition 印次，不是本文件先前標的 1991 年初版；出版者與 1991 年份本身沒錯，只是不該與這組 ISBN 綁在一起。章節/頁碼與本次使用的掃描件核對一致，不受影響。 | §2.2、§2.3.2 |

**未修正、刻意保留的項目**（非疏漏，是誠實邊界）：B5（Fletcher & Rossing
掃描版屬第三方個人網頁掃描件的風險提示）屬「風險提示・非錯誤」，本文件
內容已與該掃描件逐字核對一致，不需修改內文，僅供未來若要寫入程式註解時
改引正式版本（DOI 10.1007/978-0-387-21603-4）的參考，維持在 §6 記錄即可。
