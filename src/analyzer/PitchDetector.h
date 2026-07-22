#pragma once

#include <algorithm>
#include <array>
#include <cmath>

/**
 * Bounded, target-aware fundamental estimator for the synth tuner.
 *
 * The synth already knows which MIDI note is being played. Restricting the
 * search to +/-700 cents around that target makes an octave substitution
 * impossible while still covering every current tension/glide control. The
 * estimator measures the dry audio; the target only bounds the search.
 *
 * Work is bounded by kMaxAnalysisSamples and a fixed frequency grid. Storage
 * is fixed-size, so analyse() performs no allocation. It is suitable for a UI
 * timer and replaces the former O(N^2) NSDF scan.
 */
class PitchDetector
{
public:
    static constexpr int minSupportedMidi = 21;   // A0
    static constexpr int maxSupportedMidi = 108;  // C8
    static constexpr float searchCents = 700.0f;

    enum class Status
    {
        detected,
        unsupportedTarget,
        needMoreData,
        noSignal,
        lowConfidence
    };

    struct Result
    {
        Status status = Status::noSignal;
        float frequency = 0.0f;
        float centsFromTarget = 0.0f;
        float confidence = 0.0f;
        float rms = 0.0f;

        bool isDetected() const noexcept { return status == Status::detected; }
    };

    void setSampleRate (double newSampleRate) noexcept
    {
        sampleRate = newSampleRate > 0.0 ? newSampleRate : 44100.0;
    }

    static double midiFrequency (int midi) noexcept
    {
        return 440.0 * std::pow (2.0, static_cast<double> (midi - 69) / 12.0);
    }

    int requiredInputSamples (int targetMidi) const noexcept
    {
        if (! isTargetSupported (targetMidi))
            return 0;

        const double target = midiFrequency (targetMidi);
        const double minSearchHz = target * std::pow (2.0, -searchCents / 1200.0);
        // Six cycles provide stable low-note discrimination in inharmonic
        // modal mixtures. A 50 ms floor
        // improves cents accuracy at the high end without unbounded history.
        const double seconds = std::min (0.34, std::max (0.05, 6.0 / minSearchHz));
        return static_cast<int> (std::ceil (seconds * sampleRate));
    }

    Result analyse (const float* input, int numSamples, int targetMidi) noexcept
    {
        Result result;
        if (! isTargetSupported (targetMidi))
        {
            result.status = Status::unsupportedTarget;
            return result;
        }

        const int required = requiredInputSamples (targetMidi);
        if (input == nullptr || numSamples < required || required <= 0)
        {
            result.status = Status::needMoreData;
            return result;
        }

        const double target = midiFrequency (targetMidi);
        const double maxSearchHz = target * std::pow (2.0, searchCents / 1200.0);
        if (maxSearchHz >= sampleRate * 0.45)
        {
            result.status = Status::unsupportedTarget;
            return result;
        }

        // Average adjacent source samples while decimating. Keeping at least
        // sixteen samples per highest searched cycle bounds both aliasing and
        // CPU. The block average acts as a simple anti-alias filter.
        int stride = std::max (1, static_cast<int> (
            std::floor (sampleRate / (16.0 * maxSearchHz))));
        stride = std::max (stride,
                           static_cast<int> (std::ceil (
                               static_cast<double> (required) / kMaxAnalysisSamples)));

        const float* source = input + (numSamples - required);
        analysisCount = std::min (kMaxAnalysisSamples, required / stride);
        if (analysisCount < 32)
        {
            result.status = Status::needMoreData;
            return result;
        }

        double sumSquares = 0.0;
        double mean = 0.0;
        for (int i = 0; i < analysisCount; ++i)
        {
            double block = 0.0;
            for (int j = 0; j < stride; ++j)
                block += source[i * stride + j];
            const float value = static_cast<float> (block / stride);
            samples[static_cast<size_t> (i)] = value;
            mean += value;
            sumSquares += static_cast<double> (value) * value;
        }

        mean /= analysisCount;
        result.rms = static_cast<float> (std::sqrt (
            std::max (0.0, sumSquares / analysisCount - mean * mean)));
        if (result.rms < 1.0e-6f) // about -120 dBFS; confidence rejects noise
        {
            result.status = Status::noSignal;
            return result;
        }

        weightedEnergy = 0.0;
        for (int i = 0; i < analysisCount; ++i)
        {
            const double phase = static_cast<double> (i)
                               / static_cast<double> (analysisCount - 1);
            const double w = 0.5 - 0.5 * std::cos (twoPi * phase);
            centred[static_cast<size_t> (i)] =
                static_cast<float> (samples[static_cast<size_t> (i)] - mean);
            weights[static_cast<size_t> (i)] = static_cast<float> (w);
            const double y = centred[static_cast<size_t> (i)] * w;
            weightedEnergy += y * y;
        }

        effectiveSampleRate = sampleRate / stride;
        if (weightedEnergy <= 1.0e-20)
        {
            result.status = Status::noSignal;
            return result;
        }

        float bestCents = -searchCents;
        double bestScore = -1.0;
        for (int cents = -700; cents <= 700; cents += 10)
            consider (target, static_cast<float> (cents), bestCents, bestScore);

        const float refineStart = std::max (-searchCents, bestCents - 12.0f);
        const float refineEnd   = std::min ( searchCents, bestCents + 12.0f);
        bestScore = -1.0;
        for (float cents = refineStart; cents <= refineEnd + 0.01f; cents += 1.0f)
            consider (target, cents, bestCents, bestScore);

        // Parabolic interpolation of the one-cent grid maximum.
        if (bestCents > -searchCents + 1.0f
            && bestCents < searchCents - 1.0f)
        {
            const double left  = scoreFrequency (
                target * std::pow (2.0, (bestCents - 1.0f) / 1200.0));
            const double mid   = scoreFrequency (
                target * std::pow (2.0, bestCents / 1200.0));
            const double right = scoreFrequency (
                target * std::pow (2.0, (bestCents + 1.0f) / 1200.0));
            const double denominator = left - 2.0 * mid + right;
            if (std::abs (denominator) > 1.0e-12)
            {
                const double offset = std::clamp (
                    0.5 * (left - right) / denominator, -1.0, 1.0);
                bestCents += static_cast<float> (offset);
                bestScore = scoreFrequency (
                    target * std::pow (2.0, bestCents / 1200.0));
            }
        }

        result.centsFromTarget = bestCents;
        result.frequency = static_cast<float> (
            target * std::pow (2.0, bestCents / 1200.0));
        result.confidence = static_cast<float> (
            std::clamp (bestScore, 0.0, 1.0));

        // A maximum on the search boundary means the actual tone is not
        // contained by the measurement window. Never present it as a pitch.
        if (std::abs (bestCents) >= searchCents - 2.0f
            || result.confidence < minimumConfidence)
        {
            result.status = Status::lowConfidence;
            result.frequency = 0.0f;
            return result;
        }

        result.status = Status::detected;
        return result;
    }

    static bool isTargetSupported (int midi) noexcept
    {
        return midi >= minSupportedMidi && midi <= maxSupportedMidi;
    }

    static bool isTargetSupportedAtSampleRate (int midi,
                                                double sampleRate) noexcept
    {
        if (! isTargetSupported (midi) || sampleRate <= 0.0)
            return false;
        const double maxSearchHz = midiFrequency (midi)
                                 * std::pow (2.0, searchCents / 1200.0);
        return maxSearchHz < sampleRate * 0.45;
    }

private:
    static constexpr int kMaxAnalysisSamples = 4096;
    static constexpr double twoPi = 6.283185307179586476925286766559;
    // At the A0 decimation/window size, broadband-noise maxima can reach about
    // 0.08 across the full search grid. Keep a clear margin above that floor.
    static constexpr float minimumConfidence = 0.12f;

    void consider (double target, float cents,
                   float& bestCents, double& bestScore) const noexcept
    {
        const double frequency = target * std::pow (2.0, cents / 1200.0);
        const double score = scoreFrequency (frequency);
        if (score > bestScore)
        {
            bestScore = score;
            bestCents = cents;
        }
    }

    double scoreFrequency (double frequency) const noexcept
    {
        const double angle = twoPi * frequency / effectiveSampleRate;
        const double cosStep = std::cos (angle);
        const double sinStep = std::sin (angle);
        double cosine = 1.0;
        double sine = 0.0;
        double yc = 0.0, ys = 0.0;
        double cc = 0.0, ss = 0.0, cs = 0.0;

        for (int i = 0; i < analysisCount; ++i)
        {
            const double w = weights[static_cast<size_t> (i)];
            const double y = centred[static_cast<size_t> (i)] * w;
            const double bc = w * cosine;
            const double bs = w * sine;
            yc += y * bc;
            ys += y * bs;
            cc += bc * bc;
            ss += bs * bs;
            cs += bc * bs;

            const double nextCosine = cosine * cosStep - sine * sinStep;
            sine = sine * cosStep + cosine * sinStep;
            cosine = nextCosine;
        }

        const double determinant = cc * ss - cs * cs;
        if (determinant <= 1.0e-20)
            return 0.0;

        const double explained = (ss * yc * yc - 2.0 * cs * yc * ys
                                  + cc * ys * ys) / determinant;
        return std::clamp (explained / weightedEnergy, 0.0, 1.0);
    }

    double sampleRate = 44100.0;
    double effectiveSampleRate = 44100.0;
    double weightedEnergy = 0.0;
    int analysisCount = 0;
    std::array<float, kMaxAnalysisSamples> samples {};
    std::array<float, kMaxAnalysisSamples> centred {};
    std::array<float, kMaxAnalysisSamples> weights {};
};
