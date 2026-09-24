# 施工卡 WF0914-D9：真實 IR 取得 + 載入響度量測 + 對齊裁決包

> lane：研究（用 `build\` 現成 exe；**不碰 `src/`、`tools/`、`tests/`**）
> 先讀：`WF0914_README.md` §2 第 6 條（下載規約）、`reports/decision_packets/K02_reverb_wet_scale.zh-TW.md` 全文、
> `reports/gate_outputs/wf0907_E7_reverb.txt`（K-02 的量測方法）、`src/IRLibrary.h`（只讀，理解載入路徑）、
> HANDOVER §6 A8 列（月月 09-09：無可商用資料集就私下對照參考——授權判定的先例）。

## 0. 一句話目標

D9 登記時寫「等真實 IR 檔量測」——本卡就去拿真實 IR：找授權乾淨的公開 IR 資料庫，
下載 2–4 個代表性 IR（小房間/廳/教堂各一），用 K-02 同一套方法量「載入該 IR 後 wet 響度
相對 ALGO 差多少 dB」，把數字做成對齊方案裁決包。**不改任何程式**。

## 1. 來源與授權（先做，過不了就誠實停）

候選方向（自行查證，不預設一定可用）：OpenAIR（York）、EchoThief、其他學術 IR 庫。逐來源記錄：
- 官方頁 URL、授權條款**逐字**（CC 何種？商用可否？）、檔案格式/取樣率。
- 授權不明或要登入 → 跳過並記錄。**比照 A8 先例**：若全部來源都非商用授權，仍可下載作
  「私下對照參考」，但裁決包必須明標「量測參考用，授權不可隨產品散布」。
下載到 `external_data/ir/`（gitignored），逐檔 SHA256 記進證據檔。

## 2. 量測

1. 先讀 wf0907_E7 證據檔，照抄它量 K-02（IR vs ALGO 差 28.5 dB）的方法（同一 score、同一量測鏈；
   如果它量的是合成 IR，本卡換成真實 IR 重量，方法不變）。
2. 對每個下載的 IR：量 wet 路徑輸出響度（讀 manifest `pre_normalize_peak` 或該方法用的量測點，
   **不可直接量正規化後 WAV**）對 ALGO 的差值 dB；另記 IR 本身的寬頻能量（RMS）與長度。
3. 全部命令與輸出存 `reports/gate_outputs/wf0914_D9_ir_measure.txt`。

## 3. 裁決包 `reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md`

體例照 K02。至少三案並列（不選）：
- A：載入時能量正規化（寫明正規化定義候選，如寬頻能量歸一；標「DECIDED CONVENTION 待月月定」）；
- B：不對齊，UI 顯示 IR 相對響度資訊（配合 F-03 三態顯示）；
- C：維持現狀＋文件記載。
每案附本卡實測數字（各 IR 與 ALGO 的實際差值）、對既有 corpus 的影響評估
（corpus score 是否有用到 IR？查證後寫明——沒有的話 A 案不觸 R10，要寫清楚）。

## 4. GATE

- `git diff` 只含 reports 兩檔（證據＋裁決包）；`external_data/` 不進版控（`git status` 證明）。
- 每個數字可對回證據檔的命令輸出；授權引文可對回來源頁 URL。
