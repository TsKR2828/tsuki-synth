# TsukiSynth 開發日誌

---

## 2026-07-23 — round-4：五項待裁決落地 + 殘差判定制/f0 course 質心收緊規約

分支 `fix/deep-physics-audit-20260716`（延續 round-3，全程 unstaged、未 commit/push）。月月在對話中對 round-3 留下的五項待裁決明示「都照推薦的做」，本輪把裁決結果落地到文件（`ROADMAP_PHYSICS.md`／`TODO.md`／`DEVLOG.md`／`README.md`），**未改動任何 `src/`／`tools/` 程式碼**——(4)(5) 兩項需要的程式改動由另一輪工作平行進行中。

### 五項裁決

1. **velocity 量測域（寬帶→基頻窄帶）** — 追認。round-3 已把 F3 velocity 判定的量測域從寬帶 RMS 改到基頻 ±3% 窄帶，判定式數值未動；月月本輪正式追認此程式邏輯變更。
2. **`summer_m2`／`summer_m3` reverb decay 收斂** — 接受。`summer_m2` 2.8→2.6、`summer_m3` 累計 2.1→1.0，機器 GATE round-3 已過（`verify_score.py` 全項 PASS 含 determinism SHA256 match），藝術效果本輪由月月最終確認。
3. **`spectralTilt` heuristic 層去留** — 降級保留。聲音不動（`src/engines/CimbalomEngine.h` 的 `spectralTilt` 邏輯本輪零改動），劃界為已文件化 creative 層，不算入物理主張；`ROADMAP_PHYSICS.md` §0 與 `README.md` 域表同步加註。
4. **殘差頻譜能量：資訊性 → 判定制** — 批准，門檻 **-60.0 dB re total**。依據 round-2/round-3 累計實測基線 -74.7～-83.1 dB re total（`reports/gate_outputs/deepfix2_gate_full.txt` 等），距門檻留有 ≥14.7 dB 安全邊際。**程式改動（`tools/physics_verify.py`）由另一輪工作平行進行中**：本輪檢查確認 `RESIDUAL_BAND_HALF_WIDTH` 一帶截至此刻仍是資訊性輸出，尚未切換判定邏輯。
5. **`MODE_F0_TOL_CENTS`：授權改量測法後收緊** — 批准，量測邏輯改為 course 質心／平均後，數值由 **12.0 → 5.0**（與 `physics_verify.py` 全域容差一致）。歷史理由：舊量測點是 `--dump-modes` 的 `partials[0]`（多弦課「第 0 條弦」，by design 偏移 `-detuningCents`），非聲學質心。**程式改動（`tools/verify_score.py` 的 `check_modes()`）由另一輪工作平行進行中**：本輪檢查確認 `MODE_F0_TOL_CENTS` 截至此刻仍是字面值 `12.0`，尚未改寫。

### GATE 證據路徑規約

`reports/gate_outputs/deepfix4_*`——(4)(5) 兩項程式改動落地後，該輪工作需在此路徑下補存 selftest／`--full`／`verify_score` 等 GATE 輸出；本條目先登記路徑規約，實際結果由後續補上或引用。

### 文件同步（本輪，僅文件，Rule 5）

- `ROADMAP_PHYSICS.md`：§0 驗證域表 Cimbalom/Piano 列加 spectralTilt 劃界註記；§6 容差登記表 velocity 列依據欄追加 2026-07-23 追認記錄、殘差頻譜能量列現值改為「判定制 -60.0 dB re total（批准，實作中）」、f0（`verify_score.py`）列改為「±5 cents（course 質心量測法，授權收緊，實作中）」，三列皆保留舊有歷史理由一句。
- `README.md`：Physical Verification 域表 Cimbalom/Piano 列同步 spectralTilt 劃界註記（與 `ROADMAP_PHYSICS.md` 同一句意譯為英文）。
- `TODO.md`：五項裁決逐條改標 `[x]` + 裁決日期 + 一句話結果；新增「2026-07-23 round-4 裁決落地」段落記錄範圍與程式改動現況；round-3 snapshot 段落補一句 ratified 標記；Rule 10 報告審閱、Cubase 人工驗證、HTML 視覺驗收、push 時機等月月人工項維持 open，未關閉。

### Rule 1/2/4 確認

本輪未執行任何 git 變更狀態指令（commit/push/add/checkout/restore/stash/clean/reset），檔案留 unstaged。未調寬任何容差——(4)(5) 皆為收緊方向的裁決記錄，且尚未落地到程式碼；文件中新出現的數字（-60.0 dB re total、5.0 cents）均已註明來源（實測基線／歷史理由）與批准記錄（月月 2026-07-23）。驗收依 git diff --stat 摘要為準，見本條目末尾。

---

## 2026-07-22 — Deep physics audit round-3：velocity 量測域修正 + summer m2/m3 rest 超標修復

分支 `fix/deep-physics-audit-20260716`（延續 round-2，全程 unstaged、未 commit/push）。本輪處理 round-2 留下的兩項月月待裁決：piano velocity 物理律「違規」與 `summer_m2`／`summer_m3` 的 rest RMS 超標。兩者都不是容差變動——前者是量測域對齊物理律本身的適用範圍，後者是藝術參數（reverb decay）的收斂。

### F3 velocity 量測域修正：寬帶 → 基頻窄帶

`20·log10(2) = 6.0206 dB` 這條律的物理主張是「單一模態激發振幅正比於槌速」（`ModalResonator::excite()`），適用域是逐模態，不是寬帶頻譜形狀。round-2 的判定拿寬帶 RMS 當量測域，因此把 Hertz 接觸時間隨槌速變短、帶來的頻譜變亮（物理真實，見 `HammerImpulse.h`）也算進了「違反振幅律」——這不是振幅律的錯，是量測域選錯了。

`tools/physics_verify.py` 新增 `measure_band_rms_db()`／`FUND_BAND_HALF_WIDTH`（沿用 `measure_t60()` 同一套 ±3% Butterworth band-pass 家族），`judge_velocity()` 改在以 `measure_f0()` 量得的 f0 為中心的基頻窄帶上算 `measured_delta`/`predicted_delta`；`assess_velocity_delta()` 的判定式（`|predicted−6.0206|≤1.0` 且 `|measured−predicted|≤1.0`）數值本身**未動**。舊寬帶 RMS delta 仍印出，但標為資訊性行（「含 Hertz 接觸時間頻譜變亮，物理真實，見 `HammerImpulse.h`」），不再影響判定與 exit code。

selftest 4b（`selftest_velocity_law_negative`）改注入「弱基頻（440 Hz，比合法的 880 Hz 泛音弱 400 倍）裡的違規」，證明基頻窄帶能抓到寬帶會漏掉的問題（實測：同一對違規資料，f0-band +9.00 dB vs 寬帶 +6.03 dB）；原本的 uniform-scale +9 dB 反例保留為 `selftest_velocity_law_negative_uniform_scale()`。`tests/test_physics_verify.py` 新增 3 項（`test_selftest_velocity_law_negative_uniform_scale`、`test_fundamental_band_counterexample_isolates_violation`、`test_fundamental_band_lawful_pair_passes`）。

**實測（5 個 modal 引擎，MIDI 60，velocity 48→96，基頻窄帶）**：cimbalom +6.0587 dB（偏差 +0.04）PASS、tongue_drum +6.0574 dB（+0.04）PASS、water_gong +6.0586 dB（+0.04）PASS、water_gong_free +6.0588 dB（+0.04）PASS、piano +6.6702 dB（+0.65）PASS——**全數 PASS**。piano 的寬帶違規（+7.4373 dB，資訊性，round-2 舊值不變）確認是主迴圈已診斷的 Hertz 接觸時間頻譜變亮，不是振幅律破功。

### summer_m2／summer_m3：reverb decay 收斂修復 rest RMS 超標

round-2 逐聲道量測揭露的兩個既有超標，本輪用 FX-bypass 已鎖定源自 reverb 尾巴這個前提，收斂 `reverb.decay`（`wet` 兩首都不動）：

- **summer_m2**：`decay` 2.8 → 2.6（wet 0.28 不動）。全窗口掃描 2.8/2.75/2.7/2.65/2.6/2.4/2.2/2.0；2.8（原值）3 個休止窗量到 -49.9/-51.7/-49.9 dBFS（2/3 超標）；2.65 裕度仍不足（1.9 dB）；**2.6 是達到全窗口 ≥2 dB 裕度最保守的值**：-52.6/-54.5/-52.6 dBFS（2.6/4.5/2.6 dB 裕度）。
- **summer_m3**：`decay` 1.2 → 1.0（wet 0.20 不動；此曲 decay 在更早、尚未 commit 的階段已從 2.1 掃到 1.2，本輪是在 1.2 之上再收）。1 個休止窗；1.2（原值）量到 -47.1 dBFS（超標 2.9 dB）；1.05 裕度仍不足（1.0 dB）；**1.0 是達到 ≥2 dB 裕度最保守的值**：-52.5 dBFS（2.5 dB 裕度）。

完整逐點掃描（含每個 decay 值對音樂效果的影響備註）存於 `reports/gate_outputs/deepfix3_summer_rest_sweep.txt`，結尾標「待月月最終確認」。兩份改動後的 score 各自用 `tools/verify_score.py` 全項重驗（schema/modes/render/rests/peak/clipping/determinism）：**exit 0，含 SHA256 determinism match**。`-50.0 dBFS` 門檻數值全程未動，未新增豁免。

順帶重新產生已過期的 `scores/originals/rules_v2_demo/rules_v2_demo_001.report.html`（原檔停留在改動前的 2026-07-17，score.json 已於同日稍後改動）：`verify_score.py --html` exit 0，程式化確認六區塊齊全（banner + 2 spectrogram + 3 f0 + 4 loudness + 5 phrases/rests + 6 footer）、0 個 http(s) 外部參照。

### 最終 GATE（本輪）

- `physics_verify.py --selftest`：**PASS** 11/11，含新反例 `velocity_law_violation_rejected`（f0-band +9.00 dB 雙向拒絕；寬帶會讀到 +6.03 dB 而漏掉）與 `velocity_law_violation_rejected_uniform`（`reports/gate_outputs/deepfix3_selftest.txt`）。
- `python -m unittest tests.test_physics_verify tests.test_consonance_contract tests.test_verify_score_contract`：**PASS** 47 tests OK（`reports/gate_outputs/deepfix3_pytests.txt`）。
- `physics_verify.py --full --skip-amps`：**PASS**，`RESULT: NO CHECKED FAILURES`，「1d velocity judgment：PASS」；未驗證範圍仍是既有 3 個 rubber T60 過短案例（`reports/gate_outputs/deepfix3_gate_full.txt`）。
- `summer_m2`／`summer_m3` `verify_score.py`：**PASS**，兩者 exit 0，rest RMS 裕度 2.6/2.5 dB，determinism SHA256 match（`reports/gate_outputs/deepfix3_summer_verify.txt`）。
- `rules_v2_demo` HTML 重生成：**PASS**，六區塊齊全、0 外部參照（同上檔）。
- Corpus 回歸抽驗（未觸碰的 `physical_piano.score.json`）：**PASS**，exit 0，SHA256 match（`180b4267…`），確認本輪兩處 score 編輯以外零回歸（同上檔尾段）。

### 文件同步（本輪）

`ROADMAP_PHYSICS.md`：頂部補「2026-07-22 deep-audit round-3 update」節；§6 velocity 列措辭更新為「基頻窄帶（測得 f0 ±3%）」量測域、判定數值不變、寬帶 delta 改列資訊性，依據欄註記 2026-07-22 授權與 round-2 寬帶存證出處。`TODO.md`：piano velocity 待裁決項改記為已修正量測域、`--full` 回綠；summer m2/m3 兩筆待裁決改記為已修（decay 前後值），藝術變更待月月確認；rules_v2_demo HTML 過時項關閉。`docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md` 文末追加 Round-3 補記，紀錄三項遺留（velocity、summer rest RMS、HTML 過時）的處置與新證據路徑。

---

## 2026-07-18 — Deep physics audit round-2：覆核修復 + 四線並行 GATE + corpus 全量重跑

分支 `fix/deep-physics-audit-20260716`（延續 2026-07-17 第一輪，全程 unstaged、未 commit/push）。本輪四線並行覆核第一輪成果本身（harness／測量工具、score 資產／manifest、C++ 引擎／文件、docs／CI 設定），找到的是**驗證程序缺口**——理論特徵值常數是死碼、f0 判定退化成模型驗證自己、velocity 律沒有上限、立體聲混降掩蓋真實超標——不是新的物理模型錯誤。完整方法、逐項 GATE 命令與 corpus 完整清單見
`docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md`。

### 稽核發現與修復清單

- **F1 特徵值錨退化**：`BEAM_BETAL`／`PLATE_OMEGA`／`PLATE_FREE_OMEGA` 常數從未接回驗證路徑。`tools/physics_verify.py` 新增 `CANTILEVER_BETAL`（解析根）與 `free_plate_omegas()`（scipy 從 Kirchhoff 自由板特徵行列式第一原理重解，與 C++ 表獨立），`scan_eigenvalue_anchors()` 對 4 個邊界條件 case 判定，容差 0.10%／0.50%（free-edge）。
- **F2 f0 主錨退化**：midi 模式的 f0 判定曾拿 dump 值驗證自己；新增 `f0_expected_et` 錨回 12-TET 理論頻率（±5 cents，§6 數值未動），dump 一致性降為輔助檢查。
- **F3 velocity 律無上限**：新增 `VELOCITY_LAW_DB = 20·log10(2) = 6.0206` 上限判定，要求模型預測值本身（非僅 render vs 模型互相印證）落在 ±1.0 dB 窗內——這正是本輪抓到 piano 違規的機制。
- **F5 殘差頻譜能量**（新增，資訊性）：扣除 30ms exciter 噪聲窗後量測預測模態帶外殘留能量，不影響 exit code，門檻轉判定制待月月批准。
- **逐聲道 rest RMS**：`tools/verify_score.py` 的休止 RMS 判定改量每個窗口「最大聲聲道」而非 `(L+R)/2` 混降，避免去相關立體聲殘響尾巴互相抵消掩蓋真實超標；`-50.0 dBFS` 門檻數值未動。
- **Render manifest v2**：`src/cli/RenderApp.cpp` 新增 `wav_sha256`（實際 WAV bytes 的 SHA256），`verify_score.py` 據此驗證 manifest 與音訊一致；v1 仍明確接受為 legacy。
- **C++ 文件/生命週期**：`ScoreRenderer.h` dumpModes 的 chromatic custom-atoms 分支改用堆積配置杜絕潛在懸空指標；`StringModel.h`／`BeamModel.h`／`PlateModel.h` 補齊 velocity 慣例與正規化語意註解；`CimbalomEngine.h` `spectralTilt` 啟發式與過期 mix 註解補正；`CMakeLists.txt` 的 `TsukiSynthTunerTest` 補齊與另兩個測試 target 相同的編譯/連結設定，`VERSION 0.2.0→0.3.0`。
- **docs／CI 設定**：`.gitignore` 的 `bin[AB]/` 字元類改成兩條字面規則（實際生效，`git check-ignore` 驗證）；`physics.yml` push 分支 `main`+`Codex-fix-bug` → `main`+`fix/**`；`README.md` 清除過期 v0.2.0 敘述與 `DEV-LOG.md` 舊參照。

### 最終 GATE（本輪）

- Rebuild（六 target）：**PASS**，零編譯錯誤。
- `ctest`：**PASS** 3/3（`reports/gate_outputs/deepfix2_ctest.txt`）。
- `physics_verify.py --selftest`：**PASS**，含新反例 `amps_wrong_amplitude_rejected`／`velocity_law_violation_rejected`（`reports/gate_outputs/deepfix2_selftest.txt`）。
- `physics_verify.py --full`：**FAIL（誠實）**，exit 1（`reports/gate_outputs/deepfix2_gate_full.txt`）。唯一紅燈：piano MIDI 60 velocity ×2，模型預測自身 `+7.4373 dB` 違反 `6.0206 ± 1.0 dB` 物理律上限（render `+7.4367 dB` 與模型互相吻合，正是新檢查要抓的退化）；tongue_drum margin 僅 `0.012 dB` 逼近上限，一併提請留意。其餘：F1 特徵值錨、1b ET 範圍掃描（最大偏差 0.031 cents）、1c 材質敏感度（可量測案例）、2d 振幅判定、5b 測得 T60（0.99–1.00）全 PASS；F5 殘差能量純資訊性 `-74.7`～`-83.1 dB re total`；3 個既有 rubber `UNVERIFIED/N/A` 案例維持不變。
- Tuner oracle（`tuner_audit.py` + `tuner_audit_v2.py`）：**PASS**，v1 9 checks／v2 14 checks 0 failure，獨立 oracle 最差誤差 0.2076 cents（`reports/gate_outputs/deepfix2_tuner_oracle.txt`）。
- `python -m unittest tests.test_physics_verify tests.test_consonance_contract tests.test_verify_score_contract`：**PASS** 44 tests OK（`reports/gate_outputs/deepfix2_pytests.txt`）。
- Draft 2020-12 schema，80 個 tracked `.score.json`：**PASS** 80/80（`reports/gate_outputs/deepfix2_schema80.txt`；`verify_score.py` 無 schema-only CLI 模式，本 GATE 依指示用 scratchpad 驅動腳本原封不動呼叫 `check_schema()`，方法記錄於存證檔標頭）。
- `consonance.py` + `check_piece_consonance.py`（rules_v2_demo_001）：**PASS**，13 pairs 13 PASS 0 not-PASS（`reports/gate_outputs/deepfix2_consonance.txt`）。
- Probe SHA 比對：**match**——`physical_piano.wav`／`water_gong_clamped.wav` 用重新編譯的 CLI 渲染後與改動前基線位元完全相同，manifest v2 修改未影響音訊。

### Corpus 全量重跑（四分片 + HTML 抽驗，涵蓋全部 73 個 repository score）

- `A_examples_airadiance`（18 檔）：**18/18 PASS**（`reports/gate_outputs/deepfix2_corpus_A_examples_airadiance.txt`），既有 moonlight `rests.rms` 登記豁免依原樣觸發，無新增豁免。
- `B_classical`（Vivaldi 四季 12 檔）：**9 PASS／3 FAIL**（`reports/gate_outputs/deepfix2_corpus_B_classical.txt`）——`summer_m2` rest 20.65–21.33s 實測 `-49.9 dBFS`（門檻 -50.0，超標 0.1 dB）、`summer_m3` rest 5.12–6.00s 實測 `-47.1 dBFS`（超標 2.9 dB，舊混降法只量到 -52.6 dBFS）；FX-bypass 同窗皆 `-120.0 dBFS`，確認源自 reverb 尾巴而非模型衰減，**均未登記豁免，待月月裁決**。`autumn_m1` 的 `determinism.rendered_twice` FAIL 為高併發環境下第二次渲染進程啟動失敗（`STATUS_DLL_INIT_FAILED`），2026-07-21 單獨重驗 `ALL CHECKS PASSED`、SHA256 `2c1aa8efe869…` 兩次一致，**非真回歸，已解除**。
- `C_library_1`（21 檔）：**21/21 PASS**（`reports/gate_outputs/deepfix2_corpus_C_library_1.txt`）。
- `D_library_2`（22 檔）：**22/22 PASS**（`reports/gate_outputs/deepfix2_corpus_D_library_2.txt`）。
- `html` 樣本報告（2 份，重新生成）：**2/2 PASS**，六區塊齊全、0 外部參照。
- **淨結果**：73 個 repository score 中 71/73 淨 PASS，2 個新 FAIL（`summer_m2`／`summer_m3`）皆為逐聲道 RMS 量測法（取代舊混降法）首次揭露的既有真實超標，非本輪引擎/資產改動造成的回歸；§6 容差全程未動，無新增豁免。

### Rule 10 前後對照

`reports/deep_fix_before_after.md`：改動前 baseline CLI（commit `485c6c1`）與工作樹 CLI 對 8 首代表曲目（7 首指派 + 1 首額外 FM 域外對照組）做 RMS/peak/頻譜質心/T60/f0 全面比對。RMS 變化 `-3.712`（water_gong_free，完整觸發 Bessel free-edge 重寫）～`+2.346 dB`（physical_piano，唯一變大聲，歸因弱模態 -60dB 生命週期修正蓋過 tau→T60 縮短）；3 個獨立音符探針 f0 偏移 <1.5 cents，音高不受影響。`vivaldi_four_seasons_summer_m3` 為 score+engine 雙重改動未拆解（before 用改前 score `reverb.decay=2.1`）。

### 文件同步（本輪）

`ROADMAP_PHYSICS.md`：頂部「2026-07-18 deep-audit round-2 update」節補上本輪實際 GATE 結果與證據路徑；§6 容差登記表僅前一階段已授權的四列（T60、velocity、殘差、休止 RMS）變動，其餘未動。`TODO.md`：round-2 骨架逐項填實，corpus 新 FAIL 與 Rule 10 報告列入月月待裁決／待審閱。詳見 `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md` 全文。

---

## 2026-07-17 — Deep physics audit 全面修復、事件級協和度與最終 corpus 收斂

分支 `fix/deep-physics-audit-20260716`，保持 local／uncommitted／unpushed，並保留使用者
未追蹤的 `reports/phase_h_before_after/binA/`、`binB/`。本節是目前狀態；下方 Phase
D–K 數字是歷史存證，不應拿來覆蓋本節的新模型與新 GATE 結果。

### 實作結果

- Tuner 改為量測 dry audio，TARGET／MEASURED 分離；A0–C8、44.1–192 kHz、confidence
  與明確 refusal，並補 MIDI channel/retrigger/sustain/CC120/121/123 狀態機。
- Beam 預設 fixed-free cantilever，free-free 明確選用；Plate 改用含 Bessel／modified
  Bessel 的圓板模態形狀與 Poisson-dependent free-edge roots。MIDI／geometry 頻率模式
  分開，阻尼在最終頻率後計算，槌接觸時間含 velocity 律，弱模態以相對 −60 dB 截止。
- Score parser/schema 改為嚴格契約；custom ratios/amps、事件 identity、PCG seed、尾巴、
  layer/batch/manifest/atomic write 全接線。MaterialDB reload 交易式提交。Plugin／CLI 共用
  FX 實作，delay 0–5 s 與 reverb per-comb T60 有回歸測試。Preset 使用 stable ID/cache。
- `tools/check_piece_consonance.py` 不再拿固定 MIDI 60／固定引擎方向表代替實曲；它讀取
  每個 event 真實 `--dump-modes` 的所有 active strings、material/geometry/boundary/
  strike/velocity hammer spectrum 重算 Sethares curve。報告記錄 score／checker／公式
  工具／CLI SHA256，預設依 score 命名，不再覆蓋別首曲子的報告。
- Rules-v2 demo 的 MIDI 55 匯聚 cell 改用 event-specific 200-cent M2；MIDI 60 B 段保留
  700-cent P5。每個 steel cimbalom event 明寫 `damping_override: 0.5`，鎖住 T60/3 契約。
- 全庫重跑暴露兩個最後問題並修掉：(1) layered composite 的頂層 `--dump-modes` 是 CLI
  契約上的 N/A，verifier 現改成頂層明列 N/A、逐一 mode-scan leaf；(2) Vivaldi Summer
  m3 的 reverb `decay=2.1s` 令唯一休止窗只有 −40.1 dBFS。固定 wet=0.2 掃描 1.8/1.5/
  1.3/1.2/1.1/1.0 s 得 −43.02/−46.93/−50.44/−52.60/−55.10/−58.07 dBFS，選 1.2 s
  保留 2.6 dB 裕度，未改 −50 dBFS 門檻、未新增豁免。

### 最終 GATE（本分支）

- Release build：CLI、VST3、Standalone、Audit、Tuner、PhysicsModels 六 target 全部 exit 0。
- CTest：3/3 PASS。Python metrology/contract 單元測試全部 PASS；`physics_verify.py
  --selftest` 的 adversarial cases 全部依預期拒絕錯誤輸入。
- Tuner oracle：A0–C8 共 1056 個量測 PASS，160 個範圍外案例明確拒絕，最差 0.2076 cent。
- `physics_verify.py --full`：所有 checked cases 無失敗；10 個 T60 probe measured/model
  約 0.99–1.00。三個 14–28 ms rubber 案例明列 `UNVERIFIED/N/A`，不是 PASS。
- Draft 2020-12 schema：80/80 repository score PASS。
- `verify_score` 全 release corpus 四分片：34/34、18/18、16/16、5/5，合計 **73/73
  PASS、0 FAIL**；1 個既有 moonlight `rests.rms` 登記豁免保持可見，無新增豁免。
- Rules-v2 event-specific consonance：**13 PASS、0 VIOLATION、0 UNVERIFIED**；完整表在
  `reports/rules_v2_demo_consonance_check.md`。

完整方法、命令、驗證域與剩餘科學落差見
`docs/DEEP_FIX_VERIFICATION_2026-07-17.zh-TW.md`。

---

## 2026-07-13 — Phase I 收尾：測量法適配物理化材質 + 最終 GATE 存證 + 月月「留」決策記錄

**月月 2026-07-12 決策**：materials 物理化（Phase G+H，密度/楊氏模數/阻尼全面改為文獻/推導值）**維持（「留」）**，不 revert。本輪任務性質是「調整量測方法去配合新物理」，不是調容差——§6 容差全程凍結（f0 ±5 cents 預設、partial 2–4%、amps ±3.0 dB、T60 0.5–2.0、velocity ±1.0 dB、rest -50dB、peak -0.3dBFS，一個數字都沒動，Rule 2）。範圍限定 `tools/physics_verify.py`（Python-only），未碰 `src/` C++、`data/materials.json`、`uiux/`、任何 score JSON，渲染音訊維持位元不變。

### 三項最終 GATE 存證（Phase H 物理化材質數值之上重跑）

- `python tools/physics_verify.py --full` → `reports/gate_outputs/phase_i_gate_full.txt`：`RESULT: ALL WITHIN TOLERANCE`（1b/1c/1d/2d 全 PASS）。
- `python tools/physics_verify.py --t60 --notes 60 72` → `reports/gate_outputs/phase_i_gate_t60.txt`：`RESULT: ALL WITHIN TOLERANCE`（5 引擎 × 2 音全 PASS，容差 0.5–2.0 判定制，Phase H 當時記錄的 2 個 harness 侷限 FAIL 本輪隨量測窗口重算收斂）。
- `python tools/physics_verify.py --amps` → `reports/gate_outputs/phase_i_gate_amps.txt`：`RESULT: ALL WITHIN TOLERANCE`（5 modal 引擎前 5 partial 全 PASS）。

### 音訊未變動查核

CLI 二進位 `build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`（mtime 2026-07-12 16:17）早於本輪唯一改動的檔案 `tools/physics_verify.py`——本輪為純 Python 量測法調整，未觸碰任何 `src/`，因此不需要、也沒有重新 build 三個 target。用現有二進位對 `scores/examples/akashic_bell.score.json` 連續渲染兩次（`output/phase_i_check/run1`、`run2`），SHA256 位元完全一致（`9647c06f3203975f1385cc0fb108c44ec3196b27996f383846a14675ccb48a5b`），確認 determinism；`python tools/verify_score.py scores/examples/akashic_bell.score.json` exit 0，`determinism.sha256_match` 與全部其餘檢查皆 `[OK]`，`RESULT: ALL CHECKS PASSED`。

### 文件同步

`ROADMAP_PHYSICS.md`：§2 M5 列補上 Phase I 收尾說明（T60 GATE 在物理化材質之上重新轉綠，引用 `phase_i_gate_t60.txt`）；M7 列補上 Phase I 收尾說明（Phase H 遺留的 3 個 harness FAIL 隨此輪測量法調整收斂，M7 GATE 全綠無殘留）。`TODO.md`：materials keep/revert 待裁決項標記為「已核准（留）並已收斂」；剩餘給月月的項目重列為：4c 視覺驗收（HTML 報告需月月親自瀏覽器確認）、Cubase 人工驗證 4 步驟、Phase G+H+I 累積改動的 push 時機裁決。

---

## 2026-07-12 — Phase K：兩項音色會變的物理修正轉正（M7-7b 特徵值 + M5-5c 材質阻尼/E）+ 規則 10 全套 + corpus 重跑

分支 `main`（HEAD `4c77c54` 起），未 commit/push，Rule 7。月月 2026-07-12 同意執行兩項會改變既有渲染音訊的修正：(1) `PLATE_FREE_OMEGA` (4,0) 更新為文獻一致值；(2) materials 阻尼/楊氏模數物理化。§6 容差全程未動（Rule 2）。本輪任務：把這兩項已經落地在工作目錄的數值改動，補上規則 10 要求的完整前後對照證據 + corpus 重跑 + 文件同步。

### 兩項修正的現況（進來時已由前一輪工作套用在working tree）

- `src/physics/PlateModel.h` 的 `freeModes[]` 第 5 項：`{ 21.83f, 4, 0 } → { 21.527f, 4, 0 }`（`tools/physics_verify.py` 鏡射同步）。依據 `docs/EIGENVALUE_SOURCES.md` §3：Leissa NASA SP-160 Table 2.5 給 21.6（表格自身標「±2% 近似」），本任務獨立重解精確特徵方程給 21.527，兩者都與舊值 21.83 差距 >1%。
- `data/materials.json` 全部 14 種材質的 `damping.alpha` 改用 `T60 ≈ 2.2/(f·η)`（`η`=文獻損耗因子）在 MIDI 60 錨點反推的新值（例如 steel `0.5→0.0238`、bronze `0.8→0.1189`），修正 `wood_spruce.alpha` 排序異常；`rubber.youngs_modulus` 從 `1.5e9→5e6 Pa`（真實橡膠量級）。推導與文獻出處見 `reports/materials_physicalization_proposal.md`（Fletcher & Rossing / Ashby / Lazan / Wegst 2006 等）。`beta_air`/`gamma_radiation` 仍「待溯源」未動。

### Rule 6：三個 build target 重建

因 `src/physics/PlateModel.h` 有數值改動，`cmake --build build --config Release` 對 `TsukiSynthCLI`／`TsukiSynth_Standalone`／`TsukiSynth_VST3` 三個 target 全部 exit 0。

### 規則 10 兩階段前後對照報告：`reports/phase_h_before_after.md`

- **Stage 1（特徵值）**：直接引用既有隔離驗證存證 `reports/gate_outputs/phase_h_eig_delta.txt`——只影響 `water_gong_free` 的 (m=4,n=0) 模態，量測位移 -1.388% 與理論預測位元級吻合，其餘泛音 0.000% 不變。
- **Stage 2（材質）**：`git stash` 取出 HEAD `4c77c54` 單獨編譯出 binary A（改前），與目前工作目錄的 binary B（改後）對 6 首代表曲目（cimbalom×2/tongue_drum/water_gong×2/piano，另加 fm 域外對照組）做 RMS/peak/頻譜質心/T60(寬帶包絡)/top-partial 比對：
  - `fur_elise_opening`（fm，域外）與 `moonlight_sonata_i_yangqin`（cimbalom，但**全部 1142 個事件都用 `damping_override` 逐音覆寫阻尼**，material.json 的新 alpha 對它完全不生效）**位元完全相同**——兩種不同原因，皆非分析疏漏，詳見報告 §2.1/§2.2。
  - 其餘 4 首（tongue_drum、physical_piano、water_gong 兩種邊界）**RMS 上升 0.87–4.82 dB、頻譜質心下降 13.7–141.6 Hz（變暗）、寬帶 T60 拉長 1.3–19 倍，音高不受影響**——全部同一個機制解釋：`alpha`（頻率無關）大砍，`beta·f²`/`gamma·f`（頻率相關，未動）不變，低頻模態受益最大，方向與量級跟 `materials_physicalization_proposal.md` §6 的預測表定性一致。
- **新暴露的 3 個 FAIL（harness 侷限，非渲染 bug，逐一根因追蹤到底，已登記 `TODO.md`）**：
  1. `cimbalom`/`piano` MIDI 60 的 `--t60` 判定從 PASS 轉 FAIL（ratio 0.28）——steel 新 alpha 把 T60 拉到 26.85s，5 秒探針 + 拍頻週期平均法在這麼慢的衰減下失真（拍頻凹陷相對衰減本身占比反而變大）。
  2. `rubber` 材質在 `cimbalom`/`tongue_drum`/`water_gong` 的 f0 材質掃描全部 FAIL——rubber 的 T60 崩到 14–28ms（`η≈0.3` 遠高於其他材質），`measure_f0()` 的量測窗（跳過前 50ms）內訊號已經衰減殆盡，退回 `measure_partials()` 的 fallback 量到的是攻擊瞬態噪聲的偶然峰位，不是穩定基頻。
  3. `piano` MIDI 108（宣告範圍最高音）f0 判定從 PASS（binary A：+0.23 cents）轉 FAIL（binary B：+5~+7 cents）——固定 0.05–1.55s 分析窗在大幅拉長的 T60 下累積更多高頻泛音的頻譜洩漏，把基頻功率質心估計拉偏。
  三者皆用 binary A/B 直接排查根因（非猜測），確認是「阻尼常數變得更真實」撞上既有 harness 固定假設（5 秒探針時長／材質皆能測到基頻／固定分析窗）的直接後果。

### Corpus 全量重跑：`python tools/verify_score.py --all`

存證 `reports/gate_outputs/verify_all_corpus_phase_h.log`：**`73/73 score(s) passed all checks (1 check(s) covered by registered exemption(s)), 0 failed`，exit 0**。唯一的例外是既有登記的 moonlight `rests.rms`（`scores/verify_exemptions.json`，Phase D 就存在，與本輪修正無關）。**沒有新增的 corpus 失敗**——上面 §「新暴露的 3 個 FAIL」全部來自 `physics_verify.py` 的合成探針測試（人工 MIDI 60/72/108 音符 + rubber 材質掃描），不在實際曲目 corpus 的路徑上，因此 `--all` 沒有觸發它們。

### HTML 樣本報告重新生成

`python tools/verify_score.py --html scores/originals/ai_radiance/ai_radiance_m1.score.json` 與 `--html scores/originals/rules_v2_demo/rules_v2_demo_001.score.json` 皆 exit 0、`RESULT: ALL CHECKS PASSED`，反映本輪修正後的最新渲染音訊（`scores/examples/water_gong_clamped.report.html` 在前一輪 Phase H 材質改動落地後已經是最新狀態，本輪未重新觸碰）。

### 文件同步（本輪）

`ROADMAP_PHYSICS.md`：M7 由「In progress（待月月拍板）」轉正為 **Done**（7b 數值已更新，7a/7c 維持不變）；M5 補充 5c 數值更新說明（`damping.alpha` 從「全部待溯源」升級為「已用 eta-Q 關係部分溯源」）；§6 容差表的 f0／T60／振幅三列補上 Phase H 新 FAIL 的誠實揭露（**容差數值本身完全未動**，只是「現值」欄補充最新已知限制）。`TODO.md`：原本登記給月月的 3 項待裁決（rubber E、wood_spruce alpha 排序、free-edge (4,0)）標記為「已核准執行」，改登記本輪暴露的 3 個新 FAIL 為新的待裁決清單。

### GATE 結果彙總

- `reports/gate_outputs/phase_h_gate_amps.txt` → `RESULT: ALL WITHIN TOLERANCE`（振幅判定不受影響）。
- `reports/gate_outputs/phase_h_gate_full.txt` → `SOME CHECKS FAILED`（rubber 材質掃描 3 FAIL + piano MIDI108 f0 1 FAIL，皆已根因分析，見上）。
- `reports/gate_outputs/phase_h_gate_t60.txt` → `SOME CHECKS FAILED`（cimbalom/piano MIDI60 2 FAIL，已根因分析，見上）。
- `reports/gate_outputs/verify_all_corpus_phase_h.log` → `73/73 PASS, 0 failed`，exit 0（實際曲目 corpus 無回歸）。
- 三個 build target（Rule 6）皆 `cmake --build` exit 0。

---

## 2026-07-12 — Phase J：M9 AI 作曲規範 v2（9a/9b/9c/9d），GATE 全過

分支 `main`（HEAD 4c77c54 起），未 commit/push，Rule 7。月月 2026-07-11 授權執行 M5-M9；本輪是最後一個 milestone，M5-M8 已在 Phase G/H/I 完成。**未改動任何 `src/`**，全程只新增 `tools/`、`docs/`、`scores/`、`reports/` 檔案。

### 9a：`tools/consonance.py`（新增） —— Sethares (1993) dissonance-curve 協和度表
對 5 個 modal 引擎（cimbalom / tongue_drum / water_gong / water_gong_free / piano）在 MIDI 60 探針取前 8 個部分音（`--dump-modes` 的 freq×(amp×body_mag)，與 M2 `--amps` GATE 驗證過的同一份理論值，非另外校準）；套用 Sethares 1993 的成對粗糙度公式（常數 d\*=0.24/s1=0.0207/s2=18.96/b1=3.51/b2=5.75，程式內註解引用來源），對每個引擎自身、以及 3 組跨引擎配對（cimbalom↔tongue_drum、cimbalom↔water_gong、tongue_drum↔water_gong）在 0–1200 cents（5-cent 解析度，241 點）掃描總協和度，找局部極小值（建議音程，±10 cents 內）與局部極大值（不建議音程，±15 cents 帶）。輸出 `reports/consonance_tables.md`。有趣的發現：cimbalom 自身最協和的可達成半音音程是八度（dissonance 0.0274）而非純五度（0.0535）；tongue_drum×water_gong 跨引擎在小七度（1000 cents，0.0071）比純五度（0.0533）更協和——非諧引擎的協和規則確實跟鋼琴直覺不同，數字說了算。

### 9b：時值規則（同一份報告 §4）
`--dump-modes` 的 `decay` 欄位＝T60（M5 已驗證），單一指數衰減 dB 值對時間線性，故衰減 20dB 所需時間＝T60/3（代數推論，非新常數）。對 5 個 modal 引擎在 MIDI 48/60/72 算出 T60、T60/3（最小同音重擊間距）、密度上限（音符/秒），列入同一份報告表格。

### 9c：`AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` v2（新增 §13–§16，§1–§12 原文未動）
§13 非諧引擎和聲規則（含「12-TET 可達成」音程表、跨引擎方向限制的誠實說明）、§14 聲部配器建議（cimbalom/piano 擔和聲，tongue_drum/water_gong 擔色彩/節奏，理由是自身局部極小值的量級差異）、§15 長程結構模板（AABA/頑固低音/chaconne，附 JSON `phrases[]` 骨架範例）、§16 時值規則（T60/3 表）。每條規則都指回 `reports/consonance_tables.md` 或既有 GATE 的具體數字。

### 9d：示範新作 + 協和度合規檢查器
新增 `tools/check_piece_consonance.py`：解析 score JSON，找出每一對宣告時間重疊（`[time,time+duration)`）的事件，依引擎組合查對應的自身表或跨引擎表（含方向性——若曲子把「固定/低音」引擎放到高音端，標成 `UNVALIDATED-DIRECTION` 而非悄悄放行），判定音程是否落在 ±10 cents 的建議窗內。

新作 `scores/originals/rules_v2_demo/rules_v2_demo_001.score.json`：AABA + 尾聲，83.75 秒，cimbalom（和聲，單旋律琶音，root/P5/octave/偶爾 M3，取自 9a 表的 cimbalom 自身局部極小值）、tongue_drum（色彩/節奏，只在每個 section 開場的「匯聚 cell」標記一下，非連續 ostinato）、water_gong（結構標記，匯聚點的八度長音）。動態變化全部套用 M6 §4.6 velocity→dB 表的乾淨倍率（×1.5=+3.5dB、×0.5=−6.0dB）。琶音 onset 間距固定 0.75 秒，超過所有量測音域 T60/3 上限（0.66s）。逐條規則對應寫在 `scores/originals/rules_v2_demo/README.md`（含已知範圍限制的誠實揭露：合規檢查只看宣告時長不模擬殘響延伸、跨引擎表只驗證了固定方向）。

GATE 結果：
- `python tools/consonance.py` → `reports/consonance_tables.md`（可重現）。
- `python tools/check_piece_consonance.py scores/originals/rules_v2_demo/rules_v2_demo_001.score.json` → `reports/rules_v2_demo_consonance_check.md`：**13 個同時發聲音程對，13 PASS，0 VIOLATION，0 UNVALIDATED-DIRECTION**。
- `python tools/verify_score.py scores/originals/rules_v2_demo/rules_v2_demo_001.score.json` → `RESULT: ALL CHECKS PASSED`，exit 0（含 determinism SHA256 一致、rests RMS 通過、peak -0.45dBFS、f0 最大偏差 5.004 cents 在 ±12 容差內）。
- `python tools/verify_score.py --html scores/originals/rules_v2_demo/rules_v2_demo_001.score.json` → `rules_v2_demo_001.report.html`，exit 0。
- 因未改動任何 `src/`，不需 Rule 6 重建；仍重跑 `python tools/physics_verify.py --full`（含 `--amps`）確認零回歸：`RESULT: ALL WITHIN TOLERANCE`。

### 文件同步（本輪）
`ROADMAP_PHYSICS.md`：M9 列由「Not started」改標「Done」，§3 M9 的 9a/9b/9c/9d 四項全部打勾並附證據，GATE 段落更新。

---

## 2026-07-12 — Phase I：M7 容差緊縮轉正（7a/7b/7c）+ M5 5c 溯源 + GATE 收尾

分支 `main`（HEAD 4c77c54 起），未 commit/push，Rule 7。月月 2026-07-11 授權執行 M5-M9，本輪收尾 Phase G（T60）/Phase H（loudness）之後剩下的 M5-5c、M7 全部項目，並跑最終 GATE 存證。

### 7a：f0 容差 ±12 → ±5 cents（全域，無 per-engine 例外）
`tools/physics_verify.py` 的 `F0_TOL_CENTS`（`measure_f0()` 音訊功率質心量測）由 12.0 收緊為 **5.0**。`--full` 全量重測（6 引擎×6 notes note-range scan + 9 材質×3 modal 引擎 material scan）在新容差下全綠，最大 |cents| 僅 0.880（tongue_drum, wood_maple），其餘幾乎全部 <0.1 cents，margin ≥4 cents。detuning 縮放實驗（cimbalom/piano，5/20/40 cents）確認多弦拍頻對質心的偏移確實隨 detuning 縮放（0.003→0.044→0.199 cents），但出廠預設值遠低於門檻，故未建 per-engine 例外字典。`verify_score.py` 的 `MODE_F0_TOL_CENTS`（量測的是 `--dump-modes` 的 string-0 原始值，非聲學質心，是不同的量）**刻意未跟進收緊**，留在 12.0——3 首含多弦引擎的真實曲目量得 5.002–5.013 cents，收緊到 5 會誤殺；已登記 `TODO.md` 待月月裁決是否授權改寫 `check_modes()` 的量測邏輯。

### 7b + 7c：三個模態特徵值表文獻溯源（comment-only）
新增 `docs/EIGENVALUE_SOURCES.md`，逐一核對：
- `BEAM_BETAL`（自由樑）：`cosh(x)cos(x)=1` 解析根，`scipy.optimize.brentq` 獨立數值重解，5/5 全部匹配。
- `PLATE_OMEGA`（clamped 圓板）：Leissa *Vibration of Plates* NASA SP-160 Table 2.1（直接從 NASA NTRS 原始來源取得，OCR 不可靠改用表格截圖人工核對數字）+ 獨立解 clamped-plate 特徵方程（`mpmath` 30 位精度），12/12 匹配，最大誤差 0.03%。
- `PLATE_FREE_OMEGA`（free-edge 圓板）：Table 2.5，7 項中 6 項與表格數字位元完全相同；**發現 1 項不符**：`(m=4,n=0)` 程式碼是 21.83f，但 Table 2.5 本身（腳註「±2% 近似」）給 21.6，本任務從第一原理獨立重解精確特徵方程給 21.527——兩者都與 21.83 差距超過 1%（1.06%/1.4%），方向一致，像是真的抄錄誤植。**本輪未修改此數值**（改動會影響渲染音訊，需要月月同意 + 規則 10 前後對照報告），已寫成提案，登記 `TODO.md`。
`src/physics/BeamModel.h`、`src/physics/PlateModel.h`、`tools/physics_verify.py` 三處僅加註解（來源引用 + 上述差異提案），**未改任何數值**——確認方式：`git diff` 檢視三個檔案，所有 `-`/`+` 行都在註解區塊內，唯一的數值變動是 `F0_TOL_CENTS`（12.0→5.0，屬 7a 範圍）與 `T60_RATIO_TOLERANCE`（Phase G 已做）。因 `src/` 標頭有改動（雖然只是註解），依規則 6 重建 3 個 target（`TsukiSynth_Standalone`／`TsukiSynthCLI`／`TsukiSynth_VST3`），皆 `cmake --build` exit 0。

### 5c 補做：`materials.json` 阻尼常數溯源文件
新增 `docs/MATERIALS_SOURCES.md`：`density`/`youngs_modulus`/`poisson_ratio` 對照標準工程手冊範圍，14 種材質幾乎全部落在合理區間內（標「文獻」），但發現 `rubber.youngs_modulus = 1.5e9 Pa` 比真實橡膠（~1e6-1e7 Pa）硬 100-1000 倍，疑似為了模態求解器數值穩定性刻意選值，登記月月決策清單。`damping.alpha`/`beta_air`/`gamma_radiation`（14 材質 × 3 常數 = 42 個數字）**全部標「待溯源」**——找不到任何specific 出處，只能從 Rayleigh 型阻尼模型（Fletcher & Rossing）與已知材質阻尼量級排序（鑄鐵≫鋼/鋁、橡膠/尼龍≫金屬）做方向性合理性檢查；其中 `wood_spruce.damping.alpha = 8.0` 是四種木料中最高，但雲杉在聲學文獻中以「低阻尼、高 Q」聞名（因此是標準音板木料），現有排序（雲杉>橡木>樺木>楓木）方向看起來反了，同樣登記月月決策清單（改動屬 Rule 10 範圍，需先裁決是否為刻意選值）。**沒有任何 `materials.json`／`MaterialDB.h` 數值被更動**——這份文件本身即是 5c 任務要求的「標不出來的列入待溯源清單給月月」的交付物。

### GATE 結果（本輪最終存證）
- `python tools/physics_verify.py --full` → `reports/gate_outputs/phase_g_gate_full.txt`，`RESULT: ALL WITHIN TOLERANCE`，exit 0（f0 5.0 cents + T60 邏輯不變下的 1b/1c/1d/2d 全過）。
- `python tools/physics_verify.py --t60 --notes 60 72` → `reports/gate_outputs/phase_g_gate_t60_final.txt`，`RESULT: ALL WITHIN TOLERANCE`，exit 0（T60 比值 0.5-2.0 判定制下全 5 modal 引擎 MIDI 60/72 皆 1.00-1.28）。
- `python tools/physics_verify.py --amps` → `reports/gate_outputs/phase_g_gate_amps_confirm.txt`，`RESULT: ALL WITHIN TOLERANCE`，exit 0（M2 振幅判定快速確認，零回歸）。
- 音訊變動檢查：重新渲染 `scores/examples/akashic_bell.score.json`，SHA256 `7ba03dbc00e559775dcb63e1a47da98f9e0df910f194252a16e7c8bef009c522`，與既有歸檔雜湊**完全相同**——本輪 comment-only + 容差調整不改變任何渲染音訊，不需規則 10 前後對照報告。
- `verify_score.py` 回歸（3 首跨引擎曲目 + moonlight 豁免案例）：`moonlight_sonata_complete.score.json`（exit 0，1 個登記豁免）、`water_gong_free.score.json`（exit 0）、`ai_radiance_m1.score.json`（exit 0）全部通過。
- 三個 build target（CLI／Standalone／VST3）皆 `cmake --build` exit 0（Rule 6）。

### 文件同步（本輪，Phase I）
`ROADMAP_PHYSICS.md`：M5 列由「In progress」改標「Done」（5a/5b/5c 全部打勾，5c 附 `docs/MATERIALS_SOURCES.md` 證據）；M7 列由「In progress」改標「Done」（7a/7b/7c 全部打勾，7c 附討論中的 free-edge 差異提案）；§2 總覽表同步；§6 容差登記表 f0/T60 現值欄的 GATE 證據路徑補上本輪最終存證檔名。`TODO.md` 新增：materials.json 兩項待決（rubber E、wood_spruce alpha 排序）、PlateModel free-edge (4,0) 特徵值提案，皆登記月月決策清單。

---

## 2026-07-12 — Phase H：M6 響度物理語意（6a + 6c），GATE 全過

分支 `main`（HEAD 4c77c54 起），未 commit/push，Rule 7。月月 2026-07-11 授權執行 M5-M9。

### 6a：velocity → 響度 dB 文件化（comment-only，Rule 6 適用）
velocity 律本身早已存在且已由 M1-1d 機器驗證（`ModalResonator::excite()`：`currentAmp = baseAmp * velocity`，線性），本輪只補文件與程式碼註解，**不改任何邏輯**：
- `docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` 新增 §4.6「velocity 數字對照響度 dB 表」（聾人讀者向：velocity ×2 = +6.0 dB 換算表 + 機器驗證出處），並在 §12.1 補一段響度數字（LUFS/逐段 RMS）的說明。
- `src/score/ScoreParser.h`：在 `velocity` 欄位宣告與其解析處各加一段註解區塊，說明線性律、`+6.0206 dB` 推導、與 `physics_verify.py` M1-1d 判定的對應關係，並指回文件 §4.6。**純註解，無邏輯變動**。
- Rule 6 重驗：`cmake --build build --config Release --target TsukiSynthCLI` exit 0（`RenderApp.cpp` 因 include 到 `ScoreParser.h` 而重新編譯，純註解變動下建置成功，佐證沒有語法/邏輯破壞）。

### 6c：`verify_score.py` 加整曲 LUFS + 逐樂句 RMS
新增 `tools/loudness.py`（第三方共用模組，避免 `verify_score.py` ↔ `report_html.py` 循環 import，做法同 `report_html.py` 自己的模組註解說明的理由）：
- ITU-R BS.1770-4 Annex 1 K-weighting：以標準公佈的類比原型參數（stage 1 shelf f0=1681.974… Hz/G=3.9998…dB/Q=0.70718…；stage 2 RLB high-pass f0=38.135…Hz/Q=0.50033…）+ 雙線性轉換，在任意取樣率算出 biquad 係數（不是只硬編 48kHz 數字）；於 48kHz 與標準公佈的字面係數表交叉核對，誤差 <1.1e-12（`stage1`）/ <3e-14（`stage2`）。
- 400ms block、75% overlap（100ms hop）、絕對門檻 -70 LUFS、相對門檻（絕對門檻通過後平均值 -10 LU）兩級 gating，完整依標準的 mean-square → gate → mean-square → dB 流程實作。
- **強制自我測試**（`python tools/loudness.py` 或 `verify_score.py --selftest-lufs` 隱藏旗標）：997Hz 全幅正弦量得 **-3.0103 LUFS**（目標 -3.01 ± 0.1）；-18dBFS 997Hz 正弦量得 **-21.0103 LUFS**（目標 -21.01 ± 0.1）。兩者皆過。
- 整合進 `verify_score.py`：`measured["lufs_integrated"]`（純資訊行，§6 未登記 LUFS 容差，不影響 exit code）與 `measured["_phrase_rms"]`（`loudness.compute_segment_rms_table()`：有 `phrases` 欄位就逐樂句量 RMS dBFS，沒有就退回合併後的事件發聲時間軸分段量測——與 `report_html.py` 樂句時間軸的 fallback 邏輯一致）。Console 輸出新增一行整曲 LUFS + 逐段 RMS 明細表。
- `report_html.py`：banner-stats 行加整曲 LUFS 數字；樂句時間軸（section 5）在真的有 `phrases` 欄位時，每個樂句色塊加 RMS dBFS（hover title + 夠寬時的可見文字標籤，遵守本模組「每個品質主張必須是視覺化數字」的既有規則），merged-activity fallback 分支維持不變。

### GATE 結果
- `python tools/loudness.py`（自我測試）→ `RESULT: PASS`（997Hz 全幅 -3.0103 LUFS，-18dBFS -21.0103 LUFS）。
- `python tools/physics_verify.py --full` → `RESULT: ALL WITHIN TOLERANCE`，exit 0（確認 6a 的純註解改動零回歸）。
- `python tools/verify_score.py --html scores/originals/ai_radiance/ai_radiance_m1.score.json` → exit 0，`RESULT: ALL CHECKS PASSED`；HTML 報告新增欄位程式化驗證：banner-stats 含整曲 LUFS 數字、25 個樂句色塊皆含 RMS dBFS（title tooltip 全部命中，9 個夠寬色塊有可見文字標籤）、0 個 `http(s)://` 外部參照、3 個 `<svg>` 皆合法 XML。
- `python tools/verify_score.py --html scores/examples/water_gong_clamped.score.json`（無 `phrases` 欄位，走 fallback）→ exit 0，console 印出 1 個 merged-activity 分段 RMS，HTML 報告不受影響。
- 三個 build target（CLI / Standalone / VST3）皆 `cmake --build` exit 0（Rule 6）。

### 文件同步（本輪，Phase H）
`ROADMAP_PHYSICS.md`：M6 列 6a/6b/6c 打勾、狀態改「Done」；§2 總覽表同步更新。

---

## 2026-07-12 — Phase G：M5 T60 驗證轉正（5a+5b），GATE 全過

分支 `main`（HEAD 4c77c54 起），未 commit/push，僅動 `tools/physics_verify.py`（無 `src/` 改動，Rule 6 免重建）。

### 5a：量測改進
`tools/physics_verify.py` 的 `--t60`：探針從 3s 加長到 5s（`T60_PROBE_DUR`）；基頻隔離從舊版寬帶 ±20%（`f0*0.8~1.2`）改成以「量測到」的 f0（`measure_f0()` centroid，非 MIDI 名目頻率）為中心的 ±3% 窄頻帶（4th-order zero-phase `sosfiltfilt` 帶通）；多弦課引擎（cimbalom 與 piano——兩者都走 `renderCimbalom()`，預設 3 弦 `detuningCents=5`）在對 log-envelope 做線性回歸前，先用「≥1 個拍頻週期」的滑動平均（`fundamental_beat_freq_hz()` 讀 `--dump-modes` 的 `strings` 陣列取最快/最慢弦的差，模型自身真值，非循環論證）拉平拍頻造成的包絡起伏；回歸擬合窗於 attack 後 100ms 起，到 note-off 前 0.3s／-60dB 點／noise-floor+10dB（floor 取自實際渲染 buffer 尾段的雜訊 RMS）三者最早發生者為止，取代舊版固定 `-3~-28dB, t<1.5s` 窗。單弦引擎（tongue_drum/water_gong/water_gong_free，`ChromaticVoice`）不受影響。

### 5b：容差收緊
修法前（舊版寬帶量測）：cimbalom/piano 於 MIDI 60 ratio 僅 0.41（跌出舊 0.2–5.0 容差邊緣都危險），暴露出舊寬帶量測混進了拍頻造成的假快衰減。5a 改法後，MIDI 60 與 72 全 5 個 modal 引擎 ratio 收斂到 1.00–1.28（單弦引擎精確 1.00；cimbalom/piano 因拍頻平均後仍有 1.16–1.28 的殘餘偏差，判定 PASS），跑兩次結果位元相同（determinism，`diff` 零差異）。`T60_RATIO_TOLERANCE` 由 (0.2, 5.0) 收緊至 **(0.5, 2.0)**，`--t60` 現為 exit-code-affecting（判定制，與 `--full`/`--amps` 同等對待）。**5c（`materials.json` 阻尼常數溯源）未做**，留待後續。

### GATE 結果
`python tools/physics_verify.py --t60 --notes 60 72` → `RESULT: ALL WITHIN TOLERANCE`，exit 0。輸出存檔 `reports/gate_outputs/phase_g_gate_t60.txt`。`--full`（未改動邏輯）重跑子集確認零回歸。

### 文件同步（本輪，Phase G）
`ROADMAP_PHYSICS.md`：M5 列改標「In progress」+ 5a/5b 打勾附證據、5c 維持未勾；§6 容差登記表 T60 現值欄由「0.2–5.0（informational）」改為「0.5–2.0（判定制，M5 已達成）」。

---

## 2026-07-11 — Phase F：M4 視覺驗證報告 4a/4b 完工 + pluginval L10 全過 + README 措辭審查

分支 `main`（HEAD 64e2836 起），未 commit/push，§6 容差未動，Rule 7（不 commit/push）。

### M4：`tools/report_html.py` 新增，`verify_score.py --html` 從 placeholder 變真實作
新增純函式模組 `tools/report_html.py`，不重新判定 PASS/FAIL，只把 `verify_score.py` 已算出的 `Check` 物件與已渲染音訊畫成 6 個區塊（總結徽章／頻譜圖／f0 預測-實測對照／響度曲線＋休止驗證／樂句休止時間軸／頁尾）。頻譜圖用純 stdlib（`zlib`+`struct`）手刻 PNG encoder，內嵌為 `data:image/png;base64,...`，全程無 PIL/matplotlib、無外部網路依賴。對 `scores/examples/water_gong_clamped.score.json`（110.8 KB 輸出）與 `scores/originals/ai_radiance/ai_radiance_m1.score.json`（483–498 KB 輸出）皆 GATE exit 0。

過程中修正一個真實測量 bug：f0 對照圖初版對 `ai_radiance_m1` 事件 #56（69.3 Hz 低音 water_gong）算出 +75.43 cents 的假數字——根因是拋物線峰值內插在搜尋頻段（±3%）邊界外插了頻段外的鄰近 bin；已在 `measure_event_f0()` 加上邊界檢查，峰值落在頻段邊界時誠實標示「無法量測」而非外推假數字。

獨立驗證（另一名 worker，非本人）另外發現並修補一個無障礙缺口：`verify_one()` 早就把整曲 duration/peak_dbfs/rms_dbfs 算進 `measured` dict，但 `report_html.py` 從未把這些數字顯示成聾人讀者看得到的文字（只有 PASS/FAIL 徽章）——違反本模組自己宣告的「每個品質主張必須是視覺化、數字化，不能是『聽起來』」規則。已在 `render_badges_section()` 加一行 `.banner-stats`（duration/peak dBFS/RMS dBFS），重跑兩份報告的 GATE 仍 exit 0。

**GATE 全過**：`python tools/verify_score.py --html scores/examples/water_gong_clamped.score.json` 與對 `ai_radiance_m1.score.json` 皆 exit 0，含全部 6 區塊；程式化驗證 0 個 `http(s)://` 外部參照，PNG CRC32/IDAT 長度正確，3 個 `<svg>` 區塊皆合法 XML。**4c（月月本人瀏覽器目視驗收版面可讀性）未完成**——這是月月的眼睛，AI 不能代為勾選，M4 因此維持 In progress（Rule 5）。

### M8-8a（部分）：pluginval 自動化驗證，L5 + L10 全過
下載 pluginval 1.0.4（JUCE v8.0.3）到 scratchpad，對已建好的 `build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3` 分別跑 `--strictness-level 5` 與最高等級 `--strictness-level 10`，兩次皆 `SUCCESS`、process exit code 0。L10 額外涵蓋非釋放連續處理、state 存讀、Parameters/Background-thread/Parameter-thread-safety/Fuzz-parameters 測試。兩份 log（`reports/gate_outputs/pluginval_L5.txt` / `pluginval_L10.txt`）grep `warn|error|fail|assert`（不分大小寫）零匹配。**這只涵蓋自動化可測部分**，Cubase 內 host 掃描辨識／MIDI in 手動彈奏／GUI automation lane 手畫曲線回放／專案存檔關閉重開的 state round-trip 仍需月月人工在自己的 Cubase 操作，清單已寫進 `TODO.md`。

### M8-8b：核實 `master`/`Codex-fix-bug` 分支現況
`git branch -a` 確認 repo 目前只有 `main`（+ `remotes/origin/HEAD`、`remotes/origin/main`），沒有獨立 `master` 分支，也沒有 `Codex-fix-bug` 分支（本地或遠端皆無）——早前的 `Codex-fix-bug` 工作已在某次月月授權的 push 併入 `main`。「merge Codex-fix-bug → master」字面待辦已 moot，8b 剩下的只是「本輪 Phase F 尚未 push 的變更何時 push」交給月月裁決。

### M8-8c：README 驗證域措辭審查
逐句核對 README.md 對外主張是否符合 `ROADMAP_PHYSICS.md` §0 驗證域表：把未加範圍限定的「精確模擬音色」改成明確排除 FM Piano 與 Effect Chain 的敘述；新增「Physical Verification」章節，摘要域內/半域內/域外分類並直接引用 §6 容差數字（±12 cents、±3.0 dB、+6.0±1.0 dB、≤-50 dBFS、SHA256 determinism）與 GATE 證據路徑；三個引擎小節標題與 Effect Chain 小節標題各補上域內/域外標註。**未改任何 §6 數字**（Rule 2），只是把既有數字如實引用進使用者文件。

### GATE 結果彙總
`tools/report_html.py`（新）+ `tools/verify_score.py --html` GATE：兩份報告 exit 0，6 區塊齊全，0 個外部網路參照。pluginval L5/L10：兩次 SUCCESS/exit 0，0 個 warn/error/fail 字樣。`git branch -a`：確認分支現況（見上）。三者皆為既有唯讀查驗或純新增程式碼，未動任何 `src/`、`uiux/`、score JSON，§6 容差全程未動。

### 文件同步（本輪，Phase F）
`ROADMAP_PHYSICS.md`：M4 列改標「In progress」+ 4a/4b 打勾附證據、4c 維持未勾；M8 列改標「In progress」+ 8a 部分打勾（pluginval 證據）、8b 現況核實補述（分支不存在，moot）、8c 打勾（README 已改）。`TODO.md`：新增月月待辦清單（4c 視覺驗收步驟、Cubase 人工檢查清單、push 時機）。

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
