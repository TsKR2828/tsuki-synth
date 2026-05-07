# TsukiSynth TODO

> 更新：2026-05-08

---

## 當前：Phase 3 — Cimbalom 引擎（物理建模弦）

- [ ] 建立 `src/engines/CimbalomEngine.h/.cpp`
  - [ ] 繼承 juce::SynthesiserVoice，替換現有 SineVoice
  - [ ] 內部持有 ModalResonator + StringModel
  - [ ] noteOn → 從 MIDI note 計算弦長/張力 → StringModel 算模態 → excite
  - [ ] noteOff → damp
- [ ] PluginProcessor 改用 CimbalomEngine
  - [ ] 啟動時載入 MaterialDB（`data/materials.json`）
  - [ ] 預設材質：steel
- [ ] 加入可調參數（AudioParameterFloat）
  - [ ] 材質選擇（steel / copper / bronze / aluminum / ...）
  - [ ] 擊打位置（0.05 ~ 0.95）
  - [ ] 弦徑（0.3mm ~ 2.0mm）
  - [ ] 槌硬度（影響噪音瞬態頻寬）
- [ ] 多弦 beating
  - [ ] 每 course 2~5 條弦，微失諧 0~15 cent
- [ ] 共鳴弦（sympathetic strings）
  - [ ] 八度 / 五度頻率的弦被動共振
- [ ] 響板耦合（soundboard）
  - [ ] 低頻 body resonance（簡易 2D plate 模型 or biquad 共振）
- [ ] Damper 控制（CC#64 sustain pedal）
- [ ] 在 Cubase 中測試，A/B 對比 HTML 原型

## 待辦：Phase 4 — Chromatic Synth

- [ ] `src/physics/BeamModel.h` — Euler-Bernoulli 梁（空靈鼓）
- [ ] `src/physics/PlateModel.h` — Kirchhoff 圓板（水鑼）+ Bessel 零點
- [ ] `src/engines/ChromaticEngine.h/.cpp` — 三合一切換

## 待辦：Phase 5 — FM Piano

- [ ] `src/engines/FMPianoEngine.h/.cpp` — FM 合成移植

## 待辦：Phase 6 — 效果鏈

- [ ] Reverb（Freeverb or Schroeder）
- [ ] Delay（複用 DelayLine）
- [ ] Wall Reflection（3-tap delay + LP）
- [ ] Compressor

## 待辦：Phase 7 — GUI

- [ ] 深色木質調介面
- [ ] 引擎切換 tabs
- [ ] 物理參數旋鈕
- [ ] 模態分佈視覺化

## 待辦：Phase 8 — 預設 + 收尾

- [ ] 出廠預設音色
- [ ] Preset save/load
- [ ] DAW Automation
- [ ] 多 DAW 測試

## 低優先

- [ ] Phase 1.5：CI（GitHub Actions）
- [ ] Phase 9：AAX 格式
- [ ] Phase 10：AI Score Pipeline CLI 渲染器
