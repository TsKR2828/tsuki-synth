#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include <juce_dsp/juce_dsp.h>
#include "../dsp/AudioFIFO.h"
#include "../TsukiLookAndFeel.h"
#include <cmath>
#include <vector>

class SpectrumView : public juce::Component, private juce::Timer
{
public:
    explicit SpectrumView (AudioFIFO& fifo)
        : fifo (fifo),
          fftOrder (11),
          fftSize (1 << fftOrder),
          fft (fftOrder),
          window (static_cast<size_t> (fftSize), juce::dsp::WindowingFunction<float>::hann),
          fftData (static_cast<size_t> (fftSize * 2), 0.0f),
          scratchBuffer (static_cast<size_t> (fftSize), 0.0f),
          smoothedMagnitudes (static_cast<size_t> (fftSize / 2), -100.0f)
    {
    }

    ~SpectrumView() override { stopTimer(); }

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

    juce::Colour spectrumColour { Clr::gold };

    void setSampleRate (double sr) { sampleRate = sr; }

    void paint (juce::Graphics& g) override
    {
        auto bounds = getLocalBounds().toFloat();

        if (! isActive || ! hasData)
        {
            g.setColour (Clr::textDim.withAlpha (0.3f));
            g.setFont (juce::FontOptions (10.0f));
            g.drawText ("No signal", bounds, juce::Justification::centred);
            return;
        }

        int numBins = fftSize / 2;
        float w = bounds.getWidth();
        float h = bounds.getHeight();

        float minFreq = 30.0f;
        float maxFreq = std::min (20000.0f, (float) sampleRate * 0.5f);
        float logMin = std::log2 (minFreq);
        float logMax = std::log2 (maxFreq);

        float minDB = -80.0f;
        float maxDB = 0.0f;

        juce::Path path;
        bool started = false;

        for (int px = 0; px < (int) w; ++px)
        {
            float normX = (float) px / w;
            float freq = std::pow (2.0f, logMin + normX * (logMax - logMin));
            int bin = juce::jlimit (1, numBins - 1,
                                    (int) (freq / (float) sampleRate * (float) fftSize));

            float dB = smoothedMagnitudes[static_cast<size_t> (bin)];
            float normY = juce::jlimit (0.0f, 1.0f, (dB - minDB) / (maxDB - minDB));
            float y = bounds.getBottom() - normY * h;

            if (! started)
            {
                path.startNewSubPath (bounds.getX() + (float) px, y);
                started = true;
            }
            else
            {
                path.lineTo (bounds.getX() + (float) px, y);
            }
        }

        auto fillPath = path;
        fillPath.lineTo (bounds.getRight(), bounds.getBottom());
        fillPath.lineTo (bounds.getX(), bounds.getBottom());
        fillPath.closeSubPath();

        g.setColour (spectrumColour.withAlpha (0.08f));
        g.fillPath (fillPath);

        g.setColour (spectrumColour.withAlpha (0.7f));
        g.strokePath (path, juce::PathStrokeType (1.2f,
                          juce::PathStrokeType::curved,
                          juce::PathStrokeType::rounded));
    }

private:
    AudioFIFO& fifo;
    int fftOrder;
    int fftSize;
    juce::dsp::FFT fft;
    juce::dsp::WindowingFunction<float> window;
    std::vector<float> fftData;
    std::vector<float> scratchBuffer;
    std::vector<float> smoothedMagnitudes;
    double sampleRate = 48000.0;
    bool isActive = false;
    bool hasData = false;

    void timerCallback() override
    {
        int pulled = fifo.pull (scratchBuffer.data(), fftSize);
        if (pulled < fftSize)
            return;

        hasData = true;

        std::fill (fftData.begin(), fftData.end(), 0.0f);
        std::copy (scratchBuffer.begin(),
                   scratchBuffer.begin() + fftSize,
                   fftData.begin());

        window.multiplyWithWindowingTable (fftData.data(), static_cast<size_t> (fftSize));
        fft.performFrequencyOnlyForwardTransform (fftData.data());

        int numBins = fftSize / 2;
        float smoothing = 0.7f;

        for (int i = 0; i < numBins; ++i)
        {
            float mag = fftData[static_cast<size_t> (i)] / (float) fftSize;
            float dB = (mag > 1e-10f) ? 20.0f * std::log10 (mag) : -100.0f;

            auto idx = static_cast<size_t> (i);
            smoothedMagnitudes[idx] = smoothedMagnitudes[idx] * smoothing
                                      + dB * (1.0f - smoothing);
        }

        repaint();
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (SpectrumView)
};
