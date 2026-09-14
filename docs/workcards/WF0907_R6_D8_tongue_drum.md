# WF0907-R6：D8 tongue_drum 40 dB 音高-響度斜率 + 缺泛音——根因診斷（不改碼）

> 研究卡　執行：Opus　先讀 `WF0907_R_research_common.md`
> 依據：`TODO.md` D8；`exports/products/moonlight_batch1/PRODUCT_SHEET.md`「已知缺陷」。商品線擋路石。

## 0. 問題

同 velocity 下 tongue_drum MIDI 37→87 的 RMS 從 −32.8 掉到 −73.1 dBFS（40.3 dB；cimbalom 同域只 4.4 dB），且輸出 99.9% 能量在基頻、無泛音列。
真鋼舌鼓有豐富非諧泛音。**這是引擎 bug、參數化錯、還是物理上高音舌片本來就這樣？** 改動會觸發 Rule 10，所以本卡只診斷、出裁決包。

## 1. 重現（用 `build\` 的 CLI，輸出 `output\wf0907\R6\`）

- 單音 score × MIDI {37, 47, 57, 67, 77, 87}，tongue_drum 引擎，velocity 0.5，效果全關，各 6 秒。
- 每個：`--dump-modes` 列模態（頻率、振幅、T60、幾何 length/width/thickness）；`--render` 後 numpy 量 RMS(dBFS)、峰值、基頻與各泛音能量占比、實測 T60。
- 同法跑 cimbalom 當對照組（TODO 說 4.4 dB）。

## 2. 追程式碼（每個環節給 file:line 與該環節對 40 dB 的貢獻估計）

- `src/engines/ChromaticEngine.h:173-243`：`BeamModel::lengthFromMidiNote(midi) * sizeScale`（L177；`lengthFromMidiNote` 在 `BeamModel.h:176`，reference 0.12 m）——
  舌片長度隨音高怎麼縮？寬/厚不變的話，**模態頻率比 1 : 6.27 : 17.5（懸臂）**，MIDI 87（~1245 Hz）第二模態 ~7.8 kHz、第三 ~21.8 kHz（超出 20 kHz 被 `ModalResonator` 截掉）→ 「近純正弦」可能就是這裡。
- `ModalResonator::modeAttackEnergy` / `loudnessCompensationGain(attackE, kChromaticAttackEnergyRefA4[0]=0.009504)`（L237-243）：補償 amount 0.78 是 partial 正規化，
  對 Beam 路徑的行為——當高音只剩 1 個模態時，attackE 怎麼變、補償夠不夠？
- `BeamModel.h:121-160` 振幅 convention（VELOCITY equal-weight）；`HammerImpulse` 對 Beam 的力脈衝頻譜與 τc keytrack（`ChromaticEngine.h:216`）。
- `decayTimeForMode` → `BeamModel::decayTimeForFrequency`（D1：梁/板阻尼未溯源）——高頻 T60 是否過短導致 RMS 崩。
- 把六個環節各自「若改掉會拉回幾 dB」估出來（能用 dump-modes 數字算的就算，算不出的寫「需實驗」）。

## 3. 外部證據

- 真鋼舌鼓/handpan 頻譜文獻：Morrison & Rossing（handpan/hang 研究）、ICSV27 2021 tongue drum（`TODO.md` D4：機構庫 403，試作者自存版/ResearchGate）、
  任何給出「舌片模態比值」「不同舌片音高的相對響度」的量測。
- 製造者資料：鋼舌鼓廠商（Hapi、Rav Vast、Idiopan 等）技術頁對舌片幾何（長/寬/厚隨音高怎麼變——**真鼓通常改長度也改寬度**，且有邊界耦合）。
- 社群：r/handpan、r/tonguedrum、r/percussion 關於「高音舌片比低音小聲很多」的討論——這是判斷「40 dB 是物理還是 bug」的觀感證據（標級）。

## 4. 交付

`reports/decision_packets/D8_tongue_drum_diagnosis.zh-TW.md`：
- §0 一句話：主因是哪個環節（附數字）。
- §3 重現數字表 + 環節貢獻表。
- §4 選項：每個選項寫改哪個檔/哪行、預期把斜率拉到幾 dB、會改變哪些 corpus 曲目（列出用到 tongue_drum 的 score 檔名，`grep -l tongue_drum scores -r`）、需不需要新溯源常數（R4）。
- **不改碼**。若你認為某環節明顯是 bug（例如單位錯），用一句話講清楚證據，仍留給月月裁決。
