#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "../dsp/ModalResonator.h"
#include "../dsp/NoiseGen.h"
#include "../dsp/BiquadFilter.h"
#include "../dsp/Envelope.h"
#include "../physics/BeamModel.h"
#include "../physics/PlateModel.h"
#include "../physics/MaterialDB.h"

/**
 * Chromatic Synth 引擎 — 三合一
 *   0 = Tongue Drum（Euler-Bernoulli 梁）
 *   1 = Water Gong （Kirchhoff 圓板）
 *   2 = Custom     （使用者自填 ratio/amplitude）
 */

class ChromaticSound : public juce::SynthesiserSound
{
public:
    bool appliesToNote (int) override    { return true; }
    bool appliesToChannel (int) override { return true; }
};

class ChromaticVoice : public juce::SynthesiserVoice
{
public:
    void setMaterialDB (MaterialDB* db) { materialDB = db; }

    // 參數指標（由 Processor 設定）
    std::atomic<float>* pSubEngine     = nullptr;  // 0=beam, 1=plate, 2=custom
    std::atomic<float>* pMaterial      = nullptr;
    std::atomic<float>* pStrikePos     = nullptr;
    std::atomic<float>* pThickness     = nullptr;  // mm
    std::atomic<float>* pSize          = nullptr;   // mm (beam=length, plate=radius)
    std::atomic<float>* pExciter       = nullptr;   // 0~3
    std::atomic<float>* pPitchGlide    = nullptr;   // water gong 水位效果 (0~1)

    bool canPlaySound (juce::SynthesiserSound* s) override
    {
        return dynamic_cast<ChromaticSound*> (s) != nullptr;
    }

    void startNote (int midiNoteNumber, float velocity,
                    juce::SynthesiserSound*, int) override
    {
        if (materialDB == nullptr) return;

        auto keys = MaterialDB::getOrderedKeys();
        int matIdx = juce::jlimit (0, keys.size() - 1, (int) pMaterial->load());
        auto* mat = materialDB->getMaterial (keys[matIdx]);
        if (mat == nullptr) return;

        int subEngine = (int) pSubEngine->load();
        float strikePos = pStrikePos->load();
        float thickness = pThickness->load() * 0.001f;  // mm -> m
        float size      = pSize->load() * 0.001f;       // mm -> m
        float exciter   = pExciter->load();
        glideAmount     = pPitchGlide->load();

        std::vector<ModalResonator::Mode> modes;

        if (subEngine == 0)  // Tongue Drum (beam)
        {
            BeamModel::Params bp;
            bp.length    = BeamModel::lengthFromMidiNote (midiNoteNumber);
            bp.width     = size > 0.001f ? size : 0.02f;
            bp.thickness = thickness > 0.0001f ? thickness : 0.003f;
            bp.strikePosition = strikePos;
            bp.numModes  = 12;
            modes = BeamModel::calculateModes (bp, *mat);
        }
        else if (subEngine == 1)  // Water Gong (plate)
        {
            PlateModel::Params pp;
            pp.radius    = PlateModel::radiusFromMidiNote (midiNoteNumber);
            pp.thickness = thickness > 0.0001f ? thickness : 0.003f;
            pp.strikePosition = strikePos;
            pp.numModes  = 20;
            modes = PlateModel::calculateModes (pp, *mat);
        }
        else  // Custom harmonics
        {
            modes = buildCustomModes (midiNoteNumber, *mat);
        }

        // 保存基礎模態用於 pitch glide
        baseModes = modes;
        glidePhase = 0.0f;

        resonator.setSampleRate (getSampleRate());
        resonator.setModes (modes);
        resonator.excite (velocity);

        setupExciter (exciter, velocity);
        damped = false;
    }

    void stopNote (float, bool allowTailOff) override
    {
        if (allowTailOff)
        {
            if (! damped)
            {
                resonator.damp (0.08f);
                damped = true;
            }
        }
        else
        {
            clearCurrentNote();
        }
    }

    void pitchWheelMoved (int) override {}
    void controllerMoved (int cc, int val) override
    {
        if (cc == 64 && val < 64 && ! damped)
        {
            resonator.damp (0.08f);
            damped = true;
        }
    }

    void renderNextBlock (juce::AudioBuffer<float>& outputBuffer,
                          int startSample, int numSamples) override
    {
        bool anyActive = false;

        // Water gong pitch glide（持續降低模態頻率模擬浸水效果）
        if (glideAmount > 0.01f && ! baseModes.empty())
        {
            glidePhase += glideAmount * 0.00002f;  // slow glide
            if (glidePhase < 0.5f)
            {
                float glideMul = 1.0f - glidePhase * 0.3f;  // max 15% pitch drop
                auto glidedModes = baseModes;
                for (auto& m : glidedModes)
                    m.frequency *= glideMul;
                // 只更新頻率，不重新 excite
                resonator.setModes (glidedModes);
            }
        }

        while (--numSamples >= 0)
        {
            float sample = 0.0f;

            if (resonator.isActive())
            {
                sample += resonator.processSample();
                anyActive = true;
            }

            if (exciterEnv.isActive())
            {
                float noise = noiseGen.processSample();
                noise = exciterFilter.processSample (noise);
                sample += noise * exciterEnv.process();
                anyActive = true;
            }

            sample *= 0.2f;

            for (int ch = 0; ch < outputBuffer.getNumChannels(); ++ch)
                outputBuffer.addSample (ch, startSample, sample);

            ++startSample;
        }

        if (! anyActive)
            clearCurrentNote();
    }

private:
    /// Custom harmonics mode: user-defined ratio/amplitude
    std::vector<ModalResonator::Mode> buildCustomModes (
        int midiNote, const MaterialDB::Material& mat)
    {
        float fundamental = 440.0f * std::pow (2.0f, (float) (midiNote - 69) / 12.0f);
        // 預設 custom ratios（模擬原型 chromatic-synth.html 的手動泛音）
        static constexpr float ratios[]  = { 1.0f, 2.0f, 3.0f, 4.16f, 5.43f, 6.98f, 8.21f, 10.0f };
        static constexpr float amps[]    = { 1.0f, 0.7f, 0.5f, 0.35f, 0.25f, 0.18f, 0.12f, 0.08f };
        static constexpr int count = 8;

        std::vector<ModalResonator::Mode> modes;
        const float alpha = mat.damping.alpha;
        const float beta  = mat.damping.beta_air;
        const float gamma = mat.damping.gamma_radiation;

        for (int i = 0; i < count; ++i)
        {
            float freq = fundamental * ratios[i];
            if (freq > 20000.0f) break;

            float decayDenom = alpha + beta * freq * freq + gamma * freq;
            float decay = (decayDenom > 0.0f) ? (1.0f / decayDenom) : 5.0f;

            modes.push_back ({ freq, amps[i], decay });
        }
        return modes;
    }

    void setupExciter (float hardness, float velocity)
    {
        static constexpr float cutoffs[]   = { 500.0f, 1500.0f, 4000.0f, 10000.0f };
        static constexpr float durations[] = { 0.005f, 0.003f,  0.002f,  0.001f };
        int idx = juce::jlimit (0, 3, (int) hardness);

        exciterFilter.setSampleRate (getSampleRate());
        exciterFilter.setParams (BiquadFilter::Type::LowPass, cutoffs[idx], 0.707f);
        exciterFilter.reset();
        noiseGen.setType (NoiseGen::Type::White);
        noiseGen.reset();
        exciterEnv.trigger (velocity * 0.2f, durations[idx], getSampleRate());
    }

    MaterialDB*    materialDB = nullptr;
    ModalResonator resonator;
    bool           damped = false;

    NoiseGen           noiseGen;
    BiquadFilter       exciterFilter;
    Envelope::ExpDecay exciterEnv;

    // Pitch glide state (water gong)
    std::vector<ModalResonator::Mode> baseModes;
    float glideAmount = 0.0f;
    float glidePhase  = 0.0f;
};
