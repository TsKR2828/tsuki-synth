# WF1004-P：外掛 voice pool 按引擎分大小（Chromatic 32、Piano／Cimbalom 16、FM 16）

> 日期：2026-10-07　卡：WF1004 P 卡　狀態：**採用**（事先寫好的四條判準全過）
> 裁決依據：月月 2026-10-07「照 Fable 建議」＝Chromatic 引擎 pool 32、Piano 與 FM 維持 16，仍採證據門檻制（規劃者轉述，Fable 原文查不到）。
> 判準在量測**之前**寫好：`reports/gate_outputs/wf1004_P_criteria_preregistered.txt`（檔案時間 01:04:21；第一次量測 01:10:54）。
> 量法與重跑指令：`reports/gate_outputs/wf1004_P_method.txt`。全部原始輸出：`reports/gate_outputs/wf1004_P_raw_*`、`wf1004_P_summary_3runs.txt`。
> 月月是聾人使用者，以下全部是數字，沒有任何聽感判斷。

## 0. 一句話

Chromatic 引擎改成 32 顆、Piano 與 FM 不動之後：月光舌鼓版搶音 **64 → 0**；Chromatic 32 顆（舌鼓、水鑼、自訂泛音三種子引擎）同時發聲時，一個 512 取樣區塊的 p99 只要 **1.3～1.7 ms、0 個區塊超過 10.667 ms 預算**，
比現行 16 顆 Piano 同時發聲（p99 **10.2～10.5 ms**、每輪 6～18 個區塊超預算）輕得多；Piano、Cimbalom、FM 三個引擎的輸出新舊**逐樣本相同**。四條判準全過，採用。

## 1. 先查的兩件事

| 問題 | 答案 | 出處 |
|---|---|---|
| 月光舌鼓版走哪個引擎 | **Chromatic**：外掛 `engine` 參數 = 1，子引擎 `chr_sub_engine` = 0（Tongue Drum），走 `chromaticSynth`（`ChromaticSound`／`ChromaticVoice`）。Cimbalom（0）與 Piano（3）共用 `cimbalomSynth`；FM Piano（2）用 `fmPianoSynth` | `tests/host_probe.cpp` Q09 案例表；`src/PluginProcessor.cpp` 三個 `addVoice` 迴圈 |
| pool 常數結構 | WF1003-V 把三個迴圈改成同一個 `kVoicePoolSize`。本卡拆成三個常數放進新檔 **`src/VoicePool.h`**：`TsukiVoicePool::kCimbalom=16`、`kChromatic=32`、`kFMPiano=16`；各有編譯參數覆寫（`TSUKI_VOICE_POOL_CIMBALOM/CHROMATIC/FM`，只為了能用舊版重跑證據；WF1003-V 的全域 `TSUKI_VOICE_POOL_SIZE` 仍可用）。標頭內有每個常數的出處註解（R4） | `src/VoicePool.h` |
| CLI 受不受影響 | **不會**。CLI target 只編 `src/cli/RenderApp.cpp`（`CMakeLists.txt:150-170`），`VoicePool.h` 只被 `PluginProcessor.cpp` 與 HostProbe 引用（`grep` 在 `src/cli`、`src/score`、`src/physics`、`src/dsp`、`src/engines` 找不到 `VoicePool`）。CLI 沒有因本卡重編；`build\TsukiSynthCLI.exe` sha256 前後同為 `51dbbb25…`（證據力弱，主證據是上面的原始碼引用檢查） | `wf1004_P_raw_cli_sha_before/after.txt` |

## 2. 判準（量測前寫好，原文見 `wf1004_P_criteria_preregistered.txt`）

| 編號 | 條件（全部成立才採用） |
|---|---|
| C1 | 月光舌鼓版搶音：舊版（全 16）須量到 64（重現 WF1002-C1／WF1003-V，否則停手），新版（Chromatic 32）須為 0。用「與真 VST3 逐樣本相同」的雙胞胎量 |
| C2 | Chromatic 32 顆滿載**不劣於**現行 Piano 16 顆滿載。滿載＝32 個不同音高（MIDI 36..67）按住 3 s；**涵蓋 Chromatic 全部三種子引擎**（Tongue Drum 12 模態、Water Gong 20 模態、Custom Harmonics 8 泛音振幅全 1.0），因為子引擎每顆成本不同。基線＝同一次 HostProbe 跑出的 Piano 16 顆滿載。每輪、每種子引擎都要：(a) 5 次重複的 p99 中位數 ≤ 基線；(b) 超預算區塊總數 ≤ 基線；真 VST3（含效果鏈）同樣兩式。嚴格，不留容差 |
| C3 | Piano／Cimbalom／FM 行為與輸出完全不變：真二進位 A/B（舊版全 16 vs 新版），三個引擎 × （12 音和弦、剛好 16 音、32 音溢出）逐樣本 max\|差\| = 0；另 HostProbe 雙胞胎(16)與新版 VST3 在給愛麗絲、壓力 Piano 逐樣本相同 |
| C4 | 既有測例不變：給愛麗絲新舊相同；Chromatic ≤16 顆測例新舊相同；HostProbe 預設（不設環境變數）PASS 數等於改前、FAIL 0；ctest 4/4；CLI 不受影響 |

「不劣於 Piano 16」是本卡的決策規則（月月「證據門檻制」的落實），不是 GATE 容差，不進 ROADMAP §6。沒有任何門檻數字是調出來的：32 來自裁決、16 是現狀。

## 3. 量了什麼、怎麼量

- 機器：AMD Ryzen 5 3500X（6 核）、Windows 10、MSVC Release。是開發機不是月月的 DAW 機；絕對毫秒會變，**同一輪裡 Chromatic-32 與 Piano-16 的比較**才是可帶走的部分。
- 兩個二進位：**舊版**＝本卡動手前從 repo 建出來的 VST3（HEAD `6198922` 原始碼，全 16，sha256 `12921524…`）；**新版**＝改完後建出來的 VST3（`c324cfc1…`）。**同一個 HostProbe** 對兩個 VST3 各跑 3 輪（舊、新交錯，`TSUKI_Q09V=1`，每輪約 5.7 分鐘），所以兩邊的雙胞胎計時是同一套程式。
- 搶音與計時沿用 WF1002-C1／WF1003-V 的「雙胞胎」法（程序內 `juce::Synthesiser`，接線與外掛建構子一模一樣）。本卡在 HostProbe 加了：產品雙胞胎改成各引擎的產品 pool 大小、固定 16／32 兩個證據雙胞胎與真 VST3 的逐樣本比對、兩個新壓力測例（水鑼、自訂泛音）。**沒有新增任何 CHECK**，預設跑法的判定不變。
- 真二進位 A/B：自寫的 `ab_probe`（原始碼存 `wf1004_P_ab_probe.cpp.txt`）載入單一 .vst3，離線渲染 20 個固定 MIDI 測例（含給愛麗絲全曲、月光舌鼓全曲）走真 `processBlock()` 與預設效果鏈，寫成 float32，`compare_ab.py` 逐樣本比。**正對照**：Chromatic 32 音溢出與月光（名稱帶 `_EXPECT_DIFF`）必須有差；**負對照**：舊版自己渲兩次必須全相同，證明渲染是確定性的、「0 差」有意義。

## 4. 數字

### 4-1 搶音（確定性，3 輪都一樣；舊版 vs 新版）

| 測例 | 最多同時幾顆 | 搶音：舊版（Chromatic 16） | 搶音：新版（Chromatic 32） |
|---|---|---|---|
| **月光舌鼓版（Chromatic）** | 20 | **64（4 次搶到還按著的音）** | **0** |
| 壓力 32 顆 Tongue Drum | 32 | 16 | 0 |
| 壓力 32 顆 Water Gong | 32 | 16 | 0 |
| 壓力 32 顆 Custom Harmonics | 32 | 16 | 0 |
| 壓力 32 顆 Piano（Piano 維持 16） | 32 | 16 | 16（不變） |
| 給愛麗絲（Piano） | 12 | 0 | 0 |

綁定二進位：舊版 VST3 與 twin(16) 逐樣本相同（max\|差\| = 0），新版 VST3 與 twin(32)（Chromatic）／twin(16)（Piano）逐樣本相同，3 輪全是 0。

### 4-2 處理時間（C2；新版三輪；ms／512 取樣區塊；預算 10.667 ms）

「雙胞胎」＝只有合成器、5 次重複的 p99 中位數與超預算區塊 5 次合計；「VST3」＝新版真二進位含整條效果鏈、一次完整重播的 p99 與超預算區塊數。

| 輪 | 測例（池大小） | 雙胞胎 p99 | 雙胞胎超預算 | VST3 p99 | VST3 超預算 |
|---|---|---|---|---|---|
| 1 | **基線 Piano 滿載（16）** | **10.39** | **18** | **10.78** | **5** |
| 1 | Tongue Drum 滿載（32） | 1.37 | 0 | 1.50 | 0 |
| 1 | Water Gong 滿載（32） | 1.69 | 0 | 1.71 | 0 |
| 1 | Custom Harmonics 滿載（32） | 1.65 | 0 | 1.76 | 0 |
| 2 | **基線 Piano 滿載（16）** | **10.19** | **8** | **10.59** | **3** |
| 2 | Tongue Drum／Water Gong／Custom（32） | 1.28／1.42／1.59 | 0／0／0 | 1.38／1.47／1.78 | 0／0／0 |
| 3 | **基線 Piano 滿載（16）** | **10.16** | **6** | **10.42** | **3** |
| 3 | Tongue Drum／Water Gong／Custom（32） | 1.28／1.41／1.60 | 0／0／0 | 1.38／1.53／1.68 | 0／0／0 |

平均（雙胞胎，3 輪範圍）：Tongue Drum 32 顆 0.43～0.46 ms（預算的 4%）、Water Gong 1.01～1.07 ms（約 10%）、Custom Harmonics 1.03～1.06 ms（約 10%）；Piano 16 顆 2.31～2.37 ms（約 22%）。
Water Gong（20 模態）是 Chromatic 裡每顆最貴的，32 顆也只有 Piano 16 顆的一半不到。

舊版（全 16）三輪的月光舌鼓版真 VST3：平均 0.27～0.28 ms、p99 0.43～0.47 ms、0 個超預算；新版：平均 0.31～0.32 ms、p99 0.47～0.50 ms、0 個超預算（最慢區塊 9.72／2.93／0.64 ms，第 1 輪那個 9.72 ms 是單次尖峰，見下）。

**誠實揭露的雜訊**：作業系統偶發尖峰會讓任何案例出現單一慢區塊，跟 pool 無關——例如新版第 1 輪給愛麗絲 VST3 有 4 個超預算區塊（最慢 23.1 ms）、第 2 輪 1 個（28.2 ms），舊版第 2 輪也有 1 個（14.2 ms）；給愛麗絲的輸出新舊逐樣本相同，Piano 路徑根本沒動。
新版第 1 輪月光雙胞胎 pool32 有 2 個超預算區塊（最慢 45.5 ms）也是這種尖峰（真 VST3 同輪 0 個）。這些**都不在 C2 的不等式裡**，C2 比的是 Chromatic-32 與 Piano-16 的 p99 中位數與超預算總數，Piano-16 自己每輪就有 6～18 個真超預算。

### 4-3 真二進位 A/B（C3、C4；舊版全 16 vs 新版；逐樣本）

| 測例 | max\|差\| | 判定 |
|---|---|---|
| Cimbalom：12 音和弦／剛好 16 音／32 音溢出 | 0／0／0 | 逐樣本相同 |
| Piano：12 音和弦／剛好 16 音／32 音溢出 | 0／0／0 | 逐樣本相同 |
| FM：12 音和弦／剛好 16 音／32 音溢出 | 0／0／0 | 逐樣本相同 |
| Chromatic Tongue Drum／Water Gong／Custom：12 音和弦 | 0／0／0 | 逐樣本相同（≤16 顆沒有附帶改變） |
| Chromatic Tongue Drum／Water Gong／Custom：剛好 16 音 | 0／0／0 | 逐樣本相同（pool 16 剛好夠，兩版都不搶） |
| 給愛麗絲全曲（Piano，6,356,480 取樣／聲道） | 0 | 逐樣本相同 |
| Chromatic 32 音溢出（三種子引擎；**預期有差**） | 0.65／0.91／5.19 | 有差（正對照；舊版搶音、新版不搶，從第 0 個取樣起就不同） |
| 月光舌鼓全曲（**預期有差**） | 2.47e-2 | 17.920 s 之前逐樣本相同，之後有差 |
| 負對照：舊版自己渲兩次，全 20 案 | 全 0 | 確定性成立 |

**R10 前後對照（月光舌鼓版，外掛層）**：舊 → 新，峰值 −10.955 → −10.948 dBFS，整首 RMS −27.239 → −27.237 dBFS；差異訊號本身 RMS −61.6 dBFS（相對舊版整首 RMS 低 34.3 dB）、峰值 −32.1 dBFS。
第一個不同的樣本在 17.920 s，正好是舊版第一次搶音的時間；之後被搶掉的音在新版會自然衰減而不被切斷。CLI 渲染（75 首 WAV）不受影響。

### 4-4 外掛層驗證（R6，X4 順序）

- 重建五個測試 target＋VST3：EXIT 0（`wf1004_P_raw_build_x4.log`）。
- `ctest --test-dir build -C Release`：**4/4 Passed**（`wf1004_P_ctest.txt`）。
- HostProbe 預設（不設環境變數）：改前（`wf1004_P_raw_prechange_default_hostprobe.txt`）**241 PASS／0 FAIL**，改後（`wf1004_P_raw_default_hostprobe.txt`）**241 PASS／0 FAIL**；兩份除了輸出資料夾路徑、H7 每次隨機產生的 preset ID 與 Q09 資訊行外逐行相同（`[PASS]` 行數都是 241、`[FAIL]` 都是 0）。Q09 資訊行現在兩種引擎各自報告：Piano「twin(16 voices = product pool) … steals = 0、最多 12」，Chromatic「twin(32 voices = product pool) … steals = 0、最多 20」。
- 六輪 `TSUKI_Q09V=1` 全跑 241／0（舊版 3、新版 3）。
- 全套（pytest、physics_verify --full、verify_score、75 首雜湊、位元不變 8/8、pluginval）依規劃放整合卡；本卡 CLI 原始碼沒動、沒有重編 CLI。

## 5. 對照判準

| 判準 | 結果 | 說明 |
|---|---|---|
| **C1 搶音 64→0** | **通過** | 舊版 twin16＝64（重現 WF1002-C1／WF1003-V），新版 twin32＝0；3 輪逐輪過 |
| **C2 Chromatic 32 滿載不劣於 Piano 16 滿載** | **通過** | 3 輪 × 3 種子引擎 × （雙胞胎 p99、雙胞胎超預算、真 VST3 p99、真 VST3 超預算）共 36 條不等式全成立，p99 差約 6～8 倍 |
| **C3 Piano／Cimbalom／FM 不變** | **通過** | 9 個真二進位測例逐樣本相同；twin(16) 與新版 VST3 在給愛麗絲／壓力 Piano 3 輪 max\|差\| = 0；負對照確定 |
| **C4 既有測例不變** | **通過** | 給愛麗絲相同；Chromatic ≤16 顆相同；HostProbe 241／0 與改前相同；ctest 4/4；CLI 原始碼未動 |

**結論：採用（Chromatic 32、Piano／Cimbalom 16、FM 16）。**

## 6. 沒量到／要知道的

1. **FM 引擎**：HostProbe 沒有 FM 雙胞胎，FM 負載在任何 pool 大小都沒量。FM 維持 16 不是「量過可以」，只是沒有證據要改（A/B 顯示 FM 輸出新舊逐樣本相同）。
2. **DAW 內與其他音軌同跑**、**記憶體**（多出 16 顆 Chromatic voice 的堆積量）、**開發機以外的機器**：沒量。32 顆 Water Gong 同時發聲平均約占預算 10%，在更慢的機器上比例會變大；Piano 16 顆本來就貼著預算（p99 約 10.2～10.5 ms／10.667 ms），這是 WF1003-V 已記下的既有狀況，與本卡無關。
3. 壓力測例是合成的（32 個不同音高同時按住 3 s），不是樂譜；它是 32 顆 pool 對單一引擎能提出的最大負載。
4. 順手看到（不是本卡要處理）：合成壓力測例的輸出峰值很高——Piano 16 顆約 +8 dBFS、Custom Harmonics（8 個泛音振幅全 1.0）16 顆約 +18.5 dBFS（`wf1004_P_raw_ab_index_baseline.txt`）。這是既有行為，新舊版相同，pool 大小無關；只是提醒壓力測例的音量不代表實際用法。
5. **前置假設與事實不符**：任務書說「B2b 卡剛改過 src（Body 上限），是預期改動別還原」，也說 `WF1004_decisions.zh-TW.md` 已由 B2b 建檔。實際上 B2b 稽核判 FAIL、已還原（`wf1004_B2b_audit.txt`），工作樹開工時 `git diff` 為空、決定檔不存在。本卡沒有動 B2b 的東西，只新建決定檔寫 P 一節（檔頭註明 B2b 重做時補在前面）。
6. **文件待整合卡同步**：`HANDOVER.md`（§0 的 V 卡列「按引擎分大小是另一個要裁的選項」、§1-5「要不要加大 pool 沒裁」）與 `TODO.md`（第 23、64 行）仍是 WF1003 的說法；本卡為避免與其他卡同時改這兩個檔衝突沒有動，請整合卡改成「WF1004-P：Chromatic 32／Piano 16／FM 16 已落地」。

## 7. 本卡改了什麼

- `src/VoicePool.h`（新）：三個按引擎的常數＋覆寫巨集＋出處註解。
- `src/PluginProcessor.cpp`：三個 `addVoice` 迴圈改用三個常數；檔頭註解與兩處「All 16 voices」註解改寫。
- `tests/host_probe.cpp`：Q09 產品雙胞胎按引擎分、`TSUKI_Q09V=1` 證據行擴充、新增水鑼／自訂泛音壓力測例；沒有新增 CHECK。
- `reports/wf0925_method/voice_pool_occupancy.py`：讀 pool 大小改從 `src/VoicePool.h` 取（原本用正規表示式抓迴圈裡的字面數字，會因此失效；已驗證能讀出 16／32／16）。
- 文件：`docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §10（標題、主張原句、第 1／5 點、新增第 8 點、檔尾補記）、`docs/KNOWN_LIMITS_INDEX.zh-TW.md` B4／C9、`ROADMAP.md` 骨架行、`reports/decision_packets/WF1004_decisions.zh-TW.md`（新建）。
- 證據：`reports/gate_outputs/wf1004_P_*`（判準、方法、原始 6 輪、A/B 比對、摘要、預改後預設 HostProbe、ctest、建置 log）。
- 暫存（repo 外）：`E:\Tsuki-project\_scratch\wf1004\P\`（舊／新二進位、ab_probe、A/B 的 .f32 輸出、各腳本）。
- **沒有 commit、沒有 git add**（R7）。
