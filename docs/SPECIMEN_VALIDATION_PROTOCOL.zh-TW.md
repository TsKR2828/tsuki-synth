# 實物標本物理驗證流程（P7）

這個流程讓聾人與 AI 不靠聽感，把「程式照自己的方程式運作」與「方程式符合某一件真實樂器」分開驗證。前者由 C++／Python gate 處理；後者必須使用真實標本、校正過的感測器與保留原始資料，不能拿合成波形代替。

量測端 v2 已能自動產生複數相位、校正後的 Pa/N、指定 RMS 力下的 SPL 與複數空間指向性，驗證器也已具備相應比較器。現行合成器 Mode Dump v2 仍只輸出模態頻率、相對模態振幅與模態 T60；因此目前要求 phase、SPL 或 radiation 時仍會正確回報 `UNVERIFIED`（exit 3），直到模型端真正輸出對應物理 observable 為止。量測資料存在不代表模型預測存在，兩者不可混為 PASS。

## 1. 最低硬體與校正

- 具力感測器的 impact hammer 或有力回授的 shaker。
- 一個校正過的反應感測器：加速度計、雷射測振儀或量測麥克風。
- 兩個同步輸入通道；取樣率至少覆蓋要驗的最高模態，建議 96 kHz 或 192 kHz。
- 力與反應感測器的有效校正證書。量測前後都要記錄序號、靈敏度、單位與校正日期。
- 可重現的邊界條件：夾具、懸掛點、夾持扭矩、敲擊點、敲擊方向、反應點都使用公尺座標記錄。

## 2. 量測程序

1. 量測標本幾何、材料批號、溫度、相對濕度與氣壓。模型使用的 E、ρ、ν 不可只抄資料庫名目值；若未實測，必須把來源與不確定度寫進 uncertainty budget。
2. 固定標本並拍照／畫座標圖。邊界條件有任何重裝都視為另一輪量測。
3. 每組 excitation／response 點至少取得 8 次有效敲擊；double hit、overload、飽和或非因果 pre-trigger 必須剔除並留下紀錄。
4. 由多次量測計算 H1 FRF：`H1 = G_yx / G_xx`；coherence：`|G_yx|² / (G_xx G_yy)`。不得用單次資料的固定 coherence=1 代替。
5. 對每個模態保存頻率、相對振幅、相位、T60、coherence 與 expanded uncertainty。T60 要從隔離後的自由衰減取得，並保存擬合區間與殘差。
6. 至少重裝一次標本並重測，以把夾持／懸掛重現性納入不確定度。若只量一次，不能宣稱 specimen-level 可重現。
7. 保存原始 excitation、raw response、兩份 calibration、uncertainty budget；建議另存衍生 H1 FRF。工具會逐檔驗 SHA256，路徑必須位於 bundle 目錄內。

## 3. 自動產生 v2 bundle（建議流程）

實體現場只需完成標本／夾具／感測器安裝、校正器前後套用，以及把儀器靈敏度和座標填入設定；激振可以交給 shaker 或機器致動器，不要求人工敲擊，也不要求靠聽力判斷。以下工作由 `tools/specimen_pipeline.py` 完成：

- CSV 時基、NaN／Inf、過載與 impact double-hit 檢查。
- 電壓依力感測器、結構感測器靈敏度轉為 SI。
- 由校正器前後錄音自動算出麥克風 V/Pa、音調正確性與靈敏度漂移。
- 多次獨立紀錄的 H1、coherence、複數值與去除通道延遲後的相位。
- 頻帶隔離、Hilbert envelope、dB 線性回歸與 T60／R²；impact 使用量得的自由衰減，shaker FRF 則先轉成 impulse response。
- 聲壓／力 `P(f)/F(f)`、`dB re 20 µPa/N`、指定 `reference_force_rms_n` 下的 SPL。
- 每個 `(radius, azimuth, elevation, partial)` 的複數指向性資料。
- 重複量測的 expanded standard error、設定的不確定度 floor、所有證據的 SHA256。
- 建立可攜、自包含且可重新執行分析的 bundle；輸出目錄已存在時會拒絕覆寫。

先複製兩個模板：

```powershell
Copy-Item specimens\templates\measurement_v2.template.json work\measurement.json
Copy-Item specimens\templates\acquisition.template.json work\acquisition.json
```

Pipeline 會先依 [Specimen Acquisition v1 schema](../specimens/schema/specimen_acquisition.schema.json) 拒絕未知欄位、缺少的通道或錯誤型別，再讀取任何量測資料。

原始 CSV 每個檔案代表一次獨立紀錄。結構紀錄至少包含：

```text
time_s,force_v,response_v
0.000000,0.000012,-0.000003
...
```

聲學紀錄至少包含：

```text
time_s,force_v,microphone_v
0.000000,0.000012,0.000001
...
```

校正器 before／after CSV 至少包含 `time_s,microphone_v`。每個 `path` 代表一份紀錄，也可用 `path_glob` 自動展開一批檔案。H1/coherence 的數學最低需求是每組兩份獨立紀錄；正式模板的 `minimum_averages` 預設為 8，結構與每個指向座標都不足 8 份時會拒絕。不可把同一筆資料複製多份冒充 averages。

在 `acquisition.json` 內填入：

- `channels.force.sensitivity_v_per_n`。
- `channels.structural_response.sensitivity_v_per_si`；SI 量由 measurement 的 `response_quantity` 說明。
- 各通道 `polarity`、`delay_s`、DAQ `full_scale_v`。
- 每份 structural／acoustic CSV；聲學紀錄另填 radius／azimuth／elevation。
- calibrator before／after、校正器標稱 dB 與頻率。
- 力、反應、麥克風／校正器的可追溯校正證據檔。
- 預先鎖定的頻率搜尋寬度、T60 擬合範圍、容差與 uncertainty floor。

執行：

```powershell
python tools\specimen_pipeline.py work\acquisition.json --out work\specimen-bundle
python tools\specimen_verify.py work\specimen-bundle\measurement.json `
  --json-out work\specimen-bundle\verification-report.json
```

bundle 會包含：

```text
specimen-bundle/
├─ measurement.json
├─ verification-report.json
├─ raw/                         # 原始同步紀錄與 calibrator 前後資料
├─ calibration/                 # 複製進 bundle 的證書／校正證據
├─ config/
│  ├─ acquisition-source.json  # 原始設定
│  ├─ acquisition.json         # 路徑改成 bundle 內部，可重跑
│  └─ measurement-template.json
├─ model/modes.json
└─ analysis/
   ├─ structural-h1-frf.csv
   ├─ acoustic-transfer.csv
   ├─ microphone-calibration.json
   └─ uncertainty-budget.json
```

自動處理器不會替缺少的證書、實體座標、夾具重現性或材料不確定度編造數值；缺證據、漂移過大、double hit、過載、T60 擬合品質不足時直接拒絕產生 bundle。

## 4. 產生模型預測

先讓 score 只包含要比對的標本事件，關閉 reverb、delay、distortion 與 wall：

```powershell
cmake --build build --config Release --target TsukiSynthCLI
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --dump-modes path\to\specimen.score.json > path\to\modes.json
Get-FileHash -Algorithm SHA256 path\to\modes.json
```

把輸出的 hash 寫進 `model.mode_dump_sha256`，把事件原本的陣列位置寫進 `model.event_source_index`。Mode Dump v2 內的 `source_index` 是選擇事件的機器可讀依據。

當模型端日後實作相位與輻射算子時，verifier 已鎖定以下預測介面；不得從 measurement 回填這些數值：

```json
{
  "model_observables": [
    "modal_frequency_hz",
    "relative_modal_amplitude",
    "modal_t60_s",
    "complex_phase",
    "absolute_pressure_per_force",
    "radiation_directivity"
  ],
  "events": [{
    "source_index": 0,
    "partials": [{ "freq": 100.0, "amp": 1.0, "decay": 2.0,
                    "body_mag": 1.0, "phase_deg": -90.0 }],
    "acoustic_transfer": [{
      "model_partial_index": 0,
      "radius_m": 1.0,
      "azimuth_deg": 0.0,
      "elevation_deg": 0.0,
      "pressure_per_force_real_pa_n": 0.001,
      "pressure_per_force_imag_pa_n": -0.002
    }]
  }]
}
```

`absolute_spl` gate 比較複數 Pa/N 的絕對 level；measurement 另用已宣告的 RMS force 算出 SPL，兩個公式會互相核對。`radiation_directivity` gate 以每個 partial 的最大點正規化 level pattern，同時比較 wrapped complex phase。模型缺任何已量座標時為 `UNVERIFIED`，不會跳過缺點後宣稱 PASS。

## 5. 手動建立舊版 measurement bundle

若只有既有實驗室衍生表格、無法提供 pipeline 所需的同步 CSV，可複製舊版 [measurement.template.json](../specimens/templates/measurement.template.json)，並依 [specimen_measurement.schema.json](../specimens/schema/specimen_measurement.schema.json) 填寫。模板中的零 hash 只是佔位，未替換一定會被拒絕。此路徑不會自動產生 phase／SPL／directivity；新量測應優先使用 [measurement_v2.template.json](../specimens/templates/measurement_v2.template.json) 與 [v2 schema](../specimens/schema/specimen_measurement_v2.schema.json)。

重要欄位：

- `claim_scope`：只開啟本次真正有資料且模型支援的主張。
- `acceptance`：測試前先鎖定，不可看到結果後放寬。
- `model.uncertainty`：模型材料、幾何與邊界參數傳播後的 expanded uncertainty。
- `measured_modes[*].*_u_*`：量測 expanded uncertainty，coverage factor 記在 acquisition。
- `relative_magnitude_reference_partial_index`：量測值以該模態為 0 dB；這不等於絕對 SPL。

## 6. 執行與解讀

```powershell
python tools\specimen_verify.py path\to\measurement.json `
  --dump-modes path\to\modes.json `
  --json-out path\to\specimen-report.json
```

Exit code 與意義：

- `0 PASS`：所有已要求、且模型支援的 claim 在「中央誤差＋量測不確定度＋模型不確定度」的保守條件下通過。
- `1 FAIL`：資料有效，但至少一個已支援的物理 claim 或 coherence／mode-count 閘門失敗。
- `2 REFUSED`：schema、hash、路徑、NaN/Inf、重複 partial、缺校正或其他證據鏈無效；結果不可判讀。
- `3 UNVERIFIED`：要求了模型尚未輸出的物理量，例如 phase、絕對 SPL 或 radiation。這不是 PASS，也不是把缺資料當零。

## 7. 目前不能宣稱的事

即使三個現行模型 observable 全部 PASS，也只證明指定標本、指定邊界、指定點位的 modal frequency／relative magnitude／T60 在所列容差內。量測端已有複數 FRF、校正聲壓傳遞函數與多點 directivity 並不會自動補出模型端缺少的 signed／complex modal residue、絕對力到聲壓尺度、baffle／空間 radiation operator。在模型實作並通過同一 bundle 之前，不可把結果寫成「完整音色已物理精確重現」。
