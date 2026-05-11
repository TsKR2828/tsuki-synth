#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "../dsp/AudioFIFO.h"
#include "../TsukiLookAndFeel.h"
#include "OscilloscopeView.h"

// Container panel for analyzer views (oscilloscope, future spectrum).
// Owns the views and manages enable/disable.
class AnalyzerPanel : public juce::Component
{
public:
    explicit AnalyzerPanel (AudioFIFO& fifo)
        : oscilloscope (fifo)
    {
        addAndMakeVisible (oscilloscope);
    }

    void setActive (bool active)
    {
        oscilloscope.setActive (active);
    }

    void setAccent (juce::Colour c)
    {
        oscilloscope.waveformColour = c;
    }

    void paint (juce::Graphics& g) override
    {
        auto b = getLocalBounds().toFloat();

        g.setColour (Clr::panelBg);
        g.fillRoundedRectangle (b, 5.0f);
        g.setColour (Clr::effectBorder);
        g.drawRoundedRectangle (b.reduced (0.5f), 5.0f, 0.5f);

        g.setColour (Clr::fxTitle);
        g.setFont (juce::Font (juce::FontOptions (9.0f)).boldened());
        g.drawText ("SCOPE", (int) b.getX() + 8, (int) b.getY() + 4,
                    50, 12, juce::Justification::centredLeft);
    }

    void resized() override
    {
        // Future: split area between oscilloscope and spectrumView
        auto inner = getLocalBounds().reduced (6, 0).withTrimmedTop (18);
        oscilloscope.setBounds (inner);
    }

    OscilloscopeView oscilloscope;

    // Future: SpectrumView spectrumView;

private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (AnalyzerPanel)
};
