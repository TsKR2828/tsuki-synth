# 裁決包：IR user preset 不自包含（F-03，商品 recall blocker）

> 建立：2026-08-31　提問人：月月　狀態：**待裁決**
> 觸發：codex 稽核 F-03。本文所有 file:line 證據我都獨立回去看過原始碼複驗，
> 不是轉述稽核報告。
>
> **需要月月決定的只有兩件事**，其餘都是工程細節：
> 1. IR 資源怎麼跟著 preset 走（§3 的 A／B／C 三選一）
> 2. IR 檔不見時，該怎麼表現（§4）
>
> 這張單子不需要你懂 DSP，只需要你決定「使用者存了一個 preset，隔天打開，
> 應該聽到什麼」。

---

## 1. 現在會發生什麼事

使用者把 reverb 切到 IR 模式、載入一個 IR 檔、存成 user preset。
**這個 preset 沒有保存 IR。** 它只存了「模式＝IR」這個開關。

於是同一個 preset，會依「你在哪個 plugin instance 上打開它」得到三種不同的聲音：

| 情境 | 使用者看到 | 實際聽到 |
|---|---|---|
| 全新開的 plugin | 模式顯示 **IR** | **algorithmic reverb**（因為沒有 IR 可用） |
| 剛剛載過另一個 IR 的 instance | 模式顯示 IR，IR 名稱顯示**上一個 IR** | **上一個 IR**（完全無關的空間） |
| 原本那台、IR 檔還在 | 模式顯示 IR | 正確的 IR |

**一個 preset 應該是一個確定的聲音。現在它是一個「看你之前做過什麼」的聲音。**
這就是為什麼稽核把它列為 recall blocker——出貨後使用者存的音色是不可重現的。

### 1.1 程式證據（已複驗）

| 事實 | 位置 |
|---|---|
| user preset 只序列化 `apvts.copyState()`，不含任何 IR 資訊 | `src/PresetManager.h:139` |
| 載入 user preset 只做 `apvts.replaceState()`，不碰 EffectChain、不碰 IR 欄位 | `src/PresetManager.h:374-383` |
| `reverb_ir_path` **只**寫進 DAW state，不寫進 preset 檔 | `src/PluginProcessor.cpp:699-700` |
| 只有 `setStateInformation`（DAW 專案回復）那條路會重載 IR | `src/PluginProcessor.cpp:739-747` |
| `clearImpulseResponse()` 只翻一個 atomic flag，而且 preset 載入路徑從沒呼叫它 | `src/effects/EffectChain.h:98-101` |

### 1.2 一個容易被忽略的細節：UI 和音訊的「真相」是兩個變數

- UI 問的是 `hasReverbIR()`，也就是 `reverbIRName.isNotEmpty()`（`src/PluginProcessor.h:76`）
- 音訊問的是 `effectChain.hasImpulseResponse()`，一個獨立的 atomic（`src/effects/EffectChain.h:103`）

載入 user preset 時**兩個都沒被更新**，所以它們會各說各話。
新稽核那條「IR 按鈕可顯示 IR，但實際跑 algorithmic」就是這個分裂的外顯症狀。
**任何一個方案都必須把這兩個變數收斂成同一個真相來源**，這不是選項，是前提。

### 1.3 退回 algorithmic 不只是「換一個殘響」，音量也會跳

- algorithmic 的 wet 額外乘 `0.15`：`src/effects/SimpleReverb.h:155`
- convolution 的 wet 直接以 `m` 混合，**沒有**這個 0.15：`src/effects/EffectChain.h:204`

所以「靜默退回 algorithmic」不是溫和降級，是同時換了空間**和**響度。
（這是稽核的 K-02，目前還沒量化成固定 dB，因為 IR 本身振幅與 JUCE 的
normalization 也參一腳。但方向明確：退回不是無感的。）

---

## 2. 現有限制（會影響你怎麼選）

- IR 長度上限 **30 秒**：`src/PluginProcessor.cpp:787`
- preset 存放位置：`%APPDATA%/TsukiSynth/Presets`：`src/PresetManager.h:388-395`
- preset 是單一 XML 檔（`.tsukipreset`），目前純參數，很小

**體積參考**（30 秒是上限，實務上的空間 IR 多在 1–3 秒）：

| IR 長度 | 立體聲 24-bit WAV | 內嵌成 base64 後 |
|---|---:|---:|
| 1 秒 | 288 KB | 384 KB |
| 3 秒 | 864 KB | 1.15 MB |
| 30 秒（上限） | 8.6 MB | 11.5 MB |

---

## 3. 三個方案

### A. 內嵌（把 IR 塞進 preset 檔）

preset 存檔時把 IR 的音訊資料 base64 進 XML，載入時直接從裡面重建。

- ✅ **真正自包含**。一個檔案丟給別人就是完整的音色，換電腦、換 DAW 都一樣。
- ✅ 原始 IR 檔被刪除、改名、移動都不影響。
- ❌ preset 從幾 KB 變成 **MB 級**；十個用同一個 IR 的 preset 就存十份。
- ❌ 把第三方 IR 的音訊資料複製進每一個 preset 檔——如果那個 IR 有授權限制，
  分享 preset 等於在散布它。**這是法律面而不是技術面的問題。**
- ❌ preset 檔載入變慢（要解碼＋重建 convolution）。

### B. 複製到受管理的 IR 庫（推薦）

第一次載入 IR 時，把檔案複製到 `%APPDATA%/TsukiSynth/IR/<內容雜湊>.wav`，
preset 只記「雜湊＋原始檔名」。載入時從庫裡找。

- ✅ preset 檔維持很小。
- ✅ **同一個 IR 只存一份**，不管幾個 preset 用它（雜湊命名天然去重）。
- ✅ 使用者把原始 IR 檔刪掉／搬走／改名，preset 照樣正確——**這正是要修的那個失效**。
- ✅ 授權風險比 A 低：IR 只在本機複製一份，不會被夾帶進每個分享出去的 preset。
- ❌ **換電腦不會自動跟著走**（庫在本機）。要分享得另外做「匯出成含 IR 的包」。
- ❌ 庫會長大，未來需要一個清理機制（沒有 preset 引用的就可刪）。
- ❌ 要新增雜湊、複製、查找這套機制，是三個方案裡工程量最大的。

### C. 只存可攜的資源參考（路徑＋雜湊＋檔名）

preset 記住 IR 的絕對路徑，加上內容雜湊用來驗證「還是不是同一個檔」。

- ✅ 工程量最小，最接近現在 DAW state 已經在做的事。
- ✅ 完全沒有體積與授權問題。
- ❌ **它沒有真正解決 F-03。** 使用者刪掉／搬動 IR 檔，preset 就再次失效——
  只是從「靜默錯誤」變成「明確報錯」。是誠實了，但不是修好了。
- ❌ 換電腦幾乎必定失效（路徑不同）。

---

## 4. 第二個要決定的事：IR 不見的時候怎麼辦

不管選 A／B／C 都會遇到（A 最少），必須訂死：

| 選項 | 行為 | 評語 |
|---|---|---|
| **靜默退回 algorithmic** | 現況 | ❌ 就是這次的缺陷本身，而且還會跳音量（§1.3） |
| **保持出聲，但強制切回 algorithmic 模式 ＋ 顯眼警告** | 使用者聽得到東西，且 UI 不再謊稱是 IR | ✅ **建議** |
| **靜音 / 拒絕載入 preset** | 最「安全」 | ❌ 在 DAW 裡放到一半沒聲音，比走音更糟 |

建議第二個：**音訊永遠不能中斷，但 UI 絕對不能說謊**。

---

## 5. 我的建議

**選 B，並且把 A 當成「匯出」功能而不是預設儲存格式。**

理由：
- B 修掉的是實際會發生的失效（使用者整理硬碟、搬走取樣資料夾），
  而這正是 F-03 在真實使用中的樣子。
- A 的授權疑慮是真的：把別人的 IR 音訊夾帶進每個分享出去的 preset，
  責任在我們身上。B 只在本機複製一份，性質完全不同。
- C 工程最省，但它沒有修好問題，只是把失敗講清楚。單獨選 C 等於接受
  F-03 繼續存在——如果你想先出貨再說，這是可以的權宜，但要知道它是權宜。
- 未來要支援「把音色寄給朋友」，在 B 之上加一個「匯出成含 IR 的包」即可，
  那時再用 A 的內嵌邏輯，且只在使用者明確要分享時才承擔體積與授權。

**三個方案都必須一起做的前提**（不是選項）：
1. 收斂 §1.2 那兩個真相來源，讓 UI 與音訊不可能各說各話。
2. preset 載入時若沒有 IR，**必須主動清掉**上一個 IR 與它的 metadata，
   絕不可以沿用 instance 歷史。
3. 補三組 round-trip 測試：全新 instance／已載入別的 IR 的 instance／IR 檔不存在。
   `HostProbe H5` 只覆蓋 DAW state round-trip，**不覆蓋 user preset**，
   所以它全綠不能拿來反證這個缺陷。

---

## 6. 外部證據（2026-09-07）

> 本節由 WF0907-R3 研究卡新增，**§1–§5 原文一字未改**。
> **唯一的既有改動**：原本編號 §6 的「裁決欄」因為要空出 §6／§7 給本輪內容，往後移為 **§8**，
> 標題文字與內容完全沒動（該欄仍是空白待填）。repo 內沒有任何文件引用「F03 §6」，所以這次重編號不會打斷交叉引用。
> 存取日期一律 2026-09-07（部分查詢跨到 09-08 凌晨，已於來源清單標註）。
> 分級：**【官方】**＝廠商官方手冊／開發者在自家官網論壇的發言；**【社群】**＝使用者論壇貼文，
> 只當「使用者觀感／需求證據」，不當物理或工程證據（研究卡共同規約第 3 條）。
> 打不開的來源一律寫「未取得原文」，不憑記憶補。

### 6.1 一句話：查到的產品裡，沒有一個做「靜默用上一個 IR 頂替」

本輪查證 9 個對象（含月月自己的 DAW 內建 REVerence）。其中：

- **3 個 convolution 產品的官方手冊明確寫了缺檔行為**（REVerence、Waves IR-1、LiquidSonics Reverberate），
  三個都是**跳出來問使用者「檔案在哪」**。
- **2 個 convolution 產品（Altiverb、MConvolutionEZ）的手冊沒寫缺檔行為**——標「未取得官方說明」，不臆測。
- **3 個把資源直接收進 preset**（Aava、Vital、Serum 使用者 wavetable），**根本不會缺**。
- **1 個框架（HISE）提供「音訊檔隨 preset 一起還原」的現成開關**（`saveInPreset`）；
  原文只說「載入 preset 時會自動還原」，**沒有明說音訊資料是存進 preset 檔本身**，
  所以它算「不會缺」，但**不能拿來當 A（內嵌）的證據**（2026-09-08 第二輪複核降級）。

**在這 9 個對象裡，沒有任何一份官方說明或使用者回報描述「安靜地換成另一個聲音」。**
TsukiSynth 現在的行為（§1 那張表）在這 9 個對象裡找不到對應物——
**它不是業界慣例的一種變體，是本專案獨有的缺陷。**
（母體只有這 9 個，不等於「全業界」；未查到的見 6.7 末段。）

### 6.2 各家怎麼做（A 內嵌／B 受管理庫／C 路徑參考）

| 產品 | preset 實際存什麼 | 對應方案 | 缺檔時的行為 | 分級 |
|---|---|---|---|---|
| **Steinberg REVerence**（Cubase／Nuendo 內建，月月的 DAW） | 工廠 IR 走內建內容；使用者 IR 走檔案路徑 | **C（路徑）** | 跳 Locate 對話框要使用者指路；**而且指完不會自動記住** | 【官方】 |
| **Waves IR-1** | 參數 ＋「指向 IR 檔的指標」，IR 音訊在另一個 `.wir` 檔 | **C（路徑）** | 跳「Please locate: Filename」；取消＝不載入並顯示訊息；指到別的檔＝載入但**在畫面標示「換了別的 IR」** | 【官方】 |
| **LiquidSonics Reverberate 2** | 檔案參考 ＋ 三層自動找回機制 | **C＋救援** | ①自動找不到就問使用者 ②搜尋「我的最愛」位置 ③遞迴搜尋使用者指定資料夾；且要求**上一層資料夾名也要吻合**才算同一個檔 | 【官方】 |
| **Audio Ease Altiverb 8** | IR 只能放在三個被掃描的根資料夾（Audio Ease／User／Third party） | **B（受管理庫）** | 手冊未載明缺檔行為（**未取得官方說明**）；只寫可在 Preferences 改三個資料夾位置 | 【官方】 |
| **MeldaProduction MConvolutionEZ** | IR 用檔案選擇器＋「最愛」位置；preset 本身收在外部資料庫而非磁碟檔案 | **B/C 之間** | 手冊未載明缺檔行為（**未取得官方說明**） | 【官方】 |
| **Xfer Serum**（wavetable，同構問題） | 使用者 wavetable **內嵌進 preset**；工廠 wavetable 只記旗標不內嵌 | **A（分層內嵌）** | 開發者明說工廠內容「不內嵌以壓縮檔案大小」 | 【官方】開發者於自家論壇 |
| **Vital**（wavetable） | 全部 wavetable ＋ noise sample 一律內嵌，JSON 純文字 | **A（全內嵌）** | 不會缺；代價是體積（見 6.3） | 【社群】使用者實測 |
| **Viiri Audio Aava**（2026 新品，convolution） | **IR 壓縮後直接存進 preset** | **A（內嵌）** | 不會缺 | 【官方】開發者於 KVR 自述 |
| **HISE**（外掛開發框架） | 波形元件設 `saveInPreset` 後，載入 preset 時音訊檔**自動被還原**（原文未說明是否內嵌進 preset 檔） | **機制存在，歸類未定**（2026-09-08 由「A 可用現成機制」降級） | — | 【官方】框架維護者答覆 |

**原文引述（每條 ≤15 字）：**

- REVerence：「the old file paths have become invalid」／「The Locate Impulse Response dialog opens.」／
  「The new path to these audio files has not been saved yet.」／「you need to save your programs or presets under a different name」
  — Steinberg *Nuendo 10.3 Plug-in Reference*, "Relocating Content"。
- Waves IR-1：「IR properties and a pointer to the IR file」／
  「A complete preset is valid only if the related .WIR file is found.」／
  「a dialog box saying: "Please locate: Filename" opens」／「"IR was not loaded"」／
  「"Different IR loaded to preset" will be displayed」／「an imported .wav is not saved」
  — Waves *IR-1 software guide*, p.34「Saving Impulse Responses」。
- LiquidSonics：「When loading a preset, if impulse responses cannot be found」／
  「the user is asked to specify a file」／
  「Favourite locations are searched if a file is missing on disk at load-time」／
  「A file's folder must match to count as the same file」
  — *Reverberate 2 User Guide*, p.5「Lost Files Management」。
- Altiverb 8：「There are three folders that Altiverb scans for IRs」／
  「User contains everything you made yourself or you received from other users」
  — *Altiverb 8 manual*, p.8「Preferences tab / IR Folders」。
- MConvolutionEZ：「File lets you choose an impulse response file to process」／
  「are records in the preset database」
  — MeldaProduction *MConvolutionEZ* manual, p.7 / p.11。
- Serum（steve_xfer，Xfer 官方論壇）：「it will not embed in to user presets to keep file sizes down」／
  「Serum preset file format is complex/programmatic and isn't public」。
- Aava（ilmai，自述「I made this decision」，KVR）：「Aava actually stores IRs with the preset (compressed」／
  「to avoid the problem of moving the IRs and invalidating old DAW projects」。
- HISE（David Healey）：「set it to `saveInPreset` enabled」／
  「it will automatically be restored when the preset is loaded」——
  **原句只保證「還原」，沒有保證「內嵌」**。

### 6.3 內嵌（A）的代價，已經有人量過

| 證據 | 數字／說法 | 分級 |
|---|---|---|
| Vital 使用者實測整包 preset 體積 | 「Nearly half a gigabyte for just over 500 presets」＝平均約 **1 MB／preset** | 【社群】KVR |
| Vital 內嵌範圍 | 「The wt and noise sample are embedded into the preset」（Whywhy, 2020-12-11）；init patch 內嵌**四份**資料，其中**三份**是關掉沒在用的——「even though three of those four things are turned off and not used in the patch」（ahanysz, 2020-12-12） | 【社群】KVR |
| Serum 的分層對策 | 工廠內容不內嵌，「to keep file sizes down」 | 【官方】開發者 |
| Aava 的對策 | 「(compressed, so they take very little space」 | 【官方】開發者 |

**對照本專案 §2 的估算**：1 秒立體聲 IR base64 後約 384 KB、3 秒約 1.15 MB。
Vital 的 1 MB／preset 實測值與本專案的估算同一個量級，**§2 的數字沒有被外部證據推翻**。

### 6.4 使用者實際的抱怨（社群＝需求證據，不是工程證據）

| # | 出處 | 內容（原文引述 ≤15 字） | 日期 |
|---|---|---|---|
| C1 | Steinberg 官方論壇 "Importing Impulses Into REVerence + Save = Missing File?"（mart） | 「Reverance will ask for the path to the WAV」（重開專案就要重指一次，Cubase 7 起如此） | 2015-07-20 |
| C2 | 同上（MickGael） | 「prevented me from using it as much as i would like」 | 2015-07-20 |
| C3 | 同上（nkf） | 回報跨多台 Nuendo／Cubase 都會發生、記不記得住**沒有規律** | 2015-07-21 |
| C4 | Steinberg 官方論壇 "Load 200 Impulse Responses into REVerence…"（GuitboxGeek） | 「I did around 200 and I feel like jumping off a cliff」 | 2019-06-20 |
| C5 | 同上（ResonantMind） | 「it took me quite a few days and was extremely tedious and slow」（逐一匯入 3000 個 IR） | 2019-03-12 |
| C6 | KVR "Waves IR-L…"（whyterabbyt） | **使用者自己匯入 .wav 失敗**時：「loading wav files as new impulses does nothing except change the name listed in the menu」，同一句接著寫「there's no sound passed thorugh」 | 2012-12-28 |
| C7 | 同上（Gamma-UT） | 「the installer contains presets that refer to the full set of IRs」（安裝檔附了 preset，IR 本身卻沒隨附） | 2012-12-28 |
| C8 | KVR Aava 討論串（Velden，使用者身分回應開發者） | 「100% a very good move」（讚同把 IR 存進 preset） | 2026-05-19 |

> **C6／C7 是兩件不同的事，不可以併起來講**（2026-09-07 複核修正）。
> C6 的主詞是「loading wav files」——whyterabbyt 匯入**自己的 wav**沒成功；
> C7 是**散布層面**的問題：安裝檔附了指向完整 IR 組的 preset，但下載版沒附那些 IR。
> 同串 lfm（2012-12-30）指出實際成因是「`.xps` preset 檔為必要」，少了它 IR 就不會出現在選單。
> **「preset 指到沒安裝的 IR，結果只換了名字、沒有聲音」這個合併版說法，來源裡並不存在**，
> 前一版本文件寫了這句，本輪已刪除。

**這些抱怨真正共同指向的**：使用者不介意「被問一次檔案在哪」，
但**非常介意「每次都要問」（C1–C5）與「拿到的東西指向不存在的內容」（C7）**。
C6 的價值在另一個方向：它證明**「選單名稱換了、聲音卻沒換」這種畫面與音訊不一致的狀態，
使用者要花一整串貼文才搞得懂發生什麼事**——這正是 §7.2 第二條紅線要防的狀態，
但它不是「preset 缺檔」的證據。

### 6.5 技術限制：內嵌 MB 級資料到 preset，規範上有沒有擋？

| 問題 | 查到的結果 | 分級 |
|---|---|---|
| VST3 `.vstpreset` 格式對二進位大小有無上限 | 檔頭與 chunk list 的 offset／size 都是 **int64**；官方格式文件**沒有載明任何最大值** | 【官方】Steinberg VST3 開發者入口 |
| JUCE `setStateInformation` 能不能在裡面配置記憶體／載入音訊 | 「it doesn't happen on the audio thread」——不是 audio thread，可以配置，但要自己處理執行緒安全 | 【社群】JUCE 官方論壇 |
| JUCE 對 state 大小有無實務硬上限 | **查不到**明確數字（論壇上沒有人給過上限）。唯一硬事實來自**本機 JUCE 原始碼**，不是論壇：`getStateInformation (MemoryBlock&)`（`MemoryBlock` 內部大小型別為 `size_t`）與 `setStateInformation (const void*, int sizeInBytes)`，後者的 `int` 構成約 2 GB 的隱性上限，與本案 MB 級無關 | 【原始碼】`libs/JUCE/…/juce_AudioProcessor.h:1140` 與 `:1176`（非外部證據，僅供對照） |

結論：**沒有規範或框架層面的障礙擋住 A**。A 的代價純粹是體積、載入時間與第三方 IR 的授權責任（§3 已列）。

### 6.6 repo 現況複驗（2026-09-07，我親自重讀原始碼）

§1.1 的證據仍然成立，行號有小幅位移，複驗如下。

> **行號基準（2026-09-07 複核補記，非常重要）**：下表的 `src/PluginProcessor.cpp` 與 `src/PluginEditor.cpp`
> 行號是 **HEAD `98f346f`** 的行號，**不是現在工作樹的行號**。
> C++ lane 正在同一個工作樹平行改這兩個檔（`git diff --stat`：PluginProcessor.cpp +32/−1、PluginEditor.cpp +12/−4），
> 造成約 +30 行的位移——例如「silently degrades」那句註解在工作樹已經跑到 `:767`。
> **下一輪工程卡不可以照抄這些行號，要用關鍵字重新定位。**
> 其餘各檔（`PresetManager.h`、`EffectChain.h`、`SimpleReverb.h`、`PluginProcessor.h`、`RenderApp.cpp`）
> 在 HEAD 與工作樹上行號一致，我已逐條在工作樹上重看過。

| 主張 | 今天實際看到 |
|---|---|
| user preset 只序列化參數 | `src/PresetManager.h:136` `auto state = apvts.copyState();`（§1.1 記為 139） |
| 載入 user preset 只換參數樹 | `src/PresetManager.h:380` `apvts.replaceState (state.createCopy());`（§1.1 記為 374-383，函式起始在 374，一致） |
| IR 路徑只進 DAW state | `src/PluginProcessor.cpp:699-700` `if (reverbIRPath.isNotEmpty()) … setProperty ("reverb_ir_path", …)` |
| 只有 DAW state 那條路會重載 IR | `src/PluginProcessor.cpp:739-747`，且**原始碼註解自己寫著**「a missing file silently degrades to the algorithmic reverb」 |
| `clearImpulseResponse()` 只翻 flag | `src/effects/EffectChain.h:98-101` |
| UI 真相來源 | `src/PluginProcessor.h:76` `hasReverbIR()` ← 只看 `reverbIRName`；`src/PluginEditor.cpp:1063` 用它畫 UI |
| 音訊真相來源 | `src/effects/EffectChain.h:103-106` `hasImpulseResponse()` ← 獨立 atomic |
| algorithmic 額外乘 0.15 | `src/effects/SimpleReverb.h:155` `left = inL * dry + outL * mix * 0.15f;` |
| IR 上限 30 秒 | `src/PluginProcessor.cpp:787`（HEAD 行號） |

**新發現（不在 §1，供工程卡參考）**：`src/cli/RenderApp.cpp` 已經引入 `juce_SHA256.cpp` 並在用。
也就是說，方案 B 需要的「內容雜湊」在這個 repo 裡**不是新相依**，只是目前沒接到 plugin 端。

### 6.7 來源清單（URL ＋ 存取日期）

**【官方】廠商手冊／開發者發言**

1. Steinberg, *Nuendo 10 Plug-in Reference — REVerence: Relocating Content*
   https://archive.steinberg.help/nuendo_plugin_reference/v10/en/_shared/topics/plug_ref/reverence/reverence_content_relocating_t.html
   存取 2026-09-07。已取得整頁原文。
2. Waves, *IR-1 software guide*（PDF，p.33–34）
   https://assets.wavescdn.com/pdf/plugins/ir-convolution-reverb.pdf
   存取 2026-09-07。PDF 於本機解出文字後引用。
3. LiquidSonics, *Reverberate 2 Convolution Reverb User Guide*（PDF，p.3、p.5、p.14）
   https://downloads.liquidsonics.com/software/reverberate-2/manual/Reverberate2_User_Guide.pdf
   存取 2026-09-07。PDF 於本機解出文字後引用。
4. Audio Ease, *Altiverb 8 manual*（PDF，p.8）
   https://www.audioease.com/altiverb/files/Altiverb-8-manual.pdf
   存取 2026-09-08 凌晨（WebFetch 因超過 10 MB 上限失敗，改用 curl 下載後本機解字）。
5. MeldaProduction, *MConvolutionEZ* manual（PDF，p.6–7、p.11）
   https://www.meldaproduction.com/download/documentation/MConvolutionEZ.pdf
   存取 2026-09-07。
6. Steinberg VST3 Developer Portal, *Preset Format*
   https://steinbergmedia.github.io/vst3_dev_portal/pages//Technical+Documentation/Locations+Format/Preset+Format.html
   存取 2026-09-07。
7. Xfer Records 官方論壇, *File Types???*（steve_xfer，Xfer 開發者）
   https://xferrecords.com/forums/general/file-types
   存取 2026-09-07。**本文引用的兩句都出自 steve_xfer 2020-05-15 的同一則貼文**
   （2026-09-07 複核修正：原寫「2016-12-16 與 2020-05-15」有誤；2016-12-16 那則講的是 NMSV／FXP 檔案格式，與本卡無關）。
8. HISE 官方論壇, *Convolution Reverb embed one IR question*（David Healey）
   https://forum.hise.audio/topic/9287/convolution-reverb-embed-one-ir-question
   存取 2026-09-07。

**【社群】使用者論壇（需求證據，非工程證據）**

9. Steinberg 官方論壇, *Importing Impulses Into REVerence + Save = Missing File?*
   https://forums.steinberg.net/t/importing-impulses-into-reverence-save-missing-file/652285
   （mart 該則另見 `/652285/2`，已單獨取得原文）存取 2026-09-07。
10. Steinberg 官方論壇, *Steinberg, Load 200 Impulse Responses into REVerence…*
    https://forums.steinberg.net/t/steinberg-load-200-impulse-responses-into-reverence-tell-me-how-much-fun-you-have/124316
    存取 2026-09-07。
11. KVR Audio, *Aava – creative convolution plugin by Viiri Audio*（第 2 頁，ilmai／Velden）
    https://www.kvraudio.com/forum/viewtopic.php?p=9244778
    存取 2026-09-07。
12. KVR Audio, *Vital Preset, Wavetable, etc. thread*（第 2 頁，Whywhy／Ahanysz）
    https://www.kvraudio.com/forum/viewtopic.php?t=556602&start=30
    存取 2026-09-07。
13. KVR Audio, *Waves IR-L - where are the IRs and why wont it import?*（whyterabbyt／Gamma-UT／lfm）
    https://www.kvraudio.com/forum/viewtopic.php?t=369320
    存取 2026-09-07。
14. JUCE 官方論壇, *Is get state information thread safe?*（Nitsuj70, 2024-11-08）
    https://forum.juce.com/t/is-get-state-information-thread-safe-solved-use-setstateinformation-to-load-samples-and-dynamic-xml-values-without-ui-thread/64129
    存取 2026-09-07。**只支撐「it doesn't happen on the audio thread」這一句**；
    該串**沒有**討論 `size_t`／`int` 或任何 state 大小上限
    （2026-09-07 複核修正：那項型別事實已改掛本機 JUCE 原始碼，見 6.5）。

**打不開／未取得原文（誠實記錄，R4）**

- **Reddit 全站**：`WebFetch` 對 `www.reddit.com` 與 `old.reddit.com` 皆回「unable to fetch」，
  `site:reddit.com` 的 WebSearch 也沒有回傳任何相關討論串。
  **本輪沒有任何一條 Reddit 證據**；卡片 §1-B 想要的 r/audioengineering、r/edmproduction、
  r/Reaper、r/cubase 五條，實際只從 Steinberg 官方論壇＋KVR 取得八條（C1–C8）替代。
- **Gearspace**：`https://gearspace.com/board/music-computers/657443-waves-ir1-have-locate-impulse-files-each-time.html`
  回 HTTP 403，**未取得原文**。標題本身（「have to locate impulse files each time」）與 C1 同向，
  但因為沒讀到內文，不列為證據。
- **VI-Control**（Kontakt batch resave 會靜默存成缺樣本）：`vi-control.net` 回 HTTP 403，**未取得原文**。
  搜尋摘要提到「it resaves the patch with the samples missing」，但**未經原文核對，不採用**。
- **Native Instruments Kontakt 官方手冊**「Content Missing」章節：兩個候選 URL 皆回 404，**未取得官方說明**。
  Kontakt 那一列因此從 6.2 表中拿掉，而不是憑印象填。
- **REAPER ReaVerb**、**u-he（Zebra/Diva 使用者資源）**：本輪時間內未查到可引用的官方說明，
  **未取得官方說明**，不臆測。
  （**2026-09-08 第三輪補查已取得這兩家的官方手冊原文，見 §6.8**；本段保留，記錄當時的狀態。）
- **JUCE state 大小的實務上限**：**查不到**明確數字（見 6.5）。

---

### 6.8 第三輪補查（2026-09-08）：REAPER ReaVerb 與 u-he 兩個缺口已補上

> 本節由第四位 Opus 依 WF0907-R3 卡重跑本卡時新增，只針對 §6.7 末段標「未取得官方說明」的三家再查一次。
> **REAPER ReaVerb 與 u-he 已取得官方手冊原文；Kontakt 仍然沒有**（重試結果見本節末）。
> **§6.1–§6.7 與 §7.1–§7.4 一字未改**，本節只新增、不覆寫。
> 加上這兩家之後，§6.1 的查證母體從 **9 個變成 11 個**，而 §6.1 的結論
> **「沒有任何一個做靜默用上一個 IR 頂替」不變**——新增的兩家，一家未載明缺檔行為、一家明確跳錯誤訊息。

| 產品 | preset 實際存什麼 | 對應方案 | 缺檔時的行為 | 分級 |
|---|---|---|---|---|
| **Cockos ReaVerb**（REAPER 內建的 convolution reverb；REAPER 是 Cubase 之外的另一個主流 DAW） | `Add → File` 模組指到磁碟上的 impulse wav 檔；preset 存的是這條模組鏈的**參數**，IR 本身要使用者自己去網路上找 | **C（路徑）** | **官方手冊未載明**（兩份官方 PDF 全文檢索：`impulse` 與 `missing／not found／locate／relink` **從未出現在同一頁**）→ **未取得官方說明**，不臆測 | 【官方】 |
| **u-he Hive**（wavetable，與 IR 同構的「preset 依賴外部音檔」問題） | **wavetable 的路徑存在 preset 裡**，不是內嵌 | **C（路徑）** | 跳訊息「File wasn't loaded: [wavetable name]」，且**手冊明文警告使用者不要搬走／改名／刪除**已經被 preset 用到的 wavetable | 【官方】 |
| （旁證）**u-he Zebralette 3**（手冊版本 3.0，2025-12-04） | 拖進去的 .WAV 會被**偵測音高、切成單一 cycle**，變成 preset 裡的曲線資料 | 偏 A，但**手冊沒有明說 preset 是否仍依賴原檔**，故不列入 A 陣營 | — | 【官方】 |

**原文引述（每條 ≤15 字）：**

- **ReaVerb**（Cockos 官方 REAPER User Guide v7.79，p.330）：
  「you will need impulse wave files」／「Search the net to find all you want」／
  「save that set of parameters as a named preset」。
  ReaVerb 的 File 模組（*REAPER Effects Guide 2021*，p.37）：
  「select a different reverb impulse file」——**只有 Browse，沒有任何找回機制的描述**。
- **u-he Hive**（*Hive user guide*，p.44，WAVETABLES 章開頭的 IMPORTANT 方框）：
  「File wasn't loaded: [wavetable name]」／
  「the wavetable's path as stored in the preset is invalid」／
  「Be careful not to move, rename or delete wavetables」／
  「If you do lose factory wavetables, simply re-install Hive」。
- **u-he Zebralette 3**（*Zebralette 3 user guide*，p.31）：
  「The import routine detects pitch then slices the sample」／
  「Wavetable Import (experimental!)」。
- **u-he preset 格式為純文字**（*Zebra2 user guide*，p.11）：
  「our normal cross-platform format (editable text)」——
  這解釋了 u-he 為什麼不走內嵌：**.h2p 是純文字設定檔，塞不下音訊資料**。

**這兩列為什麼有價值（不是湊數）：**

1. **ReaVerb 補上了「另一個 DAW 內建 convolution」的對照**。它和 REVerence 一樣是 C（路徑），
   但它連缺檔行為都沒寫在手冊裡——這是**比 REVerence 更弱的一端**，
   證明 §6.2 表裡「官方寫明缺檔行為」的那三家（REVerence／IR-1／Reverberate）是**認真做過這件事的少數**，不是業界底線。
2. **Hive 是本文查到的第四個「明講」的官方例子，而且話術最短、最可以直接抄**：
   它把「哪個檔」（檔名）＋「為什麼」（preset 裡存的路徑失效了）兩件事塞進一句話。
   §7.2 那張三態表的第三態要顯示什麼字，Hive 這句就是現成範本。
3. **Hive 同時是 C 方案代價的官方自白**：手冊要求使用者「不要搬走、不要改名、不要刪除」，
   等於官方承認 **C 把維護責任丟給使用者**。這正是 §7.3 說「改選 C＝把已知痛點原封搬進來」的獨立佐證，
   而且這次是**廠商自己寫的**，不是使用者抱怨。

**Kontakt 重試記錄（仍未取得，誠實記錄 R4）：**
`support.native-instruments.com/hc/en-us/articles/6625686332317-…`（WebSearch 指到的官方文章）
以 `WebFetch` 回 **HTTP 404**、以 `curl` 帶瀏覽器 UA 同樣回 **HTTP 404**；
`…/4408645722257-…` 亦回 404；`www.native-instruments.com/ni-tech-manuals/kontakt-manual/en/` 回 404；
第三方鏡像（Westwood Instruments help centre）回 **HTTP 403**。
WebSearch 摘要裡出現的「Browse for Folder」等字句**未經原文核對，不採用**。
**Kontakt 這一列維持不列入 §6.2 表**，與前兩輪相同。

**Reddit 重試記錄（仍然零證據）：**
`WebFetch` 對 `www.reddit.com` 回「unable to fetch」（工具層拒絕）；
`curl https://www.reddit.com/search.json?...` 帶瀏覽器 UA 回 **HTTP 403**；
以 `site:reddit.com` 為導向的 WebSearch 回傳的全是商品頁與非 Reddit 論壇。
**本文到第三輪為止仍然沒有任何一條 Reddit 證據**，§7.4 的這條缺口不變。

**新增來源（接續 §6.7 的編號）：**

15. Cockos, *Up and Running: A REAPER User Guide v7.79*（PDF，p.329–331）
    https://www.reaper.fm/userguide/ReaperUserGuide779a.pdf
    存取 2026-09-08。本機下載 29,887,921 bytes，sha256 前 16 碼 `ff7ba1fbfa12f25a`，462 頁，PyMuPDF 解字。
16. Cockos, *REAPER Effects Guide (2021)*（PDF，p.35–39，ReaVerb 章）
    https://www.reaper.fm/userguide/REAPEREffectsGuide2021.pdf
    存取 2026-09-08。本機下載 2,706,851 bytes，sha256 前 16 碼 `b91701e03916f0e5`，63 頁。
17. u-he, *Hive user guide*（PDF，p.44）
    https://u-he.com/downloads/manuals/plugins/hive/Hive-user-guide.pdf
    存取 2026-09-08。本機下載 4,060,919 bytes，sha256 前 16 碼 `cb2bdcb5ef066f88`，82 頁。
18. u-he, *Zebralette 3 user guide*（PDF，p.31）
    https://uhe-dl.b-cdn.net/manuals/plugins/zebralette3/Zebralette3%20user%20guide.pdf
    存取 2026-09-08。本機下載 3,451,483 bytes，sha256 前 16 碼 `d72895767ddd4226`，72 頁。
19. u-he, *Zebra2 user guide*（PDF，p.11、p.36）
    https://u-he.com/downloads/manuals/plugins/zebra2/Zebra2-user-guide.pdf
    存取 2026-09-08。本機下載 5,529,837 bytes，sha256 前 16 碼 `d4a1230e0590b437`，114 頁。
    （Zebra2 只**匯出** wavetable、不匯入外部音檔，**不構成 preset 依賴外部檔案的案例**，
    僅用來佐證 u-he preset 是純文字格式。）

> 五份 PDF 都留在 `output/wf0907/R3/`（gitignored），稽核可離線用
> `python -c "import fitz;d=fitz.open('Hive-user-guide.pdf');print(d[43].get_text())"` 重現引述。

### 6.9 第三輪 repo 複驗（2026-09-08，工作樹現況）

§6.6 的每一條我都在**今天的工作樹**上重新 grep 過，全部成立；行號如下（**與 §6.6 的 HEAD 行號不同，位移仍在變**）：

| 主張 | 工作樹現在的位置 |
|---|---|
| user preset 只序列化參數 | `src/PresetManager.h:136` `auto state = apvts.copyState();` |
| 載入 user preset 只換參數樹 | `src/PresetManager.h:380` `apvts.replaceState (state.createCopy());` |
| `reverb_ir_path` 只進 DAW state | `src/PluginProcessor.cpp:730` |
| 「silently degrades」註解 | `src/PluginProcessor.cpp:767`（HEAD 為 `:739-747` 區塊） |
| `clearImpulseResponse()` 只翻 flag、且**仍然沒有任何呼叫者** | `src/effects/EffectChain.h:98` |
| 音訊真相來源 | `src/effects/EffectChain.h:103` `hasImpulseResponse()` |
| UI 真相來源 | `src/PluginProcessor.h:76` `hasReverbIR()` ← 只看 `reverbIRName` |
| algorithmic 額外乘 0.15 | `src/effects/SimpleReverb.h:155-156` |
| IR 上限 30 秒 | `src/PluginProcessor.cpp:815-819`（HEAD 為 `:787`）；錯誤字串「Impulse response longer than 30 s refused」 |

**§6.6 的行號警告在第三輪依然有效**：`PluginProcessor.cpp` 的位移量從 +30 行左右繼續在動。
**WF0908-P3 施工卡務必用關鍵字定位，不可照抄任何一版行號。**

---

### 6.10 第四輪補查（2026-09-08）：Kontakt 缺口補上 ＋ 三份 IR 授權合約 ＋ Cubase 現行版本確認

> 本節由第五位 Opus 依 WF0907-R3 卡重跑本卡時新增。**§6.1–§6.9 與 §7.1–§7.5 一字未改**，本節只新增。
> 本輪只做三件事：①把三輪都沒拿到的 **Kontakt 官方說明**補上；
> ②替 §3-A「內嵌有授權風險」這個**原本完全沒有外部來源**的主張去找真正的合約條文；
> ③確認 REVerence 的行為在**月月現在會用到的 Cubase 版本**上還是一樣（前三輪引的是 Nuendo 10 存檔版）。
> 所有引述都來自我本機下載的檔案（sha256 列在 §6.10.6），不是搜尋摘要。

#### 6.10.1 Kontakt（三輪未取得，本輪取得）——它把 A／B／C 三個方案**同時做成三個存檔選項**

Kontakt 存 Instrument 時，「Save as」對話框有三個選項，對應本裁決包的三個方案，**一模一樣**：

| Kontakt 的選項 | 它做什麼 | 對應本卡方案 |
|---|---|---|
| **Patch Only** | 「only saves file references in the instrument file」 | **C（只存路徑）** |
| **Patch + Samples** | 「copy the contained Samples to a new location」，並「changing the file references within the Instrument to the copies」 | **B（複製到受管理位置）** |
| **Monolith** | 「the Sample data gets embedded in the file itself」 | **A（內嵌）** |

**Kontakt 官方對這三者的評語，正好就是 §7.1 的分工：**

- Patch Only 的代價，手冊自己寫：「moving references samples on the hard drive will result in missing samples」
  （原文有 typo `references samples`，照抄不改）。
- Monolith 的定位，手冊自己寫：「This is the safest option to choose in terms of keeping Sample references intact」，
  而且**「a good way to create Instruments that should be distributed to other users」**。

> **這一句是本輪最有價值的發現。**
> §7.1 建議「平常用 B、要送人時才走 A 的內嵌」，這在前三輪是**我們自己的推論**；
> 現在有一家以樣本器著稱的廠商，在官方手冊裡用同樣的分工講同樣的話：
> **內嵌不是預設儲存格式，是「要給別人」時才用的格式。**

**還有一條直接支持「用內容雜湊、不要用檔名」：**
Kontakt 找不到樣本時預設只比對檔名，手冊承認這會出事——
「two or more different Samples on your hard disk might share a common name」，
而且「This can cause Kontakt to load the wrong Sample」。
所以 Kontakt 額外做了一個 **Check for Duplicates** 開關來「examine any files with matching names more thoroughly」。
**本卡 §7.1 的「用內容雜湊當檔名」不是過度設計——它是直接繞開 Kontakt 這個已知的坑**
（LiquidSonics 也踩過，它的解法是「上一層資料夾名也要吻合」，見 §6.2）。

**Kontakt 缺檔時的行為（第 12 個對象，仍然不是靜默頂替）：**
找不到就開 Content Missing dialog（「Kontakt will open a Content Missing dialog」），
上半顯示找不到的檔案清單與「assumed at」位置，下半提供自動搜尋（Search Filesystem／Spotlight）與手動指路（Browse for Folder／Files）。
全部失敗時，手冊說「they either don't exist on your system anymore, or have been renamed」，
使用者只有兩個選擇：「abort loading the Instrument by clicking the right button」，
或者「load the Instrument without the missing Samples with the left button」。
**沒有第三個選項叫「安靜地換一個樣本」。**

另外對 DAW 專案的部分，Kontakt 手冊明說：「Sample references will be saved in an absolute fashion」，
所以搬了樣本再開專案就會跳 Samples Missing——**和本專案 `setStateInformation` 那條路的問題同構**。

#### 6.10.2 母體從 11 個變 12 個，§6.1 的結論仍然不變

加入 Kontakt 之後：

- 有官方缺檔說明的：REVerence、Waves IR-1、LiquidSonics、u-he Hive、**Kontakt** = **5 個**
- 未載明缺檔行為：Altiverb、MConvolutionEZ、ReaVerb = 3 個
- 資源收進 preset／不會缺：Aava、Vital、Serum 使用者 wavetable = 3 個
- 框架、歸類未定：HISE = 1 個

**12 個對象裡，做「靜默用上一個資源頂替」的仍然是 0 個。**
（母體是這 12 個，不等於全業界；未取得的見 §6.10.5。）

#### 6.10.3 §3-A 的「授權風險」——本輪第一次拿到真正的合約條文

§3-A 寫「把第三方 IR 的音訊複製進每一個 preset 檔……是法律面而不是技術面的問題」。
**前三輪沒有任何來源支持這句。** 本輪查了三份實際在賣 IR 的廠商合約，三份都有明文禁止散布：

| 廠商 | 條文原句（≤15 字引述） | 對「內嵌進 preset 再分享」的意義 |
|---|---|---|
| **Audio Ease（Altiverb 的 IR）** | 「may not rent, lease, loan or distribute the IMPULSE RESPONSES」；另有「may not electronically transmit the IMPULSE RESPONSES in whole or in part」；且「licensed only for use in Altiverb」 | 最嚴：不只禁止散布，連「只授權在 Altiverb 裡用」都寫死 |
| **Eminence Digital** | 「shall not redistribute, sell, lease, sublicense, or transfer the IRs」（第 3 條第 i 款） | 明文禁止把 IR 轉給第三方 |
| **CelestionPlus** | 「not rent, lease, sub-license, redistribute, loan, provide, or otherwise make available」 | 「otherwise make available」涵蓋「把 preset 貼到網路上」 |

**所以 §3-A 的擔心是有依據的，不是我們自己想的。**

> **同時要誠實講清楚兩件事（R4 誠實原則）：**
> 1. **我不是律師，本文不是法律意見。** 這三份合約只證明「市售 IR 的授權普遍禁止散布」，
>    不證明「內嵌進 preset 一定違法」，也不證明「B 一定合法」。
> 2. **B（本機複製一份進庫）沒有觸發上面這幾條的字面內容**——它們管的是
>    rent／lease／loan／distribute／transfer／make available／electronically transmit，
>    都是「把東西給別人」；B 是使用者自己的電腦上多一份自己已經授權在用的檔案。
>    但 Audio Ease 那句「licensed only for use in Altiverb」提醒我們：
>    **有些 IR 的授權會限定用在哪個外掛**，這一點 A 和 B 都碰得到，只是 A 還多了散布那一層。
>    這件事不影響 §7.1 選 B＋，但**「匯出成含 IR 的包」那個功能上線時，UI 應該提醒使用者自己確認授權**。

#### 6.10.4 REVerence：換成月月現在會用到的版本，行為完全一樣

前三輪引的是 Nuendo 10 的存檔文件（archive.steinberg.help）。本輪改查 **Cubase Pro 15.0 現行線上手冊**，四句照樣在：

- 匯入 IR 時到底發生什麼：「the impulse response file itself is only referenced」，
  而且「It still resides in the same location as before and is not modified」——
  **官方確認 REVerence 是 C（路徑參考），不複製、不內嵌。**
- 搬檔之後：「the old file paths have become invalid」→「The Locate Impulse Response dialog opens.」
- 指完路徑還不算完：「you need to save your programs or presets under a different name」。

**還有一句直接背書 §7.1 的「工廠／使用者分流」：**
「The factory content is not a problem because it is also present」（後接 on the other computer，引述依≤15 字規定截至此）
**Steinberg 自己把「工廠內容」和「使用者自己的 IR」分開處理**，理由和 Serum 一樣（大家電腦上都有，不用再抄一份）。
§7.1 分層表第一列在前三輪只有 Serum 一個來源，現在有第二個、而且是月月的 DAW。

#### 6.10.5 本輪新增的社群證據（C9–C11）與仍然打不開的來源

新的一串 Steinberg 官方論壇討論（**社群＝需求證據，不是工程證據**），
它把 C1–C5 的時間跨度從 2015–2019 延長到 **2018–2022**：

| # | 出處 | 原文引述（≤15 字） | 日期 |
|---|---|---|---|
| C9 | Steinberg 論壇 "Impulse response file missing"（MERC476） | 「When I click a preset, it states that the impulse response is missing」 | 2018-02-08 |
| C10 | 同串（stingray_493，升級 10.5→11 後） | 開範本就跳「can not locate reverb impulse response file」 | 2021-01-07 |
| C11 | 同串（jds_global，換新電腦後開舊專案） | 「the dreaded "impulse response files missing" message on two separate instances」 | 2022-12-14 |

> **這三條要小心解讀（不可過度延伸）**：同串 andreasm／Romantique\_Tp／pjchappy 的回覆顯示，
> C9–C11 有相當部分**其實是工廠 `.vstsound` 內容被裝到錯的資料夾**，不是使用者自己的 IR 不見。
> 所以它們**不能**當成「使用者 IR 路徑失效」的證據；
> 它們能證明的是另一件事，而且對本卡一樣重要：
> **「preset 指向外部內容」這個設計，連工廠內容都會出事，而且使用者完全查不出原因**
> （C9 從 2018-02-08 問到 2018-03-05 才有人找出是安裝路徑錯）。

**仍然打不開／未取得原文（第四輪重試結果，誠實記錄，R4）：**

- **Reddit：第四輪仍然全數失敗。** 本輪試了 **3 條不同路徑**，全部被擋：
  `WebFetch https://www.reddit.com/search.json?...` → 「unable to fetch」；
  `WebFetch https://old.reddit.com/r/audioengineering/search.json?...` → 「unable to fetch」；
  `curl` 對 `www.reddit.com`／`api.reddit.com`／`old.reddit.com` 三個網域的 `.json`／`.rss` 端點 → **全部 HTTP 403**。
  另外用 `site:reddit.com` 做 WebSearch 兩次，回傳結果裡**沒有任何一條是 reddit.com 的網址**。
  **本卡累計四輪、零條 Reddit 證據。** 月月 2026-09-07 明示可以用 Reddit，
  但這台機器的網路環境打不開它——這是**環境限制，不是沒去找**。
- **Gearspace**：`curl` 帶瀏覽器 UA 重試同一個討論串，仍然 **HTTP 403**（第二次確認）。**未取得原文。**
- **Cubase Pro 13 plug-in reference PDF**：`steinberg.help` 把 HTML 頁 301 導到一個 PDF，
  該 PDF 再 301 且 `curl -L` 取回 0 bytes（HTTP 301 size 0）。**未取得原文**；
  改用 **Cubase Pro 15.0 的線上 HTML 手冊**（§6.10.4），內容已足夠。
- **VI-Control**（第三輪已記為 403）：本輪未再重試。

#### 6.10.6 本輪證據檔（本機留存，供複核）

| 檔案（`output/wf0907/R3/round4/`） | sha256 前 16 碼 | 用途 |
|---|---|---|
| `kontakt_classic.html`（564 KB，NI 官方手冊 Classic view 整頁） | `846a09243ad7d17d` | §6.10.1 全部 Kontakt 引述 |
| `Altiverb_EULA.pdf`（4 頁） | `dd3782b0108f9874` | §6.10.3 Audio Ease 三句 |
| `eminence_eula.html` | `d6cae1940e3c8bee` | §6.10.3 Eminence 一句 |
| `celestion_eula.html` | `8b11027e007b3c0b` | §6.10.3 Celestion 一句 |
| `steinberg104562.json`（論壇原始 JSON，逐則含作者與時間戳） | — | C9–C11 |

**本輪新增來源清單（URL ＋ 存取日期 2026-09-08）**

15. Native Instruments, *Kontakt User Guide — Classic view*（含 "Saving instruments"、"Samples Missing dialog"、"Batch resave"）
    https://docs.native-instruments.com/ni-tech-manuals/kontakt-manual/en/classic-view
    存取 2026-09-08。`curl` 取回整頁 HTML（HTTP 200，564,636 bytes）後本機剝標籤檢索。
    （前三輪標「404 未取得」的兩個候選 URL 是 `www.native-instruments.com/...` 路徑；
    該網域現在 301 導到 `docs.native-instruments.com`，本輪即由此取得。）
16. Audio Ease, *Altiverb 8 and Impulse Responses EULA*（PDF，p.3–4「Audio Ease IMPULSE RESPONSES license agreement」第 2 條 Restrictions）
    https://www.audioease.com/altiverb/files/Altiverb_8_and_Impulse_Responses_EULA.pdf
    存取 2026-09-08。
17. Eminence Digital, *EULA*（第 3 條 RESTRICTIONS 第 i 款）
    https://eminence-digital.com/pages/eula
    存取 2026-09-08。
18. Celestion, *CelestionPlus Impulse Responses — End User Licence Agreement*（Licence restrictions 段）
    https://www.celestionplus.com/eula/
    存取 2026-09-08。
19. Steinberg, *Cubase Pro 15.0 Plug-in Reference — REVerence: Relocating Content*
    https://www.steinberg.help/r/cubase-pro/cubaseplugref/15.0/en/_shared/topics/plug_ref/reverence/reverence_content_relocating_t.html
    存取 2026-09-08。
20. Steinberg, *Cubase Pro 15.0 Plug-in Reference — REVerence: Importing Impulse Responses*
    https://www.steinberg.help/r/cubase-pro/cubaseplugref/15.0/en/_shared/topics/plug_ref/reverence/reverence_importing_impulse_responses_t.html
    存取 2026-09-08。
21.（【社群】）Steinberg 官方論壇, *Impulse response file missing*
    https://forums.steinberg.net/t/impulse-response-file-missing/104562
    存取 2026-09-08。以 `.json` 端點取回原始貼文，逐則核對作者與日期。

---

### 6.11 第四輪 repo 複驗（2026-09-08，工作樹現況）＋ 一個給 P3 卡的新發現

§6.6／§6.9 的每一條我都在**今天的工作樹**（HEAD `98f346f`）上重新 grep 過，**全部仍然成立**。
行號**又動了一次**（`PluginProcessor.cpp` 的 30 秒上限從 `:819` 出現在錯誤字串那行）：

| 主張 | 第四輪 grep 到的位置 |
|---|---|
| user preset 只序列化參數 | `src/PresetManager.h:136` `auto state = apvts.copyState();` |
| 載入 user preset 只換參數樹 | `src/PresetManager.h:380` `apvts.replaceState (state.createCopy());` |
| `reverb_ir_path` 只進 DAW state | `src/PluginProcessor.cpp:730` |
| 「silently degrades」註解 | `src/PluginProcessor.cpp:767`（讀回在 `:769`） |
| `clearImpulseResponse()` **全 repo 仍然零呼叫者** | `src/effects/EffectChain.h:98`；`grep -rn clearImpulseResponse src/` 除定義外無其他命中 |
| 音訊真相來源 | `src/effects/EffectChain.h:103`（另 `:134` 的 maxBlock 判斷式也用它 = K-03） |
| UI 真相來源 | `src/PluginProcessor.h:76` `hasReverbIR()` |
| algorithmic 額外乘 0.15 | `src/effects/SimpleReverb.h:155-156`（左右聲道各一次） |
| IR 上限 30 秒 | `src/PluginProcessor.cpp:819` 錯誤字串 |
| user preset 目錄 | `src/PresetManager.h:388-395` `userApplicationDataDirectory / "TsukiSynth" / "Presets"` |

**新發現一：repo 裡沒有任何工廠 IR。**
`find`（排除 `build*/`、`libs/`）找到的 `.wav` 全部在 `exports/` 與測試輸出下，
`data/` 只有 `fonts/` 與 `materials.json`。
→ **P3 卡 §2.1「目前沒有工廠 IR」的假設，本輪確認為真**；`IRRef.kind = factory` 這條路現在沒有內容可測。

**新發現二（§6.6 那句「雜湊不是新相依」需要補一個但書）。**
`juce::SHA256` 目前**只有 CLI 這個 target 用得到**，而且用的是一個特例寫法：
`src/cli/RenderApp.cpp:15` 直接 `#include <juce_cryptography/hashing/juce_SHA256.cpp>`，
原始碼註解自己寫明理由——`juce_cryptography` 模組「is NOT in this target's link list」。
`CMakeLists.txt` 裡 **`TsukiSynth`（plugin）、`TsukiSynthHostProbe` 等 target 全都沒有連 `juce::juce_cryptography`**。
→ 所以 **B＋ 要在 plugin 端算雜湊，必須二選一**：
（a）plugin 端照抄 `RenderApp.cpp` 的窄化 include 寫法（**不動 CMakeLists**），或
（b）在 `CMakeLists.txt` 的 `TsukiSynth` 與 `TsukiSynthHostProbe` 加 `juce::juce_cryptography`（**要動建置檔**）。
模組本身確實已經在 `libs/JUCE/modules/juce_cryptography/hashing/juce_SHA256.{h,cpp}`，**不用下載新東西**——
§6.6 說「不是新相依」在這個意義上成立，但**不等於「不用改任何建置設定」**。
（P3 卡 §5 GATE 4 目前只允許「CMakeLists.txt 僅為加新 header」改動，這一點需要月月或規劃者確認要走 a 還是 b。）

---

## 7. 依外部證據的建議（2026-09-07）

### 7.1 A／B／C 選哪個 → **維持 B，但加一層「工廠／使用者」分流**

**§5 原本建議 B，外部證據支持這個結論，而且把它變得更明確。**

三件事讓 B 站得住：

1. **老牌四家（REVerence／IR-1／Reverberate／Altiverb）全部不是內嵌**，
   他們把 IR 放在「外掛知道的地方」，preset 只記身分。這就是 B 的骨架。
2. **但「東西一搬就斷」在這四家身上留下了痕跡**：
   REVerence 有從 2015 抱怨到今天的公開紀錄（C1–C5）；
   Waves 那邊由**官方手冊自己**寫明缺檔要跳「Please locate」對話框、指到別的檔要在畫面標示（§6.2，【官方】），
   而且散布層面真的出過「安裝檔附了 preset、IR 卻沒隨附」的事（C7）；
   （**2026-09-07 複核修正**：原文在這裡寫「Waves 那邊有 preset 指向沒安裝的 IR、結果只換了名字沒有聲音的實例（C6–C7）」，
   這是把 C6 與 C7 兩件不同的事併成一句，來源裡沒有這個說法，已刪除。C6 的正確位置在 §7.2 第二條紅線。）
   LiquidSonics 則是被逼到要寫一整節「Lost Files Management」＋三層自動找回機制（6.2）。
   （Altiverb 我沒查到對應的抱怨或缺檔說明，**不列入這一點**。）
   差別在於他們斷得「大聲」（跳對話框），本專案斷得「安靜」（換一個聲音）。
   所以 B 一定要配 §4 的「明講」，不是選配。
3. **新一代（Aava 2026、Vital、Serum）轉向內嵌，理由字面上就是本案的失效**
   （HISE 於 2026-09-08 第二輪複核從這一組移除，理由見 6.1／6.2）：
   「to avoid the problem of moving the IRs and invalidating old DAW projects」。
   這證明 A 的方向不是過度設計，但 Vital 的 1 MB／preset 與 Serum 的
   「to keep file sizes down」也證明**全內嵌會付出真實代價**。

**因此建議把 B 做成 Serum 那種分層**（這是 §5 沒有寫、由外部證據補上的部分）：

| IR 種類 | preset 存什麼 | 白話解釋 | 理由 |
|---|---|---|---|
| 未來若有工廠隨附 IR | 只存 **id** | **id = 編號**。preset 裡只寫「第 7 號大教堂」，音檔本來就跟著程式一起裝在每台電腦上，不必再抄一份 | Serum：工廠內容大家都有，內嵌只是浪費 |
| 使用者自己載入的 IR | 複製進 `%APPDATA%/TsukiSynth/IR/<內容雜湊>.wav`，preset 存 **雜湊＋原始檔名** | **雜湊 = 依內容算出來的指紋**。程式把月月選的音檔**自己抄一份收進固定資料夾**，用指紋當檔名；preset 記指紋＋原檔名。這樣月月之後把原檔搬走、改名、刪掉都不影響，而且同一個音檔載入兩次不會存兩份 | §3-B 原案；雜湊天然去重，且解掉 REVerence「同名不同檔」的坑（LiquidSonics 要靠「上一層資料夾也要吻合」才勉強繞過） |
| 要寄給朋友時 | 另做「匯出成含 IR 的包」，此時才走 A 的內嵌 | 平常的 preset 很小；只有月月**主動按「匯出給別人」**時，才把音檔一起打包進去 | §5 原案；把授權責任限縮在「使用者明確選擇分享」的那一刻 |

**一句話**：B 是業界主流的收斂形式，A 是新一代的方向，
**先把 B 做對，再把 A 當成匯出功能**——這樣兩邊的好處都拿到，兩邊的代價都不用付。

### 7.2 IR 不見時怎麼辦 → **維持「強制切回 algorithmic ＋ 顯眼警告」，但照 Waves IR-1 拆成三種情況**

§4 建議的第二項（保持出聲＋警告）與外部證據一致，而且 Waves IR-1 官方手冊
把「明講」拆得比 §4 更細，值得直接照抄行為（不是抄程式，是抄「該說什麼話」）：

| 情況 | Waves IR-1 官方怎麼做 | 建議 TsukiSynth 怎麼做 |
|---|---|---|
| 找得到（雜湊吻合） | 正常載入 | 正常載入 |
| 找不到，使用者指了別的檔 | 載入該檔，並在畫面標示「Different IR loaded to preset」 | 同樣載入，並在 IR 名稱旁明示「與 preset 存的不是同一個 IR」 |
| 找不到，使用者取消／不在 GUI 前 | 不載入，顯示「IR was not loaded」 | **不可靜音**（DAW 播放中）→ 模式強制切回 algorithmic，IR 欄位顯示「未載入」，並跳一次警告 |

**兩條紅線（外部證據支持，不是我的偏好）：**

1. **絕對不可以沿用 instance 裡上一個 IR。** 查證的 9 個對象裡沒有任何一個這樣做。
   這是 §1 那張表第二列的行為，也是 F-03 最難被使用者察覺的一種。
2. **UI 顯示「IR」而音訊在跑 algorithmic，這種狀態不可以存在。**
   IR-1 用一句畫面文字保證這件事；本專案目前有兩個各說各話的變數（6.6 複驗仍成立）。
   **社群佐證是 C6**：whyterabbyt 匯入 wav 之後「選單名稱換了、但沒有波形也沒有聲音」，
   整串貼文才把原因挖出來——畫面說一套、聲音是另一套，使用者就是查不出來。

**另外**：退回 algorithmic 時 §1.3 的 `0.15` 音量差會一起發生。
Waves 手冊裡有一個相關但**不同用途**的機制：匯入 IR 時，
**只有在峰值高於 −12 dB 時**才把峰值正規化到 −12 dB，
理由是「to allow some headroom for the expected peak growth and clipping that will occur when convolving a hot signal with a hot IR」
（*IR-1 software guide* p.34；本機 PDF sha256 前 16 碼 `eeed8bb0575749ef`，PyMuPDF 解字）。
**那是為了留 headroom 防削波，不是為了對齊響度**
（2026-09-07 複核修正：原文寫「來對齊響度」是改寫，來源沒有這麼說；
同段手冊另外把「讓全濕與全乾聽起來一樣大聲」交給使用者手動調 Direct/ER/Tail gains，而非自動正規化）。
本專案連這個防削波機制都沒有等價物，所以**退回時的音量跳動要嘛量化補償（K-02），要嘛在警告裡講明「音量也會變」**。
在 K-02 量化完成前，**建議先講明**，不要憑感覺補一個係數（R4：不新增未溯源常數）。

### 7.3 如果月月不同意，換選項的代價（各一句）

- **改選 A（全內嵌）**：preset 從幾 KB 變成約 1 MB 一顆（Vital 使用者實測的平均值，非本專案量測），
  而且每分享一次 preset 就等於散布一次第三方 IR 的音訊——**代價是體積＋法律責任**。
- **改選 C（只存路徑）**：工程最省，但外部證據顯示這正是 REVerence 從 Cubase 7 被抱怨到今天的那條路，
  **代價是十年份的已知使用者痛點原封不動搬進來**（只是從安靜壞掉變成大聲壞掉）。
- **缺檔行為改成「靜默退回」**：等於不修 F-03。
- **缺檔行為改成「拒絕載入／靜音」**：查證的 9 個對象裡只有 IR-1 接近（「IR was not loaded」），
  但它是在 GUI 前發生、使用者按了取消才靜；DAW 自動載入時靜音＝§4 已判定「比走音更糟」，
  **代價是把一個聽得出來的錯換成一個聽不出來的無聲**。

### 7.4 這一節沒有回答的事

- **本文沒有量測任何聲音。** 退回 algorithmic 到底差幾 dB（K-02）仍未量化，
  6.5 只證明「規範沒擋住內嵌」，沒有證明「內嵌對音質更好」——這兩件事無關。
- **沒有 Reddit 證據**（見 6.7）。C1–C8 全部來自 Steinberg 官方論壇與 KVR，
  樣本偏向 Cubase／KVR 族群，可能低估其他 DAW 使用者的期待。
- **Kontakt／REAPER ReaVerb／u-he 三家未取得官方說明**，
  所以 6.1 那句話的母體是**已查證的 9 個對象**，不是全業界；其中真正有官方缺檔說明的只有 3 個。

---

### 7.5 第三輪補查對建議的影響（2026-09-08）：**建議不變，而且多了一句可以直接抄的措辭**

§6.8 補進來的兩家（ReaVerb、u-he Hive）**沒有推翻 §7.1–§7.4 的任何一個字**，
但它們改變了三件事的「把握程度」，值得月月知道：

1. **B＋ 的骨架更穩。** 老牌「不內嵌」的陣營從 4 家變成 **6 家**
   （REVerence／IR-1／Reverberate／Altiverb ＋ ReaVerb ＋ Hive）。
   到目前為止**查不到任何一個成熟產品把大型音訊資料當成 preset 的預設儲存格式**——
   做內嵌的三家（Aava／Vital／Serum 使用者 wavetable）全部是新一代、而且都付出了體積代價（§6.3）。
   §7.1「先把 B 做對、把 A 當匯出功能」的分工，證據基礎比前兩輪更厚。

2. **缺檔要「明講」這件事，現在有第四個官方例子，而且它的話最好抄。**
   Hive 那句把兩件事塞進一行：**哪個檔不見了**（把檔名唸出來）＋**為什麼**（preset 裡存的路徑失效了）。
   §7.2 三態表第三態（找不到、又沒有 GUI 可以問）要顯示什麼字，建議照這個結構寫，例如：
   > 「未載入：`<原始檔名>`——這個 preset 記的 IR 在這台電腦上找不到。已切回 algorithmic reverb，**音量會和 IR 模式不同**。」
   （後半句是本專案自己的要求，來自 §1.3 的 0.15 增益差；**Hive 沒有這一句，不要說成是抄來的**。）

3. **C 方案的代價，這次是廠商自己寫下來的。**
   §7.3 原本說「改選 C＝把 REVerence 十年份的使用者抱怨原封搬進來」，靠的是社群證據（C1–C5）。
   Hive 手冊那句「Be careful not to move, rename or delete wavetables」是**官方自己承認**
   C 方案把維護責任丟給使用者。**選 B＋ 就是不把這個責任丟給月月的使用者**——
   程式自己抄一份進庫，使用者之後怎麼整理硬碟都不會壞。

**這一節同樣沒有回答的事（與 §7.4 相同，未因第三輪改變）：**

- **仍然沒有任何 Reddit 證據**（§6.8 記錄了第三輪的重試與失敗方式）。
  月月 2026-09-07 明示可以用 Reddit，但本機環境三輪都打不開，只能以官方手冊與 KVR／Steinberg 論壇替代。
- **Kontakt 仍未取得官方說明**（三輪皆 404／403）。
- **本文從頭到尾沒有量測任何聲音**；K-02（退回 algorithmic 的音量差）仍未量化，
  §7.2 的「講明音量會變」仍然是**因為量不出數字才這樣做**，不是因為它比較好。

---

### 7.6 第四輪補查對建議的影響（2026-09-08）：**建議一個字都不用改，但它從「我們的推論」變成「別人已經這樣做」**

**先講結論：§8 裁決欄裡 2026-09-08 已經記下的「問題一＝B＋、問題二＝三態」，本輪沒有任何理由推翻。**
月月如果已經看過那個裁決，**這一節不需要重新決定任何事**，只是讓你知道那個決定現在站得更穩。

本輪（§6.10）改變的是四件事的把握程度：

1. **「平常用 B、要送人時才用 A」不再是我們自己想的——Kontakt 的官方手冊就是這樣寫的。**
   §7.1 那張分層表的三列，在 Kontakt 的存檔對話框裡是三個並列的選項
   （Patch Only ＝ C、Patch + Samples ＝ B、Monolith ＝ A），
   而且 NI 官方手冊自己說 Monolith 是「a good way to create Instruments that should be distributed to other users」。
   **一模一樣的分工，一模一樣的理由。** 前三輪這一條只有 Serum 的「to keep file sizes down」當旁證，現在有正面例子。

2. **「工廠 IR 只記編號」這一列，現在有月月自己的 DAW 背書。**
   Cubase Pro 15.0 官方手冊：「The factory content is not a problem because it is also present」（後接 on the other computer，引述依≤15 字規定截至此）。
   Steinberg 自己就把工廠內容和使用者 IR 分兩種處理。

3. **「用內容雜湊當檔名」不是工程師的潔癖，是繞開一個官方承認的坑。**
   Kontakt 手冊承認只比對檔名會「load the wrong Sample」，所以它得多做一個 Check for Duplicates 開關；
   LiquidSonics 得靠「上一層資料夾名也要吻合」勉強擋。
   **B＋ 用內容雜湊，這兩個坑天生就不存在**——同名不同檔算兩個不同的 IR，同檔改了名還是同一個 IR。

4. **A 的授權風險，從「我們的判斷」升級成「三份廠商合約白紙黑字」。**
   §3-A 那個 ❌ 前三輪沒有來源，本輪有了（Audio Ease／Eminence／Celestion，§6.10.3）。
   **這讓「不要把內嵌當預設儲存格式」這個選擇更容易向月月交代**：
   如果 TsukiSynth 預設就把 IR 音訊塞進每個 preset，使用者只要把 preset 貼上網，
   就可能同時踩到「distribute」「otherwise make available」「electronically transmit」這幾個字。
   **B＋ 把這件事推遲到使用者主動按「匯出給別人」的那一刻**，而且那時候可以在畫面上提醒他自己確認授權。
   （**再說一次：我不是律師，這不是法律意見**，見 §6.10.3 的兩點但書。）

**這一節建議在 P3 落地時多做的兩件小事（都不改結論，只是把話說得更好）：**

- **缺檔警告的措辭，再抄 Kontakt 一個結構**：Kontakt 的 Content Missing 對話框除了說「哪個檔不見了」，
  還會在右邊欄位顯示「assumed at」——也就是**它本來以為檔案在哪**。
  §7.5 已經建議照 u-he Hive 的結構（唸出檔名＋說明原因），
  再加上「preset 記的原始檔名」這一項，使用者就能自己認出是哪次整理硬碟搬掉的。
  建議措辭（在 §7.5 那句之上補一個括號）：
  > 「未載入：`<原始檔名>`——這個 preset 記的 IR 在這台電腦上找不到。已切回 algorithmic reverb，**音量會和 IR 模式不同**。」
  （音量那半句仍然是本專案自己的要求，來自 §1.3 的 0.15 增益差，**不是抄來的**；K-02 量化完成前不補係數。）

- **「不要每次都問」這件事，B＋ 已經天然解決，值得在 UI 上讓使用者看見。**
  C1–C5 與 C9–C11 十年份的抱怨核心是「每開一次專案就要重指一次路」
  （REVerence 官方甚至要求「you need to save your programs or presets under a different name」才會記住）。
  B＋ 因為程式自己抄了一份進庫，**第一次載入之後永遠不會再問第二次**。
  這是相對於 REVerence／ReaVerb／Hive 的實質優勢，不是同級品。

**這一節同樣沒有回答的事（與 §7.4／§7.5 相同）：**

- **本文從頭到尾沒有量測任何聲音。** K-02（退回 algorithmic 的音量差）仍未量化。
- **仍然沒有任何 Reddit 證據**（第四輪三條路徑全被 403／unable to fetch 擋掉，§6.10.5）。
  社群樣本仍偏 Cubase／KVR 族群。
- **本文沒有法律意見**（§6.10.3）。三份 EULA 只證明市售 IR 普遍禁止散布，不證明任何做法合法或違法。
- **母體是 12 個對象**，不是全業界。

---

## 8. 裁決欄

**問題一：preset 要怎麼記住 IR？**（勾一個）

- [ ] **A**　把 IR 音訊整個內嵌進 preset（每顆 preset 約 1 MB；分享 preset＝連音檔一起送出）
- [ ] **B**　受管理 IR 庫：程式自己收一份音檔，preset 只記身分（§5 原案）
- [ ] **B＋**　**受管理 IR 庫＋工廠／使用者分流**（§7.1 建議：工廠 IR 只記編號、使用者 IR 抄一份進庫、要送人時才另外打包）
- [ ] **C**　只存檔案路徑（最省工，但等於把 REVerence 十年份的抱怨原封搬進來）

**問題二：IR 檔不見了要怎麼辦？**（勾一個）

- [ ] 靜默退回 algorithmic（＝維持現狀，等於不修 F-03）
- [ ] **強制切回 algorithmic ＋ 顯眼警告**（§4／§7.2 建議）
- [ ] 強制切回＋警告，**並照 Waves IR-1 拆成三態**：找到／指了別的檔就在畫面明示「不是同一個 IR」／取消就顯示「未載入」（§7.2 建議的完整版）
- [ ] 拒絕載入（可能靜音）

> 月月選擇：問題一＿＿＿＿＿　問題二＿＿＿＿＿
>
> 裁決日期：＿＿＿＿＿

### 裁決記錄（2026-09-08，規劃者依月月 2026-09-07 委託代決，月月可推翻）

月月 2026-09-07 原話：「A13 A14 F-03 看看能不能查到外部資料（包含 Reddit 討論版）決定」。
Reddit 在本機環境無法存取（§7.4），證據以官方手冊（REVerence／Waves IR-1／LiquidSonics）＋ Steinberg 論壇／KVR 八條替代。

- **問題一：B＋**（受管理 IR 庫＋工廠／使用者分流；「匯出給別人」才走內嵌）。
  依據：§6.1 查證 9 個對象零個做靜默頂替；老牌四家皆非內嵌；新一代內嵌的動機字面上就是本案的失效。
- **問題二：強制切回 algorithmic ＋ 警告，照 Waves IR-1 拆三態**。兩條紅線照 §7.2：不得沿用 instance 上一個 IR；UI 顯示 IR 而音訊走 algorithmic 的狀態不得存在。
- 退回時的音量跳動：K-02 量化（WF0907-E7）完成前，警告文字**講明音量會變**，不補係數（R4）。
- 落地：WF0908-P3 施工卡（`docs/workcards/WF0908_P3_f03_ir_library.md`）。

### 落地記錄（2026-09-09，WF0908-P3 施工完成）

- **問題一（B＋）**：`src/IRLibrary.h`（新）——內容雜湊（自帶 SHA-256，未新增
  CMakeLists 模組相依）定址的受管理 IR 庫，`%APPDATA%/TsukiSynth/IR/<sha256 前
  32 碼>.wav` ＋同名 `.json` metadata；`IRRef.kind` 預留 `user`/`factory`，
  factory 內容本卡未實作（確認 `data/`／BinaryData 沒有任何工廠 IR 資產）。
  `importFile()` 去重（內容相同即沿用既有庫檔）。
- **問題二（三態＋兩條紅線）**：`TsukiSynthProcessor::restoreReverbIR()`／
  `tryLoadIRRef()`（`src/PluginProcessor.{h,cpp}`）——吻合就靜默載入；resolve
  到但內容雜湊對不上就照樣載入並標記 `mismatch`（不靜默頂替）；resolve 不到
  （無 GUI）就強制切回 Algorithmic ＋清空 `effectChain` 的 IR ＋一次性警告
  （警告文字比照 §7.2/§7.6 建議措辭：報原始檔名 ＋ 講明「音量會和 IR 模式
  不同」，K-02 未量化前不補係數，R4）。兩條紅線：`restoreReverbIR()` 每次都
  先 `effectChain.clearImpulseResponse()` 才決定要不要載入（紅線一）；
  `IRStatus::loaded` 直接等於 `effectChain.hasImpulseResponse()`，同一個欄位
  不是兩個會漂移的變數（紅線二，§1 第二列同步標記已修）。
- **單一真相 / preset 序列化**：`PresetManager`（`src/PresetManager.h`）新增
  `getExtraStateBlock`/`applyExtraStateBlock` 回呼，讓 preset／DAW state 序列化
  變成「APVTS state ＋ 可選附加 ValueTree」，`PresetManager` 本身仍不知道
  「reverb_ir」是什麼（IR-agnostic，供之後其他附加區塊重用）。
  `PluginEditor.{h,cpp}` 把原本 .wav/.json 共用的 Load 鈕拆成兩顆
  （IR / Profile），面板標題改讀 `getIRStatus()` 顯示 mismatch/missing。
- **驗收**：`tests/host_probe.cpp` H7 三情境（吻合／缺檔無 GUI／庫被改寫模擬
  「指了別的檔」）全部由 `KNOWN-FAIL(F-03)` 改成硬 CHECK，
  `getStateInformation()` 讀回的 `reverb_ir`/`ir_missing`/`ir_mismatch` 與三態
  一致；67/67 PASS。8/8 位元不變、`--full` NO CHECKED FAILURES、ctest 4/4、
  pytest 260 passed/1 skipped。證據：`reports/gate_outputs/wf0908_P3_f03.txt`。

---

## 附錄：本輪未涵蓋的相鄰問題

以下在稽核裡與 IR 相關，但**不屬於這張決策單**，各自需要獨立處理：

- **K-02**：algorithmic 與 IR 的 wet 增益標度不一致（§1.3）。需要先建 IR loudness
  corpus 量化，才能決定要不要補償。
- **K-03**：單一 audio block 超過 prepare 的 maxBlock 時，會靜默改走 algorithmic
  （`src/effects/EffectChain.h:134` 的 `numSamples <= maxBlock`）。
  這是為了避免 audio thread 配置記憶體，但代表音色會依 host block size 改變。
- **新稽核 P1/P2**：`getTailLengthSeconds()` 只計 IR 長度與固定值，
  忽略物理模態尾音——Tongue Drum 實測 T60 可達 30.18 秒，但回報 2–3.45 秒，
  DAW bounce/freeze 可能截尾。**這條和 IR 無關，但同樣是商品級缺陷**，
  建議另開一張單。

---

## 複核修正記錄（2026-09-07）

另一位 Opus 做引用複核（親自打開每個來源核對），提出 8 條 findings。以下逐條列出怎麼改。
**本輪修正只動 §6、§7、§8 與本節；§1–§5 仍然一字未改。**

| # | 等級 | 位置 | 複核指出的問題 | 這次怎麼改 |
|---|---|---|---|---|
| 1 | **blocker** | §6.4 C6 列、§6.4 結論句、§7.1 第 2 點 | 「preset 指向沒安裝的 IR → 只換了名字、沒有聲音（C6–C7）」在來源裡不存在。C6 的原句主詞是 `loading wav files`（使用者自己匯入 wav 失敗），C7 是「安裝檔附了 preset 卻沒附 IR」的散布問題，兩件事被併成一句 | **刪除該合併主張**。C6 列改寫成原文條件（匯入自己的 wav）並補上完整引述；新增一段方框明說「C6／C7 是兩件不同的事」並補上 lfm 的真正成因（`.xps` preset 檔為必要）；§6.4 結論改成「使用者介意的是①每次都要問②拿到的東西指向不存在的內容」；C6 改掛到 §7.2 第二條紅線（畫面與音訊不一致）當社群佐證。§7.1 第 2 點的 Waves 子項改成**只講官方手冊寫明的缺檔行為＋C7**，並在原地標註原句已刪除 |
| 2 | minor | §6.4 C8 | 日期 2026-05-26 錯誤 | 改為 **2026-05-19**。我自己重抓該頁逐則時間戳確認：ilmai 的「Aava actually stores IRs with the preset」為 Tue May 19, 2026 5:20 pm，Velden 的「100% a very good move」為 Tue May 19, 2026 5:32 pm；5/26 是同串更後面的貼文 |
| 3 | minor | §6.7 來源 #7 | 「引述日期 2016-12-16 與 2020-05-15」錯誤 | 改為**兩句都出自 steve_xfer 2020-05-15 的同一則貼文**，並註明 2016-12-16 那則講的是 NMSV／FXP，與本卡無關。我用 `curl` 抓原始 HTML 剝標籤後逐則核對：`December 16, 2016` 那則內容是「NMSV = Native Instruments Massive / FXP = "VST" preset.」，而「it will not embed in to user presets to keep file sizes down」出現在 `May 15, 2020` 那則的 wavetable `clm ` chunk 說明裡（同一則也含「isn't public」） |
| 4 | minor | §6.3 Vital 列 | 「連 init patch 都內嵌四份沒在用的資料」把數字條件改寫了 | 改為原文條件：**內嵌四份、其中三份是關掉沒在用的**，並附上原句「even though three of those four things are turned off and not used in the patch」與作者／日期（ahanysz, 2020-12-12） |
| 5 | minor | §7.2 | 「Waves 把匯入的 IR 正規化到 −12 dB 峰值**來對齊響度**」用途被改寫，且省略觸發條件 | 改為**只有峰值高於 −12 dB 時才正規化**，且手冊給的理由是**留 headroom 防削波**（附原句 "to allow some headroom for the expected peak growth and clipping…"），並補記手冊把「全濕與全乾一樣大聲」交給使用者手動調 gain。我在本機重解 PDF 核對（`output/wf0907/R3/Waves_IR-1_software_guide.pdf`，sha256 前 16 碼 `eeed8bb0575749ef`，37 頁，p.34） |
| 6 | minor | §6.5 第三列 | JUCE `size_t`／`int` 的型別事實被掛在 JUCE 論壇名下，但該串沒討論這件事 | **出處改掛本機 JUCE 原始碼**（`libs/JUCE/modules/juce_audio_processors_headless/processors/juce_AudioProcessor.h:1140` 與 `:1176`，我自己 grep 核對），分級改標【原始碼】並註明「非外部證據」；來源 #14（JUCE 論壇）加註它**只支撐**「it doesn't happen on the audio thread」那一句。順帶把 `getStateInformation` 的描述由「用 size_t」修正為「收 `MemoryBlock&`（其大小型別為 size_t）」 |
| 7 | minor | §8 裁決欄 | 選項與 §7.1 的實際建議對不上，月月沒得勾「B＋工廠／使用者分流」；且 §7.1 分層表術語太硬 | §8 改成**可勾選的清單**，問題一加入 **B＋（受管理庫＋工廠／使用者分流）**，問題二加入「照 IR-1 拆三態」的完整版；§7.1 分層表**新增一欄「白話解釋」**，把 id／雜湊／匯出包三個詞用月月看得懂的話講一遍 |
| 8 | minor | §6.6 | 行號在今天的工作樹上對不上（C++ lane 平行改檔造成 ~+30 行位移） | §6.6 開頭**新增行號基準方框**：明說 `PluginProcessor.cpp` 與 `PluginEditor.cpp` 的行號是 **HEAD `98f346f`** 的行號、工作樹有未 staged 改動（+32/−1 與 +12/−4）、下一輪工程卡**不可照抄行號**要用關鍵字重新定位；並註明其餘各檔（PresetManager.h／EffectChain.h／SimpleReverb.h／PluginProcessor.h／RenderApp.cpp）我已在工作樹上逐條重看，行號一致 |

**本輪沒有新增任何來源。** 所有修正都是把既有來源的主張改回原文所說的範圍，
或把出處改掛到正確的地方；沒有為了補洞去找一個新的引用。

**仍然存在的缺口（與上一輪相同，未因本輪修正而改變）**：
本文**沒有任何 Reddit 證據**（`www.reddit.com` 與 `old.reddit.com` 在本環境皆無法存取），
Gearspace／VI-Control 回 403、Kontakt 官方手冊候選 URL 回 404，全部標「未取得原文」未採用；
REAPER ReaVerb 與 u-he 未查到可引用的官方說明。詳見 §6.7 末段。

---

## 第二輪引用複核記錄（2026-09-08）

第三位 Opus **重新親自打開每一個來源**核對（不看上一輪的摘要，重抓原文）。
所抓 PDF 的 SHA256 與逐句命中結果如下；**14 個來源全部核對完畢**。

| 來源 | 我這次怎麼核 | 結果 |
|---|---|---|
| Waves *IR-1 software guide* | 本機 PDF（sha256 `eeed8bb0…`，37 頁）PyMuPDF 全文檢索 | 引用的 7 句**全部逐字命中**（含 "IR properties and a pointer to the IR file"、"IR was not loaded"、"Different IR loaded to preset"、"to allow some headroom for the expected peak growth"） |
| LiquidSonics *Reverberate 2 User Guide* | 本機 PDF（sha256 `7bf3dd0e…`，29 頁） | 4 句全部命中（含 "Favourite locations are searched"、"A file's folder must match"） |
| MeldaProduction *MConvolutionEZ* | 本機 PDF（sha256 `120f2dcc…`，39 頁） | 2 句命中 |
| Audio Ease *Altiverb 8* | 本機 PDF（sha256 `63da2ff0…`，12 頁） | 2 句命中 |
| Steinberg REVerence "Relocating Content" | WebFetch 重抓整頁 | 4 句全部命中 |
| Steinberg VST3 *Preset Format* | WebFetch 重抓 | chunk offset/size 皆 **int64** 確認；**全頁無任何最大值**，§6.5 的「沒有載明上限」成立 |
| Xfer 官方論壇 *File Types???* | WebFetch 逐則列出作者與日期 | 「it will not embed in to user presets…」確為 **steve_xfer 2020-05-15**；2016-12-16 那則確實在講 NMSV／FXP。上一輪的修正正確 |
| KVR *Aava* 討論串 | `curl` 抓原始 HTML，逐則剝標籤讀時間戳 | ilmai **Tue May 19, 2026 5:20 pm**、Velden **5:32 pm**。（WebFetch 摘要一度回報 5/26，**原始 HTML 顯示為 5/19**，以原始 HTML 為準——上一輪的 2026-05-19 正確） |
| KVR *Vital* 討論串 | `curl` ＋ 逐貼文解析作者／日期 | 「The wt and noise sample are embedded」= **Whywhy, 2020-12-11**；「three of those four things are turned off」= **ahanysz, 2020-12-12**。兩條掛名與日期皆正確 |
| KVR *Waves IR-L* 討論串 | `curl` ＋ 逐貼文解析 | C6 whyterabbyt 2012-12-28、C7 Gamma-UT **2012-12-28 8:20 pm**、lfm **2012-12-30**（原句：「did not have any xps preset file - and it seems this was mandatory to show up」）三條皆屬實，且 C6／C7 確實是兩件事 |
| Steinberg 論壇 *Importing Impulses…* | WebFetch 逐則 | C1 mart 2015-07-20、C2 MickGael 2015-07-20、C3 nkf 2015-07-21 皆命中 |
| Steinberg 論壇 *Load 200 IRs…* | WebFetch 逐則 | C4 GuitboxGeek 2019-06-20「jumping off a cliff」、C5 ResonantMind 2019-03-12「extremely tedious and slow」＋3000 顆皆命中 |
| HISE 論壇 | WebFetch | 「set it to `saveInPreset` enabled」命中，**但原文只說「會被還原」，沒說「內嵌」**→ 觸發本輪唯一一條修正（見下） |
| JUCE 論壇 #64129 | WebFetch | 「it doesn't happen on the audio thread」命中；該串**確實沒有**討論任何大小上限，§6.5 把型別事實改掛本機原始碼是正確處置 |

**本輪唯一修正（1 條，minor）**：§6.1／§6.2／§6.2 引述清單／§7.1 第 3 點的 **HISE 一列**。
上一版把 HISE 歸進「A（內嵌）可用現成機制」與「新一代轉向內嵌」那一組，
但 David Healey 原句只保證「載入 preset 時會自動還原」，**沒有一個字說音訊資料存在 preset 檔裡**。
已降級為「機制存在、歸類未定」，並把 §6.1 的「4 個把資源直接收進 preset」改為 **3 個 ＋ 1 個框架另計**
（9 個對象的總數不變：3 官方缺檔說明 ＋ 2 未載明 ＋ 3 內嵌 ＋ 1 框架）。
§7.1 的三點論證**不因此改變**：Aava／Vital／Serum 三家已足以支撐「新一代轉向內嵌」。

**本輪同時重驗了 §6.6 的 repo 主張**（我自己在工作樹上 grep）：
`PresetManager.h:136`／`:380`、`EffectChain.h:98-101` 與 `:103-106`、`SimpleReverb.h:155` 的 `0.15f`、
`PluginProcessor.h:76` 的 `hasReverbIR()` 全部一致；
`PluginProcessor.cpp` 的「silently degrades」註解今天在 **`:767`**（HEAD 為 `:739-747` 區塊），
`reverb_ir_path` 寫入今天在 **`:730`**——**§6.6 的行號位移警告仍然有效，而且位移量還在變**，
下一輪工程卡務必用關鍵字定位。
`libs/JUCE/modules/juce_audio_processors_headless/processors/juce_AudioProcessor.h:1140`／`:1176`
的 `MemoryBlock&` 與 `int sizeInBytes` 兩行逐字確認無誤。

**沒有新增任何來源，沒有新增任何數字。** 本輪沒有動 §1–§5、§8 裁決欄與裁決記錄。

---

## 第四輪補查記錄（2026-09-08，第五位 Opus）

本輪**不是**引用複核輪，是**補查輪**：只針對前三輪自己記下的「未取得原文」名單再打一次，
並替 §3-A 那個沒有來源的授權主張找合約條文。

**動到的章節**：新增 §6.10、§6.11、§7.6 與本節。
**沒有動到的章節**：§1–§5、§6.1–§6.9、§7.1–§7.5、§8 裁決欄與裁決記錄、附錄、前兩輪的複核記錄——
**全部一字未改**（改前備份在 `output/wf0907/R3/F03_backup_before_round4_20260908_201802.md`，可 diff 驗證）。

| 前三輪記的缺口 | 第四輪結果 |
|---|---|
| Kontakt 官方說明（三輪 404） | ✅ **取得**。舊 URL 網域已 301 搬家到 `docs.native-instruments.com`，由新網域取得整頁（564 KB） |
| §3-A「內嵌有授權風險」沒有來源 | ✅ **取得三份廠商 EULA 原文**（Audio Ease／Eminence／Celestion） |
| REVerence 只有 Nuendo 10 存檔版 | ✅ **補上 Cubase Pro 15.0 現行手冊**，四句照樣在，另得「工廠內容不是問題」一句 |
| Reddit（三輪打不開） | ❌ **第四輪仍失敗**，3 條路徑全 403／unable to fetch（詳見 §6.10.5） |
| Gearspace（403） | ❌ **重試仍 403** |
| VI-Control（403） | — 本輪未重試 |
| JUCE state 大小實務上限 | — 本輪未再查，維持「查不到」 |

**本輪沒有推翻前三輪的任何一條主張。** §6.1 的核心結論（零個做靜默頂替）在母體從 11 擴到 12 之後仍然成立。
**本輪沒有為了補洞而編任何數字**；打不開的來源全部照原樣記為「未取得原文」。
