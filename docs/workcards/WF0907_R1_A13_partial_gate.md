# WF0907-R1：A13 partial（泛音）GATE 的主張域——外部證據與建議

> 研究卡　執行：Opus　先讀 `WF0907_R_research_common.md`
> 依據：`TODO.md` A13；`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.4；月月 2026-09-07：「看看能不能查到外部資料決定」。

## 0. 問題

`stem_verify` 現在只驗基頻與起音，**partial 的頻率與振幅從未實測**，所以不能說「泛音已驗證」。
要不要立一個 partial GATE？主張多強（只驗頻率？連振幅？）、容差多少？
**新容差不可由工程端自訂（R2）**——但可以從外部文獻找到「業界/學界量測 partial 的精度與可重複性」當依據，交給月月裁決。

## 1. 要查什麼

A. **學界怎麼量鋼琴/揚琴 partial 頻率與 inharmonicity B**、精度多少：
   - Fletcher, Blackham & Stratton 1962 (JASA) "Quality of piano tones"；Conklin 1996 (JASA) "Design and tone in the mechanoacoustic piano" Part I–III；
     Rauhala/Lehtonen/Välimäki 2007 "Fast automatic inharmonicity estimation algorithm"（JASA EL）；Hodgkinson et al. 2009；Galembo & Askenfelt 1999。
   - 重點：他們報告的 partial 頻率量測誤差（cents 或 Hz）、B 的可重複性、振幅量測的變異（dB）。
B. **商業物理建模合成器怎麼對外主張 partial 正確性**（Pianoteq 的 inharmonicity 參數、Modartt 論壇討論、使用者測 spectrogram 對比真鋼琴的貼文）。
C. **社群**：r/piano、r/synthesizers、r/audioengineering、Piano World、KVR 上關於「inharmonicity / partials / 合成鋼琴高音聽起來假」的討論——
   使用者在意的是頻率（音準感）還是振幅（音色）？找 3–5 條有實質內容的。
D. 揚琴（yangqin/cimbalom）partial 量測：`docs/EXTERNAL_ANCHOR_SOURCES.md` 已引 Sinin et al. 2026 BioResources（開放全文，本機已解析）——
   讀那份的 Table 3/4 看它報告的 f/f0 比值精度，這是最貼近本專案的外部量測。

## 2. 引擎現況要一併列出（跑數字，不改碼）

- 用 CLI `--dump-modes` 對 piano 引擎 A4 / G5 / G6 單音（velocity 0.45）列前 8 個 partial 的預測頻率與相對振幅；
  再看 `reports/gate_outputs/stem_verify_fur_elise_run.txt` 發現 2 的實測數字（G5 主導 1571.5 Hz、比值 2.0044）。
- 把「模型預測的 partial 比值」與 §1-A 文獻的真鋼琴 B 值換算的比值放同一張表。

## 3. 交付

`reports/decision_packets/A13_partial_gate_domain.zh-TW.md`：
- §4 選項至少三個：**A 不立 partial GATE（只在文件宣告未驗證）／B 只驗 partial 頻率，容差 = 文獻量測精度（附出處）／C 頻率+振幅**。
  每個選項寫：主張強度、需要哪些工具改動（估工程量）、風險（假綠燈可能性）。
- 給一個建議，但把「容差數字的出處」單獨列成一行讓月月核。
