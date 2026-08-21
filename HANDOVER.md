# TsukiSynth 交接文件

> 建立：2026-08-16　分支：`fix/deep-physics-audit-20260716`　最新 commit：`447faea`（已 push）
> **新 session 請先讀完這一頁再動手。** 詳細待辦在 `TODO.md` 開頭的「待辦總表」。

---

## 0. 一句話現況

**（2026-08-21 夜更新）**：X1/X2/三層驗證已 commit+push（49c22f5/b5ccb9b/26a0129），
**CI 三平台首次全綠**（macos = X2 實戰成功），X3 跨平台數字已得（提案待 C3 登記）。
**B2 施工卡完整執行完畢**：corpus 73/73、summer_m2 回綠、C2 發散收斂 128.75s→17.66s、
錨點 0.1497→0.0874、M10 標 Done，Rule 10 報告 `reports/b1_b2_bridge_damping_before_after.md`
——**月月已裁決 A1' 接受，本批隨後 commit**。corpus melody 掃描（informational）完成。
以下為 2026-08-16/20 的歷史現況記錄：


**兩盞紅燈（X1/X2）都已修，本機全綠，全部未 commit（R7）。**
X1（audit_repro 回歸）2026-08-16 修畢；X2（macOS Bessel）2026-08-20 修畢
（特性巨集切換 + 可攜級數，Windows 位元零改變，macos leg 轉綠需 push 後 CI 證明）。
另外 2026-08-20 月月**全權委託**建置「免耳免人工驗證三層 GATE」（TODO.md C3-b）：
L1 旋律位置驗證器 + L2 HostProbe + L3a Cubase 掃描驗證**已完工全綠**，
並首次驗證 plugin 即時路徑的旋律位置（5/5 PASS）；副產品：抓到 A12
（參數 set/restore 量化不對稱，DAW 存讀專案前後渲染位元不一致——誠實 FAIL 留檔）。
證據：`reports/gate_outputs/{x1_regression_fix,x2_bessel_portability,l1_l2_l3a_melody_gate,l3a_cubase_scan}.txt`。

---

## 1. 🔴 最優先：現在就壞著的東西

### 1.1 ~~B1 引入的回歸~~ ✅ 已修（2026-08-16，未 commit）

原症狀：CI run `31933324875` 紅燈，`ctest` 的 `audit_repro` 三項失敗
（`Semantic-order regression fixtures render successfully`／
`Permuting simultaneous events preserves the exact WAV bytes`／
`Inserting a zero-velocity event preserves the exact WAV bytes`）。

**根因**：B1 在 `src/engines/CimbalomEngine.h` 寫死
`kBridgeSoundboardMaterialKey = "wood_spruce"` 當共鳴板材質，且查表失敗時
**fail-closed**。呼叫點實為**四處**（原記三處，漏了引擎本身）：
`CimbalomEngine.h:133` → `return`、`ScoreRenderer.h:183` → `continue`、
`:704` → `return false`、`:999` → `return 0.0`。
而 `tests/audit_repro.cpp` 的測試專用精簡 DB 只有 `steel`
→ 查表必定失敗 → 渲染直接放棄 → 三個依賴渲染的測試連鎖失敗。

**月月裁決：(a)**——`tests/audit_repro.cpp::loadTestMaterial` 補進 `wood_spruce`。
理由：fail-closed 守衛本身是對的，「沒有共鳴板材質的 DB」本來就是不完整的 DB；
這是**測試 fixture 的缺口**，不是設計缺陷。數值逐字照抄 `data/materials.json`
（Rule 4 可溯源，不製造第二份會漂移的常數來源）。

**GATE**：三 target 全重建（§1.2 規約）exit 0 → `ctest` 3/3 Passed →
`TsukiSynthAuditTest.exe` 直接跑，三項具名 CHECK 皆 `[PASS]`、`PASS (0 failures)`。
`git diff --stat` 單檔 `tests/audit_repro.cpp`，**未動 `src/`**
→ R6 未觸發、**Rule 10 未觸發（無任何渲染輸出改變）**、R2 未動容差。

**未了**：這只解紅燈。「共鳴板材質該不該從寫死改成可注入」的結構問題
**併入 `TODO.md` A11 一起裁決**（A11 若選「加旗標預設關閉」或「換材質」，
需要的 plumbing 比單純注入更多，屆時一次做完；若選「確認現值」則維持寫死即可）。

### 1.2 ⚠️ 為什麼本機沒抓到——這是必須記住的教訓

B1 實作 agent 產出的 `reports/gate_outputs/b1_ctest_all.txt` 寫著「3/3 passed」，
對抗驗證的 GATE 視角也「獨立重跑」確認過——**但兩者跑的都是沒重建的舊 binary**。

`cmake --build build --config Release --target TsukiSynthPhysicsModelsTest` 只重建了
**一個**測試 target，`TsukiSynthAuditTest` 沒跟著重建，所以 `ctest` 測到的是 B1 之前的
`audit_repro.exe`。手動 `--target TsukiSynthAuditTest` 重建後，本機立刻重現與 CI
完全相同的三個 FAIL。

**規約（請寫進任何未來的施工卡）**：
```bash
# 跑 ctest 前一定要先把三個測試 target 全部重建，否則會測到舊 binary
cmake --build build --config Release --target TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest
ctest --test-dir build -C Release --output-on-failure
```

### 1.3 ~~macOS 可攜性 bug~~ ✅ 已修（2026-08-20，未 commit）

**修法**：`src/physics/BesselPortable.h`（A&S 9.1.10/9.6.10 升冪級數，驗證域
order 0..8 / x 0..16，域外 fail-closed NaN）+ `PlateModel::besselJ/besselI`
以 `__cpp_lib_math_special_functions` 特性巨集切換——有 std 的平台（MSVC 實測
巨集=201603、libstdc++）照走 std::，**Windows 前後渲染 SHA256 全等（Rule 10
不觸發）**；僅 libc++（Apple）走 fallback。錨點測試（scipy 獨立值）所有平台都跑；
Windows 上 grid 對照 std:: 最大偏差 2.1e-11。證據 `x2_bessel_portability.txt`。
**macos-14 leg 實際轉綠需 push 後 CI 證明（= A5）。** 以下為原始記錄：

#### 原症狀（跨平台 CI 第一次跑就抓到）

`cross-platform-emit (macos-14)` 建置失敗：

```
src/physics/PlateModel.h:265: error: no member named 'cyl_bessel_j' in namespace 'std'
src/physics/PlateModel.h:270: error: no member named 'cyl_bessel_i' in namespace 'std'
```

`std::cyl_bessel_j` / `std::cyl_bessel_i` 是 C++17 的數學特殊函式，**libstdc++（Linux）
有實作，libc++（Apple）沒有**。這是已知的標準庫落差，不是本專案的錯誤用法。

- ✅ ubuntu-24.04 建置成功（Linux/JUCE 依賴清單是對的）
- ✅ windows-2022 成功
- ❌ macos-14 失敗
- ⏭️ `cross-platform-compare` 因此 skipped——**跨平台實測數字這輪還是沒拿到**

**修法**：需自己實作或引入 Bessel 函式（Boost.Math、或自己寫級數/遞迴實作）。
若決定不支援 macOS，就把 macos 那條矩陣腿拿掉並在文件說明——**但那是縮小 GATE
範圍，需月月裁決**。

---

## 2. 這個專案是什麼

聾人使用者（月月）+ AI 不靠聽感、靠物理理論精確模擬聲音的 JUCE 8 VST3 合成器。

**唯一驗收依據是 `ROADMAP_PHYSICS.md`**，其 §1 有十條強制規則，開工前必讀全文。
最常踩到的：

| Rule | 內容 |
|---|---|
| R1 | 驗收只認 GATE 命令輸出，不認敘述 |
| R2 | **禁止調寬任何容差**。達不到門檻 → 回報數字 + 停下 |
| R3 | 禁止縮小 GATE 範圍 |
| R4 | 禁止 hardcode 無法溯源的物理常數 |
| R5 | Milestone 不可部分標記 Done |
| R6 | 改 `src/physics|engines|dsp|score` 後必跑 `--full` + 三 target build |
| R7 | **不 commit、不 push**（月月明示才做） |
| R10 | 任何讓既有 score 渲染結果改變的修正，必須產出前後對照報告 |

四個引擎：Cimbalom/Piano（弦，域內）、Tongue Drum（梁，域內）、
Water Gong（板，域內）、FM Piano（**域外**，已誠實標註）。

---

## 3. 檔案地圖

| 要找什麼 | 去哪 |
|---|---|
| **當前待辦（26 項，分 A/B/C/D 四類）** | `TODO.md` 開頭「待辦總表」 |
| 驗收規則與 Milestone 狀態 | `ROADMAP_PHYSICS.md` §1、§2、§6 容差表 |
| **文獻線總覽（誰是誰的前置）** | `docs/RESEARCH_INDEX.md` |
| 六張施工卡（B1–B6 規格） | `docs/workcards/B*.md` |
| 溯源文件 | `docs/{BRIDGE_ADMITTANCE,STRING_DAMPING,HAMMER_CONTACT,WOOD_ANISOTROPY,EXTERNAL_ANCHOR}_SOURCES.md` |
| GATE 證據 | `reports/gate_outputs/` |
| 歷史決策 | `DEVLOG.md` |
| AI 作曲用法 | `docs/AI_PERFORMANCE_PLAYBOOK.zh-TW.md`、`docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md` |

`libs/JUCE` 是 submodule（JUCE 8.0.12，釘在 `501c0767`，從未動過）。
新 clone 要 `git clone --recursive`，或事後 `git submodule update --init --recursive`。

---

## 4. 已完成到哪

- **M1–M7、M9 全部 Done**，GATE 全綠。
- **M4** 2026-08-15 月月目視驗收通過轉 Done。
- **M8 In progress**：剩 Cubase 四步人工驗證 + merge → `main` 時機。
- **M10（琴橋導納）In progress**：實作完成但 §1.1 的回歸未修、Rule 10 報告未產出。

corpus 基準：73 檔，上一次全綠是 2026-08-06（`af849ec`）。
阻尼寬頻化 + B1 之後**尚未重驗**。

---

## 5. 接下來的順序（建議）

1. ~~修 §1.1 的回歸~~ ✅ **2026-08-16 完成**（裁決 (a)，ctest 3/3，未 commit）。
2. ~~修 §1.3 的 macOS Bessel（X2）~~ ✅ **2026-08-20 完成**（`BesselPortable.h` A&S 級數 +
   `__cpp_lib_math_special_functions` 特性巨集切換；Windows 前後渲染 SHA256 全等 → Rule 10 未觸發；
   grid 對照 std 最大偏差 2.1e-11；macos leg 實際轉綠等 push/CI = A5）。
3. ~~重跑三 target + `--full`~~ ✅ 全綠（`x2_bessel_portability.txt`）。
   **新增（2026-08-20 委託線）**：L1/L2/L3a 三層免耳驗證完工（TODO C3-b 進度區），
   剩 piano-roll 報告層 + L3b（等 computer-use 連接器）+ corpus 掃描（排 B2 後）。
   A12 為新發現待裁決。
4. **發 B2 卡**（`docs/workcards/B2.md`）：Rule 10 前後對照報告 +
   corpus 73 檔四分片重驗 + 響度錨點常數重測。**這是唯一能讓 M10 收尾的路。**
5. 之後才輪到 B3（弦阻尼律）→ B4（槌頭）→ B5（木材）→ B6（輻射）。

**不要跳過 B2 直接做 B3。** 兩者都改阻尼律，同時改會讓 Rule 10 無法歸因
（`reports/deep_fix_before_after.md` §7 已經吃過一次這個虧）。

---

## 6. 月月待裁決（AI 不能自己決定）

完整清單見 `TODO.md` 的 A 段（A1–A11）。最擋路的四個：

- **A1** Rule 10 前後對照裁決（`reports/deep_fix_before_after.md` §00 有白話導讀）
- **A11** 共鳴板 `h=9mm` / `wood_spruce` 的確認，以及「未確認常數是否該無條件生效於預設路徑」的流程問題（三個選項已列）
- **A7** repo License 定案（已決定「保留商業」，要寫 `LICENSE` + 改 `README.md:349` 的 `TBD`）
- **A9** Cubase 四步人工驗證（AI 無法代做）

---

## 7. 關於「要不要加濾波器」（2026-08-16 月月提問）

要分成兩個完全不同的東西看：

### 7.1 物理側：**需要，而且已經在路線圖上**

`docs/BRIDGE_ADMITTANCE_SOURCES.md` §4 已列明侷限：目前用的是**平滑的**特徵導納
`Y∞`（單一實數），它在原理上無法重現 Wogram 量到的「相鄰半音 F#4 3.5s vs G4 0.7s」
這種 5:1 落差——那是共鳴板共振峰谷造成的。

要重現峰谷，就是**把單一實數 G 換成一個頻率相依的複數導納 Y(f)**，
而實作上那正是**一組並聯的共振器 = 濾波器組**。文獻做法明確：
Chaigne (ICA 2010) 就是用約 100 個並聯機械振子建模琴橋導納，每個振子三個參數
（質量／剛度／阻抗）。

**基礎設施已經有了**：`src/dsp/BiquadFilter.h` 與 `src/dsp/BodyResonance.h`
（兩個共振帶通 + 一個低通）就是小型的共振器組，`BodyResonance::totalResponse()`
已經能算穩態傳遞函數，M2 的振幅驗證也已經在用它。

**但這是「共鳴板耦合第二階段」，不是現在該做的**——目前連第一階段（B1）都還沒收尾。

### 7.2 創作側：**目前沒有，加了會落在驗證域外**

現在**沒有**使用者可見的濾波器區塊（`PluginProcessor.cpp` / `ScoreParser.h` 都查不到
`cutoff` / `resonance` 之類參數）。現有的都是物理鏈內部的：
`BiquadFilter`、`BodyResonance`、效果鏈的 Reverb/Delay/Comp/Dist、
以及 2026-08-06 加的亮度補償 EQ（高頻 shelf）。

如果要加一個傳統合成器的 VCF（cutoff + resonance），它**不是物理主張的一部分**，
必須比照 `spectralTilt` 與亮度 EQ 的做法標註為 creative 層、劃出驗證域外（R9），
且驗證時一律關閉。這是產品線的事，`ROADMAP.md` 的 v0.5「Advanced Sound Design」
本來就寫著「creative features only with explicit out-of-physical-domain labels」。

**建議**：物理側的濾波器組（7.1）是有價值的，但排在 B2 收尾之後；
創作側的 VCF（7.2）現在不做，等 M8 merge 完、產品線啟動再說。

---

## 8. 環境備忘

- 主目錄 `C:\Users\admin\Desktop\Claude\tsuki-synth`
- Windows / MSVC 19.50 / PowerShell 主、Bash 可用
- 建置：`cmake -B build -DCMAKE_BUILD_TYPE=Release -DTSUKI_BUILD_TESTS=ON`
- CLI 產物：`build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`
- Python 需 numpy + scipy（`tools/requirements-physics.txt`）
- GitHub：`TsKR2828/tsuki-synth`，CI workflow `.github/workflows/physics.yml`
  （push 到 `main` 或 `fix/**` 觸發）
