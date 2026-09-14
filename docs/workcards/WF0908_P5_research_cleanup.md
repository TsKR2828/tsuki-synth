# WF0908-P5：研究文件收尾 —— 複核殘留 findings 全清 ＋ B7.md 依 Phase 0 資料更新

> 研究卡　執行：Opus　共同規約：`WF0907_R_research_common.md`（引用鐵律）
> 這張卡只改文件；不碰 `src/` `tools/`。

## 0. 目標
把 WF0907 六張研究卡引用複核後**還留著**的 findings 逐條處理，並把 R4 的 Phase 0 資料整合進 `docs/workcards/B7.md`。

## 1. 逐條（每條處理完在該文件文末「複核修正記錄」加一行）

| 來源 | 檔案 | finding | 處理 |
|---|---|---|---|
| R1 | `reports/decision_packets/A13_partial_gate_domain.zh-TW.md` | Fletcher, Blackham & Stratton 1962《Quality of Piano Tones》標「未取得原文」，但 BYU 機構庫（scholarsarchive.byu.edu）可能有全文 | 試抓；抓到就把 B1 升級並補振幅側 dB 敘述（≤15 字原文引述）；抓不到寫明試過的 URL |
| R2 | `reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md` §0 | 把 Hall「中音域」限定條件剝掉寫成通則，與 §3.3 自相矛盾 | §0 改回「中音域」限定，結論改寫為「G5 的 2.9 倍已遠超中音域的 ≈1 倍，且 §3.3 說明 x≫1 區域模型本身不成立」；不得改動 §3 的數字 |
| R4 | `docs/B7_PHASE0_DATA.zh-TW.md` §4.3 | 三錨點來自兩篇有 14% 槌速校正差的來源，未標示，殘差敘述誤導 | 標示校正差、把殘差句改成「系統性偏差 ≥ 殘差」的誠實版 |
| R5 | `docs/EXTERNAL_DATASET_A8.zh-TW.md` | (a) 署名區塊的資料集標題是編出來的書目字串 | 改成資料檔/說明 PDF 上**逐字**的標題（打開 `external_data/tu_berlin_directivity/` 的 PDF 或 SOFA `Title` 屬性抄），並附抄自哪裡 |
| R5 | 同上 §4.1 選項 C | BRAS／Loudspeaker Orchestra 兩個 CC BY-SA 主張無 URL、無引述 | 補 URL＋存取日期＋≤15 字原文；查不到就改成「未查證」 |
| R1/R5 | `docs/EXTERNAL_ANCHOR_SOURCES.md` | 由 WF0908-P4 處理，本卡**不動** | — |

## 2. B7.md 整合（依 R4 open_items）
- §2.2 velocity→槌速表：加 Goebl 三錨點（MIDI 40→0.7、60→1.25、77→2.0 m/s）與極值（0.18／6.8），來源升級為「原文已核」，**並註明 14% 校正差**。
- §8 驗收基準 (a)：改為「分音域相對動態範圍 GATE（待月月核）」或標「絕對 SPL 出處阻塞」，兩案並列，不替月月選。
- §4.5／§4.2：`S` 平台琴查無；只有直立琴 1.265 m²（Ege 等人尺寸相乘），註明跨琴種挪用風險。
- 加一條量測注意：CLI 預設 normalize=true，力度量測必須讀 manifest 的 `pre_normalize_peak`。
- 加一條：引擎 piano 動態範圍隨音高變（C2 49.5／C4 60.1／C7 49.8 dB）成因未查。

## 3. 交付
`status`、`output_paths`、每條 finding 的處理結果一行（在 summary）。引用複核員會逐條再開來源。
