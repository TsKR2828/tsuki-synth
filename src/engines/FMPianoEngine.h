#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "../dsp/Envelope.h"
#include "../dsp/NoiseGen.h"
#include <cmath>

/**
 * FM Piano Engine — 2-operator FM synthesis
 *
 * output = sin(2*pi*fc*t + I(t) * sin(2*pi*fm*t + fb*lastMod))
 *
 * fc = carrier frequency (from MIDI note)
 * fm = fc * ratio  (modulator frequency)
 * I(t) = peak index * exp(-t/tau)  (brightness envelope)
 * fb = self-feedback (0 = pure sine mod, >0 = richer harmonics)
 *
 * Sound types control ADSR envelope shape:
 *   Piano / E.Piano / Vibraphone / Bell / Organ / Pad / Bass / Brass
 *
 * Velocity affects both amplitude and modulation index (brightness).
 * Higher notes have faster brightness decay (natural piano behavior).
 */

enum class FMPreset { Piano = 0, EPiano = 1, Vibraphone = 2, Bell = 3,
                      Organ = 4, Pad = 5, Bass = 6, Brass = 7 };

struct FMParams
{
    FMPreset preset    = FMPreset::Piano;
    float    ratio     = 2.0f;
    float    index     = 5.0f;
    float    brightness = 0.5f;
    float    feedback  = 0.0f;
    float    attackMs  = 10.0f;
    float    releaseMs = 300.0f;
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
    // Parameter pointers (set by Processor)
    std::atomic<float>* pType       = nullptr;  // 0~7 sound type (ADSR shape)
    std::atomic<float>* pRatio      = nullptr;  // mod/carrier ratio (0.5~16)
    std::atomic<float>* pIndex      = nullptr;  // peak modulation index (0~25)
    std::atomic<float>* pBrightness = nullptr;  // index decay speed (0=sustained, 1=fast)
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
        float freq = 440.0f * std::pow (2.0f, (float) (midiNoteNumber - 69) / 12.0f);

        // Read parameters
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

        // Phase increments
        carrierPhase   = 0.0;
        modulatorPhase = 0.0;
        carrierInc   = freq * juce::MathConstants<double>::twoPi / sr;
        modulatorInc = freq * (double) ratio * juce::MathConstants<double>::twoPi / sr;

        // Feedback amount (scale to safe range)
        feedbackAmount = juce::jlimit (0.0f, 0.7f, feedback * 0.7f);
        lastModOutput  = 0.0f;

        // Velocity-dependent gain and brightness
        gain = 0.2f * velocity;
        currentIndex = index * (0.3f + 0.7f * velocity);

        // Index envelope decay
        // Higher brightness = faster decay; higher notes also decay faster
        float noteScaling = 1.0f + (float) (midiNoteNumber - 60) * 0.015f;
        noteScaling = std::max (noteScaling, 0.3f);
        float decayTime = (1.0f - brightness * 0.95f) * 4.0f + 0.01f;
        decayTime /= noteScaling;
        indexDecayCoeff = (float) std::exp (-6.9078 / (decayTime * sr));

        // ADSR envelope: type presets control decay/sustain shape
        static constexpr float decays[]   = { 0.8f,  1.2f,  2.0f,  3.5f, 0.01f, 0.01f, 0.3f,  0.5f  };
        static constexpr float sustains[] = { 0.2f,  0.3f,  0.15f, 0.0f, 1.0f,  0.8f,  0.1f,  0.4f  };
        //                                    Piano  EPiano Vibra  Bell  Organ  Pad    Bass   Brass

        ampEnv.setSampleRate (sr);
        ampEnv.setAttack  (attackMs * 0.001f);
        ampEnv.setDecay   (decays[type]);
        ampEnv.setSustain (sustains[type]);
        ampEnv.setRelease (releaseMs * 0.001f);
        ampEnv.noteOn();

        // Noise gen for macro noise injection
        noiseGen.setType (NoiseGen::Type::White);
        noiseGen.reset();
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
        double sr = standaloneSR;
        float freq = 440.0f * std::pow (2.0f, (float) (midiNote - 69) / 12.0f);

        int   type       = juce::jlimit (0, 7, static_cast<int> (params.preset));
        float ratio      = params.ratio;
        float index      = params.index;
        float brightness = params.brightness;
        float feedback   = params.feedback;
        float attackMs   = params.attackMs;
        float releaseMs  = params.releaseMs;

        carrierPhase   = 0.0;
        modulatorPhase = 0.0;
        carrierInc   = freq * juce::MathConstants<double>::twoPi / sr;
        modulatorInc = freq * (double) ratio * juce::MathConstants<double>::twoPi / sr;

        feedbackAmount = juce::jlimit (0.0f, 0.7f, feedback * 0.7f);
        lastModOutput  = 0.0f;

        gain = 0.2f * velocity;
        currentIndex = index * (0.3f + 0.7f * velocity);

        float noteScaling = std::max (0.3f, 1.0f + (float) (midiNote - 60) * 0.015f);
        float decayTime = (1.0f - brightness * 0.95f) * 4.0f + 0.01f;
        decayTime /= noteScaling;
        indexDecayCoeff = (float) std::exp (-6.9078 / (decayTime * sr));

        static constexpr float decays[]   = { 0.8f,  1.2f,  2.0f,  3.5f, 0.01f, 0.01f, 0.3f,  0.5f  };
        static constexpr float sustains[] = { 0.2f,  0.3f,  0.15f, 0.0f, 1.0f,  0.8f,  0.1f,  0.4f  };

        ampEnv.setSampleRate (sr);
        ampEnv.setAttack  (attackMs * 0.001f);
        ampEnv.setDecay   (decays[type]);
        ampEnv.setSustain (sustains[type]);
        ampEnv.setRelease (releaseMs * 0.001f);
        ampEnv.noteOn();

        noiseMacroLevel = 0.0f;
        noiseGen.setType (NoiseGen::Type::White);
        noiseGen.reset();
    }

    void noteOff() { ampEnv.noteOff(); }

    bool isActive() const { return ampEnv.isActive(); }

    float getNextSample()
    {
        if (! ampEnv.isActive())
            return 0.0f;

        currentIndex *= indexDecayCoeff;

        float modInput = (float) modulatorPhase + feedbackAmount * lastModOutput;
        float modOutput = std::sin (modInput) * currentIndex;
        lastModOutput = modOutput;

        float carrier = std::sin ((float) carrierPhase + modOutput);
        float envVal = ampEnv.getNextSample();
        float sample = carrier * envVal * gain;

        carrierPhase   += carrierInc;
        modulatorPhase += modulatorInc;

        if (carrierPhase >= juce::MathConstants<double>::twoPi * 65536.0)
            carrierPhase -= juce::MathConstants<double>::twoPi * 65536.0;
        if (modulatorPhase >= juce::MathConstants<double>::twoPi * 65536.0)
            modulatorPhase -= juce::MathConstants<double>::twoPi * 65536.0;

        return sample;
    }

    void scaleFrequency (double factor)
    {
        double sr = standaloneSR > 0.0 ? standaloneSR : getSampleRate();
        double baseCarrier   = carrierInc   / (juce::MathConstants<double>::twoPi / sr);
        double baseModulator = modulatorInc / (juce::MathConstants<double>::twoPi / sr);
        carrierInc   = baseCarrier   * factor * juce::MathConstants<double>::twoPi / sr;
        modulatorInc = baseModulator * factor * juce::MathConstants<double>::twoPi / sr;
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
            // Index envelope: exponential brightness decay
            currentIndex *= indexDecayCoeff;

            // Modulator with self-feedback
            float modInput = (float) modulatorPhase + feedbackAmount * lastModOutput;
            float modOutput = std::sin (modInput) * currentIndex;
            lastModOutput = modOutput;

            // Carrier with phase modulation from modulator
            float carrier = std::sin ((float) carrierPhase + modOutput);

            // Apply amplitude envelope
            float envVal = ampEnv.getNextSample();
            float sample = carrier * envVal * gain;

            // Macro: Noise injection
            if (noiseMacroLevel > 0.001f)
                sample += noiseGen.processSample() * noiseMacroLevel * envVal * gain * 0.4f;

            // Phase accumulation
            carrierPhase   += carrierInc;
            modulatorPhase += modulatorInc;

            // Wrap phases to prevent floating point overflow
            if (carrierPhase >= juce::MathConstants<double>::twoPi * 65536.0)
                carrierPhase -= juce::MathConstants<double>::twoPi * 65536.0;
            if (modulatorPhase >= juce::MathConstants<double>::twoPi * 65536.0)
                modulatorPhase -= juce::MathConstants<double>::twoPi * 65536.0;

            for (int ch = 0; ch < outputBuffer.getNumChannels(); ++ch)
                outputBuffer.addSample (ch, startSample, sample);

            ++startSample;
        }

        if (! ampEnv.isActive())
            clearCurrentNote();
    }

private:
    double standaloneSR   = 0.0;

    // Oscillator state
    double carrierPhase   = 0.0;
    double modulatorPhase = 0.0;
    double carrierInc     = 0.0;
    double modulatorInc   = 0.0;

    // FM state
    float currentIndex    = 0.0f;
    float indexDecayCoeff = 1.0f;
    float feedbackAmount  = 0.0f;
    float lastModOutput   = 0.0f;
    float gain            = 0.0f;

    // Amplitude envelope
    Envelope ampEnv;

    // Noise (for macro noise injection)
    NoiseGen noiseGen;
    float noiseMacroLevel = 0.0f;
};

using FMVoice = FMPianoVoice;
