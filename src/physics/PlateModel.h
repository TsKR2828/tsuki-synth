#pragma once
#include "MaterialDB.h"
#include "../dsp/ModalResonator.h"
#include <vector>
#include <cmath>
#include <juce_core/juce_core.h>

/**
 * Kirchhoff 圓板振動模型 — 水鑼 (Water Gong) 引擎
 *
 * 模態頻率：f(m,n) ∝ (j(m,n)^2 / R^2) * sqrt(D / (rho*h))
 *   D = E*h^3 / (12*(1-nu^2))  板剛度
 *   j(m,n) = Bessel 函數零點
 *
 * Clamped circular plate Bessel zeros (j_mn):
 *   j(0,1)=2.405  j(1,1)=3.832  j(2,1)=5.136  j(0,2)=5.520
 *   j(3,1)=6.380  j(1,2)=7.016  j(4,1)=7.588  j(2,2)=8.417
 *   ...
 *
 * 特徵：2D 模態分佈，產生金屬鑼/鐘的複雜泛音結構
 */
class PlateModel
{
public:
    struct Params
    {
        float radius      = 0.15f;    // 半徑 (m)
        float thickness   = 0.003f;   // 板厚 (m)
        float strikePosition = 0.35f; // 擊打位置 (0=中心, 1=邊緣)
        int   numModes    = 20;
    };

    static std::vector<ModalResonator::Mode> calculateModes (
        const Params& params,
        const MaterialDB::Material& material)
    {
        std::vector<ModalResonator::Mode> modes;
        modes.reserve ((size_t) params.numModes);

        const float R = params.radius;
        const float h = params.thickness;
        const float E = material.youngsModulus;
        const float rho = material.density;
        const float nu = material.poissonRatio;

        // 板剛度 D = E*h^3 / (12*(1-nu^2))
        const float D = E * h * h * h / (12.0f * (1.0f - nu * nu));

        // sqrt(D / (rho * h))
        const float stiffness = std::sqrt (D / (rho * h));

        // Bessel function zeros for clamped circular plate
        // 格式: {j_mn, m, n} — m=圓周方向節點數, n=徑向節點數
        struct BesselZero { float value; int m; int n; };
        static constexpr BesselZero zeros[] = {
            { 2.405f,  0, 1 },
            { 3.832f,  1, 1 },
            { 5.136f,  2, 1 },
            { 5.520f,  0, 2 },
            { 6.380f,  3, 1 },
            { 7.016f,  1, 2 },
            { 7.588f,  4, 1 },
            { 8.417f,  2, 2 },
            { 8.654f,  5, 1 },
            { 8.772f,  0, 3 },
            { 9.761f,  6, 1 },
            { 10.173f, 3, 2 },
            { 10.520f, 1, 3 },
            { 10.873f, 7, 1 },
            { 11.620f, 4, 2 },
            { 11.791f, 2, 3 },
            { 11.986f, 8, 1 },
            { 13.015f, 0, 4 },
            { 13.170f, 5, 2 },
            { 13.324f, 3, 3 },
        };

        const int maxZeros = (int) (sizeof (zeros) / sizeof (zeros[0]));
        const int numToUse = std::min (params.numModes, maxZeros);

        const float alpha = material.damping.alpha;
        const float beta  = material.damping.beta_air;
        const float gamma = material.damping.gamma_radiation;

        // 基頻因子
        const float freqBase = stiffness / (juce::MathConstants<float>::twoPi * R * R);

        for (int i = 0; i < numToUse; ++i)
        {
            float jmn = zeros[i].value;
            int   m   = zeros[i].m;

            // 模態頻率
            float freq = freqBase * jmn * jmn;

            if (freq > 20000.0f)
                break;

            // 衰減
            float decayDenom = alpha + beta * freq * freq + gamma * freq;
            float decay = (decayDenom > 0.0f) ? (1.0f / decayDenom) : 8.0f;

            // 擊打位置影響（徑向位置）
            // 近似：中心敲擊 → m=0 模態強，邊緣 → 高 m 模態強
            float x = params.strikePosition;
            float amp;
            if (m == 0)
                amp = 1.0f - x * 0.5f;  // 軸對稱模態在中心最強
            else
                amp = std::pow (x, (float) m * 0.5f);  // 高 m 模態在邊緣強

            amp = std::max (amp, 0.05f);  // 保留最小振幅

            modes.push_back ({ freq, amp, decay });
        }

        return modes;
    }

    /// 從 MIDI 音符計算半徑（A4=0.15m 基準）
    static float radiusFromMidiNote (int midiNote, float referenceRadius = 0.15f)
    {
        float semitoneOffset = (float) (midiNote - 69);
        // 圓板頻率 ∝ 1/R^2，所以 R ∝ 1/sqrt(f)
        return referenceRadius * std::pow (2.0f, -semitoneOffset / 24.0f);
    }
};
