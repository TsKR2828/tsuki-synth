#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_audio_devices/juce_audio_devices.h>
#include "engines/CimbalomEngine.h"
#include "engines/ChromaticEngine.h"
#include "engines/FMPianoEngine.h"
#include "physics/MaterialDB.h"
#include "dsp/EffectsChain.h"

enum class EngineType { Cimbalom, Chromatic, FMPiano };

class MultiSound : public juce::SynthesiserSound
{
public:
    bool appliesToNote (int) override { return true; }
    bool appliesToChannel (int) override { return true; }
};

class MultiVoice : public juce::SynthesiserVoice
{
public:
    void setEngine (EngineType e)          { engineType = e; }
    void setMaterial (const Material* m)   { material = m; }
    void setCimbalomParams (const CimbalomParams* p)   { cimParams = p; }
    void setChromaticParams (const ChromaticParams* p)  { chrParams = p; }
    void setFMParams (const FMParams* p)               { fmParams = p; }

    bool canPlaySound (juce::SynthesiserSound* s) override
    {
        return dynamic_cast<MultiSound*> (s) != nullptr;
    }

    void startNote (int midiNote, float velocity, juce::SynthesiserSound*, int) override
    {
        activeEngine = engineType;

        if (engineType == EngineType::FMPiano && fmParams != nullptr)
        {
            fmVoice.prepare (getSampleRate());
            fmVoice.noteOn (midiNote, velocity, *fmParams);
            return;
        }

        if (material == nullptr)
            return;

        if (engineType == EngineType::Cimbalom && cimParams != nullptr)
        {
            cimVoice.prepare (getSampleRate());
            cimVoice.noteOn (midiNote, velocity, *material, *cimParams);
        }
        else if (engineType == EngineType::Chromatic && chrParams != nullptr)
        {
            chrVoice.prepare (getSampleRate());
            chrVoice.noteOn (midiNote, velocity, *material, *chrParams);
        }
    }

    void stopNote (float, bool allowTailOff) override
    {
        if (allowTailOff)
        {
            switch (activeEngine)
            {
                case EngineType::Cimbalom: cimVoice.noteOff(); break;
                case EngineType::Chromatic: chrVoice.noteOff(); break;
                case EngineType::FMPiano: fmVoice.noteOff(); break;
            }
        }
        else
        {
            clearCurrentNote();
        }
    }

    void pitchWheelMoved (int) override {}
    void controllerMoved (int, int) override {}

    void renderNextBlock (juce::AudioBuffer<float>& buf, int start, int num) override
    {
        bool eng = false;
        switch (activeEngine)
        {
            case EngineType::Cimbalom: eng = cimVoice.isActive(); break;
            case EngineType::Chromatic: eng = chrVoice.isActive(); break;
            case EngineType::FMPiano: eng = fmVoice.isActive(); break;
        }

        if (! eng)
        {
            if (isVoiceActive()) clearCurrentNote();
            return;
        }

        for (int i = 0; i < num; ++i)
        {
            float v = 0.0f;
            switch (activeEngine)
            {
                case EngineType::Cimbalom: v = cimVoice.getNextSample(); break;
                case EngineType::Chromatic: v = chrVoice.getNextSample(); break;
                case EngineType::FMPiano: v = fmVoice.getNextSample(); break;
            }
            v *= 0.15f;
            for (int ch = 0; ch < buf.getNumChannels(); ++ch)
                buf.addSample (ch, start + i, v);

            bool still = false;
            switch (activeEngine)
            {
                case EngineType::Cimbalom: still = cimVoice.isActive(); break;
                case EngineType::Chromatic: still = chrVoice.isActive(); break;
                case EngineType::FMPiano: still = fmVoice.isActive(); break;
            }
            if (! still) { clearCurrentNote(); break; }
        }
    }

private:
    EngineType engineType = EngineType::Cimbalom;
    EngineType activeEngine = EngineType::Cimbalom;
    const Material* material = nullptr;
    const CimbalomParams* cimParams = nullptr;
    const ChromaticParams* chrParams = nullptr;
    const FMParams* fmParams = nullptr;

    CimbalomVoice cimVoice;
    ChromaticVoice chrVoice;
    FMVoice fmVoice;
};

class TsukiSynthProcessor : public juce::AudioProcessor
{
public:
    TsukiSynthProcessor();
    ~TsukiSynthProcessor() override;

    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override;
    bool isBusesLayoutSupported (const BusesLayout& layouts) const override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override;

    const juce::String getName() const override;
    bool acceptsMidi() const override;
    bool producesMidi() const override;
    bool isMidiEffect() const override;
    double getTailLengthSeconds() const override;

    int getNumPrograms() override;
    int getCurrentProgram() override;
    void setCurrentProgram (int index) override;
    const juce::String getProgramName (int index) override;
    void changeProgramName (int index, const juce::String& newName) override;

    void getStateInformation (juce::MemoryBlock& destData) override;
    void setStateInformation (const void* data, int sizeInBytes) override;

    void addMidiMessage (const juce::MidiMessage& message);

    MaterialDB& getMaterialDB() { return materialDB; }
    CimbalomParams& getCimbalomParams() { return cimbalomParams; }
    ChromaticParams& getChromaticParams() { return chromaticParams; }
    FMParams& getFMParams() { return fmParams; }
    EffectsParams& getEffectsParams() { return effectsParams; }
    EffectsChain& getEffectsChain() { return effectsChain; }

    EngineType getEngineType() const { return engineType; }
    void setEngineType (EngineType e);
    void setMaterial (const std::string& key);
    void updateVoiceParams();

private:
    juce::Synthesiser synth;
    juce::MidiMessageCollector midiCollector;
    MaterialDB materialDB;

    EngineType engineType = EngineType::Cimbalom;
    CimbalomParams cimbalomParams;
    ChromaticParams chromaticParams;
    FMParams fmParams;
    EffectsParams effectsParams;
    EffectsChain effectsChain;

    static constexpr int numVoices = 12;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthProcessor)
};
