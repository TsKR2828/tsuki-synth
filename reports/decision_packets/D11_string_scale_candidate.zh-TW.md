# D-11 裁決包：真實鋼琴弦長/弦徑逐八度查表候選修正，是否落地？

> 工作卡：`docs/workcards/WF0914_D11_string_scale.md`（C++ lane，執行 Sonnet）
> 日期：2026-09-15（稽核打回一輪後補齊，見 `reports/d11_string_scale_before_after.md` 開頭修訂記錄）
> 完整前後對照與原始數字：`reports/d11_string_scale_before_after.md`（本裁決包只摘要三個選項，
> 細節/出處/GATE 結果一律以那份報告為準）
> **本卡未落地**：`src/physics/StringModel.h`／`src/engines/CimbalomEngine.h`／
> `tools/physics_verify.py` 的候選改動已 patch 化存檔（`reports/d11_string_scale_candidate.patch`），
> 工作樹逐位元還原（`reports/gate_outputs/wf0914_D11_revert_verify.txt`）。**不替月月選。**

---

## §0 一句話結論

候選修正（弦長/弦徑改用真實鋼琴逐八度查表，取代「每八度減半 + corpus 固定弦徑」）讓
高音區非諧性係數 B 明顯往真實量測值收斂（G6 對量測值的偏差倍數從 86.4× 縮小到 18.7×，
G5 從 21.6× 縮小到 7.6×），但同時讓 `physics_verify.py --full` 既有的 F5 殘餘能量檢查
（piano）從歷史穩定 PASS（−63.9~−64.4dB）退化為 FAIL（−58.5dB），根因未查出。三個選項
列在 §2，都不完美，看數字自己選。

## §1 核心數字（摘自 `reports/d11_string_scale_before_after.md`，逐位出處見該檔）

| 量 | before（現行） | after（候選） | 說明 |
|---|---|---|---|
| 非諧性 B，G5（對量測值 2×10⁻⁴ 的偏差倍數） | 21.6× | 7.6× | 方向正確，仍有 7.6× 誤差未消除 |
| 非諧性 B，G6（對量測值 2×10⁻⁴ 的偏差倍數） | 86.4× | 18.7× | 同上，18.7× 仍未消除 |
| `physics_verify.py --full` F5 piano 殘餘能量 | −63.9~−64.4dB（PASS，門檻 −60dB） | −58.5dB（**FAIL**） | 根因未查出，見 §5.2 |
| ctest（5 target） | 4/4 Passed | 4/4 Passed | 不受影響 |
| pytest | 264 passed/1 skipped/5 xfailed | 同左（oracle 同步鏡射候選公式後） | 不受影響 |
| 8 首代表曲位元基準 | — | 5/8 CHANGED（string/cimbalom/piano）、3/8 IDENTICAL（tongue_drum/water_gong/fm） | 符合預期影響範圍，R10 已觸發 |
| C1-C3 纏繞弦（銅包鋼）線密度 | — | 候選取芯線直徑，**低估**低音線密度 | 已知簡化，非文獻缺陷 |
| 使用者可調弦徑旋鈕 | 讀 `params.diameterMm` | 候選**完全覆寫**成查表值 | UI/UX 決策未定，見 §2 選項 A 的前提 |

## §2 三個選項（看數字自己選，不替月月裁決）

| 選項 | 做法 | 前提／代價 |
|---|---|---|
| **A：落地候選修正** | 把 patch apply 進 `src/physics/StringModel.h`／`src/engines/CimbalomEngine.h`／`tools/physics_verify.py`，8 首代表曲的音訊內容改變（5/8，已知哪些） | **前提**：先查清 F5 piano 殘餘能量退化（−63.9dB→−58.5dB）的根因並確認可接受，否則等於用一個已知的新 FAIL 換一個已知的舊誤差縮小。**額外代價**：需要另外決定 C1-C3 纏繞弦的複合線密度模型（否則低音弦密度被低估）、需要決定是否保留使用者手動弦徑覆寫（目前候選會讓 `params.diameterMm` 旋鈕失效）。**收益**：高音非諧性 B 明顯改善（2.86×~5.06×），是目前唯一在弦長模型層級縮小 A14 §3.10 缺口的候選方案。 |
| **B：不落地，維持現狀** | 什麼都不改，patch 存檔備查 | **前提**：無。**代價**：高音非諧性偏差維持 18.7×~86.4×（依音不同）不變，弦長模型仍假設「A4=0.35m、每八度減半」（MIDI 36 算出 2.49m 的弦長，比任何真實鋼琴最長弦還長一倍以上）。**收益**：零 Rule 10 衝擊、零 F5 regression 風險，8 首代表曲音訊維持逐位元不變。 |
| **C：先另立卡查 F5 根因，查清後再回頭裁決 A/B** | 本卡的 patch 繼續存檔，不落地；另開一張新卡，專門用時域/頻域拆解定位 F5 piano 殘餘能量退化的機制（多弦 beating 邊帶？某 partial 因 B 改變滑出 ±3% 判定窗？其他？） | **前提**：需要額外一張卡的工時。**代價**：非諧性 B 的改善延後生效。**收益**：避免在根因不明的情況下用一個已知 FAIL 換一個已知改善——如果查出根因是良性/可修的，就能同時拿到「非諧性改善」與「F5 繼續 PASS」；如果查出根因是候選修正模型本身的硬傷，也能避免誤落地。 |

## §3 附註：卡文標題的「2.4～5.2×」數字更正

本卡施工卡標題「B 路徑（B6 絕對聲壓）偏高 2.4～5.2×」查無出處——那組數字實際是非諧性
係數 B（物理符號，非「Path B」路徑代號）的舊數字，且已在
`reports/decision_packets/A13_partial_gate_domain.zh-TW.md:801` 被更正為 2.4～5.4
（見 `docs/STRING_SCALE_SOURCES.md:26-27`）；與弦長模型直接掛勾、有完整逐音對照表的既有發現是 A14 §3.10「B 偏高
14–87 倍」，本裁決包與 `reports/d11_string_scale_before_after.md` 都改用這個可溯源的量
做驗收依據。`absolute_pressure_per_force`（真正的 Path B 觀測量）在本卡取樣的全部音符上
mag0 逐位元不變，見 `reports/d11_string_scale_before_after.md` §3——不支持卡文標題的具體
倍率主張，僅供月月參考，不影響上面 A/B/C 三個選項的裁決。

**不動的東西**：`src/physics/StringModel.h`、`src/engines/CimbalomEngine.h`、
`tools/physics_verify.py` 的候選改動維持 patch 化、不落地；任何物理容差；
`physics_verify.py --full` 的既有 F5 門檻（−60dB，本裁決包不建議放寬）。

---

## 裁決記錄

**2026-09-15 月月裁決：選項 C（patch 存檔不落地；另立卡查 F5 根因，查清後再回頭裁決 A/B）**。
`reports/d11_string_scale_candidate.patch` 繼續存檔備查（`git apply --check` 已驗證可套用）；
工作樹維持現狀（8 首代表曲逐位元不變）。新卡登記於 `TODO.md`「D11-F5 根因調查」：
用時域/頻域拆解定位候選修正下 F5 piano 殘餘能量 −63.9→−58.5 dB 退化的機制
（多弦 beating 邊帶？某 partial 因 B 改變滑出 ±3% 判定窗？），查清後帶數字回來重開 A/B 裁決。
