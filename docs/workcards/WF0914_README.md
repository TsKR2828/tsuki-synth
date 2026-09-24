# WF0914 共同規約（所有 WF0914_* 施工卡的前提，先讀完再開卡）

> 建立：2026-09-14　規劃者：Claude Fable（主 session）　工兵：Sonnet　稽核：Opus
> 月月 2026-09-14 裁決：push+merge main 已完成（`main`=`b56747d`）；**B7 開工 + D9–D15 補缺口**，以 Dynamic Workflow 發包。
> 本檔只寫與 `WF0907_README.md` **不同**的地方；其餘規約（十條 Rule、lane 隔離、交付與稽核流程、
> 「只碰你這張卡列出的檔案」）**全部沿用 `docs/workcards/WF0907_README.md`，先讀完它**。

## 0. 本輪與 WF0907 輪的差異

| 項 | WF0907 輪 | 本輪 WF0914 |
|---|---|---|
| 位元不變基準 | `sha256_before.txt` → `post_d8` → `post_a14` | **一律 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`**，比對腳本 `reports/gate_outputs/wf0907_method/render_wf_scores.py`（支援 `--cli`）。**期望 8/8 IDENTICAL**（本輪沒有任何卡被授權改渲染輸出；任何 SHA 變化 = R10 觸發 = BLOCKED） |
| pytest 數 | 213 → 267 | 基線 **267 個測試**（09-13 commit 時點；精確細分＝263 passed＋3 xfail＋1 skip，原寫「267 passed」是口語簡寫，2026-09-25 盤點更正）。本輪整合後新基線 **270 個測試＝264 passed＋1 skip＋5 xfail**（09-15 整合卡、09-25 重跑皆同）；各卡新增測試後只會更多。**全套 pytest 只在整合卡跑**（跨 lane 污染教訓，WF0907_README 沒寫死、這裡寫死：非整合卡只跑自己新增/相關的測試檔） |
| 暫存輸出 | `output\wf0907\<卡號>\` | `output\wf0914\<卡號>\`（gitignored） |
| 證據檔 | `wf0907_<卡號>_*.txt` | `reports\gate_outputs\wf0914_<卡號>_*.txt`（進版控） |
| 現成 binary | `build\`（08-31 建） | `build\` 對應 HEAD `a38bd6a`（09-10 23:46 建，含 F-03/A14）。**Python lane 與研究 lane 用它，不要重建**。C++ lane 用 `build-wf\`（命令見 WF0907_README §1） |
| 測試 target | 三個 | **五個**：`TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest TsukiSynthSpectrumViewTest TsukiSynthHostProbe`（X4 規約照舊：跑 `ctest` 前必先重建全部測試 target） |

## 1. lane 配置與順序

| lane | 卡（依序） | 說明 |
|---|---|---|
| C++（`build-wf\`） | B7P0 → B7P1 → B7P3 → D12 → D11 | B7P0 只動 docs 不建置，但排此 lane 因 B7P1 依賴其產出 |
| Python（用 `build\` 現成 exe） | D14 → D15 | 工具層，不碰 `src/` |
| 研究（平行） | D9、D10、D13 | 不碰 `src/`、`tools/`、`tests/` |
| 整合（最後） | INTEGRATION | 唯一允許重建 `build\` 的卡 |

## 2. 本輪硬性提醒（每張卡都適用）

1. **R7 全文**：絕對不 `git commit`/`push`/`checkout`/`stash`/`reset`。稽核 PASS 後由**稽核**執行 `git add -- <files_touched>`；月月最後看 `git diff --cached`。
2. **R2/R3**：禁調寬容差、禁縮 GATE 範圍、**禁自訂新的物理容差**。工程層驗收（如記憶體量測）只**記錄實際數字**，不發明門檻。
3. **R4**：任何數字要嘛有出處（原文逐字引述＋頁碼/URL），要嘛明標「工程假設，非文獻」。研究卡**不得引用沒 fetch 過全文的來源的任何數字**（WF0907 輪抓到過編出來的資料集標題）。
4. **裁決包體例**：比照 `reports/decision_packets/K02_reverb_wet_scale.zh-TW.md`——選項並列、每案代價/前提寫清楚、附看數字就能選的表格、**不替月月選**。
5. 工兵回報一律結構化：`status`（DONE / BLOCKED / RED）、`files_touched`、`gate_results`（每條 GATE 的命令＋關鍵輸出行）、`evidence_paths`、`open_items`。發現卡文與 repo 現況矛盾 → 停下寫進 `open_items`，不要硬做（WF0908-P4 教訓：卡文可能錯）。
6. 下載類（僅 D9）：只從官方來源頁下載；逐檔記 URL、授權原文逐字、SHA256；要登入才能拿的來源直接跳過記錄；下載物放 `external_data/`（gitignored），**不進版控**。
