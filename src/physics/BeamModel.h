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
 * 舌片與鼓身相連的一端近似固支、另一端自由，因此預設使用 cantilever
 * (fixed-free) 邊界。Free-free 仍保留為明確的替代模型，不能再用一條
 * sin(n*pi*x) 同時假裝兩種邊界。
 *
 * 特徵：非諧波模態序列（不是整數倍），產生空靈鼓特有的「鐘聲感」
 */
class BeamModel
{
public:
    enum class Boundary
    {
        Cantilever, // fixed-free: tongue / tine
        FreeFree    // suspended bar
    };

    struct Params
    {
        float length    = 0.12f;     // 舌片長度 (m)
        float width     = 0.02f;     // 舌片寬度 (m)
        float thickness = 0.003f;    // 舌片厚度 (m)
        float strikePosition = 0.5f; // 擊打位置 (0~1)
        int   numModes  = 12;        // 模態數（梁模態密度低，12 足夠）
        Boundary boundary = Boundary::Cantilever;
    };

    static float decayTimeForFrequency (
        float frequency, const MaterialDB::Material& material)
    {
        const float denominator = material.damping.alpha * 2.0f
            + material.damping.beta_air * frequency * frequency
            + material.damping.gamma_radiation * frequency;
        return denominator > 0.0f ? 1.0f / denominator : 5.0f;
    }

    static std::vector<ModalResonator::Mode> calculateModes (
        const Params& params,
        const MaterialDB::Material& material)
    {
        std::vector<ModalResonator::Mode> modes;
        calculateModes (params, material, modes);
        return modes;
    }

    static void calculateModes (
        const Params& params,
        const MaterialDB::Material& material,
        std::vector<ModalResonator::Mode>& modes)
    {
        modes.clear();
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

        // cosh(lambda) cos(lambda) = -1 (cantilever) and = +1 (free-free).
        // These are the non-rigid Euler-Bernoulli roots.  The corresponding
        // analytic eigenfunctions are evaluated below, so a fixed end is
        // actually a node and a free end is not accidentally forced to zero.
        static constexpr float cantileverBetaL[] = {
            1.8751041f, 4.6940911f, 7.8547574f, 10.9955407f, 14.1371684f
        };
        static constexpr float freeFreeBetaL[] = {
            4.7300f, 7.8532f, 10.9956f, 14.1372f, 17.2788f
        };

        const float twoPiL2 = juce::MathConstants<float>::twoPi * L * L;

        for (int n = 0; n < params.numModes; ++n)
        {
            // beta_n * L
            float bn;
            if (n < 5)
                bn = params.boundary == Boundary::Cantilever
                    ? cantileverBetaL[n] : freeFreeBetaL[n];
            else
                bn = ((float) n + (params.boundary == Boundary::Cantilever ? 0.5f : 1.5f))
                    * juce::MathConstants<float>::pi;

            // 模態頻率
            float freq = (bn * bn / twoPiL2) * stiffness;

            // 衰減（梁比弦衰減快，damping 加權）
            float decay = decayTimeForFrequency (freq, material);

            // Analytic Euler-Bernoulli mode-shape coupling at the strike point.
            // Keep amplitude as a magnitude because ModalResonator currently
            // starts every mode at a common phase; sign belongs in a future
            // independently measurable phase field rather than being hidden in
            // amplitude.
            //
            // ── Modal amplitude convention: VELOCITY (equal-weight) ────────
            // amp = |phi_n(strike point)| with equal weight per mode -- no
            // 1/omega_n (displacement) or omega_n (acceleration/pressure)
            // factor. This is the modal-velocity convention: an impulsive
            // point force gives each mode an initial velocity ∝
            // phi_n(x_hit)/m_n, and with this eigenfunction scaling the
            // modal mass is the same for every mode (see the norm note
            // below), leaving amp ∝ |phi_n(x_hit)|. StringModel and
            // PlateModel use the SAME convention (cross-engine consistency).
            // Choosing the displacement or pressure convention instead would
            // tilt the whole spectrum by ≈ ∓/±6 dB/oct respectively but not
            // change per-mode structure.
            const double x = (double) juce::jlimit (0.0f, 1.0f, params.strikePosition);
            const double lambda = (double) bn;
            const double raw = modeShape (params.boundary, lambda, x);
            // With this conventional eigenfunction scaling the flexible
            // cantilever/free-free endpoint magnitude is 2.  Using the analytic
            // value avoids subtracting two ~exp(lambda) numbers for high modes.
            //
            // Normalization note: dividing by the endpoint value 2 is a
            // DISPLAY-SCALE normalization (puts max|phi| ≈ 1, matching
            // PlateModel's max|W| = 1 tables), NOT a mass normalization.
            // For these beam families the two are equivalent up to one
            // mode-independent global gain: the endpoint magnitude is
            // exactly 2 for EVERY cantilever/free-free mode, and under the
            // same conventional scaling ∫₀ᴸ phi_n² dx = L for every mode
            // (standard Euler-Bernoulli result, e.g. Blevins, "Formulas for
            // Natural Frequency and Mode Shape", Table 8-1 normalization),
            // so mass normalization would also divide all modes by the same
            // constant. Inter-mode amplitude ratios are therefore identical
            // under either normalization.
            constexpr double norm = 2.0;

            // Energy-normalised geometry gain.  Width cancels out of the ideal
            // beam eigenfrequency, but it does not cancel out of modal mass.
            // The reference merely keeps legacy output around unity; the ratio
            // is dimensionless and makes width/density/volume audibly testable.
            constexpr double referenceMassKg = 7800.0 * 0.020 * 0.003 * 0.120;
            const double massKg = std::max (1.0e-9,
                (double) material.density * (double) A * (double) L);
            const float geometryGain = juce::jlimit (0.125f, 8.0f,
                (float) std::sqrt (referenceMassKg / massKg));
            const float amp = (float) std::abs (raw / norm) * geometryGain;

            modes.push_back ({ freq, amp, decay });
        }

    }

    /// 從 MIDI 音符計算舌片長度（A4=0.12m 基準）
    static float lengthFromMidiNote (int midiNote, float referenceLength = 0.12f)
    {
        float semitoneOffset = (float) (midiNote - 69);
        // 梁頻率 ∝ 1/L^2，所以 L ∝ 1/sqrt(f)
        return referenceLength * std::pow (2.0f, -semitoneOffset / 24.0f);
    }

private:
    static double modeShape (Boundary boundary, double lambda, double x)
    {
        // Evaluate the hyperbolic combination in an exponentially scaled form.
        // Direct cosh(lx)-sigma*sinh(lx) loses virtually all precision around
        // the free endpoint once lambda grows beyond ~30.
        const double q = std::exp (-lambda);
        const double q2 = q * q;
        const double s = std::sin (lambda);
        const double c = std::cos (lambda);

        if (boundary == Boundary::Cantilever)
        {
            // phi = cosh(lx)-cos(lx)-sigma[sinh(lx)-sin(lx)]
            // sigma=(cosh(l)+cos(l))/(sinh(l)+sin(l)).
            const double denominator = 1.0 - q2 + 2.0 * q * s;
            const double sigma = (1.0 + q2 + 2.0 * q * c) / denominator;
            const double grow = (-q2 + q * (s - c)) / denominator;
            const double fall = (1.0 + q * (s + c)) / denominator;
            const double hyperbolic = grow * std::exp (lambda * x)
                                    + fall * std::exp (-lambda * x);
            return hyperbolic - std::cos (lambda * x)
                 + sigma * std::sin (lambda * x);
        }

        // Flexible free-free modes (the two rigid-body modes are excluded):
        // phi = cosh(lx)+cos(lx)-sigma[sinh(lx)+sin(lx)].
        const double denominator = 1.0 - q2 - 2.0 * q * s;
        const double sigma = (1.0 + q2 - 2.0 * q * c) / denominator;
        const double grow = (-q2 + q * (c - s)) / denominator;
        const double fall = (1.0 - q * (s + c)) / denominator;
        const double hyperbolic = grow * std::exp (lambda * x)
                                + fall * std::exp (-lambda * x);
        return hyperbolic + std::cos (lambda * x)
             - sigma * std::sin (lambda * x);
    }
};
