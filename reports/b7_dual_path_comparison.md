# B7 Phase 3：雙路徑（Path B vs Path C）一致性檢查 —— 本輪無法執行

> 工作卡：`docs/workcards/WF0914_B7P3_dual_path.md`（B7.md §6 步驟 11）
> 日期：2026-09-14　branch `fix/deep-physics-audit-20260716`　HEAD `a38bd6a2`（本卡未 commit）
> **結論先講**：本卡 §1 要求的「同一份 `--dump-modes` JSON 讀出 Path B `absolute_pressure_per_force`
> / `acoustic_transfer[]` 與 Path C 對應欄位」**做不到**——Path C（`absolute_pressure_per_force_firstprinciples_c`
> / `bridge_power_firstprinciples_c` / `acoustic_transfer_c[]`）**目前完全不存在於 `dumpModes()` 輸出**，
> 不是「差異很大」而是「根本沒有第二條路徑可比」。這是 WF0914-B7P1 稽核修復回合已經落地的既有事實
> （`reports/gate_outputs/wf0914_B7P1_auditfix_summary.txt` 第 3 點、`ROADMAP_PHYSICS.md` B7 條目
> 「B7P1 稽核修復」段），本卡只是照施工卡 §1 步驟實際去讀 JSON，親眼確認並記錄下來，**沒有新開工**、
> **沒有碰 `src/`**。

---

## §1 施工卡文字與 repo 現況的矛盾

`docs/workcards/WF0914_B7P3_dual_path.md` §1 步驟 2 寫「同一份 JSON 讀出 Path B
`"absolute_pressure_per_force"` / `acoustic_transfer[]` 與 Path C 對應欄位」，隱含前提是
「B7P1 已經把 Path C 兩個欄位接進 `dumpModes()`」。本卡 §0 也說「前置：WF0914-B7P1 已 PASS」。

但 `B7P1 已 PASS`（稽核 GATE 全綠、audit-fix 回合結束）**不等於**「Path C 有資料可比」——
稽核修復回合的第 3 點明講：

> 「§1.1 velocity-proxy-to-MIDI decision re-examined -- audit's BLOCKED claim CONFIRMED
> ... the "bridge_power_firstprinciples_c" dumpModes() field has been withdrawn
> (ScoreRenderer.h) pending 月月's decision on §1.1.」
> （`reports/gate_outputs/wf0914_B7P1_auditfix_summary.txt`）

也就是說：B7P1「PASS」的是「GATE 全綠、修復了稽核抓到的兩個真實缺陷（能量守恆違反 + 非守恆哨兵）」，
但同一回合裡，Path C 唯一還會被 `dumpModes()` 輸出的欄位（`bridge_power_firstprinciples_c`，
§1.2「否」分支下的力鏈中繼終點）也在**同一次修復**中被撤回，因為它依賴的 §1.1 proxy×127 代決
被證明是錯的（`tools/midi_to_tsukisynth.py::velocity_for()` 的實際算式是
`base_velocity(role,0.42–0.72) × (source_velocity/90.0)`，從未是 `MIDI/127`、也不與 MIDI 成比例）。

**兩層缺口疊加**：
1. §1.2 查證結果是「否」分支——`S`（音板輻射面積）維持 `UNVERIFIED`，`RadiationModel.h`
   本來就沒有 `soundboardRadiatingAreaM2()` / `pressureAtDistanceFirstPrinciples()`，
   所以就算 §1.1 沒出事，力鏈本來就只會走到 `W_bridge(f)`（`bridge_power_firstprinciples_c`），
   走不到「1.05 m 處 Pa」——即本卡 §1 原本要比的 `absolute_pressure_per_force_firstprinciples_c`
   從一開始就不會存在。
2. §1.1 事後被判 BLOCKED——連退而求其次的 `bridge_power_firstprinciples_c` 這個中繼欄位，
   也在 B7P1 稽核修復回合被撤回，**現在的 `dumpModes()` 完全不輸出任何 Path C 相關鍵**。

依 `WF0914_README.md` §2 第 5 點與 `WF0907_README.md`「WF0908-P4 教訓：卡文可能錯」：
**卡文與 repo 現況矛盾 → 停下，寫進 open_items 回報，不要硬做**。本卡 §1（雙路徑比對）在此停下，
不編造比對數字、不自行重新裁決 §1.1、不修改 `src/`（超出本卡「只跑既有 build-wf 產物與 Python
工具」的 lane 範圍）。

---

## §2 親眼驗證（實際跑 `--dump-modes`，非只讀程式碼）

命令與輸出：

```
$ ./build-wf/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe --dump-modes \
    scores/examples/physical_piano.score.json > output/wf0914/B7P3/probe_physical_piano_dumpmodes.json
exit=0
```

（`scores/examples/physical_piano.score.json`：engine=piano、C4/E4/G4/C5，material=steel——
現成 corpus score，僅用於探測目前 `dumpModes()` 實際輸出哪些鍵，不是本卡步驟 1 要求的
C2/C4/C7 × MIDI 40/77/108 測試矩陣本身，因為根本沒有 Path C 欄位可比，矩陣本身無意義去建。）

```python
>>> d = json.load(open("output/wf0914/B7P3/probe_physical_piano_dumpmodes.json", encoding="utf-8"))
>>> d["model_observables"]
['modal_frequency_hz', 'relative_modal_amplitude', 'modal_t60_s', 'radiated_power_relative', 'absolute_pressure_per_force']
>>> ev0 = d["events"][0]
>>> list(ev0.keys())
['source_index', 'engine', 'note', 'midi', 'frequency_mode', 'partials', 'strings', 'acoustic_transfer']
>>> list(ev0["partials"][0].keys())
['freq', 'amp', 'decay', 'body_mag', 'radiated_power_relative']
>>> list(ev0["acoustic_transfer"][0].keys())
['model_partial_index', 'radius_m', 'azimuth_deg', 'elevation_deg', 'pressure_per_force_real_pa_n', 'pressure_per_force_imag_pa_n']
```

**`model_observables` 裡沒有 `absolute_pressure_per_force_firstprinciples_c`、也沒有
`bridge_power_firstprinciples_c`；事件層級沒有 `acoustic_transfer_c` 鍵；partial 層級沒有任何
`_c` 後綴欄位。** `grep -c "firstprinciples_c\|bridge_power" output/wf0914/B7P3/probe_physical_piano_dumpmodes.json`
回傳 `0`。Path B 的兩個欄位（`absolute_pressure_per_force`、`acoustic_transfer[]`）如常存在——
這條路徑本身沒有問題，問題只在「沒有第二條路徑」。

原始檔案：`output/wf0914/B7P3/probe_physical_piano_dumpmodes.json`（未進版控，gitignored）。

`src/score/ScoreRenderer.h` 對應的程式碼位置（`git diff` 為空，本卡未動這個檔案，純讀）：

- L224–266：B7P1 稽核修復回合留下的完整 BLOCKED 說明註解（在迴圈頂端，`radiationFc`/
  `radiationFga` 宣告之前）。
- L333–335：piano/cimbalom/string 分支裡，原本要呼叫 Path C 組裝函式的位置現在只留一句
  「B7 Phase 1 Path C wiring removed here」的註解。
- L466–469：`modeToJson()` 裡原本要 emit `bridge_power_firstprinciples_c` 的位置，現在只留
  「emission removed here」的註解，`s << "}"` 直接收尾。

`src/physics/RadiationModel.h` L342–361：class 級註解明講 §1.2 走「否」分支，**這個檔案刻意
沒有** `soundboardRadiatingAreaM2()` 或 `pressureAtDistanceFirstPrinciples()`，力鏈停在
`bridgePowerFirstPrinciples()`（`W_bridge(f)`，informational endpoint）。

---

## §3 本卡能做、且已經做的事

- 確認了「B7P1 已 PASS」與「Path C 有資料可比」是兩件不同的事——不硬套施工卡字面指示去
  比對不存在的欄位。
- 用實際 CLI 執行結果（而非只讀程式碼）佐證這個結論，避免「程式碼看起來這樣寫，但沒有真的跑」
  的落差。
- 沒有嘗試自行裁決 §1.1（proxy 換算）、沒有嘗試重新接回 Path C 欄位、沒有改動任何 `src/` 檔案、
  沒有改動 `HammerImpulse.h` / `RadiationModel.h` / `ScoreRenderer.h`。
- §2 的裁決包（`reports/decision_packets/B7_phase2_and_open_items.zh-TW.md`）把這個事實與
  Phase 2 甲/乙案一起整理給月月，供她裁決 §1.1 之後，本卡的雙路徑比對才有辦法重新執行。

## §4 本卡做不到的事（誠實列出，不強行湊數字）

- **無法產出「逐 partial 與總量的實際差異倍率（C/B）」數字表**——沒有 Path C 的數字，除以
  Path B 的數字沒有意義；不會用「假設一個 S/假設一個 proxy 規則」去湊出一組數字再標
  「僅供參考」，那違反 Rule 4（未溯源常數）且會誤導月月的裁決基礎。
- **無法對「差異主要來自哪個環節」做歸因分析**——沒有實測差異可歸因。
- B7.md §8「驗收基準 (b)」在此仍是「待 Path C 重新接回後才能執行」的狀態，不是本卡本輪能
  推進的項目。

## §5 要恢復本卡可執行狀態，需要什麼

月月對 `docs/workcards/WF0914_B7P1_force_chain.md` §1.1 做出裁決（score `velocity` proxy 該如何
合法轉換成真實 MIDI/槌速）之後，才有一條合法的 Path C 輸入來源，Path C 欄位才可能被重新接回
`dumpModes()`（需要另立一張工兵卡，不是本卡份內）；接回之後，本卡 §1 的步驟 1–4 才有東西可執行。
`S`（§1.2）已經走完「否」分支查證，維持 `UNVERIFIED` 是本輪既定事實，不是待辦。
