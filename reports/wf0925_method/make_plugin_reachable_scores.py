#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925-V1 Part B helper: write a copy of the corpus in which every event
param the PLUGIN has no control for is removed, so --dump-modes on the copy
gives the T60s a plugin instance can actually produce (Macro knobs at their
0.5 centre).

Which params are plugin-unreachable (read from code, not assumed):
  * damping_override -- CimbalomVoice::startNote() calls
    applyStringDecayTimes(..., dampingOverride = -1.0f, ...) ("the plugin UI
    has no such control; only the CLI's score.json damping_override field
    can pass a real value", CimbalomEngine.h worstCaseTailSeconds comment);
    ChromaticVoice likewise has no damping-override parameter pointer.
  * tension_n -- StringModel::tensionForNote() is always used by
    startNote(); the plugin has no tension-in-newtons parameter (Macro
    Tension only scales frequency).
Everything else (material, diameter, strike position, exciter/hammer,
string count, detuning, tongue/plate geometry, fm_*) maps to an APVTS
parameter and is kept as authored.

The script refuses to proceed if those two claims stop being true in the
source (grep checks below).

Usage:
  python reports/wf0925_method/make_plugin_reachable_scores.py --out output/wf0925/V1/reachable
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import verify_score as vs  # noqa: E402

UNREACHABLE = ("damping_override", "tension_n")


def check_source():
    cim = (REPO / "src/engines/CimbalomEngine.h").read_text(encoding="utf-8")
    start = cim.index("void startNote (int midiNoteNumber")
    stop = cim.index("void stopNote", start)
    body = cim[start:stop]
    if "applyStringDecayTimes (baseModes, *mat, -1.0f" not in body \
            or "applyStringDecayTimes (modes, *mat, -1.0f" not in body:
        raise SystemExit("CimbalomVoice::startNote no longer passes dampingOverride=-1 -- re-check")
    if "tensionForNote" not in body:
        raise SystemExit("CimbalomVoice::startNote no longer uses tensionForNote -- re-check")
    params = (REPO / "src/ParameterLayout.cpp").read_text(encoding="utf-8")
    for bad in ("damping_override", "tension_n", "\"cim_tension\"", "\"cim_damping\""):
        if bad in params:
            raise SystemExit("ParameterLayout.cpp now has %s -- re-check" % bad)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    check_source()
    out = Path(args.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    removed = {}
    for sp in vs.find_all_scores(REPO):
        rel = sp.resolve().relative_to(REPO)
        s = json.loads(sp.read_text(encoding="utf-8"))
        n = 0
        for e in s.get("events", []):
            p = e.get("params")
            if isinstance(p, dict):
                for k in UNREACHABLE:
                    if k in p:
                        del p[k]
                        n += 1
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
        removed[rel.as_posix()] = n
    (out / "removed_params.json").write_text(json.dumps(removed, indent=1), encoding="utf-8")
    tot = sum(removed.values())
    print("wrote %d scores under %s; removed %d param entries (%s) in %d scores"
          % (len(removed), out, tot, "/".join(UNREACHABLE), sum(1 for v in removed.values() if v)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
