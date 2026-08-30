// K-04 regression: SpectrumView's pixel -> frequency mapping must stay finite
// at the 1px-wide boundary, and must stay bit-identical to the pre-fix mapping
// for every ordinary width.
//
// Before the fix drawSpectrum() computed  px / (float) (w - 1)  after clamping
// w to at least 1, so a 1px-wide view divided 0 by 0 and fed NaN into the bin
// lookup and the juce::Path coordinates. The production code now routes that
// arithmetic through SpectrumView::frequencyForPixel(), which this test calls
// directly -- same function, so the test cannot drift from what paints.

#include "analyzer/SpectrumView.h"

#include <cmath>
#include <cstdio>

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

// Mirrors SpectrumView's private kMinFreq. Kept as a literal on purpose: if
// somebody changes the constant, this test's absolute expectations should fail
// loudly rather than silently follow the new value.
constexpr float kMinFreqExpected = 30.0f;
constexpr double kSampleRate = 48000.0;

// The exact expression drawSpectrum() used before the K-04 fix.
float legacyFrequencyForPixel (int px, int width, double sampleRate)
{
    const float maxFreq  = (float) (sampleRate * 0.5);
    const float logMin   = std::log2 (kMinFreqExpected);
    const float logRange = std::log2 (maxFreq) - logMin;
    return std::pow (2.0f, logMin + (float) px / (float) (width - 1) * logRange);
}

void testOnePixelWideIsFinite()
{
    const float freq = SpectrumView::frequencyForPixel (0, 1, kSampleRate);

    CHECK (std::isfinite (freq),
           "w == 1 produces a finite frequency (K-04: was 0/0 -> NaN)");
    CHECK (! std::isnan (freq),
           "w == 1 produces a non-NaN frequency");
    CHECK (std::abs (freq - kMinFreqExpected) < 1.0e-3f,
           "w == 1 maps its single column to kMinFreq (30 Hz)");

    // Guard the pre-fix behaviour explicitly, so this test would have caught it.
    CHECK (std::isnan (legacyFrequencyForPixel (0, 1, kSampleRate)),
           "the pre-fix expression really did produce NaN at w == 1 "
           "(this test is meaningful)");
}

void testZeroAndNegativeWidthStayFinite()
{
    // drawSpectrum() clamps to w >= 1 before calling, but the helper is public
    // and must not hand NaN to any other caller either.
    CHECK (std::isfinite (SpectrumView::frequencyForPixel (0, 0, kSampleRate)),
           "w == 0 produces a finite frequency");
    CHECK (std::isfinite (SpectrumView::frequencyForPixel (0, -8, kSampleRate)),
           "negative width produces a finite frequency");
}

void testOrdinaryWidthsAreBitIdenticalToLegacy()
{
    bool allIdentical = true;
    for (int width : { 2, 3, 17, 200, 640, 1024 })
        for (int px = 0; px < width; ++px)
            if (SpectrumView::frequencyForPixel (px, width, kSampleRate)
                != legacyFrequencyForPixel (px, width, kSampleRate))
                allIdentical = false;

    CHECK (allIdentical,
           "every w >= 2 mapping is bit-identical to the pre-fix expression");
}

void testEndpointsAndMonotonicity()
{
    constexpr int width = 512;
    const float first = SpectrumView::frequencyForPixel (0, width, kSampleRate);
    const float last  = SpectrumView::frequencyForPixel (width - 1, width,
                                                         kSampleRate);

    CHECK (std::abs (first - kMinFreqExpected) < 1.0e-3f,
           "px 0 maps to kMinFreq (30 Hz)");
    CHECK (std::abs (last - (float) (kSampleRate * 0.5)) < 1.0f,
           "the last pixel maps to Nyquist");

    bool monotonic = true;
    float previous = -1.0f;
    for (int px = 0; px < width; ++px)
    {
        const float freq = SpectrumView::frequencyForPixel (px, width,
                                                            kSampleRate);
        if (! std::isfinite (freq) || freq <= previous)
            monotonic = false;
        previous = freq;
    }
    CHECK (monotonic, "the mapping is finite and strictly increasing across px");
}

void testNarrowWidthSweepIsAllFinite()
{
    bool allFinite = true;
    for (int width = 1; width <= 64; ++width)
        for (int px = 0; px < width; ++px)
            if (! std::isfinite (SpectrumView::frequencyForPixel (px, width,
                                                                  kSampleRate)))
                allFinite = false;

    CHECK (allFinite, "widths 1..64 produce finite frequencies at every pixel");
}

void testOtherSampleRatesStayFinite()
{
    bool allFinite = true;
    for (double sampleRate : { 44100.0, 48000.0, 88200.0, 96000.0, 192000.0 })
        for (int width : { 1, 2, 640 })
            for (int px = 0; px < width; ++px)
                if (! std::isfinite (SpectrumView::frequencyForPixel (px, width,
                                                                      sampleRate)))
                    allFinite = false;

    CHECK (allFinite,
           "every contract sample rate stays finite, including at w == 1");
}
}

int main()
{
    std::printf ("TsukiSynth SpectrumView regression tests (K-04)\n");
    testOnePixelWideIsFinite();
    testZeroAndNegativeWidthStayFinite();
    testOrdinaryWidthsAreBitIdenticalToLegacy();
    testEndpointsAndMonotonicity();
    testNarrowWidthSweepIsAllFinite();
    testOtherSampleRatesStayFinite();

    std::printf ("%s (%d failure%s)\n",
                 failures == 0 ? "PASS" : "FAIL", failures,
                 failures == 1 ? "" : "s");
    return failures == 0 ? 0 : 1;
}
