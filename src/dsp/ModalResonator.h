#pragma once

#include <cmath>
#include <vector>
#include <algorithm>
#include <juce_core/juce_core.h>

struct Mode
{
    double frequency   = 0.0;
    double amplitude   = 0.0;
    double decayTime   = 0.0;  // tau in seconds

    double phase       = 0.0;
    double phaseInc    = 0.0;
    double currentAmp  = 0.0;
    double decayFactor = 0.0;  // per-sample multiplier
};

class ModalResonator
{
public:
    void prepare (double newSampleRate)
    {
        sampleRate = newSampleRate;
    }

    void setModes (const std::vector<Mode>& newModes)
    {
        modes = newModes;
        const double nyquist = sampleRate * 0.5;

        modes.erase (
            std::remove_if (modes.begin(), modes.end(),
                [nyquist] (const Mode& m) { return m.frequency >= nyquist || m.frequency <= 0.0; }),
            modes.end());

        for (auto& m : modes)
        {
            m.phaseInc    = juce::MathConstants<double>::twoPi * m.frequency / sampleRate;
            m.decayFactor = std::exp (-1.0 / (m.decayTime * sampleRate));
            m.currentAmp  = m.amplitude;
            m.phase       = 0.0;
        }

        active = ! modes.empty();
    }

    void trigger (float velocity)
    {
        const double vel = static_cast<double> (velocity);
        for (auto& m : modes)
        {
            m.currentAmp = m.amplitude * vel;
            m.phase      = 0.0;
        }
        active = ! modes.empty();
    }

    void release (float damping = 1.0f)
    {
        const double d = static_cast<double> (damping);
        for (auto& m : modes)
        {
            double fastDecay = std::exp (-d * 20.0 / (m.decayTime * sampleRate));
            m.decayFactor = fastDecay;
        }
    }

    float getNextSample()
    {
        if (! active)
            return 0.0f;

        double output = 0.0;
        bool anyAlive = false;

        for (auto& m : modes)
        {
            if (m.currentAmp < 1e-7)
                continue;

            output += m.currentAmp * std::sin (m.phase);
            m.phase += m.phaseInc;

            if (m.phase >= juce::MathConstants<double>::twoPi)
                m.phase -= juce::MathConstants<double>::twoPi;

            m.currentAmp *= m.decayFactor;
            anyAlive = true;
        }

        active = anyAlive;
        return static_cast<float> (output);
    }

    void scaleFrequencies (double factor)
    {
        for (auto& m : modes)
            m.phaseInc = juce::MathConstants<double>::twoPi * m.frequency * factor / sampleRate;
    }

    bool isActive() const { return active; }
    int getNumModes() const { return static_cast<int> (modes.size()); }

private:
    std::vector<Mode> modes;
    double sampleRate = 44100.0;
    bool active = false;
};
