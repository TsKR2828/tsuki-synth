# TsukiSynth 深度修復與驗證報告（2026-07-17）

## 結論

本輪已把先前深掃找到的可實作問題放在 `fix/deep-physics-audit-20260716` 分支逐項修正。調音器不再把目標音當成量測值；梁／板邊界、最終頻率阻尼、泛音振幅生命週期、score 嚴格契約、隨機種子、FX 一致性、layer／batch／preset 與逐事件協和度等路徑都有可執行回歸測試。最終 release corpus 為 73/73 通過，沒有新增豁免。

目前可以證明的是「實作遵守已寫下的方程與契約」。尚不能證明「每一組材質常數與任一真實樂器個體完全一致」，也沒有校準到絕對 SPL。這兩件事不得混為一談。

## 調音器測試方法

### C++ 實際演算法測試

執行：

```powershell
cmake --build build --config Release --target TsukiSynthTunerTest
build\Release\TsukiSynthTunerTest.exe
```

方法：

- 直接呼叫與 UI 相同的 `PitchDetector`，不是 Python 另寫一個替代演算法。
- 對 A0–C8、44.1/48/96/192 kHz 測純音與舌片／鑼的非諧模態混合。
- 注入已知的正負 cent 位移，確認顯示來自音訊而不是 MIDI target。
- 注入 0.5×／2× 八度替代、靜音、寬頻噪聲與範圍外目標，必須拒絕而不是猜測。
- 驗證低音收集六個週期、A0 首次判定的等待時間，以及無分析期配置。
- 驗證 retrigger、跨 MIDI channel、sustain 與 CC120/121/123 的 target 狀態。

### 獨立 Python oracle

```powershell
python tools\tuner_audit.py
python tools\tuner_audit_v2.py
```

結果：A0–C8 共 1056 個量測案例通過，160 個範圍外案例明確拒絕；獨立 oracle 最差誤差 0.2076 cent。三個已知位移、八度替代與靜音拒絕皆通過。

限制：目前是 target-aware 單音量測。多聲部、強殘響、目標基頻缺失時會選擇 `Uncertain`，不承諾多音高分離。

## 泛音、頻率與衰減測試方法

```powershell
python tools\physics_verify.py --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --selftest
python tools\physics_verify.py --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --full
python -m unittest tests\test_physics_verify.py tests\test_consonance_contract.py tests\test_verify_score_contract.py -v
```

`--selftest` 先對合成的反例驗證量尺本身：缺模態、重複配對、噪聲假峰、錯誤振幅、錯誤 T60 與錯誤非諧容差都必須讓 gate 失敗。這可避免「被測程式與測試工具犯同一個錯」仍顯示綠燈。

`--full` 的量測流程：

1. 用 CLI `--dump-modes` 取得 C++ 模型預測的頻率、相對振幅與 T60。
2. 實際渲染 24-bit 音訊；24-bit 用於避免 C8 的弱第二模態被 16-bit 量化底噪吞掉。
3. 頻譜峰必須有 prominence、噪聲底線與一對一指派；缺少必要模態即失敗。
4. 前五個有效 partial 以隔離的理論訊號比較相對 dB，容差 ±3 dB。
5. T60 以測得 f0 附近 ±3% 窄頻、Hilbert envelope 與 log-slope 擬合；多弦先平均至少一個拍頻週期。
6. 材質掃描只證明參數有作用且實作符合模型；不把它稱為真實材料驗證。

最新結果：

- 六個引擎宣告音域的必要模態：PASS。
- 五個 modal 引擎的 velocity、前五 partial 相對振幅與 10 個 T60 probe：PASS。
- T60 measured/model 約 0.99–1.00。
- 24 個可量測材質案例：PASS。
- `cimbalom/rubber`、`tongue_drum/rubber`、`water_gong/rubber`：`UNVERIFIED/N/A`。其 T60 僅 0.014–0.028 秒，小於 MIDI 60 八週期所需 0.031 秒；沒有假裝成 PASS。

## 模型／DSP C++ 回歸方法

```powershell
ctest --test-dir build -C Release --output-on-failure
```

三個測試程式分別涵蓋：

- `audit_repro`：parser 負例、材質交易式載入、FIFO、事件尾巴、FLAC、layer trim/master、reverb 首次回應。
- `tuner_repro`：實際調音器與 MIDI target 狀態機。
- `physics_models_repro`：cantilever/free-free 節點與比例、plate 節點／Poisson、MIDI/geometry 模式、最終頻率阻尼、槌擊頻譜真零點、弱模態 −60 dB、PCG seed、5 秒 delay、零時間 delay、reverb T60 與 plugin/CLI FX 靜態一致性。

## Score、schema 與批次測試方法

```powershell
python tools\verify_score.py --all --quiet --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe
```

每份 event score 會做 Draft 2020-12 schema、C++ `--dump-modes`、實際渲染、休止 RMS、峰值／連續 clipping、render manifest 與兩次 SHA256 determinism。Layered composite 的頂層 mode scan 明列 `N/A`（CLI 不定義 flattened event identity），再遞迴驗證每個 leaf score 並逐 leaf mode-scan；缺檔、逃逸路徑、cycle、sample-rate drift 或 leaf 失敗仍會令整份 composite 失敗。另以負例測未知 engine/key、錯型別、fractional/out-of-range MIDI、無作用參數、假 `membrane`、不合法 boundary／frequency mode。

批次另外預檢：自然排序、大小寫不敏感的輸出碰撞、不安全 filename、既有輸出／manifest、未知材質／exciter與 layer path/source/sample-rate。預檢失敗時不應先留下前幾份輸出。

所有 80 個 repository `.score.json` 已通過 schema。Release corpus 以四個平衡分片重跑：34/34、18/18、16/16、5/5，合計 **73/73 PASS、0 FAIL**；既有 moonlight FX 藝術意圖的 1 個 `rests.rms` 登記豁免保持可見，沒有新增豁免。

這次 corpus 也找出並關閉兩個問題：`ai_radiance_complete` 的 layered 頂層 mode-scan 契約錯配；以及 Vivaldi Summer m3 在新 reverb T60 下唯一休止窗超標。後者固定 wet=0.2 掃描 decay 1.8/1.5/1.3/1.2/1.1/1.0 s，實測 −43.02/−46.93/−50.44/−52.60/−55.10/−58.07 dBFS；選 1.2 s 後完整 verifier 的同窗為 −52.6 dBFS，比 −50 dBFS 門檻多 2.6 dB 裕度，未調寬容差。

## 逐事件協和度測試方法

```powershell
python tools\consonance.py
python tools\check_piece_consonance.py scores\originals\rules_v2_demo\rules_v2_demo_001.score.json --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --out reports\rules_v2_demo_consonance_check.md
```

`consonance.py` 產生固定 MIDI 60 的設計參考表；成品驗收不直接套表。Checker 對每對宣告時間重疊的事件讀真實 C++ modes（所有 active strings、材質、幾何、邊界、敲點、body magnitude 與速度相依槌頻譜），在實際音域重建 Sethares roughness curve；實際 interval class 距最近局部極小值 ≤10 cents 才 PASS。FM／Custom 明列 `UNVERIFIED-DOMAIN`；宣告 duration 後的共鳴尾巴與八度等價假設也寫進報告。示範曲結果：13 PASS、0 VIOLATION、0 UNVERIFIED。報告包含 score、checker、公式工具與 CLI SHA256。

## 建置方法

```powershell
cmake --build build --config Release --target TsukiSynthCLI TsukiSynth_VST3 TsukiSynth_Standalone TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest
```

建置必須使用目前工作樹重新編譯，不能只執行舊 binary。VST3、Standalone、CLI 與三個測試 target 都是 release gate。

## 本輪主要修正

- 調音器：乾訊號量測、A0–C8、範圍／信心拒絕、最新 FIFO、MIDI sustain/retrigger。
- 物理：舌片 cantilever、明確 free-free、板的 Bessel/modified-Bessel 模態形狀、Poisson free-edge roots、geometry absolute frequency、最終頻率阻尼、速度相關接觸時間、相對 −60 dB 模態終止。
- 可重現：指定 PCG32、score seed + event index、render manifest；同環境可重現但不誇稱跨平台 bit-exact。
- Score：嚴格 schema/C++ 契約、拒絕 silent aliases/no-op、custom partial 真正接線、精確事件 identity、由模型／FX 推導尾巴。
- 驗證工具：layered 頂層 mode scan 明列 N/A 並逐 leaf 驗證；協和度改為 event-specific，不再固定方向或覆蓋其他 score 的報告。
- 工程：layer 路徑與 1 GiB 工作集、in-place trim、batch 預檢、atomic WAV、preset stable ID/cache、效果鏈一致與參數平滑。

## 距離最終目標的落差

1. 材質：`alpha` 只有錨點校準；`beta_air`／`gamma_radiation` 尚未逐材質溯源或量測，橡膠短瞬態尚無可靠估計器。
2. 絕對量：目前振幅是相對／正規化值，沒有槌力 N、位移 m、聲壓 Pa、dB SPL 的完整校準鏈。
3. 結構耦合：沒有音板、琴橋、琴箱、空氣腔、其他弦、踏板與 damper 的耦合模態。
4. 非線性：接觸時間仍由硬度表與速度律近似，不是以槌質量／氈壓縮曲線解出的接觸力；水鑼的水體耦合也只是 creative glide。
5. 空間：沒有 modal phase、pickup/mic 位置、方向性、房間邊界與 binaural/多聲道物理。
6. 真實世界驗證：需要獨立量測資料、試體尺寸／材質、環境條件與不確定度，不可只用程式自己的 `--dump-modes` 當唯一 oracle。
7. 產品驗證：跨 OS/compiler reproducibility、真實 DAW host、長時間 real-time 壓力、聾人可讀性與操作測試仍需外部驗收。
8. 範圍：FM Piano 與 creative effects 並非物理樂器；若產品要宣稱「樂器物理正確」，必須維持清楚標籤或另建物理模型。
9. 感知模型：Sethares roughness 是可重現的心理聲學模型，不等於所有人的音樂協和感，也不是樂器結構方程；仍需聾人可讀性研究與不同聽覺族群的外部驗證。
