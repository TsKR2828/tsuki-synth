# TsukiSynth Dev-Log

> 開發日誌 — 記錄每次 session 的進度、決策與問題

---

## 2026-05-06 — Phase 1 完成 ✅

### 驗收
- Standalone 啟動成功，虛擬鍵盤可用滑鼠彈奏
- 正弦波聲音確認輸出正常（NVIDIA HDMI Audio）
- 文字顯示正常（修正 em dash 編碼問題）
- Phase 1 交付標準達成：插件載入 + MIDI 輸入 + 聽到聲音

---

## 2026-05-06 — Phase 1 編譯成功

### 進度
- VS2026 Community + CMake 4.2.3 確認安裝（VS 路徑 `D:\Visual_Studio`）
- **VST3 + Standalone 編譯成功**
  - `build\TsukiSynth_artefacts\Release\VST3\TsukiSynth.vst3` (6MB)
  - `build\TsukiSynth_artefacts\Release\Standalone\TsukiSynth.exe` (7MB)
- 修正編譯錯誤：`BusLayout` → `BusesLayout`（JUCE API 正確類型名）
- 關閉 `COPY_PLUGIN_AFTER_BUILD`（需管理員權限，改手動複製）
- 移除 `JUCE_DISPLAY_SPLASH_SCREEN`（JUCE 8 已棄用）

### 編譯指令
```
cmake -B build -G "Visual Studio 18 2026"
cmake --build build --config Release
```

### 待處理
- 實際打開 Standalone 測試 MIDI 輸入和正弦波輸出
- 用 Reaper/Cubase 載入 VST3 測試
- 手動複製 VST3 到 `C:\Program Files\Common Files\VST3\`（需管理員）

---

## 2026-05-06 — Phase 1 骨架程式碼 + Dev-Log 建立

### 進度
- 建立 `phase1/juce-skeleton` 分支
- 完成 Phase 1 骨架程式碼：
  - `CMakeLists.txt` — JUCE 8.0.1 via FetchContent、VST3 + Standalone 格式
  - `src/PluginProcessor.h/.cpp` — 16 聲部正弦波合成器（JUCE Synthesiser 框架 + ADSR 包絡）
  - `src/PluginEditor.h/.cpp` — 基本 GUI 外殼（深色主題、標題文字）
- 修正 CONTEXT.md 本機路徑

### 待處理
- **安裝 Visual Studio 2022 Community**（勾選「使用 C++ 的桌面開發」）
- **安裝 CMake 3.22+**（或透過 VS Installer）
- 安裝完成後執行編譯：
  ```
  cmake -B build -G "Visual Studio 17 2022"
  cmake --build build --config Release
  ```
- 用 Reaper 或 Cubase 載入 VST3 測試

### 技術決策
- JUCE 引入方式：CMake FetchContent（自動下載，不需 submodule）
- 目標 JUCE 版本：8.0.1（使用新版 FontOptions API）
- 輸出格式：VST3 + Standalone（Phase 1 先不做 AU）
- 正弦波合成器作為 proof-of-life：16 voices、ADSR、0.3 master gain

### 備註
- VS2022 和 CMake 尚未安裝，程式碼先寫好備用
- 首次 `cmake -B build` 會自動 clone JUCE（約需幾分鐘）

---

## 2026-05-06 — Phase 0 完成確認 + Dev-Log 建立

### 進度
- Phase 0（規劃）所有主要項目已完成並 push 至 main
- 單一 commit: `3e76298 Phase 0: project planning`
- 已完成：README.md、ROADMAP.md、CONTEXT.md、materials.json、score schema、3 個範例 score、sound_library 索引

### 待處理
- CONTEXT.md 本機路徑需更新（舊：`Desktop\Claude\tsuki-synth` → 新：`Desktop\Claude\VoiceMusic\tsuki-synth`）
- Phase 0 剩餘：確認開發環境安裝清單（VS2022、CMake）
- 準備進入 Phase 1：環境建置 + JUCE 骨架

### 決策
- 專案名稱確定：TsukiSynth
- GitHub repo: TsKR2828/tsuki-synth

### 備註
- 本 Dev-Log 從今天開始記錄
