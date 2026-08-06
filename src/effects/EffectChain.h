#pragma once
#include "Compressor.h"
#include "StereoDelay.h"
#include "SimpleReverb.h"
#include "dsp/BiquadFilter.h"
#include "dsp/Distortion.h"
#include <juce_audio_basics/juce_audio_basics.h>
#include <juce_dsp/juce_dsp.h>

class EffectChain
{
public:
    // Parameter pointers (set by Processor)
    std::atomic<float>* pReverbMix      = nullptr;
    std::atomic<float>* pReverbSize     = nullptr;
    std::atomic<float>* pReverbDecay    = nullptr;  // seconds; <0.01 = use size
    std::atomic<float>* pReverbMode     = nullptr;  // 0 = algorithmic, 1 = IR
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

    // Brightness-compensation high shelf (documented creative layer);
    // gain 0 dB = hard bypass.
    std::atomic<float>* pEqFreq = nullptr;
    std::atomic<float>* pEqGain = nullptr;

    void prepare (double sampleRate, int maxBlockSize = 2048)
    {
        distortionL.prepare (sampleRate);
        distortionR.prepare (sampleRate);
        compressor.prepare (sampleRate);
        delay.prepare (sampleRate);
        reverb.prepare (sampleRate);

        maxBlock = juce::jmax (16, maxBlockSize);
        juce::dsp::ProcessSpec spec { sampleRate,
                                      (juce::uint32) maxBlock, 2 };
        convolution.prepare (spec);
        dryBuffer.setSize (2, maxBlock, false, false, true);
        mixScratch.resize ((size_t) maxBlock, 0.0f);

        eqL.setSampleRate (sampleRate);
        eqR.setSampleRate (sampleRate);
        eqL.reset();
        eqR.reset();

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
        convolution.reset();
        eqL.reset();
        eqR.reset();
    }

    /** Load a convolution impulse response. juce::dsp::Convolution copies /
        resamples on its own background thread, so this is safe to call from
        the message thread while audio runs. */
    void loadImpulseResponse (const juce::File& file)
    {
        convolution.loadImpulseResponse (file,
                                         juce::dsp::Convolution::Stereo::yes,
                                         juce::dsp::Convolution::Trim::yes,
                                         0);
        irLoaded.store (true, std::memory_order_release);
    }

    void clearImpulseResponse()
    {
        irLoaded.store (false, std::memory_order_release);
    }

    bool hasImpulseResponse() const
    {
        return irLoaded.load (std::memory_order_acquire);
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

        // IR mode replaces the algorithmic reverb with convolution. Fall back
        // to algorithmic when no IR is loaded, and skip IR on any block larger
        // than the prepared maximum (never allocate on the audio thread).
        const bool irMode = pReverbMode != nullptr
                         && pReverbMode->load() >= 0.5f
                         && hasImpulseResponse()
                         && numSamples <= maxBlock;

        // Authored T60 mode: a decay in seconds overrides the room-size knob
        // (mirrors the score renderer's SimpleReverb::setDecayTime contract).
        const float decaySeconds = pReverbDecay != nullptr
                                       ? pReverbDecay->load() : 0.0f;
        if (! irMode && decaySeconds >= 0.01f)
            reverb.setDecayTime (decaySeconds);

        for (int i = 0; i < numSamples; ++i)
        {
            compressor.setThreshold (smCompThreshold.getNextValue());
            compressor.setRatio (smCompRatio.getNextValue());
            delay.setTime (smDelayTime.getNextValue());
            delay.setFeedback (smDelayFeedback.getNextValue());
            delay.setMix (smDelayMix.getNextValue());
            const float sizeValue = smReverbSize.getNextValue();
            const float mixValue  = smReverbMix.getNextValue();
            if (! irMode && decaySeconds < 0.01f)
                reverb.setRoomSize (sizeValue);
            if (! irMode)
                reverb.setMix (mixValue);
            else
                mixScratch[(size_t) i] = mixValue;

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
            if (! irMode)
                reverb.processStereo (left, right);

            chL[i] = left;
            if (numChannels > 1)
                chR[i] = right;
        }

        if (irMode)
        {
            // Keep the dry post-delay signal, convolve in place, then apply
            // the same smoothed wet/dry mix the algorithmic path uses.
            dryBuffer.copyFrom (0, 0, buffer, 0, 0, numSamples);
            dryBuffer.copyFrom (1, 0, buffer, numChannels > 1 ? 1 : 0, 0,
                                numSamples);

            juce::dsp::AudioBlock<float> block (buffer);
            juce::dsp::ProcessContextReplacing<float> ctx (block);
            convolution.process (ctx);

            const float* dryL = dryBuffer.getReadPointer (0);
            const float* dryR = dryBuffer.getReadPointer (1);
            for (int i = 0; i < numSamples; ++i)
            {
                const float m = mixScratch[(size_t) i];
                chL[i] = dryL[i] * (1.0f - m) + chL[i] * m;
                if (numChannels > 1)
                    chR[i] = dryR[i] * (1.0f - m) + chR[i] * m;
            }
        }

        // Brightness-compensation shelf at the end of the chain (after
        // either reverb path). Coefficients update once per block; at
        // 0 dB the filter is skipped entirely (hard bypass).
        const float eqGain = pEqGain != nullptr ? pEqGain->load() : 0.0f;
        if (std::abs (eqGain) >= 0.005f)
        {
            const float eqFreq = pEqFreq != nullptr ? pEqFreq->load() : 2000.0f;
            eqL.setParams (BiquadFilter::Type::HighShelf, eqFreq, 0.707f, eqGain);
            eqR.setParams (BiquadFilter::Type::HighShelf, eqFreq, 0.707f, eqGain);
            for (int i = 0; i < numSamples; ++i)
            {
                chL[i] = eqL.processSample (chL[i]);
                if (numChannels > 1)
                    chR[i] = eqR.processSample (chR[i]);
            }
        }
    }

private:
    Distortion   distortionL, distortionR;
    Compressor   compressor;
    StereoDelay  delay;
    SimpleReverb reverb;
    juce::dsp::Convolution convolution;
    juce::AudioBuffer<float> dryBuffer;
    std::vector<float> mixScratch;
    std::atomic<bool> irLoaded { false };
    int maxBlock = 2048;
    BiquadFilter eqL, eqR;
    juce::SmoothedValue<float> smCompThreshold, smCompRatio;
    juce::SmoothedValue<float> smDelayTime, smDelayFeedback, smDelayMix;
    juce::SmoothedValue<float> smReverbSize, smReverbMix;
    juce::SmoothedValue<float> smDistDrive, smDistInstability, smDistMix;
};
