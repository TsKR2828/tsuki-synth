#pragma once

#include "PluginProcessor.h"
#include "TsukiLookAndFeel.h"
#include <juce_audio_utils/juce_audio_utils.h>

class TsukiSynthEditor : public juce::AudioProcessorEditor,
                          private juce::AudioProcessorValueTreeState::Listener,
                          private juce::Timer
{
public:
    explicit TsukiSynthEditor (TsukiSynthProcessor&);
    ~TsukiSynthEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;

private:
    using SliderAttachment = juce::AudioProcessorValueTreeState::SliderAttachment;
    using ComboAttachment  = juce::AudioProcessorValueTreeState::ComboBoxAttachment;

    struct KnobParam
    {
        juce::Slider slider;
        juce::Label  label;
        std::unique_ptr<SliderAttachment> attachment;
    };

    struct ComboParam
    {
        juce::ComboBox combo;
        juce::Label    label;
        std::unique_ptr<ComboAttachment> attachment;
    };

    void parameterChanged (const juce::String& parameterID, float newValue) override;
    void timerCallback() override;

    void setupKnob  (KnobParam&,  const juce::String& paramID,
                     const juce::String& labelText, bool small = false);
    void setupCombo  (ComboParam&, const juce::String& paramID,
                     const juce::String& labelText);
    void setVisible  (KnobParam&,  bool);
    void setVisible  (ComboParam&, bool);
    void updateEngine();
    int  currentEngine() const;
    juce::Colour accentForEngine (int eng) const;

    void paintPanel (juce::Graphics&, juce::Rectangle<int>, const juce::String& title);
    void layoutKnobCell  (juce::Rectangle<int> cell, KnobParam&);
    void layoutComboCell (juce::Rectangle<int> cell, ComboParam&);
    void layoutFxKnob    (juce::Rectangle<int> cell, KnobParam&);

    TsukiSynthProcessor& proc;
    TsukiLookAndFeel lnf;

    // Keyboard (state lives in processor for MIDI injection)
    juce::MidiKeyboardComponent keyboard;

    // Engine tabs
    juce::TextButton tabCim { "Cimbalom" };
    juce::TextButton tabChr { "Chromatic" };
    juce::TextButton tabFM  { "FM Piano" };

    // Preset
    juce::ComboBox   presetCombo;
    juce::TextButton presetPrev, presetNext;
    juce::TextButton presetSave { "Save" };
    juce::TextButton presetInit { "Init" };
    juce::Label      dirtyLabel;
    void rebuildPresetCombo();
    void updateDirtyIndicator();
    void promptSavePreset();

    // Cimbalom
    ComboParam  cimMaterial, cimHammer;
    KnobParam   cimStrike, cimDiameter, cimStrings, cimDetune;

    // Chromatic
    ComboParam  chrSubEngine, chrMaterial, chrExciter;
    KnobParam   chrStrike, chrThickness, chrSize, chrGlide;

    // FM Piano
    ComboParam  fmType;
    KnobParam   fmRatio, fmIndex, fmBrightness, fmFeedback, fmAttack, fmRelease;

    // Effects
    KnobParam fxRevMix, fxRevSize;
    KnobParam fxDlyTime, fxDlyFeedback, fxDlyMix;
    KnobParam fxCompThresh, fxCompRatio;

    // Distortion
    ComboParam  distType;
    KnobParam   distDrive, distInstability, distMix;

    // Layout bounds (stored in resized, used in paint)
    juce::Rectangle<int> engineArea_, effectsRow_, distRow_;
    juce::Rectangle<int> reverbBounds_, delayBounds_, compBounds_, distPanelBounds_;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthEditor)
};
