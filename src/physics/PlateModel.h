#pragma once

#include "MaterialDB.h"
#include "../dsp/ModalResonator.h"
#include <cmath>
#include <vector>
#include <array>

struct PlateParams
{
    double radius    = 0.12;    // R in meters
    double thickness = 0.003;   // h in meters
    double strikePosition = 0.35; // r_hit / R (0~1)
    int    numModes  = 25;
};

class PlateModel
{
public:
    // Kirchhoff circular plate (clamped boundary)
    // f(m,n) proportional to (j_mn)^2 / R^2 * sqrt(D / (rho * h))
    // D = E * h^3 / (12 * (1 - nu^2))  (flexural rigidity)
    static std::vector<Mode> calculateModes (const Material& mat,
                                              const PlateParams& params)
    {
        const double R   = params.radius;
        const double h   = params.thickness;
        const double rho = mat.density;
        const double E   = mat.youngsModulus;
        const double nu  = mat.poissonRatio;

        if (R <= 0.0 || h <= 0.0 || rho <= 0.0)
            return {};

        // Flexural rigidity
        const double D = E * h * h * h / (12.0 * (1.0 - nu * nu));

        // Bessel function zeros j(m,n) for clamped circular plate
        // Format: { j_value, m_order, n_order }
        struct BesselZero { double j; int m; int n; };
        static const std::array<BesselZero, 25> zeros = {{
            { 2.4048, 0, 1 }, { 3.8317, 1, 1 }, { 5.1356, 2, 1 },
            { 5.5201, 0, 2 }, { 6.3802, 3, 1 }, { 7.0156, 1, 2 },
            { 7.5883, 4, 1 }, { 8.4172, 2, 2 }, { 8.6537, 0, 3 },
            { 8.7715, 5, 1 }, { 9.7610, 3, 2 }, { 9.9361, 6, 1 },
            {10.1735, 1, 3 }, {11.0647, 4, 2 }, {11.0864, 7, 1 },
            {11.6198, 2, 3 }, {11.7915, 0, 4 }, {12.2251, 8, 1 },
            {12.3386, 5, 2 }, {13.0152, 3, 3 }, {13.3237, 1, 4 },
            {13.3543, 9, 1 }, {13.5893, 6, 2 }, {14.4755, 10, 1 },
            {14.7960, 4, 3 }
        }};

        const double alpha = mat.damping.alpha;
        const double beta  = mat.damping.betaAir;
        const double gamma = mat.damping.gammaRadiation;
        const double x     = params.strikePosition;

        // Base coefficient
        const double coeff = std::sqrt (D / (rho * h))
                           / (juce::MathConstants<double>::twoPi * R * R);

        std::vector<Mode> modes;
        const int N = juce::jmin (params.numModes, 25);

        for (int i = 0; i < N; ++i)
        {
            const double j  = zeros[static_cast<size_t>(i)].j;
            const int    m  = zeros[static_cast<size_t>(i)].m;

            const double freq = j * j * coeff;

            const double denominator = alpha + beta * freq * freq + gamma * freq;
            const double tau = (denominator > 0.0) ? 1.0 / denominator : 5.0;

            // Radial excitation: approximate J_m(j_mn * r/R)
            // Simplified: modes with m=0 excited everywhere,
            // higher m excited less near center
            double amp = 1.0;
            if (m == 0)
                amp = 1.0 - 0.3 * x;
            else
                amp = std::pow (x, static_cast<double>(m)) * (1.0 - x * x);

            amp /= (1.0 + static_cast<double>(i) * 0.05);

            Mode mode;
            mode.frequency = freq;
            mode.amplitude = std::abs (amp);
            mode.decayTime = tau;
            modes.push_back (mode);
        }

        return modes;
    }
};
