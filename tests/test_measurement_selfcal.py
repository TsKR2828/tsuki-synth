"""Sentinel tests for tools/measurement_selfcal.py (WF0907-C10, WF0909-C10B,
WF0909-C10C).

No TsukiSynthCLI render anywhere here -- these are pure-numpy, known-answer
synthetic-signal tests of the estimator's own accuracy, per the card's
requirement that the measuring instrument prove itself BEFORE the ±5-cent
product GATE is trusted.

  (a) test_pure_harmonic_a4_within_one_cent -- a clean, high-SNR, purely
      harmonic A4 tone must measure within the ratified 1-cent limit.
  (b) test_sensitivity_anti_false_green -- the real estimator, given a
      signal deliberately mistuned by +/-3.0 cents from the value it is
      told to expect, must REPORT that mistuning (+-1.0c tolerance) -- this
      is the check that stops an estimator which just echoes back the
      expected value from looking like it passed.
  (c) test_mutant_estimator_caught_by_sensitivity_check -- monkeypatches
      melody_verify.measure_pitch_cents with an "always agree with the
      expected value" mutant and proves sensitivity_check() then FAILS,
      i.e. (b) actually has teeth and is not itself a false green.

STATUS after WF0909-C10C (card RED, 2026-09-09) and the month-lead's
2026-09-10 ruling (option A -- narrow the claim domain, do NOT change the
production estimator): SIX replacement estimators have been tried and all
six rejected -- five inside the "reweight the bins of one band" family
(WF0909-C10B) and one outside it (C10C's time-domain damped-sinusoid NLS
fit). The C10C candidate was NOT landed: it is preserved unlanded in
reports/c10c_nls_candidate.patch, so no dead estimator sits in a product
file. Production is STILL the legacy hard-edge centroid, and the 1-cent
self-certification bar is STILL unmet by it -- that gap is now an
accepted, documented limit (docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md
S8.5/S9.7), not an open promise. The tests below are split accordingly:

  PRODUCTION-PATH assertions -- real, still-executing, still-failing, so
  they are strict xfails that name the open gap instead of hiding it:
  (d) test_development_grid_within_one_cent   (production: 1.1721 c)
  (e) test_holdout_grid_within_one_cent       (production: 1.0840 c)
  (f) test_gain_fidelity_within_one_cent      (production absorbs 16.86 c
      of a 40-cent deviation at MIDI 37: measured +23.14 c)
  strict=True on all three: the day an estimator really clears them,
  pytest flags the XPASS so these get promoted to plain tests rather than
  quietly passing inside an xfail.

  PRODUCTION-PATH assertions that DO hold today:
  (g) test_course_semantics_reports_centre -- the centroid does report the
      centre of a 3-string course; this is the property that killed
      C10B's single-peak candidates, so it is asserted, not assumed.
  (h) test_gain_fidelity_no_regression_vs_legacy -- whatever ships must
      never be WORSE on the gain axis than the centroid already is.
  (i) test_measure_pitch_cents_matches_legacy_after_revert -- production
      must be numerically identical to measure_pitch_cents_legacy over the
      whole development grid, so no estimator swap can land without a
      fresh audit.

STATUS after WF0914-D15 (2026-09-14: the card stopped at its own BLOCKED
rule -- new worst case > 1.18 c; the month-lead then closed D15 on
2026-09-15 with option A', narrowing the claim domain again: the release
segment's known measurer-error bound is ~7.2 c, recorded in
docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md S8.5 -- no estimator change):
run_grid()/run_holdout_grid() now each return TWO segments, "sustain"
(the original single-exponential corpus, unchanged numbers) and "release" (WF0914-D15's new two-stage-decay corpus mirroring
ModalResonator::damp()). The tests below therefore filter to segment ==
"sustain" wherever they assert the ORIGINAL pinned numbers (1170/1040
points, 1.1721/1.0840 cents) -- run_grid()'s row COUNT changed (grew), the
SUSTAIN SUBSET's numbers did not, so this is not a narrowed assertion (R3):
it is the same check, still exercising the same 1170/1040 points it always
did, just selected out of a larger returned list. New xfail tests
(j) test_release_development_grid_within_one_cent and (k)
test_release_holdout_grid_within_one_cent assert the release segment
against the SAME unmoved 1-cent bar and currently fail it by a wide margin
(development 5.2304 c, hold-out 7.2055 c) -- see
docs/workcards/WF0914_D15_selfcal_corpus.md for the card and S8.5 of the
design doc for the A' ruling that closed it. (l)
test_release_sensitivity_anti_false_green is the release segment's own
anti-false-green positive control and passes today.

WF0925-P1 (staged-review:D15-xfailpin): the pinned on-record numbers are
asserted ONLY in plain (non-xfail) tests, measured with the legacy
estimator: (i) above pins development-grid sustain 1.1721 c AND release
5.2304 c, and (m) test_holdout_grid_pins_match_record pins hold-out sustain
1.0840 c and release 7.2055 c. Inside an xfail(strict) test any failing
assert just counts as the expected failure, so a pin placed there caught
neither drift nor improvement (the pin assert ran before the 1-cent check,
so an improved estimator died on the pin and could never XPASS). The four
grid xfails, (d) (e) (j) (k), now assert only refusals / point count /
the 1-cent bar, so a real estimator improvement shows up as a strict XPASS.

WF0925b-TF (decision packet O16, P1-audit note): the release segment's
"zero refusals" condition, until then asserted only inside the strict xfails
(j) and (k), is now also asserted in the plain tests (i) (production rows,
development grid) and (m) (legacy rows, hold-out grid). Relocated, not new:
0 refusals is what both grids measure today (2026-09-25: dev 1170/1170 and
hold-out 1040/1040 release cells measured, 0 refused).

WF1003-S: the SUSTAIN segment's "zero refusals" condition, until then
asserted only inside the strict xfails (d) and (e), is likewise now also
asserted in the plain tests (i) (production rows, development grid) and (m)
(legacy rows, hold-out grid). Relocated, not new; (d)/(e) keep their own copy.
Measured 2026-10-03: sustain 1170/1170 and 1040/1040 cells measured, 0 refused.

  NOT here any more: the three C10C candidate tests (they imported
  melody_verify.measure_pitch_cents_nls, which option A kept out of the
  tree). See the comment block at the bottom of this file for what they
  asserted and where those numbers now live. The structural lesson they
  encoded still stands and is recorded in
  reports/decision_packets/C10_selfcal_domain.zh-TW.md S6.3: this file
  synthesizes "sum of exponentially decaying sinusoids + noise", so an
  estimator whose own model is exactly that can sweep every synthetic bar
  below and still be worse on real rendered audio -- clearing these bars
  is necessary, never sufficient, evidence for shipping an estimator.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import measurement_selfcal as ms  # noqa: E402
import melody_verify as mv        # noqa: E402

# On record in three documents; pinned so the xfails below cannot become
# XPASS by the GRID getting easier rather than an estimator getting better.
# Asserted in plain tests (i) and (m) with the LEGACY estimator, so they
# guard the grid itself and stay green if a better estimator lands (which
# is then reported by the strict xfails turning XPASS).
LEGACY_DEV_GRID_MAX_ABS_CENTS = 1.1721
LEGACY_HOLDOUT_GRID_MAX_ABS_CENTS = 1.0840

# WF0914-D15: the release segment's own pinned numbers (same role as the
# two above). Existing measured values, not tolerances. Sourced from
# reports/gate_outputs/wf0914_D15_gate1_dev_grid.txt / _holdout_grid.txt
# ("by segment ... release 5.2304 c" / "release 7.2055 c").
RELEASE_DEV_GRID_MAX_ABS_CENTS = 5.2304
RELEASE_HOLDOUT_GRID_MAX_ABS_CENTS = 7.2055

XFAIL_REASON = (
    "WF0909-C10C (2026-09-09, card RED): the production estimator is still "
    "the legacy hard-edge centroid, whose own error misses the ratified "
    "1-cent self-certification bar. Six replacement estimators have been "
    "tried and rejected -- five bin-reweighting variants (WF0909-C10B) and "
    "C10C's time-domain NLS fit, which cleared EVERY synthetic bar in this "
    "file (dev 0.2868 c, hold-out 0.0816 c, gain fidelity 0.0090 c, course "
    "centre 0.0064 c) and was still rejected because it turns 7 dry-stem "
    "PASS into FAIL on the product GATE path and changes 9 of the 30 "
    "strong-domain corpus files. That candidate was NOT landed (month-lead "
    "ruling, option A, 2026-09-10); it is preserved unlanded in "
    "reports/c10c_nls_candidate.patch -- see "
    "reports/c10c_nls_estimator_before_after.md and "
    "reports/decision_packets/C10_selfcal_domain.zh-TW.md S6/S7. The "
    "assertion below is NOT loosened and NOT deleted (R2); it is an xfail "
    "so CI names the open gap every run. strict=True: an XPASS means "
    "someone landed an estimator that really clears this, and should fail "
    "CI as a prompt to promote this back to a plain test.")


def test_pure_harmonic_a4_within_one_cent():
    cents, fail, onset_err_ms, f0_nom, f0_true = ms.measure_one(
        midi=69, variant="harmonic", level_dbfs=-6.0, sr=48000)
    assert fail is None, "estimator refused a clean synthetic A4: %r" % fail
    assert cents is not None
    assert abs(cents) <= 1.0, (
        "pure harmonic A4 (f0=%.3f Hz) measured %.4f cents error, "
        "exceeds the ratified 1-cent self-calibration limit" % (f0_true, cents))


def test_sensitivity_anti_false_green():
    results = ms.sensitivity_check()
    assert len(results) == 2
    for offset, cents, fail, ok in results:
        assert fail is None, "sensitivity cell refused: %r" % fail
        assert ok, (
            "estimator did not report the injected %.1f-cent mistuning "
            "(measured %.4f, tolerance +-%.1f) -- anti-false-green check failed"
            % (offset, cents, ms.SENSITIVITY_TOL_CENTS))


def test_mutant_estimator_caught_by_sensitivity_check(monkeypatch):
    """An estimator that just returns the EXPECTED f0 (0 cents, always)
    regardless of the actual signal must be caught by sensitivity_check --
    proving the +/-3 cent injection is a real defect-catcher, not a rubber
    stamp."""
    def always_agrees(mono, sr, f0, t_exp):
        return 0.0, None

    monkeypatch.setattr(mv, "measure_pitch_cents", always_agrees)

    results = ms.sensitivity_check()
    all_ok = all(ok for _offset, _cents, _fail, ok in results)
    assert not all_ok, (
        "mutant estimator that always reports 0 cents (ignores the actual "
        "signal) was NOT caught by sensitivity_check() -- the anti-false-"
        "green check has no teeth")
    # and the mutant must be the one actually exercised (offsets applied
    # were nonzero, so an honest estimator would have measured them)
    assert any(offset != 0.0 for offset, _c, _f, _ok in results)


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_development_grid_within_one_cent():
    """The 1170-point SUSTAIN-segment development grid must clear the
    ratified 1-cent self-certification bar with zero refusals. Production
    measures 1.1721 cents -- the gap C10 opened and C10B/C10C have not
    closed. (WF0914-D15: run_grid() now also returns an equal-size
    "release" segment; this test filters segment=="sustain" so it keeps
    testing the exact same 1170 points/number it always has -- see
    test_release_development_grid_within_one_cent for the new segment.)"""
    rows = [r for r in ms.run_grid() if r["segment"] == "sustain"]
    fails = [r for r in rows if r["fail_reason"] is not None]
    assert not fails, "development grid produced refusals: %r" % fails[:5]
    errs = [abs(r["error_cents"]) for r in rows if r["error_cents"] is not None]
    assert len(errs) == len(rows) == 1170
    max_abs = max(errs)
    assert max_abs <= ms.MAX_ABS_ERROR_CENTS_LIMIT, (
        "development grid max |error| = %.4f cents exceeds the ratified "
        "%.1f-cent self-calibration limit"
        % (max_abs, ms.MAX_ABS_ERROR_CENTS_LIMIT))


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_holdout_grid_within_one_cent():
    """WF0909-C10B S2.2 overfitting guard: the hold-out grid (disjoint f0
    offsets/B/level/onset from the development grid) must ALSO clear the
    1-cent bar with zero refusals. Production measures 1.0840 cents. Full
    SUSTAIN-segment grid (1040 points) -- slower than the other tests here,
    but this IS the assertion the card's GATE 1 depends on; a subset would
    not prove the hold-out number. (WF0914-D15: run_holdout_grid() now also
    returns an equal-size "release" segment; filtered out here so this test
    keeps testing the exact same 1040 points/number it always has.)"""
    rows = [r for r in ms.run_holdout_grid() if r["segment"] == "sustain"]
    fails = [r for r in rows if r["fail_reason"] is not None]
    assert not fails, "hold-out grid produced refusals: %r" % fails[:5]
    errs = [abs(r["error_cents"]) for r in rows if r["error_cents"] is not None]
    assert len(errs) == len(rows) == 1040
    max_abs = max(errs)
    assert max_abs <= ms.MAX_ABS_ERROR_CENTS_LIMIT, (
        "hold-out grid max |error| = %.4f cents exceeds the ratified "
        "%.1f-cent self-calibration limit -- estimator overfits the "
        "development grid" % (max_abs, ms.MAX_ABS_ERROR_CENTS_LIMIT))


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_release_development_grid_within_one_cent():
    """WF0914-D15: the 1170-point RELEASE-segment development grid (module
    docstring "Release/damping-segment corpus") judged against the SAME
    unmoved 1-cent bar (R2: no new tolerance). Production measures
    5.2304 cents -- far worse than the sustain segment's already-missed
    1.1721 cents, because a real damping-law change mid-analysis-window is
    exactly the failure geometry the sustain-only corpus was blind to
    (WF0909-C10C's real-audio rejection)."""
    rows = [r for r in ms.run_grid() if r["segment"] == "release"]
    fails = [r for r in rows if r["fail_reason"] is not None]
    assert not fails, "release-segment development grid produced refusals: %r" % fails[:5]
    errs = [abs(r["error_cents"]) for r in rows if r["error_cents"] is not None]
    assert len(errs) == len(rows) == 1170
    max_abs = max(errs)
    # The 5.2304 c pin lives in the plain test (i), not here (WF0925-P1).
    assert max_abs <= ms.MAX_ABS_ERROR_CENTS_LIMIT, (
        "release-segment development grid max |error| = %.4f cents exceeds "
        "the ratified %.1f-cent self-calibration limit"
        % (max_abs, ms.MAX_ABS_ERROR_CENTS_LIMIT))


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_release_holdout_grid_within_one_cent():
    """WF0914-D15 hold-out counterpart of test_release_development_grid_
    within_one_cent(): the 1040-point RELEASE-segment hold-out grid judged
    against the same unmoved 1-cent bar. Production measures 7.2055 cents."""
    rows = [r for r in ms.run_holdout_grid() if r["segment"] == "release"]
    fails = [r for r in rows if r["fail_reason"] is not None]
    assert not fails, "release-segment hold-out grid produced refusals: %r" % fails[:5]
    errs = [abs(r["error_cents"]) for r in rows if r["error_cents"] is not None]
    assert len(errs) == len(rows) == 1040
    max_abs = max(errs)
    # The 7.2055 c pin lives in the plain test (m), not here (WF0925-P1).
    assert max_abs <= ms.MAX_ABS_ERROR_CENTS_LIMIT, (
        "release-segment hold-out grid max |error| = %.4f cents exceeds "
        "the ratified %.1f-cent self-calibration limit -- estimator "
        "overfits the development grid"
        % (max_abs, ms.MAX_ABS_ERROR_CENTS_LIMIT))


def test_release_sensitivity_anti_false_green():
    """WF0914-D15's own positive control (module docstring "Release/
    damping-segment corpus" section, mirrors test_sensitivity_anti_false_
    green but on a release-segment signal): a release-segment signal
    deliberately mistuned by +/-3.0 cents from the value the estimator is
    told to expect must be REPORTED as mistuned (+-1.0c tolerance) -- proof
    the release corpus's worst-case numbers reflect real measurement, not
    the estimator echoing back the expected value."""
    results = ms.release_sensitivity_check()
    assert len(results) == 2
    for offset, cents, fail, ok in results:
        assert fail is None, "release sensitivity cell refused: %r" % fail
        assert ok, (
            "estimator did not report the injected %.1f-cent mistuning on "
            "a release-segment signal (measured %.4f, tolerance +-%.1f) -- "
            "release-corpus anti-false-green check failed"
            % (offset, cents, ms.SENSITIVITY_TOL_CENTS))


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_gain_fidelity_within_one_cent():
    """WF0909-C10C card S1.1 (the axis C10B's audit added and C10C
    promotes to a pass/fail condition): with the EXPECTED f0 held fixed and
    the TRUE frequency offset by up to +/-40 cents, the estimator must
    report the TRUE deviation to within the same ratified 1.0 cent. Not a
    new tolerance -- the same 2026-08-30 bar applied to the axis on which
    C10B's reverted raised-cosine taper silently widened the +/-5-cent
    GATE. Production (the centroid) misses this badly: a +40-cent true
    deviation at MIDI 37 measures only +23.14 cents (error 16.86 c)."""
    rows = ms.gain_fidelity_scan()
    refused = [r for r in rows if r["fail_reason"] is not None]
    assert not refused, (
        "gain-fidelity scan refused %d/%d cells: %r"
        % (len(refused), len(rows), refused[:5]))
    worst = max(rows, key=lambda r: abs(r["error_cents"]))
    assert abs(worst["error_cents"]) <= ms.MAX_ABS_ERROR_CENTS_LIMIT, (
        "gain fidelity: a TRUE deviation of %+g cents measured %+.4f cents "
        "(error %.4f c > %.1f c limit) at midi=%d %s %+g dBFS -- the "
        "estimator is absorbing real mistuning, which widens the product's "
        "+/-5-cent GATE without touching the number (R2)"
        % (worst["offset_cents"], worst["measured_cents"],
           abs(worst["error_cents"]), ms.MAX_ABS_ERROR_CENTS_LIMIT,
           worst["midi"], worst["variant"], worst["level_dbfs"]))


def test_course_semantics_reports_centre():
    """WF0909-C10C card S1.3: this project's default cimbalom/piano
    presets voice a note as a 3-string COURSE detuned -5/0/+5 cents, and
    the ratified claim is that the estimator reports the course CENTRE,
    not its loudest string. Asserted at equal amplitudes AND at 0.5/1/0.5.
    C10B's single-peak candidates (a)/(b) passed every synthetic grid and
    then failed 4 of 5 real sentinel notes on exactly this property, so it
    is asserted here rather than assumed. Production passes this today."""
    rows = ms.course_semantics_check()
    assert len(rows) == len(ms.COURSE_AMP_SETS) * len(ms.COURSE_SCAN_MIDIS)
    refused = [r for r in rows if r["fail_reason"] is not None]
    assert not refused, "course-semantics check refused: %r" % refused[:5]
    worst = max(rows, key=lambda r: abs(r["measured_cents"]))
    assert abs(worst["measured_cents"]) <= ms.MAX_ABS_ERROR_CENTS_LIMIT, (
        "a %s-amplitude 3-string course at MIDI %d measured %+.4f cents "
        "from its own centre (> %.1f c) -- the estimator is reporting a "
        "single string, not the course centroid"
        % (worst["amp_set"], worst["midi"], worst["measured_cents"],
           ms.MAX_ABS_ERROR_CENTS_LIMIT))


def test_gain_fidelity_no_regression_vs_legacy():
    """WF0909-C10B fix round, kept: the estimator the product GATE actually
    uses must not have WORSE gain fidelity than the legacy hard-edge
    centroid on the identical cells -- the check that caught C10B's
    raised-cosine taper (~0.40 gain at low MIDI) before it reached audit."""
    live_rows = ms.gain_fidelity_scan(estimator=mv.measure_pitch_cents)
    legacy_rows = ms.gain_fidelity_scan(estimator=mv.measure_pitch_cents_legacy)
    assert len(live_rows) == len(legacy_rows) > 0

    worst_regression = 0.0
    worst_cell = None
    for live, legacy in zip(live_rows, legacy_rows):
        if live["gain"] is None or legacy["gain"] is None:
            continue
        regression = abs(1.0 - live["gain"]) - abs(1.0 - legacy["gain"])
        if regression > worst_regression:
            worst_regression = regression
            worst_cell = (live, legacy)

    assert worst_regression <= 1e-9, (
        "measure_pitch_cents()'s gain fidelity is WORSE than "
        "measure_pitch_cents_legacy()'s own on at least one cell (worst "
        "regression %.4f) -- this is exactly the WF0909-C10B raised-cosine "
        "taper's defect (effectively widening the product's ±5-cent "
        "tolerance without touching the number itself, R2); cell=%r"
        % (worst_regression, worst_cell))


def test_measure_pitch_cents_matches_legacy_after_revert():
    """Production must be numerically IDENTICAL to
    measure_pitch_cents_legacy() over the full development grid (both
    segments, WF0914-D15). Both WF0909-C10B and WF0909-C10C ended with
    their candidate estimator rejected, so this is what keeps every pitch
    number already on record in this repo valid, and stops a future
    estimator swap from landing without a fresh real-audio audit.
    It also carries the development grid's two pinned on-record numbers,
    measured on the LEGACY rows (sustain 1.1721 c; since WF0925-P1 also
    release 5.2304 c, moved here out of the release xfail where a failing
    pin could never show)."""
    new_rows = ms.run_grid()

    orig = mv.measure_pitch_cents
    mv.measure_pitch_cents = mv.measure_pitch_cents_legacy
    try:
        legacy_rows = ms.run_grid()
    finally:
        mv.measure_pitch_cents = orig

    assert len(new_rows) == len(legacy_rows) == 2340
    mismatches = [
        (n, l) for n, l in zip(new_rows, legacy_rows)
        if n["fail_reason"] != l["fail_reason"]
        or (n["error_cents"] is None) != (l["error_cents"] is None)
        or (n["error_cents"] is not None
            and abs(n["error_cents"] - l["error_cents"]) > 1e-9)
    ]
    assert not mismatches, (
        "measure_pitch_cents() diverged from measure_pitch_cents_legacy() "
        "on %d/%d development-grid cells -- production is no longer the "
        "legacy hard-edge centroid; re-run the WF0909-C10B gain-fidelity "
        "audit AND the WF0909-C10C real-audio evidence rerun before "
        "shipping whatever changed it: %r"
        % (len(mismatches), len(new_rows), mismatches[:3]))
    legacy_sustain = [r for r in legacy_rows if r["segment"] == "sustain"]
    assert len(legacy_sustain) == 1170
    # WF1003-S (TODO: sustain grid zero-refusal condition out of the strict
    # xfail): the SUSTAIN segment's "zero refusals" condition was, until now,
    # asserted only inside the strict xfail (d), where a new refusal would just
    # count as the expected failure and stay invisible -- the same gap
    # WF0925b-TF closed for the RELEASE segment right below. Same condition,
    # relocated -- not a new threshold (R2); xfail (d) keeps its own copy.
    # Checked on the PRODUCTION rows (new_rows; the mismatch check above ties
    # their fail_reason to the legacy rows cell by cell).
    new_sustain = [r for r in new_rows if r["segment"] == "sustain"]
    assert len(new_sustain) == 1170
    sustain_refused = [r for r in new_sustain
                       if r["fail_reason"] is not None or r["error_cents"] is None]
    assert not sustain_refused, (
        "the production estimator refused %d/%d SUSTAIN-segment development-"
        "grid cells (on record: 0) -- the pinned 1.1721 c is no longer a max "
        "over all 1170 points: %r"
        % (len(sustain_refused), len(new_sustain), sustain_refused[:5]))
    legacy_max = max(abs(r["error_cents"]) for r in legacy_sustain
                     if r["error_cents"] is not None)
    assert abs(legacy_max - LEGACY_DEV_GRID_MAX_ABS_CENTS) < 5e-4, (
        "the production/legacy centroid now measures %.4f cents on the "
        "SUSTAIN segment of the development grid, not the %.4f on record "
        "-- the GRID changed, so every before/after number in "
        "reports/c10b_estimator_before_after.md, "
        "reports/c10c_nls_estimator_before_after.md and "
        "docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md S9 needs re-deriving"
        % (legacy_max, LEGACY_DEV_GRID_MAX_ABS_CENTS))
    legacy_release = [r for r in legacy_rows if r["segment"] == "release"]
    assert len(legacy_release) == 1170
    # WF0925b-TF (decision packet O16, P1-audit note): "zero refusals on the
    # RELEASE segment" used to be asserted only inside the strict xfail (j),
    # where a new refusal would just count as the expected failure and stay
    # invisible. Same condition, relocated -- not a new threshold (R2) --
    # and checked on the PRODUCTION rows (new_rows; the mismatch check above
    # already ties their fail_reason to the legacy rows cell by cell).
    new_release = [r for r in new_rows if r["segment"] == "release"]
    assert len(new_release) == 1170
    release_refused = [r for r in new_release
                       if r["fail_reason"] is not None or r["error_cents"] is None]
    assert not release_refused, (
        "the production estimator refused %d/%d RELEASE-segment development-"
        "grid cells (on record: 0) -- the D15 release corpus no longer "
        "measures every cell, so its pinned 5.2304 c is no longer a max over "
        "all 1170 points: %r"
        % (len(release_refused), len(new_release), release_refused[:5]))
    legacy_release_max = max(abs(r["error_cents"]) for r in legacy_release
                             if r["error_cents"] is not None)
    assert abs(legacy_release_max - RELEASE_DEV_GRID_MAX_ABS_CENTS) < 5e-4, (
        "the production/legacy centroid now measures %.4f cents on the "
        "RELEASE segment of the development grid, not the %.4f on record "
        "-- the GRID changed, so reports/gate_outputs/"
        "wf0914_D15_gate1_dev_grid.txt and docs/EARFREE_MELODY_GATE_DESIGN."
        "zh-TW.md S8.5 need re-deriving"
        % (legacy_release_max, RELEASE_DEV_GRID_MAX_ABS_CENTS))


def test_holdout_grid_pins_match_record(monkeypatch):
    """(m) WF0925-P1 (staged-review:D15-xfailpin): plain-test home for the
    HOLD-OUT grid's two pinned on-record numbers -- sustain 1.0840 c (was
    defined above but asserted nowhere) and release 7.2055 c (was only
    inside the strict xfail test_release_holdout_grid_within_one_cent,
    where a failing pin assert just counted as the expected failure).
    Same pattern and precision (< 5e-4) as the development-grid pin in
    test_measure_pitch_cents_matches_legacy_after_revert: measured with
    the LEGACY estimator, so this guards the grid itself; an estimator
    that really improves leaves this green and turns the strict xfails
    into XPASS. These are existing measured values, not new tolerances."""
    monkeypatch.setattr(mv, "measure_pitch_cents", mv.measure_pitch_cents_legacy)
    legacy_rows = ms.run_holdout_grid()
    assert len(legacy_rows) == 2080

    legacy_sustain = [r for r in legacy_rows if r["segment"] == "sustain"]
    assert len(legacy_sustain) == 1040
    # WF1003-S: the SUSTAIN segment's zero-refusal condition, relocated out of
    # the strict xfail (e) (where a new refusal would only count as the
    # expected failure) -- same condition, not a new threshold (R2); (e) keeps
    # its own copy. Legacy rows, for the reason given for the release check
    # below.
    sustain_refused = [r for r in legacy_sustain
                       if r["fail_reason"] is not None or r["error_cents"] is None]
    assert not sustain_refused, (
        "the legacy centroid refused %d/%d SUSTAIN-segment hold-out-grid "
        "cells (on record: 0) -- the pinned 1.0840 c is no longer a max over "
        "all 1040 points: %r"
        % (len(sustain_refused), len(legacy_sustain), sustain_refused[:5]))
    sustain_max = max(abs(r["error_cents"]) for r in legacy_sustain
                      if r["error_cents"] is not None)
    assert abs(sustain_max - LEGACY_HOLDOUT_GRID_MAX_ABS_CENTS) < 5e-4, (
        "the legacy centroid now measures %.4f cents on the SUSTAIN segment "
        "of the hold-out grid, not the %.4f on record -- the GRID changed; "
        "re-derive the pinned number and every document that cites it "
        "(docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md S8.5/S9)"
        % (sustain_max, LEGACY_HOLDOUT_GRID_MAX_ABS_CENTS))

    legacy_release = [r for r in legacy_rows if r["segment"] == "release"]
    assert len(legacy_release) == 1040
    # WF0925b-TF (decision packet O16, P1-audit note): the hold-out
    # counterpart of the zero-refusal check added to (i) -- relocated out of
    # the strict xfail (k), not a new threshold (R2). These rows are the
    # LEGACY estimator's (the same rows the pins are measured on); a second
    # production hold-out run (~1 min) is not added here because production
    # is held numerically identical to legacy, fail_reason included, by (i).
    release_refused = [r for r in legacy_release
                       if r["fail_reason"] is not None or r["error_cents"] is None]
    assert not release_refused, (
        "the legacy centroid refused %d/%d RELEASE-segment hold-out-grid "
        "cells (on record: 0) -- the pinned 7.2055 c is no longer a max over "
        "all 1040 points: %r"
        % (len(release_refused), len(legacy_release), release_refused[:5]))
    release_max = max(abs(r["error_cents"]) for r in legacy_release
                      if r["error_cents"] is not None)
    assert abs(release_max - RELEASE_HOLDOUT_GRID_MAX_ABS_CENTS) < 5e-4, (
        "the legacy centroid now measures %.4f cents on the RELEASE segment "
        "of the hold-out grid, not the %.4f on record -- the GRID changed; "
        "re-derive reports/gate_outputs/wf0914_D15_gate1_holdout_grid.txt "
        "and docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md S8.5"
        % (release_max, RELEASE_HOLDOUT_GRID_MAX_ABS_CENTS))


# ---------------------------------------------------------------------------
# WF0909-C10C candidate tests: REMOVED, not skipped-in-place, on 2026-09-10.
#
# Three tests used to live here and exercised
# melody_verify.measure_pitch_cents_nls (the time-domain NLS candidate):
#   - test_nls_candidate_clears_every_synthetic_bar
#   - test_synthetic_bars_cannot_certify_a_matched_model_estimator
#   - test_nls_candidate_refuses_instead_of_guessing_on_noise
#
# The month-lead ruled option A on 2026-09-10 (narrow the claim domain, do
# NOT change the production estimator), so measure_pitch_cents_nls was never
# landed in tools/melody_verify.py -- keeping dead code in a product file
# was explicitly rejected. The candidate, together with these three tests in
# their original form, is preserved verbatim in
# reports/c10c_nls_candidate.patch (unlanded); the measured numbers they
# asserted (dev grid 0.2868 c, hold-out 0.0816 c, gain fidelity 0.0090 c,
# course centre 0.0064 c, and the real-audio rejection that overrode all
# four) are on record in reports/c10c_nls_estimator_before_after.md,
# reports/gate_outputs/wf0909_C10C_nls.txt,
# docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md S9.6 and
# reports/decision_packets/C10_selfcal_domain.zh-TW.md S6/S7.
#
# They are deleted rather than @pytest.mark.skip'd because the symbol they
# import does not exist in this tree at all: a skipped test whose body can
# never be collected-and-run again is a false promise of coverage. If a
# future card re-lands the candidate, re-apply reports/c10c_nls_candidate.patch
# to get both the function and these tests back together.
# ---------------------------------------------------------------------------
