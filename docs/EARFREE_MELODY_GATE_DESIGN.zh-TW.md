# 免耳・免人工驗證設計：旋律位置三層 GATE（提案，待月月裁決）

> 起草：2026-08-20。狀態：**設計提案，未實作、未 commit（R7）**。
> 專案終極主張：「聾人與 AI 都可以按照邏輯輸出正確的旋律位置」。
> 本文件把這句話變成可以用命令輸出判定（R1）、不需要任何人耳或人手的 GATE 鏈。

---

## 0. 主張與邊界

**要證明的主張**：`score.json` 宣告的每一個事件 `(time, pitch)`，在最終渲染的
WAV 裡於宣告的時間點、以宣告的音高實際響起——逐事件、可判定、fail-closed。

**刻意不在範圍內**：好不好聽（美學）、混音品味、音色主觀評價。這些本來就
不屬於物理主張，不假裝能自動化。

**為什麼現有 GATE 還不夠**（缺口分析，2026-08-20 核實）：

| 現有工具 | 驗的是 | 缺什麼 |
|---|---|---|
| `verify_score.py` 2c | 休止段是安靜的（**負向**） | 沒驗「音在宣告位置**真的響**」（**正向**）。把整首曲子每個音都往後挪 200 ms，只要休止段判定剛好還過，2a–2e 全綠——**旋律位置錯了但 GATE 不知道** |
| `physics_verify.py` | 單音 probe 的 f0/T60/振幅 | 不看整首曲、不看時間軸 |
| `tuner_audit*` | 音高 | 不看時間軸 |
| pluginval L10 / VST3 validator | plugin 合約行為 | **不看音訊內容**——plugin 即時路徑（`CimbalomVoice` 走 APVTS）從來沒有人驗過它輸出的旋律位置，corpus 73 檔全部只走 CLI 的 `ScoreRenderer` 路徑 |
| A9 Cubase 四步 | host 整合 | 目前定義為**人工**，是主張鏈裡唯一剩下的人類環節 |

三層設計把這些缺口依序關掉。

---

## 1. L1：旋律位置驗證器 `tools/melody_verify.py`（新工具）

**輸入**：`score.json` + 渲染 WAV（來源不限——CLI 渲染、L2 harness 渲染、
L3 Cubase 匯出，同一支驗證器通吃；這是三層共用同一判定的關鍵）。

**每事件檢查**：

1. **Onset**：期望值 = `ev.time`（`ScoreRenderer.h:640` 是 sample-exact 的
   `startSample = ev.time * sr`，所以期望值沒有模糊空間）。
   量測 = 在期望 f0 ±3% 窄帶（repo 既有慣例）取 Hilbert envelope，
   在 `[t_i − W, t_i + W]` 搜尋窗內找第一次持續越過
   `噪音底 + Δ dB` 的時刻。
2. **Pitch**：量測 = 該窄帶起音後前 N ms 的頻譜質心；判定沿用
   **已批准的 5-cent course-centroid gate**（2026-07-23 月月核准，直接複用
   `verify_score.py` 的 `course_f0()` 基礎設施，不另立第二套音高判定）。
3. **缺音**：搜尋窗內無越過 → 該事件 FAIL。
4. **多餘音／錯位音**：該窄帶在**非宣告位置**出現獨立 onset → FAIL。
   （這一項就是抓「旋律位置錯了」的正向檢查。）

**Fail-closed 拒答規則**（沿用 C2 哲學：不能可靠判定就拒答，不猜）：
- 兩個並發事件的 ±3% 帶重疊且時間重疊 → 該對事件標 `UNVERIFIED`，
  列名回報，不算 PASS。
- 窄帶 SNR 低於可判定門檻 → `UNVERIFIED`。

**容差來源（R4）**：
- Pitch：5 cents——已批准，零新常數。
- Onset：**提案 ±10 ms**，推導 = 分析 hop（256 samples @ 44.1 kHz ≈ 5.8 ms）
  + 激發攻擊窗 τc（毫秒級，`HammerImpulse::tauCForNote`）。
  依 repo 慣例（M5 damping.alpha、C3 跨平台容差同款流程）：
  **先以 informational 上線印數字 → 月月看過實測分布 → 批准後轉阻斷式**。
  不批准前不擋任何東西。

**哨兵反例（驗證器自己也要被驗，repo 慣例）**：四個 fixture 必須 FAIL——
(i) 單音時移 +100 ms；(ii) 移調 +1 半音；(iii) 刪掉一個音；(iv) 多插一個音。
四個都 FAIL 驗證器才算活著。加一個 (v) 原封不動 fixture 必須 PASS。

---

## 2. L2：plugin 即時路徑 harness `TsukiSynthHostProbe`（新 CMake target）

一個 JUCE console app，用 `juce::VST3PluginFormat` **從磁碟載入建置產物
`TsukiSynth.vst3`**——跟 Cubase 載的是同一顆二進位檔，不是 link 進來的原始碼。
把 A9 四步全部變成命令輸出判定：

| A9 人工步驟 | HostProbe 自動化對應 | 判定 |
|---|---|---|
| host 掃描辨識 | FormatManager 掃描並實體化，核對名稱/參數清單 | exit code |
| MIDI in 實彈出聲 | 把 fixture 旋律轉成 sample-accurate `MidiBuffer`，`processBlock` 串流（44.1k/48k × block {64…1024}），寫 WAV → **跑 L1** | L1 exit code |
| automation lane 回放 | 串流中程式化 ramp 參數（例 `fx_eq_gain` 0→+6 dB），驗頻帶能量差 ≈ 預測值；同 automation 渲染兩次 → SHA256 一致 | 數字 + 位元 |
| 專案存讀 state | `getStateInformation` → 新實例 `setStateInformation` → 同 MIDI 重渲染 → **WAV 位元一致** | SHA256 |

這同時關掉「plugin 即時路徑從未被音訊內容驗證」的缺口——
**這缺口跟 A9 無關也存在**，X1 的四處 fail-closed 守衛之一
（`CimbalomEngine.h:133`）就在這條路徑上，目前只有 pluginval 間接碰到它。

**誠實標註**：JUCE host ≠ Cubase host。L2 證明的是 VST3 合約下的功能行為；
Cubase 專屬行為留給 L3。兩者主張分開寫，不混。

---

## 3. L3：Cubase 本尊（AI 執行，免月月動手）

本機已裝 Cubase LE AI Elements 12。分兩段，證據力不同：

**3a. host 掃描——今天就能關，純文字證據**：
Cubase 的掃描快取是可解析的 XML：
`%APPDATA%\Steinberg\Cubase LE AI Elements 12_64\Cubase AI VST3 Cache\vst3plugins.xml`。
**2026-08-20 已核實：TsukiSynth 在 `vst3plugins.xml` 內、`vst3blacklist.xml` 零筆。**
寫一支 `tools/cubase_scan_verify.py` 解析這兩個檔 + 比對 .vst3 檔案 mtime
（確認快取不是舊產物的殘影），輸出 PASS/FAIL。不用開 GUI、不用截圖、不用眼睛。

**3b. MIDI 回放 + automation + 存讀——AI 開 Cubase 操作**：
computer-use 連接器可用時，AI 自己開 Cubase：建 instrument track → 匯入
fixture MIDI 檔（用「匯入」而非虛擬 MIDI 線材，可重現性高、不需 loopMIDI）→
畫 automation → File > Export > Audio Mixdown 出 WAV → 存專案、關掉、重開、
再匯出一次。**負重判定永遠是命令輸出**：匯出的 WAV 跑 L1（旋律位置）+
兩次匯出互比（state 還原）。截圖只當過程紀錄，不當驗收依據（R1）。
（註：computer-use 連接器本 session 目前斷線，3b 待連接器恢復；3a 與 L1/L2
完全不依賴它。）

---

## 4. 聾人可讀證據：report_html.py 加 piano-roll 疊圖

L1 每次跑完，在既有 HTML 報告加一個面板：頻譜圖上疊「期望音符框」
（score.json 的 time×pitch 方塊）與「量測 onset 標記」，PASS 綠框、FAIL 紅框、
UNVERIFIED 灰框。這是「聾人可以按照邏輯**看見**旋律位置正確」的最後一哩——
主張鏈從頭到尾不經過任何人的耳朵。

---

## 5. 需要月月裁決的點（依 repo 規則，AI 不自己定）

1. **Onset 容差 ±10 ms**：informational 期看過實測分布後批准轉阻斷（同 C3 流程）。
2. **A9 GATE 重定義**：把 M8-8a「Cubase 人工四步」改成「L2 自動化四步（阻斷式）
   + L3 Cubase 實測（3a 阻斷式、3b AI 執行）」。這是改 GATE 定義，
   雖然方向是**加嚴**（多了音訊內容驗證，原人工版只看「有聲音」），仍需明示核准。
3. **實作順序**：本設計 vs X2（macOS Bessel）誰先。建議 X2 先（紅燈優先），
   L1 次之（工作量最小、立即補上「旋律位置」正向檢查的缺口）。

## 6. 建議實作順序與規模

1. **L1 + 哨兵五件組**（一支 Python 工具 + fixtures，最小可用主張）
2. **3a Cubase 快取驗證器**（半天級，立即把 A9 削掉一步）
3. **L2 HostProbe**（新 CMake target，工作量最大；GATE 段落寫進施工卡時
   必含 X4 規約：先全 target 重建再 ctest）
4. **4 piano-roll 疊圖**（L1 落地後的報告層）
5. **3b Cubase GUI 實測**（等 computer-use 連接器）

---

## 7. 實測後的方法極限（v1，2026-08-21 月光全曲 1141 事件四輪迭代）

L1 對月光（sustain-pedal 織體、reverb 5.8s、大量同音重擊與低音）的四輪結果：

| 輪 | 規則 | PASS / FAIL / UNVERIFIED |
|---|---|---|
| v1 | 基本 | 100 / 1043 / 0 |
| v2 | +Ra/Rb/Rc（乾聲 T60） | 2 / 651 / 489 |
| v3 | +有效殘響=max(T60, reverb) | 2 / 322 / 818 |
| v4 | +Rd 床能量/Re 低頻極限/Rc' course 自拍 | 2 / 38 / 1102 |

**v4 殘餘 38 FAIL + 63 extra 的定性（已定位、暫不再修）**：
- pitch −6.5~−12c，集中低音區（69/98/104/165 Hz），同音高偏差穩定 ±0.5c =
  **確定性量測偏差**：1.25s Hann 主瓣 3.2 Hz，強鄰近低音的頻譜裙擺帶外滲入
  拉低弱基頻質心。單音 probe 已由 physics_verify 驗到 0.05c → 渲染端無此偏差。
- extra rises 集中 55–138 Hz 帶：低音長尾與混響的交互調變，Rc' 的
  單 course 自拍規則覆蓋不到跨事件×混響的組合。

**結論（v1 主張域，R2：不為過單曲而加寬任何容差）**：
- **強域**：單音/稀疏織體、L2 HostProbe 渲染、無延遲效果的 fixture——
  哨兵五件組 + 對照組全綠，onset 精度 ~1ms、pitch ~1c。
- **弱域**：密集低音複音 + 長混響——大部分事件誠實拒答（v4 = 96.6% UNVERIFIED），
  可判定子集全部通過。此類曲目的位置保證來自 CLI 渲染的位元決定性
  （verify_score 2e），不來自 L1。
- 若未來要把弱域轉強：路線是「score-informed 合成模板匹配」（用 dump-modes
  的完整模態集合成每事件的預期波形做匹配濾波），工作量大，價值待 B2 後評估。

---

## 8. 分軌法實測後的主張域更新（v2，2026-08-30 給愛麗絲全曲 905 事件）

§7 的 v1 主張域說「密集低音複音 + 長混響」是弱域，位置保證只能靠 verify_score 的
位元決定性。2026-08-30 月月裁定走裁決包
`reports/decision_packets/POLYPHONIC_VERIFICATION_OPTIONS.zh-TW.md` 的**選項 A**
（逐事件乾聲分軌 + 線性疊加證明，工具 `tools/stem_verify.py`），實測結果如下，
**弱域被部分轉強，但轉強的邊界必須寫清楚**。

### 8.1 實測數字（給愛麗絲全曲，證據：`reports/gate_outputs/stem_verify_fur_elise_run.txt`）

| 做法 | PASS | FAIL | UNVERIFIED |
|---|---:|---:|---:|
| 整首一起判（L1 原路徑） | 30 | 14 | 862（95.2%） |
| 逐事件分軌（帶殘響） | 595 | 122 | 188 |
| **逐事件分軌（乾聲）** | **671** | **22** | **212** |

疊加證明 ESTABLISHED：905 軌相加 vs 成品混音殘差 −118.60 dBFS（門檻 −85 dBFS）。
=> **「逐軌驗過」可在數學上轉移到成品**，這是選項 A 的立論基礎，成立。

### 8.2 主張必須拆成兩個維度（月月 2026-08-30 查核裁定）

**不可**把音高與起音壓成單一 verdict 再報總數——那會把「音高已量到、起音沒量到」
的事件誤看成完全沒驗。正確的主張形式：

| 維度 | 乾聲全曲結果 |
|---|---|
| **音高** | 883/905 取得量測，**883/883 全在 ±5 cents 內，最大 \|偏差\| 2.4266 c** |
| **起音** | 671/905 取得精測，全在 ±10 ms 內，最大 \|偏差\| 6.9272 ms（帶殘響版 7.0522 ms） |
| 起音拒答 | 212 顆，全部 f0 < 167 Hz（Re 低頻頻帶解析度極限） |
| 起音 FAIL | 22 顆高音，基頻帶未出現足夠 rise——**不可據此宣稱音高錯** |

### 8.3 新確認的量測偏差機制：殘響對頻帶質心的著色

§7 v1 在月光上觀察到「pitch −6.5~−12c、同音高偏差穩定 ±0.5c 的**確定性量測偏差**」，
當時歸因於「強鄰近低音的頻譜裙擺外滲」。分軌實測提供了新證據：

**在單音分軌裡（根本沒有鄰近音）同樣出現此偏差**，且開/關殘響即可開關它：

| 同一顆 E4（idx 13） | melody_verify 判定 |
|---|---|
| 帶殘響 | −9.48 cents → FAIL |
| 乾聲 | −0.02 cents → PASS |

獨立量測（1 s 穩態段、2^22 點補零 FFT、拋物線內插）：E4 實際 −0.03 c、A#2 +0.00 c
（渲染端無偏差，與 §7 「單音 probe 驗到 0.05c」一致）。
用**相同的質心公式、相同的 ±3% 頻帶**但高解析度重算，E4 質心 = −0.02 c
→ 不是質心慣例本身的問題，是**低解析度質心在被殘響梳狀著色的窄帶上被拉偏**。

**結論**：`melody_verify.py:487` 的頻帶質心法對「窄帶內非平坦的頻譜著色」不穩健。
鄰近音裙擺（v1 歸因）與殘響梳狀響應（v2 新增）是同一類機制的兩個來源。
帶殘響 score 的音高判定因此帶有最多 ~9.5 cents 的系統偏差，而容差僅 5 cents。
**這個缺陷本來就在現行 L1 GATE 內，不是分軌法引入的**；以往密集段幾乎全拒答故未浮現。

=> **主張域規則（新）**：L1 的音高判定**只在乾聲訊號上有效**。
帶殘響訊號的音高數字不得作為 GATE 依據。（本次未修改 melody_verify，R2。）

### 8.4 尚未驗證、不得宣稱的事

1. **泛音（partials）完全沒有實測。** `stem_verify` 只用 `--dump-modes` 的 partials
   **預判**「別顆音的 partial 是否污染基頻帶」，從未量測任何 partial 的頻率或振幅。
   **不可**宣稱「泛音已驗證」。
2. **±5 cents 是本專案既有裁定的產品門檻，不是 ISO 或業界通用標準。**
   容差本次未動；但量測器本身應先用合成哨兵證明自身誤差 ≤1 cent，
   才有資格執行 ±5 cents 的產品 GATE（月月 2026-08-30 查核第 5 點）。
3. **22 顆高音的性質未定。** 乾聲單音實測（piano 引擎、velocity 0.427/0.462）：
   - G5（宣告 784.0 Hz）：整軌峰值 −46.7 dBFS，主導頻率 1571.5 Hz（第二 partial，
     比值 2.0044），宣告基頻處能量比峰值低 21.9 dB
   - G6（宣告 1568.0 Hz）：峰值 −54.5 dBFS，主導 3214.9 Hz（比值 2.0503），基頻低 24.0 dB
   - D7（宣告 2349.3 Hz）：峰值 −64.5 dBFS，主導即基頻（+4.7 c）——屬「整體太安靜」
   比值大於 2 的方向與 stiffness inharmonicity 一致（partial 被推高）。
   真鋼琴高音區基頻本來就弱，**因此這未必是引擎缺陷**；同時也說明
   「只在 ±3% 基頻窄帶找 rise」的問法對這類音天生答不出來。
   正解方向（月月 2026-08-30 指示）：改用 harmonic-aware 判定
   （`f_n = n·F0·√(1+B·n²)`，或直接驗 `--dump-modes` 預測的逐 partial 頻率），
   `B` 的物理合理性須另用獨立公式／參考琴資料查證（R4）。
4. **可發布措辭（月月核定）**：
   「給愛麗絲 score、模態表、渲染決定性、逐軌疊加已驗；乾聲 883 顆有音高證據，
   其中 671 顆另有起音證據」。
   **不可**寫成「905 顆音高與泛音全部驗過」。

### 8.5 v2 主張域總結

- **強域（擴大）**：單音/稀疏織體、**以及任何可分軌的乾聲密集複音**
  （分軌把「音互相遮蔽」消除，但不改變判定慣例本身的能力）。
- **弱域（縮小但仍存在）**：
  (a) f0 < 167 Hz 的起音精測（頻帶解析度極限，212 顆）；
  (b) 基頻天生弱的高音（22 顆）——需 harmonic-aware 判定才有解；
  (c) 任何帶殘響訊號的音高判定（§8.3）。
- **仍不在主張範圍內**：泛音的頻率與振幅、以及一切美學/聽感主張。
