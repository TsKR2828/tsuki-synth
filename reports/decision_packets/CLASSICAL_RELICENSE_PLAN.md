# 古典曲目授權盤點 + 換源計畫

> 建立：2026-08-28
> 性質：研究/盤點包——不動 `src/`、`tests/`、`scores/`，本檔案是唯一產出。
> 觸發：月月裁決（原文見 §5）——「換乾淨公開來源，不能賣的樂譜沒有用」。

> **2026-08-28 月月裁決：CC BY 可以（署名可接受）**→ 路線定案：
> 給愛麗絲（PD）先行已執行、四季走 IMSLP Schoonenbeek CC BY、
> 月光走 Kowalewski CC BY 4.0 或重轉譜（皆需從譜面轉譜，待排程）。

---

## 0. 一句話導讀

`scores/` 底下所有古典改編曲目（月光 4 份、Vivaldi 四季 12 樂章）目前的音符
全部來自 **Mutopia Project 的 CC BY-SA（2.5／3.0）版本**——這個授權要求「相同
授權分享」，衍生品（我們的 score.json / 成品音檔）理論上也要用同一授權公開，
不能當作專屬商品賣。Für Elise 現有檔案反而不是問題（詳見 §1.3）。

研究結果：
- **月光**：Mutopia 上只有這一份 CC BY-SA 鋼琴獨奏版，**沒有乾淨替代版**；
  IMSLP 有大量真公版掃描（1802 首版起）但**沒有現成 MIDI**，換源＝重新轉譜。
- **Vivaldi 四季**：Mutopia 同樣只有這份 CC BY-SA 版；IMSLP 有 CC BY（無
  ShareAlike，可商用）的 Schoonenbeek MIDI，但編制是「鋼琴+弦樂」，不是現在
  的獨奏小提琴+管弦弦樂編制，換源＝改編制 + 重跑轉譜工具。
- **轉譜管線**：現有 `tools/midi_to_tsukisynth.py` 是**專為 Vivaldi 四季寫
  死的批次腳本**（比月光四檔案晚三週才出現），月光的原始轉譜根本不是用這個
  工具做的，是 AI 直接手工編碼 8 萬行 JSON。換源工程量因曲目而異，見 §4。

---

## 1. 授權盤點表

逐一打開 `meta.description` / `source` 欄位（或 catalog.json）親眼核對，
非憑檔名猜測。

### 1.1 月光奏鳴曲（4 個檔案，同一 `family_id: moonlight_sonata`）

| 檔案 | 授權宣告（`meta.description` 原文摘錄） | 判定 |
|---|---|---|
| `scores/examples/moonlight_sonata_complete.score.json` | "Source MIDI: Mutopia Project, Stewart Holmes edition, Berners 1908 source, **CC BY-SA 2.5**." | **污染** |
| `scores/examples/moonlight_sonata_movement1_tongue_drum.score.json` | 同上 | **污染** |
| `scores/examples/moonlight_sonata_movement1_yangqin.score.json` | 同上 | **污染** |
| `scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json` | 同上 | **污染** |

四份都源自同一份 Mutopia MIDI（piece-info id=276，A. Winterberger 編訂的
1908 Berners 版），親自打開 Mutopia 該頁確認授權欄位原文為
**"Creative Commons Attribution-ShareAlike 2.5"**——與 repo 內宣告一致，
不是誤標。

### 1.2 Vivaldi 四季（12 個樂章 + 1 個 catalog）

`scores/classical/vivaldi_four_seasons/vivaldi_four_seasons.catalog.json`
頂層即宣告：

```
"license": "Creative Commons Attribution-ShareAlike 3.0",
"license_url": "https://creativecommons.org/licenses/by-sa/3.0/"
```

12 個樂章逐一核對 `source_url` + `license` 欄位，全部一致：

| 樂章 | Mutopia source_url (piece-info id) | 授權 |
|---|---|---|
| spring m1/m2/m3 | id=301 | CC BY-SA 3.0 |
| summer m1/m2/m3 | id=336 | CC BY-SA 3.0 |
| autumn m1/m2/m3 | id=350 | CC BY-SA 3.0 |
| winter m1/m2/m3 | id=351 | CC BY-SA 3.0 |

判定：**全部 12 個樂章污染**。`scores/classical/vivaldi_four_seasons/README.md`
也明寫「Mutopia Project performers' facsimile edition」「CC BY-SA 3.0」，
與 catalog/score 內容一致，非文件過時。

### 1.3 Für Elise（1 個檔案）

`scores/examples/fur_elise_opening.score.json`：

```json
"author": "TsukiSynth JSON test",
"description": "Für Elise opening motif rendered through TsukiSynth FM piano"
```

打開內容確認：只有極短的開頭動機（幾個音符的 `events`），**沒有任何
Mutopia / MIDI 來源欄位、沒有 CC BY-SA 宣告**，是手工寫的測試 fixture，不是
從月光同一批 Mutopia MIDI 轉來的正式改編。

**判定：現有這個檔案本身不污染**（既不是版權作品的特定編訂版重製，也沒有
宣告任何非公版授權）。但它只是 2 小節的開頭動機，不是完整曲目——如果之後
要做「完整版 Für Elise」corpus 內容，才需要真的挑一個乾淨來源（見 §2.3）。
`tests/test_specimen_verify.py` 有引用 `fur_elise` 做域外測試樣本，**不要
動這個檔案**。

### 1.4 其餘曲目（原創，非古典改編，不在盤點範圍）

`scores/originals/ai_radiance/*`、`scores/originals/rules_v2_demo/*`、
`scores/library/{akashic,clockwork,forest,ocean,rabbit,restraint}/*` 均為
TsukiSynth 原創音效/配樂（`compose_ai_radiance.py` 等工具產出），未見任何
古典曲目改編或外部授權宣告，不列入本次污染盤點。

---

## 2. 乾淨來源研究（逐一打開確認授權原文）

### 2.1 月光奏鳴曲（鋼琴獨奏，Op. 27 No. 2）

**(a) Mutopia**：搜尋 Mutopia 全站，鋼琴獨奏編制的月光只有 id=276 這一份
（CC BY-SA 2.5，就是現在用的來源）。另外查到 id=2101，標題也叫
"Sonata No. 14 'Moonlight' (1st Movement: Adagio sostenuto)"，但打開後確認
**樂器欄位是「2 Guitars」**——是 F. Tárrega／J. J. Olson 的吉他二重奏改編，
不是鋼琴獨奏，授權雖然乾淨（"Public Domain" + CC0 標籤，Ildefonso Alier
版），但編制不合用。**結論：Mutopia 上沒有月光鋼琴獨奏的乾淨替代版。**

**(b) IMSLP**：打開
`Piano_Sonata_No.14,_Op.27_No.2_(Beethoven,_Ludwig_van)` 頁面，公版掃描版本
非常多（Cappi 1802 首版、André 1810、Cranz ~1814、Schlesinger ~1830、
Peters ~1910、Universal Edition 1921 等，全數標公版）。**但頁面上沒有可用
的 MIDI/MusicXML 檔**——唯一附掛的 MIDI 是「合成演奏」錄音，授權標
**CC BY-NC-SA 4.0（非商用）**，一樣不能用。**結論：IMSLP 音符來源乾淨，但
要重新轉譜（沒有現成音符檔）。**

**(c) 其他 MIDI 庫**：`bitmidi.com`、`mididb.com`、`midishow.com` 等聚合站
都能搜到「Moonlight Sonata.mid」。實際打開 `midishow.com` 一份的下載頁，
授權寫「CC0/Public Domain」，但頁面自己註明「此授權由上傳者自行宣告」——
**沒有可查證的版本/編訂來源鏈**，不符合 R4（查不到來源就是候選，不能當
定論引用）。Musopen（非營利公版古典音樂機構）理論上是更可信的候選，但
WebFetch 打它的頁面回傳 403，**未能親眼確認是否真的有 MIDI 檔／授權原文**
——列為「未驗證候選」，不是結論。

**月光乾淨來源結論**：目前沒有「授權乾淨 + 現成音符檔」同時成立的來源。
唯一確定乾淨的是 IMSLP 的公版掃描，但需要重新轉譜（見 §4）。

### 2.2 Vivaldi 四季（12 樂章，Op. 8）

**(a) Mutopia**：同 §1.2，只有這一份 CC BY-SA 3.0 版本（4 首協奏曲共用
id 301/336/350/351），沒有查到 Mutopia 上另一份公版四季。

**(b) IMSLP**：打開
`Il_cimento_dell'armonia_e_dell'inventione,_Op.8_(Vivaldi,_Antonio)` 頁面：
- PDF 掃描：1725 阿姆斯特丹 Le Cène 首版分部譜（獨奏小提琴/小提琴 I·II/中
  提琴/通奏低音）標公版；另有 Dover 1995（Eleanor Selfridge-Field 校訂）
  urtext 版也標公版。**都只有 PDF，沒有 MIDI。**
- MIDI/合成音檔：頁面「Synthesized/MIDI」區塊有 Schoonenbeek 改編的「鋼琴
  +弦樂」版 4 首 MIDI，授權標 **"Creative Commons Attribution 3.0"**（無
  ShareAlike）；另一組「鋼琴四手聯彈+弦樂」標 **CC BY 4.0**。CC BY（無 SA）
  **允許商用且允許閉源衍生品**，只要掛名出處——這點跟 CC BY-SA 本質不同，
  是真正可以拿來賣的授權。

**Vivaldi 乾淨來源結論**：IMSLP 的 Schoonenbeek CC BY 3.0/4.0 MIDI 是目前
唯一「授權可商用 + 有現成音符檔」的候選，**但編制是鋼琴+弦樂，不是現有
score.json 的獨奏小提琴+管弦弦樂四部physical-string編制**——換源等於同時
換編制，需要重新設計 `TrackProfile` 對應並核對 12 樂章結構/拍號是否一致。
若堅持要維持原始協奏曲編制的乾淨版，唯一路徑是 1725 首版 PDF 重新轉譜（見
§4，工程量最大）。

### 2.3 Für Elise（若之後要做完整版）

打開 Mutopia id=931 頁面確認：授權欄位原文 **"Public Domain"**（CC0／No
Rights Reserved 標籤），編訂者 Stelios Samelis，來源版本 Breitkopf & Härtel
1888，**有現成 MIDI 檔**可下載
（`ftp/BeethovenLv/WoO59/fur_Elise_WoO59/fur_Elise_WoO59.mid`）。這是三首
裡唯一「授權乾淨 + 有現成音符檔」同時成立的候選，如果要擴充成完整版
Für Elise corpus 內容，直接用這份即可，不需要重新轉譜手抄音符。

---

## 3. 轉譜管線盤點

查 `tools/` 目錄 + git log，只有一支相關工具：`tools/midi_to_tsukisynth.py`
（需要 `pip install mido`）。

- **CLI 只有一個子命令 `four-seasons`**（`parse_args` 裡唯一的
  `subparsers.add_parser`），寫死要求 `--source-dir` 底下有
  `spring/`、`summer/`、`autumn/`、`winter/` 資料夾，檔名對應
  `FOUR_SEASONS` 字典裡寫死的 Mutopia 檔名。**這不是通用 MIDI→score.json
  轉換器，是專門給 Vivaldi 四季用的批次腳本。**
- `TRACK_PROFILES` 字典寫死 `solo`/`violin`/`viola`/`cello` 四個角色，
  對應 `engine: "string"`、`material: "steel"`、`exciter: "bow"`——這套
  是為管弦弦樂編制設計的，月光（`engine: "fm"` / `"cimbalom"` /
  `"tongue_drum"`，鋼琴獨奏單軌）沒辦法直接套。
- `score_document()` 函式裡把 Vivaldi 的作曲家/作品/樂章中繼資料、
  `MUTOPIA_SOURCE_URLS`、`SEASON_META` 都硬編在函式本體，換一首曲子要重寫
  這段，不是改參數就能重用。
- **可重用的通用部分**：`TickMap`、`extract_notes`、
  `add_timing_and_articulation`（含 `articulation_gap_seconds` 呼吸間隔
  邏輯）、`make_rests`、`make_phrases`、`velocity_for`、`time_signatures`、
  `tempo_map`、`validate_score`、`write_score`——這些是跟樂器無關的 MIDI
  解析/正規化基礎設施，理論上可以抽出來給新曲目重用。
- **關鍵時序證據**：`git log` 顯示月光 4 個檔案在
  `0769e5a`（2026-05-30，`feat: v0.2.0`，"Claude Opus 4.6" 掛名共同作者）
  一次性以 82,966＋17,182＋16,040＋33,171 行 JSON 加入；而
  `midi_to_tsukisynth.py` 產出的 Vivaldi catalog 標記
  `"generated": "2026-06-21"`——**晚了三週才出現**。也就是說**月光的原始
  轉譜完全沒有用到這支腳本，是 AI 直接讀 Mutopia MIDI 手工編碼進 JSON**，
  不是可重跑的工具產出。repo 內查無任何專門處理月光的轉換腳本（歷史紀錄
  裡也搜不到）。

**管線結論**：換源不是「跑一次腳本」就能完成的事。Vivaldi 有半成品可重用
（通用解析層 + 需要重寫的曲目專屬層），月光完全沒有現成管線，等同從零開始
（要嘛重演一次 AI 手工轉譜，要嘛先把 `midi_to_tsukisynth.py` 泛化成單軌
鋼琴轉換器再跑）。

---

## 4. 建議行動 + 工程量估計

| 曲目 | 建議行動 | 工程量估計 | 備註 |
|---|---|---|---|
| **Für Elise**（若要做完整版） | 直接換用 Mutopia id=931（真公版，有現成 MIDI） | **小**：泛化轉換器加一個單軌鋼琴 `TrackProfile` + 跑一次 + 抽樣核對音符 | 現有測試用檔（`fur_elise_opening`）維持原樣不動，這是新增項目不是替換 |
| **Vivaldi 四季**（12 樂章） | 換用 IMSLP Schoonenbeek CC BY 3.0/4.0 MIDI（鋼琴+弦樂編制） | **中**：改寫 `TRACK_PROFILES`／`score_document` 曲目專屬層以配合新編制，重跑轉譜，逐樂章核對拍號/樂句結構是否與原協奏曲一致 | 编制從獨奏小提琴+管弦弦樂變成鋼琴+弦樂，音色設計要重新調整；`verify_exemptions.json`／corpus 測試若引用舊檔名需同步更新（不在本次授權範圍內處理） |
| **Vivaldi 四季**（若堅持原編制） | 從 IMSLP 1725 首版 PDF 分部譜重新轉譜 | **大**：無現成 MIDI，等同重做一次 28,376 個事件的人工/AI 轉譜 | 工程量與月光同級，是本清單最重的兩項之一 |
| **月光奏鳴曲**（4 個檔案） | 從 IMSLP 公版掃描（如 1802 Cappi 首版）重新轉譜 | **大**：沒有任何現成公版 MIDI，需要真的讀譜（OMR 或人工/AI 逐音核對）產生新音符資料，規模與原本 82,966 行的手工轉譜相當 | Musopen 候選未驗證（WebFetch 403），若之後能人工打開確認且真有可商用 MIDI，可降為中等工程量 |

**優先順序建議**：Für Elise 先做（成本最低、來源最乾淨），驗證泛化後的轉譜
流程可行；Vivaldi 用 IMSLP CC BY 版本換源（編制改變但工程量可控）；月光
是三者中最難的，若急著要「乾淨可賣」的月光內容，短期替代方案是先把現有
4 個月光檔案下架/不對外賣，長期再排入重新轉譜的工程排程。

---

## 5. 月月裁決原文與日期

> 「換乾淨公開來源，不能賣的樂譜沒有用」
> —— 月月，任務指示，2026-08-28

本裁決記錄用於後續執行本計畫時的授權依據；本檔案本身只是研究/盤點產出，
未對 `scores/` 做任何修改，換源與重新轉譜的實際執行留待月月審完本計畫後
另外排工。

---

## 6. Opus 稽核記錄（2026-08-28）

稽核者：Opus 子代理，懷疑立場。方法：不採信本檔案自述的「已打開確認」，對盤點表的
score meta **重新讀原始 JSON**、對「乾淨候選」**重新 WebFetch 原頁面**取授權欄位逐字。
未動 `src/`、`tests/`、`scores/`（僅讀取），未 git add/commit/push（R7）。本節為追加。

### 6.1 盤點表 3 首 score meta 原文比對

| 抽查對象 | 本檔案的宣稱 | 重新讀檔結果 | 判定 |
|---|---|---|---|
| 月光 4 檔（§1.1） | `meta.description` 含 "Source MIDI: Mutopia Project, Stewart Holmes edition, Berners 1908 source, CC BY-SA 2.5." | 四檔 `meta.description` 尾句**逐字完全相同**，即該句；`family_id` 皆 `moonlight_sonata` | **相符** |
| Vivaldi 12 樂章（§1.2） | 12 樂章 `source_url` + `license` 全部一致，id 301/336/350/351 | 12/12 檔的**頂層 `source` 區塊**：spring×3 → id=301、summer×3 → id=336、autumn×3 → id=350、winter×3 → id=351，`license` 全為 "Creative Commons Attribution-ShareAlike 3.0"；catalog 頂層 `license`/`license_url` 亦如表所載 | **相符**（欄位路徑更正見 B4） |
| Für Elise（§1.3） | 無任何 Mutopia/MIDI 來源欄位、無 CC BY-SA 宣告，是手工測試 fixture | `meta` 僅 `title`/`id`/`author`/`description` 四鍵；全檔字串掃描 `Mutopia`／`CC BY`／`license`／`Creative`／`source` **五個關鍵字全部 False**；`events` 僅 **12 個** | **相符** |

附帶重算（本檔案其他數字，一併查證）：
- `0769e5a` 日期 **2026-05-30**，該 commit 加入月光四檔，插入行數 **82966 / 17182 / 16040 / 33171**——與 §3「關鍵時序證據」逐字相符；Vivaldi catalog `"generated": "2026-06-21"`，確實晚三週。
- `tools/` 下無任何月光專用轉換腳本，git 全歷史 `--diff-filter=A` 亦查無——§3 結論成立。
- `midi_to_tsukisynth.py`：`parse_args` 內**只有一個** `add_parser`（L917）；`MUTOPIA_SOURCE_URLS`(L36)／`TRACK_PROFILES`(L54)／`SEASON_META`(L218) 皆模組級硬編，`score_document()`(L650) 於 L667 直接索引 `SEASON_META[season]`——§3「不是通用轉換器」成立。
- Vivaldi 12 樂章 `events` 總數重算 = **28,376**，與 §4 表格數字相符。
- §1.4：對整個 `scores/` 做 `mutopia|creative commons|CC BY` 全文檢索，命中**恰好 18 檔** = 12 樂章 + catalog + README + 月光 4 檔。`scores/originals/`、`scores/library/` 零命中——「原創、不列入盤點」成立。

### 6.2 「乾淨候選」親自打開確認授權標示

| 候選 | 本檔案宣稱 | 本次 WebFetch 取回的欄位原文 | 判定 |
|---|---|---|---|
| Mutopia id=931 Für Elise（§2.3） | "Public Domain"（CC0），Stelios Samelis，Breitkopf & Härtel 1888，有現成 MIDI | 標題 "Für Elise"；Instrument "Piano"；Maintainer "Stelios Samelis"；來源版 "Breitkopf & Härtel, 1888"；授權欄 **"Public Domain"（Creative Commons No Rights Reserved）**；MIDI 下載路徑即本檔案所引之 `…/BeethovenLv/WoO59/fur_Elise_WoO59/fur_Elise_WoO59.mid` | **完全相符** |
| IMSLP Vivaldi Op.8 Schoonenbeek（§2.2b） | 鋼琴+弦樂 CC BY 3.0、鋼琴四手+弦樂 CC BY 4.0；1725 Le Cène 首版標公版 | "For Piano and Strings (Schoonenbeek)" = **"Creative Commons Attribution 3.0"**；"For Piano 4 Hands and Strings (Schoonenbeek)" = **"Creative Commons Attribution 4.0"**；Le Cène 1725 分部譜標 **"Public Domain"** | **相符**（另有本檔案未提及的 Justin Bird 鋼琴版 **CC BY-NC 4.0**，本檔案未誤推薦，僅屬遺漏） |
| （加驗）Mutopia id=276 月光 | CC BY-SA 2.5，piece id=276 | Instrument "Piano"；Maintainer "Stewart Holmes"；來源版 "Berners, 1908 (edited by A. Winterberger)"；授權 **"Creative Commons Attribution-ShareAlike 2.5"** | **相符**——§1.1 表格（Stewart Holmes edition）與內文（A. Winterberger 編訂）看似打架，實際是「排版維護者 vs 底本編訂者」兩個不同欄位，兩者皆對 |
| （加驗）Mutopia id=2101 吉他二重奏 | 2 Guitars，Tárrega/Olson 改編，PD + CC0 | Instrument **"2 Guitars"**；"Arr: F. Tárrega & J. J. Olson"；授權 **"Public Domain" [CC: No rights reserved]** | **相符** |

### 6.3 CC BY-SA / CC BY 是否被誤判成 PD

**查無誤判。** 本檔案在四處把授權分級講得正確且未混用：Mutopia id=931 與 id=2101 兩處
標 PD——經查兩頁授權欄原文確實就是 "Public Domain"；Schoonenbeek 兩份標 CC BY（無 SA）並
明寫「**CC BY（無 SA）允許商用且允許閉源衍生品**，只要掛名出處——這點跟 CC BY-SA 本質
不同」，分級正確；16 個 Mutopia 檔一律標 CC BY-SA 污染，未有一處被寫成 PD。這條沒有問題。

### 6.4 Findings

- **B1（高）§2.1(b) 關於 IMSLP 月光頁的敘述在兩點上與實際頁面不符。** 本檔案寫
  「唯一附掛的 MIDI 是『合成演奏』錄音，授權標 CC BY-NC-SA 4.0（非商用）」。本次親自打開
  該頁確認：(i) **該頁根本沒有任何可下載的 .mid 檔**，Synthesized/MIDI 區塊掛的全是 **MP3**
  合成音檔——把它稱為「MIDI」會讓讀者誤以為存在音符資料；(ii) **不是「唯一」也不是統一
  NC**——同區塊至少有 AzzJem "Creative Commons Attribution-NonCommercial-ShareAlike 4.0"、
  **"For String Orchestra (Kowalewski)" = "Creative Commons Attribution 4.0"**、
  "For Orchestra (Donn)" = "Creative Commons Attribution-ShareAlike 4.0"、Karaca
  "Creative Commons Attribution-ShareAlike 3.0"。**漏掉了一份 CC BY 4.0 的資產**。
  §2.1 的**結論仍然成立**（MP3 不是音符資料，換源仍須重新轉譜），但**理由寫錯了**，
  必須改寫，否則月月是拿一段錯誤事實在做「大工程量」的決策。
- **B2（中）§2.1 與 §2.2 對「編制不合」採用了相反的標準，而且沒有把規則寫出來。**
  Vivaldi：接受 Schoonenbeek「鋼琴+弦樂」CC BY 版當首選乾淨候選，編制與現有獨奏小提琴+
  管弦弦樂**不同**，判為「中等工程量、可控」。月光：把 Mutopia id=2101（授權比 Schoonenbeek
  更乾淨，是真 PD/CC0）以「編制不合用（2 Guitars）」一句話排除，連降級評估都沒做。
  同一個 disqualifier 得到相反判決。這不必然是錯的（吉他二重奏的音符確實無法對應鋼琴獨奏
  兩手聲部，落差比鋼琴↔鋼琴+弦樂大），但**判準沒寫出來，§4 的工程量排序就不可複現**。
  建議在 §2 開頭補一條明文規則（例如「編制差異可接受的上限＝聲部數與音域可一對一映射」）。
- **B3（中）「污染」的法律結論下得太硬，且超出本專案能自行認定的範圍。** Beethoven／
  Vivaldi 的**作品本身是公版**，Mutopia 的 CC BY-SA 涵蓋的是**該份 LilyPond 排版/編訂**；
  「從 CC BY-SA 排版抽出音高/時值資料是否構成觸發 ShareAlike 的衍生作品」是法律判斷，
  不是打開授權欄位就能確定的事實。§0 只在一處寫了「理論上」，但 §1 的「判定」欄對 16 個
  檔案直接印「**污染**」，§4／§5 再據以排出商用工程排程。建議在 §0 加一行明確聲明：
  **本檔案不是法律意見；商用發布前需由律師確認**。稽核者同樣不具法律資格，此處只指出
  文件把不確定性寫成了確定性，不對授權效力本身表態。
- **B4（低）§1 引言的欄位路徑寫得不精確。** 寫「逐一打開 `meta.description` / `source`
  欄位（或 catalog.json）」。實際上：月光的授權宣告在 `meta.description` 句尾，Vivaldi 的
  在**頂層 `source` 物件**（不是 `meta.source`），兩者路徑不同。稽核已逐檔確認資料本身
  無誤，僅建議把路徑寫死成 `meta.description` 與 `$.source.license` 以利日後複查。
- **B5（低）§2.1(c) 的 Musopen 候選標註正確，維持原樣。** 標「WebFetch 403、未能親眼確認、
  列為未驗證候選」符合 R4，本次未重試，仍為未驗證。§4 月光列的「若之後能人工打開確認…
  可降為中等工程量」措辭亦恰當。

**整體裁決**：§1 盤點表（本次抽查的 3 首、實際涵蓋全部 17 檔）**可信，照單全收**；
§3 管線盤點與 §4 的量化數字**逐項複算相符**；§2 的乾淨候選**授權標示全部正確**，但
**§2.1(b) 的事實敘述必須依 B1 改寫**，B2/B3 為需要月月拍板的判準與法律面缺口。

---

## 7. Opus 稽核記錄（2026-08-28，第二輪：Für Elise 換源執行的驗收）

稽核者：Opus 子代理，懷疑立場。本節稽核的是 §2.3／§4 所排的「Für Elise 先做」**已執行的成果**：
`scores/classical/fur_elise/`（2 個新 score）＋`tools/midi_to_tsukisynth.py` 泛化
＋`tools/verify_score.py` 探索範圍擴大。方法：**不採信任何自述**——授權重新開頁、
轉譜用**自寫的獨立 SMF parser**（刻意不呼叫被稽核的 `midi_to_tsukisynth.py`）逐音比對、
迴歸自行重跑。未動 `src/`、`tests/`、`scores/`（僅讀取），未 git add/commit/push（R7）。

### 7.1 授權：親自重開 Mutopia id=931，與證據檔逐欄位對照

`reports/gate_outputs/furelise_license_evidence.txt` 是上一輪留下的證據檔。稽核者
**獨立重新 WebFetch** `piece-info.cgi?id=931`，逐欄位對照：

| 欄位 | 證據檔記載 | 本次重新取回 | 判定 |
|---|---|---|---|
| Title | "Für Elise" | "Für Elise" | 相同 |
| Composer | "L. V. Beethoven (1770-1827)" | "L. V. Beethoven (1770–1827)" | 相同（僅連字號 vs. en dash 的轉碼差異） |
| Instrument / Style | "Piano" / "Classical" | "Piano" / "Classical" | 相同 |
| Source (edition) | "Breitkopf & Härtel, 1888" | "Breitkopf & Härtel, 1888" | 相同 |
| Maintainer | "Stelios Samelis" | "Stelios Samelis" | 相同 |
| **授權** | "Public Domain" with "CC: No rights reserved" | "Public Domain" with Creative Commons No Rights Reserved designation | **相同** |
| 授權連結 href | `http://creativecommons.org/licenses/publicdomain/` | `http://creativecommons.org/licenses/publicdomain/` | 相同 |
| Piece ID | "Mutopia-2015/08/18-931" | "Mutopia-2015/08/18-931" | 相同 |
| 下載連結 ×4 | `.ly` / `.mid` / a4 PDF / letter PDF | 四條路徑逐字相同 | 相同 |

**判定：PD 確認通過，證據檔零失真。** 與 §6.2 的第一輪稽核亦一致（第三次獨立確認）。

本地來源檔完整性：`source/CHECKSUMS.txt` 記載的兩個 SHA256 與磁碟上實檔重算**完全相符**
（`.mid` = `1c12c21c…50215a`，`.ly` = `828a7bd1…6ba7a67`）。
**殘留缺口（誠實揭露）**：稽核者**未**重新下載上游檔案比對雜湊（下載屬需授權動作），
因此「本地 `.mid` 確實就是 Mutopia 那一份」這點目前只由上一輪的下載行為擔保，非本輪獨立驗證。

### 7.2 新 score.json 的 meta／授權欄位

兩檔（`fur_elise_complete` / `fur_elise_complete_cimbalom`）的頂層 `source` 區塊：
`license` = `"Public Domain"`、`license_url` = `http://creativecommons.org/licenses/publicdomain/`、
`score_source` = `"Mutopia Project (Stelios Samelis edition)"`、`source_url` = id=931 頁面、
`attribution` 含「Breitkopf & Härtel, 1888. Public Domain -- no rights reserved.」
——**四項與 §7.1 取回的頁面原文逐字一致，無升級也無降級授權**。
`meta.tags` 含 `public-domain`；`meta.primary_type`/`sound_type` = `ambience`/`oneshot`，
**與既有 12 個 Vivaldi 樂章的慣例相同**（稽核者掃過全 corpus 26 檔確認），非隨手填值。
`editorial_note` 誠實聲明「source MIDI has constant velocity 62 on every note -- no real
dynamics encoded」，力度為 TsukiSynth 詮釋資料——**此聲明經 §7.3 實測證實為真**。

### 7.3 轉譜正確性：自寫 SMF parser 逐音比對（本節為本輪最核心的查核）

稽核者**另寫一支獨立的 Standard MIDI File 解析器**（自行處理 VLQ／running status／
note-on velocity 0 當 note-off／format-1 多軌），**完全不呼叫 `mido`，也不呼叫被稽核的
`midi_to_tsukisynth.py`**，以免用被稽核者的邏輯去驗證被稽核者。

**MIDI 檔實況**：format=1、**division = 384 ticks/quarter**、3 軌
（`control track` / `up:` / `down:`）、單一 tempo `833333 µs/quarter`、time signature 3/8。
→ 每 tick = 833333e-6 / 384 = **0.0021701380208333 s**。
score 的 `tempo_map` 記載 `{tick:0, quarter_bpm:72.0, microseconds_per_quarter:833333}`，
與檔案原始值相符（60e6/833333 = 72.000029，四捨五入為宣告的 72.0）。

**前 20 個音符 pitch/onset 逐一比對**（依 (onset, 音名) 排序後 1:1 對位）：

| # | tick | MIDI pitch | MIDI onset(s) | score note | score time(s) | Δt |
|---|---|---|---|---|---|---|
| 0 | 0 | E5 | 0.0000000 | E5 | 0.0000000 | 0 |
| 1 | 96 | D#5 | 0.2083332 | D#5 | 0.2083330 | −2.5e−07 |
| 2 | 192 | E5 | 0.4166665 | E5 | 0.4166660 | −5.0e−07 |
| 3 | 288 | D#5 | 0.6249997 | D#5 | 0.6250000 | +2.5e−07 |
| 4 | 384 | E5 | 0.8333330 | E5 | 0.8333330 | 0 |
| 5 | 480 | B4 | 1.0416663 | B4 | 1.0416660 | −2.5e−07 |
| 6 | 576 | D5 | 1.2499995 | D5 | 1.2499990 | −5.0e−07 |
| 7 | 672 | C5 | 1.4583328 | C5 | 1.4583330 | +2.5e−07 |
| 8 | 768 | A2 | 1.6666660 | A2 | 1.6666660 | 0 |
| 9 | 768 | A4 | 1.6666660 | A4 | 1.6666660 | 0 |
| 10 | 864 | E3 | 1.8749992 | E3 | 1.8749990 | −2.5e−07 |
| 11 | 960 | A3 | 2.0833325 | A3 | 2.0833330 | +5.0e−07 |
| 12 | 1056 | C4 | 2.2916657 | C4 | 2.2916660 | +2.5e−07 |
| 13 | 1152 | E4 | 2.4999990 | E4 | 2.4999990 | 0 |
| 14 | 1248 | A4 | 2.7083322 | A4 | 2.7083320 | −2.5e−07 |
| 15 | 1344 | B4 | 2.9166655 | B4 | 2.9166650 | −5.0e−07 |
| 16 | 1344 | E2 | 2.9166655 | E2 | 2.9166650 | −5.0e−07 |
| 17 | 1440 | E3 | 3.1249988 | E3 | 3.1249990 | +2.5e−07 |
| 18 | 1536 | G#3 | 3.3333320 | G#3 | 3.3333320 | 0 |
| 19 | 1632 | E4 | 3.5416652 | E4 | 3.5416650 | −2.5e−07 |

**前 20 個音符：pitch 20/20 相符，onset 誤差上限 5e−07 s（0.5 µs）＝ 6 位小數
四捨五入的必然殘差，不是 tick 換算錯誤。** 第 8/9 與 15/16 是雙手同刻的和聲，
兩軌（up/down）都正確落在同一 onset，**未發生轉譜器最常見的「兩軌各自從 0 起算」錯誤**。

**不只抽驗前 20——稽核者對全部 905 個事件做了完整掃描**：
- MIDI 音符數 **905** ＝ score 事件數 **905**（1:1，無漏音、無多音）
- **pitch 不符 = 0 / 905**（含異名同音處理：`D#5`/`G#3` 等以升記號拼寫，與 MIDI 一致）
- **onset 最大誤差 = 5.000e−07 s**（全 905 事件）
- **發聲時長超過來源 MIDI 時長的事件 = 0 / 905**
  （檢驗式：`event.duration × renderer_note_off_ratio(0.9) ≤ MIDI 時長`。
  articulation gap 只會縮短、不會拉長音符——與 `timing_policy` 宣告一致）
- articulation gap 分佈：0 ms（130 個，後接休止不需讓位）／7.29／7.9／9.72／**14.58 ms（433 個，最常見）**／22／37.5／**最大 55 ms**——皆為「小的手指離鍵間隙」量級，無異常值
- 音域 A1–E7；**來源 MIDI velocity 集合 = {62}（單一值）**，score 有 12 種 velocity
  → **`editorial_note` 說「力度是 TsukiSynth 詮釋資料、來源無真實力度」屬實，未偽稱來自樂譜**
- 揚琴版：905 事件、音名序列與鋼琴版**完全相同**、`engine` 全為 `cimbalom`、
  `variation_of` = `fur_elise_complete` — 是純引擎替換的變體，宣稱與實際相符

**判定：轉譜正確，tick 換算無誤。** 這正是任務指名最易出錯的一環，實測未發現錯誤。

### 7.4 four-seasons 子命令「零改變」的證明

**Finding F1（中）：稽核前，這份證明並不在場。**
`tools/midi_to_tsukisynth.py` 有**三處**註解宣稱 four-seasons 輸出 byte-for-byte 不變
（`TrackProfile` docstring、`track_name()` 內、`ARTICULATION_STYLE_LABELS` 前），
其中兩處明確引用「**see CLASSICAL_RELICENSE_PLAN.md execution notes**」。
**本檔案沒有 "execution notes" 這一節**（章節只有 §0–§6），`reports/` 下亦無任何對應證據檔
——即「有主張、無證據，且指向一個不存在的出處」。

**稽核者補做了這份證明**，完整輸出存於
`reports/gate_outputs/furelise_four_seasons_noop_proof.txt`。摘要：

- **障礙**：Vivaldi 來源 MIDI **不在 repo 內**（全 repo `*.mid` 只有 `fur_Elise_WoO59.mid`），
  無法用原始輸入重跑比對。
- **改用差分測試**：合成一批「Vivaldi 形狀」MIDI（type-1／384 tpq／control track ＋
  `solo`/`violinone`/`violintwo`/`viola`/`cello` 五軌各 40 音／曲中變速／零間隔音以觸發
  articulation 分支／外加一條不在 profile 內的 `continuo-organ` 軌），
  以**同一批檔案**分別餵給 `git show HEAD:tools/midi_to_tsukisynth.py`（88bdfac）與工作樹版。
- **結果**：兩版都輸出 `Generated 12 movements: 2400 events, 1038 explicit rests`；
  `diff -r` **無任何差異**；13 個輸出檔（12 樂章＋catalog）**SHA256 全部相同**。
- **佐證（rstrip(':') 確為 no-op）**：已提交的 `spring_m1` 的 `performance.role` 涵蓋
  全部 5 個 `TRACK_PROFILES`（solo_violin 820／violin_1 705／violin_2 697／
  cello_continuo 501／viola 450）。舊版 `track_name()` 無 rstrip，軌名必須與鍵**完全相等**
  才會被 `extract_notes` 收錄；五軌全部有事件 ⇒ 來源軌名本就不帶結尾冒號 ⇒ rstrip 對其為恆等。
- **殘留未證（誠實揭露）**：若原始 Vivaldi MIDI 另存在帶冒號的重複軌，新版會多收而舊版會漏收
  ——這一種情形**必須有原始 MIDI 才能排除**，差分測試涵蓋不到。實務上機率極低，但不是零。

**判定：證明現在在場且成立（我補的），但程式碼註解的交叉引用是壞的。**
建議把三處註解的「see CLASSICAL_RELICENSE_PLAN.md execution notes」改指
`reports/gate_outputs/furelise_four_seasons_noop_proof.txt`，或在本檔案真的補一節 execution notes。

### 7.5 迴歸：pytest／verify_score／既有 73 檔

| 項目 | 稽核者親自重跑的結果 |
|---|---|
| `python -m pytest tests/ -q` | **131 passed in 8.86s**，零失敗零跳過 |
| `verify_score.py` 對新檔 `fur_elise_complete` | **RESULT: ALL CHECKS PASSED**（905 事件；schema／events_sorted／midi_range／等律頻率最大偏差 0.006 cents／modal 28257 partials 無 NaN-Inf／f0 偏差最大 2.482 cents／render 決定性 SHA256 兩次相同／peak −0.45 dBFS／休止 −58.4 dBFS 低於 −50 限值 8.4 dB） |
| `verify_score.py` 對新檔 `fur_elise_complete_cimbalom` | **RESULT: ALL CHECKS PASSED** |
| `find_all_scores` 探索範圍（新舊版並排載入比對） | OLD(HEAD) **73** 檔 → NEW **75** 檔；`set(old) ⊆ set(new)` = **True**；**REMOVED = 空集合**；新增恰為 fur_elise 那 2 檔。**`verify_score.py` diff 註解宣稱的「strict superset of the old root」屬實** |
| 既有 73 檔結果不變（抽 3 檔對 `b6_corpus_recheck_shard*.txt` 比對） | 見下表，**三檔逐欄位相同** |

| 抽驗檔 | 本輪 WAV SHA256 | 前次 b6 run | tree hash | renderer | peak / gain | 判定 |
|---|---|---|---|---|---|---|
| `vivaldi_four_seasons_spring_m1` | `7a35e3290de2…` | `7a35e3290de2…` | `b59ae225076d` | `fa15495681f7` | 0.124175 / 7.65049 | **完全相同** |
| `physical_piano` | `607d0d3bc578…` | `607d0d3bc578…` | `53826bf5c91e` | `fa15495681f7` | 0.10846 / 8.75901 | **完全相同** |
| `akashic_bell` | `830d2089427a…` | `830d2089427a…` | `728dd914bbfe` | `fa15495681f7` | 0.595352 / 1.59569 | **完全相同** |

三檔皆 `RESULT: ALL CHECKS PASSED`，與前次 `-> PASS` 一致。
`git status` 亦顯示 `scores/` 下**無任何既有檔案被修改**（只有 `scores/classical/fur_elise/` 為新增未追蹤），
與「既有 73 檔不變」互為佐證。

**附註（非 finding，供月月知情）**：本輪三檔的 render manifest 都記著
`configured source=f67050b04c10 dirty`，即 CLI 執行檔是較早的建置產物（HEAD 為 88bdfac）。
本輪改動全在 `tools/`（Python），`src/` 零改動，故不影響上述位元比對的有效性；
**本輪亦未跑 ctest**（X4 規約的三 target 重建僅在 C++ 有改動時才需要，本輪不適用）。

### 7.6 Findings 總表（本輪）

- **F1（中）**：four-seasons 零改變的證明**稽核前不在場**；程式碼三處註解引用的
  「CLASSICAL_RELICENSE_PLAN.md execution notes」**是不存在的章節**。
  證明已由稽核者補做並存檔（`reports/gate_outputs/furelise_four_seasons_noop_proof.txt`），
  結論成立，但**交叉引用必須修**。
- **F2（低）**：Vivaldi 來源 MIDI 不在 repo，導致 four-seasons 只能做差分測試、
  不能用原始輸入重跑。建議把來源 MIDI（或其 SHA256 清單，比照 fur_elise 的
  `source/CHECKSUMS.txt` 做法）納管，否則往後任何一次轉譜器改動都無法做真正的迴歸。
- **F3（低）**：本地 `.mid`/`.ly` 與上游的一致性本輪未獨立驗證（未重新下載），
  只有 `CHECKSUMS.txt` 的自我一致性通過。若要閉合，需再下載一次比對雜湊。
- **無 finding 的項目**：授權（三次獨立確認 PD）、score meta 授權欄位、
  轉譜正確性（905/905 pitch 相符、onset 誤差 ≤ 5e−07 s）、力度來源的誠實揭露、
  pytest 131 綠、兩個新 score 的 verify_score 全綠、探索範圍嚴格超集、既有 73 檔位元不變。

**整體裁決**：**§2.3／§4 排定的「Für Elise 先做」已正確執行，可接受。**
最容易出錯的 tick 換算與雙軌對位經獨立解析器逐音複核**零錯誤**；授權路徑乾淨且三度確認；
迴歸全綠且既有語料位元不變。唯一實質缺失是 F1（宣稱有證明、證據不在場、出處是死連結），
性質是**文件紀律問題而非正確性問題**——補做後結論不變。
