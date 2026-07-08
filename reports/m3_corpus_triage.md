# M3 全曲庫驗證 — FAIL 分流表

> 資料來源：`reports/gate_outputs/verify_all_corpus.log`（2026-07-05 15:54 UTC 起跑，2026-07-06 補上 akashic_opening_bell_001）
> 涵蓋範圍：`scores/examples/` + `scores/classical/vivaldi_four_seasons/`（遞迴）+ `scores/originals/ai_radiance/` + `scores/library/`（遞迴），共 **73** 個 `.score.json`（`scores/tests/` 6 檔為工具測試用途，不列入曲庫驗證範圍，未跑）。
> 容差常數：全程未動，見 `tools/verify_score.py` / `tools/physics_verify.py` 原始定義（F0_TOL_CENTS=1.0 / MODE_F0_TOL_CENTS=12.0 / REST_RMS_LIMIT_DBFS=-50.0 / REST_DECAY_ALLOWANCE_S=0.5 / PEAK_LIMIT_DBFS=-0.3 / VELOCITY_DB_TARGET=6.0 / VELOCITY_DB_TOL=1.0 / T60_RATIO_TOLERANCE=(0.2,5.0) / tol_pct 各引擎 2–4%）。

## 總結

- **PASS: 67 / 73**
- **FAIL: 6 / 73**
- FAIL 只有兩種根因類別，見下表。**沒有任何一筆是頻率/partials/T60/velocity/peak 物理量測失敗**——peak_below_limit 在全部 72 個有跑到該檢查項的 score 中零失敗（全部 `normalize: true`，統一收斂到 -0.45 dBFS，未見「軟力度變大聲頂到 peak」的連帶效應，故本輪無需向月月建議調整任何 master_volume）。

| # | 檔案 | 哪個檢查 FAIL | 實測數字 vs 門檻 | 根因歸類 | 建議處置 |
|---|------|--------------|-----------------|---------|---------|
| 1 | `scores/examples/moonlight_sonata_complete.score.json` | `rests.rms_below_limit` | Rest 316.52s–316.80s 量到 **-43.1 dBFS**（門檻 -50.0 dBFS，超標 6.9 dB）；12/14 個 rest 區間超標。FX-bypass 對照：同視窗關掉 FX 只有 **-120.0 dBFS**（遠低於門檻） | **殘響尾巴**（FX-bypass 診斷坐實：關掉 reverb/delay 後乾聲道完全乾淨，超標完全是 reverb/delay wet 尾巴造成，不是模型自身衰減問題） | **建議改 score 參數，不擅改**：`global.effects.reverb.decay` / `.wet` 或 `delay.feedback` 目前設定的殘響尾巴長度超過本曲樂句間的休止時間。建議月月裁決：(a) 縮短 reverb decay 或降低 wet，或 (b) 這是刻意的長殘響美術效果、可要求對此曲目登記為「FX 藝術意圖」豁免 rest 檢查。**不動容差、不動 score，留給月月**。 |
| 2 | `scores/classical/.../autumn/vivaldi_four_seasons_autumn_m1.score.json` | `modes.dump_modes_ran` | `--dump-modes` 在 600s 內未跑完（3111 個 event） | **工具效能限制**（非物理模型 bug）：`--dump-modes` 對每個 modal event 做模態分解，events 數量與耗時近似線性；`tools/verify_score.py` 的 CLI 呼叫逾時是寫死的 600s (`run_cli(cli, args, timeout=600)`，非 ROADMAP §6 容差表項目) | **建議豁免＋理由**：見下方「Vivaldi m1/m3 逾時分析」。建議提高該 CLI 呼叫的逾時秒數（非物理容差，是工具逾時），或針對超大型曲目改用抽樣式 dump-modes 驗證。不擅自更動，列給月月裁決。 |
| 3 | `scores/classical/.../spring/vivaldi_four_seasons_spring_m1.score.json` | `modes.dump_modes_ran` | 逾時，3173 個 event | 同上（工具效能限制） | 同上 |
| 4 | `scores/classical/.../summer/vivaldi_four_seasons_summer_m1.score.json` | `modes.dump_modes_ran` | 逾時，3621 個 event | 同上（工具效能限制） | 同上 |
| 5 | `scores/classical/.../summer/vivaldi_four_seasons_summer_m3.score.json` | `modes.dump_modes_ran` | 逾時，5158 個 event（曲庫中 event 數最多的單檔） | 同上（工具效能限制） | 同上 |
| 6 | `scores/classical/.../winter/vivaldi_four_seasons_winter_m1.score.json` | `modes.dump_modes_ran` | 逾時，3255 個 event | 同上（工具效能限制） | 同上 |

## Vivaldi m1/m3 逾時分析（供月月裁決用的實測數字）

`--dump-modes` 逾時只發生在 event 數 ≥ 約 3100 的樂章；同曲庫中 event 數較少的樂章全數通過：

| Event 數 | 樂章 | dump-modes 結果 |
|---|---|---|
| 187 | autumn m2 | 通過 |
| 629 | summer m2 | 通過 |
| 851 | winter m2 | 通過 |
| 1042 | spring m2 | 通過 |
| 2071 | spring m3 | 通過 |
| 2582 | autumn m3 | 通過 |
| 2696 | winter m3 | 通過 |
| **3111** | **autumn m1** | **逾時 FAIL** |
| **3173** | **spring m1** | **逾時 FAIL** |
| **3255** | **winter m1** | **逾時 FAIL** |
| **3621** | **summer m1** | **逾時 FAIL** |
| **5158** | **summer m3** | **逾時 FAIL** |

分界線落在 event 數 2696（通過）與 3111（逾時）之間，與 600s 逾時上限（`tools/verify_score.py` `run_cli` 預設值，非物理容差）吻合，判定為工具逾時而非物理模型缺陷。這五個樂章的其餘全部檢查項（JSON schema、events 排序、MIDI range、frequency_hz 等溫律比對、render、rest、peak、無連續削波、determinism SHA256）**全部 PASS**，唯獨 `--dump-modes` 這一步沒能在時限內跑完 CLI 子行程。

**建議兩選一（由月月定，本輪不擅改）：**
1. 把 `tools/verify_score.py::run_cli` 的 timeout 從 600s 調高（例如 1800s），讓大型曲目的 `--dump-modes` 有機會跑完；此值不在 ROADMAP_PHYSICS.md §6 容差登記表內，理論上屬於工具設定而非物理主張，但仍需月月同意才動，因為會拉長 CI/驗證時間。
2. 保留 600s，把這 5 個樂章登記為「大型曲目 dump-modes 逾時」已知限制，f0/partials 正確性改用同曲目較短的 m2/m3 或抽樣驗證代表，不逐 event 全跑。

## 已修項目（機械性資產問題，已重跑轉綠）

- `scores/library/clockwork/clockwork_ambient_001.score.json`：events 陣列未按 `time` 遞增排序（前人已修，本輪確認 events 現為 0.0/0.5/1.0/1.0/1.5/2.0/2.5，單調不減）。已含在本次 corpus 全跑結果內，其 `schema.events_sorted` 檢查為 PASS，`-> PASS`。不需額外動作。

## 診斷工具確認（非 FAIL，供交接記錄）

- `tools/verify_score.py` 的 FX-bypass 診斷（rest FAIL 時額外用零 FX 副本重渲染同視窗比對 RMS）：已核實只在 (a) rest 檢查已經 FAIL 且 (b) `score_has_nonzero_fx(score)` 為真時觸發（見 `tools/verify_score.py:757`），純診斷用途、不影響 ok/fail 判定、不改動任何容差常數。上表「檔案 1」moonlight sonata 的根因判斷即由此診斷產出的 -120.0 dBFS 對照值坐實。

## 待清理暫存檔（reports/gate_outputs/ 下前人留的底線檔）

以下檔案已將有用資訊（moonlight FX-bypass 明細、Vivaldi 逾時清單、master_volume 現況表）併入本報告，內容與 `verify_all_corpus.log` 完全重複或已無新資訊，予以搬移至 scratchpad（不刪除，保留備查）：

- `_moonlight_complete.log` — 內容與 `verify_all_corpus.log` 內 moonlight 條目逐字相同，已核對。
- `_master_volumes.txt` — 各 score 目前的 `master_volume` 現況表（非「建議值」，是量測當下設定值），本輪未發現任何 score 因 velocity 線性化而 peak 超標，故無需据此调整；数值已保留在 scratchpad 供未來若要人工微调音量时参考。
- `_corpus_filelist_rest.txt` — 分批跑 corpus 時的待跑清單（不含已完成的 library/ 全部），跑批流程已完成，清單失去時效性。
- `_run_corpus.sh` — 對應上述清單的批次執行 shell script，一次性工具，corpus 已跑完不再需要。
- `_run_corpus_driver.log` — 空檔（0 bytes），無資訊。

（見任務回報 JSON 的 `notes` 欄，列出實際搬移後路徑。）

---

## Phase D 更新（2026-07-07）—— 豁免機制 + timeout 提高後的重跑，**部分完成，不覆蓋上表基準**

> 本節記錄 Phase D 對上述 6 個 FAIL 的處置結果與重跑進度。**上表（Phase B, 73/73 零遺漏）仍是唯一一次完整跑完全曲庫的基準**；Phase D 的重跑分成 4 個 chunk 平行執行，寫本節時尚未全數完成，數字如實記錄現況，不宣稱「全綠」。

### 處置結果

1. **`moonlight_sonata_complete.score.json`（原 FAIL #1，rests.rms_below_limit）→ 已解決**：
   新增 `scores/verify_exemptions.json` 登記豁免（check family `rests.rms`，比對 `rests.rms_below_limit` 前綴；理由引用本表上方的 FX-bypass 診斷 -120.0 dBFS，2026-07-07 月月經 Fable 批准）。`tools/verify_score.py` 新增豁免比對邏輯（狹義：僅比對「檔名 + check 名稱前綴」，不影響其他檔案/check）。重跑：**exit 0**，`rests.rms_below_limit` 標記 `[EXEMPT]`（原始 FAIL 訊息保留、不隱藏），其餘檢查獨立 PASS，總結行 `-> PASS (with 1 registered exemption(s))`。見 `reports/gate_outputs/corpus_phase_d_A_examples.log` 第 272/280 行。

2. **5 首 Vivaldi 大樂章逾時（原 FAIL #2–6）→ timeout 已提高，但重跑尚未完成，未證實解決**：
   `tools/verify_score.py::run_cli` 呼叫 `--dump-modes` 的 timeout 已從 600s 提高到 1800s（`tools/verify_score.py:312`）。**但**分派去重跑四季 12 樂章（含原本 5 首逾時的 autumn/spring/summer/winter m1 + summer m3）的兩個 chunk（`corpus_phase_d_B_classical_1.log` 覆蓋 autumn+spring 6 樂章、`corpus_phase_d_C_classical_2.log` 覆蓋 summer+winter 6 樂章）在寫本節時都還停在「載入豁免清單」訊息之後、尚未有任何一首樂章產出 EXIT 結果——即連第一首（autumn_m1 / summer_m1）都還沒跑完。**1800s 是否真的能讓這 5 首在時限內跑完 `--dump-modes` 尚未證實**，這是本輪唯一沒有實測數字可回報的項目。需要繼續執行（可能需要較長時間的背景跑批）才能確認。

### 本輪重跑進度（chunk 級別，寫本節時的快照）

| Chunk | 範圍 | 檔數 | 完成 | 結果 |
|---|---|---|---|---|
| A（examples） | `scores/examples/*.score.json` | 13 | 11/13 | 11 個全數 `RESULT: ALL CHECKS PASSED`（含 moonlight 豁免通過）；2 檔大型曲目（yangqin 系列）仍在跑，尚無結果 |
| B（classical 前半） | Vivaldi autumn + spring（m1–m3）| 6 | 0/6 | 尚無任何一檔產出 EXIT，autumn_m1 疑似仍在跑（無法確認是否卡住） |
| C（classical 後半） | Vivaldi summer + winter（m1–m3）| 6 | 0/6 | 同上，summer_m1 疑似仍在跑 |
| D（originals + library） | `scores/originals/` + `scores/library/`（遞迴） | 48 | 48/48 | 全數 `RESULT: ALL CHECKS PASSED`，0 FAIL |

**結論**：本輪對 moonlight 的豁免處置已驗證生效；對 5 首 Vivaldi 逾時的 timeout 提高**尚未經實測驗證**——`ROADMAP_PHYSICS.md` M3 因此維持 `In progress`，不得標記為「全綠或已登記豁免」，直到 chunk B/C 實際跑完並確認四季樂章在 1800s 內完成 `--dump-modes`。

---

## Phase D 終局更新（2026-07-08）—— corpus 73/73 全數通過，Vivaldi 逾時真根因已修復

> 本節取代上一節（2026-07-07）的「部分完成」快照，為 Phase D 的最終狀態。

### Vivaldi 逾時真根因：dumpModes 字串拼接 O(n²)，非檔案過大

上一節「timeout 提高到 1800s 尚未證實有效」的實測結果：**無效**。重跑時 autumn_m1（3111 events）與 autumn_m3（2582 events）都在 1800s 逾時——而 autumn_m3 在 Phase B 用 600s 都沒逾時過。這個「變得比以前更慢」的矛盾指向工具自身：

- 真兇：`ScoreRenderer::dumpModes()` 用 `juce::String` 累加 JSON 輸出，每次 append 整段重新配置+複製 = **O(輸出大小²)**。3000-event 檔輸出 ~7.5 MB，光字串複製就 >600s（Phase B 的 5 首逾時全是這個，模態計算本身毫秒級）。Phase D 新增 body_mag/strings 欄位讓輸出 ×4 → 時間 ×16。
- 修復：改用 `juce::MemoryOutputStream`（攤銷 O(1) append），輸出內容位元不變。
- 實測：summer_m3（5158 events，全庫最大）dump-modes 從 >1800s 逾時 → **7.2 秒**（55.3 MB 輸出）。
- 規則 6 重驗：三個 build target exit 0；`--full` 之 1b/1c/1d 全 PASS（`phase_d_gate_full_v2.txt`），零回歸。

### 最終 corpus 結果（2026-07-08 重跑）

| Chunk | 範圍 | 檔數 | 結果 |
|---|---|---|---|
| examples | `scores/examples/` | 13 | 13/13 PASS（moonlight 走 `rests.rms` 登記豁免） |
| classical | Vivaldi 四季 m1–m3 | 12 | **12/12 PASS**（含原 5 首逾時檔全過） |
| originals + library | 遞迴全部 | 48 | 48/48 PASS |
| **合計** | | **73** | **72 乾淨 PASS + 1 登記豁免、0 FAIL** |

逐檔證據：`corpus_phase_d_A_examples.log`、`corpus_phase_d_D_originals_library.log`、`corpus_phase_d_{autumn,spring,summer,winter}.log`（後四個為 2026-07-08 修復後重跑）。嚴格單次 `--all` GATE 執行歸檔：`verify_all_corpus_phase_d.log`。

### 教訓（供未來分流參考）

Phase B 曾把這 5 個逾時歸類為「大檔案已知限制」並排入豁免討論。**逾時類 FAIL 在登記為限制/豁免之前，必須先做效能歸因**（複雜度分析或 profiling）——這次差點把一個兩行就能修好的工具 bug 當成物理極限歸檔。
