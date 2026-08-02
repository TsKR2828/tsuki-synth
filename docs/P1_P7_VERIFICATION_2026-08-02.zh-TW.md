# P1–P7 修復與驗證紀錄（2026-08-02）

## 結論

本輪不是用聽感驗收。所有已完成項目都由物理不變量、數值量測、位元雜湊、反例或獨立 plugin host 判定。

| 階段 | 修復／gate | 結果 |
|---|---|---|
| P1 | 真實 DSP band 與 attack-only 假 PASS | PASS |
| P2 | 遞迴 layer provenance／manifest v4 | PASS |
| P3 | 語意事件身分／順序穩定 seed | PASS |
| P4 | 44.1–192 kHz 共用合約 | PASS |
| P5 | 量綱、被動性、因果性、疊加、非法數值、反例 | PASS |
| P6 | ASan、pluginval、Steinberg validator、完整 corpus | PASS |
| P7 | 實物量測 schema／證據鏈／保守不確定度判定器 | 軟體 PASS；真實標本資料尚未提供，不能宣稱 specimen PASS |

最終本機結果：Release 六 target build；CTest 3/3；Python 84/84；ASan 3/3；`physics_verify.py --full` 無 checked failure；pluginval L10 SUCCESS；Steinberg validator 47/47；完整曲庫 73/73、0 fail、1 筆既有明示豁免。

## P1：可渲染模態與假 PASS

### 修復

- 可渲染頻帶集中定義為 `20 Hz <= f <= min(20000 Hz, 0.49 * sample_rate)`。
- `ModalResonator::setModes()` 過濾超出 DSP 實際可產生範圍的 mode。
- 頻率／振幅／T60 非有限、振幅為零、或所有 mode 都不可渲染時，voice 不得保持 active。
- renderer 遇到「modal event 有 velocity、卻沒有 render-active modal energy」直接拒絕，不輸出只有 exciter attack 的 WAV。
- verifier 對無可量測 f0 回 `N/A`，但另有 `render_active_energy` FAIL；不能把 N/A 顯示成 f0 PASS。

### 測試方法

- 邊界值：19.99 Hz 必須拒絕；20.00 Hz 必須接受；高端邊界與 0.98 Nyquist 完全相同。
- 幾何反例：10 m 長、0.1 mm 厚的舌片使所有 mode 低於 20 Hz；render 必須失敗且訊息指出 frequency band。
- 零振幅反例：頻率合法但總 active energy=0，Python contract 必須 FAIL。
- NaN／Inf mode：輸出每個 sample 都有限且 voice inactive。

## P2：分層 score 完整證據鏈

### 修復

Manifest v4 包含：

- WAV SHA256、CLI executable SHA256、版本／commit／dirty／compiler／target／configuration。
- 根 score 與每個遞迴 layer 的 `role`、相對 `path`、SHA256。
- 以固定格式 `role<TAB>path<TAB>sha256<LF>` 建立 canonical dependency tree，再計算 `dependency_tree_sha256`。

### 測試方法

- v4 正例：根 score + child layer 的精確清單與 tree hash 一致。
- mutation：render 後改 child bytes，即使根 score 與 WAV 沒改也必須 FAIL。
- 舊版反例：layered score 搭配只綁 root 的 v3 manifest 必須以 provenance incomplete 拒絕；不能因向後相容而假綠。
- 實際 `layered_transition.score.json`：3 個 dependency file 全部驗 hash，雙 render SHA256 相同。

## P3：語意事件身分與位元重現

### 修復

- seed material 使用固定欄位順序、明確 little-endian 的二進位 encoding 與 FNV-1a 64-bit；不使用陣列 index、locale 或 `std::hash`。
- 可選 `event_id` 為 AI 編輯提供穩定主鍵；必須非空且全 score 唯一。
- 沒有 `event_id` 時使用事件的完整物理／演奏語意；完全重複事件另加 deterministic duplicate rank。
- render plan canonical sort；`velocity:0` 不 render、不延長音檔，也不影響其他事件 seed。

### 測試方法

- 把兩個同時事件在 JSON 內交換順序；兩份 WAV 必須 byte-for-byte 相同。
- 插入一個位於 10 秒的 `velocity:0` 事件；WAV 長度與 bytes 必須完全相同。
- 兩個事件使用相同 `event_id`；parser 必須拒絕。
- 相同 seed + 相同語意事件的 PCG noise 必須精確重現；不同語意事件不得取得同一 coherent noise stream。

修復前的兩個 focused probe 並非 byte-identical：同時事件交換的差異約 -90.44 dBFS、
插入 silent event 的差異約 -102.99 dBFS；修復後兩者皆為 exact byte match。由於 seed
由 index 遷移成 semantic identity，即使 score 不改，本版相對舊 binary 的 exciter/noise
attack bytes 也可能改變；這是修復本身的預期遷移，modal frequency／amplitude／T60 方程
沒有因此改變，舊 WAV SHA256 不可當成本版 golden hash。

## P4：共用取樣率合約

支援集合固定為：44100、48000、88200、96000、176400、192000 Hz。schema、parser、renderer 與 tuner test 共用同一個 C++ contract；頻帶上限隨 Nyquist 收斂。

### 測試方法

- 同一個真實 beam/tongue physical event 在六率逐一 render，輸出檔必須能讀回且 sample rate 正確。
- tuner 以全部六率跑 A0–C8／支援與拒絕區：528 組 measured、240 組因解析度／週期不足誠實 refused。
- pitch sweep 最差誤差 0.0007 cents；modal boundary 最差 0.3965 cents。

## P5：不是範例輸出，而是物理／數值不變量

### 量綱縮放

- Euler–Bernoulli beam：`f ∝ L^-2`、`f ∝ thickness`、`f ∝ sqrt(E)`、`f ∝ rho^-1/2`。
- Kirchhoff circular plate：`f ∝ R^-2`、`f ∝ thickness`、`f ∝ sqrt(E)`、`f ∝ rho^-1/2`。
- 每次只變一個輸入並比對理論 ratio；這能抓到單位錯誤、漏平方與錯用材料常數。

### 被動性與數值安全

- 無外力 modal resonator 每隔一個完整週期量能量；必須單調下降。
- NaN／Inf frequency/amplitude/T60 進入 resonator 必須 fail closed，不能傳播 NaN 或留下 active voice。
- 超大但 schema-valid 的 86400 秒、192 kHz score 必須在配置前被 1 GiB buffer budget 拒絕。

### 因果性與局部性

- 事件時間 0.2 s：0–0.2 s 每個 PCM sample 必須精確為零。
- 在 0.5 s 加入未來事件：0–0.5 s 的既有輸出必須 bit-exact 不變。
- FX 關閉時 render(A+B) 與 render(A)+render(B) 逐 sample 比較，誤差限 2e-6（涵蓋 32-bit PCM quantization）。

### mutation-style 反例

`physics_verify.py --selftest` 主動注入：50% 錯頻、缺 partial、超 Nyquist、同一 peak 被重複配對、partial +6 dB、velocity +9 dB、T60 span 不足／NaN、未建模強峰。每個反例都必須被原本的 production judgment 拒絕，不使用測試專用寬鬆判定。

## P6：發布與 host gate

### 自動化層次

- 一般 push/PR：Release build、CTest、Python contract/selftest、`--full`、代表 score、consonance，加一個獨立 MSVC ASan job。
- tag／手動 release：在上述 gate 之外，執行兩個外部 VST3 host，再以四個 runner 驗完整 73-score corpus。

### 外部 host 的實測設定

- pluginval v1.0.4；下載 ZIP SHA256 固定為 `c08e61ce3b96db41636f8ec7e76f4c7e2c13ebdac7fa1b5a1f52b4f32ec715ab`。
- strictness 10；sample rates = 44100/48000/88200/96000/176400/192000。
- block sizes = 1/2/3/7/16/31/64/127/256/511/1024；random seed `0x5453554b`；timeout 60000 ms。
- Windows 上用 `Start-Process -Wait -PassThru` 取得真正 child-process exit code，避免 GUI-subsystem 主程序提早返回的假 PASS。
- Steinberg VST3 SDK commit `58f8da7936800732561402d7936584ca4505de07`，只建 official `validator` target；本輪 47 passed／0 failed。

完整 corpus 使用 sorted list round-robin：`files[index::count]`。本輪四 shard 花費約 403.9–531.5 秒，結果 73/73；每首包含兩次 render 的 determinism 比對。

## P7：真實標本驗證入口

詳細實驗 SOP 見 [SPECIMEN_VALIDATION_PROTOCOL.zh-TW.md](SPECIMEN_VALIDATION_PROTOCOL.zh-TW.md)。

### 工具會驗什麼

- Draft 2020-12 schema、日期格式、有限數字、唯一 partial mapping。
- raw excitation、raw response、hammer/shaker calibration、response calibration、uncertainty analysis 的存在、相對路徑限制與 SHA256。
- Mode Dump v2 SHA256、event `source_index` 與 model observable contract。
- minimum mode count、每個 mode 的 coherence。
- frequency conservative error：中央相對誤差 + measurement expanded uncertainty + model relative uncertainty。
- relative-magnitude conservative error：相對參考 mode 的中央 dB 誤差 + measurement/model dB uncertainty。
- T60：measurement 與 model uncertainty interval 的最壞雙向 ratio。

### 狀態語意與反例

- PASS=0；FAIL=1；REFUSED=2（schema／hash／NaN／證據鏈無效）；UNVERIFIED=3（模型缺 observable）。
- 單元測試包含：三項支援量精確正例、+10 Hz 錯頻、低 coherence、raw artifact tamper、NaN、要求缺失 phase。
- 最後一例一定要回 UNVERIFIED，證明工具不會以 `phase=0` 或缺值代替真正複數 FRF。

## 重跑命令

```powershell
cmake --build build --config Release --target TsukiSynthCLI TsukiSynth_VST3 TsukiSynth_Standalone TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest
ctest --test-dir build -C Release --output-on-failure
python -m unittest discover -s tests -p "test_*.py" -v
python tools\physics_verify.py --selftest
python tools\physics_verify.py --full

# 四個 index 都要跑；CI 會平行執行
python tools\verify_score.py --all --shard-index 0 --shard-count 4 --cli build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe

cmake -B build-asan -DTSUKI_BUILD_TESTS=ON -DTSUKI_ENABLE_SANITIZERS=ON
cmake --build build-asan --config RelWithDebInfo --target TsukiSynthAuditTest TsukiSynthTunerTest TsukiSynthPhysicsModelsTest
tools\run_asan_ctest.ps1

python tools\specimen_verify.py specimen\measurement.json --dump-modes specimen\modes.json --json-out specimen\report.json
```

## 仍然誠實未完成的物理主張

- 目前沒有真實標本 bundle，因此本輪沒有 specimen-level PASS。
- 三個 rubber case 的 T60 短於八個可觀測週期，維持 `UNVERIFIED/N/A`。
- 複數 modal phase、力→位移→輻射聲壓、絕對 SPL、多點 radiation directivity、聲板／琴體耦合仍未進入模型。
- 同平台／build 的位元重現性已驗；跨 CPU／compiler／OS 尚未定義可接受的數值或音訊容差。
