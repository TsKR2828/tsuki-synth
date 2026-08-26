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
