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

## Housekeeping

- ~~Two dev logs coexist: `DEVLOG.md` (zh, current) + `DEV-LOG.md` (en) — converge one.~~ ✅ Merged into `DEVLOG.md`.
- `dsp/Reverb.h` / `dsp/EffectsChain.h` are CLI-side; `effects/*` are plugin-side
  (intentionally separate implementations).
