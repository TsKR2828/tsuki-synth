# TsukiSynth — TODO

> Last updated: 2026-07-07
> Branch: `Codex-fix-bug`
> **Goal: deaf people + AI verify/simulate sound by physical theory, not by ear.**

---

## Current Status

| Item | Status |
|------|--------|
| VST3 / Standalone / CLI build | ✅ exit 0 |
| Code audit (8 bugs) | ✅ fixed (Codex `b5a370d` + this session) |
| Deterministic render (same score → byte-identical) | ✅ NoiseGen seeding |
| Physics verification harness (`tools/physics_verify.py`) | ✅ all 6 engines PASS |
| CLI `--dump-modes` (single source of truth) | ✅ |
| Cimbalom MIDI-pitch tuning (stiff-string comp) | ✅ A4 +11c → +0.1c |
| Equal-RMS engine calibration | ✅ cross-engine 8 dB → 0.2 dB |
| Water gong = true clamped Kirchhoff plate | ✅ (was membrane approx) |
| Physical piano engine (CLI `"piano"`) | ✅ struck stiff steel string |
| Physical piano presets (plugin, on Cimbalom) | ✅ Grand / Bright Upright |
| Free-edge gong option (`plate_free_edge`) | ✅ default free-edge (physical: hung gong) |
| Plugin 4th "Piano" engine tab | ✅ APVTS stores denormalized (safe append) |
| Water gong default = free-edge | ✅ physically correct (hung plate, edges free) |
| Bilingual tooltip popups | ✅ warm white box, EN / 中文 on hover |
| Title bar subtitle for Piano engine | ✅ "PIANO ENGINE \| PHYSICAL MODELING STRING" |

---

## Resolved (was "Needs 月月 decision")

All three items resolved without ear-based verification — physics-based answers:

- [x] **Plugin 4th "Piano" engine tab** — confirmed APVTS stores **denormalized**
      (read JUCE 8 source: `flushToTree` writes `unnormalisedValue`). Appending
      "Piano" at index 3 is safe. Belt-and-suspenders: explicit `engine_index`
      int property in state save/load.
- [x] **Water gong default** — changed to **free-edge** (`plateFreeEdge = true`).
      Physical reasoning: a water gong is a hung plate with edges free. Clamped
      is the unphysical case. A/B scores still available for comparison.
- [x] **In-plugin loudness balance** — already verified by `physics_verify.py
      --levels` (cross-engine 0.2 dB). No ear-based action needed.

## Refinements (optional)

- [ ] Free-edge plate Ω values are approximate (Leissa ν≈0.33) — verify against a
      reference table before treating as precise.
- [ ] Advanced piano physics: hammer-felt nonlinearity, dedicated soundboard
      modes, damper pedal.
- [ ] `--t60` decay measurement is informational (audio decay fitting is noisy).

## Still pending — 月月 待辦（Phase F, 2026-07-11）

### 1. M4-4c：視覺驗收 `ai_radiance_m1.report.html`（AI 不能代做，需要月月的眼睛）

1. 用檔案總管找到 `C:\Users\admin\Desktop\Claude\tsuki-synth\scores\originals\ai_radiance\ai_radiance_m1.report.html`，直接雙擊用瀏覽器打開（不需要開任何程式或連網，單一檔案）。
2. 頁面最上方應該看到一個總結徽章區塊（PASS/FAIL 顏色框），確認顏色看起來是「通過」的顏色（綠色系），文字旁邊還有一行整曲時長／峰值 dBFS／RMS dBFS 的數字。
3. 往下滾動應該看到一張橫向的彩色頻譜圖（像一張色塊漸層圖），確認圖片有正常顯示、不是破圖或空白方塊。
4. 再往下應該看到一排「預測 f0 vs 實測 f0」的散點圖，每個點是綠/黃/紅其中一色，確認大部分點是綠色（少量黃色可接受，紅色代表超出容差）。
5. 再往下是響度曲線（一條隨時間起伏的線圖）與樂句/休止時間軸，確認線圖有畫出來、休止區間有標示（打勾符號或色塊）。
6. 最底部頁尾應該有一份檢查清單文字（列出各項 PASS/FAIL）與容差數字表格。
7. 只要**版面看得懂、圖有正常顯示、能大致看出這首曲子的結構**（哪裡吵哪裡靜、音準大致對不對），就算驗收通過，不需要判斷每個技術細節。看完後告訴 Fable「4c 驗收過了」或指出哪裡看不懂/顯示異常，Fable 會據此把 `ROADMAP_PHYSICS.md` 的 4c 打勾。

### 2. M8-8a：Cubase 人工檢查清單（純視覺確認，不需要用耳朵判斷聲音好壞）

在自己的 Cubase 裡，依序做完以下 4 步，每步只需要**看畫面**確認有沒有出現預期的視覺結果：

1. **Host 掃描辨識** — 打開 Cubase 的外掛管理員（VST3 插件列表），確認清單裡出現「TsukiSynth」這個項目、沒有顯示紅色叉叉或「掃描失敗」字樣。
2. **MIDI 輸入** — 建一軌樂器軌掛上 TsukiSynth，用滑鼠點鋼琴卷簾畫一個音符（或用 MIDI 鍵盤按一下），確認 Cubase 畫面上的音量表（meter）有跳動反應（代表有輸出訊號，不需要用耳朵聽）。
3. **Automation lane** — 在該軌開一條 automation lane，選 TsukiSynth 的任一參數（例如 Cutoff 或 Decay），手動畫一條曲線，播放時確認外掛視窗裡對應的旋鈕/滑桿有跟著曲線同步轉動或移動。
4. **State round-trip** — 存檔（Ctrl+S）、關閉 Cubase 專案、重新打開，確認外掛視窗裡剛剛設定的參數位置（旋鈕角度/滑桿位置）跟關閉前一致，沒有跳回預設值。

四步都是看畫面有沒有反應/位置對不對，不需要判斷音色好壞。完成後跟 Fable 說「Cubase 四項都過了」（或指出哪一項有異常），據此更新 `ROADMAP_PHYSICS.md` M8-8a 為完整完成。

### 3. Phase F 變更何時 push（M8-8b）

本輪（Phase F）未 commit/push 的變更清單：`tools/report_html.py`（新增）、`ROADMAP_PHYSICS.md`、`README.md`、`tools/verify_score.py`、`reports/gate_outputs/pluginval_L5.txt`（新增）、`reports/gate_outputs/pluginval_L10.txt`（新增）、`scores/examples/water_gong_clamped.report.html`（新增）、`scores/originals/ai_radiance/ai_radiance_m1.report.html`（新增）。全部停在 unstaged，等月月看完上面兩項視覺驗收後，一併決定 commit 訊息與 push 時機（Rule 7，Fable 不會自己動）。

- [ ] DAW validation (host scan / automation / state round-trip) on a real DAW — see Cubase checklist above.
- [ ] `push` remaining commits for Phase F changes when 月月 is ready (see list above). `Codex-fix-bug`/`master` branches confirmed not to exist (`git branch -a`, 2026-07-11) — that specific merge decision is moot.
- [ ] **CI workflow created, `--full` blocker now resolved — only `push` left** (`ROADMAP_PHYSICS.md` M1 task 1f):
      `.github/workflows/physics.yml` added 2026-07-02 (Windows runner, MSVC,
      builds CLI + Standalone + VST3, runs `physics_verify.py --full`).
      2026-07-05 update: M1 task 1e (`--full` flag) now exists and passes
      locally (`reports/gate_outputs/full_FINAL_gate.txt` → ALL WITHIN
      TOLERANCE), so the workflow's harness step will no longer fail with
      "unrecognized arguments." The only remaining blocker is the first push
      to GitHub to trigger the workflow at least once (M1 GATE requires "CI
      workflow 在 GitHub 上綠燈一次以上") — this is a `push`, so per rule 7
      (不 commit/push) it is 月月's call, not something to do automatically.
      README badge already points at `TsKR2828/tsuki-synth` (confirmed via
      `git remote -v`), not a placeholder.

## 月月待裁決（Phase D, 2026-07-07）

已解決、從清單移除的項目（不再需要裁決）：
- ~~`moonlight_sonata_complete` 休止超標~~ → 已登記為 `rests.rms` 豁免（`scores/verify_exemptions.json`，2026-07-07 月月經 Fable 批准），`verify_score.py` 重跑 exit 0。
- ~~5 首大型 Vivaldi 樂章 `--dump-modes` 逾時~~ → **真根因已找到並修復（2026-07-08）**：不是檔案太大，是 `ScoreRenderer::dumpModes()` 用 `juce::String` 累加輸出，每次 append 整段重配置複製 = O(n²)——3000 events 的 dump 光字串複製就 >600s。改用 `juce::MemoryOutputStream`（攤銷 O(1) append）後，最大的 summer_m3（5158 events）dump 只要 **7.2 秒**。timeout 1800s 保留作為安全網但已不再需要。四季 12 樂章全部重跑 **ALL CHECKS PASSED**（`reports/gate_outputs/corpus_phase_d_{autumn,spring,summer,winter}.log`）。
- ~~cimbalom/piano 共用增益常數的 piano RMS 偏離約 1.4 dB~~ → 已接受此妥協。
- ~~M2 `--amps` 殘差（cimbalom/piano p3-p5、water_gong p3-p5、tongue_drum p2）~~ → **真根因已找到並修復（2026-07-09，Phase E）**：不是 C++ 渲染 bug，是 `tools/physics_verify.py` 的 `synth_theory_signal()` 把 `decay` 欄位當 1/e 時間常數，`ModalResonator::excite()` 定義它是 T60，換成 `exp(-ln(1000)*t/decay)` 後全部收斂到 ≤±0.22 dB，`--amps`/`--full` 皆 `RESULT: ALL WITHIN TOLERANCE`（`reports/gate_outputs/phase_e_gate_amps.txt` / `phase_e_gate_full.txt`，根因推導 `reports/gate_outputs/amps_residual_attribution.md`）。容差未動；未改 `src/` 渲染碼，音訊位元不變，不需規則 10 前後對照或 corpus 重跑。原授權的「Phase E：新增 `--dump-signal-stage` 除錯旗標」改用範圍更小的 `--body-amount`/`--no-exciter-noise`/`--num-strings` 差異化渲染旗標（`src/dsp/DiagnosticOverrides.h`）就足夠隔離根因，未另建 `--dump-signal-stage`。

真正還剩的裁決/待完成項：

- [x] **M2 `--amps` 殘差 → 月月裁決（2026-07-09）：選 (b)，授權 C++ 層級儀器化
      追查** → **已解決，見上方「已解決」清單第 4 項（Phase E 根因修復）**。
- [x] **M2 力脈衝音色改變 → 保留**（2026-07-09 月月委任 Fable 決定）：物理正確
      （軟槌打中音域本來就發不出亮音）、有完整前後對照報告
      （`reports/m2_before_after_report.md`）。**Phase E 修正只動 harness 端理論
      預測公式，未再動任何 `src/` 渲染碼，此前的音色改變結論不受影響、不需要
      新的前後對照報告。**
- [x] **CI 紅燈連動 → 採「M1 範圍綠燈 + amps 非阻斷可視化」**（2026-07-09 月月委任
      Fable 決定）：`physics_verify.py` 新增 `--skip-amps`（僅配合 `--full`，
      不影響 `--amps` GATE 本身）；`.github/workflows/physics.yml` 主 GATE 步驟改跑
      `--full --skip-amps`，另加 `continue-on-error` 的 `--amps` 步驟讓 M2 數字
      每次 CI 都看得到但不擋綠燈；verify_score 步驟改跑 5 檔跨引擎 smoke 子集
      （全 corpus 是本地 release gate，證據已歸檔）。**Phase E 更新（2026-07-09，
      unstaged，待 push）**：2d 已過，依 workflow 註解原本的承諾把 `--skip-amps`
      從主 GATE 步驟拿掉、刪除非阻斷的 `--amps` 步驟，CI 主 GATE 改跑完整
      `--full`（涵蓋 1b+1c+1d+2d）。規則 7 擋住尚未 push，新版 workflow 在
      GitHub 上實際綠燈一次還沒發生，待月月 push 後確認。
- [x] ~~四季 12 樂章重跑~~ → **完成（2026-07-08）**：dumpModes O(n²) 修復後 12/12
      全部 ALL CHECKS PASSED。corpus 總計 **73/73：72 乾淨 PASS + 1 登記豁免
      （moonlight）、0 FAIL**。**M3 GATE 正式達成**：單次 `--all` → exit 0、
      `73/73 passed (1 exemption), 0 failed`
      （`reports/gate_outputs/verify_all_corpus_phase_d.log`）。M3 已標 Done。
      **Phase E 未改動任何渲染碼，故本輪不需要重跑整個 corpus**
      （`tools/verify_score.py --all` 上次結果依然有效）。
- [x] ~~CI 綠燈與 `--amps` 殘差連動（重要）~~ → **已解決**：2d 已過，見上方
      「CI 紅燈連動」項的 Phase E 更新——`--skip-amps` 已拿掉，選項 (a) 等於
      自然達成，不再需要 (b)/(c) 的權宜措施。
- [ ] **M8 工程收尾** — DAW（Cubase）驗證四項（host scan / MIDI / automation /
      state round-trip）尚未執行；`Codex-fix-bug` merge → master 的時機仍待月月
      裁決（通常會在 push/CI 綠燈之後）。

## 月月待裁決（Phase G / M7-7a，2026-07-12）

- [ ] **`verify_score.py` 的 `MODE_F0_TOL_CENTS` 是否授權下一輪改量測法收緊到 5 cents？**
      現況：`physics_verify.py` 的 f0 容差已收緊為全域 5.0 cents 並全綠通過
      （`reports/gate_outputs/phase_g_gate_full_f0.txt`），因為它量測的是
      `measure_f0()` 對渲染音訊做的**功率加權質心**（自動平均掉多弦拍頻）。
      但 `verify_score.py` 的 `check_modes()`／`MODE_F0_TOL_CENTS` 量測的是
      `--dump-modes` JSON 裡 `partials[0]`——只讀多弦課「第 0 條弦」的原始值，
      而 `CimbalomVoice::noteOn()`（`src/engines/CimbalomEngine.h`）依設計把
      第 0 條弦精準調到 `-detuningCents` cents（預設 detuningCents=5.0 時，
      恰好 -5.000 cents）。這不是聲學誤差，是「量哪一條弦」的量測點選擇。
      **實測**（5 首跨引擎真實曲目，2026-07-12）：
      - `ai_radiance_m1.score.json`（64 modal events，cimbalom/piano 型）：max 5.002 cents
      - `vivaldi_four_seasons_autumn_m2.score.json`（187 events）：max 5.005 cents
      - `moonlight_sonata_movement1_yangqin.score.json`（1142 events）：max 5.013 cents
      - `water_gong_clamped.score.json`（2 events，單弦引擎）：max 0.003 cents
      - `akashic_ambient_001.score.json`（2 events，單弦引擎）：max 0.003 cents
      若把 `MODE_F0_TOL_CENTS` 收緊到 5.0，上面 3 首含多弦引擎的真實曲目會
      立即 FAIL（都卡在 5.00~5.01，剛好卡在「第 0 條弦」的設計偏移上），即使
      這些曲目實際渲染出的音訊已被 `physics_verify.py` 驗證在真實基頻的
      0.05 cents 內。**維持誠實，本輪未收緊**（留在 12.0），因為要讓這個檢查
      有意義地收緊，需要先把「量什麼」從「單一弦」改成「多弦課的質心/平均」
      ——這是 `check_modes()` 的邏輯變更，不是單純調容差數字，超出本次任務
      （容差收緊）範圍。**請月月決定**：(a) 接受 12.0 作為這個檢查往後的正式
      現值（承認它量測的是「dump 是否合理」而非「聽感基頻」）；或 (b) 授權下一
      輪改寫 `check_modes()` 的 f0 量測邏輯（例如改成讀 `strings` 陣列全部
      弦、依模型自身的每弦增益加權平均），之後再收緊到 5.0。詳細技術理由見
      `tools/verify_score.py` 的 `MODE_F0_TOL_CENTS` 上方大段註解，以及
      `ROADMAP_PHYSICS.md` §6 / M7-7a。

## 已核准並執行（原 Phase I 待裁決三項，2026-07-12 月月核准，Phase H/K 已落地）

以下三項原本登記在此的待裁決，**月月已於 2026-07-12 同意執行**，兩項都已落地在 `data/materials.json`
與 `src/physics/PlateModel.h`，並補完規則 10 前後對照報告 `reports/phase_h_before_after.md` + 全 corpus
重跑（`reports/gate_outputs/verify_all_corpus_phase_h.log`，73/73 PASS，0 failed，無新增回歸）。
保留紀錄供追溯，不再是待決項：

- [x] ~~`PlateModel.h` free-edge 圓板 `(m=4,n=0)` 特徵值提案：21.83f → 21.6f？~~
      **已執行，改為 21.527f**（獨立重解精確特徵方程的值，比 Table 2.5 的 ±2% 漸近近似 21.6 更精確；
      兩者都與舊值差距 >1%，方向一致）。只影響 `water_gong_free` 一個泛音，隔離驗證見
      `reports/gate_outputs/phase_h_eig_delta.txt`，前後對照見 `reports/phase_h_before_after.md` §1。
- [x] ~~`materials.json` — `rubber.youngs_modulus = 1.5e9` Pa 是否為刻意選值？~~
      **已執行，改為 5e6 Pa**（真實橡膠量級）。已知後果：rubber 的 T60 崩到 14-28ms
      （近乎瞬時悶響，見下方「Phase K 新待裁決」的 f0 材質掃描 FAIL）。
- [x] ~~`materials.json` — 阻尼常數（alpha/beta_air/gamma_radiation）全數 42 個值皆無法溯源到具體
      文獻出處，是否接受現況？~~
      **已執行**：14 種材質的 `damping.alpha` 全部改用 `T60≈2.2/(f·η)`（η=文獻損耗因子）反推的新值
      （`reports/materials_physicalization_proposal.md`），修正了 `wood_spruce.alpha` 排序異常
      （雲杉現在正確地是四種木料中阻尼最低者）。`beta_air`/`gamma_radiation` 仍找不到文獻來源，
      維持「待溯源」未動。已知後果：steel/aluminum 等低損耗金屬的 T60 大幅拉長（MIDI60 從 ~2s
      拉長到 ~27-47s），見下方「Phase K 新待裁決」的 T60 harness FAIL。

## 月月待裁決（Phase K，2026-07-12 —— 上面三項執行後新暴露的 harness FAIL）

上面三項數值修正落地後，`reports/phase_h_before_after.md` 用 binary A（HEAD）/B（現況）前後對照 +
`physics_verify.py --full`/`--t60` 重跑，發現 3 個新 FAIL。**全部確認是「阻尼常數變得更真實」這件事
撞上既有 harness 的固定假設，不是渲染管線的 bug**（根因追蹤見該報告 §3/§4/§6），但仍是真實的新 FAIL，
如實列出，**沒有自行加任何豁免/例外**，留給月月/Opus 決定：

- [x] ~~**`cimbalom`/`piano` 於 MIDI 60 的 `--t60` 判定從 PASS 轉 FAIL（ratio 0.28，`reports/gate_outputs/phase_h_gate_t60.txt`）。**~~
      **已收斂（Phase I，2026-07-13）**：延續 M5-5a/5b 的量測方法（未動容差、未動 `T60_PROBE_DUR` 之外的判定邏輯），
      本輪 `--t60 --notes 60 72` 重跑 → `RESULT: ALL WITHIN TOLERANCE`，cimbalom/piano MIDI 60 皆 PASS。
      證據：`reports/gate_outputs/phase_i_gate_t60.txt`。以下原始根因分析保留供參考：
      根因：steel 材質新 `alpha`（`0.5→0.0238`）把 MIDI60 的模型 T60 從舊值拉長到 **26.85 秒**，但
      `T60_PROBE_DUR`（M5-5a 定死的 harness 常數）只有 **5.0 秒**，note-off 前只有約 4.5 秒可用來擬合
      衰減曲線。更關鍵的是多弦課（cimbalom/piano）額外做的「拍頻週期平均」步驟，其假設「拍頻起伏遠小於
      衰減本身」在衰減這麼慢時不再成立，拍頻凹陷把回歸出來的斜率帶偏，量出一個只有模型值 28% 的假 T60。
      單弦引擎（tongue_drum/water_gong/water_gong_free）沒有這個拍頻平均步驟，同樣被材質修正拉長 T60，
      量測依然精確（ratio 1.00）。**請月月決定**：(a) 接受現況——這是 harness 測量侷限而非渲染錯誤，
      登記為已知限制，`§6` 容差不動；(b) 授權下一輪把 `T60_PROBE_DUR` 加長（例如 30-40 秒）以正確測量
      新的長 T60（harness 邏輯改動，需重新產生所有 T60 GATE 存證）；(c) 授權下一輪修
      `measure_t60()` 的拍頻平均邏輯，讓它偵測「拍頻週期數遠少於衰減所需週期數」時改用別的估計法。
- [x] ~~**`rubber` 材質在 `cimbalom`/`tongue_drum`/`water_gong` 的 f0 材質掃描全部新增 FAIL
      （-41.6/-108.5/+55.5 cents，`reports/gate_outputs/phase_h_gate_full.txt`）。**~~
      **已收斂（Phase I，2026-07-13）**：本輪 `--full` 重跑，`cimbalom`/`tongue_drum`/`water_gong` 三引擎
      rubber 材質 f0 皆 `[OK]`（-1.3 / -4.3 / -1.1 cents，容差 5.0 cents，見 `reports/gate_outputs/phase_i_gate_full.txt`
      第 373/382/391 行）。以下原始根因分析保留供參考：
      根因：`rubber.youngs_modulus`（`1.5e9→5e6`）+ `rubber.damping.alpha`（`2.5→35.676`，橡膠文獻損耗
      因子 η≈0.3 遠高於其他材質）共同把 rubber 的 T60 壓到 **14-28 毫秒**——`materials_physicalization_proposal.md`
      §6 早就預測到這一點（"collapses to a near-instant thud"）。用 `measure_f0()` 直接對新材質重新
      探測：三個引擎全部回傳 `None`（找不到頻率），因為它跳過的前 50ms 攻擊瞬態之後，訊號已經完全衰減
      殆盡。`scan_materials()` 的 fallback（`measure_partials()`，對含攻擊瞬態的全波形做 FFT）量到的
      其實是瞬態噪聲頻譜的偶然峰位，不是穩定基頻——這解釋了為什麼三個引擎的偏移方向、量級都不一樣，
      不是同一種一致的偏差。`ROADMAP_PHYSICS.md` 的材質掃描判定訊息本身早就預留「記錄此材質為不支援」
      這條路。**請月月決定**：(a) 接受現況——把 `rubber` 正式登記為這三個引擎 f0 材質掃描的「已知不
      支援」項目（真實橡膠阻尼確實會讓槌擊變成無明確音高的悶響，這是文獻一致的物理行為）；(b) 授權
      下一輪重新檢視 `rubber` 的 `η` 選值是否要往「有明確音高但仍然悶」的方向調整（文獻範圍 0.1-1
      的低端而非中段選值），需要另一輪規則 10。
- [x] ~~**`piano` MIDI 108（宣告範圍最高音）f0 判定從 PASS 轉 FAIL
      （binary A +0.23 cents → binary B +5~+7 cents，`reports/gate_outputs/phase_h_gate_full.txt`）。**~~
      **已收斂（Phase I，2026-07-13）**：本輪 `--full` 重跑，`piano` MIDI 108 f0 判定 `[OK]`（見
      `reports/gate_outputs/phase_i_gate_full.txt` 第 353 行起）。以下原始根因分析保留供參考：
      根因：同一批 steel `alpha` 修正把 T60 大幅拉長後，固定的 0.05-1.55 秒分析窗內，原本很快衰減乾淨
      的高頻泛音現在還在響，跟基頻之間的頻譜洩漏增加，把功率質心估計值拉偏了幾個 Hz——這是「衰減變得
      更真實」撞上「固定分析窗」這個 harness 假設的又一個案例。**請月月決定**：(a) 接受現況，登記為
      已知限制；(b) 授權下一輪縮小 `ENGINE_RANGES['piano']`（把 MIDI 108 移出宣告範圍）；(c) 授權
      下一輪調整 note-range scan 在高音符的分析窗長度。
      *（此項不影響 M7 的 7a f0 容差本身，`§6` 容差 5.0 cents 未動——這是 note-range scan 的個案
      FAIL，跟 M7 已完成的容差收緊是兩件事。）*

**materials 物理化 keep/revert 決策 — resolved-kept（Phase I，2026-07-13）**：月月 2026-07-12 決定材質物理化
（Phase G+H：density/youngs_modulus/poisson_ratio 溯源 + 阻尼 alpha 全面改為文獻 η-Q 推導值）**維持不 revert**。
上面三項 Phase H 遺留的 harness FAIL 已在本輪（Phase I）測量法調整後全部收斂為 PASS，`--full`/`--t60`/`--amps`
三個 GATE 現況皆 `ALL WITHIN TOLERANCE`（`reports/gate_outputs/phase_i_gate_{full,t60,amps}.txt`），本項待裁決
正式關閉。

**重要交叉驗證（供裁決參考）**：`python tools/verify_score.py --all` 全 corpus 重跑
（`reports/gate_outputs/verify_all_corpus_phase_h.log`）結果 **73/73 PASS，0 failed**（1 個既有登記
豁免，moonlight `rests.rms`，與本輪修正無關）——**上面 3 個 FAIL 全部只出現在 `physics_verify.py`
的合成探針測試（人工 MIDI 60/72/108 音符 + rubber 材質掃描），不在任何實際曲目 corpus 的路徑上**，
所以月月現有的所有曲目都沒有因為這兩項修正而壞掉或產生休止區溢出。

## Housekeeping

- ~~Two dev logs coexist: `DEVLOG.md` (zh, current) + `DEV-LOG.md` (en) — converge one.~~ ✅ Merged into `DEVLOG.md`.
- `dsp/Reverb.h` / `dsp/EffectsChain.h` are CLI-side; `effects/*` are plugin-side
  (intentionally separate implementations).
