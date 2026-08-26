# B3 Rule 10 前後對照 — 方法腳本與 before 基線資料

> 產出：2026-08-24（B3 開工前 before 採樣，工作樹 = B1+B2 落地後、B3 未動）
> 對應施工卡：`docs/workcards/B3.md` §9（Rule 10 報告的前後對照資料）
> 方法學前例：`reports/b1_b2_bridge_damping_before_after.md`（B2 報告）

此目錄的三個腳本在 **before**（B3 改動前）與 **after**（B3 改動後）各跑一次，
同一支腳本、同一組參數，只換 `--label`。after 階段的工兵直接照下面命令原樣重跑
即可產生 after 資料。所有命令都從 repo 根目錄執行，前提是 CLI 已重建
（`build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`）。

---

## 1. `t60_material_grid.py` — T60 材質×音高對照基線

對應 B3 卡 §9 第 2 項（steel/aluminum/rubber × C2/C4/C6/C8 T60 對照表）。

**方法**（與 B2 報告 §1 同法）：單事件 probe score（cimbalom、velocity 0.5、
錨點慣例參數 diameter 0.8 mm / strike 0.3 / wood_mallet、效果器全關、無 macro）
餵 `TsukiSynthCLI --dump-modes`，讀**中央弦**（3 弦 course 中基頻最接近該 MIDI
音平均律頻率者，freqMul=1）**第一泛音（基頻模態）的 decay 欄位** = 模型 T60。
probe score 寫到系統暫存目錄，不進 repo。

```
python reports/gate_outputs/b3_method/t60_material_grid.py --label before
python reports/gate_outputs/b3_method/t60_material_grid.py --label after
```

輸出：`t60_material_grid_<label>.csv`
（欄位 material, note_name, midi, nominal_hz, center_string_f0_hz, t60_s）

**方法驗證**：before 跑出的 steel 欄 = 17.655 / 4.2969 / 0.97137 / 0.1756 s
（C2/C4/C6/C8），與 B2 報告 §1「B1+B2 疊加後」欄（17.66 / 4.30 / 0.97 / 0.18）
一致 → 與 B2 同一把尺。

## 2. `render_rep_pieces.py` — 六首代表曲整曲渲染指標

對應 B3 卡 §9 第 5 項。六首 = B2 報告 §4 同一組
（vivaldi_summer_m2 / vivaldi_summer_m3 / moonlight_yangqin /
akashic_opening_bell / ai_radiance_m1 / vivaldi_autumn_m2）。

注意：`akashic_opening_bell` 實際上只有 tongue_drum/water_gong 事件（無弦），
B3 之後它的 WAV **應該逐位元不變**——它是 after 對照時的 null 哨兵，不是弦樣本。

**方法**：現行 CLI 渲染到 **repo 外**的工作目錄（腳本強制檢查），每首記錄：
- 整曲 RMS（dBFS）：聲道平均混單聲道後 `20·log10(RMS)`（與
  `reports/phase_h_before_after/analyze.py` 同一讀檔/混音慣例）；
- 整曲頻譜質心（Hz）：整段 mono 訊號一次 rfft 的振幅加權平均頻率（無窗）；
- WAV SHA256（B3 卡 §9 第 7 項決定性聲明所需）。

```
python reports/gate_outputs/b3_method/render_rep_pieces.py --label before --workdir <repo外目錄>
python reports/gate_outputs/b3_method/render_rep_pieces.py --label after  --workdir <repo外另一目錄>
```

輸出：`rep_pieces_<label>.csv`
（欄位 piece, score_path, wav, len_s, rms_dbfs, centroid_hz, sha256）

質心定義註記：B2 報告 §4 的質心欄未留腳本，本目錄的定義（整曲無窗 rfft
振幅加權）為 before/after 自我一致的基準；跨報告比較請只比本目錄 before vs
after，不要拿 B2 報告的質心數字直接對減。

## 3. `damping_override_anchor.py` — damping_override 清單 + MIDI 60 錨點 T60

對應 B3 卡 §9 第 6 項（錨點保證變化聲明的數據來源）。

**方法**：掃 `scores/**/*.score.json` 的 `track_profiles` 與 event `params`
找出所有 `damping_override` 出現處，去重出「影響模態的參數組合」
（engine, material, diameter_mm, tension_n, num_strings, detuning_cents,
damping_override），每組合建 MIDI 60、velocity 0.5 的 probe score，
`--dump-modes` 讀中央弦基頻 T60（同第 1 節的讀法；strike/exciter 固定為
錨點慣例 0.3/wood_mallet，二者不進阻尼律）。

```
python reports/gate_outputs/b3_method/damping_override_anchor.py --label before
python reports/gate_outputs/b3_method/damping_override_anchor.py --label after
```

輸出：
- `damping_override_anchor_<label>.csv` — 每唯一組合一列（36 組）；
- `damping_override_files_<label>.md` — 30 個 score 檔的清單與檔→組合對映。

**「32 首」對帳**：施工卡與 B2 報告寫「32 首」，來源是
`grep -rl damping_override scores/` = 32 個檔——其中 2 個不是樂譜
（`scores/schema/score.schema.json`、`scores/originals/rules_v2_demo/README.md`）。
實際使用 `damping_override` 的 `*.score.json` 是 **30 首**（本腳本逐檔
解析 JSON 認定，見 md 清單）。

**null 哨兵**：組合表裡有一組 `plate`/bronze/`damping_override: null`
（akashic_bell 等），走 PlateModel——B3 不准動 Beam/Plate，這組的 after
T60 必須與 before **完全相同**（before = 7.4864 s），可當範圍隔離的檢查點。

---

## before 資料檔（本次已產出）

| 檔案 | 內容 |
|---|---|
| `t60_material_grid_before.csv` | 3 材質 × 4 音的模型 T60 |
| `rep_pieces_before.csv` | 六首整曲 RMS/質心/SHA256 |
| `damping_override_anchor_before.csv` | 36 組唯一組合的 MIDI 60 錨點 T60 |
| `damping_override_files_before.md` | 30 首 damping_override 樂譜清單＋對映 |

after 階段：跑完三支腳本後，把 `*_after.*` 與 `*_before.*` 逐欄對減即為
Rule 10 報告 §9 第 2/5/6 項的素材。
