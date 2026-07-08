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
}
