# WF0907-C12：stem_verify `--analysis-dry` + 衍生 score 的 hash/diff 寫進 JSON

> lane：Python　工兵：Sonnet　先讀 `WF0907_README.md`　前置：C11 已 PASS
> 依據：`TODO.md` C12；設計文件 §8.3「帶殘響訊號的音高判定不得作為 GATE 依據」。

## 0. 一句話目標

工具自己產生乾聲衍生 score 來分析（不再手動改 score 存 temp），並把「來源 score hash、衍生 score hash、逐葉 diff、CLI hash」
寫進 JSON，讓報告脫離使用者 temp 目錄也能溯源。

## 1. 現況（規劃者已核實）

- 現行乾聲跑法：手動把 `global.effects.reverb` 的 `wet`/`decay` 歸零另存再跑；JSON 的 `score` 欄位指向 temp 路徑。
- `stem_verify.py::run`(L558) 收 `score_path`；`make_stem_score`(L306)、`make_reference_score`(L328) 從 score 物件產分軌/參考 score。
- `verify_score.py` 已有 `sha256_file` 與 `cli_path` 的 renderer SHA 記錄（L1237-1336）可參考寫法。

## 2. 步驟

1. 新旗標：`--analysis-dry`（**預設開**）與 `--no-analysis-dry`（明示用帶效果的原 score，JSON 標 `analysis_dry: false`，
   並在報告頂層加 `warning: "pitch verdicts on wet signal are not GATE evidence (design doc §8.3)"`）。
2. 乾聲衍生規則（寫成一個純函式 `derive_dry_score(score) -> (score, leaf_diff)`）：
   `global.effects.reverb.wet = 0`、`global.effects.reverb.decay = 0`、`global.effects.delay.wet = 0`（delay 會製造幻起音）。
   其他欄位一律不動（distortion/eq 不動——它們不搬移質心；若你認為該動，記 open_items，不要動）。
   `leaf_diff` = `[{"path": "global/effects/reverb/wet", "before": 0.3, "after": 0}, ...]`，只列真的改到的葉。
   若 score 有 `layers`，衍生規則同樣套到頂層；leaf 的展開不在本卡（E9 之後才有）。
3. 衍生 score 寫到 `<out_dir>/derived/<原檔名>.dry.score.json`；分軌與參考 score 都從衍生 score 產生（疊加證明兩邊同一管線）。
4. JSON 頂層新增：
   ```
   "provenance": {
     "source_score": {"path": <相對 repo 的路徑>, "sha256": ...},
     "analysis_score": {"path": ..., "sha256": ..., "leaf_diff": [...]},
     "cli": {"path": ..., "sha256": ...},
     "analysis_dry": true
   }
   ```
5. 測試（`tests/test_stem_verify.py`）：(a) `derive_dry_score` 只改那三個葉、diff 精確；(b) 沒有 reverb 區塊的 score diff 為空；
   (c) JSON 的兩個 sha256 與實際檔案一致；(d) `--no-analysis-dry` 時 `analysis_dry=false` 且 warning 存在。
6. 實跑對照：以 8/30 的手動方法（手動歸零 wet/decay 另存 → 跑舊程式 `git show HEAD:tools/stem_verify.py`）與新旗標各跑
   `--limit 40` 給愛麗絲鋼琴版，**verdict / pitch_cents / onset_err_ms 逐顆相同**（delay wet 原本就是 0 的話結果應完全一致；
   若不同，找出是哪個葉造成，如實寫）。
7. 更新 `HANDOVER.md` §7「分軌驗證」那段的操作說明（把「目前工具沒有 --analysis-dry」改掉）與設計文件 §8.3。

## 3. 禁止

- 不改判定與容差；不碰 `melody_verify.py`。
- 衍生 score 不得寫回 `scores/`。

## 4. GATE（輸出到 `reports/gate_outputs/wf0907_C12_dry.txt`）

1. 手動法 vs 新旗標逐顆一致的比對輸出。
2. 貼一份 after.json 的 `provenance` 區塊，並用 `certutil -hashfile` 或 python 重算兩個 sha256 核對。
3. `PYTHONPATH=tools python -m pytest tests/test_stem_verify.py -q` 全綠。
4. `python -m pytest tests -q` 全綠。
5. `git diff --stat` 只含 `tools/stem_verify.py`、`tests/test_stem_verify.py`、`HANDOVER.md`、設計文件。
