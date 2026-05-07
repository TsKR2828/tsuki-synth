#pragma once
#include "PluginProcessor.h"

class TsukiSynthEditor : public juce::AudioProcessorEditor,
                          private juce::AudioProcessorValueTreeState::Listener
{
public:
    explicit TsukiSynthEditor (TsukiSynthProcessor&);
    ~TsukiSynthEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;

private:
    TsukiSynthProcessor& processorRef;

    void parameterChanged (const juce::String& parameterID, float newValue) override;
    void updateEngineVisibility();

    // UI helpers
    struct ParamSlider
    {
        std::unique_ptr<juce::Slider> slider;
        std::unique_ptr<juce::Label>  label;
        std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> attachment;
    };

    struct ParamCombo
    {
        std::unique_ptr<juce::ComboBox> combo;
        std::unique_ptr<juce::Label>    label;
        std::unique_ptr<juce::AudioProcessorValueTreeState::ComboBoxAttachment> attachment;
    };

    // Engine selector
    ParamCombo engineCombo;

    // Preset selector (non-APVTS, manually managed)
    std::unique_ptr<juce::ComboBox> presetCombo;
    std::unique_ptr<juce::Label>    presetLabel;

    // --- Cimbalom controls ---
    ParamCombo  cimMaterialCombo;
    ParamCombo  cimHammerCombo;
    ParamSlider cimStrikePosSlider;
    ParamSlider cimDiameterSlider;
    ParamSlider cimNumStringsSlider;
    ParamSlider cimDetuningSlider;

    // --- Chromatic controls ---
    ParamCombo  chrSubEngineCombo;
    ParamCombo  chrMaterialCombo;
    ParamSlider chrStrikePosSlider;
    ParamSlider chrThicknessSlider;
    ParamSlider chrSizeSlider;
    ParamCombo  chrExciterCombo;
    ParamSlider chrPitchGlideSlider;

    // --- FM Piano controls ---
    ParamCombo  fmTypeCombo;
    ParamSlider fmRatioSlider;
    ParamSlider fmIndexSlider;
    ParamSlider fmBrightnessSlider;
    ParamSlider fmFeedbackSlider;
    ParamSlider fmAttackSlider;
    ParamSlider fmReleaseSlider;

    // --- Effect chain controls (always visible) ---
    ParamSlider fxReverbMixSlider;
    ParamSlider fxReverbSizeSlider;
    ParamSlider fxDelayTimeSlider;
    ParamSlider fxDelayFbSlider;
    ParamSlider fxDelayMixSlider;
    ParamSlider fxCompThreshSlider;
    ParamSlider fxCompRatioSlider;

    void setupCombo (ParamCombo& pc, const juce::String& paramID,
                     const juce::String& labelText);
    void setupSlider (ParamSlider& ps, const juce::String& paramID,
                      const juce::String& labelText, const juce::String& suffix = {});

    void setComponentVisible (ParamCombo& pc, bool visible);
    void setComponentVisible (ParamSlider& ps, bool visible);

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthEditor)
};
