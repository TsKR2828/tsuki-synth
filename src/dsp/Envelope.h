#pragma once

#include <cmath>
#include <algorithm>

class ExpDecayEnvelope
{
public:
    void prepare (double newSampleRate) { sampleRate = newSampleRate; }

    void setDecayTime (double seconds)
    {
        decayTime = seconds;
        if (sampleRate > 0.0 && decayTime > 0.0)
            decayFactor = std::exp (-1.0 / (decayTime * sampleRate));
        else
            decayFactor = 0.0;
    }

    void trigger (float velocity = 1.0f)
    {
        currentLevel = static_cast<double> (velocity);
        active = true;
    }

    void release (double fastDecaySeconds = 0.05)
    {
        if (sampleRate > 0.0 && fastDecaySeconds > 0.0)
            decayFactor = std::exp (-1.0 / (fastDecaySeconds * sampleRate));
        else
            currentLevel = 0.0;
    }

    float getNextSample()
    {
        if (! active)
            return 0.0f;

        float out = static_cast<float> (currentLevel);
        currentLevel *= decayFactor;

        if (currentLevel < 1e-7)
        {
            currentLevel = 0.0;
            active = false;
        }

        return out;
    }

    bool isActive() const { return active; }

private:
    double sampleRate   = 44100.0;
    double decayTime    = 1.0;
    double decayFactor  = 0.999;
    double currentLevel = 0.0;
    bool   active       = false;
};
