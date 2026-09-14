# WF0907-C10：量測器自身的合成哨兵（≤1 cent 自證）

> lane：Python　工兵：Sonnet　先讀 `WF0907_README.md`
> 依據：`TODO.md` C10；月月 2026-08-30 查核第 5 點：「±5 cents 是本專案既有裁定的產品門檻，不是 ISO 或業界標準；
> 量測器本身必須先用合成訊號證明自身誤差 ≤1 cent，才有資格執行 ±5 cents 的產品 GATE。」

## 0. 一句話目標

用**已知答案的合成訊號**（不經 TsukiSynthCLI）證明 `melody_verify.py`／`stem_verify.py` 用的音高估計器
誤差 ≤ 1 cent；證明不了的區域，誠實列成表，**不准為了過線去改估計器**。

## 1. 現況（規劃者已核實）

- `tools/melody_verify.py`：`class Spectrogram`(L126)、`detect_rises`(L152)、`band_of`(L176)、`refined_onset`(L180)、
  `expected_f0s`(L217)、`verify`(L281)、`selftest`(L609)。音高判定用「5-cent course-centroid」帶質心法，
  **計算 cents 的程式碼目前在 `verify()` 裡面或附近**——第一步就是 grep `cents` 把它精確定位。
- `tools/stem_verify.py::judge_stem`(L414) 透過 `_load_module` 呼叫 melody_verify 的同一套數學。
- 既有哨兵：`python tools/melody_verify.py --selftest`（12 PASS）、`PYTHONPATH=tools python -m pytest tests/test_stem_verify.py -q`（21 passed）。
- 已知估計器極限（設計文件 `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §7/§8）：Re 規則 f0 < 167 Hz 拒 onset；
  殘響會把質心拉偏最多 9.5 cents（所以本卡**只測乾聲**）。
- 1 cent 門檻是月月裁定，**不是你可以調的數字**（R2）。

## 2. 步驟

1. **定位並抽出純函式（不改數值行為）**：把「給定 mono 訊號 + sr + 期望 f0 + 起音時間 → 量測 cents」的計算抽成
   `measure_pitch_cents(...)`（名稱可依既有風格），`verify()` 改呼叫它。**抽出前**先跑一次
   `python tools/melody_verify.py scores/tests/melody_sentinel.score.json --wav <渲染> --keep-json output/wf0907/C10/before.json`
   （渲染用 `build\` 的 CLI，命令照 README §7），抽出後再跑一次存 `after.json`，兩份 JSON 的每一顆 cents / onset 數字**逐字相同**。
   若 `--keep-json` 不存在就用工具現有的 JSON 輸出方式；重點是留下「抽出前後數字不變」的證據。
2. 新工具 `tools/measurement_selfcal.py`（只依賴 numpy/scipy）：
   - 合成訊號 = Σ 衰減正弦：已知 f0、每個 partial 已知 T60（用 `exp(-ln(1000)·t/T60)`，與 `ModalResonator` 同義）、
     已知 partial 結構（諧波 n·f0 與含 stiffness inharmonicity `f_n = n·f0·√(1+B·n²)` 兩組，B 取 1e-4 與 1e-3——
     這兩個值只用來做合成測試，不主張是任何真實樂器的 B），已知起音時間（非零、非 hop 整數倍），
     加 −90 dBFS 白噪音床，峰值 −6 / −30 / −60 dBFS 三個電平。
   - 網格：MIDI 36..100 每個半音 × 上述變因 × sr 48000（corpus 預設；若既有工具支援其他 sr 再加 44100）。
   - 對每個格點呼叫**與產品 GATE 完全相同的函式**（第 1 步抽出的那個，不可另寫一份「測試用估計器」）。
   - 報告：每格 `error_cents`；彙總 `max_abs_error_cents`、依 f0 區段（<167 Hz / 167–500 / 500–2000 / >2000）與電平分組的最大值。
   - **靈敏度反例**：同一格把合成 f0 偏移 +3.0 cents，估計器必須量到 +3.0 ± 1.0；再偏移 −3.0 亦然。
     這條防止「估計器永遠回傳期望值」的假綠燈。
   - exit code：`max_abs_error_cents ≤ 1.0` 且反例全過 → 0；否則 → 1，並印出未達標的區段表。
   - onset 誤差同時量、同時印（informational，不影響 exit code；≤1 ms 只是參考，沒有裁定門檻）。
3. `tests/test_measurement_selfcal.py`：至少 (a) 純諧波 A4 誤差 ≤ 1 cent；(b) 靈敏度反例；(c) 若把估計器換成「回傳期望值」的 mutant，反例必須 FAIL（用 monkeypatch）。
4. 若第 2 步發現某區段 > 1 cent：**不要改估計器**。在證據檔寫清楚區段與數字，`status = BLOCKED`，並在
   `reports/decision_packets/C10_selfcal_domain.zh-TW.md` 寫一張裁決包（月月看數字選：A 收窄 GATE 主張域到達標區段／B 授權改估計器並重跑所有既有證據）。
5. `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` 新增 §9「量測器自證」一小節：命令、結果表、限制（只乾聲、只合成訊號）。

## 3. 禁止

- 不改任何容差（5 cents / 10 ms / 1 cent）。
- 不改 `verify()` 的判定邏輯；只允許「抽出純函式」這種可證明數值不變的重構。
- 不碰 `tools/stem_verify.py`（C11/C12 會改它）。

## 4. GATE（輸出到 `reports/gate_outputs/wf0907_C10_selfcal.txt`）

1. 抽出前後 `before.json` / `after.json` 數字逐字相同（貼 diff 為空的證據）。
2. `python tools/melody_verify.py --selftest` → 12 PASS / 0 FAIL。
3. `PYTHONPATH=tools python -m pytest tests/test_stem_verify.py -q` → 21 passed。
4. `python tools/measurement_selfcal.py` 完整輸出（exit 0，或 exit 1 + 區段表 + BLOCKED）。
5. `python -m pytest tests -q` 全綠。
6. `git diff --stat` 只含：`tools/melody_verify.py`、`tools/measurement_selfcal.py`、`tests/test_measurement_selfcal.py`、設計文件。
