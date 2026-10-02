# TsukiSynth 物理精確化 Roadmap v2（驗收唯一依據）

> 建立日期：2026-07-02
> 地位：**本文件是後續開發的驗收唯一依據**。舊 `ROADMAP.md` 保留為歷史紀錄與產品向 backlog。
> 現行修復分支：`fix/deep-physics-audit-20260716`（2026-07-17）
>
> **給 AI 開發者（Opus / Codex / Claude）：開工前必讀 §1 強制規則與 §6 容差登記表。**

---

## 2026-09-07～16 裁決與落地補記（WF0907～WF0914 輪；2026-09-25 盤點後補寫）

> 依 Rule 8 補記。本文件自 2026-08-29（`76c41c4`）之後只在 WF0914 補過 §2 M10 列的 B7 段，下表是這段期間漏記的裁決；每列只寫做了什麼、裁決日期、證據檔。
> 過程細節見 `DEVLOG.md` 09-07～15 段與 `TODO.md` 開頭快照；逐條查證見 `reports/status_check_2026-09-25/`（2026-09-25 盤點，寫作時未入庫）。
> **git 狀態**：本文件較早段落裡的「unstaged 待審／待 push／等 UI mockup 裁決後才 merge」等字樣是當時的狀態，保留作歷史。
> 那些批次（08-06 響度校準、B1～B6、WF0907～0910 各卡）都已 commit、push 並 merge `main`（最近一次 merge `3f9b90a`，2026-09-15）。
> **WF0914 成果 2026-09-25 依月月裁決分 7 個 commit 入庫（未 push；hash 見 git log）。** **WF0925 輪（2026-09-25）的落地狀態記在檔尾「2026-09-25 WF0925 輪落地補記」**（放檔尾，是為了不讓其他文件引用的本檔行號位移）。**WF1002 輪（2026-10-02 月月裁決落地）記在檔尾「2026-10-02 WF1002 輪」；本輪月月首次授權改 §1 R6／R7 與 §6 原文，每處改動都留「2026-10-02 月月裁決 Qxx」註記。**

| 項目 | 裁決（日期） | 做了什麼 | 證據 |
|---|---|---|---|
| **A14** 高音弱基頻（M2/B4 範圍，會改渲染） | 規劃者 2026-09-08 代決「主因是引擎缺陷，B-2 先做、B-1 等文獻」（月月 09-07 委託，可推翻）；**月月 2026-09-10 放行 B-2 patch** | Felt 槌 `HammerImpulse::pianoHammerTauC()` 的音高形狀改錨已溯源的 `keytrackScale()`（k=0.32），力度形狀不變；G5/G6 基頻不再落進力脈衝深零點。位元不變 7/8，只 physical_piano 變，**8 首位元基準自此改用 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`**。B-1（力脈衝深零點形狀本身）仍等文獻（D10 補摘後兩篇缺口文獻仍付費牆）。**2026-09-25 盤點新發現**：給愛麗絲全曲乾聲 905 顆有 16 顆「基頻帶近乎無聲」FAIL（E5×9、A5×4、A6×2、A♯6×1，只出現在特定力度，例如 E5 只有 velocity 0.278 的 9 顆 FAIL）——深零點是搬到別的音高×力度組合，A14 報告只掃了音高軸。修法未定，**A14 維持開放**（`TODO.md` 登記為 D16）。**09-25 WF0925-N1 更新**：零點地圖完成（16/16 落在槌力脈衝頻譜零點），處理方式待裁決包 Q15（見檔尾 WF0925 補記） | 裁決包 `reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md`；Rule 10 報告 `reports/a14_tauc_keytrack_before_after.md`；`reports/gate_outputs/wf0910_A14_apply.txt`／`wf0910_A14_apply_AUDIT.txt`；16 顆見 `output/wf0914/D14/g2_full_report.json`（本機，gitignore；summary pass 677／fail 16／unverified 212）與盤點 `STATUS_CHECK.zh-TW.md` §2-1 |
| **D8** 空靈鼓槌具（改 score，會改渲染） | **月月 2026-09-09 裁決 `wood_mallet`** | 兩首月光空靈鼓相關 score 的 tongue_drum 事件 `exciter: finger → wood_mallet`（兩檔各 1142 事件，混音版揚琴事件不動）；獨奏版 200 Hz 以下能量 97.36%→17.55%，f0／T60 逐位元不變 | 裁決包 `reports/decision_packets/D8_tongue_drum_diagnosis.zh-TW.md`；Rule 10 報告 `reports/d8_tongue_drum_exciter_before_after.md`；`reports/gate_outputs/wf0909_D8_exciter.txt` |
| **F-03** IR preset 回存（外掛層；效果鏈屬 §0 域外） | 規劃者代決「B＋＋缺檔三態」（月月 2026-09-07 委託 AI 查外部資料決定，可推翻） | 受管理 IR 庫 `src/IRLibrary.h`（sha256 去重）、preset 存 `reverb_ir{kind,sha256,original_name}`、缺檔三態、`getIRStatus()` 為 UI／音訊單一真相 | `reports/decision_packets/F03_IR_PRESET_RECALL.zh-TW.md` §7（§8 裁決欄未勾，代決記錄在 `DEVLOG.md` 09-07～09 段）；`reports/gate_outputs/wf0908_P3_f03.txt` |
| **C10** 量測器自證（音高判定用的尺） | 月月 2026-09-09 選 B（改估計器）→ STFT 五候選＋時域 NLS 一候選全否決 → **月月 2026-09-10 改選 A（收窄主張域）** | 音高判定含量測器 ≤1.18 cent 已知系統誤差（開發 1.1721／hold-out 1.0840），±5 cent 門檻不變，**不可宣稱量測器 ≤1 cent**；產品估計器 `measure_pitch_cents()` 未動，NLS 候選只存 patch | `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.5／§9.7；`reports/decision_packets/C10_selfcal_domain.zh-TW.md` §7；`reports/gate_outputs/wf0910_C10A_landing.txt`；`reports/c10c_nls_candidate.patch` |
| **D15** 量測器自證補放鍵段語料 | **月月 2026-09-15 選 A'** | 主張域再收窄：≤1.18 cent 只涵蓋持續段；放鍵/阻尼段已知誤差上界 ~7.2 cent（開發 5.2304／hold-out 7.2055）；B'（另找估計器）不追 | `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.5；`reports/gate_outputs/wf0914_D15_gate1_*.txt`；施工卡 `docs/workcards/WF0914_D15_selfcal_corpus.md` |
| **D13** 水鑼 2.0× 缺 partial | **月月 2026-09-15 選 B** | 主張域收窄：`water_gong` 是自由邊平板、非乳突鑼，2.0× 附近無模態是域限制、非計算錯誤（已同步 §0 驗證域表 Water Gong 列）。`PlateModel.h` 檔頭與 `scores/examples/water_gong_free.score.json` 描述的同步，照裁決留待下一張動這兩檔的卡順路做（~~尚未做~~ **09-25 已由 WF0925-K1 同步**，staged 未 commit；見檔尾 WF0925 補記） | `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §1；裁決包 `reports/decision_packets/D13_gong_2x_partial.zh-TW.md` §4；`docs/GONG_PARTIAL_ANALYSIS.zh-TW.md`；`reports/gate_outputs/wf0914_D13_plate_ratios.txt` |
| **D9 → D9c** IR 模式響度（外掛層；效果鏈屬 §0 域外） | 月月 2026-09-15 選 (a)（量真實 IR）→ **月月 2026-09-16 選項 A** | D9b 量出 3 顆真實 IR 與合成 IR 的 wet-vs-ALGO 落差都在 −28.48～−28.73 dB（結構性固定差，與 IR 檔本身響度無關）；D9c 在 `src/effects/EffectChain.h` 只對 IR 模式 wet 乘固定補償 `kIrWetMakeupGain=26.9f`（+28.58 dB），**標為 DECIDED CONVENTION、非物理常數**（R4）；四組落差收斂到 +0.112／−0.131／+0.108／−0.028 dB；CLI／score 渲染不經 EffectChain，8/8 位元不變。**2026-09-25 盤點提出的限制**：對齊參考是 ALGO 預設 room size 0.5、未指定 T60；K-02 只印數字不判定，目前沒有任何 GATE 鎖住這個常數——要不要加硬 CHECK，待月月裁決。**09-25 WF0925-K2 更新**：已加 `kIrWetMakeupGain == 26.9f` 精確相等 CHECK（D9c-guard，只釘住常數本身）；IR 與 ALGO 的響度差仍沒有判定（裁決包 Q01）；常數裡約 18.06 dB 來自 JUCE Convolution 的 0.125 正規化，見 D9 裁決包檔尾 | 裁決包 `reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md`（兩次裁決記錄）；`reports/gate_outputs/wf0914_D9b_ir_injection.txt`、`wf0914_D9c_ir_makeup_gain.txt` |
| **D11** 弦長／弦徑造成非諧性 B 偏高 | **月月 2026-09-15 選 C** | 候選 patch 存檔不落地；新登記「D11-F5 根因調查」卡：候選修正下 `--full` F5 piano 殘餘能量 −63.9→−58.5 dB（門檻 −60 dB）退化的機制未查，查清後帶數字回來重開 A/B。**09-25 WF0925-F5 更新**：根因已查清（C4 基頻 T60 變短造成的頻譜洩漏），待裁決包 Q16（見檔尾 WF0925 補記） | 裁決包 `reports/decision_packets/D11_string_scale_candidate.zh-TW.md`（文末裁決記錄）；`reports/d11_string_scale_before_after.md`；`reports/d11_string_scale_candidate.patch` |
| **B7** 第一原理力鏈 | **月月 2026-09-15 選 §5 路徑 C＋驗收基準 (a) 乙案** | In progress——Phase 0 完成、Phase 1 部分完成（欄位撤回版）、Phase 2/3 BLOCKED（月月 09-15 裁決）；詳見 §2 M10 列 B7 段末「B7 現況」 | `reports/decision_packets/B7_phase2_and_open_items.zh-TW.md` §6 |
| **D12／D14**（非物理主張的工程缺口） | 月月 2026-09-14 授權「補 D9～D15」；2026-09-15 稽核 PASS 關閉 | D12：舊 DAW state `reverb_ir_path` 三態遷移（HostProbe 89 PASS）；D14：`stem_verify` 記憶體串流化（905 事件全量峰值 ≈1.65 GB，判定逐位元不變） | `reports/gate_outputs/wf0914_D12_*.txt`；`reports/gate_outputs/wf0914_D14_memory_fix.txt` |

**2026-09-25 對 WF0914 staged 樹重跑全套 GATE（D9c 落地後第一次全套）**：三主 target＋五測試 target 重建 exit 0；
ctest 4/4；pytest 270（264 passed＋1 skip＋5 xfail）；`physics_verify.py --full` NO CHECKED FAILURES；`--selftest` 13 行全 PASS；
`verify_score.py --all` 75/75（1 項既有豁免）；HostProbe 89 PASS／0 failures；位元不變 8/8 IDENTICAL（基準 `sha256_before_post_a14.txt`）。
數字與 09-15 基線相同。證據 `reports/status_check_2026-09-25/gate_logs/`（寫作時未入庫）。

---

## 2026-08-06 excitation keytrack + loudness calibration update（~~unstaged 待審~~ 已於 2026-08-10 commit `af849ec`）

- **M2 2a 槌頭模型補完音高維度（物理修正）**：`HammerImpulse::tauCForNote()`/
  `keytrackScale()` — 接觸時間 τc 隨音高 f^(-0.32) 縮放（Askenfelt & Jansson
  鋼琴量測 A0 ~4ms → C8 <1ms 擬合；該文獻本就引於檔頭，舊實作缺音高維度），
  錨 A4=1.0、clamp [0.4, 2.6]，Cimbalom/Chromatic 四個呼叫點全接。修正跨音域
  響度失衡的主因（Felt 2ms 下 C7 基頻被力脈衝頻譜壓 -37 dB）。
- **新增已文件化校準層（非物理主張，比照 spectralTilt 劃界，Rule 9 標註）**：
  `ModalResonator::modeAttackEnergy()` + `loudnessCompensationGain()` — noteOn 時
  以 300ms 攻擊窗模態能量做部分正規化（amount=0.78，月月 2026-08-06 三輪審聽
  定案），決定性 scalar、模態相對振幅不變、T60/f0 不動；Custom Harmonics 與 FM
  域外不套用。錨點常數 = A4 預設參數引擎內實測值（見 `CimbalomEngine.h`/
  `ChromaticEngine.h` 常數註解）。**velocity 律保線性**：能量預估一律用
  velocity=0.5（Hertz 錨）τc，不用實際 τc(velocity)——第一版用實際 τc 被
  `--full` F3 抓到 tongue_drum +4.72 dB 次線性 FAIL，修正後五引擎 +6.1 全 PASS，
  容差未動（Rule 2）。
- 量測與 Rule 10 前後對照：`reports/loudness_keytrack_before_after.md`
  （C2~C7 掃音 spread 27.3~36.3 dB → 8.2~8.7 dB，C2 削波消除）。
  絕對電平全面改變 → **corpus 73 檔重驗待執行**（登記於 `TODO.md`）。
  → **已完成**：73/73 PASS、0 FAIL、零新增豁免（`reports/gate_outputs/loudnessfix_corpus_{A..D}.txt`，同一 commit `af849ec`）。

---

## 2026-08-02 P1–P7 hardening update

- Modal modes outside the actual 20 Hz–`min(20 kHz, 0.98 Nyquist)` DSP band are rejected centrally. A modal event with no finite positive render-active energy now refuses rendering instead of producing an attack-only file that could falsely pass.
- Render manifest v4 recursively binds every layer dependency. Noise identity is semantic and stable under simultaneous-event permutation or zero-velocity insertion; optional unique `event_id` is available for AI editing.
- Score/parser/renderer/tuner share the six-rate 44.1–192 kHz contract. C++ gates now cover dimensional scaling, passivity, invalid numerics, causality, future-event locality, FX-off superposition and allocation refusal; MSVC ASan is a normal CI gate.
- Release CI adds pluginval L10, Steinberg's official VST3 validator and four deterministic complete-corpus shards. Local current-source results: `ctest` 3/3, Python 84/84, ASan 3/3, `physics_verify.py --full` no checked failures, validators PASS, corpus 73/73.
- `specimens/schema/specimen_measurement.schema.json` and `tools/specimen_verify.py` establish the external evidence path with raw/calibration/uncertainty hashes. Presently supported specimen claims are modal frequency, relative modal magnitude and T60. Complex phase, calibrated SPL and radiation directivity remain `UNVERIFIED`; infrastructure completion is not laboratory evidence.

---

## 2026-07-17 deep-audit update

- 現行完整方法與結果：`docs/DEEP_FIX_VERIFICATION_2026-07-17.zh-TW.md`。
- `physics_verify.py --full`：所有可量測項目無 checked failure；三個 rubber 極短瞬態明列 `UNVERIFIED/N/A`，不得沿用舊文字稱「全部材質已驗證」。
- Tuner 現為乾音訊量測：A0–C8、44.1–192 kHz、target/measured 分離、confidence／refusal；舊 NSDF/target-only 敘述作廢。
- Tongue Drum 預設改為符合舌片的 fixed-free cantilever；`free_free` 只代表明確選用的懸掛 bar。
- `frequency_mode: "midi"` 與 `"geometry"` 已拆開；只有 geometry 模式保留絕對尺寸／材質頻率。
- 同環境 SHA256 determinism 受測；跨 OS/compiler bit-exact 仍是未完成目標。
- M9 協和度 checker 現在以每個 score event 的真實 `--dump-modes` 重算（所有 active
  strings、材質、幾何、邊界、敲點與 velocity-dependent hammer spectrum），不再用
  固定 MIDI 60／固定引擎方向參考表代替；示範曲為 13 PASS、0 VIOLATION、0 UNVERIFIED。
- 最新 score GATE：Draft 2020-12 schema 80/80；release corpus 四分片合計 73/73 PASS、
  0 FAIL，僅既有 moonlight FX 藝術豁免保持可見，沒有新增豁免。Layered composite
  頂層 mode scan 明列 N/A，改由每個 leaf 的實際 `--dump-modes` 驗證。

## 2026-07-18 deep-audit round-2 update

- 稽核來源：2026-07-18 本 session 四線審查（同分支 `fix/deep-physics-audit-20260716` 上，針對第一輪 deep-audit 成果的第二輪覆核）。
- 修復範圍：round-2 修復覆核揭露的殘留缺陷——harness 量測法與判定語意、score 資產、文件／CI 設定，以及 §6 容差登記表同步（月月 2026-07-18 授權，見 §6 各列依據欄）。
- GATE 證據路徑規約：`reports/gate_outputs/deepfix2_*.txt`。完整方法、逐項 GATE 命令與 corpus 完整清單見
  `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md`。
- **實際 GATE 結果**：Rebuild（六 target）、`ctest`（3/3）、`physics_verify.py --selftest`、tuner oracle（v1+v2）、
  `unittest`（44 tests）、schema layer（80/80）、consonance gate（13/13）、probe SHA 比對皆 **PASS**（綠）。
  `physics_verify.py --full` **誠實 FAIL**（紅，exit 1）：新增的 velocity 物理律上限判定（F3）抓到 piano MIDI 60
  的模型預測值 `+7.4373 dB` 違反 `20·log10(2) = 6.0206 ± 1.0 dB` 上限——render 音訊與模型互相吻合，正是舊版
  「dump 自我一致」判定測不出來、新檢查要抓的退化；其餘子項（F1 特徵值錨、1b ET 掃描、1c 材質敏感度、
  2d 振幅、5b T60、F5 殘差資訊性）全 PASS。待月月裁決，見 `TODO.md`。
- **corpus 全量重跑**（四分片 + HTML 抽驗，涵蓋全部 73 個 repository score）：`A_examples_airadiance` 18/18、
  `C_library_1` 21/21、`D_library_2` 22/22、html 2/2 皆 **PASS**（綠）；`B_classical`（Vivaldi 四季 12 檔）
  9 PASS／3 FAIL——2 個 rest RMS 超標（`summer_m2`/`summer_m3`）是逐聲道量測法（取代舊 `(L+R)/2` 混降）
  首次揭露的既有真實超標，經 FX-bypass 確認源自 reverb 尾巴，非本輪回歸，未登記豁免、未放寬容差；
  第 3 個 `autumn_m1` determinism FAIL 為高併發環境暫時性渲染啟動失敗，2026-07-21 單獨重驗 PASS 已排除。
  淨結果 71/73，證據見 `reports/gate_outputs/deepfix2_corpus_*.txt`。
- **Rule 10 前後對照**：`reports/deep_fix_before_after.md`，8 首代表曲目 RMS/頻譜質心/T60/f0 改動前後比對，
  全部音高偏移 <1.5 cents，方向與量級可歸因到本輪修正機制。

## 2026-07-22 deep-audit round-3 update

- 處理範圍：round-2 留下的兩項月月待裁決——piano velocity 物理律「違規」、`summer_m2`／`summer_m3` rest RMS 超標。皆非容差變動：前者是量測域對齊物理律本身的逐模態適用範圍（寬帶→基頻窄帶），後者是 reverb decay 藝術參數收斂。
- **F3 velocity 量測域修正**：`tools/physics_verify.py` 新增 `measure_band_rms_db()`／`FUND_BAND_HALF_WIDTH`，`judge_velocity()` 改在基頻 ±3% 窄帶（沿用 `measure_t60()` 同一 Butterworth band 家族）量 `measured_delta`/`predicted_delta`；判定式數值（`|predicted−6.0206|≤1.0` 且 `|measured−predicted|≤1.0`）未動。寬帶 RMS delta 降級為資訊性行，不影響 exit code。**實測全數 PASS**：cimbalom +6.0587 dB、tongue_drum +6.0574 dB、water_gong +6.0586 dB、water_gong_free +6.0588 dB、piano +6.6702 dB（MIDI 60，velocity 48→96）；piano 寬帶「違規」（+7.4373 dB，資訊性）確認是 Hertz 接觸時間頻譜變亮，非振幅律破功。selftest 新增/改寫反例（見 §6 velocity 列、`docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md` round-3 補記）。
- **summer_m2／summer_m3 rest RMS 修復**：FX-bypass 已於 round-2 鎖定超標源自 reverb 尾巴；本輪掃描收斂 `reverb.decay`（`wet` 兩首皆不動）——`summer_m2` 2.8→2.6（裕度 2.6/4.5/2.6 dB）、`summer_m3` 1.2→1.0（裕度 2.5 dB）。`verify_score.py` 全項重驗兩首皆 PASS（含 determinism SHA256 match）。`-50.0 dBFS` 門檻未動，未新增豁免。完整掃描見 `reports/gate_outputs/deepfix3_summer_rest_sweep.txt`；音樂性取捨待月月最終確認。
- 順帶重生過期的 `scores/originals/rules_v2_demo/rules_v2_demo_001.report.html`（score.json 2026-07-17 改動後未跟進），`--html` PASS，六區塊齊全、0 外部參照。
- GATE 證據路徑規約：`reports/gate_outputs/deepfix3_*.txt`。詳見 `DEVLOG.md` 2026-07-22 條目與 `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md` 文末 round-3 補記。

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
| Cimbalom / Piano（StringModel） | ✅ 域內 | 敲擊剛性弦，含非諧性；振幅含已文件化 creative 層（`spectralTilt`，見 `CimbalomEngine.h` 註解），頻率／衰減不受影響；月月 2026-07-23 裁決保留並劃界。**（B3，Rule 9 標註）**弦阻尼空氣/黏彈/位錯三項為零自由參數公式（`docs/STRING_DAMPING_SOURCES.md`），materials.json 的 `beam_plate_beta_air`/`beam_plate_gamma_radiation` 對弦不生效、只給 Beam/Plate（未溯源） |
| Tongue Drum（BeamModel） | ✅ 域內 | 預設 fixed-free cantilever；`free_free` 是明確替代的懸掛 bar |
| Water Gong（PlateModel） | ✅ 域內 | Kirchhoff 圓板（clamped + free-edge；score／ChromaticEngine 預設 free-edge）。**自由邊平板、非乳突鑼**（無 boss、無鑼緣；2.0× 基頻附近結構性無模態是域限制、非計算錯誤——見 `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §1，月月 2026-09-15 D13 裁決 B） |
| Custom Harmonics | ⚠️ 半域內 | 加法合成，頻率比可驗但非物理推導 |
| FM Piano | ❌ 域外 | 已誠實標註「非物理合成」，維持此標註 |
| 效果鏈（Reverb/Delay/Comp/Dist） | ❌ 域外 | 驗證一律 FX 全關；用了效果的 score 不在物理主張範圍 |
| 未來 Sample Layer / Granular | ❌ 域外 | 若實作，必須明確標註，不得混入物理主張 |
| `frequency_mode: midi` | ⚠️ 設計聲明 | 混合系統：物理決定頻譜形狀、平均律決定基頻，不得宣稱絕對尺寸音高 |
| `frequency_mode: geometry` | ✅ 域內（方程層） | 保留材質／幾何計算的絕對頻率；仍需真實試體量測才能升級為 specimen-level 主張 |

---

## 1. AI 開發者強制規則

任何 AI（Opus / Codex / Claude / 其他）在本 repo 開發時必須遵守。違反任一條 = 該輪工作不予驗收。

1. **驗收只認 GATE 命令輸出，不認敘述。** 回報「完成」時必須附上 GATE 命令與完整輸出（或輸出檔路徑）。沒有輸出 = 沒有完成。
2. **禁止調寬任何容差。** §6 容差登記表的數值只能由月月批准修改。達不到門檻 → 回報實測數字 + 原因分析，停下來等決定；不得自行放寬後宣稱通過。（**R2 說明，F5 殘差頻譜能量：2026-10-02 月月裁決 N3＝A：認定為修正量法——扣掉預測模態自身的窗洩漏；門檻 −60 dB 不動；依據 R-b 注入測試。** 做法：`tools/physics_verify.py` 的 `measure_residual_energy()` 把 FFT 前的窗從 Hann 換成 4 項 Blackman-Harris（係數出處 Harris 1978，見常數 `F5_BLACKMAN_HARRIS_4` 註解）；±3% 帶、分析上限、[30 ms, 放鍵] 時段、−60.0 dB 門檻都沒改。依據：WF1002 R-b（`reports/wf1002_d11_piano_t60_literature_and_f5_method.zh-TW.md` §4–§5、`reports/gate_outputs/wf1002_R_b_f5_methods.txt`）——乾淨鋼琴探針 1.0 mm 舊量法 −59.47 dB（FAIL，數字跟著 T60 走、不是多餘能量），新量法 −82.73 dB；注入帶外衰減假泛音 L＝−70 dB，舊量法量成 −59.10 dB、新量法 −69.87 dB。**形式上「會判 FAIL 的情況」變少**，所以要月月裁；月月裁定這是修量法、不是放寬。`--selftest` 加反例「衰減訊號＋帶外衰減假泛音 L＝−50 dB 必 FAIL、L＝−70 dB 量值要對得上」，既有 3000 Hz 反例保留。前後數字見 `reports/gate_outputs/wf1002b_T_f5_method.txt`。）
3. **禁止縮小 GATE 範圍。** 不得只跑部分引擎、部分音符、部分 score 就宣稱整個 GATE 通過。
4. **禁止 hardcode 無法溯源的物理常數。** 每個新常數必須在程式碼註解或文件標明來源：文獻（書名/表號）、推導（公式）、或量測（方法）。
5. **Milestone 不可部分標記 Done。** 任務沒全完成就標 `In progress` 並列出剩餘項目。
6. **改動任何 `src/`（含全部子資料夾）或 `CMakeLists.txt` 之後**，宣稱完成前必跑（**2026-10-02 月月裁決 Q02=A**：範圍由原文「~~改動任何 `src/physics/`、`src/engines/`、`src/dsp/`、`src/score/` 之後~~」四個資料夾，擴成整個 `src/`＋`CMakeLists.txt`；理由：CLI 渲染也會經過 `src/effects/`，而且賣的是外掛）：
   - `python tools/physics_verify.py --full`（全引擎）→ 無 checked failure；任何 `UNVERIFIED/N/A` 必須逐項列出
   - 三個 build target（CLI / Standalone / VST3）exit 0；**外掛層另加（2026-10-02 月月裁決 Q02=A）**：改到外掛層（`src/PluginProcessor.*`、`src/PluginEditor.*`、`src/effects/`、`src/IRLibrary.h`、`src/PresetManager.h`、`src/ParameterLayout.*`、`src/Presets.h`；**2026-10-02 月月裁決 N8＝A 補列**外掛專用的 `src/HoverMagnifier.h`、`src/TsukiLookAndFeel.h`、`src/UiLocale.h`、`src/ScoreConsole.h`、`src/analyzer/`（整個資料夾）、`src/dsp/OutputPeakMeter.h`）時，另外必跑：先重建五個測試 target（`TsukiSynthAuditTest`、`TsukiSynthTunerTest`、`TsukiSynthPhysicsModelsTest`、`TsukiSynthSpectrumViewTest`、`TsukiSynthHostProbe`）再跑 `ctest`（X4 規約），以及 HostProbe 全套——上面的 `--full` 和三個 build 驗不到外掛行為
7. **不 commit、不 push（月月明示裁決時除外）；稽核 PASS 後由稽核 `git add`（staged）供月月審。**（**2026-10-02 月月裁決 Q03=A** 改字面；原文：「~~**不 commit、不 push。** 檔案留 unstaged，由月月審完決定（現行工作規則）。~~」——自 WF0907 起實務已是稽核 PASS 後 staged，見 `docs/workcards/WF0907_README.md`、`docs/workcards/WF0914_README.md` §2）
8. **文件同步。** 完成任何 GATE 後更新本文件 §2 狀態欄與 `TODO.md`。
9. **域外功能標註。** 任何驗證域外的新功能（見 §0 表），文件與 UI 必須標註，比照 FM Piano 的做法。
10. **音色會變的改動需告知。** 任何讓既有 preset / score 渲染結果改變的物理修正（如 M2），必須產出前後對照的頻譜差異報告，讓月月知情後決定。

> **~~待月月裁決~~ 已裁（2026-09-25 盤點提出；~~以上十條原文未改~~ 2026-10-02 月月裁決 Q02=A、Q03=A，R6、R7 已改字面，見上；下面兩條保留作歷史）**：
> - **R7 字面與實際流程不一致**：R7 寫「檔案留 unstaged」，但自 WF0907 起的實際流程是稽核 PASS 後由稽核執行 `git add`（staged）供月月審（`docs/workcards/WF0907_README.md`、`docs/workcards/WF0914_README.md` §2）。要不要把 R7 措辭改成「不 commit、不 push；稽核 PASS 後可 `git add`（staged）供審」，由月月決定。→ 見 `reports/decision_packets/WF0925_open_decisions.zh-TW.md` Q03（2026-09-25 補記）。**→ 2026-10-02 月月裁決 Q03=A：已照 A 改 R7 字面（見上）。**
> - **R6 範圍沒涵蓋外掛層**：R6 只列 `src/physics/`、`src/engines/`、`src/dsp/`、`src/score/`；D12 改的 `src/PluginProcessor.cpp`、D9c 改的 `src/effects/EffectChain.h`，以及 09-13 入庫的 `src/IRLibrary.h`、`src/ParameterLayout.cpp` 都不在強制範圍內（這幾張卡各自有跑 GATE，但規則文字沒有強制）。要不要把 R6 擴大到 `src/effects/` 與外掛層（`PluginProcessor`、`IRLibrary`、`ParameterLayout` 等），由月月決定。→ 見裁決包 `reports/decision_packets/WF0925_open_decisions.zh-TW.md` Q02。Q02 另查到：CLI 渲染路徑也會用到 `src/effects/`（`src/score/ScoreRenderer.h:11` include `../dsp/EffectsChain.h`，`src/dsp/EffectsChain.h:3-5` 再 include `../effects/SimpleReverb.h`、`StereoDelay.h`、`Compressor.h`），但 R6 字面沒列 `src/effects/`（2026-09-25 補記，R6 原文未改）。**→ 2026-10-02 月月裁決 Q02=A：R6 已擴成整個 `src/`＋`CMakeLists.txt`，外掛層另規定 ctest（先重建五個測試 target）＋HostProbe（見上）。**

---

## 2. Milestone 總覽

| # | 名稱 | 優先 | 支柱 | 狀態 |
|---|------|------|------|------|
| M1 | 驗證廣度擴大 + CI | P0 | 驗證 | **Done（2026-07-09，GATE 全過）**：本地 `--full` ALL WITHIN TOLERANCE（`reports/gate_outputs/full_FINAL_gate.txt`，Phase E 重跑見 `reports/gate_outputs/phase_e_gate_full.txt`）+ **GitHub CI 綠燈一次以上**（run 28957524611，`build-and-verify` ✓ 9m53s，月月 2026-07-09 授權 push 觸發，此時 M2 尚未過故 CI 跑 `--full --skip-amps`）。**Phase E 更新（unstaged，待 push）**：M2（`--amps`）已於本地全過，`.github/workflows/physics.yml` 已拿掉 `--skip-amps` 並刪除原本非阻斷的 M2 可視化步驟，CI 主 GATE 現改跑完整 `--full`（涵蓋 1b+1c+1d+2d）；**新版 workflow 已於 GitHub 綠燈**（月月 2026-07-09 授權 push `64e2836` 後，run 28960975003 `build-and-verify` ✓ 9m15s，完整 `--full` 含 2d 全過）。|
| M2 | 激發物理化 + 振幅譜驗證 | P0 | 樂器物理 | **Done（2026-07-09，Phase E，GATE 全過）**：2a–2e 全部實作完成，Phase D windowed-synthesis 預測法已就位；**Phase E 找到並修正最後根因**——`tools/physics_verify.py` 的 `synth_theory_signal()`（THEORY 端 harness 腳本，非 `src/` 渲染碼）把 `--dump-modes` 的 `decay` 欄位當成 1/e 時間常數 τ 衰減，但 `ModalResonator::excite()` 自己的公式明確把 `decayTime` 定義為 **T60**（`decayCoeff = exp(-6.9078f/(decayTime*sampleRate))`）——理論訊號衰減慢了 ln(1000)≈6.9078 倍，且不同 partial 的 decayTime 不同，此比例誤差在「相對基頻 dB」判定下不會抵消。換成正確指數 `exp(-ln(1000)*t/decayTime)` 後，5 個 modal 引擎（cimbalom / tongue_drum / water_gong / water_gong_free / piano）前 5 partial 全部收斂到 ≤±0.22 dB（原本 cimbalom/piano p3–p5 -3.0~-4.5 dB、water_gong p3–p5 -3.9~-8.0 dB、tongue_drum p2 -12.60 dB 全部 FAIL → PASS）。**容差全程未動（±3.0 dB，§6 Rule 2）**——只修了理論預測公式，不是放寬判定線；差異化渲染隔離實驗（`--body-amount 0` / `--no-exciter-noise` / `--num-strings 1`，見 `src/dsp/DiagnosticOverrides.h` + `src/cli/RenderApp.cpp` 新增的診斷專用旗標）逐一排除 BodyResonance / 敲擊噪聲 / 多弦拍頻三個候選機制，確認只有 decay-law 指數修正能關閉殘差，且這些診斷旗標預設為「不覆寫」sentinel、不在任何 score JSON / 預設 / 正常 CLI 呼叫路徑被觸發（SHA256 no-flags render 前後位元完全相同，`audio_path_changed=false`，故本輪不需規則 10 前後對照報告或整個 corpus 重跑）。GATE 證據：`reports/gate_outputs/phase_e_gate_amps.txt`（`RESULT: ALL WITHIN TOLERANCE`）、`reports/gate_outputs/phase_e_gate_full.txt`（含 `2d amplitude judgment: PASS`）；根因全推導見 `reports/gate_outputs/amps_residual_attribution.md`（承接 `amps_rootcause_analysis.md`）。<br>**B4 後續（2026-08-27，槌頭非線性接觸求解器完工，unstaged 待月月審）**：Felt 槌 tau_c 由固定 2ms 換成 `F=K·δ^α` 逐音接觸求解 `HammerImpulse::pianoHammerTauC()`（`docs/HAMMER_CONTACT_SOURCES.md` §2 三音錨常數表＋log-f 內插，錨定 `kTauCFelt`@A4/v=0.5；力度指數 −0.394～−0.500 隨音高變化），`CimbalomEngine.h` 4 呼叫點 Felt 分支；非 Felt／Chromatic 位元不變已證（`reports/gate_outputs/b4_nonfelt_invariance.txt`）。**--full F3 velocity 因此在 tau_c(v) 路徑撞牆**（piano predicted_delta C2 +6.3／C4 +7.79／C7 +19.12 dB，偏差隨 α 嚴格單調；渲染實測與模型預測吻合 <0.2 dB＝物理事實非 bug；FAIL 存證 `b4_gate_full_FAIL.txt`＋`b4_f3_alpha_monotonicity.txt`）→ **2026-08-27 月月裁決 (b)：重定義 F3 主張域**（見 §6 velocity 列；容差數值不變、固定 tau_c 路徑檢查一字不動），裁決包 `reports/decision_packets/B4_f3_velocity_ruling.md`，重定義後 GATE 全綠 `b4_gate_full_after_f3_redefine.txt`＋主張域哨兵 `b4_f3_redefine_sentinel.txt`。corpus 73/73 PASS 零新增豁免（`b4_corpus_all.txt`）；Rule 10 前後對照 `reports/b4_hammer_contact_before_after.md`；三 build＋ctest（X4 規約先重建）＋pytest 全綠（`b4_build_{cli,standalone,vst3}.txt`／`b4_ctest.txt`／`b4_pytest.txt`／`b4_x4_rebuild_tests.txt`）。Chromatic 引擎在 D2 補搜完成前不套用（域界不變）。<br>**A14 B-2 後續（2026-09-10 月月放行，2026-09-13 commit `31eb7ae`；本列 2026-09-25 補記）**：Felt 槌 `pianoHammerTauC()` 的音高形狀改錨已溯源的 `keytrackScale()`（k=0.32），力度形狀不變；G5/G6 基頻不再落進力脈衝深零點；位元不變 7/8 只 physical_piano 變，位元基準改用 `sha256_before_post_a14.txt`（Rule 10 報告 `reports/a14_tauc_keytrack_before_after.md`）。B-1（力脈衝深零點形狀）仍等文獻；2026-09-25 盤點另查到給愛麗絲全曲 16 顆新的弱基頻 FAIL（深零點搬到別的音高×力度組合），**A14 維持開放**——詳見檔頭「2026-09-07～16 裁決與落地補記」A14 列。|
| M3 | 整曲驗證工具 `verify_score.py` | P0 | 驗證 | **Done（2026-07-08，GATE 全過）**：單次 `verify_score.py --all` → `73/73 score(s) passed all checks (1 check(s) covered by registered exemption(s)), 0 failed`、exit 0（證據 `reports/gate_outputs/verify_all_corpus_phase_d.log`）。72 乾淨 PASS + 1 登記豁免（moonlight `rests.rms`，`scores/verify_exemptions.json`）。原「5 首大 Vivaldi 逾時」真根因＝`ScoreRenderer::dumpModes()` 的 `juce::String` 累加 O(n²)，改 `MemoryOutputStream` 後 5158-event 檔 dump 僅 7.2s，四季 12/12 全 PASS；逐檔證據 `corpus_phase_d_*.log`。規則 6 重驗：`--full` 之 1b/1c/1d 全 PASS 零回歸（`phase_d_gate_full_v2.txt`） |
| M4 | 視覺驗證報告（聾人介面） | P0 | 驗證/無障礙 | **Done（2026-08-15，4c 月月目視驗收通過）**：4a/4b 完工——`tools/report_html.py` 新增，`verify_score.py --html <score.json>` 產出單檔自足 HTML 視覺驗證報告（總結徽章／頻譜圖／f0 預測-實測對照／響度曲線＋休止驗證／樂句休止時間軸／頁尾），對 `scores/examples/water_gong_clamped.score.json`（110.8 KB）與 `scores/originals/ai_radiance/ai_radiance_m1.score.json`（~484 KB）皆 GATE exit 0，程式化驗證 0 個 `http(s)://` 外部參照、PNG/SVG 皆合法格式。過程中修正一個 f0 量測 bug（拋物線內插外推出頻段邊界產生假數字，已加邊界檢查改為誠實標示無法量測）。**4c 完成（2026-08-15）**：月月本人以瀏覽器打開 `ai_radiance_m1.report.html`（含 2026-08-06 二輪回饋加入的導讀卡與各區塊白話說明）目視驗收通過，確認報告可讀、判斷得了作品結構。三項齊備，Milestone 轉 Done。|
| M5 | 衰減（T60）驗證轉正 | P1 | 驗證 | **Done（2026-07-12，Phase G+I，GATE 全過）**：5a+5b（Phase G）——量測改寫為 5s 探針 + 測得 f0 為中心 ±3% 窄頻帶通（4th-order zero-phase `sosfiltfilt`）+ Hilbert envelope，多弦課（cimbalom/piano，`--dump-modes` 讀出的拍頻，非循環論證）先做 ≥1 拍頻週期滑動平均再對 log-envelope 做線性回歸，擬合窗於 attack 後 100ms 起、note-off 前 0.3s／-60dB／noise-floor+10dB 三者取先到者為止；全 5 個 modal 引擎於 MIDI 60/72 皆 1.00–1.28（cimbalom/piano 因拍頻最高到 1.28，其餘單弦引擎精確 1.00），跑兩次數字位元相同（determinism）。容差 0.2–5.0 → **0.5–2.0 判定制**已生效，`--t60` 現為 exit-code-affecting。5c（Phase I，溯源文件）——新增 `docs/MATERIALS_SOURCES.md`：`density`/`youngs_modulus`/`poisson_ratio` 對照工程手冊標「文獻」（發現 `rubber.youngs_modulus` 疑似刻意選值以穩定求解器，登記月月決策）；`damping.alpha`/`beta_air`/`gamma_radiation`（14 材質×3=42 個數字）逐一檢視後全部標「待溯源」，僅能佐證 Rayleigh 型阻尼模型與量級排序方向性合理（`wood_spruce.alpha` 排序疑似反常，登記月月決策）。**5c 補充（Phase H，2026-07-12，月月核准後數值已更新，`damping.alpha` 現況從「全部待溯源」轉為「部分已溯源」**：`reports/materials_physicalization_proposal.md` 用標準阻尼-Q 關係 `T60 ≈ 2.2/(f·η)`（`η`=文獻損耗因子，Fletcher & Rossing / Ashby / Lazan / Wegst 2006 等來源，詳見該檔 §2）反推，在 MIDI 60 錨點物理精確，14 種材質的 `damping.alpha` 全部改為新值（例如 steel `0.5→0.0238`、bronze `0.8→0.1189`，詳見該檔 §3 表），修正了 `wood_spruce.alpha` 排序異常（現在雲杉正確地是四種木料中阻尼最低者）；`rubber.youngs_modulus`（`1.5e9→5e6 Pa`）也已改為真實橡膠量級。**誠實揭露**：`alpha` 是單一頻率無關常數，只在錨點頻率（MIDI 60，Beam 引擎因既有 `*2` 加權在 MIDI 72）物理精確，其他音高是「同量級、非精確」的近似（`materials_physicalization_proposal.md` §1.3 明確標註這個侷限）；`beta_air`/`gamma_radiation` 仍維持「待溯源」未動，無文獻來源可查（**B3 更新，2026-08-24**：弦已改用零自由參數第一原理公式、不再讀這兩欄；兩欄改名 `beam_plate_beta_air`/`beam_plate_gamma_radiation` 只給 Beam/Plate，仍未溯源＝D1，見 M10 列 B3 後續）。規則 10 前後對照：`reports/phase_h_before_after.md`（Stage 2 章節）——確認 4 首受影響曲目 RMS 變大聲（+0.9~+4.8dB）、頻譜變暗（頻譜質心 -14~-142Hz）、T60 變長（1.3~19倍），音高不受影響，且暴露 2 個新的 harness 量測侷限（T60 探針時長不足以測極長衰減、rubber 材質衰減過快找不到基頻），已登記 `TODO.md`。最終 GATE 存證：`reports/gate_outputs/phase_g_gate_t60_final.txt`（Phase I 舊材質值，`--t60 --notes 60 72`，`RESULT: ALL WITHIN TOLERANCE`）；Phase H 新材質值下的 `--t60` 見 `reports/gate_outputs/phase_h_gate_t60.txt`（cimbalom/piano MIDI 60 新增 2 個 FAIL，harness 侷限非回歸，見 `reports/phase_h_before_after.md` §3）。**Phase I 收尾（2026-07-13）**：延續 5a/5b 的量測方法（不動容差，Rule 2），在 Phase H 物理化材質數值之上重跑 T60 GATE，Phase H 當時記錄的 2 個 FAIL 已隨（同方法內）量測窗口重算收斂，本輪 `--t60 --notes 60 72` → `RESULT: ALL WITHIN TOLERANCE`（5 引擎 × 2 音全 PASS）。證據：`reports/gate_outputs/phase_i_gate_t60.txt`；同時 `--full`（`phase_i_gate_full.txt`）與 `--amps`（`phase_i_gate_amps.txt`）皆 `ALL WITHIN TOLERANCE`。月月 2026-07-12「留」物理化材質的決策確認生效（詳見 `DEVLOG.md` Phase I）。 |
| M6 | 響度物理語意 | P1 | 樂器物理 | **Done（2026-07-12，Phase H，GATE 全過）**：6a（velocity→dB 文件化，`docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` §4.6 + `src/score/ScoreParser.h` 註解，comment-only）、6b（沿用 M1-1d 判定，共用不重做）、6c（`tools/loudness.py` 新增 ITU-R BS.1770-4 LUFS + 逐樂句/逐段 RMS，整合進 `verify_score.py` console 與 `report_html.py` HTML 報告）全部完成。證據：`python tools/loudness.py` 自我測試 PASS（997Hz 全幅 -3.0103 LUFS、-18dBFS -21.0103 LUFS，皆在 ±0.1 內）；`python tools/physics_verify.py --full` → `RESULT: ALL WITHIN TOLERANCE`（confirm 6a 純註解零回歸）；`python tools/verify_score.py --html scores/originals/ai_radiance/ai_radiance_m1.score.json` exit 0，HTML 報告 banner-stats 含整曲 LUFS、25 個樂句色塊皆含 RMS dBFS。詳見 `DEVLOG.md` Phase H。 |
| M7 | 容差緊縮 + 文獻對照 | P1 | 驗證 | **Done（2026-07-12，Phase H，月月同意執行 7b 數值更新後轉正）**：7a——f0 容差 ±12→±5 cents（`physics_verify.py`，全域，無 per-engine 例外），`--full` 全綠（`verify_score.py` 的 `MODE_F0_TOL_CENTS` 誠實留在 12.0，量測點不同，理由同前、已文件化的例外，見 TODO.md）。7c——`BEAM_BETAL` 5/5、`PLATE_OMEGA`（clamped）12/12 皆對照 Leissa NASA SP-160（Table 2.1）+ 獨立數值重解全數通過，comment-only，無數值變動。**7b——數值已更新（Phase H，2026-07-12，月月核准 + 規則 10 前後對照報告）**：`PLATE_FREE_OMEGA` `(m=4,n=0)`：`21.83f → 21.527f`（`src/physics/PlateModel.h` `freeModes[]` 第 5 項 + `tools/physics_verify.py` 鏡射同步改），依據 `docs/EIGENVALUE_SOURCES.md` §3 的文獻表（Leissa Table 2.5 給 21.6，表格自身標「±2% 近似」）+ 獨立數值重解精確特徵方程給 21.527（`mpmath` 40 位精度，兩次獨立重解一致）。**只影響 `water_gong_free` 引擎的一個泛音**，隔離驗證見 `reports/gate_outputs/phase_h_eig_delta.txt`：其餘泛音 0.000% 不變，該泛音頻率位移 -1.388%，與理論預測位元級吻合。因 `src/` 有數值改動，依規則 6 重建 3 個 target 全部 exit 0。**規則 10 前後對照報告**：`reports/phase_h_before_after.md`（Stage 1 章節）。最終 GATE 存證：`reports/gate_outputs/phase_h_gate_full.txt`／`phase_h_gate_amps.txt`（`--amps` 全 5 引擎 `RESULT: ALL WITHIN TOLERANCE`，確認振幅判定不受影響）；`--full`/`--t60` 在本輪材質修正（見 M5）疊加後出現 3 個新 FAIL，詳見 `reports/phase_h_before_after.md` §3/§4/§6 與 `TODO.md` 待裁決清單（皆為 harness 量測侷限，非渲染 bug，非本 milestone 範圍內的容差問題）。**Phase I 收尾（2026-07-13）**：7a/7b/7c 三項均已完成且未再變動；Phase H 遺留的 3 個 harness 侷限 FAIL 隨 M5 的 T60 量測法調整一併收斂，`--full`（`reports/gate_outputs/phase_i_gate_full.txt`）與 `--amps`（`phase_i_gate_amps.txt`）本輪重跑皆 `RESULT: ALL WITHIN TOLERANCE`，M7 判定 GATE 全綠，無待裁決殘留。 |
| M8 | 工程收尾（DAW / push / merge） | P0 | — | **8b Done（2026-08-26，月月裁決 A6）**：分支 `fix/deep-physics-audit-20260716` 首度併入 `main`（merge `b47d550`，CI 三平台全綠 run 33096174782），其後 B4 批次亦已併入（`361101e`）；B5/B6/三件套四批已 commit+push 但**依月月指示等 UI mockup 裁決後才 merge**（**2026-09-25 補記：此句已過時**——UI 裁決 2026-08-30 落地（雙開門否決→功能規格重做，`313acaa`），同日經月月授權併入 `main`（`64afb49`，另 `b7e4330` 補記錄）；之後 2026-09-07 `34aa904`、09-14 `b56747d`、09-15 `3f9b90a` 再併三次，現 `main`=`3f9b90a`）。8a 的 Cubase 人工項已由 L2/L3a/L3b 自動化+真 host 實測取代（TODO A9 關閉）。<br>（以下為 2026-07-11 的 In progress 歷史記錄，保留供追溯）8a 部分完成（pluginval L5+L10 自動化全過，`reports/gate_outputs/pluginval_L{5,10}.txt`；Cubase 人工項待月月）、8b 現況已核實（`master`/`Codex-fix-bug` 分支皆不存在，字面待辦 moot，剩 push 時機裁決）、8c 完成（README 措辭已改，見下方詳述）。 |
| M9 | AI 作曲規範 v2（非諧和聲規則） | P2 | 無障礙/AI | **Done（2026-07-12；2026-07-17 深修重驗）**：9a 的 MIDI 60 reference tables 已按 cantilever／板／槌與阻尼模型重生；9b 保留 T60/3＝衰減 20dB 的代數規則；9c 指南已同步；9d checker 已升級為逐 event 讀真實 C++ `--dump-modes` 重算，而非固定方向表。示範曲 13 PASS／0 VIOLATION／0 UNVERIFIED；實作與限制見 `reports/rules_v2_demo_consonance_check.md` 及本文件頂端 deep-audit update。歷史 2026-07-12 GATE 細節保留在 §3／`DEVLOG.md`。 |
| M10 | 琴橋導納／共鳴板耦合（頻率無關損耗通道，弦域） | P1 | 樂器物理 | **Done（2026-08-21，B2 收尾完成）**：2026-08-16 缺的兩個剩餘項已由 B2 卡補齊——(1) Rule 10 前後對照報告 `reports/b1_b2_bridge_damping_before_after.md` 已產出（§9 七項全含：白話導讀／T60 三欄對照 C2 128.75s→17.66s 發散收斂／summer_m2 由 FAIL −46.8 dBFS 回 PASS −52.2 dBFS／六曲整曲對照 ΔRMS ≤0.6 dB／錨點 0.1497→0.0874 + Chromatic 雙 null 自驗／BeamModel `*2` 重申未處理／determinism 聲明）；(2) corpus 73 檔四分片 **73/73 PASS、零新增豁免**（`b2_corpus_{A,B,C,D}.txt`）。錨點常數重測方法與證據 `b2_attack_energy_remeasure.txt`；全套 GATE 以新常數重跑後全綠（`b2_t60_baseline.txt` ALL WITHIN TOLERANCE、`b2_gate_full_final.txt` NO CHECKED FAILURES、三 build exit 0、ctest 3/3、pytest 121/121）。**改動未 commit，月月讀報告後裁決接受/回退（TODO A1'）。**（→ 2026-08-22 月月裁決 A1'「接受」，commit `4ef2c50`）<br>（以下為 2026-08-16 的 In progress 記錄，保留供追溯）<br>**⚠️ 2026-08-16 驗收更正**：本列原標 `Done`，經對抗驗證（scope 視角）指出違反 Rule 5 + Rule 10 後改回 `In progress`。理由：`bridgeLoss` 已無條件生效於所有 Cimbalom/Piano 預設渲染路徑（非旗標、非 opt-in），依 Rule 10「任何讓既有 preset／score 渲染結果改變的物理修正，必須產出前後對照的頻譜差異報告」，該報告 `reports/b1_b2_bridge_damping_before_after.md` **目前不存在**（已核實），B2 卡亦尚未開工。`physics_verify.py --full` 通過的是模型自身一致性，不能替代 Rule 10 的「與改動前音訊比對」。**剩餘項：Rule 10 前後對照報告 + corpus 73 檔重驗（皆屬 B2 範圍）。兩者齊備前本列不得標 Done。**<br>以下為實作內容：`StringModel::decayTimeForFrequency` 的阻尼律加入第四項 `T·G/(ln(1000)·L)`（`G` = 共鳴板無限板驅動點導納 `Y∞ = 1/(8√(D·ρs))` 的實部），只接在 Cimbalom/Piano（`StringModel`／`CimbalomEngine.h`）這條渲染路徑；**Chromatic 引擎（`BeamModel`/`PlateModel`/`ChromaticEngine.h`）零改動**（`git diff --stat` 確認）。新增檔案作用域常數 `kBridgeSoundboardThicknessM=0.009f`（文獻「鋼琴音板 8–10mm」範圍中點）、`kBridgeSoundboardMaterialKey="wood_spruce"`（`materials.json` 既有項，類比選擇）——**兩者皆非 TsukiSynth cimbalom 實測值，待月月確認，見 `TODO.md` A11**；刻意不加耦合折減係數（Rule 4）。`CimbalomVoice::noteOn()` 簽名新增 `soundboardMat` 參數，`src/score/ScoreRenderer.h` 三處呼叫點（dumpModes / renderCimbalom / eventMaxT60）全部跟進，`ChromaticVoice`/`FMVoice` 的 `noteOn()` 呼叫點不變。低音發散問題（`reports/damping_broadband_findings.md` 記錄的 C4/MIDI60 steel T60 26.86s）大幅收斂：`--full` 材質掃描顯示 cimbalom/piano steel MIDI 60 T60(model) 現為 **4.30s**（降至舊值的 16%）。**本 milestone 範圍不含 corpus 全量重驗與響度錨點常數（`kCimbalomAttackEnergyRefA4`）重測——那是 `docs/workcards/B2.md`（阻尼寬頻化收尾）的範圍**，`kCimbalomAttackEnergyRefA4` 本輪一個字元未動（仍是 `0.1497f`）。**此改動會讓所有 Cimbalom/Piano score 的渲染結果改變（衰減變快）**，完整的 Rule 10 前後對照報告由 B2 卡片產出（`reports/b1_b2_bridge_damping_before_after.md`，本卡不單獨產出）。GATE 證據：`reports/gate_outputs/b1_build_test.txt`（`TsukiSynthPhysicsModelsTest` build exit 0）、`b1_ctest.txt`（`physics_models_repro` Passed, 0 Failed，含 §7 新增 13 條 CHECK 全 PASS）、`b1_selftest_sentinel.txt`（哨兵：模擬的頻率相關 mutant 在同一等式判定下會 FAIL，真實實作 PASS，證明測試有偵測力）、`b1_gate_full.txt`（`RESULT: NO CHECKED FAILURES; UNVERIFIED/N/A RANGES REPORTED`，全引擎，rubber 3 例 N/A 為既有 harness 侷限與本卡無關）、`b1_t60_direction_check.txt`（人工方向抽查，非 exit-code GATE：cimbalom/piano MIDI 21–81 T60 較舊模型明顯縮短，1 個 tongue_drum/MIDI21 span<8dB 的既有 harness 量測窗侷限與 Chromatic 引擎無關、B1 未動該引擎）、`b1_build_cli.txt`／`b1_build_standalone.txt`／`b1_build_vst3.txt`（三 target 皆 exit 0）、`b1_ctest_all.txt`（3 個既有 C++ target 全 Passed，0 Failed）。<br>**B3 後續（2026-08-24，弦阻尼律換第一原理，待月月審 Rule 10 報告）**：`StringModel::decayTimeForFrequency()` 分母的 `beta_air·f²`/`gamma_radiation·f` 兩項已換成 Cuesta & Valette (1988) 零自由參數三機制 `Q⁻¹_air+Q⁻¹_visc+Q⁻¹_disl`（`docs/STRING_DAMPING_SOURCES.md`）；materials.json schema 遷移為 `beam_plate_beta_air`/`beam_plate_gamma_radiation`（fail-closed 拒載舊鍵名，數值不變、只給 Beam/Plate）。GATE 12 條全過（`reports/gate_outputs/b3_*.txt`，corpus 73/73 PASS 零新增豁免），Rule 10 報告 `reports/string_damping_firstprinciples_before_after.md`。<br>**B5 後續（2026-08-28，木材正交異向 schema 入庫，unstaged 待月月審）**：`data/materials.json` 四種木料新增可選 `orthotropic` 資料塊（9 個獨立正交異向常數 + 6 個量測泊松比 + 含水率 `Mp`，逐字轉錄自 Wood Handbook FPL-GTR-190 Table 5-1/5-2/5-13），`MaterialDB.h` 新增 fail-closed 解析/驗證；**目前零消費路徑**（`PlateModel`/`BeamModel` 仍是單一標量 `E`/`nu`，orthotropic schema 已備妥、屬死資料）。選種歧義（`wood_spruce`/`wood_maple`/`wood_oak`）已由月月 2026-08-28 裁決「照建議值走」（Spruce Sitka / Maple sugar / Oak red；birch 唯一表列條目無歧義）。GATE 8 條全過（`reports/gate_outputs/b5_*.txt`），13 首曲目 SHA256 bit-exact 全相同、corpus 四分片 73/73 PASS 零新增豁免，no-op 證明報告 `reports/b5_schema_noop_proof.md`。<br>**B6 後續（2026-08-28，輻射效率骨架 Phase 0+1，unstaged 待月月裁決 Phase 2）**：`docs/RADIATION_POWER_SOURCES.md`（Phase 0）查證 Ege & Boutillon 兩篇論文都沒有逐字給出「模態能量→輻射瓦特」的功率鏈公式，改走「標準定義代數推導」路線；並更正 `fc` 公式裡的符號誤讀（`fc=ca²/(2π√(Dx/ρs))`，不是 `Dx·H`）。新增 `src/physics/RadiationModel.h`（純函式：`criticalFrequency()`/`acousticCutoffFrequency()`/`radiationEfficiency()` σ(f) 骨架/`radiationLossFactor()`/`radiatedEnergyFraction()`），`StringModel.h` 新增 `soundboardDynamics()` getter（純暴露 B1 已算好的 D/ρs/G，不改 `bridgeLossRate()` 本身），`ScoreRenderer.h::dumpModes()` 加 `"radiated_power_relative"` 資訊性欄位（只對 string/cimbalom/piano 合格 partial、`f<fga` 才輸出；`beam`/`tongue_drum`/`plate`/`water_gong`/`custom`/`fm` 一律不輸出）。**只進 `--dump-modes` 診斷路徑，`render()`/`renderEvent()`/`ModalResonator` 一個位元未動**——8 首代表曲目 SHA256 位元不變 8/8（`reports/gate_outputs/b6_bit_identity.txt`）。GATE 全綠：三 build target exit 0、ctest 3/3（含新增 `testRadiationEfficiencyShape()`/`testRadiatedPowerChain()`，反例哨兵 `reports/gate_outputs/b6_selftest_sentinel.txt`）、pytest 131/131（含真實 `--dump-modes` 輸出的 Python 哨兵測試，確認 `radiation_directivity`/`complex_phase`/`absolute_pressure_per_force` 未被誤加）、`--full` 與 B5 基準 `b5_full.txt` 零差異（`b6_gate_full_phase1.txt`）、Vivaldi summer 樂章三（5158 事件，全 string 引擎）`--dump-modes` 4.5s 無逾時回歸（`b6_perf_sentinel.txt`）。**Phase 2（絕對物理單位校準常數）待月月從三個候選方案裁決，工兵不得自選**，詳見 `TODO.md` B6 條目與 `docs/workcards/B6.md` §6 步驟 10。<br>**B6 Phase 3/4 收尾（2026-08-28，方案 B 落地，unstaged 待月月審）**：月月裁決 Phase 2「照建議走」——方案 B 先行、方案 C 立卡排隊（`docs/workcards/B7.md`，`reports/decision_packets/B6_calibration_choice.md`「裁決記錄」節）。新增純物理訊號分接點 `DiagnosticOverrides::capturePhysicsOnlyModes`（`src/dsp/DiagnosticOverrides.h`，比照既有旗標模式）＋ `CimbalomVoice::getPhysicsOnlyModeAmplitudes()`（`src/engines/CimbalomEngine.h` 的 CLI `noteOn()` 變體專用，`startNote()` 即時播放路徑完全未動）：擷取每個 partial 在 `spectralTilt`／`loudnessCompensationGain`（創作層）之前、但 `HammerImpulse::forceSpectrumMagnitude()`（物理量）之後的振幅；旗標只由 `dumpModes()` 設為 `true`。`RadiationModel::kPascalsPerUnitPhysicsAmplitude=1.0f`＋`pressurePerForce()`（`src/physics/RadiationModel.h`）沿用 `EXTERNAL_ANCHOR_SOURCES.md` §1「數位 1.0≡1 Pa≡94dB SPL@1.05m」慣例、釘在該純物理訊號點——**R4 明確標註為月月裁決的方案 B 慣例錨定，非實測非推導**；刻意不消費 Phase 1 的 `σ(f)`/`η_rad(f)`（只當 fc/fga 有效範圍閘門，不當乘數，理由見 `docs/RADIATION_POWER_SOURCES.md` §5 補記）。`dumpModes()` 加 `"absolute_pressure_per_force"` 至 `model_observables`；每個事件加 `acoustic_transfer[]`（radius/azimuth/elevation 寫死 1.05/0/0；`imag_pa_n` 固定 0.0 且明確非相位主張；`f≥fga` 不輸出；非合格引擎/缺 D-ρs 輸出空陣列 `[]`，不省略鍵）。**`radiation_directivity`／`complex_phase` 確認未被誤加進 `model_observables`**（既有哨兵測試持續守；三則既有測試同步更新反映 Phase 3/4：`absolute_pressure_per_force`/`acoustic_transfer` 從「禁止」改「預期」）。新增測試：C++ `testPressurePerForceCalibration()`（手算對照 + doubled-constant mutant／零/負/NaN/+Inf 反例）、`testPhysicsOnlyCaptureDoesNotAffectRender()`（旗標開關下渲染路徑位元相同的單元級證明）；Python `Phase4SelfConsistencyTests`（真實 CLI dump 原封複製成 `SYNTHETIC_TEST_ONLY` bundle，`absolute_spl` claim PASS，+10dB 反例 FAIL）。**只進 `--dump-modes` 診斷路徑，`render()`/`renderEvent()`/`ModalResonator` 一個位元未動**——8 首代表曲目 SHA256 位元不變 8/8（`reports/gate_outputs/b6_bit_identity_phase34.txt`）＋單元級 `testPhysicsOnlyCaptureDoesNotAffectRender()` 雙重證明。GATE 全綠：三 build target exit 0、ctest 3/3、pytest 156/156、`--full` 與 Phase 1 基準零差異（`b6_gate_full_phase34.txt`）、corpus `verify_score.py --all` **75/75 PASS**（corpus 由 73 增至 75，兩份 `fur_elise_complete*` score 由無關工作新增、非 B6 改動；零新增豁免、零 FAIL，`b6_corpus_phase34.txt` 四分片）、specimen selftest PASS/FAIL 各一（`b6_specimen_selftest.txt`）。**B6 全卡 Done**（`docs/workcards/B6.md` §10 Phase 3/4 完成判定全數滿足）。<br>**B7 Phase 0+1（2026-09-14，WF0914-B7P0/B7P1，~~unstaged 待稽核~~→已稽核 PASS，In progress；現況以本段末「B7 現況」為準）**：Phase 0 兩份溯源文件完工——`docs/HAMMER_VELOCITY_SOURCES.md`（MIDI velocity→真實槌速 m/s，`v=2^((MIDI-52)/25)`，Goebl (2003) 博士論文式 (3.2) 原文已核，三錨點+兩實測極值+14%刻度差）、`docs/RADIATION_POWER_SOURCES.md` §8（音板輻射面積 `S`：同儕審查層級平台琴查無，只有同一台 Ege/Boutillon 直立琴的 1.2649 m²）。Phase 1（力鏈組裝）動工前依施工卡 §1.2 查證「現行音板參數（`kBridgeSoundboardThicknessM`=9mm、`wood_spruce` 材質）是否溯源自那台直立琴」——**否**：`CimbalomEngine.h` 自己的既有註解已明寫兩者是「文獻類比預設值，不是 TsukiSynth cimbalom 的實測值」（鋼琴音板 8–10mm 範圍中點、USDA Wood Handbook 通用 Sitka spruce），與 `S` 的唯一文獻數字非同一台琴、非同源參數族。依施工卡「否」分支：`S` 維持 `UNVERIFIED`，Path C 的 `absolute_pressure_per_force_firstprinciples_c`／`acoustic_transfer_c[]` 兩欄位**不輸出**（fail-closed），力鏈只落地到 §4.4 的 `W_bridge(f)`（新欄位 `"bridge_power_firstprinciples_c"`，僅 Cimbalom/Piano+Felt、且僅在該事件 D/ρs 可求時輸出）。新函式：`HammerImpulse.h` 新增 `hammerVelocityMps()`（Goebl 映射式+域外 flat clamp 0.18/6.8 m/s）與 `hertzPeakForceNewtons()`（能量守恆解 Hertz 接觸峰值力，沿用 B4 既有 K/α/m 錨點表，不改動）；`RadiationModel.h` 新增 `modalEnergyFirstPrinciples()`（本文件自推：無阻尼 SDOF 衝量-能量精確解 `E=|F_hat(ω)|²/(2m_eff)`，`m_eff=m_string/2` 沿用 `StringModel::calculateModes()` 既有「等模態質量」慣例）與 `bridgePowerFirstPrinciples()`（`W_bridge=2·α_bridge·E_mode`）。`ScoreRenderer.h::dumpModes()` 只加這一個新欄位（**此欄位已在同日稽核修復時撤回，見下 (3)**），`render()`/`renderEvent()`/`ModalResonator`/B4/B1/B6 既有函式一個字元未動。§7 五條測試依「否」分支調整（4/5 項改對 `W_bridge` 本身的物理哨兵，非 `W_rad≤W_bridge`／`acoustic_transfer_c[]` 比對，因兩者在此分支下都不存在）：`testHammerVelocityMps`（域內錨點/域外 clamp/單調/NaN 哨兵）、`testHertzPeakForceEnergyConservation`（Simpson 數值積分核對 C2/C4/C7 三音能量守恆 <1e-3）、`testHertzPeakForceCounterexample`（漏乘 (α+1) 突變體可辨識，ratio 0.41）、`testBridgePowerFirstPrinciplesChain`（手算基準點 E=0.8J/W=8.0W，利用 `forceSpectrumMagnitude` 既有 π/4 可去奇點使算式整除、F_peak 加倍功率四倍的物理哨兵、非負性、fail-closed）、`testPathBAndPathCDoNotInterfere`（B6/B7P1 兩條路徑純函式呼叫順序不影響結果+數值可區分）。GATE 全綠：三 build target exit 0（`wf0914_B7P1_build_*`）、ctest 4/4 Passed（`wf0914_B7P1_ctest.txt`，X4 先重建五測試 target）、`--full`/`--selftest` 與基線零差異（`wf0914_B7P1_gate_full.txt`/`wf0914_B7P1_selftest.txt`）、`verify_score.py --all` 與基線一致（`wf0914_B7P1_corpus_all.txt`）、位元不變性對 `sha256_before_post_a14.txt` 比對（`wf0914_B7P1_bit_identity.txt`，本卡只進 `--dump-modes`）。**剩餘項**：(a) §1.1 score velocity proxy→MIDI 換算（×127）為規劃者代決，非查證確認結果，月月可推翻（**已被同日稽核查證推翻，見下 (3)**）；(b) §8 驗收基準 (a)(b)（文獻 SPL GATE、與 B6 雙路徑一致性）本卡未執行；(c) `S` 若要繼續需月月在「跨琴種挪用直立琴 1.2649 m²」與「改用廠商規格值」之間裁決，或維持卡住——三者皆非本卡本輪範圍，詳見 `TODO.md` B7 條目與 WF0914-B7P1 完成報告。<br>**B7P1 稽核修復（2026-09-14，~~unstaged 待再次稽核~~→再次稽核 PASS 後 staged，In progress，狀態較上一輪倒退）**：稽核抓到兩個真實缺陷，皆已修——(1) **能量守恆違反**：`RadiationModel::modalEnergyFirstPrinciples()` 组裝的衝量用了兩個互不自洽的量（`F_peak` 來自 Hertz 能量守恆解，`τ_c` 卻沿用 B4 `pianoHammerTauC()`——一個完全不同、獨立錨定的量），導致 MIDI 36–96 × velocity 20–120 全域 24/24 點衝量超過物理上限 `2·m·v` 達 2.55–4.32 倍（稽核實測 MIDI60/velocity0.8：單一模態拿到全部槌頭動能的 23.7 倍）。修法：`HammerImpulse.h` 新增 `hertzImpulseConsistentTauCSeconds(note,v,F_peak)=π·m·v/F_peak`（半正弦脈衝模型自身衝量公式 `F_peak·τ_c·(2/π)` 令其等於彈性碰撞動量守恆 `2·m·v`，反解 `τ_c`——與 `F_peak` 同一組 Hertz 解自洽，不再混用 B4 獨立錨定的 `pianoHammerTauC()`），取代原本的錯誤呼叫。修復後全域衝量/`2mv` 比值精確收斂到 1.0（浮點精度內），`tests/physics_models_repro.cpp` 新增域掃描守恆測試 + regression guard（刻意重現舊呼叫方式，證明會 fail：MIDI60/velocity0.8 得 3.637 倍，與稽核實測 ~3.64 倍吻合）。(2) **§7 測試第 4 項被換成非守恆哨兵**：稽核指出「否」分支下仍有現成的守恆等價哨兵（衝量 ≤ 2mv）可測，前一輪漏做，已補上，域掃描測試 24+ 組全過。**(3) §1.1 velocity proxy→MIDI 換算重新查證後改判 BLOCKED**（稽核挑戰成立，且找到比稽核引用更直接的證據）：`tools/midi_to_tsukisynth.py::velocity_for()`——本專案唯一真正把 MIDI 轉成 score `velocity` 的程式碼——算式是 `base_velocity(role, 0.42–0.72) × (source_velocity/90.0)`（±0.025–0.035 微調，clamp 至 [0.12,0.92]），**從未是 `MIDI/127`、也不與 MIDI 成比例**（真實 MIDI velocity 在轉譜當下就被丟棄，score JSON 只留下這個複合值）。依施工卡 §1.1 原文「若查證結果與此矛盾…不要硬套，status=BLOCKED」——已撤回 `ScoreRenderer.h::dumpModes()` 對 `bridge_power_firstprinciples_c` 的欄位輸出與 `model_observables` 廣告，底層純函式（`hammerVelocityMps()`/`hertzPeakForceNewtons()`/`hertzImpulseConsistentTauCSeconds()`/`modalEnergyFirstPrinciples()`/`bridgePowerFirstPrinciples()`）保留、已修好、單元測試全過，待月月對 §1.1 裁決後再接回。**(4) 位元不變性證據檔補齊**：`wf0914_B7P1_bit_identity.txt` 這一輪重寫為真正含比對結果（先前版本只有 render log，沒有 diff/IDENTICAL 結論），本輪 8/8 IDENTICAL（含正規化 CRLF/LF 後的 `diff` exit 0 證據）。GATE 全綠：三 build target exit 0、ctest 4/4 Passed（`physics_models_repro` 內含新增守恆測試全 PASS）、`--full`/`--selftest` 與基線零差異、位元不變性 8/8 IDENTICAL。**Phase 1「最低限度交付物」（dumpModes() 新欄位）因 §1.1 BLOCKED 而未達成，狀態比上一輪「In progress」更保守——本輪判定為 BLOCKED，~~待月月裁決 §1.1~~**（月月 09-15 裁決不裁 §1.1，見下「B7 現況」）。詳見 WF0914-B7P1 稽核修復完成報告（摘要 `reports/gate_outputs/wf0914_B7P1_auditfix_summary.txt`）。<br>**B7 現況（月月 2026-09-15 裁決，`reports/decision_packets/B7_phase2_and_open_items.zh-TW.md` §6；本段 2026-09-25 依該節第 3 點同步）**：**In progress——Phase 0 完成、Phase 1 部分完成（欄位撤回版）、Phase 2/3 BLOCKED（月月 09-15 裁決）**（路徑 C＋(a) 乙案）。路徑 C＝§1.1（velocity proxy）與 `S`（§1.2）都不裁決，B7 本輪到此為止（B7.md §10/§12 的合法終點，不是 Done）：`dumpModes()` 的 `bridge_power_firstprinciples_c` 欄位維持撤回；五個純函式（`hammerVelocityMps()`／`hertzPeakForceNewtons()`／`hertzImpulseConsistentTauCSeconds()`／`modalEnergyFirstPrinciples()`／`bridgePowerFirstPrinciples()`）與測試保留入庫，產品端沒有任何呼叫點（8/8 位元不變）。(a) 乙案＝驗收基準 (a)（文獻 SPL GATE）標 BLOCKED（來源缺口），解除的三條管道（向 Goebl 索取 Fig. 2.20 校準值／機構帳號取 Roginska 2013／借閱 Meyer 動態範圍表）留給月月日後決定。之後若要重啟，要先解 §1.1（可能路線：score schema 加真實 MIDI velocity 欄位，需另開卡並改 B7.md §5 的禁令）。WF0914 成果（含 B7P0/B7P1）2026-09-25 依月月裁決分 7 個 commit 入庫（未 push；hash 見 git log）。**待月月裁決（2026-09-25 盤點提出，B7 重啟時再處理）**：`hammerVelocityMps()` 在 MIDI 20 邊界不連續——公式值 0.41 m/s，MIDI 20 以下 clamp 到實測極值 0.18 m/s，跳約 2.3 倍（文件說「比照 `interpAnchorsFlat()`」，但後者是連續的）；邊界要取公式值還是實測極值。 |

建議執行順序：M1 → M3 → M2 → M4 → M8 → M5/M6/M7 → M9 → M10。
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
（**2026-09-25 盤點註**：本段引用的 `corpus_phase_d_B_classical_1.log`／`_C_classical_2.log` 在磁碟與 git 歷史都查不到。四季 12 樂章的後續結果以 §2 M3 列為準：`reports/gate_outputs/corpus_phase_d_{spring,summer,autumn,winter}.log` 各 3/3 PASS，`verify_all_corpus_phase_d.log` 73/73。）

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
- [x] 4c. 對 AI Radiance 第一樂章產出範例報告，月月**用眼睛**驗收版面可讀性（視覺驗收，非聽覺，允許）。**2026-08-15 月月驗收通過**：`ai_radiance_m1.report.html`（含 2026-08-06 加入的「這一頁是什麼？」導讀卡與六區塊「💬 白話」說明）經月月本人瀏覽器目視後確認可讀、判斷得了作品結構。M4 三項全部完成，轉 **Done**。

**GATE**（**4a/4b 已過，2026-07-11**）：

```powershell
python tools/verify_score.py --html scores/examples/water_gong_clamped.score.json
# → exit 0, scores/examples/water_gong_clamped.report.html (110.8 KB), 含全部 6 區塊
python tools/verify_score.py --html scores/originals/ai_radiance/ai_radiance_m1.score.json
# → exit 0, scores/originals/ai_radiance/ai_radiance_m1.report.html (483–498 KB), 含全部 6 區塊
```
- 兩份報告皆已程式化驗證：`src=`/`href=` 屬性中 0 個 `http://`/`https://`；PNG chunk CRC32 與 IDAT 解壓長度正確；3 個 `<svg>` 區塊皆為合法 XML（`xml.etree.ElementTree` 可解析）。
- 月月確認報告看得懂、判斷得了作品結構（**2026-08-15 驗收通過，見 4c**）。

**不算完成**：報告只有文字表格沒有圖；需要連網載入 CDN；只做了頻譜圖沒做預測對照（對照才是驗證的核心）。

---

### M5 — 衰減（T60）驗證轉正（P1）

**為什麼**：目前 T60 容差 0.2–5.0 倍（約 ±14 dB 的範圍），標註 informational——等於沒有衰減驗證。衰減是敲擊樂器音色的第三根柱子（頻率、振幅之後）。

**任務**：

- [x] 5a. 量測改進（2026-07-12）：渲染加長到 5s；基頻帶通改為以「測得」f0（`measure_f0()` centroid，非 MIDI 名目頻率）為中心的 ±3% 窄頻帶（4th-order zero-phase `sosfiltfilt`），比舊版 ±20% 寬帶排除鄰近拍頻/雜訊更乾淨；多弦課（cimbalom/piano，同一 `renderCimbalom()` 路徑，預設 3 弦 detuning 5 cents）在對數包絡回歸前先用 ≥1 個拍頻週期（拍頻＝該音符 `--dump-modes` 讀出的弦間基頻最大差，模型自身真值、非循環論證）滑動平均，把拍頻造成的包絡起伏拉平但不動衰減率本身；回歸窗於 attack 後 100ms 起，至 note-off 前 0.3s／-60dB 點／noise-floor+10dB（floor 取自實際渲染 buffer 尾段）三者最早發生者為止。詳見 `tools/physics_verify.py` 的 `measure_t60()` docstring。
- [x] 5b. 容差收緊：0.2–5.0 → **0.5–2.0**（登記於 §6），全 modal 引擎判定制，`--t60` 現為 exit-code-affecting。5 個 modal 引擎於 MIDI 60 與 72 皆 ratio 1.00–1.28（單弦引擎 tongue_drum/water_gong/water_gong_free 精確 1.00；多弦 cimbalom/piano 1.16–1.28），跑兩次結果位元相同。GATE 輸出見 `reports/gate_outputs/phase_g_gate_t60.txt`。
- [x] 5c. `materials.json` 的阻尼三參數（alpha / beta_air / gamma_radiation）逐一標註來源或量測依據；標不出來的列入「待溯源」清單給月月。**（2026-07-12，Phase I）**：新增 `docs/MATERIALS_SOURCES.md`。`density`/`youngs_modulus`/`poisson_ratio` 對照標準工程手冊範圍，14 種材質幾乎全落在合理區間標「文獻」，唯 `rubber.youngs_modulus = 1.5e9 Pa` 比真實橡膠硬 100–1000 倍，疑似為模態求解器數值穩定性刻意選值，登記 `TODO.md` 待月月決定。`damping.alpha`/`beta_air`/`gamma_radiation`（14 材質×3=42 個數字）**全部標「待溯源」**——找不到任何具體出處，只能佐證 Rayleigh 型阻尼模型（Fletcher & Rossing）與量級排序方向性（鑄鐵≫鋼/鋁、橡膠/尼龍≫金屬）合理；`wood_spruce.damping.alpha = 8.0` 是四種木料中最高，但雲杉在聲學文獻中以低阻尼／高 Q 聞名（標準音板木料），現有排序方向看起來反常，同樣登記 `TODO.md`。**未更動任何 `materials.json`/`MaterialDB.h` 數值**——這份文件本身即是 5c 任務要求的交付物（誠實回報「標不出來」也是完成，非未完成）。
  **5c 數值更新（Phase H，2026-07-12，月月核准）**：上面登記的兩項待決都已由月月核准執行。
  `reports/materials_physicalization_proposal.md` 用 `T60 ≈ 2.2/(f·η)` 從文獻損耗因子 `η`
  反推 14 種材質的 `alpha`（MIDI 60 錨點物理精確，例如 steel `0.5→0.0238`），同時修正
  `wood_spruce.alpha` 排序異常（雲杉現在正確地是四種木料中阻尼最低者）；`rubber.youngs_modulus`
  改為 `5e6 Pa`（真實橡膠量級）。`beta_air`/`gamma_radiation` 仍維持「待溯源」未動。
  `damping.alpha` 狀態從「全部待溯源」升級為「已用 eta-Q 關係溯源，錨點頻率精確、其他音高近似」。
  規則 10 前後對照見 `reports/phase_h_before_after.md` §2。

**GATE**：

```powershell
python tools/physics_verify.py --t60
# → 全 modal 引擎 ratio ∈ [0.5, 2.0]，判定制 PASS
```

**已達成（2026-07-12）**：`reports/gate_outputs/phase_g_gate_t60.txt`（Phase G 原始，舊材質值）與
`reports/gate_outputs/phase_g_gate_t60_final.txt`（Phase I 最終存證，`--notes 60 72`，舊材質值）皆
`RESULT: ALL WITHIN TOLERANCE`，exit 0。**Phase H 新材質值下重跑**：`reports/gate_outputs/phase_h_gate_t60.txt`
——`cimbalom`/`piano` 於 MIDI 60 新增 2 個 FAIL（`ratio=0.28`，harness 的 5 秒探針 + 拍頻平均法在材質
物理化後大幅拉長的 T60（26.85s）下失真，非渲染回歸），根因分析見 `reports/phase_h_before_after.md`
§3，已登記 `TODO.md` 待月月/Opus 決定是否接受現況或授權下一輪調整 harness。§6 的 0.5–2.0 判定制
容差本身未動（Rule 2）。

**Milestone 完成（2026-07-12，Phase I，5c 數值於 Phase H 補完）**：5a（量測法改進）、5b（容差收緊生效）、
5c（材質常數溯源文件 + Phase H 數值更新，`docs/MATERIALS_SOURCES.md` + `reports/materials_physicalization_proposal.md`）
三項全部完成，M5 維持 Done。

---

### M6 — 響度物理語意（P1）（**Done，2026-07-12，Phase H**）

**為什麼**：等 RMS 校準是務實做法但不是物理。聾人判斷「這一音多大聲」需要一條定義好的、可驗證的規則。

**任務**：

- [x] 6a. 文件化 velocity 映射律：velocity → 激發力 → 振幅（現況：線性，×2 velocity = +6 dB）。寫進 `AI_PHYSICAL_COMPOSITION_GUIDE` 與 schema 註解。證據：`docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` 新增 §4.6「velocity 數字對照響度 dB 表」（velocity ×2 = +6.0 dB 換算表，聾人讀者向）；`src/score/ScoreParser.h` 在 `ScoreEvent::velocity` 欄位與其解析處各加註解區塊，說明 `ModalResonator::excite()` 的 `currentAmp = baseAmp * velocity` 線性律與 `20*log10(2)=+6.0206dB` 推導，**純註解、無邏輯變動**（`cmake --build build --config Release --target TsukiSynthCLI` exit 0 確認建置未破壞）。
- [x] 6b. M1-1d 的 +6 dB 判定即為此律的 harness 驗證（共用）。無需重做——`physics_verify.py --full` 的 `1d velocity judgment` 本來就是這條律的機器驗證，本輪重跑仍 `ALL WITHIN TOLERANCE`。
- [x] 6c. `verify_score.py` 報告加整曲 LUFS（integrated）與逐樂句 RMS，讓響度成為可讀數字。證據：新增 `tools/loudness.py`（ITU-R BS.1770-4 Annex 1 K-weighting，任意取樣率的雙線性轉換公式，於 48kHz 與標準公佈字面係數交叉核對誤差 <1.1e-12；400ms/75%overlap block + 絕對-70LUFS/相對-10LU 兩級 gating）。**自我測試**（`python tools/loudness.py` 或 `verify_score.py --selftest-lufs` 隱藏旗標）：997Hz 全幅正弦量得 **-3.0103 LUFS**（目標 -3.01±0.1，PASS）、-18dBFS 997Hz 正弦量得 **-21.0103 LUFS**（目標 -21.01±0.1，PASS）。整合：`verify_score.py` console 新增整曲 LUFS 資訊行（**純資訊，§6 未登記容差，不影響 exit code**）+ 逐樂句/逐段 RMS 明細（有 `phrases` 欄位逐樂句量測，否則退回合併事件發聲時間軸分段量測）；`report_html.py` banner-stats 行加整曲 LUFS，樂句時間軸每個樂句色塊加 RMS dBFS（hover title + 夠寬色塊的可見文字標籤）。

**GATE**（**全過，2026-07-12**）：velocity 判定綠燈（M1 共用，`physics_verify.py --full` → `RESULT: ALL WITHIN TOLERANCE`）+ 報告含 LUFS 欄位（`verify_score.py --html scores/originals/ai_radiance/ai_radiance_m1.score.json` exit 0，banner-stats 含整曲 LUFS、25 個樂句色塊皆含 RMS dBFS；`--html scores/examples/water_gong_clamped.score.json`——無 `phrases` 欄位——exit 0，console 印出 merged-activity fallback 分段 RMS）+ 文件更新（`docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` §4.6/§12.1，`DEVLOG.md` Phase H）。三個 build target（CLI/Standalone/VST3）皆 exit 0（Rule 6）。

---

### M7 — 容差緊縮 + 文獻對照（P1）

**為什麼**：f0 ±12 cents 偏寬（人耳可辨約 5 cents；我們的標準不能低於耳朵）。free-edge 板的 Ω 值目前是近似值（Leissa ν≈0.33），TODO 已列待複查。

**任務**：

- [x] 7a. f0 容差 ±12 → **±5 cents**（2026-07-12）。`physics_verify.py` 的 `F0_TOL_CENTS`（`measure_f0()` 音訊質心量測）已收緊為全域 5.0 cents，**無需個別引擎容差**：`--full` note-range scan（6 引擎×6 notes）+ material scan（9 材質×3 modal 引擎）全精度重測，最大 |cents| 僅 0.880（tongue_drum, wood_maple 材質），其餘幾乎全部 <0.1 cents，遠低於 5.0（margin ≥4 cents）。detuning 2 點縮放實驗（cimbalom/piano，detuning_cents=5/20/40）確認 cimbalom/piano 多弦拍頻造成的質心偏移**確實隨 detuning 縮放**（0.003→0.044→0.199 cents）——物理機制真實存在，但出廠預設值（detuningCents=5.0）下遠低於門檻，故單一全域常數即可，未建 per-engine dict。GATE 證據：`reports/gate_outputs/phase_g_gate_full_f0.txt`（`RESULT: ALL WITHIN TOLERANCE`）。**`verify_score.py` 的 `MODE_F0_TOL_CENTS` 刻意未跟進收緊，留在 12.0**——它量測的不是同一件事：`--dump-modes` 的 `partials[0]` 只讀多弦課「第 0 條弦」的原始值（`ScoreRenderer::dumpModes()` 只用 `allStrings[0]`），而 `CimbalomVoice::noteOn()` 把第 0 條弦按設計精準調到 `-detuningCents` cents（預設 -5.000 cents），不是聲學質心。5 首真實曲目測試中，3 首含 cimbalom/piano 的曲目量得 max cents 為 5.002/5.005/5.013——收緊到 5.0 會讓它們立即 FAIL，即使 `physics_verify.py` 已驗證這些曲目實際渲染音訊的真實基頻在 0.05 cents 內。要收緊這個檢查需要改「量測什麼」（例如改成 course 平均/質心），屬於程式邏輯變更，不在本次容差任務範圍內，故誠實回報、留在 12.0，登記於 `TODO.md` 待月月決定是否授權下一輪改量測法。
- [x] 7b. `PLATE_FREE_OMEGA` 對照文獻表（Leissa, *Vibration of Plates*, NASA SP-160 或等效來源）：誤差 ≤1% 或更新數值；來源寫進註解。**（2026-07-12，Phase I 溯源 + Phase H 數值更新）**：新增 `docs/EIGENVALUE_SOURCES.md`。直接從 NASA NTRS 取得原始文獻，Table 2.5（free-edge, ν=0.33）7 項中 6 項與程式碼數字位元完全相同（(2,0)/(0,1)/(3,0)/(1,1)/(2,1)/(0,2)）；**發現 1 項差異**：`(m=4,n=0)` 程式碼 21.83f，但 Table 2.5 給 21.6（表格自己註明是 ±2% 漸近近似）、本任務從第一原理獨立重解精確特徵方程給 21.527，兩者都與 21.83 差距超過 1%（1.06%/1.4%），方向一致，像是抄錄誤植。Phase I 當輪依規則未修改此數值，寫成提案登記 `TODO.md`。**Phase H（2026-07-12）：月月核准後數值已更新** `{ 21.83f, 4, 0 }` → `{ 21.527f, 4, 0 }`（`PlateModel.h` 與 `physics_verify.py` 兩處鏡射同步改），規則 10 前後對照報告 `reports/phase_h_before_after.md` §1：只影響 `water_gong_free` 引擎一個泛音，隔離驗證頻率位移 -1.388% 與理論預測位元級吻合，其餘泛音 0.000% 不變。
- [x] 7c. `PLATE_OMEGA`（clamped）、`BEAM_BETAL` 同樣補來源註記（數值應已正確，補溯源）。**（2026-07-12，Phase I）**：`BEAM_BETAL`（自由樑，`cosh(x)cos(x)=1` 解析根）5/5 與 `scipy.optimize.brentq` 獨立數值重解匹配；`PLATE_OMEGA`（clamped 圓板）12/12 對照 Table 2.1（NASA NTRS 原始來源 + Tom Irvine 附錄 H 二次獨立複核）與獨立解 clamped-plate 特徵方程（`mpmath` 30 位精度）皆匹配，最大誤差 0.03%（表格捨入級）。三處 `src/physics/BeamModel.h`／`src/physics/PlateModel.h`／`tools/physics_verify.py` 皆僅加註解，`git diff` 確認無任何數值行變動（這兩個表本身未受 Phase H 數值更新影響，只有 `PLATE_FREE_OMEGA` 動了）。

**GATE**：`physics_verify.py --full` 在新容差下全綠；三組常數的來源註記存在。

**7a GATE（已過，2026-07-12）**：`physics_verify.py --full`（f0 容差 5.0 cents）→ `RESULT: ALL WITHIN TOLERANCE`，證據 `reports/gate_outputs/phase_g_gate_full_f0.txt`。

**Milestone 完成（2026-07-12，Phase I 溯源 + Phase H 數值轉正）**：7a（f0 容差收緊，全域無 per-engine 例外；`verify_score.py` 側維持 12.0 為已文件化例外）+ 7c（`BEAM_BETAL`/`PLATE_OMEGA` 溯源，comment-only）+ **7b（`PLATE_FREE_OMEGA` (4,0) 數值已更新為文獻一致值 21.527f，Phase H，月月核准 + 規則 10 前後對照報告 `reports/phase_h_before_after.md`）**全部完成，M7 標 **Done**。GATE 存證：`reports/gate_outputs/phase_h_gate_full.txt`／`phase_h_gate_amps.txt`（`--amps` 全 5 引擎 `RESULT: ALL WITHIN TOLERANCE`）；`--full`/`--t60` 疊加 M5 材質修正後的新 FAIL（rubber 材質 f0 掃描、piano MIDI108 f0、cimbalom/piano MIDI60 T60）詳見 `reports/phase_h_before_after.md` §3/§4/§6，已登記 `TODO.md` 待裁決，不影響 M7 本身（那些 FAIL 是 M5 材質修正 + harness 侷限的交互作用，不是 7a/7b/7c 容差或特徵值本身的問題）。三個 build target（Rule 6，因 `src/` 有數值改動）皆 `cmake --build` exit 0。

---

### M8 — 工程收尾（P0，既有欠帳）

- [x] 8a（部分）. pluginval 自動化驗證：pluginval 1.0.4 對 `TsukiSynth.vst3` 分別跑 `--strictness-level 5` 與 `--strictness-level 10`（最高等級），兩次皆 `SUCCESS`、exit code 0，涵蓋 plugin scan、冷/熱開啟、editor 開關、27 組 program 枚舉、跨取樣率(44.1k/48k/96k)×block size(64–1024) 音訊處理、state 存讀、參數 automation、bus layout、（L10 額外）非釋放連續處理、Parameters/Background-thread/Parameter-thread-safety/Fuzz-parameters 測試，log 兩份皆 0 個 warn/error/fail 字樣。證據：`reports/gate_outputs/pluginval_L5.txt`、`reports/gate_outputs/pluginval_L10.txt`。**但這只涵蓋自動化可測的部分**——真正在 Cubase host 裡的**人工**確認（host 掃描辨識到外掛、MIDI in 實際彈奏出聲、GUI 上的 automation lane 手動畫自動化曲線後回放正確、專案存檔關閉重開 state 正確還原）**尚未做**，需要月月在自己的 Cubase 環境操作，AI 無法代為完成，清單見 `TODO.md`。
- [x] 8b. **Done（2026-08-26）**：月月裁決 A6「下一批 Commit+merge 進去」→ `fix/deep-physics-audit-20260716` 首度併入 `main`（`b47d550`），B4 批次續併（`361101e`），CI 三平台全綠。**後續四批（B5/B6/三件套/B6 收官）已 commit+push，merge 時機依月月指示等 UI mockup 裁決。**（2026-09-25 補記：已於 2026-08-30 併入 `main`，其後再併三次，見 §2 M8 列。） 以下為 2026-07-11 的歷史核實記錄：`Codex-fix-bug` 剩餘 commit push；merge → master 的決定（月月裁決）。**現況核實（2026-07-11，`git branch -a`）**：目前 repo 只有 `main`（+ `remotes/origin/HEAD`、`remotes/origin/main`），**沒有獨立的 `master` 分支存在**，也沒有本地或遠端的 `Codex-fix-bug` 分支——早前提到的 `Codex-fix-bug` 工作已經在某次月月授權的 push 中併入 `main`。故「merge `Codex-fix-bug` → master」這個字面待辦**已經 moot**（目標分支不存在，來源分支也不存在），8b 真正剩下的只是「本輪 Phase F 尚未 push 的變更何時 push」，見 8b 下方 GATE 段落與 `TODO.md`。
- [x] 8c. `README.md` 依驗證域聲明改寫「精確」相關措辭：對外主張改用「物理可驗證（physically verifiable）」，「精確」保留給 GATE 已覆蓋的項目；新增「Physical Verification」章節列出 §0 驗證域表（域內/半域內/域外）+ 逐項引用 §6 容差數字與 GATE 證據路徑；三個引擎標題與 Effect Chain 標題皆補上域內/域外標註。證據：`README.md`（本輪 diff，`git diff README.md`）。

**GATE**：DAW 驗證四項有紀錄（截圖或文字）——**pluginval 自動化涵蓋 3 項（scan-equivalent／automation／state round-trip 的非-DAW 版本），Cubase 內 MIDI in 手動彈奏確認與 host 專屬行為仍待月月人工執行**；README 措辭審過（已完成，見 8c）。

---

### M9 — AI 作曲規範 v2：非諧樂器的和聲與時值規則（P2）

**為什麼**：月月觀察到 AI 自由創作「短暫且不和諧」。這有可分析的理論原因，不需要耳朵就能改善：

1. Tongue drum / water gong 的泛音是**非諧的**（梁 1:2.76:5.40、板 1:1.73:2.33…）。用寫鋼琴音樂的方式堆三和弦，泛音會互相打架——這不是 bug，是物理。非諧樂器的合奏在真實世界（gamelan、鐘樂）有自己的一套音程規則。
2. AI 逐音生成缺乏長程結構，樂句短是通病，`phrases` 骨架先行可以緩解（指南 §11 已有，但沒有和聲規則）。

**任務**：

- [x] 9a. 為每個引擎計算「理論協和度表」：給定兩音音程，計算泛音碰撞度（如 Sethares 的 dissonance curve 方法——純計算，不用聽）。產出每引擎的建議音程集。證據：`tools/consonance.py`（Sethares 1993 公式，常數 d\*/s1/s2/b1/b2 皆引用並在檔內註解來源）→ `reports/consonance_tables.md`：5 個 modal 引擎（cimbalom/tongue_drum/water_gong/water_gong_free/piano）各自的部分音頻譜（來自 `--dump-modes`，M2 已驗證過的同一理論值）+ 0–1200 cents（5-cent 解析度）dissonance-curve 掃描 + 局部極小值（建議音程）/極大值（不建議音程），另外算了 3 組跨引擎表（cimbalom↔tongue_drum 為 M9 指定必算、cimbalom↔water_gong、tongue_drum↔water_gong）。
- [x] 9b. 時值規則：每引擎依 T60 給出最小建議音長與音符密度上限（衰減沒完成前就再擊 → 濁）。證據：同一份 `tools/consonance.py` 在報告 §4 算出 5 個 modal 引擎於 MIDI 48/60/72 的 T60（讀自 `--dump-modes` 的 `decay` 欄位，M5 已驗證過的同一份理論值）與 T60/3（衰減 20dB 所需時間的精確代數推論，非新常數）＝最小同音重擊間距，換算成密度上限（音符/秒）。
- [x] 9c. 寫進 `AI_PHYSICAL_COMPOSITION_GUIDE` v2：非諧引擎和聲規則、聲部配器建議（諧波引擎擔任和聲、非諧引擎擔任色彩/節奏）、長程結構模板（AABA、頑固低音等）。證據：`docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` version 2.0，新增 §13（非諧引擎和聲規則，含跨引擎音程規則與 12-TET 可達成音程表）、§14（聲部配器建議）、§15（長程結構模板：AABA/頑固低音/chaconne，附 JSON `phrases[]` 骨架範例）、§16（時值規則，T60/3 表）。每條規則都附 `reports/consonance_tables.md` 或 M5 T60 GATE 的具體數字，零「聽起來更好」用語。
- [x] 9d. 用 v2 規範讓 AI 重新創作一首，跑 M3/M4 驗證管線全綠，並附協和度分析報告。證據：`scores/originals/rules_v2_demo/rules_v2_demo_001.score.json`（AABA + 尾聲，83.75 秒，cimbalom/tongue_drum/water_gong 三引擎，README.md 逐條列出每個音高/時值選擇對應 §13/§16 的哪個數字）。`tools/check_piece_consonance.py` 在 2026-07-17 升級為每個 event 的真實模態頻譜（所有 active strings、material/geometry/boundary/strike/velocity hammer spectrum）重算，對 13 個宣告時間重疊音程判定 `reports/rules_v2_demo_consonance_check.md`：**13 PASS、0 VIOLATION、0 UNVERIFIED**；FM／Custom 明列域外，且報告明示不模擬 duration 後的共鳴尾巴。`verify_score.py` 的當次結果以最新 deep-fix 驗證報告為準。

**GATE**（全過）：協和度表可重現（`python tools/consonance.py` → `reports/consonance_tables.md`）；指南 v2 更新（`docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` §13–§16）；新作通過 `verify_score.py`（exit 0）且協和度合規檢查器 0 違規（`reports/rules_v2_demo_consonance_check.md`）。未改動任何 `src/`，`physics_verify.py --full`（含 `--amps`）重跑確認零回歸。

---

## 4. Nice to have（不擋目標，有餘裕才做）

依價值排序：

1. **Plugin ↔ CLI 一致性驗證** — 目前只有 CLI 是純物理路徑；驗 plugin 渲染（macro 中性 + FX 關）與 CLI 輸出的一致性，讓 DAW 使用者也在驗證域內。
2. **音板/共鳴箱耦合**（piano / cimbalom）— 真實感大增，但要先想好「音板模態怎麼驗證」，做不到理論比對就不做（原則：不增加驗證域外的物理裝飾）。
3. **鋼琴進階物理** — 槌氈非線性（velocity → 接觸時間變短 → 更亮，這是 M2 力脈衝模型的自然延伸）、同度弦組（複用 cimbalom 多弦 beating）、延音踏板共鳴。
4. **跨機器可重現性** — 在第二台機器 build 後跑 determinism 比對，位元不一致就定義容差型比對標準。**2026-08-15：量測側已完成（unstaged）**——`tools/crossplatform_verify.py`（selftest 11/11、同機 emit×2 BIT_IDENTICAL 5/5、1 LSB 注入反例正確偵測、四個 exit code 實測正確）+ CI 三平台矩陣 job。第二台機器改用 GitHub hosted runner（ubuntu-24.04 / macos-14）取代實體機。**跨平台實測數字要月月 push 後 CI 跑過才拿得到**；拿到後把數字登記進 §6「決定性」列即完成本項。**（2026-09-25 補記：已完成**——§6「決定性」列已登記跨機容差（`scores/crossplatform_tolerance.json`，commit `1c70efb`），`cross-platform-compare` 轉阻斷式 GATE。）
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
| f0 誤差（`physics_verify.py` 音訊量測） | ±5 cents（全域，無 per-engine 放寬） | ±5 cents（M7） | 2026-07-17 note-range 全過；rubber 三例因不足八週期列 N/A，不以攻擊噪聲假造 f0；**沿用本列的兩處（2026-10-02 月月裁決 Q04=A 註明）**：`melody_verify.py` 的 pitch ±5 cents（`PITCH_TOL_CENTS = vs.MODE_F0_TOL_CENTS`）與 `partial_verify.py` 的 partial 頻率 ±5 cents 都是沿用本列，不是另外的容差 |
| f0 誤差（`verify_score.py` `--dump-modes` course 質心值） | ±5 cents（`check_modes()` 已改為振幅加權 course 質心；2026-07-23 GATE 完成） | ±5 cents（M7，與 `physics_verify.py` 全域容差一致） | 舊量測點是單一弦（by design `-detuningCents` 偏移），非聲學質心；改用 course 質心後 moonlight yangqin 誤差由 5.013 降至 0.019 cents。證據：`reports/gate_outputs/deepfix4_*` |
| Partial 頻率誤差 | 2–4%（依引擎） | 維持，M7 檢討 | FFT 量測窗 ±6% 的解析限制 |
| Partial 振幅誤差 | ±3.0 dB（M2 已達成，Phase H 材質修正後重跑 `--amps` 仍 `RESULT: ALL WITHIN TOLERANCE`，`reports/gate_outputs/phase_h_gate_amps.txt`，確認材質阻尼/E 修正不影響 t=0 振幅判定） | ±3.0 dB（M2） | M2 實測後定案 |
| T60 比值 | 0.80–1.25（exit-code 判定） | 0.5–2.0 判定制（M5） | 2026-07-18 月月授權同步至工具實值（收緊方向）；2026-07-17 十個標準 probe measured/model 0.99–1.00；rubber 極短瞬態另列 N/A |
| velocity ×2 電平 | 量測域：基頻窄帶（測得 f0 ±3%，非寬帶）；主張域二分（2026-08-27 月月裁決 (b)）——**固定 tau_c 路徑**（Cimbalom 家族 Cotton/Wood/Metal 檔位、Chromatic 引擎；FM 維持既有豁免）雙重判定數值不變：實測 vs 模型預測 ±1.0 dB，且模型預測自身 \|Δ−6.0206\| ≤ 1.0 dB（物理律上限）；**tau_c(v) 路徑**（Cimbalom/Piano 家族 × Felt 氈槌 = B4 接觸求解器 `HammerImpulse::pianoHammerTauC()`，判域函式 `probe_tauc_velocity_solved()`）6.0206 dB 固定律不再是有效主張（該律是固定接觸時間假設的推論），判定改為實測 vs 模型自身預測 ±1.0 dB（match 容差數值不變、fail-closed）＋ predicted_delta 誠實列印（含相對 6.0206 dB 偏差，資訊性、不判定）；寬帶 delta 僅資訊性列印，不影響判定 | +6.0 ± 1.0 dB 判定制（M1） | 振幅正比力的物理律（20·log10 2 = +6.0206 dB）是逐模態律（`ModalResonator::excite()`），非寬帶頻譜形狀律；2026-07-18 月月授權語意同步為雙重判定；**2026-07-22 月月授權修理：量測域對齊物理律適用範圍（寬帶→基頻窄帶），非容差變更**；round-2 寬帶量測值（piano +7.4373 dB）見 `reports/gate_outputs/deepfix2_gate_full.txt` 存證，本輪起降為資訊性；**2026-07-23 月月正式追認此量測域變更**（round-4 裁決，見 `TODO.md`「2026-07-23 round-4 裁決落地」）；**2026-08-27 月月裁決 (b)：F3 主張域重定義（tau_c(v)/Felt 路徑改為模型自洽判定；容差數值不變、非容差變更；固定 tau_c 路徑檢查一字不動）**——B4 把 Felt 槌 tau_c 換成由 F=K·δ^α 解出的 tau_c(note,v)（力度指數 −0.394～−0.500 隨音高變化）後，6.0206 dB 律的固定接觸時間前提在該路徑不再成立，模型預測偏差隨 α 嚴格單調（piano C2 +6.3／C4 +7.79／C7 +19.12 dB，渲染實測與模型預測吻合 <0.2 dB＝物理事實非 bug）；裁決包 `reports/decision_packets/B4_f3_velocity_ruling.md`，FAIL 存證 `reports/gate_outputs/b4_gate_full_FAIL.txt`＋`b4_f3_alpha_monotonicity.txt`，主張域哨兵兩輪存證 `reports/gate_outputs/b4_f3_redefine_sentinel.txt` |
| 殘差頻譜能量 | 判定制 −60.0 dB re total（2026-07-23 月月批准並完成實作/GATE） | −60.0 dB re total 判定制（M2/F5） | round-2/round-3 實測基線 −74.7～−83.1 dB re total，距門檻留有 ≥14.7 dB 邊際；實作與證據見 `tools/physics_verify.py`、`reports/gate_outputs/deepfix4_*`；**2026-10-02 月月裁決 N3＝A**：量法改 4 項 Blackman-Harris 窗（修正量法、門檻數值不動；R2 說明見 §1 第 2 條），前面的基線是當時 Hann 量法的實測 |
| 休止區 RMS | 無 | ≤ −50 dBFS（M3，含殘響衰減窗） | 待 M3 實測後檢討；2026-07-18 量測法改為逐聲道 RMS 取最大（門檻 −50 dBFS 不變；量測方法變更，非容差變更） |
| 跨引擎等 RMS | 0.2 dB（已達） | 維持 | 2026-06 校準 |
| 決定性 | SHA256 一致（同機） | 跨機：max abs delta ≤ −120 dBFS、delta RMS ≤ −120 dB re signal、spectral ≤ 0.01 dB、peak pitch ≤ 0.01 cents | **2026-08-22 月月登記完成**（`scores/crossplatform_tolerance.json`，裁決「照提案登記」）：依 CI run 32446987833 第一次三平台實測（最差 5 LSB@24bit／−125.8 dB／0.0019 dB／+0.0000c）留餘裕訂定，`cross-platform-compare` 自此轉**阻斷式 GATE**（超標 exit 1）。2026-08-15 工具就位記錄：`tools/crossplatform_verify.py` + CI 三平台矩陣，無登記時 exit 3 UNREGISTERED 只印不判（Rule 2） |
| 旋律 onset 誤差（`melody_verify.py` `ONSET_TOL_S`） | ±10 ms | 維持 | **2026-10-02 月月裁決 Q04=A 補登（數值不變，只補出處）**：C3-b，2026-08-20 月月委託 AI 依推導自定（hop 量化 256/48000＝5.3 ms＋Hann 窗群延遲展幅，推導寫在 `tools/melody_verify.py` 檔頭 Tolerance provenance）；證據 `reports/gate_outputs/l1_l2_l3a_melody_gate.txt`。此前一直在用、但沒登記本表 |
| 量測器自證（`tools/measurement_selfcal.py`，`MAX_ABS_ERROR_CENTS_LIMIT`／`SENSITIVITY_TOL_CENTS`） | ≤1.0 cent＝**strict xfail 判定值**（已知達不到；`tests/test_measurement_selfcal.py` 五條 strict xfail：:195、:216、:238、:260、:298） | 主張域已收窄：持續段 ≤1.18 cent；放鍵／阻尼段約 7.2 cent | **2026-10-02 月月裁決 Q04=A 補登（數值不變，只補出處）**：1.0 cent 是月月 2026-08-30 查核第 5 點訂的；C10（月月 09-10 選 A）把主張域收窄為「量測器已知系統誤差 ≤1.18 cent」（開發 1.1721／hold-out 1.0840），D15（月月 09-15 選 A'）再限定 ≤1.18 cent 只涵蓋持續段、放鍵／阻尼段已知誤差上界約 7.2 cent（開發 5.2304／hold-out 7.2055）；不可宣稱量測器 ≤1 cent。出處 `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.5、`reports/decision_packets/C10_selfcal_domain.zh-TW.md` §7 |
| 外掛 IR−ALGO 殘響響度差（D9c，合成 IR；`audit_repro` CHECK） | \|IR−ALGO\| ≤ 0.25 dB | 維持 | **2026-10-02 月月核准登記（裁決 Q01=B）**：出處 `docs/workcards/WF0914_D9c_ir_makeup_gain.md` §2 第 2 項（:28-30，「0 ± 0.25 dB」）；0.25 dB 取自 D9b 實測的樣本展幅 0.24 dB。現值合成 IR +0.112 dB（`reports/gate_outputs/wf0914_D9c_ir_makeup_gain.txt` §2.5；09-25 ctest 重跑相同），餘裕 0.138 dB。CHECK 由 WF1002-C1 加進 `audit_repro`（以該卡證據為準）。外掛層、屬 §0 效果鏈域外，不是物理主張；對齊參考是 ALGO 預設 room size 0.5、未指定 T60；CI 只有合成 IR（三顆真實 IR 在 gitignored 的 `external_data/`） |

> **~~待月月裁決~~ 已裁（2026-09-25 盤點提出；2026-10-02 月月裁決 Q04=A＋Q01=B 補登上面最後三列，數值都不變、只補出處）**：原註記寫「有兩個實際在用的 GATE 門檻沒有登記在本表——(1) `melody_verify` 的 onset ±10 ms（C3-b，2026-08-20 月月委託 AI 依推導自定，證據 `reports/gate_outputs/l1_l2_l3a_melody_gate.txt`）；(2) 量測器自證 `measurement_selfcal` 的 ≤1.0 cent（月月 2026-08-30 查核第 5 點訂；C10／D15 已收窄主張域，見檔頭補記）。`melody_verify`／`partial_verify` 的 pitch ±5 cent 是沿用本表「f0 誤差」列，不算新容差。要不要把 (1)(2) 補登進本表（數值不變，只補登記與出處），由月月決定。」
> 處理：(1)(2) 已補登；Q01=B 的 0.25 dB 同一步登記；兩處 ±5 cent 已在「f0 誤差（`physics_verify.py`）」列註明沿用。上表其他列數值一字未動。為了不讓 §7 以後的行號位移，這段註記從 5 行壓成 2 行（原 :474-479 的位置現在是三列新登記＋本註記）。

## 7. 狀態更新規則

- 完成 GATE → 更新 §2 表狀態 + 在 `DEVLOG.md` 記一筆（含 GATE 輸出摘要）。
- 本文件的任務勾選框只在 GATE 輸出存在時才能打勾。

---

## 2026-09-25 WF0925 輪落地補記（依 Rule 8；WF0925b-DS 補寫）

> 放在檔尾、不插在檔頭：是為了不讓 `reports/decision_packets/WF0925_open_decisions.zh-TW.md`（Q02 `:161`／`:171`、Q03 `:164`、Q04 `:474-479`、Q19 `:144`）與 `docs/KNOWN_LIMITS_INDEX.zh-TW.md` 引用的本檔行號位移。檔頭「2026-09-07～16」段的引言已加一句指到這裡。
> **git 狀態**：以下全部 staged、未 commit（HEAD 仍 `18430c4`）；commit 切法見 `docs/workcards/WF0925_README.md` §4 與裁決包 Q33。
> 本輪沒有任何卡改渲染輸出（8 首代表曲位元不變 8/8 IDENTICAL，R10 未觸發），沒有新增容差或 GATE 判定門檻；§1 規則原文與 §6 容差表都沒動。
> 證據檔都在 `reports/gate_outputs/`（下表省略這個前綴）；`output/` 開頭的是 gitignored 的稽核產出。

| 項目 | 狀態 | 做了什麼（一行） | 證據 |
|---|---|---|---|
| **E8** 音訊執行緒零配置 | 已落地（WF0925-K1）；「零配置」是 K 稽核的實測，**不是 repo GATE** | 揚琴（含鋼琴）每按一個音都在音訊執行緒建一次 `juce::String`，改成 `CimbalomEngine.h` 的 static 常數；K 稽核第 2 輪把外掛 DLL 的 malloc／calloc／realloc 入口換成計數器，5 種引擎情境 × 8 個 note-on 全部 0 次，負對照每個 note-on 1 次 | `wf0925_K1_summary.txt` 第 1 項；稽核實測 `output/wf0925/K_audit2/alloc/run_current.log`、`run_negative_control.log`；做成正式 GATE 待裁（裁決包 O08） |
| **E9** tail 長度改讀 atomic | 已落地（K1） | `getTailLengthSeconds()` 只讀 20 Hz Timer 在訊息執行緒算好的 atomic 值；HostProbe H8 四個 tail 值改前改後逐字相同（34.4814／178.734／319.848／178.734 s） | `wf0925_K1_summary.txt` 第 2 項；`wf0925_K1_hostprobe.txt` |
| **E14** plugin state 版本欄位 | 已落地（K1） | plugin state 一律寫 `state_version=3`；user preset 格式版本 2，讀到比 2 新的照樣載入、但拒絕覆寫（永久相容包袱的知情確認見裁決包 O14） | `wf0925_K1_summary.txt` 第 3 項；`wf0925_K1_hostprobe.txt` |
| **E15** IRLibrary 損壞修復 | 已落地（K1；期望雜湊出處 K2） | 庫檔雜湊不符就寫暫存檔、驗雜湊、原子替換；`audit_repro` 加 SHA-256 已知答案 3 組＋截半／清成 0 位元組兩種損壞修復情境；"abc" 與 448 位元兩組對過 FIPS 180-2 原文（空字串那組原文沒有，只有 hashlib） | `wf0925_K1_summary.txt` 第 5 項；`wf0925_K2_e15_sources.txt` |
| **D12** 舊鍵斷言 | 已落地（K1） | HostProbe D12 情境 1、2 各加「輸出 state 不含 `reverb_ir_path`」斷言，PASS；情境 3 的產品行為沒動（裁決包 Q10） | `wf0925_K1_summary.txt` 第 4 項；`wf0925_K1_hostprobe.txt` |
| **D9c-guard** 常數釘住 | 已落地（WF0925-K2） | `audit_repro` 加 `kIrWetMakeupGain == 26.9f` 精確相等 CHECK（讀到 26.8999996，PASS）；這是同一個 float 字面值的相等比較，不是容差。「響度差 ≤0.25 dB」的 CHECK 沒加（0.25 dB 沒裁過，裁決包 Q01）；K-02 仍只印數字（0.112 dB）；常數裡約 18.06 dB 綁在 JUCE 的 0.125 正規化上，見 D9 裁決包檔尾 | `wf0925_K2_summary.txt` 第 2 項；`wf0925_integration_raw/04b_audit_repro_direct.txt` |
| **B7-residual** 註解同步 | 已落地（K1；純註解） | `src/physics/HammerImpulse.h` 三處 B7 殘留註解改成「目前沒有呼叫點（B7 09-15 裁決撤回 Path C 欄位），重新接回前先解裁決包 §1.1」；同檔另兩處泛指 call site 的歷史描述（約 :422、:471）不在 K1 範圍，仍待處理 | `wf0925_K1_summary.txt` 第 6 項 |
| **D9c-calib** 對齊參考說明 | 已落地（K1；純說明，數值不變） | `kIrWetMakeupGain` 註解與 D9 裁決包檔尾補「對齊參考＝ALGO 預設 size 0.5、未指定 T60」，其他 size／T60 依 Python 複製版估計差 −1.4～+4.0／−2.4～+5.3 dB（估計，不是對產品 binary 的量測） | `wf0925_K1_summary.txt` 第 6 項；`reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md` 檔尾 |
| **HostProbe 89→215** | 已落地（K1 +17 → 106；K2 +109 → 215） | K2 另把找 `data/materials.json` 改成 cwd → 環境變數 `TSUKI_REPO_ROOT` → exe 所在資料夾往上找，**不必再以 repo 根目錄為 cwd**；K2 的 E16 逐一檢查 27 個工廠 preset（27×4＋1 條負對照） | `wf0925_K2_hostprobe.txt`；整合卡 `wf0925_integration_raw/09_hostprobe_cwd_repo.txt`、`09b_hostprobe_cwd_output_wf0925_INT.txt`（兩次都 215 PASS／0 FAIL） |
| **pytest 270→288** | 已落地（WF0925-P1） | 新基線 288＝282 passed＋1 skipped＋5 xfailed；新增 18 條（selfcal hold-out 釘住 1 條＋`tests/test_stem_stream.py` 17 條），刪除 0 條 | `wf0925_integration_raw/05_pytest.txt`、`05a_pytest_collect_diff.txt` |
| **D13 同步** | 完成（K1） | `src/physics/PlateModel.h` 檔頭與 `scores/examples/water_gong_free.score.json` 的 `meta.description` 帶上「不是乳突鑼」的主張域；WAV 8/8 位元不變 | `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §1 同步記錄；`wf0925_K1_bit_identity.txt` |
| **D16** 弱基頻零點地圖 | 研究完成（WF0925-N1），**待月月裁決 Q15** | 給愛麗絲 16 顆 FAIL 16/16 落在槌力脈衝頻譜零點（基頻多被壓 14.9～24.5 dB）；真正分開 PASS／FAIL 的是基頻絕對音量（描述用、非 GATE）；商品只有給愛麗絲鋼琴版受影響。A14 仍開放 | `reports/weak_fundamental_null_map_2026-09-25.zh-TW.md`；`wf0925_N1_fur_elise_validation.txt` |
| **D11-F5** 根因 | 研究完成（WF0925-F5）；**月月 10-02 裁 Q16＝D**（維持現狀＋研究卡，WF1002-R 查到候選不比現行像真鋼琴）；「F5 PASS 依賴 0.8 mm 探針」已由 N3＝A 換窗量法解除（1.0 mm −59.47→−82.73 dB PASS，`wf1002b_T_f5_method.txt`） | 候選 patch 下 F5 piano −63.9 → −58.5 dB 全部來自 C4 基頻 T60 變短（4.1425 → 2.6733 s）；另發現現行引擎只把 F5 探針弦徑 0.8 mm 改成 1.0 mm 就是 −59.5 dB FAIL | `reports/d11_f5_root_cause_2026-09-25.zh-TW.md`；`reports/decision_packets/D11_string_scale_candidate.zh-TW.md` 檔尾；`wf0925_F5_*.txt` |

整合卡（WF0925-INT）對 staged 樹重建 `build\` 跑全套，10 條 GATE 全綠：ctest 4/4（AuditTest 110 PASS／0 FAIL）、pytest 282 passed＋1 skipped＋5 xfailed、`physics_verify.py --full` NO CHECKED FAILURES、`--selftest` 13/13、`verify_score.py --all` 75/75（1 項既有豁免）、HostProbe 215／0、位元不變 8/8 IDENTICAL。證據 `wf0925_INTEGRATION.txt`、`wf0925_integration_raw/`。

---

## 2026-10-02 WF1002 輪（月月裁決落地；依 Rule 8）

> 月月 2026-10-02 裁決「照 Fable 的說法做」：裁決包 `reports/decision_packets/WF0925_open_decisions.zh-TW.md` 38 題，以 `docs/workcards/WF1002_README.md` §1 裁定表為唯一依據。**本輪是月月第一次授權改 §1 規則原文與 §6 容差表**：§1 改 R6（Q02=A）、R7（Q03=A）；§6 補登 onset ±10 ms、量測器自證 1.0 cent（Q04=A）、D9c IR−ALGO ≤0.25 dB（Q01=B，10-02 核准），f0 列註明兩處 ±5 cent 沿用（Q04=A）——每處都留「2026-10-02 月月裁決 Qxx」註記，舊文用刪除線或引述保留；§6 既有數值一字未動。主張域（Q08 B、Q09 B＋Q09c B、Q17 A、Q19 C）升格寫在 `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §2～§10（C5 弦長／弦徑在 §11 註明等 Q16 研究卡，未升格）；CI Linux leg label 改 `ubuntu-24.04-gcc`（Q13=A）。C++ lane（Q01/Q01b/Q05/Q06/Q07/Q09 實測/Q10/Q17 註解/Q38 字串）與研究卡的落地狀態以各卡證據為準。文件 lane 證據 `reports/gate_outputs/wf1002_D_changes.txt`。**git 狀態：本輪改動未 commit；稽核 PASS 後才 staged（R7 新字面）。**
