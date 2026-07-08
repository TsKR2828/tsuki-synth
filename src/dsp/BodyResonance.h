#pragma once
#include "BiquadFilter.h"
#include <cmath>
#include <complex>
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
    }

    // Process one sample: returns the body component to be mixed in
    //
    // M1-1d velocity-linearity fix (2026-07): this used to also multiply by an
    // envelope follower (envLevel) tracking |input|. Since the resonant filters
    // below are already linear and driven by `input` (which is itself
    // proportional to velocity via ModalResonator::excite()), multiplying their
    // output by a SECOND input-derived envelope made the body-resonance term
    // scale as velocity^2, not velocity^1 -- the source of the M1-1d superlinear
    // RMS failures (cimbalom/tongue_drum/water_gong/piano all route through this
    // shared component). A passive resonant body (soundboard) is a linear
    // system in the small-signal regime: output amplitude ∝ driving force
    // (F = m·a, struck body's response scales with impulse strength), so the
    // resonant bandpass filters alone -- already amplitude- and time-envelope-
    // following because they are driven sample-by-sample by the decaying
    // `input` -- are the correct and sufficient body-resonance model. No
    // separate multiplicative envelope is applied.
    float processSample (float input)
    {
        if (amount < 0.001f)
            return 0.0f;

        // Drive the resonant filters with the input signal
        float low = bpLow.processSample (input);
        float mid = bpMid.processSample (input);

        // Low-pass to tame any harshness from the BP resonance
        float body = lpLow.processSample (low * 1.4f + mid * 0.8f);

        return body * amount * 4.0f;
    }

    // 2026-07 (--amps GATE fix, ROADMAP_PHYSICS.md M2-2d root-cause: see
    // reports/gate_outputs/amps_rootcause_analysis.md Experiment 2/3). This
    // component is mixed additively as `sample += bodyRes.processSample
    // (sample)`, i.e. the *actual* rendered path is `dry + wet`, not `wet`
    // alone. --dump-modes previously reported the pre-BodyResonance
    // ModalResonator amplitude, silently comparing to a signal that is never
    // rendered. totalResponse() closes that gap by evaluating the exact
    // steady-state complex transfer function of the full dry+wet path at a
    // given frequency, built from the SAME BiquadFilter coefficient objects
    // (bpLow/bpMid/lpLow) that processSample() drives sample-by-sample above
    // -- i.e. this is a read of the model's own linear operator, not an
    // independent re-derivation and not anything derived from rendered audio.
    // Steady-state (as opposed to a full per-sample convolution) is a
    // deliberate, documented approximation: valid when the filters' own
    // settling time (~Q/(pi*f), a few ms for these Q=1.4-1.8 resonances) is
    // short relative to the modal partial's decay time, which holds for every
    // partial inside physics_verify's "weak, not assessed" floor. Matches
    // Python `bodyres.py` prototype's analytic result to within rounding.
    std::complex<float> totalResponse (float freqHz) const
    {
        if (amount < 0.001f)
            return { 1.0f, 0.0f };
        std::complex<float> hLow = bpLow.responseAt (freqHz);
        std::complex<float> hMid = bpMid.responseAt (freqHz);
        std::complex<float> hLp  = lpLow.responseAt (freqHz);
        std::complex<float> wet  = amount * 4.0f * (1.4f * hLow + 0.8f * hMid) * hLp;
        return std::complex<float> (1.0f, 0.0f) + wet;
    }

    // |dry+wet| at freqHz -- the number --dump-modes needs (Experiment 3's
    // "|H_total(f)|" table), read straight from the live filter state.
    float magnitudeAt (float freqHz) const { return std::abs (totalResponse (freqHz)); }

private:
    double sr         = 44100.0;
    float  amount     = 0.0f;
    float  lowFreq    = 120.0f;
    float  lowMidFreq = 280.0f;

    BiquadFilter bpLow;   // resonant BP at ~120 Hz
    BiquadFilter bpMid;   // resonant BP at ~280 Hz
    BiquadFilter lpLow;   // LP to smooth the combined body

    void updateFilters()
    {
        if (sr <= 0.0) return;

        bpLow.setSampleRate (sr);
        bpLow.setParams (BiquadFilter::Type::BandPass, lowFreq, 1.8f);

        bpMid.setSampleRate (sr);
        bpMid.setParams (BiquadFilter::Type::BandPass, lowMidFreq, 1.4f);

        lpLow.setSampleRate (sr);
        lpLow.setParams (BiquadFilter::Type::LowPass, 500.0f, 0.707f);
    }
};
