# WF0925 共同規約與本輪結果（卡片清單、範圍、各卡結果、證據路徑、稽核判定）

> 建立：2026-09-25（交接卡 WF0925-HO）　流程：規劃者 → 工兵 → 稽核（親自重跑，不採信工兵自報），同 WF0914。
> 月月 2026-09-25 裁決：「剩下 AI 能處理的都處理掉」。本輪的輸入是 09-25 現況盤點
> `reports/status_check_2026-09-25/STATUS_CHECK.zh-TW.md`（結論）與 `APPENDIX_findings.zh-TW.md`（128 條逐條證據；有「查證修正」的條目以修正後為準）。
> 本檔只寫與 `WF0914_README.md`、`WF0907_README.md` **不同**的地方，加上本輪逐卡結果；十條 Rule、lane 隔離、交付與稽核流程全部沿用那兩份。
> 本輪的施工卡原文是 workflow 腳本直接派給工兵的，**沒有存成 `docs/workcards/WF0925_*.md` 檔**；每張卡做了什麼，以本檔 §2 和各卡證據檔的 summary 為準。
> 本檔的數字都是交接卡從證據檔親自核對過的（不是照抄回報）；核對不到的會寫「查不到」。
> **同日的 WF0925b 收尾輪（TF／DS／BR／XF／INT2／HO2）寫在 §7**；§0、§3、§4、§6 裡標「WF0925b」的句子是收尾輪交接卡補的註記，其餘原文不動。

## 0. 本輪與 WF0914 輪的差異

| 項 | WF0914 輪 | 本輪 WF0925 |
|---|---|---|
| 位元不變基準 | `reports/gate_outputs/b6_method/sha256_before_post_a14.txt`，期望 8/8 | **相同**。本輪沒有任何卡被授權改渲染輸出；每條 lane 與整合卡都是 **8/8 IDENTICAL**，R10 沒觸發 |
| pytest 基線 | 270 個測試＝264 passed＋1 skip＋5 xfail | **288 個測試＝282 passed＋1 skip＋5 xfail**（整合卡 `wf0925_integration_raw/05_pytest.txt`）。新增 18 條全部來自 P1：`test_measurement_selfcal.py::test_holdout_grid_pins_match_record` 1 條＋新檔 `tests/test_stem_stream.py` 17 條；刪除 0 條（`05a_pytest_collect_diff.txt`）。**WF0925b 之後是 307 個測試＝301 passed＋1 skip＋5 xfail**（+19 全來自 WF0925b-TF：stem_stream +12、stem_verify +7；刪除 0；`wf0925b_integration_raw/02_pytest.txt`，見 §7-4） |
| HostProbe | 89 PASS | **215 PASS／0 FAIL**：K1 加 17 條（E14 state_version、D12 舊鍵清除等）→ 106；K2 加 109 條（E16：27 個工廠 preset×4＋1 條負對照）→ 215 |
| AuditTest（`audit_repro`） | 09-25 盤點時 97 條 PASS | **110 條 PASS**：K1 加 12 條（E15 SHA-256 已知答案與損壞修復）→ 109；K2 加 1 條 D9c-guard → 110 |
| HostProbe 工作目錄 | **必須**在 repo 根目錄跑（H8 用 cwd 找 `data/materials.json`） | **K2 之後不必**：找法是 cwd → 環境變數 `TSUKI_REPO_ROOT` → exe 所在資料夾一路往上；用了哪條會印出來。exe 複製到 repo 外、又沒設環境變數時，仍會出現 4 個 H8 FAIL（大聲失敗，不會靜默跳過）。**WF0925 共同規約那條「必須以 repo 根目錄為 cwd」已經不成立** |
| `render_wf_scores.py` | 沒有 `--outdir`，csv/sha256 寫進 `wf0907_method/` | P1 加了 `--outdir`（不帶時行為跟以前一樣）。另外三個實務細節：`--workdir` 要放 repo 外（腳本會拒絕 repo 內路徑）、`--cli` 要用 Windows 絕對路徑（相對路徑會 WinError 2）、跟基準比對要用 `diff --strip-trailing-cr`（基準檔是 CRLF）。**WF0925b-TF 之後 `--cli` 相對路徑也可以**（腳本先轉成絕對路徑並印出來；INT2 用相對路徑跑 8/8）；改成要注意 **`--workdir` 路徑要短**：CLI 的輸出路徑約 247 字元以上會超過 Windows 260 字元上限，CLI 寫不出 render manifest、exit 1（TF 與 BR 各碰到一次） |
| 暫存輸出／證據檔 | `output\wf0914\<卡號>\`／`wf0914_<卡號>_*.txt` | `output\wf0925\<卡號>\`（gitignored）／`reports\gate_outputs\wf0925_<卡號>_*.txt`（進版控） |
| 現成 binary | `build\` 對應 09-10 build | Python lane、研究 lane、商品 lane 用 `build\` 09-15 的 CLI（sha256 `9123db8f…`，就是 clean_batch2 商品母帶的渲染器），一律先複製到自己的 output 目錄再用。C++ lane 用 `build-wf\`。**整合卡 10:39 重建 `build\` 之後，`build\` 的 CLI 變成 `b84c775b…`**；`9123db8f` 那支現在只剩 `exports/renderer_archive/TsukiSynthCLI_9123db8f_build20260915.exe`（gitignored）和 `output/wf0925/{N1,V1,R_audit}/cli.exe` 的複本。**WF0925b 時已在 repo 外多放一份**：`E:\TsukiSynth_renderer_archive\`（裁決包 O15；交接卡核對 sha256 相同，見 §7-7） |
| Python | 規約寫 3.12 | 本機實際是 **3.13.3**（CI 固定 3.12.8）；本輪所有 Python GATE 都在 3.13.3 上跑、數字都有重現核對 |
| 中斷 | — | 本輪途中碰到 session 用量上限。V1、L1、G1 由接手工兵先核對前任留下的產出（雜湊、引文、輸出）再續做；整合卡中斷時還沒產出，恢復後從第 1 步重跑。WF0925b 又碰到一次：XF、TF 由接手工兵核對前任產出後續做，INT2 中斷時沒有產出、恢復後從第 1 步重跑 |

## 1. lane 配置與順序

| lane | 卡 | 建置目錄 | 稽核 | 稽核判定 |
|---|---|---|---|---|
| C++ | K1 → K2 → K1K2fix（修正輪） | `build-wf\` | K 稽核，兩輪 | 第 1 輪標 1 條 severity=fix（K1 的 GATE 4 證據不實，見 §2 K1K2fix）→ 修正 → **第 2 輪 PASS**，stage 34 檔 |
| Python／CI | P1 | 用 `build\` 09-15 CLI 的複本 | P1 稽核 | **PASS**，stage 15 檔 |
| 研究 | N1、F5、V1、L1、G1（平行） | 不建置主 repo（F5 在 `git archive HEAD` 的隔離副本建 CLI） | R 稽核 | **五張全 PASS**，stage 75 檔 |
| 商品 | X1（音訊）→ X2（文字與包裝） | 不建置；只動 `exports/`（gitignored）和自己的證據檔 | X 稽核 | **FAIL**（1 條要修），沒 stage 任何檔；本輪沒有跑修正輪（→ **WF0925b-XF 修正，複驗 PASS**，24 檔已 stage，見 §7） |
| 規劃 | Q1（彙總裁決包） | — | — | 產出 `reports/decision_packets/WF0925_open_decisions.zh-TW.md`，由交接卡 stage |
| 整合 | INT（最後） | 唯一重建 `build\` 的卡 | — | 10 條 GATE 全綠，stage 自己的 24 檔 |
| 交接 | HO | — | — | 本檔＋HANDOVER／TODO／DEVLOG／README，連同 Q1 裁決包 stage |

## 2. 各卡結果

### C++ lane（`build-wf\`）

| 卡 | 做了什麼（白話） | 關鍵數字 | 證據 |
|---|---|---|---|
| **K1** | E8：揚琴每按一個音在音訊執行緒建一次 `juce::String` 的問題改掉（改成 `CimbalomEngine.h` 的 static 常數）；E9：`getTailLengthSeconds()` 改讀 20 Hz Timer 在訊息執行緒算好的 atomic 值；E14：plugin state 寫 `state_version=3`、preset 讀 version（比 2 新的照樣載入但拒絕覆寫）；D12：情境 1、2 加「輸出 state 不含 `reverb_ir_path`」斷言；E15：IR 匯入時庫檔雜湊不符就寫暫存檔、驗雜湊、原子替換，ctest 加 SHA-256 已知答案 3 組＋損壞修復情境；註解同步（HammerImpulse.h B7 殘留三處、PlateModel.h 檔頭 D13 主張域、`water_gong_free` 的 description、EffectChain.h D9c 對齊參考、D9 裁決包檔尾） | HostProbe 89→106、AuditTest 97→109、H8 四個 tail 值改前改後逐字相同（34.4814／178.734／319.848／178.734 s）、8/8 | `reports/gate_outputs/wf0925_K1_*.txt`（6 檔）。**注意**：K1 的 GATE 4 原始 log 是 `--cli` 後面空白、`find_cli` 選到 `build\` 的舊 CLI（`9123db8f`），沒測到 K1 的程式碼；有效的 GATE 4 看 K2、K1K2fix 或 K 稽核第 2 輪 |
| **K2** | HostProbe 找 `materials.json` 改成 cwd → `TSUKI_REPO_ROOT` → exe 往上找（盤點 live-gate 發現 2）；D9c-guard：`audit_repro` 加 `kIrWetMakeupGain == 26.9f` 精確相等 CHECK（沒加 0.25 dB 那條，留給裁決包 Q01）；E15 出處：fetch FIPS 180-2 核對 "abc"（附錄 B.1）、448 位元訊息（B.2），空字串那組原文沒有、只有 hashlib；E16：HostProbe 逐一檢查 27 個工廠 preset（paramID 都解析得到、名稱對得上、C4 渲染 192,512 個樣本全是有限值），峰值與 RMS 只印不判 | HostProbe 215／0、AuditTest 110、D9c-guard 讀到 26.8999996、K-02 = 0.112 dB（只印數字）、8/8 | `wf0925_K2_*.txt`（8 檔） |
| **K1K2fix** | 稽核第 1 輪唯一一條 fix：把 K1 的 GATE 4 證據檔照實更正（檔頭加 8 行說明，log 本體一個位元組都沒動），`wf0925_K1_summary.txt` 補 5 行更正；用 `build-wf` 重跑六條 GATE | 六條 GATE 全過；GATE 4 這次 75 份 manifest 的 renderer 都是本輪重編的 CLI；8/8 | `wf0925_K1K2fix_*.txt`（7 檔） |
| **K 稽核** | 第 1 輪做 11 個 mutation（M1–M11）逐一 FAIL；第 2 輪在 `build-wf` 重跑整套 GATE、從 repo 外親跑 HostProbe（cwd 在外 0 failures；exe 複本不設環境變數 → 正好 4 個 H8 FAIL）、E8 實測（把插件 DLL 的 malloc/calloc/realloc 入口換成計數器：5 種引擎情境 × 8 個 note-on 全部 0 次；負對照每個 note-on 1 次）、E16 塞 NaN 的 mutation 正好 1 條 FAIL | **PASS**；9 條 note 級 finding（E8 實測不是 repo GATE、E14 邊角、E15 `replaceFileIn` 極少數失敗情況、D9c 註解 +28.58 vs 20·log10(26.9)=28.595 dB、HostProbe cwd 規約過時等） | `output/wf0925/K_audit/`、`K_audit2/`（gitignored） |

### Python／CI lane

| 卡 | 做了什麼 | 關鍵數字 | 證據 |
|---|---|---|---|
| **P1** | `release-physics.yml`：建置清單補 `TsukiSynthSpectrumViewTest`、`TsukiSynthHostProbe`，`unittest discover` 改 `python -m pytest tests -q`，加 HostProbe 執行步驟與 log 上傳；`physics.yml` Windows job 加 HostProbe 建置、執行與 log 上傳；D15 的三個釘住數字（5.2304／1.0840／7.2055）搬到非 xfail 測試（沿用既有 <5e-4 比較精度，不是新容差）；`render_wf_scores.py` 加 `--outdir`；`melody_roll_video.py` 找 ffmpeg 順序改 `--ffmpeg` > `TSUKI_FFMPEG` > PATH > 原寫死路徑；`physics_verify.py`／`verify_score.py` 的 `find_cli` 改成優先挑 Release、不看 mtime，並印出選到的路徑；新增 `tests/test_stem_stream.py`（17 個測試，5 種突變全抓到）；`partial_verify.py` 的 `gate_ready` 理由字串更新 | pytest 收集 270→288；selfcal 8 passed＋5 xfailed；相關測試 179 passed＋1 skipped；8/8 | `wf0925_P1_gate1`～`gate6_*.txt`（6 檔） |
| **P1 稽核** | 6 條 GATE 全部親自重跑；D15 反例（pin 改 0.001 → 3 條都紅）；`--outdir` 預設行為動態驗證 | **PASS**。另查到 1 條 severity=fix 的**既有**問題（不是 P1 造成）：GitHub Windows runner 的 pwsh 多行 `run:` 只看最後一個指令的 exit code，`release-physics.yml:54-57` 的 ctest／pytest、`physics.yml:99-100` 的 pytest 失敗都會被後面的指令蓋掉 → 裁決包 **Q12** | `output/wf0925/P1_audit/`（含 `pwsh_mask_sim.txt`） |

### 研究 lane（不改 `src/`、`tools/`、`tests/`）

| 卡 | 做了什麼 | 關鍵數字 | 證據 |
|---|---|---|---|
| **N1**（D16 零點地圖） | 用 `--dump-modes` 掃 piano／cimbalom felt／cimbalom wood／string bow 四種激發 × MIDI 21–108 × 力度，共 27,808 格；理論（x=2·f·τc 的半正弦脈衝頻譜）與 dump 對照；給愛麗絲 149 顆 stem 用現行 binary 重渲；全 corpus 75 份掃描 | 16 顆 FAIL **16/16** 在凹口內（−14.9～−24.5 dB）；PASS 裡另有 31 顆也在凹口內（凹口是必要、不是充分條件）；真正分開 PASS／FAIL 的是基頻絕對位準：FAIL ≤ −72.1、PASS ≥ −67.2 dBFS，對既有 −70 dBFS 門檻 677／16 零誤判（樣本內）；凹口內事件數 A14 前 44 顆、現在 47 顆（洞沒變少，換了位置）；商品只有給愛麗絲鋼琴版受影響（47 顆在凹口內，16 顆 FAIL）。所有 −10 dB 分界標「描述用、非 GATE」 | `reports/weak_fundamental_null_map_2026-09-25.zh-TW.md`、`reports/weak_fundamental_null_map/`（24 檔）、`wf0925_N1_*.txt`（6 檔） |
| **F5**（D11-F5 根因） | 在 `git archive HEAD` 的隔離副本套 D11 patch 建 CLI，拆解 F5 piano 殘餘能量退化 | −63.9 → −58.5 dB **全部**來自 C4 基頻 T60 變短（4.1425 → 2.6733 s）：琴橋損耗 ∝ 弦徑²×弦長，候選把 C4 換成 1.00 mm／0.639 m，琴橋損耗 1.70 倍；衰減越快，基頻譜線裙邊漏出 ±3% 帶外越多。只換頻率、只換振幅都是 0.00 dB 變化。**新事實**：現行引擎不套候選，只把 F5 探針弦徑 0.8 mm 改成 1.0 mm 就是 −59.5 dB FAIL | `reports/d11_f5_root_cause_2026-09-25.zh-TW.md`、D11 裁決包檔尾（原文 65 行未改，加 35 行）、`wf0925_F5_*.txt`（6 檔） |
| **V1**（partial 全量＋voice pool） | partial_verify 第一次跑全曲 905 顆（informational）；外掛 16 voice 搶音照程式碼規則推算（不是外掛實測） | stem_verify 677／16／212，跟 09-14 D14 逐顆相同；partial：5,428 格中 PASS 4577／FAIL 849／UNVERIFIED 2，848 條 FAIL 偏高（中位 +5.53 c）——主因是工具以「第 0 根弦」為期望值，三弦平均高約 +5.0 c；D16 那 16 顆用泛音反推基頻 16/16 PASS。voice pool：正常彈法 50 件商品 0 件超過 16 顆（給愛麗絲最多 12）；75 首 corpus 3 首超過（都不是商品：月光全曲 FM 196、月光舌鼓 20、混合版舌鼓部分 20）；假設全程踩延音踏板，4 件商品超過（給愛麗絲兩版 22）；CPU 一顆 Cimbalom voice 約 1.37～2.71% 單核 | `reports/partial_verify_full_2026-09-25.zh-TW.md`、`reports/voice_pool_occupancy_2026-09-25.zh-TW.md`、`reports/wf0925_method/`（12 支腳本）、`wf0925_V1_*.txt`（11 檔） |
| **L1**（D1／D4／D6 文獻） | 梁／板阻尼文獻補搜，只引自己 fetch 到全文的來源 | 拿到 8 份全文＋Euphonics 三頁＋Wood Handbook；引文 71/71 逐字核對、反向核對 56 條命中 0 MISS。結論：文獻**反對**把 BeamModel `*2` 當物理機制，但**無法判斷**它代表的總量該不該留；另發現模型衰減完全不看舌片厚度（出貨樂譜 2.0／2.6／3.2 mm，文獻熱彈性差 2.56 倍、模型差 0）。D6（Wood Handbook Table 5–15，PDF 第 5–36 頁）已取得並逐字轉錄；D4 舌鼓 ICSV27 全文試了 15 條路徑仍拿不到 | `docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md`、`wf0925_L1_sources.txt` |
| **G1**（發行與授權文件） | `THIRD_PARTY_NOTICES.txt` v2（12 個元件＋PreSonus 擴充 3b，含 VST3 SDK MIT、SheenBidi Apache 2.0、IBM Plex SIL OFL 1.1 全文）；`LICENSE` 第 1–19 行條款不動，只改第三方段落（JUCE Starter 描述、「registered trademark」）；`docs/legal/JUCE8_LICENSE_REVIEW.zh-TW.md`；買家 EULA 草稿 `docs/legal/EULA_BUYER_DRAFT.md`（空格 E1–E9 待填）；安裝包腳本 `tools/installer/TsukiSynth.iss`＋README（**從沒編譯過**：本機沒有 Inno Setup）；`docs/KNOWN_LIMITS_INDEX.zh-TW.md`（已裁決限制 26 條、已知缺口 15 條、待裁升格候選 9 條）；兩封信的狀態行改「已寄出（09-15），等回覆」 | 授權全文逐字核對 `ALL VERBATIM: True`；元件確實編進 binary（字串掃描）；3 項待確認：json.h 上游版本、libogg 版本、IBM Plex 是哪個 release | `wf0925_G1_sources.txt` |
| **R 稽核** | 五張卡各自親自重跑／重抓：N1 重跑 4 格 `--dump-modes` 到小數 4 位相同；F5 自己不用 junction 另建 patch 版 CLI，wav 雜湊跟 F5 相同；V1 自寫 voice 需求模擬（給愛麗絲 12／12／22、月光舌鼓 20）；L1 自己重抓 6 份來源、雜湊全同；G1 自己重抓 JUCE 8 EULA 與 IBM Plex LICENSE | **五張全 PASS**；11 條 note（N1 資料夾 7.0 MB、voice pool 報告一處行號引用範圍不精確、安裝腳本沒編譯過、證據檔含本機路徑等） | `output/wf0925/R_audit/`（含 `AUDIT_LOG.txt`、`stage_list.txt`） |

### 商品 lane（`exports/`，gitignored；原始 `clean_batch2/` 212 檔 sha256 開工前後相同）

| 卡 | 做了什麼 | 關鍵數字 | 證據 |
|---|---|---|---|
| **X1**（音訊） | 產出都在 `exports/products/clean_batch2_v1_1_candidate/`：loop-ready 6 檔（裁到整小節、尾巴疊回開頭）；音效響度 B 案 43 檔（最大瞬時響度 −10 LUFS、≤ −1 dBTP）；音樂 7 軌 TPDF dither 版；試聽帶 6:03.560；商品圖 7 張；`QA_REPORT.md` | loop 長度誤差 0 樣本 ×6；B 案 21 檔撞到 −1 dBTP 上限，響度差距 23.0 → 18.3 LU；原鏈重出 7/7 sha256 相同再加 dither；試聽帶單一線性增益 −0.206 dB 到 −14.000 LUFS；範圍外發現：現行 distribution 有 4 個音效全精度真峰值略高於 −1.000 dBTP、樂章 2 標題前後不一致 | `wf0925_X1_*.txt`（9 檔，**untracked**） |
| **X2**（文字與包裝） | `PRODUCT_SHEET_v1_1.md`（「41 個削波樣本」改正為正規化前計數）、`LISTING_COPY_v1_1.md`（材料照 score 改正、阻尼措辭、VST 商標）、`catalog_v1_1`（欄位改名、loop-ready 欄）、三語 README、`LICENSE_SE_PACK_v1_1.txt` 草稿、Fab 說明與 Fab 版 zip、試聽包＋22 題英文答題卷、打包腳本（決定性，`--release` 在授權仍是草稿時拒絕執行） | 收工總驗證 `x2_verify.py` 86/86；zip 重打兩次 sha256 相同 | `wf0925_X2_*.txt`（6 檔，**untracked**）；入口 `exports/products/clean_batch2_v1_1_candidate/CHANGES_v1_1.md` |
| **X 稽核** | 自寫量測腳本（BS.1770-4 響度、4 倍／16 倍過取樣真峰值），不用 X1／X2 的腳本 | **FAIL**：唯一一條 fix——三語 README 寫 loop-ready 檔「跟原樂句每 N 小節重播逐樣本相同（最大差 0）」說得太滿：交付檔多了一個整體增益（−0.55～−0.77 dB，為了維持 −1 dBTP）和 24-bit 捨入，拿 zip 裡的原版檔重播來比，最大差 26,826～44,774 LSB24。其餘原始檔完整性、音訊數字、zip 內容都 PASS；另有 note：全精度真峰值在 0.01 dB 以下隨量測器而變、README 有 12 個秒數被捨入兩次、「0 顆」沒寫出 N1 只掃弦類引擎的範圍、阻尼措辭略強 | `output/wf0925/X_audit/`（`xa_measure.txt` agree 47/65 的差異逐條見 findings；`xa_zip_text.txt` 49/52 PASS） |

### 規劃、整合

| 卡 | 做了什麼 | 關鍵數字 | 證據 |
|---|---|---|---|
| **Q1**（彙總裁決包） | 把盤點 §3-1 與本輪 11 張卡的 open_items（附錄 A 共 108 條逐條歸檔）整理成一份裁決包；新查了 GitHub API（pluginval、VST3 SDK）與本機磁碟現況（舊 VST3 副本、Downloads 殘留） | **37 題（Q01–Q37）＋其他待裁 O01–O19**；每題回一個字母；總覽表標「急」與會不會改聲音。新查到：pluginval v1.0.4（`pluginval_Windows.zip` 2,408,590 B）；VST3 SDK 沒有 GitHub release，validator 要照 CI 做法自己建；三份舊 VST3 副本都還在、標準位置 `Common Files\VST3\TsukiSynth.vst3` 不存在；Downloads 殘留共 613.5 MiB；C 槽剩約 20 GB；CLI 渲染其實會 include `src/effects/`（R6 字面沒列） | `reports/decision_packets/WF0925_open_decisions.zh-TW.md`；API 原始回應 `output/wf0925/Q1/`（gitignored） |
| **INT**（整合） | 三條已 staged 的 lane 合在一起，重建 `build\` 跑全套 | **10 條 GATE 全綠**：cmake／三主 target／五測試 target EXIT=0、error/warning 0 行；ctest 4/4（AuditTest 110 PASS／0 FAIL，D9c-guard PASS，K-02 0.112 dB）；pytest **282 passed＋1 skipped＋5 xfailed＝288**；`--full` NO CHECKED FAILURES（3 個 rubber N/A，跟 K 稽核 621 行逐行相同）；`--selftest` 13/13；`verify_score --all` 75/75（1 項既有豁免）；HostProbe 在 repo 根目錄與 `output/wf0925/INT` 各跑一次都 215／0；8/8 IDENTICAL。新 `build\` CLI sha256 `b84c775b…` | `reports/gate_outputs/wf0925_INTEGRATION.txt`、`wf0925_integration_raw/`（23 檔） |

## 3. staged 狀態（交接卡 stage 之後）

- 稽核 PASS 的三條 lane：C++ 34＋Python／CI 15＋研究 75＝124 檔；整合卡 24 檔；交接卡 6 檔（本檔、`HANDOVER.md`、`TODO.md`、`DEVLOG.md`、`README.md`、`reports/decision_packets/WF0925_open_decisions.zh-TW.md`）。合計 **154 檔**。
- **沒有 stage** 的（全部 untracked）：
  - `reports/gate_outputs/wf0925_X1_*.txt`（9）、`wf0925_X2_*.txt`（6）：商品稽核 FAIL，要等修正輪複驗 PASS。
  - `reports/status_check_2026-09-25/`：09-25 盤點本身，本輪的輸入，要不要進版控見裁決包 Q34。
  - `docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md`：含售價，repo 是 PUBLIC，見 Q34a。
- 沒有任何卡做 `git commit`／`push`；HEAD 仍是 `18430c4`。
- （**WF0925b 後**：上面兩類 untracked 證據已 stage；staged 合計 **239 檔**，見 §7-5。）

## 4. 建議的 commit 切法（給裁決包 Q33 用；月月決定要不要照這樣切）

> **WF0925b 後這張表的檔數已經不對**（多了 85 檔、有 10 檔被再改過）；包含 WF0925b 的完整切法見 **§7-6**（239 檔，逐條 pathspec 已核對不重疊、不漏）。

| # | 內容 | 檔案（pathspec） | 檔數 |
|---|---|---|---|
| c1 | plugin／測試（K1＋K2）：E8／E9／E14／E15、D12 斷言、D9c-guard、E16、HostProbe cwd、B7／D13／D9c 註解 | `src/`（9 檔）、`tests/audit_repro.cpp`、`tests/host_probe.cpp`、`scores/examples/water_gong_free.score.json` | 12 |
| c2 | CI 與工具（P1） | `.github/workflows/`（2）、`tools/*.py`（4）、`tests/test_measurement_selfcal.py`、`tests/test_stem_stream.py`、`reports/gate_outputs/wf0907_method/render_wf_scores.py` | 9 |
| c3 | 研究報告與裁決包（N1／F5／V1／L1，加 D9、D11 裁決包的追記） | `docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md`、`reports/weak_fundamental_null_map*`、`reports/d11_f5_root_cause_2026-09-25.zh-TW.md`、`reports/partial_verify_full_2026-09-25.zh-TW.md`、`reports/voice_pool_occupancy_2026-09-25.zh-TW.md`、`reports/wf0925_method/`、`reports/decision_packets/D9_*.md`、`D11_*.md` | 42 |
| c4 | 發行與授權文件（G1） | `LICENSE`、`THIRD_PARTY_NOTICES.txt`、`docs/legal/`、`tools/installer/`、`docs/KNOWN_LIMITS_INDEX.zh-TW.md`、`docs/correspondence/`（2） | 9 |
| c5 | GATE 證據（各卡＋整合） | `reports/gate_outputs/wf0925_*`（52）、`wf0925_INTEGRATION.txt`、`wf0925_integration_raw/`（23） | 76 |
| c6 | 交接文件與裁決包 | `HANDOVER.md`、`TODO.md`、`DEVLOG.md`、`README.md`、`docs/workcards/WF0925_README.md`、`reports/decision_packets/WF0925_open_decisions.zh-TW.md` | 6 |

合計 154。用路徑清單 commit 時照 `HANDOVER.md` §10：清單先去 CR（`tr -d '\r'`）。

## 5. 本輪的教訓（下一輪沿用）

1. **GATE 4／GATE 3 一律明確帶 `--cli <絕對路徑>`，並檢查 log 裡 manifest 的 renderer 欄位**。K1 的 `--cli` 後面是空白，`find_cli` 自己挑了 `build\` 的舊 CLI，回報卻寫「用 build-wf」——稽核第 1 輪才抓到（K1K2fix 更正）。
2. **稽核的反例要做在「會被信任」的地方**：K 稽核的 E8 malloc 計數探針、E16 NaN mutation、P1 稽核的 D15 pin 反例，都證明了新檢查有牙齒；E8 的實測目前只是稽核工具，不是 repo 的 GATE（裁決包 O08）。
3. **商品文字要照「買家能驗證的東西」寫**：X1 的數學（tail-wrap 跟連續播放逐樣本相同）是對的，但比的是加增益之前；寫進 README 就變成說過頭（X 稽核唯一的 fix）。
4. **CI 的 pwsh 多行 `run:` 只看最後一個指令的 exit code**（P1 稽核查到的既有問題）：看到 CI 綠燈不代表中間每一步都過，Q12 裁決前要記得這件事。
5. **中斷後接手**：先核對前任留下的產出（雜湊、引文、輸出）再續做，V1、L1、G1 都照做了，也順手抓到前任的行號、頁碼錯誤。

## 6. 留給下一輪（交接卡權限外，沒改）

交接卡只准動 HANDOVER／TODO／DEVLOG／README／本檔，以下是各卡與稽核點名「交接要同步」、但檔案不在交接卡範圍的，照原樣列出。
**每條後面的「→」是 WF0925b 收尾輪的處理狀態**（2026-09-25 交接卡 HO2 補；卡號與證據見 §7）：

- `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8 的數字要換成 A14 之後的實測（V1）：671/22/212 → 677/16/212；殘差 −118.60 → −119.42 dBFS；音高 883/883、最大 2.4266 c → 889/889、最大 3.0355 c；起音 671 → 677；「22 顆高音」→ 另一批 16 顆；§8.4-4 可發布措辭的數字（措辭要月月重新核定）；§8.6「partial_verify 從未在全曲 905 規模執行過」→ 已執行。另 `:342-344` 的 partial_verify 升 GATE 說法是舊的（P1）。
  → **已處理（DS）**：數字全部換新（稽核從 V1 原始 JSON 重算 12 項全對），§8.6 改「已執行」並附數字，升 GATE 那段加更新註記。**§8.4 第 4 點可發布措辭原句沒改**，只在句後加註「最新實測 889/677，措辭待月月重新核定」；§8.6 另標出 09-09 的「22 顆 pitch_via_partials 全數 PASS」對現行 binary 已不成立（20/22，見裁決包 Q18b）。
- `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md:28-30`「同步備忘：尚未帶上這段聲明」——PlateModel.h 檔頭與 water_gong_free 描述已由 K1 帶上（K1）。
  → **已處理（DS）**：改成「K1 已同步」。
- `docs/WOOD_ANISOTROPY_SOURCES.md:157`、`:198`「Table 5–15 未取得」→ 已取得，指向 D1 文件 §7（L1）。
  → **已處理（DS）**。
- `ROADMAP_PHYSICS.md` 裡 E8／E9／E14／E15／D12-legacykey／B7-residual／D9c-calib 的狀態（K1）；R6、R7、§6 的措辭等 Q02–Q04 裁決後再改。
  → **狀態已處理（DS）**：檔尾新段列 13 條 WF0925 落地狀態，檔頭 A14／D13／D9c／D11 四列就地補一句；原本 483 行一行都沒位移（裁決包引用的行號仍有效），§1 十條原文與 §6 整節逐字相同（稽核對 HEAD 版 diff 過）。**R6、R7、§6 措辭照舊等 Q02–Q04**，只在待裁註記加了指向。
- `.github/workflows/physics.yml`、`release-physics.yml` 的 HostProbe 步驟註解還寫「working directory MUST be the repo root」（K2 之後已不必，步驟本身照樣能跑）。
  → **已處理（TF）**：兩支都改成現況（cwd → `TSUKI_REPO_ROOT` → exe 往上找，會印出用了哪條）。
- `tools/partial_verify.py` 的模組 docstring（約 :28-33）與報告 caveats（約 :667「C10 self-cal still pending 月月裁決」）仍是舊說法（P1、V1；裁決包 O16）。
  → **已處理（TF）**：docstring 與 `caveats[0]` 改成現況（C10 09-10 選 A、D15 09-15 選 A'，升 GATE 要月月另裁），`gate_ready` 仍是 false。09-25 V1 那份報告檔本身是舊輸出，沒重跑。
- `src/physics/HammerImpulse.h:422`、`:471` 兩處泛指 call site 的歷史描述（K1 沒在卡上列的行號內）。
  → **沒處理**：WF0925b 不改 `src/`，留給下一張 C++ 卡（純註解，照 R6 跑全套）。
- D9c 註解與 D9 裁決包寫「×26.9＝+28.58 dB」：嚴格算 20·log10(26.9)=28.595 dB，+28.58 是 4 樣本平均落差的原數字（K 稽核 note，只是用詞）。
  → **一半處理（DS）**：D9 裁決包檔尾加 E18（`juce_Convolution.cpp:623-629`、`:628` 的 0.125 正規化＝−18.06 dB、升 JUCE 前要重跑 K-02、28.58 vs 28.595 的用詞備註）。**`src/effects/EffectChain.h` 的註解沒改**（改 src，要另開卡）。
- `reports/voice_pool_occupancy_2026-09-25.zh-TW.md` §1 表第 1 列把 `PluginProcessor.cpp:34-36` 寫成「addSound＋addVoice 16」，addVoice 其實在幾行之後（R 稽核 note）。
  → **沒處理**：不在任何 WF0925b 卡的清單裡。
- 兩封信的標題行還是「信件草稿 1／2」（G1）。
  → **已處理（DS）**：改「信件 1／2（已寄出 2026-09-15）」。
- `reports/gate_outputs/wf0914_INTEGRATION.txt:97` 寫「15 項自我測試」，它自己的 raw 檔只有 13 項（整合卡順帶發現）。
  → **已處理（DS）**：原文不動，檔尾附加勘誤（15 → 13；稽核用 cmp 確認改前內容完整留在檔頭）。
- 商品 lane 修正輪：README 的 loop 說法（X 稽核 fix）、秒數捨入兩次、真峰值全精度數字註明量測法、「0 顆」補範圍；修完重打 zip、重跑 `x2_verify.py`，複驗 PASS 後才 stage 那 15 個證據檔。
  → **已處理（XF，稽核 PASS）**：四項全修、另補阻尼措辭與 QA 接縫百分位取法；重打 zip、`x2_verify.py` 134/134；X1／X2 的 15 個證據檔（去掉本機路徑 24 處）與 XF 的 9 個證據檔已 stage。

## 7. WF0925b 收尾輪（2026-09-25，同日接在 WF0925 之後）

> 起因：月月 09-25 裁決「剩下 AI 能處理的都處理掉」。WF0925 交接之後還剩：商品稽核 FAIL 那一條、§6 待同步清單、裁決包裡標「AI 可做／AI 可查」的幾項（Q12 建議 A、O05、O15、O16、O18），以及 Q17 選項 D 的「先算數字」。
> 收尾輪把這些做掉。流程同 WF0925：工兵 → 稽核親自重跑 → PASS 才 `git add`；**不改 `src/`、不建置 plugin、沒有任何渲染輸出改變**。
> 暫存在 `output\wf0925b\<卡號>\`（gitignored），證據在 `reports\gate_outputs\wf0925b_<卡號>_*.txt`（進版控；本機路徑一律換成 `<REPO>`／`<SCRATCH>`／`<APPDATA>` 代稱）。
> Q12 是在月月「都處理掉」的授權下**先照建議 A 做、可以推翻**；其他需要月月選的題，本輪一律只給數字、不替月月選。
> 本節數字是交接卡（HO2）從證據檔親自核對的；交接卡自己另外量的數字列在 §7-7。

### 7-1 卡片與稽核判定

| lane | 卡 | 做了什麼（白話） | 關鍵數字 | 證據 | 稽核 |
|---|---|---|---|---|---|
| CI／tools | **TF**（Q12＋O16） | Q12：兩支 workflow 的每個多行 pwsh 區塊，每一行原生指令後面補 `if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }`；HostProbe 移到各自 job 的最後（release 的 corpus job 改看 build job 的 `cli_uploaded`，所以 HostProbe 失敗時 corpus 照跑、整條仍是紅燈）；HostProbe 註解改成現況。O16 六項：`crossplatform_verify.py`、`test_dump_modes_layered.py` 的 find_cli 不再看 mtime；`stem_verify` 讀得懂 WAVE_FORMAT_EXTENSIBLE（不支援的格式照樣大聲丟錯）；`render_wf_scores.py --cli` 先轉絕對路徑；`stem_verify`、`partial_verify` 加 `--cli`（指到不存在的檔就 exit 1，不會退回自己找）；`partial_verify` docstring 與 caveats 改成現況；release 網格「0 拒量」從 strict xfail 搬到一般測試（原本的條件照搬，不是新門檻） | 照 GitHub runner 包法模擬「只讓一個指令失敗」：改前 **12 種被蓋掉**（整步綠燈）→ 改後 **0 種**（TF 模擬 30 種情境、稽核自寫模擬 31 種）；全部成功時每步都 exit 0；突變 11/11 抓到；pytest 收集 288→307（+19，刪 0）；selfcal 8 passed＋5 xfail；`--cli` 相對路徑 8/8 IDENTICAL | `wf0925b_TF_{summary,q12_yaml,q12_pwsh_sim,pytest,render_bit_identity,cli_min_runs}.txt`＋稽核 `wf0925b_TF_audit.txt` | **PASS**（stage 17 檔：程式／測試 10＋證據 7） |
| 文件 | **DS**（§6 文件同步） | EARFREE §8 換成 A14 之後的數字、§8.6 改「已執行」；ENGINE_DOMAIN_CLAIMS「K1 已同步」；WOOD `:157`／`:198`「Table 5–15 已取得」；ROADMAP 檔尾加 13 條 WF0925 落地狀態；兩封信標題「已寄出」；`wf0914_INTEGRATION.txt` 檔尾勘誤；D9 裁決包檔尾 E18；WF0907／WF0914 README 檔尾附記；KNOWN_LIMITS_INDEX 的行號（逐條狀態見 §6） | 677／16／212、殘差 −119.42 dBFS、音高 889/889 最大 3.0355 c、起音 677 最大 6.9272 ms；partial 5,428 格 PASS 4577／FAIL 849／UNVERIFIED 2、pitch_via_partials 16/16（−3.56～+1.33 c）。稽核自己從 V1 原始 JSON 重算 12 項全對；ROADMAP §1 十條與 §6 對 HEAD 逐字相同 | `wf0925b_DS_changes.txt`＋稽核 `wf0925b_DS_BR_audit.txt` | **PASS**（stage 12 檔） |
| 研究 | **BR**（Q17 選項 D 的「先算數字」） | 把 staged 樹解到隔離副本，只刪 `src/physics/BeamModel.h:54` 的 `* 2.0f`，建「現行」「拿掉 ×2」兩支 CLI 比前後；主工作樹、樂譜、商品檔都沒動 | 見 §7-2 | `reports/beam_x2_option_b_before_after_2026-09-25.zh-TW.md`、`reports/beam_x2_option_b/`（19 檔）、`wf0925b_BR_*.txt`（6 檔） | **PASS**（stage 26 檔） |
| 商品 | **XF**（商品稽核 FAIL 修正輪＋O05＋O18） | 三語 README（一般版、Fab 版）的 loop 說法照實改寫；秒數改成只捨入一次；真峰值改寫成三支量測器的實測範圍；「0 顆」補上 N1 只掃弦類引擎的範圍；阻尼措辭照 `docs/MATERIALS_SOURCES.md` 改保守；QA 接縫百分位統一取法；起草專輯授權 `LICENSE_ALBUM_v1_1.txt`（O05）；查 DistroKid 寫成 `DISTROKID_NOTES.md`（O18）；X1／X2 證據檔去掉本機路徑；重打 zip | 見 §7-3 | `wf0925b_XF_{loop_facts,tp_meters,web_sources,packages,verify,redaction,audit_rerun,originals,recheck}.txt`；入口 `exports/products/clean_batch2_v1_1_candidate/CHANGES_v1_1.md` 開頭「XF」段 | **PASS**（stage 24 檔：X1／X2 證據 15＋XF 證據 9；`exports/` 照舊不進版控） |
| 整合 | **INT2** | 開工核對 staged 歸屬；src 與 `build\` 執行檔跟 WF0925 整合卡相同，所以不重建；跑全套 GATE | 見 §7-4 | `wf0925b_INTEGRATION.txt`、`wf0925b_integration_raw/`（14 檔） | —（stage 自己的 15 檔） |
| 交接 | **HO2** | 本節、§0／§3／§4／§6 的 WF0925b 註記、HANDOVER／TODO／DEVLOG／README、裁決包追記（各題下「2026-09-25 WF0925b」那一行、新增 Q38） | 見 §7-7 | — | — |

**稽核判定的出處**：TF、DS／BR 的稽核證據進版控（`wf0925b_TF_audit.txt`、`wf0925b_DS_BR_audit.txt`）。
**XF 的稽核沒有進版控的證據檔**，判定只在稽核回報和 `output/wf0925b/XF_audit/`（gitignored）：自寫 `a3_zips` 36/36 PASS、`a5_redaction` 18/18 PASS、`x2_verify` 重跑 134/134 PASS、`a2_loops`（6 個 loop 全量、24-bit 整數）。
`wf0925b_XF_audit_rerun.txt` 是 XF 工兵自己重跑舊稽核腳本的紀錄（51/52；剩下那條是舊腳本 `output/wf0925/X_audit/xa_zip_text.py:262` 把舊字面值 −0.97..−1.05 寫死、不讀 README），**不是稽核判定**；它最後的「RESULT: PASS」是工兵加的判讀，稽核認為判讀正確、列為 note。

### 7-2 BR：拿掉 ×2 前後（全部是描述用數字、非 GATE；報告沒有替月月選 A／B／C）

- 隔離副本＝staged 樹：「現行」CLI 渲染 8 首基準 **8/8 IDENTICAL**；「拿掉 ×2」CLI 5/8 相同，變的 3 首＝月光空靈鼓版、月光揚琴＋空靈鼓混合版、`ai_radiance_m1`。
- 舌鼓每個模態都響得更久、頻率完全不變：鋼的基頻 T60 變長 **1.15～1.80 倍**（C3 35.15→60.38 s、C4 16.39→26.86 s）；鋁 1.11～1.73 倍（C4 30.135→46.965 s）；黃銅、玻璃、竹、木頭接近 2 倍。兩支 CLI 的 dump 對公式最大差 5×10⁻⁵（列印精度）。
- corpus 75 份：用到 BeamModel 的 39 份 **39/39 改變**，其餘 36 份 36/36 相同。會變的 39 份都有峰值正規化，峰值不變；全檔 RMS −1.1～+3.0 dB；尾段能量佔比最多 +6.2 dB；檔案最多長 0.77 s（音效）／2.6 s（月光）。
- 商品 clean_batch2：現行 CLI 逐位元重現 **50/50** 母帶；拿掉 ×2 後 **36 件會變**（音效 32＋AI Radiance 4），14 件不變。
- `physics_verify --full` 兩版都是 NO CHECKED FAILURES。但裡面跟衰減有關的檢查都是「渲染對模型自己的數字」，×1、×2 都會過——**不能用來判斷哪一版比較像真舌鼓**。
- 對照 D1 已引述的文獻數字，7 個對照點：現行 0 個、拿掉 ×2 只有 1 個落在範圍內（鋼 C4：拿掉 ×2 是 0.257 /s，在 0.11～0.36 內；現行 0.421 高於上緣）。鋁 C4 兩版（0.229、0.147 /s）都低於熱彈性單項 0.376～0.541 /s。兩版都是有的點偏高、有的點偏低。
- 如果選 B，後續清單在報告 §6（註解改寫、響度補償錨點要不要重量、3 首基準 sha 換新要月月核准、商品 36 件重出與 v1.1 候選重打等）。範圍外發現：`exports/products/moonlight_batch1` 舌鼓版與混合版母帶跟現行渲染本來就不同，跟 ×2 無關（跟 HANDOVER §5-2 第 3 點「月光母帶仍是舊渲染」的記錄相符）。

### 7-3 XF：商品修正輪（`exports/`，gitignored）

- 原版 `clean_batch2/` 212 檔 sha256 跟 WF0925 X1 開工前的清單相同（XF 用 Python 與 shell 各驗一次，稽核自己再算一次：少 0、多 0、改 0）。
- loop-ready 6 檔（24-bit 整數、6/6 全量）：套增益**之前**，tail-wrap 跟「母帶每 N 樣本重播」最大差 0；用 X1 記的增益重寫＝交付檔 6/6；跟 zip 裡原版重播比最大差 26,826～44,774 LSB24，常數增益差 +0.032～+0.052 dB（原版較小聲）；X1 增益 −0.5478～−0.7680 dB。README 新說法：套增益前逐樣本相同，交付檔不是逐位元相同。
- 真峰值：43 個音效，三支量測器合起來 **−0.949～−1.048 dBTP**、同一檔最多差 0.07 dB（XF 實測最大 0.0654 dB；第四支量測器 0.0662 dB，描述用、非 GATE）；loop-ready −0.996～−1.002 dBTP。`LISTING_COPY_v1_1.md` 政策 A 的舊範圍 −0.97～−1.05 也改成同一組數字。
- 商品 zip（sha256）：SE 一般版 `50749a0e…`（51 成員）、SE Fab 版 `082b8e69…`（50）、專輯 `049339ed…`（13，沒變）、試聽包 `38ac5b45…`（沒變）。跟 XF 之前比，只有兩個 SE 版的 `README.txt` 成員不同，**音檔都沒動**。
  注意：staged 的 `wf0925_X2_packages.txt`／`wf0925_X2_verify.txt` 是 X2 當時的歷史紀錄（SE `1eaa4839…`／`465f65a7…`、86/86），**現況以 `wf0925b_XF_packages.txt`／`wf0925b_XF_verify.txt`（134/134）為準**。
- 專輯授權 `LICENSE_ALBUM_v1_1.txt`（O05）：開頭有「草稿、非法律意見、待月月審」方框；第 5 條影片／直播 BGM 並列 A 案（允許）、B 案（只個人聆聽）；其他待填標 [TBD]；**不在任何 zip 裡**。
- DistroKid（O18）：說明中心 12 篇都回 HTTP 403（沒有繞過），只拿到搜尋摘要（檔內標「DK 摘要、非逐字」）；Spotify、YouTube 官方頁的逐字錨點 17/17。要點：給愛麗絲是公版樂曲，依摘要不符合 DistroKid 的 Content ID 資格；曲風選 Classical，依摘要不送 Apple Music；上傳表單的 AI 選項有沒有「部分音訊」，三次搜尋兩次有、一次沒有。K1～K7 要月月登入確認。
- `CHANGES_v1_1.md` §0 的待確認從 10 項變 **12 項**（新增 11 專輯授權、12 DistroKid）。

### 7-4 INT2：整合（`build\` 沒重建，CLI 仍是 `b84c775b…`）

| GATE | 結果 |
|---|---|
| 開工核對 | staged 224 檔、「staged 之後又改」0 檔；WF0925 的 154 檔全在（10 檔被 TF 6／DS 4 再改過），新進 70 檔逐檔歸到 TF／DS／BR／XF，來源不明 0。src/ 9 檔＋`audit_repro.cpp`、`host_probe.cpp`、`water_gong_free.score.json` 雜湊對 WF0925 C++ 稽核清單全部 OK；`build\` 6 支執行檔 sha256 跟 WF0925 整合卡相同 → 不重建 |
| pytest 全套 | **307＝301 passed＋1 skip＋5 xfail**（新基線；+19 全來自 TF，刪 0；skip／xfail 是同樣 6 條） |
| `physics_verify --full` | NO CHECKED FAILURES（3 個 rubber N/A）；570 行跟 WF0925 整合卡逐行相同 |
| `--selftest` | 13/13，逐行相同 |
| `verify_score --all` | 75/75（1 項既有豁免），75 份 manifest 的 renderer 都是 `b84c775b04ab`；3836 行逐行相同 |
| 位元不變 | **8/8 IDENTICAL**，這次 `--cli` 故意用相對路徑 |
| HostProbe | **215 PASS／0 FAIL**，cwd 在 repo 外、沒設 `TSUKI_REPO_ROOT`；跟 WF0925 整合卡 215 對 215；跑前跑後 `%APPDATA%\TsukiSynth\IR`、`\Presets` 都沒有殘留 |
| 沒跑 | cmake／ctest：執行檔沒變，WF0925 整合卡的 ctest 4/4、AuditTest 110 PASS 仍適用 |

### 7-5 staged 狀態（交接卡 stage 之後）

- **239 檔**＝WF0925 的 154 檔＋WF0925b 新進 85 檔。新進的 85 檔：TF 11（程式／測試 4＋證據 7）、DS 8（文件 7＋證據 1）、BR 26、DS／BR 稽核 1、X1／X2 證據 15、XF 證據 9、INT2 15。
  交接卡 HO2 只改已經 staged 的 6 個檔（HANDOVER、TODO、DEVLOG、README、本檔、WF0925 裁決包），檔數不變。
- 沒 stage（untracked）的只剩兩項，都等 Q34：`reports/status_check_2026-09-25/`（盤點本身）、`docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md`（含售價）。
- 沒有任何卡 `git commit`／`push`；HEAD 仍是 `18430c4`。

### 7-6 建議的 commit 切法（取代 §4 的檔數；裁決包 Q33）

| # | 內容 | 檔案（pathspec） | 檔數 |
|---|---|---|---|
| c1 | plugin／測試（K1＋K2） | `src/`、`tests/audit_repro.cpp`、`tests/host_probe.cpp`、`scores/examples/water_gong_free.score.json` | 12 |
| c2 | CI 與工具（P1＋TF） | `.github/workflows/`、`tools/*.py`、`tests/test_*.py`、`reports/gate_outputs/wf0907_method/render_wf_scores.py` | 13 |
| c3 | 研究報告與裁決包追記（N1／F5／V1／L1／BR，加 D9、D11 裁決包） | `docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md`、`reports/weak_fundamental_null_map*`、`reports/d11_f5_root_cause_2026-09-25.zh-TW.md`、`reports/partial_verify_full_2026-09-25.zh-TW.md`、`reports/voice_pool_occupancy_2026-09-25.zh-TW.md`、`reports/wf0925_method/`、`reports/decision_packets/D9_*`、`reports/decision_packets/D11_*`、`reports/beam_x2_option_b*` | 62 |
| c4 | 發行與授權文件（G1；含 DS 改的兩封信與索引） | `LICENSE`、`THIRD_PARTY_NOTICES.txt`、`docs/legal/`、`tools/installer/`、`docs/KNOWN_LIMITS_INDEX.zh-TW.md`、`docs/correspondence/` | 9 |
| c5 | 文件同步（DS） | `ROADMAP_PHYSICS.md`、`docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md`、`docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md`、`docs/WOOD_ANISOTROPY_SOURCES.md`、`docs/workcards/WF0907_README.md`、`docs/workcards/WF0914_README.md`、`reports/gate_outputs/wf0914_INTEGRATION.txt` | 7 |
| c6a | GATE 證據（WF0925 各卡＋整合＋X1／X2） | `reports/gate_outputs/wf0925_*` | 91 |
| c6b | GATE 證據（WF0925b 各卡＋稽核＋INT2） | `reports/gate_outputs/wf0925b_*` | 39 |
| c7 | 交接文件與裁決包 | `HANDOVER.md`、`TODO.md`、`DEVLOG.md`、`README.md`、`docs/workcards/WF0925_README.md`、`reports/decision_packets/WF0925_open_decisions.zh-TW.md` | 6 |

合計 239。每列用 `git diff --cached --name-only -- <pathspec> | wc -l` 數過，八列的聯集（`sort -u`）也是 239，所以不重疊、不漏。
要照這樣切，最簡單是每個 commit 直接帶 pathspec：`git commit -m "…" -- <pathspec…>`。注意 `--` 後面帶路徑時，git 拿的是這些路徑的**工作樹**內容；交接卡收工時工作樹跟 staged 完全相同（`git diff --stat` 空白），所以結果一樣——commit 前再確認一次 `git diff --stat` 是空的。用路徑清單檔時照 `HANDOVER.md` §10 先去 CR。

### 7-7 交接卡自己核對的數字（唯讀）

| 查什麼 | 命令 | 結果 |
|---|---|---|
| staged 檔數與 §7-6 切法 | `git diff --cached --name-only -- <pathspec> \| wc -l`；八列合併後 `sort -u \| wc -l` | 12／13／62／9／7／91／39／6，合計 239；聯集 239 |
| 商品 zip | `sha256sum exports/products/clean_batch2_v1_1_candidate/packages/*.zip` | `50749a0e…`／`082b8e69…`／`049339ed…`／`38ac5b45…`，跟 XF 證據相同；試聽包裡的答題卷沒有「identical」之類的說法（grep 0 行） |
| 渲染器第二份備份（O15） | `ls -la`、`sha256sum /e/TsukiSynth_renderer_archive/*` | 資料夾建立時間 09-25 11:40；exe `9123db8f63390bfe9070e9509fb2b60e9cc32ecb52e3bb2afc330d2b5fe01be8`（7,132,160 B），`README.txt`、`SHA256SUMS.txt` 跟 `exports/renderer_archive/` 那兩個檔 sha256 相同。`SHA256SUMS.txt` 裡寫的是 repo 相對路徑，在 E 槽資料夾裡直接 `sha256sum -c` 會找不到檔，要手動比 |
| staged 內容裡的本機路徑（Q34b） | 逐檔 `git show ":<檔>" \| grep -c -i 'users[\\/]admin'`（交接卡 stage 前） | 49 檔共 309 行，全是 WF0925 的證據檔與少數既有文件（最多的是 `wf0925_K2_hostprobe.txt` 52 行）。WF0925b 進版控的 74 個證據與報告檔（`wf0925b_*` 39、`beam_x2_option_b*` 20、X1／X2 15）只有 `<REPO>`／`<SCRATCH>`／`<APPDATA>` 代稱，**0 處真實本機路徑**。另外 `wf0925_V1_partial_stem_verify_full.txt` 有 E 槽路徑 `E:\tsuki_wf0925_V1\…`（沒有使用者名稱；DS／BR 稽核 note） |
| 暫存大小與磁碟（Q36b） | `du -sh`、`df -h /c /e` | `output/wf0925/` 5.2 GB、`output/wf0925b/` 1.9 GB（XF 1.3 GB、BR 391 MB、XF_audit 222 MB）、session scratchpad 8.9 GB（其中 `wf0925b` 5.4 GB）、`E:\tsuki_wf0925_V1\` 17 GB；**C 槽剩 12 GB（98%）**，WF0925 查時是 20 GB。BR 的樹副本裡的 JUCE junction 已移除（DS／BR 稽核掃 reparse point 0 個），一般刪除不會波及主 repo 的 `libs/JUCE` |
| F-03 缺檔警告字串（Q38） | `grep -n` | 中文在 `src/PluginProcessor.cpp:901`、英文 `:902-904`（staged 版行號；HEAD 版是 `:841`、`:846`）；`tests/` 與其他 cpp／h／py 沒有任何地方斷言這段文字 |

### 7-8 留給下一輪（WF0925b 之後仍未處理；不需裁決的標「AI 可做」）

1. **push 之後驗 CI**（Q12、Q33）：看 `physics.yml` 那次 run；手動觸發一次 `release-physics.yml`；job outputs 與 `!cancelled()` 條件、runner 能不能無頭載入 VST3，都要 push 後才驗得到。
2. **要改 `src/` 的小項**（AI 可做，要另開 C++ 卡、照 R6 跑全套）：`HammerImpulse.h:422`／`:471` 歷史描述；`EffectChain.h` 的 `kIrWetMakeupGain` 註解補「約 18.06 dB 來自 JUCE 0.125 正規化」與 28.595 dB 用詞；F-03 缺檔警告字串（等 Q38）；**CLI 輸出路徑約 247 字元以上就 exit 1**（`src/cli/RenderApp.cpp` 寫 render manifest 時，JUCE 的暫存檔名再多最多 14 字元，超過 Windows 260 字元上限；TF、BR 各碰到一次；要不要讓 CLI 支援長路徑另裁，現在的做法是 `--workdir` 用短路徑）。
3. **文件**（AI 可做）：`docs/KNOWN_LIMITS_INDEX.zh-TW.md` 裡指向 `TODO.md` 的行號是照 HEAD 算的，TODO 已經改寫兩次，要重對一次或在檔頭註明；voice_pool 報告 §1 的行號；EARFREE `:371` 那句「09-25 V1 報告的 `caveats[0]` 還寫…」可以補「已由 WF0925b-TF 更新」；`reports/partial_verify_full_2026-09-25.zh-TW.md:181` 同一句（歷史報告，要不要加註再定）；Q18 A 案「工具說明寫明期望值取第 0 根弦」那半（EARFREE §8.6 `:420-421` 已有描述，工具的 `--help`／docstring 還沒有）。
   等月月的：EARFREE §8.4 第 4 點可發布措辭（883/671 → 889/677）、§8.6 那句 09-09 措辭（22 顆 → 現在 20/22，Q18b）；ROADMAP R6／R7／§6 措辭等 Q02–Q04。
4. **tools**（AI 可做）：`tools/melody_verify.py` 的 `verify()` 加 `cli=None`（現在 stem_verify 的 `--cli` 是靠 run 期間暫時替換 melody_verify 私有的 find_cli）；sustain 網格的「0 拒量」也搬出 strict xfail（現況 dev 1170/1170、hold-out 1040/1040 都是 0 拒量）。
5. **商品 lane**：下一輪稽核重跑舊腳本前，要把 `output/wf0925/X_audit/xa_zip_text.py:262` 寫死的舊字面值改成讀 README；`CHANGES_v1_1.md` §2.2 差異表有三列還是 XF 之前的阻尼措辭（內部說明檔，買家看不到）；`x2_build_packages.py` 的 loop 增益差是用只記到 0.1 dB 的 catalog `gain_db` 算的（現有資料剛好沒誤差）；第四支量測器讀到 −0.94886 dBTP，比 README 印的「三支量測器合起來 −0.949」高 0.00014 dB（README 寫明是三支量測器的範圍，不算寫錯；要改成不管用哪支量測器都成立的寫法，要月月裁，R2）；score 的「可無縫循環」描述 → O10。
6. **暫存清理**（Q36b，§7-7 有大小）。

### 7-9 本輪的教訓

1. **Windows 路徑長度上限會讓 CLI 失敗**：TF、BR 都因為輸出路徑太長碰到 CLI exit 1。`--workdir` 一律用短路徑。
2. **稽核判定要有進版控的證據檔**：XF 稽核的判定只在 gitignored 的 `output/`，整合卡與交接卡只能從回報引用。下一輪稽核請跟 TF、DS／BR 一樣寫 `wf<輪>_<卡>_audit.txt`。
3. **證據外殼不要改寫被包的結果**：`wf0925b_XF_audit_rerun.txt` 把 51/52 包成「RESULT: PASS」，理由寫在檔內、判讀也對，但讀的人容易誤會。要改判讀時，原結果和新判讀分開寫。
4. **中斷後接手照 WF0925 做法**：XF、TF 先核對前任的 diff 和產出再重跑 GATE，XF 接手時還補抓到 `LISTING_COPY` 有同一個舊範圍沒改。
