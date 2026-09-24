# B7 Phase 2/3 裁決包：驗收基準 (a) 甲/乙案 + §1.1/§1.2 落地事實 + 雙路徑現況

> 工作卡：`docs/workcards/WF0914_B7P3_dual_path.md`
> 日期：2026-09-14　branch `fix/deep-physics-audit-20260716`　HEAD `a38bd6a2`（本卡未 commit）
> 依據：`docs/workcards/B7.md` §6 Phase 2/3、§8（甲/乙兩案原文）、§12；
> `docs/workcards/WF0914_B7P1_force_chain.md` §1.1/§1.2；
> `reports/gate_outputs/wf0914_B7P1_auditfix_summary.txt`；
> `reports/b7_dual_path_comparison.md`（本卡同一輪產出，§1 雙路徑比對本身做不到的完整說明）。
> **體例照 `reports/decision_packets/K02_reverb_wet_scale.zh-TW.md`**：選項並列、代價寫清楚、
> **不替月月選**。

---

## §0 一句話現況

B7P1 這一輪落地後，Path C（第一原理力鏈）在 `dumpModes()` 裡**沒有任何輸出**——不是「差一點」，
是**完全沒有**。原因是兩層查證都走到「查無/矛盾」：§1.2（音板面積 `S` 的溯源）走「否」分支，
力鏈本來就只到 `W_bridge(f)` 為止；§1.1（velocity proxy→MIDI 換算）事後被稽核挑戰並確認錯誤
（BLOCKED），連 `W_bridge(f)` 這個退而求其次的中繼輸出也被撤回。**本卡要做的 Phase 3 雙路徑比對
（B7.md §6 步驟 11）因此無法執行**（詳細證據見 `reports/b7_dual_path_comparison.md`）。
以下 §1–§4 把這個現況連同 Phase 2 甲/乙案一起整理給月月，四節都「看數字就能選，不替月月選」。

---

## §1 驗收基準 (a) 甲/乙案（B7.md §8 開頭原文轉寫 + 本輪新事實）

### 原文轉寫（`docs/workcards/B7.md` §8，一字不改，僅轉表格）

原本 §6 Phase 2 的驗收基準 (a) 是「1 m 處 pp ≈ 60 dB SPL、ff ≈ 100 dB SPL」。Phase 0 連查五輪的
結論是：這兩個數字目前拿不到出處（`docs/B7_PHASE0_DATA.zh-TW.md` §5 缺口 1：所有絕對量測都在
**距弦 10 cm**，最接近 1 m 的那一組——Goebl 博士論文 Fig. 2.20，ORTF 對、距弦約 1.5 m——**縱軸是
相對 dB**；且 DPA 的量測文章明說鋼琴要 **>5 m** 才能當點聲源，近場不能用 6 dB/倍距外推）。

| 案 | 驗收基準 (a) 怎麼寫 | 代價／前提 |
|---|---|---|
| **案 甲：分音域相對動態範圍 GATE（待月月核）** | 不驗「1 m 處幾分貝」，改驗「**同一顆音**從指定最小力度到最大力度差幾 dB」，且**必須分音域各寫一條**（C2／C4／C7 實測差 10.6 dB） | **必須先訂死下限 velocity 並寫明理由**（0.01→67.4／0.02→60.1／0.05→51.9 dB，下限一換數字全變）。**門檻數字由月月／規劃者裁決，本卡不自訂**（Rule 2）。文獻的 60.4 dB 是「不同鍵＋不同觸鍵法」的合成極值，與引擎「同一顆音」的範圍本質不對等，不能直接對齊 |
| **案 乙：標「絕對 SPL 出處阻塞」，Phase 2 不做** | 驗收基準 (a) 標記為 **BLOCKED（來源缺口）**，本卡只做到 Phase 1／Phase 3，B7 §0 的「一路推到真實 Pa」誠實記為完成一半 | 力鏈的最後一段不接通；但這是 §12 明列的合法完成路徑。要解除阻塞需要月月出手的三條管道：向 Goebl 本人索取 Fig. 2.20 的絕對校準值／用機構帳號取 Roginska et al. 2013 POMA 全文／借閱 Meyer 的動態範圍表 |

### 本輪新事實（B7P1 實際落地到哪）

**甲/乙兩案都不需要 Path C 資料**——甲案量的是引擎本身的渲染輸出動態範圍（`pre_normalize_peak`），
乙案是直接標阻塞，兩者都與本輪 Path C 是否可用**無關**。所以本輪 Path C 完全空缺這件事，
**不影響甲/乙案本身的可選性**，兩案依然都是合法選項。但它確實影響「選了之後 B7 卡整體能走多遠」：

- 若選**甲案**：可以獨立於 Path C 現況直接執行（渲染既有 corpus 或新測試音，讀
  `pre_normalize_peak`，分音域比對），**門檻仍待月月／規劃者裁決**（本卡不自訂，Rule 2）。
- 若選**乙案**：驗收基準 (a) 直接標 BLOCKED；驗收基準 (b)（雙路徑比對，本卡§6步驟11標的物）
  **現階段無論如何都執行不了**（見 §4），所以乙案某種意義上更貼近本輪的真實進度——(a)(b)
  兩條基準本輪都卡住，只有 §4.2–4.4（槌速映射、Hertz 峰值力、`W_bridge`）這段純函式落地
  且測試通過，尚未接進任何可觀測輸出。

**本卡不替月月選甲或乙**——上面只是把「選哪案對本輪現況有什麼影響」攤開。

---

## §2 `S`（音板輻射面積）的採用記錄——B7P1 §1.2

**走的分支**：「否」（`docs/workcards/WF0914_B7P1_force_chain.md` §1.2）。

**判定證據**（`src/physics/RadiationModel.h` L342–361 的既有程式碼註解，本卡讀取，一字未改）：

> 「That query asked whether THIS class's existing D/rhoS/fc params
> (`kBridgeSoundboardThicknessM` + the "wood_spruce" MaterialDB entry, both wired in from
> `CimbalomEngine.h`) trace to the SAME measured Atlas upright-piano soundboard the ONLY usable
> literature value for `S` (`docs/RADIATION_POWER_SOURCES.md` §8.2's 1.2649 m²) comes from.
> **They do not**: `CimbalomEngine.h`'s own comments say both are "文獻類比預設值...不是
> TsukiSynth cimbalom 的實測值"」

即：現行 `kBridgeSoundboardThicknessM=9mm`／`wood_spruce` 材質是 B1（琴橋導納）當初挑的
「文獻類比預設值」（鋼琴音板 8–10mm 範圍中點、USDA Wood Handbook 通用 Sitka spruce），
不是那台 Ege/Boutillon 直立琴（arXiv:1212.2323/1210.5688）本身的實測值——與 `S=1.2649 m²`
唯一可用的文獻數字**不同源**，硬套會違反 Rule 4（跨物件挪用常數）。

**落地結果**：`S` 維持 `UNVERIFIED`；`RadiationModel.h` 依施工卡「否」分支的指示，**刻意沒有**
新增 `soundboardRadiatingAreaM2()` 或 `pressureAtDistanceFirstPrinciples()`——力鏈只組裝到
`bridgePowerFirstPrinciples()`（`W_bridge(f)`，informational endpoint，B7.md §4.4 的終點）。

**月月是否已追認**：**尚未**。這是 B7P1 這一輪的**規劃者代決**（`docs/workcards/WF0914_B7P1_force_chain.md`
標頭：「依月月 09-14『B7 開工』授權；工兵照做並在報告記錄，月月可推翻」），追認/推翻留給月月看過
`ROADMAP_PHYSICS.md` B7 條目「B7 Phase 0+1」段與本裁決包之後決定。若月月推翻「否」分支的判定
（例如認為 8–10mm 中點與那台直立琴的實際板厚足夠接近、或月月授權直接借用），需要另立卡處理，
本卡不代為決定。

---

## §3 proxy 代決追認——B7P1 §1.1

**代決內容**（`docs/workcards/WF0914_B7P1_force_chain.md` §1.1 原文）：

> 「代決預設：若 score 語意是『正規化 MIDI』（v = MIDI/127），呼叫端用 `velocity * 127.0f`」

**查證結果**（B7P1 稽核修復回合，`reports/gate_outputs/wf0914_B7P1_auditfix_summary.txt` 第 3 點）：
**BLOCKED**——代決的前提（score `velocity` 語意是正規化 MIDI）不成立。

**兩份引文**：

1. `src/score/ScoreParser.h` L285–308（`velocity` 欄位的實際登記語意，程式碼既有註解）：
   > 「`velocity` in [0,1] is read here as a plain number and carried unchanged into
   > `ScoreEvent::velocity`. It is used as the LINEAR excitation-force scale for the modal
   > engines: `ModalResonator::excite()` sets `currentAmp = baseAmp * velocity`
   > (`src/dsp/ModalResonator.h`) -- no curve, no lookup table.」

   即 score 的 `velocity` 語意是「線性激振力縮放」，`physics_verify.py` 的 M1-1d 判定式
   （velocity ×2 → +6.0206 dB）就是釘死這個語意的既判 GATE——**不是** MIDI velocity 的正規化值，
   只是剛好同樣落在 [0,1] 區間。

2. `tools/midi_to_tsukisynth.py` L786–801（本專案**唯一**真正把真實 MIDI velocity 轉成 score
   `velocity` 的程式碼，`velocity_for()` 全文）：
   ```python
   def velocity_for(note: MidiNote, profile: TrackProfile, tick_map: TickMap, pace: str) -> float:
       source_scale = note.source_velocity / 90.0 if note.source_velocity else 1.0
       velocity = profile.base_velocity * source_scale
       # ...（拍點/斷奏/樂句尾/演奏速度微調，±0.025~0.035）
       return max(0.12, min(0.92, velocity))
   ```
   `source_velocity` 是真實 MIDI 0–127 值，但除的是 **90**、乘的是 `base_velocity`
   （依角色 0.42–0.72，見同檔 L123/136/149/162/175/212/219），再夾到 `[0.12, 0.92]`。
   這個複合值**從未等於 `MIDI/127`**，也**不與 MIDI 成比例**（`base_velocity` 依角色不同，
   同一個 MIDI velocity 在不同角色會得到不同的 score `velocity`）。真實 MIDI velocity
   本身在轉譜當下就被丟棄，score JSON 裡只留下這個複合值。

**依施工卡 §1.1 自己的規則**（「若查證結果與此矛盾（score 語意根本不是正規化 MIDI）→ 不要硬套，
status=BLOCKED」）：代決前提與實際查證結果矛盾，B7P1 已依卡文指示判 BLOCKED，撤回
`bridge_power_firstprinciples_c` 的 `dumpModes()` 輸出。

**月月是否已追認**：**尚未**。這也是規劃者代決被工兵查證推翻的結果，追認/推翻（或提供另一條
合法的 proxy→MIDI 換算規則）需要月月裁決，本卡不代為決定、不自行另編一條映射規則。

---

## §4 雙路徑差異數字——本輪空白，原因與恢復條件

**§1 的表格摘要**：無表格可摘要。`reports/b7_dual_path_comparison.md` §2 用實際
`--dump-modes` 輸出（`output/wf0914/B7P3/probe_physical_piano_dumpmodes.json`）證實
`model_observables` 只有 `["modal_frequency_hz", "relative_modal_amplitude", "modal_t60_s",
"radiated_power_relative", "absolute_pressure_per_force"]`——五個都是 Path B／B6 既有欄位，
沒有任何 `_c` 後綴或 `bridge_power_firstprinciples_c`；事件層級只有 `acoustic_transfer`，
沒有 `acoustic_transfer_c`。

**差異倍率（C/B）**：無法計算——分子（Path C）不存在。

**歸因分析**：無法進行——沒有數字可歸因。

**門檻由月月定**：這句話在本輪沒有意義——沒有數字，就沒有門檻可套。**真正需要月月裁決的是
更上游的兩件事**（§2、§3 已列）：`S` 的下一步（是否推翻「否」分支、或接受 B7 卡在此環節止步）、
`velocity` proxy→MIDI 的合法換算規則（是否接受某個替代方案、或維持 BLOCKED）。**這兩者任一個
往前推進，才輪得到本卡的雙路徑比對重新有事可做**——本裁決包本身不建議走哪一條，只是把「為什麼
本輪交不出數字」講清楚。

---

## §5 三條路徑並列（給月月選，不代選）

| 路徑 | 要做什麼 | 代價 |
|---|---|---|
| **A：先裁決 §1.1（proxy 換算）** | 月月定一條合法的 score velocity→真實 MIDI 換算規則（或明確認可 §1.1 目前查到的 `midi_to_tsukisynth.py` 複合公式本身可以反解／或改用別的資料源），另立工兵卡把 `bridge_power_firstprinciples_c` 接回 `dumpModes()` | 需要一次新的查證/裁決循環；接回後 Phase 3 的雙路徑比對也只能比到 `W_bridge(f)` 這一段（§1.2 仍是「否」），比不到 1.05 m 處 Pa |
| **B：先裁決 §1.2（`S`）** | 月月在「跨琴種挪用直立琴 1.2649 m²」「改用廠商規格值（0.87–1.68 m²，非同儕審查）」「維持 `S` UNVERIFIED，B7 卡在此止步」三者間選一個（B7.md §4.5 已列的三選項） | 即使選了，若 §1.1 仍 BLOCKED，力鏈上游沒有合法輸入，`S` 裁決本身無法把 Path C 接回輸出——兩個缺口需要**都**解決才有完整 Path C 可比 |
| **C：兩者都不裁決，B7 卡本輪到此為止** | 依 B7.md §10「本卡不會走到『完整 Done』」與 §12 的合法卡住路徑，把 B7 目前狀態（Phase 1 部分完成、Phase 2/3 皆未執行）記為本輪終點，之後另擇時機處理 | 符合月月既有裁決記錄「B7 三條驗收基準本來就可能查無」的心理預期；不損失任何已完成的純函式與測試（`hammerVelocityMps()`/`hertzPeakForceNewtons()`/`hertzImpulseConsistentTauCSeconds()`/`modalEnergyFirstPrinciples()`/`bridgePowerFirstPrinciples()` 全部保留、已測試，隨時可在 A/B 任一裁決後接回） |

**本卡不選 A/B/C 中的任何一條**，三者並列、代價都寫清楚，交給月月看數字自己選。

---

## §6 裁決記錄

**2026-09-15 月月裁決**：
1. **§5 三條路徑選 C**——proxy（§1.1/§3）與 `S`（§1.2/§2）皆不裁決，**B7 本輪到此為止**：
   Phase 1 記為部分完成（`dumpModes()` 欄位撤回、五個純函式與測試保留入庫），Phase 3 無資料可比。
   之後若要重啟，先解 §1.1（可能路線：score schema 加真實 MIDI velocity 欄位，需另開卡並改 B7.md §5 的禁令）。
2. **§1 驗收基準 (a) 選乙**——標 **BLOCKED（來源缺口）**；解除阻塞的三條管道（向 Goebl 索取
   Fig. 2.20 校準值／機構帳號取 Roginska 2013／借閱 Meyer 動態範圍表）留給月月日後有機會時再說。
3. 依 B7.md §10/§12，此為本卡**合法終點**；ROADMAP/TODO 的 B7 條目同步標
   「In progress——Phase 0 完成、Phase 1 部分完成（欄位撤回版）、Phase 2/3 BLOCKED（月月 09-15 裁決）」。
