# TsukiSynth — Current TODO

> Last updated: 2026-08-22
> Branch: `fix/deep-physics-audit-20260716`

The deep-audit implementation fixes are on the branch. Historical Phase D–I decisions remain in `DEVLOG.md`; this file lists only current work and scientific gaps.

**2026-08-22 快照**：紅燈清零（X1/X2/X3 done，X 段只剩 X4 文件規約）；M10 收官（A1' 接受）；
A9 關閉（L3b 真 Cubase 實測）；C3 容差登記完成（跨平台檢查轉阻斷式）；A12 修畢。
下一步 = X4 或 B3（見 HANDOVER §5）。

---

# 待辦總表（2026-08-15 整理，2026-08-22 更新）

> 文獻依據與依賴關係見 [`docs/RESEARCH_INDEX.md`](docs/RESEARCH_INDEX.md)。
> 新 session 請先讀 [`HANDOVER.md`](HANDOVER.md)。
> 下面各項的細節在本檔後半段的原始條目裡，這裡只列「要做什麼」。

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
- [ ] **X4 施工卡與流程補上「跑 ctest 前必先重建三個測試 target」** — 本輪 B1 的 `b1_ctest_all.txt`「3/3 passed」
      是**測到未重建的舊 binary**，對抗驗證的 GATE 視角「獨立重跑」也踩同一個坑。
      規約：`cmake --build build --config Release --target TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest` 之後才跑 `ctest`。
      要加進 `docs/workcards/` 六張卡的 GATE 段與未來所有卡。

## A. 等月月決定（AI 不能自己動）

- [ ] **A1 Rule 10 前後對照裁決** — 讀 `reports/deep_fix_before_after.md` §00 白話導讀後，決定「整批接受」或「指名回退某一項」。這是 7/22 那六項物理修正的最終放行。
- [x] **A1' B1+B2 Rule 10 裁決** — **2026-08-22 月月裁決「接受」**，B2 批次已 commit+push
      （`4ef2c50`/`bef60fc`）。報告 `reports/b1_b2_bridge_damping_before_after.md`。
- [x] **A2 阻尼寬頻化那批 unstaged 怎麼處理** — **已依 (b) 方案收斂完成**（事實路徑：該批與 B1 一起進了 447faea，B2 於 2026-08-21 完成收尾驗證，見 B2 條目）。
- [x] **A3 琴橋導納要不要開工**（= B1）— 已開工並完成（見 B1/B2 條目）。
- [ ] **A4 亮度 EQ 應急層去留** — 8/6 激發端修正落地後，`global.effects.eq` 高頻 shelf 的補償需求可能已部分消失，需審聽後決定是否調整建議值／文件。
- [x] **A5 push 到 GitHub** — 2026-08-21 月月授權 push（49c22f5/b5ccb9b/26a0129），CI 全綠，X3 數字已得。
- [ ] **A6 merge → `main` 時機** — M8-8b，分支 `fix/deep-physics-audit-20260716` 至今未併。
- [ ] **A7 repo License 定案** — 已決定「保留商業」。要寫 `LICENSE` + 更新 `README.md:349` 的 `TBD`。JUCE 8 走 Starter 層（免費、營收 $20,000 以下、允許閉源商業散布），發行前要讀一次 JUCE 8 EULA 的署名條款。VST3 SDK 在 JUCE 8 內是 MIT，無虞。
- [ ] **A8 外部資料集要不要下載** — CC BY-SA 4.0 與「保留商業」的相容性。**推薦：只當外部參照，repo 內只留 DOI + SHA256 + 比對數字，資料檔不進版控。**
- [x] **A9 Cubase 四步驗證** — **已由自動化取代人工並於真 Cubase 實測完成**（月月 2026-08-20 委託重定義 + 2026-08-22 L3b 實測）：
      掃描（L3a 快取 XML + GUI 建軌）／MIDI 實彈（Cubase 匯出經 melody_verify 5/5）／
      專案存讀（重開再匯出音訊位元全等）皆真 host 證據；automation 於 L2 HostProbe 合約層驗證
      （Cubase GUI 畫 lane 未做，唯一殘留人工項，非位置主張必需）。證據 `l3b_cubase_live.txt`。
- [ ] **A10 Score 控制台實操驗收** — Standalone 頂列 [Score] 鈕的實際操作。
- [ ] **A11 共鳴板厚度 h 與材質選定（B1 琴橋導納）** —— 目前實作用
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
- [ ] **B3 弦阻尼律換第一原理**（前置：建議排在 B2 之後，避免歸因混淆）
      Cuesta & Valette 三機制，零自由參數。**注意這是改阻尼律的形狀（`f²` → `f^0.5`+常數），不是換數字。**
      需依 Rule 9 標註「同一份 materials.json 對不同引擎語意不同」。
      → 依據 `docs/STRING_DAMPING_SOURCES.md`
- [ ] **B4 槌頭非線性接觸求解器**（前置：無，但風險最集中）
      `F = K·δ^α` 逐音實測值 + 槌質量表 + Stulov 遲滯參數。
      **只適用 Cimbalom/Piano**；Chromatic 在 D2 補搜完成前不得套用。
      **必須連同 noteOn 能量正規化層一起設計**，否則會撞 §6 velocity 判定。
      → 依據 `docs/HAMMER_CONTACT_SOURCES.md`
- [ ] **B5 木材正交異向**（前置：B1，等音板需要 `D` 時一併進場）
      24 樹種彈性比 + 25 樹種泊松比 + 含水率公式已備。
      Kirchhoff 板改異向版是**模型結構改動**，不是換數字。
      → 依據 `docs/WOOD_ANISOTROPY_SOURCES.md`
- [ ] **B6 force → 輻射壓力／SPL 模型**（前置：B1 + B5）
      量測面定義可沿用文獻慣例（1.05 m 球面、數位振幅 1.0 ≡ 1 Pa ≡ 94 dB）。
      實作後 `specimen_verify.py` 的 SPL/指向性才可能脫離 `UNVERIFIED`。
      → 依據 `docs/EXTERNAL_ANCHOR_SOURCES.md` §2–§3

## C. 不需要任何資料、純工程（可隨時插隊）

- [ ] **C1 rubber 短瞬態 T60 估計器** — 現行「不足八週期即 N/A」太粗，改用 EDT／Schroeder 反向積分 + 明確拒答條件，把三個 `UNVERIFIED/N/A` 轉成可判定。**需月月裁決可信門檻（幾個週期算數）**。
- [ ] **C2 多音／缺基頻調音器模式** — 只在能可靠拒答模稜兩可的情況下才做。工作量最大、對物理驗證主張價值最小。
- [ ] **C3-b 免耳三層驗證（旋律位置 GATE）** — 設計提案 `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md`（2026-08-20，未實作）：
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
      H5 兩項誠實 FAIL = A12。
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
      ✅ corpus 81 檔 melody_verify 掃描完成（informational，`reports/gate_outputs/melody_corpus_sweep_informational.txt`）：
      30 檔全綠（強域實證）+ 48 檔含 FAIL（§7 弱域：密集複音/混響/delay，位置保證由 2e 位元決定性承擔）
      + 3 檔 layered 整檔拒答（上游 CLI 無 layer 展開的 --dump-modes；工具已補優雅拒答 exit 3）。
      事件層級 473 PASS / 854 FAIL / 38633 UNVERIFIED（拒答率 96.7% = 域界定的 corpus 級實測）。
- [x] **C3 跨平台容差登記** — **2026-08-22 完成**（月月裁決「照提案登記」，詳見 X3 條目）。

## D. 還要補搜的資料（阻擋上面某些項）

- [ ] **D1 梁／板的空氣與輻射阻尼** — **未搜尋，狀態未知**。弦的公式內建圓截面幾何不適用。**這一項擋住 B3 對 Chromatic 引擎的適用性。**
- [ ] **D2 舌鼓／鑼的槌具接觸參數** — **未搜尋，狀態未知**。**擋住 B4 對 Chromatic 引擎的適用性。**
- [ ] **D3 `gamma_radiation` 的真實物理來源** — 弦的文獻明指細弦輻射可忽略，故現行那一項對弦而言的物理標籤可能就是錯的。
- [ ] **D4 舌鼓 ICSV27 2021 全文** — 機構庫 403，可試作者自存版／ResearchGate。
- [ ] **D5 銅鑼 JCIE 2005 全文** — 付費牆。
- [ ] **D6 Wood Handbook Table 5–15（溫度係數）** — 簡單，同一份 PDF 的後續頁面。
- [ ] **D7 揚琴／舌鼓／鑼的實體試體量測** — **文獻買不到，只能自己量**（`docs/SPECIMEN_VALIDATION_PROTOCOL.zh-TW.md`）。這是唯一能讓域內引擎升級到 specimen-level 主張的路。

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

## 2026-08-06（夜）跨音域響度失衡修正（unstaged 待審）

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
- [ ] **亮度 EQ 應急層去留覆核**——激發端修正落地後，既有 `global.effects.eq`
  高頻 shelf 的補償需求可能已部分消失，月月審聽後決定是否調整建議值/文件。

## 月月待裁決（pending decisions）

- [x] **`verify_score.py` 的 `MODE_F0_TOL_CENTS = 12.0` 是否授權改量測法後收緊**——**2026-07-23 裁決：授權**，改為 course 質心／平均量測法後收緊至 5.0；程式改動（`check_modes()`）由另一輪工作平行進行中，尚待該輪 GATE 存證（見「2026-07-23 round-4 裁決落地」）。
- [x] **殘差頻譜能量檢查：門檻轉判定制的批准**——**2026-07-23 裁決：批准**，轉判定制、門檻取 -60.0 dB re total（依據 round-2/round-3 累計實測基線 -74.7~-83.1 dB re total，留有 ≥14.7 dB 邊際）；程式改動（`tools/physics_verify.py`）由另一輪工作平行進行中，尚待該輪 GATE 存證。
- [x] **spectralTilt heuristic 層去留**——**2026-07-23 裁決：降級保留**，聲音不動，劃界為已文件化 creative 層（不算入物理主張），已同步 `ROADMAP_PHYSICS.md` §0 與 `README.md` 域表註記。
- [x] **【2026-07-18 round-2 → 2026-07-22 round-3 已修正】piano velocity 物理律「違規」**——量測域變更（寬帶→基頻窄帶）**2026-07-23 裁決：追認**，已同步 `ROADMAP_PHYSICS.md` §6 velocity 列依據欄。詳見 `DEVLOG.md` 2026-07-22 條目、`reports/gate_outputs/deepfix3_selftest.txt`／`deepfix3_gate_full.txt`。
- [x] **【2026-07-18 round-2 → 2026-07-22 round-3 已修】corpus 逐聲道 RMS 揭露的 2 個既有 rest 超標**——`summer_m2`（decay 2.8→2.6）／`summer_m3`（decay 1.2→1.0，累計 2.1→1.0）的殘響藝術效果**2026-07-23 裁決：接受**。機器 GATE 已於 round-3 過（`verify_score.py` 全項 PASS 含 determinism SHA256 match）。
- [ ] **Rule 10 前後對照報告審閱**——`reports/deep_fix_before_after.md`（2026-07-18 round-2）：8 首代表曲目改動前後 RMS/頻譜質心/T60/f0 比對，`physical_piano` 是唯一變大聲的一首（+2.346 dB），值得月月過目確認方向是否符合預期。**2026-08-15 月月回饋「看了但看不懂」→ 已補 §00 白話導讀**（一句話結論、逐首白話對照表、主因＝τ→T60 重新定義使音尾變 1/6.9、舌鼓泛音整組換掉的說明、哪些數字不可信、決策選項）。待月月讀完白話版後裁決「整批接受」或「指名回退某項」。

## 2026-07-23 round-4 裁決落地

> 月月於對話中對 2026-07-22 round-3 留下的五項待裁決明示「都照推薦的做」。本輪只落地文件記錄，不改 `src/`／`tools/` 程式碼。

- 決議：(1) velocity 量測域（寬帶→基頻窄帶）追認；(2) `summer_m2`/`summer_m3` decay 收斂（2.8→2.6、2.1 累計→1.0）接受；(3) `spectralTilt` 降級保留，劃界為已文件化 creative 層；(4) 殘差頻譜能量轉判定制 -60.0 dB re total；(5) `MODE_F0_TOL_CENTS` 授權改 course 質心量測法後收緊至 5.0。
- 文件同步：`ROADMAP_PHYSICS.md` §0 域表（Cimbalom/Piano 列 spectralTilt 劃界註記）+ §6 容差表（velocity/殘差/f0 三列）；`README.md` Physical Verification 域表同步 spectralTilt 劃界註記；本檔（`TODO.md`）五項裁決逐條關閉；`DEVLOG.md` 新增本輪條目。
- **(4)（殘差判定制 -60.0 dB）與 (5)（f0 course 質心 5.0）的程式碼改動已於同日稍後落地並全 GATE 綠**（文件線寫作當下平行進行中，故上一版此條標「尚未落地」）：`tools/physics_verify.py` `RESIDUAL_ENERGY_LIMIT_DB = -60.0` 判定制生效（5 引擎實測 -74.7~-83.1 dB 全 PASS，selftest 新增未建模強峰反例會 FAIL）；`tools/verify_score.py` `course_f0()` 振幅加權質心 + `MODE_F0_TOL_CENTS = 5.0`（moonlight yangqin 實測 5.013→0.019 cents，證實舊讀數為 string-0 設計偏移非真走音）。GATE 存證：`reports/gate_outputs/deepfix4_selftest.txt`／`deepfix4_gate_full.txt`（`F5 residual energy : PASS`、`RESULT: NO CHECKED FAILURES`）／`deepfix4_pytests.txt`（32+26 測試全過）。
- **corpus 全量重驗（新 f0 質心 + 5c 收緊下）：73/73**——四分片 `deepfix4_corpus_{A,B,C,D}*.txt`：B 12/12、C 21/21、D 22/22 全過；A 分片 18 檔中 `moonlight_sonata_complete` 首跑 determinism 檢查因 CLI 第二次渲染進程啟動失敗（exit 0xC0000142 = STATUS_DLL_INIT_FAILED，高併發環境故障，同 deepfix2 輪 autumn_m1 前例）記 FAIL；**2026-07-23 已單獨重驗：ALL CHECKS PASSED（含既登記 moonlight 豁免）、determinism SHA256 aaaa46e8... 兩次一致，非真回歸，已解除**。其餘 17 檔含 ai_radiance 5 檔全過。豁免仍僅 moonlight 一筆，零新增。
- Rule 1/2/4：本輪未執行任何 git 變更狀態指令，未調寬任何容差（(4)(5) 皆為收緊方向），文件中的新數字（-60.0 dB、5.0 cents）均註明批准依據與日期。

## Before merging this branch

- [x] Review the complete P1–P7 diff; keep it as one atomic physics-hardening commit because production changes, fail-closed contracts, CI gates and their evidence documentation must land together.
- [x] Push the branch and let the updated Windows CI run Python unit tests, CTest, build targets, the event-specific consonance gate and `physics_verify.py --full` — 2026-08-05 push（`aba7f84` specimen 批 + `4cf4817` scene→reverb 批），CI run 31004676104 全步驟綠。
- [ ] Validate VST3 scan, MIDI, automation and state round-trip in the intended DAW.
- [ ] Perform a visual accessibility review of the tuner and generated HTML report with the intended deaf user; automated tests cannot certify readability.

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
      **弦：已找到零自由參數的第一原理式**（Cuesta & Valette）→ `docs/STRING_DAMPING_SOURCES.md`。
      同時發現現行 `beta_air·f²` 的頻率次方與物理推導對不上（推導是 `f^0.5`+常數 / `f³` / `f¹`）。
      **梁／板未搜尋、`gamma_radiation` 真實來源未溯源。** 工作項 B3 / D1 / D3。
- [ ] Replace single-frequency damping anchors with broadband/specimen measurements and uncertainty intervals. **2026-08-06 月月裁決升級**：Rule 10 審聽確認材質物理化後全體音色「低音變大聲、高音變超小聲」（`phase_h_before_after.md` §3 已記錄的機制——單頻 η 錨高估高頻衰減是主因之一），本項定為該問題的**長期物理修法**；短期先以 `global.effects.eq` 亮度補償 creative 層應急（同日已落地，見下）。
      **2026-08-10 實作完成但卡住**（程式仍 unstaged）：寬頻化揭露模型缺頻率無關的損耗通道，C2 的 T60 由 39 s 變 129 s、corpus 掉到 72/73 → `reports/damping_broadband_findings.md`。
      該缺口的閉式解已找到（琴橋導納），**本項的前置是 B1**。工作項 A2 / B2。
- [ ] Add the synth-side calibrated force → displacement → radiated pressure/SPL model, including pickup/microphone position, signed/complex modal residue and spatial radiation. The v2 measurement pipeline/comparators are complete; this remaining item is specifically the physical prediction model.
      **輻射理論骨架與絕對校準慣例已備**（1.05 m 球面、1.0 ≡ 1 Pa ≡ 94 dB）→ `docs/EXTERNAL_ANCHOR_SOURCES.md` §1–§3。
      合成端預測模型仍未實作；相位維持 `UNVERIFIED`。工作項 B6。
- [ ] Add coupled-body/soundboard/sympathetic-resonance and realistic damper/pedal physics for piano.
      **閉式公式鏈完整、只需新增音板厚度一個參數** → `docs/BRIDGE_ADMITTANCE_SOURCES.md`。
      是阻尼寬頻化／輻射／木材異向三項的前置。工作項 **B1（建議最先做）**。
- [ ] Replace the velocity proxy with a parameterized nonlinear contact solver using hammer mass, compliance and geometry.
      **鋼琴逐音 `K`/`α` + 槌質量 + Stulov 遲滯參數已備** → `docs/HAMMER_CONTACT_SOURCES.md`。
      現行 `v^-0.2` 對應 `α=1.5`（純赫茲），實測鋼琴氈是 `α=2.3~3.0`。
      **僅適用 Cimbalom/Piano；會撞 §6 velocity 判定。** 工作項 B4 / D2。
- [ ] Model anisotropic/orthotropic wood, temperature and humidity where those claims are needed.
      **24 樹種彈性比 + 25 樹種泊松比 + 含水率公式已備** → `docs/WOOD_ANISOTROPY_SOURCES.md`。
      **建議等 B1 的音板需要 `D` 時一併進場**；單獨做效益低、破壞面大。工作項 B5 / D6。
- [ ] Validate models against external measured recordings or laboratory modal data not generated by TsukiSynth itself.
      **揚琴／舌鼓／鑼都有公開量測文獻**（初版「證據是零」已更正）→ `docs/EXTERNAL_ANCHOR_SOURCES.md` §5.1。
      但已取得的方法學等級不足、其餘卡付費牆；**可信外部錨仍須實體試體量測**。工作項 D4 / D5 / D7 / A8。
- [ ] Establish cross-platform numerical reproducibility rules (bit identity where possible, numeric/audio tolerance otherwise).
      **工具與 CI 三平台矩陣已就位、本機 GATE 全過**（`tools/crossplatform_verify.py`）。
      Rule 2：無登記容差時 exit 3 `UNREGISTERED` 只印數字不判定。
      **跨平台實測數字須 push 後由 CI 產出。** 工作項 A5 / C3。
- [ ] Add a polyphonic/missing-fundamental tuner mode only if it can refuse ambiguous cases reliably; the current target-aware monophonic detector must not guess.

## Honest N/A cases

- [ ] Design a short-transient estimator for `cimbalom/rubber`, `tongue_drum/rubber` and `water_gong/rubber`. Current T60 is only 14–28 ms, shorter than eight cycles at the probe pitch, so `--full` reports these three cases as `UNVERIFIED/N/A`.

## Deliberately outside the physical claim

- FM Piano, Custom Harmonics' authored ratios, Body macro and the artistic effect chain may remain useful, but must stay labelled non-physical/half-domain.
- Sample/granular layers do not become physical evidence merely because they are reproducible.
