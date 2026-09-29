# TsukiSynth 安裝包（Inno Setup 腳本草稿）

> 建立：2026-09-25（WF0925-G1）。**狀態：草稿，從未編譯、從未試裝。**
> 開發機上沒有安裝 Inno Setup，本卡也不下載任何執行檔，所以 `TsukiSynth.iss` 的語法只對照官方說明文件寫成，
> **沒有經過編譯器檢查**。第一次編譯一定要照下面「驗證清單」逐項做，任何一項沒過都不能拿去賣。

## 1. 這個腳本會做什麼

| 裝什麼 | 裝到哪 | 來源（repo 內） |
|---|---|---|
| VST3 外掛（整個 `TsukiSynth.vst3` 資料夾，含 `Contents\x86_64-win\TsukiSynth.vst3` 與 `Contents\Resources\moduleinfo.json`） | `{commoncf64}\VST3\TsukiSynth.vst3`（通常是 `C:\Program Files\Common Files\VST3\TsukiSynth.vst3`） | `build\TsukiSynth_artefacts\Release\VST3\TsukiSynth.vst3\` |
| Standalone | `{app}\TsukiSynth.exe`（`{app}` 預設 `C:\Program Files\TsukiSynth`） | `build\TsukiSynth_artefacts\Release\Standalone\TsukiSynth.exe` |
| CLI 渲染器 | `{app}\TsukiSynthCLI.exe` | `build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe` |
| 使用授權 | `{app}\EULA.txt`（安裝時的授權頁也顯示這份，要按同意才能裝） | `tools\installer\EULA.txt`（**不在 repo，見 §3**） |
| 第三方授權聲明 | `{app}\THIRD_PARTY_NOTICES.txt` | repo 根目錄 `THIRD_PARTY_NOTICES.txt` |

- 為什麼要裝 CLI：Standalone 的 Score 控制台會在 `TsukiSynth.exe` 旁邊找 `TsukiSynthCLI.exe`
  （`src/ScoreConsole.h` 的 `findCli()`，找不到就顯示「找不到 TsukiSynthCLI.exe（應與 Standalone 同資料夾）」）。
  2026-08-06 起的發佈包本來就同捆 CLI（`TODO.md` 2026-08-06 段）。CLI 設成可選元件，「完整安裝」預設勾選。
- 版本號：`0.3.0`，取自 `CMakeLists.txt` 第 2 行 `project(TsukiSynth VERSION 0.3.0)`。改版時兩邊要一起改（版號規則未定，盤點 E13／S10）。
- 只支援 64 位元 Windows（`ArchitecturesAllowed=x64compatible`）；需要系統管理員權限（寫入 Common Files）。
- 解除安裝：只移除安裝時放進去的檔案。**使用者資料不刪**：`%APPDATA%\TsukiSynth\Presets`、`%APPDATA%\TsukiSynth\IR`、
  `文件\TsukiSynth\Recordings`、`桌面\TsukiSynth_Renders`（位置出處見 `docs/legal/EULA_BUYER_DRAFT.md` 文末）。
- 不做程式碼簽章（變現計畫 §3：第一版先不簽）。

## 2. 需要的工具

- Inno Setup **6.3.0 以上**（腳本用到 `x64compatible`，官方更新紀錄寫這是 6.3.0 新增的；腳本開頭有版本檢查，版本太舊會直接報錯）。
  2026-09-25 官網下載頁列的是 7.1.0（2026-08-12）與 6.7.3（2026-05-26）。本卡沒有安裝任何版本。
- 腳本檔是 UTF-8（無 BOM）；官方說明寫 6.3.0 起 UTF-8 檔不需要也不建議加 BOM。

## 3. 編譯前要準備的東西

1. **月月核准的 EULA**：把 `docs/legal/EULA_BUYER_DRAFT.md` 的 `[[ … ]]` 空格填完、刪掉草稿標記與中文審稿附註，
   存成純文字 UTF-8 檔 `tools/installer/EULA.txt`。
   腳本在找不到這個檔時會**故意編譯失敗**（`#error`），避免把草稿裝進買家電腦。
2. **整合卡建好的 Release binary**：`build\` 下的 VST3、Standalone、CLI 三個 target。缺任何一個，腳本也會編譯失敗。
3. **VC++ runtime 裁決**（見 §4）。

## 4. 待月月裁決：VC++ runtime（甲／乙二選一）

事實（2026-09-25 掃描 `build\` 三個 binary 的 import 表，`reports/gate_outputs/wf0925_G1_sources.txt` §4）：
VST3、Standalone、CLI 都動態連結 `MSVCP140.dll`、`MSVCP140_2.dll`、`VCRUNTIME140.dll`、`VCRUNTIME140_1.dll`。
買家電腦如果沒有裝 Microsoft Visual C++ 可轉散發套件，DAW 可能載不進外掛（盤點 `engineering-gaps:E4`）。

| | 甲：靜態 CRT | 乙：安裝包附 `vc_redist.x64.exe` |
|---|---|---|
| 做法 | 改 `CMakeLists.txt`，讓 MSVC 把 C/C++ runtime 靜態連進 binary | 安裝時先檢查登錄，版本不夠才跑 Microsoft 的安裝程式 |
| 要動什麼 | CMakeLists（C++ lane，照 R6 跑全套 GATE，並證明 8/8 位元不變；若渲染改變依 R10 停下回報） | 只動本腳本（`.iss` 裡已寫好、先註解掉的乙案區塊） |
| 安裝包大小 | 不變 | 多一個 Microsoft 安裝程式 |
| 其他條件 | — | Microsoft 文件：只有持有 Visual Studio 授權的使用者能轉散發，受 Microsoft 授權條款約束；版本要「same or later than」建置用的 MSVC Build Tools |
| 本卡驗證到哪 | 沒改、沒建置 | 腳本沒編譯；runtime 最低版本號**待確認**（本機編譯器是 19.50.35730.0，但本卡沒找到 runtime 版本號的官方對照，不猜） |

乙案的 `vc_redist.x64.exe` 可從 Visual Studio 安裝目錄取得，或官方永久連結 https://aka.ms/vc14/vc_redist.x64.exe（**下載需月月同意**）。
放到 `tools/installer/redist/vc_redist.x64.exe`（不要進版控），再把 `.iss` 乙案區塊各行開頭的 `;;` 拿掉並填最低版本。

## 5. 其他待決或已知限制

- **對外名稱與網址**：`AppPublisher` 暫用 `TsKR`（CMake 的 `COMPANY_NAME`）；網址、信箱待月月提供（盤點 S10）。
- **舊的手動部署副本**：系統上已有 `C:\Program Files\Common Files\VST3\TsukiSynth_VST3_2026-09-10\TsukiSynth.vst3`、
  `C:\Program Files (x86)\Common Files\VST3\TsukiSynth.vst3`、`%APPDATA%\VST3\TsukiSynth.vst3` 三份舊副本（`TODO.md` 09-25 快照）。
  安裝包**不會**自動刪它們（刪系統資料夾的舊檔要月月同意，盤點 `open-work:G6-redeploy`）；DAW 可能同時掃到新舊兩份。
- **安裝介面語言**：目前只用 Inno Setup 預設（英文）。要不要加日文／中文介面，本卡沒查官方附了哪些語言檔，待定。
- **範例譜**：本腳本不附任何 score。將來要附，照盤點 `release-readiness:C2` 用白名單，排除 CC BY-SA 的月光／四季。
- **macOS**：不在本腳本範圍（變現計畫：先只賣 Windows 版）。

## 6. 第一次編譯與試裝的驗證清單（全部要有實際輸出紀錄）

1. 用 Inno Setup 6.3.0+ 編譯 `tools/installer/TsukiSynth.iss`，編譯器 0 錯誤；記下 Inno Setup 版本與輸出檔 SHA256。
2. 在**乾淨的** Windows x64（沒裝過 TsukiSynth、最好也沒裝 VC++ 可轉散發套件）執行安裝包：
   - 授權頁顯示的是核准版 EULA，不按同意無法繼續；
   - 裝完檢查 `C:\Program Files\Common Files\VST3\TsukiSynth.vst3\Contents\x86_64-win\TsukiSynth.vst3` 與 `build\` 內同一檔 SHA256 相同；
   - `{app}` 內有 `TsukiSynth.exe`、`TsukiSynthCLI.exe`、`EULA.txt`、`THIRD_PARTY_NOTICES.txt`，SHA256 與來源相同。
3. 用 HostProbe 載入安裝後的 VST3（repo 根目錄為 cwd：`build\Release\TsukiSynthHostProbe.exe <已安裝的 .vst3> <outdir>`），結果 0 failures。
   pluginval／Steinberg validator 需要下載，**要月月同意**（盤點 E2）。
4. Standalone 啟動後，Score 控制台能找到 CLI 並完成一次渲染。
5. 解除安裝：上面安裝的檔案都被移除；`%APPDATA%\TsukiSynth\` 與 `文件\TsukiSynth\` 裡使用者自己的 preset、IR、錄音都還在。
6. 再裝一次（覆蓋安裝）同一版與下一版，確認 `AppId` 讓新版認得舊版的安裝位置。
