# TsukiSynth 交接文件

> 重寫：2026-08-29／增修 2026-08-30　分支：`fix/deep-physics-audit-20260716`（HEAD `51bd6cc`）
> **新 session 請先讀完這一頁再動手。** 待辦細節在 `TODO.md` 開頭「待辦總表」；
> 歷史決策在 `DEVLOG.md`；更早版本的交接內容由 git 歷史保存，本檔只寫現況。

---

## 0. 一句話現況

**B1–B6 物理鏈全部 Done，六場物理戰役收官；驗證鏈從 MIDI 到耳朵全線閉環；
第一首授權全淨的商品曲（給愛麗絲）已產出。工作樹乾淨，全部已 commit + push。**

**UI mockup 裁決已於 2026-08-30 下達：雙開門被否決，UI 改走「功能規格 → 設計端重做」**
（見 §5 第 1 項）。同日月月明示授權，分支已全數 merge → `main` 並 push。

## 1. 立刻要知道的三件事

1. **`main` 與分支已同步（2026-08-30，月月明示授權 commit+push+merge）。**
   merge commit `64afb49`，帶入 `88bdfac`(B5+B6P1)→`0f271ae`(三件套)→`51bd6cc`(B6 收官)
   →`76c41c4`(文件收尾)→`313acaa`(UI 裁決落地+影片霓虹配色)；
   `git diff main fix/deep-physics-audit-20260716` 為空（兩邊樹完全相同）。
   分支仍保留為工作branch。**R7 照舊：往後沒有月月明示就不 commit / 不 push。**
2. **corpus 從 73 檔變成 75 檔**（新增給愛麗絲 piano/cimbalom 兩版）。任何文件寫 73 都是舊的。
   最新全綠證據：`reports/gate_outputs/b6_corpus_phase34.txt`（75/75，1 筆既有 moonlight 豁免）。
3. **月月是聾人開發者，全程免耳驗收。** 任何「聽起來如何」的主張都不算數；
   物理/位置正確性由 GATE 鏈負責，美學驗收由月月安排外部專業人士。這是本專案的根本設定。

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

## 5. 接下來該做什麼（優先序）

1. **UI 裁決已下（2026-08-30）：雙開門提案被月月否決。**
   原話：「左側那麼寬了但旋鈕超小；右側一點也沒有鋼琴／揚琴／空靈鼓的視覺感，
   看上去像廉價玩具」。裁定**撇開現行 UI 的所有既有元素**，改由設計端（Claude Design）
   從功能重新設計。`uiux/double_door_mockup.html` 與
   `docs/uiux/DOUBLE_DOOR_PROPOSAL.zh-TW.md` 就此**作廢，只留歷史**。
   → 新的設計輸入文件：**`docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md`**（2026-08-30 建立）
   ——只清點功能（60 個 APVTS 參數＋非參數控制項＋六條使用情境＋八條硬性約束），
   **刻意不寫任何顏色／尺寸／佈局**。資料全部從程式碼本體清點，不是從舊文件轉抄。
   **下一步待月月決定**：(a) 這份 spec 是否可以送出去設計；
   (b) merge → `main` 的時機（原本綁在 UI 裁決上，現在 UI 走向重設計，
   分支上的物理成果不該再被 UI 卡住——但仍**不自作主張 merge**，等月月明示）。
   **兩個誠實揭露照舊有效**：(a) 樂器模擬畫面**從來沒做過**，不是復活是全新功能；
   (b)「揚琴左右手強弱」在 APVTS 裡**沒有對應參數**，要落地得另開卡加參數與 DSP。
2. **換源重製排程**（月月 2026-08-28 裁決「CC BY 可以」）——
   計畫在 `reports/decision_packets/CLASSICAL_RELICENSE_PLAN.md`：
   月光 4 檔（CC BY-SA 2.5）+ 四季 12 樂章（CC BY-SA 3.0）授權不淨，**換源前不上架**；
   給愛麗絲已完成（真 PD）。四季可換 IMSLP Schoonenbeek CC BY（但編制不同）、
   月光需從譜面重轉譜。轉譜器已泛化（`tools/midi_to_tsukisynth.py convert` 子命令），
   four-seasons 舊路徑零改變已用位元比對證明。
3. **B7（第一原理力鏈，方案 C）**——卡已立 `docs/workcards/B7.md`。
   **前置硬性阻擋已解除**（B6 方案 B 已落地=B7 的地基）。
   開工前要補 Phase 0 三塊資料，最關鍵的缺口：**MIDI velocity（0-1 proxy）→ 真實槌速 m/s
   的映射函數查無出處**（已知真實槌速範圍 0.11–6.83 m/s，Boutillon 實測／Askenfelt KTH 講義）。
4. **D8 tongue_drum 引擎缺陷**（商品線的擋路石）——同 velocity 下有 **40.3 dB 音高-響度斜率**
   （MIDI 37→87：−32.8→−73.1 dBFS；cimbalom 同域僅 4.4 dB），且輸出近純正弦無泛音列。
   後果：空靈鼓獨奏商品不可用。屬引擎物理層調查，改動觸發 Rule 10。
5. **IR 配套修補**（`docs/IR_REVERB_AUDIT.zh-TW.md` 已出結論）——
   卷積實作本身**正統無誤**（juce::dsp::Convolution，IR 模式取代演算法 reverb）。
   但有一個 **bug 級落差：IR 路徑進 DAW session state 卻沒進使用者 preset**，
   存了 IR 模式的 preset 重載會靜默退回演算法殘響；另有 ALGO↔IR 切換 0.15× 增益跳變、
   `.wav`/`.json` 共用同一顆 Load 鈕造成心智模型混淆。三個選項與工程量在該文件 §4。
6. **音效產品線**（月月：不一定要完整樂曲，但要有判準）——
   `docs/SOUND_DESIGN_KNOWLEDGE.zh-TW.md` 已建（9 個一手來源含《The Sound Effects Bible》全文、
   6 個可寫成 Python 檢查器的量測判準）。開工前必讀，不得再盲做「10 秒兩聲鐘響」。

## 6. 檔案地圖

| 要找什麼 | 去哪 |
|---|---|
| 當前待辦 | `TODO.md` 開頭「待辦總表」（X/A/B/C/D 分段） |
| 驗收規則、Milestone、容差表 | `ROADMAP_PHYSICS.md` §1 / §2 / §6 |
| 免耳驗證設計 + 主張域 | `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §7 |
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
