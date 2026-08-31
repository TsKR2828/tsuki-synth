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

## 6. 裁決欄

> 月月選擇：＿＿＿＿＿（A 內嵌／B 受管理 IR 庫／C 資源參考）
>
> IR 不見時：＿＿＿＿＿（靜默退回／強制切回＋警告／拒絕載入）
>
> 裁決日期：＿＿＿＿＿

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
