# 施工卡 WF0914-D11：弦長/弦徑偏差 R10 前後對照 + 裁決包

> lane：C++（`build-wf\`，排在 D12 之後）　**本卡產物是 patch + 報告，不落地**（R10：月月另裁）
> 先讀：`WF0914_README.md`、`TODO.md` D11 條目與其指向的原始記錄、
> `reports/a14_tauc_keytrack_before_after.md`（**Rule 10 報告的標準體例，照抄它的結構**）、
> 弦模型相關 `src/`（自行定位：0.35 m@A4 與固定弦徑寫在哪個檔）。

## 0. 一句話目標

D11 登記：弦長 0.35 m@A4 + corpus 固定弦徑使 **B 路徑（B6 絕對聲壓）偏高 2.4～5.2×**。
本卡：(1) 溯源真實鋼琴弦長/弦徑尺度資料；(2) 若溯源成功，做候選修正的**前後對照報告**
（A14 模式：patch 存檔、不 apply 進工作樹交付），給月月裁決。

## 1. Phase A：溯源（先做；查無則本卡到此為止，誠實記錄）

要找的是**同儕審查或教科書層級**的鋼琴弦尺度資料：逐音（或分段）弦長 L(note) 與弦徑 d(note)。
候選方向：Fletcher & Rossing *The Physics of Musical Instruments*（弦樂章節的典型尺度表）、
Conklin 的 JASA 鋼琴設計系列、既有 repo 引用鏈（`BRIDGE_ADMITTANCE_SOURCES.md`、
`HAMMER_CONTACT_SOURCES.md` 的參考文獻）。規則同 D10：只用親自 fetch/讀到的數字，
廠商 stringing chart 屬廠商規格層級（可用但要明標）。產出 `docs/STRING_SCALE_SOURCES.md`
（找到/查無都要寫）。**查無 → status=DONE，報告寫明 Phase B 未執行的原因。**

## 2. Phase B：候選修正 + 前後對照（溯源成功才做）

1. 動工前：把要改的檔案原樣複製到 `output/wf0914/D11/backup/`（**還原用檔案複製，
   不用 git checkout/stash——R7**）。
2. 在 build-wf 實作候選修正（弦長/弦徑接溯源資料；體例比照 `interpAnchorsFlat()`）。
3. 量前後差異：對 corpus 代表曲（至少含 physical_piano 與一首 cimbalom）跑 `--dump-modes`，
   記 B 路徑絕對聲壓的前後值與倍率變化；跑 8 首位元基準證明**渲染輸出也會變**（這正是 R10 的證據，
   預期會變，如實記錄哪些首變）。
4. `git diff > reports/d11_string_scale_candidate.patch`，然後**從 backup 還原全部改動檔**，
   還原後 `git diff -- src/` 必須為空（證據存檔）。
5. 報告 `reports/d11_string_scale_before_after.md`（照 A14 報告體例）：改了什麼、依據、
   前後數字表、B 偏高倍率修正到多少、哪些 GATE 會受影響、「落地與否由月月裁決」。

## 3. GATE

- 交付時 `git diff -- src/ tools/ tests/` **為空**（只有 docs/reports 新檔）。
- patch 可乾淨 `git apply --check`（證據存檔）。
- 每個數字對得回 `output/wf0914/D11/` 原始輸出。
- 證據檔 `reports/gate_outputs/wf0914_D11_*.txt`。
