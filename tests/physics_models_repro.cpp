#include "physics/BeamModel.h"
#include "physics/PlateModel.h"
#include "physics/StringModel.h"
#include "physics/RadiationModel.h"
#include "physics/HammerImpulse.h"
#include "engines/ChromaticEngine.h"
#include "engines/CimbalomEngine.h"
#include "dsp/NoiseGen.h"
#include "dsp/DiagnosticOverrides.h"
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
    material.damping.beam_plate_beta_air = 1.2e-7f;        // Beam/Plate-only (B3)
    material.damping.beam_plate_gamma_radiation = 2.0e-5f; // Beam/Plate-only (B3)
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

    // String-test geometry: the StringModel::Params struct defaults
    // (diameter 0.8 mm -> r = 4.0e-4 m, tension 800 N), so these literals stay
    // traceable to an existing in-repo source rather than being new free values.
    constexpr float kTestRadius  = 4.0e-4f;
    constexpr float kTestTension = 800.0f;

    // A near-zero override wipes the internal-friction term; the T60 that
    // remains is set by the B3 air+viscoelastic+dislocation mechanisms (real
    // geometry passed), which for steel at 440 Hz lands in the tens of
    // seconds -- far from both 0 and the 10 s zero-denominator fallback... so
    // bound it well above 1 s and below 100 s exactly as before B3.
    const float overrideDecay = StringModel::decayTimeForFrequency (
        440.0f, material, 1.0e-6f, 0.0f, kTestRadius, kTestTension);
    CHECK (overrideDecay > 1.0f && overrideDecay < 100.0f,
           "Damping override retains the air/viscoelastic/dislocation losses");

    // Broadband internal friction (2026-08-10): the eta term's decay-rate
    // contribution is proportional to frequency, so doubling f must double it.
    // B3 note: the old isolation trick (zeroing beta_air/gamma_radiation on a
    // Material) no longer exists -- the string law does not read those fields
    // any more -- so the eta term is now isolated by calling
    // MaterialDB::internalFrictionRate() directly (docs/workcards/B3.md §6 8b).
    MaterialDB::Material etaOnly = material;
    const float t60At220 = 1.0f / MaterialDB::internalFrictionRate (
        etaOnly.damping.eta, 220.0f);
    const float t60At440 = 1.0f / MaterialDB::internalFrictionRate (
        etaOnly.damping.eta, 440.0f);
    CHECK (std::abs (t60At220 / t60At440 - 2.0f) < 1.0e-3f,
           "Internal friction is broadband: T60 halves per octave (rate ~ eta*f)");

    // Literature anchor: T60 = 2.2/(f*eta) must hold at ANY frequency now,
    // not just at the retired MIDI 60 anchor (materials_physicalization_proposal §1.2).
    for (const float probe : { 82.4f, 261.6256f, 1046.5f, 3520.0f })
    {
        const float predicted = 2.2f / (probe * etaOnly.damping.eta);
        const float actual = 1.0f / MaterialDB::internalFrictionRate (
            etaOnly.damping.eta, probe);
        CHECK (std::abs (actual / predicted - 1.0f) < 1.0e-4f,
               "T60 = 2.2/(f*eta) holds across the whole range, not one anchor");
    }

    // damping_override keeps its authored MIDI-60-anchor meaning for the
    // internal-friction term it replaces: with the B3 three-mechanism sum
    // disabled (radius/tension = 0 -> stringAirViscDislQInv contributes 0)
    // and no bridge loss, T60 at the anchor is exactly 1/alpha.
    const float legacyAlpha = 0.4f;              // value used by 32 authored scores
    const float atAnchorIsolated = StringModel::decayTimeForFrequency (
        261.6256f, material, legacyAlpha, 0.0f, 0.0f, 0.0f);
    CHECK (std::abs (atAnchorIsolated - 1.0f / legacyAlpha) < 1.0e-3f,
           "damping_override still means the internal-friction rate at MIDI 60");

    // B3 HONEST CHANGE: with real geometry the anchor T60 now ALSO carries the
    // frequency-dependent air+visc+dislocation sum, so the pre-B3 "bit-exact
    // 1/alpha at MIDI 60" guarantee is deliberately retired (B3 card §11).
    // Expected value re-derived from the §4.1 algebra: the override-eta and the
    // three-mechanism Q^-1 share one scale, T60 = 1/(alpha + qInv*f/2.2).
    // (Wiring test: the helper's own VALUES are pinned separately against the
    // Cuesta & Valette reference table in testStringDampingFirstPrinciples.)
    const float qInvAtAnchor = StringModel::stringAirViscDislQInv (
        261.6256f, kTestRadius, kTestTension, material);
    const float expectedAtAnchor = 1.0f
        / (legacyAlpha + qInvAtAnchor * 261.6256f / MaterialDB::kEtaToDecayRate);
    const float atAnchorReal = StringModel::decayTimeForFrequency (
        261.6256f, material, legacyAlpha, 0.0f, kTestRadius, kTestTension);
    CHECK (std::abs (atAnchorReal / expectedAtAnchor - 1.0f) < 1.0e-4f,
           "Anchor T60 with real geometry = 1/(alpha + qInv*f/2.2) per B3 Sec4.1 algebra");
    CHECK (atAnchorReal < atAnchorIsolated,
           "B3 retires the bit-exact anchor guarantee: three-mechanism sum shortens anchor T60");
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
    // B3 isolation: eta = 0 kills the internal-friction term; radius/tension
    // = 0 makes stringAirViscDislQInv() contribute 0 (its documented
    // fail-closed behavior), so ONLY the bridge term remains -- the old trick
    // of zeroing beta_air/gamma_radiation no longer applies (the string law
    // does not read those Beam/Plate-only fields any more).
    MaterialDB::Material noOtherDamping = steel();
    noOtherDamping.damping.eta = 0.0f;

    auto t60BridgeFor = [&] (float tensionOverLength)
    {
        const float bridgeLoss = tensionOverLength * G / kLn1000Probe;
        return StringModel::decayTimeForFrequency (
            261.6256f /* any freq: other terms are zero */,
            noOtherDamping, -1.0f, bridgeLoss, 0.0f, 0.0f);
    };
    CHECK (std::abs (t60BridgeFor (1250.0f) / 4.25f - 1.0f) < 0.01f,
           "T60_bridge at C2 (T/L=1250.0 N/m) matches literature table (4.25s, +-1%)");
    CHECK (std::abs (t60BridgeFor (1073.3f) / 4.95f - 1.0f) < 0.01f,
           "T60_bridge at C4 (T/L=1073.3 N/m) matches literature table (4.95s, +-1%)");
    CHECK (std::abs (t60BridgeFor (12650.0f) / 0.42f - 1.0f) < 0.01f,
           "T60_bridge at C8 (T/L=12650.0 N/m) matches literature table (0.42s, +-1%)");

    // §7-3: frequency independence. eta = 0 and radius/tension = 0 (three-
    // mechanism sum disabled), only the bridge term is nonzero --
    // decayTimeForFrequency must return the exact same value at a low and a
    // high frequency, because bridgeLoss does not depend on `frequency` at all.
    const float bridgeLossConst = 0.235270f;   // arbitrary nonzero constant
    const float t60At55   = StringModel::decayTimeForFrequency (
        55.0f, noOtherDamping, -1.0f, bridgeLossConst, 0.0f, 0.0f);
    const float t60At4000 = StringModel::decayTimeForFrequency (
        4000.0f, noOtherDamping, -1.0f, bridgeLossConst, 0.0f, 0.0f);
    CHECK (std::abs (t60At55 - t60At4000) < 1.0e-4f,
           "Bridge coupling loss term is frequency-independent (55Hz T60 == 4000Hz T60)");

    // §7-5: damping_override coexists with bridgeLoss -- the override only
    // replaces the internal-friction term; bridgeLoss must still change the
    // result when added. (Real string geometry: StringModel::Params defaults,
    // r = 0.8 mm / 2, T = 800 N -- same literals as the anchor tests above.)
    const float withOverrideNoBridge = StringModel::decayTimeForFrequency (
        261.6256f, steel(), 0.4f, 0.0f, 4.0e-4f, 800.0f);
    const float withOverrideAndBridge = StringModel::decayTimeForFrequency (
        261.6256f, steel(), 0.4f, bridgeLossConst, 4.0e-4f, 800.0f);
    CHECK (std::abs (withOverrideAndBridge - withOverrideNoBridge) > 1.0e-3f,
           "damping_override does not swallow the bridge coupling term");

    // §7-6 (reworked for B3): the B1-era default-argument compatibility
    // guarantee is deliberately retired -- decayTimeForFrequency now has NO
    // default arguments, precisely so that any stale call site fails to
    // compile instead of silently rendering without the three-mechanism
    // physics. The surviving reduction property: with every optional loss
    // channel off (no override, bridgeLoss = 0, radius/tension = 0), the law
    // must collapse to EXACTLY the pure internal-friction term 2.2/(f*eta)
    // -- nothing else may leak into the denominator.
    const float allChannelsOff = StringModel::decayTimeForFrequency (
        440.0f, steel(), -1.0f, 0.0f, 0.0f, 0.0f);
    const float pureEta = 1.0f / MaterialDB::internalFrictionRate (
        steel().damping.eta, 440.0f);
    CHECK (allChannelsOff == pureEta,
           "With override/bridge/three-mechanism channels all off, the law reduces bit-exactly to 2.2/(f*eta)");

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

    // B3 isolation: eta = 0 + radius/tension = 0 (three-mechanism sum off);
    // see the matching comment in testBridgeAdmittanceLoss().
    MaterialDB::Material noOtherDamping = steel();
    noOtherDamping.damping.eta = 0.0f;
    const float correctAt55 = StringModel::decayTimeForFrequency (
        55.0f, noOtherDamping, -1.0f, bridgeLoss, 0.0f, 0.0f);
    const float correctAt4000 = StringModel::decayTimeForFrequency (
        4000.0f, noOtherDamping, -1.0f, bridgeLoss, 0.0f, 0.0f);
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

// ── Radiation efficiency skeleton (2026-08-28 B6 Phase 1) ─────────────────
// docs/workcards/B6.md §7 / docs/RADIATION_POWER_SOURCES.md. RadiationModel.h
// is a pure-function header consumed only from the --dump-modes diagnostic
// path (ScoreRenderer::dumpModes()) -- render()/renderEvent()/
// ModalResonator are untouched by B6, so these are ordinary unit tests
// against the header directly, no CLI/subprocess involved.

void testRadiationEfficiencyShape()
{
    // docs/RADIATION_POWER_SOURCES.md §3's "additional finding": with real
    // spruce/bridge parameters fga(~1.3kHz) < fc(~1.8kHz), so the "fc <= f
    // < fga" branch (sigma==1 but f still inside the model's valid range)
    // is UNREACHABLE for any currently-tabulated material. To actually
    // exercise that branch here we use synthetic fc/fga with fc < fga, per
    // that document's §5 test-construction recommendation -- these are not
    // meant to represent any real soundboard.
    const float fc  = 1000.0f;
    const float fga = 2000.0f;

    // f < fc: strictly below 1, and non-decreasing as f increases.
    const float s100 = RadiationModel::radiationEfficiency (100.0f, fc, fga);
    const float s300 = RadiationModel::radiationEfficiency (300.0f, fc, fga);
    const float s500 = RadiationModel::radiationEfficiency (500.0f, fc, fga);
    const float s900 = RadiationModel::radiationEfficiency (900.0f, fc, fga);
    CHECK (s100 < 1.0f && s300 < 1.0f && s500 < 1.0f && s900 < 1.0f,
           "radiationEfficiency: f < fc all give sigma < 1");
    CHECK (s100 <= s300 && s300 <= s500 && s500 <= s900,
           "radiationEfficiency: f < fc branch is non-decreasing in f");

    // fc <= f < fga: identically 1 (saturated).
    const float sAtFc   = RadiationModel::radiationEfficiency (fc, fc, fga);
    const float sMid    = RadiationModel::radiationEfficiency (1500.0f, fc, fga);
    const float sNearFga = RadiationModel::radiationEfficiency (1999.9f, fc, fga);
    CHECK (std::abs (sAtFc - 1.0f) < 1.0e-6f,
           "radiationEfficiency: f == fc gives sigma == 1");
    CHECK (std::abs (sMid - 1.0f) < 1.0e-6f,
           "radiationEfficiency: fc < f < fga gives sigma == 1");
    CHECK (std::abs (sNearFga - 1.0f) < 1.0e-6f,
           "radiationEfficiency: f just below fga still gives sigma == 1");

    // f >= fga: sentinel, model has no prediction here.
    const float sAtFga  = RadiationModel::radiationEfficiency (fga, fc, fga);
    const float sAboveFga = RadiationModel::radiationEfficiency (2500.0f, fc, fga);
    CHECK (sAtFga < 0.0f, "radiationEfficiency: f == fga gives the sentinel (-1)");
    CHECK (sAboveFga < 0.0f, "radiationEfficiency: f > fga gives the sentinel (-1)");

    // Fail-closed on bad fc/fga.
    CHECK (RadiationModel::radiationEfficiency (500.0f, -1.0f, fga) < 0.0f,
           "radiationEfficiency: non-positive fc is fail-closed (-1)");
    CHECK (RadiationModel::radiationEfficiency (500.0f, fc, 0.0f) < 0.0f,
           "radiationEfficiency: non-positive fga is fail-closed (-1)");

    // ---- Counter-example (docs/workcards/B6.md §7, mandatory) --------------
    // If sigma(f) were mistakenly implemented as the linear ratio f/fc
    // instead of the real (f/fc)^2 subcritical shape, the two disagree by an
    // identifiable amount at f = 0.5*fc: 0.25 (real) vs 0.5 (mutant). This
    // mirrors testBridgeLossSentinel()'s two-round mutant/real pattern
    // (reports/gate_outputs/b1_selftest_sentinel.txt) so a future regression
    // that silently swaps the exponent gets caught.
    const float fHalf = 0.5f * fc;
    const float mutantLinear = fHalf / fc;                                  // WRONG shape
    const float realQuadratic = RadiationModel::radiationEfficiency (fHalf, fc, fga);
    const float delta = std::abs (realQuadratic - mutantLinear);
    std::cout << "[SENTINEL 1/2] mutant (linear f/fc): sigma(0.5*fc)="
              << mutantLinear << " -- if this were the real implementation, "
              << "it would silently disagree with the correct (f/fc)^2 shape\n";
    std::cout << "[SENTINEL 2/2] real radiationEfficiency (quadratic f/fc): "
              << "sigma(0.5*fc)=" << realQuadratic << '\n';
    CHECK (delta > 0.2f,
           "SENTINEL: linear-f/fc mutant is distinguishable from the real "
           "quadratic shape at f=0.5*fc (0.25 vs 0.5, delta=0.25)");
    CHECK (std::abs (realQuadratic - 0.25f) < 1.0e-4f,
           "SENTINEL: real implementation gives the expected (f/fc)^2=0.25 "
           "at f=0.5*fc, not the mutant's 0.5");
}

void testRadiatedPowerChain()
{
    // docs/RADIATION_POWER_SOURCES.md §2.2/§5: eta_rad(f) = rhoAir*cAir*
    // sigma(f) / (omega*rhoS), derived (not literature-verbatim) from the
    // radiation-efficiency definition + the SEA loss-factor definition.
    // Hand-calculated reference point: f=1000 Hz, sigma=1.0 (simplified
    // known condition per B6.md §7), rhoAir=1.2 kg/m^3, cAir=340 m/s,
    // rhoS=3.6 kg/m^2 (typical spruce areal density, same value used in
    // docs/RADIATION_POWER_SOURCES.md §3's table).
    //   omega = 2*pi*1000 = 6283.185307
    //   eta_rad = (1.2*340) / (6283.185307*3.6) = 408 / 22619.46711
    //           = 0.01803736 (hand calc, double precision)
    // Cross-check against the doc's own table: at f=1800 (=fc there),
    // sigma=1 gives eta_rad=0.01002 -- since eta_rad ∝ 1/f at fixed sigma,
    // 0.01002 * (1800/1000) = 0.018036, matching this hand calc to within
    // rounding of the doc table's own 5-significant-figure entries.
    const float f     = 1000.0f;
    const float sigma = 1.0f;
    const float rhoAir = 1.2f;
    const float cAir   = 340.0f;
    const float rhoS   = 3.6f;
    const float expectedEtaRad = 0.0180374f;

    const float etaRad = RadiationModel::radiationLossFactor (f, sigma, rhoAir, cAir, rhoS);
    CHECK (std::abs (etaRad - expectedEtaRad) < 1.0e-4f,
           "radiationLossFactor: matches hand-calculated value at f=1000Hz, "
           "sigma=1 (eta_rad=rhoAir*cAir*sigma/(omega*rhoS))");

    // Sentinel propagation: an invalid (sentinel) sigma must not be silently
    // treated as a real sigma=-1 value plugged into the formula.
    CHECK (RadiationModel::radiationLossFactor (f, -1.0f, rhoAir, cAir, rhoS) < 0.0f,
           "radiationLossFactor: sentinel sigma (-1) propagates to sentinel output");
    CHECK (RadiationModel::radiationLossFactor (f, sigma, rhoAir, cAir, -1.0f) < 0.0f,
           "radiationLossFactor: non-positive rhoS is fail-closed (-1)");

    // ---- Counter-example (docs/workcards/B6.md §7, mandatory): eta_i forced
    // to 0 (soundboard modelled as if ALL of its damping were radiative --
    // the degenerate case docs/RADIATION_POWER_SOURCES.md §5's
    // eta_i(f)=eta_total-eta_rad(f) subtraction hits when eta_total==
    // eta_rad(f)). fraction_radiated must correctly saturate to 1.0, not
    // produce NaN or a divide-by-zero.
    const float etaTotalAllRadiative = etaRad;   // eta_i = etaTotal - etaRad = 0
    const float fraction = RadiationModel::radiatedEnergyFraction (etaRad, etaTotalAllRadiative);
    CHECK (std::isfinite (fraction), "radiatedEnergyFraction: eta_i=0 degenerate case is finite (no NaN/Inf)");
    CHECK (std::abs (fraction - 1.0f) < 1.0e-6f,
           "radiatedEnergyFraction: eta_i=0 (all damping radiative) correctly gives fraction=1.0, not NaN/div-by-zero");

    // Normal case: eta_rad well below a realistic eta_total (0.02, docs/
    // BRIDGE_ADMITTANCE_SOURCES.md §2.1) gives a fraction well below 1, and
    // is fail-closed on non-positive/invalid inputs.
    const float normalFraction = RadiationModel::radiatedEnergyFraction (etaRad, 0.02f);
    CHECK (normalFraction > 0.0f && normalFraction < 1.0f,
           "radiatedEnergyFraction: realistic eta_total=0.02 gives 0 < fraction < 1");
    CHECK (RadiationModel::radiatedEnergyFraction (-1.0f, 0.02f) < 0.0f,
           "radiatedEnergyFraction: sentinel etaRad (-1) propagates to sentinel output");
    CHECK (RadiationModel::radiatedEnergyFraction (etaRad, 0.0f) < 0.0f,
           "radiatedEnergyFraction: non-positive etaTotal is fail-closed (-1)");
}

// ── Absolute calibration (2026-08-28 B6 Phase 3/4) ─────────────────────────
// docs/workcards/B6.md §7 / reports/decision_packets/B6_calibration_choice.md
// "裁決記錄". RadiationModel::pressurePerForce() is a DECIDED CONVENTION
// (kPascalsPerUnitPhysicsAmplitude), not a measured/derived physical law --
// see that constant's doc comment. The "hand calculation" below is therefore
// the definition itself (Pa/N = kPascalsPerUnitPhysicsAmplitude *
// physicsOnlyAmplitude), which is exactly what makes this test meaningful:
// it catches an accidental change to the constant's VALUE or a stray extra
// multiplier creeping in, not a physics-derivation error (there is none to
// check here -- that absence is the whole point of Option B being a
// convention anchor rather than a first-principles chain).
void testPressurePerForceCalibration()
{
    CHECK (std::abs (RadiationModel::kPascalsPerUnitPhysicsAmplitude - 1.0f) < 1.0e-9f,
           "kPascalsPerUnitPhysicsAmplitude is the decided 1.0 Pa-per-unit-"
           "amplitude convention (docs/EXTERNAL_ANCHOR_SOURCES.md §1), unchanged");
    CHECK (std::abs (RadiationModel::kMeasurementRadiusM - 1.05f) < 1.0e-6f,
           "kMeasurementRadiusM matches the 1.05 m anechoic-array convention "
           "(docs/EXTERNAL_ANCHOR_SOURCES.md §1)");

    const float amp = 0.42f;   // arbitrary representative dimensionless amplitude
    const float expected = RadiationModel::kPascalsPerUnitPhysicsAmplitude * amp;
    const float actual = RadiationModel::pressurePerForce (amp);
    CHECK (std::abs (actual - expected) < 1.0e-4f,
           "pressurePerForce: matches the hand-calculated "
           "kPascalsPerUnitPhysicsAmplitude * physicsOnlyAmplitude definition");
    CHECK (std::abs (actual - 0.42f) < 1.0e-4f,
           "pressurePerForce: with the 1.0x convention constant, output equals "
           "the input amplitude numerically (0.42 Pa/N for 0.42 amplitude)");

    // ---- Counter-example (docs/workcards/B6.md §7, mandatory): a mutant
    // that accidentally doubled the calibration constant (e.g. a stray
    // copy-pasted "x2" gain) must be distinguishable from the real 1.0x
    // convention.
    const float mutantDoubledConstant = 2.0f * amp;
    const float delta = std::abs (actual - mutantDoubledConstant);
    std::cout << "[SENTINEL 1/2] mutant (2x calibration constant): "
              << mutantDoubledConstant << " Pa/N -- if "
              << "kPascalsPerUnitPhysicsAmplitude were silently doubled, this "
              << "is what pressurePerForce(0.42) would return instead\n";
    std::cout << "[SENTINEL 2/2] real pressurePerForce(0.42): " << actual << " Pa/N\n";
    CHECK (delta > 0.3f,
           "SENTINEL: a doubled-constant mutant is distinguishable from the "
           "real 1.0x convention (0.42 vs 0.84 Pa/N, delta=0.42)");

    // ---- Pathological counter-example (mirrors testRadiatedPowerChain()'s
    // eta_i=0 degenerate case): a partial with EXACTLY ZERO (or negative)
    // physics-only amplitude -- e.g. a mode-shape node landing exactly on
    // the strike position -- must fail-closed to the sentinel, not silently
    // report a fabricated "0 Pa/N" claim. A real 0 Pa/N would break
    // specimen_verify.py's _complex_level_db() (log10 of zero magnitude,
    // raises ValueError -> the whole bundle REFUSED) instead of cleanly
    // leaving that one partial's acoustic_transfer entry omitted/UNVERIFIED.
    CHECK (RadiationModel::pressurePerForce (0.0f) < 0.0f,
           "pressurePerForce: exactly-zero amplitude fail-closes to the "
           "sentinel (-1), not a fabricated 0 Pa/N that would break "
           "specimen_verify.py's log10-of-zero-magnitude handling");
    CHECK (RadiationModel::pressurePerForce (-0.1f) < 0.0f,
           "pressurePerForce: negative amplitude (structurally should not "
           "happen upstream, but fail-closed anyway) -> sentinel");
    CHECK (RadiationModel::pressurePerForce (std::numeric_limits<float>::quiet_NaN()) < 0.0f,
           "pressurePerForce: NaN amplitude -> sentinel");
    CHECK (RadiationModel::pressurePerForce (std::numeric_limits<float>::infinity()) < 0.0f,
           "pressurePerForce: +infinity amplitude -> sentinel (not a physical value)");
}

// docs/workcards/B6.md §6 step 12 / DiagnosticOverrides::
// capturePhysicsOnlyModes doc: the new B6 Phase 3 diagnostic capture must
// not change ANYTHING CimbalomVoice::noteOn() feeds into ModalResonator --
// i.e. getModes()/getAllStringModes() must be bit-identical whether the
// flag is on or off. This is the unit-level half of §9's bit-identity
// proof; the other half is the full-WAV SHA256 check in
// reports/gate_outputs/b6_bit_identity.txt, which this fast unit test
// cannot substitute for but complements (catches a regression here in
// milliseconds instead of a multi-minute corpus re-render).
void testPhysicsOnlyCaptureDoesNotAffectRender()
{
    MaterialDB::Material mat = steel();
    // Any finite, positive-property material works as the "soundboard" for
    // THIS check -- it is about render-path invariance under the capture
    // flag, not about radiation-model correctness (which testRadiationEfficiencyShape()/
    // testRadiatedPowerChain()/testPressurePerForceCalibration() already
    // cover), so reusing steel() for both arguments is deliberate, not lazy.
    MaterialDB::Material soundboardStub = steel();

    CimbalomParams cp;   // defaults: strike 0.3, Wood exciter, 3 strings, tuneToMidi

    DiagnosticOverrides::capturePhysicsOnlyModes = false;
    CimbalomVoice voiceOff;
    voiceOff.prepare (48000.0);
    voiceOff.noteOn (69, 0.5f, mat, soundboardStub, cp);   // A4, velocity 0.5
    const auto modesOff = voiceOff.getAllStringModes();
    CHECK (voiceOff.getPhysicsOnlyModeAmplitudes().empty(),
           "capturePhysicsOnlyModes=false: getPhysicsOnlyModeAmplitudes() "
           "stays empty (no computation happened, not just an unused result)");

    DiagnosticOverrides::capturePhysicsOnlyModes = true;
    CimbalomVoice voiceOn;
    voiceOn.prepare (48000.0);
    voiceOn.noteOn (69, 0.5f, mat, soundboardStub, cp);
    const auto modesOn = voiceOn.getAllStringModes();
    const auto physicsOnly = voiceOn.getPhysicsOnlyModeAmplitudes();
    DiagnosticOverrides::capturePhysicsOnlyModes = false;   // restore the
        // default for every test that runs after this one in the same binary

    bool identical = modesOff.size() == modesOn.size();
    for (size_t s = 0; identical && s < modesOff.size(); ++s)
    {
        identical = modesOff[s].size() == modesOn[s].size();
        for (size_t i = 0; identical && i < modesOff[s].size(); ++i)
        {
            const auto& a = modesOff[s][i];
            const auto& b = modesOn[s][i];
            identical = (a.frequency == b.frequency)
                     && (a.amplitude == b.amplitude)
                     && (a.decayTime == b.decayTime);
        }
    }
    CHECK (identical,
           "capturePhysicsOnlyModes flag does not change getAllStringModes() "
           "(bit-exact float == comparison) -- the diagnostic capture is "
           "purely additive bookkeeping, never touches what feeds the render path");
    CHECK (! physicsOnly.empty(),
           "capturePhysicsOnlyModes=true: getPhysicsOnlyModeAmplitudes() is "
           "populated for a qualifying (steel string) voice");

    // ---- Counter-example: the physics-only amplitude must NOT equal the
    // render-path amplitude of the SAME partial -- if it did, that would
    // mean spectralTilt/loudnessCompensationGain got applied to the
    // "physics-only" capture too (the exact contamination Option B exists
    // to avoid), or a copy-paste bug aliased the two vectors.
    CHECK (! modesOn.empty() && ! modesOn[0].empty() && ! physicsOnly.empty(),
           "positive control: both vectors are non-empty so the next check "
           "cannot pass vacuously");
    if (! modesOn.empty() && ! modesOn[0].empty() && ! physicsOnly.empty())
    {
        std::cout << "[SENTINEL] render-path amp[0]=" << modesOn[0][0].amplitude
                  << "  physics-only amp[0]=" << physicsOnly[0]
                  << " -- must differ (render path includes "
                  << "loudnessCompensationGain/spectralTilt, physics-only excludes both)\n";
        CHECK (std::abs (modesOn[0][0].amplitude - physicsOnly[0]) > 1.0e-6f,
               "SENTINEL: physics-only amplitude differs from the render-path "
               "amplitude of the same partial (proves the creative-layer "
               "multipliers were actually excluded, not accidentally left in)");
    }
}

// ── String damping first principles (2026-08-24 B3) ───────────────────────
// docs/workcards/B3.md §7. Reference numbers are copied from
// docs/STRING_DAMPING_SOURCES.md §4.1 (Cuesta & Valette cello D-string,
// rigid-mount measurement reproduced by that document), NOT derived
// independently here.

void testStringDampingFirstPrinciples()
{
    // §7-2: Cuesta & Valette cello D-string reference. Parameters verbatim
    // from STRING_DAMPING_SOURCES.md §4.1: rho=5535, r=4.55e-4, T=147.7,
    // E=2.5e10. Q = 1/(Qinv_air+Qinv_visc+Qinv_disl) must match the table's
    // Q column at all four frequencies within 1% relative.
    MaterialDB::Material cello;
    cello.displayName = "Cuesta-Valette cello D-string stub";
    cello.density = 5535.0f;
    cello.youngsModulus = 2.5e10f;
    cello.poissonRatio = 0.30f;   // not read by stringAirViscDislQInv
    const float rCello = 4.55e-4f;
    const float tCello = 147.7f;

    struct QRef { float f; float q; };
    static constexpr QRef refs[] = {
        { 147.0f,   3629.0f },
        { 1000.0f,  6787.0f },
        { 4000.0f,  2817.0f },
        { 10000.0f, 580.0f },
    };
    for (const auto& ref : refs)
    {
        const float qInv = StringModel::stringAirViscDislQInv (
            ref.f, rCello, tCello, cello);
        const float q = 1.0f / qInv;
        std::cout << "       (Cuesta ref f=" << ref.f << "Hz: Q=" << q
                  << " vs table " << ref.q << ")\n";
        CHECK (qInv > 0.0f && std::abs (q / ref.q - 1.0f) < 0.01f,
               "String air+visc+dislocation Q matches Cuesta & Valette cello D-string reference");
    }

    // §7-2 counter-example (sentinel/mutant): the SAME reference values must
    // NOT be reproduced when the viscoelastic term's r^6 is miscopied as r^2
    // -- proving the 1% check above really pins the power law, not just the
    // order of magnitude. The broken version is simulated inline (same
    // pattern as testBridgeLossSentinel: production code is NOT mutated, so
    // the suite's PASS/FAIL count stays honest). Console output is archived
    // at reports/gate_outputs/b3_selftest_sentinel.txt together with a real
    // two-run mutation demonstration (docs/workcards/B3.md §7).
    auto mutantQInvR2 = [&] (float frequency)
    {
        const float omega = juce::MathConstants<float>::twoPi * frequency;
        const float M = (rCello * 0.5f)
            * std::sqrt (omega / StringModel::kAirKinematicViscosity);
        const float qInvAir = (StringModel::kAirDensity / cello.density)
            * (std::sqrt (2.0f) / M + 1.0f / (2.0f * M * M));
        const float qInvViscBroken = 0.003f * cello.youngsModulus * cello.density
            * juce::MathConstants<float>::pi * juce::MathConstants<float>::pi
            * std::pow (rCello, 2.0f)   // DELIBERATE mutant: r^2 instead of r^6
            * omega * omega / (4.0f * tCello * tCello);
        return qInvAir + qInvViscBroken + StringModel::kDislocationQInv;
    };
    for (const auto& ref : refs)
    {
        const float qBroken = 1.0f / mutantQInvR2 (ref.f);
        const float deviation = std::abs (qBroken / ref.q - 1.0f);
        std::cout << "[SENTINEL r^6->r^2 mutant] f=" << ref.f << "Hz: Q="
                  << qBroken << " vs table " << ref.q << " (deviation "
                  << deviation * 100.0f << "% -- same 1% criterion would report: "
                  << (deviation < 0.01f ? "[PASS] (BAD -- no detection power)"
                                        : "[FAIL] (GOOD -- power law checked)")
                  << ")\n";
        CHECK (deviation > 0.10f,
               "SENTINEL: r^2 mutant misses the Cuesta reference by far more than 10% "
               "(the 1% reference test really checks the r^6 power law)");
    }

    // §7-3: regression guard against the retired beta_air*f^2 shape. Compare
    // the 1/T60 contribution (= qInv*f/2.2) at f and 2f in the air-dominated
    // low band: the OLD beta_air*f^2 term would scale by exactly 4; the new
    // first-principles sum must land near the sqrt(2)..2 band instead
    // (air sqrt(2)/M part -> sqrt(2), air 1/(2M^2) part -> 1, dislocation
    // -> 2, viscoelastic negligible at 100 Hz; STRING_DAMPING_SOURCES.md §3).
    const float rate100 = StringModel::stringAirViscDislQInv (
                              100.0f, rCello, tCello, cello)
                          * 100.0f / MaterialDB::kEtaToDecayRate;
    const float rate200 = StringModel::stringAirViscDislQInv (
                              200.0f, rCello, tCello, cello)
                          * 200.0f / MaterialDB::kEtaToDecayRate;
    const float octaveRatio = rate200 / rate100;
    std::cout << "       (air-band 1/T60 octave ratio: " << octaveRatio
              << "; old f^2 shape would give 4.0)\n";
    CHECK (std::abs (octaveRatio - 4.0f) > 1.5f,
           "Air term is not proportional to f^2 (regression guard against the old shape)");
    CHECK (octaveRatio > 1.40f && octaveRatio < 2.0f,
           "Low-band 1/T60 octave ratio sits in the physical sqrt(2)..2 band");

    // Fail-closed behavior: invalid geometry/tension contributes 0, never
    // NaN/Inf/negative (mirrors bridgeLossRate's convention).
    CHECK (StringModel::stringAirViscDislQInv (440.0f, 0.0f, tCello, cello) == 0.0f,
           "stringAirViscDislQInv fail-closed: radius=0 -> 0.0f");
    CHECK (StringModel::stringAirViscDislQInv (440.0f, -1.0e-4f, tCello, cello) == 0.0f,
           "stringAirViscDislQInv fail-closed: negative radius -> 0.0f");
    CHECK (StringModel::stringAirViscDislQInv (440.0f, rCello, 0.0f, cello) == 0.0f,
           "stringAirViscDislQInv fail-closed: tension=0 -> 0.0f");
    CHECK (StringModel::stringAirViscDislQInv (
               440.0f, rCello, std::numeric_limits<float>::quiet_NaN(), cello) == 0.0f,
           "stringAirViscDislQInv fail-closed: non-finite tension -> 0.0f");
    CHECK (StringModel::stringAirViscDislQInv (0.0f, rCello, tCello, cello) == 0.0f,
           "stringAirViscDislQInv fail-closed: frequency=0 -> 0.0f");
    // Positive control so the fail-closed checks cannot pass vacuously.
    CHECK (StringModel::stringAirViscDislQInv (440.0f, rCello, tCello, cello) > 0.0f,
           "stringAirViscDislQInv positive control: valid inputs give a positive Q^-1");
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

// B4 (2026-08-27): piano felt-hammer nonlinear contact solver
// (docs/workcards/B4.md §7, sources docs/HAMMER_CONTACT_SOURCES.md §2-§3).
void testPianoHammerContactSolver()
{
    // §6 step 1 hand-check, frozen as regression checks: the three K/alpha
    // anchors (C2/C4/C7) reproduce the literature table exactly, and the
    // out-of-range notes (C1/C8) flat-clamp to the nearest anchor.
    CHECK (HammerImpulse::alphaForPianoNote (36) == 2.3f
           && HammerImpulse::alphaForPianoNote (60) == 2.5f
           && HammerImpulse::alphaForPianoNote (96) == 3.0f,
           "alpha(C2/C4/C7) reproduce the Euphonics Table 2 anchors exactly");
    CHECK (std::abs (HammerImpulse::logKForPianoNote (36) / 4.0e8f - 1.0f) < 1.0e-4f
           && std::abs (HammerImpulse::logKForPianoNote (60) / 4.5e9f - 1.0f) < 1.0e-4f
           && std::abs (HammerImpulse::logKForPianoNote (96) / 1.0e12f - 1.0f) < 1.0e-4f,
           "K(C2/C4/C7) reproduce the Euphonics Table 2 anchors (rel < 1e-4)");
    CHECK (HammerImpulse::hammerMassForPianoNote (24) == 0.012f
           && HammerImpulse::hammerMassForPianoNote (60) == 0.009f
           && HammerImpulse::hammerMassForPianoNote (108) == 0.005f,
           "hammer mass reproduces the C1/C4/C8 Table 1 anchors exactly");

    // §7.1 anchor reproduction: the solved tau_c is anchored at A4/v=0.5 to
    // the existing Askenfelt & Jansson felt value, so it must reproduce it.
    CHECK (std::abs (HammerImpulse::pianoHammerTauC (69, 0.5f)
                     - HammerImpulse::kTauCFelt) < 1.0e-4f,
           "pianoHammerTauC(A4, v=0.5) reproduces kTauCFelt (anchor point)");

    // §7.2 velocity directionality: faster strike -> shorter contact.
    CHECK (HammerImpulse::pianoHammerTauC (60, 0.9f)
           < HammerImpulse::pianoHammerTauC (60, 0.1f),
           "Solved contact time shortens at higher strike velocity");

    // §7.3 velocity-exponent magnitude at the three anchors (pure algebra,
    // no rendering): log(tau(v2)/tau(v1))/log(v2/v1) must approach the
    // derived exponents 2/(alpha+1)-1 = -0.394 / -0.429 / -0.500
    // (HAMMER_CONTACT_SOURCES.md §3 table) within 1e-3. v in [0.2, 0.8]
    // keeps every tau inside the [0.3ms, 8ms] safety clamp (verified below)
    // so the clamp cannot flatten the measured slope.
    {
        const int   anchorMidi[3]  = { 36, 60, 96 };
        const float expectedExp[3] = { -0.394f, -0.429f, -0.500f };
        bool slopesOk = true;
        bool unclamped = true;
        for (int i = 0; i < 3; ++i)
        {
            const float v1 = 0.2f, v2 = 0.8f;
            const float t1 = HammerImpulse::pianoHammerTauC (anchorMidi[i], v1);
            const float t2 = HammerImpulse::pianoHammerTauC (anchorMidi[i], v2);
            unclamped = unclamped
                && t1 > HammerImpulse::kPianoTauCMinS && t1 < HammerImpulse::kPianoTauCMaxS
                && t2 > HammerImpulse::kPianoTauCMinS && t2 < HammerImpulse::kPianoTauCMaxS;
            const double slope = std::log ((double) t2 / (double) t1)
                               / std::log ((double) v2 / (double) v1);
            slopesOk = slopesOk && std::abs (slope - (double) expectedExp[i]) < 1.0e-3;
            std::cout << "       velocity exponent @ MIDI " << anchorMidi[i]
                      << ": " << slope << " (expected " << expectedExp[i] << ")\n";
        }
        CHECK (unclamped,
               "Anchor-note tau_c values stay strictly inside the safety clamp");
        CHECK (slopesOk,
               "Velocity exponents at C2/C4/C7 match -0.394/-0.429/-0.500 (< 1e-3)");
    }

    // A14 B-2 (2026-09-09): pitch shape re-anchored to the measured
    // keytrackScale() curve, replacing the K/alpha/mass-derived pitch shape
    // (reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md
    // §3.2-3.5, §4 option B; docs/workcards/WF0908_P2_a14_tauc_rule10.md).
    //   tau_c_piano(note, v) = kTauCFelt * keytrackScale(note)
    //                        * [ g(note, v) / g(note, 0.5) ]

    // §A14-1: A4/v=0.5 anchor still reproduces kTauCFelt exactly
    // (keytrackScale(69)=1, g(69,0.5)/g(69,0.5)=1) -- restated here for
    // locality with the rest of the A14 B-2 checks (already covered above).
    CHECK (std::abs (HammerImpulse::pianoHammerTauC (69, 0.5f)
                     - HammerImpulse::kTauCFelt) < 1.0e-4f,
           "A14 B-2: A4/v=0.5 anchor unchanged after re-anchoring pitch shape");

    // §A14-2: C8 (MIDI 108) tau_c must drop under 1 ms at v=0.5, matching the
    // literature range cited in keytrackScale()'s doc comment (Askenfelt &
    // Jansson: A0 ~4 ms -> C8 <1 ms). Before this fix the B4-only pitch
    // shape gave C8 ~1.46 ms (A14 report §3.3).
    {
        const float tauC8 = HammerImpulse::pianoHammerTauC (108, 0.5f);
        CHECK (tauC8 < 0.001f,
               "A14 B-2: C8 tau_c < 1 ms at v=0.5 (was ~1.46 ms pre-fix)");
        std::cout << "       C8 tau_c @ v=0.5 = " << (tauC8 * 1000.0f) << " ms\n";
    }

    // §A14-3: the equivalent keytrack exponent over C2->C7, computed the same
    // way A14 report §3.3 computes it (k = -log(tauC7/tauC2)/log(f7/f2) at
    // fixed velocity), must land at keytrackScale()'s own k=0.32 (+/-0.01) --
    // pitch shape now comes entirely from keytrackScale(), so this should
    // reproduce it exactly modulo float rounding.
    {
        const float v = 0.5f;
        const float tauC2 = HammerImpulse::pianoHammerTauC (36, v);
        const float tauC7 = HammerImpulse::pianoHammerTauC (96, v);
        const float f2 = 440.0f * std::pow (2.0f, (36 - 69) / 12.0f);
        const float f7 = 440.0f * std::pow (2.0f, (96 - 69) / 12.0f);
        const double k = -std::log ((double) tauC7 / (double) tauC2)
                        / std::log ((double) f7 / (double) f2);
        CHECK (std::abs (k - 0.32) < 0.01,
               "A14 B-2: C2->C7 equivalent keytrack exponent k = 0.32 +/- 0.01");
        std::cout << "       C2->C7 equivalent k = " << k << " (expected 0.32)\n";
    }

    // §A14-4: velocity law at fixed pitch must stay numerically bit-equivalent
    // to B4's -- keytrackScale(note) is velocity-independent and cancels in
    // the ratio new(note,v)/new(note,0.5), which reduces to exactly the same
    // g(note,v)/g(note,0.5) that B4's old formula's ratio also reduced to
    // (workcard §3 step 2). This is a unit-test numeric-equivalence check,
    // not a §6-registered tolerance (R2).
    {
        const int   notes[] = { 36, 60, 69, 96 };
        const float vs[]    = { 0.2f, 0.35f, 0.65f, 0.9f };
        bool allOk = true;
        for (int note : notes)
        {
            for (float v : vs)
            {
                const double ratioNew = (double) HammerImpulse::pianoHammerTauC (note, v)
                                       / (double) HammerImpulse::pianoHammerTauC (note, 0.5f);
                const double ratioG   = (double) HammerImpulse::pianoHammerG (note, v)
                                       / (double) HammerImpulse::pianoHammerG (note, 0.5f);
                const double rel = std::abs (ratioNew - ratioG)
                                  / std::max (std::abs (ratioG), 1e-12);
                allOk = allOk && rel < 1.0e-6;
            }
        }
        CHECK (allOk,
               "A14 B-2: velocity law at fixed pitch bit-equivalent to B4 (rel < 1e-6)");
    }

    // §7.4 interpolation monotonicity: alpha(note) non-decreasing across the
    // full anchored span (the documented physical ordering, sources §2.1).
    {
        bool monotone = true;
        for (int midi = 36; midi < 96; ++midi)
            monotone = monotone && HammerImpulse::alphaForPianoNote (midi + 1)
                                   >= HammerImpulse::alphaForPianoNote (midi);
        CHECK (monotone, "alphaForPianoNote is non-decreasing over MIDI 36..96");
    }

    // §7.5 flat extrapolation at the boundaries (no linear extrapolation
    // beyond the measured anchors) for all three interpolated tables.
    CHECK (HammerImpulse::alphaForPianoNote (24) == HammerImpulse::alphaForPianoNote (36)
           && HammerImpulse::alphaForPianoNote (108) == HammerImpulse::alphaForPianoNote (96),
           "alpha flat-clamps outside the C2..C7 anchor range");
    CHECK (HammerImpulse::logKForPianoNote (24) == HammerImpulse::logKForPianoNote (36)
           && HammerImpulse::logKForPianoNote (108) == HammerImpulse::logKForPianoNote (96),
           "K flat-clamps outside the C2..C7 anchor range");
    CHECK (HammerImpulse::hammerMassForPianoNote (12) == HammerImpulse::hammerMassForPianoNote (24)
           && HammerImpulse::hammerMassForPianoNote (120) == HammerImpulse::hammerMassForPianoNote (108),
           "hammer mass flat-clamps outside the C1..C8 anchor range");

    // §7.6 counterexample (required): if the interpolation were miscoded as
    // linear-in-K (instead of linear-in-log10(K)) the C2->C7 midpoint
    // (MIDI 66, inside the C4->C7 segment) would land more than an order of
    // magnitude away -- K spans 3 decades, so this regression pins the
    // easiest-to-make mistake as a hard FAIL.
    {
        const float kCorrect = HammerImpulse::logKForPianoNote (66);
        // wrong version: linear interpolation on K itself over the SAME
        // containing segment (C4 = MIDI 60 -> C7 = MIDI 96) the correct
        // implementation uses.
        const float t = (66.0f - 60.0f) / (96.0f - 60.0f);
        const float kWrongLinear = 4.5e9f + (1.0e12f - 4.5e9f) * t;
        // correct value per §4.2: 10^(log10(4.5e9) + t*(12 - log10(4.5e9)))
        const double kExpected = std::pow (10.0, std::log10 (4.5e9)
                                     + (double) t * (12.0 - std::log10 (4.5e9)));
        CHECK (std::abs (kCorrect / (float) kExpected - 1.0f) < 1.0e-3f,
               "K(MIDI 66) matches the hand-computed log-domain interpolation");
        CHECK (kWrongLinear / kCorrect > 10.0f,
               "Linear-in-K miscoding differs from log-domain result by >1 order of magnitude");
    }

    // §7.7 Felt-branch predicate boundaries: exactly the expressions used in
    // CimbalomEngine.h. startNote(): std::round(hammer) == 1.0f (continuous
    // 0..3 knob, Felt detent +/-0.5); noteOn(): hammerIdx == 1 (exact enum
    // int). Non-Felt detents (0/2/3 and fractional values rounding to them,
    // e.g. 1.6) must NOT trigger the new solver.
    {
        auto feltPluginPath = [] (float hammer) { return std::round (hammer) == 1.0f; };
        CHECK (! feltPluginPath (0.0f) && ! feltPluginPath (2.0f)
               && ! feltPluginPath (3.0f) && ! feltPluginPath (1.6f)
               && ! feltPluginPath (0.4f) && ! feltPluginPath (2.4f),
               "Non-Felt hardness values (0/2/3, 1.6, 0.4, 2.4) do not select the solver");
        CHECK (feltPluginPath (1.0f) && feltPluginPath (0.6f) && feltPluginPath (1.4f),
               "Felt detent (1.0 and +/-0.4 neighbourhood) selects the solver");
        auto feltScorePath = [] (int hammerIdx) { return hammerIdx == 1; };
        CHECK (! feltScorePath (0) && feltScorePath (1)
               && ! feltScorePath (2) && ! feltScorePath (3),
               "Score-path exact enum: only ExciterType::Felt (1) selects the solver");
    }
}

// ── B7 Phase 1 (WF0914-B7P1, docs/workcards/B7.md §7) ──────────────────────
// First-principles force chain: velocity -> real hammer speed -> Hertz peak
// force -> real modal energy -> bridge power. §1.2 "否" branch (see
// RadiationModel::bridgePowerFirstPrinciples()'s doc comment): the current
// soundboard params are not traceable to the same measured instrument as
// S's only usable literature value, so the chain stops at W_bridge(f) --
// tests 4/5 below are therefore adapted from B7.md §7's literal wording
// (which assumes a "sigma(f)"/"S" continuation that this card's Phase 1
// does not build) into equivalent sentinels on W_bridge(f) itself, per the
// workcard's explicit "否" branch instruction. This is documented here and
// in the WF0914-B7P1 completion report, not silently substituted.

// §7 item 1: velocity-mapping range + monotonicity.
void testHammerVelocityMps()
{
    // Exact anchors (formula gives an exact power of 2 at these two points):
    // MIDI 52 -> 2^0 = 1.0 m/s; MIDI 77 -> 2^1 = 2.0 m/s (matches the Goebl &
    // Bresin (2003) "77 MIDI velocity units -> 2 m/s" anchor exactly, see
    // docs/HAMMER_VELOCITY_SOURCES.md §2).
    CHECK (std::abs (HammerImpulse::hammerVelocityMps (52.0f) - 1.0f) < 1.0e-5f,
           "hammerVelocityMps(52) == 1.0 m/s exactly (2^0)");
    CHECK (std::abs (HammerImpulse::hammerVelocityMps (77.0f) - 2.0f) < 1.0e-4f,
           "hammerVelocityMps(77) == 2.0 m/s (Goebl & Bresin 2003 anchor)");

    // Cross-check against docs/HAMMER_VELOCITY_SOURCES.md §2's own "A12
    // cross-check" table (transcribed from B7_PHASE0_DATA, hand-verifiable
    // by the closed-form formula -- reproduced here as an independent check
    // on the IMPLEMENTATION, not a re-derivation of the source numbers).
    // Note: MIDI 127 is deliberately excluded here -- it falls inside this
    // function's own ">120" domain clamp (see below), so it returns the
    // clamped 6.8 m/s, not the raw formula's 8.0 m/s docs/
    // HAMMER_VELOCITY_SOURCES.md §2 quotes for the UNCLAMPED formula value
    // at that point (used there to show the 18% overshoot the clamp exists
    // to correct, not as this function's own return value).
    struct { float midi, expectedMps; } anchors[] = {
        { 40.0f, 0.717f }, { 60.0f, 1.248f }, { 110.0f, 4.993f }
    };
    bool anchorsOk = true;
    for (const auto& a : anchors)
    {
        const float got = HammerImpulse::hammerVelocityMps (a.midi);
        anchorsOk = anchorsOk && std::abs (got - a.expectedMps) < 1.0e-3f;
        std::cout << "       hammerVelocityMps(" << a.midi << ") = " << got
                  << " (expected " << a.expectedMps << ")\n";
    }
    CHECK (anchorsOk, "hammerVelocityMps matches docs/HAMMER_VELOCITY_SOURCES.md "
                       "§2's A12 cross-check table within 1e-3");

    // Domain clamp: MIDI < 20 -> 0.18 m/s flat, MIDI > 120 -> 6.8 m/s flat
    // (the two measured extremes, docs/HAMMER_VELOCITY_SOURCES.md §3(2)/§4
    // -- the formula itself is known to overshoot outside this range).
    CHECK (HammerImpulse::hammerVelocityMps (19.9f) == 0.18f
           && HammerImpulse::hammerVelocityMps (0.0f) == 0.18f
           && HammerImpulse::hammerVelocityMps (-50.0f) == 0.18f,
           "hammerVelocityMps: MIDI < 20 clamps flat to the measured minimum 0.18 m/s");
    CHECK (HammerImpulse::hammerVelocityMps (120.1f) == 6.8f
           && HammerImpulse::hammerVelocityMps (127.0f + 1.0f) == 6.8f
           && HammerImpulse::hammerVelocityMps (300.0f) == 6.8f,
           "hammerVelocityMps: MIDI > 120 clamps flat to the measured maximum 6.8 m/s");
    // Domain boundary itself uses the formula, not the clamp (MIDI 120 -> 6.59, not 6.8).
    CHECK (HammerImpulse::hammerVelocityMps (120.0f) < 6.8f
           && HammerImpulse::hammerVelocityMps (120.0f) > 6.0f,
           "hammerVelocityMps: MIDI == 120 (boundary) still uses the formula, not the clamp");

    // Monotonicity across the full domain, clamp included.
    bool monotone = true;
    float prev = HammerImpulse::hammerVelocityMps (0.0f);
    for (float midi = 1.0f; midi <= 127.0f; midi += 1.0f)
    {
        const float cur = HammerImpulse::hammerVelocityMps (midi);
        monotone = monotone && cur >= prev;
        prev = cur;
    }
    CHECK (monotone, "hammerVelocityMps is non-decreasing over MIDI 0..127 "
                      "(clamp + formula together)");

    // Fail-closed on non-finite input.
    CHECK (HammerImpulse::hammerVelocityMps (std::numeric_limits<float>::quiet_NaN()) < 0.0f,
           "hammerVelocityMps: NaN input is fail-closed (-1)");
    CHECK (HammerImpulse::hammerVelocityMps (std::numeric_limits<float>::infinity()) < 0.0f,
           "hammerVelocityMps: +Inf input is fail-closed (-1)");
}

// §7 item 2: peak-force energy-conservation self-consistency (numerical
// integration, not a hand-picked closed-form reference -- the derivation
// itself (docs/workcards/B7.md §4.3) IS the energy-conservation identity,
// so checking hertzPeakForceNewtons()'s own delta_max/F_peak against a
// numerically-integrated contact work is the correct self-consistency
// check, matching B7.md §7 item 2's literal instruction).
void testHertzPeakForceEnergyConservation()
{
    const int   notes[]  = { 36, 60, 96 };     // C2 / C4 / C7 anchors (B4)
    const float speeds[] = { 0.3f, 1.25f, 4.0f };
    bool allConverge = true;
    for (int ni = 0; ni < 3; ++ni)
    {
        const int   note = notes[ni];
        const float v    = speeds[ni];
        const float alpha = HammerImpulse::alphaForPianoNote (note);
        const float K     = HammerImpulse::logKForPianoNote (note);
        const float m     = HammerImpulse::hammerMassForPianoNote (note);
        const float fPeak = HammerImpulse::hertzPeakForceNewtons (note, v);
        CHECK (fPeak > 0.0f, "hertzPeakForceNewtons: positive output for a valid input");

        // delta_max recovered algebraically from F_peak = K*delta_max^alpha
        // (double precision, independent of the implementation's own
        // internal delta_max local).
        const double deltaMax = std::pow ((double) fPeak / (double) K, 1.0 / (double) alpha);

        // Simpson's rule, 4000 sub-intervals, of integral_0^deltaMax K*x^alpha dx.
        const int N = 4000;
        const double h = deltaMax / N;
        auto integrand = [&] (double x) { return (double) K * std::pow (x, (double) alpha); };
        double integral = integrand (0.0) + integrand (deltaMax);
        for (int i = 1; i < N; ++i)
            integral += (i % 2 == 0 ? 2.0 : 4.0) * integrand (i * h);
        integral *= h / 3.0;

        const double kineticEnergy = 0.5 * (double) m * (double) v * (double) v;
        const double relError = std::abs (integral - kineticEnergy)
                               / std::max (kineticEnergy, 1e-30);
        allConverge = allConverge && relError < 1.0e-3;
        std::cout << "       MIDI " << note << " v=" << v
                  << " m/s: integral(K*delta^alpha, 0..deltaMax)=" << integral
                  << " J, (1/2)*m*v^2=" << kineticEnergy
                  << " J, rel error=" << relError << "\n";
    }
    CHECK (allConverge,
           "hertzPeakForceNewtons: numerically-integrated contact work matches "
           "(1/2)*m*v^2 within 1e-3 relative error at C2/C4/C7 (B7.md §7 item 2)");

    // Fail-closed on non-finite / non-positive speed.
    CHECK (HammerImpulse::hertzPeakForceNewtons (60, 0.0f) < 0.0f,
           "hertzPeakForceNewtons: zero speed is fail-closed (-1)");
    CHECK (HammerImpulse::hertzPeakForceNewtons (60, -1.0f) < 0.0f,
           "hertzPeakForceNewtons: negative speed is fail-closed (-1)");
    CHECK (HammerImpulse::hertzPeakForceNewtons (60, std::numeric_limits<float>::quiet_NaN()) < 0.0f,
           "hertzPeakForceNewtons: NaN speed is fail-closed (-1)");

    // Directionality: faster strike -> larger peak force (monotone in v),
    // same note.
    CHECK (HammerImpulse::hertzPeakForceNewtons (60, 4.0f)
           > HammerImpulse::hertzPeakForceNewtons (60, 0.5f),
           "hertzPeakForceNewtons: larger speed gives larger peak force (same note)");
}

// §7 item 3 (mandatory counter-example): a mutant delta_max that forgets to
// multiply by (alpha+1) must be distinguishable from the real implementation.
void testHertzPeakForceCounterexample()
{
    const int   note = 60;   // C4: alpha=2.5, K=4.5e9, m=0.009 kg
    const float v    = 1.25f;
    const float alpha = HammerImpulse::alphaForPianoNote (note);
    const float K      = HammerImpulse::logKForPianoNote (note);
    const float m       = HammerImpulse::hammerMassForPianoNote (note);

    const float realFPeak = HammerImpulse::hertzPeakForceNewtons (note, v);

    // Mutant: delta_max_wrong = [ m*v^2 / (2*K) ] ^ (1/(alpha+1))  -- missing
    // the (alpha+1) factor docs/workcards/B7.md §4.3's derivation requires.
    const float deltaMaxWrong = std::pow (
        m * v * v / (2.0f * K), 1.0f / (alpha + 1.0f));
    const float fPeakWrong = K * std::pow (deltaMaxWrong, alpha);

    const double ratio = (double) fPeakWrong / (double) realFPeak;
    std::cout << "[SENTINEL 1/2] mutant (missing (alpha+1) factor): F_peak="
              << fPeakWrong << " N -- if delta_max forgot to multiply by "
              << "(alpha+1), this is what hertzPeakForceNewtons(60, 1.25) "
              << "would return instead\n";
    std::cout << "[SENTINEL 2/2] real hertzPeakForceNewtons(60, 1.25): "
              << realFPeak << " N (ratio mutant/real = " << ratio << ")\n";
    // (alpha+1)=3.5 missing inside a ^(1/(alpha+1))=^(1/3.5) power law is a
    // large, easily-distinguishable multiplicative gap, not a rounding-level
    // difference -- assert at least 2x apart (order-of-magnitude margin,
    // not a new GATE tolerance, same style as testRadiationEfficiencyShape()'s
    // "delta > 0.2f" sentinel margin).
    CHECK (ratio < 0.5 || ratio > 2.0,
           "SENTINEL: delta_max mutant missing the (alpha+1) factor gives a "
           "F_peak at least 2x away from the real implementation");
}

// §7 items 4/5 ("否" branch adaptation, see the section-header comment
// above, UPDATED 2026-09-14 audit fix): item 5 still has no
// acoustic_transfer/acoustic_transfer_c JSON-field comparison to make
// (neither key exists in this "否"-branch build), so testPathBAndPathCDoNotInterfere()
// below keeps its pure-function-level adaptation. Item 4 ORIGINALLY had no
// W_rad<=W_bridge inequality available either (no S/sigma(f)) and was
// adapted down to scale-law/non-negativity sentinels only -- the audit
// (2026-09-14) correctly flagged that this dropped the one conservation
// check that WAS available and load-bearing: the assembled impulse
// feeding modalEnergyFirstPrinciples() has a hard physical ceiling, 2*m*v
// (the elastic-collision momentum bound), regardless of S/sigma(f). That
// check is now present below (the "GENUINE conservation check" block) and
// is what actually caught -- and, after the fix, verifies the repair of --
// the WF0914-B7P1 impulse/energy-conservation violation.

void testBridgePowerFirstPrinciplesChain()
{
    // Hand-calculated reference point, chosen so the half-sine spectrum's
    // pi/4 removable-singularity value (already verified independently by
    // testHammerSpectrum() above) makes the arithmetic exact:
    //   fPeakN=40 N, tauCS=0.002 s, fHz = 1/(2*tauCS) = 250 Hz
    //     -> forceSpectrumMagnitude(2*pi*250, 0.002) == pi/4 (the "turning"
    //        point, see testHammerSpectrum()).
    //   impulseDC = fPeakN*tauCS*(2/pi) = 40*0.002*(2/pi) = 0.08*(2/pi)
    //   impulseAtOmega = impulseDC * (pi/4) * excitationWeight(=1)
    //                  = 40*0.002*(2/pi)*(pi/4) = 40*0.002*0.5 = 0.04 N*s
    //     (the pi cancels exactly -- (2/pi)*(pi/4) = 1/2)
    //   E_mode = 0.04^2 / (2*0.001) = 0.0016/0.002 = 0.8 J
    //   W_bridge = 2*alphaBridge*E_mode = 2*5.0*0.8 = 8.0 W
    const float fPeakN = 40.0f, tauCS = 0.002f;
    const float fHz = 1.0f / (2.0f * tauCS);   // 250 Hz
    const float modalMassKg = 0.001f;
    const float excitationWeight = 1.0f;
    const float alphaBridge = 5.0f;

    const float eMode = RadiationModel::modalEnergyFirstPrinciples (
        fPeakN, tauCS, fHz, modalMassKg, excitationWeight);
    CHECK (std::abs (eMode - 0.8f) < 1.0e-3f,
           "modalEnergyFirstPrinciples: matches the hand-calculated 0.8 J "
           "reference point (uses forceSpectrumMagnitude's exact pi/4 value)");
    std::cout << "       E_mode(hand-calc reference) = " << eMode << " J (expected 0.8)\n";

    const float wBridge = RadiationModel::bridgePowerFirstPrinciples (alphaBridge, eMode);
    CHECK (std::abs (wBridge - 8.0f) < 1.0e-2f,
           "bridgePowerFirstPrinciples: matches the hand-calculated 8.0 W "
           "reference point (W_bridge = 2*alpha_bridge*E_mode)");
    std::cout << "       W_bridge(hand-calc reference) = " << wBridge << " W (expected 8.0)\n";

    // Physical-sanity monotonicity (adapted "conservation" check per the
    // "否" branch note above: with no S/sigma(f) continuation there is no
    // W_rad to bound W_bridge by, so this checks the physically-required
    // relationships W_bridge(f) itself must obey instead): E_mode ~
    // impulse^2, so doubling fPeakN (all else fixed) should ~4x E_mode and
    // therefore ~4x W_bridge.
    const float eModeDoubled = RadiationModel::modalEnergyFirstPrinciples (
        2.0f * fPeakN, tauCS, fHz, modalMassKg, excitationWeight);
    const float wBridgeDoubled = RadiationModel::bridgePowerFirstPrinciples (
        alphaBridge, eModeDoubled);
    CHECK (std::abs (wBridgeDoubled / wBridge - 4.0f) < 1.0e-2f,
           "bridgePowerFirstPrinciples: doubling F_peak quadruples W_bridge "
           "(E_mode ~ impulse^2 ~ F_peak^2, physical-sanity check replacing "
           "the W_rad<=W_bridge conservation inequality this '否' branch "
           "does not build)");

    // Non-negativity across a spread of physically plausible inputs.
    bool allNonNegative = true;
    for (float fp : { 5.0f, 40.0f, 200.0f })
        for (float tc : { 0.0003f, 0.002f, 0.006f })
            for (float f : { 50.0f, 440.0f, 4000.0f })
            {
                const float e = RadiationModel::modalEnergyFirstPrinciples (
                    fp, tc, f, modalMassKg, excitationWeight);
                allNonNegative = allNonNegative && e >= 0.0f;
                if (e >= 0.0f)
                {
                    const float w = RadiationModel::bridgePowerFirstPrinciples (alphaBridge, e);
                    allNonNegative = allNonNegative && w >= 0.0f;
                }
            }
    CHECK (allNonNegative,
           "modalEnergyFirstPrinciples/bridgePowerFirstPrinciples: never "
           "negative across a spread of physically plausible (F_peak, tauC, f) inputs");

    // §7 item 4, GENUINE conservation check (audit fix, 2026-09-14 --
    // replaces the mutation-sentinel-only version this test previously had
    // in that slot; the "否" branch note above still stands for why there
    // is no W_rad<=W_bridge INEQUALITY to check (no S/sigma(f)), but the
    // workcard's own physical-necessity language ("任何一組合法輸入都要
    // 滿足") has a directly available equivalent that DOES apply here: the
    // assembled impulse feeding modalEnergyFirstPrinciples() can never
    // physically exceed the hammer's own momentum change for a
    // dissipation-free Hertzian collision, 2*m*v (see
    // HammerImpulse::hertzImpulseConsistentTauCSeconds()'s doc comment for
    // the derivation). This is checked here using the REAL production
    // functions end-to-end (HammerImpulse::hammerVelocityMps() with real
    // MIDI velocity input directly -- bypassing the score `velocity`
    // proxy question entirely, which is orthogonal to this chain's own
    // internal self-consistency), across the SAME 24+ -point domain the
    // audit finding scanned (MIDI 36/48/60/72/84/96 x a spread of real
    // MIDI velocities): before the fix, every one of these failed by
    // 2.55-4.32x (reusing HammerImpulse::pianoHammerTauC() for tauC); with
    // the fix, all must hold to float precision.
    {
        const int   testNotes[]  = { 36, 48, 60, 72, 84, 96 };
        const float testMidiVels[] = { 20.0f, 40.0f, 60.0f, 77.0f, 90.0f, 110.0f, 120.0f };
        bool allWithinBound = true;
        bool allSelfConsistent = true;
        double worstRatioToBound = 0.0;
        for (int note : testNotes)
        {
            for (float midiVel : testMidiVels)
            {
                const float v     = HammerImpulse::hammerVelocityMps (midiVel);
                const float fPeak = HammerImpulse::hertzPeakForceNewtons (note, v);
                const float tauC  = HammerImpulse::hertzImpulseConsistentTauCSeconds (note, v, fPeak);
                const float m     = HammerImpulse::hammerMassForPianoNote (note);
                CHECK (fPeak > 0.0f && tauC > 0.0f && m > 0.0f,
                       "conservation domain scan: all chain inputs valid for this (note, midiVel)");
                if (fPeak <= 0.0f || tauC <= 0.0f || m <= 0.0f) continue;

                const double impulseNs = (double) fPeak * (double) tauC
                                        * (2.0 / (double) juce::MathConstants<float>::pi);
                const double boundNs = 2.0 * (double) m * (double) v;
                const double ratio = impulseNs / boundNs;
                worstRatioToBound = std::max (worstRatioToBound, ratio);
                // Self-consistent by construction: impulse should equal the
                // bound to float precision, not merely stay under it.
                allSelfConsistent = allSelfConsistent && std::abs (ratio - 1.0) < 1.0e-3;
                // Hard physical requirement regardless of construction
                // details: never exceed the momentum bound (small float
                // slack, not a new tolerance -- same 1e-3 margin used
                // throughout this file's other energy-conservation checks).
                allWithinBound = allWithinBound && ratio < 1.0 + 1.0e-3;
            }
        }
        std::cout << "       impulse/(2*m*v) worst-case ratio across MIDI "
                     "36-96 x velocity 20-120 domain scan: " << worstRatioToBound
                  << " (audit finding before this fix: 2.55-4.32x; must be ~1.0 now)\n";
        CHECK (allSelfConsistent,
               "hertzImpulseConsistentTauCSeconds: assembled impulse fPeakN*tauC*(2/pi) "
               "equals the elastic-collision momentum bound 2*m*v to within 1e-3 "
               "relative error, across MIDI 36/48/60/72/84/96 x velocity "
               "20/40/60/77/90/110/120 (B7.md SS7 item 4, conservation check)");
        CHECK (allWithinBound,
               "SENTINEL: assembled impulse never exceeds the physical momentum "
               "bound 2*m*v anywhere in the domain scan (WF0914-B7P1 audit finding, "
               "2026-09-14: this FAILED by 2.55-4.32x domain-wide before the fix)");

        // Regression guard: demonstrate that reusing the OLD (wrong) tauC
        // source -- HammerImpulse::pianoHammerTauC(), an existing B4
        // function unrelated to this Hertz solve -- DOES violate the same
        // bound at the audit's own worked example (MIDI 60, real hammer
        // speed corresponding to the audit's score velocity 0.8 case).
        // This is not testing dead code; it is a concrete demonstration
        // that the fix is load-bearing (the fail-closed CHECK above would
        // not have caught the original bug had this alternate path been
        // used instead), tied to a real, currently-existing B4 function.
        {
            const int note = 60;
            const float midiVel = 0.8f * 127.0f;   // audit's own worked example
            const float v = HammerImpulse::hammerVelocityMps (midiVel);
            const float fPeak = HammerImpulse::hertzPeakForceNewtons (note, v);
            const float m = HammerImpulse::hammerMassForPianoNote (note);
            // NOTE: this deliberately calls the score-velocity proxy of
            // pianoHammerTauC() (its 2nd arg is a [0,1] score velocity,
            // not m/s) -- this is EXACTLY the mismatched call the previous
            // B7P1 pass made at the ScoreRenderer.h call site.
            const float wrongTauC = HammerImpulse::pianoHammerTauC (note, 0.8f);
            const double wrongImpulseNs = (double) fPeak * (double) wrongTauC
                                         * (2.0 / (double) juce::MathConstants<float>::pi);
            const double boundNs = 2.0 * (double) m * (double) v;
            std::cout << "       [REGRESSION GUARD] old (wrong) tauC source: impulse/"
                         "(2*m*v) = " << (wrongImpulseNs / boundNs)
                      << " at MIDI 60, score-velocity 0.8 (audit's own example; "
                         "expected ~3.6x, i.e. a clear violation)\n";
            CHECK (wrongImpulseNs / boundNs > 1.0 + 1.0e-3,
                   "REGRESSION GUARD: reusing pianoHammerTauC() (the previous, wrong "
                   "tauC source) DOES violate the 2*m*v bound at the audit's own "
                   "worked example -- confirms this test would have caught the "
                   "original WF0914-B7P1 defect");
        }
    }

    // Fail-closed sentinels.
    CHECK (RadiationModel::modalEnergyFirstPrinciples (-1.0f, tauCS, fHz, modalMassKg, 1.0f) < 0.0f,
           "modalEnergyFirstPrinciples: non-positive fPeakN is fail-closed (-1)");
    CHECK (RadiationModel::modalEnergyFirstPrinciples (fPeakN, 0.0f, fHz, modalMassKg, 1.0f) < 0.0f,
           "modalEnergyFirstPrinciples: non-positive tauCS is fail-closed (-1)");
    CHECK (RadiationModel::modalEnergyFirstPrinciples (fPeakN, tauCS, fHz, -1.0f, 1.0f) < 0.0f,
           "modalEnergyFirstPrinciples: non-positive modalMassKg is fail-closed (-1)");
    CHECK (RadiationModel::modalEnergyFirstPrinciples (
               fPeakN, tauCS, fHz, modalMassKg,
               std::numeric_limits<float>::quiet_NaN()) < 0.0f,
           "modalEnergyFirstPrinciples: NaN excitationWeight is fail-closed (-1)");
    CHECK (RadiationModel::bridgePowerFirstPrinciples (-1.0f, 0.8f) < 0.0f,
           "bridgePowerFirstPrinciples: negative alphaBridge is fail-closed (-1)");
    // Sentinel propagation: modalEnergyFirstPrinciples()'s own -1 sentinel
    // fed into bridgePowerFirstPrinciples() must not be silently treated as
    // a real (negative) energy value.
    CHECK (RadiationModel::bridgePowerFirstPrinciples (alphaBridge, -1.0f) < 0.0f,
           "bridgePowerFirstPrinciples: sentinel eModeJoules (-1) propagates to sentinel output");

    // hertzImpulseConsistentTauCSeconds() fail-closed sentinels (audit fix,
    // 2026-09-14 -- new function).
    CHECK (HammerImpulse::hertzImpulseConsistentTauCSeconds (60, 0.0f, 40.0f) < 0.0f,
           "hertzImpulseConsistentTauCSeconds: zero speedMps is fail-closed (-1)");
    CHECK (HammerImpulse::hertzImpulseConsistentTauCSeconds (60, 1.25f, 0.0f) < 0.0f,
           "hertzImpulseConsistentTauCSeconds: zero fPeakN is fail-closed (-1)");
    CHECK (HammerImpulse::hertzImpulseConsistentTauCSeconds (60, -1.0f, 40.0f) < 0.0f,
           "hertzImpulseConsistentTauCSeconds: negative speedMps is fail-closed (-1)");
    CHECK (HammerImpulse::hertzImpulseConsistentTauCSeconds (
               60, std::numeric_limits<float>::quiet_NaN(), 40.0f) < 0.0f,
           "hertzImpulseConsistentTauCSeconds: NaN speedMps is fail-closed (-1)");
    // Directionality sanity: larger F_peak (same m, v) -> smaller tauC
    // (more force needed to deliver the same fixed 2*m*v impulse in less
    // time).
    CHECK (HammerImpulse::hertzImpulseConsistentTauCSeconds (60, 1.25f, 200.0f)
           < HammerImpulse::hertzImpulseConsistentTauCSeconds (60, 1.25f, 40.0f),
           "hertzImpulseConsistentTauCSeconds: larger F_peak gives smaller tauC "
           "(same note/speed -- fixed impulse target, less time needed at higher force)");
}

// §7 item 5 ("否" branch adaptation, see the section-header comment above):
// "Path B/C fields do not interfere" is checked here as (a) B6's
// pressurePerForce() and this card's bridgePowerFirstPrinciples() give
// numerically DIFFERENT results for representative inputs (not aliased/
// accidentally wired to the same computation), and (b) both are pure
// functions whose results do not depend on call order or on each other
// (no shared hidden state that could let one path corrupt the other) --
// this is the concrete failure mode "互不干擾" protects against; a real
// dumpModes() JSON-level acoustic_transfer/acoustic_transfer_c comparison
// does not apply here because this "否" branch never emits those two Path C
// keys (see RadiationModel::bridgePowerFirstPrinciples()'s doc comment).
void testPathBAndPathCDoNotInterfere()
{
    const float physicsOnlyAmplitude = 0.42f;   // same representative value
                                                 // testPressurePerForceCalibration() uses
    const float fPeakN = 40.0f, tauCS = 0.002f, fHz = 250.0f;
    const float modalMassKg = 0.001f, excitationWeight = 1.0f, alphaBridge = 5.0f;

    // Order 1: Path B (B6) computed first, then Path C (B7P1).
    const float pathB_order1 = RadiationModel::pressurePerForce (physicsOnlyAmplitude);
    const float eMode_order1 = RadiationModel::modalEnergyFirstPrinciples (
        fPeakN, tauCS, fHz, modalMassKg, excitationWeight);
    const float pathC_order1 = RadiationModel::bridgePowerFirstPrinciples (alphaBridge, eMode_order1);

    // Order 2: Path C (B7P1) computed first, then Path B (B6) -- same
    // inputs, reversed call order.
    const float eMode_order2 = RadiationModel::modalEnergyFirstPrinciples (
        fPeakN, tauCS, fHz, modalMassKg, excitationWeight);
    const float pathC_order2 = RadiationModel::bridgePowerFirstPrinciples (alphaBridge, eMode_order2);
    const float pathB_order2 = RadiationModel::pressurePerForce (physicsOnlyAmplitude);

    CHECK (pathB_order1 == pathB_order2 && pathC_order1 == pathC_order2,
           "SENTINEL: Path B (pressurePerForce) and Path C "
           "(bridgePowerFirstPrinciples) give bit-identical results "
           "regardless of call order -- pure functions, no shared hidden "
           "state through which one path could corrupt the other");

    std::cout << "[SENTINEL 1/2] Path B pressurePerForce(0.42) = " << pathB_order1
              << " Pa/N\n";
    std::cout << "[SENTINEL 2/2] Path C bridgePowerFirstPrinciples(hand-calc) = "
              << pathC_order1 << " W -- must not equal Path B's value (different "
              << "physical quantity, different units, independently computed)\n";
    CHECK (std::abs (pathB_order1 - pathC_order1) > 0.1f,
           "SENTINEL: Path B and Path C outputs are numerically distinguishable "
           "for representative inputs (not accidentally wired to the same "
           "computation / swapped function bodies)");
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

// ---------------------------------------------------------------------------
// Water-gong pitch glide: the SETTLED pitch must not depend on the host's
// audio buffer size.
//
// Pre-2026-08-31 the cap was a per-block REJECT (`if (glidePhase < 0.5f)`), so
// the phase froze on whatever value the last ACCEPTED block left it at -- up to
// one full increment below the cap. At 8192 samples / 48 kHz one increment is
// 0.0256 phase, which is ~15.6 cents of pitch. Same project, different buffer
// size, different tuning. The fix clamps instead of rejecting.
// ---------------------------------------------------------------------------
void testWaterGongGlideSettlesIndependentlyOfBlockSize()
{
    constexpr double kSr = 48000.0;
    constexpr float  kAmount = 1.0f;
    constexpr double kSeconds = 6.0;          // well past the ~3.3 s cap

    auto settledPhase = [&] (int blockSize)
    {
        float phase = 0.0f;
        const int totalSamples = (int) (kSeconds * kSr);
        for (int done = 0; done < totalSamples; done += blockSize)
            phase = ChromaticVoice::advanceGlidePhase (phase, kAmount,
                                                       blockSize, kSr);
        return phase;
    };

    // The pre-fix rule, reproduced exactly: advance unconditionally, and only
    // adopt the value while it is still below the cap.
    auto legacySettledPhase = [&] (int blockSize)
    {
        float phase = 0.0f, adopted = 0.0f;
        const int totalSamples = (int) (kSeconds * kSr);
        for (int done = 0; done < totalSamples; done += blockSize)
        {
            phase += kAmount * 0.15f * (float) ((double) blockSize / kSr);
            if (phase < ChromaticVoice::kGlidePhaseCap)
                adopted = phase;
        }
        return adopted;
    };

    auto centsBetween = [] (float phaseA, float phaseB)
    {
        const double a = ChromaticVoice::glideMultiplierFor (phaseA);
        const double b = ChromaticVoice::glideMultiplierFor (phaseB);
        return std::abs (1200.0 * std::log2 (a / b));
    };

    const int blockSizes[] = { 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192 };

    bool allIdentical = true;
    const float reference = settledPhase (64);
    for (int blockSize : blockSizes)
        if (settledPhase (blockSize) != reference)
            allIdentical = false;

    CHECK (allIdentical,
           "Water-gong glide settles on a bit-identical phase at every buffer size");
    CHECK (reference == ChromaticVoice::kGlidePhaseCap,
           "The settled glide phase is exactly the documented cap");
    CHECK (std::abs (ChromaticVoice::glideMultiplierFor (reference) - 0.85f) < 1.0e-6f,
           "The settled glide multiplier is the documented 0.85 (15 % drop)");

    // Self-proof: the pre-fix rule really was buffer-size dependent, so this
    // test would have failed against it rather than passing vacuously. The
    // threshold is the project's own melody-GATE pitch tolerance (5 cents, see
    // docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md) rather than an arbitrary
    // number: the pre-fix spread has to be large enough that the project's own
    // verifier would have called it a pitch error.
    double legacyWorstSpreadCents = 0.0;
    int legacyWorstBlock = 0;
    for (int blockSize : blockSizes)
    {
        const double spread = centsBetween (legacySettledPhase (64),
                                            legacySettledPhase (blockSize));
        if (spread > legacyWorstSpreadCents)
        {
            legacyWorstSpreadCents = spread;
            legacyWorstBlock = blockSize;
        }
    }
    CHECK (legacyWorstSpreadCents > 5.0,
           "The pre-fix per-block reject really did make settled pitch depend on "
           "buffer size, by more than the 5-cent melody-GATE tolerance "
           "(this test is meaningful)");
    std::cout << "       legacy worst settled-pitch spread vs 64 samples = "
              << legacyWorstSpreadCents << " cents (at " << legacyWorstBlock
              << " samples)\n";

    // The cap must never be exceeded, whatever the block size or amount.
    bool neverExceedsCap = true;
    for (int blockSize : blockSizes)
        for (float amount : { 0.02f, 0.5f, 1.0f })
        {
            float phase = 0.0f;
            for (int done = 0; done < (int) (kSeconds * kSr); done += blockSize)
            {
                phase = ChromaticVoice::advanceGlidePhase (phase, amount,
                                                           blockSize, kSr);
                if (phase > ChromaticVoice::kGlidePhaseCap || ! std::isfinite (phase))
                    neverExceedsCap = false;
            }
        }
    CHECK (neverExceedsCap,
           "Glide phase stays finite and within the cap for every amount/buffer size");

    // A zero/invalid sample rate must not produce NaN or move the phase.
    CHECK (ChromaticVoice::advanceGlidePhase (0.25f, 1.0f, 512, 0.0) == 0.25f,
           "A zero sample rate leaves the glide phase untouched");

    // Different sample rates must reach the same settled phase too -- the cap
    // is a position, not a rate.
    bool sampleRateIndependent = true;
    for (double sr : { 44100.0, 48000.0, 96000.0, 192000.0 })
    {
        float phase = 0.0f;
        for (int done = 0; done < (int) (kSeconds * sr); done += 512)
            phase = ChromaticVoice::advanceGlidePhase (phase, kAmount, 512, sr);
        if (phase != ChromaticVoice::kGlidePhaseCap)
            sampleRateIndependent = false;
    }
    CHECK (sampleRateIndependent,
           "The settled glide phase is the same at every sample rate");
}

int main()
{
    std::cout << "TsukiSynth physical-model regression tests\n";
    testBeamBoundaryAndGeometry();
    testBesselPortable();
    testWaterGongGlideSettlesIndependentlyOfBlockSize();
    testPlateModesAndPoisson();
    testGeometryFrequencyModeAndDamping();
    testBridgeAdmittanceLoss();
    testBridgeLossSentinel();
    testRadiationEfficiencyShape();
    testRadiatedPowerChain();
    testPressurePerForceCalibration();
    testPhysicsOnlyCaptureDoesNotAffectRender();
    testStringDampingFirstPrinciples();
    testDimensionalScalingLaws();
    testPassivityAndInvalidNumericRefusal();
    testHammerSpectrum();
    testPianoHammerContactSolver();
    testHammerVelocityMps();
    testHertzPeakForceEnergyConservation();
    testHertzPeakForceCounterexample();
    testBridgePowerFirstPrinciplesChain();
    testPathBAndPathCDoNotInterfere();
    testRelativeCutoffAndNoiseStreams();
    testLongDelayAndSharedEffects();
    std::cout << (failures == 0 ? "PASS" : "FAIL")
              << " (" << failures << " failures)\n";
    return failures == 0 ? 0 : 1;
}
