# TsukiSynth — 後續待辦事項

> 最後更新：2026-05-07
> 分支：`phase1/juce-skeleton`

---

## 現況摘要

| 項目 | 狀態 |
|------|------|
| VST3 插件骨架（Phase 1-8） | ✅ 完成 |
| AI Score Pipeline（Phase 10） | ✅ 完成 |
| 音效庫 | ✅ 45 筆（6 worlds × 7 scores + examples） |
| DSP：Distortion / Glide / Trim / Layers | ✅ C++ 實作完成 |
| GUI：Distortion 控制 + Rotary knobs | ✅ 初版完成 |
| 實機編譯 + DAW 載入 | ❌ 未驗證 |

### 檔案統計

- `scores/library/` — 42 個 score（6 worlds × 7：transition/notify/action/ambient/ui/variant/loop）
- `scores/examples/` — 4 個範例 score
- `scores/tests/` — 5 個 DSP 驗證 score（distortion×2, glide, trim, layer）
- `sound_library/sound_names.json` — 45 筆索引
- `data/materials.json` — 14 種材質

---

## P0：必須做（上線前）

### 0-1. 實機編譯驗證
- [ ] 安裝 Visual Studio 2022 + CMake（若未安裝）
- [ ] `cmake -B build -G "Visual Studio 17 2022"` 設定專案
- [ ] `cmake --build build --config Release` 編譯 VST3
- [ ] 確認 `build/TsukiSynth_artefacts/Release/VST3/TsukiSynth.vst3` 產出
- [ ] 修復所有 compiler warning / error

### 0-2. CLI 批次渲染驗證
- [ ] `tsukisynth-cli --batch scores/tests/*.score.json --output exports/wav/`
- [ ] 聽 test_distortion.wav → 可辨認 overdrive 效果
- [ ] 聽 test_distortion_bitcrush.wav → 可辨認 bitcrush 效果
- [ ] 聽 test_glide.wav → 可辨認 pitch sweep
- [ ] 聽 test_trim.wav → 長度約為完整版 50%
- [ ] 聽 test_layer.wav → 接縫平滑
- [ ] 渲染原 3 example scores → 輸出與 DSP 擴充前一致（無 regression）

### 0-3. 6 個 loop score 渲染驗證
- [ ] 批次渲染 `scores/library/*/\*_loop_*.score.json`
- [ ] 每個 loop 首尾接合測試（複製兩份串接，無 pop/click）
- [ ] restraint_loop_001 確認 distortion 效果有作用
- [ ] ocean_loop_001 確認 glide 效果有作用

### 0-4. DAW 載入測試
- [ ] Reaper：掛載 VST3 → MIDI 觸發 → 聽到物理建模音色
- [ ] 切換 3 個 Engine → 參數面板正確跟隨
- [ ] Distortion Drive 旋鈕 → 可聽到效果變化
- [ ] Preset save / load → 狀態完整保存
- [ ] 至少再測一個 DAW（Cubase / FL Studio / Ableton）

---

## P1：應該做（品質提升）

### 1-1. GUI 進一步美化
- [ ] 模態分佈視覺化：顯示當前 note 的 partial 頻率/衰減分佈圖
- [ ] Cimbalom Custom Harmonics 的可拖曳 harmonic editor
- [ ] Distortion 類型切換時 knob 上方加指示文字或小圖標
- [ ] 響應式調整：不同視窗尺寸下 layout 不會重疊
- [ ] 加版本號顯示（header 右側）

### 1-2. ROADMAP.md 同步更新
- [ ] 新增 Phase 10.11：Loop 素材 ×6（✅）
- [ ] 新增 Phase 10.12：GUI 重設計（✅）
- [ ] 更新「下一步可選方向」區塊（移除已完成項）
- [ ] 更新音色庫數量（36 → 45，含 loop）

### 1-3. CI/CD Pipeline
- [ ] GitHub Actions：JSON schema 驗證（`scores/**/*.score.json` vs `score.schema.json`）
- [ ] GitHub Actions：tags.json enum 對齊檢查（所有 score 的 mood/primary_type/character 均合法）
- [ ] GitHub Actions：Windows 編譯（CMake + MSVC）
- [ ] 可選：macOS cross-compile（需 runner）

### 1-4. score.schema.json 補完
- [ ] 加入 `loop_bpm` / `loop_bars` 欄位定義
- [ ] 加入 `distortion` 效果物件定義（type/drive/instability/wet）
- [ ] 加入 `glide` 事件欄位定義（from_note/duration_ms/curve）
- [ ] 加入 `layers` 頂層陣列 + `crossfade_ms` 定義
- [ ] 加入 `start_position` / `end_position` export 欄位

---

## P2：可以做（功能擴展）

### 2-1. 音效庫擴充
- [ ] 每世界觀再追加 impact / whoosh / foley 類型
- [ ] 新增更多 variant（同家族不同材質/力度/位置）
- [ ] 考慮新增 world：Void（虛空）、Crystal（水晶洞穴）
- [ ] creature 類型 score（用 glide + LFO 模擬生物叫聲）

### 2-2. Phase 9：AAX 格式
- [ ] 申請 Avid Developer 帳號
- [ ] 下載 AAX SDK
- [ ] CMakeLists 加入 AAX target（已有 conditional 框架）
- [ ] Pro Tools 載入測試

### 2-3. 進階 DSP
- [ ] Chorus effect（利用 LFO 調制 delay time）
- [ ] EQ（parametric 3-band）
- [ ] Stereo width 控制
- [ ] Per-event effects override（讓單一 event 覆蓋 global effects）

### 2-4. Score Pipeline 增強
- [ ] `--watch` 模式：監聽 score 檔案修改 → 自動重新渲染
- [ ] `--preview` 模式：即時播放渲染結果（不寫入 WAV）
- [ ] Score 合併工具：將多個 score 的 events 合併為一個
- [ ] export 支援 MP3 / OGG / FLAC 格式

### 2-5. macOS / Linux 支援
- [ ] CMake 確認 macOS 編譯（AU + VST3）
- [ ] Xcode project 生成測試
- [ ] Linux VST3 編譯測試（GCC / Clang）

---

## P3：探索性（長期方向）

- [ ] 3D Mesh → Modal：從 OBJ/STL 匯入形狀 → 有限元素 → 自動產生模態
- [ ] DiffSound 反向調參：從 WAV 音檔反推材質參數
- [ ] WebView GUI：用 React 取代 JUCE Component（嵌入式 browser）
- [ ] GPU 加速模態計算（CUDA / Metal compute shader）
- [ ] MIDI MPE 支援（per-note pitch bend + pressure）
- [ ] 整合 Haguruma 引擎：遊戲中即時觸發 TsukiSynth 音效

---

## 關鍵檔案速查

| 用途 | 路徑 |
|------|------|
| VST 入口 | `src/PluginProcessor.h` / `.cpp` |
| GUI | `src/PluginEditor.h` / `.cpp` |
| 效果鏈 | `src/dsp/EffectsChain.h` |
| Distortion | `src/dsp/Distortion.h` |
| Score 解析 | `src/score/ScoreParser.h` |
| Score 渲染 | `src/score/ScoreRenderer.h` |
| CLI 入口 | `src/cli/RenderApp.cpp` |
| JSON Schema | `scores/schema/score.schema.json` |
| 分類法 | `sound_library/tags.json` |
| 音色庫索引 | `sound_library/sound_names.json` |
| 材質庫 | `data/materials.json` |
| 開發進度 | `ROADMAP.md` |
| 音效設計規格 | `SOUND_DESIGN_SPEC.md` |
