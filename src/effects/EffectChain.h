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

        auto init = [sampleRate] (juce::SmoothedValue<float>& value, float current,
                                  double rampSeconds = 0.02)
        {
            value.reset (sampleRate, rampSeconds);
            value.setCurrentAndTargetValue (current);
        };
        init (smCompThreshold, pCompThreshold ? pCompThreshold->load() : -12.0f);
        init (smCompRatio,     pCompRatio ? pCompRatio->load() : 4.0f);
        init (smDelayTime,     pDelayTime ? pDelayTime->load() : 300.0f, 0.05);
        init (smDelayFeedback, pDelayFeedback ? pDelayFeedback->load() : 0.3f);
        init (smDelayMix,      pDelayMix ? pDelayMix->load() : 0.0f);
        init (smReverbSize,    pReverbSize ? pReverbSize->load() : 0.5f);
        init (smReverbMix,     pReverbMix ? pReverbMix->load() : 0.0f);
        init (smDistDrive,     pDistDrive ? pDistDrive->load() : 0.0f);
        init (smDistInstability,
              pDistInstability ? pDistInstability->load() : 0.0f);
        init (smDistMix,       pDistMix ? pDistMix->load() : 0.5f);
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
        // Parameter automation may arrive as block-sized steps.  Smooth every
        // continuous control so automation cannot create artificial clicks.
        if (pCompThreshold)  smCompThreshold.setTargetValue (pCompThreshold->load());
        if (pCompRatio)      smCompRatio.setTargetValue (pCompRatio->load());
        if (pDelayTime)      smDelayTime.setTargetValue (pDelayTime->load());
        if (pDelayFeedback)  smDelayFeedback.setTargetValue (pDelayFeedback->load());
        if (pDelayMix)       smDelayMix.setTargetValue (pDelayMix->load());
        if (pReverbSize)     smReverbSize.setTargetValue (pReverbSize->load());
        if (pReverbMix)      smReverbMix.setTargetValue (pReverbMix->load());
        if (pDistDrive)      smDistDrive.setTargetValue (pDistDrive->load());
        if (pDistInstability) smDistInstability.setTargetValue (pDistInstability->load());
        if (pDistMix)        smDistMix.setTargetValue (pDistMix->load());

        int numSamples  = buffer.getNumSamples();
        int numChannels = buffer.getNumChannels();

        float* chL = buffer.getWritePointer (0);
        float* chR = (numChannels > 1) ? buffer.getWritePointer (1) : chL;

        for (int i = 0; i < numSamples; ++i)
        {
            compressor.setThreshold (smCompThreshold.getNextValue());
            compressor.setRatio (smCompRatio.getNextValue());
            delay.setTime (smDelayTime.getNextValue());
            delay.setFeedback (smDelayFeedback.getNextValue());
            delay.setMix (smDelayMix.getNextValue());
            reverb.setRoomSize (smReverbSize.getNextValue());
            reverb.setMix (smReverbMix.getNextValue());

            DistortionParams dp;
            dp.type = static_cast<DistortionType> (
                pDistType ? juce::jlimit (0, 2, (int) pDistType->load()) : 0);
            dp.drive = smDistDrive.getNextValue();
            dp.enabled = dp.drive > 0.001f;
            dp.instability = smDistInstability.getNextValue();
            dp.wet = smDistMix.getNextValue();
            distortionL.setParameters (dp);
            distortionR.setParameters (dp);

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
    juce::SmoothedValue<float> smCompThreshold, smCompRatio;
    juce::SmoothedValue<float> smDelayTime, smDelayFeedback, smDelayMix;
    juce::SmoothedValue<float> smReverbSize, smReverbMix;
    juce::SmoothedValue<float> smDistDrive, smDistInstability, smDistMix;
};
