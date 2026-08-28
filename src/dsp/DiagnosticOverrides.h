#pragma once

// ─────────────────────────────────────────────────────────────────────────
// DIAGNOSTIC-ONLY CLI overrides (2026-07-09, M2 option b, 月月-authorized).
//
// Purpose: let tools/physics_verify.py isolate individual signal-path
// stages via differential renders -- e.g. render the SAME score once with
// --body-amount 0 and once with the real 0.5 body mix, then diff the two
// WAVs sample-for-sample to attribute exactly how much of the --amps
// discrepancy (see reports/gate_outputs/amps_rootcause_analysis.md) comes
// from BodyResonance vs. the exciter noise transient vs. multi-string
// beating.
//
// These are NOT part of the verified render contract (ROADMAP_PHYSICS.md
// §1): no score JSON field, plugin parameter, or preset can reach these --
// they are set ONLY by explicit tsukisynth-cli flags (see RenderApp.cpp),
// default to sentinel "no override" values, and every noteOn() site that
// reads them falls back to the exact pre-existing hard-coded constant when
// the sentinel is seen. A CLI invocation with none of --body-amount,
// --no-exciter-noise, --num-strings passed is therefore bit-identical to
// this code's pre-instrumentation behavior (proven via SHA256 of a
// no-flags render of scores/examples/akashic_bell.score.json before and
// after this header existed).
// ─────────────────────────────────────────────────────────────────────────
namespace DiagnosticOverrides
{
    // < 0.0f = no override; engines use their normal hard-coded 0.5f mix.
    inline float bodyAmountOverride = -1.0f;

    // When true, suppresses the exciter noise burst (the LP-filtered noise
    // transient triggered in setupExciter()) for every voice in the render.
    inline bool disableExciterNoise = false;

    // <= 0 = no override; Cimbalom/Piano use the score's own numStrings.
    inline int numStringsOverride = -1;

    // B6 Phase 3 (2026-08-28, 月月-authorized Option B choice -- see
    // reports/decision_packets/B6_calibration_choice.md "裁決記錄" and
    // docs/workcards/B6.md SS6 step 12). When true, CimbalomVoice::noteOn()
    // (the CLI/ScoreRenderer variant only -- NOT startNote(), the plugin's
    // real-time entry point, which never reads this flag) additionally
    // captures each partial's PURE-PHYSICS amplitude: the per-mode
    // amplitude BEFORE spectralTilt and BEFORE the cross-register
    // loudnessCompensationGain / multi-string gain are applied (both
    // CREATIVE-layer multipliers -- see the "spectralTilt: CREATIVE /
    // HEURISTIC LAYER" comment in CimbalomEngine.h), but AFTER the
    // physics-driven HammerImpulse::forceSpectrumMagnitude() term. Read via
    // CimbalomVoice::getPhysicsOnlyModeAmplitudes(), consumed only by
    // ScoreRenderer::dumpModes() for the "acoustic_transfer" field (see
    // RadiationModel::pressurePerForce()).
    //
    // Like every other flag in this file: no score JSON field, plugin
    // parameter, or preset can reach this -- set ONLY by dumpModes()
    // itself. Default false means a normal render()/renderEvent() call
    // executes the exact pre-B6-Phase-3 instruction sequence for the
    // audio-producing path (the new capture code is skipped entirely, not
    // just numerically inert -- every site that reads this flag is an
    // early-out "if" around the extra bookkeeping) -- proven via SHA256 of
    // no-flags renders before/after, see reports/gate_outputs/
    // b6_bit_identity_phase34.txt (8/8 identical to the pre-B6 baseline in
    // reports/gate_outputs/b6_method/sha256_before.txt) and the unit-level
    // check in tests/physics_models_repro.cpp's
    // testPhysicsOnlyCaptureDoesNotAffectRender().
    inline bool capturePhysicsOnlyModes = false;
}
