#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "../dsp/AudioFIFO.h"
#include "../TsukiLookAndFeel.h"
#include <atomic>
#include <cmath>
#include <vector>

class TunerView : public juce::Component, private juce::Timer
{
public:
    explicit TunerView (AudioFIFO& fifo)
        : fifo (fifo), pullBuffer (8192, 0.0f) {}

    ~TunerView() override { stopTimer(); }

    /** Wire processor atomics for synth-aware display. When the engine
     *  param equals 1 (Chromatic), TunerView shows the last noteOn MIDI
     *  note directly — NSDF is unreliable on inharmonic modal stacks. */
    void setSynthAwareSources (std::atomic<int>* lastMidi,
                               std::atomic<float>* engineParam) noexcept
    {
        pLastMidi    = lastMidi;
        pEngineParam = engineParam;
    }

    void setActive (bool active)
    {
        if (active == isActive)
            return;
        isActive = active;
        if (active)
        {
            startTimerHz (20);
        }
        else
        {
            stopTimer();
            hasSignal = false;
        }
        repaint();
    }

    bool getActive() const { return isActive; }
    void setSampleRate (double sr) { sampleRate = sr; }

    juce::Colour accentColour { Clr::gold };

    void paint (juce::Graphics& g) override
    {
        auto bounds = getLocalBounds().toFloat();

        if (! isActive || ! hasSignal)
        {
            g.setColour (Clr::textDim.withAlpha (0.3f));
            g.setFont (TsukiLookAndFeel::scaledFont (10.0f));
            const char* msg = synthAware ? "Awaiting note" : "No signal";
            g.drawText (msg, bounds, juce::Justification::centred);
            return;
        }

        // Synth-aware Chromatic layout: PLAYED label + note + target Hz, no cent bar
        if (synthAware)
        {
            auto content = bounds.reduced (8.0f, 0.0f);

            auto labelArea = content.removeFromLeft (content.getWidth() * 0.25f);
            g.setColour (Clr::textDim);
            g.setFont (TsukiLookAndFeel::scaledFont (9.0f));
            g.drawText ("PLAYED", labelArea, juce::Justification::centred);

            auto noteArea = content.removeFromLeft (content.getWidth() * 0.40f);
            g.setColour (accentColour);
            g.setFont (TsukiLookAndFeel::scaledFont (18.0f).boldened());
            g.drawText (currentNoteName, noteArea, juce::Justification::centred);

            g.setColour (Clr::text);
            g.setFont (TsukiLookAndFeel::scaledFont (11.0f));
            g.drawText (juce::String (detectedFreq, 1) + " Hz", content,
                        juce::Justification::centred);
            return;
        }

        auto barArea = bounds.removeFromBottom (14.0f).reduced (20.0f, 2.0f);
        auto content = bounds.reduced (8.0f, 0.0f);

        auto noteArea = content.removeFromLeft (content.getWidth() * 0.30f);
        g.setColour (accentColour);
        g.setFont (TsukiLookAndFeel::scaledFont (18.0f).boldened());
        g.drawText (currentNoteName, noteArea, juce::Justification::centred);

        auto freqArea = content.removeFromLeft (content.getWidth() * 0.50f);
        g.setColour (Clr::text);
        g.setFont (TsukiLookAndFeel::scaledFont (11.0f));
        g.drawText (juce::String (detectedFreq, 1) + " Hz", freqArea,
                    juce::Justification::centred);

        auto centColour = centColor();
        auto centStr = (centOffset >= 0.0f ? juce::String ("+") : juce::String())
                       + juce::String (centOffset, 1)
                       + juce::String (juce::CharPointer_UTF8 (" \xc2\xa2"));
        g.setColour (centColour);
        g.setFont (TsukiLookAndFeel::scaledFont (11.0f));
        g.drawText (centStr, content, juce::Justification::centred);

        float barH = 6.0f;
        float barY = barArea.getCentreY() - barH * 0.5f;
        float barW = barArea.getWidth();
        float barX = barArea.getX();

        g.setColour (Clr::knobTrack);
        g.fillRoundedRectangle (barX, barY, barW, barH, 2.0f);

        float cx = barX + barW * 0.5f;
        g.setColour (Clr::border);
        g.fillRect (cx - 0.5f, barY - 2.0f, 1.0f, barH + 4.0f);

        float dotPos = juce::jlimit (-50.0f, 50.0f, centOffset);
        float dotX = cx + (dotPos / 50.0f) * (barW * 0.45f);
        float dotR = 4.0f;
        g.setColour (centColour);
        g.fillEllipse (dotX - dotR, barY + barH * 0.5f - dotR,
                       dotR * 2.0f, dotR * 2.0f);
    }

private:
    AudioFIFO& fifo;
    double sampleRate = 44100.0;
    std::vector<float> pullBuffer;

    float detectedFreq = 0.0f;
    float centOffset   = 0.0f;
    float confidence   = 0.0f;
    int   nearestMidi  = -1;
    juce::String currentNoteName;
    bool hasSignal = false;
    bool isActive  = false;
    int  holdCounter = 0;
    static constexpr int holdTicks = 3;  // ~150ms @ 20Hz — short enough to avoid stale wrong notes

    // Synth-aware display sources (wired by Editor after construction)
    std::atomic<int>*   pLastMidi    = nullptr;
    std::atomic<float>* pEngineParam = nullptr;
    bool synthAware = false;

    juce::Colour centColor() const
    {
        float a = std::abs (centOffset);
        if (a <= 5.0f)  return Clr::chromatic;
        if (a <= 15.0f) return Clr::gold;
        return juce::Colour (0xffcc6666);
    }

    static juce::String midiToNoteName (int midi)
    {
        static const char* names[] = {
            "C","C#","D","D#","E","F","F#","G","G#","A","A#","B"
        };
        if (midi < 0 || midi > 127)
            return "?";
        return juce::String (names[midi % 12]) + juce::String (midi / 12 - 1);
    }

    void timerCallback() override
    {
        // Engine 1 = Chromatic → synth-aware display (NSDF unreliable on
        // inharmonic beam/plate modal stacks)
        const int engineIdx = pEngineParam ? (int) pEngineParam->load() : -1;
        const bool useSynthAware = (engineIdx == 1);

        if (useSynthAware != synthAware)
        {
            // Engine changed — reset display so no stale state leaks across modes
            synthAware = useSynthAware;
            hasSignal       = false;
            currentNoteName.clear();
            detectedFreq    = 0.0f;
            centOffset      = 0.0f;
            nearestMidi     = -1;
            holdCounter     = 0;
        }

        // Always drain the FIFO so the audio thread doesn't lap us
        int pulled = fifo.pull (pullBuffer.data(), (int) pullBuffer.size());

        if (synthAware)
        {
            const int midi = pLastMidi ? pLastMidi->load (std::memory_order_acquire) : -1;
            if (midi >= 0 && midi <= 127)
            {
                hasSignal       = true;
                nearestMidi     = midi;
                detectedFreq    = 440.0f * std::pow (2.0f, (float) (midi - 69) / 12.0f);
                centOffset      = 0.0f;
                currentNoteName = midiToNoteName (midi);
            }
            else
            {
                hasSignal = false;
                currentNoteName.clear();
            }
            repaint();
            return;
        }

        // ── NSDF branch (Cimbalom / FM Piano) ──
        if (pulled < 512)
        {
            decayHold();
            repaint();
            return;
        }

        float rms = 0.0f;
        for (int i = 0; i < pulled; ++i)
            rms += pullBuffer[(size_t) i] * pullBuffer[(size_t) i];
        rms = std::sqrt (rms / (float) pulled);

        if (rms < 0.02f)
        {
            decayHold();
            repaint();
            return;
        }

        float freq = detectPitch (pullBuffer.data(), pulled);
        if (freq >= 18.0f && freq < 10000.0f && confidence >= 0.45f)
        {
            hasSignal = true;
            holdCounter = holdTicks;
            detectedFreq = freq;
            float midiNote = 69.0f + 12.0f * std::log2 (freq / 440.0f);
            nearestMidi = juce::roundToInt (midiNote);
            centOffset = (midiNote - (float) nearestMidi) * 100.0f;
            currentNoteName = midiToNoteName (nearestMidi);
        }
        else
        {
            decayHold();
        }
        repaint();
    }

    void decayHold()
    {
        if (holdCounter > 0)
        {
            --holdCounter;
        }
        else if (hasSignal)
        {
            // Hold expired — clear stale state so no wrong note persists
            hasSignal = false;
            currentNoteName.clear();
            detectedFreq = 0.0f;
            centOffset   = 0.0f;
            nearestMidi  = -1;
        }
    }

    // ── NSDF pitch detection (McLeod-style) ──────────────────────
    float detectPitch (const float* data, int numSamples)
    {
        confidence = 0.0f;
        const int minLag = juce::jmax (2, (int) (sampleRate / 4000.0));
        const int maxLag = juce::jmin ((int) (sampleRate / 20.0),
                                       numSamples * 3 / 4);
        if (maxLag <= minLag)
            return 0.0f;

        // Compute NSDF from lag 2 so we can locate the zero-lag lobe boundary
        nsdfBuf.resize ((size_t) (maxLag + 1), 0.0f);

        for (int tau = 2; tau <= maxLag; ++tau)
        {
            float acf  = 0.0f;
            float norm = 0.0f;
            int N = numSamples - tau;
            for (int j = 0; j < N; ++j)
            {
                acf  += data[j] * data[j + tau];
                norm += data[j] * data[j] + data[j + tau] * data[j + tau];
            }
            nsdfBuf[(size_t) tau] = (norm > 1e-10f) ? (2.0f * acf / norm)
                                                     : 0.0f;
        }

        // Skip the zero-lag positive lobe: find first negative crossing
        int zeroLagEnd = -1;
        for (int tau = 2; tau <= maxLag; ++tau)
        {
            if (nsdfBuf[(size_t) tau] <= 0.0f)
            {
                zeroLagEnd = tau;
                break;
            }
        }
        if (zeroLagEnd < 0)
        {
            // No negative crossing — find first local minimum as zero-lag lobe end
            for (int tau = 3; tau < maxLag; ++tau)
            {
                if (nsdfBuf[(size_t) tau] < nsdfBuf[(size_t) (tau - 1)]
                    && nsdfBuf[(size_t) tau] < nsdfBuf[(size_t) (tau + 1)])
                {
                    zeroLagEnd = tau;
                    break;
                }
            }
            // Absolute safe fallback
            if (zeroLagEnd < 0)
                zeroLagEnd = juce::jmax (minLag, (int) (sampleRate / 2000.0));
        }

        int searchStart = juce::jmax (minLag, zeroLagEnd);

        // Collect peaks of positive lobes (after the zero-lag lobe)
        struct Peak { int lag; float val; };
        peakBuf.clear();
        bool inPos = false;
        float localMax = -1.0f;
        int   localLag = 0;

        for (int tau = searchStart; tau <= maxLag; ++tau)
        {
            if (nsdfBuf[(size_t) tau] > 0.0f)
            {
                if (! inPos) { inPos = true; localMax = -1.0f; }
                if (nsdfBuf[(size_t) tau] > localMax)
                {
                    localMax = nsdfBuf[(size_t) tau];
                    localLag = tau;
                }
            }
            else if (inPos)
            {
                peakBuf.push_back ({ localLag, localMax });
                inPos = false;
            }
        }
        if (inPos)
            peakBuf.push_back ({ localLag, localMax });

        if (peakBuf.empty())
            return 0.0f;

        float globalMax = 0.0f;
        for (const auto& p : peakBuf)
            globalMax = juce::jmax (globalMax, p.val);

        if (globalMax < 0.35f)
            return 0.0f;

        // First peak above 80 % of global max → fundamental
        float threshold = globalMax * 0.80f;
        int bestLag = 0;
        for (const auto& p : peakBuf)
        {
            if (p.val >= threshold)
            {
                bestLag = p.lag;
                confidence = p.val;
                break;
            }
        }
        if (bestLag == 0)
            return 0.0f;

        // Parabolic interpolation for sub-sample precision
        float refined = (float) bestLag;
        if (bestLag > 2 && bestLag < maxLag)
        {
            float a = nsdfBuf[(size_t) (bestLag - 1)];
            float b = nsdfBuf[(size_t) bestLag];
            float c = nsdfBuf[(size_t) (bestLag + 1)];
            float d = a - 2.0f * b + c;
            if (std::abs (d) > 1e-10f)
                refined = (float) bestLag + 0.5f * (a - c) / d;
        }

        return (float) (sampleRate / (double) refined);
    }

    std::vector<float> nsdfBuf;
    struct Peak { int lag; float val; };
    std::vector<Peak> peakBuf;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TunerView)
};
