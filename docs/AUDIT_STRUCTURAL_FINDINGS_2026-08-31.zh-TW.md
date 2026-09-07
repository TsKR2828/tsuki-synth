# 稽核問題點總整理（2026-08-31）

> 建立：2026-08-31　狀態：**診斷文件，不是施工卡**
> 對應證據：`reports/gate_outputs/stem_verify_fur_elise_run.txt`（1535 行，
> SHA256 `5FE00F7CD129CF3269B6D7A5A56E2E318FD6BCFCEA85581E03C1DF82BCFB91D3`）
> 對應修復：commit `a7413e5`（本地分支 `fix/deep-physics-audit-20260716`，未 push）
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
| 有沒有載入 IR | UI 問 `reverbIRName`（`src/PluginProcessor.h:76`） | 音訊問 `effectChain.hasImpulseResponse()`（`src/effects/EffectChain.h:103`） | 按鈕顯示 IR、實際跑 algorithmic；載入 preset 時兩個都沒更新（F-03） |
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
| F-03 IR user preset 不可重現 | plugin preset | ❌ HostProbe H5 只覆蓋 **DAW state** round-trip，不覆蓋 user preset |
| `getTailLengthSeconds()` 截尾 | plugin ↔ host 合約 | ❌ 無 |
| Pitch Glide 依 block size | plugin 音訊執行緒 | ❌ HostProbe 未注入變動 block size |
| K-03 超過 maxBlock 靜默換演算法 | plugin 音訊執行緒 | ❌ 同上 |
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

### 🔴 B. `getTailLengthSeconds()` 忽略物理模態尾音

見 §1 第三列。Tongue Drum 實測 T60 30.18 s，回報 2–3.45 s。
**建議另開一張施工卡**，不要混進 F-03（兩者都碰 reverb 欄位但成因無關）。

### 🟡 C. F-03 IR user preset 不自包含 — **等月月裁決**

決策單：`reports/decision_packets/F03_IR_PRESET_RECALL.zh-TW.md`
要決定兩件事：IR 資源怎麼跟著 preset 走（A 內嵌／B 受管理 IR 庫／C 資源參考，
建議 B）、IR 不見時怎麼表現（建議：音訊不中斷但強制切回 algorithmic ＋ 顯眼警告）。

### 🟡 D. schema 三份契約不同步（F-04 / F-05）

- C++ `--validate` 仍接受負 tempo、零拍號、負 rest、非法 kind、負 phrase
- generic MIDI converter 仍寫得出六項 schema 錯誤的 score

工程量最大的一項，適合獨立一輪。

### 🟡 E. K-02 / K-03 reverb

兩者都需要**先量化再裁定**，不能直接修：
- K-02：需要有代表性的 IR loudness corpus，才知道補償多少
- K-03：需要 DSP 測試（同一 IR、同輸入，maxBlock 與 maxBlock+1 不得靜默換演算法）

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
