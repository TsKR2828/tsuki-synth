#include "physics/BeamModel.h"
#include "physics/PlateModel.h"
#include "physics/StringModel.h"
#include "physics/HammerImpulse.h"
#include "engines/ChromaticEngine.h"
#include "dsp/NoiseGen.h"
#include "dsp/EffectsChain.h"
#include "effects/EffectChain.h"
#include "effects/StereoDelay.h"
#include <atomic>
#include <cmath>
#include <iostream>

namespace
{
int failures = 0;

#define CHECK(condition, message) do { \
    if (condition) std::cout << "[PASS] " << message << '\n'; \
    else { std::cout << "[FAIL] " << message << '\n'; ++failures; } \
} while (false)

MaterialDB::Material steel()
{
    MaterialDB::Material material;
    material.displayName = "Steel";
    material.density = 7800.0f;
    material.youngsModulus = 200.0e9f;
    material.poissonRatio = 0.29f;
    material.damping.alpha = 0.0238f;
    material.damping.beta_air = 1.2e-7f;
    material.damping.gamma_radiation = 2.0e-5f;
    return material;
}

void testBeamBoundaryAndGeometry()
{
    const auto material = steel();
    BeamModel::Params params;
    params.strikePosition = 0.0f;
    params.numModes = 8;
    auto fixed = BeamModel::calculateModes (params, material);
    bool fixedNode = ! fixed.empty();
    for (const auto& mode : fixed)
        fixedNode = fixedNode && std::abs (mode.amplitude) < 1.0e-6f;
    CHECK (fixedNode, "Cantilever analytic mode shapes have a node at the fixed end");

    params.strikePosition = 1.0f;
    auto freeEnd = BeamModel::calculateModes (params, material);
    const double cantileverRatio = freeEnd[1].frequency / freeEnd[0].frequency;
    CHECK (std::abs (cantileverRatio - 6.267f) < 0.01f,
           "Tongue default uses fixed-free eigenvalue ratios");
    CHECK (std::abs (freeEnd[0].amplitude - 1.0f) < 0.01f,
           "Cantilever free endpoint is not incorrectly forced to zero");

    params.boundary = BeamModel::Boundary::FreeFree;
    auto suspended = BeamModel::calculateModes (params, material);
    const double freeFreeRatio = suspended[1].frequency / suspended[0].frequency;
    CHECK (std::abs (freeFreeRatio - 2.757f) < 0.01f,
           "Explicit free-free beam retains its distinct modal ratios");

    params.boundary = BeamModel::Boundary::Cantilever;
    params.width = 0.01f;
    auto narrow = BeamModel::calculateModes (params, material);
    params.width = 0.04f;
    auto wide = BeamModel::calculateModes (params, material);
    CHECK (std::abs (narrow[0].frequency / wide[0].frequency - 1.0f) < 1.0e-5f,
           "Ideal beam width correctly cancels from eigenfrequency");
    CHECK (std::abs (narrow[0].amplitude / wide[0].amplitude - 2.0f) < 0.02f,
           "Beam width remains observable through modal mass");
}

void testPlateModesAndPoisson()
{
    auto material = steel();
    PlateModel::Params params;
    params.freeEdge = false;
    params.numModes = 12;
    params.strikePosition = 0.0f;
    auto centre = PlateModel::calculateModes (params, material);
    CHECK (centre.size() >= 4 && centre[1].amplitude < 1.0e-6f
           && centre[2].amplitude < 1.0e-6f && centre[0].amplitude > 0.5f,
           "Circular-plate centre strike suppresses m>0 modes without a floor");

    params.strikePosition = 1.0f;
    auto edge = PlateModel::calculateModes (params, material);
    bool clampedEdgeNode = ! edge.empty();
    for (const auto& mode : edge)
        clampedEdgeNode = clampedEdgeNode && std::abs (mode.amplitude) < 2.0e-5f;
    CHECK (clampedEdgeNode, "Clamped plate eigenfunctions vanish at the edge");

    params.freeEdge = true;
    params.numModes = 7;
    params.strikePosition = 0.0f;
    auto freeCentre = PlateModel::calculateModes (params, material);
    CHECK (freeCentre.size() == 7 && freeCentre[0].amplitude < 1.0e-6f
           && freeCentre[1].amplitude > 0.5f,
           "Free plate preserves centre nodes and the axisymmetric branch");

    auto lowNu = material;
    auto highNu = material;
    lowNu.poissonRatio = 0.20f;
    highNu.poissonRatio = 0.49f;
    auto lowModes = PlateModel::calculateModes (params, lowNu);
    auto highModes = PlateModel::calculateModes (params, highNu);
    const float lowRatio = lowModes[1].frequency / lowModes[0].frequency;
    const float highRatio = highModes[1].frequency / highModes[0].frequency;
    CHECK (std::abs (lowRatio - highRatio) > 0.3f,
           "Free-edge eigenvalues depend on the material Poisson ratio");
}

void testGeometryFrequencyModeAndDamping()
{
    const auto material = steel();
    ChromaticParams params;
    params.subEngine = ChromaticSubEngine::TongueDrum;
    params.tongueLength = 0.10;
    params.tongueWidth = 0.025;
    params.tongueThickness = 0.003;
    params.tuneToMidi = false;

    ChromaticVoice geometryVoice;
    geometryVoice.prepare (48000.0);
    geometryVoice.noteOn (69, 0.8f, material, params);
    const auto geometryModes = geometryVoice.getModes();

    params.tuneToMidi = true;
    ChromaticVoice midiVoice;
    midiVoice.prepare (48000.0);
    midiVoice.noteOn (69, 0.8f, material, params);
    const auto midiModes = midiVoice.getModes();
    CHECK (! geometryModes.empty() && ! midiModes.empty()
           && std::abs (midiModes[0].frequency - 440.0f) < 0.01f
           && std::abs (geometryModes[0].frequency - 440.0f) > 1.0f,
           "frequency_mode separates MIDI pitch lock from absolute geometry physics");
    CHECK (std::abs (midiModes[0].decayTime
           - BeamModel::decayTimeForFrequency (midiModes[0].frequency, material)) < 1.0e-5f,
           "Damping is recomputed from the final sounding frequency");

    const float overrideDecay = StringModel::decayTimeForFrequency (440.0f, material, 1.0e-6f);
    CHECK (overrideDecay > 1.0f && overrideDecay < 100.0f,
           "Damping alpha override retains air and radiation losses");
}

void testHammerSpectrum()
{
    constexpr float tau = 0.002f;
    const float turningHz = 1.0f / (2.0f * tau);
    const float firstNullHz = 3.0f / (2.0f * tau);
    const float atTurning = HammerImpulse::forceSpectrumMagnitude (
        juce::MathConstants<float>::twoPi * turningHz, tau);
    const float atNull = HammerImpulse::forceSpectrumMagnitude (
        juce::MathConstants<float>::twoPi * firstNullHz, tau);
    CHECK (std::abs (atTurning - juce::MathConstants<float>::pi * 0.25f) < 1.0e-4f,
           "1/(2*tau) is the removable pi/4 point, not a false spectral null");
    CHECK (atNull < 1.0e-5f, "Half-sine impulse first true null is 3/(2*tau)");
    CHECK (HammerImpulse::tauCForStrike (1.0f, 1.0f)
           < HammerImpulse::tauCForStrike (1.0f, 0.1f),
           "Hertz strike-speed law shortens contact at higher velocity");
}

void testRelativeCutoffAndNoiseStreams()
{
    ModalResonator resonator;
    resonator.setSampleRate (48000.0);
    resonator.reserveModes (2);
    resonator.setModes ({ { 440.0f, 1.0f, 0.01f },
                          { 660.0f, 1.0e-7f, 0.01f } });
    resonator.excite (1.0f);
    for (int i = 0; i < 240; ++i) resonator.processSample();
    CHECK (resonator.getActiveModeCount() == 2,
           "Weak modes use a relative -60 dB lifetime instead of an absolute cutoff");
    for (int i = 0; i < 300; ++i) resonator.processSample();
    CHECK (! resonator.isActive(), "Modal resonator stops after each mode reaches its T60");

    NoiseGen a, b, c;
    const auto seed0 = NoiseGen::mixSeed (1234, 0, 69, 1000);
    const auto seed1 = NoiseGen::mixSeed (1234, 1, 69, 1000);
    a.setSeed (seed0);
    b.setSeed (seed0);
    c.setSeed (seed1);
    bool identical = true;
    bool eventSeparated = false;
    for (int i = 0; i < 128; ++i)
    {
        const float av = a.processSample();
        const float bv = b.processSample();
        const float cv = c.processSample();
        identical = identical && av == bv;
        eventSeparated = eventSeparated || av != cv;
    }
    CHECK (identical, "Specified PCG noise is exactly reproducible for the same event seed");
    CHECK (seed0 != seed1 && eventSeparated,
           "Event index prevents coherent repeated-note noise streams");
}

void testLongDelayAndSharedEffects()
{
    StereoDelay delay;
    delay.prepare (48000.0);
    delay.setTime (5000.0f);
    delay.setFeedback (0.0f);
    delay.setMix (1.0f);
    int leftHit = -1, rightHit = -1;
    for (int i = 0; i < 264010; ++i)
    {
        float left = i == 0 ? 1.0f : 0.0f;
        float right = left;
        delay.processStereo (left, right);
        if (leftHit < 0 && std::abs (left) > 0.9f) leftHit = i;
        if (rightHit < 0 && std::abs (right) > 0.9f) rightHit = i;
    }
    CHECK (leftHit == 240000 && rightHit == 264000,
           "StereoDelay honours the full 5000 ms score contract including 1.10x right spread");

    StereoDelay automatedDelay;
    automatedDelay.prepare (1000.0);
    automatedDelay.setFeedback (0.0f);
    automatedDelay.setMix (0.0f);
    automatedDelay.setTime (100.0f);
    for (int i = 0; i < 50; ++i)
    {
        float left = i == 0 ? 1.0f : 0.0f;
        float right = left;
        automatedDelay.processStereo (left, right);
    }
    automatedDelay.setTime (0.0f);
    for (int i = 0; i < 200; ++i)
    {
        float left = 0.0f, right = 0.0f;
        automatedDelay.processStereo (left, right);
    }
    automatedDelay.setTime (100.0f);
    automatedDelay.setMix (1.0f);
    int historyHit = -1;
    for (int i = 0; i < 120; ++i)
    {
        float left = 0.0f, right = 0.0f;
        automatedDelay.processStereo (left, right);
        if (historyHit < 0 && std::abs (left) > 0.9f) historyHit = i;
    }
    CHECK (historyHit < 0,
           "Zero-time delay keeps history moving instead of replaying frozen stale audio");

    SimpleReverb t60Reverb;
    t60Reverb.prepare (44100.0);
    t60Reverb.setDecayTime (1.0f);
    t60Reverb.setDamping (0.0f);
    t60Reverb.setMix (1.0f);
    float earlyPeak = 0.0f;
    float latePeak = 0.0f;
    for (int i = 0; i < 50000; ++i)
    {
        float left = i == 0 ? 1.0f : 0.0f;
        float right = left;
        t60Reverb.processStereo (left, right);
        if (i >= 1000 && i < 6000)
            earlyPeak = std::max (earlyPeak, std::abs (right));
        if (i >= 45100 && i < 50100)
            latePeak = std::max (latePeak, std::abs (right));
    }
    const float reverbRatio = earlyPeak > 0.0f ? latePeak / earlyPeak : 1.0f;
    CHECK (earlyPeak > 0.0f && reverbRatio > 0.0001f && reverbRatio < 0.01f,
           "Authored reverb T60 reaches approximately -60 dB after one second");

    std::atomic<float> revMix { 0.25f }, revSize { 0.5f };
    std::atomic<float> delTime { 300.0f }, delFeedback { 0.3f }, delMix { 0.2f };
    std::atomic<float> compThreshold { -12.0f }, compRatio { 1.0f };
    std::atomic<float> distType { 0.0f }, distDrive { 0.0f };
    std::atomic<float> distInstability { 0.0f }, distMix { 0.5f };
    EffectChain plugin;
    plugin.pReverbMix = &revMix; plugin.pReverbSize = &revSize;
    plugin.pDelayTime = &delTime; plugin.pDelayFeedback = &delFeedback; plugin.pDelayMix = &delMix;
    plugin.pCompThreshold = &compThreshold; plugin.pCompRatio = &compRatio;
    plugin.pDistType = &distType; plugin.pDistDrive = &distDrive;
    plugin.pDistInstability = &distInstability; plugin.pDistMix = &distMix;
    plugin.prepare (48000.0);

    EffectsChain offline;
    offline.prepare (48000.0);
    EffectsParams ep;
    ep.reverbEnabled = true; ep.reverbRoomSize = 0.5f;
    ep.reverbDamping = 0.5f; ep.reverbWet = 0.25f;
    ep.delayEnabled = true; ep.delayTime = 0.3;
    ep.delayFeedback = 0.3f; ep.delayWet = 0.2f;
    ep.compressorEnabled = false; ep.distortionEnabled = false;
    offline.setParameters (ep);

    bool same = true;
    juce::AudioBuffer<float> oneSample (2, 1);
    for (int i = 0; i < 40000; ++i)
    {
        float pl = i == 0 ? 0.5f : 0.0f, pr = pl;
        float ol = pl, oright = pr;
        oneSample.setSample (0, 0, pl);
        oneSample.setSample (1, 0, pr);
        plugin.processBlock (oneSample);
        pl = oneSample.getSample (0, 0);
        pr = oneSample.getSample (1, 0);
        offline.processStereo (ol, oright);
        same = same && std::abs (pl - ol) < 1.0e-7f
                    && std::abs (pr - oright) < 1.0e-7f;
    }
    CHECK (same, "Plugin and CLI share the same static FX signal path");
}
}

int main()
{
    std::cout << "TsukiSynth physical-model regression tests\n";
    testBeamBoundaryAndGeometry();
    testPlateModesAndPoisson();
    testGeometryFrequencyModeAndDamping();
    testHammerSpectrum();
    testRelativeCutoffAndNoiseStreams();
    testLongDelayAndSharedEffects();
    std::cout << (failures == 0 ? "PASS" : "FAIL")
              << " (" << failures << " failures)\n";
    return failures == 0 ? 0 : 1;
}
