# TsukiSynth End User License Agreement — DRAFT

> **狀態：草稿（DRAFT），不是法律意見，需月月逐條審。** 建立：2026-09-25（WF0925-G1）。
> 這份是給**買家**的使用授權。repo 根目錄的 `LICENSE` 是原始碼的專有聲明（「No permission is granted to any person to use…」），
> 不能拿來當買家授權（盤點 `release-readiness:S3`）。
> 寫法：英文條文為主，最後附繁中摘要。`[[ … ]]` 是**待月月決定**的空格或選項，定案前不可發佈。
> 本草稿沒有參考或複製任何其他公司的 EULA 原文；條款結構是常見的軟體授權項目。
> 與 JUCE 8 EULA 相關的限制（禁止逆向、不得移除 JUCE 聲明）依據 `docs/legal/JUCE8_LICENSE_REVIEW.zh-TW.md` §4。

---

## 待月月決定的空格一覽（先看這張表）

| # | 空格 | 選項（不替月月選） | 相關盤點條目 |
|---|---|---|---|
| E1 | 授權人名稱（§1） | 用「TsKR2828」或其他正式名稱；是否寫真名 | S10 |
| E2 | 授權範圍（§2.1） | 甲：每位使用者，本人自己的電腦不限台數（同一時間一人使用）／乙：最多 N 台電腦 | S3、S8 |
| E3 | 是否限制「用本外掛做取樣音源再販售」（§3.2） | 甲：不限制／乙：禁止把未加工的單音取樣包成音源或 preset 包販售 | — |
| E4 | 是否寫「不得用於 AI 訓練」（§4.1 (h)） | 甲：不寫／乙：寫（對照：音效包 `LICENSE_SE_PACK.txt` 目前只禁「上傳到訓練資料集」、沒禁拿去訓練，盤點 R6） | R6 |
| E5 | 退款（§8） | 依販售平台規定／自訂天數／不退款（消費者法另有規定者從其規定） | — |
| E6 | 準據法與管轄（§12） | 空白，待月月定（例如中華民國法律、台灣某地方法院） | — |
| E7 | 聯絡信箱（§14） | 待月月提供（VST3 `moduleinfo.json` 的 E-Mail 目前也是空的） | S10 |
| E8 | 以哪個語言版本為準（§13.4） | 英文為準／中文為準 | — |
| E9 | 是否附 DRM／序號啟用（§2.4） | 變現計畫建議無 DRM；月月尚未裁決 | S8 |

---

## English text (draft)

**TsukiSynth — End User License Agreement**
Version [[draft 2026-09-25]]

PLEASE READ THIS AGREEMENT BEFORE INSTALLING OR USING TSUKISYNTH. BY INSTALLING, COPYING OR USING
THE SOFTWARE YOU AGREE TO THIS AGREEMENT. IF YOU DO NOT AGREE, DO NOT INSTALL OR USE THE SOFTWARE.

### 1. Parties and definitions

1.1 "Licensor" means [[E1: TsKR2828 / legal name]], the copyright holder of TsukiSynth.

1.2 "You" means the individual person, or the single company or organisation, that obtained a
licence to the Software by purchasing it from the Licensor or from a sales platform authorised
by the Licensor.

1.3 "Software" means the TsukiSynth VST3 plug-in, the TsukiSynth Standalone application, the
TsukiSynth command-line renderer, the factory presets, example files and documentation supplied
with them, and any updates the Licensor provides to You, in machine-readable (object code) form.

1.4 "Output" means audio, MIDI or other files that You create by using the Software, including
recordings and renders.

### 2. License grant

2.1 Subject to this Agreement and to payment of the purchase price, the Licensor grants You a
non-exclusive, non-transferable, non-sublicensable licence to install and use the Software
[[E2 option A: on any number of computers that You own or control, provided that the Software is
used by only one person at a time]] [[E2 option B: on up to [[N]] computers that You own or
control]].

2.2 The licence is perpetual for the version of the Software You obtained, unless it ends under
Section 11.

2.3 You may make backup copies of the installer for Your own archival purposes.

2.4 [[E9: The Software does not contain copy protection or online activation. A serial number or
order number, if issued, is a proof of purchase only.]]

2.5 The Software is licensed, not sold. The Licensor keeps all rights not expressly granted to You.

### 3. Your Output

3.1 As between You and the Licensor, You own the Output. You may use, publish, sell and license
Your Output for any purpose, including commercial music, video, games, streaming and broadcast,
without paying any further fee or royalty to the Licensor and without crediting the Licensor
(credit is appreciated but not required).

3.2 [[E3 option B: You may not use the Software to create, sell or distribute sample libraries,
virtual instruments or preset collections that consist mainly of isolated, unprocessed single-note
recordings or presets of the Software, where the purpose is to let others reproduce the sound of
the Software without a licence.]]

3.3 The Licensor makes no claim to Your compositions, arrangements or performances.

### 4. Restrictions

4.1 Except as expressly allowed by this Agreement or by applicable law that cannot be excluded by
contract, You may not:
(a) copy, distribute, share, upload, rent, lease, lend, sell or sublicense the Software or Your
licence, or make the Software available to anyone else, including over a network;
(b) transfer the Software or Your licence to another person [[E2: unless the Licensor agrees in writing]];
(c) reverse engineer, decompile or disassemble the Software, or try to derive its source code;
(d) modify, translate or create derivative works of the Software;
(e) remove or alter any copyright, trademark or licence notice in the Software or its documentation,
including the notices of third-party components;
(f) circumvent any technical limitation of the Software;
(g) use the Software in violation of any law;
(h) [[E4 option B: use the Software, its presets or its documentation to train, fine-tune or evaluate
a machine-learning model, except that You may use Your own Output as You wish under Section 3]].

4.2 The Software includes the JUCE framework, which the Licensor uses under the JUCE 8 End User
Licence Agreement. This Agreement does not grant You any licence to the JUCE framework on its own.

### 5. Third-party components

5.1 The Software contains third-party software and fonts, listed with their copyright notices and
licence texts in the file THIRD_PARTY_NOTICES.txt that is installed with the Software.

5.2 Those components are provided under their own licences. Nothing in this Agreement limits any
right You have under those licences, and where a third-party licence grants You broader rights for
its component, that licence applies to that component.

### 6. Trademarks

6.1 "TsukiSynth" and related names and logos belong to the Licensor. This Agreement does not grant
You any right to use them, other than to truthfully state that Your Output was made with TsukiSynth.

6.2 VST is a registered trademark of Steinberg Media Technologies GmbH. IBM Plex(R) is a trademark
of IBM Corp, registered in many jurisdictions worldwide. Other names are the property of their
respective owners.

### 7. Updates and support

The Licensor may, but is not required to, provide updates, fixes or support. Updates provided to
You are part of the Software and covered by this Agreement, unless they come with their own terms.

### 8. Refunds

[[E5: Refunds follow the policy of the platform where You bought the Software / a refund within
[[N]] days of purchase / no refunds, except where applicable consumer law requires otherwise.]]

### 9. Disclaimer of warranty

9.1 TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE SOFTWARE IS PROVIDED "AS IS" AND "AS
AVAILABLE", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING ANY WARRANTY OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, OR THAT THE SOFTWARE WILL BE
ERROR-FREE OR UNINTERRUPTED.

9.2 The Software is a sound-generating tool. You are responsible for monitoring levels and for
protecting Your hearing and equipment.

9.3 Some jurisdictions do not allow the exclusion of certain warranties. In those jurisdictions the
exclusions above apply only to the extent permitted by law, and You keep any consumer rights that
cannot be excluded.

### 10. Limitation of liability

10.1 TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE LICENSOR IS NOT LIABLE FOR ANY INDIRECT,
INCIDENTAL, SPECIAL OR CONSEQUENTIAL DAMAGES, OR FOR LOSS OF DATA, PROFITS, REVENUE OR BUSINESS,
ARISING FROM OR RELATED TO THE SOFTWARE OR THIS AGREEMENT, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.

10.2 THE LICENSOR'S TOTAL LIABILITY UNDER THIS AGREEMENT IS LIMITED TO THE AMOUNT YOU PAID FOR THE
SOFTWARE.

10.3 Nothing in this Agreement limits liability that cannot be limited under applicable law.

### 11. Termination

11.1 This Agreement ends automatically if You breach it and, where the breach can be fixed, You do
not fix it within [[14]] days after the Licensor tells You about it.

11.2 When this Agreement ends, You must stop using the Software and delete all copies in Your
possession.

11.3 Output You created before termination remains Yours, and Section 3.1 continues to apply to it.
Sections 3, 5, 6, 9, 10, 12 and 13 survive termination.

### 12. Governing law and jurisdiction

This Agreement is governed by the laws of [[E6: to be decided]]. [[E6: court / jurisdiction to be
decided]]. This does not take away any mandatory consumer protection You have under the law of the
country where You live.

### 13. General

13.1 This Agreement, together with THIRD_PARTY_NOTICES.txt, is the entire agreement between You and
the Licensor about the Software.

13.2 If any provision is found unenforceable, the rest of the Agreement stays in effect.

13.3 If the Licensor does not enforce a provision, that is not a waiver.

13.4 [[E8: This Agreement is written in English. A Traditional Chinese summary is provided for
convenience only; if the two differ, the English text prevails. / 以中文版為準]]

### 14. Contact

[[E7: contact e-mail]]

---

## 繁體中文摘要（方便月月審，不是正式譯本）

| 條 | 白話 |
|---|---|
| 1 定義 | 「軟體」＝VST3 外掛＋Standalone＋CLI 渲染器＋工廠 preset、範例、說明文件；「產出」＝你用它做出來的音訊、MIDI 等檔案 |
| 2 授權 | 付錢後得到非專屬、不可轉讓的永久使用權（限買到的那一版）；可以裝幾台 **[[E2 待月月定]]**；可備份安裝檔；沒有 DRM／序號只是購買證明 **[[E9 待月月定]]**；是授權不是賣斷 |
| 3 產出 | **你做出來的音訊歸你**，可商用（音樂、影片、遊戲、直播、廣播），不用再付費、不用標註出處（歡迎標註）；是否禁止把單音取樣包成音源販售 **[[E3 待月月定]]** |
| 4 限制 | 不可散布、分享、上傳、出租、轉授權；不可轉讓；**不可逆向、反編譯**；不可修改；不可移除著作權與授權聲明（含第三方）；不可繞過技術限制；是否禁止拿來訓練 AI **[[E4 待月月定]]**。軟體內含 JUCE，本合約不另外授權 JUCE 給買家 |
| 5 第三方元件 | 清單與授權全文見安裝目錄的 `THIRD_PARTY_NOTICES.txt`；第三方授權給你的權利，本合約不會減少 |
| 6 商標 | TsukiSynth 名稱屬於授權人；可以如實說「用 TsukiSynth 做的」。VST 是 Steinberg 的註冊商標；IBM Plex 是 IBM 的商標 |
| 7 更新與支援 | 沒有義務提供；提供的更新也受本合約約束 |
| 8 退款 | **[[E5 待月月定]]** |
| 9 免責 | 依現狀提供，不保證無錯誤；使用者自己注意音量、保護聽力與器材；消費者法規定不能排除的權利照樣保留 |
| 10 責任上限 | 間接損失不賠；賠償總額以你付的價錢為上限（法律不允許限制的除外） |
| 11 終止 | 違約且接到通知後 **[[14]]** 天內沒改正就自動終止；終止後要停用並刪除；**終止前做出的音訊仍歸你** |
| 12 準據法 | **[[E6 待月月定]]**；不影響買家所在國的強制消費者保護 |
| 13 其他 | 完整合約＝本合約＋`THIRD_PARTY_NOTICES.txt`；部分無效不影響其他；不主張不代表放棄；以哪個語言為準 **[[E8 待月月定]]** |
| 14 聯絡 | **[[E7 待月月提供信箱]]** |

### 起草時查過的事實（給審稿用）

- 軟體會寫入的使用者資料位置（解除安裝時不應刪除，見 `tools/installer/README.md`；行號是 HEAD `18430c4`，
  工作樹有其他卡未 commit 的修改，行號可能不同）：
  `%APPDATA%\TsukiSynth\Presets`（`src/PresetManager.h:444-447`）、`%APPDATA%\TsukiSynth\IR`（`src/IRLibrary.h:121-123`）、
  `文件\TsukiSynth\Recordings`（`src/PluginProcessor.cpp:444-446`）、`桌面\TsukiSynth_Renders`（`src/ScoreConsole.h:87-88`）。
- 本卡在 `src/` 搜 `juce::URL`、`WebInputStream`、`http://`、`https://`、`StreamingSocket`：**0 筆**，TsukiSynth 自己寫的程式碼沒有連網。
  若月月想在 EULA 加一句「本軟體不會連網、不收集資料」，要先確認 JUCE 內建功能在這個 build 的實際行為（本卡沒查），所以草稿**沒有**放這一句。
- JUCE 8 EULA 2.4 禁止逆向 Framework、2.9 禁止移除 JUCE 的聲明——§4.1 (c)(e) 對應這兩條。
