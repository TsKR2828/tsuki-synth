# D8 Rule 10 前後對照報告：兩首月光空靈鼓相關曲 `exciter: finger → wood_mallet`

> 產出：2026-09-09（施工卡 `docs/workcards/WF0909_D8_wood_mallet.md`）
> 依據：`reports/decision_packets/D8_tongue_drum_diagnosis.zh-TW.md` 選項 1；**月月 2026-09-09 裁決：`wood_mallet`**。
> 範圍：只改 `scores/examples/moonlight_sonata_movement1_tongue_drum.score.json` 與
> `scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json` 兩檔裡 **engine == "tongue_drum"** 事件的
> `params.exciter`（各 1142 個事件，`finger` → `wood_mallet`）。混音版的 cimbalom（揚琴）事件完全不動。
> 這是 Rule 10 改動（渲染輸出改變），月月已做美學裁決，本卡**落地**；本報告是規約要求的前後對照存檔。
> before 基線＝本卡開工前的乾淨工作樹（HEAD `98f346f`，兩份 score 與 index 一致）。
> 方法腳本與原始資料：`output\wf0909\D8\`（gitignored；`rule10_metrics.py`／`gen_probes.py`／`measure_slope.py`／
> `f0_t60_first5.py`，均為本卡新寫，方法沿用 `reports/gate_outputs/b4_method/render_affected_pieces.py`
> 的 RMS/質心定義與 `output/wf0907/R6/verify3/measure.py` 的斜率探針量測法）。

---

## §0 白話導讀

**一句話結論**：兩首月光空靈鼓相關曲的 tongue_drum 事件，槌具從 `finger`（超軟，接觸時間 4–11 ms）
換成 `wood_mallet`（接觸時間短很多）之後，空靈鼓獨奏版的音色從「幾乎全部能量堆在 200 Hz 以下、旋律音域
只剩 2.6%」變成「82.4% 能量落在 200 Hz–2 kHz 的旋律音域」；單音的音高-響度斜率（MIDI 37→87，同 velocity）
從 37–49 dB 掉到 3–8 dB（依樂譜實際用到的兩組幾何略有不同，見 §3）。**音高（f0）與衰減時間（T60）
在檢查過的每一顆音上都是位元不變**——exciter 只餵給力脈衝的頻譜「形狀」，不接觸模態頻率或阻尼模型，
這條是可證偽的物理預測而非假設，本報告 §4 用 `--dump-modes` 逐位元驗證過。混音版本身就受影響較小
（tongue_drum 只作揚琴的延遲光暈層，見 §5），但同一批事件也一併換了槌具以維持全庫一致。

**你要看的數字**（整曲，正規化後）：空靈鼓獨奏版 200 Hz 以下能量占比 **97.36% → 17.55%**，旋律音域
（200 Hz–2 kHz）**2.64% → 82.44%**；混音版 200 Hz 以下 **29.41% → 23.80%**，旋律音域 **70.51% → 76.13%**
（混音版原本就有揚琴撐著旋律，變化小很多，符合預期）。

**驗證通過的部分**：`verify_score.py` 兩檔全 PASS（schema／modal／render／determinism 全綠）；diff 範圍乾淨
（各 1142 行改動，非 exciter 欄位零差異）；8 首位元不變代表曲重渲後精確 6/8 不變 + 2 首改變（正是這兩首，
無外溢）；f0/T60 逐音位元不變。

**GATE 4 的兩輪紀錄**：第一輪 `python -m pytest tests -q` 有 **2 個測試失敗**（`tests/test_stem_verify.py`
的 `test_e2e_run_on_real_fixture_stem_count_matches_and_established` 與
`test_f01_own_temp_success_and_failure_paths_unaffected`）。**這兩個失敗與本卡的改動無關**：
本卡只碰兩份 `.score.json`；失敗的測試檔 `tests/test_stem_verify.py` 與其測的模組 `tools/stem_verify.py`
本卡完全沒有碰過，`git diff`（unstaged）對這兩個檔案是空的——它們的內容差異全部在**已 staged**（前幾輪
WF0907 C11/C12 卡稽核通過後的既有狀態，744 行）。查明是同一工作樹裡另一張卡（WF0909-C10B）的半成品
造成的並行汙染；C10B 半成品撤回後，**第二輪重跑全套 pytest 為 262 passed, 1 skipped, 1 xfailed，
0 failed，全綠**，證實診斷正確。詳見 §8、`reports/gate_outputs/wf0909_D8_exciter.txt`（含「第二次執行」段）。

---

## §1 改動內容

```
- "exciter": "finger"        (engine == "tongue_drum" 事件, 兩檔各 1142 個)
+ "exciter": "wood_mallet"
```

只用腳本（`output\wf0909\D8\edit_exciter.py`）解析 JSON、依 `engine=="tongue_drum"` 過濾後改單一欄位、
以 `json.dumps(indent=2, ensure_ascii=False)` 重新序列化——對**未改動**的內容做過位元級 round-trip 測試
（改動前對照 `git show HEAD:<path>` 的內容，round-trip 結果與原檔逐位元相同），確保這次唯一的差異就是
exciter 欄位本身，而不是格式化順手改動別的東西。`engine=="cimbalom"` 的揚琴事件完全沒有被腳本碰到。

## §2 diff 範圍驗證（GATE 1）

```
$ git diff --numstat -- scores/examples/moonlight_sonata_movement1_tongue_drum.score.json scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json
1142    1142   scores/examples/moonlight_sonata_movement1_tongue_drum.score.json
1142    1142   scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json
```

`git diff -- <每一檔> | grep '^[-+]' | grep -v exciter`（排除 `+++`/`---` 標頭行）在兩檔皆為空——
逐行核對過，改動的 1142 行全部、只有 `"exciter": "finger"` → `"exciter": "wood_mallet"` 這一種變化。
完整命令與輸出見 `reports/gate_outputs/wf0909_D8_exciter.txt`。

## §3 整曲 Rule 10 指標（GATE 3）

方法：channel 平均混單聲道；RMS dBFS = 20·log10(sqrt(mean(x²)))（整檔無窗）；質心＝整檔無窗 rfft
振幅平方加權平均頻率；能量占比＝該頻帶 |X(f)|² 總和 / 全頻譜 |X(f)|² 總和（與 D8 決策包 §3.5 同一組
頻帶邊界：<200 Hz／200 Hz–2 kHz／>2 kHz）。兩份 score 的 `export.normalize` 皆為 `true`，RMS 反映的是
正規化後的波形結構差、不是絕對電平差（沿用 `reports/b4_hammer_contact_before_after.md` 的說明慣例）；
質心與能量占比是尺度不變的形狀指標，不受正規化影響。

### 3a. 空靈鼓獨奏版（`moonlight_sonata_movement1_tongue_drum.score.json`，327.29 s）

| | RMS (dBFS) | 質心 (Hz) | <200 Hz | 200 Hz–2 kHz | >2 kHz |
|---|---|---|---|---|---|
| before (`finger`) | −20.22 | 81.41 | **97.3557%** | 2.6442% | 0.0001% |
| after (`wood_mallet`) | −21.59 | 367.24 | **17.5481%** | **82.4365%** | 0.0154% |
| Δ | −1.37 dB | +351.1% | −79.81 pt | +79.79 pt | +0.0153 pt |

與 D8 決策包 §3.5（97.36% → 17.55%、2.64% → 82.44%，探針幾何不同但同一份 score）幾乎逐位吻合，
交叉驗證本報告的量測鏈與決策包一致。

### 3b. 揚琴+空靈鼓混音版（`moonlight_sonata_movement1_yangqin_tongue_mix.score.json`，325.87 s）

| | RMS (dBFS) | 質心 (Hz) | <200 Hz | 200 Hz–2 kHz | >2 kHz |
|---|---|---|---|---|---|
| before (`finger`) | −23.41 | 360.13 | 29.4139% | 70.5117% | 0.0744% |
| after (`wood_mallet`) | −23.90 | 375.68 | 23.8049% | 76.1287% | 0.0663% |
| Δ | −0.49 dB | +4.3% | −5.61 pt | +5.62 pt | −0.0081 pt |

混音版變化遠小於獨奏版——tongue_drum 依設計只作揚琴的延遲光暈層（見 §5 商品表既有記載：延遲 18 ms、
平均 velocity 0.127 vs 揚琴主奏 0.247），旋律本來就由揚琴（cimbalom/wood_mallet，未動）承擔。

完整指令與輸出：`reports/gate_outputs/wf0909_D8_exciter.txt`（`rule10_metrics.py` 全文與執行結果）。

## §4 單音音高-響度斜率（MIDI 37→87，同 velocity=0.5，重用 D8 附錄 B 探針方法）

樂譜本身兩組幾何（第三組 2.0/18/0.46 只有 14/1142=1.2% 事件，本節未探）：

| 幾何 | 事件數 | 占比 |
|---|---|---|
| thickness 2.6mm / width 24mm / strike 0.44（`gmaj`） | 952 | 83.4% |
| thickness 3.2mm / width 30mm / strike 0.42（`gmin`） | 176 | 15.4% |

探針：MIDI 37/47/57/67/77/87 各 6.0 s，8.0 s 間隔，dry（無 reverb/delay/distortion），velocity=0.5，
`normalize:false`；RMS 分別取 0.3 s 窗（onset 起算）與 6.0 s 窗（全音長）；`fund_share_pct_6s` = 6.0 s
窗內 ±3% 頻帶energy 占整體頻譜能量的比例（方法完全沿用 `output/wf0907/R6/verify3/measure.py`）。

| 幾何 | exciter | 0.3s 窗斜率 37→87 | 6.0s 窗斜率 37→87 | 基頻占比 MIDI37 | 基頻占比 MIDI87 |
|---|---|---|---|---|---|
| gmaj (83.4%) | finger（出貨設定） | **37.20 dB** | 47.13 dB | 99.27% | 96.42% |
| gmaj (83.4%) | wood_mallet | **2.67 dB** | 8.32 dB | 49.61% | 99.16% |
| gmin (15.4%) | finger（出貨設定） | **39.31 dB** | 49.21 dB | 99.27% | 97.81% |
| gmin (15.4%) | wood_mallet | **2.77 dB** | 8.24 dB | 46.32% | 99.12% |

兩組幾何的方向與量級一致：0.3 s 窗斜率從 37–39 dB 掉到約 2.7 dB，與 D8 決策包引用的「41.5 → 5.5 dB
（第一輪 2.6/24/0.44 幾何，1.0 s 窗）」「47.6 → 6.7 dB（3.2/30/0.42 幾何）」同方向、不同量測窗，
數量級吻合。低音端（MIDI 37）換 `wood_mallet` 後基頻占比從 ~99% 降到 46–50%（決策包 §3.11 指出的
「基頻讓給模態 2」副作用，這裡兩組幾何都重現），高音端（MIDI 87）基頻占比不降反升（96–98% → 99%）。

完整指令、探針 score、原始量測 JSON：`output\wf0909\D8\gen_probes.py`／`measure_slope.py`／
`probe_scores\*.score.json`／`probe_render\*.wav`／`measure_slope.json`（gitignored；數字表已抄進
`reports/gate_outputs/wf0909_D8_exciter.txt`）。

## §5 f0 / T60 不變性（前 5 顆 tongue_drum 音，模型級，逐位元）

exciter 只餵給 `HammerImpulse` 的力脈衝頻譜幅度加權（`chromaticExciterHardness()` →
`cp.exciterHardness`，`src/score/ScoreRenderer.h:311`），從不接觸模態頻率（幾何決定）或阻尼/衰減模型
（另一條路徑）——所以 f0 與 T60 逐位元不變是可證偽的物理預測，不是假設。用 `--dump-modes` 對 before/after
各自的兩份 score 各取前 5 個 tongue_drum 事件，比對模態 1（基頻）的 `freq` 與 `decay`（= T60，
`model_observables` 明列 `modal_t60_s`）：

| score | idx | MIDI | f0 (Hz) | T60 (s) | f0 相同 | T60 相同 |
|---|---|---|---|---|---|---|
| tongue_drum | 0 | 37 | 69.2960 | 68.6750 | True | True |
| tongue_drum | 1 | 49 | 138.5910 | 33.0300 | True | True |
| tongue_drum | 2 | 56 | 207.6520 | 21.2390 | True | True |
| tongue_drum | 3 | 61 | 277.1830 | 15.3470 | True | True |
| tongue_drum | 4 | 64 | 329.6280 | 12.5690 | True | True |
| yangqin_tongue_mix | 3 | 37 | 69.2960 | 68.6750 | True | True |
| yangqin_tongue_mix | 4 | 49 | 138.5910 | 33.0300 | True | True |
| yangqin_tongue_mix | 5 | 56 | 207.6520 | 21.2390 | True | True |
| yangqin_tongue_mix | 7 | 61 | 277.1830 | 15.3470 | True | True |
| yangqin_tongue_mix | 9 | 64 | 329.6280 | 12.5690 | True | True |

（mix 檔的 idx 不連續是因為事件依時間排序、與同時發聲的 cimbalom 事件交錯；已篩到 engine=="tongue_drum"
的前 5 個。）完整輸出：`output\wf0909\D8\f0_t60_first5.py` 與 `dump_{old,new}_{td,mix}.json`（gitignored，
比對結果全文已存入 `reports/gate_outputs/wf0909_D8_exciter.txt`）。

## §6 verify_score.py（GATE 2）

`python tools/verify_score.py <score>` 對兩份改動後的 score 皆 **PASS**（schema／modal／render／
rests／audio／determinism 全部 `[OK]`，含 `modes.f0_deviation` 最大偏差 0.019 cents、
`determinism.sha256_match` 兩次獨立渲染逐位元相同）。完整輸出見
`reports/gate_outputs/wf0909_D8_exciter.txt`。

## §7 melody_verify.py（informational，非 GATE）

用已渲染好的 WAV（`--wav`，不重渲）跑 `tools/melody_verify.py`：

| score | 版本 | PASS | FAIL | UNVERIFIED | 總數 |
|---|---|---|---|---|---|
| tongue_drum（獨奏） | before (`finger`) | 1 | 84 | 1058 | 1143 |
| tongue_drum（獨奏） | after (`wood_mallet`) | 0 | 36 | 1107 | 1143 |
| yangqin_tongue_mix | before (`finger`) | 0 | 0 | 2285 | 2285 |
| yangqin_tongue_mix | after (`wood_mallet`) | 0 | 0 | 2285 | 2285 |

混音版兩版本完全一樣（0/0/2285）——因為 tongue_drum 與 cimbalom 大量同時發聲，
melody_verify 的頻帶碰撞（band collision）判定讓幾乎所有事件落入 UNVERIFIED，這與 exciter 無關，
是混音編曲本身的性質（見 §3b：混音版本來就不靠 tongue_drum 撐旋律）。

獨奏版的數字**不完全符合卡上「預期拒答率大降」的猜測，如實記錄**：FAIL 從 84 降到 36（降了 57%），
但 UNVERIFIED 反而從 1058 升到 1107、PASS 從 1 降到 0——狹義的「拒答率」（UNVERIFIED / 總數）其實從
92.6% 微升到 96.8%，沒有下降。合理解讀：`finger` 版接近純正弦、`wood_mallet` 版泛音豐富，兩者都遠遠
不是 melody_verify 設計要驗收的「乾淨、可拒答分類」訊號，只是不乾淨的方式不同（`finger` 版的失敗
理由多半是「二次敲擊蓋在前一顆音殘響尾巴上、殘響未衰減到 21 dB」這種**FAIL**，`wood_mallet` 版因泛音
結構複雜，同一批事件裡有更多落進「pitch 判定被同時發聲的其他事件污染」這種**UNVERIFIED**）。
FAIL 絕對數下降本身不能反推「音色變好」，melody_verify 在本卡是單純的資訊記錄，不作為 Rule 10
判斷依據（GATE 卡上明寫 informational，不是 GATE 3/4 的一部分）。

**誠實揭露一個量測雜訊來源**：`tools/melody_verify.py` 在本卡執行期間被**另一條並行 lane**
unstaged 修改（`git diff --stat` 顯示 168 行差異，非本卡所改），4 次 melody_verify 呼叫分散在
約 10 分鐘內背景執行，理論上有可能跨到修改前後兩個版本，四次結果不保證用的是同一份
`melody_verify.py`。因為本節本來就是 informational、不是 GATE，且四次呼叫都明確標註哪一版
score／哪一份 wav，不影響任何判定，這裡只是誠實記錄可能的雜訊來源。

## §8 pytest（GATE 4）——第一輪 FAIL（與本卡改動無關）／第二輪重跑 PASS

**第一輪**（同日、同工作樹，另一張卡 WF0909-C10B 半成品仍在時）：

```
$ python -m pytest tests -q
...
FAILED tests/test_stem_verify.py::test_e2e_run_on_real_fixture_stem_count_matches_and_established
FAILED tests/test_stem_verify.py::test_f01_own_temp_success_and_failure_paths_unaffected
2 failed, 258 passed, 1 skipped in 110.96s
```

隔離重跑兩次（無其他背景工作、CPU 空閒）結果一致（非併發雜訊/計時抖動）。`git diff`（unstaged）對
`tests/test_stem_verify.py`／`tools/stem_verify.py` 皆為空——本卡完全沒有碰過這兩個檔案，這兩個測試檔
也不 import `tools/melody_verify.py`（本輪其他工兵正在改的檔案，unstaged 112 行）或任何 `src/physics/*.h`
（本卡未編譯 `build\`，即使有未 commit 的 .h 改動也不會反映在現成 exe 裡）。這兩個檔案的內容差異全部是
**已 staged**（前幾輪 WF0907 C11/C12 卡稽核通過留下的狀態，744 行）——換句話說，這個失敗在本卡開工前
就已經存在於工作樹裡，只是可能還沒有人針對這兩個測試單獨跑過。`DEVLOG.md`（unstaged，本輪工兵留下）
記載了同一類「同一工作樹並行時，未完成卡的新測試檔會讓別卡的全套 pytest 紅」的教訓，並建議
「下次全套 pytest 應放整合卡而非每卡 GATE」——與本卡遇到的狀況同一類。

**第二輪**（接手重跑，C10B 半成品已撤回後）：

```
$ python -m pytest tests -q
...............x........................................................ [ 27%]
...................s.................................................... [ 54%]
........................................................................ [ 81%]
................................................                         [100%]
262 passed, 1 skipped, 1 xfailed in 155.50s (0:02:35)
rc=0
```

全綠（0 failed / 0 error），包含第一輪那兩條 `test_stem_verify.py` 測試在內。證實第一輪的診斷正確：
那 2 個 FAIL 是 C10B 半成品的並行汙染，不是本卡改動造成的迴歸；C10B 撤回後同一份工作樹上重跑即恢復
全綠。完整兩輪輸出見 `reports/gate_outputs/wf0909_D8_exciter.txt`（含「第二次執行」段）。

## §9 8 首位元不變基準換新（README §3 / §1 要求）

兩首受影響曲目在 8 首位元不變代表曲名單中（`reports/gate_outputs/b6_method/sha256_before.txt` 第 2 行
`yangqin_tongue_mix`、第 5 行 `tongue_drum`）。用 `reports/gate_outputs/b6_method/render_b6_scores.py`
（未改動，本身已支援 `--cli`，Python lane 用預設 `build\` CLI）以 `--label before_post_d8` 重渲 8 首，
寫入 `reports/gate_outputs/b6_method/sha256_before_post_d8.txt`（新基準）：

| 曲目 | 舊基準 SHA256（前16碼） | 新基準 SHA256（前16碼） | 是否相同 |
|---|---|---|---|
| moonlight_sonata_movement1_yangqin | 49514b007e3e01fc | 49514b007e3e01fc | **相同** |
| moonlight_sonata_movement1_yangqin_tongue_mix | 7b0413dd4f858079 | 280cbdac3c117c14 | **改變**（本卡） |
| physical_piano | 607d0d3bc578136f | 607d0d3bc578136f | **相同** |
| restraint_metal_click | be634798c4a0bf71 | be634798c4a0bf71 | **相同** |
| moonlight_sonata_movement1_tongue_drum | c37ac02d01f08a30 | f539aefa91919cbf | **改變**（本卡） |
| water_gong_free | 31b539c6ac08d942 | 31b539c6ac08d942 | **相同** |
| ai_radiance_m1 | 74122637a0c71278 | 74122637a0c71278 | **相同** |
| fur_elise_opening | b0877774da9e5fc5 | b0877774da9e5fc5 | **相同** |

**精確 6/8 相同 + 2/8 改變（只有本卡改動的兩首），無外溢**——符合卡上 §1 的預期，沒有觸發「其他 6 首若變
= 外溢 = RED」。舊基準檔 `sha256_before.txt` 未刪除（保留歷史）；`reports/gate_outputs/b6_method/README.md`
未動（該檔案不在本卡範圍）；`WF0907_README.md` §3 的基準切換註記另見該檔案本身的修訂（本卡按 §1 指示更新，
見 `git diff -- docs/workcards/WF0907_README.md`）。完整指令輸出：
`reports/gate_outputs/wf0909_D8_exciter.txt`。

## §10 商品表更新

`exports/products/moonlight_batch1/PRODUCT_SHEET.md` 與 `reports/product_sheets/moonlight_batch1_PRODUCT_SHEET.md`
的「已知缺陷」段落新增本卡的更新記錄（§3a 的新數字、slope 新數字），並明寫：**score 層級的音色缺陷已由
本卡解除，但商品表所列的母帶／發行檔／SHA256 尚未依新 exciter 重新渲染**（不在本卡範圍——本卡只改
`scores/` 兩個檔案，不碰 `exports/products/` 下的母帶產線），**且上架仍受最上方記載的 CC BY-SA 授權疑慮
限制、月月 2026-08-28 裁決未變**（換源重製前不上架）——不因音色缺陷解除而變成可上架。

---

## GATE 完成狀態

| GATE | 結果 |
|---|---|
| 1. diff 範圍（各 1142 行、只改 exciter） | **PASS** |
| 2. verify_score.py 兩檔 | **PASS** |
| 3. 指標表與報告 | **PASS**（本文件 + `reports/gate_outputs/wf0909_D8_exciter.txt`） |
| 4. `python -m pytest tests -q` 全綠 | 第一輪 **FAIL**（2 failed，係 C10B 半成品並行汙染，見 §8）→ **第二輪 PASS**（262 passed, 1 skipped, 1 xfailed, 0 failed，C10B 撤回後重跑） |
| 5. `git diff --stat` 範圍 | **PASS** |

**最終狀態：GATE 1-5 全數 PASS（第二輪重跑），DONE。**
證據檔：`reports/gate_outputs/wf0909_D8_exciter.txt`（含「第二次執行」段，完整命令與輸出）。
