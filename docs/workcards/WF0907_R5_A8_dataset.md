# WF0907-R5：A8 外部資料集下載（TU Berlin 樂器指向性資料庫）+ SHA256 + 首批對照數字

> 研究卡　執行：Opus　先讀 `WF0907_R_research_common.md`
> 依據：`TODO.md` A8；`docs/EXTERNAL_ANCHOR_SOURCES.md` §1；月月 2026-09-07 裁決：**下載**，只當外部參照，repo 內只留 DOI + SHA256 + 比對數字，資料檔不進版控。

## 0. 目標

把「A Database with Directivities of Musical Instruments」（arXiv:2307.02110，DepositOnce 典藏，CC BY-SA 4.0）中**與弦樂器引擎最近似的子集**抓到本機，
建立可稽核的登記（DOI、授權原文、檔案清單、大小、SHA256），並做第一筆對照數字。

## 1. 步驟

1. 找到 DepositOnce 的 DOI 與檔案清單（先看 arXiv 論文的 data availability 段）。**先查總大小**。
2. 下載規則（月月已授權下載；仍要守）：
   - 目標子集：**原聲吉他、豎琴**（撥弦，`EXTERNAL_ANCHOR_SOURCES.md` §1.1 判定為最近似）+ README/LICENSE/任何 metadata 檔。
   - 子集 ≤ 5 GB 直接下；5–20 GB 只下其中一種樂器的 SOFA 格式；> 20 GB 或無法分檔 → **不下**，回報大小與檔案結構，status=BLOCKED。
   - 存到 `C:\Users\admin\Desktop\Claude\tsuki-synth\external_data\tu_berlin_directivity\`；**把 `external_data/` 加進 `.gitignore`**（這是本卡唯一允許改的 repo 既有檔）。
3. 每個檔 `certutil -hashfile <f> SHA256`（或 python hashlib），連同位元組大小記錄。
4. 讀一個 SOFA 檔（需要 `h5py` 或 `netCDF4`：`python -m pip install h5py` 允許，記在文件）：列出維度、取樣率、麥克風位置（應為 32 點、半徑 1.05 m）、
   校準說明（應為「1.0 ≡ 1 Pa ≡ 94 dB SPL」——**親眼從檔案 metadata 或 README 確認**，不要照抄我們自己的文件）。
5. 首批對照數字（informational，不判 PASS/FAIL）：取吉他 3 個音（低/中/高），正前方麥克風，算每音的 RMS 聲壓 → dB SPL @1.05 m；
   同時列 TsukiSynth B6 方案 B 的錨定（數位 1.0 ≡ 94 dB @1.05 m）在同一表，並明寫「激發方式不同（撥 vs 敲），此表只證明量級，不證明模型」。
6. 寫 `docs/EXTERNAL_DATASET_A8.zh-TW.md`：DOI、授權全文摘錄（CC BY-SA 4.0 的署名要求原文 ≤15 字引述 + 連結）、
   「保留商業」與 CC BY-SA 相容性一句話（只當外部參照、資料不進版控、不衍生發布 → 不觸發 SA），檔案登記表、SOFA metadata、首批數字。
7. `docs/EXTERNAL_ANCHOR_SOURCES.md` §1 表格「資料集未下載」那格改為「已下載子集，見 EXTERNAL_DATASET_A8」（只改那一格）。

## 2. 禁止

- 資料檔不得 `git add`；不得放進 `reports/` 或 `docs/`。
- 不得宣稱任何「模型與實測吻合」。
