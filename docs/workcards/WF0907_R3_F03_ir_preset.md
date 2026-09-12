# WF0907-R3：F-03 IR user preset 不自包含——業界作法與社群證據

> 研究卡　執行：Opus　先讀 `WF0907_R_research_common.md`
> 依據：`reports/decision_packets/F03_IR_PRESET_RECALL.zh-TW.md`（待裁決，現建議 B）；稽核文件 §4-C。

## 0. 問題

使用者存了一個 IR 模式的 preset，隔天打開應該聽到什麼？三選一：**A 把 IR 音訊內嵌進 preset／B 受管理的 IR 庫（preset 存 id，plugin 管檔案）／C 只存路徑參考**。
以及 **IR 不見時**的行為（靜默退回 algorithmic？停聲？警告？）。月月要外部證據來決定。

## 1. 要查什麼

A. **主流 convolution / 帶樣本資源的 plugin 怎麼處理**（每家一列：preset 存什麼、缺檔怎麼辦、來源 URL）：
   REAPER ReaVerb、Waves IR-1、Audio Ease Altiverb、LiquidSonics（Reverberate/Seventh Heaven）、MeldaProduction MConvolutionEZ/MB、
   Native Instruments Kontakt（convolution 模組 + NKI 資源路徑）、Steinberg REVerence（Cubase 內建，**月月的 DAW**）、
   Xfer Serum（wavetable 內嵌進 preset 的作法）、Vital（wavetable 內嵌）、u-he（Zebra/Diva 使用者資源）。
   看官方手冊/FAQ 最準；找不到就標「未取得官方說明」。
B. **社群抱怨**：r/audioengineering、r/edmproduction、r/Reaper、r/cubase、KVR、Gearspace 搜「preset missing impulse response」、「IR not found preset」、
   「sample missing when loading preset」、「relink samples」。找 5 條有實質內容的，記使用者期待的行為（多數人希望怎樣？）。
C. **VST3 規範**對 preset 內嵌大型二進位資料有沒有限制或慣例（Steinberg VST3 SDK 文件、`.vstpreset` 格式）；JUCE 的 `getStateInformation` 對 state 大小有無實務上限（JUCE 論壇）。
D. 本專案現況：讀 F03 裁決包 §1–§4、`src/PresetManager.h`（user preset 存哪、格式）、`src/effects/EffectChain.h:86-105`（IR 載入）。

## 2. 交付

在**既有** `reports/decision_packets/F03_IR_PRESET_RECALL.zh-TW.md` **新增** §6「外部證據（2026-09-07）」與 §7「依外部證據的建議」，
不改動 §1–§5 原文。§7 要回答兩個問題（A/B/C 選哪個；缺檔行為），並給「若月月不同意建議，換選項的代價」一句話。
另在 `open_items` 列出實作要動的檔案清單（供下一輪立工程卡）。
