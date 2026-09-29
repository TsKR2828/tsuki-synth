# D9 裁決包：真實 IR 載入響度對齊（ALGO vs 真實 IR，EchoThief 3 顆量測）

> 工作卡：`docs/workcards/WF0914_D9b_ir_injection.md`（C++ lane，執行 Sonnet）
> 上游背景：`docs/workcards/WF0914_D9_ir_loudness.md`（原研究卡，BLOCKED——量測鏈本身
> 不接受外部 IR，見 `reports/gate_outputs/wf0914_D9_ir_measure.txt` §4）、
> 月月 2026-09-15 裁決「D9 選 (a)」——本卡是那個決定的落地。
> 日期：2026-09-16　工作樹 branch `fix/deep-physics-audit-20260716`（本卡未 commit）
> 數字來源：`build-wf\Release\TsukiSynthAuditTest.exe`
> （`reportReverbWetGainQuantification()` 與新函式
> `reportReverbWetGainQuantificationExternalIr()`，`tests/audit_repro.cpp`）
> 完整命令與原始輸出：`reports/gate_outputs/wf0914_D9b_ir_injection.txt`
> **本卡不改 DSP、不改 `0.15`、不改 convolution 參數** —— 只量測、只寫此裁決包。

---

## §0 一句話結論

3 顆真實空間錄製的 EchoThief IR，載入後 wet 路徑輸出的響度相對 ALGO 皆落在
**−28.5 dB 到 −28.7 dB** 之間（三顆彼此只差 0.24 dB），跟 K-02 既有基準用的合成 IR
（−28.483 dB）幾乎一樣，儘管這 3 顆 IR **檔案本身**的寬頻能量彼此差了 16.6 dB。
這代表 EffectChain 的 convolution 路徑本來就對載入的 IR 做能量正規化
（`Convolution::Normalise::yes`，JUCE 預設值，見 §2 溯源），所以「IR 比 ALGO 小
28.5 dB」這個落差**不是**因為真實 IR 檔案energy比較小，也不會因為換一顆真實 IR
就自動消失或縮小——它是 ALGO（回饋式 comb/allpass）與 IR（一次性正規化摺積）
兩種演算法結構性的響度差異，跟 K02 裁決包已有的結論一致，本卡用真實資料再次
證實。**不替月月選**；三案列在 §5。

---

## §1 現況（file:line，沿用 K02 裁決包，本卡未變動）

- `src/effects/SimpleReverb.h:155-156`：ALGO wet 分量固定多乘 `0.15`（未溯源常數，
  R4 只禁新增，不要求追溯既有）。
- `src/effects/EffectChain.h:89-96`：`EffectChain::loadImpulseResponse()` 呼叫
  ```cpp
  convolution.loadImpulseResponse (file,
                                   juce::dsp::Convolution::Stereo::yes,
                                   juce::dsp::Convolution::Trim::yes,
                                   0);
  ```
  最後一個 `Normalise` 參數未指定，取宣告預設值 `Normalise::yes`
  （`libs/JUCE/modules/juce_dsp/frequency/juce_Convolution.h:242`，File 版 overload；稽核 2026-09-16 更正，原誤引 :227=記憶體版）。

## §2 JUCE Convolution 的實際行為（本卡新溯源，供裁決依據，非工程假設）

讀 `libs/JUCE/modules/juce_dsp/frequency/juce_Convolution.cpp`：

- `ConvolutionEngine`/`EngineWithZeroLatency::makeEngine()`（約行 785-803）：
  ```cpp
  auto resampled = resampleImpulseResponse (impulseResponse, originalSampleRate, processSpec.sampleRate);
  if (wantsNormalise == Convolution::Normalise::yes)
      normaliseImpulseResponse (resampled);
  else
      resampled.applyGain ((float) (originalSampleRate / processSpec.sampleRate));
  ```
  **取樣率**：`resampleImpulseResponse(...)` 這行無條件執行（沒有先比對
  `originalSampleRate == processSpec.sampleRate` 才跳過），任何取樣率的 IR 都會被
  自動重取樣到目前的 ProcessSpec 取樣率（本卡渲染在 48 kHz；EchoThief 檔案原生
  44.1 kHz，見 `reports/gate_outputs/wf0914_D9_ir_measure.txt` §3）——**不拒收，
  自動轉換**。
  **響度**：因為 EffectChain 用的是預設 `Normalise::yes`，`normaliseImpulseResponse()`
  這個分支會執行（不是 `applyGain(originalSampleRate/processSpec.sampleRate)`
  那個單純取樣率補償分支）——**產品程式碼現在載入任何 IR 檔案時，本來就會對它
  做能量正規化**，這不是本卡新增的行為，只是本卡第一次量出「正規化後，不同
  真實 IR 檔案彼此的 wet 響度差異有多小」這個數字（見 §3）。
- `loadStreamToBuffer()`（約行 709-724）：`AudioFormatManager::createReaderFor()`
  失敗時回傳空、`sampleRate=0.0` 的 buffer，convolution 會靜默地用空 IR 繼續跑，
  **不會報錯**——這是本卡在 `tests/audit_repro.cpp` 新函式裡，呼叫
  `EffectChain::loadImpulseResponse()` 之前先自行驗證檔案可讀、失敗就主動報錯
  （fail-closed）的原因，避免量出一個看似合理但其實來自空 IR 的假數字。

## §3 實測數字（本卡新量，方法逐項照抄既有 K-02）

命令：`build-wf\Release\TsukiSynthAuditTest.exe`（設 / 不設
`TSUKI_K02_EXTERNAL_IR` 各跑一次），完整輸出見
`reports/gate_outputs/wf0914_D9b_ir_injection.txt` §3-4。
方法（與 K02 裁決包完全相同）：48 kHz、固定種子（271828）白噪 2 s burst
+ 12 s 靜音尾段，`mix=1.0`；ALGO 用 reverb 預設；量出 ALGO 的實際 T60 只作為對照
基準本身量測用（**外部 IR 的 T60 不強制對齊**，因為真實 IR 檔案的衰減特性是它
自己的物理性質，強制對齊會扭曲量測目標——這點與既有合成 IR 基準的做法不同，
既有基準特意反推合成 IR 的 T60 去對齊 ALGO 以隔離出「只換 IR 來源」這個變因，
本卡三顆真實 IR 用它們原生的衰減特性，量的是「使用者實際載入這顆真實 IR 時」
的響度落差）。

| IR | 來源 | wet 穩態 RMS（dBFS） | 量得 T60（s） | RMS 差（IR−ALGO，dB） | IR 檔本身寬頻 RMS／長度\* |
|---|---|---:|---:|---:|---|
| ALGO（對照組） | -- | **1.857**（四次重跑一致） | 1.173333 | -- | -- |
| 合成 IR（既有 K-02 基準，T60 對齊 ALGO） | 本卡合成（既有函式） | -26.626 | 1.173333 | **-28.483** | -- |
| Stairwells（小空間／樓梯間） | EchoThief | -26.869 | 2.080000 | **-28.726** | RMS=-25.054 dBFS，長度 2.276 s |
| Venues（廳／音樂廳） | EchoThief | -26.630 | 1.066667 | **-28.487** | RMS=-41.670 dBFS，長度 1.429 s |
| Sanctuaries（教堂／座堂） | EchoThief | -26.766 | 2.613333 | **-28.623** | RMS=-32.345 dBFS，長度 2.941 s |

\* IR 檔本身的寬頻 RMS／長度取自 `reports/gate_outputs/wf0914_D9_ir_measure.txt` §3
（同一批已驗證 SHA256 的檔案；用 soundfile+numpy 直接讀 WAV 樣本算，本卡未重算）。

**核心觀察**：3 顆真實 IR 的 wet RMS 展幅只有 0.24 dB（-26.869 至 -26.630），
遠小於這些 IR 檔案本身寬頻 RMS 的 16.6 dB 展幅（-41.670 至 -25.054）。三顆真實
IR 與既有合成 IR 基準（-26.626 dBFS）的差距分別是 0.243 dB、0.004 dB、0.140 dB
——幾乎重合。這證實 §2 溯源的推論：JUCE 的載入時正規化已經把「不同 IR 檔案
本身有多大聲」這個變因壓得很小，真正主導 ALGO/IR 落差量級的是兩種演算法的
結構性差異（回饋式 comb/allpass vs 一次性正規化摺積），不是特定某顆 IR 檔案
剛好比較安靜或比較大聲。

## §4 corpus／Rule 10 查證（沿用 K02 已核實的結論，本卡未重新查證）

`reports/gate_outputs/wf0907_E7_reverb.txt`（WF0907-E7）已核實並逐字記錄：
「CLI 的 ScoreRenderer 不使用 EffectChain 的 IR 分支（ScoreRenderer 只用
SimpleReverb 直接介面，見 grep 結果：EffectChain.h 只被 PluginProcessor.h 與
tests/physics_models_repro.cpp include）」。也就是說 corpus（75 首代表曲）的
CLI 渲染完全不觸發 `EffectChain` 的 convolution/IR 分支，**任何只影響 IR 路徑
的修正（下方選項 A）理論上不觸發 R10**；但和 K02 裁決包 §3 選項 A 的措辭一樣，
這是「理論上」——真正把某個選項落地前，仍須按 R10 對 8/8 位元不變腳本重新驗證，
本卡不做落地、不重跑該腳本（本卡不修 DSP）。

## §5 三個選項（看數字自己選，不替月月裁決）

| 選項 | 做法 | 本卡新數字帶來的資訊 | Rule 10 衝擊 |
|---|---|---|---|
| **A** | 載入時能量正規化：**JUCE 的 `Convolution::Normalise::yes` 已經在對 IR 檔案本身做正規化**（§2/§3），但正規化目標是「讓不同 IR 檔案彼此的響度接近」，不是「讓 IR 路徑整體響度對齊 ALGO 路徑」。要讓兩者對齊，需要在 EffectChain 的 wet/dry 混合處**額外乘一個常數增益**去補償這 −28.5 dB 左右的結構性落差（正規化定義候選：以本卡 3 顆真實 IR + 既有合成 IR 共 4 組樣本的平均落差 −28.58 dB 反推增益係數 `10^(28.58/20)≈26.9`；**DECIDED CONVENTION 待月月定**——樣本數只有 4、只涵蓋 3 種空間尺度，是否足夠代表任意使用者自帶 IR 尚待裁決）。 | 本卡證實這個落差對「哪一顆 IR」不敏感（3 顆真實 IR 只差 0.24 dB），所以一個固定增益常數校正大部分情境應該有效——但仍是基於 4 個樣本的外推，不是窮舉。 | 只影響 plugin 的 IR 模式；§4 已核實 CLI/corpus 不觸發此分支，**理論上不觸 R10**，落地前仍須重跑 8/8 位元不變腳本確認。 |
| **B** | 不對齊，UI 顯示 IR 相對響度資訊（配合 F-03 三態顯示，`src/IRLibrary.h`） | 本卡的 4 個「RMS 差」數字（-28.483 / -28.726 / -28.487 / -28.623 dB）可以直接當作 UI 提示文案的參考範圍（例如「切換到 IR 模式時響度通常會下降約 28-29 dB」）。 | 不改任何渲染輸出，零 Rule 10 衝擊。 |
| **C** | 維持現狀＋文件記載（K02 裁決包 §5 月月已對「合成 IR」情境選過這案） | 本卡的真實 IR 數字進一步支持這個判斷是穩健的——不是「剛好合成 IR 量出來的落差比較極端」，換成 3 顆風格迥異的真實空間 IR，落差量級幾乎不變。 | 零 Rule 10 衝擊。 |

## §6 授權提醒（沿用 `wf0914_D9_ir_measure.txt` §1 記錄，本卡量測用到同一批檔案，重申）

EchoThief IR（`external_data/ir/echothief/`，本卡三顆量測樣本的來源）授權文字
逐字記錄在 `wf0914_D9_ir_measure.txt` §1，重點摘錄：SDSURF 的 EchoThief License
明文禁止「embedding of EchoThief in software, applications, or other products
intended for distribution, sale, or other commercial exploitation」。
**本卡與 D9 研究卡下載的 EchoThief IR 僅供私下量測參考用，授權不可隨 TsukiSynth
產品散布或內嵌；若日後選項 A／B 的落地需要在產品裡「附帶」任何 EchoThief IR
檔案本身（例如當作出廠內建的示範 IR），必須先向 SDSURF（innovation@sdsu.edu）
另外取得商業授權**——這件事跟「用它量出的數字」是分開的：數字（−28.5 dB 這類
統計量）本身沒有著作權疑慮，可以自由使用；IR 音訊檔案本體才是需要授權的部分。

---

## §7 與原 D9 研究卡的關係（記錄，非重複勞動）

`docs/workcards/WF0914_D9_ir_loudness.md`（原卡）已完成 §1 來源／授權調查與
EchoThief 3 顆 IR 的下載＋SHA256＋IR 檔案本身寬頻 RMS／長度量測，記錄在
`reports/gate_outputs/wf0914_D9_ir_measure.txt`；該卡在 §2「wet 路徑輸出響度
相對 ALGO 差多少 dB」卡關（量測鏈 `tests/audit_repro.cpp` 當時不接受外部 IR，
且原卡被指派在不能改 `tests/` 的研究 lane），如實回報 BLOCKED，未產出裁決包。
本卡（D9b）依月月 2026-09-15「D9 選 (a)」裁決，在 C++ lane 補上外部 IR 注入點
（見 `reports/gate_outputs/wf0914_D9b_ir_injection.txt` §0），把原卡卡住的那個
數字補齊，本裁決包即為原 D9 卡 §3 要求的裁決包產出。

---

## 裁決記錄

**2026-09-16 月月裁決：選項 A（IR wet 路徑補固定增益，DECIDED CONVENTION）**。
依據：本包 §3 實測——落差為結構性固定值（三顆真實 IR + 合成 IR 皆 −28.49～−28.73 dB，
展幅 0.24 dB），與 IR 檔案本身響度（展幅 16.6 dB）無關。
落地卡：`docs/workcards/WF0914_D9c_ir_makeup_gain.md`。增益常數 ×26.9（+28.58 dB，
4 樣本平均反推）標為 DECIDED CONVENTION，非物理常數；只影響 plugin IR 模式 wet 路徑，
corpus 75 首不經此路（本包 §4 已核實），落地卡仍須重跑 8/8 位元不變證明。

---

## 附記（2026-09-25，WF0925-K1，staged-review:D9c-calib）：×26.9 的對齊參考設定

對齊參考＝ALGO 預設 size 0.5、未指定 T60；其他 size 依 Python 複製版估計差 −1.4～+4.0 dB、其他 T60 差 −2.4～+5.3 dB（估計，非量測產品 binary）。

- 依據：§3 的量測方法段已寫「ALGO 用 reverb 預設」——也就是 `pReverbSize`／`pReverbDecay` 都沒設（roomSize 0.5、沒有指定 T60），見 `tests/audit_repro.cpp` K-02 量測函式內「ALGO, reverb defaults」那段註解。IR 路徑本身不看 size／T60（`src/effects/EffectChain.h` 的 `processBlock()` 在 irMode 時不呼叫 `setRoomSize()`／`setDecayTime()`），所以 ×26.9 讓兩條路響度一致，只在這組預設下成立。本包原本沒寫清楚的是這層依賴。
- 數字出處：`reports/status_check_2026-09-25/probes/reverb_gain_replica_output.txt`（同目錄 `reverb_gain_replica.py` 用 Python 複製 SimpleReverb 的 comb／allpass 結構，白噪穩態 wet RMS，相對 size 0.5）：size 0.00 −1.36／0.25 −0.79／0.75 +1.23／1.00 +3.98 dB；decay 0.3 s −2.38／1.0 s −0.40／3.0 s +1.76／10 s +3.89／30 s +5.26 dB。同檔另列複製版的 IR wet（×26.9）減 ALGO@0.5：−0.11／+0.13／+0.57 dB，對照 D9c 實測 −0.131／+0.108／−0.028 dB。**以上都是複製版估計，不是對產品 binary 的量測。**
- 純說明：×26.9 數值不變、渲染不變；程式端同一段說明已補進 `src/effects/EffectChain.h` 的 `kIrWetMakeupGain` 註解。要不要做成使用者看得到的說明，仍待月月決定（未裁決）。

---

## 附記（2026-09-25，WF0925b-DS；WF0925 交接 E18 未竟項）：×26.9 裡約 18.06 dB 綁在 JUCE 內部常數上

- **事實**：IR 模式的摺積用 `juce::dsp::Convolution`。`src/effects/EffectChain.h` 的 `loadImpulseResponse()`（:89-96）呼叫 `convolution.loadImpulseResponse (file, Stereo::yes, Trim::yes, 0)`，沒有傳第 5 個參數，所以用宣告預設值 `Normalise::yes`（`libs/JUCE/modules/juce_dsp/frequency/juce_Convolution.h:240-242`）。
  正規化在 `libs/JUCE/modules/juce_dsp/frequency/juce_Convolution.cpp`：`makeEngine()` 在 `wantsNormalise == Convolution::Normalise::yes` 時呼叫 `normaliseImpulseResponse (resampled)`（:789-790）；係數由 `calculateNormalisationFactor()`（:623-629）算，第 628 行是 `return 0.125f / std::sqrt (sumSquaredMagnitude);`——把能量最大的那個聲道縮到平方和為 1，再乘 0.125。20·log10(0.125) = −18.06 dB。
  所以 D9c 補回的 ×26.9 裡，約 18.06 dB 是在抵銷 JUCE 這個固定係數，不全是 ALGO 與 IR 兩種演算法本身的差（2026-09-25 盤點 E18 的查證修正；上面三個行號本卡用 grep 重新確認過）。版本：submodule `libs/JUCE` 在 `501c076`，`libs/JUCE/modules/juce_core/system/juce_StandardHeader.h:42-44` 是 JUCE 8.0.12。
- **後果**：WF0925-K2 加的 D9c-guard 只檢查 `kIrWetMakeupGain == 26.9f`。JUCE 升版如果改了 0.125（或改了正規化方式），26.9 沒變、guard 照樣 PASS，IR 模式的響度卻會漂，現有 GATE 擋不住。要不要加響度判定或做成正式檢查清單，見 `reports/decision_packets/WF0925_open_decisions.zh-TW.md` Q01（B／C 案）。
- **升 JUCE 前要做的事**（程序提醒，不是新門檻）：升版後先重建測試 target，直接跑 `TsukiSynthAuditTest`，看 `[K-02] RMS difference (IR - ALGO)` 那行跟升版前有沒有變（WF0925 整合卡的值是 0.112 dB，`reports/gate_outputs/wf0925_integration_raw/04b_audit_repro_direct.txt`）；手上有真實 IR 時也用 `TSUKI_K02_EXTERNAL_IR` 重跑 K-02-EXT；並再看一次上面 `juce_Convolution.cpp` 三處的內容有沒有變。有變就停下來，帶數字給月月裁決，不自己改 26.9。
- **用詞備註**（WF0925 K 稽核 note，只是用詞）：本包與程式註解寫的「+28.58 dB」是 4 樣本平均落差的原數字；把 26.9 倍嚴格換成 dB 是 20·log10(26.9) = 28.595 dB。數值本身不變。
- 本附記只加說明：×26.9 數值不變、渲染不變。`EffectChain.h` 的 `kIrWetMakeupGain` 註解還沒補「約 18.06 dB 來自 JUCE 0.125 正規化」這句，要改 `src/` 得另開卡（本卡不動 `src/`）。
