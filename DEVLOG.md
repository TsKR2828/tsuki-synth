# TsukiSynth 開發日誌

---

## 2026-07-09 — Phase E：`--amps` 最後根因修復（decay-law 指數），GATE 全過

分支 `main`（HEAD 7c150d1 起），未 commit/push，§6 容差未動，Rule 7（不 commit/push）。

### 機制：theory-side 的 decay-law 指數搞錯了，不是 C++ 渲染 bug
Phase D 把 `--dump-modes` 理論預測法換成 windowed-synthesis 後，殘差從 -15~-40 dB 收斂到 -0.3~-8.0 dB，但 cimbalom/piano p3–p5（-3.0~-4.5 dB）、water_gong p3–p5（-3.9~-8.0 dB）、tongue_drum p2（-12.60 dB）仍超出 ±3.0 dB。逐一差異化渲染隔離（`--body-amount 0` / `--no-exciter-noise` / `--num-strings 1`，這三個是本輪新增的**診斷專用** CLI 旗標，見下段）排除 BodyResonance、敲擊噪聲、多弦拍頻後，唯一能關閉全部殘差的介入是：`tools/physics_verify.py` 的 `synth_theory_signal()` 把 `--dump-modes` 的 `decay` 欄位當 1/e 時間常數 τ 衰減（`exp(-t/decay)`），但 `ModalResonator::excite()` 自己的公式與註解明確定義 `decayTime` 是 **T60**（衰減到 -60dB 所需時間）：`decayCoeff = exp(-6.9078f/(decayTime*sampleRate))` 逐取樣套用，等效閉式解 `amp(t) = amp0*exp(-ln(1000)*t/decayTime)`，比理論端算的慢了 ln(1000)≈6.9078 倍；且不同 partial 的 decayTime 不同，這個比例誤差在「相對基頻 dB」判定下不會抵消。**這是 harness 端（`tools/`）的理論模型 bug，不是 `src/` 渲染碼的 bug**——每個差異化渲染變體都證實 C++ 渲染輸出與其自己文件化的 `decayCoeff` 公式吻合到 ≤0.22 dB。完整推導、per-partial 數字、隔離實驗表格見 `reports/gate_outputs/amps_residual_attribution.md`。

### 修法：一行指數修正 + 唯讀診斷旗標
`tools/physics_verify.py` 新增 `MODAL_DECAY_LN1000 = 6.907755278982137`（讀自 C++ 原始碼字面值 `6.9078f`，非從音訊反推——不違反無循環論證規則），`synth_theory_signal()` 的衰減項從 `exp(-t/decay)` 改成 `exp(-MODAL_DECAY_LN1000*t/decay)`。為了做隔離實驗，新增 `src/dsp/DiagnosticOverrides.h`（三個 sentinel 全域變數）+ `src/cli/RenderApp.cpp` 的 `extractDiagnosticOverrides()`（解析 `--body-amount` / `--no-exciter-noise` / `--num-strings`，從 argv 抽掉後其餘邏輯不變）+ `ChromaticEngine.h`/`CimbalomEngine.h` 三處 `noteOn()`/`setupExciter()` 讀取這些覆寫值。**這些旗標不是渲染契約的一部分**：sentinel 預設「不覆寫」，不接受任何 score JSON 欄位、外掛參數、或 preset 觸發，只有 CLI 明確傳旗標才會生效。

### 音訊路徑未變：SHA256 位元級驗證
用 `git stash`（暫存 3 個 `src/` 修改檔）建出「修正前」CLI，複製一份 exe 出來，`git stash pop` 還原（`git status` 確認 5 個修改檔全部回來），重新編譯出「修正後」CLI。兩者對 `scores/examples/akashic_bell.score.json` 做無旗標渲染，SHA256 完全相同：`7ba03dbc00e559775dcb63e1a47da98f9e0df910f194252a16e7c8bef009c522`。**音訊位元零變化**（`audio_path_changed=false`）——修的只是 harness 的理論預測公式，不是渲染碼。依規則 10，音色不變不需要前後對照報告；corpus（`verify_score.py --all`）上次 73/73 結果依然有效，本輪未重跑。

### GATE 結果：全過
3 個 build target（CLI/Standalone/VST3）重建全部 exit 0。`python tools/physics_verify.py --amps` → 5 個 modal 引擎（cimbalom / tongue_drum / water_gong / water_gong_free / piano）前 5 partial 全部 `PASS`，`RESULT: ALL WITHIN TOLERANCE`（`reports/gate_outputs/phase_e_gate_amps.txt`）。`python tools/physics_verify.py --full` → 1b/1c/1d/2d 全部 `PASS`，`RESULT: ALL WITHIN TOLERANCE`（`reports/gate_outputs/phase_e_gate_full.txt`）。**§6 容差全程未動（±3.0 dB，Rule 2）**——修的是預測公式，不是判定線。

### CI workflow 更新
`.github/workflows/physics.yml` 主 GATE 步驟原本跑 `--full --skip-amps` 並另加一個 `continue-on-error` 的非阻斷 `--amps` 步驟（Phase D 的 CI-scope 決策，見 `TODO.md`）。M2 已過，依 workflow 註解原本的承諾：拿掉 `--skip-amps`，主 GATE 步驟改跑完整 `--full`（涵蓋 1b+1c+1d+2d），刪除非阻斷的 `--amps` 步驟。規則 7 擋住尚未 push，這個新版 workflow 在 GitHub 上實際跑出綠燈一次還沒發生，待月月 push 後確認。

### 文件同步（本輪，Phase E）
`ROADMAP_PHYSICS.md`：M2 列改標 Done + GATE 段落補上 Phase E 根因證據；M1 列/1f checkbox 補充 CI workflow 更新狀態（新版尚待 push 驗證）。`TODO.md`：M2 `--amps` 殘差項移入「已解決」清單，CI 紅燈連動項與其重複項標記解決。

---

## 2026-07-08 — Phase D 收尾：dumpModes O(n²) 真根因修復 + corpus 73/73 全數通過

分支 `Codex-fix-bug`，未 commit/push，§6 容差未動。

### Vivaldi 逾時的真根因：不是檔案太大，是字串拼接 O(n²)
昨日（07-07 條目）記錄的「四季 12 樂章在 1800s timeout 下尚無結果」在重跑時複現：autumn_m1（3111 events）與 autumn_m3（**2582 events，Phase B 用 600s 都沒逾時過**）雙雙撞 1800s。m3 變得比以前更慢這一點戳破了「檔案太大」的假設——真兇是 `ScoreRenderer::dumpModes()` 用 `juce::String out; out << ...` 累加輸出：JUCE String 每次 append 都整段重新配置+複製，總成本 O(輸出大小²)。Phase B 時代 3000-event 檔的 dump 輸出約 7.5 MB，光字串複製就超過 600s（**Phase B 的 5 首逾時從頭到尾都是這個，模態數學本身只要毫秒級**）；Phase D 的 `body_mag`+`strings` 欄位把輸出再放大 ~4 倍 → 時間 ×16，連 2582 events 都活不過 1800s。

修復：`juce::MemoryOutputStream out (1 << 20)` 攤銷 O(1) append，結尾 `out.toString()`。輸出位元組內容不變（同樣的文字操作序列），只換累加容器。實測：**summer_m3（5158 events，最大檔）dump-modes 從 >1800s 逾時 → 7.2 秒（輸出 55.3 MB）**。

### Corpus 73/73 重驗完成：72 乾淨 PASS + 1 登記豁免、0 FAIL
- examples 13/13（moonlight 走 `rests.rms` 登記豁免，`-> PASS (with 1 registered exemption(s))`）
- classical 12/12（四季全過，含 Phase B 起連續逾時的 autumn_m1/spring_m1/summer_m1/summer_m3/winter_m1）
- originals + library 48/48
逐檔證據：`reports/gate_outputs/corpus_phase_d_{A_examples,D_originals_library,autumn,spring,summer,winter}.log`。嚴格單次 `--all` GATE 另行執行歸檔（`reports/gate_outputs/verify_all_corpus_phase_d.log`）。

### 規則 6 重驗（動了 `src/score/`）
三個 build target 全部重建 exit 0；`physics_verify.py --full` → 1b/1c/1d 全 PASS、僅 2d 振幅判定維持既有 FAIL（`reports/gate_outputs/phase_d_gate_full_v2.txt`）——dumpModes 效能修復零回歸。

### 教訓
Phase B 把 5 首 Vivaldi 逾時登記為「大檔案已知限制」並一度討論豁免——差點把一個可修的工具 bug 當成物理極限歸檔。**逾時類 FAIL 在歸類為「限制」前，必須先做效能歸因（profiling / 複雜度分析）。**

### 新浮現的裁決連動（詳見 `TODO.md`）
CI workflow 跑 `--full`，而 `--full` 現含 2d 判定：**只要 M2 `--amps` 殘差未解，push 後 CI 必紅**。M1「CI 綠燈一次」的 GATE 與 M2 殘差因此耦合，需月月拍板處理順序。

---

## 2026-07-07 — Phase D：`--amps` 根因攻堅 + 理論預測法修正 + 豁免機制 + corpus 部分重跑

依 `ROADMAP_PHYSICS.md` §7/§8 規則同步文件。分支 `Codex-fix-bug`，本輪全程未 commit/push，改動留 unstaged；`ROADMAP_PHYSICS.md` §6 容差登記表未動任何數值。

### 根因攻堅：`--amps` 為何全 5 引擎 partial≥2 低 10-40 dB
唯讀調查（`reports/gate_outputs/amps_rootcause_analysis.md`）鎖定結構性 bug：`ScoreRenderer::dumpModes()` 讀 `ModalResonator::getModes()` 回傳的原始模態振幅（`baseAmp`）當理論值，但真實渲染是 `modal output + BodyResonance 濾波後的同一訊號疊加` —— `BodyResonance`（兩個共振帶通 120 Hz/280 Hz + 500 Hz 低通，`amount` 恆為 0.5）在 partial 2 附近（500–700 Hz）與 dry 訊號幾乎反相疊加造成 destructive interference 近零點，這是最大單一貢獻源。字串家族引擎（cimbalom/piano，共用 `CimbalomVoice`）另有多弦 beating（numStrings=3、5-cent detuning）也未被 `--dump-modes` 模擬。piano 額外查出一個真 bug：`dumpModes()` 的 piano 分支沒有套用 `renderEvent()` 已有的 `strikePosition 0.3→0.125` / `wood_mallet→felt` override，理論與實際渲染激發參數不同。

### 修法：windowed-synthesis 理論預測（非循環論證）
`BiquadFilter.h` 新增 `responseAt()`（直接讀 `processSample()` 實際使用的係數，非重新推導 RBJ 公式），`BodyResonance::totalResponse()` 用它算出穩態 `|dry+BodyResonance(dry)|` 傳遞函數量值，經 `CimbalomVoice`/`ChromaticVoice` 的 `getBodyMagnitudeAt()`（含 `getAllStringModes()` 回傳全部多弦模態）寫入 `--dump-modes` 新增的逐 partial `body_mag` 欄位與 `strings` 陣列。`tools/physics_verify.py` 新增 `synth_theory_signal()`：對每個模態疊加 `amp*body_mag*exp(-t/decay)*sin(2*pi*freq*t)` 衰減正弦波重建純理論訊號，送進與真實渲染完全相同的 `measure_partials()` windowed-FFT，得到 apples-to-apples 的 `pred_dB`。`dumpModes()` 的 piano 分支同步補上 strikePosition/exciter override 修復。詳細方法與涵蓋範圍見 `ROADMAP_PHYSICS.md` M2 GATE 段落的證據段落。

附帶確認：`src/physics/HammerImpulse.h` 既有的 `w·τc=π` 可去奇點保護（`forceSpectrumMagnitude()`，L'Hôpital 極限 `π/4`，見檔案 119 行）在本次全頻域量測範圍內未觸發，排除為殘差來源之一。

### GATE 結果：仍未過，但殘差大幅收斂
`python tools/physics_verify.py --amps` / `--full`（證據 `reports/gate_outputs/phase_d_gate_amps.txt` / `phase_d_gate_full.txt`）：

| 引擎 | p2 | p3 | p4 | p5 | 結論 |
|---|---|---|---|---|---|
| cimbalom | -0.82 PASS | -3.01 FAIL | -4.52 FAIL | -4.19 FAIL | FAIL |
| tongue_drum | -12.60 FAIL | 過弱不判定 | 過弱不判定 | 過弱不判定 | FAIL |
| water_gong | -1.42 PASS | -3.86 FAIL | -5.00 FAIL | -7.96 FAIL | FAIL |
| water_gong_free | -0.31 PASS | -0.57 PASS | -1.53 PASS | -1.53 PASS | **PASS** |
| piano | -0.82 PASS | -3.01 FAIL | -4.52 FAIL | -4.18 FAIL | FAIL |

5 引擎中僅 water_gong_free 全通過 ±3.0 dB 容差（**容差全程未動**）。較修正前的 -15~-40 dB 已收斂到 -0.3~-8.0 dB，且此收斂幅度與唯讀調查用文件化公式手算的重建結果幾乎一致（例：cimbalom p2/p3/p4/p5 重建預測 -0.69/-2.95/-4.46/-4.14 dB vs 修正後實測 -0.82/-3.01/-4.52/-4.19 dB），確認修正正確實作了已歸因的機制。`--full` 的 M1 子 GATE（1b 音域掃描 / 1c 材質掃描 / 1d velocity 判定）不受影響仍全綠。tongue_drum partial 2 仍有約 -12.6 dB 未歸因的殘差，需要 C++ 層級 `--dump-signal-stage` 除錯旗標才能進一步定位（唯讀調查範圍之外）。M2 標記維持 **In progress**。

### 豁免登記機制：`verify_score.py` + `scores/verify_exemptions.json`
新增窄範圍豁免機制（`tools/verify_score.py`；`tools/physics_verify.py` 完全未動）：`scores/verify_exemptions.json` 登記單筆記錄——`moonlight_sonata_complete.score.json` 的 `rests.rms` check family（比對 `rests.rms_below_limit` 前綴），理由引用 FX-bypass 診斷（-120.0 dBFS dry vs -43.1 dBFS 帶 FX），2026-07-07 月月透過 Fable 批准。比對邏輯狹義（檔名 exact + check 名稱前綴），豁免只重分類不隱藏原始失敗訊息（`Check.exempt_reason` 保留 `ok=False` 與原始 message），報告印出 `[EXEMPT]` 行與 `-> PASS (with N registered exemption(s))`，不會悄悄併入單純 PASS。驗證：`water_gong_clamped.score.json`（無登記豁免的檔案）機制不生效、`moonlight_sonata_complete.score.json` 重跑 exit 0、`rests.rms_below_limit` 標 `[EXEMPT]`、其餘檢查項獨立正常 PASS。

### Corpus 重跑：僅部分完成，不宣稱全綠
Phase D 對 73 檔全曲庫分 4 個 chunk 重跑（examples 13 / classical 前半 6 / classical 後半 6 / originals+library 48）。**寫本文件時**：originals+library 48/48 完成、全 PASS；examples 完成 11/13（含 moonlight 豁免通過），2 檔大型曲目（yangqin 系列）仍在跑；**classical 兩個 chunk（四季 12 樂章，原本 5 首 600s 逾時 FAIL 的對象）尚未有任何一檔在新 1800s timeout 下產出 EXIT 結果**——分派的背景工作卡在「載入豁免清單」訊息之後，尚無單檔完成。因此 1800s timeout 是否真的解決 Vivaldi 逾時問題**尚未證實**，`m3_corpus_triage.md` 已補上 Phase D 段落誠實記錄此狀態，不覆蓋 Phase B 的 73/73 完整基準（67 PASS / 6 FAIL）。

### 待月月裁決 / 待完成（本輪不擅自處理，見 `TODO.md`）
1. M2 `--amps` 殘差是否接受現況（4/5 引擎 -3~-8 dB 未過），或繼續投入 C++ `--dump-signal-stage` 除錯定位 tongue_drum 剩餘 -12.6 dB。
2. HammerImpulse 力脈衝模型音色改變是否保留——`reports/m2_before_after_report.md` 已存在，供正式決策。
3. Vivaldi 12 樂章的 1800s timeout 重跑尚未完成，需要人力/時間繼續跑完才能確認是否解決原本 5 首逾時問題。
4. CI GitHub 綠燈仍需 push（鐵則 7 擋住）。

### 文件同步（本輪，Phase D）
- `ROADMAP_PHYSICS.md`：§2 M2/M3 狀態改寫為 In progress（附精確失敗數字，不得樂觀措辭）；M2 GATE 段落附上 windowed-synthesis 證據段落；M3 3c 附 Phase D 更新註記。
- `TODO.md`：移除已解決項目（moonlight 豁免、Vivaldi timeout 已提高、piano 1.4 dB 已接受），新增 Phase D 待裁決/待完成清單。
- `reports/m3_corpus_triage.md`：附上 Phase D 段落，記錄部分重跑結果，不覆蓋 Phase B 基準。
- `docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md`：§12.1 補上豁免登記機制存在的一句話說明。

---

## 2026-07-05 — Phase B：M1 GATE 重跑轉全綠 + M3 全曲庫首次跑完 + 文件同步

依 `ROADMAP_PHYSICS.md` §7/§8 規則，M1/M3 兩個 Milestone 的 GATE 產出後，把 §2 狀態欄、任務勾選框、`DEVLOG.md`、`TODO.md`、AI 作曲指南同步更新。分支 `Codex-fix-bug`，本輪全程未 commit/push，改動留 unstaged；未動 §6 容差登記表任何數值。

### M1：velocity 線性化 bug 修復 + GATE 重跑全綠
- 根因：`src/dsp/BodyResonance.h` 的 `envLevel` envelope-follower 與已經正比於 velocity 的原始樣本相乘，疊加出 velocity² 項，混進 cimbalom / tongue_drum / water_gong / piano 的音量（`water_gong_free` 因模態較弱恰好壓在 ±1.0 dB 窗內躲過）。修法：拿掉 envelope-follower，只留線性 resonant bandpass（被動共鳴體在小訊號域本為線性系統，F=ma）；`CimbalomEngine.h` / `ChromaticEngine.h` 的固定增益常數依新的等 RMS 基準重新校準。
- `python tools/physics_verify.py --full` 重跑：`reports/gate_outputs/full_FINAL_gate.txt` → **RESULT: ALL WITHIN TOLERANCE**。涵蓋 6 引擎 × 6 音（1b）+ 9 材質 × 3 modal 引擎（1c）+ 全引擎 velocity 判定（1d：cimbalom/tongue_drum/water_gong/water_gong_free/piano 皆 +6.0 dB PASS，fm +5.9 dB 標 EXEMPT）。
- 前後對照報告 `reports/velocity_before_after.md`（規則 10 要求）：修復前 cimbalom/tongue_drum/water_gong/piano 的 velocity ×2 皆為 +7.7~+9.5 dB FAIL，修復後全數收斂到 +6.0 dB PASS；獨立第二組驗證點（vel 0.2→0.4 / 0.4→0.8 / 0.3→0.6）證實五個 modal 引擎全部穩定在 +6.02 dB（理論值 20·log10(2)=6.0206 dB），非單點巧合。誠實揭露：cimbalom 與 piano 共用同一個 `CimbalomVoice` 增益常數，因 peak 安全（`PEAK_LIMIT_DBFS -0.3`）優先於精確 RMS re-anchor，piano 的 RMS 因此偏離理想值約 1.4 dB——已在報告中寫明，非隱藏妥協。
- 1f（CI GitHub 綠燈）：`.github/workflows/physics.yml` 已建立，但「push 觸發至少一次綠燈」被鐵則 7（不 commit/push）擋住，剩這一步待月月自行決定何時 push。M1 標 **In progress**。

### M3：`verify_score.py` 對全曲庫首次跑完，73/73 零遺漏
- 涵蓋 `scores/examples/` 全部、`scores/classical/vivaldi_four_seasons/`（四季 12 樂章）、`scores/originals/ai_radiance/`、`scores/library/`（遞迴），共 73 個 `.score.json`（`scores/tests/` 6 檔為工具自我測試用途不計入）。結果：**67 PASS / 6 FAIL**，log 存 `reports/gate_outputs/verify_all_corpus.log`，FAIL 分流分析見 `reports/m3_corpus_triage.md`。
- 6 個 FAIL 只有兩類根因，皆非物理容差失敗：
  1. `moonlight_sonata_complete.score.json` 的 `rests.rms_below_limit`：12/14 個休止區間量到 −43.1 dBFS（門檻 −50.0 dBFS）。FX-bypass 對照（同視窗關掉全部 FX 重渲染）量到 −120.0 dBFS，坐實乾聲道本身乾淨，超標完全是 reverb/delay 的 wet 尾巴造成。
  2. 5 首大型 Vivaldi 樂章（autumn/spring/summer/winter 各自的 m1 + summer m3，event 數皆 ≥3111，最多 5158）的 `modes.dump_modes_ran`：`--dump-modes` 在 `verify_score.py::run_cli` 寫死的 600s 逾時內未跑完；同曲庫 event 數 ≤2696 的樂章全數通過，分界線與 600s 上限吻合，判定為工具逾時而非模型缺陷。這 5 首的其餘全部檢查項（schema、events 排序、MIDI range、frequency_hz 平均律、render、rest、peak、無連續削波、determinism SHA256）皆 PASS。用無限時手動重跑已確認可跑完、非 crash/hang。
- 容差常數逐一稽核：`tools/verify_score.py` / `tools/physics_verify.py` 的 `F0_TOL_CENTS` / `MODE_F0_TOL_CENTS` / `REST_RMS_LIMIT_DBFS` / `REST_DECAY_ALLOWANCE_S` / `PEAK_LIMIT_DBFS` / `VELOCITY_DB_TARGET` / `VELOCITY_DB_TOL` / `T60_RATIO_TOLERANCE` 全部維持原值，未動。
- M3 標 **In progress（豁免清單待批）**：3a–3d 全部完成，剩 6 個 FAIL 的處置方式（登記豁免 vs 修 score/調整工具設定）待月月裁決，見下方待裁決清單。

### 三個 build target 重建 + C++ 回歸測試
- `cmake --build build --config Release --target TsukiSynthCLI`（以及 Standalone / VST3）三者皆 exit 0，log 存 `reports/gate_outputs/rebuild_all_FINAL.txt`。
- `tests/audit_repro.cpp` 回歸測試 20/20 PASS（見 `reports/gate_outputs/audit_cpp_FINAL.txt`），確認 velocity 修復未引入 regression。

### 待月月裁決（本輪不擅自處理，見 `TODO.md`「月月待裁決」區塊）
1. CI GitHub 綠燈需要 push，被鐵則 7 擋住——本地 GATE 已全綠，push 時機由月月決定。
2. moonlight_sonata_complete 的休止超標：縮短 `global.effects` 的 reverb decay/wet 或 delay feedback，或登記為 FX 藝術意圖豁免 rest 檢查。
3. 5 首 Vivaldi 大樂章 `--dump-modes` 600s 逾時：提高 `verify_score.py::run_cli` 的 timeout，或登記為大型曲目已知限制、改抽樣驗證。
4. cimbalom/piano 共用增益常數導致 piano RMS 偏離理想值約 1.4 dB，是否接受此妥協。

### 文件同步（本輪，Phase B）
- `ROADMAP_PHYSICS.md`：§2 M1/M3 狀態改為 In progress（附原因）；§3 M1（1a–1e）、M3（3a–3d）任務勾選框打勾並附證據檔路徑。
- `TODO.md`：CI 條目更新（`--full` blocker 已解除，只剩 push）；新增「月月待裁決」區塊。
- `docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md`：§12 驗收清單加入「新作最後一步跑 `verify_score.py`，exit 0 才算完成」規則。

---

## 2026-06-17 — Plugin UI 完善：Piano 分頁 + 雙語 Tooltip + 修正

本輪完成三項 TODO 待開發事項 + 兩項 bug 修正，分支 `Codex-fix-bug`。

### Piano 第 4 引擎分頁
- 確認 JUCE 8 APVTS 存 **denormalized** 值（讀 `juce_AudioProcessorValueTreeState.cpp` 源碼：`flushToTree` 寫 `unnormalisedValue`）→ 安全追加 "Piano" 在 index 3。
- `PluginProcessor.cpp`：engine 選項 3→4；processBlock/allNotesOff 路由 eng==3 到 cimbalomSynth；state save/load 加 `engine_index` / `chr_sub_engine_index` 明確 int 備援。
- `PluginEditor.h/cpp`：`tabPiano` 按鈕、`updateEngine` eng==3、`resized()` 四等分 tab、Piano 共用 Cimbalom 控件。
- `Presets.h`：兩個物理鋼琴 preset 移到 engine=3。
- `TsukiLookAndFeel.h`：`Clr::piano (0xff8ba0c4)` 鋼藍色。

### 水鑼預設改為 free-edge（物理正確）
- 水鑼是吊掛的板→自由邊。`ChromaticEngine.h` + `ScoreParser.h` `plateFreeEdge` 預設 `true`。
- `water_gong_clamped.score.json` 加明確 `"plate_free_edge": false`。
- `physics_verify.py` water_gong 測試加明確 `"plate_free_edge": False`。

### 雙語 Tooltip（小白框）
- `UiLocale::tooltip()` → 回傳 `"ENGLISH  /  中文"` 格式。
- `TsukiLookAndFeel.h`：`drawTooltip` 覆寫（暖白圓角框 `#f5f0e8`、深色文字 `#1a1a2e`、CJK 字型 14.4pt）+ `getTooltipBounds`（自動定位、最寬 400px）。
- `PluginEditor.h`：`juce::TooltipWindow tooltipWindow { this, 350 }`（350ms 延遲）。
- `PluginEditor.cpp`：`setupKnob` / `setupCombo` 加 `setTooltip`；tab 按鈕 + preset 按鈕加 `setTooltip`；`refreshLocalizedText` 切語言時更新所有 tooltip。

### Bug 修正
- **標題列 Piano 字幕**：eng==3 掉入 "FM PIANO" → 修正為 "PIANO ENGINE | PHYSICAL MODELING STRING"。
- **參數計數**：eng==3 顯示 7 → 修正為 6（Piano 共用 Cimbalom 6 控件）。

### 文件衛生
- `DEV-LOG.md`（英文舊日誌）內容併入本檔 `DEVLOG.md`，刪除舊檔。
- TODO.md / ROADMAP.md / CONTEXT.md 全部更新至 2026-06-17 狀態。

---

## 2026-06-16 — 物理精確化大改 + 驗證閉環（企劃目標轉向）

**企劃目標確立：聾人 + AI 不靠聽感、靠物理理論精確模擬聲音。** 整段工作圍繞此目標三支柱：**可重現性、物理可驗證性、樂器物理正確性**。分支 `Codex-fix-bug`，本輪疊在 Codex `b5a370d` 上的 commit（已 push）：

### 起點：通盤審查 + Codex 平行修復
- 全 `src/` 審查找出 8 bug（增益不一致 / glide block-size 依賴 / FM 相位精度 / buildCustomModes break / 尾音 strand / MIDI 未夾範圍…），交付 `tests/audit_repro.cpp`（零依賴自我驗證，23 checks）。
- 月月把審查交給 Codex 平行實作 → `b5a370d` + PR #4（我的 audit 修復 + dynamic tail length + 線性 release + 牆面反射物理 + FLAC + API deprecation 修正）。本輪逐行覆核：高品質無 regression。

### `13a98cb` 決定性化（落差 A）+ cimbalom 釘音 + 等 RMS
- **Determinism**：`NoiseGen` 原用 `random_device` → 同 score 每次不同。改決定性種子 + `setSeed()`，各引擎 `midiNote^velocity` 每音重設。**同 score 兩次渲染 SHA256：DIFFERENT → IDENTICAL**。
- **Cimbalom 釘音**：弦剛性 actual f1=target·√(1+B)（A4 +11c）→ 除掉，f0 釘 MIDI（保比例+多弦失諧）。A4 +11.2c→+0.1c。
- **等 RMS 校準**：魔術增益 0.15/0.2/1.0 → 等 RMS（Cim 0.070 / FM 0.100 / Chromatic 每-sub-engine outputGain）。跨引擎 RMS 差 8dB→0.2dB。

### 物理驗證閉環（落差 D）`cdb244a`/`e04f24f`/`3cfcb7c`/`1cd2352`
- `tools/physics_verify.py`：render→FFT→比對物理預測→報 f0 cents + 泛音 %。三模式：預設 partials（功率質心測 f0，對多弦 beating 穩健）、`--levels`（電平）、`--t60`（衰減，用 --dump-modes ground truth）。
- CLI `--dump-modes <score.json>`：印每事件 voiced/MIDI-tuned 模態 JSON（單一真相源）。

### 樂器物理升級 `a733419`/`26e8d74`/`9541d9c`/`b22e394`
- **Q1 水鑼→真 clamped Kirchhoff 板**：膜 Bessel 零點近似 → 真板特徵值 Ω=λ²(Leissa)，f∝Ω。泛音 1:2.54:4.56(膜)→1:2.08:3.41:3.89:5.00(板)。**水鑼音色會變**。
- **Q2 物理 piano 引擎**：score/CLI `"piano"` = StringModel 敲剛性鋼弦 + 鋼琴校準(felt/strike 1/8)；stiff-string stretch=鋼琴拉伸調音。FM Piano 保留為標註非物理合成。
- **plugin 物理鋼琴 presets**：Cimbalom 的 "Grand Piano / Bright Upright (Physical)"（零結構風險，保舊存檔相容）。
- **free-edge 鑼選項**：`plate_free_edge:true` 切自由邊(吊掛真鑼)，預設仍 clamped；A/B 範例 score 已附。
- **docs**（`ece1f9a`）：校正物理標示（水鑼=Bessel/膜近似→現真板、FM=合成非物理、CLI 不套 macro）。

### 驗收
- 全 6 引擎 harness（cimbalom/tongue_drum/water_gong/water_gong_free/fm/piano）**ALL WITHIN TOLERANCE**；CLI + Standalone build exit 0。

### 延後（需月月決策）
- **plugin 第 4 引擎 Piano 分頁**：改 APVTS engine 3→4 有舊 DAW 存檔向後相容風險（正規化值映射）→ 需先確認 APVTS 存 denormalized 才安全 append。物理鋼琴已用 preset + CLI 雙路徑交付。
- free-edge Ω 精確值複查、進階 piano（槌非線性/音板/damper）、plugin 內 FM↔modal 響度由耳朵再平衡。

### 文件衛生
- DEVLOG.md（本檔，中文）與 DEV-LOG.md（英文）並存 → 建議擇一收斂。

---

## 2026-05-31 — Tuner 結構修正

**NSDF Peak Selection 修正** (`src/analyzer/TunerView.h`)：
- NSDF 改為從 lag 2 開始計算，偵測 zero-lag lobe 邊界
- 找到 NSDF 首次 ≤ 0 的交叉點 → searchStart = max(minLag, zeroLagEnd)
- peak 搜尋完全跳過 zero-lag positive lobe，消除假基頻選取
- 移除 octave-down correction：乾淨週期訊號在 2x lag 有幾乎同強 peak，會無條件把頻率砍半

**低頻範圍擴展**：
- `maxLag` 從 `sampleRate/50`（~50 Hz 下限）改為 `sampleRate/20`（~20 Hz）
- 分析量從 `analysisSize/2` 改為 `numSamples * 3/4`
- pullBuffer 4096 → 8192（應對 96k sample rate 每 tick ~4800 samples）
- 44.1k 可測到 ~27 Hz、96k 可測到 ~31 Hz，涵蓋 C1 (32.7 Hz)

**Dry Signal 路由** (`PluginProcessor.h/cpp`, `AnalyzerPanel.h`)：
- 新增 `AudioFIFO analyzerDryFifo { 8192 }` — effectChain 之前推入 mono mix
- AnalyzerPanel 改雙 FIFO 建構：scope/spectrum 用 post-FX，tuner 用 dry
- Tuner 不受 delay/reverb 尾音和 output gain 影響

**Sample Rate 同步** (`PluginEditor.cpp`)：
- Editor timerCallback 每 tick 呼叫 `analyzerPanel.setSampleRate(proc.getSampleRate())`
- Host 切換 44.1k → 48k → 96k 時 tuner/spectrum 自動追蹤

---

## 2026-05-30 — Body Resonance + Preset 分層 + Engine-filtered Preset

**Body Resonance Layer** (`src/dsp/BodyResonance.h` — 新檔)：
- 程序式低頻共鳴：2 個 resonant bandpass (~120 Hz Q=1.8, ~280 Hz Q=1.4)
- LP smoother 500 Hz 壓制 harshness + envelope follower (~5ms attack, ~80ms release)
- `setAmount(float)` 控制混合量（0=off, 1=max），由 `macro_body` APVTS 驅動
- Cimbalom / Chromatic 引擎在 startNote 中初始化，renderNextBlock 中加算

**Raw / Body Preset 分層** (`src/Presets.h`)：
- 既有 12 個 Cimbalom/Chromatic preset 全部加上 `macro_body = 0.0f`（Raw）
- 新增 4 個 Body-enhanced preset：
  - Steel Dulcimer Body (0.75)、Copper Warm Body (0.80)
  - Crystal Tongue Body (0.70)、Bronze Gong Body (0.85)
- 合計 25 個 factory preset（原 21 + 4 Body）

**Engine-filtered Preset List** (`PluginEditor.cpp`)：
- `getPresetEngine()` helper 依 preset params 查 engine 值
- `rebuildPresetCombo()` 只顯示目前引擎 tab 對應的 factory preset
- `presetIdToIndex` vector 做 combo ID → 真實 preset index 對照
- User preset 在所有引擎 view 都顯示（分隔線後方）
- 切換引擎 tab 自動重建 preset list

---

## 2026-05-30 — Tuner View 實作 + 修正

**TunerView 實作** (`src/analyzer/TunerView.h` — 新檔)：
- McLeod NSDF 音高偵測 + parabolic interpolation
- 顯示：音名（大字）+ 頻率 Hz + cent offset（±50¢ 刻度尺）
- AnalyzerPanel 加入 TUNER tab（SCOPE / SPECTRUM / TUNER 三切換）
- 中英文 UI 標籤（「調音器」/「TUNER」）

**初版修正**：
- 八度高 bug（C4→C5）：threshold 0.7→0.93、globalMax 0.3→0.5、RMS 0.005→0.02
- 結尾 B7 bug：RMS 門檻提高至 0.02，低能量訊號直接判定 No signal

---

## 2026-05-30 — FM Piano P0-P2 完成

**P0：最優先修正** (commit `7769f95`)：
- 統一 APVTS default 與 FMParams default
- 補 `score.schema.json` FM 參數
- 補 Vibraphone / Brass factory preset（20 個 → 6 Cim + 6 Chr + 8 FM）
- `fm_brightness` UI 語意改名 "TONE DECAY" / "音色衰減"

**P1：讓 FM Piano 像樂器** (commit `5b024a3`)：
- velocity-to-index 曲線（velIndexScale 0.45~1.25）
- 分開 attackIndex / bodyIndex（per-type atkScales[] + bdyScales[]）
- 依 sound type 切換 body resonance（per-type bodyF1/F2 + bodyD1/D2）

**P2：E.Piano 3-stack 補強** (unstaged)：
- 3 並行 FM 運算子：Body (1:1) + Tine/Bell (14:1) + Shimmer (3:1, +4 cents)
- 輸出 = 60% stacks + 40% original
- 新 "Layered E.Piano" preset + 中文翻譯「層疊電鋼琴」

---

## 2026-05-15 — v0.2.0：Codex Audit + DAW 驗證 + i18n

**Codex 代碼審查 8/8 修正** (commit `0769e5a`)：
- 4× P1（Critical）：score pipeline 修正、engine switch tail-off 修正
- 4× P2（Robustness）：WavWriter atomic write、ScoreParser guard、SafePointer

**DAW 驗證**：VST3 在 Cubase 載入測試通過

**國際化** (`src/UiLocale.h`)：
- 英文 / 繁體中文雙語 UI（標籤、ComboBox items、preset 名稱、按鈕、對話框）
- LanguageToggle 按鈕即時切換
- APVTS parameter ID 完全不受語系影響

**MIDI 鍵盤 Range Indicator**：
- 各引擎 sweet spot 色帶（Cim C2-C7 / Chr C3-C6 / FM C1-C7）

**Standalone 錄音**：
- WAV 錄音功能（REC / STOP 按鈕，存到 Documents/TsukiSynth/Recordings）

---

## 2026-05-08 — Phase 8 完成：出廠預設 + 收尾

**Factory Presets（12 組出廠音色）：**

| # | 名稱 | 引擎 | 特色 |
|---|------|------|------|
| 0 | Steel Hammered Dulcimer | Cimbalom | 經典揚琴音色（Steel + Wood hammer） |
| 1 | Copper Warm Strings | Cimbalom | 溫暖厚實（Copper + Felt hammer） |
| 2 | Glass Wind Chimes | Cimbalom | 風鈴效果（Glass + Metal + 高失諧） |
| 3 | Muted Felt Piano | Cimbalom | 悶棉音色（Cotton hammer + 高擊打位置） |
| 4 | Crystal Tongue Drum | Chromatic | 空靈鼓（Aluminum + Tongue Drum） |
| 5 | Bronze Water Gong | Chromatic | 水鑼（Bronze + pitch glide 0.6） |
| 6 | Wooden Kalimba | Chromatic | 拇指琴（Spruce + Tongue Drum） |
| 7 | Ethereal Steel Bells | Chromatic | 空靈鐘聲（Custom harmonics + Delay） |
| 8 | Acoustic Piano | FM Piano | FM 鋼琴（ratio=1, index=5, bright=0.7） |
| 9 | Electric Rhodes | FM Piano | Rhodes 電鋼琴（ratio=1 + delay） |
| 10 | DX7 Crystal Bell | FM Piano | DX7 水晶鈴（ratio=7, index=8） |
| 11 | Church Organ | FM Piano | 管風琴（ratio=1, feedback=0.5） |

**Preset 系統：**
- `src/Presets.h` — 靜態預設陣列，raw parameter values
- PluginProcessor 實作 `getNumPrograms/setCurrentProgram/getProgramName`
- 使用 `param->convertTo0to1(raw)` + `setValueNotifyingHost()` 正確轉換參數值
- DAW preset browser 相容（VST3 program change）
- PluginEditor 頂部 Preset ComboBox（與 Engine selector 並排）

**目前插件總覽：**
- 3 個合成引擎（Cimbalom / Chromatic / FM Piano）
- 28 個可自動化 APVTS 參數
- 7 個效果參數（Reverb / Delay / Compressor）
- 12 個出廠預設
- VST3 + Standalone 雙格式輸出

---

## 2026-05-08 — Phase 6 完成：效果鏈

**新增效果模組（`src/effects/`）：**
- `SimpleReverb.h` — Freeverb-style Schroeder reverb
  - 8 parallel comb filters with LP damping in feedback loop
  - 4 serial allpass filters for diffusion
  - Stereo spread: R channel delay offset +23 samples
  - Parameters: room size, damping, wet/dry mix
- `StereoDelay.h` — Stereo delay effect
  - 複用 DelayLine module (circular buffer + linear interpolation)
  - One-pole LP filter in feedback path (~4kHz cutoff) for warm repeats
  - R channel 10% longer delay for spatial width
  - Parameters: time (50~2000ms), feedback (0~0.95), mix
- `Compressor.h` — Peak compressor/limiter
  - Linked stereo detection (max of L/R) to prevent image shift
  - Fixed attack 5ms / release 100ms for clean operation
  - Auto makeup gain (compensates for average gain reduction)
  - Parameters: threshold (-40~0 dB), ratio (1~20)
- `EffectChain.h` — Global chain orchestrator
  - Processing order: Compressor → Delay → Reverb
  - Reads APVTS atomic parameters per block
  - Stereo-aware processing (mono fallback supported)

**PluginProcessor 更新：**
- Effect chain integrated in processBlock (after synth engine render)
- 7 new APVTS parameters: fx_reverb_mix, fx_reverb_size, fx_delay_time, fx_delay_feedback, fx_delay_mix, fx_comp_threshold, fx_comp_ratio
- effectChain.prepare() called in prepareToPlay

**PluginEditor 更新：**
- Window height increased to 580px to accommodate effect section
- Bottom section: EFFECTS label + divider, always visible regardless of engine
- 3 rows: Reverb (mix + room), Delay (time + feedback + mix), Compressor (threshold + ratio)

**目前總參數量：** 1 global + 6 cimbalom + 7 chromatic + 7 fm piano + 7 effects = **28 parameters**

---

## 2026-05-08 — Phase 5 完成：FM Piano 引擎

**新增引擎：**
- `src/engines/FMPianoEngine.h` — 2-operator FM 合成
  - 核心公式：output = sin(carrierPhase + I(t) * sin(modulatorPhase + fb*lastMod))
  - Modulator self-feedback：產生更豐富的泛音（organ、brass 音色的關鍵）
  - Index envelope：獨立的指數衰減控制 brightness（與 amplitude ADSR 分離）
  - Velocity 雙重感應：影響 gain（音量）+ modulation index（亮度）
  - Note-dependent brightness：高音符的 index 衰減更快（自然鋼琴行為）
  - 8 種 Sound Type preset 控制 ADSR 形狀：
    - Piano (fast decay, low sustain)
    - E.Piano (medium decay)
    - Vibraphone (long decay, low sustain)
    - Bell (very long decay, no sustain)
    - Organ (instant to full sustain)
    - Pad (full sustain, for long notes)
    - Bass (fast decay)
    - Brass (medium sustain)

**PluginProcessor 更新：**
- 三引擎架構完成：cimbalomSynth + chromaticSynth + fmPianoSynth
- Engine 選擇器擴展為 3 選項（Cimbalom / Chromatic / FM Piano）
- 新增 7 個 FM 參數：fm_type, fm_ratio, fm_index, fm_brightness, fm_feedback, fm_attack, fm_release
- fm_ratio 使用 skewed range (0.4) 讓低 ratio 區間（鋼琴常用的 1.0~2.0）有更高解析度

**PluginEditor 更新：**
- 三引擎面板切換完成
- FM Piano 面板：Type 選擇器 + Ratio/Index、Brightness/Feedback、Attack/Release 三行佈局
- 副標題：「FM Piano Engine | Frequency Modulation Synthesis」

---

## 2026-05-08 — Phase 4 完成：Chromatic Synth（三合一物理建模引擎）

**新增物理模型：**
- `src/physics/BeamModel.h` — Euler-Bernoulli 梁振動模型（空靈鼓 Tongue Drum）
  - Free-free beam eigenvalues：β₁=4.730, β₂=7.853, β₃=10.996, β₄=14.137, β₅=17.279
  - 非諧波模態序列（ratio: 1.000, 2.757, 5.404, 8.933, 13.345）→ 空靈鼓特有的「鐘聲感」
  - MIDI note → 舌片長度自動計算（A4=0.12m 基準，L ∝ 1/√f）
- `src/physics/PlateModel.h` — Kirchhoff 圓板振動模型（水鑼 Water Gong）
  - 20 組 Bessel 函數零點 j(m,n)，涵蓋 m=0~8, n=1~4
  - 2D 擊打位置建模：中心敲擊 → 軸對稱模態(m=0)強，邊緣 → 高 m 模態強
  - MIDI note → 圓板半徑自動計算（A4=0.15m 基準，R ∝ 1/√f）

**新增引擎：**
- `src/engines/ChromaticEngine.h` — ChromaticVoice 三合一引擎
  - Sub-engine 0: Tongue Drum（BeamModel 驅動，12 模態）
  - Sub-engine 1: Water Gong（PlateModel 驅動，20 模態）
  - Sub-engine 2: Custom（使用者自填 ratio/amplitude，8 組泛音）
  - Water Gong pitch glide：持續降低模態頻率模擬浸水效果（最大 15% pitch drop）
  - Exciter 噪音脈衝：4 級硬度（Soft/Medium/Hard/Sharp）→ LP 濾波 + 脈衝寬度

**PluginProcessor 重構：**
- 雙引擎架構：`cimbalomSynth` + `chromaticSynth`，各 16 voice
- 新增全域 `engine` 參數（Cimbalom / Chromatic 切換）
- 新增 7 個 Chromatic 參數（chr_sub_engine, chr_material, chr_strike_pos, chr_thickness, chr_size, chr_exciter, chr_pitch_glide）
- processBlock 引擎路由：切換時自動 allNotesOff 防止殘留音符
- prepareToPlay 同時設定兩個 synth 的 sample rate

**PluginEditor 更新：**
- 引擎選擇器 ComboBox（頂部）
- 參數面板動態切換：選 Cimbalom 顯示弦參數，選 Chromatic 顯示梁/板參數
- APVTS Listener 監聽 engine 參數變化 → MessageThread 安全更新 UI
- 副標題隨引擎切換：「Cimbalom Engine | Physical Modeling String」/「Chromatic Engine | Beam / Plate / Custom」

---

## 2026-05-08 — Phase 3 完成：Cimbalom 引擎（物理建模弦）

**核心完成：**
- `src/engines/CimbalomEngine.h` — CimbalomVoice（取代 Phase 1 的 SineVoice）
  - ModalResonator + StringModel 驅動，MIDI note → 物理弦參數 → 40 模態渲染
  - 多弦 beating：每 course 1~5 條弦，可調失諧量（0~15 cents）
  - Exciter 噪音脈衝：槌硬度（cotton/felt/wood/metal）→ LP 濾波頻寬
  - Damper 控制：note off + CC#64 sustain pedal
- PluginProcessor 改用 APVTS（AudioProcessorValueTreeState）
  - 6 個可自動化參數：Material / Strike Position / Diameter / Hammer / Strings / Detuning
  - 支援 preset save/load（ValueTree → XML）
  - MaterialDB 透過 BinaryData 嵌入（不依賴外部 JSON 路徑）
- PluginEditor 改為參數控制介面（ComboBox + Slider + Label）

**Build 修正：**
- CMakeLists 加 `add_compile_options(/utf-8)` 解決 MSVC codepage 950 與 UTF-8 中文註解衝突
- `juce_add_binary_data` 嵌入 `data/materials.json`
- MaterialDB 新增 `loadFromString()` / `loadFromBinary()` 方法
- `getOrderedKeys()` 靜態方法提供固定材質排序（給 AudioParameterChoice 用）

---

## 2026-05-08 — Phase 1 + Phase 2 完成

### Phase 1：環境建置 + 骨架

**環境確認：**
- Visual Studio 2026 Community（`D:\Visual_Studio`，MSVC 14.50.35717）
- CMake 4.3.2（winget 安裝）
- Cubase LE AI Elements 12（測試用 DAW）

**完成項目：**
- JUCE 8 以 git submodule 加入（`libs/JUCE`，shallow clone）
- `CMakeLists.txt` — VST3 + Standalone 雙格式輸出
- `src/PluginProcessor.h/.cpp` — 16 voice polyphonic sine synth（juce::Synthesiser 架構）
- `src/PluginEditor.h/.cpp` — 最小 GUI（深色背景 + 標題）
- CMake generator：`Visual Studio 18 2026`（VS 裝在非標準路徑 D 槽，需指定 generator instance）
- Build 成功：零錯誤，C4819 warnings 為 JUCE 內部 codepage 問題可忽略

**VST3 驗證：**
- 產出 `TsukiSynth.vst3` 複製到 `C:\Program Files\Common Files\VST3\`
- Cubase 成功載入、MIDI 輸入有聲音輸出 ✅

**備註：**
- `%APPDATA%\VST3\` 路徑在使用者的檔案總管中不易找到（AppData 隱藏），最後手動複製到 Program Files
- CI（GitHub Actions）延後，優先推進功能開發

---

### Phase 2：DSP 模組 + 材質數據庫

**DSP 模組（全部 header-only，`src/dsp/`）：**

| 模組 | 重點設計 |
|------|---------|
| `Oscillator.h` | 相位累加器，Sin/Saw/Square/Triangle 四波形 |
| `Envelope.h` | 雙模式：ADSR（FM Piano 用）+ ExpDecay 內部類（Modal 每模態獨立衰減） |
| `BiquadFilter.h` | Audio EQ Cookbook 係數，LP/HP/BP/Notch |
| `DelayLine.h` | 環狀緩衝 + 線性插值 + feedback + pushSample/popSample API |
| `NoiseGen.h` | White（mt19937）+ Pink（Paul Kellet 6 階 IIR 近似） |
| `LFO.h` | 複用 Oscillator，加 depth / unipolar 控制 |
| `ModalResonator.h` | ⭐ 核心：N 模態衰減正弦波渲染，excite/damp API，自動截斷超出人耳範圍的模態 |

**Physics 模組（`src/physics/`）：**

| 模組 | 重點設計 |
|------|---------|
| `MaterialDB.h` | 用 juce::JSON 解析 `data/materials.json`，map 查詢，9 種材質 |
| `StringModel.h` | 弦模態頻率公式（含 inharmonicity 修正）、物理衰減、擊打位置振幅、MIDI→弦長/張力換算 |

**設計決策：**
- 全部 header-only：DSP 函式短小適合 inline，免改 CMake
- ModalResonator 只負責渲染（接收 Mode 列表），物理計算由 StringModel/BeamModel/PlateModel 分離
- ExpDecay 用每 sample 乘法因子（`exp(-6.9/τ/sr)`）而非每 sample 算 exp，效能好

---

## 2026-05-06 — Phase 0 規劃

- 建立 repo `TsKR2828/tsuki-synth`
- 撰寫 README.md + ROADMAP.md（含完整 10 phase 規劃）
- 建立 `data/materials.json`（9 種材質物理參數）
- 建立 AI Score Pipeline 資料格式先行設計：
  - `scores/schema/score.schema.json`（JSON Schema draft 2020-12）
  - `scores/examples/` — 3 個範例 score
  - `sound_library/sound_names.json` + `tags.json`
