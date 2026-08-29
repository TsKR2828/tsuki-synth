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
    testRadiationEfficiencyShape();
    testRadiatedPowerChain();
    testPressurePerForceCalibration();
    testPhysicsOnlyCaptureDoesNotAffectRender();
    testStringDampingFirstPrinciples();
    testDimensionalScalingLaws();
    testPassivityAndInvalidNumericRefusal();
    testHammerSpectrum();
    testPianoHammerContactSolver();
    testRelativeCutoffAndNoiseStreams();
    testLongDelayAndSharedEffects();
    std::cout << (failures == 0 ? "PASS" : "FAIL")
              << " (" << failures << " failures)\n";
    return failures == 0 ? 0 : 1;
}
