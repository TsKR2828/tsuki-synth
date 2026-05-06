#pragma once

#include <cmath>
#include <juce_core/juce_core.h>

enum class Waveform { Sine, Saw, Square, Triangle };

class Oscillator
{
public:
    void prepare (double newSampleRate)
    {
        sampleRate = newSampleRate;
        updateIncrement();
    }

    void setFrequency (double freq)
    {
        frequency = freq;
        updateIncrement();
    }

    void setWaveform (Waveform w) { waveform = w; }

    void reset() { phase = 0.0; }

    float getNextSample()
    {
        float output = 0.0f;

        switch (waveform)
        {
            case Waveform::Sine:
                output = static_cast<float> (std::sin (phase));
                break;

            case Waveform::Saw:
                output = static_cast<float> (1.0 - 2.0 * phase / juce::MathConstants<double>::twoPi);
                break;

            case Waveform::Square:
                output = (phase < juce::MathConstants<double>::pi) ? 1.0f : -1.0f;
                break;

            case Waveform::Triangle:
            {
                double t = phase / juce::MathConstants<double>::twoPi;
                output = static_cast<float> (4.0 * std::abs (t - 0.5) - 1.0);
                break;
            }
        }

        phase += phaseIncrement;
        if (phase >= juce::MathConstants<double>::twoPi)
            phase -= juce::MathConstants<double>::twoPi;

        return output;
    }

private:
    void updateIncrement()
    {
        phaseIncrement = juce::MathConstants<double>::twoPi * frequency / sampleRate;
    }

    double sampleRate      = 44100.0;
    double frequency       = 440.0;
    double phase           = 0.0;
    double phaseIncrement  = 0.0;
    Waveform waveform      = Waveform::Sine;
};
