#pragma once

#include "../dsp/ModalResonator.h"
#include "../dsp/NoiseGen.h"
#include "../dsp/BiquadFilter.h"
#include "../dsp/Envelope.h"
#include "../physics/MaterialDB.h"
#include "../physics/StringModel.h"
#include <juce_core/juce_core.h>
#include <array>

enum class ExciterType { Felt, Cotton, Wood, Metal };

struct CimbalomParams
{
    std::string materialKey  = "steel";
    double stringDiameter    = 0.8e-3;  // meters
    double stringLength      = 0.35;    // meters
    double strikePosition    = 0.3;     // 0~1 ratio
    ExciterType exciter      = ExciterType::Wood;
    int    stringsPerCourse  = 3;       // 1~5
    double detuneAmount      = 3.0;     // cents
    double sympatheticAmount = 0.3;     // 0~1
    double soundboardAmount  = 0.3;     // 0~1
    int    numModes          = 40;
};

class CimbalomVoice
{
public:
    void prepare (double sampleRate)
    {
        sr = sampleRate;
        for (auto& r : stringResonators)
            r.prepare (sampleRate);
        soundboardResonator.prepare (sampleRate);
        exciterEnvelope.prepare (sampleRate);
        exciterNoise.setType (NoiseType::White);
        exciterFilter.prepare (sampleRate);
    }

    void noteOn (int midiNote, float velocity, const Material& mat,
                 const CimbalomParams& params)
    {
        currentVelocity = velocity;
        active = true;

        double targetFreq = juce::MidiMessage::getMidiNoteInHertz (midiNote);

        double radius = params.stringDiameter * 0.5;
        double mu = mat.density * juce::MathConstants<double>::pi * radius * radius;
        double tension = mu * std::pow (2.0 * params.stringLength * targetFreq, 2.0);

        StringParams sp;
        sp.stringLength   = params.stringLength;
        sp.stringDiameter = params.stringDiameter;
        sp.tension        = tension;
        sp.strikePosition = params.strikePosition;
        sp.numModes       = params.numModes;

        numStrings = juce::jlimit (1, maxStringsPerCourse, params.stringsPerCourse);

        for (int s = 0; s < numStrings; ++s)
        {
            double detuneCents = 0.0;
            if (numStrings > 1)
            {
                double spread = params.detuneAmount;
                detuneCents = -spread + 2.0 * spread * s / (numStrings - 1);
            }
            double detuneRatio = std::pow (2.0, detuneCents / 1200.0);

            auto modes = StringModel::calculateModes (mat, sp);
            for (auto& m : modes)
                m.frequency *= detuneRatio;

            stringResonators[static_cast<size_t>(s)].prepare (sr);
            stringResonators[static_cast<size_t>(s)].setModes (modes);
            stringResonators[static_cast<size_t>(s)].trigger (velocity);
        }

        setupSoundboard (mat, params, targetFreq, velocity);
        setupExciter (params.exciter, velocity);

        sympatheticMix = static_cast<float> (params.sympatheticAmount);
        soundboardMix  = static_cast<float> (params.soundboardAmount);
    }

    void noteOff ()
    {
        for (int s = 0; s < numStrings; ++s)
            stringResonators[static_cast<size_t>(s)].release (0.8f);
        soundboardResonator.release (0.5f);
    }

    float getNextSample()
    {
        if (! active)
            return 0.0f;

        // Exciter noise burst (hammer impact transient)
        float exciterSample = 0.0f;
        if (exciterEnvelope.isActive())
        {
            float noise = exciterNoise.getNextSample();
            noise = exciterFilter.processSample (noise);
            exciterSample = noise * exciterEnvelope.getNextSample() * currentVelocity;
        }

        // Sum strings
        float stringSum = 0.0f;
        bool anyActive = false;
        for (int s = 0; s < numStrings; ++s)
        {
            auto& res = stringResonators[static_cast<size_t>(s)];
            if (res.isActive())
            {
                stringSum += res.getNextSample();
                anyActive = true;
            }
        }

        if (numStrings > 1)
            stringSum /= std::sqrt (static_cast<float> (numStrings));

        // Soundboard body resonance
        float sbSample = 0.0f;
        if (soundboardResonator.isActive())
        {
            sbSample = soundboardResonator.getNextSample();
            anyActive = true;
        }

        active = anyActive || exciterEnvelope.isActive();

        return exciterSample * 0.3f
             + stringSum
             + sbSample * soundboardMix;
    }

    bool isActive() const { return active; }

    void scaleFrequencies (double factor)
    {
        for (int s = 0; s < numStrings; ++s)
            stringResonators[static_cast<size_t>(s)].scaleFrequencies (factor);
        soundboardResonator.scaleFrequencies (factor);
    }

private:
    void setupSoundboard (const Material& mat, const CimbalomParams& params,
                          double fundamental, float velocity)
    {
        // Soundboard: low-frequency body modes (simplified plate-like)
        std::vector<Mode> sbModes;
        double sbFundamental = fundamental * 0.5;
        double sbRatios[] = { 1.0, 1.58, 2.24, 2.92, 3.61, 4.47 };
        for (int i = 0; i < 6; ++i)
        {
            Mode m;
            m.frequency = sbFundamental * sbRatios[i];
            m.amplitude = 0.15 / (1.0 + i * 0.8);
            double baseTau = 0.3 + 0.2 / (1.0 + i);
            double damp = mat.damping.alpha + mat.damping.betaAir * m.frequency * m.frequency;
            m.decayTime = (damp > 0.0) ? juce::jmin (baseTau, 1.0 / damp) : baseTau;
            sbModes.push_back (m);
        }
        soundboardResonator.prepare (sr);
        soundboardResonator.setModes (sbModes);
        soundboardResonator.trigger (velocity * static_cast<float> (params.soundboardAmount));
    }

    void setupExciter (ExciterType type, float velocity)
    {
        double cutoff = 2000.0;
        double decayMs = 5.0;

        switch (type)
        {
            case ExciterType::Cotton: cutoff = 1500.0;  decayMs = 8.0;  break;
            case ExciterType::Felt:   cutoff = 2500.0;  decayMs = 6.0;  break;
            case ExciterType::Wood:   cutoff = 6000.0;  decayMs = 3.0;  break;
            case ExciterType::Metal:  cutoff = 12000.0; decayMs = 2.0;  break;
        }

        exciterFilter.setParameters (FilterType::LowPass, cutoff, 0.7);
        exciterEnvelope.setDecayTime (decayMs / 1000.0);
        exciterEnvelope.trigger (velocity);
    }

    static constexpr int maxStringsPerCourse = 5;

    double sr = 44100.0;
    float currentVelocity = 0.0f;
    bool active = false;
    int numStrings = 3;

    std::array<ModalResonator, maxStringsPerCourse> stringResonators;
    ModalResonator soundboardResonator;

    NoiseGen exciterNoise;
    BiquadFilter exciterFilter;
    ExpDecayEnvelope exciterEnvelope;

    float sympatheticMix = 0.3f;
    float soundboardMix  = 0.3f;
};
