# WF0907 共同規約（所有 WF0907_* 施工卡的前提，先讀完再開卡）

> 建立：2026-09-07　規劃者：Claude（主 session）　工兵：Sonnet　稽核：Opus
> 月月 2026-09-07 裁決：可開工的工程項 + 只做了骨架的部分，以 Workflow 發包。

## 0. 這個專案是什麼（30 秒版）

聾人開發者月月 + AI，不靠聽感、靠物理理論精確模擬聲音的 JUCE 8 VST3 合成器。
**任何「聽起來如何」的主張都不算數**；驗收只認 GATE 命令的輸出（Rule 1）。
完整規則在 `ROADMAP_PHYSICS.md` §1，最常踩的十條：

| Rule | 內容 |
|---|---|
| R1 | 驗收只認 GATE 命令輸出，不認敘述 |
| R2 | **禁止調寬任何容差、禁止自訂新容差**。達不到 → 回報數字 + 停下 |
| R3 | 禁止縮小 GATE 範圍（例如把會 FAIL 的檔案從 corpus 拿掉） |
| R4 | 禁止 hardcode 無法溯源的物理常數；查不到就誠實標「未溯源」 |
| R5 | 卡不可部分標記 Done |
| R6 | 改 `src/physics|engines|dsp|score` 後必跑 `--full` + 三 target build |
| R7 | **絕對不 `git commit` / `git push` / `git checkout` / `git stash` / `git reset`** |
| R10 | 任何讓既有 score 渲染結果改變的修正，**停下**寫前後對照報告，不得自行落地 |

## 1. 路徑與環境

- Repo 根目錄：`C:\Users\admin\Desktop\Claude\tsuki-synth`（所有命令先 `cd` 到這裡；工作 branch `fix/deep-physics-audit-20260716`）
- Python：`python`（3.12；numpy/scipy/mido/pytest/jsonschema 已裝）
- ffmpeg：`C:\Users\admin\Desktop\Tools\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe`
- 現成 binary（**Python lane 與研究 lane 用這個，不要重建**）：
  - CLI：`build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe`（2026-08-31 建，對應 HEAD `cdf2017`）
  - HostProbe：`build\Release\TsukiSynthHostProbe.exe`
  - VST3：`build\TsukiSynth_artefacts\Release\VST3\TsukiSynth.vst3`
- **C++ lane 專用建置目錄 `build-wf\`**（已被 `.gitignore` 的 `build-*/` 涵蓋）：
  ```
  cmake -B build-wf -DCMAKE_BUILD_TYPE=Release -DTSUKI_BUILD_TESTS=ON
  cmake --build build-wf --config Release --target TsukiSynthCLI TsukiSynth_Standalone TsukiSynth_VST3
  cmake --build build-wf --config Release --target TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest TsukiSynthSpectrumViewTest TsukiSynthHostProbe
  ctest --test-dir build-wf -C Release --output-on-failure
  ```
  **X4 規約**：跑 `ctest` 前必先重建三個測試 target，否則測到舊 binary。
  C++ lane 的 Python GATE 一律加 `--cli build-wf\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe`
  （`verify_score.py`、`physics_verify.py` 都支援 `--cli`）。
  **理由**：Python lane 同時在用 `build\` 的 exe，兩邊不能互相覆蓋。
- **一般卡絕對不要對 `build\` 跑 cmake**（Python lane 依賴它穩定）。**唯一例外：整合卡**（所有 lane 結束後由整合工兵重建 `build\` 跑全套 GATE）。
- **位元不變基準檔**：2026-09-09 WF0909-D8（月月裁決 wood_mallet）之前用 `reports/gate_outputs/b6_method/sha256_before.txt`；D8 落地後改用 `sha256_before_post_d8.txt`（兩首月光空靈鼓相關曲目改變，其餘 6 首不變）。
  2026-09-10 A14 B-2 放行後改用 `sha256_before_post_a14.txt`（`physical_piano` 改變）。
- 暫存輸出一律放 `output\wf0907\<卡號>\`（已 gitignore）；證據檔放 `reports\gate_outputs\wf0907_<卡號>_*.txt`（要進版控）。
- 三個 lane 同時在同一個工作樹作業：**只碰你這張卡列出的檔案**。發現需要改別的檔案 → 記進 `open_items` 回報，不要動。

## 2. 交付與稽核流程

1. 工兵（Sonnet）照卡施工，跑完卡上全部 GATE，把每條 GATE 的**完整命令與輸出**存進證據檔。
2. 工兵最後回報（結構化）：`status`（DONE / BLOCKED / RED）、`files_touched`、`gate_results`、`evidence_paths`、`open_items`。
   - **BLOCKED** = 需要月月裁決或發現 R10 觸發（渲染輸出改變）→ 停下，不落地。
   - **RED** = GATE 過不了且不能靠調容差/縮範圍解 → 回報數字。
   - **不要自報 PASS 但沒附命令輸出**——稽核會親自重跑。
3. 稽核（Opus）**不採信工兵自報**：親自 `git diff -- <files_touched>`、親自重跑每條 GATE、親自開證據檔比對。
   回報 `verdict`（PASS / FAIL）+ `findings`（file:line + 主張 + 你親眼看到的證據）。
   **PASS 時稽核執行 `git add -- <files_touched>`**（staged = 稽核通過，未 commit；月月最後看 `git diff --cached`）。
4. FAIL → 工兵拿 findings 修一輪 → 稽核再驗一次。第二次仍 FAIL → 卡標 RED，不 stage，留給月月。

## 3. 每張卡都適用的硬性檢查

- **位元不變證明**（凡是碰到 `src/` 的卡）：`reports/gate_outputs/b6_method/render_b6_scores.py` 會渲染 8 首代表曲並比 SHA256
  （baseline 在 `reports/gate_outputs/b6_method/sha256_before.txt`，最新 8/8 一致的記錄在 `b6_bit_identity_phase34.txt`）。
  若該腳本不接受 `--cli` 參數，複製一份到 `reports/gate_outputs/wf0907_method/render_wf_scores.py` 加上 `--cli`，指向 `build-wf` 的 exe。
  **8/8 IDENTICAL 才算過**；任何一首 SHA 變了 = R10 觸發 = BLOCKED。
  **2026-09-09 起位元不變基準改用 `sha256_before_post_d8.txt`（D8 月月裁決 `wood_mallet` 落地，WF0909-D8）**：
  8 首中的 `moonlight_sonata_movement1_tongue_drum` 與 `moonlight_sonata_movement1_yangqin_tongue_mix` 兩首因該卡
  改了 score 裡 tongue_drum 事件的 `exciter`（`finger` → `wood_mallet`）而 SHA 改變，屬預期落地、非 R10 意外觸發；
  其餘 6 首逐位元不變。舊基準 `sha256_before.txt` 保留存檔，新卡一律比對 `sha256_before_post_d8.txt`
  （8/8 IDENTICAL 的判定標準不變，只是比對對象換了）。詳見 `reports/d8_tongue_drum_exciter_before_after.md` §9。
  **2026-09-10 A14 B-2 放行後改用 `sha256_before_post_a14.txt`（physical_piano 改變）**：
  8 首中只有 `physical_piano` 因 `HammerImpulse::pianoHammerTauC()` 音高律錨定到 `keytrackScale()`
  而 SHA 改變（`reports/a14_tauc_keytrack_before_after.md`），屬預期落地、非 R10 意外觸發；其餘 7 首逐位元不變。
  舊基準 `sha256_before_post_d8.txt` 保留存檔，新卡一律比對 `sha256_before_post_a14.txt`（7/8 vs 8/8：判定標準不變，只是比對對象與相同項目數換了）。
- `python -m pytest tests -q` 全綠（現況 213 collected）。
- 不新增任何未溯源常數；不動 `scores/crossplatform_tolerance.json`、`ROADMAP_PHYSICS.md` §6、`tools/` 內既有容差數字。
- 程式碼註解與文件用繁體中文或英文皆可，但**不得宣稱未量測的東西**（例：不可寫「泛音已驗證」）。

## 4. 卡片索引

| 卡 | lane | 工兵 | 摘要 |
|---|---|---|---|
| E1 | Python | Sonnet | requirements 加 pytest+mido、新測試檔接進 CI |
| C10 | Python | Sonnet | 量測器合成哨兵（≤1 cent 自證） |
| C11 | Python | Sonnet | stem_verify 逐顆拒答理由 |
| C12 | Python | Sonnet | stem_verify `--analysis-dry` + hash/diff 進 JSON |
| E5 | C++ | Sonnet | `getTailLengthSeconds()` 接引擎自報尾音 + Custom 判斷式單一化 |
| E8 | C++ | Sonnet | score 合法性三份契約同步（schema ↔ C++ `--validate` ↔ converter） |
| E9 | C++ | Sonnet | `--dump-modes` 支援 layered score |
| E7 | C++ | Sonnet | K-03 超過 maxBlock 的分塊處理 + K-02 wet 增益差量化 |
| E10 | C++ | Sonnet | HostProbe 加變動 block size（H6）與 user preset round-trip（H7） |
| R1 | 研究 | Opus | A13 partial GATE 主張域：外部證據 + 建議 |
| R2 | 研究 | Opus | A14 高音弱基頻：文獻 + 引擎數字對照 + 判定 |
| R3 | 研究 | Opus | F-03 IR preset：業界作法 + 社群抱怨 + 建議 |
| R4 | 研究 | Opus | B7 Phase 0：velocity→槌速映射、鋼琴 SPL 範圍溯源 |
| R5 | 研究 | Opus | A8 外部資料集下載 + SHA256 + 首批對照數字 |
| R6 | 研究 | Opus | D8 tongue_drum 40 dB 斜率 + 缺泛音 根因診斷 |

lane 內順序：Python = E1 → C10 → C11 → C12；C++ = E5 → E8 → E9 → E7 → E10；研究六張平行。

## WF0925 後更新（2026-09-25，WF0925b-DS 附加；上方原文是 WF0907 輪當時的規約，未改）

- **HostProbe 不再依賴 cwd**：WF0925-K2 之後，HostProbe 找 `data/materials.json` 的順序是 cwd → 環境變數 `TSUKI_REPO_ROOT` → exe 所在資料夾一路往上，用了哪條會印出來；exe 複製到 repo 外、又沒設環境變數時，會大聲出現 4 個 H8 FAIL（不靜默跳過）。證據 `reports/gate_outputs/wf0925_K2_hostprobe.txt`。
- **新基線**：pytest **288 個測試＝282 passed＋1 skipped＋5 xfailed**（上方 §3 寫的「現況 213 collected」是 WF0907 當時的數字）；HostProbe **215 PASS／0 FAIL**；AuditTest 110 PASS。證據 `reports/gate_outputs/wf0925_INTEGRATION.txt`、`reports/gate_outputs/wf0925_integration_raw/05_pytest.txt`、`09_hostprobe_cwd_repo.txt`。
- **本機 Python 是 3.13.3**（上方 §1 寫 3.12；CI 固定 3.12.8）。WF0925 輪所有 Python GATE 都在 3.13.3 上跑。
- **位元不變比對**：基準早已不是上方 §3 的 `sha256_before.txt`／`sha256_before_post_d8.txt`，自 A14（2026-09-10）起是 `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`，期望 8/8 IDENTICAL。比對腳本 `reports/gate_outputs/wf0907_method/render_wf_scores.py` 的用法：`--workdir` 必須在 repo 外（腳本會拒絕 repo 內路徑）；`--cli` 用 Windows 絕對路徑（相對路徑會 WinError 2）；WF0925-P1 加了 `--outdir`，把 csv／sha256 寫到指定資料夾（不帶時照舊寫進 `reports/gate_outputs/wf0907_method/`）；跟基準比對用 `diff --strip-trailing-cr`（基準檔是 CRLF）。
- 細節與其他差異見 `docs/workcards/WF0925_README.md` §0。

---

## 2026-10-03 更新註記（文件卡 DOC-B；上面原文是當時的紀錄，不改）

- 上方的 pytest 288／307、HostProbe 215、AuditTest 110、`--selftest` 13 等基線都已過時。新基線（`reports/gate_outputs/wf1002b_INTEGRATION.txt`）：ctest 4/4（AuditTest 111）、pytest **310**（304 passed＋1 skip＋5 xfail）、`--full` NO CHECKED FAILURES、`--selftest` **14/14**（WF1002b 換窗後多 1 項）、`verify_score --all` 75/75、位元不變 8/8、HostProbe **231**／0、pluginval＋validator 47/47。
- git：分支已 push 到 `168688e`（2026-10-03），`main` 仍 `3f9b90a`、未 merge；R7 已於 2026-10-02 依月月裁決 Q03=A 改字面（稽核 PASS 後 staged 供審）。
- repo 已搬到 `E:\Tsuki-project\tsuki-synth`（2026-09-30）；上方提到的 C 槽路徑是搬家前的位置。
- 之後各輪的裁定與結果見 `docs/workcards/WF1002_README.md`（§1 裁定表、§3 WF1002、§4 WF1002b）。
