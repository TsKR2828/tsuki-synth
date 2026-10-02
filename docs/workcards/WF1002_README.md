# WF1002 裁決落地輪（2026-10-02）

> 月月 2026-10-02 裁決：**「照 Fable 的說法做」**＝`reports/decision_packets/WF0925_open_decisions.zh-TW.md` 38 題，
> 以 Fable 5 第三方評斷（09-30）為最終版：**包內「建議」全採，但改 4 題**——
> Q05＝C＋根因調查卡、Q09b＝A、Q22c＝B＋聯絡例外、Q20b＝B。Q17 依 BR 數字收斂為 A。
> 流程沿用 `WF0907_README.md`、`WF0914_README.md`、`WF0925_README.md`（R1–R10、稽核 PASS 才 add）。
> repo 已搬到 `E:\Tsuki-project\tsuki-synth`；工具在 `E:\Tsuki-project\_tools`（pluginval、vst3sdk-build、innosetup、vst_logo）。

## 1. 最終裁定表（本輪的唯一依據）

| 題 | 裁定 | 落地方式 | lane |
|---|---|---|---|
| Q01 | B | audit_repro 加 CHECK：合成 IR 的 \|IR−ALGO\| ≤ 0.25 dB；0.25 dB 登記進 ROADMAP §6（出處：WF0914-D9c 施工卡 §2.2、D9b 展幅 0.24 dB；月月 10-02 核准） | C1、D |
| Q01b | B | `EffectChain.h` 開 public 唯讀存取點，D9c-guard 改用它（拿掉顯式實例化繞路） | C1 |
| Q02 | A | R6 擴成整個 `src/`＋`CMakeLists.txt`；外掛層另規定 ctest（先重建五測試 target）＋HostProbe 必跑 | D |
| Q03 | A | R7 改字面：「不 commit、不 push（月月明示裁決時除外）；稽核 PASS 後由稽核 `git add`（staged）供月月審」 | D |
| Q04 | A | §6 補登 melody_verify onset ±10 ms、量測器自證 1.0 c；兩處 ±5 c 註明沿用 f0 列 | D |
| Q05 | **C＋根因卡**（Fable） | 外掛畫面加削波指示燈（不改聲音）＋手冊/UI 規格註明；**另開唯讀根因調查卡**：preset 7/11/15 單音為何超過 0 dBFS（懷疑 B6 校準慣例錨定） | C1、R |
| Q05b | A | 不加峰值/靜音門檻 | — |
| Q06 | A | `getNumPrograms()` 只回工廠 27 個；使用者 preset 只在外掛自己選單；HostProbe H7＋pluginval Plugin programs 測項要過 | C1 |
| Q07 | A | `CMAKE_MSVC_RUNTIME_LIBRARY` 靜態 CRT；三支執行檔一起換；**必須 8/8 位元不變，CLI 渲染一變就停（R10）** | C1 |
| Q08 | C | 現在做 B：文案與主張域收窄（「物理驗證涵蓋 CLI 渲染；外掛即時演奏共用衰減律，激發與效果鏈未逐項驗證」）；parity GATE 排進 TODO 當後續 L 卡 | D、P |
| Q09 | D | B（主張域寫明 16 voice、JUCE 搶音與同音規則、GATE 只涵蓋 CLI）＋HostProbe 加「外掛串流演奏同一份 MIDI、跟 CLI 逐事件比被搶的音」的**資訊性量測**（不設門檻） | C1、D |
| Q09b | **A**（Fable） | 修 FM `Envelope::noteOff()` 對已在 Release 的 voice 重算——**R10：在隔離副本做前後對照報告＋patch，不直接落地** | C2 |
| Q09c | B | 同音提前制音寫進主張域 | D |
| Q10 | B | IR 載入失敗分支改走缺檔三態（警告附原因、保留原檔名）；情境 3 也清舊鍵；HostProbe 補「檔案存在但 >30 s」情境 | C1 |
| Q11 | C | 不動 | — |
| Q12 | A | 已完成（physics.yml＋release 首跑實戰驗證） | — |
| Q13 | A | label 改 `ubuntu-24.04-gcc`；`crossplatform_tolerance.json` 的 `_basis` 文字改 GCC 13.3（**數值不動**）；上傳/比對檔名同步 | D |
| Q14 | C | 已完成（本機＋release 首跑） | — |
| Q15 | A | 母帶不動；已知限制文字已在 v1.1 候選；16 顆時間點交聽人（Q28） | — |
| Q16 | D | TODO 登記「F5 PASS 依賴探針 0.8 mm」為已知脆弱點；**研究卡**：真鋼琴 T60 文獻對照候選＋F5 量法可改方向（只研究） | R、HO |
| Q17 | A（BR 數字收斂） | 保留 ×2；`BeamModel.h` 註解與主張域改標「DECIDED CONVENTION，經驗係數，無文獻錨點」（純註解，8/8 不變） | C1、D |
| Q18 | A | `partial_verify` 的工具說明（--help/docstring）寫明期望值取第 0 根弦、3 弦平均約高 +5 c | D |
| Q18b | B | 只記錄 | — |
| Q19 | C | C1～C4、C7、C8 甲；C6 甲（Q17=A）、C9 甲（Q09 含 B）；C5 等 Q16 研究卡 | D |
| Q20 | A | 現行全部 −1 dBTP | — |
| Q20b | **B**（Fable） | 不重出；文案維持 XF 的三量測器實測範圍寫法 | — |
| Q21 | A | 採用「AI 輔助編寫譜面，由 TsukiSynth 物理引擎演奏；未使用 AI 音訊生成」，拿掉【待月月確認】 | P |
| Q22 | A | 採用草稿架構；Q22b A、**Q22c B＋聯絡例外**（「如需 Content ID 授權請個案聯絡」）、Q22d A（英文為準）；[TBD]（通路清單、終止後作品、準據法、聯絡方式）仍待月月填 | P |
| Q23 | B | 先不上 Fab | P |
| Q24 | a C、b A | 商品圖等平台規格；試聽帶採用完整版 | P |
| Q25 | A | 全曲版放進專輯 | P |
| Q26 | A | loop 兩版都附 | P |
| Q27 | A | 音樂換 TPDF dither 版 | P |
| Q28 | A 或 C | **待月月**（認識聽人＝C） | — |
| Q29 | B | 商品名只寫 TsukiSynth；內文另行寫相容格式＋VST® 首次出現＋聲明句＋logo | P |
| Q30 | A | Windows 64-bit only | P |
| Q31 | B | 照 A 記帳；寫信給 sales@juce.com **由月月自己寄**（AI 擬稿） | E |
| Q32 | E2 甲、E4 乙、E5 照平台、E8 英、E9 無 | E1／E3／E6／E7 **待月月** | P |
| Q33 | A | commit＋push branch（本輪收尾照做） | — |
| Q34 | a A、b A、c A、d A | 變現計畫移到 repo 外 `E:\Tsuki-project\_private\`；盤點資料夾進版控 | E |
| Q35 | A | 新 build 部署＋三份舊副本加時間戳**搬**到 E:（不刪）；AI 寫腳本，**月月用管理員執行** | E |
| Q36 | a A、b A | 移到資源回收筒（AI 只移、不清空）；**不動** `exports/renderer_archive`、`E:\TsukiSynth_renderer_archive` | E |
| Q37 | 1Y 2N 3Y 4Y | 1、3 已下載；4 論文試抓到 `E:\Tsuki-project\_tools\papers\`（不進 repo） | E |
| Q38 | A | 缺檔警告改 UI 規格 v1.2 文字；F-03 施工卡那格加註日期與理由 | C1、D |

仍開著、本輪不動：Q28、Q32 的 E1/E3/E6/E7、Q22 的 [TBD]、Q24a、Inno Setup 商業授權、`.iss` 64-bit 殼。

## 2. lane 與檔案邊界

| lane | 範圍 | 建置 |
|---|---|---|
| C1（C++） | `src/`、`tests/*.cpp`、`CMakeLists.txt` | `build-wf\`（先重新 configure：快取還指 C 槽） |
| C2（R10 前後對照） | 隔離副本；只產出 `reports/` 報告＋patch | 副本自己的 build |
| D（規則與主張域文件） | `ROADMAP_PHYSICS.md`（§1 R6/R7、§6 本輪授權修改）、`docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md`、`docs/KNOWN_LIMITS_INDEX.zh-TW.md`、`.github/workflows/physics.yml`（只 Q13）、`scores/crossplatform_tolerance.json`（只 `_basis` 文字）、`tools/partial_verify.py`（只說明文字）、`docs/workcards/WF0908_P3_f03_ir_library.md`（只加註）、`docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md` | 不建置 |
| P（商品） | `exports/products/clean_batch2_v1_1_candidate/` | 不建置 |
| R（唯讀研究） | 新報告檔 | 用 `build\` 現成 exe 的複本 |
| E（環境，主 session） | repo 外檔案、回收筒、部署腳本 | — |
| INT／HO | 整合重建 `build\`、全套 GATE＋pluginval＋validator；交接文件 | `build\` |

## 3. 本輪結果與後續裁決（2026-10-02）

- 各 lane 稽核：C1 PASS（重建全套、反例有牙齒、舊 VST3 測出 7 條 FAIL）、C2 PASS（patch 未落地）、D PASS（三輪：D-1 xfail 條數、D-2 裁決原句、D-3 CLI 殘響事實）、P PASS、R PASS、追加裁決包 PASS（A-1 撤回「BOOTH 直接用草稿」）。
- 整合卡（`reports/gate_outputs/wf1002_INTEGRATION.txt`）：ctest 4/4（AuditTest 111）、pytest 307、`--full` 無失敗、selftest 13/13、75/75、8/8、HostProbe 231/0、pluginval＋validator 47/47 全過；三支執行檔不再依賴 VC++ runtime。
  **R10 觸發**：靜態 CRT 讓 2 首 overdrive 譜最後一位元改變（−132 dB）→ 月月 10-02 裁 **N9＝A 接受**。
- 事故：P lane 誤 `rm -rf output/wf1002` 刪掉 C2 與 R 第一輪暫存（主 repo、libs/JUCE 完好；C2、R 全部重跑）。之後所有隔離副本改放 repo 外 `E:\Tsuki-project\_scratch\`，junction 用完即以非遞迴方式拆除（目前 `E:\Tsuki-project` 下 0 個）。
- 月月 10-02 再裁：追加裁決包 **N1～N8 全照建議**（N1 B1 拿掉壓縮器固定補償、N2 A 落地 FM 修法、N3 A F5 改換窗量法、N4 甲 C5 升格、N5 A、N6 B、N7 A、N8 A）→ 下一輪 WF1002b 實作。
- lane E（主 session）：變現計畫移到 `E:\Tsuki-project\_private\`；Downloads 殘留 467.9 MiB 移到資源回收筒；York 碩論下載到 `_tools\papers\`（ICSV27 被擋）；JUCE 詢問信草稿＋收入記帳表；部署腳本 `E:\Tsuki-project\_tools\deploy\deploy_tsukisynth.ps1`（預覽過，待月月管理員執行）。

## 4. WF1002b（2026-10-02，實作追加裁決 N1～N8）

| 卡 | 內容 | 稽核 |
|---|---|---|
| T | N3：F5 窗 Hann→4 項 Blackman-Harris（±3% 帶、時段、−60 dB 不動），selftest 加帶外衰減假泛音反例（13→14 項）；piano F5 −63.9→−87.4 dB、1.0 mm 探針 −59.47→−82.73 dB（「依賴 0.8 mm」脆弱點解除）。N4：ENGINE_DOMAIN_CLAIMS §12（C5 升格）。N5：UI 規格 §5-3 加「無法載入」定案文字、§4.14 CLIP 燈實作。N8：R6 外掛層清單補 6 項 | PASS（四種故意改壞的版本新反例都會 FAIL） |
| C | N2：套 FM 殭屍 voice patch（`Envelope.h`）。N1：拿掉壓縮器固定 makeup（`Compressor.h`）——27 個工廠 preset 各降 2.00～7.50 dB（與 R-a 預測差 ≤0.01 dB），無 preset 超過 0 dBFS，最大 −1.85 dBFS；CLI 不經過（ratio=1 早退）。N7：`.iss` 加 `SetupArchitecture=x64`、最低版本 7.0.0（未編譯） | PASS（clean rebuild 重跑全套；75 首 hash 逐首相同） |
| R | N6：Inno Setup 商業使用「not strictly required」，官方請年營收 >US$5,000 者購買（單人 US$155）。Q24a：BOOTH 單檔 1.2 GB／全店 10 GB，音效包 78 MB、專輯 99 MB 皆符合；商品圖官方規格查不到（觀察：顯示長邊 1024 px、縮圖中央裁正方形）。CI run 37017182460（804bf03）六 job 全綠，Linux 改名 gcc 首次實戰通過 | PASS |

注意（N1 副作用）：使用者自己存過、開了壓縮器的舊 DAW 專案與 preset，重開後也會變小聲（最多 19 dB，旋鈕極端值時）。
仍開著：Body 層結構問題（preset 11 Body 0.5 約 +3.8 dBFS，B2 另開卡）；C2 S4 測例 +1.5 dB 未解釋；HostProbe Q05 檢查在 preset 15 改成只驗「不亮」路徑（合成對照仍涵蓋「亮」）。

整合卡（`reports/gate_outputs/wf1002b_INTEGRATION.txt`）重建 `build\` 全綠：ctest 4/4（AuditTest 111）、pytest **310**（304＋1 skip＋5 xfail）、`--full` 無失敗、selftest 14/14、75/75、**75 首 hash 逐首與 WF1002 整合卡相同**、8/8、HostProbe 231/0（E16 最大 −1.85 dBFS）、pluginval＋validator 47/47。新 VST3 sha256 `fa13ac17…`；三支執行檔不依賴 VC++ runtime。

---

## 5. 2026-10-03 更新註記（文件卡 DOC-B；上面 §1～§4 原文不改）

- **git**：WF1002 與 WF1002b 的成果已經月月明示 commit＋push（`2c4443e`、`cdfc0d6`、`0c4abb1`、`9c46633`、`804bf03`；`59c0b06`、`5919579`、`c49c727`、`168688e`）。分支 HEAD `168688e`，`main` 仍 `3f9b90a`，未 merge。
- **§1 表後「仍開著、本輪不動」的更新**：`.iss` 64-bit 殼已由 N7 落地（仍未編譯）；Inno Setup 商業授權已由 N6 查清（不是必須買，年營收超過 US$5,000 才被官方請求購買）；Q24a 的 BOOTH 規格已查（檔案上限符合、商品圖官方規格查不到），草稿能不能用仍待月月。Q28、Q32 的 E1／E3／E6／E7、Q22 的 [TBD] 仍開著。
- **§3 lane E 部署（Q35）**：部署腳本已於 2026-10-03 01:53 執行——標準位置 `C:\Program Files\Common Files\VST3\TsukiSynth.vst3` 的外掛本體 sha256 `fa13ac17…`（＝WF1002b 整合卡的 `build\`），三份舊副本搬到 `E:\Tsuki-project\_backups\vst3_old_20261003_015305\`（只搬、不刪）；`%APPDATA%\VST3` 那份實查已不存在。剩 Cubase 重新掃描外掛。
- **暫存清理（Q36b）**：WF0925～WF1002b 各輪在 `output/` 下的暫存資料夾與 `E:\Tsuki-project\_scratch` 已清；`exports/renderer_archive/` 與 repo 外的渲染器備份照裁定不動。
- **§4 之後仍開著**：外掛 Body 層結構問題（preset 11 Body 0.5 約 +3.8 dBFS）；FM 修法 C2 S4 測例 +1.5 dB 未解釋；HostProbe Q05 在 preset 15 只驗「不亮」路徑；plugin↔CLI parity GATE（Q08 後續 L 卡）；merge `main`。
- 文件同步：README、ROADMAP、ROADMAP_PHYSICS（檔尾「2026-10-03 狀態」，§1 規則原文與 §6 數值未改）、兩份裁決包的逐題落地行、ENGINE_DOMAIN_CLAIMS／KNOWN_LIMITS_INDEX 的狀態補記（主張原句未改；`TODO.md` 行號引用改成條目名稱）。
