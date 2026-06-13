#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "../dsp/ModalResonator.h"
#include "../dsp/NoiseGen.h"
#include "../dsp/BiquadFilter.h"
#include "../dsp/BodyResonance.h"
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

enum class ExciterType { Cotton = 0, Felt = 1, Wood = 2, Metal = 3 };

struct CimbalomParams
{
    std::string materialKey;
    double strikePosition   = 0.3;
    ExciterType exciter     = ExciterType::Wood;
    double diameterMm       = 0.8;
    int    numStrings       = 3;
    float  detuningCents    = 5.0f;
    double tensionOverride  = 0.0;   // >0 = use this tension (N), 0 = auto-calculate
    double dampingOverride  = -1.0;  // >=0 = override material damping alpha
};

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

        // Macro: Body → detuning spread + body resonance layer
        detCents *= (0.4f + mBody * 1.2f);

        bodyRes.prepare (getSampleRate());
        bodyRes.setAmount (mBody);
        bodyRes.reset();

        // ── 弦參數 ──
        StringModel::Params sp;
        sp.length         = StringModel::lengthFromMidiNote (midiNoteNumber);
        sp.tension        = StringModel::tensionForNote (midiNoteNumber,
                                sp.length, diameter, mat->density);
        sp.diameter       = diameter;
        sp.strikePosition = strikePos;
        sp.numModes       = 40;

        auto baseModes = StringModel::calculateModes (sp, *mat);

        // Material spectral tilt: stiffer materials sustain more overtones
        float logE = std::log10 (mat->youngsModulus);
        float spectralTilt = juce::jlimit (0.1f, 1.0f, (logE - 7.5f) / 4.0f);

        // Hammer force spectrum: soft hammers excite fewer high partials
        int hammerIdx = juce::jlimit (0, 3, (int) hammer);
        static constexpr float hammerCutoffPartial[] = { 3.0f, 8.0f, 20.0f, 60.0f };
        float hCut = hammerCutoffPartial[hammerIdx];

        if (! baseModes.empty())
        {
            float f1ref = baseModes[0].frequency;
            for (auto& m : baseModes)
            {
                float partialN = m.frequency / f1ref;
                m.amplitude *= std::pow (spectralTilt, (partialN - 1.0f) * 0.2f);
                float r = partialN / hCut;
                m.amplitude *= 1.0f / (1.0f + r * r);
            }
        }

        // Macro: Tension → mode frequency, Material → sustain, Damping → decay
        float tScale = 0.85f + mTension * 0.30f;
        float matScale = 0.5f + mMaterial;
        float dmpScale = 1.0f + (0.5f - mDamping) * 1.4f;

        for (auto& m : baseModes)
        {
            m.frequency *= tScale;
            m.decayTime *= matScale * dmpScale;
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
        float materialBright = juce::jlimit (0.15f, 2.0f, spectralTilt * 2.0f);
        setupExciter (hammer, velocity, mBrightness, mNoise, materialBright, getSampleRate());
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
            // Quick fade-out to avoid click on voice stealing
            for (int s = 0; s < numActiveStrings; ++s)
                strings[s].damp (0.002f);
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

    // ── Standalone API (CLI / ScoreRenderer) ──

    void prepare (double sr) { standaloneSR = sr; }

    void noteOn (int midiNote, float velocity,
                 const MaterialDB::Material& mat, const CimbalomParams& params)
    {
        double sr = standaloneSR;

        float strikePos = juce::jlimit (0.05f, 0.95f,
                                        static_cast<float> (params.strikePosition));
        float diameter  = static_cast<float> (params.diameterMm) * 0.001f;
        int   nStrings  = juce::jlimit (1, kMaxStringsPerCourse, params.numStrings);
        float detCents  = params.detuningCents;
        int   hammerIdx = juce::jlimit (0, 3, static_cast<int> (params.exciter));

        StringModel::Params sp;
        sp.length         = StringModel::lengthFromMidiNote (midiNote);
        sp.tension        = (params.tensionOverride > 0.0)
                                ? static_cast<float> (params.tensionOverride)
                                : StringModel::tensionForNote (midiNote,
                                      sp.length, diameter, mat.density);
        sp.diameter       = diameter;
        sp.strikePosition = strikePos;
        sp.numModes       = 40;

        auto baseModes = StringModel::calculateModes (sp, mat);

        // Apply damping override if specified
        if (params.dampingOverride >= 0.0)
        {
            float alpha = static_cast<float> (params.dampingOverride);
            for (auto& m : baseModes)
                m.decayTime = (alpha > 0.0f) ? (1.0f / alpha) : 5.0f;
        }

        float logE = std::log10 (mat.youngsModulus);
        float spectralTilt = juce::jlimit (0.1f, 1.0f, (logE - 7.5f) / 4.0f);

        static constexpr float hCutPartial[] = { 3.0f, 8.0f, 20.0f, 60.0f };
        float hCut = hCutPartial[hammerIdx];

        if (! baseModes.empty())
        {
            float f1ref = baseModes[0].frequency;
            for (auto& m : baseModes)
            {
                float partialN = m.frequency / f1ref;
                m.amplitude *= std::pow (spectralTilt, (partialN - 1.0f) * 0.2f);
                float r = partialN / hCut;
                m.amplitude *= 1.0f / (1.0f + r * r);
            }
        }

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

            strings[s].setSampleRate (sr);
            strings[s].setModes (modes);
            strings[s].excite (velocity);
        }

        float materialBright = juce::jlimit (0.15f, 2.0f, spectralTilt * 2.0f);
        setupExciter (static_cast<float> (hammerIdx), velocity,
                      0.5f, 0.0f, materialBright, sr);

        bodyRes.prepare (sr);
        bodyRes.setAmount (0.5f);
        bodyRes.reset();
        damped = false;
    }

    void noteOff() { applyDamp(); }

    bool isActive() const
    {
        for (int s = 0; s < numActiveStrings; ++s)
            if (strings[s].isActive()) return true;
        return exciterEnv.isActive();
    }

    float getNextSample()
    {
        float sample = 0.0f;
        for (int s = 0; s < numActiveStrings; ++s)
            if (strings[s].isActive())
                sample += strings[s].processSample();

        if (exciterEnv.isActive())
        {
            float noise = noiseGen.processSample();
            noise = exciterFilter.processSample (noise);
            sample += noise * exciterEnv.process();
        }

        sample += bodyRes.processSample (sample);
        return sample;
    }

    void scaleFrequencies (double factor)
    {
        for (int s = 0; s < numActiveStrings; ++s)
            strings[s].scaleFrequencies (factor);
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

            // Body resonance layer
            sample += bodyRes.processSample (sample);

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
                       float brightMacro, float noiseMacro,
                       float materialBright, double sr)
    {
        static constexpr float cutoffs[]   = { 500.0f, 1500.0f, 4000.0f, 10000.0f };
        static constexpr float durations[] = { 0.004f, 0.003f,  0.002f,  0.001f };

        int idx = juce::jlimit (0, 3, (int) hardness);

        float cutoff = cutoffs[idx] * (0.3f + brightMacro * 1.4f) * materialBright;
        cutoff = juce::jlimit (200.0f, 16000.0f, cutoff);

        exciterFilter.setSampleRate (sr);
        exciterFilter.setParams (BiquadFilter::Type::LowPass, cutoff, 0.707f);
        exciterFilter.reset();

        noiseGen.setType (NoiseGen::Type::White);
        noiseGen.reset();

        static constexpr float noiseAmps[] = { 0.10f, 0.20f, 0.40f, 0.70f };
        float amp = velocity * noiseAmps[idx] * (1.0f + noiseMacro * 3.0f);
        float durScale = juce::jlimit (0.5f, 3.0f, 1.5f / (materialBright + 0.5f));
        exciterEnv.trigger (amp, durations[idx] * durScale, sr);
    }

    MaterialDB*    materialDB = nullptr;
    double         standaloneSR = 0.0;
    ModalResonator strings[kMaxStringsPerCourse];
    int            numActiveStrings = 1;
    bool           damped = false;

    NoiseGen           noiseGen;
    BiquadFilter       exciterFilter;
    Envelope::ExpDecay exciterEnv;
    BodyResonance      bodyRes;
};
