#pragma once

#include <cmath>
#include <juce_core/juce_core.h>

enum class FMPreset
{
    Piano, ElectricPiano, Vibraphone, Bell,
    Organ, Bass, Strings, Brass
};

struct FMPresetData
{
    const char* name;
    double ratio;
    double index;
    double indexDecayTime;
    double ampDecayTime;
    double attackTime;
    double releaseTime;
    double brightnessRolloff;
    double ratio2;
    double index2;
    double index2DecayTime;
};

inline FMPresetData getFMPresetData (FMPreset p)
{
    switch (p)
    {
        case FMPreset::Piano:
            return { "Piano", 1.0, 5.0, 0.8, 3.0, 0.002, 0.3, 0.7, 3.0, 1.5, 0.4 };
        case FMPreset::ElectricPiano:
            return { "Electric Piano", 1.0, 3.5, 1.2, 2.5, 0.001, 0.4, 0.5, 7.0, 0.8, 0.6 };
        case FMPreset::Vibraphone:
            return { "Vibraphone", 1.0, 2.0, 2.0, 4.0, 0.001, 0.5, 0.3, 4.0, 0.5, 1.5 };
        case FMPreset::Bell:
            return { "Bell", 1.0, 8.0, 3.0, 6.0, 0.001, 1.0, 0.2, 1.4, 4.0, 2.0 };
        case FMPreset::Organ:
            return { "Organ", 1.0, 1.5, 100.0, 100.0, 0.01, 0.05, 0.1, 2.0, 0.5, 100.0 };
        case FMPreset::Bass:
            return { "Bass", 1.0, 6.0, 0.3, 1.0, 0.002, 0.1, 1.0, 1.0, 2.0, 0.15 };
        case FMPreset::Strings:
            return { "Strings", 1.0, 1.0, 100.0, 100.0, 0.15, 0.8, 0.2, 2.0, 0.3, 100.0 };
        case FMPreset::Brass:
            return { "Brass", 1.0, 4.0, 100.0, 100.0, 0.05, 0.15, 0.4, 1.0, 1.5, 100.0 };
    }
    return { "Piano", 1.0, 5.0, 0.8, 3.0, 0.002, 0.3, 0.7, 3.0, 1.5, 0.4 };
}

struct FMParams
{
    FMPreset preset       = FMPreset::Piano;
    double   masterVolume = 0.8;
    double   detune       = 0.0;
    double   stereoWidth  = 0.3;
};

class FMVoice
{
public:
    void prepare (double sampleRate)
    {
        sr = sampleRate;
    }

    void noteOn (int midiNote, float velocity, const FMParams& params)
    {
        active = true;
        released = false;
        sampleIndex = 0;

        double freq = juce::MidiMessage::getMidiNoteInHertz (midiNote);
        freq += params.detune;

        auto pd = getFMPresetData (params.preset);

        double brightnessScale = 1.0;
        if (midiNote > 60)
            brightnessScale = 1.0 - pd.brightnessRolloff * (midiNote - 60) / 67.0;
        brightnessScale = juce::jmax (0.05, brightnessScale);

        double vel = static_cast<double> (velocity);
        double velIndex = 0.5 + vel * 0.5;

        carrierFreq = freq;
        carrierPhase = 0.0;
        carrierInc = juce::MathConstants<double>::twoPi * freq / sr;

        mod1Freq = freq * pd.ratio;
        mod1Phase = 0.0;
        mod1Inc = juce::MathConstants<double>::twoPi * mod1Freq / sr;
        mod1Index = pd.index * velIndex * brightnessScale;
        mod1IndexDecay = calcDecayFactor (pd.indexDecayTime);

        mod2Freq = freq * pd.ratio2;
        mod2Phase = 0.0;
        mod2Inc = juce::MathConstants<double>::twoPi * mod2Freq / sr;
        mod2Index = pd.index2 * velIndex * brightnessScale;
        mod2IndexDecay = calcDecayFactor (pd.index2DecayTime);

        ampLevel = vel * params.masterVolume;
        ampDecay = calcDecayFactor (pd.ampDecayTime);

        attackSamples = static_cast<int> (pd.attackTime * sr);
        if (attackSamples < 1) attackSamples = 1;
        attackInc = 1.0 / static_cast<double> (attackSamples);
        attackPhase = 0.0;

        releaseDecay = calcDecayFactor (pd.releaseTime);
    }

    void noteOff()
    {
        released = true;
    }

    float getNextSample()
    {
        if (! active)
            return 0.0f;

        double env = ampLevel;
        if (sampleIndex < attackSamples)
        {
            attackPhase += attackInc;
            env *= attackPhase;
        }

        double m1 = mod1Index * std::sin (mod1Phase);
        double m2 = mod2Index * std::sin (mod2Phase);
        double out = env * std::sin (carrierPhase + m1 + m2);

        carrierPhase += carrierInc;
        mod1Phase += mod1Inc;
        mod2Phase += mod2Inc;

        if (carrierPhase > 1e6) carrierPhase = std::fmod (carrierPhase, juce::MathConstants<double>::twoPi);
        if (mod1Phase > 1e6) mod1Phase = std::fmod (mod1Phase, juce::MathConstants<double>::twoPi);
        if (mod2Phase > 1e6) mod2Phase = std::fmod (mod2Phase, juce::MathConstants<double>::twoPi);

        mod1Index *= mod1IndexDecay;
        mod2Index *= mod2IndexDecay;

        if (released)
            ampLevel *= releaseDecay;
        else
            ampLevel *= ampDecay;

        ++sampleIndex;

        if (ampLevel < 1e-7)
        {
            active = false;
            return 0.0f;
        }

        return static_cast<float> (out);
    }

    bool isActive() const { return active; }

private:
    double calcDecayFactor (double seconds)
    {
        if (seconds > 50.0) return 1.0;
        if (sr > 0.0 && seconds > 0.0)
            return std::exp (-1.0 / (seconds * sr));
        return 0.0;
    }

    double sr = 44100.0;
    bool active = false;
    bool released = false;
    int sampleIndex = 0;

    double carrierFreq = 440.0;
    double carrierPhase = 0.0;
    double carrierInc = 0.0;

    double mod1Freq = 440.0;
    double mod1Phase = 0.0;
    double mod1Inc = 0.0;
    double mod1Index = 0.0;
    double mod1IndexDecay = 0.999;

    double mod2Freq = 440.0;
    double mod2Phase = 0.0;
    double mod2Inc = 0.0;
    double mod2Index = 0.0;
    double mod2IndexDecay = 0.999;

    double ampLevel = 0.0;
    double ampDecay = 0.999;
    double releaseDecay = 0.99;

    int attackSamples = 1;
    double attackInc = 1.0;
    double attackPhase = 0.0;
};
