# TsukiSynth 交接文件

> 重寫：2026-08-22　分支：`fix/deep-physics-audit-20260716`
> **新 session 請先讀完這一頁再動手。** 待辦細節在 `TODO.md` 開頭「待辦總表」；歷史決策在 `DEVLOG.md`；
> 2026-08-16 版交接的歷史內容已由 git 歷史保存（`d46cd84` 前後），本檔只寫現況。

---

## 0. 一句話現況

**B3 完工並已併入 main。** 紅燈清零、CI 三平台全綠、M10 收官、免耳三層驗證鏈全線閉環之後，
**B3（弦阻尼律換第一原理）已於 2026-08-24 完成**：GATE 12 條全過、corpus 73/73 零新增豁免，
Rule 10 報告 `reports/string_damping_firstprinciples_before_after.md` 已產出。
**2026-08-26 月月三裁決**：A1 舊批 Rule 10 放行（整批接受）+ 授權本批 commit 併入 `main`
（A6 完成，M8-8b 關閉）+ A7 LICENSE 已寫入。A4（亮度 EQ）/A11（共鳴板 h/材質）兩份
免耳裁決包已備（`reports/decision_packets/`），仍待月月選項。**下一步 = B4（槌頭接觸）。**

## 1. 2026-08-20 ~ 08-22 這三天發生了什麼（新 session 必讀）

1. **X1/X2 紅燈修畢**：audit_repro 回歸（測試 DB 補 `wood_spruce`，月月裁決 (a)）；
   macOS Bessel（`src/physics/BesselPortable.h` A&S 級數 + `__cpp_lib_math_special_functions`
   特性巨集切換，Windows 位元零改變）。
2. **月月重大委託（2026-08-20）**：「我沒有樂理基礎也沒有程式基礎…你自己想辦法，照順序把
   缺口都補上，我最後再拿去給專業人士聽」——免耳免人工驗證全權委託 AI，容差 AI 自定但
   **R2 仍禁事後調寬**；最終**美學**驗收 = 外部專業人士試聽（月月安排）；物理/位置正確性
   由 GATE 鏈負責，兩者主張分開。
3. **免耳三層驗證建成**（設計 `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md`）：
   - **L1 `tools/melody_verify.py`**：score↔WAV 逐事件 onset(±10ms)/pitch(5c 已批准) 正向驗證
     + extra-scan；8 條 fail-closed 拒答規則（重擊遮蔽/泛音污染/course 自拍/床能量/低頻<167Hz
     精修極限/帶碰撞/delay/fm_ratio≠1），有效殘響 = max(乾 T60, reverb decay)；哨兵五件組
     （時移/移調/刪音/幻音必 FAIL + 原封必 PASS）；`--html` piano-roll 疊圖（聾人可視驗收）。
     **主張域**（設計文件 §7，月光 1141 事件四輪迭代定案）：強域=單音/稀疏/host 渲染；
     弱域=密集低音複音+長混響 → 誠實拒答，位置保證改由 verify_score 2e 位元決定性承擔。
   - **L2 `TsukiSynthHostProbe`**（`tests/host_probe.cpp`，CMake target）：載磁碟上的 .vst3，
     A9 四步自動化，**16/16 全 PASS**；plugin 即時路徑旋律位置史上首驗 5/5。
   - **L3a `tools/cubase_scan_verify.py`**：解析真 Cubase 掃描快取 XML，S1-S5 全 PASS。
   - **L3b（2026-08-22 凌晨，月月授權螢幕控制）**：AI 全程操作真 Cubase——建軌/匯入哨兵
     MIDI/tempo 100 對齊/plugin GUI 上 Reverb 歸零/匯出 Wave 48k24bit → **melody_verify 5/5**
     （onset ≤2.5ms、pitch ≤0.4c）；存檔→關閉→重開→再匯出 → **音訊 SHA256 位元全等**。
     專案留檔 `Documents\Cubase LE AI Elements Projects\无标题-06\l3b_tsukisynth_verify.cpr`。
4. **B2 施工卡完整執行**（M10 收官）：corpus **73/73 PASS 零新增豁免**、`summer_m2` 自動回綠
   （−46.8 FAIL → −52.2 PASS）、寬頻化低音發散被 B1 封頂證實（**C2 128.75s → 17.66s**）、
   響度錨點重測 `kCimbalomAttackEnergyRefA4` 0.1497→**0.0874**（中央弦反解法；Chromatic 兩值
   不變 = 雙 null 自驗）。**Rule 10 報告 `reports/b1_b2_bridge_damping_before_after.md`**，
   月月裁決 **A1' 接受**。
5. **CI 三平台首次全綠**（run 32446987833）+ **X3 跨平台數字**：max delta 5 LSB@24bit、
   pitch +0.0000c → **C3 容差已登記**（`scores/crossplatform_tolerance.json`，月月裁決照提案）
   → `cross-platform-compare` 自此為**阻斷式 GATE**。
6. **A12 修畢**（月月裁決 (a)）：36 個 float 參數轉連續（interval 0），state round-trip 位元精確；
   H5 主張修正為 fresh-vs-fresh（DAW「重開專案每次播放一致」語意——噪音事件計數器刻意隨敲擊
   遞增且不入 state）。
7. **A9 關閉**：四步全數以自動化+真 host 證據取代人工（唯一殘留 = Cubase GUI 畫 automation
   lane，L2 合約層已蓋，非位置主張必需）。

## 2. 這個專案是什麼

聾人使用者（月月）+ AI 不靠聽感、靠物理理論精確模擬聲音的 JUCE 8 VST3 合成器。
**唯一驗收依據 `ROADMAP_PHYSICS.md`**，§1 十條強制規則開工前必讀。最常踩的：

| Rule | 內容 |
|---|---|
| R1 | 驗收只認 GATE 命令輸出，不認敘述 |
| R2 | **禁止調寬任何容差**。達不到 → 回報數字 + 停下 |
| R3 | 禁止縮小 GATE 範圍 |
| R4 | 禁止 hardcode 無法溯源的物理常數 |
| R5 | Milestone 不可部分標記 Done |
| R6 | 改 `src/physics|engines|dsp|score` 後必跑 `--full` + 三 target build |
| R7 | **不 commit、不 push**（月月明示才做；本輪月月已三度授權為例） |
| R10 | 任何讓既有 score 渲染結果改變的修正，必須產出前後對照報告 |

**X4 規約（必遵守，2026-08-16 教訓）**：跑 `ctest` 前必先重建三個測試 target
（`TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest`），否則測到舊 binary。

四個引擎：Cimbalom/Piano（弦，域內，**含 B1 琴橋耦合**）、Tongue Drum（梁，域內）、
Water Gong（板，域內）、FM Piano（域外，已誠實標註）。

## 3. 檔案地圖

| 要找什麼 | 去哪 |
|---|---|
| 當前待辦 | `TODO.md` 開頭「待辦總表」（X/A/B/C/D 分段） |
| 驗收規則、Milestone、容差表 | `ROADMAP_PHYSICS.md` §1 / §2 / §6 |
| **免耳三層驗證設計 + 主張域** | `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md`（§7 = 方法極限） |
| B1+B2 的 Rule 10 前後對照（月月已接受） | `reports/b1_b2_bridge_damping_before_after.md` |
| 文獻線總覽 | `docs/RESEARCH_INDEX.md` |
| 施工卡（B3-B6 待做） | `docs/workcards/B*.md` |
| 溯源文件 | `docs/{BRIDGE_ADMITTANCE,STRING_DAMPING,HAMMER_CONTACT,WOOD_ANISOTROPY,EXTERNAL_ANCHOR}_SOURCES.md` |
| GATE 證據 | `reports/gate_outputs/`（x1/x2/x3/l1/l2/l3a/l3b/b2/a12_c3 前綴） |
| 歷史決策 | `DEVLOG.md` |

`libs/JUCE` 是 submodule（8.0.12，釘 `501c0767`，從未動過）；新 clone 用 `--recursive`。

## 4. Milestone 狀態

- **M1–M7、M9、M10 全部 Done**（M10 = 2026-08-21 B2 收官 + 月月 A1' 接受）。
- **M8 In progress**：8a 的 Cubase 驗證已由 L2/L3a/L3b 自動化完成（A9 關閉）；
  **只剩 8b：merge → `main` 時機（= TODO A6，月月裁決）**。
- corpus 基準：73 檔全綠（2026-08-21，B1+B2 疊加後，`b2_corpus_*.txt`）。

## 5. 接下來的順序（建議）

1. **月月讀 B3 Rule 10 報告並裁決**（最優先）：
   `reports/string_damping_firstprinciples_before_after.md`——先讀最前面的白話導讀卡，
   特別看 `Q⁻¹_disl`/`eta` 佔比表（steel/aluminum 受影響最大）與 `damping_override`
   錨點保證變化聲明，裁決「接受」或「指名回退」。改動全數 unstaged。
2. **月月裁決積壓**（都不擋工程線，見 TODO A 段）：A1（7/22 舊批 Rule 10 報告）、
   **A4（亮度 EQ 去留）與 A11（共鳴板 h/材質確認）——裁決包已備妥
   `reports/decision_packets/A4_brightness_eq.md`／`A11_soundboard_sensitivity.md`**、
   A10（Score 控制台實操）、A6（merge → main）、A7（License 檔）、A8（外部資料集）。
3. ~~B3 弦阻尼律~~ **已完成（2026-08-24，見上）**；X4 規約已補進六張施工卡。
4. 之後 B4（槌頭）→ B5（木材）→ B6（輻射）。

## 6. 給下一個 session 的操作備忘

- 建置：`cmake -B build -DCMAKE_BUILD_TYPE=Release -DTSUKI_BUILD_TESTS=ON`
- CLI：`build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`
- 全套 GATE：`--full`＋三 target build＋ctest（先重建三測試 target！）＋`pytest tests -q`＋
  corpus 四分片 `verify_score.py --all --shard-index N --shard-count 4`
- 旋律位置：`python tools/melody_verify.py <score> [--wav W] [--html H]`；`--selftest` 跑哨兵
- HostProbe：`build/Release/TsukiSynthHostProbe.exe build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3 <outdir>`
- 跨平台：CI 自動跑（現為阻斷式）；本機 `tools/crossplatform_verify.py --selftest`
- Cubase 掃描：`python tools/cubase_scan_verify.py`
- **系統部署的 VST3 是 0.2.0（7/12）**——要讓 Cubase 測最新版，月月需以管理員權限把
  `build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3` 覆蓋到 `C:\Program Files\Common Files\VST3\`
- GitHub `TsKR2828/tsuki-synth`，CI `.github/workflows/physics.yml`（push `main`/`fix/**` 觸發）
- Python 需 numpy+scipy+mido（`tools/requirements-physics.txt`）
