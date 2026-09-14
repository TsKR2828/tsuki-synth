# WF0907-R4：B7 Phase 0 資料補搜——velocity→槌速映射、鋼琴 SPL 範圍溯源

> 研究卡　執行：Opus　先讀 `WF0907_R_research_common.md`
> 依據：`docs/workcards/B7.md` §2.2、`docs/COMMERCIAL_PM_PUBLIC_DATA.zh-TW.md` §3–§4、`TODO.md` B7。

## 0. 問題

B7（第一原理力鏈）開工前缺兩塊資料：
1. **MIDI velocity（0–127 或 0–1 proxy）→ 真實槌速 m/s 的映射函數**。已知：Boutillon 實測範圍 0.11–6.83 m/s（pp–ff，Woodhouse *Euphonics* §11.2 轉引）、
   Askenfelt KTH 講義「forte ≈ 5 m/s、槌速 ≈ 5×鍵速」。**缺顯式映射**。
2. **真鋼琴 1 m 處 pp / ff 的 SPL 範圍**——裁決包寫的「pp≈60 dB / ff≈100 dB SPL @1m」**仍未溯源**。

## 1. 要查什麼

A. 映射：Goebl & Bresin 2003 (JASA 114) "Measurement and reproduction accuracy of computer-controlled grand pianos"（Bösendorfer SE / Yamaha Disklavier 的 MIDI velocity ↔ 槌速實測曲線）；
   Goebl, Bresin & Galembo 2005 (JASA 118) "Touch and temporal behavior of grand piano actions"；Kinoshita et al. 2007；
   Yamaha Disklavier / Bösendorfer CEUS 技術文件；MIDI 規範對 velocity 的定義（無物理單位——確認這點並引用）。
   目標：至少一組「velocity 值 ↔ m/s」的**表格或擬合式**（附原文表號/圖號）。
B. SPL 範圍：Askenfelt & Jansson KTH 講義；Fletcher & Rossing *Physics of Musical Instruments* 鋼琴章；Meyer *Acoustics and the Performance of Music* 動態範圍表（各樂器 pp/ff dB）；
   Chabassier et al. 2013 (JASA)、Roginska et al. 2013 (POMA) 近場量測。目標：有距離、有力度標示的 dB SPL 數字，至少兩個獨立來源。
C. 音板有效輻射面積 `S`：Suzuki 1986 (JASA) "Vibration and sound radiation of a piano soundboard"；Giordano 1998；Ege & Boutillon 的 S 值或音板尺寸。
D. 社群（次要）：r/piano 關於「鋼琴有多大聲（dB）」的實測貼文（手機分貝計不算物理證據，但可當觀感參照，要標清楚）。

## 2. 交付

`docs/B7_PHASE0_DATA.zh-TW.md`：
- §2 三張表（映射／SPL／S），每列：數值、條件（樂器型號、力度、距離）、來源、溯源等級（原文表格／轉引／僅摘要）。
- §4「可否開工」判定：三塊各自「齊／缺（缺什麼）」；缺的寫下一步能去哪找（機構庫、作者頁、ILL）。
- 不改 `B7.md`（規劃者之後整合）；`open_items` 列建議修改 B7.md 的段落。
