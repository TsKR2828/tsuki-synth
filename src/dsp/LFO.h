#pragma once
#include "Oscillator.h"

/**
 * 低頻振盪器 — 調變用
 * 底層複用 Oscillator，加上 depth / bipolar 控制
 * 用途：vibrato、tremolo、filter modulation
 */
class LFO
{
public:
    void setSampleRate (double sr) { osc.setSampleRate (sr); }
    void setRate (float hz)        { osc.setFrequency (hz); }
    void setDepth (float d)        { depth = d; }
    void setWaveform (Oscillator::Waveform w) { osc.setWaveform (w); }

    void reset() { osc.reset(); }

    // 回傳 [-depth, +depth]
    float processSample()
    {
        return osc.processSample() * depth;
    }

    // 回傳 [0, depth]（單極性，適合 amplitude modulation）
    float processUnipolar()
    {
        return (osc.processSample() * 0.5f + 0.5f) * depth;
    }

private:
    Oscillator osc;
    float depth = 1.0f;
};
