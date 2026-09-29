# TsukiSynth 交接文件

> 交接視窗：**2026-09-25（WF0925 輪＋WF0925b 收尾輪完工）**　分支：`fix/deep-physics-audit-20260716`
> origin 上是 `766d21d`（`main`=`3f9b90a`，09-15 merge，CI 三平台全綠）。
> 本機 HEAD `18430c4`：**WF0914 成果 09-25 已依月月裁決分 7 個 commit（`a09058c`～`18430c4`），未 push**。
> **WF0925＋WF0925b 成果 staged、未 commit**（R7；**239 檔**＝WF0925 154＋WF0925b 85；月月看 `git diff --cached`）。
> **2026-09-30 追記**：月月已把 repo 從 `C:\Users\admin\Desktop\Claude\tsuki-synth` 搬到 **`E:\Tsuki-project\tsuki-synth`**（舊文件與證據檔裡的 C 槽路徑都指這裡）；`build\`、`build-wf\` 的 CMakeCache 仍記舊路徑，下次建置前要重新 `cmake -B`。同日月月裁決 Q33＝A：WF0925＋WF0925b 依 `docs/workcards/WF0925_README.md` §7-6 切 8 個 commit 並 push branch（不 merge main）；Q14＝C、Q37 1/3/4＝Y（同意下載 pluginval／VST3 SDK／Inno Setup／VST logo）。
> **新 session 請先讀完這一頁再動手。** WF0925 與 WF0925b 的逐卡結果、證據路徑、稽核判定在 `docs/workcards/WF0925_README.md`（WF0925b 在 §7）；
> 等月月拍板的事集中在 `reports/decision_packets/WF0925_open_decisions.zh-TW.md`（**38 題 Q01–Q38**＋其他待裁 O01–O19，每題回一個字母；各題下「2026-09-25 WF0925b」那一行是收尾輪的處理結果）。
> 09-25 現況盤點在 `reports/status_check_2026-09-25/`（結論 `STATUS_CHECK.zh-TW.md`、逐條證據 `APPENDIX_findings.zh-TW.md`）；各輪快照在 `TODO.md` 開頭；歷史決策在 `DEVLOG.md`；
> 流程規約 `docs/workcards/WF0925_README.md`（沿用 `WF0914_README.md`、`WF0907_README.md`）。

---

## 0. 一句話現況

**WF0914 輪（09-14～16）的成果 09-25 已分 7 個 commit 入庫（未 push）。同一天照月月 09-25 裁決「剩下 AI 能處理的都處理掉」，接著跑了 WF0925 輪（13 張卡）和 WF0925b 收尾輪（6 張卡）：
所有 lane 稽核 PASS——WF0925 商品 lane 那 1 條 FAIL 已由 WF0925b-XF 修好、複驗 PASS；成果全部 staged 未 commit（239 檔）。
WF0925b 整合卡全套 GATE 全綠，現行基線：pytest **307 個測試**（301 passed＋1 skip＋5 xfail）、HostProbe 215 項、AuditTest 110 條 PASS；位元不變 8/8，兩輪都沒有任何渲染輸出改變。
不改 `src/` 就能做的事都做了；要月月拍板的整理成 38 題裁決包，AI 還能接著做、但要改 `src/` 或屬小修的，列在 `WF0925_README.md` §7-8。**

## 1. 立刻要知道的五件事

1. **git 狀態**
   - origin：分支 `766d21d`、`main`=`3f9b90a`（09-15 push＋merge），CI 三平台全綠（MSVC／GCC 13.3／AppleClang；Linux leg 的 label 寫 clang，實際是 GCC，裁決包 Q13）。
   - 本機 HEAD `18430c4`，比 origin 多 7 個 commit，**未 push**：
     `a09058c` B7P1 引擎純函式／`f1b2448` D12 state 遷移／`fafb96c` D9c IR 補償／`2d04e1e` D14＋D15 驗證工具／`5b087a9` 研究文件與裁決包／`d3ac52b` 施工卡＋GATE 證據／`18430c4` 交接文件（含 09-25 文件修正）。清單在 `reports/status_check_2026-09-25/commit_lists/`。
   - **staged 239 檔、未 commit**：WF0925 的 154 檔（C++ 34＋Python／CI 15＋研究 75＋整合 24＋交接 6）＋WF0925b 新進 85 檔（TF 11、DS 8、BR 26、DS／BR 稽核 1、X1／X2 證據 15、XF 證據 9、INT2 15）；另有 10 個 WF0925 檔被 WF0925b 再改過（TF 6、DS 4，都已重新 stage）。
     建議的 commit 切法（8 列、239 檔，逐列 pathspec 已核對不重疊、不漏）在 `docs/workcards/WF0925_README.md` **§7-6**（裁決包 Q33；§4 那張是 WF0925 當時的，檔數已不對）。
   - **沒 stage 的**（untracked）只剩兩項：盤點資料夾 `reports/status_check_2026-09-25/`、`docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md`（含售價，repo 是 PUBLIC），都等 Q34。
2. **WF0925 各卡結果**（逐卡細節與證據路徑見 `WF0925_README.md` §2；WF0925b 在下面第 2b 點）：

| 卡 | 一句話 | 稽核 |
|---|---|---|
| K1 | E8 音訊執行緒不再逐音建字串、E9 tail 改讀 Timer 算好的值、E14 `state_version=3`、E15 IR 庫雜湊不符時原子修復＋SHA-256 已知答案測試、D12 斷言、B7／D13／D9c 註解同步 | PASS（第 2 輪） |
| K2 | HostProbe 不再依賴 cwd（cwd → `TSUKI_REPO_ROOT` → exe 往上找）、D9c-guard（`kIrWetMakeupGain == 26.9f`）、E16 27 個工廠 preset 逐一檢查（109 條） | PASS（第 2 輪） |
| K1K2fix | 更正 K1 的 GATE 4 證據（當時 `--cli` 空白、實際測到舊 CLI），用 `build-wf` 重跑六條 GATE | PASS（第 2 輪） |
| P1 | release CI 補建置清單＋改 pytest＋加 HostProbe 步驟；每次 push 的 CI 也加 HostProbe；D15 pin 改非 xfail；`render_wf_scores.py --outdir`；`find_cli` 優先挑 Release；新增 17 個 stem 串流測試 | PASS（另查到既有的 CI exit code 遮蔽問題 → Q12） |
| N1 | D16 零點地圖：16 顆 FAIL 全在力脈衝凹口內；商品只有給愛麗絲鋼琴版受影響 | PASS |
| F5 | D11-F5 根因：F5 退化全部來自 C4 基頻 T60 變短（4.14→2.67 s）造成的窗洩漏；現行 PASS 靠探針預設弦徑 0.8 mm | PASS |
| V1 | partial_verify 第一次跑全曲 905 顆（informational）；外掛 16 voice 搶音推算：正常彈法 50 件商品都不超過 | PASS |
| L1 | D1 梁／板阻尼文獻：反對把 BeamModel ×2 當物理項、但無法判斷總量；模型不看舌片厚度；D6 取得、D4 仍拿不到 | PASS |
| G1 | THIRD_PARTY_NOTICES、LICENSE 第三方段落、JUCE 8 授權審查、買家 EULA 草稿、安裝包腳本（沒編譯過）、已知限制索引 | PASS |
| X1 | loop-ready 6 檔、音效響度 B 案 43 檔、音樂 TPDF 版、試聽帶、商品圖（全在 `exports/products/clean_batch2_v1_1_candidate/`） | FAIL（1 條要修）→ **WF0925b-XF 修正後 PASS** |
| X2 | v1.1 候選文案、catalog、三語 README、授權 v1.1 草稿、Fab 版、試聽包與 22 題答題卷；`x2_verify` 86/86 | 同上 |
| Q1 | 彙總裁決包：37 題＋O01–O19，附錄逐條歸檔 108 條 open_items（WF0925b 後補 Q38） | — |
| INT | 10 條 GATE 全綠（見第 3 點） | — |

   WF0925 商品稽核那 1 條要修的（README 寫 loop-ready 檔「跟原版每 N 小節重播逐樣本相同」說得太滿）已在 WF0925b-XF 修好，見下面第 2b 點。

2b. **WF0925b 收尾輪各卡結果**（2026-09-25 同日；不改 `src/`、不建置 plugin；逐卡細節見 `WF0925_README.md` §7）：

| 卡 | 一句話 | 稽核 |
|---|---|---|
| TF | **Q12 先照建議 A 做（可推翻）**：兩支 workflow 每個多行 pwsh 區塊逐行檢查 exit code、HostProbe 移到 job 最後；本機照 runner 包法模擬「只讓一個指令失敗」，被蓋掉的情境 12 → 0。**O16 六項 tools 小修**：find_cli 不看 mtime、stem_verify 讀 EXTENSIBLE、`render_wf_scores.py --cli` 可用相對路徑、stem_verify／partial_verify 加 `--cli`、partial_verify caveats 改成現況、release 網格 0 拒量搬出 xfail。pytest +19 | PASS |
| DS | `WF0925_README.md` §6 的文件同步：EARFREE §8 換成 A14 後的數字（677／16／212 等）、ENGINE_DOMAIN_CLAIMS、WOOD Table 5–15、ROADMAP 13 條落地狀態（§1、§6 原文不動、原 483 行不位移）、兩封信標題、wf0914 勘誤、D9 裁決包 E18 | PASS |
| BR | **Q17 的「先算數字」**：隔離副本只刪 `BeamModel.h:54` 的 `* 2.0f`，比前後。鋼基頻 T60 變長 1.15～1.80 倍（C4 16.39→26.86 s）；corpus 39 份會變、36 份不變；8 首基準變 3 首；商品 50 件變 36 件；文獻 7 點現行 0、拿掉 ×2 1 點落在範圍內。報告沒替月月選 | PASS |
| XF | **商品稽核 FAIL 修正輪**：README loop 說法照實改、秒數只捨入一次、真峰值寫成三支量測器範圍（−0.949～−1.048 dBTP）、「0 顆」補範圍、阻尼措辭改保守；重打 zip（SE 兩版只換 README，音檔沒動）；`x2_verify` 134/134；專輯授權草稿（O05）、DistroKid 查證（O18，原頁全 403，只有搜尋摘要） | PASS |
| INT2 | src 與執行檔沒變，不重建；全套 GATE 全綠（見第 3 點） | — |
| HO2 | 本檔、TODO、DEVLOG、README、`WF0925_README.md` §7、裁決包追記（各題下的 WF0925b 行、新增 Q38） | — |

   WF0925b 另外記下的：CLI 輸出路徑約 247 字元以上就 exit 1（Windows 260 字元上限；TF、BR 各碰到一次，`--workdir` 用短路徑即可，要不要改 CLI 另裁）；XF 稽核的判定只在 gitignored 的 `output/wf0925b/XF_audit/`，沒有進版控的稽核證據檔（摘要見 `WF0925_README.md` §7-1）。

3. **整合卡 GATE 與基線**
   - WF0925 整合卡（`reports/gate_outputs/wf0925_INTEGRATION.txt`，原始輸出 `wf0925_integration_raw/`）：
     三主 target＋五測試 target 重建 EXIT=0、error/warning 0 行；ctest 4/4（AuditTest 110 PASS／0 FAIL、D9c-guard PASS、K-02 +0.112 dB 只印數字）；
     pytest 282 passed＋1 skip＋5 xfail＝288；`--full` NO CHECKED FAILURES（3 個 rubber N/A）；`--selftest` 13/13；
     `verify_score --all` 75/75（1 項既有豁免）；HostProbe 215 PASS／0 failures（repo 根目錄、`output/wf0925/INT` 各跑一次）；位元不變 8/8 IDENTICAL。重建後 `build/` 的 CLI 是 `b84c775b…`。
   - **WF0925b 整合卡 INT2**（`reports/gate_outputs/wf0925b_INTEGRATION.txt`，原始輸出 `wf0925b_integration_raw/`）：src 與 `build\` 6 支執行檔跟上面相同，所以沒重建、沒跑 ctest（上面的 ctest 4/4、AuditTest 110 仍適用）。
     pytest **301 passed＋1 skip＋5 xfail＝307**（**新基線**；+19 全來自 TF，刪除 0）；`--full` NO CHECKED FAILURES（570 行跟 WF0925 整合卡逐行相同）；`--selftest` 13/13；
     `verify_score --all` 75/75（renderer 全是 `b84c775b04ab`）；位元不變 **8/8 IDENTICAL**（這次 `--cli` 故意用相對路徑）；HostProbe **215 PASS／0 FAIL**（cwd 在 repo 外、沒設 `TSUKI_REPO_ROOT`）。
   - 商品母帶的渲染器 `9123db8f…`：`exports/renderer_archive/`（gitignored）＋**repo 外第二份 `E:\TsukiSynth_renderer_archive\`**（O15，交接卡核對 sha256 相同），另有 `output/wf0925/{N1,V1,R_audit}/cli.exe` 複本。
4. **裁決包**：`reports/decision_packets/WF0925_open_decisions.zh-TW.md`，**38 題（Q01–Q38）＋O01–O19**。每題回一個字母；沒回的題＝維持現狀，AI 不動。
   開頭有總覽表（「急」欄：上架前／發版前／不急；以及選了會不會改聲音）和可以整段複製的回覆範本（範本裡的字母是規劃者建議，不是預設值）。標 R10 的選項，AI 會先做前後對照報告，不會直接落地。
   WF0925b 追記：各題下以「2026-09-25 WF0925b」開頭的那一行是收尾輪的處理結果（Q08 行號更正、Q12 已先做 A、Q15／Q20／Q21／Q26 商品文字已修、Q17 已補 BR 數字、Q18、Q33／Q34／Q36 補數字；§7 表後補 O05／O15／O16／O17／O18 的處理結果）。
   **新增 Q38**：F-03 缺檔警告措辭（「音量會和 IR 模式不同」在 D9c 之後不準；WF0925 那份包漏收，原本只掛在 TODO）。
5. **月月要做的事**
   - **審 staged**：`git diff --cached`（**239 檔**）；commit 怎麼切、要不要 push → **Q33**（切法見 `WF0925_README.md` §7-6）。CI 相關的改動（HostProbe 步驟、release workflow、Q12 已先做的 A）都要 push 之後才驗得到：push 後看 `physics.yml` 那次 run，再手動觸發一次 `release-physics.yml`。
   - **回裁決包（38 題）**：急的是「上架前」（Q15、Q20–Q28）和「發版前」（Q01、Q05–Q09、Q12、Q14、Q19、Q29–Q32、Q35、**Q38**）。
     Q12 已在「都處理掉」授權下先照 A 做，回 B／C 會改回去；Q17 選項 D 的「先算數字」已交（BR 報告），可以看數字直接在 A／B／C 裡選。
   - **下載同意**：pluginval＋Steinberg validator 重驗（**Q14**）；Inno Setup、vc_redist、VST logo、論文等（**Q37**）。兩輪 AI 都沒有下載任何執行檔。
   - **重新部署 VST3、清三份舊副本**（**Q35**，要管理員權限）：系統上仍是 09-10 的 build（缺 D12、D9c 和 WF0925 的全部改動），位置 `C:\Program Files\Common Files\VST3\TsukiSynth_VST3_2026-09-10\TsukiSynth.vst3`；另有 `(x86)`（07-12）和 `%APPDATA%\VST3`（05-07）舊副本；Cubase 的外掛快取停在 08-22。
   - **商品 v1.1 候選**：`exports/products/clean_batch2_v1_1_candidate/`，入口 `CHANGES_v1_1.md` 開頭「XF」段與 §0（**12 項待確認**，多了 11 專輯授權、12 DistroKid）。商品稽核已 PASS；原版 `clean_batch2/` 212 檔沒動過。相關題 Q15、Q20–Q28、O01、O05、O18。
     **要你登入才能確認的**：DistroKid 上傳表單的 AI 選項、Content ID、曲風（`DISTROKID_NOTES.md` K1～K7；原頁對 AI 全回 403）；專輯授權第 5 條選 A 或 B（`LICENSE_ALBUM_v1_1.txt`，草稿）。
   - **暫存清理**（**Q36**）：**C 槽只剩約 12 GB（98%）**。可清的有 `output/wf0925/` 5.2 GB、`output/wf0925b/` 1.9 GB、session scratchpad 8.9 GB、`E:\tsuki_wf0925_V1\` 17 GB；Downloads 殘留約 470 MB（Q36a）。**不要清** `exports/renderer_archive/` 和 `E:\TsukiSynth_renderer_archive\`（商品母帶的渲染器）。AI 只會移到資源回收筒，清空回收筒要你自己按。
   - 其他只能月月本人做的：寄信、註冊賣家帳號（O01）、清空資源回收筒、Limbus 有沒有用金鑰啟用、A10 Score 控制台實操（O04）。

### 1-1 09-25 盤點新發現與 WF0925 處理狀態（細節見 STATUS_CHECK §2 與 APPENDIX 條目）

1. **給愛麗絲全曲 16 顆弱基頻 FAIL**（**D16**；E5@0.278×9、A5×4、A6×2、A#6×1）。A14 B-2 把力脈衝的深零點從 G5 搬到了別的「音高＋力度」組合，08-30 時這 16 顆都是 PASS；clean_batch2 的給愛麗絲母帶含這 16 顆。
   → **WF0925-N1 零點地圖完成**：16/16 在凹口內；商品只有這份受影響；凹口內事件數 A14 前 44 顆、現在 47 顆（洞沒變少，換了位置）。母帶去留 → **Q15**。
2. **D9c 沒有硬 GATE** → **WF0925-K2 加了 D9c-guard**（常數精確等於 26.9f，刪掉或改掉會紅燈）。「IR−ALGO 響度差 ≤0.25 dB」的 CHECK 沒加（0.25 dB 不是月月裁過的容差）；JUCE 升版改了 Convolution 正規化時仍擋不住 → **Q01**。
3. **`release-physics.yml` 第一次打 tag 一定紅** → **WF0925-P1 已修**（補建 SpectrumViewTest＋HostProbe、改 pytest、加 HostProbe 步驟；staged）。還沒在 GitHub 上跑過（要 push 後手動觸發）；P1 稽核另查到多行 `run:` 只看最後一個 exit code，前面的 ctest／pytest 失敗會被蓋掉 → **Q12**，**WF0925b-TF 已先照 A 修（可推翻；staged，push 後才驗得到）**。
4. **「全曲版 41 個削波樣本」是誤讀**（正規化前的計數，母帶峰值 0.95）→ WF0925-X2 候選版 `PRODUCT_SHEET_v1_1.md` 已改正；全曲版放不放 → **Q25**。
5. **6 個 loop 檔長度不是整小節** → **WF0925-X1 做了 loop-ready 版 6 檔**（長度誤差 0 樣本）；附哪一版 → **Q26**。README 對它的說法被商品稽核抓到說太滿，**WF0925b-XF 已照實改寫、稽核 PASS**。
6. **VST3 動態連結 VC++ runtime** → **Q07**（G1 的安裝包腳本已把兩種做法寫成待選的註解區塊）。
7. **VST3 Program 參數會錯位** → **Q06**。
8. **pluginval／Steinberg validator 最後一次是 08-06** → **Q14**（要下載，等月月同意）。
9. **D15 的兩個 strict xfail 永遠不會 XPASS** → **WF0925-P1 已修**（pin 搬到非 xfail 測試；稽核反例：pin 改 0.001 就紅）。
10. **CI 的 Linux leg 實際是 GCC 13.3**（`physics.yml` label 寫 `ubuntu-24.04-clang`）→ **Q13**。

文件面的兩條（`wf0914_D9c_ir_makeup_gain.txt:252-254` 不實陳述、B7 裁決同步漏做）09-25 已在 c7 修正（勘誤附檔尾、TODO／ROADMAP 的 B7 條目已同步）。
WF0925 各卡點名「交接要同步」、但檔案不在交接卡權限內的，列在 `WF0925_README.md` §6；**WF0925b 已處理其中 9 條、1 條處理一半**（逐條標在 §6），剩下的（要改 `src/` 的註解、voice_pool 報告行號等）與 WF0925b 新留下的，列在同檔 §7-8。

## 2. 這個專案是什麼

聾人使用者（月月）+ AI 不靠聽感、靠物理理論精確模擬聲音的 JUCE 8 VST3 合成器。
**唯一驗收依據 `ROADMAP_PHYSICS.md`**，§1 十條強制規則開工前必讀（R1 只認 GATE 輸出／R2 禁調寬容差／R3 禁縮 GATE／R4 禁未溯源常數／R6 改 src 必跑 `--full`＋三 build／R7 不 commit／R10 渲染改變要前後對照）。
**X4 規約**：跑 `ctest` 前必先重建測試 target（現為五個：Audit/Tuner/PhysicsModels/SpectrumView/HostProbe）。
四個引擎：Cimbalom/Piano（弦）、Tongue Drum（梁）、Water Gong（板）、FM Piano（域外）。
**月月是聾人開發者，全程免耳驗收。** 物理／位置正確性由 GATE 鏈負責，美學驗收交給外部專業人士。corpus **75 檔**；8 首位元不變基準 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`；
基線（WF0925b 整合卡 INT2）：pytest **307 個測試**（301 passed＋1 skip＋5 xfail）、HostProbe **215 項**、AuditTest **110 條**（AuditTest 沿用 WF0925 整合卡；兩輪之間執行檔沒變）。

## 3. 三輪工程落地了什麼（全部已 commit：`5c9cdb3`～`49b8542`）

| 卡 | 白話 | 證據 |
|---|---|---|
| E1 | CI 從 5 檔白名單改跑全套 pytest；pin pytest/mido | `wf0907_E1_ci.txt` |
| E5 | host 問「聲音多長」改由物理引擎自報 worst-case T60（3.45 s → 34/179/320 s），DAW bounce 不再截尾 | `wf0907_E5_tail.txt` |
| E8 | score 合法性單一真相：schema 自動走訪 388 突變體，C++ `--validate` 從 22 條不一致修到 0 | `wf0907_E8_schema.txt` |
| E9 | `--dump-modes` 支援 layered score（三檔 3/4/260 事件） | `wf0907_E9_layered.txt` |
| E7 | K-03 超 maxBlock 分塊（位元等價）；K-02 量到 IR 比 ALGO **小 28.5 dB** | `wf0907_E7_reverb.txt`、裁決包 K02 |
| C11/C12 | stem_verify 拒答理由/直方圖；`--analysis-dry` 預設 + provenance 三個 sha256 | `wf0907_C11/C12_*.txt` |
| C10 | `measure_pitch_cents()` 抽出（位元不變）+ 合成哨兵：**1.1721 c > 1 c** | `wf0907_C10_selfcal.txt` |
| E10/E10b | H6 五種 block size 位元相同；水鑼 glide 逐取樣（原本逐 block 階梯差 +2.6 dB）；H7 user preset harness（`src/ParameterLayout.h`） | `wf0907_E10_*.txt`、`wf0908_E10b_*.txt` |
| **P3 F-03** | 受管理 IR 庫 `src/IRLibrary.h`（sha256 去重）、preset 存 `reverb_ir{kind,sha256,original_name}`、缺檔三態、`getIRStatus()` 單一真相、HostProbe 67 PASS | `wf0908_P3_f03.txt` |
| P1 | `tools/partial_verify.py`：partial 頻率內部一致性（±5 c）+ C13 `pitch_via_partials_*`；`gate_ready=false` | `wf0908_P1_partial.txt` |
| P2 → A14 落地 | A14 B-2 τc 音高律 patch 09-10 放行 `git apply`，Opus 稽核 PASS；7/8 位元不變只 physical_piano 變 | `reports/a14_tauc_keytrack_before_after.md`、`wf0910_A14_apply*.txt` |
| P4/P4b | A8 引用更正：TU Berlin 半徑 2.06 m 非 1.05、授權 BY-NC-SA、Sinin 消音室、HammerImpulse 檔頭出處改 Woodhouse | `wf0908_P4_a8.txt`、`wf0909_P4b_citation.txt` |
| **D8** | 兩首月光空靈鼓相關 score `exciter: finger → wood_mallet`（月月裁決）；200 Hz 以下能量 97% → 18%、斜率 41 → 5.5 dB | `reports/d8_tongue_drum_exciter_before_after.md` |
| 整合 ×3 | 每輪末重建 `build/`：ctest / pytest 267 / `--full` NO CHECKED FAILURES / HostProbe / 位元不變全綠 | `wf090{7,8,9}_INTEGRATION.txt` |

WF0914 輪（09-14～16）的成果 09-25 分 7 個 commit 入庫（`a09058c`～`18430c4`，未 push），摘要見 §5-0b 和 `TODO.md` 快照，逐卡證據在 `reports/gate_outputs/wf0914_*`。
WF0925 輪（09-25）的成果 staged 未 commit，摘要見 §1 第 2 點，逐卡細節在 `docs/workcards/WF0925_README.md` §2，證據在 `reports/gate_outputs/wf0925_*`。
WF0925b 收尾輪（09-25 同日）的成果也 staged 未 commit，摘要見 §1 第 2b 點，逐卡細節在 `WF0925_README.md` §7，證據在 `reports/gate_outputs/wf0925b_*`。

## 4. 驗證鏈現況

```
MIDI 原譜 ──① score_vs_midi_verify──> score.json ──② melody_verify──> WAV
                                          │                            │
                                          └──③ verify_score (75 檔) ───┘
                                                                       │
        ④ HostProbe(H1–H8) / ⑤ Cubase 實測 / ⑥ piano-roll 影片 / ⑦ stem_verify / ⑧ partial_verify ─┘
```

- ② `melody_verify`：onset ±10 ms / pitch ±5 c（既有裁定）。**量測器自證 ≤1 c 未達成**：月月 09-10 選 A 收窄主張域（持續段 1.1721 c 為已知誤差；B 路線兩家族六候選試完，見 §5-0）。D15 加入放鍵段語料後量出放鍵段 5.2304 c（開發）／7.2055 c（hold-out），09-15 選 A' 再收窄（設計文件 §8.5：放鍵段已知上界 ~7.2 c）。
- ⑦ `stem_verify`：乾聲分軌預設、拒答理由、provenance。記憶體線性成長**已修**（WF0914-D14 串流化：905 事件全量峰值 ≈1.65 GB，輸出逐位元不變）。
- ⑧ `partial_verify`：informational；振幅只記錄不判定；**不可宣稱「泛音已驗證」**。
  WF0925-V1 第一次跑全曲 905 顆：5,428 個 partial 格中 PASS 4577／FAIL 849／UNVERIFIED 2；FAIL 多數來自期望值慣例（工具以第 0 根弦為準，三弦平均高約 +5 c）。要不要改慣例、升不升 GATE → 裁決包 Q18（`reports/partial_verify_full_2026-09-25.zh-TW.md`）。
  WF0925b-TF 已把工具的 docstring 與 `caveats[0]` 改成現況（C10 選 A、D15 選 A'，升 GATE 要月月另裁），並加了 `--cli`；stem_verify 也加了 `--cli`、讀得懂 WAVE_FORMAT_EXTENSIBLE。
- ④ HostProbe（**215 項**，WF0925 前是 89）：H6 變動 block size 位元相同（含水鑼 glide）、H7 user preset 三情境（F-03 落地後為硬 CHECK）、H8 tail ≥ 引擎 worst-case、D12 舊 state 遷移三情境（K1 加了「輸出 state 不含 `reverb_ir_path`」斷言）、E14 `state_version`／preset 版本（K1）、E16 27 個工廠 preset 逐一檢查（K2，109 條；峰值與 RMS 只印不判）。
  **K2 之後不必再從 repo 根目錄跑**：H8 找 `data/materials.json` 的順序是 cwd → 環境變數 `TSUKI_REPO_ROOT` → exe 所在資料夾一路往上，用了哪條會印出來；exe 複製到 repo 外又沒設環境變數，會出現 4 個 H8 FAIL（大聲失敗）。
  HostProbe 不在 ctest（`CMakeLists.txt:255` 刻意不註冊）。**CI**：WF0925-P1 已把它加進 `physics.yml` 的 Windows job 與 `release-physics.yml`（staged，push 之後才會第一次在 GitHub 上跑；runner 能不能無頭載入 VST3 本機驗不到）。
  WF0925b-TF 再把 HostProbe 移到兩支 workflow 各自 job 的最後（Q12 選項 A 的「調次序」），註解也改成現況；INT2 在 repo 外的 cwd、不設環境變數跑 build\ 的 HostProbe 是 215／0。
- **D9c（IR 補償增益）**：WF0925-K2 加了 **D9c-guard**（`tests/audit_repro.cpp`，`kIrWetMakeupGain == 26.9f` 精確相等，讀到 26.8999996），常數被刪或改會紅燈。
  K-02 仍只印 IR−ALGO 的差（+0.112 dB），沒有響度 CHECK；JUCE 升版若改了 Convolution 的 0.125 正規化，常數沒變、響度卻會漂，現有 GATE 擋不住 → 裁決包 Q01。
- **CI 覆蓋**：每次 push 跑 4 個 ctest、全套 pytest（WF0925＋WF0925b commit 後是 307 個）、`physics_verify` selftest/t60/full、verify_score 6 首 smoke、三平台 CLI 渲染、Windows ASAN；commit＋push 後加上 HostProbe。
  **沒進 CI 的**：pluginval／validator、全 corpus 75 首、8/8 位元不變（`engineering-gaps:E19`）。
  **注意**（P1 稽核查到的既有問題，裁決包 Q12）：GitHub Windows runner 的 pwsh 多行 `run:` 只看最後一個指令的 exit code，`release-physics.yml` 那步的 ctest／pytest、`physics.yml` 的 pytest 失敗會被後面的指令蓋掉——綠燈不代表中間每一步都過。
  **WF0925b-TF 已照 Q12 建議 A 先修（可推翻）**：兩支 workflow 共 14 個多行區塊逐一檢查，每行原生指令後面補 exit code 檢查；本機照 runner 包法模擬，被蓋掉的情境 12 → 0。**GitHub 上的 origin 版本還沒有這個修正**（staged，push 後生效），在那之前 origin 上的綠燈照舊不可全信。

## 5. 下一步候選（月月選主線；09-10 四裁決見 §5-0；09-15～16 五裁決見 §5-0b；WF0925／WF0925b 之後待裁的 38 題見裁決包）

### 5-0 已落地的四裁決（2026-09-10～11）

| 裁決 | 落地 |
|---|---|
| C10 選 A | 主張域收窄寫進設計文件 §8.5/§9.7：量測器含 ≤1.18 cent 已知誤差，±5 cent 門檻不變，**不可宣稱 ≤1 cent**；C10C 工具部分入庫、時域 NLS 候選存 `reports/c10c_nls_candidate.patch` |
| A14 放行 | `git apply` 落地，Opus 稽核 PASS（含牙齒：還原公式 sha 精準回舊值）；7/8 位元不變只 physical_piano 變；基準改 `sha256_before_post_a14.txt`（09-25 盤點：B-2 引出給愛麗絲 16 顆新弱基頻 FAIL，見 §1-1） |
| 月光母帶 | 等換源重轉譜後一起重出，現在不動 |
| 兩封信 | 草稿 `docs/correspondence/2026-09-10_TU_Berlin_*.md`、`_Iowa_MIS_*.md`，月月自寄 → **09-15 已寄出，等回覆**（WF0925-G1 已把兩封信的狀態行改成「已寄出」；標題行 WF0925b-DS 已改成「信件 1／2（已寄出 2026-09-15）」） |

### 5-0b 09-15～16 五裁決（WF0914 輪；月月 09-15「五題全照建議」＋09-16 D9 選 A，各裁決包有記錄）

| 裁決 | 落地 |
|---|---|
| B7＝§5 路徑 C＋(a) 乙案 | 本輪合法終點：Phase 0 完成、Phase 1 部分完成（dumpModes 欄位撤回、五個純函式保留）、Phase 2/3 BLOCKED。B7 殘留註解 WF0925-K1 已改成「目前沒有呼叫點」 |
| D9＝(a)＋A 案 | D9b 量出結構性 −28.6 dB 固定差 → D9c 落地 `kIrWetMakeupGain=26.9f`，四組落差歸零、8/8 位元不變，D9 關閉；WF0925-K2 補了 D9c-guard |
| D11＝C | patch 存檔（`reports/d11_string_scale_candidate.patch`）；WF0925-F5 根因調查完成，要不要重開 A/B → 裁決包 Q16 |
| D13＝B | 主張域收窄 `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §1；`PlateModel.h` 檔頭與 `water_gong_free` 描述 WF0925-K1 已同步（WAV 8/8 不變） |
| D15＝A' | 設計文件 §8.5 放鍵段 ~7.2 c 已知上界；WF0925-P1 把 release 段的 pin 搬到非 xfail 測試 |

### 5-1 主線候選（依價值排；~~刪除線~~=已完成或已裁決）

1. ~~**push + merge `main`**~~ **09-15 完成**：CI 三平台全綠（含修掉 09-07 起的 spectrum_view 紅燈）。
2. **月光／四季換源重轉譜**（解上架限制的唯一路；轉譜 GATE `score_vs_midi_verify.py` 已備；D8 母帶重出掛在這後面；擋專輯 Vol.2）。
3. **UI 功能規格送設計端**（`docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md`，09-25 已同步成 **v1.2**（c7 `18430c4`）；送給誰、功能算不算做完 → 裁決包 O02）。
4. ~~**B7 第一原理力鏈開工**~~ **09-15 裁決結案（路徑 C＋(a) 乙案）**：Phase 0 溯源文件完成（`docs/HAMMER_VELOCITY_SOURCES.md`、`RADIATION_POWER_SOURCES.md` §8）；Phase 1 純函式+五條測試落地，**dumpModes 欄位撤回**（proxy 查證翻案：score velocity 實為 `base×MIDI/90±微調`，非 MIDI/127）；Phase 2/3 本輪不做，重啟前提見裁決包 `B7_phase2_and_open_items.zh-TW.md` §6。
5. ~~**D9～D15 缺口**~~ **09-15～16 全數處理並裁決**：D9（D9c 落地）、D12、D13（選 B）、D14、D15（選 A'）關閉；D10 等付費牆文獻；D11 選 C，patch 存檔，排「D11-F5 根因調查」卡。詳見 §7 與 `TODO.md` 開頭快照。
6. ~~09-25 盤點新增的候選（弱基頻零點地圖、loop-ready 版、pluginval 重驗、release CI 修正等）~~ **WF0925 輪處理完 AI 能做的部分**（§1 第 2 點）；**WF0925b 收尾輪再做掉商品 lane 修正輪、§6 文件同步、Q12、O16、Q17 的前後數字**（§1 第 2b 點）。剩下要月月拍板的在裁決包 38 題；AI 還能接著做、不需裁決的（多半要改 `src/`，要另開卡跑 R6）在 `WF0925_README.md` §7-8。

### 5-2 裁決前的原始說明（保留追溯；四項都已裁決，見 §5-0）

1. **C10 量測器自證**：B 路線已在 STFT 家族（5 候選，其中柔化質心被稽核抓到假改善撤回）與時域 NLS（合成關卡 hold-out 0.08 c 但真實渲染更差）試完。建議改選 A（收窄主張域），措辭草案 `reports/decision_packets/C10_selfcal_domain.zh-TW.md` §6.4。
   更上層發現：合成哨兵的訊號模型與 NLS 相同（套套邏輯），現行 1-cent 門檻本身不足以認證估計器，要補放鍵/阻尼段語料（後由 D15 補上）。C10C 全部改動在 `reports/c10c_nls_candidate.patch`。
2. **A14 B-2 patch 放行**（Rule 10）：`git apply reports/a14_tauc_keytrack_b2.patch`。
3. **月光空靈鼓母帶重出**：D8 只改了 score，`exports/products/moonlight_batch1/` 母帶仍是舊渲染；且月光授權（CC BY-SA）疑慮未解，仍不可上架。
4. **兩封信由月月自行決定**：TU Berlin（要商業授權）、Iowa MIS（器材對應）。AI 不代發。

## 6. 規劃者代決紀錄（月月 09-07 委託；可推翻）

| 項 | 決定 | 依據 |
|---|---|---|
| A13 | B+：只驗 partial 頻率（±5 c 既有）、不立振幅 GATE、B 對照寫報告 | `A13_partial_gate_domain` |
| A14 | 引擎缺陷：τc 音高律太平（k=0.212），基頻落半正弦力脈衝零點（G5 −33.7 dB）；B-2 先做、B-1 等文獻 | `A14_weak_fundamental_ruling` |
| F-03 | B＋（受管理 IR 庫＋工廠/使用者分流）＋缺檔三態；不得沿用 instance 上一個 IR | `F03_IR_PRESET_RECALL` §7–8 |
| K-02 | C 維持現狀（A 更糟、B 動全 corpus）；另立 D9「IR 載入響度對齊」 | `K02_reverb_wet_scale` §5 |
| A8 | 私下對照參考（月月 09-09：無可商用校準資料集就私下參考）；補充 Weinzierl 2018／Iowa 泰國鑼 | `EXTERNAL_DATASET_A8/ALTERNATIVES/SUPPLEMENT` |

## 7. 新登記的缺口（D 類）

（09-25 WF0925 輪後狀態）D9 **關閉**（D9c 補償落地；WF0925-K2 加了常數守門 D9c-guard，響度 CHECK 待 Q01）／D10 等文獻（付費牆，補摘已入庫）／
D11 patch 存檔；**「D11-F5 根因調查」WF0925-F5 已完成**（`reports/d11_f5_root_cause_2026-09-25.zh-TW.md`；另發現現行 F5 PASS 靠探針預設弦徑 0.8 mm，改 1.0 mm 就 −59.5 dB FAIL），重不重開 A/B → Q16／
D12 **關閉**（遷移落地；載入失敗分支的設計 → Q10）／D13 **關閉**（選 B；`PlateModel.h` 檔頭與 score 描述 WF0925-K1 已同步）／
D14 **關閉**（串流化落地；WF0925-P1 補了 17 個單元測試）／D15 **關閉**（選 A'；pin 已搬到非 xfail 測試）。原始登記文字見 git 歷史。
（09-25 新登記）**D16** 給愛麗絲全曲 16 顆弱基頻 FAIL（A14 B-2 把深零點搬到別的音高×力度，見 §1-1 第 1 條）：**零點地圖 WF0925-N1 已完成**，D16 本身仍開放，母帶去留與修法 → Q15。
（WF0925 附帶發現，**還沒編號**）N1：韋瓦第四季的 string＋bow 有 5,682 顆落在同一種凹口裡（非商品；換源後若沿用 bow 會帶著同樣問題），要不要登記成新 D 項 → 裁決包 O03。

## 8. 檔案地圖

| 要找什麼 | 去哪 |
|---|---|
| 當前待辦 + 各輪快照 | `TODO.md` 開頭（09-25 WF0925 快照、09-25 盤點快照、09-15 WF0914 快照＋五項裁決）；`TODO.md`「★ 2026-09-25 盤點新登記」逐條狀態 |
| **等月月拍板的事（WF0925／WF0925b 後）** | `reports/decision_packets/WF0925_open_decisions.zh-TW.md`（38 題＋O01–O19；各題下「2026-09-25 WF0925b」那一行是收尾輪結果） |
| 09-25 現況盤點 | `reports/status_check_2026-09-25/`（untracked，見 §1 第 1 點）：`STATUS_CHECK.zh-TW.md`（結論）、`APPENDIX_findings.zh-TW.md`（逐條證據）、`gate_logs/`（09-25 GATE 原始 log）、`commit_lists/`、`probes/` |
| 流程規約（lane、build-wf、X4、位元不變基準、稽核 stage 規則） | `docs/workcards/WF0907_README.md`、`WF0907_R_research_common.md`；WF0914 差異在 `WF0914_README.md`；**WF0925 差異與逐卡結果在 `WF0925_README.md`（WF0925b 收尾輪在 §7）** |
| 施工卡 | `docs/workcards/WF0907_*.md`、`WF0908_*.md`、`WF0909_*.md`、`WF0914_*.md`（13 張卡＋README）；WF0925、WF0925b 的卡由 workflow 腳本直接派發，沒存成檔，範圍以 `WF0925_README.md` §2、§7 為準 |
| 裁決包 | `reports/decision_packets/`（A13/A14/F03/K02/C10/D8；WF0914：B7/D9/D11/D13；WF0925：`WF0925_open_decisions.zh-TW.md`） |
| WF0925 研究報告 | `reports/weak_fundamental_null_map_2026-09-25.zh-TW.md`＋`reports/weak_fundamental_null_map/`（N1，D16）、`reports/d11_f5_root_cause_2026-09-25.zh-TW.md`（F5）、`reports/partial_verify_full_2026-09-25.zh-TW.md`、`reports/voice_pool_occupancy_2026-09-25.zh-TW.md`＋`reports/wf0925_method/`（V1）、`docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md`（L1）；**WF0925b**：`reports/beam_x2_option_b_before_after_2026-09-25.zh-TW.md`＋`reports/beam_x2_option_b/`（BR，Q17 拿掉 ×2 的前後數字） |
| 發行與授權文件（WF0925-G1） | `THIRD_PARTY_NOTICES.txt`、`LICENSE`（第三方段落）、`docs/legal/JUCE8_LICENSE_REVIEW.zh-TW.md`、`docs/legal/EULA_BUYER_DRAFT.md`、`tools/installer/`（`TsukiSynth.iss`＋README，沒編譯過）、`docs/KNOWN_LIMITS_INDEX.zh-TW.md` |
| Rule 10 報告 | `reports/a14_tauc_keytrack_before_after.md`（09-10 已落地）、`reports/d8_tongue_drum_exciter_before_after.md`（09-09 已落地） |
| 稽核診斷（三病根） | `docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.zh-TW.md`（§4 全部已修或已裁決） |
| 免耳驗證設計 + 主張域 + 量測器自證 | `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §7–§10（§8.5 含 D15 放鍵段上界） |
| 引擎主張域收窄（D13 水鑼） | `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` |
| 外部資料集 | `docs/EXTERNAL_DATASET_A8.zh-TW.md`、`_ALTERNATIVES`、`_SUPPLEMENT`；資料在 `external_data/`（gitignore） |
| B7 資料 | `docs/B7_PHASE0_DATA.zh-TW.md`、`docs/workcards/B7.md`、`docs/HAMMER_VELOCITY_SOURCES.md`、`docs/RADIATION_POWER_SOURCES.md` §8 |
| WF0914 其他研究文件 | `docs/STRING_SCALE_SOURCES.md`（D11）、`docs/GONG_PARTIAL_ANALYSIS.zh-TW.md`（D13）、`docs/HAMMER_CONTACT_SOURCES.md` §9（D10） |
| UI 設計輸入 | `docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md` **v1.2**（09-25 同步 D9c、D12） |
| GATE 證據 | `reports/gate_outputs/wf090{7,8,9}_*.txt`、`wf0914_*.txt`（含 `wf0914_integration_raw/`）、`wf0925_*.txt`（含 `wf0925_integration_raw/`；X1／X2 那 15 檔 WF0925b 去掉本機路徑後已 stage）、`wf0925b_*.txt`（含 `wf0925b_integration_raw/`、稽核 `wf0925b_TF_audit.txt`、`wf0925b_DS_BR_audit.txt`）、`*_INTEGRATION.txt` |
| 變現線 | `docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md`（untracked）、`exports/products/clean_batch2/`（原版，gitignored）、**`exports/products/clean_batch2_v1_1_candidate/`（WF0925 v1.1 候選，入口 `CHANGES_v1_1.md`；WF0925b-XF 修正後稽核 PASS；專輯授權草稿 `LICENSE_ALBUM_v1_1.txt`、DistroKid 查證 `DISTROKID_NOTES.md`）**；CLI 存檔 `exports/renderer_archive/`＋repo 外 `E:\TsukiSynth_renderer_archive\` |
| 歷史決策 | `DEVLOG.md` |

## 9. 操作備忘

- 建置：`cmake -B build -DCMAKE_BUILD_TYPE=Release -DTSUKI_BUILD_TESTS=ON`；CLI `build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`
- 全套 GATE（WF0925 整合卡實跑順序）：三 target + 五測試 target → `ctest`（4/4；AuditTest 110 PASS）→ `python -m pytest tests -q`（WF0925b 後：301 passed＋1 skip＋5 xfail＝307）→ `python tools/physics_verify.py --full`（NO CHECKED FAILURES）與 `--selftest`（13 行 PASS）→ `python tools/verify_score.py --all`（75/75）→ HostProbe（215 PASS）→ 位元不變（8/8）
- `verify_score.py`／`physics_verify.py` 沒帶 `--cli` 時由 `find_cli` 自己挑（WF0925-P1 後優先挑路徑含 Release 的，並印出選到哪支）。**做 GATE 時一律帶 `--cli <絕對路徑>`，再看 log 裡 manifest 的 renderer 欄位對不對**（K1 的 `--cli` 後面空白，測到了舊 CLI）。
- 位元不變：`python reports/gate_outputs/wf0907_method/render_wf_scores.py --label <名稱> --workdir <repo 外的短路徑> --cli <CLI 路徑> [--outdir <輸出資料夾>]`，產出的 `sha256_<名稱>.txt` 對 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt` 比（`diff --strip-trailing-cr`，基準檔是 CRLF）。
  **`sha256_before_post_d8.txt` 只留作存檔，拿它比會讓 physical_piano 假紅燈**。`--outdir` 是 WF0925-P1 加的（staged）；不帶時照舊寫進 `wf0907_method/`。`--workdir` 放 repo 內會被腳本拒絕。
  WF0925b-TF 之後 `--cli` 用相對路徑也可以（腳本先轉絕對路徑並印出來；staged）。**`--workdir` 要用短路徑**：CLI 的輸出路徑約 247 字元以上會超過 Windows 260 字元上限，CLI 寫不出 render manifest、exit 1（WF0925b 的 TF、BR 各碰到一次）。
- 分軌：`python tools/stem_verify.py <score> [--limit N] [--jobs N] [--json out] [--cli <CLI>]`（乾聲預設）；partial：`python tools/partial_verify.py <stem 報告.json> [--cli <CLI>]`（`--cli` 是 WF0925b-TF 加的；指到不存在的檔會 exit 1，不會退回自己找）
- 量測器自證：`python tools/measurement_selfcal.py [--holdout]`。現況 exit 1：開發網格總 max 5.2304 c（持續段 1.1721／放鍵段 5.2304）；`--holdout` 7.2055 c（持續段 1.0840／放鍵段 7.2055）。主張域見設計文件 §8.5。
- HostProbe：`build/Release/TsukiSynthHostProbe.exe <.vst3> <outdir>`。WF0925-K2 之後 cwd 不限（§4；exe 複製到 repo 外時要設 `TSUKI_REPO_ROOT`）；H7／D12／E14 會在 `%APPDATA%\TsukiSynth\Presets`、`\IR` 建檔再自己刪掉（要不要改成可指定資料夾 → 裁決包 O09）。
- ffmpeg：`C:\Users\admin\Desktop\Tools\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe`（`tools/melody_roll_video.py` 在 WF0925-P1 後的找法：`--ffmpeg` > 環境變數 `TSUKI_FFMPEG` > PATH > 這個路徑）
- Python：本機實際是 **3.13.3**（規約寫 3.12；CI 固定 3.12.8）。WF0925 的 Python GATE 都在 3.13.3 上跑。
- `build/` 的 CLI 在 09-25 10:39 被 WF0925 整合卡重建成 `b84c775b…`（WF0925b 沒重建）；重現商品母帶要用 `exports/renderer_archive/TsukiSynthCLI_9123db8f_build20260915.exe`，repo 外另有一份 `E:\TsukiSynth_renderer_archive\`（同 sha256 `9123db8f…`；裡面的 `SHA256SUMS.txt` 是 repo 相對路徑，在 E 槽直接 `sha256sum -c` 會找不到檔，要手動比）。

## 10. 工作方式備忘——補充

（原文在 §12；09-13 新增一條：**多檔 commit 用路徑清單時，要先把 CR 去掉**。Windows 寫出的清單帶 CR，git 會認不出檔名，09-13 那五個 commit 第一次全部空跑。）
Git Bash 的正確寫法：

```bash
tr -d '\r' < list.txt > list_lf.txt && git commit --pathspec-from-file=list_lf.txt -F msg.txt
```

（09-25 註：這條在 09-13～25 的版本裡，`\r` 被寫成了真的換行，照抄會變成刪 LF、路徑黏成一行；現已改正。`DEVLOG.md` 09-13 段的寫法一直是對的。）

## 11. 外部工具評估（2026-09-14，`Downloads\不知道有沒有用`）

| 工具 | 是什麼 | 授權 | 判定 |
|---|---|---|---|
| **Limbus Spatial Stage 0.9.0** | 視覺化空間混音（Sender/Master 兩插件 + 獨立程式，每軌即時頻譜） | 原價 €49.90 現 €0 無期限，需金鑰（月月已收到信）| **值得裝**：少數對聾人友善的混音工具，月光多版本混音可用。**09-14 已安裝；有沒有啟用待月月確認** |
| **Yamaha Piano Sheet Converter β** | AI 採譜：音訊 → 分級鋼琴譜（`installer.exe`，Yamaha 簽章；根目錄 dll/pak/resources 是它的解壓殘留） | β 免費，**限私人、不可商業**；需登入、音檔上傳雲端 | 可當「把錄音翻成看得見的譜」的個人工具；**不可當驗證證據、不可用於換源**（AI 猜的、會繼承錄音版權）。**09-14 已安裝** |
| Orra Deverb 1.0.0 | 去殘響 | 免費隨喜 | 可有可無：渲染本就出乾聲，外部資料集皆消音室 |
| Klanggeist 1.1.1（MODRI） | 一鈕創意頻譜效果 | 平常 €20，72h 免費促銷，需金鑰線上啟用 | 音效產品線可玩，與物理主張無關；先確認有無金鑰 |

已清：重複 zip、Mac 版、`__MACOSX`（進資源回收桶）。
**安裝狀態（09-25 查）**：Limbus（兩個 VST3＋獨立程式）和 Yamaha 都是 09-14 12:56 裝好的。Limbus 有沒有用金鑰啟用，磁碟上查不出來。
**待清（等月月點頭）**：資料夾目前共 614 MB，其中 Yamaha 解壓殘留約 470 MB（舊寫 200 MB 偏少），安裝檔約 136 MB，Klanggeist 資料夾約 10 MB。要不要清、保留哪些安裝檔，等月月回覆。

## 12. 工作方式備忘（三輪的教訓，原文）

- **規劃者畫地圖、Sonnet 工兵、Opus 稽核親自重跑**——這套三輪抓到：柔化估計器假改善、研究文件編出來的資料集標題、規劃者自己寫錯的卡文（P4 第 3 項）。**不要跳過稽核層。**
- **跨 lane 污染**：同一工作樹並行時，未完成卡的新測試檔會弄紅別卡的全套 pytest。全套 pytest 應放整合卡；工兵誠實回 RED 是對的。
- **卡文可能錯**：工兵發現卡與 repo 內更新的查證矛盾時停下回報（P4 第 3 項）是正確行為。
- **合成哨兵的盲點**：哨兵語料若與候選估計器同模型，會套套邏輯地全過；必須加「期望值固定、真值偏離」與真實音檔兩條軸。
- session limit 中斷用 `resumeFromRunId` 續跑；被中斷的卡用接手說明讓工兵先看 diff 再重跑 GATE。
- 月月的偏好不變：不腦補、查不到就說查不到、需要裁決做成看數字就能選的裁決包、白話到位。
