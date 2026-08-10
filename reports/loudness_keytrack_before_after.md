# 跨音域響度失衡修正 — Rule 10 前後對照報告

> 日期：2026-08-06　分支：`fix/deep-physics-audit-20260716`（unstaged，待月月審）
> 起因：月月審聽反映「高音變小聲、低音變大聲」（同一問題已見 `phase_h_before_after.md` §3
> 與 `TODO.md` 2026-08-06 Rule 10 條目；本輪為**激發端物理修正**線，與既有的
> 亮度 EQ 短期線、阻尼寬頻化長期線並行互補）。

## 1. 這一頁是什麼？（白話）

改動前，同力度從低音彈到高音，音量會一路掉 27~36 dB——低音大到削波、最高音
幾乎聽不見。本輪加了兩層修正，把差距收斂到約 8~9 dB（保留一點「高音本來就
比較短小」的真實樂器個性）。改的是每個音觸發那一刻算好的固定增益，**不是**
compressor / AGC 之類跟著訊號跑的東西——同一份 score 渲染兩次仍然位元相同。

## 2. 根因（三個機制疊加）

1. **槌頭接觸時間 τc 全鍵盤共用一個值**（主因）。力脈衝頻譜 H(ω) 是低通形狀：
   Felt 2ms 下 C7 基頻約 -37 dB，等於高音區永遠被軟槌悶住。真實鋼琴的槌頭是
   隨音域變輕變硬的（Askenfelt & Jansson 量測：低音 ~4ms → 最高音 <1ms，
   `HammerImpulse.h` 檔頭本來就引了這筆文獻，但舊實作沒有用上音高維度）。
2. **模態數量隨音高遞減、無能量正規化**。等權重 velocity convention 下低音
   一個音疊 40 個 mode、高音只剩個位數，疊加能量差好幾個 dB。
3. **高頻衰減快**（β_air·f² 項），RMS-over-duration 進一步塌陷——這部分是
   真實物理，刻意只做部分補償保留。

## 3. 改動內容

| 層 | 檔案 | 內容 | 定位 |
|---|---|---|---|
| A. τc keytrack | `src/physics/HammerImpulse.h` `keytrackScale()`/`tauCForNote()` | τc ∝ f^(-0.32)（A0 4ms → C8 0.8ms 擬合 Askenfelt & Jansson），錨 A4=1.0，clamp [0.4, 2.6]；四個引擎呼叫點（Cimbalom/Chromatic × startNote/noteOn）全部改用 `tauCForNote()` | **物理修正**（有文獻依據，屬 M2 2a 槌頭模型的音高維度補完） |
| B. noteOn 能量正規化 | `src/dsp/ModalResonator.h` `modeAttackEnergy()`/`loudnessCompensationGain()`；`CimbalomEngine.h`/`ChromaticEngine.h` 接入 | 觸發時算 300ms 攻擊窗模態能量 e（解析式，含槌頭頻譜、不含 velocity 與 1/√N；**槌頭頻譜一律用 velocity=0.5 Hertz 錨的 τc 預估**，見 §7 velocity 律教訓），乘 (ref/e)^(amount/2)，clamp ±12 dB；錨點 ref = A4 預設參數引擎內實測（`kCimbalomAttackEnergyRefA4 = 0.1609`、`kChromaticAttackEnergyRefA4 = {0.009852, 0.1182}`） | **已文件化校準層**（非物理主張，比照 spectralTilt 劃界；Custom Harmonics / FM 不套用） |

amount 定案 **0.78**（月月 2026-08-06 審聽裁決：0.7「高音偏低一點點」→ 試 0.85 → 定 0.78）。

## 4. 量測（C2~C7 半八度掃音、velocity 0.8、normalize=false、效果全關）

RMS spread = 掃音中最大與最小 RMS 之差；理想值不是 0（真實樂器高音本來稍弱），
目標是從「壞掉」收斂到「有個性」。

| 引擎 | 改前 spread | keytrack only | +正規化 0.78（定案） |
|---|---|---|---|
| Cimbalom (steel) | **27.28 dB**（C2 peak 0 dBFS 削波） | 20.58 dB | **8.35 dB**（C2 peak -9.4） |
| Tongue Drum (aluminum) | **29.67 dB** | — | **8.13 dB** |
| Water Gong (bronze) | **36.30 dB** | — | **8.35 dB** |

定案版逐音（Cimbalom，RMS / peak dBFS）：
C2 -28.1/-9.4，C3 -29.3/-11.2，C4 -30.1/-13.0，C5 -31.5/-14.5，C6 -33.7/-15.2，C7 -36.5/-15.4
——C5~C7 攻擊 peak 已持平（-14.5~-15.4），殘餘 RMS 斜率主要來自高音自然短衰減。

改前對照（同 Cimbalom）：C2 -22.6/0.0（削波），C7 -49.8/-29.2。

## 5. 不變量／相容性

- **決定性**：補償是 noteOn 時的純函數 scalar（僅依 mode 表、材質、槌硬度、
  velocity 經 τc 的既有 Hertz 項），無狀態、無隨機；determinism SHA256 契約不受影響。
- **模態相對振幅不變**：整組 mode 乘同一 scalar，`--amps`（±3 dB 相對判定）與
  `--dump-modes` 的 relative_modal_amplitude 語意照舊；amp 欄位如既有慣例反映
  最終渲染值（同 spectralTilt / hammer spectrum 的處理方式）。
- **velocity 律**：`excite()` 的線性 velocity 路徑未動；τc 的 velocity 相依
  （Hertz ±20% clamp）是既有行為，本輪只是把它也走進能量預估。
- **T60 / f0**：decayTime 與 frequency 完全未動。
- **絕對電平會變**（本報告的目的）：所有 modal 引擎的既有 score 渲染 SHA256 會變、
  各音域相對音量會變。**corpus 73 檔需重驗**（rest RMS 與 peak 邊際受絕對電平影響，
  特別是 summer_m2/m3 的 2.5~2.6 dB 邊際檔）。
- FM Piano / Custom Harmonics：位元不變（域外未動）。

## 6. GATE 現況

- C++ repro：ctest 3/3 PASS
- Python：pytest 121/121 PASS
- `physics_verify.py --full`：**PASS**（見 §7 的一次誠實 FAIL 與修正）
- corpus 73 檔重驗：四分片執行中，結果補記於 §7
- 建置：CLI / Standalone / VST3 Release 全部 exit 0

## 7. GATE 補記：velocity 律誠實 FAIL 與修正（同日）

第一版能量預估把**實際 τc(velocity)**（含 Hertz ±20% 項）算進補償增益，
`--full` 的 F3 velocity 判定立刻抓到：tongue_drum 基頻帶 delta **+4.72 dB**，
違反 +6.0206±1.0 dB 物理律（其餘引擎 +5.7 擦邊過）。機制：velocity ↑ → τc ↓ →
攻擊能量預估 ↑ → 補償增益 ↓，把 `excite()` 的線性 velocity 律拉成次線性。

**修正**（未動任何容差，Rule 2）：能量預估一律改用 velocity=0.5（Hertz 錨，
hertzScale=1）的 τc——補償只管跨音域平衡，力度響應交還給既有線性路徑；實際
渲染振幅仍用實際 τc（物理不變）。錨點常數隨新預估式重量（引擎內實測，
velocity 無關）。修正後 `--full` 全綠：velocity 五引擎 +6.1（piano +7.0，
既有 Hertz 增亮效應，round-3 已追認的量測域內）、`RESULT: NO CHECKED FAILURES`
（3 個 rubber UNVERIFIED 為既有已知 N/A）。log：`full_gate2.log`（scratchpad）＋
本目錄 `gate_outputs/loudnessfix_corpus_{A..D}.txt`（corpus 四分片）。

corpus 四分片結果（2026-08-06 深夜，本機四片平行）：**73/73 全 PASS、0 FAIL、
零新增豁免**（A 19/19 + B 18/18 + C 18/18 + D 18/18；僅既有 moonlight FX 藝術
豁免 1 筆保持可見）。邊際檔逐一確認：`summer_m2`（A 片）與 `summer_m3`（B 片）
rest RMS 皆 PASS——低音整體變小聲反而擴大了它們的殘響尾巴邊際。determinism
雙渲染 SHA256 檢查全數通過（含 moonlight 長曲，無 deepfix2/4 輪的併發環境故障
重演）。存證：本目錄 `gate_outputs/loudnessfix_corpus_{A..D}.txt`。
