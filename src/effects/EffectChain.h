#pragma once
#include "Compressor.h"
#include "StereoDelay.h"
#include "SimpleReverb.h"
#include <juce_audio_basics/juce_audio_basics.h>

/**
 * Global effect chain: Compressor → Delay → Reverb
 *
 * Processes the full audio buffer after synth engine rendering.
 * Each effect has its own parameters controlled via atomic pointers.
 */
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

    void prepare (double sampleRate)
    {
        compressor.prepare (sampleRate);
        delay.prepare (sampleRate);
        reverb.prepare (sampleRate);
    }

    void reset()
    {
        compressor.reset();
        delay.reset();
        reverb.reset();
    }

    void processBlock (juce::AudioBuffer<float>& buffer)
    {
        // Read parameters
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

        int numSamples  = buffer.getNumSamples();
        int numChannels = buffer.getNumChannels();

        // Ensure we have at least stereo (or mono)
        float* chL = buffer.getWritePointer (0);
        float* chR = (numChannels > 1) ? buffer.getWritePointer (1) : chL;

        for (int i = 0; i < numSamples; ++i)
        {
            float left  = chL[i];
            float right = chR[i];

            // Chain: Compressor → Delay → Reverb
            compressor.processStereo (left, right);
            delay.processStereo (left, right);
            reverb.processStereo (left, right);

            chL[i] = left;
            if (numChannels > 1)
                chR[i] = right;
        }
    }

private:
    Compressor  compressor;
    StereoDelay delay;
    SimpleReverb reverb;
};
