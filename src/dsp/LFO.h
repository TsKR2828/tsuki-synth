#pragma once

#include "Oscillator.h"

class LFO
{
public:
    void prepare (double sampleRate)
    {
        osc.prepare (sampleRate);
    }

    void setRate (double hz)       { osc.setFrequency (hz); }
    void setWaveform (Waveform w)  { osc.setWaveform (w); }
    void setDepth (float d)        { depth = d; }

    void reset() { osc.reset(); }

    // Returns bipolar value in [-depth, +depth]
    float getNextSample()
    {
        return osc.getNextSample() * depth;
    }

    // Returns unipolar value in [0, depth]
    float getNextSampleUnipolar()
    {
        return (osc.getNextSample() + 1.0f) * 0.5f * depth;
    }

private:
    Oscillator osc;
    float depth = 1.0f;
};
