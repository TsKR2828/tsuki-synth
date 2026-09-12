# WF0908-P2：A14 B-2 —— 鋼琴氈槌 τc 音高律錨定到量測曲線（Rule 10 卡，**不落地、出前後對照報告**）

> lane：C++　工兵：Sonnet　共同規約：`WF0907_README.md`（build-wf、X4、位元不變腳本）
> 依據：`reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md` §3.2–3.5、§4 選項 B、裁決記錄。

## 0. 一句話目標

`HammerImpulse::pianoHammerTauC()` 現在的音高律（由 K/α/質量錨點推出，等效 k=0.212）比文獻量測（A0 4 ms → C8 <1 ms）平，
高音 τc 太長，基頻掉進力脈衝零點。改成：**音高形狀用本檔已溯源的量測擬合 `keytrackScale()`（k=0.32，A4=2.0 ms），力度形狀保留 B4 的 `g(note,v)/g(note,0.5)`**。
**這張卡的合法終點是 BLOCKED(R10)**：程式改好、GATE 全跑、前後對照報告寫好，**不 stage src/**，等月月放行。

## 1. 現況（規劃者已核實，`src/physics/HammerImpulse.h`）

- `keytrackScale(midiNote)`：`tau_c ∝ f^(-0.32)`，錨 A4=1.0，clamp [0.4, 2.6]，註解引 Askenfelt & Jansson（A0 4 ms → C8 ~0.8 ms）。**這是既有、已溯源的形狀。**
- `pianoHammerTauC(midiNote, v)` = `kTauCFelt * g(note,v) / g(69,0.5)`，`g = [m/K]^(1/(α+1)) * v^(2/(α+1)-1)`——音高與力度**混在同一個 g 裡**。
- 呼叫點：`CimbalomEngine.h` 兩處（Felt 分支，`pianoHammerTauC(midiNoteNumber, velocity)` 與 `(midiNoteNumber, 0.5f)` 的 tauCRef）。非 Felt 走 `tauCForNote()`，不動。
- 單元測試：`tests/physics_models_repro.cpp` 有 B4 的 τc 測試（先 grep `pianoHammerTauC`），錨點 A4/v=0.5 = 2.0 ms 必須維持。
- A14 §3.2 的 x = 2·f₁·τc 表：G5 現況 2.910、G6 5.063、D7 7.120。

## 2. 設計（照做）

```
tau_c_piano(note, v) = kTauCFelt * keytrackScale(note) * [ g(note, v) / g(note, 0.5) ]
```
- A4/v=0.5 → 2.0 ms 不變（`keytrackScale(69)=1`、比值=1）。
- 音高形狀 = 量測擬合；力度形狀 = B4 的物理推導（指數隨 α(note) 變：−0.394/−0.429/−0.500）。
- clamp `kPianoTauCMinS/MaxS` 保留。**不新增常數、不改任何錨點表。**
- 註解要寫清楚：為什麼 K/α/m 推出的音高形狀被量測曲線取代（A14 §3.3：k=0.212 vs 文獻 ≈0.276–0.32；且 g 的音高形狀只在 x<1 的半正弦模型下有意義）。

## 3. 步驟

1. 先在 `build-wf` 跑 baseline（README §3 位元不變腳本，8/8 IDENTICAL）。
2. 改 `pianoHammerTauC()`；更新/新增單元測試：A4 錨點 2.0 ms 不變；C8 τc < 1 ms；等效 k 在 C2→C7 為 0.32±0.01；力度律在固定音高下與 B4 舊版**位元相同**（因為只是乘上一個與 v 無關的因子——證明方式：`new(note,v)/new(note,0.5) == old(note,v)/old(note,0.5)`，浮點容許 1e-6 相對誤差，這不是 §6 容差是單元測試的數值等價檢查）。
3. 三 build + 測試 target（X4）+ ctest + `--full --cli build-wf...`。**F3 velocity 判定**（B4 重定義後的自洽主張）必須仍 PASS；若 FAIL → 停，回報數字。
4. **前後對照量測**（用 A14 附錄 B 的重跑法，腳本在 `output/wf0907/R2/`，複製到 `reports/gate_outputs/wf0908_method/`）：
   G5/G6/D7 的 x、H(f₁)、第2−第1 partial dB；MIDI 37→87 峰值/RMS 斜率；noteComp 飽和表（MIDI 61–98）。
5. 位元不變腳本：預期 **7/8 IDENTICAL、只有 `physical_piano` 改變**；任何其他一首改變 = 外溢 = RED。
6. corpus 受影響 5 檔（`fur_elise_complete`、`physical_piano`、`akashic_action_001`、`ocean_action_001`、`ai_radiance_m3`）各跑 `verify_score.py --cli build-wf...`，並對這 5 檔做 Rule 10 指標（RMS / 頻譜質心 / T60 / f0，格式照 `reports/b4_hammer_contact_before_after.md`）。
7. 寫 `reports/a14_tauc_keytrack_before_after.md`（§0 白話導讀 + 七項/八項齊全，格式照 B4 報告）。
8. **把改動存成 patch、把工作樹還原**（讓後面的卡與整合 GATE 在未落地的樹上跑）：
   `git diff -- src/physics/HammerImpulse.h tests/physics_models_repro.cpp > reports/a14_tauc_keytrack_b2.patch`；
   然後用 `git show :src/physics/HammerImpulse.h > src/physics/HammerImpulse.h`（index 版本，同法還原測試檔）還原——**不是 git checkout**；
   重建 build-wf 三 target + 測試 target，再跑一次位元不變 → 必須回到 **8/8 IDENTICAL**（證明樹已還原）。
   patch 要能 `git apply --check` 通過（證據檔貼結果）。
9. 回報 **status=BLOCKED**，`open_items` 第一條寫「等月月 Rule 10 放行：`git apply reports/a14_tauc_keytrack_b2.patch`」。
   稽核 PASS 時 stage 的是 patch、報告、證據檔、method 腳本（src 已還原，不在 diff 裡）。

## 4. 禁止

- 不動 `forceSpectrumMagnitude()`、`keytrackScale()`、`tauCForNote()`、錨點表、clamp（影響會炸到全部樂器）。
- 不 stage `src/`（稽核 PASS 時只 stage 報告、測試、證據檔；src 留 unstaged 給月月）。
- 不調任何容差（F3 若破就是破）。

## 5. GATE（輸出到 `reports/gate_outputs/wf0908_P2_tauc.txt`）

1. baseline 8/8；改後 7/8 + 只有 physical_piano 變。2. ctest 全綠、`--full` NO CHECKED FAILURES。3. 單元測試新增項全 PASS。
4. 前後對照數字表齊全；報告存在。5. `python -m pytest tests -q` 全綠。6. `git diff --stat` 只含 `src/physics/HammerImpulse.h`、`tests/physics_models_repro.cpp`、報告、證據檔、method 腳本。

---

## 落地記錄（2026-09-10～11）

- 2026-09-10 月月裁決 **放行**（Rule 10）。`git apply reports/a14_tauc_keytrack_b2.patch` 已執行，`src/physics/HammerImpulse.h` 與 `tests/physics_models_repro.cpp` 已 staged。
- GATE（工兵 + Opus 稽核各跑一次，皆綠）：ctest 4/4、§A14-1～4 單元測試 PASS（C8 τc = 0.973 ms、C2→C7 k = 0.32）、`--full` NO CHECKED FAILURES（F3 piano PASS）、pytest 263 passed、HostProbe 0 failures、受影響 5 檔 verify_score 5/5。
- 位元不變：對 `sha256_before_post_d8.txt` 7/8，只有 `physical_piano` 607d0d3b… → 1233b53f…（與報告事前值一致）；新基準 `sha256_before_post_a14.txt` 8/8。
- 稽核牙齒：把公式連分母一起還原成 B4 舊版，`physical_piano` sha 精準回到 607d0d3b…；單拿掉 keytrackScale 乘法則得另一值（分母已改為同音 v=0.5），證明兩處改動都被位元不變抓得到。
- 證據：`reports/gate_outputs/wf0910_A14_apply.txt`、`wf0910_A14_apply_AUDIT.txt`。本卡 §0/§4 的「BLOCKED／不 stage src」是放行前的規定，自此失效。
