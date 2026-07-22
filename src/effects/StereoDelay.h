#pragma once
#include "../dsp/DelayLine.h"
#include <algorithm>

/**
 * Stereo Delay effect
 *
 * Two independent delay lines (L/R) with slight stereo spread.
 * Right channel has 10% longer delay for spatial width.
 * LP filter in feedback path for warm repeats.
 */
class StereoDelay
{
public:
    void prepare (double sr)
    {
        sampleRate = sr;
        // The right channel is deliberately 10% longer than the requested
        // delay. The score contract permits 5000 ms while the plugin control
        // currently exposes 2000 ms, so both paths share a truthful 5.5 s
        // right-channel capacity instead of silently clamping offline scores.
        delayL.prepare (sr, 5.6f);
        delayR.prepare (sr, 5.6f);
        lpStateL = 0.0f;
        lpStateR = 0.0f;
        constexpr float fc = 4000.0f;
        constexpr float pi = 3.14159265358979323846f;
        lpCoeff = 1.0f - std::exp (-2.0f * pi * fc / (float) sampleRate);
        updateDelay();
    }

    void setTime     (float ms)  { delayTimeMs = std::clamp (ms,  0.0f, 5000.0f); updateDelay(); }
    void setFeedback (float fb)  { feedback    = std::clamp (fb,  0.0f,  0.95f); }
    void setMix      (float m)   { mix         = std::clamp (m,   0.0f,  1.0f); }

    void reset()
    {
        delayL.reset();
        delayR.reset();
        lpStateL = 0.0f;
        lpStateR = 0.0f;
    }

    void processStereo (float& left, float& right)
    {
        if (delayTimeMs <= 0.0f)
        {
            // A zero-time delay is a dry bypass, but its history must keep
            // moving.  Freezing writePos here made old audio reappear when a
            // host automated the time from zero back to a non-zero value.
            delayL.pushSample (left);
            delayR.pushSample (right);
            lpStateL = 0.0f;
            lpStateR = 0.0f;
            return;
        }

        // Read delayed samples
        float delL = delayL.popSample();
        float delR = delayR.popSample();

        // LP filter in feedback (cutoff ~4kHz, simple one-pole)
        lpStateL = lpStateL + lpCoeff * (delL - lpStateL);
        lpStateR = lpStateR + lpCoeff * (delR - lpStateR);

        // Write input + filtered feedback
        delayL.pushSample (left  + lpStateL * feedback);
        delayR.pushSample (right + lpStateR * feedback);

        // Mix.  The delay lines intentionally keep advancing at mix=0 so
        // re-enabling the effect cannot replay stale audio from an earlier
        // transport position.
        float dry = 1.0f - mix;
        left  = left  * dry + delL * mix;
        right = right * dry + delR * mix;
    }

private:
    void updateDelay()
    {
        float secL = delayTimeMs * 0.001f;
        float secR = secL * 1.1f;  // 10% offset for stereo width
        delayL.setDelay (secL);
        delayR.setDelay (secR);

    }

    DelayLine delayL, delayR;
    double sampleRate  = 44100.0;
    float delayTimeMs  = 300.0f;
    float feedback     = 0.3f;
    float mix          = 0.0f;
    float lpCoeff      = 0.5f;
    float lpStateL     = 0.0f;
    float lpStateR     = 0.0f;
};
