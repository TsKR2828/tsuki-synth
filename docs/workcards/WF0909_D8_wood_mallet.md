# WF0909-D8：月光空靈鼓兩版 `exciter: finger → wood_mallet`（月月裁決）＋ Rule 10 前後對照報告

> lane：Python/樂譜（只用 `build\` 的 CLI 渲染，不碰 src/、不建置）　工兵：Sonnet　共同規約：`WF0907_README.md`
> 依據：`reports/decision_packets/D8_tongue_drum_diagnosis.zh-TW.md` 選項 1；**月月 2026-09-09 裁決：`wood_mallet`**。
> 這是 Rule 10 改動（渲染輸出改變），月月已做美學裁決，所以本卡**落地**；前後對照報告仍要產出留檔。

## 0. 一句話目標

把兩首月光空靈鼓相關 score 裡 tongue_drum 事件的 `exciter` 從 `"finger"` 改成 `"wood_mallet"`，重渲、驗證、寫前後對照，更新商品表「已知缺陷」。

## 1. 現況（規劃者已核實）
- `scores/examples/moonlight_sonata_movement1_tongue_drum.score.json`：1142 個 `"exciter": "finger"`。
- `scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json`：1142 個 `"finger"` + 1142 個 `"wood_mallet"`（揚琴那半已是 wood_mallet）→ **只改 tongue_drum 事件的**，揚琴事件不動。
- D8 裁決包 §3.5 已有整首 A/B 數字（能量分布 97.4% <200 Hz → 17.6%；主旋律音域 2.6% → 82.4%；斜率 41.48 → 5.53 dB）。
- 商品表：`exports/products/moonlight_batch1/PRODUCT_SHEET.md` 與 `reports/product_sheets/moonlight_batch1_PRODUCT_SHEET.md`「已知缺陷」段。
- **這兩首都在 8 首位元不變代表曲裡**（`reports/gate_outputs/b6_method/sha256_before.txt` 第 2 行 `yangqin_tongue_mix`、第 5 行 `tongue_drum`）。
  所以本卡落地後 8/8 基準**必然**變成 6/8 相同 + 2 首改變（只能是這兩首；其他 6 首若變 = 外溢 = RED）。
  處理：不刪舊基準檔；用 `render_wf_scores.py` 以 `build\` 的 CLI 重渲 8 首，另存 `reports/gate_outputs/b6_method/sha256_before_post_d8.txt` 當**新基準**，
  並在報告與 `WF0907_README.md` §3 註明「2026-09-09 起位元不變基準改用 `sha256_before_post_d8.txt`（D8 月月裁決）」。

## 2. 步驟
1. 用腳本（不要手改 2284 行）只改 `engine == "tongue_drum"` 事件的 `params.exciter`；`git diff --stat` 兩檔行數應各為 1142 行改動；用 jsonschema 驗兩檔仍合法（`verify_score.py` 會做）。
2. 改前先渲染舊版（`git show HEAD:<score> > output/wf0909/D8/old_*.score.json` 另存後渲染），改後渲染新版；兩版各存 WAV 到 `output/wf0909/D8/`。
3. Rule 10 指標（格式照 `reports/b4_hammer_contact_before_after.md`）：整曲 RMS、頻譜質心、200 Hz 以下能量占比、旋律音域占比、MIDI 37→87 斜率（重用 D8 附錄 B 腳本）、前 5 顆音的 f0 / T60。
4. `python tools/verify_score.py <兩檔>` 必須 PASS（若 rest RMS / peak 等既有檢查因音色變化 FAIL → **不登記豁免、不改容差**，status=RED 回報數字）。
5. `melody_verify.py` 兩檔 informational（預期拒答率大降；記數字）。
6. 更新兩份商品表「已知缺陷」：空靈鼓獨奏版的 40 dB 斜率缺陷已由 exciter 改動解除，附新數字；**上架仍受換源授權限制**（月光 CC BY-SA 疑慮未解，別寫成可上架）。
7. 報告 `reports/d8_tongue_drum_exciter_before_after.md`（§0 白話導讀 + 指標表 + 月月裁決記錄）。
8. TODO.md D8 條目不由本卡改（規劃者處理）。

## 3. 禁止
- 不改 src/；不改其他 5 首用到 tongue_drum 的原創曲（另議）；不改揚琴事件；不改任何容差或豁免。

## 4. GATE（`reports/gate_outputs/wf0909_D8_exciter.txt`）
1. 兩檔 diff 各 1142 行且只有 exciter 欄位變（貼 `git diff | grep '^[-+]' | grep -v exciter` 為空的證據）。
2. verify_score 兩檔 PASS。3. 指標表與報告存在。4. `python -m pytest tests -q` 全綠。
5. `git diff --stat` 只含兩個 score、兩份商品表、報告、證據檔（若 8/8 基準需更新則加 `sha256_before_post_d8.txt`）。
