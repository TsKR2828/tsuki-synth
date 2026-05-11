#pragma once

#include <cmath>
#include <algorithm>

class SimpleCompressor
{
public:
    void prepare (double sampleRate)
    {
        sr = sampleRate;
        updateCoefficients();
    }

    void setParameters (float thresh, float rat, float attackMs, float releaseMs, float makeupGain)
    {
        threshold = thresh;
        ratio = rat;
        attackTime = attackMs;
        releaseTime = releaseMs;
        makeup = makeupGain;
        updateCoefficients();
    }

    float processSample (float input)
    {
        float absIn = std::abs (input);
        float dB = (absIn > 1e-8f) ? 20.0f * std::log10 (absIn) : -160.0f;

        float gainReduction = 0.0f;
        if (dB > threshold)
            gainReduction = (dB - threshold) * (1.0f - 1.0f / ratio);

        float targetEnv = gainReduction;
        if (targetEnv > envelope)
            envelope = attackCoeff * envelope + (1.0f - attackCoeff) * targetEnv;
        else
            envelope = releaseCoeff * envelope + (1.0f - releaseCoeff) * targetEnv;

        float gainDB = -envelope + makeup;
        float gain = std::pow (10.0f, gainDB / 20.0f);

        return input * gain;
    }

    void reset() { envelope = 0.0f; }

private:
    void updateCoefficients()
    {
        if (sr > 0.0)
        {
            attackCoeff = std::exp (-1.0f / (static_cast<float> (sr) * attackTime * 0.001f));
            releaseCoeff = std::exp (-1.0f / (static_cast<float> (sr) * releaseTime * 0.001f));
        }
    }

    double sr = 44100.0;
    float threshold = -12.0f;
    float ratio = 4.0f;
    float attackTime = 5.0f;
    float releaseTime = 50.0f;
    float makeup = 0.0f;
    float envelope = 0.0f;
    float attackCoeff = 0.99f;
    float releaseCoeff = 0.999f;
};
