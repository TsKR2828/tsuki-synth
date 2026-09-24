# 施工卡 WF0914-D12：舊 DAW state `reverb_ir_path` 遷移到 F-03 新 schema

> lane：C++（`build-wf\`，排在 B7P3 之後）
> 先讀：`reports/decision_packets/F03_IR_PRESET_RECALL.zh-TW.md` §7–8（落地規格）、
> `src/IRLibrary.h`、plugin 的 state 存讀程式碼（`getStateInformation`/`setStateInformation` 所在檔，自行定位）、
> `reports/gate_outputs/wf0908_P3_f03.txt`（F-03 落地時的 HostProbe 證據）。

## 0. 一句話目標

D12 登記：F-03 之前存的 DAW 專案 state 帶舊鍵 `reverb_ir_path`，新版讀到會**安靜忽略、
留 algorithmic**——使用者的殘響設定無聲消失。本卡補遷移：舊 state 載入時走 F-03 的正常匯入路。

## 1. 行為規格

`setStateInformation` 讀到**舊鍵存在且新 schema（`reverb_ir{kind,sha256,original_name}`）不存在**時：
1. 路徑檔案存在 → 走 IRLibrary 正常匯入（算 sha256、去重入庫、kind=user），狀態=已載入，
   等同使用者手動載入該 `.wav`；
2. 檔案不存在 → 進 F-03 的**缺檔三態**之「缺檔」態（UI 三態顯示會亮），**不得**安靜 fallback 到
   algorithmic 而不顯示；`original_name` 記舊路徑檔名供 UI 顯示。
3. 新 schema 已存在 → 舊鍵忽略（新版 state 為準），不重複匯入。
遷移邏輯集中一處、註解標明對應本卡；`getIRStatus()` 單一真相原則不破壞（F-03 規格）。

## 2. 測試

優先擴充 HostProbe（比照 H7 user preset 三情境的做法）：合成一份帶舊鍵的 state blob，
餵 `setStateInformation`，驗證上面三種情境的三態結果；不便走 HostProbe 就加 C++ 單元測試，
報告寫明選了哪條路與理由。

## 3. GATE（build-wf lane，X4 規約）

```
三 build target + 五測試 target 重建 → ctest 全綠
build-wf HostProbe 對 build-wf VST3 跑全套（H1–H8 + 新情境）0 failures
python tools/physics_verify.py --full --cli <build-wf CLI>   # 引擎路徑未動，期望零差異
render_wf_scores.py --cli <build-wf CLI> 對 sha256_before_post_a14.txt → 8/8 IDENTICAL
（CLI 渲染不走 plugin state，SHA 理應全同；任何變化=立即 BLOCKED）
```

證據 `reports/gate_outputs/wf0914_D12_*.txt`；`TODO.md` D12 條目同步。
