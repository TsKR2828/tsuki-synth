#pragma once
#include <cmath>
#include <juce_core/juce_core.h>

/**
 * Biquad IIR 濾波器 — LP / HP / BP / Notch
 * 係數公式來源：Robert Bristow-Johnson Audio EQ Cookbook
 */
class BiquadFilter
{
public:
    enum class Type { LowPass, HighPass, BandPass, Notch };

    void setSampleRate (double sr) { sampleRate = sr; }

    void setParams (Type type, float cutoffHz, float q = 0.707f)
    {
        float w0 = juce::MathConstants<float>::twoPi * cutoffHz / (float) sampleRate;
        float cosW0 = std::cos (w0);
        float sinW0 = std::sin (w0);
        float alpha = sinW0 / (2.0f * q);

        float b0 = 0, b1 = 0, b2 = 0, a0 = 1, a1 = 0, a2 = 0;

        switch (type)
        {
            case Type::LowPass:
                b0 = (1.0f - cosW0) / 2.0f;
                b1 =  1.0f - cosW0;
                b2 = (1.0f - cosW0) / 2.0f;
                a0 =  1.0f + alpha;
                a1 = -2.0f * cosW0;
                a2 =  1.0f - alpha;
                break;

            case Type::HighPass:
                b0 =  (1.0f + cosW0) / 2.0f;
                b1 = -(1.0f + cosW0);
                b2 =  (1.0f + cosW0) / 2.0f;
                a0 =  1.0f + alpha;
                a1 = -2.0f * cosW0;
                a2 =  1.0f - alpha;
                break;

            case Type::BandPass:
                b0 =  alpha;
                b1 =  0.0f;
                b2 = -alpha;
                a0 =  1.0f + alpha;
                a1 = -2.0f * cosW0;
                a2 =  1.0f - alpha;
                break;

            case Type::Notch:
                b0 =  1.0f;
                b1 = -2.0f * cosW0;
                b2 =  1.0f;
                a0 =  1.0f + alpha;
                a1 = -2.0f * cosW0;
                a2 =  1.0f - alpha;
                break;
        }

        // normalize
        cb0 = b0 / a0;  cb1 = b1 / a0;  cb2 = b2 / a0;
        ca1 = a1 / a0;  ca2 = a2 / a0;
    }

    void reset() { x1 = x2 = y1 = y2 = 0.0f; }

    float processSample (float x0)
    {
        float y0 = cb0 * x0 + cb1 * x1 + cb2 * x2 - ca1 * y1 - ca2 * y2;
        x2 = x1;  x1 = x0;
        y2 = y1;  y1 = y0;
        return y0;
    }

private:
    double sampleRate = 44100.0;
    float cb0 = 1.0f, cb1 = 0.0f, cb2 = 0.0f;
    float ca1 = 0.0f, ca2 = 0.0f;
    float x1 = 0.0f, x2 = 0.0f;
    float y1 = 0.0f, y2 = 0.0f;
};
