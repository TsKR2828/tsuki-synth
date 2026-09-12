# 信件草稿 2：向 University of Iowa MIS 確認泰國鑼錄音的器材與取樣率

> 狀態：**草稿，由月月自行寄出**（AI 不代發）。2026-09-10 依月月裁決「兩封信要寫」擬稿。
> 收件人：Lawrence Fritts（Musical Instrument Samples 建置者，網頁署名）。**信箱請自行從 https://theremin.music.uiowa.edu/MIS.html 或 University of Iowa School of Music 教職員頁確認**，本文件不臆測。
> 語言：英文。下方附中文對照。

## 這封信要達成什麼（白話）

我們從該網站抓了泰國鑼三包錄音（ff／mf／pp），拿它當水鑼引擎的「泛音比值」對照。網站有兩處講不清楚：
(1) 同一張器材表（2013-03-20、5 英尺、Earthworks QTC40、24-bit 44.1 kHz）同時掛在「2012 前」與「2012 後」兩頁，
我們下載的三包是掛在「2012 前」那頁，無法確定是不是同一場錄音；(2) 總說明頁說 2011 起都用 24/96 錄，
但鑼的器材表與實際檔案都是 44.1 kHz。這些不影響我們現在「只比頻率比值」的用法，但要把它寫成可引用的來源就得問清楚。
順便正式確認一下「without restrictions」是否涵蓋商業產品的開發驗證用途（雖然字面上已經很清楚）。

## 英文正文（可直接複製）

**Subject:** Question about the Thai gong recordings in the Musical Instrument Samples collection (equipment and sample rate)

Dear Professor Fritts,

Thank you for maintaining the University of Iowa Electronic Music Studios Musical Instrument Samples collection. I am an independent developer building a physical-modelling synthesizer and, being deaf, I verify the synthesizer's output numerically against real recordings rather than by listening. Your Thai gong recordings (thaigong.ff.zip, thaigong.mf.zip, thaigong.pp.zip, from the "Gongs & Tamtams" page) are the only pitched gong recordings I have found with documented microphone distance and equipment, and I am using them to compare partial-frequency ratios against my gong model.

To cite the recordings correctly I would be grateful for clarification on two points:

1. The equipment table (recorded March 20, 2013, anechoic chamber, 5 feet, Earthworks QTC40, Metric Halo 2882, 24-bit 44.1 kHz stereo) appears identically on both the pre-2012 and the post-2012 Gongs & Tamtams pages. The three Thai gong zip files I downloaded are linked from the pre-2012 page. Do those three files come from the 2013 session described in that table, or from an earlier session with different equipment?
2. The main MIS page states that recordings made from 2011 onward were captured at 24-bit/96 kHz, while the gong table and the files themselves are 44.1 kHz. Is 44.1 kHz the correct native rate for the Thai gong files?

Finally, the site states that the recordings "may be downloaded and used for any projects, without restrictions." I read this as covering use during the development and validation of a commercial software product (the recordings themselves would not be redistributed or included in the product). I would appreciate a brief confirmation that this reading is correct.

Thank you for your help, and for keeping this resource freely available for so many years.

Kind regards,

[Your name]

## 中文對照（給月月看，不寄）

主旨：關於 Musical Instrument Samples 泰國鑼錄音的器材與取樣率問題

Fritts 教授您好：

感謝您維護愛荷華大學電子音樂工作室的樂器樣本庫。我是獨立開發者，正在做物理建模合成器；因為我是聾人，合成器輸出是用數字對真實錄音驗證而非用聽的。貴站的泰國鑼錄音是我找到唯一有記錄麥克風距離與器材的有音高鑼錄音，我用它比對泛音頻率比值。

為了正確引用，想請教兩點：(1) 那張器材表（2013-03-20、消音室、5 英尺、Earthworks QTC40、Metric Halo 2882、24-bit 44.1 kHz）同時出現在 2012 前與 2012 後兩頁，我下載的三個 zip 掛在 2012 前那頁，它們是那場 2013 錄音嗎，還是更早、不同器材的錄音？(2) 總頁說 2011 起用 24/96 錄，但鑼的表與檔案都是 44.1 kHz，44.1 是泰國鑼檔案的原生取樣率嗎？

另外，網站寫「可用於任何專案、無限制」，我理解為涵蓋商業軟體產品開發與驗證期間的使用（錄音本身不會再散布或進產品），想請您簡短確認這個理解正確。

謝謝您的協助，也謝謝這個資源免費開放這麼多年。

## 寄出前檢查
- [ ] 找到信箱後填入；填入姓名。
- [ ] 回覆存 `docs/correspondence/`，並更新 `docs/EXTERNAL_DATASET_SUPPLEMENT.zh-TW.md` §3 的缺口 4。
