#pragma once
#include "MaterialDB.h"
#include "../dsp/ModalResonator.h"
#include <vector>
#include <cmath>
#include <juce_core/juce_core.h>

/**
 * Kirchhoff 圓板振動模型（真 clamped 邊界）— 水鑼 (Water Gong) 引擎
 *
 * 模態頻率：f ∝ (Omega / R^2) * sqrt(D / (rho*h))
 *   D = E*h^3 / (12*(1-nu^2))                          板剛度 (flexural rigidity)
 *   Omega = lambda^2 = omega * a^2 * sqrt(rho h / D)   板特徵值參數 (Leissa)
 *
 * 2026-06 升級：原本用 Bessel J_m=0 零點(圓膜/鼓皮特徵值)做近似；現改為「真
 * clamped Kirchhoff 板」特徵值 Omega = lambda^2，並用 f ∝ Omega(線性，非平方)。
 * 泛音比例變成板而非膜：1 : 2.08 : 3.41 : 3.89 : 5.00 : 5.95 ...（材質/尺寸
 * 無關，tuneChromaticModesToMidi 會把基頻釘到 MIDI）。
 * 若要 free-edge 真鑼(吊掛自由邊)音色，把下方 Omega 表換成 free-plate 那組即可。
 *
 * 特徵：2D 板模態，金屬鑼/鐘的複雜非諧泛音結構
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

        // True clamped circular Kirchhoff-plate frequency parameters
        //   Omega = lambda^2 = omega * a^2 * sqrt(rho h / D)   (Leissa, Vibration
        //   of Plates), ordered by frequency. m = nodal diameters, n = nodal circles.
        // Replaces the old circular-MEMBRANE Bessel-zero approximation. Ratios are
        // material/size-independent. (For a free-edge gong, swap this Omega table.)
        struct PlateMode { float value; int m; int n; };
        static constexpr PlateMode zeros[] = {
            { 10.2158f, 0, 0 },
            { 21.260f,  1, 0 },
            { 34.877f,  2, 0 },
            { 39.771f,  0, 1 },
            { 51.030f,  3, 0 },
            { 60.829f,  1, 1 },
            { 69.666f,  4, 0 },
            { 84.583f,  2, 1 },
            { 89.104f,  0, 2 },
            { 90.739f,  5, 0 },
            { 111.02f,  3, 1 },
            { 120.08f,  1, 2 },
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
            float omega = zeros[i].value;
            int   m     = zeros[i].m;

            // 模態頻率 f ∝ lambda^2 = Omega (true Kirchhoff plate dispersion)
            float freq = freqBase * omega;

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
