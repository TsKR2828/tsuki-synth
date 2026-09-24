# 施工卡 WF0914-INTEGRATION：整合驗證（全部 lane 收尾後執行）

> lane：整合（**唯一允許重建 `build\` 的卡**）
> 前提：B7P0/B7P1/B7P3/D9/D10/D12/D13/D14/D15/D11 全部已稽核完（PASS 或 RED 皆可開工——
> RED 卡的改動不在工作樹上就照常整合；若 RED 卡有殘留 unstaged 改動，先回報再說，不要清理）。

## 0. 一句話目標

在合併後的工作樹上重建 `build\`，跑全套 GATE，證明本輪所有落地互不打架。

## 1. 步驟（X4 規約：ctest 前先重建五個測試 target）

```
cmake -B build -DCMAKE_BUILD_TYPE=Release -DTSUKI_BUILD_TESTS=ON
cmake --build build --config Release --target TsukiSynthCLI TsukiSynth_Standalone TsukiSynth_VST3
cmake --build build --config Release --target TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest TsukiSynthSpectrumViewTest TsukiSynthHostProbe
ctest --test-dir build -C Release --output-on-failure        # 全綠
python -m pytest tests -q                                     # 全綠（基線 267 + 本輪新增）
python tools/physics_verify.py --full                         # NO CHECKED FAILURES
python tools/physics_verify.py --selftest
python tools/verify_score.py --all                            # 75/75 或既有豁免不變
build/Release/TsukiSynthHostProbe.exe <build VST3> output/wf0914/INTEGRATION/hostprobe  # 0 failures
python reports/gate_outputs/wf0907_method/render_wf_scores.py # 對 sha256_before_post_a14.txt → 8/8 IDENTICAL
```

任何一條紅 → 不修改任何檔案，如實回報哪條紅、輸出全文存檔（status=RED）。
**整合卡自己不寫程式**；紅燈的歸屬分析（哪張卡引入）寫進回報即可。

## 2. 產出

- 全部輸出存 `reports/gate_outputs/wf0914_INTEGRATION.txt`（或分檔）。
- 回報：每條 GATE 的結果行、pytest 總數（記下新基線數字）、位元不變 8/8 結果。
