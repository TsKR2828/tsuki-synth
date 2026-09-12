# WF0907-C11：stem_verify 逐顆記錄拒答理由

> lane：Python　工兵：Sonnet　先讀 `WF0907_README.md`　前置：C10 已由稽核 PASS（同 lane 順序保證）
> 依據：`TODO.md` C11——212 顆拒答目前是黑盒。

## 0. 一句話目標

`stem_verify.py` 的 JSON 每顆事件多一個 `reason`（字串）與 `rules`（觸發的規則 id 清單，如 `Ra`/`Rb`/`Rc`/`Rd`/`Re`），
外加整份報告的 `refusal_histogram`。**判定邏輯一個字都不改。**

## 1. 現況（規劃者已核實）

- `tools/stem_verify.py`：`judge_stem`(L414) 呼叫 melody_verify；`run`(L558) 組報告；JSON 每顆現在只有
  `index/time/note/engine/verdict/onset_err_ms/pitch_cents/expected_f0_hz`。
- `melody_verify.py` 的事件結果本來就帶 reason（設計文件 §7 的 Ra–Re 規則），只是沒被帶進 stem_verify。
  第一步 grep melody_verify 裡 `reason` / `rule` 的欄位名，看它們長什麼樣。
- 既有測試 `tests/test_stem_verify.py`（21 passed）。

## 2. 步驟

1. `judge_stem` 把 melody_verify 事件結果裡的 reason / rule id 原樣帶出（不重新措辭、不翻譯、不合併）。
   如果 melody_verify 只有自由文字沒有規則 id，`rules` 就從 reason 文字裡以**既有規則名稱的精確字串**抽（例如 `"Ra"`），抽不到給空陣列，不要猜。
2. 報告層加 `refusal_histogram`：`{reason 字串: 顆數}`，另加 `rules_histogram`。
3. `tests/test_stem_verify.py` 加：(a) 拒答事件必帶非空 `reason`；(b) `refusal_histogram` 總和 = 拒答顆數；(c) 既有 21 測試不動。
4. 實跑：`python tools/stem_verify.py scores/classical/fur_elise/<鋼琴版 score> --limit 40 --jobs 3 --json output/wf0907/C11/after.json`
   （用 `build\` 的 CLI；score 檔名自己 `ls scores/classical/fur_elise/`）。**同時**用改動前的程式（`git stash` 禁用——改用
   `git show HEAD:tools/stem_verify.py > output/wf0907/C11/stem_verify_before.py` 另存後執行）跑同樣參數存 `before.json`，
   證明 `verdict` / `onset_err_ms` / `pitch_cents` 逐顆相同，只多了新欄位。
5. `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8 補一句：JSON 新欄位名稱與語意。

## 3. 禁止

- 不改任何判定；不改容差；不改 `melody_verify.py`（C10 剛動過它，這張卡只讀它）。

## 4. GATE（輸出到 `reports/gate_outputs/wf0907_C11_reason.txt`）

1. before/after 兩份 JSON 的 verdict/onset/pitch 逐顆相同（貼比對腳本與結果）。
2. after.json 拒答顆全部有非空 reason；貼 `refusal_histogram`。
3. `PYTHONPATH=tools python -m pytest tests/test_stem_verify.py -q` 全綠（≥ 24）。
4. `python -m pytest tests -q` 全綠。
5. `git diff --stat` 只含 `tools/stem_verify.py`、`tests/test_stem_verify.py`、設計文件。
