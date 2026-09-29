#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925-V1 side check found while reading the release code (descriptive,
no threshold): ScoreRenderer::eventEndTime() (src/score/ScoreRenderer.h)
sizes the CLI render buffer with a post-note-off decay factor of 0.05 for
EVERY modal engine, but ChromaticVoice::noteOff() damps with 0.08
(src/engines/ChromaticEngine.h). If a chromatic-family event is the last
thing still ringing, could the buffer end before that voice has decayed?

For each non-layered corpus score this prints:
  buffer_end   = max_e eventEndTime(e) [0.05 rule, as the renderer does]
                 + effectTailSeconds + wallDelaySeconds + tail_silence_ms
  true_end     = max_e (voice end with each family's real damp factor)
and, when true_end > buffer_end, the remaining energy (dB re its own start,
from --dump-modes amplitudes/decays) of the latest chromatic voice at
buffer_end. Uses the cached dumps and the lifetime helpers of
voice_pool_occupancy.py; note-off at 0.9*duration exactly as the CLI does.

Usage:
  python reports/wf0925_method/chromatic_tail_budget_check.py --dumps output/wf0925/V1/dumps
"""
import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(HERE))
import verify_score as vs            # noqa: E402
import voice_pool_occupancy as vpo   # noqa: E402


def effect_tail_seconds(fx):
    """Mirror of ScoreRenderer::effectTailSeconds() + wallDelaySeconds()."""
    fx = fx or {}
    rv = fx.get("reverb") or {}
    dl = fx.get("delay") or {}
    tail = 0.0
    if float(rv.get("wet", 0) or 0) > 0.001:
        longest_comb = (1617.0 + 23.0) / 44100.0
        allpass = (556.0 + 441.0 + 341.0 + 225.0 + 4.0 * 23.0) / 44100.0
        tail += longest_comb + float(rv.get("decay", 2.0)) + allpass   # ScoreParser default decay 2.0
    if float(dl.get("wet", 0) or 0) > 0.001 and float(dl.get("time_ms", 0) or 0) > 0:
        fb = float(dl.get("feedback", 0) or 0)
        repeats = math.ceil(math.log(0.001) / math.log(fb)) if fb > 0 else 1.0
        tail += max(1.0, repeats) * float(dl["time_ms"]) * 0.001 * 1.10
    wall = float((fx.get("wall") or {}).get("distance_m", 0) or 0)
    wall_s = 2.0 * wall / 343.0 if wall > 0 else 0.0
    return tail, wall_s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dumps", required=True)
    args = ap.parse_args()
    consts = vpo.read_code_constants()
    src = (REPO / "src/score/ScoreRenderer.h").read_text(encoding="utf-8")
    if "noteOff + (maxT60 - noteOff) * 0.05" not in src:
        raise SystemExit("eventEndTime() no longer uses the 0.05 rule -- re-check")
    print("damp factors read from engine code: %s ; eventEndTime() rule: 0.05 for all modal engines"
          % consts["damp_factor"])
    print("%-78s %9s %9s %9s %s" % ("score", "buf_end", "true_end", "short_s", "latest chromatic voice at buffer end"))
    n_short = 0
    for sp in vs.find_all_scores(REPO):
        s = json.loads(sp.read_text(encoding="utf-8"))
        if "layers" in s:
            continue
        events, sr, _ = vpo.load_events(sp, args.dumps, consts)
        g = s.get("global") or {}
        ex = s.get("export") or {}
        fx_tail, wall_s = effect_tail_seconds(g.get("effects"))
        tail_sil = float(ex.get("tail_silence_ms", 0) or 0) / 1000.0
        ev_end_rule = []
        true_ends = []
        for e in events:
            start = max(0.0, e["t_on"])
            dur = e["dur"]
            if e["family"] == "fm":
                rel = e["fm_release_s"]
                end_rule = max(start + dur, start + 0.9 * dur + rel)
                true_end = end_rule
            else:
                T = e["t60_max"]
                off = 0.9 * dur
                active = T if T <= off else off + (T - off) * 0.05
                end_rule = max(start + dur, start + active)
                f = e["damp_factor"]
                active_true = T if T <= off else off + (T - off) * f
                true_end = start + active_true
            ev_end_rule.append(end_rule)
            true_ends.append((true_end, e))
        buf_end = max(ev_end_rule) + wall_s + fx_tail + tail_sil
        te, e_last = max(true_ends, key=lambda x: x[0])
        rel = sp.resolve().relative_to(REPO).as_posix()
        if te > buf_end + 1e-9:
            n_short += 1
            v = vpo.Voice()
            v.ev, v.t_on, v.t_damp, v.fm_rel_t, v.fm_rel_level = e_last, e_last["t_on"], None, None, None
            v.key_down, v.sus_down = True, False
            off = e_last["t_on"] + 0.9 * e_last["dur"]
            v.end = vpo.compute_end(v)
            if off < v.end:
                vpo.stop_tail_off(v, off)
            rem = vpo.remaining_db(v, buf_end)
            print("%-78s %9.3f %9.3f %9.3f id %s %s (%s) remaining %s dB re own start"
                  % (rel[-78:], buf_end, te, te - buf_end, e_last["id"], e_last["note"], e_last["engine"],
                     ("%.1f" % rem) if rem is not None else "n/a"))
    print("scores whose last-ringing voice outlives the render buffer: %d" % n_short)


if __name__ == "__main__":
    main()
