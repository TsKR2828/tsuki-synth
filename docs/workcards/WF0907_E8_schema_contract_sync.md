# WF0907-E8：score 合法性三份契約同步（schema ↔ C++ `--validate` ↔ converter）

> lane：C++　工兵：Sonnet　先讀 `WF0907_README.md`　前置：E5 已 PASS（`build-wf` 已存在）
> 依據：稽核文件 §1 第一列、§4-D（F-04 / F-05）。

## 0. 一句話目標

「什麼是合法 score」只能有一份可執行定義：`scores/schema/score.schema.json`。
C++ `--validate` 與 Python converter 都要**被測試證明**跟它一致——不是手抄三份清單。

## 1. 現況（規劃者已核實）

- schema（Draft 2020-12）有 `minimum/maximum/enum/pattern`：`bpm 1..999`、`quarter_bpm`（tempo_map）、`time_signatures.numerator/denominator`、
  `rests.duration ≥ 0`、`rests.kind` enum、`phrases.number`、`velocity 0..1`、`note 0..127`、`engine` enum 等。第一步用腳本把 schema 全部約束列出來。
- C++ `src/score/ScoreParser.h:942-960` `validateSimpleObjectArray(root, "tempo_map", {...鍵名...}, {...必填...}, score)` **只檢查鍵名與必填，不檢查範圍/enum**。
  稽核實測：仍接受負 tempo、零拍號、負 rest、非法 kind、負 phrase。
- Python converter `tools/midi_to_tsukisynth.py:1136-1171` 組 score dict；稽核說它寫得出 6 個 schema 錯誤的檔——
  具體是哪 6 個，在 `reports/gate_outputs/stem_verify_fur_elise_run.txt` 搜 `F-04` / `F-05`。
- 既有 schema 檢查：`tools/verify_score.py` 用 `jsonschema.Draft202012Validator`（L93）；corpus 75 檔全部通過 schema。
- 既有測試：`tests/test_score_vs_midi_verify.py`、`tests/test_midi_type0.py`。

## 2. 設計

### 2.1 交叉驗證測試（單一真相的執行器）`tests/test_schema_contract_sync.py`

- 從一個合法 fixture（例如 `scores/tests/melody_sentinel.score.json`）出發，**自動走訪 schema**，對每一條約束產生突變體：
  `minimum` → 值 −1 / 邊界值；`maximum` → 邊界 +1；`enum` → 不在 enum 的字串；`pattern` → 不匹配字串；`required` → 刪鍵；`type` → 錯型別。
  （不要手打清單；走訪 schema 的程式碼就是「單一真相」的體現。）
- 對每個突變體：`jsonschema` verdict vs `TsukiSynthCLI --validate <file>` exit code，**必須一致**。
  CLI 用環境變數或 `--cli` 指到 `build-wf` 的 exe（測試預設找 `build/`，本卡跑時指到 `build-wf`；記在證據）。
- 額外一組「正例」：corpus 75 檔全部 `--validate` VALID 且 jsonschema 0 errors（R3：一個都不能少）。

### 2.2 修 C++

- `validateSimpleObjectArray` 擴充成能吃範圍/enum 規格（或新增 `validateNumberRange` / `validateEnum` helper），讓 2.1 的矩陣全對齊。
  **只拒絕 schema 也拒絕的東西**；不得比 schema 更嚴（否則 corpus 可能被誤拒）。
- 錯誤訊息格式沿用既有 `fail(score, "...")`。

### 2.3 修 converter

- 對 repo 內每一份來源 MIDI（`find scores -name "*.mid"`，至少 `fur_Elise_WoO59.mid`）跑 `convert`，產物必須 jsonschema 0 errors。
- 修法原則：**產生正確值**，不是 clamp。若來源 MIDI 本身給出 schema 不允許的值（例如 tempo 0），converter 應 `raise` 帶明確訊息，不得寫出非法檔。
- 加進 `tests/test_score_vs_midi_verify.py` 或新測試：convert → jsonschema 0 errors。

## 3. 步驟

1. 列 schema 約束清單（存 `output/wf0907/E8/constraints.json`）。
2. 寫 2.1 測試，先跑一次看**現況有幾條不一致**，貼進證據檔（這是 before）。
3. 修 C++ → 重建 CLI target → 測試矩陣全對齊。
4. 修 converter → 測試通過。
5. corpus 75 檔 `--validate` 全 VALID（loop 腳本 + 輸出）。
6. 位元不變 8/8（`--validate` 不該影響渲染，但你碰了 `src/score/`，R6/README §3 都要求證明）+ `--full --cli build-wf...` NO CHECKED FAILURES + ctest（X4 先重建）。
7. 稽核文件 §4-D 標已修 + 指向新測試。

## 4. 禁止

- 不改 schema 本身（除非發現 schema 有 bug，那就 BLOCKED 回報，不要動）。
- 任何 corpus 檔被新檢查拒絕 → **BLOCKED**，附檔名與被拒原因；不得放寬檢查、不得改 corpus 檔。

## 5. GATE（輸出到 `reports/gate_outputs/wf0907_E8_schema.txt`）

1. before：不一致條數與清單。after：`pytest tests/test_schema_contract_sync.py -q` 全綠，並貼矩陣大小（幾個突變體）。
2. corpus 75/75 VALID。
3. convert 產物 jsonschema 0 errors。
4. 三 build + 測試 target + ctest 全綠；`--full` NO CHECKED FAILURES；8/8 IDENTICAL。
5. `python -m pytest tests -q` 全綠。
6. `git diff --stat` 只含 `src/score/ScoreParser.h`、`tools/midi_to_tsukisynth.py`、`tests/test_schema_contract_sync.py`、既有測試檔、稽核文件。
