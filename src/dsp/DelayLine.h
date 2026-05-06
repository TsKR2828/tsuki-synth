#pragma once

#include <vector>
#include <cmath>

class DelayLine
{
public:
    void prepare (double newSampleRate, double maxDelaySeconds = 2.0)
    {
        sampleRate = newSampleRate;
        int maxSamples = static_cast<int> (maxDelaySeconds * sampleRate) + 1;
        buffer.resize (static_cast<size_t> (maxSamples), 0.0f);
        writeIndex = 0;
    }

    void setDelay (double delaySeconds)
    {
        delaySamples = delaySeconds * sampleRate;
        if (delaySamples >= static_cast<double> (buffer.size()))
            delaySamples = static_cast<double> (buffer.size()) - 1.0;
        if (delaySamples < 0.0)
            delaySamples = 0.0;
    }

    void setFeedback (float fb) { feedback = fb; }
    void setWetDry (float wet)  { wetMix = wet; }

    float processSample (float input)
    {
        float delayed = readSample();
        float toWrite = input + delayed * feedback;

        buffer[static_cast<size_t> (writeIndex)] = toWrite;
        writeIndex = (writeIndex + 1) % static_cast<int> (buffer.size());

        return input * (1.0f - wetMix) + delayed * wetMix;
    }

    void reset()
    {
        std::fill (buffer.begin(), buffer.end(), 0.0f);
        writeIndex = 0;
    }

private:
    float readSample() const
    {
        double readPos = static_cast<double> (writeIndex) - delaySamples;
        if (readPos < 0.0)
            readPos += static_cast<double> (buffer.size());

        int idx0 = static_cast<int> (readPos);
        int idx1 = (idx0 + 1) % static_cast<int> (buffer.size());
        double frac = readPos - static_cast<double> (idx0);

        return static_cast<float> (
            buffer[static_cast<size_t> (idx0)] * (1.0 - frac)
          + buffer[static_cast<size_t> (idx1)] * frac);
    }

    std::vector<float> buffer;
    double sampleRate   = 44100.0;
    double delaySamples = 0.0;
    int    writeIndex   = 0;
    float  feedback     = 0.0f;
    float  wetMix       = 0.5f;
};
