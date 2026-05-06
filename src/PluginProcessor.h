#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_audio_devices/juce_audio_devices.h>
#include "dsp/ModalResonator.h"
#include "physics/MaterialDB.h"
#include "physics/StringModel.h"

class ModalSound : public juce::SynthesiserSound
{
public:
    bool appliesToNote (int) override { return true; }
    bool appliesToChannel (int) override { return true; }
};

class ModalVoice : public juce::SynthesiserVoice
{
public:
    void setMaterial (const Material* mat) { material = mat; }
    void setStringParams (double diameter, double length, double strikePos, int modes)
    {
        baseDiameter = diameter;
        baseLength   = length;
        strikePosition = strikePos;
        numModes = modes;
    }

    bool canPlaySound (juce::SynthesiserSound* sound) override;
    void startNote (int midiNoteNumber, float velocity,
                    juce::SynthesiserSound*, int currentPitchWheelPosition) override;
    void stopNote (float velocity, bool allowTailOff) override;
    void pitchWheelMoved (int) override {}
    void controllerMoved (int, int) override {}
    void renderNextBlock (juce::AudioBuffer<float>&,
                          int startSample, int numSamples) override;

private:
    ModalResonator resonator;
    const Material* material = nullptr;

    double baseDiameter   = 0.8e-3;
    double baseLength     = 0.35;
    double strikePosition = 0.3;
    int    numModes       = 40;
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
    void setMaterial (const std::string& key);
    void setStrikePosition (double pos);

private:
    void updateVoiceParams();

    juce::Synthesiser synth;
    juce::MidiMessageCollector midiCollector;
    MaterialDB materialDB;

    std::string currentMaterialKey = "steel";
    double currentStrikePosition = 0.3;

    static constexpr int numVoices = 16;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthProcessor)
};
