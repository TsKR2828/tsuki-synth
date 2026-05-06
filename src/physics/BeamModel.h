#pragma once

#include "MaterialDB.h"
#include "../dsp/ModalResonator.h"
#include <cmath>
#include <vector>
#include <array>

struct BeamParams
{
    double length    = 0.15;    // L in meters
    double width     = 0.025;   // b in meters
    double thickness = 0.003;   // h in meters
    double strikePosition = 0.5;
    int    numModes  = 20;
};

class BeamModel
{
public:
    // Euler-Bernoulli beam (free-free boundary conditions)
    // f(n) = (beta_n^2 / (2*pi*L^2)) * sqrt(E*I / (rho*A))
    static std::vector<Mode> calculateModes (const Material& mat,
                                              const BeamParams& params)
    {
        const double L   = params.length;
        const double b   = params.width;
        const double h   = params.thickness;
        const double rho = mat.density;
        const double E   = mat.youngsModulus;

        // Cross-section area and second moment of area
        const double A = b * h;
        const double I = b * h * h * h / 12.0;

        if (A <= 0.0 || I <= 0.0 || L <= 0.0 || rho <= 0.0)
            return {};

        // Free-free beam beta_n values (first 20 modes)
        static const std::array<double, 20> betaL = {
            4.73004, 7.85320, 10.9956, 14.1372, 17.2788,
            20.4204, 23.5619, 26.7035, 29.8451, 32.9867,
            36.1283, 39.2699, 42.4115, 45.5531, 48.6947,
            51.8363, 54.9779, 58.1195, 61.2611, 64.4026
        };

        const double alpha = mat.damping.alpha;
        const double beta  = mat.damping.betaAir;
        const double gamma = mat.damping.gammaRadiation;
        const double x     = params.strikePosition;

        const double coeff = std::sqrt (E * I / (rho * A))
                           / (juce::MathConstants<double>::twoPi * L * L);

        std::vector<Mode> modes;
        const int N = juce::jmin (params.numModes, 20);

        for (int n = 0; n < N; ++n)
        {
            const double bn   = betaL[static_cast<size_t>(n)];
            const double freq = bn * bn * coeff;

            const double denominator = alpha + beta * freq * freq + gamma * freq;
            const double tau = (denominator > 0.0) ? 1.0 / denominator : 5.0;

            // Approximate strike position excitation for beam
            const double nn = static_cast<double> (n + 1);
            const double amp = std::abs (
                std::sin (nn * juce::MathConstants<double>::pi * x));

            Mode m;
            m.frequency = freq;
            m.amplitude = amp / (1.0 + nn * 0.1);
            m.decayTime = tau;
            modes.push_back (m);
        }

        return modes;
    }
};
