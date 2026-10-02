# Q05 根因調查：工廠 preset 7／11／15 彈一個音為什麼就超過 0 dBFS

> 卡號：WF1002-R（R-a，唯讀研究卡）　日期：2026-10-02　基底：HEAD `b41298c`
> 對應裁決：`reports/decision_packets/WF0925_open_decisions.zh-TW.md` Q05（10-02 裁定「C＋根因卡」）
> **本卡沒有改 `src/`、`tools/`、`tests/`、`scores/` 或任何既有檔。** 只新增本報告與 `reports/gate_outputs/wf1002_R_a_*.txt`（4 份）。
> 量測用的是 `build\` 現成 VST3（09-30 INT 建置）的複本，加上一支只存在 repo 外的研究用小程式（`r_probe`，見 §1）。
> 本報告所有數字都是**描述用、不是 GATE、不是新門檻**（R2）。**不替月月選。**

---

## §0 白話結論（先看這段就夠）

1. **不是 B6 的錯。** B6 的「絕對聲壓慣例錨定」（`RadiationModel`）只活在 CLI 的 `--dump-modes` 診斷輸出裡，
   外掛的發聲路徑一次都沒有呼叫它（§6 有逐行證據）。它不會讓外掛變大聲。
2. **引擎本身不吵。** 三個 preset 拿掉所有後段處理之後，引擎原始輸出的峰值是 −16.8／−10.1／−16.4 dBFS，
   跟其他 24 個 preset 在同一個範圍。引擎的音量常數（0.069、0.151、0.180）是在 CLI 校準的，校準時**沒有 Body 層、沒有效果器**。
3. **真正的原因：外掛在引擎後面又疊了三層「只會加、不會扣」的增益，沒有任何一層把音量扣回來。**
   - **(a) Body 層**：它的兩個共振濾波器被調到「正好對準這顆音的基頻和第二泛音」。
     Body 0.8 時，基頻被放大 **+15.2 dB**（公式算的），實測峰值也正好大了 **+15.1 dB**。
   - **(b) 壓縮器的自動補償（makeup）**：只要 Ratio 大於 1，就固定再加 **+4.5 dB**（預設 −12 dB／4:1）或 **+5.0 dB**（−15 dB／3:1）。
     不管訊號有沒有真的被壓，這個補償都會加上去。27 個工廠 preset 全部都開著壓縮器。
   - **(c) 殘響的 wet 累積**：房間開大（size 0.78～0.90）、聲音又很長的時候，殘響尾巴的能量會一直疊上去，
     比送進殘響的聲音大 **+5.8～+10.8 dB**（RMS）。三個 preset 最大的那一個樣本，**93%～100% 是殘響尾巴**，不是敲擊瞬間。
4. **三個 preset 各踩到哪幾層**（數字是峰值增加量，詳表在 §2）：

   | preset | 引擎原聲 | Body 層 | 壓縮器 | Delay | 殘響 | 最後 |
   |---|---|---|---|---|---|---|
   | 7 Copper Warm Strings (Body) | −16.79 | **+15.12** | +2.88 | 0 | −0.88（但最大樣本是 231 ms 的殘響尾巴） | **+0.33 dBFS** |
   | 11 Ethereal Steel Bells | −10.13 | 0（沒開） | +4.50 | −1.94 | **+9.04** | **+1.47 dBFS** |
   | 15 Bronze Water Gong (Body) | −16.37 | +4.97 | +4.50 | 0 | **+9.55** | **+2.65 dBFS** |

   - 7 號：主因是 **Body 層**。
   - 15 號：**殘響＋Body＋壓縮補償**三層一起。
   - 11 號：**殘響＋壓縮補償**；它的引擎是 Custom Harmonics，本來就沒有響度補償（設計如此，`ChromaticEngine.h:225-232` 註解），引擎原聲在 27 個裡最大聲。
5. **共同因子**：引擎原聲不低（≥ −16.8 dBFS），而且後段三層疊加的總增益是 +11.6～+19.0 dB。
   其他 24 個 preset 至少有一項低於這兩個數字。最接近的是 9 號（15 號的無 Body 版）：引擎 −16.37、後段 +11.50，峰值 −4.87 dBFS（§3）。這兩個數字只是描述，不是門檻。
6. **跟這三個無關但順手量到的**：
   - Body 的預設值是 0.5（`ParameterLayout.cpp:47`），在基頻上已經是 +11.9 dB。
     例如把 11 號的 Body 從 0 推到 0.5，輸出峰值是 **+8.30 dBFS**。所以使用者自己調的音色也很容易超過。
   - 多弦同時起振：外掛用 `1/√N` 把 N 根弦的音量平均（`CimbalomEngine.h:331`），但敲下去的瞬間 N 根弦同相，
     峰值其實跟著 √N 長。7 號用 5 根弦，比 3 根多 +2.2 dB、比 1 根多 +7.0 dB（實測，跟 √5 理論值一致）。這是次要因素。
7. **修法**：§7 列了 8 個方案，每案都寫出會改哪些聲音（R10）和工作量。**本卡不選。**

---

## §1 方法（怎麼量的）

- **binary**：`build\` 的 `TsukiSynth.vst3`、`TsukiSynthHostProbe.exe`、`TsukiSynthCLI.exe` 複製到 `output/wf1002/R/bin/`，sha256 與原檔一致。
  證據：`wf1002_R_a_setup.txt`。
- **先重現**：用 HostProbe 複本重跑。215 PASS、0 FAIL；E16 的 27 行峰值／RMS 跟 09-25 K2 的數字**逐字相同**。
  證據：`wf1002_R_a_hostprobe_e16_rerun.txt`。
  - 也就是說，09-30 的 binary 跟 09-25 時的數字一樣：7 號 +0.33、11 號 +1.47、15 號 +2.65 dBFS。
- **研究用小程式 `r_probe`**（不在 repo、不進建置）：
  - 跟 HostProbe E16 一樣，從磁碟載入 VST3、`setCurrentProgram(i)`。
  - 可以指定把某幾個參數改成某個值，換算用的是產品自己的 `createTsukiParameterLayout()`。
  - 演奏 C4、力度 0.7，1.0 秒放鍵，取 2.0 秒（跟 E16 同長度 96256 樣本）。
  - 改參數要等下一個 block 才生效，而且效果器有 20 ms 的平滑。為了不讓這段過渡污染起音，每次都先跑 8 個靜音 block，再按下琴鍵。
    檢查：168 次渲染的靜音段全部是 0；不改參數的那 27 次，跟 E16 的峰值／RMS 差距 ≤ 0.005 dB（E16 只印到小數第 2 位）。
  - 建置在 `git archive HEAD` 取出的隔離副本裡，放在 repo 外的 scratch 目錄。JUCE 用 junction 連過去，量完用 `cmd /c rmdir` 只拆連結。
    之後 JUCE 檔案數仍是 4378，`git status` 乾淨。
- **怎麼拆成「逐級」**：從訊號鏈的**尾巴往前**一級一級關掉，每一步都**精確**等於前一級的輸出。
  - 外掛的訊號順序是：引擎 → Body 層 → 失真 → 壓縮器 → Delay → 殘響 → EQ → Output。
    出處：`EffectChain.h:199`、`PluginProcessor.cpp:407-420`。三個 preset 的失真 drive 都是 0、EQ 都是 0 dB，所以這兩級本來就是旁路。
  - 殘響 mix＝0 → 輸出等於 Delay 之後（`SimpleReverb.h:154-156`，dry＝1−mix）。
  - 再加 Delay mix＝0 → 等於壓縮器之後。
  - 再加壓縮器 Ratio＝1 → 等於引擎總和（`Compressor.h:30` 直接旁路）。
  - 再加 Body＝0 → 等於沒有 Body 層的引擎原聲。
  - 這三種效果器（殘響、Delay、Output）對輸入都是線性的，所以殘響的 wet 可以**精確**拆出來：wet ＝ 輸出 −（1−mix）× 殘響輸入。
- **一個意外**：第一輪量測做到一半時，整個 `output/wf1002/R` 被不明程序刪掉了（不是本 lane。研究子代理回報它沒有刪任何資料夾）。
  JUCE 事後檢查完好。所有數字都是重做後的版本，隔離樹也搬到 repo 外，避免再發生。詳見 `wf1002_R_a_setup.txt`。

## §2 增益鏈逐級表（三個超標 preset）

| 級 | 程式位置 | 7 Copper Warm Strings (Body) | 11 Ethereal Steel Bells | 15 Bronze Water Gong (Body) |
|---|---|---|---|---|
| 引擎原聲，不含 Body 層（t0） | 引擎常數：Cimbalom `×0.069`（`CimbalomEngine.h:878`）；Chromatic gong `0.151`、custom `0.180`（`ChromaticEngine.h:695-698`）；響度補償 `loudnessCompensationGain`（custom 不套） | **−16.79** dBFS（銅、5 弦、Felt） | **−10.13**（Custom Harmonics，8 個泛音振幅和 3.18，不套槌頻譜和響度補償） | **−16.37**（青銅板） |
| ＋Body 層（t1） | `BodyResonance.h:55-68`：輸出＝乾聲＋amount×4×(1.4×BP(f1)＋0.8×BP(f2))×LP500。f1/f2＝這顆音自己的第 1、2 個模態（`CimbalomEngine.h:906-909`、`ChromaticEngine.h:717-720`） | **+15.12** → −1.67（Body 0.80） | 0（Body 0）→ −10.13 | **+4.97** → −11.40（Body 0.85；含幾何連動，見 §4） |
| ＋失真 | drive 0 → 旁路 | 0 | 0 | 0 |
| ＋壓縮器（t2） | `Compressor.h:51` makeupDB ＝ −threshold×(1−1/ratio)×0.5，**每個樣本都乘** | **+2.88**（−15 dB／3:1：makeup +5.0，實際壓了約 2.1 dB）→ +1.21 | **+4.50**（預設 −12／4：makeup +4.5，沒壓到）→ −5.63 | **+4.50**（同左）→ −6.90 |
| ＋Delay（t3） | `StereoDelay.h:73-75` dry＝1−mix | 0（mix 0）→ +1.21 | **−1.94**（mix 0.20 → dry 0.8）→ −7.57 | 0 → −6.90 |
| ＋殘響（t4） | `SimpleReverb.h:155` 輸出＝(1−mix)×乾＋0.15×mix×(8 個 comb＋4 個 allpass) | −0.88 → **+0.33**（mix 0.35／size 0.78） | **+9.04** → **+1.47**（0.55／0.90） | **+9.55** → **+2.65**（0.45／0.85） |
| ＋EQ、Output | EQ 0 dB 旁路；Output 預設 1.0（`ParameterLayout.cpp:53`） | 0 | 0 | 0 |
| **最大樣本的時間與組成** | §5 | 231 ms；wet 佔 **99.8%** | 915 ms；wet 佔 **102%**（乾聲跟 wet 反相） | 548 ms；wet 佔 **93.4%** |

讀表說明：每一格的「+x」是這一級讓**整段 2 秒的最大值**變大多少。
7 號的殘響那格是 −0.88，因為殘響把起音瞬間的乾聲壓到 65%；可是 231 ms 時殘響尾巴自己累積到 +0.31 dBFS，所以最後的峰值是尾巴造成的。

證據：`wf1002_R_a_taps_raw.txt`（168 次渲染的原始輸出）、`wf1002_R_a_analysis.txt` [1][2]。

## §3 27 個 preset 的分布與共同因子

完整表在 `wf1002_R_a_analysis.txt` [1]。每列都有 t0→t4 各級峰值，以及 Body、壓縮器、Delay、殘響各自的增減量。重點：

| 排名 | preset | 輸出峰值 | 引擎原聲 t0 | 後段總增益 t4−t0 | 主要貢獻 |
|---|---|---|---|---|---|
| 1 | 15 Bronze Water Gong (Body) | **+2.65** | −16.37 | **+19.02** | 殘響 +9.6、Body +5.0、補償 +4.5 |
| 2 | 11 Ethereal Steel Bells | **+1.47** | **−10.13** | +11.60 | 殘響 +9.0、補償 +4.5 |
| 3 | 7 Copper Warm Strings (Body) | **+0.33** | −16.79 | **+17.12** | Body +15.1、補償 +2.9 |
| 4 | 6 Steel Hammered Dulcimer (Body) | −2.77 | −19.21 | +16.44 | Body +14.0、補償 +4.4 |
| 5 | 20 DX7 Crystal Bell | −4.57 | −23.06 | +18.49 | 殘響 +14.0、補償 +4.5 |
| 6 | 9 Bronze Water Gong（15 號的無 Body 版） | −4.87 | −16.37 | +11.50 | 殘響 +7.0、補償 +4.5 |
| 7 | 14 Crystal Tongue Drum (Body) | −6.94 | −28.05 | **+21.11** | Body +12.3、殘響 +4.3、補償 +4.5 |
| … | … | … | … | … | … |
| 27 | 13 Rubber Tongue Pad | −39.78 | −38.38 | −1.40 | — |

- **壓縮器補償**：27 個 preset 全部都有，大小 +2.0～+7.5 dB。只要沒有真的壓到，實測值就等於公式值（例：5 號 −18/6 → +7.50）。
- **Body 層**：6 個 preset 有開（6、7、14、15、25、26），讓峰值增加 +0.65～+15.12 dB。
- **殘響**：size ≥ 0.85 而且聲音夠長的 preset，殘響這一級是 +7.0～+14.0 dB（9、11、12、15、20、21、22）。
  size 小或聲音短的，殘響反而讓峰值**變小**（因為乾聲被乘了 1−mix）。
- **共同因子**：超標＝「引擎原聲不低」＋「後段總增益大」。
  - 7、15 跟 6、14、20 一樣，後段總增益都 ≥ +16 dB。差別在 6、14、20 的引擎原聲低了 2.4～11.7 dB。
  - 11 號的後段只有 +11.6 dB，但引擎原聲是 27 個裡最大的（−10.13）。
  - 換句話說：沒有任何一層是單獨的元兇。是「引擎在 CLI 校準過、但外掛後段沒有預算」這個結構，在這三個 preset 上剛好疊到最高。

## §4 Body 層細節

- **公式**（`BodyResonance::totalResponse`，用跟 `BiquadFilter.h` 一樣的 RBJ 係數重算）：在基頻上的放大量

  | Body | 0.2 | 0.35 | 0.45 | **0.5（預設）** | 0.6 | 0.7 | 0.75 | **0.8** | **0.85** | 1.0 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | 基頻 f1 | +6.5 | +9.6 | +11.2 | **+11.9** | +13.1 | +14.2 | +14.7 | **+15.2** | **+15.6** | +16.8 dB |
  | 第二泛音 f2 | −1.1 | +0.2 | +1.6 | +2.3 | +3.7 | +5.0 | +5.6 | +6.1 | +6.7 | +8.2 dB |

  原因：`configureCreativeBodyLayer()` 把兩個帶通濾波器的中心頻率設成**這顆音自己的** f1、f2，所以永遠正中紅心。
  這一層是「創作層」，不是物理（`BodyResonance.h` 開頭註解：procedural）。
- **實測對公式**：7 號（0.80）引擎總和峰值 +15.12 dB，公式 +15.16；6 號（0.75）+13.97，公式 +14.69。
  15 號（水鑼，0.85）只有 +4.97，因為鑼的能量分散在很多不和諧模態，基頻不是最大的那條；再加上下面的幾何連動。
- **兩個連動，已經量過、排除**：
  - Cimbalom 的 Body 也會把弦的 detune 乘上 (0.4＋1.2×Body)（`CimbalomEngine.h:210`）。
    把有效 detune 固定在 6 音分再比：Body 0 → −16.79、Body 0.8 → −1.66。差 +15.13 dB，跟不固定時的 +15.12 一樣。**detune 對峰值沒有影響。**
  - Chromatic 的 Body 也會把幾何尺寸乘上 (0.5＋Body)（`ChromaticEngine.h:173`），然後再調回 MIDI 音高。
    15 號在 Body 0 時把 size 從 40 改到 100 mm（有效 20→50 mm），引擎原聲從 −16.37 變 −18.12。
    所以 15 號的 +4.97 裡，大約 −1.7 dB 來自幾何，**Body 層本身大約 +6.7 dB**（約略值，因為 54 mm 和 50 mm 不完全一樣）。
- **Body 掃描**（引擎總和／最後輸出，dBFS）：

  | Body | 0 | 0.2 | 0.4 | 0.6 | preset 值 | 1.0 |
  |---|---|---|---|---|---|---|
  | 7 號 | −16.79／−7.97 | −10.49／−2.83 | −6.50／−1.26 | −3.76／−0.30 | (0.8) −1.67／**+0.33** | +0.01／+0.76 |
  | 15 號 | −16.37／−4.87 | −16.48／−4.17 | −14.77／−2.05 | −13.06／+0.23 | (0.85) −11.40／**+2.65** | −10.56／+3.85 |

- **校準時沒有 Body**：引擎常數是 2026-07 在 CLI 用 `--levels`（力度 0.85、MIDI 60）校準的（`reports/velocity_before_after.md:60-76`）。
  CLI 的 Body 預設是 0（`CimbalomEngine.h:612-620` 註解：「the body-resonance layer is OFF in this standalone / physics-verified path」）。
  外掛的 Body 是事後疊上去的，沒有對應的音量扣回。

## §5 殘響細節

| preset | 最大樣本（時間） | 乾聲部分 | 殘響 wet 部分 | wet 佔比 | wet RMS 比殘響輸入 |
|---|---|---|---|---|---|
| 7 | −1.0382（231 ms） | −0.0024 | −1.0359 | 99.8% | +5.82 dB |
| 11 | −1.1846（915 ms） | +0.0247 | −1.2094 | 102.1% | **+10.75 dB** |
| 15 | +1.3573（548 ms） | +0.0895 | +1.2678 | 93.4% | +9.27 dB |
| 9（參考） | −0.5710（542 ms） | −0.0374 | −0.5336 | 93.4% | +9.43 dB |
| 20（參考） | +0.5910（515 ms） | +0.0273 | +0.5636 | 95.4% | +7.91 dB |

- 為什麼會這樣：`SimpleReverb` 是 Freeverb 式結構。wet 等於 8 個 comb 加總再乘 0.15×mix（`SimpleReverb.h:155`）。
  room size 0.85～0.90 時，comb 的回授是 0.938～0.952（`SimpleReverb.h:81`）。持續很長的音（銅弦 5 根、鋼的 Custom Harmonics、青銅鑼）送進去，尾巴會一直疊上去。
  mix 只決定「乾、濕各佔多少」，並不保證總音量不變。
- **掃描**（其他參數照 preset，最後輸出峰值，dBFS）：
  - 15 號：mix 0.15 → −5.01、0.30 → −0.36、0.45（preset）→ +2.65；size 0 → −4.98、0.5 → −2.71、0.85（preset）→ +2.65。
  - 11 號：mix 0.15 → −5.99、0.30 → −2.79、0.55（preset）→ +1.47；size 0 → −4.71、0.5 → −1.98。
  - 7 號：mix 0.15 → −0.20、size 0.5 → −1.33。7 號主要是 Body，光調殘響壓不到 −1 dBFS 以下。
- 殘響 size 對響度的影響，D9／K1 已經在 IR 模式的對齊註解裡記錄過（`EffectChain.h:275-282`，「其他 size 差 −1.4～+4.0 dB」）。本卡量到的是 ALGO 路徑自己的 wet 累積，跟 IR 補償無關（三個 preset 都是 ALGO 模式）。

## §6 B6 慣例錨定的查證（為什麼排除）

- 整個 `src/` 在 HEAD 裡呼叫 `RadiationModel::` 的地方：
  - `ScoreRenderer.h:291-292、461、529、537-541`（全部在 `dumpModes()` 函式內，從 `:140` 開始）；
  - 以及兩處註解（`DiagnosticOverrides.h:50`、`CimbalomEngine.h:585`）。
  - 證據：命令 `git grep -n "RadiationModel::" HEAD -- src` 的輸出抄在本節下方，也附在 `wf1002_R_a_analysis.txt` 檔尾。
- 「純物理振幅擷取」旗標 `capturePhysicsOnlyModes` 只在 `dumpModes()` 用 RAII 打開、離開就還原（`ScoreRenderer.h:153-177`）。
  外掛的 `startNote()` 從來不讀它（TODO B6 條目：「`startNote()` 即時播放路徑完全未動」）。
- `kPascalsPerUnitPhysicsAmplitude = 1.0f` 只是把「數位 1.0」定義成「1 Pa」，用來寫進 dump 的 JSON。它不乘到任何音訊上。
- 結論：**B6 對外掛輸出峰值的貢獻是 0。** 裁決包原本的懷疑可以撤下。

```
$ git grep -n "RadiationModel::" HEAD -- src
src/dsp/DiagnosticOverrides.h:50:    // RadiationModel::pressurePerForce()).
src/engines/CimbalomEngine.h:585:        // RadiationModel::kPascalsPerUnitPhysicsAmplitude for what this
src/score/ScoreRenderer.h:261:            // RadiationModel::modalEnergyFirstPrinciples()/
src/score/ScoreRenderer.h:291:                    radiationFc = RadiationModel::criticalFrequency (sbDyn.D, sbDyn.rhoS);
src/score/ScoreRenderer.h:292:                    radiationFga = RadiationModel::acousticCutoffFrequency();
src/score/ScoreRenderer.h:450:                // see RadiationModel::radiationEfficiency(). Omitted entirely
src/score/ScoreRenderer.h:461:                    const float sigma = RadiationModel::radiationEfficiency (
src/score/ScoreRenderer.h:529:                        RadiationModel::pressurePerForce (physicsOnlyAmplitudes[i]);
src/score/ScoreRenderer.h:537-541:  (kMeasurementRadiusM / AzimuthDeg / ElevationDeg, JSON 欄位)
```

## §7 修法選項（並列，不替月月選）

先講三個共通事實：
1. Q05 已裁 C：外掛畫面加削波指示燈，**不改聲音**。這件事 C1 lane 在做，跟下面任何一案都可以並存。
2. 外掛的 Output 是效果器之後的純線性增益（`PluginProcessor.cpp:409-420`）。實測 15 號 Output 0.5 → −3.367 dBFS，計算值 −3.367，**完全一致**。
3. 載入工廠 preset 時會先把**所有**參數重設成預設值（`PresetManager.h:439`）。所以「改預設值」會影響全部 27 個 preset。

| 案 | 做法 | 會改哪些聲音（R10） | CLI 8/8 位元基準 | 要月月另外裁什麼 | 工作量 |
|---|---|---|---|---|---|
| **A1 只改 3 個 preset 的 Output** | 在 7、11、15 的 preset 表裡加 `macro_output` | **只有這 3 個 preset，而且只改音量、不改音色**（線性，精確）。要讓峰值 ≤ 0 dBFS：Output 0.963／0.844／0.737；≤ −1 dBFS：0.858／0.752／0.657（目標值只是描述，不是門檻） | 不變（CLI 不讀 preset） | 目標峰值要定多少（新數字，R4） | S |
| **A2 只改 3 個 preset 的音色參數** | 把 7 號 Body 調低；把 11、15 的殘響 mix 或 size 調低 | 只有這 3 個，**音色會變**。實測例：7 號 Body 0.6 → −0.30；15 號殘響 mix 0.30 → −0.36；11 號 size 0.5 → −1.98、mix 0.30 → −2.79 | 不變 | 換成哪個值（美術判斷） | S |
| **B1 拿掉壓縮器的自動補償** | `Compressor.h:51` 的 makeup 改成 0，或改成使用者看得到的參數 | **全部 27 個工廠 preset ＋所有使用者音色**，整體變小 2.0～7.5 dB。這是精確值，因為補償只是一個常數倍數。7／11／15 會變成 −4.67／−3.03／−1.85；27 個裡最大聲的變成 −1.85。完整清單在 `wf1002_R_a_analysis.txt` [5] | **不變**：CLI 的壓縮器預設關閉（`EffectsChain.h:22`，`compressorEnabled=false` → ratio 1 → 旁路），整個 `src/` 沒有任何地方把它打開（`git grep compressorEnabled` 只有 `EffectsChain.h:22、82` 兩行） | 同時也是改壓縮器的行為慣例 | S～M（改 1 行，外加 R10 前後對照與 HostProbe） |
| **B2 Body 層做響度正規化** | 把 Body 層輸出除以它在 f1 的放大量（例如 Body 0.8 時 −15.2 dB），讓 Body 只改音色、不改音量 | 6 個有開 Body 的 preset（6、7、14、15、25、26），加上**所有 Body>0 的使用者音色**（Body 預設就是 0.5）。新的峰值**本卡沒有實測**：正規化前有非線性的壓縮器，只能估。估計 7 號約 −12.7～−14.8 dBFS（+0.33 − 15.16，再加回壓縮器因此少壓的 0～2.1 dB） | 不變：CLI 的 Body 預設是 0，只有診斷旗標 `--body-amount` 會開 | 正規化公式是新的慣例常數（R4，DECIDED CONVENTION） | M |
| **B3 殘響 wet 的增益慣例** | 只在外掛的 `EffectChain.h` 對 ALGO 殘響的 wet 乘一個補償。做法比照 `kIrWetMakeupGain`，只動外掛這一側 | 所有殘響 mix>0 的 preset（27/27）加上所有使用者音色。殘響這一級現在是 −3.7～+14.0 dB，每個 preset 不同，改完會各自變 | **只在外掛側做就不變**。如果改的是共用的 `SimpleReverb.h`，CLI 82 份有 reverb 的樂譜會變，8/8 可能破 | 補償值和它的依據（新常數，R4） | M |
| **B4 把 Output 的預設值調低** | `ParameterLayout.cpp:53` 的預設 1.0 改成更小的值 | **全部 27 個工廠 preset ＋新建的實例**，同一個 dB 量。要讓 27 個全部 ≤ 0 dBFS，需要 ≤ 0.737（−2.65 dB）。已經存好狀態的 DAW 專案會帶自己的 Output 值，不受影響 | 不變 | 新的預設值（R4） | S |
| **C1 只做指示燈＋文件**（=Q05 已裁的 C） | 不改聲音 | 不改 | 不變 | — | （C1 lane 進行中） |
| C2 輸出限幅（=Q05 的 B，10-02 未採用） | soft clip／limiter | 超過的那一段會被改 | 不變 | 限幅門檻（R4） | M |

附註：
- 多弦同相起振（`1/√N` 正規化只在能量上成立，峰值仍跟著 √N 長）是**次要因素**（7 號 5 弦比 3 弦多 +2.2 dB）。
  CLI 的 `noteOn()` 用的是同一個公式（`CimbalomEngine.h:547`），改它會動到 CLI 的 8/8。**本卡不列為修法選項，只記錄事實。**
- A1、A2 只是治標，Body 預設 0.5 和殘響累積這兩個結構問題還在（使用者自己調的音色照樣會超）。
  B1～B4 是改「出廠輸出增益慣例」，影響面大，但能一次處理。
  這兩類可以一起用，**選哪個是月月的裁決**。

## §8 限制與沒做的事

- 只量了 C4、力度 0.7、48 kHz、block 512（跟 E16 同條件）。其他音高、力度、取樣率的峰值沒有量。
- B2、B3 的「改完之後的峰值」只有估計或範圍，沒有實際做 patch 量（沒有在隔離副本改 src，因為選項還沒裁）。
- 殘響的 wet 增益只量了這幾個 preset 的設定（size／mix 掃描），沒有推一般公式。
- 沒有評估各 preset 的音色好不好聽，也沒有評估改完後聽感會怎樣變（R10 對照報告要等裁決後做）。
- 15 號 Body 層「純本身」的 +6.7 dB 是約略值（幾何 54 mm 對 50 mm 不完全對等）。

## 證據檔

| 檔案 | 內容 |
|---|---|
| `reports/gate_outputs/wf1002_R_a_setup.txt` | binary 複本 sha256、研究小程式的建置與隔離方式、junction 拆除、刪除意外紀錄 |
| `reports/gate_outputs/wf1002_R_a_hostprobe_e16_rerun.txt` | HostProbe 重跑完整 log，E16 跟 K2 逐字相同 |
| `reports/gate_outputs/wf1002_R_a_taps_raw.txt` | 168 次渲染的條件檔和原始輸出 |
| `reports/gate_outputs/wf1002_R_a_analysis.txt` | 分析輸出（逐級表、wet/dry 拆解、Body 公式、掃描、修法算術）、分析腳本與小程式原始碼 |
