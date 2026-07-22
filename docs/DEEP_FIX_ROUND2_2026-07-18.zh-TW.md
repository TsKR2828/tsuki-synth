# TsukiSynth 深度修復第二輪驗證報告（2026-07-18）

> 分支 `fix/deep-physics-audit-20260716`（延續 2026-07-17 第一輪，同分支未 commit/push，全程 unstaged）。
> 本文件是第一輪 `docs/DEEP_FIX_VERIFICATION_2026-07-17.zh-TW.md` 的延續，不覆蓋其結論。

## 結論

第一輪 deep-audit（2026-07-17）落地後，本輪由四條線並行覆核第一輪成果本身：harness／測量工具、score 資產／manifest、C++ 引擎與文件、docs／CI 設定。覆核發現的不是新的物理模型錯誤，而是**驗證程序本身的缺口**——部分理論錨點在程式碼裡是死碼、部分判定條件退化成「拿模型的輸出驗證模型自己」、立體聲逐聲道量測掩蓋了真實超標。六項修復落地後，GATE 誠實地在 velocity 物理律檢查上抓到一個先前被掩蓋的真實違規（piano MIDI 60），並在 corpus 重跑中因逐聲道量測法多抓到 2 個既有的 rest RMS 超標。這些都是「驗證變嚴格後暴露的既有事實」，不是本輪修復引入的新回歸——沒有任何 §6 容差被放寬，也沒有新增豁免。

## 稽核發現摘要

1. **F1 特徵值錨退化**：`BEAM_BETAL`／`PLATE_OMEGA`／`PLATE_FREE_OMEGA` 等理論特徵值常數定義後從未被任何驗證路徑消費，等於「有理論表、沒人查表」。
2. **F2 f0 主錨退化**：`assess_partial_frequencies` 在 `frequency_mode: "midi"` 下把 dump 出來的頻率當作 f0 主錨，本質是拿模型自己的輸出驗證模型自己，繞過了真正的 12-TET 理論錨點。
3. **F3 velocity 律無上限**：velocity ×2 電平檢查只驗證「render 音訊」與「模型預測」兩者是否互相一致（±1.0 dB），從未驗證模型預測本身是否符合 `20·log10(2) = 6.0206 dB` 這條物理律——兩者互相吻合、但一起偏離物理律的退化情形完全測不出來。
4. **休止 RMS mixdown 遮蔽**：舊版把左右聲道 `(L+R)/2` 混降後再量 RMS，去相關的立體聲殘響尾巴會在混降時互相抵消，讓真實超標的休止區間看起來合格。
5. **render manifest 無音訊雜湊**：manifest 只記錄 peak/gain 等衍生值，無法證明 manifest 與實際寫出的 WAV bytes 一致。
6. **文件／CI 設定漂移**：`.gitignore` 用字元類 `binA]/` 寫法無法匹配實際目錄名 `binA`/`binB`；CI push 分支仍寫 `Codex-fix-bug` 舊分支名；README 部分敘述停留在 v0.2.0。

以上 6 類問題對應四條修復線：harness（1–3）、score 資產（4–5）、C++（部分 3 的死碼消費點在 C++/Python 兩側都有）、docs／設定（6）。

## 修復清單

### 1. harness／測量工具線 —— `tools/physics_verify.py`、`tests/test_physics_verify.py`

- **F1**：新增 `CANTILEVER_BETAL`（`cos·cosh = -1` 解析根）與 `free_plate_omegas()`（用 scipy 從 Kirchhoff 自由板 `M_r=0`／`V_r=0` 特徵行列式第一原理重解，ν 從 `data/materials.json` 讀，與 C++ `PoissonRoots` 表獨立實作）。`scan_eigenvalue_anchors()` 對 `tongue_drum`（cantilever + free_free）、`water_gong`（clamped 8 項）、`water_gong_free`（free-edge ν=0.34 7 項）做頻率比值判定，容差 0.10%（梁／clamped，比照弦 oracle）與 0.50%（free-edge，ν 插值）；已接進 `--full` 與預設 run 模式。
- **F2**：新增 `f0_expected_et`——midi 模式的 f0 主錨改回 `midi_to_hz(midi)`、±5 cents（§6 數值未動）；原本的 dump 預測降級為第二條 conformance 檢查，仍判定但不再是唯一錨點。
- **F3**：`VELOCITY_LAW_DB = 20·log10(2) = 6.0206`（推導式寫入註解），`assess_velocity_delta()` 現要求**雙重判定**：`|predicted − 6.0206| ≤ 1.0` **且** `|measured − predicted| ≤ 1.0`。
- **selftest 反例**：新增 4a（partial3 +6dB 經同一路徑判 FAIL）與 4b（velocity +9dB delta 兩種失敗模式皆 FAIL）。
- **F5 殘差頻譜能量**（資訊性，不影響 exit code）：扣除 30ms exciter 噪聲窗後，量測預測模態帶（±3%）外的殘留能量，dB re total，標明 `[informational, threshold pending approval]`。
- 測試新增 19 項（eigenvalue anchor negative、ET anchor negative、velocity 律四象限、4a/4b、殘差），連同既有共 **24/24 PASS**。

### 2. score 資產／manifest 線 —— `tools/verify_score.py`、`src/cli/RenderApp.cpp`、`tests/test_verify_score_contract.py`

- **逐聲道 rest RMS**：新增 `max_channel_rms_dbfs()`，`check_rests()` 與 `fx_bypass_rest_rms()` 改成對每個休止窗量「最大聲聲道」的 RMS，而非 `(L+R)/2` 混降；`REST_RMS_LIMIT_DBFS = -50.0` 數值未動，這是量測方法修正不是容差修正。
- **render manifest v2**：`writeRenderManifest()` contract 字串升級為 `"TsukiSynth Render Manifest v2"`，新增 `wav_sha256`（用 `juce::SHA256` 對已寫出的 WAV bytes 算的雜湊，open 失敗視為硬錯誤）；`score` 欄位改存相對於 manifest 目錄的路徑。`verify_score.py` 的 manifest 檢查拆成 `check_render_manifest()`：v2 要求 `wav_sha256` 與實際檔案位元組相符；v1 仍明確接受為 legacy（訊息標註「v1 legacy contract」，不是靜默放行）；未知 contract 判 FAIL。
- 新增 12 項合約測試（反相關殘響噪聲逐聲道量測必須 FAIL、manifest v2 match/mismatch/tamper/missing-hash/大小寫不敏感、v1 legacy、未知 contract、event-count mismatch、缺 manifest），連同既有共 **14/14 PASS**。
- Probe baseline：改動前用既有 binary 渲染 `physical_piano.score.json`／`water_gong_clamped.score.json` 存證 SHA256（`180b4267…` / `d1f8b50d…`），GATE 階段重新編譯後再渲染，兩者位元完全相同，證明 manifest 修改沒有動到音訊本身。

### 3. C++ 引擎／文件線 —— `ScoreRenderer.h`、`CimbalomEngine.h`、`ChromaticEngine.h`、`StringModel.h`、`BeamModel.h`、`PlateModel.h`、`NoiseGen.h`、`CMakeLists.txt`

- `ScoreRenderer.h` dumpModes 的 chromatic 分支：把堆疊上的 custom atoms 換成堆積配置的 `VoiceWithCustomAtoms`（atoms + `ChromaticVoice`同一配置），透過 aliasing `shared_ptr` 曝露，讓 atom 生命週期在建構時就覆蓋 voice，杜絕潛在的懸空指標；值與音訊輸出逐位元不變（`testCustomDumpUsesEffectiveParameters` 覆蓋此路徑並通過）。
- `CimbalomEngine.h` 的 `spectralTilt` 啟發式（7.5/4.0/0.2/2.0）補上詳細註解：標明為未溯源的經驗值，影響範圍限定振幅／`--dump-modes`（不影響頻率／衰減），去留待月月裁決。
- `StringModel.h`／`BeamModel.h`／`PlateModel.h`：統一補上 velocity 慣例（等權重、非 1/ω 或 ω 加權，±6 dB/oct）說明；`BeamModel` 的 `norm=2` 標註為顯示尺度正規化（與質量正規化在全域增益內等價，附 Blevins 出處）；`PlateModel` 的 `max|W|=1` 標註為顯示尺度、**非**質量正規化，並解釋兩者不等價。
- `CimbalomEngine.h`／`ChromaticEngine.h` 內過期的「硬編碼 0.5f mix」註解改寫為對應現行 CLI 預設 0.0f 的正確敘述；補上 `dampingOverride` 語意註解（只取代 alpha，`beta_air·f²`／`gamma_rad·f` 仍由材質決定）。
- `NoiseGen.h` 的 Paul Kellett pink 係數標註為 44.1 kHz 設計、取樣率相依、目前引擎均未使用（僅 White 生效）。
- `CMakeLists.txt`：`TsukiSynthTunerTest` 補齊與另兩個測試 target 相同的 `target_compile_definitions`／`target_link_libraries`／設定旗標；`project VERSION 0.2.0 → 0.3.0`。
- 驗證：三個測試 target 全部 Release build 成功，`ctest` **3/3 PASS**。

### 4. docs／設定線 —— `.gitignore`、`.github/workflows/physics.yml`、`README.md`、`TODO.md`、`ROADMAP_PHYSICS.md`

- `.gitignore`：`reports/**/bin[AB]/` 字元類寫法無法匹配實際目錄名，改成兩條字面規則 `reports/**/binA/` + `reports/**/binB/`（`git check-ignore -v` 驗證兩個 6.9MB exe 皆被正確忽略）。
- `physics.yml`：push 觸發分支從 `main` + `Codex-fix-bug` 改為 `main` + `fix/**`。
- `README.md`：DAW host 驗證列重新標註為 v0.2.0 歷史紀錄、待重新人工驗證；目錄樹只引用 `DEVLOG.md`（清除 0 筆 `DEV-LOG.md` 舊參照）；build steps 補上 `pip install -r tools/requirements-physics.txt`。
- `TODO.md`／`ROADMAP_PHYSICS.md`：見下方「文件同步」與 §6 表格說明。

## GATE 逐項結果

| # | 項目 | 結果 | 存證 |
|---|---|---|---|
| 1 | Rebuild（CLI／VST3／Standalone／AuditTest／TunerTest／PhysicsModelsTest, Release） | **PASS** — 六 target 零編譯錯誤 | CLI exe timestamp 2026-07-18 20:28 |
| 2 | `ctest`（audit_repro／tuner_repro／physics_models_repro） | **PASS** — 3/3, exit 0 | `reports/gate_outputs/deepfix2_ctest.txt` |
| 3 | `physics_verify.py --selftest` | **PASS** — 含新反例 `amps_wrong_amplitude_rejected`／`velocity_law_violation_rejected` | `reports/gate_outputs/deepfix2_selftest.txt` |
| 4 | `physics_verify.py --full` | **FAIL（誠實，預期內）** — exit 1，唯一紅燈見下 | `reports/gate_outputs/deepfix2_gate_full.txt` |
| 5 | `tuner_audit.py` + `tuner_audit_v2.py` | **PASS** — v1 9 checks／v2 14 checks 0 failure，獨立 oracle 最差誤差 0.2076 cents | `reports/gate_outputs/deepfix2_tuner_oracle.txt` |
| 6 | `unittest test_physics_verify + test_consonance_contract + test_verify_score_contract` | **PASS** — 44 tests OK | `reports/gate_outputs/deepfix2_pytests.txt` |
| 7 | Schema layer（80 個 tracked `.score.json`） | **PASS** — 80 [OK]／0 [FAIL] | `reports/gate_outputs/deepfix2_schema80.txt` |
| 8 | `consonance.py` + `check_piece_consonance.py`（rules_v2_demo_001） | **PASS** — 13 pairs 13 PASS 0 not-PASS | `reports/gate_outputs/deepfix2_consonance.txt` |
| 9 | Probe SHA 比對 | **match** — `physical_piano.wav`／`water_gong_clamped.wav` 重新渲染後與改動前基線位元相同 | GATE 階段回報 |

第 7 項備註：`verify_score.py` 沒有純 schema-only 的 CLI 模式（所有模式都會渲染音訊），此 GATE 依指示用 scratchpad 驅動腳本原封不動呼叫 `verify_score.check_schema()`，方法記錄在存證檔標頭。

### `--full` 的唯一紅燈：piano velocity 物理律違規

```
piano MIDI 60: rms_lo -45.5 / rms_hi -38.1 dBFS
render delta   = +7.4  dB
model delta    = +7.4373 dB
violates 6.0206 ± 1.0 dB (F3 physical-law bound) by +1.4167 dB
```

Render 與模型互相吻合（+7.4367 vs +7.4373，舊版「dump 自我一致」判定會照樣綠燈）——這正是新檢查要抓的退化情形：兩者一起偏離物理律。機制指向 deep-audit 新增的 velocity 相依槌接觸時間（高速→接觸時間短→頻譜變亮→RMS 額外增益疊加在振幅律之上）。其餘 4 個 modal 引擎皆 PASS：cimbalom +6.2621 dB、tongue_drum +7.0086 dB（**margin 僅 0.012 dB，逼近上限，一併提請月月留意**）、water_gong +6.2905 dB、water_gong_free +6.3739 dB。fm 引擎依設計豁免（域外）。§6 容差**未放寬**，未登記新豁免。待月月裁決：修 C++ velocity→接觸時間耦合，或月月本人修訂 §6 判定式。

`--full` 其餘子結果：F1 eigenvalue anchors 全 PASS；1b note-range ET 錨最大偏差 0.031 cents（vs ±5.0）；1c 材質敏感度：可量測案例全 PASS，3 個既有 rubber 案例維持 `UNVERIFIED/N/A`（T60 14–28ms，低於 8 週期所需的 31ms 探針地板，非新問題）；2d 振幅判定全 PASS；5b 測得 T60 比值 0.99–1.00；F5 殘差能量純資訊性，`-74.7`～`-83.1 dB re total`，門檻轉判定制待批准。

## Corpus 全量重跑

四分片並行 + 2 個 HTML 報告抽驗，範圍涵蓋全部 73 個 repository score：

| Shard | 範圍 | 結果 | 存證 |
|---|---|---|---|
| A_examples_airadiance | `scores/examples/*` (13) + `scores/originals/ai_radiance/*` (5) | **18/18 PASS** | `reports/gate_outputs/deepfix2_corpus_A_examples_airadiance.txt` |
| B_classical | Vivaldi 四季 12 首 | **9 PASS／3 FAIL**（見下） | `reports/gate_outputs/deepfix2_corpus_B_classical.txt` |
| C_library_1 | akashic 8 + clockwork 7 + forest 前 6 | **21/21 PASS** | `reports/gate_outputs/deepfix2_corpus_C_library_1.txt` |
| D_library_2 | forest_ui_001 + ocean 7 + rabbit 7 + restraint 7 | **22/22 PASS** | `reports/gate_outputs/deepfix2_corpus_D_library_2.txt` |
| html | `water_gong_clamped.report.html`／`ai_radiance_m1.report.html` | **2/2 PASS**（重新生成，六區塊齊全、0 外部參照） | 無獨立存檔，結果記於本文件 |

**Shard A**：moonlight_sonata_complete 的既有登記豁免（`rests.rms_below_limit`）依原樣觸發——rest 316.52–316.80s 實測 -26.6 dBFS（門檻 -50.0），FX-bypass 同窗 -120.0 dBFS 確認是殘響尾巴非模型衰減；豁免登記於 `scores/verify_exemptions.json`（2026-07-07 核准），本輪未新增未修改。逐聲道量測下本分片沒有新增 FAIL。

**Shard B 的 3 個 FAIL（逐一根因）**：

1. `vivaldi_four_seasons_summer_m2.score.json` — `rests.rms_below_limit`：rest 20.65–21.33s 實測 **-49.9 dBFS**（門檻 -50.0，超標 0.1 dB，2/3 休止窗超標）；FX-bypass 同窗 -120.0 dBFS，確認超標源自 reverb/delay 尾巴而非模型自身衰減。**未登記於 `scores/verify_exemptions.json`，屬本輪逐聲道量測揭露的既有真實超標，待月月裁決**（改 score reverb 參數／登記豁免／接受現狀）。
2. `vivaldi_four_seasons_summer_m3.score.json` — `rests.rms_below_limit`：rest 5.12–6.00s 實測 **-47.1 dBFS**（門檻 -50.0，超標 2.9 dB，1/1 休止窗超標）。舊版 `(L+R)/2` 混降對同一窗口只量到 -52.6 dBFS——去相關立體聲殘響尾巴在混降時抵消約 5.5 dB，逐聲道量測揭露真實電平。FX-bypass 同窗 -120.0 dBFS 確認是 FX 尾巴。**未登記豁免，待月月裁決**。
3. `vivaldi_four_seasons_autumn_m1.score.json` — `determinism.rendered_twice`：run-1 第二次渲染進程啟動失敗（exit `0xC0000142` / `STATUS_DLL_INIT_FAILED`），屬高併發環境下的暫時性系統故障，非渲染邏輯問題（第一次渲染本身成功，manifest v2 的 `wav_sha256` 為 `2c1aa8efe869…`）。主迴圈 2026-07-21 單獨重驗：`RESULT: ALL CHECKS PASSED`，兩次渲染 SHA256 `2c1aa8efe869…` 一致——**確認非真回歸，已解除**，不計入待裁決清單。

**Corpus 淨結果**：73 個 repository score 中，**71/73 淨 PASS，2 個既有真實 FAIL 因本輪逐聲道 RMS 量測法而首次被抓到**（summer_m2／summer_m3，皆為 rest RMS 超標、皆已確認源自 reverb 尾巴、皆未放寬容差未偷登豁免）。這與第一輪（2026-07-17）「73/73 PASS」的差異，**成因是量測方法變嚴格（逐聲道取代混降）**，不是本輪對引擎或 score 資產的任何改動造成的音訊回歸——Rule 10 前後對照（見下）已確認 6 個代表性引擎機制對這兩首曲子的影響方向與其他曲目一致，沒有異常放大。

## Rule 10 前後對照（`reports/deep_fix_before_after.md`）

用改動前 baseline CLI（commit `485c6c1`，SHA256 `6f74d5c…`）與目前工作樹 CLI（SHA256 `f87037d…`）分別渲染 8 首代表曲目（7 首指派 + 1 首額外加入的 FM 域外對照組），RMS/peak/頻譜質心/T60 包絡/f0 全部量測：

| Score | RMS Δ (dB) | 備註 |
|---|---|---|
| `fur_elise_opening`（fm，域外對照） | -2.259 | 完全繞過 ModalResonator/HammerImpulse/PlateModel，單獨隔離 reverb 引擎替換（Schroeder→SimpleReverb）效果 |
| `moonlight_sonata_movement1_tongue_drum` | -3.682 | 無明示 `beam_boundary`，撞上 free-free→cantilever 預設改變；質心 +30.2 Hz |
| `akashic_opening_bell_001` | -1.211 | 7 tongue_drum + 1 water_gong，library score，同上機制 + 小幅 plate 貢獻 |
| `water_gong_clamped`（對照組） | -1.646 | clamped 邊界，不觸發 Bessel free-edge 重寫，仍受 T60 慣例/弱模態/reverb 改動影響 |
| `water_gong_free` | -3.712 | 完整觸發新 Bessel/modified-Bessel 徑向模態形狀與 ν 相依 free-edge 特徵值內插；Δ ≈ clamped 對照組的 2.3 倍，與機制一致 |
| `physical_piano` | **+2.346** | 8 首中唯一變大聲的一首——歸因（方向性，非隔離）為弱模態 -60dB 生命週期修正蓋過 tau→T60 縮短 |
| `moonlight_sonata_movement1_yangqin` | -2.517 | cimbalom，每個音符都有 `damping_override`（Phase H 曾位元不變），本輪因 tau→T60 重新詮釋發生在 `ModalResonator` 內部（`damping_override` 下游）而不再位元不變 |
| `vivaldi_four_seasons_summer_m3` | -2.648 | **score + engine 雙重改動未拆解**：before 用 commit-485c6c1 版本 score（`reverb.decay=2.1`），after 用當前工作樹 score（`reverb.decay=1.2`），疊加全部引擎端修正 |

全部 8 首在兩個 binary 上都成功渲染，無 score 相容性問題；3 個獨立音符探針（water_gong_clamped/free、physical_piano）的 f0 檢查確認音高偏移 < 1.5 cents，音高不受任何一項修正影響。報告明確指出本輪與 Phase H 的方法論落差：由於 6 項修正共用同一份未 commit 工作樹、其中 2 項（tau→T60、弱模態截止）在共用的 `ModalResonator.h` 內且無開關，無法逐機制隔離，僅能做曲目層級的方向性歸因。

## 新增檢查的意義

- **Eigenvalue anchors（F1）**：把此前定義卻無人消費的理論特徵值常數接回驗證路徑，讓 cantilever／free-free／clamped-plate／free-edge-plate 四種邊界條件的模態比值真正被機器驗證，而不只是「常數存在但沒人查」。
- **ET anchor（F2）**：把 `frequency_mode: "midi"` 的 f0 判定錨點改回獨立的 12-TET 理論頻率，避免「模型驗證模型自己」的循環論證；dump 一致性檢查降級為輔助而非唯一判準。
- **Velocity 物理律上限（F3）**：新增模型預測值本身是否落在 `+6.0206 ± 1.0 dB` 物理律窗內的檢查，能抓到「render 與模型互相吻合、但一起偏離物理」的退化情形——這正是本輪抓到 piano 違規的原因，舊版雙方互相印證的判定法完全測不出來。
- **殘差頻譜能量（F5，資訊性）**：量化「預測模態帶之外還有多少未解釋能量」，目前僅供參考不判定，待月月核定門檻後可轉為 exit-code 判定。
- **逐聲道 rest RMS**：修正立體聲去相關殘響尾巴在 `(L+R)/2` 混降時互相抵消、掩蓋真實超標的量測盲點；抓到的 2 個新 FAIL（summer_m2/m3）就是這個盲點過去藏住的既有事實。
- **Render manifest v2（`wav_sha256`）**：讓 manifest 第一次能被機器證明與實際 WAV bytes 一致，而非僅記錄衍生統計值；GATE 階段的 probe SHA 比對正是靠這個欄位交叉確認音訊未受修改影響。

## 待月月裁決事項

1. **piano velocity 物理律違規**（`--full` 唯一紅燈）：修 C++ velocity→接觸時間耦合，或月月本人修訂 §6 velocity 判定式。`tongue_drum` margin 僅 0.012 dB，一併留意。
2. **`vivaldi_four_seasons_summer_m2`／`summer_m3` 的 `rests.rms_below_limit`**：逐聲道量測首次揭露的既有真實超標（summer_m2 超標 0.1 dB、summer_m3 超標 2.9 dB），均確認源自 reverb 尾巴。選項：調整 score 的 reverb 參數、登記豁免（比照 moonlight 前例）、或接受現狀。
3. **殘差頻譜能量門檻轉判定制**：目前純資訊性，需月月核定門檻數值。
4. **`spectralTilt` 啟發式層去留**：`CimbalomEngine.h` 的未溯源經驗值，保留、移除或降級為文件化近似。
5. **`summer m3` `decay` 2.1→1.2 音樂性確認**：機器 GATE 已過，音樂性取捨需月月親自確認。
6. **Rule 10 報告審閱**：`reports/deep_fix_before_after.md` 的 8 首曲目前後對照，尤其 `physical_piano` 是唯一變大聲的一首，值得月月過目。
7. 承接第一輪既有待裁決項（`verify_score.py` `MODE_F0_TOL_CENTS`、Cubase 人工驗證、HTML 報告視覺驗收、push 時機）——完整列表見 `TODO.md`。

## 距離「全綠」的落差

本輪唯一未過的 GATE 是 `--full` 的 velocity 物理律判定（piano），且是**誠實暴露**而非新引入的回歸——舊版判定法本來就測不出這個問題。corpus 的 2 個新 FAIL 同理，是量測方法變嚴格後浮出的既有事實。除此之外，六項修復（F1/F2/F3/F5/逐聲道 RMS/manifest v2）全部落地、有回歸測試覆蓋、GATE 全部依規範執行且無容差放寬、無新增豁免。

---

## Round-3 補記（2026-07-22）

本輪列出的三項「月月待裁決」中，前兩項已在 round-3（`fix/deep-physics-audit-20260716`，同分支繼續 unstaged）處理完畢；第三項確認為文件層面的既有過期問題，順帶關閉。完整方法與逐項 GATE 見 `DEVLOG.md` 2026-07-22 條目；GATE 證據路徑規約 `reports/gate_outputs/deepfix3_*.txt`。

1. **piano velocity 物理律違規（本文件「待月月裁決事項」第 1 項）**——確認根因不是 C++ 模型錯，是**量測域選錯**：`6.0206 dB` 這條律的物理主張是逐模態振幅正比槌速（`ModalResonator::excite()`），round-2 的判定卻拿寬帶 RMS 驗證它，因此把 Hertz 接觸時間隨槌速變短帶來的頻譜變亮（物理真實，`HammerImpulse.h` 機制）也算成了違規。round-3 把 `judge_velocity()` 的量測域改到以 `measure_f0()` 為中心的基頻 ±3% 窄帶（`measure_band_rms_db()`，沿用 `measure_t60()` 同一 Butterworth band 家族），判定式數值本身一個字沒動。重測後 5 個 modal 引擎全數 PASS（piano +6.6702 dB，dev +0.65），`--full --skip-amps` 回綠；舊寬帶數字（piano +7.4373 dB）保留為資訊性行。selftest 4b 改注入弱基頻裡的違規以證明基頻窄帶不會漏掉寬帶會漏掉的問題，並保留 uniform-scale 反例。新證據：`reports/gate_outputs/deepfix3_selftest.txt`、`deepfix3_gate_full.txt`、`deepfix3_pytests.txt`（47/47）。**此量測域變更（寬帶→基頻窄帶）屬程式邏輯調整而非容差變更，仍待月月追認**——見 `TODO.md`。
2. **`vivaldi_four_seasons_summer_m2`／`summer_m3` 的 `rests.rms_below_limit`（本文件「待月月裁決事項」第 2 項）**——沿用 round-2 已確認的「源自 reverb 尾巴」前提，收斂 `reverb.decay`（`wet` 兩首皆不動）：`summer_m2` 2.8→2.6（3 個休止窗最緊裕度 2.6 dB）、`summer_m3` 1.2→1.0（唯一休止窗裕度 2.5 dB）。兩者 `verify_score.py` 全項重驗 PASS，含 determinism SHA256 match。`-50.0 dBFS` 門檻未動，未新增豁免。完整逐點掃描（每個 decay 值 × 每個休止窗，含音樂效果備註）：`reports/gate_outputs/deepfix3_summer_rest_sweep.txt`。**decay 縮短對殘響尾巴的藝術效果仍待月月最終確認**。
3. **`scores/originals/rules_v2_demo/rules_v2_demo_001.report.html` 過期**——順帶發現此 HTML 停留在 score.json 2026-07-17 改動之前，已用 `verify_score.py --html` 重生成並確認六區塊齊全、0 外部參照，**已關閉**，不再列為待辦。

其餘既有待裁決項（`MODE_F0_TOL_CENTS`、殘差頻譜能量判定制轉換、`spectralTilt` 去留、Rule 10 報告審閱、push 時機、Cubase／視覺驗收）本輪未觸碰，維持原狀，完整列表見 `TODO.md`。
