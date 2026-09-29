# 外掛 16 顆 voice 會不會搶音：分析估算（2026-09-25，WF0925-V1 B）

> **身分**：分析估算，不是 GATE。全文沒有新設任何判定門檻；唯一出現的「16」是 `src/PluginProcessor.cpp` 自己宣告的 pool 大小。
> 分箱（例如「剩 −10 dB 以內」）只是為了方便讀數字，一律標「描述用、非 GATE」。
> 登記項：`open-work:P1-voice-steal`（STATUS_CHECK §3-3、APPENDIX `[open-work:P1-voice-steal]`、POLYPHONIC_VERIFICATION_OPTIONS §6）。
> 本卡沒有改 `src/`、`tools/`、`tests/`。用的 CLI 是 `build\` 那支的複本 `output/wf0925/V1/cli.exe`（SHA256 `9123db8f…01be8`，跟 `build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe` 相同，也跟 clean_batch2 商品 render.json 記的 `renderer_executable_sha256` 相同）。
> **行號一律是 HEAD `18430c4`**。工作樹裡有別張卡（WF0925-K1）還沒 commit 的修改，會讓 `PluginProcessor.cpp`、`CimbalomEngine.h`、`ChromaticEngine.h`、`tests/host_probe.cpp` 的行號往後移，但本報告引用的每一段原文在工作樹裡都逐字存在、只是位置不同（`wf0925_V1_voice_pool_sources.txt` 逐段列出 HEAD 行號＋工作樹現在的行號）。
> 腳本：`reports/wf0925_method/`（下面每一節都寫了是哪支）。
> 證據（`reports/gate_outputs/`）：`wf0925_V1_cli_provenance.txt`（CLI 出處）、`wf0925_V1_voice_pool_sources.txt`（§1 每條規則的程式碼原文）、`wf0925_V1_voice_pool_dumps.txt`（T60 來源與重現）、`wf0925_V1_voice_pool_summary.txt`（§4 全部數字）、`wf0925_V1_voice_pool_lifetime_probe.txt`（§3）、`wf0925_V1_voice_pool_cpu_bench.txt`（§5）、`wf0925_V1_voice_pool_side_checks.txt`（§4.3(c) FM、§4.5、按引擎視角的子引擎混用）。
> 本卡在 09-25 被 session 中斷過一次。前任寫的腳本與數字，接手者全部重跑核對過：`--dump-modes`（兩版各 75 份）、外掛做得到版 score 副本、兩份模擬結果都與前任的檔案逐位元組相同；單音壽命表逐字相同，另外直接讀 WAV 再核一次；CPU 計時無法逐位元重現，另跑了第 3 輪並列。核對時修正了本報告幾處敘述（行號改為 HEAD、參數用量「事件數」與「參數數」分開、商品在兩版 T60 下的差異、四季齊奏的例子）。

---

## 0. 先講結論（白話）

1. **要上架的 50 件商品（clean_batch2），照正常彈法（放鍵就放鍵）都不會超過 16 顆。**
   給愛麗絲兩個版本最多同時 12 顆；AI Radiance 各樂章最多 8 顆；音效包 43 件最多 4 顆。
2. **全 corpus 75 首裡，正常彈法會超過 16 的有 3 首，都不是商品：**
   - 月光全曲（FM 引擎）：最多 196 顆。但這不是「音太多」，是 FM 引擎的一個行為（見第 4 點），196 顆裡有 184 顆的音量包絡已經低於 24-bit 最小一階那條參考線（−138.5 dB，描述用）。
   - 月光第一樂章舌鼓版：最多 20 顆，會搶 64 次。
   - 月光第一樂章揚琴＋舌鼓混合版的舌鼓部分：最多 20 顆，會搶 41 次。
3. **兩個會讓數字變大的條件：**
   - **四季（弦樂）用了外掛做不到的 `damping_override`。** 外掛沒有這個旋鈕，拿掉之後音會變長。在「全部弦樂擠在同一個外掛」的算法下，12 個樂章有 6 個超過 16（最多 26 顆）；改成「一個聲部一個外掛」就 0 個超過。
   - **整首踩住延音踏板。** corpus 沒有踏板資料，這只是假設的上限。這種情況下商品有 4 件超過：給愛麗絲兩版各 22 顆，AI Radiance 全曲的 FM 19 顆，第三樂章的 FM 17 顆。
4. **另外查到兩件跟 pool 大小無關、但會讓外掛跟 CLI 不一樣的事（加大 pool 也解決不了）：**
   - **同音重疊會提前制音。** 同一個音高的前一顆還沒放鍵、後一顆就開始時，JUCE 會先把前一顆制音；前一顆放鍵時，又會把後一顆也一起制音。給愛麗絲有 21 顆這樣的音。例如第 53 顆 A4 在 10.000 s 開始，譜上 10.463 s 才放鍵，外掛卻在 10.068 s 就開始制音。CLI 每顆音各用一顆 voice，不會這樣。
   - **FM 引擎同一個音反覆彈時，舊 voice 會一直不結束。** 每次同音按下或放開，還在收尾的舊 voice 都會從目前音量重新起算整段 release。同一個音反覆的間隔比 release 短時，舊 voice 就永遠到不了結束狀態，音量已經近乎 0，卻一直佔著位子。第 2 點月光全曲的 196 顆就是這樣來的。
5. **模型驗證**：拿 8 顆真實的 modal 引擎音，用 CLI 單獨渲染，跟這個釋放公式比。「voice 何時停止」的誤差最大 6.9 ms，佔壽命 0.07%。FM 引擎這種方法量不到（原因見 §3）。

給月月的選項（加大 pool／寫進主張域／維持）在 §6，並列，不替你選。

---

## 1. 程式碼怎麼釋放 voice（逐條附出處）

| 事實 | 出處 |
|---|---|
| 三個引擎各有一個 `juce::Synthesiser`，各 `addSound` 一個、`addVoice` 16 顆 | `src/PluginProcessor.cpp:34-36`（Cimbalom）、`:69-71`（Chromatic）、`:103-105`（FM Piano） |
| 只有「目前選的引擎」收 MIDI；Cimbalom 和 Piano 共用 cimbalomSynth 的 16 顆 | `src/PluginProcessor.cpp:350-359`、`src/ParameterLayout.cpp:26-28` |
| 沒有呼叫 `setNoteStealingEnabled`，所以用 JUCE 預設：**會搶** | `libs/JUCE/modules/juce_audio_basics/synthesisers/juce_Synthesiser.h:640`（`shouldStealNotes = true`，JUCE 8.0.12） |
| **放鍵不會馬上釋放 voice**：Cimbalom 放鍵只是把每個 mode 的衰減時間乘 0.05 | `src/engines/CimbalomEngine.h:345-358`（stopNote）、`:862-870`（applyDamp，`damp (0.05f)`） |
| Chromatic 放鍵乘 0.08 | `src/engines/ChromaticEngine.h:267-282` |
| 每個 mode 衰減到自己起始振幅的 0.001（−60 dB）就停。**所有 mode 和槌擊雜訊都停了**，才呼叫 `clearCurrentNote()` 釋放 voice | `src/dsp/ModalResonator.h:90`（stopAmp）、`:106-117`（damp）、`:179-181`；`CimbalomEngine.h:817-859`；`ChromaticEngine.h:593-672` |
| 所以 voice 的壽命是「最慢的那個 mode 在放鍵後照加速後的速度衰減完」。公式：沒放鍵（或放鍵時已超過 T60）＝`t_on + T60`；否則＝`t_off + 係數 × (T60 − (t_off − t_on))`。CLI 自己配 buffer 也是用這條（係數寫 0.05） | `src/score/ScoreRenderer.h:1559-1590`（eventEndTime） |
| FM 引擎是 ADSR：放鍵後跑完 release 才釋放；放鍵時音量已經是 0 就立刻釋放。sustain=0 的 preset，音量在 decay 後就變 0，但**沒放鍵前仍然佔著 voice** | `src/engines/FMPianoEngine.h:133-146`、`:194-215`；`src/dsp/Envelope.h:29-42`、`:76-85` |
| FM 的 `Envelope::noteOff()` 只要不是 Idle 就會重新起算 release，包括已經在 release 的 voice | `src/dsp/Envelope.h:29-40` |
| JUCE 按下一個音時，先對「所有正在發同一個音高的 voice」做 tail-off 停止，再找空 voice。空 voice＝依陣列順序第一顆沒在用的；沒有空的就搶 | `juce_Synthesiser.cpp:307-327`、`:509-523` |
| **JUCE 搶誰（依序）**：先保護「還按著的音」裡最低和最高的兩顆，然後 (1) 同音高裡最舊的 → (2) 已放鍵、不受保護的最舊的 → (3) 沒按著、不受保護的最舊的 → (4) 不受保護的最舊的 → (5) 只剩受保護的，先搶最高的、再搶最低的 | `juce_Synthesiser.cpp:525-609`；「已放鍵」的定義 `juce_Synthesiser.h:252-256`（isPlayingButReleased） |
| 被搶的 voice 走 `stopNote(0, false)`：直接切掉，不收尾 | `juce_Synthesiser.cpp:337-338`、`CimbalomEngine.h:352-357` |
| JUCE 放開一個音時，**所有**正在發這個音高的 voice 都被放開（不只一顆）；延音踏板踩住時只標記、不制音 | `juce_Synthesiser.cpp:363-390`、`:450-478` |
| CLI 是每個事件自己 new 一顆 voice，沒有 pool、不會搶 | `src/score/ScoreRenderer.h:1113`（renderEvent）→ `:1197-1229`（renderCimbalom：一個事件一顆 voice、0.9×時值放鍵、`isActive()` 迴圈在 :1227） |

---

## 2. 假設（估算只在這些假設下成立）

| # | 假設 | 為什麼這樣選 |
|---|---|---|
| M1 | 全部事件走同一個 MIDI channel。按下＝`round(time×sr)`；放開有兩種：**情境 A**＝`time + duration`（repo 自己的外掛測試工具 HostProbe 就是這樣送，`tests/host_probe.cpp:237-245`，放鍵那行在 :239），**情境 B**＝`time + 0.9×duration`（CLI 渲染器自己的放鍵點，`ScoreRenderer.h:1310-1311`）。**情境 C**＝整首踩住延音踏板（corpus 沒有踏板資料，給愛麗絲原始 MIDI 也只有 CC7、沒有 CC64，所以 C 只是假設的上限） | 兩種放鍵慣例 repo 裡都有，所以都算 |
| M2 | 同一個 sample 上，放開排在按下之前 | 一般 MIDI 檔的慣例。反過來會讓同音新音一開始就被制音 |
| M3 | 外掛參數＝每個事件自己的 score 參數，Macro 旋鈕都在中間 0.5。這時外掛的衰減倍率正好是 1.0，所以 T60 可以直接用 CLI `--dump-modes` 的 `decay`（Macro 預設值 0.5：`ParameterLayout.cpp:30-48`） | `CimbalomEngine.h:247-249`（`matScale = 0.5 + mMaterial`、`dmpScale = 1 + (0.5 − mDamping)×1.4`）、`FMPianoEngine.h:125-126`（release 同一個 dmpScale） |
| M3' | **但外掛沒有 `damping_override` 和 `tension_n`**：外掛呼叫衰減公式時固定傳 −1（`CimbalomEngine.h:265-266`、`:323-324` startNote 內兩處 `applyStringDecayTimes (…, -1.0f, …)`），`ParameterLayout.cpp` 也沒有這兩個參數。corpus 有 30 首、30813 個事件用到它們（30812 個 `damping_override`＋15 個 `tension_n`，共 30827 個參數；四季全部、月光揚琴、AI Radiance 部分音、部分音效）。所以每個結果都算兩版：**「score 版 T60」**（照 score 寫的）和**「外掛做得到版 T60」**（拿掉這兩個參數再 dump） | 腳本 `make_plugin_reachable_scores.py` 會先 grep 原始碼確認這兩件事，不成立就停 |
| M4 | voice 在「算出的結束 sample ≤ 目前 sample」時算空出來 | JUCE 在 render 子區塊結束時才清 voice（子區塊最小 32 sample）。這個顆粒度、≤20 ms 的槌擊雜訊、float32 逐 sample 乘法的捨入都沒算；§3 量了這個簡化實際差多少 |
| M5 | 外掛怎麼分：**「按引擎」**＝一個引擎一個外掛，吃下這個引擎的全部事件（例如給愛麗絲兩手同一個鋼琴外掛）；**「按聲部」**＝一個 (引擎, score 的 performance.track) 一個外掛（例如四季的小提琴一、小提琴二、中提琴、大提琴、獨奏分開） | 兩種都是 DAW 常見用法，兩種都算。注意：外掛一個 instance 同時只能選一個 Chromatic 子引擎，但 AI Radiance 與 4 個音效把 tongue_drum／water_gong／custom（或 beam／plate）混在同一份 score；「按引擎」把它們算進同一個 pool，是偏多的算法（拆開只會更少）。這些曲子的需求在情境 A/B 都 ≤8、情境 C 最多 12（`wf0925_V1_voice_pool_side_checks.txt` §3）。Cimbalom pool 沒有任何一首混用 string／cimbalom／piano |

---

## 3. 模型對不對：單音實測（描述用、非 GATE）

方法（`reports/wf0925_method/voice_lifetime_probe.py`）如下：

- 從 corpus 挑 10 顆真實事件，用 CLI 單獨渲染成乾聲、不正規化的 32-bit float。
- 尾巴加到 60 s，確保 buffer 比 voice 活得久。
- CLI 的迴圈是 `for (…; voice.isActive(); …)`，所以最後一個非零 sample 就是 voice 停止的時間點。這跟外掛清 voice 用的是同一個 `isActive()` 條件。
- 放鍵點用 CLI 自己的 0.9×duration。

| # | 引擎 | 音 | 時值 s | 最慢 mode T60 s | 預測停止 s | 實測停止 s | 差 |
|---|---|---|---|---|---|---|---|
| 0 | piano | E5（v0.278） | 0.231 | 1.153 | 0.7556 | 0.7556 | +0.01 ms |
| 1 | piano | A2 | 0.215 | 6.691 | 1.0186 | 1.0186 | +0.01 ms |
| 2 | piano | A5（v0.427） | 0.108 | 0.865 | 0.6352 | 0.6353 | +0.01 ms |
| 3 | cimbalom（月光揚琴） | 37 | 4.480 | 5.819 | 4.6213 | 4.6213 | −0.02 ms |
| 4 | tongue_drum（月光舌鼓） | 37 | 4.480 | 68.675 | 9.7034 | 9.7103 | +6.85 ms（壽命的 0.074%） |
| 5 | water_gong | C4 | 3.000 | 7.486 | 3.5829 | 3.5826 | −0.33 ms |
| 6 | string（四季冬） | C5 | 3.810 | 1.101 | 1.6011 | 1.6009 | −0.18 ms |
| 7 | string（四季夏） | Eb2 | 0.103 | 2.843 | 0.7305 | 0.7305 | +0.02 ms |
| 8 | fm | 37 | 4.480 | — | 4.5320 | （4.0019） | 量不到 |
| 9 | fm | 32 | 13.440 | — | 12.5960 | （4.0019） | 量不到 |

- modal 引擎 8 顆：最大誤差 6.85 ms。
- FM 兩顆的「最後非零 sample」都在 4.0019 s。原因是 sustain=0 的 Piano preset，attack 5 ms 加 decay 3.5 s 之後輸出就變成 0；但 envelope 仍停在 Sustain 狀態，voice 還佔著，要等放鍵才釋放。所以「最後非零 sample」量不到 FM 的 voice 壽命。FM 的壽命只能照程式碼讀，這個限制照實列出。
- 證據：`reports/gate_outputs/wf0925_V1_voice_pool_lifetime_probe.txt`。

---

## 4. 結果

完整表格見 `reports/gate_outputs/wf0925_V1_voice_pool_summary.txt`，全部搶音清單在 `output/wf0925/V1/voice_pool_{scoreT60,reachableT60}.json`（本機，gitignore）。
「需求」＝pool 無限大時同時活著的 voice 最大數，也就是完全不被搶需要幾顆。

### 4.1 總表：75 首裡幾首超過 16

| T60 版本 | 外掛怎麼分 | 情境 A（放鍵＝時值） | 情境 B（0.9×時值） | 情境 C（踩住踏板，假設） |
|---|---|---|---|---|
| score 版 | 按引擎 | **3 首**（商品 0/50），搶 892 次 | 3 首（商品 0），搶 855 次 | 14 首（商品 4），搶 9178 次 |
| score 版 | 按聲部 | 3 首（商品 0） | 3 首（商品 0） | 5 首（商品 2） |
| 外掛做得到版 | 按引擎 | **9 首**（商品 0/50），搶 2051 次 | 9 首（商品 0） | 17 首（商品 4） |
| 外掛做得到版 | 按聲部 | 3 首（商品 0） | 3 首（商品 0） | 12 首（商品 2） |

### 4.2 商品 50 件

| 商品 score | 最慢 T60 s | 情境 A 需求 | 情境 B | 情境 C（假設） |
|---|---|---|---|---|
| 給愛麗絲（鋼琴）| 13.01 | 12 | 12 | **22（搶 59 次）** |
| 給愛麗絲（揚琴版）| 13.01 | 12 | 12 | **22（搶 59 次）** |
| AI Radiance 全曲：Chromatic / Cimbalom / FM | 42.26 / 1.84 / — | 8 / 1 / 8 | 8 / 1 / 8 | 12 / 4 / **19（搶 7 次）** |
| AI Radiance 第 1～4 樂章（最大值） | ≤42.26 | ≤8 | ≤8 | 第 3 樂章 FM **17（搶 1 次）**，其餘 ≤11 |
| 音效包 43 件（最大值）| ≤56.60 | ≤4 | ≤4 | ≤6 |

「外掛做得到版」只有 Cimbalom 部分的數字會變，搶音次數全部仍是 0：
- AI Radiance 全曲與第 1、2 樂章：情境 A/B 從 1 變 2；情境 C 最多從 4 變 8（全曲 4→8、第 1 樂章 3→8、第 2 樂章 4→7、第 3 樂章 2→4、第 4 樂章 1→3）。
- 3 個音效（ocean_ambient_001、ocean_loop_001、restraint_ambient_001）從 2 變 1。
- 其餘商品數字不變（逐列比對見 summary 證據檔兩個 variant 的表）。

- 情境 C 給愛麗絲被搶的 59 次裡：43 次是同音最舊（規則 1），16 次是沒按著的最舊（規則 3），沒有一次搶到還按著的音。
- 被搶當下那顆音剩下的能量（相對它自己起音時；描述用分箱、非 GATE）分布：−10 dB 以內 15 次、−10～−20 dB 13 次、−20～−40 dB 12 次、−40～−60 dB 18 次、−60 dB 以下 1 次。

### 4.3 正常彈法（情境 A）超過 16 的 3 首：時間點與被搶的音

**(a) 月光第一樂章舌鼓版**（`scores/examples/moonlight_sonata_movement1_tongue_drum.score.json`，Chromatic）

- 需求最大 20 顆，在 254.240 s。總共有 63 段時間超過 16，合計 18.43 s。
- 會搶 64 次：規則 2（已放鍵的最舊）34 次，規則 1（同音最舊）30 次。其中 4 次搶到的是還按著的音。
- 被搶當下剩餘能量（描述用分箱）：−10 dB 以內 4 次、−10～−20 dB 7 次、−20～−40 dB 22 次、−40～−60 dB 25 次、−60 dB 以下 6 次。
- 剩最多能量的幾顆：
  - 252.000 s，第 943 顆（57，250.880 s 起音，還按著）被同音第 949 顆搶，剩 −5.6 dB；
  - 254.240 s，第 955 顆（56）剩 −5.8 dB；
  - 53.760 s，第 196 顆（66）和第 195 顆（54）同時被搶，各剩 −6.2 dB。
- 第一次超過在 17.92 s。完整 64 筆在 summary 證據檔「full steal list」。

**(b) 月光第一樂章揚琴＋舌鼓混合版的舌鼓部分**

- 需求最大 20 顆，在 254.258 s。會搶 41 次（規則 2 有 24 次、規則 1 有 17 次），其中 5 次搶到還按著的音。
- 剩最多能量的一顆：254.258 s，第 1912 顆（56），剩 −5.8 dB。
- 揚琴部分最多 10 顆，不超過。

**(c) 月光全曲 FM**（`scores/examples/moonlight_sonata_complete.score.json`）

- 需求最大 196 顆，在 661.700 s；有 93 段超過，合計 165.5 s。會搶 787 次（規則 1 有 416 次、規則 2 有 371 次），2 次搶到還按著的音。
- 剩餘音量分箱（描述用）：−10 dB 以內 94 次、−20～−40 dB 41 次、−40～−60 dB 30 次、−60 dB 以下 622 次。
- 196 的成因用 `fm_zombie_check.py` 在最高點那一瞬間查：
  - 196 顆裡，193 顆已放鍵，其中 100 顆是 32 號音、92 顆是 44 號音。
  - envelope 分箱（描述用；參考線是 24-bit 最小一階 2⁻²³≈−138.5 dB）：184 顆在這條線以下、4 顆在 −60～−138.5 dB、3 顆在 −10～−60 dB、2 顆在 −10 dB 以內、3 顆音量是 0。
  - 這段左手 32/44 兩個音每 0.13 s 交替（例：660.53 s 44、660.66 s 32、660.79 s 44…，每顆時值 0.13 s、`fm_release` 150 ms）。所以同一個音每 0.13 s 就有一次按下或放開，每一次都會把舊 voice 的 release（0.15 s）重新起算，舊 voice 就一直不結束（§1 表內 Envelope.h:29-40 那一條）。
  - float32 加上 `ScopedNoDenormals`（`PluginProcessor.cpp:305`）的情況下，音量掉到約 1e-35 之後，每 sample 的遞減量會被沖成 0，音量就停在那裡。這時 voice 要等「同音停止反覆超過一個 release 長度」才會結束，跟模型算的結束時間一樣。
- 剩最多能量的被搶音：
  - 652.340 s，第 3900 顆（66，30 ms 前才按下）被同音第 3902 顆搶，剩 −0.1 dB。這種同音 30 ms 內重打，即使沒搶，JUCE 的同音規則也會先把它制音。
  - 616.980 s，第 3475 顆（54，已放鍵 0 s）剩 −0.3 dB。

**外掛做得到版多出來的 6 首四季（只在「按引擎」時超過；「按聲部」全部不超過）**

| 樂章 | 需求最大 | 情境 A 搶幾次 | 還按著就被搶 |
|---|---|---|---|
| 春 第1樂章 | 26 | 487 | 20 |
| 冬 第1樂章 | 24 | 241 | 1 |
| 秋 第3樂章 | 20 | 16 | 0 |
| 夏 第3樂章 | 20 | 286 | 16 |
| 夏 第1樂章 | 19 | 13 | 6 |
| 冬 第3樂章 | 19 | 116 | 0 |

- 春第 1 樂章等處常見「同一瞬間同音被好幾個聲部齊奏」（例如 92.087 s 的 B4 有三顆：第 1508、1509、1510 顆）。擠在同一個 channel、pool 又滿的時候，後到的那顆會把先到、同音高的那顆當成「同音最舊」直接搶掉（1509 搶 1508、1510 搶 1509），被搶的那顆才剛起音，剩 0.0 dB。
- 這是把好幾個聲部擠進同一個外掛才會出現的。拆成一個聲部一個外掛就沒有。

### 4.4 跟 pool 大小無關的差異（加大 pool 也不會變）

這些是用「pool 無限大」的模擬數的：一顆還按著的音，在自己放鍵之前就被 JUCE 的同音規則制音。

| 範圍（情境 A、score 版） | 被同音新音制音 | 被別顆的放鍵一起制音 |
|---|---|---|
| 75 首合計，按引擎 | 8361 顆 | 6890 顆（20 首） |
| 75 首合計，按聲部 | 944 顆 | 1732 顆（20 首） |
| **給愛麗絲（商品），按引擎** | **21 顆** | **21 顆** |
| 給愛麗絲，按聲部（右手 up） | 14 顆 | 14 顆 |
| AI Radiance 全曲／第1樂章 Chromatic（商品） | 2 顆 | 1 顆 |

給愛麗絲的例子（summary 證據檔「same-note early damping」有前 40 筆）：

- 第 49 顆 A4 在 9.1667 s 按下，譜上 10.0681 s 才放。10.000 s 第 53 顆 A4 按下，把第 49 顆提前制音。
- 10.0681 s 第 49 顆的放鍵到了，JUCE 把「所有 A4」都放開，第 53 顆在自己起音後 68 ms 就開始制音（它自己的放鍵在 10.4630 s）。

CLI 每顆各自一顆 voice，所以不會這樣。這一項商品也有，而且跟 16 顆無關。

### 4.5 CLI 自己的一個小發現（跟外掛無關，順手記錄）

- `ScoreRenderer.h:1576-1583` 的 `eventEndTime()` 配 buffer 時，所有 modal 引擎一律用放鍵後 0.05 倍的衰減係數。但 Chromatic 實際放鍵用 0.08（CLI 走的 `ChromaticEngine.h:406-412` noteOff；外掛走的 `:267-282` stopNote 也是 0.08）。
- 用 `chromatic_tail_budget_check.py` 掃 75 首（layered 兩首除外）：只有 `scores/library/restraint/restraint_ui_001.score.json`（**商品**）的最後一顆 beam G3 比 buffer 多活 0.272 s。buffer 結束時，這顆音剩下的能量是它起音時的 −69.5 dB。
- 這個數字只記錄、不判定。要不要改屬於 CLI 渲染的變更（R10），不在本卡範圍，寫進 open_items。

---

## 5. 加大 pool 的 CPU 代價（估計）

**量法**（`voice_cpu_bench.py`）：

- 對四種引擎，各做一份乾聲 score：N 顆不同音同時按下、時值 8 s。N＝1/16/32/64，每種跑 3 次、取最快一次。
- 用 CLI 渲染計時，直線擬合「多一顆 voice 多花幾秒」，再除以那顆 voice 的平均壽命（同一條壽命公式），得到「一顆一直在響的 voice 要吃掉幾 % 的一顆 CPU 核心」。
- 機器：AMD Ryzen 5 3500X（6 核 6 執行緒，`Win32_Processor` 查得）、Windows 10。三輪量的時候同機都還有其他卡在跑（run3 當下另有 TsukiSynthCLI、HostProbe 在跑），數字可能偏高，只當量級看。

跑了三輪（run1／run2 是前任、run3 是接手者），三輪數字都列：

| 引擎（參數取自） | 每多一顆 voice 多花（s，run1／run2／run3） | 平均壽命 s | 一顆持續發聲的 voice 約佔單核（run1／run2／run3） |
|---|---|---|---|
| Cimbalom／piano（給愛麗絲） | 0.0751／0.0769／0.0723 | 2.838 | **2.65%／2.71%／2.55%** |
| Cimbalom／string（四季冬） | 0.0210／0.0144／0.0126 | 0.921 | 2.28%／1.56%／1.37% |
| Chromatic／tongue_drum（月光舌鼓） | 0.0103／0.0072／0.0065 | 6.435 | 0.16%／0.11%／0.10% |
| FM（月光全曲） | 0.0302／0.0222／0.0221 | 7.200 | 0.42%／0.31%／0.31% |

限制（照實列出）：

1. 量的是 CLI，不是外掛。外掛多了 BodyResonance（Macro Body 0.5 時有開）、EffectChain，而且不是整段一次算完，是每個 block 算一次。
2. JUCE 每個 block 會對**每一顆** voice 呼叫 `renderNextBlock`，不管有沒有在用（`juce_Synthesiser.cpp:254-258`）。Cimbalom／Chromatic 閒置的 voice 仍會逐 sample 跑一次迴圈，加上 BodyResonance 的 3 個濾波器（`CimbalomEngine.h:817-859`、`ChromaticEngine.h:593-672`、`src/dsp/BodyResonance.h:55-68`）。所以加大 pool，閒置時也會多一點 CPU。這部分本卡沒量，只照程式碼描述。
3. 粗估，只照上表乘法（滿載＝多出來的每一顆都在響）：
   - Cimbalom 從 16 顆加到 26 顆（四季外掛做得到版、按引擎的最大需求；四季是 string）：多 10 顆 × 1.37～2.28% ≈ **多 14～23% 單核**。
   - 同樣加到 26 顆、但拿來彈鋼琴（piano 每顆 2.55～2.71%）：多 10 顆 ≈ **多 25～27% 單核**。
   - 只加到 22 顆（情境 C 給愛麗絲的需求，piano）：多 6 顆 × 2.55～2.71% ≈ 多 15～16% 單核。
   - Chromatic 從 16 加到 20：多 4 × 0.10～0.16% ≈ 0.4～0.6%。
4. FM 的 196 顆不是加大 pool 該解決的東西（見 §4.3(c)），不列入估算。

證據：`reports/gate_outputs/wf0925_V1_voice_pool_cpu_bench.txt`。

---

## 6. 給月月的選項（並列，不替你選）

| 選項 | 內容 | 對商品的影響 | 代價／前提 | 要動的檔 |
|---|---|---|---|---|
| **A. 加大 pool** | 例如 Cimbalom 16→26、Chromatic 16→20 | 商品在情境 A/B 本來就 0 超過，不變。情境 C（踩踏板）給愛麗絲要 22 顆、AI Radiance FM 要 19 顆，加大後才不搶 | 滿載多 CPU（§5，Cimbalom +10 顆約 +14～27% 單核，看彈的是弦樂還是鋼琴）；閒置 voice 也吃一點 CPU。CLI 不經過 pool，8 首位元不變基準不受影響，但外掛輸出在密集段會改變（這正是目的）。**不能解決** §4.4 同音提前制音和 FM 舊 voice 不結束 | `src/PluginProcessor.cpp:36/71/105`（R6/R7，要你點頭） |
| **B. 寫進主張域** | 文案寫明：外掛每個引擎同時最多 16 顆，超過時照 JUCE 規則搶最舊的；同音重疊時照 JUCE 同音規則處理；物理驗證（GATE）只涵蓋 CLI 渲染 | 無 | 不改程式；要改 ENGINE_DOMAIN_CLAIMS 與變現文案 | 文件 |
| **C. 維持現狀** | 不改 | 商品在情境 A/B 為 0 超過 | 買家若踩延音踏板彈密集段、或把多聲部塞進同一個外掛，會被搶音；§4.4 的差異照舊 | 無 |

另外兩件可以單獨處理（跟上面三選一無關，也都要你點頭，也都會改外掛輸出）：

- **FM 舊 voice 不結束**：例如讓 `Envelope::noteOff()` 對已在 Release 的 voice 不再重算。會改 FM 外掛輸出；CLI 每事件一顆 voice，理論上不受影響，但仍要用 8 首位元不變驗證。
- **同音提前制音**：例如外掛改成同音不互相制音（需要自訂 `findFreeVoice`／noteOff 邏輯）。會改外掛行為。或者寫進主張域。

---

## 7. 沒做的、做不到的

- **沒用 HostProbe 讓外掛真的串流演奏再跟 CLI 比。** 那是 APPENDIX 建議的第二段，要改 `tests/host_probe.cpp`，超出本卡範圍。本報告全部是照程式碼規則推算的估計。
- **FM voice 壽命沒實測**：原因見 §3。
- **外掛的 `damping_override` 缺口**只用「拿掉參數」一種方式估。Macro Damping 旋鈕可以把全部 T60 一起乘 0.3～1.7（`dmpScale`），能不能逼近 score 的衰減，沒算。
- **沒量真實 DAW**：block 大小、子區塊顆粒度都沒量（M4）。
- **layered score**（AI Radiance 全曲、layered_transition）：用 CLI layered dump 自己報的 layer 偏移接起來。region 裁切在 MIDI 演奏裡做不到，所以這兩首的 leaf 事件全部保留（兩首的 region 起點都是 0）。
