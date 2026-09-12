# WF0908-P4：A8 引用更正（選項 X）—— 2.06 m／消音室／63 Hz 出處，程式只改註解

> lane：C++（因為碰 `src/` 註解，要證位元不變）　工兵：Sonnet　共同規約：`WF0907_README.md`
> 依據：`docs/EXTERNAL_DATASET_A8.zh-TW.md` §0-2、§4.2 選項 X（建議）、R5 open_items；A13 open_items（Sinin 消音室）。
> **授權（NC）問題是月月裁決項（§4.1），本卡不碰。**

## 0. 一句話目標

把我們自己文件與程式註解裡「引用 TU Berlin 資料庫」的三處錯誤改對；**渲染輸出零改變**。

## 1. 要改的（全部是文字）

1. `docs/EXTERNAL_ANCHOR_SOURCES.md` §1 表格：
   - 「陣列直徑 2.1 m（半徑 1.05 m）」→「半徑 2.06 m（SOFA `ReceiverPosition`，32 顆麥克風一律 2.06 m；說明 PDF 式(4) S1=54.63 m² 反推 2.085 m）」；同節後續所有「1.05 m 球面」一併改，並加一句「本專案 `radius_m=1.05` 是自訂觀測距離，與該資料庫無關」。
   - 「消音室下限 fc = 63 Hz」加出處：僅見 arXiv 2307.02110 全文；說明 PDF 無此數。
   - 授權格：「CC BY-SA 4.0」→「**CC BY-NC-SA 4.0**（資料檔 metadata 與說明 PDF；arXiv 預印本寫 BY-SA、DepositOnce 記錄寫 InC——四源不一致，見 EXTERNAL_DATASET_A8 §2.1）」。
   - 表格每格補出處欄（arXiv／JAES／資料檔）。
   - §5.1 揚琴量測「非消音室」→「消音室」（Sinin et al. 2026 p.1087 原句 “All recordings were conducted in an anechoic chamber”），並加註 Table 3 只報兩位小數、未報 FFT 解析度。
   - DOI：資料檔內印的 `10.14279/depositonce-5861.3` 回 404；可用 `10.14279/depositonce-19858`。
2. `src/physics/RadiationModel.h` `kMeasurementRadiusM` 註解：「§1's 1.05 m anechoic-array convention」→「1.05 m 是本專案自訂觀測距離（DECIDED CONVENTION）；外部資料庫實際半徑 2.06 m，兩者無關」。**數值不動。**
3. `docs/RADIATION_POWER_SOURCES.md` §5 加一句（R4 open_items）：`S = M/(ρh)` 反推路線不可行——Ege & Boutillon 兩篇全文皆無音板總質量 M。

## 2. GATE（`reports/gate_outputs/wf0908_P4_a8.txt`）
1. 三 target build（build-wf）exit 0；位元不變 8/8（只改註解，必須 IDENTICAL）；ctest（X4）。
2. `grep -n '1.05' docs/EXTERNAL_ANCHOR_SOURCES.md` 剩餘每一處都附一句說明它是本專案自訂值。
3. `git diff --stat` 只含上列三檔 + 證據檔。
