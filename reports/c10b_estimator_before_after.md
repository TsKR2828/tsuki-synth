# C10B：pitch 量測器改善 + 全量音高證據前後對照

> 工兵：Sonnet　日期：2026-09-09　卡：`docs/workcards/WF0909_C10B_estimator.md`
> 依據：月月 2026-09-09 裁決 C10 選項 B（改估計器重跑證據）
> 完整命令與輸出：`reports/gate_outputs/wf0909_C10B_estimator.txt`

> **現況（修正回合，2026-09-09）：下面 §0-§4 是原始回合的記錄，其結論已被
> 稽核推翻並撤回，保留原樣做歷史記錄，不倒填改寫。現況見本文件最後的
> 「§5 修正回合」章節：估計器已撤回，C10 的自證問題（1.1721 cents，
> hold-out 網格另量到 1.0840 cents）依然未解，卡狀態 RED。**

## 0. 一句話白話導讀（原始回合，已撤回）

`melody_verify.measure_pitch_cents()`（stem_verify / partial_verify 共用的同一顆
pitch 量測函式）原本量自己都有到 **1.17 cents** 的系統誤差，比月月定的
「≤1 cent 才有資格判 ±5 cents」門檻高。試了三種標準做法（單峰拋物線內插、
相位差法、zero-padding 質心）都各有問題——前兩種在**乾淨合成訊號**上量測誤差
壓到 0.08–0.22 cents 遠優於門檔，但一搬到**真實渲染音檔**（揚琴/大揚琴預設的
3 弦微分音「course」音色）就整個爆掉，5 顆哨兵音有 4 顆從 PASS 掉成 FAIL；
第三種（zero-padding）數學上證明壓不下去，會卡在原本的 1.17 cents 附近。

最後採用的做法是**同一個質心公式，只是把 ±3% 頻帶的兩個硬邊界從「切一刀」
改成「柔化漸層」**——保留質心對 course 微分音天生穩健的特性，同時去掉硬邊界
造成的系統偏差。結果：**開發網格 0.2924 cents、獨立 hold-out 網格 0.2465 cents，
都在 1 cent 門檻內**，而且在真實音檔（哨兵/給愛麗絲/月光）上**沒有任何一顆
從 PASS 掉成 FAIL**——給愛麗絲乾聲全曲逐顆音高判定 671/22/212 完全不變，
月光弱域反而多了 6 顆從 FAIL 修正回 PASS
`[修正回合更正：原文誤植為「月光…32顆」，32顆其實是給愛麗絲 whole-file
baseline 的數字，月光是 6 顆——見 §2 表格與 §5；此處保留原句只更正數字，
不倒填改寫論點]`。唯一的例外是一個 informational
（非 GATE）工具 `partial_verify.py` 裡，一顆早就被標記「基頻天生弱、量測極限」
的近乎沉沒在雜訊裡的泛音，兩個估計器都在門檻邊緣、換了估計器後從壓線 PASS
變成壓線 FAIL——這顆音本來就不該被信任任何一個估計器的判定。

**±5 cents 產品容差本身、拒答規則、band 選擇、course/detune 判定邏輯，
一個字都沒動（R2）。**

**（修正回合按語：上面這段的「達標」「零迴歸」結論已被稽核推翻——見 §5。
柔化質心把偏差增益壓低到約 0.40，等於在不改 ±5 cents 數字本身的情況下把
低音區實質容差放寬，違反 R2；「零迴歸」的判斷本身依賴的兩個網格結構上
測不到這個問題。）**

## 1. 為什麼三個候選方法都被否決（原始回合記錄，詳細數字見證據檔 step 1）

| 候選 | 開發網格 max\|error\| | Hold-out max\|error\| | 真實音檔（哨兵）結果 | 裁決 |
|---|---:|---:|---|---|
| (a) 單峰拋物線內插 | 0.2228c PASS | 0.0832c PASS | 5顆中4顆 PASS→FAIL（-8.95c 等） | **否決** |
| (b) 相位差法 | 0.3923c PASS | (未測，因(a)理由已否決) | 5顆中4顆 PASS→FAIL（-8.04c 等） | **否決** |
| (c) zero-padding 質心 | 1.17~1.18c FAIL（8x~64x 皆不收斂） | 未測 | 未測（開發網格已否決） | **否決** |
| (d) 邊緣柔化質心（原始回合採用） | 0.2924c PASS | 0.2465c PASS | 5顆全 PASS，數字比舊估計器更準 | **原採用，修正回合撤回** |

(a)/(b) 共同的失敗機制：本專案樂器預設 course（cimbalom/piano 3 弦，
互相微分音 ±5 cents）在分析視窗長度下，弦與弦的頻率差常常小於一個 FFT bin
（例如 C4 上 5 cents ≈ 0.377 Hz，bin 解析度 ≈ 0.81 Hz），單峰估計器在這種
「同一個 bin 裡有好幾股訊號互相干涉」的情況下，量到的是某個瞬間的相位競爭
結果，不是 course 真正的中心頻率。**合成自證網格完全沒有模擬 course**
（`measurement_selfcal.py` 自己文件裡寫明的簡化假設），所以這個失敗模式
只有拿真實渲染音檔才驗得出來——這正是本卡要求「重跑所有既有證據」而不是
「只看自證網格數字就收工」的原因。

(c) 則印證了 C10 裁決包 §0 原本的診斷：偏差來自頻帶邊界內**真實的旁瓣能量**，
不是離散取樣造成的量化誤差，所以加密同一段連續頻譜的取樣點數（zero-padding）
救不了它。

(d) 在真實音檔上表現良好、也通過了 §2.2 的 hold-out 網格，看起來像是成功
的修正——**但兩個網格都只測了「真值剛好落在頻帶中心」這一種情況**，見 §5。

## 2. 逐項證據前後對照（原始回合記錄，已被稽核推翻，見 §5）

| 項目 | 舊估計器（質心，硬邊界） | 新估計器（質心，邊緣柔化） | 結論（原始回合） |
|---|---|---|---|
| 自證：開發網格（1170點） | 1.1721c（FAIL） | 0.2924c（PASS） | 達標 |
| 自證：hold-out 網格（1040點，新增） | (未曾有此網格) | 0.2465c（PASS） | 達標，非過擬合 |
| `--selftest`（哨兵5件組） | PASS 5/5 | PASS 5/5 | 不變（新法數字更準：max 0.49c vs 1.60c）|
| 給愛麗絲 stem_verify 乾聲全曲（905事件） | 671 PASS/22 FAIL/212 UNVERIFIED | 671/22/212，逐顆 verdict 100% 相同 | 零迴歸 |
| 給愛麗絲全曲 whole-file baseline（乾聲） | 8 PASS/34 FAIL/864 UNVERIFIED | 40 PASS/2 FAIL/864 UNVERIFIED | 32 顆 FAIL→PASS，0 顆 PASS→FAIL |
| 月光 v4（1142事件，今日重量測基準） | 2 PASS/40 FAIL/1101 UNVERIFIED | 8 PASS/14 FAIL/1121 UNVERIFIED | 6 顆 FAIL→PASS，13 顆仍FAIL但數值改善，0 顆 PASS→FAIL |
| HostProbe H6（5個 block size） | 5×(5 PASS/0 FAIL/0 UNVERIFIED) | 5×(5 PASS/0 FAIL/0 UNVERIFIED) | 不變，仍位元相同 |
| corpus 30檔強域全綠子集 | 全部 0 FAIL | 全部 0 FAIL，PASS/UNVERIFIED 數字逐檔相同 | 零迴歸 |
| partial_verify 弱基頻22顆（informational） | pass=22/fail=0 | pass=21/fail=1（見上方§1解釋，近雜訊底噪音） | 1顆邊緣翻轉，已解釋 |
| partial_verify 一般40顆partials（informational） | PASS 199/FAIL 38（共237顆） | PASS 219/FAIL 18 | 淨改善 |

Cubase L3b 匯出 WAV（項目6）因檔案已不在磁碟（gitignored output/，
2026-08-22 產生）而跳過，按卡上「若在 repo/reports 內」的條件說明略過。

**（修正回合按語：這張表上「32 顆 FAIL→PASS」「6 顆 FAIL→PASS」等數字，
在沒有真實音檔 ground truth 的情況下無法區分「修正」與「假綠燈」——見 §5
的稽核發現。§5 的重跑證實：撤回估計器後，這張表的「舊估計器」欄位數字
就是現在的實際數字，「新估計器」欄位的數字已不再是本專案的產品行為。）**

## 3. 完整測試與範圍（原始回合記錄）

- `PYTHONPATH=tools python -m pytest tests/test_stem_verify.py tests/test_measurement_selfcal.py -q` → 54 passed（新增 2 條：hold-out 網格斷言、新舊估計器對照斷言）。
- `python -m pytest tests -q` → 262 passed, 1 skipped（既有、不相關的 skip）。
- 容差 `±5 cents` / `±10 ms`、`PITCH_TOL_CENTS`、`ONSET_TOL_S`、band 寬度
  `BAND_REL_WIDTH`、拒答規則 Ra–Re、course/detune 判定，全部逐位元組
  未變動（唯一新常數 `PITCH_EDGE_TAPER_FRAC = 0.75`，屬於「頻率估計數學」
  本身，不是產品容差，見 `tools/melody_verify.py` 內的完整推導註解）。

## 4. 尚待月月看過的一個誠實揭露（原始回合記錄）

月光 v4 的「FAIL→UNVERIFIED」20 顆（見證據檔 item 5）不是逐顆手動核對過
每一條拒答規則邊界，只確認了：(a) 沒有任何一顆是 PASS→FAIL（本卡最在意
的迴歸方向）、(b) 月光本來就是設計文件自己認定的弱域、非 GATE 證據。
若之後有場景需要月光的拒答理由逐顆可信度，建議另開一張小卡用 C11 的
`rules`/`reason` 欄位做完整分類，而不是本卡順手做完。

---

## 5. 修正回合（2026-09-09）：稽核 FAIL → 估計器撤回 → 全量重跑確認零漂移

### 5.0 一句話白話導讀

稽核抓到兩個 blocker：(1) §0-§2 的柔化質心把柔化的「權重最高點」釘死在
**期望值 f0** 上，等於真值離期望值越遠、量到的偏差就被壓得越小——用卡自己
的 `measurement_selfcal.measure_one(freq_offset_cents=...)` 實測，MIDI 37
真值 +12.0 cents 時，柔化估計器只測到 +4.806c（增益 0.40），舊估計器測到
+8.620c（增益 0.72，仍不完美但明顯更準）——在完全不碰 ±5 cents 這個數字的
情況下，把低音區實質可信賴的容差放寬到約 ±12.5 cents，違反 R2。(2) §0-§2
用到的開發網格與 hold-out 網格，都把頻帶對準「已經偏移過的真值」本身，
結構上只測得到「真值剛好落在頻帶中心」這一種情況，測不出 (1) 這個問題。

修正回合用稽核的方法做了一次完整的 taper 分數掃描（0.75→0.00，13 步）加
一個新試的第五候選（自我參照式 mean-shift 柔化），證實**自證誤差**與
**增益保真度**在這個估計器家族裡是連續、單調、無法兩全的取捨——完整數字
見 `reports/gate_outputs/wf0909_C10B_estimator.txt` STEP 5 與
`tools/melody_verify.py::measure_pitch_cents()` 的 docstring。依卡 §5 的
規則（三個以上方法都達不到 ≤1.0 含 hold-out，停下回報數字），
**`measure_pitch_cents()` 撤回，回到 §0-§2 記錄的硬邊界質心數學**（現在與
`measure_pitch_cents_legacy()` 位元組相同，新增的迴歸測試
`test_measure_pitch_cents_matches_legacy_after_revert` 鎖定這件事）。

全量重跑確認：撤回後，§2 表格「舊估計器」欄位的每一個數字都逐一重現
（fresh 重跑，見 §5.2），**零漂移**。C10 的核心問題——開發網格 1.1721
cents、本輪同時修正 `HOLDOUT_T_ONSET_S`（原本 9.99375× hop，幾乎沒有真的
偏離 bin 對齊）後新量出的 hold-out 網格 1.0840 cents，兩者皆 > 1.0 cent
門檻——**依然未解**。

### 5.1 為什麼「柔化質心」與新試的「mean-shift 柔化」都被否決

| 候選 | 開發網格 max\|error\| | 乾淨訊號最差增益缺口 | 裁決 |
|---|---:|---:|---|
| (d) 邊緣柔化質心 frac=0.75（原始回合出貨） | 0.2892c PASS | 0.6562（增益只剩 0.34） | **否決** |
| (d) 同候選 frac=0.50 | 0.3292c PASS | 0.5556 | 否決 |
| (d) 同候選 frac=0.20（開發網格壓線前最窄） | 0.7997c PASS | 0.4024 | 否決 |
| (d) 同候選 frac=0.00（＝舊估計器） | 1.1721c FAIL | 0.5475（見 §5.3 說明） | （基準線） |
| (e) mean-shift 柔化 frac=0.50（5/15 迭代皆收斂到同一點） | 0.7167c PASS | 0.3134（仍比舊估計器同格的 0.115 差） | **否決** |
| Blackman-Harris 低旁瓣視窗（不加柔化） | 1.7516c FAIL | 0.4721 | 否決 |

完整 13 步 taper 掃描表、mean-shift 的 4 組 frac × 迭代次數數字、
Blackman-Harris 的對照數字，都在證據檔 STEP 5 step 1。結論：taper 越寬，
零偏差時的自證誤差越小，但真的有偏差時的增益缺口越大；taper 越窄，
兩者關係反過來——這條曲線上沒有一點能同時達到「自證 ≤1 cent」與
「增益不比舊估計器差」。mean-shift 把最差情況從 ~0.55-0.66 降到 ~0.31，
確實有幫助，但收斂到的固定點仍然比舊估計器差（同一格 0.687 對 0.885），
是縮小版的同一個缺陷，不是修好。

### 5.2 撤回後的全量重跑（全部 fresh 重跑，非沿用舊檔）

| 項目 | 撤回前（§0-§2 表格「舊估計器」欄位） | 撤回後 fresh 重跑 | 結論 |
|---|---|---|---|
| 自證：開發網格（1170點） | 1.1721c | **1.1721c** | 完全一致 |
| 自證：hold-out 網格（本輪同時修正 `HOLDOUT_T_ONSET_S`） | (原網格未測過偏差軸) | **1.0840c（新算，門檻 1.0 之上）** | 首次誠實量到 |
| `--selftest`（哨兵5件組） | PASS 5/5 | **PASS 5/5** | 一致 |
| `python -m pytest tests -q` | — | **262 passed, 1 skipped, 1 xfailed** | 全綠（1 個新增 xfail 為誠實揭露，見下） |
| HostProbe H6（5個 block size） | 5×(5 PASS/0 FAIL/0 UNVERIFIED) | **5×(5 PASS/0 FAIL/0 UNVERIFIED)，位元相同** | 一致 |
| corpus 30檔強域全綠子集 | 全部 0 FAIL | **全部 0 FAIL，逐檔 PASS/UNVERIFIED 數字相同** | 一致 |
| 月光 v4 | 2 PASS/40 FAIL/1101 UNVERIFIED | **2 PASS/40 FAIL/1101 UNVERIFIED** | 一致 |
| 給愛麗絲全曲 whole-file baseline（乾聲） | 8 PASS/34 FAIL/864 UNVERIFIED | **8 PASS/34 FAIL/864 UNVERIFIED** | 一致 |
| 給愛麗絲 stem_verify 乾聲全曲（905事件） | 671 PASS/22 FAIL/212 UNVERIFIED | **671/22/212（見 §5.4 說明：引用同碼徑既有檔，未重新執行）** | 一致（邏輯保證） |
| partial_verify 弱基頻22顆（informational） | pass=22/fail=0，max\|cents\|=10.8158 | **pass=22/fail=0，max\|cents\|=10.8158** | 一致（原本翻轉的 1 顆已翻回） |
| partial_verify 一般40顆partials（informational） | PASS 199/FAIL 38（共237顆），max\|cents\|=10.1099 | **PASS 199/FAIL 38，max\|cents\|=10.1099** | 一致 |

完整命令與逐行輸出見 `reports/gate_outputs/wf0909_C10B_estimator.txt` STEP 5
step 3；產物存於 `output/wf0909/C10B_fix/`。

### 5.3 一個誠實揭露：舊估計器本身也不是完美線性的

撤回不代表舊估計器完美——`gain_fidelity_scan()`（本輪新增的 informational
工具，見 §5.5）量到舊估計器在低音區（MIDI 36-37）、極端電平（−30 dBFS）
組合下，增益缺口最差也到 0.5475（例：真值偏移 +3c，量到 +1.354c）。這是
舊估計器原本就有、C10B 之前從未被要求修的既有限制（低 SNR + 窄頻帶的
估計器解析度問題），不是本輪造成的迴歸，撤回不會讓它變得更差，也不試圖
在本卡範圍內修它——留給未來若真的要處理 C10 的自證問題時一併考慮。

### 5.4 為什麼「給愛麗絲 905 事件 stem_verify」用既有檔而非重新執行

`stem_verify.py` 對這份 905 事件的譜跑完整逐事件分軌 + 疊加證明時，記憶體
用量隨事件數成長，本輪重新執行時觀察到 25 分鐘內飆到 28 GB 以上仍在爬升
（`stem_verify.py` 本身這輪完全沒被改動，是既有行為，非本卡引入）——為了
不冒著把本機記憶體榨乾的風險，中途 `taskkill` 了這個程序，改引用上一輪
產生的 `output/wf0909/C10B/fur_elise_dry_legacy.json`。

這不是用「應該會一樣」帶過：那份檔案是上一輪**直接在同一份未改動的
`stem_verify.py` 裡把 `measure_pitch_cents` monkeypatch 成
`measure_pitch_cents_legacy`** 跑出來的，而 `measure_pitch_cents()` 現在
**就是**（一行 `return measure_pitch_cents_legacy(...)`）呼叫
`measure_pitch_cents_legacy()`——兩者的數值輸出由
`test_measure_pitch_cents_matches_legacy_after_revert`（本輪新增，PASSING）
在整個 1170 點開發網格上逐點鎖定為位元相同。本節其餘每一項會經過同一段
程式碼（月光、corpus-30、H6、給愛麗絲 whole-file baseline、
partial_verify 弱基頻/一般40）本輪全部 fresh 重跑且逐一對上舊數字，是
這個引用的間接佐證。`stem_verify.py` 在大型（900+ 事件）譜上的記憶體
用量本身記入 open_items，留給未來的卡調查，本卡未觸碰、未修改。

### 5.5 本輪新增的工具與測試

- `tools/measurement_selfcal.py::gain_fidelity_scan()`——把稽核 blocker 2
  指出的「期望值固定、真值另外偏離」這條軸永久補進自證工具本身，
  informational（不新增容差），併入預設與 `--holdout` 兩種呼叫的輸出。
- `HOLDOUT_T_ONSET_S` 修正：原本 0.0533s 是 STFT hop 的 9.99375 倍，離整數
  倍只差 0.4 個 sample，事實上仍接近 hop 對齊；改成 0.0507s（9.50625 倍，
  小數部分 0.506，是離任何整數 hop 邊界最遠的點）。
- `tests/test_measurement_selfcal.py`：`test_holdout_grid_within_one_cent`
  改成 strict xfail（斷言本身沒動，只是誠實標注這是已知未解的缺口，而不是
  悄悄消失或被砍掉）；新增 `test_measure_pitch_cents_matches_legacy_after_
  revert`（鎖定撤回後兩個函式數值相同）與
  `test_gain_fidelity_no_regression_vs_legacy`（本輪抓到 §5.1 缺陷的方法，
  寫成迴歸測試：未來任何估計器改動的增益保真度都不得比舊估計器差）。

### 5.6 範圍與容差確認

`±5 cents` / `±10 ms`、`PITCH_TOL_CENTS`、`ONSET_TOL_S`、`BAND_REL_WIDTH`、
拒答規則 Ra–Re、course/detune 判定，本輪同樣一個字都沒動（R2）。
`git diff --stat` 只涉及卡上允許的 8 個檔案（見卡 §6 GATE 4）。

### 5.7 現況與待裁決

C10 的自證問題（開發網格 1.1721c、hold-out 網格 1.0840c，皆 > 1.0 cent
門檻）依然存在，卡狀態 **RED**。`reports/decision_packets/
C10_selfcal_domain.zh-TW.md` §5 記錄同一結論並列出仍待月月裁決的選項：
§2 選項 A（收窄主張域、不改程式碼，1.1721c 相對 ±5c 仍有 4.3 倍安全係數）
依然可行；選項 B 已經試過（本文件 + 上一輪記錄的全部嘗試，共五個候選）
並確認在目前架構（`band_of` 的 ±3% 硬邊界不能動）內無解；真正的選項 C
（架構外的新方法）尚未找到。
