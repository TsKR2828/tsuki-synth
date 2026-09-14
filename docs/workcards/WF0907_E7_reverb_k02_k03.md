# WF0907-E7：K-03 超過 maxBlock 的分塊處理（修）+ K-02 ALGO↔IR wet 增益差（只量化，不修）

> lane：C++　工兵：Sonnet　先讀 `WF0907_README.md`　前置：E9 已 PASS
> 依據：稽核文件 §1 第四列、§4-E。

## 0. 一句話目標

- K-03：host 丟進來的 block 比 `prepare()` 時的 maxBlock 大時，EffectChain **不得靜默換演算法**——改成內部分塊處理，輸出必須等於「分兩次呼叫」的結果。
- K-02：ALGO reverb wet 額外乘 `0.15`（`SimpleReverb.h:155`）、IR 路徑沒有（`EffectChain.h:204`）。**先量化差多少 dB，寫裁決包，不修**
  （修哪一邊都會改渲染輸出 → Rule 10 → 月月裁決）。

## 1. 現況（規劃者已核實）

- `src/effects/EffectChain.h:35-48` `prepare(sr, maxBlockSize=2048)`：`maxBlock`、`convolution.prepare(spec)`、`dryBuffer`、`mixScratch` 都以 maxBlock 配置。
- `EffectChain.h:131-135` 有 `numSamples <= maxBlock` 的守衛——**先讀清楚超過時現在走哪條路**（稽核說是靜默退回 algorithmic）。
- `SimpleReverb.h:155-156`：`left = inL*dry + outL*mix*0.15f`。
- CLI `ScoreRenderer` 也用 EffectChain（確認一下它的 block size 是否固定 ≤ maxBlock；若是，分塊路徑在 CLI 永遠不觸發 → 位元不變）。
- C++ 測試放進既有 target `tests/audit_repro.cpp`（`TsukiSynthAuditTest`），**不要新增 CMake target**（CI yaml 由 Python lane 在改，避免衝突）。

## 2. 設計

### 2.1 K-03 修法

- `processBlock` 開頭：若 `numSamples > maxBlock`，以 `maxBlock` 為步長切成子 block，對每個子 block 走**完全相同**的既有路徑（用 `juce::AudioBuffer` 的 sub-view 或 `getArrayOfWritePointers` 偏移）。
  不允許在 audio thread 配置記憶體；不改 prepare。
- 測試（audit_repro.cpp）：prepare(48000, 512)，載入合成 IR（指數衰減白噪，固定種子，1 秒），輸入固定種子噪音 1537 samples：
  (a) 一次呼叫 1537 vs 連續三次 512+512+513 呼叫（同一初始狀態）→ **位元相同**；
  (b) 同樣的檢查在 ALGO 模式也做；(c) 反例：故意把子 block 邊界少處理 1 sample 的 mutant 必須被 (a) 抓到（可用 `#ifdef` 測試鉤子或直接在測試裡模擬「丟掉最後一個 sample」的預期輸出證明測試有牙齒）。

### 2.2 K-02 量化（不改 DSP）

- 測試或獨立小程式（放 audit_repro.cpp，印數字不判 PASS/FAIL）：同一輸入（固定種子噪音 2 s），mix=1.0：
  - ALGO：decay 參數取 reverb 預設；量 wet 輸出 RMS（dBFS）與 T60（−60 dB 交越）。
  - IR：用「與 ALGO 同 T60 的合成指數衰減噪 IR」（T60 由上一步實測值反推，寫清楚），量 wet 輸出 RMS。
  - 印：兩者 RMS 差（dB）、各自 T60、以及 ALGO 若拿掉 0.15 的理論差 `20·log10(1/0.15) = 16.48 dB` 作對照。
- 寫裁決包 `reports/decision_packets/K02_reverb_wet_scale.zh-TW.md`：現況、實測數字、三個選項與各自的 Rule 10 衝擊
  （A：IR 路徑也乘 0.15——只影響 plugin IR 模式，CLI 不用 IR 則 corpus 不變，要證明；B：拿掉 ALGO 的 0.15 並重校 corpus——全 corpus 渲染改變；C：維持並在 UI/文件標註）。
  **不要替月月選**；只給「看完數字就能選」的表。

## 3. 步驟

1. 讀 EffectChain/SimpleReverb 相關段，在證據檔開頭寫「超過 maxBlock 時現行路徑」的 file:line 說明。
2. 實作 2.1 + 測試；X4 重建 → ctest。
3. 2.2 量測 + 裁決包。
4. 位元不變 8/8 + `--full --cli build-wf...`（碰了 `src/effects`，比照 R6）。
5. 稽核文件 §4-E：K-03 標已修；K-02 指向裁決包。

## 4. 禁止

- 不改 `0.15`；不改 convolution 參數；不改 reverb 演算法。
- 不新增容差；(a) 的判定是「位元相同」，沒有容差可調。

## 5. GATE（輸出到 `reports/gate_outputs/wf0907_E7_reverb.txt`）

1. audit test 新增項目全 PASS，含反例被抓到的證據。
2. K-02 數字表。
3. 三 build + 測試 target + ctest；`--full` NO CHECKED FAILURES；8/8 IDENTICAL。
4. `python -m pytest tests -q` 全綠。
5. `git diff --stat` 只含 `src/effects/EffectChain.h`、`tests/audit_repro.cpp`、裁決包、稽核文件。
