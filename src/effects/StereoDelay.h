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
        delayL.prepare (sr, 2.0f);
        delayR.prepare (sr, 2.0f);
        lpStateL = 0.0f;
        lpStateR = 0.0f;
    }

    void setTime     (float ms)  { delayTimeMs = std::clamp (ms,  50.0f, 2000.0f); updateDelay(); }
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
        if (mix < 0.001f)
            return;

        // Read delayed samples
        float delL = delayL.popSample();
        float delR = delayR.popSample();

        // LP filter in feedback (cutoff ~4kHz, simple one-pole)
        lpStateL = lpStateL + lpCoeff * (delL - lpStateL);
        lpStateR = lpStateR + lpCoeff * (delR - lpStateR);

        // Write input + filtered feedback
        delayL.pushSample (left  + lpStateL * feedback);
        delayR.pushSample (right + lpStateR * feedback);

        // Mix
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

        // One-pole LP coefficient (~4 kHz)
        float fc = 4000.0f;
        lpCoeff = 1.0f - std::exp (-2.0f * 3.14159f * fc / (float) sampleRate);
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
