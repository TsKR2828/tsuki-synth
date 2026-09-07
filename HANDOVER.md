# TsukiSynth 交接文件

> 交接視窗：2026-08-30（2026-09-07 補記 §0-2）　分支：`fix/deep-physics-audit-20260716`
> （HEAD `cdf2017`；`main` 於 2026-09-07 再度同步，見 §0-2；工作樹乾淨）
> **新 session 請先讀完這一頁再動手。** 待辦細節在 `TODO.md` 開頭「待辦總表」；
> 歷史決策在 `DEVLOG.md`；更早版本的交接內容由 git 歷史保存，本檔只寫現況。

---

## 0. 一句話現況

**B1–B6 物理鏈全部 Done；分支已全數 merge → `main`（`b7e4330`）；
UI 改走「功能規格 → 設計端重做」；密集複音驗證缺口用逐事件分軌補上一半
（給愛麗絲拒答 862 → 212，疊加證明成立）。**

**現在擋路的是三張裁決卡**：A13（partial GATE 主張域）、A14（高音弱基頻是物理正確
還是引擎缺陷）、以及 UI 功能規格要不要送設計端。另有一批 **unstaged 待月月審**。

## 0-1. 2026-08-31 追加：codex 稽核修復輪

codex 對全專案做了兩輪稽核，證據在
`reports/gate_outputs/stem_verify_fur_elise_run.txt`（1535 行）。
修復已 commit（見下方分支狀態），**問題點整理成診斷文件**：

- `docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.zh-TW.md`
  — 三個結構性病根（同一事實兩份實作／GATE 覆蓋形狀對準 CLI 而缺陷在 plugin／
  CLI 出貨路徑乾淨所以自己踩不到）、未修清單、以及**我複驗後與稽核判斷不同的項目**。
- `reports/decision_packets/F03_IR_PRESET_RECALL.zh-TW.md`
  — IR user preset 不自包含，**待月月選 A 內嵌／B 受管理 IR 庫／C 資源參考**。

新 session 若要接這條線，先讀那份診斷文件的 §4（未修項目）與附錄（卡在裁決 vs 可開工）。

## 0-2. 2026-09-07 補記：8/31 兩個 commit 登記 + 月月裁決批次

8/30 之後分支上多了兩個 commit，先前 HANDOVER/TODO 都沒登記：

| commit | 內容 |
|---|---|
| `a7413e5` | 稽核修復批次：F-01/F-02（工具刪使用者資料）、F-06（Type-0 MIDI）、F-07（檔名驗證）、K-04/K-06（subprocess timeout）+ 哨兵測試 |
| `cdf2017` | **稽核 §4-A 已修**：水鑼 Pitch Glide 最終音高依 host buffer size（cap 改取樣層級）+ `docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.zh-TW.md` |

→ 稽核未修清單自此只剩 §4-B（`getTailLengthSeconds()`）、§4-C（F-03 裁決）、
§4-D（schema 三份契約）、§4-E（K-02/K-03）、§4-F（文件措辭）、§4-G（CI 接新測試）。

**月月 2026-09-07 裁決（一次批 6 項）**：
1. 上述兩個 commit **push + merge → `main`**（本次執行）。
2. `pytest` + `mido` 加進 `tools/requirements-physics.txt`，新測試檔接進 CI（§4-G 關閉）。
3. **A8 外部資料集（TU Berlin 樂器指向性資料庫，CC BY-SA 4.0）下載**——只當外部參照，
   repo 內只留 DOI + SHA256 + 比對數字，資料檔不進版控。
4. UI 功能規格**等所有功能做完再**送設計端重做（不是現在）。
5. A13 / A14 / F-03 改由 AI 查外部資料（含 Reddit 等社群討論）後做出決定，附證據。
6. 可開工的工程項與「只做了骨架」的部分，以 規劃者→Sonnet 工兵→Opus 稽核 的 Dynamic Workflow 發包。

## 1. 立刻要知道的三件事

1. **`main` 與分支已同步**（2026-08-30 首次；2026-09-07 再同步含 `a7413e5`/`cdf2017`，
   皆月月明示授權 commit+push+merge）。分支保留為工作 branch。
   **R7 照舊：往後沒有月月明示就不 commit / 不 push。**
2. **工作樹乾淨**（2026-09-07）。8/30 那批 stem_verify 產物已在 `212106c` 前入庫。
3. **月月是聾人開發者，全程免耳驗收。** 任何「聽起來如何」的主張都不算數；
   物理/位置正確性由 GATE 鏈負責，美學驗收由月月安排外部專業人士。這是本專案的根本設定。
   corpus 為 **75 檔**（任何文件寫 73 都是舊的），最新全綠證據
   `reports/gate_outputs/b6_corpus_phase34.txt`。

## 2. 這個專案是什麼

聾人使用者（月月）+ AI 不靠聽感、靠物理理論精確模擬聲音的 JUCE 8 VST3 合成器。
**唯一驗收依據 `ROADMAP_PHYSICS.md`**，§1 十條強制規則開工前必讀。最常踩的：

| Rule | 內容 |
|---|---|
| R1 | 驗收只認 GATE 命令輸出，不認敘述 |
| R2 | **禁止調寬任何容差**。達不到 → 回報數字 + 停下 |
| R3 | 禁止縮小 GATE 範圍 |
| R4 | 禁止 hardcode 無法溯源的物理常數；查不到就誠實標「未溯源」 |
| R5 | Milestone 不可部分標記 Done |
| R6 | 改 `src/physics\|engines\|dsp\|score` 後必跑 `--full` + 三 target build |
| R7 | **不 commit、不 push**（月月明示才做） |
| R10 | 任何讓既有 score 渲染結果改變的修正，必須產出前後對照報告 |

**X4 規約（必遵守）**：跑 `ctest` 前必先重建三個測試 target
（`TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest`），否則測到舊 binary。

四個引擎：Cimbalom/Piano（弦，域內）、Tongue Drum（梁，域內）、
Water Gong（板，域內）、FM Piano（**域外**，已誠實標註）。

## 3. 物理鏈現況（B1–B6 全 Done）

| 卡 | 做了什麼（白話） | Rule 10 報告 |
|---|---|---|
| B1 | 琴橋導納／共鳴板耦合——低音發散 C2 128.75s→17.66s | `reports/b1_b2_bridge_damping_before_after.md` |
| B2 | 阻尼寬頻化收尾 + 響度錨點重測（0.1497→0.0874） | 同上 |
| B3 | 弦阻尼律換 Cuesta & Valette 零自由參數三機制 | `reports/string_damping_firstprinciples_before_after.md` |
| B4 | 槌氈接觸時間從查表換成物理解出（力度指數 −0.2 → −0.394/−0.429/−0.500） | `reports/b4_hammer_contact_before_after.md` |
| B5 | 木材正交異向常數入庫（**schema 備妥、零消費路徑、死資料**——措辭鐵律，不可說「已支援」） | `reports/b5_schema_noop_proof.md`（bit-exact no-op） |
| B6 | 輻射效率骨架 σ(f) + **絕對聲壓校準**（方案 B）——引擎現在能主張「這個音在 1.05m 外幾 Pa」 | 不觸發（只進 `--dump-modes`，位元不變 8/8） |

**B6 校準的性質要講清楚**：月月裁決方案 B——把「數位 1.0 ≡ 1 Pa ≡ 94 dB SPL @1.05m」
釘在**創作層（響度補償/EQ）之前**的純物理訊號點。這是**慣例錨定，不是實測**，
程式碼註解已 R4 標註。真正的第一原理力鏈是 B7（見 §6）。

## 4. 驗證鏈全圖（聾人+AI 的閉環）

```
MIDI 原譜 ──① score_vs_midi_verify──> score.json ──② melody_verify──> WAV
                                          │                            │
                                          └──③ verify_score (75 檔) ───┘
                                                                       │
              ④ HostProbe(plugin) / ⑤ Cubase 實測 / ⑥ piano-roll 影片 ─┘
```

1. **`tools/score_vs_midi_verify.py`**（2026-08-29 新增，補上轉譜層缺口）——
   獨立 SMF parser（刻意**不用** mido，避免與轉譜器共模錯誤）、逐音符全量 1:1、
   pitch 整數零容差、onset ≤1ms、四種突變哨兵。
2. **`tools/melody_verify.py`**——score↔WAV 逐事件 onset(±10ms)/pitch(5c)，
   8 條 fail-closed 拒答規則，哨兵五件組，`--html` piano-roll 疊圖。
   **主張域**在 `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §7（強域=單音/稀疏；
   弱域=密集低音複音 → 誠實拒答，位置保證改由 verify_score 位元決定性承擔）。
3. **`tools/verify_score.py --all`**——corpus 75 檔全量（四分片可平行）。
4. **`TsukiSynthHostProbe`**——載磁碟 .vst3，plugin 即時路徑 16/16。
5. **L3b Cubase 實測**（2026-08-22，月月授權螢幕控制）——真 host 匯出 melody_verify 5/5、
   存讀位元全等。
6. **`tools/melody_roll_video.py`**（2026-08-29 新增）——旋律形狀影片，聾人視覺複核用。
   2026-08-30 換月月指定的霓虹配色 + 左側固定音名尺（`--theme neon` 預設）。
7. **`tools/stem_verify.py`**（2026-08-30 新增，**本輪重點**）——逐事件乾聲分軌 +
   線性疊加證明，把密集複音從「大量拒答」轉成可判定。給愛麗絲全曲拒答 **862 → 212**，
   疊加證明 ESTABLISHED（殘差 −118.60 dBFS vs 門檻 −85 dBFS）。
   **主張限制是硬的，寫在 `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8**：
   (a) 音高判定**只在乾聲上有效**（殘響會把質心拉偏最多 9.5 cents）；
   (b) 音高與起音**必須分開主張**，不可壓成單一 verdict；
   (c) **partial 的頻率與振幅從未實測，不可宣稱「泛音已驗證」**。

## 5. 接下來該做什麼（優先序）

1. **⚠️ stem_verify 收尾四項**（本輪產物，工具已可跑但還沒資格當 GATE）。
   建議順序 **C10 → C11 → C12 →（A13/A14 裁決後）C13**，細節在 `TODO.md`：
   - **C10 量測器自身的合成哨兵（先做這個）**——月月裁定：±5 cents 是本專案既有門檻、
     **不是 ISO 或業界標準**；量測器必須先用合成訊號自證誤差 **≤1 cent**，
     才有資格執行 ±5 cents 的產品 GATE。**不做這項，後面所有音高數字都站在未校驗的尺上。**
   - **C11 逐顆記錄拒答理由**——212 顆拒答目前是黑盒，無法收斂。
   - **C12 `--analysis-dry` + 衍生 score 的 hash/diff 寫進 JSON**——
     目前乾聲跑法靠手動改 score 存 temp，temp 一清就只剩口述來源。
   - **C13 harmonic-aware 判定**——給 22 顆弱基頻高音一個答得出來的問法（前置：A13/A14）。
   **兩張擋路的裁決卡**：
   - **A13 partial GATE 的主張域**——要不要立、主張多強、容差多少（新容差不可由工程端自訂，R2）。
   - **A14 高音弱基頻是物理正確還是引擎缺陷**——若判定要改引擎，**觸發 Rule 10**。

2. **UI：功能規格要不要送設計端**（等月月一句話）。
   2026-08-30 月月**否決**雙開門提案（原話：「左側那麼寬了但旋鈕超小；右側一點也沒有
   鋼琴／揚琴／空靈鼓的視覺感，看上去像廉價玩具」），裁定**撇開現行 UI 的所有既有元素**，
   由設計端從功能重新設計。`uiux/double_door_mockup.html` 與
   `docs/uiux/DOUBLE_DOOR_PROPOSAL.zh-TW.md` **作廢，只留歷史**。
   → 設計輸入文件已備妥：**`docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md`**
   （60 個 APVTS 參數全表 + 非參數控制項 + 6 條使用情境 + 8 條硬性約束，
   **刻意不寫任何顏色／尺寸／佈局**）。
   **兩個誠實揭露照舊有效**：(a) 樂器模擬畫面**從來沒做過**，不是復活是全新功能；
   (b)「揚琴左右手強弱」在 APVTS 裡**沒有對應參數**，要落地得另開卡加參數與 DSP。

3. **換源重製排程**（月月 2026-08-28 裁決「CC BY 可以」）——
   計畫在 `reports/decision_packets/CLASSICAL_RELICENSE_PLAN.md`：
   月光 4 檔（CC BY-SA 2.5）+ 四季 12 樂章（CC BY-SA 3.0）授權不淨，**換源前不上架**；
   給愛麗絲已完成（真 PD）。四季可換 IMSLP Schoonenbeek CC BY（但編制不同）、
   月光需從譜面重轉譜。轉譜器已泛化（`tools/midi_to_tsukisynth.py convert` 子命令），
   four-seasons 舊路徑零改變已用位元比對證明。
4. **B7（第一原理力鏈，方案 C）**——卡已立 `docs/workcards/B7.md`。
   **前置硬性阻擋已解除**（B6 方案 B 已落地=B7 的地基）。
   開工前要補 Phase 0 三塊資料，最關鍵的缺口：**MIDI velocity（0-1 proxy）→ 真實槌速 m/s
   的映射函數查無出處**（已知真實槌速範圍 0.11–6.83 m/s，Boutillon 實測／Askenfelt KTH 講義）。
5. **D8 tongue_drum 引擎缺陷**（商品線的擋路石）——同 velocity 下有 **40.3 dB 音高-響度斜率**
   （MIDI 37→87：−32.8→−73.1 dBFS；cimbalom 同域僅 4.4 dB），且輸出近純正弦無泛音列。
   後果：空靈鼓獨奏商品不可用。屬引擎物理層調查，改動觸發 Rule 10。
6. **IR 配套修補**（`docs/IR_REVERB_AUDIT.zh-TW.md` 已出結論）——
   卷積實作本身**正統無誤**（juce::dsp::Convolution，IR 模式取代演算法 reverb）。
   但有一個 **bug 級落差：IR 路徑進 DAW session state 卻沒進使用者 preset**，
   存了 IR 模式的 preset 重載會靜默退回演算法殘響；另有 ALGO↔IR 切換 0.15× 增益跳變、
   `.wav`/`.json` 共用同一顆 Load 鈕造成心智模型混淆。三個選項與工程量在該文件 §4。
7. **音效產品線**（月月：不一定要完整樂曲，但要有判準）——
   `docs/SOUND_DESIGN_KNOWLEDGE.zh-TW.md` 已建（9 個一手來源含《The Sound Effects Bible》全文、
   6 個可寫成 Python 檢查器的量測判準）。開工前必讀，不得再盲做「10 秒兩聲鐘響」。

## 6. 檔案地圖

| 要找什麼 | 去哪 |
|---|---|
| 當前待辦 | `TODO.md` 開頭「待辦總表」（X/A/B/C/D 分段） |
| 驗收規則、Milestone、容差表 | `ROADMAP_PHYSICS.md` §1 / §2 / §6 |
| 免耳驗證設計 + 主張域 | `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` **§8（v2，2026-08-30 分軌後最新）**、§7（v1） |
| 分軌驗證證據 | `reports/gate_outputs/stem_verify_fur_elise_run.txt`（含月月獨立查核追加段） |
| 施工卡（B7 待做） | `docs/workcards/B1–B7.md` |
| 月月裁決包（看完就能決定的問題） | `reports/decision_packets/` |
| 溯源文件 | `docs/{BRIDGE_ADMITTANCE,STRING_DAMPING,HAMMER_CONTACT,WOOD_ANISOTROPY,RADIATION_POWER,EXTERNAL_ANCHOR,TAIWAN_WOOD_SPECIES,D2_CHROMATIC_CONTACT}_*.md` |
| GATE 證據 | `reports/gate_outputs/`（x1-x4/l1-l3b/b1-b7/furelise 前綴） |
| 產品/市場 | `docs/PRODUCT_MARKET_NOTES.zh-TW.md`、`docs/SOUND_DESIGN_KNOWLEDGE.zh-TW.md`、`reports/product_sheets/` |
| UI/UX | **`docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md`（現行設計輸入）**、`docs/MUSICIAN_UX_RESEARCH.zh-TW.md`；已作廢：`docs/uiux/DOUBLE_DOOR_PROPOSAL.zh-TW.md`＋`uiux/double_door_mockup.html` |
| 田野/文化素材 | `docs/PESTLE_MUSIC_FIELD_NOTES.zh-TW.md`（月月口述杵音工藝） |
| 外部參照調查 | `docs/COMMERCIAL_PM_PUBLIC_DATA.zh-TW.md`（Pianoteq 等公開資料調查） |
| 歷史決策 | `DEVLOG.md` |

`libs/JUCE` 是 submodule（8.0.12，釘 `501c0767`，從未動過）；新 clone 用 `--recursive`。

## 7. 操作備忘

- 建置：`cmake -B build -DCMAKE_BUILD_TYPE=Release -DTSUKI_BUILD_TESTS=ON`
- CLI：`build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`
- 全套 GATE：`--full` ＋三 target build ＋ ctest（**先重建三測試 target！**）＋
  `pytest tests -q`（現 156 passed）＋ corpus 四分片
  `verify_score.py --all --shard-index N --shard-count 4`
- 轉譜驗證：`python tools/score_vs_midi_verify.py <midi> <score>`；`--selftest` 跑哨兵
- 旋律位置：`python tools/melody_verify.py <score> [--wav W] [--html H]`
- 旋律影片：`python tools/melody_roll_video.py <score> [--wav W] [--json 既有報告] [--out out.mp4]`
  `--theme neon`（預設，2026-08-30 月月指定的霓虹紫配色＋左側固定音名尺）／
  `--theme slate`（原單色深藍灰）；`--still-at <秒>` 只出一張 PNG 供快速看配色
- **分軌驗證**：`python tools/stem_verify.py <score> [--jobs N] [--json 報告.json] [--limit N]`
  （`--jobs` 預設 4；905 事件全曲約 10 分鐘）。
  **必須在乾聲上判定**——目前工具沒有 `--analysis-dry`（C12 待做），
  現行做法是先手動把 score 的 `global.effects.reverb` 的 wet/decay 歸零另存再跑。
  哨兵：`PYTHONPATH=tools python -m pytest tests/test_stem_verify.py -q`（21 passed）
- HostProbe：`build/Release/TsukiSynthHostProbe.exe <.vst3 路徑> <outdir>`
- ffmpeg（母帶/影片用）：`C:\Users\admin\Desktop\Tools\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe`
- **系統部署的 VST3 仍是 0.2.0（7/12）**——要讓 Cubase 測最新版，月月需以管理員權限把
  `build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3` 覆蓋到 `C:\Program Files\Common Files\VST3\`
- GitHub `TsKR2828/tsuki-synth`，CI `.github/workflows/physics.yml`（push `main`/`fix/**` 觸發）
- Python 需 numpy+scipy+mido（`tools/requirements-physics.txt`）

## 8. 給下一個 session 的工作方式備忘

月月 2026-08-28 明示的分工架構（token 效率考量）：
**規劃者畫地圖、Sonnet 當工兵、Opus 當驗證者**——用 Dynamic Workflow 發包，
工兵做完由獨立 Opus 稽核（不採信工兵自報，親自重跑/親自開來源），
抓到 finding 進修正回合。這套在本輪抓出過真問題（Codex 數字的 4 個 R4 失真、
B6 的 5 個缺陷、研究文件的引用不實），**不要為了省事跳過稽核層**。

月月的偏好（歷史教訓，違反過會被糾正）：
- 不要腦補——先看實際檔案/實際渲染，物件名與舊假設不可信。
- 查不到就說查不到，寧缺勿假；不要編數字充數。
- 需要人類裁決的事，做成「看完數字就能選 A/B/C」的裁決包，不要替月月決定。
- 月月沒有樂理與程式基礎，白話說明要到位；但她的直覺常常命中真問題
  （音效判準缺口、IR 疑慮、轉譜驗證缺口都是月月先提出的）。
