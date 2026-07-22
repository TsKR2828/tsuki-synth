#pragma once
#include "MaterialDB.h"
#include "../dsp/ModalResonator.h"
#include <vector>
#include <cmath>
#include <algorithm>
#include <juce_core/juce_core.h>

/**
 * Kirchhoff 圓板振動模型（clamped / completely-free 邊界）— 水鑼引擎
 *
 * 模態頻率：f ∝ (Omega / R^2) * sqrt(D / (rho*h))
 *   D = E*h^3 / (12*(1-nu^2))                          板剛度 (flexural rigidity)
 *   Omega = lambda^2 = omega * a^2 * sqrt(rho h / D)   板特徵值參數 (Leissa)
 *
 * 2026-06 升級：原本用 Bessel J_m=0 零點(圓膜/鼓皮特徵值)做近似；現改為「真
 * clamped Kirchhoff 板」特徵值 Omega = lambda^2，並用 f ∝ Omega(線性，非平方)。
 * 泛音比例變成板而非膜：1 : 2.08 : 3.41 : 3.89 : 5.00 : 5.95 ...（材質/尺寸
 * 無關，tuneChromaticModesToMidi 會把基頻釘到 MIDI）。
 * Score 層的 water_gong 預設為吊掛自由邊；這個低階 Params 結構保留 clamped
 * 預設，呼叫端必須明確傳入 score 的 plateFreeEdge。自由板根依材料 Poisson ratio
 * 插值，兩種邊界也都使用對應的 Bessel/modified-Bessel 徑向振型。
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
        bool  freeEdge    = false;    // low-level default; score water_gong explicitly supplies true
    };

    static float decayTimeForFrequency (
        float frequency, const MaterialDB::Material& material)
    {
        const float denominator = material.damping.alpha
            + material.damping.beta_air * frequency * frequency
            + material.damping.gamma_radiation * frequency;
        return denominator > 0.0f ? 1.0f / denominator : 8.0f;
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
        // Replaces the old circular-MEMBRANE Bessel-zero approximation. Clamped
        // ratios are material/size-independent; free-edge ratios vary with nu.
        //
        // SOURCE (M7 7b, 2026-07-12): Leissa, "Vibration of Plates," NASA SP-160
        // (1969), Table 2.1 (clamped circular plate; frequency-independent of nu
        // in the clamped case). All 12 entries verified two ways: (1) matched
        // digit-for-digit against Table 2.1 (n=0..3, s=0..3 block) as scanned from
        // the primary NASA source (ntrs.nasa.gov/citations/19700009156), and (2)
        // independently re-derived from the clamped-plate characteristic equation
        // Jn'(lambda)*In(lambda) - In'(lambda)*Jn(lambda) = 0 (Leissa eq. 2.5),
        // solved numerically (mpmath, 30-digit precision) for every (m,n) pair
        // including m=4,5 (n=0) which fall outside the excerpted Table 2.1 block.
        // Max deviation across all 12 entries: 0.03% (m=3,n=1: table 111.02 vs
        // solved 111.0214). All well within the 1% verification threshold; no
        // changes made.
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

        // FREE-edge circular Kirchhoff plate, lowest flexible mode is (2,0).
        //
        // SOURCE (M7 7c, 2026-07-12): Leissa, "Vibration of Plates," NASA SP-160
        // (1969), Table 2.5 ("lambda^2 for a Completely Free Circular Plate;
        // nu=0.33"), obtained from the primary NASA source
        // (ntrs.nasa.gov/citations/19700009156) and read directly off the scanned
        // table image (s = rows, n = columns 0..6).
        // 6 of 7 entries match Table 2.5 EXACTLY: (2,0)=5.253, (0,1)=9.084,
        // (3,0)=12.23, (1,1)=20.52, (2,1)=35.25, (0,2)=38.55.
        // CORRECTION APPLIED (Phase H, 2026-07-12, 月月 sign-off, Rule 10
        // before/after audio re-render done): the (4,0) entry was 21.83f, but
        // Table 2.5 lists 21.6 for (4,0) (flagged in the table itself as "true
        // within 2 percent", i.e. computed from Leissa's large-n asymptotic
        // formula eq. 2.15/2.16, not the exact eq. 2.14). The exact free-plate
        // characteristic equation (eq. 2.14) was re-derived from first
        // principles here (M_r=0 / V_r=0 Kirchhoff boundary conditions,
        // eliminated via the Bessel/modified-Bessel ODEs) and solved
        // numerically (mpmath, 40-digit precision) TWICE independently
        // (Phase G and Phase H), both times giving lambda^2(4,0) = 21.527,
        // cross-validated against Table 2.5's other 6 exact entries (<0.2%
        // agreement on each). Value updated 21.83f -> 21.527f. Source: analytic
        // characteristic-equation root, nu=0.33, independently solved,
        // consistent with Leissa SP-160 Table 2.5 (21.6, 3 s.f.). Old value
        // 21.83f kept on record in docs/EIGENVALUE_SOURCES.md.
        static constexpr PlateMode freeModes[] = {
            // value is the nu=0.33 reference. calculateModes replaces it with
            // an interpolation of roots re-solved from the free-edge moment /
            // effective-shear determinant for the actual material nu.
            { 5.262037f, 2, 0 }, { 9.068899f, 0, 1 }, { 12.243894f, 3, 0 },
            { 20.513087f, 1, 1 }, { 21.527217f, 4, 0 }, { 35.242521f, 2, 1 },
            { 38.506969f, 0, 2 },
        };
        const PlateMode* table = params.freeEdge ? freeModes : zeros;
        const int maxModes = params.freeEdge
            ? (int) (sizeof (freeModes) / sizeof (freeModes[0]))
            : (int) (sizeof (zeros)     / sizeof (zeros[0]));
        const int numToUse = std::min (params.numModes, maxModes);

        // 基頻因子
        const float freqBase = stiffness / (juce::MathConstants<float>::twoPi * R * R);

        for (int i = 0; i < numToUse; ++i)
        {
            float omega = params.freeEdge
                ? freeEigenvalueForPoisson (i, nu)
                : table[i].value;
            int   m     = table[i].m;

            // 模態頻率 f ∝ lambda^2 = Omega (true Kirchhoff plate dispersion)
            float freq = freqBase * omega;

            // 衰減
            float decay = decayTimeForFrequency (freq, material);

            // Kirchhoff radial eigenfunction at the actual strike radius.
            // This enforces the boundary and centre nodes instead of the old
            // x^(m/2) heuristic/floor.  m>0 represents the energy-equivalent
            // degenerate cos/sin pair, hence the radial coupling is independent
            // of an arbitrary angular coordinate until a spatial pickup is
            // modelled explicitly.
            //
            // ── Modal amplitude convention: VELOCITY (equal-weight) ────────
            // amp = |W_mn(strike radius)| with equal weight per mode -- no
            // 1/omega_n (displacement) or omega_n (acceleration/pressure)
            // factor. Same modal-velocity convention as StringModel and
            // BeamModel (cross-engine consistency): an impulsive point force
            // gives each mode an initial velocity ∝ W_mn(x_hit)/m_mn, and
            // the per-mode modal mass m_mn is treated as equal across modes
            // (see the display-scale note at radialModeShape()'s norm
            // tables). A displacement or far-field-pressure convention would
            // differ by an overall ≈ ∓/±6 dB/oct spectral tilt.
            const float x = juce::jlimit (0.0f, 1.0f, params.strikePosition);
            float amp = std::abs (radialModeShape (
                params.freeEdge, i, m, omega, x, nu));

            // Modal-mass geometry scaling.  Size/thickness/density therefore
            // remain observable even when a higher layer later pitch-locks the
            // fundamental to MIDI.
            constexpr double referenceMassKg = 7800.0 * juce::MathConstants<double>::pi
                                              * 0.15 * 0.15 * 0.003;
            const double massKg = std::max (1.0e-9,
                (double) rho * juce::MathConstants<double>::pi
                * (double) R * (double) R * (double) h);
            amp *= juce::jlimit (0.125f, 8.0f,
                (float) std::sqrt (referenceMassKg / massKg));

            modes.push_back ({ freq, amp, decay });
        }

        // Free-edge branches can cross as Poisson ratio changes (notably
        // (1,1)/(4,0)); expose modes in actual frequency order.
        std::stable_sort (modes.begin(), modes.end(),
            [] (const auto& a, const auto& b) { return a.frequency < b.frequency; });
    }

    /// 從 MIDI 音符計算半徑（A4=0.15m 基準）
    static float radiusFromMidiNote (int midiNote, float referenceRadius = 0.15f)
    {
        float semitoneOffset = (float) (midiNote - 69);
        // 圓板頻率 ∝ 1/R^2，所以 R ∝ 1/sqrt(f)
        return referenceRadius * std::pow (2.0f, -semitoneOffset / 24.0f);
    }

private:
    struct PoissonRoots
    {
        float nu;
        float omega[7];
    };

    // Deterministic offline roots of the completely-free Kirchhoff circular
    // plate characteristic determinant (M_r=0, V_r=0). Linear interpolation
    // over nu has <0.02% error against a dense independent root sweep; the
    // material database lies within [0.20, 0.49]. This removes the former
    // hidden assumption that every material had nu=0.33.
    static float freeEigenvalueForPoisson (int modeIndex, float poisson)
    {
        static constexpr PoissonRoots rows[] = {
            { 0.20f, { 5.655124f, 8.771826f, 13.026622f, 20.342398f, 22.746564f, 35.319491f, 38.225631f } },
            { 0.22f, { 5.598574f, 8.819653f, 12.916357f, 20.369295f, 22.577557f, 35.307521f, 38.269770f } },
            { 0.25f, { 5.511182f, 8.889893f, 12.744332f, 20.409197f, 22.311959f, 35.289654f, 38.335388f } },
            { 0.26f, { 5.481346f, 8.912918f, 12.685167f, 20.422382f, 22.220093f, 35.283722f, 38.357104f } },
            { 0.29f, { 5.389647f, 8.980859f, 12.501993f, 20.461593f, 21.934078f, 35.265994f, 38.421790f } },
            { 0.30f, { 5.358330f, 9.003137f, 12.438988f, 20.474550f, 21.835163f, 35.260108f, 38.443198f } },
            { 0.33f, { 5.262037f, 9.068899f, 12.243894f, 20.513087f, 21.527217f, 35.242521f, 38.506969f } },
            { 0.34f, { 5.229136f, 9.090469f, 12.176775f, 20.525822f, 21.420716f, 35.236681f, 38.528075f } },
            { 0.35f, { 5.195821f, 9.111868f, 12.108580f, 20.538503f, 21.312224f, 35.230854f, 38.549106f } },
            { 0.37f, { 5.127919f, 9.154160f, 11.968879f, 20.563702f, 21.089112f, 35.219234f, 38.590947f } },
            { 0.38f, { 5.093316f, 9.175058f, 11.897330f, 20.576221f, 20.974407f, 35.213441f, 38.611756f } },
            { 0.40f, { 5.022761f, 9.216366f, 11.750721f, 20.601100f, 20.738478f, 35.201891f, 38.653155f } },
            { 0.45f, { 4.838060f, 9.316888f, 11.362534f, 20.662384f, 20.108339f, 35.173219f, 38.755387f } },
            { 0.49f, { 4.681024f, 9.394602f, 11.027812f, 20.710493f, 19.559111f, 35.150492f, 38.835893f } },
        };

        const int index = juce::jlimit (0, 6, modeIndex);
        const float nu = juce::jlimit (rows[0].nu, rows[13].nu, poisson);
        for (int row = 0; row < 13; ++row)
        {
            if (nu <= rows[row + 1].nu)
            {
                const float t = (nu - rows[row].nu)
                              / (rows[row + 1].nu - rows[row].nu);
                return rows[row].omega[index]
                     + t * (rows[row + 1].omega[index] - rows[row].omega[index]);
            }
        }
        return rows[13].omega[index];
    }

    static double besselJ (int order, double x)
    {
        return std::cyl_bessel_j ((double) order, x);
    }

    static double besselI (int order, double x)
    {
        return std::cyl_bessel_i ((double) order, x);
    }

    static float radialModeShape (bool freeEdge, int tableIndex, int m,
                                  float omega, float radius, float poisson)
    {
        static constexpr float clampedNorm[] = {
            1.05571275f, 0.60320754f, 0.49931505f, 0.99746985f,
            0.44312191f, 0.58103291f, 0.40602785f, 0.48608145f,
            1.00011099f, 0.37897065f, 0.43415630f, 0.58190012f
        };
        // Norm variation over nu=[.20,.49] is below 3%; these nu=.33 maxima
        // are used only to keep each branch on a comparable display scale.
        //
        // Normalization note (applies to clampedNorm above and freeNorm
        // below): dividing by the branch maximum is a DISPLAY-SCALE
        // normalization (max|W| = 1 per branch), NOT a mass normalization
        // (∫ W² r dr = const). Unlike the beam case -- where the endpoint
        // value 2 and the modal mass are both mode-independent, so display
        // and mass normalization coincide up to one global gain -- a
        // max-normalized plate branch still has a per-mode modal mass that
        // varies from branch to branch. That residual per-mode difference
        // is knowingly absorbed into the equal-weight (velocity-convention)
        // amplitude treatment documented at calculateModes(); switching to
        // true mass normalization would re-weight branches relative to each
        // other and is a deliberate model decision, not a bugfix.
        static constexpr float freeNorm[] = {
            0.6342789f, 0.9161902f, 0.5624543f, 0.5565380f,
            0.5131424f, 0.4746762f, 1.0031191f
        };

        const double lambda = std::sqrt ((double) omega);
        const double jEdge = besselJ (m, lambda);
        const double iEdge = besselI (m, lambda);
        double coefficient;

        if (! freeEdge)
        {
            coefficient = -jEdge / iEdge; // W(1)=0
        }
        else
        {
            const double jPrime = (double) m / lambda * jEdge
                                - besselJ (m + 1, lambda);
            const double iPrime = (double) m / lambda * iEdge
                                + besselI (m + 1, lambda);
            const double oneMinusNu = 1.0 - (double) poisson;
            const double momentJ = ((double) poisson - 1.0) * lambda * jPrime
                                 + (-lambda * lambda + (double) (m * m) * oneMinusNu) * jEdge;
            const double momentI = ((double) poisson - 1.0) * lambda * iPrime
                                 + ( lambda * lambda + (double) (m * m) * oneMinusNu) * iEdge;
            coefficient = -momentJ / momentI; // M_r(1)=0
        }

        const double z = lambda * (double) radius;
        const double radial = besselJ (m, z) + coefficient * besselI (m, z);
        const int maxIndex = freeEdge ? 6 : 11;
        const int index = juce::jlimit (0, maxIndex, tableIndex);
        const double norm = freeEdge ? freeNorm[index] : clampedNorm[index];
        return (float) (radial / std::max (1.0e-12, norm));
    }
};
