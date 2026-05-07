#pragma once
#include "MaterialDB.h"
#include "../dsp/ModalResonator.h"
#include <vector>
#include <cmath>
#include <juce_core/juce_core.h>

/**
 * 弦振動物理模型 — Phase 3 Cimbalom 引擎的核心
 *
 * 模態頻率：  f(n) = (n / 2L) × √(T / μ) × √(1 + B × n²)
 * 非諧性：    B = (π³ × E × d⁴) / (64 × T × L²)
 * 衰減時間：  τ(n) = 1 / (α + β_air × f(n)² + γ_radiation × f(n))
 * 激發振幅：  a(n) = sin(n × π × x_hit / L)
 *
 * 其中：
 *   L = 弦長 (m),  T = 張力 (N),  d = 弦徑 (m)
 *   μ = 線密度 = ρ × π × (d/2)²  (kg/m)
 *   E = 楊氏模量 (Pa),  ρ = 密度 (kg/m³)
 */
class StringModel
{
public:
    struct Params
    {
        float length         = 0.35f;    // 弦長 (m)
        float tension        = 800.0f;   // 張力 (N)
        float diameter       = 0.0008f;  // 弦徑 (m)  = 0.8mm
        float strikePosition = 0.3f;     // 擊打位置 (0~1)
        int   numModes       = 40;       // 模態數
    };

    /**
     * 從物理參數計算所有模態
     * @return 模態列表，可直接傳入 ModalResonator::setModes()
     */
    static std::vector<ModalResonator::Mode> calculateModes (
        const Params& params,
        const MaterialDB::Material& material)
    {
        std::vector<ModalResonator::Mode> modes;
        modes.reserve ((size_t) params.numModes);

        const float L = params.length;
        const float T = params.tension;
        const float d = params.diameter;
        const float r = d / 2.0f;

        // 線密度 μ = ρ × π × r²
        const float mu = material.density
                         * juce::MathConstants<float>::pi * r * r;

        // 基頻 f1 = 1/(2L) × √(T/μ)
        const float f1 = (1.0f / (2.0f * L))
                         * std::sqrt (T / mu);

        // 非諧性係數 B = π³ × E × d⁴ / (64 × T × L²)
        const float pi3 = juce::MathConstants<float>::pi
                         * juce::MathConstants<float>::pi
                         * juce::MathConstants<float>::pi;
        const float d4 = d * d * d * d;
        const float B = (pi3 * material.youngsModulus * d4)
                        / (64.0f * T * L * L);

        // 阻尼參數
        const float alpha = material.damping.alpha;
        const float beta  = material.damping.beta_air;
        const float gamma = material.damping.gamma_radiation;

        for (int n = 1; n <= params.numModes; ++n)
        {
            float fn = (float) n;

            // 模態頻率（含剛性修正）
            float freq = fn * f1 * std::sqrt (1.0f + B * fn * fn);

            // 超出人耳範圍就截斷
            if (freq > 20000.0f)
                break;

            // 衰減時間
            float decayDenom = alpha + beta * freq * freq + gamma * freq;
            float decay = (decayDenom > 0.0f) ? (1.0f / decayDenom) : 10.0f;

            // 擊打位置影響振幅
            float amp = std::abs (std::sin (fn * juce::MathConstants<float>::pi
                                            * params.strikePosition));

            modes.push_back ({ freq, amp, decay });
        }

        return modes;
    }

    /**
     * 從 MIDI 音符計算弦長
     * 假設基準：A4 (MIDI 69) = 0.35m，每升一個八度弦長減半
     */
    static float lengthFromMidiNote (int midiNote, float referenceLength = 0.35f)
    {
        float semitoneOffset = (float) (midiNote - 69);
        return referenceLength * std::pow (2.0f, -semitoneOffset / 12.0f);
    }

    /**
     * 從 MIDI 音符計算所需張力
     * 給定弦長、弦徑、材質密度，反推需要多少張力才能得到正確基頻
     *   T = μ × (2L × f1)²
     */
    static float tensionForNote (int midiNote, float length, float diameter,
                                 float density)
    {
        float targetFreq = 440.0f * std::pow (2.0f, (float) (midiNote - 69) / 12.0f);
        float r = diameter / 2.0f;
        float mu = density * juce::MathConstants<float>::pi * r * r;
        float v = 2.0f * length * targetFreq;  // 弦上波速
        return mu * v * v;
    }
};
