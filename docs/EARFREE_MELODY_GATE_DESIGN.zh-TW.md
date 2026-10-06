# 免耳・免人工驗證設計：旋律位置三層 GATE（~~提案，待月月裁決~~ 起草時是提案；L1／L2／L3 已實作並在用，見檔尾 2026-10-03 現況）

> 起草：2026-08-20。狀態：**設計提案，未實作、未 commit（R7）**（2026-08-20 起草當時；之後 L1 `melody_verify`、L2 HostProbe、L3 Cubase 實測都已實作入庫，見檔尾）。
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
| v5（C10B **原始回合**，2026-09-09，見 §9） | 同 v4 規則，僅 pitch 估計器換成邊緣柔化質心——**該估計器已於 C10B 修正回合撤回，此列數字已不代表現況，僅存檔** | 8 / 14 / 1121（已撤回，見 §9.5） |
| v4（C10B **修正回合重驗**，2026-09-09，現況） | 同 v4 規則，估計器＝撤回後與 `measure_pitch_cents_legacy()` 位元組相同 | 2 / 40 / 1101 |

**v4 殘餘 38 FAIL + 63 extra 的定性（已定位、暫不再修）**：
- pitch −6.5~−12c，集中低音區（69/98/104/165 Hz），同音高偏差穩定 ±0.5c =
  **確定性量測偏差**：1.25s Hann 主瓣 3.2 Hz，強鄰近低音的頻譜裙擺帶外滲入
  拉低弱基頻質心。單音 probe 已由 physics_verify 驗到 0.05c → 渲染端無此偏差。
- extra rises 集中 55–138 Hz 帶：低音長尾與混響的交互調變，Rc' 的
  單 course 自拍規則覆蓋不到跨事件×混響的組合。

**v5（C10B 原始回合，已撤回，證據：`reports/gate_outputs/wf0909_C10B_estimator.txt` item 5）**：
v4 的 2/38/1102 是 2026-08-21 那次程式碼狀態量到的數字；2026-09-09
用「同一份 v4 規則、換成 §9.4 的柔化質心估計器」重量前，先用**未動過的舊估計器**在
當天的程式碼上重跑一次拿到 2/40/1101（與 2026-08-21 的 2/38/1102 只差 2，
差異來自這之間其他工作卡對拒答規則的微調，與本節/C10B 無關），再換上柔化質心估計器
一度測得 8/14/1121：「6 顆 FAIL→PASS、0 顆 PASS→FAIL」。**該柔化質心估計器已於
C10B 修正回合被稽核抓到結構性缺陷並撤回（見 §9.5）**，8/14/1121 這組數字與
「6 顆 FAIL→PASS」的說明僅為歷史記錄，不代表現況。**現況（估計器撤回後，
與未動過的舊估計器一致）＝上表 2/40/1101**，月光仍是 §7 定義的弱域、
informational，不當 GATE。

**結論（v1 主張域，R2：不為過單曲而加寬任何容差）**：
- **強域**：單音/稀疏織體、L2 HostProbe 渲染、無延遲效果的 fixture——
  哨兵五件組 + 對照組全綠，onset 精度 ~1ms、pitch ~1c。
- **弱域**：密集低音複音 + 長混響——大部分事件誠實拒答（v4 = 96.6% UNVERIFIED），
  可判定子集全部通過。此類曲目的位置保證來自 CLI 渲染的位元決定性
  （verify_score 2e），不來自 L1。
- 若未來要把弱域轉強：路線是「score-informed 合成模板匹配」（用 dump-modes
  的完整模態集合成每事件的預期波形做匹配濾波），工作量大，價值待 B2 後評估。

**L2 補充（WF0907-E10，2026-09-08）**：H6（可變 host block size）與 H7
（user preset round-trip）詳見 §10。一句話版：H6 全綠（哨兵旋律 5 個 block
size 位元相同，見 §10.1）；H7 因架構衝突未實作，待月月裁決（§10.2）。（→ 2026-09-09 已依裁決落地選 (B)，見 §10.2）

---

## 8. 分軌法實測後的主張域更新（v2，2026-08-30 給愛麗絲全曲 905 事件）

§7 的 v1 主張域說「密集低音複音 + 長混響」是弱域，位置保證只能靠 verify_score 的
位元決定性。2026-08-30 月月裁定走裁決包
`reports/decision_packets/POLYPHONIC_VERIFICATION_OPTIONS.zh-TW.md` 的**選項 A**
（逐事件乾聲分軌 + 線性疊加證明，工具 `tools/stem_verify.py`），實測結果如下，
**弱域被部分轉強，但轉強的邊界必須寫清楚**。

### 8.1 實測數字（給愛麗絲全曲，證據：`reports/gate_outputs/stem_verify_fur_elise_run.txt`；A14 之後的乾聲重測：`reports/gate_outputs/wf0925_V1_partial_stem_verify_full.txt`）

| 做法 | PASS | FAIL | UNVERIFIED |
|---|---:|---:|---:|
| 整首一起判（L1 原路徑） | 30 | 14 | 862（95.2%） |
| 逐事件分軌（帶殘響） | 595 | 122 | 188 |
| **逐事件分軌（乾聲）** | **677** | **16** | **212** |

（2026-09-25 更新：乾聲列原為 08-30 的 671／22／212。A14 B-2（月月 2026-09-10 放行）之後實測是
677／16／212：09-14 WF0914-D14 全量與 09-25 WF0925-V1 全量逐顆相同，判定 0 顆不同，證據
`reports/gate_outputs/wf0925_V1_partial_stem_verify_full.txt`。前兩列是 08-30 帶殘響那次的數字，
09-25 沒有重跑，保留作歷史。）

疊加證明 ESTABLISHED：905 軌相加 vs 成品混音殘差 −119.42 dBFS（門檻 −85 dBFS；2026-09-25
WF0925-V1 乾聲全量實測，08-30 A14 之前是 −118.60 dBFS）。
=> **「逐軌驗過」可在數學上轉移到成品**，這是選項 A 的立論基礎，成立。

**C10B 重驗（2026-09-09，§9 換估計器後；當時還在 A14 之前）**：`671 / 22 / 212` 這組數字逐顆
**100% 維持不變**（同一 905 顆事件，新舊估計器判定完全相同，見
`reports/gate_outputs/wf0909_C10B_estimator.txt` item 4）——換句話說本節的
主張域結論不受估計器改善影響，可以繼續引用。

### 8.2 主張必須拆成兩個維度（月月 2026-08-30 查核裁定）

**不可**把音高與起音壓成單一 verdict 再報總數——那會把「音高已量到、起音沒量到」
的事件誤看成完全沒驗。正確的主張形式：

| 維度 | 乾聲全曲結果 |
|---|---|
| **音高** | 889/905 取得量測，**889/889 全在 ±5 cents 內，最大 \|偏差\| 3.0355 c**（2026-09-25 WF0925-V1；08-30 A14 之前是 883/883、最大 2.4266 c） |
| **起音** | 677/905 取得精測，全在 ±10 ms 內，最大 \|偏差\| 6.9272 ms（2026-09-25 WF0925-V1；08-30 A14 之前是 671/905、最大同為 6.9272 ms；帶殘響版 7.0522 ms 是 08-30 的數字） |
| 起音拒答 | 212 顆，全部 f0 < 167 Hz（Re 低頻頻帶解析度極限；09-25 重測相同） |
| 起音 FAIL | 16 顆（D16：E5@0.278×9、A5@0.427×3、A5@0.452×1、A6@0.427×2、A#6@0.427×1），基頻帶近乎無聲、未出現足夠 rise——**不可據此宣稱音高錯**。成因見 N1 零點地圖 `reports/weak_fundamental_null_map_2026-09-25.zh-TW.md`（16/16 的基頻落在槌力脈衝頻譜的零點）；這 16 顆用泛音反推基頻 16/16 在 ±5 c 內（informational，`reports/partial_verify_full_2026-09-25.zh-TW.md` §4）。08-30 A14 之前是另一批 22 顆高音（G5×19、D7、G6、F#6），09-25 已全部 PASS |

**C10B 原始回合重驗（2026-09-09，A14 之前，已撤回，僅存檔）**：換上 §9.4 的柔化質心估計器後，
883/905 取得量測、883/883 全在 ±5 cents 內兩個計數都不變；最大 \|偏差\| 一度從
2.4266 c 測得 **1.1217 c**（見 `reports/gate_outputs/wf0909_C10B_estimator.txt`
item 4）。**該估計器已於 C10B 修正回合撤回（見 §9.5）：柔化漸層以期望值為中心，
真值離期望值越遠柔化壓得越低，會系統性把偏差往小報，1.1217 c 這個「更準」的
讀數正是這個缺陷的產物，不代表估計器真的更準。現況（估計器＝撤回後與
`measure_pitch_cents_legacy()` 位元組相同）＝原始的最大 \|偏差\| 2.4266 c 不變（這是 A14 之前的數字；
A14 之後用同一個估計器實測是 3.0355 c，見上表）。**

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
   （2026-09-25 註：這一點寫於 08-30。之後 `tools/partial_verify.py`（informational、`gate_ready=false`）
   已實測 partial 頻率，09-25 第一次跑完全曲 905 顆，見 §8.6「全曲 905 顆已執行」段；振幅仍只記錄、
   不判定，「泛音已驗證」仍不可宣稱。）
2. **±5 cents 是本專案既有裁定的產品門檻，不是 ISO 或業界通用標準。**
   容差本次未動；但量測器本身應先用合成哨兵證明自身誤差 ≤1 cent，
   才有資格執行 ±5 cents 的產品 GATE（月月 2026-08-30 查核第 5 點）。
3. **弱基頻音的性質（2026-09-25 更新）。** A14 之後的起音 FAIL 是 D16 的 16 顆
   （E5@0.278×9、A5@0.427×3、A5@0.452×1、A6@0.427×2、A#6@0.427×1）。N1 零點地圖
   （`reports/weak_fundamental_null_map_2026-09-25.zh-TW.md` §0）已查明：16/16 的基頻都落在
   槌力脈衝頻譜的零點（凹口）裡，被額外壓掉 14.9～24.5 dB；另有 31 顆也在凹口內但仍 PASS，
   所以凹口是必要條件、不是充分條件，真正分開 PASS／FAIL 的是基頻的絕對音量
   （FAIL ≤ −72.1、PASS ≥ −67.2 dBFS，對照既有的 −70 dBFS 門檻；描述用、非 GATE）。
   這 16 顆用泛音反推基頻 16/16 在 ±5 c 內（informational，`reports/partial_verify_full_2026-09-25.zh-TW.md` §4）。
   怎麼處理~~待月月裁決~~（`reports/decision_packets/WF0925_open_decisions.zh-TW.md` Q15）→ **2026-10-02 月月裁 Q15＝A**：母帶不動，16 顆時間點交聽人（Q28）；D16 物理缺口仍開放。
   以下是 08-30（A14 之前）那 22 顆高音的原始記錄，保留作歷史——這 22 顆 09-25 已全部 PASS
   （`reports/partial_verify_full_2026-09-25.zh-TW.md` §5）。當時的乾聲單音實測（piano 引擎、velocity 0.427/0.462）：
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
   （註：句中 883/671 的最新實測為 889/677（2026-09-25），措辭是否隨之更新待月月重新核定。
   證據 `reports/gate_outputs/wf0925_V1_partial_stem_verify_full.txt`。）
   **不可**寫成「905 顆音高與泛音全部驗過」。
5. **不可宣稱量測器 ≤1 cent**（月月 2026-09-10 裁決選 A 後新增）。
   `measure_pitch_cents()` 在合成哨兵上的最大誤差是 1.1721 cent（開發網格）／
   1.0840 cent（hold-out 網格），兩者都大於 item 2 那條 ≤1 cent 的線。
   **不可**寫任何等同於「量測器自身誤差已進入 1 cent 以內」或「自證通過」的措辭；
   可寫的是「量測器自身系統誤差 ≤1.18 cent，未達 ≤1 cent 門檻，為已知並接受的上限」。
   相關的增益軸限制（真值偏離期望值時量測器會吸收部分走音）見 §8.5 與
   `reports/decision_packets/C10_selfcal_domain.zh-TW.md` §6/§7。

### 8.5 v2 主張域總結

- **強域（擴大）**：單音/稀疏織體、**以及任何可分軌的乾聲密集複音**
  （分軌把「音互相遮蔽」消除，但不改變判定慣例本身的能力）。
- **弱域（縮小但仍存在）**：
  (a) f0 < 167 Hz 的起音精測（頻帶解析度極限，212 顆）；
  (b) 基頻被壓得很弱的音——需 harmonic-aware 判定才有解。08-30 寫作時是 22 顆高音（G5×19、D7、G6、F#6，
  09-25 已全部 PASS）；A14 之後換成 D16 的 16 顆，成因是基頻落在槌力脈衝頻譜的零點
  （`reports/weak_fundamental_null_map_2026-09-25.zh-TW.md`），這 16 顆用泛音反推基頻 16/16 在 ±5 c 內
  （informational，`reports/partial_verify_full_2026-09-25.zh-TW.md` §4）；
  (c) 任何帶殘響訊號的音高判定（§8.3）。
- **仍不在主張範圍內**：泛音的頻率與振幅、以及一切美學/聽感主張。
- **量測器自身誤差（月月 2026-09-10 裁決選 A 落地）**：音高判定含量測器自身
  系統誤差 ≤1.18 cent（開發網格 1.1721 / hold-out 1.0840，
  `tools/measurement_selfcal.py`）；±5 cent 產品門檻不變，安全係數約 4.3×；
  量測器**未**通過 ≤1 cent 自證，此為月月 2026-09-10 裁決接受的已知上限。
  因此本專案**不宣稱**量測器通過自證；GATE 的有效主張是
  「渲染音高與宣告音高的差，在計入量測器自身 ~1.2 cent 的系統誤差後，
  仍落在 ±5 cent 內」。**任何量到 3.8–5.0 cent 之間的數字，都不得單獨用來
  斷言渲染正確或錯誤**——那個區間裡量測器誤差與渲染誤差不可分辨。
  另外，量測器在「期望值固定、真值另外偏離」這條增益軸上的缺口更大
  （MIDI 37，+40 cent 的真實走音只量到 +23.14 cent，誤差 16.86 cent），
  所以**低音區實質可偵測的走音下限比 ±5 cent 寬**，低音密集段落尤其要留意。
  數字出處：§9.1–§9.6 與 `reports/gate_outputs/wf0910_C10A_landing.txt`；
  裁決記錄見 §9.7 與 `reports/decision_packets/C10_selfcal_domain.zh-TW.md` §7。
  **主張域再收窄（月月 2026-09-15 裁決 D15 選 A' 落地）**：上述「≤1.18 cent」
  **只涵蓋持續段（單一指數衰減）語料，不含放鍵/阻尼段**。WF0914-D15 補上
  放鍵/阻尼段合成語料（衰減率突變，`release_factor` 0.002/0.05/0.08 取自引擎
  `damp()` 實際呼叫值）後，量測器在該類語料上的自證誤差實測為
  **5.2304 cent（開發網格）／7.2055 cent（hold-out 網格）**，最差集中在
  MIDI 37 附近（既有 f0 < 167 Hz 弱域的延伸）；持續段分項數字不變
  （1.1721 / 1.0840，逐位元同舊記錄）。因此**放鍵/阻尼段的音高判定不得
  引用 ≤1.18 cent 的主張**，其已知誤差上界為 ~7.2 cent；放鍵段的
  「期望值固定、真值偏離」正控制（注入 ±3.0 c 量得 +2.13／−2.43 c）證明
  哨兵確實在量測訊號而非讀標稱。B' 路線（為放鍵段另找估計器）不追——
  持續段家族六候選已全數否決，放鍵段是全新訊號模型盲點、成本未知。
  數字出處：`reports/gate_outputs/wf0914_D15_gate1_*.txt`。

**JSON 欄位補記（WF0907-C11，2026-09-07）**：`stem_verify.py` 的每顆事件現多帶
`reason`（melody_verify 判定結果原樣帶出的拒答/失敗說明文字，未改寫）與 `rules`
（從 `reason` 裡精確比對本節既有規則名稱 Ra–Re 抽出的清單，抽不到即為空陣列，
不猜測），報告層另加 `refusal_histogram`（拒答＝UNVERIFIED 事件依 `reason` 原文
分組計數）與 `rules_histogram`（依 `rules` 計數，未命中任何規則 id 者歸入
`"(untagged)"`）；判定邏輯本身未變動，僅讓既有拒答理由可被追溯。

### 8.6 partial 頻率工具（informational，WF0908-P1，2026-09-09）

新工具 `tools/partial_verify.py`（依 A13 裁決包選項 B+，
`reports/decision_packets/A13_partial_gate_domain.zh-TW.md` §4）：對
`stem_verify.py`（需帶 `--out-dir` + `--keep-stems`）產出的每顆乾聲分軌，
逐 partial（預設前 6 顆）量測**頻率**——重用 `melody_verify.measure_pitch_cents()`
本體（不另寫估計器），期望值換成該事件自己的 `--dump-modes` 逐 partial
頻率，容差沿用**既有** ±5 cents（`melody_verify.PITCH_TOL_CENTS`），**未新設
任何容差**（R2）。**振幅只記錄、不判定**（`amplitude_claim: "none"`）——
A13 §4 選項 C 查遍文獻找不到可溯源的振幅容差，本工具不自行發明一個。

**身分是 informational，非 GATE**：報告 `status="informational"`、
`gate_ready=false`，理由是本工具重用的量測器（C10 自證）本身「informational
或轉 GATE」都還待月月裁決——本工具不能比自己的前提主張更強。
（2026-09-25 更新：上面這個理由已過時。C10 已於 2026-09-10 裁決選 A（§9.7）。WF0925-P1 已把工具的
`gate_ready_reason` 改成：升 GATE 要月月另行裁決；A13 選項 B+ 原本以 C10 選 A 為升級前提，但 D15 A'
（2026-09-15）之後，放鍵/阻尼段的量測器已知誤差上界約 7.2 c，大於 ±5 c，這個前提照原文已不成立。
`gate_ready` 仍是 false。09-25 V1 那份報告的 `caveats[0]` 還寫「C10 self-cal still pending 月月裁決」，是舊字串
（出自 WF0925 staged 版 `tools/partial_verify.py`；更新這個字串屬裁決包 O16，不在本文件範圍；**2026-10-03 補記：`caveats` 已由 WF0925b-TF（`31851d5`）更新，現行 `caveats[0]` 寫的是 C10 於 2026-09-10 裁 A、D15 於 2026-09-15 裁 A'，升 GATE 另待月月裁決**）。要不要升 GATE、期望值慣例怎麼定，見
`reports/decision_packets/WF0925_open_decisions.zh-TW.md` Q18。）

**拒答（reuse，不新增邏輯）**：partial 帶碰撞（本事件自己的 partial 之間
±3% 帶重疊，`melody_verify.band_of`/`overlaps` 原樣重用）與**能量本底
閘門**（頻帶電平用 `melody_verify.Spectrogram.band_db()` 原樣重用的固定
N_FFT=2048/HOP=256 逐幀慣例量測）皆一律拒答並記 `reason`，不猜。能量閘門
的判準：優先比較**本事件自己起音前的靜音段**（`stem_verify.py` 逐顆事件
單獨渲染，起音前每個 sample 依建構即是靜音，取該段頻帶電平中位數作為
這顆事件自己的本底）——若某 partial 的量測窗電平比自己的本底高出至少
`melody_verify.RISE_DB`（15.0 dB，既有起音判定常數，原樣重用，非新容差）
即信任該量測；只有在**完全沒有起音前區間可比對**時（`t_exp<=0`，即整份
score 的第一顆事件）才退回 `melody_verify.BAND_GATE_DBFS`（−70 dBFS，
同一個既有常數）當絕對地板 fallback。（本節先前版本誤寫成「一律用
−70 dBFS 絕對地板」，已依實際出貨程式碼 `tools/partial_verify.py` 的
`partial_trusted()`/`partial_pre_onset_floor_dbfs()` 更正；兩個判準用到
的常數皆為既有值，未新增容差，只是「哪個常數用在哪個情境」寫錯了。）

**C13 harmonic-aware 判定（§8.5(b) 的弱基頻音；寫作時指 08-30 那 22 顆高音，A14 之後是 D16 的 16 顆）**：`reason`
含 melody_verify 自己的字面標記「near-silent fundamental band」的事件，
另外用**引擎自己 `--dump-modes` 的 n=1/n=2 比值**反推該音自己的非諧性係數
`B`（不引外部 B，不是新常數——`f_n=n·f1·√(1+B·n²)` 對 `B` 反解代數式），
再對「本工具實際量到（PASS 或 FAIL 皆算，UNVERIFIED 排除）」的 ≥2 個 partial
做最小平方回推 `f0`，結果寫入**獨立**欄位 `pitch_via_partials_cents` /
`pitch_via_partials_verdict`——`stem_verify` 原本的 `verdict`/`reason`
完全原樣照抄，兩者絕不合併。

**實跑統計（2026-09-09 WF0908-P1 當時；證據：`reports/gate_outputs/wf0908_P1_partial.txt`）**：全曲
905 事件的 `stem_verify.py --keep-stems` 嘗試過，但該工具自身
`compare_superposition` 步驟需同時把全部事件的 stem 陣列留在記憶體，
記憶體隨事件數飆到 ~41GB 而被中止，**partial_verify.py 當時未能在全曲 905
事件規模上執行**（2026-09-25 已執行，見本段之後的「全曲 905 顆已執行」段；此為 `stem_verify.py` 既有的 O(events) 記憶體設計，
非本卡程式碼所致，細節見證據檔「附註」段）。實際跑成的是兩個子集：
(2a)+(2b) 22 顆弱基頻高音（G5/D7/G6/F♯6 全曲出現的全部 23 顆事件）與
(2c) 既有的一般 40 事件子集。**可發布措辭**：22 顆弱基頻高音的
`pitch_via_partials` 全數 PASS；一般 40 事件子集 partials_verified=237/240
（3 顆例外為 t=0 首顆事件的已知 fallback 分支）——量到的 237 顆裡有
38 顆超出 ±5 cents（PASS=199/FAIL=38/UNVERIFIED=3），22 顆弱基頻子集
137 顆量到的 partial 中有 41 顆超出（PASS=96/FAIL=41），逐項數字見證據檔
「修正回合」段。**不可**寫成「905 顆音高與泛音全部驗過」，也不可只引用
「幾乎全數落在容差內」而不附上述 PASS/FAIL 拆分。

**全曲 905 顆已執行（2026-09-25，WF0925-V1；informational、`gate_ready=false`，不是 GATE）**：
WF0914-D14 把 `stem_verify.py` 改成串流（905 事件全量峰值約 1.65 GB）之後，partial_verify 第一次跑完
全曲。stem_verify 677 PASS／16 FAIL／212 UNVERIFIED，跟 09-14 D14 全量逐顆相同；疊加殘差
−119.42 dBFS（ESTABLISHED）。partial 層共 5428 個位置（比 905×6 少 2：E7、D7 的 `--dump-modes`
只給 5 個泛音），量到 5426 個：**PASS 4577／FAIL 849**，拒答 2 個（第 0 顆 E5 的 n=5、n=6：整首
第一顆沒有起音前靜音可比，退回既有的 −70 dBFS 絕對地板）。849 個 FAIL 裡 848 個偏高、1 個偏低，
最大絕對偏差 12.39 c；主因是工具以「第 0 根弦」為期望值，而這首每顆音 3 根弦的振幅加權平均約比
第 0 根高 +5 c（描述用對照、非判定；期望值慣例怎麼定待裁決包 Q18）。D16 那 16 顆（stem_verify 判
「基頻帶近乎無聲」）的 `pitch_via_partials` **16/16 PASS**（−3.56～+1.33 c）。08-30 那 22 顆舊弱
基頻高音現在基頻直接量 22/22 PASS；用同一個 `compute_pitch_via_partials()` 補算是 20 PASS／2 FAIL
（D7 −5.48 c、G6 −5.10 c，兩顆的基頻直接量都在 ±0.2 c 內；待 Q18b），所以上一段 09-09 的可發布措辭
「22 顆弱基頻高音的 `pitch_via_partials` 全數 PASS」對現行 binary 已不成立，新措辭待月月核定。
證據：`reports/partial_verify_full_2026-09-25.zh-TW.md` §0–§5、
`reports/gate_outputs/wf0925_V1_partial_stem_verify_full.txt`、`reports/gate_outputs/wf0925_V1_partial_verify_full.txt`。
**仍不可**寫成「泛音已驗證」或「905 顆音高與泛音全部驗過」，也不可只引 PASS 4577 而不附 FAIL 849。

**C10B 原始回合重驗（2026-09-09，informational，已撤回，僅存檔，見
`reports/gate_outputs/wf0909_C10B_estimator.txt` item 9）**：換上 §9.4 的
柔化質心估計器後，一般 40 事件子集 partials_verified=237/240（計數不變）、
量到的 237 顆裡一度測得 FAIL 從 38 降到 18（PASS 199→219）；22 顆弱基頻子集
partials 量到的 137 顆中一度測得 FAIL 從 41 降到 40（PASS 96→97）；
`pitch_via_partials` 22 顆弱基頻子集一度從 pass=22/fail=0 測得
pass=21/fail=1（D7, t=100.833s 翻轉，n=1 partial 落在近乎沉沒在雜訊底的頻帶，
stem_verify 記錄的 pre-onset floor −180.6 dBFS）。**這批「淨改善」數字全部來自
已於 C10B 修正回合撤回的柔化質心估計器（見 §9.5：柔化以期望值為中心，會系統性
把偏差往小報），不代表現況。現況（估計器撤回後，與 C10B 之前逐檔相同，見
`reports/gate_outputs/wf0909_C10B_estimator.txt` fix-round step 3 與
`reports/c10b_estimator_before_after.md` §5.2）：一般 40 事件子集 PASS=199/
FAIL=38/UNVERIFIED=3（partials_verified 仍 237/240）；22 顆弱基頻子集 partials
量到的 137 顆中 PASS=96/FAIL=41；`pitch_via_partials` 22 顆弱基頻子集
pass=22/fail=0（D7 那顆邊緣案例回到原本的 PASS）。**
本工具仍是 informational（`gate_ready=false`），此結果不改變其身分。

`--b-report`（A13 選項 B+ 第二項交付，一樣**不當 GATE**）：對 A4/G5/F♯6/G6/D7
重跑 `--dump-modes`、用同一 n=1/n=2 比值法反推引擎自己的 `B`，與
`reports/decision_packets/A13_partial_gate_domain.zh-TW.md` §3.3 抄錄的
Fletcher-Hamilton 直立琴參考 `B` 並排列出比值——**只列數字，不設通過條件**，
證據見 `reports/gate_outputs/wf0908_P1_b_ratio_report.txt`。

---

## 9. 量測器自證（WF0907-C10 2026-09-07 FAIL → WF0909-C10B 原始回合一度「已達標」→ 修正回合撤回 → WF0909-C10C 架構外方法亦否決，仍 FAIL → 2026-09-10 月月裁決選 A：承認已知上限、收窄主張域）

§8.4 item 2 說「量測器本身應先用合成哨兵證明自身誤差 ≤1 cent，才有資格執行
±5 cents 的產品 GATE」（月月 2026-08-30 查核第 5 點）。§9.1–9.3 是 C10 那次
量測（結果：FAIL，1.1721 cents）；§9.4 是 C10B **原始回合**改善估計器後
一度回報「已達成」的結果；**§9.5（修正回合）發現該估計器有結構性缺陷並撤回，
§9.6（C10C）到架構外找了時域 NLS、合成關卡全過但被真實音檔否決——
C10 的自證問題依然 FAIL，未解**；§9.7 記錄月月 2026-09-10 的裁決（選 A：
承認這個已知上限、收窄主張域、不改產品估計器）。§9.1–9.5 保留原樣做歷史
記錄，不倒填改寫；**現況以 §9.6 + §9.7 為準**。

### 9.1 方法

1. 把 `melody_verify.py::verify()` 內聯的頻帶質心 pitch 判定抽成純函式
   `measure_pitch_cents(mono, sr, f0, t_exp)`（不改任何數值行為——抽出前後對
   `scores/tests/melody_sentinel.score.json` 的判定 JSON 逐位元組相同，見
   `reports/gate_outputs/wf0907_C10_selfcal.txt` step 1）。`verify()` 現在呼叫
   這個函式；`stem_verify.py` 透過 `_load_module` 呼叫同一套數學，因此也一併
   受益，但本卡未動 `stem_verify.py`。
2. 新工具 `tools/measurement_selfcal.py`：**不經 TsukiSynthCLI**，純 numpy 合成
   已知答案的訊號（已知 f0、已知每 partial `exp(-ln(1000)·t/T60)` 衰減——與
   `ModalResonator.h` L13 的 `10^(-3t/T60)` 同一衰減律、`src/physics/MaterialDB.h`
   L82 同一 `ln(1000)` 淵源；諧波與兩組 stiffness inharmonicity `f_n=n·f0·√(1+B·n²)`
   partial 結構，B∈{1e-4, 1e-3}，僅供合成測試、不主張任何真實樂器的 B 值；
   已知非零起音時間；−90 dBFS RMS 白噪音床；峰值 −6/−30/−60 dBFS 三電平），
   對每個網格點呼叫**與產品 GATE 完全相同的** `measure_pitch_cents`（同一 import，
   不是另寫一份「測試用估計器」）。
3. 網格：MIDI 36..100（每半音）× 3 種 partial 結構 × 3 個電平 × sr∈{48000, 44100}
   = 1170 點。另有靈敏度反例：同一格（A4/harmonic/−6 dBFS/48 kHz）把合成頻率
   偏移 +3.0 / −3.0 cents（估計器被告知的「期望值」不變），估計器必須量到
   對應偏移 ±1.0 cents 以內——防止「估計器永遠回傳期望值」的假綠燈
   （`tests/test_measurement_selfcal.py` 用 monkeypatch 證明這條反例真的有牙齒：
   一個「永遠回傳期望值」的 mutant 估計器會被反例抓到）。

### 9.2 結果（完整輸出：`reports/gate_outputs/wf0907_C10_selfcal.txt` step 4）

命令：`python tools/measurement_selfcal.py`

| 分組 | max \|error_cents\| |
|---|---:|
| 全網格（1170 點，0 refuse） | **1.1721** |
| f0 < 167 Hz | 1.1721 |
| f0 167–500 Hz | 0.6758 |
| f0 500–2000 Hz | 0.9836 |
| f0 > 2000 Hz | 1.1386 |
| 峰值 −6 dBFS | 1.0707 |
| 峰值 −30 dBFS | 1.0737 |
| 峰值 −60 dBFS | 1.1721 |

靈敏度反例：+3.0c → 量到 +2.9818c（OK）；−3.0c → 量到 −2.9936c（OK）。

**判定：max_abs_error_cents = 1.1721 > 1.0 cent 門檻 → 自證 FAIL。**
逐點檢視最差區（`sr=48000 midi=37`＝D2 69.3 Hz、`sr=48000 midi=100`＝
D7 2638 Hz），誤差在乾淨訊號（−6 dBFS、諧波、無殘響）就已存在
（例：MIDI37 harmonic −6 dBFS = −0.9065c），且與電平/隔壁半音無平滑趨勢
（MIDI36 = +0.29c、MIDI38 = +0.47c、MIDI37 = −0.91c），指向 1.25 s 視窗
Hann/2048/hop-256 STFT 在特定頻率-bin 對齊下的頻帶質心系統偏差——與 §7/§8.3
已記錄的「窄帶內非平坦頻譜對質心不穩健」是同一類機制，而不是本合成哨兵
本身的產物（噪音床/inharmonicity 對誤差幅度影響很小，見上表電平分組）。

**本卡未修改 `measure_pitch_cents` 的判定邏輯**（R2：不准為了過線去改估計器）；
**1.1721 cents，待月月裁決 C10 A/B**（當時；2026-09-10 已裁 A，見 §9.7）（選項 A/B 見裁決包
`reports/decision_packets/C10_selfcal_domain.zh-TW.md` §2）。

### 9.3 限制（誠實列出，不得省略）

- **只測乾聲。** 本節與 §8.3 一致：帶殘響訊號的音高判定不在本自證範圍內，
  混響梳狀著色是另一個已知偏差來源，數字更大（觀察到最多 ~9.5c）。
- **只測合成訊號，不含真實引擎渲染。** 本節證明的是「頻帶質心估計器本身,
  給定已知答案的乾淨波形」的誤差，不是「TsukiSynthCLI 渲染 + 估計器」整條鏈路
  的誤差（後者仍由 §7/§8 的全曲哨兵覆蓋）。
- **T60 為每訊號單一值（1.5 s），不逐 partial 變化。** 簡化選擇，已在
  `measurement_selfcal.py` docstring 揭露，不主張任何真實樂器的逐泛音衰減率。
- **起音誤差僅供參考，無裁定門檻。** 觀察到系統性 ~37 ms（= 合成起音時間本身），
  推測是合成訊號在起音前僅 37 ms 靜音、不足以讓 `refined_onset()` 的解析濾波器
  （~1/頻帶寬）穩定收斂，不影響本卡 exit code，也不主張任何裁定。

### 9.4 量測器自證已達成（WF0909-C10B 原始回合，2026-09-09，**已被 §9.5 推翻**）

月月 2026-09-09 對 C10 裁決包（§2 選項 A/B）裁決 **B：改估計器、重跑所有既有
音高證據**。完整方法、三個被否決候選、逐項證據前後對照見
`reports/c10b_estimator_before_after.md`（白話導讀）與
`reports/gate_outputs/wf0909_C10B_estimator.txt`（完整命令與輸出）；本節只記
結論與最終數字。

**方法**：`measure_pitch_cents()` 的頻帶質心公式本身沒有換掉（換成單峰估計法
的兩個候選在真實 course 音色上會整個垮掉，見下方「被否決的候選」），而是把
±3% 頻帶的兩個硬邊界（原本 0/1 一刀切）換成 raised-cosine **柔化漸層**
（`PITCH_EDGE_TAPER_FRAC = 0.75`，外側 75% 做餘弦漸層、中央仍是平頂）——
保留質心對 course 微分音天生穩健的特性，同時去掉硬邊界造成的系統偏差
（C10 裁決包 §0 診斷：頻帶邊界的 Hann 旁瓣洩漏不對稱地灌進質心）。舊版
（硬邊界質心）原樣保留為 `measure_pitch_cents_legacy()`，供本節與前後對照
使用；不再被 `verify()` / `stem_verify.py` / `partial_verify.py` 呼叫。

**被否決的候選**（工作卡 §2.1 列出的三個方向都試過，數字與否決理由見證據檔
step 1）：
- **單峰拋物線內插**：合成網格 0.2228c、hold-out 0.0832c，數字上完全達標，
  但真實渲染音檔（哨兵 melody_sentinel，cimbalom 預設 3 弦 course）5 顆音
  4 顆從 PASS 掉到 FAIL（最差 −8.95c）——course 的弦距常小於一個 FFT bin，
  單峰估計器在這種情況下鎖到的是瞬間相位競爭結果，不是 course 中心頻率；
  合成自證網格完全沒有模擬 course，量不出這個失效模式。
- **相位差法**：合成網格 0.3923c，靈敏度反例是三者中最準的
  （+3.0c→測得+2.99999c），但同樣是單峰法，melody_sentinel 上同樣 4/5 FAIL。
- **zero-padding 質心**（工作卡字面上寫的候選 c）：8×/16×/32×/64× 補零皆
  收斂不到 1 cent 以下（1.1796/1.1727/1.1693/1.1710c），印證裁決包 §0 的
  診斷——偏差是頻帶內真實的旁瓣能量，不是離散取樣的量化誤差，加密取樣點
  救不了它。

**結果**（完整表格見證據檔 step 1/1a）：

| 網格 | max \|error_cents\| | 判定 |
|---|---:|---|
| 開發網格（1170 點，同 §9.2 的網格） | **0.2924** | PASS（門檻 1.0） |
| Hold-out 網格（1040 點，新增，f0 偏移/B/電平/起音時間全部與開發網格不同） | **0.2465** | PASS（門檻 1.0） |

靈敏度反例（開發/hold-out 兩次呼叫皆印出同一組數字，因為都是同一個
production 估計器）：+3.0c → 量到 +2.7180c（OK）；−3.0c → 量到 −2.7241c
（OK）。

**真實音檔零迴歸驗證**（本卡新增的把關步驟，§9.2 原本沒有）：
`melody_verify.py --selftest`、`scores/tests/melody_sentinel.score.json`、
給愛麗絲乾聲全曲 905 事件 stem_verify（逐顆 verdict 100% 相同：671/22/212
不變）、給愛麗絲乾聲 whole-file baseline（32 顆 FAIL→PASS、0 顆 PASS→FAIL）、
月光 v4（6 顆 FAIL→PASS、0 顆 PASS→FAIL）、HostProbe H6 五個 block size、
corpus 30 檔強域全綠子集——**全部重跑，沒有任何一顆既有 PASS 變成 FAIL**。
唯一的邊緣案例在 informational 工具 `partial_verify.py` 裡一顆已知「基頻
天生弱、近雜訊底」的音，見 `reports/c10b_estimator_before_after.md` §1/§2。

**判定：量測器自證 ≤1 cent 已達成（2026-09-09）。** ±5 cents 產品門檻、
拒答規則、band 選擇、course/detune 判定邏輯全部未動（R2）。§9.3 列出的
限制（只測乾聲、只測合成訊號、T60 簡化、起音誤差僅供參考）對 C10B 同樣
成立，未被本輪修改觸及。

**本節（§9.4）的「已達成」結論已被 §9.5 推翻，保留原樣做歷史記錄，不倒
填改寫。現況以 §9.5 為準。**

### 9.5 修正回合：估計器撤回，自證仍未達成（WF0909-C10B 修正回合，2026-09-09）

§9.4 的柔化質心經稽核發現結構性缺陷後撤回。完整根因、五個候選（含 §9.4
沒提到的第五個、修正回合新試的 mean-shift 變體）的數字表，見
`tools/melody_verify.py::measure_pitch_cents()` 的 docstring 與
`reports/gate_outputs/wf0909_C10B_estimator.txt` step 2；本節只記結論。

**缺陷本質**：raised-cosine 柔化漸層以「期望 f0」為中心（band_of(f0) 的
中點就是 f0），所以柔化的「權重最高點」與「被拿來跟量測值比較的目標」是
同一個點——訊號真值離期望值越遠，柔化就把它壓得越低。用卡自己的
`measurement_selfcal.measure_one(freq_offset_cents=...)`（真值偏移、期望
值不動，與 §7/§8 的 stem_verify/partial_verify 用法同構）實測：MIDI 37
（~69 Hz，harmonic，−6 dBFS，clean 訊號）真值 +12.0c，§9.4 的估計器只測到
+4.806c（增益 0.40），舊估計器測到 +8.620c（增益 0.72，仍不完美但明顯更
準）——即在完全不碰 ±5 cents 這個數字的情況下，把低音區實質可信賴的容差
放寬到約 ±12.5 cents，違反 R2「不准調寬任何容差」的精神。

§9.2/§9.4 用到的開發網格與新增的 hold-out 網格，都是把 band 對準**已經
偏移過的真值**本身（`measure_one`/`measure_one_holdout` 傳給
`measure_pitch_cents` 的 `f0` 參數就是被偏移後的那個真值）——換句話說兩個
網格都只測了「真值剛好落在頻帶中心」這一種情況，結構上抓不到上一段那個
真正的缺陷；這正是本卡 §2.2 設計 hold-out 網格要防的「過擬合」，只是這次
過擬合的是兩個網格共有的同一個盲點，不是單一網格的問題。

**修正回合多試的候選（e）**：自我參照式 mean-shift 柔化——柔化中心不釘死
在 f0，而是先算一次硬邊界質心當初始估計，再反覆把柔化中心搬到「目前估計
值」重算，直到收斂（5 次迭代已收斂，15 次數字不變）。這個做法確實有幫助
（同一批偏移測試，taper 0.5 時最差增益缺口從 §9.4 版本的 ~0.55-0.66 降到
~0.31），開發網格 max\|error\| = 0.7167c 仍 < 1.0c——但收斂到的固定點在
最差格點（MIDI37，−12c 偏移）增益 0.687，仍然比舊估計器同一格的 0.885
差，屬於同一個缺陷的縮小版，不是修好。對 taper 分數做 0.75→0.0 的 13 步
掃描，證實「自證誤差」與「增益保真度」在這個 estimator 家族裡是連續、
單調、無法兩全的取捨：能把開發網格壓到 1.0 cent 以下的最窄 taper（約
0.15-0.20）本身增益缺口仍有 ~0.35-0.40，不比 0.75 taper 好。

**結論**：卡 §2.1 列出的三個候選（拋物線內插、相位差法、zero-padding）
加上 §9.4 實際出貨的柔化質心、修正回合新試的 mean-shift 變體，共五個候選
全數否決。卡 §5 的規則（三個以上方法都達不到 ≤1.0 含 hold-out，停下回報
數字）在此適用：`measure_pitch_cents()` 撤回，回到 §9.1-9.2 記錄的硬邊界
質心數學（與 `measure_pitch_cents_legacy()` 位元組相同）。**C10 的核心
問題——開發網格 max\|error\| = 1.1721 cents，本輪另外量出的 hold-out
網格（`HOLDOUT_T_ONSET_S` 同時修正為真正不對齊 hop 的 0.0507 s）
= 1.0840 cents，兩者皆 > 1.0 cent 門檻——依然未解。**

`tools/measurement_selfcal.py` 新增一個 informational（非 GATE、不新增
容差）的 gain-fidelity scan（`gain_fidelity_scan()`，`--gain-scan` 相關輸出
併入預設與 `--holdout` 兩種呼叫），把「期望值固定、真值另外偏離」這條軸
永久補進自證工具本身；`tests/test_measurement_selfcal.py` 新增
`test_gain_fidelity_no_regression_vs_legacy`，鎖定「未來任何估計器改動的
增益保真度不得比舊估計器差」——這正是本輪抓到 §9.4 缺陷所用的檢查，寫成
迴歸測試留下來。

**真實音檔重跑**（確認撤回後行為與 C10B 之前完全一致，不是新的迴歸）：
`--selftest` 5/5、`melody_sentinel` 5/5、HostProbe H6 五個 block size
25/25 PASS 位元相同、corpus 30 檔強域全綠子集全部 0 FAIL 且逐檔 PASS/
UNVERIFIED 數字與 §9.2 之前的原始記錄逐一相同、給愛麗絲乾聲全曲 stem_verify
與月光 v4 的重跑數字見 `reports/c10b_estimator_before_after.md`
「修正回合」章節。

**判定：量測器自證 ≤1 cent 尚未達成。** 決策包
`reports/decision_packets/C10_selfcal_domain.zh-TW.md` §5 記錄同一結論，
並列出當時仍待月月裁決的選項（2026-09-10 已裁 A，見 §9.7）：§2 選項 A（收窄主張域、不改程式碼）依然可行；
選項 B 已經試過且確認在目前架構內無解；真正的選項 C（架構外的新方法）
尚未找到。±5 cents 產品門檻、拒答規則、band 選擇、course/detune 判定邏輯
全部未動（R2）。

### 9.6 架構外方法已試過：時域 NLS 合成全過、真實音檔否決（WF0909-C10C，2026-09-09，卡 RED）

§9.5 說「真正的選項 C（架構外的新方法）尚未找到」。WF0909-C10C 去找了，
找到了、實作了、量完了，**結論是否決**。完整前後對照見
`reports/c10c_nls_estimator_before_after.md`，完整命令輸出見
`reports/gate_outputs/wf0909_C10C_nls.txt`；本節只記結論與數字。

**方法**：時域最小平方擬合（NLS）。不看 FFT 格子，對分析段直接擬合
`x(t) = Σ A_k·exp(−t/τ_k)·cos(2π f_k t + φ_k)`（K = 1..3 由 BIC 選），
回報振幅加權平均頻率。殘差是**模型與資料套用同一個 band 投影之後**的差
（由 Parseval 等價於帶通後時域殘差的 L2 範數）——濾波器對兩邊一視同仁，
所以不會重蹈 §9.5 候選 (d) 的覆轍。**候選程式未落地**：依月月 2026-09-10
裁決（選 A，不動產品估計器），候選連同其測試保存在
`reports/c10c_nls_candidate.patch`，`tools/melody_verify.py` 內不留死碼。

**合成關卡：四條全過，而且不是低空飛過**（門檻都是既有的 1.0 cent，
沒有新增任何容差；卡 §1.1 只是把既有的 gain-fidelity 掃描升為 GATE 判定
條件並把偏移集合擴成 0/±3/±5/±12/±25/±40 cents）：

| 合成關卡 | 現行估計器 | C10C 候選 |
|---|---:|---:|
| 開發網格（1170 點） | 1.1721 c FAIL | **0.2868 c PASS** |
| hold-out 網格（1040 點，只跑一次） | 1.0840 c FAIL | **0.0816 c PASS** |
| 增益保真（308 格，\|量測−真值\|） | 16.8647 c FAIL | **0.0090 c PASS** |
| 三弦 course 中心（18 格） | 0.3337 c PASS | **0.0064 c PASS** |

**真實音檔：否決。** 在產品 GATE 真正走的路徑（`stem_verify` 乾聲分軌、
給愛麗絲前 300 事件）候選把 **7 顆 PASS 判成 FAIL**（251/13/36 →
244/20/36，0 顆反向）；30 檔「強域全綠」corpus 動了 **9 檔**（5 PASS→FAIL、
3 UNVERIFIED→FAIL、1 PASS→UNVERIFIED），而該 corpus 記錄在案的不變量是
「0 FAIL 維持」。

**逐顆診斷（實測，非推論）**：給愛麗絲的鋼琴音 `duration` 只有 0.215–0.231 s，
分析視窗卻是 `PITCH_SEG_S` 的 1.23 s——音在視窗中段就被放鍵阻尼掐掉，
**包絡不是單一指數**，而那正是 NLS 的模型假設。擬合出的 τ ≈ 0.030–0.052 s
（線寬約 16–26 cents 在 E5/F5），模型挑的第 2、3 個「分音」彼此只差
~20 cents，**落在彼此線寬之內、根本不可分辨**，只是逼近一個寬的非勞侖茲
共振峰的柔性基底（R² 0.67→0.96，所以 BIC 一直買帳）。把不可分辨的分解拿去
做振幅加權平均，答案就會亂跳：三顆 E5/F5 分軌的帶內其實是**單一寬峰、中心
離宣告音高不到 1 cent**（bin 從 −13 到 +12 cents、相對振幅 0.84–1.00），
NLS 報 −5.04 / −5.21 / +5.07 c，質心報 −0.59 / −0.21 / +0.71 c。
**質心較接近真值。**

**這輪最重要的結構性發現（比估計器本身重要，寫進 §9 是因為它改變 §9 的
判準本身）**：`tools/measurement_selfcal.py` 合成的訊號是「指數衰減正弦波
相加 + 雜訊」，**這就是 NLS 估計器自己的模型**。所以一個「模型剛好對上」的
估計器可以近乎套套邏輯地橫掃全部四條合成關卡，卻在 GATE 真正要判的渲染
音檔上更差。**現行形式的 1-cent 自證門檻，本身不足以認證一個估計器上產品
線**——這與 C10B 稽核發現的「兩個網格都測不到增益軸」是同一類盲點，只是
高了一層（上次盲的是「軸」，這次盲的是「訊號模型」）。任何未來嘗試應先
讓哨兵語料帶上放鍵/阻尼段；那會改變現行估計器 1.1721 c 這個數字本身
（門檻不變，比對對象變），已超出 C10C 範圍，記在裁決包 §6.3 待月月定。

**落地狀態**：`measure_pitch_cents()` 行為未變（仍回傳
`measure_pitch_cents_legacy()`，1170 點開發網格上逐點位元相同，由
`tests/test_measurement_selfcal.py::test_measure_pitch_cents_matches_legacy_after_revert`
鎖定）——**本文件 §7/§8 與所有既有音高證據的數字全部維持有效，不需要重寫**。
`tools/measurement_selfcal.py` 保留兩項誠實升級（gain-fidelity 升為 GATE
判定條件、新增 `course_semantics_check()`），用現行估計器跑會誠實 exit 1。
±5 cents / ±10 ms / 拒答規則 / band 選擇 / course·detune 判定全部未動（R2）。

**判定：量測器自證 ≤1 cent 仍未達成，卡 RED。** 選項 B 現已在兩個結構不同
的家族、六個候選上試完；建議改選 §2 選項 A（收窄主張域、不改程式碼），
措辭草案見 `reports/decision_packets/C10_selfcal_domain.zh-TW.md` §6.2。

### 9.7 裁決記錄：月月 2026-09-10 選 A（收窄主張域，不改程式）

月月 2026-09-10 就 `reports/decision_packets/C10_selfcal_domain.zh-TW.md` §2
的兩個選項裁決：**選 A——收窄主張域，承認量測器自身誤差，不改產品估計器，
不再追選項 B。**

裁決內容（落地於本文件 §8.4 item 5、§8.5 最後一條，與裁決包 §7）：

1. **承認已知上限**：產品估計器（`measure_pitch_cents()`，±3% 硬邊界頻帶質心）
   自身系統誤差為 1.1721 cent（開發網格）／1.0840 cent（hold-out 網格），
   均 > 月月 2026-08-30 訂的 ≤1 cent 自證門檻。這是**接受但不修**的狀態。
2. **產品估計器一個位元都不改**：`tools/melody_verify.py` 本輪未動
   （`git diff -- tools/melody_verify.py` 為空）。因此 §7/§8 與所有既有音高
   證據的數字全部維持有效，沒有任何一份證據需要重寫或撤回。
3. **主張域收窄**：±5 cent 產品門檻不變，安全係數約 4.3×；但不得宣稱量測器
   通過 ≤1 cent 自證（§8.4 item 5），且 3.8–5.0 cent 之間的數字不得單獨用來
   斷言渲染正確或錯誤（§8.5）。
4. **C10C 候選不落地**：時域 NLS 候選（§9.6）連同其三個測試保存在
   `reports/c10c_nls_candidate.patch`，不進產品檔，避免死碼。§9.6 的
   量測結論與數字照原樣保留做歷史記錄，不倒填改寫。
5. **`tools/measurement_selfcal.py` 的兩項升級照落地**：增益保真掃描升為
   GATE 判定條件（沿用既有 1.0 cent，未新增容差）、新增
   `course_semantics_check()`。用現行估計器跑會**誠實 exit 1**——這是預期
   行為，是「承認未達標」的機器可讀形式，不是迴歸。

未結項（登記於裁決包 §7）：D15「哨兵語料補放鍵/阻尼段」——§9.6 指出現行
哨兵訊號模型（指數衰減正弦和）本身不足以認證估計器，修這個盲點會改變
1.1721 c 這個數字本身（1.0 cent 門檻不變，比對對象變），已超出本輪範圍。

---

## 10. L2 HostProbe H6 可變 block size / H7 user preset round-trip（WF0907-E10，2026-09-08）

### 10.1 H6：可變 host block size ── 全綠（water_gong Pitch Glide 段已硬化，WF0908-E10b，2026-09-09）

`tests/host_probe.cpp` 新增：哨兵旋律（H3 那份 `kMelody`）在 5 個 block size
（64 / 256 / 512(=host 常用值) / 1024 / 4096）各起一個全新 VST3 實例、各自
`prepareToPlay` 後渲染，寫 5 個 WAV；每個 size 對 64 印出「informational、不設
新容差」的 `max|delta|`（LSB @ 24-bit）與 RMS delta（dB re signal），判定則沿用
既有 `tools/melody_verify.py`（±10 ms / ±5 cents，已批准容差，未動）跑在每個
WAV 上。

**實測結果**（完整命令輸出見 `reports/gate_outputs/wf0907_E10_hostprobe.txt`）：
哨兵旋律 5 個 block size 彼此 **位元完全相同**（`max|delta|=0.000 LSB@24bit`，
`RMS delta≈-218 dB re signal` ≈ 浮點雜訊層級），5 個 WAV 的 `melody_verify.py`
結果逐事件數字也完全相同（5 PASS / 0 FAIL / 0 UNVERIFIED × 5 sizes）。同樣
方法測 FM Piano 高音（MIDI 96）也是位元完全相同。

**額外覆蓋（informational only，不餵 melody_verify，理由見下）**：water_gong
（Chromatic sub-engine 1）搭配 Pitch Glide 巨集拉滿（1.0），同樣 5 個 size 各
渲染一份，只印 delta，不判定——沒有餵 `melody_verify.py` 是因為它需要一個
`--dump-modes` 驗證過的預期音高 fixture，本卡未新造這種 fixture（超出低風險
範圍）。**這組 delta 明顯不是雜訊層級**：block 256 vs 64 已到 -11.21 dB re
signal、block 4096 vs 64 到 +2.63 dB re signal（即渲染能量已被 block size
改變到超過原訊號本身）。cdf2017 修的是「glide 推進速率」的 buffer-size
獨立性（見 `src/engines/ChromaticEngine.h:602-627` 註解），但模態頻率縮放
(`resonator.scaleFrequencies`) 仍是逐 block 呼叫一次——block 越大，glide
軌跡的取樣粒度越粗，對這種連續變頻的非線性共振器，長時間累積後波形發散是
可預期的量級問題，但目前只有這一次測量，**未經多輪重跑或機制拆解，不主張
這是 bug 還是預期的粗粒度效應**；留給後續 R 系列或月月決定是否要追。

**已硬化（WF0908-E10b，2026-09-09）**：上一段診斷（block 越大、glide 軌跡取樣
粒度越粗）證實就是根因，不是別的效應。修法：`ChromaticEngine.h::renderNextBlock()`
把 glide phase 推進 + `resonator.scaleFrequencies()` 從「每個 block 一次
（`advanceGlidePhase(..., numSamples, ...)` 用整個 block 的取樣數）」改成
「每個取樣一次（`numSamples` 固定傳 `1`，與 host block size 無關）」——block
size 不再出現在計算裡，序列本身在任何切法下都是同一串運算，因此不只是
settled phase 相同（cdf2017 那層 cap 已經保證），而是整條音軌逐取樣位元相同。
water_gong Pitch Glide=1.0 這組 CHECK 已從 informational 改成硬性判準
（**沿用哨兵旋律段既有的「位元相同」判準，不是新容差**，R2）：block
256/512/1024/4096 vs 64 皆 `max|delta|=0.000000 LSB@24bit`（4/4 PASS）。用
未修的 `build\TsukiSynth.vst3`（cdf2017 二進位）重跑同一份 HostProbe 反向
確認：同樣 4 個 CHECK 量到 757927.625 / 1693565.3125 / 3056105.0 /
5258823.25 LSB@24bit（與本節上一段的舊 informational dB 數字量級一致）
FAIL，證明新 CHECK 真的會抓到舊 bug，不是空判準。完整輸出見
`reports/gate_outputs/wf0908_E10b_glide_h7.txt`。

### 10.2 H7：user preset round-trip ── 架構衝突，已依裁決落地選 (B)（WF0908-E10b，2026-09-09）

**裁決記錄**：規劃者 2026-09-09 選 (B)，已落地（見下）。

**發現**：WF0907-E10 設計文件 §2.2 假設 HostProbe 可以直接呼叫
`PresetManager::saveUserPreset()`/`loadPreset()`（把「實例 A/B」當成能直接
呼叫這兩個方法的物件）。但這與 `tests/host_probe.cpp` 檔頭本來就寫明的設計
矛盾：本探針透過 `juce::VST3PluginFormat` 從磁碟載入**建置產物**
`TsukiSynth.vst3`（跟 DAW 載的是同一顆二進位檔），拿到的是不透明的
`juce::AudioPluginInstance`（VST3 host wrapper），不是 link 進來的
`TsukiSynthProcessor` 物件——沒有辦法呼叫它專屬的、非標準 `AudioProcessor`
介面的方法。

`saveUserPreset()`/`loadPreset()`/`deleteUserPreset()`/`userPresetExists()`
在生產環境只被 `src/PluginEditor.cpp`（Save 按鈕，跟 `AudioProcessor` **同進程**
UI 程式碼）呼叫過（`grep -rn "presetManager\."` 核實，見本卡證據檔開頭）。
VST3 合約本身沒有「host 叫 plugin 把目前狀態存成一個新命名 user preset」這種
標準操作——`getNumPrograms`/`setCurrentProgram`/`getProgramName` 這組泛型介面
確實有接到 `presetManager.loadPreset()`（讀側可行），但**沒有對應的寫側**。

若要真的測試 `saveUserPreset()`，唯一辦法是把 `PluginProcessor.cpp` 直接
link 進 `TsukiSynthHostProbe` target——但它的 `createEditor()` 回傳
`new TsukiSynthEditor(*this)`，linker 會連帶要求整條 GUI module chain
（`juce_gui_basics`/`juce_gui_extra` 等），是 `CMakeLists.txt` 的改動，
超出本卡「只碰 `tests/host_probe.cpp` + 文件」的宣告範圍（GATE 5）。

**留給月月裁決的選項**：
1. **(A) 全 link**：把 `PluginProcessor.cpp`＋`PluginEditor.cpp`＋GUI modules
   直接 link 進 HostProbe target，H7 對「實例 A 內部真正的 presetManager」
   做端到端測試——最貼近設計文件原意，但 CMakeLists.txt 改動大、GUI 依賴重。
2. **(B) 抽出無 GUI 依賴的 `createParameterLayout()`**：搬到獨立的
   `src/ParameterLayout.h/.cpp`（不 include `PluginEditor.h`），HostProbe 用它
   建一份「影子」APVTS + 真正的 `PresetManager`（`PresetManager.h` 本來就是
   header-only、只需要一個 `AudioProcessorValueTreeState&`），對這份影子
   apvts 呼叫真正的 `saveUserPreset()`；LOAD 側則仍可用真正載入的 VST3 實例
   走 `setCurrentProgram()`（已驗證是真實碼路徑）。較乾淨，但要動
   `src/PluginProcessor.cpp`（觸發 R6 全套：8/8 位元不變 + `--full`）且要改
   `CMakeLists.txt`。
3. **(C) 縮小 H7 範圍**：SAVE 側用 `getStateInformation()`（已被 H5 證實可
   泛型呼叫）手動組出 `.tsukipreset` XML 寫入磁碟（**不**呼叫真正的
   `saveUserPreset()`——所以不測它的暫存檔 atomic replace / id 保留 /
   `toSafeFilename` / overwrite 檢查邏輯），LOAD 側用真正載入的 VST3 實例走
   `setCurrentProgram()`（真實碼路徑）。不動 `src/`、不改 `CMakeLists.txt`，
   但必須誠實標註「只測了讀側，寫側是本探針自己組的檔案，不是
   `saveUserPreset()` 本身」，且 F-03（IR 狀態不隨 user preset 走）的 CHECK
   在讀側一樣可以做（`saveUserPreset()` 本來就不寫 `reverb_ir_path`，
   見 `src/PresetManager.h:136-152` vs `PluginProcessor.cpp:717-733`）。

本卡（WF0907-E10）未擅自選任何一個選項落地（R2/R3 精神：不為了過而縮小或
發明新東西），`tests/host_probe.cpp` 當時印出 `[BLOCKED]` 訊息說明現狀，
不宣稱 H7 已測。

**落地紀錄（WF0908-E10b，2026-09-09，選 (B)）**：

- `src/PluginProcessor.cpp` 的 `createParameterLayout()`（原 private static
  member）搬到新檔 `src/ParameterLayout.h`（宣告 `createTsukiParameterLayout()`）
  + `src/ParameterLayout.cpp`（實作，一字未改，純搬移）。不 include
  `PluginEditor.h`，也不 include 任何 GUI module。`PluginProcessor.cpp` 改
  `#include "ParameterLayout.h"` 並呼叫這個自由函式；`PluginProcessor.h` 移除
  原本的 private 宣告。`CMakeLists.txt`：`TsukiSynth` target 加
  `src/ParameterLayout.cpp`；`TsukiSynthHostProbe` target 的
  `add_executable` 也加這個檔案（唯一新增的 link 對象，**沒有**加
  `PluginEditor.cpp` 或任何 `juce_gui_*` module，維持這份文件開頭「GUI-free」
  的宣告）。「參數 id/範圍/預設一字不改」的驗證見 GATE 5.5（H2 前後參數清單
  diff）。
- `tests/host_probe.cpp` 新增 `ShadowProcessor`（最小 `juce::AudioProcessor`
  子類，只實作 pure-virtual 介面，成員只有 `apvts`（用
  `createTsukiParameterLayout()` 建構）+ `PresetManager presetManager{apvts}`）。
  H7 SAVE 側：設 12 個非預設參數（跨 global/macro/cimbalom/chromatic/
  reverb/eq 六組）、對這份影子 apvts 呼叫真正的
  `PresetManager::saveUserPreset("wf0908_h7", true)`。LOAD 側：**之後才**用
  `fm.createPluginInstance()` 建一個全新真 VST3 實例（讓它建構期的
  `PresetManager` ctor `scanUserPresets()` 能看到剛寫的檔案），
  `getProgramName()` 掃到該 preset 後呼叫真正的
  `setCurrentProgram()`（即 `TsukiSynthProcessor::setCurrentProgram()` →
  `presetManager.loadPreset()`，`src/PluginProcessor.cpp` 已驗證的真實碼路徑）。
  比對用**索引**而非嘗試重建 VST3 的內部數值 paramID hash：兩份
  `getParameters()` 陣列在索引 `[0, 60)` 保證是同一份
  `createTsukiParameterLayout()` 依宣告順序展開的 60 個產品參數（VST3 wrapper
  自動附加的 Bypass/Program/2048 個 MIDI CC 參數固定接在索引 60 之後——已用一次
  即時 dump 核實），逐一比對 `getName()`（防止順序悄悄跑掉）與 `getValue()`
  （容差 1e-6，浮點雜訊層級）。**結果：60/60 參數 0 mismatch，PASS**。
  最後呼叫真正的 `PresetManager::deleteUserPreset()` 清掉這次寫入的
  `%APPDATA%\TsukiSynth\Presets\wf0908_h7.tsukipreset`（真實 preset 目錄，
  跟月月自己用的是同一個）。
- **F-03 兩條 IR CHECK，維持 `KNOWN-FAIL(F-03)`**（不計入 exit code，P3 修
  F-03 後才會硬化成必過 CHECK）：(1) 存檔後讀 `.tsukipreset` 檔原始位元組，
  斷言含 `"reverb_ir_path"` 字串——今天沒有（`saveUserPreset()` 只序列化
  `apvts.copyState()`，`reverbIRPath`/`reverbIRName` 是 `TsukiSynthProcessor`
  的獨立成員，這個方法從不寫它們，見
  `reports/decision_packets/F03_IR_PRESET_RECALL.zh-TW.md` §1.1 已核實的
  程式證據）；(2) LOAD 側真實例載入 preset 後呼叫
  `getStateInformation()`（H5 已證實這條路 host-generic），同樣位元組搜尋
  `"reverb_ir_path"`——同樣今天沒有。兩者都印 `[KNOWN-FAIL(F-03)]` 而非
  `[FAIL]`，與 WF0907-E10 對 H7 `[BLOCKED]` 的 exit-code-neutral 處理精神
  一致。
- 完整命令與輸出見 `reports/gate_outputs/wf0908_E10b_glide_h7.txt`。

---

## 2026-10-03 現況（文件卡 DOC-B；只補現況，上面各節原文不動）

- 三層 GATE 都已實作並在用：L1 `tools/melody_verify.py`（onset ±10 ms 已於 2026-10-02 月月裁決 Q04=A 補登進 `ROADMAP_PHYSICS.md` §6；pitch ±5 c 沿用 f0 列）、L2 `TsukiSynthHostProbe`（2026-10-02 WF1002b 整合卡 231 PASS／0 FAIL）、L3 Cubase 實測（2026-08-22，L3b）。
- **H7 與 DAW program（2026-10-02 月月裁決 Q06=A）**：外掛報給 DAW 的 program 清單現在只含 27 個工廠音色，使用者音色不再出現在 `getProgramName()`／`setCurrentProgram()`。§10.2 描述的「掃 `getProgramName()` 找到使用者 preset 再 `setCurrentProgram()`」那條 LOAD 路徑已不存在；WF1002-C1 把 H7 的 LOAD 側改成把 preset 檔內容當成 DAW 專案 state 交給真 VST3 實例（`buildStateBlobFromPresetFile()`），外掛自己選單的路徑在新的影子 processor 上驗，並加 Q06 檢查「加了使用者 preset 前後 DAW 的 program 數都是 27」（`tests/host_probe.cpp` 檔頭 H7 說明，證據 `reports/gate_outputs/wf1002_C1_hostprobe.txt`）。
- §10.2 末段的兩條 `KNOWN-FAIL(F-03)` IR CHECK 已由 WF0908-P3（受管理 IR 庫，2026-09-09）硬化成正式 CHECK；IR「檔案存在但載不進來」的分支 2026-10-02 起改走缺檔三態（Q10=B）。
- §8.4 可發布措辭、§8.5 主張域、§9 量測器自證（C10 選 A、D15 選 A'）都沒有變。
