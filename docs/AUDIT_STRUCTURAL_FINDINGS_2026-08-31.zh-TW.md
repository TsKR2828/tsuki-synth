# 稽核問題點總整理（2026-08-31）

> 建立：2026-08-31　狀態：**診斷文件，不是施工卡**
> 對應證據：`reports/gate_outputs/stem_verify_fur_elise_run.txt`（1535 行，
> SHA256 `5FE00F7CD129CF3269B6D7A5A56E2E318FD6BCFCEA85581E03C1DF82BCFB91D3`）
> 對應修復：commit `a7413e5`（本地分支 `fix/deep-physics-audit-20260716`，未 push——2026-08-31 當時；之後已 push 並併入 `main`）
>
> **這份文件的目的**：codex 兩輪稽核列出的是「缺陷清單」。清單會讓人以為
> 問題是「還剩 N 個 bug」。實際上這些缺陷高度集中在三個結構性病根上，
> 修完清單而不動病根，下一輪還會長出同型的新缺陷。
>
> **本文所有 file:line 都是我自己回原始碼複驗過的**，不是轉述稽核報告。
> 凡是我沒複驗或複驗結果與稽核不同的，都在 §5 明確標示。

---

## 1. 病根一：同一個事實寫在兩個地方，然後漂移

這個模式在稽核裡重複出現了四次。每一次的症狀看起來完全不同，
但成因是同一個：**一件事實有兩份實作，沒有單一真相來源。**

| 同一件事實 | 地方 A | 地方 B | 症狀 |
|---|---|---|---|
| 什麼是合法 score | `scores/schema/score.schema.json` | C++ `--validate`（`src/score/ScoreParser.h:942`）＋ Python converter（`tools/midi_to_tsukisynth.py:1136-1171`）——**共三份** | `--validate` 說 VALID、schema 報 2 錯；converter 寫得出 6 個 schema 錯誤的檔（F-04 / F-05） |
| 有沒有載入 IR | UI 問 `reverbIRName`（`src/PluginProcessor.h:76`） | 音訊問 `effectChain.hasImpulseResponse()`（`src/effects/EffectChain.h:103`） | 按鈕顯示 IR、實際跑 algorithmic；載入 preset 時兩個都沒更新（F-03）——**已修（WF0908-P3）**：`getIRStatus().loaded` 直接等於 `effectChain.hasImpulseResponse()`（同一個欄位，非兩個變數），UI 只讀這一個函式，見 §4-C |
| 這個聲音有多長 | 物理引擎的模態衰減（Tongue Drum 實測 T60 30.18 s） | `getTailLengthSeconds()` 的 base＝`max(2.0, fmRelease)`，`fmRelease` 來自 **FM Piano 的 release 參數**（`src/PluginProcessor.cpp:403-412`） | Host 收到 2–3.45 s，DAW bounce/freeze 截尾 |
| wet 的增益標度 | algorithmic wet 額外乘 `0.15`（`src/effects/SimpleReverb.h:155`） | convolution wet 直接以 `m` 混合，**沒有** 0.15（`src/effects/EffectChain.h:204`） | 切模式會跳響度；「靜默退回 algorithmic」不是溫和降級（K-02） |

**最值得注意的是第三列。** `getTailLengthSeconds()` 問的是一個**完全不同引擎**的
包絡參數。物理引擎的模態衰減從頭到尾沒有參與過這個計算——不是算錯，是**根本沒接線**。

### 這條病根的處方

不是逐條修，是讓每個事實只有一份可執行的定義：
- score 合法性 → 三方共用同一份可執行契約（cross-validator suite）
- IR 狀態 → UI 與音訊讀同一個來源，preset 載入時強制收斂
- 尾音長度 → 由引擎自己回報，不要從別的引擎的參數推
- wet 標度 → 先量化，再決定補償或統一

---

## 2. 病根二：驗得最兇的地方，不是使用者用的地方

**CLI 渲染路徑**驗證密度極高：位元決定性、corpus 73/73、L1/L2/L3a 三層旋律 GATE、
跨平台容差阻斷式、ASan、177→212 pytest、4/4 ctest。

**但這兩輪的商品級缺陷，全部落在另一半**——plugin / DAW / preset / host 那一側。

| 缺陷 | 落在哪一層 | 現行 GATE 有沒有覆蓋 |
|---|---|---|
| F-03 IR user preset 不可重現 | plugin preset | ✅ 已修（WF0908-P3）：HostProbe H7 三情境（吻合／缺檔無 GUI／內容不符）全部 CHECK 化，見 §4-C |
| `getTailLengthSeconds()` 截尾 | plugin ↔ host 合約 | ✅ HostProbe H8（WF0907-E5）已覆蓋 |
| Pitch Glide 依 block size | plugin 音訊執行緒 | ✅ HostProbe H6（WF0907-E10）已注入變動 block size {64,256,512,1024,4096}；哨兵旋律 5 個 size 位元相同（melody_verify 5/5 PASS）。water_gong+Pitch Glide 巨集拉滿原本另有 informational block-size delta（明顯非雜訊層級，未深究成因）——已根治（WF0908-E10b）：`ChromaticEngine.h::renderNextBlock()` 的 glide phase 推進 + `resonator.scaleFrequencies()` 改成逐取樣（原本逐 block 一次），4 個 block size 現在同樣 0 LSB（位元相同），CHECK 已由 informational 硬化為必過項，見 `EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §10.1 |
| K-03 超過 maxBlock 靜默換演算法 | plugin 音訊執行緒 | ✅ `TsukiSynthAuditTest`/ctest（WF0907-E7，非 HostProbe）已覆蓋分塊處理 |
| F-01 / F-02 工具刪資料 | 開發者工具 | ❌ 沒有人測過「caller 自帶的非空輸出目錄」 |

**所以「全綠」曾經反覆地不等於「正確」**：稽核當時 177 passed、ctest 3/3、
ASan 3/3、HostProbe 0 failures，同時 preset 不可重現、bounce 會截尾、
驗證工具會刪使用者資料。

### 這一輪自己也踩了同一個坑（值得記住）

第一輪修 F-01/F-02 時，我們**新寫的守門碼本身沒有被當成攻擊面再驗一次**，
於是自己種了一個 P1 進去：

- containment 檢查放行了 `resolved == out_dir`，指回 `--emit` 根目錄自身的
  symlink/junction 配 `--force-clean` 會刪掉整個 emit 根目錄，**並且仍回報成功**。
  已對 pre-fix 複本實測：`emit-root survived = False`。
- `stem_verify` 的 containment 只在 `--force-clean` 與收尾兩條路徑上，
  **既存但為空**的 `stems`／`reference` symlink 完全沒檢查，WAV 會寫到
  `--out-dir` 之外。已對 pre-fix 複本實測：空目標時一路穿過所有守門到 CLI 查找。

兩者都已在 `a7413e5` 修掉並加哨兵測試。

**另一個測試設計陷阱**（同輪學到）：第一版 symlink 測試在連結目標裡放了哨兵檔，
結果**舊碼因為別的理由**（撞到「非空 stems」那道舊閘）也擋下來了——
測試看起來有效，其實沒打中。改成**空目標**才命中真正的逃逸路徑。
教訓：寫回歸測試後，必須實際拿舊碼跑一次確認它會紅。

---

## 3. 病根三：CLI 出貨路徑乾淨，所以自己不會踩到

月月自己賣的成品是 CLI 渲染的，那條路是驗到位元的，**不受上述缺陷影響**。

但商品的另一半如果是 VST3 plugin，顧客碰到的就是 §2 那一整排。
這是為什麼稽核用「商品 recall blocker」這個詞——缺陷不會出現在自己的日常流程裡，
只會出現在顧客那裡。

---

## 4. 目前未修項目（按「會不會傷到顧客」排）

### 🔴 A. Pitch Glide 最終音高依 host block size

`src/engines/ChromaticEngine.h:452-466`。

程式碼註解說「glide rate is independent of host buffer size」——**這句是對的**，
速率確實有按 block 長度縮放（`glidePhase += glideAmount * 0.15f * numSamples / sr`）。

問題在 `if (glidePhase < 0.5f)` 這個**上限判斷是逐 block 做的**：
phase 一格一格跳，跳到哪一格才越過 0.5 取決於 buffer 粒度，越過後就凍在那個值。
8192 samples 一格 ≈ 0.0256 phase ≈ 0.77 % 頻率 ≈ **約 13 cents**
（稽核測得最壞 15.57 cents，同一量級）。

**顧客換一個 buffer size，最終音高就變了。**
對一個 pitch 驗到 0.4 cent 的物理建模合成器，這是最傷招牌的一條。
修法方向：cap 要在**取樣層級**處理（把超出的部分夾住而非整格丟棄），不是逐 block 比對。

### ✅ B. `getTailLengthSeconds()` 忽略物理模態尾音 — 已修（WF0907-E5）

見 §1 第三列。Tongue Drum 實測 T60 30.18 s，回報 2–3.45 s。
修法：`CimbalomEngine.h` / `ChromaticEngine.h` 各新增 `worstCaseTailSeconds()`
（對目前參數狀態在 MIDI 21..108 逐音呼叫與 `startNote()` 相同的模態建構路徑，
取所有模態 `decayTime` 最大值，訊息執行緒上以參數值雜湊快取），
`PluginProcessor::getTailLengthSeconds()` 改回報
`max(FM envelope 估計, 目前選用引擎的 worstCaseTailSeconds()) + delay/reverb 尾巴`，
並移除原本無可溯源理由的 300 s 上限。詳見
`docs/workcards/WF0907_E5_plugin_truth_source.md`。

### ✅ C. F-03 IR user preset 不自包含 — 已修（WF0908-P3）

決策單：`reports/decision_packets/F03_IR_PRESET_RECALL.zh-TW.md`（§8 裁決記錄：
問題一 B＋受管理 IR 庫＋工廠／使用者分流；問題二強制切回 algorithmic ＋警告，
照 Waves IR-1 拆三態）。

落地：`src/IRLibrary.h`（新，內容雜湊定址的受管理 IR 庫，`%APPDATA%/TsukiSynth/IR/`）
＋ `TsukiSynthProcessor::getIRStatus()`（單一真相：`loaded` 就是
`effectChain.hasImpulseResponse()` 本人，不是第二個會漂移的變數）＋三態載入
（`restoreReverbIR()`／`tryLoadIRRef()`：吻合直接載入；找不到就強制切回
algorithmic＋一次性警告，絕不沿用 instance 既有 IR；resolve 到但內容雜湊對不上
就照樣載入並標記「不是同一個 IR」，不靜默頂替）。preset／DAW state 序列化改成
「APVTS state ＋ 可選附加 ValueTree」（`PresetManager::getExtraStateBlock`／
`applyExtraStateBlock`，`PresetManager` 本身仍不知道 IR 是什麼）。
HostProbe H7 三情境全部 CHECK 化，`KNOWN-FAIL(F-03)` 標記已移除。
詳見 `docs/workcards/WF0908_P3_f03_ir_library.md`。

### ✅ D. schema 三份契約不同步（F-04 / F-05）— 已修（WF0907-E8）

- C++ `--validate` 仍接受負 tempo、零拍號、負 rest、非法 kind、負 phrase
- generic MIDI converter 仍寫得出六項 schema 錯誤的 score

工程量最大的一項，適合獨立一輪。

修法：`ScoreParser.h::validateSimpleObjectArray` 從「只查鍵名/必填/型別」擴充成吃
每欄位的 `SimpleFieldSpec`（minimum/exclusiveMinimum/integer/enum），逐欄鏡射
`scores/schema/score.schema.json` 對 `tempo_map`/`time_signatures`/`rests`/`phrases`
的界限——只拒絕 schema 也拒絕的東西，不比 schema 更嚴。`tools/midi_to_tsukisynth.py`
的 `write_score()` 現在在既有 renderer-timing 檢查之前先跑一次
`Draft202012Validator`（`schema_errors()`），非法輸出一律 `raise`、不落地。

新的交叉驗證單一真相：`tests/test_schema_contract_sync.py` 從一個 schema-valid
fixture 出發，**走訪** schema 本身的 `minimum`/`maximum`/`exclusiveMinimum`/
`enum`/`pattern`/`required`/`type`/`oneOf`，對每一條產生突變體（388 個），
逐一比對 `jsonschema` 判定 vs `TsukiSynthCLI --validate` exit code——修前
22/388 不一致（全部在 tempo_map/time_signatures/rests/phrases），修後 0/388。
`tests/test_score_vs_midi_verify.py::ConverterSchemaContractTests` 額外證明
converter 對 repo 內每一份來源 MIDI 的 `convert` 輸出 jsonschema 0 errors，
以及 F-04 原始 6-錯誤 repro 現在會被 `write_score()` 拒絕而不寫檔。
證據：`reports/gate_outputs/wf0907_E8_schema.txt`、
`reports/gate_outputs/wf0907_E8_corpus_validate.txt`（corpus 75/75 VALID）、
`reports/gate_outputs/wf0907_E8_convert_gate3.txt`。詳見
`docs/workcards/WF0907_E8_schema_contract_sync.md`。

### ✅ E-1. K-03 超過 maxBlock 靜默換演算法 — 已修（WF0907-E7）

`EffectChain::processBlock()` 原本在 `numSamples > maxBlock` 時，`irMode` 的
`numSamples <= maxBlock` 守衛會直接失效，使用者已載入 IR 也會**靜默退回
algorithmic reverb**——不是溫和降級，是換了一整條訊號路徑而不告知。

修法：`processBlock()` 開頭偵測 `numSamples > maxBlock`，以 `maxBlock` 為步長
切成子 block（`juce::AudioBuffer` 的非擁有 sub-view 建構子，不在音訊執行緒配置
記憶體），對每個子 block 遞迴呼叫同一個 `processBlock()`，不新增任何分支邏輯。
`tests/audit_repro.cpp::testEffectChainOversizedBlockMatchesExternalChunking()`
證明：(a) IR 模式下一次 1537-sample 呼叫（觸發內部自動分塊）與外部手動
512+512+513 三次呼叫**位元相同**；(b) 同一檢查在 ALGO 模式下也成立；
(c) 在測試裡模擬「分塊邊界丟掉 1 個輸入樣本」的 mutant，證明 (a)/(b) 的位元比對
確實會抓到這類差異（有牙齒，不是空比對）。8/8 corpus 位元不變、
`physics_verify --full` NO CHECKED FAILURES、`pytest` 249 passed。
證據：`reports/gate_outputs/wf0907_E7_reverb.txt`。詳見
`docs/workcards/WF0907_E7_reverb_k02_k03.md`。

### 🟡 E-2. K-02 ALGO/IR wet 增益差 — 已量化，**等月月裁決**

`SimpleReverb.h:155-156` 的 ALGO wet 額外乘 `0.15`，`EffectChain.h` 的 IR
convolution wet 混合沒有這個因子（file:line 已在裁決包核實）。實測（48 kHz、
2 s 固定種子白噪、mix=1.0、IR 用與 ALGO 同 T60 的合成指數衰減白噪重建）：
ALGO 穩態 wet RMS = **1.857 dBFS**，IR = **−26.626 dBFS**，實測差
**−28.483 dB**（IR 更小聲）——方向與量級都跟「只算 0.15 因子」的理論值
`20·log10(1/0.15) = 16.478 dB` 對不上，因為摺積 IR 的固有能量正規化與
comb 回饋式 reverb 的穩態增益是完全不同的物理量，T60 對齊不保證響度對齊。
三個選項（A 讓 IR 也乘 0.15／B 拿掉 ALGO 的 0.15／C 維持現狀＋文件標註）與
各自的 Rule 10 衝擊：`reports/decision_packets/K02_reverb_wet_scale.zh-TW.md`。
不修 DSP，等待裁決。

### 🟢 F. `keep_stems=False` 遇到既存空 stems 目錄會保留輸出

這是 F-01 修復的**刻意副作用**，不是新 bug：
`stems_dir_ours_to_delete = not stems_dir_preexisted`——本次沒建立的目錄一律不刪。
保守方向正確（寧可留檔也不誤刪），但行為與旗標字面意思不完全一致，
文件應該講清楚。

### 🟢 G. 新測試檔尚未接進 CI — **等月月裁決**

`.github/workflows/physics.yml:61-65` 是逐檔白名單。
`test_crossplatform_emit_safety` / `test_midi_type0` / `test_render_app_filename_safety` /
`test_stem_verify` 都不在名單裡，等於這些哨兵只活在本機。

**這不是「補一行」**：`pytest` 與 `mido` 都不在 `tools/requirements-physics.txt`
（目前只有 numpy / scipy / jsonschema），要接 CI 就得動 pinned 依賴。
需要月月決定。

---

## 5. 我複驗後與稽核判斷不同 / 尚未複驗的項目

**誠實標註，避免這份文件變成第二手轉述。**

### ❗ 「Custom Harmonics 與一般 Chromatic 控件 visibility/layout 打架」— 我無法重現

稽核列為 P2。我實際追了程式路徑，**結論與稽核不同**：

- 可見性在 `src/PluginEditor.cpp:413` 算 `isCustom = isChr && (chrSub == 2)`
- 版面在 `src/PluginEditor.cpp:1246` 算 `chrCustom = (eng == 1 && chrSub == 2)`
- 兩者都源自同一個 `currentEngine()` 與同一個 `chr_sub_engine` 參數
- `chr_sub_engine` 的 listener（`src/PluginEditor.cpp:350-361`）**同時**呼叫
  `updateEngine()`（可見性）與 `resized()`（版面）

也就是說可見性與版面是一起更新的，我看不到它們會不同步的路徑。

**但這裡確實有病根一的味道**：同一個「是否為 Custom 模式」的判斷式被寫了兩份。
目前兩份一致，屬於**漂移風險**而非現行缺陷。建議抽成單一函式，但不必當 P2 修。

**已抽成單一函式（WF0907-E5）**：`TsukiSynthEditor::isCustomHarmonicsMode()`
（`src/PluginEditor.h`/`.cpp`），`:413` 與 `:1246` 兩處都改呼叫它，純重構、
條件式不變。

### ❗ 「glide、exciter 仍可能暗中影響 Custom 聲音」— 措辭我不同意

`chrGlide` / `chrExciter` 在 `src/PluginEditor.cpp:409-411` 對整個 Chromatic
（含 Custom）都是 `setVisible(..., isChr)`，**旋鈕是看得見的**，所以不是「暗中」。

實情是：`ChromaticEngine.h:455` 的 glide 只要 `glideAmount > 0.01` 就套用，
不分 sub-engine，儘管註解寫的是「Water gong pitch glide」。
**這比較像是「跨 sub-engine 生效是否為設計意圖」的問題**，需要月月確認產品意圖，
而不是一個可以直接修的 bug。

### 尚未複驗

- 稽核的 ASan / HostProbe / `physics_verify --full` 全綠結果（我只複驗了
  pytest 212 passed 與 ctest 4/4，那是修復後的數字）
- 「大型輸入缺全域資源上限」（K-05）、「部分 verifier subprocess 沒有 timeout」
  剩餘範圍（K-06 已修 physics_verify 3 處 + check_piece_consonance 1 處）

---

## 6. 一句話結論

> **已修完的那批是症狀，沒修的那批也是症狀。**
> 真正的問題是：**驗證鏈的形狀對準了 CLI，而缺陷長在 plugin 那一側；
> 加上系統裡到處都有兩份不同步的真相。**

修完 §4 的清單只是把這一輪的症狀清掉。要讓下一輪不再長出同型缺陷，
需要處理的是 §1 的單一真相來源，與 §2 的 GATE 覆蓋形狀。

---

## 附錄：卡在裁決 vs 可直接開工

**需要月月決定（4 項）**
1. F-03：IR 資源方案 A／B／C
2. F-03：IR 不見時的行為
3. CI：要不要把 `pytest` + `mido` 加進 `tools/requirements-physics.txt` 以接上新測試
4. 四季／月光換源重製排程（沿用先前待辦，與本輪稽核無關）

**不需要裁決、可直接開工（依建議順序）**
1. Pitch Glide 的 cap 改成取樣層級（§4-A，最傷商品形象）
2. `getTailLengthSeconds()` 接上引擎自報尾音（§4-B）
3. schema 三份契約統一（§4-D，工程量最大）
4. K-02 / K-03 的量化測試（§4-E，量完才能裁定修法）
5. Custom 模式判斷式抽成單一函式（§5，防漂移，順手）
