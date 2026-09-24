# TsukiSynth 交接文件

> 交接視窗：**2026-09-25**　分支：`fix/deep-physics-audit-20260716`
> （origin 上是 `766d21d`，`main`=`3f9b90a` 已 merge 同步，CI 三平台全綠；
> **WF0914 成果 2026-09-25 依月月裁決分 7 個 commit 入庫（未 push；hash 見 git log）**，見 §1 第 1 點）
> **新 session 請先讀完這一頁再動手。** 09-25 現況盤點在 `reports/status_check_2026-09-25/`（結論 `STATUS_CHECK.zh-TW.md`、逐條證據 `APPENDIX_findings.zh-TW.md`），新發現摘要見 §1-1。
> WF0914 輪細節與五項裁決（09-15~16）在 `TODO.md` 開頭快照；歷史決策在 `DEVLOG.md`；流程規約在 `docs/workcards/WF0914_README.md`（沿用 `WF0907_README.md`）。

---

## 0. 一句話現況

**WF0914 輪（09-14～16）的成果：push+merge+CI 修紅、B7 Phase 0/1（dumpModes 欄位撤回版）、D9～D15 七缺口、月月五項裁決落地（D9c `kIrWetMakeupGain=26.9f` 補平 IR −28.6 dB 落差）。這些在 2026-09-25 依月月裁決分 7 個 commit 入庫（未 push）。
09-25 對 staged 樹重跑全套 GATE，全綠，每項數字都和 09-15 基線相同；這也是 D9b/D9c 落地後第一次跑全套。
同日的現況盤點（9 agents、128 條發現、0 條被推翻）查到 repo 沒登記過的問題，最要緊的三條：給愛麗絲全曲 16 顆弱基頻 FAIL（準備上架的母帶含這 16 顆）、D9c 沒有硬 GATE、發行用 CI 第一次打 tag 一定紅。另外，系統上部署的 VST3 仍是 09-10 的舊 build（§1-1、§1 第 4 點）。
接下來的 WF0925 輪（AI 能處理的都處理，成果照慣例 staged 不 commit）正在進行，結果之後另外更新交接。**

## 1. 立刻要知道的四件事

1. **git 狀態**：origin 分支 HEAD `766d21d`（09-15 凌晨 push，`main`=`3f9b90a` 已 merge），CI 三平台全綠
   （MSVC／GCC 13.3／AppleClang；Linux leg 的 label 寫 clang，實際是 GCC，見 §1-1）。
   **WF0914 的 121 個 staged 檔 2026-09-25 依月月裁決分 7 個 commit 入庫（未 push；hash 見 git log）**：
   c1 B7P1 引擎純函式／c2 D12 state 遷移／c3 D9c IR 補償／c4 D14+D15 驗證工具／c5 研究文件與裁決包／c6 施工卡+GATE 證據／c7 交接文件（含 09-25 文件修正）。
   清單與 commit 訊息在 `reports/status_check_2026-09-25/commit_lists/`（已驗證 121 檔無重複、無遺漏、無 CR）。
   不在這 7 個 commit 裡：`docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md`（repo 是 PUBLIC，要不要進版控待月月決定）、盤點資料夾 `reports/status_check_2026-09-25/`。
2. **五項裁決已下（月月 2026-09-15「五題全照建議」＋09-16 D9 選 A，各裁決包有記錄）**：
   B7=§5 路徑 C＋(a) 乙案（本輪合法終點：Phase 0 完成、Phase 1 部分完成、Phase 2/3 BLOCKED，純函式保留）；D9=(a)+A 案已完工（D9b 量出結構性 −28.6 dB 固定差 → D9c 落地 `kIrWetMakeupGain=26.9f`，四組落差歸零、8/8 位元不變，**D9 關閉**）；
   D11=C（patch 存檔，新登記 D11-F5 根因卡）；D13=B（主張域收窄落地
   `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md`）；D15=A'（設計文件 §8.5 已加放鍵段 ~7.2c 已知上界）。
   **落地尾巴（09-25 盤點查到）**：B7 裁決包 §6 第 3 點要求同步 ROADMAP/TODO 的 B7 條目，盤點時還沒做（`staged-review:D-doc-3`）；D13 的 `PlateModel.h` 檔頭與 water_gong_free 描述同步仍欠（`open-work:D13-sync`）。
   細節見 `TODO.md` 開頭快照。**兩封信（TU Berlin、Iowa MIS）09-15 已寄出，等回覆**（repo 裡查不到回信記錄）。
3. **月月是聾人開發者，全程免耳驗收。** 物理/位置正確性由 GATE 鏈負責，美學驗收交給外部專業人士。corpus **75 檔**；8 首位元不變基準用 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`。pytest 基線 **270 個測試**（264 passed+1 skip+5 xfail）；HostProbe **89 項**。
   **09-25 重跑（staged 樹）全綠**：ctest 4/4、pytest 270、`--full` NO CHECKED FAILURES、`--selftest` 13 行全 PASS、`verify_score --all` 75/75（1 項既有豁免）、HostProbe 89 PASS／0 failures、位元不變 8/8 IDENTICAL。log 在 `reports/status_check_2026-09-25/gate_logs/`。
   （09-15 整合卡跑在 D9b/D9c 之前。D9b/D9c 各自只跑了 GATE 1-5／1-6，沒跑全套 pytest 和 75/75，09-25 這次補上了。）
4. **等月月的事**（完整排序見 STATUS_CHECK §3-1）：
   - **VST3 部署實況（09-25 查，跟舊寫法「09-14 已部署」不同）**：系統上是 `C:\Program Files\Common Files\VST3\TsukiSynth_VST3_2026-09-10\TsukiSynth.vst3`。
     整個包裝資料夾被放了進去，所以多一層子資料夾，頂層已經沒有 `TsukiSynth.vst3`。這份是 **09-10 23:46 的 build，缺 D12 和 D9c**（拿 HostProbe 測它，剛好 5 個 D12 檢查 FAIL）。
     另有舊副本 `C:\Program Files (x86)\Common Files\VST3\TsukiSynth.vst3`（07-12 build）和 `%APPDATA%\VST3\TsukiSynth.vst3`（05-07）。Cubase 的 VST3 快取停在 08-22，仍指向已不存在的頂層路徑（v0.2.0），部署後沒重掃過。
     **commit 後要不要用新 build 重新部署、清掉舊副本（會動系統資料夾），等月月同意。**
   - **渲染器存檔**：clean_batch2 的 50 份 manifest 指向的 CLI（`build/` 09-15 版，sha256 `9123db8f…`）已備份到 `exports/renderer_archive/`（gitignored）。重建 `build/` 後 CLI 雜湊一定會變，要重現商品母帶就用這支。
   - **變現線**：計畫在 `docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md`；上架前的五項裁決在 `exports/products/clean_batch2/PRODUCT_SHEET.md` §5（售價、AI 署名、全曲版、聽人把關、賣家帳號）。其中第 3 題「全曲版削波要不要重渲」的前提已不成立（§1-1 第 4 條）。
   - **小事**：Limbus 和 Yamaha 09-14 就裝好了（§11），剩兩件要月月回覆：Limbus 有沒有用金鑰啟用（磁碟上查不出來）；`Downloads\不知道有沒有用` 裡約 470 MB 的解壓殘留要不要清（刪檔不可逆，AI 不會自己刪）。A10 Score 控制台實操仍等月月。

### 1-1 09-25 盤點新發現（repo 之前沒登記；細節見 STATUS_CHECK §2 與 APPENDIX 條目）

1. **給愛麗絲全曲 16 顆弱基頻 FAIL**（`TODO.md` 登記為 **D16**；E5@0.278×9、A5×4、A6×2、A#6×1；基頻比第二泛音低 6～19 dB）。A14 B-2 把力脈衝的深零點從 G5 搬到了別的「音高＋力度」組合，08-30 時這 16 顆都是 PASS。clean_batch2 的給愛麗絲母帶含這 16 顆，所以 A14 不能算整體關閉。→ STATUS_CHECK §2-1、`open-work:N1-fe16`
2. **D9c 沒有硬 GATE**：K-02 只印數字（`tests/audit_repro.cpp:1458` informational），HostProbe 不量 IR 電平，8/8 走的是 CLI（不經 EffectChain）。把 `kIrWetMakeupGain` 刪掉，全套 GATE 仍然會是綠的。→ STATUS_CHECK §2-2、`staged-review:D9c-guard`
3. **`release-physics.yml` 第一次打 tag 一定紅**：`:45` 漏建 SpectrumViewTest（跟 `766d21d` 修的是同一個坑），`:50` 用 unittest，只收得到 199/270 個測試；這支 workflow 從沒跑過。→ STATUS_CHECK §2-3、`engineering-gaps:E1`
4. **「全曲版 41 個削波樣本」是誤讀**：那個數字是正規化之前算的（`src/score/WavWriter.h:25-43`），母帶實際峰值 0.95，沒有平頂。→ STATUS_CHECK §2-4、`release-readiness:R3`
5. **6 個 loop 檔長度不是整小節**：後面多接了餘響尾巴（例：Akashic Meditation Loop 24.3 s，照 score 的 BPM×小節數應為 16.0 s），但買家拿到的 README 寫「可無縫循環」。→ STATUS_CHECK §2-5、`release-readiness:R4`
6. **VST3 動態連結 VC++ runtime**（MSVCP140/_2、VCRUNTIME140/_1）：買家電腦沒裝可轉散發套件時，DAW 會載不進來。→ STATUS_CHECK §2-6、`engineering-gaps:E4`
7. **VST3 Program 參數會錯位**：program 格數在建立 instance 時就固定了，但使用者 preset 會增減，又依名稱排序。→ STATUS_CHECK §2-7、`engineering-gaps:E7`
8. **pluginval／Steinberg validator 最後一次是 08-06**：之後改過 tail、IR state、D12、D9c，都沒重驗。→ STATUS_CHECK §2-11、`engineering-gaps:E2`
9. **D15 的兩個 strict xfail 永遠不會 XPASS**：pin assert（`tests/test_measurement_selfcal.py:229`、`:251`）排在 ≤1 c 判定之前，數字漂移抓不到，估計器變好也抓不到。→ STATUS_CHECK §2-8、`staged-review:D15-xfailpin`
10. **CI 的 Linux leg 實際是 GCC 13.3**：`physics.yml:138` 的 label 寫 `ubuntu-24.04-clang`，但 run 34880536096 的 log 顯示 GNU 13.3.0。之後登記跨平台容差（R2）時，資料要對到正確的編譯器。→ APPENDIX「懷疑者補抓的漏項（code）」

另有兩條文件面的：`wf0914_D9c_ir_makeup_gain.txt:252-254` 說 HostProbe 原始碼搜不到 IR 字樣，實際有 83 行命中（結論本身仍成立）→ STATUS_CHECK §2-9；B7 裁決同步漏做 → STATUS_CHECK §2-10。每條由誰做、做什麼，見 STATUS_CHECK §3～§5。

## 2. 這個專案是什麼

聾人使用者（月月）+ AI 不靠聽感、靠物理理論精確模擬聲音的 JUCE 8 VST3 合成器。
**唯一驗收依據 `ROADMAP_PHYSICS.md`**，§1 十條強制規則開工前必讀（R1 只認 GATE 輸出／R2 禁調寬容差／R3 禁縮 GATE／R4 禁未溯源常數／R6 改 src 必跑 `--full`＋三 build／R7 不 commit／R10 渲染改變要前後對照）。
**X4 規約**：跑 `ctest` 前必先重建測試 target（現為五個：Audit/Tuner/PhysicsModels/SpectrumView/HostProbe）。
四個引擎：Cimbalom/Piano（弦）、Tongue Drum（梁）、Water Gong（板）、FM Piano（域外）。

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

WF0914 輪（09-14～16）的成果 09-25 分 7 個 commit 入庫，摘要見 §0～§1 和 `TODO.md` 開頭快照，逐卡證據在 `reports/gate_outputs/wf0914_*`。

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
- ④ HostProbe（89 項）：H6 變動 block size 位元相同（含水鑼 glide）、H7 user preset 三情境（F-03 落地後為硬 CHECK）、H8 tail ≥ 引擎 worst-case、D12 舊 state 遷移三情境。
  **必須在 repo 根目錄執行**：H8 用目前工作目錄找 `data/materials.json`（`tests/host_probe.cpp:1429`），在別的目錄跑會多出 4 個假 FAIL。HostProbe 不在 ctest（`CMakeLists.txt:255` 刻意不註冊），也不在 CI。
- **D9c（IR 補償增益）目前沒有硬 GATE**：K-02 是 informational，只印 IR−ALGO 的差（09-25 實測 +0.112 dB），沒有任何 CHECK。要不要加 |IR−ALGO| ≤ 0.25 dB 的 CHECK，待月月裁決（改 tests 要走 R6）。
- **CI 覆蓋**：每次 push 跑 4 個 ctest、pytest 270、`physics_verify` selftest/t60/full、verify_score 6 首 smoke、三平台 CLI 渲染、Windows ASAN。**沒進 CI 的**：HostProbe、pluginval/validator、全 corpus 75 首、8/8 位元不變（`engineering-gaps:E19`）。

## 5. 下一步候選（月月選主線；09-10 四裁決已落地，見 §5-0；09-15~16 五裁決已下，落地尾巴見 §1 第 2 點）

### 5-0 已落地的四裁決（2026-09-10～11）

| 裁決 | 落地 |
|---|---|
| C10 選 A | 主張域收窄寫進設計文件 §8.5/§9.7：量測器含 ≤1.18 cent 已知誤差，±5 cent 門檻不變，**不可宣稱 ≤1 cent**；C10C 工具部分入庫、時域 NLS 候選存 `reports/c10c_nls_candidate.patch` |
| A14 放行 | `git apply` 落地，Opus 稽核 PASS（含牙齒：還原公式 sha 精準回舊值）；7/8 位元不變只 physical_piano 變；基準改 `sha256_before_post_a14.txt`（09-25 盤點：B-2 引出給愛麗絲 16 顆新弱基頻 FAIL，見 §1-1） |
| 月光母帶 | 等換源重轉譜後一起重出，現在不動 |
| 兩封信 | 草稿 `docs/correspondence/2026-09-10_TU_Berlin_*.md`、`_Iowa_MIS_*.md`，月月自寄 → **09-15 已寄出，等回覆** |

### 5-1 主線候選（依價值排；~~刪除線~~=已完成或已裁決）

1. ~~**push + merge `main`**~~ **09-15 完成**：CI 三平台全綠（含修掉 09-07 起的 spectrum_view 紅燈）。
2. **月光／四季換源重轉譜**（解上架限制的唯一路；轉譜 GATE `score_vs_midi_verify.py` 已備；D8 母帶重出掛在這後面；擋專輯 Vol.2）。
3. **UI 功能規格送設計端**（`docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md`，月月決定找誰；v1.1 在 D9c 後有過時處，送出前要先同步，見 `open-work:U1-spec-sync`）。
4. ~~**B7 第一原理力鏈開工**~~ **09-15 裁決結案（路徑 C＋(a) 乙案）**：Phase 0 溯源文件完成（`docs/HAMMER_VELOCITY_SOURCES.md`、`RADIATION_POWER_SOURCES.md` §8）；Phase 1 純函式+五條測試落地，**dumpModes 欄位撤回**（proxy 查證翻案：score velocity 實為 `base×MIDI/90±微調`，非 MIDI/127）；Phase 2/3 本輪不做，重啟前提見裁決包 `B7_phase2_and_open_items.zh-TW.md` §6。
5. ~~**D9～D15 缺口**~~ **09-15～16 全數處理並裁決**：D9（D9c 落地）、D12、D13（選 B）、D14、D15（選 A'）關閉；D10 等付費牆文獻；D11 選 C，patch 存檔，排「D11-F5 根因調查」卡。詳見 §7 與 `TODO.md` 開頭快照。
6. 09-25 盤點新增的候選（弱基頻零點地圖、loop-ready 版、pluginval 重驗、release CI 修正等）見 STATUS_CHECK §3-3、§3-4、§4。

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

（09-15~16 狀態）D9 **關閉**（D9b 量測+D9c 補償落地；但補償增益沒有硬 GATE，見 §1-1 第 2 條）／D10 等文獻（付費牆，補摘已入庫）／D11 patch 存檔待「D11-F5 根因調查」卡（排隊中）／
D12 **關閉**（遷移落地）／D13 **關閉**（選 B 主張域收窄，`ENGINE_DOMAIN_CLAIMS.zh-TW.md`；`PlateModel.h` 檔頭與 score 描述同步仍欠）／
D14 **關閉**（串流化落地）／D15 **關閉**（選 A' 主張域收窄，設計文件 §8.5）。原始登記文字見 git 歷史。
（09-25 新登記）**D16** 給愛麗絲全曲 16 顆弱基頻 FAIL（A14 B-2 把深零點搬到別的音高×力度，見 §1-1 第 1 條）：開放，先做零點地圖，勾選項在 `TODO.md`「2026-09-25 盤點新登記」。

## 8. 檔案地圖

| 要找什麼 | 去哪 |
|---|---|
| 當前待辦 + 各輪快照 | `TODO.md` 開頭（09-15 WF0914 快照＋五項裁決） |
| 09-25 現況盤點 | `reports/status_check_2026-09-25/`（untracked，不在 7 個 commit 內，見 §1 第 1 點）：`STATUS_CHECK.zh-TW.md`（結論）、`APPENDIX_findings.zh-TW.md`（逐條證據）、`gate_logs/`（09-25 GATE 原始 log）、`commit_lists/`、`probes/` |
| 流程規約（lane、build-wf、X4、位元不變基準、稽核 stage 規則） | `docs/workcards/WF0907_README.md`、`WF0907_R_research_common.md`；WF0914 差異在 `WF0914_README.md` |
| 施工卡 | `docs/workcards/WF0907_*.md`、`WF0908_*.md`、`WF0909_*.md`、`WF0914_*.md`（13 張卡＋README） |
| 裁決包 | `reports/decision_packets/`（A13/A14/F03/K02/C10/D8；WF0914：B7/D9/D11/D13） |
| Rule 10 報告 | `reports/a14_tauc_keytrack_before_after.md`（09-10 已落地）、`reports/d8_tongue_drum_exciter_before_after.md`（09-09 已落地） |
| 稽核診斷（三病根） | `docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.zh-TW.md`（§4 全部已修或已裁決） |
| 免耳驗證設計 + 主張域 + 量測器自證 | `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §7–§10（§8.5 含 D15 放鍵段上界） |
| 引擎主張域收窄（D13 水鑼） | `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` |
| 外部資料集 | `docs/EXTERNAL_DATASET_A8.zh-TW.md`、`_ALTERNATIVES`、`_SUPPLEMENT`；資料在 `external_data/`（gitignore） |
| B7 資料 | `docs/B7_PHASE0_DATA.zh-TW.md`、`docs/workcards/B7.md`、`docs/HAMMER_VELOCITY_SOURCES.md`、`docs/RADIATION_POWER_SOURCES.md` §8 |
| WF0914 其他研究文件 | `docs/STRING_SCALE_SOURCES.md`（D11）、`docs/GONG_PARTIAL_ANALYSIS.zh-TW.md`（D13）、`docs/HAMMER_CONTACT_SOURCES.md` §9（D10） |
| UI 設計輸入 | `docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md` v1.1（09-09；D9c 後有過時處，送出前先同步） |
| GATE 證據 | `reports/gate_outputs/wf090{7,8,9}_*.txt`、`wf0914_*.txt`（含 `wf0914_integration_raw/`）、`*_INTEGRATION.txt` |
| 變現線 | `docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md`（untracked）、`exports/products/clean_batch2/`（gitignored）；CLI 存檔 `exports/renderer_archive/` |
| 歷史決策 | `DEVLOG.md` |

## 9. 操作備忘

- 建置：`cmake -B build -DCMAKE_BUILD_TYPE=Release -DTSUKI_BUILD_TESTS=ON`；CLI `build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`
- 全套 GATE（09-25 實跑順序）：三 target + 五測試 target → `ctest`（4/4）→ `python -m pytest tests -q`（264 passed＋1 skip＋5 xfail＝270）→ `python tools/physics_verify.py --full`（NO CHECKED FAILURES）與 `--selftest`（13 行 PASS）→ `python tools/verify_score.py --all`（75/75）→ HostProbe（89 PASS）→ 位元不變（8/8）
- 位元不變：`python reports/gate_outputs/wf0907_method/render_wf_scores.py --label <名稱> --workdir <repo 外的目錄>`，產出的 `sha256_<名稱>.txt` 對 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt` 比（比對時忽略 CR）。
  **`sha256_before_post_d8.txt` 只留作存檔，拿它比會讓 physical_piano 假紅燈**。注意：腳本會把 csv/sha256 寫進 `wf0907_method/`，沒有 `--outdir`。
- 分軌：`python tools/stem_verify.py <score> [--limit N] [--jobs N] [--json out]`（乾聲預設）；partial：`python tools/partial_verify.py <stem 報告.json>`
- 量測器自證：`python tools/measurement_selfcal.py [--holdout]`。現況 exit 1：開發網格總 max 5.2304 c（持續段 1.1721／放鍵段 5.2304）；`--holdout` 7.2055 c（持續段 1.0840／放鍵段 7.2055）。主張域見設計文件 §8.5。
- HostProbe：`build/Release/TsukiSynthHostProbe.exe <.vst3> <outdir>`，**cwd 必須是 repo 根目錄**（§4）；H7/D12 會在 `%APPDATA%\TsukiSynth\Presets`、`\IR` 建檔再自己刪掉。
- ffmpeg：`C:\Users\admin\Desktop\Tools\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe`

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
