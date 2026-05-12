#pragma once

#include <vector>
#include <cmath>
#include <algorithm>

class AllPassFilter
{
public:
    void prepare (int delaySamples)
    {
        buffer.resize (static_cast<size_t> (delaySamples), 0.0f);
        writePos = 0;
        bufSize = delaySamples;
    }

    float processSample (float input, float gain = 0.5f)
    {
        float delayed = buffer[static_cast<size_t> (writePos)];
        float output = -input + delayed;
        buffer[static_cast<size_t> (writePos)] = input + delayed * gain;
        writePos = (writePos + 1) % bufSize;
        return output;
    }

    void reset() { std::fill (buffer.begin(), buffer.end(), 0.0f); }

private:
    std::vector<float> buffer;
    int writePos = 0;
    int bufSize = 1;
};

class CombFilter
{
public:
    void prepare (int delaySamples)
    {
        buffer.resize (static_cast<size_t> (delaySamples), 0.0f);
        writePos = 0;
        bufSize = delaySamples;
    }

    void setFeedback (float fb) { feedback = fb; }
    void setDamp (float d) { damp = d; }

    float processSample (float input)
    {
        float delayed = buffer[static_cast<size_t> (writePos)];
        filterStore = delayed * (1.0f - damp) + filterStore * damp;
        buffer[static_cast<size_t> (writePos)] = input + filterStore * feedback;
        writePos = (writePos + 1) % bufSize;
        return delayed;
    }

    void reset()
    {
        std::fill (buffer.begin(), buffer.end(), 0.0f);
        filterStore = 0.0f;
    }

private:
    std::vector<float> buffer;
    int writePos = 0;
    int bufSize = 1;
    float feedback = 0.8f;
    float damp = 0.3f;
    float filterStore = 0.0f;
};

class SchroederReverb
{
public:
    void prepare (double sampleRate)
    {
        sr = sampleRate;
        double scale = sampleRate / 44100.0;

        static const int combDelays[] = { 1557, 1617, 1491, 1422, 1277, 1356, 1188, 1116 };
        static const int apDelays[]   = { 225, 556, 441, 341 };

        for (int i = 0; i < numCombs; ++i)
            combs[i].prepare (static_cast<int> (combDelays[i] * scale));

        for (int i = 0; i < numAllPasses; ++i)
            allPasses[i].prepare (static_cast<int> (apDelays[i] * scale));

        setParameters (0.5f, 0.3f, 0.3f);
    }

    void setParameters (float roomSize, float dampening, float wet)
    {
        float fb = 0.7f + roomSize * 0.28f;
        for (int i = 0; i < numCombs; ++i)
        {
            combs[i].setFeedback (fb);
            combs[i].setDamp (dampening);
        }
        wetLevel = wet;
    }

    float processSample (float input)
    {
        float combOut = 0.0f;
        for (int i = 0; i < numCombs; ++i)
            combOut += combs[i].processSample (input);
        combOut /= static_cast<float> (numCombs);

        float out = combOut;
        for (int i = 0; i < numAllPasses; ++i)
            out = allPasses[i].processSample (out);

        return input * (1.0f - wetLevel) + out * wetLevel;
    }

    void reset()
    {
        for (auto& c : combs) c.reset();
        for (auto& a : allPasses) a.reset();
    }

private:
    double sr = 44100.0;
    static constexpr int numCombs = 8;
    static constexpr int numAllPasses = 4;
    CombFilter combs[8];
    AllPassFilter allPasses[4];
    float wetLevel = 0.3f;
};
