#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925-V1 Part B (open-work:P1-voice-steal): ANALYSIS-ONLY estimate of how
many plugin voices each engine pool would need at once when a corpus score is
played live through the TsukiSynth VST3, and which notes JUCE would steal
when a pool of 16 runs out.

Nothing here is a GATE. No pass/fail threshold is defined anywhere in this
file; the only "16" that appears is the pool size read out of
src/PluginProcessor.cpp itself (and the only release constants are the ones
read out of the engine headers). Everything is printed as numbers.

What the plugin code does (read from source, re-read at every run so a code
change makes this script fail loudly instead of silently using stale values):

  * src/PluginProcessor.cpp: three juce::Synthesiser objects (cimbalomSynth,
    chromaticSynth, fmPianoSynth), each gets `for (int i = 0; i < N; ++i)
    addVoice(...)`. Engine choice "Cimbalom" and "Piano" both feed
    cimbalomSynth; only the CURRENTLY SELECTED engine receives MIDI
    (processBlock). No setNoteStealingEnabled() call -> JUCE default
    shouldStealNotes = true.
  * Voice release (modal engines): note-off -> stopNote(allowTailOff=true) ->
    every mode's decay coefficient is re-derived from decayTime*factor
    (CimbalomVoice::applyDamp: factor read below, 0.05 at time of writing;
    ChromaticVoice::stopNote: 0.08). A mode stops when |amp| <= 0.001*start
    amp (ModalResonator::excite/processSample, "exactly -60 dB"); the voice
    calls clearCurrentNote() once no mode (and no exciter burst) is active.
    So a voice is NOT freed at note-off and NOT after a fixed time: it lives
    until its slowest mode has fallen 60 dB under the damped decay rate.
    Per mode: end = t_on + T60 if never damped (or damped after T60);
    otherwise end = t_damp + factor*(T60 - (t_damp - t_on)). This is the same
    formula ScoreRenderer::eventEndTime() uses for its own buffer sizing.
  * FM engine: ADSR (src/dsp/Envelope.h). The voice is freed only when the
    envelope reaches Idle, i.e. after note-off + release (or immediately at
    note-off if the level is already 0). Attack/decay/sustain tables are read
    from src/engines/FMPianoEngine.h.
  * JUCE 8.0.12 Synthesiser (libs/JUCE/.../juce_Synthesiser.cpp):
      noteOn: every voice already playing the SAME note number is first sent
        stopVoice(tail-off) (it keeps occupying its slot while it rings);
        then findFreeVoice() = first inactive voice in slot order, else
        findVoiceToSteal():
          protect the lowest and the highest note among voices that are NOT
          "playing but released" (top dropped if it is the same voice);
          1) oldest voice playing the incoming note number;
          2) oldest released voice that is not protected;
          3) oldest voice without a key down that is not protected;
          4) oldest voice that is not protected;
          5) the protected top, else the protected low.
        A stolen voice gets stopNote(0, allowTailOff=false) = hard cut.
      noteOff(note): EVERY active voice with that note number gets keyDown
        false and, unless the sustain pedal holds it, stopVoice(tail-off).
      Sustain pedal (CC64) defers note-off damping.

Modelling assumptions (all stated again in the report):
  M1  one MIDI channel; note-on at round(time*sr), note-off at
      round((time + k*duration)*sr); k = 1.0 in scenario A (the repo's own
      plugin harness convention, tests/host_probe.cpp renderNotes()), k = 0.9
      in scenario B (the CLI renderer's own noteOff point,
      ScoreRenderer.h noteOffSample). Scenario C = sustain pedal held for the
      whole piece (the corpus has no pedal data; this is a hypothetical upper
      bound, not a claim about any score).
  M2  at identical sample positions note-offs are processed before note-ons.
  M3  plugin parameters are assumed set to each event's own score params
      with every Macro knob at its 0.5 centre (then the plugin's decay
      scale factors are exactly 1.0, CimbalomVoice/ChromaticVoice startNote),
      so each mode's T60 = the CLI --dump-modes "decay" field.
  M4  a voice is free for a note-on at sample n iff its computed end sample
      <= n (JUCE clears it at the end of the render sub-block; sub-block
      granularity, the <=20 ms exciter burst and float32 rounding of the
      per-sample decay are ignored -- see the probe validation section of the
      report for the measured size of that simplification).
  M5  instance split: view "family" = one plugin instance per engine pool
      receives every event of that family (e.g. both hands of Fur Elise in
      one piano instance); view "track" = one instance per (family, score
      performance.track).

Usage:
  python reports/wf0925_method/voice_pool_occupancy.py \
      --dumps output/wf0925/V1/dumps --out-json output/wf0925/V1/voice_pool.json \
      --out-txt reports/gate_outputs/wf0925_V1_voice_pool.txt
"""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import verify_score as vs  # noqa: E402  (find_all_scores, note_to_midi only)

# engine name -> plugin Synthesiser pool (ScoreRenderer.h engine dispatch +
# PluginProcessor.cpp processBlock routing)
FAMILY = {"string": "cimbalom", "cimbalom": "cimbalom", "piano": "cimbalom",
          "beam": "chromatic", "tongue_drum": "chromatic", "plate": "chromatic",
          "water_gong": "chromatic", "custom": "chromatic", "fm": "fm"}


# ---------------------------------------------------------------------------
# constants read out of the source tree (never typed in by hand)
# ---------------------------------------------------------------------------
def read_code_constants():
    pp = (REPO / "src/PluginProcessor.cpp").read_text(encoding="utf-8")
    pools = {}
    for m in re.finditer(r"for \(int i = 0; i < (\d+); \+\+i\)\s*\{\s*auto\* voice = new (\w+)Voice\(\);", pp):
        pools[m.group(2)] = int(m.group(1))
    need = {"Cimbalom", "Chromatic", "FMPiano"}
    if set(pools) != need:
        raise SystemExit("could not read voice-pool sizes from PluginProcessor.cpp: %r" % pools)
    if "setNoteStealingEnabled" in pp:
        raise SystemExit("PluginProcessor.cpp now calls setNoteStealingEnabled -- update this script")

    cim = (REPO / "src/engines/CimbalomEngine.h").read_text(encoding="utf-8")
    m = re.search(r"void applyDamp\(\)\s*\{\s*if \(! damped\)\s*\{\s*for \(int s = 0; s < numActiveStrings; \+\+s\)\s*strings\[s\]\.damp \(([\d.]+)f\);", cim)
    if not m:
        raise SystemExit("could not read CimbalomVoice::applyDamp factor")
    cim_f = float(m.group(1))

    chrom = (REPO / "src/engines/ChromaticEngine.h").read_text(encoding="utf-8")
    m = re.search(r"void stopNote \(float, bool allowTailOff\) override\s*\{\s*if \(allowTailOff\)\s*\{\s*if \(! damped\)\s*\{\s*resonator\.damp \(([\d.]+)f\);", chrom)
    if not m:
        raise SystemExit("could not read ChromaticVoice::stopNote damp factor")
    chr_f = float(m.group(1))

    fm = (REPO / "src/engines/FMPianoEngine.h").read_text(encoding="utf-8")

    def arr(name):
        mm = re.search(r"static constexpr float %s\[\]\s*=\s*\{([^}]*)\}" % name, fm)
        if not mm:
            raise SystemExit("could not read %s[] from FMPianoEngine.h" % name)
        return [float(x.strip().rstrip("f")) for x in mm.group(1).split(",") if x.strip()]
    decays, sustains = arr("decays"), arr("sustains")
    ma = re.search(r"float\s+attackMs\s*=\s*([\d.]+)f;", fm)
    mr = re.search(r"float\s+releaseMs\s*=\s*([\d.]+)f;", fm)
    if not (ma and mr):
        raise SystemExit("could not read FMParams attack/release defaults")

    env = (REPO / "src/dsp/Envelope.h").read_text(encoding="utf-8")
    if "bool isActive() const { return state != State::Idle; }" not in env:
        raise SystemExit("Envelope::isActive semantics changed -- update this script")
    mod = (REPO / "src/dsp/ModalResonator.h").read_text(encoding="utf-8")
    if "m.stopAmp    = std::abs (m.currentAmp) * 0.001f;" not in mod:
        raise SystemExit("ModalResonator stop rule changed -- update this script")

    return {
        "pool_size": {"cimbalom": pools["Cimbalom"], "chromatic": pools["Chromatic"],
                       "fm": pools["FMPiano"]},
        "damp_factor": {"cimbalom": cim_f, "chromatic": chr_f},
        "fm_decays_s": decays, "fm_sustains": sustains,
        "fm_default_attack_ms": float(ma.group(1)),
        "fm_default_release_ms": float(mr.group(1)),
        "sources": {
            "pool_size": "src/PluginProcessor.cpp addVoice loops",
            "damp_factor.cimbalom": "src/engines/CimbalomEngine.h applyDamp()",
            "damp_factor.chromatic": "src/engines/ChromaticEngine.h stopNote()",
            "fm tables": "src/engines/FMPianoEngine.h decays[]/sustains[], FMParams",
            "stop rule": "src/dsp/ModalResonator.h stopAmp = 0.001*start",
        },
    }


# ---------------------------------------------------------------------------
# events
# ---------------------------------------------------------------------------
def dump_cache_path(dumps_dir, score_path):
    rel = score_path.resolve().relative_to(REPO).as_posix()
    return Path(dumps_dir) / (rel.replace("/", "__") + ".dump.json")


def load_events(score_path, dumps_dir, consts, _depth=0):
    """Returns (events, notes) for one score; layered scores are flattened
    with the layer offsets the CLI's own layered --dump-modes reports."""
    s = json.loads(Path(score_path).read_text(encoding="utf-8"))
    sr = float(s.get("global", {}).get("sample_rate", 48000))
    dump = json.loads(dump_cache_path(dumps_dir, score_path).read_text(encoding="utf-8"))
    notes = []
    if "layers" in s:
        metas = dump.get("layers") or []
        if len(metas) != len(s["layers"]):
            raise SystemExit("layer meta mismatch for %s" % score_path)
        out = []
        for li, (layer, meta) in enumerate(zip(s["layers"], metas)):
            leaf = (Path(score_path).parent / layer["source"]).resolve()
            leaf_ev, leaf_sr, leaf_notes = load_events(leaf, dumps_dir, consts, _depth + 1)
            off = float(meta["offset_s"])
            reg = layer.get("region") or [0.0, 1.0]
            if float(reg[0]) != 0.0:
                notes.append("layer %d region starts at %.3f (not 0): leaf times kept "
                             "as leaf_time+offset, same convention as the CLI layered dump"
                             % (li, float(reg[0])))
            if float(reg[1]) != 1.0:
                notes.append("layer %d (%s) region end %.3f: MIDI playback cannot crop "
                             "audio, all leaf events kept" % (li, layer["source"], float(reg[1])))
            for e in leaf_ev:
                e2 = dict(e)
                e2["t_on"] = e["t_on"] + off
                e2["id"] = "L%d:%s" % (li, e["id"])
                e2["layer_source"] = layer["source"]
                out.append(e2)
            notes.extend(leaf_notes)
        return out, sr, notes

    dmap = {int(d["source_index"]): d for d in dump.get("events", [])}
    events = []
    for i, e in enumerate(s["events"]):
        if not (float(e.get("velocity", 0)) > 0):
            continue
        eng = e["engine"]
        fam = FAMILY[eng]
        midi = vs.note_to_midi(e.get("note"))
        perf = e.get("performance") or {}
        rec = {"id": str(i), "index": i, "t_on": float(e["time"]),
               "dur": max(0.0, float(e.get("duration", 0.0))), "midi": midi,
               "note": e.get("note"), "engine": eng, "family": fam,
               "velocity": float(e["velocity"]), "track": perf.get("track")}
        if fam != "fm":
            d = dmap.get(i)
            if d is None:
                raise SystemExit("no dump entry for event %d of %s" % (i, score_path))
            if d.get("midi") is not None and midi is not None and int(d["midi"]) != midi:
                notes.append("event %d: dump midi %s != parsed %s (dump value used)"
                             % (i, d["midi"], midi))
                rec["midi"] = int(d["midi"])
            if rec["midi"] is None and d.get("midi") is not None:
                rec["midi"] = int(d["midi"])
            strings = d.get("strings")
            modes = [m for st in strings for m in st] if strings else list(d.get("partials") or [])
            dec = np.array([float(m["decay"]) for m in modes], dtype=float)
            amp = np.array([float(m["amp"]) for m in modes], dtype=float)
            ok = np.isfinite(dec) & (dec > 0)
            dec, amp = dec[ok], amp[ok]
            if dec.size == 0:
                raise SystemExit("event %d of %s has no positive decays" % (i, score_path))
            k = int(np.argmax(dec))
            rec["t60_max"] = float(dec[k])
            rec["t60_max_mode_amp_printed_zero"] = bool(amp[k] == 0.0)
            rec["decays"] = dec
            rec["amps"] = amp
            rec["damp_factor"] = consts["damp_factor"][fam]
        else:
            p = e.get("params") or {}
            preset = int(p.get("fm_preset", 0))
            att_ms = float(p["fm_attack"]) if "fm_attack" in p else consts["fm_default_attack_ms"]
            rel_ms = float(p["fm_release"]) if "fm_release" in p else consts["fm_default_release_ms"]
            rec["fm_preset"] = preset
            rec["fm_attack_s"] = max(0.001, att_ms * 0.001)          # Envelope::setAttack floor
            rec["fm_decay_s"] = max(0.001, consts["fm_decays_s"][preset])
            rec["fm_sustain"] = min(1.0, max(0.0, consts["fm_sustains"][preset]))
            rec["fm_release_s"] = max(0.001, rel_ms * 0.001)         # Envelope::setRelease floor
        events.append(rec)
    return events, sr, notes


# ---------------------------------------------------------------------------
# voice model
# ---------------------------------------------------------------------------
class Voice:
    __slots__ = ("slot", "ev", "note", "order", "key_down", "sus_down", "t_on",
                 "t_damp", "fm_rel_t", "fm_rel_level", "end", "early")


def fm_level_held(ev, x):
    a, d, s = ev["fm_attack_s"], ev["fm_decay_s"], ev["fm_sustain"]
    if x < a:
        return x / a
    if x < a + d:
        return 1.0 - (1.0 - s) * (x - a) / d
    return s


def fm_level(v, t):
    ev = v.ev
    if v.fm_rel_t is None:
        return fm_level_held(ev, t - v.t_on)
    frac = (t - v.fm_rel_t) / ev["fm_release_s"]
    return max(0.0, v.fm_rel_level * (1.0 - frac))


def compute_end(v):
    ev = v.ev
    if ev["family"] == "fm":
        if v.fm_rel_t is None:
            return math.inf            # ADSR never reaches Idle while held
        if v.fm_rel_level <= 0.0:
            return v.fm_rel_t          # Release from 0 -> Idle on next sample
        return v.fm_rel_t + ev["fm_release_s"]
    T = ev["t60_max"]
    if v.t_damp is None or (v.t_damp - v.t_on) >= T:
        return v.t_on + T
    return v.t_damp + ev["damp_factor"] * (T - (v.t_damp - v.t_on))


def stop_tail_off(v, t):
    """stopNote(allowTailOff=true) at time t."""
    ev = v.ev
    if ev["family"] == "fm":
        lvl = fm_level(v, t)
        v.fm_rel_t, v.fm_rel_level = t, lvl     # Envelope::noteOff restarts ramp
    else:
        if v.t_damp is None:                    # `damped` flag: first damp only
            v.t_damp = t
    v.end = compute_end(v)


def remaining_db(v, t):
    """Descriptive only: stolen voice's remaining energy (modal) or envelope
    level (fm) at time t, relative to its own start, in dB."""
    ev = v.ev
    if ev["family"] == "fm":
        lvl = fm_level(v, t)
        return 20.0 * math.log10(lvl) if lvl > 0 else None
    dec, amp, f = ev["decays"], ev["amps"], ev["damp_factor"]
    e0 = float(np.sum(amp * amp))
    if e0 <= 0:
        return None
    x = t - v.t_on
    if v.t_damp is None or x <= (v.t_damp - v.t_on):
        db = -60.0 * x / dec
    else:
        xd = v.t_damp - v.t_on
        db = -60.0 * xd / dec - 60.0 * (x - xd) / (f * dec)
    alive = db > -60.0
    e = float(np.sum((amp[alive] ** 2) * 10.0 ** (db[alive] / 10.0)))
    return 10.0 * math.log10(e / e0) if e > 0 else None


def build_messages(events, sr, scenario):
    k = 0.9 if scenario == "B" else 1.0
    msgs = []
    for order, ev in enumerate(events):
        n_on = int(round(ev["t_on"] * sr))
        n_off = int(round((ev["t_on"] + k * ev["dur"]) * sr))
        if n_off < n_on:
            n_off = n_on
        msgs.append((n_on, 1, order, "on", ev))
        msgs.append((n_off, 0, order, "off", ev))
    msgs.sort(key=lambda m: (m[0], m[1], m[2]))
    return msgs


def simulate(events, sr, scenario, pool_size, until_sample=None):
    """pool_size=None -> unlimited pool (demand). Returns dict.
    until_sample: stop after processing every message at or before this
    sample (used only by fm_zombie_check.py to read the state at one instant)."""
    pedal = scenario == "C"
    msgs = build_messages(events, sr, scenario)
    slots = [] if pool_size is None else [None] * pool_size
    active = []          # used only for the unlimited pool
    counter = 0
    steals = []
    all_voices = []
    max_count, max_t, max_snapshot = 0, None, None

    def live_voices():
        return [v for v in (active if pool_size is None else slots) if v is not None]

    for n, _typ, _o, kind, ev in msgs:
        if until_sample is not None and n > until_sample:
            break
        t = n / sr
        # M4: retire voices whose end <= now
        if pool_size is None:
            active[:] = [v for v in active if not (v.end * sr <= n + 1e-9)]
        else:
            for i, v in enumerate(slots):
                if v is not None and v.end * sr <= n + 1e-9:
                    slots[i] = None
        note = ev["midi"]
        if kind == "off":
            for v in live_voices():
                if v.note == note:
                    if v.key_down and v.ev is not ev and v.early is None:
                        # JUCE noteOff(note) hits EVERY voice with that note
                        # number -- this voice's own note-off is still ahead.
                        v.early = "foreign_note_off"
                    v.key_down = False
                    if not v.sus_down:
                        stop_tail_off(v, t)
            continue
        # note-on: same-note voices get tail-off first (JUCE noteOn)
        for v in live_voices():
            if v.note == note:
                if v.key_down and v.early is None:
                    v.early = "same_note_on"
                stop_tail_off(v, t)
        stolen = None
        if pool_size is None:
            slot = len(all_voices)
        else:
            free = [i for i, v in enumerate(slots) if v is None]
            if free:
                slot = free[0]
            else:
                victim, rule = find_voice_to_steal(slots, note)
                slot = victim.slot
                stolen = {"t": t, "rule": rule, "victim": victim.ev["id"],
                          "victim_note": victim.ev["note"], "victim_midi": victim.note,
                          "victim_t_on": victim.t_on, "victim_age_s": t - victim.t_on,
                          "victim_key_down": victim.key_down,
                          "victim_released": not (victim.key_down or victim.sus_down),
                          "victim_natural_end_s": victim.end,
                          "victim_cut_s": victim.end - t,
                          "victim_remaining_db": remaining_db(victim, t),
                          "incoming": ev["id"], "incoming_note": ev["note"],
                          "incoming_midi": note}
                victim.end = t          # hard cut (stopNote(0,false))
                steals.append(stolen)
        v = Voice()
        v.slot, v.ev, v.note = slot, ev, note
        counter += 1
        v.order = counter
        v.key_down, v.sus_down = True, pedal
        v.t_on, v.t_damp, v.fm_rel_t, v.fm_rel_level = t, None, None, None
        v.early = None
        v.end = compute_end(v)
        all_voices.append(v)
        if pool_size is None:
            active.append(v)
            cnt = len(active)
        else:
            slots[slot] = v
            cnt = sum(1 for x in slots if x is not None)
        if cnt > max_count:
            max_count, max_t = cnt, t
            max_snapshot = sorted(((x.ev["note"], round(t - x.t_on, 3), x.key_down)
                                   for x in live_voices()), key=lambda z: -z[1])[:40]
    return {"max": max_count, "max_t": max_t, "max_snapshot": max_snapshot,
            "steals": steals, "voices": all_voices}


def find_voice_to_steal(slots, new_note):
    """JUCE 8.0.12 Synthesiser::findVoiceToSteal, same order of tests."""
    usable = sorted((v for v in slots if v is not None), key=lambda v: v.order)
    low = top = None
    for v in slots:                       # voices array order (slot order)
        if v is None:
            continue
        released = not (v.key_down or v.sus_down)
        if not released:
            if low is None or v.note < low.note:
                low = v
            if top is None or v.note > top.note:
                top = v
    if top is low:
        top = None
    for v in usable:
        if v.note == new_note:
            return v, "1_same_note_oldest"
    for v in usable:
        if v is not low and v is not top and not (v.key_down or v.sus_down):
            return v, "2_oldest_released"
    for v in usable:
        if v is not low and v is not top and not v.key_down:
            return v, "3_oldest_no_key"
    for v in usable:
        if v is not low and v is not top:
            return v, "4_oldest_unprotected_key_held"
    return (top, "5_protected_top") if top is not None else (low, "6_protected_low")


def over_intervals(voices, limit):
    """Exact piecewise-constant count of the unlimited-pool voices; returns
    (intervals where count > limit, total seconds above)."""
    pts = []
    for v in voices:
        end = v.end if math.isfinite(v.end) else float("inf")
        pts.append((v.t_on, 1))
        pts.append((end, -1))
    pts.sort(key=lambda p: (p[0], p[1]))   # ends before starts at same t
    cnt, out, cur_start = 0, [], None
    peak = 0
    for t, d in pts:
        cnt += d
        if cnt > limit and cur_start is None:
            cur_start = t
            peak = cnt
        elif cnt > limit:
            peak = max(peak, cnt)
        elif cnt <= limit and cur_start is not None:
            out.append((cur_start, t, peak))
            cur_start = None
    if cur_start is not None:
        out.append((cur_start, float("inf"), peak))
    total = sum((b - a) for a, b, _ in out if math.isfinite(b))
    return out, total


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dumps", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-txt", required=True)
    ap.add_argument("--catalog", default=str(REPO / "exports/products/clean_batch2/catalog.json"))
    ap.add_argument("--root", default=str(REPO),
                    help="tree whose scores/ subfolders are analysed (default: repo). "
                         "Point it at make_plugin_reachable_scores.py's output to get "
                         "plugin-reachable T60s (damping_override/tension_n removed).")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    consts = read_code_constants()
    manifest = json.loads((Path(args.dumps) / "manifest.json").read_text(encoding="utf-8"))
    scores = vs.find_all_scores(root)
    products = set()
    cat_path = Path(args.catalog)
    if cat_path.is_file():
        for c in json.loads(cat_path.read_text(encoding="utf-8")):
            if c.get("score"):
                products.add(c["score"].replace(chr(92), "/"))

    lines = []
    P = lines.append
    P("# WF0925-V1 Part B voice-pool occupancy (analysis only, no GATE, no threshold)")
    P("# code constants read from source: %s" % json.dumps({k: v for k, v in consts.items() if k != "sources"}))
    P("# dumps: %s  cli_sha256=%s  root=%s" % (args.dumps, manifest.get("cli_sha256"), root))
    P("# corpus: %d scores (tools/verify_score.py find_all_scores); clean_batch2 products: %d scores"
      % (len(scores), len(products)))
    P("# scenarios: A=note-off at time+duration (HostProbe convention); B=time+0.9*duration "
      "(CLI renderer convention); C=sustain pedal held whole piece (hypothetical upper bound)")
    P("# views: family=one instance per engine pool; track=one instance per (pool, performance.track)")
    P("")

    results = []
    for sp in scores:
        rel = sp.resolve().relative_to(root).as_posix()
        events, sr, notes = load_events(sp, args.dumps, consts)
        is_product = rel in products
        for view in ("family", "track"):
            groups = {}
            for ev in events:
                key = ev["family"] if view == "family" else "%s|%s" % (ev["family"], ev.get("track"))
                groups.setdefault(key, []).append(ev)
            for gkey, gev in sorted(groups.items()):
                fam = gev[0]["family"]
                pool = consts["pool_size"][fam]
                gev = sorted(gev, key=lambda e: (e["t_on"], e["index"] if "index" in e else 0))
                for scen in ("A", "B", "C"):
                    dem = simulate(gev, sr, scen, None)
                    cap = simulate(gev, sr, scen, pool)
                    ivals, above = over_intervals(dem["voices"], pool)
                    rules = {}
                    for st in cap["steals"]:
                        rules[st["rule"]] = rules.get(st["rule"], 0) + 1
                    rem = [st["victim_remaining_db"] for st in cap["steals"]
                           if st["victim_remaining_db"] is not None]
                    # descriptive bins only (labelled 描述用分箱、非 GATE in the
                    # report) -- they only sort numbers for reading, nothing is
                    # judged against them.
                    bins = {"(-10,0]": 0, "(-20,-10]": 0, "(-40,-20]": 0, "(-60,-40]": 0,
                            "<=-60": 0, "n/a(level 0 or inf)": 0}
                    for st in cap["steals"]:
                        x = st["victim_remaining_db"]
                        if x is None:
                            bins["n/a(level 0 or inf)"] += 1
                        elif x > -10:
                            bins["(-10,0]"] += 1
                        elif x > -20:
                            bins["(-20,-10]"] += 1
                        elif x > -40:
                            bins["(-40,-20]"] += 1
                        elif x > -60:
                            bins["(-60,-40]"] += 1
                        else:
                            bins["<=-60"] += 1
                    loudest = sorted((st for st in cap["steals"] if st["victim_remaining_db"] is not None),
                                     key=lambda st: -st["victim_remaining_db"])[:10]
                    res = {
                        "score": rel, "product": is_product, "view": view, "group": gkey,
                        "family": fam, "pool_size": pool, "scenario": scen,
                        "n_events": len(gev),
                        "demand_max": dem["max"], "demand_max_t": dem["max_t"],
                        "demand_max_snapshot": dem["max_snapshot"],
                        "seconds_demand_above_pool": above,
                        "n_intervals_above_pool": len(ivals),
                        "first_intervals": [(round(a, 3), (round(b, 3) if math.isfinite(b) else None), pk)
                                            for a, b, pk in ivals[:5]],
                        "n_steals": len(cap["steals"]),
                        # key-held voices damped before their OWN note-off by
                        # JUCE's same-note rules (unlimited pool, so this is
                        # independent of the pool size)
                        "early_damp_same_note_on": sum(1 for v in dem["voices"] if v.early == "same_note_on"),
                        "early_damp_foreign_note_off": sum(1 for v in dem["voices"] if v.early == "foreign_note_off"),
                        "early_damp_examples": [
                            {"id": v.ev["id"], "note": v.ev["note"], "t_on": round(v.t_on, 4),
                             "own_note_off": round(v.t_on + (0.9 if scen == "B" else 1.0) * v.ev["dur"], 4),
                             "damped_at": (round(v.t_damp, 4) if v.t_damp is not None
                                           else (round(v.fm_rel_t, 4) if v.fm_rel_t is not None else None)),
                             "cause": v.early}
                            for v in dem["voices"] if v.early][:40],
                        "steal_rules": rules,
                        "steals_victim_key_down": sum(1 for st in cap["steals"] if st["victim_key_down"]),
                        "steal_remaining_db_quartiles": (
                            [round(float(q), 2) for q in np.percentile(rem, [0, 25, 50, 75, 100])]
                            if rem else None),
                        "steal_remaining_db_bins_descriptive": bins,
                        "loudest_victims": loudest,
                        "steals": cap["steals"],
                        "t60_max_over_events": max((e.get("t60_max", 0.0) for e in gev), default=0.0),
                        "argmax_mode_amp_printed_zero": sum(1 for e in gev if e.get("t60_max_mode_amp_printed_zero")),
                        "notes": notes,
                    }
                    results.append(res)

    # ---- text summary ----
    P("## per score / view / group / scenario  (demand = voices needed with an unlimited pool)")
    P("%-72s %-6s %-22s %-2s %6s %6s %9s %8s %7s %7s" % (
        "score", "view", "group", "sc", "events", "demand", "t_at_max", "s_above", "steals", "held"))
    for r in results:
        P("%-72s %-6s %-22s %-2s %6d %6d %9s %8.2f %7d %7d%s" % (
            r["score"][-72:], r["view"], r["group"][:22], r["scenario"], r["n_events"],
            r["demand_max"], ("%.3f" % r["demand_max_t"]) if r["demand_max_t"] is not None else "-",
            r["seconds_demand_above_pool"], r["n_steals"], r["steals_victim_key_down"],
            "  [product]" if r["product"] else ""))
    P("")
    P("## scores whose demand exceeds the pool (any view/scenario)")
    for r in results:
        if r["demand_max"] > r["pool_size"]:
            P("%s | %s | %s | %s : demand %d > %d at t=%.3f s; %d steals (rules %s); "
              "victim key still held in %d; remaining-energy dB quartiles %s; first windows %s"
              % (r["score"], r["view"], r["group"], r["scenario"], r["demand_max"], r["pool_size"],
                 r["demand_max_t"], r["n_steals"], r["steal_rules"], r["steals_victim_key_down"],
                 r["steal_remaining_db_quartiles"], r["first_intervals"]))
    P("")
    P("## remaining-energy bins of stolen voices (DESCRIPTIVE bins, not a GATE) + 10 loudest victims")
    for r in results:
        if not r["steals"]:
            continue
        P("### %s | %s | %s | %s : %s" % (r["score"], r["view"], r["group"], r["scenario"],
                                          r["steal_remaining_db_bins_descriptive"]))
        for st in r["loudest_victims"]:
            P("  t=%9.3f  steals %-6s(id %s, on %.3f, age %.3f s, key_down=%s, rule %s) remaining %.1f dB"
              " for incoming %-6s(id %s)" % (st["t"], st["victim_note"], st["victim"], st["victim_t_on"],
                                            st["victim_age_s"], st["victim_key_down"], st["rule"],
                                            st["victim_remaining_db"], st["incoming_note"], st["incoming"]))
    P("")
    P("## first 12 steals per (score, view, group, scenario) with steals")
    for r in results:
        if not r["steals"]:
            continue
        P("### %s | %s | %s | %s  (%d steals)" % (r["score"], r["view"], r["group"], r["scenario"], r["n_steals"]))
        for st in r["steals"][:12]:
            P("  t=%9.3f  incoming %-8s(id %s)  steals %-8s(id %s, on %.3f, age %.3f s, key_down=%s, "
              "rule %s, would have rung %.3f s more, remaining %s dB)" % (
                  st["t"], st["incoming_note"], st["incoming"], st["victim_note"], st["victim"],
                  st["victim_t_on"], st["victim_age_s"], st["victim_key_down"], st["rule"],
                  st["victim_cut_s"] if math.isfinite(st["victim_cut_s"]) else float("inf"),
                  ("%.1f" % st["victim_remaining_db"]) if st["victim_remaining_db"] is not None else "n/a"))

    Path(args.out_txt).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_txt).write_text("\n".join(lines) + "\n", encoding="utf-8")

    def clean(o):
        if isinstance(o, float) and not math.isfinite(o):
            return None
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(x) for x in o]
        return o
    Path(args.out_json).write_text(json.dumps(clean({"constants": consts, "results": results}),
                                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s (%d rows) and %s" % (args.out_txt, len(results), args.out_json))
    return 0


if __name__ == "__main__":
    sys.exit(main())
