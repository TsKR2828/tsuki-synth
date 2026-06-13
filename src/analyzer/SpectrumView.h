#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include <juce_dsp/juce_dsp.h>
#include "../dsp/AudioFIFO.h"
#include "../TsukiLookAndFeel.h"
#include <cmath>
#include <vector>
#include <algorithm>
#include <cstring>

class SpectrumView : public juce::Component, private juce::Timer
{
public:
    explicit SpectrumView (AudioFIFO& fifo)
        : fifo (fifo), pullBuf (4096, 0.0f)
    {
        rebuildFFT();
    }

    ~SpectrumView() override { stopTimer(); }

    void setActive (bool active)
    {
        if (active == isActive)
            return;
        isActive = active;
        if (active)
        {
            samplesAccumulated = 0;
            hasData = false;
            startTimerHz (30);
        }
        else
        {
            stopTimer();
            hasData = false;
        }
        repaint();
    }

    bool getActive() const { return isActive; }

    void setSampleRate (double sr) { sampleRate = sr; repaint(); }

    juce::Colour accentColour { Clr::gold };

    void paint (juce::Graphics& g) override
    {
        auto bounds = getLocalBounds().toFloat();

        if (! isActive || ! hasData)
        {
            g.setColour (Clr::textDim.withAlpha (0.3f));
            g.setFont (TsukiLookAndFeel::scaledFont (10.0f));
            g.drawText ("No signal", bounds, juce::Justification::centred);
        }
        else
        {
            drawSpectrum (g, bounds);
        }

        drawOverlay (g, bounds);
    }

    void mouseDown (const juce::MouseEvent& e) override
    {
        auto bounds = getLocalBounds().toFloat();
        float sx = bounds.getRight() - 136.0f;
        float sy = bounds.getBottom() - 16.0f;

        if (e.position.y >= sy && e.position.y <= sy + 14.0f)
        {
            float x = e.position.x;
            if      (x >= sx       && x < sx + 24.0f) changeFFTOrder (11);
            else if (x >= sx + 26  && x < sx + 50.0f) changeFFTOrder (12);
            else if (x >= sx + 52  && x < sx + 76.0f) changeFFTOrder (13);
        }
    }

private:
    AudioFIFO& fifo;
    double sampleRate = 44100.0;

    int  fftOrder = 11;
    int  fftSize  = 2048;
    std::unique_ptr<juce::dsp::FFT> fft;
    std::vector<float> fftData;
    std::vector<float> windowBuf;
    std::vector<float> windowCoeffs;
    std::vector<float> magnitudeDB;
    std::vector<float> pullBuf;
    int  samplesAccumulated = 0;
    bool hasData  = false;
    bool isActive = false;

    static constexpr float kMinFreq = 30.0f;
    static constexpr float kFloorDB = -72.0f;
    static constexpr float kCeilDB  = 0.0f;

    // ── FFT setup ────────────────────────────────────────────────
    void rebuildFFT()
    {
        fft = std::make_unique<juce::dsp::FFT> (fftOrder);
        fftData.assign ((size_t) fftSize * 2, 0.0f);
        windowBuf.assign ((size_t) fftSize, 0.0f);
        magnitudeDB.assign ((size_t) (fftSize / 2 + 1), kFloorDB);
        buildWindow();
        samplesAccumulated = 0;
        hasData = false;
    }

    void changeFFTOrder (int order)
    {
        if (order == fftOrder)
            return;
        fftOrder = order;
        fftSize  = 1 << order;
        rebuildFFT();
        repaint();
    }

    void buildWindow()
    {
        windowCoeffs.resize ((size_t) fftSize);
        const float k = juce::MathConstants<float>::twoPi / (float) (fftSize - 1);
        for (int i = 0; i < fftSize; ++i)
            windowCoeffs[(size_t) i] = 0.5f * (1.0f - std::cos (k * (float) i));
    }

    // ── Timer ────────────────────────────────────────────────────
    void timerCallback() override
    {
        int pulled = fifo.pull (pullBuf.data(), (int) pullBuf.size());
        if (pulled <= 0)
            return;

        int shift = juce::jmin (pulled, fftSize);
        if (shift < fftSize)
            std::memmove (windowBuf.data(),
                          windowBuf.data() + shift,
                          (size_t) (fftSize - shift) * sizeof (float));

        std::memcpy (windowBuf.data() + fftSize - shift,
                     pullBuf.data() + (pulled - shift),
                     (size_t) shift * sizeof (float));

        samplesAccumulated = juce::jmin (samplesAccumulated + pulled, fftSize);

        if (samplesAccumulated >= fftSize)
        {
            computeSpectrum();
            hasData = true;
        }
        repaint();
    }

    void computeSpectrum()
    {
        std::fill (fftData.begin(), fftData.end(), 0.0f);
        for (int i = 0; i < fftSize; ++i)
            fftData[(size_t) i] = windowBuf[(size_t) i]
                                * windowCoeffs[(size_t) i];

        fft->performFrequencyOnlyForwardTransform (fftData.data(), true);

        int numBins = fftSize / 2 + 1;
        float norm  = 2.0f / (float) fftSize;
        for (int i = 0; i < numBins; ++i)
        {
            float mag = fftData[(size_t) i] * norm;
            magnitudeDB[(size_t) i] = 20.0f * std::log10 (mag + 1e-10f);
        }
    }

    // ── Drawing ──────────────────────────────────────────────────
    float getBinDB (float binF) const
    {
        int numBins = fftSize / 2 + 1;
        int b0 = juce::jlimit (0, numBins - 1, (int) binF);
        int b1 = juce::jlimit (0, numBins - 1, b0 + 1);
        float t = binF - (float) b0;
        return magnitudeDB[(size_t) b0] * (1.0f - t)
             + magnitudeDB[(size_t) b1] * t;
    }

    void drawSpectrum (juce::Graphics& g,
                       juce::Rectangle<float> bounds) const
    {
        float maxFreq  = (float) (sampleRate * 0.5);
        float logMin   = std::log2 (kMinFreq);
        float logRange = std::log2 (maxFreq) - logMin;
        float dbRange  = kCeilDB - kFloorDB;
        int   w = juce::jmax (1, (int) bounds.getWidth());

        juce::Path stroke;
        bool started = false;

        for (int px = 0; px < w; ++px)
        {
            float freq = std::pow (2.0f, logMin + (float) px / (float) (w - 1)
                                                * logRange);
            float binF = freq * (float) fftSize / (float) sampleRate;
            float dB   = getBinDB (binF);
            float normY = juce::jlimit (0.0f, 1.0f,
                                        (dB - kFloorDB) / dbRange);
            float y = bounds.getBottom() - normY * bounds.getHeight();

            if (! started) { stroke.startNewSubPath (bounds.getX() + (float) px, y); started = true; }
            else             stroke.lineTo (bounds.getX() + (float) px, y);
        }

        // filled area
        juce::Path fill (stroke);
        fill.lineTo (bounds.getRight(), bounds.getBottom());
        fill.lineTo (bounds.getX(),     bounds.getBottom());
        fill.closeSubPath();
        g.setColour (accentColour.withAlpha (0.12f));
        g.fillPath (fill);

        g.setColour (accentColour.withAlpha (0.7f));
        g.strokePath (stroke, juce::PathStrokeType (
            1.2f, juce::PathStrokeType::curved,
            juce::PathStrokeType::rounded));
    }

    void drawOverlay (juce::Graphics& g,
                      juce::Rectangle<float> bounds) const
    {
        float sx = bounds.getRight() - 136.0f;
        float sy = bounds.getBottom() - 16.0f;

        g.setFont (TsukiLookAndFeel::scaledFont (7.5f).boldened());

        auto opt = [&] (float x, const char* txt, int ord)
        {
            bool on = (fftOrder == ord);
            g.setColour (on ? accentColour : Clr::textDim.withAlpha (0.5f));
            g.drawText (txt, (int) x, (int) sy, 22, 14,
                        juce::Justification::centred);
        };

        opt (sx,       "2K", 11);
        opt (sx + 26,  "4K", 12);
        opt (sx + 52,  "8K", 13);

        float res = (float) (sampleRate / (double) fftSize);
        g.setColour (Clr::textDim.withAlpha (0.4f));
        g.setFont (TsukiLookAndFeel::scaledFont (7.0f));
        g.drawText (juce::String (res, 1) + " Hz/bin",
                    (int) (sx + 76), (int) sy, 64, 14,
                    juce::Justification::centredLeft);
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (SpectrumView)
};
