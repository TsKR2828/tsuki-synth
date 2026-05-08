#pragma once
#include "Compressor.h"
#include "StereoDelay.h"
#include "SimpleReverb.h"
#include "dsp/Distortion.h"
#include <juce_audio_basics/juce_audio_basics.h>

class EffectChain
{
public:
    // Parameter pointers (set by Processor)
    std::atomic<float>* pReverbMix      = nullptr;
    std::atomic<float>* pReverbSize     = nullptr;
    std::atomic<float>* pDelayTime      = nullptr;
    std::atomic<float>* pDelayFeedback  = nullptr;
    std::atomic<float>* pDelayMix       = nullptr;
    std::atomic<float>* pCompThreshold  = nullptr;
    std::atomic<float>* pCompRatio      = nullptr;

    // Distortion pointers
    std::atomic<float>* pDistType        = nullptr;
    std::atomic<float>* pDistDrive       = nullptr;
    std::atomic<float>* pDistInstability = nullptr;
    std::atomic<float>* pDistMix         = nullptr;

    void prepare (double sampleRate)
    {
        distortionL.prepare (sampleRate);
        distortionR.prepare (sampleRate);
        compressor.prepare (sampleRate);
        delay.prepare (sampleRate);
        reverb.prepare (sampleRate);
    }

    void reset()
    {
        distortionL.reset();
        distortionR.reset();
        compressor.reset();
        delay.reset();
        reverb.reset();
    }

    void processBlock (juce::AudioBuffer<float>& buffer)
    {
        // Read effect parameters
        if (pCompThreshold != nullptr)
            compressor.setThreshold (pCompThreshold->load());
        if (pCompRatio != nullptr)
            compressor.setRatio (pCompRatio->load());
        if (pDelayTime != nullptr)
            delay.setTime (pDelayTime->load());
        if (pDelayFeedback != nullptr)
            delay.setFeedback (pDelayFeedback->load());
        if (pDelayMix != nullptr)
            delay.setMix (pDelayMix->load());
        if (pReverbSize != nullptr)
            reverb.setRoomSize (pReverbSize->load());
        if (pReverbMix != nullptr)
            reverb.setMix (pReverbMix->load());

        // Read distortion parameters
        if (pDistDrive != nullptr)
        {
            DistortionParams dp;
            float drive = pDistDrive->load();
            dp.enabled     = drive > 0.001f;
            dp.type        = static_cast<DistortionType> (
                                 pDistType ? (int) pDistType->load() : 0);
            dp.drive       = drive;
            dp.instability = pDistInstability ? pDistInstability->load() : 0.0f;
            dp.wet         = pDistMix ? pDistMix->load() : 0.5f;
            distortionL.setParameters (dp);
            distortionR.setParameters (dp);
        }

        int numSamples  = buffer.getNumSamples();
        int numChannels = buffer.getNumChannels();

        float* chL = buffer.getWritePointer (0);
        float* chR = (numChannels > 1) ? buffer.getWritePointer (1) : chL;

        for (int i = 0; i < numSamples; ++i)
        {
            float left  = chL[i];
            float right = chR[i];

            // Chain: Distortion → Compressor → Delay → Reverb
            left  = distortionL.processSample (left);
            right = distortionR.processSample (right);
            compressor.processStereo (left, right);
            delay.processStereo (left, right);
            reverb.processStereo (left, right);

            chL[i] = left;
            if (numChannels > 1)
                chR[i] = right;
        }
    }

private:
    Distortion   distortionL, distortionR;
    Compressor   compressor;
    StereoDelay  delay;
    SimpleReverb reverb;
};
