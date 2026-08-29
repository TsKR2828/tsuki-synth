# B5 no-op 證明報告

> 依據 `docs/workcards/B5.md` §9 規格產出。

## 1. 一句話結論

本卡在 `data/materials.json` 四種木料新增可選 `orthotropic` schema 欄位，並在
`src/physics/MaterialDB.h` 新增對應的 fail-closed 解析/驗證邏輯——**目前沒有
任何程式碼路徑消費這批新資料**（`PlateModel.h`/`BeamModel.h` 的 Kirchhoff
板/梁公式仍是單一標量 `E`/`nu`），因此音訊渲染輸出應為 bit-exact 不變；下方
SHA256 與 corpus 結果證實了這一點：**零行為變化**。

## 2. SHA256 bit-exact 對照（GATE 第 8 項）

來源：`reports/gate_outputs/b5_sha256_compare.txt`
（before = HEAD=53e6c76，pre-B5；after = 本卡 R4 註解編輯 + orthotropic
schema 落地後，2026-08-28 渲染）

| # | 檔案 | before SHA256 | after SHA256 | 是否相同 |
|---|---|---|---|---|
| 1 | moonlight_sonata_movement1_yangqin/moonlight_sonata_i_yangqin.wav | 49514b00…f5a687e | 49514b00…f5a687e | IDENTICAL |
| 2 | moonlight_sonata_movement1_yangqin_tongue_mix/moonlight_sonata_i_yangqin_tongue_mix.wav | 7b0413dd…8e9b8b79b | 7b0413dd…8e9b8b79b | IDENTICAL |
| 3 | akashic_notify_001/UI_Bright_OneShot_E6.wav | ff3e3cf8…a1b0bb34a | ff3e3cf8…a1b0bb34a | IDENTICAL |
| 4 | forest_action_001/Impact_Punch_OneShot_C4.wav | 4e621d83…310b451f5cb | 4e621d83…310b451f5cb | IDENTICAL |
| 5 | forest_notify_001/UI_Bright_OneShot_B6.wav | e21a06f3…844bdfa98c | e21a06f3…844bdfa98c | IDENTICAL |
| 6 | forest_transition_001/Whoosh_Airy_OneShot_D5.wav | e3036f8f…8c66f3d4f6 | e3036f8f…8c66f3d4f6 | IDENTICAL |
| 7 | forest_ui_001/UI_Soft_OneShot_F5.wav | e74063ba…d34caf4ea3463fc8 | e74063ba…d34caf4ea3463fc8 | IDENTICAL |
| 8 | rabbit_notify_001/UI_Bright_OneShot_G6.wav | e37d8e6e…5911a7620cc7d61 | e37d8e6e…5911a7620cc7d61 | IDENTICAL |
| 9 | rabbit_ui_001/UI_Soft_OneShot_A5.wav | 43fc77a7…6129494a3ca02d226 | 43fc77a7…6129494a3ca02d226 | IDENTICAL |
| 10 | ai_radiance_m1/Original_AI_Radiance_Movement1.wav | 74122637…852238ec20f8204d | 74122637…852238ec20f8204d | IDENTICAL |
| 11 | rules_v2_demo_001/TsukiSynth_Rules_v2_Demo.wav | 6b3ad2b6…74277468faf8f49ee | 6b3ad2b6…74277468faf8f49ee | IDENTICAL |
| 12 | melody_sentinel/melody_sentinel.wav | a16a797b…d09f5f25e238727bc | a16a797b…d09f5f25e238727bc | IDENTICAL |
| 13 | test_glide/test_glide.wav | 47774f4f…0cd980e9ec31a6623 | 47774f4f…0cd980e9ec31a6623 | IDENTICAL |

**RESULT: 13/13 IDENTICAL**（超過 §6 步驟 9 要求的至少 4 首，含使用
`wood_spruce` 等木料材質的曲目）。

## 3. corpus 四分片結果摘要（GATE 第 7 項）

來源：`reports/gate_outputs/b5_corpus_{A,B,C,D}.txt`（
`python tools/verify_score.py --all --shard-index {0..3} --shard-count 4`）

| 分片 | 結果 | PASS 數 | 豁免數 |
|---|---|---|---|
| A（index 0） | 19/19 passed | 19 | 1（既有豁免，非新增） |
| B（index 1） | 18/18 passed | 18 | 0 |
| C（index 2） | 18/18 passed | 18 | 0 |
| D（index 3） | 18/18 passed | 18 | 0 |
| **合計** | **73/73 passed, 0 failed** | 73 | 1（既有，未新增） |

四分片總數 73、PASS 73、豁免 1 筆與本卡改動前的既有基準完全相同——沒有新增
豁免、沒有任何檔案結果改變。

## 4. 假設驗證結論

SHA256（第 2 節）與 corpus 四分片（第 3 節）兩項結果均與改動前基準逐一相同，
**no-op 假設成立**：新增的 `orthotropic` schema 對應驗證邏輯是零消費路徑，
未觸發任何音訊輸出或既有測試判定的變化。不需要依 §12 停下條件停工。

## 5. 選種裁決記錄

依 `docs/workcards/B5.md` §4.2「選種說明」，本卡對三個有歧義的樹種對應向
月月請示，**月月於 2026-08-28 裁決：「照建議值走」**，即：

- `wood_spruce` → Spruce, Sitka
- `wood_maple` → Maple, sugar
- `wood_oak` → Oak, red
- `wood_birch` → Birch, yellow（Wood Handbook 表列唯一條目，無歧義，不需裁決）

此答覆已滿足 §4.2「明確表示『不在意，照建議值走』也算明確答覆」的完成條件，
`MaterialDB.h` 新增 `Orthotropic` struct 上方的 R4 註解已依此填入裁決日期與
結論，GATE 因此解鎖。
