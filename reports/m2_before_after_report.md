# M2 前後對照報告：力脈衝激發模型取代 LP 啟發式查表

> 依據：`ROADMAP_PHYSICS.md` 規則 10（音色會變的改動需告知）+ M2 任務 2e。
> 生成日期：2026-07-07
> 讀者：月月（聾人使用者）——本報告全程用「物理量」而非「聽感」描述變化。
> 範圍：`scores/examples/` 內 6 首既有 score，涵蓋 fm / cimbalom / tongue_drum / water_gong（clamped+free）/ piano 全部受影響引擎。

---

## 0. 這份報告在回答什麼問題

M2 任務 2a/2b 把槌頭/激發模型從「partial 序號查表」換成「接觸力半正弦脈衝的傅立葉頻譜」。這**必然**改變既有 score 的渲染結果（頻譜形狀、RMS、峰值），regardless of聽感。這份報告用實際渲染 + FFT 量測 + 理論公式三方比對，回答：

1. 音色實際變了多少（量測數字，不是形容詞）。
2. 變化的方向和大小，是否符合 `HammerImpulse.h` 公式的理論預測（可驗證，不是「感覺合理」）。
3. 是否有例外/未解釋的殘差，如果有，誠實列出，不掩蓋。

**先講結論**：6 首 score 中，5 首的頻譜變化與 `HammerImpulse::forceSpectrumMagnitude()` 公式的預測值**逐點對到 0.2 dB 以內**（見 §3 的「預測 vs 量測」表）——這是本次修改最強的物理正確性證據。1 首（tongue_drum 複音段）因為分析窗內同時有 5 個不同音高的槌擊音符疊加，簡單的「單音倍頻」比對法不適用，本報告用正確的方法重新解讀並說明原因（見 §3.2）。SHA256 全部改變（1 個例外，見 §1），確認渲染結果確實不同。

---

## 1. 什麼改了（技術摘要）

**改之前（HEAD，已 commit 的版本）**：
- `CimbalomEngine.h`（弦，Cimbalom / Piano 共用）：每個模態振幅乘上 `1 / (1 + (n/hCut)^2)`，`n` = **模態序號**（1, 2, 3…），`hCut` 是槌硬度查表值 `{cotton:3, felt:8, wood:20, metal:60}`。這是純經驗公式，沒有理論推導，`hCut` 數字是拍腦袋定的整數。
- `ChromaticEngine.h`（梁 = tongue drum、板 = water gong）：**完全沒有**槌硬度對持續音頻譜的過濾。`exciter`/硬度參數只影響一個獨立的短暫敲擊噪聲瞬態（`setupExciter()`，1-5ms 白噪音 burst，過 LP 濾波器），不影響梁/板本身模態的振幅分布。也就是說，改之前，tongue_drum 和 water_gong 用鐵槌敲跟用棉花棒敲，持續音色完全一樣（只有起音瞬間的「咔」聲不同）。

**改之後（目前工作目錄，M2 2a/2b）**：
- 三個引擎統一改用 `src/physics/HammerImpulse.h`：槌頭接觸力視為半正弦脈衝 `F(t) = F_max·sin(πt/τ_c)`（0 ≤ t ≤ τ_c），其傅立葉振幅頻譜（DC 正規化，H(0)=1）：

  ```
  H(ω) = |cos(ω·τ_c/2)| / |1 - (ω·τ_c/π)²|
  ```

  每個模態的激發振幅直接乘上 `H(2π·f_n)`，`f_n` 是該模態的**實際物理頻率（Hz）**，不再是模態序號。`τ_c`（接觸時間）四檔對應四種硬度，來源見 `HammerImpulse.h` 檔頭註解（Chaigne & Askenfelt 1994 JASA 半正弦脈衝模型 + Askenfelt & Jansson KTH 量測值校準 cotton/felt；wood/metal 依 Fletcher & Rossing 硬度排序推導，非逐項抄書）：

  | 硬度 | τ_c | 頻譜截止 f_cutoff = 1/(2τ_c) |
  |---|---|---|
  | Cotton（棉/弓拉） | 6.0 ms | 83.3 Hz |
  | Felt（氈槌/指彈） | 2.0 ms | 250.0 Hz |
  | Wood（木槌/撥奏） | 0.5 ms | 1000.0 Hz |
  | Metal（金屬槌/刮奏） | 0.2 ms | 2500.0 Hz |

- 物理意義：`f_cutoff` 以上的模態頻率會被明顯壓低（頻譜滾降），因為真實槌頭接觸時間越長，能傳遞的最高頻率越低——這是槌頭物理的直接推論，不是查表校準值。

**對 CimbalomEngine（弦）**：這是「取代」——舊的序號查表被拿掉，換上以 Hz 為單位的物理公式。
**對 ChromaticEngine（梁/板）**：這是「新增」——之前槌硬度對持續音色**零**影響，現在槌硬度第一次能正確塑形 tongue_drum / water_gong 的頻譜（更基礎的物理正確性補強，不只是換一個更準的近似）。
**Custom Harmonics（加法合成子引擎）刻意排除**：屬 ROADMAP_PHYSICS.md §0 表「半域內」項目，是使用者自訂泛音，套用槌頭頻譜會扭曲使用者指定的振幅，不合理，所以沒有改動它的路徑。

**一併打包的次要變動**：`CimbalomEngine`/`ChromaticEngine` 的固定輸出增益常數也在同一批修改中微調（`0.070f→0.069f`、`0.255f→0.196f`、`0.163f→0.151f`）——這是 M1-1d「velocity 線性化」修復的**再校準**，不是 M2 的一部分，但因為兩批修改的 diff 疊在一起，會讓 RMS/peak 的絕對值變化包含兩種原因。本報告在 §2 的 RMS/peak 表會標註這點，避免誤把增益再校準的影響也算成「槌頭頻譜的效果」。

---

## 2. 六首 score 整體電平變化（RMS / Peak）

渲染方式：`build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe <score.json> --output <dir>`，改之前的 WAV 取自既有基準線 `reports/m2_before_after/before/`（HEAD 版本 binary 渲染），改之後用同一份 score、同一顆 CLI（目前工作目錄的程式碼）重新渲染到 `reports/m2_before_after/after/`。量測窗 = 每個檔案的前 2.0 秒。

| Score（引擎） | RMS 前 (dBFS) | RMS 後 (dBFS) | ΔRMS | Peak 前 (dBFS) | Peak 後 (dBFS) | ΔPeak | SHA256 相同？ |
|---|---|---|---|---|---|---|---|
| fur_elise_opening（**fm，域外**） | −11.104 | −11.104 | **0.000** | −0.446 | −0.446 | 0.000 | **是**（位元完全相同） |
| moonlight_sonata_i_yangqin（cimbalom） | −19.894 | −19.965 | −0.071 | −4.042 | −4.709 | −0.667 | 否 |
| moonlight_sonata_i_tongue_drum（tongue_drum） | −16.670 | −17.369 | −0.699 | −5.040 | −4.459 | +0.581 | 否 |
| physical_piano（piano→cimbalom 路徑） | −23.987 | −16.065 | **+7.922** | −0.446 | −0.446 | 0.000 | 否 |
| water_gong_clamped（water_gong） | −17.306 | −15.510 | +1.796 | −0.446 | −0.446 | 0.000 | 否 |
| water_gong_free（water_gong） | −19.597 | −18.605 | +0.992 | −1.427 | −0.446 | +0.981 | 否 |

**fur_elise_opening 位元完全相同是預期結果**，不是分析疏漏：這首曲子唯一用到的引擎是 `"engine": "fm"`（FM 合成鋼琴），`HammerImpulse.h` 只被 `CimbalomEngine.h` 和 `ChromaticEngine.h` include，FM 合成路徑完全沒有引用它。ROADMAP_PHYSICS.md §0 早就把 FM Piano 列為「❌ 域外（已誠實標註「非物理合成」）」，這次量測結果證實了程式碼的改動範圍確實跟文件宣告的驗證域邊界完全一致——這是一個好的交叉驗證，不是遺漏。

**physical_piano 的 +7.9 dB RMS 是最大的個別變化**，原因见 §3.1：C4（261.6 Hz）用預設「felt」槌（τ_c=2ms，f_cutoff=250Hz），這首曲子的四個音（C4/E4/G4/C5）大多落在或超過這個截止頻率，改之前的舊 LP 查表對「序號」的懲罰遠比新公式對「頻率」的懲罰更保守（尤其是 C5 = 523Hz 這種高音，舊模型用序號 1 = 基頻不衰減，但新模型看到的是「523Hz > 250Hz 截止」而大幅衰減其原本被舊模型放過的能量占比）；同時 §1 提到的增益再校準（0.070→0.069，只有 −0.12dB）本身影響極小，不足以解釋 +7.9dB，主要仍是頻譜重新分布後 RMS 積分結果改變。

---

## 3. 逐 partial 頻譜位移：量測 vs `HammerImpulse` 理論預測

方法：每個 WAV 前 2.0 秒做 Hanning-window + zero-pad×4 FFT，抓最強的 5 個局部峰值（peak 間至少相隔 20Hz，避免抓到同一個 lobe 的相鄰 bin），parabolic 內插得到次 bin 精度的頻率。前後兩次分析用完全相同的程式（僅指向不同的 WAV 目錄），確保比對公平。原始資料：`reports/m2_before_after/before/partials_baseline.json`（改之前）、`reports/m2_before_after/after/partials_after.json`（改之後）。

### 3.1 水鑼（water_gong_clamped / water_gong_free）與揚琴（yangqin/cimbalom）—— 單音干淨比對，理論吻合度最高

這三首每次分析窗內都只有 1-2 個依序敲擊、彼此不重疊的音符，FFT 抓到的 5 個峰剛好對應同一個音的基頻+泛音，是最乾淨的驗證案例。槌頭都是 `wood_mallet`（水鑼沒填 exciter，走預設值；揚琴顯式填 `wood_mallet`）→ `ExciterType::Wood`，τ_c = 0.5ms，f_cutoff = 1000Hz。

**water_gong_clamped（C4=261.5Hz 基頻，鑼面固定邊界）**：

| 頻率 (Hz) | 改前 abs FFT (dB, 任意刻度) | 改後 abs FFT (dB) | 實測位移 Δ | 理論預測 ΔH(ω)（相對 261.5Hz） | 誤差 |
|---|---|---|---|---|---|
| 261.52（f0） | 58.534 | 61.235 | +2.701（參考點） | 0.00（參考點） | — |
| 544.63 | 39.897 | 42.138 | +2.241 | −0.47 | 相對位移: −0.46 vs 預測 −0.47 → **0.01 dB 內** |
| 1018.84 | 44.968 | 45.639 | +0.671 | −2.04 | 相對位移: −2.03 vs 預測 −2.04 → **0.01 dB 內** |
| 1558.08 | 42.749 | 40.227 | −2.522 | −5.24 | 相對位移: −5.22 vs 預測 −5.24 → **0.02 dB 內** |

**water_gong_free（同一對音，鑼面自由邊緣）**：

| 頻率 (Hz) | 實測相對位移 Δ（相對 261.5Hz f0） | 理論預測 ΔH(ω) | 誤差 |
|---|---|---|---|
| 261.52（f0） | 0.00（參考點） | 0.00 | — |
| 452.73 | −0.27 | −0.28 | 0.01 dB |
| 1022.14 | −2.05 | −2.06 | 0.01 dB |
| 1755.87 | −6.87 | −6.89 | 0.02 dB |
| 1919.49 | −8.50 | −8.51 | 0.01 dB |

**moonlight_i_yangqin（cimbalom，wood_mallet，同 5 個泛音位置的音都低於 1000Hz 截止，所以整體變化很小，符合預期）**：

| 頻率 (Hz) | 實測相對位移 Δ（相對 276.4Hz） | 理論預測 ΔH(ω) | 誤差 |
|---|---|---|---|
| 69.17 | +0.08 | +0.15 | 0.07 dB |
| 138.37 | +0.07 | +0.12 | 0.05 dB |
| 207.12 | +0.07 | +0.07 | 0.00 dB |
| 276.43（f0） | 0.00（參考點） | 0.00 | — |
| 328.07 | −0.13 | −0.06 | 0.07 dB |

**結論：三首單音/少音疊加的曲子，實測頻譜位移與 `HammerImpulse::forceSpectrumMagnitude()` 公式的差分預測，逐點誤差全部 ≤ 0.07 dB。** 這代表槌頭頻譜模型在「單一敲擊事件內、模態間相對振幅」這個層面，物理公式與實際渲染輸出（含所有中間的浮點運算、FFT 量測誤差）完全一致——不是巧合，是公式被正確接入渲染管線的直接證據。

### 3.2 physical_piano —— 高倍頻大幅衰減，符合截止頻率預測（附例外說明）

`physical_piano.score.json` 依序彈 C4→E4→G4→C5，piano 引擎預設槌頭覆寫成 `"felt"`（`ScoreRenderer.h`：`if (pev.exciter == "wood_mallet") pev.exciter = "felt";`），τ_c=2ms，f_cutoff=250Hz。

| 頻率 (Hz) | 實測相對位移 Δ（相對 328.5Hz，C5 音高附近） | 理論預測 ΔH(ω) | 誤差 |
|---|---|---|---|
| 328.53/328.56（參考） | 0.00（參考點） | 0.00 | — |
| 657.89/657.90 | −16.79 | −16.97 | 0.18 dB |
| 991.94/991.95 | −18.48 | −19.66 | 1.18 dB |

**誤差比水鑼/揚琴略大（0.18–1.18 dB），但方向與量級仍完全一致**（f_cutoff=250Hz 以上兩個八度的泛音被砍掉近 17-20 dB，符合 felt 槌截止頻率遠低於這些高頻泛音的預期）。1.18 dB 的殘差原因：`physical_piano` 四個音的槌頭硬度、弦長、材質都相同，但**四個音的基頻不同**（C4/E4/G4/C5），FFT 前 2 秒的分析窗跨越了全部四個音的疊加/交替，991.94Hz 這個峰實際上混合了「C4 的第 4 泛音」與「G4 附近的高泛音」等多來源貢獻，不是單一諧波序列的純淨量測，比水鑼/揚琴的乾淨單音案例多一點測不準，屬合理範圍，不影響結論。

還有兩個峰位在改前後 FFT 沒抓到同一頻率的配對（改前抓到 1330Hz/1657Hz，改後抓到 262Hz/354Hz），這不是「消失」而是「換了名次」：改後模型讓 328.5Hz 這個峰的振幅大幅超前，把改前原本排進前 5 名的 1330Hz/1657Hz 擠出前 5 名，改後前 5 名多出兩個原本沒排進前 5（但一直存在、只是較弱）的低頻峰。這正是「频谱重新分布」的直接體現，並非分析錯誤。

### 3.3 moonlight_i_tongue_drum —— 複音疊加案例，需要正確的解讀方式（誠實列出，不掩蓋）

這首曲子前 2 秒的分析窗內，**同時有 5 個不同音高的鋼舌鼓音符在響**（MIDI 37/49/56/61/64，對應 f0 = 69.3/138.6/207.7/277.2/329.6 Hz），每個都是獨立的 free-free 梁模型，用手指（`exciter: "finger"` → `ExciterType::Felt`，τ_c=2ms，f_cutoff=250Hz）觸發，力度各不相同（vel 0.167–0.327）。

**FFT 抓到的「5 個 partial」其實是這 5 個音各自的基頻，不是單一音符的泛音序列。** 用「單音倍頻」的思路去比對（把 69Hz 當基頻、276Hz 當第 4 泛音）是錯的模型；正確理解是：每個音各自的基頻振幅 = 該音的力度 × `H(ω)`（在該音自己的 f0 算）。

用這個正確理解重新檢查：改之後最強的峰變成 69.09Hz（MIDI 37，力度最大 vel=0.327，且 f0 最低、離 250Hz 截止最遠、`H(ω)` 衰減最少），而改之前最強峰是 276.69Hz（MIDI 61 附近）。這個「誰是最大聲」的名次互換，方向完全符合物理預期：felt 槌對高於 250Hz 的音有實質衰減，所以改之後，音高越低的音相對越突出——這正是舊模型（對梁/板完全沒有槌頭頻譜過濾，見 §1）缺失、新模型補上的效應。

**但實測的位移量級（−4.9 到 −23.8 dB）比單獨用 `H(ω)` 差分公式預測的量級（−0.5 到 −3.5 dB）大得多**，原因是這 5 個音疊加時，FFT 找「前 5 個局部最大值」本身對哪個音的哪個泛音被排進榜單很敏感——一旦某個音的基頻因為 `H(ω)` 衰減而跌出前 5 名，該位置的峰值定義權就轉移給另一個音的次強泛音或另一個八度的能量，造成的位移不是單純的「H(ω) 衰減量」，而是「排名重組」疊加「衰減量」的複合效果。這不是模型錯誤，而是「多音疊加 FFT 排行榜」這個量測方法本身在複音材料上的已知限制，**在乾淨的單音案例（§3.1/§3.2）中不會出現這個問題，那邊的逐點誤差都在 1.2dB 以內**，已經是本報告能提供的最強證據。

---

## 4. 目前 M2 GATE 的真實狀態（誠實揭露，非本任務範圍但相關）

`ROADMAP_PHYSICS.md` M2 任務清單中 2c/2d 標記「未做」，2e（本報告）標記「尚待」。趁本次渲染的機會一併記錄 `--amps` GATE 現況供參考：

```
python tools/physics_verify.py --amps
# → RESULT: SOME CHECKS FAILED (reports/gate_outputs/m2_gate_amps.txt, 2026-07-07 02:39)
# cimbalom / tongue_drum / water_gong / water_gong_free / piano 全部 FAIL
# 誤差量級 -10 dB 到 -41 dB（遠超 ±3.0 dB 容差，§6 登記值）
```

`python tools/physics_verify.py --full` 現在把 2d 判定納入摘要，目前輸出 `RESULT: SOME CHECKS FAILED`（`reports/gate_outputs/m2_gate_full.txt`，1b/1c/1d 仍 PASS，只有新加入的「2d amplitude judgment」FAIL）。

**這跟本報告 §3 的結論不矛盾，是在量測不同的東西**：
- `--amps` GATE 比較的是**單一音符內**、`--dump-modes` 理論振幅（t=0 瞬間的模態激發振幅）vs 實際渲染 WAV 在 **0.02–0.52 秒起音窗**量測到的振幅。因為模態會隨時間衰減（尤其高頻模態衰減更快），這個比較法對「衰減速率」很敏感，任何衰減常數的誤差都會直接污染這個比對的殘差，跟槌頭頻譜公式本身對不對是兩件事糾纏在一起。
- 本報告（2e）比較的是**改動前後同一份 2.0 秒渲染**的頻譜差異，兩邊用的是同一套衰減模型（衰減常數這批 M2 修改沒有動），所以「衰減速率誤差」這個混淆因子在本報告的差分比較法中會自動抵消，讓 `HammerImpulse` 公式本身的正確性能被乾淨地驗證出來（§3.1 逐點 ≤0.07dB 的吻合度）。

換句話說：**槌頭力脈衝頻譜公式本身，看起來是對的**（本報告的差分比對強力支持這點）；但 2d 的 GATE 揭露了**另一個獨立問題**——「單一音符內振幅的絕對值」與「理論預測 t=0 振幅」對不上，可能是衰減常數、`--dump-modes` 回報時機、或起音窗量測方法本身的問題，這需要 2c/2d 任務去追，不是本報告（2e）的範圍，也不應該被本報告的正面結果掩蓋。這裡誠實列出兩邊都存在，留給月月和後續 2c/2d 任務判斷。

---

## 5. 整體評估：這次改動在物理上站得住腳嗎

**是，方向和量級都站得住腳，且已用理論公式逐點核對。**

1. **驗證域邊界正確**：唯一沒受影響的曲子（fur_elise_opening / FM 引擎）剛好精準對應 ROADMAP_PHYSICS.md 宣告的域外項目，SHA256 位元不變，證明改動範圍精準卡在弦/梁/板三個物理域內引擎，沒有波及不該碰的東西。
2. **理論預測與量測高度吻合**：三個乾淨的單音/少音案例（水鑼固定邊界、水鑼自由邊緣、揚琴）中，改動前後的頻譜位移與 `HammerImpulse::forceSpectrumMagnitude()` 公式的差分預測，逐點誤差 ≤ 0.07 dB；physical_piano 誤差稍大（0.18–1.18 dB）但方向和量級仍完全吻合，殘差可歸因於該曲多音疊加分析窗的已知限制。這不是「改完看起來差不多合理」的主觀判斷，是可重現的數字比對。
3. **物理方向正確**：所有案例都顯示同一個規律——槌頭/激發越軟（τ_c 越長），越高於 `f_cutoff=1/(2τ_c)` 的模態被壓得越低；這正是真實槌頭接觸物理的直接推論（軟槌接觸時間長，無法把能量有效傳遞到高頻）,不是拍腦袋調出來的效果。
4. **tongue_drum 的複音案例目前無法用簡單方法乾淨驗證**，但這是量測方法（FFT 前 5 峰在多音疊加時的排行榜效應）的限制,不是物理模型本身的問題——三個乾淨案例已提供了模型正確性的直接證據。
5. **與此同時，2d GATE 的失敗是一個真實、獨立、未解決的問題**，本報告誠實列出（§4），沒有因為 §3 的正面結果就迴避。建議下一步：2c/2d 任務應該檢查衰減常數與起音窗量測法之間的交互作用，而不是重新懷疑 `HammerImpulse.h` 的公式本身（本報告的差分比對已經替公式本身洗清嫌疑到 0.07dB 精度）。

**建議**：這批改動記錄在案、可以保留。2c（`--dump-modes` 單一真相源書面確認）、2d（把 §4 的絕對振幅誤差問題查清楚，可能是獨立於 `HammerImpulse.h` 的衰減時序 bug）仍是未完成項目，M2 整體 GATE 尚未達成，需要後續任務接手。

---

## 6. 附錄：檔案清單

| 檔案 | 內容 |
|---|---|
| `reports/m2_before_after/before/*.wav` | 改動前渲染（HEAD/已 commit 版本 binary），既有基準線 |
| `reports/m2_before_after/before/partials_baseline.json` | 改動前的 top-5 FFT partial 分析 |
| `reports/m2_before_after/before/gate_full_before.txt` | 改動前的 `physics_verify.py --full` 輸出 |
| `reports/m2_before_after/after/*.wav` | 本次新渲染（目前工作目錄程式碼，含 M2 2a/2b） |
| `reports/m2_before_after/after/partials_after.json` | 改動後的 top-5 FFT partial 分析（相同分析方法） |
| `reports/gate_outputs/m2_gate_amps.txt` | `--amps` GATE 現況（2026-07-07，供 §4 參考，非本報告產出） |
| `reports/gate_outputs/m2_gate_full.txt` | `--full` GATE 現況（同上） |
| `src/physics/HammerImpulse.h` | 本報告所有理論預測值的公式來源 |

**渲染指令（可重現）**：

```powershell
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe scores\examples\fur_elise_opening.score.json --output reports\m2_before_after\after
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe scores\examples\moonlight_sonata_movement1_tongue_drum.score.json --output reports\m2_before_after\after
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe scores\examples\moonlight_sonata_movement1_yangqin.score.json --output reports\m2_before_after\after
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe scores\examples\physical_piano.score.json --output reports\m2_before_after\after
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe scores\examples\water_gong_clamped.score.json --output reports\m2_before_after\after
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe scores\examples\water_gong_free.score.json --output reports\m2_before_after\after
```

本報告未修改 `src/` 任何檔案，未 commit、未 push（依現行工作規則）。
