# WF0907 研究卡共同規約（R1–R6 都適用）

> 先讀 `WF0907_README.md`。研究卡由 Opus 執行，另一個 Opus 做**引用複核**（親自打開每個來源確認主張在裡面）。

## 引用鐵律（過去研究文件被稽核抓到「引用不實」，這是本輪最嚴的一條）

1. 每個外部主張都要附：**URL + 存取日期（2026-09-07）+ 一句 ≤15 字的原文引述**（用引號，標明出處）。
   打不開的來源就寫「未取得原文」，不得憑記憶補內容。
2. 論文請盡量抓到原文（arXiv / 作者自存版 / 機構庫）；只有摘要就標「僅摘要」。
3. **Reddit / KVR / Gearspace / Piano World 等社群討論可以用**（月月明示），但要分級：社群 = 「使用者觀感／需求證據」，
   不是物理證據；物理數字只能來自論文、教科書、量測報告。每條社群引用附 subreddit / 討論串標題 / 日期 / 讚數（若看得到）。
4. 查不到就寫查不到（R4）。一段「已知缺口」比一段編出來的數字有價值。
5. 不得引用 TsukiSynth 自己的文件當「外部證據」。

## 工具

- `WebSearch` / `WebFetch`（若被 deferred，先用 ToolSearch 載入）。Reddit 頁面若 WebFetch 打不開，試 `old.reddit.com` 或在 URL 後加 `.json`。
- 需要跑引擎數字：用 `build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe`（唯讀使用；輸出到 `output\wf0907\<卡號>\`）。
  score 格式看 `scores/examples/physical_piano.score.json`；`--dump-modes <score>` 給模態表；`--render` 用法看 `README.md`。
- **不改 `src/` `tools/` 任何檔案**。只寫你這張卡指定的新文件。

## 交付格式（每張卡）

- 指定路徑的 `.zh-TW.md` 文件，結構：§0 一句話結論 → §1 問題 → §2 外部證據表（分級） → §3 引擎/repo 現況數字（若適用） → §4 選項與建議 → §5 已知缺口 → 附錄：來源清單。
- 結構化回報：`status`、`output_paths`、`recommendation`（一句）、`sources_count`、`open_items`。
- 白話：月月沒有樂理與程式基礎，§0 與 §4 要讓她看完就能選。
