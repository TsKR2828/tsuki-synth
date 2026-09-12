# WF0908-P3：F-03 落地 —— 受管理 IR 庫（B＋）＋ 缺檔三態 ＋ UI/音訊單一真相

> lane：C++　工兵：Sonnet（effort high）　共同規約：`WF0907_README.md`
> 依據：`reports/decision_packets/F03_IR_PRESET_RECALL.zh-TW.md` §7.1 / §7.2 / 裁決記錄（B＋、三態、兩條紅線）。
> 前置：WF0907-E10 的 H7（user preset round-trip，含 `KNOWN-FAIL(F-03)` 兩條）已在 HostProbe。

## 0. 一句話目標

使用者存了 IR 模式的 preset，隔天在任何 plugin instance 打開都聽到同一個 IR；找不到就大聲說、切回 algorithmic，**絕不靜默頂替、絕不 UI 說 IR 音訊走 algorithmic**。

## 1. 現況（R3 已複驗，行號以關鍵字重找）

- `src/PluginProcessor.h`：`reverbIRName`（UI 真相）、`getReverbIRName()/hasReverbIR()`；`.cpp` `loadImpulseResponse(file)` 設 `effectChain.loadImpulseResponse` 與 `reverbIRName`。
- `src/effects/EffectChain.h`：`loadImpulseResponse`、`clearImpulseResponse()`（**目前沒人呼叫**）、`hasImpulseResponse()`（音訊真相）。
- `src/PresetManager.h`：`saveUserPreset(name, allowOverwrite)`、`loadPreset(index)`、user preset 存 `%APPDATA%`（**先讀確認實際路徑與格式**）。
- `src/PluginEditor.cpp`：IR 顯示、`.wav`/`.json` 共用 Load 鈕（稽核文件提到的心智模型混淆，本卡順手分開）。
- `tests/host_probe.cpp` H7。
- 退回 algorithmic 有 0.15× 增益差（K-02，WF0907-E7 量化中）：本卡**只在警告文字講明音量會變**，不補係數。

## 2. 設計

### 2.1 `src/IRLibrary.h`（新）
- 目錄：`<user preset 同層>/IR/`；檔名 = `<sha256 前 32 碼>.wav`；旁邊 `<同名>.json` 記 `{original_name, sha256, sample_rate, channels, imported_at}`。
- API：`importFile(File) -> IRRef{sha256, originalName}`（複製＋去重）、`resolve(IRRef) -> File`（找不到回空）、`list()`。
- 工廠 IR：目前**沒有**工廠 IR（確認 `data/` 與 BinaryData）；預留 `IRRef.kind = user|factory`，factory 用 `id` 欄位，本卡不實作工廠內容。

### 2.2 preset 內容
- user preset 新增區塊 `reverb_ir: {kind, sha256, original_name}`；沒有 IR 時整個區塊不存在。
- DAW state（`getStateInformation`）同樣寫入同一區塊（現況 DAW state 走哪條路先讀 `PluginProcessor.cpp` 的 state 區）。

### 2.3 載入三態（Waves IR-1 對照，§7.2）
| 情況 | 行為 |
|---|---|
| resolve 成功且 sha256 吻合 | 載入；UI 顯示 original_name |
| 找不到，使用者在 GUI 指了別的檔 | 載入該檔；UI 在名稱旁標「與 preset 存的不是同一個 IR」；preset 標 dirty |
| 找不到，且無 GUI 互動（DAW 自動載入） | **模式強制切回 algorithmic**、`effectChain.clearImpulseResponse()`、UI IR 欄顯示「未載入：<original_name>」＋一次性警告（含「音量會與 IR 模式不同」字樣）；**不可靜音、不可沿用 instance 既有 IR** |

### 2.4 單一真相
- 刪掉「UI 問 `reverbIRName`、音訊問 `hasImpulseResponse()`」的雙軌：processor 提供 `IRStatus getIRStatus()`（`{loaded, name, mismatch, missing}`），UI 只讀它；`loaded` 直接取自 `effectChain.hasImpulseResponse()`。
- `loadPreset` / `setStateInformation` 一開始**先 clear IR**，再依區塊決定載入（防止沿用前一個 IR）。

### 2.5 HostProbe H7 翻成硬 CHECK（前置：WF0908-E10b 已建好選項 B 的 harness）
- H7 harness 現況（E10b）：SAVE 側 = 影子 APVTS（`src/ParameterLayout.h`）+ 真 `PresetManager::saveUserPreset()`；LOAD 側 = 真 VST3 實例 `setCurrentProgram()`。
  **IR 資訊不在 APVTS 裡**，所以 SAVE 側要讓 `PresetManager` 能收一個「附加區塊」（`reverb_ir` 區塊由 processor 提供；影子測試直接餵 `IRRef`）——設計時把 preset 序列化改成「APVTS state + 可選附加 ValueTree」，processor 與影子測試走同一個序列化函式。
- 三情境：吻合／缺檔無 GUI（預期 algorithmic + missing 旗標）／指了別的檔（預期 mismatch 旗標；此情境在無 GUI 的 HostProbe 用「resolve 失敗後由測試改寫 IR 庫索引指向另一檔」模擬）。移除 `KNOWN-FAIL(F-03)` 標記。
- 新增：`getIRStatus().loaded == effectChain.hasImpulseResponse()` 在所有情境恆成立（紅線二的機器檢查）；VST3 實例側用 `getStateInformation()` 讀回的 state 檢查 `reverb_ir` 區塊與 IR 狀態一致。

## 3. 步驟
1. 讀上列檔案；證據檔開頭寫「user preset 實際路徑、DAW state 現況、Load 鈕現況」。
2. 實作 2.1–2.4；UI 把 IR Load 與 preset Load 分成兩顆鈕（最小改動，不重設計版面——UI 重做另有計畫）。
3. 2.5；建 VST3 + HostProbe（build-wf）；跑 HostProbe 全 PASS。
4. CLI 不用 IR：位元不變 8/8 + `--full`（碰了 `src/effects`）+ ctest（X4）。
5. `docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.zh-TW.md` §1 第二列與 §4-C 標已修；F03 裁決包 §8 補「落地記錄」。

## 4. 禁止
- 不補任何響度係數；不改 SimpleReverb；不刪使用者既有 IR 檔；不新增 CMake target（測試進 host_probe）。

## 5. GATE（`reports/gate_outputs/wf0908_P3_f03.txt`）
1. HostProbe 全 PASS，三情境輸出逐條貼。2. 8/8 IDENTICAL、`--full` NO CHECKED FAILURES、ctest 全綠。3. `python -m pytest tests -q` 全綠。
4. `git diff --stat` 只含 `src/IRLibrary.h`、`src/PresetManager.h`、`src/PluginProcessor.{h,cpp}`、`src/effects/EffectChain.h`、`src/PluginEditor.{h,cpp}`、`tests/host_probe.cpp`、`CMakeLists.txt`（僅為加新 header，若需要）、稽核文件、裁決包、證據檔。
