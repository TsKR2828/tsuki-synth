#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "../dsp/Envelope.h"
#include "../dsp/NoiseGen.h"
#include <cmath>

/**
 * FM Piano Engine — 2-operator FM with hammer transient + body resonance
 *
 * NOTE: this is FM SYNTHESIS, not physical modelling. Unlike the Cimbalom /
 * Chromatic engines (string / beam / plate physics), FM Piano is a "sounds-like"
 * engine — its spectrum is exact and verifiable (a harmonic series for integer
 * ratios) but it is NOT derived from an instrument's physics. For the
 * physics-accurate goal, treat it as a synth voice, not a physical model.
 *
 * Signal chain (per sample):
 *   1. FM core:  sin(2π·fc·t + I(t) · sin(2π·fm·t + fb·lastMod))
 *   2. Hammer noise: bandpass (1.5–6 kHz) noise burst, 15–45 ms
 *   3. Body resonance: 2 soundboard modes (per-type frequencies)
 *
 * I(t) is a TWO-STAGE envelope (separates attack brightness from body damping):
 *   attackIndex: high peak, fast exponential decay (~45 ms) — transient "hammer" brightness
 *   bodyIndex:   moderate floor, slow decay (brightness param) — sustained tone color
 *   effectiveIndex = attackIndex + bodyIndex
 *
 * E.Piano 3-stack mode (P2):
 *   When type == E.Piano, three parallel FM stacks run alongside the main path:
 *     Stack A (Body):      ratio 1:1,  index 2.2, decay 650ms — piano body
 *     Stack B (Tine/Bell): ratio 14:1, index 4.5, decay 80ms  — bright attack transient
 *     Stack C (Shimmer):   ratio 3:1,  index 1.4, decay 900ms, +4 cents — glass tail
 *   Output = 60% stacks + 40% original single-stack, for richer DX7-inspired timbre.
 *
 * Sound types control ADSR shape + hammer/body amounts:
 *   Piano / E.Piano / Vibraphone / Bell / Organ / Pad / Bass / Brass
 */

enum class FMPreset { Piano = 0, EPiano = 1, Vibraphone = 2, Bell = 3,
                      Organ = 4, Pad = 5, Bass = 6, Brass = 7 };

struct FMParams
{
    FMPreset preset    = FMPreset::Piano;
    float    ratio     = 1.0f;       // must match APVTS default
    float    index     = 4.5f;       // must match APVTS default
    float    brightness = 0.6f;      // must match APVTS default
    float    feedback  = 0.02f;      // must match APVTS default
    float    attackMs  = 5.0f;       // must match APVTS default
    float    releaseMs = 500.0f;     // must match APVTS default
    uint64_t randomSeed = 0x5453554B4953594Eull;
    uint64_t eventIndex = 0;
};

class FMPianoSound : public juce::SynthesiserSound
{
public:
    bool appliesToNote (int) override    { return true; }
    bool appliesToChannel (int) override { return true; }
};

class FMPianoVoice : public juce::SynthesiserVoice
{
public:
    void setNoiseIdentity (uint64_t identity) { noiseIdentity = identity; }
    // Parameter pointers (set by Processor)
    std::atomic<float>* pType       = nullptr;  // 0~7 sound type (ADSR shape)
    std::atomic<float>* pRatio      = nullptr;  // mod/carrier ratio (0.5~16)
    std::atomic<float>* pIndex      = nullptr;  // peak modulation index (0~25)
    std::atomic<float>* pBrightness = nullptr;  // body index decay speed (0=sustained, 1=fast)
    std::atomic<float>* pFeedback   = nullptr;  // modulator self-feedback (0~1)
    std::atomic<float>* pAttack     = nullptr;  // ADSR attack (ms)
    std::atomic<float>* pRelease    = nullptr;  // ADSR release (ms)

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
        return dynamic_cast<FMPianoSound*> (s) != nullptr;
    }

    void startNote (int midiNoteNumber, float velocity,
                    juce::SynthesiserSound*, int) override
    {
        double sr = getSampleRate();

        int   type       = juce::jlimit (0, 7, (int) pType->load());
        float ratio      = pRatio->load();
        float index      = pIndex->load();
        float brightness = pBrightness->load();
        float feedback   = pFeedback->load();
        float attackMs   = pAttack->load();
        float releaseMs  = pRelease->load();

        // ── 讀取 Macro ──
        float mMaterial   = pMacroMaterial   ? pMacroMaterial->load()   : 0.5f;
        float mTension    = pMacroTension    ? pMacroTension->load()    : 0.5f;
        float mDamping    = pMacroDamping    ? pMacroDamping->load()    : 0.5f;
        float mStrike     = pMacroStrike     ? pMacroStrike->load()     : 0.5f;
        float mBrightness = pMacroBrightness ? pMacroBrightness->load() : 0.5f;
        float mBody       = pMacroBody       ? pMacroBody->load()       : 0.5f;
        noiseMacroLevel   = pMacroNoise      ? pMacroNoise->load()      : 0.0f;

        // Macro: Tension → ratio scale (0→×0.85, 0.5→×1.0, 1→×1.15)
        ratio *= (0.85f + mTension * 0.30f);

        // Macro: Material → slight ratio detune for metallic character
        ratio *= (0.95f + mMaterial * 0.10f);

        // Macro: Brightness → index scale (0→×0.3, 0.5→×1.0, 1→×1.7)
        index *= (0.3f + mBrightness * 1.4f);

        // Macro: Body → feedback scale (0→×0.4, 0.5→×1.0, 1→×1.6)
        feedback *= (0.4f + mBody * 1.2f);

        // Macro: Strike → attack time (0→faster, 0.5→neutral, 1→slower)
        attackMs *= (0.5f + mStrike);

        // Macro: Damping → release time (0→long, 0.5→neutral, 1→short)
        float dmpScale = 1.0f + (0.5f - mDamping) * 1.4f;
        releaseMs *= dmpScale;

        initVoice (midiNoteNumber, velocity, type, ratio, index,
                   brightness, feedback, attackMs, releaseMs, sr,
                   0x504C5547494Eull, noiseEventCounter++);
    }

    void stopNote (float, bool allowTailOff) override
    {
        if (allowTailOff)
        {
            ampEnv.noteOff();
        }
        else
        {
            // Force quick release to avoid click on voice stealing
            ampEnv.setRelease (0.005f);
            ampEnv.noteOff();
            clearCurrentNote();
        }
    }

    void pitchWheelMoved (int) override {}
    void controllerMoved (int, int) override {}

    // ── Standalone API (CLI / ScoreRenderer) ──

    void prepare (double sr) { standaloneSR = sr; }

    void noteOn (int midiNote, float velocity, const FMParams& params)
    {
        noiseMacroLevel = 0.0f;
        initVoice (midiNote, velocity,
                   juce::jlimit (0, 7, static_cast<int> (params.preset)),
                   params.ratio, params.index, params.brightness,
                   params.feedback, params.attackMs, params.releaseMs,
                   standaloneSR, params.randomSeed, params.eventIndex);
    }

    void noteOff() { ampEnv.noteOff(); }

    bool isActive() const { return ampEnv.isActive(); }

    float getNextSample()
    {
        if (! ampEnv.isActive())
            return 0.0f;

        return processSingleSample();
    }

    /** Scale frequency by an absolute ratio from the note-on pitch (not cumulative). */
    void scaleFrequency (double factor)
    {
        carrierInc   = originalCarrierInc   * factor;
        modulatorInc = originalModulatorInc * factor;

        // Also scale multi-stack oscillators (E.Piano 3-stack)
        if (useMultiStack)
        {
            for (int s = 0; s < kNumStacks; ++s)
            {
                stacks[s].carrierInc   = stacks[s].origCarrierInc   * factor;
                stacks[s].modulatorInc = stacks[s].origModulatorInc * factor;
            }
        }
    }

    void renderNextBlock (juce::AudioBuffer<float>& outputBuffer,
                          int startSample, int numSamples) override
    {
        if (! ampEnv.isActive())
        {
            clearCurrentNote();
            return;
        }

        while (--numSamples >= 0)
        {
            float sample = processSingleSample();

            for (int ch = 0; ch < outputBuffer.getNumChannels(); ++ch)
                outputBuffer.addSample (ch, startSample, sample);

            ++startSample;
        }

        if (! ampEnv.isActive())
            clearCurrentNote();
    }

private:
    double standaloneSR = 0.0;

    // ── FM oscillator ──
    double carrierPhase   = 0.0;
    double modulatorPhase = 0.0;
    double carrierInc     = 0.0;
    double modulatorInc   = 0.0;
    double originalCarrierInc   = 0.0;  // stored at noteOn for non-cumulative glide
    double originalModulatorInc = 0.0;
    float  feedbackAmount = 0.0f;
    float  lastModOutput  = 0.0f;
    float  gain           = 0.0f;

    // ── Two-stage modulation index ──
    float attackIndex      = 0.0f;   // transient brightness — fast decay
    float bodyIndex        = 0.0f;   // sustained tone color — slow decay
    float attackDecayCoeff = 1.0f;
    float bodyDecayCoeff   = 1.0f;

    // ── Hammer noise transient ──
    float    hammerLevel      = 0.0f;
    float    hammerDecayCoeff = 1.0f;
    float    hammerHPState    = 0.0f;   // one-pole HP filter state
    float    hammerHPCoeff    = 0.0f;
    float    hammerLPState    = 0.0f;   // one-pole LP filter state
    float    hammerLPCoeff    = 0.0f;
    NoiseGen hammerNoiseGen;             // independent, specified PCG32 stream

    // ── Body resonance (2 soundboard modes) ──
    double bodyResPhase1   = 0.0;
    double bodyResPhase2   = 0.0;
    double bodyResInc1     = 0.0;
    double bodyResInc2     = 0.0;
    float  bodyResAmp1     = 0.0f;
    float  bodyResAmp2     = 0.0f;
    float  bodyResDecay1   = 1.0f;
    float  bodyResDecay2   = 1.0f;

    // ── E.Piano 3-stack mode (P2) ──
    // Parallel FM operators: body(1:1), tine/bell(14:1), shimmer(3:1 +4¢)
    // Only active when type == 1 (E.Piano); other types use single-stack path.
    static constexpr int kNumStacks = 3;
    bool useMultiStack = false;

    struct FMStack
    {
        double carrierPhase   = 0.0;
        double modulatorPhase = 0.0;
        double carrierInc     = 0.0;
        double modulatorInc   = 0.0;
        double origCarrierInc = 0.0;   // for non-cumulative glide
        double origModulatorInc = 0.0;
        float  index          = 0.0f;
        float  decayCoeff     = 1.0f;
        float  feedbackAmt    = 0.0f;
        float  lastModOut     = 0.0f;
        float  level          = 0.0f;  // mix level relative to main output
    };
    FMStack stacks[kNumStacks];

    // ── Amplitude envelope + macro noise ──
    Envelope ampEnv;
    NoiseGen noiseGen;
    float    noiseMacroLevel = 0.0f;
    uint64_t noiseIdentity = 0;
    uint64_t noiseEventCounter = 0;

    // ──────────────────────────────────────────────────────────
    //  initVoice — shared setup for DAW (startNote) & CLI (noteOn)
    // ──────────────────────────────────────────────────────────
    void initVoice (int midiNote, float velocity, int type,
                    float ratio, float index, float brightness,
                    float feedback, float attackMs, float releaseMs,
                    double sr, uint64_t scoreSeed, uint64_t eventIndex)
    {
        float freq = 440.0f * std::pow (2.0f, (float) (midiNote - 69) / 12.0f);

        // ── FM oscillator ──
        carrierPhase   = 0.0;
        modulatorPhase = 0.0;
        carrierInc   = freq * juce::MathConstants<double>::twoPi / sr;
        modulatorInc = freq * (double) ratio * juce::MathConstants<double>::twoPi / sr;
        originalCarrierInc   = carrierInc;
        originalModulatorInc = modulatorInc;

        feedbackAmount = juce::jlimit (0.0f, 0.7f, feedback * 0.7f);
        lastModOutput  = 0.0f;
        gain = 0.100f * velocity;   // equal-RMS calibrated (2026-06)

        // ── Two-stage modulation index ──
        // Split peakIndex into fast-attack + slow-body with separate scale factors:
        //   effectiveIndex(t) = attackIndex·exp(-t/τ_fast) + bodyIndex·exp(-t/τ_slow)
        //
        // P1-1: velocity-to-index — velocity shapes timbre, not just volume
        //   soft: rounder, less hammer noise / hard: brighter, more transient
        float velIndexScale  = 0.45f + 0.80f * velocity;  // vel 0→0.45, 0.5→0.85, 1.0→1.25
        float velAttackBoost = 0.50f + 1.10f * velocity;  // attack index extra push at high vel
        float velHammerScale = 0.20f + 1.20f * velocity;  // hammer noise velocity sensitivity
        float peakIndex = index * velIndexScale;

        // ── Key scaling: reduce index for upper register ──
        // Real piano upper strings are short → fewer partials → nearly pure tone
        // C4(60)=1.0x, C5(72)=0.91x, C6(84)=0.77x, C7(96)=0.62x, C8(108)=0.48x
        float noteIndexScale = juce::jlimit (0.45f, 1.0f,
            1.2f - (float) (midiNote - 48) * 0.012f);
        peakIndex *= noteIndexScale;

        // P1-2: per-type attack/body scale factors (not ratio — can sum ≠ 1.0)
        //   attackScale > 1 = louder transient; bodyScale < 1 = thinner sustain
        //                                          Piano  EPiano Vibra  Bell   Organ  Pad    Bass   Brass
        static constexpr float atkScales[] =  { 1.20f, 1.60f, 0.80f, 1.40f, 0.20f, 0.40f, 1.10f, 0.90f };
        static constexpr float bdyScales[] =  { 0.55f, 0.45f, 0.70f, 0.80f, 0.80f, 0.70f, 0.80f, 0.65f };

        attackIndex = peakIndex * atkScales[type] * velAttackBoost;
        bodyIndex   = peakIndex * bdyScales[type];

        float noteScaling = std::max (0.3f, 1.0f + (float) (midiNote - 60) * 0.025f);

        // Attack decay: ~45 ms at C4, faster for higher notes
        float attackTimeSec = 0.045f / noteScaling;
        attackDecayCoeff = (float) std::exp (-6.9078 / (attackTimeSec * sr));

        // Body decay: controlled by tone decay param (higher = faster)
        float bodyTimeSec = (1.0f - brightness * 0.95f) * 4.0f + 0.1f;
        bodyTimeSec /= noteScaling;
        bodyDecayCoeff = (float) std::exp (-6.9078 / (bodyTimeSec * sr));

        // ── Hammer noise transient ──
        // Bandpass-filtered (1.5–6 kHz) noise burst for physical strike character
        // P1-1: velHammerScale gives soft hits less noise, hard hits more bite
        //                                         Piano  EPiano Vibra  Bell   Organ  Pad    Bass   Brass
        static constexpr float hammerAmts[]  = { 0.35f, 0.25f, 0.10f, 0.05f, 0.00f, 0.00f, 0.15f, 0.10f };

        hammerLevel = hammerAmts[type] * velHammerScale;
        float hammerTimeSec = 0.015f + 0.030f * (1.0f - velocity);  // 15-45 ms
        hammerDecayCoeff = (float) std::exp (-6.9078 / (hammerTimeSec * sr));

        // One-pole HP ~1.5 kHz + LP ~6 kHz → bandpass for strike "click" contour
        hammerHPCoeff = 1.0f - (float) std::exp (-juce::MathConstants<double>::twoPi * 1500.0 / sr);
        hammerLPCoeff = (float) std::exp (-juce::MathConstants<double>::twoPi * 6000.0 / sr);
        hammerHPState = 0.0f;
        hammerLPState = 0.0f;
        const uint32_t velocityCode = (uint32_t) std::lround (
            juce::jlimit (0.0f, 1.0f, velocity) * 16777215.0f);
        const uint64_t streamEvent = (eventIndex << 8) ^ noiseIdentity;
        const uint64_t eventSeed = NoiseGen::mixSeed (
            scoreSeed, streamEvent, (uint32_t) midiNote, velocityCode);
        hammerNoiseGen.setType (NoiseGen::Type::White);
        hammerNoiseGen.reset();
        hammerNoiseGen.setSeed (eventSeed ^ 0x48414D4D4552ull);

        // ── P1-3: Per-type body resonance ──
        // Each sound type has different resonance character to reduce "same box" feel
        //                                         Piano  EPiano Vibra  Bell   Organ  Pad    Bass   Brass
        static constexpr float bodyResAmts[] = { 0.18f, 0.10f, 0.05f, 0.02f, 0.00f, 0.02f, 0.22f, 0.03f };
        static constexpr float bodyF1[]      = {180.0f,220.0f,200.0f,  0.0f,  0.0f,120.0f, 90.0f,  0.0f };
        static constexpr float bodyF2[]      = {340.0f,440.0f,400.0f,  0.0f,  0.0f,250.0f,180.0f,  0.0f };
        static constexpr float bodyD1[]      = {  2.0f,  1.2f,  1.5f,  1.0f,  1.0f,  2.5f,  2.0f,  1.0f }; // decay sec
        static constexpr float bodyD2[]      = {  1.5f,  0.8f,  1.0f,  1.0f,  1.0f,  2.0f,  1.5f,  1.0f };

        float bodyAmt = bodyResAmts[type] * (0.6f + 0.4f * velocity);
        float noteBodyScale = juce::jlimit (0.2f, 1.0f,
            1.0f - std::max (0.0f, (float) (midiNote - 72)) * 0.02f);

        bodyResPhase1 = 0.0;
        bodyResInc1   = (double) bodyF1[type] * juce::MathConstants<double>::twoPi / sr;
        bodyResAmp1   = (bodyF1[type] > 0.0f) ? bodyAmt * 0.6f * noteBodyScale : 0.0f;
        bodyResDecay1 = (float) std::exp (-6.9078 / ((double) bodyD1[type] * sr));

        bodyResPhase2 = 0.0;
        bodyResInc2   = (double) bodyF2[type] * juce::MathConstants<double>::twoPi / sr;
        bodyResAmp2   = (bodyF2[type] > 0.0f) ? bodyAmt * 0.4f * noteBodyScale : 0.0f;
        bodyResDecay2 = (float) std::exp (-6.9078 / ((double) bodyD2[type] * sr));

        // ── ADSR envelope ──
        static constexpr float decays[]   = { 3.5f,  1.2f,  2.0f,  3.5f, 0.01f, 0.01f, 0.3f,  0.5f  };
        static constexpr float sustains[] = { 0.0f,  0.3f,  0.15f, 0.0f, 1.0f,  0.8f,  0.1f,  0.4f  };
        //                                    Piano  EPiano Vibra  Bell  Organ  Pad    Bass   Brass

        ampEnv.setSampleRate (sr);
        ampEnv.setAttack  (attackMs * 0.001f);
        ampEnv.setDecay   (decays[type]);
        ampEnv.setSustain (sustains[type]);
        ampEnv.setRelease (releaseMs * 0.001f);
        ampEnv.noteOn();

        noiseGen.setType (NoiseGen::Type::White);
        noiseGen.reset();
        noiseGen.setSeed (eventSeed ^ 0x4D4143524F4Eull);

        // ── P2: E.Piano 3-stack mode ──
        // Only E.Piano (type 1) uses parallel stacks; all others single-stack.
        useMultiStack = (type == 1);
        if (useMultiStack)
        {
            // Stack definitions: { ratio, peakIndex, level, decayMs, feedback, detuneCents }
            struct StackDef { float r; float idx; float lvl; float decMs; float fb; float detCents; };
            static constexpr StackDef defs[kNumStacks] = {
                { 1.0f,  2.2f, 0.75f, 650.0f, 0.02f,  0.0f },   // A: Body
                { 14.0f, 4.5f, 0.30f,  80.0f, 0.00f,  0.0f },   // B: Tine / Bell attack
                { 3.0f,  1.4f, 0.18f, 900.0f, 0.00f,  4.0f },   // C: Shimmer (+4 cents)
            };

            for (int s = 0; s < kNumStacks; ++s)
            {
                auto& st  = stacks[s];
                auto& def = defs[s];

                // Detune in cents → frequency multiplier
                float detuneMul = (def.detCents != 0.0f)
                    ? std::pow (2.0f, def.detCents / 1200.0f)
                    : 1.0f;

                double stackCarrierFreq = (double) freq * (double) detuneMul;

                st.carrierPhase   = 0.0;
                st.modulatorPhase = 0.0;
                st.carrierInc     = stackCarrierFreq * juce::MathConstants<double>::twoPi / sr;
                st.modulatorInc   = stackCarrierFreq * (double) def.r
                                    * juce::MathConstants<double>::twoPi / sr;
                st.origCarrierInc   = st.carrierInc;
                st.origModulatorInc = st.modulatorInc;

                // Index scaled by velocity (same velIndexScale as main path)
                st.index     = def.idx * velIndexScale;
                st.decayCoeff = (float) std::exp (-6.9078 / ((double) def.decMs * 0.001 * sr));
                st.feedbackAmt = juce::jlimit (0.0f, 0.7f, def.fb * 0.7f);
                st.lastModOut  = 0.0f;
                st.level       = def.lvl;
            }
        }
    }

    // ──────────────────────────────────────────────────────────
    //  processSingleSample — shared DSP for renderNextBlock & getNextSample
    // ──────────────────────────────────────────────────────────
    float processSingleSample()
    {
        // ── Two-stage modulation index ──
        float effectiveIndex = attackIndex + bodyIndex;
        attackIndex *= attackDecayCoeff;
        bodyIndex   *= bodyDecayCoeff;

        float envVal = ampEnv.getNextSample();
        float sample;

        if (useMultiStack)
        {
            // ── P2: E.Piano 3-stack parallel FM ──
            // Each stack is an independent 2-op FM: sin(carrier + I·sin(mod + fb·prev))
            // Summed with per-stack level weights, sharing the same amplitude envelope.
            float stackSum = 0.0f;

            for (int s = 0; s < kNumStacks; ++s)
            {
                auto& st = stacks[s];

                float modIn  = (float) st.modulatorPhase + st.feedbackAmt * st.lastModOut;
                float modOut = std::sin (modIn) * st.index;
                st.lastModOut = modOut;

                float car = std::sin ((float) st.carrierPhase + modOut);
                stackSum += car * st.level;

                st.index *= st.decayCoeff;

                st.carrierPhase   += st.carrierInc;
                st.modulatorPhase += st.modulatorInc;
                while (st.carrierPhase >= juce::MathConstants<double>::twoPi)
                    st.carrierPhase -= juce::MathConstants<double>::twoPi;
                while (st.modulatorPhase >= juce::MathConstants<double>::twoPi)
                    st.modulatorPhase -= juce::MathConstants<double>::twoPi;
            }

            // Also add the main single-stack FM (preserves existing E.Piano character
            // as a 4th layer, blended at reduced level for backward compatibility)
            float modInput  = (float) modulatorPhase + feedbackAmount * lastModOutput;
            float modOutput = std::sin (modInput) * effectiveIndex;
            lastModOutput   = modOutput;
            float mainCarrier = std::sin ((float) carrierPhase + modOutput);

            // Blend: 60% multi-stack + 40% original single-stack
            sample = (stackSum * 0.60f + mainCarrier * 0.40f) * envVal * gain;
        }
        else
        {
            // ── Original single-stack FM path (all types except E.Piano) ──
            float modInput  = (float) modulatorPhase + feedbackAmount * lastModOutput;
            float modOutput = std::sin (modInput) * effectiveIndex;
            lastModOutput   = modOutput;

            float carrier = std::sin ((float) carrierPhase + modOutput);
            sample = carrier * envVal * gain;
        }

        // ── Hammer noise transient (bandpass 1.5–6 kHz) ──
        if (hammerLevel > 0.0001f)
        {
            float noise = hammerNoiseGen.processSample();

            // HP ~1.5 kHz (one-pole)
            hammerHPState += hammerHPCoeff * (noise - hammerHPState);
            float hp = noise - hammerHPState;
            // LP ~6 kHz (one-pole)
            hammerLPState = hammerLPCoeff * hammerLPState + (1.0f - hammerLPCoeff) * hp;

            sample += hammerLPState * hammerLevel * gain;
            hammerLevel *= hammerDecayCoeff;
        }

        // ── Body resonance (soundboard modes at 180 Hz + 340 Hz) ──
        if (bodyResAmp1 > 0.0001f || bodyResAmp2 > 0.0001f)
        {
            float body = std::sin ((float) bodyResPhase1) * bodyResAmp1
                       + std::sin ((float) bodyResPhase2) * bodyResAmp2;
            sample += body * envVal * gain;

            bodyResAmp1 *= bodyResDecay1;
            bodyResAmp2 *= bodyResDecay2;
            bodyResPhase1 += bodyResInc1;
            bodyResPhase2 += bodyResInc2;
            if (bodyResPhase1 >= juce::MathConstants<double>::twoPi)
                bodyResPhase1 -= juce::MathConstants<double>::twoPi;
            if (bodyResPhase2 >= juce::MathConstants<double>::twoPi)
                bodyResPhase2 -= juce::MathConstants<double>::twoPi;
        }

        // ── Macro noise injection ──
        if (noiseMacroLevel > 0.001f)
            sample += noiseGen.processSample() * noiseMacroLevel * envVal * gain * 0.4f;

        // ── Phase accumulation ──
        carrierPhase   += carrierInc;
        modulatorPhase += modulatorInc;

        while (carrierPhase >= juce::MathConstants<double>::twoPi)
            carrierPhase -= juce::MathConstants<double>::twoPi;
        while (modulatorPhase >= juce::MathConstants<double>::twoPi)
            modulatorPhase -= juce::MathConstants<double>::twoPi;

        return sample;
    }
};

using FMVoice = FMPianoVoice;
