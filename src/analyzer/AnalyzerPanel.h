#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include <atomic>
#include "../dsp/AudioFIFO.h"
#include "../TsukiLookAndFeel.h"
#include "../UiLocale.h"
#include "OscilloscopeView.h"
#include "SpectrumView.h"
#include "TunerView.h"

class AnalyzerPanel : public juce::Component
{
public:
    explicit AnalyzerPanel (AudioFIFO& postFxFifo, AudioFIFO& dryFifo)
        : oscilloscope (postFxFifo), spectrumView (postFxFifo), tunerView (dryFifo)
    {
        auto initTab = [this] (juce::TextButton& btn, int idx)
        {
            btn.setComponentID ("tab");
            btn.setClickingTogglesState (true);
            btn.setRadioGroupId (2001);
            btn.onClick = [this, idx] { switchTab (idx); };
            addAndMakeVisible (btn);
        };

        initTab (tabScope,    0);
        initTab (tabSpectrum, 1);
        initTab (tabTuner,    2);
        tabScope.setToggleState (true, juce::dontSendNotification);

        addAndMakeVisible (oscilloscope);
        addChildComponent (spectrumView);
        addChildComponent (tunerView);
    }

    void setActive (bool active)
    {
        isActive = active;
        oscilloscope.setActive  (false);
        spectrumView.setActive  (false);
        tunerView.setActive     (false);

        if (active)
        {
            if      (currentTab == 0) oscilloscope.setActive (true);
            else if (currentTab == 1) spectrumView.setActive (true);
            else                      tunerView.setActive (true);
        }
    }

    void setAccent (juce::Colour c)
    {
        oscilloscope.waveformColour = c;
        spectrumView.accentColour   = c;
        tunerView.accentColour      = c;
    }

    void setSampleRate (double sr)
    {
        spectrumView.setSampleRate (sr);
        tunerView.setSampleRate (sr);
    }

    /** Wire processor atomics through to the tuner for synth-aware display. */
    void setSynthAwareSources (std::atomic<int>* lastMidi,
                               std::atomic<float>* engineParam) noexcept
    {
        tunerView.setSynthAwareSources (lastMidi, engineParam);
    }

    void refreshText()
    {
        tabScope.setButtonText    (UiLocale::label ("ui_scope"));
        tabSpectrum.setButtonText (UiLocale::label ("ui_spectrum"));
        tabTuner.setButtonText    (UiLocale::label ("ui_tuner"));
    }

    void paint (juce::Graphics& g) override
    {
        auto b = getLocalBounds().toFloat();
        g.setColour (Clr::panelBg);
        g.fillRoundedRectangle (b, 5.0f);
        g.setColour (Clr::effectBorder);
        g.drawRoundedRectangle (b.reduced (0.5f), 5.0f, 0.5f);
    }

    void resized() override
    {
        auto inner = getLocalBounds().reduced (6, 0).withTrimmedTop (4);

        auto tabRow = inner.removeFromTop (22);
        int tabW = 62;
        tabScope.setBounds    (tabRow.removeFromLeft (tabW));
        tabRow.removeFromLeft (2);
        tabSpectrum.setBounds (tabRow.removeFromLeft (tabW));
        tabRow.removeFromLeft (2);
        tabTuner.setBounds    (tabRow.removeFromLeft (tabW));

        auto content = inner.withTrimmedTop (2);
        oscilloscope.setBounds (content);
        spectrumView.setBounds (content);
        tunerView.setBounds    (content);
    }

    OscilloscopeView oscilloscope;
    SpectrumView     spectrumView;
    TunerView        tunerView;

private:
    juce::TextButton tabScope    { "SCOPE" };
    juce::TextButton tabSpectrum { "SPECTRUM" };
    juce::TextButton tabTuner    { "TUNER" };
    int  currentTab = 0;
    bool isActive   = true;

    void switchTab (int tab)
    {
        if (tab == currentTab)
            return;
        currentTab = tab;

        oscilloscope.setActive (false);
        oscilloscope.setVisible (tab == 0);

        spectrumView.setActive (false);
        spectrumView.setVisible (tab == 1);

        tunerView.setActive (false);
        tunerView.setVisible (tab == 2);

        if (isActive)
        {
            if      (tab == 0) oscilloscope.setActive (true);
            else if (tab == 1) spectrumView.setActive (true);
            else               tunerView.setActive (true);
        }
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (AnalyzerPanel)
};
