# TsukiSynth 交接文件

> 交接視窗：**2026-10-03（WF1002＋WF1002b 完工、已 push；WF1003 整合卡全綠、staged 未 commit）**　repo：`E:\Tsuki-project\tsuki-synth`　分支：`fix/deep-physics-audit-20260716`
> **新 session 先讀 §0、§1 再動手。** 最新裁定表與各卡結果在 `docs/workcards/WF1002_README.md`（§1 裁定表、§3 WF1002、§4 WF1002b）；
> 待辦勾選清單在 `TODO.md` 開頭；各輪細節與歷史決策在 `DEVLOG.md`（本檔不再保留舊輪的大段數字）。

---

## 0. 現況

### WF1003（2026-10-03 下午；**staged、沒 commit、沒 push**，等月月審）

月月 10-03 裁「都重跑，開 Dynamic Workflow；裁決兩項照建議規劃」。本輪 8 張卡（Sonnet 工兵＋Opus 稽核親自重跑），整合卡全套 GATE 1～9 全綠，
證據 `reports/gate_outputs/wf1003_INTEGRATION.txt`＋`wf1003_integration_raw/`。

| 卡 | 結果 | 白話 |
|---|---|---|
| B2 Body 層響度正規化 | **稽核 FAIL，已還原** | 增益沒有上限，Custom Harmonics 設定下輸出反而大 +22.7 dB（峰值 +14.80 dBFS）。修法小，patch 在 `E:\Tsuki-project\_scratch\wf1003\failed_B2\`；要重做（`wf1003_B2_audit.txt` §7）。 |
| V Q09 voice pool 16 vs 32 | PASS → **維持 16** | 32 顆能消除月光舌鼓版的 64 次搶音，但 32 顆 Piano 同時發聲時約三成區塊來不及（p99 20.5 ms／預算 10.67 ms）。按引擎分大小是另一個要裁的選項（`reports/decision_packets/WF1003_decisions.zh-TW.md`）。 |
| S 小修批次 | PASS | `melody_verify.verify()` 加 `cli`、sustain 0 拒量搬出 xfail、HostProbe 補 Q05「真的亮燈」路徑（+10 項）、docstring／文件行號改條目名。 |
| H 75 首雜湊比對工具 | PASS | `tools/hash75_compare.py`（整合卡標準步驟從此有固定工具）。 |
| C2S4 FM 同音重打 +1.5 dB | PASS（唯讀） | 相位抵消機制成立；+1.5 dB 是重打間隔的巧合（掃間隔 −3～+1.5 dB、平均 +0.03 dB），不用改程式。報告 `reports/wf1003_c2s4_same_note_level.zh-TW.md`。 |
| R release CI 重跑 | PASS | `release-physics.yml` run 37094711041 在 `bee2889` 5 job 全綠（靜態 CRT／壓縮器／FM 改動後第一次）。 |
| I Inno Setup＋`.iss` 編譯 | **BLOCKED** | 安裝精靈會跳「選擇安裝模式」要人點；ISCC 不在機器上，整合卡第 10 步（重編安裝檔）也因此 BLOCKED。 |

渲染：75 首 WAV 逐首、8 首位元基準都跟 WF1002b 相同（V 卡是外掛層、不經 CLI）。

### WF1002／WF1002b（10-02～03，已 push 到 `168688e`）

月月 10-02 裁「照 Fable 的說法做」：WF0925 彙總裁決包 38 題（Q01～Q38）以 Fable 5 第三方評斷為準，WF1002 輪全部落地；
同輪冒出的追加裁決 N1～N9，月月 10-02 全照建議（N9＝A 接受靜態 CRT 的位元變化），WF1002b 輪落地。各 lane 稽核 PASS，整合卡全綠。
10-02～03 分批 commit＋push，最後一個是 `168688e`，GitHub CI 在 `168688e` 上 6 job 全綠。**AI 能做、不需裁決的大項都做完了**；
剩下的是月月本人的事（賣音效包的註冊、定價、授權空格）、要月月裁的小題、以及幾張可以接著開的後續卡（§1-5）。

這兩輪改了什麼（白話）：外掛改成靜態 CRT（買家免裝 VC++）、DAW 只看得到 27 個工廠 preset、加 CLIP 削波指示燈、
拿掉壓縮器「沒在壓也照加」的固定補償（27 個 preset 各小 2.00～7.50 dB，最大聲的剩 −1.85 dBFS）、FM 同音反覆的殭屍 voice 修好、
IR 載入失敗改走缺檔三態、F5 量法換 Blackman-Harris 窗（「F5 PASS 依賴探針 0.8 mm」的脆弱點解除）、規則 R6／R7 改字面、§6 補登三列、主張域升格 8 條（WF1002）＋C5（WF1002b）。
**N1 副作用**：使用者自己存的、開了壓縮器的舊 DAW 專案或 preset，重開後也會變小聲（旋鈕極端值時最多 19 dB）。

## 1. 立刻要知道的事

### 1-1 月月待辦（賣音效包的最短路徑放最前）

只賣音效包，照這個順序（出處：`reports/decision_packets/WF1002_addendum_decisions.zh-TW.md` 檔尾「音效包上架清單」）：

1. **你本人註冊**：pixiv → BOOTH 開店 → 綁 PayPal（AI 不能代建帳號）。
2. **你定價**：建議音效包 ¥900（或 ¥800 開賣觀察一個月）、專輯 ¥500。
3. **你回授權 4 個空格**（`LICENSE_SE_PACK_v1_1.txt` 的 §1 通路、§8 終止前已發佈作品、§9 準據法與法院、§12 聯絡方式；回「照預設」就用裁決包裡的建議預設，**非法律意見**）。
4. **AI 接手**：填空、拿掉草稿標記、重打正式 zip（`--release`）、跑驗證。
5. **商品圖（Q24a）**：BOOTH 官方說明查不到任何商品圖規格（`reports/wf1002b_booth_image_specs.zh-TW.md`；觀察到顯示長邊 1024 px、縮圖從第一張中央裁正方形）。要你登入後台看上傳畫面有沒有提示，再決定草稿能不能用。
6. **你上傳**：zip＋商品圖＋日文文案（`LISTING_COPY_v1_1.md` A 段）。BOOTH 單檔上限 1.2 GB、全店 10 GB，音效包 77.9 MB 符合。
   專輯 WAV 要用「ファイルの追加・管理」上傳（用「アルバム情報」會被轉成 m4a／mp3／flac）。

其他只能你本人做或裁的（不擋音效包）：
- 專輯：影片 BGM 授權選 A 或 B、自己開不開 Content ID、DistroKid 登入確認 K1～K7、AI Radiance 作曲署名、MP3 試聽檔要不要從 TPDF 版重出。
- 聽人把關 Q28（找認識的人＝C，發案＝A）；試聽包已備（`clean_batch2_v1_1_candidate/packages/TsukiSynth_listening_kit_v1_1.zip`）。
- 合成器：EULA 的 E1／E3／E6／E7（Q32）；寄 JUCE 詢問信（草稿 `E:\Tsuki-project\_private\JUCE_sales_inquiry_draft.md`）。
- 環境：清空資源回收筒；Cubase 重掃外掛（§1-4）；要不要把 branch merge 進 `main`（目前沒 merge）。
- 舊的未裁小題 O02～O14（UI 規格送誰、換源排程、安裝包附不附 CLI 等），清單在 `TODO.md`「仍開著」。

### 1-2 git 狀態（2026-10-03 核對）

- **WF1003（10-03 下午）**：HEAD＝`origin/...`＝`bee2889`（10-03 上午兩個文件 commit `cde44c6`、`bee2889` 已 push）；WF1003 全部改動與證據已由整合卡 **`git add`（staged）**，沒 commit、沒 push，等月月審。
  staged 清單見 `reports/gate_outputs/wf1003_integration_raw/19_git_status_after_add.txt`。
- （10-03 上午的狀態，保留作歷史）本機 HEAD＝`origin/fix/deep-physics-audit-20260716`＝`168688e`，工作樹乾淨、stash 空。
- `main`＝`origin/main`＝`3f9b90a`（09-15 merge），**branch 比 main 多 26 個 commit，沒 merge**。
- 26 個 commit 的分段：WF0914 成果 7 個（09-25，`a09058c`～`18430c4`）、WF0925＋WF0925b 8 個（09-30，`eba91ba`～`643ab8a`）、
  09-30 證據 3 個（`b05b24e`、`d9aab66`、`b41298c`）、WF1002 5 個（10-02，`2c4443e`～`804bf03`）、WF1002b 4 個（10-03，`59c0b06`～`168688e`）。逐條看 `git log --oneline 3f9b90a..HEAD`。
- R7 現行字面（10-02 Q03＝A）：不 commit、不 push（月月明示裁決時除外）；稽核 PASS 後由稽核 `git add` 供月月審。

### 1-3 基線

**WF1003 整合卡新基線（`reports/gate_outputs/wf1003_INTEGRATION.txt`，2026-10-03）**——跟下面 WF1002b 表只差這幾格：
pytest **312＝306＋1 skip＋5 xfail**（+2＝S 卡兩條 stem_verify 單元測試）；HostProbe **241 PASS／0 FAIL**（+10＝S 卡「Q05 real lit path」）；
AuditTest 仍 111；75 首雜湊逐首與 WF1002b 相同（`tools/hash75_compare.py`，下次參考表用 `wf1003_integration_raw/12_hash75_vs_wf1002b_integration.txt`）；8/8 IDENTICAL；pluginval SUCCESS＋validator 47/47；靜態 CRT 匯入 0。
`build\` 的 sha256 改為：CLI `d308fed2…`、VST3 `f6147296…`、Standalone `05e41a85…`（全量重建；CLI 原始碼沒改，雜湊變是重編本身造成，WAV 不變）。manifest renderer 欄現行 `d308fed24af8`。
**release CI**：`release-physics.yml` run 37094711041（`bee2889`）全綠（R 卡）。安裝檔編譯仍 BLOCKED（ISCC 沒裝）。

WF1002b 整合卡的基線（`reports/gate_outputs/wf1002b_INTEGRATION.txt`）：

| GATE | 現況 |
|---|---|
| 建置 | 三主 target＋五測試 target EXIT 0；CLI／VST3／Standalone／HostProbe 都不再匯入 MSVCP140／VCRUNTIME140／api-ms-win-crt（靜態 CRT） |
| ctest | 4/4；AuditTest 111 PASS／0 FAIL（含 Q01 硬 CHECK：\|IR−ALGO\| 0.112 dB ≤ 0.25 dB） |
| pytest | **310＝304 passed＋1 skip＋5 xfail**（CI runner 上是 302＋3 skip＋5 xfail，同 310） |
| `physics_verify --full` | NO CHECKED FAILURES（3 個 rubber N/A 是既有的）；F5 新窗 5 引擎 −84.5～−96.3 dB |
| `physics_verify --selftest` | 14/14 |
| `verify_score --all` | 75/75（1 項既有豁免）；**75 首 WAV 雜湊逐首與 WF1002 整合卡相同** |
| 位元不變 | 8/8 IDENTICAL（基準 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`） |
| HostProbe | 231 PASS／0 FAIL（cwd 在 repo 外）；E16 27 個 preset 最大峰值 −1.85 dBFS |
| pluginval＋Steinberg validator | strictness 10 SUCCESS（Plugin programs：Num programs 27）；validator 47/47 |

- `build\` 現在的 sha256：CLI `f99b4a80…`、VST3 `fa13ac17…`、Standalone `6a325842…`。商品母帶的渲染器仍是舊的 `9123db8f…`（§9）。
- **CI**：`physics.yml` 在 `168688e`（run 37036197563）6 job 全綠，HostProbe 231/0、Linux leg 已叫 `ubuntu-24.04-gcc`（804bf03 那次 run 37017182460 首次實戰通過）。
  `release-physics.yml` 只在 09-30 跑過一次（run 36602858471，HEAD `d9aab66`，全綠）；**WF1002／WF1002b 的改動（靜態 CRT、壓縮器、FM）之後還沒再跑過**。

### 1-4 部署（2026-10-03 磁碟核對）

- 部署腳本 `E:\Tsuki-project\_tools\deploy\deploy_tsukisynth.ps1`（Q35＝A）。磁碟上看得到**已經用 -Apply 跑過一次（10-03 01:53）**：
  `C:\Program Files\Common Files\VST3\TsukiSynth.vst3` 的 sha256＝`fa13ac17…`（跟 `build\` 相同）；
  三份舊副本（`TsukiSynth_VST3_2026-09-10` 子資料夾、`(x86)` 那份、`%USERPROFILE%\TsukiSynth.vst3`）已搬到 `E:\Tsuki-project\_backups\vst3_old_20261003_015305\`（附 `MOVED_FROM.txt`）。
- **還沒處理的**：（`%APPDATA%\VST3\TsukiSynth.vst3` 經 10-03 主 session 實查**不存在**——09-30 前就已不在，腳本預覽也顯示「無」，不是漏搬）；`(x86)\Common Files\VST3\` 裡有一個 `TsukiSynth.vst3.rar`；
  Cubase 外掛快取 `vst3plugins.xml` 還停在 08-22 → 要月月開 Cubase 重掃，之後 AI 可跑 `tools/cubase_scan_verify.py` 核對只出現一份。

### 1-5 仍開著、AI 可以接著做的後續卡（要不要開由月月決定）

> **WF1003 更新**：B2 做了但稽核 FAIL、已還原（要加 g 上限後重做）；C2 S4 已解釋（不用改程式）；Q09 量完維持 16（按引擎分大小待裁）；
> release CI 已重跑全綠；小項（`melody_verify` 加 `cli`、sustain 搬出 xfail、`crossplatform_verify` docstring、HostProbe Q05 亮燈路徑）已做；
> `.iss` 編譯仍卡在 Inno Setup 要月月本人裝（安裝模式對話框點「僅為我安裝」）。下面原文保留作 10-03 上午的狀態。

- **Body 層 B2 卡**：N1 之後 preset 11 把 Body 調回預設 0.5 仍約 +3.8 dBFS（Body 濾波器對準基頻，0.8 時 +15 dB）。B2＝響度正規化，需新的慣例常數（要月月裁）。
- **Q08 parity GATE**（外掛↔CLI 一致性）：現在只做了文案收窄；GATE 是後續 L 卡，容差要走 §6 登記。
- **C2 S4 +1.5 dB 調查**：FM 修法後合成測例「同音按著重打」大 1.5 dB，推測是相位抵消變少，沒證實。
- **`.iss` 編譯驗證**：`tools/installer/TsukiSynth.iss` 已加 64-bit 殼（N7），沒編譯過；Inno Setup 7.1.0 安裝檔在 `_tools\innosetup\`（sha 已核、沒安裝）。商業使用不是必須買（年營收 >US$5,000 才被請求，單人 US$155；`reports/wf1002b_innosetup_license.zh-TW.md`）。
- **Q09 voice pool**：現裁 D（主張域寫明 16 voice＋HostProbe 資訊性量測，月光舌鼓版實測被搶 64 次）；要不要加大 pool 沒裁。
- **重跑 `release-physics.yml`**（上一條）；HostProbe Q05 檢查在 preset 15 只剩「不亮」路徑（合成對照仍涵蓋「亮」）。
- 小項（`TODO.md`「AI 可做」）：`melody_verify.verify()` 加 `cli`、sustain 網格 0 拒量搬出 xfail、CLI 輸出路徑約 247 字元以上 exit 1、`crossplatform_verify.py:9-10` docstring 還寫 Linux/clang 等。

## 2. 這個專案是什麼

聾人使用者（月月）＋AI 不靠聽感、靠物理理論精確模擬聲音的 JUCE 8 VST3 合成器。**月月全程免耳驗收**：物理／位置正確性由 GATE 鏈負責，美學驗收交給外部聽人。
**唯一驗收依據 `ROADMAP_PHYSICS.md`**，§1 十條規則開工前必讀（R1 只認 GATE 輸出／R2 禁調寬容差／R3 禁縮 GATE／R4 禁未溯源常數／
R6 改**整個 `src/` 或 `CMakeLists.txt`** 必跑全套，外掛層另跑 ctest＋HostProbe（10-02 Q02、N8 擴大）／R7 見 §1-2／R10 渲染改變要前後對照）。
**X4 規約**：跑 ctest 前先重建五個測試 target（Audit／Tuner／PhysicsModels／SpectrumView／HostProbe）。
四個引擎：Cimbalom／Piano（弦）、Tongue Drum（梁）、Water Gong（板）、FM Piano（域外）。主張域寫在 `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md`（§1～§12）。

## 3. 各輪摘要（細節看 DEVLOG 與各輪 README）

| 輪 | 日期 | 一句話 | 入庫 |
|---|---|---|---|
| Phase D～I、B1～B6、C3-b 免耳三層 | 07-17～08-30 | 物理鏈第一原理化、驗證鏈、商品線開張 | 早已 merge `main`；`DEVLOG.md` |
| WF0907／0908／0909 | 09-07～09 | CI 全量 pytest、tail 自報、schema 單一真相、F-03 IR 庫、partial_verify、A14 B-2、D8 | 09-13 五 commit，09-14 merge |
| WF0914 | 09-14～16 | B7 Phase 0/1、D9c IR 補償、D12 state 遷移、D13～D15 | 09-25 七 commit |
| WF0925＋WF0925b | 09-25 | 13＋6 張卡、38 題裁決包、商品 v1.1 候選 | 09-30 八 commit＋push；`WF0925_README.md` |
| 09-30 | 09-30 | repo 搬到 E 槽、重建、pluginval／validator 08-06 後首次重驗、release CI 首跑全綠 | `d9aab66`、`b41298c` |
| WF1002 | 10-02 | 38 題落地（C1／C2／D／P／R／E 六 lane） | `2c4443e`～`804bf03`；`WF1002_README.md` §1、§3 |
| WF1002b | 10-02～03 | N1～N8 落地（T／C／R 三卡） | `59c0b06`～`168688e`；`WF1002_README.md` §4 |

## 4. 驗證鏈現況

```
MIDI 原譜 ──① score_vs_midi_verify──> score.json ──② melody_verify──> WAV
                                          │                            │
                                          └──③ verify_score (75 檔) ───┘
                                                                       │
        ④ HostProbe / ⑤ Cubase 實測 / ⑥ piano-roll 影片 / ⑦ stem_verify / ⑧ partial_verify ─┘
```

- ② `melody_verify`：onset ±10 ms、pitch ±5 c（10-02 Q04 已補登 §6）。量測器自證 ≤1 c 從未達成：持續段已知誤差 ≤1.18 c、放鍵段約 7.2 c（設計文件 §8.5；5 個 strict xfail 是刻意留的缺口標記）。
- ④ HostProbe **231 項**：H1～H8、D12 舊 state 遷移（10-02 加情境 4「檔案在但 >30 s」）、E14 版本、E16 27 個工廠 preset（峰值只印不判）、
  Q05 CLIP 燈（`OutputPeakMeter.h` 合成對照＋preset 15 真實輸出）、Q06 program 只給工廠 27 個、Q09 外掛搶音資訊性量測（不判定）。cwd 不限（找不到 repo 時設 `TSUKI_REPO_ROOT`）。
- ⑦ `stem_verify`：乾聲預設、串流化（905 事件峰值約 1.65 GB）。⑧ `partial_verify`：informational，**不可宣稱「泛音已驗證」**；期望值取第 0 根弦、3 弦平均約高 +5 c 已寫進工具說明（Q18＝A）。
- **D9c**：`kIrWetMakeupGain==26.9f` 守門（D9c-guard，改用 `EffectChain::irWetMakeupGain()`）＋10-02 起 |IR−ALGO| ≤0.25 dB 硬 CHECK（Q01）。
- **F5 殘差能量**：10-03 起用 4 項 Blackman-Harris 窗（N3＝A，修量法，−60 dB 門檻不動）；selftest 加帶外衰減假泛音反例。舊 Hann 數字只列不判。
- **CI 覆蓋**：每次 push 跑 ctest 4、全套 pytest、physics_verify selftest／t60／full、verify_score 6 首 smoke、三平台 CLI 渲染比對（阻斷式）、Windows ASAN、HostProbe。
  `release-physics.yml`（手動觸發）另跑 pluginval＋validator、corpus 75 首。**沒進 CI 的**：8/8 位元不變、75 首逐首雜湊比對、靜態 CRT 匯入檢查（CI log 看不到匯入表）。
- 外掛↔CLI：物理 GATE 驗的是 CLI 路徑；外掛即時演奏只共用衰減律，激發與效果鏈未逐項驗證（Q08 文案已收窄，GATE 未做）。

## 5. 裁決紀錄（摘要；原文在各裁決包）

- **WF0925 裁決包 38 題**（`reports/decision_packets/WF0925_open_decisions.zh-TW.md`）：10-02 以 Fable 評斷為準全部裁定，逐題落地方式見 `WF1002_README.md` §1。
  仍開著的只有：Q28（聽人）、Q22 授權 4 空格、Q32 E1／E3／E6／E7、Q24a 商品圖（等平台規格，官方查不到）。O01～O19 的狀態見 `TODO.md`。
- **追加裁決包 N1～N9**（`reports/decision_packets/WF1002_addendum_decisions.zh-TW.md`）：N1 B1、N2 A、N3 A、N4 甲、N5 A、N6 B、N7 A、N8 A、N9 A，全部已落地。
- **09-10～16 的裁決**（C10＝A、A14 B-2 放行、D8 wood_mallet、B7 路徑 C＋(a) 乙、D9＝(a)＋A、D11＝C、D13＝B、D15＝A'）：`DEVLOG.md` 09-10、09-15 段與各裁決包。
- **規劃者代決（月月 09-07 委託，可推翻）**：A13＝B+（只驗 partial 頻率）、A14＝引擎缺陷、F-03＝B＋三態、K-02＝C（另立 D9）、A8＝私下對照參考。依據在 `reports/decision_packets/` 同名檔。
- 兩封信（TU Berlin、Iowa MIS）09-15 已寄，還沒有回覆記錄。

## 6. 引擎缺口（D 類）現況

D9 關閉（D9c＋Q01 硬 CHECK）／D10 等付費牆文獻（擋 A14 B-1 與 D16 引擎修法）／D11 選 C，patch 存檔；10-02 R-b 查到候選並沒有比現行更像真鋼琴（高音真實 T60 長 2～9 倍），C5 已升格主張域 §12／
D12 關閉（Q10 載入失敗分支也改走三態）／D13、D14、D15 關閉／**D16 仍開放**：給愛麗絲全曲 16 顆弱基頻（力脈衝零點），Q15＝A 母帶不動、帶已知限制上架。
未編號：四季 string＋bow 有 5,682 顆落在同一種凹口（O03 建議登記新 D 項）。BeamModel ×2 已標 DECIDED CONVENTION（Q17＝A，主張域 §6）。

## 7. 環境

- repo `E:\Tsuki-project\tsuki-synth`（09-30 從舊位置 `C:\Users\admin\Desktop\Claude\tsuki-synth` 搬來，**舊路徑已不存在**；舊證據檔裡的 C 槽路徑或 `<OLD_REPO>` 都指這裡）。
- 工具 `E:\Tsuki-project\_tools\`：`pluginval\extracted\pluginval.exe`（1.0.4）、`vst3sdk-build\bin\Release\validator.exe`、`innosetup\`（7.1.0，沒安裝）、`vst_logo\`、`papers\`（York 碩論等，不進 repo）、`deploy\`。
- 私人檔 `E:\Tsuki-project\_private\`（變現計畫、JUCE 詢問信草稿、收入記帳表；不在公開 repo）；舊 VST3 備份 `E:\Tsuki-project\_backups\`。
- **暫存已清**：`output/wf0925/`、`wf0925b/`、`wf0930/`、`wf1002/`、`wf1002b/`、`E:\Tsuki-project\_scratch\`、`E:\tsuki_wf0925_V1\` 都已移到資源回收筒（目前不存在；回收筒要月月自己清空）。
  證據檔裡寫到這些路徑（或 `<SCRATCH>`）的原始 log、`hash75.py`、`sanitize.py` 等腳本已不在；進版控的摘要和 `reports/gate_outputs/*_raw/` 仍在。`output/wf0907`～`wf0914*` 還留著。
- `build\`（整合用，CMakeCache 已是 E 槽路徑）與 `build-wf\`（C++ lane 用）都在。C 槽 10-03 剩約 63 GB。

## 8. 檔案地圖

| 要找什麼 | 去哪 |
|---|---|
| 待辦勾選清單 | `TODO.md` 開頭（10-03 快照＋「仍開著」） |
| 最新裁定表、各卡結果 | `docs/workcards/WF1002_README.md`（§1 裁定表、§3 WF1002、§4 WF1002b） |
| 裁決包 | `reports/decision_packets/WF0925_open_decisions.zh-TW.md`（38 題＋O01～O19）、`WF1002_addendum_decisions.zh-TW.md`（N1～N9＋上架清單）；更早的 A13／A14／F03／K02／C10／D8／B7／D9／D11／D13 同資料夾 |
| WF1002 研究報告 | `reports/wf1002_preset_overshoot_root_cause.zh-TW.md`（Q05 爆音根因）、`wf1002_fm_envelope_fix_before_after.zh-TW.md`＋`.patch`（FM 殭屍 voice）、`wf1002_d11_piano_t60_literature_and_f5_method.zh-TW.md`（D11 文獻＋F5 量法） |
| WF1002b 報告 | `reports/wf1002b_n1_compressor_makeup_before_after.zh-TW.md`（N1 27 個 preset 前後）、`wf1002b_booth_image_specs.zh-TW.md`、`wf1002b_innosetup_license.zh-TW.md` |
| GATE 證據 | `reports/gate_outputs/wf1002_*`（C1／C2／D／P／R、DPR 稽核、`wf1002_INTEGRATION.txt`＋`_raw/`）、`wf1002b_*`（T／C／R、稽核、`wf1002b_INTEGRATION.txt`＋`_raw/`、`wf1002b_R_ci_run.txt`）、`wf0930_*`（搬家後重建、pluginval、release CI 首跑）；更早各輪 `wf09*_*` |
| 流程規約 | `docs/workcards/WF0907_README.md`、`WF0914_README.md`、`WF0925_README.md`（§7-8 是 WF0925b 留下的小項）、`WF1002_README.md` §2 lane 表 |
| 主張域與已知限制 | `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md`（§1～§12）、`docs/KNOWN_LIMITS_INDEX.zh-TW.md`、`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §7～§10 |
| UI 設計輸入 | `docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md` v1.2（10-02 補記：§4.14 CLIP 燈、§5-3 缺檔／無法載入警告定案） |
| 發行與授權 | `THIRD_PARTY_NOTICES.txt`、`LICENSE`、`docs/legal/JUCE8_LICENSE_REVIEW.zh-TW.md`、`docs/legal/EULA_BUYER_DRAFT.md`、`tools/installer/`（`.iss`，沒編譯過） |
| 商品 | `exports/products/clean_batch2_v1_1_candidate/`（gitignored；入口 `CHANGES_v1_1.md`，含 WF1002 套裁定那段）；原版 `clean_batch2/` 沒動；`moonlight_batch1/` 換源前不上架 |
| 09-25 現況盤點 | `reports/status_check_2026-09-25/`（Q34d＝A，10-02 隨 `0c4abb1` 進版控） |
| 歷史決策 | `DEVLOG.md` |

## 9. 操作備忘

- 建置：`cmake -B build -DCMAKE_BUILD_TYPE=Release -DTSUKI_BUILD_TESTS=ON`，再 `cmake --build build --config Release --target TsukiSynthCLI TsukiSynth_Standalone TsukiSynth_VST3`
  ＋五個測試 target（`TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest TsukiSynthSpectrumViewTest TsukiSynthHostProbe`）。CLI 在 `build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`。
- **整合卡全套順序**（WF1002b 實跑）：重建 → dumpbin 匯入檢查（MSVCP／VCRUNTIME／api-ms-win-crt 要 0）→ `ctest --test-dir build -C Release`（4/4；另直接跑 AuditTest 看 111 PASS）
  → `python -m pytest tests -q`（310）→ `python tools/physics_verify.py --full --cli <CLI>`（NO CHECKED FAILURES）與 `--selftest`（14/14）
  → `python tools/verify_score.py --all --cli <CLI>`（75/75）→ **75 首雜湊逐首比對** → 位元不變 8/8 → HostProbe（231/0）→ `tools/validate_plugin.ps1`（pluginval strictness 10＋validator 47/47）。
- **75 首逐首雜湊比對（整合卡標準步驟）**：從 `verify_score --all` 的 log 抽每首 score 的 `determinism.sha256_match` 雜湊，跟上一張整合卡逐首比；
  現行參考是 `reports/gate_outputs/wf1002b_integration_raw/12_hash75_vs_wf1002_integration.txt` 的逐首表（WF1002b 用的 `hash75.py` 放在 output/，已隨暫存清掉，下次要重寫）。
- 位元不變：`python reports/gate_outputs/wf0907_method/render_wf_scores.py --label <名稱> --workdir <repo 外的短路徑> --cli <CLI> [--outdir <資料夾>]`，
  產出的 `sha256_<名稱>.txt` 用 `diff --strip-trailing-cr` 對 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`（`post_d8` 只留存檔，拿它比會讓 physical_piano 假紅燈）。
- **做 GATE 一律帶 `--cli <路徑>`**，再看 log 裡 manifest 的 renderer 欄位對不對（現行 `f99b4a8096f9`）。`--workdir` 要短：CLI 輸出路徑約 247 字元以上會寫不出 manifest、exit 1。
- HostProbe：`build/Release/TsukiSynthHostProbe.exe <.vst3> <outdir>`；會在 `%APPDATA%\TsukiSynth\Presets`、`\IR` 建檔再自己刪（O09）。
- 外掛驗證：`pwsh -NoProfile -File tools/validate_plugin.ps1 -Plugin <VST3> -Pluginval E:\Tsuki-project\_tools\pluginval\extracted\pluginval.exe -Vst3Validator E:\Tsuki-project\_tools\vst3sdk-build\bin\Release\validator.exe -Strictness 10`。
- 分軌／partial：`python tools/stem_verify.py <score> [--limit N] [--jobs N] [--json out] [--cli <CLI>]`；`python tools/partial_verify.py <stem 報告.json> [--cli <CLI>]`。
- 量測器自證：`python tools/measurement_selfcal.py [--holdout]`（現況 exit 1：開發 5.2304 c、hold-out 7.2055 c，主張域見設計文件 §8.5）。
- 商品母帶的渲染器：`exports/renderer_archive/TsukiSynthCLI_9123db8f_build20260915.exe`，repo 外另一份 `E:\TsukiSynth_renderer_archive\`（`SHA256SUMS.txt` 是 repo 相對路徑，在 E 槽要手動比）。
- ffmpeg：`%USERPROFILE%\Desktop\Tools\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe`（`melody_roll_video.py` 找法：`--ffmpeg` > `TSUKI_FFMPEG` > PATH > 這個路徑）。
- Python：本機 3.13.3（CI 固定 3.12.8）。

## 10. 外部工具（09-14 評估，簡記）

Limbus Spatial Stage 0.9.0（視覺化空間混音，對聾人友善）與 Yamaha Piano Sheet Converter β（只限私人、不可當驗證證據或用於換源）09-14 已安裝；Limbus 有沒有用金鑰啟用磁碟上查不出來。
Orra Deverb、Klanggeist 可有可無。`Downloads\不知道有沒有用` 的 Yamaha 解壓殘留 467.9 MiB 10-02 已移到回收筒（Q36a），剩安裝檔與 Klanggeist。

## 11. 工作方式教訓

- **規劃者畫地圖、Sonnet 工兵、Opus 稽核親自重跑**，不要跳過稽核層；稽核判定要寫進進版控的 `wf<輪>_<卡>_audit.txt`。
- **跨 lane 污染**：同一工作樹並行時，全套 pytest 放整合卡。卡文跟 repo 內更新的查證矛盾時停下回報。
- **合成哨兵的盲點**：哨兵語料若跟候選估計器同模型，會套套邏輯地全過；要加「期望值固定、真值偏離」與真實音檔兩條軸。
- **75 首逐首雜湊比對是整合卡標準步驟**（WF1002b 起）：8 首位元基準裡沒有開 overdrive 的譜，只有逐首比 75 首才抓得到 N9 那種「基準外」的位元變化。
- **R10 抓到靜態 CRT 的位元變化**：Q07 改靜態 CRT 後 `std::tanh` 最後一位元不同，2 首 overdrive 譜（akashic_transition_var01、restraint_loop_001）變 2 LSB@24-bit（約 −132 dB）；
  整合卡用對照建置（同一份原始碼只把 CMake 改回動態 CRT，雜湊回到舊值）證明是 Q07 造成，交月月裁（N9＝A）。改建置設定也要當渲染變更看。
- **`rm -rf` 誤刪事故（10-02）**：P lane `rm -rf output/wf1002` 路徑多刪一層，把 C2、R 第一輪暫存整個刪掉（主 repo 與 `libs/JUCE` 完好，C2、R 全部重跑）。
  之後：隔離副本一律放 repo 外；**不要在 `output/` 下建 junction**；刪資料夾前先確認確切路徑、不要對可能含 junction 的資料夾直接 `rm -rf`。
- **junction 安全拆法**：建立用 `cmd /c mklink /J <連結> <目標>`；拆除用 `cmd /c rmdir <連結>`（**不加 /s**，只拆連結、不穿過去），再用 `dir /AL /S` 確認沒有殘留的 reparse point，最後才刪外層資料夾。
- **路徑跳脫**：用 Python／sed 寫 Windows 路徑時 `\t` 會變成 tab（10-02 出過事，`168688e` 修正）；寫完用 `grep -c $'\t' <檔>` 確認是 0，或改用正斜線。
- **多檔 commit 用路徑清單時先去掉 CR**：`tr -d '\r' < list.txt > list_lf.txt && git commit --pathspec-from-file=list_lf.txt -F msg.txt`（Windows 寫的清單帶 CR，git 會認不出檔名）。
- Windows 260 字元路徑上限會讓 CLI 寫不出 manifest：`--workdir` 一律短路徑。
- session limit 中斷時，接手工兵先核對前任的 diff 與產出再重跑 GATE。
- 月月的偏好不變：不腦補、查不到就說查不到、需要裁決就做成看數字就能選的裁決包、白話到位。
