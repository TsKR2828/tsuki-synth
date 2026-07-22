#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "../dsp/ModalResonator.h"
#include "../dsp/NoiseGen.h"
#include "../dsp/BiquadFilter.h"
#include "../dsp/BodyResonance.h"
#include "../dsp/Envelope.h"
#include "../dsp/DiagnosticOverrides.h"
#include "../physics/StringModel.h"
#include "../physics/MaterialDB.h"
#include "../physics/HammerImpulse.h"
#include <array>

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
    bool   tuneToMidi       = true;  // false = tension/geometry determine absolute pitch
    uint64_t randomSeed     = 0x5453554B4953594Eull;
    uint64_t eventIndex     = 0;
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
    CimbalomVoice()
    {
        baseModesScratch.reserve (40);
        for (int i = 0; i < kMaxStringsPerCourse; ++i)
        {
            stringModesScratch[(size_t) i].reserve (40);
            strings[i].reserveModes (40);
        }
    }

    void setMaterialDB (MaterialDB* db) { materialDB = db; }
    void setNoiseIdentity (uint64_t identity) { noiseIdentity = identity; }

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
        const auto& keys = MaterialDB::getOrderedKeys();
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

        StringModel::calculateModes (sp, *mat, baseModesScratch);
        auto& baseModes = baseModesScratch;

        // ── spectralTilt: CREATIVE / HEURISTIC LAYER (not physics) ──────────
        // "Stiffer materials sustain more overtones" is a sound-design
        // intuition, NOT a derived result. Every constant here is an
        // empirical tuning value with no literature/derivation/measurement
        // source (repo Rule 4 traceability: NONE):
        //   7.5  -- log10(E) anchor ("softest" material, E = 10^7.5 Pa)
        //   4.0  -- log10(E) span mapped onto the 0..1 tilt range
        //   0.2  -- exponent scale per (partialN - 1) applied below
        //   2.0  -- materialBright = spectralTilt * 2.0 (exciter block below)
        // Impact: multiplies PHYSICAL modal amplitudes (StringModel mode
        // shapes) and therefore also flows into --dump-modes "amp"; it does
        // NOT touch modal frequencies or decay times. DO NOT change these
        // numbers casually -- they alter the rendered sound (Rule 10
        // before/after audio re-render applies). Whether this layer should
        // be removed / separated from the physical amplitude path is an open
        // question awaiting 月月's decision.
        float logE = std::log10 (mat->youngsModulus);
        float spectralTilt = juce::jlimit (0.1f, 1.0f, (logE - 7.5f) / 4.0f);

        if (! baseModes.empty())
        {
            float f1ref = baseModes[0].frequency;
            for (auto& m : baseModes)
            {
                float partialN = m.frequency / f1ref;
                m.amplitude *= std::pow (spectralTilt, (partialN - 1.0f) * 0.2f);
            }
        }

        // Macro: Tension → mode frequency, Material → sustain, Damping → decay
        float tScale = 0.85f + mTension * 0.30f;
        float matScale = 0.5f + mMaterial;
        float dmpScale = 1.0f + (0.5f - mDamping) * 1.4f;

        // Tune fundamental to the exact MIDI pitch. A stiff string's actual f1 is
        // target·√(1+B) (inharmonic sharpening), so divide it out. Modal ratios and
        // the multi-string detuning (applied per string below) are preserved.
        float tuneScale = 1.0f;
        if (! baseModes.empty() && std::isfinite (baseModes[0].frequency)
            && baseModes[0].frequency > 0.0f)
        {
            const float target = 440.0f
                * std::pow (2.0f, (float) (midiNoteNumber - 69) / 12.0f);
            tuneScale = target / baseModes[0].frequency;
        }

        for (auto& m : baseModes)
        {
            m.frequency *= tScale * tuneScale;
            m.decayTime = StringModel::decayTimeForFrequency (m.frequency, *mat)
                        * matScale * dmpScale;
        }

        const float tauC = HammerImpulse::tauCForStrike (hammer, velocity);

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

            auto& modes = stringModesScratch[(size_t) s];
            modes.assign (baseModes.begin(), baseModes.end());
            for (auto& m : modes)
            {
                m.frequency *= freqMul;
                m.decayTime = StringModel::decayTimeForFrequency (m.frequency, *mat)
                            * matScale * dmpScale;
                m.amplitude *= HammerImpulse::forceSpectrumMagnitude (
                    juce::MathConstants<float>::twoPi * m.frequency, tauC);
                m.amplitude *= gain;
            }

            strings[s].setSampleRate (getSampleRate());
            strings[s].setModes (modes);
            strings[s].excite (velocity);
        }

        // ── Exciter（槌頭噪音脈衝）──
        float materialBright = juce::jlimit (0.15f, 2.0f, spectralTilt * 2.0f);
        setupExciter (hammer, velocity, mBrightness, mNoise, materialBright, getSampleRate());
        seedNoise (0x504C5547494Eull, noiseEventCounter++, midiNoteNumber, velocity);
        configureCreativeBodyLayer (baseModes);
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
        // DIAGNOSTIC-ONLY (see DiagnosticOverrides.h): --num-strings lets
        // physics_verify.py isolate multi-string beating. Sentinel <= 0
        // means "no override" -> identical to the pre-existing behavior.
        int   nStringsRequested = (DiagnosticOverrides::numStringsOverride > 0)
                                     ? DiagnosticOverrides::numStringsOverride
                                     : params.numStrings;
        int   nStrings  = juce::jlimit (1, kMaxStringsPerCourse, nStringsRequested);
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

        StringModel::calculateModes (sp, mat, baseModesScratch);
        auto& baseModes = baseModesScratch;

        // ── spectralTilt: CREATIVE / HEURISTIC LAYER (not physics) ──────────
        // Same untraced empirical constants (7.5 / 4.0 / 0.2, plus the 2.0
        // in materialBright below) as startNote() -- see the full comment
        // block there. NOTE this is the CLI/ScoreRenderer path: the tilt is
        // multiplied into the physical modal amplitudes BEFORE
        // strings[s].setModes(), so it is baked into --dump-modes "amp"
        // values as well as the rendered audio. Frequencies and decay times
        // are unaffected. Values must not be changed without 月月's sign-off
        // (Rule 10); removal/separation of this layer is likewise 月月's
        // call.
        float logE = std::log10 (mat.youngsModulus);
        float spectralTilt = juce::jlimit (0.1f, 1.0f, (logE - 7.5f) / 4.0f);

        if (! baseModes.empty())
        {
            float f1ref = baseModes[0].frequency;
            for (auto& m : baseModes)
            {
                float partialN = m.frequency / f1ref;
                m.amplitude *= std::pow (spectralTilt, (partialN - 1.0f) * 0.2f);
            }
        }

        // Tune fundamental to the exact MIDI pitch (compensate stiff-string
        // inharmonic sharpening: actual f1 = target·√(1+B)). Ratios + detuning kept.
        if (params.tuneToMidi && ! baseModes.empty() && std::isfinite (baseModes[0].frequency)
            && baseModes[0].frequency > 0.0f)
        {
            const float target = 440.0f
                * std::pow (2.0f, (float) (midiNote - 69) / 12.0f);
            const float tuneScale = target / baseModes[0].frequency;
            for (auto& m : baseModes)
                m.frequency *= tuneScale;
        }

        const float tauC = HammerImpulse::tauCForStrike ((float) hammerIdx, velocity);
        // dampingOverride semantics: >= 0 replaces ONLY the material's
        // frequency-independent alpha term in the decay law
        //   tau(f) = 1 / (alpha + beta_air*f^2 + gamma_radiation*f);
        // the beta_air*f^2 and gamma_radiation*f terms always stay
        // material-driven (see StringModel::decayTimeForFrequency). It is
        // NOT a scale factor on the whole damping. Sentinel -1 = no
        // override (pure material damping).
        const float alphaOverride = params.dampingOverride >= 0.0
            ? (float) params.dampingOverride : -1.0f;

        numActiveStrings = nStrings;
        float gain = 1.0f / std::sqrt ((float) numActiveStrings);

        for (int s = 0; s < numActiveStrings; ++s)
        {
            float centOffset = 0.0f;
            if (numActiveStrings > 1)
                centOffset = detCents
                    * (2.0f * (float) s / (float) (numActiveStrings - 1) - 1.0f);

            float freqMul = std::pow (2.0f, centOffset / 1200.0f);

            auto& modes = stringModesScratch[(size_t) s];
            modes.assign (baseModes.begin(), baseModes.end());
            for (auto& m : modes)
            {
                m.frequency *= freqMul;
                m.decayTime = StringModel::decayTimeForFrequency (
                    m.frequency, mat, alphaOverride);
                m.amplitude *= HammerImpulse::forceSpectrumMagnitude (
                    juce::MathConstants<float>::twoPi * m.frequency, tauC);
                m.amplitude *= gain;
            }

            strings[s].setSampleRate (sr);
            strings[s].setModes (modes);
            strings[s].excite (velocity);
        }

        float materialBright = juce::jlimit (0.15f, 2.0f, spectralTilt * 2.0f);
        setupExciter (static_cast<float> (hammerIdx), velocity,
                      0.5f, 0.0f, materialBright, sr);
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
        configureCreativeBodyLayer (baseModes);
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
        return sample * 0.069f;   // equal-RMS re-calibrated (2026-07): the
                                   // BodyResonance velocity-linearity fix removed
                                   // a v^2 envelope term that was inflating body-
                                   // resonance level. RMS-only re-anchoring to the
                                   // pre-fix vel=0.85 reference would put peak at
                                   // 0.0 dBFS (violates verify_score.py's
                                   // PEAK_LIMIT_DBFS = -0.3), so this value instead
                                   // restores the pre-fix peak headroom (-2.0 dBFS
                                   // @ vel=0.85) — closest achievable equal-RMS
                                   // anchor without breaching the peak ceiling.
    }

    void scaleFrequencies (double factor)
    {
        for (int s = 0; s < numActiveStrings; ++s)
            strings[s].scaleFrequencies (factor);
    }

    /// Predicted modes of the course (representative string 0) — CLI --dump-modes.
    std::vector<ModalResonator::Mode> getModes() const
    {
        return numActiveStrings > 0 ? strings[0].getModes()
                                    : std::vector<ModalResonator::Mode>{};
    }

    /// 2026-07 (--amps GATE fix): predicted modes of EVERY active string in
    /// the course (already detuned + gain-scaled exactly as noteOn() set
    /// them up, i.e. the real per-string frequency/amplitude the renderer
    /// sums at getNextSample() time) -- not just string 0. Needed so
    /// --dump-modes' theory can reconstruct the true multi-string beating
    /// pattern (ROADMAP_PHYSICS.md M2-2d root-cause Experiment 4/5) instead
    /// of reporting a single undetuned string as if it were the whole course.
    std::vector<std::vector<ModalResonator::Mode>> getAllStringModes() const
    {
        std::vector<std::vector<ModalResonator::Mode>> out;
        for (int s = 0; s < numActiveStrings; ++s)
            out.push_back (strings[s].getModes());
        return out;
    }

    /// |dry + BodyResonance(dry)| at freqHz for THIS voice's live body-filter
    /// state (amount/frequencies as set in noteOn()) -- see BodyResonance::
    /// magnitudeAt(). Single source of truth for --dump-modes' body-filter
    /// column; not a re-derivation, reads the same bodyRes the renderer uses.
    float getBodyMagnitudeAt (float freqHz) const { return bodyRes.magnitudeAt (freqHz); }

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
            sample *= 0.069f;   // equal-RMS re-calibrated (2026-07, see getNextSample())

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
        // DIAGNOSTIC-ONLY: --no-exciter-noise skips the trigger entirely, so
        // exciterEnv.isActive() stays false for this voice's whole lifetime
        // (ExpDecay::level defaults to 0.0f) -- see DiagnosticOverrides.h.
        if (! DiagnosticOverrides::disableExciterNoise)
            exciterEnv.trigger (amp, durations[idx] * durScale, sr);
    }

    MaterialDB*    materialDB = nullptr;
    double         standaloneSR = 0.0;
    ModalResonator strings[kMaxStringsPerCourse];
    std::vector<ModalResonator::Mode> baseModesScratch;
    std::array<std::vector<ModalResonator::Mode>, kMaxStringsPerCourse> stringModesScratch;
    int            numActiveStrings = 1;
    bool           damped = false;
    uint64_t       noiseIdentity = 0;
    uint64_t       noiseEventCounter = 0;

    NoiseGen           noiseGen;
    BiquadFilter       exciterFilter;
    Envelope::ExpDecay exciterEnv;
    BodyResonance      bodyRes;
};
