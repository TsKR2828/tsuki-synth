#pragma once

#include <juce_gui_basics/juce_gui_basics.h>
#include "../dsp/AudioFIFO.h"
#include "../TsukiLookAndFeel.h"
#include "PitchDetector.h"
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstring>
#include <vector>

class TunerView : public juce::Component, private juce::Timer
{
public:
    explicit TunerView (AudioFIFO& sourceFifo)
        : fifo (sourceFifo), pullBuffer (historyCapacity, 0.0f),
          historyBuffer (historyCapacity, 0.0f)
    {
        detector.setSampleRate (sampleRate);
    }

    ~TunerView() override { stopTimer(); }

    /** The MIDI note is a labelled reference; pitch always comes from audio. */
    void setSynthAwareSources (std::atomic<int>* lastMidi,
                               std::atomic<float>* engineParam) noexcept
    {
        pLastMidi = lastMidi;
        pEngineParam = engineParam;
    }

    void setActive (bool active)
    {
        if (active == isActive)
            return;

        isActive = active;
        fifo.clear();
        clearHistory();
        clearMeasurement();
        targetMidi = -1;
        lastEngine = -1;

        if (active)
            startTimerHz (20);
        else
            stopTimer();
        repaint();
    }

    bool getActive() const noexcept { return isActive; }

    void setSampleRate (double sr)
    {
        sampleRate = sr > 0.0 ? sr : 44100.0;
        detector.setSampleRate (sampleRate);
        fifo.clear();
        clearHistory();
        clearMeasurement();
    }

    juce::Colour accentColour { Clr::gold };

    void paint (juce::Graphics& g) override
    {
        auto bounds = getLocalBounds().toFloat();
        if (! isActive)
        {
            drawCentredStatus (g, bounds, "Tuner inactive");
            return;
        }

        if (targetMidi < 0)
        {
            drawCentredStatus (g, bounds, "Awaiting note");
            return;
        }

        auto content = bounds.reduced (6.0f, 1.0f);
        auto statusRow = content.removeFromBottom (11.0f);
        auto targetRow = content.removeFromTop (content.getHeight() * 0.46f);
        auto measuredRow = content;

        drawLabel (g, targetRow.removeFromLeft (50.0f), "TARGET");
        g.setColour (accentColour);
        g.setFont (TsukiLookAndFeel::scaledFont (14.0f).boldened());
        g.drawText (midiToNoteName (targetMidi),
                    targetRow.removeFromLeft (42.0f),
                    juce::Justification::centredLeft);
        g.setColour (Clr::text);
        g.setFont (TsukiLookAndFeel::scaledFont (10.0f));
        g.drawText (juce::String (targetFrequency, 2) + " Hz", targetRow,
                    juce::Justification::centredLeft);

        drawLabel (g, measuredRow.removeFromLeft (50.0f), "MEASURED");
        if (hasSignal)
        {
            g.setColour (Clr::text);
            g.setFont (TsukiLookAndFeel::scaledFont (13.0f).boldened());
            g.drawText (midiToNoteName (nearestMidi),
                        measuredRow.removeFromLeft (42.0f),
                        juce::Justification::centredLeft);

            g.setFont (TsukiLookAndFeel::scaledFont (10.0f));
            g.drawText (juce::String (detectedFrequency, 2) + " Hz",
                        measuredRow.removeFromLeft (76.0f),
                        juce::Justification::centredLeft);

            const auto delta = (centsFromTarget >= 0.0f ? juce::String ("+")
                                                        : juce::String())
                             + juce::String (centsFromTarget, 1)
                             + juce::String (juce::CharPointer_UTF8 (" \xc2\xa2"));
            g.setColour (centColour());
            g.drawText (delta, measuredRow,
                        juce::Justification::centredRight);

            g.setColour (Clr::textDim.withAlpha (0.75f));
            g.setFont (TsukiLookAndFeel::scaledFont (8.0f));
            g.drawText ("audio confidence "
                            + juce::String (juce::roundToInt (confidence * 100.0f))
                            + "%",
                        statusRow, juce::Justification::centred);
        }
        else
        {
            g.setColour (Clr::textDim.withAlpha (0.75f));
            g.setFont (TsukiLookAndFeel::scaledFont (9.0f));
            g.drawText (measurementStatus, measuredRow,
                        juce::Justification::centredLeft);

            g.setColour (Clr::textDim.withAlpha (0.55f));
            g.setFont (TsukiLookAndFeel::scaledFont (8.0f));
            g.drawText ("Supported: A0-C8 at 44.1-192 kHz", statusRow,
                        juce::Justification::centred);
        }
    }

private:
    static constexpr int historyCapacity = 65536;

    AudioFIFO& fifo;
    double sampleRate = 44100.0;
    std::vector<float> pullBuffer;
    std::vector<float> historyBuffer;
    int historySize = 0;
    PitchDetector detector;

    float targetFrequency = 0.0f;
    float detectedFrequency = 0.0f;
    float centsFromTarget = 0.0f;
    float confidence = 0.0f;
    int targetMidi = -1;
    int nearestMidi = -1;
    int lastEngine = -1;
    bool hasSignal = false;
    bool isActive = false;
    juce::String measurementStatus { "Measuring..." };

    std::atomic<int>* pLastMidi = nullptr;
    std::atomic<float>* pEngineParam = nullptr;

    void timerCallback() override
    {
        const int engine = pEngineParam != nullptr
                               ? static_cast<int> (pEngineParam->load (
                                     std::memory_order_acquire))
                               : -1;
        const int midi = pLastMidi != nullptr
                             ? pLastMidi->load (std::memory_order_acquire)
                             : -1;

        if (engine != lastEngine || midi != targetMidi)
        {
            lastEngine = engine;
            targetMidi = midi;
            targetFrequency = (midi >= 0 && midi <= 127)
                                  ? static_cast<float> (
                                        PitchDetector::midiFrequency (midi))
                                  : 0.0f;
            clearHistory();
            clearMeasurement();
        }

        // Consume only the newest FIFO snapshot. When no target is active we
        // deliberately discard audio, preventing a new note from analysing an
        // old engine tail or audio accumulated while the tuner was hidden.
        const int pulled = fifo.pullLatest (pullBuffer.data(),
                                            static_cast<int> (pullBuffer.size()));
        if (targetMidi < 0 || targetMidi > 127)
        {
            clearHistory();
            measurementStatus = "Awaiting note";
            repaint();
            return;
        }

        if (! PitchDetector::isTargetSupportedAtSampleRate (targetMidi,
                                                             sampleRate)
            || detector.requiredInputSamples (targetMidi) > historyCapacity)
        {
            clearHistory();
            clearMeasurement();
            measurementStatus = "Out of reliable range";
            repaint();
            return;
        }

        appendHistory (pullBuffer.data(), pulled);
        const auto result = detector.analyse (historyBuffer.data(), historySize,
                                              targetMidi);
        if (result.isDetected())
        {
            hasSignal = true;
            detectedFrequency = result.frequency;
            centsFromTarget = result.centsFromTarget;
            confidence = result.confidence;
            const float midiValue = 69.0f
                + 12.0f * std::log2 (detectedFrequency / 440.0f);
            nearestMidi = juce::jlimit (0, 127, juce::roundToInt (midiValue));
            measurementStatus.clear();
        }
        else
        {
            clearMeasurement();
            switch (result.status)
            {
                case PitchDetector::Status::needMoreData:
                    measurementStatus = "Collecting audio...";
                    break;
                case PitchDetector::Status::noSignal:
                    measurementStatus = "No measurable signal";
                    break;
                case PitchDetector::Status::lowConfidence:
                    measurementStatus = "Uncertain - no pitch shown";
                    break;
                case PitchDetector::Status::unsupportedTarget:
                    measurementStatus = "Out of reliable range";
                    break;
                case PitchDetector::Status::detected:
                    break;
            }
        }
        repaint();
    }

    void appendHistory (const float* data, int count) noexcept
    {
        if (data == nullptr || count <= 0)
            return;

        const int capacity = static_cast<int> (historyBuffer.size());
        if (count >= capacity)
        {
            std::copy (data + count - capacity, data + count,
                       historyBuffer.begin());
            historySize = capacity;
            return;
        }

        const int overflow = std::max (0, historySize + count - capacity);
        if (overflow > 0)
        {
            std::memmove (historyBuffer.data(),
                          historyBuffer.data() + overflow,
                          static_cast<size_t> (historySize - overflow)
                              * sizeof (float));
            historySize -= overflow;
        }

        std::copy (data, data + count, historyBuffer.begin() + historySize);
        historySize += count;
    }

    void clearHistory() noexcept { historySize = 0; }

    void clearMeasurement()
    {
        hasSignal = false;
        detectedFrequency = 0.0f;
        centsFromTarget = 0.0f;
        confidence = 0.0f;
        nearestMidi = -1;
        measurementStatus = "Measuring...";
    }

    void drawCentredStatus (juce::Graphics& g, juce::Rectangle<float> area,
                            const juce::String& text) const
    {
        g.setColour (Clr::textDim.withAlpha (0.45f));
        g.setFont (TsukiLookAndFeel::scaledFont (10.0f));
        g.drawText (text, area, juce::Justification::centred);
    }

    static void drawLabel (juce::Graphics& g, juce::Rectangle<float> area,
                           const juce::String& text)
    {
        g.setColour (Clr::textDim);
        g.setFont (TsukiLookAndFeel::scaledFont (8.0f));
        g.drawText (text, area, juce::Justification::centredLeft);
    }

    juce::Colour centColour() const
    {
        const float distance = std::abs (centsFromTarget);
        if (distance <= 5.0f)  return Clr::chromatic;
        if (distance <= 15.0f) return Clr::gold;
        return juce::Colour (0xffcc6666);
    }

    static juce::String midiToNoteName (int midi)
    {
        static const char* names[] = {
            "C", "C#", "D", "D#", "E", "F",
            "F#", "G", "G#", "A", "A#", "B"
        };
        if (midi < 0 || midi > 127)
            return "?";
        return juce::String (names[midi % 12])
             + juce::String (midi / 12 - 1);
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TunerView)
};
