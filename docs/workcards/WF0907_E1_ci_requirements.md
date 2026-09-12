# WF0907-E1：requirements 加 pytest + mido，新測試檔接進 CI

> lane：Python　工兵：Sonnet　先讀 `WF0907_README.md`
> 依據：`docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.zh-TW.md` §4-G；月月 2026-09-07 裁決「加進去」。

## 0. 一句話目標

讓 `tests/` 底下所有 Python 測試都在 GitHub CI 跑，而不是只活在本機。

## 1. 現況（規劃者已核實）

- `tools/requirements-physics.txt` 只有 `numpy==2.1.3`、`scipy==1.14.1`、`jsonschema==4.23.0`。
- 本機已裝：`pytest 8.4.2`、`mido 1.3.3`。
- `.github/workflows/physics.yml` 的「Run spectral and T60 metrology self-tests」步驟是逐檔白名單，
  只跑 5 個檔案（`test_physics_verify`、`test_consonance_contract`、`test_verify_score_contract`、
  `test_specimen_verify`、`test_specimen_pipeline`）。
- 沒進 CI 的：`test_crossplatform_emit_safety.py`、`test_midi_type0.py`、`test_render_app_filename_safety.py`、
  `test_scene_reverb.py`、`test_score_vs_midi_verify.py`、`test_stem_verify.py`。
- 本機 `python -m pytest tests -q --co` 從 repo 根目錄**不需要** `PYTHONPATH=tools` 就能收集到 213 個測試。

## 2. 步驟

1. `tools/requirements-physics.txt` 加兩行，**釘本機版本**：`pytest==8.4.2`、`mido==1.3.3`。檔頭註解說明用途（pytest 跑 tests/；mido 給 `tools/midi_to_tsukisynth.py` 與 `test_midi_type0`）。
2. `physics.yml` 該步驟改為一行 `python -m pytest tests -q`（保留後面的 `python tools/physics_verify.py --selftest`）。
   若你實測發現某測試在乾淨環境需要 `PYTHONPATH=tools`，改用 step 級 `env: PYTHONPATH: tools`，並在證據檔寫明是哪個測試需要。
3. 確認 CI 的 CLI 建置步驟在 pytest 之前（需要 `build/` 下的 exe 的測試才找得到）——現況已是如此，不要重排其他步驟。
4. 不動 `cross-platform-emit` / `cpp-address-sanitizer` 兩個 job。

## 3. 禁止

- 不刪、不 skip 任何測試（R3）。若某測試在 CI 環境**必然**失敗（例如依賴本機絕對路徑），不要 skip，記進 `open_items` 附原因。
- 不升級 numpy/scipy/jsonschema 版本。

## 4. GATE（全部要附命令 + 輸出到 `reports/gate_outputs/wf0907_E1_ci.txt`）

1. `python -m pip install --dry-run -r tools/requirements-physics.txt` exit 0（證明釘的版本 pip 找得到）。
2. `python -m pytest tests -q` 全綠（貼出最後一行的 passed 數）。
3. `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/physics.yml'))"`——若本機沒 PyYAML，改貼 `git diff .github/workflows/physics.yml` 並人工核對縮排。
4. `git diff --stat` 只含 `tools/requirements-physics.txt`、`.github/workflows/physics.yml`。
