#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "../dsp/ModalResonator.h"
#include "../dsp/NoiseGen.h"
#include "../dsp/BiquadFilter.h"
#include "../dsp/BodyResonance.h"
#include "../dsp/Envelope.h"
#include "../dsp/DiagnosticOverrides.h"
#include "../physics/BeamModel.h"
#include "../physics/PlateModel.h"
#include "../physics/MaterialDB.h"
#include "../physics/HammerImpulse.h"
#include <algorithm>

/**
 * Chromatic Synth 引擎 — 三合一
 *   0 = Tongue Drum（Euler-Bernoulli 梁）
 *   1 = Water Gong （Kirchhoff 圓板；free/clamped 邊界見 PlateModel.h）
 *   2 = Custom     （使用者自填 ratio/amplitude）
 */

enum class ChromaticSubEngine { TongueDrum = 0, WaterGong = 1, CustomHarmonics = 2 };

struct ChromaticParams
{
    std::string materialKey;
    ChromaticSubEngine subEngine = ChromaticSubEngine::TongueDrum;
    double strikePosition   = 0.3;
    double plateRadius      = 0.12;
    double plateThickness   = 0.003;
    double tongueLength     = 0.1;
    double tongueWidth      = 0.025;
    double tongueThickness  = 0.003;
    BeamModel::Boundary tongueBoundary = BeamModel::Boundary::Cantilever;
    float  exciterHardness  = 1.0f;
    bool   plateFreeEdge    = true;   // true = free-edge (physical water gong: hung, edges free)
    bool   tuneToMidi       = true;   // false = retain geometry/material absolute frequencies
    uint64_t randomSeed     = 0x5453554B4953594Eull; // "TSUKISYN"
    uint64_t eventIndex     = 0;
};

inline void filterChromaticModesForSampleRate (
    std::vector<ModalResonator::Mode>& modes, double sampleRate)
{
    const float maxFrequency = (float) std::min (20000.0, sampleRate * 0.5 * 0.98);
    modes.erase (
        std::remove_if (modes.begin(), modes.end(), [maxFrequency] (const auto& mode)
        {
            return ! std::isfinite (mode.frequency)
                || mode.frequency <= 0.0f
                || mode.frequency > maxFrequency;
        }),
        modes.end());
}

inline void tuneChromaticModesToMidi (
    std::vector<ModalResonator::Mode>& modes, int midiNote,
    double sampleRate = 44100.0)
{
    if (modes.empty()
        || ! std::isfinite (modes.front().frequency)
        || modes.front().frequency <= 0.0f)
        return;

    const float target = 440.0f
        * std::pow (2.0f, (float) (midiNote - 69) / 12.0f);
    const float scale = target / modes.front().frequency;
    for (auto& mode : modes)
        mode.frequency *= scale;

    filterChromaticModesForSampleRate (modes, sampleRate);
}

class ChromaticSound : public juce::SynthesiserSound
{
public:
    bool appliesToNote (int) override    { return true; }
    bool appliesToChannel (int) override { return true; }
};

class ChromaticVoice : public juce::SynthesiserVoice
{
public:
    ChromaticVoice()
    {
        modeScratch.reserve (20);
        baseModes.reserve (20);
        resonator.reserveModes (20);
    }

    void setMaterialDB (MaterialDB* db) { materialDB = db; }
    void setNoiseIdentity (uint64_t identity) { noiseIdentity = identity; }

    // 參數指標（由 Processor 設定）
    std::atomic<float>* pSubEngine     = nullptr;  // 0=beam, 1=plate, 2=custom
    std::atomic<float>* pMaterial      = nullptr;
    std::atomic<float>* pStrikePos     = nullptr;
    std::atomic<float>* pThickness     = nullptr;  // mm
    std::atomic<float>* pSize          = nullptr;   // geometry scale: Tongue length / Water Gong radius
    std::atomic<float>* pExciter       = nullptr;   // 0~3
    std::atomic<float>* pPitchGlide    = nullptr;   // water gong 水位效果 (0~1)

    // Custom harmonic parameters (8 ratios + 8 amplitudes)
    std::atomic<float>* pRatio[8] = {};
    std::atomic<float>* pAmp[8]   = {};

    // Macro 參數指標
    std::atomic<float>* pMacroMaterial   = nullptr;
    std::atomic<float>* pMacroTension    = nullptr;
    std::atomic<float>* pMacroDamping    = nullptr;
    std::atomic<float>* pMacroStrike     = nullptr;
    std::atomic<float>* pMacroBrightness = nullptr;
    std::atomic<float>* pMacroBody       = nullptr;
    std::atomic<float>* pMacroNoise      = nullptr;

    bool canPlaySound (juce::SynthesiserSound* s) override
    {
        return dynamic_cast<ChromaticSound*> (s) != nullptr;
    }

    void startNote (int midiNoteNumber, float velocity,
                    juce::SynthesiserSound*, int) override
    {
        if (materialDB == nullptr) return;

        const auto& keys = MaterialDB::getOrderedKeys();
        int matIdx = juce::jlimit (0, keys.size() - 1, (int) pMaterial->load());
        auto* mat = materialDB->getMaterial (keys[matIdx]);
        if (mat == nullptr) return;

        int subEngine = (int) pSubEngine->load();
        outputGain = subEngineOutputGain (subEngine);
        float strikePos = pStrikePos->load();
        float thickness = pThickness->load() * 0.001f;  // mm -> m
        float size      = pSize->load() * 0.001f;       // mm -> m
        float exciter   = pExciter->load();
        glideAmount     = pPitchGlide->load();

        // ── 讀取 Macro ──
        float mMaterial   = pMacroMaterial   ? pMacroMaterial->load()   : 0.5f;
        float mTension    = pMacroTension    ? pMacroTension->load()    : 0.5f;
        float mDamping    = pMacroDamping    ? pMacroDamping->load()    : 0.5f;
        float mStrike     = pMacroStrike     ? pMacroStrike->load()     : 0.5f;
        float mBrightness = pMacroBrightness ? pMacroBrightness->load() : 0.5f;
        float mBody       = pMacroBody       ? pMacroBody->load()       : 0.5f;
        float mNoise      = pMacroNoise      ? pMacroNoise->load()      : 0.0f;

        // Macro: Strike → blend with per-engine strike
        strikePos *= (0.5f + mStrike);
        strikePos = juce::jlimit (0.0f, 1.0f, strikePos);

        // Macro: Body -> resonator geometry modifier + body resonance layer
        size *= (0.5f + mBody);

        bodyRes.prepare (getSampleRate());
        bodyRes.setAmount (mBody);
        bodyRes.reset();

        auto& modes = modeScratch;
        modes.clear();

        if (subEngine == 0)  // Tongue Drum (beam)
        {
            BeamModel::Params bp;
            const float sizeScale = juce::jlimit (0.5f, 5.0f, size / 0.02f);
            bp.length    = BeamModel::lengthFromMidiNote (midiNoteNumber) * sizeScale;
            bp.width     = 0.02f;
            bp.thickness = thickness > 0.0001f ? thickness : 0.003f;
            bp.strikePosition = strikePos;
            bp.numModes  = 12;
            BeamModel::calculateModes (bp, *mat, modes);
            tuneChromaticModesToMidi (modes, midiNoteNumber, getSampleRate());
        }
        else if (subEngine == 1)  // Water Gong (plate)
        {
            PlateModel::Params pp;
            const float sizeScale = juce::jlimit (0.5f, 5.0f, size / 0.02f);
            pp.radius    = PlateModel::radiusFromMidiNote (midiNoteNumber) * sizeScale;
            pp.thickness = thickness > 0.0001f ? thickness : 0.003f;
            pp.strikePosition = strikePos;
            pp.numModes  = 20;
            pp.freeEdge  = true;
            PlateModel::calculateModes (pp, *mat, modes);
            tuneChromaticModesToMidi (modes, midiNoteNumber, getSampleRate());
        }
        else  // Custom harmonics
        {
            buildCustomModes (midiNoteNumber, *mat, modes);
        }

        // Macro: Tension → frequency, Material → sustain, Damping → decay
        float tScale = 0.85f + mTension * 0.30f;
        float matScale = 0.5f + mMaterial;
        float dmpScale = 1.0f + (0.5f - mDamping) * 1.4f;

        for (auto& m : modes)
        {
            m.frequency *= tScale;
            m.decayTime = decayTimeForMode (subEngine, m.frequency, *mat)
                        * matScale * dmpScale;
        }

        configureCreativeBodyLayer (modes);

        // Hammer force-impulse spectrum (M2 2a/2b). Beam (tongue drum) and
        // plate (water gong) are struck rigid bodies in the physics-verified
        // domain (ROADMAP_PHYSICS.md §0); Custom Harmonics (subEngine==2) is
        // user-authored additive synthesis, not a physical strike model, so it
        // is intentionally left untouched — applying a hammer spectrum there
        // would silently distort user-specified amplitudes. See HammerImpulse.h
        // for the half-sine contact-pulse derivation and tau_c sources.
        if (subEngine == 0 || subEngine == 1)
        {
            float tauC = HammerImpulse::tauCForStrike (exciter, velocity);
            for (auto& m : modes)
            {
                float omega = juce::MathConstants<float>::twoPi * m.frequency;
                m.amplitude *= HammerImpulse::forceSpectrumMagnitude (omega, tauC);
            }
        }

        // 保存基礎模態用於 pitch glide
        baseModes = modes;
        glidePhase = 0.0f;

        resonator.setSampleRate (getSampleRate());
        resonator.setModes (modes);
        resonator.excite (velocity);

        setupExciter (exciter, velocity, mBrightness, mNoise, getSampleRate());
        seedNoise (0x504C5547494Eull, noiseEventCounter++, midiNoteNumber, velocity);
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
            resonator.damp (0.002f);
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

    // ── Standalone API (CLI / ScoreRenderer) ──

    void prepare (double sr) { standaloneSR = sr; }

    void noteOn (int midiNote, float velocity,
                 const MaterialDB::Material& mat, const ChromaticParams& params)
    {
        double sr = standaloneSR;

        int subEng = static_cast<int> (params.subEngine);
        outputGain = subEngineOutputGain (subEng);
        float strikePos = juce::jlimit (0.0f, 1.0f,
                                        static_cast<float> (params.strikePosition));
        float thickness = static_cast<float> (params.plateThickness > 0.0001
                                              ? params.plateThickness : 0.003);

        glideAmount = 0.0f;

        auto& modes = modeScratch;
        modes.clear();

        if (subEng == 0)
        {
            BeamModel::Params bp;
            bp.length    = static_cast<float> (params.tongueLength);
            bp.width     = static_cast<float> (params.tongueWidth);
            bp.thickness = static_cast<float> (params.tongueThickness);
            bp.boundary   = params.tongueBoundary;
            bp.strikePosition = strikePos;
            bp.numModes  = 12;
            BeamModel::calculateModes (bp, mat, modes);
            if (params.tuneToMidi)
                tuneChromaticModesToMidi (modes, midiNote, sr);
        }
        else if (subEng == 1)
        {
            PlateModel::Params pp;
            pp.radius    = static_cast<float> (params.plateRadius);
            pp.thickness = thickness;
            pp.strikePosition = strikePos;
            pp.numModes  = 20;
            pp.freeEdge  = params.plateFreeEdge;
            PlateModel::calculateModes (pp, mat, modes);
            if (params.tuneToMidi)
                tuneChromaticModesToMidi (modes, midiNote, sr);
        }
        else
        {
            buildCustomModes (midiNote, mat, modes);
        }

        filterChromaticModesForSampleRate (modes, sr);
        for (auto& mode : modes)
            mode.decayTime = decayTimeForMode (subEng, mode.frequency, mat);

        // Hammer force-impulse spectrum (M2 2a/2b). Beam/plate only — see the
        // matching comment in startNote() above; Custom Harmonics (subEng==2)
        // is user-authored additive synthesis and is left untouched. This is
        // the single source of truth also read by --dump-modes
        // (ModalResonator::getModes() returns baseAmp verbatim, per
        // ROADMAP_PHYSICS.md §2c). See HammerImpulse.h for derivation/sources.
        if (subEng == 0 || subEng == 1)
        {
            float tauC = HammerImpulse::tauCForStrike (params.exciterHardness, velocity);
            for (auto& m : modes)
            {
                float omega = juce::MathConstants<float>::twoPi * m.frequency;
                m.amplitude *= HammerImpulse::forceSpectrumMagnitude (omega, tauC);
            }
        }

        baseModes = modes;
        glidePhase = 0.0f;

        resonator.setSampleRate (sr);
        resonator.setModes (modes);
        resonator.excite (velocity);

        setupExciter (params.exciterHardness, velocity, 0.5f, 0.0f, sr);
        seedNoise (params.randomSeed, params.eventIndex, midiNote, velocity);

        bodyRes.prepare (sr);
        // DIAGNOSTIC-ONLY: --body-amount overrides the CLI default body mix
        // of 0.0f, i.e. the body-resonance layer is OFF in this standalone /
        // physics-verified path unless the flag is passed (the plugin's
        // Macro Body knob is a separate path via startNote()). See
        // DiagnosticOverrides.h. Sentinel < 0 -> unchanged 0.0f behavior.
        bodyRes.setAmount (DiagnosticOverrides::bodyAmountOverride >= 0.0f
                                ? DiagnosticOverrides::bodyAmountOverride
                                : 0.0f);
        configureCreativeBodyLayer (modes);
        bodyRes.reset();
        damped = false;
    }

    void noteOff()
    {
        if (! damped)
        {
            resonator.damp (0.08f);
            damped = true;
        }
    }

    bool isActive() const
    {
        return resonator.isActive() || exciterEnv.isActive();
    }

    float getNextSample()
    {
        float sample = 0.0f;
        if (resonator.isActive())
            sample += resonator.processSample();
        if (exciterEnv.isActive())
        {
            float noise = noiseGen.processSample();
            noise = exciterFilter.processSample (noise);
            sample += noise * exciterEnv.process();
        }
        sample += bodyRes.processSample (sample);
        return sample * outputGain;   // per-sub-engine, equal-RMS calibrated
    }

    void scaleFrequencies (double factor)
    {
        resonator.scaleFrequencies (factor);
    }

    /// Predicted modes (MIDI-tuned) — CLI --dump-modes.
    std::vector<ModalResonator::Mode> getModes() const { return resonator.getModes(); }

    /// |dry + BodyResonance(dry)| at freqHz for THIS voice's live body-filter
    /// state -- see CimbalomVoice::getBodyMagnitudeAt() / BodyResonance::
    /// magnitudeAt() for the full rationale (2026-07 --amps GATE fix).
    float getBodyMagnitudeAt (float freqHz) const { return bodyRes.magnitudeAt (freqHz); }

    void renderNextBlock (juce::AudioBuffer<float>& outputBuffer,
                          int startSample, int numSamples) override
    {
        bool anyActive = false;

        // Water gong pitch glide（持續降低模態頻率模擬浸水效果）
        // Advance scaled by block length → glide rate is independent of host buffer
        // size; 0.15/sec ⇒ glidePhase reaches the 0.5 cap (~15% drop) in ~3.3s.
        if (glideAmount > 0.01f && ! baseModes.empty())
        {
            double glideSr = getSampleRate();
            if (glideSr > 0.0)
                glidePhase += glideAmount * 0.15f * (float) ((double) numSamples / glideSr);
            if (glidePhase < 0.5f)
            {
                float glideMul = 1.0f - glidePhase * 0.3f;  // max 15% pitch drop
                // ModalResonator retains each base frequency, so scaling the
                // phase increments in place avoids a vector allocation/copy on
                // every audio block while preserving phase continuity.
                resonator.scaleFrequencies (glideMul);
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

            sample += bodyRes.processSample (sample);
            sample *= outputGain;   // per-sub-engine, equal-RMS calibrated

            for (int ch = 0; ch < outputBuffer.getNumChannels(); ++ch)
                outputBuffer.addSample (ch, startSample, sample);

            ++startSample;
        }

        if (! anyActive)
            clearCurrentNote();
    }

private:
    /// Per-sub-engine output gain — equal-RMS calibration (2026-06, re-anchored
    /// 2026-07 after the BodyResonance velocity-linearity fix removed a v^2
    /// envelope term that was inflating body-resonance level; values restore
    /// each sub-engine's pre-fix RMS at the vel=0.85 calibration reference
    /// per ROADMAP_PHYSICS.md §6 "跨引擎等 RMS").
    static float subEngineOutputGain (int subEngine)
    {
        switch (subEngine)
        {
            case 0:  return 0.196f;   // Tongue Drum (cantilever beam)
            case 1:  return 0.151f;   // Water Gong (Kirchhoff plate; shared by
                                       // clamped + free-edge, same code path)
            default: return 0.180f;   // Custom harmonics (no BodyResonance probe
                                       // exists for this path; left unchanged)
        }
    }

    static float decayTimeForMode (
        int subEngine, float frequency, const MaterialDB::Material& material)
    {
        return subEngine == 0
            ? BeamModel::decayTimeForFrequency (frequency, material)
            : PlateModel::decayTimeForFrequency (frequency, material);
    }

    void configureCreativeBodyLayer (
        const std::vector<ModalResonator::Mode>& modes)
    {
        if (modes.empty())
            return;

        const float first = juce::jlimit (40.0f, 4000.0f, modes[0].frequency);
        const float second = juce::jlimit (40.0f, 4000.0f,
            modes.size() > 1 ? modes[1].frequency : modes[0].frequency * 2.0f);
        bodyRes.setFrequencies (first, second);
        bodyRes.reset();
    }

    void seedNoise (uint64_t scoreSeed, uint64_t eventIndex,
                    int midiNote, float velocity)
    {
        const uint32_t velocityCode = (uint32_t) std::lround (
            juce::jlimit (0.0f, 1.0f, velocity) * 16777215.0f);
        const uint64_t streamEvent = (eventIndex << 8) ^ noiseIdentity;
        noiseGen.setSeed (NoiseGen::mixSeed (
            scoreSeed, streamEvent, (uint32_t) midiNote, velocityCode));
    }

    /// Custom harmonics mode: user-defined ratio/amplitude
    void buildCustomModes (
        int midiNote, const MaterialDB::Material& mat,
        std::vector<ModalResonator::Mode>& modes)
    {
        float fundamental = 440.0f * std::pow (2.0f, (float) (midiNote - 69) / 12.0f);

        static constexpr float defRatios[] = { 1.0f, 2.0f, 3.0f, 4.16f, 5.43f, 6.98f, 8.21f, 10.0f };
        static constexpr float defAmps[]   = { 1.0f, 0.7f, 0.5f, 0.35f, 0.25f, 0.18f, 0.12f, 0.08f };
        static constexpr int count = 8;

        modes.clear();
        modes.reserve (count);
        for (int i = 0; i < count; ++i)
        {
            float ratio = pRatio[i] ? pRatio[i]->load() : defRatios[i];
            float amp   = pAmp[i]   ? pAmp[i]->load()   : defAmps[i];

            if (amp < 0.01f) continue;

            float freq = fundamental * ratio;
            if (freq > 20000.0f) continue;

            float decay = PlateModel::decayTimeForFrequency (freq, mat);

            modes.push_back ({ freq, amp, decay });
        }
    }

    void setupExciter (float hardness, float velocity,
                       float brightMacro, float noiseMacro, double sr)
    {
        static constexpr float cutoffs[]   = { 500.0f, 1500.0f, 4000.0f, 10000.0f };
        static constexpr float durations[] = { 0.005f, 0.003f,  0.002f,  0.001f };
        int idx = juce::jlimit (0, 3, (int) hardness);

        float cutoff = cutoffs[idx] * (0.3f + brightMacro * 1.4f);
        cutoff = juce::jlimit (200.0f, 16000.0f, cutoff);

        exciterFilter.setSampleRate (sr);
        exciterFilter.setParams (BiquadFilter::Type::LowPass, cutoff, 0.707f);
        exciterFilter.reset();
        noiseGen.setType (NoiseGen::Type::White);
        noiseGen.reset();

        float amp = velocity * 0.2f * (1.0f + noiseMacro * 3.0f);
        // DIAGNOSTIC-ONLY: --no-exciter-noise skips the trigger entirely, so
        // exciterEnv.isActive() stays false for this voice's whole lifetime
        // (ExpDecay::level defaults to 0.0f) -- see DiagnosticOverrides.h.
        if (! DiagnosticOverrides::disableExciterNoise)
            exciterEnv.trigger (amp, durations[idx], sr);
    }

    MaterialDB*    materialDB = nullptr;
    double         standaloneSR = 0.0;
    ModalResonator resonator;
    std::vector<ModalResonator::Mode> modeScratch;
    bool           damped = false;
    uint64_t       noiseIdentity = 0;
    uint64_t       noiseEventCounter = 0;

    NoiseGen           noiseGen;
    BiquadFilter       exciterFilter;
    Envelope::ExpDecay exciterEnv;
    BodyResonance      bodyRes;

    // Pitch glide state (water gong)
    std::vector<ModalResonator::Mode> baseModes;
    float glideAmount = 0.0f;
    float outputGain  = 0.2f;   // per-sub-engine output level (equal-RMS calibrated)
    float glidePhase  = 0.0f;
};
