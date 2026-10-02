# TsukiSynth — Current TODO

> Last updated: 2026-10-02（WF1002 輪：WF0925 裁決包 38 題落地；追加裁決包 N1～N9 月月已裁，WF1002b 待實作）
> 2026-10-02 快照：見 `docs/workcards/WF1002_README.md`（裁定表＋§3 結果）。待辦：WF1002b（N1 B1 壓縮器固定補償、N2 FM 修法落地、N3 F5 換窗、N4 C5 升格、N5 警告句入規格、N6 查 Inno Setup 授權、N7 .iss 64-bit、N8 R6 清單擴大）；月月本人：註冊 BOOTH＋PayPal、定價、授權 4 空格、跑部署腳本、寄 JUCE 信、清空回收筒。
> ~~（前一版：2026-09-25 WF0925b 收尾輪完工交接）~~
> Branch: `fix/deep-physics-audit-20260716`（HEAD `18430c4`：**WF0914 成果已分 7 個 commit `a09058c`～`18430c4`，未 push**；遠端仍停在 09-15：分支 `766d21d`、`main`=`3f9b90a`）
> **WF0925＋WF0925b 成果 staged、未 commit**（R7；**239 檔**；月月看 `git diff --cached`）。
> ~~（舊版：HEAD `766d21d`；已 push，`main`=`3f9b90a` 已 merge 同步；WF0914 輪成果全部 staged 未 commit，月月看 `git diff --cached`）~~

**2026-09-25（晚）快照（WF0925b 收尾輪完工；同一個「都處理掉」裁決的收尾）**：
- **6 張卡**：TF（Q12＋O16，CI／tools）、DS（`WF0925_README.md` §6 文件同步）、BR（Q17 拿掉 ×2 的前後數字）、XF（商品稽核 FAIL 修正輪＋O05＋O18）、整合 INT2、交接 HO2。不改 `src/`、不建置 plugin。逐卡結果在 `docs/workcards/WF0925_README.md` §7。
- **稽核全 PASS**：TF PASS、DS／BR PASS、XF PASS（WF0925 商品 lane 那 1 條 FAIL 已修；X1／X2 的 15 個證據檔去掉本機路徑後 stage）。
- **INT2 全綠**（`build\` 沒重建，執行檔跟 WF0925 整合卡相同）：**pytest 新基線 307 個測試＝301 passed＋1 skip＋5 xfail**（+19 全來自 TF，刪除 0）、`--full` NO CHECKED FAILURES、`--selftest` 13/13、`verify_score --all` 75/75、位元不變 **8/8 IDENTICAL**（`--cli` 用相對路徑）、HostProbe **215／0**（cwd 在 repo 外）。證據 `reports/gate_outputs/wf0925b_INTEGRATION.txt`。
- **staged 239 檔**＝WF0925 154＋WF0925b 新進 85。建議 commit 切法見 `WF0925_README.md` §7-6。
- **裁決包變成 38 題**（新增 Q38：F-03 缺檔警告措辭）＋O01–O19；各題下「2026-09-25 WF0925b」那一行是收尾輪結果。Q12 已在授權下先做 A（可推翻）。
- **C 槽只剩約 12 GB**：暫存清理見裁決包 Q36b 的 WF0925b 行。商品母帶渲染器已在 repo 外多備份一份 `E:\TsukiSynth_renderer_archive\`（O15）。
- 下方「★ 2026-09-25 盤點新登記」一節已逐條補上 WF0925b 的狀態。

**2026-09-25（下）快照（WF0925 輪完工；月月 09-25 裁決「剩下 AI 能處理的都處理掉」）**：
- **13 張卡**：C++ lane K1／K2／K1K2fix（`build-wf\`）、Python／CI lane P1、研究 lane N1／F5／V1／L1／G1、商品 lane X1／X2、規劃 Q1（彙總裁決包）、整合 INT、交接 HO。逐卡結果、證據路徑、稽核判定在 `docs/workcards/WF0925_README.md`。
- **稽核**：C++ lane 第 1 輪標 1 條要修（K1 的 GATE 4 證據不實）→ K1K2fix 更正 → 第 2 輪 PASS；Python／CI lane PASS；研究 lane 五張全 PASS；**商品 lane FAIL**（1 條要修：README 寫 loop-ready 檔「跟原版重播逐樣本相同」說太滿），X1／X2 的 15 個證據檔沒 stage，本輪沒跑修正輪（→ **WF0925b-XF 已修、稽核 PASS、15 檔已 stage**，見上方（晚）快照）。
- **整合卡（重建 `build/`）10 條 GATE 全綠**：ctest 4/4（AuditTest 110 PASS）、**pytest 新基線 288 個測試＝282 passed＋1 skip＋5 xfail**（舊 270；新增 18 條全來自 P1，刪除 0）、`--full` NO CHECKED FAILURES、`--selftest` 13/13、`verify_score --all` 75/75（1 項既有豁免）、**HostProbe 215 PASS**（舊 89）／0 failures、位元不變 **8/8 IDENTICAL**（本輪沒有任何渲染輸出改變）。證據 `reports/gate_outputs/wf0925_INTEGRATION.txt`。
- **staged 154 檔**：C++ 34＋Python／CI 15＋研究 75＋整合 24＋交接 6。建議 commit 切法見 `WF0925_README.md` §4。
- **等月月**：裁決包 `reports/decision_packets/WF0925_open_decisions.zh-TW.md`（**37 題 Q01–Q37＋O01–O19**，每題回一個字母）；審 staged、commit／push（Q33）；pluginval 等下載（Q14、Q37）；重新部署 VST3（Q35）；商品 v1.1 候選 `exports/products/clean_batch2_v1_1_candidate/`（入口 `CHANGES_v1_1.md`）。
- 下方「★ 2026-09-25 盤點新登記」一節已逐條更新成 WF0925 之後的狀態。

**2026-09-25 快照（現況盤點 + 月月 09-25 裁決）**：
- **盤點**：9 個 agent（6 路掃描＋3 個懷疑者逐條反駁），128 條發現：92 條屬實、36 條部分修正、0 條被推翻，另有懷疑者補抓 13 條漏項。
  結論 `reports/status_check_2026-09-25/STATUS_CHECK.zh-TW.md`；逐條證據 `reports/status_check_2026-09-25/APPENDIX_findings.zh-TW.md`（本檔引用寫成 `[區段:條目]`，部分修正的條目以「查證修正」為準）。
- **09-25 對 staged 樹重跑 GATE：全綠，每項數字都跟 09-15 基線相同**。這是 D9c 落地後第一次跑全套（09-15 整合卡跑在 D9b/D9c 之前）：
  ctest 4/4、pytest 270（264 passed＋1 skip＋5 xfail）、`--full` NO CHECKED FAILURES、`--selftest` 13 行全 PASS、`verify_score --all` 75/75（1 項既有豁免）、HostProbe 89 PASS 0 failures、位元不變 8/8 IDENTICAL（基準 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`）。原始 log 在 `reports/status_check_2026-09-25/gate_logs/`。
- **月月 09-25 裁決**：「先修文件，然後照 7 個 commit 切，剩下 AI 能處理的都處理掉」。
  (1) 盤點查到的過時文件先修，修正併入 c7 交接 commit；
  (2) **WF0914 成果 2026-09-25 依月月裁決分 7 個 commit 入庫（未 push；hash 見 `git log`）**，切法清單 `reports/status_check_2026-09-25/commit_lists/`；
  (3) ~~**WF0925 輪進行中**~~ **WF0925 輪已完工**（見上方 09-25（下）快照）：AI 能做的項目照慣例 staged 不 commit。
- **部署實況（跟舊文件寫的不同）**：系統上的 VST3 是 `C:\Program Files\Common Files\VST3\TsukiSynth_VST3_2026-09-10\TsukiSynth.vst3`，多了一層子資料夾；它是 09-10 23:46 的 build，**缺 D12 和 D9c**。
  另有兩份舊副本：`C:\Program Files (x86)\Common Files\VST3\TsukiSynth.vst3`（binary 07-12）、`%APPDATA%\VST3\TsukiSynth.vst3`（05-07）。Cubase 的外掛快取停在 08-22，指向已經不存在的路徑。
  上架母帶用的 CLI（sha256 `9123db8f…`）已備份到 `exports/renderer_archive/`（WF0925b 時 repo 外再放一份 `E:\TsukiSynth_renderer_archive\`，交接卡核對 sha256 相同；裁決包 O15）。
- **最要緊的新發現**：給愛麗絲全曲有 16 顆音的基頻被壓掉（A14 B-2 把力脈衝深零點搬到別的音高×力度），登記為 **D16**。其餘新待辦列在下方「2026-09-25 盤點新登記」一節。

**2026-09-15 快照（WF0914 輪，40 agents：Fable 規劃／Sonnet 工兵／Opus 稽核親自重跑）**：
月月 09-14 裁決「push+merge main + B7 開工 + 補 D9～D15」全部執行完畢。
- **push+merge**：09-13 五 commit + 09-14 交接更新（`a38bd6a`）已 push 並 merge `main`；**CI 三平台全綠**（macOS leg 首編 `IRLibrary.h`/`ParameterLayout.cpp` 過）。附帶抓到並修掉 09-07 起就在紅的 CI 缺陷：`physics.yml` 測試建置清單漏 `TsukiSynthSpectrumViewTest`（X4 教訓的 CI 版），fix=`766d21d`。
- **落地（當時 staged，稽核 PASS；2026-09-25 已分 7 個 commit 入庫，見 09-25 快照）**：B7P0 兩份溯源文件；B7P1 力鏈底層純函式+五條測試（**dumpModes 欄位已撤回**，見 B7 條目）；D10 文獻補摘；D12 舊 `reverb_ir_path` state 三態遷移（HostProbe 89 PASS）；D14 stem_verify 記憶體解耦（905 事件全量 1.65 GB 跑完，原 >28 GB；判定逐位元不變）；D13/D11 分析+裁決包（四輪稽核）。
- ~~**BLOCKED（合法完成，等月月裁決，見下）**：B7P1/B7P3（velocity proxy 換算）、D9（量測鏈矛盾）、D15（哨兵新語料打破 ≤1.18c 主張）。~~
  **→ 09-25 註：這三項已由下方 09-15～16 五項裁決全部解除**（B7＝路徑 C 乙案合法終點、D9 關閉、D15 選 A'）。`[docs-consistency:T1]`
- **整合卡全綠**：重建 `build/`，ctest 4/4、pytest 新基線 **270 個測試**（264 passed+1 skip+5 xfail，較 267 淨增 3）、`--full` NO CHECKED FAILURES、corpus 75/75、HostProbe 0 failures、位元不變 **8/8 IDENTICAL**（post_a14 基準）。
  （09-25 註：這張整合卡 09-15 02:53 跑完，早於 D9b（09-16 00:09）和 D9c（09-16 01:18）；兩張卡各自只跑了 GATE 1-5／1-6，沒跑全套 pytest 和 corpus。D9c 之後的全套重跑見 09-25 快照，數字相同。`[docs-consistency:I1]`）

**月月 2026-09-15 五項裁決（「五題全照建議」，已全部落地或排卡）**：
（09-25 註：原寫「已全部落地」不精確——B7 裁決包 §6 第 3 點要求的 TODO/ROADMAP 條目同步 09-25 才補上，見下方 B7 條目；D13 的註解/描述同步也還欠著。`[懷疑者補抓的漏項（docs-open）]`）
1. **B7 選「§5 路徑 C + 驗收基準 (a) 乙案」**：proxy 與 S 皆不裁決，B7 本輪合法終點=Phase 0 完成、Phase 1 部分完成（dumpModes 欄位撤回、五個純函式+測試保留入庫）、Phase 2/3 BLOCKED。裁決記錄 `reports/decision_packets/B7_phase2_and_open_items.zh-TW.md` §6。背景：稽核查證推翻規劃者代決——score `velocity` 實為 `base_velocity(role)×(MIDI/90)±微調`（`tools/midi_to_tsukisynth.py::velocity_for()`），非 MIDI/127。
2. **D9 選 (a)**：C++ lane 小卡在 `tests/audit_repro.cpp` 加外部 IR 注入點，用同一 K-02 量測鏈量 EchoThief 3 顆真實 IR（`external_data/ir/echothief/`，非商用授權，量測參考用）→ **WF0914-D9b 完工（GATE 1-5 PASS，2026-09-16）**：3 顆真實 IR 的 wet-vs-ALGO 落差 -28.5～-28.7 dB（僅差 0.24 dB，跟既有合成 IR 基準 -28.483 dB 幾乎重合，儘管 IR 檔本身寬頻能量彼此差 16.6 dB——證實落差是 ALGO/IR 演算法結構性差異、非個別 IR 檔案響度），裁決包 `reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md`，對齊方案（A/B/C）待月月裁決。**月月 2026-09-16 選項 A → WF0914-D9c 完工（GATE 1-6 PASS）**：`EffectChain.h` 對 IR wet 訊號加固定補償增益 `kIrWetMakeupGain=26.9f`（+28.58 dB，DECIDED CONVENTION，4 樣本平均落差反推），K-02 四組落差由 -28.483/-28.726/-28.487/-28.623 dB 收斂到 +0.112/-0.131/+0.108/-0.028 dB（皆落在 0±0.25 dB 內），位元不變 8/8 IDENTICAL、HostProbe 89 PASS 0 failures，證據 `reports/gate_outputs/wf0914_D9c_*.txt`。
3. **D11 選 C**：patch 存檔不落地（`reports/d11_string_scale_candidate.patch`，`git apply --check` 已驗）；**新登記「D11-F5 根因調查」卡**：定位候選修正下 F5 piano 殘餘能量 −63.9→−58.5 dB 退化的機制，查清後帶數字回來重開 A/B。裁決記錄在裁決包文末。（09-25：勾選項補在「2026-09-25 盤點新登記」。`[docs-consistency:T7]`）**→ 09-25 WF0925-F5 已完成根因調查**（`reports/d11_f5_root_cause_2026-09-25.zh-TW.md`，也附在 D11 裁決包檔尾）；要不要重開 A/B → 裁決包 Q16。
4. **D13 選 B**：主張域收窄已落地——新建 `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §1（water_gong=自由邊平板、非乳突鑼；2.0× 缺失是域限制非計算錯誤）；`PlateModel.h` 檔頭/score 描述的同步留待下次動那兩檔的卡順路做。裁決記錄在裁決包 §4。（09-25 查證：兩處都還沒改——`src/physics/PlateModel.h:25`、`scores/examples/water_gong_free.score.json:7`；勾選項補在「2026-09-25 盤點新登記」。`[docs-consistency:T7]`）**→ 09-25 WF0925-K1 已同步兩處**（R6 全套＋WAV 8/8 不變）。
5. **D15 選 A'**：主張域再收窄已落地——`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.5 新增「≤1.18 cent 只涵蓋持續段；放鍵/阻尼段已知誤差上界 ~7.2 cent」段；B' 不追。
**兩封信已寄出（2026-09-15，TU Berlin 授權請求＋Iowa 器材詢問），等回覆**；月月待辦剩：~~裝 Limbus 並啟用、Yamaha 裝好後叫 AI 清 Downloads 殘留~~。
（09-25 查證：Limbus 兩個 VST3 與 Yamaha Piano Sheet Converter 都在 **09-14 12:56 已安裝**。還剩兩件要月月回覆：Limbus 有沒有用金鑰啟用（磁碟上查不到）；`Downloads\不知道有沒有用`（共 614 MB，其中 Piano Sheet Converter 解壓殘留約 470 MB，其餘是安裝檔）要不要清、留哪些。`[docs-consistency:H5]`）

**2026-09-07 補記**：8/31 兩個 commit 登記（`a7413e5` 稽核修復批次、`cdf2017` 水鑼 Pitch Glide
buffer-size 缺陷已修＝稽核 §4-A 關閉）＋月月裁決批次（push/merge、requirements 加 pytest+mido、
A8 下載、UI 等功能做完再送設計、A13/A14/F-03 由 AI 查外部資料決定）——詳見 `HANDOVER.md` §0-2
（09-25 註：這是 09-07 版 HANDOVER 的小節，現版已經沒有，請看 `git show 98f346f:HANDOVER.md`。`[docs-consistency:H9]`）。

**2026-09-07～09 三輪 Workflow 快照（WF0907 / WF0908 / WF0909，施工卡在 `docs/workcards/WF09*.md`）**（**歷史快照**：這三輪成果 09-13 已 commit，後續看 09-15、09-25 快照。`[docs-consistency:T2]`）：
規劃者→Sonnet 工兵→Opus 稽核（親自重跑）；**稽核 PASS 才 `git add`**，~~**全部未 commit**，月月看 `git diff --cached`~~ **→ 09-13 已分 5 個 commit 入庫：`5c9cdb3`／`31eb7ae`／`9ae8ce2`／`27e8393`／`49b8542`（09-14 已 push、merge `main`）**。
- **已落地（當時 staged，09-13 已 commit）**：E1 CI 全量 pytest + pytest/mido pin；E5 `getTailLengthSeconds()` 接引擎 worst-case T60（3.45 s → 34/179/320 s）+ Custom 判斷式單一化；
  E8 schema 三份契約同步（388 突變體矩陣 0 不一致、corpus 75/75、converter raise 不 clamp）；E9 `--dump-modes` 支援 layered；
  E7 K-03 超 maxBlock 分塊（位元等價）+ K-02 量化；C11 拒答理由/規則直方圖；C12 `--analysis-dry` 預設 + provenance hash/diff；
  C10 重構+`measurement_selfcal.py` 入庫（1-cent 主張另議）；E10b 水鑼 glide 逐取樣（H6 五種 block size 位元相同）+ H7 user preset harness（選項 B，`src/ParameterLayout.h`）；
  **P3 F-03 落地**（`src/IRLibrary.h` 受管理 IR 庫 B＋、缺檔三態、UI/音訊單一真相 `getIRStatus()`、HostProbe 67 PASS）；P1 `tools/partial_verify.py`（A13 B+，informational，`gate_ready=false`）。
- ~~**等月月**~~：**A14 B-2 τc 音高律 patch** `reports/a14_tauc_keytrack_b2.patch`（報告 `reports/a14_tauc_keytrack_before_after.md`；7/8 位元不變只 physical_piano 變；月月 `git apply` 即落地）。
  **→ 已結：月月 09-10 放行，已 `git apply` 落地，稽核 PASS（見 A 區 A14）。**
- ~~**進行中（WF0909）**~~：C10B 估計器 ≤1 cent（月月選 B）；D8 兩首月光 `finger→wood_mallet`（月月裁決）；P4b A8 引用更正補完；P6 A8 補充來源（Weinzierl 2018 CC BY／Iowa 泰國鑼）。
  **→ 全部已結**：C10B 兩個家族六個候選全數否決，09-10 月月改選 A（見 C10）；D8 已落地（見 D8）；P4b、P6 已完成（`reports/gate_outputs/wf0909_P4b_citation.txt`、`wf0909_P6_supplement.txt`，09-13 隨 `27e8393` 入庫）。
- **規劃者代決（月月 09-07 委託，可推翻）**：A13=B+；A14=引擎缺陷（B-2 先做、B-1 等文獻）；F-03=B＋三態；K-02=C 維持現狀（IR 反而比 ALGO 小 28.5 dB，主因非 0.15，另立「IR 載入響度對齊」D 類項）。
- **月月 09-09 裁決**：C10=B；D8=wood_mallet；A8=無可商用校準資料集→私下對照參考（TU Berlin 實為 **CC BY-NC-SA**）；K-02 交 AI 評估。
- **新登記**：D9 IR 載入響度對齊（~~等真實 IR 檔量測~~ → 09-16 D9c 落地，**已關閉**，見上方五項裁決第 2 點）；D10 B-1 真槌力譜滾降文獻（Hall 1988／Chaigne & Askenfelt 1994 Part II 仍 403/付費牆未取得；**WF0914-D10 窮盡開放管道再確認：兩篇缺口文獻仍 403/付費牆；A14（09-08）已引用的 Russell & Rossing 1998（L1-16～L1-22）補摘與力譜/震波譜計算式直接相關的段落（非新來源），無顯式 dB/octave 數字，B-1 維持 A14 既有裁定的等文獻狀態**，見 `docs/HAMMER_CONTACT_SOURCES.md` §9）；D11 弦長/弦徑造成 B 偏高 ~~2.4～5.2×~~（R10 全 corpus，~~月月另裁~~）
  **（09-25 更正：「2.4～5.2×」查無出處，其實是非諧性係數 B 的舊數字，A13 已更正為 2.4～5.4；D11 裁決包 §3 改用 A14 §3.10 的「B 偏高 14–87 倍」，候選修正下 G6 由 86.4× 降到 18.7×。09-15 月月已裁 C，見上方五項裁決第 3 點。`[docs-consistency:T8]`）**；
  D12 舊 DAW state `reverb_ir_path` 無遷移（重開只會安靜留 algorithmic）**2026-09-15 WF0914-D12 完工，三輪稽核 PASS 已 staged（HostProbe 89 PASS、位元不變 8/8）**：
  `setStateInformation()` 在新 schema（`reverb_ir` 區塊）不存在時讀舊鍵，三態遷移（檔案存在→正常匯入，
  但**不**強制切 `fx_reverb_mode`（`switchModeToIR=false`，尊重 state 已還原的模式，比對 `git show 31eb7ae^`
  舊版本來就是 false，首輪誤設 true 已被稽核抓出並修正）；
  檔案不存在→F-03 缺檔態強制切回 algorithmic＋警告；新 schema 已存在→舊鍵忽略不重複匯入，並清掉舊鍵避免殘留），
  遷移後另修 `presetDirty` 被 `restoreDirty()` 蓋掉的問題（遷移一律 `presetManager.setDirty()`），
  HostProbe 新增三情境並補上 dirty flag 斷言（真實 VST3 ABI 合成 legacy state blob 餵 setStateInformation）0 failures，
  ctest 4/4、`--full` NO CHECKED FAILURES、8/8 位元不變（首輪＋修復後兩輪都測過）；證據 `reports/gate_outputs/wf0914_D12_*.txt`；
  B7 §2.2/§8 已依 Phase 0 資料更新（velocity→槌速三錨點；絕對 SPL 出處仍阻塞）。
- **UI 功能規格送設計端**：等 WF0909 收尾 + A14 patch 裁決後執行（月月 09-07：等所有功能做完）。
  （09-25 註：WF0909 收尾、A14 裁決這兩個前提都已滿足；但月月 09-07 的條件是「等所有功能做完」，算不算做完要月月自己認定。規格 v1.1 還寫著「IR 與演算法殘響差 28 dB 尚未對齊」，D9c 之後已不成立，送出前要先同步成 v1.2。勾選項見「2026-09-25 盤點新登記」。`[open-work:U2-send]` `[open-work:U1-spec-sync]`）

The deep-audit implementation fixes are on the branch. Historical Phase D–I decisions remain in `DEVLOG.md`; this file lists only current work and scientific gaps.

**2026-08-31 稽核修復輪**：codex 兩輪稽核的問題點已整理成診斷文件
`docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.zh-TW.md`（三個結構性病根 + 未修清單 +
我複驗後與稽核判斷不同的項目）。F-03 裁決包在
`reports/decision_packets/F03_IR_PRESET_RECALL.zh-TW.md`（~~待月月選 A/B/C~~ → 規劃者代決 B＋三態（月月 09-07 委託，見 `HANDOVER.md` §6）、已在 WF0908-P3 落地：`src/IRLibrary.h` 受管理 IR 庫＋缺檔三態，09-13 隨 `31eb7ae` 入庫。`[docs-consistency:T3]`）。

**2026-08-30 快照（~~最新~~ 歷史）**：**UI 走向重設計 + 密集複音驗證缺口部分補上**。
(1) 月月**否決**雙開門 UI 提案，裁定撇開現行 UI 既有元素、由設計端從功能重做
→ 新的設計輸入 `docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md`（只清點功能，不寫樣式）。
(2) 分支已全數 **merge → `main`**（月月明示授權），`main` = `b7e4330`。
(3) 旋律影片工具換月月指定的霓虹配色 + 左側固定音名尺（`--theme neon` 預設）。
(4) **裁決包選項 A 已實作並實跑**：`tools/stem_verify.py`（逐事件乾聲分軌 + 疊加證明），
給愛麗絲全曲拒答 **862 → 212**，疊加證明 ESTABLISHED。
兩個新發現：**殘響會把 melody_verify 的音高質心拉偏最多 9.5 cents**（現行 GATE 既有缺陷）、
**22 顆高音弱基頻需 harmonic-aware 判定**。主張域已更新
（`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8）。~~**stem_verify 相關檔案全部 unstaged 待審。**~~ → 08-31 已隨 `a7413e5` commit。`[docs-consistency:T8]`

（歷史快照）**2026-08-29**：**B1–B6 物理鏈全部 Done**，六場物理戰役收官。
B6 全卡完工（方案 B 絕對聲壓校準落地，月月裁決；對抗稽核五缺陷已修）；B7 卡已立
（第一原理力鏈，前置阻擋已解除，缺 velocity→m/s 映射資料）；轉譜層 GATE
`tools/score_vs_midi_verify.py` 補上驗證鏈最後缺口；corpus **73 → 75 檔**
（新增給愛麗絲 piano/cimbalom，首個授權全淨商品曲）。
**唯一擋 merge → `main` 的是月月的 UI mockup 視覺裁決**（`uiux/double_door_mockup.html`）。
剩餘待月月：UI 裁決、換源重製排程、A8、A10。工程缺口：D8（tongue_drum 40 dB 斜率）、
D1/D2、B7 Phase 0 資料。詳見 `HANDOVER.md`。

（歷史快照：2026-08-22 紅燈清零＋M10 收官＋A9 關閉＋C3 登記＋A12 修畢；
2026-08-24 B3 完工、Rule 10 報告待裁決 → 已於 08-26 放行並併入 `main`。）

---

# 待辦總表（2026-08-15 整理，2026-08-22 更新；2026-09-25 加「盤點新登記」一節並清掉過時勾選）

> 文獻依據與依賴關係見 [`docs/RESEARCH_INDEX.md`](docs/RESEARCH_INDEX.md)。
> 新 session 請先讀 [`HANDOVER.md`](HANDOVER.md)。
> 下面各項的細節在本檔後半段的原始條目裡，這裡只列「要做什麼」。

## ★ 2026-09-25 盤點新登記（WF0925 輪後逐條更新）

> 來源：`reports/status_check_2026-09-25/STATUS_CHECK.zh-TW.md`（結論）＋`APPENDIX_findings.zh-TW.md`（逐條證據；每行最後的 `[區段:條目]` 就是附錄裡的條目 id）。
> 分三類：**等月月裁決**／**AI 可做**／**等外部**。新的 D 類編號從 **D16** 起（09-25 查過：本檔 D1～D15 已用）。
> **WF0925 輪後（2026-09-25 交接卡更新）**：每條後面的「→」寫本輪做了什麼、證據在哪；`Qxx`／`Oxx` 是裁決包 `reports/decision_packets/WF0925_open_decisions.zh-TW.md` 的題號（每題回一個字母）。
> 本輪沒有任何卡 BLOCKED 或 RED。商品 lane 稽核 FAIL（1 條要修），相關條目標「商品稽核 FAIL，待修正輪」。
> 新基線：pytest **288 個測試＝282 passed＋1 skip＋5 xfail**、HostProbe **215 項**、AuditTest **110 條**（`reports/gate_outputs/wf0925_INTEGRATION.txt`）。
> **WF0925b 收尾輪後（2026-09-25 交接卡 HO2 更新）**：各條再用「→ **WF0925b**」補上收尾輪的結果；卡號與證據見 `docs/workcards/WF0925_README.md` §7。WF0925b 沒有卡 BLOCKED 或 RED，商品稽核複驗 PASS。
> 現行基線：pytest **307 個測試＝301 passed＋1 skip＋5 xfail**、HostProbe **215 項**、AuditTest **110 條**（`reports/gate_outputs/wf0925b_INTEGRATION.txt`；AuditTest 沿用 WF0925 整合卡，執行檔沒變）。裁決包現在是 **38 題 Q01–Q38**。

### 等月月裁決

- [ ] **給愛麗絲鋼琴版母帶去留**：clean_batch2 準備上架的這份母帶含 D16 那 16 顆弱基頻。先上架，還是等 D16 修好？AI 先交零點地圖數字。`[open-work:N1-fe16]`
      → **零點地圖已交（WF0925-N1）**：16 顆 FAIL 16/16 在力脈衝凹口內；商品只有這份受影響（揚琴版、AI Radiance、音效都是 0 顆；N1 只掃弦類引擎的事件）。
      報告 `reports/weak_fundamental_null_map_2026-09-25.zh-TW.md` §6 並列 A 帶已知限制上架／B 等文獻／C 第一原理研究／D 只改這首的力度；候選版 `PRODUCT_SHEET_v1_1.md` 已寫好「已知限制」那行。→ **Q15**
      → **WF0925b**：`PRODUCT_SHEET_v1_1.md` 的「0 顆」已補上範圍（N1 只查弦類引擎；43 個音效裡只有 14 顆弦類事件），`wf0925b_XF_verify.txt` V5。
- [ ] **D9c 要不要加硬 CHECK**：K-02 只印數字、不判定，把 `kIrWetMakeupGain` 刪掉，全套 GATE 仍會是綠的。
      「0±0.25 dB」出自 D9c 施工卡（D9b 實測展幅），**不是月月裁決的容差**；升成 CHECK 等於加新的 GATE 判準，屬 R2，要月月裁。`[staged-review:D9c-guard]`
      → **WF0925-K2 已加 D9c-guard**：`tests/audit_repro.cpp` 檢查 `kIrWetMakeupGain == 26.9f`（精確相等，不是容差；讀到 26.8999996，PASS），常數被刪或改會紅燈；K 稽核 mutation 驗過有牙齒。
      沒加的是響度那條（|IR−ALGO| ≤ 0.25 dB）：JUCE 升版改了 Convolution 正規化時只有它擋得住。→ **Q01**（守門寫法要不要改成 public 唯讀存取點 → Q01b）
- [ ] **pluginval＋Steinberg validator 重驗**：上次停在 08-06，之後改過 tail 快取、IR state、D12、D9c 都沒重驗。
      要下載 pluginval 並 build SDK validator，**下載需月月同意**（或修好 release CI 後 push 手動觸發）；月月同意後由 AI 執行。`[engineering-gaps:E2]`
      → 下載資訊已查（WF0925-Q1）：pluginval v1.0.4（`pluginval_Windows.zip` 2,408,590 B，要比對 CI 釘的 SHA256）；VST3 SDK 沒有 GitHub release，validator 要照 CI 做法 clone 釘住的 commit 自己建。→ **Q14**
- [ ] **VC++ runtime**：VST3 動態連結 MSVCP140／VCRUNTIME140 等，買家電腦沒裝 VC++ 可轉散發套件時 DAW 會載不進來。二選一：靜態 CRT（改 CMakeLists，走 R6＋8/8）或安裝包附 vc_redist。`[engineering-gaps:E4]`
      → WF0925-G1 的安裝包腳本 `tools/installer/TsukiSynth.iss` 已把兩種做法寫成註解區塊待選。→ **Q07**
- [ ] **VST3 Program 參數錯位**：host 看到的 program 格數在建立 instance 時就固定，但使用者 preset 會增減、又依名稱排序 → 自動化或 program change 可能載到別的 preset，換機器也可能對不上。建議 host 只看得到 27 個工廠 preset（UX 決定）。`[engineering-gaps:E7]` → **Q06**
- [ ] **IR 模式沒有任何輸出限幅**：D9c 補償後，IR 最壞單頻增益比 ALGO 預設高 4～9 dB（Python 複製版估計，仍在 ALGO 自己的可調範圍內）。接受現狀並寫進文件，或另開卡加限幅（會改渲染，走 R10）。`[staged-review:D9c-clip]`
      → WF0925-K2 另量到（描述用、非 GATE）：C4、力度 0.7 單音時有 3 個工廠 preset 峰值超過 0 dBFS（Copper Warm Strings (Body) +0.33、Ethereal Steel Bells +1.47、Bronze Water Gong (Body) +2.65 dBFS）。→ **Q05**
- [ ] **plugin↔CLI 一致性 GATE，還是把文案收窄**：物理 GATE 驗的是 CLI 路徑；plugin 的 `startNote()` 只跟 CLI 共用衰減律，激發、macro、BodyResonance、EffectChain 各自組裝，而「可稽核物理鏈」正是賣點。
      補 parity GATE（容差要走 §6 登記），或文案改成「CLI 渲染已驗證」。`[engineering-gaps:E3]` → **Q08**
- [ ] **R6 範圍要不要涵蓋 plugin 層**：`ROADMAP_PHYSICS.md` §1 第 6 條（R6）只列 `src/physics|engines|dsp|score/`；D12 改的 `src/PluginProcessor.cpp`、D9c 改的 `src/effects/EffectChain.h` 都不在強制範圍。ROADMAP §1 是月月的規則，只有月月能改。`[懷疑者補抓的漏項（docs-open）]`
      → WF0925-Q1 新查到：CLI 渲染也會用到 `src/effects/`（`ScoreRenderer.h:11` → `dsp/EffectsChain.h:3-5` include `SimpleReverb.h` 等），R6 字面沒列。→ **Q02**
- [ ] **B7 `hammerVelocityMps()` 在 MIDI 20 跳 2.3 倍**：<20 clamp 到 0.18 m/s，公式在 20 卻是 0.412 m/s（120 那端也有 +3% 小跳）。文件說「比照 interpAnchorsFlat」，實際不連續。
      函式目前沒有呼叫點，不影響渲染；B7 重啟時請月月選：取公式邊界值（連續），或保留實測極值並寫明不連續。`[staged-review:B7-clamp]` → **Q11**
- [ ] **D12 載入失敗分支的設計**：舊路徑檔案還在、但載入失敗（>30 s、讀不到、匯入失敗）時，照 `PluginProcessor.cpp:875-878` 註解寫明的既有設計：靜默不載、不留舊路徑線索、不跳警告，跟「檔案不存在」分支不一致。
      要不要改走缺檔三態＋警告，屬推翻既有設計；改了要跑 R6。`[staged-review:D12-failpath]`（行號是 WF0925-K1 修改前的；K1 改過這個檔） → **Q10**
- [ ] **重新部署 VST3、清舊副本**：commit 後用新 build 覆寫部署（要管理員權限），清掉 `(x86)`（07-12）和 `%APPDATA%\VST3`（05-07）兩份舊副本，再讓 Cubase 重掃並跑 `tools/cubase_scan_verify.py`。動系統資料夾要月月同意。`[open-work:G6-redeploy]` `[docs-consistency:H8]`
      → 三份舊副本的路徑、sha、大小 WF0925-Q1 已重查（標準位置 `Common Files\VST3\TsukiSynth.vst3` 目前不存在）。→ **Q35**
- [ ] **變現五項裁決**：售價、AI Radiance 署名、全曲版要不要放、聽人把關、賣家帳號（`exports/products/clean_batch2/PRODUCT_SHEET.md` §5）。
      **第 3 題前提已不成立**：「41 個削波樣本」是正規化之前的計數，母帶峰值 0.95、沒有平頂，全曲版可以直接放、不必重渲。建議連同音效包的 AI 揭露口徑一起裁；賣家帳號只能月月本人註冊。`[release-readiness:R3]` `[release-readiness:P5]` `[release-readiness:R8]`
      → WF0925-X2 候選版 `PRODUCT_SHEET_v1_1.md` 已把第 3 題標「前提不成立」、AI 揭露口徑寫成【待月月確認】的建議句。全曲版 → **Q25**、AI 揭露 → **Q21**、聽人 → **Q28**、售價與帳號 → **O01**。
- [ ] **音效正規化政策**：三個打擊音效（Rabbit Stomp、Spring Release、Shackle Slam）的峰值被開頭尖峰佔掉，比全包中位數小約 12～23 LU。維持全部 −1 dBTP，還是另附響度對齊版？尖峰算不算瑕疵要靠聽人。`[release-readiness:R5]`
      → WF0925-X1 做好 B 案 43 檔（`clean_batch2_v1_1_candidate/alt_loudness/`：最大瞬時響度 −10 LUFS、≤ −1 dBTP；21 檔撞到 −1 dBTP 上限，全包差距只從 23.0 縮到 18.3 LU；其他目標值只算數字、沒出檔）。→ **Q20**
- [ ] **專輯授權**：專輯 zip 只有一句授權、沒有 LICENSE 檔；要不要允許營利影片當背景音樂、上 DistroKid 要不要開 Content ID。`[release-readiness:R7]`
      → 本輪沒起草（X2 範圍只到音效包授權）。AI 可起草、要月月點頭 → **O05**；DistroKid 的 AI 表單與 Content ID 政策還沒查證 → **O18**。
      → **WF0925b-XF（稽核 PASS）**：專輯授權草稿 `exports/products/clean_batch2_v1_1_candidate/LICENSE_ALBUM_v1_1.txt` 已起草（標草稿、非法律意見；第 5 條影片／直播 BGM 並列 A 允許／B 只個人聆聽；不在任何 zip 裡）；
      DistroKid 查證寫在同資料夾 `DISTROKID_NOTES.md`：說明中心 12 篇都 HTTP 403，只拿到搜尋摘要——給愛麗絲是公版樂曲，依摘要不符合 Content ID 資格；Classical 依摘要不送 Apple Music；AI 表單有沒有「部分音訊」摘要互相矛盾。**K1～K7 要月月登入確認；第 5 條 A／B 要月月選**（證據 `reports/gate_outputs/wf0925b_XF_web_sources.txt`）。
- [ ] **BeamModel `*2` 阻尼加權去留**：寬頻化後變成「全音域一律 2 倍過阻尼」的純經驗係數。`src/physics/BeamModel.h:48` 註解自稱「已登記 TODO.md」，實際 09-25 才登記在這裡。前置是 D1；去留會改所有舌鼓渲染（R10）。`[open-work:B1-beam-x2]` `[open-work:G19-docs-stale]`
      → **前置 D1 已完成（WF0925-L1）**：文獻反對把 ×2 當物理機制，但無法判斷它代表的總量該不該留；另發現模型衰減完全不看舌片厚度（出貨樂譜 2.0／2.6／3.2 mm，文獻熱彈性差 2.56 倍、模型差 0）。`docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md` §4 列選項。→ **Q17**
      → **WF0925b-BR 已交「拿掉 ×2」的前後數字**（隔離副本，主工作樹沒動；DS／BR 稽核 PASS；描述用、非 GATE）：鋼基頻 T60 變長 1.15～1.80 倍（C4 16.39→26.86 s），頻率不變；corpus 39 份會變、36 份逐位元相同；8 首基準變 3 首；商品 clean_batch2 50 件變 36 件；`--full` 兩版都過（這類檢查分不出哪版像真舌鼓）；文獻 7 點現行 0、拿掉 ×2 1 點在範圍內。
      報告 `reports/beam_x2_option_b_before_after_2026-09-25.zh-TW.md`（選 B 的後續在 §6）、證據 `reports/gate_outputs/wf0925b_BR_*.txt`。Q17 選項 D「先 A（改註解）」那半沒做（要改 src）。
- [ ] **partial_verify 要不要升 GATE**：A13 原規劃「C10 選 A 即可翻成 GATE」，C10 09-10 已選 A；但 D15 A' 揭露放鍵段上界約 7.2 c（大於 ±5 c），前提變了。
      照原規劃只判持續段翻 GATE，或維持 informational 並改寫 `tools/partial_verify.py:514-518` 還寫著「待月月裁決」的理由字串。AI 先交全量數字。`[open-work:P3-partial-gate-premise]`
      → **全量數字已交（WF0925-V1）**：5,428 個 partial 格中 PASS 4577／FAIL 849／UNVERIFIED 2；FAIL 多數來自期望值慣例（工具以第 0 根弦為準，三弦平均高約 +5 c）。`gate_ready` 理由字串 WF0925-P1 已更新（同檔 docstring 與報告 caveats 還是舊說法，O16）。→ **Q18**
      → **WF0925b**：docstring 與 `caveats[0]` 已由 TF 改成現況（稽核 PASS）；EARFREE §8.6 已由 DS 寫入全量數字與「期望值取第 0 根弦、3 弦平均約高 +5 c」。工具說明裡寫明期望值慣例那半還沒做（Q18 A 案）。
- [ ] **ROADMAP §6 補登與 R7 措辭**：onset ±10 ms（C3-b 委託 AI 自定，08-20）和量測器自證 1.0 c（月月 08-30 訂）在用，但沒登記進 §6；數值不變，只補登記與出處。
      R7 字面寫「留 unstaged」，實際流程是稽核 PASS 後 `git add`，措辭也請月月定。`[docs-consistency:P2]` `[docs-consistency:P3]` → **Q03**、**Q04**
      → WF0925b-DS 只在 ROADMAP `:170-171` 的待裁註記加了指向 Q02／Q03，§1 十條原文與 §6 整節一字未改（稽核對 HEAD 版 diff 過），照舊等裁。
- [ ] **UI 功能規格送誰、合成器線走不走**：功能算不算「做完」、找哪位設計端，請月月一次決定（規格 09-25 已同步成 v1.2，見下）。合成器本體上架（安裝包／手冊／demo／DRM）的 go/no-go 也掛在這裡。`[open-work:U2-send]` `[open-work:M6-synth-phase2]`
      → 送誰 → **O02**；合成器發行相關的裁決拆成 Q19、Q29–Q32（安裝包、EULA、授權文件 WF0925-G1 已起草）。
- [ ] **缺檔警告措辭**：F-03 規定的「音量會和 IR 模式不同」（`src/PluginProcessor.cpp:846` 英文版）在 D9c 之後已不準確，只剩音色不同。改字串等於改 F-03 規格措辭。`[open-work:U3-ir-warning]`
      → **裁決包沒收這一題**（WF0925-Q1 漏列），仍在這裡等月月裁；UI 規格 v1.2 已附建議文字。行號是 K1 修改前的。
      → **WF0925b：已補進裁決包，題號 Q38**（A 改成 UI 規格 v1.2 的建議文字／B 月月自訂／C 維持）。staged 版行號：中文 `src/PluginProcessor.cpp:901`、英文 `:902-904`；沒有測試斷言這段文字。
- [ ] **變現計畫與商品資料的去處**：repo 是 PUBLIC，未追蹤的 `docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md` 含售價，不宜 commit；要移出 repo 或加進 `.gitignore`。商品文字檔（授權、文案、腳本、catalog）要不要搬進受版控的位置。`[staged-review:S-monetize]` `[release-readiness:R10]`
      → **Q34**（另含：staged 檔裡 32 檔共 232 行含本機路徑 `C:\Users\admin`、盤點資料夾要不要進版控）。
      → **WF0925b**：新進的證據一律用 `<REPO>`／`<SCRATCH>` 代稱，X1／X2 那 15 檔也去掉了本機路徑（24 處）；交接卡重掃 staged，現在是 49 檔共 309 行（全是 WF0925 那批），細節見裁決包 Q34 的 WF0925b 行。
- [ ] **小事**：Limbus 有沒有用金鑰啟用；`Downloads\不知道有沒有用` 約 470 MB 殘留要不要清；A10 Score 控制台實操；調音器目視可讀性（見 Before merging 段）。`[open-work:Y1-small-actions]` `[docs-consistency:Y1]`
      → **O04**、**Q36a**（WF0925-Q1 重查：資料夾共 613.5 MiB，其中解壓殘留 467.9 MiB；C 槽剩約 20 GB）。
      → **WF0925b**：C 槽現在只剩約 **12 GB（98%）**；本輪暫存大小見裁決包 Q36 的 WF0925b 行（`output/wf0925/` 5.2 GB、`output/wf0925b/` 1.9 GB、scratchpad 8.9 GB、`E:\tsuki_wf0925_V1\` 17 GB）。
- [ ] 四季／月光換源要不要排程（擋專輯 Vol.2；見 A 區「古典曲目換源重製」）。`[open-work:C1-resource]`
      → **O03**（N1 附帶發現：四季的 string＋bow 有 5,682 顆落在同一種凹口裡，換源後若沿用 bow 會帶著同樣問題，建議登記新 D 項）。

### AI 可做（WF0925 輪處理結果；WF0925b 收尾輪的結果補在各條「→ WF0925b」）

- [x] **D16 零點地圖**（WF0925-N1，R 稽核 PASS）：A14 B-2 落地後，舊的 22 顆（G5×19 等）全轉 PASS，但力脈衝深零點搬到別的音高×力度：E5@0.278×9、A5@0.427/0.452×4、A6@0.427×2、A♯6@0.427×1。
      用 `--dump-modes` 掃四種激發 × MIDI 21–108 × 力度共 27,808 格，不改 src。16 顆 FAIL 16/16 在凹口內（−14.9～−24.5 dB）；真正分開 PASS／FAIL 的是基頻絕對位準（FAIL ≤ −72.1、PASS ≥ −67.2 dBFS，對既有 −70 dBFS 門檻 677／16 零誤判，樣本內）；凹口內事件數 A14 前 44、現在 47。
      證據 `reports/weak_fundamental_null_map_2026-09-25.zh-TW.md`、`reports/gate_outputs/wf0925_N1_*.txt`。**D16 本身仍開放**：引擎面修法併入 A14 B-1（等文獻）或 scratch 原型，母帶去留 → Q15。`[open-work:N1-fe16]` `[open-work:E1-a14-b1]`
- [x] **D11-F5 根因調查**（WF0925-F5，R 稽核 PASS；在 `git archive HEAD` 的隔離副本套 patch，主工作樹沒動）：F5 piano −63.9 → −58.5 dB **全部**來自 C4 基頻 T60 變短（4.1425 → 2.6733 s；琴橋損耗 ∝ 弦徑²×弦長，1.70 倍），衰減越快，基頻譜線裙邊漏出 ±3% 帶外越多。
      「泛音滑出判定窗」排除；多弦 beating 不是變化原因。新事實：現行引擎只把 F5 探針弦徑 0.8 → 1.0 mm 就 −59.5 dB FAIL。
      證據 `reports/d11_f5_root_cause_2026-09-25.zh-TW.md`、D11 裁決包檔尾、`wf0925_F5_*.txt`。重開 A/B → **Q16**。`[open-work:D11-F5]`
- [x] **D13 後續同步**（WF0925-K1，K 稽核 PASS）：`src/physics/PlateModel.h` 檔頭、`scores/examples/water_gong_free.score.json` 的 `meta.description` 已補「自由邊平板、不是乳突鑼、2.0× 附近沒有模態是域限制」（引 `ENGINE_DOMAIN_CLAIMS` §1 與 `wf0914_D13_plate_ratios.txt`）。R6 全套＋WAV 8/8 位元不變。`[open-work:D13-sync]` `[staged-review:D13-sync]`
      （`docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md:28-30`「同步備忘：尚未帶上這段聲明」還沒改，交接卡權限外，見 `WF0925_README.md` §6。）→ **WF0925b-DS 已改成「K1 已同步」**（DS／BR 稽核 PASS，`wf0925b_DS_changes.txt`）。
- [x] **release-physics.yml 修正**（WF0925-P1，P1 稽核 PASS；staged）：建置清單補 `TsukiSynthSpectrumViewTest`、`TsukiSynthHostProbe`；`unittest discover` 改 `python -m pytest tests -q`；加 HostProbe 執行步驟與 log 上傳。`[staged-review:CI-release]` `[engineering-gaps:E1]`
      **還沒在 GitHub 上跑過**（要 push 後手動觸發，Q33）。另外 P1 稽核查到既有問題：pwsh 多行 `run:` 只看最後一個 exit code，這一步的 ctest／pytest 失敗會被後面的指令蓋掉 → **Q12**。
- [x] **Q12 CI exit code 遮蔽**（WF0925b-TF，稽核 PASS；月月 09-25「都處理掉」授權下**先照建議 A 做、可推翻**；staged）：兩支 workflow 共 14 個多行區塊逐一檢查，每行原生指令後面補 `if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }`；HostProbe 移到各自 job 最後（release 的 corpus job 改看 `cli_uploaded`）；HostProbe 註解改成現況。
      本機照 runner 包法模擬「只讓一個指令失敗」：改前 12 種被蓋掉 → 改後 0 種。證據 `reports/gate_outputs/wf0925b_TF_q12_yaml.txt`、`wf0925b_TF_q12_pwsh_sim.txt`、`wf0925b_TF_audit.txt`。
      **還沒在 GitHub 上跑過**：push（Q33）後看 `physics.yml` 那次 run，再手動觸發一次 `release-physics.yml`。
- [x] **D15 xfail pin 改成非 xfail**（WF0925-P1）：5.2304／7.2055 與原本沒人用的 hold-out 持續段 1.0840 都搬到非 xfail 測試（沿用既有 <5e-4 比較精度）；strict xfail 只留「≤1 c」判定；docstring 過時的「card BLOCKED」、不存在的檔名已修。稽核反例：pin 改 0.001 → 3 條都紅。`[staged-review:D15-xfailpin]`
      代價：selftest 測試檔本機單檔約 5m46s → 7m45s（CI 每次多約 2 分鐘）。
- [x] **B7 殘留註解**（WF0925-K1）：`src/physics/HammerImpulse.h` 三處（原 :334、:342-343、:513）改成「目前沒有呼叫點（B7 09-15 裁決撤回），重新接回前先解 §1.1」。純註解，R6 全套＋8/8。`[staged-review:B7-residual]`
      （同檔 :422、:471 還有兩處泛指 call site 的歷史描述，不在卡上的行號內、沒改。WF0925b 不改 src，照舊沒改，列在 `WF0925_README.md` §7-8。）
- [x] **UI 功能規格同步 v1.2**：**09-25 盤點後的文件修正已完成**（隨 c7 `18430c4` 入庫；不是 WF0925 卡做的，本條原本漏勾）：`docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md` → v1.2，28 dB 改標結案並寫明適用條件、補 D12 遷移三種結果。`[open-work:U1-spec-sync]`
- [x] **partial_verify 全曲 905 顆實跑**（WF0925-V1，R 稽核 PASS）：informational，`gate_ready=false`。stem_verify 677／16／212 跟 D14 逐顆相同；partial 5,428 格 PASS 4577／FAIL 849／UNVERIFIED 2（848 條 FAIL 偏高，中位 +5.53 c）；D16 那 16 顆用泛音反推基頻 16/16 PASS（−3.56～+1.33 c）。
      證據 `reports/partial_verify_full_2026-09-25.zh-TW.md`、`wf0925_V1_partial_*.txt`。期望值慣例與升 GATE → Q18。`[open-work:P2-partial-full]`
- [x] **loop 非整小節**（WF0925-X1；README 說法 WF0925b-XF 修正，商品稽核 PASS）：`exports/products/clean_batch2_v1_1_candidate/loop_ready/` 做好 6 檔（裁到整小節、尾巴疊回開頭；長度誤差 0 樣本；整體降到 −1.000 dBTP）。原版沒替換。`[release-readiness:R4]` `[open-work:M4-loop-seam]`
      ~~**商品稽核 FAIL，待修正輪**~~：README 寫 loop-ready 檔「跟原版每 N 小節重播逐樣本相同」說太滿（交付檔多了整體增益 −0.55～−0.77 dB 和 24-bit 捨入）。附哪一版 → **Q26**；接縫會不會喀一聲要聽人（Q28）。
      → **WF0925b-XF 已修**：README 改成「套增益前逐樣本相同；交付檔跟自己拿原版重播不是逐位元相同（原版小聲 0.03～0.05 dB）」；6 個 loop 用 24-bit 整數全量重算，跟原版重播最大差 26,826～44,774 LSB24。證據 `reports/gate_outputs/wf0925b_XF_loop_facts.txt`、`wf0925b_XF_recheck.txt`。AI 部分做完，剩 Q26／Q28。
- [x] **音效包授權漏洞與 Fab**（WF0925-X2；同一條 README 措辭 WF0925b-XF 修正，商品稽核 PASS）：`LICENSE_SE_PACK_v1_1.txt` 草稿（英／繁中／日，標明草稿、非法律意見；補上只授權給從授權通路取得的人、禁止訓練或微調 AI、Content ID 與開源 repo 各 A/B 案、遊戲內嵌界線、違約終止）＋`FAB_PLATFORM_NOTE.txt`＋不附自訂 LICENSE 的 Fab 版 zip。原版沒替換。`[release-readiness:R6]`
      ~~**商品稽核 FAIL，待修正輪**（同一條 README 措辭）~~ → WF0925b-XF 已修（重打 zip：SE 一般版 `50749a0e…`、Fab 版 `082b8e69…`，只有 README 成員變；`x2_verify.py` 134/134，`wf0925b_XF_verify.txt`）。AI 部分做完，採不採用 → **Q22**、Fab 做法 → **Q23**；Fab EULA 頁回 403（機器人驗證）沒讀到。
- [x] **第三方授權聲明檔**（WF0925-G1，R 稽核 PASS）：新增 `THIRD_PARTY_NOTICES.txt`（12 個元件＋PreSonus 擴充，含 VST3 SDK MIT、SheenBidi Apache 2.0、IBM Plex SIL OFL 1.1 全文，逐字核對 ALL VERBATIM）；`LICENSE` 改「registered trademark」並更新 JUCE Starter 描述（第 1–19 行條款不動）。`[release-readiness:S4]`
      3 項查不到、標「待確認」：json.h 上游版本、libogg 版本、IBM Plex 是哪個 release。
- [x] **JUCE 8 EULA 查證**（2026-09-25 已完成）：JUCE 8.0.12；Starter 年營收 US$20k 以下免費、可閉源，沒有 splash 或署名要求，跟 `LICENSE` 一致；營收保守要把合成器、音效包、專輯合計。Starter 要不要到 juce.com 註冊查不到定論（見 A7）。`[release-readiness:S4]` `[open-work:M5-juce-eula]`
      → WF0925-G1 寫成 `docs/legal/JUCE8_LICENSE_REVIEW.zh-TW.md`（含升級價、超過門檻的後果、JUCE 9 EULA 對照）；註冊與收入怎麼算 → **Q31**。
- [x] **外掛 16 voice 搶音量測**（WF0925-V1，**照程式碼規則推算，不是外掛實測**）：正常彈法 50 件商品 0 件超過 16 顆（給愛麗絲最多 12）；75 首 corpus 3 首超過（都不是商品：月光全曲 FM 196、月光舌鼓 20、混合版舌鼓部分 20）；假設全程踩延音踏板 4 件商品超過；一顆 Cimbalom voice 約 1.37～2.71% 單核。
      證據 `reports/voice_pool_occupancy_2026-09-25.zh-TW.md`、`wf0925_V1_voice_pool_*.txt`。加大 pool／寫進主張域／補外掛實測 → **Q09**。`[open-work:P1-voice-steal]`
- [x] **D1 梁／板阻尼文獻補搜**（WF0925-L1，R 稽核 PASS）：見上方 BeamModel `*2` 條與 D 區 D1。`[open-work:R-D1]`
- [~] **D9c 常數註解補依賴說明**：**D9c-calib 那半已做**（WF0925-K1：`EffectChain.h` 註解補「對齊參考＝ALGO 預設 size 0.5、未設 T60」與其他 size／T60 的估計差）。
      **E18 那半沒做**：「約 18.06 dB 來自 JUCE Convolution 的 0.125 正規化、JUCE 升版前要重跑 K-02」還沒寫進註解（純文字；也可以用 Q01 的 C 案寫進「升級 JUCE 檢查清單」）。`[engineering-gaps:E18]` `[staged-review:D9c-calib]`
      → **WF0925b-DS 寫進了 D9 裁決包檔尾（E18 段）**：`juce_Convolution.cpp:623-629`、`:628`（`return 0.125f / std::sqrt (…)`）、`:789-790`、`.h:240-242`，20·log10(0.125)＝−18.06 dB，升 JUCE 前要重跑 K-02，以及 +28.58 vs 20·log10(26.9)＝28.595 dB 的用詞備註（DS／BR 稽核核對行號與數字）。**`src/effects/EffectChain.h` 的註解本身還沒改**（改 src，要另開卡），所以這條維持 [~]。
- [x] **測試補強（小）**：27 個工廠 preset 回歸（WF0925-K2，放在 HostProbe：paramID 都解析得到、名稱對得上、C4 渲染全是有限值，27×4＋1 條負對照＝109 條；峰值與靜音門檻沒加，屬新判準）；D14 `read_wav_header`／`StemArrayStream` 單元測試（WF0925-P1，`tests/test_stem_stream.py` 17 個，5 種突變全抓到）。`[engineering-gaps:E16]` `[staged-review:D14-tests]`
- [~] **工程小修（會動 src/CI）**：`[engineering-gaps:E5]` `[engineering-gaps:E8]`
  - [x] HostProbe 接進 CI（WF0925-P1：`physics.yml` Windows job 與 `release-physics.yml`；push 後才驗得到）。
  - [x] HostProbe 不依賴工作目錄（WF0925-K2：cwd → `TSUKI_REPO_ROOT` → exe 往上找；整合卡在 `output/wf0925/INT` 跑 215／0）。
  - [ ] HostProbe 不碰真實 `%APPDATA%`（要改 `IRLibrary`／`PresetManager` 讀環境變數，改 src）→ **O09**。
  - [x] `render_wf_scores.py` 加 `--outdir`（WF0925-P1；不帶時行為不變）。
  - [x] Cimbalom 每個音在音訊執行緒建一次 `juce::String`（WF0925-K1 E8：改成 static 常數，沒選「快取 Material* 指標」；K 稽核用 malloc 計數探針實測 5 種引擎情境 0 次、負對照每個 note-on 1 次）。即時音訊安全檢查要不要做成正式 GATE → **O08**。
- [x] **WF0925 另外做完的（盤點 §3-4／§4 的工程項）**：
  - E9 tail 快取（K1）：`getTailLengthSeconds()` 只讀 20 Hz Timer 在訊息執行緒算好的 atomic 值；H8 四個 tail 值改前改後逐字相同。參數變動最多晚 50 ms 反映，沒在真的 DAW 上驗過。
  - E14 版本欄位（K1）：plugin state 寫 `state_version=3`，preset 讀 version（比 2 新的照樣載入、拒絕覆寫）。state 格式一旦進客戶專案就是永久相容包袱 → **O14**（知情確認）。
  - E15 IR 庫修復（K1＋K2）：庫檔雜湊不符時寫暫存檔、驗雜湊、原子替換；SHA-256 已知答案 3 組（"abc" 與 448 位元訊息對 FIPS 180-2 原文；空字串那組原文沒有、只有 hashlib）。兩套 SHA-256 要不要統一 → **O12**。
  - `find_cli` 優先挑 Release、印出選到的 CLI；`melody_roll_video.py` 的 ffmpeg 找法（P1）。`crossplatform_verify.py` 等還在看 mtime → **O16**。
- [x] **O16 tools 小修六項**（WF0925b-TF，稽核 PASS；staged）：`crossplatform_verify.py`、`test_dump_modes_layered.py` 的 find_cli 改成跟 physics_verify／verify_score 同一條規則（Release 優先、不看 mtime）；`stem_verify` 讀得懂 WAVE_FORMAT_EXTENSIBLE（不支援的格式照樣丟 ValueError）；`render_wf_scores.py --cli` 先轉絕對路徑（相對路徑 8/8 IDENTICAL）；`stem_verify`、`partial_verify` 加 `--cli`（指到不存在的檔 exit 1）；`partial_verify` docstring 與 caveats 改成現況；release 網格「0 拒量」從 strict xfail 搬到一般測試（原條件照搬）。
      突變 11/11 抓到；pytest 288 → 307（+19：stem_stream +12、stem_verify +7；刪 0）。證據 `reports/gate_outputs/wf0925b_TF_*.txt`。還剩兩條小事（sustain 網格的 0 拒量、`melody_verify.verify()` 的 `cli` 參數）列在 `WF0925_README.md` §7-8。
- [x] ~~**還沒做、AI 可以接著做（不需裁決）**~~：商品 lane 修正輪（README 措辭、秒數捨入兩次、真峰值全精度數字註明量測法、「0 顆」補範圍，修完重打 zip、重跑 `x2_verify.py`，稽核 PASS 後才 stage X1／X2 的 15 個證據檔）；交接卡權限外的文件同步（`docs/workcards/WF0925_README.md` §6 逐條列）。
      → **WF0925b 已做**：商品修正輪（XF，稽核 PASS，`x2_verify.py` 134/134，24 個證據檔已 stage）；文件同步（DS，§6 裡 9 條已處理、1 條處理一半，逐條狀態標在 §6）。
- [ ] **WF0925b 之後還能接著做、不需裁決的**（細節 `docs/workcards/WF0925_README.md` §7-8）：
      要改 `src/`（另開 C++ 卡、照 R6 跑全套）：`HammerImpulse.h:422`／`:471` 歷史描述、`EffectChain.h` 的 E18 註解；CLI 輸出路徑超過 Windows 260 字元上限時 exit 1（要不要支援長路徑另裁，現在 `--workdir` 用短路徑就好）。
      文件：`docs/KNOWN_LIMITS_INDEX.zh-TW.md` 指向本檔的行號是照 HEAD 算的（本檔已改寫兩次），要重對或在檔頭註明；voice_pool 報告 §1 行號；EARFREE `:371` 補一句「caveats 已由 WF0925b-TF 更新」；Q18 A 案在工具說明寫明期望值慣例。
      tools：`melody_verify.verify()` 加 `cli=None`；sustain 網格的 0 拒量搬出 strict xfail。
      商品 lane：下一輪稽核重跑前把 `output/wf0925/X_audit/xa_zip_text.py:262` 寫死的舊字面值改成讀 README；`CHANGES_v1_1.md` §2.2 三列舊阻尼措辭（內部檔）。

### 等外部

- [ ] **兩封信的回覆**（TU Berlin 指向性資料商業授權／Iowa MIS 泰國鑼器材，09-15 寄出）：repo 沒有回覆記錄；收到時轉給 AI 登記。`[open-work:W1-letters]`
      → WF0925-G1 已把兩封信的狀態行改成「已寄出（2026-09-15，依月月記錄），等回覆」；標題行還寫「信件草稿」。→ **WF0925b-DS 已把標題行改成「信件 1／2（已寄出 2026-09-15）」**。回覆仍然沒有。
- [ ] **付費牆文獻**：D10（Hall 1988、Chaigne & Askenfelt 1994 Part II；擋 A14 B-1 和 D16 的引擎修法）、D5（銅鑼 JCIE 2005）、Rossing & Shepherd 1982（D13 選項 A 的前提）、B7 驗收基準 (a) 的絕對 SPL 出處（Goebl Fig. 2.20／Roginska 2013／Meyer）。月月若有機構帳號可以一次代取。`[open-work:W2-paywall]`
      → WF0925-L1 另外拿不到的：D4 舌鼓 ICSV27 全文（15 條路徑都失敗；月月可用瀏覽器開 `https://unige.iris.cineca.it/bitstream/11567/1063604/1/full_paper_1117_20210430223100647.pdf`，或寫信向作者要）、Alon 2015 York 碩士論文（超過 WebFetch 10 MB 上限）、Zoghaib & Mattei 2013（HAL 防爬蟲）、Van Eysden & Sader 2007（網站憑證錯誤）。下載請求 → **Q37**。
- [ ] **D7 實體試體量測**：文獻買不到，只能自己量（見 D 區 D7）。`[open-work:W2-paywall]`
- [ ] **聽人把關**：品質美感只能靠外部聽人。建議列成約 15 分鐘的定點清單：3 個打擊音效的開頭、6 個 loop 的接縫、Gate Open Dark 的 overdrive、D16 那 16 顆。要不要花錢找人由月月裁（變現第 4 題）。`[release-readiness:H1]` `[release-readiness:S6]`
      → WF0925-X2 已做好試聽包 `clean_batch2_v1_1_candidate/packages/TsukiSynth_listening_kit_v1_1.zip`（約 7 分鐘音檔、22 題英文是非題、約 15 分鐘作答）。→ **Q28**

## 🔴 0. 紅燈（優先於一切，2026-08-16）

- [x] **X1 修 B1 引入的 `audit_repro` 回歸** — **2026-08-16 月月裁決 (a)，已修，本機回綠（未 commit，R7）**。
      原症狀：CI run `31933324875` 紅燈，本機重建測試 target 後同樣三項 FAIL：
      `Semantic-order regression fixtures render successfully`／`Permuting simultaneous events preserves the exact WAV bytes`／`Inserting a zero-velocity event preserves the exact WAV bytes`。
      **根因**：B1 在 `CimbalomEngine.h` 寫死 `kBridgeSoundboardMaterialKey="wood_spruce"` 且查表 fail-closed
      （**四處**呼叫點，非三處：`CimbalomEngine.h:133` → `return`、`ScoreRenderer.h:183` → `continue`、
      `:704` → `return false`、`:999` → `return 0.0`），
      但 `tests/audit_repro.cpp` 的測試專用材質 DB 只有 `steel` → 渲染放棄 → 連鎖失敗。
      **裁決理由**：fail-closed 守衛本身是對的——「沒有共鳴板材質的 DB」本來就是不完整的 DB，
      守衛正確地把它擋下來。這是**測試 fixture 的缺口**，不是設計缺陷。
      **修法**：`tests/audit_repro.cpp::loadTestMaterial` 補進 `wood_spruce`，數值逐字照抄
      `data/materials.json`（Rule 4 可溯源，且不製造第二份會漂移的物理常數來源）。
      **GATE**：三 target 全重建（X4 規約）exit 0 → `ctest` 3/3 Passed → `TsukiSynthAuditTest.exe`
      直接執行確認三項具名 CHECK 皆 `[PASS]`、`PASS (0 failures)`。
      `git diff --stat` = `tests/audit_repro.cpp | 26 +++-` 單檔，**未動 `src/`**
      → R6 未觸發、**Rule 10 未觸發（無任何渲染輸出改變）**、R2 未動容差。
      **未了**：本項只解紅燈，不解「共鳴板材質該不該可注入」的結構問題——那併入 A11 一起裁決（見 A11）。
- [x] **X2 修 macOS 建置失敗（可攜性）** — **2026-08-20 已修（委託授權，見 C3-b），本機全綠，未 commit（R7）**。
      原因：`std::cyl_bessel_j`／`_i` 是 C++17 數學特殊函式，libstdc++/MSVC 有、libc++（Apple）沒有。
      **修法（不縮小 GATE 範圍，R3）**：新增 `src/physics/BesselPortable.h`（A&S 9.1.10/9.6.10 升冪級數，
      驗證域 order 0..8 / x 0..16 依 PlateModel 實際使用域推導，域外 fail-closed NaN）；
      `PlateModel::besselJ/besselI` 以標準特性巨集 `__cpp_lib_math_special_functions` 切換——
      有 std 的平台照走 std::（**Windows 渲染位元零改變已用前後 SHA256 證明 → Rule 10 不觸發**），
      僅 libc++ 走 fallback。
      **GATE**：錨點測試（scipy 獨立值 + A&S 對照，所有平台都跑）PASS；
      Windows 全域 grid 對照 std:: 最大偏差 2.1e-11（界 1e-10，一階原理推導）PASS；
      域外 5 哨兵 NaN + 正控制 PASS；三 target 重建 + ctest 3/3 + `--full` NO CHECKED FAILURES。
      證據 `reports/gate_outputs/x2_bessel_portability.txt`。
      **未了**：macos-14 leg 實際轉綠需 push 後 CI 證明（併入 A5）。
- [x] **X3 跨平台實測數字已取得** — **2026-08-21 push 後 CI run 32446987833 三平台全綠**（macos leg
      = X2 的 BesselPortable 首次實戰成功）。實測：max |delta| ≤ 5 LSB @24-bit、delta RMS ≤ −125.8 dB
      re signal、spectral ≤ 0.0019 dB、pitch 全部 +0.0000 cents。
      證據：`reports/gate_outputs/x3_crossplatform_first_numbers.txt`。
      → **C3 完成（2026-08-22 月月裁決「照提案登記」）**：`scores/crossplatform_tolerance.json` 已建
      （−120 dBFS / −120 dB re signal / 0.01 dB / 0.01 c）+ ROADMAP §6 決定性列已更新，
      `cross-platform-compare` 自此為**阻斷式 GATE**。selftest 全過 + 同機 compare exit 0 驗證生效。
- [x] **X4 施工卡與流程補上「跑 ctest 前必先重建三個測試 target」** — **2026-08-24 完成**。本輪 B1 的 `b1_ctest_all.txt`「3/3 passed」
      是**測到未重建的舊 binary**，對抗驗證的 GATE 視角「獨立重跑」也踩同一個坑。
      規約：`cmake --build build --config Release --target TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest` 之後才跑 `ctest`。
      已加進 `docs/workcards/` 六張卡（B1–B6）的 GATE 段：已完工的 B1/B2 用「2026-08-24 事後補記」註記形式，
      未施工的 B3–B6 直接融入 GATE 清單表格前的強制說明。未來所有新卡沿用同一段規約文字。
      （09-25 註：上面「三個測試 target」是 08-24 當時的原文。現在 CMakeLists 有**五個**測試 target：Audit/Tuner/PhysicsModels/SpectrumView 四個註冊了 ctest，HostProbe 刻意不註冊。
      只重建三個會讓 `spectrum_view_repro` Not Run——09-07～14 CI 紅燈就是這個原因（`766d21d` 修 `physics.yml`；`release-physics.yml:45` 還沒修，見「2026-09-25 盤點新登記」）。`[docs-consistency:R2]`）

## A. 等月月決定（AI 不能自己動）

- [x] **A13 partial GATE 的主張域** — **2026-09-08 規劃者代決 B+（月月 09-07 委託）**：只驗 partial 頻率內部一致性（±5 cents 既有容差）、不立振幅 GATE、`B` 對照寫成非 GATE 報告；工具 `tools/partial_verify.py`（WF0908-P1）已入庫，`gate_ready=false` 直到 C10B 量測器自證達標。
      （09-25 註：C10B 候選全數否決、09-10 C10 改選 A，這個條件不會再達成；A13 裁決包原本寫「C10 選 A 即可翻成 GATE」，但 D15 A' 揭露放鍵段上界約 7.2 c，前提又變了。要不要升 GATE 待月月裁，見「2026-09-25 盤點新登記」。`[open-work:P3-partial-gate-premise]`）裁決包 `reports/decision_packets/A13_partial_gate_domain.zh-TW.md`。原始記錄：2026-08-30 新增。`stem_verify` **完全沒有實測 partial
      的頻率或振幅**（`--dump-modes` 的 partials 只用來預判基頻帶污染），因此目前
      **不可宣稱「泛音已驗證」**。要不要立 partial GATE、以及它的主張要多強
      （只驗頻率？連振幅一起？容差多少？）需月月裁決——**新容差不可由工程端自訂（R2）**。
      參考：`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.4。
- [~] **A14 高音弱基頻是物理正確還是引擎缺陷** — **2026-09-08 規劃者代決「部分合理，主因引擎缺陷」**：半正弦力脈衝在 x=2·f·τc≫1 區被外插（G5 x=2.91 正中零點，基頻 −33.7 dB），τc 音高律 k=0.212 比文獻平。
      **月月 2026-09-10 裁決放行 → B-2 patch 已 `git apply` 落地**（`reports/a14_tauc_keytrack_before_after.md` 文末落地記錄；7/8 位元不變、physical_piano 607d0d3b→1233b53f 與報告事前值一致；5 檔 verify_score PASS；`--full` NO CHECKED FAILURES；位元基準改 `sha256_before_post_a14.txt`；~~Opus 稽核中~~ → **09-10 稽核 PASS**，`reports/gate_outputs/wf0910_A14_apply_AUDIT.txt` verdict = PASS）。B-1 等文獻（D10）。原始記錄：2026-08-30 新增，**擋住 22 顆音的判定**。
      **09-25 維持 [~]，理由兩個**：(1) B-1 仍等文獻（D10）；(2) 盤點新發現 B-2 落地後，舊的 22 顆全部轉 PASS，但深零點搬到了 E5／A5／A6／A♯6 的特定力度，給愛麗絲全曲有 **16 顆新 FAIL**，登記為 **D16**（見「2026-09-25 盤點新登記」）。`[docs-consistency:T3]` `[open-work:N1-fe16]`
      乾聲單音實測（piano 引擎、velocity 0.427/0.462）：G5 峰值 −46.7 dBFS、主導頻率
      1571.5 Hz（第二 partial，比值 2.0044）、基頻低 21.9 dB；G6 峰值 −54.5 dBFS、
      主導 3214.9 Hz（比值 2.0503）、基頻低 24.0 dB；D7 峰值 −64.5 dBFS（主導即基頻）。
      比值 > 2 與 stiffness inharmonicity 方向一致，且真鋼琴高音區基頻本來就弱
      → **可能完全正確**。但整體電平偏低這點與 D8（tongue_drum 40 dB 斜率）氣味相近。
      需物理域判定 + 溯源；若判定要改引擎，**觸發 Rule 10**。
      證據：`reports/gate_outputs/stem_verify_fur_elise_run.txt` 發現 2。

- [x] **A1 Rule 10 前後對照裁決** — **2026-08-26 月月裁決「放行」（整批接受）**。7/22 那六項物理修正
      （`reports/deep_fix_before_after.md`）最終放行，無指名回退項。同一句裁決一併授權「下一批
      commit + merge 進 main」（= A6 執行、B3 批次落地）。
- [x] **A1' B1+B2 Rule 10 裁決** — **2026-08-22 月月裁決「接受」**，B2 批次已 commit+push
      （`4ef2c50`/`bef60fc`）。報告 `reports/b1_b2_bridge_damping_before_after.md`。
- [x] **A2 阻尼寬頻化那批 unstaged 怎麼處理** — **已依 (b) 方案收斂完成**（事實路徑：該批與 B1 一起進了 447faea，B2 於 2026-08-21 完成收尾驗證，見 B2 條目）。
- [x] **A3 琴橋導納要不要開工**（= B1）— 已開工並完成（見 B1/B2 條目）。
- [x] **A4 亮度 EQ 應急層去留** — **2026-08-27 月月裁決「調整文件建議值」，已落地（程式碼零改動）**：
      `docs/AI_PERFORMANCE_PLAYBOOK.zh-TW.md` §5 eq 條目改為「預設不開」——8/6 激發端修正
      （τc keytrack + 響度校準）落地後補償需求已消失，且 EQ 與 normalize 交互會把整曲電平
      下拉（六首實測 −0.02~−0.19 dB，water_gong 低頻曲目 −0.33 dB）。eq 機制本身保留
      （藝術用、域外）。依據裁決包 `reports/decision_packets/A4_brightness_eq.md`。
- [x] **A5 push 到 GitHub** — 2026-08-21 月月授權 push（49c22f5/b5ccb9b/26a0129），CI 全綠，X3 數字已得。
- [x] **A6 merge → `main` 時機** — **2026-08-26 月月裁決「下一批 Commit+merge 進去」，已執行**：
      B3 批次（X4+B3+Rule 10 報告+裁決包+LICENSE）commit 後併入 `main` 並 push（M8-8b 完成，
      阻斷式跨平台 GATE 由 CI 驗證）。
- [x] **A7 repo License 定案** — **2026-08-26 完成**：依「保留商業」決定寫入 `LICENSE`
      （All rights reserved 專有授權 + 中文摘要 + 第三方元件條款）、`README.md` License 段 TBD 已更新。
      **殘留提醒**：正式發行前仍要讀一次 JUCE 8 EULA 的署名條款（LICENSE 檔內已註記）。VST3 SDK 在 JUCE 8 內是 MIT，無虞。
      **→ 2026-09-25 已查證**（`[release-readiness:S4]`）：repo 內 JUCE 為 8.0.12；Starter 方案年營收 US$20k 以下免費、可閉源商用，EULA 沒有 splash 或署名要求，跟 LICENSE 的寫法一致。
      營收保守算法要把合成器、音效包、專輯合計。Starter 要不要先到 juce.com 註冊，查不到定論。
      但 VST3 SDK 的 MIT、JUCE 的依賴、IBM Plex 字型的 OFL 都要求隨軟體附聲明，repo 目前沒有第三方授權聲明檔（見「2026-09-25 盤點新登記」）。
- [x] **A8 外部資料集要不要下載** — **2026-09-07 月月裁決下載 → 09-09 裁決「無替代就私下對照參考」**。已下載吉他/豎琴子集到 `external_data/`（gitignore），登記 `docs/EXTERNAL_DATASET_A8.zh-TW.md`。
      **兩個更正**：授權實為 **CC BY-NC-SA 4.0**（資料檔 metadata；arXiv 預印本寫 BY-SA 是我們原本抄錯的來源）；量測半徑 **2.06 m 非 1.05 m**（`RadiationModel.h` 1.05 是自訂慣例，註解已改）。
      替代搜尋（`docs/EXTERNAL_DATASET_ALTERNATIVES.zh-TW.md`）：可商用且校準到絕對聲壓 = 0；補充來源 Weinzierl 2018 JASA（CC BY）+ Iowa MIS 泰國鑼（WF0909-P6 ~~入庫中~~ → 09-09 完成，09-13 隨 `27e8393` 入庫）。寫信要商業授權由月月自行決定。
- [x] **A9 Cubase 四步驗證** — **已由自動化取代人工並於真 Cubase 實測完成**（月月 2026-08-20 委託重定義 + 2026-08-22 L3b 實測）：
      掃描（L3a 快取 XML + GUI 建軌）／MIDI 實彈（Cubase 匯出經 melody_verify 5/5）／
      專案存讀（重開再匯出音訊位元全等）皆真 host 證據；automation 於 L2 HostProbe 合約層驗證
      （Cubase GUI 畫 lane 未做，唯一殘留人工項，非位置主張必需）。證據 `l3b_cubase_live.txt`。
- [ ] **A10 Score 控制台實操驗收** — Standalone 頂列 [Score] 鈕的實際操作。
- [x] **月光第一批商品 CC BY-SA 授權疑慮** — **2026-08-28 月月裁決「換乾淨公開來源」**：
      本批四首（`exports/products/moonlight_batch1/PRODUCT_SHEET.md` /
      `reports/product_sheets/moonlight_batch1_PRODUCT_SHEET.md`）在換源重製前不上架，
      僅作內部 demo/引擎對照用。後續執行 = 新待辦「古典曲目換源重製」（見下）。
- [ ] **古典曲目換源重製**（月月裁決 2026-08-28）— 計畫見
      `reports/decision_packets/CLASSICAL_RELICENSE_PLAN.md`。
      **2026-08-28 追加裁決「CC BY 可以（署名可接受）」，路線定案**：
      - [x] 給愛麗絲（PD）— 先行已執行（`scores/classical/fur_elise/` +
            `reports/gate_outputs/furelise_license_evidence.txt` /
            `furelise_four_seasons_noop_proof.txt` /
            `fur_elise_complete_melody_verify.json`）。
      - [ ] Vivaldi 四季 — 待排程：走 IMSLP Schoonenbeek CC BY，需從譜面重新轉譜。
      - [ ] 月光奏鳴曲 — 待排程：走 Kowalewski CC BY 4.0 或重轉譜，需從譜面重新轉譜。
      **轉譜 GATE 工具（本輪新增，登記為 classical 產線標配，未來每次轉譜/換源皆須跑）**：
      - `tools/score_vs_midi_verify.py`——來源 MIDI ↔ `.score.json` 全曲逐音比對
        （note_pairing/counts/bidirectional match/pitch/onset/duration），
        獨立實作 SMF parser（不共用 `mido`，避免與轉譜器共模失效）；給愛麗絲
        兩份 score 已各自 11 PASS/0 FAIL、905/905 matched（`reports/gate_outputs/
        furelise_midi_verify.txt`）。**現況誠實標註**：docstring 自稱
        "full-corpus" 但 `scores/` 下僅 `fur_Elise_WoO59.mid` 一份來源 MIDI
        入庫，14 份 classical score.json 目前只有 2 份（鋼琴/揚琴給愛麗絲）
        被此 GATE 實際覆蓋；Vivaldi 四季來源 MIDI 尚未入庫。~~**尚未接進任何
        GATE/CI/文件**（`.github/workflows`、README 快查表皆零命中）~~——四季/
        月光換源排程執行時，此工具與其 pytest（`tests/test_score_vs_midi_
        verify.py`，23 passed）須納入該次轉譜的驗收流程，不能只跑既有
        render-audio 系 GATE（`verify_score.py`/`melody_verify.py`/
        `physics_verify.py`）。
        **09-25 更正「尚未接進 CI」**（`[open-work:V1-score-vs-midi]`，已自行查證）：
        `tests/test_score_vs_midi_verify.py` 的 `EndToEndFurEliseTests` 對兩份給愛麗絲 score
        跑 `svm.verify()`，斷言 905/905 matched。這個檔的 26 個測試都在 pytest 收集範圍內
        （`python -m pytest tests --collect-only` 共 270 個，其中 26 個出自此檔）。
        CI `physics.yml` 從 E1 起每次 push 都跑 `python -m pytest tests -q`，沒有 `continue-on-error`，是阻斷式。
        來源 MIDI `fur_Elise_WoO59.mid` 和兩份 score 都已入庫，CI 不會因缺檔 skip。
        所以對目前唯一入庫的 MIDI↔score 配對，這道 GATE 早就在 CI 裡跑。
        還開著的只有一件：四季/月光換源時，要把新配對加進這組測試（上面那句仍然有效）。
      - `tools/melody_roll_video.py`——聾人可視旋律 shape 影片（piano-roll
        滾動疊圖），重用 `melody_verify.py` 的偵測數學（zero 新增
        pitch/onset 判定邏輯，僅新增繪圖/切窗）；給愛麗絲驗證影片
        （`reports/gate_outputs/fur_elise_melody_roll_run.txt`）確認忠實
        重用。**已知限制**：`DEFAULT_FFMPEG` 寫死月月本機絕對路徑（有
        `--ffmpeg` 可覆蓋，換機/CI 無 PATH 後援）；同樣**尚未接進文件/CI**。
        換源產線執行時可選配當人工複核輔助，非強制 GATE。
- [x] **IR 稽核** — 已完成，見 `docs/IR_REVERB_AUDIT.zh-TW.md`（~~unstaged 待審~~ → 08-28 已隨 `0f271ae` commit。`[docs-consistency:T3]`）。
- [x] **UI 雙開門**（提案 + mockup 完成，~~待月月視覺裁決~~）— 提案
      `docs/uiux/DOUBLE_DOOR_PROPOSAL.zh-TW.md`、互動 mockup
      `uiux/double_door_mockup.html`；月月看過裁決後才開實作卡。
      **→ 2026-08-30 月月否決**（`313acaa`，見上方 08-30 快照）：改由設計端照 `docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md` 從功能重做，不開雙開門實作卡。
      未入版控的 `docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md` §3 #2 和 `exports/products/clean_batch2/LISTING_COPY.md` 還把「雙開門裁決」當待辦，措辭同樣過時。`[docs-consistency:T3]` `[release-readiness:S2]`
- [x] **A11 共鳴板厚度 h 與材質選定（B1 琴橋導納）** —— **2026-08-27 月月裁決 (i)「確認現值」，關閉**：
      `h = 9mm`／`wood_spruce` 由月月確認維持（依據裁決包
      `reports/decision_packets/A11_soundboard_sensitivity.md`；`docs/BRIDGE_ADMITTANCE_SOURCES.md`
      §5 已補確認記錄），零程式碼改動。X1 併入的「可注入」子問題依裁決就地關閉——
      選 (i) 即維持寫死，不做旗標/注入 plumbing（物理層 `bridgeLossRate()` 本就可注入，
      引擎/renderer 層寫死維持現狀）。以下為原始待裁決記錄（保留供追溯）。目前實作用
      `h = 9mm`（文獻「鋼琴音板 8–10mm」範圍中點）、材質 = `wood_spruce`
      （`materials.json` 既有項，鋼琴/揚琴音板慣用雲杉的類比選擇）。
      兩者皆非 TsukiSynth cimbalom 的實測值，是暫定的文獻類比預設值
      （`docs/BRIDGE_ADMITTANCE_SOURCES.md` §5）。需月月確認是否合理，
      或改用其他材質/厚度。
      **2026-08-16 對抗驗證額外指出的流程問題（月月請一併裁決）**：這兩個未確認的
      常數目前是**無條件生效**於所有 Cimbalom/Piano 預設渲染路徑，沒有旗標可關。
      這與 repo 既有慣例不一致——M5 的 `damping.alpha` 文獻值是「月月核准後才更新
      `materials.json`」，響度補償 `amount=0.78` 是「三輪審聽定案」後才落地。
      本輪則是先落地、確認延後到 A11。緩解因素：值本身可溯源（滿足 Rule 4）、
      查表失敗 fail-closed；（2026-08-22 註：該批已隨 A1' 接受 commit，本項仍開放——
      月月確認數值或改值都只是一次常數修改 + Rule 10 小報告的事。）
      選項：(i) 維持現況、由月月直接確認數值；(ii) 加旗標預設關閉、確認後才開；
      (iii) 改用其他厚度/材質重跑。
      **2026-08-16 X1 併入本項的第四個子問題**：X1 裁決走 (a)（測試 DB 補 `wood_spruce`），
      只解了紅燈，**沒解**「共鳴板材質是否該從寫死改成可注入」。目前 4 處呼叫點各自
      `materialDB->getMaterial(kBridgeSoundboardMaterialKey)`。若 A11 選 (ii)（加旗標預設關閉）
      或 (iii)（換材質），需要的 plumbing 比單純注入更多，屆時一次做完；若 A11 選 (i)（確認現值），
      維持寫死即可，不必另外改。**故本子問題刻意不獨立行動，綁在 A11 一起裁決。**
      註：物理層 `StringModel::bridgeLossRate()` 本來就已收 `const Material&` + `thicknessM` 兩個參數，
      是可注入的；寫死只發生在引擎／renderer 層。
- [x] **A12 plugin 參數 set/restore 量化不對稱** — **2026-08-22 月月裁決 (a)、已修**：36 個 float 參數
      interval → 0（連續），round-trip 位元精確（0.42→0.42→0.42）；H5 主張同時修正為 fresh-vs-fresh
      （DAW「重開專案每次播放一致」語意——噪音事件計數器刻意隨敲擊遞增且不入 state，live-vs-fresh 非有效主張）。
      HostProbe 16/16 全 PASS + melody 5/5 重驗綠。CLI 不讀 APVTS → corpus 零影響（Rule 10 不觸發）。
      證據 `reports/gate_outputs/a12_c3_close.txt`。原始記錄：（L2 HostProbe 2026-08-20 首捕）—
      host `setValue(0.42)` 後 live 讀回 0.42（plain 0.428，**未量化**），但 state 存讀後變
      0.422222（plain 0.43，**量化到 0.01 步進**）→ **DAW 專案存檔重開後的渲染與存檔前位元不一致**
      （HostProbe H5 兩項誠實 FAIL，`reports/gate_outputs/l1_l2_l3a_melody_gate.txt`）。
      不對稱在 JUCE APVTS 層（setValue 不 snap、replaceState snap）。聽感差異極微（≤半步進），
      但違反位元精確還原主張。**不影響 CLI corpus**（CLI 不走 APVTS）→ 修正屬 Rule 10 免touch。
      修法選項：(a) 參數 interval 改 0（連續，round-trip 無損，編輯器旋鈕變平滑）；
      (b) 自訂參數類別讓 setValue 也 snap（live 聽感微變）；(c) 接受現狀、文件標註。需月月裁決。

## B. 資料齊、可以開工（**依此順序**，理由見 `RESEARCH_INDEX.md` §4）

> 09-25 註：B1–B6 已全部 Done（08-29 收官），B7 停在 09-15 裁決的合法終點，這個順序已經不再用來排工作。
> `docs/RESEARCH_INDEX.md` 停在 08-15；它 §5 的「D7／D8」指的是別的東西（Giordano 導納曲線／資料集本體），**跟本檔的 D7（實體試體）、D8（tongue_drum 斜率）不是同一項**。`[docs-consistency:C2]`

- [x] **B1 琴橋導納／共鳴板耦合**——**2026-08-21 由 B2 收尾補齊 Rule 10 報告 + corpus 73/73 後轉完成**（M10 已標 Done，見 ROADMAP §2）。
      `Y∞ = 1/(8√(D·ρs))` → `α = (T/L)·Re Y` → `1/T60_bridge = T·G/(ln1000·L)`。
      新增參數只有音板厚度 `h`。刻意不加耦合折減係數（Rule 4）。
      → 依據 `docs/BRIDGE_ADMITTANCE_SOURCES.md`；工作卡 `docs/workcards/B1.md`。
      **已完成**：`StringModel::decayTimeForFrequency` 加第四項 + `bridgeLossRate()`；
      只接 Cimbalom/Piano，Chromatic 零改動（`git diff --stat` 核實）；
      `ScoreRenderer.h` 三處呼叫點跟進；新增 15 條 CHECK 含哨兵反例。
      **GATE**：三 target build exit 0、ctest 全過、`--full` `NO CHECKED FAILURES`、
      `tools/` 零 diff（R2 未動容差）、未 commit（R7）。證據 `reports/gate_outputs/b1_*.txt`。
      **驗收交叉檢查（2026-08-16，由我獨立執行）**：cimbalom/steel/MIDI 60 的
      `T60(model) = 4.299 s`，與 `BRIDGE_ADMITTANCE_SOURCES.md` §3 事前獨立算出的
      並聯預測 **4.18 s 相差 3%**；舊值 26.86 s。tongue_drum steel 仍 16.39 s，
      確認 Chromatic 未被誤動。公式鏈判定為忠實實作。
      **剩餘（屬 B2 範圍，齊備前不得標完成）**：Rule 10 前後對照報告
      `reports/b1_b2_bridge_damping_before_after.md`（**目前不存在**）+ corpus 73 檔重驗。
- [x] **B2 阻尼寬頻化收尾** — **2026-08-21 完成（委託授權；改動未 commit，待月月讀 Rule 10 報告裁決）**。
      施工卡 11 條 GATE 全過：t60 ALL WITHIN TOLERANCE、--full NO CHECKED FAILURES、
      三 build exit 0、ctest 3/3、pytest 121/121、**corpus 73/73 PASS 零新增豁免**
      （`b2_*.txt` 全套證據）。寬頻化低音發散被 B1 封頂證實（C2 128.75s→17.66s）；
      `summer_m2` 自動回綠（−46.8 FAIL → −52.2 PASS，未動容差/score/豁免）。
      錨點重測：Cimbalom 0.1497→0.0874（中央弦反解法，`b2_attack_energy_remeasure.txt`）、
      Chromatic 兩值不變（noteComp≈1 雙 null 自驗）。
      **Rule 10 報告：`reports/b1_b2_bridge_damping_before_after.md`（§9 七項全含）——
      月月請讀 §0 白話導讀後裁決「接受」或「指名回退」（= 新 A1' 裁決項）。**
      施工卡 §7 哨兵測試未實作，理由記載於報告附錄（測試端重算=第二份會漂移的複本）。
- [x] **B3 弦阻尼律換第一原理** — **2026-08-24 完成（改動未 commit，待月月讀 Rule 10 報告裁決）**
      Cuesta & Valette 三機制，零自由參數（`Q⁻¹_air+Q⁻¹_visc+Q⁻¹_disl`），阻尼律形狀已換
      （`f²` → `f^0.5`+常數 / `f³` / `f¹`）；materials.json schema 遷移
      `beta_air`→`beam_plate_beta_air`、`gamma_radiation`→`beam_plate_gamma_radiation`
      （fail-closed 拒載舊鍵名，數值不變、只給 Beam/Plate），Rule 9 標註已補進
      `ROADMAP_PHYSICS.md` §0 驗證域表。
      施工卡 §8 GATE 12 條全過：`b3_gate_full.txt`（NO CHECKED FAILURES）、`b3_t60.txt`、
      三 build exit 0、`b3_ctest.txt`、`b3_pytest.txt`、**corpus 73/73 PASS 零新增豁免**
      （`reports/gate_outputs/b3_corpus_{A,B,C,D}.txt`）；反例哨兵 `b3_selftest_sentinel.txt`。
      **Rule 10 報告：`reports/string_damping_firstprinciples_before_after.md`（§9 八項全含，
      尤其 `Q⁻¹_disl`/`eta` 佔比表與 `damping_override` 錨點保證變化聲明）——月月請讀後裁決。**
      → 依據 `docs/STRING_DAMPING_SOURCES.md`
- [x] **B4 槌頭非線性接觸求解器**（前置：無，但風險最集中）— **Done（2026-08-27，
      月月裁決 (b)「重定義 F3 velocity 主張域」後收尾完成；改動留 unstaged 待月月授權 commit，R7）**。
      實作：HammerImpulse.h 三常數表+內插+pianoHammerTauC（錨定 kTauCFelt@A4/v=0.5）、
      CimbalomEngine 4 呼叫點 Felt 分支、7 條新測試全 PASS、非 Felt/Chromatic 位元不變已證
      （`b4_nonfelt_invariance.txt`）、ctest/pytest/selftest/三 build 全綠
      （`b4_build_{cli,standalone,vst3}.txt`/`b4_ctest.txt`/`b4_pytest.txt`/`b4_selftest.txt`，
      X4 規約先重建 `b4_x4_rebuild_tests.txt`/`b4_f3_redefine_x4_rebuild.txt`）。
      **F3 撞牆與裁決**：--full F3 velocity 判定 piano 路徑 FAIL——predicted_delta C2 +6.3(PASS)/
      C4 +7.79(dev +1.77 FAIL)/C7 +19.12(dev +13.10 FAIL)，偏差隨 α 嚴格單調（C7>C4>C2）、
      渲染實測與模型預測吻合 <0.2 dB（match_ok 過、law_ok 破）＝本條目早就預告的
      「撞 §6 velocity 判定」物理事實，非實作 bug（存證 `b4_gate_full_FAIL.txt`/
      `b4_f3_alpha_monotonicity.txt`）→ 照卡 §12 停工出裁決包
      `reports/decision_packets/B4_f3_velocity_ruling.md` → **2026-08-27 月月裁決 (b)**：
      F3 主張域二分（固定 tau_c 路徑檢查一字不動；tau_c(v)/Felt 路徑改「實測 vs 模型自身預測
      ±1.0 dB」自洽判定＋predicted_delta 誠實列印），match 容差數值未動、未放寬任何檢查
      （R2 遵守，登記見 `ROADMAP_PHYSICS.md` §6 velocity 列）。
      重定義後收尾證據：`b4_gate_full_after_f3_redefine.txt`（NO CHECKED FAILURES）、
      主張域哨兵兩輪 `b4_f3_redefine_sentinel.txt`、`b4_f3_redefine_ctest.txt`/
      `b4_f3_redefine_pytest.txt`/`b4_f3_redefine_alpha_recheck.txt`、
      **corpus 73/73 PASS 零新增豁免**（`b4_corpus_all.txt`）、
      **Rule 10 前後對照報告 `reports/b4_hammer_contact_before_after.md`**。
      `F = K·δ^α` 逐音實測值 + 槌質量表 + Stulov 遲滯參數。
      **只適用 Cimbalom/Piano**；Chromatic 在 D2 補搜完成前不得套用。
      **必須連同 noteOn 能量正規化層一起設計**，否則會撞 §6 velocity 判定。
      → 依據 `docs/HAMMER_CONTACT_SOURCES.md`
- [x] **B5 木材正交異向 schema 入庫**（前置：B1，等音板需要 `D` 時一併進場）
      2026-08-28 完成（月月裁決照建議值走；GATE 8 條全過；no-op 證明
      `reports/b5_schema_noop_proof.md`）。orthotropic schema 已備妥
      （目前零消費路徑，死資料）。
      Kirchhoff 板改異向版仍是**模型結構改動**，不是換數字，未做。
      → 依據 `docs/WOOD_ANISOTROPY_SOURCES.md`
- [x] **B6 force → 輻射壓力／SPL 模型**（前置：B1 + B5，皆已 Done）
      **Done（2026-08-28，Phase 3/4 落地，unstaged 待月月審）**：
      Phase 0（`docs/RADIATION_POWER_SOURCES.md`）查證結果——`fc` 公式的
      `H` 是誤讀（更正為 `fc=ca²/(2π√(Dx/ρs))`，非 `Dx·H`）；
      `W_rad=σρ₀c₀S⟨v²⟩`／`η_rad=ρ₀c₀σ/(ωρs)` 兩篇 Ege & Boutillon 論文
      都沒有逐字給出，改用「標準定義代數推導」路線（非文獻逐字引用，程式
      註解已標明溯源等級）；`σ(f)` 採用 §4.4 工程近似式（`(f/fc)²`
      次臨界形狀，非 Ege & Boutillon 曲線）。Phase 1（`src/physics/
      RadiationModel.h` 新檔＋`ScoreRenderer.h::dumpModes()` 加
      `"radiated_power_relative"` 資訊性欄位）先前已完成並驗收。
      **Phase 2 裁決（2026-08-28，月月）**：「照建議走」——**方案 B 先行**
      （純物理訊號點校準，本輪據此開工），**方案 C 立卡排隊**（`docs/
      workcards/B7.md`，完整第一原理力鏈，另開工）。裁決記錄見
      `reports/decision_packets/B6_calibration_choice.md`「裁決記錄」節。
      **Phase 3/4（本輪，方案 B 落地）**：
      - 新增純物理訊號分接點 `DiagnosticOverrides::capturePhysicsOnlyModes`
        （`src/dsp/DiagnosticOverrides.h`，比照既有旗標模式）＋
        `CimbalomVoice::getPhysicsOnlyModeAmplitudes()`（`src/engines/
        CimbalomEngine.h`，CLI `noteOn()` 變體專用，`startNote()` 即時
        播放路徑完全未動）——擷取每個 partial 在 `spectralTilt`（創作/
        啟發式層）與 `loudnessCompensationGain`／多弦正規化增益（創作層）
        之前、但 `HammerImpulse::forceSpectrumMagnitude()`（物理量）之後
        的振幅。旗標只由 `dumpModes()` 設為 `true`，`render()`/
        `renderEvent()` 從未觸碰。
      - `RadiationModel::kPascalsPerUnitPhysicsAmplitude = 1.0f`（`src/
        physics/RadiationModel.h`）＋ `pressurePerForce()`——沿用
        `EXTERNAL_ANCHOR_SOURCES.md` §1「數位 1.0 ≡ 1 Pa ≡ 94 dB SPL
        @1.05m」慣例，釘在上述純物理訊號點。**R4 明確標註：月月裁決的
        方案 B 慣例錨定，不是實測值、也不是推導值**。刻意不消費
        `radiationEfficiency()`/`radiationLossFactor()`（σ(f)/η_rad(f)
        只當 fc/fga 閘門，不當乘數——理由見 `RADIATION_POWER_SOURCES.md`
        §5 補記，避免把不同溯源等級的不確定度混進同一個絕對數字判定）。
      - `dumpModes()` 加 `"absolute_pressure_per_force"` 至
        `model_observables`；每個已 dump 事件加 `acoustic_transfer[]`
        （`radius_m`/`azimuth_deg`/`elevation_deg` 寫死 1.05/0/0；
        `pressure_per_force_imag_pa_n` 固定 0.0 且明確標註**非相位主張**
        （程式碼註解＋`RADIATION_POWER_SOURCES.md` §5 補記皆已明寫）；
        `f≥fga` 的 partial 不輸出；非 string/cimbalom/piano 引擎或缺
        D/ρs 的事件輸出空陣列 `[]`，不是省略鍵）。**`radiation_directivity`／
        `complex_phase` 確認未被加進 `model_observables`**（既有哨兵測試
        持續守，三則既有測試同步更新以反映 Phase 3/4：`absolute_pressure_
        per_force`/`acoustic_transfer` 從「禁止」改為「預期」）。
      - 測試：C++ `testPressurePerForceCalibration()`（手算對照 1.0×
        校準常數 + 反例：doubled-constant mutant／零/負/NaN/+Inf
        fail-closed）、`testPhysicsOnlyCaptureDoesNotAffectRender()`（旗標
        開關下 `getAllStringModes()` 位元相同的單元級證明 + 正控制：
        physics-only 振幅確實不同於 render-path 振幅）；Python
        `Phase4SelfConsistencyTests`（`tests/test_specimen_verify.py`）
        對 A4/steel/velocity=0.5（`kCimbalomAttackEnergyRefA4` 同一錨點，
        `strike_position` 微調 0.3→0.31 迴避既有模型/harness 交互作用——
        0.3 的 `sin(n·π·0.3)` 模態公式在 n=10/20/30 給出真實振幅零點，
        `specimen_verify.py` 對 dump 全部 partials 做無條件比對性檢查，
        振幅零點會讓 bundle REFUSED，這是既有、與 B6 無關的問題，依規定
        不修改 `specimen_verify.py`）跑真實 `--dump-modes`，原封複製成
        `SYNTHETIC_TEST_ONLY` bundle，`absolute_spl` claim PASS；
        反例（+10dB tamper）FAIL（誤差精確等於 10.0dB，見
        `reports/gate_outputs/b6_specimen_selftest.txt`）。
      **GATE 全綠**：三 build target exit 0、ctest 3/3、pytest 156/156、
      `--full` 與 Phase 1 基準零差異（`b6_gate_full_phase34.txt` diff
      `b6_gate_full_phase1.txt` 除末尾 `EXIT=0` 記帳行外零差異）、8 首
      代表曲目 SHA256 位元不變 8/8（`b6_bit_identity_phase34.txt`，
      `render()`/`renderEvent()`/`ModalResonator` 皆未觸碰）、corpus
      `verify_score.py --all` **75/75 PASS**（corpus 由 73 增至 75——
      其間 `fur_elise_complete`/`fur_elise_complete_cimbalom` 兩份 score
      由無關工作新增，非 B6 改動；1 項既有 `moonlight_sonata_complete`
      豁免延續、零新增豁免、零 FAIL，`b6_corpus_phase34.txt` 四分片）、
      specimen selftest PASS/FAIL 各一（`b6_specimen_selftest.txt`）。
      量測面：1.05 m 球面、正前方單點（無指向性模型）、數位振幅 1.0 ≡
      1 Pa ≡ 94 dB。
      → 依據 `docs/EXTERNAL_ANCHOR_SOURCES.md` §2–§3、
      `docs/RADIATION_POWER_SOURCES.md`、`docs/workcards/B6.md`
- [~] **B7 完整第一原理力鏈校準（方案 C）**（前置：**B6 方案 B 落地**——
      **2026-08-28 已滿足**，B6 Phase 3/4 皆 Done，見上一條目；本卡可以
      開工，但仍待有人實際排入工作）
      **狀態（月月 09-15 裁決，照 `reports/decision_packets/B7_phase2_and_open_items.zh-TW.md` §6 第 3 點指定措辭同步）：
      In progress——Phase 0 完成、Phase 1 部分完成（欄位撤回版）、Phase 2/3 BLOCKED（月月 09-15 裁決）。**
      裁決內容：§5 三條路徑選 **C**（proxy 與 `S` 都不裁，B7 本輪到此為止＝合法終點）；§1 驗收基準 (a) 選**乙**（標 BLOCKED，來源缺口）。
      要重啟得先解 §1.1：score schema 加真實 MIDI velocity 欄位，需要另開卡，並改 B7.md §5 的禁令。
      解除 (a) 阻塞的三條管道（向 Goebl 要 Fig. 2.20 校準值／機構帳號取 Roginska 2013／借 Meyer 動態範圍表）留給月月日後有機會再說。
      下面各段「已 staged」「BLOCKED 待月月裁決」是 09-14 當時的狀態；WF0914 成果 2026-09-25 已 commit。
      （09-25 補同步：裁決包要求的這句 09-15 沒寫進 TODO/ROADMAP，盤點查到後補上。`[docs-consistency:T6]` `[懷疑者補抓的漏項（docs-open）]`）
      **B7 殘留尾巴**（都不影響現有渲染）：
      `HammerImpulse.h:334/342-343/513` 的註解還指向已撤回的 `dumpModes()` Path C 欄位（`[staged-review:B7-residual]`）；
      `hammerVelocityMps()` 在 MIDI 20 有 2.3 倍的跳躍（`[staged-review:B7-clamp]`，重啟時由月月裁）；
      `hertzImpulseConsistentTauCSeconds` 只做到衝量自洽，錨點 α=2.3～3.0 時接觸時間只有真 Hertz 碰撞的 0.695～0.599 倍（`[staged-review:B7-tauC]`，長期研究）。
      這三條的勾選項見「2026-09-25 盤點新登記」。
      **2026-09-14 WF0914-B7P0+B7P1 進度更新（In progress，稽核 PASS 已 staged）**：
      Phase 0 兩份溯源文件已完工（`docs/HAMMER_VELOCITY_SOURCES.md`——
      Goebl 2003 博士論文式 (3.2) `v=2^((MIDI-52)/25)`，原文已核；
      `docs/RADIATION_POWER_SOURCES.md` §8——音板輻射面積 `S`：同儕審查層級
      平台琴查無，只有直立琴 1.2649 m²）。Phase 1 力鏈組裝已落地但**卡在
      §1.2「否」分支**：查證 `RadiationModel.h`/`CimbalomEngine.h` 現行音板
      參數（`kBridgeSoundboardThicknessM=9mm`、`wood_spruce` 材質）後，
      `CimbalomEngine.h` 自己的註解已明寫兩者皆「文獻類比預設值，不是
      TsukiSynth cimbalom 的實測值」——**不是**那台 Ege/Boutillon 直立琴
      的實測值，與 `S` 唯一可用的文獻數字（同一台直立琴）非同源。故
      `S` 維持 `UNVERIFIED`，Path C 的 `absolute_pressure_per_force_firstprinciples_c`
      / `acoustic_transfer_c[]` 兩欄位**不輸出**（fail-closed），力鏈只
      落地到 §4.4 的 `W_bridge(f)`（新欄位
      `"bridge_power_firstprinciples_c"`，僅 Cimbalom/Piano + Felt）。
      新函式：`HammerImpulse::hammerVelocityMps()`/`hertzPeakForceNewtons()`
      （§4.2/§4.3，能量守恆推導）、`RadiationModel::modalEnergyFirstPrinciples()`/
      `bridgePowerFirstPrinciples()`（§4.4，SDOF 衝量-能量精確解推導，本文件自推）。
      §7 五條測試對應調整為 `testHammerVelocityMps`/
      `testHertzPeakForceEnergyConservation`/`testHertzPeakForceCounterexample`/
      `testBridgePowerFirstPrinciplesChain`（4/5 項改對 `W_bridge` 的哨兵，
      「否」分支下無 `W_rad` 可比、無 `acoustic_transfer_c[]`）/
      `testPathBAndPathCDoNotInterfere`，全過。GATE 全綠：三 build target
      exit 0、ctest 4/4 Passed（X4 先重建五測試 target）、`--full`/
      `--selftest` 與基線零差異、`verify_score.py --all` 與基線一致、
      位元不變性對 `sha256_before_post_a14.txt` 8/8 IDENTICAL（本卡只進
      `--dump-modes`，未動 `render()`/`renderEvent()`）。證據
      `reports/gate_outputs/wf0914_B7P1_*.txt`。**剩餘項**：(a) §1.1 velocity
      proxy→MIDI 換算為規劃者代決（proxy×127），非查證確認，月月可推翻；
      (b) §8 驗收基準 (a)(b)（文獻 SPL GATE、與 B6 雙路徑一致性）本卡未執行
      （Phase 1 完成即本卡此輪的交付範圍）；(c) `S` 若要繼續，需月月在
      §4.5 的兩個選項（跨琴種挪用直立琴 1.2649 m²／改用廠商規格值）之間
      裁決，或維持卡住。詳見 WF0914-B7P1 完成報告。
      **2026-09-14 B7P1 稽核修復（複稽 PASS 已 staged，In progress，狀態較
      上一輪倒退為 BLOCKED）**：稽核抓到兩個真實缺陷，皆已修——(1) 能量守恆
      違反：`RadiationModel::modalEnergyFirstPrinciples()` 组裝的衝量用了兩個
      互不自洽的量（`F_peak` 來自 Hertz 能量守恆解，`τ_c` 卻沿用 B4
      `pianoHammerTauC()`——一個完全不同、獨立錨定的量），導致 MIDI 36–96 ×
      velocity 20–120 全域 24/24 點衝量超過物理上限 `2·m·v` 達 2.55–4.32 倍。
      修法：`HammerImpulse.h` 新增 `hertzImpulseConsistentTauCSeconds(note,v,
      F_peak)=π·m·v/F_peak`（半正弦脈衝模型自身衝量公式 `F_peak·τ_c·(2/π)`
      令其等於彈性碰撞動量守恆 `2·m·v`，反解 `τ_c`，與 `F_peak` 同一組 Hertz
      解自洽），取代原本的錯誤呼叫；修復後全域衝量/`2mv` 比值精確收斂到 1.0
      （浮點精度內）。(2) §7 測試第 4 項原本被換成非守恆哨兵，已補上真正的域
      掃描守恆測試 + regression guard（`tests/physics_models_repro.cpp`）。
      **(3) §1.1 velocity proxy→MIDI 換算重新查證後改判 BLOCKED**（稽核挑戰
      成立）：`tools/midi_to_tsukisynth.py::velocity_for()`——本專案唯一真正
      把 MIDI 轉成 score `velocity` 的程式碼——算式是 `base_velocity(role,
      0.42–0.72) × (source_velocity/90.0)`（±0.025–0.035 微調，clamp 至
      [0.12,0.92]），**從未是 `MIDI/127`、也不與 MIDI 成比例**（真實 MIDI
      velocity 在轉譜當下就被丟棄）。依施工卡 §1.1「若查證結果與此矛盾…不要
      硬套，status=BLOCKED」，已撤回 `ScoreRenderer.h::dumpModes()` 對
      `bridge_power_firstprinciples_c` 的欄位輸出與 `model_observables`
      廣告；底層純函式（`hammerVelocityMps()`/`hertzPeakForceNewtons()`/
      `hertzImpulseConsistentTauCSeconds()`/`modalEnergyFirstPrinciples()`/
      `bridgePowerFirstPrinciples()`）保留、已修好、單元測試全過，待月月對
      §1.1 裁決後再接回。**(4) 位元不變性證據檔補齊**：`wf0914_B7P1_
      bit_identity.txt` 這一輪重寫為真正含比對結果（先前版本只有 render
      log，沒有 diff/IDENTICAL 結論），本輪 8/8 IDENTICAL。GATE 全綠：三
      build target exit 0、ctest 4/4 Passed、`--full`/`--selftest` 與基線
      零差異、位元不變性 8/8 IDENTICAL。**Phase 1「最低限度交付物」
      （dumpModes() 新欄位）因 §1.1 BLOCKED 而未達成**，待月月裁決 §1.1：
      score velocity 該如何合法轉換成真實 MIDI/槌速，才能繼續這條診斷鏈。
      **2026-09-14 WF0914-B7P3（稽核 PASS 已 staged，~~BLOCKED 待月月裁決~~ → 09-15 月月已裁：路徑 C＋(a) 乙案＝本卡本輪合法終點，見本條目開頭狀態行）**：施工卡要求的
      Phase 3 雙路徑比對（B7.md §6 步驟 11）本輪**執行不了**——實際跑
      `--dump-modes` 確認 `model_observables`/事件層級/partial 層級**完全
      沒有任何 Path C 欄位**（`bridge_power_firstprinciples_c` 已在 B7P1
      稽核修復回合撤回，`absolute_pressure_per_force_firstprinciples_c`
      因 §1.2「否」分支本來就未落地），沒有第二條路徑可比，非「差異很大」
      而是「無資料」。已把這個事實與 Phase 2 甲/乙案一起整理成裁決包
      `reports/decision_packets/B7_phase2_and_open_items.zh-TW.md`
      （§1 甲/乙案＋新事實、§2 `S` 採用記錄追認、§3 proxy 代決追認、
      §4 雙路徑差異＝空白＋恢復條件），完整過程見
      `reports/b7_dual_path_comparison.md`。**本卡未碰 `src/`**
      （`git diff -- src/` 為空）。
      **2026-08-28 立卡（月月裁決：「C 立卡排隊」，`reports/decision_packets/
      B6_calibration_choice.md`「裁決記錄」節）**：施工卡
      `docs/workcards/B7.md`——從 MIDI velocity 一路換算真實物理單位
      （槌速 m/s → Hertz 接觸峰值力 N → 音板真實振動功率 → 1.05m 處 Pa），
      不靠任何「拿輸出訊號回推」的事後校準捷徑。三條驗收基準：
      (a) 文獻 SPL 範圍 GATE（真實鋼琴 1m pp≈60dB／ff≈100dB SPL，**尚未
      溯源到具體文獻，動工前必須先查到出處**）、(b) 與 B6 方案 B 錨點的
      雙路徑一致性檢查（差異門檻待 B 落地後才定，不預先寫死）、
      (c) 終極驗收＝D7 實體試體量測（本卡不涵蓋，另待月月安排）。
      前置補搜三塊（本輪已用 WebSearch/WebFetch 做初步查證，見 B7.md §2.2）：
      MIDI velocity→真實槌速 m/s 對應（Askenfelt & Jansson 方向——已直接
      WebFetch 到 Woodhouse *Euphonics* §11.2 轉引 Boutillon「0.11–6.83
      m/s（pp–ff）」與 Askenfelt KTH 講義頁「forte 槌速約 5 m/s、槌速≈
      5×鍵速」兩條可信但**未給 MIDI velocity 顯式映射**的來源，映射函數
      本身仍是缺口）、音板有效輻射面積 `S` 推導、`σ(f)` 信度（已知 `fc`/
      `fga` 幾乎重合、飽和分支活動窗僅 2.6% 頻寬，繼承自 `RADIATION_POWER_
      SOURCES.md` §3 補記）。
      **商業物理建模公司公開驗證資料調查（B7 前置研究，已完成）**：
      `docs/COMMERCIAL_PM_PUBLIC_DATA.zh-TW.md`——查 Modartt/Pianoteq、
      Audio Modeling、AAS、Arturia 四家，**月月假說（商業公司會公開驗證
      資料以取信消費者）本輪未被證實**：四家皆無可稽核的「模型輸出 vs.
      真實樂器量測」比對數據/白皮書/學術論文（§0/§1 一句話結論）。
      有用產出兩項：(1) §3 Askenfelt & Jansson KTH 講義的 MIDI velocity→
      真實槌速 m/s 數字**可直接用**，餵入本卡 §1 的「映射函數仍是缺口」；
      (2) §4 確認裁決包裡「pp≈60 dB / ff≈100 dB SPL @1m」這組數字**仍是
      未溯源**——查無鋼琴專屬、標明 1m 距離的權威出處，本卡驗收基準 (a)
      動工前仍須另尋文獻源（Chabassier et al. 2013 JASA、Roginska et al.
      2013 POMA 近場量測為候選延伸讀物，見該文件 §0 表格）。
      → 依據 `docs/workcards/B7.md`、`docs/workcards/B6.md` §6 Phase 2、
      `reports/decision_packets/B6_calibration_choice.md`、
      `docs/COMMERCIAL_PM_PUBLIC_DATA.zh-TW.md`

## C. 不需要任何資料、純工程（可隨時插隊）

> **2026-08-30 新增的 stem_verify 收尾四項，建議順序 C10 → C11 → C12 → (A13/A14 裁決後) C13。**

- [~] **C10 量測器自身的合成哨兵** — **WF0907-C10 實測 1.1721 cents > 1 cent**（MIDI 37/100 附近 bin 對齊系統偏差；工具 `tools/measurement_selfcal.py` 1170 格點+靈敏度反例已入庫）。
      **月月 2026-09-09 裁決 B「改估計器」→ 已在兩個家族六個候選上試完，全數否決（2026-09-09～10）**：
      (1) STFT-bin 家族五候選（拋物線內插／相位差／zero-padding／柔化質心／mean-shift）——柔化質心一度報 0.29 c 但被稽核抓到「以期望 f0 為中心柔化＝把量測值往目標拉，低音區實質放寬到 ±12.5 c」，撤回；
      (2) 時域 NLS 擬合（WF0909-C10C，Opus）——合成關卡大幅領先（hold-out 0.08 c、增益保真 0.009 c）**但真實渲染更差**（0.22 s 短音在 1.23 s 視窗、放鍵阻尼非單一指數 → τ 只剩 0.03–0.05 s、線寬 16–26 c；給愛麗絲前 300 顆 7 顆 PASS→FAIL、30 檔強域動 9 檔），未上產品路徑。
      **更上層發現**：合成哨兵的訊號模型正好就是 NLS 的模型 → 現行形式的 1-cent 門檻本身不足以認證估計器；要補「放鍵/阻尼段」語料，但那會改變 1.1721 這個比對數字（門檻不變）。
      **現況**：產品估計器＝原始硬邊界質心（位元組不變），`measurement_selfcal.py` 多了增益保真掃描（升為 GATE 條件）與三弦 course 檢查，並有「增益保真不得比舊版差」迴歸測試。C10C 全部改動存成 `reports/c10c_nls_candidate.patch`（未落地）。
      **規劃者建議：改選 A（收窄主張域）**，措辭草案在裁決包 §6.4；~~等月月一句話~~。
      **→ 2026-09-10 月月選 A，已落地**：`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.5／§9.7 寫明量測器含 ≤1.18 cent 已知誤差（開發 1.1721／hold-out 1.0840），±5 cent 門檻不變，**不可宣稱 ≤1 cent**。
      09-15 D15 選 A' 再收窄：≤1.18 cent 只涵蓋持續段，放鍵/阻尼段已知誤差上界約 7.2 cent（§8.5）。
      本條以「收窄主張域」結案，保留 [~] 是因為 ≤1 cent 從未達成：5 個 strict xfail 刻意留著當開放缺口的標記。
      **09-25 另查到**：兩個 release 段 strict xfail 的 pin assert 排在 ≤1 c 判定之前，數字漂移抓不到，估計器變好也永遠不會 XPASS（`[staged-review:D15-xfailpin]`，勾選項見「2026-09-25 盤點新登記」）。`[docs-consistency:T6]`
      原始記錄：月月 2026-08-30 查核第 5 點：
      ±5 cents 是本專案既有裁定的產品門檻，**不是 ISO 或業界標準**；
      要用它執行 GATE，量測器本身必須先用**合成訊號**（已知頻率、已知衰減、
      已知泛音結構）證明自身誤差 **≤1 cent**。目前沒有這個證明。
      不做這項，後面所有音高數字都站在一把未經校驗的尺上。
- [x] **C11 逐顆記錄拒答理由** — **2026-09-08 Done（WF0907-C11，隨 C12 稽核 staged）**：每顆 `reason`/`rules`（Ra–Re 精確字串抽取）+ `refusal_histogram`/`rules_histogram`，判定零改變（before/after 逐顆相同）。原始記錄：`stem_verify` 的 JSON 目前只有
      index/time/note/engine/verdict/onset_err_ms/pitch_cents/expected_f0_hz，
      **沒有 reason 欄位**。212 顆拒答因此是黑盒，無法收斂（要靠人工重跑單顆才知道理由）。
      melody_verify 本來就回傳 reason，只是沒被帶進來。
- [x] **C12 `--analysis-dry` 旗標 + 衍生 score 的 hash/diff 寫進 JSON** — **2026-09-08 Done（WF0907-C12）**：乾聲為預設（`--no-analysis-dry` 帶 §8.3 warning），`provenance{source_score,analysis_score,leaf_diff,cli}` 三個 sha256，手動法 vs 旗標 40 顆逐欄零差異。原始記錄：
      目前乾聲跑法是手動改 score 存到 temp，**JSON 裡的 `score` 指向使用者 temp 路徑**，
      temp 一清就只剩口述來源（月月 2026-08-30 查核指出）。
      應由工具自己產生乾聲衍生 score，並把來源 hash 與 leaf diff 寫進報告。
      §8.3 已定：**帶殘響訊號的音高判定不得作為 GATE 依據**，所以乾聲應是預設分析路徑。
- [x] **C13 harmonic-aware 判定** — **2026-09-09 Done（WF0908-P1，informational）**：`tools/partial_verify.py` 的 `pitch_via_partials_*` 欄位（與 `verdict` 分離，月月 08-30 裁定）；B 由 dump 的 f2/f1 反推不引外部值。A14 判為缺陷後 22 顆要在 B-2 patch 落地後重量。
      （09-25 查證：B-2 已落地，但 `reports/gate_outputs/` 找不到 A14 之後重量的記錄；partial_verify 也從沒在全曲 905 顆規模跑過。弱基頻的組成已換成 D16 那 16 顆。勾選項見「2026-09-25 盤點新登記」。`[open-work:P2-partial-full]`）原始記錄：給 22 顆弱基頻高音一個「答得出來」的問法：
      驗 `f_n = n·F0·√(1+B·n²)` 或直接對 `--dump-modes` 預測的逐 partial 頻率比對。
      **前置**：A13 主張域裁決、A14 物理判定。`B` 的物理合理性須獨立查證（R4）。
- [x] **D14 stem_verify 記憶體線性成長修復** — **2026-09-14 Done（WF0914-D14）**：診斷出 `run()` 的
      `stem_arrays={}` dict 把每顆事件完整 float64 音訊陣列留到函式最後才用（`compare_superposition()`
      那一次呼叫），905 顆事件全曲跑會同時全部活在記憶體裡，登記時實測 >28 GB（隨事件數線性成長，
      當時只能 `--limit 300`）。改用 `read_wav_header()`（只讀 WAV 'fmt ' chunk 取樣率/聲道數，不讀音訊
      資料）做相容性檢查取代整段讀入，並新增 `StemArrayStream`（duck-typed 串流物件，`len()`/`for`
      跟真正的 list 行為一致，`compare_superposition()` 本體一行未改）取代 dict，讓疊加證明改成逐顆
      讀入、加總、即釋放。GATE 1（等價性）：修改前後各跑一次 `--limit 300`，300 顆事件逐欄 0 差異
      （provenance 三個 sha256 全 match，僅 --out-dir 路徑字串不同）。GATE 2（記憶體證據，PowerShell
      Get-Process 輪詢，`output/wf0914/D14/measure_peak_ws.ps1`）：905 事件 score 分別以 `--limit 300`／
      `600`／全量三檔量峰值 working set——1310.7 MB／1269.7 MB／1530.0 MB（peak_ws_reported 600→
      1611.8 MB、全量→1649.9 MB），事件數從 300→905（3.02 倍）峰值只從 ~1.3 GB→~1.65 GB，**不是線性
      成長**；全量（無 --limit，就是登記時「跑不完」的那個案例）本次**完整跑完**（status=ok、905/905
      事件、superposition established=True）。GATE 3：`tests/test_stem_verify.py` 49 passed（含
      monkeypatch 詐報 n_stems_summed 的防呆哨兵、真實 CLI 端到端哨兵，逐一重跑確認不受影響）。
      證據 `reports/gate_outputs/wf0914_D14_memory_fix.txt`。原始記錄：見 D14 施工卡
      `docs/workcards/WF0914_D14_stem_memory.md`。

- [ ] **C1 rubber 短瞬態 T60 估計器** — 現行「不足八週期即 N/A」太粗，改用 EDT／Schroeder 反向積分 + 明確拒答條件，把三個 `UNVERIFIED/N/A` 轉成可判定。**需月月裁決可信門檻（幾個週期算數）**。
- [ ] **C2 多音／缺基頻調音器模式** — 只在能可靠拒答模稜兩可的情況下才做。工作量最大、對物理驗證主張價值最小。
- [x] **C3-b 免耳三層驗證（旋律位置 GATE）** — 設計提案 `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md`（2026-08-20，~~未實作~~）：
      **09-25 改 [x]**：「未實作」是 08-20 開卡當時的狀態。下方進度 L1／L2／L3a／報告層／L3b 已全部 ✅
      （證據 `reports/gate_outputs/l1_l2_l3a_melody_gate.txt`、`l1_selftest_v2.txt`、`l3b_cubase_live.txt`），A9 已 [x]；
      「H5 兩項誠實 FAIL」已由 A12（08-22）修好。唯一沒做的是 Cubase GUI 手畫 automation lane，A9 已誠實標註。`[docs-consistency:T5]`
      L1 `melody_verify.py`（score↔WAV 逐事件 onset+pitch 正向驗證，補上「休止安靜≠音在對的位置」的缺口，含五件哨兵）＋
      L2 `TsukiSynthHostProbe`（JUCE host 載磁碟上的 .vst3，A9 四步全自動化，順帶首次驗 plugin 即時路徑的音訊內容）＋
      L3 Cubase 本尊（3a 掃描快取 XML 解析——**已核實 TsukiSynth 在 vst3plugins.xml、blacklist 零筆**；3b AI 開 Cubase 匯出、L1 判定）。
      **2026-08-20 月月裁決：三項全權委託 AI**（原話「你自己想辦法，然後照順序把缺口都補上，我最後再拿去給專業人士聽」）。
      委託範圍與界線：(1) 容差由 AI 依推導自定，**R2 仍然有效——定案後不得為了讓測試通過而調寬**；
      (2) A9 走自動化重定義；(3) 順序 = X2 → L1 → 3a → L2 → piano-roll 報告層 → 3b；
      (4) R7 仍然有效（不 commit）；(5) **最終美學驗收改為外部專業人士試聽**（月月安排），
      物理/位置正確性由 GATE 鏈負責，兩者主張分開。
      **進度（2026-08-20，證據 `reports/gate_outputs/l1_l2_l3a_melody_gate.txt`）**：
      ✅ **L1** `tools/melody_verify.py` 完工——哨兵五件組 PASS（unmodified 全綠 max |onset err| 0.27ms／
      時移+100ms／移調+1半音／刪音／幻音四種竄改全數被抓）；粗偵測(STFT rise、median 床壓拍頻空點)→
      零相位包絡 50% 交越精修（無偏估計）雙段式；onset 容差 ±10ms 定案（實測餘裕 >30×）；
      pitch 沿用已批准 5-cent course-centroid；複音帶碰撞/delay/fm_ratio≠1 一律 fail-closed 拒答。
      fixture `scores/tests/melody_sentinel.score.json`。
      ✅ **L2** `TsukiSynthHostProbe`（CMake target，載磁碟 .vst3）完工——H1 掃描/H2 實體化/
      H3 MIDI 串流渲染+跨實例位元決定性/H4 automation ramp 位元決定性+3-12kHz +8.6dB/
      H5 state round-trip。**plugin 即時路徑旋律位置首次被驗：5/5 PASS（onset ≤1.31ms、pitch ≤1.31c）**。
      H5 兩項誠實 FAIL = A12（→ 08-22 A12 已修，HostProbe 16/16 PASS；現為 89 項）。
      ✅ **L3a** `tools/cubase_scan_verify.py` 完工——真實 Cubase LE AI Elements 12 掃描快取 S1-S5 全 PASS
      （雙 class、Instrument 分類、無 blacklist、快取↔磁碟時戳一致）；S6 誠實揭露部署落差（裝的是 0.2.0）。
      ✅ **報告層** `melody_verify.py --html`——piano-roll 疊圖（頻譜圖底 + 期望音符框
      綠/紅/灰 + 多餘音菱形），獨立頁面、不動已過 M4 目視驗收的主報告。
      ✅ **複音拒答三規則（2026-08-20 夜，moonlight 全曲 1141 事件試跑揭露）**：
      Ra 同音重擊遮蔽（用 dump-modes T60 預測前擊殘響，衰減 < RISE_DB+6dB → 拒答）、
      Rb 並發泛音入帶污染音高（僅拒 pitch、onset 照判）、
      Rc 多重長尾拍頻假 rise（≥2 同帶殘響重疊 → 該 rise 歸因拍頻、拒答列名）。
      全部以 dump-modes 物理資料計算，非啟發式。哨兵 5/5 重驗綠
      （E 幻音改 +2 半音——原 +7 與 Ra 正確衝突，哨兵抓到了設計互動）。
      **2026-08-21 追加三條（moonlight v3 迭代揭露，全部可推導非啟發式）**：
      Rd 床能量拒答（無 rise 只在「前置床近靜音」時才是缺席證明；密集織體+混響墊高的床 → 拒答）、
      Re 低頻精修極限（誤差 ≈10% 包絡上升時間 → f0 < 167 Hz 拒 onset、pitch 照判——連純靜音前置的
      首音都 −17.9ms，證明是估計器解析度不是污染）、
      Rc' 單一 detune course 自拍（三弦 ±5c 在低頻拍週期秒級，深 null 回升 ≠ onset）；
      Ra/Rb/Rc 改用 **有效殘響 = max(乾聲 T60, reverb decay)**（5.8s 混響下乾聲預測失效的修正）。
      哨兵 B 的抓法自動轉移到 extra-scan（Rd 誠實拒答「被錯位音自己弄熱的床」，錯位仍被抓，設計自洽）。
      證據 v3：`reports/gate_outputs/l1_selftest_v2.txt`（12 PASS / 0 FAIL）。
      **月光四輪收斂（v1→v4：1043→651→322→38 FAIL）**；v4 殘餘 38 個 = 低音帶
      Hann 裙擺滲入的確定性量測偏差（非渲染錯誤，physics_verify 單音 0.05c 佐證）——
      **R2 判斷：回報數字停手，不為單曲過擬合**。主張域定案見設計文件 §7：
      強域（單音/稀疏/HostProbe）全綠；弱域（密集低音複音+長混響）誠實拒答 96.6%，
      位置保證由 verify_score 2e 位元決定性承擔。
      ✅ **L3b 完成（2026-08-22 凌晨，月月授權螢幕控制，AI 全程操作真 Cubase）**：
      建 TsukiSynth 軌 → 匯入哨兵 MIDI（路由+tempo 100 對齊）→ plugin GUI 上 Reverb 歸零 →
      Export Wave/48k/24bit → **melody_verify 5/5 PASS（onset ≤2.5ms、pitch ≤0.4c、extra-scan PASS）**；
      加碼 A9 第四步：存檔/關閉/重開/再匯出 → **音訊資料 SHA256 位元全等**（容器 10B 差=iXML 時戳）。
      證據 `reports/gate_outputs/l3b_cubase_live.txt` + 專案 l3b_tsukisynth_verify.cpr 留檔。
      A9 四步覆蓋：掃描✅ MIDI 實彈✅ 存讀✅；automation 於 L2 合約層✅（GUI 畫 lane 未做，誠實標註）。
      註：host 測的是系統部署的 0.2.0（升級部署需月月以管理員權限覆蓋 Common Files\VST3）。
      （09-25 註：現在系統上部署的是 09-10 build，放在 `Common Files\VST3\TsukiSynth_VST3_2026-09-10\` 子資料夾，缺 D12/D9c；Cubase 快取停在 08-22，部署後還沒重掃。見 09-25 快照。`[docs-consistency:H8]`）
      ✅ corpus 81 檔 melody_verify 掃描完成（informational，`reports/gate_outputs/melody_corpus_sweep_informational.txt`）：
      30 檔全綠（強域實證）+ 48 檔含 FAIL（§7 弱域：密集複音/混響/delay，位置保證由 2e 位元決定性承擔）
      + 3 檔 layered 整檔拒答（上游 CLI 無 layer 展開的 --dump-modes；工具已補優雅拒答 exit 3）。
      事件層級 473 PASS / 854 FAIL / 38633 UNVERIFIED（拒答率 96.7% = 域界定的 corpus 級實測）。
- [x] **C3 跨平台容差登記** — **2026-08-22 完成**（月月裁決「照提案登記」，詳見 X3 條目）。

## D. 還要補搜的資料（阻擋上面某些項）

- [~] **D1 梁／板的空氣與輻射阻尼** — ~~**未搜尋，狀態未知**~~ **2026-09-25 WF0925-L1 已補搜到能取得的上限**（`docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md`；證據 `reports/gate_outputs/wf0925_L1_sources.txt`）。弦的公式內建圓截面幾何不適用。**這一項擋住 B3 對 Chromatic 引擎的適用性。**
      結果：8 份全文（Chaigne & Lambourg 2001、Ege 等 2009、Arcas & Chaigne 2010、Chaigne & Doutaut 1997、Humbert 等 2017、Cross & Lifshitz 2001、Zeng 等 2022、Irvine 2010）＋Euphonics＋Wood Handbook；衰減是熱彈性、黏性空氣、聲輻射、支撐損耗幾種機制相加，各有規律。
      文獻反對把 BeamModel `*2` 當物理項，但給不出支撐損耗的數字，無法判斷總量該不該留；另發現模型三個阻尼項在頻率趨近 0 時全變 0（文獻都有常數項）、而且衰減不看舌片厚度。能真正定量的只剩 D7 實測或 D4 論文。缺口**部分閉合**；`*2` 去留 → 裁決包 Q17。
      2026-09-25 WF0925b-BR 另算了「拿掉 ×2」的前後數字（描述用、非 GATE；`reports/beam_x2_option_b_before_after_2026-09-25.zh-TW.md`）：對照本條 D1 已引述的文獻 7 個點，現行 0 個、拿掉 ×2 只有 1 個（鋼 C4）落在範圍內，兩版都是有的點偏高、有的點偏低，文獻仍判斷不了總量。
- [ ] **D2 舌鼓／鑼的槌具接觸參數** — **未搜尋，狀態未知**。**擋住 B4 對 Chromatic 引擎的適用性。** 2026-08-28 進展（見 `docs/D2_CHROMATIC_CONTACT_SEARCH.zh-TW.md` §8）：通用板-槌 `K` 標定表（**Bruno L. Giordano 2005 博論，Padova/IRCAM——非 N. J. Giordano、非 McGill**）已由 Opus 打開本地 PDF 逐格核對通過（§8.3）；中國鑼/木魚/鼓棒三條**仍未核**（本輪未取得原文）。但 handpan/鋼舌鼓/tam-tam 自身成套接觸數據仍缺，且 Giordano 的 `α=3/2` 是採用而非量測、槌頭為硬木/Plexiglas，**缺口未閉合**。
- [x] **D3 `gamma_radiation` 的真實物理來源** — **2026-08-24 由 B3 關閉**：弦不再讀此欄（改用零自由參數三機制公式）；欄位已在 schema 改名為 `beam_plate_gamma_radiation` 並在程式註解誠實標示「只給 Beam/Plate、未溯源」（Beam/Plate 側的溯源仍是 D1 範圍）。
- [ ] **D4 舌鼓 ICSV27 2021 全文** — 機構庫 403，可試作者自存版／ResearchGate。**2026-09-25 WF0925-L1 再試，共 15 條路徑都失敗**（試過的網址記在 `docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md` §6）。月月可以用瀏覽器直接開 `https://unige.iris.cineca.it/bitstream/11567/1063604/1/full_paper_1117_20210430223100647.pdf`，或寫信向作者要（AI 不寄信）。
- [ ] **D5 銅鑼 JCIE 2005 全文** — 付費牆。
- [x] **D6 Wood Handbook Table 5–15（溫度係數）** — **2026-09-25 WF0925-L1 已取得**：官方 PDF 第 5–36 頁，全表 20 列逐字轉錄在 `docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md` §7（R 稽核自己渲染原頁逐格比對相符）。`docs/WOOD_ANISOTROPY_SOURCES.md:157`、`:198` 還寫「未取得」，要另外同步（交接卡權限外）。→ **WF0925b-DS 已同步**（改成「已取得」並指向 D1 文件 §7）。
- [ ] **D7 揚琴／舌鼓／鑼的實體試體量測** — **文獻買不到，只能自己量**（`docs/SPECIMEN_VALIDATION_PROTOCOL.zh-TW.md`）。這是唯一能讓域內引擎升級到 specimen-level 主張的路。
- [~] **D8 tongue_drum 音高-響度斜率與缺泛音（2026-08-28 月光商品 QA 發現）** — **2026-09-08 根因已診斷**（`reports/decision_packets/D8_tongue_drum_diagnosis.zh-TW.md`）：
      樂譜 `exciter:"finger"` 被翻成 4.3–10.8 ms 超軟槌，力脈衝頻譜獨佔 −43.2 dB，補償又被 ±12 dB 上限卡住；改 `wood_mallet` 斜率 41.5 → 5.5 dB（程式零改動）。
      **月月 2026-09-09 裁決 `wood_mallet` → WF0909-D8 已落地（staged）**：兩首月光空靈鼓相關 score 各 1142 顆 tongue_drum 事件改 exciter（揚琴事件不動），
      Rule 10 報告 `reports/d8_tongue_drum_exciter_before_after.md`（200 Hz 以下能量 97.36% → 17.55%、旋律音域 2.64% → 82.44%、單音斜率 37–39 → ~2.7 dB、f0/T60 位元不變），
      verify_score 兩檔 PASS，8 首位元不變基準換 `reports/gate_outputs/b6_method/sha256_before_post_d8.txt`（6 首不變 + 2 首預期改變）。
      （09-25 註：09-10 A14 落地後基準又換成 `sha256_before_post_a14.txt`，兩份只差 physical_piano 一首；**現在一律用 post_a14**，post_d8 只留存檔，拿它比會讓 physical_piano 假紅燈。`[docs-consistency:H1]`）
      **未做**：`exports/products/moonlight_batch1/` 的母帶仍是 08-28 舊渲染。**月月 2026-09-10 裁決：母帶等月光換源（重轉譜）完成後一起重出**，現在不重出（反正授權未淨不能賣）。**D8 引擎面缺陷條目自此改為「樂譜設定問題已解；引擎槌具標定仍掛 D2」。**
      長期項：Chromatic 槌具 τc 重新標定（擋在 D2）、梁模態比值升級（擋在 D4/D7）、補償飽和診斷警告（純新增，可獨立提案）。原始記錄：
      同 velocity 探針渲染實測：tongue_drum MIDI 37→87 RMS 從 −32.8 掉到 −73.1 dBFS
      （**40.3 dB 斜率**；cimbalom 同域僅 4.4 dB），且輸出近純正弦（99.9% 能量在基頻，
      無泛音列；真實鋼舌鼓應有豐富非諧泛音；cimbalom 為 79.5–94.0%）。後果：高音域
      旋律實質不可用（月光空靈鼓版商品被 QA 判暫緩上架，見
      `exports/products/moonlight_batch1/PRODUCT_SHEET.md`「已知缺陷」）。
      **調查方向**：BeamModel 響度 keytrack／`modeAttackEnergy` 對 Beam 路徑的行為、
      Beam 模態截斷；與 D1（梁/板阻尼未溯源）、D2（槌具接觸未溯源）可能同根。
      屬引擎物理層調查，改動會觸發 Rule 10。

---

## 2026-08-02 audit follow-up

- [x] T60 final judgment now requires both the 0.80–1.25 measured/model ratio and at least 8.0 dB of fitted decay; insufficient span fails closed after the 30 s retry. Regression tests include the former false-pass counterexample.
- [x] Render manifest v4 binds WAV, renderer, root score and every recursive layer dependency, plus a canonical dependency-tree SHA256. Layer mutation and legacy-v3 layered false-provenance cases are regression-tested.
- [x] Tuner status/support/label text now uses the higher-contrast `textMid` colour and at least 9 pt base size.
- [x] README/roadmap/playbook wording now distinguishes implementation conformance from external physical validation and reflects the 5-cent course-centroid gate.
- [x] Rebuilt CLI, VST3, Standalone and all three C++ test targets in Release; CTest 3/3, Python 84/84, ASan 3/3, fresh-build `physics_verify.py --full`, pluginval L10 and Steinberg validator 47/47 all pass.
- [x] New 73-score corpus run completed in deterministic round-robin shards: 19/19 + 18/18 + 18/18 + 18/18 = 73/73, 0 fail; the one existing moonlight FX-art exemption remains explicit.
- [x] Added Specimen Measurement v1 schema, hashed evidence-chain verifier and laboratory protocol. Frequency/relative magnitude/T60 are comparable now; unsupported phase/SPL/radiation claims fail closed as `UNVERIFIED`.
- [x] Added the non-human Specimen Measurement v2 pipeline: repeated synchronized CSV → calibrator-derived V/Pa → complex H1/coherence/phase/T60/Pa-per-N/SPL/directivity → uncertainty, hashes, self-contained bundle and report. All v2 comparators are implemented; current synth phase/absolute-radiation model observables correctly remain `UNVERIFIED` until the physical model emits them.

Acceptance snapshot (round-1, 2026-07-17): six Release targets build; CTest and Python contract/metrology tests pass;
schema 80/80; release corpus 73/73 with one existing visible FX-art exemption; event-specific
rules demo 13/13 PASS; `physics_verify.py --full` has no checked failures and three explicit
rubber `UNVERIFIED/N/A` cases.

Round-2 snapshot (2026-07-18, `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md`): six Release targets rebuild
clean; ctest 3/3, pytest 44/44, tuner oracle, schema 80/80 and consonance gates all PASS. `physics_verify.py
--full` has one **honest FAIL** (piano MIDI 60 velocity vs the +6.0206 dB physical-law bound — see pending
decisions). Corpus per-channel rest-RMS re-measurement gives 71/73 net PASS: 2 new honest FAILs
(`summer_m2`/`summer_m3` rest RMS, both traced to a reverb tail, neither exempted) surfaced by the
stricter measurement, not by any audio regression. No §6 tolerance was widened; no new exemption was
registered.

Round-3 snapshot (2026-07-22, `reports/gate_outputs/deepfix3_*.txt`): fixed both round-2 honest FAILs.
Velocity: `physics_verify.py`'s F3 measurement domain moved from wideband RMS to the fundamental's own
±3% band (matching the law's per-mode physical scope; wideband delta is now printed informational-only) —
all 5 modal engines now PASS at MIDI 60, incl. piano (+6.6702 dB, dev +0.65); `--full --skip-amps` is green.
Summer: `reverb.decay` narrowed on both files (wet untouched) — `summer_m2` 2.8→2.6 (2.6 dB worst-case
margin), `summer_m3` 1.2→1.0 (2.5 dB margin); both re-verified PASS incl. determinism SHA256 match. Stale
`rules_v2_demo_001.report.html` (predating its score.json's 2026-07-17 edit) regenerated and re-checked.
No §6 tolerance widened; no new exemption registered; both score edits and the measurement-domain change
awaited 月月's sign-off (musical effect / domain-change ratification respectively) — **ratified 2026-07-23,
see "2026-07-23 round-4 裁決落地" below.**

## 2026-08-06 月月審聽/驗收裁決落地

- [x] **Rule 10 審聽回饋**：全體音色低音偏大、高音偏小（機制＝Phase H 阻尼物理化 + round-2 T60 語意修正疊加，`phase_h_before_after.md` §3 有記錄）。裁決：**短期亮度補償層 + 長期頻變阻尼兩個都做**。短期已落地：`global.effects.eq.{high_shelf_freq_hz, high_shelf_gain_db}`（RBJ 高頻 shelf，documented creative 層、不入物理主張；gain 0 = 硬 bypass，既有 corpus 渲染位元不變——`akashic_opening_bell_001` SHA256 前後一致驗證過；+6dB 實測 3k-12k 帶 +5.67 dB、低頻帶 +0.01 dB）。plugin 端同步 `fx_eq_freq`/`fx_eq_gain` + BRIGHTNESS 面板。長期線見「Verification gaps」阻尼寬頻化條目。
- [x] **M4-4c 首輪驗收回饋**：報告看不出用途（預設讀者懂管線）。已修：`report_html.py` 頁首加「這一頁是什麼？」導讀卡 + 六個區塊各加一行「💬 白話」說明；`ai_radiance_m1.report.html` 已重產，**2026-08-15 月月目視驗收通過 → M4 三項齊備轉 Done**（`ROADMAP_PHYSICS.md` §2 M4 列與 §3 M4-4c 已同步）。
- [x] **M4-4c 二輪回饋「報告像隱藏功能、Standalone 應可當獨立工具」**：`src/ScoreConsole.h` Score 控制台（`c0615fa`）——Standalone 頂列 [Score] 鈕，一鍵渲染 score.json（子程序呼叫同捆 `TsukiSynthCLI.exe`，渲染合約單一來源；輸出 `桌面\TsukiSynth_Renders`）＋開資料夾／開報告／python 產報告。發佈包自此同捆 CLI。**待月月實際操作驗收**。

## 2026-08-06（夜）跨音域響度失衡修正（~~unstaged 待審~~ 已於 2026-08-10 commit `af849ec`，09-25 註）

- [x] **激發端根因修正**（同題第三線，與亮度 EQ 應急線／阻尼寬頻化長期線並行）：
  τc keytrack（`HammerImpulse::tauCForNote`，文獻擬合 f^-0.32）+ noteOn 攻擊能量
  正規化（`ModalResonator::loudnessCompensationGain`，amount=0.78 月月審聽定案，
  已文件化校準層、比照 spectralTilt 劃界）。C2~C7 掃音 spread：Cimbalom 27.3→8.65、
  TongueDrum 29.7→8.13、WaterGong 36.3→8.35 dB；C2 削波消除。`--full` 第一輪
  抓到 velocity 次線性（tongue_drum +4.72 dB 違 F3 律）→ 能量預估改用 velocity=0.5
  Hertz 錨 τc 修正，全綠 `NO CHECKED FAILURES`；ctest 3/3 + pytest 121/121 +
  三 target rebuild 綠。Rule 10 報告：`reports/loudness_keytrack_before_after.md`。
- [x] **corpus 73 檔重驗**——**73/73 全 PASS、0 FAIL、零新增豁免**（A 19/19 +
  B 18/18 + C 18/18 + D 18/18，僅既有 moonlight 豁免保持可見）；邊際檔
  summer_m2/m3 rest RMS 皆過（低音變小聲反而擴大邊際）。存證：
  `reports/gate_outputs/loudnessfix_corpus_{A..D}.txt`。
- [x] **亮度 EQ 應急層去留覆核**——激發端修正落地後，既有 `global.effects.eq`
  高頻 shelf 的補償需求可能已部分消失，月月審聽後決定是否調整建議值/文件。
  **→ 已由 A 區 A4 結案**（2026-08-27 月月裁決「調整文件建議值」，eq 預設不開，程式碼零改動）。`[docs-consistency:T4]`

## 月月待裁決（pending decisions）

- [x] **`verify_score.py` 的 `MODE_F0_TOL_CENTS = 12.0` 是否授權改量測法後收緊**——**2026-07-23 裁決：授權**，改為 course 質心／平均量測法後收緊至 5.0；程式改動（`check_modes()`）由另一輪工作平行進行中，尚待該輪 GATE 存證（見「2026-07-23 round-4 裁決落地」）。
- [x] **殘差頻譜能量檢查：門檻轉判定制的批准**——**2026-07-23 裁決：批准**，轉判定制、門檻取 -60.0 dB re total（依據 round-2/round-3 累計實測基線 -74.7~-83.1 dB re total，留有 ≥14.7 dB 邊際）；程式改動（`tools/physics_verify.py`）由另一輪工作平行進行中，尚待該輪 GATE 存證。
- [x] **spectralTilt heuristic 層去留**——**2026-07-23 裁決：降級保留**，聲音不動，劃界為已文件化 creative 層（不算入物理主張），已同步 `ROADMAP_PHYSICS.md` §0 與 `README.md` 域表註記。
- [x] **【2026-07-18 round-2 → 2026-07-22 round-3 已修正】piano velocity 物理律「違規」**——量測域變更（寬帶→基頻窄帶）**2026-07-23 裁決：追認**，已同步 `ROADMAP_PHYSICS.md` §6 velocity 列依據欄。詳見 `DEVLOG.md` 2026-07-22 條目、`reports/gate_outputs/deepfix3_selftest.txt`／`deepfix3_gate_full.txt`。
- [x] **【2026-07-18 round-2 → 2026-07-22 round-3 已修】corpus 逐聲道 RMS 揭露的 2 個既有 rest 超標**——`summer_m2`（decay 2.8→2.6）／`summer_m3`（decay 1.2→1.0，累計 2.1→1.0）的殘響藝術效果**2026-07-23 裁決：接受**。機器 GATE 已於 round-3 過（`verify_score.py` 全項 PASS 含 determinism SHA256 match）。
- [x] **Rule 10 前後對照報告審閱**（**→ 已由 A 區 A1 結案：2026-08-26 月月裁決「放行」，整批接受、無指名回退**。`[docs-consistency:T4]`）——`reports/deep_fix_before_after.md`（2026-07-18 round-2）：8 首代表曲目改動前後 RMS/頻譜質心/T60/f0 比對，`physical_piano` 是唯一變大聲的一首（+2.346 dB），值得月月過目確認方向是否符合預期。**2026-08-15 月月回饋「看了但看不懂」→ 已補 §00 白話導讀**（一句話結論、逐首白話對照表、主因＝τ→T60 重新定義使音尾變 1/6.9、舌鼓泛音整組換掉的說明、哪些數字不可信、決策選項）。待月月讀完白話版後裁決「整批接受」或「指名回退某項」。

## 2026-07-23 round-4 裁決落地

> 月月於對話中對 2026-07-22 round-3 留下的五項待裁決明示「都照推薦的做」。本輪只落地文件記錄，不改 `src/`／`tools/` 程式碼。

- 決議：(1) velocity 量測域（寬帶→基頻窄帶）追認；(2) `summer_m2`/`summer_m3` decay 收斂（2.8→2.6、2.1 累計→1.0）接受；(3) `spectralTilt` 降級保留，劃界為已文件化 creative 層；(4) 殘差頻譜能量轉判定制 -60.0 dB re total；(5) `MODE_F0_TOL_CENTS` 授權改 course 質心量測法後收緊至 5.0。
- 文件同步：`ROADMAP_PHYSICS.md` §0 域表（Cimbalom/Piano 列 spectralTilt 劃界註記）+ §6 容差表（velocity/殘差/f0 三列）；`README.md` Physical Verification 域表同步 spectralTilt 劃界註記；本檔（`TODO.md`）五項裁決逐條關閉；`DEVLOG.md` 新增本輪條目。
- **(4)（殘差判定制 -60.0 dB）與 (5)（f0 course 質心 5.0）的程式碼改動已於同日稍後落地並全 GATE 綠**（文件線寫作當下平行進行中，故上一版此條標「尚未落地」）：`tools/physics_verify.py` `RESIDUAL_ENERGY_LIMIT_DB = -60.0` 判定制生效（5 引擎實測 -74.7~-83.1 dB 全 PASS，selftest 新增未建模強峰反例會 FAIL）；`tools/verify_score.py` `course_f0()` 振幅加權質心 + `MODE_F0_TOL_CENTS = 5.0`（moonlight yangqin 實測 5.013→0.019 cents，證實舊讀數為 string-0 設計偏移非真走音）。GATE 存證：`reports/gate_outputs/deepfix4_selftest.txt`／`deepfix4_gate_full.txt`（`F5 residual energy : PASS`、`RESULT: NO CHECKED FAILURES`）／`deepfix4_pytests.txt`（32+26 測試全過）。
- **corpus 全量重驗（新 f0 質心 + 5c 收緊下）：73/73**——四分片 `deepfix4_corpus_{A,B,C,D}*.txt`：B 12/12、C 21/21、D 22/22 全過；A 分片 18 檔中 `moonlight_sonata_complete` 首跑 determinism 檢查因 CLI 第二次渲染進程啟動失敗（exit 0xC0000142 = STATUS_DLL_INIT_FAILED，高併發環境故障，同 deepfix2 輪 autumn_m1 前例）記 FAIL；**2026-07-23 已單獨重驗：ALL CHECKS PASSED（含既登記 moonlight 豁免）、determinism SHA256 aaaa46e8... 兩次一致，非真回歸，已解除**。其餘 17 檔含 ai_radiance 5 檔全過。豁免仍僅 moonlight 一筆，零新增。
- Rule 1/2/4：本輪未執行任何 git 變更狀態指令，未調寬任何容差（(4)(5) 皆為收緊方向），文件中的新數字（-60.0 dB、5.0 cents）均註明批准依據與日期。

## Before merging this branch

> **歷史段落**（09-25 註）：分支自 08-26 起已多次 merge 進 `main`——`b47d550`（08-26）、`361101e`（08-28）、`64afb49`／`b7e4330`（08-30）、`34aa904`（09-07）、`b56747d`（09-14）、`3f9b90a`（09-15）。下面各項依實況逐條結案。`[docs-consistency:T5]`

- [x] Review the complete P1–P7 diff; keep it as one atomic physics-hardening commit because production changes, fail-closed contracts, CI gates and their evidence documentation must land together.
- [x] Push the branch and let the updated Windows CI run Python unit tests, CTest, build targets, the event-specific consonance gate and `physics_verify.py --full` — 2026-08-05 push（`aba7f84` specimen 批 + `4cf4817` scene→reverb 批），CI run 31004676104 全步驟綠。
- [x] Validate VST3 scan, MIDI, automation and state round-trip in the intended DAW.
      **→ 由 A9／L3b 完成（2026-08-22 真 Cubase）**：掃描、MIDI 實彈、專案存讀都有真 host 證據（`reports/gate_outputs/l3b_cubase_live.txt`）。
      **但書**：DAW 內的 automation 只驗到 L2 HostProbe 合約層，Cubase GUI 手畫 lane 沒做（A9 已誠實標註）。當時測的是部署的 0.2.0。
- [~] Perform a visual accessibility review of the tuner and generated HTML report with the intended deaf user; automated tests cannot certify readability.（09-25 拆成兩項：）
  - [x] HTML 報告：2026-08-15 月月目視驗收通過（M4-4c，見「2026-08-06 月月審聽/驗收裁決落地」）。
  - [ ] 調音器可讀性：查不到目視證據，待月月本人看。

## 2026-07-18 round-2 修復（完成，詳見 `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md`）

> 稽核來源：2026-07-18 本 session 四線審查。GATE 證據路徑規約：`reports/gate_outputs/deepfix2_*.txt`。

- [x] 工具/量測線：`tools/physics_verify.py` — F1 特徵值錨（`CANTILEVER_BETAL`/`free_plate_omegas()`）接回消費點、F2 f0 主錨改回 12-TET ET 理論值、F3 velocity 律上限雙重判定（`6.0206 ± 1.0 dB`）、F5 殘差頻譜能量資訊性檢查、selftest 反例 4a/4b；`tests/test_physics_verify.py` 新增 19 測試，24/24 PASS。
- [x] 引擎/渲染線：`src/score/ScoreRenderer.h`（dumpModes custom-atoms 堆積配置杜絕懸空指標）、`src/engines/CimbalomEngine.h`/`ChromaticEngine.h`（spectralTilt 註解、過期 mix 註解修正）、`src/physics/StringModel.h`/`BeamModel.h`/`PlateModel.h`（velocity 慣例與正規化語意註解）、`src/dsp/NoiseGen.h`（pink 係數標註取樣率相依）、`CMakeLists.txt`（TunerTest target 補齊設定、VERSION 0.2.0→0.3.0）；ctest 3/3 PASS。
- [x] score 資產線：`tools/verify_score.py` 逐聲道 rest RMS（取代 `(L+R)/2` 混降）、`src/cli/RenderApp.cpp` render manifest v2（新增 `wav_sha256`）；`tests/test_verify_score_contract.py` 新增 12 測試，14/14 PASS；probe SHA 基線比對確認 manifest 修改未影響音訊位元。
- [x] 文件/設定線：`.gitignore` binA/binB 字面規則、CI push 分支 `main` + `fix/**`、README 狀態表/目錄/build 依賴、§6 容差登記表同步（月月 2026-07-18 授權，四列：T60/velocity/殘差/休止RMS）——完成。
- [x] 各線 GATE 輸出彙整與零回歸確認：9 項 GATE（rebuild/ctest/selftest/`--full`/tuner oracle/pytest/schema80/consonance/probe SHA）+ 4 分片 corpus + HTML 抽驗全部執行並存證於 `reports/gate_outputs/deepfix2_*.txt`；`--full` 誠實 FAIL 於 piano velocity 物理律（見「月月待裁決」）、corpus 於 `summer_m2`/`summer_m3` 誠實 FAIL（逐聲道量測揭露既有超標，非回歸）；`autumn_m1` determinism 為環境暫時性故障已重驗排除；零 §6 容差放寬、零新增豁免。

## 2026-07-22 round-3 修復（完成，詳見 `DEVLOG.md` 2026-07-22 條目 + `docs/DEEP_FIX_ROUND2_2026-07-18.zh-TW.md` round-3 補記）

> 處理範圍：round-2 遺留的兩項待裁決（piano velocity「違規」、summer m2/m3 rest 超標）。GATE 證據路徑規約：`reports/gate_outputs/deepfix3_*.txt`。

- [x] `tools/physics_verify.py` F3 velocity 量測域修正：寬帶 RMS → 基頻 ±3% 窄帶（`measure_band_rms_db()`/`FUND_BAND_HALF_WIDTH`），判定式數值未動；寬帶 delta 降為資訊性行。5 個 modal 引擎 MIDI 60 velocity 48→96 全數 PASS（見「月月待裁決」量測域追認項）。`tests/test_physics_verify.py` 新增 3 測試，共 47/47 PASS。
- [x] `scores/classical/vivaldi_four_seasons/summer/vivaldi_four_seasons_summer_m2.score.json`（decay 2.8→2.6）、`.../summer_m3.score.json`（decay 1.2→1.0）：休止 RMS 超標修復，`verify_score.py` 全項重驗 PASS 含 determinism SHA256 match；完整掃描見 `reports/gate_outputs/deepfix3_summer_rest_sweep.txt`（藝術效果待月月確認）。
- [x] `scores/originals/rules_v2_demo/rules_v2_demo_001.report.html` 過期重生成（原檔停留在 score.json 2026-07-17 改動前）——已關閉，不再是待辦。
- [x] GATE 彙整：selftest 11/11、pytest 47/47、`--full --skip-amps` PASS（NO CHECKED FAILURES）、summer 兩檔 verify PASS、未觸碰的 `physical_piano.score.json` 回歸抽驗 PASS，全部存證於 `reports/gate_outputs/deepfix3_*.txt`；零 §6 容差放寬、零新增豁免。

## Verification gaps that must stay explicit

> 2026-08-15：各條的文獻現況與可開工性已整理到 [`docs/RESEARCH_INDEX.md`](docs/RESEARCH_INDEX.md)，
> 可執行工作項見本檔開頭的「待辦總表」。下面保留缺口本身的定義（不得因為
> 找到文獻就刪除——缺口關閉的條件是 GATE 通過，不是資料到手）。

- [ ] Obtain citable or measured values for every material's `beta_air` and `gamma_radiation`.
      **弦：已用零自由參數第一原理公式關閉**（Cuesta & Valette 三機制，B3，2026-08-24）→
      `docs/STRING_DAMPING_SOURCES.md`；弦不再讀這兩欄，欄位改名
      `beam_plate_beta_air`/`beam_plate_gamma_radiation` 只給 Beam/Plate。
      **Beam/Plate 仍未溯源（D1）**——本缺口對 Chromatic 引擎維持開放。工作項 D1（B3/D3 已關）。
      **09-25 現況**：D1 仍未搜尋；BeamModel 的 `*2` 經驗阻尼加權去留也卡在 D1，09-25 才正式登記（見「2026-09-25 盤點新登記」）。`[docs-consistency:T8]`
- [ ] Replace single-frequency damping anchors with broadband/specimen measurements and uncertainty intervals. **2026-08-06 月月裁決升級**：Rule 10 審聽確認材質物理化後全體音色「低音變大聲、高音變超小聲」（`phase_h_before_after.md` §3 已記錄的機制——單頻 η 錨高估高頻衰減是主因之一），本項定為該問題的**長期物理修法**；短期先以 `global.effects.eq` 亮度補償 creative 層應急（同日已落地，見下）。
      **2026-08-10 實作完成但卡住**（程式仍 unstaged）：寬頻化揭露模型缺頻率無關的損耗通道，C2 的 T60 由 39 s 變 129 s、corpus 掉到 72/73 → `reports/damping_broadband_findings.md`。
      該缺口的閉式解已找到（琴橋導納），**本項的前置是 B1**。工作項 A2 / B2。
      **09-25 現況**：上面「程式仍 unstaged」「卡住」是 08-10 的狀態。B1（琴橋導納）、B2（寬頻化收尾）08-21 Done，08-22 月月接受後 commit（見 A1'），C2 的 T60 由 128.75 s 收斂到 17.66 s，corpus 73/73 回到全 PASS；**弦的部分已解**。
      缺口保留 [ ]，因為還缺兩塊：實體試體量測與不確定度區間（D7）、梁/板的阻尼溯源（D1）。`[docs-consistency:T8]`
- [ ] Add the synth-side calibrated force → displacement → radiated pressure/SPL model, including pickup/microphone position, signed/complex modal residue and spatial radiation. The v2 measurement pipeline/comparators are complete; this remaining item is specifically the physical prediction model.
      **輻射理論骨架與絕對校準慣例已備**（1.05 m 球面、1.0 ≡ 1 Pa ≡ 94 dB）→ `docs/EXTERNAL_ANCHOR_SOURCES.md` §1–§3。
      合成端預測模型仍未實作；相位維持 `UNVERIFIED`。工作項 B6。
      **09-25 現況**：B6 方案 B 08-28 Done——`--dump-modes` 已輸出 `absolute_pressure_per_force` 和 `acoustic_transfer[]`，但這是月月裁決的慣例錨定，不是實測也不是推導。
      B7 第一原理力鏈停在 09-15 裁決的合法終點（Phase 1 部分完成）。拾音位置、相位、指向性仍 `UNVERIFIED`，缺口維持開放。`[docs-consistency:T8]`
- [ ] Add coupled-body/soundboard/sympathetic-resonance and realistic damper/pedal physics for piano.
      **閉式公式鏈完整、只需新增音板厚度一個參數** → `docs/BRIDGE_ADMITTANCE_SOURCES.md`。
      是阻尼寬頻化／輻射／木材異向三項的前置。工作項 **B1（建議最先做）**。
      **09-25 現況**：B1 已 Done（08-21），但它是無限板導納損耗通道，重現不了 Wogram 量到的相鄰半音 5:1 落差（有限音板的共振峰谷結構，`reports/damping_broadband_findings.md` §4.1）。
      有限音板共振、共鳴、制音器/踏板都還沒做，缺口維持開放。`[docs-consistency:T8]` `[open-work:L1-longterm]`
- [ ] Replace the velocity proxy with a parameterized nonlinear contact solver using hammer mass, compliance and geometry.
      **鋼琴逐音 `K`/`α` + 槌質量 + Stulov 遲滯參數已備** → `docs/HAMMER_CONTACT_SOURCES.md`。
      現行 `v^-0.2` 對應 `α=1.5`（純赫茲），實測鋼琴氈是 `α=2.3~3.0`。
      **僅適用 Cimbalom/Piano；會撞 §6 velocity 判定。** 工作項 B4 / D2。
      **09-25 現況**：上面「現行 `v^-0.2`」是 B4 之前的說法。B4 Felt 路徑（Cimbalom/Piano）的非線性接觸求解器 08-27 已 Done（F3 主張域二分，見 B4 條目）；
      Chromatic 仍卡在 D2，本缺口對 Chromatic 維持開放。`[docs-consistency:T8]`
- [ ] Model anisotropic/orthotropic wood, temperature and humidity where those claims are needed.
      **24 樹種彈性比 + 25 樹種泊松比 + 含水率公式已備** → `docs/WOOD_ANISOTROPY_SOURCES.md`。
      **建議等 B1 的音板需要 `D` 時一併進場**；單獨做效益低、破壞面大。工作項 B5 / D6。
      **09-25 現況**：B5 異向 schema 08-28 已入庫，但沒有任何程式讀它（死資料），Kirchhoff 板改異向版沒做，缺口維持開放。`[docs-consistency:T8]`
- [ ] Validate models against external measured recordings or laboratory modal data not generated by TsukiSynth itself.
      **揚琴／舌鼓／鑼都有公開量測文獻**（初版「證據是零」已更正）→ `docs/EXTERNAL_ANCHOR_SOURCES.md` §5.1。
      但已取得的方法學等級不足、其餘卡付費牆；**可信外部錨仍須實體試體量測**。工作項 D4 / D5 / D7 / A8。
      **09-25 現況**：A8 已裁「無可商用校準資料集 → 私下對照參考」（TU Berlin 為 CC BY-NC-SA），D7 實體試體仍沒做，缺口維持開放。`[docs-consistency:T8]`
- [x] Establish cross-platform numerical reproducibility rules (bit identity where possible, numeric/audio tolerance otherwise).
      **工具與 CI 三平台矩陣已就位、本機 GATE 全過**（`tools/crossplatform_verify.py`）。
      Rule 2：無登記容差時 exit 3 `UNREGISTERED` 只印數字不判定。
      **跨平台實測數字須 push 後由 CI 產出。** 工作項 A5 / C3。
      **→ 09-25 改 [x]**：X3（2026-08-21，CI run `32446987833` 三平台實測數字）＋C3（2026-08-22 月月裁決照提案登記 `scores/crossplatform_tolerance.json`）完成，`cross-platform-compare` 已是阻斷式 GATE，符合本節「GATE 通過才關缺口」的規定。
      **注意**：CI 的 Linux leg 標籤寫 clang，實際編譯器是 GCC 13.3（`physics.yml` 沒設 CC/CXX）。所以三平台實際是 MSVC／GCC／AppleClang，日後登記跨平台容差要對到正確編譯器。`[docs-consistency:T5]` `[懷疑者補抓的漏項（code）]`
- [ ] Add a polyphonic/missing-fundamental tuner mode only if it can refuse ambiguous cases reliably; the current target-aware monophonic detector must not guess.

## Honest N/A cases

- [ ] Design a short-transient estimator for `cimbalom/rubber`, `tongue_drum/rubber` and `water_gong/rubber`. Current T60 is only 14–28 ms, shorter than eight cycles at the probe pitch, so `--full` reports these three cases as `UNVERIFIED/N/A`.

## Deliberately outside the physical claim

- FM Piano, Custom Harmonics' authored ratios, Body macro and the artistic effect chain may remain useful, but must stay labelled non-physical/half-domain.
- Sample/granular layers do not become physical evidence merely because they are reproducible.
