# D11 Rule 10 前後對照報告：真實鋼琴弦長/弦徑逐八度查表取代簡化假設

> **2026-09-15 修訂**：稽核打回本報告 4 條 findings，已逐條修復——(1) §2 的非諧性 B
> 改用引擎實際定義（`freq = fn·f1·√(1+B·fn²)` 的閉式反解 `B=(r-1)/(4-r)`，r=(f2/2f1)²）
> 重算，取代原本誤用的小 B 近似式 `(r-1)/4`（`output/wf0914/D11/analyze_probe.py` 已修正，
> 見下方 §2 起始處的更正說明）；(2) §0/§2 的「87倍→14倍」「21倍→5倍」改用同一定義前後
> 一致重算為「87倍→18.7倍」「21.6倍→7.6倍」；(3) §6 的「2/8 首與官方基準不同」查證後
> 為誤判（本卡自建基線與官方 `sha256_before_post_a14.txt` 逐位元相同，只有 CRLF/LF 換行
> 差異），已改寫並補上獨立驗證證據；(4) patch 內死連結 `docs/d11_string_scale_before_after.md`
> 已修正為 `reports/d11_string_scale_before_after.md`（在候選碼上編輯、重新產生 patch、
> 再還原，`git diff`/`git apply --check` 重新驗證）。另外新增 `reports/decision_packets/
> D11_string_scale_candidate.zh-TW.md` 補齊 `WF0914_README.md` 要求的裁決包體例。
> 以下內文已依修復結果更新；未受影響的段落（§1 改動內容、§3 Path B 觀測量、§4/§5/§7
> 等）原樣保留。
>
> 產出：2026-09-15（施工卡 `docs/workcards/WF0914_D11_string_scale.md`）
> 依據：`docs/STRING_SCALE_SOURCES.md`（Phase A 溯源，轉引 `docs/HAMMER_CONTACT_SOURCES.md` §2.2，
> 原始出處 Woodhouse, *Euphonics* §12.2.1 Table 1）。
> **本卡合法終點是 BLOCKED(R10)：程式改好、GATE 全跑、本報告寫好，`src/`／`tools/` 未落地
> （改動存成 patch），等月月放行。**
> 體例比照 `reports/a14_tauc_keytrack_before_after.md`。
> before 基線＝本卡開工前的工作樹（含 WF0914-B7P0/B7P1/B7P3/D12 等既有 staged/unstaged 修改，
> HEAD `a38bd6a` 上再疊加這些卡）；本卡另存自己的當下基線
> `reports/gate_outputs/wf0914_D11_sha256_baseline_current_tree.txt`（單一變數比較用，
> **經 §6 驗證與 README 記錄的官方 `sha256_before_post_a14.txt` 逐位元相同**，2026-09-15
> 修訂前的初版曾誤判兩者不同，已撤回，詳見 §6）；
> before/after 皆用 `build-wf` 重建的 CLI 獨立渲染/dump。

---

## §0 白話導讀卡

**一句話結論**：鋼琴/揚琴的弦長公式一直假設「A4 是 0.35m，每升一個八度弦長剛好減半」，
弦徑則整條琴鍵盤固定一個數字（不隨音高變）——這兩個都是簡化假設，不是真鋼琴的樣子。
真鋼琴的弦長從最低音到最高音差 20 倍、弦徑也跟著變，而且低音到中音之間有一段明顯的
「斷點」（真實製琴在那裡從纏繞弦換成裸弦）。本卡把 `docs/HAMMER_CONTACT_SOURCES.md` 已經
查到、記錄在案的真實鋼琴逐八度弦長/弦徑表接進候選修正，量出來的效果是：**非諧性係數 B
在高音區明顯改善**（G6 對量測值的偏差倍數從 86.4× 縮小到約 18.7×，G5 從 21.6× 縮小到約
7.6×——用引擎實際定義的閉式公式重算，見 §2 開頭的更正說明），方向與
`reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md` §3.10 已登記的問題一致；
但也發現候選修正會讓 `physics_verify.py --full` 的一項自我一致性檢查（F5 殘餘能量）從歷史上
穩定 PASS（-63.9~-64.4dB）變成 FAIL（-58.5dB），這是本卡誠實回報、**沒有進一步查出根因**的
新缺口，見 §5。**本卡不建議在根因未查清前直接落地。**

**卡文標題用詞更正**（先讀，避免誤導）：本卡施工卡標題寫「B 路徑（B6 絕對聲壓）偏高
2.4～5.2×」，工兵核對後發現這句話**查無出處**——「2.4～5.2 倍」實際是非諧性係數 B（物理
符號，不是「Path B」路徑代號）的舊數字，且已在原文件被更正為 2.4～5.4；與弦長模型直接
掛勾、有完整逐音對照表的真正既有發現是 A14 §3.10 的「B 偏高 14–87 倍」。詳見
`docs/STRING_SCALE_SOURCES.md` §0。本報告的驗收數字因此改用可溯源、可核對的量
（非諧性係數 B 的前後對照、`absolute_pressure_per_force` 的前後對照），不使用卡文標題那個
查無出處的倍率。

---

## §1 改動內容

```cpp
// before（現行，src/physics/StringModel.h）
length(note)   = 0.35 * 2^(-(note-69)/12)              // 每八度減半，A4=0.35m
diameter(note) = <corpus 固定值，通常 0.8mm 或 score 指定 diameter_mm>

// after（本卡候選，StringModel::lengthFromScaleTable()/diameterFromScaleTable()）
length(note)   = interp(C1..C8 逐八度真實弦長表, note)   // 分段線性內插，範圍外 flat 夾住
diameter(note) = interp(C1..C8 逐八度真實芯線直徑表, note)
```

- 錨點（C1–C8，MIDI 24/36/48/60/72/84/96/108）、內插規則體例比照
  `HammerImpulse.h::interpAnchorsFlat()`，獨立實作（`StringModel.h` 不 include
  `HammerImpulse.h`），詳見 `docs/STRING_SCALE_SOURCES.md` §1 的完整表格與來源。
- 只改了 `StringModel::lengthFromMidiNote()` 的**呼叫端**（`CimbalomEngine.h` 三個構造路徑：
  `startNote()`、`noteOn()`、`worstCaseTailSeconds()`），`lengthFromMidiNote()` 函式本體
  **原封不動保留**（避免任何其他呼叫端受影響——目前確認只有這三處呼叫，見 §7 影響範圍）。
- 新增 `StringModel::lengthFromScaleTable()`／`diameterFromScaleTable()`，`tensionForNote()`
  未改（張力仍由長度/直徑/密度反推目標頻率，函式本體不變，只是現在吃到不同的 L/d 輸入）。
- 同步更新 `tools/physics_verify.py::stiff_string_oracle()`（獨立 Python 鏡射，見 §5.1
  的理由）——這個檔案本來就在卡文 GATE 的「`git diff -- src/ tools/ tests/` 必須為空」範圍內。
- **已知限制（誠實登記，非文獻缺陷）**：C1–C3 為真實纏繞弦（銅包鋼），本引擎的
  `StringModel` 只有單一材質/單一直徑的圓弦模型，候選修正取**芯線直徑**（不含纏繞層），
  會低估低音弦的線密度。真正的複合纏繞弦模型是本卡範圍外的獨立缺口，見
  `docs/STRING_SCALE_SOURCES.md` §2。

---

## §2 非諧性係數 B 前後對照（A14 §3.10 同一組音，核心結果）

診斷腳本：`output/wf0914/D11/probe_notes.score.json`（piano 引擎、steel、v=0.45、
`diameter_mm:1.0`、效果全關、`--dump-modes` 讀 partial[0]/[1] 反解 B；單音診斷，非
corpus，不計入 8 首位元基準）。

> **本節 2026-09-15 修訂（稽核 finding 1）**：本節初版 `output/wf0914/D11/analyze_probe.py`
> 用 `B=((f2/2f1)²-1)/4`——這是小 B 時的近似式，**不是**引擎的實際定義。引擎
> `src/physics/StringModel.h`（`calculateModes()`）用的是 `freq = fn·f1·√(1+B·fn²)`，
> 令 `r=(f2/2f1)²` 反解得閉式 `B=(r-1)/(4-r)`（`reports/decision_packets/
> A13_partial_gate_domain.zh-TW.md` §五「同上，改用閉式 B=(r−1)/(4−r)」、
> `A14_weak_fundamental_ruling.zh-TW.md` §3.10「B 的封閉式也同形」兩處都明寫這條閉式）。
> 近似式系統性偏低（B 越大偏差越大），已修正 `analyze_probe.py` 改用閉式重算，下表與
> `reports/gate_outputs/wf0914_D11_B_coefficient_probe.txt` 已同步更新。閉式重算的 A4/G5/G6
> before 值（1.360936×10⁻³／4.321166×10⁻³／1.728428×10⁻²）與 A13 §五記錄的**閉式
> `B=(r−1)/(4−r)` 反解值**（1.36081×10⁻³／4.32113×10⁻³／1.72844×10⁻²，A13:842「同上，
> 改用閉式…反解」欄，非同表 841 行的最小平方擬合值）一致到四位有效數字，交叉驗證方法正確。

| 音 | MIDI | B（before，閉式） | B（after，閉式） | 倍率 (before/after) | 第2泛音偏離2×整數倍 before (cent) | after (cent) |
|---|---|---|---|---|---|---|
| C2 | 36 | 2.556×10⁻⁵ | 1.846×10⁻³ | 0.014×（**反向增大**，見下方說明） | 0.066 | 4.772 |
| A4 | 69 | 1.361×10⁻³ | 7.082×10⁻⁴ | 1.92× | 3.522 | 1.836 |
| G4 | 67 | 1.080×10⁻³ | 5.574×10⁻⁴ | 1.94× | 2.797 | 1.446 |
| **G5** | 79 | 4.321×10⁻³ | 1.512×10⁻³ | **2.86×** | 11.102 | 3.912 |
| **G6** | 91 | 1.728×10⁻² | 3.737×10⁻³ | **4.63×** | 43.034 | 9.615 |
| D7 | 98 | 3.880×10⁻² | 7.663×10⁻³ | 5.06× | 91.940 | 19.525 |
| C7 | 96 | 3.080×10⁻² | 7.146×10⁻³ | 4.31× | 74.305 | 18.232 |

（cent 欄不受 B 定義修正影響，數字與初版相同；cents 只用 `ratio=f2/2f1`，未經過 B 反解。）

**與 A13/A14 的交叉驗證**：A14 §3.10 記錄「引擎 f₂ 偏離 2×」G5=11.1 cent、G6=43.0 cent
（1.0mm 欄）——本卡獨立重算的 before 欄**逐位吻合**（11.102、43.034）。閉式 B 值本身也對得上
A13 §五獨立複算欄（見上方更正說明），確認本卡的 before 測量方法與既有記錄一致。

**方向判讀**：G5/G6/D7/C7（中高音以上）B 值全部下降 2.86×～5.06×，往真實量測值（A14 §3.10
的 G5=2×10⁻⁴、G6=2×10⁻⁴）收斂——G6 對量測值的偏差倍數從 A14 §3.10 記錄的 87×（精確重算
86.4×，0.8mm 時 55×，本卡用 1.0mm 對應 A14 表中的 87× 那一欄）縮小到約 **18.7×**
（3.737×10⁻³ / 2×10⁻⁴）；G5 對量測值的偏差倍數從 21.6×（A14 表記 21×）縮小到約 **7.6×**
（1.512×10⁻³ / 2×10⁻⁴）。仍未完全消除誤差但方向正確、量級明顯改善。**C2 是例外，B 不減
反增約 72 倍**（1.846×10⁻³ / 2.556×10⁻⁵）——這不是候選修正的缺陷，而是舊公式在低音區
本身更不真實：舊公式 `0.35×2^(-(36-69)/12)` 在 MIDI 36 算出 2.49m 的弦長（比任何真實
立式/平台鋼琴的最長弦還長超過一倍），真實鋼琴低音弦長只有約 0.9m（見
`docs/STRING_SCALE_SOURCES.md` §1 表），縮短的弦配合固定弦徑，非諧性自然比舊公式算出
的「不真實地趨近於零」更高——這正是候選修正要修的問題本身，不是新缺陷。

---

## §3 `absolute_pressure_per_force`（Path B 觀測量）前後對照

同一批 `--dump-modes` 輸出，`acoustic_transfer[i].pressure_per_force_{real,imag}_pa_n`
（1.05m 處，Pa/N）：

### physical_piano.score.json（C4/E4/G4/C5，diameter_mm:1.0）

| 音 | MIDI | mag0 before (Pa/N) | mag0 after | 是否相同 | 全partial RMS before | after | 比值(after/before) | amp 加權 before | after | 比值 |
|---|---|---|---|---|---|---|---|---|---|---|
| C4 | 60 | 2.994288×10⁻¹ | 2.994288×10⁻¹ | **逐位元相同** | 3.834672×10⁻¹ | 3.835684×10⁻¹ | 1.0003 | 1.648219×10⁻¹ | 1.674765×10⁻¹ | 1.0161 |
| E4 | 64 | 2.730752×10⁻¹ | 2.730752×10⁻¹ | **逐位元相同** | 3.096216×10⁻¹ | 3.097128×10⁻¹ | 1.0003 | 1.516477×10⁻¹ | 1.548990×10⁻¹ | 1.0214 |
| G4 | 67 | 2.488891×10⁻¹ | 2.488891×10⁻¹ | **逐位元相同** | 2.644855×10⁻¹ | 2.646469×10⁻¹ | 1.0006 | 1.436352×10⁻¹ | 1.436478×10⁻¹ | 1.0001 |
| C5 | 72 | 2.072562×10⁻¹ | 2.072562×10⁻¹ | **逐位元相同** | 2.077411×10⁻¹ | 2.077134×10⁻¹ | 0.9999 | 9.920217×10⁻² | 9.920206×10⁻² | 1.0000 |

### moonlight_sonata_movement1_yangqin.score.json（6 個抽樣音，涵蓋低/中/高音域）

| 音 (MIDI) | mag0 是否相同 | RMS 比值(after/before) | amp加權估算(略) |
|---|---|---|---|
| 29 (F1附近) | 逐位元相同 | 0.8981 |
| 44 | 逐位元相同 | 0.9795 |
| 56 | 逐位元相同 | 0.9989 |
| 61 | 逐位元相同 | 0.9999 |
| 66 | 逐位元相同 | 1.0000 |
| 87 | 逐位元相同 | 1.0000 |

**發現（比卡文標題重要）**：`absolute_pressure_per_force` 的**基頻分量（partial[0] 的
mag0）在本卡取樣的全部 10 個音符上，before/after 逐位元完全相同**——這個觀測量在
`tuneToMidi=true`（corpus 預設）下只吃「調到目標頻率後的頻率值」，不吃弦長/弦徑本身
（弦長/弦徑只影響調音前的原始頻率與非諧性 B，調音步驟把基頻鎖回 MIDI 目標音高，兩者互相
抵銷）。也就是說：**卡文標題「B 路徑絕對聲壓偏高 2.4～5.2×」這個具體主張，就本卡實際測到
的 `absolute_pressure_per_force` 觀測量而言，找不到支持——這個量根本沒有隨候選修正的弦長/
弦徑改動而改變。** 全partial RMS（不含 amp 加權）與 amp 加權後的估算總壓力的變化幅度依引擎
而異：physical_piano 4 音（C4/E4/G4/C5）都只有 <2.2% 的變化；moonlight yangqin 6 個取樣音裡
midi 56/61/66/87 同樣 <2.2%，但 midi 29 RMS 比值 0.8981（**−10.2%**）、midi 44 RMS 比值 0.9795
（**−2.05%**），變化明顯較大（低音域受弦長/弦徑改動影響較大，見上表）。無論哪個引擎、哪個
取樣音，量級都遠小於卡文標題宣稱的 2.4～5.2 倍。這與 §0 的「卡文標題用詞更正」互相印證。

---

## §4 8 首代表曲位元不變（R10 證據，預期會變）

`reports/gate_outputs/wf0907_method/render_wf_scores.py`（`--cli build-wf\...`）：

| 曲目 | before sha256（前16位） | after sha256（前16位） | 是否相同 | 引擎 |
|---|---|---|---|---|
| moonlight_sonata_movement1_yangqin | 49514b007e3e01fc | 01849a9de6884ef2 | **不同** | cimbalom（受影響） |
| moonlight_sonata_movement1_yangqin_tongue_mix | 280cbdac3c117c14 | baa56ebe022bcc4f | **不同** | cimbalom+tongue_drum 混合（受影響部分） |
| physical_piano | 1233b53f1e8660bc | b1f0b58a65c892d2 | **不同** | piano（受影響） |
| restraint_metal_click | be634798c4a0bf71 | 9759a47e28ca09e3 | **不同** | string（受影響） |
| moonlight_sonata_movement1_tongue_drum | f539aefa91919cbf | f539aefa91919cbf | 相同 | tongue_drum（不受影響，BeamModel） |
| water_gong_free | 31b539c6ac08d942 | 31b539c6ac08d942 | 相同 | water_gong（不受影響，PlateModel） |
| ai_radiance_m1 | 74122637a0c71278 | 9812a5ac2ca7d8d9 | **不同** | cimbalom 混合（受影響部分） |
| fur_elise_opening | b0877774da9e5fc5 | b0877774da9e5fc5 | 相同 | fm（不受影響，FMPianoEngine 不用 StringModel） |

**5/8 CHANGED、3/8 IDENTICAL**——完全符合預期：只有 string/cimbalom/piano 引擎路徑
（走 `StringModel::lengthFromMidiNote`）受影響，tongue_drum/water_gong（`BeamModel`/
`PlateModel`）與 fm（`FMPianoEngine`）三首逐位元不變，證明候選修正的影響範圍精準侷限在
`CimbalomEngine.h` 三個呼叫點，沒有外溢到其他引擎。**這正是 R10 預期的結果，不是意外。**

證據：`reports/gate_outputs/wf0914_D11_sha256_baseline_current_tree.txt`（本卡自建 before
基線）、`reports/gate_outputs/wf0907_method/sha256_wf0914_D11_after.txt`（after）。

---

## §5 GATE：`physics_verify.py --full`（誠實回報一項未解 FAIL）

### 5.1 先修：`stiff_string_oracle()` 需要同步鏡射候選公式

`tools/physics_verify.py::stiff_string_oracle()` 的文件字串明寫它是「獨立 Python 鏡射，
用來檢查 C++ dump source 有沒有漂移」，但它硬寫了**舊公式**（`0.35*2^(-(midi-69)/12)` +
`diameter_mm` 直讀）。改了 C++ 端的公式後，這個獨立鏡射理所當然會回報「漂移」——這不是
候選修正的缺陷，是鏡射腳本沒跟著改。本卡在 `tools/physics_verify.py` 裡同步鏡射了候選
公式（新增段落明確標註「WF0914-D11 候選修正，patch 未落地」），修正後 `1b note-range scan`
與所有 `oracle: ... [OK]` 全部恢復 PASS（見 `reports/gate_outputs/wf0914_D11_physics_verify_full.txt`
第一輪 FAIL 存檔於 `output/wf0914/D11/physics_verify_full_after.txt` 供比對，同步前
`stiff-string oracle max error` 共 10 個 FAIL（[OK] 僅 1 條），值域 0.1237%～13.7101%）。

### 5.2 未解決的 FAIL：F5 殘餘能量（piano）

同步 oracle 後重跑，`--full` 結果：

```
F1 eigenvalue anchors: PASS
1b note-range scan   : PASS   <- 5.1 修好後恢復 PASS
1c material sensitivity: CHECKED CASES PASS; 3 UNVERIFIED/N/A （既有 3 筆 rubber UNVERIFIED，非本卡新增）
1d velocity judgment : PASS
2d amplitude judgment: PASS
5b measured T60       : PASS
F5 residual energy   : FAIL (limit -60.0 dB re total; see lines above)
   cimbalom    residual: -62.3 dB -> PASS
   tongue_drum residual: -75.9 dB -> PASS
   water_gong  residual: -72.7 dB -> PASS
   water_gong_free residual: -77.9 dB -> PASS
   piano       residual: -58.5 dB re total (120 predicted modes, limit -60.0 dB) -> FAIL
RESULT: SOME CHECKS FAILED
```

**與歷史基線對照**（同一個 F5 piano residual 檢查，過去三次記錄）：

| 記錄來源 | piano F5 residual | 判定 |
|---|---|---|
| `reports/gate_outputs/b4_gate_full.txt`（B4，2026-08-27） | −64.4 dB | PASS |
| `reports/gate_outputs/wf0908_P2_tauc_physics_verify_full.txt`（A14 B-2） | −63.9 dB | PASS |
| `reports/gate_outputs/wf0910_A14_apply.txt`（A14 落地後） | −63.9 dB | PASS |
| **本卡候選修正（after）** | **−58.5 dB** | **FAIL** |

**誠實聲明：本卡未查出這個 5.4~5.9 dB 劣化的根因。** 已排除的可能：
- 不是 oracle 過期造成的假訊號（§5.1 修好 oracle 後這個 FAIL 依然存在，數字完全沒變）。
- 不是既有 3 筆 rubber UNVERIFIED 範圍的問題（那三筆在「Unverified ranges」單獨列出，
  與 F5 piano residual 是兩個不同的檢查）。
- MIDI 60 剛好落在候選弦長表的 C4 錨點（60），弦長從舊公式 0.5886m 變成新表 0.639m
  （**弦徑同樣隨表變動，不是只有弦長改變**——A4（MIDI 69）本身並非候選弦長表的錨點
  （錨點固定在 C1–C8 對應的 MIDI 24/36/48/60/72/84/96/108），A4 的 L/d 由 C4（60）／
  C5（72）兩個錨點內插而來、同樣被改動：L 從舊公式 0.35m 變成 0.40275m、d 從 corpus
  固定值 1.0mm 變成內插值 0.955mm，對應 §2 表列 A4 的 B before/after 比值 1.92×
  （稽核另用 B∝d²/L⁴ 的比例關係反推，與此比值吻合）——沒有任何一個音「兩個公式碰巧完全
  相同」）；
  懷疑與此有關，但本卡未進一步用時域/頻域拆解去定位到底是哪個機制（多弦 beating 邊帶、
  是否某個 partial 的實際渲染頻率因 B 改變而滑出 ±3% 判定窗、或其他）產生了增加的殘餘能量。
  這個根因調查超出本卡「候選修正示範 + 前後對照」的範圍，需要另立卡處理或由月月裁決
  是否值得繼續查。

**這個 FAIL 對月月裁決的意義**：候選修正在「非諧性 B 準確度」上有清楚、可信、方向正確的
改善（§2），但同時讓 `--full` 的一項既有自我一致性 GATE 從穩定 PASS 退化成 FAIL。**本卡不
建議在這個 FAIL 根因未查清前直接採納這版候選修正**——這正是為什麼本卡的合法終點是
BLOCKED(R10) 而非「建議直接落地」。

完整輸出：`reports/gate_outputs/wf0914_D11_physics_verify_full.txt`（含 oracle 修好後的完整
`--full` 輸出）；oracle 修好前的第一輪（含 10 個 stiff-string oracle max error FAIL、另有 1 條 count 不符的 FAIL + 同一個 F5 FAIL）
存檔 `output/wf0914/D11/physics_verify_full_after.txt`（未進版控，供工兵/稽核核對用）。

### 5.3 ctest / pytest

- `ctest --test-dir build-wf -C Release`：**4/4 Passed**（候選修正建置後；含既有
  `physics_models_repro` 測試，沒有任何測試假設舊的 `lengthFromMidiNote()`/固定弦徑行為，
  因此候選修正沒有讓既有單元測試變紅）。證據：`output/wf0914/D11/ctest_final.txt`。
- `python -m pytest tests -q`：**264 passed, 1 skipped, 5 xfailed**（候選修正建置後，含
  `tools/physics_verify.py` 的候選修正）。證據：`output/wf0914/D11/pytest_final.txt`。

---

## §6 before 基線 vs 官方 `sha256_before_post_a14.txt`（2026-09-15 修訂，稽核 finding 3）

> **更正**：本節初版聲稱「對當下工作樹重新渲染 8 首，只有 2 首與官方舊基準
> `sha256_before_post_a14.txt` 不同」——這個說法**查無此事**，是誤判，已撤回。

實測結果（逐位元比對，忽略換行符號）：`reports/gate_outputs/wf0914_D11_sha256_baseline_current_tree.txt`
（本卡自建 before 基線）與 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`
（README 記錄的官方基準）**8/8 sha256 逐位元相同**——唯一差異是純文字檔的換行符號
（CRLF vs LF；968 bytes vs 976 bytes，內容 0 差異）。獨立驗證命令：

```
$ diff <(tr -d '\r' < reports/gate_outputs/wf0914_D11_sha256_baseline_current_tree.txt) \
       <(tr -d '\r' < reports/gate_outputs/b6_method/sha256_before_post_a14.txt)
(no output — 逐位元相同)
```

另有稽核獨立重建 `build-wf` 全部 target 後重跑 `render_wf_scores.py` 產生的
`reports/gate_outputs/wf0907_method/sha256_audit_d11_opus.txt`，同樣與官方基準
**8/8 IDENTICAL**（`49514b…`／`280cbd…`／`1233b5…`／`be6347…`／`f539ae…`／`31b539…`／
`741226…`／`b08777…` 全部逐位元相同），與本卡自建基線互相印證。

**結論**：本卡開工時的工作樹（含 B7P0/B7P1/B7P3/D12 等既有未 commit 修改）在渲染輸出層級
**與官方基準完全一致**，沒有先前其他卡造成的位元漂移。本卡另建
`sha256_baseline_current_tree.txt` 這個檔案本身沒有問題（確保單一變數比較的習慣做法），
但初版報告據此推導出的「建議整合卡重新校準官方基準」是基於一個不存在的量測結果，
**已在 open_items 撤回**；官方基準不需要因為 D11 重新校準。

---

## §7 影響範圍確認（只有 3 個呼叫點，且只在 CimbalomEngine 內）

`grep -rn "lengthFromMidiNote" src/` 顯示**全 repo 只有 `CimbalomEngine.h` 三處呼叫**
`StringModel::lengthFromMidiNote()`（`startNote()`／`noteOn()`／`worstCaseTailSeconds()`）；
`BeamModel.h` 有自己獨立的同名函式（`lengthFromMidiNote(note, referenceLength=0.12f)`），
被 `ChromaticEngine.h`（tongue_drum/water_gong）呼叫，**與本卡完全無關、本卡沒有改動**。
`tests/physics_models_repro.cpp` 沒有任何測試直接呼叫 `lengthFromMidiNote`/`tensionForNote`，
候選修正不會讓既有單元測試變紅（§5.3 已驗證）。

---

## §8 GATE 完成狀態

| GATE | 結果 | 證據 |
|---|---|---|
| Phase A 溯源 | 命中既有 repo 引用鏈，無需新 fetch | `docs/STRING_SCALE_SOURCES.md` |
| 候選修正實作 + 三 build target | CLI/Standalone/VST3 全部 exit 0 | 本次會話建置輸出（未存檔，純建置日誌） |
| 五測試 target + ctest | **4/4 Passed** | `output/wf0914/D11/ctest_final.txt` |
| `physics_verify.py --full` | **SOME CHECKS FAILED**（F5 piano residual −58.5dB，見 §5.2，未查出根因） | `reports/gate_outputs/wf0914_D11_physics_verify_full.txt` |
| `pytest tests -q` | **264 passed, 1 skipped, 5 xfailed** | `output/wf0914/D11/pytest_final.txt` |
| 8 首位元基準 | 5/8 CHANGED（string/cimbalom/piano）＋3/8 IDENTICAL（非 StringModel 引擎）——符合預期 | §4 |
| 非諧性 B 前後對照（閉式定義，2026-09-15 修正） | G5/G6/D7/C7 全部改善 2.86×～5.06×；與 A13/A14 逐位交叉驗證吻合 | §2 |
| `absolute_pressure_per_force` 前後對照 | 全部取樣音符 mag0 逐位元相同；卡文標題「2.4～5.2×」找不到支持 | §3 |
| before 基線 vs 官方 `sha256_before_post_a14.txt`（2026-09-15 修正） | **8/8 逐位元相同**（差異只有 CRLF/LF），初版「2/8 首不同」的說法已撤回 | §6、`reports/gate_outputs/wf0914_D11_sha256_baseline_vs_official_diff.txt` |
| `git diff -- src/ tools/ tests/` 交付時為空（本卡三檔） | **0 行差異**（`git status --porcelain` 只剩其他卡既有的 `PluginProcessor.cpp/h`／`HammerImpulse.h`／`RadiationModel.h`／`ScoreRenderer.h`／`host_probe.cpp`／`physics_models_repro.cpp`／`test_measurement_selfcal.py`／`measurement_selfcal.py`／`stem_verify.py`，皆非本卡改動） | `reports/gate_outputs/wf0914_D11_revert_verify.txt` |
| patch `git apply --check` | **通過（exit=0）**，patch 內死連結（finding 4）已修正並重新驗證 | 同上 |
| 裁決包（`WF0914_README.md` §2.4 體例） | 已補齊 | `reports/decision_packets/D11_string_scale_candidate.zh-TW.md` |

---

## §9 patch 化與工作樹還原（待稽核親自複核）

```
git diff -- src/physics/StringModel.h src/engines/CimbalomEngine.h tools/physics_verify.py \
    > reports/d11_string_scale_candidate.patch
```

> **2026-09-15 修訂（稽核 finding 4）**：初版 patch 在 `src/physics/StringModel.h` 新增的
> 註解裡寫「由月月裁決（`docs/d11_string_scale_before_after.md`）」——這個路徑不存在
> （報告實際存在 `reports/` 下，`docs/` 沒有這個檔）。修法：`git apply` 把候選碼帶回工作樹、
> 把註解路徑改成 `reports/d11_string_scale_before_after.md`、重新
> `git diff -- src/physics/StringModel.h src/engines/CimbalomEngine.h tools/physics_verify.py
> > reports/d11_string_scale_candidate.patch` 覆寫 patch 檔，再依下方同一套還原流程把工作樹
> 還原乾淨。`tools/physics_verify.py` 的候選段落本身未動，只有 `StringModel.h` 的註解文字
> 改了一個字串。還原後重新驗證 `git diff`／`git apply --check` 皆通過（見下方輸出，
> 已重新執行並更新 `reports/gate_outputs/wf0914_D11_revert_verify.txt`）。這個修法不影響
> 任何程式邏輯（只改一行註解裡的文件路徑），不需要重新建置/重跑 ctest/pytest/8首位元基準。

還原方式：`cp output/wf0914/D11/backup/StringModel.h.orig src/physics/StringModel.h`、
`cp output/wf0914/D11/backup/CimbalomEngine.h.orig src/engines/CimbalomEngine.h`（**檔案複製
還原，不用 `git checkout`/`stash`，R7 合規**）；`tools/physics_verify.py` 沒有另存 backup
副本（本檔案是實作中途才決定touch，見 §5.1），改用編輯器直接把新增的 D11 段落換回原本
兩行（`diameter = float(params.get("diameter_mm", 0.8)) * 0.001`／
`length = 0.35 * 2.0 ** (-(midi - 69) / 12.0)`），與 patch 檔內容逐字比對一致。

**實際執行結果**（`reports/gate_outputs/wf0914_D11_revert_verify.txt` 完整輸出）：

```
$ git diff -- src/physics/StringModel.h src/engines/CimbalomEngine.h tools/physics_verify.py | wc -l
0
$ git apply --check reports/d11_string_scale_candidate.patch
exit=0
```

`git status --porcelain -- src/ tools/ tests/` 還原後只剩其他 WF0914 卡（B7P0/B7P1/D12 等）
既有、非本卡改動的檔案（`PluginProcessor.cpp/h`、`HammerImpulse.h`、`RadiationModel.h`、
`ScoreRenderer.h`、`host_probe.cpp`、`physics_models_repro.cpp`、`test_measurement_selfcal.py`、
`measurement_selfcal.py`、`stem_verify.py`）——本卡三個檔案（`StringModel.h`／
`CimbalomEngine.h`／`tools/physics_verify.py`）**逐位元回到開工前狀態，未落地**，改動完整
保存在 `reports/d11_string_scale_candidate.patch`（sha256 見交付時的 `git add` 前稽核複核）。

**還原後再重建 `build-wf`（CLI/Standalone/VST3 + 5 測試 target）＋ ctest ＋ 重跑 8 首位元基準**
（比對本卡開工前自建的基線 `sha256_wf0914_D11_baseline.txt`）：

```
ctest: 100% tests passed, 0 tests failed out of 4
8/8 IDENTICAL（moonlight_sonata_movement1_yangqin、..._tongue_mix、physical_piano、
  restraint_metal_click、..._tongue_drum、water_gong_free、ai_radiance_m1、fur_elise_opening
  全部 sha256 與開工前基線逐位元相同）
```

**這證明候選修正的還原是乾淨、可逆、位元級完整的**——不只是原始碼文字層級的 diff 為零，
連實際渲染出的音訊也回到與開工前逐位元相同的狀態。完整輸出：
`reports/gate_outputs/wf0914_D11_revert_verify.txt`、
`reports/gate_outputs/wf0914_D11_sha256_postrevert.txt`。
