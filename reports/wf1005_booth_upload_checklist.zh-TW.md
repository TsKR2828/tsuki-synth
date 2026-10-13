# BOOTH 上架步驟：只賣音效包（WF1005-L，2026-10-12）

> 給月月。AI 能做的都做完了：授權照預設填好、草稿方框拿掉、正式 zip 打好並驗證過。剩下是你本人在 BOOTH 後台做的事。
> 證據：`reports/gate_outputs/wf1005_L_license_release.txt`（12 處空格前後對照、zip sha256、驗證輸出）。

## 先看這三件事

1. **要上傳的只有一個檔**：下面表裡的 `TsukiSynth_Worldview_SE_Pack_v1.1.zip`。同資料夾還有 6 個別的 zip，**不要傳**（見第 6 節）。
2. **授權第 9 條（準據法與法院）是 AI 的建議，不是法律意見。** 預設值是「中華民國（台灣）法律、台灣台北地方法院」；要不要找律師看、要不要改，由你決定。要改的話告訴 AI 哪一條，AI 改完會重打 zip（sha256 會變）。
3. **還沒定價**。建議 ¥900，或 ¥800 開賣、觀察一個月再調（出處：`reports/decision_packets/WF1002_addendum_decisions.zh-TW.md` 檔尾「音效包上架清單」第 2 步；`LISTING_COPY_v1_1.md` 第 16 行）。AI 不替你定。

## 1. 要上傳的檔

| 項目 | 內容 |
|---|---|
| 路徑 | `E:\Tsuki-project\tsuki-synth\exports\products\clean_batch2_v1_1_candidate\packages\TsukiSynth_Worldview_SE_Pack_v1.1.zip` |
| sha256 | `867f94faf5f6c2114024ce91a957b47443657c34a5a9926e5eca649058cb18b5` |
| 大小 | 77,927,295 B（約 74.3 MiB；BOOTH 單檔上限 1.2 GB，差很多） |
| 成員 | 51 個：`LICENSE.txt`、`README.txt`、43 個音效 WAV、6 個 loop-ready WAV |
| 內含授權 | `LICENSE.txt` 的 sha256 `e965080d8bd9e147481e683196cfa566ce32b3424f114fee9defbce8c7158a34`（12 處空格已填、0 處 TBD、0 處草稿標記） |

上傳前自己核對一次（PowerShell）：

```
Get-FileHash -Algorithm SHA256 "E:\Tsuki-project\tsuki-synth\exports\products\clean_batch2_v1_1_candidate\packages\TsukiSynth_Worldview_SE_Pack_v1.1.zip"
```

輸出的 Hash 要跟上表 sha256 相同（大小寫不計）。不同的話別傳，告訴 AI。

**上傳位置**：BOOTH 商品編輯頁的「ファイルの追加・管理」。專輯的 WAV 才有「アルバム情報」會被轉檔的問題，音效包 zip 走「ファイルの追加・管理」就沒事（出處：`reports/wf1002b_booth_image_specs.zh-TW.md` §1-1，BOOTH 官方說明）。

## 2. 日文文案

- 出處：`exports/products/clean_batch2_v1_1_candidate/LISTING_COPY_v1_1.md` 的 **A 段「音效包 — BOOTH（日文主文案）」**（第 11～57 行左右）。
- 商品名、本文、収録內容、音量、ループ、利用規約、タグ都在裡面。
- 第 16 行的「価格（建議）」是給你的備註，**不要貼進商品頁**。
- 「利用規約」段最後一句「詳細は同梱の LICENSE をご覧ください」，跟 zip 內的 `LICENSE.txt` 對得上。
- 這份文案是 AI 起草的；我沒有查到有人審過日文。要不要請人看一眼，由你決定。

## 3. 價格

| 選項 | 內容 |
|---|---|
| 建議 | ¥900 |
| 或 | ¥800 開賣，觀察一個月再調 |
| 現況 | **你還沒定**。定了以後告訴 AI，文案備註可以同步改。 |

## 4. 商品圖

- 草稿位置：`E:\Tsuki-project\tsuki-synth\exports\products\clean_batch2_v1_1_candidate\art\`
  - `cover_draft.png`（1600×1600）
  - 六張世界觀縮圖 `thumb_akashic.png`、`thumb_rabbit.png`、`thumb_restraint.png`、`thumb_forest.png`、`thumb_ocean.png`、`thumb_clockwork.png`（各 1200×1200）
- 你 10-02 裁的是「等平台規格」（Q24a=C）。AI 查過 BOOTH 官方說明：**商品圖的格式、尺寸、檔案大小、張數、比例，官方都查不到**（`reports/wf1002b_booth_image_specs.zh-TW.md`）。
- 非官方觀察（只當參考）：顯示用的圖長邊約 1024 px；商品列表縮圖會從第一張圖的中央裁成正方形。草稿是正方形，照這個觀察不會被裁。
- **請你登入 BOOTH 後台，看商品圖上傳畫面有沒有規格提示。有提示就照提示**，沒有的話再決定草稿能不能直接用。草稿是 AI 做的，還沒經你點頭。
- 商品圖可以後補，不擋上傳 zip。

## 5. 上架前最後確認（你本人）

1. BOOTH 店鋪與 PayPal 都已經好了（你說註冊完成）。
2. 把第 1 節的 zip 傳到 BOOTH，商品頁貼第 2 節的日文文案，填第 3 節的價格，放第 4 節的商品圖。
3. 授權裡寫的授權通路是「BOOTH 與 itch.io」。**只上 BOOTH 沒問題**，itch.io 之後上的話英文文案在 `LISTING_COPY_v1_1.md` 的 B 段。
4. 授權第 12 條聯絡方式是「BOOTH 的訊息功能」。如果之後只在 itch.io 賣給沒有 BOOTH 帳號的人，他們不一定聯絡得到你；到時候再決定要不要加別的聯絡方式。
5. 授權第 8 條的白話：違約的人，違約前依規定發佈的作品可以留在市面上；違約後他要停止使用並刪除複本。預設是這樣，你要改隨時說。
6. 聽人把關（Q28）建議做但不擋音效包上架。

## 6. 不要上傳的檔

都在 `packages\` 資料夾，檔名容易混：

| 檔 | 為什麼不傳 |
|---|---|
| `TsukiSynth_Worldview_SE_Pack_v1.1_candidate.zip` | 舊的候選版，裡面的 `LICENSE.txt` 還是草稿（12 處 TBD、有草稿方框） |
| `TsukiSynth_Worldview_SE_Pack_v1.1_candidate_FAB.zip` | 舊候選版，Fab 暫緩 |
| `TsukiSynth_Worldview_SE_Pack_v1.1_FAB.zip` | 正式命名但 Fab 暫緩（Q23=B），不上架 |
| `TsukiSynth_Album_Vol1_v1.1.zip` | 正式命名是 `--release` 一次打三個造成的。**專輯授權還沒裁**（影片 BGM A／B 等，`LICENSE_ALBUM_v1_1.txt` 仍有 16 處 `[TBD`、42 處 TBD 字樣），這個 zip 也沒有授權檔，不能賣 |
| `TsukiSynth_Album_Vol1_v1.1_candidate.zip` | 專輯舊候選版 |
| `TsukiSynth_listening_kit_v1_1.zip` | 給聽人的試聽包，內部用 |

## 7. 這次授權填了什麼（三語語意一致，逐字前後對照在證據檔 §1）

| 條 | 填入 |
|---|---|
| §1 授權通路 | BOOTH 與 itch.io |
| §8 違約前已正常發佈的作品 | 可以繼續留在市面上 |
| §9 準據法與法院 | 中華民國（台灣）法律；台灣台北地方法院為管轄法院（AI 建議，非法律意見） |
| §12 聯絡方式 | BOOTH 的訊息功能 |

兩個小提醒，AI 沒有替你決定：

- 預設值只說「台灣台北地方法院」，沒說是不是「專屬」管轄，所以條文只寫「管轄法院」，沒寫「專屬」。
- 預設值寫的是「台灣台北地方法院」，條文照寫，沒有改成官方用字「臺灣臺北地方法院」。

## 8. 專輯現況（不在這次裁決範圍）

`LICENSE_ALBUM_v1_1.txt` 一個字都沒動。仍待你裁：第 5 條影片 BGM 選 A 或 B（要跟 DistroKid 開不開 Content ID 一起想）、署名、通路、出處標示、準據法、語言版本等。
專輯裡有幾格（通路、準據法、聯絡）跟音效包同類，但你只對音效包說「照預設」，所以 AI 沒有套用到專輯。要套的話跟 AI 說一聲。
