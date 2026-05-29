#pragma once

#include "PluginProcessor.h"
#include "TsukiLookAndFeel.h"
#include "UiLocale.h"
#include "analyzer/AnalyzerPanel.h"
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
        juce::String paramID;
    };

    struct ComboParam
    {
        juce::ComboBox combo;
        juce::Label    label;
        std::unique_ptr<ComboAttachment> attachment;
        juce::String paramID;
    };

    class LocalizedMidiKeyboard : public juce::MidiKeyboardComponent
    {
    public:
        LocalizedMidiKeyboard (juce::MidiKeyboardState& state,
                               juce::MidiKeyboardComponent::Orientation orientation)
            : juce::MidiKeyboardComponent (state, orientation) {}

        /** Set the "sweet spot" range indicator for the current engine. */
        void setRangeIndicator (int low, int high, juce::Colour colour)
        {
            rangeLow    = low;
            rangeHigh   = high;
            rangeColour = colour;
            repaint();
        }

        juce::String getWhiteNoteText (int midiNoteNumber) override
        {
            return juce::MidiKeyboardComponent::getWhiteNoteText (midiNoteNumber);
        }

        void drawWhiteNote (int midiNoteNumber, juce::Graphics& g,
                            juce::Rectangle<float> area,
                            bool isDown, bool isOver,
                            juce::Colour lineColour, juce::Colour textColour) override
        {
            juce::MidiKeyboardComponent::drawWhiteNote (
                midiNoteNumber, g, area, isDown, isOver, lineColour, textColour);

            if (rangeLow < rangeHigh
                && midiNoteNumber >= rangeLow && midiNoteNumber <= rangeHigh)
            {
                g.setColour (rangeColour.withAlpha (isDown ? 0.0f : 0.4f));
                g.fillRect (area.getX() + 1.0f, area.getBottom() - 3.0f,
                            area.getWidth() - 2.0f, 2.5f);
            }
        }

        void drawBlackNote (int midiNoteNumber, juce::Graphics& g,
                            juce::Rectangle<float> area,
                            bool isDown, bool isOver,
                            juce::Colour noteFillColour) override
        {
            juce::MidiKeyboardComponent::drawBlackNote (
                midiNoteNumber, g, area, isDown, isOver, noteFillColour);

            if (rangeLow < rangeHigh
                && midiNoteNumber >= rangeLow && midiNoteNumber <= rangeHigh)
            {
                g.setColour (rangeColour.withAlpha (isDown ? 0.0f : 0.55f));
                g.fillRect (area.getX() + 1.0f, area.getBottom() - 2.5f,
                            area.getWidth() - 2.0f, 2.0f);
            }
        }

    private:
        int rangeLow  = 0;
        int rangeHigh = 127;
        juce::Colour rangeColour { 0xffc49a6c };  // Clr::gold
    };

    void parameterChanged (const juce::String& parameterID, float newValue) override;
    void timerCallback() override;

    void setupKnob  (KnobParam&,  const juce::String& paramID, bool small = false);
    void setupCombo  (ComboParam&, const juce::String& paramID);
    void setVisible  (KnobParam&,  bool);
    void setVisible  (ComboParam&, bool);
    void updateEngine();
    int  currentEngine() const;
    juce::Colour accentForEngine (int eng) const;

    // Localization
    void refreshLocalizedText();
    void refreshComboItems (ComboParam&);
    void refreshRecorderText();

    void paintPanel (juce::Graphics&, juce::Rectangle<int>, const juce::String& title);
    void layoutKnobCell  (juce::Rectangle<int> cell, KnobParam&);
    void layoutComboCell (juce::Rectangle<int> cell, ComboParam&);
    void layoutFxKnob    (juce::Rectangle<int> cell, KnobParam&);

    TsukiSynthProcessor& proc;
    TsukiLookAndFeel lnf;

    // Keyboard (state lives in processor for MIDI injection)
    LocalizedMidiKeyboard keyboard;

    // Engine tabs
    juce::TextButton tabCim { "Cimbalom" };
    juce::TextButton tabChr { "Chromatic" };
    juce::TextButton tabFM  { "FM Piano" };

    // Language toggle
    juce::TextButton langToggle;

    // Standalone recorder
    juce::TextButton recordButton { "REC" };

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

    // Macro
    KnobParam macroMaterial, macroTension, macroDamping, macroStrike;
    KnobParam macroBrightness, macroBody, macroNoise, macroOutput;

    // Effects
    KnobParam fxRevMix, fxRevSize;
    KnobParam fxDlyTime, fxDlyFeedback, fxDlyMix;
    KnobParam fxCompThresh, fxCompRatio;

    // Distortion
    ComboParam  distType;
    KnobParam   distDrive, distInstability, distMix;

    // Analyzer
    AnalyzerPanel analyzerPanel;

    // Brand assets
    juce::Path moonPath;
    juce::Typeface::Ptr wordmarkTypeface;

    // Layout bounds (stored in resized, used in paint)
    juce::Rectangle<int> macroArea_, engineArea_, effectsRow_, distRow_, analyzerRow_;
    juce::Rectangle<int> reverbBounds_, delayBounds_, compBounds_, distPanelBounds_;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthEditor)
};
