#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "../dsp/ModalResonator.h"
#include "../dsp/NoiseGen.h"
#include "../dsp/BiquadFilter.h"
#include "../dsp/Envelope.h"
#include "../physics/StringModel.h"
#include "../physics/MaterialDB.h"

/**
 * Cimbalom 引擎 — 物理建模弦振動
 *
 * 架構：
 *   MIDI Note On → Exciter (槌頭噪音脈衝)
 *                → String Resonator ×N (微失諧 beating)
 *                → output
 *
 *   MIDI Note Off / CC#64 → Damper (加速衰減)
 */

static constexpr int kMaxStringsPerCourse = 5;

// ─── Sound ───
class CimbalomSound : public juce::SynthesiserSound
{
public:
    bool appliesToNote (int) override    { return true; }
    bool appliesToChannel (int) override { return true; }
};

// ─── Voice ───
class CimbalomVoice : public juce::SynthesiserVoice
{
public:
    void setMaterialDB (MaterialDB* db) { materialDB = db; }

    // 參數指標（由 Processor 設定，指向 APVTS 的 raw parameter）
    std::atomic<float>* pMaterial       = nullptr;  // index
    std::atomic<float>* pStrikePos      = nullptr;  // 0.05 ~ 0.95
    std::atomic<float>* pDiameter       = nullptr;  // mm
    std::atomic<float>* pHammerHardness = nullptr;  // 0~3
    std::atomic<float>* pNumStrings     = nullptr;  // 1~5
    std::atomic<float>* pDetuning       = nullptr;  // cents

    // Macro 參數指標
    std::atomic<float>* pMacroMaterial   = nullptr;
    std::atomic<float>* pMacroTension    = nullptr;
    std::atomic<float>* pMacroDamping    = nullptr;
    std::atomic<float>* pMacroStrike     = nullptr;
    std::atomic<float>* pMacroBrightness = nullptr;
    std::atomic<float>* pMacroBody       = nullptr;
    std::atomic<float>* pMacroNoise      = nullptr;

    bool canPlaySound (juce::SynthesiserSound* sound) override
    {
        return dynamic_cast<CimbalomSound*> (sound) != nullptr;
    }

    void startNote (int midiNoteNumber, float velocity,
                    juce::SynthesiserSound*, int) override
    {
        if (materialDB == nullptr) return;

        // ── 讀取參數 ──
        auto keys = MaterialDB::getOrderedKeys();
        int matIdx = juce::jlimit (0, keys.size() - 1,
                                   (int) pMaterial->load());
        auto* mat = materialDB->getMaterial (keys[matIdx]);
        if (mat == nullptr) return;

        float strikePos = pStrikePos->load();
        float diameter  = pDiameter->load() * 0.001f;   // mm → m
        int   nStrings  = juce::jlimit (1, kMaxStringsPerCourse,
                                        (int) pNumStrings->load());
        float detCents  = pDetuning->load();
        float hammer    = pHammerHardness->load();

        // ── 讀取 Macro（中心 0.5 = 無變化）──
        float mMaterial   = pMacroMaterial   ? pMacroMaterial->load()   : 0.5f;
        float mTension    = pMacroTension    ? pMacroTension->load()    : 0.5f;
        float mDamping    = pMacroDamping    ? pMacroDamping->load()    : 0.5f;
        float mStrike     = pMacroStrike     ? pMacroStrike->load()     : 0.5f;
        float mBrightness = pMacroBrightness ? pMacroBrightness->load() : 0.5f;
        float mBody       = pMacroBody       ? pMacroBody->load()       : 0.5f;
        float mNoise      = pMacroNoise      ? pMacroNoise->load()      : 0.0f;

        // Macro: Strike → blend with per-engine strike
        strikePos *= (0.5f + mStrike);
        strikePos = juce::jlimit (0.05f, 0.95f, strikePos);

        // Macro: Body → detuning spread
        detCents *= (0.4f + mBody * 1.2f);

        // ── 弦參數 ──
        StringModel::Params sp;
        sp.length         = StringModel::lengthFromMidiNote (midiNoteNumber);
        sp.tension        = StringModel::tensionForNote (midiNoteNumber,
                                sp.length, diameter, mat->density);
        sp.diameter       = diameter;
        sp.strikePosition = strikePos;
        sp.numModes       = 40;

        auto baseModes = StringModel::calculateModes (sp, *mat);

        // Macro: Tension → mode frequency, Material → sustain, Damping → decay
        float tScale = 0.85f + mTension * 0.30f;
        float matScale = 0.5f + mMaterial;
        float dmpScale = 1.0f + (0.5f - mDamping) * 1.4f;

        for (auto& m : baseModes)
        {
            m.frequency *= tScale;
            m.decay *= matScale * dmpScale;
        }

        // ── 多弦 beating ──
        numActiveStrings = nStrings;
        float gain = 1.0f / std::sqrt ((float) numActiveStrings);

        for (int s = 0; s < numActiveStrings; ++s)
        {
            float centOffset = 0.0f;
            if (numActiveStrings > 1)
                centOffset = detCents
                    * (2.0f * (float) s / (float) (numActiveStrings - 1) - 1.0f);

            float freqMul = std::pow (2.0f, centOffset / 1200.0f);

            auto modes = baseModes;
            for (auto& m : modes)
            {
                m.frequency *= freqMul;
                m.amplitude *= gain;
            }

            strings[s].setSampleRate (getSampleRate());
            strings[s].setModes (modes);
            strings[s].excite (velocity);
        }

        // ── Exciter（槌頭噪音脈衝）──
        setupExciter (hammer, velocity, mBrightness, mNoise);
        damped = false;
    }

    void stopNote (float, bool allowTailOff) override
    {
        if (allowTailOff)
        {
            applyDamp();
        }
        else
        {
            clearCurrentNote();
        }
    }

    void pitchWheelMoved (int) override {}

    void controllerMoved (int controller, int value) override
    {
        // CC#64 Sustain Pedal：放開時制音
        if (controller == 64 && value < 64)
            applyDamp();
    }

    void renderNextBlock (juce::AudioBuffer<float>& outputBuffer,
                          int startSample, int numSamples) override
    {
        bool anyActive = false;

        while (--numSamples >= 0)
        {
            float sample = 0.0f;

            // 弦共振
            for (int s = 0; s < numActiveStrings; ++s)
            {
                if (strings[s].isActive())
                {
                    sample += strings[s].processSample();
                    anyActive = true;
                }
            }

            // 槌頭瞬態噪音
            if (exciterEnv.isActive())
            {
                float noise = noiseGen.processSample();
                noise = exciterFilter.processSample (noise);
                sample += noise * exciterEnv.process();
                anyActive = true;
            }

            // 輸出（master gain 防 clipping）
            sample *= 0.15f;

            for (int ch = 0; ch < outputBuffer.getNumChannels(); ++ch)
                outputBuffer.addSample (ch, startSample, sample);

            ++startSample;
        }

        if (! anyActive)
            clearCurrentNote();
    }

private:
    void applyDamp()
    {
        if (! damped)
        {
            for (int s = 0; s < numActiveStrings; ++s)
                strings[s].damp (0.05f);
            damped = true;
        }
    }

    void setupExciter (float hardness, float velocity,
                       float brightMacro = 0.5f, float noiseMacro = 0.0f)
    {
        // 槌硬度 → 噪音頻寬
        //   0=cotton(柔) 1=felt 2=wood 3=metal(硬)
        static constexpr float cutoffs[]   = { 500.0f, 1500.0f, 4000.0f, 10000.0f };
        static constexpr float durations[] = { 0.004f, 0.003f,  0.002f,  0.001f };

        int idx = juce::jlimit (0, 3, (int) hardness);

        // Brightness macro: scale cutoff (0→×0.3, 0.5→×1.0, 1→×1.7)
        float cutoff = cutoffs[idx] * (0.3f + brightMacro * 1.4f);
        cutoff = juce::jlimit (200.0f, 16000.0f, cutoff);

        exciterFilter.setSampleRate (getSampleRate());
        exciterFilter.setParams (BiquadFilter::Type::LowPass, cutoff, 0.707f);
        exciterFilter.reset();

        noiseGen.setType (NoiseGen::Type::White);
        noiseGen.reset();

        // Noise macro: boost exciter amplitude (0→×1, 1→×4)
        float amp = velocity * 0.25f * (1.0f + noiseMacro * 3.0f);
        exciterEnv.trigger (amp, durations[idx], getSampleRate());
    }

    MaterialDB*    materialDB = nullptr;
    ModalResonator strings[kMaxStringsPerCourse];
    int            numActiveStrings = 1;
    bool           damped = false;

    NoiseGen           noiseGen;
    BiquadFilter       exciterFilter;
    Envelope::ExpDecay exciterEnv;
};
