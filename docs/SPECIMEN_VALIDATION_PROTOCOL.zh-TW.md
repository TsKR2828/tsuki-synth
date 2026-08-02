# 實物標本物理驗證流程（P7）

這個流程讓聾人與 AI 不靠聽感，把「程式照自己的方程式運作」與「方程式符合某一件真實樂器」分開驗證。前者由 C++／Python gate 處理；後者必須使用真實標本、校正過的感測器與保留原始資料，不能拿合成波形代替。

目前 Mode Dump v2 可主張的量只有：模態頻率、相對模態振幅、模態 T60。它明確把複數相位、絕對 SPL、空間輻射指向性列為 unsupported。只要量測 bundle 要求其中任何一項，`specimen_verify.py` 必須回報 `UNVERIFIED`（exit 3），不得顯示 PASS。

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

## 3. 產生模型預測

先讓 score 只包含要比對的標本事件，關閉 reverb、delay、distortion 與 wall：

```powershell
cmake --build build --config Release --target TsukiSynthCLI
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe --dump-modes path\to\specimen.score.json > path\to\modes.json
Get-FileHash -Algorithm SHA256 path\to\modes.json
```

把輸出的 hash 寫進 `model.mode_dump_sha256`，把事件原本的陣列位置寫進 `model.event_source_index`。Mode Dump v2 內的 `source_index` 是選擇事件的機器可讀依據。

## 4. 建立 measurement bundle

複製 [measurement.template.json](../specimens/templates/measurement.template.json)，並依 [specimen_measurement.schema.json](../specimens/schema/specimen_measurement.schema.json) 填寫。模板中的零 hash 只是佔位，未替換一定會被拒絕。

重要欄位：

- `claim_scope`：只開啟本次真正有資料且模型支援的主張。
- `acceptance`：測試前先鎖定，不可看到結果後放寬。
- `model.uncertainty`：模型材料、幾何與邊界參數傳播後的 expanded uncertainty。
- `measured_modes[*].*_u_*`：量測 expanded uncertainty，coverage factor 記在 acquisition。
- `relative_magnitude_reference_partial_index`：量測值以該模態為 0 dB；這不等於絕對 SPL。

## 5. 執行與解讀

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

## 6. 目前不能宣稱的事

即使三個已支援 claim 全部 PASS，也只證明指定標本、指定邊界、指定點位的 modal frequency／relative magnitude／T60 在所列容差內。尚未有複數 FRF、校正聲源到聲壓的傳遞函數、baffle／空間 radiation operator 與多點 directivity 前，不可把結果寫成「完整音色已物理精確重現」。
