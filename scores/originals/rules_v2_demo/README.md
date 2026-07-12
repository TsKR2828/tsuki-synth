# Rules v2 Demo（規則二版示範作）

**ROADMAP_PHYSICS.md M9-9d GATE 示範作。** 這首曲子的每一個規則都對應到
`reports/consonance_tables.md`（M9-9a：Sethares dissonance-curve 局部極小值）
或該報告 §4（M9-9b：T60/3 時值下限）裡的一個具體數字。沒有任何音高/時值選擇是
「聽起來對」決定的——見下方逐條對照。

## 曲式

AABA + 尾聲（末段延長的匯聚 cell 當結尾）：

| Section | 大約時間 | 根音 | 動態 (velocity) |
|---|---|---:|---:|
| A | 0 – ~21s | MIDI 55 (G3) | 0.40 |
| A2 | ~21 – ~39s | MIDI 55 (G3) | 0.60（×1.5 = +3.5dB，M6 表） |
| B | ~39 – ~63s | MIDI 60 (C4，A 根音 +500c＝cimbalom 自身局部極小值之一) | 0.90（×1.5 = +3.5dB） |
| A3（recap） | ~63 – ~82s | MIDI 55 (G3) | 0.45（B 的 ×0.5 = −6.0dB） |
| 尾聲 | ~82 – ~90s | MIDI 55 (G3) | 0.45（cimbalom）/ 0.225（water_gong，×0.5=−6dB 淡出） |

全部動態變化都是 `docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` §4.6（M6-6a velocity→dB
表）裡列出的乾淨倍率（×1.5=+3.5dB、×0.5=−6.0dB、×2=+6.0dB），不是隨手挑的數字。

## 配器角色（9c 聲部配器建議的具體實作）

- **cimbalom（和聲角色）**：唯一擔任同時多聲部/和聲功能的引擎，因為它是 5 個
  modal 引擎中最接近諧波的一個（`reports/consonance_tables.md` §2：partial 比例
  1.000/2.001/3.004/4.009...，幾乎整數）。全曲主體是**單旋律琶音**（同一時間只有
  一個 cimbalom 音在響），刻意不疊 cimbalom 自身和弦，理由見下方「範圍限制」。
- **tongue_drum（色彩/節奏角色）**：只在每個 section 開場的「匯聚 cell」短促標記
  一下（0.35 秒），不是連續 ostinato。這呼應 ROADMAP_PHYSICS.md M9 的「為什麼」
  段落裡提到的 gamelan/鐘樂典範——一個宣告樂段開始的短促標記音，而非連續旋律。
- **water_gong（結構標記角色）**：只在匯聚 cell 出現，八度長音覆蓋在 cimbalom
  持續音上，標記段落邊界；尾聲的 water_gong 音拉長到 6 秒，是全曲最後、最長的
  聲音（自然的收尾）。

## 匯聚 Cell（每個 section 開場的固定樣板）

```
t0        : cimbalom 持續音 = section 根音（root）
t0        : tongue_drum = root+7 半音（P5，700 cents）
              -> cimbalom→tongue_drum 跨引擎表最佳局部極小值 690 cents
                 （距離 10 cents，在 ±10 建議窗內；dissonance=0.0344，
                 reports/consonance_tables.md §3「cimbalom vs tongue_drum」）
t0+0.45s  : water_gong = root+12 半音（八度，1200 cents）
              -> cimbalom→water_gong 跨引擎表局部極小值 1195 cents
                 （距離 5 cents；dissonance=0.0503，同報告 §3「cimbalom vs
                 water_gong」）
              tongue_drum 已於 t0+0.35s 結束，兩者不重疊——見下方範圍限制。
```

`tools/check_piece_consonance.py` 對本曲的驗證結果（`reports/rules_v2_demo_consonance_check.md`）：
**13 個同時發聲音程對，13 個 PASS，0 個違規、0 個方向未驗證。**

## Cimbalom 自身琶音音程（單旋律，非同時發聲，但選字取自 self-consonance 表）

琶音 cell 用 `root, +7(P5), +12(octave), +7(P5)` 循環（A2/A3 額外加入
`+4(M3)` 當經過音）。這些位移數字取自 `reports/consonance_tables.md` §2
cimbalom 自身局部極小值：

- +7（700c）：曲線上最深的谷（實際極小值 705c，dissonance=0.0535，全曲線最低點之一）
- +12（1200c，八度）：dissonance=0.0274
- +4（400c，M3）：一個較弱、但仍登記在案的局部極小值（390c，dissonance=0.1713）

因為是單旋律（同一時間只有一個音），這裡的「協和度」是琶音聽感/理論的參考，不是
`check_piece_consonance.py` 會逐一稽核的「同時發聲」項目——這點在下面的範圍限制
裡誠實寫出來，不假裝它跟匯聚 cell 的跨引擎驗證是同一件事。

## 時值下限（M9-9b，T60/3）

`reports/consonance_tables.md` §4：cimbalom @ MIDI 55 附近（介於 48/60 兩個量測點
之間）T60 ≈ 1.95–1.98s，T60/3 ≈ 0.65–0.66s。本曲 cimbalom 琶音的 onset 間距固定
在 **0.75 秒**，全程超過每個量測音域的 T60/3 上限（0.66s），不會出現「上一擊還沒
衰減 20dB 就再擊同一個音」的情形——琶音本身音高不同（root/P5/8ve 輪替），實際上
比同音再擊的門檻更寬鬆，這裡採用比門檻更保守的統一間距，方便稽核。

tongue_drum 每次匯聚 cell 只響一次（不連續反覆），water_gong 同理，因此兩者都
遠低於 `reports/consonance_tables.md` §4 列出的密度上限（tongue_drum 2.46/s、
water_gong 2.53/s）。

## 已知範圍限制（誠實寫出，不是隱藏的簡化）

1. `tools/check_piece_consonance.py` 只檢查 score JSON 宣告的 `[time,
   time+duration)` 視窗有沒有重疊，不模擬敲擊後實際共鳴環繞超出宣告時長的部分。
   由於全曲的匯聚 cell 之間刻意保持單旋律（cimbalom 不與其他引擎重疊），這個
   限制主要只影響「cimbalom 琶音音符彼此之間」是否有共鳴殘留——見下一條。
2. Cimbalom 自身的 T60（~2 秒）比 0.75 秒的琶音間距長很多，代表**同一句琶音裡
   前一個音的共鳴會物理性地延續進下一個音符期間**（這是真實共鳴，不是 bug）。
   `check_piece_consonance.py` 不會把這種「宣告時長之外的殘響」算進同時發聲判定
   （它只看宣告的 duration），所以這份協和度檢查是保守/範圍受限的，不是「這首曲子
   完全沒有殘響交疊」的宣稱。
3. 跨引擎驗證只做了三個方向固定的配對（cimbalom→tongue_drum、cimbalom→water_gong、
   tongue_drum→water_gong，見 `tools/consonance.py` 的 `CROSS_PAIRS`）；本曲設計
   時刻意讓每次同時發聲都遵守這個方向（較低音一定是配對表裡「固定」的那個引擎），
   避免觸發「方向未驗證」。
4. `verify_score.py`（`--html` 報告 `rules_v2_demo_001.report.html`）用的
   f0 容差是 `MODE_F0_TOL_CENTS`＝12.0 cents（ROADMAP_PHYSICS.md M7-7a 說明過的
   既有例外，量測點是 `--dump-modes` 原始 string-0 值，非聲學質心），跟
   `tools/consonance.py`／`physics_verify.py` 用的 5.0 cents 是不同量測管線，
   不是本曲另外放寬的容差。

## 驗證指令與結果

```powershell
python tools/consonance.py                                              # 產出 reports/consonance_tables.md
python tools/check_piece_consonance.py scores/originals/rules_v2_demo/rules_v2_demo_001.score.json
  # -> reports/rules_v2_demo_consonance_check.md: 13 pairs, 13 PASS, 0 not-PASS
python tools/verify_score.py scores/originals/rules_v2_demo/rules_v2_demo_001.score.json
  # -> RESULT: ALL CHECKS PASSED (exit 0)
python tools/verify_score.py --html scores/originals/rules_v2_demo/rules_v2_demo_001.score.json
  # -> rules_v2_demo_001.report.html, exit 0
```
