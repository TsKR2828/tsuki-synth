#pragma once

#include "PluginProcessor.h"
#include <juce_audio_utils/juce_audio_utils.h>

class TsukiSynthEditor : public juce::AudioProcessorEditor,
                          private juce::MidiKeyboardStateListener
{
public:
    explicit TsukiSynthEditor (TsukiSynthProcessor&);
    ~TsukiSynthEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;

private:
    void handleNoteOn (juce::MidiKeyboardState*, int midiChannel, int midiNoteNumber, float velocity) override;
    void handleNoteOff (juce::MidiKeyboardState*, int midiChannel, int midiNoteNumber, float velocity) override;
    void populateMaterialBox();
    void syncParamsToGUI();

    TsukiSynthProcessor& processorRef;

    juce::MidiKeyboardState keyboardState;
    juce::MidiKeyboardComponent keyboardComponent;

    // Controls
    juce::ComboBox materialBox;
    juce::ComboBox exciterBox;
    juce::Slider strikeSlider;
    juce::Slider stringsSlider;
    juce::Slider detuneSlider;
    juce::Slider soundboardSlider;

    // Labels
    juce::Label materialLabel;
    juce::Label exciterLabel;
    juce::Label strikeLabel;
    juce::Label stringsLabel;
    juce::Label detuneLabel;
    juce::Label soundboardLabel;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthEditor)
};
