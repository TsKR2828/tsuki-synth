#include "analyzer/PitchDetector.h"
#include "dsp/AudioFIFO.h"
#include "dsp/MidiNoteTracker.h"

#include <algorithm>
#include <cstdint>
#include <cmath>
#include <cstdio>
#include <vector>

namespace
{
int failures = 0;

#define CHECK(condition, message)                                      \
    do                                                                 \
    {                                                                  \
        if (condition)                                                 \
            std::printf ("[PASS] %s\n", message);                    \
        else                                                           \
        {                                                              \
            std::printf ("[FAIL] %s\n", message);                    \
            ++failures;                                                \
        }                                                              \
    } while (false)

std::vector<float> sineFor (double frequency, double sampleRate,
                            int samples, double phase = 0.0)
{
    std::vector<float> signal (static_cast<size_t> (samples));
    constexpr double twoPi = 6.283185307179586476925286766559;
    for (int i = 0; i < samples; ++i)
        signal[static_cast<size_t> (i)] = static_cast<float> (
            0.4 * std::sin (twoPi * frequency * i / sampleRate + phase));
    return signal;
}

std::vector<float> modalFor (double fundamental, double sampleRate, int samples,
                             const std::vector<double>& ratios,
                             const std::vector<double>& amplitudes)
{
    std::vector<float> signal (static_cast<size_t> (samples), 0.0f);
    constexpr double twoPi = 6.283185307179586476925286766559;
    for (size_t mode = 0; mode < ratios.size(); ++mode)
    {
        const double frequency = fundamental * ratios[mode];
        if (frequency >= sampleRate * 0.45)
            continue;
        for (int i = 0; i < samples; ++i)
        {
            const double time = i / sampleRate;
            signal[static_cast<size_t> (i)] += static_cast<float> (
                amplitudes[mode] * std::exp (-time / (1.2 - 0.12 * mode))
                * std::sin (twoPi * frequency * time + 0.19 * mode));
        }
    }
    return signal;
}

std::vector<float> noiseFor (int samples, uint32_t seed)
{
    std::vector<float> signal (static_cast<size_t> (samples));
    for (auto& sample : signal)
    {
        seed = seed * 1664525u + 1013904223u;
        sample = (static_cast<float> ((seed >> 8) & 0x00ffffffu)
                  / 8388608.0f - 1.0f) * 0.2f;
    }
    return signal;
}

void testLatestAudioFifo()
{
    AudioFIFO fifo (4);
    const float first[] = { 1, 2, 3, 4 };
    const float newer[] = { 5, 6 };
    float output[4] = {};
    fifo.push (first, 4);
    fifo.push (newer, 2);
    const int count = fifo.pull (output, 4);
    CHECK (count == 4 && output[0] == 3 && output[1] == 4
               && output[2] == 5 && output[3] == 6,
           "AudioFIFO overwrites stale history and preserves newest order");

    AudioFIFO latest (8);
    const float values[] = { 1, 2, 3, 4, 5, 6 };
    latest.push (values, 6);
    float tail[3] = {};
    CHECK (latest.pullLatest (tail, 3) == 3
               && tail[0] == 4 && tail[1] == 5 && tail[2] == 6
               && latest.getAvailable() == 0,
           "AudioFIFO pullLatest discards older unread analyser data");

    latest.push (values, 2);
    latest.clear();
    CHECK (latest.getAvailable() == 0,
           "AudioFIFO clear discards inactive analyser history");
}

void testMidiNoteTracker()
{
    MidiNoteTracker tracker;
    tracker.noteOn (0, 60);
    tracker.noteOn (1, 64);
    tracker.noteOff (1, 64);
    CHECK (tracker.selectedNote() == 60,
           "Releasing newest channel note selects the newest note still held");

    tracker.noteOn (0, 60); // retrigger same key
    tracker.noteOff (0, 60);
    CHECK (tracker.selectedNote() == 60 && tracker.isActive (0, 60),
           "Retriggered note remains active until matching note-offs arrive");
    tracker.noteOff (0, 60);
    CHECK (tracker.selectedNote() == -1,
           "Matching retrigger note-offs fully release the note");

    tracker.noteOn (2, 55);
    tracker.sustainPedal (2, true);
    tracker.noteOff (2, 55);
    CHECK (tracker.selectedNote() == 55,
           "Sustain pedal retains a released note on its MIDI channel");
    tracker.noteOn (2, 67);
    tracker.noteOff (2, 67);
    CHECK (tracker.selectedNote() == 67,
           "Most recent sustained note is selected");
    tracker.sustainPedal (2, false);
    CHECK (tracker.selectedNote() == -1,
           "Sustain-off releases all unheld notes on that channel");

    tracker.noteOn (3, 48);
    tracker.sustainPedal (3, true);
    tracker.allNotesOff (3); // CC123 follows note-off semantics
    CHECK (tracker.selectedNote() == 48,
           "CC123 respects an active sustain pedal");
    tracker.allSoundOff (3); // CC120 is immediate
    CHECK (tracker.selectedNote() == -1,
           "CC120 immediately clears held and sustained notes");

    tracker.noteOn (4, 72);
    tracker.sustainPedal (4, true);
    tracker.noteOff (4, 72);
    tracker.resetControllers (4); // CC121 releases pedal-held note
    CHECK (tracker.selectedNote() == -1,
           "CC121 resets sustain and releases unheld notes");
}

void testPitchRangeSweep()
{
    constexpr double rates[] = { 44100.0, 48000.0, 96000.0, 192000.0 };
    int supportedCases = 0;
    int refusedCases = 0;
    float worstCents = 0.0f;

    for (const double sampleRate : rates)
    {
        PitchDetector detector;
        detector.setSampleRate (sampleRate);
        for (int midi = 0; midi <= 127; ++midi)
        {
            if (! PitchDetector::isTargetSupported (midi))
            {
                const auto result = detector.analyse (nullptr, 0, midi);
                if (result.status != PitchDetector::Status::unsupportedTarget)
                {
                    std::printf ("[FAIL] range refusal sr=%.0f MIDI=%d\n",
                                 sampleRate, midi);
                    ++failures;
                }
                else
                {
                    ++refusedCases;
                }
                continue;
            }

            const int count = detector.requiredInputSamples (midi) + 16;
            const double frequency = PitchDetector::midiFrequency (midi);
            auto signal = sineFor (frequency, sampleRate, count,
                                   midi * 0.371);
            const auto result = detector.analyse (signal.data(), count, midi);
            worstCents = std::max (worstCents,
                                   std::abs (result.centsFromTarget));
            if (! result.isDetected()
                || std::abs (result.centsFromTarget) > 1.0f)
            {
                std::printf ("[FAIL] sweep sr=%.0f MIDI=%d status=%d cents=%.3f conf=%.3f\n",
                             sampleRate, midi, static_cast<int> (result.status),
                             result.centsFromTarget, result.confidence);
                ++failures;
            }
            else
            {
                ++supportedCases;
            }
        }
    }

    CHECK (supportedCases == 4 * (PitchDetector::maxSupportedMidi
                                  - PitchDetector::minSupportedMidi + 1),
           "PitchDetector measures every A0-C8 target at 44.1/48/96/192 kHz");
    CHECK (refusedCases == 4 * (128 - (PitchDetector::maxSupportedMidi
                                      - PitchDetector::minSupportedMidi + 1)),
           "PitchDetector explicitly refuses every target outside A0-C8");
    std::printf ("[INFO] pitch sweep worst error %.4f cents (%d measured, %d refused)\n",
                 worstCents, supportedCases, refusedCases);

    PitchDetector lowRate;
    lowRate.setSampleRate (8000.0);
    const int c8Samples = lowRate.requiredInputSamples (108);
    auto c8 = sineFor (PitchDetector::midiFrequency (108), 8000.0, c8Samples);
    CHECK (lowRate.analyse (c8.data(), c8Samples, 108).status
               == PitchDetector::Status::unsupportedTarget,
           "PitchDetector refuses targets whose search window exceeds Nyquist");
}

void testPitchIsMeasuredNotCopiedFromTarget()
{
    PitchDetector detector;
    detector.setSampleRate (48000.0);
    const int target = 69;
    const int count = detector.requiredInputSamples (target) + 16;

    bool shiftedOk = true;
    for (const double ratio : { 0.85, 1.15, 0.85 * 0.85 })
    {
        auto signal = sineFor (PitchDetector::midiFrequency (target) * ratio,
                               48000.0, count, 0.73);
        const auto result = detector.analyse (signal.data(), count, target);
        const float expectedCents = static_cast<float> (1200.0 * std::log2 (ratio));
        if (! result.isDetected()
            || std::abs (result.centsFromTarget - expectedCents) > 1.0f)
        {
            std::printf ("[FAIL] shifted pitch ratio=%.5f expected=%.2f measured=%.2f status=%d\n",
                         ratio, expectedCents, result.centsFromTarget,
                         static_cast<int> (result.status));
            ++failures;
            shiftedOk = false;
        }
    }
    CHECK (shiftedOk,
           "Audio estimator reports tension/glide offsets instead of MIDI target");

    auto octaveLow = sineFor (220.0, 48000.0, count);
    auto octaveHigh = sineFor (880.0, 48000.0, count);
    CHECK (! detector.analyse (octaveLow.data(), count, target).isDetected()
               && ! detector.analyse (octaveHigh.data(), count, target).isDetected(),
           "Target-aware detector refuses octave substitutions");

    std::vector<float> silence (static_cast<size_t> (count), 0.0f);
    CHECK (! detector.analyse (silence.data(), count, target).isDetected(),
           "PitchDetector never reports silence as a measured note");

    const auto tongue = modalFor (
        PitchDetector::midiFrequency (target) * 0.85, 48000.0, count,
        { 1.0, 2.756, 5.404, 8.933 }, { 1.0, 0.55, 0.30, 0.15 });
    const auto gong = modalFor (
        PitchDetector::midiFrequency (target) * 0.85 * 0.85, 48000.0, count,
        { 1.0, 1.730, 2.328, 2.892 }, { 1.0, 0.70, 0.50, 0.40 });
    const auto tongueResult = detector.analyse (tongue.data(), count, target);
    const auto gongResult = detector.analyse (gong.data(), count, target);
    CHECK (tongueResult.isDetected()
               && std::abs (tongueResult.centsFromTarget
                            - 1200.0f * std::log2 (0.85f)) < 2.0f,
           "Inharmonic tongue modes report the shifted audio fundamental");
    CHECK (gongResult.isDetected()
               && std::abs (gongResult.centsFromTarget
                            - 1200.0f * std::log2 (0.85f * 0.85f)) < 2.0f,
           "Inharmonic gong modes report combined tension/glide shift");
}

void testInharmonicRangeBoundaries()
{
    constexpr double rates[] = { 44100.0, 48000.0, 96000.0, 192000.0 };
    bool allDetected = true;
    float worstError = 0.0f;
    for (const double sampleRate : rates)
    {
        for (const int midi : { 21, 108 })
        {
            PitchDetector detector;
            detector.setSampleRate (sampleRate);
            const int count = detector.requiredInputSamples (midi) + 16;
            const double ratio = midi == 21 ? 0.85 * 0.85 : 1.15;
            const double fundamental = PitchDetector::midiFrequency (midi) * ratio;
            const float expected = static_cast<float> (1200.0 * std::log2 (ratio));

            const auto tongue = modalFor (
                fundamental, sampleRate, count,
                { 1.0, 2.756, 5.404, 8.933 },
                { 1.0, 0.55, 0.30, 0.15 });
            const auto gong = modalFor (
                fundamental, sampleRate, count,
                { 1.0, 1.730, 2.328, 2.892 },
                { 1.0, 0.70, 0.50, 0.40 });

            for (const auto* signal : { &tongue, &gong })
            {
                const auto result = detector.analyse (
                    signal->data(), count, midi);
                const float error = std::abs (result.centsFromTarget - expected);
                worstError = std::max (worstError, error);
                if (! result.isDetected() || error > 2.0f)
                {
                    allDetected = false;
                    std::printf ("[FAIL] modal boundary sr=%.0f MIDI=%d status=%d error=%.3fc conf=%.3f\n",
                                 sampleRate, midi,
                                 static_cast<int> (result.status), error,
                                 result.confidence);
                }
            }
        }
    }
    CHECK (allDetected,
           "Inharmonic tongue/gong fundamentals measure at A0 and C8 on all rates");
    std::printf ("[INFO] modal boundary worst error %.4f cents\n", worstError);
}

void testBroadbandNoiseIsUncertain()
{
    bool allRefused = true;
    for (const double sampleRate : { 44100.0, 192000.0 })
    {
        for (const int midi : { 21, 69, 108 })
        {
            PitchDetector detector;
            detector.setSampleRate (sampleRate);
            const int count = detector.requiredInputSamples (midi) + 16;
            for (uint32_t seed = 1; seed <= 64; ++seed)
            {
                const auto noise = noiseFor (count,
                                             seed + static_cast<uint32_t> (midi));
                if (detector.analyse (noise.data(), count, midi).isDetected())
                {
                    allRefused = false;
                    std::printf ("[FAIL] noise detected sr=%.0f MIDI=%d seed=%u\n",
                                 sampleRate, midi, seed);
                }
            }
        }
    }
    CHECK (allRefused,
           "Broadband noise is reported uncertain instead of as a pitch");
}
}

int main()
{
    std::printf ("TsukiSynth tuner regression tests\n");
    testLatestAudioFifo();
    testMidiNoteTracker();
    testPitchRangeSweep();
    testPitchIsMeasuredNotCopiedFromTarget();
    testInharmonicRangeBoundaries();
    testBroadbandNoiseIsUncertain();

    std::printf ("%s (%d failure%s)\n",
                 failures == 0 ? "PASS" : "FAIL", failures,
                 failures == 1 ? "" : "s");
    return failures == 0 ? 0 : 1;
}
