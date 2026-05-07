#pragma once
#include "PluginProcessor.h"

class TsukiSynthEditor : public juce::AudioProcessorEditor
{
public:
    explicit TsukiSynthEditor (TsukiSynthProcessor&);
    ~TsukiSynthEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;

private:
    TsukiSynthProcessor& processorRef;

    // 參數 UI 元件
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

    ParamCombo  materialCombo;
    ParamCombo  hammerCombo;
    ParamSlider strikePosSlider;
    ParamSlider diameterSlider;
    ParamSlider numStringsSlider;
    ParamSlider detuningSlider;

    void setupCombo (ParamCombo& pc, const juce::String& paramID,
                     const juce::String& labelText);
    void setupSlider (ParamSlider& ps, const juce::String& paramID,
                      const juce::String& labelText, const juce::String& suffix = {});

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthEditor)
};
