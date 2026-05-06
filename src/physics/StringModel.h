#pragma once

#include "MaterialDB.h"
#include "../dsp/ModalResonator.h"
#include <cmath>
#include <vector>

struct StringParams
{
    double stringLength   = 0.35;   // L in meters
    double stringDiameter = 0.8e-3; // d in meters (0.8mm)
    double tension        = 800.0;  // T in Newtons
    double strikePosition = 0.3;    // x_hit / L (0.0 ~ 1.0)
    int    numModes       = 40;
};

class StringModel
{
public:
    static std::vector<Mode> calculateModes (const Material& mat,
                                              const StringParams& params)
    {
        const double L   = params.stringLength;
        const double d   = params.stringDiameter;
        const double T   = params.tension;
        const double x   = params.strikePosition;
        const int    N   = params.numModes;
        const double rho = mat.density;
        const double E   = mat.youngsModulus;

        // linear density: mu = rho * pi * (d/2)^2
        const double radius = d * 0.5;
        const double mu = rho * juce::MathConstants<double>::pi * radius * radius;

        if (mu <= 0.0 || T <= 0.0 || L <= 0.0)
            return {};

        // ideal fundamental: f1 = (1 / 2L) * sqrt(T / mu)
        const double f1_ideal = std::sqrt (T / mu) / (2.0 * L);

        // inharmonicity coefficient: B = (pi^3 * E * d^4) / (64 * T * L^2)
        const double pi3 = juce::MathConstants<double>::pi
                         * juce::MathConstants<double>::pi
                         * juce::MathConstants<double>::pi;
        const double d4  = d * d * d * d;
        const double B   = (pi3 * E * d4) / (64.0 * T * L * L);

        const double alpha = mat.damping.alpha;
        const double beta  = mat.damping.betaAir;
        const double gamma = mat.damping.gammaRadiation;

        std::vector<Mode> modes;
        modes.reserve (static_cast<size_t> (N));

        for (int n = 1; n <= N; ++n)
        {
            // f(n) = n * f1 * sqrt(1 + B * n^2)
            const double nn = static_cast<double> (n);
            const double freq = nn * f1_ideal * std::sqrt (1.0 + B * nn * nn);

            // tau(n) = 1 / (alpha + beta * f^2 + gamma * f)
            const double denominator = alpha + beta * freq * freq + gamma * freq;
            const double tau = (denominator > 0.0) ? 1.0 / denominator : 10.0;

            // amplitude(n) = sin(n * pi * x_hit / L)
            const double amp = std::abs (
                std::sin (nn * juce::MathConstants<double>::pi * x));

            Mode m;
            m.frequency = freq;
            m.amplitude = amp;
            m.decayTime = tau;

            modes.push_back (m);
        }

        return modes;
    }

    static double calculateFundamental (const Material& mat,
                                         const StringParams& params)
    {
        const double radius = params.stringDiameter * 0.5;
        const double mu = mat.density * juce::MathConstants<double>::pi * radius * radius;

        if (mu <= 0.0 || params.tension <= 0.0 || params.stringLength <= 0.0)
            return 0.0;

        return std::sqrt (params.tension / mu) / (2.0 * params.stringLength);
    }
};
