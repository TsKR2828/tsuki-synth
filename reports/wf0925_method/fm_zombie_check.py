#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925-V1 Part B: why does moonlight_sonata_complete (FM engine) need
~196 voices with an unlimited pool? Descriptive only.

Mechanism (read from code): Envelope::noteOff() (src/dsp/Envelope.h) runs
whenever state != Idle -- including a voice that is ALREADY in Release -- and
restarts the release ramp from the current level over the full release time.
JUCE Synthesiser::noteOn()/noteOff() call stopVoice(tail-off) on EVERY active
voice holding that note number, so each re-strike of a note (and each
note-off of that note) restarts the release of all older, still-releasing
voices of the same note. If the same note recurs more often than its release
time, older voices never reach Idle.

This script re-runs the unlimited-pool simulation (scenario A) and, at the
moment of peak demand, prints every active voice's envelope level (dB re the
envelope peak 1.0, exact-arithmetic model) in descriptive bins, plus how
many of those voices are key-held vs released.

Note on float32: the plugin runs under juce::ScopedNoDenormals
(PluginProcessor.cpp processBlock), so a releaseRate below FLT_MIN flushes to
0 and the level then stays constant (~1e-35 or so) instead of shrinking --
the voice still only goes Idle after a full release time without a restart,
i.e. the same end time the model uses. Only the printed dB of such voices
differs (the model's exact arithmetic shows smaller numbers); both are far
below anything a 24-bit output can represent.
"""
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import voice_pool_occupancy as vpo  # noqa: E402

import math


def main():
    dumps = sys.argv[1] if len(sys.argv) > 1 else "output/wf0925/V1/dumps"
    consts = vpo.read_code_constants()
    sp = (REPO / "scores/examples/moonlight_sonata_complete.score.json").resolve()
    events, sr, _ = vpo.load_events(sp, dumps, consts)
    events = sorted(events, key=lambda e: (e["t_on"], e["index"]))
    r = vpo.simulate(events, sr, "A", None)
    t = r["max_t"]
    n_peak = int(round(t * sr))
    # re-run up to (and including) the peak instant so every voice's state is
    # the state AT the peak, not its final state
    r2 = vpo.simulate(events, sr, "A", None, until_sample=n_peak)
    live = [v for v in r2["voices"] if v.end * sr > n_peak + 1e-9]
    print("peak demand %d at t=%.3f s ; voices alive at that instant (recomputed): %d" % (r["max"], t, len(live)))
    bins = Counter()
    notes = Counter()
    for v in live:
        lvl = vpo.fm_level(v, t)
        db = 20 * math.log10(lvl) if lvl > 0 else None
        if db is None:
            b = "level 0"
        elif db > -10:
            b = "(-10,0]"
        elif db > -60:
            b = "(-60,-10]"
        elif db > -138.5:
            b = "(-138.5,-60]"
        else:
            b = "<=-138.5 (below 24-bit LSB 2^-23, reference line only)"
        bins[b] += 1
        notes[(v.ev["note"], v.key_down)] += 1
    print("envelope level bins at the peak (DESCRIPTIVE, not a GATE): %s" % dict(bins))
    print("key_down=True: %d ; released: %d" % (sum(1 for v in live if v.key_down),
                                                 sum(1 for v in live if not v.key_down)))
    print("voices by (note, key_down), top 10: %s" % notes.most_common(10))
    rel = sorted({round(e["fm_release_s"], 3) for e in events})
    print("fm_release values in this score (s): %s" % rel)


if __name__ == "__main__":
    main()
