# WF0907-R2：A14 高音弱基頻——物理正確還是引擎缺陷

> 研究卡　執行：Opus　先讀 `WF0907_R_research_common.md`
> 依據：`TODO.md` A14；證據 `reports/gate_outputs/stem_verify_fur_elise_run.txt` 發現 2。

## 0. 問題

乾聲單音實測（piano 引擎，velocity 0.427/0.462）：G5 峰值 −46.7 dBFS、主導頻率 1571.5 Hz（第二 partial，比值 2.0044）、基頻低 21.9 dB；
G6 峰值 −54.5 dBFS、主導 3214.9 Hz（比值 2.0503）、基頻低 24.0 dB；D7 峰值 −64.5 dBFS。
**真鋼琴高音區基頻也這麼弱嗎？整體電平掉這麼多正常嗎？** 若是引擎缺陷，改動觸發 Rule 10。

## 1. 要查什麼

A. 真鋼琴高音頻譜的量測文獻：Fletcher/Blackham/Stratton 1962；Askenfelt & Jansson（KTH "Five lectures on the acoustics of the piano" 開放全文）；
   Giordano《Physics of the Piano》；Conklin 1996 Part II（弦與 soundboard）；任何給出 C6–C8 區「基頻 vs 第二 partial 相對強度（dB）」的量測。
   重點數字：高音區基頻相對第二 partial 的 dB 差；擊弦點（strike point ≈ 1/8 弦長在高音區變化）對基頻的抑制；soundboard 在高頻的輻射效率。
B. **整體電平隨音高的變化**：真鋼琴同力度下 C7 vs C4 的 SPL 差（dB）；Askenfelt 講義或 Meyer《Acoustics and the Performance of Music》的動態範圍表。
C. 社群：r/piano、Piano World 關於「鋼琴最高兩個八度聽起來像敲木頭／沒有音高感」的討論（這是知名現象，找有量測或錄音分析的貼文最好）；
   Pianoteq 論壇關於高音區「太薄／太亮」的使用者回饋。
D. 稀疏但重要：inharmonicity 讓比值 > 2 是正常的（B 越大越偏）；查文獻中 G5/G6 的典型 B 值，換算比值與本專案的 2.0044/2.0503 比。

## 2. 引擎數字（跑，不改碼）

- 建三個單音 score（G5=79、G6=91、D7=98，velocity 0.45，piano 引擎，效果全關），`--dump-modes` 列預測 partial 頻率/振幅/T60；
  `--render` 後用 numpy 做 FFT 量實際基頻與第二 partial 的 dB 差、整體峰值 dBFS。與 A4 同法對照。
- 追程式碼：`src/engines/CimbalomEngine.h` 的擊弦點（strike position）隨音高怎麼變、`HammerImpulse` 力脈衝頻譜對高音基頻的壓制（B4 的 τc(v) 與 keytrack）、
  `loudnessCompensationGain`（amount 0.78）在高音區的行為、B1 琴橋損耗對高頻 T60 的影響。把每個環節對「基頻 −21.9 dB」的貢獻拆出來（能拆多少寫多少）。
- **對照 D8**（tongue_drum 40 dB 斜率）：piano 引擎 MIDI 37→87 同 velocity 的 RMS 斜率是多少？（TODO D8 說 cimbalom 同域 4.4 dB）

## 3. 交付

`reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md`：
- §0 一句話：「物理上合理／不合理／部分合理（哪部分）」，附最關鍵的一個外部數字。
- §4 選項：A 判定為物理正確，關閉 A14，C13 走 harmonic-aware 判定；B 判定為缺陷，立 Rule 10 施工卡（寫出要改哪個環節、預期改變哪些 corpus 曲目）；
  C 部分（例如比值正確但整體電平偏低），分開處理。
- 若外部資料不足以判定，誠實寫「無法從文獻判定，需 D7 實體量測」，並說明缺哪個數字。
