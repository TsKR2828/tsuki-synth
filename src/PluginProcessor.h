#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_audio_devices/juce_audio_devices.h>
#include "engines/CimbalomEngine.h"
#include "physics/MaterialDB.h"

class CimbalomSound : public juce::SynthesiserSound
{
public:
    bool appliesToNote (int) override { return true; }
    bool appliesToChannel (int) override { return true; }
};

class CimbalomJuceVoice : public juce::SynthesiserVoice
{
public:
    void setParams (const Material* mat, const CimbalomParams* p)
    {
        material = mat;
        params = p;
    }

    bool canPlaySound (juce::SynthesiserSound* sound) override
    {
        return dynamic_cast<CimbalomSound*> (sound) != nullptr;
    }

    void startNote (int midiNoteNumber, float velocity,
                    juce::SynthesiserSound*, int) override
    {
        if (material == nullptr || params == nullptr)
            return;
        engine.prepare (getSampleRate());
        engine.noteOn (midiNoteNumber, velocity, *material, *params);
    }

    void stopNote (float, bool allowTailOff) override
    {
        if (allowTailOff)
            engine.noteOff();
        else
            clearCurrentNote();
    }

    void pitchWheelMoved (int) override {}
    void controllerMoved (int, int) override {}

    void renderNextBlock (juce::AudioBuffer<float>& buffer,
                          int startSample, int numSamples) override
    {
        if (! engine.isActive())
        {
            if (isVoiceActive())
                clearCurrentNote();
            return;
        }

        for (int i = 0; i < numSamples; ++i)
        {
            float value = engine.getNextSample() * 0.15f;
            for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
                buffer.addSample (ch, startSample + i, value);

            if (! engine.isActive())
            {
                clearCurrentNote();
                break;
            }
        }
    }

private:
    CimbalomVoice engine;
    const Material* material = nullptr;
    const CimbalomParams* params = nullptr;
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

    void setMaterial (const std::string& key);
    void updateVoiceParams();

private:
    juce::Synthesiser synth;
    juce::MidiMessageCollector midiCollector;
    MaterialDB materialDB;
    CimbalomParams cimbalomParams;

    static constexpr int numVoices = 12;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthProcessor)
};
