# WF0908-E10b：水鑼 glide 逐 block 階梯修正 ＋ H7 user preset harness（選項 B）＋ H6 入庫

> lane：C++　工兵：Sonnet（effort high）　共同規約：`WF0907_README.md`
> 依據：`reports/gate_outputs/wf0907_E10_hostprobe.txt` H6 補充段（water_gong glide=1.0：block 4096 vs 64 RMS delta **+2.63 dB re signal**，一般旋律則 −217 dB＝位元相同）；
> `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §10.2 三選項 → **規劃者裁決選 (B)**（2026-09-09）。

## 0. 一句話目標

1. 水鑼 pitch glide 的**頻率更新改成逐取樣**（或等價的逐取樣內插），讓 glide 曲線不再是「block 長度的階梯」；修完 H6 的水鑼補充測試要從 informational 轉成硬 CHECK（判準沿用 H6 一般旋律已達到的「位元相同」——不是新容差，是既有 H6 主張的延伸）。
2. H7 依選項 B 建 harness：`createParameterLayout()` 抽到 `src/ParameterLayout.h`（無 GUI include），HostProbe 建影子 APVTS + 真 `PresetManager` 呼叫真 `saveUserPreset()`；LOAD 側用真 VST3 實例 `setCurrentProgram()`。
3. E10 已做好的 H6 程式碼（`tests/host_probe.cpp` unstaged 部分）一併納入本卡稽核與 stage。

## 1. 現況（規劃者已核實）

- `src/engines/ChromaticEngine.h` `startNote`/render 路徑附近：`glidePhase += glideAmount * 0.15f * numSamples / sr`，之後一次 `resonator.scaleFrequencies(...)`——**每 block 一次**。`cdf2017` 只修了「最終音高的 cap」，沒修「軌跡逐 block 量化」。
- CLI `ScoreRenderer` 的音對音滑音是逐取樣算的（`cdf2017` 記錄），與 plugin 這條路無關 → 本卡預期 **CLI 位元不變 8/8**。
- `tests/host_probe.cpp`：H6 已實作（5 種 block size，一般旋律 melody_verify 5/5 PASS、位元相同；水鑼 glide 補充段 informational）；H7 目前印 `[BLOCKED]`。
- `PresetManager.h` header-only，只需要 `AudioProcessorValueTreeState&`。`createParameterLayout()` 目前在 `PluginProcessor.cpp`（先 grep）。
- `CMakeLists.txt` HostProbe target（約 L260-270）：link 清單要加 `ParameterLayout.cpp`（若抽成 .cpp）；**不要**把 PluginEditor 拉進來。

## 2. 設計

### 2.1 glide 逐取樣
- 在 voice 的 render 迴圈內，每個取樣（或每 N≤16 取樣，若效能需要——但 N 必須是常數且與 host block 無關，並在註解寫明「與 block size 無關」）更新 glide phase 並呼叫 `scaleFrequencies`；若 `scaleFrequencies` 太貴，改為只更新相位增量（等價數學），證明方式：兩種實作在 block=64 下位元相同。
- cap 邏輯（`cdf2017`）保留；`glideAmount` 語意不變。
- 只動 plugin 的 `startNote`/`renderNextBlock` 路徑；CLI `noteOn()` 變體不碰。

### 2.2 H7 harness（選項 B）
- 新檔 `src/ParameterLayout.h`（+ `.cpp` 若需要）：`juce::AudioProcessorValueTreeState::ParameterLayout createTsukiParameterLayout()`；`PluginProcessor.cpp` 改呼叫它（純搬移，**參數 id/範圍/預設一字不改**——用 HostProbe H2 的參數清單 dump 前後比對證明）。
- HostProbe H7：
  1. 影子 `juce::AudioProcessor`（最小 dummy processor）+ APVTS(layout) + `PresetManager`；設 ≥10 個非預設參數；`saveUserPreset("wf0908_h7", true)`。
  2. 真 VST3 實例 B：掃 `getNumPrograms()/getProgramName()` 找到 `wf0908_h7`，`setCurrentProgram()`；比對 B 的每個參數值與影子 APVTS 位元相同。
  3. IR 兩條 CHECK 維持 `KNOWN-FAIL(F-03)`（P3 會翻硬）。
  4. 清理 `deleteUserPreset`；證據檔寫 preset 目錄。
- 誠實標註：SAVE 側測的是真 `saveUserPreset()` 對影子 APVTS；LOAD 側是真 plugin 實例。

### 2.3 H6 硬化
- 水鑼 glide=1.0 補充段改為 CHECK：各 block size vs 64 的 max|delta| 必須 = 0 LSB（與一般旋律段同一判準）。修好 2.1 才會過；修不到位元相同（例如浮點累加順序差）→ 回報實際數字並 **status=RED**，不得改成容差。

## 3. 步驟
1. build-wf baseline 8/8。2. 實作 2.1 → HostProbe H6 硬化跑過。3. 實作 2.2 → H7 PASS（含 KNOWN-FAIL 兩條）。
4. 三 target + 五測試 target（X4）+ ctest + `--full --cli build-wf...` + 8/8 IDENTICAL（碰了 `src/engines`）。5. H2 參數清單前後 diff 為空。
6. 設計文件 §10.1 加「已硬化」、§10.2 加「裁決記錄：選 (B)，已落地」；稽核文件 §2 表格更新。

## 4. 禁止
- 不改 glide 的 cap 值、`0.15f` 速率常數、`glideAmount` 範圍；不新增容差；不把 PluginEditor link 進 HostProbe；不改 CLI 渲染路徑。

## 5. GATE（`reports/gate_outputs/wf0908_E10b_glide_h7.txt`）
1. HostProbe 全 PASS（H6 水鑼段 0 LSB ×4、H7 參數 round-trip PASS、KNOWN-FAIL(F-03) ×2）。2. 8/8 IDENTICAL、`--full` NO CHECKED FAILURES、ctest 全綠。3. H2 參數清單前後相同。4. `python -m pytest tests -q` 全綠。
5. `git diff --stat` 只含 `src/engines/ChromaticEngine.h`、`src/ParameterLayout.{h,cpp}`、`src/PluginProcessor.{h,cpp}`、`tests/host_probe.cpp`、`CMakeLists.txt`、設計文件、稽核文件、證據檔。
