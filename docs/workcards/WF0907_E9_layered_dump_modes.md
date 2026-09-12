# WF0907-E9：`--dump-modes` 支援 layered score

> lane：C++　工兵：Sonnet　先讀 `WF0907_README.md`　前置：E8 已 PASS
> 依據：`src/cli/RenderApp.cpp:565-569` 明寫 `layer expansion is not implemented`；corpus 3 檔 layered 因此整檔拒答
> （`tools/melody_verify.py:225-230`；`reports/gate_outputs/melody_corpus_sweep_informational.txt`）。

## 0. 一句話目標

layered score 也能 `--dump-modes`：把每個 leaf 的事件**依渲染時實際套用的 offset/gain** 展平成絕對時間的事件清單，
讓 verify_score / melody_verify / stem_verify 對 layered 曲目有 ground truth。**渲染路徑一個位元都不能變。**

## 1. 現況（規劃者已核實）

- layered 渲染：`src/score/ScoreRenderer.h:577` `renderLayered(score, outputFile)`，L596-640 逐 layer 讀 sub-score、遞迴 `hasLayers` 檢查。
  **先讀完這段**，記下每個 layer 套用了哪些欄位（offset？gain？pan？mute？），dump 必須鏡射同一組。
- manifest 有 layer 依賴樹與循環偵測（`RenderApp.cpp:143-224`），可重用其解析方式。
- `RenderApp.cpp:555-580` 是 `--dump-modes` 入口；`renderer.dumpModes(score)` 現只吃 event score。
- corpus 的 layered 檔：`scores/examples/layered_transition.score.json`、`scores/originals/ai_radiance/ai_radiance_complete.score.json`、`scores/tests/test_layer.score.json`。
- `tools/verify_score.py:891` 註明 dump-modes 只吃 event score、layered 頂層 mode scan 標 N/A——本卡之後它可以改（但 Python 端改動不在本卡，記 open_items）。

## 2. 設計

- `ScoreRenderer::dumpModesLayered(const Score&)`（或讓 `dumpModes` 內部分流）：
  1. 依 `renderLayered` 同一順序、同一解析（base dir、遞迴、循環守衛）載入每個 leaf。
  2. 對每個 leaf 呼叫既有 `dumpModes(leaf)` 取事件級輸出。
  3. 展平：每個事件 `time += layer offset`（若 renderLayered 有 offset）、振幅乘 layer gain（若有），並加欄位 `layer_source`（相對路徑）與 `layer_depth`。
  4. 頂層 JSON 加 `"layered": true, "layers": [{"source":..., "offset_s":..., "gain":..., "event_count": N}]`，
     `model_observables` 等既有頂層欄位保留（值以 leaf 的邏輯合併：若無法合併，誠實輸出 `null` 並加 `"note"` 說明）。
  5. 若 layer 有 dump 不支援的屬性（例如 mute/solo/時間伸縮）**而 renderLayered 確實有實作**：照實作鏡射；若 renderLayered 沒實作，dump 也不要發明。
- 循環或 leaf 解析失敗 → exit 1 + 明確錯誤（fail-closed，與現行 renderLayered 一致）。

## 3. 步驟

1. 讀 `renderLayered` 並在證據檔開頭列出「layer 會套用的欄位清單 + 對應 ScoreRenderer.h 行號」。
2. 實作 §2。
3. 對三個 layered corpus 檔跑 `--dump-modes`，JSON 可解析；寫一支 `tests/test_dump_modes_layered.py`：
   (a) 展平事件數 = 各 leaf 事件數總和；(b) 每個事件的時間 = leaf 時間 + offset（用 Python 重算比對）；
   (c) 循環 fixture（自己在 `scores/tests/` 建一個 A→B→A）exit 1。測試以 `--cli` 指向 `build-wf`。
4. `verify_score.py --cli build-wf... <三個 layered 檔>` 仍 PASS（現況為 N/A 的部分維持 N/A 是可接受的；不得變 FAIL）。
5. 位元不變 8/8 + `--full` + ctest（X4）。
6. `RenderApp.cpp` 的錯誤訊息更新；`tools/verify_score.py:891` 那段註解的說明由 Python lane 之後處理——記 open_items。

## 4. 禁止

- 不改 `renderLayered` 的任何行為；不改 `render()`。
- 不在 dump 裡「補償」或「正規化」任何振幅（8/30 分軌稽核抓過工兵峰值正規化做假綠燈——那是 blocker 級錯誤）。

## 5. GATE（輸出到 `reports/gate_outputs/wf0907_E9_layered.txt`）

1. 三個 layered 檔 `--dump-modes` exit 0 + 每檔展平事件數。
2. `pytest tests/test_dump_modes_layered.py -q` 全綠。
3. `verify_score.py` 三檔結果。
4. 三 build + 測試 target + ctest；`--full` NO CHECKED FAILURES；8/8 IDENTICAL。
5. `python -m pytest tests -q` 全綠。
6. `git diff --stat` 只含 `src/score/ScoreRenderer.h`、`src/cli/RenderApp.cpp`、`tests/test_dump_modes_layered.py`、`scores/tests/<循環 fixture>`。
