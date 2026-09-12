# WF0909-P6：A8 裁決落地 ＋ 兩個可商用補充來源入庫（Weinzierl 2018、Iowa MIS 泰國鑼）

> 研究卡　執行：Opus　共同規約：`WF0907_R_research_common.md`（引用鐵律）
> 依據：`docs/EXTERNAL_DATASET_ALTERNATIVES.zh-TW.md`（2026-09-09，可商用且校準到絕對聲壓的資料集 = 0）；
> **月月 2026-09-09 裁決**：「看一下有沒有其他資料集參考，沒有的話先私下對照參考」→ 無 → **A8 = 選項 A 私下對照參考**。

## 1. 要做的
1. `docs/EXTERNAL_DATASET_A8.zh-TW.md` §4.1 加「裁決記錄（2026-09-09）」：月月選 A（私下對照參考，資料留本機 gitignore，不進程式常數、不進出貨文件）；
   選項 B（寫信要商業授權）**列為月月可自行決定的後續**，AI 不代發信。§4.2 加「規劣者裁決選 X，已由 WF0908-P4／WF0909-P4b 落地」。
2. 下載兩個補充來源到 `external_data/`（已 gitignore）：
   - Weinzierl et al. 2018 JASA（CC BY 4.0）PDF（約 1 MB）→ `external_data/weinzierl_2018_jasa/`；抄 LICENSE/授權原句、SHA256、TABLE I 中與本專案相關的列（鋼琴、定音鼓、任何撥/敲弦樂器）到新文件。
   - Iowa MIS 泰國鑼三包（約 90 MB）→ `external_data/iowa_mis_thai_gong/`；抄「without restrictions」原句與頁面 URL、麥克風型號/距離記錄、檔案清單 SHA256。
   下載前確認大小；任一來源打不開就寫「未取得」，不找替代。
3. 新文件 `docs/EXTERNAL_DATASET_SUPPLEMENT.zh-TW.md`：§0 一句話 → §1 兩來源登記表（授權原文、校準狀態＝Weinzierl 有 B&K 4230 校準器記錄／Iowa 未校準、對哪個引擎有用）→ §2 首批數字（informational）：
   Weinzierl TABLE I 鋼琴聲功率級 vs 本專案 B6 方案 B 的量級（**只證量級，不證模型**）；Iowa 泰國鑼一顆音的 FFT 前 5 partial 頻率比值 vs `water_gong` 引擎 `--dump-modes` 同音高的比值（用 `build\` CLI，輸出 `output\wf0909\P6\`）→ §3 缺口。
4. `docs/EXTERNAL_ANCHOR_SOURCES.md` 只在 §1 表格末加一行指向新文件（一行，不改其他）。
5. `TODO.md` A8 條目**不由本卡改**（規劃者處理）。

## 2. 禁止
- 資料檔不進版控；不宣稱「模型與實測吻合」；不改 src/ tools/。
