#pragma once

#include <cmath>
#include <juce_core/juce_core.h>

enum class FilterType { LowPass, HighPass, BandPass };

class BiquadFilter
{
public:
    void prepare (double newSampleRate)
    {
        sampleRate = newSampleRate;
        reset();
    }

    void setParameters (FilterType type, double frequency, double Q = 0.707)
    {
        const double w0    = juce::MathConstants<double>::twoPi * frequency / sampleRate;
        const double cosw0 = std::cos (w0);
        const double sinw0 = std::sin (w0);
        const double alpha = sinw0 / (2.0 * Q);

        double b0 = 0, b1 = 0, b2 = 0, a0 = 1, a1 = 0, a2 = 0;

        switch (type)
        {
            case FilterType::LowPass:
                b0 = (1.0 - cosw0) / 2.0;
                b1 =  1.0 - cosw0;
                b2 = (1.0 - cosw0) / 2.0;
                a0 =  1.0 + alpha;
                a1 = -2.0 * cosw0;
                a2 =  1.0 - alpha;
                break;

            case FilterType::HighPass:
                b0 =  (1.0 + cosw0) / 2.0;
                b1 = -(1.0 + cosw0);
                b2 =  (1.0 + cosw0) / 2.0;
                a0 =  1.0 + alpha;
                a1 = -2.0 * cosw0;
                a2 =  1.0 - alpha;
                break;

            case FilterType::BandPass:
                b0 =  alpha;
                b1 =  0.0;
                b2 = -alpha;
                a0 =  1.0 + alpha;
                a1 = -2.0 * cosw0;
                a2 =  1.0 - alpha;
                break;
        }

        coeffB0 = b0 / a0;
        coeffB1 = b1 / a0;
        coeffB2 = b2 / a0;
        coeffA1 = a1 / a0;
        coeffA2 = a2 / a0;
    }

    float processSample (float input)
    {
        double x = static_cast<double> (input);
        double y = coeffB0 * x + coeffB1 * x1 + coeffB2 * x2
                                - coeffA1 * y1 - coeffA2 * y2;
        x2 = x1;
        x1 = x;
        y2 = y1;
        y1 = y;

        return static_cast<float> (y);
    }

    void reset()
    {
        x1 = x2 = y1 = y2 = 0.0;
    }

private:
    double sampleRate = 44100.0;
    double coeffB0 = 1.0, coeffB1 = 0.0, coeffB2 = 0.0;
    double coeffA1 = 0.0, coeffA2 = 0.0;
    double x1 = 0.0, x2 = 0.0;
    double y1 = 0.0, y2 = 0.0;
};
