# WF0907-E10：HostProbe 加 H6 變動 block size、H7 user preset round-trip

> lane：C++　工兵：Sonnet　先讀 `WF0907_README.md`　前置：E7 已 PASS
> 依據：稽核文件 §2「GATE 覆蓋形狀對準 CLI，缺陷長在 plugin 側」——Pitch Glide 依 block size（已修 `cdf2017`）與 F-03 都是現行 HostProbe 抓不到的。

## 0. 一句話目標

把 plugin 側兩個沒人守的合約變成 HostProbe 的常設檢查：
- **H6**：同一段 MIDI 在不同 host block size 下渲染，旋律位置（onset ±10 ms / pitch ±5 cents，**既有已批准容差**）必須全部 PASS，
  並印出 block-vs-block 的樣本差異（informational，不設新容差）。
- **H7**：user preset 存→新實例載回，APVTS 全部參數位元相同；IR 狀態的差異**誠實列為已知 FAIL（F-03 待裁決）**，不得計為回歸。

## 1. 現況（規劃者已核實）

- `tests/host_probe.cpp`（CMake target `TsukiSynthHostProbe`）：H1 掃描 / H2 實體化 / H3 MIDI 串流渲染 + 跨實例位元決定性 / H4 automation / H5 DAW state round-trip。
  用法：`build-wf\Release\TsukiSynthHostProbe.exe <.vst3> <outdir>`（若路徑不同以 CMakeLists 為準）。
- `src/PresetManager.h`：`saveUserPreset(name, allowOverwrite)`(L122)、`loadPreset(index)`(L60)、`userPresetExists`(L115)、`deleteUserPreset`(L180)。
  user preset 存到磁碟哪裡、格式為何——先讀完這個檔。
- IR：`PluginProcessor.h:75-76` `getReverbIRName()/hasReverbIR()`；`PluginProcessor.cpp:795-797` `loadImpulseResponse(file)`；
  `EffectChain.h:103` `hasImpulseResponse()`。**UI 與音訊各問一份**（稽核病根一）。
- Pitch Glide 修正：`src/engines/ChromaticEngine.h:452-466`（`cdf2017`）。H6 的 water_gong 案例就是它的回歸測試。
- 既有旋律 GATE：`python tools/melody_verify.py <score> --wav <wav>`（容差 ±10 ms / 5 cents，已批准）；HostProbe H3 現在就是用一份哨兵 score + MIDI，沿用同一份。

## 2. 設計

### 2.1 H6

- block sizes：`{64, 256, 1024, 4096}` 以及 `prepareToPlay` 時的 maxBlock 本身；每個 size 重新 `prepareToPlay(48000, N)`、新鮮實例、同一 MIDI 序列（H3 那份，需含 water_gong 有 glide 的音與 piano 高音）。
- 每個 size 各寫一個 WAV 到 outdir（`h6_block_<N>.wav`）。
- HostProbe 內部印：各 size 對 64 的 max |delta|（LSB @24-bit）與 RMS delta（dB re signal）——**只印，不判**。
- 判定交給既有工具：卡的 GATE 步驟對每個 WAV 跑 `melody_verify.py`，全部 PASS 才算 H6 過。
  （若 HostProbe 能直接呼叫 python 就內嵌；不能就由 GATE 腳本做，證據檔要有每個 size 的 melody_verify 輸出。）

### 2.2 H7

- 實例 A：設一組非預設參數（至少 10 個含各引擎 + 效果），切 reverb 到 IR 模式並 `loadImpulseResponse` 一個合成 IR 檔（寫到 outdir），`saveUserPreset("wf0907_h7", true)`。
- 實例 B（新鮮）：`loadPreset` 該 user preset。
- CHECK：APVTS 每個參數 `getRawParameterValue` 位元相同（列出不同者）。
- CHECK（**預期 FAIL，F-03**）：`B.hasReverbIR()`、`B.effectChain.hasImpulseResponse()` 與 A 相同。這兩條要**明確標記 `KNOWN-FAIL(F-03)`**，
  且 HostProbe 的總 exit code **不因它們變非零**（用獨立計數器印 `known_fail_count`），避免 CI 誤紅；F-03 裁決落地後再翻成硬 CHECK。
- 清理：測完刪掉 user preset（`deleteUserPreset`），不留垃圾在月月的 preset 目錄；**先確認 preset 目錄位置並在證據檔寫明**。

## 3. 步驟

1. 讀 host_probe.cpp 與 PresetManager.h，證據檔開頭寫「user preset 存哪、H3 用哪份 MIDI/score」。
2. 實作 H6/H7；建 HostProbe target；對 `build-wf` 的 VST3 跑。
3. GATE 腳本跑 melody_verify × 5 個 WAV。
4. 若碰了 `src/`（理論上只碰 tests/），才需要 8/8 + `--full`；沒碰就寫明「未碰 src/」。
5. `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §7 的 L2 段補 H6/H7 說明；稽核文件 §2 表格更新覆蓋狀態。

## 4. 禁止

- 不改 melody_verify 容差；H6 不新增 block-vs-block 容差（只印）。
- H7 不得為了過而在 preset 裡「順手」存 IR 路徑——那是 F-03 的裁決內容。

## 5. GATE（輸出到 `reports/gate_outputs/wf0907_E10_hostprobe.txt`）

1. HostProbe 完整輸出：H1–H5 照舊 PASS、H6 各 size 差異表、H7 參數 round-trip PASS + `KNOWN-FAIL(F-03)` 兩條。
2. melody_verify 對 5 個 H6 WAV 全 PASS。
3. 測試 target build + ctest 全綠。
4. `python -m pytest tests -q` 全綠。
5. `git diff --stat` 只含 `tests/host_probe.cpp`、設計文件、稽核文件（若碰了 src/ 要附 8/8 與 `--full`）。
