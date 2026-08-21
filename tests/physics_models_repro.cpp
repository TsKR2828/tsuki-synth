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
#include <limits>

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
    material.damping.eta = 2.0e-4f;   // steel loss factor (materials.json)
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
           "Damping override retains air and radiation losses");

    // Broadband internal friction (2026-08-10): the eta term's decay-rate
    // contribution is proportional to frequency, so doubling f must double it.
    // Verified against the isolated term (beta/gamma zeroed) so the f^2 and f
    // terms cannot mask a wrong exponent.
    MaterialDB::Material etaOnly = material;
    etaOnly.damping.beta_air = 0.0f;
    etaOnly.damping.gamma_radiation = 0.0f;
    const float t60At220 = StringModel::decayTimeForFrequency (220.0f, etaOnly);
    const float t60At440 = StringModel::decayTimeForFrequency (440.0f, etaOnly);
    CHECK (std::abs (t60At220 / t60At440 - 2.0f) < 1.0e-3f,
           "Internal friction is broadband: T60 halves per octave (rate ~ eta*f)");

    // Literature anchor: T60 = 2.2/(f*eta) must hold at ANY frequency now,
    // not just at the retired MIDI 60 anchor (materials_physicalization_proposal §1.2).
    for (const float probe : { 82.4f, 261.6256f, 1046.5f, 3520.0f })
    {
        const float predicted = 2.2f / (probe * etaOnly.damping.eta);
        const float actual = StringModel::decayTimeForFrequency (probe, etaOnly);
        CHECK (std::abs (actual / predicted - 1.0f) < 1.0e-4f,
               "T60 = 2.2/(f*eta) holds across the whole range, not one anchor");
    }

    // damping_override keeps its authored MIDI-60-anchor meaning: an override
    // numerically equal to the old alpha must reproduce the old T60 at MIDI 60.
    const float legacyAlpha = 0.4f;              // value used by 32 authored scores
    const float atAnchor = StringModel::decayTimeForFrequency (
        261.6256f, etaOnly, legacyAlpha);
    CHECK (std::abs (atAnchor - 1.0f / legacyAlpha) < 1.0e-3f,
           "damping_override still means the internal-friction rate at MIDI 60");
}

// ── Bridge/soundboard admittance coupling loss (2026-08-16 B1) ────────────
// docs/workcards/B1.md §7. Reference numbers are copied from
// docs/BRIDGE_ADMITTANCE_SOURCES.md §2.1 (Y_inf self-check table) and §3
// (T60_bridge literature table), NOT derived independently here.

void testBridgeAdmittanceLoss()
{
    // §7-1: Y_inf formula vs. the literature self-check table
    // (BRIDGE_ADMITTANCE_SOURCES.md §2.1), using ITS synthetic material
    // (E=11.5 GPa, rho=400 kg/m^3, nu=0.30) -- NOT materials.json's
    // wood_spruce, which has different numbers.
    MaterialDB::Material soundboardStub;
    soundboardStub.displayName = "Bridge admittance self-check stub";
    soundboardStub.youngsModulus = 11.5e9f;
    soundboardStub.density = 400.0f;
    soundboardStub.poissonRatio = 0.30f;

    // bridgeLossRate(tension, length, ...) = tension*G/(ln1000*length); with
    // tension=ln(1000) and length=1, this collapses to exactly G = Y_inf, so
    // we can read Y_inf straight off the public function without a private
    // hook.
    const float kLn1000Probe = 6.907755278982137f;
    const float yInf8mm  = StringModel::bridgeLossRate (kLn1000Probe, 1.0f, soundboardStub, 0.008f);
    const float yInf10mm = StringModel::bridgeLossRate (kLn1000Probe, 1.0f, soundboardStub, 0.010f);
    CHECK (std::abs (yInf8mm / 3.01e-3f - 1.0f) < 0.005f,
           "Y_inf at h=8mm matches BRIDGE_ADMITTANCE_SOURCES.md Sec2.1 table (3.01e-3 s/kg, +-0.5%)");
    CHECK (std::abs (yInf10mm / 1.93e-3f - 1.0f) < 0.005f,
           "Y_inf at h=10mm matches BRIDGE_ADMITTANCE_SOURCES.md Sec2.1 table (1.93e-3 s/kg, +-0.5%)");

    // §7-2: T60_bridge vs. the literature table (BRIDGE_ADMITTANCE_SOURCES.md
    // Sec3), cross-checking the alpha->T60 algebra chain directly (bypasses
    // bridgeLossRate's internal Y_inf calculation on purpose -- this test is
    // about decayTimeForFrequency's denominator wiring, not the Y_inf formula
    // that test §7-1 already covers). G = 1.3e-3 s/kg is the literature
    // upright-piano average admittance (Sec2.1).
    const float G = 1.3e-3f;
    MaterialDB::Material noOtherDamping = steel();
    noOtherDamping.damping.eta = 0.0f;
    noOtherDamping.damping.beta_air = 0.0f;
    noOtherDamping.damping.gamma_radiation = 0.0f;

    auto t60BridgeFor = [&] (float tensionOverLength)
    {
        const float bridgeLoss = tensionOverLength * G / kLn1000Probe;
        return StringModel::decayTimeForFrequency (
            261.6256f /* any freq: other 3 terms are zero */,
            noOtherDamping, -1.0f, bridgeLoss);
    };
    CHECK (std::abs (t60BridgeFor (1250.0f) / 4.25f - 1.0f) < 0.01f,
           "T60_bridge at C2 (T/L=1250.0 N/m) matches literature table (4.25s, +-1%)");
    CHECK (std::abs (t60BridgeFor (1073.3f) / 4.95f - 1.0f) < 0.01f,
           "T60_bridge at C4 (T/L=1073.3 N/m) matches literature table (4.95s, +-1%)");
    CHECK (std::abs (t60BridgeFor (12650.0f) / 0.42f - 1.0f) < 0.01f,
           "T60_bridge at C8 (T/L=12650.0 N/m) matches literature table (0.42s, +-1%)");

    // §7-3: frequency independence. eta=beta_air=gamma_radiation=0, only the
    // bridge term is nonzero -- decayTimeForFrequency must return the exact
    // same value at a low and a high frequency, because bridgeLoss does not
    // depend on `frequency` at all.
    const float bridgeLossConst = 0.235270f;   // arbitrary nonzero constant
    const float t60At55   = StringModel::decayTimeForFrequency (
        55.0f, noOtherDamping, -1.0f, bridgeLossConst);
    const float t60At4000 = StringModel::decayTimeForFrequency (
        4000.0f, noOtherDamping, -1.0f, bridgeLossConst);
    CHECK (std::abs (t60At55 - t60At4000) < 1.0e-4f,
           "Bridge coupling loss term is frequency-independent (55Hz T60 == 4000Hz T60)");

    // §7-5: damping_override coexists with bridgeLoss -- the override only
    // replaces the internal-friction term; bridgeLoss must still change the
    // result when added.
    const float withOverrideNoBridge = StringModel::decayTimeForFrequency (
        261.6256f, steel(), 0.4f, 0.0f);
    const float withOverrideAndBridge = StringModel::decayTimeForFrequency (
        261.6256f, steel(), 0.4f, bridgeLossConst);
    CHECK (std::abs (withOverrideAndBridge - withOverrideNoBridge) > 1.0e-3f,
           "damping_override does not swallow the bridge coupling term");

    // §7-6: backward compatibility -- omitting the 4th argument must be
    // byte-for-byte identical to passing bridgeLoss=0.0f explicitly.
    const float threeArgCall = StringModel::decayTimeForFrequency (440.0f, steel());
    const float fourArgZero  = StringModel::decayTimeForFrequency (440.0f, steel(), -1.0f, 0.0f);
    CHECK (threeArgCall == fourArgZero,
           "Omitting bridgeLoss is identical to passing bridgeLoss=0.0f (existing callers unaffected)");

    // §7-7: bridgeLossRate() fail-closed reprs -- non-finite/non-positive
    // inputs must return 0.0f, never NaN/Inf/negative.
    CHECK (StringModel::bridgeLossRate (1000.0f, 1.0f, soundboardStub, 0.0f) == 0.0f,
           "bridgeLossRate fail-closed: soundboardThicknessM=0 -> 0.0f");
    CHECK (StringModel::bridgeLossRate (1000.0f, 1.0f, soundboardStub, -0.005f) == 0.0f,
           "bridgeLossRate fail-closed: negative soundboardThicknessM -> 0.0f");
    CHECK (StringModel::bridgeLossRate (1000.0f, 0.0f, soundboardStub, 0.009f) == 0.0f,
           "bridgeLossRate fail-closed: length=0 -> 0.0f");
    CHECK (StringModel::bridgeLossRate (1000.0f, -1.0f, soundboardStub, 0.009f) == 0.0f,
           "bridgeLossRate fail-closed: negative length -> 0.0f");
    CHECK (StringModel::bridgeLossRate (0.0f, 1.0f, soundboardStub, 0.009f) == 0.0f,
           "bridgeLossRate fail-closed: tension=0 -> 0.0f");
    CHECK (StringModel::bridgeLossRate (
               std::numeric_limits<float>::quiet_NaN(), 1.0f, soundboardStub, 0.009f) == 0.0f,
           "bridgeLossRate fail-closed: non-finite tension -> 0.0f");
}

// §7-4 sentinel/mutant test: proves the §7-3 equality check has real
// detection power (would actually flag a regression), not a tautology that
// passes for any implementation. Full write-up + this test's own console
// output are archived verbatim at reports/gate_outputs/b1_selftest_sentinel.txt
// (docs/workcards/B1.md §8 GATE row 3). Deliberately does NOT touch
// StringModel.h -- the "broken" version is simulated inline, entirely inside
// this test function, so the suite's overall PASS/FAIL count stays honest
// (a real production-code mutation would need its own separate build+run,
// which is out of scope for a single ctest invocation).
void testBridgeLossSentinel()
{
    const float bridgeLoss = 0.235270f;   // representative nonzero constant

    // "Broken" mutant: bridgeLoss deliberately scaled by frequency, exactly
    // the shape of regression this sentinel guards against (someone
    // accidentally routing the 4th term through a frequency-dependent
    // expression instead of a constant).
    auto brokenT60 = [&] (float freq)
    {
        const float brokenBridgeLoss = bridgeLoss * (freq / 261.6256f);
        return 1.0f / brokenBridgeLoss;
    };
    const float brokenAt55   = brokenT60 (55.0f);
    const float brokenAt4000 = brokenT60 (4000.0f);
    const bool brokenWouldPassEqualityCheck =
        std::abs (brokenAt55 - brokenAt4000) < 1.0e-4f;
    std::cout << "[SENTINEL 1/2] mutant (frequency-scaled bridgeLoss): T60(55Hz)="
              << brokenAt55 << "s  T60(4000Hz)=" << brokenAt4000
              << "s -- same equality check as the real test would report: "
              << (brokenWouldPassEqualityCheck ? "[PASS] (BAD -- no detection power)"
                                                : "[FAIL] (GOOD -- regression caught)")
              << '\n';
    CHECK (! brokenWouldPassEqualityCheck,
           "SENTINEL: mutant frequency-dependent bridgeLoss is distinguishable "
           "at 55Hz vs 4000Hz (proves the Sec7-3 equality check has detection power)");

    MaterialDB::Material noOtherDamping = steel();
    noOtherDamping.damping.eta = 0.0f;
    noOtherDamping.damping.beta_air = 0.0f;
    noOtherDamping.damping.gamma_radiation = 0.0f;
    const float correctAt55 = StringModel::decayTimeForFrequency (
        55.0f, noOtherDamping, -1.0f, bridgeLoss);
    const float correctAt4000 = StringModel::decayTimeForFrequency (
        4000.0f, noOtherDamping, -1.0f, bridgeLoss);
    const bool correctPassesEqualityCheck =
        std::abs (correctAt55 - correctAt4000) < 1.0e-4f;
    std::cout << "[SENTINEL 2/2] real StringModel::decayTimeForFrequency: T60(55Hz)="
              << correctAt55 << "s  T60(4000Hz)=" << correctAt4000
              << "s -- verdict: " << (correctPassesEqualityCheck ? "[PASS]" : "[FAIL]")
              << '\n';
    CHECK (correctPassesEqualityCheck,
           "SENTINEL: real bridgeLoss term passes the same equality check "
           "(frequency-independent, as required)");
}

void testDimensionalScalingLaws()
{
    const auto material = steel();

    BeamModel::Params beam;
    beam.numModes = 1;
    beam.length = 0.12f;
    beam.thickness = 0.003f;
    const float beamBase = BeamModel::calculateModes (beam, material)[0].frequency;
    beam.length *= 2.0f;
    const float beamLong = BeamModel::calculateModes (beam, material)[0].frequency;
    beam.length = 0.12f;
    beam.thickness *= 2.0f;
    const float beamThick = BeamModel::calculateModes (beam, material)[0].frequency;
    auto fourE = material;
    fourE.youngsModulus *= 4.0f;
    beam.thickness = 0.003f;
    const float beamFourE = BeamModel::calculateModes (beam, fourE)[0].frequency;
    auto fourRho = material;
    fourRho.density *= 4.0f;
    const float beamFourRho = BeamModel::calculateModes (beam, fourRho)[0].frequency;
    CHECK (std::abs (beamLong / beamBase - 0.25f) < 2.0e-5f
           && std::abs (beamThick / beamBase - 2.0f) < 2.0e-5f
           && std::abs (beamFourE / beamBase - 2.0f) < 2.0e-5f
           && std::abs (beamFourRho / beamBase - 0.5f) < 2.0e-5f,
           "Beam frequencies obey L^-2, thickness, sqrt(E), and rho^-1/2 scaling");

    PlateModel::Params plate;
    plate.freeEdge = false;
    plate.numModes = 1;
    plate.radius = 0.15f;
    plate.thickness = 0.003f;
    const float plateBase = PlateModel::calculateModes (plate, material)[0].frequency;
    plate.radius *= 2.0f;
    const float plateLarge = PlateModel::calculateModes (plate, material)[0].frequency;
    plate.radius = 0.15f;
    plate.thickness *= 2.0f;
    const float plateThick = PlateModel::calculateModes (plate, material)[0].frequency;
    plate.thickness = 0.003f;
    const float plateFourE = PlateModel::calculateModes (plate, fourE)[0].frequency;
    const float plateFourRho = PlateModel::calculateModes (plate, fourRho)[0].frequency;
    CHECK (std::abs (plateLarge / plateBase - 0.25f) < 2.0e-5f
           && std::abs (plateThick / plateBase - 2.0f) < 2.0e-5f
           && std::abs (plateFourE / plateBase - 2.0f) < 2.0e-5f
           && std::abs (plateFourRho / plateBase - 0.5f) < 2.0e-5f,
           "Plate frequencies obey R^-2, thickness, sqrt(E), and rho^-1/2 scaling");
}

void testPassivityAndInvalidNumericRefusal()
{
    ModalResonator passive;
    passive.setSampleRate (48000.0);
    passive.setModes ({ { 1000.0f, 1.0f, 0.1f } });
    passive.excite (1.0f);
    float previousCycleEnergy = std::numeric_limits<float>::infinity();
    bool monotonicallyDecaying = true;
    for (int cycle = 0; cycle < 80; ++cycle)
    {
        float energy = 0.0f;
        for (int i = 0; i < 48; ++i)
        {
            const float sample = passive.processSample();
            energy += sample * sample;
        }
        monotonicallyDecaying = monotonicallyDecaying
            && energy < previousCycleEnergy;
        previousCycleEnergy = energy;
    }
    CHECK (monotonicallyDecaying,
           "Unforced modal energy decays monotonically cycle by cycle");

    ModalResonator invalid;
    invalid.setSampleRate (48000.0);
    invalid.setModes ({
        { std::numeric_limits<float>::quiet_NaN(), 1.0f, 1.0f },
        { std::numeric_limits<float>::infinity(), 1.0f, 1.0f },
        { 440.0f, std::numeric_limits<float>::quiet_NaN(), 1.0f },
        { 880.0f, 1.0f, std::numeric_limits<float>::quiet_NaN() }
    });
    invalid.excite (1.0f);
    bool finiteSilence = ! invalid.isActive();
    for (int i = 0; i < 128; ++i)
    {
        const float sample = invalid.processSample();
        finiteSilence = finiteSilence && std::isfinite (sample)
            && sample == 0.0f;
    }
    CHECK (finiteSilence,
           "Invalid modal numbers fail closed without NaN output or a live voice");

    ModalResonator mixed;
    mixed.setSampleRate (48000.0);
    mixed.setModes ({
        { 440.0f, 1.0f, 1.0f },
        { 880.0f, std::numeric_limits<float>::quiet_NaN(), 1.0f },
        { 1320.0f, 0.5f, std::numeric_limits<float>::infinity() }
    });
    mixed.excite (1.0f);
    bool mixedFinite = mixed.isActive();
    for (int i = 0; i < 4096; ++i)
        mixedFinite = mixedFinite && std::isfinite (mixed.processSample());
    CHECK (mixedFinite && mixed.getModes().size() == 1,
           "Invalid modes cannot poison a simultaneously active valid mode");
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
    ModalResonator frequencyGate;
    frequencyGate.setSampleRate (48000.0);
    frequencyGate.setModes ({ { 19.99f, 1.0f, 1.0f },
                              { 20.0f, 1.0f, 1.0f },
                              { 20001.0f, 1.0f, 1.0f } });
    const auto retained = frequencyGate.getModes();
    CHECK (retained.size() == 1 && retained[0].frequency == 20.0f,
           "Modal frequency gate exactly matches the DSP renderable band");

    ChromaticParams subaudible;
    subaudible.subEngine = ChromaticSubEngine::TongueDrum;
    subaudible.tongueLength = 10.0;
    subaudible.tongueWidth = 0.001;
    subaudible.tongueThickness = 0.0001;
    subaudible.tuneToMidi = false;
    ChromaticVoice subaudibleVoice;
    subaudibleVoice.prepare (48000.0);
    subaudibleVoice.noteOn (60, 0.8f, steel(), subaudible);
    CHECK (subaudibleVoice.getModes().empty(),
           "Geometry modes below 20 Hz are rejected instead of becoming attack-only audio");

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
           "Distinct semantic event identities prevent coherent repeated-note noise streams");
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


void testBesselPortable()
{
    // X2 (2026-08-20): the portable ascending-series Bessel fallback that
    // libc++ (Apple) platforms use in PlateModel::besselJ/besselI. Verified
    // two independent ways so the macos leg is covered even though this
    // machine's std library also has the functions:
    //
    // (1) Literature/scipy anchors -- run on EVERY platform. Values from
    //     scipy.special.jv/iv 1.x (independent implementation; J0(1) and
    //     J1(1) also cross-checked against Abramowitz & Stegun Table 9.1 to
    //     all printed digits). Chosen to span the actual plate usage domain:
    //     orders 0..6, arguments up to sqrt(120.08) = 10.958 (largest
    //     clamped eigenvalue) plus the free-edge moment order m+1 = 6.
    struct Anchor { int m; double x; double j; double i; };
    static constexpr Anchor anchors[] = {
        { 0,  1.0,     7.6519768655796661e-01, 1.2660658777520084e+00 },
        { 1,  1.0,     4.4005058574493355e-01, 5.6515910399248503e-01 },
        { 0,  2.0,     2.2389077914123562e-01, 2.2795853023360673e+00 },
        { 2,  5.0,     4.6565116277752290e-02, 1.7505614966624236e+01 },
        { 3, 10.0,     5.8379379305186670e-02, 1.7583807166108531e+03 },
        { 5,  9.5,    -1.6132126019962670e-01, 4.5213152819727270e+02 },
        { 6, 11.0,    -2.0158400087404349e-01, 1.3720929647738608e+03 },
        { 0, 10.958,  -1.7847614684721927e-01, 7.0024303045643919e+03 },
    };
    // Tolerance derivation (BesselPortable.h header): |error| bounded by
    // (largest series term) * eps; over the anchor range the largest term is
    // I_0(10.958) ~ 7.0e3, so absolute error <~ 1.6e-12. Judge with a mixed
    // absolute/relative criterion at 1e-11 (6x margin over the bound; R2
    // note: this is a first-principles error bound, not a fitted number).
    bool anchorsOk = true;
    for (const auto& a : anchors)
    {
        const double j = tsuki::besselJPortable (a.m, a.x);
        const double i = tsuki::besselIPortable (a.m, a.x);
        if (std::abs (j - a.j) > 1e-11 * (1.0 + std::abs (a.j))) anchorsOk = false;
        if (std::abs (i - a.i) > 1e-11 * (1.0 + std::abs (a.i))) anchorsOk = false;
    }
    CHECK (anchorsOk,
           "Portable Bessel matches independent scipy/A&S anchors (mixed 1e-11)");

    // (2) Dense grid against the std implementation -- runs on platforms
    //     that have it (Windows/Linux, i.e. the ones whose production path
    //     still uses std::), proving fallback and production agree
    //     everywhere PlateModel can evaluate them.
   #if defined(__cpp_lib_math_special_functions)
    bool gridOk = true;
    double worst = 0.0;
    for (int m = 0; m <= 8; ++m)
        for (double x = 0.0; x <= 16.0 + 1e-9; x += 0.05)
        {
            const double dj = std::abs (tsuki::besselJPortable (m, x)
                                        - std::cyl_bessel_j ((double) m, x))
                            / (1.0 + std::abs (std::cyl_bessel_j ((double) m, x)));
            const double di = std::abs (tsuki::besselIPortable (m, x)
                                        - std::cyl_bessel_i ((double) m, x))
                            / (1.0 + std::abs (std::cyl_bessel_i ((double) m, x)));
            worst = std::max ({ worst, dj, di });
            if (dj > 1e-10 || di > 1e-10) gridOk = false;
        }
    std::cout << "       (portable-vs-std worst mixed deviation over "
                 "9 orders x 321 args: " << worst << ")\n";
    CHECK (gridOk,
           "Portable Bessel agrees with std::cyl_bessel_j/_i on the full validated grid (mixed 1e-10)");
   #endif

    // Fail-closed domain sentinels: outside the validated domain the
    // fallback must refuse (NaN), never extrapolate.
    CHECK (std::isnan (tsuki::besselJPortable (9, 1.0)),
           "Portable Bessel fail-closed: order 9 (outside validated domain) -> NaN");
    CHECK (std::isnan (tsuki::besselJPortable (-1, 1.0)),
           "Portable Bessel fail-closed: negative order -> NaN");
    CHECK (std::isnan (tsuki::besselIPortable (0, 16.5)),
           "Portable Bessel fail-closed: x > 16 (outside validated domain) -> NaN");
    CHECK (std::isnan (tsuki::besselJPortable (0, -0.5)),
           "Portable Bessel fail-closed: negative x -> NaN");
    CHECK (std::isnan (tsuki::besselJPortable (0,
               std::numeric_limits<double>::quiet_NaN())),
           "Portable Bessel fail-closed: NaN x -> NaN");
    // In-domain positive control so the sentinels cannot pass vacuously.
    CHECK (std::isfinite (tsuki::besselJPortable (6, 11.0)),
           "Portable Bessel positive control: in-domain evaluation is finite");
}

int main()
{
    std::cout << "TsukiSynth physical-model regression tests\n";
    testBeamBoundaryAndGeometry();
    testBesselPortable();
    testPlateModesAndPoisson();
    testGeometryFrequencyModeAndDamping();
    testBridgeAdmittanceLoss();
    testBridgeLossSentinel();
    testDimensionalScalingLaws();
    testPassivityAndInvalidNumericRefusal();
    testHammerSpectrum();
    testRelativeCutoffAndNoiseStreams();
    testLongDelayAndSharedEffects();
    std::cout << (failures == 0 ? "PASS" : "FAIL")
              << " (" << failures << " failures)\n";
    return failures == 0 ? 0 : 1;
}
