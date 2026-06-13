#pragma once
#include "BiquadFilter.h"
#include <cmath>
#include <algorithm>

// Procedural body resonance — two resonant bandpass filters
// driven by the engine output, adding low-end weight and fullness.
// Designed to be lightweight and per-voice.

class BodyResonance
{
public:
    void prepare (double sampleRate)
    {
        sr = sampleRate;
        updateFilters();
    }

    void setAmount (float amt)
    {
        amount = std::clamp (amt, 0.0f, 1.0f);
    }

    void setFrequencies (float lowHz, float lowMidHz)
    {
        lowFreq    = lowHz;
        lowMidFreq = lowMidHz;
        updateFilters();
    }

    void reset()
    {
        lpLow.reset();
        bpLow.reset();
        bpMid.reset();
        envLevel = 0.0f;
    }

    // Process one sample: returns the body component to be mixed in
    float processSample (float input)
    {
        if (amount < 0.001f)
            return 0.0f;

        // Envelope follower on input to shape body energy
        float absIn = std::abs (input);
        float coeff = (absIn > envLevel) ? envAttack : envRelease;
        envLevel += coeff * (absIn - envLevel);

        // Drive the resonant filters with the input signal
        float low = bpLow.processSample (input);
        float mid = bpMid.processSample (input);

        // Low-pass to tame any harshness from the BP resonance
        float body = lpLow.processSample (low * 1.4f + mid * 0.8f);

        // Shape with envelope — body decays naturally with the note
        return body * amount * envLevel * 4.0f;
    }

private:
    double sr         = 44100.0;
    float  amount     = 0.0f;
    float  lowFreq    = 120.0f;
    float  lowMidFreq = 280.0f;

    BiquadFilter bpLow;   // resonant BP at ~120 Hz
    BiquadFilter bpMid;   // resonant BP at ~280 Hz
    BiquadFilter lpLow;   // LP to smooth the combined body

    float envLevel   = 0.0f;
    float envAttack  = 0.0f;
    float envRelease = 0.0f;

    void updateFilters()
    {
        if (sr <= 0.0) return;

        bpLow.setSampleRate (sr);
        bpLow.setParams (BiquadFilter::Type::BandPass, lowFreq, 1.8f);

        bpMid.setSampleRate (sr);
        bpMid.setParams (BiquadFilter::Type::BandPass, lowMidFreq, 1.4f);

        lpLow.setSampleRate (sr);
        lpLow.setParams (BiquadFilter::Type::LowPass, 500.0f, 0.707f);

        // Envelope follower coefficients (~5ms attack, ~80ms release)
        envAttack  = 1.0f - std::exp (-1.0f / (0.005f * (float) sr));
        envRelease = 1.0f - std::exp (-1.0f / (0.080f * (float) sr));
    }
};
