#pragma once
#include <cmath>
#include <juce_core/juce_core.h>

/**
 * 基礎振盪器 — 相位累加器 + 多波形
 * 用途：LFO 的底層、FM Piano 的 carrier/modulator、測試用
 */
class Oscillator
{
public:
    enum class Waveform { Sine, Saw, Square, Triangle };

    void setSampleRate (double sr) { sampleRate = sr; updateDelta(); }
    void setFrequency (double hz)  { frequency = hz;  updateDelta(); }
    void setWaveform (Waveform w)  { waveform = w; }

    void reset() { phase = 0.0; }

    float processSample()
    {
        float out = 0.0f;

        switch (waveform)
        {
            case Waveform::Sine:
                out = (float) std::sin (phase);
                break;
            case Waveform::Saw:
                out = (float) (1.0 - phase / juce::MathConstants<double>::pi);
                break;
            case Waveform::Square:
                out = phase < juce::MathConstants<double>::pi ? 1.0f : -1.0f;
                break;
            case Waveform::Triangle:
                out = (float) (2.0 * std::abs (1.0 - phase / juce::MathConstants<double>::pi) - 1.0);
                break;
        }

        phase += phaseDelta;
        if (phase >= juce::MathConstants<double>::twoPi)
            phase -= juce::MathConstants<double>::twoPi;

        return out;
    }

private:
    void updateDelta()
    {
        if (sampleRate > 0.0)
            phaseDelta = frequency * juce::MathConstants<double>::twoPi / sampleRate;
    }

    double sampleRate  = 44100.0;
    double frequency   = 440.0;
    double phase       = 0.0;
    double phaseDelta  = 0.0;
    Waveform waveform  = Waveform::Sine;
};
