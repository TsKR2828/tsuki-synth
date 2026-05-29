#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_audio_utils/juce_audio_utils.h>
#include "physics/MaterialDB.h"
#include "effects/EffectChain.h"
#include "dsp/AudioFIFO.h"
#include "PresetManager.h"

class TsukiSynthProcessor : public juce::AudioProcessor
{
public:
    TsukiSynthProcessor();
    ~TsukiSynthProcessor() override;

    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override  { return true; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 2.0; }
    bool isBusesLayoutSupported (const BusesLayout& layouts) const override
    {
        return layouts.getMainOutputChannelSet() == juce::AudioChannelSet::stereo();
    }

    int getNumPrograms() override;
    int getCurrentProgram() override;
    void setCurrentProgram (int index) override;
    const juce::String getProgramName (int index) override;
    void changeProgramName (int, const juce::String&) override {}

    bool startRecording();
    void stopRecording();
    bool isRecording() const { return recordingActive.load(); }
    juce::String getRecordingStatus() const;
    juce::File getLastRecordingFile() const;

    void getStateInformation (juce::MemoryBlock& destData) override;
    void setStateInformation (const void* data, int sizeInBytes) override;

    juce::AudioProcessorValueTreeState apvts;
    PresetManager presetManager { apvts };
    AudioFIFO analyzerFifo { 4096 };
    juce::MidiKeyboardState keyboardState;
    MaterialDB materialDB;

private:
    juce::Synthesiser cimbalomSynth;
    juce::Synthesiser chromaticSynth;
    juce::Synthesiser fmPianoSynth;

    EffectChain effectChain;

    std::atomic<float>* pEngine = nullptr;
    std::atomic<float>* pMacroOutput = nullptr;
    juce::SmoothedValue<float> smoothedOutput { 1.0f };
    int lastEngine = -1;
    int tailOffEngine = -1;  // engine index still rendering tail-off after switch
    bool skipNextProgramChange = false;  // suppress first setCurrentProgram after state restore
    double currentSampleRate = 44100.0;

    juce::TimeSliceThread recordingThread { "TsukiSynth Recorder" };
    mutable juce::CriticalSection recordingLock;
    std::unique_ptr<juce::AudioFormatWriter::ThreadedWriter> recordingWriter;
    std::atomic<bool> recordingActive { false };
    juce::File lastRecordingFile;
    juce::String recordingStatus;

    static juce::AudioProcessorValueTreeState::ParameterLayout
        createParameterLayout();

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthProcessor)
};
