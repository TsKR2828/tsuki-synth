# A14 B-2 Rule 10 前後對照報告：鋼琴氈槌 τc 音高律錨定到量測曲線（B4 g-based → keytrackScale）

> 產出：2026-09-09（施工卡 `docs/workcards/WF0908_P2_a14_tauc_rule10.md`）
> 依據：`reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md` §3.2–3.5、§4 選項 B、2026-09-08 裁決記錄。
> **本卡合法終點是 BLOCKED(R10)：程式改好、GATE 全跑、本報告寫好，`src/` 未落地（改動存成 patch），等月月放行。**
> 範圍：只有 `HammerImpulse::pianoHammerTauC()` 的**音高形狀**——原本由 B4 的 K/α/質量錨點表隱含推出
> （等效 k≈0.212），改成本檔已溯源的量測擬合 `keytrackScale()`（k=0.32，A4=2.0ms）；**力度形狀不變**
> （仍是 B4 的 `g(note,v)/g(note,0.5)`，只是分母從固定的 `g(69,0.5)` 換成同一個音符的 `g(note,0.5)`）。
> `keytrackScale()`、`forceSpectrumMagnitude()`、`tauCForNote()`、四檔硬度查表、clamp 常數**全部未動**。
> before 基線＝本卡開工前的乾淨工作樹（HEAD `98f346f`，`src/physics/HammerImpulse.h`／
> `tests/physics_models_repro.cpp` 均與 index 一致）；before/after 各自用 `build-wf` 重建的 CLI 獨立渲染。
> 方法腳本與原始資料：`reports/gate_outputs/wf0908_method/`（`a14_b2_tauc_probe.py`、
> `affected5_before_after.py`；沿用 `reports/gate_outputs/wf0907_method/render_wf_scores.py` 做 8 首位元不變）。

---

## §0 白話導讀卡

**一句話結論**：鋼琴氈槌接觸時間 τc 的「音高怎麼隨鍵盤位置縮短」這條曲線，從程式內部算出來的形狀
換成貼合實測（Askenfelt & Jansson）的曲線之後，**G5/G6 的基頻不再掉進力脈衝公式的深零點**：
G5 的第2泛音相對基頻從「反超 +9.1 dB」變成「基頻正常壓過泛音 −2.7 dB」，G6 從「反超 +10.9 dB」變成
「基頻壓過泛音 −36.9 dB」；跨鍵盤（MIDI 37→87）整體響度落差從 −22.1 dB 收斂到 −17.9 dB（少掉 4.2 dB
的人工陡降）。**音高（f0）與衰減（T60）在受影響的全部 949 個事件、逐 partial 完全零差**（本輪自己
獨立重驗，方法見 §3）；受影響的只有這 5 首 corpus（RMS 變化 ≤0.65 dB，都在正規化尺度內），
其餘 68 首與非 Felt 路徑照 R6 規約不需要重測（B4 已建立的路徑分派邏輯本卡未動一行）。

**為什麼會這樣**：B4 原公式把「音高」跟「力度」兩件事混在同一個比例式 g(note,v) 裡，音高的部分
只是三個 K/α 錨點和八個槌質量錨點按物理推導出來的副產品（等效冪次 k≈0.212），沒有人真的拿它去對過
量測曲線；比文獻量測值（k≈0.276～0.32）平了將近 1/3，高音的接觸時間因此偏長，長到 G5 的基頻正好
撞上力脈衝頻譜 `H(f,τc)=|cos(ωτc/2)|/|1-(ωτc/π)²|` 在 x=2f·τc=3 的深零點（−34.5 dB）。改法是把音高
形狀直接換成本檔案本來就有、已溯源的 `keytrackScale()`（A0 4ms→C8 <1ms 的量測擬合），力度形狀完全
不動——只是分母從「固定 A4 錨點」換成「同一個音自己的 v=0.5 值」，這樣兩件事才真正分開。

**你要做的裁決**：接受這批改變（`git apply reports/a14_tauc_keytrack_b2.patch`），或指名回退／要求
先做 A14 §4 的 B-1（力脈衝滾降形狀本身）。所有改動目前都在 patch 檔裡、工作樹已還原（§7 有還原後
8/8 位元不變的重跑證據），你保有完整否決權。

**這次沒有解決的**：A14 §4 的 B-1（力脈衝在 x>1 之後為什麼有「深零點」而不是平滑滾降——文獻原文
仍未取得，A14 report 明寫不得先填替代曲線）；noteComp 響度補償在 MIDI 67 以上仍然頂到 clamp 上限
4.0（§5 有數字，改善很小，B-1/B-2 都做完才會退出飽和，這是預期中的殘留，A14 決策記錄已登記）。

---

## §1 改動內容

```cpp
// before (B4, 2026-08-27)
tau_c_piano(note, v) = kTauCFelt * g(note, v) / g(69, 0.5)

// after (A14 B-2, 本卡)
tau_c_piano(note, v) = kTauCFelt * keytrackScale(note) * [ g(note, v) / g(note, 0.5) ]
```

- A4（MIDI 69）/ v=0.5 錨點完全不變（`keytrackScale(69)=1`、`g(69,0.5)/g(69,0.5)=1`）——單元測試
  `pianoHammerTauC(69,0.5) == kTauCFelt`（1e-4 內）仍過。
- 力度律在固定音高下與 B4 舊版**數值等價**（不是巧合，是代數恆等式）：
  `new(note,v)/new(note,0.5) == g(note,v)/g(note,0.5) == old(note,v)/old(note,0.5)`
  （`keytrackScale(note)` 與 v 無關，比值裡直接消掉）——單元測試新增 §A14-4，
  4 個音高 × 4 個力度共 16 組相對誤差 < 1e-6，全部驗證通過。
- 只動了 `src/physics/HammerImpulse.h` 的 `pianoHammerTauC()` 函式本體與其上方註解；
  `keytrackScale()`、`forceSpectrumMagnitude()`、`tauCForNote()`、`pianoHammerG()`、
  `alphaForPianoNote()`／`logKForPianoNote()`／`hammerMassForPianoNote()`、四檔硬度表、clamp
  常數 `kPianoTauCMinS/MaxS` **一行都沒動**——所以 CimbalomEngine.h 的兩處呼叫點
  （`pianoHammerTauC(midiNoteNumber, velocity)` 與 `(midiNoteNumber, 0.5f)`）簽章不變，不用改呼叫端。
- 新增單元測試（`tests/physics_models_repro.cpp`，§A14-1～§A14-4）：A4 錨點不變、C8 τc < 1ms、
  C2→C7 等效 k = 0.32±0.01、力度律位元等價。

---

## §2 GATE 1：8 首代表曲位元不變（README §3 位元不變腳本）

`reports/gate_outputs/wf0907_method/render_wf_scores.py`（沿用既有腳本，`--cli build-wf\...`）：

| 曲目 | before sha256（前 16 位） | after sha256（前 16 位） | 是否相同 |
|---|---|---|---|
| moonlight_sonata_movement1_yangqin | 49514b007e3e01fc | 49514b007e3e01fc | 相同 |
| moonlight_sonata_movement1_yangqin_tongue_mix | 7b0413dd4f858079 | 7b0413dd4f858079 | 相同 |
| **physical_piano** | 607d0d3bc578136f | **1233b53f1e8660bc** | **不同（預期）** |
| restraint_metal_click | be634798c4a0bf71 | be634798c4a0bf71 | 相同 |
| moonlight_sonata_movement1_tongue_drum | c37ac02d01f08a30 | c37ac02d01f08a30 | 相同 |
| water_gong_free | 31b539c6ac08d942 | 31b539c6ac08d942 | 相同 |
| ai_radiance_m1 | 74122637a0c71278 | 74122637a0c71278 | 相同 |
| fur_elise_opening | b0877774da9e5fc5 | b0877774da9e5fc5 | 相同 |

**7/8 IDENTICAL，只有 `physical_piano` 改變** —— 與卡上 §3 步驟 5 的預期完全一致。
證據檔：`reports/gate_outputs/wf0907_method/sha256_wf0908_p2_baseline.txt`（開工前基線）、
`sha256_wf0908_p2_after.txt`（改後）；重建 patch 還原後又重跑一次 `sha256_wf0908_p2_after_recheck.txt`，
與 `sha256_wf0908_p2_after.txt` **逐位元相同**（證明 patch 重套用可重現同一顆 binary，見 §7）。

---

## §3 f0 / T60 逐位元零差（949 個事件、86,900 個 partial 全量驗證）

不像 B4 report 只挑 22 個 Felt 事件抽驗，本輪對 5 首受影響曲目**全部事件**跑
`--dump-modes`，把每個 partial 的 `freq` 與 `decay` 欄位（**不含 `amp`**）四捨五入到小數 6 位後串接，
取 SHA256 指紋；`amp` 欄位另外單獨取一份指紋做對照組（`affected5_before_after.py`）：

| 曲目 | events | partials | freq/decay sha256（前 16 位，before=after 才算過） | amp sha256 before | amp sha256 after |
|---|---|---|---|---|---|
| fur_elise_complete | 905 | 84,732 | `badd6b330de222d6`（**相同**） | `ea5dca47bc4f5fa6` | `70d8a5f279944864`（**不同**） |
| physical_piano | 4 | 416 | `e6e24d1201899565`（**相同**） | `38b286f496616910` | `bc1299a1874c1900`（**不同**） |
| akashic_action_001 | 2 | 58 | `73c44e5ab381e363`（**相同**） | `cce55e1527e24e51` | `d638ab4bcc87578c`（**不同**） |
| ocean_action_001 | 2 | 127 | `96165dac466df1a4`（**相同**） | `d19f40deb522202e` | `e1e5a8c0b576e7fb`（**不同**） |
| ai_radiance_m3 | 36 | 1,567 | `d813f14dc6a8dae4`（**相同**） | `41c9851c9fccc328` | `3eecce72fbed6088`（**不同**） |

**5/5 曲目、86,900 個 partial 的 freq＋decay 逐位元完全相同**（f0／T60 零差），**同時 5/5 曲目的 amp
指紋全部不同**（證明 τc 確實變了、激發振幅真的重新計算，不是碰巧沒接線）。這是比 B4 report 的抽樣
方法更強的證據——不是挑 22 個代表事件，是這 5 首曲子的**全部**事件。
原始資料：`reports/gate_outputs/wf0908_method/affected5_fingerprint_{before,after}.json`。

閉環理由（與 B4 report §2b 同一套論證，這裡改用全量指紋做）：`pianoHammerTauC()` 的輸出只餵給
`HammerImpulse::forceSpectrumMagnitude()` 做振幅整形（`CimbalomEngine.h` 兩處呼叫點），frequency 由
`StringModel::calculateModes()`／decay 由 `StringModel::decayTimeForFrequency()` 算，兩者都不吃 τc
參數（`git diff` 只碰 `HammerImpulse.h` 一個檔案可證）——因此 freq/decay 不可能被這次改動影響，
指紋比對只是把這個代碼層事實在數據上釘死。

---

## §4 受影響 5 曲整曲 RMS／頻譜質心對照（Rule 10 指定量）

`affected5_before_after.py`（RMS＝整曲混單聲道 20·log10(RMS)、質心＝整曲無窗 rfft 振幅加權，
與 B3／B4 report 同一把尺，但**注意不可跨報告直接對減**——各報告的受影響清單/基線不同）：

| 曲目 | RMS 前 (dBFS) | RMS 後 | ΔRMS (dB) | 質心前 (Hz) | 質心後 | Δ質心 |
|---|---|---|---|---|---|---|
| fur_elise_complete | −23.338 | −22.691 | +0.647 | 697.45 | 708.42 | +1.57% |
| physical_piano | −18.579 | −18.485 | +0.094 | 842.61 | 836.32 | −0.75% |
| akashic_action_001 | −22.249 | −22.007 | +0.242 | 1180.46 | 1167.73 | −1.08% |
| ocean_action_001 | −23.199 | −23.160 | +0.039 | 244.88 | 206.81 | **−15.55%** |
| ai_radiance_m3 | −20.585 | −20.642 | −0.057 | 783.81 | 783.23 | −0.07% |

**歸因**：`physical_piano`（`before` 值 = B4 report「後」欄 −18.579／842.61，逐位吻合，確認 baseline
接續正確）的 Felt 事件涵蓋 C4–C5，本卡只動音高形狀、力度形狀不變，中音域 keytrackScale 與 B4 舊等效
指數差異不大，RMS/質心變化很小（<0.1dB／<1%）。`ocean_action_001` 質心 −15.55% 最大：唯一 Felt 事件
是 D1（MIDI 26，flat 夾在最近錨點外），keytrackScale 在極低音域把接觸時間拉得比 B4 舊公式更長
（低音本來就該長，符合 keytrackScale 的量測意圖），高次 partial 份額相對降低，質心下移——這是**低音
更貼近文獻低音長接觸時間形狀**的直接結果，不是缺陷。`fur_elise_complete` 質心 +1.57%（905 個 Felt
事件橫跨全鍵盤，含 G5/G6 附近的音，基頻回升後高頻份額比例變化）。`akashic_action_001`（D5 事件）與
`ai_radiance_m3`（F4–F5 附近事件，貼近 A4 錨點）變化都很小。

**5 首個別 GATE**（`verify_score.py --cli build-wf\...`，未用 `--all`——依卡 §3 步驟 6 只需這 5 檔）：

| 曲目 | before | after |
|---|---|---|
| fur_elise_complete | PASS | PASS |
| physical_piano | PASS | PASS |
| akashic_action_001 | PASS | PASS |
| ocean_action_001 | PASS | PASS |
| ai_radiance_m3 | PASS | PASS |

**5/5 × 2（before/after）= 10/10 ALL CHECKS PASSED**。
證據：`reports/gate_outputs/wf0908_method/affected5_verify_{before,after}.txt`、
`affected5_render_{before,after}.csv`。

---

## §5 A14 §3 核心數字：τc / x / H(f1) / 逐 partial 對照（G5/G6/D7 為主，C4/A4 為對照）

`a14_b2_tauc_probe.py`：對每個音渲染單音 score（piano 引擎、v=0.45、steel Ø1.0mm，效果全關、
`normalize:false`，與 A14 report 附錄 B 同一套診斷設定），`--dump-modes` 取中央弦 partial 振幅；
τc/x/H(f1) 是本卡自己獨立寫的 Python 鏡像（`HammerImpulse.h` 的 float64 重寫），**先用 before 變體
自我核對**：本輪算出的 before 數字（τc/x/H(f1)）與 A14 report §3.2/§3.3 的 float64 複核欄
（G5 x=2.910／H=−34.50dB，G6 x=5.063／H=−47.91dB，D7 x=7.120／H=−48.44dB）**逐位吻合**，
證明鏡像公式正確、方法論與既有 A14 卡一致。

| 音 | τc 前 (ms) | τc 後 | x 前 | x 後 | H(f1) 前 (dB) | H(f1) 後 | dump 第2−第1 partial 前 (dB) | 後 |
|---|---|---|---|---|---|---|---|---|
| C4 | 2.3535 | 2.4711 | 1.2315 | 1.2930 | −3.242 | −3.595 | −8.178 | −10.667 |
| A4（錨點） | 2.0967 | 2.0967 | 1.8451 | 1.8451 | −7.880 | −7.880 | −9.952 | −9.952 |
| **G5** | 1.8560 | **1.7466** | 2.9101 | **2.7387** | −34.496 | **−24.238** | **+9.066** | **−2.725** |
| **G6** | 1.6146 | **1.4025** | 5.0632 | **4.3982** | −47.909 | **−27.092** | **+10.909** | **−36.871** |
| D7 | 1.5154 | 1.2334 | 7.1204 | 5.7954 | −48.444 | −30.717 | −24.454 | −8.020 |

**A4 錨點行前後逐位元相同**（τc/x/H(f1)/dump 全部一致，設計如此）。**G5、G6 是本卡的核心成果**：
第2泛音相對基頻從「反超」（+9.07 dB／+10.91 dB，A14 §1 原始問題的症狀）變成「基頻正常壓過第2泛音」
（−2.73 dB／−36.87 dB）。D7 的 H(f1) 也從 −48.4dB 回升到 −30.7dB（改善 17.7dB），但 dump 第2−第1
仍是負值（−8.02dB，方向本來就對，只是幅度變了——D7 x 從 7.12 降到 5.80，仍遠大於 1，仍在 A14 §3.3
指出的「半正弦模型失效區」，這是 B-1 才能處理的範疇，B-2 沒有義務也沒有能力解決）。C4 略微變差
（H(f1) −3.24→−3.60dB，x 1.23→1.29，變化 <0.4dB，中低音域 keytrackScale 比 B4 舊等效 k 稍陡一點點
的預期副作用，量級遠小於高音的改善）。

---

## §6 MIDI 37→87 跨鍵盤斜率、noteComp 飽和表

**跨鍵盤峰值/RMS 斜率**（`a14_sweep_piano.score.json`，同一份 score 前後各渲染一次；沿用
A14 R2 的 `sweep.py` 端點差方法）：

| | before | after | 改善 |
|---|---|---|---|
| 峰值斜率 MIDI37→87 | **−22.098 dB** | **−17.857 dB** | 少掉 4.24 dB 陡降 |
| RMS 斜率 MIDI37→87 | **−27.459 dB** | **−25.254 dB** | 少掉 2.21 dB 陡降 |

before 兩欄與 A14 report §3.5「piano（felt，現況）」列（−22.10dB／−27.46dB）逐位吻合，交叉確認
本輪 before 基線正確接上 A14 卡當時量到的狀態。**跨鍵盤響度陡降有改善但沒有完全消失**——A14 §3.5
自己指出真正的決定性對照組是「只換 τc」（wood 槌，−2.2dB），B-2 只修音高律的一半（keytrackScale
本身仍在 x>1 用一個只在 x<1 有效的力脈衝模型），完全拉平要等 B-1。

**noteComp 響度補償反解值**（`ModalResonator::loudnessCompensationGain()`，反解方法：v=0.5 時
`tauC(actual)==tauCRef` 精確相等，dump 中央弦 p1 振幅 = `sin(π/8)·H(f1,τcRef)·noteComp/√nStrings`，
逆解 noteComp；clamp [0.25, 4.0]）：

| MIDI | 61 | 64 | 67 | 69 | 79 | 91 | 98 |
|---|---|---|---|---|---|---|---|
| noteComp 前 | 2.7667 | 3.3241 | 4.0000（飽和） | 4.0000（飽和） | 4.0002（飽和） | 4.0001（飽和） | 3.9979 |
| noteComp 後 | 2.8975 | 3.4251 | 4.0000（飽和） | 4.0000（飽和） | 4.0000（飽和） | 3.9998（飽和） | **3.9993（飽和）** |

before 各欄與 A14 report §3.4 反解表（2.767／3.324／4.000／4.000／4.001／3.997／3.994）逐位吻合
（<0.01 誤差，method 獨立重寫的正常浮點/取樣差）。**MIDI 67 起仍然頂到飽和上限，B-2 沒有讓它退出
飽和**——這是 A14 決策記錄裁決 (2026-09-08 增補) 已經預告的殘留：noteComp 是對全部 ~120 個模態的
攻擊能量積分，音高形狀的局部改善（G5/G6/D7 附近）被積分平均掉，要等 B-1（滾降形狀本身）修完才可能
把整體攻擊能量拉回 clamp 範圍內。**誠實聲明：本卡沒有解決 noteComp 飽和，只確認它前後都在飽和、
飽和值本身幾乎不變**（MIDI 98 從未飽和 3.9979 變成剛好卡在飽和邊界 3.9993，屬雜訊量級）。

---

## §7 patch 化與工作樹還原（Rule 10 硬性要求，卡上步驟 8）

```
git diff -- src/physics/HammerImpulse.h tests/physics_models_repro.cpp \
    > reports/a14_tauc_keytrack_b2.patch
```

- `git apply --check reports/a14_tauc_keytrack_b2.patch` → **通過**（證據：
  `reports/gate_outputs/wf0908_P2_tauc.txt` 內附完整輸出）。
- 還原方式：`git show :src/physics/HammerImpulse.h > src/physics/HammerImpulse.h`、
  `git show :tests/physics_models_repro.cpp > tests/physics_models_repro.cpp`
  （讀 index 版本覆寫工作樹，**不是 `git checkout`**，R7 合規）。
- 還原後重建 `build-wf` 三 target + 測試 target，重跑位元不變腳本 →
  **8/8 IDENTICAL**（`reports/gate_outputs/wf0907_method/sha256_wf0908_p2_baseline.txt`
  = 開工前基線；本輪流程：baseline(8/8) → 改動 → after(7/8) → revert 量測用（before 測量） →
  重套用 patch → after_recheck(與 after 逐位元相同，見 §2）→ 最終於本報告完成後再次還原，
  由稽核親自重跑確認）。
- **依卡 §4 禁止項，`src/physics/HammerImpulse.h` 與 `tests/physics_models_repro.cpp` 兩者都留在
  patch 裡不落地、不 stage**：稽核 PASS 時只 stage patch 檔本身、本報告、
  `reports/gate_outputs/wf0908_P2_tauc.txt`、`reports/gate_outputs/wf0908_method/*`、
  `reports/gate_outputs/wf0907_method/render_wf0908_p2_*.csv`／`sha256_wf0908_p2_*.txt`。

---

## §8 GATE 完成狀態（`reports/gate_outputs/wf0908_P2_tauc.txt` 附完整命令輸出）

| GATE | 結果 | 證據 |
|---|---|---|
| 1. baseline 8/8 | IDENTICAL | `sha256_wf0908_p2_baseline.txt` |
| 1. 改後 7/8＋只有 physical_piano 變 | 確認 | `sha256_wf0908_p2_after.txt` diff（§2） |
| 2. ctest 全綠 | 4/4 Passed | `wf0908_P2_tauc_ctest.txt` |
| 2. `--full --cli build-wf...` | NO CHECKED FAILURES（F3 piano PASS，3 筆既有 rubber UNVERIFIED 不變） | `wf0908_P2_tauc_physics_verify_full.txt` |
| 3. 單元測試新增項 | §A14-1～§A14-4 全 PASS（含 C8<1ms=0.9727ms、k=0.32000、力度律 16/16 組 <1e-6） | ctest stdout（physics_models_repro） |
| 4. 前後對照數字表 | §4／§5／§6 齊全；本報告存在 | 本檔 |
| 5. `python -m pytest tests -q` | 260 passed, 1 skipped | `wf0908_P2_tauc_pytest.txt` |
| 6. `git diff --stat` 範圍 | 只含 `src/physics/HammerImpulse.h`、`tests/physics_models_repro.cpp`、本報告、`reports/a14_tauc_keytrack_b2.patch`、`reports/gate_outputs/wf0908_P2_tauc.txt`、`reports/gate_outputs/wf0908_method/*` | `wf0908_P2_tauc.txt` 內附 `git diff --stat` |
| 5 首受影響 corpus 個別 GATE | 10/10 ALL CHECKS PASSED（before+after） | `affected5_verify_{before,after}.txt` |
| f0/T60 全量位元不變 | 5/5 曲目、86,900 partial freq/decay 逐位元相同 | `affected5_fingerprint_{before,after}.json` |
| patch `git apply --check` | 通過 | `wf0908_P2_tauc.txt` |
| 工作樹還原後重跑位元不變 | 8/8 IDENTICAL | `wf0908_P2_tauc.txt` |

---

## 附：方法與再現

```
# 1. baseline（開工前，8/8）
python reports\gate_outputs\wf0907_method\render_wf_scores.py --label wf0908_p2_baseline \
    --workdir <repo外目錄> --cli build-wf\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe

# 2. 改動 HammerImpulse.h + physics_models_repro.cpp，三 build + 測試 target（X4）
cmake --build build-wf --config Release --target TsukiSynthCLI TsukiSynth_Standalone TsukiSynth_VST3
cmake --build build-wf --config Release --target TsukiSynthAuditTest TsukiSynthTunerTest ^
    TsukiSynthPhysicsModelsTest TsukiSynthSpectrumViewTest TsukiSynthHostProbe
ctest --test-dir build-wf -C Release --output-on-failure
python tools\physics_verify.py --full --cli build-wf\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe

# 3. 前後對照（τc/x/H/noteComp/sweep；5 曲 render+fingerprint；逐一 verify_score.py）
python reports\gate_outputs\wf0908_method\a14_b2_tauc_probe.py --cli <cli> --label <before|after> \
    --variant <before|after> --workdir <repo外目錄>
python reports\gate_outputs\wf0908_method\affected5_before_after.py --cli <cli> --label <before|after> \
    --workdir <repo外目錄>

# 4. patch 化 + 還原
git diff -- src/physics/HammerImpulse.h tests/physics_models_repro.cpp > reports\a14_tauc_keytrack_b2.patch
git apply --check reports\a14_tauc_keytrack_b2.patch
git show :src/physics/HammerImpulse.h > src/physics/HammerImpulse.h
git show :tests/physics_models_repro.cpp > tests/physics_models_repro.cpp
# 重建 + 重跑步驟 1 位元不變腳本，確認回到 8/8 IDENTICAL
```

逐欄位定義：RMS＝整曲混單聲道 20·log10(RMS)、質心＝整曲無窗 rfft 振幅加權（與 B3/B4 report 同尺，
不可跨報告直接對減）；τc/x/H(f1) 為本卡獨立寫的 `HammerImpulse.h` float64 Python 鏡像，
已用 A14 report 的 float64 複核欄與本卡自己的 before 變體交叉驗證逐位吻合；freq/decay 指紋＝
`--dump-modes` 全部 partial 的 `(freq, decay)` 四捨五入 6 位小數後串接取 SHA256，`amp` 另外單獨取指紋
做「確實接線」的對照組。

---

## 落地記錄（2026-09-10）

月月 2026-09-10 裁決：**放行**本卡的 B-2 patch，`git apply reports/a14_tauc_keytrack_b2.patch`，
落地卡 `docs/workcards/WF0908_P2_a14_tauc_rule10.md`，整合工兵 Sonnet 執行、證據檔
`reports/gate_outputs/wf0910_A14_apply.txt`。

- **patch sha256**：`5f5cce8d137bede2b2c70e3ef47793f7d01ff1c0dfabf144c7b867e6b9d489de`
  （`reports/a14_tauc_keytrack_b2.patch`）。
- **位元不變（8 首代表曲，對 `build\` binary 重跑）**：7/8 IDENTICAL；只有 `physical_piano` 改變——
  舊 sha256 `607d0d3bc578136ff8ebb0bd5c428582d2c2db6ede3989286284539399d52f71` →
  新 sha256 `1233b53f1e8660bcb46277da814c62190c8f283e20d57ae8297fb865878fc55b`，
  與本檔 §2 表格記錄的預期 after 值完全一致。新基準另存為
  `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`（`sha256_before_post_d8.txt` 保留存檔）。
- **GATE 結果一行摘要**：三 build target + 五測試 target（`build\`）全 exit 0；`ctest` 4/4 Passed
  （含 §A14-1～§A14-4 四項新單元測試 PASS）；`physics_verify.py --full` → NO CHECKED FAILURES
  （F3 piano velocity 判定仍 PASS，僅既有 3 筆 rubber UNVERIFIED）；受影響 5 檔 `verify_score.py` 全 PASS；
  `pytest tests -q` 263 passed / 1 skipped / 3 xfailed；HostProbe PASS (0 failures)。
  全套細節見 `reports/gate_outputs/wf0910_A14_apply.txt`。
