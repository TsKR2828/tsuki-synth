# B4 Rule 10 前後對照 — 方法腳本與 before 基線資料

> 產出：2026-08-27（B4 開工前 before 採樣，工作樹 = HEAD f67050b，乾淨、B3 已落地）
> 對應施工卡：`docs/workcards/B4.md` §8 步驟 1／§9（Rule 10 報告的前後對照資料）
> 方法學前例：`reports/gate_outputs/b3_method/README.md`（同一套 before/after 雙跑法）
> 開工前 `--full` 基線：`reports/gate_outputs/b4_baseline_full.txt`
> （`RESULT: NO CHECKED FAILURES; UNVERIFIED/N/A RANGES REPORTED`）

此目錄的四個腳本在 **before**（B4 改動前）與 **after**（B4 改動後）各跑一次，
同一支腳本、同一組參數，只換 `--label`。所有命令從 repo 根目錄執行，前提是
CLI 已重建（`build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`）。

---

## 1. `scan_affected_scores.py` — 受影響 score 清單

對應 B4 卡 §9「先用腳本掃出清單，不要憑印象挑幾首」。

**判定條件**（照 `src/score/ScoreRenderer.h` 現況，不是照 §9 的簡述字面）：
event `engine ∈ {string, cimbalom, piano}`（renderCimbalom 路徑）**且**有效
exciter 經 `cimbalomExciterFromString()` 映為 `ExciterType::Felt`
（felt / felt_mallet / finger / finger_tap / rubber_mallet；piano 引擎先套
renderEvent() 的 `wood_mallet→felt` 覆寫，所以預設 exciter 的 piano 一律 Felt）。
Chromatic 引擎（beam/tongue_drum/plate/water_gong/custom）即使 exciter 是
felt 家族也**不受影響**——它們走 `chromaticExciterHardness()`，且 B4 明文
不碰 `ChromaticEngine.h`（施工卡 §3 硬邊界）。layers 型 score 由 source
子譜遞迴判定；track_profiles 只是 metadata（renderer 不套用），不進判定。

corpus 枚舉與 `tools/verify_score.py::find_all_scores()` 同一組（73 首）。

```
python reports/gate_outputs/b4_method/scan_affected_scores.py --label before
python reports/gate_outputs/b4_method/scan_affected_scores.py --label after
```

輸出：`affected_scores_<label>.md`（人讀）+ `affected_scores_<label>.json`
（機器清單，供第 2 支腳本用）。

**before 結果：73 首中 5 首受影響**（felt 事件數）：
`physical_piano`(4, piano)、`ai_radiance_m3`(16, cimbalom/felt_mallet)、
`ai_radiance_complete`(經 layers 引用 m3)、`akashic_action_001`(1, string/finger)、
`ocean_action_001`(1, string/rubber_mallet)。其餘 68 首（含所有 vivaldi）
在 B4 後渲染必須逐位元不變。交叉驗證：`grep` felt 家族 exciter 命中的另外
12 檔全部只落在 Chromatic 引擎事件上（見本次工兵回報）。

## 2. `render_affected_pieces.py` — 受影響曲目整曲渲染指標

改造自 `b3_method/render_rep_pieces.py`（同一套 RMS/質心/SHA256 定義：
聲道平均混 mono、整曲 `20·log10(RMS)`、整曲無窗 rfft 振幅加權質心、
WAV 原始位元組 SHA256），曲目清單改讀第 1 支腳本的 json（全量，不挑）。

```
python reports/gate_outputs/b4_method/render_affected_pieces.py --label before --workdir <repo外目錄>
python reports/gate_outputs/b4_method/render_affected_pieces.py --label after  --workdir <repo外另一目錄>
```

輸出：`affected_render_<label>.csv`
（欄位 piece, score_path, wav, len_s, rms_dbfs, centroid_hz, sha256）

## 3. `anchor_partials.py` — C2/C4/C7 錨點音 partial 表（Felt piano 路徑）

對應 B4 卡 §9「C2/C4/C7 × velocity 48/127、96/127 的 --dump-modes 前 5
partial 相對振幅 (dB re fundamental) 前後對照表」。

**方法**：單事件 probe score，`engine: "piano"`、**無任何 params 覆寫**
（piano 分支自動 wood_mallet→felt、strike 0.3→0.125，正是 B4 要換 tau_c
來源的 Felt 路徑），velocity = 48/127 與 96/127；`--dump-modes` 讀
**中央弦**（3 弦 course 中基頻最接近平均律者，b3_method/B2 同一慣例）
前 5 partial，`20·log10(amp_i/amp_1)`。CSV 同時保留原始 amp 欄，
after 對照不必重推 dB。probe 寫進系統暫存目錄，不進 repo。

```
python reports/gate_outputs/b4_method/anchor_partials.py --label before
python reports/gate_outputs/b4_method/anchor_partials.py --label after
```

輸出：`anchor_partials_<label>.csv`

**before 關鍵數字**（p1..p5 dB re fundamental）：

| note | vel | p1 | p2 | p3 | p4 | p5 |
|---|---|---|---|---|---|---|
| C2 | 48/127 | 0.00 | +3.60 | +2.86 | −1.37 | −10.65 |
| C2 | 96/127 | 0.00 | +4.01 | +4.06 | +1.29 | −4.67 |
| C4 | 48/127 | 0.00 | −11.32 | −12.08 | −25.37 | −25.39 |
| C4 | 96/127 | 0.00 | −5.29 | −14.64 | −19.06 | −20.88 |
| C7 | 48/127 | 0.00 | −23.26 | −14.21 | −15.49 | −22.50 |
| C7 | 96/127 | 0.00 | −2.87 | −24.47 | −20.40 | −19.19 |

（C7 p2 的 20 dB 級跳動來自 felt 脈衝力頻譜的零點附近取樣——p2≈4.2 kHz
落在現行 tau_c(v) 下力頻譜第一零點附近，velocity 改 tau_c 就把零點掃過
p2。這正是 tau_c 敏感度的放大鏡，after 對照時預期這幾格變動最大。）

## 4. `nonfelt_invariance.py` — Wood/Cotton/Metal 位元不變參照

對應 B4 卡 §6 步驟 7／§8 步驟 7。cimbalom A4（MIDI 69）velocity 0.5
錨點慣例 probe × 三個非 Felt exciter（wood_mallet / cotton_mallet /
metal_mallet），各記：渲染 WAV SHA256、`--dump-modes` stdout SHA256、
中央弦全部 partial amp（CLI 原樣 5 位小數）。

```
python reports/gate_outputs/b4_method/nonfelt_invariance.py --label before
python reports/gate_outputs/b4_method/nonfelt_invariance.py --label after
```

輸出：`nonfelt_invariance_<label>.txt`。**B4 完工後 after 檔除 label 標題行外
必須與 before 檔逐位元相同**（直接 diff）。渲染決定性已驗證：本次 before
連跑兩次，全部 SHA256 相同。

**before SHA256（wav / dump-modes 前 16 hex）**：
wood_mallet `48748d253b58b77c` / `70b567c963f1348a`；
cotton_mallet `b0d1afc4c6d1f728` / `d2dc579849e4829b`；
metal_mallet `63ad3d9f12b8f0b1` / `d10fc53238628e16`。

---

## before 資料檔（本次已產出）

| 檔案 | 內容 |
|---|---|
| `affected_scores_before.md` / `.json` | 73 首掃描結果：5 首受影響 + 68 首不變清單 |
| `affected_render_before.csv` | 5 首受影響曲目整曲 RMS/質心/SHA256 |
| `anchor_partials_before.csv` | C2/C4/C7 × v48/v96 前 5 partial 相對振幅 |
| `nonfelt_invariance_before.txt` | Wood/Cotton/Metal probe 的 WAV/dump SHA256 + amp |

after 階段：B4 落地、CLI 重建後，四支腳本原樣重跑 `--label after`，
與 `*_before.*` 逐欄對照即為 Rule 10 報告
（`reports/b4_hammer_contact_before_after.md`）§9 所需素材；
`nonfelt_invariance_after.txt` 與 68 首不受影響清單另構成位元不變性證據。

---

## after 階段補記（2026-08-27，Rule 10 報告產出時）

四支腳本已以 `--label after` 原樣重跑（before 檔一律未動；
`anchor_partials_after.csv` 於報告產出時再重跑一次，與 F3 裁決前
（00:18）產出的版本**逐位元相同**——CLI binary 未變，F3 裁決 (b) 只改
Python 判定端）。before 渲染 WAV 完整保留於
`%TEMP%\b4_render_before`（SHA256 與 `affected_render_before.csv` 逐一
核對相符），after 渲染在 `%TEMP%\b4_render_after`。

報告階段另增四支腳本（同目錄，供覆核重跑）：

| 腳本 | 輸出 | 用途 |
|---|---|---|
| `t60_f0_felt_events.py` | `t60_f0_felt_events_after.csv` | 受影響曲目全部 22 個 felt 事件的模型 f0/T60 逐 partial 不變性（felt vs cotton_mallet 換激發器雙 dump 精確比對；封閉證據鏈見腳本 docstring） |
| `audio_t60_sample.py` | `audio_t60_sample.csv` | before/after WAV 音訊級衰減斜率取樣（±3% 帶通 + Hilbert 對數斜率，同窗同帶同尺） |
| `unaffected_sentinels_check.py` | `unaffected_sentinels_after.txt` | 6 首不受影響整曲 sentinel 重渲染，SHA256 對 `b3_method/rep_pieces_after.csv`（= B4-before 基線）逐位元比對 |
| `tauc_curve_mirror.py` | `tauc_curve_mirror.csv` | 新舊 tau_c 公式鏡像重算（敘事用），先自我驗證：錨點/力度指數恆等式 + 鏡像 H 比值對 anchor CSV 實測 p1_amp 比值（C2/C4 斷言 ≤0.2 dB） |
