# TsukiSynth TODO

> 更新：2026-05-08

---

## 已完成：Phase 3 — Cimbalom 引擎（物理建模弦）

- [x] 建立 `src/engines/CimbalomEngine.h`
  - [x] CimbalomVoice 繼承 juce::SynthesiserVoice，替換 SineVoice
  - [x] 內部持有 ModalResonator + StringModel
  - [x] noteOn → 從 MIDI note 計算弦長/張力 → StringModel 算模態 → excite
  - [x] noteOff → damp
  - [x] Exciter 噪音脈衝（槌硬度控制頻寬）
- [x] PluginProcessor 改用 CimbalomEngine + APVTS
  - [x] BinaryData 嵌入 MaterialDB
  - [x] 預設材質：steel
- [x] 6 個可自動化參數
  - [x] 材質選擇（9 種）
  - [x] 擊打位置（0.05 ~ 0.95）
  - [x] 弦徑（0.3mm ~ 2.0mm）
  - [x] 槌硬度（Cotton / Felt / Wood / Metal）
  - [x] 弦數（1~5 per course）
  - [x] 失諧量（0~15 cents）
- [x] 多弦 beating（微失諧）
- [x] Damper 控制（CC#64 sustain pedal + note off）
- [x] PluginEditor 參數介面（ComboBox + Slider）
- [x] Preset save/load（APVTS → XML）
- [ ] 共鳴弦（sympathetic strings）— 延後，需要跨 voice 通訊
- [ ] 響板耦合（soundboard）— 延後，Phase 7 GUI 一起做
- [ ] 在 Cubase 中 A/B 對比 HTML 原型 — 待月月測試

## 已完成：Phase 4 — Chromatic Synth（三合一物理建模）

- [x] `src/physics/BeamModel.h` — Euler-Bernoulli 梁（空靈鼓）
- [x] `src/physics/PlateModel.h` — Kirchhoff 圓板（水鑼）+ Bessel 零點
- [x] `src/engines/ChromaticEngine.h` — 三合一引擎（beam/plate/custom）
- [x] PluginProcessor 加入引擎切換參數（engine: Cimbalom/Chromatic）
- [x] Chromatic 7 參數 APVTS 整合（sub_engine/material/strike_pos/thickness/size/exciter/pitch_glide）
- [x] PluginEditor 引擎切換 UI（ComboBox + 參數面板動態顯示/隱藏）
- [x] 圓板 pitch glide（水鑼浸水效果）
- [x] 編譯通過（VST3 + Standalone）

## 已完成：Phase 5 — FM Piano（2-operator FM 合成）

- [x] `src/engines/FMPianoEngine.h` — FM 合成引擎
- [x] carrier + modulator + index envelope（指數衰減 brightness）
- [x] modulator self-feedback（organ/brass 音色用）
- [x] velocity 感應（影響 gain + modulation index）
- [x] 高頻 brightness 衰減（高音符 index 衰減更快）
- [x] 8 種 sound type preset（Piano/E.Piano/Vibraphone/Bell/Organ/Pad/Bass/Brass）
- [x] 7 個 APVTS 參數（type/ratio/index/brightness/feedback/attack/release）
- [x] PluginProcessor 三引擎路由完成
- [x] PluginEditor 三引擎面板切換
- [x] 編譯通過（VST3 + Standalone）

## 已完成：Phase 6 — 效果鏈

- [x] Reverb — Freeverb-style（8 comb + 4 allpass, stereo spread）
- [x] Delay — Stereo delay（LP in feedback, 10% R offset for width）
- [x] Compressor — Peak compressor（linked stereo, auto makeup gain）
- [x] EffectChain 串接（Compressor → Delay → Reverb）
- [x] 7 個 FX 參數 APVTS 整合
- [x] PluginEditor 效果控制面板（always visible, 底部三行）
- [x] 編譯通過（VST3 + Standalone）

## 待辦：Phase 7 — GUI（需月月參與設計）

- [ ] 深色木質調介面（需設計方向確認）
- [ ] 自訂旋鈕 / 滑桿視覺
- [ ] 模態分佈視覺化
- [x] 引擎切換 UI（已有 ComboBox + 面板切換）

## 已完成：Phase 8 — 預設 + 收尾

- [x] 出廠預設音色（12 組：Cimbalom×4 + Chromatic×4 + FM Piano×4）
- [x] Preset selector ComboBox（PluginEditor 頂部）
- [x] JUCE getNumPrograms/setCurrentProgram 整合（DAW preset browser 可用）
- [x] DAW Automation — 28 個 APVTS 參數全部可自動化
- [x] State save/load（APVTS → XML）
- [ ] 多 DAW 測試 — 待月月在 Cubase 中驗證
- [ ] A/B 對比 HTML 原型 — 待月月測試

## 低優先

- [ ] Phase 1.5：CI（GitHub Actions）
- [ ] Phase 9：AAX 格式
- [ ] Phase 10：AI Score Pipeline CLI 渲染器
