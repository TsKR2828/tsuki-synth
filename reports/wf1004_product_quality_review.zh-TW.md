# WF1004 Q 卡：既有成品檔案品質總查（唯讀）

> 2026-10-07｜branch `fix/deep-physics-audit-20260716`（開工 HEAD `6198922`）｜對象：`exports/products/clean_batch2_v1_1_candidate/`（gitignored）、`E:\Tsuki-project\_tools\papers\`
> **全程唯讀**：products 與 papers 沒有任何寫入（`sha256sum -c` 前後相同，見 §2）。暫存放 `E:\Tsuki-project\_scratch\wf1004\Q\`（repo 外）。
> **這張卡沒有 GATE**：下面所有量測都是「資訊性」，沒有設任何門檻、沒有動任何容差（R2）。判斷只靠數字，沒有任何聽感判斷。
> raw 輸出與重跑腳本：`reports/gate_outputs/wf1004_Q_raw_*`（清單在 §8）。

---

## 0. 先直接回答月月的兩個問題

### 問題 (1)「資料夾內是不是有關於音效怎麼做才正確的論文（我記得有）」

**有，你的記憶是對的，但手上的那份是壞檔，而且「音效怎麼做才正確」比較貼近的是另一份文件。** 分三塊：

| 你可能指的 | 在哪 | 現況（數字） |
|---|---|---|
| **handpan（舌鼓同族）碩士論文** Alon 2015, York | `E:\Tsuki-project\_tools\papers\Alon2015_York_MSc_handpan.pdf` | **檔案只下載了 22.9%**：本機 5,259,264 B，原站 `Content-Length` 22,959,998 B。沒有 xref／trailer／`%%EOF`，PyMuPDF 與 poppler 都讀成 0 頁。`SHA256SUMS.txt` 只能證明「這個殘檔沒被改」，不能證明它完整。我從殘檔硬解出前 34 頁（摘要、目次、第 1 章、第 2 章到「Hang」那一節）；**第 4 章的量測（模態頻率比 Table 4.1、T60 Table 4.2、附錄 E／F）整段不在檔內**。（證據：`wf1004_Q_raw_york_pdf_truncation.txt`） |
| 「音效怎麼做才正確」的判準 | `docs/SOUND_DESIGN_KNOWLEDGE.zh-TW.md`（08-28 起草，已入庫） | 這不是論文，是「音效設計職業知識庫」：9 個來源，只有 1 本書（Viers, *The Sound Effects Bible*），其餘是業界部落格與 VNDev wiki。它把判準翻成 6 支檢查器（`loudness_check`、`loop_seam_check`、`spectral_band_report`、`attack_energy_ratio`、`duration_class_check`、`mud_ratio_compare`），**6 支全部沒有實作**（全 repo 只有這份 md 出現這六個名字）；文末 Opus 稽核留了 A1、A2 兩條中等問題，沒看到後續修訂。 |
| 物理模型的文獻溯源 | `docs/*_SOURCES.md`、`docs/D1…`、`docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md`；PDF 原檔在 `output/wf0907/R4/`（gitignored）等處 | 我掃了 `output/`、`external_data/`、`_tools/papers/`、`docs/`（不含 `output/wf0907/R3` 的軟體手冊）共 39 份 PDF：**真的可讀的文件 23 份、網站擋機器人／網頁擷取 14 份、殘檔 2 份（York、`goebl_diss.pdf`）**。那 23 份是鋼琴音板／鋼琴演奏、排練室聲學、MIDI 規格、指向性資料庫、授權書；舌鼓／handpan 專屬的只有上面那份殘檔。ICSV27 舌鼓論文（`output/wf0907/R6/icsv27.pdf`）只有 5,928 B，是網站擋機器人的頁面，**不是論文**。D10（Hall 1988、Chaigne & Askenfelt 1994）仍在付費牆後（`DEVLOG.md:192`），沒取得。（`wf1004_Q_raw_pdf_inventory.txt`） |

補充：「handpan＝tongue drum 同族」只對一半。論文談的 handpan 是半球殼上的音區（前三個模態調成 1:2:3）；引擎的 `tongue_drum`／`beam` 是**固支－自由的懸臂梁**（理論頻率比 1 : 6.267 : 17.548 : 34.386）。判準只能部分轉移，見 §4。

### 問題 (2)「是不是原本就有反推有效程度的審核方式」

**有，而且是這個專案從 2026-06 就定下的核心做法**（`ROADMAP_PHYSICS.md` §0：「聾人與 AI 用物理理論驗證聲音，不靠聽」）：從渲染出來的 WAV 反向量測 f0、泛音、T60、音高與起音時間，再跟模型預測或宣告值比。對應工具與它自己的「有效程度」數字：

- `physics_verify.py`（f0 ±5 c、partial 頻率 2–4%、振幅 ±3 dB、T60 比 0.80–1.25、力度×2＝+6±1 dB、殘差 −60 dB；另有跟 C++ 表格無關的特徵值錨點 F1）。
- `melody_verify.py`／`stem_verify.py`／`partial_verify.py`：從 WAV 反推「每個音在不在宣告的時間、音高對不對」（onset ±10 ms、pitch ±5 c）。
- **量測器自己的有效程度**：`measurement_selfcal.py` 用已知答案的合成訊號校準量測器：持續段誤差 ≤1.18 c，放鍵／阻尼段約 7.2 c；月月原訂的 ≤1.0 c **從未達成**（五條 strict xfail 刻意留著，`ROADMAP_PHYSICS.md` §6、`EARFREE_MELODY_GATE_DESIGN` §8.5／§9）。
- `verify_score.py --all`：75/75 通過，43 個商品音效的 score 全在裡面（`wf0925_K1_verify_score_all.txt`：library 43/43 PASS）。

**但它驗的不是「商品 WAV 好不好」**，邊界要看清楚（§1 逐項）：
1. 它驗的是「渲染結果 ＝ 模型自己的預測＋獨立的解析解」，**沒有任何真實樂器量測當錨**（`TODO` D7 實體試體量測沒做；`specimen_verify.py` 只有契約與樣板，沒有資料）。
2. 物理 GATE 一律「效果全關」；商品音效全部有 reverb（43 個都有，catalog／score 可查），所以**商品 WAV 本身不在物理主張範圍內**（`ROADMAP_PHYSICS.md` 驗證域表：效果鏈 ❌ 域外）。
3. 沒有人耳驗證；沒有 DC、單聲道相容、頭尾突兀、頻譜平衡這類「音效交付品質」檢查（§1 表末列）。

---

## 1. 既有審核鏈盤點：驗了什麼、怎麼驗、沒驗什麼

> 讀過：`QA_REPORT.md`、`LISTENING_CHECKLIST.md`、`CHANGES_v1_1.md`、`catalog_v1_1.csv/json`＋`catalog_v1_1_FIELDS.md`、各 manifest、`scripts/x1_*`／`x2_*`／`xf_*`（檔頭與核心檢查）、`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md`、`SOUND_DESIGN_SPEC.md`、`SOUND_LIBRARY_PLAN.md`、`docs/SOUND_DESIGN_KNOWLEDGE.zh-TW.md`、`tools/verify_score.py`／`physics_verify.py` 檔頭。
> 注意：`SOUND_DESIGN_SPEC.md` 與 `SOUND_LIBRARY_PLAN.md` **不是審核標準**：前者是分類／命名規格（主大類、OneShot／Loop／Variant、檔名規則），後者是 43 個音效的製作計畫（引擎、材質配置、實作步驟）；兩份都沒有品質判準。

| 層 | 工具／證據 | 驗了什麼 | 怎麼驗 | **沒驗什麼** |
|---|---|---|---|---|
| A 引擎 vs 理論 | `physics_verify.py --full`、`--selftest`（14/14） | f0（±5 c）、泛音頻率比、振幅、T60（0.80–1.25）、力度律、殘差能量（−60 dB）、特徵值錨點 | 單音探針 → 效果全關渲染 → FFT／窄帶包絡 → 對模型 `--dump-modes` 與獨立解析解 | 真實樂器（D7 未做）；有效果的 WAV；FM 域外；rubber 三例 N/A；舌鼓 T60 靠 ×2 經驗係數，**無文獻錨點**（`ENGINE_DOMAIN_CLAIMS` §6） |
| B 整曲 | `verify_score.py --all`（75/75） | schema、模態表健全（2b：驗的是 dump 不是音訊，f0 偏差 0.002 c 這種數字是模型對平均律）、休止區 ≤ −50 dBFS、**母帶**峰值 ≤ −0.3 dBFS 且無連續削波、同機決定性 | 一次渲染＋一次 dump，比 sha256 | 交付檔（母帶之後還乘了增益、轉檔）；音高／起音（交給 C）；響度；接縫；頻譜；DC |
| C 旋律位置 | `melody_verify`（L1）、`stem_verify`、`partial_verify`（資訊性）、HostProbe（L2）、Cubase（L3） | 每個事件在宣告時間（±10 ms）響起、音高在 ±5 c | 從 WAV 反推 onset／f0（分軌乾聲）；量測器自證 | 有殘響／效果的音（§8.3 著色）；f0<167 Hz 起音；放鍵段（~7.2 c）；泛音「不可宣稱已驗證」；商品音效不是這條鏈的對象 |
| D 商品層 | `x1_*`（響度／loop／TPDF／試聽帶）、`xf_*`（loop 事實 31/31、三支量測器、recheck 20/20）、`x2_verify.py`（179/179） | 原版 212 檔未動；zip 成員逐位元＝來源；重打決定性；文字沒有被點名的錯誤說法；loop 長度 0 樣本誤差；tail-wrap 在「套增益前」與重播模擬逐樣本一致；TPDF 可重現 | ffmpeg 8.1.1＋自寫腳本；文字用 grep 核對 | 峰值上限（**只有 X1 那支量測器判定**，其他量測器最多差 0.065 dB，QA §2 已寫明）；DC、單聲道、頭尾、頻譜、人耳 |
| E 人耳 | `LISTENING_CHECKLIST.md`（22 題）＋試聽包 zip | 接縫喀聲、起音爆音、失真、16 顆弱基頻 | **還沒有人做**（Q28 待月月） | README 自己寫「接縫沒有經人耳確認」 |
| F 外部判準 | `SOUND_DESIGN_KNOWLEDGE.zh-TW.md` §8 六支檢查器 | — | **未實作** | 全部 |

---

## 2. 既有鏈重驗結果（全部重新跑，不沿用舊結論）

證據：`wf1004_Q_raw_manifest_check.txt`、`wf1004_Q_raw_analysis.txt`、`wf1004_Q_raw_markers_and_readme_check.txt`。

| 項目 | 結果 |
|---|---|
| `_CANDIDATE_MANIFEST_SHA256.txt`（85 行） | 84 OK、**1 FAILED：`QA_REPORT.md`**。這是已宣告的 XF 文字修改（`CHANGES_v1_1.md` XF 段、`x2_verify.py` 的 `XF_EDITED_X1_FILES`）；`_X2_MANIFEST_SHA256.txt` 第 9 行記的是現行值 `149bab69…`，與磁碟相同。**不是新問題。** |
| `_X2_MANIFEST_SHA256.txt`（56 行） | 56/56 OK |
| 原版 212 檔（`_ORIGINALS_SHA256_before.txt` 對 `clean_batch2/`） | 212/212 OK |
| `_pre_WF1002_backup_SHA256.txt` | 19/19 OK |
| 磁碟上有、兩個 manifest 都沒記的檔 | 只有兩個 manifest 本身（`comm` 比對） |
| 4 個 zip | `testzip` 全 None；SE 51／Fab 50／專輯 15／試聽包 18 個成員；SE、Fab、專輯 zip 的每個成員 sha256＋大小＝`PACKAGES_MANIFEST_v1_1.txt` 逐列（51＋50＋15 列 0 不符）；zip 檔本身 sha256＝manifest 標頭 |
| 專輯 MP3 7 個 | sha256 ＝ `clean_batch2/preview/music/` 的 v1.0 檔（與 README「沿用 v1.0、沒重出」一致） |
| catalog vs 實檔（43 音效） | `duration_s` 對 WAV 樣本數÷取樣率：43/43 在 0.6 ms 內（最大差 0.479 ms，Akashic Library Drone，是 catalog 只存 3 位小數）；`dist_sha256` ＝ zip 成員 sha256：43/43 |
| catalog loop 欄（6 個） | `loop_ready_samples`、`loop_ready_sha256` 對 zip 成員 6/6 相同；N＝⌊小節×4×60×48000÷BPM＋0.5⌋ 重算 6/6 相同（Rabbit：164,571） |
| catalog 專輯欄（7 首） | `album_v1_1_wav_sha256` ＝ zip 內 WAV 7/7；`duration_s` 對實檔 7/7 在 4 ms 內（取小數 2 位） |
| **catalog 欄位限制** | catalog **沒有**取樣率、位深、聲道欄位，這三項只能對 README／文案的宣稱比（見下一列）。 |
| 格式宣稱（README／LISTING：48 kHz／24-bit／立體聲；專輯 44.1 kHz／16-bit／立體聲） | soundfile 與 ffprobe 兩邊讀：SE 49 個 WAV 全是 48000／2ch／pcm_s24le、`nb_samples`＝幀數；專輯 7 個全是 44100／2ch／pcm_s16le |
| README 檔案清單（49 列）vs zip | 49 列都在 zip、zip 的 49 個 WAV 都有列；秒數照「只捨入一次」重算全對；loop 表 18 格（original／loop-ready 秒數）全對 |
| README「最大瞬時響度 −28.4～−5.4 LUFS」 | 重量 −28.357～−5.357（ebur128 400 ms，尾端補 0.5 s），四捨五入同 |
| 專輯 README「−13.98～−14.35 LUFS」 | ebur128 讀 −13.9～−14.3（1 位小數；loudnorm 與 ebur128 差約 0.03 LU，QA §7-4 已記） |
| 草稿標記清點 | 見 §2.1 |

### 2.1 草稿標記現況（買家會看到的 vs 內部文件）

| 檔 | `[TBD` | 說明 |
|---|---|---|
| **SE zip 的 `LICENSE.txt`（買家會拿到）** | 14 行（2 行方框說明＋12 處正文：第 1、8、9、12 條 × 三語） | 檔頭方框寫「DRAFT … NOT LEGAL ADVICE … Do not ship as-is」（`LICENSE.txt:1-10`），與 `LICENSE_SE_PACK_v1_1.txt` 同 |
| SE／Fab／專輯 zip 的 `README.txt` | 0 | 第一行都是「[v1.1 CANDIDATE - pending approval …]」；SE README 有一句「接縫沒有經人耳確認」 |
| **專輯 zip** | 沒有 LICENSE 檔 | 成員只有 7 WAV＋7 MP3＋README；`LICENSE_ALBUM_v1_1.txt` 在 repo 內有 16 處 ASCII `[TBD`、「TBD」字樣共 42 處（三語，含全形［TBD］；含第 5 條影片 BGM 的 A／B 案） |
| `LISTING_COPY_v1_1.md` | 0 `[TBD`，8 處「待月月」 | 價格等 |
| `PRODUCT_SHEET_v1_1.md` | 3 `[TBD`、8 處「待月月」 | 內部 |

---

## 3. 獨立重量（49 個 SE WAV＋7 個專輯 WAV）

量法：自己的腳本，不用 X1／XF 的程式：真峰值用 scipy `resample_poly` 4×／8×／32×（短檔三個都量，長檔 4×／8×）；整合／瞬時響度用 ffmpeg ebur128；削波用整數碼（24-bit 8388607、16-bit 32767）；其他用 numpy。腳本與原始 JSON 在 `wf1004_Q_raw_script_q_measure.py`、`wf1004_Q_raw_se_measure.json`、`wf1004_Q_raw_album_measure.json`。

### 3.1 真峰值：對照 README 的「−1 dBTP」

| 集合 | 我的量測範圍（三個倍率取全部） | README 宣稱 | 讀數 > −1.000 的檔數 |
|---|---|---|---|
| SE 音效 43 | **−1.0544 ～ −0.9489** dBTP；取樣峰值 −1.3455 ～ −1.0455 dBFS | −0.949 ～ −1.048（三支量測器） | 8／43（任一倍率）；8× 也是 8 |
| SE loop-ready 6 | −1.0008 ～ −0.9941 | −0.996 ～ −1.002 | 6／6（任一倍率）；8× 時 5／6 |
| 專輯 WAV 7 | −1.8200 ～ −0.9915 | −1.00 ～ −1.83（「WAV, full precision」） | 4／7（8× 全部 > −1.000） |
| 試聽帶 WAV | −1.1646（4×）／−1.1556（8×）；取樣峰值 −1.2515 | QA §6 寫 −1.173（X1 量測器） | 0 |

**這是 `WF0925_README.md` §7-8 第 5 點與 `TODO.md:79` 已記的同一個議題，不是新發現**：
- 該議題的實例我重現了：Clockwork Ticking Room 在 32× 讀 −0.9489（README 上限寫 −0.949，高 0.0001 dB；既有記錄 −0.94886／+0.00014 dB）；Forest Bird Call 在 4× 讀 −1.0544（既有記錄「下緣 4 倍 −1.0544」）。
- **同類但量級略大、README 沒寫到的**：loop-ready 6 檔最高 −0.9941（README 上緣 −0.996，高 0.0019 dB）；專輯 4 軌讀 −0.9915～−0.9966（高於 −1.000 最多 0.0085 dB），而專輯 README **沒有**「讀數隨量測器」那句註記（SE README 有）。
- 沒有任何 WAV 的真峰值高於 −0.9489 dBTP；56 個 WAV 的取樣峰值都 ≤ −1.0000009 dBFS（最高的是 Forest Rain Pattern 與 Ocean Wave Cycle 的 loop-ready，整數碼 7,476,354）。
- 取樣峰值幾乎都剛好 −1.0455 dBFS：43 個音效大多是「母帶 −0.446 dBFS 再固定增益 −0.6 dB（0.1 dB 解析度取整）」的結果（`QA_REPORT.md` §7-1、`CHANGES` §9-6 已解釋）。
- 專輯 MP3（沿用 v1.0）解碼後真峰值：Complete −0.944、Cimbalom −0.948、M3 −0.984、Für Elise −0.986、M1 −1.790、M2 −1.302、M4 −1.159（README 沒寫 MP3 的峰值，只是記下）。

### 3.2 削波／DC／頭尾／立體聲

| 項目 | 結果（全 56 個 WAV；細表在 `wf1004_Q_raw_analysis.txt` §E、`wf1004_Q_raw_extra.txt` §H–J） |
|---|---|
| 削波 | **0 個樣本碰到滿刻度**（24-bit／16-bit 整數碼）；「連續相同值且 ≥ 0.5 滿刻度」最長 2 個樣本（Ocean Abyss Hum、Depth Slam、Wave Cycle、Restraint Iron Drone，低頻波峰頂端，峰值 −1.05 dBFS，不是削波） |
| DC | 全檔平均 −88 ～ −48 dBFS。**多數是起音後會衰減回零的低頻位移**（例：Restraint Lock Click (Distorted) 四等分 −42.2／−77.6／−97.7／−127.4 dBFS）。**例外**：Restraint Industrial Pulse 的 loop-ready 版全程不衰減（四等分 −48.1／−47.8／−48.5／−48.9 dBFS，約 +0.004 滿刻度）。鏈上沒有任何 DC 檢查。 |
| 開頭 | 49 個 SE 檔，第 1 個樣本全都不是 0（沒有靜音前導）；第 1 個樣本相對該檔峰值：一次性音效裡 11／43 在 −35 dB 以上，最大的 Lock Click −26.3 dB（但它第 1 擊較輕，峰值在 51 ms）、Bolt Click −26.5 dB（峰值 1.8 ms）、Ding Angry −28.1 dB（0.48 ms）、Bell Strike −30.8 dB（0.54 ms）、Gear Click −32.5 dB（0.60 ms） |
| 結尾 | 一次性音效最後一個樣本最高：Bolt Click −75.9 dBFS、Droplet Tap −77.4、Bubble Pop −83.1、Tick Loop −83.6；其餘 ≤ −92 dBFS（未淡出但量級極小）。loop-ready 6 檔本來就不收在靜音（最後 10 ms RMS −30.5 ～ −53.7 dBFS） |
| 立體聲 | 49 個 SE 檔沒有一個是雙單聲道（L/R 相關 −0.47 ～ +0.96）。**單聲道摺疊**（(L+R)/2 相對平均聲道 RMS）：最差 Ocean Tide Wash −5.04 dB（相關 −0.473）、Ocean Wave Cycle＋loop-ready −4.65 dB、Akashic Library Drone −4.63、Restraint Iron Drone −4.01、AI Radiance M4 −3.65；56 個檔裡相關為負的 9 個。鏈上沒有單聲道相容檢查。 |

### 3.3 loop-ready 接縫（描述；「聽起來會不會喀」這張卡判不了）

1. **長度**：6／6 ＝ N 小節整數樣本（768000／164571／230400／576000／384000／192000）。
2. **接縫跳差與百分位**：我獨立重算的接縫跳差（0.00070／0.00324／0.01823／0.00530／0.00010／0.03034）與「檔內相鄰差百分位」（Akashic 22.0%／Rabbit 1.4%／Restraint 77.8%／Forest 44.7%／Ocean 4.6%／Clockwork 52.7%）**6／6 與 `QA_REPORT.md` §3 表逐格相同**。
3. **接縫曲率與高頻突發**（我新加的描述量）：接縫處二階差分（曲率）≤ 該檔內最大曲率的有 5／6；Clockwork 是 0.51471，比檔內最大 0.51421 高 0.1%，因為接縫正好是第 1 拍起音（檔內最大曲率也是那個起音）。接縫前後 ±1 ms 的高頻能量，相對**該檔最響的 2 ms 窗**都低（−2.7 ～ −26.8 dB），相對**該檔中位數 2 ms 窗**則 Ocean／Akashic 低 3～5 dB、Rabbit／Restraint／Forest／Clockwork 高 2.4／5.6／8.7／16.4 dB（＝起音）。意思：接縫沒有出現比該檔自己的起音更突兀的高頻事件。這**不等於**聽不到喀聲。
4. **tail-wrap 與原版的關係（獨立重推）**：把 zip 內「原版」每 N 樣本疊回開頭，再用最小平方擬一個常數增益，殘差：擬合增益 +0.0320 ～ +0.0522 dB（README「原版小聲 0.03～0.05 dB」✓），最大殘差 **1.97 ～ 2.00 LSB24**（`CHANGES` XF 段「1.97～2.00」✓），6／6。
5. 以 `SOUND_DESIGN_KNOWLEDGE` §5 的四點對照：(1)(2)「起點與終點接近 0」**不成立**（loop-ready 首樣本絕對值 0.0025～0.0722、末樣本 −25.4 ～ −52.4 dBFS，不是零交越；該文件自己的稽核已指出零交越不是充分條件，且容差「待定」）；(3) 一階差分連續性：跳差都在檔內相鄰差分布內，**成立**；(4) 頻譜連續性：見上一點，**只做了描述**。

---

## 4. 論文對照（資訊性；不是 GATE，不碰容差）

**先講限制**：York 論文本機殘檔只有前 34 頁。能引用的只有它的背景章（多數是它引用別人的結果），**它自己量到的模態頻率比與 T60 都讀不到**。引述只用意譯。

### 4.1 能抓到的「正確性判準」（出處：殘檔第 2 章，印刷頁碼約 20～34）

| # | 論文敘述（意譯） | 出處位置 | 可量化嗎 |
|---|---|---|---|
| P1 | steelpan 每個音的前三個主要模態調成 1:2:3；Hang 的音區主要模態同為 1:2:3（F3 的 174／348／520 Hz） | §2.1.4、§2.1.5（引 Achong、Wessel 等，不是作者自測） | 可：模態頻率比 |
| P2 | 金屬條（glockenspiel 類）的泛音是非諧波的，衰減快、對音色影響小 | §2.1.2 | 只能定性（方向可查） |
| P3 | 兩個接近頻率的簡諧振動產生拍頻，拍頻＝頻率差；純音差 < 12.5 Hz 時聽得到拍 | §2.1.1.3（引別人） | 可，但屬耦合／分裂模態現象 |
| P4 | handpan 的 T60、模態頻率比實測值 | 第 4 章 Table 4.1／4.2、附錄 E／F | **不在檔內** |

### 4.2 對 tongue drum 類商品 WAV 的資訊性量測

對象：12 個 `beam`／`tongue_drum` 單事件商品 WAV（Light Tap、Bell Strike、Gear Click、Acorn Tap、Droplet Tap、Bubble Pop、Bubble Pop Deep、Ding、Ding Angry、Carrot Button、Bolt Click，以及 Library Opening Bell 的第一個音 D4）。模型預測用商品母帶當年的渲染器（`exports/renderer_archive/TsukiSynthCLI_9123db8f_build20260915.exe`）`--dump-modes`（唯讀）；與目前 build 的 dump 完全相同。獨立錨點：固支－自由梁特徵值 βL＝1.8751041／4.6940911／7.8547574／10.9955407／14.1371684（`physics_verify.py` 內的獨立常數）推出的頻率比 **1 : 6.2669 : 17.5475 : 34.3861 : 56.8426**。商品 score 全部用預設懸臂邊界（沒有 `beam_boundary` 覆寫）。證據：`wf1004_Q_raw_tongue_table.txt`、`wf1004_Q_raw_tongue_drum.json`。

| 判準 | 結果 | 判定 | 為什麼 |
|---|---|---|---|
| P1 模態頻率比 1:2:3 | 能量夠大（相對基頻 > −50 dB）的第二模態有 10 個檔量得到：頻率比 6.262 ～ 6.365（模型 6.267）；第三模態有 3 個檔：17.568／17.673／17.572（模型 17.547）；Bolt Click 第四模態 34.366（模型 34.386）；另 2 個檔（Bubble Pop、Bubble Pop Deep）第二模態低於 −50 dB 量不到。模型 `--dump-modes` 的模態表裡沒有 2× 或 3×。商品 WAV 在 2×／3× 附近有 −39 ～ −48 dB 的小峰（Acorn Tap、Carrot Button 是一整串間隔 3～10 Hz 的連續裙邊；Bell Strike、Gear Click 各 1 個 3× 小峰 −45／−47 dB；Opening Bell 2 個 2× 小峰 −43／−48 dB），來源沒查（可能是瞬態裙邊、激發器接觸頻譜或殘響），不是模型裡的離散模態 | **偏離（設計如此）** | 引擎是懸臂梁，不是殼面音區，論文判準不適用；**同時符合獨立的懸臂梁特徵值錨點**：那 10 個第二模態頻率比與 6.2669 的差 −0.07% ～ +1.6%（最大是 Carrot Button，該模態 T60 只有 0.015 s，FFT 窗內幾乎是瞬態），落在專案登記的 partial 頻率容差 2–4% 內；第三模態 +0.12% ～ +0.72% |
| P2 金屬條泛音衰減快 | 模型側（dump）：12 個檔第二模態 T60／基頻 T60＝0.04 ～ 0.15（Ding 0.041、Ding Angry 0.045、其餘 0.09 ～ 0.15）；商品 WAV 第二模態相對基頻的量到電平：10 個量得到的檔在 −7 ～ −47 dB（金屬槌的 Bell Strike／Gear Click 只低 7／9 dB） | **方向符合（模型側）；商品 WAV 側無法判定** | 商品 WAV 帶 reverb（43 個都有，這 12 個 wet 0.08 ～ 0.45、decay 0.3 ～ 6.0 s），窄帶包絡斜率量到的 T60 與模型值的比，23 個讀數從 0.08× 到 42×（例：Acorn Tap 基頻量到 1.55 s、模型 0.097 s；Bell Strike 第二模態量到 5.2 s、模型 0.123 s），無法分離模態衰減與殘響，這不是量測器壞掉，是商品本來就有殘響。「對音色影響小」是聽感主張，量不到 |
| P3 拍頻 | 不適用 | **無法判定** | `beam` 是單一梁、沒有耦合音區，模型不產生分裂模態；FFT 在基頻旁 3～11 Hz 的小峰是窗函數旁瓣與殘響，不能當拍頻 |
| P4 T60 與頻率比實測值 | 讀不到 | **無法判定** | 檔內沒有第 4 章。**專案內已記**：舌鼓 BeamModel 衰減式的 `*2.0` 是「DECIDED CONVENTION，經驗係數，無文獻錨點」（`ENGINE_DOMAIN_CLAIMS` §6），所以舌鼓類商品的衰減時間（例：Bolt Click 基頻模型 T60 22.6 s、Library Opening Bell D4 14.4 s）目前**沒有任何文獻對照** |
| （附帶）基頻 vs 宣告音高 | 12 個檔兩種估計器（FFT 峰值內插；窄帶解析訊號瞬時頻率）**只有 6 個彼此差 ≤ 2.1 c**（Ding −0.3／+0.4 c、Ding Angry +1.2／+1.0、Acorn Tap −1.6／−0.1、Droplet −3.3／−1.2、Bolt Click +0.1／+1.0、Opening Bell −3.4／−3.3），這 6 個都在宣告音 ±3.4 c 內；其餘 6 個兩估計器差 2.3 ～ 11.5 c（最大是 Carrot Button −11.4／+0.1 c；Bubble Pop 的窄帶估計器改用 ±6% 頻寬時甚至讀到 −29.3 c） | **6 個符合 ±5 c；6 個無法判定** | 短促、衰減快、帶殘響的音，超出量測器自證範圍（自證只涵蓋持續段 ≤1.18 c，放鍵／阻尼段 ~7.2 c，`EARFREE` §8.5），所以 3.8～5.0 c 或更大的讀數**不能**拿來說渲染正確或錯誤 |

AI Radiance 的 M1／M3／M4 也含 `tongue_drum` 事件（16／16／32 個），但混在多引擎織體裡，沒有做單音量測，這裡記「未量」。

---

## 5. Findings（按嚴重度；每條附數字與出處）

### 5.1 擋上架

> 判定基準：**若現在把候選版原樣上架會出問題**的項目。**音訊本體這次重量沒有查到任何擋上架的問題**（0 削波、格式與宣稱相符、sha256 全對、catalog 與實檔一致）。下面兩條都是已知項，不是新發現。

| # | 對象 | 事實 | 出處 |
|---|---|---|---|
| B1 | **音效包 SE zip（BOOTH／itch 版）** | 買家會拿到的 `LICENSE.txt` 仍是草稿：檔頭方框「Do not ship as-is」、**12 處正文 [TBD]**（第 1 授權通路、第 8 終止後已發佈作品、第 9 準據法與法院、第 12 聯絡方式，各三語）；zip 檔名帶 `_candidate`；README 第一行「[v1.1 CANDIDATE - pending approval]」。`x2_build_packages.py --release` 設計上會拒絕這種狀態。 | zip 成員 `LICENSE.txt:1-10,23,84,88,101,…`；`HANDOVER.md` §1-1 第 3–4 項；`CHANGES_v1_1.md` §0 表第 3 項 |
| B2 | **專輯 zip** | zip 內**沒有授權檔**；README 寫「影片 BGM 可以」＝授權第 5 條 A 案，但 A／B 案還沒裁；`LICENSE_ALBUM_v1_1.txt`「TBD」字樣共 42 處（三語）。只擋專輯，不擋音效包。 | 專輯 zip 成員清單；`CHANGES_v1_1.md` §0 第 6 項 |

### 5.2 建議修

| # | 對象 | 事實（數字） | 建議 | 出處 |
|---|---|---|---|---|
| R1 | 專輯 README 真峰值句 | 寫「−1.00 to −1.83 dBTP (WAV, full precision)」；獨立量測 4／7 軌讀 −0.9915 ～ −0.9966（> −1.000，最多高 0.0085 dB）。SE README 已有「同檔在不同量測器最多差 0.07 dB」註記，專輯沒有。 | 專輯 README 三語補同一句量測器註記（只是文字，不動音檔）；屬 R2 邊界，由月月決定 | §3.1；`QA_REPORT.md` §2 XF 補註 |
| R2 | SE README／LISTING 的 loop-ready 真峰值範圍 | 寫 −0.996～−1.002（三支量測器）；第四支量測器讀 −0.9941～−1.0008，6／6 在 32× 讀 > −1.000，高於 README 上緣最多 0.0019 dB。與 `TODO.md:79` 已開著的「−0.94886 寫法」是同一件事，這次補一個 loop-ready 的實例。 | 併入 `TODO.md:79` 那一條處理 | §3.1；`TODO.md:79` |
| R3 | 專輯 README「由 TsukiSynth 物理模型引擎演奏」 | AI Radiance 三個樂章含非物理的 `fm` 事件（M2：4、M3：32、M4：12）與半域內的 `custom` 事件（M1：12、M2：18、M4：6）；Complete Suite 是以 `layers` 疊這四個樂章的 score（`crossfade_ms` 1400）。買家 README 沒標；`PRODUCT_SHEET`／`LISTING_COPY` C 段有寫「FM 電鋼」。R9 要求域外功能在文件標註。 | 專輯 README 加一句「部分樂章含非物理的 FM 音色」 | `scores/originals/ai_radiance/*.score.json`（grep 引擎計數）；`ROADMAP_PHYSICS.md` 驗證域表、R9 |
| R4 | 外部判準的檢查器全未實作 | `SOUND_DESIGN_KNOWLEDGE.zh-TW.md` §8 列了 6 支檢查器（高優先：`loudness_check`、`loop_seam_check`），全 repo 零實作；該文件仍標 draft，稽核的 A1（§3 引號句無出處）、A2（§5 把零交越稱「充分條件」）兩條中等問題沒修。鏈上因此沒有 DC、單聲道、頭尾、接縫的任何檢查（§3.2、§3.3 我是臨時量的）。 | 先把 `loop_seam_check`（§3.3 四點）、`loudness_check` 做成**資訊性**工具（該文件 §8 自己定的上線方式）；常數要走月月核准（R4／R2）；修 A1／A2 | `docs/SOUND_DESIGN_KNOWLEDGE.zh-TW.md` §8、稽核記錄 B 段 |
| R5 | 聽人把關仍是 0 | 22 題答題卷＋試聽包（`TsukiSynth_listening_kit_v1_1.zip`）已備，沒有人做過；所有「會不會喀」「失真像不像壞掉」的結論都還是空的（README 也自己寫了「沒有經人耳確認」）。 | Q28（月月）：不擋音效包，但它是**唯一**覆蓋「聽起來是否瑕疵」的一層 | `LISTENING_CHECKLIST.md`、`HANDOVER.md` §1-1 |
| R6 | 試聽包 A 組選的起音檔 | A 組 3 檔（Stomp、Spring Release、Shackle Slam）第 1 個樣本相對峰值是 −58.8／−51.4／−53.6 dB（很緩）；而一次性音效裡有 11 檔第 1 個樣本在 −35 dB 以上（Bolt Click −26.5、Ding Angry −28.1、Bell Strike −30.8、Gear Click −32.5、Lock Click −26.3，峰值在 0.5～1.8 ms 的就有 Bolt Click、Ding Angry、Bell Strike、Gear Click 四個）。A 組是依「峰值落在開頭」選的，沒涵蓋這些。 | 若要補人耳題，優先加這 4 個 | §3.2；`LISTENING_CHECKLIST.md` §1 A 組 |
| R7 | 論文殘檔 | `_tools/papers/Alon2015_York_MSc_handpan.pdf` 只有 22.9%（5,259,264／22,959,998 B）；`README.txt` 把 5,259,264 B 當成原檔大小記錄、`SHA256SUMS.txt` 只驗殘檔。 | 重新下載完整檔（22,959,998 B；遠端 `Content-MD5` 十六進位 `7526a6e8c0d272a9182191fcfeb1c898`，可用來驗）。**下載要月月同意**；我只做了一次 HTTP HEAD，沒下載。下載完還要在 README 記實際大小，`SHA256SUMS.txt` 重算。 | `wf1004_Q_raw_york_pdf_truncation.txt`；`_tools/papers/README.txt` |

### 5.3 資訊性

| # | 事實 | 出處 |
|---|---|---|
| I1 | 重量與既有記錄的對得上：接縫百分位 6／6、tail-wrap 殘差 1.97～2.00 LSB24 6／6、README 秒數 49 列＋18 格、maxM 範圍、catalog 長度／sha 43／43、loop 長度 6／6。**沒有任何一項新的不一致。** | §2、§3.3 |
| I2 | 單聲道摺疊：8 個 SE 檔＋專輯 M4 相關為負；最差 Ocean Tide Wash 摺成單聲道小 5.04 dB。遊戲／手機單聲道播放時，海洋類長音會明顯變小聲。沒有任何文件宣稱單聲道相容。 | `wf1004_Q_raw_extra.txt` §H |
| I3 | DC：Restraint Industrial Pulse loop-ready 全程約 +0.004（−48 dBFS）。起因是該 score 的 overdrive（wet 0.4、drive 0.3）加 plate／iron，不衰減，在循環中是恆定偏移；量級小，只記錄。 | §3.2 |
| I4 | `beam` 類商品的衰減時間（舌鼓類）沒有文獻錨點（`*2` 經驗係數），商品文案已寫「減衰パラメータは推定値」，說法與現況一致。 | `ENGINE_DOMAIN_CLAIMS` §6；`LISTING_COPY` A 段 |
| I5 | `SOUND_DESIGN_KNOWLEDGE` 候選判準的商品數字（不設門檻、只印）：UI 類（catalog `primary_type`＝ui）19 檔，檔長 0.51～29.6 s、包絡掉到 −40 dB 的時間 0.17～5.96 s（Gear Click 0.17、Acorn Tap 0.22、Carrot Button 0.22、Light Tap 0.38 s 等 4 檔 ≤ 0.4 s；該文件只有 UI「micro-interaction 100–300 ms」一條硬數字，且不適用 Bell／Chime 類）；`mud_ratio`（250–500 Hz 能量占比）中位數 0.7%、最大 79.0%（Gate Open），調性音的占比其實就是音高所在頻段，單一批次沒有同類基準，**無法判定**。 | `wf1004_Q_raw_sound_design_checks.txt` |
| I6 | 這張卡額外查到：39 份 PDF 中 14 份是網頁擋頁／擷取（其中 12 份是 2～12.6 KB 的擋機器人頁面，含 `output/wf0907/R6/icsv27.pdf`；另 `mcgill_amplitude.pdf` 382 KB、`uncg_practice.pdf` 24 KB 是網頁擷取），`goebl_diss.pdf` 也是殘檔（1,535,950 B、PyMuPDF 0 頁；同目錄 `goebl_diss2.pdf` 完整 194 頁）。這些都在 gitignored 的 `output/`，不是穩定存放處。 | `wf1004_Q_raw_pdf_inventory.txt` |
| I7 | 專輯 MP3 沿用 v1.0，與 TPDF 版 WAV 不同源（README 已寫明）；MP3 與 WAV 時長逐位相同（ffprobe 到 3 位小數）。 | `wf1004_Q_raw_extra.txt` §K |

---

## 6. 沒做、做不到的

- 沒有人耳判斷；沒有改任何商品檔、論文檔、容差、程式碼；沒有 git add／commit／push。
- 沒有重渲染任何音訊（模型預測用 `--dump-modes`，只印不寫）。T60 在商品 WAV 上無法與乾聲模型值直接比，若要比必須重渲「效果全關」版本，那是新渲染，不在本卡範圍。
- York 論文第 4 章（模態頻率比與 T60 實測表）讀不到；ICSV27 舌鼓論文、Zoghaib & Mattei 2013、Van Eysden & Sader 2007 仍未取得（`_tools/papers/README.txt`）；D10 付費牆文獻仍未取得。
- 商品圖草稿（`art/`）、授權文字的法律內容、DistroKid 流程不在本卡範圍。
- catalog 沒有取樣率／位深／聲道欄位，這三項只對 README／文案宣稱比。

## 7. 一句話結論

音訊檔本身的數字與文件宣稱一致，沒有削波、格式沒錯、雜湊與 catalog 全對；**會擋上架的只剩授權草稿與候選標記（已知）**。既有審核鏈很完整地驗了「模型自洽＋打包無誤＋文字不誇大」，**沒驗的是交付品質的外圍（DC、單聲道、頭尾、接縫的程式化檢查）與人耳**；論文那份是殘檔，要重下載才能談 handpan 的實測判準。

## 8. 證據檔與重跑

`reports/gate_outputs/`：
- `wf1004_Q_raw_manifest_check.txt`（§2 前半）、`wf1004_Q_raw_markers_and_readme_check.txt`（§2.1、README 清單核對）
- `wf1004_Q_raw_se_measure.json`、`wf1004_Q_raw_album_measure.json`、`wf1004_Q_raw_analysis.txt`、`wf1004_Q_raw_extra.txt`（§3）
- `wf1004_Q_raw_tongue_table.txt`、`wf1004_Q_raw_tongue_drum.json`、`wf1004_Q_raw_tongue_f0_two_estimators.json`（§4.2）
- `wf1004_Q_raw_sound_design_checks.txt/.json`（I5）、`wf1004_Q_raw_pdf_inventory.txt`、`wf1004_Q_raw_york_pdf_truncation.txt`（§0、§4、R7、I6）
- `wf1004_Q_raw_run_facts.txt`（工具版本、渲染器雜湊）、`wf1004_Q_raw_report_claim_checks.txt`（報告內數字的最後核對：43/43 有 reverb、2×／3× 峰、T60 比值範圍、loop-ready 首末樣本、PDF 分類）
- `wf1004_Q_raw_script_*.py`：全部腳本。重跑：先把兩個 zip 解到暫存（成員與 packages 內相同），再依序 `q_measure.py se`、`q_measure.py album`、`q_analyze.py`、`q_extra.py`、`q_tongue.py`、`q_f0check.py`、`q_sdk.py`、`q_markers.py`、`q_readme.py`、`q_pdfs.py`；腳本內路徑指向 `E:\Tsuki-project\_scratch\wf1004\Q\`。
- York 殘檔的文字抽取（`alon_extract.py`）輸出**不入庫**（論文授權 CC BY-NC-ND 2.5），只留在暫存。
