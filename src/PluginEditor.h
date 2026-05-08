#pragma once

#include "PluginProcessor.h"
#include <juce_audio_utils/juce_audio_utils.h>

class TsukiSynthEditor : public juce::AudioProcessorEditor,
                          private juce::AudioProcessorValueTreeState::Listener
{
public:
    explicit TsukiSynthEditor (TsukiSynthProcessor&);
    ~TsukiSynthEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;

private:
    using SliderAttachment = juce::AudioProcessorValueTreeState::SliderAttachment;
    using ComboAttachment  = juce::AudioProcessorValueTreeState::ComboBoxAttachment;

    struct ParamSlider
    {
        std::unique_ptr<juce::Slider> slider;
        std::unique_ptr<juce::Label>  label;
        std::unique_ptr<SliderAttachment> attachment;
    };

    struct ParamCombo
    {
        std::unique_ptr<juce::ComboBox> combo;
        std::unique_ptr<juce::Label>    label;
        std::unique_ptr<ComboAttachment> attachment;
    };

    void parameterChanged (const juce::String& parameterID, float newValue) override;
    void updateEngineVisibility();

    void setupSlider (ParamSlider&, const juce::String& paramID,
                      const juce::String& labelText, bool rotary = false);
    void setupCombo  (ParamCombo&, const juce::String& paramID,
                      const juce::String& labelText);
    void setVisible  (ParamSlider&, bool);
    void setVisible  (ParamCombo&, bool);

    void paintPanel (juce::Graphics&, juce::Rectangle<int>, const juce::String& title);

    TsukiSynthProcessor& processorRef;

    // Keyboard
    juce::MidiKeyboardState keyboardState;
    juce::MidiKeyboardComponent keyboardComponent;

    // Engine
    ParamCombo engineCombo;

    // Preset (manual, not APVTS)
    std::unique_ptr<juce::ComboBox> presetCombo;
    std::unique_ptr<juce::Label>    presetLabel;

    // Cimbalom
    ParamCombo  cimMaterial, cimHammer;
    ParamSlider cimStrike, cimDiameter, cimStrings, cimDetune;

    // Chromatic
    ParamCombo  chrSubEngine, chrMaterial, chrExciter;
    ParamSlider chrStrike, chrThickness, chrSize, chrGlide;

    // FM Piano
    ParamCombo  fmType;
    ParamSlider fmRatio, fmIndex, fmBrightness, fmFeedback, fmAttack, fmRelease;

    // Effects
    ParamSlider fxRevMix, fxRevSize;
    ParamSlider fxDlyTime, fxDlyFeedback, fxDlyMix;
    ParamSlider fxCompThresh, fxCompRatio;

    // Distortion
    ParamCombo  distType;
    ParamSlider distDrive, distInstability, distMix;

    // Layout rects
    juce::Rectangle<int> enginePanelBounds;
    juce::Rectangle<int> effectsPanelBounds;
    juce::Rectangle<int> distortionPanelBounds;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthEditor)
};
