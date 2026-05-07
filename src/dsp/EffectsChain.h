#pragma once

#include "Reverb.h"
#include "DelayLine.h"
#include "Compressor.h"
#include "Distortion.h"
#include "BiquadFilter.h"

struct EffectsParams
{
    bool   reverbEnabled    = true;
    float  reverbRoomSize   = 0.5f;
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
        reverbL.prepare (sampleRate);
        reverbR.prepare (sampleRate);
        delayL.prepare (sampleRate, 2.0);
        delayR.prepare (sampleRate, 2.0);
        compL.prepare (sampleRate);
        compR.prepare (sampleRate);
        hiCut.prepare (sampleRate);
        hiCut.setParameters (FilterType::LowPass, 16000.0, 0.707);
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

        reverbL.setParameters (p.reverbRoomSize, p.reverbDamping, p.reverbWet);
        reverbR.setParameters (p.reverbRoomSize, p.reverbDamping, p.reverbWet);
        delayL.setDelay (p.delayTime);
        delayL.setFeedback (p.delayFeedback);
        delayL.setWetDry (p.delayWet);
        delayR.setDelay (p.delayTime * 1.12);
        delayR.setFeedback (p.delayFeedback);
        delayR.setWetDry (p.delayWet);
        compL.setParameters (p.compThreshold, p.compRatio, 5.0f, 50.0f, p.compMakeup);
        compR.setParameters (p.compThreshold, p.compRatio, 5.0f, 50.0f, p.compMakeup);
    }

    void processStereo (float& left, float& right)
    {
        if (params.distortionEnabled)
        {
            left  = distortionL.processSample (left);
            right = distortionR.processSample (right);
        }

        if (params.reverbEnabled)
        {
            left  = reverbL.processSample (left);
            right = reverbR.processSample (right);
        }

        if (params.delayEnabled)
        {
            left  = delayL.processSample (left);
            right = delayR.processSample (right);
        }

        if (params.compressorEnabled)
        {
            left  = compL.processSample (left);
            right = compR.processSample (right);
        }

        left  *= params.masterVolume;
        right *= params.masterVolume;
    }

    void reset()
    {
        distortionL.reset();
        distortionR.reset();
        reverbL.reset();
        reverbR.reset();
        delayL.reset();
        delayR.reset();
        compL.reset();
        compR.reset();
    }

private:
    EffectsParams params;
    Distortion distortionL, distortionR;
    SchroederReverb reverbL, reverbR;
    DelayLine delayL, delayR;
    SimpleCompressor compL, compR;
    BiquadFilter hiCut;
};
