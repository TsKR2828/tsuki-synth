# 信件草稿 1：向 TU Berlin 請求樂器指向性資料庫的商業使用許可

> 狀態：**草稿，由月月自行寄出**（AI 不代發）。2026-09-10 依月月裁決「兩封信要寫」擬稿。
> 收件人：David Ackermann <david.ackermann@tu-berlin.de>（信箱來源：SOFA 檔 `AuthorContact` 屬性與論文通訊欄，見 `docs/EXTERNAL_DATASET_A8.zh-TW.md` §4.1）
> 建議副本：Fabian Brinkmann、Stefan Weinzierl（論文共同作者；信箱請自行從 TU Berlin Audio Communication Group 網頁確認，本文件不臆測）
> 語言：英文（收件人為德國學者）。下方附中文對照，寄英文版即可。

## 這封信要達成什麼（白話）

資料庫的授權標籤是 CC BY-NC-SA 4.0，NC = 不可商業使用。我們的用途是「拿它當尺，私下檢查合成器算出來的音量量級對不對」，
資料本身不會進產品、不會散布。這封信問兩件事：(1) 這種內部驗證用途在他們眼中算不算「商業使用」；
(2) 若算，能否給書面許可（或告知授權費用／條件）。同時順便回報我們發現的兩個小問題（DOI 失效、arXiv 版授權標示與資料檔不一致），
這是給對方的善意，也讓對方知道我們真的仔細讀過。

## 英文正文（可直接複製）

**Subject:** Permission request: internal validation use of "A Database with Directivities of Musical Instruments" (DepositOnce 10.14279/depositonce-19858)

Dear Dr. Ackermann,

I am writing regarding the dataset *A Database with Directivities of Musical Instruments* (DepositOnce, DOI 10.14279/depositonce-19858; JAES 72(3), 2024; arXiv:2307.02110). Thank you for making such a carefully calibrated resource public.

I am an independent developer working on TsukiSynth, a physical-modelling software synthesizer (hammered strings, tongue drum, gong) that I intend to release commercially. A distinctive constraint of the project is that I am a deaf developer: every claim the synthesizer makes about its sound is verified numerically rather than by ear. Your database is, to my knowledge, the only public instrument recording set calibrated to absolute sound pressure (1.0 ≡ 1 Pa), which makes it uniquely valuable as an external reference for checking whether the absolute levels my model predicts are physically plausible.

My intended use is narrow:

- The data would be used only as a private reference for sanity-checking model output (order-of-magnitude comparison of sound pressure levels, and partial-frequency ratios for the guitar and harp recordings).
- No audio, directivity data, or derived numerical tables from the database would be included in the product, its presets, its documentation, or any distributed file.
- The database would not be redistributed, and the SOFA files stay on my development machine only.

The licence attached to the SOFA files and the documentation PDF is CC BY-NC-SA 4.0. I would like to ask:

1. Whether you consider the internal validation use described above to fall within the non-commercial scope of the licence, given that the product being validated is commercial but the data never enters it; and
2. If not, whether you would be willing to grant written permission for this specific use, and under what conditions.

I would of course credit the database in the project's technical documentation regardless of the outcome, and I am happy to share the comparison results if they are of any interest to your group.

Two small observations, in case they are useful to you:

- The DOI printed inside the documentation PDF and in the `Reference` attribute of the SOFA files (10.14279/depositonce-5861.3) currently returns HTTP 404; the resolvable identifier is 10.14279/depositonce-19858.
- The arXiv preprint (2307.02110) states the licence as CC BY-SA 4.0, whereas the SOFA metadata and the documentation PDF state CC BY-NC-SA 4.0. I have treated the data files as authoritative.

Thank you very much for your time.

Kind regards,

[Your name]
[Optional: project page or GitHub link]

## 中文對照（給月月看，不寄）

主旨：關於《樂器指向性資料庫》內部驗證用途的許可請求

Ackermann 博士您好：

我來信是關於貴團隊公開的《A Database with Directivities of Musical Instruments》。感謝你們公開這麼仔細校準的資源。

我是獨立開發者，正在做一個物理建模合成器 TsukiSynth（敲擊弦、舌鼓、鑼），打算商業發行。這個專案的特別之處是我是聾人開發者，合成器對聲音的每一項主張都用數字驗證、不靠耳朵。據我所知貴資料庫是唯一校準到絕對聲壓的公開樂器錄音集，對檢查「模型算出來的絕對音量是否物理合理」非常有價值。

我的用途很窄：只當私下的參考尺（比對聲壓量級、吉他與豎琴的泛音頻率比值）；任何音訊、指向性資料或推導表格都不會進產品、preset、文件或任何散布檔案；資料不會再散布，只留在我的開發機。

檔案上的授權是 CC BY-NC-SA 4.0。想請教：(1) 上述內部驗證用途是否落在非商業範圍內（產品是商業的，但資料從不進產品）；(2) 若不算，是否願意給這個特定用途的書面許可，條件為何。

不論結果如何我都會在技術文件署名，也樂意分享比對結果。

兩個小發現供參考：文件與 SOFA 檔內印的 DOI 5861.3 目前 404，可解析的是 19858；arXiv 預印本寫 CC BY-SA，檔案 metadata 與 PDF 寫 CC BY-NC-SA，我以檔案為準。

謝謝您的時間。

## 寄出前檢查
- [ ] 填入姓名；要不要放專案連結由你決定。
- [ ] 副本收件人信箱請自行確認（本文件不臆測）。
- [ ] 若對方回覆「內部驗證可以」或給書面許可，把回信存到 `docs/correspondence/` 並在 `docs/EXTERNAL_DATASET_A8.zh-TW.md` §4.1 記錄；A8 即可從「私下對照」升級。
