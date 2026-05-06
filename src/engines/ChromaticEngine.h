#pragma once

#include "../dsp/ModalResonator.h"
#include "../dsp/NoiseGen.h"
#include "../dsp/BiquadFilter.h"
#include "../dsp/Envelope.h"
#include "../physics/MaterialDB.h"
#include "../physics/BeamModel.h"
#include "../physics/PlateModel.h"
#include <juce_core/juce_core.h>

enum class ChromaticSubEngine { TongueDrum, WaterGong, CustomHarmonics };

struct ChromaticParams
{
    ChromaticSubEngine subEngine = ChromaticSubEngine::TongueDrum;
    std::string materialKey     = "aluminum";

    // Tongue drum (beam)
    double tongueLength    = 0.12;
    double tongueWidth     = 0.025;
    double tongueThickness = 0.003;

    // Water gong (plate)
    double plateRadius     = 0.15;
    double plateThickness  = 0.002;
    double waterLevel      = 0.0;  // 0 = dry, 1 = fully submerged

    // Shared
    double strikePosition  = 0.5;
    int    numModes        = 20;

    // Custom harmonics
    struct Harmonic { double ratio; double amplitude; };
    std::vector<Harmonic> customHarmonics = {
        {1.0, 1.0}, {2.0, 0.5}, {3.0, 0.25}, {4.16, 0.15},
        {5.43, 0.1}, {6.8, 0.06}, {8.2, 0.03}
    };
};

class ChromaticVoice
{
public:
    void prepare (double sampleRate)
    {
        sr = sampleRate;
        resonator.prepare (sampleRate);
        exciterEnvelope.prepare (sampleRate);
        exciterNoise.setType (NoiseType::White);
        exciterFilter.prepare (sampleRate);
    }

    void noteOn (int midiNote, float velocity, const Material& mat,
                 const ChromaticParams& params)
    {
        active = true;
        double targetFreq = juce::MidiMessage::getMidiNoteInHertz (midiNote);

        std::vector<Mode> modes;

        switch (params.subEngine)
        {
            case ChromaticSubEngine::TongueDrum:
                modes = buildTongueDrumModes (mat, params, targetFreq);
                break;

            case ChromaticSubEngine::WaterGong:
                modes = buildWaterGongModes (mat, params, targetFreq);
                waterGlideActive = params.waterLevel > 0.01;
                waterGlidePhase = 0.0;
                waterGlideFactor = 1.0;
                waterGlideTarget = 1.0 / (1.0 + params.waterLevel * 0.6);
                waterGlideSpeed = 0.5 + params.waterLevel * 2.0;
                break;

            case ChromaticSubEngine::CustomHarmonics:
                modes = buildCustomModes (params, targetFreq, mat);
                break;
        }

        resonator.prepare (sr);
        resonator.setModes (modes);
        resonator.trigger (velocity);

        // Exciter
        double cutoff = 4000.0;
        double decay  = 4.0;
        exciterFilter.setParameters (FilterType::LowPass, cutoff, 0.7);
        exciterEnvelope.setDecayTime (decay / 1000.0);
        exciterEnvelope.trigger (velocity);
    }

    void noteOff()
    {
        resonator.release();
    }

    float getNextSample()
    {
        if (! active)
            return 0.0f;

        // Water gong pitch glide effect
        if (waterGlideActive && waterGlideFactor > waterGlideTarget)
        {
            waterGlidePhase += 1.0 / sr;
            double progress = 1.0 - std::exp (-waterGlidePhase * waterGlideSpeed);
            waterGlideFactor = 1.0 - progress * (1.0 - waterGlideTarget);
        }

        float exciterSample = 0.0f;
        if (exciterEnvelope.isActive())
        {
            float noise = exciterNoise.getNextSample();
            noise = exciterFilter.processSample (noise);
            exciterSample = noise * exciterEnvelope.getNextSample();
        }

        if (waterGlideActive)
            resonator.scaleFrequencies (waterGlideFactor);

        float resonatorSample = resonator.getNextSample();
        active = resonator.isActive() || exciterEnvelope.isActive();

        return exciterSample * 0.2f + resonatorSample;
    }

    bool isActive() const { return active; }

private:
    std::vector<Mode> buildTongueDrumModes (const Material& mat,
                                             const ChromaticParams& params,
                                             double targetFreq)
    {
        BeamParams bp;
        bp.length    = params.tongueLength;
        bp.width     = params.tongueWidth;
        bp.thickness = params.tongueThickness;
        bp.strikePosition = params.strikePosition;
        bp.numModes  = params.numModes;

        auto modes = BeamModel::calculateModes (mat, bp);

        if (modes.empty())
            return modes;

        // Scale all modes so fundamental matches target MIDI frequency
        double ratio = targetFreq / modes[0].frequency;
        for (auto& m : modes)
            m.frequency *= ratio;

        return modes;
    }

    std::vector<Mode> buildWaterGongModes (const Material& mat,
                                            const ChromaticParams& params,
                                            double targetFreq)
    {
        PlateParams pp;
        pp.radius    = params.plateRadius;
        pp.thickness = params.plateThickness;
        pp.strikePosition = params.strikePosition;
        pp.numModes  = params.numModes;

        auto modes = PlateModel::calculateModes (mat, pp);

        if (modes.empty())
            return modes;

        double ratio = targetFreq / modes[0].frequency;
        for (auto& m : modes)
        {
            m.frequency *= ratio;
            // Water adds mass, increases damping
            m.decayTime *= (1.0 - params.waterLevel * 0.4);
        }

        return modes;
    }

    std::vector<Mode> buildCustomModes (const ChromaticParams& params,
                                         double targetFreq,
                                         const Material& mat)
    {
        std::vector<Mode> modes;
        const double alpha = mat.damping.alpha;
        const double beta  = mat.damping.betaAir;
        const double gamma = mat.damping.gammaRadiation;

        for (const auto& h : params.customHarmonics)
        {
            double freq = targetFreq * h.ratio;
            double denom = alpha + beta * freq * freq + gamma * freq;
            double tau = (denom > 0.0) ? 1.0 / denom : 3.0;

            Mode m;
            m.frequency = freq;
            m.amplitude = h.amplitude;
            m.decayTime = tau;
            modes.push_back (m);
        }

        return modes;
    }

    double sr = 44100.0;
    bool active = false;

    ModalResonator resonator;
    NoiseGen exciterNoise;
    BiquadFilter exciterFilter;
    ExpDecayEnvelope exciterEnvelope;

    // Water gong pitch glide
    bool   waterGlideActive = false;
    double waterGlidePhase  = 0.0;
    double waterGlideFactor = 1.0;
    double waterGlideTarget = 1.0;
    double waterGlideSpeed  = 1.0;
};
