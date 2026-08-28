# 音樂人 UX 痛點研究——「我的最愛」模式的系統化挖掘

> **狀態：draft，待 Opus 稽核。**
> 建立：2026-08-28（純研究，未落地任何程式碼）。
> 方法：WebSearch + WebFetch 直接開討論串／官方頁面查證，只收「親眼看到內文」的
> 一手來源；查不到內文、只憑標題推論的一律標「候選」。
> 目的：月月的「我的最愛」功能靈感來自看到別人抱怨其他合成器缺這個——
> 這份文件把這個「抱怨 → 功能」的模式系統化，挖掘更多同類型的機會。
> **重要澄清**：本 repo 目前（`src/PresetManager.h`）**沒有**「我的最愛」的程式碼，
> 只有 factory/user preset 的載入/儲存/刪除——「最愛」目前是月月口述的構想，
> 尚未落地。下文的「TsukiSynth 已有」一律以實際掃過的 `src/` 為準，不是猜測。

---

## 0. 白話：一段話講完

查了 KVR Audio、Gearspace、HISE 論壇、CLAP 規格 GitHub 討論、Surge XT 官方
無障礙頁與 GitHub issue，共挖到 **約 20 條一手痛點**，分 9 個主題。其中
**無障礙（視障音樂人）是最大的機會缺口**：目前 `src/PluginEditor.cpp` 完全沒有
鍵盤導覽或 screen reader 標籤（grep 零命中），只有 `HoverMagnifier`（放大文字，
給低視力用，不是給全盲用）。而 Surge XT——同樣是 **JUCE** 專案——已經做出
業界公認「最無障礙的合成器」，技術路徑完全可複製。這是本研究認為優先度
最高的功能靈感。

---

## 1. 痛點總表（依主題分類）

每條格式：**痛點** → 來源 → TsukiSynth 現況。

### 1.1 Preset 瀏覽／管理／我的最愛

| 痛點 | 來源 | TsukiSynth 現況 |
|---|---|---|
| 合成器要嘛把 preset 清單暴露給 host 但內部無管理，要嘛內建管理但不暴露給 host——兩者很少同時做好；使用者要跨多顆合成器搜尋/標籤 preset 完全沒有標準做法。beely：「the whole patch management thing is currently an inconsistent mess, really.」 | [KVR "Dilemma with preset management"](https://www.kvraudio.com/forum/viewtopic.php?t=445162) | **可做**：`PresetManager` 目前只有 factory/user 兩層清單，無標籤、無跨清單搜尋。 |
| u-he 的「我的最愛」只能用顏色標記，不能重新命名分類。boojiboy：「I'd love to be able to trawl through my sounds... and categorise the best sounds.」u-he 開發者 Urs 親自回覆：允許最愛自由改名會在資料庫裡產生 ambiguity/glitch 風險。 | [KVR "u-he Preset Browser"](https://www.kvraudio.com/forum/viewtopic.php?t=613409&start=15) | **可做，且是設計參考**：說明「最愛」不能只是打勾——要能分類/命名，但底層資料結構要先想清楚避免 Urs 提到的那種 ambiguity。 |
| 依名稱字母排序時，重新命名或搬動 preset 後使用者會迷失位置。Sir Hannes：「Stop jumping presets if renamed... I am lost now. Where I was before?」 | 同上 | **可做**：若做 preset 清單要記住「使用者上次瀏覽位置」，不要每次重排。 |
| 許多 sound designer 用字首分類 preset 命名，導致方向鍵逐一瀏覽時「連續聽到十幾個同類型的 pad」，難以獲得多樣靈感。u-he 用隱藏的「Discover」隨機挑選功能局部解決。 | 同上 | **可做**：隨機/多樣化瀏覽（非純字母序）是被驗證過的解法，可低成本抄。 |
| 「preset browser 沒有搜尋功能、沒有分類搜尋」被點名為「the single worst way to allow preset selections」（針對主畫面下拉選單式的瀏覽）。 | [KVR 一般討論摘要，見上方 WebSearch 結果] | **可做**：目前 GUI 無任何 preset 搜尋列。 |

### 1.2 Undo/Redo

| 痛點 | 來源 | TsukiSynth 現況 |
|---|---|---|
| Serum 在合成器本體「no undo in the actual synth」（wavetable editor 內有，但主參數沒有），被評論者點名「one little thing Vital has over Serum」。 | [KVR "Undo for Serum"](https://www.kvraudio.com/forum/viewtopic.php?t=606100) | **可做**：`PresetManager` 有 `isDirty()`/`setDirty()` 髒狀態追蹤，但沒有操作歷史堆疊，改參數後無法復原。 |
| 使用者請求隨機化按鈕旁加 undo：「clicking random, landing on the perfect sound, accidentally clicking it again, and losing it to the void forever」。 | [KVR "I want users to vouch..."](https://www.kvraudio.com/forum/viewtopic.php?p=9257515) | **可做**：TsukiSynth 若做隨機化/預設生成功能，undo 是必要配套，不是加分項。 |
| Surge XT 的 screen reader 選項會朗讀「Undo/Redo」操作結果——換句話說，undo 本身還牽動無障礙體驗（動作發生了但畫面看不到，需要語音回饋）。 | [Surge XT Accessibility 官方頁](https://surge-synthesizer.github.io/accessibility/) | **可做**：undo 與無障礙朗讀應該一起設計，見 §2。 |

### 1.3 旋鈕精度／微調

| 痛點 | 來源 | TsukiSynth 現況 |
|---|---|---|
| 旋鈕同時回應垂直與水平滑鼠移動，意外的水平位移會讓數值跳動，難以精準調整。 | [KVR "Behaviour and fine adjustment of knobs in plugins"](https://www.kvraudio.com/forum/viewtopic.php?t=478099) | 未溯源（未讀過 TsukiSynth 旋鈕元件原始碼是否受此影響，屬另一輪稽核範圍） |
| 微調普遍要求按住修飾鍵（Shift/Ctrl/Alt 不等）轉旋鈕才能細調，被批評對「需要空手彈奏同時調音色」的人不友善；建議改用同心圓環（中心粗調、外環細調，FabFilter 舊版做法）取代修飾鍵。 | 同上 | **可做**：若 TsukiSynth 旋鈕已用修飾鍵微調（常見 JUCE Slider 模式），可考慮加同心環替代方案。 |
| Surge XT 的鍵盤導覽方案：Up/Down 調值、Shift=更小增量、Ctrl/Cmd=量化步進、Enter=直接輸入數值、Delete=重設。這是「不靠滑鼠也能精準調」的完整解法，同時服務視障與非視障使用者。 | [Surge XT Accessibility 官方頁](https://surge-synthesizer.github.io/accessibility/) | **可做**：這組鍵盤語意比單純「Shift+拖曳」更完整，值得直接抄規格。 |

### 1.4 Preset 音量／初始化一致性

| 痛點 | 來源 | TsukiSynth 現況 |
|---|---|---|
| 大量軟體合成器的 preset 響度落差極大，某些 preset 峰值逼近甚至超過 0dBFS，是「業界普遍的爛習慣」，切換 preset 試音時要一直調音量，戴耳機時甚至有風險。SynthMaster 被點名做得比較好。 | [KVR "Soft synth presets - Differences in volume"](https://www.kvraudio.com/forum/viewtopic.php?t=469338)、[KVR "Diva presets too loud"](https://www.kvraudio.com/forum/viewtopic.php?t=347660) | 未溯源（TsukiSynth 現有 factory preset 是否有響度正規化，需查 `PresetManager`/`Presets.h` 內容或另開稽核，本輪未核對每個 preset 實測響度） |
| Synthmaster One 的主音量是「per preset」儲存且被批「太大聲」——反面案例：把音量存進 preset 本身而非獨立於 preset 之外的全域增益。 | [KVR "Synthmaster One: Master volume is per preset"](https://www.kvraudio.com/forum/viewtopic.php?t=535655) | **可做**：若 TsukiSynth 要加「安全音量」/一致性機制，應是獨立於 preset 資料之外的一層，而不是塞進 preset schema。 |
| 使用者要求 init/初始化 preset 選項，抱怨某些外掛「要自己手動存一個 init preset」而非內建選單選項。 | [KVR "Init presets, do want"](https://www.kvraudio.com/forum/viewtopic.php?t=245446)、[KVR "Init patch?"](https://www.kvraudio.com/forum/viewtopic.php?t=505040) | 未溯源（`PresetManager::initPreset()` 已存在此函式名稱，但本輪未讀其實作內容確認是否已對 GUI 曝光為選單項——標「候選」，需另核對） |

### 1.5 CPU 效能

| 痛點 | 來源 | TsukiSynth 現況 |
|---|---|---|
| CPU 用量直接決定「能疊幾軌」「能不能即時監聽混音」「要不要凍結軌道」。DJ Warmonger：「I like to run my full mix in real time and I get angry when I can't do so.」原 po 因 CPU 考量避開 Spire、把 Bazille 只拿來單獨算圖成音檔而非即時多軌使用。 | [KVR "How important is a synth's CPU usage?"](https://www.kvraudio.com/forum/viewtopic.php?t=453903&start=60) | 未溯源（TsukiSynth 為物理建模引擎，CPU 特性與本輪查到的 wavetable/減法合成案例不同源，需另開效能量測任務，不在本輪範圍） |
| 「CPU 友善」與「音色強大」被視為互斥的取捨——u-he Diva 幾乎是「業界最強類比模擬但 CPU 重」的公認案例，反覆被提及。 | 同上（forum 標題本身即 "Powerful synths that are CPU friendly?"） | 未溯源（同上） |

### 1.6 視窗縮放／GUI 尺寸

| 痛點 | 來源 | TsukiSynth 現況 |
|---|---|---|
| Kontakt 等大量外掛在 4K 螢幕上無法縮放，Soundtoys 官方明說「there are no plans currently to implement resizable GUIs」，被使用者列為長年未解痛點；反例是 Serum/Spire 用向量化 GUI 可自由縮放。 | [KVR "Soundtoys Plugins still not resizable?!?!"](https://www.kvraudio.com/forum/viewtopic.php?t=578347&start=345)、[KVR "FLStudio - Kontakt scaling on 4K"](https://www.kvraudio.com/forum/viewtopic.php?t=529842) | **已有**：`docs/GUI_DESIGN_GUIDE.md` 記載視窗預設 620×920、可縮放區間 540×820–1100×1400。此痛點 TsukiSynth 已經解決，非缺口。 |

### 1.7 MIDI 對應／學習

| 痛點 | 來源 | TsukiSynth 現況 |
|---|---|---|
| 部分 host（如 tracktion）能對某些合成器指派「上一個/下一個 preset」快捷鍵，但對另一些合成器（如 u-he 系列）不行——不一致性本身就是抱怨來源。 | [KVR "Dilemma with preset management"](https://www.kvraudio.com/forum/viewtopic.php?t=445162)（urlwolf 發言） | 未溯源（本輪未查到 TsukiSynth 是否已支援 host 端 preset 上一個/下一個的 MIDI/快捷鍵對應，且未查到 MIDI CC learn 相關一手抱怨串，標「候選待補搜」） |

### 1.8 無障礙／視障音樂人（重點章節，見 §2 深入分析）

見下一節。此處先列總表定位：

| 痛點 | 來源 | TsukiSynth 現況 |
|---|---|---|
| 旋鈕/滑桿數值無法用方向鍵/PageUp/PageDown/Home/End 調整，被列為「critical bug」等級的問題。 | [HISE 論壇 "Plugins for the visually-impaired users"](https://forum.hise.audio/topic/7426/plugins-for-the-visually-impaired-users-att-all-developers)（David Healey、Goran Rista 發言） | **可做**：`src/PluginEditor.cpp` grep 不到任何 `keyPressed`/`setWantsKeyboardFocus`，代表目前旋鈕完全沒有鍵盤操作路徑。 |
| 按鈕被 screen reader 誤讀成 "checkbox" 元件類型；裝飾性圖示（icon）擋在按鈕前面造成 screen reader 導覽雜訊。 | 同上（Goran Rista 發言） | **可做**：需要正確設定 JUCE `AccessibilityHandler` 的 role，而非讓框架猜測。 |
| CLAP 規格開發者討論：全盲使用者需要「screen reader 語音輸出獨立於主音軌路由，避免混音」、「GUI 缺乏鍵盤導覽與焦點管理」、「滑鼠 hover 沒有對應的無障礙工具通知」三大障礙；結論——無障礙該做在外掛程式碼本身（透過 OS 層 API），不是規格層的事。Surge 維護者 baconpaul 現身說法。 | [CLAP GitHub Discussion #225](https://github.com/free-audio/clap/discussions/225) | **可做**：這條直接告訴我們「JUCE + OS accessibility API」這條路線是對的，不需要等外部標準。 |

---

## 2. 深入：無障礙是最大的機會缺口（含可直接抄的技術規格）

### 2.1 為什麼標優先

- `src/PluginEditor.cpp` 目前 **零** 鍵盤導覽、**零** AccessibilityHandler 標籤——
  只有 `HoverMagnifier`（第 290 行附近註解「repeats small text enlarged」），
  這服務的是**低視力**放大需求，跟 screen reader 服務的**全盲**族群是兩回事。
- 這不是小眾議題：**MIDI Association 正在推「Music Accessibility Standard（MAS）」**，
  由多位全盲職業音樂人共同發起——Juho Tuomainen（芬蘭，用 Reaper+JAWS/NVDA）、
  Jean-Philippe Rykiel（巴黎）、Scott Chesworth（倫敦製作人，OSARA 無障礙外掛
  貢獻者）；產業端已有 Native Instruments、Arturia 表態關注，教育端有
  Berklee/哥倫比亞/Full Sail 參與，目標是 ISO 標準化。
  來源：[KVR "Music Accessibility Standard (MAS)"](https://www.kvraudio.com/forum/viewtopic.php?t=579136)
- **同樣用 JUCE 的 Surge XT 已經做出業界公認最無障礙的合成器**，且技術路徑
  完全公開透明——這代表 TsukiSynth 不需要從零發明，是抄規格的問題，不是
  做不做得到的問題。

### 2.2 Surge XT 技術路徑（可直接參考的規格）

來源：[Surge XT Accessibility 官方頁](https://surge-synthesizer.github.io/accessibility/)、
[GitHub Issue #4616](https://github.com/surge-synthesizer/surge/issues/4616)（baconpaul 於
2021-05-29 開的 issue，標籤 Accessibility / Rebuild With JUCE / UX，目標
Surge XT 1.0）。

- **鍵盤導覽**：Tab/Shift+Tab 在控制項間移動；方向鍵調整目前聚焦的參數；
  Alt+句號/逗號跳到主要介面區塊；Shift+F10 開右鍵選單；場景切換/振盪器選擇/
  調變管理各有專屬快捷鍵。
- **參數調值語意**：Up/Down 調值，Shift=更小增量，Ctrl(Cmd)=量化步進，
  Enter=直接輸入數值，Delete=重設為預設值。
- **Screen reader 主動朗讀**：可選開關，切換 patch/wavetable、加入或移除
  「我的最愛」、使用 Undo/Redo 時會有語音提示——**這條直接對應月月的
  「我的最愛」構想：Surge 已經證明「最愛」這個功能本身也需要無障礙語音回饋，
  不是做完視覺 UI 就結束。**
- **技術基礎**：走 JUCE 框架自帶的 accessibility layer（`AccessibilityHandler`），
  在 OS 層（Windows: MSAA/UIA 或 SAPI 語音；Mac: VoiceOver）自動介接，
  不需要外掛自己重新發明語音引擎。
- **誠實揭露已知限制**：Windows 上 patch 搜尋結果目前對 screen reader 不可見、
  選單關閉後的焦點變化偵測有延遲——兩者都標註為 JUCE 框架本身的已知問題，
  不是 Surge 的設計缺陷。這種「誠實列出限制」的做法本身也值得參考。

### 2.3 CLAP 開發者的三分法（可作為需求檢查清單）

來源：[CLAP GitHub Discussion #225](https://github.com/free-audio/clap/discussions/225)，
發起者 Trinitou，Surge 維護者 baconpaul 回應。

1. **色盲**：需要可自訂或高對比配色方案（TsukiSynth 現行深色系見
   `docs/GUI_DESIGN_GUIDE.md`，尚未查是否通過對比度檢查——候選待補查）。
2. **全盲**：(a) screen reader 語音輸出要能獨立於主聲音路由，避免語音跟音樂
   混在一起播出；(b) GUI 要有鍵盤導覽與焦點管理；(c) hover 狀態要能被輔助
   工具偵測到。
3. **結論**（baconpaul）：無障礙的落地點是「外掛程式碼本身把 OS 層 accessibility
   API 接好」，這件事發生在 CLAP／VST3 規格層之上，所以不需要等規格演進，
   現在就能做。

### 2.4 另一份一手佐證：視障音樂人挑選外掛的實際判準

來源：[KVR "Finding an accessible synth for a visually impaired person"](https://www.kvraudio.com/forum/viewtopic.php?t=623173)，
原 po **blindingSlow**，回覆者 **MrJubbly**。

視障使用者（未必全盲，含低視力）實際點名偏好的功能組合：
- 參數可用**數字鍵盤直接輸入**（雙擊或右鍵開文字框），不必靠精細拖曳；
- **滑鼠滾輪**支援粗調/細調兩檔；
- **深色介面**且**顏色可自訂**（例：黑底白字）；
- **介面夠緊湊**，減少為了看清楚而放大縮放、進而增加滑鼠移動疲勞。
被點名做得好的三套：FabFilter Twin 3、Kilohearts Phase Plant、Fors Pivot——
共同點是「數字輸入 + 滾輪 + 深色可自訂」，沒有一套宣稱做了完整 screen reader
支援（只有 Surge XT 做到這層級）。

---

## 3. 功能靈感清單（依優先序，比照「我的最愛」的誕生模式）

「我的最愛」的模式是：**看到別人抱怨某合成器沒有 X → TsukiSynth 做 X**。
下表延續這個模式，每條都標明「抱怨來源 → 對應功能」，依優先序排列。

| 序 | 抱怨來源（一手） | 對應功能 | 優先理由 |
|---|---|---|---|
| 1 | HISE 論壇：旋鈕/滑桿無法鍵盤調整；CLAP 討論：GUI 缺焦點管理；Surge：已證明 JUCE 能做到 | **JUCE AccessibilityHandler 全面接線**（Tab 導覽 + 方向鍵調值 + screen reader 標籤） | 目前是零基礎（grep 零命中），影響最大族群（全盲+低視力+鍵盤操作偏好者三種人共用同一套基礎設施），且有現成規格可抄，不必自己設計。 |
| 2 | u-he 論壇：最愛只能打勾/顏色，不能命名分類；Surge：最愛需要語音朗讀回饋 | **「我的最愛」功能本身**：不只是打勾清單，要能命名/分類，且與 §2.2 的 screen reader 朗讀掛鉤（加入/移除最愛時有語音提示） | 這正是月月構想的原始功能，現在有兩份一手證據告訴我們「最愛」做不好的兩種方式（u-he 的命名限制、多數合成器完全沒有語音回饋），可以一次避開。 |
| 3 | KVR 多串：preset 響度落差大、Synthmaster One 音量存進 preset 本身被批 | **獨立於 preset 之外的安全音量層**（不隨 preset 切換而暴衝，且不把音量寫進 preset schema） | 直接影響使用安全（耳機音量突變）與試音體驗，且 TsukiSynth 现有 `PresetManager` 結構改動成本可控（加一層 gain，不動 preset schema）。 |
| 4 | Serum 論壇：本體無 undo；隨機化按鈕無 undo 導致「landing on perfect sound, losing it forever」 | **參數層級 undo/redo 堆疊**（非僅 preset 存檔層級） | 與 #1 的無障礙朗讀直接掛鉤（Surge 的 screen reader 會朗讀 undo/redo 結果），一次設計兩個功能共用同一套操作歷史基礎設施。 |
| 5 | KVR "Dilemma with preset management"：preset 瀏覽無搜尋/無標籤/無法跨清單 | **Preset 搜尋列 + 標籤系統**（不是取代 §2 的「最愛」，是更廣的分類機制） | 目前 `PresetManager` 只有平面清單，是所有後續 preset 相關功能（含最愛、含 A/B）的地基，宜與 #2 一起規劃資料結構。 |

**未進入前五、但值得記錄的候選**：旋鈕同心圓環微調（取代修飾鍵）、u-he 的
「Discover」隨機瀏覽解法、preset 清單記住瀏覽位置。這些都屬於「錦上添花」
層級，優先度低於上面五項，因為上面五項有明確一手抱怨證明「使用者會因此
放棄某合成器」，這三項只是「體驗更好」。

---

## 4. 查證方法與限制（誠實揭露）

- 全部來源皆為 WebFetch 直接開啟討論串/官方頁面取得的內文摘要，非僅憑
  搜尋結果標題推論。凡標「未溯源」或「候選」的項目，代表本輪只查到標題/
  間接線索，未實際開啟內文核對，**不得在後續文件中當作已查證事實引用**。
- Reddit（r/synthesizers、r/edmproduction、r/WeAreTheMusicMakers）**本輪
  WebFetch 直接被拒**（工具回報「unable to fetch from www.reddit.com」），
  WebSearch 也未能命中對應版面的一手討論串內容——**此三個版面本輪掛零，
  是明確缺口，不是查過沒找到**。若後續要補，需要換一手能讀 Reddit 內文的
  管道（例如 Reddit 官方 API 或第三方鏡像），而不是繼續用同一組工具重試。
- Sound on Sound 等付費測評媒體本輪未能取得具體評論一手引文（搜尋只回傳
  部落格聚合文，非 Sound on Sound 原文），**標「未溯源」**。
- TsukiSynth 現況欄位僅以本輪實際 grep/read 過的檔案為準
  （`src/PresetManager.h`、`src/PluginEditor.cpp`、`docs/GUI_DESIGN_GUIDE.md`）；
  未讀到的部分（旋鈕元件原始碼、preset 響度實測、MIDI CC 對應現況）一律
  標「未溯源」，不得腦補。

---

## 5. 來源總表

| # | 標題 | URL |
|---|---|---|
| S1 | Dilemma with preset management (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=445162 |
| S2 | The u-he Preset Browser (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=613409&start=15 |
| S3 | Undo for Serum (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=606100 |
| S4 | I want users to vouch with me for a feature... (KVR) | https://www.kvraudio.com/forum/viewtopic.php?p=9257515 |
| S5 | Behaviour and fine adjustment of knobs in plugins (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=478099 |
| S6 | Soft synth presets - Differences in volume (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=469338 |
| S7 | Diva presets too loud (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=347660 |
| S8 | Synthmaster One: Master volume is per preset (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=535655 |
| S9 | Init presets, do want (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=245446 |
| S10 | Init patch? (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=505040 |
| S11 | How important is a synth's CPU usage? (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=453903&start=60 |
| S12 | Soundtoys Plugins still not resizable?!?! (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=578347&start=345 |
| S13 | FLStudio - Kontakt scaling on 4K monitor (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=529842 |
| S14 | Plugins for the visually-impaired users (HISE forum) | https://forum.hise.audio/topic/7426/plugins-for-the-visually-impaired-users-att-all-developers |
| S15 | Accessibility discussion (CLAP GitHub #225) | https://github.com/free-audio/clap/discussions/225 |
| S16 | Surge XT Accessibility (官方頁) | https://surge-synthesizer.github.io/accessibility/ |
| S17 | Use JUCE Accessibility branch... (Surge GitHub Issue #4616) | https://github.com/surge-synthesizer/surge/issues/4616 |
| S18 | Finding an accessible synth for a visually impaired person (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=623173 |
| S19 | Music Accessibility Standard (MAS) (KVR) | https://www.kvraudio.com/forum/viewtopic.php?t=579136 |

---

## 6. 待辦掛鉤

- 本文件建立時**未改動任何程式碼**，純研究產出，依 R7 未 add/commit/push。
- §3 優先序清單建議在下一次 GUI/preset 相關施工卡（workcard）開工前先過
  月月裁決——尤其 #1（無障礙基礎設施）改動範圍橫跨整個 `PluginEditor`，
  屬於架構層級決策，不是單一元件調整。
- §4 列出的缺口（Reddit 三版面、Sound on Sound、TsukiSynth 旋鈕原始碼/
  preset 響度實測/MIDI 對應現況）若要補，應開獨立的稽核任務，不要在
  同一輪裡用推論填空。

---

## 7. Opus 稽核記錄（2026-08-28）

稽核者：Opus 子代理，懷疑立場。方法：**不採信本文件自述的「已 WebFetch 開過」**，
對痛點抽 5 條以上重新開原始來源逐字核對；**不採信「TsukiSynth 現況」欄的自述**，
一律回 `src/` 重新 grep/read 驗證。未動 `src/`、`tests/`、`scores/`（僅讀取），
未 git add/commit/push（R7）。本節為追加。

### 7.1 抽查來源逐字核實（要求 5 條，實查 8 條）

| # | 抽查的痛點 | 本文件的引用 | 稽核者重新 WebFetch 取回的原文 | 判定 |
|---|---|---|---|---|
| S1 | §1.1 patch 管理是「inconsistent mess」+ 兩難 + tracktion 快捷鍵不一致 | beely：「the whole patch management thing is currently an inconsistent mess, really.」 | beely 原文：「Yeah, the whole patch management thing is currently an inconsistent mess, really.」；兩難由 **urlwolf** 原文佐證：「Many good synths have no preset management built in. But they expose the preset list to the host. Many good synths have some kind of built-in preset management. But they DO NOT expose the preset list to the host.」；§1.7 的 tracktion 說法亦命中：「in tracktion you can assign shortcuts to next and previous preset on say Charlatan (no manager) but not on say an U-he synth」 | **三項全部相符** |
| S2 | §1.1 u-he 最愛不能改名／重排迷失／Discover | boojiboy、Urs、Sir Hannes 三段引文 | Urs：「renaming a Favourite beyond the surface to something like 'Bass' is going to cause ambiguity and possibly glitches in the database.」；Sir Hannes：「…the preset jumps to another position due to ABC sorting. I am lost now. Where I was before?」；Discover 由 Urs 描述：「you get a random selection of those presets, up to 50, in a random order.」 | **相符**（boojiboy 原句為「…trawl through my sounds **from different programmers** and categorise the best sounds **across them all**」，本文件的省略號縮寫未失真，見 F5） |
| S3 | §1.2 Serum 本體無 undo | 「no undo in the actual synth」＋「one little thing Vital has over Serum」 | 發言者為 **swilow11**：「As above, no undo in the actual synth, but undo in wavetable editor.」「It's not ideal, and one little thing Vital has over Serum.」 | **相符** |
| S14 | §1.8 HISE：方向鍵無法調值、按鈕被讀成 checkbox、icon 造成雜訊 | 標為「David Healey、Goran Rista 發言」、「被列為『critical bug』等級」 | 三條 BUG 全部由 **gorangrooves（Goran Rista）** 提出：「BUG: Slider values can not be adjusted using arrow keys, nor page up/down, home/end.」「BUG: Buttons are read as 'checkbox' element type.」「I have many icons **behind** buttons that blind users must scroll through」 | **實質相符，措辭有兩處失準**，見 F5 |
| S15 | §1.8/§2.3 CLAP #225 三分法 | 發起者 Trinitou、baconpaul 回應、三大障礙、結論走 OS API | 發起者 **Trinitou**（2022-11-30）確認；三障礙逐條命中（「route this output only into monitoring but not into the audio master」／「jump to next/previous focus element」／「notify the host about the current mouse hover GUI element」）；baconpaul 結論：「This is nothing to do with CLAP...The accessible APIs are OS specific...not part of the CLAP spec.」 | **完全相符** |
| S16 | §2.2 Surge XT 鍵盤規格 8 項＋最愛語音＋已知限制 | Tab/方向鍵/Shift/Ctrl/Enter/Delete/Alt+句號逗號/Shift+F10；朗讀含「加入或移除最愛」；Windows 搜尋不可見＋選單焦點延遲 | **8 項按鍵語意逐條命中原文**；朗讀選項原文：「makes Surge XT speak additional messages when you change patches or wavetables, **add or remove a patch from favorites** and use the Undo/Redo features.」；兩條限制原文亦命中 | **完全相符**（本文件最關鍵的一條——「最愛需要語音回饋」——原文確實存在，非腦補） |
| S17 | §2.2 Surge Issue #4616 的 metadata | baconpaul 於 2021-05-29 開，標籤 Accessibility / Rebuild With JUCE / UX，目標 Surge XT 1.0 | 標題「Use JUCE Accessibility branch to bring reasonable accessibility to Surge XT 1.0」；opener **baconpaul**；日期 **May 29, 2021**；三個標籤逐字相同；milestone **Surge XT 1.0** | **五項 metadata 全部相符** |
| S19 | §2.1 MAS 的人名／公司／學校／ISO | Juho Tuomainen（芬蘭，Reaper+JAWS/NVDA）、Jean-Philippe Rykiel（巴黎）、Scott Chesworth（倫敦，OSARA）、NI/Arturia、Berklee/哥倫比亞/Full Sail、ISO 目標 | 三位音樂人自述逐條命中（「I am Juho Tuomainen, a blind... musician from Finland.」／「I am a blind musician from Paris France」／「I'm Scott from London, a fellow blind producer/musician who's also using REAPER」）；NI「want to follow the evolution of the standard」；Arturia 由 Athan Billias 表述；三校經 MIDI In Music Education SIG；ISO：「the standard would also be standardized with ISO」 | **相符**（人名／國籍／工具／機構全部無虛構） |

**S11（§1.5 CPU）另行核對，發現問題**，見 F2。

### 7.2 「TsukiSynth 已有／可做」標註逐條回 `src/` 核對

本文件全文**只有一處**標「已有」（§1.6），其餘為「可做」或「未溯源／候選」。逐條驗：

| 標註處 | 本文件宣稱 | `src/` 實況 | 判定 |
|---|---|---|---|
| §1.6 **已有**：視窗可縮放 620×920，區間 540×820–1100×1400 | 依據 `docs/GUI_DESIGN_GUIDE.md` | `src/PluginEditor.cpp:305` `setResizable (true, true);`／`:306` `setResizeLimits (540, 820, 1100, 1400);`／`:10-11` `kW = 620; kH = 920;`＋`:307` `setSize (kW, kH)` | **屬實，且數字逐一相符**。唯一的「已有」沒有亂標 |
| §0/§1.8/§3 無障礙「零基礎」 | `PluginEditor.cpp` grep 不到 `keyPressed`／`setWantsKeyboardFocus` | 稽核者把範圍**擴大到整個 `src/`**：`keyPressed`／`setWantsKeyboardFocus`／`AccessibilityHandler`／`setAccessible`／`setTitle`／`setDescription`／`setHelpText`／`grabKeyboardFocus`／`createFocusTraverser` **全部 0 命中** | **屬實，且比本文件宣稱的更強**（不只 PluginEditor，是全 repo 零命中） |
| §2.1 只有 `HoverMagnifier`（第 290 行附近註解「repeats small text enlarged」） | 服務低視力非全盲 | `src/PluginEditor.cpp:290` 原文：`// -- Hover magnifier (accessibility: repeats small text enlarged) ----`，**行號逐字命中**；元件本體在 `src/HoverMagnifier.h` | **屬實**（註解在 `.cpp` 290 行、class 在 `HoverMagnifier.h`，本文件敘述無誤） |
| §0/§9 行首澄清「repo 目前沒有『我的最愛』程式碼」 | 只有 factory/user 載入/儲存/刪除 | `src/PresetManager.h` 對 `favorite`／`Favorite`／`tag`／`Tag` **0 命中**；只有 `loadPreset`/`saveUserPreset`/`deleteUserPreset`/`scanUserPresets`/`initPreset` | **屬實** |
| §1.2 `PresetManager` 有 `isDirty()`/`setDirty()`、無操作歷史堆疊 | | `PresetManager.h:214-215` 確有兩者（`std::atomic` 實作）；全 `src/` 無 undo/redo 堆疊 | **屬實** |
| §1.1/§3#5 preset 只有平面清單、無搜尋 | | 全 `src/` 無 `searchBox`/`searchField`/preset filter | **屬實** |
| §3#5 括號提到「（含最愛、含 A/B）」 | | 全 `src/` 對 `A/B`／`abCompare`／`compareA`／`snapshotA` **0 命中** | **無誤標**。原句是列「後續要蓋在同一地基上的功能」，**並未宣稱 A/B 已存在**——稽核前的疑慮（「說已有 A/B 就要真的有」）**不成立** |

**結論：「已有／可做」欄位查無任何一處把沒有的功能寫成已有。**
反而查到**兩處把已經有的東西寫成「未溯源」**（低估自己），見 F3、F4。

### 7.3 Findings

- **F1（中）§1.5 第 2 列的來源引用是錯的，且該引用的標題從未被打開過。**
  該列來源欄寫「同上（forum 標題本身即 "Powerful synths that are CPU friendly?"）」。
  「同上」＝S11（`t=453903`）。稽核者重新開 S11，**該串的實際標題是
  "How important is a synth's CPU usage?"**，不是 "Powerful synths that are CPU friendly?"。
  後者是**另一串**、不在 §5 來源總表、本輪從未開啟。這違反 R3（沒親眼看到的來源不准引用）。
  同一列的「u-he Diva 幾乎是『業界最強類比模擬但 CPU 重』的公認案例，反覆被提及」
  在稽核者取回的 S11 內文中**未能證實**（回傳明確表示該特徵描述不在可讀內容中）。
  **建議**：整列改標「未溯源」，或把標題更正並把 Diva 那句刪掉／另尋一手來源。
  同列的 §1.5 第 1 列**完全屬實**（DJ Warmonger「I like to run my full mix in real time
  and I get angry when I can't do so.」逐字命中；Spire/Bazille 原文亦命中）。

- **F2（中）§1.1 第 5 列有一段加引號的引文，但沒有可開啟的來源，與 §4 的自我宣告互相矛盾。**
  該列來源欄寫「[KVR 一般討論摘要，見上方 WebSearch 結果]」，**無 URL、不在 §5 的 S1–S19 表內**
  （稽核者對全文做 URL 盤點：正文 19 個 URL、§5 表 19 個 URL、**雙向零孤兒**——唯一的例外
  就是這一列）。但引號內的「the single worst way to allow preset selections」是逐字引文格式。
  §4 第 1 點卻宣告「**全部**來源皆為 WebFetch 直接開啟討論串/官方頁面取得的內文摘要，
  非僅憑搜尋結果標題推論」。**這一列使該宣告不成立。**
  **建議**：補一手 URL，或把引號拿掉改述為「未溯源候選」，並修正 §4 的「全部」措辭。

- **F3（中）§1.4 第 3 列的「Init preset」被標成候選待核，但實際上 TsukiSynth 早就做了，
  而且是 GUI 上的獨立按鈕。**
  本文件寫「`PresetManager::initPreset()` 已存在此函式名稱，但本輪未讀其實作內容確認是否已對
  GUI 曝光為選單項——標「候選」，需另核對」。稽核者核對結果：
  `src/PluginEditor.cpp:190-198` 有 `presetInit` 按鈕，`onClick` 直接呼叫
  `proc.presetManager.initPreset()` 並 `rebuildPresetCombo()` + `updateDirtyIndicator()`，
  且 `addAndMakeVisible (presetInit)`。**比 KVR 那串抱怨的「要自己手動存一個 init preset」更好——
  是常駐按鈕，不是選單深處。** 標「候選」在 R4 意義上不算說謊（未查證就標未查證是誠實的），
  但**這是一個現成的賣點被漏記**。建議改標「已有」。

- **F4（中）§1.7 與 §1.1 第 1 列低估了現況：TsukiSynth 其實已經站在 urlwolf 那個兩難的「好的一邊」。**
  urlwolf 的抱怨核心是「要嘛暴露給 host 但無內部管理，要嘛有內部管理但不暴露給 host」。
  稽核者核對：`src/PluginProcessor.cpp:858-885` **完整實作了 host program 介面**——
  `getNumPrograms()` 回傳 `presetManager.getNumPresets()`、`getCurrentProgram()`、
  `setCurrentProgram()` 直接 `presetManager.loadPreset(index)`、`getProgramName()` 回傳
  preset 名稱，全部 routed through PresetManager；同時 `src/PluginEditor.cpp:167-185` 有
  內建的 `<`／`>` 上一個/下一個 preset 按鈕。
  **＝內部管理與 host 清單兩者同時具備，正是 S1 說「很少同時做好」的那件事。**
  §1.1 第 1 列只寫「可做：無標籤、無跨清單搜尋」（標籤/搜尋的部分屬實），
  §1.7 則整列標「未溯源」。建議兩處都補記「host program 清單已暴露＝該痛點的一半已解」。
  §1.7 的另一半（**MIDI CC learn**）稽核者確認**真的沒有**：全 `src/` 對
  `midiLearn`／`controllerNumber`／`ccNumber`／`MidiMessage::isController` **0 命中**，
  這半邊維持「缺口」正確。

- **F5（低）S14 的兩處措辭失準（不影響結論，但屬引文精度問題）。**
  (i) 本文件寫「被列為『**critical bug**』等級的問題」，原文只寫 `BUG:`，**沒有 "critical" 這個字**；
  加引號的「critical bug」會被讀成原文用語。
  (ii) 本文件寫「裝飾性圖示（icon）**擋在按鈕前面**」，原文是「icons **behind** buttons」（在按鈕**後面**）。
  功能面的抱怨（盲用使用者得逐一捲過這些 icon）兩種說法都成立，但空間關係被寫反了。
  (iii) §1.8 第 1 列標「David Healey、Goran Rista 發言」，但三條 BUG **全部出自 gorangrooves 一人**；
  David Healey 是 HISE 開發者、是回應方而非提報方。建議把第 1 列的署名收斂為 Goran Rista。

- **F6（低）§0 的兩個數字對不上。**
  (i) 寫「分 **9** 個主題」，但 §1 實際只有 **8** 個子節（1.1–1.8）；若把 §2.4 算進去要寫清楚。
  (ii) 寫「共挖到 **約 20 條**一手痛點」，§1 各表實際 21 列——「約」字可容納，不算錯，僅記錄。

- **F7（低）§0 說「查了…Gearspace…」，但 §5 的 19 個來源沒有一個來自 Gearspace，
  §4 的「誠實揭露」也沒把它列為掛零缺口。**
  §4 對 Reddit 三版面與 Sound on Sound 的掛零揭露得很好（明確寫「是明確缺口，不是查過沒找到」），
  但 Gearspace 享受了「有查」的敘述卻沒有任何產出、也沒被列入缺口清單。
  建議比照 Reddit 的寫法補一行，否則 §0 與 §4/§5 之間存在讀者無法察覺的落差。

**整體裁決**：本文件的**來源可信度很高**——抽查 8 條一手來源、涵蓋 KVR/HISE/GitHub/官方頁
四種載體，其中 7 條逐字相符（含最關鍵的 S16「Surge 的最愛需要語音回饋」與 S17 的五項 issue
metadata，都不是腦補）；**唯一的來源硬傷是 F1（§1.5 第 2 列引了一個沒開過的標題）與
F2（一段沒有 URL 的引文）**。
「TsukiSynth 已有／可做」欄位**查無任何一處把沒有的功能寫成已有**，唯一的「已有」（§1.6 可縮放）
逐一數字命中原始碼；無障礙「零基礎」的宣稱經全 `src/` 擴大 grep 後**比原文更強**。
反方向的偏差有兩處（F3 init 按鈕、F4 host program 介面），都是**低估自己**，
對 §3 的優先序影響是：#3/#5 的地基比文件以為的多、§1.7 應從「未溯源」降級為「一半已解」。
**§3 的前五名優先序本身不受任何 finding 動搖**——#1（無障礙）建立在 S14/S15/S16/S17/S19
五條全部核實的證據上，是本文件最紮實的一段。
