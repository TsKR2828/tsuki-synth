#pragma once
#include <vector>
#include <cmath>
#include <algorithm>
#include <juce_core/juce_core.h>

/**
 * Modal Resonator - core DSP component of TsukiSynth
 *
 * Decomposes vibration into N independent decaying sinusoids (modes).
 * Each mode has its own frequency, amplitude, and decay time.
 *
 *   output(t) = sum[ amp[n] * exp(-t/decay[n]) * sin(2*pi*freq[n]*t) ]
 *
 * Mode parameters are computed by physics models (StringModel / BeamModel / PlateModel)
 * and passed in. This module only handles efficient rendering.
 */
class ModalResonator
{
public:
    /// Physical description of a single mode
    struct Mode
    {
        float frequency = 440.0f;   // Hz
        float amplitude = 1.0f;     // initial amplitude (from strike position)
        float decayTime = 1.0f;     // seconds (from material damping)
    };

    void setSampleRate (double sr) { sampleRate = sr; }

    /// Set modes (computed by physics model, passed in)
    void setModes (const std::vector<Mode>& newModes)
    {
        int n = (int) newModes.size();
        modes.resize ((size_t) n);

        for (int i = 0; i < n; ++i)
        {
            modes[(size_t) i].freq       = newModes[(size_t) i].frequency;
            modes[(size_t) i].baseAmp    = newModes[(size_t) i].amplitude;
            modes[(size_t) i].decayTime  = newModes[(size_t) i].decayTime;
            modes[(size_t) i].phase      = 0.0f;
            modes[(size_t) i].currentAmp = 0.0f;
            modes[(size_t) i].decayCoeff = 1.0f;
            modes[(size_t) i].phaseDelta = 0.0f;
        }
    }

    /// Excite (MIDI note on)
    void excite (float velocity)
    {
        active = true;
        for (auto& m : modes)
        {
            // skip modes outside audible range
            if (m.freq > 20000.0f || m.freq < 20.0f)
            {
                m.currentAmp = 0.0f;
                continue;
            }

            m.currentAmp = m.baseAmp * velocity;
            m.phase      = 0.0f;
            m.phaseDelta = m.freq * (float) juce::MathConstants<double>::twoPi / (float) sampleRate;

            // decay coefficient: reach -60dB (~0.001) after decayTime seconds
            if (m.decayTime > 0.0f)
                m.decayCoeff = std::exp (-6.9078f / (m.decayTime * (float) sampleRate));
            else
                m.decayCoeff = 0.0f;
        }
    }

    /// Damp (damper off / note off - accelerate decay)
    void damp (float factor = 0.05f)
    {
        for (auto& m : modes)
        {
            float shortened = m.decayTime * factor;
            if (shortened > 0.0f)
                m.decayCoeff = std::exp (-6.9078f / (shortened * (float) sampleRate));
            else
                m.decayCoeff = 0.0f;
        }
    }

    /// Render one sample
    float processSample()
    {
        if (! active)
            return 0.0f;

        float output = 0.0f;
        bool anyActive = false;

        for (auto& m : modes)
        {
            if (m.currentAmp < 0.0001f)
                continue;

            output += m.currentAmp * std::sin (m.phase);

            m.phase += m.phaseDelta;
            if (m.phase >= (float) juce::MathConstants<double>::twoPi)
                m.phase -= (float) juce::MathConstants<double>::twoPi;

            m.currentAmp *= m.decayCoeff;
            anyActive = true;
        }

        if (! anyActive)
            active = false;

        return output;
    }

    /// Render into a buffer (additive)
    void processBlock (float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
            buffer[i] += processSample();
    }

    /// Update mode frequencies without resetting phase or amplitude (for pitch glide)
    void updateFrequencies (const std::vector<Mode>& newModes)
    {
        int n = juce::jmin ((int) modes.size(), (int) newModes.size());
        for (int i = 0; i < n; ++i)
        {
            modes[(size_t) i].freq = newModes[(size_t) i].frequency;
            modes[(size_t) i].phaseDelta = newModes[(size_t) i].frequency
                * (float) juce::MathConstants<double>::twoPi / (float) sampleRate;
        }
    }

    void scaleFrequencies (double factor)
    {
        for (auto& m : modes)
            m.phaseDelta = m.freq * (float) factor
                           * (float) juce::MathConstants<double>::twoPi / (float) sampleRate;
    }

    bool isActive() const { return active; }

    int getActiveModeCount() const
    {
        int count = 0;
        for (const auto& m : modes)
            if (m.currentAmp >= 0.0001f) ++count;
        return count;
    }

    /// Snapshot current modes (frequency / amplitude / decay) for the CLI
    /// --dump-modes single-source-of-truth verification path.
    std::vector<Mode> getModes() const
    {
        std::vector<Mode> out;
        out.reserve (modes.size());
        for (const auto& m : modes)
            out.push_back ({ m.freq, m.baseAmp, m.decayTime });
        return out;
    }

private:
    struct ModeState
    {
        float freq       = 0.0f;
        float baseAmp    = 0.0f;
        float decayTime  = 0.0f;
        float phase      = 0.0f;
        float phaseDelta = 0.0f;
        float currentAmp = 0.0f;
        float decayCoeff = 1.0f;
    };

    double sampleRate = 44100.0;
    std::vector<ModeState> modes;
    bool active = false;
};
