#pragma once

#include "../effects/SimpleReverb.h"
#include "../effects/StereoDelay.h"
#include "../effects/Compressor.h"
#include "Distortion.h"

struct EffectsParams
{
    bool   reverbEnabled    = true;
    float  reverbRoomSize   = 0.5f;
    float  reverbDecaySeconds = -1.0f; // >=0 selects measurable T60
    float  reverbDamping    = 0.3f;
    float  reverbWet        = 0.25f;

    bool   delayEnabled     = false;
    double delayTime        = 0.3;
    float  delayFeedback    = 0.3f;
    float  delayWet         = 0.2f;

    bool   compressorEnabled = false;
    float  compThreshold     = -12.0f;
    float  compRatio         = 4.0f;
    float  compMakeup        = 0.0f;

    bool           distortionEnabled    = false;
    DistortionType distortionType       = DistortionType::Overdrive;
    float          distortionDrive      = 0.5f;
    float          distortionInstability = 0.0f;
    float          distortionWet        = 0.5f;

    float  masterVolume      = 1.0f;
};

class EffectsChain
{
public:
    void prepare (double sampleRate)
    {
        distortionL.prepare (sampleRate);
        distortionR.prepare (sampleRate);
        compressor.prepare (sampleRate);
        delay.prepare (sampleRate);
        reverb.prepare (sampleRate);
    }

    void setParameters (const EffectsParams& p)
    {
        params = p;

        DistortionParams dp;
        dp.enabled     = p.distortionEnabled;
        dp.type        = p.distortionType;
        dp.drive       = p.distortionDrive;
        dp.instability = p.distortionInstability;
        dp.wet         = p.distortionWet;
        distortionL.setParameters (dp);
        distortionR.setParameters (dp);

        if (p.reverbDecaySeconds >= 0.0f)
            reverb.setDecayTime (p.reverbDecaySeconds);
        else
            reverb.setRoomSize (p.reverbRoomSize);
        reverb.setDamping (p.reverbDamping);
        reverb.setMix (p.reverbEnabled ? p.reverbWet : 0.0f);
        delay.setTime ((float) (p.delayTime * 1000.0));
        delay.setFeedback (p.delayFeedback);
        delay.setMix (p.delayEnabled ? p.delayWet : 0.0f);
        compressor.setThreshold (p.compThreshold);
        compressor.setRatio (p.compressorEnabled ? p.compRatio : 1.0f);
    }

    void processStereo (float& left, float& right)
    {
        // Chain: Distortion → Compressor → Delay → Reverb (matches plugin)
        if (params.distortionEnabled)
        {
            left  = distortionL.processSample (left);
            right = distortionR.processSample (right);
        }

        compressor.processStereo (left, right);
        // Keep both stateful effects advancing at wet=0, matching the plugin.
        delay.processStereo (left, right);
        reverb.processStereo (left, right);

        left  *= params.masterVolume;
        right *= params.masterVolume;
    }

    void reset()
    {
        distortionL.reset();
        distortionR.reset();
        compressor.reset();
        delay.reset();
        reverb.reset();
    }

private:
    EffectsParams params;
    Distortion distortionL, distortionR;
    Compressor compressor;
    StereoDelay delay;
    SimpleReverb reverb;
};
