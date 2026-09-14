# WF0907-E5：`getTailLengthSeconds()` 接引擎自報尾音 + Custom 判斷式單一化

> lane：C++　工兵：Sonnet　先讀 `WF0907_README.md`（**本卡是 C++ lane 第一張：由你建立 `build-wf`**）
> 依據：`docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.zh-TW.md` §1 第三列、§4-B、§5 第一項。

## 0. 一句話目標

Host 問「這個聲音有多長」時，答案要來自**物理引擎自己的模態衰減**，不是 FM Piano 的 release 參數。
順手把 PluginEditor 裡寫了兩份的「是否 Custom Harmonics 模式」抽成一個函式。

## 1. 現況（規劃者已核實）

- `src/PluginProcessor.cpp:403-430` `getTailLengthSeconds()`：`base = max(2.0, fmRelease)`，`fmRelease` 來自 `pFMRelease`（FM Piano 參數），
  再加 delay 尾巴。**物理引擎的 T60 從頭到尾沒參與**。Tongue Drum 實測 T60 30.18 s，回報 2–3.45 s → DAW bounce/freeze 截尾。
- 引擎的模態 T60 來源：`CimbalomEngine.h:239/301/518` 呼叫 `StringModel::decayTimeForFrequency(...)`；
  `ChromaticEngine.h:210/346` 呼叫 `decayTimeForMode()`(L567) → `BeamModel::/PlateModel::decayTimeForFrequency`。
  `ModalResonator::Mode::decayTime` 定義為 **T60**（`ModalResonator.h:94-96`）。
- **這些引擎檔同時被 CLI `ScoreRenderer` 使用**——任何重構都必須證明 CLI 渲染位元不變（README §3）。
- Custom 判斷式兩份：`src/PluginEditor.cpp:413` `isCustom = isChr && (chrSub == 2)`；`:1246` `chrCustom = (eng == 1 && chrSub == 2)`。
  兩者的 listener 在 `:350-361` 同時呼叫 `updateEngine()` 與 `resized()`，目前一致，屬漂移風險。

## 2. 設計（照做，不要重新發明）

### 2.1 尾音

- 每個物理引擎新增 `double worstCaseTailSeconds() const`：對**目前參數狀態**（材質、子引擎、幾何/尺寸、damping macro 等所有會影響 `decayTime` 的參數）
  在 MIDI 21..108 逐音呼叫**與 noteOn 完全相同的模態建構路徑**，取所有模態 `decayTime` 的最大值。
  - 若模態建構目前是 voice 的成員函式且與 noteOn 綁在一起，**抽出一個 const 靜態 helper**讓 noteOn 與本函式共用；
    抽出後 noteOn 的數值路徑必須位元相同（README §3 的 8/8 證明就是為這件事）。
  - 這個計算在 message thread 呼叫（`getTailLengthSeconds()` 就是 message thread），不在 audio thread；88 次模態計算是便宜的，
    但請快取：只在相關參數改變時重算（用 APVTS listener 或參數值雜湊比對皆可），`getTailLengthSeconds()` 只讀快取值。
- `getTailLengthSeconds()` 改為：`max(現行 FM/envelope 估計, 目前選用引擎的 worstCaseTailSeconds())` + 現行 delay 尾巴 + 現行 reverb 尾巴（若有）。
  **不設上限**（沒有可溯源的理由設上限；JUCE 允許長尾）。FM 引擎（域外）維持 envelope 估計。
- 不要用「目前正在響的 voice」來算——host 在沒有聲音時也會問，答案必須是 worst case。

### 2.2 Custom 判斷式

- `PluginEditor` 新增 `bool isCustomHarmonicsMode() const`（讀 `currentEngine()` 與 `chr_sub_engine`），`:413` 與 `:1246` 都改呼叫它。純重構。

### 2.3 HostProbe 新檢查（tests/host_probe.cpp）

- 對三個物理引擎預設狀態（cimbalom、tongue_drum、water_gong；FM 排除）：
  `CHECK(getTailLengthSeconds() >= 引擎 worstCaseTailSeconds())`，並印出兩者數值；
  另用 HostProbe 既有的 MIDI 渲染路徑實彈一顆 tongue_drum MIDI 40 十秒後量 RMS 仍 > −60 dBFS 相對峰值時，
  `CHECK(getTailLengthSeconds() > 10.0)`（這是把「host 被告知的長度」與「實際還在響」綁在一起的物理檢查；不引入新容差，−60 dB 就是 T60 的定義）。

## 3. 步驟

1. 建 `build-wf`（README §1 命令；第一次全建 JUCE 會花十幾分鐘，用 `run_in_background` 或加長 timeout）。
2. 先跑 baseline：用 README §3 的位元不變腳本，以 `build-wf` 的 CLI（未改碼）渲染 8 首 → 必須 8/8 與 `sha256_before.txt` 相同。
   這一步證明「乾淨 build-wf ≡ 既有基線」，之後的比對才有意義。
3. 實作 §2。
4. 三 target build + 四個測試 target build（X4）+ ctest + HostProbe 對 `build-wf\TsukiSynth_artefacts\Release\VST3\TsukiSynth.vst3` 跑。
5. `python tools/physics_verify.py --full --cli build-wf\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe` → NO CHECKED FAILURES（R6，因為碰了 `src/engines`）。
6. 位元不變 8/8。
7. `docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.zh-TW.md` §4-B 標「已修（WF0907-E5）」+ 一行修法；§5 第一項標「已抽成單一函式」。

## 4. 禁止

- 不改任何 `decayTimeForFrequency` 的公式、常數或材質表（R4）。
- 不改 `render()` / `renderEvent()` / `ModalResonator` 的數值路徑。
- 若第 2 步 baseline 不是 8/8，**停下回報**（環境問題，不是你的錯，但不能往下做）。

## 5. GATE（輸出到 `reports/gate_outputs/wf0907_E5_tail.txt`）

1. build-wf baseline 8/8 IDENTICAL。
2. 三 build + 四測試 target exit 0；`ctest` 全 Passed。
3. HostProbe 全 PASS（貼三個引擎的 tail 數值 vs worstCaseTailSeconds）。
4. `--full` NO CHECKED FAILURES。
5. 改碼後位元不變 8/8 IDENTICAL。
6. `python -m pytest tests -q` 全綠。
7. `git diff --stat` 只含 `src/PluginProcessor.{h,cpp}`、`src/PluginEditor.{h,cpp}`、`src/engines/*.h`、`tests/host_probe.cpp`、稽核文件。
