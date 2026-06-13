#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "../dsp/AudioFIFO.h"
#include "../TsukiLookAndFeel.h"

class OscilloscopeView : public juce::Component, private juce::Timer
{
public:
    explicit OscilloscopeView (AudioFIFO& fifo)
        : fifo (fifo), scratchBuffer (4096, 0.0f)
    {
    }

    ~OscilloscopeView() override { stopTimer(); }

    void setActive (bool active)
    {
        if (active == isActive)
            return;
        isActive = active;
        if (active)
            startTimerHz (30);
        else
            stopTimer();
        repaint();
    }

    bool getActive() const { return isActive; }

    juce::Colour waveformColour { Clr::gold };

    void paint (juce::Graphics& g) override
    {
        auto bounds = getLocalBounds().toFloat();

        if (! isActive || displayCount < 2)
        {
            g.setColour (Clr::textDim.withAlpha (0.3f));
            g.setFont (TsukiLookAndFeel::scaledFont (10.0f));
            g.drawText ("No signal", bounds, juce::Justification::centred);
            return;
        }

        // center line
        float cy = bounds.getCentreY();
        g.setColour (Clr::border.withAlpha (0.3f));
        g.drawHorizontalLine ((int) cy, bounds.getX(), bounds.getRight());

        // waveform path
        int trigger = findTrigger();
        int samplesToShow = juce::jmin (displayCount - trigger,
                                        (int) scratchBuffer.size());
        if (samplesToShow < 2)
            return;

        float xScale = bounds.getWidth() / (float) (samplesToShow - 1);
        float yScale = bounds.getHeight() * 0.45f;

        juce::Path path;
        path.startNewSubPath (bounds.getX(),
                              cy - scratchBuffer[(size_t) trigger] * yScale);

        for (int i = 1; i < samplesToShow; ++i)
        {
            float x = bounds.getX() + (float) i * xScale;
            float y = cy - scratchBuffer[(size_t) (trigger + i)] * yScale;
            path.lineTo (x, y);
        }

        g.setColour (waveformColour.withAlpha (0.8f));
        g.strokePath (path, juce::PathStrokeType (1.5f,
                          juce::PathStrokeType::curved,
                          juce::PathStrokeType::rounded));
    }

private:
    AudioFIFO& fifo;
    std::vector<float> scratchBuffer;
    int displayCount = 0;
    bool isActive = false;

    void timerCallback() override
    {
        int pulled = fifo.pull (scratchBuffer.data(),
                                (int) scratchBuffer.size());
        if (pulled > 0)
        {
            displayCount = pulled;
            repaint();
        }
    }

    int findTrigger() const
    {
        int searchEnd = juce::jmax (0, displayCount - getWidth());
        for (int i = 1; i < searchEnd; ++i)
        {
            if (scratchBuffer[(size_t) (i - 1)] <= 0.0f &&
                scratchBuffer[(size_t) i] > 0.0f)
                return i;
        }
        return 0;
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (OscilloscopeView)
};
