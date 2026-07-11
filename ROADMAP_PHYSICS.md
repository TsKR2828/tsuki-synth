# TsukiSynth 物理精確化 Roadmap v2（驗收唯一依據）

> 建立日期：2026-07-02
> 地位：**本文件是後續開發的驗收唯一依據**。舊 `ROADMAP.md` 保留為歷史紀錄與產品向 backlog。
> 分支：`Codex-fix-bug`（基準線 = 2026-06-17 狀態，全 6 引擎 harness PASS）
>
> **給 AI 開發者（Opus / Codex / Claude）：開工前必讀 §1 強制規則與 §6 容差登記表。**

---

## 0. 目標與驗收哲學

### 最終目標

**聾人 + AI 不靠聽感、靠物理理論精確模擬聲音。**

三支柱：

1. **可重現性** — 同一份 score 渲染結果位元一致（同環境），跨環境有明確容差標準。
2. **物理可驗證性** — 渲染出來的音訊，其頻率、振幅、衰減都能和理論預測值機器比對。
3. **樂器物理正確性** — 模型使用真實物理方程（弦/梁/板），常數可溯源到文獻或推導。

### 驗收哲學

- **唯一驗收標準是理論正確。** 月月的聽感不參與驗收，AI 的「聽起來像」描述也不算數。
- 每個 Milestone 有 **GATE**：一組可執行的命令 + 明確的數字門檻。GATE 全過 = 完成，否則 = 未完成。
- 「MVP 先做一半」不存在於本文件。Milestone 內任務全部完成才能標 Done。

### 驗證域聲明（哪些東西受物理主張保護）

| 元件 | 域 | 說明 |
|---|---|---|
| Cimbalom / Piano（StringModel） | ✅ 域內 | 敲擊剛性弦，含非諧性 |
| Tongue Drum（BeamModel） | ✅ 域內 | free-free Euler-Bernoulli 梁 |
| Water Gong（PlateModel） | ✅ 域內 | Kirchhoff 圓板（clamped + free-edge） |
| Custom Harmonics | ⚠️ 半域內 | 加法合成，頻率比可驗但非物理推導 |
| FM Piano | ❌ 域外 | 已誠實標註「非物理合成」，維持此標註 |
| 效果鏈（Reverb/Delay/Comp/Dist） | ❌ 域外 | 驗證一律 FX 全關；用了效果的 score 不在物理主張範圍 |
| 未來 Sample Layer / Granular | ❌ 域外 | 若實作，必須明確標註，不得混入物理主張 |
| Chromatic scaling（尺寸→音色、MIDI→音高） | ⚠️ 設計聲明 | 混合系統：物理決定頻譜形狀、平均律決定基頻。對外表述必須講明，不得宣稱「全物理」 |

---

## 1. AI 開發者強制規則

任何 AI（Opus / Codex / Claude / 其他）在本 repo 開發時必須遵守。違反任一條 = 該輪工作不予驗收。

1. **驗收只認 GATE 命令輸出，不認敘述。** 回報「完成」時必須附上 GATE 命令與完整輸出（或輸出檔路徑）。沒有輸出 = 沒有完成。
2. **禁止調寬任何容差。** §6 容差登記表的數值只能由月月批准修改。達不到門檻 → 回報實測數字 + 原因分析，停下來等決定；不得自行放寬後宣稱通過。
3. **禁止縮小 GATE 範圍。** 不得只跑部分引擎、部分音符、部分 score 就宣稱整個 GATE 通過。
4. **禁止 hardcode 無法溯源的物理常數。** 每個新常數必須在程式碼註解或文件標明來源：文獻（書名/表號）、推導（公式）、或量測（方法）。
5. **Milestone 不可部分標記 Done。** 任務沒全完成就標 `In progress` 並列出剩餘項目。
6. **改動任何 `src/physics/`、`src/engines/`、`src/dsp/`、`src/score/` 之後**，宣稱完成前必跑：
   - `python tools/physics_verify.py`（全引擎）→ `ALL WITHIN TOLERANCE`
   - 三個 build target（CLI / Standalone / VST3）exit 0
7. **不 commit、不 push。** 檔案留 unstaged，由月月審完決定（現行工作規則）。
8. **文件同步。** 完成任何 GATE 後更新本文件 §2 狀態欄與 `TODO.md`。
9. **域外功能標註。** 任何驗證域外的新功能（見 §0 表），文件與 UI 必須標註，比照 FM Piano 的做法。
10. **音色會變的改動需告知。** 任何讓既有 preset / score 渲染結果改變的物理修正（如 M2），必須產出前後對照的頻譜差異報告，讓月月知情後決定。

---

## 2. Milestone 總覽

| # | 名稱 | 優先 | 支柱 | 狀態 |
|---|------|------|------|------|
| M1 | 驗證廣度擴大 + CI | P0 | 驗證 | **Done（2026-07-09，GATE 全過）**：本地 `--full` ALL WITHIN TOLERANCE（`reports/gate_outputs/full_FINAL_gate.txt`，Phase E 重跑見 `reports/gate_outputs/phase_e_gate_full.txt`）+ **GitHub CI 綠燈一次以上**（run 28957524611，`build-and-verify` ✓ 9m53s，月月 2026-07-09 授權 push 觸發，此時 M2 尚未過故 CI 跑 `--full --skip-amps`）。**Phase E 更新（unstaged，待 push）**：M2（`--amps`）已於本地全過，`.github/workflows/physics.yml` 已拿掉 `--skip-amps` 並刪除原本非阻斷的 M2 可視化步驟，CI 主 GATE 現改跑完整 `--full`（涵蓋 1b+1c+1d+2d）；**新版 workflow 已於 GitHub 綠燈**（月月 2026-07-09 授權 push `64e2836` 後，run 28960975003 `build-and-verify` ✓ 9m15s，完整 `--full` 含 2d 全過）。|
| M2 | 激發物理化 + 振幅譜驗證 | P0 | 樂器物理 | **Done（2026-07-09，Phase E，GATE 全過）**：2a–2e 全部實作完成，Phase D windowed-synthesis 預測法已就位；**Phase E 找到並修正最後根因**——`tools/physics_verify.py` 的 `synth_theory_signal()`（THEORY 端 harness 腳本，非 `src/` 渲染碼）把 `--dump-modes` 的 `decay` 欄位當成 1/e 時間常數 τ 衰減，但 `ModalResonator::excite()` 自己的公式明確把 `decayTime` 定義為 **T60**（`decayCoeff = exp(-6.9078f/(decayTime*sampleRate))`）——理論訊號衰減慢了 ln(1000)≈6.9078 倍，且不同 partial 的 decayTime 不同，此比例誤差在「相對基頻 dB」判定下不會抵消。換成正確指數 `exp(-ln(1000)*t/decayTime)` 後，5 個 modal 引擎（cimbalom / tongue_drum / water_gong / water_gong_free / piano）前 5 partial 全部收斂到 ≤±0.22 dB（原本 cimbalom/piano p3–p5 -3.0~-4.5 dB、water_gong p3–p5 -3.9~-8.0 dB、tongue_drum p2 -12.60 dB 全部 FAIL → PASS）。**容差全程未動（±3.0 dB，§6 Rule 2）**——只修了理論預測公式，不是放寬判定線；差異化渲染隔離實驗（`--body-amount 0` / `--no-exciter-noise` / `--num-strings 1`，見 `src/dsp/DiagnosticOverrides.h` + `src/cli/RenderApp.cpp` 新增的診斷專用旗標）逐一排除 BodyResonance / 敲擊噪聲 / 多弦拍頻三個候選機制，確認只有 decay-law 指數修正能關閉殘差，且這些診斷旗標預設為「不覆寫」sentinel、不在任何 score JSON / 預設 / 正常 CLI 呼叫路徑被觸發（SHA256 no-flags render 前後位元完全相同，`audio_path_changed=false`，故本輪不需規則 10 前後對照報告或整個 corpus 重跑）。GATE 證據：`reports/gate_outputs/phase_e_gate_amps.txt`（`RESULT: ALL WITHIN TOLERANCE`）、`reports/gate_outputs/phase_e_gate_full.txt`（含 `2d amplitude judgment: PASS`）；根因全推導見 `reports/gate_outputs/amps_residual_attribution.md`（承接 `amps_rootcause_analysis.md`）。|
| M3 | 整曲驗證工具 `verify_score.py` | P0 | 驗證 | **Done（2026-07-08，GATE 全過）**：單次 `verify_score.py --all` → `73/73 score(s) passed all checks (1 check(s) covered by registered exemption(s)), 0 failed`、exit 0（證據 `reports/gate_outputs/verify_all_corpus_phase_d.log`）。72 乾淨 PASS + 1 登記豁免（moonlight `rests.rms`，`scores/verify_exemptions.json`）。原「5 首大 Vivaldi 逾時」真根因＝`ScoreRenderer::dumpModes()` 的 `juce::String` 累加 O(n²)，改 `MemoryOutputStream` 後 5158-event 檔 dump 僅 7.2s，四季 12/12 全 PASS；逐檔證據 `corpus_phase_d_*.log`。規則 6 重驗：`--full` 之 1b/1c/1d 全 PASS 零回歸（`phase_d_gate_full_v2.txt`） |
| M4 | 視覺驗證報告（聾人介面） | P0 | 驗證/無障礙 | **In progress（2026-07-11）**：4a/4b 完工——`tools/report_html.py` 新增，`verify_score.py --html <score.json>` 產出單檔自足 HTML 視覺驗證報告（總結徽章／頻譜圖／f0 預測-實測對照／響度曲線＋休止驗證／樂句休止時間軸／頁尾），對 `scores/examples/water_gong_clamped.score.json`（110.8 KB）與 `scores/originals/ai_radiance/ai_radiance_m1.score.json`（~484 KB）皆 GATE exit 0，程式化驗證 0 個 `http(s)://` 外部參照、PNG/SVG 皆合法格式。過程中修正一個 f0 量測 bug（拋物線內插外推出頻段邊界產生假數字，已加邊界檢查改為誠實標示無法量測）。**4c 未完成**：需要月月本人用瀏覽器實際打開 `ai_radiance_m1.report.html` 確認版面可讀性，AI 不能代為視覺驗收，Milestone 因此不能標 Done（Rule 5）。|
| M5 | 衰減（T60）驗證轉正 | P1 | 驗證 | Not started |
| M6 | 響度物理語意 | P1 | 樂器物理 | Not started |
| M7 | 容差緊縮 + 文獻對照 | P1 | 驗證 | Not started |
| M8 | 工程收尾（DAW / push / merge） | P0 | — | **In progress（2026-07-11）**：8a 部分完成（pluginval L5+L10 自動化全過，`reports/gate_outputs/pluginval_L{5,10}.txt`；Cubase 人工項待月月）、8b 現況已核實（`master`/`Codex-fix-bug` 分支皆不存在，字面待辦 moot，剩 push 時機裁決）、8c 完成（README 措辭已改，見下方詳述）。 |
| M9 | AI 作曲規範 v2（非諧和聲規則） | P2 | 無障礙/AI | Not started |

建議執行順序：M1 → M3 → M2 → M4 → M8 → M5/M6/M7 → M9。
（M1 與 M3 純工程、不改音色、風險最低；M2 改音色，需要 M1 的廣覆蓋 harness 先就位才能安全做。）

---

## 3. Milestone 詳述

### M1 — 驗證廣度擴大 + CI（P0）

**為什麼**：目前「全 6 引擎 PASS」實際上只有 MIDI 60、69 兩個音 × 6 引擎 = 12 個探針，固定 velocity、單一材質。覆蓋面撐不起「精確」的主張。

**任務**：

- [x] 1a. 為每個引擎定義**有效音域**（物理上合理的範圍，參考 plugin 的 sweet spot：Cim C2–C7 / Chr C3–C6 / FM C1–C7 / Piano A0–C8），寫進 `physics_verify.py` 的 ENGINES 表與文件。證據：`reports/gate_outputs/full_FINAL_gate.txt` 各引擎 `valid range MIDI …` 標頭行。
- [x] 1b. 音域掃描：每個引擎至少 **6 個音**，涵蓋有效音域兩端（例：MIDI 36/48/60/72/84/96 裁剪到有效域）。證據：`reports/gate_outputs/full_FINAL_gate.txt`（6 引擎 × 6 音，`1b note-range scan : PASS`）。
- [x] 1c. 材質掃描：UI 暴露的 9 種材質，各在 MIDI 60 對 cimbalom / tongue_drum / water_gong 跑 f0 + partials 檢查。證據：`reports/gate_outputs/full_FINAL_gate.txt`（9 材質 × 3 引擎全 `[OK]`，`1c material scan : PASS`）。
- [x] 1d. velocity 線性檢查轉正：`--levels` 的「velocity ×2 → +6 dB」從顯示改為判定（modal 引擎 +6.0 ± 1.0 dB，FM 標註豁免）。證據：`reports/gate_outputs/full_FINAL_gate.txt`（`1d velocity judgment : PASS`，cimbalom/tongue_drum/water_gong/water_gong_free/piano 皆 +6.0 dB PASS，fm +5.9 dB EXEMPT）+ 前後對照 `reports/velocity_before_after.md`。
- [x] 1e. 加 `--full` 模式一鍵跑完 1b + 1c + 1d。證據：`reports/gate_outputs/full_FINAL_gate.txt` 開頭 `--full: M1 verification breadth`，結尾 `RESULT: ALL WITHIN TOLERANCE`。
- [x] 1f. GitHub Actions CI：push 時 build CLI + 跑 `physics_verify.py --full`，README 加 badge。證據：2026-07-09 月月授權 push（commit 623e265/3b35d82/7c150d1）後，run **28957524611** `build-and-verify` ✓（9m53s）：3 target build exit 0 + `--full --skip-amps` ALL WITHIN TOLERANCE + verify_score 5 檔 smoke 全過；非阻斷 `--amps` 步驟如預期 FAIL（M2 殘差，不擋綠燈）。**Phase E 更新（unstaged，待月月 push）**：M2 殘差已修正、`--amps` 本地全過，`.github/workflows/physics.yml` 已改為主 GATE 直接跑不加 `--skip-amps` 的 `--full`（涵蓋 2d）並刪除原本的非阻斷 `--amps` 步驟；月月 push `64e2836` 後新版 workflow 於 GitHub 綠燈：run **28960975003** `build-and-verify` ✓（9m15s，完整 `--full` 含 2d + smoke 全過）。
- [x] 1g. 若掃描發現某引擎在某音域超差 → **不准調寬容差**，記錄實測數字，縮小該引擎宣告的有效音域或修模型，由月月裁決。本輪掃描結果：6 引擎 6 音 + 9 材質皆 PASS，未發現需縮小音域或修模型的情形，無待裁決項。

**GATE**：

```powershell
python tools/physics_verify.py --full
# → RESULT: ALL WITHIN TOLERANCE
# 且輸出涵蓋：6 引擎 × ≥6 音 + 9 材質 × 3 引擎 + velocity 判定
```
- CI workflow 在 GitHub 上綠燈一次以上。

**不算完成**：只加了參數沒實際跑全套；某引擎音域縮到只剩中央一個八度卻沒記錄原因；CI 只 build 不跑 harness。

---

### M2 — 激發物理化 + 振幅譜驗證（P0）

**為什麼**：音色一半是振幅譜。目前模態「頻率」是物理的，但「每個模態多大聲」一半是查表啟發式（槌硬度 → LP 截止 partial 數：cotton=3 / felt=8 / wood=20 / metal=60），沒有理論預測值，harness 因此完全沒驗振幅。這是「精確模擬音色」主張最大的缺角。

**任務**：

- [x] 2a. 把槌/激發改成**力脈衝模型**：接觸時間 τ_c 的半正弦（或 Hertz 接觸）力脈衝，其頻譜 |F(ω)| 成為每模態激發振幅的理論預測。槌硬度 → τ_c 映射需有依據（文獻值或推導，註記來源）。證據：`src/physics/HammerImpulse.h`（半正弦脈衝 F(t)=F_max·sin(πt/τ_c) 的傅立葉轉換 |F(ω)| 已用數值積分逐點核對閉式解，誤差 <1e-4；DC 正規化 H(0)=1.0；τ_c 四檔 cotton=6.0ms/felt=2.0ms/wood=0.5ms/metal=0.2ms，來源見檔案內註解：Chaigne & Askenfelt 1994 JASA 95(2) 半正弦脈衝模型 + 接觸時間隨硬度/衝擊力縮短的定性關係；Askenfelt & Jansson (KTH) 量測值「接觸時間低音 ~4ms 到最高音 <1ms、±20% 隨力度變化」直接引用校準 cotton/felt 數值；wood/metal 依 Fletcher & Rossing Ch.12 槌硬度排序原則推導，非逐項抄錄該書表格數值，已在註解中誠實標註）。
- [x] 2b. 模態激發振幅 = |F(2πf_n)| × sin(nπx/L)（弦；梁/板用對應模態形狀函數）。現有 sin 項保留，LP 查表移除或降級為「脈衝頻譜的已文件化近似」。證據：`src/engines/CimbalomEngine.h`（`hammerCutoffPartial[]={3,8,20,60}` 與 `hCutPartial[]` 兩處查表已移除，`StringModel` 的 `sin(nπx/L)` 擊弦位置項未動）、`src/engines/ChromaticEngine.h`（beam/plate 新增 impulse spectrum 相乘，`BeamModel`/`PlateModel` 既有模態形狀函數未動；Custom Harmonics 因非物理域刻意排除）。數值驗證：4 種槌硬度在 cimbalom/tongue_drum/water_gong 三引擎的振幅比值與 `HammerImpulse` 公式預測值逐 partial 核對，誤差 <2%（JSON dump 5 位小數捨入為主要殘差來源）。`physics_verify.py --full` → `RESULT: ALL WITHIN TOLERANCE`（頻率/材質/velocity 判定不受影響，§6 容差未動）；`verify_score.py` 對 AI Radiance m1/m2、Vivaldi Autumn m2（187 events / 4659 partials）三首真實曲目全部 `RESULT: ALL CHECKS PASSED`（無 NaN/Inf、peak < -0.3dBFS、SHA256 determinism 保持）。**尚待**：2c（`--dump-modes` 已自動反映新振幅，但月月尚未書面確認此即滿足「單一真相源」原則）、2d（`--amps` harness 模式未建）、2e（前後對照頻譜差異報告未做，音色確實已改變——見下方 GATE 段落，規則 10 適用，月月需知情）。
- [x] 2c. `--dump-modes` 輸出的 amplitude 欄位變成理論可溯源值（單一真相源原則不變）。證據：`ScoreRenderer::dumpModes()` 與渲染路徑共用同一份 `noteOn()` → `ModalResonator::getModes()` 路徑，amplitude 欄位自動反映 `HammerImpulse::forceSpectrumMagnitude()` 結果（經 4 種槌硬度 × 3 引擎實測核對確認）。無需獨立修改。另修復一個前既存 bug：`dumpModes()` 先前未讀取 score 的 exciter 欄位（預設 Wood），已提取共享 helper `cimbalomExciterFromString()` 修復。
- [x] 2d. harness 加 `--amps` 模式：前 5 個 partial 的相對電平（rel dB）實測 vs 預測，容差 **±3.0 dB**（登記於 §6）。證據：`tools/physics_verify.py` 新增 `dump_modes_partials()`、`judge_amps()`、`scan_amps()`，5 modal 引擎覆蓋，FM 豁免。已整合進 `--full`。**2026-07-07 Phase D 修正**：理論預測法從「渲染前的原始模態振幅」改為 windowed-synthesis 預測（見下方「M2 GATE 證據」段落），殘差從 -15~-40 dB 收斂到 -0.3~-8.0 dB。**2026-07-09 Phase E 修正（GATE 現已全過）**：找到剩餘殘差的根因——`synth_theory_signal()` 把 `decay` 欄位當 1/e 時間常數，但 `ModalResonator::excite()` 定義它是 T60，換成 `exp(-ln(1000)*t/decay)` 後所有引擎前 5 partial 收斂到 ≤±0.22 dB。**GATE 全過**：5 個 modal 引擎（cimbalom / tongue_drum / water_gong / water_gong_free / piano）全部 partial 在 ±3.0 dB 內，證據 `reports/gate_outputs/phase_e_gate_amps.txt` + `reports/gate_outputs/amps_residual_attribution.md`。容差全程未動。
- [x] 2e. 前後對照報告：全部 factory preset + `scores/examples/` 抽 6 首，渲染新舊版本、輸出頻譜差異摘要（音色會變，月月需知情——規則 10）。證據：`reports/m2_before_after_report.md`（6 首 score、5 引擎）。FM 位元完全相同（域外未動）；3 個乾淨單音/雙音案例頻譜差值與 HammerImpulse 公式預測吻合至 ≤0.07 dB。

**GATE**（**全過，2026-07-09**，證據 `reports/gate_outputs/phase_e_gate_amps.txt` / `phase_e_gate_full.txt`）：

```powershell
python tools/physics_verify.py --amps
# → 全 modal 引擎（cimbalom / tongue_drum / water_gong / water_gong_free / piano）
#   前 5 partial rel-dB 誤差 ≤ ±3.0 dB，RESULT: ALL WITHIN TOLERANCE
python tools/physics_verify.py --full   # M1 的 GATE 不得因 M2 破掉 -> RESULT: ALL WITHIN TOLERANCE（含 2d）
```
- 力脈衝公式與 τ_c 來源已寫在 `src/physics/` 註解 + `docs/` 說明。
- 前後對照報告存在且列出每個 preset 的頻譜差異（`reports/m2_before_after_report.md`，2a/2b 階段）。Phase E 的 decay-law 修正只動 `tools/physics_verify.py`（harness 端理論預測），未動任何 `src/` 渲染碼，渲染出的音訊位元不變（SHA256 no-flags render 前後相同），故不需要新的規則 10 前後對照報告。

**M2 GATE 證據（2026-07-07 Phase D）—— windowed-synthesis 理論預測法**：

`--dump-modes` 的理論振幅預測已從「渲染前的原始模態振幅（`ModalResonator::getModes()` 的 `baseAmp`）」改為理論端的 windowed-synthesis 預測，且全程只用文件化的公式/係數計算，**未從渲染音訊反推校準**（無循環論證）：對探測到的事件，取得每個聲部/每根弦的完整模態清單（頻率、振幅、衰減，以及新增的逐 partial `body_mag` 欄位），在與真實渲染相同的取樣率/長度下，對每個模態疊加 `amp*body_mag*exp(-t/decay)*sin(2*pi*freq*t)` 衰減正弦波，重建出一段純理論訊號；`body_mag` 是 `BiquadFilter::responseAt()`（直接讀取 `processSample()` 實際使用的 `cb0/cb1/cb2/ca1/ca2` 係數本身，不是重新推導 RBJ 公式）與 `BodyResonance::totalResponse()` 算出的穩態 `|dry + BodyResonance(dry)|` 傳遞函數量值，經 `CimbalomVoice::getBodyMagnitudeAt()` / `ChromaticVoice::getBodyMagnitudeAt()`（含 `CimbalomVoice::getAllStringModes()` 回傳全部多弦模態，非只有 string 0）逐 partial 寫入 `--dump-modes` 的 `body_mag` 欄位與新增的 `strings` 陣列。此理論訊號再送進與真實渲染完全相同的 windowed-FFT peak-picker（`measure_partials()`），得到 apples-to-apples 的 `pred_dB`。

此方法涵蓋（且僅涵蓋）三個已用文件化公式量化、非從渲染音訊校準回推的機制：**(1) BodyResonance 共鳴體濾波**——兩個共振帶通（120 Hz / 280 Hz）+ 500 Hz 低通對 dry 訊號疊加，在 partial 2 附近造成 destructive interference 近零點；**(2) 多弦 beating**——cimbalom/piano 共用的 `CimbalomVoice`（numStrings=3、5-cent detuning）多弦疊加；**(3) piano 專屬的 exciter/strike-position 理論-渲染參數不一致 bug**——`ScoreRenderer::dumpModes()` 先前未套用 `renderEvent()` 已有的 `strikePosition 0.3→0.125` / `wood_mallet→felt` override，已同步修復。修正後，殘差從舊有的 -15~-40 dB 收斂到 -0.3~-8.0 dB（詳細每 partial 數字見 §2 M2 列）。根因報告額外做了排除性檢查確認沒有遺漏其他已知機制：`ModalResonator::processSample()` 是精確閉式 decaying-sinusoid（無隱藏濾波）；敲擊噪聲的 `ExpDecay` 包絡在 20 ms 量測窗開始前已完全衰減（>-90 dB）；tongue_drum 探針渲染峰值 0.397（無削波飽和）。`HammerImpulse::forceSpectrumMagnitude()` 既有的 `w·τc=π` 可去奇點保護（`src/physics/HammerImpulse.h:119`，L'Hôpital 極限 `π/4`）在本次量測全頻域範圍內未觸發，已排除為殘差來源。tongue_drum partial 2 仍有約 -12.6 dB 的殘差未歸因，需要 C++ 層級的 `--dump-signal-stage` 除錯旗標才能進一步定位（超出本輪唯讀調查範圍）。完整推導與逐步數字見 `reports/gate_outputs/amps_rootcause_analysis.md`；**容差全程未動（±3.0 dB，Rule 2）**。

**Phase E 補充證據（2026-07-09）—— decay-law 指數修正，關閉全部殘差**：

根因：`synth_theory_signal()` 把 `--dump-modes` 的 `decay` 欄位當 1/e 時間常數 τ 衰減（`exp(-t/decay)`），但 `ModalResonator::excite()` 自己的公式與註解明確定義 `decayTime` 是 **T60**（衰減到 -60dB 所需時間）：`decayCoeff = exp(-6.9078f/(decayTime*sampleRate))` 逐取樣套用，等效閉式解是 `amp(t) = amp0 * exp(-ln(1000)*t/decayTime)`，比理論端算的慢了 ln(1000)≈6.9078 倍。改成 `MODAL_DECAY_LN1000 = 6.907755278982137`（讀自 C++ 原始碼字面值 `6.9078f`，非從音訊反推）套用後，殘差全部收斂至 ≤±0.22 dB。差異化渲染隔離實驗（新增 `src/dsp/DiagnosticOverrides.h` + `RenderApp.cpp` 的 `--body-amount` / `--no-exciter-noise` / `--num-strings` 診斷專用旗標，sentinel 預設值＝不覆寫、不在任何正常渲染路徑觸發，SHA256 no-flags render 前後位元相同）逐一排除 BodyResonance、敲擊噪聲、多弦拍頻三個候選機制，確認只有 decay-law 指數修正是必要且充分的關鍵。完整推導、per-partial 數字、隔離實驗表格見 `reports/gate_outputs/amps_residual_attribution.md`。**容差全程未動（±3.0 dB，Rule 2）**——這是理論預測公式的修正，不是判定線放寬；且因為未改動任何 `src/` 渲染碼，渲染音訊位元不變，不觸發規則 10。

**不算完成（歷史記錄，已於 Phase E 全部達成）**：~~振幅預測值是「反過來從渲染結果抄的」（循環論證）~~——decay-law 常數讀自 C++ 原始碼字面值，非從音訊反推；~~τ_c 數值沒有來源註記~~——見 2a 證據；~~只驗 cimbalom 一個引擎~~——5 個 modal 引擎全覆蓋且全過。

**2a/2b 完成後的音色變化告知（規則 10，非正式 2e 報告的暫代揭露）**：

移除 LP 查表、換成力脈衝頻譜後，**音色會變**，且變化方向對每種槌硬度都一致：新模型比舊 LP 查表在高 partial 滾降得更快、更早。以 C4（f0≈261.6 Hz 諧波序列）為例，振幅相對值（1.0=不衰減）：

| n | freq (Hz) | cotton 舊 | cotton 新 | felt 舊 | felt 新 | wood 舊 | wood 新 | metal 舊 | metal 新 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 261.6 | 0.900 | **0.025** | 0.985 | 0.767 | 0.998 | 0.984 | 1.000 | 0.997 |
| 2 | 523.3 | 0.692 | **0.024** | 0.941 | 0.293 | 0.990 | 0.938 | 0.999 | 0.990 |
| 4 | 1046.5 | 0.360 | **0.004** | 0.800 | 0.058 | 0.962 | 0.767 | 0.996 | 0.960 |
| 6 | 1569.8 | 0.200 | **0.001** | 0.640 | 0.024 | 0.917 | 0.533 | 0.990 | 0.911 |
| 10 | 2616.3 | 0.083 | **0.001** | 0.390 | 0.007 | 0.800 | 0.097 | 0.973 | 0.767 |

觀察：cotton/felt（軟槌）新模型明顯更暗、更小聲，連基頻（n=1）都會被衰減（因為軟槌 τ_c=6ms 的頻譜截止 f_cutoff=1/(2τ_c)≈83Hz 遠低於 C4 的 261.6Hz，這是物理上正確的預測——真實軟棉槌打中音域本來就發不出清亮的音，這是舊 LP 查表沒有捕捉到的效應）；metal（硬槌）變化最小，因為金屬槌 τ_c=0.2ms 的頻譜截止極高，在可聽頻域內幾乎不衰減。

這只是單一諧波序列的示意數字，**不是** 2e 要求的正式報告（2e 需要全部 factory preset + 6 首 `scores/examples/` 實際渲染音檔的頻譜差異摘要，尚未做）。全部既有 score（含 AI Radiance、Vivaldi 抄本）已用 `verify_score.py` 驗證過仍能正常渲染（無 NaN/clipping/determinism 問題），但**其實際音色已經改變**，正式的前後對照聆聽/頻譜報告待 2e 完成才能讓月月做最終判斷是否保留此版本。

---

### M3 — 整曲驗證工具 `verify_score.py`（P0）

**為什麼**：harness 只驗單音探針；AI Radiance 那次的全曲檢查（5,083 模態、休止、峰值）是手工做的。AI 作曲流程的最後一步應該是機器蓋章，不是人工檢查清單。這也是「AI 自由創作」能自我把關的前提。

**任務**：

- [x] 3a. 新工具 `tools/verify_score.py <score.json>`，對**任意** score 執行並輸出 JSON 報告：
  - schema 合法、events 依 time 排序、MIDI 0–127、frequency_hz 符合平均律
  - `--dump-modes` 全事件掃描：無空模態集、無 NaN/Inf、頻率 (0, 20k]、衰減常數合法、f0 偏差統計（最大 cents）
  - **休止實測**：`rests` 區間的渲染音訊 RMS 低於門檻（預設 −50 dBFS，考慮前音殘響衰減，見 §6）——這是「休止沒被共鳴吞掉」第一次有機器驗證
  - 峰值 ≤ −0.3 dBFS、無 clipping、無全零輸出
  - **決定性檢查**：渲染兩次 → SHA256 一致
  證據：`reports/gate_outputs/verify_all_corpus.log` 逐檔列出上述全部檢查項的 `[OK]`/`[FAIL]`。
- [x] 3b. exit code：0 = 全過。錯誤訊息可讀（給非工程背景的月月看）。證據：`reports/gate_outputs/verify_all_corpus.log` 每檔皆印 `>>> EXIT_CODE: N`。
- [x] 3c. 對現有資產全量跑一遍：`scores/examples/` 全部、四季 12 樂章、AI Radiance 4 樂章，修掉跑出來的問題或記錄豁免原因。證據：`reports/gate_outputs/verify_all_corpus.log`（73/73 零遺漏，67 PASS / 6 FAIL）+ 豁免分流分析 `reports/m3_corpus_triage.md`；6 個 FAIL 待月月裁決（清單見 `TODO.md`「月月待裁決」區塊），僅兩類根因（moonlight 殘響尾巴 FX-bypass 坐實、5 首 Vivaldi 大樂章 `--dump-modes` 600s 工具逾時），皆非物理容差失敗。
- [x] 3d. 寫進 `AI_PHYSICAL_COMPOSITION_GUIDE` 的驗收清單：新作最後一步 = 跑此工具。證據：`docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` §12 驗收清單新增條目。

**2026-07-07 Phase D 更新（3c 的 6 個 FAIL 處置）**：豁免登記機制已實作於 `tools/verify_score.py`（新增 `scores/verify_exemptions.json` 登記表，僅比對「檔名 + check 名稱前綴」，狹義生效），`moonlight_sonata_complete.score.json` 的 `rests.rms_below_limit` 已登記豁免（reason 引用 FX-bypass 診斷），重跑 exit 0、`-> PASS (with 1 registered exemption(s))`。`--dump-modes` 的 CLI timeout 也已從 600s 提高到 1800s（`tools/verify_score.py:312`）。**但四季 12 樂章尚未在本輪以新 timeout 重新驗證完成**——分派給 Vivaldi 重跑的背景工作在寫本文件時仍卡在「載入豁免清單」、未產出任何一檔的 EXIT 結果（見 `reports/gate_outputs/corpus_phase_d_B_classical_1.log` / `_C_classical_2.log`），因此 1800s 是否真的解決原本 5 首的逾時問題**尚未證實**，不得標記為已解決。`scores/originals/`+`scores/library/`（48 檔）本輪已完整重跑，全數 PASS。詳見 `reports/m3_corpus_triage.md` 的 Phase D 段落。

**GATE**：

```powershell
python tools/verify_score.py scores/originals/ai_radiance/movement1.score.json   # exit 0
python tools/verify_score.py --all   # examples + 四季 + ai_radiance 全綠或有已記錄豁免
```

**不算完成**：只做 schema 檢查沒做渲染側驗證；休止檢查沒實作（這是本 milestone 的核心新能力）；只跑了一首就宣稱全量通過。

---

### M4 — 視覺驗證報告（聾人介面）（P0）

**為什麼**：目前「不靠聽感」的介面是 CLI 文字輸出，plugin 的 scope/spectrum/tuner 是給聽人即時調音用的。聾人作曲者需要**渲染後的視覺證據**。這是把「物理可驗證」從工程師工具變成使用者功能的一步，也是整個企劃無障礙價值的落地。

**任務**：

- [x] 4a. `verify_score.py --html` 產出單檔 HTML 報告：
  - 全曲頻譜圖（spectrogram，時間 × 頻率 × 強度）
  - 每事件「預測 f0 vs 實測 f0」對照圖（cents 偏差著色：綠 ≤5 / 黃 ≤12 / 紅 >12）
  - 響度曲線（RMS over time）+ 休止區間標示（驗證通過打勾）
  - 樂句/呼吸區間視覺化（讀 `phrases` / `rests` 欄位）
  - 頂部總結徽章：PASS / FAIL + 各分項
  證據：新增 `tools/report_html.py`（純函式，不重新判定 PASS/FAIL，只把 `verify_score.py` 已算出的 `Check` 物件與已渲染的音訊畫成圖），`verify_score.py --html` 已從 M3 遺留的 placeholder 接上真正實作。全 6 個區塊（總結徽章／頻譜圖／f0 對照／響度曲線／樂句休止／頁尾）皆已在下方 GATE 輸出的兩份報告中驗證存在。實作過程中發現並修正一個真實測量 bug：f0 對照圖初版對 `ai_radiance_m1` 事件 #56（69.3 Hz 低音 water_gong）算出 +75.43 cents 的假數字——根因是拋物線峰值內插在「搜尋頻段（±3%）邊界」外插了頻段外的鄰近 bin；已在 `measure_event_f0()` 加上邊界檢查（峰值若落在頻段邊界視為「無內部峰值」，誠實標示無法量測而非外推假數字，見 `report_html.py` 內註解），修正後同一事件不再出現於最大偏差前 10 名。
- [x] 4b. 單一 HTML 檔、無外部網路依賴（inline SVG/JS），能用瀏覽器直接開。證據：頻譜圖用純 stdlib（`zlib`+`struct`）手刻 PNG encoder 內嵌為 `data:image/png;base64,...`，無 PIL/matplotlib；已用程式化檢查確認兩份報告的 `src=`/`href=` 屬性中 `http://`/`https://` 出現次數為 0（見下方 GATE 輸出），且 PNG 的 CRC32／IDAT 解壓長度、三個 `<svg>` 區塊皆已驗證為合法格式。
- [ ] 4c. 對 AI Radiance 第一樂章產出範例報告，月月**用眼睛**驗收版面可讀性（視覺驗收，非聽覺，允許）。**尚待**：`ai_radiance_m1.report.html` 已產出（見下方 GATE），但「月月確認報告看得懂、判斷得了作品結構」需要月月本人實際打開瀏覽器查看後才能勾選——AI 不能代為驗收視覺可讀性，Milestone 因此維持 In progress。

**GATE**（**4a/4b 已過，2026-07-11**）：

```powershell
python tools/verify_score.py --html scores/examples/water_gong_clamped.score.json
# → exit 0, scores/examples/water_gong_clamped.report.html (110.8 KB), 含全部 6 區塊
python tools/verify_score.py --html scores/originals/ai_radiance/ai_radiance_m1.score.json
# → exit 0, scores/originals/ai_radiance/ai_radiance_m1.report.html (483–498 KB), 含全部 6 區塊
```
- 兩份報告皆已程式化驗證：`src=`/`href=` 屬性中 0 個 `http://`/`https://`；PNG chunk CRC32 與 IDAT 解壓長度正確；3 個 `<svg>` 區塊皆為合法 XML（`xml.etree.ElementTree` 可解析）。
- 月月確認報告看得懂、判斷得了作品結構（**待辦，見 4c**）。

**不算完成**：報告只有文字表格沒有圖；需要連網載入 CDN；只做了頻譜圖沒做預測對照（對照才是驗證的核心）。

---

### M5 — 衰減（T60）驗證轉正（P1）

**為什麼**：目前 T60 容差 0.2–5.0 倍（約 ±14 dB 的範圍），標註 informational——等於沒有衰減驗證。衰減是敲擊樂器音色的第三根柱子（頻率、振幅之後）。

**任務**：

- [ ] 5a. 量測改進：渲染加長到 5s、基頻帶通更窄、避開 note-off 加速阻尼區、必要時對數斜率分段擬合。
- [ ] 5b. 容差收緊：0.2–5.0 → **0.5–2.0**（第一階段，登記於 §6），全 modal 引擎判定制。
- [ ] 5c. `materials.json` 的阻尼三參數（alpha / beta_air / gamma_radiation）逐一標註來源或量測依據；標不出來的列入「待溯源」清單給月月。

**GATE**：

```powershell
python tools/physics_verify.py --t60
# → 全 modal 引擎 ratio ∈ [0.5, 2.0]，判定制 PASS
```

**不算完成**：只改容差沒改量測方法（會直接 FAIL 或不穩）；材質常數溯源跳過。

---

### M6 — 響度物理語意（P1）

**為什麼**：等 RMS 校準是務實做法但不是物理。聾人判斷「這一音多大聲」需要一條定義好的、可驗證的規則。

**任務**：

- [ ] 6a. 文件化 velocity 映射律：velocity → 激發力 → 振幅（現況：線性，×2 velocity = +6 dB）。寫進 `AI_PHYSICAL_COMPOSITION_GUIDE` 與 schema 註解。
- [ ] 6b. M1-1d 的 +6 dB 判定即為此律的 harness 驗證（共用）。
- [ ] 6c. `verify_score.py` 報告加整曲 LUFS（integrated）與逐樂句 RMS，讓響度成為可讀數字。

**GATE**：velocity 判定綠燈（M1 共用）+ 報告含 LUFS 欄位 + 文件更新。

---

### M7 — 容差緊縮 + 文獻對照（P1）

**為什麼**：f0 ±12 cents 偏寬（人耳可辨約 5 cents；我們的標準不能低於耳朵）。free-edge 板的 Ω 值目前是近似值（Leissa ν≈0.33），TODO 已列待複查。

**任務**：

- [ ] 7a. f0 容差 ±12 → **±5 cents**。若某引擎物理上做不到（如 cimbalom 多弦 beating 的質心偏移），為該引擎登記個別容差 + 物理原因，不得無說明豁免。
- [ ] 7b. `PLATE_FREE_OMEGA` 對照文獻表（Leissa, *Vibration of Plates*, NASA SP-160 或等效來源）：誤差 ≤1% 或更新數值；來源寫進註解。
- [ ] 7c. `PLATE_OMEGA`（clamped）、`BEAM_BETAL` 同樣補來源註記（數值應已正確，補溯源）。

**GATE**：`physics_verify.py --full` 在新容差下全綠；三組常數的來源註記存在。

---

### M8 — 工程收尾（P0，既有欠帳）

- [x] 8a（部分）. pluginval 自動化驗證：pluginval 1.0.4 對 `TsukiSynth.vst3` 分別跑 `--strictness-level 5` 與 `--strictness-level 10`（最高等級），兩次皆 `SUCCESS`、exit code 0，涵蓋 plugin scan、冷/熱開啟、editor 開關、27 組 program 枚舉、跨取樣率(44.1k/48k/96k)×block size(64–1024) 音訊處理、state 存讀、參數 automation、bus layout、（L10 額外）非釋放連續處理、Parameters/Background-thread/Parameter-thread-safety/Fuzz-parameters 測試，log 兩份皆 0 個 warn/error/fail 字樣。證據：`reports/gate_outputs/pluginval_L5.txt`、`reports/gate_outputs/pluginval_L10.txt`。**但這只涵蓋自動化可測的部分**——真正在 Cubase host 裡的**人工**確認（host 掃描辨識到外掛、MIDI in 實際彈奏出聲、GUI 上的 automation lane 手動畫自動化曲線後回放正確、專案存檔關閉重開 state 正確還原）**尚未做**，需要月月在自己的 Cubase 環境操作，AI 無法代為完成，清單見 `TODO.md`。
- [ ] 8b. `Codex-fix-bug` 剩餘 commit push；merge → master 的決定（月月裁決）。**現況核實（2026-07-11，`git branch -a`）**：目前 repo 只有 `main`（+ `remotes/origin/HEAD`、`remotes/origin/main`），**沒有獨立的 `master` 分支存在**，也沒有本地或遠端的 `Codex-fix-bug` 分支——早前提到的 `Codex-fix-bug` 工作已經在某次月月授權的 push 中併入 `main`。故「merge `Codex-fix-bug` → master」這個字面待辦**已經 moot**（目標分支不存在，來源分支也不存在），8b 真正剩下的只是「本輪 Phase F 尚未 push 的變更何時 push」，見 8b 下方 GATE 段落與 `TODO.md`。
- [x] 8c. `README.md` 依驗證域聲明改寫「精確」相關措辭：對外主張改用「物理可驗證（physically verifiable）」，「精確」保留給 GATE 已覆蓋的項目；新增「Physical Verification」章節列出 §0 驗證域表（域內/半域內/域外）+ 逐項引用 §6 容差數字與 GATE 證據路徑；三個引擎標題與 Effect Chain 標題皆補上域內/域外標註。證據：`README.md`（本輪 diff，`git diff README.md`）。

**GATE**：DAW 驗證四項有紀錄（截圖或文字）——**pluginval 自動化涵蓋 3 項（scan-equivalent／automation／state round-trip 的非-DAW 版本），Cubase 內 MIDI in 手動彈奏確認與 host 專屬行為仍待月月人工執行**；README 措辭審過（已完成，見 8c）。

---

### M9 — AI 作曲規範 v2：非諧樂器的和聲與時值規則（P2）

**為什麼**：月月觀察到 AI 自由創作「短暫且不和諧」。這有可分析的理論原因，不需要耳朵就能改善：

1. Tongue drum / water gong 的泛音是**非諧的**（梁 1:2.76:5.40、板 1:1.73:2.33…）。用寫鋼琴音樂的方式堆三和弦，泛音會互相打架——這不是 bug，是物理。非諧樂器的合奏在真實世界（gamelan、鐘樂）有自己的一套音程規則。
2. AI 逐音生成缺乏長程結構，樂句短是通病，`phrases` 骨架先行可以緩解（指南 §11 已有，但沒有和聲規則）。

**任務**：

- [ ] 9a. 為每個引擎計算「理論協和度表」：給定兩音音程，計算泛音碰撞度（如 Sethares 的 dissonance curve 方法——純計算，不用聽）。產出每引擎的建議音程集。
- [ ] 9b. 時值規則：每引擎依 T60 給出最小建議音長與音符密度上限（衰減沒完成前就再擊 → 濁）。
- [ ] 9c. 寫進 `AI_PHYSICAL_COMPOSITION_GUIDE` v2：非諧引擎和聲規則、聲部配器建議（諧波引擎擔任和聲、非諧引擎擔任色彩/節奏）、長程結構模板（AABA、頑固低音等）。
- [ ] 9d. 用 v2 規範讓 AI 重新創作一首，跑 M3/M4 驗證管線全綠，並附協和度分析報告。

**GATE**：協和度表可重現（腳本輸出）；指南 v2 更新；新作通過 `verify_score.py`。

---

## 4. Nice to have（不擋目標，有餘裕才做）

依價值排序：

1. **Plugin ↔ CLI 一致性驗證** — 目前只有 CLI 是純物理路徑；驗 plugin 渲染（macro 中性 + FX 關）與 CLI 輸出的一致性，讓 DAW 使用者也在驗證域內。
2. **音板/共鳴箱耦合**（piano / cimbalom）— 真實感大增，但要先想好「音板模態怎麼驗證」，做不到理論比對就不做（原則：不增加驗證域外的物理裝飾）。
3. **鋼琴進階物理** — 槌氈非線性（velocity → 接觸時間變短 → 更亮，這是 M2 力脈衝模型的自然延伸）、同度弦組（複用 cimbalom 多弦 beating）、延音踏板共鳴。
4. **跨機器可重現性** — 在第二台機器 build 後跑 determinism 比對，位元不一致就定義容差型比對標準。
5. **更多材質** — 每種新材質附文獻來源（規則 4）。
6. **知覺量測視覺化** — sharpness / roughness 等心理聲學指標進 HTML 報告。
7. **MusicXML 轉換器** — 比 MIDI 保留更多譜面資訊（staccato、力度記號直接可讀）。
8. **舊 ROADMAP 的產品項**（世界觀音色庫、preset tag 搜尋、mod matrix lite）— 產品線 B，見 §5。

## 5. 明確不做 / 域外聲明

- **連續激發樂器**（運弓、管樂）：非線性自激振盪，無閉式解、難驗證——研究等級工程量，不做。敲擊/撥彈類（線性模態衰減 + 閉式特徵值 + FFT 可驗）才是本企劃的地盤，這個選擇在物理上是對的。
- **FEM / 流體聲學**：研究域，不做。
- **Wavetable / 多層取樣 / 頻譜重合成 / 內建音序器**：沿用舊 ROADMAP 的 Not Planned。
- **Sample Layer**（舊 v0.3 計畫）：與物理可驗證目標**直接衝突**（取樣沒有理論預測值）。若未來仍要做，比照 FM 標註域外，且優先級排在 M1–M8 全部完成之後。

## 6. 容差登記表

**AI 不得修改本表數值。要改，先給月月實測數字與理由。**

| 項目 | 現值 | 目標值（Milestone） | 依據 |
|---|---|---|---|
| f0 誤差 | ±12 cents | ±5 cents（M7） | 人耳可辨閾約 5 cents，標準不得低於耳朵 |
| Partial 頻率誤差 | 2–4%（依引擎） | 維持，M7 檢討 | FFT 量測窗 ±6% 的解析限制 |
| Partial 振幅誤差 | 無（未驗證） | ±3.0 dB（M2） | 待 M2 實測後檢討 |
| T60 比值 | 0.2–5.0（informational） | 0.5–2.0 判定制（M5） | 量測法改進後收緊 |
| velocity ×2 電平 | 顯示用 | +6.0 ± 1.0 dB 判定制（M1） | 振幅正比力的物理律 |
| 休止區 RMS | 無 | ≤ −50 dBFS（M3，含殘響衰減窗） | 待 M3 實測後檢討 |
| 跨引擎等 RMS | 0.2 dB（已達） | 維持 | 2026-06 校準 |
| 決定性 | SHA256 一致（同機） | 維持；跨機另訂（NTH-4） | — |

## 7. 狀態更新規則

- 完成 GATE → 更新 §2 表狀態 + 在 `DEVLOG.md` 記一筆（含 GATE 輸出摘要）。
- 本文件的任務勾選框只在 GATE 輸出存在時才能打勾。
