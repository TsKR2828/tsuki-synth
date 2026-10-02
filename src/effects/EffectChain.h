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

    /** WF1002-C1（月月 2026-10-02 裁決 Q01b=B）：kIrWetMakeupGain 的 public
        唯讀存取點，給 tests/audit_repro.cpp 的 D9c-guard 用（取代原本以顯式
        實例化讀 private 成員的繞路寫法）。只回傳常數本身，不改任何狀態，
        不參與 processBlock()，聲音不變。 */
    static constexpr float irWetMakeupGain() noexcept { return kIrWetMakeupGain; }

    void processBlock (juce::AudioBuffer<float>& buffer)
    {
        // Hosts are not required to keep every callback <= the block size
        // negotiated in prepare(). Rather than silently falling back to a
        // different signal path (see the old numSamples <= maxBlock guard
        // below), split any oversized block into maxBlock-sized chunks and
        // run each one through the exact same processing below -- output
        // must be bit-identical to calling this function once per chunk.
        // The AudioBuffer(Type* const*, channels, startSample, numSamples)
        // constructor only wraps existing pointers (channels <= 32 use
        // preallocatedChannelSpace), so this never allocates on the audio
        // thread.
        const int totalSamples = buffer.getNumSamples();
        if (totalSamples > maxBlock)
        {
            int startSample = 0;
            while (startSample < totalSamples)
            {
                const int chunk = juce::jmin (maxBlock, totalSamples - startSample);
                juce::AudioBuffer<float> subBuffer (buffer.getArrayOfWritePointers(),
                                                     buffer.getNumChannels(),
                                                     startSample, chunk);
                processBlock (subBuffer);
                startSample += chunk;
            }
            return;
        }

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
                // kIrWetMakeupGain applies only to the just-convolved wet
                // sample (chL[i]/chR[i] here), never to the dry component --
                // see the constant's declaration below for the full
                // DECIDED CONVENTION derivation/citation.
                chL[i] = dryL[i] * (1.0f - m) + (chL[i] * kIrWetMakeupGain) * m;
                if (numChannels > 1)
                    chR[i] = dryR[i] * (1.0f - m) + (chR[i] * kIrWetMakeupGain) * m;
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
    // DECIDED CONVENTION (月月 2026-09-16 裁決 D9 選項 A;
    // reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md §5/裁決記錄):
    // IR（convolution）模式的 wet 路徑相對 ALGO 路徑的響度結構性偏低，
    // 4 樣本（3 顆 EchoThief 真實 IR：Stairwells/Venues/Sanctuaries ＋ 1 顆
    // 既有合成 IR）平均落差 -28.58 dB（見
    // reports/gate_outputs/wf0914_D9b_ir_injection.txt §3/§4：-28.483 /
    // -28.726 / -28.487 / -28.623 dB，展幅僅 0.24 dB）。這是 ALGO（回饋式
    // comb/allpass）與 IR（一次性正規化摺積）兩種演算法結構性的響度差異，
    // 不是個別 IR 檔案本身比較安靜——JUCE 的 Convolution::Normalise::yes
    // （宣告預設值，EffectChain::loadImpulseResponse() 未覆寫）已把不同
    // IR 檔案本身的能量正規化掉，3 顆真實 IR 的 wet RMS 展幅只有 0.24 dB，
    // 遠小於這些 IR 檔案本身寬頻 RMS 的 16.6 dB 展幅（詳見上述裁決包 §2/§3）。
    // kIrWetMakeupGain = 26.9f（+28.58 dB，= 10^(28.58/20)，4 樣本平均落差
    // 的反相補償）把這個結構性落差補平，只乘在 IR wet 訊號上（dry 訊號、
    // ALGO 路徑一概不動，見 processBlock() 的施加點）。**非物理常數**，
    // 是 4 樣本平均值反推的工程慣例（DECIDED CONVENTION），樣本僅涵蓋
    // 3 種空間尺度（小房間／樓梯間、音樂廳、教堂座堂），非窮舉。
    // 對齊參考（WF0925-K1，staged-review:D9c-calib）：對齊參考＝ALGO 預設
    // size 0.5、未指定 T60（K-02 量測時 pReverbSize/pReverbDecay 皆未設）；
    // IR 路徑本身不看 size/T60（irMode 時不呼叫 setRoomSize/setDecayTime），
    // 所以「IR 與 ALGO 響度一致」只在這組預設下成立。其他 size 依 Python
    // 複製版估計差 −1.4～+4.0 dB（size 0.0 −1.36／1.0 +3.98）、其他 T60
    // 差 −2.4～+5.3 dB（0.3 s −2.38／30 s +5.26）（估計，非量測產品 binary；
    // 出處 reports/status_check_2026-09-25/probes/reverb_gain_replica_output.txt，
    // 腳本 reverb_gain_replica.py 同目錄）。純說明，數值不變。
    // WF1002-C1 補註（盤點 E18 查證修正；WF0925 稽核用詞 note）：
    // (1) 26.9 倍裡約 18.06 dB 來自 JUCE Convolution 的正規化係數 0.125
    //     （−20·log10(0.125) = 18.06 dB；libs/JUCE/modules/juce_dsp/frequency/
    //     juce_Convolution.cpp:628，Normalise::yes 路徑）——JUCE 升版若改了
    //     這個係數，「26.9 沒被改」的 D9c-guard 照樣綠燈，所以 audit_repro
    //     另有 Q01 的 |IR−ALGO| ≤ 0.25 dB 響度 CHECK（月月 2026-10-02 核准）。
    // (2) 用詞：嚴格算 20·log10(26.9) = 28.595 dB；上文「+28.58 dB」是 4 樣本
    //     平均落差的原數字（反相補償的目標值），兩者差 0.015 dB，不是筆誤。
    // 純註解，數值不變。
    static constexpr float kIrWetMakeupGain = 26.9f;

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
