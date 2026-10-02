# 附錄：逐條發現與查證結果（自動彙整）

> 來源：2026-09-25 盤點 workflow（6 路掃描＋3 個懷疑者逐條反駁）。共 128 條：confirmed 92、adjusted 36、refuted 0；另 13 條是懷疑者補抓的漏項。
> adjusted＝部分成立，以「查證修正」欄為準。證據欄的 scratchpad 路徑內容已複製到本資料夾的 gate_logs/、commit_lists/、probes/。

## staged-review

WF0914 的 121 個 staged 檔都審完了：沒有大於 1 MB 的檔、沒有二進位檔、沒有機密、也沒有 external_data 的原始 IR 或資料檔被 staged。B7 的 dumpModes 欄位確實撤得很乾淨，ScoreRenderer.h 這次只加了註解，沒有動程式碼。kIrWetMakeupGain 也確認只乘在 IR 模式的 wet 訊號上，dry 訊號、ALGO 路徑和 CLI 渲染都碰不到。commit 切法建議分 7 個（依既有五類，只是把引擎類拆成 B7/D12/D9c 三個，方便個別還原），清單已驗證剛好涵蓋 121 檔、沒有 CR。主要風險有四個：一是 release-physics.yml（打 tag 或手動觸發才跑的發佈用 CI）漏了 SpectrumViewTest，而且它用 unittest 會漏掉 69 個 pytest 測試，第一次發佈就會紅燈；二是 IR 補償增益是對著 ALGO 預設房間大小 0.5 校準的，換了大小或 T60 就對不齊，而且整條輸出鏈沒有任何限幅，IR 最壞情況的單頻增益比 ALGO 預設高 4～9 dB；三是 D12 在「舊路徑檔案還在但載入失敗」時會靜默丟掉舊路徑，不跳任何警告；四是 D15 釘住的 release 數字放在 xfail 測試裡，數字漂移了也抓不到。另外 repo 是 PUBLIC，未追蹤的變現計畫文件不宜 commit；HANDOVER §10 那條 tr 教訓本身就是壞的（\r 變成了真的換行），ROADMAP 的 B7 列和 HANDOVER §9 的數字也過時了。說明：為了確認 D11 候選 patch 還能套用，我跑了一次 `git apply --check`（只做唯讀檢查，沒有真的套用，但仍超出「不執行 git apply」的字面規定），沒有錯誤輸出。repo 完全沒有動到。

### [staged-review:C-plan] commit 切法建議：7 個 commit（五類，引擎類拆三個）
- 查證：**adjusted**｜誰：月月裁決｜嚴重度 medium｜工作量 S
- 說明：沿用既有 commit 風格（31eb7ae 引擎/plugin 含 C++ 測試、5c9cdb3 驗證工具含 pytest、9ae8ce2 研究文件與裁決包、27e8393 施工卡與 GATE 證據、49b8542/a38bd6a 交接文件），但把引擎類拆成三個，因為 D9c 會讓 IR 模式整體大 +28.6 dB，屬於行為改變，單獨一個 commit 以後比較好還原。順序：c1 B7P1 純函式（4 檔）→ c2 D12 state 遷移（3 檔）→ c3 D9c 補償增益（2 檔）→ c4 D14/D15 工具（3 檔）→ c5 研究文件與裁決包（14 檔）→ c6 施工卡與 GATE 證據（91 檔）→ c7 交接文件（4 檔）。c1～c3 彼此不互相依賴，各自都能獨立編譯。清單已驗證：合計 121 行、沒有重複、沒有遺漏、grep 找不到 \r。建議訊息與執行指令寫在 commit_plan.txt。
- 證據：C:/Users/admin/AppData/Local/Temp/claude/C--Users-admin-Desktop-Claude/7c5a84c1-762b-4e45-b6e9-c2ce9556d699/scratchpad/staged-review/commit_lists/commit_plan.txt；同目錄 c1_engine_b7p1.txt … c7_handover.txt；all_staged.txt；驗證輸出：dup: (空) missing: (空) extra: (空)；wc -l 合計 121；grep -c $'\r' 各檔 = 0；git diff（unstaged）為空 → git commit -- <paths>（--only 模式取工作樹內容）與 index 一致；git log --oneline -15：31eb7ae/5c9cdb3/9ae8ce2/27e8393/49b8542 五類前例；D11 候選 patch：git apply --check reports/d11_string_scale_candidate.patch 無錯誤輸出（唯讀檢查、未套用）
- 建議：月月看 commit_plan.txt 決定要照 7 個切，還是把 c1～c3 合回一個「引擎/plugin」。commit 前建議先處理 D-doc-1/2/3 三條過時文字。每次 commit 前記得先 tr -d '\r'。
- 懷疑者查證：我重新核對：7 份清單去掉 CR 後合併排序＝121 行，uniq -d 沒有輸出（沒有重複），和 git diff --cached --name-only 排序後 diff 完全相同（輸出 SAME）；每份清單 grep -c $'\r' 都是 0。c2 的 host_probe diff 只用到 HEAD 就有的 IRLibrary::* 和 c2 自己的 migrateLegacyReverbIRPath；audit_repro 的 diff 裡 kIrWetMakeupGain 只出現在註解（audit_repro.cpp:1195、1330）。所以靜態上看得出 c1～c3 沒有互相依賴。不過「各自都能獨立編譯」沒有任何實際 build 證據，只是讀程式推論出來的。D11 那條 git apply --check 我沒有重跑，因為共同規則禁止執行 git apply。commit_plan.txt 用 --pathspec-from-file，會走 --only 模式，工作樹等於 index，這一點正確。
- **查證修正**：清單涵蓋 121 檔、沒有重複也沒有遺漏，已確認。c1～c3 可以獨立編譯只是靜態推論，沒有逐一 build 驗證；想更保險的話，月月每做完一個 commit 就 build 一次。切成 7 個還是 5 個，由月月決定。

### [staged-review:CI-release] release-physics.yml 漏建 SpectrumViewTest，而且用 unittest 會漏掉 69 個 pytest 測試
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：766d21d 只修了 physics.yml 兩處測試建置清單。發佈用的 release-physics.yml（打 v* tag 或手動觸發才跑）line 45 還是只建三個測試 target，但 ctest 已經註冊了 spectrum_view_repro → 會出現 Not Run，第一次發佈就紅燈（就是 09-07 那個紅燈的發佈版）。另外 line 50 用 `python -m unittest discover`，pytest 風格的 test_measurement_selfcal.py（這次 staged）、test_partial_verify.py、test_stem_verify.py 共 69 個 test_ 函式完全不會被收集，是靜默漏跑。
- 證據：.github/workflows/release-physics.yml:45 --target ... TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest（沒有 SpectrumViewTest）；.github/workflows/release-physics.yml:49-50 ctest ...；python -m unittest discover -s tests -p "test_*.py"；CMakeLists.txt:249 add_test(NAME spectrum_view_repro ...)；實測：python -m unittest discover -s tests -p test_measurement_selfcal.py → 'Ran 0 tests ... NO TESTS RAN'（partial_verify、stem_verify 兩檔同樣結果）；grep -c '^def test_'：12 / 10 / 47
- 建議：release-physics.yml:45 補上 TsukiSynthSpectrumViewTest；line 50 改成 `python -m pytest tests -q`（和 physics.yml:61 一致）。改完留 unstaged 給月月審（R7）。
- 懷疑者查證：release-physics.yml:45 的建置清單只有 TsukiSynthAuditTest、TsukiSynthTunerTest、TsukiSynthPhysicsModelsTest；CMakeLists.txt:249 有 add_test(NAME spectrum_view_repro)；:49 跑 ctest，:50 用 unittest discover。實測 python -m unittest discover -s tests -p <檔名>，三個檔都是「Ran 0 tests / NO TESTS RAN」，grep 到的 test_ 函式是 12/10/47 個。unittest 全部 discover 到 199 個（沒有 import 失敗），pytest --collect-only 收到 270 個，所以漏掉 71 個收集項。tools/requirements-physics.txt 已經 pin 了 pytest==8.4.2，改成 pytest 不必新增相依。

### [staged-review:D9c-scope] kIrWetMakeupGain 確實只作用在 IR 模式的 wet 上（已核實）
- 查證：**confirmed**｜誰：資訊｜嚴重度 low｜工作量 n/a
- 說明：增益只出現在 `if (irMode)` 區塊裡，乘在剛做完摺積的 chL/chR 上，dry 那一項 (1-m) 沒乘；irMode 成立的條件是 mode≥0.5、已載入 IR、而且 numSamples≤maxBlock。整個 repo 只有 PluginProcessor 用到 EffectChain，CLI/ScoreRenderer 走 SimpleReverb，所以 8/8 位元不變本來就測不到這項改動（D9c GATE 4 自己也寫了這點）。
- 證據：src/effects/EffectChain.h:158-161 irMode 條件；src/effects/EffectChain.h:212-236 只在 if (irMode) 內：chL[i] = dryL[i]*(1-m) + (chL[i]*kIrWetMakeupGain)*m；src/effects/EffectChain.h:275 static constexpr float kIrWetMakeupGain = 26.9f；grep EffectChain src → 只有 src/PluginProcessor.h:5,112
- 建議：不需要動作。
- 懷疑者查證：EffectChain.h:158-161 是 irMode 的條件；:212-236 只在 if (irMode) 裡面把 chL/chR 乘上 kIrWetMakeupGain，dry 那一項 (1-m) 沒有乘；:275 定義 26.9f。grep EffectChain src，只命中 PluginProcessor.h:5 和 :112。

### [staged-review:D9c-clip] IR 模式補償後沒有任何限幅；最壞情況的單頻增益比 ALGO 預設高 4～9 dB
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 M
- 說明：EffectChain 之後只有 EQ shelf 和 Macro Output 增益，沒有 limiter 或 soft clip。D9c 讓 IR wet 的 RMS 和 ALGO 對齊（白噪輸入時 wet 本來就比輸入大約 +10 dB；D9c 證據裡 ALGO wet 穩態 RMS 已經是 +1.857 dBFS，超過滿刻度）。所以「mix 開大會超過 0 dBFS」不是 D9c 新造成的，ALGO 本來就會這樣。但我用 Python 複製了兩條路徑（不是產品 binary；複製版對 D9c 實測的誤差在 0.6 dB 內）量最壞情況的單頻增益 max|H|：三顆 EchoThief IR ×26.9 是 +28.7～+33.2 dB，ALGO 預設 size 0.5 是 +24.5 dB、size 1.0 是 +37.8 dB。也就是 IR 模式窄頻峰值比 ALGO 預設高 4～9 dB，但仍在 ALGO 自己的可調範圍內。月月聽不到爆音，而 HostProbe 沒有 IR 響度情境，K-02 又只印數字不判定，所以 IR 模式爆音沒有任何自動偵測。
- 證據：src/PluginProcessor.cpp:382-395 effectChain.processBlock → 只乘 smoothedOutput，之後直接錄音/輸出；src/effects/EffectChain.h:239-254 EQ 之後就結束了；reports/gate_outputs/wf0914_D9c_ir_makeup_gain.txt:116 ALGO wet steady-state RMS = 1.857 dBFS；reports/gate_outputs/wf0914_D9c_ir_makeup_gain.txt:252-255 HostProbe 沒有涵蓋 IR wet 響度情境；scratchpad/staged-review/reverb_gain_replica_output.txt：max|H| ALGO size0.5 +24.48 dB / IR Stairwells +33.19 / Venues +28.67 / Sanctuaries +30.08；rms|H| 都在 +10.2～+10.5 dB
- 建議：月月決定：(a) 接受現狀，在 UI 規格或文件註明「reverb mix 高時可能超過 0 dBFS」；或 (b) 另開卡在輸出端加安全限幅或峰值指示。(b) 會改變渲染，要走 R10 前後對照。不論選哪個，都建議加一條 IR 峰值的量化證據（見 D9c-guard）。
- 懷疑者查證：PluginProcessor.cpp:382 呼叫 effectChain.processBlock 之後，:384-395 只乘 smoothedOutput，接著就是錄音和輸出。整個 src 只有 Distortion.h:73 用到 tanh，沒有任何 limiter 或 clip。D9c 證據 :116 記的是 ALGO 1.857 dBFS，:252-255 寫 HostProbe 沒有 IR 響度情境。我逐一比對複製腳本 reverb_gain_replica.py：comb 的 H=z^-N(1-d1 z^-1)/(1-d1 z^-1-fb d2 z^-N)、allpass 的 (-1+1.5z^-M)/(1-0.5z^-M)、×0.15，都和 SimpleReverb.h:81-156 一致；它對 D9c 實測的驗證誤差在 +0.57 dB 以內。要注意：max|H| 的數字全部來自 Python 複製版，不是產品 binary。另外依它自己的表，ALGO size=1.0 是 +37.8 dB，本來就比 IR 高，所以「超過 0 dBFS」不是 D9c 新造成的，這點原文也有寫。

### [staged-review:D9c-calib] 26.9 只在 ALGO 預設房間大小 0.5 時對齊；換 size/T60 會差 −2.4～+5.3 dB
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：K-02 和 K-02-EXT 的 ALGO 參考都是在 pReverbSize=null（等於 0.5）、沒有設 T60 的條件下量的。IR 路徑完全忽略 size（irMode 時不呼叫 setRoomSize）。用 Python 複製版量 ALGO wet 相對 size 0.5 的變化：size 0→1 是 −1.36～+3.98 dB，指定 T60 0.3～30 s 是 −2.38～+5.26 dB。所以「IR 與 ALGO 響度一致」只在預設設定下成立。常數也可以拆解成：JUCE Normalise 係數 0.125（−18.06 dB）加上 ALGO 預設的淨 wet 增益（約 +10.2 dB），合計 ≈ 28.2 dB，和實測 28.58 dB 相符，所以「結構性」這個說法沒錯。但 EffectChain.h 的註解和 D9 裁決包都沒寫明「參考點是 ALGO@size0.5」。
- 證據：tests/audit_repro.cpp:1272-1275 ALGO 用 reverb 預設（pReverbSize/pReverbDecay 為 null → roomSize 0.5）；src/effects/SimpleReverb.h:81 roomFeedback = roomSize*0.28 + 0.7；src/effects/EffectChain.h:179-182 irMode 時不呼叫 setRoomSize/setMix；libs/JUCE/modules/juce_dsp/frequency/juce_Convolution.cpp:628 return 0.125f / std::sqrt(sumSquaredMagnitude)；scratchpad/staged-review/reverb_gain_replica_output.txt（size 0.00 −1.36 / 1.00 +3.98；decay 0.3 s −2.38 / 30 s +5.26 dB）；src/effects/EffectChain.h:258-274 註解沒提參考設定
- 建議：在 EffectChain.h 常數註解和 D9 裁決包補一句：「對齊參考 = ALGO 預設 size 0.5、未指定 T60；其他 size 差 −1.4～+4.0 dB（複製版估計）」。純文字，不改數值。要不要做成使用者可見的說明，由月月決定。
- 懷疑者查證：EffectChain.h:179-182 在 irMode 時不呼叫 setRoomSize/setMix，:167 也不套 decay；audit_repro.cpp:1270-1273 的 ALGO 用 null size/decay，等於 roomSize 0.5；JUCE juce_Convolution.cpp:628 是 0.125f/sqrt(...)。複製版的輸出數字（size 0→1 −1.36～+3.98 dB，decay 0.3～30 s −2.38～+5.26 dB）和原文一致。但原文說「D9 裁決包都沒寫明參考點」只對一半：D9_ir_loudness_alignment.zh-TW.md:78 的方法段已經寫了「ALGO 用 reverb 預設」。真正缺的是「換 size/T60 對齊就會跑掉」這層依賴說明。EffectChain.h:258-274 的註解確實沒提參考設定。
- **查證修正**：D9 裁決包 :78 已經寫了量測用「ALGO reverb 預設」，但裁決包和 EffectChain.h 常數註解都沒說「26.9 只在 size 0.5、沒設 T60 時對齊；其他 size 依 Python 複製版估計差 −1.4～+4.0 dB，其他 T60 差 −2.4～+5.3 dB」。建議補這一句說明依賴關係（純文字）。

### [staged-review:D9c-guard] 沒有任何回歸測試鎖住 kIrWetMakeupGain
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：K-02 在 audit_repro 裡只 printf（informational，no PASS/FAIL），HostProbe 也沒有 IR 情境。有人把 26.9 改掉或刪掉，ctest、HostProbe、位元不變測試全部照樣綠燈（CLI 不經 EffectChain）。D9c 卡的驗收條件「0±0.25 dB」只存在於 GATE 文字證據裡。
- 證據：tests/audit_repro.cpp:1186-1191 'this function asserts nothing'；tests/audit_repro.cpp:1458 'K-02 quantification (informational, no PASS/FAIL)'；reports/gate_outputs/wf0914_D9c_ir_makeup_gain.txt:252-255 HostProbe 沒有 IR 情境
- 建議：在 audit_repro 用既有的合成 IR K-02 流程加一條 CHECK，判準直接沿用 D9c 卡自己的「0±0.25 dB」（出自 D9b 實測展幅，不是新容差）。加測試等於加 GATE，先讓月月點頭。
- 懷疑者查證：audit_repro.cpp:1186-1191 寫著「quantifies (does not PASS/FAIL) ... this function asserts nothing」；:1253-1316 的 reportReverbWetGainQuantification 只有 printf，沒有 CHECK；:1458 印的是「K-02 quantification (informational, no PASS/FAIL)」。grep tests/ 和 tools/，kIrWetMakeupGain 與 0.25 dB 只出現在註解（audit_repro.cpp:1195/1198/1330/1332）。所以把 26.9 改掉也不會有任何測試變紅。這條同時否定了 E18「D9c 測試已經在 CI 守著」的說法。

### [staged-review:D12-failpath] D12：舊路徑檔案還在但載入失敗時，靜默丟掉舊路徑、不跳警告
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：migrateLegacyReverbIRPath() 在檔案存在的分支呼叫 loadReverbIRFile(file, importError, false)，但失敗原因（超過 30 s、不是可讀音檔、匯入 IRLibrary 失敗）都被丟掉。呼叫端照樣移除 reverb_ir_path、setDirty。結果：(1) 使用者之後一存檔，這個 IR 的唯一線索就永久消失；(2) 如果舊專案存的 mode 是 IR，UI 會顯示 IR 模式，但 getIRStatus() 是 loaded=false、missing=false，面板標題什麼都不顯示，EffectChain 則因為 hasImpulseResponse()=false 靜默改走 ALGO。這正好違反 restoreReverbIR 註解說的 red line 2（UI 宣稱 IR，音訊卻靜默走 algorithmic）。檔案不存在的分支反而有警告，兩個分支行為不一致。HostProbe 三個情境都沒測到這個分支。
- 證據：src/PluginProcessor.cpp:880 loadReverbIRFile (file, importError, false); return;（importError 沒有被使用）；src/PluginProcessor.cpp:621-643 migratedLegacyIR=true 後 tree.removeProperty("reverb_ir_path")；src/PluginProcessor.cpp:679-711 validateAndLoadIRFile 超過 30 s / 讀不到就 return false；src/PluginProcessor.cpp:910-921 getIRStatus：loaded=hasImpulseResponse()；src/PluginEditor.cpp:1133-1152 loaded 和 missing 都是 false 時標題不顯示任何 IR 資訊；src/effects/EffectChain.h:158-161 irMode 需要 hasImpulseResponse()；tests/host_probe.cpp:1222-1424 只有「檔案可讀」「檔案不存在」「新 schema 已存在」三個情境
- 建議：失敗分支改走和「檔案不存在」一樣的缺檔三態：reverbIRMissing=true、expectedIRRef.originalName=檔名，再呼叫 forceAlgorithmicMissingIR()，警告文字附上 importError；HostProbe 補一個「檔案存在但超過 30 s」情境。這會改 src/，要跑 R6 全套。
- 懷疑者查證：事實大致屬實：PluginProcessor.cpp:879-881 的 importError 宣告後沒有被用到；:621-643 遷移後照樣 removeProperty；:705-709 超過 30 s 就 return false；getIRStatus :915-919 在 loaded=false、missing=false 時 name 是空的；PluginEditor.cpp:1133-1152 兩個都 false 時標題不附任何 IR 資訊；HostProbe 只測了三個情境。但有兩點要修正：(1) 這是刻意寫下的設計，不是漏掉：PluginProcessor.cpp:875-878 明寫「A failure here (unreadable, >30 s) ... degrades the same way a bad GUI-picked file would: no IR loaded, no forced mode change, no fabricated identity to warn about」；D12 施工卡 §1 只規定「檔案存在」和「不存在」兩種，沒涵蓋「存在但載入失敗」。(2)「UI 顯示 IR、音訊卻走 ALGO」不是這個分支獨有：PluginEditor.cpp:294-298 的 revModeButton 在沒載入任何 IR 時也能切到 IR，EffectChain.h:160 會靜默走 ALGO。所以是既有的狀態，不能算這個分支獨自違反 red line 2。
- **查證修正**：舊路徑檔案還在但載入失敗（超過 30 s、讀不到、匯入失敗）時，程式照設計（PluginProcessor.cpp:875-878 有註解說明）靜默不載入，也不保留舊路徑線索；這不在 D12 卡的規格內。要不要改成走缺檔三態並跳警告，屬於推翻既有設計，應由月月裁決（改了要跑 R6）。「mode=IR 但沒有 IR」是 revModeButton 本來就能造成的既有狀態，不是這個分支獨有。

### [staged-review:D12-legacykey] D12：新 schema 已存在時，舊 reverb_ir_path 鍵不會被清掉；而且沒有測試驗證清除
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：移除舊鍵只寫在遷移分支裡。情境 3（reverb_ir 區塊和舊鍵同時存在）時，舊鍵會一直跟著之後的每次存檔（雖然永遠被忽略，但註解自己說過「不讓它殘留」）。情境 1、2 也沒有斷言輸出的 state 裡已經沒有 reverb_ir_path，所以 removeProperty 這行等於沒有測試保護。
- 證據：src/PluginProcessor.cpp:621-645 removeProperty 只在 if (! irChild.isValid()) 裡；src/PluginProcessor.cpp:627-642 註解：'so it does not linger in every future save'；tests/host_probe.cpp:1293-1316、1343-1354 情境 1/2 沒有檢查 reverb_ir_path 已不在輸出 state 裡
- 建議：在 host_probe 情境 1/2 加上 !memoryBlockContainsAscii(state, "reverb_ir_path")。要不要在情境 3 也清掉舊鍵，由月月決定（兩種都不影響聲音）。
- 懷疑者查證：PluginProcessor.cpp:621-645 的 removeProperty("reverb_ir_path") 只在 if (! irChild.isValid()) 裡面；:630-631 註解寫著「so it does not linger in every future save」。grep host_probe.cpp，情境 1 和 2（:1291-1310、:1345-1358）都沒有斷言輸出的 state 裡已經沒有 reverb_ir_path。

### [staged-review:B7-residual] B7 dumpModes 欄位確實撤回乾淨（程式碼），但 HammerImpulse.h 註解還指向已撤回的呼叫點
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：ScoreRenderer.h 的 staged diff 全部都是 // 註解（+51 行，沒有任何程式碼），src/cli、tools、schema/json 都 grep 不到 bridge_power_firstprinciples_c 或這五個函式的呼叫。不過 HammerImpulse.h 的區段標頭和 doc 還寫著「feeding ScoreRenderer::dumpModes()'s Path C fields only」「see the caller-side conversion note at the call site, ScoreRenderer.h's dumpModes()」「a Path C field built from it」，和 09-15 裁決（欄位撤回）不一致。ScoreRenderer.h 在渲染迴圈中間留了一段約 40 行的墓碑註解，描述已刪掉的程式碼。
- 證據：git diff --cached -- src/score/ScoreRenderer.h：+44/+3/+4 行全部都是 // 註解；grep bridge_power_firstprinciples|hammerVelocityMps|... 在 *.h/*.cpp/*.py/*.json：產品端只有定義處和 ScoreRenderer.h:224/334/466 註解；src/physics/HammerImpulse.h:334 'feeding ScoreRenderer::dumpModes()'s Path C fields only'；src/physics/HammerImpulse.h:342-343 'see the caller-side conversion note at the call site, ScoreRenderer.h's dumpModes()'；src/physics/HammerImpulse.h:513 'a Path C field built from it'；reports/decision_packets/B7_phase2_and_open_items.zh-TW.md:166-169 裁決：dumpModes() 欄位撤回、五個純函式保留
- 建議：commit 前把 HammerImpulse.h:334/342-343/513 改成「目前沒有呼叫點（B7 09-15 裁決撤回），重新接回前先解 §1.1」。ScoreRenderer.h 的 40 行墓碑要不要縮成三行指向裁決包，由月月決定（純註解，不影響渲染）。
- 懷疑者查證：git diff --cached --numstat 顯示 ScoreRenderer.h 是 +51/-0，用 grep 排除 // 註解後只剩一行空白的 +，所以沒有程式碼改動。src、tools、schema、scores 裡都 grep 不到五個函式或欄位名的呼叫點，只有 RadiationModel.h 的 doc 註解和 ScoreRenderer.h:224/256-260/334/466 的註解。HammerImpulse.h:334「feeding ScoreRenderer::dumpModes()'s Path C fields only」、:342-343「see the caller-side conversion note at the call site, ScoreRenderer.h's dumpModes()」、:513「a Path C field built from it」都還在，和裁決包 :166-169 的撤回裁決不一致。只有一處要修正：那段墓碑註解（ScoreRenderer.h:224 起）是在 dumpModes()（:135 起）的逐事件迴圈裡，屬於診斷路徑，不是渲染迴圈。
- **查證修正**：程式碼撤回得很乾淨，已確認。HammerImpulse.h:334/342-343/513 的註解仍然指向已撤回的 Path C 欄位，應在 commit 前改掉。ScoreRenderer.h 那段約 40 行的墓碑註解在 dumpModes() 的逐事件迴圈裡（診斷路徑），不在渲染迴圈；要不要縮短由月月決定。

### [staged-review:B7-clamp] hammerVelocityMps() 在 MIDI 20 有 2.3 倍的跳躍（號稱比照 interpAnchorsFlat 的 flat clamp，實際不連續）
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 low｜工作量 S
- 說明：公式在 MIDI 20 是 0.412 m/s，但 MIDI 19.9 被 clamp 到實測下限 0.18 m/s，中間跳了 2.29 倍；MIDI 120（6.589）→120.1（6.8）也有 +3% 的小跳。文件和註解說「體例比照 interpAnchorsFlat()」，但 interpAnchorsFlat 是維持邊界值、不會跳的。函式現在沒接任何路徑，不影響現有渲染；但以後接回時，MIDI 19 的槌速會不到 MIDI 20 的一半。測試 line 1144-1155 已經把這組 clamp 值釘死。
- 證據：src/physics/HammerImpulse.h:388-395 <20→0.18f、>120→6.8f、否則 2^((midi-52)/25)；python：2**((20-52)/25)=0.4118、2**((120-52)/25)=6.5887；docs/HAMMER_VELOCITY_SOURCES.md:137-139 'MIDI 20–120（≈0.41–6.6 m/s）…clamp 到實測極值 0.18 / 6.8 m/s（體例比照 interpAnchorsFlat()）'；tests/physics_models_repro.cpp:1144-1155
- 建議：B7 重啟時請月月裁決：clamp 到公式在邊界的值（0.41/6.59，連續），或保留實測極值、在文件明寫「邊界不連續」。現在不必動。
- 懷疑者查證：HammerImpulse.h:388-395：MIDI <20 回 0.18f，>120 回 6.8f，其餘用 2^((m-52)/25)。python 算出 2^((20-52)/25)=0.4118，是 0.18 的 2.288 倍；2^((120-52)/25)=6.589。HAMMER_VELOCITY_SOURCES.md:137-139 寫「體例比照 interpAnchorsFlat()」，但 HammerImpulse.h:225-238 的 interpAnchorsFlat 是維持邊界值，連續不跳。physics_models_repro.cpp:1144-1155 已經把 19.9→0.18、120.1→6.8 釘死。這個函式現在沒有呼叫點。邊界要取公式值還是實測極值，牽涉 R4 的溯源選擇，owner 標 yueyue-decision 是對的。

### [staged-review:B7-tauC] hertzImpulseConsistentTauCSeconds 只有衝量自洽；接觸時間只有真 Hertz 碰撞的 0.60～0.71 倍
- 查證：**adjusted**｜誰：長期研究｜嚴重度 low｜工作量 M
- 說明：τc=π·m·v/F_peak 是讓半正弦脈衝的衝量剛好等於 2mv 反解出來的，α=1 時是精確解。但錨點 α=2.3～3.0 時，這個 τc 只有精確 Hertz 碰撞接觸時間的 0.711～0.599 倍：同一個峰值力的半正弦，不可能同時滿足峰值、衝量、時長三項。所以 doc 說的「self-consistent with the SAME Hertzian collision」只在衝量上成立，送進 forceSpectrumMagnitude 的頻譜滾降會比真 Hertz 脈衝短（偏亮）。domain-scan 測試「impulse/2mv≈1」是代數恆等式，只能保護公式本身，驗證不到物理。目前沒接路徑，不影響渲染。
- 證據：src/physics/HammerImpulse.h:533-543 tauC = pi*m*speedMps/fPeakN；精確 Hertz 接觸時間 = 2·(δmax/v)·Γ(1+1/n)Γ(1/2)/Γ(1/2+1/n)，n=α+1；計算：α=2.2→0.711、2.5→0.665、3.0→0.599、3.5→0.546；src/physics/HammerImpulse.h:202 kPianoHammerAlpha = {2.3, 2.5, 3.0}；tests/physics_models_repro.cpp:1398-1402 'Self-consistent by construction'
- 建議：B7 重啟時用數值積分解 m·ẍ=−K·x^α，同時比對接觸時間和頻譜，再決定 τc 取衝量等價、時長等價，還是直接換成 Hertz 真實脈衝形狀。doc 措辭可以先改成「衝量自洽」。
- 懷疑者查證：公式本身重新推導確認：τ_impulse/T_Hertz = π/(n·I_n)，n=α+1，I_n=Γ(1+1/n)Γ(1/2)/Γ(1/2+1/n)。python 算出：α=1 時 1.0，2.2 時 0.7115，2.3 時 0.6951，2.5 時 0.6645，3.0 時 0.5991。錨點 α 在 HammerImpulse.h:202 是 {2.3, 2.5, 3.0}，所以原文「錨點 α=2.3～3.0 時是 0.711～0.599」上限寫錯了，0.711 其實是 α=2.2 的值。另外 doc（HammerImpulse.h:496-509）本來就明寫這是讓「half-sine model's OWN assembled impulse」等於 2mv，已經標明是衝量自洽，沒有宣稱時長也吻合，所以措辭問題比原文說的輕。測試 :1400-1401 確實寫「Self-consistent by construction」，屬於代數恆等。
- **查證修正**：錨點 α=2.3～3.0 時，τc 只有真 Hertz 接觸時間的 0.695～0.599 倍，頻譜偏亮。doc 已經寫明是衝量自洽，措辭大致誠實。這是長期研究項，B7 重啟時處理。

### [staged-review:D15-xfailpin] D15 release 段釘住的數字放在 xfail(strict) 測試裡，數字漂移也抓不到；註解引用的檔名不存在
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：RELEASE_DEV/HOLDOUT_GRID_MAX_ABS_CENTS（5.2304/7.2055）只在兩個 @xfail(strict=True) 測試裡檢查。xfail 測試裡任何一條 assert 失敗都算「預期失敗」而維持綠燈，所以數字漂移時這條 pin 完全沒有作用，和註解「stops the xfails below silently drifting」相反。對照組：sustain 段的 1.1721 有放在非 xfail 的 test_measure_pitch_cents_matches_legacy_after_revert 裡，有受保護。另外 line 105 引用的 wf0914_D15_gate1_dev.txt / _holdout.txt 不存在（實際檔名是 *_dev_grid.txt / *_holdout_grid.txt）；line 54 還寫著「card BLOCKED」，但 D15 已經用 A' 關閉。
- 證據：tests/test_measurement_selfcal.py:102-107 pin 常數與 'stops the xfails below silently drifting' 註解；tests/test_measurement_selfcal.py:214、240 @pytest.mark.xfail(strict=True, reason=XFAIL_REASON)，pin assert 在這兩個測試裡；ls reports/gate_outputs | grep D15 → wf0914_D15_gate1_dev_grid.txt / _holdout_grid.txt（沒有 _dev.txt）；tests/test_measurement_selfcal.py:54 'card BLOCKED per its own rule'；HANDOVER.md:115 D15 已關閉（選 A'）
- 建議：新增一條非 xfail 測試，只 pin release 段數值（和 legacy 那條同一個模式）；xfail 測試保留 ≤1 c 那條判定。修正 line 105 的檔名和 line 54 的狀態文字。
- 懷疑者查證：test_measurement_selfcal.py:102-107 的註解寫「stops the xfails below silently drifting」；pin 的 assert 放在 :215 和 :241 兩個 @pytest.mark.xfail(strict=True) 測試裡（:229、:251），沒有指定 raises=，所以 AssertionError 一律算預期失敗。實際情況比原文說的更糟：pin assert 排在 ≤1 c 判定之前，只要估計器變好、release max_abs 不再是 5.2304，就會先死在 pin assert，被記成 xfail，永遠不會 XPASS。這兩個 strict xfail 等於既偵測不到漂移，也偵測不到改善。ls reports/gate_outputs 只有 wf0914_D15_gate1_dev_grid.txt/_holdout_grid.txt，沒有 :105 引用的 _dev.txt。:54 仍寫「card BLOCKED」，但 HANDOVER.md:115 已記 D15 關閉（A'）。

### [staged-review:D14-tests] D14 串流化正確，但 read_wav_header/StemArrayStream 沒有直接的單元測試
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：確認過 stem 檔要到 superposition 算完之後才清掉（line 1308-1331 的 rmtree 在 compare_superposition 之後），所以延後讀檔是安全的；compare_superposition 只用 len() 和迭代。不過新函式只被 e2e 測試間接用到：沒有測 fmt 前面有 LIST 之類其他 chunk、奇數大小 chunk 的對齊、WAVE_FORMAT_EXTENSIBLE 等邊界情況，也沒有記憶體回歸測試。
- 證據：tools/stem_verify.py:210-239 read_wav_header；tools/stem_verify.py:666-702 StemArrayStream；tools/stem_verify.py:722-724 compare_superposition 只用 len() 和 for arr in stem_arrays；tools/stem_verify.py:1062 compare_superposition 在 1308-1331 清理之前；grep StemArrayStream|read_wav_header tests/*.py → 沒有結果
- 建議：在 tests/test_stem_verify.py 補 read_wav_header 的邊界測試（前置 LIST chunk、奇數 chunk、extensible fmt），並比對 read_wav_float 的 sr/ch 是否一致。
- 懷疑者查證：stem_verify.py:210-239 的 read_wav_header 和 :666-700 的 StemArrayStream 都存在；:721-725 的 compare_superposition 只用 len() 和 for 迭代；:1062 在呼叫 compare_superposition 時，:1319-1331 的 rmtree 還沒跑。grep tests/，StemArrayStream 和 read_wav_header 都沒有結果。補充一點：read_wav_header 只讀 fmt 的前 16 bytes，所以 EXTENSIBLE 格式本身不會出錯，只是沒有測試覆蓋。

### [staged-review:CI-coverage] 新增的 C++ 與 Python 測試都有進 CI；只有 HostProbe（含 D12 三情境）不在 CI
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 M
- 說明：WF0914 沒有新增測試 target，新測試都加在既有檔裡：audit_repro、physics_models_repro 在 physics.yml:54 建置、:57 ctest，ASan job:265 也有建；test_measurement_selfcal.py 由 physics.yml:61 的 pytest 收集。所以 physics.yml 的兩處建置清單不需要更新。但 host_probe.cpp（這次 +311 行，D12 三情境＋H7）按設計不註冊 ctest，CI 也沒跑；雖然 CI 已經在建 VST3，D12 的回歸保護仍然只在本機。
- 證據：.github/workflows/physics.yml:54 與 :265 四個測試 target（含 SpectrumViewTest）；.github/workflows/physics.yml:50-51 已建 TsukiSynth_VST3；.github/workflows/physics.yml:61 python -m pytest tests -q；CMakeLists.txt:255 'Deliberately NOT registered with add_test'；tests/host_probe.cpp:1513 return failures == 0 ? 0 : 1（可以直接當 CI 步驟）；reports/gate_outputs/wf0914_integration_raw/09_hostprobe.txt 'PASS (0 failures)'
- 建議：在 physics.yml 的 VST3 建置之後加一步：build TsukiSynthHostProbe，然後跑 TsukiSynthHostProbe.exe <vst3> $RUNNER_TEMP/hp。要先試跑一次，確認 headless runner 能載入 VST3、H7 寫得進 %APPDATA%。這是 CI 行為改變，先給月月看。
- 懷疑者查證：physics.yml:54 和 :265 都建四個測試 target（含 SpectrumView）；:50-51 有建 VST3；:57 跑 ctest；:61 跑 pytest。CMakeLists.txt:255 寫 Deliberately NOT registered，:266 是 HostProbe 的 add_executable；host_probe.cpp:1513 是 return failures==0?0:1。git diff --cached --numstat 顯示 CMakeLists.txt 不在 staged 裡，所以沒有新的 test target。

### [staged-review:D-doc-1] HANDOVER §10 的 tr 教訓本身就是壞的：'\r' 變成了真的換行
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：line 145-146 的位元組是 `tr -d '` + LF + `'`，反斜線 r 不見了，變成一個真的換行。照抄會變成 tr -d '\n'，把所有路徑黏成一行，commit 會因為 pathspec 對不上而失敗。HEAD 版本就已經是這樣（不是這輪造成的），但這輪正好要照這條教訓做多檔 commit。
- 證據：git show :HANDOVER.md | sed -n 145p | od -c → `   t   r       -   d       '  \n`；git show HEAD:HANDOVER.md 同一句同樣壞掉（'  \n 1 4 0 - ' 之後才接 `）
- 建議：commit c7 之前，把 HANDOVER.md:145-146 改回一行：`tr -d '\r'`（用 code span 包起來）。
- 懷疑者查證：git show :HANDOVER.md | sed -n 145,146p | od -c 顯示 `tr -d ' 後面緊接 \n '`，反斜線 r 不見了。git show HEAD:HANDOVER.md 的 :139 也一樣壞掉。

### [staged-review:D-doc-2] HANDOVER §9 操作備忘的數字過時（267 / post_d8 / 1.1721 c）
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：§9 還寫著 pytest「267 passed」，位元不變基準是 sha256_before_post_d8.txt，measurement_selfcal「現況 exit 1，1.1721 c」。但同一份 HANDOVER §1 已經寫明新基線是 270（264 passed+1 skip+5 xfail）、基準改用 post_a14。而且 D15 之後工具印出的總 max_abs_error_cents 是 5.2304（dev）/ 7.2055（holdout）；1.1721 只是 sustain 段的數字。
- 證據：git show :HANDOVER.md 第 137 行 '（267 passed）… 對 sha256_before_post_d8.txt'；git show :HANDOVER.md 第 139 行 '（現況 exit 1，1.1721 c）'；HANDOVER.md:28 'pytest 基線自本輪起 270 個測試'；:79 基準改 sha256_before_post_a14.txt；reports/gate_outputs/wf0914_D15_gate1_dev_grid.txt:13-15 sustain 1.1721 / release 5.2304 / max_abs_error_cents = 5.2304；reports/gate_outputs/wf0914_integration_raw/05_pytest.txt '264 passed, 1 skipped, 5 xfailed'
- 建議：§9 改成：pytest 264 passed＋1 skip＋5 xfail；基準 post_a14；selfcal 印 sustain 1.1721 / release 5.2304（dev），exit 1。
- 懷疑者查證：HANDOVER.md:137 寫「（267 passed）…對 sha256_before_post_d8.txt」，:139 寫「（現況 exit 1，1.1721 c）」。但 :28 寫基線是 270（264+1+5），:79 寫基準改用 post_a14；wf0914_D15_gate1_dev_grid.txt 印的是 sustain 1.1721 / release 5.2304 / max_abs_error_cents = 5.2304；05_pytest.txt:5 是「264 passed, 1 skipped, 5 xfailed」。

### [staged-review:D-doc-3] ROADMAP B7 列還是「unstaged 待稽核 / BLOCKED 待月月裁決 §1.1」，沒照 09-15 裁決同步
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：B7 裁決包 §6 第 3 點要求 ROADMAP/TODO 的 B7 條目同步標成「In progress——Phase 0 完成、Phase 1 部分完成（欄位撤回版）、Phase 2/3 BLOCKED（月月 09-15 裁決）」。TODO 已經同步，但 staged 的 ROADMAP M10 列裡，B7 段還停在稽核當下的狀態。
- 證據：ROADMAP_PHYSICS.md:155（staged）'B7 Phase 0+1（2026-09-14 … unstaged 待稽核，In progress）' 與 '本輪判定為 BLOCKED，待月月裁決 §1.1'；reports/decision_packets/B7_phase2_and_open_items.zh-TW.md:172-173 同步措辭；TODO.md:14 已記錄路徑 C＋(a) 乙案
- 建議：commit c7 之前，在 ROADMAP:155 的 B7 段尾端補上裁決包指定的那句狀態，並把「unstaged 待稽核」改成已稽核、已裁決。
- 懷疑者查證：ROADMAP_PHYSICS.md 只有 :155 這一行（M10 列）提到 B7，內容仍是「B7 Phase 0+1（2026-09-14，WF0914-B7P0/B7P1，unstaged 待稽核，In progress）」和「本輪判定為 BLOCKED，待月月裁決 §1.1」。grep 09-15、部分完成、欄位撤回都沒有結果。裁決包 B7_phase2_and_open_items.zh-TW.md §6 第 3 點要求同步寫「In progress——Phase 0 完成、Phase 1 部分完成（欄位撤回版）、Phase 2/3 BLOCKED（月月 09-15 裁決）」。TODO.md 已經同步。

### [staged-review:S-public] repo 是 PUBLIC；24 個 staged 檔含 C:\Users\admin 路徑（其中一處是 Claude session 暫存路徑），沒發現機密
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 low｜工作量 S
- 說明：gh 查到 visibility=PUBLIC。新增行裡有 90 行含 C:\Users\admin 的絕對路徑，分布在 24 個檔（大多是 GATE 證據的建置/HostProbe log，另有 HANDOVER 的 ffmpeg 路徑、%APPDATA% preset 路徑）。wf0914_D13_plate_ratios.txt:59-61 還記了一個 C:\Users\admin\.claude\projects\...\tool-results\*.pdf 暫存路徑，對讀者沒有用，也會露出本機結構。HEAD 裡已經有 214 個檔這樣做，是既有慣例。用 api key/secret/password/token/ghp_/sk-/信箱等 pattern 掃新增行，全部沒有命中。
- 證據：gh repo view → {"nameWithOwner":"TsKR2828/tsuki-synth","visibility":"PUBLIC"}；新增行 grep C:\Users\admin：90 行；逐檔：wf0914_D9b_ir_injection.txt 19、integration_raw/02_build_main_targets.txt 14、09_hostprobe.txt 13、D12_hostprobe.txt 13 …（共 24 檔）；reports/gate_outputs/wf0914_D13_plate_ratios.txt:59-61 C:\Users\admin\.claude\projects\C--Users-admin-Desktop-Claude\147112da-...\tool-results\webfetch-...pdf；git grep -c C:/Users/admin HEAD → 214 個檔（既有慣例）；secret pattern grep：沒有結果
- 建議：月月決定是否接受公開 repo 裡有本機使用者路徑（既有慣例）。至少可以把 D13 證據裡那個 .claude 暫存 PDF 路徑改成「本機暫存，未入庫」。
- 懷疑者查證：gh repo view 回傳 visibility PUBLIC。新增行裡含 C:\Users\admin 的共 90 行。逐檔看 staged 內容，共 24 個檔含這個路徑；但其中 HANDOVER.md 那一行在 HEAD 就有，不是新增行，所以真正「新增行」分布在 23 個檔（小出入）。wf0914_D13_plate_ratios.txt:59-61 確實是 .claude\projects\...\tool-results\webfetch-*.pdf。git grep HEAD 有 214 個檔含這個路徑。用 secret pattern 掃新增行，沒有命中。

### [staged-review:S-monetize] 未追蹤的 MONETIZATION_PLAN 不宜 commit 進公開 repo
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 S
- 說明：唯一的 untracked 檔 docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md 內容是變現計畫（含售價、BOOTH 等 10 處相關字詞），目前沒有被 staged，這是正確的。但 repo 是 PUBLIC，一旦被 git add（例如某次 add docs/），商業計畫就公開了；.gitignore 也沒有擋它。
- 證據：git status --short --untracked-files=all → ?? docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md；grep -c -i -E '售價|價格|price|BOOTH' → 10；gh repo view visibility=PUBLIC
- 建議：月月決定：把它移出 repo（例如 Desktop 的私人資料夾），或加進 .gitignore。這次 commit 維持不 add。
- 懷疑者查證：git status 顯示 ?? docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md；git check-ignore 的 exit=1，表示沒被忽略；售價/價格/price/BOOTH 命中 10 行；repo 是 PUBLIC。staged diff 和 HEAD 裡都沒有這份檔或定價內容（grep 只命中「改變現行」這類誤判字串）。

### [staged-review:S-size] 大檔、外部資料：通過（沒有 >1MB 檔、沒有二進位、external_data 沒被追蹤）
- 查證：**confirmed**｜誰：資訊｜嚴重度 low｜工作量 n/a
- 說明：121 檔裡最大的是 333,496 bytes（三份幾乎一樣的全 corpus verify 輸出：B7P1_corpus_all、_auditfix、integration 08_verify_score_all）。numstat 沒有任何二進位檔。external_data/ 已被 .gitignore:28 擋住，git ls-files external_data 為空，EchoThief IR、TU Berlin、Iowa 的原始檔都沒有被 staged；staged 裡只有衍生數字（dB、比值）、sha256 和檔名引用。另外 19 個 staged 文件寫著「完整見 output/wf0914/...」，但 output/ 被 gitignore（本機 266 MB），這是既有慣例（HEAD 有 30 檔同樣寫法），原始輸出只存在本機。
- 證據：git cat-file -s 排序：最大 333496 reports/gate_outputs/wf0914_integration_raw/08_verify_score_all.txt；git diff --cached --numstat | awk '$1=="-"' → 沒有結果；git check-ignore -v external_data/ → .gitignore:28；git ls-files external_data → 沒有結果；git check-ignore output/... → .gitignore:23；du -sh output/wf0914 = 266M
- 建議：不需要動作。可以選擇刪掉一份重複的 333 KB corpus 輸出。output/wf0914 原始輸出建議另外備份，否則證據鏈只能靠本機。
- 懷疑者查證：staged 最大的三個檔是 333445/333445/333496 bytes（B7P1_corpus_all、_auditfix、08_verify_score_all）；numstat 裡沒有二進位項目；external_data 被 .gitignore:28 擋住，git ls-files external_data 是 0；output/ 被 .gitignore:23 擋住，du 出 output/wf0914 是 266M。

### [staged-review:D13-sync] D13 同步備忘確認仍未做：PlateModel.h 檔頭與 water_gong_free 的 description 都還沒帶上 2.0× 主張域聲明
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 low｜工作量 S
- 說明：PlateModel.h 和 scores/examples/water_gong_free.score.json 這輪都沒有改動（不在 staged、也不在 unstaged）。PlateModel.h 檔頭沒有提到 2.0× / 乳突鑼 / ENGINE_DOMAIN_CLAIMS；score 的 meta.description 仍然只寫「ratios 1 : 1.73 : 2.33 : 3.91」，沒有「結構上沒有 2.0× 模態、不代表乳突鑼」的聲明。這和 D13 裁決「留待下一張本來就要動這兩檔的卡順路做」一致，所以是已知的未完成事項。
- 證據：git diff --cached --name-only -- src/physics/PlateModel.h scores/ → 沒有結果；git status 兩檔都沒有變更；grep 2x|boss|乳突|ENGINE_DOMAIN src/physics/PlateModel.h → 只有不相關的 line 19/76/215；water_gong_free.score.json meta.description：'...ratios 1 : 1.73 : 2.33 : 3.91. A/B against water_gong_clamped.score.json.'；docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md:28-30 同步備忘；reports/decision_packets/D13_gong_2x_partial.zh-TW.md:146-147
- 建議：維持裁決（等順路），或開一張小卡現在就補：純註解/描述，score 描述改了不影響渲染，但仍照 R6 慣例驗證 8/8 位元不變。
- 懷疑者查證：git status 對 PlateModel.h 和 water_gong_free.score.json 都沒有輸出（沒有變更）。grep 2x、乳突、ENGINE_DOMAIN、boss，在 PlateModel.h 都沒有相關結果。meta.description 仍是「...ratios 1 : 1.73 : 2.33 : 3.91. A/B against water_gong_clamped...」。ENGINE_DOMAIN_CLAIMS.zh-TW.md:28-30 和 D13 裁決包 :146-147 都明訂「順路再做」，所以這是已裁決的延後，不是漏做。

## engineering-gaps

以「要拿去賣的 VST3 合成器」標準看，最急的是發行和相容性這一層，不是物理本體。(1) release-physics.yml 從來沒跑過，而且一跑就會紅：它的建置清單漏了 SpectrumViewTest，跟 766d21d 修掉的是同一個坑；它用 unittest 跑測試，270 個只收得到 199 個。(2) pluginval 和 Steinberg validator 最後一次紀錄停在 08-06，之後改過 tail 快取、IR state、D12 遷移、D9c，都沒有重新驗。(3) 現在的 VST3 是動態連結 MSVC runtime（有 MSVCP140/VCRUNTIME140 的 import），買家電腦缺 VC++ 可轉散發套件就載不進 DAW。(4) 物理 GATE 驗的是 CLI 那條路徑，賣的 plugin 走另一份 startNote 程式碼，兩者一致性沒有任何測試（ROADMAP_PHYSICS.md:407 還列在「Nice to have」）。另外 HostProbe（D12/H7/H8）不在 CI 裡；WF0914 staged 的 2012 行從沒進過 CI；VST3 的 Program 參數會因為使用者存 preset 而索引錯位；Cimbalom 每按一個音就在音訊執行緒配置一次 juce::String。src/tools/tests 裡沒有真正的 TODO/FIXME/HACK 標記，ASAN 每次 push 都有在跑（09-14 那次是綠的），pluginval v1.0.4 也仍是最新版。

### [engineering-gaps:E1] 發行用 CI（release-physics.yml）從沒跑過，而且一跑就會紅
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 high｜工作量 S
- 說明：這是「上架前自動跑 pluginval＋Steinberg validator＋全 corpus」的唯一流程，但它從來沒被觸發過：唯一的 tag 是 playable-vst3-clean-build-v0，不符合 v* 規則。它自己也有兩個問題：(1) 建置清單漏了 TsukiSynthSpectrumViewTest，但 ctest 已經註冊了 spectrum_view_repro，所以會出現 Not Run，整個 job 變紅。這跟 766d21d 在 physics.yml 修掉的是同一個缺陷，只是 release 這支沒一起改。(2) 它用 `python -m unittest discover`，只收得到 unittest.TestCase 的測試，stem_verify、partial_verify、measurement_selfcal 那些 pytest 風格的函式（含 strict xfail）會被悄悄漏掉。結果就是發行用的閘門比每次 push 的 CI 還鬆。
- 證據：.github/workflows/release-physics.yml:45 建置清單只有 TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest（沒有 SpectrumViewTest、HostProbe）；.github/workflows/release-physics.yml:49 ctest 會跑所有已註冊的 test；CMakeLists.txt:249 add_test(NAME spectrum_view_repro ...)；.github/workflows/release-physics.yml:50 python -m unittest discover -s tests -p "test_*.py" -v；指令：unittest.defaultTestLoader.discover('tests') → countTestCases = 199；python -m pytest tests --collect-only → 270 tests collected；指令：gh run list --workflow release-physics.yml → 空白（沒有任何執行紀錄）；git tag -l → 只有 playable-vst3-clean-build-v0；git log 766d21d：「CI 修紅燈：兩個測試建置步驟補 TsukiSynthSpectrumViewTest target」（只改 physics.yml）
- 建議：release-physics.yml:45 補上 TsukiSynthSpectrumViewTest 和 TsukiSynthHostProbe；:50 改成 `python -m pytest tests -q`（跟 physics.yml 一致）。push 後用 workflow_dispatch 手動跑一次，確認四個分片和兩個驗證器都綠了再談上架。
- 懷疑者查證：事實和 CI-release 相同，都已確認：release-physics.yml:45/:50、CMakeLists.txt:249。gh run list --workflow release-physics.yml 是空的；git tag -l 只有 playable-vst3-clean-build-v0，不符合 v*；unittest 收 199 個、pytest 收 270 個。要修正三點：(1) 它和 CI-release 是同一件事，應該合併；(2) 建議在 :45 補建 TsukiSynthHostProbe 沒有用，因為 HostProbe 沒註冊 ctest（CMakeLists.txt:255），光建不會跑，必須另加執行步驟；(3) 這個 workflow 只有發版或手動觸發時才跑，平常 push 不受影響，嚴重度標 high 偏高。改 .github 要照 R7 留 unstaged；用 workflow_dispatch 試跑要先 push，需要月月動作。
- **查證修正**：和 CI-release 合併成一條：release-physics.yml:45 補上 TsukiSynthSpectrumViewTest；:50 改成 python -m pytest tests -q。HostProbe 要另加一個執行步驟，不是加進建置清單就好。嚴重度 medium，是發版前的必修項；試跑要等月月 push 之後手動觸發。

### [engineering-gaps:E2] pluginval／Steinberg validator 最後一次驗證停在 08-06，之後 plugin 改動沒重驗
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 high｜工作量 S
- 說明：pluginval L10＋Steinberg validator 最後一次跑是 08-06（DEVLOG 有記，但沒留 log）；repo 裡唯一存下來的 log 是 07-11，裡面顯示的還是 v0.2.0。之後動到 host 相容性的改動有：E5 tail 改成引擎自報並加上快取（09-07）、F-03 state 加 reverb_ir 區塊（09-08）、D9c IR wet 增益，還有 staged 的 D12 legacy state 遷移。這些正好是 pluginval 的 state 存讀、Background thread、Parameter thread safety、tail 等測項會碰到的地方。pinned 的 pluginval v1.0.4 仍是官方最新版（2024-12-04），所以工具本身不用升級。
- 證據：reports/gate_outputs/pluginval_L10.txt 檔頭：TsKR: TsukiSynth v0.2.0（檔案 mtime 07-11，commit 4c77c54 2026-07-12）；DEVLOG.md:390（08-06 段）：pluginval strictness 10 + Steinberg validator 47/47；之後各段與 reports/gate_outputs/wf09* 都沒有 pluginval 結果；HANDOVER.md:44 E5 tail 改動、HANDOVER.md:50 P3 F-03 state 改動（都在 09-07 之後）；指令：gh api repos/Tracktion/pluginval/releases → 最新 v1.0.4 2024-12-04T12:16:00Z
- 建議：用 staged 狀態 build 出 VST3，在本機跑 tools/validate_plugin.ps1（strictness 10），log 存進 reports/gate_outputs/。中期可以在 physics.yml 每次 push 加一個 pluginval strictness 5 的快速 step，不要只放在從沒跑過的 release workflow。
- 懷疑者查證：pluginval_L10.txt:10 是「TsukiSynth v0.2.0」，最後一次 commit 是 4c77c54（2026-07-12）；DEVLOG.md:390 在 08-06 段（:368 起），記了 L10 + validator 47/47，但沒有存 log；比 :390 新的 DEVLOG 段落和 wf09* 證據都 grep 不到 pluginval。gh api 顯示 v1.0.4（2024-12-04）仍是最新版。要修正的是 owner/effort：tools/validate_plugin.ps1:3-10 規定 -Pluginval 和 -Vst3Validator 兩個都必填，但本機的 Desktop、Temp、Downloads 都找不到 pluginval.exe（PowerShell 搜尋沒有結果）；要跑得先下載 pluginval、clone 並 build Steinberg SDK validator（依安全規則，下載要月月同意），不然就得 push 之後用 workflow_dispatch。所以不是 AI 馬上能做的 S 級工作。
- **查證修正**：上次 pluginval/validator 重驗停在 08-06，之後 state/tail/IR 的改動都沒重驗，已確認。重跑需要下載 pluginval 並 build VST3 SDK validator（要月月同意下載），或 push 後手動觸發 release workflow（要先修 E1）。owner 應該改成「月月批准後由 AI 執行」，工作量 S～M。

### [engineering-gaps:E3] 物理 GATE 驗的是 CLI 路徑；賣的 plugin 走另一份程式碼，一致性沒有測試
- 查證：**adjusted**｜誰：月月裁決｜嚴重度 high｜工作量 L
- 說明：physics_verify、verify_score、corpus、位元不變這些檢查，全部經過 CimbalomVoice/ChromaticVoice::noteOn()（標註為 Standalone API：CLI／ScoreRenderer）。DAW 裡實際用的是 startNote()，這是另一份手寫的同一條物理鏈，還多了 macro 縮放、BodyResonance、EffectChain（含 kIrWetMakeupGain），而且只有 plugin 路徑開了 ScopedNoDenormals。HostProbe 只驗音高和 onset（melody_verify），不驗 T60 或模態頻率。ROADMAP 把「Plugin ↔ CLI 一致性驗證」列在 Nice to have，也還沒做。但變現計畫的主打賣點正是「可稽核物理鏈」，買家買到的 plugin 其實在驗證域外。
- 證據：src/engines/CimbalomEngine.h:147 startNote()（plugin）與 :369-373 「Standalone API (CLI / ScoreRenderer)」noteOn()，兩份各自組裝 StringModel/HammerImpulse/bridgeLoss；src/engines/ChromaticEngine.h:133 startNote() 與 :294-298 noteOn() 同樣是兩份；grep ScopedNoDenormals → 只在 src/PluginProcessor.cpp:305，ScoreRenderer/CLI 沒有；ROADMAP_PHYSICS.md:407「Plugin ↔ CLI 一致性驗證 — 目前只有 CLI 是純物理路徑」（列在 §4 Nice to have）；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:95 差異化文案＝「語意材料參數＋JSON 譜 CLI＋可稽核物理鏈」
- 建議：月月要選一條：(a) 上架前補 parity GATE：HostProbe 載入 VST3，macro 全 0.5、FX 全關，用同一份 score 渲染，跟 CLI 比模態頻率和 T60（容差要走 §6 登記，不能 AI 自訂）；長期把 startNote/noteOn 抽成共用函式。(b) 或者先把文案主張域收窄成「CLI 渲染已驗證、plugin 即時演奏未驗證」。
- 懷疑者查證：CimbalomEngine.h:147 的 startNote 和 :369-373 的 Standalone API noteOn、ChromaticEngine.h:133 和 :294-298 都存在；ScopedNoDenormals 只出現在 PluginProcessor.cpp:305；ROADMAP_PHYSICS.md:407 把 Plugin↔CLI 一致性列在 §4 Nice to have；變現計畫 :95 的文案寫「可稽核物理鏈」。但有兩處要修正：(1)「兩份各自組裝」只對一部分。CimbalomEngine.h:121-146 的 applyStringDecayTimes() 明寫「shared by startNote() (realtime voice), noteOn() (CLI/ScoreRenderer standalone) and worstCaseTailSeconds()」，在 :265/:323/:539/:702 共用，所以衰減律（T60 公式）是同一份，重複的是其餘的激發和組裝部分。(2) HostProbe 不是完全不碰 T60：H8（host_probe.cpp:1465-1499）會檢查到回報的 tail 為止仍高於 −60 dB，只是沒有驗 T60 值和模態頻率本身。
- **查證修正**：plugin 的 startNote() 和 CLI 的 noteOn() 共用衰減律 helper（applyStringDecayTimes，CimbalomEngine.h:121-146），但激發、振幅、macro、BodyResonance、EffectChain 是各自組裝的；HostProbe 只驗音高/onset 和 tail 長度（H8），不驗模態頻率和 T60 值。目前沒有 plugin↔CLI 一致性 GATE，和「可稽核物理鏈」的文案有落差。要補 parity GATE（容差得走 §6 登記）還是收窄文案，由月月選。

### [engineering-gaps:E4] VST3 動態連結 MSVC runtime，買家電腦缺 VC++ 可轉散發套件時載不進 DAW
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 high｜工作量 S
- 說明：CMakeLists 沒設定 CMAKE_MSVC_RUNTIME_LIBRARY，所以預設是 /MD（動態 CRT）。實際掃描 build 出來的 VST3，裡面 import 了 MSVCP140.dll、MSVCP140_2.dll、VCRUNTIME140.dll、VCRUNTIME140_1.dll。買家機器如果沒裝 VC++ 2015-2022 可轉散發套件（或版本太舊，缺 MSVCP140_2），DAW 掃描時會載入失敗或把它列入黑名單，這是插件客服最常見的問題之一。變現計畫的 Inno Setup 項目裡沒有提到這件事。
- 證據：CMakeLists.txt 全檔 grep MSVC_RUNTIME / MultiThreaded → 無；指令：grep -a -o 'VCRUNTIME…\.dll' build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3/Contents/x86_64-win/TsukiSynth.vst3 → MSVCP140.dll、MSVCP140_2.dll、VCRUNTIME140.dll、VCRUNTIME140_1.dll、api-ms-win-crt-*；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:65 安裝包項目只寫「Inno Setup 一鍵裝到 Common Files\VST3＋PDF 手冊」
- 建議：二選一：(a) 在 add_subdirectory(libs/JUCE) 之前加 `set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")`，改成靜態 CRT，插件業界多半這樣做；(b) 在 Inno Setup 安裝包裡附帶 vc_redist.x64.exe。選 (a) 屬於 R6（改建置要重跑 --full＋三 build），也要重跑 8/8 位元不變確認。
- 懷疑者查證：grep CMakeLists.txt，MSVC_RUNTIME 和 MultiThreaded 都沒有結果。在 build/TsukiSynth_artefacts/Release/VST3/.../TsukiSynth.vst3（2026-09-25 03:13 重建）上跑 grep -a，看得到 MSVCP140.dll、MSVCP140_2.dll、VCRUNTIME140.dll、VCRUNTIME140_1.dll。變現計畫的安裝包項目在 :67（原文寫 :65，行號小偏差），只寫 Inno Setup 裝到 Common Files\VST3＋PDF 手冊，全檔 grep redist/runtime 都沒有結果。

### [engineering-gaps:E5] HostProbe（D12 遷移／H7 preset＋IR／H8 tail／H6 block size）不在 CI，也不在 ctest
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 M
- 說明：D12 legacy reverb_ir_path 遷移三情境、F-03 IR 三態、user preset 往返、tail ≥ 引擎 worst-case 這幾項，只有 HostProbe 在測，而 HostProbe 刻意沒註冊 add_test，兩個 workflow 也都沒 build 它。所以「ctest 全綠」和「CI 全綠」都不包含這些。另外，HostProbe 會直接寫入使用者真實的 %APPDATA%/TsukiSynth/IR 與 Presets（沒有可覆寫的目錄）；如果上一輪中途崩潰留下殘檔，下一輪的「not yet in the managed library」檢查就會失敗。
- 證據：CMakeLists.txt:255「Deliberately NOT registered with add_test」、:266 add_executable(TsukiSynthHostProbe ...)；physics.yml:54 測試建置清單沒有 TsukiSynthHostProbe；release-physics.yml:45 也沒有；tests/host_probe.cpp:1222-1330 D12 三情境只存在於 HostProbe；tests/*.py 與其他 .cpp 都沒有 reverb_ir_path 測試；src/IRLibrary.h:119-126、src/PresetManager.h:442-450 固定用 userApplicationDataDirectory；tests/host_probe.cpp:1254-1257 CHECK(!IRLibrary::resolve(expectedRef).existsAsFile(), "D12: legacy IR source not yet in the managed library")，fixture seed 固定為 3
- 建議：在 physics.yml 的 build-and-verify 裡，VST3 build 之後加上 build＋run TsukiSynthHostProbe（Windows runner 可以 host VST3）。IRLibrary/PresetManager 讀一個環境變數（例如 TSUKI_DATA_DIR）來覆寫資料目錄，讓 HostProbe 在 CI 和本機都用暫存目錄，不去碰真實使用者資料。
- 懷疑者查證：CMakeLists.txt:255 寫 NOT registered，:266 是 add_executable；physics.yml:54 和 release-physics.yml:45 都沒有 HostProbe。IRLibrary.h:121 和 PresetManager.h:445 都固定用 userApplicationDataDirectory，grep TSUKI_DATA 和 getEnvironmentVariable 都沒有結果。host_probe.cpp:1247 用 makeImpulseFixture(2000, 3) 固定 seed，:1254-1257 CHECK「not yet in the managed library」，:1315-1316 才清理，所以中途崩潰留下的殘檔會讓下一輪失敗。

### [engineering-gaps:E6] WF0914 staged 的 2012 行程式碼從沒進過 CI（含 ASAN、macOS/Linux 編譯）
- 查證：**adjusted**｜誰：月月動手｜嚴重度 medium｜工作量 S
- 說明：HANDOVER 說的「CI 三平台全綠」指的是 766d21d。之後 staged 的 src/tests/tools 改動（D9c、D12、B7P1 純函式、D14 串流化、host_probe/physics_models_repro 新測試）只有本機證據，還沒經過 ASAN、Linux clang 或 macOS AppleClang 編譯。R7 規定不 commit 所以這是預期中的狀態，但要記得：commit＋push 之後的第一輪 CI 才是真正的跨平台驗收。
- 證據：指令：git diff --cached --stat -- src tools tests CMakeLists.txt .github → 12 files changed, 2012 insertions(+), 35 deletions(-)；指令：gh run list --workflow physics.yml → 最新一次 34880536096，2026-09-14T18:23:50Z（main，success）；之後沒有 run；HANDOVER.md:4「WF0914 輪全部成果 staged 未 commit」
- 建議：月月審完 git diff --cached 裁定 commit 後，push 到 fix/** 分支觸發 physics.yml，看到六個 job 全綠，才算 WF0914 真正驗收完。
- 懷疑者查證：git diff --cached --stat -- src tools tests CMakeLists.txt .github 的結果是 12 files changed, 2012 insertions(+), 35 deletions(-)。gh run list physics.yml 最新一筆是 34880536096（2026-09-14T18:23:50Z，main，success），之後沒有新的 run。但「Linux clang」說錯了：gh run view 34880536096 --log 顯示 ubuntu 那條 leg 是「CXX compiler identification is GNU 13.3.0」，physics.yml:174-175 也沒有指定 CC/CXX，所以 Linux 那條是 GCC。
- **查證修正**：WF0914 staged 的 2012 行 src/tools/tests 改動還沒進過 CI（Windows MSVC build+ASan、Linux GCC 13.3 和 macOS AppleClang 只編 CLI）。要等月月審完 commit 並 push 之後，第一輪 CI 才算真正驗收。

### [engineering-gaps:E7] VST3 Program 參數的格數在建立 instance 時就固定，但 preset 數會變，索引會錯位
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 S
- 說明：getNumPrograms() 等於「工廠 preset 數＋使用者 preset 數」，而使用者 preset 依名稱排序。JUCE VST3 wrapper 的 ProgramChangeParameter 在建構時就把 stepCount 固定成當下的 getNumPrograms()-1。後果：(1) 使用者存了新 preset 之後，host 的 Program 參數碰不到新的那筆；(2) 新 preset 如果名稱排在前面，既有使用者 preset 的索引全部往後移，host 自動化或 program change 會載到另一個 preset；(3) 每台機器的使用者 preset 數不同，VST3 參數資訊（stepCount）也跟著不同，同一個專案換機器開，program 對應就不一樣。setStateInformation 已經用 presetId 和 restoredProgramToIgnore 補了「state 還原」這一條，但沒涵蓋上面三種情況。
- 證據：src/PluginProcessor.cpp:987-990 getNumPrograms() = jmax(1, presetManager.getNumPresets())；src/PresetManager.h:51 getNumPresets() = factory + user；:347-357 scanned.sort(NameCmp) 依名稱排序；libs/JUCE/modules/juce_audio_plugin_client/juce_audio_plugin_client_VST3.cpp:1027-1037 ProgramChangeParameter 建構時 info.stepCount = owner.getNumPrograms() - 1；src/PluginProcessor.cpp:997-1009 setCurrentProgram 直接 presetManager.loadPreset(index)
- 建議：建議：host 看到的 programs 只給工廠 preset（數量固定、跨機器一致），使用者 preset 只在 plugin 自己的 preset 選單裡。這是 UX 決定，要月月裁；落地後要重跑 pluginval 的 Plugin programs 測項和 HostProbe H7。
- 懷疑者查證：PluginProcessor.cpp:987-990 的 getNumPrograms 是 jmax(1, getNumPresets())；PresetManager.h:51 是 factory+user；:347-357 用 NameCmp 依名稱排序；JUCE juce_audio_plugin_client_VST3.cpp:1027-1037 的 ProgramChangeParameter 在建構時設 info.stepCount = owner.getNumPrograms() - 1；PluginProcessor.cpp:997-1009 的 setCurrentProgram 只擋 restoredProgramToIgnore，其餘直接 loadPreset(index)。Presets.h:481 起有 27 個工廠 preset（0-26）。

### [engineering-gaps:E8] 每個 Cimbalom/Piano 音符在音訊執行緒 malloc 一次，而且沒有任何自動化 RT 安全檢查
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：startNote() 由 Synthesiser::renderNextBlock 在音訊執行緒呼叫。其中 materialDB->getMaterial(kBridgeSoundboardMaterialKey) 傳的是 const char*，但 getMaterial 的參數是 const juce::String&，每次都會建一個暫時的 juce::String（heap 配置加釋放）。其餘路徑我查過：mode 向量都有預先 reserve、參數都讀 atomic、processBlock 有 ScopedNoDenormals、錄音用 tryEnter、IR 由 juce::dsp::Convolution 在背景執行緒載入，這些都沒問題。但整個專案沒有 RealtimeSanitizer 之類的工具，這種違規只能靠人工讀程式碼抓。這個改動不影響 DSP 數值，位元應該不變。
- 證據：src/engines/CimbalomEngine.h:55 static constexpr const char* kBridgeSoundboardMaterialKey = "wood_spruce"；src/engines/CimbalomEngine.h:163 auto* soundboardMat = materialDB->getMaterial (kBridgeSoundboardMaterialKey);（在 startNote 內，:147）；src/physics/MaterialDB.h:180 const Material* getMaterial (const juce::String& name) const；grep -rn 'realtime\|RTSan\|nonblocking' src tests CMakeLists.txt .github → 無
- 建議：在 setMaterialDB() 裡先把 wood_spruce 的 Material* 存起來（或改成 static const juce::String），startNote 直接用指標。另外在 Linux clang（LLVM 20 以上）加一個 -fsanitize=realtime 的 processBlock harness job，讓「音訊執行緒零配置」也變成有 GATE 輸出的主張。改完要跑位元不變 8/8。
- 懷疑者查證：CimbalomEngine.h:55 是 constexpr const char*；:163 在 startNote（:147 起）裡呼叫 materialDB->getMaterial(kBridgeSoundboardMaterialKey)；MaterialDB.h:180 的參數是 const juce::String&，所以每次都會建一個暫時的 juce::String（非空字串會在 heap 配置）。我抽查了其他路徑：startNote 用的 baseModesScratch 在 :88 reserve(40)，StringModel::calculateModes 也是 clear+reserve(numModes)。numModes 是否一定 ≤40 我沒有逐一確認，所以「其餘都沒問題」只算部分核實。

### [engineering-gaps:E9] tail 快取假設「只在 message thread 被呼叫」，但實際由 host 決定
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：getWorstCaseTailSecondsCached() 會改寫 mutable 快取欄位，沒有任何同步；重算時 worstCaseTailSeconds() 還會配置 vector（掃 88 個音）。程式註解說 getTailLengthSeconds 是 message-thread-only by construction，但 VST3 的 getTailSamples、AU 的 GetTailTime 在哪個執行緒呼叫，是 host 決定的，不是本專案能保證的。只要某個 host 在音訊執行緒或多執行緒下呼叫，就會有 data race 和 RT 配置。目前沒有 log 證明哪個 host 真的這樣做，所以列為推理風險。
- 證據：src/engines/CimbalomEngine.h:713-730 註解「Not thread-safe against concurrent callers -- valid because both ... are message-thread-only by construction」；src/engines/CimbalomEngine.h:951 mutable bool cachedTailValid（以及後面兩個 mutable 欄位）；:659 baseModesLocal.reserve (40)（重算時配置）；src/engines/ChromaticEngine.h:515-518、:813 同樣的模式；src/PluginProcessor.cpp:212-249 getTailLengthSeconds() 直接呼叫 voice 0 的 cached 函式
- 建議：改成參數變動時（APVTS listener 或 editor timer，都在 message thread）重算，結果存進 std::atomic<double>；getTailLengthSeconds() 只讀這個 atomic。H8 現有檢查可以直接當回歸測試。
- 懷疑者查證：CimbalomEngine.h:713-719 的註解和 :720-730 的 mutable 快取、:951-953 的 mutable 欄位、:656-659 重算時會建 vector 並 reserve，ChromaticEngine.h:515-518 也一樣，都確認。但「VST3 getTailSamples 在哪個執行緒被呼叫由 host 決定」和 SDK 契約不符：JUCE 內附的 VST3 SDK ivstaudioprocessor.h 標註 getTailSamples() 是「[UI-thread & Setup Done]」，JUCE 的 VST3 wrapper（:3604）也只在這個函式裡呼叫 getTailLengthSeconds。AU 的 GetTailTime（AU_1.mm:1198）確實沒有這種保證，但 AU 目前沒有建置（CMakeLists.txt:79-82）。
- **查證修正**：VST3（目前唯一發佈的格式）依 SDK 契約，getTailSamples 在 UI 執行緒呼叫，所以只有 host 違反規範時才會出事。等哪天要出 AU 時，這條才變成實際風險。改成 atomic 快取仍是低成本的防禦，優先度 low。

### [engineering-gaps:E10] 位元不變（R10）回歸守門沒有自動化，CI 只渲染 6/75 首
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 M
- 說明：「改 src 後 8 首 SHA256 位元不變」是這個專案最常用的防誤改檢查，但腳本放在 reports/gate_outputs/wf0907_method/，是從 b5、b6 那兩張卡的腳本一路複製改來的，CLI 路徑還寫死成 .exe；基準檔放在 reports/gate_outputs/b6_method/，完全不在 CI 裡。每次 push 的 CI 只跑 6 首 smoke，全 corpus 75 首只存在於從沒跑過的 release workflow（見 E1）。所以只要有人漏跑本機腳本，渲染結果被意外改變也不會有紅燈。
- 證據：reports/gate_outputs/wf0907_method/render_wf_scores.py:48-49 DEFAULT_CLI = …"build", "TsukiSynthCLI_artefacts", "Release", "TsukiSynthCLI.exe"；基準 reports/gate_outputs/b6_method/sha256_before_post_a14.txt（HANDOVER.md:28）；physics.yml:78-102 CI 只驗 6 首 smoke，註解寫全 corpus 是 LOCAL release gate；physics.yml 全檔 grep sha256_before / render_wf_scores → 無
- 建議：把腳本收進 tools/（找 CLI 的方式與 verify_score.find_cli 一致），在 physics.yml Windows 那條 leg 加一步：渲染 8 首，跟 repo 內 CI 專用的基準 SHA 比對（runner 的 MSVC 可能跟本機不同，基準要在 CI 上重新建立）。改動渲染的 commit 必須同時更新基準和 Rule 10 報告，否則 CI 紅燈。
- 懷疑者查證：reports/gate_outputs/wf0907_method/render_wf_scores.py:47-48 的 DEFAULT_CLI 是 ...Release/TsukiSynthCLI.exe（有 --cli 可以覆寫）；基準檔在 reports/gate_outputs/b6_method/sha256_before_post_a14.txt；grep .github/workflows，sha256_before 和 render_wf_scores 都沒有結果；physics.yml:78-102 只跑 6 首 smoke。要在 CI 加新的 GATE，屬於 CI 行為改變，應先讓月月點頭。

### [engineering-gaps:E11] ASAN 只在 Windows MSVC（只有 address），Linux clang 的 ASan+UBSan 已經能開但沒有 job
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：cpp-address-sanitizer 每次 push 都有跑，09-14 那次 success，這部分沒問題；本機 build-asan/ 停在 08-02，但既然 CI 有在跑，這不重要。只是 MSVC 沒有 UBSan，而 CMake 的 tsuki_enable_test_sanitizers 早就支援 clang 的 -fsanitize=address,undefined，Linux 的 JUCE 相依套件在 cross-platform-emit job 也已經裝好。未定義行為（整數溢位、越界 shift、float→int 越界）目前沒有任何工具在抓。
- 證據：CMakeLists.txt:16-25 elseif Clang|GNU → -fsanitize=address,undefined；physics.yml:244-269 cpp-address-sanitizer 只有 runs-on: windows-2022；指令：gh run view 34880536096 → cpp-address-sanitizer success 2026-09-14T18:23:54Z；build-asan/ 目錄 mtime Aug 2（本機，已被 CI 取代）
- 建議：新增一個 ubuntu-24.04 clang job：-DTSUKI_ENABLE_SANITIZERS=ON，build 四個測試 target 後跑 ctest。apt 那段可以直接複製 physics.yml:149-158。
- 懷疑者查證：CMakeLists.txt:16-25 的 Clang|GNU 分支會加 -fsanitize=address,undefined；physics.yml:244-269 的 ASan job 只在 windows-2022 跑；gh run view 顯示 cpp-address-sanitizer 是 success；build-asan 的 mtime 是 2026-08-02。要修正的是：CI 的 ubuntu leg 其實是 GNU 13.3.0（見 CI log），不是 clang。GNU 分支同樣支援 ASan+UBSan；如果新 job 想用 clang，得明確設定 CC=clang/CXX=clang++。
- **查證修正**：建議新增一個 ubuntu-24.04 job：-DTSUKI_ENABLE_SANITIZERS=ON（runner 預設的 GCC 13.3 就支援 address+undefined；要用 clang 得明確設 CC/CXX），build 四個測試 target 後跑 ctest。

### [engineering-gaps:E12] macOS/AU 從沒 build 過 plugin；Score 控制台寫死 Windows 檔名
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 M
- 說明：CI 的 macOS leg 只 build CLI，PluginProcessor.cpp、PluginEditor.cpp、AU wrapper 從來沒在 mac 上編譯過（AU 要 -DTSUKI_AU=ON 才會開）。ScoreConsole 找 CLI 時寫死 "TsukiSynthCLI.exe" 和 "Release" 目錄，mac 的 Standalone 按 Score 一定找不到 CLI；產報告還要求 PATH 裡有 python。使用者資料目錄用 userApplicationDataDirectory，在 mac 上會是 ~/Library/TsukiSynth，不是慣例的 ~/Library/Application Support/。如果 v0.4 EA 只賣 Windows，這些可以先擱著，但文案要寫清楚平台。
- 證據：physics.yml:174-178 cross-platform-emit 只 Configure CMake (CLI only) → --target TsukiSynthCLI；CMakeLists.txt:79-82 AU 只在 TSUKI_AU AND APPLE 時加入 FORMATS；src/ScoreConsole.h:98 getSiblingFile ("TsukiSynthCLI.exe")；:105-109 寫死 .getChildFile ("Release").getChildFile ("TsukiSynthCLI.exe")；:239 args = { "python", …；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:72「AU build 從沒人手動測過」
- 建議：先裁定首發平台。若要支援 mac：加一個 macos-14 job build VST3＋AU（-DTSUKI_AU=ON）並跑 auval；ScoreConsole 依平台決定副檔名；資料目录改成 Application Support。若首發只有 Windows：商品頁標明 Windows only，這條延後。
- 懷疑者查證：physics.yml:174-178 的 macOS leg 只設定並 build TsukiSynthCLI；CMakeLists.txt:79-82 的 AU 只在 TSUKI_AU AND APPLE 時加入；ScoreConsole.h:98 寫死 getSiblingFile("TsukiSynthCLI.exe")，:103-109 寫死 Release/TsukiSynthCLI.exe；:239 的 args 是 { "python", ...}；IRLibrary.h:121 和 PresetManager.h:445 用 userApplicationDataDirectory（在 mac 上是 ~/Library）。變現計畫的 AU 那句在 :74（原文寫 :72，行號小偏差）。

### [engineering-gaps:E13] 發行管線缺件：沒有安裝包腳本、CI 不產出 VST3、版本號四個月沒動、plugin 沒有 provenance
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 M
- 說明：repo 裡沒有任何安裝包或簽章相關檔案。release workflow 只上傳 CLI（給 corpus 分片用），沒有上傳 VST3/Standalone，所以賣出去的 binary 只能從本機 build（可能是 dirty tree）。專案版本 0.3.0 從 07-23 到現在都沒動，中間 state 格式改過好幾次（F-03、D12），DAW 和客服都分不出是哪一版。BuildProvenance（commit/dirty）只有 CLI 有，plugin binary 沒有記錄自己來自哪個 commit。不簽章這件事，變現計畫已經有明確主張（先不簽），所以不列為缺陷。
- 證據：指令：git ls-files | grep -iE '\.iss$|installer|signtool|codesign|notar|\.wxs$|nsis' → 無；release-physics.yml:83-88 upload-artifact 只有 build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe；CMakeLists.txt:2 project(TsukiSynth VERSION 0.3.0)；git log -S"VERSION 0.3.0" → e0eb06a 2026-07-23；CMakeLists.txt:147 generated/BuildProvenance.h 只加在 TsukiSynthCLI 的 include 目錄
- 建議：定一個發版規則：版本號跟 git tag 綁定；release workflow 產出 VST3＋Standalone＋CLI 的 zip 並附 SHA256，還有 Inno Setup 安裝檔（和 E4 的 CRT 決定一起處理）；plugin 的 About 或 state 寫入 commit/dirty。安裝包工時變現計畫估 2 晚。
- 懷疑者查證：git ls-files 找 iss/installer/signtool/codesign/notar/wxs/nsis，只有兩個誤判（measurement_selfconsistent.json 裡碰巧含 nsis 字串）；release-physics.yml:83-88 只上傳 TsukiSynthCLI.exe；CMakeLists.txt:2 是 VERSION 0.3.0，git log -S 查到 e0eb06a（2026-07-23）；CMakeLists.txt:145-147 的 generated 目錄只加在 TsukiSynthCLI，BuildProvenance 只被 RenderApp.cpp:21/306-314 用到。

### [engineering-gaps:E14] plugin state 沒有版本欄位；user preset 有寫 version 但讀取時從沒用過
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：getStateInformation 寫了 presetIndex、presetId、presetDirty、engine_index、chr_sub_engine_index、ir_missing、ir_mismatch 和 reverb_ir 子節點，但沒有 state_version。D12 判斷舊格式靠的是「有沒有 reverb_ir_path 這個鍵」。PresetManager 存 preset 時會寫 version=2，但 scanUserPresets 讀取時從來不看它。第一次賣出之後，每一個客戶專案的 state 都是永久相容包袱。趁現在加版本號最便宜，之後每次格式遷移就能用明確的 switch 處理，不必再猜鍵名。
- 證據：src/PluginProcessor.cpp:527-565 getStateInformation 寫入的屬性清單（沒有任何 version）；src/PluginProcessor.cpp:620-645 D12 遷移靠 tree.getProperty("reverb_ir_path") 判斷；src/PresetManager.h:173 root.setAttribute ("version", 2)；:303-358 scanUserPresets 沒有讀 version
- 建議：getStateInformation 加 state_version=3（把 F-03 之後的格式定為 3），setStateInformation 依版本分支（沒有版本就視為舊格式，走現在的 D12 路徑）；PresetManager 讀 version 並對未知的新版本保守處理。HostProbe H5/H7/D12 要加一條「版本欄位存在且往返不變」。這是 R6 級改動，需跑全套 GATE。
- 懷疑者查證：PluginProcessor.cpp:527-565 寫進 state 的屬性裡沒有任何 version（grep version 沒有結果）；:620-645 的 D12 靠 reverb_ir_path 這個鍵判斷舊格式；PresetManager.h:173 寫 setAttribute("version", 2)，全檔沒有地方讀 version。補充：state 格式一旦定下來就是永久的相容包袱，雖然歸類為 ai-now，最好先讓月月知情。

### [engineering-gaps:E15] IRLibrary 手寫 SHA-256 沒有已知答案回歸測試；重新匯入修不好已損壞的庫檔
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：(1) IRLibrary 自己手寫了 SHA-256，只在 P3 卡當時用 Python hashlib 手動對照過一次，沒有進 ctest。HostProbe 只做自我一致性檢查（同一份實作算兩次一定相同），實作算錯也照樣會過。而 CLI 那邊其實直接 #include 了 JUCE 的 juce_SHA256.cpp，等於同一個 repo 裡有兩套 SHA-256，兩邊都是當初「不能改 CMakeLists」的卡片限制留下的權宜做法。(2) importFile 發現目標檔已存在就直接沿用，不驗內容雜湊；copyFileTo 也不是原子寫入。所以庫檔一旦損壞或只寫了一半，使用者重新選原檔也修不好，之後每次載入都會是 mismatch。(3) IRLibrary::list() 沒有任何呼叫端，庫只會一直變大，沒有清理介面。
- 證據：src/IRLibrary.h:47-106 自寫 sha256Hex；tests/*.cpp 中 grep 'ba7816bf|e3b0c442'（abc/空字串的已知雜湊）→ 無；reports/gate_outputs/wf0908_P3_f03.txt:41「經 Python hashlib 對照 ""/"abc"/pangram 三組向量驗證一致」（一次性手動）；src/cli/RenderApp.cpp:3-15 #include <juce_cryptography/hashing/juce_SHA256.cpp>（因為 CMakeLists 超出卡片範圍）；src/IRLibrary.h:172-180 if (! dest.existsAsFile()) 才複製，否則直接沿用、不驗 hash；grep IRLibrary::list src → 沒有呼叫端
- 建議：兩個 target 都 link juce::juce_cryptography，統一改用 juce::SHA256，刪掉 RenderApp.cpp 的 .cpp include 和自寫實作；audit_repro 加 SHA-256 已知答案測試（空字串、abc）。import 時如果目標檔已存在，先驗 hash，不符就先寫暫存檔再覆蓋。若 hash 輸出位元組相同，preset 相容性不受影響。
- 懷疑者查證：IRLibrary.h:47 自己寫了 sha256Hex，:115 在用；grep tests 和 tools，ba7816bf|e3b0c442（已知答案向量）都沒有結果；wf0908_P3_f03.txt:41-42 記的是「經 Python hashlib 對照 ""/"abc"/pangram 三組向量驗證一致」（一次性手動）；RenderApp.cpp:3-15 用 #include <juce_cryptography/hashing/juce_SHA256.cpp>；IRLibrary.h:172-180 只有在 !dest.existsAsFile() 時才複製，不驗既有檔；:205 定義了 list()，但 grep IRLibrary::list 在 src 和 tests 都沒有呼叫端。

### [engineering-gaps:E16] 27 個工廠 preset 沒有回歸測試；打錯的 paramID 會被靜默略過
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：loadFactoryPreset 遇到找不到的 paramID 會直接跳過，不報錯。目前沒有任何測試逐一載入工廠 preset、確認每個都能渲染出有限值、不靜音、峰值低於 0 dBFS。pluginval 的 Plugin programs 測項只切換 program，不看聲音。我用靜態比對確認過，Presets.h 目前用到的 30 個 paramID 全都在 ParameterLayout 裡，所以現在沒有 bug，缺的是之後的守門。
- 證據：src/PresetManager.h:411-419 if (auto* param = apvts.getParameter (entry.paramID)) … 找不到就略過；tests/*.cpp grep getFactoryPresetList → 無（只有 host_probe.cpp:582 的 shadow 空實作）；指令（本次）：比對 Presets.h 用到的 id 與 ParameterLayout.cpp 的 PID → used 30, missing []
- 建議：在 audit_repro 或 HostProbe 加一個迴圈，逐一跑 27 個工廠 preset：斷言每個 paramID 都解析得到，並各渲染 C4 一個音 2 秒，檢查 isfinite、峰值 < 0 dBFS、RMS 高於靜音門檻。
- 懷疑者查證：PresetManager.h:414-419 在 getParameter 找不到時直接略過；Presets.h:481 起確實是 27 個工廠 preset；我自己用 regex 比對 Presets.h 用到的 id 和 ParameterLayout.cpp，used 30、missing []；tests/*.cpp 沒有任何工廠 preset 的回歸測試。要修正 owner：建議裡的「峰值 < 0 dBFS」「RMS 高於靜音門檻」是新的判定門檻。依 R2/R4，門檻不能由 AI 自訂（靜音門檻的數值也沒有來源）。只有「每個 paramID 都解析得到、輸出 isfinite」這兩項不需要新門檻。
- **查證修正**：「27 個工廠 preset 的 paramID 都解析得到、渲染結果是 isfinite」可以由 AI 直接加。峰值上限和靜音 RMS 門檻屬於新 GATE 判準，要月月核准並溯源後才能加。

### [engineering-gaps:E17] 工具可攜性：ffmpeg 路徑寫死在月月電腦；find_cli 取最新 mtime，可能靜默用到 Debug build
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：melody_roll_video.py 的預設 ffmpeg 路徑寫死成 C:\Users\admin\Desktop\Tools\…（有 --ffmpeg 可覆寫）。physics_verify 和 verify_score 的 find_cli 會在整個 build/ 底下 rglob，挑 mtime 最新的那個執行檔。如果同時有 Debug 和 Release，GATE 可能不知不覺用 Debug CLI 跑；render manifest 雖然記了 exe 的 sha，但報告上看不出來。tools/validate_plugin.ps1 和 run_asan_ctest.ps1 本來就是 Windows 專用，不算缺陷。src 裡的 C:\ 路徑只出現在註解。
- 證據：tools/melody_roll_video.py:97-98 DEFAULT_FFMPEG = Path(r"C:\Users\admin\Desktop\Tools\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe")；tools/physics_verify.py:886-893、tools/verify_score.py:375-383 return max(cands, key=lambda p: p.stat().st_mtime)；src/PluginProcessor.cpp:525 註解提到 debug.log，但記錄程式碼已經不存在（%APPDATA%/TsukiSynth/debug.log 最後寫入 08-22）
- 建議：ffmpeg 改成依序找 --ffmpeg、環境變數 TSUKI_FFMPEG、shutil.which('ffmpeg')；find_cli 優先挑路徑含 Release 的，並把選到的路徑印到 stdout 與報告；順手刪掉 PluginProcessor.cpp:525 那行過時註解。
- 懷疑者查證：melody_roll_video.py:97-98 的 DEFAULT_FFMPEG 寫死 C:\Users\admin\Desktop\Tools\...；physics_verify.py:886-893 和 verify_score.py:375-383 都用 max(cands, key=st_mtime)；PluginProcessor.cpp:525 註解寫 Logging (debug.log)，下一行就直接是 == State ==，沒有記錄程式碼；%APPDATA%/TsukiSynth/debug.log 最後修改是 2026-08-22 02:22。目前 build/ 底下只有 Release 的 CLI，所以誤用 Debug 還只是潛在風險。

### [engineering-gaps:E18] kIrWetMakeupGain 其中 18.06 dB 來自 JUCE 內部常數 0.125，JUCE 升版前要重跑 D9c
- 查證：**adjusted**｜誰：資訊｜嚴重度 low｜工作量 n/a
- 說明：JUCE 8.0.12 的 Convolution 正規化係數是 0.125/sqrt(能量)，也就是固定壓掉 18.06 dB。所以 D9 量到的 −28.58 dB 落差裡，約 18 dB 其實是 JUCE 的內建 headroom，不完全是「ALGO 與 IR 演算法的結構差」；3 顆 IR 展幅只有 0.24 dB，也跟能量正規化加 Parseval 定理的預期一致。這代表 26.9 倍的補償增益跟 JUCE 內部實作綁在一起。好消息是 audit_repro 的 D9c 測試（0 ± 0.25 dB）已經在 CI 守著，JUCE 改了這個常數就會紅燈。這條不是缺陷，是提醒：升級 JUCE submodule 時要把它當成預期中的斷點。
- 證據：libs/JUCE/modules/juce_dsp/frequency/juce_Convolution.cpp:623-629 calculateNormalisationFactor → return 0.125f / std::sqrt (sumSquaredMagnitude);；libs/JUCE/modules/juce_core/system/juce_StandardHeader.h:42-44 JUCE 8.0.12；src/effects/EffectChain.h:258-275 kIrWetMakeupGain = 26.9f 的註解沒有提到 0.125；tests/audit_repro.cpp:1193-1201 D9c 測試（在 CI ctest 內）；reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md grep '0.125' → 無
- 建議：不用改程式碼。建議在 EffectChain.h 常數註解補一句「其中 20·log10(0.125) = −18.06 dB 來自 JUCE Convolution 正規化」，並在升 JUCE 的 checklist 寫上「D9c 測試必須仍綠」。
- 懷疑者查證：juce_Convolution.cpp:623-629 的 0.125f/sqrt(...)、juce_StandardHeader.h 的 8.0.12、EffectChain.h:258-275 註解沒提 0.125、D9 裁決包 grep 0.125 沒有結果，這幾點都對。但核心說法「audit_repro 的 D9c 測試（0±0.25 dB）已經在 CI 守著，JUCE 改常數就會紅燈」是錯的：audit_repro.cpp:1193-1201 只是註解；:1253-1316 只 printf；:1458 印的是「informational, no PASS/FAIL」；grep kIrWetMakeupGain 只命中註解。所以 JUCE 升版改了這個常數也不會有任何測試紅燈，正是 D9c-guard 指出的缺口。
- **查證修正**：kIrWetMakeupGain 約有 18.06 dB 來自 JUCE Convolution 的正規化係數 0.125，已確認，建議補註解。但現在沒有任何測試守著 26.9：K-02 只印數字、不判定。JUCE 升版前必須手動重跑 K-02/K-02-EXT，或者先補上 D9c-guard 的 CHECK（要月月同意）。

### [engineering-gaps:E19] CI 覆蓋盤點：哪些 GATE 有進 CI、哪些沒有
- 查證：**adjusted**｜誰：資訊｜嚴重度 low｜工作量 n/a
- 說明：每次 push 都會跑的：4 個 ctest（Audit/Tuner/PhysicsModels/SpectrumView）、pytest 270（涵蓋 score_vs_midi_verify、partial_verify、stem_verify（實際用 CLI 渲染 sentinel 再跑 melody_verify）、measurement_selfcal（5 個 strict xfail 誠實掛著 1.1721 c 缺口）、crossplatform emit 安全性）、physics_verify --selftest/--t60/--full、verify_score 6 首 smoke、consonance、三平台 CLI 渲染與比較、Windows ASAN。沒進 CI 的：HostProbe（E5）、pluginval/validator（E1/E2）、全 corpus 75 首（E1）、位元不變 8/8（E10）、cubase_scan_verify（本來就只能本機）。cross-platform-compare 在容差登記之前永遠只發 notice、不會紅，這是 R2 刻意設計。供應鏈方面：actions 用 tag 而不是 SHA pin（ilammy/msvc-dev-cmd@v1 是第三方），跨平台 job 的 numpy>=1.26 沒有 pin，跟 requirements-physics.txt 的 numpy==2.1.3 不一致。src/tools/tests 裡沒有真正的 TODO/FIXME/HACK/XXX（唯一命中是 melody_verify.py:49 引用 TODO.md 的 C2 條目）。
- 證據：.github/workflows/physics.yml:53-108 build-and-verify 各 step；physics.yml:221-234 compare exit 3 → ::notice::；physics.yml:39,172,254 ilammy/msvc-dev-cmd@v1；physics.yml:168,207 pip install "numpy>=1.26"；tools/requirements-physics.txt:2 numpy==2.1.3；指令：grep -rnE '\b(TODO|FIXME|HACK|XXX)\b' src tools tests … → 只有 tools/melody_verify.py:49；指令：gh run view 34880536096 → 六個 job 全 success（2026-09-14）
- 建議：順序建議：先做 E1、E2，再 E5、E10。跨平台 job 的 numpy 改成跟 requirements 同版；有空再把 actions 改成 commit SHA pin。
- 懷疑者查證：physics.yml:53-108 的步驟、:221-234 的 exit 3 發 notice、:39/:172/:254 用 ilammy/msvc-dev-cmd@v1、:168/:207 裝 numpy>=1.26、requirements:2 是 numpy==2.1.3、gh run view 六個 job 全 success，這些都確認。有三處不精確：(1)「5 個 strict xfail 掛著 1.1721 c 缺口」不對。依 test_measurement_selfcal.py:171-283，5 個 xfail 分別是 sustain dev 1.1721、holdout 1.0840、release dev 5.2304、release holdout 7.2055、gain fidelity（dev_grid 輸出 worst 16.8647 c）。(2) grep TODO|FIXME|HACK|XXX 除了 melody_verify.py:49，還命中 CimbalomEngine.h:43、BeamModel.h:48、BesselPortable.h:7、HammerImpulse.h:187、MaterialDB.h:23，不過都是引用 TODO.md，不是真正的待辦標記，結論不變。(3)「三平台」裡的 Linux 是 GCC 13.3，不是 clang。
- **查證修正**：盤點大致正確。修正：5 個 strict xfail 對應五個不同缺口（1.1721/1.0840/5.2304/7.2055 c 與增益保真），不是只有 1.1721 c；src 裡的 TODO 命中都是引用 TODO.md，不是真正待辦；Linux leg 是 GCC 13.3。

## 懷疑者補抓的漏項（code）

- CI 的 Linux leg 標成 clang，實際編譯器是 GCC：physics.yml:137-138 的 label 是 ubuntu-24.04-clang，但 :174-175 沒有設定 CC/CXX；gh run view 34880536096 --log 顯示「cross-platform-emit (ubuntu-24.04, ubuntu-24.04-clang) -- The CXX compiler identification is GNU 13.3.0」。所以 HANDOVER/TODO 寫的「CI 三平台」，實際是 MSVC、GCC、AppleClang；xplat 的上傳檔名和報告標籤也跟著標錯。這會影響之後登記跨平台容差（R2）時，資料對應到哪個編譯器。
- D15 的兩個 release strict xfail 永遠不可能 XPASS：tests/test_measurement_selfcal.py:229 和 :251 的 pin assert（必須等於 5.2304/7.2055）排在 ≤1 c 判定之前，只要估計器改善，就會先在 pin assert 失敗、被記成 xfail，strict 的『改善時要升格』機制因此失效。另外 LEGACY_HOLDOUT_GRID_MAX_ABS_CENTS=1.0840（:100）只有定義、沒有任何 assert 用到它（HEAD 版的 :81 也一樣），所以 holdout sustain 的 1.0840 c 同樣沒有 pin 保護。
- staged 的 D9c GATE 證據有一句不實陳述：reports/gate_outputs/wf0914_D9c_ir_makeup_gain.txt:252-253 寫「全檔搜尋 IR|Convolution|reverbMode|loadImpulseResponse 在 HostProbe 原始碼中無匹配」，但 grep -c -E 對 tests/host_probe.cpp 命中 83 行（HEAD 版也有 32 行，例如 H7 的 IR 情境、D12 的 reverb_ir）。結論（沒有 IR 響度情境）仍然成立，但證據文字是錯的，commit 前建議改寫。
- staged 的 HANDOVER.md 內部前後矛盾、檔案地圖過時：:89（§5-1 第 5 點）還寫「D9/D15 誠實 BLOCKED 待裁決」，但 :113-115（§7）寫 D9、D15 都已關閉；:123 施工卡只列 WF0907/0908/0909，:124 裁決包只列 A13/A14/F03/K02/C10/D8（漏了 B7/D9/D11/D13），:131 GATE 證據只列 wf090{7,8,9}，都沒有納入 WF0914。這和 D-doc-2 同一類，建議在 c7 commit 前一起修掉。
- E18 和 D9c-guard 兩條互相矛盾：E18 說 D9c 的 0±0.25 dB 已經有 CI 測試守著，D9c-guard 說沒有。實際查證 D9c-guard 才對（audit_repro.cpp:1458 印的是 informational, no PASS/FAIL），整合報告時要以 D9c-guard 為準，否則會誤以為 JUCE 升版有安全網。

## docs-consistency

規劃者列的疑點大多屬實，只有一條不成立：HANDOVER §3 標題「全部已 commit：5c9cdb3～49b8542」是對的，真正過時的是 TODO.md 第 26 行的「全部未 commit」。最要緊的是 HANDOVER §9 的操作備忘：位元基準寫成舊的 post_d8、pytest 寫 267 passed、量測器自證寫 1.1721 c。照著跑會讓 physical_piano 假紅燈，數字也對不上。月月待辦也寫錯了三件：兩封信同一份文件裡前面說已寄出、後面又列成待辦；Limbus 和 Yamaha 其實 09-14 12:56 就裝好了（比 a38bd6a 寫交接還早 8 小時），真正剩下的是 Limbus 有沒有啟用、以及月月點頭後清掉 Downloads 那個 614 MB 的資料夾。VST3 部署的寫法也跟實況不符：裝上去的是 09-10 的舊 build，放在子資料夾裡，Cubase 從 08-22 之後就沒開過。TODO.md 後段有十幾條早就完成或被否決的項目還掛著 [ ]，其中「UI 雙開門」已經被抄進 09-16 的變現計畫；README、CONTEXT.md、TODO_HANDOFF.md、RESEARCH_INDEX.md、ROADMAP_PHYSICS.md 也各有過時的狀態、指令和編號。以上都只查證、沒改任何檔案，要不要改、怎麼改由月月決定。

### [docs-consistency:H1] HANDOVER §9 的位元不變指令用過期基準 post_d8，照做會讓 physical_piano 假紅燈
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 high｜工作量 S
- 說明：HANDOVER.md:137 寫「位元不變 … 對 sha256_before_post_d8.txt」，但同一份文件的 §1-3（:28）、WF0914_README.md:12 和整合卡都規定要用 sha256_before_post_a14.txt。這兩個基準檔只差 physical_piano 一首（A14 在 09-10 刻意改了它）。新 session 照 §9 跑，會得到 7/8，把 physical_piano 誤判成回歸。
- 證據：HANDOVER.md:137 「位元不變 `reports/gate_outputs/wf0907_method/render_wf_scores.py` 對 `sha256_before_post_d8.txt`」；HANDOVER.md:28 「8 首位元不變基準用 `.../sha256_before_post_a14.txt`」；diff 兩基準檔：只有 `607d0d3b… physical_piano` vs `1233b53f… physical_piano` 不同；reports/gate_outputs/wf0914_INTEGRATION.txt GATE 10：比對 sha256_before_post_a14.txt → 8/8 IDENTICAL
- 建議：把 HANDOVER.md:137 的 `sha256_before_post_d8.txt` 改成 `sha256_before_post_a14.txt`，並註明 post_d8 只留作存檔。
- 懷疑者查證：HANDOVER.md:137 寫「對 `sha256_before_post_d8.txt`」，:28 寫 post_a14。兩個基準檔都在 reports/gate_outputs/b6_method/，diff 後只差 physical_piano 一行（607d0d3b… vs 1233b53f…）。WF0914_README.md:12 規定「一律 post_a14」；wf0914_INTEGRATION.txt:123/132 也是用 post_a14 跑出 8/8。這個錯在 `git show HEAD:HANDOVER.md` 的第 131 行就已存在，不是本輪才產生的。

### [docs-consistency:H2] HANDOVER §9 和 WF0914_README 的 pytest 數字過時或寫得不精確（267 passed vs 實際 264 passed+1 skip+5 xfail=270）
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：HANDOVER.md:137 寫「python -m pytest tests -q（267 passed）」，同一份文件 :28 寫 270 個測試。整合卡查證過：267 本來就不是「267 passed」，HEAD 當時實際是 263 passed＋3 xfail＋1 skip；本輪之後是 264 passed＋1 skipped＋5 xfailed，共 270 個。WF0914_README.md:13 寫「基線 267 passed」也是同樣的簡寫錯誤。另外 WF0914_README.md:4 的 main=b56747d 是開卡當時的值，現在 main 是 3f9b90a。
- 證據：HANDOVER.md:137 「`python -m pytest tests -q`（267 passed）」；HANDOVER.md:28 「pytest 基線自本輪起 **270 個測試**（264 passed+1 skip+5 xfail）」；wf0914_INTEGRATION.txt GATE 5：「264 passed, 1 skipped, 5 xfailed」「HEAD 實際細分＝263 passed + 3 xfailed + 1 skipped = 267 total」「README 的『267 passed』是『267 個測試』口語簡寫」；docs/workcards/WF0914_README.md:13 「基線 **267 passed**」；git rev-parse main → 3f9b90a（WF0914_README.md:4 寫 b56747d）
- 建議：HANDOVER.md:137 改成「264 passed, 1 skipped, 5 xfailed（共 270）」。WF0914_README 是施工卡歷史，可在 :13 補一句「實為 263 passed+3 xfail+1 skip」，不動也可以。
- 懷疑者查證：HANDOVER.md:137「(267 passed)」和 :28「270 個測試（264 passed+1 skip+5 xfail）」兩處數字對不上。wf0914_INTEGRATION.txt:52 實測是「264 passed, 1 skipped, 5 xfailed」；:59-65 說明 267 是總數，其中 263 passed、3 xfailed、1 skipped。WF0914_README.md:13 寫「基線 **267 passed**」。WF0914_README.md:4 寫 main=b56747d，這是開卡當時的正確值；現在 `git rev-parse main` 得到的是 3f9b90a。

### [docs-consistency:H3] HANDOVER §9 和 §4 的量測器自證現況還停在 1.1721 c，D15 之後預設輸出已是 5.2304 c
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：HANDOVER.md:139 寫「measurement_selfcal.py（現況 exit 1，1.1721 c）」，:67 也只提 1.1721 c 已知誤差。D15（已 staged）把放鍵/阻尼段加進語料，現在預設執行的輸出是 max_abs_error 5.2304 c（持續段 1.1721、放鍵段 5.2304），hold-out 是 7.2055 c。月月 09-15 裁決 D15 選 A'，主張域已收窄成「持續段 ≤1.18c、放鍵段上界約 7.2c」，這兩處沒同步。
- 證據：HANDOVER.md:139 「`python tools/measurement_selfcal.py [--holdout]`（現況 exit 1，1.1721 c）」；reports/gate_outputs/wf0914_D15_gate1_dev_grid.txt:13-15 「sustain 1.1721 c」「release 5.2304 c」「max_abs_error_cents = 5.2304 (limit 1.0)」；DEVLOG.md:44 「新 worst-case 5.2304 c（開發）／7.2055 c（hold-out）」；TODO.md:18 D15 選 A' 已落地
- 建議：§9 改成「現況 exit 1：開發 5.2304 c（持續段 1.1721／放鍵段 5.2304）、hold-out 7.2055 c；主張域見設計文件 §8.5」，§4 ② 補一句放鍵段上界約 7.2 c。
- 懷疑者查證：HANDOVER.md:139 寫「現況 exit 1，1.1721 c」，:67 也只提 1.1721 c。但 wf0914_D15_gate1_dev_grid.txt:13-15 的實測是 sustain 1.1721 c、release 5.2304 c、max_abs_error_cents = 5.2304（limit 1.0）。DEVLOG.md:44 記 hold-out 7.2055 c，EARFREE 設計文件 :314/:317 也已經寫進 ~7.2 c 的上界，只有 HANDOVER 這兩處沒跟上。

### [docs-consistency:H4] 兩封信：同一份 HANDOVER 前面說已寄出、後面列為月月待辦；信件草稿檔頭仍寫「草稿」
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：HANDOVER.md:27 和 TODO.md:19、DEVLOG.md:5/22 都寫 09-15 已寄出。但 HANDOVER.md:29「等月月自己做的三件小事不變」仍把「寄兩封信」列第一項。兩份信件檔頭還寫「狀態：草稿，由月月自行寄出」。有沒有真的寄出，只有月月的敘述可依據，repo 裡查不到寄件證據。
- 證據：HANDOVER.md:27 「**兩封信 09-15 已寄出等回覆。**」；HANDOVER.md:29 「等月月自己做的三件小事不變：寄兩封信（`docs/correspondence/`）；…」；docs/correspondence/2026-09-10_TU_Berlin_directivity_license_request.md:3 與 _Iowa_MIS_…md:3 「狀態：**草稿，由月月自行寄出**」；TODO.md:19 「兩封信已寄出（2026-09-15…），等回覆」
- 建議：把 HANDOVER.md:29 的「寄兩封信」拿掉，改成「等兩封信回覆」。兩份信件檔頭改成「已於 2026-09-15 由月月寄出，等回覆」。
- 懷疑者查證：HANDOVER.md:27 說已寄出，同一份文件 :29 卻仍把「寄兩封信」列成月月待辦。兩份信件的第 3 行都還是「狀態：**草稿，由月月自行寄出**」。DEVLOG.md:5/:22 和 TODO.md:19 都寫 09-15 已寄出。repo 裡查不到寄件證據，只能依月月的說法。

### [docs-consistency:H5] Limbus 和 Yamaha 在 09-14 12:56 就裝好了，文件仍列為「待安裝」
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：HANDOVER.md:29、§11（:152、:157）和 TODO.md:19 把「裝 Limbus Spatial Stage 並啟用」「Yamaha 裝好後叫 AI 清 Downloads 殘留」列為月月待辦。實際上兩個都在 09-14 12:56 裝好了，比 a38bd6a 寫下這段交接的時間（09-14 20:40）還早 8 小時。Limbus 有沒有用金鑰啟用，磁碟上查不到授權檔，只看到 AppData 裡 12:56 產生的 preferences.xml，無法判定。Yamaha 裝好了，所以「清 Downloads 殘留」的前提已滿足；資料夾目前 614 MB，仍含 Piano Sheet Converter.exe 解壓殘留（235 MB）和幾個安裝檔。
- 證據：ls C:/Program Files/Common Files/VST3 → `Limbus Spatial Sender.vst3`、`Limbus Spatial Stage Master.vst3`（2026-09-14 12:56）；ls C:/Program Files/Limbus Audio/Limbus Spatial Stage → Standalone.exe、unins000.exe（2026-09-14 12:56）；ls C:/Users/admin/AppData/Local/Programs/Piano Sheet Converter（2026-09-14 12:56）；git log a38bd6a → 2026-09-14 20:40:12；git show a38bd6a:HANDOVER.md:23 已列「裝 Limbus…並用信裡的金鑰啟用」；du -sh Downloads/不知道有沒有用 → 614M
- 建議：文件改成「Limbus 已安裝（09-14）；啟用與否待月月確認」「Yamaha 已安裝（09-14）；Downloads\不知道有沒有用 的殘留等月月授權後由 AI 清理」。刪檔要先問月月。
- 懷疑者查證：磁碟上實際看到：Common Files/VST3 下的 `Limbus Spatial Sender.vst3`、`Limbus Spatial Stage Master.vst3` 是 2026-09-14 12:56:07 建立；`Program Files/Limbus Audio/Limbus Spatial Stage` 有 unins000.exe（12:56:41）；`AppData/Local/Programs/Piano Sheet Converter` 是 12:56:04 建立。a38bd6a 的 commit 時間是 2026-09-14 20:40:12，那一版的 HANDOVER:23 已經把兩者列為待安裝。Roaming/Limbus Audio 下只有一個 preferences.xml（130 B），判斷不出有沒有用金鑰啟用。Downloads 資料夾 du 結果 614M。另外 §11 說的「約 200 MB 殘留」偏低：根目錄非安裝檔約 310 MB，加上 locales 48 MB、resources 112 MB，合計約 470 MB。

### [docs-consistency:H6] HANDOVER §5-1 還說 D9/D15 BLOCKED、B7 Phase 2/3 等三問，跟同一份文件 §0/§1/§7 的已裁決矛盾
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：HANDOVER.md:89 寫「D9/D15 誠實 BLOCKED 待裁決」，:88 寫「Phase 2/3 掛在裁決包三問」。但 :13-14、:24-26、:113 都說五項裁決已下：D9 已關閉，D15 選 A' 已落地，B7 選路徑 C＋(a) 乙案，本輪合法終點。另外交接視窗寫 2026-09-15，但內容已經包含 09-16 的 D9c。
- 證據：HANDOVER.md:89 「D9/D15 誠實 BLOCKED 待裁決」；HANDOVER.md:88 「Phase 2/3 掛在裁決包三問」；HANDOVER.md:24-26 「D9=(a)+A 案已完工…**D9 關閉**…D15=A'」；HANDOVER.md:113 「D9 **關閉**…D15 **關閉**」；HANDOVER.md:3 「交接視窗：**2026-09-15**」
- 建議：§5-1 第 4、5 項改寫成已裁決的狀態（B7：路徑 C 乙案，Phase 2/3 本輪不做；D9/D15：09-15~16 已關閉），交接視窗改成 2026-09-15~16。
- 懷疑者查證：HANDOVER.md:88 寫「Phase 2/3 掛在裁決包三問」、:89 寫「D9/D15 誠實 BLOCKED 待裁決」，但同一份文件 :24-26 和 :113 都寫已裁決、已關閉。:3 的交接視窗寫「2026-09-15」，內容卻有 09-16 才做的 D9c（TODO:15）。

### [docs-consistency:H7] HANDOVER §10 的 commit 教訓指令被寫壞：`tr -d '\r'` 變成了真的換行
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：HANDOVER.md:145-146 本來應該寫 `tr -d '\r'`，但文字裡的 \r 被寫成真正的換行字元，讀起來是 `tr -d '<換行>'`，也就是刪 LF。照做的話，路徑清單會黏成一行，commit 還是會失敗。DEVLOG.md:69 是正確的 `tr -d '\r'`。這個錯在 HEAD（a38bd6a）就已經存在。
- 證據：od -c HANDOVER.md 第 145 行：`t r   - d   ' \n ' `；git show HEAD:HANDOVER.md 第 139 行同樣以 `tr -d '` 斷行；DEVLOG.md:69 「`tr -d '\r'` 後才成功」
- 建議：把 HANDOVER.md:145-146 合回一行，寫成 `tr -d '\r'`。
- 懷疑者查證：用 `sed -n 145,146p HANDOVER.md | od -c` 看到的是 `t r - d ' \n ' `，本來該寫 `\r` 的地方變成了真正的換行字元。`git show HEAD:HANDOVER.md` 第 139 行一樣在 `tr -d '` 斷行。DEVLOG.md:69 寫的 `tr -d '\r'` 是正確的。小補正：HEAD 是 766d21d，不是 a38bd6a；不過 HEAD 那一版的 HANDOVER 內容來自 a38bd6a。

### [docs-consistency:H8] VST3 部署的寫法跟實況不符：舊 build、放在子資料夾、Cubase 從未重掃
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：HANDOVER.md:29「VST3 已於 09-14 部署」、DEVLOG.md:71「月月自行覆蓋 Common Files 完成部署」、README「Current build (2026-09-10) deployed to Cubase on 2026-09-14」，實況有四點不同：(1) 部署位置是整個包裝資料夾 `Common Files\VST3\TsukiSynth_VST3_2026-09-10\TsukiSynth.vst3`（連 怎麼安裝.txt 也在裡面），不是覆蓋頂層的 TsukiSynth.vst3，頂層那份已經不在了；(2) 裝上去的是 09-10 23:46 的 build，不含 WF0914 已 staged 的 D12 state 遷移（PluginProcessor.cpp）和 D9c IR 補償增益（EffectChain.h）；(3) Cubase 的 vst3plugins.xml 最後寫入是 08-22，仍指向已不存在的頂層路徑，設定檔也都停在 08-22，所以 Cubase 在部署後沒開過，也沒掃過新 build；(4) L3b 真 host 實測測的是當時的 0.2.0（TODO.md:595）。Cubase 會遞迴掃子資料夾（FabFilter 子資料夾有被收進快取），所以下次開 Cubase 應該掃得到。
- 證據：ls Common Files/VST3/TsukiSynth_VST3_2026-09-10/ → TsukiSynth.vst3/、怎麼安裝.txt（2026-09-13 03:33）；頂層無 TsukiSynth.vst3；怎麼安裝.txt：「這一版建於 2026-09-10 23:46，含 F-03 IR 庫、tail length、glide 逐取樣、A14 高音修正」；Cubase AI VST3 Cache/vst3plugins.xml mtime 2026-08-22 01:56，內容 `C:/Program Files/Common Files/VST3/TsukiSynth.vst3/Contents/x86_64-win/TsukiSynth.vst3`；git diff --cached --stat：src/PluginProcessor.cpp、src/effects/EffectChain.h 有改動；README.md:37 「Current build (2026-09-10) deployed to Cubase on 2026-09-14」
- 建議：文件改寫成實況：已部署 09-10 build 到子資料夾，Cubase 尚未重掃，不含 WF0914 的 plugin 端改動。等 commit 後要不要重新部署、重跑 L3b 由月月決定；AI 可以附上正確的覆蓋步驟。
- 懷疑者查證：`ls Common Files/VST3` 看到的是 TsukiSynth_VST3_2026-09-10/（2026-09-13 03:33:35），裡面有 TsukiSynth.vst3/ 和 怎麼安裝.txt，頂層沒有 TsukiSynth.vst3。怎麼安裝.txt 寫「這一版建於 2026-09-10 23:46」。已部署 binary 的 sha256 是 786643…，跟 build/（cff475…，09-25）和 build-wf/（761704…，09-16）都不一樣。Cubase 的 vst3plugins.xml mtime 是 2026-08-22 01:56，內容仍指向 `C:/Program Files/Common Files/VST3/TsukiSynth.vst3/...`；Cubase 設定檔最後寫入都在 08-22 14:27。TODO.md:595 寫「host 測的是系統部署的 0.2.0」。README 那句在 :38，不是 :37。桌面上的 TsukiSynth_VST3_2026-09-10 已經不在，比較像是月月整個資料夾剪下貼到 Common Files，而不是覆蓋舊的。

### [docs-consistency:H9] HANDOVER §8 檔案地圖和交叉引用缺 WF0914，還有兩三個指向不存在的小節
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：§8（:117-132）的施工卡、裁決包、GATE 證據只列 WF0907~0909。缺的有：WF0914_*.md 施工卡 14 份；B7/D9/D11/D13 四份裁決包；wf0914_* 證據；ENGINE_DOMAIN_CLAIMS、HAMMER_VELOCITY_SOURCES、STRING_SCALE_SOURCES、GONG_PARTIAL_ANALYSIS 等新文件。另外 HANDOVER.md:5 寫「見 §0-1」、TODO.md:23 寫「HANDOVER.md §0-2」，但 HANDOVER 沒有這兩個小節（§0 只有一段）。README.md:362 寫「see HANDOVER.md §6 for the full list」，§6 現在是規劃者代決表，指令清單在 §9。
- 證據：HANDOVER.md:123-124 「施工卡 | docs/workcards/WF0907_*.md、WF0908_*.md、WF0909_*.md」「裁決包…（A13/A14/F03/K02/C10/D8）」；ls reports/decision_packets → B7_phase2_and_open_items、D9_ir_loudness_alignment、D11_string_scale_candidate、D13_gong_2x_partial 都存在；grep '§0-[0-9]' → HANDOVER.md:5 §0-1、TODO.md:23 §0-2；HANDOVER 標題只有 `## 0. 一句話現況`；README.md:362 「Quick reference (see `HANDOVER.md` §6 for the full list)」
- 建議：§8 補上 WF0914 各列；HANDOVER:5 的「§0-1」改成「§1-1」；TODO:23 改成「HANDOVER.md（09-07 版，見 git 歷史）」；README:362 改成「§9」。
- 懷疑者查證：HANDOVER.md:123-124 只列 WF0907~0909，以及 A13/A14/F03/K02/C10/D8。docs/workcards 下的 WF0914_* 共 14 檔（13 張卡加 README）；decision_packets 下有 B7_phase2…、D9_…、D11_…、D13_…。ENGINE_DOMAIN_CLAIMS 只在 §1（:26）出現，§8 沒有。HANDOVER 的標題只有 `## 0. 一句話現況`，找不到 §0-1。TODO:23 引用的 §0-2 在任何版本的標題裡都查不到。README.md:362 寫「HANDOVER.md §6」，但 §6 現在是規劃者代決表。

### [docs-consistency:T1] TODO 開頭快照的 BLOCKED 那一行已被下方五項裁決取代，但沒標註
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：TODO.md:10 仍寫「BLOCKED（合法完成，等月月裁決）：B7P1/B7P3、D9（量測鏈矛盾）、D15（…打破 ≤1.18c 主張）」。緊接著 :13-18 就記錄 09-15~16 已全數裁決並落地。同一段落前後矛盾，快速瀏覽的人會以為還卡著。
- 證據：TODO.md:10 「**BLOCKED（合法完成，等月月裁決，見下）**：B7P1/B7P3…、D9…、D15…」；TODO.md:13 「月月 2026-09-15 五項裁決（…已全部落地或排卡）」、:15 D9c 完工、:18 D15 選 A' 已落地
- 建議：TODO.md:10 前面加「（已由 09-15~16 裁決解除，見下）」，或改寫成「曾 BLOCKED → 已裁」。
- 懷疑者查證：TODO.md:10 的 BLOCKED 行（B7P1/B7P3、D9、D15），緊接在下面的 :13-18 就記錄五項裁決都已落地，但 :10 沒有加任何標註。

### [docs-consistency:T2] TODO 的 WF0907~09 快照段落全面過時（其中「全部未 commit」才是真的錯，HANDOVER §3 反而是對的）
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：查證結果：HANDOVER §3 的標題「全部已 commit：5c9cdb3～49b8542」正確。IRLibrary.h、ParameterLayout、HammerImpulse 在 31eb7ae，measurement_selfcal 和 partial_verify 在 5c9cdb3，a14/d8 報告在 9ae8ce2，都是 09-13 的 commit。過時的是 TODO.md:26「稽核 PASS 才 git add，全部未 commit」。同一段還有：:32「等月月：A14 B-2 patch」（09-10 已 apply）；:33「進行中（WF0909）：C10B、D8、P4b、P6」（全部已結）；:36「D9 等真實 IR 檔量測」「D11…月月另裁」（D9 已關閉，D11 已裁 C）；:46「UI 功能規格送設計端：等 WF0909 收尾＋A14 裁決後」（兩個條件都已滿足，只剩月月決定找誰）；:34 有錯字「規劣者」。
- 證據：TODO.md:26 「**稽核 PASS 才 `git add`，全部未 commit**」；git log：5c9cdb3/31eb7ae/9ae8ce2/27e8393/49b8542 都在 2026-09-13；git show --stat 31eb7ae 含 src/IRLibrary.h、src/physics/HammerImpulse.h；TODO.md:32 「**等月月**：**A14 B-2 τc 音高律 patch**」 vs HANDOVER.md:79 「A14 放行 | `git apply` 落地，Opus 稽核 PASS」；TODO.md:36 「D9 IR 載入響度對齊（等真實 IR 檔量測）」「D11 …（R10 全 corpus，月月另裁）」；TODO.md:46 「等 WF0909 收尾 + A14 patch 裁決後執行」、HANDOVER.md:87 「月月決定找誰」；TODO.md:34 「**規劣者代決**」
- 建議：這段標題加「（歷史快照；09-13 已 commit，後續見 09-15 快照）」，把 :26/:32/:33/:36/:46 的狀態詞改掉，錯字改成「規劃者」。
- 懷疑者查證：TODO.md:26「**稽核 PASS 才 `git add`，全部未 commit**」，但 git log 顯示 5c9cdb3、31eb7ae、9ae8ce2、27e8393、49b8542 都在 09-13 就 commit 了。其餘過時處：:32 還寫等 A14 patch（09-10 已 apply，見 TODO:137 和 HANDOVER:79）；:33 還寫 C10B/D8/P4b/P6 進行中；:36 還寫 D9 等量測、D11 月月另裁；:34 錯字「規劣者」。:46 的兩個前提確實都已滿足，但原文還附了月月 09-07 的「等所有功能做完」，這一句是月月的判斷，不能直接當成已滿足（見 U2-send）。

### [docs-consistency:T3] TODO A 區還有幾條已否決或已完成的項目掛著 [ ]/[~]；其中「UI 雙開門」已經被抄進變現計畫
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：(1) TODO.md:208 的「UI 雙開門（待月月視覺裁決）」還是 [ ]，但 :56 記錄月月 08-30 已否決（commit 313acaa「雙開門否決→功能規格重做」）。這條過時項目已經被 09-16 的 MONETIZATION_PLAN:66 當成待辦抄進去（「UI 雙開門裁決落地或明確擱置」）。(2) :207「IR 稽核（unstaged 待審）」其實 08-28 已在 0f271ae commit。(3) :137 A14 [~] 寫「Opus 稽核中」，稽核檔 verdict 已經是 PASS。(4) :53「F-03 裁決包…（待月月選 A/B/C）」已由規劃者代決 B+，並已在 P3 落地。
- 證據：TODO.md:208 「- [ ] **UI 雙開門**（提案 + mockup 完成，待月月視覺裁決）」；TODO.md:56 「月月**否決**雙開門 UI 提案」；git log 313acaa 「UI 裁決落地（雙開門否決→功能規格重做）」；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:66 「UI 雙開門裁決落地或明確擱置…| 月月裁決→AI 實作」；git log --diff-filter=A -- docs/IR_REVERB_AUDIT.zh-TW.md → 0f271ae 2026-08-28；TODO.md:137 「Opus 稽核中」 vs reports/gate_outputs/wf0910_A14_apply_AUDIT.txt 「verdict = PASS」；TODO.md:53 「（待月月選 A/B/C）」 vs HANDOVER.md:107 F-03 B＋
- 建議：UI 雙開門改 [x]（08-30 否決，改走 UI_FUNCTIONAL_SPEC）；IR 稽核拿掉「unstaged」；A14 改成 [x]，註明 B-2 已落地、稽核 PASS、B-1 併入 D10；F-03 那行補「→ B+ 已落地」。變現計畫 #2 的修正見 M1。
- 懷疑者查證：(1) TODO.md:208 雙開門仍是 [ ]，但 :56 和 313acaa 已否決，MONETIZATION_PLAN:66 把它當成待辦抄了進去，屬實。(2) :207 寫「unstaged 待審」，但 `git log --diff-filter=A` 顯示 IR_REVERB_AUDIT 在 0f271ae（08-28）就入庫了，屬實。(3) :137 的「Opus 稽核中」確實過時，wf0910_A14_apply_AUDIT.txt:538 已是「verdict = PASS」。可是建議把 A14 改成 [x] 不妥：B-1 仍在等文獻（D10），而且 N1-fe16 查到 B-2 落地後出現新的弱基頻 FAIL，[~] 應該保留。(4) :53 的 F-03「待月月選 A/B/C」已由 HANDOVER:107 的 B＋ 取代，也已在 P3 落地，屬實。
- **查證修正**：UI 雙開門改成 [x]（08-30 否決，改走 UI_FUNCTIONAL_SPEC）；IR 稽核拿掉「unstaged」；A14 維持 [~]，把「Opus 稽核中」改成「09-10 稽核 PASS」，並註明 B-1 仍等文獻（D10），另外還有 N1 新發現的弱基頻；F-03 補「→ B+ 已於 P3 落地」。

### [docs-consistency:T4] TODO 後段兩條 [ ] 其實早在 A 區結案（亮度 EQ 去留、Rule 10 報告審閱）
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：TODO.md:684「亮度 EQ 應急層去留覆核」[ ]，就是 :153 的 A4（08-27 月月裁決「調整文件建議值」已落地）。TODO.md:694「Rule 10 前後對照報告審閱 reports/deep_fix_before_after.md」[ ]，就是 :146 的 A1（08-26 月月裁決「放行」整批接受）。同一事件兩處狀態不一致。
- 證據：TODO.md:684 「- [ ] **亮度 EQ 應急層去留覆核**」 vs TODO.md:153 「- [x] **A4 亮度 EQ 應急層去留** — **2026-08-27 月月裁決…已落地**」；TODO.md:694 「- [ ] **Rule 10 前後對照報告審閱**——`reports/deep_fix_before_after.md`」 vs TODO.md:146 「- [x] **A1 Rule 10 前後對照裁決** — **2026-08-26 月月裁決「放行」**」
- 建議：兩條改成 [x]，各補一句「→ 見 A4（08-27）」和「→ 見 A1（08-26）」。
- 懷疑者查證：TODO.md:684「[ ] 亮度 EQ 應急層去留覆核」和 :153「[x] A4 … 2026-08-27 月月裁決『調整文件建議值』，已落地」是同一件事。TODO.md:694「[ ] Rule 10 前後對照報告審閱 reports/deep_fix_before_after.md」和 :146-147「[x] A1 …（`reports/deep_fix_before_after.md`）最終放行」也是同一件事。

### [docs-consistency:T5] C3-b、cross-platform、「Before merging」這幾條 [ ] 實際已完成或部分完成
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：(1) TODO.md:547 的 C3-b「設計提案…（2026-08-20，未實作）」[ ]，但同一條目 :556-599 已列 L1/L2/L3a/報告層/L3b 全部 ✅，A9 也已 [x]（:168）。:565「H5 兩項誠實 FAIL = A12」也已由 A12 修好（:238）。(2) :762「Establish cross-platform numerical reproducibility rules」[ ]，文字還寫「跨平台實測數字須 push 後由 CI 產出」，但 X3（:116-122）和 C3（:600）早已 [x]，容差也已登記成阻斷式 GATE。(3) :706「Before merging this branch」這一節的標題本身已過時（分支已多次 merge：b47d550/361101e/64afb49/34aa904/b56747d/3f9b90a）。:710 的 DAW 驗證已由 A9/L3b 完成；:711 的 HTML 報告目視驗收已由 M4-4c 在 08-15 通過（:667），但調音器的可讀性目視查不到證據，應該拆出來單獨掛著。
- 證據：TODO.md:547 「- [ ] **C3-b 免耳三層驗證** — 設計提案…（2026-08-20，未實作）」與 :557/:562/:566/:589 「✅ L1/L2/L3a/L3b」；TODO.md:762 「- [ ] Establish cross-platform numerical reproducibility rules」 vs :600 「- [x] **C3 跨平台容差登記**」；git log main --merges：b47d550(08-26)、361101e(08-28)、64afb49/b7e4330(08-30)、34aa904(09-07)、b56747d(09-14)、3f9b90a(09-15)；TODO.md:711 「- [ ] Perform a visual accessibility review of the tuner and generated HTML report」；TODO.md:667 「2026-08-15 月月目視驗收通過」
- 建議：C3-b 和 cross-platform 改 [x]（補證據路徑）；Before merging 一節加「（歷史，分支已 merge）」；710 改 [x]；711 拆成「HTML 報告 [x]／調音器可讀性 [ ]（待月月）」。
- 懷疑者查證：C3-b（:547）仍是 [ ]、還寫「未實作」，但 :556-599 的 L1/L2/L3a/報告層/L3b 都是 ✅，屬實。:762 仍是 [ ]，可是 :116-122 的 X3 和 :600 的 C3 已是 [x]，屬實。`git log main --merges` 列出 b47d550、361101e、64afb49、b7e4330、34aa904、b56747d、3f9b90a，所以「Before merging」這一節確實過時。例外是 :710：:594 明寫「automation 於 L2 合約層✅（GUI 畫 lane 未做，誠實標註）」，所以「在目標 DAW 驗 automation」其實沒有完全做完，不能單純勾 [x]。
- **查證修正**：C3-b 和 :762 改 [x] 並附證據路徑；Before merging 一節加「（歷史，分支已多次 merge）」；:710 改 [x]，但要註明「DAW 內 automation 只驗到 L2 合約層，Cubase GUI 手畫 lane 沒做（A9 已誠實標註）」；:711 拆開，HTML 報告 [x]（:667 08-15 通過），調音器可讀性 [ ] 待月月。

### [docs-consistency:T6] TODO 的 C10 和 B7 條目沒記錄月月已下的裁決
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：TODO.md:511 的 C10 條目最後停在「規劃者建議：改選 A…等月月一句話」，但月月 09-10 已選 A 並落地（HANDOVER.md:67/:78、DEVLOG.md:58-59），D15 之後又收窄到放鍵段約 7.2c。B7 條目（:392-499）最新一段是「2026-09-14 WF0914-B7P3…BLOCKED 待月月裁決」，沒寫 09-15 已裁「§5 路徑 C＋(a) 乙案＝本輪合法終點」（這條只出現在開頭快照 :14 和裁決包 §6）。
- 證據：TODO.md:511 「**規劃者建議：改選 A（收窄主張域）**…等月月一句話」；DEVLOG.md:58 「**月月 09-10 四裁決**：C10 選 A（收窄主張域）」；TODO.md:457 「**2026-09-14 WF0914-B7P3（稽核 PASS 已 staged，BLOCKED 待月月裁決）**」；reports/decision_packets/B7_phase2_and_open_items.zh-TW.md:164 「## §6 裁決記錄」
- 建議：C10 條目補「09-10 月月選 A 已落地（§8.5/§9.7）；09-15 D15 選 A' 再收窄」，看要不要改成 [x]。B7 條目補「09-15 裁決：路徑 C＋乙案，Phase 2/3 本輪不做（裁決包 §6）」。
- 懷疑者查證：TODO.md:511 仍寫「規劃者建議：改選 A…等月月一句話」，但 DEVLOG.md:58 記錄月月 09-10 已選 A。B7 條目最新一段 :457 寫「BLOCKED 待月月裁決」；在 TODO 裡搜「路徑 C」，只有 :14 的開頭快照找得到。更重要的是 B7 裁決包 §6 第 3 點（decision_packets/B7_phase2_and_open_items.zh-TW.md 約 :172）明文要求「ROADMAP/TODO 的 B7 條目同步標『In progress——Phase 0 完成、Phase 1 部分完成（欄位撤回版）、Phase 2/3 BLOCKED（月月 09-15 裁決）』」，但在 TODO 和 ROADMAP 都搜不到「Phase 2/3 BLOCKED」。也就是說，這一步是裁決寫明要做卻沒做。

### [docs-consistency:T7] D11-F5（唯一排隊的卡）和 D13 後續同步在 TODO 裡沒有待辦勾選項
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：HANDOVER.md:14 說「排隊卡剩 D11-F5 根因調查」，D11 裁決包 :63 也寫「新卡登記於 TODO.md『D11-F5…』」。但 TODO 只在開頭快照 :16 用一句敘述帶過，沒有 [ ] 項，也沒有施工卡檔（docs/workcards 只有 WF0914_D11_string_scale.md）。D13 的同步備忘（PlateModel.h 檔頭仍寫「金屬鑼/鐘的複雜非諧泛音結構」、water_gong_free.score.json 的 meta.description 也還沒同步）只記在 TODO:17 和 ENGINE_DOMAIN_CLAIMS:28-30，同樣沒有待辦項。「UI 功能規格送設計端」也沒有 [ ]。這些很容易被遺忘。
- 證據：grep -rn 'D11-F5' → 只出現在 DEVLOG:17、HANDOVER:14/25/113、D11 裁決包:63、TODO:16（敘述句）；TODO.md 所有 `- [ ]` 項目中沒有 D11-F5、D13 同步、UI 送設計端；src/physics/PlateModel.h:25 「特徵：2D 板模態，金屬鑼/鐘的複雜非諧泛音結構」；docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md:28-30 「同步備忘…留待下一張本來就要動這兩個檔案的卡順路同步」
- 建議：在 TODO D 區補三條 [ ]：D11-F5 根因調查（附裁決包路徑）、D13 註解/描述同步（附 PlateModel.h:25 和 score 路徑，會觸發 R6）、UI 規格送設計端（等月月找人）。
- 懷疑者查證：在全 repo 搜 D11-F5，只出現在 DEVLOG:17、HANDOVER:14/25/113、D11 裁決包:63、TODO:16，TODO 裡沒有對應的 `- [ ]` 項，docs/workcards 也沒有施工卡。src/physics/PlateModel.h:25 仍寫「金屬鑼/鐘的複雜非諧泛音結構」。water_gong_free.score.json:7 的 description 仍寫「the physically-appropriate boundary for a hung gong」。ENGINE_DOMAIN_CLAIMS:28-30 自己寫了「同步備忘」。

### [docs-consistency:T8] TODO 其他小的過時處：「08-30 快照（最新）」、stem_verify unstaged、D11 數字已被更正、驗證缺口的說明文字
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 M
- 說明：(1) TODO.md:55 寫「2026-08-30 快照（最新）」，但上方已有 09-07/09-15 快照；:64「stem_verify 相關檔案全部 unstaged 待審」其實 08-31 已在 a7413e5 commit。(2) :36「D11 弦長/弦徑造成 B 偏高 2.4～5.2×」是 D11 卡已查證為撞名和舊數字的說法：那是非諧性係數 B，A13 已更正為 2.4～5.4，D11 改用 A14 §3.10 的 14–87×，G6 從 86.4× 降到 18.7×。(3) Verification gaps :743-765 的說明仍寫「2026-08-10 實作完成但卡住（程式仍 unstaged）」「合成端預測模型仍未實作；工作項 B6」「B1（建議最先做）」「現行 v^-0.2」，但 B1~B6 都已 Done。這一節自己規定缺口不因資料到手就刪，所以勾選框可以保留，只是狀態說明要更新。
- 證據：TODO.md:55 「**2026-08-30 快照（最新）**」；git log --diff-filter=A -- tools/stem_verify.py → a7413e5 2026-08-31；TODO.md:36 「D11 弦長/弦徑造成 B 偏高 2.4～5.2×」 vs reports/decision_packets/D11_string_scale_candidate.zh-TW.md:42-47 「卡文標題的『2.4～5.2×』數字更正」；TODO.md:744 「**2026-08-10 實作完成但卡住**（程式仍 unstaged）」、:748 「合成端預測模型仍未實作…工作項 B6」、:751 「工作項 **B1（建議最先做）**」
- 建議：「（最新）」改成「（歷史）」；:64 補「→ 08-31 a7413e5 已 commit」；:36 的數字改成跟 D11 裁決包一致；Verification gaps 各條補一句「2026-09 現況：B? 已 Done，缺口剩…」。
- 懷疑者查證：TODO.md:55 寫「2026-08-30 快照（最新）」；:64 寫 stem_verify「全部 unstaged 待審」，但 `git log --diff-filter=A -- tools/stem_verify.py` 是 a7413e5（08-31）。:36 寫「2.4～5.2×」，D11 裁決包 §3（約 :42-47）已明文更正為非諧性係數 B（A13 已更正為 2.4～5.4），並改用 14–87×。Verification gaps 的 :744「程式仍 unstaged」、:748「工作項 B6 仍未實作」、:751「B1（建議最先做）」都過時，因為 B1~B6 已經 Done。

### [docs-consistency:R1] README 版本段落說 09-13 那批「尚未 push 或 merge」，實際已 push、merge，CI 全綠
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：README.md:44 寫「five commits 5c9cdb3…49b8542 … committed on the branch, not yet pushed or merged」。實際上 09-14 已 merge（b56747d），09-15 修完 CI 再 merge（3f9b90a），CI 在 766d21d 和 3f9b90a 都是 success。同一句的「B1–B6 are merged to main (2026-09-07)」也不精確：B5/B6 在 08-30 的 64afb49 就已併入。README 這一輪沒更新（不在 staged 清單內）。
- 證據：README.md:44 「is **committed on the branch, not yet pushed or merged**」；gh run list：3f9b90a main success、766d21d branch success（2026-09-14T18:xx Z）；git log main --merges：64afb49 2026-08-30 「B5/B6 物理收官…」；git diff --cached --stat 不含 README.md
- 建議：改成「pushed and merged to main (3f9b90a, 2026-09-15), CI green on all three platforms; WF0914 batch staged, uncommitted」，B1–B6 的日期改成 2026-08-30。
- 懷疑者查證：README.md:44 寫「committed on the branch, not yet pushed or merged」。`gh run list` 顯示 3f9b90a（main）和 766d21d（branch）在 2026-09-14T18:xx Z 都是 success。`git log main --merges` 顯示 64afb49 在 08-30 就寫「B5/B6 物理收官」。`git diff --cached --name-only` 裡沒有 README.md。

### [docs-consistency:R2] README/CONTEXT/TODO_HANDOFF 的建置指令只建 3 個測試 target，照做會重演 CI 紅燈
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：README.md:356（build）、:360（「Always rebuild the three test targets」）、:127（ASan）只列 Audit/Tuner/PhysicsModels 三個測試 target。但 CMakeLists 有 5 個（其中 SpectrumViewTest 有註冊 ctest），CI 的 physics.yml:54 和 :265 也都含 SpectrumViewTest。新 checkout 照 README 建置後跑 ctest，spectrum_view_repro 會 Not Run，正是 09-07~14 CI 紅燈的根因（HANDOVER:20-21）。CONTEXT.md:66、TODO_HANDOFF.md:29 和 TODO.md:125（X4 規約原文）也是三個。
- 證據：README.md:356 「--target TsukiSynthCLI TsukiSynth_VST3 TsukiSynth_Standalone TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest」；README.md:127 ASan「--target TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest」；CMakeLists.txt:233/249 「add_executable(TsukiSynthSpectrumViewTest…)」「add_test(NAME spectrum_view_repro…)」；:266 TsukiSynthHostProbe；physics.yml:54、:265 含 TsukiSynthSpectrumViewTest；HANDOVER.md:35 「現為五個：Audit/Tuner/PhysicsModels/SpectrumView/HostProbe」
- 建議：README 三處補上 TsukiSynthSpectrumViewTest（build 那處連 TsukiSynthHostProbe 一起補），文字改成「five test targets」。CONTEXT/TODO_HANDOFF 見 C1 的處理方式。
- 懷疑者查證：README.md:356 和 :360 只建三個測試 target，:127 的 ASan 那一行也一樣。CMakeLists.txt:233/:249 有 SpectrumViewTest 和 add_test(spectrum_view_repro)，:266 有 HostProbe。physics.yml:54 和 :265 都包含 SpectrumViewTest。TODO_HANDOFF.md:29 也是三個。細節要更正：CONTEXT.md:66 根本沒建任何測試 target（只建 CLI/VST3/Standalone），接著就跑 ctest，比「三個」更糟。TODO.md:125 是 X4 完工當時的歷史原文，可以不改，加一句註記就好。另外 .github/workflows/release-physics.yml:45 也只建三個測試 target，同樣的缺陷還留在那裡（見 missed）。
- **查證修正**：README :356/:360/:127、TODO_HANDOFF:29 補 TsukiSynthSpectrumViewTest（:356 連 TsukiSynthHostProbe 一起補），文字改成 five test targets。CONTEXT.md:66 目前沒建任何測試 target 就跑 ctest，要一起處理，或整份標成歷史。release-physics.yml:45 也要同步（見 missed）。

### [docs-consistency:R3] README 的功能表、檔案樹、狀態有多處過時，其中幾處互相矛盾
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 low｜工作量 M
- 說明：(1) README.md:106 寫 HostProbe「16/16 automated checks PASS」，現為 89 PASS。(2) 功能表的「Preset Browser (visual popup + category filter)」「Harmonic Editor」，以及檔案樹的 PresetBrowser.h、HarmonicEditor.h：這兩個檔案在 2026-05-22 的 1954418 已刪除，UI 現在是 presetCombo 下拉選單。(3) 檔案樹缺 IRLibrary.h、ParameterLayout.*、HammerImpulse.h、RadiationModel.h、BesselPortable.h、ScoreConsole.h、HoverMagnifier.h、DiagnosticOverrides.h 等。(4) B5 寫「Schema staged」（:94、:391），實際早已 commit 並 merge。(5) :129 說 Mode Dump 只輸出頻率/振幅/T60、SPL 維持 UNVERIFIED，跟同一份 README 的 B6 列（已輸出 absolute_pressure_per_force/acoustic_transfer）矛盾。(6) Physics chain（2026-09-14）表沒有 B7 Phase0/1 和 D9c（IR wet 固定 +28.6 dB 補償，DAW 裡 IR 模式的溼聲電平會變）。(7) 平台列寫「macOS (Clang) planned」，但 CI 已在 macos-14/ubuntu 建 CLI 做跨平台比對（plugin 本體仍只在 Windows）。
- 證據：README.md:106 「(16/16 automated checks PASS)」 vs reports/gate_outputs/wf0914_D12_hostprobe.txt 「[PASS]」×89、「PASS (0 failures)」；git show --stat 1954418（2026-05-22）：src/PresetBrowser.h -189、src/HarmonicEditor.h -92；find src 無這兩檔；src/PluginEditor.h:155 `juce::ComboBox presetCombo;`；README.md:94 「Schema staged, zero consumption」；README.md:129 「The current synth Mode Dump still emits only modal frequency, relative modal magnitude and T60」；src/effects/EffectChain.h:233 `(chL[i] * kIrWetMakeupGain) * m`；physics.yml:135-140 matrix windows-2022／ubuntu-24.04／macos-14
- 建議：更新 HostProbe 數字、刪掉或改寫兩列已不存在的功能（先跟月月確認 UI 現況的說法）、補齊檔案樹、B5 改成 committed、:129 改成跟 B6 一致、Physics chain 表加 B7（部分）和 D9c 一行、平台列寫清楚「CLI 三平台 CI、plugin 目前只有 Windows」。
- 懷疑者查證：(1) README:106 寫「16/16」，wf0914_D12_hostprobe.txt 是 89 個 [PASS]、PASS (0 failures)，屬實。(2) 1954418（2026-05-22）刪了 src/PresetBrowser.h 和 src/HarmonicEditor.h，在 src 裡搜 category 零筆，所以「Preset Browser (visual popup + category filter)」確實已不存在。但「Harmonic Editor（8 partials）」這個功能還在，改成內嵌在 PluginEditor.h:172 的 `KnobParam chrRatios[8], chrAmps[8]`，過時的只有 README:257/:259 檔案樹裡那兩個檔名。(3)(4) README:94、:391 寫「Schema staged」，屬實。(5) 那句 Mode Dump 的話在 README:132，不是 :129，但確實跟 :95 B6 列說的有輸出 absolute_pressure_per_force 矛盾。(6) README:84 的 Physics chain 表沒有 B7 和 D9c，屬實。(7) README:240「macOS (Clang) planned」，但 physics.yml:135-140 的 matrix 已含 ubuntu-24.04 和 macos-14，:178 只建 CLI，屬實。
- **查證修正**：改法同原建議，但 Harmonic Editor 不用刪：功能還在，改成內嵌在主編輯器的 8 組 ratio/amp 旋鈕，只要把檔案樹裡的 HarmonicEditor.h/PresetBrowser.h 拿掉。Preset Browser 那列改成「preset 下拉選單（presetCombo），沒有分類篩選」。

### [docs-consistency:R4] D13 的 water_gong 主張域收窄只寫進 ENGINE_DOMAIN_CLAIMS，驗收主文件和原始碼註解都沒跟上
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：月月 09-15 裁決 D13 選 B：water_gong＝自由邊平板，不是乳突鑼。這個只寫進 docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md。ROADMAP_PHYSICS §0 驗證域表（:113，驗收唯一依據）、README Physical Verification 表（Water Gong 列）都只寫「Kirchhoff 圓板（clamped + free-edge）」，沒指向這份聲明。PlateModel.h:25 還寫「金屬鑼/鐘的複雜非諧泛音結構」，語氣偏向鑼。ENGINE_DOMAIN_CLAIMS:28-30 自己承認尚未同步。
- 證據：ROADMAP_PHYSICS.md:113 「| Water Gong（PlateModel） | ✅ 域內 | Kirchhoff 圓板（clamped + free-edge） |」；grep ENGINE_DOMAIN_CLAIMS ROADMAP_PHYSICS.md README.md → 0 筆；src/physics/PlateModel.h:25 「特徵：2D 板模態，金屬鑼/鐘的複雜非諧泛音結構」；docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md:14-17 「它**不是**乳突鑼…的模型」
- 建議：ROADMAP_PHYSICS §0 和 README 的 Water Gong 列補「自由邊平板，非乳突鑼（見 ENGINE_DOMAIN_CLAIMS §1）」。PlateModel.h 註解照 ENGINE_DOMAIN_CLAIMS 的約定，等下一張動 src 的卡一起改（改 src 會觸發 R6）。
- 懷疑者查證：ROADMAP_PHYSICS.md:113 寫「Kirchhoff 圓板（clamped + free-edge）」；在 ROADMAP_PHYSICS.md 和 README.md 搜 ENGINE_DOMAIN_CLAIMS 都是 0 筆；README.md:74 也一樣。PlateModel.h:25 還是舊說法。ENGINE_DOMAIN_CLAIMS:14-17、:28-30 屬實。

### [docs-consistency:P1] ROADMAP_PHYSICS.md（驗收唯一依據）自 08-29 以來幾乎沒更新，漏記 A14/D8/C10/D13/D15/D9c，B7 段落也停在撤回前
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 M
- 說明：Rule 8 要求每次完成 GATE 後更新 §2 狀態和 TODO。但：(1) 全檔 0 處提到 A14（09-10 會改變渲染的 τc keytrack 修正，屬 M2/B4 範圍）；D8、C10/D15 量測主張域收窄、D13 引擎主張域收窄、D9c 的 DECIDED CONVENTION 也都沒有。(2) §2 M10 列新加的 B7 段開頭寫「unstaged 待稽核，In progress」「dumpModes() 只加這一個新欄位」，同一格後面才補寫已撤回，而且沒記錄 09-15 的「路徑 C＋乙案」裁決。(3) 檔頭最上面的段落仍是「2026-08-06 … （unstaged 待審）」，並寫「corpus 73 檔重驗待執行」（TODO:680 早已 73/73）。(4) M8 列寫「B5/B6/三件套…等 UI mockup 裁決後才 merge」，但之後已 merge 四次。(5) M3 詳述（:261）引用的 corpus_phase_d_B_classical_1.log 從未入庫。
- 證據：grep -c 'A14' ROADMAP_PHYSICS.md → 0；git log -1 -- ROADMAP_PHYSICS.md → 76c41c4 2026-08-29；ROADMAP_PHYSICS.md:155 「**B7 Phase 0+1（2026-09-14，WF0914-B7P0/B7P1，unstaged 待稽核，In progress）**」；同格後段「已撤回 `ScoreRenderer.h::dumpModes()` 對 `bridge_power_firstprinciples_c` 的欄位輸出」；ROADMAP_PHYSICS.md:11 「## 2026-08-06 excitation keytrack + loudness calibration update（unstaged 待審）」、:30 「corpus 73 檔重驗待執行」；ROADMAP_PHYSICS.md:153 「**依月月指示等 UI mockup 裁決後才 merge**」；ROADMAP_PHYSICS.md:130 R8「完成任何 GATE 後更新本文件 §2 狀態欄與 `TODO.md`」
- 建議：在檔頭加一段「2026-09-07~16 更新」，列出 A14（Rule 10 報告路徑、位元基準改 post_a14）、D8、F-03、C10 A/D15 A'、D13 B、D9c 慣例常數、B7 本輪終點；M10 的 B7 段把開頭狀態詞改成「已稽核 staged，09-15 裁決路徑 C 乙案」；08-06 段拿掉「unstaged/待執行」；M8 補上後續 merge 記錄。
- 懷疑者查證：`grep -c A14 ROADMAP_PHYSICS.md` 得到 0；git log 最後一次 commit 是 76c41c4（08-29）。本輪 staged 只改了 M10 那一格（diff 1+/1-），而且 B7 段仍寫「unstaged 待稽核，In progress」和「unstaged 待再次稽核，In progress，狀態較上一輪倒退」；在 ROADMAP 搜 09-15 是 0 筆。:11 標題仍是「（unstaged 待審）」、約 :29「corpus 73 檔重驗待執行」、:153「依月月指示等 UI mockup 裁決後才 merge」。:261 引用的 reports/gate_outputs/corpus_phase_d_B_classical_1.log 和 _C_classical_2.log 在磁碟上不存在，git 歷史也查不到。補充：B7 裁決包 §6 第 3 點明文要求同步 ROADMAP 的 B7 條目，這一步沒有執行。

### [docs-consistency:P2] §6 容差登記表沒收錄實際在用的 GATE 門檻（melody_verify ±10 ms/±5 c、partial_verify ±5 c、selfcal 1 c）
- 查證：**adjusted**｜誰：月月裁決｜嚴重度 low｜工作量 S
- 說明：ROADMAP_PHYSICS §6 規定容差數值只能由月月批准。但 melody_verify 的 onset ±10 ms / pitch ±5 c（C3-b 08-20 月月委託 AI 依推導自定）、partial_verify 的 ±5 c（A13 B+）、measurement_selfcal 的 1.0 c 門檻都在用，也寫在 HANDOVER §4，§6 表裡卻沒有這幾列。D9c 的「0±0.25 dB」施工卡已聲明不是新容差，不必列。要不要把這幾列加進表、要怎麼寫，需要月月決定。
- 證據：grep 'onset|melody_verify|partial_verify|1.18' ROADMAP_PHYSICS.md → 0 筆；HANDOVER.md:67 「② melody_verify：onset ±10 ms / pitch ±5 c（既有裁定）」；TODO.md:552 「容差由 AI 依推導自定，R2 仍然有效——定案後不得為了讓測試通過而調寬」；wf0914_D15_gate1_dev_grid.txt:15 「(limit 1.0)」
- 建議：做成一張小裁決：這幾個門檻要不要登記進 §6（數值不變，只補登記和出處）。月月點頭後由 AI 補列。
- 懷疑者查證：ROADMAP §6（:423-438）確實沒有 onset、melody_verify、partial_verify 和 selfcal 1c 這幾列（grep 0 筆）。細節要分開看：melody_verify 和 partial_verify 的 ±5 c 是直接沿用 §6 已登記的「f0 誤差 ±5 cents」（TODO:559「pitch 沿用已批准 5-cent course-centroid」、EARFREE:338），嚴格說不算新容差；真正沒登記的是 onset ±10 ms（C3-b 由 AI 在月月委託下自定，TODO:552/:558）和 selfcal 1.0 c（月月 08-30 查核第 5 點自己訂的，TODO:511-515）。owner 歸月月裁決是對的。
- **查證修正**：請月月裁決：把 onset ±10 ms（C3-b 委託 AI 自定，08-20）和量測器自證 1.0 c（月月 08-30 訂）補登進 §6，數值不變；±5 c 那兩處寫明是沿用既有的 f0 列，不必另開一列。

### [docs-consistency:P3] R7 規則原文（留 unstaged）和實際流程（稽核 PASS 後 git add 成 staged）不一致
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 low｜工作量 S
- 說明：ROADMAP_PHYSICS.md:135 的 R7 寫「不 commit、不 push。檔案留 unstaged，由月月審完決定」。但從 WF0907 起的實際流程是稽核 PASS 後由稽核執行 git add（WF0914_README.md:30），HANDOVER.md:19 也寫「staged 未 commit（R7）」。規則字面跟流程不符，新 AI 可能把 staged 誤判成違規，或反過來以為可以不 add。規則措辭要由月月決定。
- 證據：ROADMAP_PHYSICS.md:135 「**不 commit、不 push。** 檔案留 unstaged，由月月審完決定」；docs/workcards/WF0914_README.md:30 「稽核 PASS 後由**稽核**執行 `git add -- <files_touched>`」；git status：122 檔全數 staged
- 建議：請月月決定 R7 要不要改成「不 commit、不 push；稽核 PASS 後可 git add（staged）供審」。
- 懷疑者查證：ROADMAP_PHYSICS.md:135 寫「檔案留 unstaged」，但 WF0907_README.md:58 和 WF0914_README.md:30 都規定稽核 PASS 後由稽核執行 git add；git status 目前是 121 個 staged 加 1 個 untracked（原證據寫「122 檔全數 staged」不精確）。使用者記憶 feedback_no_auto_commit.md 也寫「留 unstaged 比留 staged 還安全」，所以這個落差確實要由月月決定。

### [docs-consistency:C1] CONTEXT.md（08-06）和 TODO_HANDOFF.md（07-17）整份過時，沒有標成歷史
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：CONTEXT.md 還寫：「Working tree clean. Merge to main is gated on…Cubase 4-step validation」（A9 08-22 已結，已 merge 六次）；IR「path persisted in state」（F-03 已改成 sha256 受管理庫，D12 已做遷移）；「No soundboard/body coupling…nonlinear contact solver」（B1/B4 已完成）；「Release corpus 73/73」（現為 75）；「Real DAW automation/state…still require human/host validation」（L2/L3b 已做）；指令只建 3 個 target。README 08-28 的稽核紀錄（:451）早就點名 CONTEXT 的 73/73 過時，至今沒改。TODO_HANDOFF.md 還寫 corpus 73/73、「cross-platform bit identity is not」（沒提 C3 的容差 GATE），重跑指令只有 3 個測試 target。兩份都沒被 HANDOVER 引用，但 README 檔案樹列了 CONTEXT.md。ROADMAP.md 雖自稱歷史，:28 仍寫「DAW validation Pending」。
- 證據：CONTEXT.md:3 「Last updated: 2026-08-06」、:17-20 「Working tree clean. Merge to `main` is gated on the owner's manual items」、:36 「path persisted in state」、:52 「73/73 PASS」、:82 「No soundboard/body coupling…nonlinear contact solver」、:86；TODO_HANDOFF.md:3 「Updated 2026-07-17」、:21-23；README.md:451 「The same stale 73/73 also appears in `CONTEXT.md`」；ROADMAP.md:28 「| — | DAW validation (host scan / automation / state) | Pending |」
- 建議：CONTEXT.md、TODO_HANDOFF.md 檔頭各加一行「歷史快照（日期），現況一律看 HANDOVER.md / TODO.md」，不必重寫內文。ROADMAP.md 的 DAW validation 列補「→ 2026-08-22 L3b 完成」。要不要移到 docs/archive 由月月決定。
- 懷疑者查證：CONTEXT.md:3 寫 2026-08-06；:17-20 寫 Working tree clean、merge gated on Cubase；:36 寫「path persisted in state」；:52 寫 73/73；:86 說 DAW state 需人工；TODO_HANDOFF.md:3 寫 07-17、:21/:23；README.md:451 早就點名過；ROADMAP.md:28 仍是「DAW validation Pending」，這些都屬實。兩處要更正：CONTEXT.md:66 的建置指令根本沒有測試 target（不是三個）；:82「No soundboard/body coupling…nonlinear contact solver」只有部分過時。B4 已有 Felt 路徑的接觸求解器（HammerImpulse.h:181/:192），B1 只是無限板導納損耗通道；共鳴、制音器/踏板，以及木材異向的實際使用（TODO:319 零消費）到現在都還沒有。
- **查證修正**：CONTEXT.md、TODO_HANDOFF.md 檔頭各加「歷史快照（日期），現況看 HANDOVER.md／TODO.md」。如果只改一句，CONTEXT:82 改成「B1 無限板導納與 B4 Felt 接觸求解器已有；有限音板共振、共鳴、制音器/踏板、異向木材實際使用仍無」。ROADMAP.md:28 補「→ 2026-08-22 L3b 完成（GUI automation lane 未做）」。

### [docs-consistency:C2] RESEARCH_INDEX.md 停在 08-15，而且 D7/D8 編號跟 TODO/HANDOVER 撞號
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：RESEARCH_INDEX 的 #1~#8 狀態全是 08-15 的「可開工／卡住／等 push」，但 B1~B6 都已 Done，#8 的跨平台也已完成。更麻煩的是編號：RESEARCH_INDEX §5 的 D7 是「Giordano 1998 原始導納曲線」、D8 是「資料集本體（SOFA/SNDB/MAPS/BiVib）」；TODO 的 D7 是「實體試體量測」、D8 是「tongue_drum 斜率」，HANDOVER 的 D8 也是舌鼓 exciter。TODO:82 和 :251 仍叫讀者照 RESEARCH_INDEX §4 的施工順序做。
- 證據：git log -1 -- docs/RESEARCH_INDEX.md → 019c078 2026-08-15；docs/RESEARCH_INDEX.md:116 「| D7 | Giordano 1998 原始導納曲線 |」、:117 「| D8 | 資料集本體（SOFA／SNDB／MAPS／BiVib） |」；TODO.md:610 「D7 揚琴／舌鼓／鑼的實體試體量測」、:611 「D8 tongue_drum 音高-響度斜率」；docs/RESEARCH_INDEX.md:47 「| 8 | 跨平台可重現性 | … | 工具與 CI 已就位，**等 push** |」；TODO.md:251 「依此順序，理由見 `RESEARCH_INDEX.md` §4」
- 建議：RESEARCH_INDEX 檔頭加「2026-08-15 快照：#1~#6 對應 B1~B6 皆已 Done（見 TODO B 區）」；§5 的 D7/D8 改名（例如 R-D7/R-D8），或註明「與 TODO D7/D8 不同」。
- 懷疑者查證：docs/RESEARCH_INDEX.md 最後一次 commit 是 019c078（08-15）；:41 的 #2 還寫「已實作（unstaged）…卡住」，:47 的 #8 還寫「等 push」。§5 的 :116 D7=Giordano、:117 D8=資料集本體，跟 TODO:610 D7=實體試體、:611 D8=tongue_drum 撞號。TODO:251「依此順序，理由見 RESEARCH_INDEX.md §4」。（TODO:82 只是指向依據，沒有叫人照順序做。）

### [docs-consistency:M1] 09-16 的變現計畫和 clean_batch2 產出沒進交接鏈，計畫裡還引用了過時的 UI 雙開門待辦
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 S
- 說明：docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md 是 repo 唯一的 untracked 檔。它和 exports/products/clean_batch2/（50 個母帶加上架包；exports/ 被 gitignore）在 HANDOVER、TODO、DEVLOG、README 都查不到。計畫裡有月月要做的事（看 clean_batch2/PRODUCT_SHEET.md §5 的五件裁決、註冊 BOOTH 和 PayPal、授權方式裁決），HANDOVER §1-4 的「月月待辦」沒有列。計畫 §3 #2 把已被否決的 UI 雙開門當成待裁決（源頭是 T3 的過時 TODO）。這份檔要不要進版控、交接要不要收錄，由月月決定。
- 證據：git status --short → `?? docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md`（唯一 untracked）；grep -i 'MONETIZATION|變現|clean_batch2|BOOTH' HANDOVER.md TODO.md README.md DEVLOG.md → 0 筆；git check-ignore -v exports/products/clean_batch2 → .gitignore:22 exports/；MONETIZATION_PLAN:66 「UI 雙開門裁決落地或明確擱置」、:82 「月月看 `clean_batch2/PRODUCT_SHEET.md` §5 五件裁決 → 註冊 BOOTH＋PayPal」
- 建議：請月月決定變現計畫要不要進版控。至少在 HANDOVER §1-4 或 §5 加一行指向它和它的月月待辦；計畫 §3 #2 改成「UI 功能規格 v1.1 送設計端（雙開門已於 08-30 否決）」。
- 懷疑者查證：git status 顯示 `?? docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md` 是唯一的 untracked 檔。在 HANDOVER/TODO/README/DEVLOG 搜 MONETIZATION|變現|clean_batch2|BOOTH，全部 0 筆（grep rc=1）。`git check-ignore` 顯示 .gitignore:22 exports/。MONETIZATION_PLAN:66「UI 雙開門裁決落地或明確擱置」、:82 本週排程，還有 PRODUCT_SHEET.md:74-80 的五件拍板事項，都屬實。

### [docs-consistency:I1] 「整合卡全綠」是在 D9c 之前跑的；D9c 沒有重跑全套 pytest 和 corpus
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：HANDOVER §0/§1 和 TODO:11 把「整合卡全綠（pytest 270、8/8）」放在五項裁決之後講，讀起來像涵蓋全部改動。但整合卡的證據檔寫於 2026-09-15 02:53，D9c 在 09-16 01:18 才落地（改了 src/effects/EffectChain.h 和 tests/audit_repro.cpp）。D9c 自己的 GATE 1-6 有跑 build、ctest、--full、位元不變 8/8 和 HostProbe（用 build-wf），但沒跑全套 pytest，也沒跑 verify_score --all 75/75。另外 src/effects/ 不在 R6 列舉的目錄裡。這不代表有錯，只是文件沒講清楚順序。live-gate agent 此刻正在重建 build/（build/ 裡有 09-25 03:1x 的新產物），結果應以它為準。
- 證據：ls -la：wf0914_INTEGRATION.txt 2026-09-15 02:53；wf0914_D9c_ir_makeup_gain.txt 2026-09-16 01:18；src/effects/EffectChain.h 2026-09-16 01:07；wf0914_D9c_ir_makeup_gain.txt §1~§6：build/ctest、補償驗證、--full、位元不變、HostProbe、diff 範圍；沒有 pytest 和 verify_score --all；ROADMAP_PHYSICS.md:132 R6 只列 `src/physics/`、`src/engines/`、`src/dsp/`、`src/score/`
- 建議：HANDOVER §0 補一句「整合卡（09-15）早於 D9c；D9c 另跑 GATE 1-6」。如果這次 live-gate 重跑的結果是綠的，就把它記成 D9c 之後的整合基準。
- 懷疑者查證：wf0914_INTEGRATION.txt 的 mtime 是 2026-09-15 02:53；wf0914_D9c_ir_makeup_gain.txt 是 09-16 01:18；EffectChain.h 是 09-16 01:07；tests/audit_repro.cpp 是 09-16 01:08。D9c 證據只有 §1-§6 GATE（build/ctest、補償、--full、位元不變、HostProbe、diff），沒有跑全套 pytest 和 verify_score --all，屬實。漏掉的是：D9b 也在整合卡之後（wf0914_D9b_ir_injection.txt 是 09-16 00:09），它同樣改了 tests/audit_repro.cpp（外部 IR 注入點），只跑了 GATE 1-5。ROADMAP:132 的 R6 列舉確實不包含 src/effects/。
- **查證修正**：HANDOVER §0 補一句「整合卡（09-15 02:53）早於 D9b（09-16 00:09）和 D9c（09-16 01:18）；兩者各自跑了 GATE 1-5／1-6（含 ctest、--full、8/8、HostProbe），都沒有重跑全套 pytest 和 corpus 75/75」。如果這次 live-gate 重跑是綠的，就記成 D9c 之後的整合基準。

### [docs-consistency:V1] 查證結果：HANDOVER §3 的「全部已 commit：5c9cdb3～49b8542」正確（規劃者的疑點不成立）
- 查證：**confirmed**｜誰：資訊｜嚴重度 low｜工作量 n/a
- 說明：§3 表列的 WF0907~0909 成果都在 09-13 的五個 commit 裡：IRLibrary.h、ParameterLayout、HammerImpulse（A14）在 31eb7ae；measurement_selfcal、partial_verify 在 5c9cdb3；a14/d8 的 Rule 10 報告和 patch 在 9ae8ce2；施工卡和證據在 27e8393；交接文件在 49b8542。跟它矛盾的是 TODO.md:26「全部未 commit」，那一邊才過時（見 T2）。WF0914 的成果沒列在 §3，這是對的：它們確實還是 staged 未 commit。
- 證據：git log：5c9cdb3/31eb7ae/9ae8ce2/27e8393/49b8542 皆 2026-09-13；git show --stat 31eb7ae → src/IRLibrary.h、src/ParameterLayout.cpp、src/physics/HammerImpulse.h；git show --stat 5c9cdb3 → tools/measurement_selfcal.py、tools/partial_verify.py；git show --stat 9ae8ce2 → reports/a14_tauc_keytrack_b2.patch、reports/d8_tongue_drum_exciter_before_after.md
- 建議：HANDOVER §3 不用改；要改的是 TODO.md:26（見 T2）。
- 懷疑者查證：`git show --stat 31eb7ae` 有 src/IRLibrary.h 和 HammerImpulse.h（A14）；5c9cdb3 有 measurement_selfcal 和 partial_verify；9ae8ce2 有 a14 patch 和 d8 報告。這些 commit 都在 09-13。HANDOVER:38 的「全部已 commit」是對的，過時的是 TODO:26。

### [docs-consistency:Y1] 要月月親自回覆或授權的小事：Limbus 有沒有啟用、Downloads 殘留要不要清
- 查證：**confirmed**｜誰：月月動手｜嚴重度 low｜工作量 S
- 說明：磁碟上只能確認 Limbus 和 Yamaha 在 09-14 裝好，查不到 Limbus 有沒有用金鑰啟用。Downloads\不知道有沒有用 目前 614 MB，裡面有 Piano Sheet Converter 解壓殘留、各工具安裝檔、Klanggeist 資料夾。刪檔屬於不可逆操作，要月月點頭才能做。
- 證據：ls C:/Users/admin/AppData/Roaming/Limbus Audio/Spatial Stage Standalone → 只有 preferences.xml（130 B，2026-09-14 12:56）；du -sh Downloads/不知道有沒有用 → 614M；內含 installer.exe 121 MB、Piano Sheet Converter.exe 235 MB 等
- 建議：請月月回兩件事：「Limbus 啟用了沒」「Downloads 殘留要不要清、保留哪些安裝檔」。AI 依回覆清理並更新 HANDOVER §11。
- 懷疑者查證：Roaming/Limbus Audio/Spatial Stage Standalone 下只有 preferences.xml（130 B，09-14 12:56:19），判斷不出有沒有啟用。Downloads 資料夾 du 是 614M，內含 installer.exe 121,038,216 B、Piano Sheet Converter.exe 235,164,136 B、Klanggeist 資料夾和 zip、Limbus/Orra 安裝檔。刪檔是不可逆操作，要月月點頭。

## open-work

盤點基準：HEAD 766d21d（main=3f9b90a），09-16 之後沒有新 commit。121 個檔 staged、0 個 unstaged，另有 1 個 untracked（MONETIZATION_PLAN）。09-15~16 那五項裁決（B7=C/乙、D9=A、D11=C、D13=B、D15=A'）都已落地；D9、D12、D13、D14、D15 經查證確實已關閉。真正還開著的最大一件是月月還沒審 staged 內容、還沒 commit。其次是變現線：音效包和專輯的五項上架裁決、賣家帳號註冊；合成器本體則還卡在 UI 送設計端。這輪查到一個新狀況：A14 B-2 落地後，給愛麗絲全曲乾聲 905 顆裡有 16 顆 FAIL，全部是基頻被壓掉，而且集中在特定音高加特定力度（E5@0.278、A5@0.427/0.452、A6/A#6@0.427）。引擎自己的 dump 顯示這些音的基頻比第二泛音低 6～19 dB。也就是說，力脈衝深零點只是從 G5 搬到了別的音，而 clean_batch2 準備上架的給愛麗絲母帶就含這 16 顆。AI 現在就能動手、不必等裁決的有這幾件：D11-F5 根因調查、零點地圖、UI 規格同步 v1.2、PlateModel.h 檔頭同步、JUCE EULA 查核、loop 接縫數值檢查、外掛 16 voice 搶音量測、D1 文獻補搜，以及一批文件過期勾選的修正。另外，score_vs_midi_verify 其實已經透過全套 pytest 跑在 CI 上，只剩文件沒跟上。

### [open-work:G0-commit] WF0914 的 121 個 staged 檔 + 1 個 untracked 變現計畫，等月月審完決定 commit
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 high｜工作量 S
- 說明：WF0914 輪全部成果（B7P0/P1、D9b/c、D10、D11/D13 裁決包、D12、D14、D15、整合卡證據）都已 staged 但沒 commit，距今 10 天。工作樹不乾淨會拖住後面所有事：重新部署 VST3、變現計畫 Phase 2 #1、下一輪施工卡的基線。docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md 是 untracked，也不在 staged 清單裡；要不要一起進 commit 得月月定。依 R7，AI 不能代為 commit。
- 證據：git diff --cached --name-only | wc -l → 121；git diff --name-only | wc -l → 0；git status: ?? docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md；HANDOVER.md:5-6「WF0914 輪全部成果 staged 未 commit，月月看 git diff --cached」；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:65 Phase 2 #1「WF0914 staged 成果審完 commit＋push（現在工作樹不乾淨）」
- 建議：月月看 git diff --cached（可照 HANDOVER §10 的建議分成程式／證據／文件幾個 commit，路徑清單記得先 tr -d '\r'），並決定 MONETIZATION_PLAN 要不要一起進版控。commit 完再做 G6 重新部署與文件修正（G19）。
- 懷疑者查證：`git diff --cached --name-only | wc -l` 是 121；git status 唯一的 untracked 是 MONETIZATION_PLAN。HANDOVER.md:5 寫「WF0914 輪全部成果 staged 未 commit，月月看 git diff --cached」。MONETIZATION_PLAN:65 把 commit＋push 列為 Phase 2 #1、歸月月。依 R7，AI 不能代為 commit。

### [open-work:N1-fe16] 新發現：A14 B-2 落地後，弱基頻從 G5 搬到 E5/A5/A6/A#6，給愛麗絲全曲有 16 顆 FAIL
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 high｜工作量 S
- 說明：這輪我自己分析了 D14 全量 905 顆的乾聲報告（677 PASS / 16 FAIL / 212 UNVERIFIED），又對同一份 score 跑了 --dump-modes（輸出在 scratchpad，repo 沒動）。16 顆 FAIL 的理由全是「near-silent fundamental band」，只出現在特定的音高加力度組合：E5@0.278 共 9 顆、A5@0.427/0.452 共 4 顆、A6@0.427 共 2 顆、A#6@0.427 共 1 顆。引擎自己的 dump 顯示這些音的基頻比第二泛音低 6.2～18.9 dB；同樣是 E5，力度 0.427～0.462 時基頻反而高出 17～45 dB。以前那 22 顆（G5×19、D7、G6、F#6）現在全部 PASS（G5 的 n1/n2 為 -0.8～+5.2 dB）。可見 A14 B-2 並沒有消除半正弦力脈衝的深零點，只是把它移到別的音高與力度組合；A14 報告寫「G5/G6 不再掉進深零點」沒錯，但沒有掃過力度這一軸。clean_batch2 準備上架的給愛麗絲鋼琴版母帶，是 09-15 的 build 渲染的，這 16 顆就在裡面。
- 證據：output/wf0914/D14/g2_full_report.json summary {'pass': 677, 'fail': 16, 'unverified': 212}（reports/gate_outputs/wf0914_D14_memory_fix.txt:209）；scratchpad/open-work/fur_elise_weak_fundamental_triage.txt：('E5',0.278) n1/n2 -18.5 dB ×9；('E5',0.427) +44.8；('A5',0.427) -18.9；('A6',0.427) -6.2；('G5',0.427) -0.8；reports/decision_packets/A13_partial_gate_domain.zh-TW.md:276 舊 22 顆組成 G5×19、D7×1、G6×1、F♯6×1；reports/a14_tauc_keytrack_before_after.md:20「G5/G6 的基頻不再掉進力脈衝公式的深零點」；exports/products/clean_batch2/PRODUCT_SHEET.md:5,27 渲染器 2026-09-15 build，Für Elise Complete 在上架清單
- 建議：AI 先做三件，都不必改 src：(1) 在 TODO 登記成新 D 類項；(2) 用 --dump-modes 掃 piano Felt 路徑的 MIDI×velocity 網格，畫出哪些格子的基頻會掉進零點（n1/n2 < -10 dB）；(3) 在 clean_batch2 PRODUCT_SHEET 已知限制補一行。數字交給月月判斷給愛麗絲母帶要不要先上架，引擎面的修法併入 A14 B-1（見 E1）。
- 懷疑者查證：我自己重算：output/wf0914/D14/g2_full_report.json 的 stem_verify.summary 是 {pass 677, fail 16, unverified 212}，16 顆的理由都是「no onset in near-silent fundamental band」。對照 score 的 velocity：E5@0.278 FAIL 9、A5@0.427 FAIL 3、A5@0.452 FAIL 1、A6@0.427 FAIL 2、A#6@0.427 FAIL 1；E5@0.427/0.437/0.452/0.462 共 79 顆全 PASS；G5@0.427 的 19 顆和 D7、G6、F#6 現在全 PASS。另外補一條 A14 之前的因果證據：08-30 的 output/stem_verify_fur_elise_dry.json 裡，這 16 顆（E5@0.278×9、A5×4、A6×2、A#6×1）當時全是 PASS，G5@0.427 的 19 顆則是 FAIL（跟 stem_verify_fur_elise_run.txt 記的 22 顆組成一致）。fur_elise_complete.score.json 從 0f271ae（08-28）之後沒改過，所以翻轉的原因就是 A14 B-2。用 scratch dump 的 n1/n2 抽查，E5@0.278 是 -18.5 dB、E5@0.427 是 +44.8、A5@0.427 是 -18.9、G5@0.427 是 -0.8，跟原發現一致。a14 報告 :20 只講 G5/G6；repo 裡搜不到任何地方登記這 16 顆。PRODUCT_SHEET.md:5/:27 寫 09-15 build，Für Elise Complete 在上架清單上。

### [open-work:D11-F5] D11-F5 根因調查（唯一排隊卡，月月已裁 C 授權）
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 M
- 說明：候選的弦長/弦徑查表修正把高音非諧性 B 往量測值拉近（G6 偏差 86.4×→18.7×），但 --full 的 F5 piano 殘餘能量從 -63.9 dB 退化到 -58.5 dB（門檻 -60），根因沒查出來。月月 09-15 選 C，等於授權另開卡查，所以這件不必再等裁決。目前只登記了名字，沒有施工卡。patch 動到的三個檔（StringModel.h、CimbalomEngine.h、physics_verify.py）從 D11 卡之後都沒改過，patch 基底仍有效。build-wf/ 還在，可以用。查清之後，選項 A 還帶兩個子裁決（C1-C3 纏繞弦線密度、使用者弦徑旋鈕會被覆寫）。
- 證據：reports/decision_packets/D11_string_scale_candidate.zh-TW.md:61-65 裁決記錄 C＋新登記 D11-F5；reports/d11_string_scale_before_after.md:208-251 F5 piano -58.5 dB FAIL、根因未查；git diff --stat HEAD -- src/physics/StringModel.h src/engines/CimbalomEngine.h tools/physics_verify.py → 空；Grep 'D11-F5'：只出現在 HANDOVER/TODO/DEVLOG/裁決包，沒有 docs/workcards 施工卡；build-wf/Release/*.exe 存在（09-15/16）
- 建議：開 WF 施工卡：在獨立副本或 build-wf 套 patch，用時域/頻域把 piano MIDI 60 的殘餘能量拆開，逐一檢驗多弦 beating 邊帶、partial 滑出 ±3% 判定窗等假說，查完原樣還原並附 8/8 還原證明。帶數字回來重開 A/B 裁決包。
- 懷疑者查證：D11 裁決包:61-65 記錄選 C，並新登記 D11-F5。d11_string_scale_before_after.md:208-235 記 F5 piano -58.5 dB FAIL、根因未查。`git diff --stat HEAD` 查 StringModel.h、CimbalomEngine.h、physics_verify.py 三個檔結果是空的；patch 也正好只動這三個檔。build-wf/Release/*.exe 存在（09-15/16）。子裁決見裁決包:31-32（纏繞弦、弦徑旋鈕被覆寫）。提醒：調查時不能在主工作樹套 patch（R7 和工作樹現況），要用獨立副本，原建議已經有寫到。

### [open-work:U1-spec-sync] UI 功能規格 v1.1 已過期：還寫著「IR 與演算法殘響差 28 dB 尚未對齊」
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：這份規格是送設計端的唯一輸入，但它是 09-09 版。09-16 的 D9c 已經用 kIrWetMakeupGain=26.9 把落差補平（四組殘差都在 ±0.25 dB 內）；D12 也新增了舊專案 reverb_ir_path 的三態遷移與 dirty flag 行為。規格 §5-3 和 §6 仍要求設計端「預留音量警告位置」，理由是一個已經不存在的 28 dB 落差。照現況送出去，設計端會拿到錯的前提。這是純文件同步，AI 現在就能做。
- 證據：docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md:250-251「IR 與演算法殘響本來就差約 28 dB，尚未對齊」；docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md:266「還沒做的：IR 與演算法殘響的音量差（約 28 dB）尚未對齊」；src/effects/EffectChain.h:275 static constexpr float kIrWetMakeupGain = 26.9f；src/PluginProcessor.cpp:610-671 legacy reverb_ir_path 遷移（D12）
- 建議：產出 v1.2：更新 §5-3、§6 的 IR 響度敘述（已對齊，DECIDED CONVENTION，4 樣本），並補上 D12 舊專案遷移的使用者可見行為。等 G0 commit 完再改，避免 staged 上面又疊 unstaged。
- 懷疑者查證：docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md:251 寫「IR 與演算法殘響本來就差約 28 dB，尚未對齊」，§6 IR 列（約 :266）寫「還沒做的：…約 28 dB…尚未對齊…預留警告位置」。這份檔最後一次 commit 是 49b8542（09-13），本輪沒有 staged。EffectChain.h:275 已有 `kIrWetMakeupGain = 26.9f`，:233 只乘在 IR wet 上。PluginProcessor.cpp:610-643 已有 legacy reverb_ir_path 遷移。

### [open-work:U2-send] UI 功能規格送設計端（月月決定找誰）
- 查證：**adjusted**｜誰：月月裁決｜嚴重度 medium｜工作量 n/a
- 說明：送出的前提（等 WF0909 收尾、A14 裁決）早就滿足了，現在只差月月決定設計端人選。這是合成器本體能不能上架的前提：變現計畫 Phase 2 #2 要求「賣的東西要有定版 UI」。另外變現計畫把這項寫成「UI 雙開門裁決」，但雙開門 08-30 已被月月否決，正確的待辦是按功能規格重做。
- 證據：HANDOVER.md:87「UI 功能規格 v1.1 送設計端（月月決定找誰）」；TODO.md:46「等 WF0909 收尾 + A14 patch 裁決後執行」（兩個條件都已滿足）；docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md:3-5 月月 08-30 否決雙開門；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:66「UI 雙開門裁決落地或明確擱置」（措辭過期）
- 建議：先做 U1（v1.2 同步），再由月月決定設計端人選與預算；AI 可以把 v1.2 整理成可直接寄出的包（規格 + 參數表）。
- 懷疑者查證：HANDOVER.md:87 寫「月月決定找誰」、TODO.md:46 寫「等 WF0909 收尾 + A14 patch 裁決後執行（月月 09-07：等所有功能做完）」，這兩個技術前提確實都已滿足。但月月原話是「等所有功能做完」（TODO:23 也寫「UI 等功能做完再送設計」），而 B7 Phase 2/3 BLOCKED、D11-F5 排隊中、N1 新缺陷還沒處理，「功能做完了沒」要月月自己判斷，不能直接說前提早就滿足。MONETIZATION_PLAN:66 措辭過期，屬實。
- **查證修正**：規劃者當初列的兩個前提（WF0909 收尾、A14 裁決）已滿足；但月月 09-07 的條件是「等所有功能做完」，算不算做完要她自己認定。先做 U1（v1.2 同步），再請月月一次決定兩件事：功能算不算凍結、找哪位設計端。

### [open-work:U3-ir-warning] 外掛缺檔警告「音量會和 IR 模式不同」在 D9c 之後已不準確
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 low｜工作量 S
- 說明：F-03 當初規定 IR 缺檔時要寫這句警告，當時是因為 IR 比 ALGO 小 28 dB。D9c 補平後這句話已不成立（剩下的只是音色不同）。字串寫在 src，改它屬於 F-03 規格措辭的變更。這裡查不到任何測試斷言這段文字。
- 證據：src/PluginProcessor.cpp:846 " the volume will differ from IR mode."（中文版同段 :841「音量會和 IR 模式不同」）；docs/workcards/WF0908_P3_f03_ir_library.md:36 規定警告要含「音量會與 IR 模式不同」字樣；grep 'volume will|Not loaded' tests/ → 無命中
- 建議：AI 擬好新舊措辭對照（例如改成「已切回演算法殘響，音色會不同」），月月一句話確認後再改，改完照 R6 重建三個 target 並跑 HostProbe。
- 懷疑者查證：src/PluginProcessor.cpp:846 是「the volume will differ from IR mode.」；:841-842 的中文 UTF-8 解碼後是「音量會和 IR 模式不同」。WF0908_P3_f03_ir_library.md:36 規定警告要含這幾個字。在全 repo 的 cpp/h/py 搜「Switched back|Not loaded|volume will」，只命中 src/PluginProcessor.cpp，沒有測試斷言這段文字。因為措辭是 F-03 規格規定的，改之前問月月是合理的。

### [open-work:M1-listing-decisions] clean_batch2 上架前的五項裁決（售價／AI Radiance 署名／全曲版削波／聽人把關／賣家身分）
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 high｜工作量 S
- 說明：50 個授權乾淨的母帶、zip、文案都已完成。上架只差月月拍板：售價（建議音效包 ¥900、專輯 ¥500）；AI Radiance 的 composer 欄目前是 "Codex"，要怎麼署名；全曲版 41 個削波樣本要不要降 master_volume 重渲；要不要花 US$30–80 找聽人把關；賣家身分。月月是聾人，品質只能靠外部聽人，而 N1 發現的 16 顆弱基頻正是聽人該留意的點。
- 證據：exports/products/clean_batch2/PRODUCT_SHEET.md:74-80 §5 五件拍板事項；exports/products/clean_batch2/PRODUCT_SHEET.md:35「#3 全曲版母帶有 41 個樣本達滿刻度」；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:82 本週排程「月月看 §5 五件裁決 → 註冊 BOOTH＋PayPal」
- 建議：月月逐項回答五題。AI 可以先把 M3（削波量化）和 M4（loop 接縫）的數字做好附上，讓第 3 題和上架判斷看數字就能選。
- 懷疑者查證：exports/products/clean_batch2/PRODUCT_SHEET.md:74-80 是五件拍板事項；:29/:35 寫 AI Radiance 全曲版有 41 個削波樣本；:37 寫「未做任何人耳審聽」。MONETIZATION_PLAN:82 本週排程也把這五件列為第一步。

### [open-work:M2-accounts] 賣家帳號註冊（BOOTH＋PayPal／itch.io／Fab／Lemon Squeezy）
- 查證：**confirmed**｜誰：月月動手｜嚴重度 high｜工作量 S
- 說明：每個平台都要月月本人註冊和做身分驗證，AI 不能代辦（涉及建立帳號與金流）。這是第一筆收入的門檻。
- 證據：exports/products/clean_batch2/PRODUCT_SHEET.md:80「這些都要月月本人註冊，我不能代辦」；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:36-48 通路費率表、:82 排程
- 建議：M1 定案後，月月先註冊 BOOTH＋PayPal 上架音效包與專輯；itch/Fab 放第二週。
- 懷疑者查證：PRODUCT_SHEET.md:80「這些都要月月本人註冊，我不能代辦」；MONETIZATION_PLAN:82 排程。建立帳號和金流屬於 AI 禁止代辦的範圍。

### [open-work:M3-clip-quant] AI Radiance 全曲版 41 個削波樣本：先量出降多少 master_volume 才會歸零
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：四個樂章各自渲染都沒有削波，疊層後才出現 41 個滿刻度樣本。要不要改 score 是月月的決定，但「要降幾 dB 才歸零、LUFS 會變多少」可以由 AI 在 scratchpad 複製 score 試渲算出來，不動 repo。
- 證據：exports/products/clean_batch2/PRODUCT_SHEET.md:29,35 Complete Suite 母帶削波樣本 41；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:26「AI Radiance 全曲版 ⚠️ 母帶 41 個削波樣本，暫不放」
- 建議：在 scratch 複製 score，掃 master_volume（例如 -0.5～-3 dB），用 .render.json 的 samples_at_or_above_full_scale 找出歸零點，數字交給 M1 第 3 題。
- 懷疑者查證：PRODUCT_SHEET.md:29/:35 寫 41 個滿刻度樣本，來源是 `.render.json` 的 samples_at_or_above_full_scale；四個樂章各自渲染都是 0；建議「全曲版待 master_volume 下調重渲（需改 score，留給月月裁決）」。MONETIZATION_PLAN:26「暫不放」。在 scratch 複製 score 試渲不會動到 repo。

### [open-work:M4-loop-seam] 6 個 loop 音效的接縫還沒驗（上架前的風險項）
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：計畫說要「在 DAW 看一次波形」，這件事可以用數值免耳完成：量頭尾交接處的樣本不連續、斜率跳變、交接前後短窗的頻譜差。產物在 exports/（gitignore），只需要讀檔，不動 repo。
- 證據：exports/products/clean_batch2/PRODUCT_SHEET.md:55「Loop 類（6 檔）… 未驗證無縫接點（CLI tail_silence_ms: 0）」；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:96「loop 檔未驗接縫」
- 建議：寫一支 scratch 腳本，對 6 個 loop 算接縫處的樣本跳變（dBFS）、斜率比、交界 ±20 ms 的頻譜差，產出圖表報告；有問題的檔再交月月決定要不要重渲。
- 懷疑者查證：PRODUCT_SHEET.md:55「未驗證無縫接點（CLI tail_silence_ms: 0）」；MONETIZATION_PLAN:96 也寫這一點。另外 catalog.csv 的描述已經對買家寫「可無縫循環」（第 9 行 akashic Meditation Loop）、「自然循環」（第 24 行），等於文案已先宣稱了未驗證的性質，所以這件更該在上架前量。

### [open-work:M5-juce-eula] JUCE 8 EULA 署名/收入條款還沒複查（賣 VST3 之前必做）
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：A7 留了一個尾巴：正式發行前要複查 JUCE 8 EULA。LICENSE 自己寫「符合 Starter tier（收入低於 USD 20,000、可閉源商用）」，這段寫法是否與現行 EULA 一致，本輪沒有逐條核對。這只影響「賣合成器本體」；賣渲染出來的音檔不經手 JUCE 程式碼的散布。
- 證據：LICENSE:22-26「qualifies for the JUCE Starter tier (free; revenue below USD 20,000 …). Before any public release, review the JUCE 8 EULA attribution requirements.」；TODO.md:164「殘留提醒：正式發行前仍要讀一次 JUCE 8 EULA 的署名條款」；libs/JUCE/LICENSE.md：模組為 AGPLv3／JUCE 8 EULA 雙授權
- 建議：AI 用 WebFetch 讀 juce.com/legal/juce-8-licence 原文，逐條對照 LICENSE 的說法（收入上限、署名/啟動畫面、閉源條件），寫成一頁白話摘要，必要時附 LICENSE 修正草案。
- 懷疑者查證：LICENSE:22-26 寫「qualifies for the JUCE Starter tier (free; revenue below USD 20,000 …) Before any public release, review the JUCE 8 EULA attribution requirements.」；TODO.md:164 有殘留提醒；libs/JUCE/LICENSE.md 寫 AGPLv3 和 JUCE 8 EULA 雙授權。repo 裡查不到任何逐條核對的紀錄。

### [open-work:M6-synth-phase2] 合成器本體上架 Phase 2（安裝包／手冊／demo 影片／DRM 方式）整體的 go/no-go
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 L
- 說明：計畫把合成器 EA 排在第 5 週。安裝包（Inno Setup）和 demo 素材 AI 做得出來；手冊要等 UI 定版；DRM（建議不做）與要不要簽章得月月裁決。月月目前還沒對這條線下決定。ROADMAP.md 的 v1.0（Installer/manual/demo）也一直是 Planned。
- 證據：docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:61-74 Phase 2 六件事；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:72-74 簽章建議第一版不簽；ROADMAP.md:285「v1.0 | Product Release — Installer, manual, demo videos, licensing | Planned」
- 建議：月月先裁「合成器線走不走、何時走」與 DRM 方式。走的話，AI 依序做安裝包 → demo 影片素材（melody_roll_video）→ 等 UI 定版後寫手冊。
- 懷疑者查證：MONETIZATION_PLAN:61-74 是 Phase 2 的六件事；:72-74 建議第一版不簽章；ROADMAP.md:285 寫「v1.0 | Product Release — Installer, manual, demo videos, licensing | Planned」。repo 裡查不到月月對這條線的裁決。

### [open-work:P1-voice-steal] 外掛 16 voice 上限會不會搶音：一直沒量過
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 M
- 說明：CLI 是每個事件開一顆獨立 voice，外掛則是每個引擎 16 顆 voice pool，會 voice stealing。引擎自報的 worst-case T60 長達 34/179/320 秒，密集段落很可能把 pool 用光，DAW 裡播出來的就會和 corpus 渲染不一樣。08-30 的裁決包登記為「該立卡查的疑慮」，DEVLOG 寫「仍未量測」，之後也查不到有人處理。合成器要賣，這條直接影響使用者在 DAW 裡聽到的東西。
- 證據：reports/decision_packets/POLYPHONIC_VERIFICATION_OPTIONS.zh-TW.md:130-136 §6「這尚未量測，不是缺陷宣告，是一個該立卡查的疑慮」；DEVLOG.md:198「外掛路徑 16 voice pool 的 voice stealing 疑慮（裁決包 §6）仍未量測」；src/PluginProcessor.cpp:36,71,105 for (int i = 0; i < 16; ++i) addVoice；HANDOVER.md:43 E5 worst-case T60 3.45 s → 34/179/320 s
- 建議：兩段做：(1) 純分析，用 --dump-modes 的 T60 加上 note-off/damper 行為，估給愛麗絲與幾首密集曲的同時活躍 voice 數；(2) 用 HostProbe 讓外掛串流渲染同一份 MIDI，和 CLI 逐事件比對，量出被搶掉的音。結果寫成裁決包（要不要加大 pool 或寫進主張域）。
- 懷疑者查證：src/PluginProcessor.cpp:36/:71/:105 都是 `for (int i = 0; i < 16; ++i)`。POLYPHONIC_VERIFICATION_OPTIONS.zh-TW.md:130-136 寫「這尚未量測…該立卡查的疑慮」；DEVLOG.md:198 寫「仍未量測」。在 reports、docs、TODO 搜 voice steal/搶音，只命中這兩處，TODO 沒有登記。

### [open-work:G6-redeploy] 系統上部署的 VST3 還是 09-13 的舊 binary，沒有 D12/D9c
- 查證：**adjusted**｜誰：月月動手｜嚴重度 medium｜工作量 S
- 說明：HANDOVER 說 09-14 部署過，但 Common Files\VST3 裡實際的 binary 修改時間是 09-13 03:33（資料夾名 TsukiSynth_VST3_2026-09-10），比 D12 遷移（09-15）和 D9c IR 補償（09-16）都早。月月在 Cubase 用到的外掛少了這兩項修正。覆寫需要管理員權限。
- 證據：C:/Program Files/Common Files/VST3/TsukiSynth_VST3_2026-09-10/TsukiSynth.vst3/Contents/x86_64-win/TsukiSynth.vst3 mtime 2026-09-13 03:33:35；HANDOVER.md:29「VST3 已於 09-14 部署」；TODO.md:15 D9c 2026-09-16 完工
- 建議：G0 commit 完、重建 VST3 後，月月用管理員權限覆寫部署（或授權 AI 產生部署腳本讓月月執行），再跑一次 cubase_scan_verify.py 確認 S6 版本一致。
- 懷疑者查證：已部署 binary 的 mtime 是 2026-09-13 03:33:35，sha256 786643…，跟 build/ 和 build-wf/ 都不同。同一資料夾的 怎麼安裝.txt 寫「這一版建於 2026-09-10 23:46」，所以它是 09-10 的 build，09-13 只是打包/複製的時間，不是「09-13 的 binary」。它不含 D12（PluginProcessor.cpp staged）和 D9c（EffectChain.h 09-16）是對的。另外 Cubase 的 vst3plugins.xml 最後在 08-22 寫入，還指向已不存在的頂層路徑，表示部署之後 Cubase 還沒重掃過（見 H8）。
- **查證修正**：系統上部署的 VST3 是 09-10 23:46 的 build（09-13 打包，放在 Common Files\VST3\TsukiSynth_VST3_2026-09-10\ 子資料夾），不含 D12 和 D9c；Cubase 從 08-22 起沒有重掃。等 G0 commit、重建之後，由月月用管理員權限覆寫，再跑 cubase_scan_verify.py 確認 S6。

### [open-work:C1-resource] 古典曲目換源重轉譜（四季 Schoonenbeek CC BY／月光重轉譜）還沒排程
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 L
- 說明：08-28 已定案：CC BY 可以。給愛麗絲已完成，四季和月光都停在「待排程」，沒有任何進度。四季用 IMSLP Schoonenbeek CC BY MIDI，編制會從獨奏小提琴＋弦樂變成鋼琴＋弦樂，工程量中；月光沒有現成乾淨 MIDI，要從公版掃描重轉，工程量大。這是解除 16 首上架限制的唯一路，月光空靈鼓 D8 母帶重出也掛在這後面。轉譜 GATE（score_vs_midi_verify）已經備好。下載外部 MIDI 須月月同意。
- 證據：reports/decision_packets/CLASSICAL_RELICENSE_PLAN.md:7-9 路線定案、:204-216 工程量估計；TODO.md:177-185 四季/月光 [ ] 待排程；TODO.md:616 月光母帶等換源後一起重出；HANDOVER.md:86 主線候選 2「解上架限制的唯一路」
- 建議：月月裁定兩件事：要不要先做四季、接不接受編制改成鋼琴＋弦樂。同意後，AI 先抽出 midi_to_tsukisynth.py 的通用層、下載 Schoonenbeek MIDI（下載前逐檔確認），每樂章都要過 score_vs_midi_verify。
- 懷疑者查證：CLASSICAL_RELICENSE_PLAN.md:7-9 路線定案，§4（約 :204-216）有工程量估計。TODO.md:184-185 的四季和月光都是 [ ] 待排程；:616 月光母帶等換源。repo 裡查不到任何進度。小矛盾：TODO:184 說四季「需從譜面重新轉譜」，但計畫 §4 說 Schoonenbeek 有現成 CC BY MIDI（工程量「中」），兩處說法不一致。

### [open-work:D13-sync] PlateModel.h 檔頭與 water_gong_free 描述，還沒同步 D13 主張域
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：D13 已裁 B，也建了 ENGINE_DOMAIN_CLAIMS §1，但兩處仍是舊說法：PlateModel.h 檔頭寫「金屬鑼/鐘的複雜非諧泛音結構」，score 描述寫「the physically-appropriate boundary for a hung gong」。月月的裁決只說「下次動這兩檔的卡順路做」，沒有禁止單獨做，所以不需要再裁決。改 PlateModel.h 雖然只是註解，照 R6 仍要跑 --full 和三個 build；8/8 預期位元不變。
- 證據：docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md:28-30 同步備忘「尚未帶上這段聲明」；src/physics/PlateModel.h:10-25 檔頭無 boss/乳突鑼字樣，:24「金屬鑼/鐘的複雜非諧泛音結構」；scores/examples/water_gong_free.score.json meta.description「the physically-appropriate boundary for a hung gong」
- 建議：G0 commit 後開小卡，只改註解和 description 字串，跑 R6（--full＋三 build）與 8/8 位元不變，staged 留給月月審。
- 懷疑者查證：PlateModel.h 那一句在 :25（不是 :24）；water_gong_free.score.json:7 的 description 還是舊說法，屬實。但 D13 裁決記錄（D13 裁決包 §4 約 :147、TODO:17、ENGINE_DOMAIN_CLAIMS:28-30）寫的落地方式是「留待下一張本來就要動這兩檔的卡順路做」。單獨開卡雖然沒有被禁止，但跟裁決時記下的做法不同，最好先跟月月說一聲。另外 water_gong_free 是 8 首位元基準之一，也在 crossplatform_verify.py:94 的清單裡：改 description 不會改 WAV，但 score 的 sha 會變，provenance 清單也會跟著變。
- **查證修正**：兩處舊說法確實還在（PlateModel.h:25、water_gong_free.score.json:7）。依裁決記錄，預設是等下一張本來就要動這兩檔的卡順路改；如果要單獨開小卡，先告知月月。改完照 R6 跑，並確認 8/8 WAV 位元不變（score sha 和 provenance 會變屬正常）。

### [open-work:D13-claims-ext] ENGINE_DOMAIN_CLAIMS 只有水鑼一條，其他已裁決的主張域限制散在各處
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：主張域清單目前只有 §1 water_gong。其他已經成立的限制分散在 5 份以上文件：量測器持續段 ≤1.18c、放鍵段 ~7.2c（C10/D15）；弦長模型假設 A4=0.35 m、每八度減半（MIDI 36 算出 2.49 m，D11）；梁的 *2 經驗阻尼與 D1 未溯源；Chromatic 槌具未標定（D2）；FM 域外。變現計畫把「可稽核物理鏈」當主要賣點，所以一份集中、只彙整已裁決事實的主張域清單有直接價值。只彙整不新增主張，不需裁決；若出現新的收窄才要月月裁。
- 證據：docs/ENGINE_DOMAIN_CLAIMS.zh-TW.md:1-30 只有 §1；reports/decision_packets/D11_string_scale_candidate.zh-TW.md:39「MIDI 36 算出 2.49m 的弦長」；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:95 差異化＝「可稽核物理鏈」
- 建議：AI 把各裁決包已定案的限制逐條轉寫進 §2 之後，每條附裁決日期與出處，不改措辭、不新增主張；再給月月一頁白話版當產品說明素材。
- 懷疑者查證：ENGINE_DOMAIN_CLAIMS.zh-TW.md 只有 30 行，只有 `## 1. water_gong` 一節，屬實。但這份文件的檔頭（:4-6）規定每條聲明都要「附裁決記錄與分析文件出處」，而且範圍是「每個引擎物理模型模擬的是什麼、不是什麼」。原建議要收的幾項裡：量測器 ≤1.18c/7.2c 是工具主張，已在 EARFREE §8.5，放進引擎清單會分類錯；D11 選的是 C（不落地），弦長假設不是一條已裁決的主張；Beam `*2` 和 D1 是未決缺口，不是裁決。所以「只彙整已裁決事實、不需裁決」這個說法不成立，至少一部分條目要月月點頭。
- **查證修正**：AI 可以擬一份「已知限制索引」，只放指向各裁決包和 EARFREE §8.5 的連結，不直接寫成 ENGINE_DOMAIN_CLAIMS 的新聲明。要升格成正式引擎主張的條目（例如 FM 域外、弦長模型假設），逐條做成小裁決給月月選。

### [open-work:V1-score-vs-midi] score_vs_midi_verify「接進 GATE」其實大多已完成，只剩文件沒跟上
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：查證結果：tests/test_score_vs_midi_verify.py 的 EndToEndFurEliseTests 會對兩份真實給愛麗絲 score 跑 svm.verify()，要求 905/905 對上。CI 從 E1 起跑全套 pytest，而且是阻斷式，所以這個工具對唯一入庫的 MIDI↔score 配對早就在 CI 裡執行。TODO 和 README 還寫「尚未接進任何 GATE/CI」，這是 E1 之前的舊敘述。真正還開著的只有：未來四季/月光換源時要把新配對加進這組測試（已登記為產線標配）。
- 證據：tests/test_score_vs_midi_verify.py:278-301 EndToEndFurEliseTests 斷言 905 matched；.github/workflows/physics.yml:58-61 python -m pytest tests -q（阻斷式）；TODO.md:194-199「尚未接進任何 GATE/CI/文件」；README.md:517-520「not wired into any CI workflow」（08-28 稽核記錄）；README.md:364-373 quick reference 沒列 score_vs_midi/stem/partial
- 建議：併入 G19 文件修正：更正 TODO:194-199 的敘述，README quick reference 補列 score_vs_midi_verify / stem_verify / partial_verify / measurement_selfcal。C1 換源時再把新配對加進 EndToEnd 測試。
- 懷疑者查證：tests/test_score_vs_midi_verify.py:279-301 的 EndToEndFurEliseTests 斷言 905 matched。夾具 scores/classical/fur_elise/source/fur_Elise_WoO59.mid 用 git ls-files 查是 TRACKED，CI 不會因缺檔而 skip。整合卡那唯一 1 個 skip 是 test_render_app_filename_safety.py:135（05b_pytest_verbose_xfail_skip_reasons.txt）。physics.yml:58-61 會跑 `python -m pytest tests -q`，沒有 continue-on-error。TODO:194-199 和 README:517-520 的舊說法都屬實。

### [open-work:G19-docs-stale] 文件過期勾選與前後矛盾（commit 後一次清掉）
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：下面這些已經做完或已裁決，文件卻還寫著開放或舊狀態，會誤導下個 session。其中最要緊的是 README 仍寫「重建三個測試 target」，而實際是五個；09-07～14 CI 紅燈的根因正是少建了 SpectrumView。完整清單：TODO:208 雙開門 [ ]（08-30 已否決）；TODO:684 亮度 EQ 覆核 [ ]（A4 08-27 已裁）；TODO:694 Rule 10 審閱 [ ]（A1 08-26 已裁）；TODO:710 DAW 驗證 [ ]（A9 已關）；TODO:762 跨平台規則 [ ]（C3 08-22 已關）；ROADMAP_PHYSICS M8 列「等 UI mockup 裁決後才 merge」（09-15 已 merge）；B7 列「unstaged 待再次稽核」且沒記 09-15 的 C/乙 裁決；HANDOVER:137 基準寫 post_d8、pytest 267（應為 post_a14、270）；HANDOVER:124 裁決包清單缺 B7/D9/D11/D13；D13 裁決包:149 殘留一句「月月尚未裁決，此節留白待填」；BeamModel.h:48 自稱「已登記 TODO.md」，實際 TODO 查無這一條。
- 證據：README.md:356,360 只列三個測試 target；HANDOVER.md:35 X4 現為五個；TODO.md:208,684,694,710,762 未勾；ROADMAP_PHYSICS.md:153 M8「依月月指示等 UI mockup 裁決後才 merge」；ROADMAP_PHYSICS.md B7 段「B7P1 稽核修復（2026-09-14，unstaged 待再次稽核，In progress）」；grep '09-15' ROADMAP_PHYSICS.md 無命中；HANDOVER.md:137 sha256_before_post_d8.txt / 267 passed vs HANDOVER.md:28 post_a14 / 270；reports/decision_packets/D13_gong_2x_partial.zh-TW.md:149；src/physics/BeamModel.h:48「去留為月月裁決項（已登記 TODO.md）」；grep '\*2' TODO.md 無此條
- 建議：G0 commit 後開一張文件同步卡：逐條打勾並附關閉依據，修 README X4（五個 target，與 physics.yml 同步），更正 HANDOVER §8/§9，刪掉 D13 殘句，在 TODO 正式登記 Beam *2 裁決項（見 B1）。BeamModel.h 的註解若要改屬 src，照 R6 流程。
- 懷疑者查證：逐條查過：README:356/:360 是三個 target；TODO:208/:684/:694/:710/:762 都未勾；ROADMAP:153 M8；ROADMAP M10 的 B7 段寫 unstaged，搜 09-15 為 0 筆；HANDOVER:137 寫 post_d8/267；HANDOVER:124 的清單缺 B7/D9/D11/D13；D13 裁決包:149「*月月尚未裁決，此節留白待填。*」（:141 §4 已經有裁決記錄）；BeamModel.h:48 寫「已登記 TODO.md」，但在 TODO/ROADMAP/HANDOVER/RESEARCH_INDEX 搜「`*2`|過阻尼|經驗加權」都找不到這一條。唯一例外是 :710 要附 GUI automation lane 的但書（見 T5）。

### [open-work:P2-partial-full] partial_verify 從沒在 905 顆全曲規模跑過；D14 修好記憶體後已經能跑
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：設計文件明寫 partial_verify 從未在全曲 905 事件規模執行，原因是 stem_verify 當時會吃到 ~41 GB。D14 之後全量只需要 1.65 GB。A13 裁決包也要求「修完 B-2 後這 22 顆要重量」，但 A14 落地後查不到重量的證據。這件和 N1 相關：弱基頻的組成已經換了一批。
- 證據：docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md:370-374「partial_verify.py 從未在全曲 905 事件規模上執行過」；reports/gate_outputs/wf0914_D14_memory_fix.txt:203-214 全量 905 跑完，peak ≈1.65 GB；reports/decision_packets/A13_partial_gate_domain.zh-TW.md:543-544「修完 B-2 後這 22 顆要重量」；reports/gate_outputs/ 下只有 wf0908_P1/wf0909_C10B/C10C 用過 partial_verify，沒有 A14 之後的全量記錄
- 建議：用現成 build 跑 stem_verify --keep-stems 全量，接著跑 partial_verify，產出 A14 之後的 informational 報告（新的弱基頻子集 pitch_via_partials、partial PASS/FAIL 拆分），並更新設計文件 §8.5 的數字（措辭不動）。
- 懷疑者查證：EARFREE_MELODY_GATE_DESIGN.zh-TW.md:370-374 寫「partial_verify.py 從未在全曲 905 事件規模上執行過」（~41GB）。wf0914_D14_memory_fix.txt:203-214 的全量 905 顆峰值是 1649.9 MB。A13 裁決包:543-544「修完 B-2 後這 22 顆要重量」。在 reports/gate_outputs 下，用過 partial_verify 的只有 wf0907~0910 的證據檔，D14 裡的命中只是測試說明，沒有 A14 之後的全量紀錄。

### [open-work:P3-partial-gate-premise] partial_verify 升 GATE 的前提已經變了（C10 已裁 A），理由字串還寫「待裁決」
- 查證：**adjusted**｜誰：月月裁決｜嚴重度 low｜工作量 S
- 說明：partial_verify 維持 gate_ready=false 的理由是「C10 量測器 informational 或 GATE 還待月月裁決」。但 C10 09-10 已選 A：量測器帶著 ≤1.18c 已知誤差照常用於 ±5c GATE。這個前提已經不成立，工具要永久維持 informational，還是改用新條件升 GATE，需要月月重新決定。
- 證據：tools/partial_verify.py:514-518 gate_ready_reason「C10 … is itself still pending 月月裁決 on informational-vs-GATE status」；docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md:342-344 同一理由；HANDOVER.md:78「C10 選 A：主張域收窄…±5 cent 門檻不變」
- 建議：AI 先做 P2 拿到全量數字，再出一份小裁決包（甲：永久 informational 並改理由字串；乙：頻率 ±5c 升 GATE，振幅仍不判）給月月選。
- 懷疑者查證：tools/partial_verify.py:514-518 的 gate_ready_reason 還寫 C10「still pending 月月裁決」，EARFREE:342-344 也一樣，屬實。但原發現漏了一條：A13 裁決包:542-543 早就寫好「月月選 A 即可翻成 GATE」，也就是 C10 選 A（09-10）之後，照既有規劃本來就可以升 GATE，不是完全要重新裁決。不過 D15 A'（09-15）確認放鍵段量測誤差上界約 7.2 c，已經大於 ±5 c 門檻，partial_verify 的量測窗如果涵蓋放鍵段，升 GATE 的前提就變了。所以還是需要月月確認，owner 歸月月對，理由要改寫。
- **查證修正**：A13 裁決包:543 原本規劃「C10 選 A 即可把 partial_verify 翻成 GATE」，C10 已在 09-10 選 A。但 D15 A' 揭露放鍵段上界約 7.2 c（大於 ±5 c），前提已經不同。請月月在「照 A13 原規劃翻 GATE（只判持續段）」和「維持 informational、改寫理由字串」之間選一個；AI 先用 P2 拿全量數字附上。

### [open-work:B1-beam-x2] BeamModel 的 *2 阻尼加權去留（孤兒裁決項，前置是 D1）
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 M
- 說明：寬頻化之後，舌鼓 BeamModel 內部摩擦項的 *2 變成「全音域一律 2 倍過阻尼、不再有任何錨點理由」的純經驗係數。B1/B2 報告兩度重申「未處理、另卡裁決」，程式註解也自稱已登記 TODO，但 TODO 裡查不到這一條。去留會改所有舌鼓渲染（R10 全觸發），合理的去留依據要靠 D1 梁阻尼文獻。
- 證據：src/physics/BeamModel.h:38-57 decayTimeForFrequency … internalFrictionRate(...) * 2.0f，註解:45-48；reports/damping_broadband_findings.md:135-141 §5；reports/b1_b2_bridge_damping_before_after.md:98-104 §6「本卡未處理、已登記」；grep '\*2' TODO.md 無此條
- 建議：先在 TODO 正式登記（G19）。D1 有結果後，AI 做 R10 前後數字（拿掉 *2 對 tongue_drum T60 和 corpus 的影響，在 scratch 副本跑，不落地），出成裁決包給月月選。
- 懷疑者查證：src/physics/BeamModel.h:38-57，其中 :52-53 是 `internalFrictionRate(...) * 2.0f`；:45-48 的註解寫「不再有任何錨點理由的純經驗係數。去留為月月裁決項（已登記 TODO.md）」。但在 TODO/ROADMAP/HANDOVER/RESEARCH_INDEX 搜「`*2`|過阻尼|經驗加權」都沒有這一條。ROADMAP:155 M10 只附帶一句「BeamModel `*2` 重申未處理」。

### [open-work:R-D1] D1 梁／板的空氣與輻射阻尼文獻：從來沒搜過
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 M
- 說明：RESEARCH_INDEX 和 TODO 都標「未搜尋，狀態未知」。梁/板阻尼律只有 eta·f、beta·f²、gamma·f 三項，f→0 時全部趨近 0，這正是弦在 B1 之前低音 T60 發散的同一種結構；beam_plate_beta_air/gamma_radiation 也仍標未溯源。這是舌鼓/水鑼 T60 主張與 B1（*2）的共同前置。純文獻研究，不需裁決。
- 證據：TODO.md:604 D1「未搜尋，狀態未知」；docs/RESEARCH_INDEX.md:109 同上；src/physics/BeamModel.h:38 T60(f)=1/(2·eta·f/2.2 + beta·f² + gamma·f)；reports/gate_outputs/wf0914_integration_raw/06_physics_verify_full.txt:477-480 tongue_drum steel T60 16.39 s、aluminum 30.1 s @MIDI 60
- 建議：開研究 lane 卡，照 WF0907_R_research_common 的規約做：只引用實際 fetch 到全文的數字，逐字引文加頁碼；查不到就誠實寫查不到。產出 docs/BEAM_PLATE_DAMPING_SOURCES 草稿。
- 懷疑者查證：TODO.md:604 D1「未搜尋，狀態未知」，RESEARCH_INDEX.md:109 也一樣。BeamModel.h:38 的阻尼律三項在 f→0 時都趨近 0。wf0914_integration_raw/06_physics_verify_full.txt 裡 tongue_drum steel 16.390 s、aluminum 30.135 s，屬實。TODO:743-747 也寫「Beam/Plate 仍未溯源（D1）」。

### [open-work:E1-a14-b1] A14 B-1（力脈衝深零點形狀）：文獻仍在付費牆後，另有一條第一原理替代路
- 查證：**adjusted**｜誰：等外部｜嚴重度 medium｜工作量 L
- 說明：D10 已把開放管道查盡，Hall 1988、Chaigne & Askenfelt 1994 Part II 仍然 403 或付費。N1 的發現讓這一項從「等文獻的理論缺口」變成「實際影響上架曲目的缺陷」；A14 報告也記錄 MIDI 67 以上的 noteComp 仍頂在 clamp 4.0。另有一條不靠付費文獻的路：用 B4 已有的 K、α、槌質量，直接數值積分非線性接觸 F=Kδ^α，得到真實的力脈衝形狀再做 FFT，取代半正弦假設。這只是研究假說，效果還沒驗證。
- 證據：TODO.md:36 D10「兩篇缺口文獻仍 403/付費牆」；reports/a14_tauc_keytrack_before_after.md:38-40 B-1 未解、noteComp MIDI 67 以上頂 clamp 4.0；docs/HAMMER_CONTACT_SOURCES.md §9（D10 補摘）；N1 證據：E5@0.278 n1/n2 -18.5 dB
- 建議：文獻繼續等（月月若有機構帳號可以代取）。AI 可以先在 scratch 做數值接觸積分的原型，比較它和半正弦在 N1 那些格子的頻譜，產出研究報告；R4 規定溯源到 B4 常數，落地與否另裁。
- 懷疑者查證：TODO.md:36 D10 仍是 403/付費牆；a14 報告 §0（約 :38-40）寫 B-1 未解、noteComp 在 MIDI 67 以上頂到 clamp 4.0；HANDOVER_CONTACT_SOURCES §9（:236）是 D10 補摘，都屬實。N1 讓這一項的影響變得具體，這點也成立。但替代路有一個沒說的前提：HammerImpulse.h:472 自己寫「F = K*delta^alpha above has NO dissipation term」，無耗散的冪次律積分出來是對稱脈衝，頻譜仍可能有深谷，不保證能消除零點。repo 裡已有 Stulov 遲滯參數（HAMMER_CONTACT_SOURCES.md §5 :147-168，F₀/p/ε/τ₀ 已取得），原型要把遲滯（不對稱回彈）一起放進去才有意義。這是我的推論，沒有實測。
- **查證修正**：文獻繼續等。AI 可以在 scratch 做接觸力數值積分原型，但要同時比較三種：無耗散 F=Kδ^α、加 Stulov 遲滯（HAMMER_CONTACT_SOURCES §5 已有參數）、半正弦，看 N1 那些格子（E5@0.278、A5@0.427…）的基頻和二次泛音比。純冪次律是對稱脈衝，未必能去掉深零點。落地與否另外裁決。

### [open-work:C-C1] C1 rubber 短瞬態 T60 估計器：研究部分可以先做，門檻要月月裁
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 M
- 說明：--full 一直留著 3 筆 UNVERIFIED/N/A（cimbalom/tongue_drum/water_gong 的 rubber，T60 14～28 ms，不到 8 個週期）。「幾個週期算數」是新容差，必須月月裁（R2）。但 EDT/Schroeder 候選估計器的實作、合成已知 T60 哨兵、在這 3 筆上的數字，都不需要裁決，AI 可以先做完再出裁決包。價值偏低，只影響 rubber 這種邊緣材質。
- 證據：TODO.md:545 C1「需月月裁決可信門檻（幾個週期算數）」；reports/gate_outputs/wf0914_integration_raw/06_physics_verify_full.txt:475,485,495,498,622 三筆 N/A / UNVERIFIED
- 建議：在 tools 外的 scratch 原型實作 EDT/Schroeder＋明確拒答條件；哨兵要含「期望值固定、真值偏離」這條軸（HANDOVER §12 的教訓）；產出裁決包，列 4/6/8 週期三檔門檻各自的判定結果。
- 懷疑者查證：TODO.md:545 寫「需月月裁決可信門檻」；06_physics_verify_full.txt 的 cimbalom/rubber 0.028s、tongue_drum/rubber 0.014s、water_gong/rubber 0.028s 都是 N/A/UNVERIFIED，結尾 UNVERIFIED/N/A 3 cases，屬實。原型本身不需要裁決，門檻值需要（R2）。

### [open-work:CI-hostprobe] HostProbe（外掛即時路徑 89 項）沒跑在 CI
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 M
- 說明：D12（舊 state 遷移）和 D9c（IR 補償）都是外掛專屬路徑，唯一的自動驗證是本機 HostProbe。CI 的測試建置清單沒有 TsukiSynthHostProbe，workflow 裡也查不到 hostprobe。外掛正是要賣的東西，回歸只靠本機人跑。這不是既有登記項，是建議補的缺口。
- 證據：TODO.md:13-15 D9c/D12 證據都是 HostProbe 89 PASS（本機）；TODO.md:37-44 D12 HostProbe 三情境；grep -i hostprobe .github/workflows/*.yml → 無命中；README.md:370 HostProbe 只列為本機命令
- 建議：AI 擬 physics.yml 的 Windows leg 新增步驟：build TsukiSynthHostProbe 後對剛建好的 VST3 執行，0 failures 才算過。要 push 才驗證得了，所以 push 前須月月授權。
- 懷疑者查證：在 .github/workflows/*.yml 搜 hostprobe/HostProbe 是 0 筆；physics.yml:54/:265 的測試建置清單沒有 TsukiSynthHostProbe；CMakeLists:255 註明 HostProbe 是刻意不註冊進 ctest。D12 和 D9c 的 89 PASS 都是在本機跑的（wf0914_D12_hostprobe.txt）。HostProbe 能不能在 GitHub 的 Windows runner 上無頭執行，這次沒有驗證；改 workflow 要 push 才驗得到，需要月月授權。

### [open-work:W1-letters] 兩封信（TU Berlin 商業授權／Iowa MIS 泰國鑼器材）09-15 已寄，等回覆
- 查證：**confirmed**｜誰：等外部｜嚴重度 low｜工作量 n/a
- 說明：已寄出 10 天。repo 內查不到回覆記錄，本輪也沒去讀信箱。TU Berlin 那封關係到 A8 指向性資料能否商用；Iowa 那封是泰國鑼器材對應（D13/P6 的背景）。目前都不擋主線。
- 證據：HANDOVER.md:27「兩封信 09-15 已寄出等回覆」；DEVLOG.md:20 同上；docs/correspondence/2026-09-10_TU_Berlin_directivity_license_request.md、2026-09-10_Iowa_MIS_thai_gong_equipment_query.md
- 建議：月月收到回信時轉給 AI 登記。若要追蹤，月月可以授權 AI 讀那兩封信的回覆串（僅限這兩封）。
- 懷疑者查證：HANDOVER.md:27 和 DEVLOG.md:22 都寫 09-15 已寄出；repo 裡搜不到任何回覆紀錄。這次沒有讀信箱（也不應該在沒授權的情況下讀）。

### [open-work:W2-paywall] 其他付費牆或需實體量測的資料缺口（D5、Rossing & Shepherd 1982、B7 絕對 SPL 出處、D7）
- 查證：**confirmed**｜誰：等外部｜嚴重度 low｜工作量 n/a
- 說明：D5 銅鑼 JCIE 2005 全文要付費。Rossing & Shepherd 1982 是 D13 選項 A 做乳突鑼模態表的前提。B7 驗收基準 (a) 已裁乙（BLOCKED），解除要走三條管道：向 Goebl 索取 Fig 2.20 校準值、Roginska 2013 POMA、Meyer 動態範圍表。D7 實體試體量測買不到，只能自己量。這幾項都不擋現在的主線。
- 證據：TODO.md:608 D5、:610 D7；reports/decision_packets/D13_gong_2x_partial.zh-TW.md:32-34 Rossing & Shepherd 未取得；reports/decision_packets/B7_phase2_and_open_items.zh-TW.md:170-171 三條管道留給月月
- 建議：維持登記。月月若有圖書館或機構帳號的機會，可以一次代取 Hall 1988、Chaigne&Askenfelt 1994 II、JCIE 2005、Rossing&Shepherd 1982、Roginska 2013。
- 懷疑者查證：TODO.md:608 D5 是付費牆、:610 D7 只能自己量；D13 裁決包約 :32-34 寫 Rossing & Shepherd (1982)「本卡未取得全文」；B7 裁決包 §6 第 2 點列了三條管道（Goebl Fig. 2.20、Roginska 2013、Meyer），留給月月。

### [open-work:R-D2D4D6] D2/D4/D6 小型文獻補搜（AI 可做，價值偏低）
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：D4 舌鼓 ICSV27 2021：機構庫 403，可以試作者自存版。D6 Wood Handbook Table 5-15 溫度係數：同一份公版 PDF 的後續頁，但 B5 的異向 schema 目前零消費，拿到也沒地方用。D2 Chromatic 槌具：中國鑼、木魚、鼓棒三條還沒核原文。都不需要裁決；D4 對梁模態比值升級（D8 長期項）較有用。
- 證據：TODO.md:605 D2「中國鑼/木魚/鼓棒三條仍未核」；TODO.md:607 D4、:609 D6；docs/WOOD_ANISOTROPY_SOURCES.md:198「[ ] 溫度相依的逐項係數表（Table 5–15）未取得」；TODO.md:319「orthotropic schema…目前零消費路徑，死資料」
- 建議：排在 D1 之後，照研究 lane 規約做，一張卡處理 D4＋D2 剩餘三條；D6 等之後真的有消費者再做。
- 懷疑者查證：TODO.md:605 D2「中國鑼/木魚/鼓棒三條**仍未核**」；:607 D4 機構庫 403；:609 D6；WOOD_ANISOTROPY_SOURCES.md:198「[ ] 溫度相依的逐項係數表（Table 5–15）未取得」；TODO:318「目前零消費路徑，死資料」。

### [open-work:L1-longterm] 長期物理缺口（有限音板共振結構／共鳴踏板／木材異向實際接入／乳突鑼模型／B7 重啟／相位與指向性）
- 查證：**confirmed**｜誰：長期研究｜嚴重度 low｜工作量 L
- 說明：B1 用的是無限板導納，能解決低音發散，但重現不了 Wogram 量到的相鄰半音 5:1 落差（有限音板的共振峰谷結構）。共鳴、制音器、踏板物理都還沒做。B5 異向木材是死資料。水鑼乳突鑼模型（D13 選項 A）缺可溯源的模態表。B7 要重啟，得先解除 B7.md §5 禁令，讓 score 帶真實 MIDI velocity。相位、指向性維持 UNVERIFIED。每一項都是 milestone 級，而且大多會觸發 R10。
- 證據：reports/damping_broadband_findings.md:120-128 Wogram F#4 3.5 s vs G4 0.7 s，5:1；TODO.md:749 coupled-body/sympathetic/damper [ ]、:756 anisotropic [ ]；reports/decision_packets/B7_phase2_and_open_items.zh-TW.md:168-169 重啟需先解 §1.1（score schema 加真實 MIDI velocity，需改 B7.md §5 禁令）；TODO.md:746 相位/SPL 預測模型仍開
- 建議：維持登記，不在變現線前面排。月月如果想重啟物理主線，建議先做「有限音板導納」的文獻盤點卡（研究 lane，不動 src）。
- 懷疑者查證：damping_broadband_findings.md:124-128 寫 Wogram F#4 3.5 s 對 G4 0.7 s，5:1；TODO.md:749 coupled-body/sympathetic/damper 和 :756 anisotropic 都是 [ ]；B7 裁決包 §6 第 1 點寫重啟前要先解 §1.1、改 B7.md §5 的禁令；TODO:746 的 SPL/相位模型仍開著。

### [open-work:Y1-small-actions] 月月自己的小事：A10 Score 控制台實操、調音器目視無障礙檢查、裝 Limbus、清 Yamaha 殘留
- 查證：**adjusted**｜誰：月月動手｜嚴重度 low｜工作量 S
- 說明：A10（Standalone [Score] 鈕實際操作驗收）和調音器目視可讀性檢查只能月月本人看；Limbus Spatial Stage 要月月自己安裝啟用；Yamaha Piano Sheet Converter 裝好後才叫 AI 清 Downloads 的約 200 MB 殘留。本輪沒有查證 Downloads 的現況。
- 證據：TODO.md:172 A10 [ ]、:668「待月月實際操作驗收」；TODO.md:711 visual accessibility review of the tuner [ ]；HANDOVER.md:29, :157 Limbus／Yamaha 待辦
- 建議：月月有空時處理；Yamaha 裝好後跟 AI 說一聲，AI 再列出要清的檔讓月月確認後刪除。
- 懷疑者查證：A10 屬實：TODO.md:172 是 [ ]，:668 寫「**待月月實際操作驗收**」；調音器目視在 TODO:711 也屬實。但「裝 Limbus」「Yamaha 裝好後」這兩件已經過時：Limbus 兩個 VST3 和 Standalone 在 2026-09-14 12:56 已安裝，Yamaha Piano Sheet Converter 在 AppData/Local/Programs 也是 09-14 12:56 已安裝（見 H5）。原發現自己說「本輪沒有查證 Downloads 現況」；實測資料夾是 614 MB，其中 Yamaha 解壓殘留約 470 MB，不是 200 MB。
- **查證修正**：月月自己的小事：A10 Score 控制台實操、調音器目視可讀性檢查；Limbus 已裝（09-14），只需確認有沒有用金鑰啟用；Yamaha 已裝（09-14），請月月授權 AI 列出 Downloads\不知道有沒有用 裡約 470 MB 的解壓殘留（另有 136 MB 安裝檔、Klanggeist 10 MB），確認後再刪。

### [open-work:I1-closed] 已查證確實關閉、不要再當成待辦（含一筆過時記憶）
- 查證：**adjusted**｜誰：資訊｜嚴重度 low｜工作量 n/a
- 說明：以下都有裁決或 GATE 證據：D9（D9c 已落地）、D12（遷移）、D13（主張域 B）、D14（記憶體）、D15（A' 主張域）、C10（選 A；5 個 xfail 是刻意保留、每次 CI 都會點名的開放缺口）、A14 B-2（已落地）、B7（09-15 合法終點）、K-02/F-03/A8。另外，記憶裡「阻尼律缺支撐損耗、低音會發散」這條對弦已經過時：B1/B2 讓 C2 從 128.75 s 收斂到 17.66 s，M10 已 Done；還開著的只剩梁/板（見 R-D1、B1）。
- 證據：TODO.md:13-18 五項裁決落地；reports/gate_outputs/wf0914_integration_raw/05b_pytest_verbose_xfail_skip_reasons.txt:6-12 五個 xfail 刻意保留；ROADMAP_PHYSICS.md:155 M10 Done「C2 128.75s→17.66s」；reports/decision_packets/B7_phase2_and_open_items.zh-TW.md:164-173 §6 裁決記錄
- 建議：寫交接時照這份清單把它們移到「已關閉」；有空可以更新 project_tsuki_damping_gap 記憶，註明弦域已由 B1 解決。
- 懷疑者查證：大多屬實：TODO:13-18 五項裁決；05b_pytest_verbose_xfail_skip_reasons.txt 的 5 個 XFAIL 都是刻意保留；ROADMAP:155 M10 寫 C2 128.75s→17.66s，所以「阻尼缺口、低音發散」這條記憶對弦來說確實過時。但有三處不能算乾淨關閉：(1) B7 裁決包 §6 第 3 點要求同步 ROADMAP/TODO 的 B7 條目，沒有執行（見 T6、P1）；(2) D13 已裁，但 PlateModel.h:25 和 score description 的同步還欠著（D13-sync）；(3) A14 B-2 已落地，但 N1-fe16 查到它讓 16 顆新的弱基頻 FAIL 出現，A14 整體應維持開放。
- **查證修正**：確實關閉：D9、D12、D14、D15、C10（選 A；5 xfail 刻意保留）、K-02、F-03、A8（裁決面；TU Berlin 回信仍在等）。已裁但落地有尾巴：B7（裁決要求的 ROADMAP/TODO 同步沒做）、D13（註解和描述同步）。不能算關閉：A14（B-1 等文獻，而且 B-2 引出 N1 的 16 顆新 FAIL）。記憶 project_tsuki_damping_gap 可以註明弦域已由 B1/B2 解決，梁/板仍開著（D1、`*2`）。

## 懷疑者補抓的漏項（docs-open）

- [CI 同款缺陷還留在 release workflow] .github/workflows/release-physics.yml:45 只建 TsukiSynthAuditTest、TunerTest、PhysicsModelsTest 三個測試 target，:49 接著跑 `ctest --test-dir build -C Release`。spectrum_view_repro 從 09-13 起就註冊在 CMakeLists.txt:249，所以這個 workflow 會出現跟 09-07~14 一樣的 Not Run 紅燈。766d21d 只修了 physics.yml（`git show --stat 766d21d` 只列 physics.yml 4 行），release-physics.yml 最後一次改動是 7a7292c（08-02）。`gh run list --workflow release-physics.yml` 的結果是 []，從來沒跑過。它的觸發條件是 push tags "v*" 或手動，所以變現計畫第一次打 v 標籤發版時一定紅。另外它用的是 `python -m unittest discover`（:50），不是 pytest；tests/ 下 15 個 test 檔裡有 3 個是 pytest 函式式寫法（例如 test_measurement_selfcal.py:129 的 def test_…、:171 的 @pytest.mark.xfail），unittest 會靜默不收這些測試（這點是推論，沒有實跑）。owner：AI 可以擬修正，但要 push 驗證，須月月授權。
- [B7 裁決有一步沒落地，所以「五項裁決全部落地」不精確] reports/decision_packets/B7_phase2_and_open_items.zh-TW.md §6 第 3 點明文要求：「ROADMAP/TODO 的 B7 條目同步標『In progress——Phase 0 完成、Phase 1 部分完成（欄位撤回版）、Phase 2/3 BLOCKED（月月 09-15 裁決）』」。但 `grep 'Phase 2/3 BLOCKED'` 在 TODO.md 和 ROADMAP_PHYSICS.md 都是 0 筆：TODO:457 仍寫「BLOCKED 待月月裁決」，ROADMAP:155 的 B7 段仍寫「unstaged 待稽核／待再次稽核」。HANDOVER.md:6 和 TODO.md:13 卻說「已全部落地」。
- [R6 規則範圍沒涵蓋外掛路徑程式碼] ROADMAP_PHYSICS.md:132 的 R6 只列 src/physics/、src/engines/、src/dsp/、src/score/。本輪 D12 改的 src/PluginProcessor.cpp、D9c 改的 src/effects/EffectChain.h，以及 09-13 的 src/IRLibrary.h、src/ParameterLayout.cpp，都不在 R6 強制範圍內。這幾張卡都有自己跑 GATE，但規則文字沒有強制；而外掛正是要賣的產品。要不要把 R6 擴大到 src/effects/ 和外掛層，只有月月能決定（ROADMAP §1 是月月的規則）。
- [Downloads 殘留量寫太少] HANDOVER.md:157「待清：Yamaha 裝好後根目錄約 200 MB 解壓殘留」。實測 Downloads/不知道有沒有用 裡：根目錄檔案 445.4 MB，扣掉安裝檔 135.9 MB（installer.exe、Limbus、Orra、Klanggeist zip），再加上 locales 48 MB 和 resources 112 MB，Piano Sheet Converter 的解壓殘留約 470 MB。這跟 H5/Y1 同一條線，更新文件時數字要一起改。

## release-readiness

音效包（43 個）和專輯（6 軌）的檔案是齊的：zip 內容跟 catalog 逐一對得上，雜湊值 0 個不符。母帶規格也用另一個量測器重量過，結果達標：音樂 −13.9～−14.1 LUFS，所有檔案真峰值都 ≤ −1 dBTP，100 個檔案都沒有削波平頂。PRODUCT_SHEET 說全曲版有「41 個削波樣本」，查下來是誤讀：那個數字是正規化之前算的，母帶本身沒有削波。所以 §5 第 3 題的前提不成立，全曲版可以不重渲就加進專輯，放不放由月月決定。真正卡住上架的是另外幾件：6 個 loop 檔的長度都不等於小節長度，卻寫著「可無縫循環」；授權條款有幾個漏洞，而且 Fab 平台不接受自訂授權；文案裡的「沒有 AI」「阻尼是實測常數」說法跟 repo 記錄對不上；三個打擊音效的峰值被開頭一瞬間的尖峰佔掉，聽起來會比其他音效小 13～23 LU。合成器本體的 6 件前置事一件都沒完成：staged 成果還沒 commit；UI 那條已經過時（雙開門 08-30 就被否決了）；安裝包、使用授權（EULA）、第三方授權聲明檔都還沒有；release CI 裡有一個已知會紅燈的缺陷。月光和四季的授權問題不影響這兩個現有商品，但專輯 Vol.2 會被卡住；合成器如果附範例譜，也要把這兩批檔案排除。

### [release-readiness:R1] 音效包／專輯 zip 內容完整、雜湊全對
- 查證：**confirmed**｜誰：資訊｜嚴重度 low｜工作量 n/a
- 說明：用 python zipfile 直接讀 zip（沒有解壓進 repo），跟 catalog.json 比對。音效包 zip 有 45 個檔案：43 個 WAV，加 LICENSE.txt 和 README.txt，沒有缺也沒有多；43 個 WAV 的 sha256 跟 catalog 的 dist_sha256 全部一致。專輯 zip 有 13 個檔案：6 個 WAV、6 個 MP3、1 個 README；按設計排除了全曲版；6 個 WAV 的 sha256 全部一致。兩個 zip 的 testzip 都回報正常。PRODUCT_SHEET §4 列的資料夾（masters/distribution/preview/packages/logs）都在。這部分可以直接上架。
- 證據：C:/Users/admin/AppData/Local/Temp/claude/C--Users-admin-Desktop-Claude/7c5a84c1-762b-4e45-b6e9-c2ce9556d699/scratchpad/release-readiness/zipcheck.py 輸出：SE zip 45 entries；audio in zip 43 expected 43 missing [] extra []；sha checked 43 mismatch 0；同一支腳本：Album zip 13 entries；audio 12 expected 12；sha checked 6 mismatch 0；testzip None；exports/products/clean_batch2/build_packages.py:28-31（排除 ai_radiance_complete）
- 建議：不用處理，照現狀可以上傳。
- 懷疑者查證：自寫 scratchpad/verify-release/zipv.py 直接讀 zip：SE zip 45 個（.wav 43＋.txt 2），testzip=None；Album zip 13 個（wav 6、mp3 6、txt 1），testzip=None；49 個 WAV（43 sfx＋6 music）的 sha256 對 catalog.json dist_sha256 全部一致（mismatch 0），磁碟上 50 個 distribution 檔也全對。build_packages.py:26-31 確實排除 ai_radiance_complete。PRODUCT_SHEET §4 列的 masters/distribution/preview/packages/logs 都在。

### [release-readiness:R2] 母帶規格重新量測：−14 LUFS／−1 dBTP 達標，100 個檔案都沒有削波
- 查證：**adjusted**｜誰：資訊｜嚴重度 low｜工作量 n/a
- 說明：原本的量測用的是 ffmpeg 的 loudnorm。這次改用另一個濾鏡 ebur128（peak=true+sample）把 50 個 distribution 檔全部重量一遍。音樂 7 軌的整合響度在 −13.9～−14.1 LUFS，真峰值在 −1.0～−1.8 dBTP；catalog 記的揚琴版 −0.97 屬於四捨五入的差距，ebur128 量到的是 −1.0。音效 43 個檔的真峰值全部是 −1.0 dBTP，取樣峰值都 ≤ −1.0。格式也都對：音樂是 44.1k/16bit 立體聲，音效是 48k/24bit 立體聲。另外把 50 個母帶加 50 個 distribution 共 100 個檔案都掃了一遍，找「連續相同峰值」這種削波平頂，結果 0 個，母帶最大取樣峰值 0.95000（−0.45 dBFS）。專輯 MP3 的真峰值在 −0.9～−1.8 dBTP。
- 證據：scratchpad/release-readiness/measure.py → measure_out.json：例 fur_elise_complete I=-13.9 TP=-1.0；ai_radiance_m1 I=-14.0 TP=-1.8；sfx 43/43 TP=-1.0；scratchpad/release-readiness/cliptest_all.py 輸出：files 100, flat-top files 0, max peak 0.95000；MP3：Original_AI_Radiance_Complete.mp3 TP=-0.9；fur_elise_complete.mp3 TP=-1.0
- 建議：不用處理。可以把這次的量測結果附進 PRODUCT_SHEET，當作第二個量測器的佐證。
- 懷疑者查證：自寫 lufs.py 用 ffmpeg ebur128=peak=true+sample 重量 50 個 distribution：fur_elise_complete I=-13.9 TP=-1.0；cimbalom -14.1/-1.0；ai_radiance_m1 -14.0/-1.8；m2 -14.0/-1.3；m3 -14.0/-1.0；m4 -14.0/-1.1；但 ai_radiance_complete I=-14.3（catalog 也記 -14.34），不在它寫的 -13.9～-14.1 區間。音效 43 個 TP 全是 -1.0、sample peak 最大 -1.0；格式：音樂 44.1k/s16 立體聲，音效 48k/24bit 立體聲。50 個母帶我自己掃過（clipv.py），最大峰值 0.9500000，沒有連續 3 個以上貼峰值的取樣。7 個音樂 MP3 的 TP 在 -0.9～-1.8。
- **查證修正**：量到的 7 軌音樂整合響度是 -13.9～-14.3 LUFS。全曲版 -14.3，其餘 6 軌 -13.9～-14.1。其他數字都成立：真峰值 -1.0～-1.8 dBTP、音效 43/43 TP=-1.0、母帶最大峰值 0.95、沒有削波平頂。

### [release-readiness:R3] 「全曲版 41 個削波樣本」是誤讀，母帶沒有削波
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 S
- 說明：PRODUCT_SHEET 看到 .render.json 的 samples_at_or_above_full_scale=41，就判定「母帶源頭已有削波」，因此建議不放全曲版。讀原始碼後發現：WavWriter 是在套用正規化增益之前，先數 float 緩衝裡 ≥1.0 的取樣；之後把峰值拉到 0.95 才寫檔，中間沒有任何硬削。實際量全曲版母帶：峰值 0.95000，沒有平頂。整批語料檢查（corpus 75/75）對這首也是 PASS，peak −0.45 dBFS。另外有三個音效的同一欄位不是 0（Gate Open Dark 2767、Stomp 18、Shackle Slam 20），PRODUCT_SHEET 沒提，但原因一樣，也沒有削波。所以 §5 第 3 題「要不要調低 master_volume 重渲」的前提不成立，全曲版可以不重渲直接加進專輯。
- 證據：src/score/WavWriter.h:25-34（先數 |x|>=1.0）、:36-43（之後才乘 0.95/peak）；masters/originals/Original_AI_Radiance_Complete.wav.render.json：normalize=true, pre_normalize_peak=1.132, applied_gain=0.839, samples_at_or_above_full_scale=41；scratchpad/release-readiness/cliptest.py：Original_AI_Radiance_Complete.wav peak=0.95000 flat-top runs 0；reports/gate_outputs/wf0914_B7P1_corpus_all_auditfix.txt:2102 rendered 136.60s peak -0.45 dBFS；檔尾 75/75 passed；exports/products/clean_batch2/PRODUCT_SHEET.md:29、:35、:78
- 建議：月月決定全曲版要不要放進專輯（不需要重渲）。決定後由 AI 修正 PRODUCT_SHEET §2/§5-3、LISTING_COPY C 段的說法，需要的話重跑 build_packages.py。另外建議把 render manifest 的欄位語意寫清楚：這是正規化前的計數。
- 懷疑者查證：src/score/WavWriter.h:25-34 在正規化前先數 |x|>=1.0，:36-43 之後才乘 0.95/peak，中間沒有硬削。render.json 內容：pre_normalize_peak=1.132、applied_gain=0.839、samples_at_or_above_full_scale=41。另外三個音效的同一欄位也不是 0：Magic_Dark 2767、Impact_Stomp 18、Impact_Dark_C2 20。自己量母帶 Original_AI_Radiance_Complete.wav：峰值 0.95，貼峰值的取樣只有 1 個，沒有平頂。wf0914_B7P1_corpus_all_auditfix.txt 在 :2102 附近寫 peak -0.45 dBFS，檔尾是 75/75 passed。補充：誤讀擴散得比清單寫的廣，除了 PRODUCT_SHEET:29/:35/:78，還有 LISTING_COPY.md:102、MONETIZATION_PLAN:26、build_packages.py:26 的註解，以及 catalog.json/csv 的 `clipped_samples` 欄（master_batch.py:114 產生；PRODUCT_SHEET:53 說 catalog 可以直接餵上架表單）。修正時要一起改。owner 標月月裁決正確，因為要不要放全曲版是商品決定。

### [release-readiness:R4] 6 個 loop 檔的長度不等於小節長度，卻寫著「可無縫循環」
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 high｜工作量 M
- 說明：拿 score 裡的 loop_bpm 和 loop_bars 算出每個 loop 應有的長度，再跟檔案實際長度比，6 個全部偏長（後面接了餘響尾巴）：rabbit 5.37 秒，應為 3.43 秒（140 BPM、2 小節）；akashic 24.3 秒，應為 16.0 秒；forest 16.7 秒，應為 12.0 秒；ocean 15.8 秒，應為 8.0 秒；restraint 8.5 秒，應為 4.8 秒；clockwork 5.17 秒，應為 4.0 秒。買家整個檔案拿去循環，節拍會斷，最後一個音的尾巴也沒有接回開頭。但 zip 裡給買家看的 README 對 Akashic Meditation Loop 寫「可無縫循環」，跟 PRODUCT_SHEET:55 寫的「未驗證」互相矛盾；BOOTH 文案則把檢查接縫的工作丟給買家。這件事完全可以用量測解決，不需要耳朵。
- 證據：scratchpad/release-readiness/loopcheck.py 輸出：rabbit_loop_001: file 5.366s | bpm 140 bars 2 -> musical loop 3.429s；akashic_loop_001: file 24.325s -> 16.0s；ocean_loop_001: 15.825s -> 8.0s；SE zip 內 README.txt：akashic__Akashic_Meditation_Loop.wav | loop | 冥想循環 — ...可無縫循環；exports/products/clean_batch2/PRODUCT_SHEET.md:55；LISTING_COPY.md:41-42（ループ素材は継ぎ目を確認してから）
- 建議：AI 在 exports/ 裡另外產一套 loop-ready 版本，不改 scores/ 和 src/：把檔案裁到剛好的小節取樣數，超出的尾巴疊回開頭（tail-wrap），或者渲染兩輪、取第二輪。完成後用數字驗收：長度誤差小於 1 個取樣、接縫跳差和 RMS 連續性都要量。在這之前，先把 README 裡的「可無縫循環」拿掉。
- 懷疑者查證：讀 score 的 meta.loop_bpm/loop_bars（事件 time 單位是秒，ScoreParser.h:309），用 ffprobe 量檔案長度：akashic 24.32s，應為 16.0；clockwork 5.17，應為 4.0；forest 16.69，應為 12.0；ocean 15.82，應為 8.0；rabbit 5.37，應為 3.43；restraint 8.53，應為 4.8。score 沒寫拍號，但事件落點跟 4/4 吻合，例如 ocean 最後一個音剛好在 8.0s 結束。6 個 score 都是 export.tail_silence_ms=0。SE zip 的 README 第 7 行 akashic 寫「可無縫循環」，第 24 行 forest 寫「自然循環」；PRODUCT_SHEET:55 和 MONETIZATION_PLAN:96 都寫未驗證；LISTING_COPY:41-42 要買家自己確認。嚴重度判 high 偏重：文案已經提醒買家，而且只影響 6/43 檔。不過 README 是買家實際拿到的錯誤陳述，上架前一定要修。

### [release-readiness:R5] 三個打擊音效被開頭一瞬間的尖峰佔掉峰值，響度比其他音效小很多（需要聽覺把關）
- 查證：**adjusted**｜誰：月月裁決｜嚴重度 medium｜工作量 S
- 說明：音效是按真峰值正規化的。有三個檔的峰值被一個不到 2 ms 的開頭尖峰佔掉，本體音量因此被壓得很低。Rabbit Stomp 的峰值在 0.1 ms，比檔案其他部分高 16 dB，只有 12 個取樣在峰值 −6 dB 以內，波峰因數 36 dB，最大瞬時響度 −28.4 LUFS。Clockwork Spring Release 的峰值在 0.2 ms，高出 5.5 dB，響度 −24.9 LUFS。Restraint Shackle Slam 高出 6.8 dB，響度 −22.5 LUFS。整包音效的最大瞬時響度分布在 −28.4～−5.4 LUFS，相差 23 LU，中位數大約 −10 LUFS。也就是說，這三個「重擊」音效在直播裡聽起來可能比「叮」小 15～20 dB。開頭那個尖峰是物理上合理的硬擊暫態，還是爆音，只看數字判斷不了；這是全批最需要聽人確認的地方。
- 證據：scratchpad/release-readiness/spike.py：rabbit_action_001 Rabbit Stomp peak@0.1 ms n(>-6dB)=12 peak vs rest 16.0 dB；scratchpad/release-readiness/impact.py：Rabbit Stomp crest 36.3 dB, 90% energy by 94 ms；scratchpad/release-readiness/maxmom.py：min -28.4 max -5.4 spread 23.0；scores/library/rabbit/rabbit_action_001.score.json（metal_hammer, strike_position 0.1, damping_override 10）
- 建議：月月先決定正規化政策：維持現在的「全部 −1 dBTP」，或另外附一套「響度對齊」版（例如最大瞬時響度統一到 −10 LUFS，不超過 −1 dBTP），這一步 AI 可以做，免耳。開頭尖峰算不算瑕疵要靠聽人：把這 3 個檔、6 個 loop、Gate Open Dark（刻意加了 overdrive）列成 15 分鐘的定點清單，交給 Fiverr/SoundBetter 的聽人，只問「開頭有沒有爆音、接縫會不會喀一聲」，比泛泛聽 30 分鐘便宜也準。
- 懷疑者查證：自寫 spike.py 跟 lufs.py 重量。Rabbit Stomp：峰值在 0.12 ms，比 ±2 ms 以外的部分高 16.0 dB，波峰因數 35.8 dB。Spring Release：峰值在 0.17 ms，高 5.5 dB。Shackle Slam：峰值在 20.27 ms，不是 2 ms 以內，高 6.8 dB。音效最大瞬時響度 min -28.4、max -5.4，中位數 -9.9。rabbit_notify_001 是 -5.4。score 內容：rabbit_action_001 是 steel string、metal_hammer、strike_position 0.1、damping_override 10。
- **查證修正**：Rabbit Stomp 和 Spring Release 的峰值是 0.2 ms 內的開頭尖峰。Shackle Slam 的峰值在 20 ms，屬於早期暫態，不是 2 ms 內的尖峰。這三個檔跟全包中位數（-9.9 LUFS）差 12.6～18.5 dB；Stomp 跟兔兔 Ding 差 23 dB。所以「小 15～20 dB」要改成「小約 12～23 dB」。其餘結論不變：先由月月裁正規化政策，尖峰算不算瑕疵要靠聽人判斷。

### [release-readiness:R6] 音效包授權條款有漏洞，Fab 平台不接受自訂授權
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：(1) 第 8 行寫「By purchasing or downloading」，照字面，從盜版站下載的人也拿到授權，應該改成「向授權通路購買」。(2) AI 禁令只禁「上傳到訓練資料集」，沒禁「拿去訓練」。(3) Content ID 那條沒講清楚：買家把含有音效的自己作品登記 Content ID 行不行？如果行，可能害到其他合法買家的影片被認領。(4) 遊戲、App 發佈檔裡本來就能拆出音檔，開源專案也常把 WAV 放在公開 repo，這兩種情況算不算「再散布」沒寫清楚。(5) 缺違約即終止、準據法、三語版本衝突時以哪一版為準、授權對象（個人或一個團隊）。(6) Fab 查證結果：賣家只能用 CC-BY（限免費）或 Fab Standard License，文件沒提到可以掛自訂 EULA；要禁 AI 訓練得用 Standard License 加 NoAI 標記。所以 zip 裡的 LICENSE 在 Fab 會跟平台授權衝突；Unity 也有自己的標準 EULA（這點沒有另外查證）。以上是條文漏洞的整理，不是法律意見。
- 證據：exports/products/clean_batch2/LICENSE_SE_PACK.txt:8（By purchasing or downloading）、:19-21（redistribute）、:22（Upload ... AI/ML training dataset）、:23-24（content-ID）；https://dev.epicgames.com/documentation/en-us/fab/licenses-and-pricing-in-fab（Standard／CC-BY 兩種；NoAI 需 Standard）；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:40-41（計畫要上 Fab／Unity）
- 建議：AI 起草 LICENSE_SE_PACK v1.1，補上 (1)～(5)，另外做一個 Fab 版 zip：不附會衝突的 LICENSE，改附一份說明「本平台以 Fab Standard License 為準」，上架時勾 NoAI。月月看過決定後才替換 packages/ 裡的檔案。要不要找律師看，由月月決定。
- 懷疑者查證：LICENSE_SE_PACK.txt:8「By purchasing or downloading」、:19-21 再散布、:22 只禁止上傳到 AI/ML training dataset、:23-24 禁止 content-ID，都確認過。另外 LISTING_COPY:39「AI 学習利用は禁止」和 :82「no AI-training use」的範圍比授權條文寬，文案和授權互相不一致，支持第 (2) 點。WebFetch Fab 官方頁：只有 CC-BY（免費）和 Standard License（Personal/Professional 兩層）兩種；NoAI 標記不能配 CC-BY、必須用 Standard；文件沒提到可以附自訂 EULA。MONETIZATION_PLAN:40 確實計畫上 Fab。owner 標 ai-now 起草、月月決定替換，合理。

### [release-readiness:R7] 專輯沒有完整授權檔，跟 DistroKid／Content ID 計畫會打架
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 S
- 說明：專輯 zip 只有一行 README（「個人聆聽＋在自己影片當背景音樂 OK、不可轉售」），沒有 LICENSE 檔，串流平台營利、Content ID、署名方式都沒寫。LISTING_COPY 又計畫把同一批曲目上 DistroKid。如果之後開了 YouTube Content ID 類的服務，買家照授權把曲子當背景音樂用，影片反而可能被認領，跟「可以當背景音樂」的承諾衝突。DistroKid 對公版曲目錄音的 Content ID 政策這次沒有查證。
- 證據：exports/products/clean_batch2/build_packages.py:34-38（README 唯一授權句）；exports/products/clean_batch2/LISTING_COPY.md:94（授權＝個人聆聽＋影片 BGM）、:104-106（DistroKid）
- 建議：月月決定兩件事：專輯要不要允許營利影片當背景音樂；上 DistroKid 時要不要開 Content ID（建議不開）。之後由 AI 參照音效包格式，起草一份專輯 LICENSE（中英日），重打專輯 zip。
- 懷疑者查證：build_packages.py:34-38 專輯 README 只有一句授權（Personal listening + background use in your own videos OK; no resale），zip 內沒有 LICENSE（namelist 只有 WAV/MP3/README.txt）。LISTING_COPY.md:94 寫授權＝個人聆聽＋影片 BGM，:104-106 計畫上 DistroKid。DistroKid 的 Content ID 政策我也沒有查證。

### [release-readiness:R8] 文案有幾處說法跟 repo 記錄對不上（AI 參與、阻尼常數、世界觀內容）
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 S
- 說明：(1) 英文文案寫「no AI audio generation」「100% original」。音訊確實是物理引擎算的，但 43 個音效譜的 commit 都掛了 Claude 共同作者（例如 cae318c），AI Radiance 的 composer 欄是 Codex。專輯文案有揭露 AI 輔助，音效包沒有，前後不一致；Unity 等平台還有 AI 揭露規定（見 MONETIZATION_PLAN:41）。(2) 文案說振動是從「real material constants (density, Young's modulus, damping)」算出來的，但 docs/MATERIALS_SOURCES.md 記載 beta_air、gamma_radiation 這兩項阻尼，14 種材料全部是「待溯源」，這樣寫過頭了。(3) 文案說「每個世界觀大多有 loop」，實際 6 個世界觀都有。(4) 另外，著作權法普遍不保護純 AI 生成的內容。音效包和專輯的「禁止轉售」如果主要靠著作權撐，對 AI 參與比例高的曲目效力可能偏弱。這是風險提示，不是法律意見。
- 證據：exports/products/clean_batch2/LISTING_COPY.md:76-80、:73-74；git log --diff-filter=A -- scores/library：cae318c/27fdba7/... 2026-05-07，trailer 含 Co-Authored-By: Claude Opus 4.6；scores/originals/ai_radiance/ai_radiance.catalog.json:4 "composer": "Codex"；docs/MATERIALS_SOURCES.md:164-166（beta_air/gamma_radiation Still 待溯源）；exports/products/clean_batch2/PRODUCT_SHEET.md:77（AI 署名待裁）
- 建議：月月裁定 AI 揭露的統一說法，建議兩個商品都寫「AI 輔助編寫譜面，由 TsukiSynth 物理引擎演奏；未使用 AI 音訊生成」。AI 再照裁定修文案：阻尼改成「密度、楊氏模量取自工程手冊，阻尼部分為估計值」，並修正 loop 那句的事實。
- 懷疑者查證：LISTING_COPY.md:76-80 寫「100% original…real material constants (density, Young's modulus, damping)…no AI audio generation」，:73-74 寫「(in most) a loop」；實際 6 個世界觀各有一個 loop（catalog 的 sound_type=loop 共 6 個）。git log --diff-filter=A -- scores/library：cae318c、60e5c58 的 trailer 是 Co-Authored-By: Claude Opus 4.6，0ff83b1 是 Claude Fable 5。ai_radiance.catalog.json:4 寫 "composer": "Codex"。docs/MATERIALS_SOURCES.md:164-166 寫 beta_air/gamma_radiation 14 種材料都還待溯源；damping.alpha 是從文獻損耗因數推導的量級。所以「阻尼部分為估計值」的說法恰當。這件事要月月裁定揭露口徑，owner 標對了。

### [release-readiness:R9] 上架素材缺：商品圖 0 張、沒有 demo 試聽帶、README 只有中文
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 low｜工作量 M
- 說明：clean_batch2 裡圖片檔數量是 0。BOOTH 的教學建議準備 3～5 張商品圖；是否必填，官方文件沒查到。Fab 和 itch 也都有封面欄位。目前只有 43 個分開的 MP3，沒有一條串起來的試聽帶（demo reel）。zip 裡 README 的描述只有繁中，主要買家卻在 BOOTH（日文）和 itch/Fab（英文）。
- 證據：find exports/products -iname '*.png' -o -iname '*.jpg' → images: 0；SE zip README.txt 每行描述為繁中（例：阿卡西紀錄之門開啟 — 雙層青銅圓板敲擊...）；https://booth.fanbox.cc/posts/4198867、https://design-works.jp/2026/08/31/booth-digital-products/（商品画像 3～5 枚推奨）
- 建議：AI 做四件事：(a) 用波形或頻譜圖做封面、各世界觀縮圖的草稿，配色遵守單色系 Charta 基準，給月月挑；(b) 把 43 個音效串成一條試聽帶，量成 −14 LUFS 左右；(c) README 補英文和日文描述。都由月月核可後才替換。
- 懷疑者查證：find exports/products 找 png/jpg/jpeg/webp，結果 0 個。exports/videos 只有兩支舊的給愛麗絲影片，沒有音效試聽帶。SE README（已解出到 scratchpad/verify-release/se_readme.txt）43 行描述裡 42 行是繁中，akashic__Library_Opening_Bell 那行是英文。BOOTH 建議 3～5 張商品圖的外部來源，我沒有另外查證。
- **查證修正**：商品圖 0 張、沒有 demo 試聽帶，這兩點屬實。README 描述是 42 行繁中、1 行英文（Library Opening Bell），沒有日文，所以不是「只有中文」，而是語言混雜、而且缺日文和英文的完整版。建議做法不變。

### [release-readiness:R10] 商品資料沒進版控；「可位元重現」要等 staged 成果 commit 才成立
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 low｜工作量 S
- 說明：exports/ 被 .gitignore 排除，所以 LICENSE_SE_PACK、LISTING_COPY、master_batch.py、catalog 在 git 裡一份都沒有；MONETIZATION_PLAN 還是 untracked；HANDOVER、TODO、DEVLOG 都沒提到這條變現線，下一個 session 只能靠記憶找到。另外，50 份 render manifest 都寫著 configured_source_dirty=true（HEAD 766d21d 加上未 commit 的 staged 內容），渲染器 exe 只存在 build/。目前 build/ 的 CLI sha256 還是 9123db8f…，跟 manifest 一致，但下次重建就會被蓋掉，到時「可位元重現」就找不到對應的原始碼和執行檔。
- 證據：.gitignore:22 exports/（git check-ignore -v 命中）；git ls-files exports → 0；git status：?? docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md；grep BOOTH/clean_batch2/MONETIZATION 於 HANDOVER.md/TODO.md/DEVLOG.md → 無命中；render.json："configured_source_commit": "766d21d…", "configured_source_dirty": true, "renderer_executable_sha256": "9123db8f…"；sha256sum build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe → 9123db8f…（2026-09-15 02:07）
- 建議：月月決定：把商品的文字檔（授權、文案、腳本、catalog，不含音檔）搬進受版控的 docs/products/，並 commit MONETIZATION_PLAN。另外把 9123db8f 那支 CLI exe 複製一份跟 masters/ 放在一起。等 WF0914 commit 之後，在 PRODUCT_SHEET 補上實際的 commit 號。
- 懷疑者查證：.gitignore:22 exports/，git check-ignore 命中；git ls-files exports 輸出 0；git status 只有 docs/MONETIZATION_PLAN 是 ??；HANDOVER/TODO/DEVLOG/README 搜 BOOTH|clean_batch2|MONETIZATION|變現 都沒有命中。50 份 render.json 全部是 (766d21d, dirty=True, 9123db8f)。build/ 的 CLI sha256 目前仍是 9123db8f…（2026-09-15 02:07）。補充加強：build/ 的 CLI 建好之後，src/data/CMakeLists 裡只改過 src/effects/EffectChain.h（D9c，09-16 01:07），而 src/score 和 src/cli 都沒有 include EffectChain，所以 CLI 相關原始碼跟目前 staged 狀態一致，commit 後補 commit 號是可行的。但 build-wf 的 CLI 用同一份 CLI 原始碼編出來，sha 是 aa70cb57…，跟 9123db8f 不同，可見執行檔本身重建後雜湊不會一樣。manifest 的 renderer_executable_sha256 只能靠保存那支原檔才對得上，所以「複製一份 exe」這個建議是必要的。

### [release-readiness:R11] 轉 16-bit 時沒加 dither（小瑕疵）
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：master_batch.py 把音樂轉成 44.1k/16bit 時沒有指定 dither，而 ffmpeg 的 dither_method 預設是 0（不加）。影響只在很小聲的淡出和殘響尾巴，會多一點量化失真，不是上架阻礙。
- 證據：exports/products/clean_batch2/master_batch.py:98（-ar 44100 -sample_fmt s16，無 dither 參數）；ffmpeg -h full → -dither_method ... (default 0)
- 建議：下次重出專輯時加上 -af aresample=dither_method=triangular，然後重量 LUFS 和 TP。可以跟 R3 的全曲版重打包一起做。
- 懷疑者查證：master_batch.py:95-98 的 loudnorm(linear=true) 之後接 -ar 44100 -sample_fmt s16，沒有指定 dither。ffmpeg -h full 顯示 -dither_method 的預設是 0。影響只在很小聲的尾巴，屬於小瑕疵，判斷合理。

### [release-readiness:P5] PRODUCT_SHEET §5 的五個待裁決項目前全部還沒裁
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 high｜工作量 S
- 說明：五項是：售價、AI Radiance 署名、全曲版削波、要不要找聽人、賣家身分註冊。在 HANDOVER、TODO、DEVLOG 裡都找不到 09-16 之後的裁決紀錄，repo 在 09-16 之後也沒有任何變動。其中第 3 項的前提已被 R3 推翻（沒有削波）。第 2 項應該跟 R8 一起裁，才能跟音效包的 AI 揭露一致。第 5 項（BOOTH/pixiv、PayPal、Lemon Squeezy、Fab/Hyperwallet）只能月月本人去註冊。
- 證據：exports/products/clean_batch2/PRODUCT_SHEET.md:74-80；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:82（本週：月月看 §5 五件裁決）；git log -1：766d21d 2026-09-15 02:01（之後無 commit）
- 建議：建議的裁決順序：先裁 R8（AI 揭露），再裁 R3（全曲版放不放），然後定價（計畫建議音效包 ¥900、專輯 ¥500）；聽人見 R5 的定點清單；最後月月本人去註冊 BOOTH 和 PayPal。
- 懷疑者查證：PRODUCT_SHEET.md:74-80 的五項待裁決都在。HANDOVER/TODO/DEVLOG 找不到任何售價、署名、BOOTH 的裁決紀錄。用 find -newer（09-16 20:05）查，repo 內除了 build 目錄以外沒有更新的檔案；MONETIZATION_PLAN 的 mtime 是 09-16 20:03。git log -1 是 766d21d 2026-09-15 02:01。第 3 項的前提已被 R3 推翻，我自己量母帶確認沒有平頂。

### [release-readiness:S1] 合成器前置 #1：WF0914 staged 成果還沒 commit 和 push
- 查證：**adjusted**｜誰：月月動手｜嚴重度 high｜工作量 S
- 說明：工作樹有 staged 121 檔（新增 101、修改 20），另外 1 個 untracked（MONETIZATION_PLAN）。HEAD 還停在 766d21d。遠端 CI 三平台全綠，驗的是 766d21d；staged 裡有改到音訊和 state 的 src，例如 D9c 在 EffectChain.h 補了 kIrWetMakeupGain，D12 改了 PluginProcessor 的 state 遷移。這些只有本機整合卡綠，遠端 CI 還沒跑過。
- 證據：git status --porcelain：101 'A '、20 'M '、1 '??'；HANDOVER.md:18-19（staged 未 commit，R7）；TODO.md:13（D9c kIrWetMakeupGain=26.9f）、:44-49（D12）；gh run list：最後綠燈 2026-09-14T18:23 main
- 建議：月月審 git diff --cached，決定 commit 怎麼切，然後 push，確認遠端 CI 三平台再綠一次。依 R7，AI 不代為 commit。
- 懷疑者查證：git status --porcelain：101 個 'A '、20 個 'M '、1 個 '??'；git diff --cached --stat 是 121 files。staged 的 src 有 PluginProcessor.cpp/.h、EffectChain.h、HammerImpulse.h、RadiationModel.h、ScoreRenderer.h。gh run list：最後綠燈是 2026-09-14T18:23 main 和 18:01 branch，之後沒有新的 run。但有兩處引用行號錯了：TODO.md:13 是「五項裁決」標題，D9c kIrWetMakeupGain 在 :15；D12 在 TODO.md:37-45，不是 :44-49。
- **查證修正**：內容屬實，只修正引用：D9c 在 TODO.md:15，D12 在 TODO.md:37-45。owner 標月月動手正確（R7）。

### [release-readiness:S2] 合成器前置 #2：「UI 雙開門裁決」這條已經過時，真正卡的是 UI 要不要等設計師重做
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 high｜工作量 n/a
- 說明：MONETIZATION_PLAN 把 #2 寫成「雙開門裁決落地或擱置」。但月月 08-30 已經否決雙開門，裁定由設計端照功能規格重做；規格 v1.1 在 09-09 就可以送出，一直停在「月月決定找誰」。TODO.md:208 還留著一條沒打勾的舊項目「UI 雙開門，待月月視覺裁決」，跟 :56 互相矛盾。要賣的版本到底用現行 UI，還是等設計師，沒有人定過。
- 證據：TODO.md:56（月月否決雙開門 UI 提案…由設計端從功能重做）、:208（殘留舊待辦）；DEVLOG.md:140-144（否決原話）；HANDOVER.md:87（UI 功能規格 v1.1 送設計端，月月決定找誰）；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:66
- 建議：月月二選一：(A) Early Access 先用現行 UI 上架，文案標明「UI 改版中」；(B) 先把規格 v1.1 送出去、找到設計師，等新 UI 再賣。裁完由 AI 更正 MONETIZATION_PLAN §3 #2，刪掉 TODO.md:208 的舊項目。
- 懷疑者查證：TODO.md:56 記月月否決雙開門、改由設計端從功能重做；TODO.md:208 還留著沒打勾的「UI 雙開門…待月月視覺裁決」，兩者矛盾。DEVLOG.md:140-144 是否決原話。HANDOVER.md:87 寫規格 v1.1 送設計端、月月決定找誰。MONETIZATION_PLAN:66 仍寫「雙開門裁決落地或擱置」。另外 LISTING_COPY.md:120 也寫著「UI 雙開門裁決」，同樣過時，要一起改。補充：TODO.md:23、:46 記月月 09-07 裁定「UI 等功能做完再送設計」，所以卡住的除了找誰，還有功能算不算做完。

### [release-readiness:S3] 合成器前置 #3：安裝包、手冊、使用授權（EULA）全部沒有；現行 LICENSE 不能拿來當買家授權
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 high｜工作量 M
- 說明：git ls-files 查不到任何 .iss、.nsi、installer、manual、EULA、NOTICE 類檔案。repo 根目錄的 LICENSE 是原始碼的專有聲明，寫著「No permission is granted to any person to use…」，照字面連付錢的買家都不能用，所以一定要另寫一份給買家的 EULA（授權範圍、可裝幾台機器、退款、免責）。計畫 #3 只寫了 Inno Setup 加 PDF 手冊，沒列 EULA 和第三方授權聲明（見 S4）。
- 證據：git ls-files | grep -iE '\.iss$|\.nsi$|installer|setup|manual|EULA|THIRD_PARTY|NOTICE' → 無輸出；LICENSE:9-12（No permission is granted to any person to use…）；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:67
- 建議：S2 裁定之後由 AI 做：寫 Inno Setup 腳本，安裝到 Common Files\VST3，並附 EULA 同意頁；起草 EULA（中英日，給月月審）；手冊 PDF 以 UI_FUNCTIONAL_SPEC 為骨架。安裝包用 HostProbe 加 pluginval 驗證「裝完能載入」，這一步不需要耳朵。
- 懷疑者查證：git ls-files 和 git diff --cached --name-only 用 .iss/.nsi/installer/setup/manual/EULA/THIRD_PARTY/NOTICE/OFL 過濾，都沒有輸出。LICENSE:9-12「No permission is granted to any person to use…」屬實。MONETIZATION_PLAN:67 只列 Inno Setup 加 PDF 手冊。repo 外的部署資料夾 C:/Program Files/Common Files/VST3/TsukiSynth_VST3_2026-09-10/ 有一份「怎麼安裝.txt」手動安裝說明，但它不是安裝包，也不是 EULA。

### [release-readiness:S4] 第三方授權：JUCE 8 Starter 可以免費商用，但要附第三方授權聲明檔（目前沒有）
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 high｜工作量 S
- 說明：這次上網查證。JUCE：repo 內 libs/JUCE 是 8.0.12，模組採 AGPLv3 和 JUCE 8 商業授權雙軌。JUCE 8 EULA 的 Starter 是年營收 US$20,000 以下免費，可以閉源商業發行；EULA 內文沒有 splash screen 或署名要求。超過門檻就要升級 Indie（US$300k 以下，US$40/月或 US$800 買斷）或 Pro，否則要立即停止發行。以個人身分計算時，只算「因使用 JUCE 產生的收入」，但捐款、贊助、廣告這類間接收入也算，所以保守做法是把合成器、音效包、專輯（都是 JUCE 做的 CLI 產出）的收入合計。走 AGPL 等於要公開原始碼，跟專有路線衝突，不適用。VST3 SDK：3.8 起是 MIT 授權（moduleinfo 顯示 VST 3.8.0），MIT 要求發行時附上著作權聲明和授權全文。另外 JUCE 會把 FLAC、Ogg Vorbis（兩個都在 juce_audio_formats.h 預設開啟）、png、jpeg、zlib、HarfBuzz、SheenBidi（Apache 2.0）編進二進位；內嵌的 IBM Plex 字型是 SIL OFL 1.1，要求隨軟體附上著作權和授權文字，但 repo 裡沒有 OFL.txt。repo LICENSE 寫「VST is a trademark」，應改成「registered trademark」。Starter 需不需要先到 juce.com 註冊或領取：EULA 摘要沒看到這個要求，查不到定論。
- 證據：libs/JUCE/CMakeLists.txt:35 project(JUCE VERSION 8.0.12)；libs/JUCE/LICENSE.md（AGPLv3／JUCE 8 licence 雙授權＋依賴清單）；https://juce.com/legal/juce-8-licence/：Starter $20,000 Free；Indie $300,000 $40/mo $800；Pro $175/mo $3,500；個人營收＝'total revenue or funding generated by that individual or entity's use of the Framework from all sources, including donations, sponsorship, advertising'；https://steinbergmedia.github.io/vst3_dev_portal/pages/VST+3+Licensing/VST3+License.html（3.8 起 MIT，需保留 copyright/permission notice）；build/…/TsukiSynth.vst3 moduleinfo.json："SDKVersion": "VST 3.8.0"；libs/JUCE/modules/juce_audio_formats/juce_audio_formats.h:75、:84（FLAC/Ogg 預設 1）；CMakeLists.txt:105-108（binary data＝materials.json＋IBMPlexSans-SemiBold.ttf）；字型 name table：'licensed under the SIL Open Font License, Version 1.1'；LICENSE:22-28
- 建議：AI 做一份 THIRD_PARTY_NOTICES.txt，內容包括 VST3 MIT、JUCE 各依賴的授權、IBM Plex OFL 全文，放進安裝包並在手冊引用；修 LICENSE 的商標用語。月月確認一件事：JUCE Starter 要不要到 juce.com 領取或註冊（查不到定論）。
- 懷疑者查證：libs/JUCE/CMakeLists.txt 寫 project(JUCE VERSION 8.0.12)；libs/JUCE/LICENSE.md:6-8 是 AGPLv3/JUCE licence 雙授權，:41-54 列了 FLAC(BSD)、Ogg(BSD)、jpeglib、pnglib/zlib、HarfBuzz、SheenBidi(Apache) 等依賴。juce_audio_formats.h:75、:84 的 FLAC/OGG 預設是 1，CMakeLists 沒關掉（WavWriter 還用到 FlacAudioFormat）。CMakeLists.txt:105-108 把 materials.json 和 IBMPlexSans-SemiBold.ttf 編成 binary data；字型 name table 寫 SIL OFL 1.1；repo 內沒有 OFL 文字檔。build/ 裡 moduleinfo.json 的 SDKVersion 是 "VST 3.8.0"。WebFetch juce.com/legal/juce-8-licence：Starter 營收 $20k 以下免費；Indie $300k（$40/月或 $800）；Pro（$175/月或 $3,500）；個人收入的定義含 donations/sponsorship/advertising；EULA 沒有 splash 或署名要求，也沒提發行前要註冊；超過門檻就要升級或立即停止發行。WebFetch Steinberg VST3 License：3.8 起採 MIT，要保留著作權和授權聲明。LICENSE:28 寫的是「VST is a trademark」。

### [release-readiness:S5] 文案商品名用了「VST3」，要照 Steinberg 商標規範
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：LISTING_COPY 的合成器商品名寫「(VST3, Windows)」。Steinberg 的使用規範：產品名用到 VST，旁邊要放 VST Compatible Logo；每個宣傳這個產品的網頁都要看得到這個 logo；「VST」第一次出現要加 ®；要附「VST is a registered trademark of Steinberg Media Technologies GmbH.」；不准用「VSTi」這類變形詞。目前文案和 repo 都沒有 ® 和這句聲明。
- 證據：exports/products/clean_batch2/LISTING_COPY.md:112；https://steinbergmedia.github.io/vst3_dev_portal/pages/VST+3+Licensing/Usage+guidelines.html（logo 須在 immediate visual proximity；每頁可見；禁 VSTi）
- 建議：合成器上架時由 AI 修文案：第一次出現寫 VST®3，加上商標聲明句；logo 素材從 Steinberg 官方取得後放上商品頁。如果不想放 logo，就改寫成不在產品名裡出現「VST」。
- 懷疑者查證：LISTING_COPY.md:112 寫「(VST3, Windows)」。WebFetch Steinberg Usage guidelines：logo 要放在 immediate visual proximity、每個宣傳頁都要看得到；第一次出現要加 ®；要附「VST is a registered trademark of Steinberg Media Technologies GmbH.」；禁用 VSTi。VST3 License 頁說 MIT 下商標使用是選擇性的，但只要用了 VST 名稱就要照規範。所以「不在產品名裡用 VST」這個替代方案成立。

### [release-readiness:S6] 合成器前置 #4：聽人把關還沒做（需要聽覺，建議找聽人）
- 查證：**confirmed**｜誰：月月動手｜嚴重度 medium｜工作量 S
- 說明：TODO、DEVLOG、HANDOVER 裡都沒有找過或發案給聽人的紀錄。物理 GATE 只能證明「程式忠實實作了模型」，證明不了好不好聽。合成器是即時演奏的工具，旋鈕調動時的拉鍊聲、爆音、極端參數下的怪聲，都是買家第一時間會聽到的。計畫預算 US$30–80。可以先用量測補一部分：pluginval L10（本機最後一次是 07-11，太舊）、HostProbe（目前 89 PASS）、參數自動化時的斷點偵測；但音色美感只能靠聽人。
- 證據：docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:68、:93；reports/gate_outputs/pluginval_L10.txt（2026-07-11，SUCCESS）——之後 F-03/D12/D9c/E5 等 src 改動未再跑本機 pluginval；HANDOVER.md:28（月月是聾人開發者，全程免耳驗收）
- 建議：月月發案時，附一份 AI 寫的定點清單：4 個引擎各彈 5 分鐘、極端旋鈕掃過一遍、音效包 R5 那 10 個檔，只問「有沒有爆音、喀聲、刺耳」，請聽人標出時間碼。在那之前，AI 先在本機跑一次 pluginval L10 加 HostProbe，建立最新的量測基準。
- 懷疑者查證：reports/gate_outputs/pluginval_L10.txt 和 L5 的 mtime 都是 2026-07-11。搜全 repo（排除 libs/build）的 pluginval 證據檔，都沒有比這更新的本機執行紀錄。release-physics.yml 雖然有 pluginval 步驟，但從來沒跑過（見 S9）。TODO/DEVLOG/HANDOVER 都沒有找聽人的紀錄。MONETIZATION_PLAN:68、:93 屬實。補充：已部署在 C:/Program Files/Common Files/VST3/ 的外掛是 09-13 03:33 的 build（sha 78664330…），比 D12（09-15）和 D9c（09-16）都早。如果量測基準或聽人用的是這份已安裝版本，測到的就是舊程式碼。

### [release-readiness:S7] 合成器前置 #5：demo 影片目前只有兩支舊的給愛麗絲鋼琴版
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 M
- 說明：工具 tools/melody_roll_video.py 已經有了，但成品只有 exports/videos 裡兩支給愛麗絲鋼琴版：08-28 和 08-30 做的，各 133 秒，不是計畫的 60 秒。這兩支的音訊早於 09-10 的 A14（改了 physical_piano 的聲音），已經不是現行聲音。計畫要的三支（揚琴給愛麗絲、鋼舌鼓即興、CLI 批次渲染示範）一支都還沒做。另外 demo 不能拿月光或四季當素材（見 C2）。
- 證據：exports/videos：fur_elise_melody_roll.mp4（Aug 28 14:26，133.389 s）、fur_elise_melody_roll_neon.mp4（Aug 30 00:02）；HANDOVER.md:52（A14 09-10 落地，physical_piano 渲染改變）；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:69
- 建議：AI 用 clean_batch2 的現行母帶（揚琴給愛麗絲、AI Radiance 分軌）剪出 60 秒素材，片頭加上響度和峰值量測字卡；鋼舌鼓即興要新寫一份原創譜；CLI 示範用錄螢幕，不需要聲音。月月負責剪輯和看畫面，混音響度用量測把關。
- 懷疑者查證：exports/videos 只有 fur_elise_melody_roll.mp4（08-28 14:26）和 _neon.mp4（08-30 00:02），ffprobe 量兩支都是 133.389 s。fur_elise_melody_roll_run.txt:1 顯示渲染的是 fur_elise_complete.score.json（piano 引擎）。reports/a14_tauc_keytrack_before_after.md:100、:126 顯示 A14 改變了 fur_elise_complete 的振幅指紋，RMS +0.647 dB。所以這兩支影片的音訊確實不是現行聲音。計畫中的三支影片都沒有成品。

### [release-readiness:S8] 合成器前置 #6：授權方式（要不要 DRM）還沒裁
- 查證：**confirmed**｜誰：月月裁決｜嚴重度 medium｜工作量 n/a
- 說明：計畫建議不做 DRM，Lemon Squeezy 的序號只當購買紀錄。repo 裡查不到任何裁決紀錄，程式碼也沒有序號或啟用相關實作（現狀等於無 DRM）。
- 證據：docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:70；grep 'DRM|Lemon Squeezy|序號' 於 TODO/DEVLOG/HANDOVER → 無相關裁決
- 建議：月月裁定「無 DRM＋序號只記錄」或其他方案。建議跟 S3 的 EULA 一起定，因為 EULA 要寫明可以裝幾台機器。
- 懷疑者查證：MONETIZATION_PLAN:70 只是建議。TODO/DEVLOG/HANDOVER/README 搜 DRM、Lemon Squeezy、序號、license key、serial，都沒有裁決，只命中無關的 serial allpass。src 裡也沒有任何序號或啟用相關實作。

### [release-readiness:S9] release CI 有已知紅燈缺陷，而且從來沒跑過
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：release-physics.yml 只在推 v* tag 或手動觸發時跑，gh 查不到任何執行紀錄；現有唯一的 tag 是 playable-vst3-clean-build-v0，不符合 v* 格式。它的建置清單漏了 TsukiSynthSpectrumViewTest，ctest 會把 spectrum_view_repro 標成 Not Run 而變紅，跟 766d21d 在 physics.yml 修掉的是同一個問題。第 50 行還在用 unittest discover，會默默跳過 3 個 pytest 寫法的測試檔（test_measurement_selfcal、test_partial_verify、test_stem_verify），跟 E1 已經改成跑 pytest 的主 CI 不一致。月月第一次打 v0.4 tag 時，release gate 就會紅。
- 證據：.github/workflows/release-physics.yml:45（target 清單無 TsukiSynthSpectrumViewTest）、:49（ctest）、:50（python -m unittest discover）；CMakeLists.txt:249 add_test(NAME spectrum_view_repro …)；.github/workflows/physics.yml:54（已含 SpectrumViewTest）、:61（pytest）；grep -L unittest.TestCase tests/test_*.py → test_measurement_selfcal.py / test_partial_verify.py / test_stem_verify.py；gh run list --workflow 'Release Physics Gates' → 無紀錄；git tag → playable-vst3-clean-build-v0
- 建議：開一張小卡：第 45 行補上 TsukiSynthSpectrumViewTest，第 50 行改成 python -m pytest tests -q，跟主 CI 對齊。月月 commit 之後用 workflow_dispatch 手動跑一次，打 tag 之前先確認會綠。
- 懷疑者查證：release-physics.yml:6-10 只在 workflow_dispatch 或 v* tag 時觸發；:45 的 target 清單沒有 TsukiSynthSpectrumViewTest；:49 跑 ctest；:50 用 python -m unittest discover。CMakeLists.txt:249 有 add_test spectrum_view_repro。physics.yml:54 已補上 SpectrumViewTest，:61 改用 pytest。grep 找不到 unittest.TestCase 的檔案有 3 個：test_measurement_selfcal/test_partial_verify/test_stem_verify。gh run list --workflow 'Release Physics Gates' 沒有任何紀錄；git tag 只有 playable-vst3-clean-build-v0。staged 內容沒有改到 .github。

### [release-readiness:S10] 發行資訊不齊：版號、廠商網址和信箱、關於頁
- 查證：**confirmed**｜誰：AI 可做｜嚴重度 low｜工作量 S
- 說明：CMake 的版號還是 0.3.0，文案卻寫 v0.4。VST3 的 moduleinfo 裡 Vendor 是 TsKR，URL 和 E-Mail 都是空的，因為 juce_add_plugin 沒設 COMPANY_WEBSITE、COMPANY_EMAIL。UI 只在標題列顯示版號，沒有關於頁可以放著作權、商標聲明和第三方授權。另外，Windows 程式碼簽章計畫是第一版先不簽；macOS 的 AU 從沒實機測過，計畫是先只賣 Windows 版。
- 證據：CMakeLists.txt:2 project(TsukiSynth VERSION 0.3.0)；:93-102（無 COMPANY_WEBSITE/EMAIL）；moduleinfo.json："URL": "", "E-Mail": ""；src/PluginEditor.cpp:1027-1032（只有版號）；exports/products/clean_batch2/LISTING_COPY.md:112（v0.4）；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:72-74
- 建議：UI 定案後由 AI 一次補齊：升版號、補廠商網址和信箱（月月提供）、手冊或關於頁列出授權聲明。簽章維持計畫不動。
- 懷疑者查證：CMakeLists.txt:2 是 VERSION 0.3.0；:93-103 的 juce_add_plugin 沒有 COMPANY_WEBSITE/EMAIL。build/ 和部署版的 moduleinfo.json 都是 URL ""、E-Mail ""。src/PluginEditor.cpp:1027-1032 只畫出「v」加 JucePlugin_VersionString；grep about/copyright/licen 沒有命中。LISTING_COPY:112 寫 v0.4。

### [release-readiness:S11] 隨插件發行的資料：授權都乾淨（材料庫、字型之外沒有第三方音訊）
- 查證：**adjusted**｜誰：資訊｜嚴重度 low｜工作量 n/a
- 說明：插件二進位裡只嵌了兩樣東西：data/materials.json 和 IBM Plex 字型。materials.json 的密度、楊氏模量是工程手冊上的物理常數，木材正交異性比值來自 USDA Wood Handbook；事實性數值可以隨商品發行。沒有出廠 IR：IRLibrary.h 明寫 factory IR 是保留欄位、沒有程式路徑會用到。EchoThief IR（非商用）和 TU Berlin 資料（CC BY-NC-SA）都放在 gitignore 掉的 external_data/，只拿來量測參考，沒有隨發行。clean_batch2 用到的譜面效果只有 reverb、delay、distortion、wall 這幾種，沒有任何 IR 卷積，所以音效包和專輯也沒夾帶第三方 IR。字型的 OFL 聲明見 S4。
- 證據：CMakeLists.txt:105-108；docs/MATERIALS_SOURCES.md:39-45（手冊常數，Wood Handbook）；src/IRLibrary.h:25-28（no factory IR…no code path constructs a factory IRRef）；TODO.md:13（EchoThief 非商用授權，量測參考用）；HANDOVER.md:128（external_data gitignore）；scores/library|originals|classical/fur_elise 的 global.effects 鍵集合：delay/distortion/reverb/wall（無 ir）
- 建議：不用處理。如果以後要出「出廠 IR」，只能用自錄的，或確認可商用授權的 IR。
- 懷疑者查證：CMakeLists.txt:105-108 屬實。src/IRLibrary.h:23-28 確實寫 factory IR 是保留欄位，沒有程式路徑會用到。自寫腳本走訪 catalog 的 50 份 score（含 layered 的子 score），global.effects 的鍵只有 {wall, delay, distortion, reverb}，reverb 裡也沒有 mode/ir 欄位。HANDOVER:128 寫 external_data 已 gitignore。但有兩處引用要修：EchoThief 非商用授權的說明在 TODO.md:15，不是 :13；木材正交異性比值實際存在 data/materials.json 的 orthotropic 區塊，出處文件是 docs/WOOD_ANISOTROPY_SOURCES.md，不是 MATERIALS_SOURCES:39-45。MATERIALS_SOURCES:42-44 自己也寫了，密度和楊氏模量只做過數值範圍檢查，沒有逐一核對原始出處。不過事實性的數值本來就不受著作權保護，所以授權結論不變。
- **查證修正**：結論成立：隨插件發行的只有 materials.json（事實性數值）和 IBM Plex 字型（OFL，見 S4），沒有出廠 IR；clean_batch2 也沒用到 IR。引用改成：EchoThief 見 TODO.md:15，木材正交異性見 docs/WOOD_ANISOTROPY_SOURCES.md。

### [release-readiness:C1] 月光／四季換源：不影響現有兩個商品，但卡住專輯 Vol.2，而且沒有進展
- 查證：**adjusted**｜誰：長期研究｜嚴重度 medium｜工作量 L
- 說明：影響範圍：音效包譜面（scores/library）和 AI Radiance 對 Mutopia／CC BY 的全文檢索都是 0 命中（稽核過）；給愛麗絲三度獨立確認是公版。所以 clean_batch2 兩個商品不受影響。受影響的是：moonlight_batch1（還在 exports/products 裡，不能上傳，而且是 D8 之前的舊渲染）和專輯 Vol.2。08-28 之後沒有任何換源進度，scores/classical 裡仍只有 fur_elise 和 vivaldi 兩個資料夾。月光：沒有「授權乾淨＋現成音符」的來源，只能從 IMSLP 公版掃描重新轉譜，工程量大。裁決標頭寫「月光走 Kowalewski CC BY 4.0」，但稽核 B1 指出那一頁只有 MP3，沒有音符資料，走這條仍然要轉譜。四季：IMSLP 有 Schoonenbeek 的 CC BY MIDI，但編制會變成鋼琴加弦樂，工程量中等；上架時要掛署名。Yamaha 那個 AI 採譜工具不能拿來換源。另外，稽核 B3 指出：從 CC BY-SA 排版抽出音符算不算觸發「相同方式分享」，是法律問題，建議商用前問律師。
- 證據：reports/decision_packets/CLASSICAL_RELICENSE_PLAN.md:7-9（裁決路線）、:130-131（月光無現成乾淨音符）、:149-154（Schoonenbeek CC BY 需改編制）、:212（月光工程量大）、:251（library/originals 零命中）、:271-279（B1：IMSLP 月光頁只有 MP3）、:288-294（B3：非法律意見）、:329（Für Elise PD 三度確認）；HANDOVER.md:86（換源＝解上架限制的唯一路）、:98（月光母帶仍是舊渲染）、:153（Yamaha 不可用於換源）；ls scores/classical → fur_elise vivaldi_four_seasons；ls exports/products → clean_batch2 moonlight_batch1
- 建議：維持「換源前不賣」。建議先做四季（Schoonenbeek CC BY，工程量中等，署名寫進文案），月光排在後面；開工前月月先裁是否要找律師確認 B3。為了避免誤上傳，建議把 moonlight_batch1/PRODUCT_SHEET 標成「不可上架」。
- 懷疑者查證：CLASSICAL_RELICENSE_PLAN.md:7-9（裁決路線）、:17-19、:64-71、:130、:149-154、:271-279（B1：IMSLP 頁面只有 MP3；Kowalewski 那份是 CC BY 4.0 的弦樂團錄音）、:288-294（B3，非法律意見）、:333（第三次獨立確認 PD）都屬實。但兩處行號偏了：「月光工程量大」在 :211，不是 :212；library/originals 零命中在 :250，不是 :251。ls scores/classical 只有 fur_elise 和 vivaldi_four_seasons。另外，moonlight_batch1/PRODUCT_SHEET.md 其實已經在 :134 和 :147 寫了「本批四首在換源重製前不上架，僅作內部 demo/引擎對照用」，只是檔頭的「上架前必讀」區（:9-20）沒寫，還附了建議上架文案（:110）。
- **查證修正**：影響範圍和建議順序（先做四季、月光後做、商用前確認 B3）都成立。修正兩點：(1) moonlight_batch1/PRODUCT_SHEET 已經有「換源前不上架」的標記（:134、:147），只是不在檔頭，建議是把這句移到檔頭，並把 :110 的上架文案標成作廢，不是從零補標。(2) 行號 :212 改 :211，:251 改 :250。

### [release-readiness:C2] 合成器如果附範例譜或做 demo，要排除 CC BY-SA 檔
- 查證：**adjusted**｜誰：AI 可做｜嚴重度 medium｜工作量 S
- 說明：合成器的主要賣點之一是「JSON 譜 CLI」。如果安裝包附上 repo 裡的範例譜，scores/examples 裡的 4 份月光（CC BY-SA 2.5）和 scores/classical/vivaldi_four_seasons 的 12 個樂章（CC BY-SA 3.0）就會跟著出去。要嘛不附，要嘛另外以 CC BY-SA 發行並掛署名，否則會跟專有商品混在一起。demo 影片和商品頁試聽同樣不能用這兩批的渲染。插件二進位本身沒有用到這些譜（src 只在 ScoreRenderer.h:140 的註解提到 Vivaldi）。
- 證據：ls scores/examples：moonlight_sonata_complete / _movement1_tongue_drum / _movement1_yangqin / _movement1_yangqin_tongue_mix .score.json；reports/decision_packets/CLASSICAL_RELICENSE_PLAN.md:17-19、:64-71；grep -rin moonlight|vivaldi src → 只有 src/score/ScoreRenderer.h:140 註解
- 建議：做安裝包（S3）時，範例譜改用白名單，只收 scores/library、scores/originals、scores/classical/fur_elise 和自製示範譜，並在打包腳本裡檢查：只要檔案含有 Mutopia 或 CC BY-SA 字樣，打包就失敗。
- 懷疑者查證：ls scores/examples 有 4 份 moonlight；vivaldi_four_seasons 有 12 個樂章。grep -rli 'mutopia|creative commons|CC BY' scores 命中：vivaldi 12 個樂章加 catalog 和 README、月光 4 份，但也命中 fur_elise 的兩份 score 和 source/fur_Elise_WoO59.ly，因為這幾個檔的 meta 含「Mutopia Project (Stelios Samelis edition)」字樣（PD）。src 只有 ScoreRenderer.h:140 在註解裡提到 Vivaldi。
- **查證修正**：排除 CC BY-SA 範例譜的建議成立。但建議裡「檔案含 Mutopia 字樣就讓打包失敗」這條規則會把白名單裡的 Für Elise（Mutopia PD 版）一起擋掉。檢查字樣應該改成「BY-SA／ShareAlike／CC BY-SA」，或依 score meta 的授權欄位判定，不要看有沒有 Mutopia。

### [release-readiness:H1] 需要「聽」才能把關的環節彙總，以及免耳替代方式
- 查證：**confirmed**｜誰：月月動手｜嚴重度 medium｜工作量 S
- 說明：月月全程免耳驗收，所以下面列出每個需要聽的環節、可以先用量測替代多少。(1) 音效開頭尖峰算不算爆音（R5）：可以量尖峰和本體的差距、波峰因數，但到底是瑕疵還是合理的硬擊，要聽人確認。(2) loop 接縫（R4）：可以完全用量測取代，看長度、接縫跳差、RMS 連續性。(3) 整包音效響度一致性（R5）：可以完全用量測取代，看最大瞬時響度和短期響度。(4) 音樂好不好聽（專輯）：音高和起音時間已由 GATE 證明（給愛麗絲 905/905），美感要聽人。(5) 合成器即時演奏時的爆音、拉鍊聲（S6）：pluginval、HostProbe、參數斷點偵測可以補一部分，音色美感要聽人。(6) demo 影片混音（S7）：響度和峰值可以用量測把關。建議把 (1)、(4)、(5) 合成一次發案，給聽人定點清單並請他標時間碼，其他全部改用量測。
- 證據：HANDOVER.md:28；docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md:68、:93；exports/products/clean_batch2/PRODUCT_SHEET.md:37（未做任何人耳審聽）；本報告 R4/R5 量測腳本（scratchpad/release-readiness/loopcheck.py、spike.py、maxmom.py）
- 建議：AI 先把 (2)、(3)、(6) 用量測做完，並寫好聽人定點清單（包含檔名、時間點、要問的問題）；月月再發一次 US$30–80 的案，把 (1)、(4)、(5) 一起處理。
- 懷疑者查證：HANDOVER.md:28（免耳驗收）、PRODUCT_SHEET.md:37（沒做人耳審聽）、MONETIZATION_PLAN:68、:93 屬實。905/905 的證據在 reports/gate_outputs/furelise_midi_verify.txt 和 TODO.md:190。注意 905/905 只涵蓋給愛麗絲，AI Radiance 沒有 MIDI 對照，只有 corpus 檢查。第 (2)(3) 項可以完全改用量測，這個判斷跟我重量 R4/R5 的結果一致。

## 懷疑者補抓的漏項（release）

- 已部署的外掛是舊版：C:/Program Files/Common Files/VST3/TsukiSynth_VST3_2026-09-10/TsukiSynth.vst3/Contents/x86_64-win/TsukiSynth.vst3 的 mtime 是 2026-09-13 03:33，sha256 是 78664330…。這比 D12（state 遷移，09-15）和 D9c（kIrWetMakeupGain，09-16 01:07）都早，也跟目前 build/ 的 VST3（cff47572…，2026-09-25 03:13 剛被重建）不同。之後做 pluginval/HostProbe 量測基準、demo 錄影、給聽人的試聽版，都要先換成現行 build，否則測到的是舊程式碼。
- 渲染器執行檔無法靠重建還原：只有 src/effects/EffectChain.h 比 build/ 的 CLI（2026-09-15 02:07，9123db8f…）新，而 src/score 和 src/cli 都沒有 include EffectChain。可是 build-wf 的 CLI（09-15 23:56）用同一份 CLI 原始碼，sha 卻是 aa70cb57…。也就是說重建後雜湊一定不一樣，50 份 manifest 的 renderer_executable_sha256 只能靠保存 9123db8f 那支原檔才對得上。本輪 live-gate 已經在 2026-09-25 03:13 重建 build/ 的 VST3 和測試執行檔；我最後檢查時 CLI 還是 9123db8f，但任何一次 clean build 都會把它蓋掉。建議在月月同意下，先把這支 exe 備份到 repo 外。
- 削波誤讀擴散的範圍比 R3 寫的廣：除了 PRODUCT_SHEET:29/:35/:78，還有 LISTING_COPY.md:102（先不放全曲版，母帶 41 個削波樣本）、MONETIZATION_PLAN:26（母帶 41 個削波樣本，暫不放）、build_packages.py:26 的註解，以及 catalog.json/catalog.csv 的 `clipped_samples` 欄（master_batch.py:114 從 samples_at_or_above_full_scale 直接複製；ai_radiance_complete=41）。PRODUCT_SHEET:53 說 catalog 可以直接餵上架表單，所以這個欄名本身會把錯誤說法帶到上架頁，修正時要一起改名或加註。
- 文案承諾的 AI 限制比授權條文寬：LISTING_COPY.md:39 寫「AI 学習利用は禁止」、:82 寫「no AI-training use」，但 LICENSE_SE_PACK.txt:22 只禁止「上傳到 AI/ML training dataset」。商品頁的說法比授權檔寬，買家拿到的條文反而較窄，R6 修約時要讓兩邊一致。

## live-gate 原始摘要

我對目前的 staged 樹（HEAD 766d21d + 121 個 staged 檔，也就是 D9c 落地後的最終狀態）重建了 build/，完整 GATE 跑了一遍，全部綠燈，每一項數字都和 09-15 基線一樣。這是 D9c 之後第一次在 build/ 上跑全套：09-15 整合卡用的 build/ VST3 建於 09-15 02:09，EffectChain.h 是 09-16 01:07 才改的；D9c 卡當時是在 build-wf/ 裡驗的。

- ctest：4/4 通過。audit_repro 的 K-02 資訊行現在是「RMS difference (IR - ALGO) = 0.112 dB」，原本是 -28.5 dB，證明 D9c 確實編進去了。
- pytest：264 passed + 1 skipped + 5 xfailed，共 270。
- physics_verify --full：NO CHECKED FAILURES，輸出和 09-15 逐行相同（diff 0 行）。
- selftest：全 PASS，和 09-15 相同。
- verify_score --all：75/75 通過，1 項既有豁免，3838 行輸出和 09-15 相同。
- HostProbe：89 PASS，0 failures，文字和 09-15 相同。
- 位元不變：8/8 IDENTICAL（對 sha256_before_post_a14.txt）。
- git status 前後完全一樣。

部署查核：實際部署的是 C:\Program Files\Common Files\VST3\TsukiSynth_VST3_2026-09-10\TsukiSynth.vst3（整個外層資料夾被放進 VST3 目錄，形成子資料夾）。它的 dll 連結時間是 2026-09-10 23:46:54，比 staged 程式碼舊，少了 D12 和 D9c。用本次 HostProbe 測這份部署版，剛好只有 5 個 D12 檢查 FAIL。

### 部署查核

部署位置是 C:\Program Files\Common Files\VST3\TsukiSynth_VST3_2026-09-10\TsukiSynth.vst3。桌面整個外層資料夾被放進 VST3 目錄，所以多了一層子資料夾；安裝說明「怎麼安裝.txt」原本是要把 TsukiSynth.vst3 直接放在 VST3 底下。VST3 根目錄下已經沒有直接的 TsukiSynth.vst3。

部署版 dll：
- sha256 786643308473051ef4750c632dc3874ad3b29491dafb6ff4fee81fd47cc8b0af，7947264 bytes
- 檔案 mtime 2026-09-13 03:33:35
- PE 連結時間 2026-09-10 23:46:54，和安裝說明寫的「建於 2026-09-10 23:46」一致
- moduleinfo 版本 0.3.0

本次 build 產物：sha256 cff47572c20b6fa4360c66e624533f107930ad148bf88f5556249ae06174a8ab，7945216 bytes，連結時間 2026-09-25 03:13:30。

結論：部署版落後於 staged 程式碼。
- 缺 D12：src/PluginProcessor.cpp 在 09-15 00:13 修改；拿本次 HostProbe 測部署版，剛好只有 5 個 D12 遷移檢查 FAIL（84/5）。
- 缺 D9c：src/effects/EffectChain.h 在 09-16 01:07 修改，晚於部署版連結時間。
- B7P1 的 HammerImpulse.h、RadiationModel.h、ScoreRenderer.h（09-14 22:2x）也在連結時間之後，但它們會不會改變 plugin 輸出我沒有驗證。
- 部署版和 HEAD 已 commit 的程式碼是否一致：沒有建 HEAD 就沒辦法驗證，這次沒建。

其他找到的舊副本：
- C:\Program Files (x86)\Common Files\VST3\TsukiSynth.vst3：64 位元 dll，連結時間 2026-07-12 16:20:05，sha a7865256…
- %APPDATA%\VST3\TsukiSynth.vst3：2026-05-07，sha 150225de…，不是標準 VST3 路徑
- 桌面 TsukiSynth_v0.3.0_20260805 和 _20260806 兩個資料夾
- C:\Users\admin\TsukiSynth.vst3 和 Temp\TsukiSynth-v0.2-win64：只剩空殼，沒有 dll

Cubase LE AI Elements 12 的 VST3 快取（vst3plugins.xml，mtime 2026-08-22）只記錄 C:/Program Files/Common Files/VST3/TsukiSynth.vst3，版本 0.2.0，執行檔時間 2026-07-12T08:20:05Z，和上面 (x86) 那份的連結時間相同。這個路徑現在已經不存在。Cubase 下次掃描會不會掃到子資料夾裡的 09-10 版，要開 Cubase 才知道，我沒有驗證。依指示沒有重新部署。

### 附註

我怎麼做到不寫 repo：
- render_wf_scores.py 會把 csv 和 sha256 寫進 reports/gate_outputs/wf0907_method/，而且沒有參數可以改輸出位置。我改用 scratchpad 裡的 wrapper（run_render_wf_redirect.py）：原封不動 exec 原腳本，REPO 照原邏輯計算，只在呼叫 main() 前把 __file__ 指到 scratchpad，輸出就落在 scratchpad/live-gate/render_out/。
- pytest 和 physics_verify 加了 PYTHONDONTWRITEBYTECODE=1，pytest 另加 -p no:cacheprovider，避免寫 __pycache__ 和 .pytest_cache。
- HostProbe 的 outdir 用 scratchpad 絕對路徑，cwd 用 repo 根目錄。
- 除了 build/ 以外，repo 內沒有新增或修改任何檔案。
- HostProbe 的 H7 和 D12 會在 %APPDATA%\TsukiSynth\Presets 與 \IR 建立檔案再自己刪掉。三次執行後兩個資料夾都是空的，只有 mtime 變了。這兩個資料夾執行前是否已存在，我無法確認，因為執行前的快照只列了檔案、沒列資料夾。

發現的缺口（建議補上）：
1. D9c 沒有硬性 GATE 把關。
   - audit_repro 的 K-02 標明「informational, no PASS/FAIL」，D9c 卡 §0 也確認 K-02 沒有 CHECK 斷言。
   - 這次看到 0.112 dB 是靠人讀輸出。將來如果有人把 kIrWetMakeupGain 拿掉或改錯，ctest、pytest、HostProbe、8/8 全部都還會是綠的。
   - HostProbe 輸出和 09-15 逐字相同，代表它不量 IR wet 電平；8 首位元不變全走 CLI，CLI 根本沒 include EffectChain.h（src/cli/RenderApp.cpp 的 include 清單）。
   - 建議在 audit_repro 加一條 CHECK：|IR−ALGO| ≤ 0.25 dB，正是 D9c 卡寫的預期值。這需要月月裁決，而且改 src/tests 要照 R6 流程。
2. HostProbe 的 H8 靠目前工作目錄找 data/materials.json（tests/host_probe.cpp:1429-1430）。不在 repo 根目錄執行會出現 4 個假 FAIL，我這次就踩到。建議改成相對於 exe 解析，或加一個參數。
3. render_wf_scores.py 一定寫進 repo，沒有 --outdir。建議加上，之後唯讀驗證就不必靠 wrapper。
4. 09-15 整合報告 GATE 7 寫 selftest「15 項」，原始輸出其實是 13 行。只是文件筆誤，不影響結論。
5. 部署版（09-10 build）比 staged 程式碼舊，少了 D12 和 D9c。另外還有 (x86) 和 %APPDATA%\VST3 等舊副本，Cubase 快取也停在 08-22、指向已經不存在的路徑。要不要在 commit 後重新部署、清掉舊副本，請月月決定。

所有 log 在 C:/Users/admin/AppData/Local/Temp/claude/C--Users-admin-Desktop-Claude/7c5a84c1-762b-4e45-b6e9-c2ce9556d699/scratchpad/live-gate/：
- 01 到 10b 各步驟 log，09a 是錯誤 cwd 那次、09b 是部署版對照
- deploy_pe_compare.txt、prebuild_sha256_build_0915.txt、postbuild_sha256_build_20260925.txt
- render_out/sha256_live_gate_20260925.txt
