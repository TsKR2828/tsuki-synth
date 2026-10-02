# TsukiSynth 現況盤點（2026-09-25）

> 方法：9 個 agent，6 路掃描、3 個懷疑者逐條反駁，共 128 條發現：92 條屬實、36 條部分修正、0 條被推翻。另有懷疑者補抓的 13 條漏項。
> 全程沒有改 repo 的原始檔，沒有 `git add`，也沒有 commit。唯一的改動是重建 `build/` 的編譯產物。本資料夾是這次新增的，untracked。
> 逐條細節與證據見 `APPENDIX_findings.zh-TW.md`。GATE 原始 log 在 `gate_logs/`，commit 清單在 `commit_lists/`，量測腳本在 `probes/`。

---

## 0. 一句話

**程式本身健康：今天對 staged 樹重跑全套 GATE，每一項數字都跟 09-15 基線一模一樣。**
卡住的是流程：WF0914 的 121 個檔從 09-15 起 staged 等月月審，已經 10 天。
部署在系統上的 VST3 是 09-10 的舊版。
這次另外查到 repo 沒登記過的問題：**給愛麗絲全曲有 16 顆音的基頻被壓掉**，準備上架的母帶就含這 16 顆。

---

## 1. 目前做到哪裡

### 1-1 進度

| 區塊 | 狀態 |
|---|---|
| 物理鏈 B1–B6 | 完成（08-29 收官） |
| B7 第一原理力鏈 | Phase 0 完成；Phase 1 部分完成（純函式入庫，dumpModes 欄位已撤回）；Phase 2/3 BLOCKED，是 09-15 裁決定的合法終點 |
| D9–D15 缺口 | D9、D12、D13、D14、D15 已關閉；D10 等付費牆文獻；D11 的 patch 存檔，排隊等「D11-F5 根因調查」 |
| 驗證鏈 ①–⑧ | 都在；HostProbe 89 項，corpus 75 檔 |
| git | HEAD `766d21d`，`main`=`3f9b90a`，已 push。**121 檔 staged 未 commit**，另有 1 個 untracked（變現計畫） |
| CI | physics.yml 三平台綠（注意：Linux leg 標成 clang，實際是 GCC 13.3）；**release-physics.yml 從沒跑過，第一次跑一定紅**（見 §4） |
| 變現線 | clean_batch2 音效包 43 檔＋專輯 6 軌已完成，zip 與 catalog 雜湊全對；等月月的 5 項裁決與賣家帳號 |

### 1-2 今天（09-25）重跑 GATE：全綠

09-15 的整合卡跑在 D9c 之前，這是 D9c 落地後第一次在 `build/` 上跑全套。

| GATE | 結果 | 跟基線比 |
|---|---|---|
| 三個主 target＋五個測試 target 重建（X4） | exit 0 | — |
| ctest | 4/4 | 相同。K-02 資訊行由 −28.5 dB 變成 **+0.112 dB**，證明 D9c 有編進去 |
| pytest | 264 passed＋1 skip＋5 xfail＝270 | 相同 |
| `physics_verify --full` | NO CHECKED FAILURES | 與 09-15 逐行 diff 為 0 |
| `--selftest` | 13 行全 PASS | 相同（09-15 摘要寫的「15 項」是筆誤） |
| `verify_score --all` | 75/75，含 1 項既有豁免 | 3838 行輸出 diff 為 0 |
| HostProbe | 89 PASS / 0 failures | 相同 |
| 位元不變（post_a14 基準） | 8/8 IDENTICAL | 相同 |
| 結束時 git status | 與開始時完全相同 | — |

### 1-3 部署實況（跟文件寫的不同）

- 實際裝的是 `C:\Program Files\Common Files\VST3\TsukiSynth_VST3_2026-09-10\TsukiSynth.vst3`。整個外層資料夾被放進 VST3 目錄，所以多了一層子資料夾。
- 這份是 **09-10 23:46 的 build，缺 D12 和 D9c**。用 HostProbe 測它，剛好只有 5 個 D12 檢查 FAIL（84/5）。
- 還有舊副本：`C:\Program Files (x86)\Common Files\VST3\TsukiSynth.vst3`（07-12），以及 `%APPDATA%\VST3\TsukiSynth.vst3`（05-07）。
- Cubase 的外掛快取停在 08-22，指向一個已經不存在的路徑（v0.2.0）。

---

## 2. 這次新查到、repo 裡沒登記的事（依重要性排）

1. **給愛麗絲全曲 16 顆弱基頻 FAIL**（懷疑者重算屬實）。
   A14 B-2 讓原本的 G5 等 22 顆全部轉 PASS，但力脈衝的深零點沒有消失，是搬到別的「音高＋力度」組合：
   - E5@0.278 共 9 顆
   - A5@0.427/0.452 共 4 顆
   - A6@0.427 共 2 顆
   - A#6@0.427 共 1 顆

   這些音的基頻比第二泛音低 6～19 dB。08-30 時這 16 顆都是 PASS，score 之後沒改過，所以是 A14 造成的。A14 報告只掃了音高，沒掃力度。**clean_batch2 的給愛麗絲母帶含這 16 顆。**
2. **D9c 沒有任何硬 GATE 守著。**
   K-02 只印數字、不判定，HostProbe 不量 IR 電平，8 首位元不變走的是 CLI，而 CLI 根本沒 include EffectChain。所以把 `kIrWetMakeupGain` 刪掉，全套 GATE 仍然會是綠的。
3. **發行用 CI 第一次打 tag 必紅。**
   `release-physics.yml:45` 漏了 SpectrumViewTest，跟 766d21d 修掉的是同一個坑，只是 release 這支沒一起改。`:50` 用 unittest，只收得到 199/270 個測試。
4. **「全曲版 41 個削波樣本」是誤讀。**
   那個數字是正規化之前算的。母帶實際峰值 0.95，沒有平頂。所以變現裁決第 3 題「要不要重渲全曲版」的前提不成立。這個誤讀散在 PRODUCT_SHEET、LISTING_COPY、MONETIZATION_PLAN、catalog 的 `clipped_samples` 欄。
5. **6 個 loop 檔長度不是小節長度**（後面多接了餘響尾巴），但買家拿到的 README 寫「可無縫循環」。
6. **VST3 動態連結 VC++ runtime**（MSVCP140_2 等）。買家電腦沒裝 VC++ 可轉散發套件時，DAW 會載不進來。
7. **VST3 Program 參數會錯位。**
   host 看到的 program 格數在建立 instance 時就固定了，但使用者 preset 會增減、又依名稱排序。結果是自動化或 program change 可能載到別的 preset，換台機器也可能對不上。
8. **D15 的兩個 strict xfail 永遠不會 XPASS。**
   pin assert 排在 ≤1 c 判定之前，所以數字漂移抓不到，估計器變好也抓不到。註解引用的檔名也不存在。
9. **D9c 的 GATE 證據檔有一句不實陳述**：`wf0914_D9c_ir_makeup_gain.txt:252`。它說 HostProbe 原始碼搜不到 IR 字樣，實際有 83 行命中。結論本身仍然成立，但句子要改。
10. **B7 裁決有一步沒落地**：TODO:457 和 ROADMAP:155 的 B7 條目沒有照 §6 第 3 點同步。所以「五項裁決全部落地」這句話不精確。
11. **pluginval 和 Steinberg validator 最後一次是 08-06。** 之後改過 tail、IR state、D12、D9c，都沒有重驗。

---

## 3. 還要做的（依「誰做」分）

### 3-1 等月月（依擋路程度排）

| # | 事項 | 備註 |
|---|---|---|
| 1 | **審 staged，決定 commit 切法** | 已備好 7 個 commit 的清單（`commit_lists/`，已驗證 121 檔無重複、無遺漏、無 CR）。也可以把 c1～c3 合成 5 個。建議 commit 前先修 HANDOVER §9/§10 與 ROADMAP B7 列的過時文字 |
| 2 | commit 後要不要重新部署 VST3、清掉 (x86) 和 %APPDATA% 的舊副本 | 動系統資料夾，要你同意 |
| 3 | 變現 5 裁決：售價、AI 署名口徑、全曲版要不要放、聽人把關、賣家帳號 | 第 3 題前提已不成立（§2-4），可以直接放、不必重渲 |
| 4 | 給愛麗絲母帶：先上架，還是等弱基頻修好 | 見 §2-1 |
| 5 | UI 功能規格要送給誰 | 規格 v1.1 有幾處過時，要先同步成 v1.2 |
| 6 | 四季和月光換源重轉譜要不要排程 | 擋住專輯 Vol.2 |
| 7 | 新的工程裁決候選 | D9c 要不要加硬 CHECK（|IR−ALGO| ≤ 0.25 dB）；IR 模式要不要加輸出限幅（會改渲染，走 R10）；Program 參數只給工廠 preset；靜態 CRT 還是附 vc_redist；plugin↔CLI 一致性 GATE 還是把文案收窄；R6 要不要涵蓋 plugin 層（`src/effects`、`PluginProcessor`）；B7 的 MIDI 20 clamp 跳 2.3 倍 |
| 8 | 小事 | Limbus 有沒有啟用；Downloads 裡約 470 MB Yamaha 解壓殘留要不要清（文件寫 200 MB，偏少）；A10 Score 控制台實操 |

### 3-2 等外部

- 兩封信（TU Berlin、Iowa MIS），09-15 寄出，等回覆。
- 付費牆文獻：D10（Hall 1988 / Chaigne & Askenfelt Part II）、D5、B7 絕對 SPL 的出處。
- D7 實體試體量測。

### 3-3 AI 現在就能做，不用等裁決，也不改 src

| 事項 | 價值 |
|---|---|
| 弱基頻「零點地圖」：用 `--dump-modes` 掃 piano 的 MIDI×力度網格 | 高：決定給愛麗絲母帶去留的數字 |
| D11-F5 根因調查（唯一排隊卡，已授權） | 中 |
| loop-ready 版本：放在 exports/，裁到整小節，把尾巴疊回開頭，接縫用數字驗收 | 中：上架前必修 |
| LICENSE_SE_PACK v1.1 草稿＋Fab 版 zip | 中：Fab 只接受平台授權 |
| THIRD_PARTY_NOTICES.txt | 中：VST3 MIT、JUCE 依賴、IBM Plex OFL，目前 repo 沒有 OFL 全文 |
| 文件同步一批（清單見 §5） | 中 |
| partial_verify 全曲 905 顆實跑（D14 修好記憶體後已經能跑） | 低～中 |
| D1 梁／板阻尼文獻補搜（從沒搜過，擋 BeamModel ×2 裁決） | 中 |
| 外掛 16 voice 搶音量測 | 中 |

JUCE 授權已經順便查證：JUCE 8.0.12，Starter 方案年營收 US$20k 以下免費、可閉源，沒有 splash 或署名要求，跟 LICENSE 寫的一致。營收保守算法要把合成器、音效包、專輯合計。

### 3-4 AI 能做，但會動 src/tests/CI，要你點頭（R6/R7）

- release-physics.yml 修兩行，改完需 push 後手動試跑。
- D15 測試的 pin 改成非 xfail。
- HostProbe 接進 CI。
- `render_wf_scores.py` 加 `--outdir`。
- HostProbe 改成不依賴目前工作目錄。
- Cimbalom 每個音在音訊執行緒建一次 `juce::String`，改成預先存好指標。

---

## 4. 最好可以補上的（以「要賣的外掛」為標準，依價值排）

1. **pluginval（strictness 10）＋Steinberg validator 重驗。** 上次停在 08-06。要下載 pluginval、build SDK validator，需要你同意下載；或者修好 release CI 後手動觸發。
2. **修 release CI**，並在每次 push 的 CI 加一個 pluginval strictness 5 的快速 step。
3. **VC++ runtime**：改成靜態 CRT（業界多半這樣做），或在安裝包附 vc_redist。
4. **D9c 硬 CHECK**：成本很小，能防止「補償增益被悄悄拿掉」。
5. **plugin↔CLI 一致性**：現在物理 GATE 驗的是 CLI 路徑。plugin 的 `startNote()` 跟 CLI 共用衰減律，但激發、macro、BodyResonance、EffectChain 是各自組裝的，而「可稽核物理鏈」正是賣點。兩條路擇一：補 parity GATE，或把文案收窄成「CLI 渲染已驗證」。
6. **Program 參數只暴露工廠 preset**：解掉 §2-7 的錯位。
7. **發行件**：安裝包腳本、買家用 EULA（現行 LICENSE 不能直接當買家授權）、THIRD_PARTY_NOTICES、版本號（0.3.0 已四個月沒動）、廠商網址與信箱、關於頁。
8. **測試補強**：
   - plugin state 加版本欄位。
   - IRLibrary 手寫 SHA-256 加已知答案測試。
   - 27 個工廠 preset 加回歸測試（打錯的 paramID 目前會被靜默略過）。
   - D14 的 `read_wav_header` 和 `StemArrayStream` 加單元測試。
9. **即時音訊安全自動化**：在 Linux clang 加一個 RTSan job。
10. **位元不變回歸自動化**：CI 目前只渲染 6/75 首。
11. **macOS/AU**：plugin 從沒在 mac build 過；Score 控制台寫死了 Windows 檔名。這項要看有沒有打算賣 mac 版。

音效包上架前另有這些（詳見附錄 release-readiness 段）：

- 三個打擊音效的峰值被開頭尖峰佔掉，比全包中位數小 12～23 LU。要先定正規化政策；尖峰算不算瑕疵要聽人判斷。
- 文案的「阻尼是實測常數」說過頭了：beta_air 和 gamma_radiation 這兩項還待溯源。
- 音效包沒揭露 AI 參與，跟專輯的說法不一致。
- 16-bit 轉檔沒加 dither。
- 商品圖 0 張。

需要「聽」才能把關的環節彙總成一張約 15 分鐘的定點清單，建議交給聽人：3 個打擊音效的開頭、6 個 loop 的接縫、Gate Open Dark 的 overdrive。

---

## 5. 過時或互相矛盾的文件（AI 可一次修，要你同意）

- **HANDOVER §9**：
  - 位元基準寫成 post_d8，照做 physical_piano 會假紅燈，應改 post_a14。
  - pytest 寫 267，應為 270。
  - 量測器自證寫 1.1721 c，D15 後預設輸出是 5.2304 c。
- **HANDOVER §10**：`tr -d '\r'` 的 `\r` 被寫成了真的換行，指令本身是壞的。
- **HANDOVER 其他**：
  - §5-1 還寫 D9/D15 BLOCKED，跟同一份文件的 §0/§1/§7 矛盾。
  - §8 檔案地圖沒有 WF0914。
  - 兩封信前面說已寄出、後面又列成待辦。
  - Limbus 和 Yamaha 09-14 就裝好了，仍列「待安裝」。
  - 部署寫法跟 §1-3 的實況不符。
- **TODO.md**：
  - 開頭快照的 BLOCKED 行已被裁決取代，但沒標註。
  - WF0907～09 段寫「全部未 commit」，這是錯的，那批早就 commit 了。
  - 十幾條已完成或已否決的項目還掛著 `[ ]`：UI 雙開門、A1 與 A4 的重複條、C3-b、Before merging 等。
  - D11-F5 和 D13 後續同步沒有勾選項。
- **README**：
  - HostProbe 寫 16/16，實際 89。
  - PresetBrowser.h 和 HarmonicEditor.h 已刪，但檔案樹還列著。Harmonic Editor 功能其實還在，改成內嵌在主編輯器。
  - B5 寫「staged」，實際早已 commit。
  - 平台列寫「macOS planned」，但 CI 已在 macOS 建 CLI。
  - 09-13 那批寫「尚未 push」，實際已 push 並 merge。
- **ROADMAP_PHYSICS**（驗收唯一依據）：從 08-29 起幾乎沒更新，漏記 A14/D8/C10/D13/D15/D9c，§0 的 Water Gong 列沒指向 ENGINE_DOMAIN_CLAIMS。
- **CONTEXT.md、TODO_HANDOFF.md、RESEARCH_INDEX.md**：整份過時，沒標成歷史。RESEARCH_INDEX 的 D7/D8 編號還跟 TODO 撞號。
- **變現計畫與 clean_batch2**：沒進交接鏈；計畫裡還引用已被否決的 UI 雙開門。

---

## 6. 建議的下一步順序

1. 你審 staged，決定切 7 個還是 5 個 commit。我可以先把 §5 裡 HANDOVER/ROADMAP 那幾條過時文字修好，讓 c7 交接 commit 是乾淨的。
2. commit 並 push 之後：修 release CI，重跑 pluginval，用新 build 重新部署 VST3。
3. 同時由 AI 做弱基頻零點地圖，拿數字回來讓你決定給愛麗絲母帶去留。
4. 變現線：你裁那 5 題（第 3 題已可直接放）；AI 修 loop、授權檔、文案、THIRD_PARTY_NOTICES。
