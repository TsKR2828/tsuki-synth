# 施工卡 WF0914-B7P1：B7 Phase 1 力鏈組裝（純 --dump-modes 診斷路徑）

> lane：C++（`build-wf\`）　前置：WF0914-B7P0 已 PASS（兩份溯源文件已存在）
> 先讀：`WF0914_README.md`、`WF0907_README.md`、**`docs/workcards/B7.md` 全文（§3–§8、§11、§12 逐字）**、
> `docs/HAMMER_VELOCITY_SOURCES.md`、`docs/RADIATION_POWER_SOURCES.md` §8、
> `src/physics/HammerImpulse.h`、`src/physics/RadiationModel.h`、`src/score/ScoreRenderer.h::dumpModes()`。

## 0. 一句話目標

照 B7.md §4/§5/§6 Phase 1 實作力鏈：`HammerImpulse.h` 新增 `hammerVelocityMps()` 與
`hertzPeakForceNewtons()`、`RadiationModel.h` 新增力鏈組裝、`dumpModes()` 新增 Path C 欄位
（`"absolute_pressure_per_force_firstprinciples_c"` + `acoustic_transfer_c[]`，僅 Cimbalom/Piano + Felt），
**不碰 `render()`/`renderEvent()`、不碰 `specimen_verify.py`、不碰 B6 既有欄位**。§7 五條測試全加。

## 1. 兩個規劃者代決（依月月 09-14「B7 開工」授權；工兵照做並在報告記錄，月月可推翻）

### 1.1 velocity proxy → MIDI 的換算

物理函式一律以**真實 MIDI 0–127** 為輸入：`hammerVelocityMps(float midiVelocity /* 0–127 */)`。
proxy 換算只發生在 `dumpModes()` 呼叫端。**動工前先查證**：
1. 讀 `src/score/ScoreParser.h`（與 schema）確認 score `velocity` 欄位的登記語意；
2. 讀轉譜器那條 `/90` 曲線的所在與用途（它是轉譜端響度曲線還是 score 語意的一部分）。
**代決預設**：若 score 語意是「正規化 MIDI」（v = MIDI/127），呼叫端用 `velocity * 127.0f`，
程式註解寫明「規劃者代決 2026-09-14：proxy×127；/90 曲線屬轉譜端，非 score 語意；月月可推翻」。
若查證結果與此矛盾（score 語意根本不是正規化 MIDI）→ **不要硬套**，status=BLOCKED 回報實際讀到的定義。

### 1.2 音板輻射面積 S（條件式，兩分支都合法）

動工時先查證：`RadiationModel.h` 現行音板參數（D、ρs、h、fc 的來源常數）是否溯源自
Ege/Boutillon **直立琴**論文（讀檔頭引用與 `RADIATION_POWER_SOURCES.md` §1–§2 的出處鏈）。
- **是** → 走 B7.md §4.5 警告的路線 1：本卡目標樂器**明確寫死為直立琴**（與既有音板參數同一台琴、
  同一參數族，一致性成立），`S = 1.265 m²`，程式註解標「Atlas 直立琴 0.91×1.39 m 相乘，
  乘法是本專案做的；目標琴種=直立琴（與音板參數同源）；平台琴不得沿用」。完成報告明寫這個判定與證據。
- **否**（參數來源不是那台直立琴，或混源）→ `S` 維持查無：§4.5–4.6 標 `UNVERIFIED`，
  Path C 兩個欄位**不輸出**（fail-closed，B7.md §5），力鏈只落地到 §4.4 的 `W_bridge`
  （以獨立診斷欄位輸出 `"bridge_power_firstprinciples_c"` 供 Phase 3 部分比對），報告明寫卡點。

## 2. 實作邊界（B7.md §3 的「不要碰」全數生效）

- 不動 B4/B1/B6 既有函式一個字元；新函式為純函式。
- `E_mode(f)` 用真實單位從 `F_peak` 重算（B7.md §4.4），選用的脈衝譜離散化方式在報告寫明理由。
- δ_max/F_peak 推導照 §4.3，註解標「推導自能量守恆，非逐字引用」＋固定接觸點簡化聲明。
- clamp 體例比照 `interpAnchorsFlat()`：MIDI <20 → 0.18 m/s、>120 → 6.8 m/s（出處見 HAMMER_VELOCITY_SOURCES）。

## 3. 測試（`tests/physics_models_repro.cpp`，B7.md §7 五條照單全收）

1. 槌速映射範圍＋單調性；2. 峰值力能量守恆自洽（數值積分誤差 <1e-3）；
3. 漏乘 `(alpha+1)` 反例可辨識；4. `W_rad ≤ W_bridge` 守恆不等式；
5. Path B/C 欄位互不干擾哨兵。（若走 §1.2 否分支，測試 4/5 改為對 `W_bridge` 欄位的等價哨兵，報告寫明。）

## 4. GATE（B7.md §8 全表，build-wf lane）

X4 規約：ctest 前先重建**五個**測試 target。Python GATE 一律 `--cli build-wf\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe`。

```
python tools/physics_verify.py --full          # 動工前基線 + 完工後，兩份都存證據
cmake --build build-wf ...（三 build target + 五測試 target）
ctest --test-dir build-wf -C Release --output-on-failure
python tools/physics_verify.py --selftest
python tools/verify_score.py --all --cli ...   # 75/75 或既有豁免不變
python reports/gate_outputs/wf0907_method/render_wf_scores.py --cli ...
#   對 sha256_before_post_a14.txt，期望 8/8 IDENTICAL（本卡只進 dump-modes，任何 SHA 變化=BLOCKED）
```

證據存 `reports/gate_outputs/wf0914_B7P1_*.txt`。完成定義照 B7.md §10「Phase 1 完成」段；
文件同步（ROADMAP_PHYSICS.md/TODO.md，Rule 8）標 `In progress`，列 (a)(b) 為剩餘項。
