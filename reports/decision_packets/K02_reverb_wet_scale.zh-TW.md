# K-02 裁決包：ALGO 與 IR reverb wet 增益差（只量化，不修）

> 工作卡：`docs/workcards/WF0907_E7_reverb_k02_k03.md`（C++ lane，執行 Sonnet）
> 日期：2026-09-08
> 工作樹 branch `fix/deep-physics-audit-20260716`，HEAD `98f346f`（本卡未 commit）
> 數字來自 `TsukiSynthAuditTest.exe`（`reportReverbWetGainQuantification()`，`tests/audit_repro.cpp`）
> 完整命令與原始輸出見 `reports/gate_outputs/wf0907_E7_reverb.txt` §2
> **本卡不改 `0.15`、不改 convolution 參數、不改 reverb 演算法** —— 只量測、只寫此裁決包。

---

## §0 一句話結論

ALGO 路徑的 wet 輸出比 IR 路徑**多乘一次 `0.15`**（`SimpleReverb.h:155-156`），IR 路徑
（`EffectChain.h` 的 convolution 分支，wet/dry 混合見 `EffectChain.h:225-230`）**沒有**這個因子。
若只看這一個因子，理論差是 `20·log10(1/0.15) = 16.478 dB`（IR 應該比 ALGO 大約 16.5 dB 更大聲）。
**但實測到的整體差是 IR 比 ALGO 小 28.483 dB**——方向相反、量級也不同，代表 0.15 因子不是
唯一、甚至不是本次量測中的主導變因（見 §2 說明）。**不替月月選**；三個選項與各自的 Rule 10
衝擊列在 §3。

---

## §1 現況（file:line）

- `src/effects/SimpleReverb.h:155-156`：
  ```cpp
  left  = inL * dry + outL * mix * 0.15f;
  right = inR * dry + outR * mix * 0.15f;
  ```
  ALGO（Freeverb 式 comb+allpass）路徑的 wet 分量固定多乘 `0.15`。這個常數沒有物理溯源
  （不是任何量測或文獻反推值，純粹是舊版整體響度的手動配平），R4 只要求不新增這類常數、
  不要求追溯既有的。

- `src/effects/EffectChain.h:211-230`（IR 分支，convolution.process 後的 wet/dry 混合）：
  ```cpp
  convolution.process (ctx);
  ...
  chL[i] = dryL[i] * (1.0f - m) + chL[i] * m;
  ```
  没有任何額外係數乘 convolution 的輸出——`m`（reverbMix）之外沒有第二個縮放。

## §2 實測數字

命令：`build-wf\Release\TsukiSynthAuditTest.exe`（見 GATE 證據檔 §2 完整輸出）。
方法：`reportReverbWetGainQuantification()`——48 kHz、固定種子（271828）白噪 2 s burst
+ 12 s 靜音尾段，`mix=1.0`；ALGO 用 reverb 預設（`roomSize=0.5`，未 author decay）；
先量出 ALGO 的實際（emergent）T60，再合成一顆「指數衰減白噪」IR，把它的 −60 dB 衰減點
**反推對齊**到同一個 T60，餵同一段噪音進 IR 模式量。T60 判定用「−60 dB 交越」
（burst 結束後，512-sample 滑動窗 RMS 相對 burst 穩態電平掉到 −60 dB 的第一個時間點）。

| 量 | ALGO | IR（T60 對齊） |
|---|---|---|
| wet 穩態 RMS（dBFS） | **1.857** | **−26.626** |
| 量到的 T60（s） | 1.173333 | 1.173333（與合成 IR 的目標 T60 一致，確認 IR 對齊成功） |

- **RMS 差（IR − ALGO） = −28.483 dB**（IR 比 ALGO 小 28.5 dB）
- **理論差（只算 0.15 因子）= 20·log10(1/0.15) = 16.478 dB**（IR 應該比 ALGO 大 16.5 dB）

### 這代表什麼——誠實的落差說明

實測方向和量級都跟「只有 0.15 因子」的理論值對不上。這不是量測錯誤，是兩個演算法的
本質差異蓋過了 0.15 因子：

1. **ALGO 是回饋式 comb/allpass（IIR）**：8 個並聯 comb 在穩態下對寬頻雜訊有近似
   單位增益的持續響應（回饋讓輸入能量在濾波器裡循環疊加），wet RMS 跟輸入 RMS
   量級相近是正常的。
2. **IR 是一次性摺積（FIR）**：這裡用來對齊 T60 的**合成 IR**本身是「隨機白噪 × 指數衰減
   envelope」；它的總能量（所有 IR 樣本平方和）由 envelope 下的面積決定，跟 ALGO 回饋
   結構的穩態增益是完全不同的物理量，即使兩者 T60 相同也不會有相近的穩態 wet 電平。
3. 換句話說：**T60 對齊只保證「多快消失」相同，不保證「多大聲」相同**——而 K-02 真正要問的
   正是「多大聲」這件事，0.15 只是其中一個已知、可讀出的因子，實測到的 −28.483 dB
   落差裡混了「0.15 因子」和「IR 摺積 vs comb 回饋的固有增益差」兩件事，本次方法**無法把
   兩者分開**。

**能誠實回答的只有**：ALGO 路徑確實多乘 `0.15`（file:line 已核實，§1），這個因子本身的
理論貢獻是 16.478 dB；至於「使用者實際切換 ALGO/IR 時聽到的整體音量落差」還受 IR 檔案本身
的能量正規化方式影響（例如真實録的 IR 檔案，其能量分佈與這裡的合成白噪 IR 不同），
不能只用 0.15 一個數字去預測。

## §3 三個選項（看數字自己選，不替月月裁決）

| 選項 | 做法 | Rule 10 衝擊 |
|---|---|---|
| **A** | IR 路徑也乘 `0.15`（`EffectChain.h:229-230` 加係數） | 只影響 plugin 的 IR 模式（`EffectChain::processBlock`）。CLI／`ScoreRenderer` 目前不使用 IR 路徑（README 已核實 CLI 不觸發此分支），所以 **corpus 渲染理論上不變**——但這是「理論上」，真正落地前仍需按 R10 對 8/8 位元不變腳本重新驗證（若哪天 corpus 開始用 IR 模式就會改變）。 |
| **B** | 拿掉 ALGO 的 `0.15`（`SimpleReverb.h:156`） | **全 corpus 渲染改變**——`SimpleReverb` 被 CLI／`ScoreRenderer` 的 reverb 路徑直接使用（無 IR 分支），任何動它就是動了現有 8 首代表曲的音訊內容，R10 觸發，需要完整前後對照報告才能落地。 |
| **C** | 維持現狀，在 UI／文件標註「ALGO 與 IR 音量不對等，需自行用 wet/mix 補償」 | 不改任何渲染輸出，零 Rule 10 衝擊；缺點是使用者切換 reverb 模式時響度會突然跳動（本次實測跳動方向是 IR 明顯更小聲，−28.5 dB，不是原先設計文件假設的「IR 更大聲」）。 |

## §4 附註：與工作卡假設的落差

工作卡 §0 的描述「ALGO reverb wet 額外乘 0.15、IR 路徑沒有」（file:line 已核實為真）
隱含的預期是「IR 會比 ALGO 大聲」，但 §2 的實測顯示**實際落差方向相反**——這點必須
明寫在此，供月月裁決時參考：**選項 A（讓 IR 也乘 0.15）不會讓兩者音量對齊**，因為
真正主導落差的是摺積 IR 本身的能量正規化，不是 0.15 這個因子；若要讓 ALGO/IR 切換時
音量真正一致，需要的是「IR 載入時依響度正規化」這類獨立於本卡範圍的設計，不在本裁決包
三選項之內。

---

## §5 裁決記錄（2026-09-09，月月：「K-02 你評估，我看不懂」→ 規劃者評估並代決）

**白話版**：這個問題原本以為是「ALGO 多乘了一個 0.15，所以 IR 比較大聲」，量了之後發現方向反了——
IR 反而小 28.5 dB，而且主因不是 0.15，是兩種殘響演算法本來就不同量級。所以三個選項都**修不到真正的問題**：

| 選項 | 我的評估 |
|---|---|
| A：IR 也乘 0.15 | **更糟**。IR 已經小 28.5 dB，再乘 0.15 變小 45 dB。否決。 |
| B：拿掉 ALGO 的 0.15 | 全 corpus 75 檔渲染改變，等於重做所有商品的母帶。B4 之後現行 CLI 音質已被定為最終音質，不值得為 plugin 端的切換手感動它。否決。 |
| **C：維持現狀＋標註** | **採用**。零 Rule 10 衝擊。F-03 落地卡（WF0908-P3）的缺檔警告文字已規定要寫「音量會與 IR 模式不同」。 |

**同時登記一項新工程項（D 類，不在本輪）**：「IR 載入時的響度對齊」——真正能讓切換不跳音量的方法，
是在載入 IR 時量它的能量並對齊到 ALGO 路徑的 wet 電平（Waves IR-1 有類似的匯入正規化，但目的是防削波不是對齊，見 F03 §7.2）。
這需要先用**真實 IR 檔**（不是本卡的合成白噪 IR）量幾組數字才知道對齊目標怎麼定，否則會變成憑空造常數（R4）。
只影響 plugin IR 模式，CLI 不用 IR → 不觸發 Rule 10。等 F-03 落地後再開卡。

**不動的東西**：`SimpleReverb.h` 的 0.15、`EffectChain.h` 的 IR 混合、任何容差。
