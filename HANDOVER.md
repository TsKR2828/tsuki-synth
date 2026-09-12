# TsukiSynth 交接文件

> 交接視窗：2026-09-09（09-11 補記四裁決落地）　分支：`fix/deep-physics-audit-20260716`
> （HEAD `98f346f`，`main` = `34aa904` 同步至 09-07；**工作樹 250+ 個檔案 staged 未 commit、零 unstaged**，見 §1）
>
> **2026-09-10～11 月月四裁決已全部落地**：C10 選 A（主張域收窄：量測器含 ≤1.18 cent 已知誤差，不可宣稱 ≤1 cent；C10C 工具部分入庫、NLS 候選存 patch）／
> **A14 B-2 patch 已 apply**（Opus 稽核 PASS；位元基準改 `sha256_before_post_a14.txt`）／月光母帶等換源後一起出／兩封信草稿在 `docs/correspondence/`（月月寄）。
> §5 以下保留裁決前說明供追溯。
> **新 session 請先讀完這一頁再動手。** 待辦細節在 `TODO.md` 開頭「待辦總表」與「三輪 Workflow 快照」；
> 歷史決策在 `DEVLOG.md`（09-07～09 段）；施工卡與流程規約在 `docs/workcards/WF0907_README.md`。

---

## 0. 一句話現況

**09-07～09 三輪 Dynamic Workflow（71 個 agent）把稽核清單清空、F-03 落地、D8 解除、A13/A14/F-03/K-02 代決完成；
全部成果 staged 未 commit，等月月審 `git diff --cached` 並裁決 §5 的四件事。**

## 1. 立刻要知道的四件事

1. **工作樹狀態**：`git diff --cached --stat` ≈ 233 檔、+39k 行。**staged = Opus 稽核親自重跑 GATE 通過**（規劃者文件 HANDOVER/TODO/DEVLOG/施工卡/證據檔亦 staged）。
   unstaged 只剩 0 個實質改動；`reports/c10c_nls_candidate.patch` 是 C10C 未落地候選（見 §5-1）。
   **R7 照舊**：沒有月月明示不 commit / 不 push。月月授權後的建議 commit 切法：(a) WF0907 工程批、(b) WF0908 F-03+P1+E10b 批、(c) WF0909 D8+P4b 批、(d) 研究文件與裁決包、(e) 施工卡與證據——或一次一個 commit 也可以。
2. **等月月放行的 patch**：`reports/a14_tauc_keytrack_b2.patch`（A14 B-2，Rule 10）——`git apply` 即落地，只影響 5 個鋼琴 score，報告 `reports/a14_tauc_keytrack_before_after.md`。
3. **月月是聾人開發者，全程免耳驗收。** 物理/位置正確性由 GATE 鏈負責，美學驗收由外部專業人士。corpus **75 檔**；8 首位元不變基準自 09-09 起用 `reports/gate_outputs/b6_method/sha256_before_post_d8.txt`（D8 改了兩首月光空靈鼓相關曲目）。
4. **系統部署的 VST3 仍是 0.2.0（7/12）**——F-03、tail length、glide 逐取樣等 plugin 側修正要讓 Cubase 看到，月月需以管理員權限把 `build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3` 覆蓋到 `C:\Program Files\Common Files\VST3\`。

## 2. 這個專案是什麼

聾人使用者（月月）+ AI 不靠聽感、靠物理理論精確模擬聲音的 JUCE 8 VST3 合成器。
**唯一驗收依據 `ROADMAP_PHYSICS.md`**，§1 十條強制規則開工前必讀（R1 只認 GATE 輸出／R2 禁調寬容差／R3 禁縮 GATE／R4 禁未溯源常數／R6 改 src 必跑 `--full`＋三 build／R7 不 commit／R10 渲染改變要前後對照）。
**X4 規約**：跑 `ctest` 前必先重建測試 target（現為五個：Audit/Tuner/PhysicsModels/SpectrumView/HostProbe）。
四個引擎：Cimbalom/Piano（弦）、Tongue Drum（梁）、Water Gong（板）、FM Piano（域外）。

## 3. 三輪工程落地了什麼（全部 staged）

| 卡 | 白話 | 證據 |
|---|---|---|
| E1 | CI 從 5 檔白名單改跑全套 pytest；pin pytest/mido | `wf0907_E1_ci.txt` |
| E5 | host 問「聲音多長」改由物理引擎自報 worst-case T60（3.45 s → 34/179/320 s），DAW bounce 不再截尾 | `wf0907_E5_tail.txt` |
| E8 | score 合法性單一真相：schema 自動走訪 388 突變體，C++ `--validate` 從 22 條不一致修到 0 | `wf0907_E8_schema.txt` |
| E9 | `--dump-modes` 支援 layered score（三檔 3/4/260 事件） | `wf0907_E9_layered.txt` |
| E7 | K-03 超 maxBlock 分塊（位元等價）；K-02 量到 IR 比 ALGO **小 28.5 dB** | `wf0907_E7_reverb.txt`、裁決包 K02 |
| C11/C12 | stem_verify 拒答理由/直方圖；`--analysis-dry` 預設 + provenance 三個 sha256 | `wf0907_C11/C12_*.txt` |
| C10 | `measure_pitch_cents()` 抽出（位元不變）+ 合成哨兵：**1.1721 c > 1 c** | `wf0907_C10_selfcal.txt` |
| E10/E10b | H6 五種 block size 位元相同；水鑼 glide 逐取樣（原本逐 block 階梯差 +2.6 dB）；H7 user preset harness（`src/ParameterLayout.h`） | `wf0907_E10_*.txt`、`wf0908_E10b_*.txt` |
| **P3 F-03** | 受管理 IR 庫 `src/IRLibrary.h`（sha256 去重）、preset 存 `reverb_ir{kind,sha256,original_name}`、缺檔三態、`getIRStatus()` 單一真相、HostProbe 67 PASS | `wf0908_P3_f03.txt` |
| P1 | `tools/partial_verify.py`：partial 頻率內部一致性（±5 c）+ C13 `pitch_via_partials_*`；`gate_ready=false` | `wf0908_P1_partial.txt` |
| P2 | A14 B-2 τc 音高律 patch（**未落地**，見 §5-2） | `reports/a14_tauc_keytrack_before_after.md` |
| P4/P4b | A8 引用更正：TU Berlin 半徑 2.06 m 非 1.05、授權 BY-NC-SA、Sinin 消音室、HammerImpulse 檔頭出處改 Woodhouse | `wf0908_P4_a8.txt`、`wf0909_P4b_citation.txt` |
| **D8** | 兩首月光空靈鼓相關 score `exciter: finger → wood_mallet`（月月裁決）；200 Hz 以下能量 97% → 18%、斜率 41 → 5.5 dB | `reports/d8_tongue_drum_exciter_before_after.md` |
| 整合 ×3 | 每輪末重建 `build/`：ctest / pytest 267 / `--full` NO CHECKED FAILURES / HostProbe / 位元不變全綠 | `wf090{7,8,9}_INTEGRATION.txt` |

## 4. 驗證鏈現況

```
MIDI 原譜 ──① score_vs_midi_verify──> score.json ──② melody_verify──> WAV
                                          │                            │
                                          └──③ verify_score (75 檔) ───┘
                                                                       │
        ④ HostProbe(H1–H8) / ⑤ Cubase 實測 / ⑥ piano-roll 影片 / ⑦ stem_verify / ⑧ partial_verify ─┘
```

- ② `melody_verify`：onset ±10 ms / pitch ±5 c（既有裁定）。**量測器自證 ≤1 c 尚未達成**（1.1721 c；B 路線兩家族六候選試完，見 §5-1）。
- ⑦ `stem_verify`：乾聲分軌預設、拒答理由、provenance。**已知**：905 事件全曲記憶體 >28 GB（TODO D14），`--limit 300` 可跑。
- ⑧ `partial_verify`：informational；振幅只記錄不判定；**不可宣稱「泛音已驗證」**。
- ④ HostProbe：H6 變動 block size 位元相同（含水鑼 glide）、H7 user preset 三情境（F-03 落地後為硬 CHECK）、H8 tail ≥ 引擎 worst-case。

## 5. 等月月裁決（四件）——**2026-09-10 月月已全部裁決**：1 選 A（收窄主張域，落地中）／2 放行（patch apply 中）／3 母帶等換源後一起出／4 兩封信要寫（草稿在 `docs/correspondence/`，由月月寄）。以下保留裁決前的說明。

1. **C10 量測器自證**：B 路線已在 STFT 家族（5 候選，其中柔化質心被稽核抓到假改善撤回）與時域 NLS（合成關卡 hold-out 0.08 c 但真實渲染更差）試完。
   **建議改選 A（收窄主張域）**，措辭草案 `reports/decision_packets/C10_selfcal_domain.zh-TW.md` §6.4。
   更上層發現：合成哨兵的訊號模型與 NLS 相同（套套邏輯），現行 1-cent 門檻本身不足以認證估計器——要補放鍵/阻尼段語料（會改比對數字、不改門檻）。
   C10C 的全部改動（含增益保真升 GATE、course 檢查、`measure_pitch_cents_nls()` 候選）在 `reports/c10c_nls_candidate.patch`，選 A 後可另開小卡只落地工具部分。
2. **A14 B-2 patch 放行**（Rule 10）：`git apply reports/a14_tauc_keytrack_b2.patch`。
3. **月光空靈鼓母帶重出**：D8 只改了 score，`exports/products/moonlight_batch1/` 母帶仍是舊渲染；且月光授權（CC BY-SA）疑慮未解，仍不可上架。
4. **兩封信由月月自行決定**：TU Berlin（要商業授權）、Iowa MIS（器材對應）。AI 不代發。

## 6. 規劃者代決紀錄（月月 09-07 委託；可推翻）

| 項 | 決定 | 依據 |
|---|---|---|
| A13 | B+：只驗 partial 頻率（±5 c 既有）、不立振幅 GATE、B 對照寫報告 | `A13_partial_gate_domain` |
| A14 | 引擎缺陷：τc 音高律太平（k=0.212），基頻落半正弦力脈衝零點（G5 −33.7 dB）；B-2 先做、B-1 等文獻 | `A14_weak_fundamental_ruling` |
| F-03 | B＋（受管理 IR 庫＋工廠/使用者分流）＋缺檔三態；不得沿用 instance 上一個 IR | `F03_IR_PRESET_RECALL` §7–8 |
| K-02 | C 維持現狀（A 更糟、B 動全 corpus）；另立 D9「IR 載入響度對齊」 | `K02_reverb_wet_scale` §5 |
| A8 | 私下對照參考（月月 09-09：無可商用校準資料集就私下參考）；補充 Weinzierl 2018／Iowa 泰國鑼 | `EXTERNAL_DATASET_A8/ALTERNATIVES/SUPPLEMENT` |

## 7. 新登記的缺口（D 類）

D9 IR 載入響度對齊（等真實 IR 檔量測）／D10 B-1 真槌力譜滾降文獻／D11 弦長 0.35 m@A4 與 corpus 固定弦徑造成 B 偏高 2.4～5.2×（R10 全 corpus）／
D12 舊 DAW state `reverb_ir_path` 無遷移／D13 水鑼引擎在 2.0× 無 partial 而真泰國鑼最強泛音在 2.000×（自由邊平板 vs 乳突鑼）／
D14 stem_verify 900+ 事件記憶體線性成長 >28 GB／D15 合成哨兵缺放鍵/阻尼段語料。

## 8. 檔案地圖

| 要找什麼 | 去哪 |
|---|---|
| 當前待辦 + 三輪快照 | `TODO.md` 開頭 |
| 流程規約（lane、build-wf、X4、位元不變基準、稽核 stage 規則） | `docs/workcards/WF0907_README.md`、`WF0907_R_research_common.md` |
| 施工卡 | `docs/workcards/WF0907_*.md`、`WF0908_*.md`、`WF0909_*.md` |
| 裁決包 | `reports/decision_packets/`（A13/A14/F03/K02/C10/D8） |
| Rule 10 報告 | `reports/a14_tauc_keytrack_before_after.md`（未落地）、`reports/d8_tongue_drum_exciter_before_after.md`（已落地） |
| 稽核診斷（三病根） | `docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.zh-TW.md`（§4 全部已修或已裁決） |
| 免耳驗證設計 + 主張域 + 量測器自證 | `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §7–§10 |
| 外部資料集 | `docs/EXTERNAL_DATASET_A8.zh-TW.md`、`_ALTERNATIVES`、`_SUPPLEMENT`；資料在 `external_data/`（gitignore） |
| B7 Phase 0 資料 | `docs/B7_PHASE0_DATA.zh-TW.md`、`docs/workcards/B7.md` |
| UI 設計輸入 | **`docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md` v1.1（09-09 已同步 F-03/D8，可送設計端）** |
| GATE 證據 | `reports/gate_outputs/wf090{7,8,9}_*.txt`、`*_INTEGRATION.txt` |
| 歷史決策 | `DEVLOG.md` |

## 9. 操作備忘

- 建置：`cmake -B build -DCMAKE_BUILD_TYPE=Release -DTSUKI_BUILD_TESTS=ON`；CLI `build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`
- 全套 GATE：三 target + 五測試 target → `ctest` → `python -m pytest tests -q`（267 passed）→ `python tools/physics_verify.py --full` → HostProbe → 位元不變 `reports/gate_outputs/wf0907_method/render_wf_scores.py` 對 `sha256_before_post_d8.txt`
- 分軌：`python tools/stem_verify.py <score> [--limit N] [--jobs N] [--json out]`（乾聲預設）；partial：`python tools/partial_verify.py <stem 報告.json>`
- 量測器自證：`python tools/measurement_selfcal.py [--holdout]`（現況 exit 1，1.1721 c）
- HostProbe：`build/Release/TsukiSynthHostProbe.exe <.vst3> <outdir>`
- ffmpeg：`C:\Users\admin\Desktop\Tools\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe`

## 10. 工作方式備忘（三輪的教訓）

- **規劃者畫地圖、Sonnet 工兵、Opus 稽核親自重跑**——這套三輪抓到：柔化估計器假改善、研究文件編出來的資料集標題、規劃者自己寫錯的卡文（P4 第 3 項）。**不要跳過稽核層。**
- **跨 lane 污染**：同一工作樹並行時，未完成卡的新測試檔會弄紅別卡的全套 pytest。全套 pytest 應放整合卡；工兵誠實回 RED 是對的。
- **卡文可能錯**：工兵發現卡與 repo 內更新的查證矛盾時停下回報（P4 第 3 項）是正確行為。
- **合成哨兵的盲點**：哨兵語料若與候選估計器同模型，會套套邏輯地全過；必須加「期望值固定、真值偏離」與真實音檔兩條軸。
- session limit 中斷用 `resumeFromRunId` 續跑；被中斷的卡用接手說明讓工兵先看 diff 再重跑 GATE。
- 月月的偏好不變：不腦補、查不到就說查不到、需要裁決做成看數字就能選的裁決包、白話到位。
