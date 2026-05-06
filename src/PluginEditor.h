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
    void handleNoteOn (juce::MidiKeyboardState*, int, int, float) override;
    void handleNoteOff (juce::MidiKeyboardState*, int, int, float) override;
    void populateMaterialBox();
    void showEngineControls();

    TsukiSynthProcessor& processorRef;

    juce::MidiKeyboardState keyboardState;
    juce::MidiKeyboardComponent keyboardComponent;

    // Engine switch
    juce::ComboBox engineBox;
    juce::Label engineLabel;

    // Shared
    juce::ComboBox materialBox;
    juce::Label materialLabel;
    juce::Slider strikeSlider;
    juce::Label strikeLabel;

    // Cimbalom-specific
    juce::ComboBox exciterBox;
    juce::Label exciterLabel;
    juce::Slider stringsSlider;
    juce::Label stringsLabel;
    juce::Slider detuneSlider;
    juce::Label detuneLabel;
    juce::Slider soundboardSlider;
    juce::Label soundboardLabel;

    // Chromatic-specific
    juce::ComboBox subEngineBox;
    juce::Label subEngineLabel;
    juce::Slider waterSlider;
    juce::Label waterLabel;

    // FM Piano-specific
    juce::ComboBox fmPresetBox;
    juce::Label fmPresetLabel;
    juce::Slider fmDetuneSlider;
    juce::Label fmDetuneLabel;
    juce::Slider fmVolumeSlider;
    juce::Label fmVolumeLabel;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthEditor)
};
