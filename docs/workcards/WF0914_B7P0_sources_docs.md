# 施工卡 WF0914-B7P0：B7 Phase 0 溯源文件收尾

> lane：C++（但本卡**只動 docs**，不建置、不碰 `src/`）
> 前提：先讀 `WF0914_README.md`、`WF0907_README.md`、**`docs/workcards/B7.md` 全文**、
> **`docs/B7_PHASE0_DATA.zh-TW.md` 全文**（本卡的唯一資料來源）。

## 0. 一句話目標

把 WF0908-P5 已查回來的 Phase 0 資料，照 B7.md §3 的要求**轉寫**成兩份正式溯源文件——
`docs/HAMMER_VELOCITY_SOURCES.md`（新建）與 `docs/RADIATION_POWER_SOURCES.md` 新增 §8——
讓 B7P1 動工時有正式依據文件可引。**本卡是轉寫，不是新研究**：不做新的 WebSearch、
不引任何 `B7_PHASE0_DATA` 裡沒有的數字。

## 1. 前置檢查（B7.md §1 的三步確認，本卡代表 B7 全輪做一次）

1. 讀 `TODO.md` B6 條目，確認 Done 且 Phase 3/4 完成。
2. 讀 `ROADMAP_PHYSICS.md` §2 milestone 表，B6 打勾。
3. 開 `src/score/ScoreRenderer.h::dumpModes()`，親眼確認 `"absolute_pressure_per_force"` 與
   `acoustic_transfer[]` 的產生程式碼存在，並在回報裡寫明它讀的是哪個訊號分接點（file:line）。
任一步不符 → status=BLOCKED，回報實際讀到的文字，**整個 B7 輪停止**。

## 2. 要產出的檔案

### 2.1 新建 `docs/HAMMER_VELOCITY_SOURCES.md`（體例比照 `RADIATION_POWER_SOURCES.md`）

必含（全部從 `B7_PHASE0_DATA` §2.1/§4.3 與 B7.md §2.2 轉寫，附原出處）：
- 映射式 `hammerVelocityMps = 2^((MIDI − 52)/25)`，出處 Goebl (2003) 博士論文 Ch.3 式 (3.2)，
  原文 "was chosen to be MIDIvel = 52 + 25 · log2(fhv)"，**性質＝Bösendorfer SE 裝置慣例，非物理定律**。
- 三錨點（MIDI 40→0.7／60→1.25／77→2.0 m/s）與兩實測極值（0.18／6.8 m/s），各自出處、頁碼
  （**p.1163，09-09 已更正過頁碼，照抄最新版**）、有無 +14% 槌速校正。
- **+14% 刻度差**整段（Goebl et al. 2005 註 9 逐字引述；「系統性偏差 ≥ 殘差」的正確措辭；
  可用精度下限 ±14% ≈ ±1.14 dB）。**禁止**寫「三點交叉驗證全中」。
- 定義域 MIDI 20–120（≈0.41–6.6 m/s）有實測支撐；域外建議 clamp 至 0.18/6.8；
  MIDI 127 由式得 8.0 m/s 比實測最大高 18%；式表示不了極弱按壓觸鍵。
- 引擎 0–1 力度 proxy 與 MIDI 的對應**尚未裁決**這一條，原樣保留為 open item（B7P1 會處理）。
- 量測注意兩條（`pre_normalize_peak`；動態範圍隨音高變 10.6 dB、成因未查不主張）。

### 2.2 `docs/RADIATION_POWER_SOURCES.md` 新增 §8「音板輻射面積 S 的 Phase 0 補搜結果」

從 `B7_PHASE0_DATA` §2.3/§4.1 轉寫：
- 同儕審查層級：**平台琴查無**（累計 10+ 負面來源；arXiv:1210.3948 有 `area A` 卻不印數值）。
- 直立琴：Atlas 0.91 m × 1.39 m → **1.265 m²（乘法是本專案做的，論文沒印面積）**，出處兩篇 arXiv 逐字引述。
- 廠商規格層級：Baldwin 六台平台琴 0.87–1.68 m²；47 吋直立琴 1.2774 m² 與論文值差 0.99%；
  **是板面積非有效輻射面積、量法未明**。
- `S = M/(ρh)` 反推路線不通的理由（M=9 kg 含肋條琴橋；平台琴根本沒有 M）。
- **跨琴種挪用警告**照 B7.md §4.5 原文精神寫入。
- §8 末補一小節：σ(f) 信度上限量化（`fc≈1274`／`fga≈1308`、飽和窗 33.7 Hz＝有效頻寬 2.6%、
  97%+ 輸出走 `(f/fc)²` 近似——數字全部沿用 §3 補記既有值，不重新推導）。

### 2.3 `docs/workcards/B7.md`

§6 Phase 0 第 1、2 項後面各補一行「✅ 2026-09-14 WF0914-B7P0 完成 → 見 <文件>」。不動其他字。

## 3. GATE（本卡無建置、無渲染）

- `git diff --stat` 只含上列三檔。
- 逐數字溯源自查：新文件裡每個數值/引文都能在 `B7_PHASE0_DATA` 或 B7.md 找到同值來源
  （自查表存 `output/wf0914/B7P0/trace_check.md`，稽核會抽查）。
- 回報附 §1 三步檢查的實際證據（file:line、實際文字）。
