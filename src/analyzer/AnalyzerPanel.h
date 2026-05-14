#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "../dsp/AudioFIFO.h"
#include "../TsukiLookAndFeel.h"
#include "OscilloscopeView.h"
#include "SpectrumView.h"

class AnalyzerPanel : public juce::Component
{
public:
    explicit AnalyzerPanel (AudioFIFO& fifo)
        : oscilloscope (fifo),
          spectrumView (fifo)
    {
        addAndMakeVisible (oscilloscope);
        addChildComponent (spectrumView);

        toggleBtn.setButtonText ("SPECTRUM");
        toggleBtn.setColour (juce::TextButton::buttonColourId, juce::Colours::transparentBlack);
        toggleBtn.setColour (juce::TextButton::textColourOffId, Clr::textDim);
        toggleBtn.onClick = [this] { toggleView(); };
        addAndMakeVisible (toggleBtn);
    }

    void setActive (bool active)
    {
        oscilloscope.setActive (showingSpectrum ? false : active);
        spectrumView.setActive (showingSpectrum ? active : false);
    }

    void setAccent (juce::Colour c)
    {
        oscilloscope.waveformColour = c;
        spectrumView.spectrumColour = c;
    }

    void setSampleRate (double sr)
    {
        spectrumView.setSampleRate (sr);
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
        g.drawText (showingSpectrum ? "SPECTRUM" : "SCOPE",
                    (int) b.getX() + 8, (int) b.getY() + 4,
                    60, 12, juce::Justification::centredLeft);
    }

    void resized() override
    {
        auto area = getLocalBounds();
        auto header = area.removeFromTop (18);
        toggleBtn.setBounds (header.removeFromRight (70).reduced (2, 1));

        auto inner = area.reduced (6, 0);
        oscilloscope.setBounds (inner);
        spectrumView.setBounds (inner);
    }

    OscilloscopeView oscilloscope;
    SpectrumView     spectrumView;

private:
    juce::TextButton toggleBtn;
    bool showingSpectrum = false;

    void toggleView()
    {
        showingSpectrum = ! showingSpectrum;
        oscilloscope.setVisible (! showingSpectrum);
        spectrumView.setVisible (showingSpectrum);

        bool active = oscilloscope.getActive() || spectrumView.getActive();
        oscilloscope.setActive (! showingSpectrum && active);
        spectrumView.setActive (showingSpectrum && active);

        toggleBtn.setButtonText (showingSpectrum ? "SCOPE" : "SPECTRUM");
        repaint();
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (AnalyzerPanel)
};
