#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include <juce_audio_processors/juce_audio_processors.h>
#include "TsukiLookAndFeel.h"

class HarmonicEditor : public juce::Component
{
public:
    using APVTS = juce::AudioProcessorValueTreeState;
    using SliderAttachment = APVTS::SliderAttachment;

    explicit HarmonicEditor (APVTS& vts) : apvts (vts)
    {
        for (int i = 0; i < 8; ++i)
        {
            auto& bar = bars[i];

            bar.ampSlider.setSliderStyle (juce::Slider::LinearBarVertical);
            bar.ampSlider.setRange (0.0, 1.0, 0.01);
            bar.ampSlider.setTextBoxStyle (juce::Slider::NoTextBox, true, 0, 0);
            bar.ampSlider.setColour (juce::Slider::trackColourId, Clr::chromatic.withAlpha (0.6f));
            bar.ampSlider.setColour (juce::Slider::backgroundColourId, Clr::panelBg);
            addAndMakeVisible (bar.ampSlider);

            bar.ratioSlider.setSliderStyle (juce::Slider::RotaryHorizontalVerticalDrag);
            bar.ratioSlider.setRange (0.25, 20.0, 0.01);
            bar.ratioSlider.setTextBoxStyle (juce::Slider::TextBoxBelow, false, 36, 12);
            bar.ratioSlider.setColour (juce::Slider::textBoxTextColourId, Clr::textDim);
            bar.ratioSlider.setColour (juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
            addAndMakeVisible (bar.ratioSlider);

            bar.ampAttach = std::make_unique<SliderAttachment> (
                apvts, "chr_amp_" + juce::String (i), bar.ampSlider);
            bar.ratioAttach = std::make_unique<SliderAttachment> (
                apvts, "chr_ratio_" + juce::String (i), bar.ratioSlider);

            bar.label.setText (juce::String (i + 1), juce::dontSendNotification);
            bar.label.setFont (juce::FontOptions (9.0f));
            bar.label.setColour (juce::Label::textColourId, Clr::textDim);
            bar.label.setJustificationType (juce::Justification::centred);
            addAndMakeVisible (bar.label);
        }
    }

    void paint (juce::Graphics& g) override
    {
        auto b = getLocalBounds().toFloat();
        g.setColour (Clr::panelBg);
        g.fillRoundedRectangle (b, 4.0f);
        g.setColour (Clr::effectBorder);
        g.drawRoundedRectangle (b.reduced (0.5f), 4.0f, 0.5f);

        g.setColour (Clr::fxTitle);
        g.setFont (juce::Font (juce::FontOptions (9.0f)).boldened());
        g.drawText ("HARMONICS", (int) b.getX() + 6, (int) b.getY() + 2, 70, 12,
                    juce::Justification::centredLeft);
    }

    void resized() override
    {
        auto area = getLocalBounds().reduced (4).withTrimmedTop (14);
        int barW = area.getWidth() / 8;
        int ratioH = 32;

        for (int i = 0; i < 8; ++i)
        {
            auto col = area.removeFromLeft (barW);
            auto labelRow = col.removeFromTop (12);
            auto ratioRow = col.removeFromBottom (ratioH);

            bars[i].label.setBounds (labelRow);
            bars[i].ratioSlider.setBounds (ratioRow.reduced (2, 0));
            bars[i].ampSlider.setBounds (col.reduced (3, 2));
        }
    }

private:
    APVTS& apvts;

    struct BarControl
    {
        juce::Slider ampSlider;
        juce::Slider ratioSlider;
        juce::Label  label;
        std::unique_ptr<SliderAttachment> ampAttach;
        std::unique_ptr<SliderAttachment> ratioAttach;
    };

    BarControl bars[8];

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (HarmonicEditor)
};
