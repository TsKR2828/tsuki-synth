# WF0925 彙總裁決包：本輪留下、等月月拍板的事

> 卡號：WF0925-Q1（規劃者）｜日期：2026-09-25
> 工作樹：branch `fix/deep-physics-audit-20260716`，HEAD `18430c4`（比 origin 多 7 個 commit，未 push）。
> 撰寫時 staged 124 檔：P1 15 檔、研究 lane 75 檔、C++ lane 34 檔。X1/X2 的 15 個證據檔還是 untracked，因為商品稽核 FAIL、在等修正。
> 體例比照 `reports/decision_packets/K02_reverb_wet_scale.zh-TW.md`：每題有白話問題、背景數字（附出處）、並列選項、明標的建議。
> **本包不替月月選。** 本卡只寫了這一個檔：沒改程式、沒改其他文件、沒 `git add`。
>
> 題目來源：
> - 09-25 盤點：`reports/status_check_2026-09-25/STATUS_CHECK.zh-TW.md` §3-1 與 `APPENDIX_findings.zh-TW.md`（有「查證修正」的條目，以修正後為準）。
> - 本輪各 lane 的回報：C++ lane（K1、K2、K1K2fix、稽核）、Python lane（P1、稽核）、研究 lane（N1、F5、V1、L1、G1、稽核）、商品 lane（X1、X2、稽核）。
>
> 本卡新查了兩類數字：GitHub API（Q14、Q37）和本機磁碟現況（Q35、Q36）。命令和結果都在附錄 B，API 原始回應存在 `output/wf0925/Q1/`（gitignored）。
> 包裡的「−70 dBFS」「0.25 dB」「±5 c」等數字，全部引自既有來源。**本卡沒有新增任何判定門檻。**
> 行號注意：引自盤點 APPENDIX 的 `src/` 行號（例如 `PluginProcessor.cpp:382-395`），是盤點當時、K1 修改之前的行號。本輪 K1 改過 `PluginProcessor.cpp`、`CimbalomEngine.h` 等檔，現在的行號可能已經往後移，原文內容不變。`.github/`、`ROADMAP_PHYSICS.md` 的行號是本卡撰寫時重新查的。
>
> **2026-09-25 WF0925b 追記（收尾輪交接卡 HO2）**：同日又跑了 WF0925b 收尾輪（TF／DS／BR／XF／INT2，全部稽核 PASS 或全綠，逐卡見 `docs/workcards/WF0925_README.md` §7）。
> 各題下方以「**2026-09-25 WF0925b**」開頭的那一行是收尾輪的處理結果或補的數字；**題目、背景、選項、建議的原文都沒改**。
> 另外新增 **Q38**（F-03 缺檔警告措辭，WF0925 這份包漏收；在「六、」），所以現在是 **38 題 Q01–Q38＋O01–O19**。
> WF0925b 之後 `.github/` 的行號已經變了（TF 改過兩支 workflow），Q12、Q13 背景裡的行號是 WF0925 當時的。

---

## 怎麼回覆（看這裡就好）

- **每題回一個字母**，例如「Q01 B」。有子題的，例如「Q09b A」。
- **沒回的題＝維持現狀**，AI 不動。
- 「建議」是規劃者的看法，可以略過。
- 標 **R10** 的選項會改變聲音：可能是 CLI 渲染，也可能是外掛輸出。選了之後，AI 會先做一份前後對照報告給你看，**不會直接落地**。
- 標「要你動手」的：寄信、註冊帳號、需要管理員權限的系統資料夾、清空資源回收筒。這些 AI 依規定不能代做。

回覆範本（可以整段複製改字母）：

```
Q01 B  Q01b B  Q02 A  Q03 A  Q04 A  Q05 C  Q05b A  Q06 A  Q07 A  Q08 C
Q09 D  Q09b B  Q09c B  Q10 B  Q11 C  Q12 A  Q13 A  Q14 C
Q15 A  Q16 D  Q17 D  Q18 A  Q18b B  Q19 C（C1甲 C2甲 C3甲 C4甲 C7甲 C8甲，其餘等）
Q20 A  Q20b B  Q21 A  Q22 A  Q22b A  Q22c A  Q22d A  Q23 B  Q24a C  Q24b A
Q25 A  Q26 A  Q27 A  Q28 A  Q29 B  Q30 A  Q31 B  Q32（E1…E9 逐項）
Q33 A  Q34a A  Q34b A  Q34c A  Q34d A  Q35 A  Q36a A  Q36b A  Q37 1Y 2N 3Y 4Y
```

（上面這組字母就是各題「建議」的集合，只為了方便複製，**不是預設值**。）

（2026-09-25 WF0925b：新增的 Q38 不在上面的範本裡；要一起回就在最後加「Q38 A」之類。Q12 已在「都處理掉」授權下先照 A 做，回 B 或 C 就會改回去。）

---

## §0 總覽

「急」欄的意思：**上架前**＝賣音效包／專輯之前要定；**發版前**＝賣合成器本體之前要定；**不急**＝不擋任何東西。

| 題 | 一句話 | 選項 | 建議 | 選建議會不會改聲音 | 急 |
|---|---|---|---|---|---|
| Q01 | D9c 補償增益要不要加「響度差 ≤0.25 dB」的測試 | A/B/C | B | 不會 | 發版前 |
| Q02 | R6（改了就要跑全套 GATE）要不要涵蓋外掛層 | A/B/C | A | 不會 | 不急 |
| Q03 | R7 條文「留 unstaged」跟實務「稽核後 staged」對齊 | A/B/C | A | 不會 | 不急 |
| Q04 | §6 容差登記表補登兩個在用的門檻 | A/B/C | A | 不會 | 不急 |
| Q05 | 外掛輸出沒有限幅（IR 模式、部分工廠 preset 會超過 0 dBFS） | A/B/C/D | C | 不會 | 發版前 |
| Q06 | VST3 Program 參數只給工廠 preset | A/B/C | A | 不會（外掛行為變） | 發版前 |
| Q07 | VC++ runtime：靜態 CRT 還是附 vc_redist | A/B | A | 要驗 8/8 | 發版前 |
| Q08 | 外掛↔CLI 一致性：補 GATE 還是把文案收窄 | A/B/C | C | 不會 | 發版前 |
| Q09 | 外掛 16 顆 voice 會搶音 | A/B/C/D | D | 不會 | 發版前 |
| Q10 | D12：IR 載入失敗時靜默丟路徑、情境 3 舊鍵不清 | A/B/C/D | B | 不會 | 不急 |
| Q11 | B7 槌速函式在 MIDI 20 跳 2.3 倍 | A/B/C | C | 不會 | 不急 |
| Q12 | CI 多行指令只看最後一個 exit code（前面失敗會被蓋掉） | A/B/C | A | 不會 | 發版前 |
| Q13 | CI 的 Linux 標成 clang，實際是 GCC | A/B/C | A | 不會 | 不急 |
| Q14 | pluginval＋Steinberg validator 重驗（**要下載**） | A/B/C/D | C | 不會 | 發版前 |
| Q15 | 給愛麗絲鋼琴版母帶 16 顆弱基頻（D16） | A/B/C/D | A | 不會 | 上架前 |
| Q16 | D11 要不要依 F5 根因結果重開 A/B | A/B/C/D | D | 不會 | 不急 |
| Q17 | 舌鼓 BeamModel 的 ×2 阻尼 | A/B/C/D | D | 不會 | 不急 |
| Q18 | partial_verify 的期望值慣例、要不要升 GATE | A/B/C | A | 不會 | 不急 |
| Q19 | 9 條已知限制要不要升格成正式引擎主張 | A/B/C | C | 不會 | 發版前 |
| Q20 | 音效包響度政策 | A/B/C/D | A | 不會 | 上架前 |
| Q21 | AI 揭露口徑 | A/B/C | A | 不會 | 上架前 |
| Q22 | 音效包授權 v1.1 草稿要不要採用 | A/B/C | A | 不會 | 上架前 |
| Q23 | Fab 版怎麼做 | A/B/C | B | 不會 | 上架前 |
| Q24 | 商品圖、試聽帶採不採用 | a:A/B/C　b:A/B | a C、b A | 不會 | 上架前 |
| Q25 | AI Radiance 全曲版放不放進專輯 | A/B | A | 不會 | 上架前 |
| Q26 | loop 附哪一版 | A/B/C | A | 不會 | 上架前 |
| Q27 | 音樂 16-bit 版換成 TPDF dither 版 | A/B | A | 極小（見題內） | 上架前 |
| Q28 | 找聽人把關 | A/B/C | A | 不會 | 上架前 |
| Q29 | 合成器商品名裡 VST 怎麼寫 | A/B/C | B | 不會 | 發版前 |
| Q30 | 合成器首發平台（Windows／mac／AU） | A/B/C | A | 不會 | 發版前 |
| Q31 | JUCE Starter 要不要註冊、收入怎麼算 | A/B/C | B | 不會 | 發版前 |
| Q32 | 合成器買家 EULA 九個空格（E1–E9） | 逐項 | 見題內 | 不會 | 發版前 |
| Q33 | 本輪 staged 怎麼 commit、要不要 push | A/B/C | A | 不會 | 擋 Q12/Q14 |
| Q34 | 公開 repo：變現計畫、本機路徑、repo 公開與否、盤點資料夾 | a/b/c/d | 全 A | 不會 | 不急 |
| Q35 | 重新部署 VST3、清三份舊副本 | A/B/C/D | A | 不會 | 發版前 |
| Q36 | Downloads 約 470 MB 殘留、本輪暫存清理 | a:A/B/C　b:A/B/C | a A、b A | 不會 | 不急（C 槽剩 20 GB） |
| Q37 | 其他下載請求（Inno Setup、vc_redist、VST logo、論文） | 逐項 Y/N | 見題內 | 不會 | 看題 |
| Q38 | 外掛缺檔警告「音量會和 IR 模式不同」要不要改（WF0925b 補收） | A/B/C | A | 不會（只是畫面文字） | 發版前 |
| §7 | 其他待裁（不好用一個字母回的，或屬於你本人的事） | — | — | — | — |

---

## 一、規則與容差

### Q01　D9c 補償增益要不要加「響度差 ≤0.25 dB」的測試

**白話問題**：D9c 讓外掛 IR 模式的殘響，跟演算法殘響（ALGO）一樣大聲，做法是把 IR 的殘響乘 26.9 倍。
本輪 K2 已經加了一條測試，確認「26.9 這個數字沒被改掉」。
還有一個洞沒補：數字沒改，但 JUCE 升版改了內部算法，結果兩邊又不一樣大聲。
要不要再加一條測試，直接量「IR 和 ALGO 的響度差不超過 0.25 dB」？
0.25 dB 是規劃者寫 D9c 施工卡時，從 D9b 實測的展幅 0.24 dB 取的。**這個數字你沒裁過**，依 R2 和 §6，要你核准才能拿來當判準。

**背景數字**
- 補償後四組落差：合成 IR +0.112、Stairwells −0.131、Venues +0.108、Sanctuaries −0.028 dB。出處：`reports/gate_outputs/wf0914_D9c_ir_makeup_gain.txt` §2.5。0.25 dB 的來源寫在施工卡 `docs/workcards/WF0914_D9c_ir_makeup_gain.md:30`。
- 本輪 ctest 重跑，合成 IR 仍是 +0.112 dB（`wf0925_K1K2fix_build_ctest.txt`）。套用 0.25 dB 的話，餘裕是 0.138 dB。
- 26.9 倍裡，約 18.06 dB 來自 JUCE Convolution 的正規化係數 0.125（`libs/JUCE/modules/juce_dsp/frequency/juce_Convolution.cpp:628`）。JUCE 升版如果改了它，「26.9 沒被改」那條測試照樣綠燈。這是盤點 E18 的查證修正。
- 三顆真實 IR 放在 `external_data/`，這個資料夾是 gitignored，CI 上沒有。所以 CI 能跑的只有合成 IR 那一組。
- K2 讀 private 常數用的是 C++ 標準允許的「顯式實例化」寫法：合法，但繞路。比較乾淨的做法是在 `src/effects/EffectChain.h` 開一個唯讀存取點。這要改 src，不過不會改聲音。

| 選項 | 做法 | 代價 | 前提 | 改聲音？ | 工作量 |
|---|---|---|---|---|---|
| **A** 維持 | 只留「26.9 相等」那條；K-02 繼續只印數字 | JUCE 升版造成的響度漂移沒有自動擋 | 無 | 不會 | 0 |
| **B** 加響度 CHECK | 合成 IR 的 IR−ALGO 落差絕對值 ≤0.25 dB，並把 0.25 dB 登記進 §6。出處寫施工卡 §2.2 和 D9b 展幅 | 多一條你核准的容差 | 你核准 0.25 dB | 不會（只加測試） | S（C++ lane） |
| **C** 寫進清單 | 不加容差；在「升級 JUCE 檢查清單」寫明必須手動重跑 K-02／K-02-EXT | 靠人記得 | 無 | 不會 | S（文件） |

**子題 Q01b（守門的寫法）**：A＝保留 K2 的顯式實例化寫法；B＝另開卡，在 `EffectChain.h` 開 public 唯讀存取點。B 要跑 R6 全套，但不改聲音。

**建議（規劃者看法，可略過）**：Q01 選 **B**。成本小，而且是唯一擋得住「JUCE 升版悄悄改響度」的做法。Q01b 選 **B**，可以等下次有卡要動 `EffectChain.h` 時順路做。

---

### Q02　R6 要不要涵蓋外掛層

**白話問題**：R6 規定，改了某些資料夾，就一定要跑 `physics_verify --full` 加三個 build target。現在只列了 `src/physics/`、`src/engines/`、`src/dsp/`、`src/score/`。外掛層和 `src/effects/` 都不在名單上。

**背景數字**
- 原文在 `ROADMAP_PHYSICS.md:161`；待裁的註記在 `:171`。
- 不在 R6 名單裡的檔：
  - `src/effects/`：`EffectChain.h`、`SimpleReverb.h`、`StereoDelay.h`、`Compressor.h`
  - `src/cli/RenderApp.cpp`
  - `src/PluginProcessor.cpp`、`PluginEditor.cpp`
  - `src/IRLibrary.h`、`PresetManager.h`、`ParameterLayout.cpp`、`Presets.h`
  - `CMakeLists.txt`
- **本卡新查到**：CLI 渲染其實會用到 `src/effects/`。`src/score/ScoreRenderer.h:11` include `../dsp/EffectsChain.h`，`src/dsp/EffectsChain.h:3-5` 再 include `../effects/SimpleReverb.h`、`StereoDelay.h`、`Compressor.h`。所以改 `SimpleReverb.h` 可能改到 CLI 渲染，但照 R6 字面不必跑 GATE。
- 實務上沒出事：WF0914、WF0925 的 C++ lane 每張卡都照跑全套（K1、K2 各六條 GATE）。
- R6 指定的 GATE（`--full`＋三個 build）驗不到外掛行為。外掛層要靠 ctest（跑前先重建五個測試 target）和 HostProbe 才驗得到。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 擴成整個 `src/` 加 `CMakeLists.txt` | 外掛層另外規定 ctest 和 HostProbe 必跑 | 每次改外掛都要跑全套。光是 verify_score 這一步，本輪就要 24 分鐘到 1 小時（K1K2fix 約 24 分鐘，K2 約 1 小時，看機器負載） | 不會 | S（交接卡改 ROADMAP 文字） |
| **B** 只補 CLI 會用到的 `src/effects/`、`src/cli/` | 外掛層照舊靠各卡自律 | 規則跟「賣的是外掛」不一致 | 不會 | S |
| **C** 維持原文 | — | CLI 路徑（`SimpleReverb.h`）有沒寫進規則的洞 | 不會 | 0 |

**建議**：**A**。把已經在做的事寫成規則。

---

### Q03　R7 條文跟實務對齊

**白話問題**：兩邊寫法不一樣。
- R7 原文（`ROADMAP_PHYSICS.md:164`）：「不 commit、不 push。檔案留 unstaged」。
- 從 WF0907 起的實際流程：稽核 PASS 後，由稽核 `git add`，變成 staged（`docs/workcards/WF0907_README.md:58`、`WF0914_README.md:30`）。
- 今天那 7 個 commit，是依你的明示裁決做的。

你以前說過「留 unstaged 比 staged 安全、commit 訊息自己寫」。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 改字面 | 改成：「不 commit、不 push（月月明示裁決時除外）；稽核 PASS 後由稽核 `git add`（staged）供月月審」 | 等於正式接受 staged 當審查區 | 不會 | S |
| **B** 字面不變，改流程 | 稽核 PASS 後不 add，只交檔案清單，由你自己 add | 你多一步手動；三輪以來的流程要改 | 不會 | S |
| **C** 字面不變，只加註 | 在 WF README 註明「staged＝待審區」 | 規則和流程還是兩套說法 | 不會 | S |

**建議**：**A**。對齊三輪以來你已經接受的實務。如果你還是覺得 unstaged 比較安心，選 **B**。

---

### Q04　§6 容差登記表補登

**白話問題**：有兩個 GATE 門檻一直在用，但沒登記在 `ROADMAP_PHYSICS.md` §6。
- `melody_verify` 的 onset ±10 ms：C3-b，08-20 你委託 AI 依推導自定。證據 `reports/gate_outputs/l1_l2_l3a_melody_gate.txt`。
- 量測器自證的 1.0 c：你 08-30 查核第 5 點訂的。C10、D15 之後，主張域已收窄成：持續段 ≤1.18 c，放鍵段約 7.2 c。1.0 c 現在是 strict xfail 的判定值，也就是已知達不到。

另外兩個 ±5 c 不用新開一列：`melody_verify` 和 `partial_verify` 的 pitch ±5 c，是直接沿用 §6 已登記的「f0 誤差」列。待裁註記在 `ROADMAP_PHYSICS.md:474-479`。

| 選項 | 做法 | 改聲音？ | 工作量 |
|---|---|---|---|
| **A** 兩列都補登 | 數值不變，只補出處；兩處 ±5 c 註明「沿用 f0 列」 | 不會 | S（交接卡） |
| **B** 只補 selfcal 1.0 c | onset ±10 ms 是 AI 自定的，另外再裁 | 不會 | S |
| **C** 不補 | 維持檔尾備註 | 不會 | 0 |

如果 Q01 選 B，0.25 dB 也會在這一步一起登記。

**建議**：**A**。

---

## 二、外掛工程

### Q05　外掛輸出端沒有任何限幅

**白話問題**：外掛輸出前沒有 limiter，也沒有 soft clip。
IR 模式補償之後會超過 0 dBFS，有些工廠 preset 彈一個音也會超過。
你聽不到爆音，目前也沒有任何自動偵測。

**背景數字**
- `src/PluginProcessor.cpp:382-395`：effectChain 處理完，只再乘一次 Output 增益就輸出。整個 src 只有 `Distortion.h:73` 用到 tanh。出處：盤點 D9c-clip。
- 最壞情況的單頻增益（用 Python 複製兩條路徑算的，**不是產品 binary**，對實測的誤差在 0.6 dB 內）：
  - ALGO 預設 size 0.5：+24.5 dB
  - 三顆 IR ×26.9：+28.7～+33.2 dB
  - ALGO size 1.0：+37.8 dB
- **本輪 K2 實測**（E16，C4、力度 0.7、單音；只描述，不是 GATE）。出處 `reports/gate_outputs/wf0925_K2_hostprobe.txt:280/300/320`：
  - 7 號 Copper Warm Strings (Body) 峰值 **+0.33 dBFS**
  - 11 號 Ethereal Steel Bells **+1.47 dBFS**
  - 15 號 Bronze Water Gong (Body) **+2.65 dBFS**
  - 最小聲的是 13 號 Rubber Tongue Pad，峰值 −39.79 dBFS。
  - 為什麼會超過 0 dBFS，本卡沒有拆解。
- 26.9 只在 ALGO 預設 size 0.5、沒指定 T60 時才對齊。其他 size 差 −1.4～+4.0 dB，其他 T60 差 −2.4～+5.3 dB（複製版估計）。K1 已把這段依賴寫進 `EffectChain.h` 註解和 D9 裁決包。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 維持＋文件註明 | UI 規格和手冊寫「mix 開大或部分 preset 會超過 0 dBFS，請用 Output 調」 | 使用者要自己注意 | 不會 | S |
| **B** 輸出端加安全限幅 | soft clip 或 limiter | 外掛輸出在超過時會變，至少 3 個工廠 preset 會變；限幅門檻是新常數，要標 DECIDED CONVENTION（R4） | **會（外掛輸出，R10）**；CLI 不經過外掛輸出端，8/8 預期不變 | M |
| **C** 加削波指示燈 | 聲音不動，超過 0 dBFS 時畫面亮燈；可以一起寫進要送設計的 UI 規格 v1.2 | 要改 `PluginEditor` | 不會 | S～M |
| **D** 調低 3 個 preset 的 Output | 只改 preset 7、11、15 | 治標，不治本 | **會（那 3 個 preset，R10）** | S |

**子題 Q05b**：E16 要不要訂「峰值上限／靜音門檻」當 GATE？這是新判準，你要給數字，數字也要能溯源。A＝不加，維持只印數字；B＝加，數字由你另外給。

**建議**：Q05 選 **C**，再加 A 的文件註明，理由是看得到的指示對你最直接。Q05b 選 **A**。

---

### Q06　VST3 Program 參數只暴露工廠 preset（E7）

**白話問題**：DAW 看到的 program 格數，在外掛建立時就固定了。但使用者 preset 會增減，又依名稱排序。結果有三種：
1. 新存的 preset，DAW 叫不到。
2. 名字排在前面的新 preset，會讓舊的編號整體往後移，自動化會載到別的 preset。
3. 換一台電腦，編號就不一樣。

**背景數字**
- `getNumPrograms()`＝工廠 27 個＋使用者 preset 數（`src/PluginProcessor.cpp:987-990`、`src/PresetManager.h:51`，依名稱排序在 `:347-357`）。
- JUCE VST3 wrapper 建立時就固定 `stepCount`（`juce_audio_plugin_client_VST3.cpp:1027-1037`）。
- 「state 還原」這種情況已經用 presetId 補好，上面三種沒涵蓋。出處：盤點 E7。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 只給工廠 27 個 | 使用者 preset 只出現在外掛自己的選單 | DAW 的 program change 叫不到使用者 preset；已經把自動化設到使用者 preset 的舊專案會對不上（目前只有你在用） | 不會（任何 preset 的聲音都不變；外掛行為會變） | S。R6 全套，另跑 HostProbe H7 和 pluginval 的 Plugin programs 測項 |
| **B** 維持＋文件 | 寫明「DAW 的 program 編號只保證前 27 個」 | 三種錯位照舊 | 不會 | 0 |
| **C** 固定格數 | 27 個工廠＋固定 N 個使用者槽，空槽顯示 Empty | 設計較複雜，N 要你定 | 不會 | M |

**建議**：**A**。

---

### Q07　VC++ runtime：靜態 CRT 還是附 vc_redist（E4）

**白話問題**：VST3、Standalone、CLI 三個執行檔，都要靠買家電腦裝好 Microsoft VC++ 可轉散發套件。沒裝的話，DAW 可能載不進外掛。

**背景數字**
- 三個執行檔都 import 了 `MSVCP140.dll`、`MSVCP140_2.dll`、`VCRUNTIME140.dll`、`VCRUNTIME140_1.dll`（`reports/gate_outputs/wf0925_G1_sources.txt` §4）。
- `CMakeLists.txt` 沒設定 `CMAKE_MSVC_RUNTIME_LIBRARY`。
- 兩案細節在 `tools/installer/README.md` §4。

| 選項 | 做法 | 代價 | 前提 | 改聲音？ | 工作量 |
|---|---|---|---|---|---|
| **A**（甲）靜態 CRT | 改 `CMakeLists.txt`，把 runtime 靜態連進執行檔 | C++ lane 要跑 R6 全套 | 要證明 8/8 位元不變；如果 CLI 渲染變了，就依 R10 停下回報 | 預期不會，要驗 | S～M |
| **B**（乙）安裝包附 `vc_redist.x64.exe` | 只改 `.iss`（乙案區塊已寫好、先註解掉） | 要下載，見 Q37-2。Microsoft 的轉散發條件：限持有 Visual Studio 授權的人轉散發（G1 引 Microsoft 文件）。最低版本號**查不到**官方對照 | 你同意下載 | 不會 | S |

**建議**：**A**。不用下載，也不受轉散發條件限制；盤點 E4 的說法是外掛業界多半這樣做。

---

### Q08　外掛↔CLI 一致性：補 GATE，還是把文案收窄（E3）

**白話問題**：物理 GATE 驗的是 CLI 渲染，但買家買的是外掛，外掛走的是另一份組裝程式碼。可是文案主打「可稽核物理鏈」。

**背景數字**
- 衰減律是共用的：`applyStringDecayTimes`，`src/engines/CimbalomEngine.h:121-146`。
- 激發、振幅、macro、BodyResonance、EffectChain 是兩邊各自組裝的：外掛走 `startNote()`，CLI 走 `noteOn()`。
- HostProbe 只驗音高、onset 和 tail 長度（H8），不驗模態頻率，也不驗 T60。
- `ROADMAP_PHYSICS.md:407` 把這項列在 Nice to have。
- 文案寫「可稽核物理鏈」：`docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:95`。
- 本輪 V1 又查到三件只有外掛會發生的事：搶 voice、同音提前制音、FM 舊 voice 不結束（見 Q09）。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 補 parity GATE | HostProbe 載入 VST3（macro 0.5、FX 關），渲染同一份 score，跟 CLI 比模態頻率和 T60。長期把 `startNote`／`noteOn` 抽成共用函式 | 容差要你另外核准、登記進 §6；抽共用函式時可能改到外掛輸出 | 加測試不會；抽共用函式時**可能會（R10）** | L |
| **B** 文案收窄 | 寫「物理驗證只涵蓋 CLI 渲染；外掛即時演奏共用衰減律，激發與效果鏈沒有逐項驗證」。要改 LISTING_COPY、ENGINE_DOMAIN_CLAIMS、KNOWN_LIMITS | 賣點說得比較保守 | 不會 | S |
| **C** 先 B，A 排後續 | 上架前先收窄文案，parity GATE 另排 | — | 不會 | S，之後 L |

**建議**：**C**。

> **2026-09-25 WF0925b**：行號更正（WF0925b-DS 查到，DS／BR 稽核 PASS）——上面「`ROADMAP_PHYSICS.md:407`」指錯了，:407 是 M7 段尾的 `---`；「Plugin ↔ CLI 一致性驗證」在 Nice to have 第 1 條 **`ROADMAP_PHYSICS.md:441`**（`docs/KNOWN_LIMITS_INDEX.zh-TW.md` B5 引的也是 :441）。DS 同步 ROADMAP 時刻意沒讓原本的 483 行位移，本包其他 ROADMAP 行號（:144、:161、:164、:171、:474-479）仍然正確。選項不受影響。

---

### Q09　外掛 16 顆 voice 會不會搶音（V1）

**白話問題**：外掛每個引擎只有 16 顆 voice，用完就搶最舊的。CLI 沒有這個限制，每個事件各用一顆 voice。

**背景數字**（出處 `reports/voice_pool_occupancy_2026-09-25.zh-TW.md` §0、§4、§5；全部是照程式碼規則推算的估計，**不是外掛實測**）
- **要上架的 50 件商品**，照正常彈法都不會超過 16 顆：
  - 給愛麗絲兩版最多 12 顆
  - AI Radiance 最多 8 顆
  - 音效包最多 4 顆
- **全 corpus 75 首**裡，有 3 首超過，都不是商品：
  - 月光全曲（FM）196 顆，其中 184 顆的音量已經低於 −138.5 dB 參考線
  - 月光舌鼓版 20 顆，會搶 64 次
  - 混合版的舌鼓部分 20 顆，會搶 41 次
- **假設全程踩延音踏板**，有 4 件商品超過：給愛麗絲兩版各 22 顆、AI Radiance 全曲 FM 19 顆、第三樂章 FM 17 顆。
- 四季：外掛沒有 `damping_override`，所有弦樂塞進同一個外掛時，12 個樂章有 6 個超過（最多 26 顆）；一個聲部一個外掛就 0 個超過。
- **加大 pool 也解決不了的兩件事**：
  - 同音提前制音：給愛麗絲有 21 顆會提早開始制音。
  - FM 同音反覆時，舊 voice 一直不結束。
- CPU 代價（估計，只當量級看；每一顆一直在響的 voice）：
  - Cimbalom 彈鋼琴 2.55～2.71% 單核
  - Cimbalom 彈弦樂 1.37～2.28%
  - Chromatic 0.10～0.16%
  - 例：Cimbalom 從 16 顆加到 26 顆，滿載約多 14～27% 單核。
- 這個模型拿 8 顆單音驗證過：「voice 什麼時候停」的誤差最大 6.9 ms。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 加大 pool | 例如 Cimbalom 16→26、Chromatic 16→20（`PluginProcessor.cpp:36/71/105`） | 多吃 CPU；解決不了同音制音和 FM 問題 | **會（外掛密集段，R10）**；CLI 8/8 不受影響 | S |
| **B** 寫進主張域 | 文案和 ENGINE_DOMAIN_CLAIMS 寫明：16 顆、照 JUCE 規則搶、照 JUCE 同音規則、GATE 只涵蓋 CLI | 無 | 不會 | S |
| **C** 維持 | 不改 | 買家踩踏板彈密集段，或多聲部塞同一個外掛時，會被搶音 | 不會 | 0 |
| **D** B＋補實測 | 先 B；再授權 AI 改 `tests/host_probe.cpp`，讓外掛串流演奏同一份 MIDI，跟 CLI 逐事件比，量出實際被搶的音 | 要改測試檔（R6/R7） | 不會 | M |

**子題 Q09b（FM 舊 voice 不結束）**：A＝修。例如讓 `Envelope::noteOff()` 遇到已經在 Release 的 voice 時不重算。這會改 FM 外掛輸出（**R10**），CLI 理論上不受影響，但要驗 8/8。B＝不修，寫進主張域。
**子題 Q09c（同音提前制音）**：A＝改，要自訂 `findFreeVoice`／noteOff 邏輯（**R10**，外掛行為會變）。B＝不改，寫進主張域。

**建議**：Q09 選 **D**，Q09b 選 **B**，Q09c 選 **B**。先記錄，等 D 的實測數字回來再決定要不要動程式。

---

### Q10　D12：IR 載入失敗的分支、情境 3 的舊鍵

**白話問題**：舊專案存的 IR 路徑，如果檔案還在、但載不進來（超過 30 秒、讀不到、匯入失敗），外掛會靜默丟掉這條路徑，不跳警告。你之後一存檔，這個 IR 的線索就永遠消失了。
相比之下，「檔案不存在」的分支反而會警告。
另外，新舊格式同時存在的情況下（情境 3），舊的 `reverb_ir_path` 鍵不會被清掉。

**背景數字**
- 這是刻意的設計：`src/PluginProcessor.cpp:875-881` 的註解有寫，`importError` 算出來之後沒被使用。這個情況也不在 D12 卡的規格內。出處：盤點 D12-failpath 查證修正。
- 情境 3 的舊鍵：`:621-645`，`removeProperty` 只在遷移分支裡。
- K1 已經在情境 1、2 加上「輸出的 state 不含 `reverb_ir_path`」的斷言。
- 稽核的邊角記錄：state_version 比 3 新、又帶舊鍵時，這次載入會跳過遷移，舊鍵留著。下次存檔標成 3，再讀時才照 D12 遷移。照目前的程式脈絡，實務上碰不到。
- 聲音：不論選哪個，IR 沒載入時音訊都走 ALGO，所以**聲音不變**。差別只在 UI 有沒有警告、state 裡留不留舊鍵。

| 選項 | 做法 | 改聲音？ | 工作量 |
|---|---|---|---|
| **A** 全部維持 | — | 不會 | 0 |
| **B** 兩件都做 | 失敗分支改走「缺檔三態」：跳警告、附失敗原因、保留原檔名。情境 3 也清掉舊鍵。HostProbe 補一個「檔案存在但超過 30 s」的情境 | 不會 | S（R6 全套） |
| **C** 只做失敗分支警告 | 舊鍵不動 | 不會 | S |
| **D** 只清情境 3 的舊鍵 | — | 不會 | S |

每個選項都一樣：「比 3 新的 state」那個邊角不處理，只記錄。

**建議**：**B**。

---

### Q11　B7 槌速函式在 MIDI 20 跳 2.3 倍

**白話問題**：`hammerVelocityMps()` 用公式算到 MIDI 20 是 0.412 m/s，但 MIDI 19.9 被夾到實測下限 0.18 m/s，中間跳了 2.29 倍。上界 MIDI 120 是 6.589→6.8，只跳 3%。
文件說這是「比照 `interpAnchorsFlat()`」，但那個函式是連續不跳的。

**背景數字**
- 程式碼：`src/physics/HammerImpulse.h:388-395`。測試 `tests/physics_models_repro.cpp:1144-1155` 把 0.18 和 6.8 釘住了。
- 這個函式**目前沒有任何呼叫點**，所以不影響現在的聲音。
- B7 Phase 2/3 是 09-15 裁決的 BLOCKED。出處：盤點 B7-clamp。

| 選項 | 做法 | 改聲音？ | 工作量 |
|---|---|---|---|
| **A** 夾到公式邊界值 | 0.41／6.59，連續；改測試釘值 | 不會（沒有呼叫點） | S |
| **B** 保留實測極值 | 0.18／6.8；文件改寫成「邊界不連續」 | 不會 | S |
| **C** 先不動 | 等 B7 重啟時再裁 | 不會 | 0 |

**建議**：**C**。

---

### Q12　CI：多行指令只看最後一個 exit code

**白話問題**：GitHub 的 Windows runner 跑多行指令時，只看最後一行的結果。所以排在前面的 ctest、pytest 就算失敗，整步還是綠燈。
這是 P1 稽核抓到的既有問題（級別：要修），不是 P1 造成的。

**背景數字**
- 受影響的地方：
  - `.github/workflows/release-physics.yml:54-57`：ctest、pytest、`--selftest`、`--full` 四行寫在同一步。
  - `.github/workflows/physics.yml:99-100`：pytest 失敗，會被後面的 `--selftest` 蓋掉。
- 本機用 pwsh 7.6.6 照 GitHub 的包法模擬：前兩個指令分別 exit 8、exit 1，整步結果還是 exit 0（`output/wf0925/P1_audit/pwsh_mask_sim.txt`）。
- HostProbe 那一步有自己明寫 `exit $code`，不受影響。
- 另一條 note：`physics.yml` 把 HostProbe 步驟放在 pytest、T60、`--full`、整曲 smoke 之前（`:59-95`）。如果 runner 上載不進 VST3，後面這些 gate 都會被跳過。
- P1 的 CI 改動在本機只驗到 YAML 能解析；真的跑起來會怎樣，要 push 之後才看得到（見 Q33）。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 修＋調次序 | 授權 AI 開卡：每個指令後檢查 exit code，或拆成獨立步驟。HostProbe 移到其他 gate 之後，或加 `if: always()`。push 後看 `physics.yml`，再手動觸發一次 release workflow | 改 `.github` 要 push 才驗得到（你動作） | 不會 | S |
| **B** 只修 exit code | HostProbe 次序不動 | 上面那條 note 的風險還在 | 不會 | S |
| **C** 先不修 | — | 知道 release CI 目前的「綠」不可信 | 不會 | 0 |

**建議**：**A**。

> **2026-09-25 WF0925b**：**已處理（先做 A）**——月月 09-25「都處理掉」授權下，WF0925b-TF 已照 A 做，**可推翻**（回 B：把兩支 workflow 的 HostProbe 移回原位、拿掉 build job 的 outputs 和 corpus job 的 `if`；回 C：整個還原 TF 對兩支 workflow 的改動）。做法：兩支 workflow 共 14 個多行 `run:` 區塊逐一檢查，每行原生指令後面補 `if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }`；HostProbe 移到各自 job 最後（release 的 corpus job 改看 `cli_uploaded`，HostProbe 失敗時 corpus 照跑、整條仍是紅燈）。本機照 runner 包法模擬「只讓一個指令失敗」：改前 12 種被蓋掉 → 改後 0 種（TF 30 種情境、稽核自寫 31 種；稽核 PASS）。**還沒在 GitHub 上跑過**，push（Q33）後看 `physics.yml` 那次 run，再手動觸發一次 `release-physics.yml`。改動 staged 未 commit。證據 `reports/gate_outputs/wf0925b_TF_q12_yaml.txt`、`wf0925b_TF_q12_pwsh_sim.txt`、稽核 `wf0925b_TF_audit.txt`。

---

### Q13　CI 的 Linux 標成 clang，實際用的是 GCC

**白話問題**：CI 裡 Linux 那條寫著 `ubuntu-24.04-clang`，但實際編譯器是 GCC 13.3。
跨平台容差是 08-22 登記的，當時的說明文字也寫成 clang，但用的其實是 GCC 的資料。

**背景數字**
- `physics.yml:175-176` 的 label 是 `ubuntu-24.04-clang`，但沒有設定 CC/CXX。
- CI run 34880536096 的 log：「The CXX compiler identification is GNU 13.3.0」。出處：盤點懷疑者補抓。
- `scores/crossplatform_tolerance.json:4` 的 `_basis` 寫「ubuntu-24.04/clang」。上傳的檔名也帶 clang（`physics.yml:264`）。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 名字改成真的 | label 改成 `ubuntu-24.04-gcc`；`_basis` 文字改成 GCC 13.3（**數值不動**）；上傳檔名跟著改 | 動到已登記容差檔的文字，要你點頭；要 push 才驗得到 | 不會 | S |
| **B** 讓 CI 真的用 clang | 設定 CC/CXX | 容差是用 GCC 資料訂的，換編譯器可能要重量，甚至超標 | 不會 | M |
| **C** 維持 | 在交接文件記一句「名字跟實際不符」 | — | 不會 | 0 |

**建議**：**A**。

---

### Q14　pluginval＋Steinberg validator 重驗（**需要下載**）

**白話問題**：外掛的相容性驗證，上一次是 08-06（pluginval strictness 10＋Steinberg validator 47/47，DEVLOG:390，沒留 log）。之後這些會影響 DAW 相容性的改動，都還沒重驗：
- tail 快取（09-07）
- IR state（09-08）
- D12、D9c
- 本輪 K1 的三項：
  - E9：tail 改由計時器更新，參數變了最多晚 50 ms 才反映，沒在真的 DAW 驗過
  - E14：state_version
  - E15：IR 匯入的原子替換

本機沒有 `pluginval.exe`，也沒有 `validator.exe`。

**背景數字（本卡用 GitHub API 查的，只抓資料，沒下載任何檔。命令見附錄 B）**

| 項目 | 查到的事實 |
|---|---|
| pluginval 最新版 | `v1.0.4`，2024-12-04 發佈。前 5 個 release 都不是 prerelease，v1.0.4 就是最新版，跟 `release-physics.yml:13` 釘的版本相同 |
| Windows 檔 | `pluginval_Windows.zip`，**2,408,590 bytes**，網址 `https://github.com/Tracktion/pluginval/releases/download/v1.0.4/pluginval_Windows.zip`。API 沒提供雜湊，下載後要比對 `release-physics.yml:14` 釘的 SHA256 `c08e61ce3b96db41636f8ec7e76f4c7e2c13ebdac7fa1b5a1f52b4f32ec715ab`。**zip 裡是執行檔** |
| Steinberg validator 的取得方式 | 沒有現成執行檔，要從 VST3 SDK 原始碼自己建（跟 CI `release-physics.yml:104-112` 同一套做法）：`git clone --filter=blob:none https://github.com/steinbergmedia/vst3sdk.git`，checkout 釘住的 commit `58f8da79…`，只抓 4 個 submodule（`base`、`cmake`、`pluginterfaces`、`public.sdk`），再用本機 MSVC 建出 `validator.exe` |
| 釘住的 commit 是哪版 | `58f8da79`（2025-11-17）＝`v3.8.0_build_66`（2025-10-20）再加 2 個 commit。compare API 顯示 ahead 2、behind 0，兩個 commit 都只改授權文字。JUCE 附的 SDK 也是 3.8.0 |
| 大小 | GitHub API 的 size 欄（單位 KB，是 GitHub 上含歷史的儲存大小，**實際抓下來多大本卡沒實測**）：vst3sdk 2,746、vst3_base 568、vst3_cmake 349、vst3_pluginterfaces 261、vst3_public_sdk 17,610，合計 **21,534 KB（約 21 MB）** |
| 不需要的部分 | SDK README:143 寫 `git clone --recursive`，這會連 `vst3_doc`（269,681 KB）和 `vstgui`（15,670 KB）一起抓。CI 刻意不抓這兩個 |
| 最新 SDK | `v3.8.1_build_84`（2026-08-11）。建議沿用 CI 釘的 commit，不升版 |
| Steinberg 官網的 SDK zip | developers 頁面是 JavaScript 產生的，本卡抓不到下載連結和大小（**查不到**） |

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 本機下載＋建置 | 你同意下載 pluginval_Windows.zip（約 2.4 MB）和 SDK 原始碼（約 21 MB 以內）。AI 驗 SHA256、建 validator，跑 `tools/validate_plugin.ps1 -Strictness 10`，log 存 `reports/gate_outputs/`。下載物放 gitignored 資料夾 | C 槽只剩 20 GB（Q36） | 不會 | S～M |
| **B** 不在本機下載 | 先 push（Q33）、修 CI（Q12），再手動觸發 `release-physics.yml`，在 GitHub runner 上跑 | 要等 push 和 CI 修好；runner 能不能無頭載入外掛，還沒驗過 | 不會 | S |
| **C** A＋B 都做 | A 先驗現在的 build，B 之後當常規 | — | 不會 | S～M |
| **D** 暫不重驗 | — | 發版前一定要補 | 不會 | 0 |

**建議**：**C**。

---

## 三、物理與音色

### Q15　給愛麗絲鋼琴版母帶：16 顆弱基頻（D16）

**白話問題**：鋼琴槌敲弦的力道，在頻譜上有幾個「洞」。給愛麗絲鋼琴版有 16 顆音的基頻剛好掉進洞裡，基頻被壓到幾乎沒聲音。
準備上架的母帶就含這 16 顆。要先上架，還是修好再上？

**背景數字**
- 16 顆 FAIL 的位置：
  - E5@0.278 共 9 顆
  - A5@0.427 共 3 顆、A5@0.452 共 1 顆
  - A6@0.427 共 2 顆
  - A#6@0.427 共 1 顆
- 16 顆全部在洞裡，基頻被多壓掉 14.9～24.5 dB。
- 真正分開 PASS 和 FAIL 的是基頻音量本身：FAIL 全部 ≤ −72.1 dBFS，PASS 全部 ≥ −67.2 dBFS。對既有的 −70 dBFS 門檻，677 PASS／16 FAIL，0 誤判。
- 這是 A14 B-2 造成的：洞在的事件數，舊公式 44 顆、現行 47 顆。洞沒有變少，只是換了位置。
- 以上出處：`reports/weak_fundamental_null_map_2026-09-25.zh-TW.md` §0、§4。
- **商品中只有給愛麗絲鋼琴版受影響。** 揚琴版 0 顆、AI Radiance 五軌 0 顆、43 個音效 0 顆。N1 只掃了弦類引擎的事件；商品稽核提醒，文案寫「0 顆」時要註明範圍。
- 本輪 V1 另外量到：這 16 顆用泛音反推的基頻，16/16 都 PASS（−3.56～+1.33 c）。也就是說，音高本身是對的，問題只在基頻太小聲（`reports/partial_verify_full_2026-09-25.zh-TW.md` §4）。
- 選 A 需要的「已知限制」那行文字，X2 已經寫進候選版 `PRODUCT_SHEET_v1_1.md` §2.2 了。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 帶已知限制上架 | 母帶不動；文案補「已知限制」；把 16 顆的時間點交給聽人（Q28）重點聽 | 沒修到 | 不會 | 0（文字已備） |
| **B** 等文獻 | 等 A14 B-1 需要的付費牆文獻（D10：Hall 1988、Chaigne & Askenfelt Part II），拿到真實脈衝形狀再改 | 時程未知；修好後商品要重渲 | **會（所有 piano／felt，R10）** | M |
| **C** 第一原理研究 | 不等文獻，數值解「槌＋弦」的接觸過程。要同時比三種：無耗散、加 Stulov 遲滯、半正弦（盤點 E1-a14-b1 查證修正）；純冪次律未必能消掉洞 | 結果未知 | **會（R10），而且是新的物理主張** | M～L |
| **D** 只改這首的力度 | 改 `fur_elise_complete.score.json` 裡落在洞裡的音。E5、A5 調 1～1.6 dB 就能離開洞；A6、A#6 要往上調才有效 | 只繞過這一首，洞還在 | **會（只改這首，R10）** | S |

**建議**：**A**（跟 N1 報告的看法相同）。B 留著當根本修法。如果聽人說這幾顆聽得出怪，再對這一首做 D。

> **2026-09-25 WF0925b**：已補範圍——WF0925b-XF 在 `PRODUCT_SHEET_v1_1.md` 的「0 顆」後面補上「N1 只檢查弦類引擎（piano／cimbalom／string）的事件」，並寫出 43 個音效裡只有 14 顆是弦類事件（稽核核對跟 N1 報告 §5 一致）。選項與建議不變。證據 `reports/gate_outputs/wf0925b_XF_verify.txt`（V5）。

---

### Q16　D11 要不要依 F5 根因結果重開 A/B

**白話問題**：09-15 你選了 C，意思是先查清楚 F5 為什麼退化。現在查清了：候選修正讓 C4 的 T60 從 4.14 秒縮到 2.67 秒，F5 的量法會把「衰減變快造成的頻譜洩漏」算成殘餘能量。這不是模型沒預測到的能量。
問題是：候選修正要不要落地？

**背景數字**
- 出處：`reports/decision_packets/D11_string_scale_candidate.zh-TW.md` 檔尾「F5 根因調查結果」；`reports/d11_f5_root_cause_2026-09-25.zh-TW.md`。
- 非諧性係數 B 對量測值的偏差倍數：G5 從 21.6× 變 7.6×，G6 從 86.4× 變 18.7×。
- 在現行規則下（F5 會影響 exit code、−60 dB 是 07-23 核准的門檻、R2 禁止放寬），**候選落地後 `--full` 會是 FAIL（−58.5 dB）**。
- 候選會改整個鍵盤的 T60。相對 0.8 mm 樂譜：C4～C7 短 22～36%，A0～C2 長 15～92%。哪一邊比較像真鋼琴，還沒評估。
- 現狀也不穩：現在 F5 會 PASS，是因為探針預設弦徑 0.8 mm。探針改成 1.0 mm（跟 `physical_piano.score.json` 一樣）就是 −59.5 dB FAIL；0.95 mm 是 −60.6 dB。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 落地完整候選 | 套用 `reports/d11_string_scale_candidate.patch` | 另外要你裁 3 件事：F5 量法要不要改（改 GATE 量法，另案）、纏繞弦怎麼處理、弦徑旋鈕還能不能調 | **會（5/8 代表曲變，R10）** | M |
| **B** 維持現狀 | 候選繼續存檔 | 高音非諧性偏差照舊；F5 PASS 依賴探針 0.8 mm | 不會 | 0 |
| **C** 落地中間版（只換弦長） | F5 −63.1 dB PASS；1.0 mm 樂譜的 B 偏差 G5 9.6×、G6 27.0× | 中高音 T60 變短（A4 1.72→1.52 s）；其他 GATE 還沒跑過 | **會（R10）** | M |
| **D** 維持＋研究卡 | B 的內容，再加兩件：把「F5 PASS 依賴探針 0.8 mm」登記進 TODO 當已知脆弱點；另開研究卡，找真鋼琴 T60 的文獻對照候選，並研究 F5 量法可以怎麼改。查完第三次重開 | 要多一張卡 | 不會 | S＋研究 |

**建議**：**D**。

---

### Q17　舌鼓 BeamModel 的 ×2 阻尼

**白話問題**：舌鼓的阻尼公式裡有一個「×2」，找不到任何文獻出處。要保留、拿掉，還是換成文獻那一套？

**背景數字**（出處 `docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md` §0、§4）
- 文獻**反對把 ×2 當成物理機制**：8 份全文沒有任何一份用「材料損耗乘固定倍數」。
- 但文獻**無法判斷它的總量該不該留**。以鋼舌片 262 Hz 為例：
  - 已知機制加總（只描述）是 0.11～0.36 /s
  - 模型乘 1 是 0.257 /s，乘 2 是 0.421 /s
  - 支撐損耗（舌片接鼓身）文獻給不出數字，只會讓總量更大。
- 新發現：模型的衰減完全不看舌片厚度。出貨的樂譜有三種厚度（鋼 3.2、鋼 2.6、鋁 2.0 mm）。文獻的熱彈性在這三種厚度之間差 2.56 倍，模型差 0 倍。
- 拿掉 ×2 的效果：鋼 C4 的 T60 從 16.39 s 變 26.86 s，C3 從 35.15 s 變 60.38 s。

| 選項 | 做法 | 改聲音？ | 工作量 |
|---|---|---|---|
| **A** 保留並改標 | 不動 ×2；註解和主張域改寫成「DECIDED CONVENTION，經驗係數，無文獻錨點」 | 不會 | S |
| **B** 拿掉 | 刪掉 `* 2.0f` | **會（所有舌鼓事件，R10）** | M |
| **C** 換成文獻的機制分解 | 熱彈性＋空氣黏性＋輻射＋支撐。衰減函式要能拿到厚度，缺的來源還很多 | **會（全部，R10）** | L |
| **D** A＋先算數字 | 先 A；同時讓 AI 在 scratch 副本算 B 的前後數字（L1 說不用等裁決就能做），數字回來再裁 A/B/C | 不會 | S |

**建議**：**D**。

> **2026-09-25 WF0925b**：**已補數字（D 的「先算數字」那半；「先 A」改註解那半沒做）**——WF0925b-BR 在 staged 樹的隔離副本只刪 `BeamModel.h:54` 的 `* 2.0f`，建兩支 CLI 比前後，主工作樹沒動（DS／BR 稽核 PASS：稽核對過副本跟 index 樹只差這一行，用兩支 CLI 自己重跑 8 首、抽 3 個音高重跑 T60、corpus 抽 2 檔重算，都對得上）。全部是描述用、非 GATE：鋼基頻 T60 變長 1.15～1.80 倍（C3 35.15→60.38 s、C4 16.39→26.86 s），鋁 1.11～1.73 倍（C4 30.135→46.965 s），黃銅、玻璃、竹、木頭接近 2 倍，頻率完全不變；corpus 75 份裡用到 BeamModel 的 39 份全變、其餘 36 份逐位元相同；8 首基準變 3 首（月光空靈鼓版、月光揚琴＋空靈鼓混合版、ai_radiance_m1）；商品 clean_batch2 50 件裡 36 件會變（音效 32＋AI Radiance 4）；會變的檔峰值不變（都有正規化），全檔 RMS −1.1～+3.0 dB，最多長 0.77 s（音效）／2.6 s（月光）；`--full` 兩版都 NO CHECKED FAILURES（但這類檢查 ×1、×2 都會過，分不出哪版像真舌鼓）；對照 D1 已引述的文獻 7 個點，現行 0 個、拿掉 ×2 只有 1 個（鋼 C4）落在範圍內。報告沒有替你選。報告 `reports/beam_x2_option_b_before_after_2026-09-25.zh-TW.md`（選 B 的後續清單在 §6）、資料與圖 `reports/beam_x2_option_b/`、證據 `reports/gate_outputs/wf0925b_BR_*.txt`（6 檔）、稽核 `wf0925b_DS_BR_audit.txt`。

---

### Q18　partial_verify 的期望值慣例、要不要升 GATE

**白話問題**：`partial_verify` 第一次跑完給愛麗絲全曲 905 顆（只資訊用，不判定）。
結果：5,428 個泛音格，量到 5,426 個，PASS 4,577、FAIL 849，另外 2 個拒量。
849 個 FAIL 裡，848 個偏高。原因是工具拿「第 0 根弦」當期望值，但每顆音 3 根弦的平均比第 0 根高約 +5 c。

**背景數字**（出處 `reports/partial_verify_full_2026-09-25.zh-TW.md` §2、§3、§5）
- 扣掉 3 弦平均的偏移之後，FAIL 那群的偏差中位數只剩 +0.03 c。
- 如果改用 3 弦平均當期望值，會有 120 個超出，其中 97 個是 A2 的 n=1。這是量測器低音區的既有缺口。
- 本輪 P1 只更新了 `gate_ready` 的理由字串；工具報告裡的 caveats 還寫「C10 待裁」，這是小修，列在 §7。

| 選項 | 做法 | 改聲音？ | 工作量 |
|---|---|---|---|
| **A** 維持資訊用＋寫明 | 工具說明和 EARFREE 文件寫明「期望值取第 0 根弦，3 弦平均高約 +5 c」 | 不會 | S |
| **B** 改用 3 弦平均 | 期望值改成 3 弦加權平均，仍只資訊用 | 不會 | S～M |
| **C** B＋升成 GATE | 照 A13 原規劃只判持續段，升成 GATE（±5 c 沿用 f0 列）。升之前再給你一版數字 | 不會 | M |

**子題 Q18b**：A13 那 22 顆重量之後，D7（−5.48 c）和 G6（−5.10 c）用泛音反推的基頻 FAIL，但直接量基頻是 PASS（+0.001、−0.162 c）。A＝開小卡追查；B＝只記錄。

**建議**：Q18 選 **A**，Q18b 選 **B**。

> **2026-09-25 WF0925b**：背景裡那條「caveats 還寫『C10 待裁』」**已處理**——WF0925b-TF 把 `tools/partial_verify.py` 的 docstring 與 `caveats[0]` 改成現況（C10 09-10 選 A、D15 09-15 選 A'，升 GATE 要你另裁），`gate_ready` 仍是 false（TF 稽核 PASS）。WF0925b-DS 已把本題的全量數字寫進 EARFREE §8.6，`:420-421` 也寫了「期望值取第 0 根弦、3 弦平均約高 +5 c」（描述用、非判定）；A 案要的「工具說明也寫明」那半**還沒做**。另外 DS 查到：EARFREE §8.6 裡 09-09 的可發布措辭「22 顆 pitch_via_partials 全數 PASS」對現行 binary 已不成立（現在 20/22，就是 Q18b 那兩顆），DS 只加註、沒改原句，新措辭等你核定。證據 `reports/gate_outputs/wf0925b_TF_summary.txt`、`wf0925b_DS_changes.txt`。

---

### Q19　9 條已知限制要不要升格成正式引擎主張

**白話問題**：G1 整理了 `docs/KNOWN_LIMITS_INDEX.zh-TW.md`，§C 列出 9 條候選，問要不要寫進 `docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md`，成為正式主張。每條是二選一：「甲＝升格」或「乙＝不升格」。

| # | 候選 | 原句出處 |
|---|---|---|
| C1 | FM Piano 域外（不是物理合成） | `ROADMAP_PHYSICS.md` §0 :144 |
| C2 | Custom Harmonics 半域內 | 同 §0 :143 |
| C3 | Cimbalom／Piano 振幅含 creative 層和校準層 | TODO :833、:813-816；§0 :140 |
| C4 | `frequency_mode: midi` 是混合系統 | §0 :147 |
| C5 | 弦長／弦徑模型假設 | D11 裁決包 §0（跟 Q16 連動） |
| C6 | 舌鼓 BeamModel ×2 經驗阻尼 | `BeamModel.h:44-48`（跟 Q17 連動） |
| C7 | Chromatic 槌具沒有標定 | TODO :430 |
| C8 | 絕對聲壓輸出是慣例錨定 | TODO :897-901 |
| C9 | 外掛 16 voice 跟 CLI 的差異 | V1 報告 §6（跟 Q09 連動） |

| 選項 | 做法 |
|---|---|
| **A** 全部甲 | 9 條都升格 |
| **B** 全部乙 | 都不升格，只留在索引和原出處 |
| **C** 逐條 | 回覆時寫「C1甲 C2乙 …」 |

都不改聲音，工作量 S（交接卡或文件卡做）。

**建議**：**C**。C1～C4、C7、C8 選甲：原句已經在 ROADMAP §0 或 TODO，事實清楚。C5、C6、C9 等 Q16、Q17、Q09 裁完再定。

---

## 四、商品（音效包、專輯、合成器）

> 候選版全部放在 `exports/products/clean_batch2_v1_1_candidate/`（gitignored）。原版 `clean_batch2/` 的 212 個檔一個都沒動過：X1、X2 和商品稽核各自用兩種方法核對過 sha256。
> 打包腳本 `scripts/x2_build_packages.py` 已經把 Q25、Q26、Q20、Q27 做成開關。你選完，重跑一次就是對應的 zip。
> 授權草稿還有 DRAFT 或 [TBD] 時，腳本會拒絕 `--release`。
> **商品稽核目前 FAIL 一條，AI 修，不需要你裁**：README 三語寫 loop-ready 檔循環時「逐樣本相同」，說得太滿了。實際交付檔還多了一個整體增益和 24-bit 捨入。修好後要重打 zip、重跑 `x2_verify`。
>
> **2026-09-25 WF0925b**：**已修，商品稽核複驗 PASS**——WF0925b-XF 改了三語 README（一般版、Fab 版）的 loop 說法，順手修了稽核的四條 note（秒數只捨入一次、真峰值寫成三支量測器的實測範圍、「0 顆」補範圍、阻尼措辭改保守），重打 zip，`x2_verify.py` 134/134；原版 `clean_batch2/` 212 檔仍然一個都沒動。新 zip：SE 一般版 `50749a0e…`、SE Fab 版 `082b8e69…`（只有 README 成員變，音檔沒動）；專輯 `049339ed…`、試聽包 `38ac5b45…` 沒變。X1／X2＋XF 共 24 個證據檔已 stage。入口 `CHANGES_v1_1.md` 開頭「XF」段；§0 待確認從 10 項變 12 項（加專輯授權 O05、DistroKid O18）。證據 `reports/gate_outputs/wf0925b_XF_*.txt`（9 檔）；稽核判定只在回報和 `output/wf0925b/XF_audit/`（gitignored），摘要見 `docs/workcards/WF0925_README.md` §7-1。

### Q20　音效包響度政策

**白話問題**：43 個音效，現在每一個都把峰值拉到 −1 dBTP。結果三個打擊音效（開頭有尖峰）聽起來比其他小聲很多。要不要換一種對齊方式？

**背景數字**（出處 `QA_REPORT.md` §4）
- 現行（A 案）：整包最大瞬時響度 −28.4～−5.4 LUFS，差 **23.0 LU**。
- B 案（每檔最大瞬時響度 −10 LUFS，但不超過 −1 dBTP）：
  - 差距縮到 **18.3 LU**
  - 21 檔撞到 −1 dBTP 上限，沒辦法再拉大
  - 三個打擊音效還是很小聲：Rabbit Stomp −28.3、Spring Release −24.9、Shackle Slam −22.4
- 其他目標值（只計算，沒做成檔，只描述）：
  - −14：8 檔撞上限，差 14.3 LU
  - −20：3 檔，差 8.3 LU
- 要把打擊音效拉上來，只能加限幅器，會改變聲音。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 現行 | 全部 −1 dBTP | 差 23.0 LU | 不會 | 0 |
| **B** −10 LUFS 上限 | 用 X1 已做好的 `alt_loudness/` | 22 檔變小聲；打擊音效沒改善 | 不會（音量變，音色不變） | 0（已做好） |
| **C** 其他目標值 | 回覆時寫數字，例如「C −14」 | 目標越低，整包越小聲 | 不會 | S |
| **D** 加限幅器拉打擊音效 | — | 尖峰算不算瑕疵，要聽人判斷 | **會** | S＋聽人 |

**子題 Q20b**：現行 distribution 有 4 個音效，全精度真峰值略高於 −1.000 dBTP（−0.966～−0.970）：Bird Call (Alarm)、Lock Click、Ticking Room、Acorn Tap。原因是舊腳本用 0.1 dB 精度的摘要算增益。
商品稽核用另一支量測器量，0.01 dB 以下的讀數會跟著量測器變。例如 Bird Call (Alarm) 量到 −1.007／−0.999。
A＝用全精度重出；B＝不重出，文案寫「約 −1 dBTP」。

**建議**：Q20 選 **A**。改動最少，打擊音效小聲是尖峰本身的性質，README 寫明就好。Q20b 選 **B**。

> **2026-09-25 WF0925b**：已補數字（文字照實，音檔沒動）——WF0925b-XF 把 README 與 `LISTING_COPY_v1_1.md` 政策 A 的真峰值說法，從「−0.97～−1.05」改成三支量測器合起來的實測範圍 **−0.949～−1.048 dBTP**，註明「同一檔在不同量測器最多差 0.07 dB（XF 實測最大 0.0654），小數後幾位看量測器」；B 案說法改成「設定增益用的那支量測器 ≤ −1.000，其他量測器最多讀高 0.07 dB」。這只是把現況寫實，**不等於替 Q20b 選 B**；要不要用全精度重出（Q20b A）照舊等你。第四支量測器讀到 −0.94886，比印出的 −0.949 高 0.00014 dB（README 寫的是三支量測器的範圍，不算寫錯；描述用、非 GATE）。證據 `reports/gate_outputs/wf0925b_XF_tp_meters.txt`、`wf0925b_XF_recheck.txt`。

---

### Q21　AI 揭露口徑

**白話問題**：音效包的文案要不要說明 AI 參與了哪些部分？

**背景數字**
- 音效譜的 8 個新增 commit，都帶 AI 共同作者 trailer。這是商品稽核核對的事實。
- 專輯已經揭露了 AI 參與，音效包沒有，兩邊說法不一致（盤點 R8）。
- X2 的建議句：「AI 輔助編寫譜面，由 TsukiSynth 物理引擎演奏；未使用 AI 音訊生成」。已經寫進 README、LICENSE 第 11 條和文案，都標了【待月月確認】。
- 各平台的 AI 揭露規定、DistroKid 的 AI 表單，本卡**沒有查證**。

| 選項 | 做法 |
|---|---|
| **A** 採用建議句 | — |
| **B** 你自訂 | 回覆時附上句子 |
| **C** 不揭露 | 跟專輯說法不一致 |

都不改聲音，工作量 0～S。

**建議**：**A**。

> **2026-09-25 WF0925b**：背景裡「DistroKid 的 AI 表單本卡沒有查證」**已查到能查的程度**（O18，WF0925b-XF）：DistroKid 說明中心 12 篇都回 HTTP 403（沒有繞過），只拿到搜尋摘要——上傳表單的 AI 選項（歌詞／音樂／全部音訊）有沒有「部分音訊」，三次搜尋兩次有、一次沒有，**要你登入 DistroKid 確認**。選項與建議不變。見 `exports/products/clean_batch2_v1_1_candidate/DISTROKID_NOTES.md`（K1～K7）、證據 `reports/gate_outputs/wf0925b_XF_web_sources.txt`。

---

### Q22　音效包授權 v1.1 草稿要不要採用

**白話問題**：v1.0 的授權有 5 個漏洞（盤點 R6）：誰有授權、AI 訓練、Content ID、遊戲和開源 repo、終止條款和準據法。
X2 寫了三語草稿 `LICENSE_SE_PACK_v1_1.txt`，**不是法律意見**。

| 選項 | 做法 |
|---|---|
| **A** 採用草稿架構 | 你填 [TBD] 後定稿 |
| **B** 先請律師看 | 費用本卡沒查 |
| **C** 維持 v1.0 | 5 個漏洞都還在 |

**子題**（草稿預設都是 A，細節見 `CHANGES_v1_1.md` §2.5）
- **Q22b 第 4 條（公開原始碼 repo）**：A＝可以放，但限實際用到的專案，要放獨立資料夾加聲明檔；B＝不可以放進公開 repo。
- **Q22c 第 6 條（Content ID）**：A＝音效跟大量原創內容結合的較大作品可以登記，但要撤回誤認領；B＝一律不可以登記。
  X2 的描述：A 對「用音效做歌」的買家比較友善；B 最不會害到其他買家。
- **Q22d 以哪個語言版本為準**：A＝英文；B＝中文。

還要你寫出來的 [TBD]：授權通路清單、第 8 條「終止後已發佈的作品怎麼辦」、準據法和法院、聯絡方式。

**建議**：Q22 選 **A**；Q22b、Q22c 維持草稿預設 **A**；Q22d 選 **A**。

---

### Q23　Fab 版怎麼做

**背景數字**（X2 逐字核對了 Fab 官方頁 27/27 句）
- Fab 只有兩種授權：CC-BY（免費）和 Standard。
- NoAI 標記只能配 Standard。
- Standard 一定要同時開 Personal 和 Professional 兩層價。
- **沒解決的事**：
  - Fab 官方的音訊類「接受格式」只列了 UEFN／Unreal Engine／Unity，純 WAV zip 能不能當主檔沒寫清楚。
  - 商品圖最小要 1920×1080、小於 3 MB，X1 的草稿不符合。
  - Fab EULA 頁回 403（機器人驗證），本卡沒有繞過，所以沒讀到。
- v1.0 寫的「Fab 88%」分潤沒查證過，v1.1 已經拿掉。

| 選項 | 做法 | 代價 |
|---|---|---|
| **A** 照 X2 做法上 Fab | Standard＋NoAI，zip 不附自訂 LICENSE，兩層價由你定 | 格式和 EULA 的疑問還沒解 |
| **B** 先不上 Fab | BOOTH／itch 先上；等你登入 Fab 後台確認純 WAV 能不能當主檔再說 | 晚一個通路 |
| **C** 上 Fab、用 CC-BY 免費 | — | 沒有收入 |

都不改聲音。

**建議**：**B**。

---

### Q24　商品圖、試聽帶採不採用

**Q24a 商品圖**：X1 做了草稿：6 張世界觀縮圖（1200×1200）＋1 張封面（1600×1600），用 Charta 藍黑金米色票，字體是 GenRyuMin＋Garamond（Charta 指定的字體本機沒裝）。**各平台的圖片規格沒查證。**
- A＝採用草稿
- B＝重出（你指定字體、要不要加日文、尺寸）
- C＝等你登入上架平台後台看過規格再定

**Q24b 試聽帶**：43 段完整長度接起來，共 6:03.560。只套一個線性增益 −0.206 dB，響度 −14.000 LUFS，WAV −1.173 dBTP、MP3 −1.081 dBTP，沒有壓縮也沒有限幅。商品稽核用自己的量測獨立核對過。
- A＝採用完整版
- B＝另做精華短版（你定規則：每檔取幾秒、要不要淡出）

**建議**：Q24a 選 **C**，Q24b 選 **A**。

---

### Q25　AI Radiance 全曲版放不放進專輯

**背景**：「全曲版有 41 個削波樣本」是誤讀，那是正規化之前數的。實際上 50 個母帶的峰值都是 0.95，碰到滿刻度的樣本 0 個（X2 實測，商品稽核核對過）。所以**不需要重渲**。
另外，N1 查過 AI Radiance 五軌，弱基頻 0 顆。

- A＝放
- B＝不放（候選版預設，跟 v1.0 一樣）

都不改聲音。

**建議**：**A**。當初不放的理由已經不成立。

---

### Q26　loop 附哪一版

**背景**：
- 原版 6 個 loop 比整小節長：每跑一圈多 1.2～8.3 秒，是後面接的餘響尾巴。
- X1 做了 loop-ready 版：把尾巴疊回開頭，長度誤差 0 樣本。
- 接縫聽起來會不會「喀」一聲，還沒有人聽過。
- README 的說法要先修（本節開頭那條商品稽核 FAIL）。

- A＝兩版都附（候選版預設）
- B＝只附 loop-ready
- C＝只附原版

都不改聲音。

**建議**：**A**。

> **2026-09-25 WF0925b**：背景第 4 點「README 的說法要先修」**已修，稽核 PASS**——README 現在寫：套增益之前，tail-wrap 跟「母帶每 N 樣本重播」逐樣本相同；交付檔又整體乘了 −0.55～−0.77 dB 並存成 24-bit，所以跟自己拿原版重播**不是逐位元相同**（原版小聲 0.03～0.05 dB）。XF 與稽核都用 24-bit 整數全量量過 6 個 loop：跟原版重播最大差 26,826～44,774 LSB24；loop-ready 真峰值 −0.996～−1.002 dBTP（三支量測器）。接縫聽起來會不會「喀」一聲，仍然沒人聽過（Q28）。證據 `reports/gate_outputs/wf0925b_XF_loop_facts.txt`、`wf0925b_XF_recheck.txt`。

---

### Q27　音樂 16-bit 版換成 TPDF dither 版

**背景**：
- 7 軌都用原本的處理鏈重出，sha256 跟原本逐位元相同，證明能重現；然後再加 TPDF dither。
- 量化誤差 RMS 0.4995 LSB（理論值 0.5）。
- 有 4 軌在原鏈的真峰值略高於 −1.000，所以 dither 前先調小 0.001～0.032 dB。代價是揚琴版響度從 −14.10 變 −14.13 LUFS。
- 換了之後專輯 zip 要重打（開關已做好）。音樂的 MP3 試聽檔沒有重出。

- A＝換
- B＝不換

改變只在 16-bit 量化雜訊，外加上面那 4 軌 ≤0.032 dB 的音量微調。

**建議**：**A**。

---

### Q28　找聽人把關

**背景**：你是免耳驗收，需要用耳朵把關的地方，已經縮成一份 22 題的是非題答題卷，約 15 分鐘：
- 3 個打擊音效的開頭
- 6 個 loop 的接縫
- Gate Open Dark 的 overdrive
- D16 那 16 顆（加上邊緣的 A5@0.462、G#5@0.427）

試聽包 `packages/TsukiSynth_listening_kit_v1_1.zip`（116.7 MB）已經做好。費用 PRODUCT_SHEET 估 US$30–80。

- A＝發案（SoundBetter 或 Fiverr；只列名稱，AI 沒下單，也不會下單）
- B＝不發案，先上架
- C＝找你認識的聽人

**建議**：**A** 或 **C**。

---

### Q29　合成器商品名裡 VST 怎麼寫

**背景**（`docs/legal/JUCE8_LICENSE_REVIEW.zh-TW.md` §6.2）
- 一旦用了「VST」這個字，就要照 Steinberg 規範：宣傳頁要放 VST Compatible Logo、第一次出現要加 ®、要附商標聲明句、不能寫 VSTi。
- 商品名能不能寫 VST，Steinberg 兩份官方文字互相矛盾：官網 §6 說可以；SDK README 說禁止。
- `.vst3` 副檔名本身算不算商標使用，**查不到**。

- A＝名稱帶「VST® 3」＋logo（要下載 logo，Q37-3）
- B＝名稱只寫「TsukiSynth」，內文另起一行寫相容格式，附 logo、®、聲明句。兩份官方文字都滿足，但一樣要下載 logo。
- C＝完全不提 VST

**建議**：**B**。

---

### Q30　合成器首發平台

**背景**：外掛從來沒在 mac 上建置過（盤點 E12）：
- CI 的 macOS 只建 CLI。
- AU 要加 `-DTSUKI_AU=ON` 才會開。
- Score 控制台寫死 `TsukiSynthCLI.exe`。
- 資料夾在 mac 上會是 `~/Library/TsukiSynth`，不是慣例的 Application Support。

變現計畫是先只賣 Windows。

| 選項 | 做法 | 工作量 |
|---|---|---|
| **A** Windows only | 商品頁標明 Windows 64-bit | 0 |
| **B** Windows＋macOS | 加 macOS CI build（VST3＋AU）和 auval，改 Score 控制台和資料夾 | M |
| **C** 合成器本體先不賣 | 只賣音效包和專輯 | 0 |

都不改聲音。

**建議**：**A**。

---

### Q31　JUCE Starter 要不要註冊、收入怎麼算

**背景**（`docs/legal/JUCE8_LICENSE_REVIEW.zh-TW.md` §0、§2、§5）
- 門檻：近 12 個月營收或資金 US$20,000 以下。算的是「因使用 JUCE 而來」的全部收入，捐款、贊助、廣告也算。
- EULA 寫下載或使用就算同意，沒寫要註冊；但也沒寫不用註冊。**查不到定論。**
- 音效包、專輯、直播收入算不算；毛額還是淨額：**查不到**。保守做法是三條產品線加總、用毛額。
- 只描述、不是 GATE：以售價 US$29 算，約 689 套到門檻。

| 選項 | 做法 |
|---|---|
| **A** 不註冊、不寄信 | 每月記一次三條產品線的毛收入，滾動 12 個月加總 |
| **B** A＋寄信問 | 你寄信到 sales@juce.com 問三件事：Starter 要不要註冊、音效包／專輯／直播算不算、毛額還是淨額。**寄信要你自己寄。** |
| **C** 到 juce.com 建帳號 | **你本人操作** |

**建議**：**B**。回覆來之前照 A 做。

---

### Q32　合成器買家 EULA 九個空格

**背景**：`docs/legal/EULA_BUYER_DRAFT.md` 是草稿，不是法律意見。九個空格填完後，要另存成 `tools/installer/EULA.txt`，安裝包才編得過。

| 格 | 題目 | 選項 | 規劃者建議 |
|---|---|---|---|
| E1 | 授權人名稱 | TsKR2828，或其他正式名稱（寫不寫真名） | 你定 |
| E2 | 授權範圍 | 甲：每位使用者，本人的電腦台數不限，同一時間一人用；乙：最多 N 台 | 甲 |
| E3 | 禁不禁止把未加工的單音取樣包成音源再賣 | 甲：不限制；乙：禁止 | 你定 |
| E4 | 寫不寫「不得用於 AI 訓練」 | 甲：不寫；乙：寫 | 乙（跟音效包 v1.1 第 5 條一致） |
| E5 | 退款 | 照平台規定／自訂天數／不退款（消費者法另有規定者除外） | 照平台 |
| E6 | 準據法與管轄 | 你定 | 你定 |
| E7 | 聯絡信箱 | 你提供（VST3 的 moduleinfo 也還是空的） | 你定 |
| E8 | 以哪個語言版本為準 | 英文／中文 | 英文 |
| E9 | 要不要 DRM 或序號 | 變現計畫建議不做 | 不做 |

回覆格式：「Q32 E2甲 E4乙 E5平台 E8英 E9無，E1/E6/E7 另附」。

---

## 五、版控與環境

### Q33　本輪 staged 怎麼 commit、要不要 push

**背景**：
- HEAD `18430c4`，比 origin 多 7 個 commit，還沒 push。
- 撰寫時 staged 124 檔：P1 15、研究 75、C++ 34。
- X1、X2 的 15 個證據檔還是 untracked，等商品稽核修正。
- 撰寫時整合卡正在跑（`reports/gate_outputs/wf0925_integration_raw/` 已經出現），結果以整合卡回報為準。
- 只要 push 到 `fix/**`，`physics.yml` 就會自動跑。P1 的 CI 改動、HostProbe 步驟（Q12）、release workflow 試跑（Q14-B），都要 push 之後才驗得到。

| 選項 | 做法 | 代價 |
|---|---|---|
| **A** commit＋push branch | 整合卡和交接卡 PASS 後，照交接卡的 commit 清單切 commit，push 這個 branch（**不 merge main**） | 雲端上看得到這一輪的內容（repo 是公開的，見 Q34） |
| **B** 只 commit、不 push | — | CI 相關的題驗不到 |
| **C** 維持 staged | 你自己審 | 同上 |

都不改聲音，工作量 S。

**建議**：**A**。

> **2026-09-25 WF0925b**：已補數字——現在 staged **239 檔**＝WF0925 的 154＋WF0925b 新進 85（TF 11、DS 8、BR 26、DS／BR 稽核 1、X1／X2 證據 15、XF 證據 9、INT2 15）；X1／X2 那 15 個證據檔已在商品稽核複驗 PASS 後 stage。整合卡已有結果：WF0925 INT 10 條全綠、WF0925b INT2 全套全綠（pytest 307＝301 passed＋1 skip＋5 xfail、`--full` NO CHECKED FAILURES、75/75、8/8、HostProbe 215/0）。沒 stage 的只剩 Q34 的兩項。包含 WF0925b 的 commit 切法（8 列、239 檔，逐列 pathspec 已核對不重疊、不漏）在 `docs/workcards/WF0925_README.md` §7-6。HEAD 仍是 `18430c4`，沒有 commit／push。

---

### Q34　公開 repo 的四件小事

**背景**：
- repo 是 PUBLIC（`gh repo view` 回傳 visibility=PUBLIC，盤點 S-public）。
- 本卡掃了 staged 的 124 檔：
  - 32 檔共 232 行含 `C:\Users\admin`
  - 其中 4 檔含 Claude session 暫存路徑（例如 `wf0925_K2_hostprobe.txt` 13 行）
  - 用常見機密字樣掃描（api key、password、token 格式、信箱）：**0 命中**
- HEAD 裡本來就有 241 檔含這種路徑，是既有慣例。

- **Q34a** `docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md`（untracked，沒被 ignore，內含售價）：
  - A＝移到 repo 外的私人資料夾，交接文件改指向新位置
  - B＝加進 `.gitignore`，留在原處（檔名會出現在公開的 .gitignore）
  - C＝commit 進公開 repo
- **Q34b** 證據檔裡的本機路徑：
  - A＝接受（既有慣例）
  - B＝從下一輪起，新證據檔改用 `<repo>`、`<scratch>` 代號；既有的不動
  - C＝連歷史一起清（要改寫 git 歷史，不建議）
- **Q34c** repo 要不要維持公開：
  - A＝維持
  - B＝改 private（GitHub 設定，你操作；對 Actions 額度等的影響本卡沒查）
- **Q34d** `reports/status_check_2026-09-25/`（916 KB，untracked，21 檔含本機路徑；ROADMAP 和 HANDOVER 已經引用它）：
  - A＝進版控
  - B＝不進，只留在本機

**建議**：Q34a **A**、Q34b **A**、Q34c **A**、Q34d **A**。

> **2026-09-25 WF0925b**：已補數字（Q34b）——WF0925b 各卡的證據一律用 `<REPO>`／`<SCRATCH>`／`<APPDATA>` 代稱；XF 另把 X1／X2 那 15 個證據檔裡的本機路徑換掉（24 處，換回去逐位元相同，稽核 PASS）。交接卡重掃 staged：WF0925b 新進的 74 個證據與報告檔 **0 處真實本機路徑**；整體是 49 檔共 309 行含 `C:\Users\admin`，都在 WF0925 的證據與少數既有文件（最多 `wf0925_K2_hostprobe.txt` 52 行）；另 `wf0925_V1_partial_stem_verify_full.txt` 有 E 槽路徑（沒有使用者名稱）。WF0925 那批沒改，等你回 Q34b（選 A 就不動；B 只管以後）。命令見 `docs/workcards/WF0925_README.md` §7-7。

---

### Q35　重新部署 VST3、清掉三份舊副本

**背景**（本卡 09-25 唯讀查的，沒動任何檔）

| 舊副本 | 版本 | 外掛本體 sha256 前 16 碼／大小 | 狀況 |
|---|---|---|---|
| ① `C:\Program Files\Common Files\VST3\TsukiSynth_VST3_2026-09-10\TsukiSynth.vst3` | 09-10 23:46 build（檔案時間 09-13 03:33） | `786643308473051e`／7,947,264 B | 現在實際裝的是這份。多了一層子資料夾；缺 D12、D9c 和本輪 K1 |
| ② `C:\Program Files (x86)\Common Files\VST3\TsukiSynth.vst3` | 07-12 | `a78652567d781338`／7,763,968 B | 很舊 |
| ③ `%APPDATA%\VST3\TsukiSynth.vst3`（`C:\Users\admin\AppData\Roaming\VST3\`） | 05-07 | `150225de97d5767…`／5,639,168 B | 不是標準 VST3 路徑 |

另外還有：
- 桌面上的 `TsukiSynth_v0.3.0_20260805`（15 MB）和 `_20260806`（22 MB）
- `C:\Users\admin\TsukiSynth.vst3`：空殼，0 B
- 標準位置 `C:\Program Files\Common Files\VST3\TsukiSynth.vst3` 目前**不存在**
- Cubase 的外掛快取停在 08-22，指向已經不存在的路徑
- 寫入 Program Files 需要管理員權限

| 選項 | 做法 | 代價 |
|---|---|---|
| **A** 部署新版＋收掉舊副本 | commit（Q33）後，用整合卡 PASS 的 build 部署：<br>1. 先把 ①②③ 加時間戳備份到 `E:\`（照你「覆蓋前先備份」的習慣，**只搬、不刪**）<br>2. 新版直接放在 `C:\Program Files\Common Files\VST3\TsukiSynth.vst3`，不要子資料夾<br>3. 開 Cubase 重掃，跑 `tools/cubase_scan_verify.py`<br>AI 準備腳本，**你用管理員身分執行** | 要你動手一次 |
| **B** 只部署新版 | 舊副本不動 | DAW 可能同時掃到新舊兩份 |
| **C** 等安裝包 | 安裝包編好再用它部署（要先下載 Inno Setup、EULA 定稿） | 比較晚；安裝包也不會刪舊副本 |
| **D** 暫不部署 | — | 你在 Cubase 用的一直是舊版 |

都不改聲音。

**建議**：**A**。

---

### Q36　Downloads 殘留、本輪暫存清理

**背景**：C 槽剩 **20 GB**（使用率 97%）。

**Q36a** `C:\Users\admin\Downloads\不知道有沒有用\`，總共 613.5 MiB：

| 內容 | 大小 |
|---|---|
| Piano Sheet Converter 的 Electron 解壓殘留（`Piano Sheet Converter.exe`、`resources`、`locales`、各種 dll、pak 等） | **467.9 MiB** |
| 安裝檔（`installer.exe`、Limbus、Orra、Klanggeist zip） | 135.9 MiB |
| Klanggeist 資料夾 | 9.7 MiB |

Piano Sheet Converter 已經裝在 `AppData\Local\Programs\Piano Sheet Converter`。

- A＝把 467.9 MiB 解壓殘留移到資源回收筒，保留安裝檔和 Klanggeist
- B＝整個資料夾移到資源回收筒
- C＝不動

AI 只會「移到資源回收筒」；**清空回收筒（永久刪除）要你自己按**。

**Q36b** 本輪暫存（都不進版控）：

| 位置 | 大小 | 說明 |
|---|---|---|
| `output/wf0925/` | 4.8 GB | 含 F5 隔離樹 364 MB |
| session scratchpad | 3.3 GB | — |
| `E:\tsuki_wf0925_V1\` | 17 GB | 905 顆分軌，可以用 stem_verify 重跑產生 |

商品母帶的渲染器（CLI sha `9123db8f…`）已經另外備份在 `exports/renderer_archive/`，清 `output/` 不會弄丟它。

- A＝交接卡結束、commit 之後，全部移到資源回收筒
- B＝只清 C 槽上的，保留 E 槽的分軌
- C＝都保留

**建議**：Q36a **A**，Q36b **A**。

> **2026-09-25 WF0925b**：已補數字（Q36b）——收尾輪又多了暫存，而且 **C 槽只剩 12 GB（98%）**。交接卡重量：`output/wf0925/` 5.2 GB、`output/wf0925b/` 1.9 GB（XF 1.3 GB、BR 391 MB、XF_audit 222 MB）、session scratchpad 8.9 GB（其中 wf0925b 5.4 GB）、`E:\tsuki_wf0925_V1\` 17 GB。BR 樹副本裡接 JUCE 的 junction 已拆掉（稽核掃 reparse point 0 個），一般刪除不會波及主 repo 的 `libs/JUCE`。**不要清的**：`exports/renderer_archive/` 與 `E:\TsukiSynth_renderer_archive\`（商品母帶的渲染器，見 O15）。Q36a 的 Downloads 殘留交接卡沒重量，數字照上表。

---

### Q37　其他下載請求（每列回 Y 或 N）

| # | 要下載什麼 | 從哪裡 | 大小 | 是不是執行檔 | 什麼時候需要 |
|---|---|---|---|---|---|
| 1 | Inno Setup 7.1.0（x64 安裝程式） | GitHub `jrsoftware/issrc` 的 release `is-7_1_0`（2026-08-12），`https://github.com/jrsoftware/issrc/releases/download/is-7_1_0/innosetup-7.1.0-x64.exe`；API 提供的 digest 是 `sha256:0362a383…` | 14,304,168 B | **是**（安裝程式） | 要編安裝包時。`tools/installer/README.md` 寫要 6.3 以上；7.x 的相容性本卡沒查 |
| 2 | `vc_redist.x64.exe` | `https://aka.ms/vc14/vc_redist.x64.exe`（官方永久連結，引自 installer README） | 本卡沒查 | **是** | 只在 Q07 選 B 時 |
| 3 | VST Compatible Logo | GitHub `steinbergmedia/vst3_doc` 的 `artwork/`，只抓 svg 和 png（每檔 908～43,917 B）；不用抓整個 doc（269,681 KB） | 16 檔全抓 13,169,899 B（eps 每檔約 3.1 MB） | 否（圖檔） | Q29 選 A 或 B 時 |
| 4 | 論文 PDF（L1 取不到的） | (a) D4 ICSV27 舌鼓論文：`https://unige.iris.cineca.it/bitstream/11567/1063604/1/full_paper_1117_20210430223100647.pdf`，請你用瀏覽器開，或寫信向作者索取<br>(b) Alon 2015 York 碩士論文：`https://etheses.whiterose.ac.uk/id/eprint/12260/1/EyalMSc.pdf`，超過 WebFetch 的 10 MB 上限<br>(c) Zoghaib & Mattei 2013：HAL 防爬蟲擋住，要你手動下載<br>(d) Van Eysden & Sader 2007：對方網站憑證錯誤，沒取得 | (b) 超過 10 MB，其他本卡沒查 | 否 | 做 Q17-C 或 Q15-C 的研究時才用得到 |

回覆格式：「Q37 1Y 2N 3Y 4Y」。

**建議**：1 Y（要編安裝包的話）；2 看 Q07；3 看 Q29；4 不急。

---

## 六、WF0925b 補收（2026-09-25 收尾輪交接卡 HO2）

### Q38　外掛缺檔警告「音量會和 IR 模式不同」要不要改

**白話問題**：preset 記的 IR 檔在這台電腦上找不到時，外掛會自動切回演算法殘響，並跳一句警告，裡面寫「音量會和 IR 模式不同」。
這句是當年 IR 比演算法殘響小約 28 dB 時寫的；09-16 D9c 補償之後，預設設定下兩種模式的音量已經對齊，這句話就不準了，剩下的差別主要是音色。
這句字樣是 F-03 施工卡規定的，改它等於改 F-03 的規格措辭，所以要你點頭。WF0925 那份包漏收了這一題（它一直掛在 `TODO.md` 等裁）。

**背景數字**
- 字串位置（staged 版行號）：中文 `src/PluginProcessor.cpp:901`「音量會和 IR 模式不同」、英文 `:902-904`「Switched back to algorithmic reverb; the volume will differ from IR mode.」，在 `forceAlgorithmicMissingIR()` 裡。HEAD 版是 `:841`、`:846`（盤點 APPENDIX `[open-work:U3-ir-warning]` 引的是 HEAD 行號）。
- 規格出處：`docs/workcards/WF0908_P3_f03_ir_library.md:36` 規定警告要「含『音量會與 IR 模式不同』字樣」。
- D9c 之後 K-02 四組 IR−ALGO 落差是 +0.112／−0.131／+0.108／−0.028 dB（對齊參考是 ALGO 預設 size 0.5、未設 T60）；把空間大小或 T60 調離預設時，兩種模式的音量仍可能差幾 dB（`docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md` §5-3、§6），但已經不是這句原本指的 28 dB。
- 建議文字已經寫在 UI 規格 v1.2 §5-3「缺檔警告文案」（AI 擬、未定案）：中文「已切回演算法殘響，**殘響的音色會和原本的 IR 不同。**」、英文「Switched back to algorithmic reverb; **the reverb will sound different from the original IR.**」
- 交接卡 09-25 用 grep 查過：`tests/` 和其他 cpp／h／py 沒有任何地方斷言這段文字；這串字只在外掛畫面顯示，CLI 不編這個檔（`CMakeLists.txt:141-143` 的 CLI 只有 `src/cli/RenderApp.cpp`）。

| 選項 | 做法 | 代價 | 改聲音？ | 工作量 |
|---|---|---|---|---|
| **A** 改成 UI 規格 v1.2 的建議文字 | AI 開小卡改 `src/PluginProcessor.cpp` 中英兩段字串，同步改 F-03 施工卡那一格的措辭（加註日期與理由）；照 R6 重建三個 target、跑 HostProbe | 動 F-03 規格措辭 | 不會（只是畫面文字） | S |
| **B** 你自訂措辭 | 回覆時附上中文（和英文，或交給 AI 翻），其餘同 A | — | 不會 | S |
| **C** 維持現行字串 | 不改；在已知限制記一句「這句在 D9c 之後不準」 | 使用者看到的警告跟實際不符 | 不會 | 0 |

**建議**（交接卡的看法）：**A**。

---

## §7　其他待裁（不好用一個字母回，或是你本人的事）

| # | 事項 | 誰 | 出處 |
|---|---|---|---|
| O01 | 售價（建議音效包 ¥900、專輯 ¥500）、賣家帳號註冊（BOOTH＋PayPal、itch 等） | 你本人（AI 不能代建帳號） | 盤點 M1、M2；PRODUCT_SHEET §5 |
| O02 | UI 功能規格要送給誰；功能算不算已經凍結。送出前先把 v1.1 同步成 v1.2 | 你 | 盤點 U1、U2 |
| O03 | 四季、月光換源重轉譜要不要排程。另外 N1 發現：四季的 string＋bow 有 5,682 顆在同一種洞裡，換源後如果還用 bow，會帶著同樣的問題。建議登記成新的 D 項 | 你 | 盤點 C1；N1 open_items 第 4 點 |
| O04 | A10 Score 控制台實際操作、調音器目視檢查、Limbus 有沒有用金鑰啟用 | 你動手 | 盤點 Y1 |
| O05 | 專輯的完整授權檔（盤點 R7），還沒起草 | AI 可起草，要你點頭 | X2 open_items 第 7 點 |
| O06 | 安裝包要不要附 `TsukiSynthCLI.exe`。Standalone 的 Score 控制台會在同一個資料夾找它 | 你 | G1 open_items 第 7 點 |
| O07 | 發行資訊：CMake 的 COMPANY_WEBSITE／EMAIL、版號規則（0.3.0 從 07-23 沒動過）、About 頁放 VST logo 或商標聲明（改 src，要走 R6） | 你給資料，AI 改 | 盤點 S10、E13；G1 open_items 第 9 點 |
| O08 | 即時音訊安全檢查自動化：把稽核的 malloc 計數探針做成正式 GATE，或在 Linux clang 加 RTSan job（要改 CMakeLists 和 CI） | 你點頭，AI 做 | C++ 稽核 note；K1 open_items 第 5 點 |
| O09 | HostProbe 跟 audit 測試會寫真的 `%APPDATA%\TsukiSynth\`（跑完會自己清掉）。要不要讓 IRLibrary、PresetManager 讀環境變數改資料夾（改 src） | 你點頭 | K1 第 9 點；P1 第 10 點 |
| O10 | score 的 `meta.description` 還寫「可無縫循環」「自然循環」，另有兩處材料字眼是舊的。改 score JSON 會讓 `root_score_sha256` 改變，要走 R10 | 你 | X2 open_items 第 6 點 |
| O11 | CLI 的 `ScoreRenderer::eventEndTime()` 一律用 0.05 配 buffer，但 Chromatic 放鍵用 0.08。商品 restraint_ui_001 最後一顆 G3 比 buffer 多活 0.272 s（buffer 結束時剩 −69.5 dB）。要改就是 CLI 渲染變更（R10） | 你 | V1 open_items 第 7 點 |
| O12 | IRLibrary 自己寫的 SHA-256，跟 RenderApp 用的 JUCE SHA256 要不要統一；`IRLibrary::list()` 沒有呼叫端、庫也沒有清理介面（要改 CMakeLists） | 你點頭 | K1 第 6 點 |
| O13 | preset 檔格式比 2 新時會被拒絕覆寫，但畫面只顯示通用錯誤訊息（改 PluginEditor） | 你點頭 | C++ 稽核 note |
| O14 | **知情確認**：plugin state 已定成 `state_version=3`。一旦寫進客戶的專案，就是永久的相容包袱 | 你知道就好 | K1 open_items 第 7 點 |
| O15 | 商品母帶的渲染器已經備份在 `exports/renderer_archive/TsukiSynthCLI_9123db8f_build20260915.exe`（sha 核對相同；在 repo 資料夾內、gitignored）。**本卡新發現：`build\` 的 CLI 已在 09-25 10:39 被整合卡重建，變成 `b84c775b…`**，所以現在只剩這份備份和 `output/` 裡的複本。要不要再放一份到 repo 外，例如 E 槽 | 你 | 本卡查證（附錄 B） |
| O16 | tools 小修（AI 可做，不改渲染，要開卡）：<br>• `crossplatform_verify.py` 和 `test_dump_modes_layered.py` 的 find_cli 還是看 mtime<br>• stem_verify 不支援 WAVE_FORMAT_EXTENSIBLE<br>• `render_wf_scores.py --cli` 要轉成絕對路徑<br>• stem_verify、partial_verify 加 `--cli`<br>• partial_verify 的 caveats 字串還寫「C10 待裁」<br>• release 網格「0 拒量」只在 xfail 測試裡檢查 | 你點頭 | P1 第 3–6 點；V1 第 3、10 點；P1 稽核 note |
| O17 | 規約更新：本機 Python 實際是 3.13.3，不是規約寫的 3.12（CI 固定 3.12.8） | 交接卡 | P1 第 9 點；V1 第 11 點 |
| O18 | DistroKid 的 AI 表單選項、Content ID 政策還沒查證 | AI 可查（只讀網頁） | X2 open_items 第 7 點 |
| O19 | 不必處理：K2 回報的外來 `find.exe`（PID 13496），**本卡 09-25 查詢時已經不存在** | — | K2 第 9 點；K1K2fix 第 5 點 |

**2026-09-25 WF0925b 處理結果**（表格原文不動，逐項補在這裡）：
- **O05**　2026-09-25 WF0925b：**已起草，等你審**——WF0925b-XF 寫了 `exports/products/clean_batch2_v1_1_candidate/LICENSE_ALBUM_v1_1.txt`：開頭有「草稿、非法律意見、待月月審」方框；第 5 條影片／直播當背景音樂並列 A 案（允許）、B 案（只個人聆聽）；準據法、聯絡方式等標 [TBD]；**不在任何 zip 裡**（XF 稽核 PASS）。你要決定第 5 條選 A 或 B，以及開不開 DistroKid Social Media Pack（Content ID）（`DISTROKID_NOTES.md` 的 K2／K3）。選 B 的話，專輯 README（`scripts/x2_build_packages.py` 的 album_readme）要跟著改、專輯 zip 要重打。
- **O15**　2026-09-25 WF0925b：**已處理**——repo 外的第二份備份在 `E:\TsukiSynth_renderer_archive\`（資料夾 09-25 11:40 建立）。交接卡核對：exe sha256 `9123db8f63390bfe…`（7,132,160 B），跟 `exports/renderer_archive/` 那份相同，`README.txt`、`SHA256SUMS.txt` 也逐位元組相同。`SHA256SUMS.txt` 裡是 repo 相對路徑，在 E 槽資料夾裡直接 `sha256sum -c` 會找不到檔，要手動比。清暫存（Q36b）時兩份都不要動。
- **O16**　2026-09-25 WF0925b：**六項全部已處理**（WF0925b-TF，稽核 PASS，staged 未 commit）：find_cli 不再看 mtime；stem_verify 讀得懂 WAVE_FORMAT_EXTENSIBLE（不支援的格式照樣大聲丟錯）；`render_wf_scores.py --cli` 先轉絕對路徑（相對路徑 8/8 IDENTICAL）；stem_verify、partial_verify 加 `--cli`（指到不存在的檔 exit 1，不會退回自己找）；partial_verify caveats 改成現況；release 網格「0 拒量」搬到一般測試（原條件照搬，不是新門檻）。pytest 288 → 307（+19，刪 0）。TF 另外留了兩條小事：sustain 網格的「0 拒量」同樣還在 xfail 裡；`melody_verify.verify()` 沒有 `cli` 參數（stem_verify 的 `--cli` 是靠暫時替換私有函式做到的）。證據 `reports/gate_outputs/wf0925b_TF_*.txt`。
- **O17**　2026-09-25 WF0925b：已寫進規約——`docs/workcards/WF0925_README.md` §0「Python」列與 `HANDOVER.md` §9（本機 3.13.3、CI 固定 3.12.8）；WF0925b 的 Python GATE 也都在 3.13.3 上跑。
- **O18**　2026-09-25 WF0925b：**已查到能查的程度**——WF0925b-XF 寫成 `DISTROKID_NOTES.md`：DistroKid 說明中心 12 篇都回 HTTP 403（沒有繞過），只拿到搜尋摘要（標「DK 摘要、非逐字」）；Spotify、YouTube 官方頁的逐字錨點 17/17。要點：給愛麗絲是公版樂曲，依摘要**不符合 Content ID 資格**（YouTube 官方也寫公版樂曲不能當參考檔）；曲風選 Classical，依摘要 **DistroKid 不送 Apple Music**；上傳表單的 AI 選項有沒有「部分音訊」，三次搜尋兩次有、一次沒有。**K1～K7 都要你登入 DistroKid 確認**。證據 `reports/gate_outputs/wf0925b_XF_web_sources.txt`。
- **新增 Q38**（F-03 缺檔警告措辭，`[open-work:U3-ir-warning]`）：WF0925 這份包漏收，收在「六、」，可以用一個字母回。

---

## 附錄 A　本輪各 lane 回報的 open_items 歸檔（逐條）

歸入欄的代號：
- **Qxx／Oxx**＝本包的題號
- **交接**＝交接卡同步文件，不需要裁決
- **AI 修**＝稽核或本輪已經指派 AI 修，不需要裁決
- **已處理**＝本輪已經解決
- **記錄**＝資訊性，不需要動作

### C++ lane

| 卡 | # | 摘要 | 歸入 |
|---|---|---|---|
| K1 | 1 | GATE 6 命令的細節：workdir 放 repo 外、`--outdir`、絕對路徑、CRLF | 交接（寫進操作備忘） |
| K1 | 2 | GATE 3/4 跑的時候帶著其他 lane 的 tools 改動 | 已處理（K1K2fix 和稽核在最終樹上重跑） |
| K1 | 3 | E9 的 tail 最多晚 50 ms 更新，沒在真的 DAW 驗過 | Q14 |
| K1 | 4 | H8「完全相同」只比到 6 位有效數字 | 記錄 |
| K1 | 5 | E8 靠讀程式碼下結論，RTSan 要改 CMakeLists 和 CI | O08 |
| K1 | 6 | 兩套 SHA-256 沒統一；`list()` 沒有呼叫端 | O12 |
| K1 | 7 | state 格式是永久相容包袱 | O14 |
| K1 | 8 | 交接卡要同步的文件 | 交接 |
| K1 | 9 | 測試會寫真的 %APPDATA% | O09 |
| K2 | 1 | FIPS 180-2 裡沒有空字串範例 | 記錄（註解已照實寫） |
| K2 | 2 | D9c 守門用顯式實例化；0.25 dB 待裁 | Q01、Q01b |
| K2 | 3 | 3 個工廠 preset 峰值超過 0 dBFS；峰值上限和靜音門檻屬新判準 | Q05、Q05b |
| K2 | 4 | E16 放在 HostProbe，沒放 ctest（要改 CMakeLists） | 記錄（CI 的 HostProbe 步驟有守著） |
| K2 | 5 | K1 的 GATE 4 證據用錯了 CLI | 已處理（K1K2fix） |
| K2 | 6 | 兩個測試檔同時帶著 K1 和 K2 的改動 | 已處理（稽核一起 stage） |
| K2 | 7 | 規約「HostProbe 必須以 repo 根目錄為 cwd」已經不成立 | 交接 |
| K2 | 8 | GATE 6 的操作細節 | 交接 |
| K2 | 9 | 外來 find.exe | O19 |
| K2 | 10 | %APPDATA% 已清空 | 記錄 |
| K1K2fix | 1 | 舊 json 裡 K1 GATE 4 的說法不實 | 交接（改引 K2／K1K2fix 的證據） |
| K1K2fix | 2 | 要 add 的檔 | 已處理（稽核已 stage） |
| K1K2fix | 3 | MSVC 重編不是逐位元組可重現 | 記錄（參見 O15） |
| K1K2fix | 4 | 稽核 note 五條 | 見下方「C++ 稽核」 |
| K1K2fix | 5 | 外來 find.exe | O19 |
| K1K2fix | 6 | 暫存 285 MB＋22 MB 可以刪 | Q36b |
| C++ 稽核 | note | E8 的 malloc 計數不是正式 GATE | O08 |
| C++ 稽核 | note | Material* 快取的疑慮不適用 | 記錄 |
| C++ 稽核 | note | `replaceFileIn` 的極端失敗情境 | 記錄 |
| C++ 稽核 | note | E14：比 3 新的 state 帶舊鍵 | Q10（各選項都「只記錄」） |
| C++ 稽核 | note | D9c 註解寫「+28.58 dB」，嚴格算是 28.595 | 交接（措辭） |
| C++ 稽核 | note | 舊 json 的 GATE 4 說法 | 交接 |
| C++ 稽核 | note | HostProbe cwd 規約 | 交接 |
| C++ 稽核 | note | E9 計時器沒在真的 DAW 驗過 | Q14 |
| C++ 稽核 | note | 外來 find.exe | O19 |
| C++ 稽核（第 1 輪，經 K1K2fix 轉述） | note | preset 比較新的格式只顯示通用錯誤 | O13 |

### Python lane

| 卡 | # | 摘要 | 歸入 |
|---|---|---|---|
| P1 | 1 | CI 改動只驗到 YAML 能解析，要 push 才看得到 runner 上的結果 | Q33、Q12 |
| P1 | 2 | Linux 的 label 標 clang，實際是 GCC | Q13 |
| P1 | 3 | partial_verify 的 docstring、caveats 和 EARFREE 文件還是舊說法；升不升 GATE | Q18、O16、交接 |
| P1 | 4 | 另外兩處 find_cli 還看 mtime | O16 |
| P1 | 5 | stem_verify 不支援 EXTENSIBLE | O16 |
| P1 | 6 | `render_wf_scores --cli` 要轉絕對路徑 | O16 |
| P1 | 7 | HANDOVER 要更新；selfcal 測試讓每次 CI 多約 2 分鐘 | 交接、記錄 |
| P1 | 8 | find_cli 會印一行到 stdout | 記錄 |
| P1 | 9 | Python 3.13.3 | O17 |
| P1 | 10 | 資料夾改用環境變數覆寫 | O09 |
| P1 稽核 | fix | pwsh 多行指令只看最後一個 exit code | Q12 |
| P1 稽核 | note | HostProbe 步驟排在其他 gate 前面 | Q12 |
| P1 稽核 | note | release 網格「0 拒量」只在 xfail 裡檢查 | O16 |
| P1 稽核 | note | 證據檔裡夾了 ANSI 跳脫字元 | 記錄 |

### 研究 lane

| 卡 | # | 摘要 | 歸入 |
|---|---|---|---|
| N1 | 1 | 給愛麗絲母帶選 A/B/C/D | Q15 |
| N1 | 2 | PRODUCT_SHEET 要補「已知限制」一行 | 已處理（X2 的 v1.1 候選版 §2.2），跟著 Q15 |
| N1 | 3 | TODO D16 狀態、HANDOVER、DEVLOG | 交接 |
| N1 | 4 | 四季的 bow 也在洞裡，建議登記新的 D 項 | O03 |
| N1 | 5 | 誠實限制 | 記錄 |
| N1 | 6 | 工作樹同時有其他卡的改動 | 記錄 |
| N1 | 7 | 資料 7.0 MB 要不要進版控 | 已處理（稽核已 stage）；有疑慮看 Q34 |
| N1 | 8 | 沒做 git 寫入 | 記錄 |
| F5 | 1 | 帶著新數字重開 D11 A/B | Q16 |
| F5 | 2 | 選 A 的話，F5 量法要另裁 | Q16（A 的前提） |
| F5 | 3 | F5 PASS 依賴探針 0.8 mm | Q16（D） |
| F5 | 4 | T60 跟真鋼琴的比對沒做 | Q16（D 的研究卡） |
| F5 | 5 | 「B1 吃掉餘裕」是推論，沒驗證 | 記錄 |
| F5 | 6 | patch 的基底可能要重新對齊 | Q16（A 的注意事項） |
| F5 | 7 | TODO 要標記完成 | 交接 |
| F5 | 8 | F5 的 scratch 樹可以刪 | Q36b |
| V1 | 1 | EARFREE 文件的數字要更新 | 交接 |
| V1 | 2 | partial 期望值的慣例 | Q18 |
| V1 | 3 | partial_verify 的 caveats 字串 | O16 |
| V1 | 4 | D7、G6 用泛音反推的基頻 FAIL | Q18b |
| V1 | 5 | D16 那 16 顆用泛音反推 16/16 PASS | Q15（背景數字） |
| V1 | 6 | voice pool 三選一，外加 FM、同音兩件 | Q09、Q09b、Q09c |
| V1 | 7 | eventEndTime 0.05 對 0.08 | O11 |
| V1 | 8 | 沒做 HostProbe 串流比對 | Q09（D） |
| V1 | 9 | E 槽 17 GB 分軌 | Q36b |
| V1 | 10 | stem_verify、partial_verify 沒有 `--cli` | O16 |
| V1 | 11 | Python 3.13.3 | O17 |
| V1 | 12 | 選 B 要改的文件 | Q09 |
| L1 | 1 | ×2 的去留 | Q17 |
| L1 | 2 | AI 可以先算 B 的數字 | Q17（D） |
| L1 | 3 | 衰減不看厚度 | Q17（背景數字） |
| L1 | 4 | S3 和 S5 差 7～9 倍 | Q17（背景，不裁） |
| L1 | 5 | D4 論文 | Q37-4(a) |
| L1 | 6 | Alon 碩士論文 | Q37-4(b) |
| L1 | 7 | Zoghaib、Van Eysden | Q37-4(c)(d) |
| L1 | 8 | WOOD_ANISOTROPY、TODO 要同步 | 交接 |
| L1 | 9 | PDF 只存在本機暫存 | 記錄 |
| G1 | 1 | EULA 的 E1–E9 | Q32 |
| G1 | 2 | VC++ runtime | Q07 |
| G1 | 3 | 下載 Inno Setup；pluginval 和 validator | Q37-1、Q14 |
| G1 | 4 | VST logo 要從完整 SDK 取 | Q37-3、Q29 |
| G1 | 5 | LISTING_COPY 的 VST 寫法 | Q29 |
| G1 | 6 | JUCE 要不要註冊、收入怎麼算 | Q31 |
| G1 | 7 | 安裝包附 CLI | O06 |
| G1 | 8 | KNOWN_LIMITS §C 的 9 條 | Q19 |
| G1 | 9 | About 頁、COMPANY 資訊、版號 | O07 |
| G1 | 10 | `.gitignore` 要擋 redist 和安裝包輸出；EULA.txt 進不進版控 | O07（跟 Q07、Q32 一起定） |
| G1 | 11 | 兩封信的標題還寫「草稿」 | 交接 |
| G1 | 12 | notices 裡 3 個版本查不到 | 記錄（查不到） |
| G1 | 13 | 交接要同步的清單 | 交接 |
| G1 | 14 | 安裝包不會刪舊副本 | Q35 |
| 研究稽核 | note | voice pool 報告的一處行號引用不精確 | 交接（措辭） |
| 研究稽核 | note | N1 資料 7 MB | Q34 |
| 研究稽核 | note | 證據檔含本機路徑 | Q34b |
| 研究稽核 | note | .iss 從沒編譯過 | Q37-1 |

### 商品 lane

| 卡 | # | 摘要 | 歸入 |
|---|---|---|---|
| X1 | 1 | 證據檔的位置 | 記錄 |
| X1 | 2 | dither 前先做了音量微調 | Q27 |
| X1 | 3 | loop 版本 | Q26 |
| X1 | 4 | 響度政策 | Q20 |
| X1 | 5 | 換 TPDF | Q27 |
| X1 | 6 | 試聽帶長度 | Q24b |
| X1 | 7 | 商品圖的字體、版面、日文、尺寸 | Q24a |
| X1 | 8 | 4 檔全精度真峰值略高於 −1.000 | Q20b |
| X1 | 9 | 樂章 2 標題不一致 | 已處理（v1.1 候選版） |
| X1 | 10 | 兩支量測器差 0.03 LU | 記錄 |
| X1 | 11 | 需要聽的地方 | Q28 |
| X1 | 12 | 沒做的項目 | 已處理（X2 接手）；專輯 LICENSE 見 O05 |
| X2 | 1 | 證據檔含本機路徑 | Q34b |
| X2 | 2 | 裁決 (1)–(10) | Q21、Q25、Q26、Q20、Q27、Q22、Q23、Q29、Q28、O01 |
| X2 | 3 | 「取自工程手冊」的措辭 | AI 修（文案措辭，連同商品稽核 note 一起改）；要不要更保守由你在 Q22 定稿時看 |
| X2 | 4 | Fab 的格式、圖片尺寸、EULA 403 | Q23、Q24a |
| X2 | 5 | v1.0 的材料寫錯 | 已處理 |
| X2 | 6 | score meta 裡的舊說法 | O10 |
| X2 | 7 | 沒做：專輯 LICENSE、合成器 EULA、圖片尺寸、MP3、DistroKid、logo | O05、Q32、Q24a、Q27、O18、Q37-3 |
| X2 | 8 | 需要聽的地方 | Q28 |
| X2 | 9 | 交接要同步 | 交接 |
| X2 | 10 | 開關測試時修了一處措辭 | 記錄 |
| 商品稽核 | fix | README 寫「逐樣本相同」太滿 | AI 修（見 §四 開頭） |
| 商品稽核 | note | 全精度真峰值隨量測器變 | Q20b |
| 商品稽核 | note | 接縫百分位的取法不一致 | AI 修（描述欄，不影響結論） |
| 商品稽核 | note | 試聽帶數字一致 | 記錄 |
| 商品稽核 | note | README 秒數捨入了兩次 | AI 修 |
| 商品稽核 | note | 阻尼措辭略強 | AI 修（跟 X2 第 3 點一起） |
| 商品稽核 | note | 「0 顆」沒寫出 N1 的範圍 | AI 修（文案補範圍） |
| 商品稽核 | note | FAIL 所以沒 stage | Q33（修好複驗 PASS 後 stage） |

### 盤點 STATUS_CHECK §3-1 的對照

| §3-1 # | 事項 | 本包 |
|---|---|---|
| 1 | 審 staged、決定 commit 切法 | 已完成（今天 7 個 commit）；本輪的見 Q33 |
| 2 | 重新部署、清舊副本 | Q35 |
| 3 | 變現 5 題 | Q21（AI 署名）、Q25（全曲版）、Q28（聽人）、O01（售價、帳號） |
| 4 | 給愛麗絲母帶 | Q15 |
| 5 | UI 規格送誰 | O02 |
| 6 | 四季、月光換源 | O03 |
| 7 | 工程裁決候選 | Q01（D9c CHECK）、Q05（限幅）、Q06（Program）、Q07（CRT）、Q08（一致性）、Q02（R6）、Q11（MIDI 20 clamp） |
| 8 | Limbus、Downloads、A10 | O04、Q36a |

---

## 附錄 B　本卡自己查的數字（命令與結果）

全部是唯讀：GitHub API 只抓 JSON 資料，沒有下載任何執行檔或安裝包；磁碟只列檔案、算大小，沒有移動或刪除任何東西。
原始回應存在 `output/wf0925/Q1/`（gitignored）。下表的 sha256 是回應檔本身的雜湊。

| 查什麼 | 命令 | 關鍵結果 | 回應檔 sha256（前 16 碼） |
|---|---|---|---|
| pluginval 最新 release | `curl -sS -H "Accept: application/vnd.github+json" https://api.github.com/repos/Tracktion/pluginval/releases/latest` | `v1.0.4`，2024-12-04T12:16:00Z；`pluginval_Windows.zip` 2,408,590 B（digest：None） | `666f69e831fa8b00` |
| pluginval 前 5 個 release | `…/releases?per_page=5` | v1.0.4、v1.0.3、v1.0.2、v1.0.1、v1.0.0，都不是 prerelease | `63b105f17300bbe1` |
| vst3sdk repo | `…/repos/steinbergmedia/vst3sdk` | size 2,746 KB，MIT，default master | `a7a5e5f873c428e1` |
| vst3sdk releases | `…/vst3sdk/releases?per_page=5` | 空（GitHub 上沒有 release，只有 tag） | `2ba33ca0557f1bb5` |
| vst3sdk tags | `…/vst3sdk/tags?per_page=8` | 含 `v3.8.1_build_84`（3cdf9ca5）、`v3.8.0_build_66`（9fad9770） | `2e40b7d2fad9ed20` |
| 釘住的 commit | `…/vst3sdk/commits/58f8da79…` | 2025-11-17，「Remove wrong license agreement sentense」 | `be449c259df22ca1` |
| 釘住的 commit 相對 3.8.0 | `…/vst3sdk/compare/9fad9770…58f8da79…` | ahead 2、behind 0 | （未存雜湊） |
| submodule 清單 | `curl https://raw.githubusercontent.com/steinbergmedia/vst3sdk/58f8da79…/.gitmodules` | base、cmake、doc、pluginterfaces、public.sdk、tutorials、vstgui4 | （未存雜湊） |
| submodule 大小 | `…/repos/steinbergmedia/{vst3_base,vst3_cmake,vst3_pluginterfaces,vst3_public_sdk,vst3_doc,vstgui}` | 568／349／261／17,610／269,681／15,670 KB | `5cfef3a0…`／`4933b785…`／`bad0cab4…`／`26a0c03b…`／`fafd4126…`／`14123410…` |
| 最新 SDK commit | `…/vst3sdk/commits?per_page=3`；`…/commits/3cdf9ca5…` | master＝3cdf9ca5，2026-08-11「VST3 SDK 3.8.1」 | `ab47e18be865d00c`／`477b9cecbe8dd240` |
| SDK README 取得方式 | `curl …/vst3sdk/master/README.md` | :143 `git clone --recursive https://github.com/steinbergmedia/vst3sdk.git` | `83165df5693e3e77` |
| VST logo 檔 | `…/repos/steinbergmedia/vst3_doc/contents/artwork` | 16 檔，合計 13,169,899 B（svg、png、eps、ico、icns） | `ba7c8f3ac3821ed0` |
| Steinberg 官網 SDK zip | `curl -sSL https://www.steinberg.net/developers/`＋WebFetch | 頁面由 JavaScript 產生，抓不到下載連結（**查不到**） | — |
| Inno Setup 最新 release | `…/repos/jrsoftware/issrc/releases/latest` | `is-7_1_0`，2026-08-12；`innosetup-7.1.0-x64.exe` 14,304,168 B，digest `sha256:0362a383ed217d4c…` | `d00b807cf0180aec` |
| 舊 VST3 副本 | `find … -name TsukiSynth.vst3` 加上 `stat`、`sha256sum`（只讀） | 見 Q35 的表；標準位置 `Common Files\VST3\TsukiSynth.vst3` 不存在 | — |
| Downloads 殘留 | `du`，加上 Python `os.walk` 分類加總（只讀） | 總計 643,252,689 B（613.5 MiB）；解壓殘留 490,593,036 B（467.9 MiB）；安裝檔 135.9 MiB；Klanggeist 9.7 MiB | — |
| 磁碟空間 | `df -h /c /e` | C：477G，已用 457G，剩 20G（97%）；E：剩 2.3T | — |
| 暫存大小 | `du -sh output/wf0925 <scratchpad> /e/tsuki_wf0925_V1` | 4.8G／3.3G／17G | — |
| 渲染器 CLI | `sha256sum build/…/TsukiSynthCLI.exe output/wf0925/*/cli.exe exports/renderer_archive/*.exe` | build\ 現在是 `b84c775b…`（09-25 10:39 重建）；V1、N1、R_audit 的複本和 renderer_archive 都是 `9123db8f63390bfe9070e9509fb2b60e9cc32ecb52e3bb2afc330d2b5fe01be8` | — |
| staged 內容掃描 | 逐檔 `git show ":<檔>"`，grep 本機路徑、session 暫存路徑、機密字樣 | 124 檔；32 檔共 232 行含 `C:\Users\admin`；4 檔含 session 暫存路徑；機密字樣 0 命中 | — |
| CLI 路徑會用到 src/effects | `grep -n "#include" src/score/ScoreRenderer.h src/dsp/EffectsChain.h` | ScoreRenderer.h:11 → dsp/EffectsChain.h:3-5 → effects/SimpleReverb.h、StereoDelay.h、Compressor.h | — |
| 外來 find.exe | `Get-Process -Id 13496` | 查無此程序 | — |
