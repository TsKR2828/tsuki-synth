#pragma once
#include <vector>
#include <cmath>
#include <algorithm>
#include <juce_core/juce_core.h>

/**
 * Modal Resonator — TsukiSynth 的核心 DSP 元件
 *
 * 原理：將物體振動分解為 N 個獨立的衰減正弦波（模態），
 *       每個模態有自己的頻率、振幅、衰減時間。
 *
 *   output(t) = Σ amplitude[n] × exp(-t / decay[n]) × sin(2π × freq[n] × t)
 *
 * 模態參數由外部物理模型（StringModel / BeamModel / PlateModel）計算後傳入。
 * 本模組只負責高效渲染。
 */
class ModalResonator
{
public:
    /// 單一模態的物理描述
    struct Mode
    {
        float frequency = 440.0f;   // Hz
        float amplitude = 1.0f;     // 初始振幅（由擊打位置決定）
        float decayTime = 1.0f;     // 秒（由材質阻尼決定）
    };

    void setSampleRate (double sr) { sampleRate = sr; }

    /// 設定模態組（由物理模型計算後傳入）
    void setModes (const std::vector<Mode>& newModes)
    {
        int n = (int) newModes.size();
        modes.resize ((size_t) n);

        for (int i = 0; i < n; ++i)
        {
            modes[(size_t) i].freq       = newModes[(size_t) i].frequency;
            modes[(size_t) i].baseAmp    = newModes[(size_t) i].amplitude;
            modes[(size_t) i].decayTime  = newModes[(size_t) i].decayTime;
            modes[(size_t) i].phase      = 0.0f;
            modes[(size_t) i].currentAmp = 0.0f;
            modes[(size_t) i].decayCoeff = 1.0f;
            modes[(size_t) i].phaseDelta = 0.0f;
        }
    }

    /// 激發（MIDI note on）
    void excite (float velocity)
    {
        active = true;
        for (auto& m : modes)
        {
            // 跳過超出人耳範圍的模態
            if (m.freq > 20000.0f || m.freq < 20.0f)
            {
                m.currentAmp = 0.0f;
                continue;
            }

            m.currentAmp = m.baseAmp * velocity;
            m.phase      = 0.0f;
            m.phaseDelta = m.freq * (float) juce::MathConstants<double>::twoPi / (float) sampleRate;

            // 衰減係數：在 decayTime 秒後降到 -60dB (~0.001)
            if (m.decayTime > 0.0f)
                m.decayCoeff = std::exp (-6.9078f / (m.decayTime * (float) sampleRate));
            else
                m.decayCoeff = 0.0f;
        }
    }

    /// 制音（damper off / note off → 加速衰減）
    void damp (float factor = 0.05f)
    {
        for (auto& m : modes)
        {
            // 將衰減時間縮短到 factor 倍
            float newDecay = m.decayTime * factor;
            if (newDecay > 0.0f)
                m.decayCoeff = std::exp (-6.9078f / (newDecay * (float) sampleRate));
            else
                m.decayCoeff = 0.0f;
        }
    }

    /// 渲染一個 sample
    float processSample()
    {
        if (! active)
            return 0.0f;

        float output = 0.0f;
        bool anyActive = false;

        for (auto& m : modes)
        {
            if (m.currentAmp < 0.0001f)
                continue;

            output += m.currentAmp * std::sin (m.phase);

            m.phase += m.phaseDelta;
            if (m.phase >= (float) juce::MathConstants<double>::twoPi)
                m.phase -= (float) juce::MathConstants<double>::twoPi;

            m.currentAmp *= m.decayCoeff;
            anyActive = true;
        }

        if (! anyActive)
            active = false;

        return output;
    }

    /// 渲染一個 buffer
    void processBlock (float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
            buffer[i] += processSample();
    }

    bool isActive() const { return active; }

    int getActiveModeCount() const
    {
        int count = 0;
        for (const auto& m : modes)
            if (m.currentAmp >= 0.0001f) ++count;
        return count;
    }

private:
    struct ModeState
    {
        float freq       = 0.0f;
        float baseAmp    = 0.0f;
        float decayTime  = 0.0f;
        float phase      = 0.0f;
        float phaseDelta = 0.0f;
        float currentAmp = 0.0f;
        float decayCoeff = 1.0f;
    };

    double sampleRate = 44100.0;
    std::vector<ModeState> modes;
    bool active = false;
};
