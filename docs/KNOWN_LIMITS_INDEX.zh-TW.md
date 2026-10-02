# 已知限制索引（Known Limits Index）

> 建立：2026-09-25（WF0925-G1，文件 lane）。依據：盤點 `open-work:D13-claims-ext` 的**查證修正**——
> 只做「已知限制索引」，每條一行、指向原始裁決包或設計文件的段落與日期；
> **不新增主張、不改措辭**，也**不是** `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` 的新聲明（正式引擎主張只寫在那份）。
> 引號「」內是出處原文（省略原文的粗體標記與換行）；沒加引號的是本索引的短標籤，意思以出處原文為準。
> 行號是 HEAD `18430c4` 的行號（本索引引用的檔案除特別註明外，工作樹與 HEAD 相同）。**2026-09-25 WF0925b-DS 更新**：A1–A8 指向 `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` 與 `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` 的行號，已改成這兩檔在 WF0925b 同步之後的行號（EARFREE §8、ENGINE_DOMAIN_CLAIMS §1 有增補）；`ROADMAP_PHYSICS.md` 的行號 WF0925b 刻意沒有位移，仍與 HEAD 相同。
> 標「未入庫」的是 WF0925 同輪其他卡的產出，寫作時還沒 commit，內容可能再變。

用途：做產品說明或回答「TsukiSynth 驗證了什麼、沒驗證什麼」時，從這裡找到原始出處，**照原文引用**。

---

## A. 已裁決的限制（有裁決記錄）

| # | 範圍 | 限制（短標籤或原文） | 裁決（日期／誰） | 出處 |
|---|---|---|---|---|
| A1 | `water_gong` 引擎 | 「它不是乳突鑼（泰國鑼、爪哇鑼等常見的 boss+盤面構造）的模型」；2.0× 附近沒有模態是域限制 | 2026-09-15 月月（D13 選 B） | `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §1（:10-37）；`reports/decision_packets/D13_gong_2x_partial.zh-TW.md` §4（:141-147） |
| A2 | 音高量測器（工具主張） | 「量測器自身系統誤差 ≤1.18 cent，未達 ≤1 cent 門檻，為已知並接受的上限」；不可宣稱量測器 ≤1 cent | 2026-09-10 月月（C10 選 A） | `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.4 item 5（:301-310）、§9.7（:722-751）；`reports/decision_packets/C10_selfcal_domain.zh-TW.md` §7（:270-） |
| A3 | 音高量測器（工具主張） | 「任何量到 3.8–5.0 cent 之間的數字，都不得單獨用來斷言渲染正確或錯誤」；低音區可偵測的走音下限比 ±5 cent 寬 | 2026-09-10 月月（C10 選 A） | EARFREE §8.5（:321-333） |
| A4 | 音高量測器（工具主張）放鍵段 | 「放鍵/阻尼段的音高判定不得引用 ≤1.18 cent 的主張，其已知誤差上界為 ~7.2 cent」 | 2026-09-15 月月（D15 選 A'） | EARFREE §8.5（:334-350） |
| A5 | 旋律驗證的報告方式 | 音高與起音分兩個維度報，不可壓成單一 verdict | 2026-08-30 月月查核裁定 | EARFREE §8.2（:218-237） |
| A6 | 可發布措辭 | 「給愛麗絲 score、模態表、渲染決定性、逐軌疊加已驗；乾聲 883 顆有音高證據，其中 671 顆另有起音證據」；不可寫成「905 顆音高與泛音全部驗過」（2026-09-25 註：句中 883/671 的最新實測為 889/677，措辭是否更新待月月重新核定，見出處的句後註） | 月月核定（v2，2026-08-30） | EARFREE §8.4 item 4（:295-300） |
| A7 | 主張範圍外 | 「仍不在主張範圍內：泛音的頻率與振幅、以及一切美學/聽感主張」 | v2 主張域（2026-08-30） | EARFREE §8.5（:320） |
| A8 | 旋律驗證弱域 | f0 < 167 Hz 的起音精測、基頻被壓得很弱的音（08-30 是 22 顆高音；A14 之後是 D16 的 16 顆）、任何帶殘響訊號的音高判定 | v2 主張域（2026-08-30） | EARFREE §8.5（:313-319）、§8.3 |
| A9 | partial（泛音）驗證 | 只立 partial 頻率內部一致性（沿用 ±5 cents），不立振幅 GATE；`B` 對照寫成不當 GATE 的報告；工具先以 informational 實作 | 2026-09-08 規劃者代決 B+（月月 09-07 委託，可推翻） | `reports/decision_packets/A13_partial_gate_domain.zh-TW.md`「裁決記錄」（:536-548） |
| A10 | F3 velocity 判定 | 主張域二分：固定 tau_c 路徑判定不動；Felt 路徑改「實測 vs 模型自身預測」自洽判定，容差數值未動 | 2026-08-27 月月（B4 選 (b)） | `ROADMAP_PHYSICS.md` §6 velocity 列（:468）；`TODO.md` B 區 B4 條目；`reports/decision_packets/B4_f3_velocity_ruling.md` |
| A11 | 槌氈接觸求解器適用範圍 | 「只適用 Cimbalom/Piano；Chromatic 在 D2 補搜完成前不得套用」 | 2026-08-27（B4 完工） | `TODO.md` B 區 B4 條目；（**2026-10-02 已升格** → `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §7，月月裁決 Q19 C7 甲） |
| A12 | Cimbalom/Piano 振幅的 `spectralTilt` | 「劃界為已文件化 creative 層（不算入物理主張）」 | 2026-07-23 月月 | `TODO.md`「2026-07-23 round-4 裁決落地」段；`ROADMAP_PHYSICS.md` §0 表 Cimbalom/Piano 列（:140）；（**2026-10-02 已升格** → `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §4，月月裁決 Q19 C3 甲） |
| A13 | 響度校準層 `loudnessCompensationGain` | 「已文件化校準層、比照 spectralTilt 劃界」（amount=0.78 月月審聽定案） | 2026-08-06 月月 | `TODO.md`「2026-08-06（夜）跨音域響度失衡修正」段；`reports/loudness_keytrack_before_after.md`；（**2026-10-02 已升格** → `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §4，月月裁決 Q19 C3 甲） |
| A14 | 亮度 EQ（`global.effects.eq`） | 機制保留（藝術用、域外），文件建議改為預設不開 | 2026-08-27 月月（A4） | `TODO.md` A 區 A4 條目；`reports/decision_packets/A4_brightness_eq.md` |
| A15 | FM Piano 引擎 | 「❌ 域外」「已誠實標註「非物理合成」，維持此標註」 | ROADMAP §0 驗證域表（該列 git 最早見於 2026-07-09 `7c150d1`；沒找到單獨的裁決包） | `ROADMAP_PHYSICS.md` §0（:144）；`TODO.md`「Deliberately outside the physical claim」段；（**2026-10-02 已升格** → `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §2，月月裁決 Q19 C1 甲） |
| A16 | Custom Harmonics | 「⚠️ 半域內」「加法合成，頻率比可驗但非物理推導」 | 同上（2026-07-09 `7c150d1`） | `ROADMAP_PHYSICS.md` §0（:143）；（**2026-10-02 已升格** → `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §3，月月裁決 Q19 C2 甲） |
| A17 | 效果鏈（Reverb/Delay/Comp/Dist） | 「驗證一律 FX 全關；用了效果的 score 不在物理主張範圍」 | 同上（2026-07-09 `7c150d1`） | `ROADMAP_PHYSICS.md` §0（:145） |
| A18 | `frequency_mode: midi` | 「混合系統：物理決定頻譜形狀、平均律決定基頻，不得宣稱絕對尺寸音高」 | 該列 git 最早 2026-07-23 `e0eb06a` | `ROADMAP_PHYSICS.md` §0（:147）；（**2026-10-02 已升格** → `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §5，月月裁決 Q19 C4 甲） |
| A19 | `frequency_mode: geometry` | 「仍需真實試體量測才能升級為 specimen-level 主張」 | 同上（2026-07-23 `e0eb06a`） | `ROADMAP_PHYSICS.md` §0（:148） |
| A20 | 明確不做 | 連續激發樂器（運弓、管樂）、FEM／流體聲學、Sample Layer 等 | ROADMAP §5（該節 git 最早 2026-07-09 `7c150d1`） | `ROADMAP_PHYSICS.md` §5（:450-456） |
| A21 | 外掛 IR 模式響度補償 `kIrWetMakeupGain` ×26.9 | 「標為 DECIDED CONVENTION，非物理常數」；只影響 plugin IR 模式 wet 路徑；對齊參考是 ALGO 預設 room size 0.5、未指定 T60 | 2026-09-16 月月（D9 選 A）；對齊參考限制 2026-09-25 盤點補記 | `reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md`「裁決記錄」（:150-157）；`ROADMAP_PHYSICS.md` D9→D9c 列（:27）；同裁決包 2026-09-25 附記（工作樹，未入庫） |
| A22 | 絕對聲壓輸出 `absolute_pressure_per_force` | 「這是月月裁決的慣例錨定，不是實測也不是推導」（只進 `--dump-modes` 診斷輸出） | 2026-08-28 月月（B6「照建議走」＝方案 B） | `reports/decision_packets/B6_calibration_choice.md`「裁決記錄」（:142-）；`TODO.md`「Verification gaps that must stay explicit」第 3 條；（**2026-10-02 已升格** → `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §8，月月裁決 Q19 C8 甲） |
| A23 | 第一原理力鏈（B7） | Phase 0 完成、Phase 1 部分完成（`dumpModes()` 欄位撤回）、Phase 2/3 BLOCKED | 2026-09-15 月月（§5 路徑 C＋(a) 乙案） | `reports/decision_packets/B7_phase2_and_open_items.zh-TW.md` §6（:164-） |
| A24 | 弦長／弦徑模型 | 候選修正（真實鋼琴逐八度查表）patch 存檔不落地，現行模型不變；F5 根因已於 09-25 查清，A/B ~~待重開~~（2026-10-02 月月裁 Q16＝D：不重開） | 2026-09-15 月月（D11 選 C） | `reports/decision_packets/D11_string_scale_candidate.zh-TW.md`「裁決記錄」（:59-65）；F5 根因補記與 `reports/d11_f5_root_cause_2026-09-25.zh-TW.md`（未入庫）；（~~C5 **未升格**：2026-10-02 裁定表 Q19「C5 等 Q16 研究卡」，見 `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §11~~ → C5 **2026-10-02 已升格**（月月裁決 N4＝甲）→ `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §12） |
| A25 | 音板參數 | h = 9 mm／`wood_spruce` 確認維持現值 | 2026-08-27 月月（A11 選 (i)） | `TODO.md` A 區 A11 條目；`reports/decision_packets/A11_soundboard_sensitivity.md` |
| A26 | 外部校準資料 | 無可商用的校準資料集，外部資料只作私下對照參考（TU Berlin 為 CC BY-NC-SA） | 2026-09-09 月月（A8） | `TODO.md` A 區 A8 條目、「Verification gaps that must stay explicit」第 7 條；`docs/EXTERNAL_DATASET_A8.zh-TW.md` |

## B. 已知缺口（開放中：還沒裁決、或等資料／等外部）

| # | 範圍 | 缺口（短標籤） | 登記日期 | 出處 |
|---|---|---|---|---|
| B1 | Beam/Plate 阻尼 | `beam_plate_beta_air`／`beam_plate_gamma_radiation` 未溯源（D1）；BeamModel 的 `*2` 在寬頻化後成為「全音域一律 2 倍過阻尼、不再有任何錨點理由的純經驗係數」，去留待裁（前置 D1） | 缺口原始登記早於 08-15；`*2` 09-25 正式登記 | `TODO.md`「Verification gaps that must stay explicit」第 1 條、09-25 等月月裁決（:138）；`src/physics/BeamModel.h:44-48`；D1 補搜 `docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md`（2026-09-25，未入庫）；（`*2` 部分：**2026-10-02 月月裁決 Q17=A** 保留並改標「DECIDED CONVENTION，經驗係數，無文獻錨點」，已升格 → `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §6〔Q19 C6 甲〕；`beam_plate_beta_air`／`beam_plate_gamma_radiation` 未溯源仍開放） |
| B2 | Chromatic 槌具 | 舌鼓／鑼的槌具接觸參數未標定（D2） | D2 補搜 2026-08-28 起（草稿） | `TODO.md` D 區 D2 條目；`docs/D2_CHROMATIC_CONTACT_SEARCH.zh-TW.md`；`docs/HAMMER_CONTACT_SOURCES.md` §6（:176-198）；（「Chromatic 槌具未標定」**2026-10-02 已升格** → `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §7〔Q19 C7 甲〕；D2 缺口本身仍開放） |
| B3 | Piano 力脈衝深零點 | A14 B-1（力譜滾降形狀）等付費牆文獻（D10）；D16 給愛麗絲 16 顆弱基頻 | A14 2026-09-08；D16 2026-09-25 | `reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md`「裁決記錄」（:931-942）；`TODO.md`「★ 仍開著」的 D16 條目；`reports/weak_fundamental_null_map_2026-09-25.zh-TW.md` §0／§6（未入庫） |
| B4 | 外掛 vs CLI 的 voice 行為 | 外掛每引擎 16 顆 voice（會搶音、同音重疊提前制音、FM 同音反覆時舊 voice 不結束），CLI 每事件一顆 | 疑慮 2026-08-30；量測 2026-09-25 | `reports/decision_packets/POLYPHONIC_VERIFICATION_OPTIONS.zh-TW.md` §6（:130-136）；`reports/voice_pool_occupancy_2026-09-25.zh-TW.md` §0／§6（未入庫）；（**2026-10-02 月月裁決 Q09=D（含 B）＋Q09c=B**：已寫進 `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §10〔Q19 C9 甲〕；FM 舊 voice 不結束 Q09b=A 要修，patch 先在隔離副本做 R10 前後對照、~~未落地~~ **→ 追加裁決 N2＝A 已於 WF1002b 落地（commit `59c0b06`）**；外掛串流實測由 WF1002-C1 做） |
| B5 | 外掛路徑的物理驗證 | 物理 GATE 驗的是 CLI 路徑；plugin↔CLI 一致性未驗 | ROADMAP §4 早期；09-25 列入裁決 | `ROADMAP_PHYSICS.md` §4 第 1 條（:441）；`TODO.md`「✓ 已結：WF0925 裁決包 38 題」Q08 列（原「09-25 等月月裁決」一節已於 10-03 改寫，原文見 `git show 168688e:TODO.md`）；（**2026-10-02 月月裁決 Q08=C**：先做 B 收窄，已寫進 `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §9；parity GATE 排後續 L 卡，仍開放） |
| B6 | 鋼琴耦合物理 | 有限音板共振、共鳴、制音器／踏板都還沒做（B1 只補了無限板導納損耗） | — | `TODO.md`「Verification gaps that must stay explicit」第 4 條；`reports/damping_broadband_findings.md` §4.1（:108-） |
| B7 | 木材異向 | 異向 schema 已入庫但沒有程式讀它 | 2026-08-28 | `TODO.md`「Verification gaps that must stay explicit」第 6 條 |
| B8 | 外部量測驗證 | 實體試體量測（D7）沒做；可信外部錨仍須試體量測 | — | `TODO.md`「Verification gaps that must stay explicit」第 7 條、D 區 D7（:750）；`docs/SPECIMEN_VALIDATION_PROTOCOL.zh-TW.md` |
| B9 | 輻射預測 | 拾音位置、相位、指向性仍 `UNVERIFIED` | — | `TODO.md`「Verification gaps that must stay explicit」第 3 條 |
| B10 | 短瞬態 | `cimbalom/rubber`、`tongue_drum/rubber`、`water_gong/rubber` 在 `--full` 報 `UNVERIFIED/N/A` | — | `TODO.md`「Honest N/A cases」段 |
| B11 | 調音器 | 複音／缺基頻模式沒做（只有在能可靠拒答時才做） | — | `TODO.md`「Verification gaps that must stay explicit」最後一條 |
| B12 | 材料常數出處 | 密度、楊氏模量、泊松比標為文獻值，但原文寫明「no one paged through this codebase's history to confirm the exact reference used when they were entered」 | — | `docs/MATERIALS_SOURCES.md:37-44` |
| B13 | partial_verify 升 GATE | A13 原規劃的前提被 D15（放鍵段 ~7.2 c）改變，要月月重新確認 | 2026-09-25 | `TODO.md`「✓ 已結：WF0925 裁決包 38 題」Q18 列（原「09-25 等月月裁決」一節已於 10-03 改寫，原文見 `git show 168688e:TODO.md`） |
| B14 | 外掛 IR 模式 | D9c 常數原本沒有 GATE 鎖住（09-25 WF0925-K2 已加精確相等 CHECK 釘住 26.9；但 IR 與 ALGO 的響度差仍沒有判定，常數裡約 18.06 dB 綁在 JUCE 的 0.125 正規化上，見 `reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md` 檔尾與裁決包 Q01）；IR 模式沒有輸出限幅 | 2026-09-25 | `TODO.md`「✓ 已結：WF0925 裁決包 38 題」Q01、Q05 列（原「09-25 等月月裁決」一節已於 10-03 改寫，原文見 `git show 168688e:TODO.md`）；（**2026-10-02 月月裁決 Q01=B**：已加 IR−ALGO ≤0.25 dB 硬 CHECK；**Q05=C**：不加限幅、加 CLIP 削波指示燈；N1＝B1 拿掉壓縮器固定補償） |
| B15 | B7 殘留函式 | `hammerVelocityMps()` 在 MIDI 20 不連續（目前沒有呼叫點，不影響渲染） | 2026-09-25 | `TODO.md`「✓ 已結：WF0925 裁決包 38 題」Q11 列（原「09-25 等月月裁決」一節已於 10-03 改寫，原文見 `git show 168688e:TODO.md`） |

---

## C. ~~待月月逐條裁決~~ 已裁（2026-10-02）：要不要升格成 `ENGINE_DOMAIN_CLAIMS` 的正式引擎主張

`ENGINE_DOMAIN_CLAIMS.zh-TW.md` 檔頭規定：只記「每個引擎物理模型模擬的是什麼、不是什麼」，每條要「附裁決記錄與分析文件出處」。
盤點查證修正指出：量測器的 ≤1.18 c／~7.2 c（上表 A2–A4）是**工具主張**、已在 EARFREE §8.5，放進引擎清單會分類錯，所以**不列為升格候選**。
下面每一條都是「甲：照出處原句升格進 `ENGINE_DOMAIN_CLAIMS`」或「乙：不升格，只留在本索引與原出處」；本索引**不替月月選**。

**2026-10-02 月月裁決 Q19＝C（逐條）**：C1～C4、C7、C8 甲；C6 甲（Q17=A）；C9 甲（Q09 含 B）；C5 等 Q16 研究卡（裁定表 `docs/workcards/WF1002_README.md` §1）。升格後的正式主張在 `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §2～§10，下表最後一欄「裁決結果」指到節號。

| # | 候選 | 對應上表 | 升格時的原句來源 | 備註（事實，非建議） | 裁決結果（2026-10-02） |
|---|---|---|---|---|---|
| C1 | FM Piano 域外（非物理合成） | A15 | `ROADMAP_PHYSICS.md` §0（:144） | 盤點查證修正點名的例子之一 | 甲：已升格 → §2 |
| C2 | Custom Harmonics 半域內 | A16 | `ROADMAP_PHYSICS.md` §0（:143） | — | 甲：已升格 → §3 |
| C3 | Cimbalom/Piano 振幅含 creative 層與校準層 | A12、A13 | `TODO.md`「2026-07-23 round-4 裁決落地」段、「2026-08-06（夜）跨音域響度失衡修正」段；`ROADMAP_PHYSICS.md` §0（:140） | 頻率／衰減不受這兩層影響（ROADMAP §0 :140 原文） | 甲：已升格 → §4 |
| C4 | `frequency_mode: midi` 是混合系統 | A18 | `ROADMAP_PHYSICS.md` §0（:147） | — | 甲：已升格 → §5 |
| C5 | 弦長／弦徑模型假設（每八度減半＋corpus 固定弦徑） | A24 | `reports/decision_packets/D11_string_scale_candidate.zh-TW.md` §0 | 盤點查證修正點名的例子之一；D11 選 C 後現行模型不變，A/B 等 F5 根因回來重開 | ~~**未升格**：等 Q16 研究卡 → §11 註明~~ **甲：已升格（2026-10-02 月月裁決 N4＝甲，追加裁決包 `reports/decision_packets/WF1002_addendum_decisions.zh-TW.md`）→ §12**（措辭照 R-b 報告 §6 草稿） |
| C6 | 舌鼓 BeamModel `*2` 經驗阻尼 | B1 | `src/physics/BeamModel.h:44-48` 註解 | 屬未決缺口，不是裁決；要先裁 B1（前置 D1） | 甲（Q17=A）：已升格 → §6 |
| C7 | Chromatic（舌鼓／水鑼）槌具未標定 | A11、B2 | `TODO.md` B 區 B4 條目 | — | 甲：已升格 → §7 |
| C8 | 絕對聲壓輸出是慣例錨定 | A22 | `TODO.md`「Verification gaps that must stay explicit」第 3 條 | 只在 `--dump-modes` 診斷輸出 | 甲：已升格 → §8 |
| C9 | 外掛 16 voice 與 CLI 的差異 | B4 | `reports/voice_pool_occupancy_2026-09-25.zh-TW.md` §6（未入庫） | V1 報告 §6 的選項之一就是「寫進主張域」，要等那份裁決 | 甲（Q09 含 B）：已升格 → §10（Q08 收窄句在 §9） |

---

## 2026-10-03 狀態補記（文件卡 DOC-B；只補狀態，不改上面各列的出處原文與標籤）

- **TODO.md 引用改成條目名稱**：`TODO.md` 在 2026-10-03 改寫（1026 → 924 行），上面原本引用的 `TODO.md` 行號全部位移，已改成引章節名或條目名；原「09-25 等月月裁決」一節已改寫成「✓ 已結：WF0925 裁決包 38 題」表，舊文用 `git show 168688e:TODO.md` 查。表頭說的「行號是 HEAD `18430c4`」只對其他檔的行號仍成立。
- **「未入庫」字樣已過時**：標「未入庫」的 WF0925 產出都已在 2026-09-30 commit＋push（`eba91ba`～`b41298c`）。
- **B4**：FM 同音反覆時舊 voice 不結束——追加裁決 N2＝A 已在 WF1002b 落地（`src/dsp/Envelope.h`，commit `59c0b06`；月光全曲 FM 同時活著的 voice 196→14、被搶 798→0，`reports/wf1002_fm_envelope_fix_before_after.zh-TW.md`）。搶音與同音提前制音照舊（Q09c=B）。
- **B14**：Q01=B 已加 IR−ALGO ≤0.25 dB 硬 CHECK（現值 0.112 dB，`ROADMAP_PHYSICS.md` §6 已登記）；輸出端仍沒有限幅（Q05=C），改加 CLIP 削波指示燈；N1＝B1 拿掉壓縮器固定補償後，27 個工廠 preset 單音沒有一個超過 0 dBFS（最大 −1.85 dBFS）。
- **A24／C5**：Q16＝D（D11 不重開）；「F5 PASS 依賴探針 0.8 mm」已由 N3＝A 換窗量法解除（`reports/gate_outputs/wf1002b_T_f5_method.txt`）；C5 已升格（`docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md` §12）。
- **B3**：Q15＝A（給愛麗絲母帶不動）；D16 物理缺口本身仍開放。**B5**：parity GATE 仍是後續 L 卡。**B13**：Q18＝A、Q18b＝B（只記錄，不升 GATE）。**B15**：Q11＝C（不動）。
- **新登記的開放缺口（事實，出處 `docs/workcards/WF1002_README.md` §4）**：外掛 Body 層結構問題（preset 11 把 Body 調回預設 0.5 時約 +3.8 dBFS，另開卡）；FM 修法的合成測例「同音按著重打」修後大 1.5 dB，原因未證實；N1 副作用——使用者自己存過、開了壓縮器的舊專案與 preset 重開會變小聲（旋鈕極端值時最多 19 dB）。
