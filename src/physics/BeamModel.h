#pragma once
#include "MaterialDB.h"
#include "../dsp/ModalResonator.h"
#include <vector>
#include <cmath>
#include <juce_core/juce_core.h>

/**
 * Euler-Bernoulli 梁振動模型 — 空靈鼓 (Tongue Drum) 引擎
 *
 * 模態頻率：f(n) = (beta_n^2 / (2*pi*L^2)) * sqrt(E*I / (rho*A))
 *
 * Free-free beam beta_n values:
 *   beta_1=4.730, beta_2=7.853, beta_3=10.996, beta_4=14.137, beta_5=17.279
 *   -> ratio: 1.000, 2.757, 5.404, 8.933, 13.345
 *
 * 特徵：非諧波模態序列（不是整數倍），產生空靈鼓特有的「鐘聲感」
 */
class BeamModel
{
public:
    struct Params
    {
        float length    = 0.12f;     // 舌片長度 (m)
        float width     = 0.02f;     // 舌片寬度 (m)
        float thickness = 0.003f;    // 舌片厚度 (m)
        float strikePosition = 0.5f; // 擊打位置 (0~1)
        int   numModes  = 12;        // 模態數（梁模態密度低，12 足夠）
    };

    static std::vector<ModalResonator::Mode> calculateModes (
        const Params& params,
        const MaterialDB::Material& material)
    {
        std::vector<ModalResonator::Mode> modes;
        modes.reserve ((size_t) params.numModes);

        const float L = params.length;
        const float w = params.width;
        const float h = params.thickness;

        // 截面慣性矩 I = w * h^3 / 12
        const float I = w * h * h * h / 12.0f;
        // 截面積 A = w * h
        const float A = w * h;

        // sqrt(E*I / (rho*A))
        const float stiffness = std::sqrt (
            material.youngsModulus * I / (material.density * A));

        // Free-free beam eigenvalues (beta_n * L)
        // 前 5 個精確值，之後用近似公式 beta_n ≈ (2n+1)*pi/2
        //
        // SOURCE (M7 7b, 2026-07-12): these are the analytic roots of
        // cosh(x)*cos(x) = 1 (the free-free Euler-Bernoulli beam frequency
        // equation; see e.g. Blevins, "Formulas for Natural Frequency and Mode
        // Shape," table for a free-free uniform beam), independently verified
        // numerically in this task (scipy.optimize.brentq bracketing each root)
        // to 7-8 significant digits:
        //   4.7300407, 7.8532046, 10.9956078, 14.1371655, 17.2787597
        // All 5 tabulated values below match the numerically re-solved roots to
        // within their stated precision (largest rounding gap: beta_4L, table
        // 14.1372 vs solved 14.1371655 -> rounds identically at 4 decimals). No
        // changes needed.
        static constexpr float betaL[] = {
            4.7300f, 7.8532f, 10.9956f, 14.1372f, 17.2788f
        };

        const float alpha = material.damping.alpha;
        const float beta  = material.damping.beta_air;
        const float gamma = material.damping.gamma_radiation;

        const float twoPiL2 = juce::MathConstants<float>::twoPi * L * L;

        for (int n = 0; n < params.numModes; ++n)
        {
            // beta_n * L
            float bn;
            if (n < 5)
                bn = betaL[n];
            else
                bn = ((float) (2 * (n + 1) + 1)) * juce::MathConstants<float>::pi / 2.0f;

            // 模態頻率
            float freq = (bn * bn / twoPiL2) * stiffness;

            // 衰減（梁比弦衰減快，damping 加權）
            float decayDenom = alpha * 2.0f + beta * freq * freq + gamma * freq;
            float decay = (decayDenom > 0.0f) ? (1.0f / decayDenom) : 5.0f;

            // 擊打位置影響（free-free beam mode shape 近似）
            float x = params.strikePosition;
            float amp = std::abs (std::sin (((float) (n + 1)) * juce::MathConstants<float>::pi * x));

            modes.push_back ({ freq, amp, decay });
        }

        return modes;
    }

    /// 從 MIDI 音符計算舌片長度（A4=0.12m 基準）
    static float lengthFromMidiNote (int midiNote, float referenceLength = 0.12f)
    {
        float semitoneOffset = (float) (midiNote - 69);
        // 梁頻率 ∝ 1/L^2，所以 L ∝ 1/sqrt(f)
        return referenceLength * std::pow (2.0f, -semitoneOffset / 24.0f);
    }
};
