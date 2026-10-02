# Inno Setup 商業使用授權：要不要買？（WF1002b-R，N6＝B）

> 2026-10-02，WF1002b-R（唯讀研究）。只引用本卡自己抓過的官方原文；原始檔存在 `output/wf1002b/R/web/`（gitignored），sha256 與抓取紀錄見 `reports/gate_outputs/wf1002b_R_web_fetch_log.txt`。
> 本頁不是法律意見，只是把官方條文讀給你聽。

---

## 一句話結論

**不是「必須買」，是「官方請求」。** 法律上的授權條文（LICENSE.TXT）允許任何人免費做商業用途；另外官方「請求」年營收超過 **5,000 美元** 的商業使用者買授權，而且官方自己寫「並非嚴格要求」。

對你（個人在 BOOTH 賣東西）來說：

| 你的情況 | 官方怎麼說 | 白話 |
|---|---|---|
| 還沒正式出貨安裝檔 | 不用先買，等安裝檔真的要上線再買 | **現在不用買** |
| 開賣後，一年營收 ≤ 5,000 美元 | 不算官方定義的「商業使用者」 | **官方沒有請你買**（想贊助可以捐款或照樣買） |
| 開賣後，一年營收 > 5,000 美元 | 屬於「商業使用者」，官方請求購買 | **建議買 Single User（US$155，未稅）**；不買也不違反 LICENSE.TXT |
| 以後把 Inno Setup 放進 CI 自動編譯 | 官方期待「至少一張 Single User」 | 同上，只是請求 |

---

## 1. 法律授權條文（LICENSE.TXT）——允許商業用途、不收錢

來源：<https://jrsoftware.org/files/is/license.txt>（抓取 2026-10-02，HTTP 200，1521 B）

- 逐字：「Permission is granted to anyone to use this software for any purpose, including commercial applications」
- 條件只有 4 條（白話）：
  1. 散布原始碼要保留版權聲明與條件清單。
  2. 散布二進位檔要保留版權聲明和網址（例如「關於」視窗裡那些）。
  3. 不可謊稱是你寫的；在產品文件裡致謝「歡迎但不強制」。
  4. 改過的版本要標明是改過的。
- 條文裡**沒有任何收費、營收門檻或購買義務**。

Inno Setup 7 的「What's new」頁也說使用條件看同一份 LICENSE.TXT：「For conditions of distribution and use, see LICENSE.TXT」（<https://jrsoftware.org/files/is7-whatsnew.htm>）。
**注意**：我抓的是官網目前那份 LICENSE.TXT；本機 `E:\Tsuki-project\_tools\innosetup\innosetup-7.1.0-x64.exe` 沒安裝、沒拆開，所以**安裝包內附的 LICENSE.TXT 跟官網這份是否逐字相同，沒核對**（open item）。

## 2. 「商業授權」頁——是請求，不是義務

來源：<https://jrsoftware.org/isorder.php>（抓取 2026-10-02，HTTP 200）

**是不是必須買？**
- 問：「Are commercial users required to purchase a license?」
- 答（逐字）：「It is not strictly required.」後面接著說他們認為請所有商業使用者購買是公平的，「regardless of the version being used」（不管用哪個版本）。
- 頁首：「we request that all commercial users of Inno Setup purchase licenses, regardless of the version being used」

**誰算「商業使用者」？**（逐字列兩種）
- 「A for-profit organization with annual revenue exceeding USD 5000, or the equivalent in other currencies.」
- 「An individual/freelancer using Inno Setup as part of for-profit work with an annual revenue exceeding USD 5000」
- 補充：開源／免費軟體收到的捐款也算進營收門檻。
- 白話：你是「個人、拿它做營利的事」，所以看的是**年營收是否超過 5,000 美元**。條文沒寫清楚「營收」是只算 TsukiSynth 商品、還是你個人所有營利收入——**這點官方沒定義，查不到**。

**還沒出貨要不要先買？**
- 逐字：「No; the license may be purchased later, once your Inno Setup-built installers are actually ready to be used in production.」

**「使用」指什麼？**
- 執行 Inno Setup 的 IDE 或編譯器算「使用」。
- 在 CI 上沒人操作、但腳本在呼叫編譯器：「then purchase of a single-user license is expected at minimum」。
- 買家執行你的安裝檔**不算**「使用 Inno Setup」：「Deploying an Inno Setup-built installer (in other words, running a Setup program) does not count as using Inno Setup in this context.」
- 沒授權編出來的安裝檔**不會被標成未授權**：「installers built without a license are not explicitly marked as unlicensed」。

**非商業使用者？**
- 逐字：「We're not requesting that non-commercial users purchase licenses」；捐款歡迎。
- 捐款頁（<https://jrsoftware.org/isdonate.php>）：「Inno Setup is free for non-commercial use」，並說商業使用者請走購買頁、不要用捐款（購買有發票，捐款沒有）。

**買了會多什麼？**
- 不多功能：「Licenses do not include additional features.」
- 不多技術支援：支援仍是免費論壇那套。
- 純粹是支持開發＋有正式授權紀錄（官方說很多組織要審計用）。

## 3. 從哪個版本開始？

- **6.5.0（2025-08-12）** 首次推出商業授權。來源：<https://jrsoftware.org/files/is6-whatsnew.htm>，該版本標題下第一節逐字「Introducing commercial licenses」，內文「we kindly ask that you purchase a license」（是「請」，不是「必須」）。
- 但官方明說請求**不分版本**（「regardless of the version being used」），所以不是「用 6.4 以前就不用」。
- 下載頁（<https://jrsoftware.org/isdl.php>）說 Inno Setup 7 是靠商業授權收入做出來的，並請商業使用者購買或捐款。我們下載的是 **7.1.0**（下載頁日期 2026-08-12）。

## 4. 價格與授權對象

價格不在 HTML 裡，是頁面用 Paddle 即時算出來的。我在瀏覽器打開 <https://jrsoftware.org/isorder.php>，讀頁面自己的 Paddle 價格預覽（2026-10-02，地區被判定為 TW）：

| 方案 | 人數 | 未稅（USD） | 台灣稅額（USD） | 含稅（USD） |
|---|---|---|---|---|
| **Single User** | 1 人 | **$155.00** | $7.75 | $162.75 |
| Team | 2–5 人 | $410.00 | $20.50 | $430.50 |
| Enterprise | 不限 | $1,195.00 | $59.75 | $1,254.75 |

頁面以台幣顯示時：Single User **NT$4,931.02**（未稅）＋稅 NT$246.55＝**NT$5,177.57**。
（價格是 Paddle 依地區、當下匯率算的，結帳時可能有差；以結帳畫面為準。）

授權性質（逐字摘自購買頁）：
- 永久授權、一次付清：「All commercial licenses are perpetual and require a single payment.」含兩年大小版更新；過期後原版本照常可用。
- 兩年後要續更新：兩個月內續約打 6 折（「60% of the current price」）。
- 30 天退款：「We offer a 30-day money-back guarantee」。
- 一張 Single User 授權給一個人，那個人可以裝在自己是主要使用者的多台電腦上。
- 「Licensee Name」填你的名字或組織名，會顯示在程式裡。
- 經銷商是 Paddle.com（Merchant of Record），付款、退款、發票都由 Paddle 處理。

## 5. 個人小賣家用它包安裝檔賣商品，要不要買？

照第 2 節逐字條文推論：
- **授權條文（LICENSE.TXT）**：不用買，商業用途本來就允許。
- **官方請求**：只在你「年營收 > 5,000 美元」時才被列為商業使用者；而且「安裝檔真的要上線時」再買即可。
- **不買的後果**：條文上沒有罰則、安裝檔也不會被標記。這是誠信／支持開發的問題，不是授權違約。

AI 不替你決定。可能的做法（給你挑）：
- 甲：開賣前就買 Single User（US$155 未稅），一勞永逸、有發票。
- 乙：先不買，年營收接近 5,000 美元時再買（官方 FAQ 允許「之後再買」）。
- 丙：換免費工具（第 6 節），或只給 zip＋安裝說明（N6 原選項 C）。

## 6. 替代方案（只列授權性質＋原文出處）

### NSIS（Nullsoft Scriptable Install System）
- 來源：<https://raw.githubusercontent.com/kichik/nsis/master/COPYING>、<https://nsis.sourceforge.io/License>（皆 2026-10-02 抓，HTTP 200）
- 主體是 **zlib/libpng 授權**：「Permission is granted to anyone to use this software for any purpose, including commercial applications」。
- 壓縮模組另有授權：bzip2 模組用 bzip2 授權；**LZMA 模組用 Common Public License 1.0**（CPL）。
- 官方頁面**沒有**任何付費請求、營收門檻或維護費。
- 白話：完全免費、可商用；要遵守的只有「別說是你寫的」「改過要標明」這類條件。

### WiX Toolset
- 原始碼授權：**Microsoft Reciprocal License (MS-RL)**。來源：<https://raw.githubusercontent.com/wixtoolset/wix/main/LICENSE.TXT>。
- 但**官方編好的二進位版**另有一份「Open Source Maintenance Fee」EULA。來源：<https://raw.githubusercontent.com/wixtoolset/wix/main/OSMFEULA.txt>
  - 逐字：「The Fee applies only to Users that use the Software as part of revenue-generating activities and have an annual gross revenue greater than or equal to US$10,000.」
  - 年總營收 < 10,000 美元免付；自己從原始碼編譯不受這份 EULA 約束。
- 官方說明頁（<https://wixtoolset.org/osmf/>，頁面標題顯示 FireGiant Docs）：維護費「first introduced in WiX v6」、「the EULA acceptance enforcement was implemented in WiX v7」；營收超過 1 萬美元的組織要透過 GitHub 贊助 wixtoolset 組織來付。
- 費用金額：OSMF EULA 第 2 條只寫「follow the payment terms set forth by the Project」，**具體月費金額我沒查到**（沒點進 GitHub Sponsors 頁）。
- 白話：WiX 是做 .msi 的，學習曲線比 Inno Setup 陡；而且新版也開始收維護費，門檻 1 萬美元。

### 不用安裝程式
- N6 原本的選項 C：只給 zip＋安裝說明（把 .vst3 資料夾複製到 `C:\Program Files\Common Files\VST3\`）。沒有任何第三方授權問題，但對買家比較不友善。

---

## 7. 查不到／沒做的事

1. 安裝包 `innosetup-7.1.0-x64.exe` 內附的 LICENSE.TXT 沒拆開核對（沒安裝、沒執行）。
2. 「年營收 5,000 美元」是只算這個商品還是你個人全部營利收入：官方沒定義。
3. WiX 維護費的具體金額。
4. <https://jrsoftware.org/ishistory.php> 回 404（舊版本歷史頁不存在），版本資訊改用 is6／is7 的 What's new 頁。
5. 購買頁的條款（Terms of Service）全文沒抓。
