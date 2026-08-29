# B5 裁決包：木材正交異向常數——3 個選種問題

> 建立：2026-08-28（夜間，草稿階段，月月未上線）
> 性質：**免耳裁決包**——純文獻表格數字比對，不需要聽。
> 卡：`docs/workcards/B5.md` §4.2／§6 步驟 2（§12 停工條款已觸發）
> 狀態：**本卡目前停在「草稿」**——程式碼與測試已依建議值寫好並通過 sanity
> 建置，但**尚未進入 §8 正式 GATE**（--full／corpus／SHA256 對照／文件更新
> 全部未做），等本裁決包的答覆後才能繼續。

---

## 0. 一句話導讀

`data/materials.json` 的 4 個木料條目要新增「正交異向常數」（順紋/橫紋剛度比、
6 個泊松比），數字全部逐字抄自 Wood Handbook FPL-GTR-190。其中 3 個材質在
文獻表裡對應到不只一個候選樹種，工兵不能自己選，需要月月三選一（或明確
表示「不在意，照建議值走」）。

## 1. 三個候選對

| TsukiSynth 材質 | 候選 A（本卡建議值） | 候選 B | 差異影響 |
|---|---|---|---|
| `wood_spruce` | **Spruce, Sitka**（`ratio_ET_EL=0.043`，異向比 ≈23倍） | Spruce, Engelmann（`ratio_ET_EL=0.059`，異向比 ≈17倍） | 兩者密度都落在現有 `MATERIALS_SOURCES.md` 記載的 400–450 範圍內，單看密度無法區分；異向比差約 37% |
| `wood_maple` | **Maple, sugar**（`ratio_ET_EL=0.065`） | Maple, red（Wood Handbook 另有一列，本卡未抄，因為現有文件完全未指定亞種） | 現有 `materials.json` 的 `wood_maple` 密度/E 也未標註是哪個楓木亞種 |
| `wood_oak` | **Oak, red**（`ratio_ET_EL=0.082`） | Oak, white | 同上，現有文件未指定橡木亞種 |

完整 9+6+1 個數字見 `docs/workcards/B5.md` §4.2 四張表（已逐字轉錄進
`data/materials.json`）。

## 2. 為什麼工兵不能自己決定

`docs/MATERIALS_SOURCES.md` 對 `wood_spruce` 密度的依據原文就寫「Sitka/
Engelmann spruce ~400-450」——兩個亞種都吻合現有密度值，這是「現有資料本身
帶有的歧義」，不是本卡新引入的問題，也沒有更多線索能單向推出唯一解。
`wood_maple`／`wood_oak` 的情況更直接：現有文件完全没有指定亞種。

## 3. 目前的狀態（草稿，非最終）

- `data/materials.json` 已用候選 A（建議值）寫入 4 個木料條目。
- `MaterialDB.h` 已完成 fail-closed schema/解析/驗證，`present`/`hasGRT`
  旗標語意如卡片 §5.2。
- `tests/audit_repro.cpp` 已加 `testOrthotropicSchemaFailClosed()`，3 正例
  +6 反例全部針對建議值撰寫，sanity 建置與「故意造壞」哨兵已過（見
  `reports/gate_outputs/b5_method/draft_sentinel.txt`）。
- **沒有跑**：`--full`、corpus 四分片、SHA256 前後比對、`ROADMAP_PHYSICS.md`/
  `TODO.md` 更新——這些都排在本裁決包答覆之後（§6 步驟 3 之後才算開工）。
- 若月月選了候選 B 的任何一項，需要回頭改 `data/materials.json` 對應條目的
  9+6+1 個數字（`MaterialDB.h`/測試的 schema 邏輯本身不受影響，因為它們
  不依賴具體樹種值，只依賴範圍規則）。

## 4. 請月月回答

三個候選對各選 A 或 B（或回「都照建議值走」視為對三項都選 A）：

1. `wood_spruce` → Sitka（建議）／Engelmann？
2. `wood_maple` → sugar（建議）／red？
3. `wood_oak` → red（建議）／white？

回覆後工兵會把答案填回 `MaterialDB.h` 的 R4 註解「月月裁決日期/結論」欄，
並繼續 §6 步驟 3 之後（正式 GATE：--full/corpus/SHA256/文件更新）。
