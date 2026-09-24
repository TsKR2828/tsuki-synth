# 施工卡 WF0914-D9b：K-02 量測鏈加外部 IR 注入點 + 真實 IR 量測 + 裁決包

> 建立：2026-09-15　依據：**月月 2026-09-15 裁決 D9 選 (a)**——「把 D9 的量測步驟改分類到
> C++ lane，補一張小卡在 `tests/audit_repro.cpp` 新增可讀外部 WAV 路徑的 K-02 變體，
> 重新編譯 build-wf 後跑同一量測鏈」。
> lane：C++（`build-wf\`）。先讀：`WF0914_README.md`、`WF0907_README.md`、
> `docs/workcards/WF0914_D9_ir_loudness.md`（原卡）、`reports/gate_outputs/wf0914_D9_ir_measure.txt`
> （EchoThief 3 顆 IR 的路徑/SHA256/授權記錄）、`tests/audit_repro.cpp::reportReverbWetGainQuantification()`、
> `reports/decision_packets/K02_reverb_wet_scale.zh-TW.md`、`reports/gate_outputs/wf0907_E7_reverb.txt`。

## 0. 一句話目標

讓 K-02 的既有量測鏈能吃外部真實 IR 檔，量出 3 顆 EchoThief IR 的 wet 響度相對 ALGO 差幾 dB，
補齊原 D9 卡缺的核心數字，產出裁決包。

## 1. 實作要求

1. `tests/audit_repro.cpp`：K-02 量測函式新增**外部 IR 變體**——建議用環境變數
   （如 `TSUKI_K02_EXTERNAL_IR=<wav路徑>`）或測試 binary 的 argv 切換；讀檔失敗 fail-closed
   （明確報錯，不 silent fallback 合成 IR）。**未設變數時行為與現狀逐位元相同**
   （既有合成 IR 路徑一個字元不動——這是 GATE 3 的驗收點）。
2. 量測方法**照抄既有 K-02**（同一 score、同一訊號點、同一 dB 計算），只換 IR 來源；
   取樣率不合時的處理方式（重取樣或拒收）要寫明並溯源到 JUCE Convolution 的實際行為。
3. 對 3 顆 EchoThief IR（先驗 SHA256 與 `wf0914_D9_ir_measure.txt` 記錄一致）各量：
   wet-vs-ALGO 響度差 dB＋該 IR 寬頻 RMS/長度；順帶記合成 IR 的既有值當對照組。

## 2. 裁決包 `reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md`

體例照 K02，三案並列不選：A 載入時能量正規化（正規化定義候選明標 DECIDED CONVENTION 待定）／
B 不對齊＋UI 顯示 IR 相對響度（配合 F-03 三態）／C 維持現狀＋文件記載。
每案附本卡實測數字；查證並寫明 corpus score 是否走 IR 路徑（K02 已核實 CLI 不走 IR 分支
→ A 案不觸 R10，要引出處）；EchoThief 授權標注「非商用，量測參考用，不可隨產品散布，
正式商用需向 SDSURF（innovation@sdsu.edu）取得授權」。

## 3. GATE（build-wf lane，X4 規約）

1. 三 build target + 五測試 target 重建 exit 0。
2. `ctest --test-dir build-wf -C Release` 全綠（未設環境變數，既有測試行為不變）。
3. **預設行為不變證據**：不設變數跑 K-02 量測，輸出數字與 `wf0907_E7_reverb.txt` 記錄的
   合成 IR 值一致（同機同 binary 應完全相同；有差就停下回報）。
4. 外部 IR 變體：3 顆 IR 各跑一次＋一個 fail-closed 反例（不存在的路徑→明確報錯）。
5. 本卡不碰 `src/`；`git diff` 只含 `tests/audit_repro.cpp`＋reports 兩檔（證據＋裁決包）。
   位元不變比對不需跑（CLI binary 的 src 未動），稽核抽驗 `git diff -- src/` 為空即可。

證據 `reports/gate_outputs/wf0914_D9b_*.txt`；`TODO.md` D9 條目同步。
