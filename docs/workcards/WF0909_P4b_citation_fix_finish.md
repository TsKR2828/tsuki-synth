# WF0909-P4b：補完 A8 引用更正（P4 第 3 項改用已查證版本）＋ B7.md §4.6 ＋ HammerImpulse 檔頭出處

> lane：C++（碰 `src/` 註解 → 位元不變）　工兵：Sonnet　共同規約：`WF0907_README.md`
> 背景：WF0908-P4 第 1、2 項已完成（`docs/EXTERNAL_ANCHOR_SOURCES.md`、`src/physics/RadiationModel.h` 註解，**目前 unstaged、未稽核**）；
> 第 3 項卡上文字有誤（規劃者寫「兩篇皆無 M」，但 `docs/B7_PHASE0_DATA.zh-TW.md` C7/C9/C12 已查到 arXiv:1210.5688 有 `M = 9 kg`），工兵正確拒寫。本卡用查證版本補完。

## 1. 要做的（全部是文字／註解）

1. **`docs/RADIATION_POWER_SOURCES.md` §5**（L230 起「對 Phase 1 的具體建議」，含 `S = M/(ρh)` 反推建議那段）加一段「2026-09-09 補記」，內容**照 `B7_PHASE0_DATA.zh-TW.md` C7/C9/C12 與其「C7/C9 更正說明」抄**，重點兩點：
   (a) `M` 有出處：Ege & Boutillon arXiv:1210.5688「`Lx = 1.39 m, Ly = 0.91 m and total mass M = 9 kg`」，且 arXiv:1210.5109 定義 `M` 為含肋條、琴橋、撐條的整塊音板質量；
   (b) 因此**不可**用生雲杉密度 `ρ≈400`、`h=8 mm` 反推面積（會高估約 2.22 倍，隱含等效體密度 889 kg/m³）；直立琴可直接用 `Lx·Ly = 1.2649 m²`，平台琴仍查無 → 反推路線「不必要／不適用」而非「不可行」。
   每句附 B7_PHASE0_DATA 的列號（C7/C9/C12）當內部出處。
2. **`docs/workcards/B7.md`** L87 表格列與 L237/L239（§4.6）：「r=1.05 m，EXTERNAL_ANCHOR_SOURCES.md §1 慣例」改為「r=1.05 m 是本專案自訂觀測距離（`RadiationModel.h::kMeasurementRadiusM`，DECIDED CONVENTION）；外部資料庫實際半徑 2.06 m，兩者無關」。L10/L23 的「1.05 m 處」保留（那是本專案觀測點的敘述）。
3. **`src/physics/HammerImpulse.h`** 檔頭 L10「接觸力近似半正弦脈衝（Chaigne & Askenfelt 1994, …）」：A14 附錄查證該文**明文反對**半正弦假設，正確出處為 Woodhouse《Euphonics》§2.2.6／§12.1.2（見 `reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md` 附錄「2026-09-08 增補」）。只改這段註解的出處與措辭；L38、L186 兩處提到 Chaigne & Askenfelt 的**先讀上下文**，若是「軟氈槌數值引用」（非半正弦主張）就不動。**數值零改動。**
4. 一併把 P4 已完成的兩檔納入本卡稽核與 stage。

## 2. GATE（`reports/gate_outputs/wf0909_P4b_citation.txt`）
1. build-wf 三 target exit 0；位元不變 **8/8 IDENTICAL**（本卡在 D8 之前或之後跑都要對基準說明：若 D8 已先落地，用 `sha256_before_post_d8.txt`，否則用 `sha256_before.txt`——兩檔都比，把結果寫清楚）；ctest（X4）。
2. `grep -n '1.05' docs/EXTERNAL_ANCHOR_SOURCES.md docs/workcards/B7.md` 每一處都附自訂觀測距離說明或屬本專案觀測點敘述。
3. `git diff --stat`（unstaged）只含：`docs/EXTERNAL_ANCHOR_SOURCES.md`、`src/physics/RadiationModel.h`、`docs/RADIATION_POWER_SOURCES.md`、`docs/workcards/B7.md`、`src/physics/HammerImpulse.h`、證據檔。
