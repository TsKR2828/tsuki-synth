# TsukiSynth — Current TODO

> Last updated: 2026-08-02
> Branch: `fix/deep-physics-audit-20260716`

The deep-audit implementation fixes are on the branch. Historical Phase D–I decisions remain in `DEVLOG.md`; this file lists only current work and scientific gaps.

## 2026-08-02 audit follow-up

- [x] T60 final judgment now requires both the 0.80–1.25 measured/model ratio and at least 8.0 dB of fitted decay; insufficient span fails closed after the 30 s retry. Regression tests include the former false-pass counterexample.
- [x] Render manifest v4 binds WAV, renderer, root score and every recursive layer dependency, plus a canonical dependency-tree SHA256. Layer mutation and legacy-v3 layered false-provenance cases are regression-tested.
- [x] Tuner status/support/label text now uses the higher-contrast `textMid` colour and at least 9 pt base size.
- [x] README/roadmap/playbook wording now distinguishes implementation conformance from external physical validation and reflects the 5-cent course-centroid gate.
- [x] Rebuilt CLI, VST3, Standalone and all three C++ test targets in Release; CTest 3/3, Python 84/84, ASan 3/3, fresh-build `physics_verify.py --full`, pluginval L10 and Steinberg validator 47/47 all pass.
- [x] New 73-score corpus run completed in deterministic round-robin shards: 19/19 + 18/18 + 18/18 + 18/18 = 73/73, 0 fail; the one existing moonlight FX-art exemption remains explicit.
- [x] Added Specimen Measurement v1 schema, hashed evidence-chain verifier and laboratory protocol. Frequency/relative magnitude/T60 are comparable now; unsupported phase/SPL/radiation claims fail closed as `UNVERIFIED`.
- [x] Added the non-human Specimen Measurement v2 pipeline: repeated synchronized CSV → calibrator-derived V/Pa → complex H1/coherence/phase/T60/Pa-per-N/SPL/directivity → uncertainty, hashes, self-contained bundle and report. All v2 comparators are implemented; current synth phase/absolute-radiation model observables correctly remain `UNVERIFIED` until the physical model emits them.

Acceptance snapshot (round-1, 2026-07-17): six Release targets build; CTest and Python contract/metrology tests pass;
schema 80/80; release corpus 73/73 with one existing visible FX-art exemption; event-specific
rules demo 13/13 PASS; `physics_verify.py --full` has no checked failures and three explicit
rubber `UNVERIFIED/N/A` cases.

Round-2 snapshot (2026-07-18, `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md`): six Release targets rebuild
clean; ctest 3/3, pytest 44/44, tuner oracle, schema 80/80 and consonance gates all PASS. `physics_verify.py
--full` has one **honest FAIL** (piano MIDI 60 velocity vs the +6.0206 dB physical-law bound — see pending
decisions). Corpus per-channel rest-RMS re-measurement gives 71/73 net PASS: 2 new honest FAILs
(`summer_m2`/`summer_m3` rest RMS, both traced to a reverb tail, neither exempted) surfaced by the
stricter measurement, not by any audio regression. No §6 tolerance was widened; no new exemption was
registered.

Round-3 snapshot (2026-07-22, `reports/gate_outputs/deepfix3_*.txt`): fixed both round-2 honest FAILs.
Velocity: `physics_verify.py`'s F3 measurement domain moved from wideband RMS to the fundamental's own
±3% band (matching the law's per-mode physical scope; wideband delta is now printed informational-only) —
all 5 modal engines now PASS at MIDI 60, incl. piano (+6.6702 dB, dev +0.65); `--full --skip-amps` is green.
Summer: `reverb.decay` narrowed on both files (wet untouched) — `summer_m2` 2.8→2.6 (2.6 dB worst-case
margin), `summer_m3` 1.2→1.0 (2.5 dB margin); both re-verified PASS incl. determinism SHA256 match. Stale
`rules_v2_demo_001.report.html` (predating its score.json's 2026-07-17 edit) regenerated and re-checked.
No §6 tolerance widened; no new exemption registered; both score edits and the measurement-domain change
awaited 月月's sign-off (musical effect / domain-change ratification respectively) — **ratified 2026-07-23,
see "2026-07-23 round-4 裁決落地" below.**

## 2026-08-06 月月審聽/驗收裁決落地

- [x] **Rule 10 審聽回饋**：全體音色低音偏大、高音偏小（機制＝Phase H 阻尼物理化 + round-2 T60 語意修正疊加，`phase_h_before_after.md` §3 有記錄）。裁決：**短期亮度補償層 + 長期頻變阻尼兩個都做**。短期已落地：`global.effects.eq.{high_shelf_freq_hz, high_shelf_gain_db}`（RBJ 高頻 shelf，documented creative 層、不入物理主張；gain 0 = 硬 bypass，既有 corpus 渲染位元不變——`akashic_opening_bell_001` SHA256 前後一致驗證過；+6dB 實測 3k-12k 帶 +5.67 dB、低頻帶 +0.01 dB）。plugin 端同步 `fx_eq_freq`/`fx_eq_gain` + BRIGHTNESS 面板。長期線見「Verification gaps」阻尼寬頻化條目。
- [x] **M4-4c 首輪驗收回饋**：報告看不出用途（預設讀者懂管線）。已修：`report_html.py` 頁首加「這一頁是什麼？」導讀卡 + 六個區塊各加一行「💬 白話」說明；`ai_radiance_m1.report.html` 已重產，**2026-08-15 月月目視驗收通過 → M4 三項齊備轉 Done**（`ROADMAP_PHYSICS.md` §2 M4 列與 §3 M4-4c 已同步）。
- [x] **M4-4c 二輪回饋「報告像隱藏功能、Standalone 應可當獨立工具」**：`src/ScoreConsole.h` Score 控制台（`c0615fa`）——Standalone 頂列 [Score] 鈕，一鍵渲染 score.json（子程序呼叫同捆 `TsukiSynthCLI.exe`，渲染合約單一來源；輸出 `桌面\TsukiSynth_Renders`）＋開資料夾／開報告／python 產報告。發佈包自此同捆 CLI。**待月月實際操作驗收**。

## 2026-08-06（夜）跨音域響度失衡修正（unstaged 待審）

- [x] **激發端根因修正**（同題第三線，與亮度 EQ 應急線／阻尼寬頻化長期線並行）：
  τc keytrack（`HammerImpulse::tauCForNote`，文獻擬合 f^-0.32）+ noteOn 攻擊能量
  正規化（`ModalResonator::loudnessCompensationGain`，amount=0.78 月月審聽定案，
  已文件化校準層、比照 spectralTilt 劃界）。C2~C7 掃音 spread：Cimbalom 27.3→8.65、
  TongueDrum 29.7→8.13、WaterGong 36.3→8.35 dB；C2 削波消除。`--full` 第一輪
  抓到 velocity 次線性（tongue_drum +4.72 dB 違 F3 律）→ 能量預估改用 velocity=0.5
  Hertz 錨 τc 修正，全綠 `NO CHECKED FAILURES`；ctest 3/3 + pytest 121/121 +
  三 target rebuild 綠。Rule 10 報告：`reports/loudness_keytrack_before_after.md`。
- [x] **corpus 73 檔重驗**——**73/73 全 PASS、0 FAIL、零新增豁免**（A 19/19 +
  B 18/18 + C 18/18 + D 18/18，僅既有 moonlight 豁免保持可見）；邊際檔
  summer_m2/m3 rest RMS 皆過（低音變小聲反而擴大邊際）。存證：
  `reports/gate_outputs/loudnessfix_corpus_{A..D}.txt`。
- [ ] **亮度 EQ 應急層去留覆核**——激發端修正落地後，既有 `global.effects.eq`
  高頻 shelf 的補償需求可能已部分消失，月月審聽後決定是否調整建議值/文件。

## 月月待裁決（pending decisions）

- [x] **`verify_score.py` 的 `MODE_F0_TOL_CENTS = 12.0` 是否授權改量測法後收緊**——**2026-07-23 裁決：授權**，改為 course 質心／平均量測法後收緊至 5.0；程式改動（`check_modes()`）由另一輪工作平行進行中，尚待該輪 GATE 存證（見「2026-07-23 round-4 裁決落地」）。
- [x] **殘差頻譜能量檢查：門檻轉判定制的批准**——**2026-07-23 裁決：批准**，轉判定制、門檻取 -60.0 dB re total（依據 round-2/round-3 累計實測基線 -74.7~-83.1 dB re total，留有 ≥14.7 dB 邊際）；程式改動（`tools/physics_verify.py`）由另一輪工作平行進行中，尚待該輪 GATE 存證。
- [x] **spectralTilt heuristic 層去留**——**2026-07-23 裁決：降級保留**，聲音不動，劃界為已文件化 creative 層（不算入物理主張），已同步 `ROADMAP_PHYSICS.md` §0 與 `README.md` 域表註記。
- [x] **【2026-07-18 round-2 → 2026-07-22 round-3 已修正】piano velocity 物理律「違規」**——量測域變更（寬帶→基頻窄帶）**2026-07-23 裁決：追認**，已同步 `ROADMAP_PHYSICS.md` §6 velocity 列依據欄。詳見 `DEVLOG.md` 2026-07-22 條目、`reports/gate_outputs/deepfix3_selftest.txt`／`deepfix3_gate_full.txt`。
- [x] **【2026-07-18 round-2 → 2026-07-22 round-3 已修】corpus 逐聲道 RMS 揭露的 2 個既有 rest 超標**——`summer_m2`（decay 2.8→2.6）／`summer_m3`（decay 1.2→1.0，累計 2.1→1.0）的殘響藝術效果**2026-07-23 裁決：接受**。機器 GATE 已於 round-3 過（`verify_score.py` 全項 PASS 含 determinism SHA256 match）。
- [ ] **Rule 10 前後對照報告審閱**——`reports/deep_fix_before_after.md`（2026-07-18 round-2）：8 首代表曲目改動前後 RMS/頻譜質心/T60/f0 比對，`physical_piano` 是唯一變大聲的一首（+2.346 dB），值得月月過目確認方向是否符合預期。**2026-08-15 月月回饋「看了但看不懂」→ 已補 §00 白話導讀**（一句話結論、逐首白話對照表、主因＝τ→T60 重新定義使音尾變 1/6.9、舌鼓泛音整組換掉的說明、哪些數字不可信、決策選項）。待月月讀完白話版後裁決「整批接受」或「指名回退某項」。

## 2026-07-23 round-4 裁決落地

> 月月於對話中對 2026-07-22 round-3 留下的五項待裁決明示「都照推薦的做」。本輪只落地文件記錄，不改 `src/`／`tools/` 程式碼。

- 決議：(1) velocity 量測域（寬帶→基頻窄帶）追認；(2) `summer_m2`/`summer_m3` decay 收斂（2.8→2.6、2.1 累計→1.0）接受；(3) `spectralTilt` 降級保留，劃界為已文件化 creative 層；(4) 殘差頻譜能量轉判定制 -60.0 dB re total；(5) `MODE_F0_TOL_CENTS` 授權改 course 質心量測法後收緊至 5.0。
- 文件同步：`ROADMAP_PHYSICS.md` §0 域表（Cimbalom/Piano 列 spectralTilt 劃界註記）+ §6 容差表（velocity/殘差/f0 三列）；`README.md` Physical Verification 域表同步 spectralTilt 劃界註記；本檔（`TODO.md`）五項裁決逐條關閉；`DEVLOG.md` 新增本輪條目。
- **(4)（殘差判定制 -60.0 dB）與 (5)（f0 course 質心 5.0）的程式碼改動已於同日稍後落地並全 GATE 綠**（文件線寫作當下平行進行中，故上一版此條標「尚未落地」）：`tools/physics_verify.py` `RESIDUAL_ENERGY_LIMIT_DB = -60.0` 判定制生效（5 引擎實測 -74.7~-83.1 dB 全 PASS，selftest 新增未建模強峰反例會 FAIL）；`tools/verify_score.py` `course_f0()` 振幅加權質心 + `MODE_F0_TOL_CENTS = 5.0`（moonlight yangqin 實測 5.013→0.019 cents，證實舊讀數為 string-0 設計偏移非真走音）。GATE 存證：`reports/gate_outputs/deepfix4_selftest.txt`／`deepfix4_gate_full.txt`（`F5 residual energy : PASS`、`RESULT: NO CHECKED FAILURES`）／`deepfix4_pytests.txt`（32+26 測試全過）。
- **corpus 全量重驗（新 f0 質心 + 5c 收緊下）：73/73**——四分片 `deepfix4_corpus_{A,B,C,D}*.txt`：B 12/12、C 21/21、D 22/22 全過；A 分片 18 檔中 `moonlight_sonata_complete` 首跑 determinism 檢查因 CLI 第二次渲染進程啟動失敗（exit 0xC0000142 = STATUS_DLL_INIT_FAILED，高併發環境故障，同 deepfix2 輪 autumn_m1 前例）記 FAIL；**2026-07-23 已單獨重驗：ALL CHECKS PASSED（含既登記 moonlight 豁免）、determinism SHA256 aaaa46e8... 兩次一致，非真回歸，已解除**。其餘 17 檔含 ai_radiance 5 檔全過。豁免仍僅 moonlight 一筆，零新增。
- Rule 1/2/4：本輪未執行任何 git 變更狀態指令，未調寬任何容差（(4)(5) 皆為收緊方向），文件中的新數字（-60.0 dB、5.0 cents）均註明批准依據與日期。

## Before merging this branch

- [x] Review the complete P1–P7 diff; keep it as one atomic physics-hardening commit because production changes, fail-closed contracts, CI gates and their evidence documentation must land together.
- [x] Push the branch and let the updated Windows CI run Python unit tests, CTest, build targets, the event-specific consonance gate and `physics_verify.py --full` — 2026-08-05 push（`aba7f84` specimen 批 + `4cf4817` scene→reverb 批），CI run 31004676104 全步驟綠。
- [ ] Validate VST3 scan, MIDI, automation and state round-trip in the intended DAW.
- [ ] Perform a visual accessibility review of the tuner and generated HTML report with the intended deaf user; automated tests cannot certify readability.

## 2026-07-18 round-2 修復（完成，詳見 `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md`）

> 稽核來源：2026-07-18 本 session 四線審查。GATE 證據路徑規約：`reports/gate_outputs/deepfix2_*.txt`。

- [x] 工具/量測線：`tools/physics_verify.py` — F1 特徵值錨（`CANTILEVER_BETAL`/`free_plate_omegas()`）接回消費點、F2 f0 主錨改回 12-TET ET 理論值、F3 velocity 律上限雙重判定（`6.0206 ± 1.0 dB`）、F5 殘差頻譜能量資訊性檢查、selftest 反例 4a/4b；`tests/test_physics_verify.py` 新增 19 測試，24/24 PASS。
- [x] 引擎/渲染線：`src/score/ScoreRenderer.h`（dumpModes custom-atoms 堆積配置杜絕懸空指標）、`src/engines/CimbalomEngine.h`/`ChromaticEngine.h`（spectralTilt 註解、過期 mix 註解修正）、`src/physics/StringModel.h`/`BeamModel.h`/`PlateModel.h`（velocity 慣例與正規化語意註解）、`src/dsp/NoiseGen.h`（pink 係數標註取樣率相依）、`CMakeLists.txt`（TunerTest target 補齊設定、VERSION 0.2.0→0.3.0）；ctest 3/3 PASS。
- [x] score 資產線：`tools/verify_score.py` 逐聲道 rest RMS（取代 `(L+R)/2` 混降）、`src/cli/RenderApp.cpp` render manifest v2（新增 `wav_sha256`）；`tests/test_verify_score_contract.py` 新增 12 測試，14/14 PASS；probe SHA 基線比對確認 manifest 修改未影響音訊位元。
- [x] 文件/設定線：`.gitignore` binA/binB 字面規則、CI push 分支 `main` + `fix/**`、README 狀態表/目錄/build 依賴、§6 容差登記表同步（月月 2026-07-18 授權，四列：T60/velocity/殘差/休止RMS）——完成。
- [x] 各線 GATE 輸出彙整與零回歸確認：9 項 GATE（rebuild/ctest/selftest/`--full`/tuner oracle/pytest/schema80/consonance/probe SHA）+ 4 分片 corpus + HTML 抽驗全部執行並存證於 `reports/gate_outputs/deepfix2_*.txt`；`--full` 誠實 FAIL 於 piano velocity 物理律（見「月月待裁決」）、corpus 於 `summer_m2`/`summer_m3` 誠實 FAIL（逐聲道量測揭露既有超標，非回歸）；`autumn_m1` determinism 為環境暫時性故障已重驗排除；零 §6 容差放寬、零新增豁免。

## 2026-07-22 round-3 修復（完成，詳見 `DEVLOG.md` 2026-07-22 條目 + `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md` round-3 補記）

> 處理範圍：round-2 遺留的兩項待裁決（piano velocity「違規」、summer m2/m3 rest 超標）。GATE 證據路徑規約：`reports/gate_outputs/deepfix3_*.txt`。

- [x] `tools/physics_verify.py` F3 velocity 量測域修正：寬帶 RMS → 基頻 ±3% 窄帶（`measure_band_rms_db()`/`FUND_BAND_HALF_WIDTH`），判定式數值未動；寬帶 delta 降為資訊性行。5 個 modal 引擎 MIDI 60 velocity 48→96 全數 PASS（見「月月待裁決」量測域追認項）。`tests/test_physics_verify.py` 新增 3 測試，共 47/47 PASS。
- [x] `scores/classical/vivaldi_four_seasons/summer/vivaldi_four_seasons_summer_m2.score.json`（decay 2.8→2.6）、`.../summer_m3.score.json`（decay 1.2→1.0）：休止 RMS 超標修復，`verify_score.py` 全項重驗 PASS 含 determinism SHA256 match；完整掃描見 `reports/gate_outputs/deepfix3_summer_rest_sweep.txt`（藝術效果待月月確認）。
- [x] `scores/originals/rules_v2_demo/rules_v2_demo_001.report.html` 過期重生成（原檔停留在 score.json 2026-07-17 改動前）——已關閉，不再是待辦。
- [x] GATE 彙整：selftest 11/11、pytest 47/47、`--full --skip-amps` PASS（NO CHECKED FAILURES）、summer 兩檔 verify PASS、未觸碰的 `physical_piano.score.json` 回歸抽驗 PASS，全部存證於 `reports/gate_outputs/deepfix3_*.txt`；零 §6 容差放寬、零新增豁免。

## Verification gaps that must stay explicit

- [ ] Obtain citable or measured values for every material's `beta_air` and `gamma_radiation`.
- [ ] Replace single-frequency damping anchors with broadband/specimen measurements and uncertainty intervals. **2026-08-06 月月裁決升級**：Rule 10 審聽確認材質物理化後全體音色「低音變大聲、高音變超小聲」（`phase_h_before_after.md` §3 已記錄的機制——單頻 η 錨高估高頻衰減是主因之一），本項定為該問題的**長期物理修法**；短期先以 `global.effects.eq` 亮度補償 creative 層應急（同日已落地，見下）。
- [ ] Add the synth-side calibrated force → displacement → radiated pressure/SPL model, including pickup/microphone position, signed/complex modal residue and spatial radiation. The v2 measurement pipeline/comparators are complete; this remaining item is specifically the physical prediction model. **2026-08-15 文獻線推進（未實作）**：`docs/EXTERNAL_ANCHOR_SOURCES.md` §1–§3 — 找到**校準到絕對聲壓**的外部量測（樂器指向性資料庫，消音室 32 通道球陣列半徑 1.05 m，**數位振幅 1.0 ≡ 1 Pa ≡ 94 dB**，SOFA/CC BY-SA 4.0），提供了 TsukiSynth 目前完全欠缺的「量測面定義 + 絕對單位慣例」；輻射效率的理論骨架（臨界頻率 `fc = ca²/(2π√(Dx·H))` ≈ 1.8 kHz、波導聲學截止 `fga = ca/(2p)` ≈ 1.3 kHz）可由材質／幾何算出無需新查表常數。**仍缺**：合成端「位移→輻射功率→指定距離 Pa」那一段未實作；相位預測未實作 ⇒ 相位主張維持 `UNVERIFIED`（順序是先實作再比對，不是先找資料）；資料庫**不含**揚琴／舌鼓／鑼，最接近的只有撥弦的吉他／豎琴。
- [ ] Add coupled-body/soundboard/sympathetic-resonance and realistic damper/pedal physics for piano. **2026-08-15 文獻線推進（未實作）**：`docs/BRIDGE_ADMITTANCE_SOURCES.md` — 找到可實作的閉式公式鏈，解決 `damping_broadband_findings.md` §4 指出的「缺頻率無關損耗通道」缺口：無限板驅動點導納 `Y∞ = 1/(8√(D·ρs))`（純實數、與頻率無關；Cremer/Heckl/Ungar + Skudrzyk，與 Ege & Boutillon 的 `Y_C=(1/4h²)√(3(1−ν²)/(Eρ))` 代數等價，已獨立驗算）→ 弦端振幅衰減率 `α=(T/L)·Re Y`（由反射係數推導，與文獻引用形式一致）→ `1/T60_bridge = T·G/(ln(1000)·L)`。量級估算：`G=1.3e-3 s/kg`（Ege & Boutillon 直立鋼琴實測平均）下 C4 得 4.7 s vs Wogram 實測 ≈5.1 s（現行模型 26.9 s）。**只需新增一個參數（共鳴板厚度 h）**。侷限已列：平滑導納抓不到相鄰半音 5:1 落差（那需要第二階段的音板模態模型）、>1.1 kHz 換波導區、丟棄虛部、單極化、揚琴無對應實測。**實作會改所有既有 score 的衰減 → 觸發 Rule 10 + Rule 6 + corpus 重驗，待月月裁決是否開工。**
- [ ] Replace the velocity proxy with a parameterized nonlinear contact solver using hammer mass, compliance and geometry. **2026-08-15 文獻線完成（未實作）**：`docs/HAMMER_CONTACT_SOURCES.md` — 取得槌氈冪律 `F = K·δ^α` 的逐音實測值（C2 `K=4e8, α=2.3`／C4 `4.5e9, 2.5`／C7 `1e12, 3.0`，Hall & Askenfelt 經 Chaigne & Askenfelt）+ 逐音槌質量（C1 12 g → C8 5 g）、弦長／直徑／張力-弦長比／敲擊比（C1–C8 全表，已通過 `f₁` 回推自洽檢查 <0.15%）。**具體發現**：現行 `tauCForStrike()` 的 `τc ∝ v^-0.2` 正好對應 `α=1.5`（純赫茲，金屬對金屬），實測鋼琴氈是 `α=2.3~3.0` ⇒ `v^-0.39~-0.50`，敏感度差約 2 倍；且現行 `f^-0.32` keytrack 與由 `m`/`K`/`α` 推導的相對 τc（C2:C4:C7 = 1.000:0.726:0.451 vs 現行 1.000:0.641:0.330）方向量級一致，證實 8/6 那個擬合抓到的是真物理、只是係數是配的。**風險**：改力度指數會直接撞 §6「velocity ×2 電平」判定（8/6 那輪就因此被 F3 抓到次線性 FAIL），必須連同能量正規化層一起設計；且 K/α 是**鋼琴專屬**，beam/plate 引擎無對應文獻，硬套違反 Rule 4。遲滯（Stulov）參數未取得。
- [ ] Model anisotropic/orthotropic wood, temperature and humidity where those claims are needed. **2026-08-15 文獻線完成（未實作，且建議暫緩）**：`docs/WOOD_ANISOTROPY_SOURCES.md` — 由 USDA Wood Handbook (FPL-GTR-190) Ch.5 取得 24 樹種正交異向彈性比（Table 5–1）、25 樹種 12 個泊松比（Table 5–2）、含水率修正式 Eq. 5–3 `P = P12·(P12/Pg)^((12−M)/(Mp−12))` 與 `Mp` 表（Table 5–13，未列樹種可假設 25）、溫度線性關係與 150 °C 適用上限。西加雲杉 `ET/EL = 0.043` ⇒ 順紋比切向硬 23 倍，等向性近似在板模態頻率上可差 √23 ≈ 4.8 倍。**建議暫緩的理由**：弦是鋼的不咬；Beam/Plate 改正交異向是**模型結構改動**（Kirchhoff 板要換成 `Dx/Dy/Dxy` 異向版）不是換數字；溫濕度目前沒有任何 score 欄位或 UI 暴露環境條件。真正會用到的是**共鳴板**的 `D`（`BRIDGE_ADMITTANCE_SOURCES.md` §2.1），故建議共鳴板耦合先做、本批資料隨之進場。溫度逐項係數表（Table 5–15）未取得。
- [ ] Validate models against external measured recordings or laboratory modal data not generated by TsukiSynth itself. **2026-08-15 盤點完成（未下載任何資料）**：`docs/EXTERNAL_ANCHOR_SOURCES.md` §1／§4 — 絕對錨只有一個候選（§1 的校準指向性資料庫，但**不含揚琴／舌鼓／鑼**，最接近的是撥弦吉他／豎琴；其打擊樂器是定音鼓＝膜，schema 明確拒收，域外）。相對錨（泛音比例／非諧性 B／T60 隨頻率走勢）可用 SNDB／MAPS／BiVib，**但這些資料集不記錄幾何、材質、邊界與張力**，故永遠只能是相對比對、不能升級為 specimen-level 證據。**結論：揚琴／舌鼓／鑼的外部證據仍然是零，只有走 `SPECIMEN_VALIDATION_PROTOCOL` 實體量測一途。** 資料集是否下載、BY-SA 授權與 repo 的相容性待月月裁決。
- [ ] Establish cross-platform numerical reproducibility rules (bit identity where possible, numeric/audio tolerance otherwise). **2026-08-15 工具與 CI 已就位，unstaged，尚未取得跨平台實測**：新增 `tools/crossplatform_verify.py`（`--emit` 各平台渲染 5 首固定探針；`--compare` 以 Windows/MSVC 為參考比對 SHA256、max|Δ| dBFS、Δ RMS re signal、首個相異取樣、頻譜偏差 dB、峰值 bin 音高 cents）+ `.github/workflows/physics.yml` 新增 `cross-platform-emit`（windows-2022 / ubuntu-24.04 / macos-14 三矩陣）與 `cross-platform-compare` 兩個 job。**Rule 2 遵守**：無登記容差時輸出 exit 3 `UNREGISTERED` 只印實測數字、不自行判定 PASS/FAIL，CI 端以 notice 而非紅燈呈現；等月月把數字登記進 `ROADMAP_PHYSICS.md` §6 後才轉為阻斷式 GATE。**本機 GATE 已過**：`--selftest` 11/11（含反例：1 LSB 擾動須測得 −138.47 dBFS、+0.5 dB 增益須測得 0.5 dB 頻譜偏差、+50 cents 位移須測到、判定器對超限必須 FAIL、空容差檔不得靜默 PASS）；同機 emit×2 → `BIT_IDENTICAL` 5/5；注入 1 LSB 反例 → 正確偵測並定位到第 50000 frame；四個 exit code（0/1/2/3）逐一實測正確。**剩下的是月月 push 才能取得的證據**——跨平台實測數字必須等 CI 在 GitHub 上跑過。
- [ ] Add a polyphonic/missing-fundamental tuner mode only if it can refuse ambiguous cases reliably; the current target-aware monophonic detector must not guess.

## Honest N/A cases

- [ ] Design a short-transient estimator for `cimbalom/rubber`, `tongue_drum/rubber` and `water_gong/rubber`. Current T60 is only 14–28 ms, shorter than eight cycles at the probe pitch, so `--full` reports these three cases as `UNVERIFIED/N/A`.

## Deliberately outside the physical claim

- FM Piano, Custom Harmonics' authored ratios, Body macro and the artistic effect chain may remain useful, but must stay labelled non-physical/half-domain.
- Sample/granular layers do not become physical evidence merely because they are reproducible.
