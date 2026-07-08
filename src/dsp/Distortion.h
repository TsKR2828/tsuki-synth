#pragma once

#include "LFO.h"
#include <cmath>
#include <algorithm>

enum class DistortionType { Overdrive, Bitcrush, Wavefold };

struct DistortionParams
{
    bool           enabled     = false;
    DistortionType type        = DistortionType::Overdrive;
    float          drive       = 0.5f;
    float          instability = 0.0f;
    float          wet         = 0.5f;
};

class Distortion
{
public:
    void prepare (double sampleRate)
    {
        lfo.setSampleRate (sampleRate);
        lfo.setWaveform (Oscillator::Waveform::Sine);
        lfo.setRate (3.5);
        holdCounter = 0;
        holdSample  = 0.0f;
        holdSampleInit = false;
    }

    void setParameters (const DistortionParams& p)
    {
        params = p;
        lfo.setDepth (p.instability);
    }

    float processSample (float input)
    {
        if (! params.enabled || params.wet < 0.001f)
            return input;

        float driveNow = std::clamp (params.drive + lfo.processSample(), 0.0f, 1.0f);
        float distorted = 0.0f;

        switch (params.type)
        {
            case DistortionType::Overdrive:
                distorted = processOverdrive (input, driveNow);
                break;
            case DistortionType::Bitcrush:
                distorted = processBitcrush (input, driveNow);
                break;
            case DistortionType::Wavefold:
                distorted = processWavefold (input, driveNow);
                break;
        }

        return input * (1.0f - params.wet) + distorted * params.wet;
    }

    void reset()
    {
        lfo.reset();
        holdCounter = 0;
        holdSample  = 0.0f;
        holdSampleInit = false;
    }

private:
    float processOverdrive (float input, float drive)
    {
        float gain = 1.0f + drive * 20.0f;
        return std::tanh (input * gain);
    }

    float processBitcrush (float input, float drive)
    {
        if (! holdSampleInit)
        {
            holdSample = input;
            holdSampleInit = true;
        }
        int reduction = static_cast<int> (1.0f + drive * 63.0f);
        holdCounter++;
        if (holdCounter >= reduction)
        {
            holdCounter = 0;
            float steps = 4.0f + (1.0f - drive) * 252.0f;
            holdSample = std::round (input * steps) / steps;
        }
        return holdSample;
    }

    float processWavefold (float input, float drive)
    {
        float gain = 1.0f + drive * 5.0f;
        return std::sin (input * gain * 3.14159265f);
    }

    DistortionParams params;
    LFO lfo;
    int   holdCounter = 0;
    float holdSample  = 0.0f;
    bool  holdSampleInit = false;
};
